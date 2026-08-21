# Proposed answers to open gates

Prepared 2026-08-18 at Buyan's instruction to answer gate questions from technical knowledge and from the **Law of Mongolia on Non-Banking Financial Activities** (adopted 12 Dec 2002, State Great Khural) — <https://legalinfo.mn/mn/detail/103>.

Each item is classified:

- **LEGAL** — settled by statute. Cited. Not a matter of preference.
- **ENGINEERING** — my recommendation with reasoning. Take it or overrule it; it is reversible before ratification.
- **RESERVED** — genuinely needs Buyan: a business or licensing fact no amount of source-reading can supply.

The driver may act on LEGAL and ENGINEERING items. It must still stop on RESERVED ones.

---

## What the statute does and does not settle

**It settles deposit-taking.** Article 12.1.3 prohibits an NBFI "to accept deposits or open deposit accounts of individuals or legal entity", and 12.1.4 prohibits accepting deposits by issuing cheques, cards or promissory notes.

**It does not settle arithmetic.** The law is silent on rounding, decimal places, intermediate precision and day-count. Article 15.1 routes financial statements to the Accounting Law, so *presentation* follows that (and MNT minor unit 2); nothing in statute fixes an intermediate `MathContext`. Article 13.4 delegates capital adequacy to FRC regulation — relevant to Tier-A provisioning, not to Run 1.

So: the precision question is **not** a legal question. It is a parity question with a business decision inside it.

---

## G-1 — ratify DEC-1

### 1. `IntermediatePrecisionDigits` — rename, or keep and document? → **ENGINEERING: split it into two fields**

Not a rename. One field cannot carry two senses when the two senses produce different money. Fineract threads one `MathContext` and consumes it as significant digits in `multiply/divide(…, mc)` and as decimal places in `setScale(mc.getPrecision(), …)` (`ProgressiveEMICalculator.java:1962`, `:1979`).

Proposed shape:

- `SignificantDigits int32` — the `MathContext` precision used in multiply/divide.
- `RateFactorScale int32` — the scale passed to `setScale(…)` on rate factors.

Both echoed verbatim in every capture record, so a vector can never be replayed under settings it wasn't captured at. Keeping one field and "documenting both senses" preserves the exact ambiguity that the D-01 capture proves is worth a minor unit per period.

### 2. Ordering rule — reproduce the oracle's order, or reject the request? → **ENGINEERING: reproduce (option a)**

Fineract is the fallback and the shadow-parity partner. If the contract rejects an input the oracle accepts (disbursement landing exactly on a repayment due date), the two sides can no longer be run against the same traffic, which is what shadow testing *is*. Parity first; encode a business restriction, if wanted, as a separate validation layer in front of both implementations — never inside the parity boundary.

### 3. Must the discriminating vector be captured before ratification? → **ANSWERED BY FACT — yes, and it is done**

Captured 2026-08-18 from the pinned oracle (`.softhouse/capture/out/capture-raw.json`): `D-01` at precision 12 vs `D-01-p19` at 19, 18 installments / 18.5 % / principal 87,654,321. Total interest `13,393,481.05` vs `13,393,481.04`; first divergence period 5 principal `4,531,420.25` vs `4,531,420.26`; **17 per-period divergences, never healing**. T5's prediction from source is now empirical.

### 4. `DayCountActualActual` in the Run-1 domain while unvectored? → **ENGINEERING: keep the enum, refuse the computation**

Keep the value in the type (removing it later would be a contract change, which is a gate), but have the Go implementation return an explicit "unsupported: no golden vector" error until one exists. A code path that returns plausible numbers nobody has ever compared to the oracle is exactly the unverifiable promise this project exists to avoid. Adding support later is behaviour, not shape — no contract amendment needed.

### 5. `allowFullTermForTranche` as a pinned-false conformance obligation? → **ENGINEERING: yes, and capture it at `true` too**

Two independent reviewers (T3b, T5) refuted the "dead field" claim: the builder setter reaches it (`LoanApplicationTerms.java:606`) and the guard never consults `isMultiDisburseLoan()` (`ProgressiveEMICalculator.java:142-144`). Pin it false as an obligation, and spend one cheap capture at `true` so the behaviour is documented rather than assumed dormant.

### 6. The Mongolian tenant's rounding mode and precision → **RESERVED, with a strong default**

**Legally unconstrained** (see above). **Technically constrained** by one rule: the Go module must run *exactly* what the production Fineract tenant runs, or shadow parity is meaningless.

Recommended procedure, which the driver can execute without you:

1. Read the **effective** values off the running oracle (no `FINERACT_*` rounding/precision env overrides are set on the current container, so stock defaults are in force) and record them in `.softhouse/reference-oracle.md`.
2. **Pin them explicitly** in the tenant configuration rather than inheriting a default — a default that changes in a future Fineract release would silently move money.
3. Re-capture C-00 at the pinned values so the calibration vector and the production configuration cannot drift apart.

**What is genuinely yours:** whether MNT consumer loans round **HALF_UP** (the borrower-facing convention in most retail lending, and what Fineract's own tests mock) or **HALF_EVEN** (statistically unbiased, the properties default). It changes payable amounts, it will appear in customer contracts and FRC reporting, and no source file can tell us what Gerege intends to sell.

---

## G-2 — permit a third attempt at T2? → **ENGINEERING: yes, once, reshaped**

The failure is systematic, not random: corrections land in the section the review names and miss the sections restating the same claim. So a third identical attempt would fail identically. Reshape it: apply T3b's 10 enumerated edits surgically, then a **mechanical grep sweep** for every restatement of each corrected claim, with the sweep's output attached to the handoff. Cap at one attempt; if it fails again, T3b's review becomes the specification of record and the port is graded on vectors — which is the real acceptance criterion regardless.

---

## Deposit-taking activation — **LEGAL, and now answerable**

Previously deferred as "port yes, activate no". The statute makes the first half unconditional:

- **Under an NBFI (ББСБ) licence: activation is prohibited.** Articles 12.1.3 and 12.1.4. Ported savings code ships disabled by configuration, and an NBFI-licensed deployment exposes no deposit endpoint. This is not a risk judgement; it is the licence.
- **Under a Savings and Credit Cooperative (ХЗХ) licence: permitted, but only from members** — the Law on Savings and Credit Cooperatives allows a licensed SCC to take savings from its members and lend to members only.
- **RESERVED:** which licensed entity actually operates this platform. The two answers differ, so the deployment must know which it is.

Unchanged either way: never render member savings as insured, protected or guaranteed.

---

# DECIDED by Buyan — 18 August 2026

- **Rounding mode: `HALF_UP`.** Closes G-1 item 6's reserved half. All nine existing captures already used HALF_UP, so no re-capture is needed on mode grounds.
- **Licence: NBFI (ББСБ).** Closes the deposit-taking activation gate: **activation prohibited** (Art. 12.1.3 / 12.1.4). Savings code ports but ships disabled with no endpoint exposed. The SCC members-only path does not apply.

## What that resolved on its own, and what it exposed

Precision was left open. It is **not** a business choice: `MoneyHelper.PRECISION = 19` is a compile-time constant and `getMathContext()` returns `new MathContext(19, tenantRoundingMode)` [VERIFIED: `fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java:35, 91-93`]. Only the mode is per-tenant. **Production `MathContext` = `(19, HALF_UP)`.**

So the answer to "significant digits vs scale" is settled empirically rather than by preference: whatever the Go port does, it must reproduce Fineract at precision 19 with HALF_UP, and `SignificantDigits`/`RateFactorScale` are both fed from that one `MathContext` exactly as Fineract feeds them.

**This invalidates most of the current capture set as parity evidence.** `C-00`, `D-01`, `D-02`, `D-02b`, `D-03`, `D-04`, `D-01-p8` and `D-01-mnt` were captured at precision 12 or 8 — precisions production never runs. They remain valuable as *discrimination probes* (they are what proved the ambiguity moves money), but they are not parity vectors. Only `D-01-p19` sits at the production precision.

### Required follow-on work

1. **Re-capture the parity corpus at `(19, HALF_UP)`**, beginning with a fresh `C-00` calibration at those settings. Until that exists, no conformance run can claim production parity.
2. **Re-label the existing captures** in the vector store as `probe` rather than `parity`, so nobody later mistakes a precision-12 vector for evidence.
3. **Pin `(19, HALF_UP)` in tenant configuration explicitly** — never inherit a default that a future Fineract release could move.
4. **T4 retry** may now proceed against T5's nine required changes plus every ENGINEERING answer above; nothing in DEC-1 is blocked on a human any more except the signature itself.

### Still with Buyan

Only the **ratification signature** on the corrected DEC-1 (T6). Every decision feeding it is now answered. When T4's retry and its re-review land clean, DEC-1 is a one-word confirmation away.

---

## New G-1 item (raised by pass-2 Finding 2): `installmentAmountInMultiplesOf` → **ENGINEERING: expose it, honour server semantics, refuse until Path-B vectored**

Pass 2 proved the field is **inert through the embeddable seam** (`LoanApplicationTerms.assembleFrom` reads 18 of the record's 19 components; the accessor is never called) while the **server path honours it** (`LoanApplicationTerms.java:1301-1305, 1617-1618`; `Money.java:154`). So the corpus cannot discriminate between a port that honours it and one that ignores it.

Treat it exactly as `DayCountActualActual`:

1. **Keep the field in DEC-1.** Removing it would be a contract change later, and rounding installments to the nearest 100 ₮ is an ordinary Mongolian product feature — a contract that cannot express it is wrong for this market.
2. **Specify server semantics normatively** in DEC-1, citing the source lines, so the intended behaviour is unambiguous even though Path A cannot show it.
3. **The Go port returns "unsupported: no discriminating vector" when the field is non-null**, until a Path-B (server API) vector exists. Never silently drop it — silent drop is the seam's accident, not a specification.
4. **Mark the capture plan's proposal to close this gap through Path A as impossible**, not merely pending.

Rationale: the failure mode this project exists to prevent is a port that passes its corpus and is wrong. Two fields now demonstrably sit in that blind spot (this one and precision-vs-scale). An explicit refusal converts a silent wrong answer into a loud missing feature — the only honest option while the evidence is out of reach.

**Consequence for Run 1's verification:** `/softhouse-uat` conformance can no longer claim to grade DEC-1 from Path A alone. Path B (captures through the running server API on `:8443`) becomes a prerequisite for the parity corpus, not an optimisation. The oracle is already up and reachable on local fires, so this is schedulable work, not a new blocker.

---

# Standing policy — greenfield (Buyan, 18 Aug 2026)

Gerege NBFI is a new business: no legacy product, no installed base, no existing customer contract. So **the driver chooses and recommends** rather than asking. Only licence facts, CUTOVER, regulatory sign-off, and anything spending real money or exposing a live endpoint still come to Buyan. See CLAUDE.md § Answering gates.

## Decisions taken under that policy

### P-1 · Installment rounding to a multiple → **launch WITHOUT it**

Run-1 loan products ship with `installmentAmountInMultiplesOf = null`. Rounding installments to the nearest 100 ₮ is a legitimate feature, but pass 2 proved the capture seam cannot grade it, so shipping it now would mean shipping an unvectored money path — precisely what this project forbids.

- **Chosen:** launch without multiple-rounding; `installmentAmountInMultiplesOf` stays in DEC-1; the Go port **refuses** (explicit unsupported error) when it is non-null.
- **Rejected:** launch with it and grade later — that certifies a money path no vector can discriminate.
- **Reversible:** yes. Adding it later needs Path-B (server API) vectors and a port change, no contract amendment.
- **Consequence:** Path-B captures drop from *urgent* to *normal* priority. They are still required before this feature can ever ship.

### P-2 · DEC-1 ratification → **agent-decidable on a clean independent review**

Under the greenfield policy, ratifying the first version of the contract is a design decision, not a business fact. When T4's retry passes independent re-review with no rejection-grade findings, the driver ratifies DEC-1, records the rationale, and proceeds to T7/T10. Buyan may reverse it at any point before cutover — and cutover remains a hard `user` gate regardless.

### P-3 · Reporting cadence → **exceptions only**

Routine fire activity is no longer narrated. Surfaced to Buyan: rejections, gates that reach RESERVED, failures that park a context, milestones (a context reaching parity), and anything that contradicts something previously reported as settled.

---

## P-4 · Stop revising the contract — ratify v8 with obligations

**Decision (19 Aug 2026, standing until reversed).** DEC-1 has been through eight revisions and five independent re-reviews. Each round finds fewer and narrower defects, and revision 8 passes a 4,578-cell spec check. The marginal defect caught by revision *n+1* is now worth less than the cost of the entire program waiting on it — all 17 contexts are behind this gate, and **zero lines of the port exist**.

Therefore, on T43's verdict:

- **Clean / ACCEPTED** → ratify immediately, as already provided for.
- **ACCEPTED WITH REQUIRED CHANGES** → **ratify anyway.** Record every residual finding as a numbered **conformance obligation** in DEC-1 §9, each one naming the vector or capture that would settle it. Then start T7 and T10 in the same fire.
- **REJECTED with a defect that changes money** → this is the only case that blocks. Fix that specific defect, ratify, and record the rest as obligations. Do not open a general revision round.

**No revision 9 for anything short of a money-changing defect.** A residual finding recorded as an obligation is not ignored — it is graded by vectors later, which is the real acceptance test. A finding that only exists in prose has never been graded by anything.

**Rationale.** Contract-first was correct and these reviews caught real defects (precision-vs-scale, two silently-dropped inputs, `n`'s definition, the per-period interest specification). But the contract cannot be proven correct by more reading; it can only be proven by a port running against the oracle. Freezing an imperfect boundary with its imperfections *written down and scheduled* beats an unfrozen perfect one that never ships.

**This decision was stated on 18 Aug and not recorded in the repo, so no fire could act on it — which cost revisions 6, 7 and 8.** A decision that lives only in conversation does not exist.

---

## P-5 · Close tier 0 — obligations, not fifth drafts

**Decision (21 Aug 2026, standing until reversed).** T10 passed conformance on its first run — 13/13 parity, 1,350 cells, 0 failures, 6/6 invariants, re-run by the driver rather than taken on report. The port is graded and green. Yet the task list has grown 46 → 153, and its open tail is documentation churn: `T70`/`T72`/`T78` are the third, fourth and **fifth** drafts of one `futureUnrecognizedInterest` write-up, with four more tasks in flight that apply findings from reviews of fixes to reviews.

The same reasoning as P-4 applies, one level up:

- **A finding already covered by a passing vector is an obligation, not a blocker.** Record it in DEC-1 §9 or the context's obligations list, naming the vector that grades it, and close the task.
- **No third draft of a prose item.** If a wording/justification task has been rejected twice, the reviewer's text becomes the record of that item and the task closes `superseded_by_review`. Reviews are already committed artefacts; re-deriving prose a fifth time grades nothing.
- **Money-changing findings are exempt** — they still block, still get fixed, still get re-reviewed. The test is the same as P-4's: does it change a number the oracle would emit? If not, it is an obligation.

**Then close tier 0 and move to Tier A (GL/accounting).** Tier 0's purpose was to prove the pipeline end-to-end on the smallest real slice. It has: oracle pinned, two capture paths, harness green, contract ratified, port passing. Holding it open for prose polish while 16 contexts and ~533k LOC wait is the wrong trade.

**Rationale.** The reviews earned their cost when they caught precision-vs-scale, the two silently-dropped inputs, and `n`'s definition — defects that change money. They stop earning it when they recurse on their own output. The vectors are the acceptance test; anything a vector already grades does not need a fifth prose draft to be true.
