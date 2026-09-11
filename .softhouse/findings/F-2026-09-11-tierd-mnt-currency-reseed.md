# F-2026-09-11 — Tier D replay re-seeded to MNT (currency edit only, disposable copy)

Status: IN PROGRESS (OH-TIERD4-BM). This note is committed at the currency-edit step, before the
replay, per the task's iteration-100 gate.

## What was decided, and by whom

The driver's decision of 2026-09-11: MNT, like EUR, has 2 minor digits (ISO 4217 496), so a
scenario's arithmetic does not change with the currency code. Re-seeding the throwaway's seeded
currency to MNT and replaying produces the **oracle's own responses in MNT** — observations, not
synthesis. The edit is made only in the disposable copy `/Users/buv/fineract-tierd`, never in the
pinned `/Users/buv/fineract`, and is recorded as a diff in the capture's `OWNER.md`.

## Where the e2e runner fixes the currency

`fineract-test-application.properties` contains no currency setting. The currency is fixed by two
runner-side mechanisms:

1. `CurrencyGlobalInitializerStep.CURRENCIES` (runner, `@Order(HIGHEST_PRECEDENCE)`) posts the
   active-currency list via `currency().updateCurrencies(...)`. Stock value `["EUR", "USD"]`.
2. The product/charge factories stamp every seeded product with a currency constant —
   `LoanProductsRequestFactory.CURRENCY_CODE = "EUR"` (used by loan products and, by static
   import, working-capital products), `SavingsProductRequestFactory.DEFAULT_SAVINGS_PRODUCT_CURRENCY_CODE
   = "EUR"`, `WorkingCapitalChargeRequestFactory.DEFAULT_CURRENCY_CODE = "EUR"`, and
   `ChargeGlobalInitializerStep.CURRENCY_CODE = CurrencyOptions.EUR.value`.

The Gherkin phrases `"{string} EUR transaction amount"` are **labels**, not configuration, and are
left untouched.

## The edit

Pure EUR→MNT substitution across the seeding path (5 files, disposable copy only). Full diff:
`.softhouse/capture/tierd-feasibility/uc6-mnt/currency-seed-mnt.diff`
(sha256 `1facd283a516f7fc26ddde324119e842baae5bd5ab73979b645a5dabc0a4b771`).

| file | before | after |
| --- | --- | --- |
| `CurrencyGlobalInitializerStep.java` | `Arrays.asList("EUR", "USD")` | `Arrays.asList("MNT", "USD")` |
| `LoanProductsRequestFactory.java` | `CURRENCY_CODE = "EUR"` | `CURRENCY_CODE = "MNT"` |
| `SavingsProductRequestFactory.java` | `DEFAULT_SAVINGS_PRODUCT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `WorkingCapitalChargeRequestFactory.java` | `DEFAULT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `ChargeGlobalInitializerStep.java` | `CURRENCY_CODE = CurrencyOptions.EUR.value` | `CURRENCY_CODE = "MNT"` |

The substitution keeps the seeding path internally consistent. Fineract refuses a product/charge
currency mismatch ("Charge and Loan Product must have the same currency.",
`LoanProductWritePlatformServiceJpaRepositoryImpl.assembleListOfProductCharges`), so loan and
savings products, their charges, and the active-currency list all move together. USD stays active
because the USD product variant (`CURRENCY_CODE_USD`) and USD working-capital variant remain.

## Why it should be a no-op arithmetically

Both currencies carry 2 minor digits, so integer minor-unit arithmetic is identical. The oracle's
disbursement/schedule values are expected to be byte-identical to the EUR replay except for the
currency code itself. The replay in step 2 of the task must show this rather than assume it.

## Open questions (this run)

- Q2: do the UC6 scenarios still PASS in MNT?
- Q3: do the extracted read-backs carry `MNT` as their currency?
- Q4: does one of the pilot's three candidates now pass admission and `loan-go`?
- Q5: what is promoted, if anything?

Answers land in `.softhouse/capture/tierd-feasibility/uc6-mnt/OWNER.md` and a closing finding.
