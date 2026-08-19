# T50 — separate the AMBIENT rounding mode from the THREADED one

Branch `softhouse/T50-ambient-vs-threaded-rounding`.
**RAW OBSERVED ONLY.** Nothing here is promoted, nothing is admitted to the graded domain, and no
DEC-1 amendment is proposed. G-1 is open; this is evidence and provenance, not contract text.

Artefacts (all under `.softhouse/capture/mathcontext/`):

| file | what |
|---|---|
| `src/CaptureT50Ambient.java` | Tier 1 harness — the site expressions, run against the oracle's own classes |
| `src/run-t50-tier1.sh` | Tier 1 precondition script (throwaway `docker run --rm`) |
| `src/CaptureT50Tier2.java` | Tier 2 harness — the oracle's own methods, private ones by reflection |
| `src/run-t50-tier2.sh` | Tier 2 precondition script |
| `src/t50-negative-tests.sh` | failability proof — 2 clean acceptances, 9 corruption rejections |
| `analysis/t50_assert_tier1.py` / `t50_assert_tier2.py` | the admissibility assertions + full cell dumps |
| `analysis/t50_pivot_tier1.py` + `-output.txt` | the Tier 1 grid as 7×7 pivot tables, 2016 cells |
| `out/t50-tier1.json` (2016 cases) / `out/t50-tier2.json` (1400 cases) | the payloads |
| `out/t50-tier1-assert.txt` / `t50-tier2-assert.txt` | the runs, cell by cell |
| `out/t50-digests.txt` | sha256 of every T50 artefact |

Both runners printed `== PASS -- capture admissible`.

---

## What I set out to separate

Two open findings, one mechanism: **a rounding mode a porter would naturally thread is actually
taken from the ambient `MoneyHelper` context.**

- **N46-1** — `ProgressiveLoanScheduleGenerator.java:445-446` (`calculateInstallmentCharge`) and
  `:464-465` (`calculateSpecificDueDateChargeWithPercentage`) divide under the **threaded** `mc` and
  then hand the quotient to the **two-argument** `Money.of(currency, amount)`.
  `[VERIFIED: ProgressiveLoanScheduleGenerator.java:445, :464 — both lines read
  `Money.of(cumulative.getCurrency(), amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc))`]`
- **N46-3** — `MathUtil.percentageOf(BigDecimal, BigDecimal, int)` builds
  `new MathContext(precision, MoneyHelper.getRoundingMode())`.
  `[VERIFIED: MathUtil.java:472-473]`

The exact mechanism, re-derived from source before any run:

- `Money.of(currency, amount)` → `of(currency, amount, MoneyHelper.getMathContext())`
  `[VERIFIED: Money.java:114-116]`.
- The private constructor stores that context and then rounds:
  `this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());`
  `[VERIFIED: Money.java:52]`, where `getMc()` is
  `return mc != null ? mc : MoneyHelper.getMathContext();` `[VERIFIED: Money.java:494-496]`.
- So on the two-argument path the injected `mc` **is** the ambient context, and the scale-2 rounding
  runs under the ambient mode — while the division one line earlier ran under the threaded mode.
- The `roundToMultiplesOf` branch at `Money.java:47-51` cannot confound this, because it is gated on
  `currency.getDecimalPlaces() == 0` and MNT has 2. Every probe below uses MNT with
  `inMultiplesOf = null`.

Six loan-path sites pass a literal `19` to `percentageOf`, all on down-payment computation
`[VERIFIED as grep with file:line, re-run this fire:
`AbstractCumulativeLoanScheduleGenerator.java:1897`, `:2060`; `LoanApplicationTerms.java:866`;
`LoanDownPaymentHandlerServiceImpl.java:198`; `LoanWritePlatformServiceJpaRepositoryImpl.java:448`,
`:3538` — no seventh site exists in main source]`.

---

## The tenant-write correction (confirmed or overturned)

**The brief's correction is CONFIRMED. A tenant write cannot separate the two contexts on Path B.**

`[VERIFIED: LoanScheduleAssembler.java:753 — `final MathContext mc = MoneyHelper.getMathContext();`]`
`[VERIFIED: LoanScheduleAssembler.java:765 — `LoanScheduleModel loanScheduleModel = loanScheduleGenerator.generate(mc, loanApplicationTerms, loanCharges, detailDTO);`]`

The threaded argument is the *same object reference* the ambient read returned, and
`MoneyHelper.getMathContext()` serves it out of a per-tenant cache
`[VERIFIED: MoneyHelper.java:90-93 — `mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))`]`,
so a later ambient read inside `Money.of` returns that identical instance. Moving the tenant's
`RoundingMode` moves both axes at once and the experiment observes nothing. That is why this stayed
`TO_BE_CAPTURED` across two fires, and **T46's and T48's recorded blocker ("needs a tenant write on
the shared server") is wrong** — not merely insufficient, but pointed at an experiment that cannot
work.

What does separate them is exactly what the brief said: an in-process run.
`MoneyHelper.initializeTenantRoundingMode(String, int)` is `public static` and writes a plain
`ConcurrentHashMap` `[VERIFIED: MoneyHelper.java:54-64]`, so setting the ambient mode needs **no
server, no tenant write and no database**. Both T50 tiers ran in throwaway `docker run --rm`
containers with no network and no PostgreSQL.

I could find **no** configuration under which a tenant write would have separated them on Path B, so
I am not overturning the brief.

**Corollary, and it is the sharper half of the finding:** Path A and Path B build their
`MathContext` differently.

| path | how the generator gets its `MathContext` | ambient vs threaded |
|---|---|---|
| Path A — embeddable seam `generate(mc, LoanRepaymentScheduleModelData)` `[:81]` | the caller supplies `mc`; the ambient is whatever the tenant has | **independent** — separable |
| Path B — server, `LoanScheduleAssembler` → `generate(mc, terms, charges, detailDTO)` `[:87]` | `mc = MoneyHelper.getMathContext()` `[:753]`, threaded at `[:765]` | **identical object** — inseparable in production |

So in the shipped server the two modes are always equal and the leak is *latent*. It becomes live the
moment a port, a test harness, or any future code threads a context that is not the ambient one —
which is precisely what a Go port doing "pass the MathContext down" would do.

**The seam asymmetry the brief asked me to state:** the Path A seam `generate(mc, LoanRepaymentScheduleModelData)`
at `:81` delegates to `generate(mc, loanApplicationTerms, null, null)`
`[VERIFIED: ProgressiveLoanScheduleGenerator.java:81-84]` — **`loanCharges` is hard-wired `null`**.
The charge sites at `:445` and `:464` are reached only from the `:87` overload. Consequence for the
program: **a Go conformance harness built on the Path A embeddable seam can never exercise a single
charge**, and therefore can never grade N46-1 by end-to-end comparison. Charge parity needs the `:87`
overload (Tier 2 below reaches it in process) or the live server.

---

## Tier 1 — method, cells observed, verdict

**Method.** Six probe sites × six input shapes × (7 ambient modes + ABSENT) × 7 threaded modes =
**2016 cells**, each with its own tenant id so `MoneyHelper`'s per-tenant caches make the cases
independent. Every class exercised (`Money`, `MoneyHelper`, `MathUtil`, `CurrencyData`) is loaded
from `/app/fineract-provider.jar`; the harness copies **no** Fineract source, which the runner
asserts. The eight probed `.class` files were located in their module jars and digested
(`out/t50-tier1-class-digests.txt`).

Sites (S1/S6 are the two N46-1 loci, transcribed; S3/S4 the two N46-3 loci; S2/S5 are the
counterfactual mirrors — what a port that threads the context would compute):

| site | expression | source |
|---|---|---|
| S1 | `Money.of(cur, a.multiply(pct).divide(100, mc))` | `ProgressiveLoanScheduleGenerator.java:445-446` |
| S6 | same expression | `…:464-465` |
| S2 | `Money.of(cur, …, mc)` — 3-arg | counterfactual |
| S3 | `MathUtil.percentageOf(a, pct, 19)` | `MathUtil.java:472-473` |
| S4 | `Money.of(cur, MathUtil.percentageOf(a, pct, 19))` | `LoanApplicationTerms.java:865-866` |
| S5 | `MathUtil.percentageOf(a, pct, new MathContext(19, threaded))` | counterfactual |

Values chosen so the rounding step under test is an **exact tie**: V1 `100.50 × 1% = 1.005`
(last kept digit even), V2 `100.50 × 3% = 3.015` (odd), V4 `4,020,100.50 × 25% = 1,005,025.125`
(MNT-sized), V5/V6 twenty-significant-digit values that tie at 19 digits, and **V3 the null control**
`100.00 × 1% = 1.0000` where no rounding decision exists.

**Attestation and coverage guards, all enforced in the runner:**

- `MoneyHelper.PRECISION` read off the oracle = **19**.
- The **ordinal map read back out of `MoneyHelper` itself**, not assumed:
  0→UP, 1→DOWN, 2→CEILING, 3→FLOOR, **4→HALF_UP**, 5→HALF_DOWN, **6→HALF_EVEN**; ordinal 7 throws
  `IllegalArgumentException: Invalid rounding mode value: 7. Valid values are 0-6`.
  `[VERIFIED: t50-tier1.json → ordinalProof]`
- **Vacuity canary (T46-N2):** reading `MoneyHelper.getMathContext()` on a tenant that was never
  initialised **threw** `IllegalStateException: Rounding mode is not initialized for tenant:
  t50_canary_never_initialised`. The absence probe is therefore live, not vacuous.
- 2016/2016 cases attested object-vs-intent, 0 disagreements. **1512 cases have the ambient mode
  strictly different from the threaded mode** — the separation no tenant write can produce.

**Cells observed — the absence probe (42 ABSENT cases per site):**

| site | ABSENT cases | threw `Rounding mode is not initialized` | completed | reads ambient? |
|---|---|---|---|---|
| S1-CHARGE-2ARG | 42 | **42** | 0 | YES, by absence |
| S6-SPECIFICDUE-2ARG | 42 | **42** | 0 | YES |
| S3-PCTOF-INT19 | 42 | **42** | 0 | YES |
| S4-DOWNPAYMENT-LAT866 | 42 | **42** | 0 | YES |
| S2-CHARGE-3ARG | 42 | 0 | **42** | NO |
| S5-PCTOF-MC | 42 | 0 | **42** | NO |

**Cells observed — the 7×7 grid** (`ambient moves it in N/7 threaded columns` means: hold the threaded
mode fixed, sweep the ambient mode, count columns in which the observation changed):

| site | value | distinct | ambient moves it | threaded moves it |
|---|---|---|---|---|
| S1 | V1 (1.005) | 2 → `1.00`, `1.01` | **7/7** | **0/7** |
| S1 | V2 (3.015) | 2 → `3.01`, `3.02` | **7/7** | 0/7 |
| S1 | V4 (1,005,025.125) | 2 → `1005025.12`, `1005025.13` | **7/7** | 0/7 |
| S1 | V5 / V6 (19-digit tie) | 2 | **7/7** | 0/7 |
| S1 | V3 null control | **1** | 0/7 | 0/7 |
| S6 | identical to S1 on all six values | | **7/7** | 0/7 |
| S2 (3-arg) | V1, V2, V4, V5, V6 | 2 each | 0/7 | **7/7** |
| S3 | V1, V2, V3, V4 | **1** (arithmetic exact at 19 digits) | 0/7 | 0/7 |
| S3 | V5, V6 | 2 → e.g. `…456.788` / `…456.789` | **7/7** | 0/7 |
| S4 | V1, V2, V4, V5, V6 | 2 each | **7/7** | 0/7 |
| S5 (MathContext overload) | V5, V6 | 2 each | 0/7 | **7/7** |

Worked cell, S1/V1, ambient=HALF_EVEN, threaded=HALF_UP: quotient `1.005` → observed **`1.00`**.
Mirror control, ambient=HALF_UP, threaded=HALF_EVEN: quotient `1.005` → observed **`1.01`**.
The two runs differ, and they differ in the direction the *ambient* mode predicts.

Full 7×7 pivots for every (site, value) pair: `analysis/t50-pivot-tier1-output.txt`, 2016 cells.
Full one-line-per-cell dump: `out/t50-tier1-assert.txt`.

**Verdict (Tier 1).**
1. At the two N46-1 loci the **ambient** mode governs the money value and the **threaded** mode is
   entirely inert — 0/7 in every ambient row, on all five discriminating shapes.
2. Not merely inert at MNT scale: even on V5/V6, where the threaded mode *does* move the quotient's
   19th significant digit (visible in S2's cells), the subsequent `setScale(2)` discards the moved
   digit. So on this expression **there is no shape at 2 decimal places on which the threaded mode
   can be observed at all.**
3. `MathUtil.percentageOf(a, pct, 19)` takes the ambient mode (S3, 7/7), and its `MathContext`
   overload takes the threaded one (S5, 7/7) — the two overloads of the same helper are two
   different specifications.
4. `LoanApplicationTerms.java:865-866` (S4) leaks **twice** on the ambient: once in `percentageOf`
   and again in the 2-arg `Money.of`. Both leaks point the same way, so they compound rather than
   cancel.
5. The null control is flat on all six sites — the grid is not simply always-different.

---

## Tier 2 — method, cells observed, verdict

**Method.** Five legs × five shapes × (7 ambient + ABSENT) × 7 threaded = **1400 cells**, entering
the oracle's *own methods* rather than transcribed expressions. `LoanCharge` is a JPA entity with no
usable constructor, so it is allocated with `sun.misc.Unsafe#allocateInstance` and its fields set
reflectively; the class bytes executed are the oracle's, out of `BOOT-INF/lib/fineract-loan-*.jar`.
The generator is wired exactly as the shipped embeddable seam wires it
(`DefaultScheduledDateGenerator`, `ProgressiveEMICalculator` over it, a no-op
`InterestScheduleModelRepositoryWrapper`) `[VERIFIED against EmbeddableProgressiveLoanScheduleGenerator.java:38-43]`.

| leg | what it enters | reached how |
|---|---|---|
| L1 | `ProgressiveLoanScheduleGenerator#calculateInstallmentCharge` `[:432-452]` | reflection (private) |
| L2 | `#calculateSpecificDueDateChargeWithPercentage` `[:454-468]` | reflection (private) |
| L3 | `LoanApplicationTerms.assembleFrom(modelData, mc)` `[:579]` → Builder ctor `[:304, block :329-338]` | public |
| L4 | `#generate(mc, terms, charges, detailDTO)` `[:87]` with a percentage instalment fee | public |
| L5 | `LoanApplicationTerms.assembleFrom(...)` `[:609]` → ctor `[:747, block :863-869]` | reflection over the 76-parameter factory |

**Reachability, published before any verdict:**

| leg | ambient-present cases | completed | ABSENT cases | threw `Rounding mode is not initialized` |
|---|---|---|---|---|
| L1 | 245 | **245** | 35 | **35** |
| L2 | 245 | **245** | 35 | **35** |
| L3 | 245 | **245** | 35 | **0** (completed) |
| L4 | 245 | **245** | 35 | **35** |
| L5 | 245 | **245** | 35 | **35** |

**Cells observed:**

| leg | value | distinct | ambient moves it | threaded moves it |
|---|---|---|---|---|
| **L1** | W1 `100.50 × 1%` | 2 → `1.00`, `1.01` | **7/7** | **0/7** |
| L1 | W2 principal+interest branch | 2 → `1.00`, `1.01` | **7/7** | 0/7 |
| L1 | W3 interest-only branch | 2 → `1.00`, `1.01` | **7/7** | 0/7 |
| L1 | W4 MNT `4,020,100.50 × 25%` | 2 → `1005025.12`, `1005025.13` | **7/7** | 0/7 |
| L1 | W5 null control | **1** | 0/7 | 0/7 |
| **L2** | W1–W4 | 2 each, same values as L1 | **7/7** | 0/7 |
| L2 | W5 null control | **1** | 0/7 | 0/7 |
| **L3** (Path A builder) | W1 | 2 → `1.00`, `1.01` | **0/7** | **7/7** |
| L3 | W4 | 2 → `1005025.12`, `1005025.13` | 0/7 | **7/7** |
| **L5** (server ctor) | W1 | 2 → `1.00`, `1.01` | **7/7** | **0/7** |
| L5 | W4 | 2 → `1005025.12`, `1005025.13` | **7/7** | 0/7 |
| **L4** | all five | **1** each (`0.00` on all six periods) | 0/7 | 0/7 |

L5's positional argument fill is self-validated: `indexSelfCheck=params=76 t[0]=CurrencyData
t[15]=Money t[24]=Money t[53]=Boolean t[54]=BigDecimal t[39]=Integer; principalAsAssembled=100.50;
pctAsAssembled=1`, and the observation under ambient HALF_UP / threaded HALF_EVEN is **`1.01`**,
i.e. ambient-governed.

**Verdict (Tier 2).**

1. **L1 and L2 reproduce Tier 1 exactly at the real methods.** The two N46-1 loci are
   ambient-governed on every discriminating shape, on all three charge-calculation branches
   (percent-of-amount, percent-of-amount-and-interest, percent-of-interest). This is an
   *observation* of the private methods, not a transcription of their bodies.
2. **A new finding the brief did not anticipate: `LoanApplicationTerms` computes the down payment
   two different ways, and which one runs depends on which factory built the object.**
   - The **Builder** constructor threads everything:
     `Money.of(getCurrency(), MathUtil.percentageOf(getPrincipal().getAmount(), getDisbursedAmountPercentageForDownPayment(), builder.mc), builder.mc)`
     `[VERIFIED: LoanApplicationTerms.java:329-332]` — 3-arg `Money.of`, `MathContext` overload of
     `percentageOf`, and `roundToMultiplesOf(..., builder.mc)` at `:334`.
   - The **other** constructor is fully ambient:
     `Money.of(getCurrency(), MathUtil.percentageOf(getPrincipal().getAmount(), getDisbursedAmountPercentageForDownPayment(), 19))`
     `[VERIFIED: LoanApplicationTerms.java:865-866]`, preceded by 2-arg `Money.zero(getCurrency())`
     at `:863` and followed by 2-arg `roundToMultiplesOf` at `:868`.
   - Observation matches source: L3 (Builder) is threaded 7/7 and its ABSENT cases **complete**;
     L5 (other ctor) is ambient 7/7 and its ABSENT cases **throw** 35/35.
   - Which one production uses: `LoanScheduleAssembler.java:548` calls the long
     `assembleFrom(...)` overload `[VERIFIED]`, which returns
     `new LoanApplicationTerms(currency, …)` `[VERIFIED: LoanApplicationTerms.java:647]` — the
     `:747` constructor. **So the server down-payment path is the AMBIENT one**, and the Path A
     embeddable seam's is the threaded one `[VERIFIED: ProgressiveLoanScheduleGenerator.java:82 →
     LoanApplicationTerms.java:579 → :564 `new LoanApplicationTerms(this)`]`.
3. **L4 was reached but did not discriminate — reported, not dressed up.** All 35 ABSENT cases threw,
   so `generate(:87)` provably reads the ambient context somewhere; but the observed fee was `0.00`
   on all six periods in all 245 completed cells. The published diagnostic says why:
   `chargeIsPercentageBased=true; chargeIsInstalmentFee=true; chargeIsFeeCharge=true;
   chargeIsDueAtDisbursement=false; percentage=1; perPeriodBase=P=0.00/I=0.00; …` — **the schedule
   this harness produced has zero principal and zero interest in every period**, so the percentage
   charge has a zero base and no rounding decision exists. This is a T46-N3 "shape that changes
   nothing": the charge machinery ran, the money was zero, and **no conclusion about N46-1 is drawn
   from L4.** What a future fire needs is stated in Follow-ups.

---

## N46-1 status after this task

**CONFIRMED BY OBSERVATION.** Previously `TO_BE_CAPTURED` for two fires on a blocker that could not
have worked.

- Confirmed twice independently: by transcription against the oracle's own `Money`/`MoneyHelper`
  (Tier 1 S1/S6, 7/7 vs 0/7 on four discriminating shapes) and by entering the private methods
  themselves (Tier 2 L1/L2, 7/7 vs 0/7 on four shapes across all three charge-calculation branches).
- Confirmed by **absence** as well as by difference: 42/42 (Tier 1) and 35/35 (Tier 2) uninitialised-
  ambient cases threw `IllegalStateException`, while the 3-arg counterfactual completed 42/42.
- Reachable at MNT's 2 decimal places: the observed pair on an ordinary MNT-sized amount is
  `1005025.12` vs `1005025.13` — one minor unit, on a fee.
- **Still not gradeable by the existing corpus**, and now for a reason stronger than "no capture has
  the two modes disagreeing": on Path B they *cannot* disagree (same object), and the Path A seam
  carries no charges at all (`:81` passes `loanCharges = null`).

## N46-3 status after this task

**CONFIRMED BY OBSERVATION, and sharpened.**

- `MathUtil.percentageOf(value, percentage, 19)` takes the ambient mode: Tier 1 S3, ambient 7/7,
  threaded 0/7, on the two shapes where a 19-significant-digit rounding decision exists; 42/42
  absence cases threw. The `MathContext` overload (S5) is the exact mirror.
- The literal-19 sites are only *half* the picture. At `LoanApplicationTerms.java:865-866` the
  ambient is read **twice** — by `percentageOf(…, 19)` and again by the 2-arg `Money.of` — and it is
  the second read that is reachable at ordinary MNT magnitudes. `percentageOf` itself only
  discriminates when the operand needs more than 19 significant digits (S3 gave one distinct value on
  V1/V2/V3/V4 and two on V5/V6), whereas the `Money.of` scale-2 rounding discriminates at
  `1,005,025.125`.
- The two constructors of `LoanApplicationTerms` disagree with each other (see Tier 2 verdict 2), and
  the **server path is the ambient one**.
- I did **not** reach the other five literal-19 sites. `AbstractCumulativeLoanScheduleGenerator:1897`
  and `:2060`, `LoanDownPaymentHandlerServiceImpl:198`,
  `LoanWritePlatformServiceJpaRepositoryImpl:448` and `:3538` are `[VERIFIED as grep with file:line]`
  and `[UNVERIFIED as behaviour]`. What T50 established is that the *helper* they all call takes the
  ambient mode; whether each call site's surrounding code then re-rounds is not observed.

## What a Go port must do differently as a result

Stated as observations about the oracle's behaviour, not as contract text.

1. **Two rounding contexts must be modelled, not one.** A port that threads a single `MathContext`
   through `calculateInstallmentCharge` and uses it for the final quantisation to minor units will
   diverge from the oracle on every tie whenever the threaded mode differs from the tenant mode.
   The oracle's rule at `:445-446` is: **divide under the threaded context; quantise to the
   currency's minor units under the TENANT (ambient) mode.**
2. **The quantisation is `setScale(decimalPlaces, ambientMode)`, and it is where the money lands.**
   In integer-minor-unit terms: compute the exact rational `amount × percentage / 100`, then round
   to minor units using the tenant's mode. The threaded precision (19) affects only digits the
   quantisation discards — on this expression it is unobservable at 2 decimal places.
3. **`percentageOf(x, p, <literal precision>)` and `percentageOf(x, p, mc)` are different
   functions.** A port must not collapse them. The int overload = `MathContext(precision,
   tenantMode)`; the `MathContext` overload = the caller's mode.
4. **Down payment has two implementations in the oracle and the server takes the ambient one.** A Go
   port must decide which it is reproducing and say so; porting the Builder variant would silently
   reproduce Path A rather than production.
5. **Under the ratified tenant parameters `(19, HALF_UP)` there is currently no divergence**, because
   the server makes the two contexts the same object. The risk is entirely in the *port*: threading
   a context is the natural Go idiom and is exactly the thing that breaks parity here. This is a
   defect class a Go port can introduce, not one Fineract currently exhibits.
6. **A conformance harness on the Path A embeddable seam cannot grade any of this.** `:81` passes
   `loanCharges = null`, so charge arithmetic is unreachable from that seam by construction.

## Negative tests / failability

`src/t50-negative-tests.sh` — no container, no oracle. Transcript:
`out/negative/t50-negative-tests-output.txt`, per-case transcripts `out/negative/t50-neg-*.txt`.

```
ok  tier1-clean                  -> exit 0 (wanted 0)
ok  tier2-clean                  -> exit 0 (wanted 0)
ok  N1-vacuous-canary            -> exit 1   (canary rewritten to "NO THROW")
ok  N2-attestation-drift         -> exit 1   (ambient object ≠ what the case id declares)
ok  N3-threaded-precision-drift  -> exit 1   (threaded precision echoed as 12)
ok  N4-null-control-moves        -> exit 1   (one V3 control cell changed to 0.99)
ok  N5-case-dropped              -> exit 1   (one case deleted; count no longer matches)
ok  N6-absent-case-succeeded     -> exit 1   (an ABSENT case made to look like it read the ambient)
ok  N7-ordinal-map-drift         -> exit 1   (ordinal 4 relabelled HALF_EVEN)
ok  N8-tier2-null-control-moves  -> exit 1
ok  N9-tier2-vacuous-canary      -> exit 1
```

N1/N9 are the important ones: they prove the **coverage detector** works. If the absence probe had
been vacuous, the checker would have refused the payload rather than reporting 42/42 as evidence.

The **runners** were also observed rejecting real failures during this fire, not only synthetic ones:
`run-t50-tier1.sh` printed `BREACH: a probed class is NOT in the oracle jar` when the class-digest
step looked in `BOOT-INF/classes` (Fineract ships its modules as jars under `BOOT-INF/lib`), and
`BREACH: JSON payload does not parse` when a stack trace carried an unescaped tab. Both aborted the
run and published nothing. On the assertion path the runner moves the payload to `*.json.REJECTED`
before exiting non-zero.

## Server state (must be: untouched, nothing contacted)

- `fineract-fineract-1` — **Up 21 hours (healthy)**, `fineract-db-1` — **Up 43 hours (healthy)**, at
  the end of this task. Neither was started, stopped, restarted, re-tenanted, reconfigured, `exec`'d
  into, read from or written to.
- **No HTTP request was made to `https://localhost:8443`** and **no PostgreSQL connection was
  opened.** Both harnesses run entirely in process on classes unzipped from the jar; the code paths
  exercised reach no database.
- Every container was `docker run --rm`, mounting only `.softhouse/capture/mathcontext`.
- **No tenant write anywhere.** `MoneyHelper.initializeTenantRoundingMode` writes a static
  `ConcurrentHashMap` inside the throwaway JVM `[VERIFIED: MoneyHelper.java:54-64]`; it does not
  touch `fineract_tenants` or any schema.
- No Gradle was run in `/Users/buv/fineract`. `git -C /Users/buv/fineract status --porcelain` is
  **empty** and HEAD is `426a23544e8426a38ae43ae404670a0a7e85b9eb`, checked by both runners as a
  precondition and re-checked after the last run.
- Wrote only under `.softhouse/capture/mathcontext/` and `.softhouse/handoff/`.
  **`.softhouse/capture/charges/` was not touched** — it belongs to T51 this fire.
- The frozen adapter contract was not modified and no DEC-1 change is proposed.

## Unverified

Marked honestly; none of these is filled with a plausible value.

- **`[UNVERIFIED]` — the five other literal-19 `percentageOf` call sites.**
  `AbstractCumulativeLoanScheduleGenerator:1897`, `:2060`, `LoanDownPaymentHandlerServiceImpl:198`,
  `LoanWritePlatformServiceJpaRepositoryImpl:448`, `:3538` are verified as *text at those lines* and
  unverified as *behaviour*. Only `LoanApplicationTerms:866` was executed (Tier 2 L5).
- **`[UNVERIFIED]` — whether `generate(:87)` applies a percentage charge correctly on a non-zero
  schedule.** L4 ran, the ambient was provably read, and the fee was `0.00` because this harness's
  schedule had `P=0.00/I=0.00` in every period. I did not diagnose *why* the schedule was zero, and I
  am not asserting that the oracle loses the charge — a previous fire recorded charge-loss findings
  and this observation is **not** evidence for or against them.
- **`[UNVERIFIED]` — whether any *other* ambient read exists inside `generate(:87)`.** The absence
  probe proves at least one; it does not enumerate them. `Money.total(...)` at `Money.java:233` and
  `Money.zero(MonetaryCurrency)` at `:117-119` are further 2-arg (ambient) entry points I noted from
  source but did not probe.
- **`[UNVERIFIED]` — behaviour when the two contexts differ in *precision* as well as mode.** Every
  T50 cell threads precision 19, matching the ambient. Threaded-precision separation was T42's
  subject and is untouched here.
- **`[UNVERIFIED]` — anything about the live server's current tenant configuration.** T50 deliberately
  did not read it.
- L5's enum-typed and Integer-typed arguments were filled with type defaults (`values()[0]`, `1`) to
  get past unconditional unboxing in the `:747` constructor. This is `[VERIFIED]` as not affecting
  the observation only to the extent of the read-back self-check (principal and percentage arrive
  intact, `installmentAmountInMultiplesOf` stays null so `roundToMultiplesOf` cannot fire); I did not
  prove the other 70 arguments are irrelevant to the down-payment block, only that the block's own
  inputs are correct.

## Follow-ups

1. **Correct the two prior records.** T46's and T48's "needs a tenant write on the shared server" is
   wrong for this experiment and should be replaced with "needs an in-process run; a tenant write
   moves both axes together on Path B". Anything downstream that inherited that blocker should be
   re-checked.
2. **A discriminating charge vector still does not exist and cannot exist on the Path A seam.** If the
   program wants one, it must come from the `:87` overload or the live server. The specific missing
   piece is a `LoanApplicationTerms` shape that yields a non-zero per-period principal through
   `generate(:87)` in process — T50's L4 got everything except that.
3. **The `LoanApplicationTerms` dual implementation deserves its own item.** Two constructors, two
   rounding regimes, same field, and the seam a harness picks decides which one it grades. Suggest
   raising it as a distinct finding rather than folding it into N46-3.
4. **Enumerate the ambient entry points.** `Money.java` has at least four 2-arg/no-mc doors
   (`of(currency, amount)` `:114`, `zero(MonetaryCurrency)` `:118`, `total(...)` `:233`, `getMc()`
   fallback `:494`). A port needs the list, and the absence technique used here enumerates them
   cheaply: remove the ambient initialisation and see what throws.
5. **Adopt the absence probe as the default coverage detector.** Both tiers here are readable
   primarily because the ABSENT column tells you whether the site was reached *before* the rounding
   grid tells you what it did. It cost about ten lines per harness.
