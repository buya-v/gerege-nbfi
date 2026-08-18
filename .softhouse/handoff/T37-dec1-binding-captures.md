# T37 — DEC-1 §8 binding captures (items 3, 3a, 3b, 3c, 3d)

**Result: all five binding items captured from the pinned reference oracle (Fineract), and all
five observations SEPARATE the right reading from the wrong one.** Eleven captures in total —
the five binding shapes with a second shape each for 3, 3b, 3c and 3d, plus a rig calibration
and a reproduction control. Everything is stored in **raw observed form only** under
`.softhouse/capture/dec1-binding/`; nothing was promoted to the vector store, and DEC-1 was not
edited.

One material defect in DEC-1 revision 6 was found while doing it, and it is reported here rather
than fixed — see **Follow-ups F-1**.

Branch: `softhouse/T37-dec1-binding-captures`. Files written: `.softhouse/capture/dec1-binding/**`
and this handoff. Nothing else was touched.

---

## Captures taken

All eleven ran through the **Path A embeddable seam** (DEC-1 §3.2), in process, in a throwaway
`docker run --rm` container against image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`. No server was started;
PostgreSQL was not contacted; the shared `fineract-fineract-1` / `fineract-db-1` containers were
not touched. Recipe: `.softhouse/capture/dec1-binding/REPRODUCE.md`. Raw output:
`.softhouse/capture/dec1-binding/out/t37-binding.json` (verbatim stdout, log lines included, in
`out/t37-binding-raw.json`; stderr was empty).

Every case pins: MNT (or USD for the calibration), `MinorUnitDigits` 2, one disbursement,
`RepaymentEvery` 1, MONTHS, DECLINING_BALANCE, `DaysInMonth DAYS_30` / `DaysInYear DAYS_360`,
`daysInYearCustomStrategy null`, down payment 0, `installmentAmountInMultiplesOf null`,
`fixedLength null`, `interestRecognitionOnDisbursementDate false`,
`allowPartialPeriodInterestCalculation true`, `allowFullTermForTranche false`, tenant timezone
`Asia/Ulaanbaatar`, tenant rounding-mode ordinal **4 (HALF_UP)**. Threaded `MathContext`
**(19, HALF_UP)** everywhere except the labelled calibration.

### Controls (not binding items, but they license everything below)

| id | shape | observed | verdict |
|---|---|---|---|
| `T37-CAL` | USD 100 / 6 × 7.0 %, threaded **(12, HALF_UP)** | term 182, level **17.01**, final **17.00**, total interest **2.05**, splits 16.43/0.58 · 16.52/0.49 · 16.62/0.39 · 16.72/0.29 · 16.81/0.20 · 16.90/0.10 | **reproduces the shipped test literal digit-for-digit** — the rig is calibrated. NOT a parity vector [VERIFIED: capture `T37-CAL`] |
| `T37-CTL-Q0a` | MNT 1,200,000 / 6 × 21.6 %, (19, HALF_UP) | level **212,787.28**, final **212,787.30**, total interest **76,723.70** | **reproduces committed observation Q0a** (`.softhouse/reviews/t23-probe/t23-probe-output.txt`) digit-for-digit through a different harness [VERIFIED: capture `T37-CTL-Q0a`] |

### Item 3 — trips the EMI re-adjust guard

**`T37-3-A`** — MNT 1,014,632 / 6 × **7.0 %**, schedule start = disbursement 2024-01-01. Observed: `loanTermInDays` 182, totalDisbursed **1,014,632.00**, totalInterest **20,815.82**,
totalRepayment **1,035,447.82**.

| # | window | principal | interest | total | balance |
|---|---|---|---|---|---|
| 1 | 2024-01-01 → 2024-02-01 | 166,655.95 | 5,918.69 | 172,574.64 | 847,976.05 |
| 2 | 2024-02-01 → 2024-03-01 | 167,628.11 | 4,946.53 | 172,574.64 | 680,347.94 |
| 3 | 2024-03-01 → 2024-04-01 | 168,605.94 | 3,968.70 | 172,574.64 | 511,742.00 |
| 4 | 2024-04-01 → 2024-05-01 | 169,589.48 | 2,985.16 | 172,574.64 | 342,152.52 |
| 5 | 2024-05-01 → 2024-06-01 | 170,578.75 | 1,995.89 | 172,574.64 | 171,573.77 |
| 6 | 2024-06-01 → 2024-07-01 | 171,573.77 | 1,000.85 | **172,574.62** | 0.00 |

**`T37-3-B`** — MNT 127,704 / 36 × 16.8 %, start = disbursement 2024-01-01. Observed: term 1096,
totalInterest **35,746.56**, level **4,540.30**, final **4,540.06**. Full 36 rows in the capture file.

### Item 3a — separates the loop's strict ADOPTION test

**`T37-3a`** — MNT 100,025 / 12 × 16.8 %, start = disbursement 2024-01-01. Observed: term 366,
totalDisbursed **100,025.00**, totalInterest **9,334.19**, totalRepayment **109,359.19**;
level **9,113.26** on periods 1–11, final **9,113.33**, per-period interest
1,400.35 / 1,292.37 / 1,182.88 / 1,071.85 / 959.27 / 845.12 / 729.36 / 611.99 / 492.97 / 372.29 /
249.91 / 125.83. Full rows in the capture file.

### Item 3b — separates the per-period interest ROUND-TRIP

**`T37-3b`** — MNT 13,202 / 6 × 16.8 %, start = disbursement 2024-01-01. Observed: term 182,
totalInterest **654.38**, totalRepayment **13,856.38**.

| # | window | principal | interest | total | balance |
|---|---|---|---|---|---|
| 1 | 2024-01-01 → 2024-02-01 | 2,124.57 | 184.83 | 2,309.40 | 11,077.43 |
| 2 | 2024-02-01 → 2024-03-01 | 2,154.32 | 155.08 | 2,309.40 | 8,923.11 |
| 3 | 2024-03-01 → 2024-04-01 | 2,184.48 | 124.92 | 2,309.40 | 6,738.63 |
| 4 | 2024-04-01 → 2024-05-01 | 2,215.06 | 94.34 | 2,309.40 | 4,523.57 |
| 5 | 2024-05-01 → 2024-06-01 | 2,246.07 | 63.33 | 2,309.40 | 2,277.50 |
| 6 | 2024-06-01 → 2024-07-01 | 2,277.50 | 31.88 | **2,309.38** | 0.00 |

**`T37-3b-2`** — MNT 3,924,149 / 6 × 16.8 %, start = disbursement **2024-01-31** (month-end seed,
so the §4.2 re-anchor is exercised too). Observed: totalInterest **194,510.78**, level
**686,443.30**, final **686,443.28**.

### Item 3c — trips the guard in the LATER-DISBURSEMENT window

**`T37-3c`** — MNT 10,548,069 / 6 × 16.8 %, schedule start 2024-01-01, single disbursement
**2024-02-01** (on repayment period 1's due date, so `|relatedRepaymentPeriods| = 5` while
`NumberOfRepayments = 6`). Observed: term 182, totalInterest **447,124.73**.

| row | window | principal | interest | total | balance |
|---|---|---|---|---|---|
| REPAYMENT 1 | 2024-01-01 → 2024-02-01 | 0.00 | 0.00 | 0.00 | **0.00** |
| DISBURSEMENT | 2024-02-01 | 10,548,069.00 | | | |
| REPAYMENT 2 | 2024-02-01 → 2024-03-01 | 2,051,365.78 | 147,672.97 | 2,199,038.75 | 8,496,703.22 |
| REPAYMENT 3 | 2024-03-01 → 2024-04-01 | 2,080,084.90 | 118,953.85 | 2,199,038.75 | 6,416,618.32 |
| REPAYMENT 4 | 2024-04-01 → 2024-05-01 | 2,109,206.09 | 89,832.66 | 2,199,038.75 | 4,307,412.23 |
| REPAYMENT 5 | 2024-05-01 → 2024-06-01 | 2,138,734.98 | 60,303.77 | 2,199,038.75 | 2,168,677.25 |
| REPAYMENT 6 | 2024-06-01 → 2024-07-01 | 2,168,677.25 | 30,361.48 | **2,199,038.73** | 0.00 |

**`T37-3c-2`** — MNT 13,549,647 / 6 × 21.6 %, disbursement 2024-02-01. Observed: totalInterest
**740,381.83**, level **2,858,005.77**, final **2,858,005.75**, repayment row 1 all zero with
balance 0.00.

### Item 3d — disbursement STRICTLY INSIDE a repayment period

**`T37-3d`** — MNT 1,200,000 / 6 × 21.6 %, schedule start 2024-01-01, single disbursement
**2024-01-15**. Observed: term 182, totalInterest **66,528.72**, totalRepayment **1,266,528.72**.
The DISBURSEMENT row is emitted **before** repayment row 1 (2024-01-15 lies in `[from, due)` of
period 1).

| # | window | principal | interest | total | balance |
|---|---|---|---|---|---|
| 1 | 2024-01-01 → 2024-02-01 | 199,242.79 | **11,845.16** | 211,087.95 | 1,000,757.21 |
| 2 | 2024-02-01 → 2024-03-01 | 193,074.32 | 18,013.63 | 211,087.95 | 807,682.89 |
| 3 | 2024-03-01 → 2024-04-01 | 196,549.66 | 14,538.29 | 211,087.95 | 611,133.23 |
| 4 | 2024-04-01 → 2024-05-01 | 200,087.55 | 11,000.40 | 211,087.95 | 411,045.68 |
| 5 | 2024-05-01 → 2024-06-01 | 203,689.13 | 7,398.82 | 211,087.95 | 207,356.55 |
| 6 | 2024-06-01 → 2024-07-01 | 207,356.55 | 3,732.42 | **211,088.97** | 0.00 |

**`T37-3d-2`** — MNT 127,704 / 36 × 16.8 %, disbursement **2024-01-20**. Observed: term 1096,
totalInterest **34,373.07**, period-1 interest **692.07**, level **4,500.95**, final **4,543.82**.

---

## What each capture discriminates

Method (`.softhouse/capture/dec1-binding/analysis/discriminate.py`): for each capture, run
DEC-1 revision 6's reading and the wrong reading side by side; take the set of cells on which
**the two readings disagree** — those are the only cells that carry information about the
question the capture was taken to settle — and ask which reading the **observation** agrees with
on exactly those cells. A cell where both readings agree tells you nothing about them.

The model is `analysis/dec1_readings.py`: T33's from-text transcription of DEC-1 revision 6
copied verbatim, plus three marked edits that add the loop-absent and no-adoption readings and a
full per-row renderer. Exact `Decimal` at explicit contexts and integer minor units throughout;
**no float anywhere on a money path**.

| capture | item | discriminating cells | observation agrees with rev 6 | with the wrong reading | verdict |
|---|---|---|---|---|---|
| `T37-3-A` | 3 | 17 | 17/17 | 0/17 | **SEPARATES** |
| `T37-3-B` | 3 | 122 | 122/122 | 0/122 | **SEPARATES** |
| `T37-3a` | 3a | 39 | 39/39 | 0/39 | **SEPARATES** |
| `T37-3b` | 3b | 4 | 4/4 | 0/4 | **SEPARATES** |
| `T37-3b-2` | 3b | 9 | 9/9 | 0/9 | **SEPARATES** |
| `T37-3c` | 3c | 14 | 14/14 | 0/14 | **SEPARATES** |
| `T37-3c-2` | 3c | 14 | 14/14 | 0/14 | **SEPARATES** |
| `T37-3d` | 3d | 25 | 25/25 | 0/25 | **SEPARATES** |
| `T37-3d-2` | 3d | 145 | 145/145 | 0/145 | **SEPARATES** |

Full output: `.softhouse/capture/dec1-binding/analysis/discriminate-output.txt`.

**Item 3 — the observation separates the readings.** On `T37-3-A` a port that never implements
`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` returns final installment **172,574.67** and
17 differing cells; the oracle returned **172,574.62**, which is the loop-present answer
[VERIFIED: capture `T37-3-A` vs `analysis/discriminate-output.txt`]. On `T37-3-B` the same
comparison is 122 cells wide and moves **total interest** too — 35,746.69 (loop absent) vs the
observed **35,746.56**. I did not instrument the guard, so I cannot say "the guard fired" as a
direct observation; what is observed is that the oracle's answer is the one only a
guard-fired-and-trial-adopted execution produces, and is not the one a port without the loop
produces. That is exactly the separation the binding asks for.

**Item 3a — the observation separates the readings.** On `T37-3a` the loop **fires**, builds a
trial, and the strict test `|newDiff| < |oldDiff|` **rejects** it. A port that omits step 7 adopts
anyway and returns level **9,113.20** / total interest **9,334.17**; the oracle returned
**9,113.33** final with level **9,113.26** and total interest **9,334.19**
[VERIFIED: capture `T37-3a`]. Note the shape is a *pure* 3a discriminator: on it the loop-absent
reading is **identical** to revision 6 (0 differing cells, `analysis/select_shapes-output.txt`),
so this capture grades 3a and grades nothing about item 3 — which is precisely why revision 4
split them into two items, and this is the first empirical confirmation that the split was right.

**Item 3b — the observation separates the readings.** The textbook `balance × rateFactor` gives
final **2,309.39** and total interest **654.39**; the oracle gave **2,309.38** and **654.38**
[VERIFIED: capture `T37-3b`]. `T37-3b-2` separates them 9 cells wide on a month-end seed
(194,510.79 vs the observed **194,510.78**). So §4.3.2's three separately `MathContext`-rounded
operations — `× rateFactorTillPeriodDueDate`, `÷ lengthTillPeriodDueDate`, `× length` — are now
**graded**, and the "they cancel, so collapse them" shortcut is now refuted by observation rather
than by re-derivation. The gap is one minor unit; that is the whole point — it is a payable amount.

**Item 3c — the observation separates the readings.** Reading `n` as `NumberOfRepayments` instead
of `|relatedRepaymentPeriods|` gives final **2,199,038.77**; the oracle gave **2,199,038.73**, and
the wrong reading also shifts the level installment and every period's principal/balance —
14 cells. `T37-3c-2` reproduces the separation at a different rate and principal
[VERIFIED: captures `T37-3c`, `T37-3c-2`]. **Caveat, and it is a real one:** on these two captures
DEC-1 revision 6 as transcribed does **not** reproduce every cell — it misses repayment row 1's
`balance` (see **F-1**). It reproduces every cell on which the two `n` readings differ, so the
separation on the `n` question stands; but this capture is *not* a clean end-to-end conformance
vector until F-1 is resolved.

**Item 3d — the observation separates the readings, by the widest margin in the set.** A port that
hard-codes the day-count ratio to 1 charges a full month's interest on a 17-day exposure: period-1
interest **21,600.00** and total interest **76,723.81**. The oracle returned period-1 interest
**11,845.16** and total interest **66,528.72** — an observed gap of **MNT 10,195.09** in total
interest on a MNT 1.2 M loan, with all 25 discriminating cells going to revision 6
[VERIFIED: capture `T37-3d`]. `T37-3d-2` separates them across **145** cells (34,373.07 vs
35,762.25). **P0-T32-1 is now settled empirically**: §4.1.1's proration is what the oracle does,
and the clause revision 6 deleted from `contract.go` is observed false. The figures DEC-1 §4.3.2
records as re-derivations for this shape (11,845.16 / 211,087.95 / 211,088.97 / 66,528.72) are now
**observed** — but see **F-2** before anything is done with that.

---

## Attestation

Full attestation with every check and every digest:
`.softhouse/capture/dec1-binding/ATTESTATION.md`. Summary:

- **Pinned Fineract commit** `426a23544e8426a38ae43ae404670a0a7e85b9eb`, checkout clean
  [VERIFIED: `git -C /Users/buv/fineract rev-parse HEAD`, `status --porcelain` empty].
- **Image** `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`,
  created 2026-08-17T11:29:56Z; `/app/fineract-provider.jar` sha256
  `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9`.
- **Seam-class diff: no output — byte-identical** to the pinned original; sha256
  `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`. My copy lives under
  `dec1-binding/src/`; `.softhouse/capture/src/` was never read from or written to.
- **JVM**, read inside the container: `openjdk 21.0.11 2026-04-21 LTS`, Zulu21.50+19-CA,
  build `21.0.11+10-LTS`, vendor Azul Systems, Inc.
- **`MathContext` in force, on the oracle's own testimony, two independent witnesses:**
  (a) the oracle's SLF4J log, 11 of 11 lines `Initialized rounding mode for tenant '<id>': HALF_UP`
  (`out/t37-binding-log.txt`); (b) `MoneyHelper.getMathContext()` echoed per case as
  `precision=19 roundingMode=HALF_UP`, with `MoneyHelper.PRECISION` read as **19**. Threaded
  context `(19, HALF_UP)` on all ten parity candidates; `(12, HALF_UP)` on the labelled calibration
  only.
- **Determinism:** the whole run was executed a second time from a fresh container and the JSON
  payload is **byte-identical** (`diff` clean).
- **Calibration passed** (`T37-CAL` reproduces the shipped literal) and **reproduction control
  passed** (`T37-CTL-Q0a` reproduces committed Q0a digit-for-digit).
- **No float:** all amounts rendered with `BigDecimal.toPlainString()`; no `double`/`float`/
  `doubleValue()` on any amount path in the harness, and none in the analysis model.
- **sha256 of every output file** is listed in `ATTESTATION.md` §8.
- The harness additionally emits the three per-period columns audit T22 recorded as missing —
  `fromDate`, `fee`, `penalty` — so a later promotion does not need a re-capture for them.
- **Storage:** raw observed form only, under `.softhouse/capture/dec1-binding/`. **Nothing
  promoted to the vector store** — DEC-1 is revision 6 and UNRATIFIED (G-1 open), and the shape is
  what is being ratified. Rationale in `PROVENANCE.md`.

---

## Items I could not capture (and why)

**None. All five binding items were captured, and all five separate.** For completeness, the two
things I deliberately did *not* do:

- I did not capture anything for §8 items 1, 2, 4, 5, 6 or 7 — out of scope for T37.
- I did not attempt anything requiring the running server (Path B). Another worker holds it this
  fire, and none of the five shapes needs it: all five live inside the progressive schedule
  generator, and all five pin `installmentAmountInMultiplesOf` and `daysInYearCustomStrategy` to
  the inert values that make Path A's blind spot empty (DEC-1 §3.2).

---

## Unverified

- **"The guard fired."** I did not instrument `EmiAdjustment` or `ProgressiveEMICalculator`, so no
  capture directly observes the guard's three conjuncts evaluating true. What is observed is that
  the oracle's output matches the loop-present reading and not the loop-absent one. `[UNVERIFIED
  as a direct observation; VERIFIED as a discrimination: analysis/discriminate-output.txt]`
- **Iteration count.** Nothing here observes how many of the at-most-three adopted iterations ran
  on any shape. `[UNVERIFIED]`
- **The mechanism behind F-1.** My reading of the source (below) explains the observed 0.00, but I
  did not instrument it, so the *mechanism* is a source reading, not an observation. The **0.00
  itself is observed**, twice here and once in the already-committed Q0b.
- **Counts quoted from earlier reviews** — T26's 2,855/2,156, T29's 699/43,992 and 2,143/120,000,
  T32's 2,913/2,913 and MNT 1,816,050.11 — are **re-derivations by those tasks**. I did not re-run
  their sweeps and this task neither confirms nor disputes them. `[UNVERIFIED here]`
- **Generalisation.** Nine binding captures grade nine shapes. They do not license any claim about
  an un-sampled `(principal, term, rate, disbursement-date)` tuple — DEC-1 §4.1's "there is no size
  threshold" applies unchanged.

---

## Follow-ups

**F-1 (P0 for DEC-1, and it is a money field). DEC-1 §4.3.2 step 4 mis-states
`OutstandingPrincipalMinor` on a pre-disbursement repayment row in the later-disbursement window.**
I did not edit DEC-1; reporting it as instructed.

- Step 4 says `OutstandingPrincipalMinor = max(0, balance carried in + amounts disbursed in this
  period − PrincipalMinor)`, citing `RepaymentPeriod.java:389-403`. Transcribed literally, on
  `T37-3c` that gives repayment row 1 a balance of **10,548,069.00**.
- **The oracle returned 0.00** [VERIFIED: captures `T37-3c`, `T37-3c-2`], and the same 0.00 appears
  on the already-committed observation Q0b (`.softhouse/reviews/t23-probe/t23-probe-output.txt`
  line 20) — so this is not new oracle behaviour, it is a defect in the *specification* that no
  prior check could see.
- **Why no prior check saw it:** T33's from-text experiment compares only
  `(level, final, total interest)` (`t33_spec_check.py::summarise`). Row 1's balance is not in
  those three numbers, so revision 6 passes 13/13 while getting this cell wrong. **Full-row
  comparison is what found it, and the corpus-validation scripts should be widened to compare
  every cell.**
- **Mechanism, from source** `[UNVERIFIED as an observation; source read at the pin]`: the plan's
  per-row balance is `LoanScheduleModelRepaymentPeriod.getOutstandingLoanBalance()`, set at
  `ProgressiveLoanScheduleGenerator.java:132` **during that period's own iteration**. The
  disbursement is only registered into the interest schedule model at `:351`, inside
  `processDisbursements`, which fires for the period satisfying
  `!disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)` —
  `[from, due)`, from-inclusive **due-exclusive** (`:307-309`). A disbursement on period 1's due
  date therefore belongs to period **2**'s iteration, so period 1's balance is read before any
  disbursement exists. Note this `[from, due)` rule is a **third** date-membership rule, distinct
  from both membership rules DEC-1 §4.3.1 states, and DEC-1 states it nowhere.
- **Scope of the error:** it affects only repayment rows before the first related period, which
  only the later-disbursement window produces. All other cells on `T37-3c` / `T37-3c-2` reproduce
  exactly, and item 3c's separation is unaffected.
- **Recommendation:** a DEC-1 revision 7 stating (a) that a pre-disbursement repayment row's
  `OutstandingPrincipalMinor` is **zero**, not the amount awaiting disbursement, and (b) the
  `[from, due)` disbursement-attachment rule that produces it and the emitted row order. That is a
  contract change on an unratified draft — agent work under CLAUDE.md's amended rule — but it is
  **not mine to make**, and it should be re-derived independently before it is written.

**F-2. Do not copy the observed 3d figures into DEC-1 §4.3.2 as a correction of its re-derived
table.** The re-derived and observed figures happen to agree there, which is a good sign — but
DEC-1 labels that table "re-derivation, not observation" deliberately, and promoting observed
numbers into the contract body while G-1 is open re-creates the exact contract-shaped-storage
problem this task was told to avoid. Cite `.softhouse/capture/dec1-binding/` instead.

**F-3. The five binding items are now capturable-and-captured, but the binding is a *conformance*
precondition, not a capture one.** DEC-1 §8's binding says no conformance PASS may be claimed and
no cutover proposed until an **admissible vector** exists for each. These are attested observations,
not vector-store entries. Closing the binding needs the promotion step (§8 item 1: attestation
block, per-period columns — this harness now emits all three — and a committed run recipe, which
`REPRODUCE.md` supplies), and that promotion should happen **after** G-1 closes. Cutover remains a
hard `user` gate regardless.

**F-4. Widen the corpus-validation scripts to full-cell comparison.** F-1 is the second defect in
this program found by comparing something the existing check did not look at. `discriminate.py`'s
`cells()`/`compare()` pair is a drop-in pattern: flatten to an addressable cell map, diff every
cell, and report separation only on the cells where the two readings actually disagree.

**F-5. Item 3's shape does not grade 3a and 3a's shape does not grade item 3** — measured, not
assumed (`analysis/select_shapes-output.txt`). Any future "one vector closes both" proposal should
be checked against that output first.
