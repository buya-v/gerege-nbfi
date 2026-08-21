#!/bin/bash
# T169 — drive the SECOND way "0 errored" was unfalsifiable on the pre-fix rigs.
#
# The pre-fix handler ends with `e.printStackTrace(System.err)` [CaptureT100.java:448,
# CaptureT117.java:643, CaptureT83.java:492 — same line, same rig lineage]. Every runner in this
# program then refuses the run on non-empty stderr. The refusal below is the EXACT four lines from
# the committed run-t117.sh, extracted verbatim into a scratch copy (T114's standing ruling: the
# committed script is READ, never edited, and never re-run for this purpose).
set -uo pipefail
SRC=/Users/buv/gerege-nbfi/.claude/worktrees/agent-af1f5b7aebc97911d/.softhouse/capture/t117-familyb/src/run-t117.sh

echo "the refusal, quoted verbatim from the committed runner:"
grep -n '\-s "\$ERR"' "$SRC"
echo
echo "and the handler line that guarantees it fires whenever a cell is recorded:"
grep -n 'printStackTrace' /Users/buv/gerege-nbfi/.claude/worktrees/agent-af1f5b7aebc97911d/.softhouse/capture/t117-familyb/src/CaptureT117.java
echo
echo "DRIVE: run that refusal against a NON-EMPTY stderr, exactly as a recorded RuntimeException"
echo "       would have left it."
ERR=/tmp/t169probe/fake-stderr.txt
printf 'java.lang.ArithmeticException: / by zero\n\tat org.apache.fineract...\n' > "$ERR"
( [ -s "$ERR" ] && { printf 'RUN FAILED: stderr NOT empty:\n' >&2; cat "$ERR" >&2; exit 1; } || true )
echo "EXIT $?   <- non-zero: the run is REFUSED, so no integrity line is ever printed"
echo
echo "CONTROL: the same refusal against an EMPTY stderr."
: > "$ERR"
( [ -s "$ERR" ] && { printf 'RUN FAILED: stderr NOT empty:\n' >&2; cat "$ERR" >&2; exit 1; } || true )
echo "EXIT $?   <- zero: the run proceeds, and prints its integrity line, which therefore can only"
echo "             ever have read '0 errored'."
