#!/bin/sh
# T91 — score one attack-transcript directory.
#
# For every transcript it reports the exit status and whether the ONE sentence this whole task
# exists to make honest is present:
#     PASS  effective rounding mode canary: period-1 interest <x> (= HALF_UP)
# A reader believes that sentence.  ADMITS = the attack got the script to print it (or to exit 0);
# REFUSES = the script exited non-zero and never printed it.
#
# Two traps this run has already hit, both guarded here:
#   * `grep -a` is NOT sufficient.  BSD grep in a UTF-8 locale matches NOTHING in a file containing
#     an invalid multibyte sequence AND RETURNS 0.  Every grep below is LC_ALL=C.
#   * A check that passes VACUOUSLY ON ZERO FILES is the defect class this run keeps finding.  An
#     empty transcript set is an ERROR here, not a pass.
#
# Usage:  sh verdict.sh <out/LABEL-SH dir>
set -u
D=${1:?usage: sh verdict.sh <transcript dir>}
[ -d "$D" ] || { echo "not a directory: $D" >&2; exit 2; }

S='PASS  effective rounding mode canary'
DG='PASS  canary request pinned by DIGEST COMPARISON'

n=0; admits=0; refuses=0
printf '%-46s %-6s %-8s %-9s %s\n' TRANSCRIPT EXIT CANARY-OK DIGEST-PIN VERDICT
printf '%-46s %-6s %-8s %-9s %s\n' '---' '---' '---' '---' '---'
for f in "$D"/A*.txt; do
  [ -f "$f" ] || continue
  n=$((n+1))
  st=$(LC_ALL=C tail -1 "$f" | sed 's/EXIT=//')
  if LC_ALL=C grep -qF "$S" "$f"; then c=YES; else c=no; fi
  if LC_ALL=C grep -qF "$DG" "$f"; then d=YES; else d=no; fi
  # An attack ADMITS if the rig either printed the HALF_UP certification or exited 0.
  if [ "$c" = YES ] || [ "$st" = 0 ]; then v=ADMITS; admits=$((admits+1)); else v=REFUSES; refuses=$((refuses+1)); fi
  printf '%-46s %-6s %-8s %-9s %s\n' "$(basename "$f")" "$st" "$c" "$d" "$v"
done

echo
if [ "$n" -eq 0 ]; then
  echo "ERROR: zero transcripts in $D — a scan over an empty file set proves NOTHING." >&2
  echo "       (this is the vacuous-pass defect class; it is an error here, not a pass)" >&2
  exit 3
fi
echo "transcripts: $n   ADMITS: $admits   REFUSES: $refuses"

# A7 is an INVARIANCE test, not an exploit: a symlink to the pinned tie must be ACCEPTED.
# It is expected to ADMIT under a correct rig, so it is named here rather than silently counted.
echo "note: A7 (symlink to the pinned tie) is an invariance test — a correct rig ADMITS it."
