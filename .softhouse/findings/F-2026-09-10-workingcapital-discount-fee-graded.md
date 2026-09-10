# F-2026-09-10 — workingcapital now GRADES total_discount_fee; the clamp stays refused

**Status:** RESOLVED for `total_discount_fee` (the refusal is relaxed, the first
non-zero observation is promoted as WC-06, and a new drive is live). OPEN for
the `UnrealizedIncomeFromDiscountFee` clamp and for the eleven other stored terms
still refused — a relaxation is only for a term a capture has earned.
**Extends:** [`F-2026-09-10-workingcapital-ungraded-terms.md`](F-2026-09-10-workingcapital-ungraded-terms.md).
**Subject capture:** `.softhouse/capture/wc-discount-nonzero/` (committed by
`OH-WCCAP-P`; **this run is the grading half of that deliberate split** — no
capture was taken, no POST/PUT/DELETE issued, nothing created in the oracle).
**Scope:** one bounded context, `workingcapital`. `.softhouse/guards/ledger-invariants.baseline`
and `.softhouse/conformance.sh` untouched.

## What is newly graded

The capture holds facility **id 2** `OHWCCAP-DISCNONZERO-L01` (product id 2
`OHK-WC-Discount-Nonzero`, discount `37.53` MNT, non-overridable), client 5,
disbursed 1000 on 2026-09-03. Its balance read-back is the first committed
observation of a non-zero `totalDiscountFee`. Every cell below was re-read from
the committed file (not from the OWNER prose) and re-verified before anything
was built on it; the capture hash was re-verified after promotion:

    sha256(.softhouse/capture/wc-discount-nonzero/out/wc-loan-discount-detail-raw.json)
      = 65e67678218eda58aa1536726c98ef0ddd88ca962556adfe5ecd260f88f967b9   == capture_sha256

| cell (file) | value (MNT) | minor units | vector field |
|---|---|---:|---|
| `balance.totalDiscountFee` | 37.53 | **3753** | `total_discount_fee` |
| `balance.principal` | 1037.53 | **103753** | `principal` |
| `balance.principalOutstanding` | 1037.53 | 103753 | `principal_outstanding` |
| `balance.totalExpectedRepayment` | 1037.53 | 103753 | `total_expected_repayment` |
| `balance.totalOutstanding` | 1037.53 | 103753 | `total_outstanding` |
| `balance.unrealizedIncomeFromDiscountFee` | 37.53 | 3753 | `unrealized_income_from_discount_fee` |
| `balance.principalPaid` | 0.0 | 0 | `principal_paid` |
| `balance.totalRepayment` | 0.0 | 0 | `total_repayment` |
| `balance.totalDisbursement` | 0.0 | 0 | `total_disbursement` |
| `disbursementDetails[0].principal` | 1000.0 | 100000 | `disbursement.principal` |
| `disbursementDetails[0].actualAmount` | 1000.0 | 100000 | `disbursement.actual_amount` |
| `status.id` / `.code` / `.active` | 300 / `loanStatusType.active` / true | — | `status_id` / `status` / `status_active` |

All values are whole minor units (MNT ISO 496, minor unit 2); **no sub-minor
residue**, so G-19 / DEC-2 predicate G-08 does not bite. The principal algebra
is the oracle's own, read from the reference file:
`WorkingCapitalLoanBalance.java:118` sets `totalDiscountFee = discount` and
`:119` sets `principal = disbursedAmount.add(discount)` (method `:115-121`), so
`1000 + 37.53 = 1037.53`. A port that drops the add is wrong.

## What was promoted

* `.softhouse/vectors/workingcapital/WC-06-detail-discount-nonzero.json` —
  parity vector, seam `working-capital-loans-detail`, capability
  `wc-loan-balance-read`, `capture_ref`
  `.softhouse/capture/wc-discount-nonzero/out/wc-loan-discount-detail-raw.json`,
  `capture_sha256` `65e67678218eda58aa1536726c98ef0ddd88ca962556adfe5ecd260f88f967b9`,
  `capture_case_id` `OHWCCAP-DISCNONZERO-L01`, citation with the raw balance
  block and `file:line` from the Fineract tree. 15 cells pinned.

Under `workingcapital-go` the store now reports
`vectors_loaded=6 parity_pass=6 parity_fail=0 refused=0 inadmissible=0
harness_error=0`, `graded_cells=62 money_cells=40 invariant_violations=0`.

## The refusal, relaxed for TotalDiscountFee ONLY

`workingcapital/balance.go` `ValidateGradedDomain()` is the seam that refuses a
stored term the corpus cannot discriminate (added by `OH-WC-S`). Exactly one
entry was removed — the `{"TotalDiscountFee", ...}` line. The eleven remaining
refusals all still stand, each still a true statement about the corpus:

    PrincipalPaid, PrincipalAdjustment, Fee, FeePaid, Penalty, PenaltyPaid,
    RealizedIncomeFromDiscountFee, OverpaymentAmount, TotalDisbursement,
    TotalDiscountFeeAdjustment, BreachPastDueAmount

`Principal` (100051 in the seed capture) and now `TotalDiscountFee` (3753) are
the only two stored terms admitted. Removing the one entry the capture earned is
the whole relaxation; nothing else was dropped, and the unit tests still assert
every remaining refusal fires and names its term
(`workingcapital_test.go:127-149`).

## The new drive, and proof it was inert before it was live

`workingcapital-wrong-discount-dropped-from-principal`
(`nexus/internal/apps/workingcapital/conformance/impl.go`) stores the product
discount in `totalDiscountFee` but sets `principal` to the disbursed amount
alone, dropping the discount the oracle adds (`principal -= totalDiscountFee`).
`kills.sh` measures it, and the same binary measured against a scratch store
containing only the five seed vectors:

| store | vectors | `parity_fail` for the drive |
|---|---:|---:|
| old corpus (`.softhouse/vectors/workingcapital` minus WC-06) | 5 | **0** |
| new corpus (full store) | 6 | **1** |

Zero on the old corpus and one on the new proves the gap was real: every earlier
captured balance carried `totalDiscountFee` 0, so subtracting it from principal
changed nothing and no drive could see the defect. The kill is exactly WC-06.
**The drive was measured, not assumed** — had WC-06 not been promoted, this
binary would have been an inert drive killing zero, and the finding is that the
corpus, not the drive, was the missing instrument.

## What this capture still CANNOT grade

### The `max(..., 0)` clamp — deliberately NOT driven

`UnrealizedIncomeFromDiscountFee` ports
`WorkingCapitalLoanBalance.java:151-155` (`max(totalDiscountFee − adjustment −
realized, 0)`, the `.max(BigDecimal.ZERO)` at `:154`). The facility now supplies
the first non-zero operand (`totalDiscountFee 3753`), but
`totalDiscountFeeAdjustment` and `realizedIncomeFromDiscountFee` are both **0**,
so the un-clamped expression is `3753 − 0 − 0 = +37.53` — firmly on the
**positive** branch. A port that omits the `max(…, 0)` computes the same answer.
**No drive for the clamp was registered: it would kill zero.** The clamp is gradeable
only from a balance in which

    totalDiscountFeeAdjustment + realizedIncomeFromDiscountFee > totalDiscountFee

so the un-clamped expression goes negative and `max(…, 0)` is the only thing
making the result 0. The oracle reaches that through a non-zero discount
(`totalDiscountFee` set at disbursement, `:118`), amortization raising
`realizedIncomeFromDiscountFee`
(`WorkingCapitalLoanDiscountFeeAmortizationServiceImpl.java:116`), and a
discount change raising `totalDiscountFeeAdjustment` and reducing `principal`
(`WorkingCapitalLoanWritePlatformServiceImpl.java:1056-1057`). A discount
reduction after some income is realised, or any adjustment exceeding the
remaining discount, drives it negative. That write is the natural next capture —
and it mutates the very facility these numbers were read from, which is why this
capture deliberately did not exercise it.

### `total_disbursement` — structurally zero, no capture can close it

Left refused. `OH-WC-S` established that no caller of `setTotalDisbursement`
exists anywhere under the reference `src/main`, so the column is structurally
zero in the reference implementation: there is no observation to take. The
refusal protects against a divergent database row and stays.

## Controls and kill counts (re-measured on this tree)

Instrument control (proves `kills.sh` is live): `loanschedule-wrong-days-in-year-365 -> 45`.

Every `workingcapital` drive, via `kills.sh workingcapital <impl>`:

    workingcapital-go                                        -> 0   (control)
    workingcapital-wrong-total-outstanding                   -> 3
    workingcapital-wrong-tranche-dropped                     -> 1
    workingcapital-wrong-status-ordinal                      -> 1
    workingcapital-wrong-list-row-mapping                    -> 1
    workingcapital-wrong-discount-dropped-from-principal     -> 1   (new)

The four pre-existing drives were not weakened by the change (each still kills
its own vectors); the new one kills exactly WC-06. No drive kills zero.

## Bar

`go build ./...` clean; `go test ./...` clean; `bash .softhouse/conformance.sh`
still exits 2 as the recorded §4.4.2 decision with the ledger findings at the
baseline pairs and census 17 — the same verdict as before the change. No
`.dump` committed; no baseline or harness file touched; no oracle write issued.
