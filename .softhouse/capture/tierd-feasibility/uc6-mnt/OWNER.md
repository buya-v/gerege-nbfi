# uc6-mnt — UC6 replay read-backs in the tenant's own currency (MNT)

Owner run: `feat/OHTIERD4bm` (OH-TIERD4-BM), worktree `/Users/buv/oh-gerege-tierd4`.

## Why this capture exists

The first Tier D replay (`.softhouse/findings/F-2026-09-11-tierd-feasibility.md`) replayed UC6
against the throwaway oracle with the runner's stock seeded currency **EUR**, then offered the
read-backs to the `loan` seams. The pilot
(`.softhouse/findings/F-2026-09-11-tierd-pilot-loan-refusal.md`) showed every vector was refused
at admission by the `tenant_params` equality rule: the read-backs were captured under EUR, but
the loan pin (`.softhouse/PIN-loan.json`) is **MNT**.

MNT and EUR both have two ISO 4217 minor digits (`MNT` = 496, `EUR` = 978), so the scenario
arithmetic — and therefore the oracle's own numbers — does not change when the currency code
changes. Re-seeding the runner to MNT replays the *same* scenarios and produces the oracle's own
responses **in the tenant's currency**, which is an observation the loan seams can admit, not a
synthesis. Nothing was re-computed or converted.

## The edit (disposable copy only)

Made **only** in `/Users/buv/fineract-tierd` (the disposable clone). Never in the pinned
`/Users/buv/fineract`. The recorded diff is:

- `currency-seed-mnt.diff` — `git diff --no-color -- fineract-e2e-tests-core fineract-e2e-tests-runner`
- sha256 `1facd283a516f7fc26ddde324119e842baae5bd5ab73979b645a5dabc0a4b771`

The currency is fixed in two places: the active-currency seed (runner initializer) and the
product-factory constants that stamp every seeded product and charge. The step phrases such as
`{string} EUR transaction amount` are **labels**, not configuration, and are untouched.

| file | before | after |
| --- | --- | --- |
| `fineract-e2e-tests-runner/.../CurrencyGlobalInitializerStep.java` | `Arrays.asList("EUR", "USD")` | `Arrays.asList("MNT", "USD")` |
| `fineract-e2e-tests-core/.../LoanProductsRequestFactory.java` | `CURRENCY_CODE = "EUR"` | `CURRENCY_CODE = "MNT"` |
| `fineract-e2e-tests-core/.../SavingsProductRequestFactory.java` | `DEFAULT_SAVINGS_PRODUCT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `fineract-e2e-tests-core/.../WorkingCapitalChargeRequestFactory.java` | `DEFAULT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `fineract-e2e-tests-runner/.../ChargeGlobalInitializerStep.java` | `CURRENCY_CODE = CurrencyOptions.EUR.value` | `CURRENCY_CODE = "MNT"` |

EUR→MNT is a pure substitution across the seeding path: every product and charge that was EUR is
now MNT, exactly as they were all EUR together before. USD variants (`CURRENCY_CODE_USD`, the
second active currency) are unchanged. The unused `CurrencyOptions` import in
`ChargeGlobalInitializerStep` was removed with it, because the enum has no `MNT` member.

## Throwaway

- tenant `tierd`, image `fineract:latest` = `e596339626bf…`, timezone `Asia/Ulaanbaatar`,
  rounding mode `4` (HALF_UP) — seeded by `throwaway/docker-compose.tierd.yml`.
- standing tenants `gerege`/`default` untouched; `preflight.sh` wrote
  `throwaway/out/STANDING-baseline.txt` before start and `down.sh` compared to it.

## Status

- [ ] Replay UC6 scenarios in MNT (per-scenario pass/fail recorded here)
- [ ] Extract loan 1 / loan 10 with `bin/extract.py` into this directory
- [ ] Read-back currencies checked = MNT
