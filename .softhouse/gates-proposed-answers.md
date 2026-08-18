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
