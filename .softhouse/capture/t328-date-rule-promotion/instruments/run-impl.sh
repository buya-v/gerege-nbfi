#!/usr/bin/env bash
# T328 -- run the ledger conformance corpus against ONE named implementation.
#
# It is a thin wrapper so that a survival transcript and a death transcript are
# produced by THE SAME COMMAND, differing only in the tree's state. The binary is
# compiled from THIS worktree (the runtime repo-root anchor, T165), so `-repo-root`
# is never passed and the report prints which tree it resolved.
#
# usage: bash run-impl.sh <impl-name> [extra flags...]
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
IMPL="$1"; shift || true

echo "T328 run-impl: HEAD=$(git -C "$REPO" rev-parse --short HEAD)  impl=$IMPL"
echo "T328 run-impl: ledger vectors on disk: $(ls "$REPO/.softhouse/vectors/ledger" | wc -l | tr -d ' ')"
echo "---"
cd "$REPO/nexus" || exit 2
go run ./internal/apps/loanschedule/conformance/cmd/conformance \
  -ledger-impl "$IMPL" -oracle-probe up "$@"
rc=$?
echo "---"
echo "T328 run-impl: EXIT $rc"
exit "$rc"
