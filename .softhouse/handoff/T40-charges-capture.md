# T40 — charges: the corpus's fee/penalty blind spot, closed by observation

**Task:** T40, branch `softhouse/T40-charges-capture`, worker `test_writer`.
**Fire:** local `20260819-080001`, Buyan's Mac. **The reference oracle (Fineract) WAS reachable and every
number below is an OBSERVATION made on it** — nothing is computed, extrapolated, interpolated or authored.
Oracle Database is prohibited and appears nowhere; the only engine touched is **PostgreSQL 18.3**.

> **RAW OBSERVED FORM ONLY. NOTHING WAS PROMOTED to the parity vector store and NOTHING is stored
> contract-shaped.** Gate G-1 is open, DEC-1 is UNRATIFIED, and the contract *shape* is exactly what is
> still being ratified — so shaping a capture to it would prejudge the thing under review. Every artefact
> in `.softhouse/capture/charges/` is a raw HTTP response body plus provenance about how it was obtained.
> Promotion is a separate decision and is explicitly not mine.

**Why this task existed.** T35 established that **every fee and every penalty in the entire committed
corpus is `0.00`**. `patterns.md`: *coverage is what a corpus can distinguish, never what it contains.* A
Go port could have got charge handling arbitrarily wrong and passed 100% of the corpus. This task removes
that blindness for the progressive schedule endpoint.

---

## 0. Headline

**Five behaviours were observed that no existing vector can see, and two of them are money-affecting
defects in the reference oracle itself.**

1. **`totalRepaymentExpected` is internally inconsistent with the periods it summarises.** A charge applied
   in the main schedule loop — every instalment fee, every flat or percent-of-amount specified-due-date
   charge, every penalty — raises `feeChargesDue`/`penaltyChargesDue` and `totalDueForPeriod` on its period
   and raises `totalFeeChargesCharged`/`totalPenaltyChargesCharged`, but **is not added to
   `totalRepaymentExpected`**. Only disbursement-time charges, and the two *separated* calculation types,
   are. **Observed on 15 of 21 captures** (invariant C5), and re-derived from source.  **[SUPERSEDED by T46 C-3: C5 is a discrimination PROBE, not an invariant -- DEC-1 rev 8's ratified C-1 forbids asserting it. See CORRECTIONS.]**
2. **A specified-due-date charge dated after the last due date is accepted (HTTP 200) and then silently
   vanishes.** `FC-17` is **byte-identical to the zero-charge control**. The API's only date guard rejects
   dates *before* disbursement; there is no upper bound.
3. **A percent-of-interest specified-due-date charge dated on the disbursement date also silently
   vanishes** (`FC-20`, byte-identical to the control) — while a *flat* charge on the same date lands in
   period 1 with its full amount (`FC-11`). Two charges, same due date, one paid and one lost, decided
   solely by calculation type. Root cause re-derived: the separated path runs after the loop, when
   `isFirstPeriod()` is already false.
4. **Charges never touch the money core.** Across all 21 captures the principal split, the interest, the
   outstanding principal balance and the EMI are **cell-for-cell identical to the zero-charge control**
   (invariants C8/C9). A charge sits *alongside* the EMI, never inside it.
5. **The rounding locus is observable and it differs between two charges that describe the same thing.**
   "3.75 % of interest" totals **5,437.06** as a per-instalment charge (twelve roundings summed) and
   **5,437.07** as a specified-due-date charge (one rounding of the whole-term interest). Likewise
   1.2345 % of amount-plus-interest: **16,603.92** vs **16,603.88**, four minor units apart.

---

## 1. Preconditions — run FIRST, as required

`bin/preconditions.sh` is **T36's script copied byte-verbatim** from `.softhouse/capture/pathb/t36/`
(read-only to this task); `bin/run-preconditions.sh` is only a wrapper that supplies `CANARY_REQ` and the
tenant. It was run before *every* create and *every* capture in this task, and a breach aborts the caller.

**Result: 21 of 21 assertions PASS, exit 0** [VERIFIED: `.softhouse/capture/charges/out/preconditions-T40.txt`,
re-run per script into `out/control/preconditions.txt`, `out/charges/preconditions.txt`,
`out/charges/preconditions-pass2.txt`, `out/fc/preconditions.txt`, `out/attested/preconditions.txt`].

Load-bearing values it asserted, each from a primary source:

| assertion | observed |
|---|---|
| image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| jar `git.commit.id` / `git.dirty` | `426a23544e8426a38ae43ae404670a0a7e85b9eb` / `false` |
| `MoneyHelper.PRECISION` (deployed bytecode, `javap`) | **19** |
| tenant | `gerege`, timezone **`Asia/Ulaanbaatar`** (zone id; no offset hard-coded) |
| `c_configuration.rounding-mode` | **4** = `HALF_UP`, enabled |
| mode in force this JVM run | `HALF_UP` (MoneyHelper init line, `2026-08-18T09:53:01.711Z`) |
| **behavioural half-cent canary** | **`20925.05`** — the arithmetic itself answering `HALF_UP` |
| `schema_connection_parameters` | empty |
| PostgreSQL | `18.3 (Debian 18.3-1.pgdg13+1)`, `server_version_num 180003`, `org.postgresql.Driver`, `jdbc:postgresql://db:5432/…` |
| prohibited engines | **0** hits in container env, **0** prohibited driver jars in the boot jar |

Effective **`MathContext(19, HALF_UP)`** — the ratified production setting
[VERIFIED: `out/attested/attestation.json` → `effective_math_context.matches_ratified_production_setting: true`].

---

## 2. Zero-charge control — run BEFORE anything was created

`bin/control.sh` sends the four **committed** Path B calc requests **byte-verbatim** from
`.softhouse/capture/pathb/req/` through T40's own harness and compares the responses to the committed
capture files. *patterns.md: re-emit input-for-input before you add cases.*

**CONTROL PASSED — 4 of 4 byte-for-byte identical** [VERIFIED: `out/control/`]:

| capture | response SHA-256 | == committed corpus |
|---|---|---|
| B-01 baseline | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | **yes** |
| B-02 multiplesOf 100 | `9de8757deeb02476d48e4c84a42b297cc99fab9a286adb505c005ab8d99d02f8` | **yes** |
| B-03 `FULL_LEAP_YEAR` | `892dd6f537ef34f50f6c46258d054e620565951e671b414184f0ffb9f7da58bf` | **yes** |
| B-04 `FEB_29_PERIOD_ONLY` | `c80f62b01721ab15e994dcf7fca5d5f3f60ada39aa210ca45bbb67b65c724a80` | **yes** |

These are the same four digests T36 attested. **The harness is not a variable**, so every difference
reported below is caused by the charge and by nothing else — each `FC-nn` request is the committed
`calc-B-01-baseline.json` with **only** a `charges` array injected, by pure text substitution on one
anchor line (`bin/mkcalcs.sh`, `bin/mkcalcs2.sh`). No JSON parse, no re-serialise, no float.

---

## 3. What I created on the tenant (additive only — every id, so a later fire can find them)

`select count(*) from m_charge` in `fineract_gerege` was **0** before this task, so **charge ids 1–12 are
exactly T40's** and nothing pre-existing was mutated. No product, no tenant, no configuration row and no
schema object was created, changed or deleted; the server was **not** restarted (uptime 14 h at the end of
the task, `fineract-db-1` 37 h); the `default` tenant was not touched.

| id | name | `charge_time_enum` | `charge_calculation_enum` | amount | penalty |
|---|---|---|---|---|---|
| 1 | T40 flat fee at disbursement | 1 DISBURSEMENT | 1 FLAT | `15000.000000` | no |
| 2 | T40 flat fee per instalment | 8 INSTALMENT_FEE | 1 FLAT | `2500.000000` | no |
| 3 | T40 percent of amount at disbursement | 1 DISBURSEMENT | 2 PERCENT_OF_AMOUNT | `1.234500` % | no |
| 4 | T40 percent of interest per instalment | 8 INSTALMENT_FEE | 4 PERCENT_OF_INTEREST | `3.750000` % | no |
| 5 | T40 percent of amount plus interest per instalment | 8 INSTALMENT_FEE | 3 PCT_OF_AMOUNT_AND_INTEREST | `1.234500` % | no |
| 6 | T40 PENALTY flat on specified due date | 2 SPECIFIED_DUE_DATE | 1 FLAT | `7500.000000` | **yes** |
| 7 | T40 flat fee on specified due date | 2 SPECIFIED_DUE_DATE | 1 FLAT | `9000.000000` | no |
| 8 | T40 PENALTY flat per instalment | 8 INSTALMENT_FEE | 1 FLAT | `1200.000000` | **yes** |
| 9 | T40 percent of amount per instalment | 8 INSTALMENT_FEE | 2 PERCENT_OF_AMOUNT | `0.500000` % | no |
| 10 | T40 percent of amount on specified due date | 2 SPECIFIED_DUE_DATE | 2 PERCENT_OF_AMOUNT | `1.234500` % | no |
| 11 | T40 percent of interest on specified due date | 2 SPECIFIED_DUE_DATE | 4 PERCENT_OF_INTEREST | `3.750000` % | no |
| 12 | T40 percent of amount plus interest on specified due date | 2 SPECIFIED_DUE_DATE | 3 PCT_OF_AMOUNT_AND_INTEREST | `1.234500` % | no |

All `chargeAppliesTo = 1` (LOAN), `chargePaymentMode = 0` (REGULAR), `currencyCode = MNT`, active
[VERIFIED: `out/attested/attestation.json` → `charges_as_persisted`, read as `to_jsonb` rows from
PostgreSQL with a SHA-256 per row; **the `amount` column holds a PERCENTAGE for calculation types 2/3/4**].

State after the task [VERIFIED: `psql`]: `fineract_gerege` — `m_charge` 12, `m_product_loan` 16 (all T22's
and T36's, unchanged), **`m_loan` 0**, **`m_loan_charge` 0** (`calculateLoanSchedule` is a pure calculation
endpoint; nothing was persisted). `fineract_default` — `m_charge` 0, `m_product_loan` 10, `m_loan` 0.

**Two things the API forced on me, both observed, not assumed:**

* `amount` is **mandatory** on every element of the loan application's `charges` array. Omitting it returns
  HTTP 400 `validation.msg.loan.charges.amount.cannot.be.blank`. Every request therefore repeats the
  definition's amount as exact decimal text.
* A specified-due-date charge dated **before** the disbursement date is refused: HTTP 403
  `error.msg.loanCharge.cannot.be.added.as.specified.due.date.outside.range`
  [VERIFIED: `out/XR-01-fee-before-disbursement-HTTP403.json`; filed as a **refusal**, never as a capture].

---

## 4. The captures

21 accepted captures + 1 refusal. Every request is the committed B-01 baseline (product 1, client 1,
principal 1,200,000 MNT, 12 monthly repayments, 21.6 % p.a., disbursed `01 January 2026`) plus a `charges`
array. Raw bodies in `.softhouse/capture/charges/out/fc/`; a third independent issue of every one is in
`out/attested/` alongside the attestation.

| id | charge under test | what it discriminates |
|---|---|---|
| FC-01 | flat 15,000 at DISBURSEMENT | which period a disbursement charge lands in; whether it alters the EMI |
| FC-02 | flat 2,500 per INSTALMENT | per-period repetition; EMI vs total-due separation |
| FC-03 | 1.2345 % of amount at DISBURSEMENT | percentage base for a disbursement charge |
| FC-04 | 3.75 % of interest per INSTALMENT | whether the base is the *period's* interest; rounding locus |
| FC-05 | 1.2345 % of amount+interest per INSTALMENT | whether the base is the period's principal+interest |
| FC-06 | **PENALTY** 7,500, due **15 Mar 2026** (strictly inside period 3) | fee/penalty column separation; interior date membership |
| FC-07 | fee 9,000, due **01 Apr 2026** (= period 3 dueDate = period 4 fromDate) | upper boundary: which of two adjacent periods |
| FC-08 | **PENALTY** 1,200 per INSTALMENT | penalties repeat like fees, in their own column |
| FC-09 | 0.5 % of amount per INSTALMENT | base = the period's principal, not the whole principal |
| FC-10 | 1.2345 % of amount, due **15 Jun 2026** (inside period 6) | base for a specified-due-date percentage |
| FC-11 | fee 9,000, due **01 Jan 2026** (= disbursement date = period 1 fromDate) | lower boundary of the FIRST period |
| FC-12 | fee 9,000, due **01 Jan 2027** (= final dueDate) | last period, upper boundary |
| FC-13 | fee 9,000, due **31 Dec 2026** (inside period 12) | interior of the last period |
| FC-14 | fee 9,000, due **20 Jan 2026** (inside period 1) | interior of the first period |
| FC-15 | 1 + 2 + 6 + 8 together | fee and penalty simultaneously; additivity within a period |
| FC-16 | fee 9,000, due **01 Feb 2026** (= period 1 dueDate = period 2 fromDate) | first-period upper boundary |
| FC-17 | fee 9,000, due **01 Mar 2027** (two months past the end) | off-the-end: dropped, or clamped to the last period? |
| FC-19 | 3.75 % of interest, SPECIFIED_DUE_DATE, due 15 Jun 2026 | the *separated* code path; whole-term interest base |
| FC-20 | 3.75 % of interest, SPECIFIED_DUE_DATE, due **01 Jan 2026** | first-period boundary **on the separated path** |
| FC-21 | 1.2345 % of amount+interest, SPECIFIED_DUE_DATE, due 15 Jun 2026 | separated path, second calculation type |
| FC-22 | penalty per instalment **+** penalty on a period boundary | two penalties summing into one period |
| XR-01 | fee 9,000, due **15 Dec 2025** (before disbursement) | the date guard — **refused, HTTP 403** |

Full-cell tables for all of them: **`out/FULLCELL.md`** (every period, every column, plus every leaf that
moved against the control, in integer minor units). Fee/penalty columns side by side:
**`out/FEECOLS.md`**. Both are generated by exact-`Decimal` tools (`parse_float=Decimal`); no binary float
is constructed at any point.

---

## 5. Full-cell comparison — the shape of the check

`patterns.md`: *compare every cell, not the headline scalars — that comparison shape is what let a money
defect hide through five consecutive reviews.* `bin/fullcell.py` flattens each response to **286 leaves**
and compares every one against the control as an exact `Decimal` in integer minor units, with **no
tolerance**, distinguishing a moved number from a structural difference.

| capture | leaves compared | leaves moved vs the zero-charge control |
|---|---|---|
| FC-01 flat disbursement | 286 | **9** |
| FC-02 flat instalment | 286 | **80** |
| FC-03 pct-of-amount disbursement | 286 | **9** |
| FC-04 pct-of-interest instalment | 286 | **80** |
| FC-05 pct-of-amount+interest instalment | 286 | **80** |
| FC-06 penalty inside period 3 | 286 | **8** |
| FC-07 fee on period 3 dueDate | 286 | **8** |
| FC-08 penalty per instalment | 286 | **80** |
| FC-09 pct-of-amount per instalment | 286 | **80** |
| FC-10 pct-of-amount inside period 6 | 286 | **8** |
| FC-11 fee on the disbursement date | 286 | **8** |
| FC-12 fee on the final dueDate | 286 | **7** |
| FC-13 fee inside period 12 | 286 | **7** |
| FC-14 fee inside period 1 | 286 | **8** |
| FC-15 combined fee + penalty | 286 | **113** |
| FC-16 fee on period 1 dueDate | 286 | **8** |
| **FC-17 fee after the final dueDate** | 286 | **0** |
| FC-19 pct-of-interest SDD inside period 6 | 286 | **9** |
| **FC-20 pct-of-interest SDD on the disbursement date** | 286 | **0** |
| FC-21 pct-of-amount+interest SDD inside period 6 | 286 | **9** |
| FC-22 two penalties | 286 | **80** |

The **two zero rows are the loudest result in the table**: the oracle accepted a charge with HTTP 200 and
returned a schedule that is byte-identical to the schedule with no charge at all.

### Worked example — FC-01, the whole plan (all 13 rows, all columns)

| period | fromDate | dueDate | days | principalDue | interestDue | **fee** | **penalty** | outstanding principal | totalDueForPeriod | EMI |
|---|---|---|---|---|---|---|---|---|---|---|
| — (disbursement) | — | 2026-01-01 | — | — | — | **15000.00** | — | 1200000.00 | 15000.00 | — |
| 1 | 2026-01-01 | 2026-02-01 | 31 | 90482.37 | 21600.00 | 0.00 | 0.00 | 1109517.63 | 112082.37 | 112082.37 |
| 2 | 2026-02-01 | 2026-03-01 | 28 | 92111.05 | 19971.32 | 0.00 | 0.00 | 1017406.58 | 112082.37 | 112082.37 |
| 3 | 2026-03-01 | 2026-04-01 | 31 | 93769.05 | 18313.32 | 0.00 | 0.00 | 923637.53 | 112082.37 | 112082.37 |
| 4 | 2026-04-01 | 2026-05-01 | 30 | 95456.89 | 16625.48 | 0.00 | 0.00 | 828180.64 | 112082.37 | 112082.37 |
| 5 | 2026-05-01 | 2026-06-01 | 31 | 97175.12 | 14907.25 | 0.00 | 0.00 | 731005.52 | 112082.37 | 112082.37 |
| 6 | 2026-06-01 | 2026-07-01 | 30 | 98924.27 | 13158.10 | 0.00 | 0.00 | 632081.25 | 112082.37 | 112082.37 |
| 7 | 2026-07-01 | 2026-08-01 | 31 | 100704.91 | 11377.46 | 0.00 | 0.00 | 531376.34 | 112082.37 | 112082.37 |
| 8 | 2026-08-01 | 2026-09-01 | 31 | 102517.60 | 9564.77 | 0.00 | 0.00 | 428858.74 | 112082.37 | 112082.37 |
| 9 | 2026-09-01 | 2026-10-01 | 30 | 104362.91 | 7719.46 | 0.00 | 0.00 | 324495.83 | 112082.37 | 112082.37 |
| 10 | 2026-10-01 | 2026-11-01 | 31 | 106241.45 | 5840.92 | 0.00 | 0.00 | 218254.38 | 112082.37 | 112082.37 |
| 11 | 2026-11-01 | 2026-12-01 | 30 | 108153.79 | 3928.58 | 0.00 | 0.00 | 110100.59 | 112082.37 | 112082.37 |
| 12 | 2026-12-01 | 2027-01-01 | 31 | 110100.59 | 1981.81 | 0.00 | 0.00 | 0.00 | 112082.40 | 112082.40 |

Plan totals: `totalPrincipalExpected` 1,200,000.00; `totalInterestCharged` 144,988.47;
`totalFeeChargesCharged` **15,000.00**; `totalPenaltyChargesCharged` 0.00; `totalRepaymentExpected`
**1,359,988.47**; `loanTermInDays` 365. The **only** nine leaves that moved are the nine fee-bearing cells
of the disbursement pseudo-period plus the two fee totals — principal, interest, balances and the EMI are
untouched [VERIFIED: `out/FULLCELL.md` → FC-01].

---

## 6. The questions the brief asked, answered FROM OBSERVATION

### Q1. Does a charge alter the EMI, or sit alongside it?

**It sits alongside it. Observed, on every capture.** `totalInstallmentAmountForPeriod` is
`112082.37` for periods 1–11 and `112082.40` for period 12 on **all 21 captures** — cell-for-cell identical
to the zero-charge control (invariant C9, PASS 21/21). What moves is `totalDueForPeriod`.

FC-02 (flat 2,500 per instalment) is the clearest witness [VERIFIED: `out/FEECOLS.md` → FC-02]:

| period | EMI (`totalInstallmentAmountForPeriod`) | fee | `totalDueForPeriod` |
|---|---|---|---|
| 1–11 | 112082.37 | 2500.00 | **114582.37** |
| 12 | 112082.40 | 2500.00 | **114582.40** |

So a port that folds the charge into the annuity — or that treats `totalDueForPeriod` and
`totalInstallmentAmountForPeriod` as the same field — diverges on every single period the moment any
charge exists. No vector before today could see that, because every fee in the corpus was `0.00`.

*Mechanism, cited separately:* the charge is applied **after** the EMI is fixed —
`emiCalculator.findRepaymentPeriod(...)` sets principal and interest, then
`applyChargesForCurrentPeriod(...)` adds the charge
[VERIFIED: `fineract-progressive-loan/.../ProgressiveLoanScheduleGenerator.java:125-140`].

### Q2. Does a charge change the outstanding **principal** balance?

**No. Observed.** `principalDue`, `principalOriginalDue`, `interestDue` and
`principalLoanBalanceOutstanding` are cell-for-cell identical to the control on **all 21 captures**
(invariant C8, PASS 21/21) — including FC-01, where a 15,000 fee is due at disbursement and the
disbursement period still reports `principalLoanBalanceOutstanding` = 1,200,000.00, and including FC-15
where 66,900 of fees and penalties are due in total. `totalPrincipalExpected` is 1,200,000.00 everywhere
and `sum(principalDue)` equals it exactly (invariant C6, PASS 21/21) — **principal still amortises to
zero** in the presence of charges.

### Q3. Which period does a disbursement-date charge land in?

**Two different answers, decided by charge TYPE, not by the date.** This is the sharp result.

| capture | charge | due date | lands in |
|---|---|---|---|
| FC-01 | FLAT, `chargeTimeType = DISBURSEMENT` | (implicit) | **`periods[0]`, the disbursement pseudo-period** (`dueDate` 2026-01-01, no `period` number) |
| FC-03 | PERCENT_OF_AMOUNT, `DISBURSEMENT` | (implicit) | **`periods[0]`** — 14,814.00 |
| FC-11 | FLAT, `SPECIFIED_DUE_DATE` | **01 Jan 2026** (the disbursement date) | **period 1** — 9,000.00, and `periods[0]` fee stays `0.00` |
| FC-20 | PERCENT_OF_INTEREST, `SPECIFIED_DUE_DATE` | **01 Jan 2026** | **nowhere — silently dropped**, response byte-identical to the control |

So "the disbursement date" is not a period; `chargeTimeType` is. A port that routes by date rather than by
`chargeTimeType` puts FC-11's fee in the wrong row, and one that assumes symmetry between the two
percentage paths loses FC-20's fee entirely.

### Q4. Period membership for a specified-due-date charge

Observed, across six captures, and it is **not** a single interval rule:

| due date | relation to the periods | lands in | capture |
|---|---|---|---|
| 2026-01-01 | = period 1 `fromDate` (and the disbursement date) | **period 1** | FC-11 |
| 2026-01-20 | strictly inside period 1 | **period 1** (byte-identical to FC-11) | FC-14 |
| 2026-02-01 | = period 1 `dueDate` = period 2 `fromDate` | **period 1** (byte-identical to FC-11) | FC-16 |
| 2026-04-01 | = period 3 `dueDate` = period 4 `fromDate` | **period 3** | FC-07 |
| 2026-12-31 | strictly inside period 12 | **period 12** | FC-13 |
| 2027-01-01 | = period 12 `dueDate`, the final due date | **period 12** (byte-identical to FC-13) | FC-12 |
| 2027-03-01 | after the final due date | **nowhere — silently dropped** | FC-17 |
| 2025-12-15 | before the disbursement date | **refused, HTTP 403** | XR-01 |

The membership interval is therefore **`[fromDate, dueDate]` for the first period and `(fromDate, dueDate]`
for every other period** — half-open below, closed above, with the first period's lower bound made
inclusive so a charge on the disbursement date is not lost. FC-16 is the decisive one: `2026-02-01` is
simultaneously period 1's `dueDate` and period 2's `fromDate`, and it goes to **period 1**.

*Mechanism, cited separately:* `LoanCharge.isDueInPeriod` → `LoanRepaymentScheduleProcessingWrapper.isInPeriod`:
`isFirstPeriod ? isDateInRangeInclusive : isDateInRangeFromExclusiveToInclusive`
[VERIFIED: `fineract-loan/.../LoanCharge.java:371-373`; `fineract-loan/.../LoanRepaymentScheduleProcessingWrapper.java:251-254`].
The brief predicted this is where date-membership defects hide in this program; it is, and the corpus can
now tell the two ends of the interval apart.

### Q5. What base does each percentage use?

All observed [VERIFIED: `out/FEECOLS.md`]:

| calculation | charge time | observed base | witness |
|---|---|---|---|
| PERCENT_OF_AMOUNT | DISBURSEMENT | the **whole principal** — 1.2345 % × 1,200,000 = **14,814.00** | FC-03 |
| PERCENT_OF_AMOUNT | SPECIFIED_DUE_DATE | the **whole principal** — **14,814.00**, all of it in period 6 | FC-10 |
| PERCENT_OF_AMOUNT | INSTALMENT_FEE | **that period's `principalDue`** — 452.41, 460.56, 468.85, 477.28, 485.88, 494.62, 503.52, 512.59, 521.81, 531.21, 540.77, 550.50 | FC-09 |
| PERCENT_OF_INTEREST | INSTALMENT_FEE | **that period's `interestDue`** — 810.00, 748.92, 686.75, 623.46, 559.02, 493.43, 426.65, 358.68, 289.48, 219.03, 147.32, 74.32 | FC-04 |
| PERCENT_OF_INTEREST | SPECIFIED_DUE_DATE | the **whole-term interest** — 3.75 % × 144,988.47 = **5,437.07**, all of it in period 6 | FC-19 |
| PERCENT_OF_AMOUNT_AND_INTEREST | INSTALMENT_FEE | that period's principal + interest (= the EMI) — **1,383.66 on every period** | FC-05 |
| PERCENT_OF_AMOUNT_AND_INTEREST | SPECIFIED_DUE_DATE | principal + whole-term interest — 1.2345 % × 1,344,988.47 = **16,603.88** | FC-21 |

**The rounding locus is now observable.** FC-04 and FC-19 are the same nominal charge — 3.75 % of interest
— and differ by **one minor unit** in the total (5,437.06 vs 5,437.07), because one rounds twelve times and
sums while the other rounds once. FC-05 and FC-21 differ by **four** minor units (16,603.92 vs 16,603.88).
Invariant C1 confirms the per-instalment totals are the *sum of the rounded parts*, not a re-rounded whole:
`totalFeeChargesCharged` = Σ `feeChargesDue` exactly, on all 21 captures. A port that computes the total
independently of the periods gets FC-04 wrong by a tugrik-cent and FC-05 wrong by four.

*Mechanism, cited separately:* `calculateInstallmentCharge` uses `principalInterestForThisPeriod`;
`calculateSpecificDueDateChargeWithPercentage` uses `principalDisbursed` and
`totalInterestChargedForFullLoanTerm`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:433-452` and `:454-468`].

### Q6. Fee versus penalty — does the response really separate them?

**Yes, and additively within a period.** FC-15 combines charge 1 (flat 15,000 at disbursement), charge 2
(flat 2,500 per instalment), charge 6 (**penalty** 7,500 due 15 Mar 2026) and charge 8 (**penalty** 1,200
per instalment) [VERIFIED: `out/FEECOLS.md` → FC-15]:

| period | fee | penalty | totalDueForPeriod | EMI |
|---|---|---|---|---|
| — (disbursement) | 15000.00 | — | 15000.00 | — |
| 1, 2, 4–11 | 2500.00 | 1200.00 | 115782.37 | 112082.37 |
| **3** | 2500.00 | **8700.00** = 1200 + 7500 | **123282.37** | 112082.37 |
| 12 | 2500.00 | 1200.00 | 115782.40 | 112082.40 |

`totalFeeChargesCharged` **45,000.00** (= 15,000 + 12 × 2,500), `totalPenaltyChargesCharged` **21,900.00**
(= 12 × 1,200 + 7,500). Charges of the same kind sum within a period; the two kinds never mix columns.
FC-22 corroborates on penalties alone.

---

## 7. The two defects, stated plainly

### D-1 — `totalRepaymentExpected` omits every charge applied in the main loop

Invariant **C5** (`totalRepaymentExpected == Σ totalDueForPeriod`) **FAILS on 15 of 21 captures**  **[SUPERSEDED by T46 C-3: relabelled probe P5, reported as a signed delta. See CORRECTIONS.]**
[VERIFIED: `out/INVARIANTS.md`]. Observed, four different ways:

| capture | charge | `totalFeeChargesCharged` | `totalRepaymentExpected` | included? |
|---|---|---|---|---|
| control | none | 0.00 | 1,344,988.47 | — |
| FC-01 | flat, **DISBURSEMENT** | 15,000.00 | **1,359,988.47** (= +15,000.00) | **yes** |
| FC-03 | pct-of-amount, **DISBURSEMENT** | 14,814.00 | **1,359,802.47** (= +14,814.00) | **yes** |
| FC-02 | flat, INSTALMENT_FEE | 30,000.00 | 1,344,988.47 (unchanged) | **no** |
| FC-04 | pct-of-interest, INSTALMENT_FEE | 5,437.06 | 1,344,988.47 (unchanged) | **no** |
| FC-07 | flat, SPECIFIED_DUE_DATE | 9,000.00 | 1,344,988.47 (unchanged) | **no** |
| FC-10 | pct-of-amount, SPECIFIED_DUE_DATE | 14,814.00 | 1,344,988.47 (unchanged) | **no** |
| FC-08 | **penalty**, INSTALMENT_FEE | (penalty 14,400.00) | 1,344,988.47 (unchanged) | **no** |
| FC-19 | pct-of-interest, **SPECIFIED_DUE_DATE** | 5,437.07 | **1,350,425.54** (= +5,437.07) | **yes** |
| FC-21 | pct-of-amt+int, **SPECIFIED_DUE_DATE** | 16,603.88 | **1,361,592.35** (= +16,603.88) | **yes** |
| FC-15 | four charges, 66,900.00 total | 45,000.00 fee / 21,900.00 penalty | **1,359,988.47** (= +15,000.00 only) | **partly** |

FC-15 is the sharpest: 66,900 MNT of fees and penalties are shown as due across the periods and only the
15,000 disbursement fee reaches `totalRepaymentExpected`. **51,900 MNT is visible in the rows and absent
from the total.**

*Mechanism, re-derived from source (not read back from a comment):* on the progressive path
`applyChargesForCurrentPeriod` adds the charge to the period and to the two charge totals but **never calls
`addTotalRepaymentExpected`** [VERIFIED: `ProgressiveLoanScheduleGenerator.java:367-382` — the method body
is `addLoanCharges`, `addTotalFeeChargesCharged`, `addTotalPenaltyChargesCharged`, and nothing else]. The
running total is seeded with the disbursement charges only
[VERIFIED: `fineract-loan/.../LoanScheduleParams.java:211` and `:246` — `final Money totalRepaymentExpected
= chargesDueAtTimeOfDisbursement;`] and then accumulates principal + interest per period
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:137`]. The **only** charge contribution after the seed
comes from `updatePeriodsWithCharges`, which serves just the separated calculation types
[VERIFIED: `:486`]. The cumulative (non-progressive) generator does add them
[VERIFIED: `fineract-loan/.../AbstractCumulativeLoanScheduleGenerator.java:504`], so **the two generators  **[SUPERSEDED by T46 C-4: `:504` is the site of AGREEMENT. The disagreement is the cumulative MAIN LOOP at `:392` with `ScheduleCurrentPeriodParams.java:144-145`. See CORRECTIONS.]**
disagree** — which is itself a reason not to "fix" this in the Go port without a decision.

**Consequence for the port and for DEC-1:** `totalRepaymentExpected` is **not** the sum of the period
totals and must not be modelled as a derived sum. Whatever DEC-1 says this field means, it has to say which
of the two Fineract behaviours the port reproduces, and a parity vector must pin it. I did not touch
`docs/adr/**` — T38 owns DEC-1 this fire.

### D-2 — two ways to lose a charge silently

**D-2a, off the end.** `FC-17` — a 9,000 fee dated `01 March 2027`, two months past the final due date —
returns HTTP 200 and a response **byte-identical to the zero-charge control** (`713a3560…c062009`), with
`totalFeeChargesCharged` `0.00`. The charge is not clamped to the last period and not rejected; it is
simply gone. *Mechanism:* the only date guard is one-sided —
`if (loanCharge.isSpecifiedDueDate() && DateUtils.isBefore(loanCharge.getDueLocalDate(), disbursementDate))`
[VERIFIED: `fineract-loan/.../serialization/LoanChargeValidator.java:59-67`]. XR-01 shows the *before* case
does throw. There is no *after* case.

**D-2b, the first period on the separated path.** `FC-20` — 3.75 % of interest, `SPECIFIED_DUE_DATE`, due
`01 January 2026` — also returns a response **byte-identical to the control**, while `FC-11` (a flat charge,
same due date, same everything else) returns 9,000.00 in period 1. *Mechanism:*
`separateTotalCompoundingPercentageCharges` removes PERCENT_OF_INTEREST and
PERCENT_OF_AMOUNT_AND_INTEREST specified-due-date charges from the main loop
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:492-504`] and `updatePeriodsWithCharges` applies them
**after** the loop has finished [VERIFIED: `:154` calls it after the `for` loop at `:116-145`], passing
`scheduleParams.isFirstPeriod()` [VERIFIED: `:479`, `:483`]. But `isFirstPeriod()` is
`1 == instalmentNumber` [VERIFIED: `fineract-loan/.../LoanScheduleParams.java:533-535`] and
`incrementInstalmentNumber()` has already run once per period [VERIFIED: `:143`], so by then it is
**false for every period, including period 1** — and the inclusive lower bound that saves FC-11 never
applies. FC-19 (same charge, due mid-period-6) lands correctly, which is what isolates the fault to the
first period's lower boundary rather than to the whole separated path.

**Both are money-losing in the borrower's favour and invisible to the API caller.** Neither could be seen
by any capture in the corpus before today.

---

## 8. Property invariants

`bin/invariants.py`, exact `Decimal` in integer minor units, ten assertions per capture
[VERIFIED: `out/INVARIANTS.md`]:

| invariant | result |
|---|---|
| C1 Σ `feeChargesDue` == `totalFeeChargesCharged` | **PASS 21/21** |
| C2 Σ `penaltyChargesDue` == `totalPenaltyChargesCharged` | **PASS 21/21** |
| C3 `totalDueForPeriod` == principal + interest + fee + penalty, per period | **PASS 21/21** |
| C4 `feeChargesOutstanding` == `feeChargesDue`, same for penalties | **PASS 21/21** |
| C5 `totalRepaymentExpected` == Σ `totalDueForPeriod` | **FAIL on 15 of 21** — see D-1 |  **[SUPERSEDED by T46 C-3: probe, not invariant.]**
| C6 Σ `principalDue` == `totalPrincipalExpected` (amortises to zero) | **PASS 21/21** |
| C7 Σ `interestDue` == `totalInterestCharged` | **PASS 21/21** |
| C8 principal / interest / outstanding identical to the control | **PASS 21/21** |
| C9 EMI identical to the control | **PASS 21/21** |
| C10 no negative money anywhere | **PASS 21/21** |

C5's failures are the finding, not a defect in the tool — and the tool is demonstrably failable, because it
fails. C1 passing on the percentage captures is the assertion that pins the rounding locus (§6 Q5).

---

## 9. Determinism

Every request was issued **three** times: by `bin/capture.sh` into `out/fc/`, again into `out/fc-rerun/`,
and a third time by the attestation generator into `out/attested/`.

**All 21 responses are byte-identical across all three issues** [VERIFIED: `out/DETERMINISM.txt`;
`out/attested/attestation.json` → `byte_identical_to_prior_issue: true` on all 21]. Four responses recur
across *different* requests, which is itself the evidence for §6:

| digest | captures sharing it | what the coincidence proves |
|---|---|---|
| `713a3560…c062009` | control B-01, **FC-17**, **FC-20** | two charged requests produce the zero-charge schedule |
| `d157b0a2…362b356` | FC-11, FC-14, FC-16 | 01 Jan, 20 Jan and 01 Feb 2026 all land in period 1 |
| `fbb8d670…6b2bbc5f` | FC-12, FC-13 | 31 Dec 2026 and 01 Jan 2027 both land in period 12 |

---

## 10. Attestation

Canonical machine-readable form: **`.softhouse/capture/charges/out/attested/attestation.json`**, schema
`gerege-nbfi/pathb-attestation/v1`, generated by `bin/attest-t40.py` (derived from T36's `attest.py`;
T36's own tree was read, never written). It **drives** its own capture run, so digests and timestamps
describe one run. **`notes` is empty — every attested field was read from a primary source; none was
guessed and none was unread.**

```
capture path      Path B — running Fineract server (REST + PostgreSQL)
tenant            gerege | Asia/Ulaanbaatar | schema fineract_gerege | port 5432 | m_loan rows 0
rounding mode     c_configuration.rounding-mode = 4 (HALF_UP), enabled
                  in force this JVM run: HALF_UP (MoneyHelper init line, 2026-08-18T09:53:01.711Z)
                  confirmed behaviourally: half-cent canary -> 20925.05   (HALF_EVEN would give 20925.04)
precision         MoneyHelper.PRECISION = 19, read by javap from the DEPLOYED fineract-core jar
MathContext       MathContext(19, HALF_UP)   == ratified production setting
image             sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a
jar               git.commit.id 426a23544e8426a38ae43ae404670a0a7e85b9eb, git.dirty false, 1.16.0-SNAPSHOT
JVM               Zulu 21.0.11+10-LTS (read inside the container)
PostgreSQL        18.3 (Debian 18.3-1.pgdg13+1) aarch64, server_version_num 180003, image postgres:18.3
driver            org.postgresql.Driver, jdbc:postgresql://db:5432/fineract_tenants
prohibited engines  0 hits in container env; 0 prohibited driver jars in the boot jar
MNT               decimal_places 2, enabled  (ISO 4217 496, minor unit 2)
money serialised  EXACT TEXT (parse_float=str) — no float constructed anywhere
```

Per-capture, all HTTP 200 except the recorded refusal, captured `2026-08-19T00:17:30Z`–`00:17:31Z`:

| id | HTTP | response SHA-256 | byte-identical to prior issue |
|---|---|---|---|
| CTRL-B-01 | 200 | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | (= committed corpus) |
| FC-01-flat-disbursement | 200 | `18bc7b0e30ed14d615989c25cbe394220f38a531c17408c5ed9f68a6921700be` | yes |
| FC-02-flat-instalment | 200 | `eb121bcb048d978127c9919e3a65551364fe1d3d73fe635a4d5099ea9b7b8bbe` | yes |
| FC-03-pctamount-disbursement | 200 | `04c3c58545ca0c457619918352798219f651d6ae64ce993d557706f1942c2100` | yes |
| FC-04-pctinterest-instalment | 200 | `4b350ecf532bf8921901880d081b311d58a91c7d22cfe0cc91b3e5b4a9ee337f` | yes |
| FC-05-pctamountinterest-instalment | 200 | `2f2a242fa80ca563f9599c270f0118e6bc31f6f36e23a1fb630d2df6348accc9` | yes |
| FC-06-penalty-inside-p3 | 200 | `000f9f6bc6b73382d44a01dcfa7815a2e7743d8dddd9d28205cf871cd30c745b` | yes |
| FC-07-fee-on-p3-duedate | 200 | `dffaf0001a4f3b31d6e3ed6b418332e978daf07b384d86b9644b4779c099ed9e` | yes |
| FC-08-penalty-instalment | 200 | `a08d24d7042263e47453e3122221c15af64fd18bb180ee6b97a184abff2b0b73` | yes |
| FC-09-pctamount-instalment | 200 | `090fce5d47b04d796610f8edffffa26a393155b4a125a2032932a3bd6502e0dd` | yes |
| FC-10-pctamount-inside-p6 | 200 | `71c23d4d1795c0e6502fc02848174fc776c31e0d4fb39a7d0f73de72cf39f4a0` | yes |
| FC-11-fee-on-disbursement-date | 200 | `d157b0a21c893ec03ffa6a165c7e83929c9fca9199dc5659bfa7f8322362b356` | yes |
| FC-12-fee-on-final-duedate | 200 | `fbb8d67050a6672a7d82f06e38dd91eb118d13899daef72a721803e56b2bbc5f` | yes |
| FC-13-fee-inside-p12 | 200 | `fbb8d67050a6672a7d82f06e38dd91eb118d13899daef72a721803e56b2bbc5f` | yes |
| FC-14-fee-inside-p1 | 200 | `d157b0a21c893ec03ffa6a165c7e83929c9fca9199dc5659bfa7f8322362b356` | yes |
| FC-15-combined-fee-and-penalty | 200 | `6dfe679c85915dbf44bf1385f4e9c132e8593265844ab456e9c349ba937a7b81` | yes |
| FC-16-fee-on-p1-duedate | 200 | `d157b0a21c893ec03ffa6a165c7e83929c9fca9199dc5659bfa7f8322362b356` | yes |
| FC-17-fee-after-final-duedate | 200 | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | yes |
| FC-19-pctinterest-sdd-inside-p6 | 200 | `a214f3ae361dd2f13a150f659b19c84b0bcc6d8144a68fd1f7ff2832992928aa` | yes |
| FC-20-pctinterest-sdd-on-disb | 200 | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | yes |
| FC-21-pctamtint-sdd-inside-p6 | 200 | `52eb83b1ce9730754f2b6f18a159881975ded9d4a2afa2e544f913b976ee32c4` | yes |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | 200 | `f7c4d6a88d1d9f33e8c455a812450beceff03b62360c2db4f84043e2dc8ba005` | yes |
| **XR-01** (refusal, not a capture) | **403** | `1af1083d1ba86fafcf4871c1b5b7a242684b1b85cf809a44bea50d2d1c9d1805` | n/a |

**Self-check of T40's own write surface**, 10 assertions, all PASS [VERIFIED: `out/SELFCHECK.txt`]: no
prohibited-engine token outside a detection pattern; no float construction in any analysis code; every
analysis tool forces `parse_float=Decimal` and the attestation forces `parse_float=str`; no
`first_name`/`last_name`; no insured/protected/guaranteed language; no hard-coded UTC offset; no error body
filed as a capture.

---

## 11. What I could not capture, and why

* **`chargeTimeType = OVERDUE_INSTALLMENT` (9) — the classic penalty — is not reachable from this
  endpoint.** It is applied by the COB `Apply penalty to overdue loans` job against a *persisted, overdue*
  loan; `calculateLoanSchedule` persists nothing (`m_loan` count 0). Capturing it needs an approved and
  disbursed loan plus a business-date advance, which needs a restart or a business-date API call I judged
  outside "additive-only" for a shared server. **`TO_BE_CAPTURED`.** Note this leaves the *most
  operationally important* penalty type still ungraded; only application-time penalties are covered here.
* **`chargeTimeType = TRANCHE_DISBURSEMENT` (12) and `PERCENT_OF_DISBURSEMENT_AMOUNT` (5)** need
  `multiDisburseLoan = true`, i.e. a new product. Product creation is additive and I could have done it,
  but multi-disbursement changes the schedule shape itself and would have confounded the controlled
  comparison that makes every table above readable. **`TO_BE_CAPTURED` — worth its own task.**
* **Charge `minCap` / `maxCap`, `taxGroupId`, `glAccountId`, `chargePaymentMode = ACCOUNT_TRANSFER (1)`,
  `feeFrequency`/`feeInterval`** — all unexercised. Caps in particular are a rounding-and-clamping surface
  and a plausible defect home. **`TO_BE_CAPTURED`.**
* **Waiver, payment, and the `getDueAmounts` path** — none of it is reachable without a persisted loan.
* **A charge whose percentage lands on an exact half-cent tie.** I looked for one against period 1's
  interest (21,600.00) and proved arithmetically that none exists at that base: a tie needs `216 × p` to end  **[SUPERSEDED by T46 C-2: the proof is FALSE and two ties have been OBSERVED -- `0.021875 %` of 21,600.00 = 4.725 -> 4.73, and `0.009375 %` = 2.025 -> 2.03. See CORRECTIONS.]**
  in `…5` at the third decimal, and `216p` is even for every terminating decimal `p`. I did **not** search
  the other eleven periods or other principals. The tenant-level canary already pins the mode, so this is a
  refinement, not a gap in the mode evidence. **`TO_BE_CAPTURED`** if someone wants the rounding mode pinned
  *inside the charge arithmetic specifically*.
* **`Asia/Hovd` (+07) is still unexercised**, as T36 noted. Every date in these requests is an explicit
  civil date, so it is not load-bearing here — but it will be for anything clock-sensitive.
* **Non-progressive (cumulative) schedules.** Everything here is `loanScheduleType = PROGRESSIVE`. D-1 says
  the cumulative generator behaves *differently*; I observed only the progressive side.

---

## 12. Unverified

Everything material above is tagged `[VERIFIED: …]` and traces to a committed artefact in
`.softhouse/capture/charges/`. The honest exceptions:

* **`[UNVERIFIED]` — that FC-11/FC-14/FC-16 sharing one digest means the *charge* landed identically rather
  than the whole document coinciding for some other reason.** Byte identity of the full response is very
  strong evidence, and `out/FULLCELL.md` shows the same 8 leaves moving in the same direction for all
  three; but I did not construct a case that would distinguish "same period" from "same everything".
* **`[UNVERIFIED]` — that D-1's asymmetry is a *bug* rather than an intended distinction between
  "disbursement charges are part of what you repay" and "instalment charges are not".** What is verified is
  the behaviour, the source path, and the fact that the cumulative generator does the opposite. Calling it a
  defect is my reading; a reviewer may disagree, and DEC-1's owner must decide which behaviour the port
  reproduces.
* **`[UNVERIFIED]` — that D-2b affects only the first period's lower bound.** I observed FC-20 dropped and
  FC-19 (mid-period-6) correct, and re-derived the stale `isFirstPeriod()`. I did **not** probe a separated
  charge dated on an interior period *boundary* (e.g. `01 April 2026`), which the same staleness should
  leave unaffected but which I have not witnessed.
* **`[UNVERIFIED]` — that charge ids 1–12 are the only charge rows this tenant will ever have from T40.**
  They are all that exist now (`m_charge` count 12, verified), but nothing stops a later fire adding more.
* **`[UNVERIFIED]` — anything about how these charges behave once a loan is *persisted and paid*.** Every
  observation here is from the pure calculation endpoint. `feeChargesOutstanding == feeChargesDue` (C4) is
  true only because nothing has been paid.
* **`[UNVERIFIED]` — the exact `daysInPeriod`/`totalOverdue` semantics.** They appear in my tables because
  full-cell comparison prints every column; I did not design a probe for either.
* **Note for the reviewer, so it is not mistaken for a violation:** the strings `ojdbc`, `oracle.jdbc`,
  `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver` appear in `bin/preconditions.sh`, `bin/attest-t40.py`
  and `bin/selfcheck.sh` **only inside `grep` patterns that assert those engines are ABSENT**, and every one
  of those assertions observed **0** hits. They are detection, never a driver, dialect or dependency. The
  word "oracle" throughout this handoff means the **Fineract reference implementation**, never Oracle
  Database.

---

## 13. New findings for the next reviewer, and follow-ups

1. **The charge blind spot is closed for the progressive `calculateLoanSchedule` endpoint, and closing it
   immediately produced two defects.** That is the fifth consecutive round in which a newly-examined surface
   yielded a P0-shaped finding. `patterns.md` says to plan for the next review to find something; it did.
2. **D-1 is a DEC-1 question, not just a Fineract observation.** `totalRepaymentExpected` cannot be
   specified as "the sum of the period totals". The contract must say which of Fineract's two generator
   behaviours the Go port reproduces, and a vector must pin it. **I did not edit `docs/adr/**` — T38 owns
   DEC-1 revision 7 this fire.**
3. **D-2a and D-2b are candidate P0s against the reference oracle itself.** Both silently lose money the
   API caller has asked to charge. Before a port copies them, someone has to decide whether parity means
   "reproduce the drop" or "reject the input". That is a design decision with a regulatory flavour (a
   borrower charged a fee that never appears on the schedule), so it belongs in the gate file, not in a
   worker's judgement.
4. **The three-scalar comparison would have missed all of it.** Level installment, final installment and
   total interest are *identical to the control on all 21 captures*. Every finding in this handoff lives in
   the columns that comparison never looked at. Restate this in `patterns.md` if it needs a second witness.
5. **Follow-ups, in the order I would take them:** (a) capture `OVERDUE_INSTALLMENT` penalties, which needs
   a persisted loan and a business-date advance — plan it as a task that owns the server and can afford
   state; (b) capture `minCap`/`maxCap`, the most likely remaining rounding-and-clamping defect home;
   (c) capture multi-disbursement/tranche charges in their own task; (d) repeat this whole set against the
   **cumulative** generator, since D-1 says the two disagree; (e) provision an `Asia/Hovd` tenant on a fire
   that can afford a restart.
6. **Standing rule reaffirmed:** capture on `gerege`, never on `default`; the preconditions enforce it and
   they passed 21/21 five times in this task.

---

## Files

Everything is under **`.softhouse/capture/charges/`** (T40's write surface, plus this handoff):

```
bin/preconditions.sh          T36's script, copied byte-verbatim (its tree is read-only to T40)
bin/run-preconditions.sh      wrapper: supplies CANARY_REQ + tenant, tees the transcript
bin/lib.sh                    the harness: POST, non-200 aborts, sha256
bin/control.sh                STEP 2 — zero-charge control, byte-for-byte vs the committed corpus
bin/mkcharges.sh              charge definitions 1–10, authored as TEXT
bin/mkcharges2.sh             charge definitions 11–12 (the separated code path)
bin/create-charges.sh         creates 1–10 on the tenant, reads the rows back from PostgreSQL
bin/create-charges2.sh        creates 11–12
bin/mkcalcs.sh                FC-01..FC-15 requests, by text substitution on the committed B-01 request
bin/mkcalcs2.sh               FC-16..FC-22 + XR-01
bin/capture.sh                the capture run (preconditions first; non-200 aborts)
bin/determinism.sh            byte-comparison of the first and second issue
bin/fullcell.py               FULL-CELL diff, exact Decimal, integer minor units, zero tolerance
bin/feecols.py                fee/penalty columns side by side with the control
bin/invariants.py             ten charge invariants (C1–C10)
bin/attest-t40.py             the attestation generator; drives its own capture run
bin/selfcheck.sh              T40's own write surface vs the project non-negotiables
req/                          every request, exactly as sent
out/preconditions-T40.txt     the first precondition run (21/21 PASS)
out/control/                  zero-charge control captures + its precondition transcript
out/charges/                  charge-create responses + precondition transcripts
out/fc/                       the 21 charge captures (first issue)
out/fc-rerun/                 the 21 charge captures (second issue) — determinism
out/attested/                 third issue + attestation.json + canary + precondition transcript
out/XR-01-...-HTTP403.json    the observed refusal (not a capture)
out/FULLCELL.md               every period, every column, every moved leaf
out/FEECOLS.md                fee/penalty columns per capture
out/INVARIANTS.md             C1–C10 per capture
out/DETERMINISM.txt           byte-identity results
out/SELFCHECK.txt             non-negotiables self-check
```

---

# CORRECTIONS — T46 (branch `softhouse/T46-capture-corrections`), against T44 findings A-1 … A-8 and T44-X1

**Appended by T46. Nothing above this line was altered.** Full working:
`.softhouse/capture/charges/ATTESTATION-T46.md`.

## C-1 (A-3) — §§4-9's framing of the per-request `amount` is wrong, and the corpus was blind

This handoff calls the mandatory per-request `amount` a redundant echo of the definition
(*"Every request therefore repeats the definition's amount as exact decimal text"*). **It is not
redundant: the request value is AUTHORITATIVE and `m_charge.amount` is ignored.** Because T40 always
made the two equal, **no capture in the original 21 could tell the two readings apart** — a Go port that
read the definition passed all 21 and was wrong.

**Seven new captures make them disagree, and the request wins seven for seven**
[`out/t46/DEFVSREQ.txt`]:

| capture | charge (time, calc) | definition | request | DEFINITION would give | **OBSERVED** |
|---|---|---|---|---|---|
| `T46-CH-01` | 4 (8, 4) | `3.750000` | `1.25` | `810.00` | **`270.00`** |
| `T46-CH-02` | 1 (1, 1) | `15000.000000` | `7777.77` | `15000.00` | **`7777.77`** |
| `T46-CH-03` | 4 (8, 4) | `3.750000` | `0.021875` | `810.00` | **`4.73`** |
| `T46-CH-04` | 4 (8, 4) | `3.750000` | `0.009375` | `810.00` | **`2.03`** |
| `T46-CH-05` | 5 (8, 3) | `1.234500` | `2.5` | `1383.65685765` | **`2802.06`** |
| `T46-CH-06` | 3 (1, 2) | `1.234500` | `0.5` | `14814.00` | **`6000.000`** |
| `T46-CH-07` | 8 (8, 1) penalty | `1200.000000` | `333.33` | `1200.00` | **`333.33`** |

Four `charge_calculation_enum` values, two `charge_time_enum` values, fee and penalty.
**The vector's fixture is the REQUEST BYTES, not the `m_charge` row.**
`out/attested/attestation.json`'s `charges_as_persisted` block stays load-bearing for
`charge_time_enum` / `charge_calculation_enum` / `is_penalty` and is load-bearing for **no money value**.
Corroborated independently by T44's audit probes AP-5/AP-6 with different values.

## C-2 (A-5) — §11's arithmetic proof is FALSE, and a half-cent tie has now been observed

§11 says *"a tie needs `216 × p` to end in `…5` at the third decimal, and `216p` is even for every
terminating decimal `p`"*. `p` is a decimal, not an integer. **Two exact ties, both `HALF_UP`:**
`0.021875 %` of `21600.00` = `4.725` → **`4.73`**; `0.009375 %` = `2.025` → **`2.03`**
(`HALF_EVEN` would give `4.72` / `2.02`). Delete §11's claim; the in-charge-arithmetic rounding-mode
canary exists and is captured.

**The rounding locus, re-derived** — and it is not where §11 assumed:
`ProgressiveLoanScheduleGenerator.java:445-446` multiplies and divides under the **threaded** `mc`
(exact at precision 19), then wraps the result in the **two-argument** `Money.of(MonetaryCurrency, …)`
[`Money.java:114-116`], which supplies **`MoneyHelper.getMathContext()` — the AMBIENT context** — and
`Money.java:52` does `setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())`.
**The charge tie is decided by the AMBIENT tenant rounding mode, not the threaded one.**

## C-3 (A-4) — C5 is a discrimination probe, not an invariant

DEC-1 revision 8's ratified decision **C-1** forbids any harness asserting `totalRepaymentExpected ==
Σ rows`. Shipped as an invariant, C5 makes a **correct** Go port fail 15 of 21. `bin/t46-invariants.py`
keeps `C1 C2 C3 C4 C6 C7 C8 C9 C10` as invariants (**0 failures over 28 captures**) and reports C5 as
**probe P5** — the signed delta `TRE − Σ rows` in integer minor units, **non-zero on 20 of 28**, from
`−1,361` to `−5,190,000`. The suite is proved failable. `bin/invariants.py` is left as T40's evidence;
what must not happen is C5 travelling forward as a conformance check.

## C-4 (A-2) — D-1's single source citation points at the site of AGREEMENT

`AbstractCumulativeLoanScheduleGenerator.java:504` is inside `updatePeriodsWithCharges` — the
**separated** path, which the progressive generator has too (`ProgressiveLoanScheduleGenerator.java:486`).
Replace it with the cumulative **main loop**: `:392`
`scheduleParams.addTotalRepaymentExpected(totalInstallmentDue)`, `:352`
`totalInstallmentDue = currentPeriodParams.fetchTotalAmountForPeriod()`, and
`ScheduleCurrentPeriodParams.java:144-145` defining that as principal + interest + fee + penalty.
The conclusion is unchanged and true; only the pointer moves.
`[VERIFIED on T44's evidence; UNVERIFIED by T46]`

## C-5 (A-1, A-8) — the attestation

- **A-1:** the Path B wiring citation was entirely absent (**zero** grep hits). It is now recorded and
  re-verified: `LoanScheduleAssembler.java:753`, `:777`, `:797` read `MoneyHelper.getMathContext()` and
  `:765` hands that reference to `generate(mc, …)`; `LoanScheduleGeneratorServiceImpl.java:44` likewise.
  **On Path B the ambient context IS the threaded object**, which is why T40's ambient reading was right
  — but rule 4 requires that be said and cited.
- **A-8:** the `c_configuration` row and the `MoneyHelper` init log line are **one** ambient witness, not
  two [`MoneyHelper.java:59-64` logs the same local it caches]. Rule 6 still holds, via T36's behavioural
  canary and now via C-2's two in-charge ties.

## C-6 (A-6) — response scale is CALLER-CONTROLLED, and ungraded

`T46-CH-06` returns the disbursement fee as **`6000.000`** (scale 3) because `0.5 %` of `1200000.00` is
scale 3 and **nothing on the disbursement path wraps it in `Money`**, so the currency's 2 decimal places
are never applied. The instalment path *is* wrapped, which is why `T46-CH-03` comes back at scale 2.
Comparing these as numbers rather than as text would silently pass a port emitting `6000.00`.

## C-7 (A-7) — the run recipe is runnable again

11 `bin/` files hard-coded T40's ephemeral worktree path. `bin/t46-fix-paths.py` makes them
self-locating. **Proved to change nothing: 21 of 21 responses re-issued BYTE-IDENTICAL** through the
fixed scripts against the live oracle — a third independent issue of the corpus
[`out/t46-reissue/IDENTITY.txt`] — and `bin/invariants.py` still reproduces `out/INVARIANTS.md`
byte-for-byte.

## C-8 (T44-X1) — Path B captures are float-shaped on the wire

Raw bytes stay canonical and are **not** rewritten. **57 exact-text sidecars** `<name>-exact.json` are
added, in which every JSON number becomes a JSON **string** carrying the wire literal byte for byte,
produced without constructing a single float and **proved identical leaf-for-leaf** to the raw capture
[`out/t46/EXACT-TEXT.md`, `bin/t46-exacttext.py`, failable via `--negative`]. Measured by T46:
**17,693 bare JSON number occurrences, 552 distinct literals**, of which **65** would have their text
changed by a float round-trip; Path A control **0**.
**Admissibility rule: a Path B vector is compared as EXACT DECIMAL TEXT, never through a JSON number.**

## C-9 — new `TO_BE_CAPTURED` items this pass raises

- whether `m_charge.amount` governs when the request **omits** `amount` (every capture supplies it);
- a shape separating the **ambient** from the **threaded** rounding mode inside charge arithmetic
  (needs the two to differ, i.e. a tenant write this task may not make);
- `charge_calculation_enum` 5 and 9 and `charge_time_enum` 2 re-tested with a *disagreeing* amount.
