# Clean installation tests

A fresh Raspberry Pi OS 64-bit SD card is the clearest first-install test.
Preserve your working card and repeat from the clean OS image for independent
trials. A queue/file cleanup below retains apt dependencies and other CUPS
settings; it is an empty-project test, not an empty-OS test.

## Existing Pi: remove only this project

These instructions assume the default queue NLN41 and no other queue using
raster-nln41. Inspect `lpstat -p -v` first. Complete/cancel pending jobs before
removal: deleting a CUPS queue discards its jobs. If it points to another printer,
do not use this cleanup on that queue. Save any project logs/backups you need;
removing /var/lib/nln41-arm64-driver deletes the rollback snapshots.

```sh
sudo systemctl start cups
if lpstat -p NLN41 >/dev/null 2>&1; then
    sudo lpadmin -x NLN41
fi
lpoptions -x NLN41
sudo lpoptions -x NLN41
sudo rm -f /usr/lib/cups/filter/raster-nln41
sudo rm -f /usr/share/ppd/nln41/NL-N41.ppd
sudo rm -f /usr/local/sbin/nln41-rollback
sudo rm -rf /var/lib/nln41-arm64-driver
sudo systemctl restart cups
```

Other separately named queues using this filter must be migrated/removed first.
Do not clear /etc/cups or its spool directory. Avahi is needed for discovery;
do not remove other services. This release installs no static Avahi XML file.
Inspect any older hand-created NL-N41 advertisement before removing that file.

Verify no NLN41 destination and no project filter/state remain, then run the
new Pi installer. The installer reapplies the correct sharing settings and
stops/disables p910nd. Check capability PASS, automatic Mac discovery and one
label/one grayscale image. Test a real barcode separately.

## Mac clean client test

In Printers & Scanners remove every old queue for this NL-N41, keeping unrelated
printers. Add only the newly discovered service after Pi installation. Use the
application's Default Settings preset rather than an older custom preset.
Do not install a Mac script, vendor driver or the Pi PPD locally for this test.

Resetting the whole Mac printing system also removes unrelated printers and
presets; a scoped queue removal is enough here. If testing absolute absence
of a previously installed vendor driver, inspect its exact files and shared
filter use before removal; no vendor uninstaller is bundled with this project.

## Verification boundaries

An existing Mac with built-in AirPrint still uses Apple's printing components.
The test verifies absence of project/vendor dependencies in its chosen client
queue, not absence of all system printing software. The original user's
v0.6.1 report confirmed empty Pi queue/filter/state, then capability PASS,
a generated AirPrint client PPD and successful grayscale/barcode output.
A new v0.6.2 physical run has not been claimed. Installer rollback is simulated
locally; complete a live rollback check on a test system if needed.
