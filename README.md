# NefLaca NL-N41 Pi AirPrint

Turn a **NefLaca NL-N41** USB thermal label printer into a shared network printer
with a Raspberry Pi. Install on the Pi once, then print from a Mac or iPhone
using built-in AirPrint support. The project repository name is
**`nln41-pi-airprint`**. Current release: **v0.6.2**.

[Detailed user guide](docs/USER-GUIDE.md) ·
[Client setup](docs/CLIENT-SETUP.md) · [GitHub publishing](docs/PUBLISHING.md)

## Why I made this

I own a **NefLaca NL-N41, a 203 dpi direct-thermal label printer**. I wanted to
print shipping labels from different computers and my phone without installing
a vendor driver on every device, while keeping the existing USB printer useful.

My first setup used a Raspberry Pi as a network-to-USB bridge. It moved the
bytes successfully, but the computer still needed a driver to turn a PDF into
printer commands. The macOS package I examined contained an x86_64 filter;
that executable could not run natively on Raspberry Pi OS 64-bit / Linux ARM64.

I therefore developed an independent CUPS raster-to-TSPL filter that runs on
the Pi. CUPS prepares the document, the filter creates the printer's bitmap,
and the Pi sends TSPL over USB. Clients see a shared AirPrint/IPP printer.

The final user workflow is deliberately simple: **Gray is the default for both
grayscale pictures and ordinary black-and-white labels.** There is no custom
Gray / Black & White menu to choose in the normal AirPrint path. This worked
for grayscale pictures and barcode labels in my tests, so I kept that workflow.

## Quick start

1. Download [the Pi installation ZIP](packages/nln41-pi-airprint-v0.6.2.zip)
   from this repository or its GitHub Release. Extract it on the Pi.
2. Connect the powered-on NL-N41 to the Pi by USB. Open a terminal in the
   extracted installation folder and run:

   ```sh
   sudo sh ./nln41-pi-airprint-v0.6.2.run
   ```

3. Wait for **Capability check: PASS**. Installation does not print a label.
4. On a Mac on the same LAN, open **System Settings > Printers & Scanners >
   Add Printer**, select **NefLaca NL-N41 AirPrint @ your Pi**, keep the
   automatically selected Use setting, and click Add.
5. Print a correctly sized label: **4x6 inches, one copy**. Use fit-to-page if
   needed and review the preview before printing.

No vendor driver, Mac installer or Mac setup script is required for this path.
Use may show AirPrint or **NefLaca NL-N41 independent TSPL driver**; the name
comes from the Pi. On the verified Mac, the generated PPD's nickname ends in
`-AirPrint`, supports PDF/JPEG/URF, and does not call `raster-nln41` locally.
See [client setup](docs/CLIENT-SETUP.md) for manual fallback and Windows/Linux.

The displayed IP is read from the Pi at install time. There is no built-in
personal IP, username or USB serial. The printer serial is discovered via USB.
The Pi must remain powered on and connected for remote printing.

## Compatibility

| Component | Supported scope and evidence |
| --- | --- |
| Brand / model | **NefLaca NL-N41**, USB `2aaf:9006`, TSPL, 203 dpi |
| Print server | Raspberry Pi OS 64-bit / Debian ARM64, CUPS 2.x; Debian 12/13 ABI baseline |
| Tested server hardware | Raspberry Pi 4; other ARM64 boards are not physically verified |
| macOS | Pi clean install, automatic discovery/addition and Gray/barcode output reported successful with v0.6.1 |
| iPhone / iPad | iPhone printing with Gray defaults reported working in preceding versions; iPad not separately tested |
| Windows | Windows 11 IPP setup documented; not physically verified, no Mopria certification claim |
| Linux desktop | CUPS driverless/IPP setup documented; not physically verified |
| Label stock | Default 4x6 inches / 101.6x152.4 mm; gap 2 mm |

The compiled filter is Linux AArch64, not a macOS executable. 32-bit Pi OS,
CUPS 3, other printer models, other DPI, duplex, cutters/peelers and hardware
status polling are outside the supported scope. Maximum output is 864x2400
dots. Send an A4/Letter document only after scaling it to the actual label.

## What installation does

- Installs Debian/Raspberry Pi OS packages using apt; internet is needed for
  missing dependencies. It does not require local compilation.
- Detects the printer, installs the compiled filter and Pi PPD, creates or
  upgrades the `NLN41` USB queue, and sets Gray / 4x6 / one-copy defaults.
- Stops/disables p910nd to prevent USB contention, enables CUPS/Avahi sharing,
  and checks advertised PDF/URF/PWG/203 dpi capabilities.
- Refuses to replace a busy queue or a same-name queue for another device.
- Saves a rollback snapshot. Shared-server settings affect all shared queues
  on that Pi; use the installer on the intended LAN print server.

Rollback on the Pi, after finishing or cancelling pending jobs:

```sh
sudo /usr/local/sbin/nln41-rollback
```

It restores the latest installation's prior driver, queue/defaults/description,
sharing and service states. Dependency packages stay installed. A clean
installation's new queue is removed. [Installation details](docs/INSTALL-PI.md)
explain paths, logs, upgrades, recovery and the difference from a clean OS test.

## Rendering

Gray uses serpentine Floyd-Steinberg halftoning and preserves source intensity.
The thermal printer receives black/white dots that visually represent gray.
Pure black/white source pixels work in the same mode. No near-white background
cleanup is applied: a faint gray image background may produce sparse dots.
Source artwork, scaling and the 203 dpi printhead all affect barcode quality;
scan a real printed barcode separately before relying on it.

Advanced local filter options remain in the source for development. They are
not added to the ordinary AirPrint client interface in this distribution.

## Package and source

The Pi ZIP includes the `.run`, English installation guides,
client/troubleshooting documentation, LICENSE, integrity manifest, and `src/`
with the complete project: C source, precompiled ARM64 filter, PPDs, Makefile,
build/test scripts and install/rollback tools. The `.run` embeds the same source
for inspection; normal installation uses the precompiled executable.

The repository also includes `packages/` with the ready-to-download ZIP, `.run`
and SHA256SUMS. Repository package links in this README refer to that folder;
the offline installer's source copy excludes nested package archives.

For a build: [BUILD.md](docs/BUILD.md). For validation and its limits:
[TESTING.md](docs/TESTING.md). To regenerate the Pi package:
`python3 scripts/build-release.py`.

## Independent implementation and license

MIT license: [LICENSE](LICENSE). This project contains an independently written
filter, not vendor source or proprietary driver executables. Reference package
interfaces and controlled output samples informed behavior; this was not a
formally separated two-team clean-room process. See
[reference analysis](docs/REFERENCE-ANALYSIS.md).

NefLaca and NL-N41 identify the tested printer brand and model. This is a
community project, not an official NefLaca driver or an Apple-certified product.
