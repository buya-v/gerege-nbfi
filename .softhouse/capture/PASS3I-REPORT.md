# Capture pass 3i — the two multiples-of inputs, finally told apart

Task **T74**. Recipe: `sh .softhouse/capture/src/run-pass3i.sh`. Harness
`.softhouse/capture/src/Capture3i.java`. It is pass 3h's rig with **one structural fix** and a new
case list; every precondition of pass 3h is preserved, three are added and one is replaced by a
strictly stronger form.

Reference oracle (Fineract) `426a23544e8426a38ae43ae404670a0a7e85b9eb`, image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, in-process, **no Fineract
server started and no database connection opened**. "Oracle" here is the Fineract reference
implementation; Oracle Database is a prohibited product in this program and PostgreSQL is the only
permitted one.

---

## Why the pass exists

T21 required change **P1-8** — which is T19 required change **10**, unfixed for six passes:

> `Capture3.java` constructs `new CurrencyData(code, code, digits, c.installmentMultiplesOf(), …)`
> **and** passes `c.installmentMultiplesOf()` as the model's `installmentAmountInMultiplesOf`, **and**
> emits both JSON keys from that same field. The harness structurally cannot vary the two
> independently.

One field, three destinations, **two entirely different mechanisms**. No capture taken through any
harness from `Capture3.java` to `Capture3h.java` could attribute an observed difference to either
input. And the difference is not hypothetical: T21's auditor observed that at
`currencyDecimalPlaces = 0`, MNT 5,000,000 / 18 × 18.5 % emits total interest **763994** at
`inMultiplesOf = null` and **764100** at `100`, all eighteen periods differing.

`Capture3i.java` gives them separate components, separate constructor arguments and separate emitted
keys, and the runner **refuses a run** in which the emitted pair is not demonstrably independent.

## The two mechanisms, from the pinned source

| | **channel 1** | **channel 2** |
|---|---|---|
| site | `Money.java:44-52`, the **private constructor** | `ProgressiveEMICalculator.java:1761-1776` |
| gated on | `currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && currency.getInMultiplesOf() > 0 && MathUtil.isGreaterThanZero(amountScaled)` — **four** conjuncts | `scheduleModel.installmentAmountInMultiplesOf() != null && > 0` |
| rounds | **every `Money` the calculation builds** — principal, interest, EMI, balance, plan totals | the **equal monthly installment only** |
| rule | nearest multiple, **tenant** rounding mode, `Money.java:150-157` | nearest multiple, mode from a `MathContext` parameter, `Money.java:163-170` (`:159-161` only delegates) |
| zero-guard | **none** | `safeRoundingForEMI` — a rounding that would zero a positive EMI is discarded (`:1772-1774`) |
| reachable on Path A | **yes** | **no** — `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` (`:579-607`) builds only through `Builder`, contains zero occurrences of `MultiplesOf`, and the `Builder` has no setter for it |

## The case list — 36

**Nine rig calibrations** (all eight of pass 3h's carried over unchanged, plus one added):

| calibration | reproduces | from |
|---|---|---|
| `P-CAL` | `P-CAL` at (12, HALF_UP) | pass 3b |
| `P-CAL-P00` | `P-00` | pass 3b |
| `P-CAL-EMI6` | `P-EMI-6-1M014632` | pass 3c |
| `P-CAL-LATQ0a` | `P-LAT-Q0a` | pass 3e |
| `P-CAL-MNT50M` | `P-MNT-50M` | pass 3b |
| `P-CAL-DRIFTF` | `P-DRIFT-F` | pass 3e |
| `P-CAL-ZPA` | `T64-ZP-A` | pass 3g |
| `P-CAL-ZPB` | `T64-ZP-B` | pass 3g |
| **`P-CAL-MNT5M`** *(added by 3i)* | **`P-MNT-5M`** | pass 3b |

`P-CAL-MNT5M` is the one that matters here: it is the `decimalPlaces = 2`, no-multiples-of control
that the whole group A/B family differs from in one or two fields, and its observation is **already a
promoted parity vector**. `P-CAL-MNT50M` is the same `36 × 16.8 %` shape as group E at a principal of
50,000,000. **All nine reproduced their committed observation cell for cell, `inputs` and tenant id
included.**

Then: a 2×2 factorial over the two inputs at `decimalPlaces = 0` (**group A**) and the same at the
production `decimalPlaces = 2` (**group B**); five gate-and-rule probes for channel 1 (**group C**);
a three-case zero-guard separator (**group D**); and the `36 × 16.8 %` small-principal shape T21
required change **P1-11** asked for, each with a precision-12 companion (**group E**).

## What was observed

### 1. Every cell the multiples-of family moves belongs to `CurrencyData.inMultiplesOf`

| pair | result |
|---|---|
| `T74-A0-DP0-NONE` vs `T74-A1-DP0-CUR100` | **DIFFERENT** — 763994 → 764100 |
| `T74-A0-DP0-NONE` vs `T74-A2-DP0-INST100` | **IDENTICAL** |
| `T74-A1-DP0-CUR100` vs `T74-A3-DP0-BOTH100` | **IDENTICAL** |
| `P-MNT-5M` vs `T74-B1-DP2-CUR100` | **IDENTICAL** |
| `P-MNT-5M` vs `T74-B2-DP2-INST100` | **IDENTICAL** |
| `P-MNT-5M` vs `T74-B3-DP2-BOTH100` | **IDENTICAL** |

`T74-A0` and `T74-A1` reproduce T21's section-B arms **cell for cell**, 19 rows each — so the earlier
observation is confirmed by a second harness, and for the first time it is **attributed**.

This is the **first observed** proof that Path A is blind to `installmentAmountInMultiplesOf`. Until
pass 3i that blindness rested on a source reading alone, because no harness could set the field
without also setting the currency's.

### 2. At the production `MinorUnitDigits = 2`, neither input moves a single cell

Group B is byte-identical to `P-MNT-5M` on all three arms. **A Gerege deployment runs MNT at minor
unit 2, so both inputs are inert in production through this seam**, and no vector over either of them
could grade anything.

### 3. The channel-1 gate is exactly four conjuncts

| case | `inMultiplesOf` | result |
|---|---|---|
| `T74-C1-DP0-CUR1` | 1 | **IDENTICAL** to baseline — gate opens, arithmetic inert at scale 0 |
| `T74-C2-DP0-CUR0` | 0 | **IDENTICAL** — `> 0` false |
| `T74-C3-DP0-CURNEG` | −100 | **IDENTICAL** — `> 0` false |
| `T74-C4-DP0-CUR7` | 7 | **DIFFERENT** |
| `T74-C5-DP0-CUR1000` | 1000 | **DIFFERENT** |

### 4. Channel 1 rounds the DISBURSED PRINCIPAL itself

`T74-C4-DP0-CUR7` requested a principal of **5,000,000** and the oracle emitted
`totalDisbursedAmount` **5,000,002**, with the `DISBURSEMENT` row's principal and balance both
`5000002`.

`LoanApplicationTerms.assembleFrom` opens with `Money.of(modelData.currency(),
modelData.disbursementAmount(), mc)` (`:580`), straight through the leaking constructor. **The
borrower is lent two tugriks that nobody asked for**, and the schedule then amortizes them
correctly. This is not a defect in Fineract — it is what "round monetary amounts into multiples of
say 20/50" means when the currency has no minor unit — but a port that quantized only the *output*
columns and not the *input* principal would diverge on the totals.

### 5. Channel 1 has no zero-guard, and that is what tells the two channels apart

`T74-D1-DP0-SMALL-CUR1000` — MNT 1,000 / 6 × 21.6 %, `inMultiplesOf = 1000`:

```
idx  emi   calcDueInt  dueInt  duePrincipal  balance  isFullyPaid
0    0     0           0       0             1000     True
...
4    0     0           0       0             1000     True
5    1000  0           0       1000          1000     False
```

Total interest **`0`**. Five of six EMIs quantize to zero and stay there. `safeRoundingForEMI` exists
precisely to prevent that — and it does not fire, because it belongs to the channel this seam never
reaches. **An observation of a mechanism by the absence of the guard that would have stopped it.**

### 6. The emitted `balance` column does not amortize to zero on that shape

The last row carries `principal 1000` and `balance 1000`. `totalOutstandingBalance` still ends at
`0` and `totalPrincipalAmount` still equals `totalDisbursedAmount`, so the plan totals are
consistent; the per-row outstanding-balance column is not.

**Mechanism, verified from source.** `RepaymentPeriod.getOutstandingLoanBalance()` (`:389-402`) is a
`Memo` whose dependency array is `{paidPrincipal, paidInterest, interestPeriods,
totalDisbursedAmount}` — **`emi` is not in it**, unlike `getDueInterest()`'s memo (`:288-289`), which
does list `emi`. With every EMI quantized to zero, every period is *vacuously* `isFullyPaid`
(`:371-372` is `emi + credited + FUI == totalPaid`, i.e. `0 == 0`), so
`calculateLastUnpaidRepaymentPeriodEMI` takes its `:1178-1181` fallback branch — and that branch's
last filter, `rp.getOutstandingLoanBalance().isGreaterThanZero()`, **populates the memo on the last
period**. `:1210` then raises that period's EMI to 1000 through a plain Lombok `@Setter` that
invalidates nothing, and nothing recomputes the balance afterwards: the smoothing loop breaks
immediately at `:1267` because `shouldBeAdjusted()` is false, so `:1306` never runs.

**The guard that finds the target period is what staled its balance.**

**This shape is at `decimalPlaces = 0` and therefore outside the graded domain.** Whether the same
mechanism is reachable at `decimalPlaces = 2` is an open follow-up with a named candidate shape — see
the T74 handoff. No promoted vector is affected: `principal_amortizes_to_zero` and
`balance_roll_forward` hold on all 42.

### 7. Group E — the `36 × 16.8 %` shape, and the first vectors that grade the precision seam

| principal (MNT) | interest at (19, HALF_UP) | at (12, HALF_UP) | graded cells that move |
|---|---|---|---|
| 4.00 | `1.14` | `1.13` | 23 of 146 |
| 59.00 | `16.51` | `16.52` | 27 of 146 |
| 72.00 | `20.14` | `20.13` | **2** of 146 |
| 340.00 | `95.15` | `95.16` | 25 of 146 |
| 426.00 | `119.18` | `119.20` | 39 of 146 |
| 6,940.00 | `1942.65` | `1942.66` | 18 of 146 |

Divergence runs in **both directions** across the six, so it is a rounding boundary and not a bias a
port could correct with a sign. The same shape at 50,000,000 (`P-CAL-MNT50M`, a promoted vector) is
precision-**insensitive**. **T21 §6.2's refutation of the size-threshold claim is confirmed
independently, at every one of the six principals.**

## Attestation

- run id `pass3i-20260820T093826Z` (the committed run)
- captures canonical sha256 **`41bcf7306f691b730d17ed7fa08131b16052d737773c80d12f5abacf6b7d581f`**
- **DETERMINISM CONTROL, free.** The pass was run **twice** with the identical harness
  (`Capture3i.java` sha256 `772f922687da55de9780e215dce12f8a834dc76a0b8ff7427d5400127b2ab06c`), at run
  ids `pass3i-20260820T092556Z` and `pass3i-20260820T093826Z`. Both produced the **same captures
  canonical sha256**, cell for cell across all 36 cases. The whole-file digests differ, as they must,
  because the attestation carries a UTC timestamp.
- effective `MathContext` **(19, HALF_UP), RoundingMode ordinal 4**, asserted by the runner on every
  case; `MoneyHelper.PRECISION` read from the runtime as **19**, not asserted
- stderr **empty** (`e3b0c442…b7852b855`, the sha256 of zero bytes)
- seam sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`, byte-identical to
  the pinned original **and** to the digest pinned as a literal in the runner
- `pathIdentity.identical` true on **36 of 36**
- image `git.commit.id` agrees with the pinned checkout; `git.dirty` false

## The prediction, and that it was registered first

`.softhouse/capture/t74-multiplesof/PREDICTION.md` and `predicted.json` were committed **two commits
before** `run-pass3i.sh` was run. `check-prediction.py` grades the capture against them:
**1,083 predictions over 875 money cells, 1,082 held, 1 refuted.** The refutation is sharp claim S2
— the final row's `balance` on `T74-D1` — and it is §6 above. Everything else, including both 19-row
schedules cell for cell and all twelve group-E totals, was confirmed.

## What this pass does NOT establish

- **Whether channel 1 reads the tenant rounding mode or the threaded one.** `Money.java:154` reads
  `MoneyHelper.getRoundingMode()` (tenant) while `:167` takes the mode from a `MathContext`
  parameter. Separating them needs a case whose threaded mode differs from its tenant mode, and the
  runner's precondition 9 refuses any case not at HALF_UP ordinal 4 in both. Weakening a standing
  guard to buy one observation was not done. `[UNVERIFIED-BY-CAPTURE]`.
- **Anything about channel 2's actual arithmetic.** This seam never delivers its input, so every
  statement about `safeRoundingForEMI` here is read from source. Path B is where it can be observed.
- **Anything about `decimalPlaces` other than 0 and 2.**
- **Promotion of anything from groups A–D.** See `PASS3I-PROMOTION` below.

## PASS3I-PROMOTION

**From groups A, B, C and D: NOTHING.** Four independent reasons, each sufficient:

1. The frozen contract's `Currency` struct carries `Code` and `MinorUnitDigits` and nothing else.
   There is **no field** for `CurrencyData.inMultiplesOf`, so a vector over it cannot be expressed as
   a contract request at all.
2. `Currency.MinorUnitDigits == 2` is a graded-domain predicate; groups A, C and D run at 0.
3. `capabilities.json` records `currency.zero.decimals` with `in_graded_domain: false`.
4. `installment.rounding.multiple` is `blind` on `path_a_embeddable` — and pass 3i is the capture
   that **proves** it. A vector over a blind capability grades nothing; that is the T66 lesson.

Group B is the sharpest of the four: its observed blocks are byte-identical to the already-promoted
`P-MNT-5M`, so a vector there would duplicate an existing one while claiming to grade an input it
cannot move.

**From group E: six vectors, promoted.** All at MNT `minor_unit_digits = 2` and (19, HALF_UP), inside
the graded domain, on `schedule.core`, which is `exercised` for this seam. Promotion script
`.softhouse/handoff/T74-promote-vectors.py`; it re-asserts every one of those conditions and exits
non-zero rather than writing a vector that fails one.

## Files

```
.softhouse/capture/src/Capture3i.java                             harness
.softhouse/capture/src/run-pass3i.sh                              recipe, 18 failure preconditions
.softhouse/capture/out/capture-prod3i-*                           capture, attestation, log, digests
.softhouse/capture/t74-multiplesof/PREDICTION.md                  registered first
.softhouse/capture/t74-multiplesof/predicted.json                 the machine-checkable form
.softhouse/capture/t74-multiplesof/check-prediction.py            grades the capture against it
.softhouse/capture/t74-multiplesof/build-counterfactuals.py       measures the precision margin
.softhouse/capture/t74-multiplesof/out/t74-counterfactuals-pass3i.json
.softhouse/handoff/T74-promote-vectors.py                         promotion
```
