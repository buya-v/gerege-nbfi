# F-2026-09-11 — Tier D replay re-seeded in MNT: UC6 passes, read-backs are MNT, one pilot vector ADMITTED

**Status: ANSWERED.** `OH-TIERD4-BM`, worktree `/Users/buv/oh-gerege-tierd4`, branch
`feat/OHTIERD4bm`. The driver's 2026-09-11 currency decision is carried out end to end: the
disposable oracle is re-seeded to MNT, UC6 replays green, the read-backs come out MNT, and the
pilot's lead candidate is admitted by the loan tenant pin and passes `loan-go`. **One vector
promoted**; `.softhouse/vectors/loan/` goes 31 → 32.

## 1. The currency edit — smallest possible, disposable copy only

The runner does **not** fix the currency in `fineract-test-application.properties`. It is fixed
by the active-currency initializer and by the product/charge request factories that stamp every
seeded product. The step phrases such as `{string} EUR transaction amount` are Gherkin **labels**,
not configuration, and are untouched.

| file (in `/Users/buv/fineract-tierd` only) | before | after |
| --- | --- | --- |
| `fineract-e2e-tests-runner/.../CurrencyGlobalInitializerStep.java` | `Arrays.asList("EUR", "USD")` | `Arrays.asList("MNT", "USD")` |
| `fineract-e2e-tests-core/.../LoanProductsRequestFactory.java` | `CURRENCY_CODE = "EUR"` | `CURRENCY_CODE = "MNT"` |
| `fineract-e2e-tests-core/.../SavingsProductRequestFactory.java` | `DEFAULT_SAVINGS_PRODUCT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `fineract-e2e-tests-core/.../WorkingCapitalChargeRequestFactory.java` | `DEFAULT_CURRENCY_CODE = "EUR"` | `... = "MNT"` |
| `fineract-e2e-tests-runner/.../ChargeGlobalInitializerStep.java` | `CURRENCY_CODE = CurrencyOptions.EUR.value` | `CURRENCY_CODE = "MNT"` |

Recorded diff: `.softhouse/capture/tierd-feasibility/uc6-mnt/currency-seed-mnt.diff`. Pinned
`/Users/buv/fineract` untouched. MNT and EUR both have 2 ISO 4217 minor digits (496 / 978), so
the arithmetic — and every amount — is unchanged; only the code emitted by the oracle changes.

## 2. Replay — 11/11 UC6 scenarios PASS in MNT

Rebuilt only the two modules the edit touches (JDK container over the disposable copy,
`--no-daemon`, bounded heap, named Gradle cache), brought up the throwaway (tenant `tierd`, image
`fineract:latest` = `e596339626bf…`, `Asia/Ulaanbaatar`, rounding mode 4), and replayed
`LoanUpdateApprovedAmount.feature` with the Feign capture on.

```
11 scenarios (11 passed)
199 steps (199 passed)
```

| # | scenario | feature line | result |
| --- | --- | --- | --- |
| 1 | UC1 | 5 | PASS |
| 2 | UC3 | 19 | PASS |
| 3 | UC4 | 36 | PASS |
| 4 | UC8_1 | 55 | PASS |
| 5 | UC8_2 | 75 | PASS |
| 6 | UC8_3 | 92 | PASS |
| 7 | UC5_1 | 109 | PASS |
| 8 | UC5_2 | 123 | PASS |
| 9 | **UC6** | 137 | PASS |
| 10 | UC7_1 | 165 | PASS |
| 11 | UC7_2 | 204 | PASS |

Full log: `.softhouse/capture/tierd-feasibility/uc6-mnt/replay-uc6-mnt.log`. **No scenario failed**,
so there is no failed-step finding to record. The oracle's own assertions reproduced every
`.feature` expected value under MNT.

## 3. Extraction — loan 1 / loan 10, all read-backs MNT

`bin/extract.py` over `feign-uc6-mnt.log` (146,276,167 B, 38,469 lines): 1,463 exchanges, 278
loan-keyed, **11 loans / 343 files / 2,835,261 kept body bytes**. Committed under
`.softhouse/capture/tierd-feasibility/uc6-mnt/` for the pilot's two target loans only:

* **loan 1** — product 50, client 1, 1000.00, 6 periods, 7%.
* **loan 10** — product 96, client 10, three tranches 300/200/500.

65 files + a filtered manifest (`manifest-uc6-loans-1-10.json`, with source line, bytes and
sha256 per body) + a filtered summary. Every committed body that carries a currency object
resolves to `code = "MNT"` (`decimalPlaces 2`); the capture contains no EUR token at all. So
the driver's premise holds: replaying the runner re-seeded to MNT makes the oracle emit
**observations in MNT**, not synthesis.

## 4. Promotion — the lead pilot candidate now ADMITS and `loan-go` passes

The pilot (`F-2026-09-11-tierd-pilot-loan-refusal.md`) offered three candidates, all refused
because their `tenant_params.currency` was EUR. I re-transcribed **one**, the lead candidate
`LN-TD-L10-loan-1-pending-amortizes-to-zero` (seam `loan-schedule-amortization`), from the MNT
read-back with `tenant_params.currency = "MNT"` — the **observed** value, read from the capture,
not inherited from the gerege vectors:

* capture: `.softhouse/capture/tierd-feasibility/uc6-mnt/loan-1-detail-associations-all-1.json`
* sha256 `cc82ab652b8c2648c41a0d1771f5f84d19d1d113e4b97bdd8f5ed5952ad233f7`
* `capture_case_id` `fe61fc1a-87f2-4180-ad97-6116ed335c36` (the loan's observed `externalId`)
* cells: `principalDisbursed 1000.0 → "100000"`; `principalDue[1..6]`
  `164.26,165.21,166.18,167.15,168.12,169.08 → ["16426","16521","16618","16715","16812","16908"]`;
  sum `"100000"` == disbursed; final outstanding `0.0 → "0"`.

Result:

```
$ go test -count=1 -run Committed ./internal/apps/loan/conformance/      # ok
$ go run ./internal/apps/loan/conformance/cmd/conformance -root ..
VERDICT: PASS (exit 0)
vectors_loaded=32 parity_pass=32 parity_fail=0 refused=0 inadmissible=0 harness_error=0
graded_cells=214 money_cells=74 invariant_violations=0
```

Committed as `.softhouse/vectors/loan/LN-TD-L10-loan-1-pending-amortizes-to-zero.json`.

**The other two candidates were deliberately not promoted.** The pilot's counterfactual measured
`...-schedule-interest-period-1` and `...-disbursement-net` as noticed by **zero drives**; promoting
them would add inert vectors. The amortization candidate was the pilot's only candidate that
moves a drive (it adds a second kill to three already-killed amortization drives), so it is the
one worth an MNT-backed vector. Choosing it is the smallest useful promotion.

## 5. Isolation — CLEAN, file named

`preflight.sh` wrote `throwaway/out/STANDING-baseline.txt` in **this** worktree before the
throwaway started (12 counters over `fineract-db-1` and `gerege-oracle-db`). After the replay,
`down.sh` compared against that exact file and reported **every counter `== baseline`**
(`teardown-isolation.txt`). Standing health 200. All `tierd-*` containers, the `tierd-oracle`
network, and the leftover unused `tierd-gradle` volume are gone. The build container ran with
`--network container:tierd-oracle-app`, so the Feign client's `https://localhost:8443` reached
the **throwaway** via the shared netns — never the host's standing oracle at 8443.

## 6. Controls and the bar

* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit-2 line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
  completed and the bar is refused by that recorded decision`. Ledger findings == baseline; no
  `HARD guard failed`.
* Loan harness: 32/32 parity pass, 0 refused, 0 inadmissible.
* `.softhouse/guards/` (baseline 8 pairs), `.softhouse/conformance.sh`, `.softhouse/maps/`
  untouched. PostgreSQL only; Oracle Database nowhere. Integer minor units throughout; no float
  (the `nofloat` scan reports violations=0).

## 7. What this establishes

The pilot's blocker was a **currency** mismatch, not a mapping defect. Re-seeding the e2e runner
to MNT removes that mismatch at the source: the same scenario, the same read-back shape, the
same arithmetic, but the oracle emits MNT — and the loan pin admits it. The mapped `LN-L10`
cells survive admission unchanged, which independently confirms the THIRD PASS's Q4 mapping on
the money cells. The two "zero-drive" candidates are still correctly left unpromoted; currency
was necessary but not sufficient to make them useful.
