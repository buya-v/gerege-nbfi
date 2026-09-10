# OWNER — wc-discount-nonzero

**Subject:** a working-capital product whose `discount` is NON-ZERO, so a facility
disbursed on it carries a non-zero `totalDiscountFee` and the
`UnrealizedIncomeFromDiscountFee` clamp gets its first non-zero operand.

**Oracle:** Fineract reference implementation, tenant `gerege`, containers
`gerege-oracle-db` (postgres) + `gerege-oracle-app` (fineract).
**Business date observed:** 2026-09-03 (COB date 2026-09-02).
**Snapshot (pre-write):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohwccapp-write-20260910T122128Z.dump`
(3,099,608 bytes, magic `PGDMP`, `pg_restore -l` = 2,515 TOC entries). Not committed.

## Status

**Complete.** Product created and committed; facility submitted, approved,
disbursed and read back, committed separately. The discounted facility exists in
the oracle with a **non-zero `totalDiscountFee` (3753 minor units)**.

## 2. What was created (facility)

| object | id | fields observed |
|---|---|---|
| working-capital loan `OHWCCAP-DISCNONZERO-L01` | **2** | `productId 2`, `clientId 5`, principal 1000, `totalPaymentVolume 1000`, `periodPaymentRate 1`, disbursed 2026-09-03, status `loanStatusType.active` |

Endpoint chain (all 200):
`POST /working-capital-loans` -> resourceId 2,
`POST /working-capital-loans/2?command=approve`,
`POST /working-capital-loans/2?command=disburse`
(`out/wc-loan-discount-disburse-raw.json` -> `{"loanId":2,"subResourceId":3,
"changes":{"actualDisbursementDate":[2026,9,3],"transactionAmount":1000,"status":"ACTIVE"}}`),
`GET /working-capital-loans/2`.

### Balance read-back — the deliverable

`GET /working-capital-loans/2` -> 200, `out/wc-loan-discount-detail-raw.json`,
`balance` block:

| field | value (MNT) | minor units |
|---|---|---|
| `totalDiscountFee` | **37.53** | **3753** |
| `totalDiscountFeeAdjustment` | 0.0 | 0 |
| `realizedIncomeFromDiscountFee` | 0.0 | 0 |
| `unrealizedIncomeFromDiscountFee` | **37.53** | **3753** |
| `principal` | 1037.53 | 103753 |
| `principalPaid` | 0.0 | 0 |
| `principalOutstanding` | 1037.53 | 103753 |
| `totalExpectedRepayment` | 1037.53 | 103753 |
| `totalOutstanding` | 1037.53 | 103753 |
| `totalRepayment` | 0.0 | 0 |
| `totalDisbursement` | 0.0 | 0 (structural — no writer) |
| `overpaymentAmount` | 0.0 | 0 |
| `fee` / `penalty` / `breachPastDueAmount` | 0.0 | 0 |

`balance.principal` (1037.53) = disbursed 1000 + discount 37.53, exactly the
algebra in `WorkingCapitalLoanBalance.applyDisbursement()`
(`WorkingCapitalLoanBalance.java:115-120`: `this.totalDiscountFee = discount`
at :118, `this.principal = disbursedAmount.add(discount)` at :119). The
top-level loan `principal` is the net 1000.0.

Read-only DB cross-check (`out/db-crosscheck-readonly.txt`):

    m_wc_loan_balance : 2|2|1037.530000|0.000000|37.530000|0.000000|0.000000|0.000000
    m_wc_loan         : 2|OHWCCAP-DISCNONZERO-L01|2|1000.000000|1000.000000|1.000000|37.530000|37.530000
    m_wc_loan_product : 2|OHK-WC-Discount-Nonzero|37.530000
    (cols: id|loan|principal|principal_paid|total_discount_fee|total_discount_fee_adjustment|realized_income_from_discount_fee|total_disbursement)

Everything was written **through the REST API**; SQL was read-only.

## 1. What was created (product)

| object | id | fields observed |
|---|---|---|
| working-capital product `OHK-WC-Discount-Nonzero` | **2** | `discount 37.53`, `principal 1000.0`, `periodPaymentRate 1.0`, `npvDayCount 360`, `currency MNT` decimalPlaces 2, `allowAttributeOverrides.discountDefault false` |

Endpoint: `POST /working-capital-loan-products` -> 200 `{"resourceId":2}`
(`out/wc-product-discount-create-raw.json`, `.status`). Read-back:
`GET /working-capital-loan-products/2` -> 200
(`out/wc-product-discount-readback-raw.json`) shows `"discount": 37.53`.

`allowAttributeOverrides.discountDefault = false` makes that discount the
NON-OVERRIDABLE product default, so a loan submitted on this product inherits it
without a per-loan `discount` param
(`WorkingCapitalLoanAssemblerImpl.java:187-190`).

## Choice of numbers, and the arithmetic (worked out BEFORE creating anything)

* **`discount = 37.53`** — non-round: a whole-tugrik port or a hardcoded-zero
  port loses the `.53`, so truncation is visible. It is stored directly by
  `WorkingCapitalLoanBalance.applyDisbursement()` (`WorkingCapitalLoanBalance.java:118`),
  **not** multiplied by anything, so it lands on exactly **3753 minor units**
  (MNT, minor unit 2). No sub-minor residue (G-19 / DEC-2 predicate G-08).
* **`principalAmount = 1000`** (integer token) and **disbursement
  `transactionAmount = 1000`** (integer token), so no money value in any `req/`
  body is a JSON float — every non-integer value is a quoted decimal string.

Predicted post-disbursement balance, from the oracle's own algebra:

    WorkingCapitalLoanBalance.applyDisbursement(disbursedAmount):
        totalDiscountFee = product.discount           = 37.53            -> 3753
        principal        = disbursedAmount + discount = 1000 + 37.53     -> 103753
        overpaymentAmount / principalPaid / realizedIncome / adjustment   = 0
    WorkingCapitalLoanBalance.getUnrealizedIncomeFromDiscountFee():
        max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncome, 0)
                                                      = max(37.53 - 0 - 0, 0) = 37.53 -> 3753

**Observed == predicted**, to the cent (see section 2). All money cells land on
whole minor units. `totalDisbursement` stays 0: it has **no write path** in the
oracle's working-capital module (structurally zero for MNT), so no capture can
grade it.

## Byte-stability of `req/`

Every money value in `req/` is an integer token (`1000`) or a quoted decimal
string (`"37.53"`). No `json.dumps` of a parsed number, so no `100.00 -> 100.0`
class drift. **Verified** — a scan of all `req/*.json` finds zero `\d+\.\d+`
tokens outside quoted strings:

    req/wc-product-discount-create.json  53e94ef087039b14  ("discount":"37.53")
    req/wc-loan-discount-submit.json     fdaa15ee8417257b
    req/wc-loan-discount-approve.json    f7912d1f628149f4
    req/wc-loan-discount-disburse.json   3299f5ad79653edb

## Endpoints driven (every pair in `out/`)

| step | endpoint | status | artifact |
|---|---|---|---|
| list products (pre) | `GET /working-capital-loan-products` | 200 | `out/wc-products-pre-raw.json` |
| create product | `POST /working-capital-loan-products` | 200 `{"resourceId":2}` | `out/wc-product-discount-create-raw.json` |
| list products (post) | `GET /working-capital-loan-products` | 200 | `out/wc-products-post-raw.json` |
| product read-back | `GET /working-capital-loan-products/2` | 200 | `out/wc-product-discount-readback-raw.json` |
| list loans (pre) | `GET /working-capital-loans` | 200 | `out/wc-loans-pre-raw.json` |
| submit loan | `POST /working-capital-loans` | 200 `{"resourceId":2}` | `out/wc-loan-discount-submit-raw.json` |
| approve loan | `POST /working-capital-loans/2?command=approve` | 200 | `out/wc-loan-discount-approve-raw.json` |
| disburse loan | `POST /working-capital-loans/2?command=disburse` | 200 | `out/wc-loan-discount-disburse-raw.json` |
| loan read-back | `GET /working-capital-loans/2` | 200 | `out/wc-loan-discount-detail-raw.json` |
| list loans (post) | `GET /working-capital-loans` | 200 | `out/wc-loans-post-raw.json` |

Scripts: `bin/step01-product.sh`, `bin/step02-facility.sh` (re-runnable; product
keyed on name, loan keyed on `externalId`).

## Safety

Tenant `gerege` only; SQL was read-only; nothing was SQL-inserted. No `.dump` is
committed. No `.go` file, guard, or `ErrNoGradedCapture` refusal was touched.

## What the grading run inherits

* Product id **2** `OHK-WC-Discount-Nonzero`, `discount 37.53`
  (`allowAttributeOverrides.discountDefault false`).
* Facility id **2** `OHWCCAP-DISCNONZERO-L01` on that product, client 5,
  disbursed 2026-09-03 for 1000.
* `totalDiscountFee` = **37.53 MNT = 3753 minor units** (non-zero for the first
  time), `principal` = **1037.53 MNT = 103753 minor units**.
* `unrealized_income_from_discount_fee` = **3753 minor units**, with
  `totalDiscountFeeAdjustment = 0` and `realizedIncomeFromDiscountFee = 0`, i.e.
  the clamp `max(totalDiscountFee - adjustment - realized, 0)` now has a
  **non-zero first operand** but the un-clamped expression is still positive, so
  the `max(...,0)` branch itself is not yet discriminated.

### How close the clamp came, and what remains

The clamp is on the last step of the discount-income chain. The facility now
supplies `totalDiscountFee = 3753`; two terms remain at 0:

* `totalDiscountFeeAdjustment` — increased by
  `updateBalanceForDiscountChange(loan, amount, true)`
  (`WorkingCapitalLoanWritePlatformServiceImpl.java:1048-1054`:
  `balance.setTotalDiscountFeeAdjustment(balance.getTotalDiscountFeeAdjustment().add(amount))`,
  and `principal` reduced by the same amount), reached from
  `makeDiscountFeeAdjustment` (`...WritePlatformServiceImpl.java:555`). Its
  command is `WorkingCapitalLoanDiscountFeeAdjustmentCommandHandler`
  (`@CommandType(entity = "WORKINGCAPITALLOAN", action = "DISCOUNTFEEADJUSTMENT")`).
  It requires a `relatedResourceId` pointing at an active `DISCOUNT_FEE`
  transaction (`...WritePlatformServiceImpl.java:568-572`) and is validated
  against the still-unadjusted remainder of that discount
  (`validator.validateDiscountAdjustmentTransaction(..., remainingDiscountAmount, ...)`,
  `:581-588`). The facility captured here is the `DISCOUNT_FEE` transaction that
  this adjustment would target.
* `realizedIncomeFromDiscountFee` — recomputed from the net of non-reversed
  `DISCOUNT_FEE_AMORTIZATION` transactions by
  `recalculateRealizedIncome` (`WorkingCapitalLoanDiscountFeeAmortizationServiceImpl.java:111-121`,
  setter at `:116`).

(There is also a separate one-time discount-*change* command,
`PUT /working-capital-loans/{loanId}/discount`
(`WorkingCapitalLoanApiResource.java:352-366`); this capture did not exercise
it.)

Driving `adjustment + realized > 37.53` is what makes the un-clamped expression
negative and finally exercises the `max(...,0)` floor. That is deliberately
left to the grading/follow-on run: this capture's objective was the non-zero
`total_discount_fee`, and the discount-change command mutates the facility that
the numbers above were read from. A capture of that command (its accept/refuse
response and the resulting balance read-back) is the natural next write.
