#!/bin/bash
# T8-promote verification wrapper: activates the repo-local Go toolchain and runs
# the conformance harness from this worktree. Kept in the handoff directory so the
# exact command that produced the recorded output is auditable.
set -u
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$HERE/.softhouse/conformance.sh" "$@"
rc=$?
echo "CONFORMANCE_EXIT=$rc"
exit $rc
