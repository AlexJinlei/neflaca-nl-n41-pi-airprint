# Historical developer reference: custom desktop modes

The source retains ppd/NL-N41-Network.ppd for regression checks and inspection
of earlier custom per-job nln41-mode=BlackWhite/Gray behavior. It is not the
normal client setup for this Pi-only release. No Mac launcher is distributed.

Ordinary clients add the automatically discovered AirPrint queue and use the
Pi Gray default. The automatically generated Mac PPD does not include the
custom mode menu; grayscale images and binary labels work without it.
Do not select the Pi's NL-N41.ppd as a local Mac driver: raster-nln41 is a
Linux ARM64 executable that runs on the server.
