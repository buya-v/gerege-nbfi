# T42 — which `MathContext` actually governs the money, and whether precision 19 is observable

> ## CORRECTED IN PLACE BY T46 — read this first
>
> The T44 independent audit (`.softhouse/reviews/T44-capture-audit.md` §3) raised eleven findings
> against this handoff and its capture set. **T46 closed them and edited this document in place.**
> Every correction is marked `**[T46 CORRECTION …]**` at the point it applies; the full working,
> the identity proofs and the new negative legs are in
> `.softhouse/handoff/T46-mathcontext-corrections.md` and
> `.softhouse/capture/mathcontext/ATTESTATION.md`.
>
> **No recorded observation was changed by T46**, and no T42 payload was modified. The two
> corrections that change a *number* in this document are N-3's site inventory (M-1/M-2) and the
> E1 matrix's distinct coverage, 10 rather than 13 (M-3). Everything else is a correction to a
> justification, a `file:line`, or a claim's scope.
>
> **The three headline results are unaffected and stand:** (a) the ambient context is provably
> never read on the Path A seam for a 2-dp currency; (b) on Path B the threaded context *is* the
> ambient object; (c) threaded precision 19 separates from 12 on ordinary shapes.

## Verdict, in two sentences

**(a) T39's N-3 is right about Path A and wrong as a general claim, and the difference matters.**
On the **Path A** seam the threaded `MathContext` is the arithmetic and the ambient `MoneyHelper`
context is — on 11 of 13 probe shapes — **provably never read at all**, not merely inert. On
**Path B** the two are *the same object*: the production caller does
`final MathContext mc = MoneyHelper.getMathContext()` and hands that straight to
`generate(mc, …)`, which I read off the **deployed bytecode inside the running server**. So the
ambient reading is worthless as evidence about Path A arithmetic and is *the* evidence about
Path B arithmetic. **No committed capture is mis-valued; T35's and T37's justifications are
wrong and must be re-worded, T36's is substantially sound.**

**(b) T39's N-4 is superseded: a separating shape exists, and it is an ordinary loan.**
Threaded precision 19 separates from 12 on **MNT 50,000,000 over 360 months at 21.6 %** — total
interest **274,527,298.56** at precision 19 against **274,527,296.51** at precision 12, a
**MNT 2.05** gap across **861 cells** — and at **MNT 25,000,000 / 360 months / 7.7 %** (610 cells).
Buyan's ratified precision-19 parameter is **observably load-bearing** on shapes a Mongolian NBFI
would actually write. Separation is **not monotone in principal**, so there is no "safe below X".

**Branch:** `softhouse/T42-mathcontext-inforce`.
**Written:** `.softhouse/capture/mathcontext/**` and this file. Nothing else.
**Storage:** raw observed form only; nothing promoted (`capture/mathcontext/PROVENANCE.md`).
**Totals:** 354 observed cases across two captures, **243,308 cells compared full-cell**, 172
control cells reproduced, 6 negative legs all failing correctly, both payloads byte-deterministic.

---

## 1. The experiments, and their negative runs

Recipe: `.softhouse/capture/mathcontext/REPRODUCE.md`. Failability: `NEGATIVE-TESTS.md`.
Attestation: `ATTESTATION.md`. All figures below are from
`analysis/discriminate-output.txt`, `analysis/discriminate2-output.txt`,
`analysis/controls-output.txt` and `out/t42-pathb-wiring.txt`.

### E1 — the ABSENCE probe. The decisive one, and the one T39 could not run.

T39 varied the two contexts with **global `-D` overrides**, one whole run per axis, and inferred
"the ambient is not in force" from *nothing moved*. That inference is weak: a rounding-mode flip
is only visible on a value that lands on a rounding boundary, so "nothing moved" is consistent
with "it was read and happened not to matter".

T42 replaces the difference test with an **absence** test. Each case carries its own tenant id
(`MoneyHelper` caches per tenant, `MoneyHelper.java:37-38, :91-93` — **[T46 CORRECTION, M-9]**
this document originally cited `:36-37`; `:37` is `roundingModeCache` and `:38` is
`mathContextCache`, re-opened in the pinned checkout). The `-D` cases put a tenant
into `ThreadLocalContextUtil` and **never call `initializeTenantRoundingMode` for it**, so any
ambient read throws:

```
IllegalStateException: Rounding mode is not initialized for tenant: <id>   [MoneyHelper.java:79]
```

- **If the schedule still generates, the ambient context was provably never consulted.**
- **If it throws, the stack trace names the exact line that consulted it.**

**The probe is proved live, not vacuous.** The harness first runs an explicit canary on an
uninitialised tenant and records the throw; `run-mathcontext.sh` **fails the whole run** if the
canary ever stops throwing, and negative leg **N4** inverts that expectation and confirms the
guard fires. Without N4 this whole section would be unfalsifiable.

**Result — 13 shapes, one run** (`analysis/discriminate-output.txt`):

| shape | ambient `DOWN` | ambient `UP` | threaded `DOWN` | **ambient ABSENT** |
|---|---|---|---|---|
| plain (T39-CTL-Q0a) | identical | identical | **23 cells** | generated fine |
| drift (T39-P0-A) | identical | identical | **22 cells** | generated fine |
| monthEnd (T39-ME-B) | identical | identical | **23 cells** | generated fine |
| downPayment 25 % | identical | identical | **20 cells** | generated fine |
| downPayment 33.333 % on MNT 1,000,001 | identical | identical | **24 cells** | generated fine |
| downPayment + `installmentAmountInMultiplesOf` 1000 | identical | identical | **24 cells** | generated fine |
| `installmentAmountInMultiplesOf` 1000 | identical | identical | **23 cells** | generated fine |
| **currency 0 dp + `inMultiplesOf` 100** | **23 cells** | identical | identical | **THREW** |
| **currency 0 dp + `inMultiplesOf` 100 + downPayment** | **27 cells** | **17 cells** | identical | **THREW** |
| `fixedLength` 6 | identical | identical | **23 cells** | generated fine |
| `DaysInYear ACTUAL` | identical | identical | **18 cells** | generated fine |
| `ACTUAL` / `ACTUAL` | identical | identical | **23 cells** | generated fine |
| `interestRecognitionOnDisbursementDate` | identical | identical | **23 cells** | generated fine |

3,820 cells compared. Behavioural discriminator present on both axes: the threaded flip moves
`totalInterestAmount` `76723.70 → 76723.65` on the plain shape; the ambient flip moves it
`76900 → 76400` on the 0-dp shape.

**The two shapes that throw name the site by observation:**

```
IllegalStateException: Rounding mode is not initialized for tenant: t42_t42_mx_07_d
  at MoneyHelper.getRoundingMode(MoneyHelper.java:79)
  at Money.roundToMultiplesOf(Money.java:154)
  at Money.<init>(Money.java:50)
  at Money.of(Money.java:107)                       <-- the THREE-argument of(); mc WAS supplied
  at LoanApplicationTerms.assembleFrom(LoanApplicationTerms.java:580)
  at ProgressiveLoanScheduleGenerator.generate(ProgressiveLoanScheduleGenerator.java:82)
```

This is a genuine ambient **leak inside `Money` itself**: `LoanApplicationTerms.java:580` passes
the threaded `mc` explicitly, `Money.of(…, mc)` honours it, and then the constructor calls the
**two-argument** `roundToMultiplesOf(BigDecimal, Integer)` which hard-codes
`MoneyHelper.getRoundingMode()` [`Money.java:154`], ignoring the `mc` it was handed. It is reached
only when `currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 &&
inMultiplesOf > 0` [`Money.java:49-51`]. **MNT has 2 decimal places, so a ratified MNT
configuration never reaches it.** [VERIFIED: `analysis/discriminate-output.txt`; source lines
transcribed]

### E2 — the two WIRINGS, side by side, in one payload

The Path A / Path B distinction is not about the seam; it is about **where the caller got its
`MathContext`**. Capture 2 runs the identical shape twice, changing only that:

| tenant ordinal | ambient reading | effective threaded mc | **Path A wiring** total interest | **Path B wiring** total interest |
|---|---|---|---|---|
| 4 `HALF_UP` | `precision=19 roundingMode=HALF_UP` | `precision=19 roundingMode=HALF_UP` | 76723.70 | 76723.70 |
| 1 `DOWN` | `…=DOWN` | `…=DOWN` | **76723.70** | **76723.65** |
| 0 `UP` | `…=UP` | `…=UP` | **76723.70** | **76723.72** |
| 6 `HALF_EVEN` | `…=HALF_EVEN` | `…=HALF_EVEN` | 76723.70 | 76723.70 |

Cells moved from the ordinal-4 baseline: `4→1` Path A **0**, Path B **23**; `4→0` Path A **0**,
Path B **22**. On T36's half-cent-tie shape (MNT 1,162,502.50 × 12 × 21.6 %): `4→1` Path A **0**,
Path B **42**; `4→6` (`HALF_UP`→`HALF_EVEN`) Path A **0**, Path B **28**, `140457.89 → 140457.88`
— which independently reproduces the mechanism behind T36's `20925.05` / `20925.04` canary.

**Negative run:** `-Dt42.breakWiring=true` silently turns the Path B cases into Path A cases, and
`run-mathcontext2.sh`'s wiring assertion catches it (leg **N5**). So the two families are not
merely *labelled* differently — the label is checked against the object actually handed to the
generator. [VERIFIED: `analysis/discriminate2-output.txt`; `out/negative/n5-broken-wiring.txt`]

### E3 — the Path B wiring, read off the DEPLOYED bytecode of the running oracle

A source line is a claim about the repository. `out/t42-pathb-wiring.txt` reads the artefact that
is actually serving, via `javap -p -c` inside `fineract-fineract-1` (read-only; nothing restarted,
re-tenanted, reconfigured or written):

```
LoanScheduleAssembler.assembleLoanScheduleFrom(...)
   31: invokestatic  MoneyHelper.getMathContext:()Ljava/math/MathContext;
   34: astore        9
  ...
  109: aload         9           <-- THE SAME LOCAL SLOT
  116: invokeinterface LoanScheduleGenerator.generate:(Ljava/math/MathContext;...)
```

Running container image `sha256:e596339626bf…0459a`; jar sha256 `60fb6dbd631d…f4c9`;
`git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`;
`LoanScheduleAssembler.class` sha256 `d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea`.
Four `MoneyHelper.getMathContext` call sites across the two classes that build a schedule on
Path B. [VERIFIED: `out/t42-pathb-wiring.txt`]

### Controls and determinism

172 control cells reproduce digit for digit against **transcribed** literals — the shipped
`EmbeddableProgressiveLoanScheduleGeneratorTest` expectation (61 cells) and four committed
captures taken by **other harnesses on other tasks** (T37-3-A, Q0a, T39-P0-A's full 6×9 table,
T39-ME-B's full table). Both payloads are byte-identical on a re-run from fresh containers.
Six negative legs all exit 1 naming the breach. [VERIFIED: `analysis/controls-output.txt`;
`NEGATIVE-TESTS.md`; `ATTESTATION.md` §3-§5]

---

## 2. (a) The answer, stated as a rule an attestation can follow

### THE T42 ATTESTATION RULE

> **1. Name the two contexts separately. Never write "the `MathContext` in force" without saying
> which.**
>
> - the **THREADED** context = the `MathContext` object actually passed to the arithmetic
>   (`generate(mc, …)`, `scheduleModel.mc()`, `Money.of(…, mc)`);
> - the **AMBIENT** context = `MoneyHelper.getMathContext()` for the current tenant.
>
> **2. On the THREADED context, echo the object, not the intent.** Print
> `mc.getPrecision()`, `mc.getRoundingMode()` and `mc.toString()` read off the reference handed to
> the callee. This is the reading that is evidence about arithmetic.
>
> **3. On the AMBIENT context, state what it witnesses and what it does not.** It witnesses that
> the tenant was configured as ratified. It is evidence about the arithmetic **only where the
> caller sourced the threaded context from it** — and then say so, citing the wiring.
>
> **4. State the WIRING explicitly, per capture path:**
>
> | path | wiring | is the ambient reading evidence about the money? |
> |---|---|---|
> | **Path B** — running server | `LoanScheduleAssembler.java:753, :777, :797`, `LoanScheduleGeneratorServiceImpl.java:44` do `mc = MoneyHelper.getMathContext()` and pass it to `generate(mc, …)`. **Same object.** | **Yes** — it *is* the threaded context. Cite the wiring; do not leave it implicit. |
> | **Path A** — embeddable seam | the harness constructs its own `mc`. The two are **independent variables**. | **No** — it witnesses the tenant configuration only. It is still worth attesting for exactly that. Plus the one leak in rule 5. |
>
> **5. On Path A, the ambient context still reaches the money at exactly one site on the graded
> call graph** — `Money.<init>` → `Money.roundToMultiplesOf(BigDecimal, Integer)` →
> `MoneyHelper.getRoundingMode()` [`Money.java:50, :154`; `MoneyHelper.java:79`] — reached only
> when the currency has **0 decimal places** *and* a positive `inMultiplesOf`. **MNT has 2, so a
> ratified MNT capture never reaches it.** A capture that changes the currency's decimal places
> must re-attest the ambient context as load-bearing.
>
> **6. A configuration echo is not a discriminator. Carry a behavioural canary** — a value that
> differs by rounding mode — for whichever context the attestation claims governs. On Path B,
> T36's half-cent tie (`1,162,502.50 × 0.018 = 20,925.045` → `20925.05` under `HALF_UP`,
> `20925.04` under `HALF_EVEN`) is the right one and already exists. On Path A the canary must
> move the **threaded** mode, and `76723.70 → 76723.65` on the plain 6 × 21.6 % MNT 1,200,000
> shape is the cheapest one.
>
> **7. The PRECISION half of `(19, HALF_UP)` can never disagree with the source** —
> `MoneyHelper.PRECISION = 19` is a compile-time constant [`MoneyHelper.java:35`] and only the
> mode is tenant-configurable. Echoing it is a **provenance** claim, not a discrimination. But it
> **is** now discriminable behaviourally: see §3.
>
> **8. `(19, tenant mode)` is the LOAN-PATH rule, not a Fineract-wide one.** See finding **N-3**
> below: savings/deposits use hard-coded `MathContext.DECIMAL64` and `new MathContext(15|10, …)`.

---

## 3. (b) T39 N-4 — the honest search, and its result

### A separating shape EXISTS. Here is the smallest one found, per family.

Mechanism, transcribed not guessed: the rate factor is
`.setScale(mc.getPrecision(), mc.getRoundingMode())`
[`ProgressiveEMICalculator.java:1962` and `:1979`] — the precision acts as an **absolute scale** on
a quantity of order 1e-2, so the truncated residual is of order `10^-precision` and reaches a
minor unit once the balance × term product is large enough.

| n | rate | **smallest observed separating principal (MNT)** | cells | total interest p19 | total interest p12 |
|---|---|---|---|---|---|
| 360 | 7.7 % | **25,000,000** | 610 | `39166419.22` | `39166419.28` |
| 360 | 21.6 % | **50,000,000** | **861** | `274527298.56` | `274527296.51` |
| 120 | 13 % | 500,000,000 | 228 | `395864439.78` | `395864439.71` |
| 36 | 13 % | 2,000,000,000 | 72 | `425964544.20` | `425964544.19` |
| 6 | 21.6 % | 200,000,000,000 | 15 | `12787282386.75` | `12787282386.76` |

The 360 × 21.6 % row is the headline: **MNT 50,000,000 (≈ USD 14,500) over 30 years at 21.6 % —
an ordinary Mongolian NBFI loan — differs by MNT 2.05 in total interest between precision 19 and
precision 12, across 861 cells.** [VERIFIED: `analysis/discriminate2-output.txt`]

### The three caveats, stated plainly because they change how the result may be used

1. **Separation is NOT monotone in principal.** At 360 × 7.7 %, MNT 25,000,000 separates but
   30M, 40M, 50M, 60M and 70M do not, and 80M does again. At 360 × 21.6 %, 50M separates but 80M
   and 100M do not. The residual either crosses a minor-unit boundary or it does not; there is no
   threshold below which precision 12 is safe. **"Small loans are unaffected" would be a false
   inference from this table.**
2. **Precision 19 vs 8 separates almost everywhere** — 47 of 48 shapes in capture 1, including
   MNT 1,200,000 over 36 months. Only the 19-vs-12 question was ever hard.
3. **T39's N-4 was not wrong, it was narrow.** Its 16 shapes were 6, 12 and 36 periods at
   principals up to MNT 50,000,000; none of them reaches the 360-period regime where the residual
   accumulates. The correct reading of N-4 is "not separated by *these sixteen* shapes", which is
   what it said. It should now be **superseded**, not merely qualified.

### How wide the search was, and what it did not cover

**Swept:** 110 shapes across two captures — principals MNT 1,200,000 → 100,000,000,000,000 (8
decades plus a 24-point ladder inside the two lowest), terms {6, 36, 120, 360}, rates {7.7, 13,
16.8, 21.6}, `DAYS_30`/`DAYS_360` and `ACTUAL`/`ACTUAL`, on-lattice and inside T39's drift region,
at threaded precision {19, 12, 8}. **238,204 cells** compared full-cell.

**Not covered, `TO_BE_CAPTURED`:**

- `RepaymentEvery > 1`; `WEEKS`, `DAYS`, `YEARS` frequencies (`calculatePeriodRatio`'s other arms,
  `ProgressiveEMICalculator.java:1405, :1407, :1408`) — entirely uncaptured, as T39 also recorded.
- `DaysInYearCustomStrategy` non-null; `interestCalculationPeriodMethod = SAME_AS_REPAYMENT_PERIOD`
  (`:1513-1521`, a different rate-factor arm with `BigDecimal.valueOf(12)`/`(52)` denominators).
- Multi-disbursement, interest rate changes mid-term, interest pause, equal amortization, loan
  term variations, **charges** — none is reachable through `LoanRepaymentScheduleModelData`; Path A
  passes `loanCharges = null` [`ProgressiveLoanScheduleGenerator.java:83`].
- **Everything downstream of schedule generation**: repayment allocation, accruals, COB, charge-off.
  Those are Path B only, and there the ambient/threaded distinction collapses (§2 rule 4) — but see
  finding **N-4** for a site there that overrides the tenant mode outright.
- Precisions other than {19, 12, 8}; rounding modes other than {HALF_UP, DOWN, UP, HALF_EVEN}.

### What this means for the ratified precision-19 parameter

Before T42: `MoneyHelper.PRECISION = 19` was a **transcription** claim — true of the source, with
no captured shape able to tell 19 from 12. `CLAUDE.md` said "not a choice", and T39 N-4 said the
corpus could not see it.

After T42: it is an **observable** parameter. A Go port that computes the rate factor at any
precision other than 19 will diverge on ordinary retail shapes, and the corpus can now prove it.
**Recommended:** promote one 360-period shape (e.g. MNT 50,000,000 / 360 / 21.6 %) to the parity
corpus **once G-1 closes**, labelled as the precision-discriminating vector, alongside a
`(12, HALF_UP)` sibling kept explicitly as a discrimination probe. That pair is the only thing in
the program that makes Buyan's ratified parameter falsifiable.

---

## 4. The exact corrections T35, T36, T37 and `reference-oracle.md` need

**I did not edit any of these files.** The orchestrator should apply the following.

### Is any committed capture INVALIDATED? No. Here is the demonstration, not the assertion.

Three independent legs:

1. **The threaded context was independently echoed and asserted in every one of them.** T35's
   attestation table row "per capture" records `explicit mc (19, HALF_UP)` for eleven of twelve and
   `(12, HALF_UP)` for `P-CAL`; T37 records "threaded context `(19, HALF_UP)` on all ten parity
   candidates"; T39's `run-periodratio.sh` assertion 10 fails the run on any threaded mismatch. The
   *value* that governs was therefore attested correctly in all three.
2. **The single ambient site on the Path A call graph is unreachable at 2 decimal places**, proved
   by observation here (§1 E1) and by the source predicate `Money.java:49-51`. **Every committed
   Path A capture uses a 2-decimal-place currency** — I grepped the committed payloads:
   `"currencyDecimalPlaces": 0` appears in **no** committed capture outside my own
   (`.softhouse/capture/mathcontext/out/`), and the only committed file carrying
   `"currencyInMultiplesOf": 100` is `.softhouse/capture/out/capture-tenant-raw.json`, whose cases
   `T-IM100-he` / `T-IM100-hu` both record `"currencyDecimalPlaces": 2`.
3. **That committed pair is itself an independent corroboration.** `T-IM100-he` (ambient
   `HALF_EVEN`) and `T-IM100-hu` (ambient `HALF_UP`) run the same shape at the same threaded
   `(12, HALF_UP)` and return **identical** period rows — an earlier harness, on an earlier task,
   already showing the ambient inert on Path A at 2 dp. T42 explains why.

**Conclusion: the values are unaffected; only the justification was wrong.** That is exactly the
"fine answer" the task allowed — and it is demonstrated, not assumed.

### T35 — `.softhouse/handoff/T35-patha-admissibility.md`

- **§1 table, row "effective `MathContext`"** (line 37). Currently:
  *"**effective `MathContext`** for a tenant initialised with value 4 | precision 19, HALF_UP,
  ordinal 4; `matchesRatifiedProductionSetting: true` | [VERIFIED: `MoneyHelper.getMathContext()`
  /`getRoundingMode()` at runtime]"*.
  **Replace "effective" with "ambient (`MoneyHelper`)"** and append: *"On Path A this witnesses the
  tenant configuration, not the arithmetic — the threaded `mc` is supplied by the harness and is
  attested on the row below [T42]."*
- **§1 table, row "per capture"** (line 38) is already correct and is the load-bearing row.
  **Re-label it "THREADED `MathContext`, echoed per capture — this is the arithmetic."**
- **§5 leg 3 / "Precision needs no runtime reading"** (lines 128-129) — keep, but add: *"precision
  19 vs 12 is nonetheless behaviourally discriminable; see T42 §3."*
- **The one-line summary** (line 155): *"Path A pass 3b ran at `MathContext(19, HALF_UP)`…"* —
  amend to *"…ran with a **threaded** `MathContext(19, HALF_UP)` and an **ambient** `MoneyHelper`
  context also at `(19, HALF_UP)`, ordinal 4."*
- **No value in T35 changes.**

### T36 — `.softhouse/handoff/T36-pathb-admissibility.md`

**T36 is substantially sound and should not be rewritten.** It is the only one of the three whose
attestation was already carrying a behavioural discriminator (**P14**, the half-cent canary,
`20925.05` on `gerege` vs `20925.04` on `default`, same server, same run), and on Path B the
ambient reading *is* the threaded context. Two additions only:

- **§1 table, row "effective `MathContext`"** — add the wiring citation: *"On Path B the threaded
  `MathContext` handed to the schedule generator **is** this object:
  `LoanScheduleAssembler.java:753 → :765` (also `:777`, `:797`,
  `LoanScheduleGeneratorServiceImpl.java:44`), verified against the deployed bytecode in
  `.softhouse/capture/mathcontext/out/t42-pathb-wiring.txt`. That is why the ambient reading is
  evidence about the arithmetic here and is not on Path A [T42]."*
- **Note that P14 discriminates the MODE only, not the precision.** Add: *"the precision half of
  `(19, HALF_UP)` is a transcription claim here; T42 §3 supplies the first shape that
  discriminates it behaviourally."*

### T37 — `.softhouse/handoff/T37-dec1-binding-captures.md`

This is the one whose wording is straightforwardly wrong. **§5 bullet, lines 219-224.** Currently:

> **`MathContext` in force, on the oracle's own testimony, two independent witnesses:**
> (a) the oracle's SLF4J log, 11 of 11 lines `Initialized rounding mode for tenant '<id>': HALF_UP`;
> (b) `MoneyHelper.getMathContext()` echoed per case as `precision=19 roundingMode=HALF_UP` …
> Threaded context `(19, HALF_UP)` on all ten parity candidates …

**Neither (a) nor (b) is a witness to the arithmetic on Path A** — both read the ambient context,
which T42 shows is never consulted on these shapes. They are one witness to the *tenant
configuration*, counted twice. Replace with:

> **`MathContext`, two contexts, attested separately [T42]:**
> - **THREADED — this is the arithmetic.** `(19, HALF_UP)` on all ten parity candidates,
>   `(12, HALF_UP)` on the labelled calibration, echoed per case off the object handed to
>   `generate(mc, …)` and asserted by the runner.
> - **AMBIENT (`MoneyHelper`) — this is the tenant configuration, not the arithmetic.**
>   `precision=19 roundingMode=HALF_UP` echoed per case, corroborated by 11 of 11 SLF4J
>   `Initialized rounding mode …: HALF_UP` lines. On the **Path A** seam this context is
>   **provably never read** for a 2-decimal-place currency
>   [VERIFIED: `.softhouse/capture/mathcontext/analysis/discriminate-output.txt`], so it witnesses
>   provenance only. It would be evidence about the arithmetic on **Path B**, where the caller
>   sources the threaded context from it (`LoanScheduleAssembler.java:753`).
> - `MoneyHelper.PRECISION` read as **19**.
> - **No value in this capture changes.** The threaded context was already echoed and asserted; only
>   the justification above was wrong.

### `.softhouse/reference-oracle.md` — the corrections to fold in

1. **New subsection "Which `MathContext` governs — the attestation rule."** Paste §2 of this
   handoff (the eight-point rule) verbatim. It is the durable output of T42.
2. **The wiring table** (Path A independent / Path B ambient-sourced), with the four source
   citations and the deployed-bytecode digest
   `d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea`.
3. **The single Path A ambient leak**: `Money.<init>` `Money.java:50` →
   `roundToMultiplesOf(BigDecimal, Integer)` `Money.java:154` → `MoneyHelper.getRoundingMode()`
   `MoneyHelper.java:79`, reached only at `decimalPlaces == 0 && inMultiplesOf > 0`. Record that MNT
   at 2 dp never reaches it, **and that a Go port must reproduce it if it ever supports a 0-dp
   currency with an `inMultiplesOf`.**
4. **Amend T39's N-3** where reference-oracle records it: the claim "the ambient context is not the
   arithmetic in force" is **true of Path A only**; on Path B the two are the same object.
5. **Supersede T39's N-4.** Record the separating shapes table from §3, the non-monotonicity, and
   that precision 19 is now an observable parameter rather than a transcription claim.
6. **Record finding N-3 below** — `(19, tenant mode)` is a **loan-path** rule, not Fineract-wide.
7. **Record finding N-4 below** — the one loan-path site that hard-codes `RoundingMode.DOWN`.

---

## 5. New findings

**N-1. The ambient leak is inside `Money`, and it ignores an `mc` it was explicitly given.**
`LoanApplicationTerms.assembleFrom` [`:580`] passes the threaded `mc`; `Money.of(…, mc)`
[`Money.java:105-107`] honours it; and then `Money`'s constructor calls the **two-argument**
`roundToMultiplesOf` [`Money.java:50` → `:152-158`] which hard-codes `MoneyHelper.getRoundingMode()`.
The same pattern appears again at `Money.java:161-171`, where the *three*-argument
`roundToMultiplesOf(Money, Integer, MathContext)` uses the supplied `mc` for the division and then
finishes with the **two**-argument `Money.of`, i.e. the ambient context for the final `setScale`.
A Go port that threads a context correctly everywhere will therefore be *more* consistent than
Fineract and will diverge on 0-dp/`inMultiplesOf` currencies. **This is a port hazard, and it is
observed, not read.** [VERIFIED: stack trace, `analysis/discriminate-output.txt`; source lines
transcribed]

**N-2. On the two ambient-reading shapes the THREADED rounding mode is inert — a complete
inversion.** `zeroDpMultiples100` moves 23 cells on the ambient flip and **0** on the threaded
flip. With 0 decimal places and `inMultiplesOf = 100` everything is snapped to multiples of 100 by
the ambient mode, which swamps the threaded mode's 1e-19-scale effect. So "the threaded context is
what matters" is *also* shape-dependent, and neither context is universally the answer. This is
why the rule in §2 is a **per-site** rule and not a slogan.
[VERIFIED: `analysis/discriminate-output.txt`]

**N-3. `(19, tenant mode)` is the LOAN-PATH rule, not a Fineract-wide one — savings hard-codes
different precisions.** Every hard-coded `MathContext` in main source outside the loan modules is
in savings/deposits: **81** uses of `MathContext.DECIMAL64` (precision **16**, `HALF_EVEN`) —
49 in `fineract-core/.../portfolio/savings/domain/interest/` (`EndOfDayBalance`,
`AnnualCompoundingPeriod`, `BiAnnualCompoundingPeriod`, `MonthlyCompoundingPeriod`,
`QuarterlyCompoundingPeriod`, `DailyCompoundingPeriod`), 31 in `fineract-provider` savings
services, 1 in `fineract-savings` — plus **4** `new MathContext(15, MoneyHelper.getRoundingMode())`
and **9** `new MathContext(10, MoneyHelper.getRoundingMode())`
(`SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:526, :627, :695, :822, :919`;
`DepositAccountWritePlatformServiceJpaRepositoryImpl.java:496, :540, :837`;
`SavingsAccountDomainServiceJpa.java:329`). **The loan modules
(`fineract-loan`, `fineract-progressive-loan`, the embeddable seam) contain exactly one
hard-coded `MathContext` — see N-4 — and no `DECIMAL64` at all.**
Consequence: `CLAUDE.md`'s "**the production `MathContext` is therefore `(19, HALF_UP)`**" is
correct **for the loan path** and must not be carried into the savings port. Deposit-taking
activation is prohibited for the NBFI licence, but the *code is in scope for porting*, and a
porter who assumes `(19, HALF_UP)` there will be wrong on every compounding calculation.
[VERIFIED: repo-wide grep of the pinned checkout, `/src/test/` and `/misc/` excluded]

**N-4. One loan-path site overrides the tenant rounding mode outright.**
`AdvancedPaymentScheduleTransactionProcessor.java:2844-2845`:
`new MathContext(MoneyHelper.getMathContext().getPrecision(), RoundingMode.DOWN)` — it keeps the
tenant precision and **replaces the tenant mode with `DOWN`**, with a source comment explaining
why (*"Rounding mode DOWN grants that evenPortion cant pay more than unprocessed transaction
amount"*). Reached only when `evenPortion.add(balanceAdjustment).isLessThanZero()` during
in-advance repayment allocation. It is **not** on the schedule-generation path and so is invisible
to every capture this program holds. A Go port of repayment allocation must reproduce it, and DEC-1
must not state "the tenant rounding mode governs every step". `TO_BE_CAPTURED` — reaching it needs
a repayment transaction, i.e. Path B.
[VERIFIED: source transcription with `file:line`; **not** observed]

**N-5. The absence probe is a reusable technique, and it is strictly stronger than a
difference probe.** "I changed X and nothing moved" is consistent with "X was read and did not
matter". "I removed X and the computation completed" is not. `MoneyHelper` happens to throw on an
uninitialised tenant, which makes the technique free here; the general pattern —
*make the suspected dependency fatal rather than merely different, then prove the fatality is real
with a canary* — belongs in `patterns.md`. It found the exact leaking line in one run, which five
prior tasks of difference-probing did not.

**N-6. Threaded precision 19 vs 8 separates almost everywhere, 19 vs 12 only in the long-term
regime.** 47 of 48 capture-1 shapes separate 19 from 8, including MNT 1,200,000 over 36 months;
only 30 of 48 separate 19 from 12, and none at n=6 below MNT 200,000,000,000. The corpus's existing
precision-8 probes (`D-01-p8`) were therefore always going to look decisive and were never the hard
case. [VERIFIED: `analysis/discriminate-output.txt`]

**N-7. `MoneyHelper.getMathContext()` caches the `MathContext` object per tenant**
[`MoneyHelper.java:37, :91-93`] and only `initializeTenantRoundingMode` / `updateTenantRoundingMode`
evict it. T35 already established `updateTenantRoundingMode` has no production caller. Consequence
for Path B attestations: **the ambient reading is fixed at JVM start for a tenant**, so a
`c_configuration.rounding-mode` row edited after boot is inert — which T36 (**P13**) already
asserts. T42 adds only that this is now the *arithmetic's* cache on Path B, not just a
configuration cache, so the "row edited after boot is inert" fact is load-bearing rather than
hygienic.

---

## 6. What I could NOT capture, and why

- **A behavioural rounding-mode flip on the real Path B transport.** It needs the running server's
  tenant rounding mode changed, which needs a restart (`MoneyHelper` caches at startup; the only
  runtime re-init endpoint, `InternalConfigurationsApiResource:87-92`, is `@Profile(TEST)` and
  absent from this image — T36 established both). **Container discipline forbids it and another
  worker depends on the server staying up, so I did not do it.** What stands instead: the deployed
  bytecode showing the wiring, T36's already-committed two-tenant canary
  (`20925.05` / `20925.04` on `gerege` / `default`, same server, same run), and T42's Path-B-wired
  cases reproducing the mechanism on Path A's transport. `TO_BE_CAPTURED`: a Path B capture that
  moves the tenant ordinal and observes the response, at the next planned server restart.
- **Instrumented proof of *which* threaded step consumed the context.** Nothing here instruments
  `rateFactorByRepaymentPeriod`. What is observed is that the output moves when the threaded
  context moves and does not when the ambient does. That is a discrimination, not an internal
  observation.
- **The Path B-only ambient sites** — `AdvancedPaymentScheduleTransactionProcessor` (~14 sites),
  `LoanCharge.java:315`, `SingleLoanChargeRepaymentScheduleProcessingWrapper.java:141, :183`,
  `LoanSchedulePeriodData.java:161`, `LoanMapper.java:49`, `AprCalculator.java:53`,
  `LoanRepaymentScheduleInstallment.java:1296`. All read the ambient context, and on Path B that is
  the same object as the threaded one, so the distinction is moot there — but N-4 shows at least one
  of them departs from the tenant mode. Uncaptured.
- **Everything listed in §3's coverage statement** — other frequencies, `RepaymentEvery > 1`,
  charges, multi-disbursement, term variations.

---

## 7. Unverified

- **"11 of 13 shapes never consult the ambient context."** Verified *for those thirteen shapes*.
  It licenses no claim about an unsampled shape, and in particular none about anything reachable
  only through `LoanApplicationTerms` rather than `LoanRepaymentScheduleModelData`. `[UNVERIFIED as
  a general claim about Path A]`
- **"No committed capture is mis-valued."** Verified for the three legs in §4: the threaded context
  was independently attested, the Path A ambient site is unreachable at 2 dp, and every committed
  capture uses a 2-dp currency (grep over the committed payloads). It is **not** a re-run of the
  committed captures — I did not re-execute T35's or T36's suites. `[VERIFIED for the three legs
  stated; UNVERIFIED as a re-run]`
- **The `MathContext.DECIMAL64` / `new MathContext(15|10, …)` counts in N-3** are a repo-wide grep
  of the pinned checkout with `/src/test/` and `/misc/` excluded. They are **transcriptions**, not
  observations; no savings code was executed. `[UNVERIFIED as behaviour]`
- **N-4 is a source transcription only.** The `RoundingMode.DOWN` override was never executed.
  `[UNVERIFIED as behaviour]`
- **"Separation is not monotone in principal"** is verified on the sampled ladder (24 principals at
  360 × 7.7 %, 9 at 360 × 21.6 %). Whether some finer ladder is monotone in a sub-interval is not
  claimed. `[VERIFIED on the sampled points only]`
- **The Path B *transport* was not exercised at all by this task.** Every observation is Path A;
  the Path B claims rest on the deployed bytecode and on T36's committed canary. `[stated]`
- **Whether the `Money.java:154` leak is the ONLY ambient read on the Path A graph.** Thirteen
  shapes found one. A fourteenth shape may find another — T39's model was 13-of-13 clean before it
  was attacked, too. Assume the next review finds something.

---

## 8. Follow-ups

**F-1 (for the orchestrator, immediate).** Apply §4 to `.softhouse/reference-oracle.md` and to the
three handoffs. The `reference-oracle.md` attestation rule is the durable artefact; the handoff
corrections are hygiene.

**F-2 (for DEC-1, reported not acted on — T41 owns revision 8 this fire).** DEC-1 should state,
normatively: (i) which `MathContext` governs each step and where the caller obtains it; (ii) that
the `Money` `inMultiplesOf` branch reads the ambient rounding mode and ignores a supplied one
(N-1); (iii) that `(19, tenant mode)` is scoped to the loan path (N-3); (iv) that repayment
allocation contains a hard-coded `DOWN` (N-4) — or explicitly declare repayment allocation out of
DEC-1's graded domain.

**F-3 (for `patterns.md`).** Two entries. *Absence beats difference*: when a suspected dependency
can be made fatal, make it fatal and prove the fatality with a canary; "I changed it and nothing
moved" is not evidence it was not read (N-5). *An attestation must name the wiring*: "the
`MathContext` in force" is not a fact until you say which object and where the caller got it.

**F-4 (for the vector store, after G-1 closes).** Promote the precision-discriminating pair
(MNT 50,000,000 / 360 / 21.6 % at threaded `(19, HALF_UP)`, with its `(12, HALF_UP)` sibling kept
as a labelled discrimination probe). It is the only artefact in the program that makes Buyan's
ratified precision-19 parameter falsifiable. Also worth promoting: one 0-dp/`inMultiplesOf` shape,
as the vector that pins N-1's ambient leak — but only once DEC-1 decides whether a 0-dp currency is
in the graded domain at all.

**F-5.** Every corpus-validation script should adopt full-cell comparison. This is the fourth
defect class a three-scalar check could not see: the precision separation at 360 × 7.7 % moves 610
cells while `totalInterestAmount` moves by MNT 0.06.
