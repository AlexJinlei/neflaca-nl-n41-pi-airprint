#!/bin/sh
# Debian 12+ ARM64 ABI baseline. Supply a Zig compiler and extracted Debian sysroot.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
: "${ZIG:?Set ZIG to an absolute path to zig 0.14.1}"
: "${CUPS_SYSROOT:?Set CUPS_SYSROOT to extracted ARM64 libcups2-dev, libcupsimage2-dev and libcups2 packages}"
mkdir -p bin/linux-aarch64
"$ZIG" cc -target aarch64-linux-gnu.2.36 -O2 -std=c11 \
 -Wall -Wextra -Wpedantic -Wno-deprecated-declarations \
 -I "$CUPS_SYSROOT/usr/include" src/raster-nln41.c \
 "$CUPS_SYSROOT/usr/lib/aarch64-linux-gnu/libcups.so.2" \
 -ffile-prefix-map="$PWD"=. -fdebug-prefix-map="$CUPS_SYSROOT"=/sysroot \
 -Wl,--strip-all -Wl,--allow-shlib-undefined -lm -o bin/linux-aarch64/raster-nln41
file bin/linux-aarch64/raster-nln41
