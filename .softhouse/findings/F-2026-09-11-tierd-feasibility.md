# F-2026-09-11 — Tier D feasibility: FIRST ATTEMPT, partial (salvaged by the driver)

**Status: OPEN — question 1 partly answered, questions 2-5 unanswered.** `OH-TIERD-BG` stopped at
257 events without committing; the driver salvaged its rig and wrote this record.

## What was learned
1. **The e2e runner needs Fineract's Feign client SDK built from source.** `fineract-e2e-tests-core`
   depends on `fineract-client-feign`, generated from the OpenAPI spec and compiled with Gradle — the
   run started `./gradlew` on the PINNED checkout (`/Users/buv/fineract`). The build ran for minutes and
   **failed: "Gradle build daemon disappeared unexpectedly"** — consistent with memory pressure on a
   16 GB host that was also running the standing oracle, another agent run and unrelated containers.
2. **The build wrote gitignored output into the pinned checkout** (`fineract-client-feign/build`,
   `fineract-e2e-tests-core/build`). HEAD stayed `426a23544` and `git status --porcelain` stayed empty,
   so no capture rig's precondition broke — but the checkout is read-only by rule. **The driver deleted
   both directories** (they were newer than the brief; older gitignored build dirs were left alone).
3. **The run wrote a throwaway rig** (`.softhouse/capture/tierd-feasibility/throwaway/`): compose file,
   env, preflight, isolation guard, teardown — copied from T305's, tenant named `tierd`, port 8444, no
   published DB port. **It was never started**: no container was created (driver checked `docker ps -a`).
4. The run's last action was an unbounded `find /Users/buv …`, which never returned.

## What the next attempt must do differently
* Build the SDK in a DISPOSABLE COPY of the pinned checkout (e.g. `cp -a` or a `git worktree` of
  `426a23544` outside `/Users/buv/fineract`), never in the pinned tree.
* Build only the two modules needed, `--no-daemon`, with a bounded JVM heap, and nothing else heavy running.
* Never run `find` over the home directory.

---

## SECOND ATTEMPT (OH-TIERD2-BH) — the replay WORKS; salvaged by the driver

`OH-TIERD2-BH` did not finish its write-up: at 430 events its model calls began failing with
`DeepseekException "Insufficient Balance"` (the DeepSeek account reached −0.11 USD; the fallback
did not engage because the provider answers a 400, not a retriable error). The driver recorded
what its evidence establishes. **Questions 1–3 are answered positively; 4 and 5 are not.**

1. **Harness — yes, on this host, with a recipe.** The Feign client SDK and the runner build in a
   JDK container (`eclipse-temurin:21-jdk`) over a disposable `cp` copy of the pinned checkout
   (`/Users/buv/fineract-tierd`, not a git worktree; the pinned tree is untouched), with
   `--no-daemon --max-workers=1`, a bounded heap (`-Xmx3g -XX:+UseSerialGC`) and a named Gradle
   cache volume. Six builds failed first (one in generated `StandingInstructionsApi.java`
   with missing symbols) before `BUILD SUCCESSFUL`.
2. **Replay — yes, and fast.** Against the throwaway (same image `e596339626bf`, tenant `tierd`,
   `Asia/Ulaanbaatar`, rounding mode 4), **12 scenario executions from
   `LoanUpdateApprovedAmount.feature` (UC1, UC3, UC5_1, UC5_2, UC6 ×2, UC7_1, UC7_2, UC8_2, UC8_3 and
   two over-applied variants) all PASSED — every step — in 0.5–1.5 s each** (allure results in the
   disposable copy). Passing means the oracle, replayed, reproduced the `.feature` file's own
   expected values.
3. **Capture — yes, but coarse.** A Feign debug hook (`-Dfineract.feign.debug=true`) wrote every
   request and response: `feign-s1.log` 243 MB (1,809 exchanges, 24 schedule read-backs) and
   `feign-uc6.log` 147 MB. Most of the volume is the runner's global initializer seeding the
   tenant. A usable pipeline must extract the per-scenario loan read-backs from that stream.
4. **Mapping — NOT ANSWERED.** Whether those read-backs fit the `loanschedule`/`loan` vector shapes
   was being examined when the run died.
5. **Scale and cost — partly.** Per-scenario replay is ~1 s after a one-off initializer; the cost is
   the one-off SDK build and the log extraction, not the replay.

**Isolation, driver-verified after the run died:** tenant `gerege`'s last writes are 07:05:39Z
(OH-CHGCAP-BD's final repayment and waive, commands 234–235), before Tier D began; `default` has
had no write since 2026-09-03. The rig's own teardown reported "THE STANDING ORACLE MOVED" on every
counter — a false alarm: its baseline file lived in the first attempt's deleted worktree, so it
compared against empty values. Every `tierd-*` container was removed. The pinned checkout was
rebuilt into once more by the STALE first run after the first cleanup; the driver removed that
output again (HEAD `426a23544`, porcelain empty throughout).

**Recommendation (driver):** Tier D is feasible. The next run — after the model credit is restored —
answers question 4 from the existing `feign-*.log` evidence without re-running anything: extract one
scenario's loan read-back and map it onto a `loanschedule` vector, or say which cells cannot map.
The disposable copy (997 MB) is kept for it.

---

## THIRD PASS (OH-TIERD3-BJ) — question 4 mapped cell-by-cell, question 5 costed

**Status:** Q1-Q3 answered yes (pass 2). Q4 answered: **no, the replayed read-backs do not map onto the
`loanschedule` generator vectors; yes, they map onto the `loan` single-cell read-back vectors, with
transforms.** Q5 answered with measured bytes. **No vector promoted** — see the driver decision at the
end.

### 0. Evidence integrity: the salvaged extraction was partly fabricated

Before mapping, I re-extracted every captured body direct from `feign-uc6.log` by source line and
byte-compared it. Four loan-10 request files held **loan 1's** bodies (a file-order bug in the salvaged
extraction):

| file | was | now |
|---|---|---|
| `loan-10-create-request.json` | loan 1: 590 B, productId 50, clientId 1 | loan 10: 780 B, productId 96, clientId 10, 3 tranches 300/200/500, verified against the `POST /loans` response `resourceId: 10` |
| `loan-10-disburse-request-2.json` | loan 1's 300 | loan 10's 200 (02 Jan) |
| `loan-10-disburse-request-3.json` | loan 1's 300 | loan 10's 700, **HTTP 403 rejected** (03 Jan, over the 1000 approved) |
| `loan-10-disburse-request-4.json` | loan 1's 300 | loan 10's 500 (03 Jan) |

`loan-10-detail-all.json` and all loan-1 files were verified byte-identical. The whole manifest
(source line, bytes, sha256 per file) is recorded in
`.softhouse/capture/tierd-feasibility/uc6/OWNER.md`. Committed as `c58d98f4`.

### 1. What was captured

`feign-uc6.log` is the loan-creation/update feature replay: **11 loans** created and read back (12
passed Allure executions). Relevant loans by `resourceId`:

| loan | product | client | principal (major) | n | rate |
|---|---|---|---|---|---|
| 1 | 50 `LP2_ADV_PYMNT_..._PMT_ALLOC_1` | 1 | 1000.00 | 6 | 7% |
| 10 | 96 `LP2_ADV_PYMNT_..._MULTIDISBURSE_EXPECT_TRANCHE` | 10 | 1000.00 (300+200+500) | 6 | 7% |
| 11 | 96 | 11 | 1200.00 | 6 | 7% |

Tenant `tierd` (throwaway, port 8444) on the pinned commit `426a23544`; timezone
`Asia/Ulaanbaatar`; declared rounding mode `4` (HALF_UP); **currency EUR** (`decimalPlaces` 2) — not
gerege's MNT. Two snapshots of loan 1 matter: **pending approval** (`associations=all`, line 22145),
which carries period-1 interest 5.83 and total interest 20.52; and **closed**
(`associations=repaymentSchedule`, line 22527), where the same-day 1000.00 repayment
(`loan-1-repayment-request.json`) recalculated interest to 0.00. The closed snapshot is the wrong one
to grade an interest cell.

### 2. Q4 — cell-by-cell mapping

#### 2a. Target A: the `loanschedule` parity vectors (`path_a_embeddable`)

The nearest vector is **`P-00-baseline-6x7pct`**, not P-03: P-00 is 6 monthly repayments at 7% p.a.,
DECLINING_BALANCE, FIXED_30_360, one disbursement on the schedule start — exactly UC6 loan 1's shape.
P-03 differs only in disbursing on a repayment **due** date, which UC6 loan 1 does not reproduce
(disbursement 2025-01-01 == `schedule_start_date`, i.e. on the start, which is also every repayment's
`from_date`).

| P-00 request cell | UC6 loan-1 read-back source | verdict |
|---|---|---|
| `time_zone` | not a field of the loan read model | **cannot map** — tenant config |
| `currency.code` | `currency.code` = EUR | maps directly (value differs: EUR not USD) |
| `currency.minor_unit_digits` | `currency.decimalPlaces` = 2 | direct |
| `rounding.significant_digits` | absent | **cannot map** — tenant config |
| `rounding.rate_factor_scale` | absent | **cannot map** — tenant config |
| `rounding.mode` | absent (declared HALF_UP in the rig) | **cannot map** — not in the payload |
| `schedule_start_date` | `repaymentSchedule.periods[0].dueDate` = 2025-01-01 | transform (array -> object) |
| `disbursements[0].date` | `periods[0].dueDate` (loan 1) / `disbursementDetails[].expectedDisbursementDate` (loan 10) | transform |
| `disbursements[0].amount_minor` | `periods[0].principalDisbursed` 1000.00 -> `"100000"` | transform major->minor |
| `number_of_repayments` | `numberOfRepayments` = 6 | direct |
| `repayment_every` | `repaymentEvery` = 1 | direct |
| `repayment_frequency_unit` | `repaymentFrequencyType` (`...periodFrequencyType.months`) | transform enum->string `"MONTHS"` |
| `annual_nominal_interest_rate` | `interestRatePerPeriod` 7.0 + `interestRateFrequencyType` per-year | transform -> `{7, 100}` |
| `interest_method` | `interestType.code` `...declining.balance` | transform -> `"DECLINING_BALANCE"` |
| `day_count` | `daysInYearType` 360 + `daysInMonthType` 30 + `interestCalculationPeriodType` daily | transform -> `"FIXED_30_360"` |
| `down_payment_percentage` | `enableDownPayment` = false | weak transform (only asserts 0) |
| `installment_rounding_multiple_minor` | absent (product-level) | **cannot map** |

| P-00 `expect.periods[]` | UC6 loan-1 pending schedule row | verdict |
|---|---|---|
| row `kind` = DISBURSEMENT/REPAYMENT | not labelled; only inferable (disbursement row has `principalDisbursed`, no `period`, no `fromDate`) | **cannot map** — the read model omits `kind` |
| `installment_number` | `period` present on repayment rows, absent (null) on the disbursement row | partial — the generator's 0 must be *asserted*, not observed |
| `from_date` | absent on the disbursement row, present on repayments | **cannot map** for row 0 |
| `due_date` | `dueDate` | direct |
| `principal_minor` | `principalDue` 164.26 -> `"16426"`, ... | transform major->minor |
| `interest_minor` | `interestDue` 5.83 -> `"583"`, ... | transform major->minor |
| `outstanding_principal_minor` | `principalLoanBalanceOutstanding` | transform major->minor |
| `observed_total_due_minor` | absent | **cannot map** |

**Verdict.** The read-back reproduces the generator's *shape and money*: UC6 loan 1 is the P-00 shape
at 1000.00 rather than 100.00, and its 6 principal components in integer minor units are
`[16426,16521,16618,16715,16812,16908]`, summing to `100000` and ending at `0`. (Note it is not a
clean 10x of P-00: per-period rounding on the actual balance means the components differ slightly
from 10x P-00's, which is the point of a parity vector — the money is oracle-specific.) But **7 of the
17 P-00 request cells — every rounding/tenant cell and the installment-rounding multiple — are simply
not in the REST read model**, and the row labels (`kind`, row-0 `from_date`, `observed_total_due_minor`)
are missing too. More decisively, P-00's seam is `path_a_embeddable`: it grades the in-process schedule
**generator**, and **no HTTP route exposes that generator** — the read-back is the *persisted read
model* at a different seam. So the read-back cannot be a readiness source for the `loanschedule`
vectors as a whole: it can corroborate their money, but it cannot supply the request cells they grade.

#### 2b. Target B: the `loan` single-cell read-back vectors

These vectors are themselves transcriptions of a REST read-back (under gerege/MNT), so the direction of
provenance is right. Mapping UC6 loan 1 pending:

| vector | vector cell | UC6 loan-1 value (minor units) | verdict |
|---|---|---|---|
| `LN-L06-schedule-interest-period-1` | `request.schedule.principal_minor` | `"100000"` (principal 1000.00) | **direct** |
| | `request.schedule.rate_per_annum_pct` | `7` | **direct** |
| | `request.schedule.days_in_year` / `days_in_month` | `360` / `30` | **direct** |
| | `expect.interest_minor` | `"583"` (periods[1] interestDue 5.83) | **direct** |
| `LN-L06-disbursement-net` | `request.disburse.approved_principal_minor` | `"100000"` | **direct** |
| | `request.disburse.charges_due_at_disbursement_minor` | `"0"` (`feeChargesAtDisbursementCharged` 0.0) | **direct** |
| | `expect.net_disbursal_minor` | `"100000"` | **direct** |
| `LN-L10-schedule-principal-amortizes-to-zero` | `request.principal_disbursed_minor` | `"100000"` (periods[0] principalDisbursed) | **direct** |
| | `request.principal_components_minor[]` | `[16426,16521,16618,16715,16812,16908]` | **direct** (major->minor per component) |
| | `expect.principal_sum_minor` | `"100000"` | **direct** |
| | `expect.final_principal_balance_minor` | `"0"` | **direct** |

Every cell maps, and the `LN-L10` invariant holds exactly (the components sum to the disbursed
principal and the final balance is zero). The `tenant_params` block does **not** map: UC6 is EUR, not
MNT, and the `rounding_ordinal 4` is a *declared* rig setting, not an observed one. That block, and
`provenance.capture_ref` / `capture_sha256` / `capture_case_id`, are exactly the fields the driver
decision (sec. 4) must set — they cannot be inherited from gerege.

Loan 10 (multi-tranche) also maps to `LN-L10` (its components sum to `100000` and end at `0`) but
**not** to `LN-L06-disbursement-net`: a multi-tranche loan's top-level `netDisbursalAmount` (500.00 at
the read) does not represent a single disbursement, so that vector's single-disbursement premise does
not hold.

**Q4 answer:** *No* for the `loanschedule` context — the replay read-back is the persisted read model,
the vectors grade the embeddable generator, and most request cells do not exist in the read-back.
*Yes, with transforms* for the `loan` context — the `LN-L06` and `LN-L10` single-cell shapes transcribe
directly from UC6 loan 1 once money is taken to integer minor units and enums are normalised.

### 3. Q5 — scale and cost, measured

Feign debug log counted with a streaming regex parser over the raw files (no whole log loaded):

| | `feign-uc6.log` | `feign-s1.log` |
|---|---|---|
| file bytes | 146,653,987 (146.7 MB) | 243,112,578 (243.1 MB) |
| exchanges (`<--- HTTP`) | 1,444 | 603 |
| `POST /loans` creates | 11 | 1 |
| loan commands (approve/disburse/repay) | 34 | 3 |
| `GET ...associations=repaymentSchedule` | **13** | **3** |
| schedule read-back bytes | 211,188 | 48,679 |
| other loan read-backs (`all`/`transactions`/`collection`) | 178 / 2,544,692 B | 16 / 235,719 B |
| non-loan (global initializer seeding) | 1,208 / 137,112,246 B (**93.5%**) | 580 / 240,004,950 B (**98.7%**) |
| usable loan signal (creates+commands+reads) | 2,787,490 B (**1.9%**) | 312,051 B (0.13%) |

**Correction to pass 2.** The pass-2 figure "`feign-s1.log` 243 MB (1,809 exchanges, 24 schedule
read-backs)" is **not supported by the log on disk**: the file has 603 exchanges (the raw `--->` count
of 1,206 doubles because Feign prints both the request URL arrow and a `---> END HTTP` line), and only
**3** GETs carry `associations=repaymentSchedule` (another 6 carry `associations=all`). The 1,809/24
numbers describe a different or earlier run. Raw evidence, not the brief, governs: 3 and 13.

**Bytes per scenario.** uc6's 12 executions share one 146.7 MB log, ~12.2 MB/execution of raw log. But
~93.5% of that is one-off seeding; the marginal loan payload is tiny: the 13 schedule read-backs total
211 KB (~16 KB each), and all loan traffic 2.79 MB, i.e. **~0.23 MB per execution**. Schedule evidence
alone is ~0.14% of log bytes.

**Extraction effort.** The parser is small: a ~60-line Python/awk stream that regexes the Feign framing
(`[Api#method] ---> METHOD url`; bodies terminated by `---> END HTTP (n-byte body)` / `<--- END HTTP`),
`json.loads` each body to validate it, and writes one file per body. It runs in **under one second**
across both logs (390 MB). The expensive part is not I/O, it is **attribution** — keying an exchange to
its scenario and loan. The salvaged run keyed by file order and got four bodies wrong; the fix must key
on the `resourceId` returned by each `POST /loans` and follow that loan's command chain.

**What a bulk extractor would have to do:**
1. **Stream** — the two logs are 390 MB; decode incrementally, never load a file.
2. **Parse Feign framing robustly** — request URL arrow, method, and body on prefixed lines; request
   and response each end with an `END HTTP` marker.
3. **Attribute by id, not position** — take `resourceId` from each create response, then follow
   approve -> disburse(s) -> repay and the `GET /loans/{id}?associations=...` reads, tagging each body
   with the true loan id and the loan status at read time.
4. **Filter by URL prefix** — 93-99% of bytes are the global initializer; skip non-`/loans` traffic
   without materialising bodies.
5. **Snapshot by state** — a schedule read-back exists in several states (pending / active / closed);
   only one carries the discriminating cell.
6. **Record provenance per body** — source line, byte length, sha256, and id/status, so a
   mis-attributed body cannot survive review.

**Recommendation: a hand-picked subset plus a thin reusable parser — not a bulk pipeline, but not
"not worth it" either.** The useful schedule evidence is ~0.4 MB across these two runs; even a perfect
pipeline would hand over the same handful of snapshots, because the hard parts (enum normalisation,
seam eligibility, tenant provenance) are judgement, not volume. A pipeline costs more to build and
maintain than the extraction it automates, and its one real value — id-keyed attribution — is a
~60-line script. Build that streaming parser and id-keyed attribution once as a one-file utility, use
it to hand-pick a small set of vectors per run, and revisit a pipeline only if Tier D grows to hundreds
of executions where per-run parsing is the bottleneck.

### 4. Driver decision required before any promotion

No vector is promoted. Provenance from a throwaway tenant needs a driver decision:

1. **Are throwaway-tenant captures admissible provenance at all?** The bytes come from the same pinned
   oracle (`426a23544`) but a different tenant (`tierd`), seed data, and currency (EUR). Admitting them
   widens what counts as a capture; refusing them keeps every vector traceable to `gerege`.
2. **If admitted, what tenant/currency/rounding does the vector declare?** Observed: EUR, minor units
   2, timezone `Asia/Ulaanbaatar`, rounding mode `4` (HALF_UP, declared not observed). These must **not**
   silently inherit the gerege vectors' MNT/`HALF_UP` block.
3. **What `capture_ref` is authoritative?** The current location is
   `.softhouse/capture/tierd-feasibility/uc6/`, whose OWNER.md states it is NOT tenant `gerege`. Either
   that path is blessed as a capture_ref, or the decision is that throwaway captures may only
   *corroborate* (a finding footnote) and never back a vector.

Until (1)-(3) are recorded, the UC6 read-back answers Q4 and informs the mapping, but it cannot promote
`LN-L06-schedule-interest-period-1`, `LN-L06-disbursement-net`, or
`LN-L10-schedule-principal-amortizes-to-zero` from these values.

