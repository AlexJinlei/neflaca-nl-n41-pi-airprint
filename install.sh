#!/bin/sh
# Install only this independently named filter and PPD; does not edit queues.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
[ "$(uname -s)" = Linux ] || { echo 'Installation is for Linux only.' >&2; exit 1; }
mode=${1:-source}
case "$mode" in
 source) binary=build/raster-nln41 ;;
 --prebuilt) [ "$(uname -m)" = aarch64 ] || { echo 'Prebuilt requires aarch64.' >&2; exit 1; }; binary=bin/linux-aarch64/raster-nln41 ;;
 *) echo 'Usage: sudo ./install.sh [--prebuilt] (default: install existing local build)' >&2; exit 1 ;;
esac
[ -x "$binary" ] || { echo 'Missing binary. Run make as your normal user first.' >&2; exit 1; }
filterdir=/usr/lib/cups/filter
ppddir=/usr/share/ppd/nln41
backup=/var/lib/nln41-arm64-driver/backup
# Keep the original state of these two paths for idempotent rollback.
if [ ! -f "$backup/state" ]; then
 install -d -m 700 "$backup"
 for kind in filter ppd; do
  case "$kind" in filter) target=$filterdir/raster-nln41 ;; ppd) target=$ppddir/NL-N41.ppd ;; esac
  if [ -L "$target" ]; then echo "Refusing to replace symlink: $target" >&2; exit 1; fi
  if [ -f "$target" ]; then cp -p "$target" "$backup/$kind"; else : > "$backup/$kind.absent"; fi
 done
 printf 'v1\n' > "$backup/state"
fi
# Catch an incompatible binary or missing runtime library before replacing files.
check=$(mktemp)
trap 'rm -f "$check"' EXIT HUP INT TERM
set +e
"./$binary" 2> "$check"
status=$?
set -e
if [ "$status" != 1 ] || ! grep -q 'Usage: raster-nln41' "$check"; then
 cat "$check" >&2; rm -f "$check"
 echo 'Binary cannot execute correctly on this system; rebuild locally.' >&2; exit 1
fi
rm -f "$check"
install -d "$filterdir" "$ppddir"
install -m 755 "$binary" "$filterdir/raster-nln41"
install -m 644 ppd/NL-N41.ppd "$ppddir/NL-N41.ppd"
chown root:root "$filterdir/raster-nln41" "$ppddir/NL-N41.ppd"
echo "Installed $filterdir/raster-nln41 and $ppddir/NL-N41.ppd"
echo 'Create a new queue with lpadmin as shown in README.md.'
