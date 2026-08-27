# T116 — registered prediction, gate G-8 option (a), family-B PROMOTION capture

**Registered BEFORE any observation exists.** This file and `prediction.json` are committed in a
commit that is a **strict ancestor** of the commit carrying `out/capture-t116-raw.json`. If that
ancestry does not hold, this prediction is worthless and should be treated as such (P-9).

**The oracle here is the Fineract reference implementation** at pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, Path A embeddable seam, `(19, HALF_UP)`, MNT dp 2, in a
throw-away `docker run --rm` from the pinned image. **Oracle Database is a prohibited product in
this program and appears nowhere in this work**; no database connection is opened and no server is
started.

## What T116 is for

T116 carries an **explicit promotion mandate** for G-8 **option (a)**: promote a parity vector over
the family-B region with an explicit, narrow `invariant_exemptions` declaration. Options (b) and (c)
amend the graded domain and are hard `user` gates; T116 does not touch them, does not prepare them,
and recommends nothing about them.

T116 re-captures the shapes it intends to promote **from the live oracle** rather than transcribing
another task's committed bytes. A committed figure is evidence of when it was true, not that it is
true (P-63).

## The three cells

All at 600.0 % p.a. nominal, MNT, `minorUnitDigits = 2`, `FIXED_30_360`, monthly, `repaymentEvery`
1, disbursement 2024-01-01, schedule start 2024-01-01, no down payment, no rounding multiple —
entirely inside DEC-1's graded domain.

| id | n | B (minor) | predicted |
|---|---|---|---|
| `T116-CLEAN-R600p0-N103-B1` | 103 | 1 | **NOT family B.** Amortizes: principal repaid 1 minor unit, final-row balance **0** |
| `T116-FAMB-R600p0-N104-B1` | 104 | 1 | **family B.** Every repayment row `principal 0.00`; principal repaid **0**; balance **1** on every row including the last |
| `T116-FAMB-R600p0-N108-B1` | 108 | 1 | **family B.** Same shape |

Emission order is scrambled by the recorded permutation `random.Random(20260822)` and is
`T116-FAMB-R600p0-N104-B1, T116-CLEAN-R600p0-N103-B1, T116-FAMB-R600p0-N108-B1`. Tenant ids are
distinct from every previous pass (`t116_*`).

## Falsifiable claims, in integer minor units

1. **P1** — every case emits exactly `n` REPAYMENT rows plus one DISBURSEMENT row.
2. **P2** — on `N103`, the sum of REPAYMENT-row `principal` equals the disbursed **1** minor unit,
   and the final row's `balance` is **0**.
3. **P3** — on `N104` and `N108`, the sum of REPAYMENT-row `principal` is **0** minor units, and the
   final row's `balance` is **1** minor unit.
4. **P4** — on `N104` and `N108`, `totalPrincipalAmount` reads `0.00` while `totalInterestAmount` is
   strictly positive: interest is scheduled against a principal that is never repaid.
5. **P5 — an existence claim, so an empty measurement REFUTES rather than passes through** (T114's
   ruling on vacuous guards): **at least one** of the three cases is family B, and **at least one**
   is not. A capture in which every case looks alike refutes this file.
6. **P6** — the two rig calibrations `P-CAL-ZPA` / `P-CAL-ZPB` reproduce the already-promoted
   `T64-ZP-A` / `T64-ZP-B` **cell for cell with zero input differences**. If they do not, nothing
   else in this capture is admissible evidence.

## What this prediction does NOT claim

- **Nothing about family B's cause.** It remains `[UNVERIFIED]` by every task in this program, and
  F-T114-1 showed the leading (sub-ulp) explanation does not reach n = 104.
- **Nothing about the extent of family B** beyond these three cells.
- **Nothing about whether the Go port reproduces these cells.** That is measured afterwards, by the
  real harness, on the promoted store — not predicted here.
