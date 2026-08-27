# T18 — Independent audit of the 2026-08-18 pass-1 golden-vector capture

Reviewer: independent (T18). Run `2026-08-17-run1-harness-schedule-poc`.
Artefacts audited: `.softhouse/capture/src/Capture.java`, `.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java`,
`.softhouse/capture/out/capture-raw.json` (9 results), `.softhouse/capture/out/capture-stderr.txt`.
Oracle of record: `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (read-only), image `fineract:latest`.

> **Scope note.** A *pass 2* capture (`Capture2.java`, `out/capture-tenant-*.{json,txt}`, `PASS2-REPORT.md`,
> `README-pass2.md`) appeared in the main checkout at 15:30–15:35 on 2026-08-18, **after** this worktree was
> created, and is **not** part of this audit. Where I mention it, it is flagged as unreviewed context only;
> no finding below depends on it.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

The nine observed schedules are **sound and trustworthy as numbers**. I verified provenance cryptographically
(the pinned image's own `git.properties` carries `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`,
`git.dirty=false`), verified the copied seam class is byte-identical to the pinned original, read every line of
`Capture.java` and found **no synthesised, predicted, asserted or hard-coded expected value anywhere**, and —
most importantly — **independently re-derived C-00 and the entire D-01 family from the pinned source in a model
I wrote myself, reproducing all four schedules digit-for-digit at precisions 8, 12 and 19**, including the
`setScale(precision)` rate-factor quantization and the iterative EMI-adjustment loop that only fires at
precision 8. C-00 reproduces the shipped test literals and the README transcript exactly, so no capture is void.
D-02, D-02b, D-03 and D-04 each match the pinned source's written rule exactly.

It is **not** ACCEPTED outright because the capture set is, by the capture plan's **own admissibility rules**,
not yet a vector set: (1) the plan's environment-attestation block (§4.1: *"A vector captured without this block
attached is not admissible"*) is **absent from the artefact entirely** — the provenance claim exists only as a
Java comment written by the same agent; (2) three per-period columns the plan mandates (`fromDate`, `fee`,
`penalty`, §4.2) are **never emitted by the harness**, so a Go port could get `fromDate` wrong and no vector
would catch it; (3) no build/run recipe was committed with pass 1, so the run is not reproducible from the repo;
(4) D-04's stack trace was discarded, leaving the failing frame to be inferred rather than observed; and (5) the
D-01 label *"discriminates MathContext precision-vs-scale"* over-claims — a precision **sweep** cannot, by
construction, separate the two senses, and reading it that way would be a serious error (§4 below).

None of these void a number. All are fixable without re-running the JVM except (1), (3) and (4).

---

## 1. Provenance — is this really the pinned oracle?

**Verdict: VERIFIED, and more strongly than the header claims.**

| Claim in `Capture.java:4-5` | Independent check | Result |
|---|---|---|
| Fineract commit `426a23544e…` | `git log -1` in the pinned checkout | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean [VERIFIED: `git -C /Users/buv/fineract log -1 --format='%H %cI %s'` → `426a23544e8426a38ae43ae404670a0a7e85b9eb 2026-08-12T14:59:16+02:00 Merge pull request #5946`; `git -C /Users/buv/fineract status --short` → empty] |
| Image `sha256:e596339626bf…` exists | `docker image inspect` | exists, `RepoTags=[fineract:latest]`, created `2026-08-17T11:29:56Z`, `linux/arm64` [VERIFIED: `docker image inspect e596339626bf… --format '{{.Id}} \| repotags={{.RepoTags}} \| created={{.Created}} \| os={{.Os}}/{{.Architecture}}'` → `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a \| repotags=[fineract:latest] \| created=2026-08-17T11:29:56.52027346Z \| os=linux/arm64`] |
| **Image really contains that commit** (not claimed by the header — I checked) | read `BOOT-INF/classes/git.properties` out of `/app/fineract-provider.jar` inside the image | `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`, `git.build.version=1.16.0-SNAPSHOT`, `git.closest.tag.commit.count=273`, `git.commit.time=2026-08-12T12:59+0000` [VERIFIED: `docker run --rm -e JAVA_TOOL_OPTIONS= --entrypoint sh fineract:latest -c 'unzip -p /app/fineract-provider.jar BOOT-INF/classes/git.properties'`] |
| JVM Zulu 21.0.11 | `java -version` inside the image, `JAVA_TOOL_OPTIONS` emptied | `openjdk version "21.0.11" 2026-04-21 LTS`, `Zulu21.50+19-CA (build 21.0.11+10-LTS)` [VERIFIED: `docker run --rm -e JAVA_TOOL_OPTIONS= --entrypoint sh fineract:latest -c 'java -version'`] |
| stderr fingerprint | `capture-stderr.txt` contains exactly `Picked up JAVA_TOOL_OPTIONS: ` | identical to the first line my own container run emitted — weak but real corroboration that pass 1 ran inside this image with `JAVA_TOOL_OPTIONS` emptied [VERIFIED: `cat .softhouse/capture/out/capture-stderr.txt` → `Picked up JAVA_TOOL_OPTIONS:`] |

**The copied seam class is byte-identical to the pinned original.** SHA-256 of both files is
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`; `diff -u` exits 0.
[VERIFIED: `shasum -a 256 /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java /Users/buv/gerege-nbfi/.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java` → same digest twice; `diff -u <orig> <copy>; echo exit=$?` → `exit=0`]

That check is load-bearing, because **the seam class is not in the image**: the image's `BOOT-INF/lib` carries
`fineract-progressive-loan`, `fineract-loan`, `fineract-core` and friends, but **no**
`fineract-progressive-loan-embeddable-schedule-generator` jar
[VERIFIED: `docker run --rm -e JAVA_TOOL_OPTIONS= --entrypoint sh fineract:latest -c 'unzip -l /app/fineract-provider.jar | grep -E "BOOT-INF/lib/fineract"'` → 20 module jars listed, none embeddable].
The seam had to be compiled from source against the image's classpath, so byte-identity is the only thing
standing between "ran the oracle" and "ran a lookalike". It passes.

**Every class the harness imports exists at the claimed coordinates in the pinned checkout** —
`EmbeddableProgressiveLoanScheduleGenerator`, `LoanRepaymentScheduleModelData`, `LoanSchedulePlan*`,
`CurrencyData`, `DaysInMonthType` / `DaysInYearType` / `DaysInYearCustomStrategyType`, `InterestMethod`
[VERIFIED: `find /Users/buv/fineract -name '<X>.java' -not -path '*/.git/*'` for each]. The 6-argument
`CurrencyData` constructor is `(code, name, decimalPlaces, inMultiplesOf, displaySymbol, nameCode)`
[VERIFIED: `CurrencyData.java:59-60`], so the harness's `new CurrencyData(code, code, digits, null, code, code)`
puts `2` in `decimalPlaces` and `null` in `inMultiplesOf` — the two fields `Money` actually reads.

**Residual provenance gaps (required changes, none rejection-grade):**

- The artefact itself carries **no attestation**: no JVM string, no jar SHA-256, no image digest, no commit, no
  timestamp, no runtime `MoneyHelper.PRECISION`, no tenant rounding mode, no capture-path label. The plan
  requires all of these and declares a vector without them inadmissible
  [VERIFIED: `docs/analysis/tier0-vector-capture-plan.md` §4.1 → *"A vector captured without this block attached is not admissible."*].
  The plan's **Run C-01 (environment attestation) was never executed**
  [VERIFIED: `jq -r '.captures[].id' capture-raw.json` → `C-00, D-01, D-01-p19, D-01-p8, D-01-mnt, D-02, D-02b, D-03, D-04` — no C-01].
- **No build or run recipe was committed with pass 1**: `.softhouse/capture/` held only `src/` and `out/` when
  this audit began — no script, Dockerfile or command log
  [VERIFIED: `find /Users/buv/gerege-nbfi/.softhouse/capture -type f` → 4 files]. The run is not reproducible
  from the repository.

---

## 2. Synthesis check — the cardinal rule

**Verdict: CLEAN. No expected value is computed, asserted, hard-coded or massaged anywhere.**

I read all 205 lines.

- The only literals in the file are **inputs** — `Case` constructor arguments: dates, principals, rates,
  precisions, currency codes, flags [VERIFIED: `Capture.java:40-102`].
- `run()` does exactly three things: build a `MathContext` and a `LoanRepaymentScheduleModelData`, echo those
  inputs, and stringify whatever `generator.generate(mc, config)` returned. Every emitted number is a bare
  `plan.getX()` / `period.getX()` appended verbatim [VERIFIED: `Capture.java:117-128`, `:161`, `:171-197`].
- There is **no** assertion, no comparison against a reference, no rounding, no scaling, no arithmetic on any
  returned value. The only arithmetic-looking expression is `BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0`
  at `:125` and `:149`, which derives the `isDownPaymentEnabled` **input** flag exactly as the shipped test does
  [VERIFIED: `EmbeddableProgressiveLoanScheduleGeneratorTest.java:56` → identical expression]. It is applied
  identically to the model and to the echoed JSON, so the two cannot drift.
- The `purpose` strings reference T5's hypotheses. They are commentary and do not touch the numbers. One of them
  nevertheless **over-claims** — see §4.2.
- Nothing is filtered or reordered: the loop at `:178` walks `plan.getPeriods()` in list order and emits one row
  per period, with an explicit `UNKNOWN:<class>` fallback (`:196`) rather than silently dropping an unrecognised
  type. Good discipline.

**Four defects in the *recording* — none of them synthesis, all of them real:**

1. **Columns are dropped.** A `REPAYMENT` row emits `periodNumber, dueDate, outstandingLoanBalance, principal,
   interest, totalDue, totalOutstandingBalance` and **omits `periodFromDate`, `feeAmount`, `penaltyAmount`**
   [VERIFIED: `Capture.java:188-194`, versus the fields available at `LoanSchedulePlan.java:69-78`]. The plan
   mandates all ten [VERIFIED: plan §4.2 → *"Record every period: `periodNumber`, `fromDate`, `dueDate`,
   `principal`, `interest`, `fee`, `penalty`, `totalDue`, `outstandingBalance`, `totalOutstandingBalance`"*].
   The disbursement row also omits `getOutstandingLoanBalance()`, but that one is **not** an information loss:
   `LoanSchedulePlan.from` builds the disbursement period with the disbursed principal passed twice, so the two
   columns are identical by construction [VERIFIED: `LoanSchedulePlan.java:53-56`]. `fromDate`, `fee` and
   `penalty` **are** genuine losses.
2. **`BigDecimal.toString()`, not `toPlainString()`.** Values go through `StringBuilder.append(BigDecimal)`,
   which can emit scientific notation for a sufficiently negative scale [`Capture.java:172-174`, `:181`,
   `:185-194`]. Scale-2 money never triggers it, so no captured value is affected, but the plan explicitly
   required `toPlainString()` [VERIFIED: plan §4.0 → *"as `BigDecimal.toPlainString()` at the source scale —
   **never** via `double`"*]. A latent corruption channel, not a present defect. The `double` half of that rule
   **is** honoured: no `double` appears anywhere in `Capture.java`.
3. **The error branch discards the stack trace** — only `e.getClass().getName()` and `e.getMessage()` are kept
   [`Capture.java:162-167`]. This is why D-04's failing frame had to be inferred from source (§7) rather than read.
4. **Hand-rolled JSON with escaping only on the error message** (`"`→`'`, newline→space, `:165`). Inputs and
   `purpose` are unescaped. `jq` parses the current file, so nothing is broken today; it is fragile for later cases.

---

## 3. C-00 calibration — does it actually pass?

**Verdict: PASSES, digit-for-digit, on every column it emits. No capture in the file is void on calibration grounds.**

Source of truth located independently at
`fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92`
and `fineract-progressive-loan-embeddable-schedule-generator/README.md:48-63`.

| Field | Test literal | README literal | C-00 observed | Match |
|---|---|---|---|---|
| `loanTermInDays` | `182` (`:74`) | `182` (README:51) | `182` | ✅ |
| `totalDisbursedAmount` | `100.00` (`:75`) | `100.00` (README:52) | `100.00` | ✅ |
| `totalInterestAmount` | `2.05` (`:76`) | `2.05` (README:53) | `2.05` | ✅ |
| `totalRepaymentAmount` | `102.05` (`:77`) | `102.05` (README:54) | `102.05` | ✅ |
| period count | `7` (`:79`) | 6 repayments + 1 disbursement | 7 rows | ✅ |
| disbursement | `2024-01-01`, principal `100.0` (`:80`) | `2024-01-01, Amount: 100.00` | `2024-01-01`, `100.00` | ✅ |
| p1 | `16.43 / 0.58 / 17.01 / 83.57 / 85.04` (`:81-82`) | `83.57, 16.43, 0.58, 17.01` | `16.43 / 0.58 / 17.01 / 83.57 / 85.04` | ✅ |
| p2 | `16.52 / 0.49 / 17.01 / 67.05 / 68.03` (`:83-84`) | `67.05, 16.52, 0.49, 17.01` | identical | ✅ |
| p3 | `16.62 / 0.39 / 17.01 / 50.43 / 51.02` (`:85-86`) | `50.43, 16.62, 0.39, 17.01` | identical | ✅ |
| p4 | `16.72 / 0.29 / 17.01 / 33.71 / 34.01` (`:87-88`) | `33.71, 16.72, 0.29, 17.01` | identical | ✅ |
| p5 | `16.81 / 0.20 / 17.01 / 16.90 / 17.00` (`:89-90`) | `16.90, 16.81, 0.20, 17.01` | identical | ✅ |
| p6 | `16.90 / 0.10 / 17.00 / 0.0 / 0.0` (`:91-92`) | `0.00, 16.90, 0.10, 17.00` | `16.90 / 0.10 / 17.00 / 0.00 / 0.00` | ✅ |

[VERIFIED: `jq -c '.captures[]|select(.id=="C-00")|.observed' capture-raw.json`, compared cell by cell against
`EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92` and `README.md:48-63`]

**Exactly which columns the source literals corroborate, and how strongly:**

- **Corroborated at full string scale** (the README prints `BigDecimal` via `%s`): `dueDate`,
  `outstandingLoanBalance`, `principal`, `interest`, `totalDue`, and the four plan-level fields. This is the
  *only* evidence that scale 2 is preserved rather than merely the numeric value.
- **Corroborated as a `double` only** — the test funnels every literal through `toDouble()`
  [VERIFIED: `EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122`]: `periodNumber`,
  `totalOutstandingBalance` (`85.04 / 68.03 / 51.02 / 34.01 / 17.00 / 0.0`), and the disbursement principal. A
  `double` assertion cannot distinguish `0.2` from `0.20` — the plan's "toDouble trap" (§5.4), and it bites
  here: **`totalOutstandingBalance` has no scale corroboration from any shipped source**, because the README
  does not print that column at all.
- **Not covered at all, because the harness does not emit them**: `periodFromDate` (asserted for all 7 periods
  at `:103-105`), `feeAmount` (`0.0` × 6), `penaltyAmount` (`0.0` × 6).

**Two incidental findings from this comparison:**

- **C-00's inputs are not byte-identical to the shipped test's.** The harness passes
  `new CurrencyData("usd","usd",2,null,"usd","usd")`; the test passes
  `new CurrencyData("usd","US Dollar",2,null,"usd","$")`
  [VERIFIED: `Capture.java:120-121` vs `EmbeddableProgressiveLoanScheduleGeneratorTest.java:47`]. Only `code`,
  `decimalPlaces` and `inMultiplesOf` are read on this path — `Money`'s constructor uses `getInMultiplesOf()`
  and `getDecimalPlaces()` [VERIFIED: `Money.java:40-52`], and currency equality compares `code` — and all
  three agree, so the deviation is **non-load-bearing**. But the plan said "the complete table in §2.1,
  **verbatim**", and it is not verbatim; record the deviation instead of leaving a later reader to find it.
- **The module README's transcript is stale relative to its own `misc/Main.java`.** `Main.java:86` appends
  `", Total Outstanding Balance: %s"` to every repayment line; no README line carries that column
  [VERIFIED: `misc/Main.java:86` vs `README.md:57-62`]. The README output cannot have been produced by the
  current `Main.java`. It remains valid corroboration for the columns it does show, but plan §4.0 acceptance
  check 4 ("a second, independent attestation of the same figures") is only **partially** satisfiable.

---

## 4. Does D-01 genuinely discriminate?

**Verdict: the *observation* is correct and I reproduced it exactly. The *label* is wrong, and the distinction
matters enough that reading it the labelled way would be a serious error.**

### 4.1 My independent re-derivation

I did not adopt T5's numbers. I read the arithmetic out of the pinned source and implemented it myself in a
`Decimal` model with `ROUND_HALF_UP`, modelling `BigDecimal.multiply/divide(…, mc)` as significant-digit
rounding, `setScale(n, HALF_UP)` as decimal-place quantization, `1 + rateFactor` as an **exact** addition, and
`Money` construction as `setScale(2, HALF_UP)`:

- rate factor —
  `interestRate.multiply(interestFractionPerPeriod, mc).multiply(actualDaysInPeriod, mc).divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode())`
  [VERIFIED: `ProgressiveEMICalculator.java:1950-1963`, reached via `:1536` `case DAYS_30` → `:1598-1610`
  `case MONTHS` → `rateFactorByRepaymentEveryMonth` `:1921-1927`; the rate is pre-divided by 100 at `:1319`]
- `rateFactorPlus1 = 1 + rateFactor`, **no MathContext** [VERIFIED: `RepaymentPeriod.java:216-218`]
- `rateFactorPlus1N = Π (1+rf_i)` with `mc`, then `stripTrailingZeros`
  [VERIFIED: `ProgressiveEMICalculator.java:1815-1819` and `:1723-1724`]
- `fnResult = fold_{i≥2} (1 + fn_{i-1}·(1+rf_i))` with `mc`
  [VERIFIED: `ProgressiveEMICalculator.java:1822-1828`, `:1991-1993`]
- `EMI = rateFactorPlus1N · outstandingBalance ÷ fnResult`, then `Money.of(…, mc)`
  [VERIFIED: `ProgressiveEMICalculator.java:1838-1841`, `:1730-1733`]
- per-period interest `= balance · rateFactorTillPeriodDueDate ÷ lengthTillDue · length`, then `Money`
  [VERIFIED: `InterestPeriod.java:145-158`, `RepaymentPeriod.java:255-257`];
  `dueInterest = min(calculatedDueInterest, EMI)` [`RepaymentPeriod.java:272-286`];
  `duePrincipal = EMI − dueInterest` [`RepaymentPeriod.java:345-350`]
- the last period absorbs the residual [`ProgressiveEMICalculator.java:1160-1195`], and if the last-vs-penultimate
  EMI gap is large enough — `|Δ| × 100 > floor(n/2)` — the whole EMI is nudged by `Δ/n` and the schedule
  recomputed, iteratively, until the gap stops shrinking
  [VERIFIED: `EmiAdjustment.java:31-44`, driven from `ProgressiveEMICalculator.java:1258-1300`]

**Result — my model reproduces the oracle exactly at all three precisions**, including the adjustment loop,
which fires **only** at precision 8:

| | EMI | p1 principal / interest | p5 principal / interest / balance | p18 principal / interest / total |
|---|---|---|---|---|
| **p12 — my model** | `5,613,766.78` | `4,262,429.33 / 1,351,337.45` | `4,531,420.25 / 1,082,346.53 / 65,674,840.83` | `5,528,535.21 / 85,231.58 / 5,613,766.79` |
| **p12 — D-01 observed** | `5,613,766.78` | `4,262,429.33 / 1,351,337.45` | `4,531,420.25 / 1,082,346.53 / 65,674,840.83` | `5,528,535.21 / 85,231.58 / 5,613,766.79` |
| **p19 — my model** | `5,613,766.78` | `4,262,429.33 / 1,351,337.45` | `4,531,420.26 / 1,082,346.52 / 65,674,840.82` | `5,528,535.20 / 85,231.58 / 5,613,766.78` |
| **p19 — D-01-p19 observed** | `5,613,766.78` | `4,262,429.33 / 1,351,337.45` | `4,531,420.26 / 1,082,346.52 / 65,674,840.82` | `5,528,535.20 / 85,231.58 / 5,613,766.78` |
| **p8 — my model** | `5,613,766.95` | `4,262,429.25 / 1,351,337.70` | `4,531,420.15 / 1,082,346.80 / 65,674,841.25` | `5,528,535.24 / 85,231.60 / 5,613,766.84` |
| **p8 — D-01-p8 observed** | `5,613,766.95` | `4,262,429.25 / 1,351,337.70` | `4,531,420.15 / 1,082,346.80 / 65,674,841.25` | `5,528,535.24 / 85,231.60 / 5,613,766.84` |

[VERIFIED: independent model at `/tmp/rederive.py`, compared against
`jq -r '.captures[]|select(.id|startswith("D-01"))| …' capture-raw.json`; every listed cell equal]

The precision-8 agreement is the single strongest piece of evidence in this audit: a model that stops at the
naive amortization gets `5,613,765.80` there. Only reproducing Fineract's `EmiAdjustment` convergence loop lands
on `5,613,766.95` with p1 `4,262,429.25` and p18 total `5,613,766.84`. That is not reachable by accident.
**The D-01 family is behaviourally consistent with the pinned source at the minor-unit level.**
`loanTermInDays = 547` is also correct (2024-01-01 → 2025-07-01 = 366 + 181).

### 4.2 What this settles about T5 §1 — and what it does not

**What it settles.** At precision 12 I computed the schedule **both ways at the same precision** — with the
trailing `setScale` (sense 2 present, what the source does) and without it (sense 1 only, what DEC-1's text
describes):

| p12, principal 87,654,321, 18 × 18.5 % | period 5 principal / interest / balance | period 18 principal / total |
|---|---|---|
| with `setScale` — the source | `4,531,420.25 / 1,082,346.53 / 65,674,840.83` | `5,528,535.21 / 5,613,766.79` |
| significant digits only — DEC-1's text | `4,531,420.`**`26`**` / 1,082,346.`**`52`**` / 65,674,840.`**`82`** | `5,528,535.`**`20`**` / 5,613,766.`**`78`** |
| **oracle, observed (D-01)** | `4,531,420.25 / 1,082,346.53 / 65,674,840.83` | `5,528,535.21 / 5,613,766.79` |

[VERIFIED: `/tmp/rederive.py` with `apply_setscale=True` and `False` at precision 12, vs the D-01 `jq` extract]

So **the oracle implements the two-sense reading**, and a Go port implementing only sense 1 diverges by one
minor unit from period 5 onward and ends on a different final principal. T5 §1.3's specific prediction is now
confirmed *empirically*, not merely re-derived. This is the discriminating evidence G-1 step 1 asked for.

**What it does NOT settle, and where conflation would be a serious error.** The three precision runs
(`p8 / p12 / p19`) **cannot** separate the two senses, because `mathContextPrecision` drives *both*
simultaneously: raising 12→19 raises the significant-digit count **and** the `setScale` decimal-place count. A
precision sweep turns one knob that moves two things. There is a trap sitting in this very data:

> the **sense-1-only** schedule at precision **12** is **identical** to the **oracle's** schedule at precision
> **19** — `4,531,420.26 / 1,082,346.52`, final principal `5,528,535.20`.

Anyone comparing D-01 against D-01-p19 and nothing else could "explain" the delta as the sense difference, and
would be wrong: the p12↔p19 delta and the sense-1↔sense-2 delta merely coincide in magnitude and direction on
this one vector. That coincidence is not a law and must not be relied on.

The discrimination is only available because a **counterfactual** — sense 1 only, at fixed precision 12 — was
computed **outside** the oracle. The oracle can never emit it. Consequently:

- the capture file contains **no marker** of which reading produced it; the discriminating comparison lives
  entirely in a re-derivation that is not in the artefact;
- the D-01 `purpose` string, *"discriminates MathContext precision-vs-scale (T5 s1)"* [`Capture.java:58`], is an
  over-claim as written. What D-01 actually is: **the input configuration at which the two readings diverge,
  with the oracle's answer recorded at three precisions.** Relabel it, and store the sense-1 counterfactual
  beside it, explicitly tagged as computed and not observed.

**D-01-mnt** is byte-identical to D-01 in every observed field
[VERIFIED: `jq` extraction of both `observed` blocks → all 19 rows and all four plan-level fields equal].
The currency **code** does not participate in the arithmetic at `decimalPlaces = 2`. That is a real but narrow
result: it says nothing about `decimalPlaces = 0`, nothing about `inMultiplesOf`, and nothing about MNT display
conventions.

---

## 5. D-02 / D-02b — month-end

**Verdict: the observation matches `adjustDate` exactly, and it settles re-anchor-vs-clamp in favour of
RE-ANCHOR. One adjacent question the captures cannot answer is settled from source instead.**

The rule, in full [VERIFIED: `DefaultScheduledDateGenerator.java:168-176`]:

```java
private Temporal adjustDate(final Temporal date, final Temporal seedDate, final PeriodFrequencyType frequencyType) {
    if (frequencyType.isMonthly() && seedDate.get(DAY_OF_MONTH) > 28 && date.get(DAY_OF_MONTH) >= 28) {
        int noOfDaysInCurrentMonth = YearMonth.from(date).lengthOfMonth();
        int seedDay = seedDate.get(DAY_OF_MONTH);
        return date.with(DAY_OF_MONTH, Math.min(noOfDaysInCurrentMonth, seedDay));
    }
    return date;
}
```

applied after each `plusMonths(1)` step [VERIFIED: `DefaultScheduledDateGenerator.java:128-131`, driven from
the period loop at `:58-72`].

**D-02, seed 2024-01-31 (`seedDay = 31 > 28`)** — my hand-trace vs observed:

| step | `plusMonths(1)` | day ≥ 28 | `min(lengthOfMonth, 31)` | traced | observed |
|---|---|---|---|---|---|
| 1 | 2024-02-29 | ✓ | min(29,31) = 29 | 2024-02-29 | 2024-02-29 ✅ |
| 2 | 2024-03-29 | ✓ | min(31,31) = 31 | 2024-03-31 | 2024-03-31 ✅ |
| 3 | 2024-04-30 | ✓ | min(30,31) = 30 | 2024-04-30 | 2024-04-30 ✅ |
| 4 | 2024-05-30 | ✓ | min(31,31) = 31 | 2024-05-31 | 2024-05-31 ✅ |
| 5 | 2024-06-30 | ✓ | min(30,31) = 30 | 2024-06-30 | 2024-06-30 ✅ |
| 6 | 2024-07-30 | ✓ | min(31,31) = 31 | 2024-07-31 | 2024-07-31 ✅ |

**D-02b, seed 2024-01-30 (`seedDay = 30 > 28`)** — the sharp discriminator:

| step | `plusMonths(1)` | `min(lengthOfMonth, 30)` | traced | observed |
|---|---|---|---|---|
| 1 | 2024-02-29 | min(29,30) = 29 | 2024-02-29 | 2024-02-29 ✅ |
| 2 | 2024-03-29 | min(31,30) = **30** | 2024-03-30 | 2024-03-30 ✅ |
| 3–6 | … | 30 each | 04-30, 05-30, 06-30, 07-30 | identical ✅ |

[VERIFIED: `jq -c '.captures[]|select(.id=="D-02" or .id=="D-02b")|.observed' capture-raw.json` against the trace]

**D-02b decides it.** Under *clamp-and-carry* (each step from the previous clamped day) period 2 would be
**2024-03-29**; under *re-anchor to seed* it is **2024-03-30**. The oracle emitted **2024-03-30**. The rule is
**re-anchor to the seed day, floored by the target month's length, re-applied on every monthly step whenever
`seedDay > 28` and the stepped date lands on day ≥ 28** — never a carry. D-02 alone would not have settled it
(31 and clamp-carry agree on several steps); the matched pair does. The plan's C-02/C-03 pairing instinct was
correct and should be preserved.

Both schedules are otherwise numerically identical to C-00 (`182` days, interest `2.05`, the same six splits),
because under `DAYS_30`/`DAYS_360` the `actualDays/calculatedDays` ratio cancels and the rate factor is
independent of the actual day counts. That is a useful control result and should be stated in the vector record
rather than left implicit.

**What the captures cannot settle, settled from source instead:** *which input becomes the seed.* D-02 and
D-02b set `scheduleGenerationStartDate == disbursementDate`, so they cannot discriminate. Source does:
`seedDate = modelData.disbursementDate()` when non-null, falling back to `scheduleGenerationStartDate`
[VERIFIED: `LoanApplicationTerms.java:583-589`, inside `assembleFrom` at `:579`]. A Go port must key the
month-end rule off the **disbursement date**, and no captured vector currently proves that. One variant
(start 2024-01-01, disburse 2024-01-31) would pin it.

**Deviation from the plan:** C-02/C-03 specified principal `MNT 1,000,000` (`100000000` minor units) at rate
`9.99`, with acceptance check "principals sum to `100000000`". D-02/D-02b used principal `100` USD at `7.0`
[VERIFIED: plan §4.2 rows C-02/C-03 vs `Capture.java:78-88`]. The **date** gap is closed; the **MNT-scale** half
of those runs is not.

---

## 6. D-03 — ordering boundary (observation only; the horn is the ratifier's)

**Verdict: a faithful observation of the oracle's emitted order. Mechanism confirmed line by line.**

Inputs: `scheduleGenerationStartDate = 2024-01-01`, `disbursementDate = 2024-02-01`, principal `100`,
6 monthly, 7.0 %, precision 12, `allowFullTermForTranche = false` [VERIFIED: `jq` on D-03 `inputs`].

**Emitted list, in the order the oracle produced it** [VERIFIED: `jq -c '.captures[]|select(.id=="D-03")|.observed' capture-raw.json`]:

| index in list | type | periodNumber | dueDate | balance | principal | interest | total | totalOutstandingBalance |
|---|---|---|---|---|---|---|---|---|
| 0 | **REPAYMENT** | **1** | **2024-02-01** | `0.00` | `0.00` | `0.00` | `0.00` | `101.76` |
| 1 | **DISBURSEMENT** | — | **2024-02-01** | — | `100.00` | — | — | — |
| 2 | REPAYMENT | 2 | 2024-03-01 | `80.23` | `19.77` | `0.58` | `20.35` | `81.41` |
| 3 | REPAYMENT | 3 | 2024-04-01 | `60.35` | `19.88` | `0.47` | `20.35` | `61.06` |
| 4 | REPAYMENT | 4 | 2024-05-01 | `40.35` | `20.00` | `0.35` | `20.35` | `40.71` |
| 5 | REPAYMENT | 5 | 2024-06-01 | `20.24` | `20.11` | `0.24` | `20.35` | `20.36` |
| 6 | REPAYMENT | 6 | 2024-07-01 | `0.00` | `20.24` | `0.12` | `20.36` | `0.00` |

Plan level: `loanTermInDays = 182`, `totalDisbursedAmount = 100.00`, `totalInterestAmount = 1.76`,
`totalRepaymentAmount = 101.76`. Six repayment periods, **five** of them paying.

**Why the oracle does this — verified against the half-open window T5 cites:**

1. `periods` is built by a single pass over the six pre-generated repayment periods, and inside each iteration
   `processDisbursements(...)` runs **before** `periods.add(repaymentPeriod)`
   [VERIFIED: `ProgressiveLoanScheduleGenerator.java:116-145` — disbursements at `:121-122`, repayment appended
   at `:141`].
2. The window test is `!disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)` —
   **half-open `[from, due)`** [VERIFIED: `ProgressiveLoanScheduleGenerator.java:307-308`]. For iteration 1
   (`from = 2024-01-01`, `due = 2024-02-01`), `2024-02-01.isBefore(2024-02-01)` is **false**, so the loop
   `continue`s at `:310`. Repayment period 1 is appended with no disbursement having occurred, hence all-zero
   amounts.
3. For iteration 2 (`from = 2024-02-01`, `due = 2024-03-01`) the disbursement **is** in window, so the
   disbursement period is appended at `:318` — *before* repayment period 2 is appended at `:141`. Hence
   `[RP1(zero), DISB, RP2, …]`.
4. Installment numbering comes from a counter incremented once per repayment period regardless of content
   [VERIFIED: `:123` `repaymentPeriod.setPeriodNumber(scheduleParams.getInstalmentNumber())`, `:143`
   `incrementInstalmentNumber()`], so the zero period consumes number **1** and the five paying installments are
   numbered **2..6**.
5. `LoanSchedulePlan.from` preserves list order — it iterates `model.getPeriods()` and appends, with no sort
   [VERIFIED: `LoanSchedulePlan.java:45-83`].
6. `totalOutstandingBalance` is a **running remainder** initialised to `totalRepaymentExpected` and decremented
   by each repayment's `totalDue` as the list is walked [VERIFIED: `LoanSchedulePlan.java:48-49`, `:68`]. That
   is why the zero period reports `101.76` — the entire loan total — on a date at which, in list order, nothing
   has yet been disbursed. **This column is order-dependent by construction**, which is exactly why the ordering
   question is load-bearing for the port rather than cosmetic.
7. `loanTermInDays = 182` is measured 2024-01-01 → 2024-07-01, i.e. from the **schedule generation start**, not
   from the disbursement (which would be 151 days).

Arithmetic self-consistency holds: principals `19.77 + 19.88 + 20.00 + 20.11 + 20.24 = 100.00`; interest
`0.58 + 0.47 + 0.35 + 0.24 + 0.12 = 1.76`; `101.76 = 100.00 + 1.76`.

**No recommendation is offered on which horn to take.** This is G-1 open decision 2 and belongs to the human
ratifier. What is now on the record is the precise thing that must be either reproduced or rejected: a
zero-valued repayment period numbered 1, dated on the disbursement date, emitted *before* the disbursement
period of the same date, consuming an installment number, and carrying a `totalOutstandingBalance` equal to the
whole loan.

---

## 7. D-04 — the error

Observed: `"observed": null`, `"error": "java.lang.IllegalStateException: No tenant context available.
MoneyHelper requires a valid tenant context to ensure proper multi-tenant isolation."`
[VERIFIED: `jq` on D-04; the message is reproduced exactly by the string concatenation at
`MoneyHelper.java:178-179`].

### Why the flag changes the code path

`allowFullTermForTranche` is read in exactly one place on this call tree:

```java
if (scheduleModel.loanProductRelatedDetail().isAllowFullTermForTranche() && numberOfRepayments > 0
        && operation.getAction().equals(EmiChangeOperation.Action.DISBURSEMENT)) {
    addFullTermTrancheDisbursement(scheduleModel, operation);            // ← true
} else {
    scheduleModel.changeOutstandingBalanceAndUpdateInterestPeriods(...)  // ← false: the ordinary path
```
[VERIFIED: `ProgressiveEMICalculator.java:142-152`]

The guard **never consults `isMultiDisburseLoan()`**, so a single-disbursement loan takes the tranche branch as
soon as the flag is set. `addFullTermTrancheDisbursement` [`:155-174`] calls `buildLoanApplicationTerms`
[`:176`], whose fluent chain contains, at **`ProgressiveEMICalculator.java:182`**:

```java
.seedDate(firstDisbursedPeriodStartDate).inArrearsTolerance(Money.zero(loanProductRelatedDetail.getCurrencyData()))
```

That is the **one-argument** `Money.zero(CurrencyData)` overload, which resolves its `MathContext` from
`MoneyHelper.getMathContext()` [VERIFIED: `Money.java:130-131`] → `getTenantIdentifier()` →
`ThreadLocalContextUtil.getTenant()` returns `null` in a bare JVM → throw
[VERIFIED: `MoneyHelper.java:91-94`, `:173-180`]. **This is precisely the fourth `MoneyHelper` fallback T3b
flagged at `ProgressiveEMICalculator.java:182` — confirmed at that exact line.** Every other `Money` call on the
`false` path is `mc`-qualified, which is why the eight successful runs never reach `MoneyHelper` at all.

*(This frame was inferred from source because the harness discarded the stack trace — see §2 defect 3. The
inference is tight: it is the only unqualified `Money` factory call on the branch, and the thrown message
matches `MoneyHelper.java:178-179` verbatim. It should nevertheless have been observed, not inferred.)*

### (a) Does the error itself prove `allowFullTermForTranche` is not a dead field?

**Yes — and this is the strongest available form of that evidence.** A dead field cannot change observable
behaviour. Here, holding all eighteen other inputs identical to C-00 and flipping this one boolean turns a
successful schedule into an exception thrown from a branch that is unreachable when the flag is `false`
[VERIFIED: C-00 inputs at `Capture.java:53-54` vs D-04 inputs at `:99-102` differ only in
`allowFullTermForTranche`; outputs: a full 7-period schedule vs `IllegalStateException`]. The flag demonstrably
selects control flow. T3b's and T5's refutation of the "dead field" claim is now corroborated by the oracle
itself.

**Care with the converse:** this proves the flag is *live*, not that it changes the *numbers*. Whether a
successful tranche-branch run yields a different schedule than the `false` run is a separate question that D-04
does **not** answer, because it produced no schedule.

### (b) What would a capture need to exercise this path?

**A tenant context supplied by the harness, in-process. A running server is NOT required.** Both pieces are
public static API on classes already proven to be on the capture classpath — the exception itself came from
`MoneyHelper` on that classpath:

- `ThreadLocalContextUtil.setTenant(FineractPlatformTenant)` — `public static`
  [VERIFIED: `ThreadLocalContextUtil.java:33`, `:48`]
- `MoneyHelper.initializeTenantRoundingMode(String tenantIdentifier, int roundingModeValue)` — `public static`,
  populating the per-tenant cache that `getRoundingMode()` / `getMathContext()` read
  [VERIFIED: `MoneyHelper.java:54-65`, `:74-94`]

The *embeddable entry point* cannot supply it — `EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)`
takes no tenant and sets none [VERIFIED: `EmbeddableProgressiveLoanScheduleGenerator.java:45-47`] — but the
harness that calls it can, immediately before the call. So the missing piece is a **harness change**, not a
server.

**This has a consequence any such vector must carry.** Once a tenant is set, the tranche branch's `MathContext`
is **not** the caller's `mc`: `MoneyHelper.getMathContext()` returns
`new MathContext(PRECISION /* = 19 */, <tenant's configured rounding mode>)`
[VERIFIED: `MoneyHelper.java:35`, `:91-94`]. A tranche-path capture is therefore governed by **two**
MathContexts — the explicit one and an ambient tenant-derived one whose rounding mode is a *deployment
configuration value*, not a source constant. Any such vector must stamp the tenant identifier and the rounding
mode in force, or it is uninterpretable. Note this also means **G-1 open decision 6** ("the live tenant's actual
rounding mode") is **not** answered by pass 1: Path A reached `MoneyHelper` exactly once, and only to fail.

*Unreviewed context, not relied upon:* the concurrent pass-2 artefact appears to have done exactly this
(`capture-tenant-log.txt` logs `Initialized rounding mode for tenant 'cap_t04t': HALF_EVEN`, and `T-04f`/`T-04t`
both return schedules). That is pass-2's evidence to defend under its own review, not mine.

---

## 8. Coverage honesty

### 8.1 Plan gaps — closed, partly closed, still open

| Plan gap (`docs/analysis/tier0-vector-capture-plan.md` §3) | Status after pass 1 | Evidence |
|---|---|---|
| §3.2 month-end + re-anchoring | **CLOSED for the date rule** (re-anchor proven by the D-02/D-02b pair). **NOT** closed at MNT scale; the *seed-selection* question is undischarged by any vector (settled from source only) | §5 |
| §3.7 long declining-balance terms | **PARTLY CLOSED** — the corpus capped declining balance at 6 periods; D-01 is 18. Plan runs C-05 (36) and C-06 (60) not executed | D-01 |
| §3.9 MNT-scale principals | **PARTLY CLOSED** — D-01 / D-01-mnt run principal `87,654,321` (8,765,432,100 minor units), far past the corpus's `100`. Plan runs C-04/C-05/C-06 not executed, and `D-01-mnt` differs from `D-01` only in the currency *code* | §4.2 |
| §3.1 uneven principal division | **PARTLY CLOSED** — D-01 exercises residual absorption in the final period at scale | D-01 p18 |
| §3.5 `installmentAmountInMultiplesOf` | **STILL TOTALLY OPEN — and unfillable on this path**, see 8.2 | all 9 cases pass `null` |
| §3.3 leap-year Feb 29 under `ACTUAL`/`ACTUAL` | **STILL OPEN** — all 9 runs are `DAYS_30`/`DAYS_360` with `daysInYearCustomStrategy = null` | all `inputs` blocks |
| §3.8 0 % rate | **STILL OPEN** — lowest rate captured is 7.0 | all `inputs` blocks |
| §3.6 single installment (`numberOfRepayments == 1`) | **STILL OPEN** — captured terms are 6 and 18 only | all `inputs` blocks |
| §3.4 multi-period rate variation | **STILL OPEN** (Path B / Tier A; not expressible via `LoanRepaymentScheduleModelData`) | — |
| plan §4.1 environment attestation (C-01) | **NOT PERFORMED** | 9 results, no C-01 |

Closed **beyond** the plan: the precision-vs-scale discriminator (§4), the disbursement-on-due-date ordering
boundary (§6), and the `allowFullTermForTranche` liveness proof (§7). Those are the three questions G-1 actually
turns on, so substituting the D-runs for the plan's C-runs was, on balance, good judgement. It needs to be
*recorded* as a deliberate deviation rather than left as an unexplained divergence from a reviewed plan.

### 8.2 A structural finding the captures imply but never state

`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` — the sole entry point from the
embeddable seam — **never reads `modelData.installmentAmountInMultiplesOf()`**, and `LoanApplicationTerms.Builder`
has **no setter for it at all**
[VERIFIED: `LoanApplicationTerms.java:579-606` contains no such call;
`grep -n "Builder installmentAmountInMultiplesOf\|private Integer installmentAmountInMultiplesOf" LoanApplicationTerms.java`
→ a single hit, the private field at `:217`]. The value is therefore **accepted by the record and silently
discarded** on this path, so `getInstallmentAmountInMultiplesOf()` is always `null` downstream
[`ProgressiveLoanScheduleGenerator.java:110`]. Gap §3.5 is not merely unfilled — it is **unfillable through the
embeddable seam**; only the server path can close it.

Likewise `disbursementDatas` is fixed to an empty list at `LoanApplicationTerms.java:600` and then back-filled
with one synthetic disbursement [VERIFIED: `ProgressiveLoanScheduleGenerator.java:113` calling
`prepareDisbursementsOnLoanApplicationTerms` at `:285-292`], so **multi-tranche behaviour is out of reach of
this harness entirely** — which is the deeper reason D-04's tranche flag lands somewhere strange.

### 8.3 Things the captures claim or imply but do not establish

1. **"Discriminates precision-vs-scale."** Not as labelled; the *pair* {observation + external counterfactual}
   does. See §4.2, including the p12/p19 coincidence trap.
2. **The header's provenance block.** Written by the capturing agent and unverifiable from the artefact alone.
   I verified it externally; the artefact still cannot stand on its own.
3. **`D-01-mnt` as "an MNT vector."** It establishes currency-code invariance at `decimalPlaces = 2`. Nothing
   about other decimal settings, `inMultiplesOf`, or display.
4. **Implied completeness of the `inputs` block.** All 19 components of `LoanRepaymentScheduleModelData` are
   echoed, but the `CurrencyData` sub-record is only partly echoed — `inMultiplesOf` is a **load-bearing** input
   read by the `Money` constructor [`Money.java:47-50`] and is never recorded, only implicitly `null`.
5. **`allowPartialPeriodInterestCalculation = true` in every run.** Never varied, so nothing is established
   about `false`. Note it does not even reach the rate-factor branch used here:
   `interestCalculationPeriodMethod` is never set by `assembleFrom`, so the `!= null` guard at
   `ProgressiveEMICalculator.java:1510` fails and control falls to `case DAYS_30` at `:1536`
   [VERIFIED: no `interestCalculationPeriodMethod` call in `LoanApplicationTerms.java:579-606`].
6. **Nothing about the server path, the tenant rounding mode, timezones, or PostgreSQL.** Path A touches no
   database. Every `Asia/Ulaanbaatar` / `Asia/Hovd` question in `reference-oracle.md` finding 1 remains open.

---

## Required changes — priority ordered, actionable without me

**P0 — blocking admissibility as vectors; do these before any vector-store promotion:**

1. **Attach a machine-readable environment-attestation block to the capture artefact**, per plan §4.1: Fineract
   commit, image digest, the image jar's `git.properties` `git.commit.id`, JVM string read *inside* the
   container, SHA-256 of the compiled harness classpath entries, runtime `MoneyHelper.PRECISION`, tenant
   rounding mode (or the explicit statement "no tenant set; `MoneyHelper` unreached except in D-04"), capture
   path (`Path A — embeddable seam`), and a UTC timestamp. Put it in `capture-raw.json` as a top-level
   `attestation` object — not in a Java comment. Until it exists, the plan's own rule says these are not vectors.
2. **Commit a reproducible run recipe** — the exact `docker run` / `javac` / `java` invocation and classpath
   construction, with the seam-class byte-identity check as a **precondition step that fails the run**, not a
   manual habit.
3. **Emit the three missing per-period columns** — `periodFromDate`, `feeAmount`, `penaltyAmount` — and re-run.
   Without `fromDate` the vectors cannot catch a period-boundary error in the Go port, and the shipped test
   asserts it for all seven C-00 periods.

**P1 — correctness of the record:**

4. **Relabel D-01.** Replace *"discriminates MathContext precision-vs-scale"* with what it actually is: *"the
   input configuration at which the two readings of `mc.getPrecision()` diverge; the oracle's answer recorded at
   precisions 8, 12 and 19."* Store the sense-1-only counterfactual beside it, tagged
   `COMPUTED-COUNTERFACTUAL — not observed`, and record the warning that on this vector the p12↔p19 delta
   coincides with the sense delta **by accident**.
5. **Print the stack trace (or top 5 frames) on the error branch** [`Capture.java:162-167`], so a failing
   capture records *where* it failed instead of requiring source archaeology.
6. **Switch every `BigDecimal` emission to `toPlainString()`** [`:172-174`, `:181`, `:185-194`], per plan §4.0.
7. **Record `CurrencyData.inMultiplesOf`** in the `inputs` block; the `Money` constructor reads it.
8. **Record the C-00 input deviation** (`name` / `displaySymbol` differ from the shipped test) and the finding
   that the module README transcript is stale relative to `misc/Main.java:86`, so plan §4.0 acceptance check 4
   is a *partial* second attestation.

**P2 — coverage, ordered by how much port risk each removes:**

9. **Pin the seed-selection rule with a vector**: `scheduleGenerationStartDate = 2024-01-01`,
   `disbursementDate = 2024-01-31`. Source says the seed is the disbursement date
   [`LoanApplicationTerms.java:583-589`]; no captured vector proves it.
10. **Run the tranche path with a tenant** (`ThreadLocalContextUtil.setTenant` +
    `MoneyHelper.initializeTenantRoundingMode`), capturing `allowFullTermForTranche` `true` vs `false` as a
    matched pair, and **stamp the tenant rounding mode on both** — that branch runs under
    `MathContext(19, <tenant mode>)`, not the caller's `mc`.
11. **Close the remaining plan gaps Path A *can* reach**: 0 % rate, `numberOfRepayments = 1`, `ACTUAL`/`ACTUAL`
    across a Feb 29, and the plan's MNT-scale C-04/C-05/C-06 shapes.
12. **Record in `reference-oracle.md` that §3.5 (`installmentAmountInMultiplesOf`) and multi-tranche are
    UNREACHABLE through Path A** — the Builder has no setter for the former and `disbursementDatas` is fixed
    empty. Planning further Path A captures for them wastes fire time.

---

## What this capture set does and does not license us to conclude about gate G-1

**It licenses:**

- **G-1 unblock step 1 is satisfied for the precision-vs-scale defect.** A discriminating configuration was run
  against the pinned oracle and the oracle's answer recorded: at precision 12, principal 87,654,321,
  18 × 18.5 % p.a., the oracle emits period-5 principal `4,531,420.25` / interest `1,082,346.53` and final
  principal `5,528,535.21`. The sense-1-only reading that DEC-1's current text describes yields `…26` / `…52` /
  `5,528,535.20`. **DEC-1 as drafted is empirically wrong by one minor unit**, not merely arguably wrong. The T4
  retry may proceed on evidence rather than on re-derivation alone, and G-1 open decision 3 ("must the
  discriminating vector be captured before ratification?") can be answered *"it has been."*
- **G-1 open decision 5 is settled on the facts.** `allowFullTermForTranche` is provably live: flipping it alone
  changes control flow observably (§7). Treating it as a conformance obligation rather than a dead field is now
  the only position consistent with the oracle.
- **G-1 open decision 2 has its evidence base.** The oracle's emitted order at the boundary is recorded with
  full precision (§6). The *choice* between reproducing it and rejecting the request at the boundary remains the
  ratifier's alone.
- **A month-end rule for the Go port**, in the form the source states and the oracle confirms: re-anchor to the
  seed day, floored by the target month's length, whenever monthly and `seedDay > 28` (§5) — keyed off the
  disbursement date per source, though that keying is not yet vectored.

**It does not license:**

- **Ratifying or amending DEC-1.** G-1 is a `user` CONTRACT gate. This audit changes what the ratifier knows; it
  does not cross the gate, and nothing here is stored in contract-shaped form.
- **Treating these nine results as admissible golden vectors.** By the capture plan's own §4.1/§4.2 rules they
  are not — no attestation block, three mandated columns missing, no reproducible recipe. They are *audited
  observations*: reliable inputs to a decision, not yet entries in a vector store.
- **Any conclusion about `installmentAmountInMultiplesOf`, multi-tranche, mid-term rate changes, 0 % rates,
  single-installment loans, `ACTUAL`/`ACTUAL` day counts, MNT at any decimal setting other than 2, the tenant's
  configured rounding mode, timezone handling, or anything on the server path.** All untouched by pass 1.
- **Any inference that "the golden test passes" means the port is safe.** C-00 passing is a harness check. The
  entire point of D-01 is that C-00 **cannot** detect the defect class that matters — at principal 100 the
  currency layer absorbs it.
- **Cutover of anything.** Unchanged, and not in question here.
