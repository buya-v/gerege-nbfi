# T46 — closing the T44 audit's `mathcontext` findings (M-1 … M-11)

**Branch:** `softhouse/T46-capture-corrections`.
**Written:** `.softhouse/capture/mathcontext/**`, this file, and corrections in place inside
`.softhouse/handoff/T42-mathcontext-inforce.md`. Nothing else.
**Input:** `.softhouse/reviews/T44-capture-audit.md` §3 and
`.softhouse/handoff/T42-mathcontext-inforce.md`.
**Oracle:** REACHABLE. `fineract-fineract-1` (up 16 h, healthy) and `fineract-db-1`
(`postgres:18.3`) were **read only** — one `docker exec` for `javap`/`unzip` into a fresh
`/tmp/t46j`. Three throwaway `docker run --rm` on
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`. Nothing restarted,
re-tenanted, reconfigured, dropped or written. **PostgreSQL only**; the 348-entry classpath scan
reported zero Oracle Database / MySQL / MariaDB entries on every run.

## Verdict

**All eleven findings are closed.** Nine are closed by correcting a claim; **three of those are
also closed by an experiment that did not exist before** — the vacuity guard is exercised (M-8),
the Path B slot dataflow is machine-asserted with a negative leg (M-6), and the M-5 object echo
is *proved* rather than argued (M-5).

**No recorded observation was changed.** No `out/t42-*.json` payload was touched; every T42
digest in `ATTESTATION.md` §9 still holds. Two T42 *source* files changed and both digests are
published with what changed: `src/CaptureMathContext.java` (**comment-only**) and
`analysis/controls.py` (**append-only**, default output byte-identical, proved twice).

**One correction must be escalated outside my write surface** — see §12.

---

## 1. M-3 (P1) — the E1 coverage rationale is refuted by T42's own data. **CLOSED.**

### What I verified, independently, with an exact-decimal script

`analysis/t46_distinct_coverage.py` → `analysis/t46_distinct_coverage-output.txt`. It reads
`out/t42-mathcontext.json` with `json.load(..., parse_float=Decimal)`, raises `SystemExit` on any
float leaf, and compares the `observed` blocks **cell by cell as exact text**.

| observed | value |
|---|---|
| `-A` baselines in the E1 matrix | **13** |
| byte-identical to `T42-MX-00-A` (`plain`), including `plain` itself | **4** — `plain`, `multiples1000`, `fixedLength6`, `interestRecognitionOnDisb` |
| **distinct observations** | **10, not 13** |
| `plain` vs `multiples1000`: substantive inputs differing | **1** — `installmentAmountInMultiplesOf` `null` → `1000` |
| `plain` vs `multiples1000`: observed cells compared / differing | **74 / 0** |
| period-1 `total` on both | `212787.28` — **not** a multiple of 1000 |

**T44's count is confirmed exactly.** One nuance T44 did not state and I will: the two cases also
differ in `tenantId` (`t42_t42_mx_00_a` vs `t42_t42_mx_06_a`), because the harness assigns a unique
tenant to *every* case by design. That is a harness variable, not a shape variable; the substantive
input difference is one.

### A second, independent confirmation T44 did not use

`T42-MX-06-D` — `multiples1000` with the ambient context **absent** — **generated a schedule**
rather than throwing. It could not have, had the three-argument
`Money.roundToMultiplesOf(Money, Integer, MathContext)` run: that helper finishes with the
**two**-argument `Money.of` [`Money.java:169` → `:102-104`], which calls
`MoneyHelper.getMathContext()` and would have hit the uninitialised tenant exactly as
`T42-MX-07-D` and `T42-MX-08-D` did. **The absence probe would have caught the site had it been
reached. It was not.**

### Cause, re-read by me on the pinned checkout

`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
[`fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanApplicationTerms.java:579-607`]
builds the `Builder` chain and **never calls the `installmentAmountInMultiplesOf` setter**, even
though `LoanRepaymentScheduleModelData` carries the field
[`LoanRepaymentScheduleModelData.java:36`]. So on this seam
`ProgressiveLoanScheduleGenerator.java:110` passes `null` into
`generatePeriodInterestScheduleModel`, and the guard at `:335` is false so the three-argument
`Money.roundToMultiplesOf` at `:336-338` never runs.
[VERIFIED: files re-opened by me in `/Users/buv/fineract`, `git rev-parse HEAD` =
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty]

### What I corrected, and where

- **`src/CaptureMathContext.java` — comment only** (a comment correction changes no observation,
  and the re-emission in §5 proves it: 147,630 of 147,634 leaves byte-identical):
  - the `ambientProbeShapes()` doc comment, which claimed the shapes *"REACH every ambient-context
    read the static scan found on the Path A call graph"*;
  - the `installmentAmountInMultiplesOf` justification comment, which claimed it reached the
    three-argument helper;
  - the **class header's `T42-AMB-*` case-family line**, which restated the same claim — a leak
    T44 did not flag and `patterns.md` warns about.
- **`ATTESTATION.md` §2.5** (new section), **`PROVENANCE.md`** blind spot **B-1**,
  **`REPRODUCE.md`**, and **T42's handoff** at the Verdict, at §1 E1's table caption, at four table
  rows (marked ⚠), in a boxed correction after the leak paragraph, in §3's `TO_BE_CAPTURED` list,
  and in §7 Unverified.

### N-1's second half — over-tagging corrected

T42's N-1 read: *"The same pattern appears again at `Money.java:161-171` … **This is a port hazard,
and it is observed, not read.**"* The tag is now **split**, in T42's handoff §5:

- `Money.java:150-157` (two-argument `roundToMultiplesOf`) — **observed.** The oracle's own stack
  trace names `Money.java:154`.
- `Money.java:163-170` (three-argument overload) — **`[UNVERIFIED as behaviour]`**, a transcription.
  No case reached it. `TO_BE_CAPTURED`.

### Blind spot added

`PROVENANCE.md` **B-1**: the `installmentAmountInMultiplesOf` ambient path — three-argument
`Money.roundToMultiplesOf` [`Money.java:163-170`] plus its trailing two-argument `Money.of`
[`:169` → `:102-104`] — is **ungraded**, and is **unreachable through
`LoanRepaymentScheduleModelData` at all**, so no Path A capture can ever grade it.

---

## 2. M-4 (P1, new oracle fact) — the field is honoured or lost BY CALLER. **CLOSED.**

**I re-opened both files myself, read-only, no Gradle build**, in `/Users/buv/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean.

`fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.java`:

- **`:44`** `final MathContext mc = MoneyHelper.getMathContext();`
- **`:49-61`** builds `new LoanRepaymentScheduleModelData(…)`, and **`:56`** is
  `loanProductRelatedDetail.getInstallmentAmountInMultiplesOf(), //`
- **`:63`** `return scheduleGenerator.generate(mc, modelData).getTotalInterestAmount();`

and `assembleFrom(modelData, mc)` [`LoanApplicationTerms.java:579-607`] then **drops the field**.
**T44's line numbers `:56` and `:63` are confirmed exactly.**

Meanwhile the REST `calculateLoanSchedule` path via `LoanScheduleAssembler` **does honour** the
field — capture `B-02`, `112,082.37 → 112,100.00`. Nothing in T46 disturbs that observation.

**So `installmentAmountInMultiplesOf` is honoured or lost depending on which production caller
builds the schedule, and DEC-1 must not state its behaviour unconditionally.**

Recorded in `PROVENANCE.md` blind spot **B-2**, `ATTESTATION.md` §2.5, and T42's handoff §1 and §3.
`TO_BE_CAPTURED` on both callers.
`[VERIFIED as source; UNVERIFIED as behaviour — no capture exercises
calculateInteresOnlyWithFirtDisbursement.]`

---

## 3. M-1 / M-2 (P1) — the hard-coded `MathContext` inventory, re-derived. **CLOSED.**

`analysis/t46_mathcontext_inventory.sh` → `analysis/t46_mathcontext_inventory-output.txt`. Every
line is a grep hit with `file:line` over the pinned checkout, `/src/test/` and `/misc/` excluded.
Nothing derived, nothing counted by hand.

**15 `new MathContext(` sites in main source**, by the precision argument as written:

| precision | count | sites |
|---|---|---|
| **15** | **4** | `SavingsAccountDomainServiceJpa.java:329`; `DepositAccountWritePlatformServiceJpaRepositoryImpl.java:496`; `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:526`, `:822` |
| **10** | **5** | `DepositAccountWritePlatformServiceJpaRepositoryImpl.java:540`, `:837`; `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:627`, `:695`, `:919` |
| **8** | **2** | `SavingsAccountCharge.java:562` (`fineract-savings`); **`ShareAccountCharge.java:240`** (`fineract-provider/src/main/java/org/apache/fineract/portfolio/shareaccounts/domain/`) |
| non-literal | **4** | `MoneyHelper.java:93`, `:124` (the `PRECISION = 19` constant); `MathUtil.java:473` (a *parameter*); `AdvancedPaymentScheduleTransactionProcessor.java:2845` (T42's N-4) |

**T44's M-1 is confirmed: the 15-or-10 total is 9, not 13.** T42's N-3 published 9
`new MathContext(10, …)` sites; there are 5, and its list was the union of the 15s and the 10s all
labelled 10. **T44's M-2 is confirmed: both precision-8 sites were omitted, and
`ShareAccountCharge.java:240` is in share accounts, a separate Tier B context.**

**What I re-derived and found CORRECT in N-3:**

- `MathContext.DECIMAL64`: **81** = 49 `fineract-core` + 31 `fineract-provider` + 1
  `fineract-savings`;
- **0** `DECIMAL64` occurrences whose path contains neither "saving" nor "deposit";
- **0** `DECIMAL64` in any loan module;
- `fineract-loan` **0**, `fineract-progressive-loan` **1**
  (`AdvancedPaymentScheduleTransactionProcessor.java:2845`), the embeddable seam **0** literal
  `new MathContext(` sites.

### NEW FINDING (T46-N1) — an indirect hard-code neither T42 nor T44 has

`MathUtil.percentageOf(BigDecimal, BigDecimal, int)` [`MathUtil.java:472-473`] is

```java
public static BigDecimal percentageOf(final BigDecimal value, final BigDecimal percentage, final int precision) {
    return percentageOf(value, percentage, new MathContext(precision, MoneyHelper.getRoundingMode()));
}
```

so a caller passing a **literal** precision hard-codes the precision **and takes the AMBIENT
rounding mode**. **Six loan-path call sites pass a literal `19`**, all on down-payment computation:

- `fineract-loan/.../AbstractCumulativeLoanScheduleGenerator.java:1897`, `:2060`
- `fineract-loan/.../LoanApplicationTerms.java:866`
- `fineract-loan/.../LoanDownPaymentHandlerServiceImpl.java:198`
- `fineract-provider/.../LoanWritePlatformServiceJpaRepositoryImpl.java:448`, `:3538`

**Consequence.** T42's N-3 sentence *"the loan modules contain exactly one hard-coded
`MathContext`"* is true only of the literal `new MathContext(` form. Through `MathUtil` there are
six more, and each takes the **ambient** mode rather than a threaded one — the exact class of leak
T42's N-1 documents inside `Money`. A Go port that threads a context through down-payment
computation will be more consistent than Fineract and may diverge. `TO_BE_CAPTURED`; recorded in
`PROVENANCE.md` **B-4** and T42's handoff §3.
`[VERIFIED as grep with file:line; UNVERIFIED as behaviour — none executed.]`

Corrections applied to N-3 in T42's handoff §5 (full replacement table, with the original text
retained for the record) and to `ATTESTATION.md`'s correction table. **`reference-oracle.md` is
outside my write surface — escalated in §12.**

---

## 4. M-11 (P2) — the 172 control cells are now published. **CLOSED.**

In the order the brief required.

1. **`analysis/controls.py` re-run UNMODIFIED.** Output sha256
   `4b847fc97fc5545bd0913f40ae50408a948101891f6b921b83e0c372d4988e1c` — **byte-identical** to the
   committed `analysis/controls-output.txt` (`diff` silent).
2. **Verbose mode added, append-only.** `T42_CONTROLS_VERBOSE=1` (env) or `--verbose` (argv).
   Default is `False`, so the default path is untouched; the added code is one flag, one `cell_rows`
   list appended to inside the existing `eq()`, and one print block guarded by `if VERBOSE:` before
   the existing summary. The label split (`control-id` / `field`) is derived from the existing
   `where` strings, so **no call site changed**.
3. **Default mode re-run after the edit.** Output sha256 `4b847fc9…72548d` **again** — byte-identical
   to both the committed file and the pre-change re-run. Re-verified a third time at the end of the
   task.
4. **Verbose output published:** `analysis/t46-controls-cells-output.txt`, 179 lines —
   **172 cells listed as `control-id | field | expected | observed | MATCH`, 172 MATCH, 0 MISMATCH**,
   then the unchanged two-line summary.

`analysis/controls.py`'s digest moved from
`e82aecfe130737cd1d722ec22e793a86f2fc8a6b6a5d2635daa75715ec72548d` to
`eb257639afabf648326a53104ad434c3e56f687fd3647794c9bcfd3a4af7d5ed`; both are published in
`ATTESTATION.md` §9.1 with the reason and the identity proof.

---

## 5. M-5 (P2) — corrected AND proved. **CLOSED, and upgraded from a claim to an observation.**

### The claim correction (what the brief asked for)

`ATTESTATION.md` §2.1 now states plainly that in `out/t42-mathcontext.json` the keys
`threadedMathContextPrecision` / `threadedMathContextRoundingMode` carry the case record's
**INTENT** (`c.precision()`, `c.mode()`), not a reading off the object, on **214 of the 354** cases
in the set — a breach of T42's own ratified rule 2 on the capture that carries E1. It states what
is unaffected and why: the two objects are constructed one line apart from the same record; the
**ambient** field in capture 1 *is* read off the object; the two stack traces are direct
observations; and E1 is an **absence** result that turns on whether a schedule generated at all.
It records that `CaptureMathContext2.java:203-205` complies fully, and that the same fix is
demonstrated in the sibling set by `.softhouse/capture/periodratio/src/CapturePeriodRatio2.java`
— which echoes `mc.toString()` / `mc.getPrecision()` / `mc.getRoundingMode()` at `:342-344` and a
`wiring` field at `:345-347`. **I read that file; I did not edit it or anything else under
`capture/periodratio/`.** `[UNVERIFIED as a stable citation]` — a concurrent sibling task owns
that set and was still writing to the file, so the line numbers are correct as read but may drift.

### The optional part — done, and it was cheap

- `analysis/t46_make_capture3.py` **generates** `src/CaptureMathContext3.java` from
  `src/CaptureMathContext.java` with exactly four mechanical edits (header, class name, `harness`
  label, four **appended** keys), asserting each anchor occurs exactly once. Generating rather than
  hand-copying makes the diff reviewable, and `run-mathcontext3.sh` **regenerates it and refuses to
  run if the file has been hand-edited**.
- The four added keys are read off `mc` — the very reference passed to
  `generator.generate(mc, config)`: `threadedMathContext` (`mc.toString()`),
  `threadedMathContextPrecisionFromObject`, `threadedMathContextRoundingModeFromObject`, `wiring`.
  **The two original keys are left in place**; nothing is replaced.
- `src/run-mathcontext3.sh` re-runs the capture in throwaway `docker run --rm` containers on the
  pinned image and **will not publish** unless `analysis/t46_m5_identity.py` passes; on failure it
  moves the payload to `*.json.REJECTED` and exits non-zero.

### The identity proof — `analysis/t46-m5-identity-proof.txt`

| | |
|---|---|
| cases | 214 committed, 214 re-emitted, 214 common |
| top-level keys identical | 12 of 13 (`harness` differs, by design and by declaration) |
| **previously published leaves compared** | **147,634** |
| **leaves that MOVED** | **0** |
| leaves EXEMPT, enumerated verbatim in the proof | **4** |
| **leaves byte-identical** | **147,630** |
| keys added | **856** |
| **cases where the OBJECT echo disagrees with the INTENT** | **0 of 214** |

**The 4 exemptions, stated in full because they are the one carve-out.** They are the harness's
*own* frames inside the two absence stack traces —
`at CaptureMathContext.run(CaptureMathContext.java:423)` and
`at CaptureMathContext.main(CaptureMathContext.java:323)` on `T42-MX-07-D` and `T42-MX-08-D`. A
re-emission by a differently-named class cannot reproduce its own frames, and they carry no
information about the oracle. **Every oracle frame** — `MoneyHelper.getRoundingMode`,
`Money.roundToMultiplesOf`, `Money.<init>`, `Money.of`, `LoanApplicationTerms.assembleFrom`,
`ProgressiveLoanScheduleGenerator.generate` — **and every money cell is byte-identical.** The
exemption is a regex that requires *both* the old and the new value to be a harness self-frame;
anything else remains fatal, and every exemption taken is printed.

**Honesty note.** The first run of `run-mathcontext3.sh` **REJECTED** the payload, because the
carve-out did not exist yet and those 4 leaves were fatal. That transcript is kept deliberately as
`out/negative/t46-n8-identity-check-rejects.txt`: it is evidence that the check refuses to publish.
The carve-out was then written, named, justified and made to print what it exempts.

**The substance.** The last row of the table is the finding: **M-5's materiality is now observed,
not argued.** Capture 1 was mis-*named*, never mis-*valued*.

**`out/t46-mathcontext3.json` does not replace `out/t42-mathcontext.json`.** Both are kept; the T42
payload remains the record of what T42 observed.

### Failability — negative leg N9

`src/t46-negative-identity.sh` moves one money cell by one minor unit (`T42-CAL` period-1
`interest` `0.58 → 0.59`, computed with `Decimal`, never `float`) and the check exits 1 naming that
cell; on the real pair it exits 0.
[`out/negative/t46-n9-identity-check-failable.txt`]

---

## 6. M-10 (P2) — E2's framing corrected everywhere it appears. **CLOSED.**

Corrected in **`ATTESTATION.md` §6** and in **T42's handoff §1 E2**, in both cases at the point the
claim is made rather than in a footnote.

**What E2's Path A column is:** a **replication** of E1's ambient rows. It runs the same plain
shape (MNT 1,200,000 × 6 × 21.6 %, 2 dp), varies the ambient tenant ordinal, holds the threaded
context fixed, and observes **0** differing cells — which is exactly `T42-MX-00-A`'s ambient-flip
rows in the E1 table. Same inputs, same seam, same conclusion, one harness later. **Two runs of one
experiment are one experiment.** Worse, taken alone the `PA` arm is a **difference** probe, the
weaker design E1 exists to replace.

**What E2 genuinely does add:**

1. **The `PB` arm — the contrast E1 has no version of.** When the caller sources the threaded
   context *from* the ambient one, moving the ambient moves **23** cells (`4→1`), **22** (`4→0`),
   and **28** on T36's half-cent-tie shape (`140457.89 → 140457.88`). That is the whole content of
   ratified rule 4 and it is a real, separate result.
2. **A rule-2-compliant attestation** — `CaptureMathContext2.java:203-205`.
3. **Negative leg N5**, proving the two families are not merely *labelled* differently.

**What E2 does NOT add:** independent evidence that the ambient context is unread on Path A. That
claim rests on **E1 alone**, plus T42 §4's grep over the committed corpus.

---

## 7. M-6 (P2) — machine assertion added, with a negative leg. **CLOSED.**

**The finding is confirmed:** `src/read-pathb-wiring.sh`'s only machine assertion is

```sh
N_GMC="$(grep -c 'MoneyHelper.getMathContext' "$OUT" || true)"
[ "$N_GMC" != "0" ] || fail "..."
```

and the same-local-slot claim ends with *"Read the dataflow yourself in the transcript"*.

**What I added.** `analysis/t46_assert_pathb_slot.py` parses a `javap -p -c` transcript into
methods and asserts, per method that calls `MoneyHelper.getMathContext`:

- **A1** the instruction immediately after `invokestatic MoneyHelper.getMathContext` is
  `astore <slot>`;
- **A2** that same slot is later `aload`ed and consumed by an `invoke*` whose descriptor contains
  `Ljava/math/MathContext;`;
- **A3** no other `astore <slot>` occurs in between — the slot is not re-assigned, so the object
  consumed **is** the object `MoneyHelper` returned;
- **A4** the consuming method's **name and the `mc` argument position** are reported per site, not
  assumed.

`src/t46-assert-pathb-slot.sh` drives it: it **re-reads the deployed bytecode off the running
`fineract-fineract-1`** with `javap` (read-only — unzips two `.class` files into a fresh
`/tmp/t46j`; nothing restarted, re-tenanted, reconfigured or written), asserts on the committed
transcript **and** the re-read, then asserts against a **slot-drifted** copy.

**Result** [`analysis/t46-pathb-slot-assertion-output.txt`]:

| method | slot | getMC@ | astore@ | aload@ | consumer | `mc` arg |
|---|---|---|---|---|---|---|
| `assembleLoanScheduleFrom` | 9 | 31 | 34 | 57 | `updateInterestForEqualAmortization` | 1 of 4 |
| `assembleLoanScheduleFrom` | 9 | 31 | 34 | 109 | **`LoanScheduleGenerator.generate`** | 1 of 4 |
| `assembleForInterestRecalculation` | 6 | 0 | 3 | 83 | `LoanScheduleGenerator.rescheduleNextInstallments` | 1 of 6 |
| `calculatePrepaymentAmount` | 8 | 19 | 22 | 87 | `LoanScheduleGenerator.calculatePrepaymentAmount` | **4 of 7** |
| `calculateInteresOnlyWithFirtDisbursement` | 2 | 37 | 40 | 201 | **`ProgressiveLoanScheduleGenerator.generate`** | 1 of 2 |

**PASS** on the committed transcript, **PASS** on the fresh re-read, **FAIL (6 breaches)** on the
slot-drifted copy. T42's linchpin claim holds, and is now machine-checked.

**Independently reconfirmed digests, 20 hours after T42 read them:** jar
`60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9`; `LoanScheduleAssembler.class`
`d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea` — the same digest T42 and the
T44 audit each recorded independently. **Newly recorded:** `LoanScheduleGeneratorServiceImpl.class`
sha256 `eca9b7d9010722e19c90bfd84c29cba9e3352adc0b460020b0df96608d1e31d6`.

---

## 8. M-7 (P2) — the qualification now travels with the claim. **CLOSED where I can write.**

Applied at **four** places, not one (`patterns.md`: corrections leak):

1. T42 handoff **Verdict** — the sentence itself now carries
   `[VERIFIED for the three legs in §4, plus T46's fourth leg for capture 1; UNVERIFIED as a re-run
   of T35's or T36's suites]`.
2. T42 handoff **§4**, as a boxed instruction stating that the qualification is part of the claim
   wherever it is repeated, and that **leg 1 is a self-report** of exactly the class T42 refuses
   elsewhere — weaker than legs 2 and 3, and shown inaccurate for T39 (F39-3) and for T42's own
   capture 1 (M-5).
3. `ATTESTATION.md` **§2.7**, a new section.
4. **A fourth, independent leg supplied by T46:** the re-emission proves the object echo and the
   intent agree on all 214 cases of capture 1 (§5 above) — which converts leg 1 for this capture
   from a self-report into an observation.

**T46 did NOT re-run T35's or T36's suites either**, so the "UNVERIFIED as a re-run" half stands
unchanged. **`reference-oracle.md` also carries the unqualified form — escalated in §12.**

---

## 9. M-8 (P2) — the vacuity guard has now been exercised. **CLOSED.**

**The finding is confirmed from source.** `run-mathcontext.sh`'s assertion block has:

```python
must_throw = os.environ["EXPECT_CANARY_THROWS"] == "1"
if must_throw and not canary.startswith("THREW java.lang.IllegalStateException"):   # :157-160
    bad.append("the ambient-absence probe is VACUOUS: ...")
if not must_throw and canary.startswith("THREW"):                                    # :161-162
    bad.append("negative run: the canary DID throw when the run asserted it would not: ...")
```

N4 sets `T42_EXPECT_CANARY_THROWS=0`, so `must_throw` is **False** and the branch that fires is the
**second** — which is exactly what N4's own transcript records. **N4 proves the canary throws; it
never exercised the vacuity guard**, and the vacuity guard is the one that makes E1 falsifiable.

**Exercised, as negative leg N7** (`src/t46-negative-vacuity.sh`,
`out/negative/t46-n7-vacuity-guard.txt`), by the technique leg N6 already uses for `controls.py`:
run the **shipped** assertion code against a deliberately corrupted payload. "Shipped" is literal —
the Python block is **extracted from `src/run-mathcontext.sh` at run time** (the heredoc between
`<<'PY'` and the closing `PY`), so the guard exercised is the committed one and cannot drift from
it. No container is started; the running oracle is not contacted.

| | |
|---|---|
| corruption | `ambientCanary` rewritten from `THREW java.lang.IllegalStateException: …` to `precision=19 roundingMode=HALF_UP`, `EXPECT_CANARY_THROWS` left at default 1 |
| observed cells proved identical between source and corrupted payload | **140,978** (the corruption touched nothing else) |
| result on the corrupted payload | **exit 1**, `BREACH: the ambient-absence probe is VACUOUS: MoneyHelper.getMathContext() on an uninitialised tenant returned 'precision=19 roundingMode=HALF_UP' instead of throwing IllegalStateException. Every ABSENCE case is meaningless.` |
| result on the **uncorrupted** payload (control leg) | **exit 0**, `ok 214 captures, 13 of them ambient-ABSENT` — so the guard **discriminates** |

`NEGATIVE-TESTS.md` is corrected in **three** places: the header count, the N4 row of the top
table, and the "N4 is the one that matters" section that made the wrong claim.

---

## 10. M-9 (P2) — four `file:line` drifts, each re-opened by me. **CLOSED.**

I re-opened every one in `/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(working tree clean) before writing it down. **All four of T44's corrections are confirmed.**

| T42 said | correct | what is actually there |
|---|---|---|
| `Money.java:152-158` | **`:150-157`** | `public static BigDecimal roundToMultiplesOf(final BigDecimal existingVal, final Integer inMultiplesOf)` opens at `:150`; the `MoneyHelper.getRoundingMode()` divide is `:154`; the method closes at `:157` |
| `Money.java:161-171` | **`:163-170`** | the three-argument `roundToMultiplesOf(Money, Integer, MathContext)` opens at `:163` and closes at `:170`; **`:159-161` is the two-argument `Money` overload**, which is what T42's range wrongly swallowed |
| `Money.java:49-51` | **`:48-50`** | the `if (currency.getInMultiplesOf() != null && …` opens at `:48`, continues on `:49`, and the guarded `roundToMultiplesOf(amountScaled, currency.getInMultiplesOf())` call is `:50` |
| `MoneyHelper.java:37` | **`:38`** | `:37` is `roundingModeCache`; `:38` is `mathContextCache`. T42's `:36-37` in §1 E1 should read `:37-38`. |

**The stack-trace line numbers T42 published are correct and unchanged** — `Money.java:154`,
`:50`, `:107`, `MoneyHelper.java:79`, `LoanApplicationTerms.java:580`,
`ProgressiveLoanScheduleGenerator.java:82` all match the pinned source.

### *"pass it to `generate(mc, …)`"* — wrong for **`:777` and `:797`**

Named, with what they actually do, machine-extracted from the deployed bytecode **and** re-read in
the pinned source:

| site | actually |
|---|---|
| `LoanScheduleAssembler.java:753` | `updateInterestForEqualAmortization(mc, …)` at `:758` **and** `loanScheduleGenerator.generate(mc, …)` at `:765` — **claim holds** |
| **`LoanScheduleAssembler.java:777`** | `loanScheduleGenerator.rescheduleNextInstallments(mc, …)` at `:787-788` — **not `generate`** |
| **`LoanScheduleAssembler.java:797`** | `loanScheduleGenerator.calculatePrepaymentAmount(currency, onDate, loanApplicationTerms, mc, …)` at `:805-806` — **not `generate`, and `mc` is the 4th argument of 7, not the 1st** |
| `LoanScheduleGeneratorServiceImpl.java:44` | `scheduleGenerator.generate(mc, modelData)` at `:63` — **claim holds** |

The **substance** of ratified rule 4 is unaffected: on all four the threaded context is the ambient
object. But `patterns.md` is explicit — *cite the call site, not the helper* — and the row is now
per-site. Corrected in `ATTESTATION.md` §2.3, in T42 handoff §2 rule 4, in the T42 handoff Verdict
(which restated it), and in the T36 correction in T42 handoff §4 (which restated it again).

---

## 11. Corrections-leak sweep

After every correction I grepped the whole set for restatements
(`patterns.md`: *"an author fixes the section the review named and leaves the sections that restate
the same claim"*). Found and fixed, beyond what T44 named:

- **The `Money.java:49-51` citation appears TWICE** in T42's handoff — §1 E1 *and* §4 leg 2. Both
  corrected.
- **The "generate(mc, …)" claim appears THREE times** — §2 rule 4, the Verdict, and the T36
  correction in §4. All three corrected.
- **The E1 coverage claim appears in the `CaptureMathContext.java` class header** as well as on
  `ambientProbeShapes()`. Both corrected.
- **"No committed capture is mis-valued" appears in the Verdict, §4, §7 and `reference-oracle.md`.**
  The first three corrected; the fourth escalated.
- **`MoneyHelper.java:37` appears in N-7** as well as `:36-37` in §1 E1. Both corrected.

Final grep confirms **zero** remaining occurrences of `Money.java:152-158`, `:161-171`, `:49-51`,
`:49-52`, `MoneyHelper.java:36-37`, or a bare `MoneyHelper.java:37` citation for the
`MathContext` cache anywhere under `.softhouse/capture/mathcontext/` or in T42's handoff.

---

## 12. MUST BE ESCALATED — outside my write surface

**`.softhouse/reference-oracle.md`. I did not edit it.** Two corrections are needed; the first is a
wrong number already folded in.

1. **The `new MathContext` total is wrong.** `reference-oracle.md` records
   *"**13** `new MathContext(15|10, …)`"*. **The correct total is 9** — 4 at precision 15 and 5 at
   precision 10. The 13 was 4 + 9, double-counting the 15s, inherited from T42's N-3 miscount.
   **And two precision-8 sites must be added**: `SavingsAccountCharge.java:562` and
   **`ShareAccountCharge.java:240`, which is in `portfolio/shareaccounts/` — share accounts, a
   different Tier B context with its own precision, not savings/deposits.** Any accompanying claim
   that every hard-coded `MathContext` outside the loan modules is in savings/deposits must be
   withdrawn. This is a **porter-facing** number: it is the part of N-3 a Tier B porter will
   actually use.
   [VERIFIED: `.softhouse/capture/mathcontext/analysis/t46_mathcontext_inventory-output.txt`]
2. **Two claims need qualifying wherever `reference-oracle.md` carries them:**
   *"no committed capture is mis-valued"* must read
   `[VERIFIED for the three legs stated; UNVERIFIED as a re-run]` (M-7), and the Path B wiring row
   must not say all four sites *"pass it to `generate(mc, …)`"* — `:777` calls
   `rescheduleNextInstallments`, `:797` calls `calculatePrepaymentAmount` with `mc` as the 4th
   argument (M-9).
3. **Worth folding in as new facts** (T46's additions, not corrections): the `installmentAmountInMultiplesOf`
   caller-dependence (M-4 / §2 above) and the six indirect `MathUtil.percentageOf(…, 19)`
   ambient-mode sites (T46-N1 / §3 above).

**Also for the orchestrator, not written by me:** `patterns.md` candidates in §14.

---

## 13. Unverified

Stated plainly, and separately from everything above.

- **The re-emission's identity proof carves out 4 leaves.** They are the harness's own
  `CaptureMathContext.run`/`.main` stack frames, they are enumerated verbatim in the published
  proof, and a differently-named class cannot reproduce them. **147,630 of 147,634 leaves are
  byte-identical and 0 oracle-observed leaves moved** — but "every previously published value is
  identical" is *not* literally true and I will not write that it is. `[stated]`
- **M-4 is a source transcription.** `calculateInteresOnlyWithFirtDisbursement` was never executed;
  no capture reaches that entry point. `[VERIFIED as source; UNVERIFIED as behaviour]`
- **T46-N1's six `MathUtil.percentageOf(…, 19)` sites** are a grep with `file:line`. None was
  executed. `[UNVERIFIED as behaviour]`
- **The whole re-derived `new MathContext` inventory** is a grep of the pinned checkout with
  `/src/test/` and `/misc/` excluded. No savings, deposit or share-account code was run.
  `[UNVERIFIED as behaviour]`
- **`Money.java:163-170` (the three-argument `roundToMultiplesOf`) was never executed** by any
  capture in this program. N-1's second half is a transcription. `[UNVERIFIED as behaviour]`
- **T46 did not re-run T35's or T36's suites**, so M-7's "UNVERIFIED as a re-run" is unchanged.
- **The M-5 re-emission was run ONCE at its final source state**, not twice. Its determinism is
  witnessed *against the committed T42 payload* (147,630 identical leaves from a different
  container on a different day), which is a stronger check than a same-day self-diff — but it is
  not a same-source re-run, and I did not do one. `[stated]`
- **The Path B slot assertion is a BYTECODE-DATAFLOW assertion, not an execution.** It proves the
  deployed artefact stores and loads one slot; it does not observe a request being served.
  T42's §7 statement that **the Path B transport was not exercised at all** remains true of T46
  too. `[stated]`
- **The verbose control mode lists the cells `controls.py` compares.** It does not widen what is
  compared: C2/C3/C5 still assert only the columns their source artefacts publish. Publishing 172
  cells is a transparency fix, not a coverage increase. `[stated]`
- **`controls.py` parses the payload with plain `json.load`.** I checked that no money leaf is
  affected — every money value in the payload is a JSON **string** (`"100.00"`, `"2.05"`), and the
  only bare numbers touched (`loanTermInDays`, `periodNumber`) are integers compared via `str()`.
  No monetary value passes through a float. But `controls.py` itself does not *enforce* that, and I
  did not change it to, because that would have altered a committed script beyond append-only.
  `[VERIFIED by inspection of the payload; the script carries no guard]`
- **I did not re-verify T44's own arithmetic** beyond the findings assigned to me (the E1/E2/§3
  cell totals, the nine property invariants, the 105 re-transcribed control cells). Those remain on
  T44's testimony.

---

## 14. New findings, and follow-ups

- **T46-N1 (P2, new oracle fact).** Six loan-path sites hard-code precision 19 **and take the
  ambient rounding mode** via `MathUtil.percentageOf(…, 19)` → `new MathContext(precision,
  MoneyHelper.getRoundingMode())` [`MathUtil.java:472-473`], all on down-payment computation.
  Refutes T42 N-3's "exactly one hard-coded `MathContext` in the loan modules" as a general claim,
  and is a **port hazard of the same shape as N-1**. `TO_BE_CAPTURED`. §3 above.
- **T46-N2 (P2, method).** The absence probe would have caught M-3 on its own: `T42-MX-06-D`
  generated a schedule where a reached three-argument `roundToMultiplesOf` must have thrown. **An
  absence probe is also a coverage detector** — if the shape you added to reach a site does not
  throw when the dependency is removed, you did not reach the site. That is a free, general check
  and nobody used it. Candidate for `patterns.md`.
- **T46-N3 (P2, method).** *A shape that changes nothing is not coverage.* Three of thirteen E1
  levers moved zero cells, and the set believed itself fully covering for a whole fire. **Diff every
  new shape against the control before claiming it exercises anything** — it costs one script and it
  is exactly the "coverage is what a corpus can distinguish" lesson applied at shape level rather
  than corpus level. Candidate for `patterns.md`.
- **T46-N4 (P2, method).** *Publish the cells, not the verdict.* A 2-line `PASS` and a 172-line
  cell dump cost the same to produce and differ completely in what a reviewer can check.
  Candidate for `patterns.md`.
- **F-1 (orchestrator, immediate).** Apply §12 to `.softhouse/reference-oracle.md`.
- **F-2 (DEC-1).** Add to T42's F-2 list: DEC-1 must **not** state `installmentAmountInMultiplesOf`
  behaviour unconditionally — it is honoured by the REST `LoanScheduleAssembler` route and lost by
  `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` (M-4).
- **F-3 (vector store, after G-1).** The `installmentAmountInMultiplesOf` blind spot can only be
  closed on **Path B**. `B-02` already exists; a matching Path B vector plus a
  `calculateInteresOnlyWithFirtDisbursement` capture would pin the caller-dependence.

---

## 15. Artefacts

**Added under `.softhouse/capture/mathcontext/`:**

`analysis/t46_distinct_coverage.py` + `-output.txt` (M-3) ·
`analysis/t46_mathcontext_inventory.sh` + `-output.txt` (M-1/M-2) ·
`analysis/t46-controls-cells-output.txt` (M-11) ·
`analysis/t46_assert_pathb_slot.py`, `analysis/t46-pathb-slot-assertion-output.txt`,
`src/t46-assert-pathb-slot.sh`, `out/t46-pathb-wiring-reread.txt`,
`out/negative/t46-pathb-wiring-slot-drifted.txt` (M-6) ·
`src/t46-negative-vacuity.sh`, `out/negative/t46-n7-vacuity-guard.txt`,
`out/negative/t46-corrupted-canary-payload.json` (M-8) ·
`analysis/t46_make_capture3.py`, `src/CaptureMathContext3.java`, `src/run-mathcontext3.sh`,
`analysis/t46_m5_identity.py`, `analysis/t46-m5-identity-proof.txt`, `out/t46-mathcontext3*.{json,txt}`,
`src/t46-negative-identity.sh`, `out/negative/t46-n9-identity-check-failable.txt`,
`out/negative/t46-perturbed-reemission.json`, `out/negative/t46-n8-identity-check-rejects.txt` (M-5).

**Modified:** `ATTESTATION.md` (correction table + §2.1, §2.3, §2.4, §2.5, §2.6, §2.7, §3, §5, §6,
§9.1, §9.2) · `NEGATIVE-TESTS.md` · `PROVENANCE.md` (blind-spot list B-1…B-4; directory discipline)
· `REPRODUCE.md` (T46 recipes) · `src/CaptureMathContext.java` (**comment only**) ·
`analysis/controls.py` (**append-only**) · `.softhouse/handoff/T42-mathcontext-inforce.md`
(18 in-place `[T46 CORRECTION]` / `[T46 ADDITION]` marks).

**All digests, including the two T42 files whose digests moved and why:** `ATTESTATION.md` §9.1.
**Recipes:** `REPRODUCE.md`, T46 section.
