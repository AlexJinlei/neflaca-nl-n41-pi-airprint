#!/bin/sh
# Offline macOS reference extraction. No installer scripts are executed.
set -eu
[ "$#" = 2 ] || { echo 'Usage: analyze-pkg.sh /path/to/driver.pkg /new/output/directory' >&2; exit 1; }
pkg=$1
out=$2
[ ! -e "$out" ] || { echo 'Output directory must not exist.' >&2; exit 1; }
command -v pkgutil >/dev/null
pkgutil --expand-full "$pkg" "$out"
find "$out" -type f -name '*.ppd.gz' -exec sh -c 'for p do gzip -dc "$p" > "$p.expanded.ppd"; done' sh {} +
find "$out" -type f -name 'raster-tspl' -exec sh -c '
 for p do
  file "$p" > "$p.file.txt"
  shasum -a 256 "$p" > "$p.sha256.txt"
  strings "$p" > "$p.strings.txt"
  otool -L "$p" > "$p.imports.txt"
  otool -l "$p" > "$p.load-commands.txt"
  nm "$p" > "$p.symbols.txt"
  otool -tvV "$p" > "$p.disassembly.txt"
 done' sh {} +
echo 'Expanded and analyzed without installing. Treat extracted scripts as data.'
