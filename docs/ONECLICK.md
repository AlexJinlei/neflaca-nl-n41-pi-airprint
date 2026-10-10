# Installer internals and rollback

The public .run bundles a compiled ARM64 filter and inspectable source. Its
SHA256 payload check runs before extraction; extraction can be requested without
installation using --extract. It has no remote executable-script download.
Apt installs only distribution packages; internet access is therefore needed.
The digest checks transfer consistency; it is not a publisher signature.

Installation checks Linux aarch64/Debian/CUPS 2.x, system dependencies, queue
ownership, pending jobs and binary loading. It saves a root-only snapshot,
detects USB, stops/disables p910nd, installs its independently named filter/PPD,
creates/updates NLN41 and applies Gray, 4x6, 2 mm gap, zero extra rotation,
normal polarity/mirror and one-copy defaults. It enables CUPS/Avahi shared
printing and checks advertised PDF/URF/PWG/203 dpi capabilities. No paper prints
unless --print-test is explicitly requested.

Backups and logs are in /var/lib/nln41-arm64-driver/oneclick/. A current symlink
selects the latest installation snapshot. Installation and rollback share a lock.
The persistent /usr/local/sbin/nln41-rollback helper survives download deletion.

Rollback restores the previous filter, installed PPD, queue PPD/URI/description/options,
queue enabled/accepting/shared state, cupsd.conf and changed service states.
A fresh install's new queue is removed only after pending-job checks. Other
queues are not recreated from a whole printers.conf snapshot. Apt dependency
packages and their installation side effects are retained. Server-wide sharing
settings are restored from a snapshot, so review later server changes first.

Configuration failures after replacement starts attempt automatic rollback.
A busy queue or a same-name queue for another printer is left unchanged.
No connection default, password file, account or repository URL is embedded.

The legacy file-only install.sh/uninstall.sh and setup-network.sh tools remain
for manual source workflows. Use the .run one-click route for a complete
install/upgrade and its matching rollback helper.

See INSTALL-PI.md, CLIENT-SETUP.md and USER-GUIDE.md for user steps.
