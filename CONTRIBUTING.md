# Contributing

Build/test with CUPS 2.x and a compiler using the instructions in docs/BUILD.md.
Keep proprietary vendor implementation code/executables out of this project.
Report behavioral evidence and independent fixes rather than copying a driver.

For a printing issue, include printer model/USB ID, OS/CUPS version, chosen
paper/mode and the specific filter error. Remove personal usernames, addresses,
serials, document contents and job titles from logs. Tests use a synthetic USB
serial and the documentation-only 192.0.2.10 address; they never connect to it.

Do not attach private shipping labels. Use neutral small test patterns and
check payload polarity, stride/padding, dimensions and copy counts. Mark whether
a result is byte-level/offline or physically printed. New device support needs
actual protocol/media/printhead evidence; do not assume all TSPL units match.

Keep English installer prompts and file-specific Gatekeeper instructions.
The project's MIT license applies to original contributions.
