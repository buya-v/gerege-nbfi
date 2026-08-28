# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 4 — **NINE WORKERS IN FLIGHT.** Updated live, not at exit.

If you are reading this after a kill, the table below is what was running. Each worker was told to commit
incrementally. Verify every row with `git log --oneline main..<branch>`; **a branch with no commit means that
worker died before its first checkpoint and the task is `needs_retry`, not `in_progress`.** `in_progress`
never means "work is happening"; it means "a driver said so, once".

## BAR ON `main` — GREEN, but it was RED for three commits this iteration and the driver caused it

```
bash .softhouse/conformance.sh   →  VERDICT: PASS (exit 0)
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value
46 parity vectors / 7884 cells · all 14 wrong ledger implementations KILLED · pin 14 == population 14
dead-path frontier GREEN, deadOccurrences 108 · P-number citations VERDICT PASS, 0 fatal
```

### ⚠ THE DRIVER REDDENED `main` AND PUSHED IT — READ THIS BEFORE YOU WRITE ANY DIRECTIVE FILE
Dispatching T398, the driver wrote a bare `P-<n>` token into **this file** naming a pattern that did not
exist yet. `.softhouse/RESUME.md` is a **DIRECTIVE file** to `check-pnumber-citations.py`, so that is a
**FATAL UNDEFINED citation**, and `guard_pnumber_citations` is a **HARD guard**:

```
PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/RESUME.md:42 <the token>
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

`main` was red from `4cf77a42` to `c0b15151` — **three pushed commits** — and nothing detected it. It surfaced
only because an unrelated merge result was being graded. Two lessons, neither of which is "the guard worked":
- **T392 had reported this exact near-miss in its own handoff** and the driver reproduced it within minutes.
- **The driver never runs the bar on its own commits**, and it is the only identity that pushes to `main`.
  Filed as **`T413`**'s sibling **`T412`**.
- **Exit 2 with NO probe line printed is a HARD-guard failure, never an oracle outage.** The oracle has been
  reachable for this entire fire.

## MERGED THIS ITERATION — each verified on the MERGE RESULT before `main` was touched

| Merge | What it was |
|---|---|
| `T392` | **`P-98`** — a control that cannot fail and a control that refuses everything are the same defect wearing opposite signs. Driver verified the P-number free independently before merge. |
| `T396` | T389's three citation defects — and **three REAL port traps**, all re-verified by the driver against `/Users/buv/fineract @ 426a23544`, not accepted on the worker's word. |

**The three port traps are the most portable thing this iteration produced**, and they are what `G-20` asked
for — actual porting knowledge rather than more instrument:
- **A** — `isBeforePeriod` switches on `isFirstPeriod`: strict `isBefore` for the first period, `!isAfter`
  for every other. At `tillDate == fromDate` the first installment is kept and all others dropped. A
  single-comparison Go port diverges **silently** — the loan is still selected, so it is a no-op, not an error.
- **B** — the `!chargeOnDueDate ||` short-circuit removes both date cutoffs from one config row.
- **C** — the progressive `plusDays(1)` shift reaches installment selection and interest but **not**
  `addChargeAccrual`, which still gets raw `tillDate`. Two distinct Go failures.

## IN FLIGHT

| Task | Branch | What it is |
|---|---|---|
| `T391` | `softhouse/T391-accrual-promotion` | **Promote T388's accrual observations into vectors.** Oracle-only work. The pin it may need moved to `conformance.sh:4551` (+75) under T404 — **match it BY NAME.** |
| `T390` | `softhouse/T390-baseline-attribution` | Oracle-state baseline attribution; ships a wiring patch as a request. |
| `T402` | `softhouse/T402-t386-conditions` | **Blocks `T399`.** A `2>` redirect that returns 1 without running the command. |
| `T404` | `softhouse/T404-t384-conditions` | The fifth registration fail-open. **Has ended two turns mid-drive**; fix is committed, GREEN-AFTER and R1/R2/R3 are not. |
| `T400` | `softhouse/T400-t385-conditions` | `fire-program.sh` offsets that "cannot drift apart" and do. |
| `T393` | `softhouse/T393-t382-conditions` | T382's four conditions on T374. |
| `T398` | `softhouse/T398-measured-but-backwards` | A measured remedy that is measured and still backwards. Must take the next free cardinal above `P-98`. |
| `T405` | `softhouse/T405-review-t397` | INDEPENDENT review of T397 — a change to the **admission comparator**, which is grading. |
| `T411` | `softhouse/T411-review-t401` | INDEPENDENT review of T401. |

## COMPLETE, HELD UNMERGED PENDING REVIEW
`T397` (`softhouse/T397-t387-conditions`) — token-bounded `verbatimInCapture`, qualified verdict. Driver
re-ran its float sweep independently: 4 hits, **all inside comments stating the prohibition**.
`T401` (`softhouse/T401-zsh-census-gap`) — purely additive; applied nothing, by design.

## ⚠ A SYSTEMIC PLAN-GATE MISS, FOUND AND CLOSED THIS ITERATION
Plan gate 1 requires every coder task to carry a paired INDEPENDENT reviewer. **Seven of ten in this wave had
none** (`T390 T391 T397 T400 T401 T402 T404`); only `T393` was paired. Cause: all were planned as
review-CONDITION follow-ups, and the pairing was applied to the original task but **never re-applied to the
follow-up** — so a chain that began with a review was drifting back into unreviewed money-path changes.
Filed `T405`–`T411`, one per code task.

## QUEUE FOR THE NEXT FIRE
`T406`–`T410` (reviewers, as their subjects land) → `T399` (needs `T402`) → `T413` (apply T401's four census
extensions; needs `T404`) → `T412` (the driver never grades its own commits) → `T394` (reviews `T393`) →
`T395` (G-21, DEC-2 **evidential correction only**).

## OPEN GATES — none blocks anything, and no CONTRACT gate is open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`. `G-20` and `G-21` were stored as **bare strings**
in `program.json`, which **crashed `ready-tasks.py`** after it had printed READY and BLOCKED — so every driver
running it got a full, plausible task list and **no gate section at all**. Normalised into gate objects; the
resolver now surfaces non-dict entries as `MALFORMED` and reads them as **OPEN**, never closed.
