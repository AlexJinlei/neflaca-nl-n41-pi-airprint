# Build and binary provenance — 0.6.2

## Native build on the Pi

Install the distribution's development dependencies, then build/test:

```sh
sudo apt install build-essential libcups2-dev libcupsimage2-dev python3 cups-client
make
make test
```

The Makefile uses cups-config and public libcups raster/PPD APIs, linking
-lcups -lm. It does not copy a CUPS raster implementation or require a separate
vendor library. CUPS 2.x PPD APIs are deprecated but still used for this release.
The project does not implement CUPS 3 Printer Application support.

Optional file-only install: `sudo ./install.sh`; compiled binary install:
`sudo ./install.sh --prebuilt`. These do not set up a queue/sharing. Use the
.run installer for the complete installation and its matching rollback.

## Included Linux ARM64 filter

Built on macOS ARM64 using official Zig 0.14.1 and Debian 12 ARM64 CUPS
2.4.2-3+deb12u9 headers/linking library, targeting aarch64-linux-gnu.2.36.
Debian 12/13 is the recommended ABI baseline. The executable depends on the
Pi's system dynamic loader, libc, libm and libcups, not bundled copies.
The installer checks loading/usage before replacing driver files.

SHA256 (0.6.2):
`044f128924b4c4a25655ada9adf68eb60b5614ba2aded55fb0862b1fdb918ff4`

ELF64 little endian, AArch64 (183), /lib/ld-linux-aarch64.so.1. Direct dependencies:
libcups.so.2, libm.so.6, libc.so.6. Referenced glibc versions include 2.17 and
2.34. It is stripped of debug metadata and local build paths. See
elf-inspection.json. The macOS development host cannot run this Linux ELF;
the user separately reported successful v0.6.1 clean installation on the Pi,
automatic Mac discovery/addition and grayscale/barcode output with this same
binary. Local source tests and hardware reports are distinct evidence.

## Cross-build

Provide your own Zig executable and an extracted Debian ARM64 sysroot:

```sh
ZIG=/path/to/zig CUPS_SYSROOT=/path/to/arm64-sysroot ./scripts/cross-build.sh
python3 scripts/inspect-elf.py bin/linux-aarch64/raster-nln41
```

The script strips the executable and maps source paths. No credentials or
local default paths are written to the binary. Native builds may include
debug information; use the stripped cross-build or an appropriate target
strip tool before publishing those binaries.

Reference downloads and measured SHA256 values:

| Input | SHA256 |
| --- | --- |
| zig-aarch64-macos-0.14.1.tar.xz | 39f3dc5e79c22088ce878edc821dedb4ca5a1cd9f5ef915e9b3cc3053e8faefa |
| libcups2-dev_2.4.2-3+deb12u9_arm64.deb | 40e5d3508a8dea0f55277015b9193b93bb7c89ad44c481b356cff0685b1f6a0c |
| libcupsimage2-dev_2.4.2-3+deb12u9_arm64.deb | 10aea22bb1e3492c72982c64e7795ee934daaf197aaf73a7fe42b06bf0da9c34 |
| libcups2_2.4.2-3+deb12u9_arm64.deb | 41c9220d57d9eb3b5245f17038c830053f12176f6eef611c6f6941fcbf6d507f |

Sources: [Zig 0.14.1](https://ziglang.org/download/0.14.1/),
[Debian CUPS pool](https://deb.debian.org/debian/pool/main/c/cups/),
[CUPS raster API](https://openprinting.github.io/cups/doc/api-raster.html).
These are measured content hashes, not a separate publisher-signature audit.
Compiler/sysroot packages are not included in this release.

## Rebuild the installation packages

```sh
python3 scripts/build-release.py
```

This updates the source SHA256SUMS and creates packages/nln41-pi-airprint-v0.6.2.run,
the Pi installation ZIP, and packages/SHA256SUMS. The ZIP has full source in src/;
its .run embeds the same source/binary payload. No Mac installer is built.
Build/cache/git/package/work output folders are excluded; tar owners/timestamps
are normalized. SHA256 detects content changes, not publisher identity. Update
this document if you change the ARM64 binary. For a browser-uploaded GitHub
checkout, preserve executable modes with Git, or invoke .sh/.py files with
sh/bash/python3 as appropriate instead of relying on their execute bits.
