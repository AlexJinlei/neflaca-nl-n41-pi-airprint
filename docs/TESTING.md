# Tests and hardware validation

## Filter evidence retained without changes

The C filter source and stripped ARM64 ELF are byte-identical to v0.6.1.
The inherited v0.6.0 native macOS ARM64 CUPS/Clang test run included 584 filter
invocations: CUPS/PWG/URF, compressed/uncompressed, 1/8-bit K/W/sGray and 8-bit
RGB/sRGB, row padding, multiple pages, copies, rotations/mirror/negative,
Gray monotonicity, original near-white density, threshold options and actual
failure handling. The old v0.5.3 suite also passed ASan/UBSan; no new sanitizer
run is claimed. The shipping filter/installers use public CUPS APIs.

## v0.6.2 local release checks

- 11 simulated Pi installation/rollback tests, including USB discovery,
  fresh/upgrade paths, prior description/default restoration, failure recovery,
  other-device and pending-job protection. No real services are modified.
- Both source PPDs checked using cupstestppd; the existing 4x6 Adobe-name warning
  remains. The historical network PPD stays for regression inspection only.
- .run help/extraction; source/payload/outer ZIP manifests; ELF architecture and
  preserved binary hash; normalized tar ownership/time; archive integrity.
- English document links and public privacy/content audit.
- `make test` remains available for developer rebuilds. No Mac installer is built.

## Physical evidence reported by the user

On 2026-10-10, v0.6.1 was tested after removing the Pi queue, filter and installer
state. Installation reached capability PASS. Mac discovered the printer without
manual IP/queue entry or a Mac script. Its generated PPD nickname ended in
-AirPrint and advertised PDF/JPEG/URF with pass-through filter rules rather than
raster-nln41. The user then reported grayscale and barcode labels printing
normally. Earlier versions also printed from an iPhone with Gray defaults.

Version v0.6.2 changes packaging/documentation, version labels and setup summary
wording. It retains the verified rendering binary and server configuration
behavior. A new v0.6.2 hardware test, Windows/Linux client tests, other boards,
advanced client number-up/layout and live rollback are not claimed.

## Repeat on your own printer

Install, confirm capability PASS, add the discovered printer, then print one
4x6 label and one grayscale image. Check sheet count, preview/orientation,
complete borders, gray tones, feed/gap and black/white polarity. Scan a real
shipping barcode separately. The supplied test patterns are not logistics codes.

For Pi tests in the source checkout:

```sh
lp -d NLN41 -n 1 -o PageSize=4x6 tests/test-label.ps
lp -d NLN41 -n 1 -o PageSize=4x6 tests/grayscale-label.ps
```

In an installer folder prepend src/ to the test paths. Submit separately and
wait for each to finish. Check `lpstat -W not-completed -o NLN41` and the CUPS
error log if anything stops. Finish/cancel jobs before rollback. A passed
capability check alone is not proof of paper output. See CLEAN-TEST.md for
empty-project versus clean-OS testing.
