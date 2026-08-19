#!/bin/sh
# T40 — run T36's fail-the-run preconditions before ANY charge capture.
# Copied verbatim from .softhouse/capture/pathb/t36/preconditions.sh (read-only to T40).
# Exit non-zero => DO NOT CAPTURE.
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513
OUT=${1:-$W/.softhouse/capture/charges/out/preconditions-T40.txt}
CANARY_REQ="$W/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json" \
  sh "$W/.softhouse/capture/charges/bin/preconditions.sh" gerege > "$OUT" 2>&1
rc=$?
cat "$OUT"
echo "PRECONDITIONS_EXIT=$rc"
exit $rc
