# T51 — the alias and the tranche charge, captured

**Task** T51, branch `softhouse/T51-alias-and-tranche-captures`.
**Fire** local `20260819-140003`, Buyan's Mac. The reference oracle (Fineract) **was reachable** and
every number below is an **OBSERVATION made on it**, except where a line is explicitly labelled a
re-derivation. Oracle Database is prohibited and appears nowhere; the only engine touched is
**PostgreSQL 18.3**.

> ## THIS TASK CAPTURES. IT DOES NOT ADMIT.
> **RAW OBSERVED FORM ONLY.** Gate **G-1 is open** and DEC-1 is unratified while a sibling task
> re-reviews it, so nothing here is promoted, admitted to the graded domain, proposed as a DEC-1
> amendment, or written contract-shaped. No file under `docs/adr/**`, `.softhouse/vectors/**`,
> `program.json`, `tasks.json`, `gates.md`, `patterns.md` or `reference-oracle.md` was touched.
> **`.softhouse/capture/mathcontext/` was not touched** (T50 owns it this fire).

---

## 0. Headline

**Item 1 is settled by observation: T48-N1's alias is REAL in source, the slot it feeds IS read on
the `calculateLoanSchedule` path — both of its readers were reached and both were shown to move
money — and the product/request setting `interestRecognitionOnDisbursementDate` still moves
NOTHING. 0 of 153/164 cells on every one of eight shapes.** The oracle's schedule matches the
31-December boundary on **6 of 6** crossing periods where the two boundary readings differ, and the
1-January boundary on **0 of 6**, while the product flag was `true` on half of those captures.

**Item 2 is settled too, and T48's premise turned out to be wrong twice.** A multi-disbursement
product and three genuine tranches still give a schedule **byte-identical** to
`chargeCalculationType` 2 (0 of 302 cells) — the tranche product is not what separates them. What
does: **tranches that do not sum to the loan principal** (12,345.00 vs 14,814.00) and
**`minCap`/`maxCap`** (13,641.50 vs 5,000.00; 24,000.00 vs 8,000.00). So `chargeCalculationType` 5
**is** per-tranche, and it was hidden by linearity, not by the absence of tranches.

**Item 3 landed as well**: `minCap`/`maxCap` are captured above, and `fixedLength` was captured
after finding the guard that had been blocking it since T44.

---

## Oracle reachability and preconditions

`https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP"}`. Tenant `gerege`,
image `sha256:e596339626bf…`, jar `git.commit.id 426a23544e8426a38ae43ae404670a0a7e85b9eb`,
`git.dirty=false`, PostgreSQL 18.3, `Asia/Ulaanbaatar`.

`bin/run-preconditions.sh` (T36's 15 assertions, 21 printed checks, including the **behavioural
half-cent canary** — period-1 interest `20925.05`; `HALF_EVEN` would give `20925.04`) was run
**before every one of the six capture passes and again after passes 1, 2 and 5**, and printed its
PASS line each time:

```
ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
PRECONDITIONS_EXIT=0
```

Committed at `capture/charges/out/t51/preconditions{,-after,-pass2,-pass2-after,-pass3,-pass4,-pass5,-pass5-after,-pass6}.txt`.
Each capture script hard-aborts unless the literal string `ALL PRECONDITIONS HOLD` is present, so a
gate that merely returned 0 without running would still fail the run.

The pinned checkout `/Users/buv/fineract` stayed read-only: `git status --porcelain` is **empty**
and `HEAD` is still `426a23544e8426a38ae43ae404670a0a7e85b9eb`. No Gradle build ran. The shared
containers were never started, stopped, restarted, re-tenanted or reconfigured.

---

## Item 1 — T48-N1, method and cells observed

### 1.1 The citation, re-opened. T48-N1 is exactly right — with one correction to the brief

`LoanApplicationTerms.toLoanConfigurationDetails()` [VERIFIED: `LoanApplicationTerms.java:1746-1756`]
passes, as its **16th positional argument** [VERIFIED: `:1753`]

```java
isInterestChargedFromDateSameAsDisbursalDateEnabled != null && isInterestChargedFromDateSameAsDisbursalDateEnabled,
```

into a constructor whose 16th parameter is `boolean interestRecognitionOnDisbursementDate`
[VERIFIED: `LoanConfigurationDetails.java:67-76`, the parameter at `:72`], assigned at
[VERIFIED: `:92`] and returned by `isInterestRecognitionOnDisbursementDate()`
[VERIFIED: `:201-203`]. I counted both argument lists position by position; they line up.

The field `LoanApplicationTerms.interestRecognitionOnDisbursementDate` [VERIFIED: declared `:290`,
set from the builder `:327-328`, set through `assembleFrom` `:880`] is **never read by
`toLoanConfigurationDetails()`** [VERIFIED: the only two reads of that field in the file are
`:1740` inside `getLoanProductRelatedDetail()` and `:880`, the assignment].

**Correction to the brief.** The brief says "two distinct **product** settings are aliased onto
one". Only one of them is a product setting. `isInterestChargedFromDateSameAsDisbursalDateEnabled`
is a **GLOBAL configuration value**, read from `configurationDomainService.isInterestChargedFrom
DateSameAsDisbursementDate()` [VERIFIED: `LoanScheduleAssembler.java:370-371`,
`GlobalConfigurationConstants.java:45` → `interest-charged-from-date-same-as-disbursal-date`], and
passed to `assembleFrom` at [VERIFIED: `:559`]. `interestRecognitionOnDisbursementDate` is a product
setting, overridable per request [VERIFIED: `LoanScheduleAssembler.java:537-541`;
`LoanScheduleValidator.java:78` lists it as supported on `calculateLoanSchedule`]. **The alias
therefore crosses two different configuration scopes** — a tenant-global switch is delivered into
the slot a per-product/per-request switch is named for. That makes the defect worse than stated, not
better: a Go port cannot fix it by wiring "the other product field".

### 1.2 What reads the slot downstream — the whole reachable surface

`LoanConfigurationDetails.isInterestRecognitionOnDisbursementDate()` is the `ILoanConfigurationDetails`
implementation the progressive path uses: `ProgressiveLoanScheduleGenerator.generate` calls
`emiCalculator.generatePeriodInterestScheduleModel(…, loanApplicationTerms.toLoanConfigurationDetails(), …)`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:108-110`], and the model stores it as
`ILoanConfigurationDetails loanProductRelatedDetail` [VERIFIED:
`ProgressiveLoanInterestScheduleModel.java:62,75,78`].

A grep of all **main** sources for `isInterestRecognitionOnDisbursementDate` finds exactly **two**
call sites that read it *through that interface*:

| site | reached when | reached in this pass? |
|---|---|---|
| `ProgressiveEMICalculator.java:1579`, inside `getFractionPeriodDueDateForEndOfYear` [`:1578-1584`], called only from `calculatePeriodFractions` [`:1560`], called only from the two `partialPeriodCalculationNeeded` branches [`:1393-1397`, `:1526-1530`] | `daysInYearType == ACTUAL` **and** the period crosses a calendar year **and** not suppressed by `FEB_29_PERIOD_ONLY` [`:1372-1374`, `:1505-1507`] | **YES** — passes 1 and 2 |
| `ProgressiveEMICalculator.java:194`, inside `buildLoanApplicationTerms` [`:176-204`], called only from `addFullTermTrancheDisbursement` [`:167`], guarded by `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` [`:140-143`] | the product allows full-term-for-tranche and a disbursement is applied | **YES** — passes 5 and 6 |

Every other hit in the grep is on `LoanProductRelatedDetail` (the real product entity), not on the
aliased `LoanConfigurationDetails`, and so is a different question.

### 1.3 The fixtures

Two products were created from the **same committed payload** (`capture/pathb/req/product-3-diycs-fullleapyear.json`)
by text substitution on named lines only (T36's method), so every numeric literal is byte-identical
and no money value was round-tripped through a parser. `diff` reports **6 changed lines** each
(name, shortName, and `daysInYearCustomStrategy` → `interestRecognitionOnDisbursementDate`), and
`diff P1 P2` reports exactly three changed lines.

| id | shortName | `days_in_year_enum` | `interest_calculated_in_period_enum` | schedule type | `interest_recognition_on_disbursement_date` |
|---|---|---|---|---|---|
| **17** | `T5A` | 1 (ACTUAL) | 0 (DAILY) | PROGRESSIVE | **`t`** |
| **18** | `T5B` | 1 (ACTUAL) | 0 (DAILY) | PROGRESSIVE | **`f`** |

The run does not take that on trust. It asserts in PostgreSQL that 17 and 18 agree on **20 compared
columns** and differ on `interest_recognition_on_disbursement_date`, and aborts otherwise
(`t51-capture.sh`, the `matched-pair assertion`). Negative test **N5** shows that assertion
returning 0 for a deliberately mismatched pair, so it is not a tautology.

`interestCalculationPeriodType 0` (DAILY) is not decoration: a `SAME_AS_REPAYMENT_PERIOD` product
returns at `ProgressiveEMICalculator.java:1516-1524` **before** the partial-period branch, so the
arm — and the slot — would be unreachable.

### 1.4 The cells

Full-cell comparison: every period row, every column, plus the plan totals. Never the three headline
scalars (`patterns.md`: on some defect classes full-cell comparison is the only version of the check
that exists).

| shape | disbursed | why it should move if the slot moves | product 17 (TRUE) vs 18 (FALSE) |
|---|---|---|---|
| `AA1` | 01 Nov 2024 | T48's AA-1 shape; period 2 crosses 2024→2025 | **0 of 153 cells** |
| `DEC15` | 15 Dec 2024 | crossing period, 16-day first segment at the 31-Dec boundary, 17 at the 1-Jan boundary | **0 of 153** |
| `DEC31` | 31 Dec 2024 | first segment is **0 days** at 31-Dec, **1 day** at 1-Jan — the sharpest separator the rule admits | **0 of 153** |
| `R13` | 15 Dec 2023, `repaymentEvery` 13 | each period spans **three** year segments, so the boundary is chosen twice per period | **0 of 65** |
| `NL2L` | 15 Dec 2023, monthly | the other direction: 365-day year → 366-day year | **0 of 153** |
| `NOCROSS` | 01 Feb 2025 | CONTROL — no crossing, so the arm cannot fire | **0 of 153** |
| `AA1` + request `interestRecognitionOnDisbursementDate: true` on product 18 | 01 Nov 2024 | the per-request override [`LoanScheduleAssembler.java:537-541`] | **0 of 153** vs plain product 18 |
| `AA1` + request `…: false` on product 17 | 01 Nov 2024 | the override in the other direction | **0 of 153** vs plain product 17 |
| `FTTP` (products 20/21, full-term-tranche arm firing) | 01 Nov 2024, two tranches | the **second** reader, `:194` | **0 of 164** |

**The shapes are not inert.** The same comparator, on the same captures:

* `AA1` at `daysInYearType` ACTUAL vs the same shape forced to 365 (arm suppressed at the first
  conjunct): **79 of 153 cells differ**, e.g. `row1.interestDue` `21245.90` → `21304.11`.
* the full-term-tranche guard on vs off, on the **same** product 20: **52 of 164 cells differ**,
  e.g. `loanTermInDays` `242` → `181`, `row4.principalDue` `194788.28` → `236781.30`.
* negative test **N8** shows the identical comparator reporting 23 cells on a pair that does differ.

### 1.5 Which boundary did the oracle use? — the discrimination that decides it

`calculatePeriodFractions` [VERIFIED: `ProgressiveEMICalculator.java:1548-1570`] computes
`f = Σ_years days(segment) / Year.of(year).length()`, with the segment boundary at **31 December**,
or at **1 January of the next year** when the slot is true [VERIFIED: `:1578-1584`]. The two give
different `f`, hence different rate factors, hence different period interest.

Both candidates were **re-derived from the observed dates** at the ratified `MathContext(19, HALF_UP)`
and compared with the interest the oracle actually returned. The dates, balances and interests below
are **OBSERVATIONS**; the two candidate columns are **RE-DERIVATIONS**.

| capture | period | from → due | balance at start | **oracle interest** | 31-Dec re-derivation | 1-Jan re-derivation | verdict |
|---|---|---|---|---|---|---|---|
| `AA1-P1` (flag **TRUE**) | 2 | 2024-12-01 → 2025-01-01 | 1008552.46 | **18453.18** | `30/366 + 1/365` → **18453.18** | `31/366 + 0/365` → 18451.55 | **31-Dec** |
| `AA1-P2` (flag FALSE) | 2 | 2024-12-01 → 2025-01-01 | 1008552.46 | **18453.18** | **18453.18** | 18451.55 | 31-Dec |
| `DEC31-P1` (flag **TRUE**) | 1 | 2024-12-31 → 2025-01-31 | 1200000.00 | **22014.25** | `0/366 + 31/365` → **22014.25** | `1/366 + 30/365` → 22012.31 | **31-Dec** |
| `DEC31-P2` (flag FALSE) | 1 | 2024-12-31 → 2025-01-31 | 1200000.00 | **22014.25** | **22014.25** | 22012.31 | 31-Dec |
| `DEC15-P1` (flag **TRUE**) | 1 | 2024-12-15 → 2025-01-15 | 1200000.00 | **21983.20** | `16/366 + 15/365` → **21983.20** | `17/366 + 14/365` → 21981.26 | **31-Dec** |
| `DEC15-P2` (flag FALSE) | 1 | 2024-12-15 → 2025-01-15 | 1200000.00 | **21983.20** | **21983.20** | 21981.26 | 31-Dec |
| `R13-P1` / `-P2` | 1 | 2023-12-15 → 2025-01-15 | 1200000.00 | 281214.25 | `16/365 + 366/366 + 15/365` → 281214.25 | `17/365 + 366/366 + 14/365` → 281214.25 | **both agree** |
| `R13-P1` / `-P2` | 2 | 2025-01-15 → 2026-02-15 | 662929.90 | 155354.44 | `350/365 + 46/365` → 155354.44 | `351/365 + 45/365` → 155354.44 | **both agree** |

**Tally over the crossing periods where the two readings differ: 31-December 6, 1-January 0,
neither 0.** Four further crossing periods (the `R13` ones) are recorded as **discriminating
nothing** — the segments they move sit in years of *equal* length, so the two readings coincide.
That is T48-N4's rule reappearing, and it is reported rather than counted as evidence.

The re-derivation is failable: negative test **N7** feeds it a plausible fabricated value
(`22013.00`, between the two readings) and shows it matching neither.

*(Corroboration, not evidence I produced: the committed `T48B-AA1-p7-raw.json` — product 7, flag
`f`, same shape — carries `totalInterestCharged 76160.63`, and every AA1 capture here reproduces
exactly that, on the flag-TRUE product too. T48's Path A2 twin with the flag actually bound recorded
76158.97.)*

---

## Item 1 — verdict: is the alias behaviourally reachable?

**The slot is reachable and load-bearing; the product setting that shares its name is not.** Both
statements are needed and both are now observed:

1. **The slot is read, and what it holds moves money.** The `31-Dec`/`1-Jan` re-derivations differ
   by MNT 1.63–1.94 in period-1 interest on these shapes, and the arm-vs-no-arm control moves 79 of
   153 cells. So this is not a dead branch: a port that got the boundary wrong would diverge.
2. **On 8 shapes × both readers, the product flag and the request override move 0 cells**, and the
   oracle's arithmetic matches the `false` reading on 6 of 6 discriminating periods **even when the
   product flag is `true`**. The slot never receives the product setting.

So T48-N1's `[UNVERIFIED]` server-side consequence is now resolved, and resolved in the **opposite
direction to the one a reader would assume from the field name**: it is not that "a Path B schedule
would move if the two aliased settings differed" — on the two readers reachable from
`calculateLoanSchedule`, the product setting can never reach the slot at all, so it cannot differ
*into* it. What could still move the slot is the **tenant-global** configuration
`interest-charged-from-date-same-as-disbursal-date`, which is `false` on `gerege` and which this task
**did not** write (the brief forbids writing tenant configuration, and a sibling worker shares the
server).

**The second reader is worth stating separately, because it is aliased twice.** At
`ProgressiveEMICalculator.java:194` the slot's value is copied into
`new LoanApplicationTerms.Builder().interestRecognitionOnDisbursementDate(…)`, and that object is
then passed through `generateTemporaryScheduleModel` → `toLoanConfigurationDetails()`
[VERIFIED: `:1099-1106`] — which reads `isInterestChargedFromDateSameAsDisbursalDateEnabled` again.
The `Builder`-based constructor [VERIFIED: `LoanApplicationTerms.java:304-351`] **never assigns**
`isInterestChargedFromDateSameAsDisbursalDateEnabled` (the field is only assigned at `:847`, from the
positional constructor), so on that path it is `null` and `:1753` yields `false` unconditionally.
**Re-derived from source; the observation is consistent with it** (products 20 and 21, arm firing,
0 of 164 cells) but the observation alone cannot distinguish "always false" from "false because the
global config is false". Marked accordingly in §Unverified.

---

## What a Go port must do differently

Stated as behaviour to reproduce, in terms DEC-1 would need. **This is not a DEC-1 amendment and
proposes none**; it is the raw finding a properly-gated decision would consume.

1. **Do not wire the schedule generator's `interestRecognitionOnDisbursementDate` input to the loan
   product's field of that name.** On the progressive `calculateLoanSchedule` path the oracle feeds
   that input from the **tenant-global** configuration
   `interest-charged-from-date-same-as-disbursal-date`. A port that wires the correctly-named getter
   diverges the moment the two disagree — and the two are in different configuration scopes, so
   "keep them in step" is not available as a mitigation.
2. **The year-segment boundary is 31 December** whenever that input is false, which on any tenant
   with the global configuration off (as `gerege` has it) is **always**, regardless of the product
   or request setting. Observed: 6 of 6 discriminating periods.
3. **The product/request `interestRecognitionOnDisbursementDate` is inert on this path.** A port may
   accept and persist it (Fineract does), but must not let it reach the schedule. The
   request-level override [`LoanScheduleAssembler.java:537-541`] is inert too — observed, both
   directions.
4. **This is bug-for-bug territory.** The oracle's behaviour is the specification while Fineract is
   the fallback; a port that "fixes" the alias produces different money on every ACT/ACT loan whose
   period crosses a calendar year, on a tenant where the global switch is on. If the program ever
   wants the corrected semantics, that is a deliberate divergence to be gated, not a port detail.
5. **A conformance vector for this rule must cross a leap-year boundary with segments of unequal
   year length.** Shapes whose crossing sits inside a run of equal-length years score a port
   identically under both boundary readings — observed on 4 of 10 crossing periods here (`R13`).
6. **The second reader carries the same hazard.** `allowFullTermForTranche` re-ages the schedule
   (52 of 164 cells) and reads the same aliased slot; a port must not let the product field reach it
   there either.

---

## Item 2 — `chargeCalculationType` 5

### 2.1 The contradiction, re-observed by this task

Three `POST /charges` attempts at `chargeCalculationType` 5 on `chargeTimeType` 1, 2 and 8 were
**all rejected, HTTP 400**, creating nothing:

```
"The parameter `chargeCalculationType` must not be any of [ 5 ] ."
userMessageGlobalisationCode: validation.msg.charge.chargeCalculationType.is.one.of.unwanted.enumerations
parameterName: chargeCalculationType
```

The rejecting site, re-opened: `ChargeDefinitionCommandFromApiJsonDeserializer.performChargeTimeN
CalculationTypeValidation` [VERIFIED: `fineract-charge/.../ChargeDefinitionCommandFromApiJsonDeserializer.java:482-497`],
the `else` branch at **`:493-495`** — `isNotOneOfTheseValues(PERCENT_OF_DISBURSEMENT_AMOUNT.getValue())`
for every `chargeTimeType` other than `TRANCHE_DISBURSEMENT`, whose own allowed set is
`{FLAT (1), PERCENT_OF_DISBURSEMENT_AMOUNT (5)}` [VERIFIED: `ChargeCalculationType.java:82-84`].
The same request has already passed `validValuesForLoan()`, which **lists 5**
[VERIFIED: `ChargeCalculationType.java:60-64`]. T48-N2 confirmed, independently, from the oracle.

**So type 5 is reachable only at `chargeTimeType` 12.** T48's charge id **13** (unmodified) is that
definition, and this task created id **14** (`FLAT` at `chargeTimeType` 12) as the other admissible
tranche charge.

### 2.2 The tranche product did NOT separate it — and that is finding one

A real multi-disbursement product (id **19**, `allow_multiple_disbursals = t`, `max_disbursals = 3`)
with **three genuine tranches** (500,000 / 300,000 / 400,000 on 3 dates):

| capture | charge | `totalFeeChargesCharged` | disbursement rows (exact text) |
|---|---|---|---|
| `TR-00-ctrl` | none | `0.00` | `0` `0` `0` |
| `TR-01-c5-tranche` | id 13, ct **5**, 1.2345 % | `14814.00` | `14814.000000` ×3 |
| `TR-02-c2-comparator` | id 3, ct **2**, 1.2345 % | `14814.00` | `14814.000000` ×3 |
| `TR-03-c1flat-tranche` | id 14, ct **1**, 7000 | `21000.00` | `21000` ×3 |
| `TR-06` — same request on **product 1** (single-disbursement) | id 13, ct 5 | `14814.00` | `14814.000000` ×3 |

* **`TR-01` vs `TR-02`: 0 of 302 cells differ.** The comparison T48 said needed a tranche product
  has one, and still discriminates nothing.
* **`TR-01` vs `TR-06`: 0 of 302 cells differ.** The multi-disbursement *product* was not needed at
  all — `disbursementData` on the request produces the identical tranche schedule on the ordinary
  single-disbursement product 1. What the product flag governs is whether `disbursementData` is
  **mandatory**: `TR-05` (product 19, no `disbursementData`) is **HTTP 403**,
  *"For this loan product, disbursement details must be provided"* (`error.msg.disbursementData.required`),
  while T48-CH-10 on product 1 returned 200.
* The charge did land (`TR-01` vs `TR-00`: **23 of 302 cells**), and FLAT is distinguishable from
  type 5 (`TR-03` vs `TR-01`: **23 of 302**), so the zero is a fact about the oracle, not a broken
  comparator. Negative test **N8** and **N3** (corrupting 1.2345 → 9.9999 moves
  `totalFeeChargesCharged` to `119998.80`) confirm that.

**Why.** `LoanChargeAssembler` [VERIFIED: `LoanChargeAssembler.java:190-204`] creates **one
`LoanCharge` per disbursement detail** for `chargeTimeType` 12, each with
`loanPrincipal = disbursementDetail.getPrincipal()`. So type 5 really is *per tranche* — and
`Σ_i p·t_i = p·Σ_i t_i`, which is exactly the type-2 reading whenever the tranches sum to the loan
principal. **Linearity hid it, not the absence of tranches.** (FLAT is visibly per-tranche:
7000 × 3 = `21000`.)

### 2.3 Two shapes that DO separate type 5 from type 2 — finding two

**(a) tranches that do not sum to the principal.** Request `principal` 1,200,000 with
`disbursementData` 400,000 + 300,000 + 300,000 = **1,000,000**:

| capture | charge | `totalFeeChargesCharged` |
|---|---|---|
| `TR-07-c5-tranches-sum-1000000` | ct **5** | **`12345.00`** ( = 1.2345 % of **1,000,000**, the sum of tranches ) |
| `TR-08-c2-tranches-sum-1000000` | ct **2** | **`14814.00`** ( = 1.2345 % of **1,200,000**, the loan principal ) |

**23 of 302 cells differ.** The oracle accepted the mismatch at HTTP 200 without complaint.

**(b) `minCap` / `maxCap` — a clamp is not linear.** Caps are copied from the definition onto
**every** `LoanCharge` [VERIFIED: `LoanChargeService.java:527-528`] and applied by
`LoanCharge.minimumAndMaximumCap` [VERIFIED: `LoanCharge.java:326-350`], so they clamp each tranche
charge separately. Tranches 500,000 / 300,000 / 400,000; 1.2345 % of each is 6172.5 / 3703.5 / 4938:

| capture | charge | `totalFeeChargesCharged` (**observed**) | re-derivation (mine) |
|---|---|---|---|
| `TR-09-c5-maxcap` | id 15, ct 5, `maxCap 5000` | **`13641.50`** | per tranche: `5000 + 3703.5 + 4938 = 13641.50` |
| `TR-10-c2-maxcap` | id 16, ct 2, `maxCap 5000` | **`5000.00`** | once: `min(14814, 5000) = 5000` |
| `TR-13-c5-maxcap-onetranche` | id 15, one tranche of 1,200,000 | **`5000.00`** | isolates "the cap binds" from "the cap is per tranche" |
| `TR-11-c5-mincap` | id 17, ct 5, 0.1 %, `minCap 8000` | **`24000.00`** | per tranche: `8000 × 3` |
| `TR-12-c2-mincap` | id 18, ct 2, 0.1 %, `minCap 8000` | **`8000.00`** | once: `max(1200, 8000)` |

`TR-09` vs `TR-10`: **23 of 302 cells**. `TR-11` vs `TR-12`: **23 of 302**. `TR-09` vs `TR-01`
(cap vs no cap): **23 of 302**, so the cap binds. `TR-09` vs `TR-13`: **254 of 326**.

### 2.4 Two further raw observations from these captures

* **The disbursement-row fee scale is caller-controlled, again** (T46-N2, T48-N5): `14814.000000`
  and `12345.000000` and `13641.500000` at **scale 6**, `21000` at **scale 0**, while every other
  money field on the same row is scale 2. This is why the whole comparison is done on exact-text
  sidecars and never through a JSON number.
* **The aggregate charge total is repeated on EVERY disbursement row**, so
  `Σ totalDueForPeriod` triple-counts it: `1364661.850000` against a `totalRepaymentExpected` of
  `1335033.85` on `TR-01`/`TR-02`/`TR-06`, and `1383219.85` vs `1341219.85` on `TR-03`. The
  single-tranche `TR-04` agrees exactly. This extends T40's finding 1 to tranche schedules; no claim
  is made here about which of the two is "right".

---

## Item 3 (if reached)

**Reached, and both halves landed.**

**`minCap` / `maxCap`** — captured above (§2.3b). Open on the gap list since T44; now observed on
four captures with the caps binding, plus a control where a single tranche makes the two readings
coincide.

**`fixedLength`** — the reason it was never captured is a guard nobody had recorded. Sent on an
interest-bearing request it is **HTTP 403**:

```
"Fixed Length configuration is only allowed for zero interest products"
error.msg.fixed.length.only.supported.for.zero.interest
```

[VERIFIED: `LoanProductDataValidator.java:2784-2787`, reached from
`LoanApplicationValidator.fixedLengthValidations` `:819-834`.] Crucially `thereIsInterest` is derived
from the **request's** `interestRatePerPeriod` [VERIFIED: `:829-830`], not from the product — so no
new product was needed. The second guard is
`fixedLength >= ((numberOfRepayments - 1) * repayEvery) + 1` [VERIFIED: `:2790-2796`]; `fixedLength 11`
against 12 × 1 is **HTTP 403**, *"Wrong configuration between Number Of Repayments: 12 * 1 and Fixed
Length: 11 values"*.

At zero interest, `fixedLength` **stretches the final period's due date** and nothing else:

| capture | `loanTermInDays` | last period | cells vs control |
|---|---|---|---|
| `FL0-CTRL` (no `fixedLength`) | `365` | 2026-12-01 → **2027-01-01** | — |
| `FL0-12` | `365` | 2026-12-01 → **2027-01-01** | **0 of 280 — discriminates nothing** |
| `FL0-18` | `546` | 2026-12-01 → **2027-07-01** | **3 of 280**: `loanTermInDays`, `row12.daysInPeriod` (31 → 212), `row12.dueDate` |
| `FL0-365` | `11109` | 2026-12-01 → **2056-06-01** | 3 of 280 vs `FL0-18` |

So `fixedLength` is expressed in the repayment frequency unit (months here), it changes **only the
final due date, the final period's day count and the term in days**, and at the natural term it is a
no-op. Interest is `0.00` throughout by construction, so **these captures say nothing about how
`fixedLength` interacts with interest** — that combination is unreachable, by the validator above.

---

## Negative tests / failability

`bin/t51-negative.sh`, output at `out/t51/NEGATIVE-TESTS.txt`. **8 of 8 pass.**

| # | what is broken on purpose | guard that caught it |
|---|---|---|
| N1 | preconditions run against tenant `default` | **exit 1 with 5 named breaches** — wrong timezone (`Asia/Kolkata`), `rounding-mode = 6` (HALF_EVEN), MySQL-era `schema_connection_parameters`, the JVM's own log line saying `HALF_EVEN`, and the canary not run |
| N2 | a payload with `"productId": 0` left in | the template-fill guard's predicate fires |
| N3 | charge amount corrupted 1.2345 → 9.9999 | response differs; `totalFeeChargesCharged` becomes `119998.80` — the comparison is not vacuous |
| N4 | a malformed payload | HTTP 400; `lib.sh`'s `post()` aborts on any non-200 rather than writing an error body as a capture |
| N5 | the P1/P2 matched-pair SQL assertion, run against products 17 and 8 | returns **0** — not a tautology |
| N6 | one sidecar leaf corrupted in memory | the exact-text identity check names `totalFeeChargesCharged` |
| N7 | a fabricated interest value (`22013.00`) between the two boundary readings | the discriminator matches **neither** |
| N8 | the full-cell comparator itself | reports 0 on the identical pair and **23** on the separating pair |

**Determinism.** `bin/t51-determinism.sh` re-issued **all 47** committed T51 requests against the
same running oracle: **47 of 47 reproduced byte for byte**, server state unchanged.

**Exact-text discipline (T44-X1, T46-N2).** Every raw capture has a `-exact.json` sidecar in which
every JSON number is re-emitted as a JSON **string** carrying the literal wire characters. No float
is constructed anywhere — `json.loads(…, parse_float=str, parse_int=str)` hands back the raw matched
literal. The raw bytes are never rewritten. The analysis re-checks every sidecar leaf for leaf
against the raw bytes and requires zero bare JSON numbers in the sidecar; all 47 pass.

---

## Server state: before/after counts and every id added

Read by read-only SQL, exactly as T46 and T48 did:

```
psql -d fineract_gerege -tAc "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)"

BEFORE (m_charge | m_loan | m_product_loan):   13 | 0 | 16
AFTER  (m_charge | m_loan | m_product_loan):   18 | 0 | 21
```

**Additions, all new ids, nothing modified and nothing deleted:**

| kind | id | what |
|---|---|---|
| product | **17** | `T51 IROD true` (`T5A`) — ACT/ACT + DAILY, PROGRESSIVE, `interest_recognition_on_disbursement_date = t` |
| product | **18** | `T51 IROD false` (`T5B`) — the matched comparator, flag `f` |
| product | **19** | `T51 tranche multidisburse` (`T5C`) — product 1's configuration plus `allow_multiple_disbursals = t`, `max_disbursals = 3` |
| product | **20** | `T51 FTT IROD true` (`T5D`) — as 17 plus multi-disburse and `allow_full_term_for_tranche = t` |
| product | **21** | `T51 FTT IROD false` (`T5E`) — the matched comparator for 20 |
| charge | **14** | `T51 flat TRANCHE disbursement` — tt 12, ct 1, 7000 |
| charge | **15** | `T51 pct of disbursement TRANCHE maxCap5000` — tt 12, ct 5, 1.2345, `max_cap 5000` |
| charge | **16** | `T51 pct of amount DISB maxCap5000` — tt 1, ct 2, 1.2345, `max_cap 5000` |
| charge | **17** | `T51 pct of disbursement TRANCHE minCap8000` — tt 12, ct 5, 0.1, `min_cap 8000` |
| charge | **18** | `T51 pct of amount DISB minCap8000` — tt 1, ct 2, 0.1, `min_cap 8000` |

**Three further `POST /charges` attempts were REJECTED (HTTP 400) and created nothing** — ct 5 at
chargeTimeType 1, 2 and 8. Full record in `out/t51/CREATED-IDS.txt`, `created-charges.txt`,
`created-charges-pass2.txt`.

**Not changed.** `m_loan` is 0 before and after every pass (each script asserts it and aborts
otherwise). Charge ids 1–13 are byte-unchanged: the digest of `id|name|charge_time_enum|
charge_calculation_enum|amount` over ids ≤ 13 is `f9f755e30680080a65b69c58f6f98153`. Products 1–16
untouched. **No `c_configuration` row was written** — `rounding-mode = 4`, `enabled`, still holds,
and the behavioural half-cent canary still returns `20925.05` after every pass. The containers were
never started, stopped, restarted, re-tenanted or reconfigured. Passes 3, 4 and 6 assert
before == after and created nothing at all.

**Write surface actually touched (all under the paths the brief allows):**
`.softhouse/capture/charges/bin/t51-*.{sh,py}`, `.softhouse/capture/charges/req/{prod,calc}-T51-*.json`,
`.softhouse/capture/charges/out/t51/**`, `.softhouse/capture/charges/out/t51-rerun/**`, and this
handoff. **Not touched:** `.softhouse/capture/mathcontext/**` (T50 owns it), every other
`.softhouse/capture/*` subtree, `docs/adr/**`, `nexus/**`, `.softhouse/reviews/**`, `tasks.json`,
`program.json`, `RESUME.md`, `reference-oracle.md`, `patterns.md`, `gates.md`, `LOCK`.

---

## Unverified

* **That the tenant-global `interest-charged-from-date-same-as-disbursal-date` would move the slot
  if it were `true`.** Re-derived from source (`LoanScheduleAssembler.java:370-371` → `:559` →
  `LoanApplicationTerms.java:847` → `:1753`); **not observed**, because observing it means writing
  tenant configuration on a server a sibling worker shares, which the brief forbids. `[UNVERIFIED]`
  — and it is the single most valuable thing left to capture about this alias. `TO_BE_CAPTURED`.
* **That on the `allowFullTermForTranche` path the slot is `false` *unconditionally*** (because the
  `Builder` never assigns `isInterestChargedFromDateSameAsDisbursalDateEnabled`
  [`LoanApplicationTerms.java:304-351`], rather than merely because the global config is off).
  Re-derived from source; the observation (0 of 164 cells) is consistent with both explanations and
  cannot separate them while the global config is `false`. `[UNVERIFIED]`
* **That `:1579` and `:194` are the ONLY readers of the aliased slot.** Established by grepping all
  main sources for `isInterestRecognitionOnDisbursementDate` and classifying each hit by receiver
  type. This program has had an "enumeration is complete" claim be wrong twice. `[UNVERIFIED as an
  exhaustiveness claim; each individual site listed is VERIFIED.]`
* **Anything about `chargeCalculationType` 5 on a PERSISTED loan.** `LoanChargeService.java:280-286`
  yields `loanCharge.getTrancheDisbursementCharge().getloanDisbursementDetails().getPrincipal()`
  when a `LoanTrancheDisbursementCharge` exists and `loan.getPrincipal()` otherwise — a branch the
  preview endpoint cannot exercise. Persisting a loan is outside this task's mandate. `[UNVERIFIED]`
* **That `fixedLength` does nothing but move the final due date.** Observed on four zero-interest
  captures only; the interest-bearing combination is refused by the validator, so no capture in this
  program can say what it does to interest. `[UNVERIFIED beyond the zero-interest case.]`
* **Whether the tranche fee repetition on every disbursement row (§2.4) is a rendering artefact or
  a charging one.** Only the schedule preview was observed. `[UNVERIFIED]`
* **That the negative tests would reject a correctly-configured run of a *wrong* oracle.** No fire
  has a second Fineract build to test that against. `[UNVERIFIED]`

---

## Follow-ups and remaining TO_BE_CAPTURED

**Closed by this task**

* T48's *"whether the server keeps `interestRecognitionOnDisbursementDate` and
  `isInterestChargedFromDateSameAsDisbursalDateEnabled` in step"* — **closed**, and the answer is
  that they are in different configuration scopes and the product one never reaches the slot.
* T48's *"a separating shape for `chargeCalculationType` 5 needs a multi-disbursement (tranche)
  product"* — **closed, and the premise was wrong on both counts**: the tranche product does not
  separate it, and a persisted loan is not required. Two separating shapes are captured.
* T44/T46/T48's `minCap` / `maxCap` — **closed**.
* T44/T46/T48's `fixedLength` — **closed for zero-interest products**; the interest-bearing case is
  *not capturable*, with the validator cited, rather than `TO_BE_CAPTURED`.

**Still `TO_BE_CAPTURED`**

* **The tenant-global `interest-charged-from-date-same-as-disbursal-date` set to `true`.** Needs a
  tenant write, so it needs either an exclusive fire or a throwaway container. It is the only way to
  observe the alias *delivering* a different value, and it would upgrade §"What a Go port must do
  differently" item 2 from "always 31-Dec on this tenant" to a witnessed two-sided rule.
* **N46-1, the ambient charge rounding mode** — unchanged from T46/T48; needs a tenant write.
* **`chargeCalculationType` 5 on a persisted loan with real tranche disbursements**, to reach
  `LoanChargeService.java:280-283`'s non-null `TrancheDisbursementCharge` branch. Requires
  persisting a loan; recorded rather than attempted.
* **Whether `allowFullTermForTranche` re-aging conserves principal.** Raw observation from
  `T51-FTTP-P4`: `totalRepaymentExpected 1098842.93` against 1,200,000 disbursed, over 6 periods,
  while the arm-off twin gives `1266814.98`. Not this task's question and no claim is made, but it
  should not go unrecorded.
* **`chargeTimeType` 9 (`OVERDUE_INSTALLMENT`)** — unchanged from T40/T46/T48 (HTTP 403 at
  definition time).
* **`Asia/Hovd`**, down payments, interest recalculation, the cumulative generator — unchanged.

**Reproduce**

```
sh  .softhouse/capture/charges/bin/t51-mkfixtures.sh     # fixtures, no oracle contact
sh  .softhouse/capture/charges/bin/t51-capture.sh        # pass 1: products 17/18/19, charge 14
sh  .softhouse/capture/charges/bin/t51-capture2.sh       # pass 2: charges 15-18, separating shapes
sh  .softhouse/capture/charges/bin/t51-capture3.sh       # pass 3: fixedLength
sh  .softhouse/capture/charges/bin/t51-capture4.sh       # pass 4: request-level allowFullTermForTranche
sh  .softhouse/capture/charges/bin/t51-capture5.sh       # pass 5: products 20/21
sh  .softhouse/capture/charges/bin/t51-capture6.sh       # pass 6: same-product control
python3 .softhouse/capture/charges/bin/t51-analyse.py    # sidecars + item 1 + item 2 pass 1
python3 .softhouse/capture/charges/bin/t51-analyse2.py   # item 2 pass 2 + item 3
python3 .softhouse/capture/charges/bin/t51-analyse3.py   # the second reader
sh  .softhouse/capture/charges/bin/t51-determinism.sh    # 47/47 byte-identical
sh  .softhouse/capture/charges/bin/t51-negative.sh       # 8/8 failability legs
```

Re-running the capture passes on a server that already has these ids will create **further** new
ids; the scripts are additive and never reuse or mutate one. Committed output lives in
`.softhouse/capture/charges/out/t51/` (`ANALYSE.txt`, `ANALYSE2.txt`, `ANALYSE3.txt`,
`DETERMINISM.txt`, `NEGATIVE-TESTS.txt`).
