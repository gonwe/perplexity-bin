#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -n "$(git status --porcelain)" ]]; then
  echo 'Commit the validated packaging changes before publishing to AUR.' >&2
  exit 1
fi
diff -u .SRCINFO <(makepkg --printsrcinfo)
staging_dir=$(mktemp -d)
trap 'rm -rf "$staging_dir"' EXIT
git clone ssh://aur@aur.archlinux.org/perplexity-bin.git "$staging_dir/aur"
for file in PKGBUILD .SRCINFO perplexity.sh LICENSE.upstream LICENSE; do
  cp "$file" "$staging_dir/aur/$file"
done
git -C "$staging_dir/aur" add PKGBUILD .SRCINFO perplexity.sh LICENSE.upstream LICENSE
if git -C "$staging_dir/aur" diff --cached --quiet; then
  echo 'AUR already matches the validated recipe.'
  exit 0
fi
version=$(sed -n 's/^pkgver=//p' PKGBUILD)
revision=$(sed -n 's/^pkgrel=//p' PKGBUILD)
git -C "$staging_dir/aur" -c user.name=gonwex -c user.email=gonwe@qq.com \
  commit -m "Update official Perplexity to ${version}-${revision}"
git -C "$staging_dir/aur" push origin HEAD:master
git -C "$staging_dir/aur" fetch origin master
test "$(git -C "$staging_dir/aur" rev-parse HEAD)" = \
     "$(git -C "$staging_dir/aur" rev-parse origin/master)"
git -C "$staging_dir/aur" show origin/master:.SRCINFO
