# OWNER — `gl-accounting-surface`

**Subject:** the loan→GL journal-entry posting surface, opened by creating the first
loan product in this oracle with accounting enabled.

**Produced by:** run `OH-GL-R` (brief `.softhouse/briefs/OH-INV-Q.md`'s successor,
`.softhouse/briefs/OH-GL-R.md`; log `.softhouse/briefs/logs/ohglr.log`; conversation
`7dc6296f3a6c47d1915b75c2e7df6569`).

**Directory named for the SUBJECT, not the run.** The run wrote these under `ohglr/`, a
bare task id. Per `.softhouse/guards/check-capture-namespace.sh` — "a capture or review
directory is named for its SUBJECT; the task-id prefix is a CONVENIENCE, never the
directory's identity" — it was renamed to its subject **before first commit**, while
renaming was still permitted. Directory names are frozen at first commit; this one is now
frozen. `bin/common.sh` was updated in the same move, the only file that referenced the old
path.

**Committed by the driver on the run's behalf.** `OH-GL-R` reached the 500-iteration limit
with these 71 files on disk and **zero commits**. Its final recorded reasoning was
*"7527 captured files ARE tracked. So the convention is to commit captures … I should
commit them (they're the evidence)."* — it was one step from committing and ran out. The
files are its work, not the driver's; the driver verified and committed them.

## What the oracle now contains, and it is ADDITIVE

* loan product **id 3 `OHLGR-Accrual-Loan`, `ACCRUAL PERIODIC`** — the first
  accounting-enabled product here. Products **1 and 2 are untouched and remain
  `accountingRule: NONE`**, so no committed capture's provenance moved.
* 11 new GL accounts (`OHLGR-*`), 2 clients, 2 loans (**10**, **11**).
* Charges: a flat fee **100**, a specified-due-date fee **100**, a penalty **57**.

## Why this directory matters

1. **The loan→GL posting surface exists here for the first time.** Journal entries 17-22,
   balanced double-entry, verified by the driver before commit:
   loan 10 debits 100100.0 == credits 100100.0; loan 11 debits 100000.0 == credits 100000.0.
2. **It closes `F-2026-09-09-fee-penalty-blind.md`.** Loan **11** carries all four summary
   terms non-zero with **fee ≠ penalty**, which the finding named as the requirement
   (equal values would let a term-swap defect survive):
   `100000.0 + 6618.53 + 100.0 + 57.0 = 106775.53`
   (minor units `10000000 + 661853 + 10000 + 5700 = 10677553` — no residue).
   Loan **10** is the useful contrast: fee outstanding **0**, penalty **57**, which
   discriminates the penalty term on its own.

**No vector has been promoted from these captures yet.** Committing an observation and
grading it are different acts; the promotion, with drives that must kill, is separate work.
