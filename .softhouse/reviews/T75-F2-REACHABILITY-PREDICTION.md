# T75 — reviewer's OWN prediction, registered BEFORE the probe runs (P-9)

Task T75, independent review of `softhouse/T74-pathA-multiplesof`. This file is committed
**before** any capture is taken, so that the probe below cannot be re-described after the fact.

## What is being settled

T74 follow-up **F-2**: is the stale-balance mechanism of `RepaymentPeriod.getOutstandingLoanBalance()`
reachable **inside the graded domain** (`Currency.MinorUnitDigits == 2`)? T74 observed it only at
`decimalPlaces = 0` with `CurrencyData.inMultiplesOf = 1000` (`T74-D1`), a configuration the frozen
contract cannot even express, and marked reachability at dp 2 `[UNVERIFIED]` with a named candidate.

If it IS reachable at dp 2, the reference oracle emits a **graded-domain** schedule whose `balance`
column does **not** amortize to zero, which contradicts this project's stated
`principal_amortizes_to_zero` / `balance_roll_forward` property invariants.

## The probe

Path A, in-JVM embeddable seam, pinned Fineract `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
image `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, tenant rounding
HALF_UP (ordinal 4), `MoneyHelper.PRECISION` 19. No Fineract server, no database connection, no
shared oracle state written.

Calibrations carried, both already-promoted parity vectors at the rounding floor and at dp 2:
`T64-ZP-A` (MNT 0.28 / 56 x 21.6%) and `T64-ZP-B` (MNT 0.28 / 55 x 21.6%), inputs byte-identical to
pass 3g including tenant id. If either fails to reproduce, nothing else from the probe is believed.

Candidate, **T74's own fully specified F-2 candidate**: MNT **0.01** / **6** x **21.6 %**,
`currencyDecimalPlaces = 2`, `(19, HALF_UP)`, start = disbursement = 2024-01-01, MONTHS/1,
DECLINING_BALANCE, DAYS_30 / DAYS_360, no down payment, **both multiples-of inputs null**.
Neighbours captured alongside to bound the region: MNT 0.01 / 12, MNT 0.02 / 6, MNT 0.03 / 6,
MNT 0.05 / 6 and MNT 0.01 / 56, same settings.

## Predictions (registered)

Derivation. r = 0.216 / 12 = 0.018. Annuity factor r / (1 - (1+r)^-6) = 0.018 / (1 - 1.018^-6)
= 0.018 / 0.1016808... = 0.1770486... Level installment = 0.01 x 0.1770486 = **0.00177**, which
quantizes to **0.00** at scale 2. So:

- **R1.** Every one of the six periods carries `emi 0.00`, therefore
  `isFullyPaid` is vacuously true on all six (`RepaymentPeriod.java:371-372`, `0 == 0`), therefore
  `findLastUnpaidRepaymentPeriod` is empty and `getTotalPaidPrincipal()` is zero, therefore
  `calculateLastUnpaidRepaymentPeriodEMI` takes the `:1178-1181` fallback branch.
- **R2.** The `:1180` filter `rp.getOutstandingLoanBalance().isGreaterThanZero()` evaluates the
  memo on the LAST period while its `duePrincipal` is still 0, so the memo is populated with
  **0.01** and the period is selected.
- **R3.** `:1210` raises that period's EMI to `diff` = 0.01 + 0 - 0 = **0.01** through a plain
  `@Setter` that invalidates nothing; `emi` is absent from the memo's dependency array
  (`RepaymentPeriod.java:400`), so the balance is NOT recomputed.
- **R4. THE HEADLINE PREDICTION.** The final repayment row comes back
  `principal 0.01, interest 0.00, total 0.01, **balance 0.01**` — i.e. a graded-domain schedule
  whose outstanding-principal column does **not** reach zero. Rows 1-5 come back
  `principal 0.00, interest 0.00, total 0.00, balance 0.01`.
- **R5.** `totalInterestAmount` = **0.00**; `totalPrincipalAmount` = `totalDisbursedAmount` =
  **0.01**; `totalRepaymentAmount` = **0.01**.
- **R6.** MNT 0.02 / 6 quantizes to 0.0035 -> 0.00 and behaves the same (balance 0.02 on every row).
  MNT 0.05 / 6 quantizes to 0.00885 -> **0.01**, a NON-zero EMI, so the poisoning branch does
  **not** run and that schedule amortizes to zero normally. The boundary between the two is
  therefore predicted to fall between MNT 0.02 and MNT 0.05 for the 6 x 21.6 % shape.
- **R7.** The two calibrations reproduce pass 3g's committed `T64-ZP-A` and `T64-ZP-B` observed
  blocks cell for cell.

**If R4 holds, F-2 is settled AFFIRMATIVE and the finding is material:** the reference oracle
produces, inside the graded domain, a schedule that violates a stated property invariant of this
project, and no vector in the store has power over it.

**If R4 is refuted** — for instance if the seam refuses the request, or if some other guard raises
the EMI before the memo is touched — that refutation is recorded here as such, and F-2 stays open
with the negative result named.

Registered by the T75 reviewer before running the probe.
