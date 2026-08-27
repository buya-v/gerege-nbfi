# T42 — provenance and storage form

## RAW OBSERVED FORM ONLY. Nothing here is promoted.

Gate **G-1 is open** and **DEC-1 is unratified**. The contract *shape* is what is being ratified,
so a contract-shaped capture would beg the question. Everything under this directory is stored in
the shape the oracle emitted it, keyed by an opaque case id, with the inputs echoed beside it.
**Nothing is in the parity vector store and nothing should be moved there by this task.**

## What these captures ARE

Discrimination probes about **which `MathContext` governs which arithmetic step**, and a search
for a shape on which threaded precision 19 separates from 12. They answer a question about the
*provenance rule for attestations*, not about the loan schedule contract.

Specifically:

- The **matrix** cases (`T42-MX-*`) deliberately run at non-ratified ambient rounding modes
  (`DOWN`, `UP`) and non-ratified threaded modes (`DOWN`), and two of them at a non-MNT-shaped
  currency (0 decimal places with `inMultiplesOf`). **None of these is production-representative
  and none may ever be promoted as a parity vector.** They exist to make an ambient read visible.
- The **absence** cases (`T42-MX-*-D`) run with `MoneyHelper` deliberately uninitialised. Two of
  them produce no schedule at all, only a stack trace. That stack trace *is* the finding.
- The **precision** cases (`T42-PREC-*`, `T42B-PREC-*`) run at threaded precision 12 and 8, which
  `CLAUDE.md` already records as discrimination probes rather than parity vectors, and at
  principals up to MNT 100,000,000,000,000 chosen to expose the arithmetic rather than to model a
  product.
- The **wiring** cases (`T42B-PA-*` / `T42B-PB-*`) differ only in where the `MathContext` came
  from. The `PB` family reproduces Path B's *wiring* on Path A's *transport*; it is **not** a Path
  B capture and must not be labelled one.

## The only cases that are production-representative

`T42-CTL-Q0a`, `T42-CTL-1`, `T42-CTL-P0A`, `T42-CTL-MEB` — the four reproduction controls, at the
ratified `(19, HALF_UP)` on MNT with 2 decimal places. They exist to prove this harness is not the
variable, and every one of them **already exists** in the committed corpus from T37 and T39.
Promoting them would duplicate, not add.

`T42-CAL` is the rig calibration at `(12, HALF_UP)` against a shipped USD test literal. It is
**never** a parity vector, exactly as T37's and T39's calibrations are not.

## Where the numbers came from

Every published number is either

- **observed** from a live run against the pinned oracle
  (commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`, image
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`), or
- **transcribed** from a source literal or a committed artefact, with `file:line` given.

Nothing is synthesised, extrapolated or interpolated. Uncovered behaviour is `TO_BE_CAPTURED` and
is listed in the handoff's coverage section, and in the blind-spot list below.

## Blind spots — `TO_BE_CAPTURED` (list opened by T46 from audit findings M-3 and M-4)

T42's §3 coverage statement is still the authoritative list of *unswept shapes*. This section adds
the blind spots the T44 audit found that T42 believed it had covered, plus the two production
facts that fall out of them.

### B-1. The `installmentAmountInMultiplesOf` ambient path is UNGRADED

The three-argument `Money.roundToMultiplesOf(Money, Integer, MathContext)`
[`Money.java:163-170`], which divides with the *supplied* `mc` and then finishes with the
**two-argument** `Money.of` [`:169` → `:102-104`], i.e. the **ambient** context for the final
`setScale`. **This site was never reached by any T42 case.** T42's harness comment claimed the
`multiples1000` and `downPaymentMultiples1000` shapes reached it; they do not.

- **Observed:** `T42-MX-00-A` (plain) vs `T42-MX-06-A` (`multiples1000`) — one substantive input
  differs, **0 of 74 observed cells** differ; the absence case `T42-MX-06-D` generated a schedule
  instead of throwing [VERIFIED: `analysis/t46_distinct_coverage-output.txt`].
- **Cause:** `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
  [`LoanApplicationTerms.java:579-607`] never sets the field, so
  `ProgressiveLoanScheduleGenerator.java:110` and the guard at `:335` read `null`.
- **Consequence:** the field **is not reachable at all through `LoanRepaymentScheduleModelData`**,
  so no Path A capture can ever grade it. Grading it needs Path B — the REST
  `calculateLoanSchedule` route, where capture `B-02` already shows it live
  (`112,082.37 → 112,100.00`).
- **Distinct coverage of the E1 matrix is 10, not 13.** Four of the thirteen `-A` observations are
  byte-identical to `plain`: `plain`, `multiples1000`, `fixedLength6`, `interestRecognitionOnDisb`.

### B-2. `installmentAmountInMultiplesOf` is honoured or lost BY CALLER (a production fact)

`LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` — the
multi-disbursement interest-only entry point — builds a `LoanRepaymentScheduleModelData` passing
the field at **`:56`** and calls `scheduleGenerator.generate(mc, modelData)` at **`:63`**, and
`assembleFrom` then drops it. The REST path via `LoanScheduleAssembler` **does** honour it.
`TO_BE_CAPTURED` on both callers; **DEC-1 must not state this field's behaviour
unconditionally.** [VERIFIED: both files re-opened by T46 in the pinned checkout at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean; **UNVERIFIED as behaviour** for
the `calculateInteresOnlyWithFirtDisbursement` caller — no capture exercises it.]

### B-3. Carried forward from T42 §3, unchanged

`RepaymentEvery > 1`; the `WEEKS` / `DAYS` / `YEARS` frequency arms; `DaysInYearCustomStrategy`
non-null; `interestCalculationPeriodMethod = SAME_AS_REPAYMENT_PERIOD`; multi-disbursement;
mid-term rate changes; interest pause; equal amortization; loan term variations; **charges**
(`loanCharges = null` on this seam); everything downstream of schedule generation (repayment
allocation, accruals, COB, charge-off) including N-4's hard-coded `RoundingMode.DOWN`; the Path B
**transport** (every T42 observation is Path A); precisions other than {19, 12, 8} and modes other
than {`HALF_UP`, `DOWN`, `UP`, `HALF_EVEN`}.

### B-4. New from T46's inventory re-derivation

`MathUtil.percentageOf(BigDecimal, BigDecimal, int)` [`MathUtil.java:472-473`] constructs
`new MathContext(precision, MoneyHelper.getRoundingMode())` — the **ambient** rounding mode. Six
loan-path call sites pass a **literal 19**
[`AbstractCumulativeLoanScheduleGenerator.java:1897`, `:2060`; `LoanApplicationTerms.java:866`;
`LoanDownPaymentHandlerServiceImpl.java:198`; `LoanWritePlatformServiceJpaRepositoryImpl.java:448`,
`:3538`], all on down-payment computation. Uncaptured.
[VERIFIED: `analysis/t46_mathcontext_inventory-output.txt`, grep with `file:line`;
**UNVERIFIED as behaviour** — none was executed.]

## Directory discipline

**T46 (corrections) wrote only** `.softhouse/capture/mathcontext/**`,
`.softhouse/handoff/T46-mathcontext-corrections.md` and corrections inside
`.softhouse/handoff/T42-mathcontext-inforce.md`. It **read** `.softhouse/capture/periodratio/`
(specifically `src/CapturePeriodRatio2.java`, as the reference for the M-5 object-echo fix) and
wrote nothing there. `.softhouse/reference-oracle.md`, `.softhouse/patterns.md`,
`.softhouse/tasks.json`, `.softhouse/program.json`, `.softhouse/gates.md`,
`.softhouse/reviews/**`, `docs/adr/**` and `nexus/**` were **not** edited; the corrections
`reference-oracle.md` needs are reported in T46's handoff for the orchestrator to apply.
T46 added `src/CaptureMathContext3.java`, `src/run-mathcontext3.sh`, three `t46-*` negative-leg
scripts and eight `t46_*` / `t46-*` analysis artefacts. **`out/t46-mathcontext3.json` does not
replace `out/t42-mathcontext.json`; both are kept.**

T42 wrote **only** `.softhouse/capture/mathcontext/**` and
`.softhouse/handoff/T42-mathcontext-inforce.md`. It read `.softhouse/capture/periodratio/`,
`/out/`, `/pathb/` and `/dec1-binding/` and wrote to none of them. `docs/adr/**` and `nexus/**`
were not touched (T41 owns them this fire). `.softhouse/reference-oracle.md`,
`.softhouse/patterns.md`, `.softhouse/tasks.json`, `.softhouse/program.json` and
`.softhouse/gates.md` were read and **not** edited; the corrections they need are reported in the
handoff for the orchestrator to apply.

The seam source under `src/` is this task's **own copy**, proved byte-identical to the pinned
original by `diff` and by sha256
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — the same digest T37 and T39
recorded independently. Sibling capture directories were never compiled from.
