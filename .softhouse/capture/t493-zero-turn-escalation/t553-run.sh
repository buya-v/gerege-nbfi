#!/usr/bin/env bash
# t553-run.sh <repo> <guard> [guard args...]
# Run the guard inside <repo> and print its exit code. Nothing else.
set -uo pipefail
REPO="$1"; GUARD="$2"; shift 2
cd "$REPO"
"$GUARD" "$@"
rc=$?
printf '<<exit=%s>>\n' "$rc"
exit "$rc"
