# Human decision gates — gerege-nbfi migration

`/softhouse-program` appends a block here whenever it reaches a `user` gate, then parks that context and moves to the next unblocked one. **No automation crosses a gate.** Buyan resolves them here (or in the run report) and the next fire picks the context back up.

Gate classes that always stop:
- **CUTOVER** of any context from Fineract to Go — requires vectors passing + a clean shadow-parity window + regulatory / parallel-run sign-off.
- **CONTRACT** — ratifying or amending DEC-n / the frozen adapter contract.
- **REGULATORY** — FRC / external-audit acceptance, parallel-run sign-off.
- **ACTIVATION** — enabling deposit-taking behavior (FRC / Bank of Mongolia licensing). Porting savings code is not gated; switching it on is.

---

## Open

### G-1 · CONTRACT · ratify DEC-1 — **NOT YET ANSWERABLE**

| | |
|---|---|
| Gate class | CONTRACT (ratify / amend DEC-n) |
| Task | T6, run `2026-08-17-run1-harness-schedule-poc` |
| Context | `tier0-harness-schedule-poc` — **blocked**, and with it every other context (all 16 declare tier 0 as a transitive dependency) |
| Raised by | cloud fire `20260817-2000` |
| State | **Do not answer this yet.** The draft was independently reviewed and **REJECTED** (T5). It must be corrected and a discriminating vector captured before ratification is a meaningful question. |

**Why it is not answerable.** Ratifying DEC-1 as drafted would freeze an ambiguity that provably changes money:

- Fineract threads **one** `MathContext` and consumes it in **two incompatible senses** — significant digits in every `multiply/divide(…, mc)`, and **decimal places** in `setScale(mc.getPrecision(), …)` at `ProgressiveEMICalculator.java:1962` and `:1979` (the only two such sites in main code, both on the per-period rate factor). DEC-1 defines the field in the first sense only.
- T5 computed both readings across 560 configurations. At precision 12, three diverge in a **payable amount** — first at 18 installments / 18.5 % p.a. / principal 87,654,321 (an ordinary Mongolian SME size), where period-5 principal is `4,531,420.25` under the correct reading and `…​.26` under the contract's. The one-minor-unit error appears in period 5 and **never heals**, ending in a different final principal. Across precisions 8/10/12/15/16/19, **189 configurations diverge**.
- **The shipped conformance vector does not discriminate between the two readings.** The corpus cannot currently detect this defect class — which is why "the golden test passes" is not evidence here.

**What was proven (both reviewers re-derived independently, no shared context):**

- The headline arithmetic is right: EMI `17.01`, all six splits (`16.43/0.58`, `16.52/0.49`, `16.62/0.39`, `16.72/0.29`, `16.81/0.20`, `16.90/0.10`), term 182 days, total interest `2.05`. Reproduced digit-for-digit by T3b and T5 separately.
- The golden test round-trips through the contract completely — 19 oracle inputs map to 13 fields + 6 pinned constants; principal `100` encodes as `10000` integer minor units.
- No non-negotiable is violated anywhere in `contract.go`; `go build` and `go vet` pass.
- **Independent corroboration:** T3b and T5 — different reviewers, different artefacts — both refuted the claim that `allowFullTermForTranche` is a dead field. The builder setter reaches it (`LoanApplicationTerms.java:606`) and the guard at `ProgressiveEMICalculator.java:142-144` never consults `isMultiDisburseLoan()`. Pinning it to `false` stays correct, but it is a **behavioural obligation to be conformance-tested**, not an absent input.

**What unblocks this gate**, in order:

1. Capture a **discriminating vector** from the reference oracle — one whose expected output differs between the two readings (T5 supplies the exact configuration). This needs the live oracle, so only an oracle-reaching fire can do it. Until it exists, no correction can be *proven* right.
2. Run the **T4 retry** (attempt 2 of 2; DEC-1 is an unratified DRAFT, so correcting it is agent work, not a gate) against T5's nine required changes.
3. Re-review, then bring the gate back.

---

### Decisions only Buyan can make — needed *before* step 2 above

An agent must not pick these; the T4 retry is parked on them.

1. **`IntermediatePrecisionDigits`: rename or re-document?** T5 recommends renaming to `IntermediatePrecision` and documenting both senses normatively (proposed wording in review §1.5). The alternative is keeping the name and carrying the dual sense in the doc comment. Renaming a field of a soon-frozen contract is cheap now and expensive later.
2. **Ordering rule fix** — the current rule is refuted when a disbursement lands exactly on a repayment due date (half-open window, `ProgressiveLoanScheduleGenerator.java:307-308`). Choose **(a)** reproduce the oracle's emitted order, or **(b)** reject such a request at the boundary.
3. **Must the discriminating vector be captured before ratification?** T5 recommends yes, and I agree — the corpus demonstrably cannot detect this defect class today. Saying no means ratifying on re-derivation alone.
4. **`DayCountActualActual`** — does it stay in the Run-1 contract domain while unvectored, or come out until it has vectors?
5. **`allowFullTermForTranche`** — accept as a conformance obligation (pinned `false`, and tested to stay false) rather than a dead field?
6. **The live tenant's actual rounding mode** — unresolvable from source. `application.properties:77` defaults to `6` (`HALF_EVEN`), but the tests mock `HALF_UP`, and production `MoneyHelper.PRECISION` is `19` while the tests mock `12`. Capture must assert what is really in force; someone has to state what the Mongolian tenant will be configured to.

---

### G-1 · UPDATE from local fire `20260818-152328` — the gate has moved, but is still not answerable

**Two capture passes now exist against the pinned oracle.** Both are RAW OBSERVED via Path A (the
embeddable seam, in-process, no database — see `.softhouse/reference-oracle.md`). **Both are still under
independent audit (T18 for pass 1, T19 for pass 2). Nothing below may be treated as settled until those
land, and no vector has been promoted to the store.** Recorded now so the next fire does not re-do the work.

Artefacts: `.softhouse/capture/out/capture-raw.json` (pass 1, 9 captures),
`.softhouse/capture/out/capture-tenant-raw.json` (pass 2, 13 captures),
`.softhouse/capture/PASS2-REPORT.md`.

**Calibration passed.** Pass 1's `C-00` reproduced the shipped expectation on the nose — EMI `17.01`,
splits `16.43/0.58`, `16.52/0.49`, `16.62/0.39`, `16.72/0.29`, `16.81/0.20`, `16.90/0.10`, term 182 days,
total interest `2.05`. Pass 2 reproduced it again from a separate harness, with and without a tenant
context. The rig is calibrated against the only literal the corpus attests.

#### What the captures now say about the six reserved decisions

| # | Decision | Status after capture |
|---|---|---|
| 1 | Rename `IntermediatePrecisionDigits`? | **Unchanged — still yours.** Naming, not arithmetic. But see the new decision 7: whatever the field is called, precision is now *observed* to be load-bearing. |
| 2 | Ordering rule: reproduce the oracle's order, or reject the request? | **Now informed by observation.** With `scheduleGenerationStartDate = 2024-01-01` and `disbursementDate = 2024-02-01`, the oracle emits a **zero-valued REPAYMENT period 1 dated 2024-02-01 *before* the DISBURSEMENT period on the same date**, then numbers the real repayments **2..6** — five paying installments, not six, and totals `1.76` interest on `101.76`. Horn (a) is now a concrete, capturable behaviour rather than a guess. The choice is still yours. |
| 3 | Must the discriminating vector be captured *before* ratification? | **Satisfied — and it settled the question against DEC-1.** Pass 1 ran T5's exact configuration (18 × 18.5 %, principal 87,654,321) at precisions 8, 12 and 19, and the T18 auditor independently re-derived all three and reproduced the oracle exactly. **DEC-1 as drafted is empirically wrong by one minor unit**: at precision 12 the oracle emits period-5 principal `4,531,420.25` / interest `1,082,346.53` and final principal `5,528,535.21`, where the significant-digits-only reading DEC-1's text describes emits `…26` / `…52` / `5,528,535.20`. **Read the caveat below before citing this.** |
| 4 | Does `DayCountActualActual` stay in the Run-1 domain while unvectored? | **Unchanged — still unvectored, still yours.** |
| 5 | Accept `allowFullTermForTranche` as a pinned-`false` conformance obligation? | **Now confirmed live by the running oracle** — a third independent confirmation, and the first that is not a source reading. Pass 1's `D-04` (`true`) *crashed* for want of a tenant context, proving the `true` branch executes different code that reaches `MoneyHelper`. Pass 2 supplied a tenant: it then runs, and is **schedule-identical** to `false` on single-disbursement loans at both small and large principal. So "pinned `false` as a tested obligation" is now the evidence-backed reading. Its behaviour on a genuine multi-disbursement loan remains **uncaptured** — Path A cannot express more than one disbursement. |
| 6 | The Mongolian tenant's actual rounding mode | **Still unanswered, and we now know why it is hard.** `HALF_EVEN` (the `application.properties:77` default, `6`) and `HALF_UP` (what the tests mock, `4`) produced **identical output in every pass-2 pair**. Read narrowly: the ambient `MoneyHelper` context (observed as `precision=19` + tenant mode) does not reach the arithmetic on these inputs through this seam. The two paths that *do* consult it are exactly the two Path A cannot exercise. **The question that most needs answering is the one still out of reach.** |


> **Correction, recorded by the T18 audit — an orchestrator over-claim.** A precision **sweep** cannot by
> itself separate the two *senses* of the `MathContext`, because one integer drives both. And there is a
> trap in the obvious reading: the sense-1 schedule at precision 12 is **identical** to the oracle's at
> precision 19, so treating the `D-01` vs `D-01-p19` delta as "the sense difference" is **wrong**. The
> discrimination is real, but it exists only because the counterfactual sense-1 schedule was computed
> *outside* the oracle — and that counterfactual is **not in the captured artefact**. Any conformance
> vector claiming to pin the sense question must carry it explicitly, or it pins nothing.

#### NEW — decision 7, raised by pass 2, and it is the most serious thing found this fire

**`installmentAmountInMultiplesOf` is accepted by the capture seam and silently dropped.**

`LoanRepaymentScheduleModelData` is a 19-component record. `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
(`LoanApplicationTerms.java:579-606`) — the only entry the seam uses (`ProgressiveLoanScheduleGenerator.java:82`) —
reads 18 of them and never calls `modelData.installmentAmountInMultiplesOf()`. Observed behaviour matches:
supplied as `100`, as `1`, and through `CurrencyData.inMultiplesOf` as well, it moved **no figure at all**,
including on a 100-unit loan whose `17.01` EMI could not survive rounding to multiples of 100 unchanged.
The *server* path does honour it (`LoanApplicationTerms.java:1301-1305`, `:1617-1618`;
`ProgressiveEMICalculator.java:1763-1764`; `Money.java:154`).

Why this is a contract question and not a bug report: a Go port could **honour** the input (matching the
server) or **ignore** it (matching the seam) and score **identically** against every vector Path A can
produce. That is exactly the defect class T5 found for precision-vs-scale — a contract input the grading
corpus provably cannot discriminate — now in a second field, on a parameter Mongolian products would
routinely use (installments rounded to the nearest 100 ₮).

**Asking for:** which of these, before DEC-1 is frozen —

- **(a)** Build **Path B** capture (running Fineract server + PostgreSQL) for the inputs Path A drops, and
  keep `installmentAmountInMultiplesOf` in the contract domain. Correct, and materially more capture rig
  than Tier 0 budgeted for.
- **(b)** Take the field **out** of the Run-1 contract domain until Path B exists, and pin it absent — the
  same treatment decision 4 proposes for `DayCountActualActual`.
- **(c)** Keep it in the domain, pinned to `null`, as a conformance obligation tested to stay `null` — the
  treatment decision 5 proposes for `allowFullTermForTranche`.

**The orchestrator's recommendation is (b) or (c), not (a), for Run 1** — Tier 0 exists to prove the
pipeline on the smallest real slice, and standing up Path B inside it would defeat that. But this is a
contract-domain decision and therefore yours. Whichever you choose, DEC-1 should state, for **every** input
in its domain, whether the grading path honours it: an input the contract exposes but the corpus cannot
test is unconformance-testable by construction, and that fact belongs in the frozen document.


> **Update after the T19 audit — decision 7 is broader than first stated, and two of its arguments were wrong.**
>
> - **The seam honours 17 of the contract's 19 inputs, not 18.** A **second** input is silently dropped:
>   `daysInYearCustomStrategy` **is** read by `assembleFrom` (`:604`), so it passes the "never read" test,
>   but the `Builder` **copy-constructor** (`:304-351`) never copies it out. A reflective read returns
>   `null` and a leap-year differential confirms `FULL_LEAP_YEAR` == `FEB_29_PERIOD_ONLY` == `null`.
>   The defect is therefore a **class** — an unchecked, hand-maintained builder copy — not one field.
>   Buyan's answer (expose, specify server semantics, refuse until Path-B vectored) applies unchanged to
>   both fields, but it now covers two.
> - **The claim is now proved rather than inferred.** The auditor assembled `LoanApplicationTerms` through
>   the seam's own overload and read `installmentAmountInMultiplesOf` reflectively as `null`.
> - **Two supporting arguments were wrong and are withdrawn.** (i) "A `17.01` EMI rounded to multiples of
>   100 cannot be a no-op" — it can: `safeRoundingForEMI` (`:1770-1776`) returns the unrounded EMI when
>   rounding would zero it. The conclusion survives on `T-IM1-he` and the MNT pair. (ii) "Ruled out through
>   both channels" — `CurrencyData.inMultiplesOf` is gated on `decimalPlaces == 0` (`Money.java:48-51`) and
>   the harness hard-codes `2`, so that channel was structurally inert. At `decimalPlaces = 0` it *does*
>   move the schedule, so "uncapturable through this seam" was too broad as written.
> - **The "server path honours it" citations were misattributed** — they point at the *cumulative*
>   generator, not the *progressive* one being ported. The normative specification Buyan asked for must
>   cite the progressive path.
>
> The auditor's own summary is the sharpest statement of why this blocks ratification: *the seam accepts a
> 19-component contract and honours 17; for the other two the corpus has **zero discriminating power**,
> which is a defect in the conformance rig itself and sufficient reason not to freeze DEC-1 on the premise
> that seam-captured vectors cover the contract's input domain.*

#### What still has to happen before the gate is answerable

1. **T18 / T19 audits land** and the captures are either accepted or sent back. (In flight this fire.)
2. **Buyan answers decisions 1–7.** Several of the T4 retry's nine required changes depend on them.
3. **T4 retry** (attempt 2 of 2) against T5's nine changes plus whatever 1–7 resolve to.
4. **Re-review**, then the gate comes back.

Steps 2–4 have not moved. What changed this fire is that the *evidence* the gate was waiting on now exists,
and one new decision was added that nobody knew to ask.

### G-2 · POLICY · third attempt for the T2 behaviour extraction?

`policy.max_retries_per_task = 1` and `park_after_retries = true`. T2 has now used attempt 1 (rejected) and its one retry (rejected again), so it is **parked by policy** rather than by judgement. Not a money question — a budget one.

The failure is systematic and diagnosable: **the analyst corrected each section the review named, but not the other sections that restate the same claim.** Month-end stepping was fixed in §4.4 and left wrong in §7.4 and the vector matrix; "cancels to 1" fixed in §4.2, left wrong in §7.4. A Go implementer reading the document still meets the original wrong instruction. A third identical attempt would likely repeat this.

**Asking for:** permission for one more attempt with a *different task shape* — apply T3b's ten enumerated edits surgically, then run a mechanical consistency sweep that greps every corrected claim for restatements elsewhere in the document, rather than another free-form rewrite. If the answer is no, the alternative is to treat T3b's review as the specification of record and have the port graded against vectors alone.

## Resolved

_(none yet)_

---

## G-1 update — fire `20260818-173900` (local, oracle REACHABLE)

**Status: still open, but no longer waiting on a question. It is waiting on three named corrections.**

The driver did **not** ratify. Standing policy **P-2** permits ratification on a *clean* independent
review; T23's verdict is `ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable as it stands`. Ratifying
anyway would have been exactly the move the policy exists to prevent.

### What this fire settled

- **DEC-1 v2 exists** and answers the defect that rejected v1. It splits the **contract domain** (every
  value the types admit, frozen by ratification) from the **graded domain** (the subset a capture can
  actually discriminate). §5 now states, for every input, whether the corpus can discriminate it and by
  which capture.
- **The split survived adversarial review.** T23 answered the question that mattered most — can the graded
  domain widen *without* amending a ratified DEC-n? — as **yes**. It is not a loophole around a hard gate.
  Only the *mechanism* for recording a widening is unspecified (P1).
- **The "silently dropped component" worry is closed as a class.** T23 mechanically diffed all 37 `Builder`
  fields against the 36 copied, and all 19 record components: **there is no third dropped component.**
  T19's fear that this was an open-ended defect class is retired.
- **Path B works and grades what Path A drops** (T22). `installmentAmountInMultiplesOf` moves 12/12 periods
  (`B-02`); `daysInYearCustomStrategy` moves the schedule via `FEB_29_PERIOD_ONLY` (`B-04`) — but
  `FULL_LEAP_YEAR` is byte-identical to the field being *unset*, so it remains undiscriminated.
- **A false rounding rule was caught before it froze.** The oracle rounds the EMI to the **nearest**
  multiple under the tenant mode, not up (`Money.java:163-171`), observed rounding **down** at principal
  1,190,000: `111,148.35 → 111,100.00`. DEC-1 would have inherited the error.
- **The size-threshold claim is refuted** (T21). p12/p19 divergence appears at principal **4.00** on the
  36×16.8% shape and is **absent** at 50,000,000 and 87,654,321. There is no threshold, and no shortcut
  may be justified by loan size.

### The three P0 defects that block ratification

1. **The EMI re-adjust loop is live inside the graded domain.** §4.3 says it is reachable only *outside*;
   §9's obligation list omits it. It is called at `ProgressiveEMICalculator.java:749` on **every**
   generation, and its guard compares `|ΔEMI|×100` against a `Money` of amount `floor(n/2)` — because
   `Money.copy(double)` **replaces** the amount — so it does not depend on installment rounding at all.
   **7 of 10 graded-domain requests diverge from the contract as specified**, and **no vector in the corpus
   trips it.** Observed: MNT 1,014,632 / 6 × 7.0% → oracle `172,574.64` vs specified `172,574.63`;
   MNT 127,704 / 36 × 16.8% → total interest `35,746.56` vs `35,746.69`.
2. **A disbursement outside `[ScheduleStartDate, last due date)` is silently discarded** — observed as zero
   disbursement rows and an all-zero schedule. The ordering rule's third clause describes a row the seam
   never emits.
3. **`FrequencyYears` does not always throw.** It throws on the 30/360 arm only; under
   `DayCountActualActual` the oracle returned a full 3-period schedule (term 1096, interest `551,982.62`).
   The refusal's normative justification is false and there is no error-precedence rule.

### What unblocks G-1

`T24` (apply the three P0s + T23's P1 list) → an independent re-review → the driver ratifies under P-2.
**Nothing here needs Buyan.** All three are ENGINEERING, answerable from source and observation, and the
oracle is reachable on the local fire. P0-1 additionally requires *capturing vectors that trip the
re-adjust loop*, which the corpus currently cannot do — that is capture work, not a decision.

### Still RESERVED (unchanged)

Nothing blocking Run 1. Licence (NBFI ББСБ) and rounding mode (HALF_UP) are decided. Cutover, regulatory
sign-off and deposit-taking activation remain hard `user` gates and are not in Run 1's path.
