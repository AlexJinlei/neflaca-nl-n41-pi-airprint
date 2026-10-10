#!/bin/sh
# Enable the existing USB queue's tested raster formats and CUPS DNS-SD sharing.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
queue=${1:-NLN41}
case "$queue" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid queue name.' >&2; exit 1;; esac
lpstat -p "$queue" >/dev/null
[ -z "$(lpstat -W not-completed -o "$queue")" ] || { echo "Queue has pending jobs; finish or cancel them first." >&2; exit 1; }
for tool in ipptool python3 cupsd; do command -v "$tool" >/dev/null || { echo "Missing $tool: install cups-ipp-utils python3 cups-daemon." >&2; exit 1; }; done
backup=/var/lib/nln41-arm64-driver/network-backup
if [ ! -d "$backup" ]; then
 install -d -m 700 "$backup"
 cp -p /etc/cups/cupsd.conf "$backup/cupsd.conf"
 cp -p "/etc/cups/ppd/$queue.ppd" "$backup/queue.ppd"
 cp -p /usr/lib/cups/filter/raster-nln41 "$backup/filter"
 lpoptions -p "$queue" > "$backup/options.txt"
 printf '%s\n' "$queue" > "$backup/queue"
fi
[ "$(cat "$backup/queue")" = "$queue" ] || { echo 'Backup belongs to a different queue.' >&2; exit 1; }
./install.sh --prebuilt
lpadmin -p "$queue" -P /usr/share/ppd/nln41/NL-N41.ppd \
 -o PageSize=4x6 -o Orientation=0 -o MirrorImage=False -o NegativeImage=False \
 -o nln41-mode=DriverDefault -o Dither=FloydSteinberg \
 -o cm-calibration-default=true -o printer-is-shared=true
systemctl enable --now avahi-daemon
cupsctl --share-printers BrowseLocalProtocols=dnssd BrowseDNSSDSubTypes=_print,_universal
cupsd -t
systemctl restart cups
ipptool -tv "ipp://localhost:631/printers/$queue" tests/network-attributes.test
printf '\nNetwork configuration complete. Re-add this printer on the Mac and select AirPrint.\n'
