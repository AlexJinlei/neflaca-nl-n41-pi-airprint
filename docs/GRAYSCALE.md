# Gray and Black & White

Gray is the default. It uses the source's original intensity and serpentine
Floyd-Steinberg diffusion to represent gray by black-dot density. The NL-N41
still receives one-bit TSPL, not variable-heat eight-bit pixels.

There is no near-white cutoff or background-cleaning algorithm. A slightly
gray source background can produce sparse black dots. A mathematically white
source background remains white. Pure binary labels work in Gray too.

The PPD asks the document renderer for 8-bit sGray. The filter accepts existing
one-bit streams, but cannot recover gray lost upstream. Ordinary PDF input can
be rendered to gray by CUPS/Ghostscript on the Pi.

Black & White uses Threshold (default 128) even for gray photos. Ordered Bayer
8x8 is an advanced alternative. Every mode preserves width padding, uses the
same transforms/copies logic and validates real input failures.

Example from the source project root:

```sh
lp -d NLN41 -n 1 -o PageSize=4x6 tests/grayscale-label.ps
lp -d NLN41 -n 1 -o PageSize=4x6 -o nln41-mode=BlackWhite tests/grayscale-label.ps
```

Both installers apply server nln41-mode=DriverDefault and Dither=FloydSteinberg.
Ordinary AirPrint clients use the Pi Gray default; there is no custom mode menu.
Advanced filter/PPD options remain available for local development.
