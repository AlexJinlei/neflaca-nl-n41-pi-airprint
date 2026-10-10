# Pi installation — NefLaca NL-N41 Pi AirPrint v0.6.2

Install this package **on the Pi**. You do not install it on the Mac or phone.
This guide assumes the extracted installation ZIP; `src/` below is its complete
source project. In a GitHub source checkout, the `.run` is under packages/.

## Before installing

You need Raspberry Pi OS 64-bit / Debian ARM64 with CUPS 2.x, sudo access, a
powered-on NefLaca NL-N41 attached by USB, label stock, a LAN connection, and
internet for distribution dependencies. Debian 12/13 is the binary ABI baseline.
A Mac, vendor driver and SSH are not required for direct Pi installation.

Check `uname -m`: it must say `aarch64`. Use 64-bit Raspberry Pi OS, not 32-bit
OS on a 64-bit board. The Pi should remain powered on while clients print.

## Download, extract and run

Download nln41-pi-airprint-v0.6.2.zip from the project's Release. Extract it on
the Pi using the file manager or unzip, then open a terminal in the extracted
nln41-pi-airprint-v0.6.2 folder. Keep the `.run` intact; do not edit it as text.

```sh
sudo sh ./nln41-pi-airprint-v0.6.2.run
```

Enter the Pi administrator password if requested; password characters may not
appear. Wait for **Installation complete. Capability check: PASS**.
No test label prints automatically. The summary shows the actual current Pi
address/URI for manual fallback; the address is not a built-in default.

The `.run` is a shell installer with an embedded compressed payload. It checks
that payload's SHA256 before extraction. It installs distribution dependencies,
checks the ARM64 filter can load, detects USB, creates/upgrades NLN41, applies
Gray/4x6/2 mm gap/one-copy defaults and configures CUPS/Avahi sharing. It stops
and disables p910nd because it must not compete for the USB printer.

Add clients using [CLIENT-SETUP.md](CLIENT-SETUP.md). Ordinary AirPrint uses
Gray for images and binary labels; there is no custom Gray/Black & White menu.
No Mac setup script is included or needed. If your Mac asks about an unsigned
vendor installer, cancel it: the Pi-only workflow does not need that installer.

## Check the installed driver and submit a label

From this installation folder, on the Pi:

```sh
lpstat -p NLN41 -v
lpoptions -p NLN41 -l
sha256sum src/bin/linux-aarch64/raster-nln41 /usr/lib/cups/filter/raster-nln41
```

The USB URI should identify your actual printer. The two driver hashes should
match. Dither should mark FloydSteinberg as the default. Submit tests separately
and wait for each to finish:

```sh
lp -d NLN41 -n 1 -o PageSize=4x6 src/tests/test-label.ps
```

```sh
lp -d NLN41 -n 1 -o PageSize=4x6 src/tests/grayscale-label.ps
```

Each command requests one label. The supplied grayscale pattern is not a
scannable logistics barcode; test/scan your own shipping label separately.
Capability PASS checks declared formats/resolution, not physical paper output.

## Several printers, upgrades and options

A queue with pending jobs must finish or have its jobs cancelled before upgrade.
A same-name queue for another device is left unchanged. With several NL-N41s,
get the actual URI from `sudo lpinfo -v` and pass it explicitly:

```sh
sudo sh ./nln41-pi-airprint-v0.6.2.run --uri 'usb://NefLaca/NL-N41?serial=YOUR_SERIAL'
```

Use the complete URI reported on your Pi; YOUR_SERIAL is a placeholder.
`--queue` chooses a queue name, `--no-apt` is for already-installed dependencies,
and `--print-test` explicitly requests a label after success. `--help` lists
options. A normal rerun upgrades the matching queue and saves a new snapshot.
Download and run a newer release for future upgrades; there is no background
self-updater. The Pi's hostname can keep discovery stable if DHCP changes its IP.

## Paths and rollback

| Item | Installed location |
| --- | --- |
| ARM64 filter | /usr/lib/cups/filter/raster-nln41 |
| Installable Pi PPD | /usr/share/ppd/nln41/NL-N41.ppd |
| Active CUPS PPD | /etc/cups/ppd/NLN41.ppd for the default queue |
| Logs and snapshots | /var/lib/nln41-arm64-driver/oneclick/ (root only) |
| Persistent rollback helper | /usr/local/sbin/nln41-rollback |

The installer changes server-wide sharing, including DNS-SD subtypes; other
queues stay intact but their discovery can change. It shares on the intended
local network. No cloud or router port-forwarding is required.

After finishing or cancelling pending jobs:

```sh
sudo /usr/local/sbin/nln41-rollback
```

This restores the latest installation's previous driver/PPDs, queue URI,
description/options/states, cupsd.conf and service states. A freshly created
queue is removed. Dependency packages and apt side effects are retained. Pi
rollback does not delete client queues on Macs/phones. The helper survives
removing the downloaded ZIP. Do not delete its snapshot directory first.
Configuration failures after file replacement attempt automatic recovery.
See [ONECLICK.md](ONECLICK.md) for installer internals.

## Inspect, verify and rebuild

The outer ZIP includes CONTENTS-SHA256SUMS. From its extracted folder:

```sh
sha256sum -c CONTENTS-SHA256SUMS
```

This detects altered files, not the publisher's identity. The Release's
SHA256SUMS separately covers the ZIP and `.run`. To inspect the embedded source
without installing (also works on a Mac):

```sh
sh ./nln41-pi-airprint-v0.6.2.run --extract inspect
```

Normal installation uses the compiled filter; full source is included so users
can inspect, rebuild and maintain it. For a native rebuild, use the instructions
in src/docs/BUILD.md. No vendor installer/source/executable is bundled.
