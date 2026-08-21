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

# Normalise ONLY the three things that must differ between the two runs:
#   1. the recorded `interpreter:` header line;
#   2. the interpreter token inside the echoed command, which appears only on the `$ ` line and
#      only in quotes, so the substitution is anchored to that line and cannot silently fold a
#      difference in the recipe's own output;
#   3. the label embedded in the temp-file paths the runner generates.
# Everything else — every PASS/FAIL line, every digest, the exit status — is compared verbatim.
norm() {
  LC_ALL=C sed -e '/^interpreter: /d' \
               -e '/^\$ /s/"bash"/"INTERP"/g' -e '/^\$ /s/"sh"/"INTERP"/g' \
               -e "s/$L-bash/LABEL/g" -e "s/$L-sh/LABEL/g" "$1"
}

# V-E (T115) — the comparison domain was HALF the evidence.
# This loop iterated over "$A"/A*.txt only, so a transcript present on the BASH side and absent on
# the SH side was never compared, and the script still reported "sh and bash agree on all N".
# MEASURED by T115: with A1.txt on both sides and a wildly different A2.txt on the bash side only,
# it printed `pairs compared: 1  differing: 0` and `RESULT: sh and bash agree`, exit 0.  An
# invariance claim over a domain that is only one side's file list is not an invariance claim.
# The domain is now the UNION of both sides; a name present on one side only is a difference.
# Same class again: the normalised scratch files used to be written into $O, the directory under
# audit.  A read-only $O would leave the previous run's .inv-a/.inv-b in place and the comparison
# would silently grade STALE bytes.  Scratch now lives in a directory this script owns.
INVDIR=$(mktemp -d "${TMPDIR:-/tmp}/shell-invariance.XXXXXX") || {
  echo "ERROR: cannot create a scratch directory — refusing to compare." >&2; exit 3; }
trap 'rm -rf "$INVDIR"' EXIT

n=0; bad=0
NAMES=$( { ls "$A"/A*.txt 2>/dev/null; ls "$B"/A*.txt 2>/dev/null; } | while read -r p; do basename "$p"; done | sort -u )
for name in $NAMES; do
  f=$A/$name
  b=$B/$name
  n=$((n+1))
  if [ ! -f "$f" ]; then echo "MISSING  $f  (present under $L-bash only)"; bad=$((bad+1)); continue; fi
  if [ ! -f "$b" ]; then echo "MISSING  $b"; bad=$((bad+1)); continue; fi
  norm "$f" > "$INVDIR/.inv-a"; norm "$b" > "$INVDIR/.inv-b"
  if diff -q "$INVDIR/.inv-a" "$INVDIR/.inv-b" >/dev/null; then
    echo "identical  $(basename "$f")"
  else
    echo "DIFFERS    $(basename "$f")"; diff "$INVDIR/.inv-a" "$INVDIR/.inv-b" | head -20; bad=$((bad+1))
  fi
done

echo
# An empty comparison set is an ERROR, not a pass: this is the vacuous-pass defect class.
[ "$n" -gt 0 ] || { echo "ERROR: compared ZERO transcript pairs — proves nothing." >&2; exit 3; }
echo "pairs compared: $n   differing: $bad"
[ "$bad" -eq 0 ] || exit 1
echo "RESULT: sh and bash agree on all $n transcripts for label '$L'."
