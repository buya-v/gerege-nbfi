# Human decision gates — gerege-nbfi migration

`/softhouse-program` appends a block here whenever it reaches a `user` gate, then parks that context and moves to the next unblocked one. **No automation crosses a gate.** Buyan resolves them here (or in the run report) and the next fire picks the context back up.

Gate classes that always stop:
- **CUTOVER** of any context from Fineract to Go — requires vectors passing + a clean shadow-parity window + regulatory / parallel-run sign-off.
- **CONTRACT** — ratifying or amending DEC-n / the frozen adapter contract.
- **REGULATORY** — FRC / external-audit acceptance, parallel-run sign-off.
- **ACTIVATION** — enabling deposit-taking behavior (FRC / Bank of Mongolia licensing). Porting savings code is not gated; switching it on is.

---

## GATE REGISTER — the authoritative state of every gate id

**Read this table first.** The prose sections below are the *raising and deciding record*, appended
chronologically and never rewritten, so several gate ids appear more than once and an early block can carry a
state line that a later block supersedes. **When a section heading and this table disagree, this table is
right** — it is rebuilt from `.softhouse/program.json.gates_pending` at every fire that touches a gate.
Built by local fire `20260821-125942`.

| Gate | Class | State | Decided by / blocking on | Where the LIVE block is |
|---|---|---|---|---|
| **G-1** | CONTRACT | **CLOSED — RATIFIED** | local fire `20260819-140003` | `## G-1 · CLOSED — RATIFIED` (the `## Open` heading immediately below is STALE for G-1) |
| **G-2** | POLICY | **CLOSED — DECLINED** | local fire `20260820-080002`, `chosen_by: agent` | T2 stays permanently parked |
| **G-3** | ENGINEERING | **CLOSED — Option A** | local fire `20260820-110001`, `chosen_by: agent` | `## G-3 — CLOSED (Option A)`. The earlier `## G-3 raised` block is the raising record only. |
| **G-4** | ENGINEERING | **OPEN — HARD `user` GATE** | Buyan. Amends a **ratified** DEC-n, which no agent may do (CLAUDE.md § Answering gates). | `## G-4` |
| **G-5** | ENGINEERING | **OPEN — HARD `user` GATE** | Buyan. Amends a **ratified** DEC-n. | `## G-5` |
| **G-6** | PRODUCT | **CLOSED — ACCEPTED** | local fire `20260820-140000`, `chosen_by: agent`. Authorises **no cutover**. | `## G-6` |
| **G-7** | — | **NEVER ALLOCATED** | — | The id was skipped. Nothing is missing; do not go looking for it. |
| **G-8** | ENGINEERING | **OPEN** | Not yet asking for a decision. Options (b) and (c) would narrow the graded domain → hard `user` gate; (a) may not. | `## G-8 — TWO phenomena at the rounding floor…`. `## G-8-NOTICE` is SUPERSEDED history. |
| **G-9** | PRODUCT | **CLOSED — DECIDED** | local fire `20260821-054355`, `chosen_by: agent`. Carries a `driver_error_correction`: the decision stands, the driver's stated *consequence* was false. | `## G-9 — CLOSED` |
| **G-10** | ENGINEERING | **OPEN — driver recommends (c), Buyan may overrule** | Blocks nothing today. | `## G-10 — REFINED…` |
| **G-11** | CONTRACT | **OPEN — NOT RATIFIABLE** | The driver, once DEC-2 rev 3 passes a review clean. `chosen_by: agent` is permitted here (CLAUDE.md makes DEC-n ratification agent-decidable); what is NOT permitted is ratifying rev 2. | `## G-11 — DEC-2 rev 2 REJECTED` |
| **G-12** | ENGINEERING | **OPEN — measurement required first** | `A2-29` must measure before anyone recommends. Blocks nothing today. | `## G-12 — Fineract STORES a running balance on the entry` |

**Open right now: G-4, G-5, G-8, G-10, G-11, G-12.** Of those, **G-4 and G-5 are hard `user` gates** (each amends a
ratified DEC-n); **G-8, G-10 and G-12 block no work today** and the driver has recorded a recommendation on each.

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

## G-3 raised — **ENGINEERING** — may `gofmt` rewrite the ratified `contract.go`? *(SUPERSEDED — **CLOSED, Option A**, in the `## G-3 — CLOSED` section below; this block is the raising record, not the state)*

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

## G-8 — TWO phenomena at the rounding floor (one of them in TWO shapes), and a THIRD outcome in which there is no schedule at all, under one gate id

- **id**: G-8
- **class**: ENGINEERING to measure; the *remedy* is a DEC-n amendment, which is a hard `user` gate
- **task**: T75 (found the shape, and stated the family-A mechanism first), T83 (measured family A),
  T84 (reproduced T83, measured family B, and rejected T83's write-up), T100 (rewrote this section
  and re-measured both discriminators), T101 (independent review — reproduced the measurement over a
  **wider** cell set than T100 swept, and rejected the write-up on three sentences), T112 (applied
  T101's corrections and deleted the superseded UPDATE block named below), T114 (independent review
  of T112 — **re-derived every load-bearing number in this section from scratch and all of it
  reproduced**; MICRO-FIX on two false sentences, one of them introduced by T112's own fix), T122
  (applied T114's findings), T129 (independent review of T122 — rebuilt the sentence-by-sentence
  scope audit from scratch, 117 rows, 6 fail, **every failure a scope or disposition statement and
  the measurements perfect**; MICRO-FIX), T140 (applied T129's six findings and adopted the standing
  rule below), **T117** (measured family B past n = 1000, moved the residual to MNT 5.01 at n = 1000
  and found the **PARTIAL** shape; refused to edit this section and said why), **T159** (independent
  review of T117 — APPROVED, then asked past n = 1000 and **doubled** the residual to **MNT 10.01 at
  n = 3000**, found the fourth partial cell, detonated the shared rig's `RuntimeException` handler,
  and produced the 25-site list this rebuild works from; also refused to edit this section),
  **T169** (fixed the shared capture rig to `catch (Throwable)`), **T177** (measured that the
  oracle's `StackOverflowError` is a function of **JVM state**, not of the cell's inputs, and
  reconciled T159 against T169), **T170** (this rebuild: applied T159's 25 sites plus the further
  sites it found itself, split every family-B sentence into FULL and PARTIAL, added the THIRD
  OUTCOME block, and folded in T177)
- **context**: tier0-harness-schedule-poc / loan-schedule
- **state**: **OPEN** — blocks nothing today. T112 fixed the write-up, T122 fixed two sentences in
  T112's fix, and T170 rebuilt the family-B half after T117 and T159 moved the measurement;
  **none of them decided the gate, and none of them may.**
- **raised_by**: local fire 20260820-170001, from T75's approval of T74
- **recorded_in**: `.softhouse/gates.md`
- **supersedes**: the block `## G-8 — UPDATE from local fire 20260820-200002` that stood on `main`
  until T112, together with the two inline `[CORRECTION — local fire 20260820-230001, driver]`
  annotations added to it as a stopgap. That block attributed the **family-B** exemption
  measurement — 761 graded cells, **0 cell diffs**, FAIL turning to PASS under an invariant
  exemption — to **family A**, which is the gate's most decision-relevant sentence stated
  backwards, and it carried the superseded **18**-refutation count. **T112 deleted it in the same
  commit that landed this section**, so this is now the only G-8 write-up in this file. Nothing it
  said correctly is lost; everything is restated below, scoped to the family it belongs to.
  **That claim was audited claim-by-claim twice — by T114, which found exactly one loss (T84's
  12-cell tenant-id/reversed-order re-ask, restored above), and again by T122, which re-read the
  deleted block end to end and restored one further provenance clause (T83's probe topology: no
  server, no database connection). **A third claim-by-claim audit, by T129, found one further
  substantive loss — `main:947`'s "T83 … took no number from T75", the independence claim that makes
  the "T75's report is CONFIRMED" below mean anything — and T140 restored it, verified at source.**
  Verified on a scratch merge into current `main` in a throwaway
  clone: the merged file carries exactly ONE `## G-8` heading, and the only surviving mentions of the
  deleted block are this bullet naming it.**

### STANDING RULE — how to edit this section (adopted at T140, proposed by T129)

This section is the artefact **Buyan reads to decide a `user` gate**, and it has now carried a wrong
number or a wrong scope statement to that reader **five separate times**: a family A/B inversion, an
18-instead-of-22 refutation count born of a float in an analysis script (P-25), an unscoped
"largest n" sentence that contradicted the section ten lines away (P-26), a `tasks.json`
disposition that the author had already reversed and never swept (P-21 by a third route), and — the
fifth, found by T117 and T159 and repaired by T170 — **a whole family description that was true when
written and went FALSE when the measured set grew**: family B was described as *"it sums to 0.00 …
no row carries a non-zero principal … principal MNT 0.01, no other principal has produced a
family-B cell … nothing above n = 250 has ever been asked"*, and the partial shape, 20 distinct
principals and terms to n = 3000 falsified all of it. Every one of the five
was in **prose**, not in a measurement. **The fifth has a different mechanism from the other four
and is the one to guard against next: nobody wrote anything wrong. A sentence with no scope on it
is a standing claim about every future measurement, and it fails silently the day somebody asks a
bigger question.** So:

1. **Nobody edits this section without rebuilding the sentence-by-sentence scope table.** Not a
   grep for the sentence you are changing — a rebuild, claim by claim, of what every sentence
   asserts and the domain it was measured over. T129's rebuild ran to 117 rows and found six
   failures, **all six of them scope or disposition statements in a section whose measurements are
   perfect**. That ratio is the whole reason for this rule.
2. **The editor adds itself to the non-decision roster** at *"decided none, recommended none, and
   pre-implemented none"* below, and to the `task:` bullet above. That roster is the section's own
   attestation; a stale one is a claim made in the name of tasks that never made it.
3. **Sweep for the concept, never for the wording** (P-21 / P-26) — including your own change of
   mind. A correction you later reverse leaves its own restatements behind as fossils, and they are
   the most convincing fossils in the document because they were written by the person who now knows
   better. **A site list handed to you by a reviewer is a starting point, never the sweep** — T129
   named five sites for that `tasks.json` fossil and a concept-grep found **seven**. Then **write
   down what the sweep could not have found**.
4. **Exact arithmetic only, including for display** (P-25). Any number re-derived for this section is
   integer minor units or `fractions.Fraction`; a float in an analysis script has already put a wrong
   count in front of the decision-maker once.
5. **Analyse the `.gz` captures, not the plain `.json` extracts** — see the warning in the Evidence
   block below. The extracts give a plausible, self-consistent, wrong answer.
6. **Verify the merge by merging** (P-24), in a throwaway clone against *current* `main`: exactly one
   `## G-8` heading, no conflict on `.softhouse/tasks.json`, and `gates.md` resolving to your
   branch's blob.

### Read this first: G-8 is TWO phenomena and THREE outcomes, and a remedy for one is not a remedy for the other

Everything below is scoped to the family it was measured on. A sentence about family A is not a
sentence about family B, and neither is a sentence about the graded domain as a whole — the domain
is graded **by sampling**, and rate, principal and `NumberOfRepayments` are unbounded in it
[VERIFIED by T100 at `nexus/internal/apps/loanschedule/contract/contract.go:1163-1170`: *"are graded
by sampling rather than by enumeration … No claim is made that any un-sampled value is safe"*].

**And family B itself has TWO shapes, not one** — the **FULL** shape, in which the principal column
sums to `0.00` and nothing is repaid, and the **PARTIAL** shape, in which it sums to a non-zero
amount that is still short of the disbursement. The partial shape was found by T117 and extended by
T159; **every family-B sentence written before them describes the full shape only**, and the two are
distinguished throughout below. There is also a **third outcome** — the oracle producing **no
schedule at all** — which is neither family and has its own block after this one.

| | **FAMILY A — stale derived column** | **FAMILY B — genuine non-amortization** |
|---|---|---|
| principal column sums to the disbursed amount | **yes** | **NO.** FULL: sums to `0.00`. PARTIAL: sums to a non-zero amount short of the disbursement |
| `totalPrincipalAmount` | = the disbursement | FULL: **`0.00`** · PARTIAL: `0.02` / `0.04` / `0.05` / `1.66` on the four shapes measured |
| non-zero principal rows | exactly **one**, the last, carrying the whole disbursement | FULL: **none** · PARTIAL: exactly **one**, the last, carrying **part** of the disbursement |
| last row's interest | `0.00` | `0.01` **only where the disbursement is 1 minor unit** (150 of the 209 cells); 19 distinct values across the full shape, and `0.11` / `0.12` / `0.14` / `13.32` on the four partial shapes |
| balance column | constant at the disbursed amount | FULL: constant at the disbursed amount · PARTIAL: **two** values — the disbursed amount, then the residual on the last row |
| `totalOutstandingAmount` | `0` | `0` on all 209 — **so this field does not discriminate** |
| forcing the oracle's own balance `Memo` to recompute | balance goes to **`0.00`** | **does not move** — but measured on **3** of the 29 record cells only, all at 1 minor unit; **UNMEASURED** on all 180 cells T117 and T159 added, and on every partial cell |
| the Go port | **diverges**, on exactly one cell per case | **reproduces it cell for cell — no divergence at all** on the **29** record cells (T84's 22, T100's 1 through the real grader, and T101's re-grade of all 29); **UNMEASURED** on all 180 cells T117 and T159 added, and never on a partial cell |
| `invariant_exemptions` as a remedy | **inert** — the failure is a cell diff | **decisive** — the failure is purely invariant — **established on ONE full cell** (600.0 % / MNT 0.01 / n = 108). On a partial cell nobody has checked whether the port even reproduces the oracle, so "purely invariant" is **unmeasured** there |
| measured at | **11** of the 12 annual rates swept (all but 600.0 %), `3 ≤ n ≤ 600`, **312 cells** | **one** annual rate (600.0 %), `104 ≤ n ≤ 3000`, principals **1 … 1001 minor units**, **209 cells** |

Cells behind that table: **312 family-A** (198 T83 + 111 T84 + 3 T100) and **209 family-B** — the
**29** of the four record captures (22 T84 + 7 T100) plus **180** added by T117 (155) and T159 (25).
The 312 and the 29 were re-derived from the committed raw captures by T100's own classifier
[`.softhouse/capture/t100-g8-rescope/src/classify_two_families.py`, `out/column-shape-{t83,t84,t100}.json`];
**all 209 family-B cells and all 312 family-A cells were re-derived again, in integer minor units
from the `.gz` raw captures alone, by T170** [`.softhouse/capture/t170-g8-rebuild/src/extract_t170.py`,
`src/aggregate_t170.py`, `out/extract-t170.json`, `out/aggregate-t170.json` — 1,035 cases read across
seven committed captures, 0 skipped, 0 unclassifiable]. The 209 family-B cells cover **190 distinct
(rate, n, principal) shapes**; the difference is deliberate re-asks under disjoint tenant ids, not
new shapes.

**Every row of that table holds on every cell of its family in the FOUR RECORD captures (T83, T84,
T84b, T100) — no exceptions, no mixed cases.** It is **not** uniform over the 209: the partial shape
splits **four** of the rows (principal-column-sums, `totalPrincipalAmount`, non-zero principal rows,
balance column), a fifth (last row's interest) turns out to have been a statement about a
1-minor-unit disbursement rather than about family B, and **three** of the rows (memo recompute, the
Go port, `invariant_exemptions`) are simply **unmeasured** on the 180 new cells. That
distinction is the whole reason this table now carries a FULL and a PARTIAL entry. The two
*families* remain disjoint, and the discriminator that separates them — *does the principal column
sum to the disbursed amount?* — is **untouched** by any of this [re-derived by T170 over all 1,035
cases; every family-B cell fails it and every family-A cell passes it].

**What was found originally.** T75 registered a prediction, committed it, and only then ran a
calibrated probe against the pinned oracle image (its calibrations reproduced `T64-ZP-A`/`T64-ZP-B`
cell-for-cell with zero input diffs). Result: **MNT 0.01 / 6 × 21.6 % at `MinorUnitDigits = 2` —
inside the graded domain, no multiples-of input involved — makes the reference oracle emit a
schedule whose balance column never reaches zero, `0.01` on every row including the last, while the
Go port returns `0`.** That shape is **family A** [VERIFIED by T112's own re-classification of the
committed raw captures, in integer minor units: `T83-SW-R21p6-N6-B1` — **the shape in the sentence,
MNT 0.01** — has a REPAYMENT principal column summing to 1 minor unit against a 1-minor-unit
disbursement, and a last row still carrying 1 minor unit outstanding. T100 tagged this sentence with
the *neighbouring* cell `T100-FAMA-R21p6-N6-B2` (MNT 0.02), which is also family A but is not the
shape described; corrected here per T101 F-5. The claim was always true — only its citation was to
the wrong cell].

**Why it matters.** On family A this is a live port-vs-oracle divergence on an **admitted** shape,
and it sets two of this project's own rules against each other:

- *"Fineract is the oracle and fallback. No ported Go context is correct until its golden vectors match."*
- *"property invariants … principal amortizes to zero."*

**On family B it is worse and it is different: there is no port-vs-oracle divergence to arbitrate,
because the port agrees with the oracle — both emit a schedule that never repays the loan.** A
declared-divergence mechanism would have to be able to say *"both are wrong"*, which the harness
cannot express today. **That sentence is measured on the 29 record cells only** — all of them full
shape, all at a 1-minor-unit disbursement. **Nobody has graded the port on a PARTIAL cell, or on any
of the 180 cells T117 and T159 added**, so "the port agrees with the oracle" is a claim about 29
cells and not about family B [T170; the gap is stated, not filled — T170 ran no port grading].

Today `conformance.sh` reports PASS with **43 parity vectors, 5,664 graded cells** and 0 invariant
violations — **only because no vector covers either family.** That is precisely the blind spot the
conformance gate exists to eliminate, so a green bar is not evidence against this finding.
[T170 re-ran it: `bash .softhouse/conformance.sh` → VERDICT PASS, exit 0, 43 parity vectors PASS /
0 FAIL, 5664 cells graded, 0 invariant violations, 0 assertions NOT RUN. The **42 / 5576** this
paragraph and the closing paragraph both carried was T112's and T140's measurement and is stale, not
wrong-at-the-time — a count in this section must name the run that produced it.]

---

## THE THIRD OUTCOME — the reference oracle can produce NO SCHEDULE AT ALL

**Added at T170, because until now this section had no sentence for it.** Every other sentence in
G-8 is about *what the oracle emitted*. There is a third possibility, and it has been observed:

> **The reference oracle can answer the request by throwing `java.lang.StackOverflowError`, emitting
> no schedule at all.** So the outcome of asking the oracle a cell in this region is one of **three**
> things — it amortizes, it emits a schedule that does not amortize, or **there is no schedule**.

This matters to the gate and not only to the write-up. **Option (b) proposes to refuse a region from
the graded domain, and a graded domain that can express only "amortizes" and "does not amortize"
will silently classify a crash as one of the two.** Option (b) cannot be drafted without this third
outcome in it. **T170 does not decide option (b); it remains a hard `user` gate.**

**What was observed.** Two of the 49 cases in T159's committed capture carry no `observed` block at
all and an `error` of `java.lang.StackOverflowError: null` — `T159-R600p0-N2000-B10001` and
`T159-R600p0-N3000-B100001` [VERIFIED by T170 by extraction from the raw
`.softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz`: 49 cases, **47 observed / 2
errored**, `out/extract-t170.json` → `summary.errored_cells`]. The captured `errorStackTop` on both
is the reference oracle recursing into itself: frames repeating the pair
`ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI(…:1183)` →
`lambda$calculateLastUnpaidRepaymentPeriodEMI$66(…:1214)` through `java.util.Optional.ifPresent`
[VERIFIED by T170 from the same captured frames; the source reading of `:1183` / `:1211-1212` /
`:1214` at the pinned commit `426a23544` is T159's].

**And the throw is a function of JVM STATE, not of the cell's inputs — T177 measured this, and it
changes what may be said here** [`.softhouse/reviews/T177-stackoverflow-nondeterminism.md`,
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md`; 139 probe trials, 348 seam
calls, 75 java processes]:

- **Cold start throws every time.** The disputed cell (B = 10001 minor units, n = 3000) as the
  JVM's very first seam call, default `-Xss`, C2 on: **33 JVMs, 0 observed, 33 threw.** T159's
  detonation (B = 10001, n = 2000): **9 JVMs, 0 observed, 9 threw** [T177,
  `out/ANALYSIS-ALL.txt` "COLD START" block].
- **Warm-up removes it, as a step function.** Inside one JVM the disputed cell flips from threw to
  observed at **attempt 5** and never flips back — **7 of 7** independent default-flag JVMs, and in
  **107 trials** of that cell no `observed` was ever followed by a `threw` in the same process. The
  warming need not be the same cell: 50 prior calls on a different, never-throwing cell buys the
  same thing (3/3), while 1 and 10 do not (0/3 and 0/3).
- **It moves with `-Xss` and with the JIT.** First call of a cold JVM, 2 JVMs per size: 512k, 1m, 2m
  and 4m **throw 2/2**; 8m and 16m **observe 2/2**. With C2 off (`-XX:TieredStopAtLevel=1`) the
  transition **never happens** — 8 attempts, 8 throws.
- **Therefore a boundary in (B, n) measured by asking each cell ONCE is not a boundary in the input
  space — it is the probe's own warm-up curve.** Any sentence whose premise is such a boundary is
  **refuted at the premise**, not merely imprecise — including the *"it is not monotone:
  `(B=10001, n=2000)` dies while `(B=10001, n=3000)` succeeds"* sentence in the NOTICE block at the
  end of this file, which is corrected there. Under equal JVM state both cells throw (cold) and both
  answer (warm).

  > **CORRECTED BY T182 (independent review of T177), local fire `20260821-125942`.** This bullet
  > previously read *"the throwing region is **not** a region of the input space at all"* — a
  > universal, and **T177's own headline table falsifies it**: at one fixed cold state, `B = 1001`
  > was **observed 9/9** while `B = 10001` **threw 33/33 at the same n**. That **is** an input
  > boundary, at a stated JVM state. The defensible claim — which T177 states correctly in its own
  > follow-up 1 and then contradicts in its Impact §1 — is the one now written above: input
  > dependence is only meaningful **relative to a pinned JVM state**, and a once-per-cell probe pins
  > nothing. This matters practically, because cold-start-per-cell is the design T177 itself
  > recommends and it asks each cell exactly once.
- **T159 and T169 never disagreed about the oracle.** T177 replayed T159's committed case list in
  T159's committed order: the only two cells that threw are exactly the two that threw in T159's
  committed capture, and the money reproduces — **24 comparisons against committed T159 values, 0
  mismatches** [T177, `out/ANALYSIS-ALL.txt` money block]. They asked the same cell at different
  points on a JVM's warm-up curve, and the rig had no field in which to record that.

**G-8's headline number is NOT at risk from this, and the two cells must not be confused.** The
MNT 10.01 residual belongs to **B = 1001 minor units** at n = 3000 (`T159-R600p0-N3000-B1001`). The
cell that throws is **B = 10001**, and **when the oracle answers it, it amortizes fully** — it is not
a family-B cell at all: `totalPrincipalAmount 100.01` against a `100.01` disbursement, final balance
`0.00`, 19 non-zero principal rows [VERIFIED by T170 by extraction from T159's raw capture, where
that cell was observed]. T177 asked the **headline**
cell from **9 cold starts: 9 observed, 0 threw**, with `totalInterestAmount 15010.01` on all 16 of
its observations, matching T159's committed value. **The headline cell is cold-safe.** *The two ids
differ by one digit and the driver's own brief for T177 conflated them; T177 refused that premise
and was right.*

**One artefact to stop misreading.** Every `errorStackDepthTotal` of exactly `1024` in this program's
captures is **HotSpot's recording cap, not a depth** [T177; T170 notes that T159's own capture does
not carry the field at all — it records `error`, `errorCause` and `errorStackTop` only, so the
warning bites on T169-era and later captures]. With the cap lifted
(`-XX:MaxJavaStackTraceDepth=0`) the true depth reached at overflow **varies** as compilation
proceeds — 5119, 4683, 4683, then **8400** frames on the fourth attempt in one JVM, and on the fifth
it fits. T177 measured frame *depth*, not frame *size*, and **asserts no mechanism**.

> **CORRECTED BY T182, local fire `20260821-125942`.** This passage previously said the depth
> **"rises"**. It does not monotonically rise: the series **falls 8.5 %** at attempt 2 (5119 → 4683),
> and the "rises" reading only holds if 8400 is compared to 4683 rather than to the 5119 it started
> from. It is **four points from a single JVM** — too few for a trend either way. What the four points
> *do* support is the weaker and sufficient claim: the depth is **not stable**, so a fixed recorded
> value is not a measurement of it.
>
> **T182 also supplied a stronger argument for the cap than T177 gave**, and it is worth stating
> because it does not depend on the four-point series at all: across the 512k → 4m `-Xss` sweep the
> recorded depth is **exactly 1024, with zero variance, over ~72 throws**. An eightfold change in
> stack size cannot leave a true depth bit-identical — **invariance under a variable that must move
> it is itself proof of a recording artefact.**

**What is NOT known about the third outcome, and must not be filled in:**

- **Its extent.** Only **three** cells have ever been asked as probes under controlled JVM state —
  (B = 10001, n = 3000), (B = 10001, n = 2000) and (B = 1001, n = 3000) — plus a warm-up control at
  (B = 10001, n = 200) and a one-pass replay of T159's 24-cell prefix. Whether
  any **other** committed capture in this program is affected is `[UNVERIFIED]` — T177 did not
  re-run T83, T84, T100 or T117, and neither did T170.
- **The exact `-Xss` boundary.** Measured only that 4m throws and 8m observes, 2 JVMs each; the
  interval was not bisected. `[UNVERIFIED]`
- **The mechanism inside C2**, and whether "attempt 5" is a constant or a compilation threshold this
  cell happens to cross at 5. `[UNVERIFIED]`
- **Whether de-optimisation can flip an observed cell back to throwing.** Never seen in 139 trials;
  no run was long enough to force one. `[UNVERIFIED]`
- **Whether the Go port must reproduce it.** T177 offers, explicitly **as a reasoned inference and
  not as a measurement**, that the throw is an environmental limit of the JVM rather than a semantic
  the port owes. Nothing in this file grades a port on a throwing cell. `[UNVERIFIED]`

**A rig note, because it changes how the older "0 errored" lines should be read.** Before T169 the
shared capture rig caught `RuntimeException`, not `Throwable`, so **no completed run in the history
of this program could print anything other than `0 errored`** [T169]. T169 landed the shared
`catch (Throwable)` recorder (`.softhouse/capture/lib/ThrewOutcome.java`,
`lib/sweep_integrity.py`, `lib/check_no_narrow_catch.py`); T159's own harness had already made the
one behavioural change to `catch (Throwable)`, which is why its two throws were recorded at all.
**An older capture's "0 errored" is therefore not evidence that nothing threw.**

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

**T83's sweep — 330 cells, all family A** [T83, branch `softhouse/T83-nonamortizing-boundary`. The
probe is the **in-process Path A embeddable seam** in a throw-away container built from the pinned
oracle image: it **does not start the Fineract server and opens no database connection**, and it
writes nothing to the running reference-oracle container or its PostgreSQL database
[VERIFIED by T122 at `src/run-t83.sh:5-10`; the seam source is pinned by `cmp` against the pinned
checkout **and** by a sha256 literal in the script at `:99-107`, because two files mutated the same
way compare equal under `cmp`]. **It took no number from T75** — T83 generated its own cells by a
contiguous sweep and re-measured the shape T75 reported from scratch, which is what makes "T75's
report is CONFIRMED" below an independent confirmation rather than a restatement [VERIFIED by T140
at `.softhouse/capture/t83-nonamortizing/src/CaptureT83.java:16`, *"T83 re-measures that
INDEPENDENTLY — it takes no number from T75 — and measures the EXACT BOUNDARY by a contiguous
sweep"*, and `:25-26`, *"THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING … does not classify
them"*. This clause stood in the deleted `main` UPDATE block at `main:.softhouse/gates.md:947` and
was the one substantive claim not carried over; restored at T140 on T129's F-T129-6]. Its
prediction was committed as a strict ancestor of its evidence,
and it calibrates against two already-committed captures with **zero input differences including
tenant id**;
reproduced by T84 byte-identically, canonical sha256 `01b41d9c…3101b`, 332 cases; T84 additionally
re-asked **12 boundary cells with different tenant ids and in a different emission order, with each
boundary pair reversed — 12 of 12 identical**, so the boundary is neither tenant-dependent nor
order-of-emission dependent [`T84-review-t83.md`
§1.3; re-verified by T122 from the committed capture: the twelve `T84-RP-*` cells carry their own
`t84_rp_*` tenant ids, distinct from T83's `cap_t83_*`, and each one's whole `observed` block is
byte-identical to the same-shape T83 cell — 12 matched, 12 identical. **The words "in reversed
order" stood here until T140 and were loose**: measured, the twelve cells' partners sit at T83
emission positions 265, 79, 78, 2, 215, 214, 285, 284, 171, 170, 19, 18 — neither increasing nor
decreasing, i.e. a *scramble* in which the five same-shape boundary **pairs** are each locally
reversed relative to T83 (79 before 78, 215 before 214, 285 before 284, 171 before 170, 19 before
18) and the remaining two cells are singletons. The conclusion is unaffected and fully supported —
T140 re-derived the 12-of-12 byte-identity and the tenant-id disjointness independently — only the
description was wrong]; re-classified a
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
0.01/56 at 21.6 % all fail; **MNT 0.03 through MNT 0.06 — 3..6 minor units, which is the entire
range swept above the boundary at that shape — are clean at 21.6 % / n = 6** [VERIFIED by T112 from
T83's raw capture: exactly principals 1..6 minor were asked at that shape, 1 and 2 fail, 3..6 are
clean, and nothing larger was asked. The earlier phrasing "0.03 **and above**" claimed a half-line
the sweep does not cover — T101 F-7].

**21.6 % is not load-bearing for family A** — family A exists at **11 of the 12** annual rates
swept: every rate from 0.12 % to 300.0 %, and **NOT at 600.0 %**, where every failing cell is
family B and no family-A cell has ever been observed. That is the same count the discriminator
table above carries, and it is spelled out here on purpose: an earlier revision of this paragraph
read "family A exists at **all 12** rates swept", which asserted family A at precisely the rate
that *defines* family B and contradicted that table nine lines earlier. The table had been scoped
and this prose restatement of the same claim had not — pattern P-23 leaking by the exact route
`patterns.md` records [T101 F-1; **independently re-measured by T112** over all 687 swept cells of
the four committed raw captures: the family-A rate set is {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6,
36.0, 48.0, 96.0, 300.0} — **eleven** — and family A at 600.0 % is the **empty set**]. Across T83's
grid the rate moves *where* the boundary sits and moves it DOWN as the rate rises; the region is
**empty at n = 2** at all four rates T83 tested, and grows with the term.

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

## FAMILY B — the principal column does not repay the loan, in FULL or in PART

### Discriminator for family B

**The discriminator is unchanged and still separates the families cleanly:** a cell is family B when
the REPAYMENT rows' `principal` column **does not sum to the disbursed amount** [re-derived by T170
over all 1,035 cases of the seven committed captures: every family-B cell fails this test, every
family-A cell passes it, 0 exceptions]. What has changed is the **description** attached to it, which
was written when only one shape had been seen. **There are two shapes:**

- **FULL — 202 of the 209 cells measured.** The principal column sums to **`0.00`**,
  `totalPrincipalAmount` reads `0.00`, **no** row carries a non-zero principal, and the balance
  column is constant at the disbursed amount. Where the disbursement is 1 minor unit — 150 of the
  209 — the last row carries `interest 0.01`.
- **PARTIAL — 7 measurements over 4 distinct shapes, all found after this section was written.** The
  principal column sums to a **non-zero** amount that is still **short** of the disbursement,
  exactly **one** row (the **last**) carries a non-zero principal, and the balance column takes
  **two** values — the disbursed amount, then the residual on the final row. Measured
  [VERIFIED by T170 by extraction, integer minor units, from
  `capture-t117p2-raw.json.gz` and `capture-t159-raw.json.gz`]:

| shape (600.0 %) | disbursed | amortized | **residual** | `totalPrincipalAmount` | balance column | last row's interest |
|---|---|---|---|---|---|---|
| n = 108, B = 11 minor | 11 | **5** | **6** | `0.05` | `0.11` → `0.06` | `0.11` |
| n = 121, B = 11 minor | 11 | **4** | **7** | `0.04` | `0.11` → `0.07` | `0.12` |
| n = 150, B = 11 minor | 11 | **2** | **9** | `0.02` | `0.11` → `0.09` | `0.14` |
| n = 2000, B = 999 minor | 999 | **166** | **833** | `1.66` | `9.99` → `8.33` | `13.32` |

The first three were found by T117 and re-asked by T159 under **disjoint tenant ids**; the fourth is
T159's and is far larger than the other three. **T170 re-verified the re-ask independently: each
pair's whole `observed` block is byte-identical under a canonical dump (`sort_keys=True`,
`separators=(',',':')`), 3 of 3, while the tenant ids differ (`t117p2_r600p0_n108_b11` vs
`t159_r600p0_n108_b11`, and so on).** So the partial shape is neither a tenant artefact nor a
one-run fluke.

**On all 209 family-B cells the unamortized residual equals the final row's `balance` exactly, and
`totalOutstandingAmount` reads `0`** — 209 of 209, 0 exceptions [T170]. So `totalOutstandingAmount`
still does not discriminate, on either shape.

Forcing the memo to recompute **does not move the balance** — but that was measured on **3** cells,
all full shape, all at a 1-minor-unit disbursement, and it is **unmeasured on every partial cell and
on all 180 cells T117 and T159 added.**

The discriminator is exactly the test the driver's re-derivation named in advance as fatal to the
family-A reframing when applied to all of G-8: *"If it ever fails to sum, the reframing above is
**wrong** and G-8 is the broader finding after all."* It failed.

### What was measured, and over what domain — narrower than family A in RATE, and now WIDER in TERM and in the largest failing PRINCIPAL

**This heading used to read "a MUCH narrower domain than family A", and in the dimensions a reader
cares about that is now false.** Family B is still narrower in **rate** — one annual rate against
eleven — and in the *number* of distinct failing principals: **20** (all odd) against family A's
**66**. But it is now **wider in term** — family A's failing cells run `3 ≤ n ≤ 600` and family B's
run `104 ≤ n ≤ 3000` — and **wider in the largest failing principal**: **1001 minor units
(MNT 10.01)** against family A's **291 minor units (MNT 2.91)** [all four figures re-derived by T170
from the raw captures in integer minor units].

**T84 measured 22 family-B cells; T100 measured 7 more; T117 measured 155 and T159 measured 25 —
209 in total, over 190 distinct (rate, n, principal) shapes** [each count re-derived by T170 from
the raw `.gz` captures; `out/extract-t170.json`]. Union of what has been observed:

- annual rate **600.0 % — and no other rate has ever produced a family-B cell.** T84 swept 300.0 %
  with B = 2 at n = 100, 150, **170…204 contiguously**, 220 and 260 — **41 cells, all clean** — and
  300.0 % with B = 1 at six terms up to n = 260 (n = 100, 150, 175, 196, 220, 260): the 300 %
  failures are **family A** (their principal column sums) [VERIFIED by T100's re-classification of
  T84's raw capture: 6 family-A cells at 300.0 %, 0 family-B. Domain re-derived by T140 from the
  committed `.gz` captures: **the largest n asked at 300.0 % is 260 for both principals**, not 204 —
  204 is the top of the *contiguous* run only, and an earlier revision said "B = 2 through n = 204",
  which under-stated the domain. The 41 B = 2 cells cover 39 distinct n; n = 175 and n = 196 were
  each asked twice and agree].
- principal: **20 distinct values, every one ODD**, from **1 to 1001 minor units** —
  `1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101, 501, 503, 551, 601, 801, 999, 1001`
  [re-derived by T170 from the raw captures: the four record captures contain exactly one of them
  (**1**); T117's two captures contain **14** — `1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101,
  501`; and T159 added **6** — `503, 551, 601, 801, 999, 1001`]. **This bullet used to read
  *"principal MNT 0.01 (1 minor unit) — no other
  principal has produced a family-B cell"*, which was true of the four record captures and is now
  false.** Every family-B principal observed is odd; **that is an observation over 209 cells, not a
  law**, and no even principal has been shown to be safe.
- repayment counts: **`104 ≤ n ≤ 3000`**. Family B has been observed at terms across that whole
  range — **but NOT at every term in it**; there are measured clean gaps inside otherwise-contiguous
  family-B stretches, which is the band structure below.
  - **The four record captures** (T84, T100) cover **n ∈ {104…122} ∪ {150, 200, 250}** at
    600.0 % / MNT 0.01: T84 measured 104…121 contiguously plus 150 and 200 (22 cells, of which
    n = 108 and n = 120 were measured twice, once in each of its two probes, agreeing); T100 added
    n = 122 and n = 250. At **n = 103** that shape is **clean** [T84; re-measured by T100; n-set and
    contiguity re-derived by T112, and again by T170].
  - **T117** added **155** family-B cells — 122 in its pass 1 (principals 1, 3, 5) and 33 in its
    pass 2 (principals 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101, 501). Its family-B terms run
    104, 108, 121, 150, 250, then **300…361 and 364…390** — 362 and 363 are absent from the
    family-B set, which is the band structure showing through — then 620, 630, 640, 650, 860, 870,
    910, 920, 930, 940, 950, 960, 970, 980, 990, 995…1000. **115 distinct terms**, topping out at
    **n = 1000** [term set extracted by T170 from the two raw `.gz` captures].
  - **T159** added **25** more, at principals 1, 11, 501, 503, 551, 601, 801, 999, 1001 and
    `n ∈ {108, 121, 150, 360, 361, 364, 365, 389, 390, 1000, 1200, 1500, 2000, 3000}`.
  - **The old sentence *"Nothing above n = 250 has ever been asked at the family-B shape"* is
    false.** It has been asked to **n = 3000**, and it is family B there. **n = 3000 is simply the
    largest term anyone has asked** — see the residual bound below.
  - Family B is **not a half-line in n and not a bounded island**: T117 found an interleaved band
    structure, with clean gaps inside otherwise-contiguous family-B stretches [T117, reviewed and
    approved by T159]. So a five-point ladder in n cannot bound it, and T159's own registered
    "threshold term of order 2·B" model was **refuted** by its own measurement — B = 801 is family B
    at n = 1000 while B = 601, 701, 751, 901 and 999 are clean at the same term, and B = 1001 is
    clean at n = 1200, 1500 and 2000 and only turns family B at n = 3000.
  - *(Scope note kept from earlier revisions, because it is still the thing that goes wrong here:
    T84's largest n **anywhere** is **600**, at 0.12 % — `T84B-XL-R0p12-N600-B291` — and its largest
    n at 600.0 % / MNT 0.01 is **200**. An unscoped "largest n" sentence contradicted this section
    twice before — T101 F-4, T114 F-T114-2. Every n above is scoped to the shape it was asked at.)*

**The Go port reproduces family B cell for cell — 0 divergent cells — on the 29 cells of the four
record captures, and ON NOTHING ELSE** [T84 over its 22; T100 through the real grader on
`T100-FAMB-R600p0-N108-B1`: **761 graded cells, 0 cell diffs**; T101 re-graded all **29** through the
real `conformance.Run` on `main`'s current port: **25,751 graded cells, 0 cell diffs**]. On those 29
there is **no oracle/port divergence at all**; both compute a schedule that does not repay the loan.
**Nobody has graded the port on any of the 180 cells T117 and T159 added, and nobody has graded it on
a PARTIAL cell at all.** That matters more than it looks: "the port agrees with the oracle" is the
entire reason family B is described as *"both are wrong"* rather than as a port defect, and on the
partial shape it is simply **unmeasured** `[UNVERIFIED]`.

**Family B is NOT order-dependent — measured on 3 cells** [T84, 3 of 3; **re-run by T100**, 3 of 3
unmoved at n = 104, 108, 120, all at a 1-minor-unit disbursement, while the family-A control in the
same run moved 1.09 → 0.00]. So the family-A mechanism above does **not** explain family B, and no
claim is made that it does. **Order-dependence has never been tested on a partial cell, nor on any
of the 180 new cells** `[UNVERIFIED]`.

### What is NOT known about family B

- **Its cause.** T84 measured *that* it is not order-dependent and *that* the principal column sums
  to zero; it did not locate the code path, and neither did T100, T117 or T159. **Nobody has looked
  for it.** `[UNVERIFIED]` A candidate mechanism must now also explain the **partial** shape — one
  non-zero principal row, on the last period — and must explain why B = 801 is family B at n = 1000
  while B = 601, 701, 751, 901 and 999 are clean at the same term.
- **Whether it exists at any other RATE, or below n = 104.** Every family-B cell ever measured is at
  **600.0 %** and at `n ≥ 104`. `[UNVERIFIED]` **The "at any other principal" half of this question
  is ANSWERED and the old sentence is deleted, not softened:** 20 distinct principals from 1 to 1001
  minor units are family B, so "every family-B cell ever measured is 600.0 % / MNT 0.01 / n ≥ 104"
  is **false**.
- **Whether it terminates.** It does **not** terminate anywhere anyone has looked: n = 3000 fails,
  and **nothing above n = 3000 has been asked**. The largest unamortized residual rose from
  MNT 0.01 to **MNT 5.01 at n = 1000** (T117) to **MNT 10.01 at n = 3000** (T159) — **each time
  because somebody asked a larger term, and neither worker found a limit.** `[UNVERIFIED]`
- **Whether the Go port reproduces the 180 new cells, or any partial cell.** Never graded.
  `[UNVERIFIED]`
- **Whether any of the 180 new cells is order-dependent.** Never tested. `[UNVERIFIED]`
- **`MinorUnitDigits ≠ 2`, and Path B / REST.** Not measured, by anyone. `[UNVERIFIED]`
- **Whether an EVEN principal can be family B.** All 20 observed are odd; no even principal has been
  shown safe, and no claim is made either way. `[UNVERIFIED]`

---

## Option (a), RESCOPED — reachable today on a FULL family-B cell, needs a port change on family A, UNMEASURED on a PARTIAL cell

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

- **On a FULL family-B cell, option (a) is reachable TODAY** — with the existing mechanism, **no
  port change**, and no DEC-n amendment. The failure there is purely invariant, because the port
  agrees with the oracle. This is the cheap option the gate's earlier text said did not exist; it
  exists, on the family T83 never sampled. **Scope it exactly: this was demonstrated on ONE cell,
  600.0 % / MNT 0.01 / n = 108, and the port has never been graded on a PARTIAL cell.** On a partial
  cell the oracle emits a non-zero principal on the last row; whether the port emits the same number
  is unmeasured, so whether the failure there is "purely invariant" or a **cell diff** — which
  `invariant_exemptions` cannot touch — is **not known** `[UNVERIFIED]`. **Anything promoted under
  option (a) must name the shape it covers.** And per T177, a capture that promotes a cell must also
  state the JVM state it was taken in (see THE THIRD OUTCOME above): T177 measured G-8's headline
  cell observed **9/9 from cold**, and has **no** cold-start datum for any other family-B cell.
- **On family A, option (a) still requires a port change**, exactly as T83 concluded. Its full shape
  is: change the port to emit the oracle's stale balance, *and then* carry the exemptions, because
  at that point the port's own output would violate them. That is a port change no agent has made or
  proposes to make unilaterally.

T83's sentence *"Option (a) is NOT reachable with the existing mechanism alone"* is therefore **true
of family A and false of family B**, and it was recorded here unscoped.

**How to read the exit codes of those four runs — three of the four ARE this finding, and must not
be discounted.** `Summary.ExitCode()` returns **1** as soon as
`ParityFail + ContractFail + SelfTestFail > 0 || InvariantViolations > 0`, **before it ever inspects
`FatalReasons`** [VERIFIED by T112 at `nexus/internal/apps/loanschedule/conformance/grade.go:154-160`
on current `main`]. So:

- **FAMILY-B-NO-EXEMPTION (exit 1), FAMILY-A-NO-EXEMPTION (exit 1) and FAMILY-A-WITH-EXEMPTION
  (exit 1)** exit non-zero **because of the G-8 failure itself** — the parity FAIL, plus on family
  B the two invariant violations. Those three exit codes are the finding, not scratch-store noise.
- **Only FAMILY-B-WITH-EXEMPTION's exit 2 is unrelated to G-8.** That run has no fail and no
  violation, so control reaches the second branch and the corpus-level coverage fatal decides: a
  one-vector scratch store cannot kill `monthend.reanchor`, which the full committed corpus does.
  That is an artefact of grading one vector in isolation and says nothing about either family.

[VERIFIED by T112 from T100's own committed run record `out/exemption-demo-t100.json`: exit codes
**1 / 2 / 1 / 1** with `parityFail` 1 / 0 / 1 / 1 and `invariantViolations` 2 / 0 / 0 / 0, in that
file's own order — `FAMILY-B-NO-EXEMPTION`, `FAMILY-B-WITH-EXEMPTION`, `FAMILY-A-NO-EXEMPTION`,
`FAMILY-A-WITH-EXEMPTION`; T101 reproduced all four runs independently on `main`'s current port and
got the same codes.] An earlier revision said *each* variant's exit code had "nothing to do with G-8". That
was false for three of the four and taught the reader to discount an honest signal — T101 F-3. The
**case outcome** and the invariant statuses in the table above remain the measurement; what changes
is that three of the four exit codes now agree with them instead of being waved away.

Prepared and **NOT promoted**, for both families:
`.softhouse/capture/t83-nonamortizing/proposed-vector-{no-exemption,with-exemption}.json` (T83,
family A at 21.6 % / MNT 0.01 / n = 6), `.softhouse/reviews/T84-evidence/proposed-vector-family2-{no-exemption,with-exemption}.json`
(T84, family B).

---

## The bound on the failing principal, RESTATED OVER THE DOMAIN ACTUALLY SWEPT

This file previously said *"Every principal in the region is far below one MNT (the largest anywhere
in the sweep is MNT 0.23)"*. That was true of **T83's grid** and false as a statement about the
graded domain. Restated, with the domain named each time:

- **Over T83's grid** (rates {7.0, 16.8, 21.6, 36.0} × the **eight discrete terms**
  n ∈ {2, 3, 4, 6, 12, 24, 36, 56} — a set, not a contiguous range — principals 1..27 minor): the
  largest failing principal is **MNT 0.23**, at 7.0 % / n = 56 [re-derived by T112 from T83's raw
  capture; the discrete-term wording per T101 F-8].
- **Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates from 0.12 % to
  600.0 %; n from 1 to 600): the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600
  [T84 measured it; **T100 re-measured that exact shape independently and reproduced it**, and
  measured MNT 2.92 clean at the same shape; both re-derived again by T112 from the raw captures,
  and again by T170]. **The two absolute figures are the statement — MNT 0.23 over T83's grid,
  MNT 2.91 over the union, a ratio of 291 ÷ 23 = 12.65×.** An earlier revision wrote "**11.6×** the
  old bound". That multiple was taken against a *different* denominator — the "below MNT 0.25" bound
  this file asserted before T83's grid was measured (2.91 ÷ 0.25 = 11.64) — and the rewrite deleted
  every mention of MNT 0.25, leaving a ratio whose denominator the reader could no longer find. It is
  given in absolutes here so it cannot drift again [T101 F-2]. **MNT 2.91 is a FAMILY-A figure over
  the four record captures, and it is no longer the record for G-8** — see the next bullet.
- **Over the union that includes T117's and T159's captures, the largest unamortized residual is
  MNT 10.01 AT n = 3000** — `T159-R600p0-N3000-B1001`, 600.0 %, a disbursement of 1001 minor units,
  **3000** REPAYMENT rows every one of them `principal "0.00"`, `totalPrincipalAmount 0.00`,
  balance frozen at `10.01` from `2024-02-01` to `2274-01-01`, and `totalInterestAmount 15010.01`
  [VERIFIED by T170 by extraction from `capture-t159-raw.json.gz` in integer minor units: disbursed
  1001, amortized 0, residual 1001; 3000 of 3000 REPAYMENT rows at zero principal; one distinct
  balance value across all 3000 rows]. It is a **family-B** cell, not the 0.12 % family-A one.
  - **State it with its term, always: "MNT 10.01 at n = 3000".** The figure was MNT 0.01 while only
    n ≤ 250 had been asked, **MNT 5.01 at n = 1000** once T117 asked (`T117P2-R600p0-N1000-B501` —
    501 minor disbursed, 1000 rows of `principal "0.00"`, `totalInterestAmount 2505.01`, balance
    frozen at `5.01` to `2107-05-01` [VERIFIED by T170 the same way]), and **MNT 10.01 at n = 3000**
    once T159 asked. **The residual doubled when the term tripled, and it doubled because somebody
    asked a bigger question, not because a boundary was found.**
  - **MNT 10.01 is the largest OBSERVED residual, NOT A BOUND.** n = 3000 is simply the largest term
    anyone has asked. **Two independent workers have now raised this ceiling by asking a larger term
    and neither found a limit.** Writing "MNT 10.01" without its term would repeat, one level up,
    exactly the error the MNT 0.23 / MNT 2.91 restatement above was written to correct.
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
nothing above 600 %, nothing at or below 0 %. **T117 and T159 added no new rate: every one of their
180 family-B cells is at 600.0 %.**

**On the term, the premise of this paragraph has changed and the conclusion has not.** It used to
read *"No term above n = 600 has ever been asked"*. That is **false**: terms have been asked to
**n = 3000**, at 600.0 % only, and family B is still there. **The conclusion — that the measurement
establishes no upper bound on the failing principal over the graded domain as a whole — is now
confirmed by measurement rather than inferred**, because each of the two workers who asked a larger
term got a larger residual. Above `n = 600` nothing has been asked at any rate but 600.0 %, and
nothing at all has been asked above `n = 3000`.

The practical reading — that no commercially realistic Mongolian loan *amount* has been observed to
fail — still holds over everything swept to date: the largest failing disbursement anywhere in the
record is **1001 minor units, MNT 10.01**. **It is not a proof about the domain, and it is a weaker
statement than it was**, because the same reading would have said "MNT 0.23" before T84 asked,
"MNT 2.91" before T117 asked and "MNT 5.01" before T159 asked.

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
**fails**. The gap is below the ulp of ½ at 19 significant digits (**1e-19**) on **25 of the 29
family-B cells OF THE FOUR RECORD CAPTURES** — and **NOT** on the four at **n = 104, 105 and 106**,
where it is **2.43, 1.62 and 1.08 ulp** respectively. **Every "29" and every "25 of 29" in this
closed-form block is scoped to those four captures. The closed form has NEVER been evaluated on the
180 family-B cells T117 and T159 added, nor on any partial cell** — T170 did not evaluate it either
`[UNVERIFIED]`. So a sub-ulp argument does not reach the cells at the region's
**lower boundary**, which is where the phenomenon starts and therefore where its cause will be
decided. Sub-ulp quantization of the EMI in the oracle's own `(19, HALF_UP)` arithmetic is offered
as a possible explanation **for the other 25**, not as a verified mechanism, and it is **not** an
explanation for n = 104…106 `[UNVERIFIED]`.

[Re-derived independently by T122 in **exact rational arithmetic** (`fractions.Fraction`, money
parsed as integer minor units, the comparison made against `Fraction(1, 10**19)` — no float on any
decision path, P-25) over all 29 family-B cells of the four committed raw captures — **and over
those only; the 180 cells T117 and T159 added are not in this evaluation**. Exact gaps:
n=104 `+2.4293e-19` = 2.43 ulp (two cells, `T84B-NSW-R600p0-N104-B1` and `T100-FAMB-R600p0-N104-B1`,
agreeing); n=105 `+1.6195e-19` = 1.62 ulp; n=106 `+1.0797e-19` = 1.08 ulp; then n=107 `+7.1979e-20`
= 0.72 ulp and everything above it strictly smaller, down to n=250 `+4.7441e-45`. The gap is
strictly positive on all 29 and strictly decreasing across the 22 distinct n, so the ulp crossing is
**between n = 106 and n = 107** and is crossed exactly once. An earlier revision stated the sub-ulp
claim over the whole family; it contradicted the `+2.429e-19` figure quoted on the line above it —
T114 F-T114-1.]

**What the failure at n = 104…106 means for the open question of family B's cause.** Family B's
mechanism is still `[UNVERIFIED]` and this narrows what may be assumed about it:

- **A "the EMI quantizes to zero because the gap is beneath the arithmetic's resolution" story is
  refuted at the region's first three terms.** At n = 104 the residual is more than **two** units in
  the last place of ½ carried at the tenant's ratified precision — a difference the oracle's own
  `(19, HALF_UP)` arithmetic **can** represent. Whatever makes those cells fail is therefore not
  simple exhaustion of significant digits, and any candidate mechanism must explain n = 104, 105 and
  106 on its own terms.
- **The boundary of the region and the boundary of the sub-ulp condition do not coincide.** The
  region starts at n = 104 (n = 102 and n = 103 are measured clean at the same shape); the sub-ulp
  condition starts at n = 107. A cause that tracked the sub-ulp condition would have put the
  region's edge at 107. It is at 104, so the two are different thresholds and at most one of them
  can be the cause.
- **Consequently the sub-ulp observation is a correlate over 25 of the four record captures' 29
  cells, not the explanation of the family**, and it must not be used to argue that family B is
  confined to residuals too small to matter. **That last warning is now settled by measurement
  rather than by caution: the residual reaches MNT 10.01 at n = 3000**, and the closed form was
  never evaluated at those terms at all. The next worker on family B should start at **n = 104**,
  not in the sub-ulp tail, and should treat locating the code path — which neither T84, T100, T101,
  T112, T114, T117, T159 nor T170 did — as the open work.

**A count correction — and its cause is a FLOAT.** T84's write-up records **18** refutations;
T100's exact-rational evaluation over the same 342 cells finds **22**. **T101 adjudicated the
dispute by recomputing from the raw captures in exact rational arithmetic and RULED FOR 22** — over
T83's 330 cells 330 held and 0 were refuted; over T84's 342 cells **320 held, 22 refuted, and there
were 0 exact ties at all**.

The four disputed cells are T84's own probe-1 "tie" cells
`T84-TIE-R600p0-N{108,120,150,200}-B1`. **T84's `.softhouse/reviews/T84-evidence/prediction.json`
stores `BtimesA` for them as the IEEE-754 double `0.5`** — e.g.
`{"B": 1, "BtimesA": 0.5, "n": 108, "predictedFails": false}`. In exact rational arithmetic
`B·a − ½` at those shapes is strictly **positive** and of order 1e-20 (`+4.799e-20` at n = 108), so
the closed form predicts CLEAN there and the measured FAIL refutes it. Double precision cannot
resolve a residual that small, so four strict inequalities were read as exact ties and dropped from
the count [T101's ruling and its diagnosis; the stored literal `0.5` re-read by T112 from the
committed `prediction.json`].

**Record the cause, not just the correction.** The difference between "two agents counted
differently" and "a float in an analysis script put a wrong number into the document the product
owner reads" is the whole point of this project's no-floating-point rule. That rule visibly bound
the port, the schema, the vectors and the fixtures; it did not visibly bind the **analysis and
prediction scripts**, and this is exactly what that gap costs — the script graded nothing, and its
float still reached this gate. **22 is the count.** The rule is now written down as **P-25** in
`.softhouse/patterns.md`: it binds anything whose output is used to reason about money, and the test
is *"if this number is wrong, does a wrong money claim reach a human?"*

### Two KNOWN DEFECTS in this gate's own probe sources — recorded, deliberately NOT fixed

Found by T114 while reviewing T112 and re-verified by T122. **Neither changes any published number**
— that is stated below as a measurement, not as an assurance. Both are left byte-identical on
purpose: these are **executed probe sources**, and editing one — even a comment — destroys the
byte-reproducibility of a committed capture from the sources that produced it, which is the property
that makes the evidence above worth anything. The same reasoning T112 applied in
`.softhouse/capture/t100-g8-rescope/CORRECTIONS-T112.md` applies here. **A future re-run of either
script must fix these FIRST, in a new pass with new ids, and must not silently re-emit into the
existing `out/` directories.**

1. **A LIVE FLOAT in an analysis script — P-25 in a file, not in a lesson.**
   `.softhouse/capture/t83-nonamortizing/src/classify-boundary.py:102` sorts with
   `key=lambda kv: (float(kv[0][0]), kv[0][1])`, while the same file's own header at **`:20`** states
   *"Nothing here constructs a float."* **The header is false.** This is the *second* live instance
   of exactly the gap the paragraph above is about, and it is sitting inside this gate's own evidence
   set. **No published result is affected, and T122 measured that rather than asserting it:** the
   `float()` is a sort key over annual-rate *labels* only — no money value is converted, and no
   classification, comparison or count reads it. T122 copied the script unmodified to a scratch
   directory, produced a variant differing **only** in that one key (`fractions.Fraction(str(...))`
   instead of `float(...)`), and ran both against the committed capture: the emitted
   `measured-boundary.json` files are **identical**, the stdout boundary tables are **identical row
   for row**, and the unmodified run reproduces the committed
   `out/measured-boundary.json` **exactly**. The four labels T83 swept — 7.0, 16.8, 21.6, 36.0 — order
   the same way under either key. The sibling scripts got this right and said so precisely
   (`swept_domain.py:6`; `closed_form_check.py:13-16`).
2. **`closed_form_check.py` crashes on its own all-clean path.**
   `.softhouse/capture/t100-g8-rescope/src/closed_form_check.py:83` computes
   `min(abs(r['gap_float']) for r in refuted)` with no guard for an empty `refuted`, so an input with
   **zero** refutations exits **1** with `ValueError: min() arg is an empty sequence`. **No recorded
   number is affected:** every count prints *before* the crash, and the committed
   `out/closed-form-check.json` was written by the 342-cell T84 run where `refuted` has 22 members
   and the crash path is not taken. T122 re-ran the script unmodified from a scratch copy (sha256
   `55ecbc8f…`, byte-identical to the committed source, and the committed `out/` untouched): on T83's
   330 cells it prints **330 / 330 held / 0 refuted / 0 ties** and *then* exits 1; on T84's two
   captures it prints **342 / 320 held / 22 refuted / 0 ties**, exits 0, and its output is
   **byte-identical to the committed `out/closed-form-check.json`**. The hazard is a signalling one:
   a script whose job is to report refutations returns a **failure exit on the clean input**, which a
   future re-runner will read as "the check failed" when it means "there was nothing to report".

**So: the closed form is a good description of family A on the grid where it was fitted, and it is
not a law. It does not predict family B at all.** No claim is made for any un-sampled rate, term or
day-count.

## The three options, still undecided — (b) and (c) remain a hard `user` gate

- **(a)** promote a parity vector for the region with an explicit invariant exemption. **Reachable
  today on a FULL family-B cell with zero port change; requires a port change on family A; UNKNOWN
  on a PARTIAL family-B cell, because the port has never been graded on one.** Scope any decision to
  one family *and to one shape*; a vector for one says nothing about the other. Per T177 the capture
  behind any promotion must also record the JVM state it was taken in.
- **(b)** refuse the region from the graded domain as a documented contract-refusal vector. Cheap in
  code for family A over the grid swept — but the region is **not** fully bounded, and it is a
  **graded-domain amendment**. Three things it must now account for, none of which existed when this
  option was first written:
  - **The term half of the old "not fully bounded" reason has changed and the reason still holds.**
    It used to read *"no term beyond n = 600 has been asked"*; terms have since been asked to
    **n = 3000** and family B is still there, with a larger residual each time somebody asked. The
    other half — **family B has been seen at only one rate** — is unchanged and still true.
  - **THE THIRD OUTCOME.** Part of this region cannot be evaluated by the reference implementation
    on demand at all: it can throw `java.lang.StackOverflowError` and emit no schedule. A refusal
    drafted in a graded domain that can express only "amortizes" and "does not amortize" will
    silently classify a crash as one of them. See the THIRD OUTCOME block above.
  - **And the throwing is not a property of the inputs** (T177), so a refusal cannot be written as a
    set of (rate, principal, term) that "the oracle cannot evaluate" — the same inputs answer or
    throw depending on the JVM's warm-up state.
- **(c)** treat it as an oracle defect and diverge deliberately, keeping the port's `0`. That is what
  the port does *today, ungraded, on family A only* — **on the 29 record family-B cells the port
  emits the same non-amortizing schedule the oracle does, so there is nothing to diverge from and
  (c) does not describe them at all.** On the 180 cells T117 and T159 added, and on every partial
  cell, **the port has never been graded**, so whether (c) describes them is **unknown**
  `[UNVERIFIED]`.

**(b) and (c) both amend the graded domain, which is a change to a ratified DEC-n — a hard `user`
gate no agent may cross.** Buyan decides. T83, T84, T100, T101, T112, **T114, T122, T129, T140 and
T170** have each handled them and
**decided none, recommended none, and pre-implemented none**; they attach only the measurement and
the scoping. T112's whole mandate was the write-up: it corrected sentences and deleted a superseded
block, and it moved nothing about the gate's substance; T114, T122, T129, T140 and T170 likewise
touched only the prose. **T117, T159, T169 and T177 measured for this gate and deliberately edited
nothing in it** — T117 and T159 both refused to edit `gates.md` because this STANDING RULE demands a
full sentence-by-sentence rebuild and parallel workers were live; T170 is that rebuild.
**This roster is the section's own non-decision attestation, so it must name every
task that has reviewed or edited the section — T114 and T122 were missing until T140 added them
(T129 F-T129-4), and the omission was invisible to a reader. If you edit this section, add
yourself here.**

**What unblocks it**: a `user` decision, now on **two** phenomena, **two shapes of the second one**,
and **a third outcome in which there is no schedule at all**. **What it
blocks**: nothing today — no vector covers either family and the conformance run is exit 0 without
them. **What it leaves uncovered**:

- **Over the union of everything T83, T84 and T100 swept**, **341 measured divergent-or-invalid
  cells** sit outside the corpus — **312 family-A port-vs-oracle divergences** plus **29 family-B
  cells where the PORT ITSELF emits a schedule that does not repay the loan and no vector says
  so**. The last 29 are the worse half. (T84's narrower accounting gave
  **331** — 198 T83 + 111 T84 family-A plus 22 family-B — because it predates T100's own cells;
  331 is right on T84's set and 341 is right on that union — T101 F-6. T101 then re-graded the whole
  union through the real
  `conformance.Run` and the real port on current `main`: all **312** family-A cells give **exactly
  one** diff each, always the final row's `outstanding_principal_minor`, and all **29** family-B
  cells give **0 cell diffs across 25,751 graded cells**. Family counts re-derived independently
  again by T112 from the four committed raw captures: 687 swept / 312 family A / 29 family B / 346
  clean; re-derived a further time by T170.)
- **Plus 180 further family-B cells** from T117 and T159 that no vector covers **and that nobody has
  graded against the port at all** — so they cannot be added to the "341" figure, which is a count of
  cells whose port behaviour was *measured*. **Uncovered cells: 341 measured + 180 ungraded = 521
  known family-A-or-B cells outside the corpus.** Stating them separately is deliberate: an
  ungraded cell is a worse position than a graded divergent one, not a better one.
- **And an unknown number of inputs on which the oracle throws instead of answering**, which no
  vector and no invariant can express today.

**Conformance is unmoved by this rebuild**: `bash .softhouse/conformance.sh` → **VERDICT PASS, exit
0, 43 parity vectors, 5664 graded cells, 0 invariant violations, 0 assertions NOT RUN** [measured by
T170 on its own branch. T140's rewrite recorded **42 / 5576** at the time and that figure is now
stale — a corpus count in this section must name the run it came from]. Nothing was promoted;
`PIN.json` and `capabilities.json` are untouched.

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

> **READ THIS BEFORE ANALYSING THOSE TWO CAPTURES — the `.gz` is the capture, the `.json` is an
> extract.** `out/` holds **both** forms of each T84 capture and they are **not** the same evidence.
> `capture-t84-raw.json.gz` holds **251** cases and `capture-t84b-raw.json.gz` holds **95** — these
> are the captures, and **every count in this section is derived from them**. The plain
> `capture-t84-raw.json` (**15** cases) and `capture-t84b-raw.json` (**14** cases) are committed
> **extracts**, retaining only the cases cited in `T84-review-t83.md`. They are strict,
> content-identical **subsets**: no id in an extract is absent from its `.gz`, and every id present
> in both is byte-identical under a canonical dump [VERIFIED independently by T129 and again by
> T140]. Each extract also records the full capture's canonical sha256 in
> `_t84_full_captures_canonical_sha256`, and **that digest reproduces exactly over the `.gz`
> captures array** — `3900a204…ccdcbf17` for t84 (251 cases) and `47611b04…22723313` for t84b (95
> cases) — which is independent provenance that the `.gz` is the capture and the extract is a
> faithful excerpt of it [VERIFIED by T140 under `run-t84.sh:109`'s own recipe,
> `json.dumps(caps, sort_keys=True, separators=(',',':'))`; the digest is recipe-sensitive, and a
> canonicalisation that differs in `ensure_ascii` reproduces neither]. **Analysing the plain files
> silently yields a plausible wrong answer** — it produces **16** family-B cells and **3**
> non-sub-ulp exceptions against the true **29** and **4**, and nothing about the run looks wrong,
> because a subset of a capture is a perfectly well-formed capture. T122 hit this and caught it;
> T129 reproduced the wrong numbers exactly, and **T140 reproduced them a third time** — running its
> own classifier over the extracts gives **370** total swept cells and **16** family B (distinct
> n = {104, 105, 108, 120, 121, 122, 150, 200, 250}, of which n = 104 twice and n = 105 give the 3
> non-sub-ulp exceptions), against the true **687** and **29** **of those four captures** — the
> family-B total across all seven committed captures is **209**, see the discriminator table above.
> [T170 hit this warning too and obeyed it: every T170 figure is derived from the `.gz` where a `.gz`
> exists, and its script names each input path and prints the sha256 of the bytes it read.]

**The two-family split, committed on `softhouse/T100-g8-two-families`** —
`.softhouse/capture/t100-g8-rescope/`: `PREDICTION.md` (registered in an ancestor commit),
`prediction.json`, `src/gencases.py`, `src/build_harness.py`, `src/CaptureT100.java`,
`src/run-t100.sh`, `src/postcheck.py`, `src/classify_two_families.py`, `src/column_shape.py`,
`src/closed_form_check.py`, `src/largest_failing.py`, `src/swept_domain.py`,
`src/exemption_demo_t100.py`, and under `out/`: `capture-t100-raw.json`,
`t83-reclassified.json`, `t84-reclassified.json`, `t100-classified.json`,
`column-shape-{t83,t84,t100}.json`, `closed-form-check.json`, `largest-failing.json`,
`orderdep-t84probe-rerun-by-t100.json`, `exemption-demo-t100.json`.

**The independent review that rejected T100's write-up and reproduced its measurement over a wider
cell set, committed on `softhouse/T101-review-t100`** — `.softhouse/reviews/T101-review-of-T100.md`
(56-row sentence-by-sentence scope table; all 29 family-B cells re-graded through the real
`conformance.Run` on `main`'s current port for 25,751 graded cells and 0 cell diffs; all 312
family-A cells re-graded for exactly one diff each; the 18-vs-22 ruling) and
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T101.md`.

**The corrections, committed on `softhouse/T112-g8-rework-retry`** — this section as it now stands,
plus `.softhouse/capture/t100-g8-rescope/CORRECTIONS-T112.md`, which records the one superseded
phrasing (T101 F-4) still carried by that directory's **registered prediction and executed probe
sources**, and why those four files were deliberately left byte-identical rather than edited.
T112 measured nothing new against the reference oracle: every number it added or changed was
re-derived in integer minor units from the four already-committed raw captures, or read from
`grade.go` and `out/exemption-demo-t100.json` in this repository.

**The independent review of T112, committed on `softhouse/T114-review-t112`** —
`.softhouse/reviews/T114-review-of-T112.md` and
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T114.md`. **VERDICT MICRO-FIX.** T114 wrote
its own classifier from scratch, sharing no code with T83's, T84's, T100's or T112's, and
**re-derived every load-bearing number in this section — all of it reproduced**: 687 / 312 / 29 /
346, all ten discriminator rows on 341 of 341 cells, the 11-of-12 rate split, MNT 0.23 / MNT 2.91 /
12.65× / MNT 1.09, 761-with-0-diffs and 2525-with-1-diff, 198 divergent cells one per case, 106/106
predictions, 330/330 and 320-held/22-refuted/0-ties, both canonical digests, and **every** Fineract
and `grade.go` citation. It also **attacked the rig** (P-22): T83's prediction checker was driven
red three ways and probed for vacuity, and it **fails closed** on an empty measurement. It found two
false sentences — corrected by T122 below — and **refused a false premise in its own dispatch
brief** (P-20): the brief attributed the family-B exemption result to family A for the **third**
time, which is the error `main` had already corrected in `95ec06a`.

**T114's findings applied, committed on `softhouse/T122-g8-t114-fixes`** — this section as it now
stands, plus the KNOWN-DEFECTS record in `CORRECTIONS-T112.md` and
`.softhouse/capture/t83-nonamortizing/KNOWN-DEFECTS.md`, and the corrections to T112's and T100's
handoffs. T122 contacted the reference oracle **not at all** and measured nothing new against it:
the four family-B ulp gaps were re-derived in **exact rational arithmetic** from the committed raw
captures, T84's full n-set and the 12 `T84-RP-*` re-ask were re-derived the same way, and the two
probe-source defects were re-verified by running unmodified copies from a scratch directory. It
changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go` and no `nexus/` file, and
it left `.softhouse/tasks.json` at the **merge-base blob `7e49bd93`**, so the branch authors **no
change at all** to the orchestrator's file and any merge into any future `main` takes `main`'s side
with no conflict (F-T114-3, the evil merge in `eea5e80`; a snapshot of `main` was tried first and
was rejected because `main` edits that file continuously — `git diff main --
.softhouse/tasks.json` on the branch is therefore **not** empty, and that is the correct state for a
file the branch must not touch). **Do not "fix" that diff.** The check that means anything is the
post-merge one, and it passes: on a scratch merge into current `main` the merged tree's
`tasks.json` blob equals `main`'s exactly and the path does not appear in the merge at all
[VERIFIED by T122 against `main@79a67d1`, by T129 against `main@fdcdf09` and `main@e35ea7b`, and by
T140 against `main@c535841` — **four different `main` heads, none of which the disposition was
designed against**, which is the whole point of it. The line count of that diff is a function of how
far `main` has moved since the merge base, so no single value belongs in this file: it was 1,097
lines at `main@e35ea7b`, 1,258 at `main@bcf2c55`, and 1,326 at `main@c535841` — three readings
during a single task and its review].

**T129's findings applied, committed on `softhouse/T140-g8-t129-fixes`** — this section as it now
stands, plus the same five-site sweep applied to `T112.md`. T140 contacted the reference oracle
**not at all**: the 687-cell split, the 29 family-B cells, the four ulp gaps and the crossing, the
300.0 % domain, the twelve `T84-RP-*` partner positions and the two capture-extract digests were all
re-derived from the committed capture bytes in **exact rational and integer arithmetic**, by a
script sharing no code with T83's, T84's, T100's, T112's, T114's, T122's or T129's classifiers. It
changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go` and no `nexus/` file, and
it left `.softhouse/tasks.json` at the merge-base blob exactly as T122 did.

**The measurement that moved family B, committed on `softhouse/T117-familyb-probe`** —
`.softhouse/capture/t117-familyb/`, notably `out/capture-t117-raw.json.gz` (202 cases) and
`out/capture-t117p2-raw.json.gz` (89 cases), plus `PREDICTION*.md`, `src/`, and the analysis under
`out/`. Handoff: `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T117.md`.

**The independent review that approved it and then doubled its headline, committed on
`softhouse/T159-review-t117`** — `.softhouse/capture/t159-review-t117/`, notably
`out/capture-t159-raw.json.gz` (49 cases, **47 observed / 2 errored**), `out/rederive-t159.json`,
`out/census-t159.json`, `out/quote-audit-t159.json` (the 102-check P-46 audit) and
`out/guard-red-drives.txt`. Review pointer: `.softhouse/reviews/T159-review-of-T117.md`; the review
in full is `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T159.md`, whose §9 carries the
25-site `gates.md` sweep this rebuild started from.

**The shared rig fix, committed on `softhouse/T169-capture-rig-throwable`** —
`.softhouse/capture/lib/ThrewOutcome.java`, `lib/sweep_integrity.py`,
`lib/check_no_narrow_catch.py`, and the controlled pre/post pair under `capture/src/t169-red/`.

**The JVM-state measurement behind the THIRD OUTCOME block, committed on
`softhouse/T177-stackoverflow-nondeterminism`** — `.softhouse/capture/t177-so-nondeterminism/`:
`src/CaptureT177{,b}.java`, the four trial matrices, per-process raw stdout/stderr for all **75**
java processes under `out/{pilot,matrixA,matrixB,matrixC}/raw/`, every `out/ANALYSIS-*.txt`
transcript, `out/jvm-defaults.txt` and `MANIFEST.sha256`. Write-up:
`.softhouse/reviews/T177-stackoverflow-nondeterminism.md`; handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md`.

**This rebuild, committed on `softhouse/T170-g8-rebuild`** — `.softhouse/capture/t170-g8-rebuild/`:
`src/extract_t170.py` (every figure T170 carries into this section, re-derived **by extraction** in
integer minor units from the seven committed raw captures — no float anywhere, no worker's analysis
layer read, `.gz` preferred wherever one exists, each input's sha256 printed),
`src/aggregate_t170.py` (the FULL-vs-PARTIAL shape facts and the family-A control),
`src/split_claims_t170.py` (the denominator for the sentence-by-sentence rebuild the STANDING RULE
requires), and under `out/`: `extract-t170.json`, `aggregate-t170.json`, `claim-units-t170.json`,
plus `SCOPE-TABLE-T170.md`. **T170 contacted the reference oracle not at all for any G-8 figure**:
the only thing it executed against this repository's own tooling was `bash .softhouse/conformance.sh`
(exit 0, 43 parity vectors, 5664 cells), and every G-8 number it wrote came out of the committed
capture bytes. It changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go`, no
DEC-n and no `nexus/` file. Handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T170.md`.

---

## G-9 — CLOSED (chart of accounts) — local fire 20260821-054355, `chosen_by: agent`

**Class: PRODUCT.** Not RESERVED: CLAUDE.md's RESERVED list is licence facts, CUTOVER, regulatory
acceptance/parallel-run sign-off, and anything spending real money / exposing a live endpoint /
binding a third party. Choosing a launch chart of accounts is none of those. It would become
RESERVED only if it turned on what the **FRC has accepted**, rather than what a greenfield business
elects to launch with — and this decision deliberately does not touch that question.

### The premise, re-derived by the driver rather than taken on report

A2-1's backlog B-5 and A2-3's operational corroboration both claim Fineract ships no default chart.
**Confirmed independently on the pinned checkout `426a23544`:**

- Across the two tenant seed-data changelogs — `0002_initial_data.xml` (1,810 `<insert>` elements)
  and `0003_postgresql_specific_initial_data.xml` (108) — **1,918 seed inserts, of which ZERO target
  `acc_gl_account`** [VERIFIED: driver re-derivation, this fire].
- Across **all** of `db/changelog/tenant/parts/`, `acc_gl_account` appears **only** as
  `createTable` (`0001_initial_schema.xml:49`) and two `createIndex` statements. There is no
  `<insert tableName="acc_gl_account">` anywhere in the changelog set. The 21 files that mention the
  table at all mention it inside **report parameter SQL that SELECTs from it**
  [VERIFIED: driver re-derivation, this fire].

So Fineract ships **the table and no rows**. The gate's premise is sound.

### DECISION

1. **The chart of accounts is DATA, not code.** The Go port implements the GL account *model*,
   `acc_product_mapping` resolution and the posting rules; the chart itself is seed data that lives
   outside the port. This mirrors what the reference oracle actually does, and that is the point:
   porting "the chart" as Go code would invent a structure Fineract does not have, and an invented
   structure **cannot be graded against the oracle** because the oracle has nothing to compare to.
2. **Launch with the minimal chart the captured vectors exercise** — CLAUDE.md's PRODUCT preference:
   the simplest configuration provable against the oracle, features deferred rather than shipped
   unvectored.
3. **An FRC-aligned production chart is a separate, data-only deliverable.** It is not part of the
   A2 port and adopting one in a live deployment sits downstream of CUTOVER, which is already a hard
   `user` gate. Nothing here pre-empts that.

Buyan may reverse any of the three.

### THE DECISION ALONE DOES NOT UNBLOCK THE A2 CODER — the capture does not yet cover the chart

Deciding "the minimal chart the vectors exercise" is only actionable if the vectors exercise a chart
that a loan product mapping can actually be built on. **They do not, and this is a measured gap, not
a worry:**

- The entire A2 capture (327 files under `capture/tierA-a2/out/`) contains **exactly four distinct
  GL accounts, and all four are `ASSET`**: `10000` Assets (HEADER), `10100` Fund Source (DETAIL),
  `10201` Loan Portfolio (DETAIL), `19999` Clean Delete Target Renamed Again (HEADER)
  [VERIFIED: driver enumeration over the committed capture bytes, this fire]. **No INCOME, EXPENSE,
  LIABILITY or EQUITY account was ever created.**
- `LoanProductDataValidator.java:663-710` makes **nine accounts `notNull()`** for *both* cash-based
  and accrual-based loan accounting — FUND_SOURCE, LOAN_PORTFOLIO, TRANSFERS_SUSPENSE,
  INTEREST_ON_LOANS, INCOME_FROM_FEES, INCOME_FROM_PENALTIES, INCOME_FROM_RECOVERY,
  LOSSES_WRITTEN_OFF, OVERPAYMENT. Accrual adds **three more** at `:761-777` — INTEREST_RECEIVABLE,
  FEES_RECEIVABLE, PENALTIES_RECEIVABLE. Everything else in those blocks (GOODWILL_CREDIT, the
  `CHARGE_OFF_*` and `INCOME_FROM_GOODWILL_CREDIT_*` family) is `ignoreIfNull()`
  [VERIFIED: driver read of the pinned source, this fire].

**The capture holds 2 of the 9 mandatory accounts.** So the A2 coder is unblocked on the *decision*
and still short of *evidence*: a capture task must first create the remaining seven — necessarily
spanning INCOME, EXPENSE and LIABILITY types — before any product-to-account mapping can be observed
from the oracle at all. Raised as **A2-7** rather than left as an assumption the coder would
discover the hard way.

`[UNVERIFIED]` — whether the nine/twelve mandatory set at *product creation* is the same set the
*posting* paths require at runtime. The validator is what was read; the journal-entry writers were
not. A2-7 should measure it rather than infer it.

### G-9 CORRECTION — the driver's "2 of the 9" consequence was FALSE. Refuted by A2-7, verified by the driver.

**The DECISION above stands unchanged.** It rests on the seed-changelog measurement (0 of 1,918 `<insert>`
elements target `acc_gl_account`), which was re-derived correctly and independently. **What follows is a
correction to the CONSEQUENCE the driver attached to it**, which was wrong on every count.

The driver wrote that the A2 capture held "exactly four distinct GL accounts, all `ASSET`", that no INCOME,
EXPENSE, LIABILITY or EQUITY account had ever been created on tenant `gerege`, and that "the corpus holds
2 of the 9" mandatory accounts. **All three claims are false**, and A2-7 refuted them *before acting on the
brief* rather than dutifully creating seven accounts that already existed.

Driver-verified against the bytes already committed on `main`, not taken on A2-7's report:

- `out/A2-150-db-final-state.txt` is a **21-row `acc_gl_account` dump spanning all five classifications** —
  including `20100 Overpayment Liability` (2), `40100 Interest On Loans` (4), `40200 Income From Fees` (4),
  `40300 Income From Penalties` (4), `40400 Recoveries` (4), `50100 Losses Written Off` (5),
  `50200 Goodwill Credit` (5) and `30000 Equity` (3).
- `out/A2-072-db-product-mapping-rows.txt` shows **product 22 with all nine mandatory slots mapped**
  (`financial_account_type` 1,2,3,4,5,6,10,11,12), plus goodwill (13) and a payment-channel override.
- A2-7 additionally cites fourteen `POST /glaccounts`, every one HTTP 200, `resourceId` 5–18.

**Root cause, and it is the driver's, stated exactly.** The enumeration walked `out/**/*`, called
`json.load` on each file inside `try/except Exception: continue`, and matched only dicts carrying **both**
`glCode` and `name`. That silently swallowed every psql `.txt` dump — which is where the real state lives —
and every POST request body, which does not carry that shape. The script could only ever find a subset, and
**reported the subset as the whole, with no signal that it had skipped anything.**

This is the program's own recurring failure class — *a check that stops checking and says so nowhere* —
committed by the driver **inside a gate decision, in the paragraph claiming to have measured the gap.**
It is P-32 (a snapshot read as the current state; the driver also passed A2-7 a likely-origin hypothesis it
independently corroborated: `out/A2-019-db-glaccount-rows.txt` is a snapshot taken *before*
`run-020-accounts.sh` ran) compounded by a silent-skip enumerator.

**Consequences for the plan, corrected:**

- **A2-8 (the A2 coder) is NOT blocked on missing accounts.** It never was. The chart and a full nine-slot
  cash mapping were already in the corpus. The dependency A2-8 → A2-7 was justified by a false premise.
- **A2-7 was still worth running, on its own findings rather than the driver's.** What genuinely did not
  exist: any **REST read-back of a non-ASSET GL account**, and **any `GET /loanproducts/{id}` at all** —
  eleven POSTs and **zero reads** in the whole corpus, so the product-to-account mapping had never once been
  observed *at the contract boundary* that A2-8 must port.
- **The runtime-vs-creation question the driver marked `[UNVERIFIED]` is now MEASURED, and the answer is
  NO — the sets differ.** On product 46 (all nine `notNull()` slots mapped, no `ignoreIfNull()` ones),
  charge-off returns **404 `… does not exist for an account of type CHARGE OFF EXPENSE`** and goodwillCredit
  returns **404 `… GOODWILL CREDIT`** — both `ignoreIfNull()` at creation. A product Fineract will happily
  create therefore cannot complete every posting path.
- **A2-7 also refuted its own source reading**, which is the behaviour this pipeline wants: `validateForUpdate`
  marks everything `ignoreIfNull()`, so a PUT flipping cash→accrual without receivables *should* pass — it is
  **refused 400 listing all twelve**, because `ProductToGLAccountMappingWritePlatformServiceImpl.java:410-411`
  re-runs the *create* validator **iff the accounting rule changed**.
- **New, and it is a design input to A2-8, not a defect to fix here:** `A2-214` re-sends a mapping the oracle
  itself accepted as product 23 and gets **403**, because GL account 2 was retyped ASSET→INCOME underneath
  five live product mappings. **The oracle holds that state, reports it without complaint, and will not
  re-create it — and the read-back structurally cannot reveal it**, since `GET /loanproducts/{id}` returns
  `{id, name, glCode}` per slot and **no type or usage at all**. Raised as G-10.

---

## G-10 — REFINED by its own independent review, local fire `20260821-134344` — still **OPEN**

Raised last fire from A2-7's `A2-214` 403. Re-derived and sharpened by **A2-11**, the paired reviewer, whose
brief explicitly asked whether G-10's framing was *accurate and not overstated*. Two answers, opposite
directions, and both matter:

**1. The wording in `gates.md` is CORRECT AS WRITTEN and needs no change — but the reasoning around it was
overstated elsewhere.** The claim "**the read-back** structurally cannot reveal it" is true and stays: `GET
/loanproducts/{id}` returns `{id, name, glCode}` per slot and no `type`, no `usage`. The broader restatement
that *"nothing at the contract boundary reveals it"* is **false** — `GET /glaccounts/2` reveals INCOME
plainly. The distinction is exact and load-bearing: **one call cannot reveal the retype; two calls can.** A
port that resolves classification through a second `/glaccounts/{id}` read is not blind to this. A port that
trusts the product read alone is.

**2. "Five products" UNDERSTATES it — there are five products but SIX mapping rows.** Product **27**
duplicates **gl 16 (ASSET)** and **gl 2 (INCOME)** in a **single payment-type slot**, which the repository
resolves to **one** row. So a slot a porter would reasonably model as unique is not unique in the stored
data, and the count depends on whether you are counting products, mapping rows, or resolved slots. Any
disclosure of G-10 must say which.

### What this does NOT change

The driver's recommendation stands: **(c) — take vectors only from products the oracle would still accept.**
A2-11 did not disturb it, and this refinement strengthens it, since the affected surface is larger than
first recorded, not smaller. **G-10 remains OPEN** and no vector may be taken from the affected products
without saying so.

### And it is now explained, not merely observed

Independently of A2-11, the driver re-derived *why the oracle is in this state at all* —
`.softhouse/reviews/driver-rederivation-20260821-134344-A2-trap3-classification.md`. The only
journal-entries-exist guard on the GL-account update path
(`GLAccountWritePlatformServiceJpaRepositoryImpl.java:151-159`) is keyed on **`USAGE`**, gated on
`isHeaderAccount()`. **`TYPE` is not mentioned**, though `deleteGLAccount` has its own entries-exist check at
`:201-203`, so the repository query was available and simply was not applied to classification. Fineract
refuses to *disable* an account a product points at (`validateForAttachedProduct`, `:178-189`) and permits
*retyping* an account with posted history.

**So G-10 is not an oddity of the capture tenant. It is the documented behaviour of the update path**, and
any Fineract deployment can reach the same state. Combined with `acc_gl_journal_entry` carrying no
classification column, a retype retroactively re-renders every entry ever posted to that account — which is
why trap (3) requires the Go port to carry classification **on the entry**.

---

## G-8-NOTICE (SUPERSEDED — historical record; the LIVE G-8 section is above) — local fire `20260821-134344`: T117's measurement moves the bound. **REVIEWED — T159 APPROVED; the number then DOUBLED; T170 has since APPLIED all of this to the G-8 write-up above.**

**Status of this block, as of T170: SUPERSEDED BY THE SECTION ABOVE, and kept as the record of how the
measurement moved.** Everything in it that was still true has been folded into G-8 itself — the FULL vs
PARTIAL split of family B, the MNT 10.01-at-n=3000 residual, the enlarged rate/term/principal domain, and
the third outcome, which now has its own block (**THE THIRD OUTCOME — the reference oracle can produce NO
SCHEDULE AT ALL**). **Read G-8 above, not this block.** Two things in it are corrected in place below:
the *"not monotone"* sentence, refuted by **T177**, and the framing that made the cell which throws look
like the cell behind the headline residual — **it is not**.

*Original status line, kept because the record is the point:* **"T117 has reported; its paired reviewer
T159 has NOT."** The driver was recording the
measurement here rather than rewriting G-8, because rewriting a gate Buyan decides on, on the strength of a
single unreviewed worker report, is precisely the mistake that produced **P-40** and **P-46** this same fire.
**Nothing below could be quoted to Buyan, or into any disclosure, until T159 returned a verdict** — it has
(APPROVED), and **the rebuild the STANDING RULE requires has since been done, by T170.**

### The headline as T117 reported it — SUPERSEDED BY T159 IN THE UPDATE BELOW; every figure here is T117's

**The failing principal EXCEEDS one minor unit, and no upper bound is established.**

- Largest unamortized residual observed: **501 minor units = MNT 5.01**, at 600.0 % / n = 1000 — 1000 rows
  of `principal "0.00"`, balance frozen at 5.01 for 83 years, MNT 2,505.01 of scheduled interest, principal
  never repaid. That also exceeds the whole-corpus **family-A** record of MNT 2.91. **[T159 has since
  measured MNT 10.01 at n = 3000 — see the UPDATE below. MNT 5.01 is T117's figure, not the record.]**
- **"Sub-minor-unit dust" is dead.** The open question T117 was sent to settle asked whether the failing
  principal could exceed one minor unit. Answer: yes, by a factor of 501 — **and by 1001 once T159 asked a
  larger term.**
- **No bound.** The first failing term grows with the principal (B ≤ 51 fails at n=108; B=101 at 250; B=501
  at 1000; **B ≥ 1001 clean at all five terms T117 asked** — *and B = 1001 is family B at n = 3000, which
  T159 asked and T117 did not; the clean reading was a property of the probe set, exactly as this bullet
  goes on to warn*). Because the largest failing principal **tracks the
  largest term asked**, and nothing above n = 1000 has ever been asked, **MNT 5.01 is the largest OBSERVED,
  not a bound.** T159 has been sent to ask beyond n = 1000 specifically to test whether this is a real trend
  or an artefact of the probe set. *That answer, not this one, is what should reach Buyan.*
- Family B is **neither a half-line in n nor a bounded island** — an interleaved band structure, with clean
  gaps inside otherwise-contiguous family-B stretches.

### One correction the driver makes to T117's own reading, in T117's favour and against it

T117 reports that `gates.md`'s claim "on every family-B cell it sums to 0.00" is falsified by three partial
cells (B=11, n ∈ {108,121,150}, principal column summing to 5, 4 and 2 minor units against an 11-minor-unit
disbursement — a **partial** shortfall, a shape the record did not contain).

The sentence it refers to was the opening of G-8's **"Discriminator for family B"**, and it actually read
*"On every family-B cell **measured so far** it sums to **0.00** against a **0.01** disbursement"*.
**T170 has since rewritten that whole paragraph into a FULL shape and a PARTIAL shape, so the wording quoted
here no longer appears in the file; it is preserved in this NOTICE because the correction is the record.**
So:

- **It was true when written**, and it is explicitly hedged (`measured so far`) and explicitly scoped to a
  `0.01` disbursement — which *is* the B=1 case. T117 slightly overstates by calling it an unqualified
  universal.
- **But T117 is right where it counts:** the *measured set* has now grown, and the hedge is what carried the
  sentence — not a scoping decision anyone made deliberately. Any reader who took `0.00` as the family-B
  signature now has a wrong mental model, and the **partial-shortfall shape is genuinely new**.
- The **discriminator-table row** *"principal column sums to the disbursed amount | yes | NO — it sums to
  0.00"* carried **no hedge at all** and was the one that needed the rebuild. **Repaired by T170**: it now
  reads *"NO. FULL: sums to `0.00`. PARTIAL: sums to a non-zero amount short of the disbursement."*

*Recording both halves because a reviewer's finding is not improved by overstating it, and a gate is not
protected by understating it.* T159 was asked to complete the sweep — T117 listed **nine** affected
sentences and correctly marked that list a starting point, not the sweep (**P-37**); T159 found **25**, and
T170 took those 25 as a floor and swept again.

**A note on the file:line citations in this NOTICE block.** They were accurate against the `gates.md` that
stood when the block was written, and **T170's rebuild moved every line in G-8**. Each one has therefore been
replaced above by the name of the sentence or table row it points at, which does not drift. *A line number in
a document that is actively edited is a citation with a shelf life — cite the claim, not the coordinate.*

### What is NOT in question

G-8's options **(b)** and **(c)** amend the graded domain and remain **hard `user` gates**. T117 decided
nothing about the gate, touched no vector, and did not go near them. **T116** (option (a), the family-B
promotion) is **not** invalidated — its target cell is untouched — but it is deliberately **not dispatched**
this fire: it would move the store's vector count while two reviewers are actively measuring store counts,
and the deflation manifest (**T160**) that would make such a move safe does not exist yet.

### UPDATE — T159 reviewed T117, APPROVED it, and then DOUBLED the headline by asking the question T117 said nobody had asked

**The DO-NOT-CITE hold above is lifted. What replaces it is a larger number and the same warning.**

T159 re-derived every one of T117's figures from the **raw captures**, reading none of its analysis layer:
102 mechanical claim-vs-observed checks — **100 exact, 0 fabrications, 2 scope imprecisions**; all five
committed digests reproduce; the P-9 control genuine by `merge-base --is-ancestor`, with the prediction
commits containing zero observation keys; **17/17 re-asked cells byte-identical under disjoint tenant ids**,
including the MNT 5.01 cell and all three partials.

**Then it asked past n = 1000, which T117 had flagged as the reason its own number was not a bound.**

| | T117 | T159 |
|---|---|---|
| largest unamortized residual | **MNT 5.01** at n = 1000 | **MNT 10.01** at n = 3000 |
| rows of `principal "0.00"` | 1000 | **3000** |
| balance frozen | 83 years | **2024 → 2274** |
| scheduled interest | MNT 2,505.01 | **MNT 15,010.01** |
| partial-shortfall cells | 3 | **4** (new: residual 833 minor against a 999-minor disbursement) |
| distinct family-B principals | 14 | **20**, all odd |

**`T159-R600p0-N3000-B1001` reports `totalPrincipalAmount 0.00`. And n = 3000 is simply the largest term
T159 asked.** The residual **doubled when the term tripled**, and it doubled *because someone asked a bigger
question*, not because a boundary was found.

> **Any disclosure of G-8 must state the residual WITH ITS TERM — "MNT 10.01 at n = 3000" — and must still
> say it is the largest OBSERVED and not a bound.** Two independent workers have now raised this ceiling by
> asking a larger term, and neither found a limit. Writing "MNT 10.01" without its term would repeat, one
> level up, exactly the error T117 was sent to correct.

### THREE THINGS NOBODY HAD RECORDED, and the first one needs a sentence G-8 does not have

1. **THE REFERENCE ORACLE THROWS.** Two cells died with `java.lang.StackOverflowError` —
   `ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI` recursing into itself at
   `ProgressiveEMICalculator.java:1214`. **G-8's write-up has no sentence for a third outcome in which no
   schedule is produced at all** — it contemplates "amortizes" and "does not amortize", not "the oracle
   throws". **Option (b) needs one**, because a graded domain that cannot express "no answer" will silently
   classify a crash as something else. **This finding STANDS and now has its own block in G-8 above
   (THE THIRD OUTCOME), added by T170.**

   > **CORRECTED BY T177 — the reasoning attached to it, not the finding.** This entry originally continued:
   > *"**It is not monotone**: `(B=10001, n=2000)` dies while `(B=10001, n=3000)` succeeds, so this is not a
   > simple size limit and cannot be excluded by bounding the inputs."* **The premise is refuted.** T177
   > measured **139 probe trials across 75 java processes** and found the throw to be a function of **JVM
   > state — warm-up / JIT tier / `-Xss` — not of the cell's inputs**: from a cold JVM, `(B=10001, n=3000)`
   > threw **33 of 33** times and `(B=10001, n=2000)` **9 of 9**; from attempt 5 inside a JVM neither throws.
   > The two cells differ in **run position**, not in behaviour — the first was T159's sweep cell #1 and the
   > second its #27. **So "the throwing region" is not a region of the input space at all**, and any sentence
   > whose premise is a boundary in (B, n) is refuted rather than merely imprecise. The **conclusion** —
   > that this cannot be excluded by bounding the inputs — may still hold; **T177 did not test it**, and it
   > no longer rests on that pair of cells. See the THIRD OUTCOME block above.

   > **AND THE CELL THAT THROWS IS NOT THE CELL BEHIND THE HEADLINE RESIDUAL.** T177 corrected its own
   > dispatch brief on this and it is worth stating here, because the two are one digit apart: the MNT 10.01
   > residual is **B = 1001 minor units** (`T159-R600p0-N3000-B1001`); the cell that throws is
   > **B = 10001**, which **amortizes fully** and is not a family-B cell at all. T177 asked the **headline**
   > cell from **9 cold starts: 9 observed, 0 threw**, `totalInterestAmount 15010.01` every time.
   > **G-8's headline number is cold-safe and is not in doubt.**
2. **A LATENT HOLE IN THE SHARED RIG**, inherited by T83, T84, T100 **and** T117 alike: it catches
   `RuntimeException`, **not** `Throwable`. T159 found it **by detonating it**. T117's "0 errored" is sound
   *for the run that completed*, but the rig **cannot distinguish "none errored" from "none asked that
   errors"** — and a `StackOverflowError` is an `Error`, not a `RuntimeException`, so it is exactly what
   slips through. Raised as **T169** — **which landed**: T169 measured that the hole was not merely blind
   but **unfalsifiable** (no completed run in this program's history could have printed anything but
   `0 errored`) and shipped the shared `catch (Throwable)` recorder. **T177 then explained the apparent
   T159-vs-T169 disagreement about the disputed cell: there was none about the oracle** — replaying T159's
   committed case list in T159's committed order reproduces T159 cell for cell, with **24 money comparisons
   and 0 mismatches**. They asked the same cell at different points on a JVM's warm-up curve.
3. **The discriminator table's `balance column` row** (`gates.md:978` when this was written) —
   *"balance column | constant at the disbursed amount"* is **also falsified** by the
   partial cells, and is **not** on T117's list of nine. **Repaired by T170**: that row now reads FULL
   *"constant at the disbursed amount"* / PARTIAL *"two values — the disbursed amount, then the residual on
   the last row"*, measured on all four partial shapes.

### The rebuild is a task, not a footnote — **and it has been DONE, by T170**

T159's §9 lists **25 `gates.md` sites**, six of them not on T117's nine. Neither worker edited `gates.md` —
correctly, because its STANDING RULE demands a full sentence-by-sentence scope rebuild and parallel workers
were live. **The list was produced; the rebuild was raised as T170 and T170 executed it**, taking those 25
as a floor rather than a ceiling and re-sweeping the file for the concept (P-26/P-37). T170 re-derived every
figure it carried into G-8 **by extraction** from the committed raw `.gz` captures in integer minor units,
reading no worker's analysis layer. **T170 decided nothing**: options (b) and (c) remain hard `user` gates
and option (a) remains T116's.

### Driver's own errors in this exchange, recorded because the record is the point

- **The driver's T159 brief listed 13 principals while saying 14** — `101` was missing. T117's handoff was
  correct; the driver's restatement of it was not. *A brief that miscounts the evidence it is quoting is the
  P-46 shape at one remove: the reviewer was handed a subtly wrong version of what it was checking.*
- T117 attributes `+2.4292883e-19` to T122, but T122 committed `+2.4293e-19`; the 8-digit literal is T100's
  `gap_float` — **a float**. The value is real, the attribution is wrong. Minor, and recorded rather than
  silently fixed.
- The driver's A/B attribution was **right** this time — checked by T159, after being wrong three times
  previously.


## G-11 — DEC-2 revision 2 is REJECTED and MUST NOT BE RATIFIED

**Raised and recorded by local fire `20260822-080001`. Class CONTRACT. State: OPEN — NOT RATIFIABLE.**

This is **not** a hard `user` gate. Under `CLAUDE.md` § *Answering gates*, **DEC-n ratification is
agent-decidable** once the contract passes an independent review **clean** — the driver ratifies, records the
rationale, and proceeds, with Buyan retaining veto. This entry exists to record that the condition **has not
been met**, so that a later fire reading "agent-decidable" does not ratify on that basis alone.

**Review history, which is the whole point of the entry:**

| Review | Verdict | What it left behind |
|---|---|---|
| `A2-14` on rev 1 | **REJECTED** | three shape findings |
| `A2-17` on rev 2 | **MICRO-FIX** | applied its **own** 7-line fix — so the document then stood **reviewed by nobody** |
| `A2-19` on rev 2 post-micro-fix | **REJECTED** | applied **no** fix, deliberately, so the document the driver holds is exactly what was reviewed |

**The rejection-grade finding, driver-reproduced independently before it was written up.** DEC-2 asserts in
three places — banner fact 2, §8.1 fact 2, and A2-17's new §4.10 text — that *"no `ledger` vector CAN
exist."* **That is false.** §5.1's own *heading* carries the true and weaker claim: no `ledger` vector is
**expressible**. Admission-impossibility is strictly stronger, and it fails.

Copy any `loanschedule` parity vector into `.softhouse/vectors/ledger/`, change **only** `case_id` and
`context`, and the harness reports:

```
VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle, 5711 cells compared.
```

`A2-19`'s figures and the driver's own independent probe agree **exactly**: 44 / 5711. The cause is one line
— `context` is constrained only to be non-empty and to equal its own directory name (`admit.go:115`,
`:119-120`); **no allowlist exists.** The strong claim rested on control **PC-3**, which was a **false
negative**: it failed on two *author-correctable* defects, not a structural wall (**P-50** — the prover was
never made falsifiable toward the fix). `A2-16` read a failing control as a wall; `A2-17` re-derived the
*argument* but never re-ran the *corrected control*.

**What unblocks G-11:** `A2-20` (close the `context` hole), then `A2-21` (DEC-2 revision 3 — retract the
three false assertions, and give §5.2 a specification that is more than non-regression), then a further
independent review passing **clean**.

**What A2-19 CONFIRMED, so this is not read as a document without merit:** 47 of 47 Fineract citations hit at
their exact cited lines (overall `[VERIFIED]` hit rate **62/64 = 96.9%**, one drift and one wrong, neither a
money claim); §5.4's retraction reproduced exactly; the banner, §8.1 and §8.3 **do** defuse the I-3/I-4
misreading; and **P-8 is genuinely independent of P-1…P-5**, which is what licensed `A2-18` to build the
ledger-invariant guard this same fire.

**No `user` gate was crossed to record this, and none is being asked for.** G-4, G-5, G-8 and G-10 are
untouched.


## G-12 — Fineract STORES a running balance on the entry, and our non-negotiable says balances are DERIVED

| | |
|---|---|
| Gate class | ENGINEERING |
| Task | `A2-29` (measurement), raised by `A2-26` |
| Context | `tierA-gl-accounting` / slice `A2` |
| Raised by | local fire `20260822-000013` |
| State | **OPEN — measurement required before a recommendation.** Blocks nothing today. |

**The finding.** `A2-26`'s DB dump — `.softhouse/capture/tierA-a2/out/A2-370-db-ledger-state.txt` — records
that `acc_gl_journal_entry` carries **`office_running_balance`** and **`organization_running_balance`**.
Fineract stores a balance **on the entry**.

**Why it is a gate and not a bug report.** Two instructions in `CLAUDE.md` meet in this one column:

- *"The ledger is double-entry and append-only. **Balances are derived, never written.**"*
- *"Contract-first, schema-first, strangler … **adopt Fineract's PostgreSQL schema**."*

So the reference oracle does the thing the port is forbidden to do, in a table the port is instructed to
adopt. This is the **same shape as G-8** — "Fineract is the oracle" set against a stated invariant — and
G-8's handling is the precedent: **measure the boundary first, then choose.**

**What must be measured before any option is argued** (this is `A2-29`, and it is the whole point):

1. Are those columns ever **READ** to serve a balance, or only written? Every reader in the pinned checkout
   `426a23544`, cited.
2. Do they reach any **contract-boundary** response, or are they purely internal? `A2-26` found them in a
   `psql` dump — that is not the same as finding them in `/journalentries`.
3. **Can the stored value DISAGREE with the derived sum?** A stored balance that always equals the derived
   one is a **cache**; one that can drift is a **second source of truth**. The two cases have completely
   different consequences for the port, and no option should be argued before this is known.

**Options, not a closed list, and none is chosen yet:**

- **(a)** The port derives balances and simply does not populate the columns — a schema-level divergence that
  no contract-boundary cell exposes.
- **(b)** The port writes them to keep the adopted schema byte-compatible for shadow-parity, while **never
  reading** them — honouring *"derived"* in behaviour and *"schema-first"* in storage.
- **(c)** Treat any vector cell exposing them as outside the graded domain. **This narrows the graded domain
  and is therefore a HARD `user` gate** — recommendable, not takeable.

**Blocks nothing today.** No `ledger` vector exists yet (G-11 is open), so no vector grades the column. The
risk is that it becomes load-bearing silently once one does.

