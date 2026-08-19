# T42 — attestation

Everything below is **measured**, not assumed. Where a value came from a source literal it is
given with `file:line`. Nothing here is promoted to the parity vector store — see `PROVENANCE.md`.

> ## CORRECTIONS APPLIED BY T46 — read this before any section below
>
> The T44 independent audit (`.softhouse/reviews/T44-capture-audit.md` §3) raised eleven findings
> against this set. T46 closed them. **No recorded observation was changed**; every correction
> below is a correction to a *claim*, and each is also applied in place at the section it
> affects. Full working: `.softhouse/handoff/T46-mathcontext-corrections.md`.
>
> | finding | the corrected claim |
> |---|---|
> | **M-1 / M-2** | N-3's hard-coded-`MathContext` inventory was miscounted. The re-derived inventory is in `analysis/t46_mathcontext_inventory-output.txt`: **15** `new MathContext(` sites in main source — **4** at literal precision 15, **5** at literal 10 (**9** combined, not 13), **2** at literal 8 (`SavingsAccountCharge.java:562`, `ShareAccountCharge.java:240` — the latter in **share accounts**, a different Tier B context), and **4** with a non-literal precision. |
> | **M-3** | The E1 shapes do **not** reach every ambient read on the Path A call graph. `installmentAmountInMultiplesOf` is **inert on this seam** and its target site was never reached; **distinct coverage of the E1 matrix is 10, not 13**. See §2.5 below. |
> | **M-4** | A second production caller, `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement`, also drops `installmentAmountInMultiplesOf`, while the REST `calculateLoanSchedule` path honours it. See §2.5. |
> | **M-5** | In capture 1 the keys named `threadedMathContextPrecision` / `threadedMathContextRoundingMode` carry the case record's **INTENT**, not a reading off the object. See §2.1. **T46 re-emitted the capture with the object echo added and proved the two agree on all 214 cases** — see §2.6. |
> | **M-6** | E3's shipped assertion is only `grep -c 'getMathContext' != 0`. T46 added a real machine assertion of the same-local-slot dataflow, with a negative leg. See §2.3. |
> | **M-7** | "No committed capture is mis-valued" must always travel with T42 §7's qualification. See §2.7. |
> | **M-8** | `NEGATIVE-TESTS.md`'s description of leg N4 was wrong; the vacuity guard had never been exercised. T46 exercised it (leg **N7**). |
> | **M-9** | Four `file:line` drifts inside `[VERIFIED]` tags, and "pass it to `generate(mc, …)`" is wrong for 2 of the 4 wiring sites. Corrected in §2.3 and §2.4. |
> | **M-10** | E2's "Path A = 0 cells" is a **replication** of E1's ambient rows, not an independent second experiment. See §6. |
> | **M-11** | `analysis/controls-output.txt` published 2 summary lines. A verbose mode now publishes all 172 compared cells: `analysis/t46-controls-cells-output.txt`. See §3. |

## 1. The environment, on the oracle's own testimony

| attested value | observed | source |
|---|---|---|
| pinned Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean | asserted on every run by both runner scripts |
| image | `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`; launched **by id** | `docker image inspect`, asserted every run |
| `/app/fineract-provider.jar` | sha256 `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9` | measured in-container, and again inside the **running** server |
| the jar's own `git.properties` | `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.build.version=1.16.0-SNAPSHOT`, **`git.dirty=false`** | read in-container; also read from the running `fineract-fineract-1` (`out/t42-pathb-wiring.txt`) |
| JVM | `21.0.11+10-LTS`, Zulu, Azul Systems | `out/t42-mathcontext-oracle-identity.txt` |
| seam class | byte-identical to the pinned original (`diff` silent), sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — the **same digest T37 and T39 recorded independently** | `diff` + `shasum`, asserted every run |
| classpath | **348** entries, digest `68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f` — **identical to T39's** — with **zero** Oracle Database / MySQL / MariaDB entries | asserted every run |
| `MoneyHelper.PRECISION` read from the running oracle | **19** | echoed in both payloads; asserted |
| stderr | 0 bytes on every capture run | asserted |
| database | none. This seam opens no connection. | Path A |

## 2. The MathContext attestation — stated the way T42 says it must be

This is the section T42 exists to get right. **Two contexts, named separately, each with what it
is and is not evidence of.**

### 2.1 The THREADED `MathContext` — the one handed to `generate(mc, …)`

- Capture 1: every case constructs its own and **echoes the constructed values**; the runner
  asserts each case ran at the precision and mode its id declares. Calibration `T42-CAL` at
  `(12, HALF_UP)`, the four controls and the whole matrix at `(19, HALF_UP)`, the precision sweep
  at `(19|12|8, HALF_UP)`.
  > **CORRECTION — M-5. In capture 1 these two keys are INTENT, not the OBJECT.**
  > `out/t42-mathcontext.json`'s `threadedMathContextPrecision` and
  > `threadedMathContextRoundingMode` are written from `c.precision()` and `c.mode()` — the case
  > record that was used to *construct* the `MathContext` — not from `mc.getPrecision()` /
  > `mc.getRoundingMode()` read off the reference handed to `generate(mc, …)`
  > [`src/CaptureMathContext.java`, the `b.append("        \"threadedMathContextPrecision\"…` pair].
  > That is a breach of T42's own ratified attestation rule 2, on the capture that carries E1, and
  > it covers **214 of the 354** cases in this set. The key names assert an object reading; read
  > them as intent.
  >
  > **What is NOT affected, and why — stated so the correction is not read as wider than it is.**
  > The two objects are constructed one line apart from the same record
  > (`final MathContext mc = new MathContext(c.precision(), c.mode());`), so no value depends on
  > the distinction; the **ambient** field in capture 1 *is* read off the object
  > (`MoneyHelper.getMathContext()`); the two stack traces are direct observations; and **E1 is an
  > absence result** — it turns on whether a schedule generated at all, which no echo can affect.
  > **T46 did not leave this as an argument: it re-emitted the capture with the object echo added
  > and proved the object and the intent agree on all 214 cases (§2.6).**
  >
  > `src/CaptureMathContext2.java:203-205` (capture 2) complies fully — it writes `mc.toString()`,
  > `mc.getPrecision()`, `mc.getRoundingMode()` and an explicit `wiring` field. The same fix is
  > demonstrated in a sibling set by
  > `.softhouse/capture/periodratio/src/CapturePeriodRatio2.java:342-345`, which echoes
  > `mc.toString()` / `mc.getPrecision()` / `mc.getRoundingMode()` and a `wiring` field
  > [read by T46, not edited — that set belongs to another task].
- Capture 2: every case **echoes `mc.toString()`, `mc.getPrecision()` and `mc.getRoundingMode()`
  read off the object actually passed to the generator**, not off the intent that built it.
- **This is the reading that is evidence about the arithmetic on Path A.** Observed: moving it
  moves the money on 11 of 13 probe shapes (`analysis/discriminate-output.txt`).

### 2.2 The AMBIENT `MoneyHelper` `MathContext` — the tenant's configured context

- Every case sets its own tenant into `ThreadLocalContextUtil`, calls
  `MoneyHelper.initializeTenantRoundingMode(tenantId, ordinal)` with an explicitly named ordinal
  (or, for the absence cases, **deliberately does not**), and echoes `MoneyHelper.getMathContext()`.
  The runner asserts the echo matches the ordinal.
- The oracle's own SLF4J `Initialized rounding mode for tenant …` lines are kept
  (`out/t42-mathcontext-log.txt`, 201 lines; `out/t42-mathcontext2-log.txt`, 140 lines).
- **What this reading IS evidence of:** that the tenant was configured as intended, and — on the
  **Path B wiring only** — of the arithmetic, because there the caller sources the threaded
  context *from* this one (§2.3).
- **What it is NOT evidence of:** the arithmetic on the Path A wiring. Observed: moving it moves
  **nothing** on 11 of 13 probe shapes, and on those shapes the absence probe proves it was never
  read at all.

### 2.3 The wiring, read off the DEPLOYED bytecode of the running server

`out/t42-pathb-wiring.txt`, `javap -p -c` inside `fineract-fineract-1`, class file sha256
`d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea`:

```
LoanScheduleAssembler.assembleLoanScheduleFrom(...)
   31: invokestatic  MoneyHelper.getMathContext:()Ljava/math/MathContext;
   34: astore        9
  ...
  107: aload         11          // the LoanScheduleGenerator
  109: aload         9           // <-- THE SAME LOCAL SLOT
  111: aload_1
  112: aload         7
  114: aload         10
  116: invokeinterface LoanScheduleGenerator.generate:(Ljava/math/MathContext;...)
```

Four `MoneyHelper.getMathContext` call sites in the two classes that build a schedule on Path B.
**On Path B the threaded context IS the ambient one — the same object reference.**
[VERIFIED: `out/t42-pathb-wiring.txt`; source counterpart `LoanScheduleAssembler.java:753`, `:765`,
`:777`, `:797`, `LoanScheduleGeneratorServiceImpl.java:44`]

> **CORRECTION — M-6. This section's only shipped machine assertion was
> `grep -c 'MoneyHelper.getMathContext' != 0`** (`src/read-pathb-wiring.sh`, the `N_GMC` check).
> The same-local-slot claim — the content of ratified rule 4 — was left to the reader ("Read the
> dataflow yourself in the transcript"), unasserted and with no negative leg.
>
> **T46 closed it.** `analysis/t46_assert_pathb_slot.py` asserts, off the `javap` transcript:
> **A1** the instruction after `invokestatic MoneyHelper.getMathContext` is `astore <slot>`;
> **A2** that slot is later `aload`ed into an `invoke*` whose descriptor takes a `MathContext`;
> **A3** the slot is not re-assigned in between. `src/t46-assert-pathb-slot.sh` runs it against
> the committed transcript **and against a fresh read-only `javap` re-read of the running
> server**, then runs it again against a **slot-drifted** copy, which it must reject.
> Result: **PASS on both real transcripts, FAIL (6 breaches) on the drifted one**
> [VERIFIED: `analysis/t46-pathb-slot-assertion-output.txt`].
>
> The re-read confirms the deployed digests independently, 20 hours after T42 took them:
> jar `60fb6dbd631d…f4c9`, `LoanScheduleAssembler.class`
> `d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea` — the same digest T42 and
> the T44 audit each recorded — and, newly recorded,
> `LoanScheduleGeneratorServiceImpl.class` sha256
> `eca9b7d9010722e19c90bfd84c29cba9e3352adc0b460020b0df96608d1e31d6`
> [VERIFIED: `out/t46-pathb-wiring-reread.txt`].
>
> **CORRECTION — M-9. "…and pass it to `generate(mc, …)`" is wrong for 2 of the 4 sites.**
> Machine-extracted from the deployed bytecode, and re-read in the pinned source:
>
> | site | what it actually does with the `MathContext` |
> |---|---|
> | `LoanScheduleAssembler.java:753` (slot 9) | `updateInterestForEqualAmortization(mc, …)` at `:758`, **and** `loanScheduleGenerator.generate(mc, …)` at `:765` — the claim holds |
> | `LoanScheduleAssembler.java:777` (slot 6) | `loanScheduleGenerator.rescheduleNextInstallments(mc, …)` at `:787-788` — **not `generate`** |
> | `LoanScheduleAssembler.java:797` (slot 8) | `loanScheduleGenerator.calculatePrepaymentAmount(currency, onDate, terms, mc, …)` at `:805-806` — **not `generate`, and `mc` is the 4th argument, not the 1st** |
> | `LoanScheduleGeneratorServiceImpl.java:44` (slot 2) | `scheduleGenerator.generate(mc, modelData)` at `:63` — the claim holds |
>
> [VERIFIED: `analysis/t46-pathb-slot-assertion-output.txt` for the bytecode; the pinned source
> lines re-opened by T46 in `/Users/buv/fineract`]. The *substance* of rule 4 is unaffected —
> on every one of the four the threaded context is the ambient object — but the wiring row must
> name what each caller invokes, not assume they all invoke `generate`.

### 2.4 The one place on Path A where the ambient IS read

Observed, with the exact line named by the oracle's own stack trace:

```
java.lang.IllegalStateException: Rounding mode is not initialized for tenant: t42_t42_mx_07_d
  at MoneyHelper.getRoundingMode(MoneyHelper.java:79)
  at Money.roundToMultiplesOf(Money.java:154)
  at Money.<init>(Money.java:50)
  at Money.of(Money.java:107)                     <-- the THREE-argument of(), mc WAS supplied
  at LoanApplicationTerms.assembleFrom(LoanApplicationTerms.java:580)
  at ProgressiveLoanScheduleGenerator.generate(ProgressiveLoanScheduleGenerator.java:82)
```

Reached only when `currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 &&
inMultiplesOf > 0` [`Money.java:48-50` — **corrected by T46, audit finding M-9; the original cited
`:49-51`**. Re-opened in the pinned checkout: the `if` opens at `:48`, its second line is `:49`,
and the guarded `roundToMultiplesOf(amountScaled, currency.getInMultiplesOf())` call is `:50`].
MNT has **2** decimal places, so the ratified MNT configuration never reaches it.

The two-argument `roundToMultiplesOf(BigDecimal, Integer)` that the trace names is
`Money.java:150-157` (**corrected by T46 from `:152-158`**); the three-argument
`roundToMultiplesOf(Money, Integer, MathContext)` is `Money.java:163-170` (**corrected from
`:161-171`**; `:159-161` is the two-argument `Money` overload). The stack-trace line numbers
themselves — `Money.java:154`, `:50`, `:107` — were and remain correct.

### 2.5 What the E1 matrix did NOT reach — corrected by T46 (findings M-3 and M-4)

`src/CaptureMathContext.java`'s comment on `ambientProbeShapes()` claimed the thirteen shapes
*"between them REACH every ambient-context read the static scan found on the Path A call graph"*,
and justified the `installmentAmountInMultiplesOf` shape as the one reaching the three-argument
`Money.roundToMultiplesOf` and its trailing two-argument `Money.of`. **That site was never
reached, and the claim is withdrawn.** The source comments are corrected in place.

**Observed, from the committed payload alone**
[VERIFIED: `analysis/t46_distinct_coverage-output.txt`, produced by
`analysis/t46_distinct_coverage.py` with `json.load(..., parse_float=Decimal)` and exact-text
cell comparison]:

- `T42-MX-00-A` (plain) and `T42-MX-06-A` (`multiples1000`) differ in exactly one substantive
  input — `installmentAmountInMultiplesOf` `null` → `1000` — plus the per-case `tenantId` the
  harness assigns to every case. Their observations differ in **0 of 74 cells**.
- Period-1 `total` is `212787.28` on both, **not** a multiple of 1000.
- The absence case `T42-MX-06-D` **generated a schedule** rather than throwing. It could not have,
  had the three-argument helper run: that helper finishes with the two-argument
  `Money.of(currencyData, amountScaled)` [`Money.java:169` → `:102-104`], which calls
  `MoneyHelper.getMathContext()` and would have thrown on the uninitialised tenant.
- **Four** of the thirteen `-A` observations are byte-identical to `plain` — `plain`,
  `multiples1000`, `fixedLength6`, `interestRecognitionOnDisb` — so **distinct coverage of the
  E1 matrix is 10, not 13**, and three of the levers chosen to widen coverage moved nothing.

**Cause, re-read on the pinned checkout by T46:**
`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
[`fineract-loan/.../LoanApplicationTerms.java:579-607`] never calls the builder's
`installmentAmountInMultiplesOf` setter, although `LoanRepaymentScheduleModelData` carries the
field [`LoanRepaymentScheduleModelData.java:36`]. So on the Path A seam
`ProgressiveLoanScheduleGenerator.java:110` and the guard at `:335` both see `null`.

**M-4 — a second PRODUCTION caller drops it too.** This is not only a harness blind spot.
[VERIFIED by T46 by re-opening both files in `/Users/buv/fineract`, commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean]:

- `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` — the
  multi-disbursement interest-only entry point — passes
  `loanProductRelatedDetail.getInstallmentAmountInMultiplesOf()` into the
  `LoanRepaymentScheduleModelData` at **`:56`** and calls `scheduleGenerator.generate(mc, modelData)`
  at **`:63`**; `assembleFrom` then drops the field. **So this production path silently loses it.**
- The REST `calculateLoanSchedule` path via `LoanScheduleAssembler` **does honour it** — capture
  `B-02`, `112,082.37 → 112,100.00`. Nothing here disturbs that observation.

**So the field is honoured or lost BY CALLER**, and DEC-1 must not state its behaviour
unconditionally.

**Added to the blind-spot list** (`PROVENANCE.md`): the `installmentAmountInMultiplesOf` ambient
path — three-argument `Money.roundToMultiplesOf` [`Money.java:163-170`] plus its trailing
two-argument `Money.of` [`Money.java:169` → `:102-104`] — is **`TO_BE_CAPTURED`**, and cannot be
reached through `LoanRepaymentScheduleModelData` at all.

### 2.6 T46's re-emission — the M-5 fix, proved rather than argued

`src/CaptureMathContext3.java` (generated from `src/CaptureMathContext.java` by
`analysis/t46_make_capture3.py`; four mechanical edits, no arithmetic touched) re-runs capture 1
in a throwaway `docker run --rm` container on the same pinned image and adds four keys per case,
**read off the `mc` reference actually handed to `generate(mc, config)`**:
`threadedMathContext` (`mc.toString()`), `threadedMathContextPrecisionFromObject`,
`threadedMathContextRoundingModeFromObject`, and an explicit `wiring` field. The two original
keys are left in place, so nothing published is replaced.

`analysis/t46_m5_identity.py` then compares the two payloads leaf by leaf, exact text, no float
[VERIFIED: `analysis/t46-m5-identity-proof.txt`]:

| | |
|---|---|
| cases | 214 committed, 214 re-emitted, 214 common |
| previously published leaves compared | **147,634** |
| leaves that MOVED | **0** |
| leaves EXEMPT and enumerated verbatim in the proof | **4** — the harness's *own* `CaptureMathContext.run`/`.main` frames inside the two absence stack traces. Every **oracle** frame (`MoneyHelper.getRoundingMode`, `Money.roundToMultiplesOf`, `Money.<init>`, `Money.of`, `LoanApplicationTerms.assembleFrom`, `ProgressiveLoanScheduleGenerator.generate`) is byte-identical. A re-emission by a differently-named class cannot reproduce its own frames, and they carry no information about the oracle. |
| leaves byte-identical | **147,630** |
| keys added | **856** |
| **cases where the OBJECT echo disagrees with the INTENT** | **0 of 214** |

That last row is the substance: M-5's materiality is now **observed**, not argued — no value in
capture 1 was ever mis-attested, only mis-named. The identity check is proved failable: negative
leg **N9** perturbs one money cell by one minor unit (`T42-CAL` period-1 `interest`
`0.58 → 0.59`) and the check exits 1 naming that cell
[`out/negative/t46-n9-identity-check-failable.txt`].

**`out/t46-mathcontext3.json` does not replace `out/t42-mathcontext.json`.** Both are kept; the
committed T42 payload remains the record of what T42 observed.

### 2.7 The qualification that must travel with "no committed capture is mis-valued"

**CORRECTION — M-7.** T42's verdict states *"No committed capture is mis-valued"* flatly, and
`.softhouse/reference-oracle.md` has folded it in that way, while T42 §7 qualifies it correctly.
**The qualification is part of the claim and must be carried wherever it is stated:**

> `[VERIFIED for the three legs stated in T42 §4; UNVERIFIED as a re-run — T35's and T36's
> suites were not re-executed.]`

And leg 1 specifically is weaker than the other two: it is a **self-report**, citing T35's,
T37's and T39's own attestations that they echoed the threaded context — the exact class of
evidence T42 refuses elsewhere. Audit findings **F39-3** and **M-5** show that self-report is
inaccurate for at least T39 and for T42's own capture 1, both of which echoed **intent** under
object-named keys. **Legs 2 and 3 do carry the conclusion** — the Path A ambient site is
unreachable at 2 dp, proved by observation and by the source predicate, and every committed
Path A capture uses a 2-dp currency — so the conclusion stands on those two. T46 adds a fourth,
independent leg for capture 1 itself: the object/intent agreement proved in §2.6.

## 3. Controls — 172 cells, all reproduce

`analysis/controls.py`, exit 0. Every expectation **transcribed** with `file:line`, never computed.

| control | expectation transcribed from | result |
|---|---|---|
| **C1** `T42-CAL`, USD 100 / 6 × 7.0 % at threaded `(12, HALF_UP)` | the shipped Fineract test literal `EmbeddableProgressiveLoanScheduleGeneratorTest.java:44` (MathContext), `:74-77` (totals), `:79-95` (rows) — 61 cells | **reproduced digit for digit** |
| **C2** `T42-CTL-Q0a` | committed observation **Q0a**; also T37-CTL-Q0a and T39-CTL-Q0a | **reproduced** |
| **C3** `T42-CTL-1` | committed capture **T37-3-A** / **T39-CTL-1** | **reproduced** |
| **C4** `T42-CTL-P0A` — full 6×9 period table | committed capture **T39-P0-A**, `.softhouse/handoff/T39-periodratio-observation.md` §2 | **reproduced digit for digit** |
| **C5** `T42-CTL-MEB` — full period table | committed capture **T39-ME-B**, same handoff §2 | **reproduced digit for digit** |

Four of the five reproduce records taken by **different harnesses on different tasks**, so the
harness is not the variable. The control suite is proved failable (`NEGATIVE-TESTS.md` N6).

> **CORRECTION — M-11. `analysis/controls-output.txt` publishes two summary lines, not the 172
> compared cells**, so the control claim could not be checked from committed output alone.
>
> **T46 closed it, without changing the default output by one byte.** In order:
> 1. `analysis/controls.py` was **re-run unmodified**: output sha256
>    `4b847fc97fc5545bd0913f40ae50408a948101891f6b921b83e0c372d4988e1c`, **identical** to the
>    committed `analysis/controls-output.txt`.
> 2. An **append-only** verbose mode was added — `T42_CONTROLS_VERBOSE=1` or `--verbose` — which
>    prints every compared cell as `control-id | field | expected | observed | MATCH`.
> 3. The default mode was re-run: output sha256 **`4b847fc9…72548d` again**, byte-identical to
>    both the committed file and the pre-change re-run.
> 4. The verbose run is published as **`analysis/t46-controls-cells-output.txt`**: 179 lines,
>    **172 cells listed, 172 MATCH, 0 MISMATCH**, then the unchanged two-line summary.
>
> The control claim is now checkable cell by cell from committed output.

## 4. Determinism

Both captures were re-run from fresh containers and both payloads are **byte-identical**
(`diff` clean):

- `t42-mathcontext.json` sha256 `f2a037a10b8d6a74e6b3dd5eedbaa18ad5fe34cab0f36f6a69cba47373206553`
- `t42-mathcontext2.json` sha256 `f7ffeb2a519e076d2483195ea359bc5ac5fa433d8da0f610cc3abded309c6b84`

## 5. Failability

Six negative legs, all exit 1 naming the breach — wrong pin, wrong image id, seam-class drift,
the absence probe's own guard inverted, the wiring broken, and a corrupted control payload.
`NEGATIVE-TESTS.md`.

> **CORRECTION — M-8, and three legs added by T46.** `NEGATIVE-TESTS.md` said leg **N4** fires
> the *"the ambient-absence probe is VACUOUS"* guard. **It fires the opposite branch of the same
> `if`.** N4 sets `T42_EXPECT_CANARY_THROWS=0`, so `must_throw` is `False` and the branch that
> runs is *"negative run: the canary DID throw when the run asserted it would not"*
> [`src/run-mathcontext.sh:161-162`]. **The vacuity guard itself — `:157-160`, the guard that
> makes E1 falsifiable — had never been exercised.**
>
> Three legs now exist that did not before:
>
> | leg | what it exercises | result |
> |---|---|---|
> | **N7** `src/t46-negative-vacuity.sh` | the **vacuity guard**, by extracting the SHIPPED assertion block out of `run-mathcontext.sh` at run time and running it against a payload whose `ambientCanary` has been rewritten from a `THREW …` string to `precision=19 roundingMode=HALF_UP`, with `must_throw` left at 1 | **exit 1**, `BREACH: the ambient-absence probe is VACUOUS: … returned 'precision=19 roundingMode=HALF_UP' …`; the same block on the **uncorrupted** payload exits 0, so the guard discriminates. 140,978 observed cells proved identical between the two payloads — the corruption touched only the canary field. `out/negative/t46-n7-vacuity-guard.txt` |
> | **N8** `src/t46-assert-pathb-slot.sh` | the **Path B slot assertion** (M-6), against a slot-drifted `javap` transcript | **exit 1**, 6 breaches; PASS on both the committed transcript and a fresh re-read. `analysis/t46-pathb-slot-assertion-output.txt` |
> | **N9** `src/t46-negative-identity.sh` | the **M-5 identity check**, against a re-emission with one money cell moved by one minor unit | **exit 1** naming `T42-CAL /observed/periods[1]/interest: '0.58' -> '0.59'`; exit 0 on the real pair. `out/negative/t46-n9-identity-check-failable.txt` |
>
> A tenth artefact, `out/negative/t46-n8-identity-check-rejects.txt`, is kept deliberately: it is
> the transcript of the **first** re-emission run, which the identity check **rejected** before
> the harness-self-frame carve-out was written and justified. It is evidence that the check was
> refusing to publish, not rubber-stamping.

## 6. Scale of the comparison

`analysis/count_cells.py`:

| comparison | cells |
|---|---|
| (a) the ambient/threaded matrix, capture 1 | **3,820** (plus 2 cases that threw — the absence result) |
| (a) the wiring comparison, capture 2 | **1,284** |
| (b) precision sweep, capture 1 (48 shapes × {19v12, 19v8}) | **90,528** |
| (b) precision sweep, capture 2 (62 shapes × 19v12) | **147,676** |
| **total** | **243,308** |

**FULL-CELL comparison** throughout: the four plan totals plus every column of every period row —
`fromDate`, `dueDate`, `principal`, `interest`, `fee`, `penalty`, `balance`, `total`,
`totalOutstandingBalance`, plus `loanTermInDays`. Never the three headline scalars; that shape is
what let defect F-1 hide through five reviews (`.softhouse/patterns.md`).

## 7. No float, integer minor units

`BigDecimal.toPlainString()` in both harnesses; exact **string** comparison in every analysis
script; no `double`, `float` or `doubleValue()` on any amount path. The shipped test literal
asserts Java `double`s, so `controls.py` transcribes them as the decimal **strings** the oracle
emits (`2.05`, `0.00`, `16.43`) rather than parsing them as floats.

## 8. Containers

Ten throwaway `docker run --rm`, mounting only `.softhouse/capture/mathcontext` (`run-mathcontext.sh` starts two per run — an identity container and a capture container — and ran three times: the capture, the determinism re-run and negative leg N4; `run-mathcontext2.sh` starts one per run and ran four times: the first capture, the widened capture, the determinism re-run and negative leg N5. Legs N1, N2 and N3 fail before any container is started, by design.)
`fineract-fineract-1` and `fineract-db-1` were **not** started, stopped, restarted, re-tenanted,
reconfigured, dropped or written to. `read-pathb-wiring.sh` does `docker exec` into the running
`fineract-fineract-1` to run `javap` and `unzip` into its `/tmp`; it opens no database connection
and changes no server state.

## 9. sha256 of every artefact

```
4b847fc97fc5545bd0913f40ae50408a948101891f6b921b83e0c372d4988e1c  analysis/controls-output.txt
e82aecfe130737cd1d722ec22e793a86f2fc8a6b6a5d2635daa75715ec72548d  analysis/controls.py
0a5d53e4713b061cfa48926a1f329f45f67fa0a520b1a9f86e1ac8d868ceeb08  analysis/discriminate-output.txt
83894a27c19b23b9c2e94c314b97331f7c6e5912d734dc0baeb15566a3809e17  analysis/discriminate.py
05fc6da79284b3f1bb998503899fcc49f23fc6f508f23eb1ba70be57e94a39d3  analysis/discriminate2-output.txt
b01ead7c740f1046e4835bf41c0ae4bbc03bb07ec02e7d736fd6dea258624bc7  analysis/discriminate2.py
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t42-determinism-classpath.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t42-determinism-oracle-identity.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t42-determinism-stderr.txt
f2a037a10b8d6a74e6b3dd5eedbaa18ad5fe34cab0f36f6a69cba47373206553  out/t42-determinism.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t42-determinism2-classpath.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t42-determinism2-stderr.txt
f7ffeb2a519e076d2483195ea359bc5ac5fa433d8da0f610cc3abded309c6b84  out/t42-determinism2.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t42-mathcontext-classpath.txt
8fd1cae1a90ba6ad2c8be8dbf62293091f9b024432b63c8f4dbf9747194a4fb0  out/t42-mathcontext-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t42-mathcontext-oracle-identity.txt
273f3d0fc1b5cc897f385cd03364adae93ec017411049c66c611361635d4d2ef  out/t42-mathcontext-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t42-mathcontext-stderr.txt
f2a037a10b8d6a74e6b3dd5eedbaa18ad5fe34cab0f36f6a69cba47373206553  out/t42-mathcontext.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t42-mathcontext2-classpath.txt
cfd2e59234b8cf187a41513e5f84f21815f0003cffb3096bc9855a34115038a7  out/t42-mathcontext2-log.txt
27bc6a4485a1086642effe87acb4ec8c18548256619ff19d361da5ee33e83651  out/t42-mathcontext2-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t42-mathcontext2-stderr.txt
f7ffeb2a519e076d2483195ea359bc5ac5fa433d8da0f610cc3abded309c6b84  out/t42-mathcontext2.json
6faaedc657bfcbe09444d0c7527aa51f6e204d032ee6ab3a517824b2c10415b3  out/t42-pathb-wiring.txt
c89366e75db269b8c120b473918ae6edcbbebb337ed52eec66f9bb66cf5d54be  src/CaptureMathContext.java
aaf3bfbc1f8297673b9010a9e5667586b3ea6b8840118ba69acc65f0b8055fb4  src/CaptureMathContext2.java
bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714  src/EmbeddableProgressiveLoanScheduleGenerator.java
2928577a82c7fa8dc73e3471047fa9ee8d034c5cf5413163ad5f60f3eae87bc8  src/read-pathb-wiring.sh
04cbe868d8135fc5a7f1be4c28f201aecbc96443a3e2bd97713d113a51aa97f6  src/run-mathcontext.sh
a4f66f3c18502a1e09fe5091e151f938c88ba031892100c04a2ff4e5c56a9802  src/run-mathcontext2.sh
0cb1fa7f266f2c85b0f0060e4687ed7491ae8a030b4384fa5e974a0c05d55efe  src/run-negative-tests.sh
```

`out/t42-neg4.json` has the **same** digest as `t42-mathcontext.json` — expected: N4 only inverted
an assertion, so the payload it produced is identical and only the verdict differs. The
`count_cells.py` / `count_cells-output.txt` digests are omitted here because they were produced
after this table was written; re-run the `find … | xargs shasum` command in `REPRODUCE.md` for
the current full list.
