#!/bin/bash
# T229 — the BAR, run exactly as the brief specifies: `. .softhouse/bin/go-env.sh` from the repo
# root, then `bash .softhouse/conformance.sh` (never `sh`; exit 3 = wrong-interpreter refusal).
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
pwd
. .softhouse/bin/go-env.sh
bash .softhouse/conformance.sh
echo "CONFORMANCE_EXIT=$?"
