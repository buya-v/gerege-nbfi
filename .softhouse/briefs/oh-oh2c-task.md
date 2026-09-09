# OH-2c — make DEC-2 §4.4.2 OPERATIVE: publication decidable while the bar stays red

Repo: /Users/buv/oh-gerege-oh2c   Branch: fix/OH2c-publication-gate (already checked out)
Work ONLY in this worktree. Do not touch /Users/buv/gerege-nbfi or any other worktree.

## Read these first, in this order

1. `docs/adr/DEC-2-gl-accounting-adapter.md` §4.4.2 — ratified last commit (f2f744d2).
2. `.softhouse/guards/ledger-invariants.baseline` — the 9 remaining rows and the REPAIRED block.
3. `.softhouse/guards/drive-red-ledger-invariants.sh` — already implements the both-directions rule.
4. `.softhouse/hooks/bar-attest.sh` lines 21-27 — the FOUR attestation conditions.
5. `.softhouse/conformance.sh` line ~6027 `timed_guard guard_ledger_invariants || failed=1`.

## The problem, precisely

§4.4.2 ratifies: publication is permitted while the guard's finding set is EXACTLY the baseline,
refused on deviation in EITHER direction. `drive-red-ledger-invariants.sh` already decides that
correctly — it exits 0 today.

But NOTHING CONSULTS IT. `driver-push-gate.sh` records an attestation only via `bar-attest.sh`,
and `bar-attest.sh` requires all four of:
  1. the probe line PRINTED at least once   2. every probe line reads `up`
  3. a `VERDICT: PASS` line present          4. the bar's exit status is 0

Condition 1 is the real blocker, and it is subtler than "exit != 0". `guard_ledger_invariants` is
a HARD guard; when it fails, `run_guards` returns BEFORE the oracle probe prints and BEFORE any
vector is graded. So today there is genuinely NO VERDICT — not a failing one. Simply teaching the
gate to tolerate exit 2 would attest a tree on which NO VECTOR WAS EVER GRADED. That is worse than
the current refusal. Do not do it.

## What to build

Make the bar RUN TO COMPLETION when the ledger finding set matches the baseline, while STILL
ENDING RED — then teach the attestation path to accept that one specific, fully-graded shape.

  (a) In `run_guards`: when `guard_ledger_invariants` fails, consult the same both-directions
      comparison `drive-red-ledger-invariants.sh` uses. If the set matches the baseline EXACTLY,
      record the failure but DO NOT return early — let the run continue to the probe and to vector
      grading. The bar must still end EXIT 2 and must print an unmissable line naming the state,
      e.g. `conformance: RED BY RECORDED DECISION (DEC-2 §4.4.2) — findings == baseline`.
      If the set DEVIATES in either direction, behave exactly as today: return immediately, EXIT 2,
      no verdict. That path must not change.

  (b) In `bar-attest.sh`: accept a tree when conditions 1-3 hold AND the only reason condition 4
      fails is the recorded-decision state from (a) — verified by RE-RUNNING the both-directions
      comparison itself, never by grepping for the banner text from (a). A banner is not evidence.
      Any other failing guard, an absent probe, a probe reading `down`, or a missing/failing
      VERDICT line must still refuse. Record in the attestation ledger that the tree was attested
      under §4.4.2, so a reader can tell it from a green one.

## Hard constraints — violating any of these fails the task

* You may NOT edit `.softhouse/guards/ledger-invariants.baseline`. Obligation 3 of §4.4.2: the
  baseline is not editable by the agent whose work changed the finding set.
* You may NOT edit `.softhouse/guards/ledgerguard/` or `check-ledger-invariants.sh`. The guard's
  exit code is untouched by §4.4.2 — it must still exit 1 standalone. Verify it still does.
* You may NOT weaken, skip, reorder or shorten ANY other guard. If your change makes a second
  guard stop running or stop mattering, you have broken the bar.
* You may NOT make `guard_ledger_invariants` pass, print fewer findings, or report a lower count.
  All 34 findings across 9 pairs must still be printed on every run.
* Do not touch `nexus/` at all. No Go source changes. This is a harness/gate task only.

## Prove it — these tests are the deliverable, not the diff

Write them as a runnable script and paste its output in your final message.

  T1 baseline matches      -> bar EXIT 2, probe line PRESENT, VERDICT line present,
                              bar-attest.sh ATTESTS, ledger row marks it §4.4.2.
  T2 a finding APPEARS     -> temporarily plant a balance write in a nexus file that has no
                              baseline row; bar returns early, NO probe line, bar-attest REFUSES.
                              Revert the plant.
  T3 a finding is SILENCED -> temporarily append an unfindable row to a COPY of the baseline and
                              point the comparison at the copy; bar-attest REFUSES.
                              (Do not modify the real baseline file.)
  T4 a DIFFERENT guard fails -> temporarily break one unrelated cheap guard; bar-attest REFUSES
                              even though the ledger set matches. Revert.
  T5 guard still refuses   -> `bash .softhouse/guards/check-ledger-invariants.sh` EXIT 1.
  T6 finding count         -> ledgerguard still reports 34 findings across 9 pairs.

T4 is the one that matters most. If T4 attests, your change is a hole, not a gate.

## Report

State what you changed and why, paste the T1-T6 output, and name anything you could NOT verify.
If you conclude this design is unsound, STOP and say so with your reasoning instead of building a
weaker version. A refusal with an argument is a good outcome here; a gate with a hole is not.
