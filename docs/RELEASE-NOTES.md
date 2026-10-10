# NefLaca NL-N41 Pi AirPrint v0.6.2

A Pi-only public distribution of an independent ARM64 CUPS driver for the
**NefLaca NL-N41** 203 dpi USB thermal label printer.

Install once on Raspberry Pi OS 64-bit / Debian ARM64. The Pi shares the
printer through CUPS/IPP and Bonjour discovery; verified Mac clients use
built-in AirPrint without a vendor driver or dedicated Mac setup script.

Gray is the default for grayscale pictures and black/white labels. Ordinary
AirPrint has no custom rendering-mode menu. The user reported successful
v0.6.1 clean installation, automatic Mac discovery/addition, grayscale and
barcode-label output; this release retains the same filter source and ARM64
binary while simplifying distribution and expanding documentation.

Includes the `.run`, compiled Linux AArch64 filter, complete source, PPDs,
Makefile/build/test/install/rollback scripts, English project motivation
and user guides, MacBook/Windows/Linux client setup and GitHub publishing steps.
No personal IP/login/serial, private artwork or vendor executable is bundled.
Setup checks capabilities and does not print a label automatically.

Download **nln41-pi-airprint-v0.6.2.zip** for installation, or the single `.run`
if you prefer. Both are covered by SHA256SUMS. MIT license.

Windows/Linux clients, other printer models/boards and advanced page-layout
features remain unverified. CUPS 2.x and Linux ARM64 are required. This is an
independent community project, not an official NefLaca driver.
