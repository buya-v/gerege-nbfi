#!/usr/bin/env bash
# =============================================================================================
# T323 -- THE RED DRIVE FOR THE THREE NEWLY WIRED GUARDS.
#
# EVERY ARM RUNS THE WHOLE BAR (`bash .softhouse/conformance.sh`), NEVER THE GUARD STANDALONE.
# That is the entire point of the task: "a guard that is green because the wiring never reaches
# it is exactly the defect you are fixing". A standalone red drive would re-prove what T299,
# T316 and T319 each already proved, and would say nothing about the wiring.
#
# IT DRIVES A SCRATCH CLONE, NEVER THE WORKING TREE. A live fire holds .softhouse/LOCK in the
# real repo; nothing here touches it, or .git/hooks.
#
# WHAT EACH ARM RECORDS, and why these three facts and not a pass/fail:
#   EXIT        the bar's exit status. 2 == EXIT_UNUSABLE == "no verdict is available".
#   PROBE       whether the `reference oracle (...) probe = up|down` line was PRINTED.
#   MARKER      whether the specific refusal text this arm predicts is present.
#
# P-84 IS WHY `PROBE` IS A COLUMN. "P-84 -- 'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING.
# READ THE ABSENCE, NOT THE VALUE." [VERIFIED: .softhouse/patterns.md:2782]. The driver's park
# condition is `exit 2` AND a probe line PRESENT AND reading `down`. A failed HARD guard exits 2
# BEFORE probe_oracle is reached, so the line is ABSENT -- and a reader must still be able to
# tell that apart from an oracle outage. Every red arm below therefore asserts EXIT=2 AND
# PROBE=ABSENT, and the green arm asserts EXIT=0 AND PROBE=PRESENT. If a red arm ever shows
# PROBE=PRESENT, P-84 has been broken by the wiring and the arm FAILS.
#
# USAGE:  bash drive-red-t323.sh /path/to/scratch/clone
# =============================================================================================
set -u

SCRATCH="${1:?usage: drive-red-t323.sh <scratch-clone-root>}"
[ -d "$SCRATCH/.git" ] || { echo "not a git clone: $SCRATCH" >&2; exit 2; }

PASSES=0
FAILS=0

# A HARD reset, not `git checkout -- .`: several arms stage a DELETION with `git rm`, and a
# checkout does not undo a staged delete. `git clean` is scoped to .softhouse so the Go build
# cache in nexus/ survives and each arm does not pay for a cold rebuild.
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
  out="$(mktemp "${TMPDIR:-/tmp}/t323-arm.XXXXXXXX")"
  ( cd "$SCRATCH" && bash .softhouse/conformance.sh ) >"$out" 2>&1
  rc=$?
  if LC_ALL=C grep -q 'reference oracle (.*) probe = ' "$out"; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi

  verdict=PASS
  [ "$rc" = "$want_exit" ]        || verdict=FAIL
  [ "$probe" = "$want_probe" ]    || verdict=FAIL
  [ "$marker_seen" = YES ]        || verdict=FAIL

  printf '%-46s exit=%-2s (want %-2s)  probe=%-8s (want %-8s)  marker=%-3s  >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$verdict"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1))
    echo "    --- transcript tail ---"
    LC_ALL=C tail -25 "$out" | sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
  cp "$out" "$SCRATCH/../t323-arm-$name.txt" 2>/dev/null || true
  rm -f "$out"
}

# --------------------------------------------------------------------------------------------
# GREEN CONTROL. P-50: a guard must stay GREEN on a clean tree, or every red arm below is
# meaningless -- a bar that refuses everything refuses correctly by accident.
# --------------------------------------------------------------------------------------------
m_none() { :; }

# --------------------------------------------------------------------------------------------
# T299 ARMS
# --------------------------------------------------------------------------------------------
# An UNDOCUMENTED collision: a second directory under an id that already owns one, with no
# OWNER*.md. T319 already owns capture/t319-reconciler-f5, so this makes N=2, required N-1=1,
# present 0.
#
# EVERY PATH THIS DRIVE PLANTS IS ASSEMBLED AT RUN TIME, AND THAT IS NOT COSMETIC.
# ---------------------------------------------------------------------------------------------
# This script is a TRACKED INSTRUMENT, so T316's census reads it like any other. Its first
# version spelled these paths as literals, which put FIVE rows on the dead-path frontier and had
# to be reconciled in conformance.sh. That was wrong twice over:
#
#   (1) It broke arm T299-02. That arm CREATES the collision directory, so the three literals
#       naming it suddenly RESOLVED, the frontier LOST three rows, and the wiring correctly
#       refused with "row(s) GONE from the frontier". The drive was perturbing the very frontier
#       another of its arms was measuring. [MEASURED: the authoritative first run, arm T299-02,
#       exit=2, `5,7d4` against the reconciliation list.]
#
#   (2) It failed T323's OWN test, the one written beside DEADPATH_T323_RECONCILE_LIST: "can the
#       instrument still do its job if the literal goes away? YES -> incidental, REPAIR it."
#       This drive needs *a* directory and *a* non-resolving path; it never needed those
#       particular spellings. All five were INCIDENTAL and should have been repaired, not pinned.
#       Applying the rule to its author's own work is the only reason it is worth writing down.
#
# The mechanics: `$CAP` resolves to a directory that EXISTS, and every leaf is concatenated onto
# it, so no quoted string in this file contains a `.softhouse/` path that fails to resolve. The
# planted instrument's dead literal is written through a `%s` format, which the census classes
# indeterminate rather than dead (PLACEHOLDER_RE, census_dead_paths.py:70 -- grep the SYMBOL,
# the line moves; this citation was stale at :63 one fire after it was written) -- and the literal
# still lands in the PLANTED file, which is what actually drives T316 red.
CAP="$SCRATCH/.softhouse/capture"
COLLIDE_LEAF="t319-a-second-rig"        # any leaf sharing an id with an existing capture dir
DEADPATH_LEAF="t323-a-path-that-does-not-exist/x.json"

m_t299_collision() {
  mkdir -p "$CAP/$COLLIDE_LEAF" || return 1
  echo "planted by T323's red drive" > "$CAP/$COLLIDE_LEAF/NOTE.md" || return 1
  ( cd "$SCRATCH" && git add -A ".softhouse/capture/$COLLIDE_LEAF" ) || return 1
}
# The SAME collision, DOCUMENTED. This is the discrimination arm: if it also went red the guard
# would be measuring "two directories" rather than "two directories and nobody said who owns
# them", and the rule would be "never collide" -- which T299 explicitly rejected because
# renaming a committed evidence directory breaks every transcript citing it by path.
m_t299_documented() {
  mkdir -p "$CAP/$COLLIDE_LEAF" || return 1
  echo "planted by T323's red drive" > "$CAP/$COLLIDE_LEAF/NOTE.md" || return 1
  echo "Owner: T323. This directory is NOT T319's work." \
    > "$CAP/$COLLIDE_LEAF/OWNER-IS-T323-NOT-T319.md" || return 1
  ( cd "$SCRATCH" && git add -A ".softhouse/capture/$COLLIDE_LEAF" ) || return 1
}
# CALIBRATION FAILURE -> exit 2, and the guard's own probe line ABSENT. T299's vacuity refusal:
# remove the known T256/T259 collision the guard calibrates against, and it must refuse rather
# than report a clean tree. A guard that cannot re-find the defect it was written for is not
# measuring anything.
m_t299_decalibrate() {
  ( cd "$SCRATCH" && git rm -rq --ignore-unmatch \
      .softhouse/capture/t256-verdict-predicate .softhouse/capture/t256-toolchain-population ) || return 1
}
# THE WIRING'S OWN ARM, not T299's: the guard is made to print no `namespace: root` line, so
# this harness cannot tell WHICH TREE it inspected. That must be an instrument failure, never a
# pass -- it is the readback that stops the cwd defect T323 measured from returning silently.
m_t299_no_root_line() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' 's/^say "namespace:   root    \$ROOT"$/: # root line suppressed by T323 red drive/' \
      .softhouse/guards/check-capture-namespace.sh ) || return 1
  LC_ALL=C grep -q 'root line suppressed' "$SCRATCH/.softhouse/guards/check-capture-namespace.sh" || return 1
}

# --------------------------------------------------------------------------------------------
# T316 ARMS
# --------------------------------------------------------------------------------------------
# THE FRONTIER GROWS by one row nobody recorded.
m_t316_new_dead_path() {
  local dir="$CAP/t323-wire-the-unwired-guards"
  mkdir -p "$dir" || return 1
  # The dead literal lands in the PLANTED file, not in this one: the `%s` keeps the census from
  # counting this script itself as an instrument naming a dead path.
  printf '#!/bin/sh\ncat ".softhouse/capture/%s"\n' "$DEADPATH_LEAF" \
    > "$dir/PLANTED-dead-path.sh" || return 1
  ( cd "$SCRATCH" && git add -A .softhouse/capture/t323-wire-the-unwired-guards ) || return 1
}
# SELF-REFERENCE, ARM 1: remove the CENSUS the guard depends on. T316's whole point. It must
# exit 2 with its probe line absent -- it must never pass for lack of anything to check.
m_t316_no_census() {
  ( cd "$SCRATCH" && git rm -q --ignore-unmatch \
      .softhouse/capture/t316-dead-path-guards/census_dead_paths.py ) || return 1
}
# SELF-REFERENCE, ARM 2: remove the PIN. Same requirement, different dependency.
m_t316_no_pin() {
  ( cd "$SCRATCH" && git rm -q --ignore-unmatch .softhouse/guards/dead-path-frontier.pin ) || return 1
}
# THE ANTI-AMNESTY ARM, and it is the wiring's own. Do what the handoff asks the NEXT holder of
# the pin to do -- fold every reconciled row INTO the pin, which makes T316's guard GREEN -- but
# do only HALF of it, leaving DEADPATH_T323_RECONCILE_LIST populated. The list is now excusing
# rows that are no longer on the frontier. A pin is a frontier, not an amnesty, so a stale
# reconciliation list must FAIL the bar rather than sit there quietly forever.
#
# THE ROWS ARE READ OUT OF conformance.sh, NEVER RETYPED HERE. A second hand-maintained copy of
# the list would rot against the first the moment either moved -- which is P-86's shape, "the
# corrected cardinal rotted in the place it was RESTATED" -- and this arm would then be driving
# something other than the guard it claims to drive. It went red exactly that way once: the arm
# was written against a 4-row list and the list grew to 9.
#
# T326 REPAIRED THIS ARM, and the reason is the arm's own subject. T323 wrote above that the next
# holder of the pin must "fold these four rows INTO it and empty the list"; T326 held the pin and
# did exactly that. The mutation as written then aborted with "the reconciliation list is EMPTY --
# this arm has nothing to make stale", i.e. THE ARM STOPPED DRIVING THE MOMENT ITS INSTRUCTION WAS
# FOLLOWED. A drive arm that dies when the thing it recommends is done is a guard that only works
# when someone remembers to run it (P-45) with a longer fuse, so it is repaired rather than
# deleted: the anti-amnesty check in guard_dead_path_frontier is still live and still needs
# driving. BOTH DIRECTIONS ARE HANDLED, and both produce the SAME condition -- guard GREEN and
# the list NON-EMPTY -- which is the only condition the arm was ever about.
m_t316_stale_list() {
  ( cd "$SCRATCH" && LC_ALL=C python3 - <<'PY'
import io, re, sys
CONF = ".softhouse/conformance.sh"
PIN = ".softhouse/guards/dead-path-frontier.pin"
conf = io.open(CONF, encoding="utf-8").read()
m = re.search(r"^DEADPATH_T323_RECONCILE_LIST='(.*?)'$", conf, re.S | re.M)
if not m:
    sys.exit("could not read DEADPATH_T323_RECONCILE_LIST out of conformance.sh")
rows = [r for r in m.group(1).splitlines() if r.strip()]
if rows:
    # The list still carries rows the pin does NOT. Do the fold, and only the fold: the guard
    # goes GREEN and the list is left populated, so it is now excusing rows that are pinned.
    with io.open(PIN, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(r + "\n")
    print("appended %d row(s) to the pin, list left populated" % len(rows))
    raise SystemExit(0)
# The list is empty and the pin already carries every row, so the guard is ALREADY green. Make
# the list stale from the other side: populate it with a row that is already pinned. THE ROW IS
# READ OUT OF THE PIN, NEVER RETYPED -- a second hand-maintained copy rots against the first the
# moment either moves, which is P-86's shape and is why this arm went red once already.
pinned = [l.rstrip("\n") for l in io.open(PIN, encoding="utf-8")
          if l.strip() and not l.lstrip().startswith("#")]
if not pinned:
    sys.exit("the pin has no rows -- this arm cannot construct a stale list")
row = pinned[0]
if "'" in row:
    sys.exit("pinned row %r contains a single quote; it cannot be embedded in the shell"
             " assignment this arm rewrites" % row)
new = conf[:m.start(1)] + row + conf[m.end(1):]
if new == conf:
    sys.exit("rewriting DEADPATH_T323_RECONCILE_LIST changed nothing")
io.open(CONF, "w", encoding="utf-8").write(new)
print("populated the list with 1 ALREADY-PINNED row, pin untouched: %s" % row)
PY
  ) || return 1
}

# --------------------------------------------------------------------------------------------
# T319 ARMS
# --------------------------------------------------------------------------------------------
# THE GREEN LEG FAILS: plant T309's shipped single-term predicate into the REAL ready-tasks.py.
# The matrix must catch that the shipped tool now demotes live work.
m_t319_break_tool() {
  ( cd "$SCRATCH" && LC_ALL=C python3 - <<'PY'
import io, re, sys
p = ".softhouse/bin/ready-tasks.py"
s = io.open(p, encoding="utf-8").read()
# Neuter the conjunctive ownership predicate by forcing the demotion decision true.
n = 0
out = []
for line in s.splitlines(True):
    if line.startswith("def task_is_demotable_in_session(") and n == 0:
        out.append(line)
        out.append("    return True  # T323 red drive: T309's single-term predicate\n")
        n += 1
    else:
        out.append(line)
if n == 0:
    sys.exit("could not find task_is_demotable_in_session")
io.open(p, "w", encoding="utf-8").write("".join(out))
PY
  ) || return 1
}
# THE MATRIX'S OWN CONTRACT: `_assert_matrix_can_see_a_redispatch` must fail the WHOLE RUN if no
# cell in the table advances the clock across a re-dispatch. Deleting the cell that catches this
# class has to be a RED run, not a smaller green one -- otherwise the guard quietly shrinks to
# the subset somebody left behind. Driven by making every cell report redispatch=False.
m_t319_blind_matrix() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' 's/redispatch=True/redispatch=False/g' \
      .softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py ) || return 1
  ! LC_ALL=C grep -q 'redispatch=True' "$SCRATCH/.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py" || return 1
}
# The rig itself removed: the ownership predicate becomes UNGRADED, which is a refusal.
m_t319_no_rig() {
  ( cd "$SCRATCH" && git rm -q --ignore-unmatch \
      .softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py ) || return 1
}

# --------------------------------------------------------------------------------------------
# T323 ITERATION-2 ARMS -- guard_guards_dir_registration
# --------------------------------------------------------------------------------------------
# THE GUARD UNDER TEST is the one T323 added to close its OWN structural finding: three guards
# reached nothing, and nothing in conformance.sh stopped a fourth. These three arms drive it
# through the WHOLE BAR, like every arm above.
#
# Paths are ASSEMBLED, for the reason recorded at the top of this file: a literal that stops
# resolving moves T316's frontier, and an instrument must not perturb the thing another of its
# arms measures.
GUARDS_DIR="$SCRATCH/.softhouse/guards"
PLANTED_CHECKER_LEAF="zz-t323-planted-checker.sh"

# ARM 12 -- THE CLASS THIS GUARD EXISTS FOR: a new checker lands in the canonical guards
# directory and nothing in conformance.sh calls it. Before this guard, that was exit 0.
m_t323b_plant_unwired_checker() {
  printf '%s\n' '#!/usr/bin/env bash' \
                'echo "planted by the T323 red drive; invoked by nothing"' \
                'exit 0' > "$GUARDS_DIR/$PLANTED_CHECKER_LEAF" || return 1
  ( cd "$SCRATCH" && git add -A ".softhouse/guards/$PLANTED_CHECKER_LEAF" ) || return 1
}

# ARM 13 -- THE CALLER DECLARATION IS VERIFIED, NOT BELIEVED. repo-state-attest.sh is declared as
# being run by the fire driver. Strip every mention from the fire driver and the declaration is
# now FALSE -- the checker is unwired again and the table is excusing it. Deleting the lines
# (rather than renaming the path) is deliberate: a renamed literal would ALSO move T316's
# frontier, and this arm is about the declaration, not about dead paths.
m_t323b_break_caller_decl() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' '/repo-state-attest/d' .softhouse/bin/fire-program.sh ) || return 1
  ! LC_ALL=C grep -q 'repo-state-attest' "$SCRATCH/.softhouse/bin/fire-program.sh" || return 1
}

# ARM 14 -- THE SUBJECT DECLARATION IS VERIFIED TOO. drive-red-ledger-invariants.sh is declared
# NOT to be a guard but the red drive FOR ledgerguard. Make it stop naming ledgerguard and the
# declaration no longer describes anything: either it stopped being that drive, or the row was
# wrong. Both are refusals. The replacement token is NOT a .softhouse-rooted path, so no dead
# path literal is created.
m_t323b_break_subject_decl() {
  ( cd "$SCRATCH" && LC_ALL=C sed -i '' 's/ledgerguard/lgrguard_renamed_by_t323/g' \
      .softhouse/guards/drive-red-ledger-invariants.sh ) || return 1
  ! LC_ALL=C grep -q 'ledgerguard' "$SCRATCH/.softhouse/guards/drive-red-ledger-invariants.sh" || return 1
}

echo "============================================================================================"
echo "T323 RED DRIVE -- every arm runs the WHOLE BAR, never a guard standalone."
echo "scratch clone: $SCRATCH"
echo "============================================================================================"

arm "00-GREEN-CONTROL-clean-tree"          0 PRESENT 'VERDICT: PASS \(exit 0\)'                                      m_none
arm "T299-01-undocumented-collision"       2 ABSENT  'guard_capture_namespace FAILED'                                m_t299_collision
arm "T299-02-same-collision-DOCUMENTED"    0 PRESENT 'VERDICT: PASS \(exit 0\)'                                      m_t299_documented
arm "T299-03-decalibrated-corpus"          2 ABSENT  'CALIBRATION FAILED'                                            m_t299_decalibrate
arm "T299-04-no-root-line-readback"        2 ABSENT  'cannot tell which tree it inspected'                           m_t299_no_root_line
arm "T316-05-frontier-grew-unrecorded"     2 ABSENT  'THE FRONTIER MOVED IN A WAY NOBODY RECORDED'                   m_t316_new_dead_path
arm "T316-06-census-removed-SELFREF"       2 ABSENT  'guard_dead_path_frontier REFUSED'                              m_t316_no_census
arm "T316-07-pin-removed-SELFREF"          2 ABSENT  'guard_dead_path_frontier REFUSED'                              m_t316_no_pin
arm "T316-08-stale-reconcile-list"         2 ABSENT  'RECONCILIATION LIST HAS GONE STALE'                            m_t316_stale_list
arm "T319-09-shipped-tool-demotes"         2 ABSENT  'guard_reconciler_ownership FAILED'                             m_t319_break_tool
arm "T319-10-matrix-blind-to-redispatch"   2 ABSENT  'guard_reconciler_ownership FAILED'                             m_t319_blind_matrix
# The marker here is 'predicate is UNGRADED' and NOT 'ownership predicate is UNGRADED', which is
# how this arm read on its first run. It FAILED -- on the marker only, with exit=2 and
# probe=ABSENT both correct -- because the guard emits that sentence as two `warn` calls and the
# phrase straddles the line break. The arm was wrong, not the guard. Recorded rather than quietly
# corrected: a marker regex is an assertion about the transcript's SHAPE, and this one had never
# been run before it was believed.
arm "T319-11-rig-removed"                  2 ABSENT  'predicate is UNGRADED'                                         m_t319_no_rig

arm "T323-12-new-checker-invoked-by-nothing" 2 ABSENT  'IS INVOKED BY NOTHING'                                        m_t323b_plant_unwired_checker
arm "T323-13-caller-declaration-now-false" 2 ABSENT  'is DECLARED as being run by'                                   m_t323b_break_caller_decl
arm "T323-14-subject-declaration-now-false" 2 ABSENT  'is DECLARED as the red drive for'                              m_t323b_break_subject_decl

reset_tree
echo "============================================================================================"
echo "T323 RED DRIVE: $PASSES passed, $FAILS failed."
echo "============================================================================================"
[ "$FAILS" -eq 0 ]
