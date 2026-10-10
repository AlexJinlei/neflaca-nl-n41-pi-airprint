# Network sharing and automatic AirPrint discovery

The .run installs a local USB CUPS queue and enables CUPS/Avahi DNS-SD sharing
on the Pi. PDF goes through the server renderer; PWG/URF input goes directly
to the supported raster decoder. CUPS generates real capability/discovery data;
no static fabricated AirPrint TXT record is installed.

The installer shares on the local network using CUPS --share-printers, sets
BrowseLocalProtocols=dnssd and BrowseDNSSDSubTypes=_print,_universal,
and sets printer-is-shared=true on NLN41. It sets the queue description to
NefLaca NL-N41 AirPrint. CUPS normally appends @ <server name> in the list.
The queue name and URI remain NLN41 and ipp://<PI_HOST>:631/printers/NLN41.

On a Mac on the same LAN, open System Settings > Printers & Scanners > Add
Printer. Select NefLaca NL-N41 AirPrint @ your Pi in the default list. Use
may show AirPrint or the Pi model name; keep the automatic selection and click
Add. The user verified a generated -AirPrint client PPD with no local TSPL
filter. No Mac script or manual IP/queue entry is needed when discovery works.
Ordinary AirPrint uses the Pi Gray default without a custom mode menu.

## Why an older release appeared as Bonjour Shared

The _cups subtype tells macOS to treat the service as a shared CUPS printer
and use traditional driver matching. It can then offer Generic PostScript
rather than AirPrint. Removing that subtype allows AirPrint capability-based
configuration. This behavior is documented in the
[OpenPrinting discussion answered by the CUPS maintainer](https://github.com/OpenPrinting/cups/discussions/841).
The subtype list is a
[CUPS server configuration](https://openprinting.github.io/cups/doc/man-cupsd.conf.html).

Bonjour Shared is a discovery classification, not proof of an old raw queue.
If the active queue PPD names raster-nln41, it is using this project's Pi driver.
Keep that queue and Avahi running. Deleting them would remove working printing
or discovery. Earlier raw USB/TCP forwarding is a separate transport path.

## Update an existing working queue without reinstalling

Run on the Pi; substitute your queue name if it differs from NLN41:

```sh
sudo cupsctl BrowseDNSSDSubTypes=_print,_universal
sudo lpadmin -p NLN41 -D 'NefLaca NL-N41 AirPrint'
sudo cupsd -t
sudo systemctl restart cups
```

Close and reopen Add Printer on the Mac, allow discovery to refresh, then
select the new name and keep the automatically selected Use setting. Existing Mac queues retain their
previous configuration; add a new discovered queue for verification.
No print job is submitted by these commands.

The subtype change affects **every shared queue on this CUPS server**. Queues
and drivers are preserved, but clients may discover them differently. For a
manual change, record the original subtype setting and queue description first
if you need to undo it. The one-click installer snapshots/restores cupsd.conf
and the previous queue description automatically.

## Validation and discovery problems

A passed capability check confirms declared formats/resolution, not real paper
output or actual Mac discovery. The user verified v0.6.1 clean installation,
automatic Mac discovery/addition and grayscale/barcode printing. Test one 4x6
label with one copy on your own setup. Advanced client page-layout
features such as number-up have not been verified after this discovery change.

Network isolation, firewalls or separate subnets can prevent discovery. Manual
full-URI setup is described in CLIENT-SETUP.md. No cloud service is needed.
If the old Bonjour Shared entry remains after refreshing, check on the Pi:

```sh
sudo cupsctl | grep -E 'Browse(LocalProtocols|DNSSDSubTypes)'
```

The subtype value should have _print,_universal without _cups. Avoid adding a
second static Avahi service for the same queue. Report the current
advertisement before deleting any unexpected entry.

For an existing manually managed queue, scripts/setup-network.sh updates
files/sharing and Gray defaults, with its own network-backup/rollback tool.
It omits _cups too, but leaves the queue description as configured. Its rollback
scope differs from the complete .run installer; do not mix recovery workflows.
Prefer INSTALL-PI.md and ONECLICK.md for new installs.
