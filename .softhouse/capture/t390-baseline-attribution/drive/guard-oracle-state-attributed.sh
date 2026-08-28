# ---------------------------------------------------------------------------
# guard_oracle_state_attributed: EVERY ROW ABOVE THE FLOOR IN THE SHARED REFERENCE ORACLE
# NAMES THE THING THAT CREATED IT.  [T390 — wiring the instrument T363 built and nothing ran.]
# ---------------------------------------------------------------------------
# WHY IT IS HERE AT ALL. The instrument
#   .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh
# has existed since T363 and was invoked by NOTHING THAT RUNS. Measured by T390 on 2026-08-28,
# and this is a statement about the search: `grep -c oracle-state-baseline` over THIS file = 0;
# `grep -rn` over `.softhouse/bin/` = 0 hits; the repository has no `.github/` and its only
# non-sample git hook is `reference-transaction`; every other reference in the tree is prose
# (handoffs, reviews, `reference-oracle.md`, `program.json`) or A REVIEW'S OWN DRIVE SCRIPT
# (`t367-review-t363/drive.sh`, `drive-independent-sweep.sh`) — and T367 asked the question
# explicitly, as its check X9, and shipped anyway. That is P-45, "a test-only guard is not a
# guard", and it was not hypothetical: T388 moved the shared oracle by twenty-four rows and the
# instrument built to notice did not run. It is also invisible to guard_guards_dir_registration,
# whose population is `.softhouse/guards/**` — this instrument lives under `.softhouse/capture/`.
#
# EXIT-CODE MAPPING, AND THE ONE CARVE-OUT. The instrument declares 0 attributed / 1
# UNATTRIBUTED / 2 database unreachable / 3 wrong interpreter.
#   0 -> pass.
#   1 -> REFUSAL. Somebody wrote to the standing Fineract instance and did not record it.
#   2 -> SKIPPED, return 0, with a loud unconditional line. An unreachable database is NOT a
#        verdict about the ledger — the identical rule conformance.sh applies to its own exit 2
#        — and CLAUDE.md's program driver keeps analysis and spec work running while the oracle
#        is down. A guard that turned `docker stop` into a hard bar failure would make this
#        harness unrunnable offline, and `--self-test` is on this same run_guards path.
#   3 -> REFUSAL. It cannot arise from here, because this invokes `bash` explicitly; that is
#        precisely why it must refuse if it ever does — it would mean the call below had stopped
#        being what this comment says it is.
#   any other code, or the instrument missing/unreadable -> REFUSAL. "Did not run" must never
#        read as "clean". [T383's lesson, inverted: a guard that cannot fail and a guard that
#        refuses everything are the same defect wearing opposite signs.]
#
# THE RESIDUAL FAIL-OPEN, DECLARED RATHER THAN HIDDEN. The exit-2 carve-out means a host with no
# docker skips this guard on every run — P-45 again, one level up. It is MITIGATED, not closed:
# the `ORACLE_STATE_BASELINE = SKIPPED` line below is unconditional and machine-greppable, so a
# run that never exercised this guard says so in its own transcript, and a census that counts
# skips can be added on top of it without touching this function.
#
# WHAT THIS DOES NOT COVER is written down in the instrument's own header as exception classes
# (a) consumed sequence, (b) direct SQL, (c) update below the floor, (d) the scheduler. Read it
# there; do not restate the list here, because a restated list rots (P-80).
guard_oracle_state_attributed() {
  local inst="$REPO_ROOT/.softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh"
  local out rc
  if [ ! -f "$inst" ]; then
    warn "conformance: guard_oracle_state_attributed: THE INSTRUMENT IS MISSING at"
    warn "conformance:   .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh"
    warn "conformance: With it absent, nothing grades attribution of writes to the SHARED reference"
    warn "conformance: oracle. That is a REFUSAL and never a pass."
    return 1
  fi
  # `bash`, never `sh`: the instrument exits 3 under a POSIX-mode shell, and a guard that invoked
  # it wrongly would convert its own mistake into a bar failure.
  out="$(bash "$inst" 2>&1)"; rc=$?
  case "$rc" in
    0)
      say "conformance: oracle-state baseline: ALL MOVEMENT ATTRIBUTED (instrument exit 0)."
      printf '%s\n' "$out" | LC_ALL=C grep -aE '^(FLOOR|  ok )' | sed 's/^/conformance:   /'
      return 0
      ;;
    1)
      warn "conformance: UNATTRIBUTED MOVEMENT IN THE SHARED REFERENCE ORACLE."
      warn "conformance: Somebody wrote to the standing Fineract instance and did not record it in"
      warn "conformance:   .softhouse/capture/t363-oracle-baseline/PROBES.tsv"
      printf '%s\n' "$out" | sed 's/^/conformance:   /' >&2
      warn "conformance: Do NOT repair this by widening the floor. Find what did it — a task, or a"
      warn "conformance: SCHEDULED JOB (exception class (d) in the instrument's header) — and add"
      warn "conformance: its rows to PROBES.tsv."
      return 1
      ;;
    2)
      say "conformance: ORACLE_STATE_BASELINE = SKIPPED (the oracle's database is UNREACHABLE)."
      say "conformance:   This is NOT a verdict about the ledger, and NOT a pass for attribution."
      say "conformance:   Attribution of writes to the shared oracle was NOT checked on this run."
      return 0
      ;;
    3)
      warn "conformance: guard_oracle_state_attributed: the instrument refused the INTERPRETER"
      warn "conformance: (its exit 3). This guard invokes it with \`bash\` explicitly, so this"
      warn "conformance: cannot happen unless the call site changed. REFUSED — it did not run."
      printf '%s\n' "$out" | sed 's/^/conformance:   /' >&2
      return 1
      ;;
    *)
      warn "conformance: guard_oracle_state_attributed: the instrument exited $rc, which is not"
      warn "conformance: one of its four declared codes. It did not answer the question, and"
      warn "conformance: 'did not run' is not 'clean'. REFUSED."
      printf '%s\n' "$out" | sed 's/^/conformance:   /' >&2
      return 1
      ;;
  esac
}
