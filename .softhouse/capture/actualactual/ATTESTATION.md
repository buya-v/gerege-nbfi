# T48 — attestation, under the eight-point rule in `.softhouse/reference-oracle.md`

That rule was **corrected twice this fire** (T42's original list, then T46's additions). This
attestation follows the corrected version, and in particular does **not** repeat the "two independent
witnesses that are both ambient" defect found in **T37** *and* **T39**.

---

## 1. The two contexts, named separately

* **THREADED** — the `MathContext` object actually passed to the arithmetic.
* **AMBIENT** — `MoneyHelper.getMathContext()` for the current tenant.

They are never conflated below and never counted as two witnesses of one thing.

## 2. The THREADED context is echoed **off the object**, not as intent

`CaptureActualActual.threadedEcho(mc, wiring)` emits `mc.toString()`, `mc.getPrecision()` and
`mc.getRoundingMode()` **read off the reference handed to the callee**, under
`threadedMathContext` / `threadedMathContextPrecision` / `threadedMathContextRoundingMode`. The case
record's *intent* fields are emitted separately and `run-actualactual.sh` **fails the run** if intent and
object ever disagree — so a drift between what the harness meant and what the oracle got is a breach,
not a silent pass.

Observed on every non-calibration capture: `precision=19 roundingMode=HALF_UP`, precision `19`, mode
`HALF_UP`. On the calibration captures: precision `12`, mode `HALF_UP` (embeddable-seam literal) or
`HALF_EVEN` (`ProgressiveEMICalculatorTest` literals).

## 3. The AMBIENT context — what it witnesses, and what it does not

Ambient reads `precision=19 roundingMode=HALF_UP` on every non-calibration capture (and
`precision=19 roundingMode=HALF_EVEN` on the `S1`…`S5` calibrations, whose tenant ordinal is 6).

It witnesses **that the tenant was configured as ratified**. On Path A and Path A2 it is **not** evidence
about the arithmetic, because both seams construct their own `MathContext` and thread it; the two are
independent variables. Every capture carries `"ambientIsNotTheArithmeticHere": true` for exactly that
reason.

**One witness, counted once.** The oracle's SLF4J line
`Initialized rounding mode for tenant '<id>': HALF_UP` is emitted by `MoneyHelper` from **the same local
it writes into `roundingModeCache`** [VERIFIED: `MoneyHelper.java:59-64`], which `:74-82` then reads back.
The log line and `MoneyHelper.getMathContext()` are therefore **one ambient witness observed twice**, not
two independent witnesses. `run-actualactual.sh` prints it labelled `AMBIENT witness (one, not two)`.

## 4. The WIRING, stated explicitly, per path

| path | wiring | is the ambient reading evidence about the money? |
|---|---|---|
| **Path A** | the harness's own `mc` object is the argument of `EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)` [VERIFIED: seam class `:44-46`], which forwards **the same object** to `ProgressiveLoanScheduleGenerator.generate(mc, modelData)`, which reaches the calculator as `generatePeriodInterestScheduleModel(..., mc)` [VERIFIED: `ProgressiveLoanScheduleGenerator.java:108-109`]. | **No.** Independent of the ambient. |
| **Path A2** | the harness's own `mc` object is the 4th argument of `ProgressiveEMICalculator.generatePeriodInterestScheduleModel(periods, detail, null, mc)` and is stored on the returned `ProgressiveLoanInterestScheduleModel`, which `calculateRateFactorPerPeriod` reads back as `scheduleModel.mc()` [VERIFIED: `ProgressiveEMICalculator.java:1487`]. | **No.** Independent of the ambient. |
| **Path B** | `LoanScheduleAssembler.java:753` and `LoanScheduleGeneratorServiceImpl.java:44` do `mc = MoneyHelper.getMathContext()` and pass **that same object** to `generate(mc, …)`. | **Yes — it *is* the threaded context.** Wiring cited, never left implicit. |

## 5. The ambient leaks — **there are two known, and this is an enumeration, not an exhaustiveness claim**

`reference-oracle.md`'s own note applies: the enumeration of ambient leaks has been wrong **twice**
(T43 P1-T43-2, and T46's N46-1), which is the argument for not resting a conclusion on it.

1. **The 0-dp `inMultiplesOf` leak.** `Money.<init>` [`Money.java:50`] → `roundToMultiplesOf(BigDecimal,
   Integer)` [`Money.java:154`] → `MoneyHelper.getRoundingMode()` [`MoneyHelper.java:79`], ignoring the
   `mc` it was handed. Reached only when the currency has **0 decimal places** *and* a positive
   `inMultiplesOf`. **MNT has 2**, so no MNT capture in this pass reaches it. The USD calibration cases
   run at `inMultiplesOf = 1` but still at 2 decimal places, so it stays shut there too.
2. **The CHARGE rounding leak (T46 N46-1), reachable at MNT's 2 decimal places.**
   `ProgressiveLoanScheduleGenerator.java:445-446` → the two-arg `Money.of` → `Money.java:114-116` →
   `Money.java:52` `setScale(2, getMc().getRoundingMode())`. **No capture in
   `.softhouse/capture/actualactual/` carries a charge**, so this pass does not reach it either — but the
   T48 charge pass under `.softhouse/capture/charges/out/t48/` **does** carry charges, and its rounding
   mode is therefore ambient. It is still `TO_BE_CAPTURED`: separating ambient from threaded there
   requires a **tenant write on the shared server**, which this task is forbidden to make. **N46-1 was
   deliberately not attempted.**

## 6. A behavioural canary, not a configuration echo

* **Path B** — the T36 half-cent tie (`1,162,502.50 × 0.018 = 20,925.045` → `20925.05` under `HALF_UP`,
  `20925.04` under `HALF_EVEN`) is asserted by `preconditions.sh` before **every** Path B post in this
  task, and passed every time [`pathb/out/preconditions.txt`, `charges/out/t48/preconditions.txt`].
  That is the arithmetic itself answering `HALF_UP`, not a row in `c_configuration`.
* **Path A / Path A2** — the canary is the **threaded** negative leg: `negative-tests.sh` N5 forces the
  threaded mode to `HALF_EVEN` and N6 forces the precision to 12, and the recipe **exits 1 naming the
  breach** in both. A suite that has never failed has not been tested; this one has, on **8 axes**.

## 7. Precision 19 is a provenance claim here, and is labelled as one

`MoneyHelper.PRECISION = 19` is a compile-time constant [VERIFIED: `MoneyHelper.java:35`], so echoing it
is provenance, not discrimination. **No capture in this pass separates threaded precision 19 from 12** —
T39's separating shape (50 M / 360 months) is not in this set. Stated so that "attested" does not read as
"witnessed". `TO_BE_CAPTURED` for this arm specifically.

## 8. `(19, tenant mode)` is the LOAN-PATH rule

Every capture in this pass is on the loan path, so the rule applies. It is **not** a Fineract-wide rule —
see `reference-oracle.md`'s corrected N-3 inventory (81 `MathContext.DECIMAL64` uses, 9 explicit
`new MathContext(…)` sites, and `ShareAccountCharge.java:240` in **share accounts**, not savings).

---

## Determinism

| set | first run | fresh-container re-run | result |
|---|---|---|---|
| `seam` | `out/t48-seam.json` | `out/t48det-seam.json` | **byte-identical** |
| `calc` | `out/t48-calc.json` | `out/t48det-calc.json` | **byte-identical** |
| `exact` | `out/t48-exact.json` | `out/t48det-exact.json` | **byte-identical** |
| Path B (13 captures) | `pathb/out/*-raw.json` | re-posted verbatim | **byte-identical, 13 of 13** |
| Path B charges (19 captures) | `charges/out/t48/*-raw.json` | `charges/out/t48-rerun/` | **byte-identical, 19 of 19** |

Each Path A / A2 re-run built a **new** `docker run --rm` container from the pinned image and recompiled
the harness from source inside it. Only the log's wall-clock timestamps differ between runs, and those
are split off into `*-log.txt` and are not part of the payload.

## Digests

`find . -type f | sort | xargs shasum -a 256` over `.softhouse/capture/actualactual/` — headline entries:

```
2c46cb06f57ba7ca27328fc89bb9aad5a8a84486d716d4f665ad8867da324eed  ./out/t48-seam.json
91daa0f15e4fe03ea8f36ddda29d152f9b93822be1a0d33a6d6191da1f19188d  ./out/t48-calc.json
777f0daa2539e8696305cbd1ab493d6b007ffa07d986358820b989d14df41287  ./out/t48-exact.json
bdf711ec0011c5eda8ef1785516e91ad63f218583ecb766c6b705d2e9d290cd2  ./src/CaptureActualActual.java
bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714  ./src/EmbeddableProgressiveLoanScheduleGenerator.java   (== the pinned original)
7094ef51c36470ae081f71c4e39305e6559e0f87931aedeff799d23f3dc0fbd2  ./src/run-actualactual.sh
bd2efd944a724cdba2cc3d30e9ce6c0e11c4d9803f27aa72dd59953ec63a566a  ./src/negative-tests.sh
e1a8b73f1443046b6f1247d4f49b38d6e729709bd3c58b77e2719bb7b27e6fc1  ./src/pathb-capture.sh
```

Regenerate the full list with:

```sh
cd .softhouse/capture/actualactual && find . -type f | sort | xargs shasum -a 256
```
