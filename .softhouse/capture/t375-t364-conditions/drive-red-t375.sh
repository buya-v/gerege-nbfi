#!/usr/bin/env bash
# =============================================================================================
# T375 -- THE RED DRIVE FOR T364's CONDITIONS C-T364-1, C-T364-2 AND C-T364-4.
#
# IT DOES NOT REPLACE drive-red-t358.sh; IT RUNS IT FIRST, AS ARM SET 1 -- and that drive in
# turn runs T323's as ITS arm set 1, so this one file exercises all three generations. Copying
# the earlier arms in here would create a second hand-maintained copy of an instrument that
# already exists, and the two would rot against each other the moment either moved -- P-86,
# "THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES THE ROT"
# [VERIFIED: .softhouse/patterns.md:2854]. A MISSING predecessor drive is a REFUSAL here, never
# a skip, for the same reason T358 made it one.
#
# EVERY ARM RUNS THE WHOLE BAR (`bash .softhouse/conformance.sh`), NEVER THE GUARD STANDALONE,
# and never `sh` -- `sh .softhouse/conformance.sh` exits 3, which is a refusal to run and not a
# verdict.
#
# IT DRIVES A SCRATCH CLONE, NEVER THE WORKING TREE.
#
# WHAT EACH ARM RECORDS:
#   EXIT    the bar's exit status. 2 == EXIT_UNUSABLE == "no verdict is available".
#   PROBE   whether the `reference oracle (...) probe = up|down` line was PRINTED.
#   MARKER  whether the specific refusal text this arm predicts is present.
#
# P-84 IS WHY `PROBE` IS A COLUMN -- "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE
# ABSENCE, NOT THE VALUE." [VERIFIED: .softhouse/patterns.md:2813]. The driver's park condition
# is exit 2 AND a probe line PRESENT reading `down`; a failed HARD guard exits 2 BEFORE
# probe_oracle is reached, so the line is ABSENT, and a reader must still tell those apart.
# THE PRESENCE OF THE LINE IS ESTABLISHED BEFORE ANY VALUE IS READ, AND THAT RULE IS P-84 --
# NOT P-83. P-83 is "TWO INDEPENDENT MOVEMENTS OF ONE PINNED NUMBER RECONCILE BY RUNNING, NEVER
# BY ARITHMETIC" [VERIFIED: .softhouse/patterns.md:2806], which is a different rule about a
# different question. drive-red-t358.sh cites P-83 for presence-before-value in two places and
# so did the task brief this drive was written from; T364 caught it, and it is CORRECTED HERE
# rather than propagated. [T364 NOTE-3; the ordinals are P-83 :2806 and P-84 :2813.]
#
# P-83 IS HONOURED SEPARATELY AND FOR ITS OWN QUESTION, at the foot of this file: the pinned
# quantities a merge can move are reconciled BY RUNNING THE BAR ON THE MERGE RESULT, never by
# adding this branch's deltas to main's figures.
#
# EVERY PLANTED PATH IS ASSEMBLED AT RUN TIME. This file is a TRACKED instrument, so T316's
# dead-path census reads it like any other; a `.softhouse/`-rooted literal that does not resolve
# would put a row on the frontier and turn the very bar these arms measure red. T323's drive
# learned that with five rows. Leaves are held as separate variables and concatenated.
#
# THE THREE FINDINGS THIS DRIVE IS ABOUT, and none of them touches money, the ledger, a vector,
# a DEC-n or the frozen adapter contract -- all three are wrong PASSes about THE BAR'S OWN
# COVERAGE, which is the class T364 gave conditions for rather than REJECT:
#
#   F-T364-1  an unwired Go checker named `main.go` anywhere under the guards directory read
#             INVOKED and the bar stayed GREEN, because the invocation test matched the
#             BASENAME and `main.go` occurs on two non-comment lines of the harness where a
#             DIFFERENT guard reads that file's text. Closed by matching the member's PATH.
#             ARMS 01, 02 (control) and 03 (the REVERT arm, which reproduces the fail-open).
#
#   F-T364-2  the rule the guard PRINTS -- "a file may not vouch for itself" -- was defeated by
#             a leading `./`, because the self-reference test was the one step in that chain
#             that did not normalise. Closed by comparing the path GIT resolves. ARMS 04..08,
#             with 08 the REVERT arm and 09 the control that the fix does not break a
#             legitimate `./`-spelled witness.
#
#   FU-T358-1 nothing in the bar recorded a wall-clock cost. A guard spun at 99.7% CPU for
#             9m43s while its own comment advertised 0.23 s, and the only detector was a human
#             noticing. ARMS 13..17, driven with a DELIBERATELY SLOW GUARD and its control.
#
# THE TWO REVERT ARMS ARE THE P-22 EVIDENCE AND THEY ARE THE POINT OF THIS FILE. "A guard, a
# canary, or a control that cannot fail is worse than none -- because it is believed"
# [VERIFIED: .softhouse/patterns.md:473]. Arms 03 and 08 UNDO the one-token change each fix
# consists of, in the scratch tree, and assert the bar goes GREEN on the very input the fixed
# bar refuses. A fix whose removal changes nothing was never a fix.
#
# USAGE:  bash drive-red-t375.sh /path/to/scratch/clone
# =============================================================================================
set -u

SCRATCH="${1:?usage: drive-red-t375.sh <scratch-clone-root>}"
[ -d "$SCRATCH/.git" ] || { echo "not a git clone: $SCRATCH" >&2; exit 2; }

PASSES=0
FAILS=0

reset_tree() {
  ( cd "$SCRATCH" && git reset -q --hard HEAD \
      && git clean -qfd .softhouse >/dev/null 2>&1 ) || true
}

# arm <name> <expected-exit> <expected-probe: PRESENT|ABSENT> <marker-regex> <mutation-fn>
arm() {
  local name="$1" want_exit="$2" want_probe="$3" marker="$4" fn="$5"
  local out rc probe marker_seen verdict
  reset_tree
  "$fn" || { echo "ARM $name: MUTATION FAILED TO APPLY" >&2; FAILS=$((FAILS+1)); return; }
  out="$(mktemp "${TMPDIR:-/tmp}/t375-arm.XXXXXXXX")"
  ( cd "$SCRATCH" && bash .softhouse/conformance.sh ) >"$out" 2>&1
  rc=$?
  # P-84: PRESENCE of the probe line is established before anything reads its value.
  if LC_ALL=C grep -q 'reference oracle (.*) probe = ' "$out"; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi

  verdict=PASS
  [ "$rc" = "$want_exit" ]        || verdict=FAIL
  [ "$probe" = "$want_probe" ]    || verdict=FAIL
  [ "$marker_seen" = YES ]        || verdict=FAIL

  printf '%-56s exit=%-2s (want %-2s)  probe=%-8s (want %-8s)  marker=%-3s  >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$verdict"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1))
    echo "    --- transcript tail ---"
    LC_ALL=C tail -40 "$out" | sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
  cp "$out" "$SCRATCH/../t375-arm-$name.txt" 2>/dev/null || true
  rm -f "$out"
}

# ---------------------------------------------------------------------------------------------
# ASSEMBLED PATHS. Nothing below is spelled as a whole `.softhouse/`-rooted literal that fails to
# resolve; `$GUARDS_DIR` names a directory that EXISTS and every leaf is concatenated onto it.
# ---------------------------------------------------------------------------------------------
GUARDS_DIR="$SCRATCH/.softhouse/guards"
GUARDS_REL=".softhouse/guards"
CONF_REL=".softhouse/conformance.sh"
CONF_ABS="$SCRATCH/$CONF_REL"

LG_LEAF="ledgerguard"
TD_LEAF="testdata"
MAIN_LEAF="main.go"
CHECKER_DIR_LEAF="zz-t375-checker"
UNIQUE_GO_LEAF="zz-t375-checker.go"
SELF_DIR_LEAF="zz-t375-selfcert"
SELF_LEAF="zz-t375-selfcert.sh"
FIXTURE_LEAF="zz-t375-fixture.sh"
GHOST_LEAF="a-witness-t375-never-committed.txt"
LEDGER_WITNESS_LEAF="check-ledger-invariants.sh"

MAIN_ABS="$GUARDS_DIR/$LG_LEAF/$MAIN_LEAF"
MAIN_REL="$GUARDS_REL/$LG_LEAF/$MAIN_LEAF"
CHECKER_DIR="$GUARDS_DIR/$CHECKER_DIR_LEAF"
PLANTED_MAIN_ABS="$CHECKER_DIR/$MAIN_LEAF"
PLANTED_MAIN_REL="$GUARDS_REL/$CHECKER_DIR_LEAF/$MAIN_LEAF"
PLANTED_UNIQUE_ABS="$CHECKER_DIR/$UNIQUE_GO_LEAF"
PLANTED_UNIQUE_REL="$GUARDS_REL/$CHECKER_DIR_LEAF/$UNIQUE_GO_LEAF"
SELF_DIR="$GUARDS_DIR/$SELF_DIR_LEAF"
SELF_ABS="$SELF_DIR/$SELF_LEAF"
SELF_REL="$GUARDS_REL/$SELF_DIR_LEAF/$SELF_LEAF"
FIXTURE_DIR="$GUARDS_DIR/$LG_LEAF/$TD_LEAF"
FIXTURE_ABS="$FIXTURE_DIR/$FIXTURE_LEAF"
FIXTURE_REL="$GUARDS_REL/$LG_LEAF/$TD_LEAF/$FIXTURE_LEAF"
LEDGER_WITNESS_REL="$GUARDS_REL/$LEDGER_WITNESS_LEAF"

# The directive spelled ONCE, here, and never retyped in an arm -- so no arm can pass because it
# and the guard happen to agree on a typo.
MARKER_WORD="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$1"; }

# --------------------------------------------------------------------------------------------
# EDITING THE HARNESS IN THE SCRATCH TREE. `sed -i` is not portable between GNU and BSD, so
# every mutation writes a new file and moves it into place. Each one ASSERTS THAT IT CHANGED
# SOMETHING; a mutation that silently failed to apply would make its arm pass for the wrong
# reason, which is the shape this whole drive exists to refuse.
# --------------------------------------------------------------------------------------------
subst_once() {  # subst_once <file> <literal-old-line> <literal-new-line>
  local f="$1" old="$2" new="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$old" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    subst_once: '$old' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t375-subst.XXXXXXXX")" || return 1
  # LITERAL replacement, built from index()/substr(). awk's sub() takes an ERE, and every line
  # this drive rewrites contains `*`, `$`, `(` and `"` — a regex substitution here would either
  # miss or match the wrong thing, and an arm whose mutation silently missed would pass for the
  # wrong reason. That is the defect this whole drive exists to refuse.
  LC_ALL=C awk -v old="$old" -v new="$new" '
    { i = index($0, old)
      if (i > 0) $0 = substr($0, 1, i-1) new substr($0, i + length(old))
      print }
  ' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$new" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}

insert_after() {  # insert_after <file> <literal-anchor-line> <text-to-insert>
  local f="$1" anchor="$2" text="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$anchor" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    insert_after: anchor occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t375-ins.XXXXXXXX")" || return 1
  LC_ALL=C awk -v anchor="$anchor" -v text="$text" '
    { print } index($0, anchor) { print text }
  ' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$text" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}

drop_line() {  # drop_line <file> <literal-line>
  local f="$1" line="$2" tmp n
  n="$(LC_ALL=C grep -cF -- "$line" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    drop_line: '$line' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t375-drop.XXXXXXXX")" || return 1
  LC_ALL=C grep -vF -- "$line" "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$line" "$tmp" && { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}

# --------------------------------------------------------------------------------------------
# MUTATIONS
# --------------------------------------------------------------------------------------------
m_none() { return 0; }

# A genuinely unwired Go checker, TRACKED, in its own new subdirectory, named `main.go`. Nothing
# in the harness calls it and nothing names its path. Before T375 this read INVOKED and the bar
# stayed GREEN (arm 03 reproduces that); after T375 it is INVOKED BY NOTHING.
plant_unwired_maingo() {
  mkdir -p "$CHECKER_DIR" || return 1
  { printf 'package main\n\n'
    printf '// A checker planted by the T375 red drive. Nothing runs it.\n'
    printf 'func main() {}\n'
  } > "$PLANTED_MAIN_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$PLANTED_MAIN_REL" ) || return 1
  # PRECONDITION, asserted rather than assumed: the planted file's own PATH must not already
  # occur in the harness, or this arm would be measuring the residual gap instead of the fix.
  ! LC_ALL=C grep -qF -- "$PLANTED_MAIN_REL" "$CONF_ABS" || return 1
  # ...and its BASENAME MUST occur, or the arm is not about F-T364-1 at all.
  LC_ALL=C grep -qF -- "$MAIN_LEAF" "$CONF_ABS" || return 1
}

# THE CONTROL FOR arm 01. The IDENTICAL file, in the IDENTICAL directory, under a basename that
# does NOT occur in the harness. T364 proved the basename was the whole difference; both
# directions must now be red.
plant_unwired_unique() {
  mkdir -p "$CHECKER_DIR" || return 1
  { printf 'package main\n\n'
    printf '// A checker planted by the T375 red drive. Nothing runs it.\n'
    printf 'func main() {}\n'
  } > "$PLANTED_UNIQUE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$PLANTED_UNIQUE_REL" ) || return 1
  ! LC_ALL=C grep -qF -- "$UNIQUE_GO_LEAF" "$CONF_ABS" || return 1
}

# THE REVERT ARM FOR F-T364-1. Puts the invocation test back to the BASENAME and plants the same
# unwired `main.go`. Expect the bar GREEN and the file reported INVOKED -- i.e. T364's F1
# reproduced on this tree, which is what makes arm 01 evidence rather than an assertion.
revert_invocation_to_basename_and_plant() {
  subst_once "$CONF_ABS" '      *"$rel"*)' '      *"$base"*)' || return 1
  plant_unwired_maingo || return 1
}

# A tracked member that declares REACHED-BY <spelling of its own path>. One helper, four
# spellings, so the arms differ in EXACTLY the spelling and nothing else.
plant_selfcert() {  # $1 = the witness spelling to write into the row
  mkdir -p "$SELF_DIR" || return 1
  { printf '#!/bin/sh\n'
    directive "$1"
    printf 'echo "planted by the T375 red drive"\n'
  } > "$SELF_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$SELF_REL" ) || return 1
}
m_selfcert_exact()    { plant_selfcert "$SELF_REL"; }
m_selfcert_dotslash() { plant_selfcert "./$SELF_REL"; }
m_selfcert_dotdot()   { plant_selfcert "$GUARDS_REL/$LG_LEAF/../$SELF_DIR_LEAF/$SELF_LEAF"; }
m_selfcert_absolute() { plant_selfcert "$SCRATCH/$SELF_REL"; }

# THE REVERT ARM FOR F-T364-2. Puts the self-reference test back to the RAW STRING COMPARE and
# plants the `./` spelling. Expect the bar GREEN with reached-by=2 -- T364's F3 reproduced.
revert_selfcert_to_raw_and_plant_dotslash() {
  subst_once "$CONF_ABS" \
    '        elif [ "$self_wit" = "$rel" ] || [ "$self_norm" = "$rel" ]; then' \
    '        elif [ "$self_wit" = "$rel" ]; then' || return 1
  m_selfcert_dotslash || return 1
}

# THE CONTROL THAT THE NORMALISATION DOES NOT BREAK A LEGITIMATE `./`-SPELLED ROW. A fixture in
# the ledgerguard module declares REACHED-BY `./<main.go>` -- a DIFFERENT tracked file -- and
# main.go is made to name the fixture, exactly as the test that consumes a fixture would. This
# must be ACCEPTED. Without it, "the guard refuses `./`" and "the guard refuses self-reference"
# are indistinguishable, and only the second is the rule.
m_legit_dotslash_witness() {
  mkdir -p "$FIXTURE_DIR" || return 1
  { printf '#!/bin/sh\n'
    directive "./$MAIN_REL"
    printf 'echo "ordinary test fixture, planted by the T375 red drive"\n'
  } > "$FIXTURE_ABS" || return 1
  # PRECONDITION: main.go must not already name the fixture, or "the witness names the member"
  # would be established by accident rather than by this mutation.
  ! LC_ALL=C grep -qF -- "$FIXTURE_LEAF" "$MAIN_ABS" || return 1
  # Anchored on main.go's OWN machine-read row, which occurs exactly once, so the added line
  # lands inside the same `//` header block and main.go stays a valid Go source.
  insert_after "$MAIN_ABS" "$MARKER_WORD" \
    "// The T375 red drive: this module's fixture is $FIXTURE_LEAF, opened by the tests below." \
    || return 1
  LC_ALL=C grep -qF -- "$FIXTURE_LEAF" "$MAIN_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" "$MAIN_REL" ) || return 1
}

# A witness that is a DIRECTORY. git resolves it to every tracked file beneath it, so "the
# witness" would be whichever line came first -- refused as ambiguous.
m_witness_is_directory() {
  mkdir -p "$SELF_DIR" || return 1
  { printf '#!/bin/sh\n'
    directive "$GUARDS_REL"
    printf 'echo "planted by the T375 red drive"\n'
  } > "$SELF_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$SELF_REL" ) || return 1
}

# A witness carrying PATHSPEC MAGIC that resolves to exactly one tracked file. git accepts it;
# the `-f` test on the TYPED spelling must still refuse it. This is the arm that proves T375's
# normalisation did not open the hole it was closing another one.
m_witness_pathspec_magic() {
  mkdir -p "$SELF_DIR" || return 1
  { printf '#!/bin/sh\n'
    directive ":(glob)$LEDGER_WITNESS_REL"
    printf 'echo "planted by the T375 red drive"\n'
  } > "$SELF_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$SELF_REL" ) || return 1
}

# A witness that EXISTS on disk but is NOT TRACKED. Regression control for the one branch T375
# rewrote from a second `git ls-files` call into a test on the captured output.
m_witness_untracked() {
  mkdir -p "$SELF_DIR" || return 1
  printf 'not committed\n' > "$SELF_DIR/$GHOST_LEAF" || return 1
  { printf '#!/bin/sh\n'
    directive "$GUARDS_REL/$SELF_DIR_LEAF/$GHOST_LEAF"
    printf 'echo "planted by the T375 red drive"\n'
  } > "$SELF_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$SELF_REL" ) || return 1
  ( cd "$SCRATCH" && git status --porcelain -- "$GUARDS_REL/$SELF_DIR_LEAF/$GHOST_LEAF" \
      | LC_ALL=C grep -q '^??' ) || return 1
}

# --------------------------------------------------------------------------------------------
# COST ARMS. A DELIBERATELY SLOW GUARD, and its control one number away.
# --------------------------------------------------------------------------------------------
GUARD_ANCHOR='guard_guards_dir_registration() {'

m_slow_guard_breach() { insert_after "$CONF_ABS" "$GUARD_ANCHOR" '  sleep 70'; }
m_slow_guard_under()  { insert_after "$CONF_ABS" "$GUARD_ANCHOR" '  sleep 10'; }
m_cost_no_budget_row() { drop_line "$CONF_ABS" 'guard_capture_namespace|60'; }
m_cost_stale_row() {
  insert_after "$CONF_ABS" 'GUARD_COST_BUDGETS="guard_graded_root_is_this_tree|60' \
    'guard_zz_t375_never_runs|60'
}
m_cost_vacuous_census() {
  subst_once "$CONF_ABS" \
    '  GUARD_COST_TIMED=$((GUARD_COST_TIMED + 1))' \
    '  GUARD_COST_TIMED=$((GUARD_COST_TIMED + 0))'
}

# =============================================================================================
# ARM SET 1 -- THE PREDECESSOR DRIVE, RUN UNMODIFIED. A MISSING DRIVE IS A REFUSAL, NOT A SKIP.
# =============================================================================================
T358_DRIVE="$SCRATCH/.softhouse/capture/t358-t323-conditions/drive-red-t358.sh"
echo "T375 RED DRIVE -- every arm runs the WHOLE BAR, never a guard standalone, never \`sh\`."
echo
echo ">>> ARM SET 1: drive-red-t358.sh, unmodified, against T375's conformance.sh."
echo ">>> (that drive runs drive-red-t323.sh as ITS arm set 1, so all three generations run.)"
reset_tree
if [ -f "$T358_DRIVE" ]; then
  if bash "$T358_DRIVE" "$SCRATCH"; then
    echo ">>> ARM SET 1: T358 DRIVE PASSED in full."
    PASSES=$((PASSES+1))
  else
    echo ">>> ARM SET 1: T358 DRIVE FAILED. T375 broke an arm an earlier task pinned."
    FAILS=$((FAILS+1))
  fi
else
  echo ">>> ARM SET 1: T358's drive is MISSING. That is a REFUSAL, not a skip -- an absent"
  echo ">>> predecessor drive cannot establish that T375 left its arms standing."
  FAILS=$((FAILS+1))
fi
echo

# =============================================================================================
# ARM SET 2 -- T375's OWN ARMS. GREEN CONTROL FIRST (P-50): a guard must stay GREEN on a clean
# tree, or every red arm below proves nothing.
# =============================================================================================
echo ">>> ARM SET 2: T375's own arms."
arm "T375-00-GREEN-CONTROL-clean-tree" 0 PRESENT \
  'GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0' \
  m_none

# ---- F-T364-1: the basename fail-open -------------------------------------------------------
arm "T375-01-unwired-main.go-NOW-REFUSED" 2 ABSENT \
  "$CHECKER_DIR_LEAF/$MAIN_LEAF IS INVOKED BY NOTHING" plant_unwired_maingo
arm "T375-02-CONTROL-unwired-UNIQUE-basename" 2 ABSENT \
  "$UNIQUE_GO_LEAF IS INVOKED BY NOTHING" plant_unwired_unique
arm "T375-03-REVERT-fix-main.go-is-ABSOLVED-again" 0 PRESENT \
  'population=7 invoked=4 declared=2 reached-by=1 invoked-by-nothing=0' \
  revert_invocation_to_basename_and_plant

# ---- F-T364-2: the `./` self-certification bypass -------------------------------------------
arm "T375-04-selfcert-EXACT-spelling" 2 ABSENT \
  'declares REACHED-BY ITSELF' m_selfcert_exact
arm "T375-05-selfcert-via-DOTSLASH" 2 ABSENT \
  'declares REACHED-BY ITSELF' m_selfcert_dotslash
arm "T375-06-selfcert-via-DOTDOT" 2 ABSENT \
  'declares REACHED-BY ITSELF' m_selfcert_dotdot
arm "T375-07-selfcert-via-ABSOLUTE-path" 2 ABSENT \
  'declares REACHED-BY ITSELF' m_selfcert_absolute
arm "T375-08-REVERT-fix-DOTSLASH-is-ACCEPTED-again" 0 PRESENT \
  'population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0' \
  revert_selfcert_to_raw_and_plant_dotslash
arm "T375-09-CONTROL-legit-DOTSLASH-witness-ACCEPTED" 0 PRESENT \
  'population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0' \
  m_legit_dotslash_witness
arm "T375-10-witness-is-a-DIRECTORY" 2 ABSENT \
  'resolves to MORE THAN ONE TRACKED PATH' m_witness_is_directory
arm "T375-11-witness-carries-PATHSPEC-MAGIC" 2 ABSENT \
  'REACHED-BY WITNESS DOES NOT EXIST' m_witness_pathspec_magic
arm "T375-12-witness-UNTRACKED-still-refused" 2 ABSENT \
  'which is NOT TRACKED' m_witness_untracked

# ---- FU-T358-1: the wall-clock record and its ceiling ----------------------------------------
arm "T375-13-SLOW-guard-BREACHES-its-ceiling" 2 ABSENT \
  'took 7[0-9]s, over its 60s CEILING' m_slow_guard_breach
arm "T375-14-CONTROL-slow-but-UNDER-the-ceiling" 0 PRESENT \
  'COST 1[0-9]s / ceiling 60s   guard_guards_dir_registration' m_slow_guard_under
arm "T375-15-guard-with-NO-BUDGET-ROW-refuses" 2 ABSENT \
  'ran with NO BUDGET ROW' m_cost_no_budget_row
arm "T375-16-STALE-budget-row-refuses" 2 ABSENT \
  'guard_zz_t375_never_runs, which this run' m_cost_stale_row
arm "T375-17-VACUOUS-cost-census-refuses" 2 ABSENT \
  'NOT ONE guard was timed' m_cost_vacuous_census

reset_tree
echo
echo "T375 RED DRIVE: $PASSES passed, $FAILS failed. (arm set 1 counts as one.)"
echo "DISTINCT ARMS IN THIS FILE: 18. The line above counts arm set 1 as ONE, so its total is"
echo "18 + 1 = 19 and NOT the sum of every arm that ran -- T364's NOTE-1 charged exactly that"
echo "double-count against T358's '29 arms' label, and the label is spelled here so it cannot"
echo "be inferred wrongly. The predecessor drives report their own counts in their own output."
[ "$FAILS" -eq 0 ]
