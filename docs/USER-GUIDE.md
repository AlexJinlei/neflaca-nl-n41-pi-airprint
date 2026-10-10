# User guide — NefLaca NL-N41 Pi AirPrint

## The printing path

Mac / phone / IPP client → Pi CUPS → raster-nln41 → TSPL → USB NL-N41.
Install only on the Pi. The printer remains a USB device; the Pi provides its
network endpoint and performs conversion. The Pi and printer must be powered on.

The printer brand is **NefLaca**, the model **NL-N41**, and the printhead is
203 dpi. The default queue is NLN41. Display name:
NefLaca NL-N41 AirPrint @ <your Pi's server name>.

## First installation

Read [INSTALL-PI.md](INSTALL-PI.md), connect USB and run the included `.run`
on the Pi. Wait for capability PASS. Then add the discovered printer on your
client using [CLIENT-SETUP.md](CLIENT-SETUP.md). Start with a known 4x6 PDF,
one copy, and correct label stock. Setup does not print anything automatically.

No user/IP/serial is prefilled. The fallback address printed by setup comes from
the Pi at that time; if its IP later changes, use discovery or its current
hostname/address. Choose the interface on the same LAN if several are shown.

## Day-to-day printing

- Choose the NL-N41 AirPrint printer and **4x6 inches** paper.
- Begin with one copy and check the preview: correct rotation, complete label,
  useful margins and no cropping. Fit a differently sized page to label stock.
- Gray is already the default. Print grayscale pictures and black/white labels
  through the same queue. No custom rendering-mode menu is needed or shown.
- Use app Default Settings during the first test instead of an old saved preset.
  A client preset can override paper, orientation, scaling or other job options.
- Wait for a job to finish before submitting another during diagnosis. Unplugging
  or powering off the Pi prevents clients from reaching this USB printer.

Do not treat a successful submission as proof of good barcode output. Test a
real printed barcode with its intended scanner; source size, antialiasing,
scaling, stock and printhead condition matter at 203 dpi.

## Why grayscale prints on a black/white thermal printer

The filter represents gray with a pattern of black/white dots using serpentine
Floyd-Steinberg error diffusion. Pure black/white source pixels also work in
this mode. No background whitening is applied. Sparse dots around an image
can be a faithful rendering of a near-white gray source background.

A client's Black and White checkbox/preset can mean monochrome printing; it
is not this project's advanced threshold algorithm selector. The supported
simple workflow leaves the Pi at its Gray default.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No printer in the list | Pi/printer power; same LAN; no guest Wi-Fi isolation; CUPS and Avahi running; manual IPP fallback |
| Bonjour Shared / Generic PostScript | Check the Pi subtype list; it should omit _cups; close/reopen Add Printer after an upgrade |
| Use shows the Pi driver name | This can be normal: the verified Mac generated a -AirPrint client PPD; the Linux filter stays on the Pi |
| Phone lists old NLN41 and new NefLaca NL-N41 AirPrint | A Known Printers entry can reflect the previously used name; select the new entry and verify live Pi queues before deleting anything |
| No Gray / Black & White menu | Expected in ordinary AirPrint; Gray is the default and handles binary labels |
| Rotated output exceeds size | Select 4x6 and review scaling/orientation; avoid a full-size Letter/A4 page or extra bitmap rotation |
| Stopped on server / no output | Inspect the Pi queue and CUPS log; capability PASS does not check paper output |
| Slow first job | Check rendering and USB/service status; p910nd must not hold the USB printer |
| Light dots / white holes in black areas | Check source data first, then stock/printhead/roller; software success does not establish physical print quality |

Useful Pi checks:

```sh
lpstat -p NLN41 -l
lpstat -W not-completed -o NLN41
systemctl is-active cups avahi-daemon p910nd
sudo cupsctl | grep -E 'Browse(LocalProtocols|DNSSDSubTypes)'
sudo tail -n 80 /var/log/cups/error_log
```

CUPS/Avahi should be active and p910nd inactive (or absent).
The subtype list should contain _print,_universal without _cups.
For detailed filter errors see [ERRORS.md](ERRORS.md). If more detail is needed,
enable `sudo cupsctl --debug-logging`, reproduce one job, inspect the log, then
turn it off using `sudo cupsctl --no-debug-logging`. Logs can contain names,
filenames and printer identifiers; remove personal data before sharing them.

## Recovery and separate install tests

For rollback, use `sudo /usr/local/sbin/nln41-rollback` after completing or
cancelling pending jobs. It restores the latest Pi snapshot and keeps apt
packages. Remove client queues separately in their settings if needed.

A queue/file cleanup on an existing OS tests driver installation from empty
project state, but does not prove first installation of dependencies. To test
that case, use a freshly written 64-bit Raspberry Pi OS SD card; preserve your
working card. For an existing setup, [CLEAN-TEST.md](CLEAN-TEST.md) describes a
scoped cleanup. Do not erase all CUPS configuration or other printers.

## Package contents

The install ZIP contains the `.run`, README, detailed English docs,
LICENSE, CONTENTS-SHA256SUMS and full source under src/. Normal installation
uses the included ARM64 binary. Source is there for audit and maintenance,
not a requirement to compile during installation. The self-extracting `.run`
contains the same complete project and can be inspected with --extract.

## Phone shows an old and a new printer name

After a queue/service is renamed, a phone can show the previous name under
Known Printers and the current name under Other Printers. The original user
observed NLN41 and NefLaca NL-N41 AirPrint with the same Pi host. This suggests
a remembered old entry plus a newly discovered service; the screenshot alone
does not prove two active Pi queues. Select the current AirPrint name.

To check the live server, run on the Pi:

```sh
lpstat -p -v
sudo grep -RlE 'NLN41|NL-N41|printers/NLN41' /etc/avahi/services
```

One queue suggests there is no duplicate CUPS destination. A static Avahi file
may still advertise a second service; inspect any result before removing it.
No output from the second command is normal for this installer, which uses
CUPS' own dynamic advertisement. Close/reopen the phone print dialog after
selecting the new service. Do not delete a working queue based only on names.
