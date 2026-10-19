#!/usr/bin/env python3
"""Check the vendor's Linux repository; optionally update the AUR recipe."""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen

INDEX_URL = "https://packages.perplexity.ai/deb/dists/stable/main/binary-amd64/Packages"
ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Release:
    version: str
    build: int
    sha256: str

    @property
    def order(self):
        return tuple(map(int, self.version.split("."))), self.build


def parse_index(text):
    releases = []
    for paragraph in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in paragraph.splitlines()
                      if ": " in line and not line.startswith((" ", "\t")))
        if fields.get("Package") != "perplexity" or fields.get("Architecture") != "amd64":
            continue
        version = fields.get("Version", "")
        if not re.fullmatch(r"\d+(?:\.\d+){1,3}", version):
            raise ValueError("Unexpected upstream version")
        match = re.fullmatch(
            rf"pool/main/p/perplexity/perplexity_{re.escape(version)}\+build(\d+)_amd64\.deb",
            fields.get("Filename", ""))
        digest = fields.get("SHA256", "")
        if not match or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Unexpected upstream filename or SHA256")
        releases.append(Release(version, int(match[1]), digest))
    if not releases:
        raise ValueError("No official perplexity amd64 release in repository")
    return max(releases, key=lambda release: release.order)


def assignment(text, key):
    match = re.search(rf"^{re.escape(key)}=(\S+)$", text, re.M)
    if not match:
        raise ValueError(f"Missing PKGBUILD field: {key}")
    return match[1]


def update_recipe(text, latest):
    current = Release(assignment(text, "pkgver"), int(assignment(text, "_build")),
                      assignment(text, "_sha256"))
    if latest.order < current.order:
        raise ValueError("Upstream appears older; refusing automatic downgrade")
    if latest.order == current.order:
        if latest.sha256 != current.sha256:
            raise ValueError("Same version/build changed hash; manual review required")
        return text
    pkgrel = int(assignment(text, "pkgrel")) + 1 if latest.version == current.version else 1
    for key, value in {"pkgver": latest.version, "pkgrel": pkgrel,
                       "_build": latest.build, "_sha256": latest.sha256}.items():
        text = re.sub(rf"^{re.escape(key)}=\S+$", f"{key}={value}", text, count=1, flags=re.M)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Print status without changing files (default)")
    mode.add_argument("--apply", action="store_true", help="Update PKGBUILD and regenerate .SRCINFO")
    args = parser.parse_args()
    with urlopen(INDEX_URL, timeout=45) as response:
        latest = parse_index(response.read(2 * 1024 * 1024).decode("utf-8"))
    path = ROOT / "PKGBUILD"
    original = path.read_text()
    updated = update_recipe(original, latest)
    changed = updated != original
    print(json.dumps({"update_available": changed, "latest": asdict(latest)}, indent=2))
    if args.apply and changed:
        path.write_text(updated)
        try:
            srcinfo = subprocess.check_output(["makepkg", "--printsrcinfo"], cwd=ROOT, text=True)
        except Exception:
            path.write_text(original)
            raise
        (ROOT / ".SRCINFO").write_text(srcinfo)


if __name__ == "__main__":
    main()
