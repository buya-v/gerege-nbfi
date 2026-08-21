# T159 — independent review of T117 (gate G-8). VERDICT: **APPROVED**.

**This file is a pointer, deliberately.** The review in full — every re-derivation, the 102-check
P-46 quotation audit, the live-oracle re-observation, the four P-22 guard red drives and the
25-site `gates.md` sweep — is at:

> **`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T159.md`**

It is not duplicated here, because two copies of a 500-line evidence document drift, and this
program has already been bitten by a claim surviving in the restatement after it was corrected at
the site (P-21 / P-26).

Evidence directory: **`.softhouse/capture/t159-review-t117/`**.
Branch: `softhouse/T159-review-t117` — `4890ca0` (PREDICTION) → `9d6a8fd` (OBSERVED) → `1b2fc47`
(HANDOFF); the prediction commit is a **strict ancestor** of the observation commit (P-9).

## The four lines a reader needs

1. **APPROVED.** Every number T159 re-derived independently from T117's RAW captures came back
   equal to T117's. 102 mechanical claim-vs-observed checks: **100 exact, 0 fabrications, 2 scope
   imprecisions** that change no headline. All five committed digests reproduce.
2. **THE HEADLINE NUMBER IS ALREADY STALE, AND T117 SAID IT WOULD BE.** T117 reported a largest
   unamortized residual of MNT 5.01 and warned it was "the largest *observed*, not a bound", since
   nothing above n = 1000 had ever been asked. T159 asked. The residual **doubled**:
   **MNT 10.01** at `T159-R600p0-N3000-B1001` — 3000 rows of `principal "0.00"`, balance frozen for
   250 years, MNT 15,010.01 of scheduled interest. **3000 is simply the largest term T159 asked.**
   Any G-8 sentence stating a magnitude must state the term it was measured at.
3. **The reference oracle also THROWS.** Two cells died with `java.lang.StackOverflowError` inside
   `ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI`, which recurses into itself
   (`ProgressiveEMICalculator.java:1214`). It is not monotone in `n` or in `B`. `gates.md` has no
   sentence for a third outcome in which the oracle produces no schedule at all — and option (b)
   needs one.
4. **T117 reproduces.** 17 of 17 re-asked cells came back **byte-identical** under tenant ids
   disjoint from T117's, including the MNT 5.01 headline cell and all three PARTIAL B = 11 cells.
   The band structure at B = 1 is real cell-for-cell, with no boundary off by one.

## What T159 did NOT do

It **did not edit `.softhouse/gates.md`** — that section's STANDING RULE requires a full
sentence-by-sentence scope rebuild and parallel workers were live. §9 of the handoff produces the
site list (25 sites, six of them not on T117's list of nine); **the driver rebuilds it.**

It **decided nothing about G-8**. Options (b) and (c) amend the graded domain and are hard `user`
gates. No vector, `PIN.json`, `capabilities.json`, `contract.go`, DEC-n, `tasks.json` or Go file was
touched; `gofmt -w` was never run.

*"The oracle" throughout is the Fineract reference implementation. Oracle Database is a prohibited
product in this program; this work opened no database connection and started no server.*
