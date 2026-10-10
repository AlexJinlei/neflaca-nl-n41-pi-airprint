# Changelog

## 0.6.2 — NefLaca NL-N41 Pi AirPrint public package

- Publish one Pi installer and a complete source tree under nln41-pi-airprint.
- Add detailed English usage, project motivation, hardware brand/model,
  client setup, troubleshooting, rollback and GitHub publishing instructions.
- Document verified automatic Mac discovery: Use can show the Pi model name;
  the generated client PPD uses built-in AirPrint and does not run raster-nln41.
- Keep Gray as the single normal client workflow for photos and binary labels.
- Remove the Mac installer from this distribution. Preserve driver algorithms,
  ARM64 binary and server configuration behavior from 0.6.1.
- Record user-reported 0.6.1 clean-install, automatic discovery and successful
  grayscale/barcode printing; do not claim a new 0.6.2 hardware test.

## 0.6.1 — Automatic AirPrint discovery

- Advertise CUPS queues with _print,_universal and omit _cups so macOS can
  select AirPrint rather than treating the printer as Bonjour Shared.
- Set the Pi queue description to NefLaca NL-N41 AirPrint; preserve the old
  description for rollback. CUPS adds its normal server-name suffix.
- Make list-based Mac setup the first path; retain manual IPP as a fallback.
- Retain the same ARM64 binary and Gray default. No raster algorithm changes.
- Live Mac discovery still requires verification on the user's LAN.

## 0.6.0 — Public distribution

- Package Pi-direct and Mac-to-Pi installation together in one public source tree.
- Require the user's own Pi SSH login; remove personal address/user defaults.
- Include MacBook/Windows/Linux client setup and macOS blocked-script instructions.
- Strip ARM64 debug paths and normalize payload archive ownership metadata.
- Use synthetic device identifiers in tests; omit private artwork/attachments.
- Include project purpose, compatibility, MIT license, build/rollback/test and
  GitHub publishing instructions. Add a package builder for both installation ZIPs.
- Preserve preceding 0.5.4 Gray defaults and driver behavior; no new raster or
  printer protocol algorithm is introduced in this release.

Pre-public builds established USB/TSPL conversion, Gray halftoning, per-job modes,
threshold conversion, original near-white rendering and shared-client printing.
Private experimental packages are not part of this repository's public history.
