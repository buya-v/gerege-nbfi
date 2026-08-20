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

### G-2 · POLICY · third attempt for the T2 behaviour extraction? — **CLOSED: DECLINED**

`policy.max_retries_per_task = 1` and `park_after_retries = true`. T2 has now used attempt 1 (rejected) and its one retry (rejected again), so it is **parked by policy** rather than by judgement. Not a money question — a budget one.

The failure is systematic and diagnosable: **the analyst corrected each section the review named, but not the other sections that restate the same claim.** Month-end stepping was fixed in §4.4 and left wrong in §7.4 and the vector matrix; "cancels to 1" fixed in §4.2, left wrong in §7.4. A Go implementer reading the document still meets the original wrong instruction. A third identical attempt would likely repeat this.

**Asking for:** permission for one more attempt with a *different task shape* — apply T3b's ten enumerated edits surgically, then run a mechanical consistency sweep that greps every corrected claim for restatements elsewhere in the document, rather than another free-form rewrite. If the answer is no, the alternative is to treat T3b's review as the specification of record and have the port graded against vectors alone.


#### DECISION — **DECLINED**, local fire `20260820-080002`, 20 August 2026 (`chosen_by: agent`, Buyan may reverse)

Closed by the `/softhouse-program` driver under `CLAUDE.md` § *Answering gates* — this is a **PRODUCT/process**
item with **no RESERVED content**: it is not a cutover, not a DEC-n amendment, not a licence fact, not a
regulatory sign-off. The standing instruction is *choose and recommend, do not ask*.

**No third attempt. T2 stays parked permanently.** The specification of record for the progressive-loan
schedule is, in order: **DEC-1 revision 12** (ratified, frozen in `contract.go`), **the 29-vector parity
corpus**, and **T3b's re-review** (whose re-derivations are sound even though the document it reviewed was not).

**Why, in one line: the artefact is not on any task's dependency path, and the failure mode it exhibits is one
that prose has and vectors do not.**

1. **It has been superseded twice over.** DEC-1 survived ten review rounds to ratification, and T9's
   dedicated hunt for DEC-1/source disagreement audited six places and found **none** — *"where DEC-1 and the
   folklore differ, DEC-1 matches the source."* A third prose attempt would be re-deriving, less rigorously,
   what a ratified and independently re-reviewed artefact already states.
2. **The gate's own diagnosis argues against spending the attempt.** The systematic failure is *"corrections
   land in the section the review named but not in the sections that restate the same claim."* That is a
   defect class **a document has and an executable corpus does not** — a vector cannot restate a claim
   inconsistently in a second section. The program's answer to *"is the spec right?"* is now mechanical:
   mutate the port, see whether the corpus kills it. That loop closed four money-moving mutations last fire.
   Prose cannot be mutation-tested.
3. **Opportunity cost, on the one fire that can reach the oracle.** An opus attempt spent on a superseded
   document is an attempt not spent on corpus expansion — the thing measurably catching defects.

**The real risk in declining was NOT the missing document — it was the existing one, and it was worse than
the gate knew.** The driver read `docs/analysis/progressive-schedule-behavior.md` before deciding and found
the rejected restatements still live, including one that is **refuted by an oracle observation the corpus
already holds**:

> §7.4 told a Go implementer that `2026-01-31 → 02-28 → 03-28` is *"exactly what a Go port's date-stepping
> must replicate bit-for-bit."* **The oracle re-anchors on the disbursement seed.** Parity vector `P-02`
> has period 2 due **`2024-03-31`**. The behaviour §7.4 prescribes is recorded in the corpus as the killed
> counterfactual `MONTHEND-CONTINUE-FROM-CLAMPED-DAY`, and a port built from that paragraph **fails
> conformance** — on the due date, at a money margin of exactly zero, which is why it is graded structurally.

So the document was not merely stale; **it was an instruction to build a known-wrong port, sitting in the
repo's only prose behaviour narrative.** Rather than buy a third rewrite, the driver neutralised the hazard
directly and at no model cost:

- a **⛔ SUPERSEDED — DO NOT IMPLEMENT FROM THIS DOCUMENT** banner at the top, naming the three sources of
  record and stating that unmarked sections carry no warranty;
- inline **⛔ CORRECTION** blocks at the three sites T3b enumerated and the driver re-verified as still
  wrong: §7.4's month-end rule (refuted by `P-02`), §7.4's *"cancel to `1` regardless"* (refuted by the
  §5.1 `setScale` step and by `LB-DEC31`, which separates the ACT/ACT arm by **6,015 minor units**), and
  §8's unpinned MathContext (settled: `(19, HALF_UP)`, and probes at precision 12/8 are never promotable);
- a correction to the `ls-008` row, which restated the refuted rule a fourth time.

**Reversal condition.** If a Tier-A task finds it genuinely needs a prose schedule narrative that DEC-1 and
the corpus do not supply, re-raise this gate with the specific gap named. *"It would be nice to have"* is not
that; a named unanswerable question is.


---

## G-1 · **CLOSED — RATIFIED**, local fire `20260819-140003`, 19 August 2026

**DEC-1 revision 12 is RATIFIED.** Closed by the `/softhouse-program` driver under `CLAUDE.md`'s amended
rule (DEC-n ratification is agent-decidable) and policy P-2. **It never reached Buyan, because it never had
a RESERVED item** — the triage of fire `20260819-080001` established `decisions_reserved_for_user` was
empty, and this fire did not add one. **Buyan retains veto and may reverse this.**

### The ten rounds, because the trend is the argument

| round | revision | verdict |
|---|---|---|
| T5, T23, T26, T29, T32, T34, T37-observed | 1 – 6 | a **new P0 every round**, each on a surface no prior round had examined |
| **T43** | 8 | **no P0** — driver **DECLINED** |
| **T49** | 10 | **no P0**, 3 P1 — driver **DECLINED** |
| **T53** | 11 | **no P0, no P1**, 6 P2 + *"apply the six, then ratify"* |
| T54 applied the six; driver verified each | **12** | **RATIFIED** |

### Why the driver declined twice and then did not

One discriminator, applied consistently: **was a sentence known to be false about to be frozen?**

- Revision 8 — **yes.** P1-T43-3 stated M4 decides which row a *charge* lands on; an `INSTALMENT_FEE`
  consults no membership test and lands on every row (MNT 27,500 on FC-02). The corpus later refuted the old
  reading 13-of-21 → 21-of-21.
- Revision 10 — **yes.** P1-T49-2: `contract.go` and §4.9 both still said the ACT/ACT arm had *"no capture in
  the corpus"* and was un-re-derived. False since revision 5; T48 had captured it on three seams. It sat in a
  **`contract.go` doc comment**, where ratification freezes it.
- Revision 12 — **no.** T53's six were applied and each verified by the driver; T54's two further findings
  were **disposed of, not deferred** (one fixed by the driver before the freeze, one verified already absent).
  **No known false sentence remains.**

**Stated plainly: no round returned a bare CLEAN, and the ratification record does not claim one did.**
T53's acceptance was *conditional*, its condition was met and verified, and the reviewer itself authorised
ratification once it was.

### The mechanical proofs, each reproduced by the driver rather than taken on report

- **§3.1 and §4.1 byte-identical across revisions 10, 11 and 12** — sha256 `42b978e2abb9` (3,592 chars) and
  `b88faca50f22` (1,169 chars). Those two sections *are* the graded domain and the rounding decision, so their
  byte-identity proves **no graded-domain predicate moved** — which is why N46-1/N46-3 landing as errata
  needed no gate.
- **`contract.go`'s non-comment body byte-identical** — sha256 `2530f13ecad961f2` over 96 non-comment lines,
  proved three independent ways (T52's count, T53's string-aware Go lexer, the driver's diff parse).
- **0 out-of-range citations**, sustained across T49 (155 distinct / 329 occurrences), T52 (171), T53 (all 47
  added) and T54 (24 on added lines).

### What ratification does NOT mean — and none of this is now decided

- **NOT that `contract.go` compiles.** No Go toolchain exists on this host; `go build ./...` has **never
  run** against it. Ten rounds graded its comments and its shape against source and vectors; nothing has
  graded whether it builds. `[UNVERIFIED]` — see `.softhouse/reference-oracle.md`.
- **NOT parity with Fineract, and NOT a cutover.** No vector is promoted; `DayCountActualActual` is still
  refused with `ErrNoDiscriminatingVector`; the ~60 captures of that arm are **CAPTURED, NOT PROMOTED**.
- **NOT that the aliased input was witnessed delivering a wrong value.** It was not and cannot be on this
  tenant — the tenant-global flag is `false`, so the alias delivers what a correct port would. The alias
  exists and the slot is live, but **the harm is re-derived, not observed.** `TO_BE_CAPTURED`.

### Consequence

**T6 is done and T7 — the golden-vector conformance harness — is unblocked, along with T9–T15 behind it.**
T7 carries two constraints its author must not discover late: charge conformance can only be graded on **Path
B** (the Path A seam hard-wires `loanCharges` to `null`), and **no Go toolchain exists**, so the harness can
be designed but not executed against Go until one is installed.

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts.

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

---

### G-1 · UPDATE from cloud catch-up fire `cloud-20260818-2000` — still open, and now precisely scoped

**Nothing in G-1 needs Buyan.** Every remaining item is ENGINEERING, and the cloud fire proved most of it needs no
live oracle at all. The gate is open because the contract is not yet correct — not because a question is unanswered.

**What this fire established.** DEC-1 went **v2 → v3 → v4** and is mid-flight to **v5**, under three independent
re-reviews. The driver did **not** ratify at any point, because standing policy **P-2** licenses ratification only
on a *clean* review and no review came back clean:

| Review | Subject | Verdict | New P0s found |
|---|---|---|---|
| T23 (earlier fire) | DEC-1 v2 | ACCEPTED WITH REQUIRED CHANGES | 3 |
| **T26** (this fire) | DEC-1 v3 | ACCEPTED WITH REQUIRED CHANGES | **1** — the EMI re-adjust loop was specified by its *trigger*, never its *effect* |
| **T29** (this fire) | DEC-1 v4 | ACCEPTED WITH REQUIRED CHANGES | **2** — `n` misdefined; **the per-period interest computation specified nowhere** |

**The pattern worth recording, because it is the whole argument for this pipeline.** Each round the corpus passed
*both* the right and the wrong reading. T26's finding: 2,855 of 24,000 in-graded-domain shapes trip the guard and
no Run-1 vector trips it. T29's: the textbook interest reading diverges on 699 of 43,992 shapes and **all 13
committed observations pass either way**. Three times now, "the golden test passes" has been no evidence at all.
This is precisely the failure DEC-1 exists to prevent — a port that passes its corpus and is wrong.

**Convergence, not thrash.** T29 independently verified the *entire* T28 loop specification and all ~20 of its
`file:line` citations, and its from-scratch model reproduces **13 of 13** committed observations digit-for-digit.
Each new P0 has been in an area the previous review had not examined, not a re-opening of settled ground.

**What unblocks ratification** — all agent-decidable, none needing Buyan and none needing the oracle:
1. **T31** applies T29's two P0s → DEC-1 **v5** (in flight at this fire's close).
2. **T32** re-reviews v5. If clean, the driver ratifies under P-2 and **G-1 closes without reaching Buyan**.

**What is NOT a ratification precondition** — the reviewers agree, and the driver concurs: capturing the vectors
that trip the EMI re-adjust guard and separate the interest round-trip. Those are bound to **conformance PASS and
cutover** (ADR §8 items 3, 3a, and now 3b/3c), not to the freeze. No `loanschedule` PASS and no cutover proposal
until all four exist. They need a live oracle, which only the local fire can reach.

**Still RESERVED for Buyan, and untouched by any of this:** cutover authorization, regulatory / parallel-run
sign-off, deposit-taking activation, and licence facts. **None of them is in Run 1's path.**

---

### G-1 · UPDATE from local fire `20260819-080001` (oracle REACHABLE) — **the reserved list is now EMPTY**

The gate record still carried six items under *"Decisions only Buyan can make"*. **All six have since been
answered**, five inside DEC-1 revisions 3–6 and one by Buyan's own ratified tenant parameters. Triaged
against CLAUDE.md § Answering gates, **G-1 contains zero RESERVED items.** It is not a `user` gate; it is
an engineering convergence problem, and it closes when an independent re-review comes back clean (P-2).

| # | Item as originally recorded | Class | Disposition |
|---|---|---|---|
| 1 | `IntermediatePrecisionDigits`: rename + document both senses, or keep the name | ENGINEERING | **Closed.** The field was replaced outright, not renamed; DEC-1 §4.2 states the defect it replaces and the two incompatible senses the oracle threads through one `MathContext` [`ProgressiveEMICalculator.java:1950-1963`]. |
| 2 | Ordering rule: reproduce the oracle's order, or reject a disbursement on a repayment due date | ENGINEERING | **Closed by observation.** DEC-1 §4.6 reproduces the emitted order; revision 3's P0-2 deleted the third clause after observing that a disbursement on/after the last due date or before `ScheduleStartDate` yields **no disbursement row at all** (cases Q1a/Q1b/Q2). That shape is refused as outside the graded domain, so the rule never has to key such a row. |
| 3 | Must a discriminating vector be captured *before* ratification? | PRODUCT | **Decided: yes** — and satisfied. T37 captured **all five** of DEC-1 §8's BINDING shapes from the live oracle at (19, HALF_UP), and **all five separate the readings**. |
| 4 | Does `DayCountActualActual` stay in the Run-1 contract domain while unvectored? | ENGINEERING | **Closed.** DEC-1 §4.9: the member stays in the value domain and the *computation* is refused with `ErrNoDiscriminatingVector`. Keeping it costs nothing; removing it later would be a narrowing and therefore a gate. |
| 5 | Accept `allowFullTermForTranche` as a pinned-false conformance obligation rather than a dead field | ENGINEERING | **Closed.** DEC-1 §4.4 records it as a real behavioural pin — the setter is reached [`LoanApplicationTerms.java:606`] and the guard never consults multi-disbursement [`ProgressiveEMICalculator.java:142-144`]. Two captures differing only in the flag were taken at (19, HALF_UP) and are *observed* identical. |
| 6 | State the Mongolian tenant's actual rounding mode | RESERVED at the time | **Answered by Buyan, 18 August 2026**, and now a ratified tenant parameter in CLAUDE.md: **`HALF_UP`** (`RoundingMode` ordinal 4), precision **19** (a compile-time constant, `MoneyHelper.PRECISION`; only the mode is tenant-configurable). Production `MathContext` = **(19, HALF_UP)**. |

**What actually gates G-1, therefore:** one clean independent re-review of DEC-1. Six consecutive
re-reviews (T23, T26, T29, T32, T34) plus one capture (T37) have each found a **new** P0 on a surface no
prior round examined, so the driver has never been licensed to ratify. Revision 7 is in flight as T38.

**Nothing here is escalated to Buyan.** Per CLAUDE.md, DEC-n ratification is agent-decidable on a clean
independent review; Buyan retains veto. **Still RESERVED and untouched:** cutover, regulatory /
parallel-run sign-off, deposit-taking activation, and licence facts — none of which is in Run 1's path.

---

### G-1 · RATIFICATION DECISION, fire `20260819-080001` — **NOT RATIFIED**, and the reviewer disagreed

DEC-1 reached **revision 8**, the ratification candidate, and independent re-review **T43** returned
**ACCEPTED WITH REQUIRED CHANGES — no P0**. That is the first round in eight to find no P0, and T43
stated plainly that it *"found no reason not to ratify"*, recommending the driver ratify under P-2 and
carry the corrections as a revision-9 erratum.

**The driver declined. DEC-1 is NOT ratified and G-1 stays open.** The reasoning, recorded so it can be
overturned:

1. **The bar is written and it says clean.** CLAUDE.md: *"once the contract passes an independent review
   **clean**, the driver ratifies it."* T43's own verdict vocabulary distinguishes **CLEAN** from
   **ACCEPTED WITH REQUIRED CHANGES**, and it chose the latter. A reviewer may recommend policy; it does
   not set it.
2. **The standing invariant forbids the shortcut.** *"Continuity is achieved by finding other work, never
   by lowering a bar."* Eight rounds of cost is not a reason to redefine "clean".
3. **The decisive one — ratification FREEZES.** A ratified DEC-n cannot be amended by an agent without a
   gate. **P1-T43-3 is a known-wrong statement about money**: §4.3.2's M4 is stated as deciding which row
   a **charge** lands on, but `getCumulativeAmountOfCharge` computes `isDue` at `:403` and the
   `isInstalmentFee()` arm at `:404-405` **never reads it** — an instalment fee lands on **every** row,
   with no membership test at all. Observed on `FC-02` (12 charge cells) and `FC-07` (1). A porter
   following the frozen text would mis-price by **MNT 27,500** on FC-02's shape. Freezing a statement we
   already know to be wrong is precisely what ratification must never do — and revision 8 *introduced*
   that charges section, so the error is new, not inherited.
4. **The cost of one more round is small and the evidence says convergence, not thrash.** Revision 9 is an
   erratum — three P1s and three P2s — not a rewrite. The findings changed *shape* this round: the
   previous seven were **wrong about the money**; T43's are all *"the sentence is right, the evidence
   pinned under it is not"*. That is what converging looks like.

**What now closes G-1:** revision 9 applies T43's errata (and T44's capture-audit findings), then **one**
independent re-review. If that returns CLEAN, the driver ratifies under P-2 without reaching Buyan.

**Buyan may overturn this.** Ratifying revision 8 today would be defensible — no P0, and the three P1s are
citation and scope-of-claim defects, one of which bites only a charge port that Run 1 does not build. It
would unblock **T7** (the conformance harness) and everything behind it roughly one round earlier. The
driver judged that unblocking a harness one round early is worth less than not freezing a known-wrong
money sentence. **This is a judgment call, not a statute, and it is the only thing in G-1 that is.**

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts. None is in Run 1's path.

---

### G-1 · UPDATE from local fire `20260819-140003` (oracle REACHABLE) — **NOT RATIFIED at revision 10**, and this time the reviewer and the driver agree

**Still ENGINEERING_ONLY. `decisions_reserved_for_user` is still EMPTY. G-1 is not a `user` gate and this fire did not make it one.**

#### The second consecutive no-P0 round

T49 re-reviewed **revision 10** and returned **ACCEPTED WITH REQUIRED CHANGES — no P0**. That is two in a
row (T43 on revision 8, T49 on revision 10) after seven straight rounds that each found a new P0. What T49
verified positively matters as much as what it found:

- It reproduced revision 10's packed-whole-months closed form **from first principles**: 14,976 days →
  **112,147,776** ordered pairs, predicate fires **45,253**, both cross-terms **0**, `k_oracle ≡ k_clamped`,
  first firing pair `2000-01-29`/`2001-02-28` packed 12 / clamped 13 / oracle 13 — matching the document exactly.
- Citation audit: **155 distinct citations, 329 occurrences, 0 out of range, 0 ambiguous.**
- The **M4/M5 restatement grep found no leak** — the T2-style failure mode the driver specifically warned it
  about is not present.

#### Why the driver declined anyway — one item, re-verified by the driver at source

**P1-T49-2.** `contract.go:367-370` and DEC-1 §4.9 both still say the `DayCountActualActual` arm has
*"no capture in the corpus"* and that *"no independent re-derivation has yet reproduced [it] from source"*.
**Both are now false.** P2-T29-1 retired the re-derivation claim in **revision 5** — §4.10 and §8 item 5
already say so — and T48 captured the arm on three seams last fire (~60 captures), with `B-03`/`B-04` on
Path B. It leaked across **five revisions and eight review rounds**.

It sits in a **`contract.go` doc comment**. **Ratification freezes it, and correcting it afterwards is a
gate.** This is the same category as the known-wrong money sentence that made the driver decline at
revision 8 — a false statement being frozen into the artefact — and the reviewer's own recommendation was
likewise "ratify *after* a bounded erratum pass", not "ratify now". **Reviewer and driver agree this time.**

Two supporting P1s, both re-derived by the driver rather than taken on report:
- **P1-T49-3** — revision 10's own worked check in §4.5.1 is wrong by exactly 10²:
  `2,160,000 × 21,875 = 47,250,000,000`, not `472,500,000`, which is the product of the **major**-unit
  `21,600`. The conclusion it supports, and the observed `4.73`/`2.03`, are correct.
- **P1-T49-1** — the capture seam drops a **third** of the 19 components, so §2.2's "honours 17 of 19" and
  §3.2's "**exactly** the two the graded domain pins" are false *inside the argument that licenses freezing
  the contract on a seam-captured corpus*. The conclusion survives and is **strengthened** — the blind spot
  is still empty, now on three pins.

#### What this fire added that revision 11 must carry

Three findings **confirmed by observation** in the same fire, two of which change what a correct sentence says:

- **N46-1 and N46-3 — CONFIRMED, no longer `TO_BE_CAPTURED`.** The **ambient** `MoneyHelper` mode governs the
  charge value at `ProgressiveLoanScheduleGenerator.java:445-446`/`:464-465` in **7/7** threaded columns
  (threaded moves it in **0/7**), reachable at MNT scale — `1005025.12` vs `1005025.13` on a fee.
  **The recorded blocker was refuted:** T46 and T48 both wrote that separating the two axes "needs a tenant
  write", but `LoanScheduleAssembler:753` reads `getMathContext()` and `:765` threads *that same cached
  reference*, so a tenant write moves both together and the experiment cannot work. On the shipped server
  the leak is **latent**; it goes live the moment a port threads a context — the natural Go idiom.
  **This is a defect class a Go port introduces, not one Fineract exhibits.**
- **The alias crosses configuration scopes** (T51, driver-verified at `LoanScheduleAssembler.java:370-371`).
  `isInterestChargedFromDateSameAsDisbursalDateEnabled` is a **tenant-global configuration**, not a product
  setting, so **a port cannot fix the alias by wiring "the other product field."** Both downstream readers
  were proven to move money (79/153 and 52/164 cells), so **the slot is LIVE** — yet products 17/18 matched
  on 20 SQL columns differ in **0 cells** across 8 shapes, so **the product setting is INERT**. The oracle
  matches the **31-December** boundary on 6 of 6 discriminating periods. A port must wire from the global
  config and reproduce 31-December bug-for-bug.
- **T50-N2 — the Path A embeddable seam can NEVER exercise a charge.** `ProgressiveLoanScheduleGenerator.java:81`
  calls `generate(mc, loanApplicationTerms, null, null)` — `loanCharges` hard-wired `null` (driver-verified
  by reading the line). **Charge conformance can only ever be graded on Path B**, which constrains T7's
  harness design and bears on §2.2/§3.2/§5's seam-coverage reasoning.

#### What unblocks G-1 now

1. **T52** — revision 11, a **bounded** erratum pass: T49's six items plus the three findings above. No type,
   field, enum member or graded-domain predicate moves; if one must, that is an amendment and a gate.
2. **A diff-scoped check** that the items landed and that every money statement the diff introduces
   re-derives — **not a ninth full re-derivation**. T49's own recommendation, and the rounds have converged.
3. **The driver ratifies under policy P-2 and records the rationale. Buyan retains veto.**

#### The reversible judgement, restated for Buyan

The driver has now declined ratification twice on no-P0 reviews (revision 8, revision 10). Both times the
reason was a **known-false sentence about to be frozen**, not doubt about the money — and both times the
next revision proved the sentence really was wrong. **If you would rather trade that rigour for speed, say
so and DEC-1 can be ratified at its current revision.** The cost of the current path is roughly one round
per fire; the cost of the other is that correcting a frozen falsehood needs a gate.

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts. None is in Run 1's path.

---

## G-3 — **ENGINEERING** — may `gofmt` rewrite the ratified `contract.go`? *(OPEN — driver-decidable, deliberately not self-answered)*

**Raised by** local fire `20260819-170001`, immediately after the first ever compile of the ratified artefact.
**Context** `tier0-harness-schedule-poc`. **Blocks** nothing — every task proceeds under the standing
instruction below. This gate exists to stop a *silent* change, not to pause work.

### What was found

A repo-local Go toolchain was installed this fire (`go1.26.6`, sha256-verified, gitignored — see
`.softhouse/reference-oracle.md`), which finally allowed the ratified DEC-1 artefact to be compiled:

```
cd nexus && go build ./...   → exit 0
             go vet  ./...   → exit 0
             go test ./...   → exit 0  ("no test files")
gofmt -l .                   → internal/apps/loanschedule/contract/contract.go
```

`gofmt` wants to rewrite the frozen contract. The diff was captured and **NOT applied**:

- **Extent:** 3 hunks, 25 diff lines. Every hunk inserts a bare `//` line **between numbered list items
  inside doc comments** — Go 1.19+ doc-comment list normalisation.
- **Semantically inert:** no type, field, enum member, error value, identifier or specified predicate moves.
- **Caveat on the mechanical check, so nobody misreads it:** "identical after stripping all whitespace"
  reports **NO**, because gofmt inserts new `//` tokens and `/` is not whitespace. The inserted tokens are
  *empty comment markers*; the prose is unchanged. That check is not evidence of a substantive edit.

### Why this is a gate and not a nit

The doc comments in `contract.go` **ARE the specification** — the file says so itself, and DEC-1 §*Amendment
gate* makes "re-documenting any identifier in this package" an amendment requiring a gate once ratified.
So the risk is not that gofmt's output is wrong. The risk is the **failure mode**:

> An editor format-on-save, or a `coder` who runs `gofmt -w ./...` from the repo root, silently mutates a
> frozen ratified artefact — and the diff looks like harmless formatting noise in review.

That is the same category as the defects the driver declined ratification over at revisions 8 and 10: not a
wrong number, but a wrong thing quietly entering a frozen artefact. The driver did not self-answer it under
P-2 for one reason: **the artefact is already frozen, and the whole point of freezing is that the driver
stops being the one who may edit it.** Answering "yes, reformat it" would be the driver reaching into a
ratified file on aesthetic grounds hours after ratification — precisely the discipline DEC-1's amendment
clause was written to impose. Recording it and working around it costs nothing.

### Standing instruction until this gate is answered — already in force

1. **No task may run `gofmt -w`, `go fmt`, or a format-all over
   `nexus/internal/apps/loanschedule/contract/contract.go`.** Format only files you created.
2. **`gofmt -l` reporting exactly that one path is the EXPECTED state.** A UAT must not fail on it, and a
   harness's gofmt-cleanliness check must exempt that path *with a comment saying why* — an unexplained
   exemption invites a later agent to "fix" it.
3. If the file's formatting is ever found to differ from the ratified bytes, that is a **process incident** to
   investigate, not a diff to accept.

### The three options, and the driver's recommendation

| Option | Effect | Cost |
|---|---|---|
| **A — leave it unformatted** *(in force now)* | ratified bytes stay byte-identical; the sha256 guardrails from revisions 10/11/12 keep working unchanged | one permanent, documented gofmt exemption; every fire must re-learn it (mitigated: it is recorded here, in `reference-oracle.md`, and in T7's brief) |
| **B — apply gofmt as a recorded no-predicate erratum** | tree becomes gofmt-clean; the exemption disappears | the ratified artefact's bytes change, which **invalidates the `contract.go` byte-identity guardrail** (sha256 `2530f13ecad961f2` over the 96-line non-comment body still holds, but the whole-file hash does not) and sets the precedent that "inert" edits to a frozen file are fine — the precedent is the real cost, not the whitespace |
| **C — amend DEC-1 to state the file is exempt from gofmt** | makes A explicit in the specification | a DEC-1 amendment is itself a gate, so this is the most expensive route to the outcome A already delivers |

**Driver's recommendation: A**, and treat it as the answer unless Buyan prefers otherwise. It is free, it is
already in force, it preserves every existing guardrail, and it keeps the freeze meaning what it says. The
only argument for B is tooling tidiness, and a documented one-line exemption buys the same tidiness without
touching a ratified artefact.

**Nothing here is RESERVED.** No money, no live endpoint, no third party, no licence fact — this is recorded
for Buyan's awareness and reversal, not because an agent could not reason about it.

---

## G-4 — **ENGINEERING** — DEC-1 carries a promotion condition that is provably TOO STRONG *(OPEN — needs a DEC-1 amendment, which no agent may make)*

**Raised by** local fire `20260819-170001`, from task **T55**, and **independently re-derived by the driver**
before being recorded. **Context** `tier0-harness-schedule-poc`. **Blocks** nothing today: the corrected
condition is already in force operationally and is what T7's harness was told to use.

### The defect

T48-N4's promotion condition for the `DayCountActualActual` arm — restated in `RESUME.md`, `gates.md`
**and in DEC-1 commentary** — requires a promoted vector to cross a leap boundary **"with a non-zero first
segment"**.

**The "non-zero first segment" requirement is false.** Capture `LB-DEC31` has a **zero** first segment and
still grades the arm by **6,015 minor units**.

### Driver re-derivation — this was recomputed from scratch, not accepted on T55's report

Shape: principal `1,200,000` MNT, one repayment, `21.6 %` nominal annual, disbursed **31 December 2024**,
due **31 January 2025**. 2024 is a leap year (366); 2025 is not (365). The **31-December** segmentation
boundary — which the oracle matched 6 of 6 in T51 — puts the 2024 segment at **zero days**.

| Branch | Rate factor | Interest | Status |
|---|---|---|---|
| **ARM** (ACT/ACT, per-calendar-year denominators) | `0/366 + 31/365` = `0.08493150684931506849` | **`22014.25`** | **OBSERVED** in `LB-DEC31-p3`, `-p4`, `-p7` — all three products, and in the determinism re-runs |
| **PLAIN** (one denominator, from the period-start year) | `31/366` = `0.08469945355191256831` | `21954.10` | counterfactual — what a no-arm port yields |

`1,200,000 × 0.216 × 0.08493150684931506849 = 22014.246…` → **`22014.25`** at HALF_UP, precision 19.
Difference **`60.15` major = `6,015` minor units.** `[VERIFIED: driver re-derivation at (19, HALF_UP);
observed value present in 9 capture files including re-runs]`.

**Why a zero first segment still discriminates** — the mechanism, which is the part worth recording:
the PLAIN branch takes its single denominator from the **period-start year** (2024 → 366), while the ARM
assigns the days to the year they **actually fall in** (2025 → 365). The zero-length 2024 segment
contributes nothing to the ARM, but the PLAIN branch *still uses 2024's length*. So the two branches diverge
whenever the start year's length differs from the length of the year the days land in — **segment length is
irrelevant; the year lengths are what matter.**

### The correction being asked for

> **Wrong:** crosses a leap boundary **with a non-zero first segment**.
> **Correct:** the period **spans two calendar years of differing length**.

### What was and was not changed

- **DEC-1 was NOT touched.** T55 found the defect, correctly declined to amend a ratified artefact, and
  reported it; the driver verified it and also declined. A ratified DEC-n cannot be amended by an agent
  (`CLAUDE.md` § Blocking questions).
- **`RESUME.md` and `gates.md` use the corrected condition from this fire on.** They are operational files,
  not ratified artefacts.
- **T7's harness was instructed mid-flight to use the corrected condition** and to cite it as T55-N1 with
  DEC-1's wording noted as under gate.

So the only thing outstanding is the **wording inside DEC-1**. Until it is amended, DEC-1 states a condition
stricter than the evidence supports — the failure mode is a *false negative*: a future task reads DEC-1,
rejects `LB-DEC31` as unpromotable for want of a non-zero first segment, and discards a vector that grades
the arm by 6,015 minor units.

### Asking for

Approval to amend DEC-1's commentary on the ACT/ACT promotion condition, **wording only**, replacing
"non-zero first segment" with "spans two calendar years of differing length". **No type, field, enum member,
error value or graded-domain predicate moves**; the arm's specified arithmetic is unchanged and this is a
correction *toward* what the source and the captures already do. Rejecting the amendment is also workable —
the condition would then live only in the operational files, with DEC-1 known-wrong on this one sentence,
which is precisely the situation the driver twice declined to ratify into.

**Not RESERVED.** No money, no live endpoint, no third party, no licence fact.

---

## G-5 — **ENGINEERING** — DEC-1 contradicts itself on a ZERO interest rate, and the harness's own self-test depends on which way it is read *(OPEN — needs a DEC-1 amendment, which no agent may make)*

**Raised by** local fire `20260819-200001`, from task **T10** (the first Go port), **driver-confirmed**.
**Context** `tier0-harness-schedule-poc`. **Blocks** nothing today — the port follows the enumerated list,
which is what the harness enforces — but the two readings disagree about a reachable request.

### The contradiction

- `AnnualNominalInterestRate`'s doc comment says a **zero rate is "outside the graded domain"**.
- The **enumerated graded-domain list** does not contain any rate predicate at all.
- `admit.go:846-907` implements the list and therefore **has no rate predicate**.
- `_selftest/SELFTEST-01-two-period-zero-rate.json` **is a zero-rate request**.

So a port that follows DEC-1's **prose** refuses `SELFTEST-01` with `ErrNoDiscriminatingVector`, and the
harness reports that refusal as **FAIL, exit 1**. A port that follows DEC-1's **list** grades it and passes.
The specification cannot be satisfied both ways, and the harness's own self-test fixture is the shape that
exposes it.

### What T10 did, and why it is the right interim call

Implemented **the enumerated list**, matching the harness, and flagged the conflict rather than resolving it.
That keeps the port and the grader consistent with each other and leaves the decision where it belongs.
**T10 did not amend DEC-1**, correctly — a ratified DEC-n is not an agent's call.

### Asking for

A **wording-only** DEC-1 amendment picking one reading. The driver recommends **making the prose match the
list** — i.e. deleting the "zero rate is outside the graded domain" sentence — for three reasons:

1. The list is what the harness enforces, so the prose is the part that is already inert.
2. A zero-rate schedule is a perfectly ordinary NBFI product shape (an interest-free instalment plan), and
   putting it outside the graded domain would mean shipping it **ungraded** rather than not shipping it.
3. `SELFTEST-01` — the fixture that proves the harness can distinguish pass from fail — is zero-rate. Making
   zero rate ungradeable would require re-authoring the harness's own self-test.

The alternative (keep the prose, add a rate predicate to the list, re-author `SELFTEST-01`) is defensible but
strictly more work for a worse outcome.

**Not RESERVED.** No money, no live endpoint, no third party, no licence fact. Recorded for Buyan's awareness
and reversal, not because an agent could not reason about it.
