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

Section 1 (product) is **done and committed**. Section 2 (facility + disburse +
read-back) is filled in by the second commit.

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
  `WorkingCapitalLoanBalance.applyDisbursement()` (`WorkingCapitalLoanBalance.java:117`),
  **not** multiplied by anything, so it lands on exactly **3753 minor units**
  (MNT, minor unit 2). No sub-minor residue (G-19 / DEC-2 predicate G-08).
* **`principalAmount = 1000`** (integer token) and **disbursement
  `transactionAmount = 1000`** (integer token), so no money value in any `req/`
  body is a JSON float — every non-integer value is a quoted decimal string.

Expected post-disbursement balance (from the oracle's own algebra:

    WorkingCapitalLoanBalance.applyDisbursement(disbursedAmount):
        totalDiscountFee = product.discount          = 37.53     -> 3753 mono
        principal        = disbursedAmount + discount = 1037.53   -> 103753
        overpaymentAmount                             = 0
        principalPaid                                 = 0
        realizedIncomeFromDiscountFee                 = 0
        totalDiscountFeeAdjustment                    = 0
    WorkingCapitalLoanBalance.getUnrealizedIncomeFromDiscountFee():
        max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncome, 0)
                                                      = max(37.53 - 0 - 0, 0) = 37.53 -> 3753

All money cells land on whole minor units. `totalDisbursement` stays 0: it has
**no write path** in the oracle's working-capital module (structurally zero for
MNT), so no capture can grade it.

## Byte-stability of `req/`

Every money value in `req/` is an integer token (`1000`) or a quoted decimal
string (`"37.53"`). No `json.dumps` of a parsed number, so no `100.00 -> 100.0`
class drift. To be re-verified before the final commit.

## Endpoints driven

| step | endpoint | status | artifact |
|---|---|---|---|
| list products (pre) | `GET /working-capital-loan-products` | 200 | `out/wc-products-pre-raw.json` |
| create product | `POST /working-capital-loan-products` | 200 `{"resourceId":2}` | `out/wc-product-discount-create-raw.json` |
| list products (post) | `GET /working-capital-loan-products` | 200 | `out/wc-products-post-raw.json` |
| product read-back | `GET /working-capital-loan-products/2` | 200 | `out/wc-product-discount-readback-raw.json` |

Script: `bin/step01-product.sh` (re-runnable; product keyed on name).

## Safety

Tenant `gerege` only; SQL was read-only; nothing was SQL-inserted. No `.dump` is
committed. No `.go` file, guard, or `ErrNoGradedCapture` refusal was touched.

## What the grading run inherits

* Product id **2**, discount **37.53** -> `totalDiscountFee` **3753** minor units
  once a facility is disbursed on it.
* `unrealized_income_from_discount_fee` = **3753** with adjustment and realized
  income both 0, i.e. the clamp is exercised with a non-zero operand but the
  un-clamped expression is still positive. To make the clamp itself
  discriminating the grading run needs
  `adjustment + realized > totalDiscountFee` (a discount-fee adjustment or
  realized amortization on top), which is a follow-on capture, not this one.
