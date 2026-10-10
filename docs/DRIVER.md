# Driver behavior and options

CUPS/Ghostscript renders documents; raster-nln41 accepts CUPS, Apple URF and
PWG raster through the public libcups raster API. It does not parse PDF itself.
1/8-bit K/W/sGray and 8-bit RGB/sRGB chunked streams at 203x203 dpi are supported.
CMYK, planar, 16-bit, duplex, wrong DPI and excessive dimensions fail clearly.

Each page is fully read/checked, converted to one-bit, optionally rotated,
mirrored/negated and written as SIZE, sensing/settings, CLS, BITMAP and PRINT.
TSPL 0 means black, 1 means white; MSB is the leftmost pixel. Row stride is
handled separately from active width; padding to whole bytes is always white.
Max output: 864x2400 dots. Gray error state resets between pages.

| Option | Values / default |
| --- | --- |
| nln41-mode | DriverDefault on server (Gray by default); advanced BlackWhite option forces threshold |
| Dither | FloydSteinberg default; Threshold; Ordered (Bayer 8x8) |
| Threshold | 1..255, default 128; only Threshold uses it |
| PageSize | Default 4x6; 101x152mm.Fullbleed and small label sizes in PPD |
| Resolution | 203dpi only |
| PrintSpeed | None default (preserve device setting), or 2..5 inch/s |
| PrintDarkness | None default (preserve), or 0..15 |
| PaperType | 1 default (GAP), 2 (BLINE), 3 (continuous), None (preserve) |
| GapLength | 0..10 mm, default 2 |
| FowardOffset | -30..30 mm, default 0; spelling retained for compatibility |
| ShiftMove | -12..12 mm, default 0; TSPL horizontal shift |
| Orientation | 0 default; 1/2/3 are extra clockwise 90/180/270 degrees |
| MirrorImage / NegativeImage | False default; True supported |
| PostAction | 1 default (tear); None/0 disable; cutter/peel disabled |

Standard landscape/orientation-requested is handled by the upstream renderer.
Do not apply extra rotation twice. A 4x6 portrait page rotated 90 degrees would
be 6 inches wide and is correctly rejected. Margins are not silently shifted;
nonzero input margins fail. Default full-bleed output respects the label size.

Gray uses serpentine Floyd-Steinberg, including original near-white shades.
It does not detect/clean backgrounds or vary individual dots' heat. Black &
White uses threshold conversion even for a gray photo. Per-job nln41-mode
wins over Dither; DriverDefault preserves that advanced setting.

Copies are 1..999. A raster header NumCopies >1 wins; otherwise argv copies is
used. Copies are not multiplied. Each bitmap uses PRINT 1,N, giving A,A,B,B
for multiple pages. Collate=True with copies>1 is unsupported; submit repeated
one-copy jobs for A,B,A,B. Confirm actual counts if an upstream client expands
copies into repeated raster pages.

Original input problems produce CUPS ERROR diagnostics and nonzero exit.
A malformed later page cannot undo earlier pages already printed. Hardware
feed alignment, sensor mode, thermal paper, roller/head condition and darkness
still affect physical results; software cannot correct mechanical faults.
