#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
command -v cups-config >/dev/null || { echo 'Install build-essential libcups2-dev libcupsimage2-dev first.' >&2; exit 1; }
make all
make test
