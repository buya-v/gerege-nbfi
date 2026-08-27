# T44 — independent audit of `.softhouse/capture/mathcontext/` (task T42)

**Verdict: ACCEPTED WITH REQUIRED CHANGES.**

Every headline result of T42 reproduces under independent re-execution and independent
recomputation. Both payloads are byte-deterministic from fresh throwaway containers; every cell
count, every separating-shape figure and every observed money value in the handoff is either
observed or transcribable to a `file:line` that says what T42 says it says. The defects are:
**two wrong numbers and one false universal in finding N-3** (which has already been ratified into
`.softhouse/reference-oracle.md`), **one observation-tagged claim that was never observed**
(N-1's second half), **a probe-shape coverage rationale that the observations refute**, and a
cluster of attestation-discipline points where T42 does not meet the rule T42 itself authored.

**No committed capture value is invalidated by anything in this audit.** T42's substantive
conclusions — the ambient context is provably never read on the Path A seam at 2 dp, the two
contexts are the same object on Path B, and threaded precision 19 separates from 12 on an
ordinary retail loan — all stand.

Write surface used: `.softhouse/capture/audit-t44/mathcontext/` only. Nothing under
`.softhouse/capture/mathcontext/**` was modified (verified: it is byte-identical to the committed
tree; my re-runs wrote only into my own `out/`). No commit made.

---

## 1. What I re-ran, and what it showed

All commands were run from `/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/mathcontext`.
Transcripts are in `out/`; scripts and their outputs are in `analysis/`.

### 1.1 Byte-for-byte re-execution against the live reference oracle (Fineract)

`src/` was copied into my own directory and `diff -r` proved the copy byte-identical
(`DIFF-CLEAN`), including the seam class at sha256
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`.

| run | command | result |
|---|---|---|
| capture 1 | `T42_OUT_PREFIX=audit-rerun1 bash ./src/run-mathcontext.sh` | `== PASS`, exit 0; payload sha256 **`f2a037a10b8d6a74e6b3dd5eedbaa18ad5fe34cab0f36f6a69cba47373206553`** — **byte-identical** to the committed `t42-mathcontext.json` (`diff -q` silent) |
| capture 2 | `T42_OUT_PREFIX=audit-rerun2 bash ./src/run-mathcontext2.sh` | `== PASS`, exit 0; payload sha256 **`f7ffeb2a519e076d2483195ea359bc5ac5fa433d8da0f610cc3abded309c6b84`** — **byte-identical** to the committed `t42-mathcontext2.json` |

Both re-runs independently reproduced: 348 classpath entries at digest
`68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f`, zero prohibited Oracle
Database / MySQL / MariaDB entries (and `postgresql-42.7.11.jar` present), 0-byte stderr, the
pinned commit `426a23544e8426a38ae43ae404670a0a7e85b9eb` clean, image
`sha256:e596339626bf…0459a`, and the canary
`THREW java.lang.IllegalStateException: Rounding mode is not initialized for tenant: t42_canary_never_initialised`.
[VERIFIED: `out/AUDIT-rerun1-console.txt`, `out/AUDIT-rerun2-console.txt`, `DIGESTS-before-prune.txt`]

Throwaway `docker run --rm` only, mounting my own directory. `fineract-fineract-1` and
`fineract-db-1` were never started, stopped, restarted, re-tenanted, reconfigured or written to;
the only contact with them was read-only `docker exec` (`unzip` into `/tmp`, `javap`, `sha256sum`).

### 1.2 Failability — the two central negative legs, re-run

| leg | command | result |
|---|---|---|
| **N4** (the absence probe's guard) | `T42_EXPECT_CANARY_THROWS=0 … run-mathcontext.sh` | **exit 1**, `BREACH: negative run: the canary DID throw when the run asserted it would not: 'THREW java.lang.IllegalStateException: …'` |
| **N5** (the wiring assertion) | `T42_JAVA_PROPS=-Dt42.breakWiring=true … run-mathcontext2.sh` | **exit 1**, six breaches, first `BREACH: T42B-PB-ord1: PATH B wiring must hand the generator the AMBIENT context; ambient 'precision=19 roundingMode=DOWN' but effective 'precision=19 roundingMode=HALF_UP'` |

[VERIFIED: `out/AUDIT-neg4.txt`, `out/AUDIT-neg5.txt`]

### 1.3 The Path B wiring, re-read off the deployed bytecode myself

`docker exec -e JAVA_TOOL_OPTIONS= fineract-fineract-1 … javap -p -c` on the class extracted from
`/app/fineract-provider.jar` in the running server:

- jar sha256 `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9` ✔
- `LoanScheduleAssembler.class` sha256
  **`d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea`** ✔ (T42's digest, reproduced)
- `assembleLoanScheduleFrom`: `31: invokestatic MoneyHelper.getMathContext` → `34: astore 9` …
  `109: aload 9` → `116: invokeinterface LoanScheduleGenerator.generate:(Ljava/math/MathContext;…)`
  — **the same local slot 9**. ✔ T42's claim reproduced exactly.
- Also confirmed, which T42 did not spell out: `assembleForInterestRecalculation`
  (`0: getMathContext → 3: astore 6 … 83: aload 6 → 93: rescheduleNextInstallments(mc,…)`) and
  `calculatePrepaymentAmount` (`19: getMathContext → 22: astore 8`) thread the ambient object too;
  the second `generate` site (in `updateInterestForEqualAmortization`) receives slot 9 as its own
  parameter. Three `getMathContext` sites in `LoanScheduleAssembler` + one in
  `LoanScheduleGeneratorServiceImpl` = the "four call sites" T42 claims. ✔

[VERIFIED: `out/AUDIT-javap-assembler.txt`, `out/AUDIT-javap-digests.txt`]

### 1.4 Independent recomputation (`analysis/audit_recompute.py`)

Written from the definitions, exact `Decimal`, `parse_float=Decimal`, exact-string cell comparison,
**no float anywhere**. `discriminate*.py` was neither imported nor copied.

**Everything reproduces.** Every cell in T42's E1 13-shape table (23/22/23/20/24/24/23/[23 ambient
DOWN]/[27 DOWN, 17 UP]/23/18/23/23, and THREW vs generated), E2's 0-vs-23 / 0-vs-22 / 0-vs-42 /
0-vs-28, the canaries `76723.70 → 76723.65` and `76900 → 76400` and `140457.89 → 140457.88`, the
§3 separating table (`274527298.56` / `274527296.51` / 861 cells; `39166419.22` / `39166419.28` /
610 cells; `395864439.78`/`.71`/228; `425964544.20`/`.19`/72; `12787282386.75`/`.76`/15), the
non-monotonicity ladder (360×7.7 %: 25 M separates, 30–70 M do not, 80 M does; 360×21.6 %: 50 M
separates, 80 M and 100 M do not), N-6's "47 of 48" and "30 of 48", and the cell totals
**3,820 + 90,528 + 147,676 + 1,284 = 243,308** and **238,204**.

The wiring figure 1,284 is T42's *comparison* count (12 comparisons × cells-per-case); the total
cells *present* in the 16 wiring observations is 1,712. Both accountings are internally consistent
and `count_cells.py`'s method is the honest one. No discrepancy.
[VERIFIED: `analysis/audit_recompute-output.txt`]

### 1.5 Invariants, re-run not claimed (`analysis/audit_invariants.py`)

Over all **352 committed observations** (212 in capture 1 + 140 in capture 2; 2 cases threw):

| invariant | result |
|---|---|
| I1 Σ principal due (repayment+down-payment) == principal disbursed | **CLEAN 352/352** |
| I1b plan `totalDisbursedAmount` == disbursement rows | **CLEAN** |
| I1c final row balance == 0 | **CLEAN** |
| I2 Σ row interest == plan `totalInterestAmount` | **CLEAN** |
| I3 row `total` == principal + interest + fee + penalty | **CLEAN** |
| I4 no negative money | **CLEAN** |
| I5 no exponent notation; no money leaf with more decimals than the currency | **CLEAN** |
| I7 balance ladder non-increasing | **CLEAN** |
| I6 Σ row totals == plan `totalRepaymentAmount` *(reported, not asserted — T41 C-1)* | holds on every case here |

On **T41 decision C-1**: C-1 is about `totalRepaymentExpected` on the *charged* schedule path,
where the oracle omits charges applied in the main loop. These payloads carry `loanCharges = null`
and every fee/penalty cell is `0.00`, so I6 is not the C-1 invariant and its holding here is not
evidence against C-1. I therefore report I6 rather than assert it — asserting it on a charged
payload would be a harness bug, not a finding.

Failability of my own suite proved: `analysis/audit_invariants_failability.py` corrupts one
observation in memory and **6 invariants fire** (`analysis/audit_invariants-failability.txt`).

### 1.6 Controls, independently re-transcribed (`analysis/audit_controls.py`)

I re-read the literals from the primary sources myself rather than trusting `controls.py`:

- **C1** — `EmbeddableProgressiveLoanScheduleGeneratorTest.java`: `MathContext(12, HALF_UP)`, `182`,
  `100.00`, `2.05`, `102.05`, 7 periods, rows `16.43/0.58/…/17.01/83.57/85.04` … `16.90/0.10/…/17.00/0.00/0.00`.
- **C4** — `T39-P0-A` from `.softhouse/handoff/T39-periodratio-observation.md` §2: `185`,
  `1200000.00`, `76984.00`, `1276984.00` and the full 6×9 table (`192580.67 | 20250.00 | … | 1064153.33` …).

**105 cells re-transcribed, all reproduce digit for digit** (`analysis/audit_controls-output.txt`).
Script proved failable via `AUDIT_SELFTEST=1`.

### 1.7 Prohibited-token / PostgreSQL-only scan

`grep -rIEi 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver/mysql'` over
`.softhouse/capture/mathcontext/` matches **only** grep patterns asserting absence in the two
runner scripts and prose in `ATTESTATION.md` / `REPRODUCE.md` / `NEGATIVE-TESTS.md`. **CLEAN.**
The oracle classpath carries `postgresql-42.7.11.jar` and zero prohibited driver entries.

---

## 2. Findings

### P1-T44MC-1 — N-3's `new MathContext(10, …)` count is wrong (9 claimed, **5** actual), and the ratified `reference-oracle.md` carries a wrong total

T42 §5 N-3 states "plus **4** `new MathContext(15, MoneyHelper.getRoundingMode())` and **9**
`new MathContext(10, MoneyHelper.getRoundingMode())`" and then gives a citation list of nine
`file:line`s. Re-running the grep myself over the pinned checkout (`/src/test/` and `/misc/`
excluded):

```
new MathContext(15 : 4 sites  — DepositAccountWritePlatformServiceJpaRepositoryImpl.java:496
                                SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:526, :822
                                SavingsAccountDomainServiceJpa.java:329
new MathContext(10 : 5 sites  — DepositAccountWritePlatformServiceJpaRepositoryImpl.java:540, :837
                                SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:627, :695, :919
```

The nine citations T42 lists are the **union of both groups**, not the precision-10 group. The
correct statement is **4 at precision 15 and 5 at precision 10, nine in total**.

`.softhouse/reference-oracle.md` has already ratified the derived figure as "**13**
`new MathContext(15|10, …)`" — 4 + 9. The correct total is **9**.

**Severity P1** — a published, now-ratified count that does not survive re-running the grep it
claims to come from. The qualitative conclusion (savings uses other precisions; the loan path does
not) is unaffected.
[VERIFIED: my grep, reproduced in §1 of this report; `reference-oracle.md` "Two findings that reach
beyond Tier 0"]

### P1-T44MC-2 — N-3's universal claim is false: there is a hard-coded `MathContext` outside savings/deposits, and precision **8** is missing entirely

N-3 asserts: "**Every hard-coded `MathContext` in main source outside the loan modules is in
savings/deposits**". `reference-oracle.md` carries the same as "All 81 `MathContext.DECIMAL64`
uses and 13 `new MathContext(15|10, …)` in main source are in **savings/deposits**."

The full grep of `new MathContext(` in main source (15 sites) contains two that N-3 never mentions:

```
fineract-provider/.../portfolio/shareaccounts/domain/ShareAccountCharge.java:240
        final MathContext mc = new MathContext(8, MoneyHelper.getRoundingMode());
fineract-savings/.../portfolio/savings/domain/SavingsAccountCharge.java:562
        final MathContext mc = new MathContext(8, MoneyHelper.getRoundingMode());
```

`ShareAccountCharge` is **share accounts**, a Tier B context in scope for porting, not
savings/deposits. So the universal is false, and **precision 8 is a third hard-coded precision the
finding omits**. A porter reading N-3 as ratified would carry `(19, HALF_UP)` into share-account
charge calculation and be wrong.

Confirmed correct in N-3, and reproduced by me: **81** `MathContext.DECIMAL64` (49 `fineract-core`
/ 31 `fineract-provider` / 1 `fineract-savings`; 49 of them in
`portfolio/savings/domain/interest/`), **zero** `DECIMAL64` in the loan modules, and **exactly one**
hard-coded `MathContext` in `fineract-loan` + `fineract-progressive-loan` + the embeddable seam
(`AdvancedPaymentScheduleTransactionProcessor.java:2845`).

**Severity P1** — a false universal in a ratified port-hazard finding.
[VERIFIED: repo-wide grep of the pinned checkout at `426a2354…`]

### P1-T44MC-3 — the E1 probe-shape coverage rationale is refuted by T42's own observations, and N-1's second half is tagged `[VERIFIED … observed]` for a site that was never reached

`CaptureMathContext.java:163-166` states the shapes were "chosen so that between them they REACH
every ambient-context read the static scan of the pinned source found on the Path A call graph",
and `:179-181` says `installmentAmountInMultiplesOf` was chosen because
`Money.roundToMultiplesOf(Money,Integer,MathContext)` "ends in the TWO-argument `Money.of`, i.e.
the ambient context".

That site was **never reached**. Observed, from T42's own committed payload:

- `T42-MX-00-A` (plain) and `T42-MX-06-A` (`multiples1000`) differ in exactly one input,
  `installmentAmountInMultiplesOf` (`null` vs `1000`), and their observations differ in **0 cells**;
  period-1 total is `212787.28` on both — not a multiple of 1000.
- Root cause, transcribed: `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
  [`fineract-loan/.../LoanApplicationTerms.java:579-607`] never calls the builder's
  `installmentAmountInMultiplesOf(…)` setter, so `ProgressiveLoanScheduleGenerator.java:110`
  reads `loanApplicationTerms.getInstallmentAmountInMultiplesOf()` as `null`.
- Therefore the three-argument `Money.roundToMultiplesOf` [`Money.java:163-170`] and its trailing
  two-argument `Money.of` [`Money.java:103` → `MoneyHelper.getMathContext()`] are **unreachable
  through this seam** — had they been reached, the ABSENT case would have thrown, exactly as the
  0-dp cases did.

Consequences:

1. **N-1's second half is over-tagged.** "The same pattern appears again at `Money.java:161-171` …
   **This is a port hazard, and it is observed, not read.** `[VERIFIED: stack trace,
   analysis/discriminate-output.txt; source lines transcribed]`". The stack trace evidences
   `Money.java:154` only. The `:163-170` leak is a **transcription** and must be tagged
   `[UNVERIFIED as behaviour]`.
2. **Distinct coverage is smaller than 13.** Four of the thirteen `-A` observations are
   byte-identical to `plain`: `plain`, `multiples1000`, `fixedLength6`, `interestRecognitionOnDisb`
   (0 cells differ). So the E1 matrix carries **10 distinct observations, not 13**, and three of
   the levers chosen to widen coverage (`installmentAmountInMultiplesOf` — dropped;
   `fixedLength=6` at `noRepayments=6`; `interestRecognitionOnDisbursementDate` at
   `disbursementDate == startDate`) had **zero observable effect**.
3. **§3's `TO_BE_CAPTURED` list omits this.** The `installmentAmountInMultiplesOf` ambient path is
   listed nowhere as uncaptured, because T42 believed it captured.

The headline "11 of 13 shapes provably never read the ambient context" remains **literally true and
correctly qualified in §7**; what fails is the rationale for believing those thirteen shapes cover
the Path A ambient reads.

**Severity P1** — an `[VERIFIED … observed]` tag over an unexecuted site, plus an unsupported
coverage claim.
[VERIFIED: `analysis/audit_crosschecks-output.txt`, `analysis/audit_distinctness-output.txt`;
source transcription with `file:line` above]

### P1-T44MC-4 — new oracle fact for DEC-1: `LoanRepaymentScheduleModelData.installmentAmountInMultiplesOf` is a contract input the oracle **silently ignores**, on production Path B as well

Falling out of P1-T44MC-3 and worth raising in its own right, because it is a DEC-1 contract fact
and no task has recorded it:

- The embeddable-model entry point `ProgressiveLoanScheduleGenerator.generate(MathContext, LoanRepaymentScheduleModelData)`
  [`:81-83`] delegates to `LoanApplicationTerms.assembleFrom(modelData, mc)`, which drops the field.
- This is **not** a harness artefact: the production Path B site
  `LoanScheduleGeneratorServiceImpl.java:44-63` reads the ambient `mc`, builds a
  `LoanRepaymentScheduleModelData` **passing `loanProductRelatedDetail.getInstallmentAmountInMultiplesOf()`**,
  and calls `scheduleGenerator.generate(mc, modelData)`. That production call therefore also loses
  the field.
- The `LoanApplicationTerms(Builder)` constructor does honour it when set by the *other*
  `assembleFrom` overloads (`LoanApplicationTerms.java:333-334`,
  `Money.roundToMultiplesOf(downPaymentAmount, …, builder.mc)`), so the two entry points into the
  same generator disagree about whether the field exists.

**Consequence for DEC-1:** a Go port that honours `installmentAmountInMultiplesOf` on the
embeddable-model contract would diverge from the oracle, and **the corpus cannot see it** — every
committed capture that sets the field produces output identical to one that does not.
`TO_BE_CAPTURED`: an `installmentAmountInMultiplesOf` shape through an entry point that honours it.

**Severity P1** (against DEC-1, not against T42's conclusions).
[VERIFIED: observed 0-cell difference above; source transcription `LoanApplicationTerms.java:579-607`,
`:333-334`, `ProgressiveLoanScheduleGenerator.java:81-83`, `:110`,
`LoanScheduleGeneratorServiceImpl.java:44-63`]

### P2-T44MC-5 — T42 fails its own rule 2 on capture 1 (214 of 354 cases)

Rule 2, now ratified: *"On the THREADED context, echo the object, not the intent. Print
`mc.getPrecision()`, `mc.getRoundingMode()` and `mc.toString()` read off the reference handed to
the callee."*

- **Capture 2 complies**: `CaptureMathContext2.java:203-205` echoes `mc`, `mc.getPrecision()`,
  `mc.getRoundingMode()` off the object built at `:174-178` and passed at `:216`.
- **Capture 1 does not**: `CaptureMathContext.java:394-395` echoes `c.precision()` and `c.mode()`
  from the `Case` record; the object is constructed separately at `:369`. `mc.toString()` is never
  printed. `ATTESTATION.md` §2.1 discloses this ("echoes the **constructed values**") but the rule
  as ratified is unconditional.

**Independently corroborated:** the parent auditor raised the same defect as **M-P1** in
`.softhouse/capture/audit-t44/analysis/T44-mathcontext-parent-checks.md`, from a separate check
with no shared context. Two workers converging on one finding is the strongest signal this
pipeline produces.

This covers all 13 E1 shapes and the whole 48-shape precision sweep — i.e. the experiments the
Path A half of the rule rests on. The risk is low (the object is `new MathContext(c.precision(),
c.mode())` fifteen lines later) but it is precisely the class of defect T42 faults T35/T37 for.
**Fix: either bring capture 1 to rule 2, or state in `reference-oracle.md` that capture 1 attests
the intent and is corroborated by the runner's per-case assertion.**
[VERIFIED: source lines above]

### P2-T44MC-6 — E3 has no machine assertion of its actual claim and no negative leg

The Path B row of the ratified rule rests entirely on E3. But `src/read-pathb-wiring.sh`'s only
mechanical assertion is `grep -c 'MoneyHelper.getMathContext' != 0` — "the string appears at least
once". The load-bearing claim (the *same local slot* feeds `generate`) is delegated to the reader:
the script prints *"Read the dataflow yourself in the transcript"*. `NEGATIVE-TESTS.md`'s six legs
cover `run-mathcontext.sh`, `run-mathcontext2.sh` and `controls.py`; **none covers
`read-pathb-wiring.sh` or E3**. By T42's own standard — *an assertion suite that has never failed
has not been tested* — E3's evidence is unfailable by construction.

Mitigating: I re-derived the dataflow by hand from a fresh `javap` and **it holds** (§1.3). The
finding is about the artefact's discipline, not about the claim's truth.
[VERIFIED: `src/read-pathb-wiring.sh` lines 68-80; `NEGATIVE-TESTS.md` table]

### P2-T44MC-7 — "No committed capture is mis-valued" is stated unqualified in the verdict and in the ratified doc; leg 1 is a self-report of the kind T42 refuses elsewhere

§4's heading is *"Here is the demonstration, not the assertion"* and the two-sentence verdict says
flatly "**No committed capture is mis-valued**". `reference-oracle.md` repeats it: "T42
demonstrated this in three legs rather than asserting it."

- **Leg 1** — "The threaded context was independently echoed and asserted in every one of them" —
  cites T35's and T37's **own attestation tables** and T39's **own runner assertion**. Those are the
  same class of self-report T42 correctly declines to accept for the ambient context. T42 did not
  re-run any of the three suites and §7 says so.
- **Leg 2** (the Path A ambient site is unreachable at 2 dp, observed here, plus a grep over the
  committed payloads) and **leg 3** (the committed `T-IM100-he`/`T-IM100-hu` pair returning
  identical rows) are genuine independent evidence and are what actually carries the conclusion.

The conclusion survives on legs 2 and 3. The framing does not: §7's honest qualification
("**[VERIFIED for the three legs stated; UNVERIFIED as a re-run]**") should propagate to the verdict
and to `reference-oracle.md`, and leg 1 should be labelled corroboration rather than demonstration.
[VERIFIED: T42 handoff §4 and §7; `reference-oracle.md` "Amendments to earlier attestations"]

### P2-T44MC-8 — `NEGATIVE-TESTS.md` misdescribes which guard N4 fires; the vacuity guard has never been exercised

`NEGATIVE-TESTS.md` §"N4 is the one that matters" quotes the guard

> `BREACH: the ambient-absence probe is VACUOUS: MoneyHelper.getMathContext() on an uninitialised
> tenant returned … instead of throwing IllegalStateException.`

and says "N4 inverts that expectation and confirms the guard fires."

It does not. `T42_EXPECT_CANARY_THROWS=0` fires the **other** branch
(`not must_throw and canary.startswith("THREW")`), whose message is *"negative run: the canary DID
throw when the run asserted it would not"* — which is what both T42's own transcript
(`out/negative/n4-canary-assertion-inverted.txt`) and **my re-run** (`out/AUDIT-neg4.txt`) record.
The `VACUOUS` branch — the one that protects the experiment if `MoneyHelper` ever stops throwing —
**has never been exercised**.

Substantively harmless: the canary is *observed* to throw on every capture run, which is the fact
that matters, and N4 makes that observation failable in one direction. But the documentation claims
more than the leg proves.
[VERIFIED: `src/run-mathcontext.sh` payload-assertion block; `out/AUDIT-neg4.txt`]

### P2-T44MC-9 — `file:line` drift in several `[VERIFIED]` citations, and one imprecise wiring claim in the ratified rule

All ±2 lines; none changes a claim, but the program's whole evidence discipline is `file:line`.

| cited | actual (pinned checkout) |
|---|---|
| `Money.java:152-158` (2-arg `roundToMultiplesOf`) | `150-157` |
| `Money.java:161-171` (3-arg `roundToMultiplesOf`) | `163-170` |
| `Money.java:49-51` (the `inMultiplesOf` predicate) | `48-50` |
| `MoneyHelper.java:37` (the MathContext cache) | `38` (`:37` is the rounding-mode cache) |

Correct as cited: `MoneyHelper.java:35`, `:79`, `:91-93`; `Money.java:50`, `:107`, `:154`;
`LoanApplicationTerms.java:580`; `ProgressiveLoanScheduleGenerator.java:82`;
`AdvancedPaymentScheduleTransactionProcessor.java:2844-2845` (with the transcribed comment
*"Rounding mode DOWN grants that evenPortion cant pay more than unprocessed transaction amount"* at
`:2841-2843` and the guard `evenPortion.add(balanceAdjustment).isLessThanZero()` at `:2840`);
`LoanScheduleAssembler.java:753`, `:765`, `:777`, `:797`;
`LoanScheduleGeneratorServiceImpl.java:44`; the 14 `MoneyHelper.` sites in
`AdvancedPaymentScheduleTransactionProcessor`.

Separately, `reference-oracle.md` rule 4 says all four sites "do `mc = MoneyHelper.getMathContext()`
and pass it to `generate(mc, …)`". True of `LoanScheduleAssembler.java:753` (→ `:765`) and
`LoanScheduleGeneratorServiceImpl.java:44`; `:777` feeds `rescheduleNextInstallments(mc, …)` and
`:797` feeds `calculatePrepaymentAmount`'s generator. Reword to "pass it to the generator".
[VERIFIED: re-read of each line in `/Users/buv/fineract` at `426a2354…`]

### P2-T44MC-10 — E2's "Path A" column is a replication of E1's ambient rows, not a second experiment

`T42-MX-00-{A,B,E}` and `T42B-PA-ord{4,1,0}` have **identical inputs** on every field and
**0 differing cells**. So E2's "Path A moved 0 cells" re-measures E1's "ambient identical" on the
same shape in a second payload. This is not the T37 double-count sin — E2's load-bearing column is
the *Path B* one, which is new, and T42 never claims the two are independent witnesses. But
`reference-oracle.md`'s "Measured side by side in one payload: moving the tenant ordinal 4 → 1
moves **0 cells** under the Path A wiring and **23 cells** under the Path B wiring" reads as one
experiment when the 0 half is a replication of E1. Worth one clause.
[VERIFIED: `analysis/audit_crosschecks-output.txt`]

### P2-T44MC-11 — `controls-output.txt` publishes two summary lines, not the 172 cells

A reader cannot audit the control result without re-running the script; the compared cells are not
itemised. (I re-transcribed 105 of them from the primary sources and they reproduce — §1.6.)
Compare `discriminate-output.txt`, which does publish its per-shape detail.

---

## 3. What I checked and found CLEAN

- **Byte-determinism.** Both payloads reproduce byte-identically from fresh throwaway containers on
  an independent run. sha256s match T42's `ATTESTATION.md` §4 exactly.
- **Every published cell count and money value** in handoff §1 (E1, E2), §3 (the separating table,
  the ladder) and the cell totals — recomputed with my own exact-`Decimal` tool. All reproduce.
- **The absence experiment is sound.** The two ABSENT cases that threw are **exactly** the two
  0-decimal-place shapes (set equality verified). Each of the eleven that generated produced a full
  6-row schedule with non-zero interest **and** moved 18–24 cells under the threaded rounding-mode
  flip, so none short-circuited before the graded arithmetic. The canary is present in the payload
  and in the header of every run, including mine.
- **The stack trace** in the handoff and `ATTESTATION.md` is a faithful transcription of the frames
  in `T42-MX-07-D` / `T42-MX-08-D`.
- **The Path B wiring** — bytecode digest, four call sites, same-local-slot dataflow — reproduced by
  my own `javap`.
- **N-3's DECIMAL64 arithmetic** — 81 / 49 / 31 / 1, 49 in the savings interest package, 0 in the
  loan modules, exactly one hard-coded `MathContext` in the loan modules.
- **N-4** — `AdvancedPaymentScheduleTransactionProcessor.java:2844-2845`, its guard and its source
  comment, transcribed correctly and honestly tagged `[UNVERIFIED as behaviour]` in §7.
- **N-7** — `MoneyHelper` caches per tenant via `computeIfAbsent`; an exception in the mapping
  function installs no entry, so the ABSENT cases leave the cache genuinely empty and cannot
  contaminate later cases. Unique tenant id per case makes the 354 cases independent.
- **Controls** — C1 and C4 re-transcribed from the primary sources by me; 105 cells reproduce.
- **Failability** — N4 and N5 both re-run and both exit 1 naming the breach.
- **Invariants** — all nine applicable invariants clean over 352 observations; my suite proved
  failable.
- **Money rule** — `BigDecimal.toPlainString()` throughout both harnesses; exact-string comparison
  in the analysis; no `double`/`float`/`doubleValue()` on any amount path; no exponent notation and
  no over-scaled money leaf anywhere in either payload.
- **PostgreSQL-only** — zero prohibited driver entries on the 348-entry classpath;
  `postgresql-42.7.11.jar` present; the only prohibited tokens in the artefact are grep patterns
  asserting absence.
- **Directory discipline** — T42 wrote only `.softhouse/capture/mathcontext/**` and its handoff, as
  `PROVENANCE.md` claims. The running containers were not mutated.
- **Storage form** — raw observed form only, opaque case ids, inputs echoed beside outputs; nothing
  contract-shaped; `PROVENANCE.md` explicitly forbids promoting the matrix, absence, precision and
  wiring families. Correct for an open G-1.

---

## 4. Admissibility verdict

Gate **G-1 is open**, so nothing here is admissible to the parity vector store *today*. The
following is what may be promoted **once G-1 closes**, and what may not.

### 4.1 MAY be promoted — with conditions

**T42B-PREC-30-p19** — MNT 50,000,000 / 360 months / 21.6 %, MNT 2 dp, `DAYS_30`/`DAYS_360`,
monthly, `DECLINING_BALANCE`, no down payment, no charges, **threaded `(19, HALF_UP)`**, ambient
`HALF_UP` (ordinal 4). Production-representative on every axis; all nine invariants clean;
byte-deterministic across two independent runs. Total interest `274527298.56`, 861 cells.

Conditions, all of which T42's F-4 leaves implicit:

1. **Promote the full 861 cells, not the three headline scalars.** The sibling shape at
   360 × 7.7 % moves 610 cells while `totalInterestAmount` moves MNT 0.06 — a three-scalar vector
   would grade this defect class as green. (Program lesson, five consecutive reviews.)
2. **The `(12, HALF_UP)` sibling `T42B-PREC-30-p12` is a labelled discrimination probe and never a
   parity vector**, consistent with `CLAUDE.md`'s standing ruling on precision-12 captures.
3. **A single shape is a legitimate vector, but not a legitimate characterisation.** A vector's job
   is to grade one request, and this one does that. What it must *not* carry is any implication of
   a threshold: separation is non-monotone (25 M separates at 7.7 %, 30–70 M do not, 80 M does; 50 M
   separates at 21.6 %, 80 M and 100 M do not). Labelling it "the shape above which precision
   matters" would be false.
4. **Because it is non-monotone, one shape is weak assurance.** A Go port running the rate factor at
   precision 12 would still match the oracle on **30 of the 62** capture-2 shapes (32 separate).
   I recommend promoting a
   **triple**: the separating shape, plus at least one *non*-separating neighbour at the same rate
   (e.g. MNT 30,000,000 and MNT 80,000,000 / 360 / 21.6 %, both non-separating), so the corpus grades
   the pattern rather than one lucky point. Both neighbours are equally production-representative
   and already captured.

### 4.2 MAY NOT be promoted

- **Every `T42-MX-*` matrix case.** They run deliberately non-ratified ambient (`DOWN`, `UP`) and
  threaded (`DOWN`) modes; two use a 0-dp currency with `inMultiplesOf`, which MNT is not.
- **Every `T42-MX-*-D` absence case.** Two produce no schedule at all; the rest run with
  `MoneyHelper` deliberately uninitialised, which is not a production state.
- **`T42-CAL`.** USD, precision 12, a rig calibration against a shipped test literal. Never a vector.
- **Every `T42B-PB-*` wiring case.** These reproduce Path B's *wiring* on Path A's *transport*. They
  must never be labelled a Path B capture; `PROVENANCE.md` says so and is right.
- **Every `-p8` and `-p12` case**, except as an explicitly labelled discrimination probe.
- **The four `T42-CTL-*` controls.** Production-representative but already committed from T37 and
  T39; promoting them duplicates rather than adds.
- **T42's F-4 second suggestion — "one 0-dp/`inMultiplesOf` shape, as the vector that pins N-1's
  ambient leak".** Hold. That shape's *observed* behaviour is a throw, not a schedule; a promotable
  version needs an initialised tenant, and DEC-1 has not decided whether a 0-dp currency is in the
  graded domain at all. Capture it first, promote it after DEC-1 rules.

### 4.3 Blind spots — *coverage is what a corpus can distinguish, never what it contains*

1. **`installmentAmountInMultiplesOf` — believed covered, actually inert** (P1-T44MC-3/4). Zero
   discriminating power, and worse than absent: a Go port that *honours* the field would diverge
   from the oracle and the corpus would report green. Highest-value new gap this audit found.
2. **`fixedLength` and `interestRecognitionOnDisbursementDate`** — set but observationally inert at
   the shapes chosen (0 cells vs plain). No discriminating power at these shapes.
3. **Charges.** Every `fee` and `penalty` cell in both payloads is `0.00`; Path A passes
   `loanCharges = null`. Zero discriminating power over charges. (T40 owns this elsewhere.)
4. **`RepaymentEvery > 1`; `WEEKS`, `DAYS`, `YEARS` frequencies** — the other
   `calculatePeriodRatio` arms, entirely uncaptured.
5. **`Money.java:163-170` / `Money.java:103` ambient leaks** — unreachable through this seam, never
   observed. `TO_BE_CAPTURED`.
6. **The Path B transport.** Not exercised at all. The wiring is read off deployed bytecode (which I
   confirmed); no Path B request was issued and no tenant ordinal was moved on the running server.
7. **`AdvancedPaymentScheduleTransactionProcessor.java:2844-2845`'s hard-coded `DOWN`.** Source only,
   never executed, reachable only through a repayment transaction.
8. **All savings/deposit/share-account `MathContext` behaviour** (DECIMAL64, 15, 10 and the
   **8** this audit adds). Transcription only; no savings or share code was executed anywhere in
   this program.
9. **Precisions outside {19, 12, 8}; rounding modes outside {HALF_UP, DOWN, UP, HALF_EVEN};
   currencies outside MNT-2dp, MNT-0dp-with-`inMultiplesOf`, USD-2dp.**
10. **Multi-disbursement, mid-term rate changes, interest pause, equal amortization, loan term
    variations, `SAME_AS_REPAYMENT_PERIOD`, non-null `DaysInYearCustomStrategy`** — none reachable
    through `LoanRepaymentScheduleModelData`.
11. **Non-monotonicity beyond the sampled ladder.** 24 principals at 360 × 7.7 % and 9 at
    360 × 21.6 %. A finer ladder could behave differently between sampled points; nothing here
    licenses a claim about an unsampled principal.

---

## 5. Required changes

1. **N-3, in both the handoff and `.softhouse/reference-oracle.md`:** correct "9
   `new MathContext(10, …)`" to **5**, and "13 `new MathContext(15|10, …)`" to **9**
   (P1-T44MC-1).
2. **N-3's universal:** replace "every hard-coded `MathContext` in main source outside the loan
   modules is in savings/deposits" with the enumerated truth, and add the two **precision-8** sites
   — `ShareAccountCharge.java:240` (**share accounts**, not savings) and
   `SavingsAccountCharge.java:562` (P1-T44MC-2).
3. **N-1:** re-tag the `Money.java:163-170` half `[UNVERIFIED as behaviour]`; it was transcribed,
   not observed (P1-T44MC-3).
4. **Add the `installmentAmountInMultiplesOf` drop** as an observed finding with its DEC-1
   consequence, and add it to §3's `TO_BE_CAPTURED` (P1-T44MC-3/4).
5. **Qualify "no committed capture is mis-valued"** in the verdict and in `reference-oracle.md` with
   §7's own wording, and relabel leg 1 corroboration rather than demonstration (P2-T44MC-7).
6. **Either add an E3 assertion + negative leg, or tag the Path B row's evidence** as
   bytecode-read-and-hand-verified rather than machine-asserted (P2-T44MC-6). This audit
   hand-verified it; that fact should be recorded next to the rule.
7. **Note that capture 1 echoes the constructed intent, not the object** — or bring it to rule 2
   (P2-T44MC-5).
8. Minor: fix the four `file:line` drifts and the "pass it to `generate(mc, …)`" phrasing
   (P2-T44MC-9); note the E1/E2 replication (P2-T44MC-10); itemise the 172 control cells
   (P2-T44MC-11); correct `NEGATIVE-TESTS.md`'s description of which guard N4 fires (P2-T44MC-8).

None of these changes a captured value. All are corrections to justification, count or coverage
claim — the same category of defect T42 itself found in T35 and T37.

---

## 6. Unverified

- **"Both payloads are byte-deterministic."** Verified for two re-runs on this host, this image,
  this day. `[VERIFIED for these runs; UNVERIFIED as a general property]`
- **My E1/E2/§3 recomputation** reads the **committed** payloads. It is an independent
  recomputation of the published numbers, not an independent capture — though the captures
  themselves were independently re-executed and came back byte-identical, which closes that gap.
  `[VERIFIED]`
- **"`installmentAmountInMultiplesOf` is inert on this seam."** Verified by observation for the two
  shapes T42 captured and by source transcription of `assembleFrom`. I did **not** run a capture
  through an entry point that honours the field, so I have not observed what honouring it produces.
  `[VERIFIED as a drop; the honouring behaviour is TO_BE_CAPTURED]`
- **N-3's counts** are my re-run of a repo-wide grep with `/src/test/` and `/misc/` excluded,
  matching T42's stated method. They are **transcriptions**; no savings or share-account code was
  executed. `[UNVERIFIED as behaviour]`
- **N-4** — I re-read the site and its guard; it was never executed by anyone.
  `[UNVERIFIED as behaviour]`
- **The Path B dataflow** is verified on the deployed `LoanScheduleAssembler` and, by inspection of
  the same transcript, on `assembleForInterestRecalculation` and `calculatePrepaymentAmount`. I did
  **not** disassemble `LoanScheduleGeneratorServiceImpl` myself (T42's transcript covers it and the
  source line is confirmed). `[VERIFIED for LoanScheduleAssembler; source-confirmed for the fourth
  site]`
- **"No committed capture is mis-valued."** I did **not** re-run T35's, T36's, T37's or T39's
  suites. I re-derived T42's argument and found legs 2 and 3 sound and leg 1 a self-report.
  `[UNVERIFIED as a re-run]`
- **The 172-cell control claim.** I re-transcribed and re-verified **105** of them (C1 and C4) from
  the primary sources. The remaining C2/C3/C5 cells I checked only via `controls.py`'s own PASS.
  `[VERIFIED for 105; the balance rests on T42's script]`
- **Whether the four inert-lever observations mean the levers are broken or merely no-ops at these
  shapes.** `fixedLength` and `interestRecognitionOnDisbursementDate` **are** threaded by
  `assembleFrom`; `installmentAmountInMultiplesOf` is **not**. Whether the first two would move
  money at other shapes is unmeasured. `[VERIFIED for the threading; UNVERIFIED as behaviour]`
- **This audit's own completeness.** T42 found what five prior tasks of difference-probing did not;
  T39 looked 13-of-13 clean until it was attacked. Assume the next review finds something here too.

---

## 7. Artefacts produced by this audit

```
.softhouse/capture/audit-t44/mathcontext/
  AUDIT-MATHCONTEXT.md                      this report
  DIGESTS-before-prune.txt                  sha256 of all 28 re-run artefacts, including the
                                            byte-identical payloads (pruned after digesting)
  src/                                      byte-identical copy of T42's src/, diff-proved
  analysis/audit_recompute.py               independent recomputation of every published number
  analysis/audit_recompute-output.txt
  analysis/audit_invariants.py              9 property invariants over 352 observations
  analysis/audit_invariants-output.txt
  analysis/audit_invariants_failability.py  proves the invariant suite fires
  analysis/audit_invariants-failability.txt
  analysis/audit_controls.py                controls re-transcribed from the primary sources
  analysis/audit_controls-output.txt
  analysis/audit_crosschecks.py             E1/E2 replication, inert-lever, 0-dp set equality
  analysis/audit_crosschecks-output.txt
  analysis/audit_distinctness-output.txt    the 13 shapes collapse to 10 distinct observations
  out/AUDIT-rerun1-console.txt              capture 1 re-run, PASS, payload byte-identical
  out/AUDIT-rerun2-console.txt              capture 2 re-run, PASS, payload byte-identical
  out/AUDIT-neg4.txt                        negative leg N4, exit 1
  out/AUDIT-neg5.txt                        negative leg N5, exit 1
  out/AUDIT-javap-assembler.txt             my own javap of the deployed LoanScheduleAssembler
  out/AUDIT-javap-digests.txt               jar + class sha256 read from the running server
  out/audit-rerun*/audit-neg*-{classpath,log,oracle-identity,stderr}.txt
```
