#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
backup=/var/lib/nln41-arm64-driver/network-backup
queue=$(cat "$backup/queue")
lpadmin -p "$queue" -P "$backup/queue.ppd"
install -m 755 "$backup/filter" /usr/lib/cups/filter/raster-nln41
install -m 644 "$backup/cupsd.conf" /etc/cups/cupsd.conf
cupsd -t
systemctl restart cups
echo "Restored filter, queue PPD and CUPS sharing configuration. Prior options are in $backup/options.txt."
