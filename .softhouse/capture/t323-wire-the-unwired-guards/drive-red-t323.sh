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
m_t299_collision() {
  mkdir -p "$SCRATCH/.softhouse/capture/t319-a-second-rig" || return 1
  echo "planted by T323's red drive" > "$SCRATCH/.softhouse/capture/t319-a-second-rig/NOTE.md" || return 1
  ( cd "$SCRATCH" && git add -A .softhouse/capture/t319-a-second-rig ) || return 1
}
# The SAME collision, DOCUMENTED. This is the discrimination arm: if it also went red the guard
# would be measuring "two directories" rather than "two directories and nobody said who owns
# them", and the rule would be "never collide" -- which T299 explicitly rejected because
# renaming a committed evidence directory breaks every transcript citing it by path.
m_t299_documented() {
  mkdir -p "$SCRATCH/.softhouse/capture/t319-a-second-rig" || return 1
  echo "planted by T323's red drive" > "$SCRATCH/.softhouse/capture/t319-a-second-rig/NOTE.md" || return 1
  echo "Owner: T323. This directory is NOT T319's work." \
    > "$SCRATCH/.softhouse/capture/t319-a-second-rig/OWNER-IS-T323-NOT-T319.md" || return 1
  ( cd "$SCRATCH" && git add -A .softhouse/capture/t319-a-second-rig ) || return 1
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
  mkdir -p "$SCRATCH/.softhouse/capture/t323-wire-the-unwired-guards" || return 1
  printf '#!/bin/sh\ncat ".softhouse/capture/t323-a-path-that-does-not-exist/x.json"\n' \
    > "$SCRATCH/.softhouse/capture/t323-wire-the-unwired-guards/PLANTED-dead-path.sh" || return 1
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
# THE ANTI-AMNESTY ARM, and it is the wiring's own. Fold T305's four rows into the pin -- which
# makes T316's guard GREEN -- while leaving DEADPATH_T323_RECONCILE_LIST populated. The list is
# now excusing rows that are no longer there. A pin is a frontier, not an amnesty, so a stale
# reconciliation list must FAIL the bar rather than sit there quietly forever.
m_t316_stale_list() {
  {
    echo '.softhouse/capture/t305-openingbalance-accepting-side/red-drive-conformance-guard.sh | .softhouse/capture/t999-rig/attest'
    echo '.softhouse/capture/t305-openingbalance-accepting-side/red-drive-conformance-guard.sh | .softhouse/capture/t999-rig/attest/gerege.disposable'
    echo '.softhouse/capture/t305-openingbalance-accepting-side/red-drive-conformance-guard.sh | .softhouse/vectors/ledger/ACCEPT.json'
    echo '.softhouse/capture/t305-openingbalance-accepting-side/red-drive-conformance-guard.sh | .softhouse/vectors/ledger/REFUSE.json'
  } >> "$SCRATCH/.softhouse/guards/dead-path-frontier.pin" || return 1
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
arm "T319-11-rig-removed"                  2 ABSENT  'ownership predicate is UNGRADED'                               m_t319_no_rig

reset_tree
echo "============================================================================================"
echo "T323 RED DRIVE: $PASSES passed, $FAILS failed."
echo "============================================================================================"
[ "$FAILS" -eq 0 ]
