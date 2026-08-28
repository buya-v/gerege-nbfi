#!/usr/bin/env bash
# =============================================================================================
# T364 -- THE REVIEWER'S FORGE DRIVE against T358's REACHED-BY direction and its widened
# population. Written for the T364 independent review of branch softhouse/T358-t323-conditions.
#
# EVERY ARM RUNS THE WHOLE BAR (`bash .softhouse/conformance.sh`), never a guard standalone.
# T323's first graded run is the standing proof that a standalone green says nothing about the
# wired route, and T358 walked into the same lesson again with a quadratic substitution that
# only the whole bar caught.
#
# EACH ARM RECORDS THREE FACTS AND ALL THREE MUST MATCH:
#   EXIT    the bar's exit status. 2 == EXIT_UNUSABLE == "no verdict is available".
#   PROBE   whether the `reference oracle (...) probe = up|down` line was PRINTED. PRESENCE is
#           established before any value is read -- that is P-84, "'EXIT 2 WITH NO PROBE LINE'
#           IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."
#           [VERIFIED: .softhouse/patterns.md:2813]. NOT P-83, which the T364 brief and T358's
#           own drive both cite for this rule; P-83 is "TWO INDEPENDENT MOVEMENTS OF ONE PINNED
#           NUMBER RECONCILE BY RUNNING, NEVER BY ARITHMETIC" [VERIFIED: patterns.md:2806] --
#           which is the rule about the MERGE RESULT, not about the probe line. See T364 NOTE-3.
#   MARKER  whether the specific text this arm predicts is present.
#
# *** READ THE `want` COLUMN BEFORE READING THE VERDICT. ***
# Three of these arms (F1, F3, F4) assert EXIT 0 because I predict a FAIL-OPEN. A PASS on
# those three is A DEFECT FOUND, not a guard working. Each is paired with a control that
# differs in exactly one identifier, so the difference cannot be attributed to anything else.
#
# NO HOST-STATE LITERAL IS ASSIGNED TO A NAME ANYWHERE IN THIS FILE. A tracked .sh that
# assigns a literal /tmp path to a variable is exactly what guard_no_host_state_in_lint_corpus
# pins at 18 sites, and this file enters that corpus the moment it is committed. A reviewer's
# instrument that turns the bar red is a reviewer who has not read his own review. Temporary
# files come from `mktemp`; the transcript directory is an argument.
#
# EVERY `.softhouse/`-ROOTED PATH IS ASSEMBLED AT RUN TIME from a directory that exists. This
# file also enters T316's dead-path corpus, and a glob or a leaf spelled whole would read there
# as a path that resolves to nothing. T323's drive learned that with five frontier rows.
#
# USAGE:  bash drive-forge-t364.sh <scratch-clone-root> [transcript-dir]
# =============================================================================================
set -u
SCRATCH="${1:?usage: drive-forge-t364.sh <scratch-clone-root> [transcript-dir]}"
OUTDIR="${2:-$SCRATCH/..}"
[ -d "$SCRATCH/.git" ] || { echo "not a git clone: $SCRATCH" >&2; exit 2; }

PASSES=0; FAILS=0
GUARDS_REL=".softhouse/guards"
GUARDS_DIR="$SCRATCH/$GUARDS_REL"
LG_LEAF="ledgerguard"
PROBE_LEAF="zz-t364-checker"
MAIN_LEAF="main.go"
UNIQUE_LEAF="zz-t364-unique-checker.go"
SELF1_LEAF="zz-t364-selfcert.sh"
SELF2_LEAF="zz-t364-selfcert2.sh"
SELF3_LEAF="zz-t364-selfcert3.sh"

# The directive spelled ONCE, here, never retyped in an arm.
MARKER_WORD="GUARDS-DIR-REGISTRATION:"

reset_tree() {
  ( cd "$SCRATCH" && git reset -q --hard HEAD \
      && git clean -qfd .softhouse >/dev/null 2>&1 ) || true
}

arm() {
  local name="$1" want_exit="$2" want_probe="$3" marker="$4" fn="$5"
  local out rc probe marker_seen verdict
  reset_tree
  "$fn" || { echo "ARM $name: MUTATION FAILED TO APPLY" >&2; FAILS=$((FAILS+1)); return; }
  out="$(mktemp "${TMPDIR:-/tmp}/t364-forge.XXXXXXXX")"
  ( cd "$SCRATCH" && bash .softhouse/conformance.sh ) >"$out" 2>&1
  rc=$?
  # PRESENCE of the probe line is established before anything reads its value. P-84 --
  # "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."
  # [VERIFIED: .softhouse/patterns.md:2813].
  if LC_ALL=C grep -q 'reference oracle (.*) probe = ' "$out"; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi
  verdict=PASS
  [ "$rc" = "$want_exit" ]     || verdict=FAIL
  [ "$probe" = "$want_probe" ] || verdict=FAIL
  [ "$marker_seen" = YES ]     || verdict=FAIL
  printf '%-46s exit=%-2s (want %-2s)  probe=%-8s (want %-8s)  marker=%-3s  >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$verdict"
  LC_ALL=C grep -E "$MARKER_WORD population|REACHED-BY |INVOKED    " "$out" | sed 's/^/      /'
  if [ "$verdict" = FAIL ]; then FAILS=$((FAILS+1)); else PASSES=$((PASSES+1)); fi
  cp "$out" "$OUTDIR/t364-forge-$name.txt" 2>/dev/null || true
  rm -f "$out"
}

m_none() { :; }

# ---------------------------------------------------------------------------------------------
# FORGE 1 / CONTROL 2 -- IS THE `.go` CLASS ACTUALLY CLOSED, OR ONLY CLOSED FOR BASENAMES THAT
# DO NOT ALREADY APPEAR IN THE HARNESS?
#
# The invocation test is `case "$code" in *"$base"*)` over the comment-stripped harness, and
# `base` is the member's BASENAME. After T358's own DECLARATION-TABLE cut, the literal string
# "main.go" still occurs on TWO non-comment lines of conformance.sh -- a `local ccsrc=` and a
# `say`, both belonging to a DIFFERENT guard that reads that file's TEXT. So I predict that a
# genuinely unwired Go checker named main.go, in a brand-new subdirectory, is absolved
# automatically and the bar stays GREEN.
#
# F2 is the control and plants the SAME file under a unique basename. The two arms differ in
# exactly one identifier. If F1 is green and F2 is red, the basename is the whole difference.
# ---------------------------------------------------------------------------------------------
f1_unwired_main_go() {
  mkdir -p "$GUARDS_DIR/$PROBE_LEAF" || return 1
  { printf 'package main\n\n'
    printf 'func main() { println("T364 forge: an unwired Go checker. Nothing runs me.") }\n'
  } > "$GUARDS_DIR/$PROBE_LEAF/$MAIN_LEAF" || return 1
  ( cd "$SCRATCH" && git add -A "$GUARDS_REL/$PROBE_LEAF/$MAIN_LEAF" ) || return 1
}

f2_unwired_unique_go() {
  mkdir -p "$GUARDS_DIR/$PROBE_LEAF" || return 1
  { printf 'package main\n\n'
    printf 'func main() { println("T364 forge: an unwired Go checker. Nothing runs me.") }\n'
  } > "$GUARDS_DIR/$PROBE_LEAF/$UNIQUE_LEAF" || return 1
  ( cd "$SCRATCH" && git add -A "$GUARDS_REL/$PROBE_LEAF/$UNIQUE_LEAF" ) || return 1
}

# ---------------------------------------------------------------------------------------------
# FORGE 3 / FORGE 4 / CONTROL 5 -- CAN A MEMBER VOUCH FOR ITSELF AFTER ALL?
#
# T358's guard refuses a REACHED-BY row whose witness IS the member, and its arm 20 drives that
# red. The test is a RAW STRING COMPARISON, `[ "$self_wit" = "$rel" ]`, while every other step
# in the chain normalises: `-f "$REPO_ROOT/./p"` resolves, and `git ls-files --error-unmatch`
# accepts both `./p` and `a/../p` and normalises them to `p`. The witness-names-the-member grep
# is then satisfied BY THE ROW'S OWN TEXT, because the row contains the member's basename.
#
# So I predict that one line -- the member naming ITSELF with a leading './' -- passes all four
# verifications and the bar stays GREEN. F5 is the control: the exact self-reference, no prefix,
# which must still go RED.
# ---------------------------------------------------------------------------------------------
plant_selfcert() {
  # $1 = leaf, $2 = the witness path exactly as it should appear in the row
  local leaf="$1" witness="$2"
  { printf '#!/usr/bin/env bash\n'
    printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$witness"
    printf 'echo "T364 forge: nothing in this repository invokes me."\n'
  } > "$GUARDS_DIR/$leaf" || return 1
  ( cd "$SCRATCH" && git add -A "$GUARDS_REL/$leaf" ) || return 1
}

f3_selfcert_dotslash() { plant_selfcert "$SELF1_LEAF" "./$GUARDS_REL/$SELF1_LEAF"; }
f4_selfcert_dotdot()   { plant_selfcert "$SELF2_LEAF" "$GUARDS_REL/$LG_LEAF/../$SELF2_LEAF"; }
f5_selfcert_exact()    { plant_selfcert "$SELF3_LEAF" "$GUARDS_REL/$SELF3_LEAF"; }

echo "============================================================================================"
echo "T364 FORGE DRIVE -- the reviewer's own arms against T358. Whole bar, every arm."
echo "scratch: $SCRATCH"
echo "head:    $( cd "$SCRATCH" && git rev-parse HEAD )"
echo "============================================================================================"

# The green control comes FIRST. A bar that refuses everything refuses correctly by
# accident, and every arm below would then be meaningless. It also re-reads the census line
# verbatim, so a selector that silently stopped matching fails here.
arm "F0-GREEN-CONTROL"                0 PRESENT 'GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0' m_none

arm "F1-unwired-main.go-ABSOLVED"     0 PRESENT 'VERDICT: PASS \(exit 0\)'      f1_unwired_main_go
arm "F2-CONTROL-unwired-unique.go"    2 ABSENT  'IS INVOKED BY NOTHING'         f2_unwired_unique_go
arm "F3-selfcert-via-dotslash"        0 PRESENT 'VERDICT: PASS \(exit 0\)'      f3_selfcert_dotslash
arm "F4-selfcert-via-dotdot"          0 PRESENT 'VERDICT: PASS \(exit 0\)'      f4_selfcert_dotdot
arm "F5-CONTROL-selfcert-exact"       2 ABSENT  'declares REACHED-BY ITSELF'    f5_selfcert_exact

reset_tree
echo "============================================================================================"
echo "T364 FORGE DRIVE: $PASSES arms matched their prediction, $FAILS did not."
echo "F1, F3 and F4 PREDICT A FAIL-OPEN and assert exit 0. A PASS on those three is a DEFECT"
echo "FOUND. F2 and F5 are their controls and must be RED."
echo "============================================================================================"
