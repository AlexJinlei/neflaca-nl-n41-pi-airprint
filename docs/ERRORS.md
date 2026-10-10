# Diagnose printing errors

Gray/RGB content is valid in both modes. Black & White forces threshold
conversion; Gray retains tones through halftoning. There is no content-mismatch
rejection. A faint gray background can correctly produce sparse printed dots.

Wrong size/resolution, unsupported raster layout/colorspace, invalid options,
truncated input, cancellation and output failures still fail with a specific
English CUPS ERROR. The first filter error is retained through cleanup. Client
windows can show only “Stopped on server”; the Pi log/job message is the
reliable fallback. No client popup agent is installed.

On the Pi:

```sh
lpstat -p NLN41 -l
lpstat -W not-completed -o NLN41
sudo tail -n 100 /var/log/cups/error_log
```

Temporarily enable debug logging for one retry, then disable it:

```sh
sudo cupsctl --debug-logging
# Submit one correctly sized test here, then read error_log.
sudo cupsctl --no-debug-logging
```

From the source root, inspect retained server job messages:

```sh
ipptool -tv ipp://localhost:631/printers/NLN41 tests/job-diagnostics.test
```

Replace localhost with your own host only when running remotely. History policy
can limit available records. Remove private titles/usernames/addresses before
sharing logs in a public issue. The installer does not submit those logs online.

Typical fixes: use 4x6 paper instead of A4/Letter; do not add a 90-degree extra
rotation to portrait 4x6; install system cups-filters/Ghostscript for documents;
finish/cancel old stopped jobs before upgrading. New defaults do not rewrite
options saved in an old job. Check p910nd is not competing for USB.

References: [CUPS filter diagnostics](https://openprinting.github.io/cups/doc/api-filter.html).
