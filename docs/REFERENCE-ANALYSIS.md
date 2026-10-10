# Independent implementation and reference observations

A reference NL-N41 macOS driver package (version 1.3.0) was expanded offline
without running installer scripts. Its x86_64 Mach-O filter, PPD interface,
imports/symbol names and strings were inspected. Controlled CUPS raster samples
were also passed through the reference filter under an x86_64 execution path;
stdout was captured offline, not sent to a printer.

This is independently written behavioral reimplementation. It is not a formal
legal clean-room claim involving separate analyst and implementer teams. No
vendor source/function body was copied or linked. Reference installers, PPDs,
executables, disassembly and original private files are absent from this public
source distribution. Small synthetic command/output observations are retained
in vendor-observations.json for protocol evidence.

## Interface facts

The reference filter reads CUPS raster/options/PPD and emits TSPL on stdout.
Its observable commands include SIZE, GAP/BLINE, OFFSET, SHIFT, SPEED, DENSITY,
CLS, BITMAP and PRINT. It uses whole-page bitmaps. USB transport belongs to the
CUPS backend, not the raster filter. Public raster APIs are used in this driver.

Observed NL-N41 bit polarity is 0=black, 1=white (MSB-first), supported by both
controlled reference output and preceding physical tests. The independent
filter uses TSPL BITMAP mode 0, which was physically accepted by the NL-N41.
It does not aim to make output byte-identical to the vendor filter.

## Deliberate differences

- Honor active width separately from cupsBytesPerLine; reference padded-row
  samples showed undesirable stride consumption in its one-bit path.
- Interpret K versus W/sGray polarity explicitly and handle RGB luminance.
- Use exact 4x6 inch points plus explicitly named metric media; do not copy
  incorrect small-label dimensions observed in the original PPD.
- Enforce 203 dpi and the documented printhead/label-size limits.
- Round millimeters to dots for shift; track padding through all transforms.
- Respect documented header/argv copy priority rather than dropping copies.
- Use an original halftoning implementation with Gray default. Preserve source
  intensity; no near-white clipping or automatic background cleanup.
- Preserve specific CUPS ERROR diagnostics for actual input/output failures.

Reference documentation supplied 203 dpi, 50-108 mm media width, 25-300 mm
length and speed/density ranges. USB identity is 2aaf:9006 and the reported
active command set is TSPL. These identify NL-N41, not all TSPL devices.

Reference macOS package SHA256:
1c1b2e09b8cc211ea480e5ea44f14e605f9a4bc52e6388e9dacd8841fe8d1b63.
For independent reproduction with a lawfully obtained reference package,
scripts/analyze-pkg.sh extracts static data; scripts/vendor-blackbox.py captures
small synthetic samples. Neither is used during normal driver installation.

Public API reference: [CUPS Raster API](https://openprinting.github.io/cups/doc/api-raster.html).
