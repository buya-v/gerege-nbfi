# `t27-probe` — T27 re-check scripts

> **NOT RUN AGAINST A LIVE ORACLE.** No Fineract instance and no PostgreSQL was reachable in the sandbox
> where these were written and run. **Neither script makes an oracle observation, and neither synthesizes,
> invents or extrapolates an oracle value.** Every input is an artifact already committed on `main`; every
> source citation is re-read from the pinned Fineract checkout at `/home/user/fineract`
> @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

Written for `.softhouse/reviews/T27-corpus-corrections-review.md` — the independent promotability audit of
T25's capture-corpus corrections.

## `t27_mutate.py` — mutation testing of the two invariant checkers T25 repaired

**Why.** T25 repaired two checks that could not fail:

- `.softhouse/capture/pathb/t22-probe/invariants.py` had `verdict("I5", True, …)` hard-coded (T22 P1-13).
- `.softhouse/capture/out/t21-probe-invariants.py`'s `X2` was a naive roll-forward, invalid for `P-03` whose
  first emitted row is a **pre-disbursement snapshot** (T21 P1-5); it was replaced by the audit's
  position-aware `A3`.

"It prints ALL PASS" does not show a check can fail. This script proves it can: it takes a **committed**
capture, corrupts **one money literal by one minor unit**, and asserts the checker reports FAILURE.

**Method.** Mutation is a **byte-level text substitution** on the raw JSON; the arithmetic is
`decimal.Decimal` in minor units. **No floating-point value is ever constructed** — required by CLAUDE.md,
and the reason this does not simply `json.load` / `json.dump` the file. Mutated files are written to a temp
directory and are never committed. No file under `.softhouse/capture/` is modified.

**Cases.**

| # | mutation | must break |
|---|---|---|
| Path B 1 | `B-01` 2nd `interestDue` `19971.32` → `.33` | `I5` |
| Path B 2 | `B-01` 4th `principalLoanBalanceOutstanding` +0.01 | `S2` |
| Path A A | `P-01` 4th repayment `balance` +0.01 | `X2` |
| Path A B | `P-03` DISBURSEMENT `principal` +0.01 | `X1` **and** `X2` — proves the new `X2` is not merely disabled for `P-03` |
| Path A C | `P-MNT-5M` 1st repayment `total` +0.01 | `I4`, `I5` |
| Path A D | *control*: the retracted **naive** `X2`, re-implemented, on the **unmutated** `P-03` | must still spuriously FAIL — proves the repair changed the formulation, not the data |

```sh
python3 .softhouse/reviews/t27-probe/t27_mutate.py          # both suites
python3 .softhouse/reviews/t27-probe/t27_mutate.py pathb    # Path B only
python3 .softhouse/reviews/t27-probe/t27_mutate.py passa    # Path A only
```

Result at the time of review: `T27 MUTATION VERDICT: ALL REPAIRED CHECKS ARE GENUINELY FAILABLE` (exit 0).

## `t27_verify_claims.py` — mechanical verification of every corrected claim

Forty checks over committed artifacts and the pinned source:

1. `PASS3-REPORT.md` and `PASS3-REPORT-shared.md` are byte-identical (SHA-256).
2. All **16** `(shape, principal) → (p12, p19, verdict)` triples the corrected PASS3 section asserts are
   parsed out of `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt` and matched exactly. Prints a NOTE
   that the 131,433 verdict is a full-schedule comparison whose **totals are equal** — the annotation the
   correction dropped (review RC-4).
3. `capture-prod-raw.json` really is 11 captures at `(19, HALF_UP)` + 1 calibration at `(12, HALF_UP)`
   — the `tasks.json` count fix.
4. Each P0 admissibility blocker is confirmed **still open in the artifact**: no `attestation` key, no
   `periodFromDate`/`feeAmount`/`penaltyAmount`, no run recipe, no Path B sidecar, the broken
   `-o out/B-$n-*-raw.json` glob and the missing `%{http_code}` and rounding-mode precondition.
5. The Path B round-**down** observation: the applied EMI is a single multiple of 100 across periods 1–11;
   an annuity model at `MathContext(19, HALF_UP)` is **calibrated against the committed `B-01` EMI** before
   being used, then re-derives the unrounded EMI `111,148.35`; the observed `111,100.00` is shown to be below
   it (round-**down**), a round-up rule is shown to give `111,200`, and round-to-nearest under HALF_UP is
   shown to reproduce the observation.
6. `FULL_LEAP_YEAR` ≡ field-unset and the day-count relations, by SHA-256 over committed probes:
   `p07 ≡ B-03`, `B-04 ≠ B-03`, `p05 ≡ p06`, `p07 ≠ p08`, `p09 ≡ B-01`.
7. The Path B fresh-tenant `(19, HALF_UP)` re-observation and the `t22-probe` re-capture are byte-identical
   to the committed corpus.

```sh
python3 .softhouse/reviews/t27-probe/t27_verify_claims.py
```

Result at the time of review: `ALL CHECKS PASS (0 failure(s))` (exit 0).

Decimal only; no floating-point anywhere. Read-only with respect to the repository.
