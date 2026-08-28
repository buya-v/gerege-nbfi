#!/usr/bin/env bash
# =============================================================================================
# T358 -- THE RED DRIVE FOR T337'S CONDITIONS C-1..C-5 ON guard_guards_dir_registration.
#
# IT DOES NOT REPLACE drive-red-t323.sh; IT RUNS IT FIRST, AS ARM SET 1. Copying T323's fifteen
# arms in here would create a second hand-maintained copy of an instrument that already exists,
# and the two would rot against each other the moment either moved -- which is the shape P-86
# names, "THE CORRECTED CARDINAL ROTTED IN THE PLACE IT WAS RESTATED"
# [VERIFIED: .softhouse/patterns.md, P-86]. So T323's drive stays authoritative for its own
# arms and this file adds only what T358 changed.
#
# EVERY ARM RUNS THE WHOLE BAR (`bash .softhouse/conformance.sh`), NEVER THE GUARD STANDALONE.
# A standalone green says nothing about the wired route; that is T323's own thesis and its first
# graded run proved it the expensive way.
#
# IT DRIVES A SCRATCH CLONE, NEVER THE WORKING TREE.
#
# WHAT EACH ARM RECORDS, and why these three facts:
#   EXIT    the bar's exit status. 2 == EXIT_UNUSABLE == "no verdict is available".
#   PROBE   whether the `reference oracle (...) probe = up|down` line was PRINTED.
#   MARKER  whether the specific refusal text this arm predicts is present.
#
# P-84 IS WHY `PROBE` IS A COLUMN -- "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE
# ABSENCE, NOT THE VALUE." [VERIFIED: .softhouse/patterns.md:2813]. The driver's park condition
# is exit 2 AND a probe line PRESENT reading `down`. A failed HARD guard exits 2 BEFORE
# probe_oracle is reached, so the line is ABSENT, and a reader must still tell those apart.
# Every red arm asserts EXIT=2 AND PROBE=ABSENT; every green arm asserts EXIT=0 AND
# PROBE=PRESENT. A red arm that ever shows PROBE=PRESENT means the wiring broke P-84 and the
# arm FAILS. P-83 is honoured by testing PRESENCE before reading any value.
#
# EVERY PLANTED PATH IS ASSEMBLED AT RUN TIME. This file is a TRACKED instrument, so T316's
# dead-path census reads it like any other; a `.softhouse/`-rooted literal that does not resolve
# would put a row on the frontier and turn the very bar these arms measure red. T323's drive
# learned that with five rows. Leaves are held as separate variables and concatenated.
#
# USAGE:  bash drive-red-t358.sh /path/to/scratch/clone
# =============================================================================================
set -u

SCRATCH="${1:?usage: drive-red-t358.sh <scratch-clone-root>}"
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
  out="$(mktemp "${TMPDIR:-/tmp}/t358-arm.XXXXXXXX")"
  ( cd "$SCRATCH" && bash .softhouse/conformance.sh ) >"$out" 2>&1
  rc=$?
  # P-83: PRESENCE of the probe line is established before anything reads its value.
  if LC_ALL=C grep -q 'reference oracle (.*) probe = ' "$out"; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi

  verdict=PASS
  [ "$rc" = "$want_exit" ]        || verdict=FAIL
  [ "$probe" = "$want_probe" ]    || verdict=FAIL
  [ "$marker_seen" = YES ]        || verdict=FAIL

  printf '%-52s exit=%-2s (want %-2s)  probe=%-8s (want %-8s)  marker=%-3s  >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$verdict"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1))
    echo "    --- transcript tail ---"
    LC_ALL=C tail -30 "$out" | sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
  cp "$out" "$SCRATCH/../t358-arm-$name.txt" 2>/dev/null || true
  rm -f "$out"
}

# ---------------------------------------------------------------------------------------------
# ASSEMBLED PATHS. Nothing below is spelled as a whole `.softhouse/`-rooted literal that fails to
# resolve; `$GUARDS_DIR` names a directory that EXISTS and every leaf is concatenated onto it.
# ---------------------------------------------------------------------------------------------
GUARDS_DIR="$SCRATCH/.softhouse/guards"
GUARDS_REL=".softhouse/guards"
LG_LEAF="ledgerguard"
TD_LEAF="testdata"
FIXTURE_LEAF="setup.sh"
MAIN_LEAF="main.go"
PY_LEAF="zz-t358-planted-checker.py"
GO_LEAF="zz-t358-planted-checker.go"
GHOST_LEAF="a-witness-that-was-never-committed.txt"

FIXTURE_DIR="$GUARDS_DIR/$LG_LEAF/$TD_LEAF"
FIXTURE_ABS="$FIXTURE_DIR/$FIXTURE_LEAF"
FIXTURE_REL="$GUARDS_REL/$LG_LEAF/$TD_LEAF/$FIXTURE_LEAF"
MAIN_ABS="$GUARDS_DIR/$LG_LEAF/$MAIN_LEAF"
MAIN_REL="$GUARDS_REL/$LG_LEAF/$MAIN_LEAF"
LEDGER_WITNESS_REL="$GUARDS_REL/check-ledger-invariants.sh"

# The directive spelled ONCE, here, and never retyped in an arm.
MARKER_WORD="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$1"; }

# Plant the ordinary Go test fixture T337 used to turn the whole bar red, and TRACK it -- an
# untracked file is invisible to `git ls-files` and would prove nothing.
plant_fixture() {
  mkdir -p "$FIXTURE_DIR" || return 1
  { printf '#!/bin/sh\n'
    printf 'echo "ordinary test fixture, planted by the T358 red drive"\n'
  } > "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
}

# Make main.go NAME the fixture, the way the test that consumes a fixture actually would. The
# line is inserted immediately after main.go's own machine-read row, so the file stays a valid
# Go source and stays gofmt-clean (both are `//` comment lines in the same header block).
main_names_fixture() {
  ( cd "$SCRATCH" && LC_ALL=C python3 - "$MAIN_REL" "$FIXTURE_LEAF" <<'PY'
import io, sys
p, leaf = sys.argv[1], sys.argv[2]
s = io.open(p, encoding="utf-8").read()
anchor = "REACHED-BY"
i = s.find(anchor)
if i < 0:
    sys.exit("main.go carries no REACHED-BY row to anchor against")
j = s.index("\n", i) + 1
add = "// The T358 red drive: this module's fixture is %s, opened by the tests below.\n" % leaf
io.open(p, "w", encoding="utf-8").write(s[:j] + add + s[j:])
PY
  ) || return 1
  LC_ALL=C grep -qF -- "$FIXTURE_LEAF" "$MAIN_ABS" || return 1
}

# =============================================================================================
# C-1 -- THE DEPTH-CROSSING SELECTOR. RED, THEN GREEN, BOTH DRIVEN HERE.
#
# T337 planted this exact file and took the whole bar to exit 2 with the probe absent. T358 does
# NOT answer that by narrowing the selector to one directory level: that would buy the fixture's
# peace by no longer looking one directory down, trading T337's F-1 for a larger F-3. The
# selector still reaches ANY DEPTH -- now with ':(glob)' magic, so the depth is DECLARED rather
# than inherited from an fnmatch accident -- and the fixture's remedy is a row the tripping task
# can write in its OWN files.
#
# ARM 15 is therefore still RED, deliberately: an unexplained file under the guards tree is a
# refusal. ARM 16 is the same tree plus TWO LINES, both inside the ledgerguard module, and it is
# GREEN. Arm 16 is the load-bearing one: it is the proof that the remedy is performable in
# scope, which is the whole of T337 F-T337-2.
# =============================================================================================
m_15_fixture_undeclared() { plant_fixture; }

m_16_fixture_declared_in_grant() {
  plant_fixture || return 1
  main_names_fixture || return 1
  # One line in the fixture's own header, naming a witness inside the same module.
  ( directive "$MAIN_REL"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" "$MAIN_REL" ) || return 1
}

# =============================================================================================
# THE DECLARATION IS VERIFIED, NEVER BELIEVED -- four ways it can be false, four refusals.
# Without these arms REACHED-BY would be a self-certification hole: any task could silence the
# guard by asserting a sentence about itself.
# =============================================================================================
# 17 -- the witness EXISTS and is TRACKED but DOES NOT NAME the member.
m_17_witness_does_not_name() {
  plant_fixture || return 1
  ( directive "$MAIN_REL"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
  ! LC_ALL=C grep -qF -- "$FIXTURE_LEAF" "$MAIN_ABS" || return 1
}
# 18 -- the witness DOES NOT EXIST.
m_18_witness_missing() {
  plant_fixture || return 1
  ( directive "$GUARDS_REL/$GHOST_LEAF"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
}
# 19 -- the witness exists and names the member, but is UNTRACKED. Host state: absent from every
# commit, unreviewable, and different in every worktree.
m_19_witness_untracked() {
  plant_fixture || return 1
  printf 'this untracked file names %s and nothing else\n' "$FIXTURE_LEAF" \
    > "$GUARDS_DIR/$GHOST_LEAF" || return 1
  ( directive "$GUARDS_REL/$GHOST_LEAF"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  # The fixture is tracked; the WITNESS deliberately is not.
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
}
# 20 -- the member declares ITSELF. Trivially "named by the witness", and the one shape that
# would make the whole direction worthless.
m_20_self_witness() {
  plant_fixture || return 1
  ( directive "$FIXTURE_REL"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
}

# 26 -- THE GREEDY STRIP. The witness is lifted with `${row##*REACHED-BY}`, which strips to the
# LAST occurrence of the marker, so a row naming the marker twice leaves an EMPTY witness. An
# unreadable row must be an ERROR and never a pass -- that branch is otherwise unreachable, and
# a branch nobody has seen fire is a branch nobody has tested (P-22).
m_26_unreadable_row() {
  plant_fixture || return 1
  ( printf '# %s REACHED-BY REACHED-BY\n' "$MARKER_WORD"; cat "$FIXTURE_ABS" ) > "$FIXTURE_ABS.tmp" || return 1
  mv "$FIXTURE_ABS.tmp" "$FIXTURE_ABS" || return 1
  ( cd "$SCRATCH" && git add -A "$FIXTURE_REL" ) || return 1
}

# =============================================================================================
# C-3 -- THE POPULATION IS NO LONGER SHELL-ONLY. T323's handoff claimed "a fourth unwired checker
# cannot land"; with a '*.sh' population a Python or Go checker landed unseen, and a Go checker
# lives in this directory today. These two arms are the proof the claim now matches the search.
# =============================================================================================
m_21_python_checker_unwired() {
  { printf '#!/usr/bin/env python3\n'
    printf 'print("planted by the T358 red drive; invoked by nothing")\n'
  } > "$GUARDS_DIR/$PY_LEAF" || return 1
  ( cd "$SCRATCH" && git add -A "$GUARDS_REL/$PY_LEAF" ) || return 1
}
# A GO checker, and one directory DOWN -- the two widenings at once. Placed in the module's
# testdata directory so it is not compiled into the ledgerguard package.
m_22_go_checker_unwired_nested() {
  mkdir -p "$FIXTURE_DIR" || return 1
  { printf 'package main\n\n'
    printf 'func main() { println("planted by the T358 red drive; invoked by nothing") }\n'
  } > "$FIXTURE_DIR/$GO_LEAF" || return 1
  ( cd "$SCRATCH" && git add -A "$GUARDS_REL/$LG_LEAF/$TD_LEAF/$GO_LEAF" ) || return 1
}

# =============================================================================================
# THE NEW ROW ON A REAL FILE IS LOAD-BEARING, NOT DECORATION. main.go now carries a REACHED-BY
# row. Both halves of it must be able to fail.
# =============================================================================================
# 23 -- THE DISCRIMINATION ARM, AND IT IS DELIBERATELY GREEN. Strip the REACHED-BY row from
# main.go and the bar does NOT refuse: main.go falls back to INVOKED, because
# conformance.sh:1484 holds `local ccsrc="$REPO_ROOT/<guards>/ledgerguard/main.go"` on a
# non-comment line -- a DIFFERENT guard reading main.go's text, not anything that runs it. That
# is T337 F-T337-4 with a name and a line number: the invocation test proves a file is NAMED,
# never that it is EXECUTED. So the row on main.go is a TRUTH improvement (it records what
# actually reaches the checker) and is NOT what keeps main.go out of the unwired bucket. This
# arm pins that fact rather than hiding it: it asserts the census line SHIFTS from
# reached-by=1/invoked=3 to reached-by=0/invoked=4. If someone later tightens the invocation
# test to require an executed call, THIS ARM GOES RED and tells them main.go now needs its row.
# The load-bearing proofs of REACHED-BY are arms 15-20, 24 and 26, on the planted fixture.
m_23_strip_real_row() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' "/$MARKER_WORD/d" "$MAIN_REL" ) || return 1
  ! LC_ALL=C grep -qF -- "$MARKER_WORD" "$MAIN_ABS" || return 1
}
# 24 -- the WITNESS side of the real row. Rename main.go's mention inside
# check-ledger-invariants.sh and the declaration stops describing anything.
# NOTE, so a reader is not misled by the transcript: this mutation ALSO breaks
# guard_ledger_invariants, which runs earlier in run_guards and refuses on its own. Both refuse,
# both join the same tally, and the marker asserted here is the REGISTRATION guard's sentence
# specifically -- so the arm still proves what it claims.
m_24_real_witness_stops_naming() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' 's/main\.go/entrypoint.go/g' "$LEDGER_WITNESS_REL" ) || return 1
  ! LC_ALL=C grep -qF -- "$MAIN_LEAF" "$SCRATCH/$LEDGER_WITNESS_REL" || return 1
}

# =============================================================================================
# C-5 -- T337's EXTRA ARM, FOLDED IN SO IT STAYS EXERCISED.
#
# T323's drive removes the census (arm 06) and removes the pin (arm 07). It never drives a pin
# that is PRESENT BUT EMPTY, which is the shape most likely to degrade silently: a guard that
# reads zero rows and reports "frontier vs nothing == clean". T337 drove it once by hand and the
# guard refused correctly; an arm driven once by hand and never committed is a guard nobody has
# seen fail since, so it lives here now.
# =============================================================================================
PIN_LEAF="dead-path-frontier.pin"
m_25_pin_present_but_empty() {
  : > "$GUARDS_DIR/$PIN_LEAF" || return 1
  [ ! -s "$GUARDS_DIR/$PIN_LEAF" ] || return 1
}

echo "============================================================================================"
echo "T358 RED DRIVE -- every arm runs the WHOLE BAR, never a guard standalone."
echo "scratch clone: $SCRATCH"
echo "============================================================================================"
echo
echo "--- ARM SET 1: T323's fifteen arms, run unmodified against T358's conformance.sh ---------"
echo "    (no gate T323 pinned may move because T358 widened a population.)"
T323_DRIVE="$SCRATCH/.softhouse/capture/t323-wire-the-unwired-guards/drive-red-t323.sh"
if [ -f "$T323_DRIVE" ]; then
  if bash "$T323_DRIVE" "$SCRATCH"; then
    echo ">>> ARM SET 1: T323 DRIVE PASSED in full."
    PASSES=$((PASSES+1))
  else
    echo ">>> ARM SET 1: T323 DRIVE FAILED. T358 broke an arm T323 relies on."
    FAILS=$((FAILS+1))
  fi
else
  echo ">>> ARM SET 1: T323's drive is MISSING. That is a REFUSAL, not a skip -- this drive"
  echo "    claims to run it, and a claim about a search is not a fact about the world."
  FAILS=$((FAILS+1))
fi
echo
echo "--- ARM SET 2: T358's own arms ------------------------------------------------------------"

m_none() { :; }

# P-50: the green control comes FIRST. A bar that refuses everything refuses correctly by
# accident, and every red arm below would then be meaningless. This arm also re-reads the
# widened population line, so a selector that silently stopped matching would show up here.
arm "00-GREEN-CONTROL-clean-tree"                0 PRESENT 'GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0' m_none

# C-1: RED then GREEN on T337's own planted fixture.
arm "T358-15-nested-fixture-UNDECLARED"          2 ABSENT  'IS INVOKED BY NOTHING'                          m_15_fixture_undeclared
arm "T358-16-nested-fixture-DECLARED-in-grant"   0 PRESENT 'VERDICT: PASS \(exit 0\)'                       m_16_fixture_declared_in_grant

# The declaration is verified, never believed.
arm "T358-17-witness-does-not-name-member"       2 ABSENT  'REACHED-BY WITNESS DOES NOT NAME'               m_17_witness_does_not_name
arm "T358-18-witness-does-not-exist"             2 ABSENT  'REACHED-BY WITNESS DOES NOT EXIST'              m_18_witness_missing
arm "T358-19-witness-untracked"                  2 ABSENT  'which is NOT TRACKED'                           m_19_witness_untracked
arm "T358-20-member-declares-ITSELF"             2 ABSENT  'declares REACHED-BY ITSELF'                     m_20_self_witness

arm "T358-26-unreadable-row-empty-witness"       2 ABSENT  'with NO witness path after it'                  m_26_unreadable_row

# C-3: the population is no longer shell-only.
arm "T358-21-python-checker-unwired"             2 ABSENT  'IS INVOKED BY NOTHING'                          m_21_python_checker_unwired
arm "T358-22-go-checker-unwired-NESTED"          2 ABSENT  'IS INVOKED BY NOTHING'                          m_22_go_checker_unwired_nested

# The real row on main.go: arm 23 shows the MEMBER side is NOT load-bearing (main.go falls
# back to INVOKED off conformance.sh:1484) and pins that; arm 24 shows the WITNESS side IS.
arm "T358-23-strip-row-FALLS-BACK-to-INVOKED"    0 PRESENT 'population=6 invoked=4 declared=2 reached-by=0 invoked-by-nothing=0' m_23_strip_real_row
arm "T358-24-real-witness-stops-naming-member"   2 ABSENT  'REACHED-BY WITNESS DOES NOT NAME'               m_24_real_witness_stops_naming

# C-5: T337's extra arm, now committed.
arm "T358-25-pin-PRESENT-BUT-EMPTY"              2 ABSENT  'an empty pin is a failed READ'                  m_25_pin_present_but_empty

reset_tree
echo "============================================================================================"
echo "T358 RED DRIVE: $PASSES passed, $FAILS failed.  (arm set 1 counts as one.)"
echo "============================================================================================"
[ "$FAILS" -eq 0 ]
