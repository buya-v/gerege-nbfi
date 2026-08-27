#!/usr/bin/env bash
# T203 - run the conformance harness from the repo root with the toolchain
# sourced, capturing full output.  Invoked with `bash`, never `sh` (exit 3 is a
# wrong-interpreter refusal, not a failure).
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 9
. .softhouse/bin/go-env.sh
bash .softhouse/conformance.sh
echo "CONFORMANCE_EXIT=$?"
