#!/bin/bash
# T306 review probe — does the WIDENED capability gate still refuse a shape this
# store has not observed?
#
# Four probe vectors (build-probes.py) are dropped into a SCRATCH COPY of the
# store and the conformance binary is run over that copy. Nothing under
# .softhouse/vectors is touched and no request reaches the reference oracle.
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acee94120db93ffce
. "$W/.softhouse/bin/go-env.sh"

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t306-widen.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/vectors" || exit 1
python3 "$W/.softhouse/reviews/T306/probe/build-probes.py" "$SCRATCH/vectors" || exit 1

cd "$W/nexus" || exit 1
go build -o "$SCRATCH/conf" ./internal/apps/loanschedule/conformance/cmd/conformance || exit 1

"$SCRATCH/conf" -oracle-probe=up -context=ledger -repo-root="$W" \
  -store="$SCRATCH/vectors" > "$SCRATCH/run.txt" 2>&1
echo "binary exit=$?"
echo
grep -n "ZZZ-T306" "$SCRATCH/run.txt" | head -80
echo
echo "---- verdict lines ----"
grep -E "VERDICT|inadmissible|INADMISSIBLE|admitted|ledger (parity|oracle-refusal)" "$SCRATCH/run.txt" | head -20
echo
echo "scratch: $SCRATCH"
cp "$SCRATCH/run.txt" "$W/.softhouse/reviews/T306/out/widened-gate-probe.txt"
