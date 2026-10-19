#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

for script in PKGBUILD perplexity.sh scripts/validate.sh scripts/publish-aur.sh; do
  bash -n "$script"
done
python3 -m unittest discover -s tests -v
diff -u .SRCINFO <(makepkg --printsrcinfo)
makepkg --cleanbuild --force --noconfirm
namcap PKGBUILD
rules=$(python3 - <<'PY'
from Namcap.rules import all_rules
excluded = {"elfpaths", "pydepends", "shebangdepends"}
print(",".join(name for name, rule in all_rules.items() if rule.enable and name not in excluded))
PY
)
while IFS= read -r package; do
  # Vendor bundles belong in /opt. The local-template Python scripts run in
  # the app-managed uv venv (see its manifest), not the host Python environment.
  # Select rules explicitly: some Namcap versions re-enable earlier entries
  # when multiple exclusions are passed to -e.
  report=$(namcap -r "$rules" "$package")
  printf '%s\n' "$report"
  if [[ "$report" == *' E: '* ]]; then
    exit 1
  fi
done < <(makepkg --packagelist)

desktop-file-validate pkg/perplexity-bin/usr/share/applications/perplexity.desktop
test -x pkg/perplexity-bin/opt/Perplexity/resources/native/bin/perplexity
test -x pkg/perplexity-bin/usr/bin/perplexity
test ! -e pkg/perplexity-bin/lib/systemd/system/perplexity-local-runtime-setup.service
test ! -e pkg/perplexity-bin/usr/lib/systemd/system/perplexity-local-runtime-setup.service
