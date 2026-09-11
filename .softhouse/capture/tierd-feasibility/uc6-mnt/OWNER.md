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

## Replay result — 11/11 scenarios PASS in MNT

`LoanUpdateApprovedAmount.feature` replayed end to end against the MNT-seeded throwaway
(`fineract:latest` = `e596339626bf…`, tenant `tierd`). Full Gradle output:
`replay-uc6-mnt.log`. Feign capture: `feign-uc6-mnt.log` (146,276,167 bytes, 38,469 lines;
kept in the disposable copy, not committed for size). Summary line:
**`11 scenarios (11 passed)` / `199 steps (199 passed)`**.

| # | scenario | feature line | result |
| --- | --- | --- | --- |
| 1 | UC1 — update approved amount for progressive loan | 5 | PASS |
| 2 | UC3 — after undo disbursement, single disb progressive | 19 | PASS |
| 3 | UC4 — over-applied, percentage, multidisbursal | 36 | PASS |
| 4 | UC8_1 — over-applied + capitalized income, percentage | 55 | PASS |
| 5 | UC8_2 — capitalized income, progressive | 75 | PASS |
| 6 | UC8_3 — capitalized income, multidisbursal | 92 | PASS |
| 7 | UC5_1 — before disbursement, single disb cumulative | 109 | PASS |
| 8 | UC5_2 — before disbursement, single disb progressive | 123 | PASS |
| 9 | **UC6** — approved-amount change, multidisbursal, no tranches | 137 | PASS |
| 10 | UC7_1 — approved-amount change with lower value, two tranches | 165 | PASS |
| 11 | UC7_2 — approved-amount change with greater value, two tranches | 204 | PASS |

Passing is the oracle's own check: the runner asserts the response values in the `.feature`
file, so MNT did not change a single scenario's arithmetic (as expected: MNT and EUR both
have 2 minor digits).

## Extraction — `bin/extract.py` on the MNT Feign log

```
python3 bin/extract.py <disposable>/fineract-e2e-tests-runner/build/capture/feign-uc6-mnt.log --out uc6-mnt
exchanges: 1463 total, 278 loan, 1185 skipped
loans: 11; files: 343; kept body bytes: 2835261
```

Only **loan 1** (product 50, client 1, 1000.00, 6 periods, 7%) and **loan 10** (product 96,
client 10, three tranches 300/200/500) are committed here — 65 files, matching the pilot's
two target loans. The other 278 loan files are reproducible from the log and were not
committed. `manifest-uc6-loans-1-10.json` carries the source line, bytes and sha256 of every
committed body; `summary-uc6-loans-1-10.json` carries the per-loan counts and the full-run
totals.

## Read-back currency check — every committed read-back is MNT

Every file whose JSON contains a currency object resolves to `code = "MNT"`
(`decimalPlaces = 2`, name "Mongolian Tugrik"). The committed bodies with currency:
`loan-1-detail-*` (13 reads) and `loan-10-detail-*` (43 reads) plus the two
`*-transactions-template-*` payloads. Request/command bodies carry no currency field (the
loan's currency comes from the seeded product). No `EUR` token appears anywhere in the
capture (see `currency-seed-mnt.diff`). `loan-1-create-request.json` has no currency member;
the created loan's currency is the product's MNT.

## Promotion — one pilot candidate now ADMITS and passes `loan-go`

The pilot's first candidate (`LN-TD-L10-loan-1-pending-amortizes-to-zero`, seam
`loan-schedule-amortization`) was re-transcribed from the MNT read-back
`loan-1-detail-associations-all-1.json` (externalId `fe61fc1a-87f2-4180-ad97-6116ed335c36`,
sha256 `cc82ab652b8c2648c41a0d1771f5f84d19d1d113e4b97bdd8f5ed5952ad233f7`) with
`tenant_params.currency = "MNT"` — the observed value, not an inheritance. It is committed at
`.softhouse/vectors/loan/LN-TD-L10-loan-1-pending-amortizes-to-zero.json`.

```
$ go test -count=1 -run Committed ./internal/apps/loan/conformance/     # ok
$ go run ./internal/apps/loan/conformance/cmd/conformance -root ..
VERDICT: PASS (exit 0)
vectors_loaded=32 parity_pass=32 parity_fail=0 refused=0 inadmissible=0 harness_error=0
```

The other two pilot candidates (`...-schedule-interest-period-1`, `...-disbursement-net`) were
**not** re-transcribed: the pilot measured both as noticed by **zero** drives, so they would be
inert additions. Only the amortization candidate, which the pilot measured as adding a second
kill to three drives, was promoted.

## Isolation

`preflight.sh` wrote `throwaway/out/STANDING-baseline.txt` in THIS worktree before the
throwaway started; `down.sh` compared against it. Standing tenants `gerege`/`default`
untouched. Every `tierd-*` container removed. The build container ran with
`--network container:tierd-oracle-app`, so the Feign client's `https://localhost:8443`
reached the **throwaway** (shared netns), never the host's standing oracle.

## Status

- [x] Replay UC6 scenarios in MNT (per-scenario pass/fail recorded above)
- [x] Extract loan 1 / loan 10 with `bin/extract.py` into this directory
- [x] Read-back currencies checked = MNT
- [x] Pilot candidate re-transcribed from the MNT capture; admitted and passing under `loan-go`
