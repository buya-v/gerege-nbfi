# T22 — Independent audit of the Path B captures

Reviewer: independent (T22, second attempt; the first was killed mid-flight and left no verdict).
Run `2026-08-17-run1-harness-schedule-poc`. Date 2026-08-18, local fire.
Subject: `.softhouse/capture/pathb/` — `PATHB-REPORT.md`, `REPRODUCE.md`, `req/`, `out/` (`B-01`..`B-04`),
and the rescued WIP in `.softhouse/capture/pathb/t22-probe/`.
Oracle of record: running Fineract server, image `sha256:e596339626bf…`, commit `426a23544e…`, over
**PostgreSQL 18.3**. Pinned source (read-only): `/Users/buv/fineract`.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

The four numbers sets are **sound, reproducible and invariant-clean**, and — the point of the whole task —
**Path B does genuinely grade both inputs Path A silently drops.** I reproduced all four captures
byte-for-byte three separate ways, including on a **genuinely fresh tenant** I provisioned for this audit;
I confirmed both differentials are isolated *and persisted in PostgreSQL*; I re-derived **five** Path B
schedules digit-for-digit from the pinned progressive source in a model I wrote from scratch, including the
final-installment residual-absorption rule; and I mechanically re-checked ten property invariants on every
capture (the orchestrator checked none).

It is **not ACCEPTED outright** because of three things the report gets wrong or leaves undone, one of which
would have propagated a false rule into DEC-1:

1. **P0 — the normative rounding rule in Result 2 is FALSE.** The report says *"The EMI is raised to the next
   multiple of 100."* The oracle **rounds to the NEAREST multiple, using the tenant rounding mode**
   (`Money.java:163-171`). I observed it rounding **down**: at principal MNT 1,190,000 with
   `installmentAmountInMultiplesOf = 100`, the unrounded EMI `111,148.35` becomes **`111,100.00`**, not
   `111,200.00`. A Go port built to the report's sentence diverges from the oracle on roughly half of all
   inputs.
2. **P0 — the captures were taken at the WRONG tenant rounding mode, and I can prove the mode is live.** The
   report says the mode "was not asserted". It is stronger than that: the `default` tenant runs at
   **HALF_EVEN** (`rounding-mode = 6`; the server's own log line
   `Initialized rounding mode for tenant 'default': HALF_EVEN`), not the ratified `HALF_UP`. And the mode is
   **not** inert on this path — I exhibited an input where the two modes give different money on the same
   server (`20,925.05` vs `20,925.04` in period 1). The four captures happen to be mode-insensitive, which I
   established by **re-observing** them at HALF_UP, not by assuming it.
3. **P0 — none of the admissibility furniture from T18/T19 is attached.** No machine-readable attestation
   sidecar; `REPRODUCE.md` asserts image/driver/health but **not** the two settings that actually decide the
   arithmetic (tenant rounding mode, precision); and its capture loop is written with a shell glob in
   `curl -o` that cannot produce the committed filenames.

Nothing here voids a number. Every figure in `out/B-0*.json` survived.

---

## 0. Artefacts I created on the oracle — so the next fire can tell mine from the corpus

**No loan was ever persisted** (`select count(*) from m_loan` = 0 in both tenants); `calculateLoanSchedule`
is a pure calculation endpoint.

| Where | What | Why |
|---|---|---|
| PostgreSQL | database **`fineract_gerege`** (owner `postgres`) | fresh-tenant reproduction |
| `fineract_tenants.tenant_server_connections` | row **id 2** → `fineract_gerege`, `schema_connection_parameters = ''` | ditto |
| `fineract_tenants.tenants` | row **id 2**, identifier **`gerege`**, `timezone_id = 'Asia/Ulaanbaatar'` | closes gap (a) |
| `fineract_gerege.c_configuration` | **`rounding-mode = 4` (HALF_UP)** | closes gap (b) |
| tenant `gerege` | currencies MNT+USD; clients 1–2; loan products **1–4** (the Path B corpus, verbatim payloads), **5–9** = `TP5..TP9` item-8 probes, **10** = `TM1`, **11** = `TM2`, **12** = `TR1` | audit probes |
| tenant `default` | loan products **9 (`TM1`)** and **10 (`TM2`)** | the two-tenant rounding-mode probe |
| container | `fineract-fineract-1` **restarted twice** (17:50, 17:51 local) to provision the tenant and re-init `MoneyHelper` | unavoidable — tenants are read at startup |

Products **5–8 (`T2A..T2D`) in tenant `default` are NOT mine** — they were created by the killed first T22
worker. Tenant `default` is otherwise untouched: I changed no configuration on it.

---

## 1. What I re-ran, exactly

All scripts are committed under `.softhouse/capture/pathb/t22-audit/`.

```sh
# --- preconditions (REPRODUCE.md §Preconditions), all asserted
docker image inspect fineract:latest --format '{{.Id}}'
docker inspect fineract-fineract-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -iE 'driver|jdbc'
docker inspect fineract-fineract-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb'
docker exec fineract-fineract-1 sh -c 'unzip -l /app/fineract-provider.jar | grep -iE "postgres|ojdbc|mysql|mariadb"'
docker exec fineract-fineract-1 sh -c 'unzip -p /app/fineract-provider.jar BOOT-INF/classes/git.properties'
docker exec fineract-db-1 psql -U root -t -c 'select version();'
curl -sk https://localhost:8443/fineract-provider/actuator/health

# --- reproduction 1: committed request bytes, same tenant, existing products 1-4
sh .softhouse/capture/pathb/t22-audit/rerun-default.sh

# --- reproduction 2 (rescued WIP, re-verified): freshly created products 5-8 in `default`
shasum -a 256 .softhouse/capture/pathb/t22-probe/out/calc-B-0*-halfeven-raw.json

# --- reproduction 3: GENUINELY FRESH TENANT (Asia/Ulaanbaatar + HALF_UP), products land at 1-4
sh .softhouse/capture/pathb/t22-audit/fresh-tenant.sh

# --- persistence read-back, from PostgreSQL not from the create response
docker exec fineract-db-1 psql -U root -d fineract_default \
  -At -c "select to_jsonb(t) from m_product_loan t where id in (1,2,3,4) order by id;" > products-asrow.jsonl
python3 .softhouse/capture/pathb/t22-audit/rowdiff.py products-asrow.jsonl

# --- independent invariants (10 checks, exact Decimal, integer minor units)
python3 .softhouse/capture/pathb/t22-audit/t22_invariants.py <each capture>

# --- cross-path claim, B-01 vs pass-3 P-MNT-1M2
python3 .softhouse/capture/pathb/t22-audit/t22_crosspath.py

# --- independent re-derivation from the pinned PROGRESSIVE source
python3 .softhouse/capture/pathb/t22-audit/t22_rederive.py

# --- item-8 probes  (DIYCS under SAME_AS_REPAYMENT_PERIOD; day-count under DAILY vs SARP)
python3 .softhouse/capture/pathb/t22-audit/mkprobe.py && sh .../probe.sh

# --- tenant rounding-mode discrimination, same request to both tenants
python3 .../mkmode.py  && sh .../modeprobe.sh    # absorbed by the EMI re-adjust loop — negative result
python3 .../mkmode2.py && sh .../modeprobe2.sh   # DISCRIMINATES
```

### Precondition results

| Assertion | Observed | Verdict |
|---|---|---|
| Image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | ✅ matches |
| Jar's own `git.properties` | `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`, Zulu build | ✅ build-attested |
| `driverClassName` | `FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME=org.postgresql.Driver` | ✅ |
| JDBC URL | `FINERACT_HIKARI_JDBC_URL=jdbc:postgresql://db:5432/fineract_tenants` | ✅ |
| Prohibited engines in container env | 0 hits for `ojdbc\|oracle.jdbc\|:1521\|com.mysql.cj\|mariadb` | ✅ |
| Prohibited engines in the jar | 0 hits; the only driver jar is `BOOT-INF/lib/postgresql-42.7.11.jar`; `/app/plugins` empty | ✅ |
| Prohibited engines in the compose file | `docker-compose-postgresql.yml`, 0 hits | ✅ |
| Database | `postgres:18.3`, `PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) … aarch64` | ✅ |
| Health | `{"status":"UP",...}` | ✅ |

**One engine smell, P1, not a violation.** The `default` tenant's `tenant_server_connections` row carries
MySQL-only JDBC parameters — `serverTimezone=UTC&useLegacyDatetimeCode=false&sessionVariables=time_zone='-00:00'`
— stale seed data from Fineract's MySQL era. It is de facto inert (pgjdbc ignores unknown URL properties; six
live connections to `fineract_default`), and no MySQL driver exists anywhere in the stack, so the
PostgreSQL-only rule is not breached. But it is MySQL-shaped configuration sitting on the tenant row every
Path B capture ran through, and `REPRODUCE.md` does not assert it away. I set it to `''` on the tenant I
created.

---

## 2. Per-capture table

Money read as exact `Decimal` throughout (`json.loads(..., parse_float=Decimal, parse_int=Decimal)`); every
comparison in **integer minor units**; no tolerance anywhere; no float constructed at any point.

| | reproduced byte-for-byte? | field persisted in PostgreSQL? | 10 invariants | re-derived from source | usable as a parity vector? |
|---|---|---|---|---|---|
| **B-01** baseline | ✅ ×3 — same tenant, fresh products in `default`, **and a fresh tenant** (`sha256:713a3560…` all four times) | n/a (control); `installment_amount_in_multiples_of` **NULL**, `days_in_year_custom_strategy` **NULL** | **ALL PASS** | ✅ **digit-for-digit**, both HALF_EVEN and HALF_UP | **YES**, once the attestation lands. Mode-insensitive — re-observed identical at `(19, HALF_UP)` |
| **B-02** multiplesOf 100 | ✅ ×3 (`sha256:9de8757d…`) | ✅ `installment_amount_in_multiples_of = 100.000000` | **ALL PASS** | ✅ **digit-for-digit**, incl. the multiplesOf rounding and residual absorption | **YES**, same condition |
| **B-03** `FULL_LEAP_YEAR` | ✅ ×3 (`sha256:892dd6f5…`) | ✅ `days_in_year_custom_strategy = 'FULL_LEAP_YEAR'` | **ALL PASS** | not re-derived (DAILY + partial-period path; out of my model's scope) | **YES as a control** — but see §5: `FULL_LEAP_YEAR` is behaviourally **identical to the field being unset**, so B-03 alone has no discriminating power |
| **B-04** `FEB_29_PERIOD_ONLY` | ✅ ×3 (`sha256:c80f62b0…`) | ✅ `days_in_year_custom_strategy = 'FEB_29_PERIOD_ONLY'` | **ALL PASS** | not re-derived (same reason) | **YES — this is the discriminating one.** A port that ignores the field returns B-03's numbers here and fails |

**Differential isolation, verified against the persisted rows, not the create response.** Dumping
`to_jsonb(m_product_loan)` and diffing every column:

- products **1 vs 2** differ in exactly **4** columns: `id`, `name`, `short_name`,
  **`installment_amount_in_multiples_of` (NULL → 100.000000)**.
- products **3 vs 4** differ in exactly **4** columns: `id`, `name`, `short_name`,
  **`days_in_year_custom_strategy` ('FULL_LEAP_YEAR' → 'FEB_29_PERIOD_ONLY')**.
- `m_loan_product_payment_allocation_rule` is identical for all four (same 12-rule `DEFAULT` order,
  `NEXT_INSTALLMENT`).
- The calc requests differ in **`productId` only** for both pairs.

The isolation is clean. The report's claim that it is clean is correct.

**Report claims I re-checked mechanically and confirmed:** B-01↔B-02 "12 of 12 periods differ" ✅;
B-03↔B-04 "12 of 12 periods differ, delta 352.22" ✅; "EMI held constant for periods 1–11" — the
`totalDueForPeriod` set for periods 1–11 of B-02 is exactly `{112100.00}` ✅; "period 12 is
`109,888.23` + `1,977.99` = `111,866.22`, deliberately not the rounded EMI" ✅.

---

## 3. Independent re-derivation from the pinned source

I wrote `t22_rederive.py` from the source, not from the report. Citations, all in the **progressive**
generator (the earlier misattribution to the cumulative generator, flagged by T19 item 5, is a live hazard and
I avoided it deliberately):

| Step | Pinned source |
|---|---|
| server path passes the field the seam drops | `ProgressiveLoanScheduleGenerator.java:108-110` — `emiCalculator.generatePeriodInterestScheduleModel(periods, terms.toLoanConfigurationDetails(), terms.getInstallmentAmountInMultiplesOf(), mc)` |
| Path A path that drops it | `ProgressiveLoanScheduleGenerator.java:81-82` — `LoanApplicationTerms.assembleFrom(modelData, mc)` |
| nominal rate → fraction | `ProgressiveEMICalculator.java:1318-1320` |
| SAME_AS_REPAYMENT_PERIOD + monthly short-circuit | `ProgressiveEMICalculator.java:1510-1516` (and `:1377-1383` for the interest variant) |
| rate factor | `ProgressiveEMICalculator.java:1950-1963`, note the trailing `.setScale(mc.getPrecision(), mc.getRoundingMode())` — **decimal places, not significant digits** |
| `1 + Σ rate factors` | `RepaymentPeriod.java:216-217` (exact `BigDecimal::add`, no `MathContext`) |
| `Π(1+f)` and the `fn` fold | `ProgressiveEMICalculator.java:1816-1820`, `:1822-1828`, `:1991-1993` |
| EMI | `ProgressiveEMICalculator.java:1838-1841` — `rateFactorPlus1N * balance / fnResult` |
| money quantisation | `Money.java:40-52` — `setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())` |
| multiplesOf | `ProgressiveEMICalculator.java:1761-1776` → `Money.java:159-171` |
| per-period interest | `InterestPeriod.java:145-157`, `RepaymentPeriod.java:251-257` |
| due split | `RepaymentPeriod.java:272-285` (`min(calculatedDueInterest, emi)`), `:345-349` (`max(0, emi - dueInterest)`) |
| **final-installment residual absorption** | `ProgressiveEMICalculator.java:1160-1219`; `diff` at `:1202-1203`, applied at `:1205` |

**The residual absorption rule, stated normatively** (this is what DEC-1 must carry):

> `lastPeriod.emi ← lastPeriod.emi + (totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal
> + Σ dueInterest − Σ emi)`
>
> i.e. the final installment absorbs the whole rounding residual of the schedule. It is **not** "the last
> period is whatever is left"; it is the EMI plus a signed delta, and the delta can be positive
> (B-01: `112,082.37 → 112,082.40`) or negative (B-02: `112,100.00 → 111,866.22`).

**Results — five schedules, all digit-for-digit, every period, both rounding modes:**

| capture | inputs | mode | verdict |
|---|---|---|---|
| `B-01` | P 1,200,000 / 12 / 21.6 % | HALF_EVEN | **RE-DERIVED DIGIT-FOR-DIGIT** (12/12 periods + both totals) |
| `B-02` | same, multiplesOf 100 | HALF_EVEN | **RE-DERIVED DIGIT-FOR-DIGIT** |
| fresh-tenant `B-01` | same | HALF_UP | **RE-DERIVED DIGIT-FOR-DIGIT** |
| fresh-tenant `B-02` | same, multiplesOf 100 | HALF_UP | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `TR1` round-down probe | P 1,190,000, multiplesOf 100 | HALF_UP | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `TM2` half-cent probe | P 1,162,502.50 | HALF_UP **and** HALF_EVEN | **RE-DERIVED DIGIT-FOR-DIGIT in both** |

B-03/B-04 are **not** re-derived here. They run the DAILY + `ACTUAL` + cross-year *partial-period* path
(`ProgressiveEMICalculator.java:1400-1414`, `calculatePeriodFractions` at `:1550-1568`), which is a
materially different arm of the code; modelling it honestly is more than this audit's remaining budget. That
is recorded as an open item, not glossed.

---

## 4. Property invariants — the first mechanical check, on all four (and six more)

`t22_invariants.py`, written from scratch (I did **not** trust the rescued `t22-probe/invariants.py` — its
`I5` verdict is hard-coded `verdict("I5", True, …)` and can never fail; see §9).

| | I1 Σprincipal = disbursed | I2 final balance = 0 | I3 Σinterest = total | I4 Σtotal = totalRepayment | I5 splits sum to whole | I6 P+I+F+Pen = total | S1 all money integral in minor units | S2 running balance ties | S3 disbursement row ties | S4 term days = span = Σ daysInPeriod |
|---|---|---|---|---|---|---|---|---|---|---|
| B-01 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 365 |
| B-02 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 365 |
| B-03 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 366 |
| B-04 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 366 |

All six of my own probe captures pass identically. **Not one money literal in any capture fails to be exactly
representable in integer minor units** — the CLAUDE.md non-negotiable holds across the whole Path B set,
including the half-cent probe whose *inputs* carry a `.50`.

---

## 5. The settled finding: **does Path B actually grade the two fields Path A drops?**

**YES for both — with one refinement the report does not make.**

### `installmentAmountInMultiplesOf` — graded, unambiguously

Persisted (`m_product_loan.installment_amount_in_multiples_of = 100.000000`), isolated (4-column row diff),
and it moves **12 of 12 periods**, both totals, and the EMI. Path A cannot see it at all
(`LoanApplicationTerms.assembleFrom` never reads it), so `B-01`/`B-02` is the only pair in the whole corpus
with any discriminating power over it. A Go port that ignores the field scores `B-01` and fails `B-02`.

**But the rule the report states is wrong.** `applyInstallmentAmountInMultiplesOf`
(`ProgressiveEMICalculator.java:1761-1768`) → `safeRoundingForEMI` (`:1770-1776`) →
`Money.roundToMultiplesOf(Money, Integer)` (`Money.java:159-161`) → `Money.java:163-171`:

```java
amountScaled = amountScaled.divide(inMultiplesOfValue, 0, mc.getRoundingMode()).multiply(inMultiplesOfValue);
```

That is **round to the NEAREST multiple under the tenant rounding mode**, not "raise to the next multiple".
`B-02` cannot tell the two apart (`112,082.37 / 100 = 1120.8237`, which rounds up either way). I therefore
put a round-**down** case to the oracle:

> product `TR1`, principal **MNT 1,190,000**, multiplesOf 100, tenant `gerege` at `(19, HALF_UP)`.
> Unrounded EMI **`111,148.35`** → applied EMI **`111,100.00`** (periods 1–11), final installment
> `111,741.26`, total repayment `1,333,841.26`.
> Re-derived digit-for-digit by my model. Raw capture: `t22-audit/out-rounddown/rounddown-gerege-raw.json`.

`111,100.00 < 111,148.35`. The EMI was rounded **down**. The report's sentence is refuted by the oracle.

Two further normative facts the contract needs, neither of which is in the report:

- **`safeRoundingForEMI` has a zero-guard** (`:1772-1774`): if rounding would zero a positive EMI, the
  *unrounded* EMI is used instead. So `multiplesOf` is not unconditionally applied.
- **The EMI re-adjust loop can undo the multiplesOf rounding.**
  `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (`:1258-1308`, up to 3 iterations) re-rounds
  `emiAdjustment.adjustedEmi()` and adopts it if the last-vs-penultimate EMI gap shrinks. I hit this
  empirically: my first rounding-mode probe (`TM1`, principal 1,163,000, multiplesOf **1**) predicted a
  clean HALF_UP/HALF_EVEN split at the scale-0 tie (`108,626.50 → 108,627` vs `108,626`), and the oracle
  returned **`108,626.00` on both tenants** — the loop converged both modes to the same schedule. That is a
  real behaviour a Go port must reproduce, and no vector in the corpus pins it. The negative capture is kept:
  `t22-audit/out-modeprobe/`.

### `daysInYearCustomStrategy` — graded, but only one of its two values does anything

Persisted, isolated, moves **12 of 12 periods** and both totals (delta `352.22` on 1.2 M). But:

> **`FULL_LEAP_YEAR` is behaviourally identical to the field being unset.**
> Probe `TP7` — B-03's product with `daysInYearCustomStrategy` **removed entirely** — returns a capture
> **byte-identical to `B-03`** (`sha256:892dd6f5…` both). Source agrees: `DaysInYearType.getNumberOfDays`
> (`DaysInYearType.java:81-86`) has no `FULL_LEAP_YEAR` branch, and `getNumberOfDays`
> (`ProgressiveEMICalculator.java:1346-1352`) only special-cases `FEB_29_PERIOD_ONLY`.

So the discriminating value is `FEB_29_PERIOD_ONLY` alone, and `B-04` is the vector that grades it. A port
that ignores the field entirely still passes `B-03` and fails `B-04` — which is all the corpus needs. The
report should say this rather than presenting the pair as symmetric.

**Both fields are therefore now vectored, and the standing disposition "refuse with *unsupported: no
discriminating vector*" is dead for both** — the report's conclusion 1 is upheld, on evidence I re-derived
independently.

---

## 6. Cross-path claim — `B-01` vs pass-3 `P-MNT-1M2`

**Confirmed, precisely.** All 12 periods and all three totals match in integer minor units:

```
 per   A principal  B principal   A interest   B interest    A total     B total
   1      9048237     9048237      2160000     2160000    11208237   11208237  ok
   …            …           …            …           …           …          …
  12     11010059    11010059       198181      198181    11208240   11208240  ok
 totalDisbursed  120000000 / 120000000    totalInterest 14498847 / 14498847
 totalRepayment 134498847 / 134498847
```

**Correction to the framing, not to the claim.** The task brief asked whether `B-01` equals `P-MNT-1M2`
*"digit-for-digit"*. As whole documents they do **not**: Path A disbursed 2024-01-01 and reports
`loanTermInDays = 366`; Path B disbursed 2026-01-01 and reports `365`; every due date differs. The report's
own wording — *"reproduces … to the minor unit"* — is the accurate one, and it is the money that matches.
The corroboration is real and it is the strongest calibration evidence the program has: two seams, two
day-count configurations, one arithmetic. The report's caveat that this does **not** show day-count settings
are ignored is correct, and §8 below now settles what it left open.

One thing this equality does **not** license, and the report does not claim it: `P-MNT-1M2` was captured at
`(19, HALF_UP)` and `B-01` at `(19, HALF_EVEN)`. Their agreement is evidence that *these inputs* are
mode-insensitive, not that the mode is irrelevant.

---

## 7. The two named gaps — both now settled with observations

### (a) Tenant timezone `Asia/Kolkata` — **metadata only. Proven, not argued.**

CLAUDE.md requires `Asia/Ulaanbaatar` (+08) or `Asia/Hovd` (+07), no DST, never a hard-coded offset. The
`default` tenant is `Asia/Kolkata` (`select timezone_id from tenants` → `Asia/Kolkata`).

I provisioned tenant **`gerege` with `timezone_id = 'Asia/Ulaanbaatar'`**, ran `REPRODUCE.md` end to end on
it with the committed request bytes, and **all four captures came back byte-identical** — same four SHA-256
digests as the committed corpus. The timezone changes **no captured figure**. It cannot: every date in these
requests is an explicit civil date (`"01 January 2026"`, `dd MMMM yyyy`), and the tenant zone reaches only
business-date resolution, which these requests use for validation (`submittedOnDate ≤ business date`) and not
for arithmetic.

**Closing it requires:** nothing for these four vectors — record the observation and move on. It becomes
load-bearing the moment a capture depends on "today" (COB, accruals, arrears, delinquency, `loanTermInDays`
of an open-ended product). For those, a Mongolian tenant is mandatory *before* capture, and both zones must
be exercised, because Gerege operates in two. `Asia/Ulaanbaatar` and `Asia/Hovd` both exist in the tenant
store's `timezones` table, so no seed work is needed.

### (b) Rounding mode and precision not asserted — **the mode was WRONG, and it is LIVE**

Three separate findings, in increasing order of consequence.

**1. The mode the four captures actually ran at is HALF_EVEN, not HALF_UP.**
`ConfigurationDomainServiceJpa.getRoundingMode()` (`:222-235`) defaults to `6` and the tenant DB holds
`c_configuration.rounding-mode = 6`. The container seeds it from
`fineract.tenant.config.rounding-mode=${FINERACT_CONFIG_ROUNDING_MODE:6}`
(`application.properties:77`, consumed by liquibase at `:514` into
`db/changelog/tenant/parts/0002_initial_data.xml:219-220`). The server logged it itself:

```
2026-08-17 11:31:58 [default] MoneyHelper : Initialized rounding mode for tenant `default`: HALF_EVEN
2026-08-18 09:53:01 [gerege ] MoneyHelper : Initialized rounding mode for tenant `gerege`: HALF_UP
```

The first line predates the Path B fire and spans it. So **every Path B capture on record was taken at
`(19, HALF_EVEN)`** — precision 19 is not in doubt (`MoneyHelper.PRECISION = 19`, compile-time,
`MoneyHelper.java:35`; `getMathContext()` at `:91-93`), but the mode is not the ratified one. The report's
"not asserted" understates this: it was asserted, by default, to the wrong value.

**2. The mode is live on this path — I exhibited a discriminating capture.**
Same product, same request, two tenants differing only in `rounding-mode`. Input chosen so that period-1
interest is an exact half-cent tie: principal **MNT 1,162,502.50**, and `1,162,502.50 × 0.018 = 20,925.045`.

| tenant | mode | p1 interest | p1 principal | total interest | total repayment |
|---|---|---|---|---|---|
| `gerege` | **HALF_UP** | `20,925.05` | `87,654.98` | `140,457.89` | `1,302,960.39` |
| `default` | **HALF_EVEN** | `20,925.04` | `87,654.99` | `140,457.88` | `1,302,960.38` |

Both were predicted in advance by my re-derivation model and both match it digit-for-digit. Raw captures:
`t22-audit/out-modeprobe2/`. The tie is taken at `Money.java:52`
(`setScale(decimalPlaces, getMc().getRoundingMode())`) via `RepaymentPeriod.java:251-257`. **The tenant
rounding mode is not a dead knob on Path B.**

**3. The four captures are nevertheless mode-insensitive — because I re-observed them, not because I assumed
it.** The fresh-tenant run at `(19, HALF_UP)` returned the same four SHA-256 digests as the corpus taken at
`(19, HALF_EVEN)`.

**Closing it requires:**
- record the four captures' asserted setting as `(19, HALF_UP)` **on the strength of the fresh-tenant
  re-observation committed here** (`t22-audit/out-fresh-tenant/`), not on the original run;
- add `rounding-mode` and `MoneyHelper.PRECISION` to `REPRODUCE.md`'s precondition block as **fail-the-run**
  assertions;
- **stop capturing on `default`.** Point Path B at a tenant provisioned at
  `FINERACT_CONFIG_ROUNDING_MODE=4` + `Asia/Ulaanbaatar`. `gerege` is now that tenant and is ready. Note the
  env var must be set *before* the tenant's first liquibase run, or the config must be updated and the
  server restarted — `MoneyHelper` caches per tenant at startup and the only runtime re-init endpoint,
  `InternalConfigurationsApiResource` (`:87-92`), is `@Profile(TEST)` and unavailable here.

---

## 8. The orchestrator's two explicit NON-claims — both settled

The abstentions were **honest and correctly scoped, but over-cautious**: both were answerable, one from
source alone, and I settled both empirically.

### (i) Isolated effect of `daysInYearCustomStrategy` under `SAME_AS_REPAYMENT_PERIOD` — **ZERO**

Probes `TP5`/`TP6`: B-01's product shape (`interestCalculationPeriodType = 1`, `ACTUAL`/`ACTUAL`) with
`FULL_LEAP_YEAR` vs `FEB_29_PERIOD_ONLY`, over a term spanning 29 Feb 2024. Captures are
**byte-identical** (`sha256:ff92fc5d…` both).

Source says why, and says it unconditionally: `calculateRateFactorPerPeriod` reads
`daysInYearCustomStrategy` at `:1497-1498`, but the `isSameAsRepaymentPeriod()` + monthly branch at
`:1510-1516` **returns before any use of it**, with `daysInYear` hard-set to `12`. Same structure in the
interest variant at `:1377-1383`. So under `SAME_AS_REPAYMENT_PERIOD` with monthly (or weekly) repayment the
field **cannot** bite — this is a theorem about the code, not a property of these inputs.

The report was right to refuse to claim an isolated effect from `B-03`/`B-04` (which vary two axes). It was
wrong to leave the question open: the answer is zero, and the contract should state the precondition
(`interestCalculationPeriodType = DAILY` **and** `daysInYearType = ACTUAL`) rather than describing the field
as unconditionally live. `LoanProduct.java:462-472` already enforces the `ACTUAL` half at product creation.

### (ii) Do `daysInYearType` / `daysInMonthType` affect a progressive schedule? — **YES under DAILY, NO under SAME_AS_REPAYMENT_PERIOD**

| probe | shape | result |
|---|---|---|
| `TP7` vs `TP8` | DAILY, `ACTUAL`/`ACTUAL` vs `360`/`30` | **DIFFER** (`892dd6f5…` vs `ff92fc5d…`); total interest `144,659.21` vs `144,988.47` |
| `TP9` vs `B-01` | SAME_AS_REPAYMENT_PERIOD, `360`/`30` vs `ACTUAL`/`ACTUAL` | **byte-identical** (`713a3560…` both) |

So the day-count settings are live on the progressive path, but **only** when
`interestCalculationPeriodType = DAILY`. Under `SAME_AS_REPAYMENT_PERIOD` + monthly they are dead by the
same `:1510-1516` short-circuit. Incidentally `TP8` (DAILY, 360/30) reproduces the
`SAME_AS_REPAYMENT_PERIOD` schedule exactly — 30/360 monthly *is* one-twelfth — which is a pleasing
consistency check on the whole rig.

Both answers are now vectored, at production settings, on the fresh tenant. Raw captures:
`t22-audit/out-probe/`.

---

## 9. Inherited defect lists applied to Path B

### T18 (`.softhouse/reviews/T18-capture-audit.md`) P0 list

| T18 P0 | Status on Path B |
|---|---|
| 1. machine-readable **environment-attestation block** attached to the artefact | ❌ **STILL OPEN.** The provenance table lives in `PATHB-REPORT.md` prose. `out/*.json` are raw server bytes and cannot carry it, so Path B needs a **sidecar** `attestation.json` per capture set. Missing: capture-path label (`Path B — running server`), tenant identifier, **tenant rounding mode**, `MoneyHelper.PRECISION`, tenant timezone, PostgreSQL version string, request SHA-256, response SHA-256, UTC timestamp. By the capture plan's own §4.1 rule these are not yet admissible vectors. |
| 2. committed **run recipe** | ⚠️ **PARTLY CLOSED.** `REPRODUCE.md` exists and is genuinely good — its "Gotchas" section saved me four round trips. Two defects: (a) the capture loop writes `-o out/B-$n-*-raw.json`, a shell glob that cannot expand for a not-yet-existing file, so running the recipe verbatim creates files literally named `B-01-*-raw.json`, not the committed names; (b) the preconditions do not assert the tenant rounding mode, precision or timezone — the exact omission that let a HALF_EVEN corpus be recorded as if it were parity-grade. |
| 3. emit `fromDate`, `fee`, `penalty` per period | ✅ **CLOSED BY CONSTRUCTION.** The server emits `fromDate`, `dueDate`, `daysInPeriod`, `feeChargesDue`, `penaltyChargesDue`, `principalDue`, `interestDue`, `totalDueForPeriod`, `principalLoanBalanceOutstanding`, `totalOutstandingForPeriod` and more. Path B is strictly richer than Path A here. |
| 4. retained stack traces on the error branch | ➖ **N/A but worth a rule.** No capture errored. Path B's failure mode is an HTTP error body, which is self-describing — but only if it is *saved*. `REPRODUCE.md` discards the HTTP status entirely (`curl -sk … -o file` with no `-w '%{http_code}'`), so a 400 would land in `out/` looking like a capture. Add status capture. |

### T19 (`.softhouse/reviews/T19-capture-pass2-audit.md`) ten required changes

| T19 item | Status on Path B |
|---|---|
| 1–2 (retract the 17.01 argument / the "both channels" claim) | ✅ N/A — Path B repeats neither |
| 3 (`daysInYearCustomStrategy` as a second dropped input) | ✅ **carried correctly** into `PATHB-REPORT.md`, with the right mechanism and line numbers (`:604`, `:304-351`) |
| 4 (state that the captures are *probes*, not parity vectors, w.r.t. the ratified MathContext) | ❌ **REPEATED, in the same shape.** Pass 2's sin was precision 12; Path B's is mode HALF_EVEN. §7(b) |
| 5 (**cite the progressive generator, not the cumulative one**) | ⚠️ `PATHB-REPORT.md` cites the Path A defect correctly but gives **no server-path citation at all** for Results 2 and 3. It should carry `ProgressiveLoanScheduleGenerator.java:108-110`, `ProgressiveEMICalculator.java:1761-1776`, `:1330-1352`, `Money.java:159-171`. Absent citations are how the cumulative/progressive confusion got in last time |
| 6–7 (restate warrants, fix `MoneyHelper` citations) | ✅ N/A |
| 8 (record the controls and gaps) | ⚠️ partly — the caveats section is honest and unusually good, but omits that no invariant was checked and that `FULL_LEAP_YEAR ≡ unset` |
| 9 (cosmetic line refs) | ✅ the two line refs Path B does give (`:604`, `:304-351`) are correct |
| 10 (**separate the two multiples-of fields**) | ✅ **CLOSED.** Path B varies `installmentAmountInMultiplesOf` while `currency.inMultiplesOf` stays `0` and `decimalPlaces` `2`, so the `Money.java:47-51` currency channel (gated on `decimalPlaces == 0`) is provably inert and contributes nothing. The two are cleanly separated for the first time |

### The rescued T22 WIP (`.softhouse/capture/pathb/t22-probe/`)

Verified, kept, and corrected:

- `repro.sh` / `capture.sh` / `mkreq.py` / `mkcalc.py` — **sound**. I re-hashed the outputs they produced:
  all four match the committed corpus byte-for-byte, and they were produced through **freshly created
  products (5–8)**, which makes them an independent reproduction. That is real evidence and I have counted it.
- The `halfeven` filename tag is **misleading**: nothing in those scripts changes the rounding mode. The tag
  records what the prior worker had *discovered* the mode to be, not a variant they ran. Read as a variant it
  would be a false record. Renamed in spirit here; the files are left where they are so the provenance chain
  stays intact.
- `invariants.py` — **defective**: `verdict("I5", True, …)` hard-codes the split-sum invariant to PASS. It
  prints a failure line above it, so a human would notice, but the returned verdict cannot fail. I did not
  reuse it; `t22-audit/t22_invariants.py` is written from scratch and checks ten invariants including a
  genuinely-failable I5.
- `rederive.py` — not used. I wrote my own from source, which is the point of the task.

---

## 10. Required changes

### P0 — blocks promotion of `B-01`..`B-04` to the vector store

1. **Retract and replace the rounding rule in `PATHB-REPORT.md` Result 2.** *"The EMI is raised to the next
   multiple of 100"* is false. The rule is: **round the EMI to the nearest multiple of
   `installmentAmountInMultiplesOf`, using the tenant rounding mode**
   (`ProgressiveEMICalculator.java:1770-1776` → `Money.java:163-171`), **with a zero-guard** that returns the
   unrounded EMI when rounding would zero a positive one. Cite the round-down observation
   (`t22-audit/out-rounddown/`, principal 1,190,000 → EMI `111,100.00` from an unrounded `111,148.35`).
   Anything DEC-1 says about this field must be written from the corrected rule.
2. **State that `B-01`..`B-04` were captured at `(19, HALF_EVEN)`**, not the ratified `(19, HALF_UP)`, and
   that they are admissible at `(19, HALF_UP)` **only** on the strength of the fresh-tenant re-observation
   committed at `t22-audit/out-fresh-tenant/` (four identical SHA-256 digests). Carry the server's own log
   line as the evidence for the original mode.
3. **Attach a machine-readable attestation sidecar** to the Path B capture set: capture path, image digest,
   jar `git.commit.id` + `git.dirty`, JVM string, PostgreSQL `version()`, tenant identifier, **tenant
   rounding-mode ordinal and name**, `MoneyHelper.PRECISION`, tenant timezone, per-capture request and
   response SHA-256, UTC timestamp. Until it exists, the capture plan's §4.1 rule says these are not vectors.
4. **Make `REPRODUCE.md`'s preconditions fail the run**, and add the two that decide the arithmetic:
   `select value from c_configuration where name='rounding-mode'` **must be 4**, and
   `select timezone_id from tenants` **must be `Asia/Ulaanbaatar` or `Asia/Hovd`**. Also assert
   `schema_connection_parameters` is empty (the `default` row carries MySQL-era JDBC parameters).
5. **Fix the capture loop.** `-o out/B-$n-*-raw.json` cannot produce the committed filenames. Write the names
   out, and capture `-w '%{http_code}'` so an HTTP error cannot be mistaken for a capture.
6. **Re-point Path B at a production-settings tenant.** Stop capturing on `default` (Kolkata / HALF_EVEN).
   Tenant `gerege` (Asia/Ulaanbaatar, HALF_UP) is provisioned and verified; or rebuild the stack with
   `FINERACT_CONFIG_ROUNDING_MODE=4` before the tenant's first liquibase run.

### P1 — correctness and completeness of the record

7. **Record that `FULL_LEAP_YEAR` is behaviourally identical to the field being unset** (probe `TP7` ≡ `B-03`,
   byte-identical; `DaysInYearType.java:81-86` has no branch for it). `B-04` is the only vector with
   discriminating power over `daysInYearCustomStrategy`; say so, and stop presenting the pair as symmetric.
8. **Record the precondition for the field**: it can only bite under `interestCalculationPeriodType = DAILY`
   **and** `daysInYearType = ACTUAL` (`ProgressiveEMICalculator.java:1510-1516` short-circuits everything
   else; `LoanProduct.java:462-472` enforces the ACTUAL half). Cite probes `TP5`/`TP6` (byte-identical under
   `SAME_AS_REPAYMENT_PERIOD`).
9. **Add the day-count answer to the record**: `daysInYearType`/`daysInMonthType` move a progressive schedule
   under DAILY (`TP7` ≠ `TP8`) and are inert under `SAME_AS_REPAYMENT_PERIOD` (`TP9` ≡ `B-01`). This closes
   the second non-claim.
10. **Add the server-path citations** to Results 2 and 3: `ProgressiveLoanScheduleGenerator.java:108-110`
    (the field the seam drops is passed here), `ProgressiveEMICalculator.java:1761-1776`, `:1330-1352`,
    `:1160-1219`, `Money.java:159-171`. Path B's report currently cites only the Path A defect. T19 item 5
    exists because this exact omission produced cumulative-generator citations last time.
11. **Record the EMI re-adjust loop as unpinned contract behaviour**
    (`ProgressiveEMICalculator.java:1258-1308`, ≤3 iterations). It can absorb a `multiplesOf` rounding
    difference entirely — demonstrated by the negative probe at `t22-audit/out-modeprobe/`, where HALF_UP and
    HALF_EVEN converged to the same schedule. A Go port that implements the rounding but not the loop will
    diverge. Capture a vector that forces the loop to iterate.
12. **State the residual-absorption rule normatively** in the report (not only as a worked example):
    `lastEmi = emi + (P + ΣI − Σemi)`, `ProgressiveEMICalculator.java:1202-1205`. The delta is signed.
13. **Correct the `t22-probe` provenance note**: the `halfeven` tag names the mode that was *discovered*, not
    a variant that was *run*; no script there changes the rounding mode. And mark
    `t22-probe/invariants.py` as defective (`I5` hard-coded to PASS) so nobody re-uses it.
14. **Record that `B-03`/`B-04` are not independently re-derived.** They run the DAILY cross-year
    partial-period arm (`ProgressiveEMICalculator.java:1400-1414`, `calculatePeriodFractions` `:1550-1568`).
    Their numbers are reproduced, invariant-clean and internally consistent, but no one has yet rebuilt them
    from source. That is the largest remaining hole in the Path B evidence.

---

## What Path B does and does not license us to conclude about gate G-1

*My own reading, from the source and the running server — not a restatement of the report.*

**It licenses these.** The Path B rig is trustworthy: the pinned build, the mandated engine, and captures that
regenerate byte-for-byte across three independent executions including a fresh tenant. Both inputs Path A
drops are now genuinely graded, and DEC-1 may treat `installmentAmountInMultiplesOf` and
`daysInYearCustomStrategy` as **live inputs the contract must expose and the Go module must implement** —
refusing them would make the port diverge from the oracle by construction. The corroboration between Path A's
seam and Path B's full stack on `P-MNT-1M2`/`B-01` is real, and the money invariants hold everywhere.

**It does not license these.** It does not license the report's round-up rule — DEC-1 must carry
round-to-nearest-under-tenant-mode instead. It does not license calling `B-01`..`B-04` production-settings
parity vectors on the original run; only the fresh-tenant re-capture committed here does that. It does not
license any claim about `daysInYearCustomStrategy` outside `DAILY` + `ACTUAL`, where the field is provably
inert. It says nothing about multi-disbursement, charges, down payments, repayments, or any path through
`getDueAmounts` — every capture here is a clean unpaid schedule. And it is not, and cannot be, evidence for
cutover, which remains a hard `user` gate.
