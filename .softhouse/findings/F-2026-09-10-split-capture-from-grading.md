# F-2026-09-10 — an oracle-WRITING task that must also GRADE does not fit one run

**Status:** DECIDED. Acted on immediately (`OH-WCCAP-P`).
**Evidence:** every run this session, sorted by whether it had to do both.

## The measurement

| run | wrote to the oracle? | also had to grade? | outcome |
|---|---|---|---|
| `OH-GL-R` | yes | yes | cap-death, 71 files uncommitted, salvage later **reverted** |
| `OH-INV-Y` | yes | yes | terminal died; salvaged by hand |
| `OH-WCDISC-O` | yes | yes | **killed at 251 iterations, nothing created, nothing written** |
| `OH-SHARES-K` | yes | capture-first, graded after | landed (killed late, lost nothing) |
| `OH-COLL-L` | yes | capture-first, graded after | landed clean |
| `OH-ALLOC-G` | yes | capture-first, graded after | landed clean |
| `OH-JE-C`, `OH-DIR-D`, `OH-MAP-E`, `OH-AMORT-F`, `OH-ACCRUAL-M`, `OH-PROV-N` | no | yes | all landed clean |

**Pure grading runs land. Capture-then-grade runs land when the capture commits FIRST.
Runs that must design the oracle write AND the grading in one budget do not.**

`OH-WCDISC-O` is the clearest case because it had every advantage: a complete map from
`OH-WC-S` (the exact write path `file:line` and the exact capture needed), one property,
a non-round-value instruction, and a 120-iteration checkpoint. It still spent 251
iterations orienting — existing captures, then step scripts, then a conformance baseline,
then Fineract Java source — and created nothing.

## Why the shape is hard, not the task

An oracle write is a **design** problem before it is an execution one: which endpoint, what
body, what values keep the arithmetic clean under G-19, what order of approve/activate/
disburse, what to snapshot first. A grading task is a **transcription** problem against an
observation that already exists. Asking one budget to do both means the run cannot start
writing anything until it has solved the harder half, so the checkpoint passes with an
empty tree and there is nothing to salvage when it ends.

## The rule

**Split them.** Dispatch capture-only, then grade the committed capture in a separate run.

* The capture run's whole deliverable is `(request, response)` pairs plus an `OWNER.md`,
  committed. **No vector, no drive, no refusal relaxation.** Its checkpoint is "the object
  exists in the oracle and the capture is committed", which it can reach early.
* The grading run then has what every clean run this session had: an observation already on
  disk, and one property to pin.

This also makes a kill cheap at every point, which is the property that made `OH-SHARES-K`
survive being killed with two commits already in.

## The counter-case, so this is not over-applied

`OH-ALLOC-G` did both in one run and landed. It could, because its oracle write was a
**single repayment on an existing loan** — no product to design, no configuration, the
amount decided by arithmetic the brief had already worked out. **Split when the write
requires designing a new object; a one-call write against existing objects is fine.**
