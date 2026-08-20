#!/bin/sh
# T91 — the recipe must behave identically under `sh` and under `bash`.
#
# T85 required this of T80 and it is required here for the same reason: the call-through
# dot-sources the rig instead of exec'ing an interpreter precisely so that the caller's shell is
# preserved.  That is a claim, and a claim gets driven, not asserted.
#
# Compares every transcript pair <LABEL>-sh/X.txt vs <LABEL>-bash/X.txt after normalising the two
# things that MUST differ: the recorded interpreter, and the label embedded in the temp-file paths.
#
# Usage:  sh shell-invariance.sh <out-dir> <LABEL>
# Exit:   0 = every pair identical after normalisation; 1 = a pair differs; 3 = nothing compared.
set -u
O=${1:?usage: sh shell-invariance.sh <out-dir> <LABEL>}
L=${2:?usage: sh shell-invariance.sh <out-dir> <LABEL>}
A=$O/$L-sh
B=$O/$L-bash
[ -d "$A" ] && [ -d "$B" ] || { echo "missing $A or $B" >&2; exit 2; }

norm() {   # strip the interpreter line and fold the label out of embedded paths
  LC_ALL=C sed -e '/^interpreter: /d' -e "s/$L-bash/LABEL/g" -e "s/$L-sh/LABEL/g" "$1"
}

n=0; bad=0
for f in "$A"/A*.txt; do
  [ -f "$f" ] || continue
  b=$B/$(basename "$f")
  n=$((n+1))
  if [ ! -f "$b" ]; then echo "MISSING  $b"; bad=$((bad+1)); continue; fi
  norm "$f" > "$O/.inv-a"; norm "$b" > "$O/.inv-b"
  if diff -q "$O/.inv-a" "$O/.inv-b" >/dev/null; then
    echo "identical  $(basename "$f")"
  else
    echo "DIFFERS    $(basename "$f")"; diff "$O/.inv-a" "$O/.inv-b" | head -20; bad=$((bad+1))
  fi
done
rm -f "$O/.inv-a" "$O/.inv-b"

echo
# An empty comparison set is an ERROR, not a pass: this is the vacuous-pass defect class.
[ "$n" -gt 0 ] || { echo "ERROR: compared ZERO transcript pairs — proves nothing." >&2; exit 3; }
echo "pairs compared: $n   differing: $bad"
[ "$bad" -eq 0 ] || exit 1
echo "RESULT: sh and bash agree on all $n transcripts for label '$L'."
