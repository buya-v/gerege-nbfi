#!/usr/bin/env bash
# T367 -- an INDEPENDENT casualty sweep, with selectors T363's casualty-sweep.sh does NOT carry.
# T363 named `[UNVERIFIED] that the 11 selectors are exhaustive`. This is the twelfth onward.
#
# Unlike casualty-sweep.sh, this one READS git grep's EXIT STATUS and refuses to print a zero
# it did not measure (rc 0 = hits, 1 = no hits, >=2 = the selector never ran).
#
# READ-ONLY. It is a grep.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2
ARCHIVE='(/out/|/evidence/|/transcripts/|/logs/|/red-drive/|/baseline/|\.softhouse/runs/|\.softhouse/logs/|\.softhouse/handoff/|\.softhouse/reviews/|\.softhouse/observations/)'

sel() {
  local label="$1"; shift
  local all rc
  all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?
  if [ "$rc" -ge 2 ]; then
    printf '\n=== %s\n    *** SELECTOR DID NOT RUN (git grep rc=%s). This is NOT "zero hits".\n%s\n' "$label" "$rc" "$all"
    return
  fi
  local live; live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE")
  printf '\n=== %s\n    total=%s   LIVE=%s\n' "$label" \
    "$(printf '%s' "$all" | grep -c .)" "$(printf '%s' "$live" | grep -c .)"
  printf '%s' "$live" | grep . | cut -c1-190 | sed 's/^/      /'
}

echo "T367 INDEPENDENT SWEEP -- selectors NOT in casualty-sweep.sh"
echo "repo: $(git rev-parse --short HEAD)  date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

sel "X1  the PROCESSED/ERROR split of the audit table (present tense)" -n -E '[0-9]+ PROCESSED / [0-9]+ ERROR|split is \*\*[0-9]+'
sel "X2  any present-tense row count for m_portfolio_command_source" -n -E 'm_portfolio_command_source (is|=|carries|holds) ?\*{0,2}[0-9]'
sel "X3  'the whole gerege audit table' style scope claims"          -n -E 'whole `?gerege`? audit table|across the whole .{0,20}audit'
sel "X4  distinct transaction_id spelled as a live cardinal"          -n -E 'distinct_transaction_id = [0-9]+|distinct transaction_id.{0,12}(is|=) ?\*{0,2}[0-9]+'
sel "X5  '26 transactions' / '31 transactions' style"                 -n -E '\b(26|31) (distinct )?transactions?\b'
sel "X6  claims that the ledger has 60 or 71 rows, present tense"     -n -E 'ledger (has|holds|carries) \*{0,2}(60|64|71|75)'
sel "X7  MNT-only assertions not already named by T363"               -n -E 'only currency|single currency|currency is MNT|all MNT'
sel "X8  a max-id pin other than 64/352 (a floor someone else typed)" -n -E 'max id (is|=) ?\*{0,2}[0-9]+'
sel "X9  is oracle-state-baseline.sh referenced by anything that RUNS?" -n -F 'oracle-state-baseline.sh'
sel "X10 is PROBES.tsv referenced by anything that RUNS?"             -n -F 'PROBES.tsv'
sel "X11 a deliberately MALFORMED selector, to prove this sweep refuses" -n -E 'gl (16|17'

echo
echo "END. X11 must report 'SELECTOR DID NOT RUN'. If it reports 0 hits, this sweep is as"
echo "fail-open as the one it is auditing."
