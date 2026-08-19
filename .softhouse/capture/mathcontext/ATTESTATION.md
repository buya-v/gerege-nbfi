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
inMultiplesOf > 0` [`Money.java:49-51`]. MNT has **2** decimal places, so the ratified MNT
configuration never reaches it.

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

## 4. Determinism

Both captures were re-run from fresh containers and both payloads are **byte-identical**
(`diff` clean):

- `t42-mathcontext.json` sha256 `f2a037a10b8d6a74e6b3dd5eedbaa18ad5fe34cab0f36f6a69cba47373206553`
- `t42-mathcontext2.json` sha256 `f7ffeb2a519e076d2483195ea359bc5ac5fa433d8da0f610cc3abded309c6b84`

## 5. Failability

Six negative legs, all exit 1 naming the breach — wrong pin, wrong image id, seam-class drift,
the absence probe's own guard inverted, the wiring broken, and a corrupted control payload.
`NEGATIVE-TESTS.md`.

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
