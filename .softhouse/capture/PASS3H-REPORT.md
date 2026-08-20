# Capture pass 3h — the mechanism columns

Task **T66**. Recipe: `sh .softhouse/capture/src/run-pass3h.sh`. Harness
`.softhouse/capture/src/Capture3h.java`. It is pass 3g's rig with a new case list **and one
new column family**; every precondition of pass 3g is preserved and three are added.

Reference oracle (Fineract) `426a23544e8426a38ae43ae404670a0a7e85b9eb`, image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, in-process, **no
Fineract server started and no database connection opened**. "Oracle" here is the Fineract
reference implementation; Oracle Database is a prohibited product in this program.

## Why the pass exists

`futureUnrecognizedInterest` **cannot be read off a returned schedule.** It feeds
`RepaymentPeriod.calculateCalculatedDueInterest()` (`:252-265`) and `getDueInterest()`
(`:271-286`), and `getDueInterest()` is
`min(calculatedDueInterest, emiPlusCreditedAmountsPlusFutureUnrecognizedInterest)`. On a
zero-EMI period that minimum is `min(cdi, 0) = 0` **whatever `cdi` is** — so an observed
interest of `0` on a dead row says nothing about the quantity
`getPeriodWithUnrecognizedInterest` (`:1805-1814`) actually tests. Every capture pass in
this program until now recorded only the returned plan, and was therefore structurally
blind to the field. That is why T63 could report the port gap only as **UNPROVEN**.

## How the field is reached without touching the seam

`ProgressiveEMICalculator` is `final`, so it cannot be subclassed. `Capture3h.java`
constructs the oracle's own `ProgressiveLoanScheduleGenerator` around the oracle's own
`ProgressiveEMICalculator` placed behind a `java.lang.reflect.Proxy` whose entire behaviour
is: delegate the call unchanged, and if the method was
`generatePeriodInterestScheduleModel`, remember the returned
`ProgressiveLoanInterestScheduleModel`. That is the same object the generator then mutates,
so after `generate()` returns the harness reads the oracle's own final per-period state:
`futureUnrecognizedInterest`, `interestMovedUpward`, `unrecognizedInterest`,
`calculatedDueInterest`, `dueInterest`, `emi`, `duePrincipal`, `outstandingLoanBalance`,
`totalPaidAmount`, `isFullyPaid`. **Nothing is reimplemented and the seam class is not
modified** — its byte identity against the pinned original is still asserted (precondition
4) and the run is void without it.

### PATH IDENTITY — the calibration that licenses reading those columns

Every case is **also** run through the pristine embeddable seam. Both plans are rendered
cell for cell by one renderer (`renderPlan`) and `run-pass3h.sh` **fails the run** if any
pair differs (new precondition 14). A mechanism column read off a lookalike computation
would be worthless.

Result: **18 of 18 identical.**

## Rig calibrations — 8, all reproduced cell for cell

Each calibration's `inputs` are byte-identical to a committed capture, **tenant id
included**, and its whole `observed` block must equal the committed one. The runner refuses
the run otherwise, and no expected value may ever be adjusted to make one pass.

| calibration | reproduces | from | precision |
|---|---|---|---|
| `P-CAL` | `P-CAL` | pass 3b | (12, HALF_UP) |
| `P-CAL-P00` | `P-00` | pass 3b | (19, HALF_UP) |
| `P-CAL-EMI6` | `P-EMI-6-1M014632` | pass 3c | (19, HALF_UP) |
| `P-CAL-LATQ0a` | `P-LAT-Q0a` | pass 3e | (19, HALF_UP) |
| `P-CAL-MNT50M` | `P-MNT-50M` | pass 3b | (19, HALF_UP) |
| `P-CAL-DRIFTF` | `P-DRIFT-F` | pass 3e | (19, HALF_UP) |
| **`P-CAL-ZPA`** | `T64-ZP-A` | **pass 3g** | (19, HALF_UP) |
| **`P-CAL-ZPB`** | `T64-ZP-B` | **pass 3g** | (19, HALF_UP) |

The two added by this pass are the point: `T64-ZP-B` is the **only shape in the entire
committed corpus whose schedule carries a zero-EMI tail**, which is exactly the
precondition half T63 could not test. The rig is calibrated **on** the shape under study,
not merely near it.

## Attestation

- run id `pass3h-20260820T063946Z` (the committed run)
- captures canonical sha256 **`fdd751a209c9518b157ca6fd70aef06a91acff94953e1f8cc6c4d45162b90b73`**
  (stable across runs; the whole-file digest is not, because the attestation carries a
  timestamp)
- `capture-prod3h-raw.json` sha256 `4181400baf3bf5cc8b99cb85e5c02a0a79b42708a1dc4a7635d105149bb7610c`
- harness `Capture3h.java` sha256 `08e002ea6da3e1c95ed2e3ae9d6d96af70031d3466cc534619e2b8884a605c6f`
- **DETERMINISM CONTROL, free.** The pass was run **twice**: once at run id
  `pass3h-20260820T062756Z` with harness sha256 `d620a8c1de31d6e68edd84256bd08b967b694f90762a63b6b398e10707cad39e`,
  and again after that harness's file header was rewritten (a **comment-only** change — the
  first draft had inherited pass 3f / task T64's rationale verbatim, a P-12 corrections
  leak). Both runs produced the **identical captures canonical sha256**
  `fdd751a209c9518b157ca6fd70aef06a91acff94953e1f8cc6c4d45162b90b73`, cell for cell across
  all 18 cases and all 416 mechanism rows. The whole-file digests differ, as they must,
  because the attestation carries a timestamp and the harness digest.
- effective `MathContext` **(19, HALF_UP), RoundingMode ordinal 4** — the ratified
  production setting, asserted by the runner
- stderr **empty** (`e3b0c442…b7852b855`, the sha256 of zero bytes)
- seam sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`, byte-identical
  to the pinned original
- image `git.commit.id` agrees with the pinned checkout; `git.dirty` false

## What was observed

18 cases, **416 period rows**.

- `futureUnrecognizedInterest` == `"0.00"` on **416 of 416** rows.
- `interestMovedUpward` == `false` on **416 of 416** rows.
- `unrecognizedInterest` == `"0.00"` on **416 of 416** rows.
- `pathIdentity.identical` == `true` on **18 of 18** cases.

**Five of the eighteen cases exhibit the full structural precondition** — at least one
period that is `isFullyPaid() == true` with `emi == "0.00"` and `totalPaidAmount == "0"`
(vacuously fully paid, nothing actually paid), lying **strictly after** the last
not-fully-paid period:

| case | n | last not-fully-paid index L | vacuously fully-paid periods after L |
|---|---|---|---|
| `P-CAL-ZPB` | 55 | 14 | **40** |
| `T66-M-R12000` | 12 | 1 | 10 |
| `T66-M-DRIFT-R2400` | 6 | 2 | 3 |
| `T66-M-DRIFT-R12000` | 12 | 1 | 10 |
| `T66-M-FLOOR-HR` | 5 | 1 | 3 |

**And on every one of them the oracle left `futureUnrecognizedInterest` at `"0.00"` and
`interestMovedUpward` at `false`.**

The reason is visible in the rows themselves, and it is **not** the reason the driver's
hypothesis proposed. Those tail periods do not merely fail the "strictly after" test — they
carry **`calculatedDueInterest == "0.00"` and `outstandingLoanBalance == "0.00"`**, because
`L` is by construction the period at which the loan finishes amortizing. Sample, lifted
from the capture (`dump-rows.py`):

```
=== T66-M-R12000   (n=12, last-not-fully-paid L=1)
    idx  emi        calcDueInt  dueInt     unrec   FUI     IMU    balance      fullyPaid
    0    121000.00  120000.00   120000.00  0.00    0.00    False  11000.00     False
    1    121000.00  110000.00   110000.00  0.00    0.00    False  0.00         False <- L
    2    0.00       0.00        0.00       0.00    0.00    False  0.00         True (after L)
   ...
    11   0.00       0.00        0.00       0.00    0.00    False  0.00         True (after L)
```

So the driver's hypothesis step 4 — *"those tail periods can carry
`getUnrecognizedInterest() > 0`"* — is **refuted on every observed shape**. The mechanism is
inert for two independent reasons, and the observation establishes the simpler one.

## What this pass does NOT establish

- It reads the **real** model. The `futureUnrecognizedInterest` decision is taken on a
  **deep copy** (`:1226`). That is sound for this question because on the ordinary generate
  path `calculateLastUnpaidRepaymentPeriodEMI` is entered on the real model exactly once
  (`:747`), the field is written as the last act of that call (`:1250`) and nothing after it
  resets the field on the real model — `:1288`'s calls run on the smoothing loop's trial
  copy. So the observed value **is** the outcome of the one decision. It is **not** an
  observation of the copy's internal state.
- It says nothing about the smoothing loop's **trial** copy, about multi-tranche
  disbursement, payments, charges, re-aging, capitalized income or interest pauses. Every
  one of those breaks a premise of the T66 proof — see `t66-unrecognized-interest/PREDICTION.md` §4.
- **Nothing here is promoted to the parity vector store.** These are mechanism observations,
  not parity candidates: no counterfactual moves a cell of them, because the field they
  record is not a field the frozen contract returns.

## Files

```
.softhouse/capture/src/Capture3h.java          harness
.softhouse/capture/src/run-pass3h.sh           recipe, 15 failure preconditions
.softhouse/capture/out/capture-prod3h-*        capture, attestation, log, digests
.softhouse/capture/t66-unrecognized-interest/PREDICTION.md        registered first
.softhouse/capture/t66-unrecognized-interest/check-prediction.py  P1..P5 against the capture
.softhouse/capture/t66-unrecognized-interest/dump-rows.py         the rows around L
```
