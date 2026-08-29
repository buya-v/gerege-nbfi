#!/bin/bash
# T433 / C-T423-1 — append an ATTRIBUTED correction footer to every committed transcript that
# echoes T393's false impossibility.
#
# WHY APPEND RATHER THAN REWRITE. These files are records of what the tooling PRINTED. The
# false sentence is in them because run-all.sh emitted it. Editing the line out would destroy
# the evidence that this program shipped a false claim in tracked executables — which is the
# very thing C-T423-1 exists to record — and would leave a reader with a bare negation removed.
# So the bytes stay and the correction is appended, marked, dated and attributed.
#
# IDEMPOTENT: a file that already carries the footer is skipped, so re-running does not stack
# duplicates. That is checked by a MARKER, not by a line count (P-29: a count is a weak
# tripwire).
#
# SCOPE: only `.softhouse/capture/t393-t382-conditions/` and `.softhouse/reviews/A2-11/`,
# T433's assigned paths. Echoes outside those paths are DISCLOSED BY NAME in
# `.softhouse/capture/t393-t382-conditions/out/T433-CORRECTION.md` and deliberately untouched.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). T433_ROOT overrides the derived root.
#
# EXIT 0  every echoing transcript in scope now carries the footer.
# EXIT 1  at least one still echoes the claim without a footer.
# EXIT 2  REFUSED — the search found NOTHING to annotate, which means the pattern or the root
#         is wrong, not that the repository is clean. A sweep that matched nothing has not
#         proved anything (P-72: calibrate on a known positive).
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${T433_ROOT:-$(cd "$HERE/../../../.." && pwd)}"
MARKER="T433 / C-T423-1 -- CORRECTION APPENDED TO A RECORD"
PAT="There is no committed baseline older than HEAD for those 632\.|no baseline older than HEAD anywhere|does not exist and cannot be manufactured here|committed baseline older than HEAD for those 632 observations"

SCOPE1="$ROOT/.softhouse/capture/t393-t382-conditions"
SCOPE2="$ROOT/.softhouse/reviews/A2-11"
for d in "$SCOPE1" "$SCOPE2"; do
  [ -d "$d" ] || { echo "REFUSED: $d is not a directory. Wrong T433_ROOT ($ROOT)?" >&2; exit 2; }
done

# CALIBRATION on a known positive (P-72), before any negative is reported: a file this worker
# KNOWS contains the pattern must be matched by the pattern, or the instrument is broken.
CAL="$SCOPE1/out/05-executable-diff.txt"
if [ -f "$CAL" ] && ! grep -qE "$PAT" "$CAL"; then
  echo "REFUSED: the calibration file $CAL does not match the pattern. The SWEEP is broken," >&2
  echo "         and its negatives would be statements about the regex, not the repository." >&2
  exit 2
fi

# TRANSCRIPTS ONLY. The corrected SOURCE files quote the false text on purpose, tagged
# [QUOTED-FALSE-CLAIM], and appending a shell heredoc to a .py or a .sh would corrupt it. So
# this annotator touches only recorded output — .txt and .tsv — and any line that carries the
# tag is not an echo, it is a correction.
echoing() {
  grep -rlE "$PAT" "$SCOPE1" "$SCOPE2" --include="*.txt" --include="*.tsv" 2>/dev/null \
    | LC_ALL=C sort | while IFS= read -r f; do
        grep -E "$PAT" "$f" | grep -qv "QUOTED-FALSE-CLAIM" && printf '%s\n' "$f"
      done
}

HITS=0; ANNOTATED=0; SKIPPED=0
while IFS= read -r f; do
  HITS=$((HITS + 1))
  if grep -qF "$MARKER" "$f"; then
    echo "  skip (already annotated)  ${f#$ROOT/}"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi
  cat >> "$f" <<EOF

================================================================================
$MARKER
================================================================================
This transcript is a RECORD of what the tooling printed. Above, it echoes T393's
claim that no committed baseline older than HEAD exists for the 632 post-fork
captured oracle observations. THAT CLAIM IS FALSE. The bytes are left exactly as
they were printed, because deleting them would destroy the evidence that this
program shipped a false claim in tracked executable files.

THE BASELINE EXISTS AND ALWAYS DID: the blob at the commit that FIRST ADDED each
observation, \`git log --diff-filter=A -- <path>\`. It is an object inside an
ALREADY-COMMITTED commit, so laundering MANIFEST.sha256 inside the mutating commit
cannot reach it.

MEASURED OVER THE WHOLE 632, NOT A SAMPLE (T433, two independent derivations of the
birth commit agreeing 632/632): 632 born STRICTLY OLDER than the tip, 0 born at the
tip, 631 still byte-identical to their birth blob, 1 legitimate re-capture
(out/A2-370-db-ledger-state.txt) adjudicated by digest.
  -> .softhouse/capture/t433-t423-c1/out/00-whole-632-sweep.txt

T433 landed the comparison as ARM F, section 8 of
.softhouse/reviews/A2-11/verify-capture-integrity.py. Driven RED then GREEN in situ:
  -> .softhouse/capture/t433-t423-c1/out/20-ARMF-IN-SITU-DRIVE.txt

Index of every corrected site and every surviving echo:
  -> .softhouse/capture/t393-t382-conditions/out/T433-CORRECTION.md
================================================================================
EOF
  echo "  annotated                 ${f#$ROOT/}"
  ANNOTATED=$((ANNOTATED + 1))
done < <(echoing)

echo
echo "  files matching the claim in scope : $HITS"
echo "  annotated this run                : $ANNOTATED"
echo "  already annotated                 : $SKIPPED"

if [ "$HITS" -eq 0 ]; then
  echo "REFUSED: the sweep matched NOTHING. On a repository that has not yet been corrected"
  echo "         that is impossible, so this is a statement about the pattern or the root"
  echo "         ($ROOT), never about the world. REFUSED."
  exit 2
fi

# The check that makes this a guard rather than a script: nothing in scope may echo the claim
# without carrying the correction.
BAD=0
while IFS= read -r f; do
  grep -qF "$MARKER" "$f" || { echo "  STILL UNCORRECTED ${f#$ROOT/}"; BAD=$((BAD + 1)); }
done < <(echoing)
if [ "$BAD" -ne 0 ]; then
  echo "T433 TRANSCRIPT ANNOTATION: FAIL — $BAD file(s) echo the false claim with no correction."
  exit 1
fi
echo "T433 TRANSCRIPT ANNOTATION: PASS — every file in scope that echoes the claim carries the"
echo "correction in the same file, so a reader who greps the false sentence finds the refutation"
echo "without having to know it exists."
exit 0
