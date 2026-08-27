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
# V-F (T115) — same class again: the normalised scratch files used to be written into $O, the
# directory under audit.
#
# T151 (F-T138-4) — THE FIX IS RIGHT; ITS STATED REASON WAS WRONG, AND THE WRONG REASON UNDERSTATES
# THE HAZARD.  T115 wrote "a read-only $O would leave the previous run's .inv-a/.inv-b in place and
# the comparison would silently grade STALE bytes."  A read-only $O ALONE IS FAIL-CLOSED: a shell
# redirect cannot CREATE a file in an unwritable directory, so `norm` writes nothing, `diff` reports
# "No such file", and the script exits 1.  Loud and safe.
#
# What actually produces the vacuous pass is READ-ONLY SCRATCH FILES — .inv-a/.inv-b already present
# and mode 444 — because a redirect to an EXISTING file needs write permission on the FILE, not on
# the directory.  And then $O NEED NOT BE READ-ONLY AT ALL.  T138 drove all five cases over a pair
# that genuinely differs [VERIFIED: T138 out/R3b-VF.txt]:
#     $O writable, no scratch      -> DIFFERS, exit 1                     (control, caught)
#     $O 555,      no scratch      -> false DIFFERS, exit 1               (fail-closed)
#     $O 555,      scratch 644     -> DIFFERS, exit 1                     (caught)
#     $O 555,      scratch 444     -> "pairs compared: 1  differing: 0", exit 0   <-- VACUOUS
#     $O writable, scratch 444     -> the same vacuous pass               <-- $O irrelevant
# Scratch now lives in a directory this script creates and owns, which closes both readings.
# NOTE (T151, F-T138-5): no committed guard drives V-F red.  `prove-guards.sh` exits 0 with every
# leg OK when this fix is reverted, so this paragraph and T138's transcript are the whole of the
# evidence — do not cite GUARDS-RED.txt for it.
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
