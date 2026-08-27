#!/bin/bash
# T155: run a scratch tree's own conformance.sh and record verdict + probe line.
# $1 = tree root, $2 = label, $3.. = extra args
set -u
TREE="$1"; LABEL="$2"; shift 2
OUT="/tmp/t155/out/$LABEL.txt"
mkdir -p /tmp/t155/out
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
# CWD MATTERS. cmd/conformance/main.go does `conformance.FindRepoRoot(".")`, so
# the Go binary resolves the repo from the CALLER'S working directory, not from
# the script's own location. Invoking a scratch tree's conformance.sh by
# absolute path from outside that tree grades the CALLER'S store and scans the
# CALLER'S Go tree while the shell guards report the scratch tree's paths.
# T155 caught that with a 22-vs-24 file-count cross-check on its first run.
cd "$TREE" || exit 9
bash "$TREE/.softhouse/conformance.sh" "$@" > "$OUT" 2>&1
rc=$?
echo "=== $LABEL exit=$rc ==="
echo "--- probe line PRESENT? ---"
if LC_ALL=C grep -aq 'reference oracle (.*) probe = ' "$OUT"; then
  LC_ALL=C grep -a 'reference oracle (.*) probe = ' "$OUT"
else
  echo "NO PROBE LINE PRINTED — this exit is NOT an oracle-outage verdict"
fi
echo "--- counts / verdict ---"
LC_ALL=C grep -aE 'parity vectors|cells compared|no-float|VERDICT|census|CASE_ID|HARD guard|FLOAT' "$OUT" | head -40
echo "=== end $LABEL (full output at $OUT) ==="
