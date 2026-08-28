#!/bin/bash
# T428: build the conformance binary from a named tree and run EVERY registered
# deliberately-wrong ledger implementation against the full committed corpus.
# usage: t428-run-arms.sh <treeroot> <outdir>
set -u
tree="$1"; outdir="$2"
mkdir -p "$outdir"
cd "$tree" || exit 9
bin="$outdir/conformance-bin"
go build -C "$tree/nexus" -o "$bin" ./internal/apps/loanschedule/conformance/cmd/conformance || exit 9

"$bin" -list-implementations > "$outdir/00-list.txt" 2>&1
names=$(LC_ALL=C sed -n 's/^\([a-z0-9-][a-z0-9-]*\)   \[-ledger-impl\] DELIBERATELY WRONG:.*$/\1/p' "$outdir/00-list.txt")
n=0
for impl in $names; do
  "$bin" -oracle-probe=up "-ledger-impl=$impl" > "$outdir/arm-$impl.txt" 2>&1
  rc=$?
  echo "$impl exit=$rc"
  echo "EXIT=$rc" >> "$outdir/arm-$impl.txt"
  n=$((n+1))
done
"$bin" -oracle-probe=up > "$outdir/arm-CONTROL-ledger-go.txt" 2>&1
echo "CONTROL exit=$?"
echo "ARMS RUN: $n"
