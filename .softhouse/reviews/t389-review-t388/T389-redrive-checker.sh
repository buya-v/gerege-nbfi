#!/usr/bin/env bash
# T389 -- RE-DRIVE of T388's disjointness checker (11-derive-forbidden-set.py).
#
# P-45: a checker nobody has watched FAIL enforces nothing. T388 states it red-drove
# its own checker with `--check 16,41` -> exit 1. This RE-DRIVES it independently, with
# T388's own mutation AND four mutations T388 did NOT use, plus a control and an
# anti-calibration.
#
# The checker is trusted here only if ALL of:
#   * the CONTROL (the real, disjoint set 35-47) exits 0 -- it does not fail on
#     unmutated input, i.e. it is not a stuck-red checker;
#   * EVERY mutation that genuinely intersects the forbidden set exits 1 -- it can
#     actually fail, i.e. it is not a stuck-green checker (the P-45 defect);
#   * the anti-calibration (an id in no set at all) exits 0 -- it is not flagging
#     everything indiscriminately.
#
# The checker is run from a scratch extraction of T388's committed tree at
# /tmp/t389scratch, whose .softhouse/vectors is a SYMLINK to the real promoted store
# in this worktree, so the forbidden set it derives is derived from the real corpus
# and not from a copy T389 could have doctored.
set -u
S=/tmp/t389scratch/.softhouse/capture/t388-accrual-capture/11-derive-forbidden-set.py
pass=0
fail=0

run() {
  label="$1"; accts="$2"; want="$3"
  out=$(python3 "$S" --check "$accts" 2>&1); rc=$?
  echo "--------------------------------------------------------------------"
  echo "CASE   : $label"
  echo "--check: $accts"
  echo "expect : exit $want"
  echo "$out" | tail -6
  echo "ACTUAL : exit $rc"
  if [ "$rc" = "$want" ]; then
    echo "RESULT : OK"
    pass=$((pass + 1))
  else
    echo "RESULT : *** UNEXPECTED ***"
    fail=$((fail + 1))
  fi
}

echo "T389 RE-DRIVE OF T388's DISJOINTNESS CHECKER"
echo "checker : $S"
echo "vectors : $(readlink /tmp/t389scratch/.softhouse/vectors)"
echo

# CONTROL -- the real set T388 created. Must PASS (exit 0).
run "CONTROL: real T388 accounts 35-47 (unmutated input)" 35,36,37,38,39,40,41,42,43,44,45,46,47 0

# T388's own stated red drive, RE-RUN by T389 rather than read.
run "MUTATION A: T388's own red drive, gl 16 injected" 16,41 1

# Mutations T388 did NOT use. Each targets a forbidden member reachable only through a
# key a naive scan would miss -- so each independently proves the DERIVATION, not just
# the comparison, is doing work.
run "MUTATION B: gl 22, found only via capabilities-ledger unposted_slots" 22,35 1
run "MUTATION C: gl 15, reached only via contra_gl_account_id" 15,36 1
run "MUTATION D: gl 18, LDG-REFUSE-02 rerun_invariant account" 18,43 1
run "MUTATION E: the whole real set PLUS one forbidden member" 35,36,37,38,39,40,41,42,43,44,45,46,47,17 1

# ANTI-CALIBRATION: an id in NEITHER set must not be flagged, or the checker is just
# returning 1 unconditionally.
run "ANTI-CALIB: gl 999, in no set at all -- must PASS" 999 0

echo "===================================================================="
echo "CASES OK: $pass   UNEXPECTED: $fail"
if [ "$fail" -ne 0 ]; then
  echo "VERDICT: the checker did NOT behave as a working checker must."
  exit 1
fi
echo "VERDICT: checker DRIVEN RED on 5 distinct intersecting inputs and GREEN on 2"
echo "         disjoint inputs. It can fail, and it does not fail indiscriminately."
exit 0
