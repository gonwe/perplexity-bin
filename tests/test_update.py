import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location("updater", Path(__file__).parents[1] / "scripts/update.py")
updater = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = updater
spec.loader.exec_module(updater)

HASH = "a" * 64
RECIPE = f"pkgver=26.10.2\npkgrel=1\n_build=117519\n_sha256={HASH}\n"


def index(version="26.10.2", build=117519, filename=None):
    filename = filename or f"pool/main/p/perplexity/perplexity_{version}+build{build}_amd64.deb"
    return (f"Package: perplexity\nVersion: {version}\nArchitecture: amd64\n"
            f"Filename: {filename}\nSHA256: {HASH}\n")


class Updates(unittest.TestCase):
    def test_selects_latest_from_multiple_versions(self):
        latest = updater.parse_index(index("26.9.10") + "\n" + index())
        self.assertEqual(latest.version, "26.10.2")

    def test_rejects_unexpected_download_path(self):
        with self.assertRaises(ValueError):
            updater.parse_index(index(filename="../../malicious.deb"))

    def test_no_change_for_existing_release(self):
        self.assertEqual(updater.update_recipe(RECIPE, updater.parse_index(index())), RECIPE)

    def test_new_build_increments_pkgrel(self):
        updated = updater.update_recipe(RECIPE, updater.parse_index(index(build=117520)))
        self.assertIn("pkgrel=2\n", updated)
        self.assertIn("_build=117520\n", updated)

    def test_new_version_resets_pkgrel(self):
        updated = updater.update_recipe(RECIPE.replace("pkgrel=1", "pkgrel=4"),
                                        updater.parse_index(index("26.11.1", 120000)))
        self.assertIn("pkgver=26.11.1\n", updated)
        self.assertIn("pkgrel=1\n", updated)

    def test_refuses_downgrade_and_replaced_binary(self):
        for latest in (updater.Release("26.9.1", 111111, HASH),
                       updater.Release("26.10.2", 117518, HASH),
                       updater.Release("26.10.2", 117519, "b" * 64)):
            with self.subTest(latest=latest), self.assertRaises(ValueError):
                updater.update_recipe(RECIPE, latest)


if __name__ == "__main__":
    unittest.main()
