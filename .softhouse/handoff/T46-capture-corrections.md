# T46 — capture corrections against audit T44

**Task:** T46, branch `softhouse/T46-capture-corrections`, worker `test_writer`.
**Corrects:** the three capture sets audited by T44 — `.softhouse/capture/periodratio/` (T39),
`.softhouse/capture/charges/` (T40), `.softhouse/capture/mathcontext/` (T42).

**Reference oracle (Fineract) reachability, this fire: REACHABLE** [VERIFIED by this task:
`actuator/health` → `{"status":"UP","groups":["liveness","readiness"]}`; `fineract-fineract-1`
(`fineract:latest`) up 16 h healthy, `fineract-db-1` (`postgres:18.3`) up 38 h healthy;
`docker image inspect fineract:latest` → the pinned digest
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`; pinned checkout
`/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty].
So this task **re-executed and captured** rather than only re-writing.

> **RAW OBSERVED FORM ONLY. NOTHING PROMOTED TO THE PARITY VECTOR STORE, NOTHING CONTRACT-SHAPED.**
> Gate **G-1** is open and DEC-1 is unratified. Every artefact added here is a raw payload, a sidecar
> derived from one by a proved-identity transformation, an analysis script, or a correction to a claim.

**Discipline observed.** Path A work ran in throwaway `docker run --rm` containers on the pinned image.
Path B work was **additive only** against tenant `gerege`: no restart, no re-tenant, no schema write,
and **no charge definition created, modified or deleted** — T40's `m_charge` ids 1–12 were used exactly
as they stand (`m_charge` count unchanged). `/Users/buv/fineract` was read only; no Gradle build ran.
Write surface: `.softhouse/capture/{periodratio,charges,mathcontext}/**` plus this handoff and appended
corrections to the T39/T40/T42 handoffs. `docs/adr/**`, `nexus/**`, `.softhouse/reviews/**`,
`.softhouse/capture/audit-t44/**`, `tasks.json`, `program.json`, `RESUME.md`, `reference-oracle.md`,
`patterns.md`, `gates.md` and `LOCK` were **not** touched.

---

## 0. Headline

**The headline result is a negative one, and it is the strongest thing in this pass.**

> **The month-end special case cannot be separated by itself — anywhere.** Not "not yet captured": *not
> capturable* within the progressive generator. Proved in closed form, measured exhaustively over
> **112,147,776 ordered date pairs** inside the pinned oracle image, and the escape route T44 proposed
> is closed by an **observation**: the `YEARS` arm throws.

Everything else this task did was to make each set's claims exactly as strong as its evidence, and to
close by capture the two gaps the oracle could settle:

| finding | status | how |
|---|---|---|
| **F39-1** month-end family grades a PAIR | **CLOSED — the special case is provably non-separable** | closed form + 112 M-pair exhaustive sweep + `T46-YR-*` observed throw |
| **F39-2** T39's attestation repeats T37's defect | **CLOSED** | attestation corrected; T39 added to the amended list |
| **F39-3** threaded context echoed as intent | **CLOSED by re-emission** | 16 cases re-emitted with the object echo; **2072 / 2072 values identical** |
| **F39-4** imprecise line citations | **CLOSED** | four citations corrected, each re-opened by this task |
| **A-1** Path B wiring citation absent | **CLOSED** | five sites cited and verified |
| **A-2** D-1 cites the site of agreement | **CORRECTED (on T44's evidence)** | pointer moved to `:392` + `ScheduleCurrentPeriodParams.java:144-145` |
| **A-3** corpus cannot see which input supplies the money | **CLOSED by capture** | 7 new captures; **request governs, 7 for 7** |
| **A-4** C5 shipped as an invariant | **CLOSED** | relabelled probe **P5**, signed delta, new failable suite |
| **A-5** false negative claim about half-cent ties | **CLOSED by capture** | **two exact ties observed**, both `HALF_UP`; rounding locus re-derived |
| **A-6** response scale ungraded | **SHARPENED** | scale is **caller-controlled**: `6000.000` observed |
| **A-7** recipe hard-codes a dead worktree | **CLOSED** | 11 files self-locating; **21 / 21 responses byte-identical** on re-issue |
| **A-8** one ambient witness counted twice | **CLOSED** | corrected with the `MoneyHelper.java:59-64` mechanism |
| **T44-X1** Path B float-shaped on the wire | **CLOSED** | 57 exact-text sidecars, identity-proved, no float constructed |
| **M-3, M-4, M-5, M-10, M-11** and M-1/M-2/M-6…M-9 | see §6 | delegated leg; `T46-mathcontext-corrections.md` |

**Two new findings** this pass raises are in §7.

---

## 1. F39-1 — the month-end special case has NO separating shape

Full working: `.softhouse/capture/periodratio/ATTESTATION-T46.md` §1.

### The argument

`calculatePeriodRatio` [`ProgressiveEMICalculator.java:1419-1459`] returns a pure function of
`(seedDate, fromDate, dueDate, n)`; `n` is read at `:1441` and `:1449` and nowhere else [VERIFIED: the
method opened by this task]. So readings that agree on `n` return byte-equal ratios, hence equal money.

With `k = (b.year*12+b.month) − (a.year*12+a.month)`:

- **packed** (`ChronoUnit.MONTHS.between`, via `DateUtils.getExactDifference` [`DateUtils.java:308-317`])
  `= k − [a.day > b.day]`
- **naive** ("count calendar months, step back one if `plusMonths` overshoots")
  `= k − [min(a.day, len(b)) > b.day]`

They differ **iff** `a.day > b.day` **and** `len(b) ≤ b.day`, i.e. **`b` is the last day of its month
and `a.day > b.day`** — verbatim the predicate at **`:1432`**. And when it fires, the oracle takes
`packed(a, b + 1 day)`; `b+1` is the first of the next month and `a.day ≥ 29 > 1`, so that is `k` —
exactly what naive returns. **`nOracle ≡ nNaive`, identically. The special case IS the compensation.**

### The measurement

`analysis/T46MonthDiffExhaustive.java`, compiled and run **inside the pinned oracle image** (so the
`java.time` semantics are the oracle's own, `java.vm.version 21.0.11+10-LTS`), over **every ordered date
pair** in 2000-01-01 … 2040-12-31 [`analysis/t46_monthdiff_exhaustive-output.txt`]:

```
ordered date pairs swept                    : 112147776
month-end special case FIRES (:1432)        : 45253
nPacked != nNaive                           : 45253
fires AND nPacked == nNaive                 : 0
does NOT fire AND nPacked != nNaive         : 0
nOracle != nNaive   [R2 vs R4]              : 0
nOracle != nPacked  [R2 vs R3]              : 45253
YEARS arm: yPacked != yNaive                : 165
first YEARS separator found                 : seed=2000-02-29 from=2001-02-28 yPacked=0 yNaive=1
```

T44 swept 59,130 `(start, period)` pairs and found 701 = 701 with 0 divergences. This is the whole date
space, and it is a superset by construction.

### T44's proposed escape route is closed, by observation

T44 wrote that a packed-vs-naive discriminator *"has to come from `calculatePeriodRatio`'s `YEARS` /
`WEEKS` / `DAYS` arms"*. All three are now captured (§3) and none of them delivers one:

- **`WEEKS` / `DAYS` cannot separate packed from naive at all** — `plusWeeks(k)` is `+7k` days and
  `plusDays(k)` is `+k` days, so the overshoot branch is unreachable and the two functions coincide.
  Measured `0` in the same sweep.
- **`YEARS` *does* separate** (165 pairs, all 29 Feb → 28 Feb) — **but the YEARS arm is unreachable.**
  `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` [`:1602-1610`] has `DAYS`, `WEEKS`, `MONTHS`
  and then `default -> throw new UnsupportedOperationException("Invalid repayment frequency")` at
  **`:1609`**. The YEARS ratio is computed at `:1405` and thrown away into that exception.

**OBSERVED** [`out/t46-periodratio-arms.json`]: `T46-YR-A` (29 Feb 2020 seed — the separator shape) and
`T46-YR-B` (ordinary seed) both return
`java.lang.UnsupportedOperationException: Invalid repayment frequency`.

### So

**Relabel the `T39-ME-*` family** to *"grades the month-end special case **jointly with** the packed
whole-months rule"*. They grade that pair on **12 periods** (independently re-derived, §3). A port with
two cancelling defects passes all four **and is correct on this arm** — which is the honest way to put
it, and better than "there is a vector we have not taken yet", because there is not one and never will be.

**For DEC-1 (T45's surface, not T46's):** pin the **packed** rule normatively alongside the special
case, or state the naive rule with no special case. The three formulations are equivalent only as
pairs; every single clause on its own is wrong.

---

## 2. F39-2 / F39-3 — the attestation, and a proved re-emission

**F39-2.** `ATTESTATION.md` §4's *"two independent witnesses to the mode, both from the oracle"* are
**one witness**: the SLF4J `Initialized rounding mode…` line and `MoneyHelper.getMathContext()` are one
cache write, logged and then read back [VERIFIED by this task: `MoneyHelper.java:59-64` emits the log
line from the same local it puts into `roundingModeCache`; `:74-82` reads it back; `:91-94`
`computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))`]. Both are **ambient**,
and on Path A the ambient context is provably never read for a 2-dp currency (T42 E1). The heading and
`run-periodratio.sh:196`'s word "effective" are corrected to **ambient** in
`capture/periodratio/ATTESTATION-T46.md`. **T42's amended-attestations list named T35/T36/T37 and
`reference-oracle.md` and omitted T39; T39 belongs on it.** *(That list lives in
`.softhouse/reference-oracle.md`, which is outside T46's write surface — see §8, escalations.)*
**No captured value is affected.**

**F39-3 — closed by re-emission, not by argument.** `src/CapturePeriodRatio2.java` echoes, off the
`MathContext` reference actually handed to `EmbeddableProgressiveLoanScheduleGenerator.generate(mc,
modelData)`: `mc.toString()`, `mc.getPrecision()`, `mc.getRoundingMode()`, plus an explicit `wiring`
field. `src/run-t46-periodratio.sh` asserts **those**, requires `mc.toString()` to agree with its own
getters, requires intent not to have drifted from object, and says **AMBIENT** where T39 said
"effective".

**The identity proof `patterns.md` demands before any new column may be trusted**
[`analysis/t46_reemit_identity.py`, `…-output.txt`]:

```
captures compared            : 16
leaves + top-level compared  : 2072
RESULT: 2072 of 2072 published values IDENTICAL.
```

Four new leaves per capture, **no new case in the pass** — new cases went into a separate pass with
separate ids, because mixing them would have destroyed the identity check (T35's lesson).

---

## 3. New Path A pass — the uncaptured arms, and `RepaymentEvery > 1`

`-Dt46.set=arms`, new ids, separate payload `out/t46-periodratio-arms.json`. Closes T44 periodratio
blind spots **2** and **3**.

| capture | freq | every | observed |
|---|---|---|---|
| `T46-ARM-CTL` | MONTHS | 1 | control (inputs identical to `T39-CTL-Q0a`); term 182 d, total interest `76723.70` |
| `T46-YR-A` / `T46-YR-B` | YEARS | 1 | **THROW** `UnsupportedOperationException: Invalid repayment frequency` |
| `T46-WK-A` | WEEKS | 1 | term 42 d, total interest `17701.61` |
| `T46-WK-B` | WEEKS | 1 | disbursement after start; term 42 d, total interest `15518.91` |
| `T46-WK-C` | WEEKS | 2 | term 84 d, total interest `35525.93` |
| `T46-DY-A` | DAYS | 1 | term 6 d, total interest `2521.26` |
| `T46-DY-B` | DAYS | 10 | term 60 d, total interest `25325.62` |
| `T46-RE-2` | MONTHS | 2 | term 366 d, total interest `155652.82` |
| `T46-RE-3` | MONTHS | 3 | drift anchoring; term 550 d, total interest `236687.94` |
| `T46-RE-2ME` | MONTHS | 2 | 31 Jan seed; term 366 d, total interest `155652.82` |

### What it DISCRIMINATES — measured, not assumed

`analysis/t46_arms_ratio.py` re-implements `calculatePeriodRatio` and `calculateSeedDate` **from the
pinned source only**, in exact integer date arithmetic, and reports the ratio (never money) under each
of T44's four readings over **186 repayment periods** across both T46 passes:

```
periods where R1 (RepaymentEvery) differs from the pinned R2 : 41
periods where R3 (no month-end special case) differs from R2 : 12
periods where R4 (naive whole-units, no special case) != R2  : 0
```

- It **reproduces T39's own separations independently** — the eight `T39-P0-*` captures separate R1 on
  38 periods, the four `T39-ME-*` separate R3 on 10 — through code that never reads T39's `analysis/`.
- **`T46-RE-3` separates R1 on 3 periods at `RepaymentEvery = 3`** — the program's first capture that
  discriminates `periodRatio` from `RepaymentEvery` at `RepaymentEvery ≠ 1`. T44 blind spot 3 said a
  port could get the multiplier right and `RepaymentEvery` wrong and still pass all 16. It no longer can.
- **`T46-RE-2ME` separates R3 on 2 periods at `RepaymentEvery = 2`** — month-end anchoring outside the
  every-1 lattice.
- **`T46-WK-*`, `T46-DY-*`, `T46-RE-2`, `T46-ARM-CTL` separate NOTHING** among R1/R3/R4. Stated because
  it is true: they add arm coverage, not discriminating power. *Coverage is what a corpus can
  distinguish.*

**Failable and deterministic** [`capture/periodratio/NEGATIVE-TESTS-T46.md`]: the `arms` pass re-executed
from a fresh throwaway container is **byte-identical**
(`sha256 eab5dc0cd8e9b74e428c9d8cd0d87a8ea72129c01fe1375ec679b624fb893fc4`); forcing the **threaded**
rounding mode to `DOWN` exits 1 with 13 breaches read off the `MathContext` **object**; a wrong seam
sha exits 1 before any capture runs.
- **R4 = R2 on all 186 periods** — §1's proof arriving a third way, on real observed schedules.

---

## 4. Charges — A-3 and A-5 closed by capture

Full working: `.softhouse/capture/charges/ATTESTATION-T46.md`; requests `req/calc-T46-CH-0*.json`;
responses `out/t46/`; analysis `out/t46/DEFVSREQ.txt`.

### A-3 — the **request** supplies the money. `m_charge.amount` is ignored.

| capture | charge (time, calc) | definition | request | DEFINITION would give | **OBSERVED** |
|---|---|---|---|---|---|
| `T46-CH-01` | 4 (8, 4) pct of interest | `3.750000` | `1.25` | `810.00` | **`270.00`** |
| `T46-CH-02` | 1 (1, 1) flat, disbursement | `15000.000000` | `7777.77` | `15000.00` | **`7777.77`** |
| `T46-CH-03` | 4 (8, 4) | `3.750000` | `0.021875` | `810.00` | **`4.73`** |
| `T46-CH-04` | 4 (8, 4) | `3.750000` | `0.009375` | `810.00` | **`2.03`** |
| `T46-CH-05` | 5 (8, 3) pct of amount+interest | `1.234500` | `2.5` | `1383.65685765` | **`2802.06`** |
| `T46-CH-06` | 3 (1, 2) pct of amount, disbursement | `1.234500` | `0.5` | `14814.00` | **`6000.000`** |
| `T46-CH-07` | 8 (8, 1) flat PENALTY / instalment | `1200.000000` | `333.33` | `1200.00` | **`333.33`** |

**Seven for seven, across four `charge_calculation_enum` values, two `charge_time_enum` values, fee and
penalty.** Mechanism: `ProgressiveLoanScheduleGenerator.java:445-446` / `:464-465` use
`loanCharge.getPercentage()` — the `LoanCharge`'s own field, populated from the request — and flat
charges take `loanCharge.amount()` / `amountOrPercentage()` at `:412` / `:449`.

**Consequence: the vector's fixture is the REQUEST BYTES.** `attestation.json`'s `charges_as_persisted`
block stays load-bearing for the enums and is load-bearing for **no money value in the set**.
Corroborated by T44's AP-5/AP-6 with different values on a different task.

### A-5 — T40 §11's proof is false; two half-cent ties observed

`0.021875 %` of period-1 interest `21600.00` is **exactly `4.725`** → observed **`4.73`**;
`0.009375 %` is **exactly `2.025`** → observed **`2.03`**. `HALF_EVEN` would give `4.72` / `2.02`.

**The rounding locus, re-derived — and it is ambient:**

1. `ProgressiveLoanScheduleGenerator.java:445-446` multiplies and divides under the **threaded** `mc`
   (exact at precision 19 for these inputs — no rounding).
2. The result is wrapped by the **two-argument** `Money.of(MonetaryCurrency, BigDecimal)`
   [`Money.java:114-116`], which supplies **`MoneyHelper.getMathContext()` — the AMBIENT context**.
3. `Money.java:52` does `setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())`.

**A Go port that threads one `MathContext` and forgets the ambient fallback will get interest right and
charge ties wrong.** This is `patterns.md`'s "hidden second rounding context" landing on charges.

### A-4 — C5 relabelled

`bin/t46-invariants.py` keeps `C1 C2 C3 C4 C6 C7 C8 C9 C10` as invariants (**0 failures over 28
captures**) and reports C5 as **probe P5**: the signed delta `TRE − Σ rows` in integer minor units,
**non-zero on 20 of 28**, from `−1,361` to `−5,190,000`. Proved failable (`--negative` → exit 1, three
broken invariants). T40's `bin/invariants.py` is left as its committed evidence and still reproduces
`out/INVARIANTS.md` byte-for-byte.

### A-6 — response scale is caller-controlled

`0.5 %` of `1200000.00` returns **`6000.000`** on the wire — scale **3**, because nothing on the
disbursement path wraps it in `Money`, so the currency's 2 decimal places are never applied (the
instalment path *is* wrapped, which is why `T46-CH-03` comes back at scale 2). Comparing these as
numbers rather than as text silently passes a port emitting `6000.00`. **Response scale remains
ungraded by every check in the corpus.**

### A-7 — the recipe runs again

11 `bin/` files made self-locating by `bin/t46-fix-paths.py`. **Proved to change nothing: 21 of 21
committed responses re-issued BYTE-IDENTICAL** against the live oracle — a **third** independent issue
of the corpus, on a different day by a different task [`out/t46-reissue/IDENTITY.txt`].

### A-1 / A-8 — the attestation

A-1: five wiring sites cited and re-opened by this task — `LoanScheduleAssembler.java:753`, `:777`,
`:797` read `MoneyHelper.getMathContext()`, `:765` hands that reference to `generate(mc, …)`, and
`LoanScheduleGeneratorServiceImpl.java:44` likewise. **On Path B the ambient context IS the threaded
object**, which is why T40's ambient reading was right — rule 4 just requires it be said and cited.
A-8: the `c_configuration` row and the `MoneyHelper` init line are **one** witness.

---

## 5. T44-X1 — exact-text serialisation for Path B

**The decision, and what it does to already-committed records:**

1. **Raw response bytes stay canonical and are NOT rewritten.** A JSON number literal on the wire is
   already exact text; the hazard is entirely in the consumer. Mutating a committed capture to fix a
   consumer bug would destroy the only thing that makes it evidence.
2. **57 exact-text sidecars** `<name>-exact.json` are **added**, in which every JSON number is
   re-emitted as a JSON **string** carrying the wire literal byte for byte
   [`bin/t46-exacttext.py`, `out/t46/EXACT-TEXT.md`].
3. **No float is constructed producing them.** Python's decoder hands the *raw matched literal* to
   `parse_float` / `parse_int`, so `json.loads(text, parse_float=str, parse_int=str)` yields the
   original characters and never touches a binary double.
4. **Identity is proved, not asserted:** every sidecar is re-read and required to agree with its raw
   capture leaf-for-leaf **as text** and to carry **zero** bare JSON numbers. All 57 pass; the check is
   failable (`--negative`, exit 1).
5. Measured independently: **17,693 bare JSON number occurrences across 552 distinct literals**;
   **65** distinct literals would have their **text** changed by a float round-trip. Path A control:
   **0** bare decimal numbers in all five Path A payloads.

**Admissibility rule that must travel with any promoted Path B vector: compared as EXACT DECIMAL TEXT,
never through a JSON number.** In Go: never `encoding/json` into `interface{}` (which yields `float64`)
— use `json.Number`, or read the sidecar's strings.

---

## 6. `mathcontext` (M-1 … M-11)

Run as a delegated leg on a disjoint write surface. Its findings, working and identity proofs are in
**`.softhouse/handoff/T46-mathcontext-corrections.md`**, and the corrections themselves in
`.softhouse/capture/mathcontext/**`. Read that handoff alongside this one; anything it could not close,
and anything it needs escalated outside its write surface, is listed there and repeated in §8.

**M-4 is recorded in both of the other two sets' blind-spot lists**, as T44 required: the REST
`calculateLoanSchedule` path via `LoanScheduleAssembler` **honours**
`installmentAmountInMultiplesOf` [VERIFIED by this task: `out/control/B-02-multiplesof100-raw.json`
period 1 `totalInstallmentAmountForPeriod` is `112100.00`, against `112082.37` in the `B-01` baseline],
while `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` (`:44` ambient `mc`,
then `generate(mc, modelData)`) inherits Path A's drop, because
`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` never sets it
[VERIFIED: `LoanApplicationTerms.java:579-606` contains **zero** occurrences of `MultiplesOf`].
**The field is honoured or lost BY CALLER, and DEC-1 must not state its behaviour unconditionally.**

---

## 7. New findings this pass raises

### **N46-1 (P1) — the charge rounding mode is AMBIENT, not threaded.**

`ProgressiveLoanScheduleGenerator.java:445-446` computes the percentage under the **threaded** `mc`, then
hands it to the **two-argument** `Money.of` [`Money.java:114-116`], which injects
`MoneyHelper.getMathContext()`; the scale-2 rounding then happens at `Money.java:52` under **that**
context's rounding mode. On Path B the two coincide, so nothing observed here is wrong — but a port that
threads one context and forgets the ambient fallback rounds charge ties by the wrong rule. It is
undetectable by every capture in the program today, because no capture has the two modes disagreeing.
**`TO_BE_CAPTURED` (needs a tenant write; not permissible for this task).**

### **N46-2 (P2) — the disbursement-row charge scale is caller-controlled.**

`6000.000` (scale 3) from a request amount of `0.5`; `7777.77` (scale 2) from `7777.77`;
`14814.000000` (scale 6) from `1.2345`. The disbursement path never wraps the value in `Money`, so the
currency's decimal places are never applied. **Any comparison that parses these as numbers rather than
as text is blind to it** — which is exactly why T44-X1's exact-text rule matters, and is the first case
found where a float/number comparison would have hidden a real behaviour.

---

## 8. What I could NOT close, and escalations

**Could not close:**

- **A separating shape for the month-end special case.** There is none (§1). Recorded as *not
  capturable* rather than `TO_BE_CAPTURED`, with the argument.
- **Ambient vs threaded rounding mode inside charge arithmetic** (N46-1). Separating them requires the
  two to differ, which on Path B means writing the tenant's rounding mode on the **shared** server. T46
  is forbidden to restart or re-tenant it, and a sibling was running. `TO_BE_CAPTURED`.
- **Whether `m_charge.amount` governs when the request OMITS `amount`.** Every capture in the corpus
  supplies it. `TO_BE_CAPTURED`.
- **A-2's replacement citation** was **not** re-opened by T46; it rests on T44's evidence and T44's
  parent auditor's re-verification. `[VERIFIED on T44's evidence; UNVERIFIED by this task]`
- **`chargeTimeType = OVERDUE_INSTALLMENT`**, tranche/multi-disbursement charges, `minCap`/`maxCap`,
  the cumulative generator, `Asia/Hovd`, and anything needing a persisted loan — unchanged from T40.
- **`RepaymentEvery > 3`**, `DaysInMonth = ACTUAL`, `DaysInYear = ACTUAL`, multi-disbursement, down
  payments, `fixedLength`, `interestRecognitionOnDisbursementDate` — unchanged from T44.
- **Whether precision 19 is observable at all on the Path A seam.** T39 found 19 and 12
  indistinguishable across sixteen shapes; T46's eleven new shapes do not change that.

**Escalations — corrections needed in files outside T46's write surface:**

1. **`.softhouse/reference-oracle.md`** — T42's amended-attestations list (T35, T36, T37) must gain
   **T39** (F39-2). *Owner: the orchestrator.*
2. **`.softhouse/reference-oracle.md`** — the folded-in N-3 total *"13 `new MathContext(15|10, …)`"* is
   a double count; see the delegated leg's handoff for the re-derived inventory. *Owner: the
   orchestrator.*
3. **DEC-1 (`docs/adr/**`, T45's surface this fire)** — the month-end obligation must pin the **packed**
   whole-months rule normatively alongside the special case (§1); and the
   `installmentAmountInMultiplesOf` obligation must be stated **per caller**, not unconditionally (§6).
4. **`.softhouse/patterns.md`** — candidate lesson: *a blind spot can be closed by proving it
   unclosable, and that is a better outcome than a `TO_BE_CAPTURED` that can never succeed.*
   *Owner: the orchestrator's postmortem.*

---

## 9. Unverified

- **That §1's closed form holds outside the swept range.** The measurement is exhaustive over ordered
  pairs in 2000-01-01 … 2040-12-31 (112,147,776); the argument is arithmetic over
  `(k, a.day, b.day, len(b))` and has no year dependence, but it is a re-derivation, not a machine-checked
  proof. `[VERIFIED on the swept range and by closed form; UNVERIFIED as a machine proof]`
- **That `n` is the only thing the three readings change** — read off `:1419-1459` by this task, not
  established by instrumentation. `[VERIFIED by reading; UNVERIFIED by instrumentation]`
- **That the YEARS throw is unconditional** — observed on two shapes and re-derived from `:1602-1610`.
  `[VERIFIED on T46-YR-A/B; UNVERIFIED as universal]`
- **That "the request governs" holds for charge types not tried** — observed on
  `charge_calculation_enum` 1, 2, 3, 4 and `charge_time_enum` 1, 8. Enum 5, enum 9 and
  `charge_time_enum` 2 were not re-tested with a disagreeing amount.
  `[VERIFIED on seven captures; UNVERIFIED as a general rule]`
- **That §4's rounding locus is the only one on the charge path.** It is the one the two observed ties
  went through; caps, taxes and the separated path may add others. `[UNVERIFIED]`
- **That `HALF_UP` at a charge tie is the tenant mode rather than a coincidence.** The tenant mode was
  not moved, so the ties are consistent with `HALF_UP` and inconsistent with `HALF_EVEN` but do not
  isolate the mechanism. `[VERIFIED as an observation; UNVERIFIED as a controlled experiment]`
- **That 552 distinct literals is the complete set** — it is the set present in the committed Path B
  captures at their current magnitudes. "0 of them change value today" must never be read as "floats are
  safe here".
- **That `analysis/t46_arms_ratio.py` is a complete model.** It reproduces T39's own R1 and R3
  separations independently, which is the check that matters, but it models the **ratio** only and
  predicts no money. `[VERIFIED against T39's separations; UNVERIFIED as a money model]`
- **The delegated `mathcontext` leg's findings** are reported on its evidence in its own handoff; T46's
  parent re-verified **M-4** (the `LoanApplicationTerms` drop and the `B-02` counter-observation) and
  nothing else from that leg. `[VERIFIED on the leg's evidence; UNVERIFIED by this task]`
- **Note so it is not mistaken for a violation:** the strings `ojdbc`, `oracle.jdbc`, `:1521`,
  `com.mysql.cj`, `mariadb`, `go-sql-driver` appear in this work only inside `grep` patterns asserting
  those engines are **ABSENT**, and every such assertion observed **0** hits. "Oracle" throughout means
  the **Fineract reference implementation**; the only database engine touched is **PostgreSQL 18.3**.
- **This pass's own coverage.** T44 found what T39/T40/T42 could not distinguish; T46 found that T44's
  own proposed remedy could not reach its target, and raised two new findings of its own. Assume the
  next round finds something; a clean verdict would be the surprise.
