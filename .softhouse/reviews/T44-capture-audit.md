# T44 — independent audit of three capture sets

**Task:** T44, branch `softhouse/T44-capture-audit`, worker `auditor`.
**Audited:** `.softhouse/capture/periodratio/` (T39), `.softhouse/capture/charges/` (T40),
`.softhouse/capture/mathcontext/` (T42) — the three capture sets from fire `20260819-080001`,
none of which had been independently audited.

**Reference oracle (Fineract) reachability, this fire:** **REACHABLE**
[VERIFIED: `actuator/health` → `{"status":"UP","groups":["liveness","readiness"]}`;
`fineract-fineract-1` (`fineract:latest`) up 15 h healthy, `fineract-db-1` (`postgres:18.3`)
up 38 h healthy; `docker image inspect fineract:latest` →
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, created
`2026-08-17T11:29:56Z` — the pinned digest]. Pinned checkout `/Users/buv/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty
[VERIFIED: run by this task]. So this audit re-executed work rather than only reading it.

**Storage discipline observed by this audit.** Everything written by T44 is raw audit evidence
under `.softhouse/capture/audit-t44/**`. **Nothing is promoted to the parity vector store and
nothing is stored contract-shaped** — gate **G-1** is open. The three audited subtrees,
`dec1-binding/`, `src/`, `out/`, `pathb/`, `docs/adr/**`, `nexus/**`, `.softhouse/reviews/T43*`
and `t43-probe/` were **read only, never written**.

---

## Verdicts

| set | task | verdict | findings |
|---|---|---|---|
| `.softhouse/capture/periodratio/` | T39 | **ACCEPTED WITH REQUIRED CHANGES** | F39-1, F39-2 (P1); F39-3, F39-4 (P2) |
| `.softhouse/capture/charges/` | T40 | **ACCEPTED WITH REQUIRED CHANGES** | A-1…A-4 (P1); A-5…A-8 (P2) |
| `.softhouse/capture/mathcontext/` | T42 | **ACCEPTED WITH REQUIRED CHANGES** | M-1…M-4 (P1); M-5…M-11 (P2) |
| cross-cutting | — | — | T44-X1 (P2) |

**No set was rejected, and no synthesised number was found in any of the three** — the single thing
this audit most needed to rule out. Every published figure traced to an observed oracle response or to
a source literal at the cited `file:line`, with **one** exception, A-2, where the line is real but says
the opposite of what it is cited for.

**What the three sets share** is not a bad number; it is a **narrower proof than the handoff claims**.
In T39 the month-end family grades a pair of behaviours rather than the one it names; in T40 the corpus
cannot see which of two inputs supplies the charge amount; in T42 the shapes chosen to reach a leak do
not reach it. In each case the *conclusion* survives and the *coverage claim* does not — which is the
`patterns.md` lesson, *coverage is what a corpus can distinguish*, landing for the sixth consecutive
round.

**Two findings were reached independently by two audit legs with no shared context** — M-1/M-2 (N-3's
miscount) and M-5 (T42 breaking its own rule 2). By this program's own standard that is the strongest
evidence it generates.

---

# 1. `periodratio` (T39) — **ACCEPTED WITH REQUIRED CHANGES**

**The headline claim survives, and it survives an independent re-derivation rather than a
re-reading.** P0-T34-1 is confirmed. The *second* claim — that the month-end special case is
graded — does not survive: the family grades a **pair** of behaviours, and the mis-port a real
porter would write is invisible to every capture in it.

## 1.1 What I re-ran, and what it showed

| leg | result |
|---|---|
| **Seam-source identity**, computed by me against the pinned original | `sha256 bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`, `diff` silent — identical for `periodratio/src/`, `mathcontext/src/` **and** `capture/src/` [VERIFIED: this task] |
| **Full re-execution** of `run-periodratio.sh` from a fresh `docker run --rm` container, harness copied into `audit-t44/rerun-periodratio/` and `diff -r`-proved identical first | `== PASS -- capture admissible`; 16 captures; classpath 348 entries, digest `68e68148…b5f95f`, **zero** Oracle Database / MySQL / MariaDB entries |
| **Byte-identity of the payload** vs the committed one | **identical**; both `sha256 898435d89b58c1c61dd0b9d55b2bae38ab8fedd33f41d314ffea09b5c7e5b3a2` — matches T39's published digest |
| **Failability leg 1** — `T39_EXPECT_SEAM_SHA=deadbeef` | **exit 1**, `BREACH: seam class sha256 is bf397f0b…, expected deadbeef` |
| **Failability leg 2** — `-Dt39.mathContextRoundingMode=DOWN` (the **threaded** axis, the one that is evidence about money) | **exit 1**, 17 breaches: the left-set-override breach plus `threaded rounding mode DOWN, expected HALF_UP` on all 16 cases |
| **Provenance sweep** — the handoff's observed table, the `T39-P0-A` 6 × 9 worked table, the `T39-ME-B` table, `loanTermInDays`, the disbursed/repayment totals | **110 of 110 published values traced to the observed payload, 0 mismatched** [`audit-t44/analysis/t44_provenance_t39-output.txt`] |
| **Control C1** — the transcription from the shipped test literal | verified line by line against the pinned source: `EmbeddableProgressiveLoanScheduleGeneratorTest.java:44` (`new MathContext(12, RoundingMode.HALF_UP)`), `:74-77` (`182`, `100.00`, `2.05`, `102.05`), `:79-92` (7 periods and their rows). Payload `T39-CAL` matches every one |
| **Control C2** — `T39-CTL-Q0a` vs committed `Q0a` | reproduces `t23-probe-output.txt:5-16` digit for digit through a different harness on a different task |
| **Independent re-derivation** (below) | R2 reproduces **131 of 132** interest cells; R1 fails **39 of 132** |

An accidental leg worth recording: a **typo'd** negative-test property
(`-Dt39.mathContextRoundingModeOverride=…`, not the real `-Dt39.mathContextRoundingMode=…`) was
silently ignored and the run PASSED — correctly, because the payload came back **byte-identical**
to the good run, so the override really was inert. The harness asserts the three *recognised*
override properties are unset; an unrecognised `-D` is simply not a variable.

## 1.2 The independent re-derivation

I wrote `audit-t44/analysis/t44_periodratio_independent.py` **from the pinned source only** —
`ProgressiveEMICalculator.java:1404-1413`, `:1419-1458`, `:1461-1479`, `:1536-1537`, `:1598-1611`,
`:1922-1927`, `:1950-1963`, and `DateUtils.java:312, :315-317`. It never reads T39's
`analysis/` (`readings.py`, `t34_model.py`, `t34_periodratio.py`). Exact `Decimal`, `parse_float=Decimal`,
no float anywhere. It predicts each period's interest as
`round(previousBalance × rateFactor, 2, HALF_UP)` with

```
rateFactor = setScale( interestRate × (30 × MULTIPLIER / daysInYear) × actualDays / calculatedDays,
                       precision-as-SCALE, mode )          [:1962 - precision used as a SCALE]
```

and `MULTIPLIER` being the reading under test. Result over all 16 captures / 132 interest cells:

| reading | reproduces |
|---|---|
| **R1** — multiplier is `RepaymentEvery` (DEC-1 rev 6) | **93 / 132** — fails on 39 cells, all inside the 8 drift shapes, **0** failures on the 4 controls |
| **R2** — `periodRatio`, packed whole-months, month-end case PRESENT (the pinned source) | **131 / 132** |
| **R3** — `periodRatio`, packed whole-months, month-end case OMITTED | 121 / 132 |
| **R4** — `periodRatio`, month-end case OMITTED **and** whole-months done the naive way | **131 / 132 — identical to R2 on every cell** |

The single R2 "miss" is `T39-ME-A` period 3 (`37,132.16` observed vs `37,132.17`), where **all
four** readings predict the same wrong value — my simplified model does not carry the EMI
re-adjust/residual step. It carries no discriminating information and is a limit of my model, not
of the capture.

**P0-T34-1 is independently confirmed.** Worked at the decisive cell: `T39-P0-A` period 1 has
`periodRatio = 1.034482758620689655`, `actualDays = 29` (disbursement 01-31 inside a period opening
01-28), `calculatedDays = 32`, so `0.216 × (30 × 1.034482…/360) × 29/32 = 0.016875` exactly, and
`0.016875 × 1,200,000 = 20,250.00` — the observed value. Under R1 the multiplier is `1` and the
same arithmetic gives `19,575.00` — the DEC-1 value T34 hand-worked. Two readings, one observation,
and the observation is R2's.

**N-1 is independently confirmed too.** `:1412-1413` passes `(…, periodRatio, BigDecimal.valueOf(30), …)`;
`:1536-1537` passes `(…, repaymentEvery, daysInMonth, …)`; and `:1508` computes
`daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) : calculatedDaysInRepaymentPeriod`,
so on DEC-1's graded domain (`DaysInMonth = DAYS_30`) the fourth argument is `30` on both sites and
the *effective* difference is exactly one argument. T39's correction to T34 is right.

## 1.3 Findings

### **F39-1 (P1) — the month-end family does not discriminate what its handoff says it does.**

T39 states: *"the oracle agrees **116 of 116** with the routine that includes those four lines and
**0 of 116** with the same routine minus them"*, and concludes the special case is *"live and
load-bearing"*. The comparison is sound; the **null hypothesis is the wrong one**.

T39's R3 omits the special case while keeping Java's **packed** whole-months rule —
`ChronoUnit.MONTHS.between`, which is `(prolepticMonth × 32 + dayOfMonth)` differenced and
integer-divided by 32 [VERIFIED: `DateUtils.java:312, :315-317` → `ChronoUnit.between`; the packed
rule is `java.time.LocalDate.monthsUntil`]. That combination is not what a porter writes. The
obvious implementation of "whole months between two dates" is *count calendar months, step back one
if `plusMonths` overshoots* — and **that implementation, with the special case omitted, reproduces
the oracle exactly.**

Measured, not argued [VERIFIED: `audit-t44/analysis/t44_r2_vs_r4_sweep-output.txt`], over every
`(scheduleStartDate, period)` pair for 1,095 start dates across 2023-01-01…2025-12-30 × terms
{6, 12, 36}, `RepaymentEvery = 1`, MONTHS:

```
  (start, period) pairs                                : 59130
  periods on which the MONTH-END SPECIAL CASE FIRES    : 701
  periods where packed and naive whole-months DISAGREE : 701
  periods where periodRatio(R2) != periodRatio(R4)     : 0
```

The 701 periods where the special case fires are **exactly** the 701 where the two whole-months
functions disagree, and the two errors cancel on every one. The special case is *precisely a
compensation* for the packed rule's month-end undercount: when `fromDate` is the last day of its
month and `seedDate.day > fromDate.day`, packed undercounts by one and the `+1 day` nudge at
`:1433` restores it — which is also what the naive rule returns unaided.

Consequence, and it is the `patterns.md` lesson in its exact form — *coverage is what a corpus can
distinguish*: **all four `T39-ME-*` captures score a port with two cancelling defects as correct.**
They grade the *pair* (`month-end special case` ∧ `packed whole-months`), never the special case
alone.

*Corroboration.* T41's own probe reached the same seam from the contract side and raised **F-1,
"step B's whole-months function is two functions; pin the packed rule"** [`.softhouse/handoff/T41-dec1-v8.md`,
commit `b299ade`]. Two tasks with no shared context converging on one seam is the strongest signal
this pipeline produces (`patterns.md`), and it upgrades this from a re-derivation to a corroborated
finding.

**Required change.** (a) The T39 handoff's verdict and §2 table must say the ME family grades the
pair, not the special case, and must name R4 as the untested reading. (b) DEC-1's month-end
obligation must pin the **packed** rule normatively alongside the special case — the special case
without the packed rule is *wrong*, and neither clause is safe stated alone. (c) A discriminator
for packed-vs-naive is **`TO_BE_CAPTURED`** and cannot come from this family: it has to come from
`calculatePeriodRatio`'s `YEARS` / `WEEKS` / `DAYS` arms (`:1405`, `:1407`, `:1408`), which call
`getExactDifference` with **no** special case at all, so there the two rules do not cancel. Those
arms are entirely uncaptured today.

### **F39-2 (P1) — T39's attestation repeats the exact defect T42 found in T37, and T42's correction list omits T39.**

`ATTESTATION.md` §4 is headed *"The `MathContext` actually in force, as the oracle itself reports
it"* — the phrasing T42's rule 1 exists to ban — and then offers *"Two independent witnesses to the
mode, both from the oracle rather than from this harness"*:

1. the oracle's SLF4J log, 16 lines of `Initialized rounding mode for tenant '<id>': HALF_UP`;
2. `MoneyHelper.getMathContext()` echoed per case as `precision=19 roundingMode=HALF_UP`.

**Both are ambient, and they are not two witnesses — they are one cache write, logged and then read
back.** [VERIFIED: `MoneyHelper.java:59-64` — `initializeTenantRoundingMode` computes
`roundingMode`, does `roundingModeCache.put(...)` and emits that very log line from the same local;
`:91-94` — `getMathContext()` does `mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))`;
`:74-82` — `getRoundingMode()` reads `roundingModeCache.get(tenantId)`.] This is verbatim the defect
T42 raised against T37 §5 ("one witness counted twice"), and on Path A the ambient context is
**provably never read** for a 2-dp currency anyway.

T42 §4 issues corrections for **T35, T36, T37 and `reference-oracle.md`** and **never names T39** —
so the fold-in that landed on `main` (commit `2df4d49`) corrected three attestations and left a
fourth carrying the identical wording defect, in the same fire.

**Mitigation, stated because it is real:** §4's own closing paragraph (lines 83-89) draws the
ambient/threaded distinction honestly and says *"only the second is a statement about the
arithmetic"*, and the N7 negative leg is a genuine **threaded** behavioural canary that I re-ran and
watched fail. **No captured value is affected** — only the justification, exactly as with T37.

**Required change.** Correct `capture/periodratio/ATTESTATION.md` §4: retitle it to name the
ambient context, delete "two independent witnesses" (they are one), and add T39 to the amended-
attestations list in `reference-oracle.md`.

### **F39-3 (P2) — the threaded `MathContext` is echoed as INTENT, not as the object.**

T42 rule 2: *"On the THREADED context, echo the object, not the intent — `mc.getPrecision()`,
`mc.getRoundingMode()`, `mc.toString()`, read off the reference handed to the callee."*

T39 does not. `CapturePeriodRatio.java:261` builds the object —
`final MathContext mc = new MathContext(c.precision(), c.mode());` — and `:286-287` write
`c.precision()` and `c.mode()`, the **case record's own fields**, into the payload. Nothing anywhere
reads `mc`. The ambient context, by contrast, *is* correctly echoed off the object
(`:256 String.valueOf(MoneyHelper.getMathContext())` into `inputs.ambientMoneyHelperMathContext`) —
so the set attests the context that does not matter by the object, and the context that does matter
by its intent.

Consequence: `run-periodratio.sh`'s assertion 10 (`:202`, `:210`) compares those intent fields
against a constant, so it is **tautological with respect to the object handed to `generate`**. It
cannot be wrong today, because `:261` is constructed from the same two fields one line later; it
simply does not have the strength the attestation claims for it. Also `:196` calls the ambient
reading *"effective MoneyHelper MathContext"* — the exact word T42 told T35 to drop.

**Required change.** Echo `mc.getPrecision()` / `mc.getRoundingMode()` / `mc.toString()` into a
`threadedMathContext` field, assert *that*, and rename the `:196` breach text to "ambient".

### **F39-4 (P2) — line citations for the month-end case are imprecise in a way a porter would act on.**

The handoff defines R3 as *"R2 minus `:1429-1434`"*, and the verdict cites `:1426-1436`. Neither is
the special case. `:1429` is `.getDayOfMonth();`, the continuation of the `targetDateLastDay`
declaration opened at `:1428`; `:1434` is `} else {`; `:1426-1436` is the entire `case MONTHS ->`
arm. The special case proper is the predicate at **`:1432`** and the nudged call at **`:1433`**.
A porter deleting `:1429-1434` literally removes a declaration and does not compile.
Separately, §3 N-1's prose says `daysInMonth` is computed at `:1509` while its own `[VERIFIED]` tag
says `:1508`; **`:1508` is correct** [VERIFIED: this task].

## 1.4 Checked and found CLEAN

- Seam class byte-identical to the pinned original — verified by me, not read back.
- Live re-execution byte-identical to the committed payload; T39's published digest is real.
- The run recipe is genuinely failable, including on the **threaded** axis specifically.
- 110 / 110 published values traced to an observation. **No synthesised number found anywhere in
  the set** — the primary thing this audit was sent to look for.
- Both controls verified against their cited sources, one of them a source literal read line by line.
- No float on any money path in `src/` or `analysis/`; `BigDecimal.toPlainString()` throughout.
- No Oracle Database / MySQL / MariaDB entry on the 348-entry classpath — asserted on **my** run.
- Container discipline held: every container `--rm`; `fineract-fineract-1` / `fineract-db-1` were
  read but never started, stopped, re-tenanted or written to, by T39 or by me.
- `PROVENANCE.md` separates OBSERVED / RE-DERIVED / TRANSCRIBED explicitly, and the separation holds
  where I checked it.
- T39 §7's self-declared unverified items are honest and complete as far as I could test them.

## 1.5 Admissibility — `periodratio`

**May be promoted once G-1 closes:**

- **`T39-P0-A` … `T39-P0-H`** (8 drift shapes) — the strongest parity candidates in the set. They
  discriminate the P0 on 415 full cells, are bracketed by three in-domain controls on which all
  readings agree, are byte-deterministic across two independent executions on different days, and
  ran at the ratified threaded `(19, HALF_UP)`. `T39-P0-F` (MNT 100) and `T39-P0-D`
  (MNT 50,000,000 / 36) should both go, since they pin the bottom and top of the observed range.
- **`T39-ME-A` … `T39-ME-D`** — admissible **only if relabelled per F39-1**. As "grades the
  month-end special case" they are misleading; as "grades the month-end special case *jointly with*
  the packed whole-months rule" they are sound and worth keeping.
- **`T39-CTL-1`, `T39-CTL-2`, `T39-CTL-Q0a`** — admissible as **controls**, never as discriminators;
  by construction all three readings agree on them.

**May NOT be promoted:**

- **`T39-CAL`** — runs at threaded `(12, HALF_UP)`, not the ratified setting; T39 already says so.
  A second reason this audit adds: its transcription source asserts through `double`
  (`toDouble(...)`, `2.05`, `102.05` at `…Test.java:75-77`), so it is only as exact as a 2-dp
  double round-trip. Rig calibration only.
- **Anything asserting the month-end special case in isolation** — see F39-1.

**Blind spots — what this corpus cannot distinguish:**

1. **packed vs naive whole-months** — provably indistinguishable across the entire swept monthly
   domain (F39-1). `TO_BE_CAPTURED` via the `YEARS`/`WEEKS`/`DAYS` arms.
2. `calculatePeriodRatio`'s `YEARS`, `WEEKS`, `DAYS` arms (`:1405`, `:1407`, `:1408`) — **entirely
   uncaptured**, as T39 records.
3. `RepaymentEvery > 1` — every capture pins `1`, and `RepaymentEvery` is the *other* reading's
   whole content, so a port could hard-code the multiplier to `periodRatio` **and** mishandle
   `RepaymentEvery` and still pass all 16.
4. `DaysInMonth = ACTUAL` (routes to a different arm at `:1400-1402`/`:1534`) and
   `DaysInYear = ACTUAL`.
5. **Charges** — every `fee` and `penalty` is `0.00` on all 16, so the set has zero discriminating
   power over them; the `charges` set is where that is answered.
6. `installmentAmountInMultiplesOf` and `daysInYearCustomStrategy` — Path A **drops both**
   (`reference-oracle.md`, Path A blind spot), so they are unreachable here by construction.
7. Multi-disbursement, down payments, `fixedLength`, `interestRecognitionOnDisbursementDate`.
8. The EMI re-adjust loop is not exercised by these shapes (only `T39-ME-A` period 3 shows a
   residual my model cannot follow) — it is pinned by the `dec1-binding` set, not this one.
9. T39's N-2 disjointness sweep (51,729 pairs / 210 firings) is **uncommitted** and self-declared
   `[UNVERIFIED as a committed artefact]`; I did not reproduce it and it is not reproducible from
   the committed files. My own 59,130-pair sweep is committed under `audit-t44/analysis/` and is
   *not* the same experiment, so it neither confirms nor refutes N-2.

---

# 2. `charges` (T40) — **ACCEPTED WITH REQUIRED CHANGES**

**Every observation in the set reproduced.** All five headline behaviours are real, the two silent-loss
paths are real, and no synthesised number was found. What the audit found instead is that **the corpus
does not pin the input it thinks it pins**, that D-1's single source citation points at the one line
that refutes it, and that C5 is a probe wearing an invariant's badge.

Full working, scripts and raw outputs: `.softhouse/capture/audit-t44/charges/AUDIT-CHARGES.md`.

## 2.1 What was re-run against the live oracle

- **11 of the 21 requests re-issued byte-verbatim** from `capture/charges/req/` (plus the CTRL-B-01
  control from `capture/pathb/req/`) against the running server: **all byte-identical**, including
  `XR-01`'s HTTP 403 body. T40's determinism claim holds.
- **The precondition script proved failable**: run against tenant `default` instead of `gerege` it
  **exits 1 naming five breaches**, the behavioural half-cent canary among them. And it is
  byte-verbatim T36's script — three-way sha256 match.
- **C1–C10 re-implemented independently** from the stated definitions and re-run: matches
  `out/INVARIANTS.md` cell for cell, including C5's 15 failures.
- **A 336-leaf diff** (against T40's 286) reproduced every moved-leaf count; the difference is exactly
  `25 dates × 2`, which confirms "286 leaves" really is every money leaf.
- **All seven Q5 percentage bases and both rounding-locus gaps recomputed exactly** —
  `5,437.06` vs `5,437.07` and `16,603.92` vs `16,603.88`.
- **D-2a / D-2b byte-identity re-verified four ways.** `> 60 published numbers` in §§4-9 traced to raw
  JSON leaves, **zero synthesised values**. The 12 `m_charge` rows match the attestation exactly, and
  the tenant was left as found (`m_charge` 12, `m_loan` 0 — nothing created, nothing modified).

## 2.2 Findings

### **A-1 (P1) — T42 rule 4's wiring citation is entirely absent.**
`grep -E 'LoanScheduleAssembler|LoanScheduleGeneratorServiceImpl|wiring|threaded|ambient'` over the whole
of `capture/charges/` **and** the handoff returns **zero hits**. T40 is a **Path B** set, so its ambient
`MoneyHelper` reading genuinely *is* the threaded object — but rule 4 requires that be *said and cited*
(`LoanScheduleAssembler.java:753, :777, :797`; `LoanScheduleGeneratorServiceImpl.java:44`), not left
implicit. As written, the attestation presents the ambient reading as "the effective `MathContext`" with
nothing connecting it to the arithmetic. **The conclusion is right and the justification is missing.**

### **A-2 (P1) — D-1's single source citation points at the one line where the two generators AGREE.**
The handoff says *"The cumulative (non-progressive) generator does add them
[VERIFIED: `AbstractCumulativeLoanScheduleGenerator.java:504`], so the two generators disagree."*
I opened it myself. `:504` is
`scheduleParams.addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment));`
sitting inside `updatePeriodsWithCharges`, immediately after `addTotalFeeChargesCharged` /
`addTotalPenaltyChargesCharged` at `:502-503` — i.e. the **separated-path** site that the progressive
generator has too, at `ProgressiveLoanScheduleGenerator.java:486`. Cited as proof of disagreement, it is
the one site of agreement.

**The conclusion is nonetheless true, at a different line** [VERIFIED by me on the pinned source]: the
cumulative **main loop** does `scheduleParams.addTotalRepaymentExpected(totalInstallmentDue)` at `:392`,
where `:352` sets `totalInstallmentDue = currentPeriodParams.fetchTotalAmountForPeriod()` and
`ScheduleCurrentPeriodParams.java:144-145` defines that as
`principalForThisPeriod.plus(interestForThisPeriod).plus(feeChargesForInstallment).plus(penaltyChargesForInstallment)`.
The progressive main loop adds only `principalDue.plus(interestDue, mc)` [`:137`].

**P1 because D-1 is the finding that drove T41's ratified DEC-1 decision C-1.** A reader checking the one
citation offered for its most consequential half would conclude the opposite. **Required change:** replace
`:504` with `:392` + `ScheduleCurrentPeriodParams.java:144-145`, in the handoff and everywhere D-1 is
restated.

### **A-3 (P1) — the observed money came from the REQUEST amount, not from the attested charge definitions.**
The handoff frames the mandatory per-request `amount` as a redundant echo of the definition
(*"Every request therefore repeats the definition's amount as exact decimal text"*). It is not redundant —
**the request value is authoritative and `m_charge.amount` is ignored**, for percentage and flat charges
alike, observed on the live oracle:

| probe | request | definition in `m_charge` | observed |
|---|---|---|---|
| AP-5 | `{"chargeId": 4, "amount": 0.001875}` | charge 4 = **3.750000 %** | period-1 fee **0.41**, not 810.00 |
| AP-6 | `{"chargeId": 1, "amount": 12345.67}` | charge 1 = **15000.000000** | disbursement fee **12345.67**, not 15,000 |

Consequence: `attestation.json`'s `charges_as_persisted` block — 12 rows each carrying a
`persisted_row_sha256` — is load-bearing provenance for `charge_time_enum`, `charge_calculation_enum` and
`is_penalty`, and is **not load-bearing for a single money value in the set**. And because T40 always made
the two equal, **no capture in the corpus can distinguish "the definition governs" from "the request
governs"**; a Go port that read the definition's amount passes all 21 and is wrong. **Required change:**
the vector's fixture is the **request bytes**, not the definition row, and the admissibility record must
say so.

### **A-4 (P1) — C5 is a discrimination probe, not an invariant; carried forward it becomes an assertion DEC-1 §9 forbids.**
Judged as the brief asked. **In T40's favour on the facts:** C5 *failing* is exactly what produced D-1,
T40 ran before T41 decided, and `invariants.py` is demonstrably failable *because* C5 fails. As a probe it
is the most valuable instrument in the set. **But as an invariant it is wrong about the oracle** — T41's
ratified C-1 obliges that *"no adapter, harness or conformance check may assert it equals the sum of the
rows"* — and its PASSes carry no information: the 6 captures where it passes pass for three unrelated
reasons (nothing landed at all: FC-17, FC-20; disbursement-only: FC-01, FC-03; separated-path only:
FC-19, FC-21). A green C5 says nothing about a port. **A correct Go port, discarding
`totalRepaymentExpected` per C-1, would fail C5 on 15 of 21.** **Required change:** relabel C5 a
discrimination probe recording the signed delta `TRE − Σ rows` per capture (0 on 6, `−543,706` to
`−5,190,000` minor units on the other 15), and do not ship `invariants.py` with C5 in it as the
conformance harness for a promoted charges corpus.

### **A-5 (P2) — §11's arithmetic proof that no half-cent tie exists at that base is false, and one was found.**
The handoff proves *"a tie needs `216 × p` to end in `…5` at the third decimal, and `216p` is even for
every terminating decimal `p`"*. It is not: `p = 0.001875 %` gives exactly `0.405` on period-1 interest
`21,600.00`, and the live oracle returned **0.41** — `HALF_UP`; `HALF_EVEN` would give `0.40`. So the
in-charge-arithmetic rounding-mode canary T40 declared impossible **exists and has now been observed**.

### **A-6 (P2) — the disbursement row serialises charge fields at the underlying `BigDecimal` scale.**
`0`, `15000`, `14814.000000` on the wire, against the handoff's 2-dp rendering; every T40 tool normalises
scale away, so only the SHA-256s can see it. Same family as the known `totalOutstandingAmount` scale-0
fact — **response scale is ungraded**.

### **A-7 (P2) — 15 of 19 `bin/` scripts hard-code T40's ephemeral worktree path**, so the shipped run
recipe breaks the moment softhouse prunes that worktree. A recipe that cannot be re-run is not a recipe.

### **A-8 (P2) — the `c_configuration` row and the `MoneyHelper` init line are listed as two assertions
but are one ambient witness** — the T37 shape again (see F39-2; the mechanism is `MoneyHelper.java:59-64`
writing the cache and logging from the same local). Rule 6 is nonetheless satisfied here, because T36's
half-cent canary is real behavioural evidence and on Path B the ambient **is** the arithmetic.

### **T44-X1 (P2, cross-cutting) — the Path B captures are float-shaped on the wire.**
Measured, not asserted [`audit-t44/analysis/t44_float_scan-output.txt`,
`t44_float_roundtrip-output.txt`]: every charges response carries **207–214 bare (unquoted) non-integer
JSON numbers** — 9,122 occurrences, 245 distinct literals, max scale 6 — because Fineract's REST layer
serialises `BigDecimal` as a JSON *number*. The Path A payloads (`periodratio`, `mathcontext`) carry
**0**: every money leaf there is a JSON *string*.

Consequence: any consumer that parses a Path B capture without forcing exact decimal parsing constructs
binary floats, which the project rule forbids outright. Today **0 of 245 literals change VALUE** on a
float round-trip, but **41 of 245 change TEXT** (`"1200000.00" → 1200000.0`), and the rule is *integer
minor units, exact text*. T40's own tools do force `parse_float=Decimal`/`str` and are clean; the hazard
is inherited by whatever consumes the promoted vectors — including the Go conformance harness, where
`encoding/json` into `interface{}` yields `float64` by default. **Required change:** the admissibility
record must state that Path B vectors are compared as exact decimal text, never through a JSON number.

## 2.3 Checked and found CLEAN

11/11 live re-issues byte-identical (incl. the 403 body) plus the control; preconditions byte-verbatim
T36 and **proven failable**; independent C1–C10 matching cell for cell; the 336-leaf diff reproducing
every moved-leaf count; all seven Q5 bases and both rounding-locus gaps recomputed exactly; D-2a/D-2b
byte-identity re-verified four ways; determinism 21/21 across three committed issues; **> 60 published
numbers traced to raw JSON leaves with zero synthesised values**; every cited source line verified
**except A-2**; the 12 charge rows matching `m_charge`; SELFCHECK's ten assertions confirmed; the write
surface exactly `capture/charges/**` + its handoff [VERIFIED: `git diff --name-only` from the merge base].
Three audit probes (AP-1/2/3) additionally **close one of T40's own `[UNVERIFIED]` items in its favour** —
the separated path uses `(from, due]` for every period and loses only period 1's `fromDate`.

## 2.4 Admissibility — `charges`

**Admissible as raw observations now.** As parity vectors after G-1 **only if** three things hold:
(i) the vector is `(request bytes → response bytes)` — the request carries the charge amount (A-3);
(ii) `totalRepaymentExpected` is **discarded** per DEC-1 C-1 and **C5 is removed from the harness** (A-4);
(iii) comparison is exact decimal text, never a JSON number (T44-X1). 17 of the 21 responses are distinct.

**FC-17 and FC-20 must be labelled NEGATIVE vectors only.** Both are byte-identical to the zero-charge
control, so **an adapter that ignored the `charges` array entirely passes both**. They record a behaviour;
they cannot grade one.

**Blind spots:** one loan shape underneath all 21 (principal `120000000`, interest `14498847`,
`loanTermInDays` 365, 12 periods) — term, rate, frequency and anchoring are all ungraded here; **0 of 39
percentage roundings is a rounding tie**, so nothing in the committed set discriminates `HALF_UP` from
`HALF_EVEN` *inside charge arithmetic* (A-5 supplies the shape that would); "period principal+interest"
vs "the EMI" is unseparated even on product 2; response scale ungraded (A-6);
`OVERDUE_INSTALLMENT` (the operationally important penalty), tranche/multi-disbursement charges,
`minCap`/`maxCap`, the cumulative generator and `Asia/Hovd` all remain **`TO_BE_CAPTURED`**.

---

# 3. `mathcontext` (T42) — **ACCEPTED WITH REQUIRED CHANGES**

**Judged under T42's own eight-point rule, as the brief required — and the rule is the right rule.**
Both experiments reproduce, both payloads re-execute byte-identically, and the deployed-bytecode Path B
wiring is real. What fails is narrower and specific: **the inventory in N-3 is miscounted, the coverage
rationale behind the decisive experiment is refuted by T42's own data, and T42 breaks its own rule 2 on
the capture that carries that experiment.**

Full working: `.softhouse/capture/audit-t44/mathcontext/AUDIT-MATHCONTEXT.md` and the parent auditor's
independent checks in `.softhouse/capture/audit-t44/analysis/T44-mathcontext-parent-checks.md`.

## 3.1 What was re-run

- **Both payloads re-executed in throwaway `--rm` containers: byte-identical** (`f2a037a1…`,
  `f7ffeb2a…`).
- **Negative legs N4 and N5 re-run**, both exit 1 naming the breach — including N5, which proves the
  Path A / Path B labels are checked against the object actually handed to the generator.
- **The Path B wiring re-read off the deployed bytecode** with an independent `javap` inside
  `fineract-fineract-1`: class sha256 `d5ef3989…711ea`, the same local slot 9 loaded into `generate`.
  T42's linchpin claim holds.
- **E1, E2 and §3 recomputed** with an independent exact-`Decimal` tool; the cell totals
  `3,820 + 90,528 + 147,676 + 1,284 = 243,308` and `238,204` all reproduce.
- **Nine property invariants clean over 352 observations**, suite proved failable; 105 control cells
  re-transcribed from primary sources.
- **Independently by the parent auditor:** E1 reproduces exactly — all 13 `-D` cases record the ambient
  read throwing (so the probe is live, not vacuous), **11 generated a schedule anyway** and **2 threw**,
  and the 2 are exactly the 0-dp + `inMultiplesOf` shapes. The headline separating pair is in the
  payload at the published values (`274527298.56` / `274527296.51`). T42 §4 leg 2 confirmed:
  `"currencyDecimalPlaces": 0` appears in **no** committed capture outside T42's own, and the one
  committed file with a positive `currencyInMultiplesOf` records 2 dp on all 13 cases — so the Path A
  ambient leak is unreachable in the committed corpus.

## 3.2 Findings

### **M-1 (P1) — N-3's `new MathContext(…)` inventory is miscounted, and the wrong total is already in `reference-oracle.md`.**
*Found independently by both audit legs, with no shared context.* N-3 publishes **9**
`new MathContext(10, …)` sites; there are **5**. The nine `file:line`s it lists are the **union** of the
four precision-15 and five precision-10 sites, all labelled as 10s — `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:526`,
`:822`, `DepositAccountWritePlatformServiceJpaRepositoryImpl.java:496` and
`SavingsAccountDomainServiceJpa.java:329` are precision **15**. `reference-oracle.md` has folded in the
derived total as *"**13** `new MathContext(15|10, …)`"* (4 + 9, double-counting the 15s); **the correct
total is 9**.

**What does hold, checked independently:** `MathContext.DECIMAL64` = **81** (49 `fineract-core` +
31 `fineract-provider` + 1 `fineract-savings`), **0** in any loan module, **0** outside a savings/deposit
path; **4** × precision 15; and N-4's `AdvancedPaymentScheduleTransactionProcessor.java:2845` really is
the loan modules' only hard-coded `MathContext`.

**P1 because N-3 exists to steer the Tier B savings port** — an inventory is the one part of it a porter
will actually use, and `patterns.md` is explicit that a transcription may never be wrong.

### **M-2 (P1) — N-3's universal claim is false: precision 8 exists, and one site is not in savings/deposits.**
*Also found by both legs.* N-3 says *"Every hard-coded `MathContext` in main source outside the loan
modules is in savings/deposits."* Two `new MathContext(8, MoneyHelper.getRoundingMode())` sites are
omitted from the finding entirely: **`SavingsAccountCharge.java:562`** (`fineract-savings`) and
**`ShareAccountCharge.java:240`**, which is in `portfolio/shareaccounts/` — **share accounts, a separate
Tier B context with its own precision**. A porter reading N-3 would carry `(19, HALF_UP)` into share
accounts and be wrong there too, which is precisely the error N-3 was written to prevent.

### **M-3 (P1) — the coverage rationale behind the decisive experiment is refuted by T42's own observations.**
`CaptureMathContext.java:163-166` says the E1 shapes were chosen so that *"between them they REACH every
ambient-context read the static scan found on the Path A call graph"*, and `:179-181` justifies the
`installmentAmountInMultiplesOf` shape as the one reaching the three-argument
`Money.roundToMultiplesOf` and its trailing two-argument `Money.of`. **That site was never reached.**

Observed in T42's own payload: `T42-MX-00-A` (plain) and `T42-MX-06-A` (`multiples1000`) differ in
exactly one input — `installmentAmountInMultiplesOf` `null` vs `1000` — and their observations differ in
**0 cells**; period-1 total is `212787.28` on both, which is not a multiple of 1000. The cause is the
already-known Path A blind spot: `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
never sets it, so `ProgressiveLoanScheduleGenerator.java:110` reads `null`. Had the site been reached,
the ABSENT case would have thrown exactly as the 0-dp cases did.

Two consequences: **(a) N-1's second half is over-tagged** — *"The same pattern appears again at
`Money.java:161-171` … **This is a port hazard, and it is observed, not read.**"* The stack trace
evidences `Money.java:154` only; the second site is a **transcription** and must read
`[UNVERIFIED as behaviour]`. **(b) Distinct coverage is 10, not 13** — four of the thirteen `-A`
observations are byte-identical to `plain` (`plain`, `multiples1000`, `fixedLength6`,
`interestRecognitionOnDisb`), so three of the levers chosen to widen coverage had **zero** observable
effect, and the `installmentAmountInMultiplesOf` ambient path appears nowhere in §3's
`TO_BE_CAPTURED` list because T42 believed it captured.

**The headline "11 of 13 shapes provably never read the ambient context" remains true** and is correctly
qualified in T42 §7. What fails is the reason for believing those thirteen shapes were the right thirteen.

### **M-4 (P1, new oracle fact for DEC-1) — a second production site silently drops `installmentAmountInMultiplesOf`.**
Falling out of M-3 and worth raising separately because no task has recorded it. **Stated with care, so
it does not appear to contradict an attested observation:** the REST `calculateLoanSchedule` path via
`LoanScheduleAssembler` **does honour** the field — that is capture `B-02`, `112,082.37 → 112,100.00`,
and nothing here disturbs it. But **`LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement`**
is a *different* production entry point on the multi-disbursement interest-only path, and it
**inherits Path A's blind spot** [VERIFIED by me on the pinned source]: `:56` passes
`loanProductRelatedDetail.getInstallmentAmountInMultiplesOf()` into the
`LoanRepaymentScheduleModelData`, `:63` calls `scheduleGenerator.generate(mc, modelData)`, and
`assembleFrom(modelData, mc)` drops it. So the field is honoured or lost **depending on which production
caller builds the schedule**. `TO_BE_CAPTURED`, and DEC-1 should not state the field's behaviour
unconditionally.

### **M-5 (P2) — T42 fails its own ratified rule 2 on the capture that carries the decisive experiment.**
*Found independently by both legs (parent's M-P1).* `CaptureMathContext2.java:203-205` complies fully —
it writes `mc.toString()`, `mc.getPrecision()`, `mc.getRoundingMode()` **and** an explicit `wiring` field,
and is the best-attested capture in the program. `CaptureMathContext.java:394-395` does not: it writes
`c.precision()` and `c.mode()` — the case record's **intent** — under keys named
`threadedMathContextPrecision` / `threadedMathContextRoundingMode` that assert otherwise. **214 of the
354 cases** are attested that way, and capture 1 is where E1 lives.

Materiality is low and should be said plainly: the ambient field in capture 1 *is* read off the object,
the two stack traces are direct observations, and E1 is an **absence** result that does not depend on the
threaded echo. No value is affected. It is the same defect as **F39-3** against T39 — which suggests the
two harnesses share the ancestor that has it.

### **M-6 (P2) — E3's only machine assertion is `grep -c 'getMathContext' != 0`.**
The same-local-slot claim — the actual content of the ratified Path B row — is **unasserted and has no
negative leg**. It was hand-verified by the audit leg and it holds, but a claim that carries a ratified
rule should be machine-checked.

### **M-7 (P2) — "no committed capture is mis-valued" is unqualified where it is ratified.**
T42's verdict and `reference-oracle.md` state it flatly while T42 §7 qualifies it correctly
(`[VERIFIED for the three legs stated; UNVERIFIED as a re-run]`). Leg 1 is a **self-report** of exactly
the class T42 refuses elsewhere — it cites T35's, T37's and T39's own attestations that they echoed the
threaded context, and F39-3/M-5 show that claim is weaker than stated for at least T39. Legs 2 and 3 do
carry the conclusion, so it stands; the qualification must travel with it.

### **M-8 (P2) — `NEGATIVE-TESTS.md` mis-describes what N4 proves.** It says N4 fires the "probe is
VACUOUS" guard; it fires the opposite branch. **The vacuity guard has never been exercised** — and it is
the guard that makes E1 falsifiable.

### **M-9 (P2) — four `file:line` drifts inside `[VERIFIED]` tags**: `Money.java:152-158`→`:150-157`,
`:161-171`→`:163-170`, `:49-51`→`:48-50`, `MoneyHelper.java:37`→`:38`; and *"pass it to
`generate(mc, …)`"* is wrong for 2 of the 4 ratified wiring sites.

### **M-10 (P2) — E2's "Path A = 0 cells" is a replication of E1's ambient rows**, not a second
experiment: identical inputs, 0 differing cells, presented as independent corroboration.

### **M-11 (P2) — `controls-output.txt` publishes 2 summary lines, not the 172 compared cells**, so the
control claim cannot be checked from the committed output alone.

## 3.3 Checked and found CLEAN

Both payloads byte-identical on re-execution in fresh containers; every E1/E2/§3 number and all four cell
totals recomputed independently; N4 and N5 re-run and both fail correctly; the deployed-bytecode wiring
re-read with an independent `javap` (`d5ef3989…711ea`, slot 9 → `generate`); nine property invariants
clean over 352 observations with the suite proved failable; 105 control cells re-transcribed from primary
sources; N-3's DECIMAL64 arithmetic exact (81 = 49 + 31 + 1, 0 in loan modules, 0 outside savings) and
N-4's `:2844-2845` confirmed; the 2 throwers are exactly the 2 zero-dp shapes and the 11 that generated
all ran graded arithmetic; the Path A ambient leak confirmed unreachable across the whole committed
corpus; PostgreSQL-only and no-float discipline clean; write surface exactly
`capture/mathcontext/**` + its handoff.

**And the rule itself is sound.** Nothing in this audit disturbs the eight-point attestation rule; the
absence-over-difference technique is genuinely stronger than what preceded it, and applying it to T39
and T40 is what produced F39-2, A-1 and A-8.

## 3.4 Admissibility — `mathcontext`

**Promote, once G-1 closes: `T42B-PREC-30-p19`** (MNT 50,000,000 / 360 / 21.6 % at threaded
`(19, HALF_UP)`), full 861 cells — the only artefact in the program that makes Buyan's ratified
precision-19 parameter falsifiable. With it: its `-p12` sibling kept as a **labelled discrimination
probe**, and — because separation is **non-monotone in principal** — at least two *non-separating*
neighbours (30 M, 80 M) so the vector cannot be passed by a port that merely happens to land on a
matching residual. A precision-12 port still matches on 30 of 62 shapes, so a single shape is not a
sufficient vector.

**Not promotable:** the matrix family, the absence cases, the wiring-PB cases, the `-p8`/`-p12`
families and `T42-CAL` (all discrimination probes or off-ratified-settings), and the four duplicate
controls.

**Blind spots**, the largest being the one this audit found:
`installmentAmountInMultiplesOf` was **believed covered and is inert** (M-3), so the three-argument
`Money.roundToMultiplesOf` ambient path is ungraded; the E1 matrix carries 10 distinct observations,
not 13; the **Path B transport was not exercised at all** by T42 (its own §7 says so) — every Path B
claim rests on bytecode plus T36's committed canary; `RepaymentEvery > 1`, the `WEEKS`/`DAYS`/`YEARS`
arms, `SAME_AS_REPAYMENT_PERIOD`, multi-disbursement, interest pause, term variations and **charges**
are all out of reach of `LoanRepaymentScheduleModelData`; precisions other than {19, 12, 8} and modes
other than {HALF_UP, DOWN, UP, HALF_EVEN} are untried; and N-4's hard-coded `RoundingMode.DOWN` in
repayment allocation remains `TO_BE_CAPTURED`.

---

# 4. Method

Three legs ran in parallel on disjoint write surfaces, with the parent auditor also running its own
checks on the `mathcontext` set so that the most consequential claims had two independent looks. Every
leg was told to re-derive rather than re-read, to re-run rather than trust committed output, and to run
each shipped recipe in a **failing** configuration. Three recipes were exercised negatively —
T39's (seam-sha and threaded-mode legs), T40's preconditions (tenant `default`), and T42's N4/N5 — and
**all three failed correctly, naming the breach**.

Nothing was written outside `.softhouse/capture/audit-t44/**`,
`.softhouse/reviews/T44-capture-audit.md` and `.softhouse/handoff/T44-capture-audit.md`. The running
containers were read (`javap`, read-only `psql`, read-only REST calculation calls) and never restarted,
re-tenanted or written to; charge definitions 1–12 on tenant `gerege` were left exactly as T40 made them
(`m_charge` 12, `m_loan` 0, nothing created).

**Write-surface discipline of the three audited sets, checked with `git diff --name-only` from each
branch's merge base:** T39 authored exactly `capture/periodratio/**` + its handoff; T40 exactly
`capture/charges/**` + its handoff; T42 exactly `capture/mathcontext/**` + its handoff. **All three
clean.**

---

# 5. Unverified

- **That my independent model is a complete specification of the graded path.** It predicts the
  *interest* column from the previous row's observed balance; it does not model the EMI solver, the
  re-adjust loop or principal allocation. It reproduces 131 of 132 interest cells and the one miss
  is common to all four readings. `[VERIFIED for the interest column on these 16 captures;
  UNVERIFIED as a general model]`
- **That R2 and R4 coincide everywhere**, rather than on the swept domain. Verified on 59,130
  `(start, period)` pairs, 2023-2025, terms {6, 12, 36}, `RepaymentEvery = 1`, MONTHS. The
  mechanism (the `+1 day` nudge equals the packed rule's month-end undercount) is a re-derivation
  from `:1432-1433` and `LocalDate.monthsUntil`, not an exhaustive proof.
  `[VERIFIED on the swept domain; UNVERIFIED outside it]`
- **T39's 415 / 116 full-cell counts** are reproduced from `analysis/discriminate-output.txt:176-177`
  as committed output. My independent count is on the **interest column only** (39 R1 failures,
  11 R3 failures) and is not the same statistic, so it corroborates the direction and sign but does
  not re-derive the totals. `[VERIFIED as committed output; UNVERIFIED as an independent recount]`
- **N-2's 51,729-pair sweep** — not reproduced (see §1.5 blind spot 9).
- **Generalisation.** Sixteen captures grade sixteen shapes. Nothing here licenses a claim about an
  unsampled `(startDate, disbursementDate, principal, term, rate)` tuple.
- **Whether the packed-vs-naive blind spot is the last one in this family.** T39's R2 was
  15-of-16 clean before it was attacked with a fourth reading; assume a fifth exists.
- **The `charges` and `mathcontext` legs were run by delegated auditors**, and their findings are
  reported here on their evidence. I independently re-verified the ones a ratified artefact rests on —
  **A-2** (`AbstractCumulativeLoanScheduleGenerator.java:392` + `ScheduleCurrentPeriodParams.java:144-145`
  against the cited `:504`), **M-1/M-2** (the full `new MathContext(…)` site listing and the DECIMAL64
  breakdown), **M-3/M-4** (`LoanScheduleGeneratorServiceImpl.java:44-63`), **M-5** (the two harnesses'
  echo lines), and E1's 11/2 split — and each held. **A-1, A-3, A-5, A-6, A-7, A-8, M-6 … M-11 I did
  not re-verify myself.** `[VERIFIED on the leg's evidence; UNVERIFIED by the parent auditor]`
- **T44-X1's value-loss measurement** is over the 245 distinct literals present in the committed
  charges captures at their current magnitudes and scales. It says nothing about a payload with larger
  magnitudes, and the "0 of 245 change value" result must not be read as "floats are safe here".
- **Whether A-3's request-over-definition precedence holds for every charge type.** It is observed on
  one percentage charge and one flat charge. `[VERIFIED on those two; UNVERIFIED as a general rule]`
- **This audit's own coverage.** I found what these three sets fail to distinguish where I thought to
  look. Every prior capture audit in this program found something, and so did this one; that is a
  statement about how often these corpora are narrower than claimed, not a guarantee that the list is
  now complete.
