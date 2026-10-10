#!/usr/bin/env python3
"""Build an auditable, offline-payload self-extracting installer."""
import hashlib
import gzip
import io
from pathlib import Path
import tarfile
import sys
BASE = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE.parent / 'nln41-pi-airprint-v0.6.2.run'
stream = io.BytesIO()
with tarfile.open(fileobj=stream, mode='w') as t:
    for p in sorted(BASE.rglob('*')):
        rel = p.relative_to(BASE)
        if p.is_file() and not p.is_symlink() and not any(x in rel.parts for x in ['build', '__pycache__', '.git', 'packages', 'dist', 'work']) and p.name != '.DS_Store':
            # Do not expose build-host usernames, groups or timestamps.
            info = t.gettarinfo(str(p), arcname=str(Path('nln41-pi-airprint') / rel))
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
            info.mtime = 0
            info.pax_headers = {}
            with p.open('rb') as f:
                t.addfile(info, f)
payload = gzip.compress(stream.getvalue(), mtime=0)
digest = hashlib.sha256(payload).hexdigest()
header = r'''#!/bin/sh
# NL-N41 0.6.2 -- embedded independent ARM64 driver, no remote code downloads.
set -eu
export LANG=C LC_ALL=C
case "${1:-}" in
 --help|-h)
  cat <<'HELP'
NL-N41 One-Click Installer 0.6.2
Install: sudo sh ./nln41-pi-airprint-v0.6.2.run
Print a test label: sudo sh ./nln41-pi-airprint-v0.6.2.run --print-test
Multiple printers: add --uri 'usb://NefLaca/NL-N41?serial=...'
Extract only: sh ./nln41-pi-airprint-v0.6.2.run --extract destination-directory
Rollback: sudo /usr/local/sbin/nln41-rollback
Requires Debian / Raspberry Pi OS ARM64, a USB-connected printer, and internet access to install dependencies.
HELP
  exit 0 ;;
esac
if [ "${1:-}" != --extract ]; then
 [ "$(uname -s)" = Linux ] && [ "$(uname -m)" = aarch64 ] && [ -f /etc/debian_version ] || { echo 'Raspberry Pi OS 64-bit / Debian ARM64 is required.' >&2; exit 1; }
 if [ "$(id -u)" != 0 ]; then exec sudo sh "$0" "$@"; fi
fi
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
line=$(awk '/^__NLN41_PAYLOAD__$/ {print NR + 1; exit}' "$0")
tail -n +"$line" "$0" > "$scratch/payload.tar.gz"
if command -v sha256sum >/dev/null 2>&1; then
 actual=$(sha256sum "$scratch/payload.tar.gz" | awk '{print $1}')
else
 actual=$(shasum -a 256 "$scratch/payload.tar.gz" | awk '{print $1}')
fi
[ "$actual" = __DIGEST__ ] || { echo 'Installer integrity check failed. Download the installer again.' >&2; exit 1; }
if [ "${1:-}" = --extract ]; then
 [ "$#" = 2 ] || { echo 'Usage: --extract destination-directory' >&2; exit 1; }
 mkdir -p "$2"
 tar -xzf "$scratch/payload.tar.gz" -C "$2"
 echo "Extracted to $2"
 exit 0
fi
tar -xzf "$scratch/payload.tar.gz" -C "$scratch"
if ! command -v python3 >/dev/null 2>&1; then
 apt-get update
 DEBIAN_FRONTEND=noninteractive apt-get install -y python3
fi
python3 "$scratch/nln41-pi-airprint/scripts/oneclick.py" "$@"
exit 0
__NLN41_PAYLOAD__
'''.replace('__DIGEST__', digest)
out.write_bytes(header.encode() + payload)
out.chmod(0o755)
print(out)
