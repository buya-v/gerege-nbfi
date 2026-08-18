# Handoff — T21, independent audit of capture pass 3

**Branch:** `softhouse/T21-capture-pass3-audit-v2`
**Deliverable:** `.softhouse/reviews/T21-capture-pass3-audit.md`
**Verdict:** ACCEPTED WITH REQUIRED CHANGES (4 × P0, 7 × P1)
**Date:** 2026-08-18. Reference oracle reachable; pinned image and commit verified.

## What I did

1. **Re-ran `Capture3.java` unmodified** in the pinned image (`sha256:e596339626bf…`, Fineract
   `426a23544e…`, clean tree, seam class SHA-256 `bf397f0b…` identical to the pinned original). Output
   **byte-identical** to the committed `capture-prod-raw.json`. Log identical modulo timestamps; stderr 0
   bytes both. The prior worker's reproduction file is byte-identical to mine too.
2. **Wrote my own re-derivation of the progressive amortization from the pinned Fineract source**
   (`.softhouse/reviews/t21v2/t21v2-rederive.py`), not reusing the earlier worker's script. It reproduces
   **all twelve captures to the minor unit** — every period column, every total, including all four MNT-scale
   schedules, the month-end re-anchored pair, and the P-03 pre-disbursement boundary.
3. **Re-checked the six property invariants myself** (`t21v2-invariants.py`), integer minor units, zero
   tolerance, plus six additional checks of my own. All twelve pass all six.
4. **Ran two new probes against the oracle** through the same Path A seam (`T21v2Probe.java`,
   `T21v2Probe2.java`): a p12-vs-p19 divergence sweep at 20 points, and differential + reflective tests of
   `installmentAmountInMultiplesOf` and `daysInYearCustomStrategy` at `(19, HALF_UP)`.
5. **Compared pass 3 against passes 1 and 2** structurally (`t21v2-crosspass.py`).
6. **Applied T18's P0 list and T19's required change 10** to `Capture3.java` and pass 3's artefacts.

## What I concluded

- **The numbers are sound.** Nothing is synthesised; the run is bit-reproducible; the arithmetic is
  independently re-derivable from source; the invariants hold integer-exact. This is the best-evidenced
  capture set the program has.
- **`P-CAL` calibration holds** against the shipped literal read directly out of
  `EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92`, and it is correctly labelled non-parity in the
  report. `P-01` is byte-identical to pass-1 `D-01-p19`.
- **Load-bearing question 1 — P-03 / `X2`: the orchestrator is right, the prior worker's inference is not.**
  `X2` is not one of the six invariants; it was the prior worker's own extra check, and its formulation
  (seed the balance at `totalDisbursedAmount`, then subtract) is invalid for a schedule whose first emitted
  row precedes the disbursement. The position-aware version holds on P-03 and on all twelve. The zeroed
  period-1 row is genuine oracle behaviour with a source mechanism
  (`ProgressiveLoanScheduleGenerator.java:116-145`), and `loanTermInDays = 182` measured from the schedule
  start is correct (`ProgressiveLoanInterestScheduleModel.java:200-207`).
- **Load-bearing question 2 — the size-threshold claim: REFUTED by the oracle.** The oracle's p12/p19 pair
  **diverges at principal 4.00** on the 36 × 16.8 % shape and is **identical at 50,000,000** on that same
  shape and at **87,654,321** on the 6 × 7.0 % shape. All four MNT captures are p12/p19-identical, so pass 3
  supplies no evidence that Mongolian loan sizes are precision-sensitive. Sensitivity is a rounding-boundary
  property of `(principal, n, rate)`, not a magnitude property.
- **Both dropped inputs are still dropped at `(19, HALF_UP)`** — confirmed by differential *and* reflectively:
  `assembleFrom` (`LoanApplicationTerms.java:579-607`) never sets `installmentAmountInMultiplesOf` (the
  `Builder` has no setter for it at all), and the `Builder` copy-constructor (`:304-351`) never copies
  `daysInYearCustomStrategy` even though `assembleFrom` sets it on the builder at `:604`.
- **The prior T21 worker's re-derivation model is wrong** on the EMI smoothing pass (never applied; trigger
  formula misreads `Money.copy(double)` as a multiply). Its threshold probe therefore reports divergences the
  oracle does not have — the oracle emits identical schedules at its headline 6 × 7.0 % / 43,811. Its
  reproduction step and its P-03 structural reading are correct and I adopt them, having re-verified both.
- **Pass 3 inherits three of T18's four P0 blockers unfixed** (no attestation block, no `fromDate`/`fee`/
  `penalty`, no committed run recipe; plus the discarded stack trace), and **T19's required change 10**
  (the harness still cannot vary `CurrencyData.inMultiplesOf` independently of
  `installmentAmountInMultiplesOf`).

## What may be promoted

Eleven captures — `P-00`, `P-01`, `P-02`, `P-02b`, `P-03`, `P-04f`, `P-04t`, `P-MNT-5M`, `P-MNT-1M2`,
`P-MNT-50M`, `P-MNT-4M999` — **once the four P0 items are closed**. `P-CAL` may never be promoted as a parity
vector; it is calibration at `(12, HALF_UP)`.

## What I could not settle, and what settling it needs

1. **Whether the eleven candidates are admissible as vectors.** They are not, today, purely for procedural
   reasons (P0 items 2–4). Settling it needs **one re-run of `Capture3.java`** after adding the attestation
   block and the three per-period columns, plus a committed run script. Cheap; no new analysis.
2. **How wide the precision-sensitivity boundary really is.** I established it exists at principal 4.00 on
   one shape and is absent at 50,000,000 on the same shape. I did **not** map it. Settling it needs a
   deliberate oracle sweep over `(n, rate)` as well as principal — my model is now oracle-corroborated at
   29 points (12 captures + 17 probe points) and is a safe locator, but every headline must still be re-run
   against the oracle. Recommend adding the 36 × 16.8 % small-principal family to the capture plan.
3. **Anything about the two dropped inputs from Path A.** Structurally unreachable through this seam; I can
   only prove they are dropped. Path B (running server + PostgreSQL) reaches them and was captured after
   pass 3; its audit is T22's, not mine. Nothing I found contradicts it — the server honours what the seam
   drops, which is exactly the rig defect T19 named.
4. **Whether `PASS2-REPORT.md` has been corrected** per T19's items 1–9. I did not verify; out of scope here,
   but a downstream reader of pass 3 will follow the cross-references into it.
5. **Nothing about the server path, multi-disbursement, down-payment rounding, `safeRoundingForEMI`'s
   zero-fallback, timezones or PostgreSQL.** Untouched by pass 3; Path A opens no database.

## Files I produced

```
.softhouse/reviews/T21-capture-pass3-audit.md      the audit (deliverable)
.softhouse/handoff/T21-capture-pass3-audit.md      this file
.softhouse/reviews/t21v2/t21v2-rederive.py         my from-source re-derivation (all 12 match)
.softhouse/reviews/t21v2/t21v2-invariants.py       my invariant checker (6 claimed + 6 mine)
.softhouse/reviews/t21v2/t21v2-crosspass.py        cross-pass structural comparison
.softhouse/reviews/t21v2/t21v2-threshold.py        model-located divergence scan (locator only)
.softhouse/reviews/t21v2/T21v2Probe.java           oracle probe: threshold + dropped inputs + reflection
.softhouse/reviews/t21v2/T21v2Probe2.java          oracle probe: compact p12/p19 sweep
.softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt    raw oracle output, probe 1
.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt   raw oracle output, probe 2
```

No file under `.softhouse/capture/` was modified. No Go was written. Nothing is stored in contract-shaped
form; DEC-1 and `docs/adr/` are untouched.
