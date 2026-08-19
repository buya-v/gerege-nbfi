# T39 — observing the `rateFactorTillPeriodDueDate` multiplier (P0-T34-1)

## Verdict

**P0-T34-1 is CONFIRMED BY OBSERVATION.** The pinned reference oracle (Fineract) uses
`periodRatio`, not `RepaymentEvery`, on the `rateFactorTillPeriodDueDate` call site. On the
**415 cells where the two readings disagree**, across **8 shapes inside the drift region**, the
oracle agrees with `periodRatio` on **415 of 415** and with `RepaymentEvery` on **0 of 415**.
The worst total-interest gap T34 re-derived — **MNT 398,967.73** on a MNT 50,000,000 / 36 ×
21.6 % loan — is now an **observed** gap, digit for digit
[VERIFIED: capture `T39-P0-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`].

**A second question was settled at the same time.** `calculatePeriodRatio`'s month-end special
case (`ProgressiveEMICalculator.java:1426-1436`) is **live and load-bearing**: on 4 shapes and
**116 disagreeing cells**, the oracle agrees **116 of 116** with the routine that includes those
four lines and **0 of 116** with the same routine minus them. Omitting them roughly doubles
`periodRatio` on alternate periods — **MNT 83,959.76** of extra interest on one MNT 3.9 M / 6-month
loan [VERIFIED: capture `T39-ME-A`].

**Branch:** `softhouse/T39-periodratio-observation`.
**Written:** `.softhouse/capture/periodratio/**` and this file. Nothing else — `docs/adr/**`,
`nexus/**`, `.softhouse/reference-oracle.md`, `.softhouse/patterns.md`, sibling capture
directories and the running containers were all left alone.

**Storage:** *raw observed form only.* Gate G-1 is open and DEC-1 is unratified, so the contract
*shape* is what is being ratified and a contract-shaped capture would beg the question. **Nothing
is promoted to the parity vector store.** Rationale in
`.softhouse/capture/periodratio/PROVENANCE.md`.

---

## 1. What was captured

Sixteen schedules, one run, Path A embeddable seam, in process, throwaway `docker run --rm`
containers, ratified production `MathContext (19, HALF_UP)` everywhere except the labelled
calibration. Recipe: `.softhouse/capture/periodratio/REPRODUCE.md`. Payload:
`.softhouse/capture/periodratio/out/t39-periodratio.json`.

Every case pins MNT (USD for the calibration), `MinorUnitDigits` 2, one disbursement,
`RepaymentEvery` 1, MONTHS, DECLINING_BALANCE, `DaysInMonth DAYS_30` / `DaysInYear DAYS_360`,
`daysInYearCustomStrategy null`, down payment 0, `installmentAmountInMultiplesOf null`,
`fixedLength null`, `interestRecognitionOnDisbursementDate false`,
`allowPartialPeriodInterestCalculation true`, `allowFullTermForTranche false`, tenant timezone
`Asia/Ulaanbaatar`, tenant rounding-mode ordinal **4 (HALF_UP)**.

### The three readings compared

| | reading | source |
|---|---|---|
| **R1** | multiplier = `RepaymentEvery` | DEC-1 §4.3.2 lines 486-490; `contract.go:1455-1459` |
| **R2** | multiplier = `periodRatio` | `ProgressiveEMICalculator.java:1404-1413` → `calculatePeriodRatio` `:1419-1458` → `calculateSeedDate` `:1461-1479` |
| **R3** | `periodRatio` with the month-end special case omitted | R2 minus `:1429-1434`; the most plausible mis-port of the routine |

R1 and R2 are T34's transcriptions, copied **byte-identically** into
`.softhouse/capture/periodratio/analysis/` (`t34_model.py`, `t34_periodratio.py`); R3 is the same
routine with one `MARKED EDIT`. All three are **re-derivations** — no oracle was contacted by
them. The oracle decides.

### The observed table

`obs` is the oracle. `R1` and `R3` are re-derived predictions; the gap column is
`observed − predicted`.

| capture | start | disbursement | n | rate | principal | **observed total interest** | R1 predicts | gap vs R1 | R3 predicts | gap vs R3 | cells R1≠R2 | cells R2≠R3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `T39-CTL-Q0a` | 2024-01-01 | 2024-01-01 | 6 | 21.6 | 1,200,000 | **76,723.70** | 76,723.70 | 0.00 | 76,723.70 | 0.00 | 0 | 0 |
| `T39-CTL-1` | 2024-01-01 | 2024-01-01 | 6 | 7.0 | 1,014,632 | **20,815.82** | 20,815.82 | 0.00 | 20,815.82 | 0.00 | 0 | 0 |
| `T39-CTL-2` | 2024-01-15 | 2024-01-15 | 6 | 21.6 | 1,200,000 | **76,723.70** | 76,723.70 | 0.00 | 76,723.70 | 0.00 | 0 | 0 |
| `T39-P0-A` | 2024-01-28 | 2024-01-31 | 6 | 21.6 | 1,200,000 | **76,984.00** | 74,607.33 | **+2,376.67** | 76,984.00 | 0.00 | **30** | 0 |
| `T39-P0-B` | 2024-01-28 | 2024-01-29 | 6 | 21.6 | 1,200,000 | **76,772.34** | 76,018.25 | **+754.09** | 76,772.34 | 0.00 | **30** | 0 |
| `T39-P0-C` | 2024-01-29 | 2024-01-31 | 12 | 16.8 | 5,000,000 | **470,451.99** | 461,722.74 | **+8,729.25** | 470,451.99 | 0.00 | **59** | 0 |
| `T39-P0-D` | 2024-01-28 | 2024-01-31 | 36 | 21.6 | 50,000,000 | **18,659,151.45** | 18,260,183.72 | **+398,967.73** | 18,659,151.45 | 0.00 | **180** | 0 |
| `T39-P0-E` | 2025-01-28 | 2025-01-31 | 6 | 21.6 | 1,200,000 | **76,809.48** | 74,539.07 | **+2,270.41** | 76,809.48 | 0.00 | **29** | 0 |
| `T39-P0-F` | 2024-01-28 | 2024-01-31 | 6 | 21.6 | **100** | **6.41** | 6.21 | **+0.20** | 6.41 | 0.00 | **27** | 0 |
| `T39-P0-G` | 2024-03-28 | 2024-03-31 | 6 | 16.8 | 2,500,000 | **124,359.75** | 120,625.67 | **+3,734.08** | 124,359.75 | 0.00 | **30** | 0 |
| `T39-P0-H` | 2024-11-28 | 2024-11-30 | 6 | 16.8 | 3,000,000 | **149,987.71** | 145,985.84 | **+4,001.87** | 149,987.71 | 0.00 | **30** | 0 |
| `T39-ME-A` | 2024-01-31 | 2024-01-31 | 6 | 16.8 | 3,924,149 | **194,510.78** | 194,510.78 | 0.00 | 278,470.54 | **−83,959.76** | 0 | **29** |
| `T39-ME-B` | 2024-01-31 | 2024-01-31 | 6 | 21.6 | 1,200,000 | **76,723.70** | 76,723.70 | 0.00 | 109,900.97 | **−33,177.27** | 0 | **29** |
| `T39-ME-C` | 2023-01-31 | 2023-01-31 | 6 | 21.6 | 1,200,000 | **76,723.70** | 76,723.70 | 0.00 | 109,900.97 | **−33,177.27** | 0 | **29** |
| `T39-ME-D` | 2024-01-30 | 2024-01-30 | 6 | 21.6 | 1,200,000 | **76,723.70** | 76,723.70 | 0.00 | 95,308.80 | **−18,585.10** | 0 | **29** |
| `T39-CAL` | 2024-01-01 | 2024-01-01 | 6 | 7.0 | USD 100 | **2.05** | — rig calibration at (12, HALF_UP), not a parity vector — | | | | | |

[VERIFIED: `.softhouse/capture/periodratio/out/t39-periodratio.json`;
`analysis/discriminate-output.txt`]

---

## 2. Discrimination, measured on the disagreeing cells only

The method T37 proved: take the cells where the two readings **disagree** — the only cells that
carry information about the question — and ask which reading the observation agrees with there.
A cell where both readings agree tells you nothing, and counting it inflates the verdict.

**Comparison is FULL-CELL:** `fromDate`, `dueDate`, `principal`, `interest`, `fee`, `penalty`,
outstanding `balance`, `total` due and `totalOutstandingBalance` on **every** row, plus
`loanTermInDays`, `totalDisbursedAmount`, `totalInterestAmount`, `totalRepaymentAmount` and the
disbursement row's three columns. **Not** the three headline scalars — that shape is exactly what
let defect F-1 hide through five reviews.

| question | separating shapes | discriminating cells | observation agrees with the **DEC-1** reading | observation agrees with the **pinned-source** reading |
|---|---|---|---|---|
| **P0-T34-1** — is the multiplier `RepaymentEvery` or `periodRatio`? | 8 | **415** | **0 / 415** | **415 / 415** |
| **month-end special case** — is `:1429-1434` in force? | 4 | **116** | (omitted: **0 / 116**) | (present: **116 / 116**) |

And end to end, not only on the disagreeing cells: **R2 reproduces every cell of every one of the
15 parity-setting captures — 1,239 cells — with zero mismatches**: all 8 drift shapes, all 4
month-end shapes and all 3 controls. There is no residual cell where the pinned-source reading and the oracle
part company on this family.

[VERIFIED: `analysis/discriminate-output.txt`]

### Worked example — `T39-P0-A`, the shape T34 §1.4 named

Schedule start 2024-01-28, disbursement 2024-01-31, MNT 1,200,000, 6 × 21.6 %.
Observed `periodRatio` per repayment period (re-derived from the pinned source):
`1.03448275862068965517`, `1.06451612903225806452`, `1`, `1.03225806451612903226`, `1`,
`1.03225806451612903226` — i.e. four of six periods are off the `ScheduleStartDate + k months`
lattice.

**Observed** (the oracle):

| # | from | due | principal | interest | fee | penalty | balance | total | totalOutstandingBalance |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2024-01-28 | 2024-02-29 | 192,580.67 | **20,250.00** | 0.00 | 0.00 | 1,007,419.33 | 212,830.67 | 1,064,153.33 |
| 2 | 2024-02-29 | 2024-03-31 | 193,527.22 | 19,303.45 | 0.00 | 0.00 | 813,892.11 | 212,830.67 | 851,322.66 |
| 3 | 2024-03-31 | 2024-04-30 | 198,180.61 | 14,650.06 | 0.00 | 0.00 | 615,711.50 | 212,830.67 | 638,491.99 |
| 4 | 2024-04-30 | 2024-05-31 | 201,390.35 | 11,440.32 | 0.00 | 0.00 | 414,321.15 | 212,830.67 | 425,661.32 |
| 5 | 2024-05-31 | 2024-06-30 | 205,372.89 | 7,457.78 | 0.00 | 0.00 | 208,948.26 | 212,830.67 | 212,830.65 |
| 6 | 2024-06-30 | 2024-07-31 | 208,948.26 | 3,882.39 | 0.00 | 0.00 | 0.00 | **212,830.65** | 0.00 |

term 185 days; total disbursed 1,200,000.00; **total interest 76,984.00**; total repayment
1,276,984.00.

**What DEC-1 revision 6, read literally, predicts for the same request** (re-derivation):

| # | principal | interest | balance | total |
|---|---|---|---|---|
| 1 | 192,859.52 | **19,575.00** | 1,007,140.48 | 212,434.52 |
| 2 | 194,305.99 | 18,128.53 | 812,834.49 | 212,434.52 |
| 3 | 197,803.50 | 14,631.02 | 615,030.99 | 212,434.52 |
| 4 | 201,363.96 | 11,070.56 | 413,667.03 | 212,434.52 |
| 5 | 204,988.51 | 7,446.01 | 208,678.52 | 212,434.52 |
| 6 | 208,678.52 | 3,756.21 | 0.00 | 212,434.73 |

total interest 74,607.33. **Every principal, every interest, every balance and every installment
differs**, plus all three totals — 30 cells. T34's hand-worked period-1 figures (`19,575.00` as
DEC-1 is written against `20,250.00` from the pinned source, ratio 1.03448…) are now **observed**:
the oracle returned **20,250.00** [VERIFIED: capture `T39-P0-A`].

### Worked example — `T39-ME-B`, the month-end special case

Schedule start = disbursement 2024-01-31, MNT 1,200,000, 6 × 21.6 %. The special case fires on
repayment periods 2, 4 and 6 (0-based 1, 3, 5). With it, `periodRatio` is `[1,1,1,1,1,1]`; without
it, `[1,2,1,2,1,2]` — the four omitted lines are all that stop the oracle charging a **double**
month on alternate periods.

| # | from | due | principal | interest | balance | total |
|---|---|---|---|---|---|---|
| 1 | 2024-01-31 | 2024-02-29 | 191,187.28 | 21,600.00 | 1,008,812.72 | 212,787.28 |
| 2 | 2024-02-29 | 2024-03-31 | 194,628.65 | 18,158.63 | 814,184.07 | 212,787.28 |
| 3 | 2024-03-31 | 2024-04-30 | 198,131.97 | 14,655.31 | 616,052.10 | 212,787.28 |
| 4 | 2024-04-30 | 2024-05-31 | 201,698.34 | 11,088.94 | 414,353.76 | 212,787.28 |
| 5 | 2024-05-31 | 2024-06-30 | 205,328.91 | 7,458.37 | 209,024.85 | 212,787.28 |
| 6 | 2024-06-30 | 2024-07-31 | 209,024.85 | 3,762.45 | 0.00 | **212,787.30** |

total interest **76,723.70**; the special-case-omitted reading predicts **109,900.97** — a
**MNT 33,177.27** overcharge on a MNT 1.2 M loan, 29 cells wide. The oracle is the
special-case-present reading on all 29 [VERIFIED: capture `T39-ME-B`].

---

## 3. New findings, for the reviewer and for DEC-1 revision 7

**N-1 (correction to the P0's framing, in DEC-1's favour). Two arguments differ syntactically;
only ONE of them differs on the graded domain.** The task brief and T34 §1.2 both say "two
arguments differ, not one". The pinned source passes `(…, periodRatio, BigDecimal.valueOf(30), …)`
at `:1412-1413` and `(…, repaymentEvery, daysInMonth, …)` at `:1536-1537`. But `daysInMonth` is
computed at `:1509` as `daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) :
calculatedDaysInRepaymentPeriod`, and DEC-1 §3.1's graded domain fixes `DaysInMonth = DAYS_30`.
So on the graded domain the 4th argument is `30` on **both** call sites and the *effective*
difference is exactly the multiplier. The correction DEC-1 revision 7 needs is therefore a
one-argument correction, and a revision that "fixed" `daysInMonth` too would be wrong outside the
graded domain. [VERIFIED: `ProgressiveEMICalculator.java:1508`, `:1412-1413`, `:1536-1537`]

**N-2. The P0 question and the month-end question are DISJOINT in shape space — no single vector
can grade both.** Re-derived over 51,729 same-month `(ScheduleStartDate ≤ DisbursementDate)`
pairs across 2023-2025 × terms {6, 12, 36}: the month-end special case fires on **210** of them,
and on **0 of those 210** does `ScheduleStartDate ≠ DisbursementDate`. The special case only fires
when `calculateSeedDate` returns the schedule start — i.e. when the boundaries are *on* the
lattice — while the P0 drift requires them *off* it. Consequence for DEC-1 §8: the new capture
item T34 §1.6 proposes (item **3e**) needs **two** vectors, not one, and the observed cell counts
confirm it (`d12 > 0 ⇒ d23 = 0` and vice versa on all 15 shapes).
[VERIFIED: `analysis/select_shapes-output.txt`, `analysis/discriminate-output.txt`; the 51,729-pair
sweep is a re-derivation run by this task and is **not** in a committed output file]

**N-3 (material, and it weakens an attestation claim this program has been making). The ambient
`MoneyHelper` `MathContext` is NOT the arithmetic in force on Path A.** Forcing the tenant
`RoundingMode` ordinal to `1` (DOWN) changed `MoneyHelper.getMathContext()` to
`precision=19 roundingMode=DOWN` on the oracle's own testimony — and left **all sixteen observed
blocks byte-identical**. Forcing the *threaded* `MathContext` rounding mode to DOWN moved
**fifteen of sixteen** (e.g. `T39-CTL-Q0a` total interest `76723.70` → `76723.65`). So the SLF4J
`Initialized rounding mode for tenant …` line and the echoed `MoneyHelper.getMathContext()` —
which T37's attestation §4 calls "the `MathContext` actually in force" — witness the *tenant
configuration*, not the arithmetic that produced the numbers. Both should still be attested; only
the **threaded** context is evidence about the money. Every capture attestation in this program
should be re-read with that distinction.
[VERIFIED: `out/t39-neg5.json` vs `out/t39-periodratio.json` (0/16 differ);
`out/t39-neg7.json` vs `out/t39-periodratio.json` (15/16 differ); `NEGATIVE-TESTS.md`]

**N-4. Threaded precision 12 and 19 are indistinguishable on all sixteen shapes.** Forcing the
threaded precision to 12 left every observed block byte-identical. This is a **coverage statement
about these shapes**, not a general one — the rate factor is `setScale`d to the precision as a
*scale*, and the residual sits below one minor unit at these magnitudes. A shape that separates 12
from 19 is `TO_BE_CAPTURED`, and until one exists, "captured at (19, HALF_UP)" is a provenance
claim, not a discrimination claim, for this family.
[VERIFIED: `out/t39-neg6.json` vs `out/t39-periodratio.json`]

**N-5. There is no size threshold, observed.** `T39-P0-F` is MNT 100 — the smallest principal that
still amortises — and it still separates the readings on **27 cells**, with the observed total
interest `6.41` against `6.21` predicted by DEC-1 as written. T34's re-derived claim that "there is
no size threshold below which the reading is safe" is now observed at the bottom end.
[VERIFIED: capture `T39-P0-F`]

**N-6. The drift is not a January artefact, not a leap-year artefact, and not a 31-day-month
artefact.** It reproduces seeded in March (`T39-P0-G`, +3,734.08), in a 30-day November
(`T39-P0-H`, disbursement on the 30th, +4,001.87) and in the common year 2025 (`T39-P0-E`,
+2,270.41). The month-end special case likewise reproduces in a common year (`T39-ME-C`, identical
to the leap-year `T39-ME-B` to the cent).
[VERIFIED: captures `T39-P0-E`, `T39-P0-G`, `T39-P0-H`, `T39-ME-C`]

**N-7. Drift changes the DUE DATES, not only the money — and a three-scalar check cannot see
that either.** On `T39-P0-A` the observed windows are `01-28 → 02-29 → 03-31 → 04-30 → 05-31 →
06-30 → 07-31` and `loanTermInDays` is **185**, not 182. Any conformance check that compares
level/final/total-interest and no date would miss a three-day term difference on a real loan.
[VERIFIED: capture `T39-P0-A`]

---

## 4. Controls

All four passed; `analysis/controls-output.txt`. Expectations are **transcribed** with `file:line`,
never computed.

| control | expectation transcribed from | compared | result |
|---|---|---|---|
| **C1 calibration** `T39-CAL`, USD 100 / 6 × 7.0 % at `(12, HALF_UP)` | the shipped Fineract test literal: `EmbeddableProgressiveLoanScheduleGeneratorTest.java:44` (MathContext), `:74-77` (totals), `:79-95` (rows) | **61 cells** (4 totals + 3 disbursement columns + 6 rows × 9 columns) | **reproduced digit for digit.** Labelled; NEVER a parity vector |
| **C2 reproduction** `T39-CTL-Q0a` | committed observation **Q0a**, `.softhouse/reviews/t23-probe/t23-probe-output.txt:5-16` | **42 cells** | **reproduced digit for digit** |
| **C3 reproduction** `T39-CTL-1` | committed capture **T37-3-A**, `.softhouse/handoff/T37-dec1-binding-captures.md` item 3 | **40 cells** | **reproduced digit for digit** |
| **C4 reproduction** `T39-ME-A` | committed capture **T37-3b-2**, same handoff, item 3b | the 3 scalars that handoff publishes | **reproduced digit for digit** |

Three of the four reproduce records taken by **different harnesses on different tasks**, so the
harness is not the variable. `T39-CTL-1` and `T39-CTL-2` are additionally *in-graded-domain
controls outside the drift region*: on them all three readings agree on every cell, and the oracle
agrees with all three — which is what makes the 415-cell separation elsewhere attributable to the
multiplier and not to the rig.

**Determinism:** the whole capture was re-run from a fresh container and the JSON payload is
**byte-identical** (`diff` clean; both sha256
`898435d89b58c1c61dd0b9d55b2bae38ab8fedd33f41d314ffea09b5c7e5b3a2`).

**The recipe is failable, proved:** seven deliberately-wrong runs, all exit 1 naming the breach —
wrong pin, dirty checkout, wrong image id, seam-class drift, wrong ambient MathContext, wrong
threaded precision, wrong threaded rounding mode. Transcripts in
`.softhouse/capture/periodratio/NEGATIVE-TESTS.md`.

---

## 5. Attestation summary

Full attestation: `.softhouse/capture/periodratio/ATTESTATION.md`.

- **Pinned Fineract commit** `426a23544e8426a38ae43ae404670a0a7e85b9eb`, checkout clean, asserted
  on every run.
- **Image** `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`,
  created 2026-08-17T11:29:56Z, launched **by id**; `/app/fineract-provider.jar` sha256
  `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9`.
- **The jar's own `git.properties`**: `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`,
  `git.commit.id.describe=1.15.0-273-g426a235`, **`git.dirty=false`** — the binary's own testimony
  that it was built from the pin, clean.
- **Seam class byte-identical** to the pinned original (`diff` silent), sha256
  `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — the same digest T37
  recorded independently. My copy lives under `capture/periodratio/src/`; sibling directories were
  never read from, compiled from or written to.
- **JVM**: `openjdk 21.0.11 2026-04-21 LTS`, Zulu21.50+19-CA, build `21.0.11+10-LTS`, Azul Systems.
  **No `-D` flags on a capture run**, and the payload records all three negative-test overrides as
  `null` (asserted). `user.timezone` came back `null` because the entrypoint is overridden —
  recorded, and inert here because every date is an explicit civil date.
- **`MoneyHelper.PRECISION` read from the running oracle: 19.** Ambient
  `MoneyHelper.getMathContext()` = `precision=19 roundingMode=HALF_UP` on all sixteen, and the
  oracle's own SLF4J log carries 16 of 16 `Initialized rounding mode … HALF_UP` lines. Threaded
  `(19, HALF_UP)` on fifteen; `(12, HALF_UP)` on the labelled calibration only. **But see N-3:**
  only the *threaded* context is evidence about the arithmetic.
- **Classpath**: 348 entries, digest
  `68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f`, **zero** Oracle Database /
  MySQL / MariaDB entries — asserted every run.
- **No float** anywhere: `BigDecimal.toPlainString()` in the harness, Python `decimal` at explicit
  contexts in the analysis, exact string comparison throughout.
- **sha256 of every output file** in `ATTESTATION.md` §9.
- **Containers:** six throwaway `--rm`, mounting only this task's directory. `fineract-fineract-1`
  and `fineract-db-1` were not started, stopped, reconfigured or written to.

---

## 6. What I could NOT capture, and why

- **The guard, the seed and the ratio directly.** Nothing here instruments
  `calculatePeriodRatio`, `calculateSeedDate` or the rate factor. What is observed is that the
  oracle's output is the one only a `periodRatio`-with-month-end-case execution produces, and is
  not the one either alternative produces. That is a discrimination, not an internal observation,
  and it is what the question needs.
- **A shape grading BOTH the P0 and the month-end case.** None exists on the swept grid — see
  **N-2**. Not a gap in this capture; a structural fact about the two questions.
- **A shape separating threaded precision 12 from 19.** None of these sixteen does — see **N-4**.
  `TO_BE_CAPTURED`.
- **`RepaymentEvery > 1`, non-monthly frequencies, `DaysInMonth ACTUAL`, `DaysInYear ACTUAL`,
  multi-disbursement, down payments, `installmentAmountInMultiplesOf`, `fixedLength`, charges.**
  Out of scope for this task and, for the last four, partly outside Path A's reach. `periodRatio`'s
  `YEARS`/`WEEKS`/`DAYS` arms (`:1405`, `:1407`, `:1408`) are **entirely uncaptured** —
  `TO_BE_CAPTURED`.
- **Anything needing the running server (Path B).** A sibling worker owns it this fire and none of
  these shapes needs it.
- **Fee and penalty discrimination.** Every observed `fee` and `penalty` is `0.00`, as everywhere
  else in this corpus. Those columns are *compared* here (they are part of the full-cell check) but
  they discriminate nothing, exactly as `patterns.md` records.

---

## 7. Unverified

- **"The month-end special case fired on periods 2, 4 and 6."** That is a **re-derivation** from
  the pinned source (`analysis/readings.py::monthend_special_case_fires`), not an instrumented
  observation. What is *observed* is that the oracle's output matches the reading that includes
  the special case and not the reading that omits it. `[UNVERIFIED as a direct observation;
  VERIFIED as a discrimination: analysis/discriminate-output.txt]`
- **The 51,729-pair disjointness sweep in N-2** was run by this task as a re-derivation and its
  raw output is not committed — only its conclusion is stated here. Re-runnable from
  `analysis/readings.py`. `[UNVERIFIED as a committed artefact; the conclusion is corroborated by
  the 15 captured shapes, on every one of which exactly one of the two questions separates]`
- **T34's counts** — 55 of 5,767 pairs in 2024, 54 of 5,738 in 2025, 480 of 480 swept requests —
  were **not** re-run by this task. This capture neither confirms nor disputes them; it observes 8
  points inside the region they describe. `[UNVERIFIED here]`
- **Generalisation.** Sixteen captures grade sixteen shapes. They license no claim about an
  un-sampled `(ScheduleStartDate, DisbursementDate, principal, term, rate)` tuple.
- **Whether R2 is the *complete* specification.** R2 reproduced all 1,239 cells of these 15 shapes,
  which is strong, but T34's model was also 13-of-13 clean before it was attacked. Assume the next
  review finds something.

---

## 8. Follow-ups

**G-1 (for DEC-1 revision 7, T38's task — reported, not acted on).** The revision T34 §1.6 asks
for is now **observationally required**, not merely re-derived. Three additions this capture
supports beyond T34's list:

1. State `periodRatio`'s **month-end special case** (`:1426-1436`) normatively. It is not an edge
   case: it is worth MNT 83,959.76 on one captured six-month loan, and a port that drops those four
   lines double-charges alternate periods. T34 §1.6 item 2 mentions the adjustment; it should be
   normative and cited, with the "`targetDateLastDay == targetDateDay && seedDateDay >
   targetDateDay`" predicate spelled out.
2. Correct **one** argument, not two — see **N-1**.
3. §8's new capture item **3e** needs **two** vectors, drift and month-end, because no shape grades
   both — see **N-2**.

**G-2. Attestation practice.** Every future capture attestation should distinguish the **ambient**
`MoneyHelper` context from the **threaded** `MathContext`, and should claim only the second as
evidence about arithmetic — see **N-3**. `.softhouse/reference-oracle.md` is the right place for
that rule; I did not edit it.

**G-3. Widen every corpus-validation script to full-cell comparison.** This is the third defect
class in this program that a three-scalar check could not see: `loanTermInDays` moves by three days
on `T39-P0-A`, and due dates move on every drift shape. `analysis/discriminate.py`'s
`observed_cells()` / `disagree()` pair is a drop-in pattern.

**G-4. Promotion is still blocked and should stay blocked.** These are attested observations, not
vector-store entries. Promote after G-1 closes, using `REPRODUCE.md` as the committed run recipe.
Cutover remains a hard `user` gate regardless.

---

# CORRECTIONS — T46 (branch `softhouse/T46-capture-corrections`), against T44 findings F39-1 … F39-4

**Appended by T46. Nothing above this line was altered** — `patterns.md` forbids mutating a committed
record; corrections to *claims* are appended, corrections to *observations* would need a re-run that
proves identity, and one was done (§2 below). Full working:
`.softhouse/capture/periodratio/ATTESTATION-T46.md`.

## C-1 (F39-1) — the verdict and §2 table overstate what the `T39-ME-*` family grades

**This handoff says:** *"the oracle agrees 116 of 116 with the routine that includes those four lines
and 0 of 116 with the same routine minus them"*, and concludes the month-end special case is *"live and
load-bearing"*.

**The comparison is sound; the null hypothesis is the wrong one.** The four `T39-ME-*` captures grade
the **PAIR** — `month-end special case ∧ packed whole-months` — never the special case alone. A port
with two cancelling defects (naive whole-months **and** no special case) reproduces the oracle exactly.

**T46 settled the question T44 left open, and the answer is that the special case has NO separating
shape at all:**

- **Closed form.** `packed(a,b) = k − [a.day > b.day]`, `naive(a,b) = k − [min(a.day, len(b)) > b.day]`.
  They differ iff `b` is the last day of its month **and** `a.day > b.day` — which is verbatim the
  predicate at `ProgressiveEMICalculator.java:1432`. And when it fires, `packed(a, b+1day) = k` = naive.
  So `nOracle ≡ nNaive`, identically.
- **Exhaustive measurement**, run inside the pinned oracle image over **every ordered date pair** in
  2000-01-01 … 2040-12-31: **112,147,776 pairs, 0 R2-vs-R4 separators**; special-case firings
  **45,253** = packed/naive disagreements **45,253**, both cross-terms **0**
  [`.softhouse/capture/periodratio/analysis/t46_monthdiff_exhaustive-output.txt`].
- **T44's proposed remedy does not work either.** `WEEKS` and `DAYS` cannot separate packed from naive
  (`plusWeeks`/`plusDays` make the overshoot branch unreachable), and the `YEARS` arm — which *can*
  separate — is **unreachable**: `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` has no YEARS
  case and throws at `:1609`. **OBSERVED**: `T46-YR-A` and `T46-YR-B` both come back
  `java.lang.UnsupportedOperationException: Invalid repayment frequency`.

**So the blind spot is PERMANENT for this generator, not `TO_BE_CAPTURED`.** Relabel the family:
*"grades the month-end special case jointly with the packed whole-months rule"*. DEC-1 must pin the
packed rule normatively alongside the special case — neither clause is safe stated alone.

## C-2 (F39-2) — `ATTESTATION.md` §4's "two independent witnesses" are ONE

The oracle's SLF4J `Initialized rounding mode…` line and `MoneyHelper.getMathContext()` are **one cache
write, logged and then read back** [VERIFIED: `MoneyHelper.java:59-64`, `:74-82`, `:91-94`]. Both are
**ambient**, and on Path A the ambient context is provably never read for a 2-dp currency. Read §4's
heading as *"the AMBIENT MoneyHelper context"*, and `run-periodratio.sh:196`'s word "effective" as
"ambient". **T42's correction list (T35, T36, T37, `reference-oracle.md`) omitted T39; it should have
included it.** No captured value is affected — §4's own closing paragraph draws the distinction
correctly, and the N7 leg is a genuine **threaded** canary.

## C-3 (F39-3) — the threaded `MathContext` was echoed as INTENT; re-emitted off the OBJECT

`CapturePeriodRatio.java:286-287` wrote the case record's `c.precision()` / `c.mode()`; nothing read
`mc`, so assertion 10 was tautological. **T46 re-emitted all sixteen cases** through
`src/CapturePeriodRatio2.java`, which echoes `mc.toString()`, `mc.getPrecision()`,
`mc.getRoundingMode()` and an explicit `wiring` field off the reference handed to `generate()`, and
`src/run-t46-periodratio.sh` asserts those.

**Identity proof: 2072 of 2072 published values IDENTICAL**, 16 of 16 captures, four new leaves per
capture and no new case in the pass [`analysis/t46_reemit_identity-output.txt`].

## C-4 (F39-4) — line citations

- the month-end special case is **`:1432`** (predicate) and **`:1433`** (nudged call), **not**
  `:1429-1434` and **not** `:1426-1436` (that is the whole `case MONTHS ->` arm; `:1429` is a
  declaration continuation and `:1434` is `} else {`).
- `daysInMonth` is computed at **`:1508`** — the prose's `:1509` is wrong, the tag was right.

## C-5 — blind spots this handoff should now record

- **`RepaymentEvery > 1` is no longer a blind spot at 2 and 3.** New captures `T46-RE-3` (MONTHS,
  every 3, drift anchoring) separates `periodRatio` from `RepaymentEvery` on **3 periods**, and
  `T46-RE-2ME` (MONTHS, every 2, 31 Jan seed) separates the special case on **2 periods**
  [`analysis/t46_arms_ratio-output.txt`].
- `installmentAmountInMultiplesOf` is honoured or lost **BY CALLER** (T44 M-4):
  `LoanScheduleAssembler` honours it; `LoanScheduleGeneratorServiceImpl` (`:44`, `generate(mc,
  modelData)`) inherits Path A's drop, because
  `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` never sets it
  [VERIFIED: `LoanApplicationTerms.java:579-606` contains zero occurrences of `MultiplesOf`].
