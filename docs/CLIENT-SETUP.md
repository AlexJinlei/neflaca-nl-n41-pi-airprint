# Add the shared printer: MacBook, Windows and Linux

Install on the Pi first. Keep it powered on and on the same LAN as the client.
At the end of installation, note the Pi's hostname/IP and the queue URI.
`<PI_HOST>` below is a placeholder: replace it with **your own** hostname or IP.
The normal queue is `NLN41`; if you chose --queue, substitute that name too.
The connection goes to the Pi, not directly to the USB printer.

The shared queue URI is `ipp://<PI_HOST>:631/printers/NLN41`. Port 631 is IPP.
Do not use a raw port-9100 / Generic Text / PCL queue for these instructions.

## MacBook / macOS

1. Open System Settings > Printers & Scanners > Add Printer.
2. In the default list, select **NefLaca NL-N41 AirPrint @ your Pi**.
3. Keep the automatically selected **Use** setting and click Add. It may show
   AirPrint or the Pi model name. No Mac installer, IP or queue entry is needed.
   In the verified setup, macOS generated an AirPrint client PPD even when Use
   displayed NefLaca NL-N41 independent TSPL driver.
4. Print a 4x6 PDF with the correct paper size and one copy.

If discovery fails, use the IP (globe) tab as a fallback:

- Address: `<PI_HOST>:631`
- Protocol: AirPrint
- Queue: `printers/NLN41`
- Name: `NefLaca NL-N41 AirPrint`
- Use: AirPrint

After upgrading from an older release, close and reopen Add Printer and allow
Bonjour to refresh. If the entry still says Bonjour Shared / Generic PostScript,
see source docs/NETWORK.md to check the server's _cups advertisement. Do not
choose Generic PostScript to work around that discovery issue.

The normal queue uses the Pi Gray default for grayscale pictures and binary
labels. There is no custom Gray / Black & White menu in this distribution.
The Linux ARM64 raster-nln41 filter executes on the Pi, not on the Mac.
The source retains a historical network PPD for developer regression checks;
it is not required for normal client setup.

## Windows 11 (24H2 or later recommended)

1. Open Settings > Bluetooth & devices > Printers & scanners > Add device.
2. Choose Add manually > Add a printer using an IP address or hostname.
3. Select **IPP Device**. Enter the full queue URL
   `ipp://<PI_HOST>:631/printers/NLN41`, rather than only the Pi's bare address.
4. Complete setup using the inbox Microsoft IPP Class Driver when available.
   Select 4x6 inches in printing preferences, then send one correctly sized PDF.

Microsoft documents this directed-IPP route and full-URL fallback in its
[IPP setup guide](https://learn.microsoft.com/universal-print/fundamentals/universal-print-connector-with-ipp).
This is a local Pi queue; **no Universal Print account or connector is used**.
The project is not Mopria-certified; this Windows route still needs testing
against the shared CUPS queue. Do not treat the instructions as certification.

Optional alternative on a system whose PrintManagement module supports
`IppURL`: open PowerShell as administrator and enter your own host:

```powershell
$piHost = Read-Host 'Pi hostname or IP'
Add-Printer -Name 'NefLaca NL-N41 AirPrint' -IppURL "http://${piHost}:631/printers/NLN41"
```

The parameter is documented in [Microsoft Add-Printer](https://learn.microsoft.com/en-us/powershell/module/printmanagement/add-printer?view=windowsserver2025-ps).
If IPP Device/IppURL is unavailable or Windows insists on a vendor driver,
record the Windows version and Pi capabilities before troubleshooting; this
release does not ship a Windows driver. Older Windows builds are not validated.
The Pi's Gray default handles jobs without a custom local mode request.

## Linux desktop with CUPS

In the desktop printer settings, add a network printer and select the discovered
IPP queue or enter `ipp://<PI_HOST>:631/printers/NLN41`. Choose driverless /
IPP Everywhere, then select 4x6 paper. No local TSPL filter is needed.

A terminal alternative (Bash, after installing your distribution's CUPS client
and local CUPS scheduler) is:

```sh
read -r -p 'Pi hostname or IP: ' pi_host
sudo lpadmin -p NLN41_Remote -E -v "ipp://${pi_host}:631/printers/NLN41" -m everywhere
sudo lpadmin -p NLN41_Remote -o media=na_index-4x6_4x6in
lp -d NLN41_Remote -n 1 /path/to/your-4x6-label.pdf
```

The `lpadmin -m everywhere` remote queue pattern is documented by
[OpenPrinting CUPS sharing](https://openprinting.github.io/cups/doc/sharing.html).
If the distribution needs CUPS administration rights, use its normal sudo /
lpadmin group policy. Driverless capability negotiation still needs a real
client test for that distribution. Match the Pi's 203 dpi and 4x6 paper rather
than defaulting to A4; ordinary clients use the Pi Gray default.

## iPhone / iPad

Select the shared NLN41 from the normal print dialog, use 4x6 paper and start
with one copy. A system Black and White preset may still appear: it is not
our custom threshold selector. Unspecified jobs use the Pi's Gray default.

## If adding or printing fails

- Confirm Pi installation ended with capability PASS, and that both devices
  are on the same LAN. Network isolation / separate subnets can block discovery.
- Try the complete IPP queue URL if automatic discovery fails.
- Confirm the Pi's current address; there is no fixed address in these packages.
- Use 4x6 and fit-to-page for a differently sized document. Full-size A4/Letter
  exceeds this label printer's output width.
- Check `lpstat -p NLN41 -l`, `lpstat -W not-completed -o NLN41` and the Pi CUPS
  error log. See source `docs/ERRORS.md` for details.

The user confirmed v0.6.1 clean Pi installation, automatic Mac discovery/addition
and successful grayscale/barcode printing. Earlier iPhone printing worked too. Windows
and Linux client configuration is documented from primary references and has
not been physically exercised in this development environment.
