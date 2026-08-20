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

### Driver check, local fire `20260820-080002` — **the feared failure mode is already prevented MECHANICALLY, and loudly**

G-3's stated risk is a *silent* mutation: *"an editor format-on-save, or a `coder` who runs `gofmt -w ./...`
from the repo root, silently mutates a frozen ratified artefact — and the diff looks like harmless formatting
noise in review."* The driver tested whether that is actually true, rather than reasoning about it.

**It is not. The mutation is not silent — it halts the harness on the very next run.**

`.softhouse/vectors/PIN.json` carries `contract_sha256`, and `conformance/admit.go:87-93` compares it against
the file's real digest on every run. The driver **demonstrated** this rather than reading it: appending a
single trailing newline to `contract.go` — a semantically inert, whitespace-only change of exactly the class
gofmt would make — produced

```
--- WHY THIS RUN CANNOT BE TRUSTED ---
    * frozen contract nexus/internal/apps/loanschedule/contract/contract.go digest c5bf0918… does not match
      the store pin 0db73d4a…: the corpus is expressed in the ratified DEC-1 shape and a change to that shape
      invalidates it. This is not a harness bug to work around — either the edit needs a gate, or the corpus
      needs re-validating and the pin re-stamping

VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

`contract.go` was restored byte-for-byte immediately (`0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139`,
matching PIN.json) and `git status --porcelain` came back empty.

**What this changes for the decision.** G-3 remains Buyan's — it concerns a frozen ratified artefact, and the
driver still declines to reach into one on aesthetic grounds. But its *urgency* is now measured rather than
assumed: a stray `gofmt -w` cannot slip through review as formatting noise, because the next conformance run
refuses to produce a verdict at all and names the file. **Option A costs nothing and is protected by a guard
that provably fires.** The gate is safe to leave open indefinitely.

**Backlog (not part of the gate).** `.softhouse/conformance.sh:31` defines `CONTRACT_REL` and never uses it —
the real check lives in `admit.go`. A vestigial shell variable that looks like a guard is mildly misleading to
the next reader; delete it or wire it up.

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

---

## G-3 — CLOSED (Option A), local fire `20260820-110001`

**Class:** ENGINEERING. No RESERVED content, so the driver decides it (CLAUDE.md § *Answering gates*).

**Decision: Option A.** `nexus/internal/apps/loanschedule/contract/contract.go` is **never** `gofmt`'d. The
exemption is a standing instruction, **not** a DEC-1 amendment.

**Why the feared failure mode cannot happen — demonstrated twice, not argued:**
1. Fire `20260819-170001`: the driver appended one inert newline to the frozen file; the next harness run
   returned **exit 2 UNUSABLE**, naming both digests (`admit.go:87-93` against `PIN.json`'s
   `contract_sha256`).
2. Fire `20260820-110001`, task **T68**: `VerifyContractDigest` fires at **`grade.go:237`, before
   `LoadStore`** — confirmed by the driver by grep and by T68 by demonstration, on both a `_selftest`-scoped
   run and an **empty store**. There is no path by which a vector loads without the digest being checked.

A silent mutation of the ratified artefact is therefore impossible; a mutation halts the harness loudly.

**Rejected alternatives.** Option B (apply the formatting as an "inert erratum") would change the ratified
bytes, invalidate the whole-file byte-identity guardrail, and — the real cost — establish the precedent that
"semantically inert" edits to a frozen file are acceptable. Option C (amend DEC-1 to record the exemption)
spends a ratified-document amendment to buy exactly what Option A already delivers for nothing.

**In force, unchanged:** no task may `gofmt -w` that path, and `gofmt -l` reporting **exactly that one file**
is the EXPECTED state and must not fail a UAT.

**Buyan may reverse this.**

---

# G-6 — accept the Tier-0 PoC slice (task T14) — **CLOSED, ACCEPTED by the driver**

| | |
|---|---|
| **Class** | **PRODUCT / process.** No RESERVED content. |
| **Task** | T14, run `2026-08-17-run1-harness-schedule-poc`, context `tier0-harness-schedule-poc` |
| **Raised by** | the original Run-1 plan, as `executor: "user"` |
| **Closed by** | local fire `20260820-140000` (`/softhouse-program` driver) |
| **chosen_by** | `agent` |
| **Blocks** | nothing further; T15 (archive) and Tier A follow |

## Why the driver decided this rather than parking it

The task was planned `executor: "user"`, and the driver checked that label against CLAUDE.md
§ *Answering gates* rather than treating it as settling the question. **RESERVED is an exhaustive
list**: which licence a deployment holds and any fact about Gerege's legal entity; **CUTOVER**
authorization; regulatory acceptance / parallel-run sign-off; and anything that spends real money,
exposes a live endpoint, or binds Gerege to a third party.

**T14 is none of those, and says so in its own description**: *"Explicitly recorded: NOTHING is cut
over from Fineract to Go in this run."* It asks whether the PoC is adequate proof that the pipeline
works — a greenfield process judgement. The standing policy is directly on point: the driver chooses
and recommends, and *"a choice recorded in writing is easier to overturn than a question is to
answer."* **P-2** already set this precedent by making DEC-1 ratification agent-decidable on a clean
independent review. Parking the whole program on this item would idle the factory on a question no
statute, vector or source reading is waiting to answer.

## What was proven

Every number below was **re-run by the driver**, not accepted from a worker's report, and the
independent verifier T13 reproduced them separately in its own worktree.

```
conformance          exit 0 — 36/36 parity vectors PASS, 4034 cells graded, 72 ungraded
                     4 contract-refusal PASS, 1 self-test PASS
                     0 refused · 0 inadmissible · 0 harness errors
                     0 invariant violations · 0 invariant assertions NOT RUN
--prove              exit 0 — 21/21 mutation proofs
--self-test          exit 0
go build / vet / test (-count=1, not cached)   0 / 0 / 0
contract.go sha256   identical to PIN.json contract_sha256
```

**The acceptance rests on the pipeline catching real defects, not on a green bar.** In evidence:

- **T67 REJECTED T65 — a diff whose code was correct, because its written rule was false.** The
  driver confirmed two of T67's three findings from committed source *before* ruling. **T69** then
  fixed it and **found a defect in T67's own replacement text**, and refused to assert a third reason
  for `futureUnrecognizedInterest`, marking it `[UNVERIFIED]` instead. Three wrong reasons for one
  bullet is what this pipeline exists to stop, and it stopped at two.
- **T64** registered a falsifiable prediction naming all 221 rows **one commit before** the capture;
  the oracle returned 1539/1539 cells, zero mismatches. A mutation green on all 32 vectors is red at 36.
- **T68** found the correction document was wrong about its own reason, twice — P-11 recursing.
- **T66** (this fire) **refuted the driver's own hypothesis**, and the driver re-ran all three of its
  legs — re-capturing pass 3h to the identical canonical digest — rather than accept either side.
  The driver then **overstated a finding against T66 and withdrew it** on checking the handoff.

A pipeline in which the reviewer overrules the coder, the reviewer's own text gets corrected, and the
**driver's** hypothesis is refuted by a worker and its own finding withdrawn, is the thing this PoC
was built to demonstrate.

## Accepted WITH these residuals recorded, not glossed

1. **T12 is `done_partial`, and the acceptance does not pretend otherwise.** The rehydration half is a
   committed re-runnable assertion (`.softhouse/bin/rehydrate-check.sh`). **The mid-flight checkpoint
   half is still unexercised** — for a fourth fire running, because every dispatched worker has
   completed. That is the better outcome and it leaves the drill undone. T14's own description names
   the drill as something to review, so this is a real, if narrow, shortfall in the evidence.
2. **36 vectors is not "the loan module is correct."** The graded domain is DEC-1's: one
   disbursement, monthly `DECLINING_BALANCE`, `FIXED_30_360`, no charges, no payments, no
   multi-tranche, no re-aging. T13 recorded the ungraded areas (rate-factor exactness
   `TO_BE_CAPTURED`, precision 19 vs 12 unseparated, origination-time rate variation untested).
3. **`ZP-PRINCIPAL-NOT-CLAMPED` survives all 36 vectors.** The negative clamp remains ungraded and is
   in the backlog, kept as an honest negative.
4. **T2 stays permanently parked** (G-2), and T70/T71 — the correction of the now-stale
   `[UNVERIFIED]` marker T66 settled — were in flight when this was decided. Both are doc-only and
   neither can move a graded cell.

## What this acceptance is NOT

**It is not a cutover, and it does not authorise one.** Nothing moves from Fineract to Go. Cutover
remains a hard `user` gate requiring vectors passing **plus** a clean shadow-parity window **plus**
regulatory / parallel-run sign-off, and no automation may cross it. Deposit-taking activation,
regulatory sign-off and licence facts are equally untouched and are not in Run 1's path.

**Buyan may reverse this.**

---

## G-8 — TWO phenomena at the rounding floor, under one gate id

- **id**: G-8
- **class**: ENGINEERING to measure; the *remedy* is a DEC-n amendment, which is a hard `user` gate
- **task**: T75 (found the shape, and stated the family-A mechanism first), T83 (measured family A),
  T84 (reproduced T83, measured family B, and rejected T83's write-up), T100 (rewrote this section
  and re-measured both discriminators)
- **context**: tier0-harness-schedule-poc / loan-schedule
- **state**: **OPEN** — blocks nothing today
- **raised_by**: local fire 20260820-170001, from T75's approval of T74
- **recorded_in**: `.softhouse/gates.md`

### Read this first: G-8 is TWO phenomena, and a remedy for one is not a remedy for the other

Everything below is scoped to the family it was measured on. A sentence about family A is not a
sentence about family B, and neither is a sentence about the graded domain as a whole — the domain
is graded **by sampling**, and rate, principal and `NumberOfRepayments` are unbounded in it
[VERIFIED by T100 at `nexus/internal/apps/loanschedule/contract/contract.go:1163-1170`: *"are graded
by sampling rather than by enumeration … No claim is made that any un-sampled value is safe"*].

| | **FAMILY A — stale derived column** | **FAMILY B — genuine non-amortization** |
|---|---|---|
| principal column sums to the disbursed amount | **yes** | **NO — it sums to 0.00** |
| `totalPrincipalAmount` | = the disbursement | **0.00** |
| non-zero principal rows | exactly **one**, the last, carrying the whole disbursement | **none** |
| last row's interest | `0.00` | `0.01` |
| balance column | constant at the disbursed amount | constant at the disbursed amount |
| `totalOutstandingAmount` | `0` | `0` — **so this field does not discriminate** |
| forcing the oracle's own balance `Memo` to recompute | balance goes to **`0.00`** | **does not move** |
| the Go port | **diverges**, on exactly one cell per case | **reproduces it cell for cell — no divergence at all** |
| `invariant_exemptions` as a remedy | **inert** — the failure is a cell diff | **decisive** — the failure is purely invariant |
| measured at | **11** of the 12 annual rates swept (all but 600.0 %), `3 ≤ n ≤ 600`, **312 cells** | **one** annual rate (600.0 %), `104 ≤ n ≤ 250`, **29 cells** |

Cells behind that table: **312 family-A** (198 T83 + 111 T84 + 3 T100) and **29 family-B** (22 T84 +
7 T100), each re-derived from the committed raw captures by T100's own classifier
[`.softhouse/capture/t100-g8-rescope/src/classify_two_families.py`, `out/column-shape-{t83,t84,t100}.json`].
Every row of that table holds on **every** cell of its family in those captures — no exceptions, no
mixed cases. The two families are disjoint and each is internally uniform on what was swept.

**What was found originally.** T75 registered a prediction, committed it, and only then ran a
calibrated probe against the pinned oracle image (its calibrations reproduced `T64-ZP-A`/`T64-ZP-B`
cell-for-cell with zero input diffs). Result: **MNT 0.01 / 6 × 21.6 % at `MinorUnitDigits = 2` —
inside the graded domain, no multiples-of input involved — makes the reference oracle emit a
schedule whose balance column never reaches zero, `0.01` on every row including the last, while the
Go port returns `0`.** That shape is **family A** [VERIFIED by T100: `T100-FAMA-R21p6-N6-B2`, its
principal column sums to 2 minor units against a 2-minor-unit disbursement].

**Why it matters.** On family A this is a live port-vs-oracle divergence on an **admitted** shape,
and it sets two of this project's own rules against each other:

- *"Fineract is the oracle and fallback. No ported Go context is correct until its golden vectors match."*
- *"property invariants … principal amortizes to zero."*

**On family B it is worse and it is different: there is no port-vs-oracle divergence to arbitrate,
because the port agrees with the oracle — both emit a schedule that never repays the loan.** A
declared-divergence mechanism would have to be able to say *"both are wrong"*, which the harness
cannot express today.

Today `conformance.sh` reports PASS with 42 parity vectors and 0 invariant violations — **only
because no vector covers either family.** That is precisely the blind spot the conformance gate
exists to eliminate, so a green bar is not evidence against this finding.

---

## FAMILY A — the outstanding-balance column is STALE with respect to the oracle's own final EMI adjustment

### Discriminator for family A

A cell is family A when **all** of these hold, and they were checked on every cell claimed below:

1. the last emitted row carries a non-zero outstanding `balance`;
2. the REPAYMENT rows' `principal` column still **sums exactly to the disbursed amount** — in every
   family-A cell measured so far by exactly one non-zero principal row, the last, carrying the whole
   disbursement;
3. forcing the oracle's own balance `Memo` to recompute drives that balance to **`0.00`**.

Test 3 is the decisive one: it is what separates A from B, and it is the discriminator the driver's
re-derivation named in advance (*"a memo-staleness defect predicts [order dependence] … a genuine
non-amortization predicts no order dependence at all"*,
`.softhouse/reviews/driver-rederivation-20260820-200002-G8.md`).

### What was measured, and over what domain

**T83's sweep — 330 cells, all family A** [T83, branch `softhouse/T83-nonamortizing-boundary`;
reproduced by T84 byte-identically, canonical sha256 `01b41d9c…3101b`, 332 cases; re-classified a
third time by T100 from the same raw capture: **198 fail / 132 clean / 0 family B**]. Domain swept:
annual rates **{7.0, 16.8, 21.6, 36.0}** × repayment counts **{2, 3, 4, 6, 12, 24, 36, 56}**,
principal swept contiguously in minor units from 1 past the boundary (1..27 minor), every cell
emitted whether clean or not. All strictly inside the graded domain (MNT dp 2, single disbursement
on the schedule start date 2024-01-01, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down
payment, both multiples-of inputs null, `(19, HALF_UP)`).

**T84's extension — 111 further family-A cells** at annual rates **{0.12, 1.2, 3.6, 7.0, 12.0, 16.8,
21.6, 36.0, 48.0, 96.0, 300.0}** and terms up to **n = 600**, principals 1..100 000 minor.

**T100's confirmation — 3 family-A cells** re-asked with **different tenant ids**, in a **scrambled
order**, from its own capture (`out/capture-t100-raw.json`, canonical sha256 `314c4d55…2bfba`, rig
calibrations reproducing the committed `T64-ZP-A`/`T64-ZP-B` cell-for-cell with 0 input diffs):
21.6 % / n=6 / MNT 0.02, 3.6 % / n=360 / MNT 1.09, 0.12 % / n=600 / MNT 2.91 — all three fail, all
three sum, all three predicted in advance.

### The boundary table — MEASURED BY T83, over T83's grid only

"Failing" = the emitted schedule's LAST row carries a non-zero outstanding balance, which is exactly
the cell `principal_amortizes_to_zero` reads. **This table describes 4 rates × 8 terms and nothing
else**; T84's and T100's cells at other rates and longer terms are reported after it, and they move
the largest failing principal by more than an order of magnitude.

| rate % | n | principals swept (minor) | cases | LARGEST FAILING | SMALLEST CLEAN | contiguous |
|---|---|---|---|---|---|---|
| 21.6 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 21.6 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 21.6 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 21.6 | 24 | 1..13 | 13 | **9** (MNT 0.09) | **10** (MNT 0.10) | yes |
| 21.6 | 36 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |
| 21.6 | 56 | 1..21 | 21 | **17** (MNT 0.17) | **18** (MNT 0.18) | yes |
| 7.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 7.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 7.0 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 7.0 | 24 | 1..15 | 15 | **11** (MNT 0.11) | **12** (MNT 0.12) | yes |
| 7.0 | 36 | 1..20 | 20 | **16** (MNT 0.16) | **17** (MNT 0.17) | yes |
| 7.0 | 56 | 1..27 | 27 | **23** (MNT 0.23) | **24** (MNT 0.24) | yes |
| 16.8 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 16.8 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 16.8 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 16.8 | 24 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 16.8 | 36 | 1..18 | 18 | **14** (MNT 0.14) | **15** (MNT 0.15) | yes |
| 16.8 | 56 | 1..23 | 23 | **19** (MNT 0.19) | **20** (MNT 0.20) | yes |
| 36.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 36.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 36.0 | 12 | 1..8 | 8 | **4** (MNT 0.04) | **5** (MNT 0.05) | yes |
| 36.0 | 24 | 1..12 | 12 | **8** (MNT 0.08) | **9** (MNT 0.09) | yes |
| 36.0 | 36 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 36.0 | 56 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |

**T75's report is CONFIRMED and is a strict subset of this.** MNT 0.01/6, 0.02/6, 0.01/12 and
0.01/56 at 21.6 % all fail; 0.03/6 and above are clean **at 21.6 % / n = 6**.

**21.6 % is not load-bearing for family A** — family A exists at all 12 rates swept, from 0.12 % to
300.0 %. Across T83's grid the rate moves *where* the boundary sits and moves it DOWN as the rate
rises; the region is **empty at n = 2** at all four rates T83 tested, and grows with the term.

### The port divergence, family A only — ONE CELL PER CASE

On family A the divergence against the Go port is **the FINAL row's outstanding principal and
nothing else**: **198 divergent cells over T83's 198 failing cases** [T83, `out/port-vs-oracle.json`;
T84 re-ran it and got an identical file; port control on `T64-ZP-A`/`T64-ZP-B` = 0 mismatch cells;
the port refused nothing], plus **111 further divergent cases** in T84's own family-A sweep. T100
re-measured one of them through the real grader: `T100-FAMA-R3p6-N360-B109` grades **2525 cells with
exactly one diff — `row 360 outstanding_principal_minor: expected 109 minor units, got 0`**
[`out/exemption-demo-t100.json`]. The port amortizes; the oracle's balance column does not.

### The mechanism — FIRST STATED BY T75, and it applies to family A

**Attribution: the `:400` / `:1180` / `:1210` chain is T75's**, stated in `T75-pathA-multiplesof-review.md`
§5 one fire before the driver's re-derivation restated it, and T75 additionally carries the
`isFullyPaid()` step. It is not the driver's finding and this record previously failed to say so.

Source, re-verified line by line by T100 at the pinned commit `426a23544`:

- `RepaymentPeriod.getOutstandingLoanBalance()` is a `Memo` whose body subtracts `getDuePrincipal()`
  (`RepaymentPeriod.java:398`) — a direct function of `emi` — while its dependency array at **`:400`**
  is `{paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}` and **omits `emi`**;
- the sibling `getDueInterest()` memo **does** declare `emi` (`:278` opening, `:283`), so the
  omission is asymmetric inside one class;
- `isFullyPaid()` is `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())`,
  i.e. `0 == 0` when every EMI quantizes to zero [T75];
- `calculateLastUnpaidRepaymentPeriodEMI` (`ProgressiveEMICalculator.java:1160`) then takes its
  fallback, whose last filter at **`:1180`** is `rp.getOutstandingLoanBalance().isGreaterThanZero()`
  — which **populates the memo on the target period** — and **`:1210`** raises that period's EMI in
  the **same method** through a plain setter that invalidates nothing;
- the only three readers of `getOutstandingLoanBalance()` in the calculator are `:617`, `:1180`
  and `:1629`.

**The driver's candidate site is REFUTED** [T83, re-verified by T84 and again by T100]:
`RepaymentPeriod.getInitialBalanceForEmiRecalculation()` (`:413-426`) reads `getPrevious()`'s
balance and therefore can never populate the LAST period's memo.

### The mechanism is also OBSERVED, not only read — family A only

`ProbeOrderDep.java` / `ProbeOrderDep2.java` force the oracle's own balance `Memo` to recompute by
moving a DECLARED dependency (`paidPrincipal`) and moving it back to the same value.

- T83, on 5 of 5 family-A shapes: balance as emitted non-zero, balance after forced recompute
  **`0.00`**; 4 of 4 clean controls unmoved; path identity true on all 9.
- T84 re-ran T83's probe and reproduced 5/5 and 4/4.
- **T100 re-ran T84's probe itself** [`out/orderdep-t84probe-rerun-by-t100.json`]: the family-A cell
  `OD2-FAM1-R3p6-N360-B109` moves **`1.09` → `0.00`**; three clean controls (including an ordinary
  MNT 1,200,000 loan) unmoved; path identity true on all 7; `paidPrincipal` restored on all 7.

So **family A is precisely: the reference oracle's outstanding-balance column is stale with respect
to its own final EMI adjustment, while its principal column and its own totals are right.** That
sentence is true **of family A** — it was written into this file by T83 as a description of **all**
of G-8, and in that unscoped form it is **false**; see family B.

---

## FAMILY B — the principal column itself never repays the loan

### Discriminator for family B

A cell is family B when the REPAYMENT rows' `principal` column **does not sum to the disbursed
amount**. On every family-B cell measured so far it sums to **0.00** against a **0.01** disbursement,
`totalPrincipalAmount` reads `0.00`, **no** row carries a non-zero principal, the last row carries
`interest 0.01`, and forcing the memo to recompute **does not move the balance**. This is exactly
the test the driver's re-derivation named in advance as fatal to the family-A reframing when applied
to all of G-8: *"If it ever fails to sum, the reframing above is **wrong** and G-8 is the broader
finding after all."* It failed.

### What was measured, and over what domain — a MUCH narrower domain than family A

**T84 measured 22 family-B cells; T100 measured 7 more.** Union of what has been observed:

- annual rate **600.0 % — and no other rate has ever produced a family-B cell.** T84 swept 300.0 %
  with B = 2 through n = 204 and 300.0 % with B = 1 at six terms up to n = 260: the 300 % failures
  are **family A** (their principal column sums) [VERIFIED by T100's re-classification of T84's raw
  capture: 6 family-A cells at 300.0 %, 0 family-B].
- principal **MNT 0.01 (1 minor unit)** — no other principal has produced a family-B cell.
- repayment counts **n ∈ {104…122} ∪ {150, 200, 250}**: T84 measured 104…121 contiguously plus 150
  and 200 (22 cells, of which n = 108 and n = 120 were measured twice, once in each of its two
  probes, agreeing); **T100 added n = 122 and n = 250, which are above the top of n T84 swept, and
  both are family B.** At **n = 103** the same shape is **clean** [T84; re-measured by T100].

**The Go port reproduces family B cell for cell — 0 divergent cells** [T84 over all 22; T100 through
the real grader on `T100-FAMB-R600p0-N108-B1`: **761 graded cells, 0 cell diffs**]. On family B there
is **no oracle/port divergence at all**; both compute a schedule that does not repay the loan.

**Family B is NOT order-dependent** [T84, 3 of 3; **re-run by T100**, 3 of 3 unmoved at n = 104, 108,
120 while the family-A control in the same run moved 1.09 → 0.00]. So the family-A mechanism above
does **not** explain family B, and no claim is made that it does.

### What is NOT known about family B

- **Its cause.** T84 measured *that* it is not order-dependent and *that* the principal column sums
  to zero; it did not locate the code path, and neither did T100. `[UNVERIFIED]`
- **Whether it exists at any other rate, at any other principal, or below n = 104.** Every family-B
  cell ever measured is 600.0 % / MNT 0.01 / n ≥ 104. `[UNVERIFIED]`
- **Whether it terminates.** n = 250 fails; nothing above n = 250 has been asked. `[UNVERIFIED]`
- **`MinorUnitDigits ≠ 2`, and Path B / REST.** Not measured, by anyone. `[UNVERIFIED]`

---

## Option (a), RESCOPED — reachable today on family B, needs a port change on family A

Option (a) is *"promote a parity vector for the region with an explicit invariant exemption."*
Whether that works **depends entirely on which family the vector covers**, because
`invariant_exemptions` has power over invariant statuses and none over cell diffs
(`CheckInvariants` runs first at `grade.go:488` and the `len(diffs) > 0` early return at `:489-493`
short-circuits the **outcome**, not the computation [VERIFIED by T100 at those lines]; T83's earlier
citation of `:487-497` as if the diff check ran first was imprecise, per T84).

**Both halves below were measured by T100 in a single run, with the REAL `conformance.Run` and the
REAL Go port, over a throw-away store under `/tmp`, on two cells transcribed from T100's own
capture. Nothing was written to `.softhouse/vectors`; the corpus count did not change**
[`out/exemption-demo-t100.json`; T84 measured the family-B half first, on its own capture, and T100's
run reproduces its numbers].

| | **family B** (600.0 % / MNT 0.01 / n = 108) | **family A** (3.6 % / MNT 1.09 / n = 360) |
|---|---|---|
| graded cells | 761 | 2525 |
| cell diffs | **0** | **1** — `row 360 outstanding_principal_minor: expected 109, got 0` |
| without any exemption | **FAIL**, `principal_portions_sum_to_disbursed` and `principal_amortizes_to_zero` **VIOLATED** | **FAIL** on the cell diff, all six invariants **HOLD** |
| with exemptions | **PASS**, parityPass 1, 0 violations, **zero port change** | **FAIL — unchanged.** The exemptions register as EXEMPT and the cell diff still decides |
| admissible | yes, both variants | yes, both variants |

So:

- **On family B, option (a) is reachable TODAY** — with the existing mechanism, **no port change**,
  and no DEC-n amendment. The failure there is purely invariant, because the port agrees with the
  oracle. This is the cheap option the gate's earlier text said did not exist; it exists, on the
  family T83 never sampled.
- **On family A, option (a) still requires a port change**, exactly as T83 concluded. Its full shape
  is: change the port to emit the oracle's stale balance, *and then* carry the exemptions, because
  at that point the port's own output would violate them. That is a port change no agent has made or
  proposes to make unilaterally.

T83's sentence *"Option (a) is NOT reachable with the existing mechanism alone"* is therefore **true
of family A and false of family B**, and it was recorded here unscoped.

**A caveat on reading those runs:** each variant's process exit code is non-zero for a reason that
has nothing to do with G-8 — a one-vector scratch store trips the corpus-level coverage fatals
(`monthend.reanchor` has no killing vector there; "no parity vector was graded" when the only vector
fails). The **case outcome** and the invariant statuses in the table are the measurement; the exit
code of a scratch store is not.

Prepared and **NOT promoted**, for both families:
`.softhouse/capture/t83-nonamortizing/proposed-vector-{no-exemption,with-exemption}.json` (T83,
family A at 21.6 % / MNT 0.01 / n = 6), `.softhouse/reviews/T84-evidence/proposed-vector-family2-{no-exemption,with-exemption}.json`
(T84, family B).

---

## The bound on the failing principal, RESTATED OVER THE DOMAIN ACTUALLY SWEPT

This file previously said *"Every principal in the region is far below one MNT (the largest anywhere
in the sweep is MNT 0.23)"*. That was true of **T83's grid** and false as a statement about the
graded domain. Restated, with the domain named each time:

- **Over T83's grid** (rates {7.0, 16.8, 21.6, 36.0} × n ∈ {2…56}, principals 1..27 minor): the
  largest failing principal is **MNT 0.23**, at 7.0 % / n = 56.
- **Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates from 0.12 % to
  600.0 %; n from 1 to 600): the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600
  — **11.6× the old bound** [T84 measured it; **T100 re-measured that exact shape independently and
  reproduced it**, and measured MNT 2.92 clean at the same shape].
- **MNT 1.09 fails at 3.6 % p.a. over n = 360 — an ordinary 30-year monthly term at an ordinary
  rate** [T84; **re-measured by T100**, `T100-FAMA-R3p6-N360-B109`, with MNT 1.10 clean beside it].
  This is not sub-MNT dust and must not be described as such. It is still an absurdly small *loan*,
  but the shape that produces it is not absurd.
- The region **grows as the term lengthens and as the rate falls**: at 0.12 % the largest failing
  principal runs 59, 118, 176, 234, 291 minor units at n = 120, 240, 360, 480, 600 — i.e. ≈ n/2
  minor units, which is what the closed form below predicts in the limit r → 0
  [T100's re-derivation, `out/largest-failing.json`; every one of those bracketed by a measured clean
  cell one minor unit above].

**What was NOT swept, and therefore what this bound does not cover.** Only `MinorUnitDigits = 2`,
only MNT, only DAYS_30/DAYS_360, only MONTHS/1, only a single disbursement on the schedule start
date, no down payment, no charges, both multiples-of inputs null, only `(19, HALF_UP)`. Only twelve
annual rates were ever asked — {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6, 36.0, 48.0, 96.0, 300.0,
600.0} — out of a continuum; nothing between 3.6 % and 7.0 %, nothing between 96 % and 300 %,
nothing above 600 %, nothing at or below 0 %. **No term above n = 600 has ever been asked**, and
since the largest failing principal grows with n, **the measurement establishes no upper bound on
the failing principal over the graded domain as a whole** — only over the grid swept. The
practical reading — that no commercially realistic Mongolian loan *amount* has been observed to fail
— holds **over that grid**, and is not a proof about the domain.

## The closed form — TESTED AND FALSIFIED outside the sampled grid

T83 registered *"fails iff `B_minor × a(r,n) < 0.5`"*, where `a(r,n) = r/(1−(1+r)^−n)` and
`r = annual/100/12`, and **labelled it a HYPOTHESIS CONSISTENT WITH the measurement rather than a
measured fact**. **That call was right, and T84's measurement vindicated it.** On T83's own grid it
held on all 32 shapes, 106 of 106 registered predictions, 0 refuted [`check-prediction.py`, exit 0,
re-run by T84 with the same result].

**It is false outside that grid.** T100 re-evaluated it in **exact rational arithmetic**: over
T83's own 330 cells it holds **330 of 330**; over all 342 non-calibration cells of T84's two
captures, **320 held, 22 refuted, 0 exact ties**
[`src/closed_form_check.py`, `out/closed-form-check.json`]. **Every one of the 22 refutations is a
family-B cell** — 600.0 % / B = 1 / n ≥ 104 — where the closed form predicts CLEAN (the exact gap
`B·a − ½` is positive: `+2.429e-19` at n = 104, falling to `+3.025e-36` at n = 200) and the oracle
**fails**. The gap there is below the ulp of ½ at 19 significant digits, which is consistent with
the EMI quantizing to zero in the oracle's own `(19, HALF_UP)` arithmetic — offered as an
explanation, not as a verified mechanism `[UNVERIFIED]`.

**A count correction:** T84's write-up records **18** refutations; T100's exact-rational evaluation
over the same 342 cells finds **22**. The four extra are T84's own probe-1 tie cells
`T84-TIE-R600p0-N{108,120,150,200}-B1`, which `T84-evidence/prediction.json` registers as
`predictedFails: false` and which measured FAIL. Either count supports the same conclusion; 22 is
the number T100 can show.

**So: the closed form is a good description of family A on the grid where it was fitted, and it is
not a law. It does not predict family B at all.** No claim is made for any un-sampled rate, term or
day-count.

## The three options, still undecided — (b) and (c) remain a hard `user` gate

- **(a)** promote a parity vector for the region with an explicit invariant exemption. **Reachable
  today on family B with zero port change; requires a port change on family A.** Scope any decision
  to one family; a vector for one says nothing about the other.
- **(b)** refuse the region from the graded domain as a documented contract-refusal vector. Cheap in
  code for family A over the grid swept — but the region is **not** fully bounded (see the bound
  above: no term beyond n = 600 has been asked, and family B has been seen at only one rate), and it
  is a **graded-domain amendment**.
- **(c)** treat it as an oracle defect and diverge deliberately, keeping the port's `0`. That is what
  the port does *today, ungraded, on family A only* — **on family B the port emits the same
  non-amortizing schedule the oracle does, so there is nothing to diverge from and (c) does not
  describe family B at all.**

**(b) and (c) both amend the graded domain, which is a change to a ratified DEC-n — a hard `user`
gate no agent may cross.** Buyan decides. T83, T84 and T100 each analysed them and **decided none
and recommend none**; T100 attaches only the measurement and the scoping.

**What unblocks it**: a `user` decision, now on **two** phenomena rather than one. **What it
blocks**: nothing today — no vector covers either family and the conformance run is exit 0 without
them. **What it leaves uncovered**: on T84's accounting, **331 measured divergent-or-invalid cells**
sit outside the corpus — 309 family-A port-vs-oracle divergences (198 T83 + 111 T84) plus **22
family-B cells where the PORT ITSELF emits a schedule that does not repay the loan and no vector
says so**. The last 22 are the worse half.

**Conformance is unmoved by this rewrite**: `bash .softhouse/conformance.sh` → **VERDICT PASS, exit
0, 42 parity vectors, 5576 graded cells, 0 invariant violations**. Nothing was promoted; `PIN.json`
and `capabilities.json` are untouched.

### Evidence

**Family A, committed on `softhouse/T83-nonamortizing-boundary`** — `.softhouse/capture/t83-nonamortizing/`:
`PREDICTION.md`, `predicted-boundary.json`, `src/CaptureT83.java`, `src/run-t83.sh`,
`src/classify-boundary.py`, `src/check-prediction.py`, `src/ProbeOrderDep.java`,
`src/run-orderdep.sh`, `src/t83port.go.txt`, `src/run-port.py`, `src/t83grade.go.txt`,
`src/run-exemption-demo.py`, and under `out/`: `capture-t83-raw.json`,
`capture-t83-attestation.json`, `capture-t83-oracle-log.txt`, `measured-boundary.json`,
`port-vs-oracle.json`, `orderdep.json`, `exemption-demo.json`.

**Family B, committed on `softhouse/T84-review-t83`** (and copied unmodified onto
`softhouse/T100-g8-two-families` so these citations resolve) — `.softhouse/reviews/T84-evidence/`:
`PREDICTION.md`, `prediction.json`, `prediction2.json`, `src/CaptureT84.java`,
`src/CaptureT84B.java`, `src/ProbeOrderDep2.java`, `src/run-t84.sh`, `src/run-orderdep2.sh`,
`src/exemption-demo.py`, `src/classify.py`, `src/eval-probe{1,2}.py`,
`proposed-vector-family2-{no-exemption,with-exemption}.json`, and under `out/`:
`capture-t84-raw.json{,.gz}`, `capture-t84b-raw.json{,.gz}`, `port-vs-oracle.json`,
`orderdep2.json`, `exemption-demo.json`. Review: `.softhouse/reviews/T84-review-t83.md`.

**The two-family split, committed on `softhouse/T100-g8-two-families`** —
`.softhouse/capture/t100-g8-rescope/`: `PREDICTION.md` (registered in an ancestor commit),
`prediction.json`, `src/gencases.py`, `src/build_harness.py`, `src/CaptureT100.java`,
`src/run-t100.sh`, `src/postcheck.py`, `src/classify_two_families.py`, `src/column_shape.py`,
`src/closed_form_check.py`, `src/largest_failing.py`, `src/swept_domain.py`,
`src/exemption_demo_t100.py`, and under `out/`: `capture-t100-raw.json`,
`t83-reclassified.json`, `t84-reclassified.json`, `t100-classified.json`,
`column-shape-{t83,t84,t100}.json`, `closed-form-check.json`, `largest-failing.json`,
`orderdep-t84probe-rerun-by-t100.json`, `exemption-demo-t100.json`.
