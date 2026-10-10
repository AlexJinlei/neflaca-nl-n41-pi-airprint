#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
backup=/var/lib/nln41-arm64-driver/backup
[ -f "$backup/state" ] || { echo 'No recorded installation; nothing changed.'; exit 0; }
echo 'Remove queues using raster-nln41 before running rollback (see README).'
for kind in filter ppd; do
 case "$kind" in filter) target=/usr/lib/cups/filter/raster-nln41 ;; ppd) target=/usr/share/ppd/nln41/NL-N41.ppd ;; esac
 if [ -f "$backup/$kind" ]; then cp -p "$backup/$kind" "$target"; else rm -f "$target"; fi
done
rm -f "$backup/state" "$backup/filter" "$backup/ppd" "$backup/filter.absent" "$backup/ppd.absent"
rmdir "$backup" 2>/dev/null || true
rmdir /var/lib/nln41-arm64-driver 2>/dev/null || true
rmdir /usr/share/ppd/nln41 2>/dev/null || true
echo 'Filter and PPD restored/removed. Existing vendor driver files were not touched.'
