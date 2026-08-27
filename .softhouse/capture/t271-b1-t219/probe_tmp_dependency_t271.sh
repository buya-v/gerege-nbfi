#!/usr/bin/env bash
# T271 -- DECISIVE TEST of an OUT-OF-SCOPE defect this task tripped over: is `.softhouse/
# conformance.sh`'s GREEN contingent on a transient file in /tmp?
#
# READ THE NEXT PARAGRAPH IN THE PAST TENSE. [T293] It described the tree as it stood when T271
# was written; T273 landed in the same fire and REPAIRED it. `02-escape-matrix-fix.sh` line 6 is
# now a comment and its fixture is a `mktemp -d` scratch dir. The correction is at "WHAT EXIT 1
# MEANS NOW" below, and it is stated here too because this is the paragraph people skim (P-46).
#
# `.softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh` SET
# `C=/tmp/t234_matrix2.txt` at line 6 and CREATED it at line 7. The fail-open linter's C1 check
# asks whether that absolute path EXISTS ON DISK NOW:
#
#     path PRESENT -> C2 only            -> TIER 2 -> matches FAILOPEN_PIN_FILE_LIST -> bar GREEN
#     path ABSENT  -> C1 dead path + C2  -> TIER 1 -> frontier != pin              -> bar EXIT 2
#
# T271 DELIBERATELY LEAVES THE FILE DELETED AND THE BAR RED. Creating it would be manufacturing a
# green out of host state no reviewer can see and no commit records, which is the exact move P-88
# records this program rejecting -- and moving the pin to match would be lowering the bar. The
# defect is in t234's instrument and in conformance.sh's pin, both OUTSIDE T271's scope and both
# CONTENDED this fire. REPORTED, NOT FIXED.
#
# IT RESTORES THE STATE IT FOUND, AND THAT MATTERS MORE THAN IT LOOKS. /tmp is SHARED across
# every agent on this host: an earlier draft ended by unconditionally deleting the file, which
# would silently turn a CONCURRENT worker's conformance bar red for reasons invisible to it.
# Measured live during T271: the file reappeared seconds after this probe removed it, so some
# other process on this Mac creates it -- which is P-88 sharpened, because the bar's colour then
# depends on INTER-AGENT TIMING, not merely on reboot. This script therefore records whether the
# file was present when it started and puts that back before it exits. It is a MEASUREMENT, not a
# repair and not a side effect.
#
# T293 CORRECTED TWO OVER-CLAIMS IN THE PARAGRAPH ABOVE, BOTH BY OBSERVATION.
#
#   (1) "restored by the trap on EVERY exit path including an error" was FALSE for one path.
#       SIGKILL cannot be trapped by any shell. T293 signalled this probe at t=9s -- inside
#       READING B, when it holds the file CREATED while it had found it ABSENT -- and measured:
#       SIGTERM restored, SIGINT restored, SIGKILL LEFT THE FILE PRESENT. The honest statement
#       is "every exit path bash can trap", and it is now written that way. INT/TERM/HUP are
#       trapped EXPLICITLY below rather than left to the EXIT trap's signal behaviour, so the
#       intent is inspectable; SIGKILL is disclosed, not covered.
#       [.softhouse/reviews/T293/evidence/50-restoration-by-observation.txt]
#
#   (2) `restoredAsFound=1` USED TO BE A HARD-CODED LITERAL in the two summary lines below --
#       printed BEFORE the EXIT trap that does the restoring had run, so it was structurally
#       incapable of being a measurement. T293 red-drove it: with `trap restore_found_state
#       EXIT` deleted, this probe found the file PRESENT, left it ABSENT, and STILL PRINTED
#       `restoredAsFound=1`. That is a fail-open in the evidence line of a probe written to
#       expose fail-opens. The claim is now emitted by the trap itself, AFTER restoring, from
#       a RE-READ of the path -- see `T271-RESTORE:` below, which is the measured line. The
#       summary lines no longer assert it. [../../reviews/T293/red/t293-neutered-probe.sh.txt]
#
# THIS FILE'S FIRST DRAFT WAS ITSELF FAIL-OPEN, AND T259's LINT CAUGHT IT ON THE RUN THAT
# INTRODUCED IT. It read `python3 "$LINT" | grep "$ROW" || echo "(row not on the frontier)"`,
# which prints the same reassuring absence whether grep found nothing (exit 1) or grep BROKE
# (exit >1) -- *`git grep`/`grep` exits 1 on NO MATCH and >1 on ERROR* (P-81), inside a probe
# written to expose a fail-open. Kept in the record rather than quietly repaired: three
# instruments in this program have died on this exact line shape. The repair is below -- the
# linter's status and grep's status are each captured and CLASSIFIED, and >1 is a hard ERROR.
#
# EXIT 0 = the contingency was DEMONSTRATED (the defect is real and reproduced)
#      1 = REFUTED: the classification did not move with the file
#      2 = ERROR: an instrument could not be run or a search broke. NEVER an absence.
#
# T293 -- WHAT EXIT 1 MEANS NOW, BECAUSE IT INVERTED AND NOTHING NOTICED FOR A WHOLE FIRE.
# The legend above was written when the defect was live, so exit 1 read as "T271's explanation
# is WRONG and must not be quoted". THAT READING IS NOW FALSE and it repudiates the evidence
# P-88 rests on. This probe cannot tell "never true" from "true, then REPAIRED" -- both give
# A == B == C. As of T273 (commit 7e85a3e) the second is the case: `02-escape-matrix-fix.sh`
# line 6 no longer hard-codes the path at all, it is a `mktemp -d` scratch dir, so the
# classification correctly stops moving with the file. T293 ran this probe and measured
# `T271-TMPDEP: REFUTED contingent=0` in both the found-ABSENT and found-PRESENT arms.
#
#   READ IT THIS WAY:  exit 1 = T273'S REPAIR STILL HOLDS. This is the healthy result.
#                      exit 0 = THE REPAIR HAS REGRESSED -- a literal path is back in the
#                               linter's corpus and the bar's colour is host-decided again.
#
# So the probe is now a REGRESSION TEST, and its subject path must stay a literal for exactly
# the reason it always did: naming the path IS the measurement.
#
# NOTHING CALLS THIS FILE, AND T293 DECIDED THAT IS CORRECT RATHER THAN LEAVING IT UNSAID (P-45,
# P-89). `guard_no_host_state_in_lint_corpus` in .softhouse/conformance.sh ALREADY covers the
# regression: 02-escape-matrix-fix.sh is in that census's population, so putting the literal back
# adds a census row and the bar goes EXIT 2 — measured by T293, restore verified. Wiring this
# probe too would cost ~19s per bar for a duplicate signal. What it still gives a human is the
# EXPLANATION behind that row, which is why it is kept and repaired rather than deleted.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
LINT="$ROOT/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
TARGET=/tmp/t234_matrix2.txt
ROW='02-escape-matrix-fix.sh'
# An ABSOLUTE path on purpose: a bare invocation may resolve to bundled ugrep, which carries a
# hidden --exclude-dir and silently narrows the corpus (P-75).
SEARCH=/usr/bin/grep

[ -f "$LINT" ] || { echo "ERROR: the fail-open linter is absent: $LINT" >&2; exit 2; }

# The state as FOUND, captured before anything is touched, and restored by the trap on every exit
# path BASH CAN TRAP -- normal, `set -e`, INT, TERM, HUP. NOT SIGKILL, which no shell can trap and
# which T293 measured leaving this file PRESENT after it was found ABSENT. A probe that leaves the
# host different from how it found it is not a probe; it is an edit nobody reviewed.
WAS_PRESENT=0
if [ -e "$TARGET" ]; then WAS_PRESENT=1; fi   # `[ ] && x=1` would abort under `set -e`
restore_found_state() {
  if [ "$WAS_PRESENT" -eq 1 ]; then
    printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n' > "$TARGET"
  else
    rm -f "$TARGET"
  fi
  # THE RESTORATION CLAIM IS RE-READ FROM THE PATH, NEVER ASSERTED. [T293]
  # This line is emitted by the trap, AFTER the restore, from a fresh `[ -e ]` -- so deleting
  # the restore above makes it print `restored=0`, where the old hard-coded `restoredAsFound=1`
  # in the summary lines printed `1` regardless and was measured doing exactly that.
  local now=0
  if [ -e "$TARGET" ]; then now=1; fi
  local ok=0
  if [ "$now" -eq "$WAS_PRESENT" ]; then ok=1; fi
  echo "T271-RESTORE: foundPresent=$WAS_PRESENT nowPresent=$now restored=$ok"
}
# EXIT covers normal and `set -e` exits. INT/TERM/HUP are named EXPLICITLY so the intent is
# readable rather than inferred from the shell's signal semantics; each re-raises after the
# EXIT trap runs. SIGKILL IS NOT TRAPPABLE BY ANY SHELL and is disclosed in the header, not
# covered -- T293 measured it leaving the file PRESENT after finding it ABSENT.
trap restore_found_state EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

# One reading of the frontier row. NO PIPELINE, and every exit status classified.
reading() {
  local out json lrc=0 grc=0 row
  out="$(mktemp)"
  json="$(mktemp)"
  FAILOPEN_LINT_JSON="$json" python3 "$LINT" >"$out" 2>&1 || lrc=$?
  if [ "$lrc" -ne 0 ] && [ "$lrc" -ne 1 ]; then
    echo "ERROR: the linter exited $lrc, which is neither clean (0) nor violations (1)." >&2
    rm -f "$out" "$json"
    return 2
  fi
  row="$("$SEARCH" "^FAILOPEN-FRONTIER.*$ROW" "$out")" || grc=$?
  rm -f "$out" "$json"
  case "$grc" in
    0) printf '%s\n' "$row" ;;
    1) printf '%s\n' "(row NOT on the frontier -- search exit 1, a TRUE no-match, P-81)" ;;
    *) echo "ERROR: the search exited $grc. That is an ERROR, not a no-match (P-81), and this" >&2
       echo "       probe will not report an absence it did not measure." >&2
       return 2 ;;
  esac
}

echo "T271 -- is the conformance bar's GREEN contingent on a file in /tmp? (P-88's shape)"
echo "================================================================================"
echo "  repo   : $ROOT"
echo "  linter : .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
echo "  probe  : $TARGET"
echo ""

echo "--- READING A: $TARGET ABSENT (the state this worktree is in) ---"
rm -f "$TARGET"
if [ -e "$TARGET" ]; then ls -la "$TARGET"; else echo "    (not present)"; fi
A="$(reading)"
echo "    $A"
echo ""

echo "--- READING B: the SAME tree, byte for byte, with the /tmp file PRESENT ---"
printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n' > "$TARGET"
if [ -e "$TARGET" ]; then ls -la "$TARGET"; else echo "    (not present)"; fi
B="$(reading)"
echo "    $B"
echo ""

echo "--- READING C: the file removed again, to show the flip is not one-way ---"
rm -f "$TARGET"
if [ -e "$TARGET" ]; then ls -la "$TARGET"; else echo "    (not present)"; fi
C="$(reading)"
echo "    $C"
echo ""

echo "NOT CAUSED BY T271 -- the three files involved are untouched on this branch:"
# Against the MERGE BASE, not against `main`. `main` moves under a running fire, and diffing a
# moving ref would let somebody else's later edit to t234 read as T271's. BASE is resolved
# explicitly and its failure is an ERROR, never an empty diff read as innocence.
BASE=""
BASE="$(git -C "$ROOT" merge-base HEAD main)" || {
  echo "ERROR: could not resolve merge-base(HEAD, main); refusing to print an innocence claim" >&2
  exit 2
}
echo "    merge base: $BASE"
git -C "$ROOT" diff --stat "$BASE" -- \
  .softhouse/capture/t234-sweep-instrument-audit/ \
  .softhouse/conformance.sh \
  .softhouse/capture/t238-failopen/
echo "    (no diff lines above means T271 changed none of them)"
echo ""

if [ "$A" != "$B" ] && [ "$A" = "$C" ]; then
  echo "CONCLUSION: the tree is IDENTICAL across all three readings and the classification MOVED."
  echo "The conformance bar's exit code is decided by whether a file exists in /tmp. That is"
  echo "P-88's shape in a different guard: a green that depends on scratch state outside the repo."
  echo ""
  if [ "$WAS_PRESENT" -eq 1 ]; then FOUND=PRESENT; else FOUND=ABSENT; fi
  echo "HOST STATE: $TARGET was $FOUND when this probe started and is put back that way by the"
  echo "EXIT trap. T271 neither manufactures the green nor forces the red on a host it shares"
  echo "with other workers."
  echo "T271-TMPDEP: DEMONSTRATED contingent=1 foundPresent=$WAS_PRESENT restore=see-T271-RESTORE-line"
  exit 0
fi
echo "CONCLUSION: the classification did NOT move with the file."
echo "TWO READINGS, AND THIS PROBE CANNOT TELL THEM APART -- decide it from the tree, not here:"
echo "  (a) T273'S REPAIR HOLDS. 02-escape-matrix-fix.sh no longer hard-codes the path, so the"
echo "      classification is a property of the tree. THIS IS THE EXPECTED RESULT since 7e85a3e."
echo "  (b) the hypothesis was never true, and T271's account of the red bar is wrong."
echo "Check which by reading 02-escape-matrix-fix.sh line 6. Do NOT quote this exit as (b) alone."
echo "T271-TMPDEP: REFUTED contingent=0 foundPresent=$WAS_PRESENT restore=see-T271-RESTORE-line"
exit 1
