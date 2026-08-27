#!/bin/bash
# T223 — run the project bar exactly as the brief specifies, from this worktree.
#   . .softhouse/bin/go-env.sh
#   bash .softhouse/conformance.sh          # bash, NEVER sh
set -uo pipefail
cd "$(dirname "$0")/../../../.."
. .softhouse/bin/go-env.sh
bash .softhouse/conformance.sh
echo "CONFORMANCE_EXIT=$?"
