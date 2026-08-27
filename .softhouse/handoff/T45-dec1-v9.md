# T45 — DEC-1 revision 8 → revision 9 (erratum)

| | |
|---|---|
| Task | T45, `spec_writer` |
| Branch | `softhouse/T45-dec1-v9` |
| Artefacts | `docs/adr/DEC-1-schedule-generator-adapter.md` (revision 9), `nexus/internal/apps/loanschedule/contract/contract.go`, `.softhouse/reviews/t45-probe/` |
| Inputs | `.softhouse/reviews/T43-DEC-1-v8-rereview.md` (primary), `.softhouse/reviews/T44-capture-audit.md`, `.softhouse/handoff/T44-capture-audit.md`, `T41-dec1-v8.md`, T39/T40/T42 handoffs, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| Oracle contacted | **No.** No container, no Gradle, no HTTP. Every observation is quoted from a committed capture with its id. |
| Prior branch check | `git branch -a --list 'softhouse/T45*'` → **none**. No prior work to resume. |
| Contract shape | **No type, field set, enum member or graded-domain predicate moves.** §3.1 byte-identical to revision 8; `contract.go` diff against `main` is **0 non-comment lines** (filtered diff, run by this task). |

---

## 1. What changed, per finding

### P1-T43-1 — the citation that refuted the decision it supported. **CONFIRMED, four sites re-pinned.**

Revision 8 cited `AbstractCumulativeLoanScheduleGenerator.java:504` four times as where the
cumulative generator differs from the progressive one.

**Re-derived independently here.** `:504` is byte-identical to
`ProgressiveLoanScheduleGenerator.java:486` — `md5` of each line is
`364d5bfb99ae0249e5392a89164d033a`. Both are `updatePeriodsWithCharges`, iterating the
`nonCompoundingCharges` **separated** set only. The two whole methods differ **only** in their
parameter types (`MonetaryCurrency` vs `CurrencyData`) and in whether the two `PrincipalInterest`
`Money.of` calls carry `mc`. `:504` is the one line the two generators **share**.

**The real mechanism** — and it is a *different mechanism*, not an extra call: the cumulative
generator folds the period's charges into the period total **before** adding it.
`applyChargesForCurrentPeriod` [`:349`] → `fetchTotalAmountForPeriod()` [`:352`, defined at
`ScheduleCurrentPeriodParams.java:144-146` as `principal + interest + fee + penalty`] →
`addTotalRepaymentExpected(totalInstallmentDue)` [`:392`]. Against the progressive generator's
`:137`, `addTotalRepaymentExpected(principalDue.plus(interestDue, mc))`, which carries no charge
term, and `:140` → `:367-382`, which writes only the two columns and the two cumulative totals.

**Decision C-1 stands unchanged.** Sites corrected: §4.5.1's mechanism paragraph, §4.5.1's
blind-spot bullet 4, §9's adapter obligation, the revision-8 history entry, and
`contract.go:1330ff`. The document now says explicitly that `:504` and `:486` are the same line,
so the next reviewer does not re-raise it.

Probe: `.softhouse/reviews/t45-probe/t45-cumulative-vs-progressive-output.txt`
(regenerable: `gen-cumulative-vs-progressive.sh`).

### P1-T43-2 — the exhaustiveness claim. **CONFIRMED, and the FORM of the claim changed.**

Enumerated mechanically: `Money.java` has exactly **7 direct `MoneyHelper` reads** (`:103`,
`:115`, `:119`, **`:131`**, `:154`, `:160`, `:495`) and **4 indirect routes** through the
two-argument `Money.of` (`:169`, **`:233`**, **`:266`**, `:377`). Revision 8 listed 8 of the 11;
the three in bold were missing. `ProgressiveEMICalculator.java:182` passes the **one-argument**
`Money.zero(CurrencyData)` → `Money.java:130-132` → `:131` → ambient, gated on
`isAllowFullTermForTranche()` [`:142-144`] — **a §4.4 pin, not a §3.1 predicate**, so revision 8's
closing sentence was false of it.

**The change that matters is not the three additions.** The list is now stated as a **closed set
over one file** (which is machine-checkable, and was checked), and the *conclusion* — that no
in-graded-domain Path-A execution reads the ambient context — **no longer rests on it**. It rests
on **T42's absence test**, an experiment over the whole call graph. Rationale, stated in the
document: this enumeration has now been wrong twice (T42 forced the first widening, T43 the
second), and a claim that has been wrong twice should not be load-bearing a third time.

Sites corrected: §4.1.2's enumeration bullet, §4.1.2's closing bullet, §4.1.2's P4 prediction,
§4.1's "One mode, not three" list, §4.1's adapter-obligation paragraph, and `contract.go:736ff`
and `:808ff`.

Reachability of `:224-234` and `:261-267` on the Path-A call graph is left `[UNVERIFIED]`, as
T43 left it. All 79 `.plus(` call sites in `fineract-progressive-loan/src/main` were inspected
and none passes a collection or a `double` — recorded as a grep result, not a proof
(`t45-plus-callsites.txt`).

Probe: `t45-ambient-sites-output.txt` (regenerable: `gen-ambient-sites.sh`).

### P1-T43-3 — M4 and the instalment fee. **CONFIRMED, and the corpus REFUTES revision 8's wording on 8 of 21 captures.**

Re-derived from `ProgressiveLoanScheduleGenerator.java:400-415`. `isDue` — which *is* M4 — is
computed at `:403`; the `isInstalmentFee()` arm at `:404-405` **never reads it**. An
`INSTALMENT_FEE` lands on **every** repayment row with no membership test. M4 gates only `:406`,
`:408`, `:411`.

**Revision 9 narrows M4 and adds M5 — "no membership test at all" — as the table's fifth
convention.** The section heading, the intro, the "which rule governs which field" sentence, §9's
obligation, `contract.go`'s doc block and every restatement were updated; the count moved from
four rules to five conventions.

Observed money: `FC-02` (flat MNT 2,500 `INSTALMENT_FEE`) moves **12** charge cells,
`totalFeeChargesCharged` `30,000.00` = 2,500 × 12; `FC-07` (flat MNT 9,000 `SPECIFIED_DUE_DATE`)
moves **1**. A port on revision 8's wording collects 2,500.00 where the oracle charges 30,000.00 —
**MNT 27,500 lost** on that shape.

**A second, smaller defect this task found while modelling it** (see §4 below): revision 8's M4
row stated the flag's *main-loop* semantics only, leaving the separated-path staleness to the
following paragraph and to §4.5.1 C-2b. A from-text model of the row alone mis-predicts `FC-20`
and only `FC-20`. **Revision 9 moves the per-path flag statement into the M4 row itself.**

### P2s

- **P2-T43-1 (down-payment term).** Confirmed: `addTotalRepaymentExpected(downPaymentAmount)` at
  `ProgressiveLoanScheduleGenerator.java:345`, inside the `isDownPaymentEnabled()` branch at
  `:332-347`. Inert under §4.4's `Rate{0, 1}` pin. C-1's forward semantics are now written as a
  full four-term formula instead of a three-term prose clause.
- **P2-T43-2 (1,224 vs 1,239).** Confirmed and **explained**: T39's analysis compares 4
  schedule-level totals + **3** disbursement-row cells + 9 per repayment row
  (`discriminate.py:39-60`); T41's model compares the same but only **2** disbursement-row cells
  (`t41_validate.py:215-224` — no `fromDate`). One cell per capture, 15 in all. Each count now
  states its leaf set. The "four corpora" that listed five items is corrected to five.
- **P2-T43-3 (stale first-witness cell). NOT CONFIRMED, and revision 9 says so.** T38's probe
  reports `T37-3c` cell `R2.principal` with figures (`2,051,365.77` against the observed
  `2,051,365.78`); T41's probe reports `R2.balance` because it takes `sorted(diff)[0]` —
  **lexicographic** order (`t41_discriminate.py:143`). Both are differing cells of the same
  capture; neither is stale. The same applies to `P-01`, `T37-3-A`, `T37-3a` and `T39-P0-A`, where
  the two probes also disagree — so had this been "fixed" as raised, four *more* cells would have
  been churned to no purpose. The column is renamed "one witnessing cell" and the ambiguity is
  documented. **This is the one T43 finding revision 9 declines.**

### T44, folded in

- **F39-1 (NARROWS a claim).** The four `T39-ME-*` captures grade the **pair** — packed
  whole-months **and** the month-end special case — not the special case alone. Narrowed in
  §4.1.1 step B, §4.3.2's evidence table, §4.3.1's discriminate table (a new row for the
  corpus-blind reading), §8 item 3f, §9 obligation (f), and two revision-history restatements.
  **§4.1.1 step B already pinned the two clauses as a pair (revision 8's own finding F-1), so
  nothing normative changes** — what changes is every claim about what the captures *grade*.
  §8 item 3f now names the `YEARS`/`WEEKS`/`DAYS` arms as where a special-case-alone discriminator
  must come from, and is **written so that the sibling capture task's result settles it either
  way**: a shape that separates the clause upgrades "captured as a pair" to "captured separately"
  and changes nothing normative; a failure to find one leaves the pair statement standing.
- **A-3 (NARROWS a claim).** The charge money came from the **request** `amount`, not the
  attested definitions. Added to §4.5.1 fact 4, to §4.5.1's blind-spot list as a new entry, to
  §8 item 1's machine-readable requirements, to §8 item 9's `TO_BE_CAPTURED` list as item (g), and
  to §9's capture-programme obligation. The fixture of any promoted charge vector is the
  **request bytes**.
- **A-5 (a revision-8 claim that is FALSE).** Revision 8 recorded T40's claim that no charge
  percentage lands on an exact half-cent tie against period-1 interest. One does: `0.001875 %` of
  `21,600.00` is exactly `0.405` and the oracle returned `0.41`. The blind-spot bullet is
  rewritten to record the observation and to say that what remains is *promotion*, not a search.
  **Nothing in DEC-1 rested on the false claim.**
- **A-4 (touched lightly).** §9's C-1 obligation now labels `INVARIANTS.md` C5 a **discrimination
  probe** rather than an invariant, which is what C-1's own next sentence already required.

---

## 2. Leak grep

`t45_leakgrep.py`, run over **both** artefacts, 11 retired patterns, each hit classified as a live
leak or an explicit acknowledgement using a ±3-line context window. **Result: 0 live leaks.**
Output: `t45-leakgrep-output.txt`.

| pattern | hits | live |
|---|---|---|
| `AbstractCumulativeLoanScheduleGenerator.java:504` as a difference | 6 | 0 |
| "the cumulative generator does the opposite / adds them" | 0 | 0 |
| M4 as "which row a CHARGE lands on", unqualified | 2 | 0 |
| "the FOUR date-membership rules" / "all four of §4.3.2" | 0 | 0 |
| "reached at exactly these call sites" | 0 | 0 |
| "every remaining site sits on the installment-multiple …" | 1 | 0 |
| the four-site tenant-global list `Money.java:103, :115, :160, :377` | 0 | 0 |
| "separates step B's month-end special case", unqualified | 0 | 0 |
| "T40 proved none exists" (the half-cent tie) | 0 | 0 |
| a bare cell count with no leaf set | 0 | 0 |
| C-1's three-term progressive semantics | 0 | 0 |

**P1-T43-1 was itself a leak — one wrong citation repeated four times — and the same pattern held
for the others**: M4's wording had 6 sites, the ambient list 4, the month-end claim 7, the cell
counts 4, the half-cent claim 2. Every one was found by grepping the whole document rather than by
editing where the reviewer pointed.

---

## 3. Citation check

Two probes, because the range check is not the one that would have caught P1-T43-1.

- **Range** (`t45_citecheck.py`): every `<Name>.java:<n>[-<m>]` in the document and in
  `contract.go` extracted, resolved against the pinned checkout (6,049 Java files indexed,
  main + `*Test.java`), and checked in range. **440 of 440 in range, 0 out of range, 0
  unresolvable, 0 ambiguous basenames.** 730 bare `:n` citations are counted and explicitly **not**
  machine-checked, because resolving them needs prose context — the count is reported so the
  claim is not overstated.
- **Content** (`t45_citecontent.py`): **69 assertions** that a cited line or range *contains* an
  expected token, covering every citation revision 9 touches plus the highest-value inherited ones.
  **69 of 69 pass.** This is the check that catches a P1-T43-1: `ACLSG:504` passes only because
  the assertion says it contains the *shared* separated-path line, which is what revision 9 now
  claims it is.

---

## 4. Spec check

**Step 0, and it is what an erratum owes before any replay is meaningful.** `t45_normdiff.py`
diffs every fenced normative block between revision 8 (`main`) and revision 9: **19 blocks in
revision 8, 0 removed, 0 altered, 4 added** (the `getCumulativeAmountOfCharge` extract, the two
cumulative-generator extracts, and C-1's four-term formula), and **§3.1 byte-identical**. So the
arithmetic text a from-text model reads is unchanged, and the committed revision-8 model is a
correct transcription of revision 9. **This is stated in the document and in this handoff rather
than presenting the replay as an independent re-transcription, which it is not.**

**Replay** (`t45_validate.py`, `t45_discriminate.py`, inherited model):

| leg | corpus | cells compared | result |
|---|---|---|---|
| A1 | 13 observation triples | 39 (level, final, total interest) | 13 of 13 |
| A2 | Path-A pass 3 (11) | 712 (`fromDate`, `dueDate`, `principal`, `interest`, `balance`, `total` per row; `loanTermInDays`, `totalInterestAmount`) | 11 of 11 |
| A3 | T37 binding (10) | 776 (same cells) | 10 of 10 |
| A4 | T39 parity-setting (15) | 1,224 (adds `fee`, `penalty`, `totalOutstandingBalance`, `totalDisbursedAmount`, `totalRepaymentAmount`, disbursement `dueDate` + `principal`) | 15 of 15 |
| A5 | T40 charge captures (21), schedule core | 1,827 (`fromDate`, `dueDate`, `principalOriginalDue`, `principalDue`, `interestDue`, `principalLoanBalanceOutstanding`, `totalInstallmentAmountForPeriod`; `loanTermInDays`, `totalPrincipalExpected`, `totalInterestCharged`) | 21 of 21 |
| | | **4,578** | **PASS, zero mismatches** |

**Discrimination**: all nine wrong readings replayed cell by cell. Every one is still separated by
at least one committed capture except the M1/M3 collapse, which is inert and named as
corpus-blind. `ratio-is-always-1` 12/21 + 15/15; textbook 2/21 + 1/15; `n = NumberOfRepayments`
2/21; whole-principal 3/21; loop-absent 6/21 + 8/15; no-adoption-test 1/21; `RepaymentEvery`
0/21 + 8/15; month-end-omitted 3/21 + 4/15.

**Three legs revision 8's probe never ran** (`t45_extra.py`, `t45-extra-output.txt`):

- **C1 — Path-A pass 3b**, all twelve, **872 cells**, including the disbursement row's `balance`
  and `principal` that pass 3 lacked. **11 of 11 reproduce** (`P-CAL` skipped: threaded precision 12).
- **C2 — Path B**, the four committed `B-0n` captures, **192 cells**. `B-01` reproduces exactly;
  `B-02` (`installmentAmountInMultiplesOf = 100`), `B-03` and `B-04` (`daysInYearCustomStrategy`)
  do not, which is the §4.4 / §4.7 **refusal being correct**, not the model being wrong. Recorded
  that way in the probe output so it is not misread.
- **C3 — T44's F39-1, re-derived inside DEC-1's own model.** Over **59,130** `(ScheduleStartDate,
  repayment period)` pairs (1,095 start dates 2023-01-01…2025-12-30 × terms {6, 12, 36},
  `RepaymentEvery` 1): special case fires on **701**, `packed ∧ ¬special` disagrees on exactly
  those **701**, `clamped-step ∧ ¬special` disagrees on **0**. **T44's figures reproduced digit
  for digit by independent code.**

**And a fourth leg on the only normative content revision 9 adds** (C4): M4 and M5 transcribed
from revision 9's text alone and replayed against the **set of repayment rows carrying a non-zero
`feeChargesDue` or `penaltyChargesDue`** on all 21 charge captures — the exact question M4 and M5
answer, and one that needs no charge *amount* to score.

- **revision 9's M4 + M5: 21 of 21.**
- **revision 8's "M4 decides which row a charge lands on": 13 of 21** — refuted by the six
  `INSTALMENT_FEE` captures (`FC-02`, `FC-04`, `FC-05`, `FC-08`, `FC-09`, `FC-15`), by `FC-22`,
  and by `FC-20`.

**P1-T43-3 is therefore not editorial: it is a reading the committed corpus refutes on eight
captures.**

---

## 5. What I deliberately did NOT change

- **§4.3.1's normative loop block, the `periodRatio` definition, §3.1, §4.2's re-anchor, §4.3.2
  steps 1–5, the interest pseudocode.** T43 verified ~70 citations and all of this clean. The
  normative-block diff above proves mechanically that none of it moved.
- **P2-T43-3's first-witness cells.** Re-derived and found correct as written; changing them would
  have churned five table rows to substitute one probe's arbitrary ordering for another's. The
  column is relabelled and the reason recorded instead.
- **§8 item 3f's binding.** T44's F39-1 narrows what the captures *grade*; it does not disqualify
  them, because §4.1.1 step B and §9 obligation (f) require the **pair** and the captures grade
  the pair. The binding stays at seven vectors and the item stays discharged-by-capture,
  pending promotion.
- **Decisions C-1 and C-2.** Both stand. Revision 9 reopens no decision.
- **Anything that would move a type, field, enum member or graded-domain predicate.** None was
  needed; nothing did.
- **`.softhouse/capture/**`, `reference-oracle.md`, `patterns.md`, `tasks.json`, `program.json`,
  `gates.md`.** Read-only or out of my write surface. T44's required changes to the *capture sets*
  (relabelling the T39 handoff, C5 as a probe, the request-bytes fixture) are **not mine** and are
  not done here.

---

## 6. New findings from this task

1. **The M4 table row understated the flag's path-dependence** (found by C4, not by T43). A model
   transcribed from the row alone mis-predicts `FC-20` — a charge the oracle silently loses. The
   fact was in the document, two paragraphs away and again in §4.5.1 C-2b, but not in the row a
   porter would transcribe. **Moved into the row.** Same shape as the T43 findings: right document,
   wrong place.
2. **A measurement trap in the F39-1 sweep, recorded in §4.1.1.** The sweep must build its
   boundaries with §4.2's **re-anchor**. On plain `plusMonths` boundaries the month-end special
   case fires **zero** times over the same 59,130 pairs and the sweep silently proves nothing.
   T45's first run did exactly that and reported `fires: 0`. Anyone re-running this measurement —
   including the sibling capture task — should check the fire count is non-zero before believing
   the result.
3. **T44's A-5 makes a revision-8 sentence false**, which the task brief did not list among the
   T44 items to fold in. Corrected; nothing rested on it.
4. **`AbstractCumulativeLoanScheduleGenerator.java:492-493`** uses the **two-argument**
   `Money.of(currency, …)` where the progressive generator's `:474-475` passes `mc`. That is an
   **ambient** read on the cumulative generator's separated path. Not in scope for DEC-1 (the
   cumulative generator is out of the contract's domain) and **not** added to the document, but it
   is worth knowing when the cumulative generator is ported. `[UNVERIFIED by observation]`

---

## 7. Gate items

**None.** No correction required a type, field set, enum member or graded-domain predicate to
move, so nothing hit the STOP condition in the brief. Revision 9 reopens no ratified decision and
takes no `user`-reserved decision.

---

## 8. Is revision 9 ratifiable?

**In my judgement yes, and for a reason revision 8 could not offer.**

T43 returned no P0 and found no reason not to ratify. The one thing standing between revision 8
and a freeze was **P1-T43-3 — a known-wrong sentence about money**. That sentence is now not only
corrected but **refuted by the committed corpus on 8 of 21 captures under revision 8's reading and
reproduced on 21 of 21 under revision 9's**, which is a stronger discharge than a re-derivation.
The other two P1s were citation defects; both are re-pinned, both machine-checked, and the second
had its *claim form* strengthened so it cannot fail the same way a third time.

Against that, three things a ratifier should weigh, all of them recorded in the document:

1. **T44's F39-1 narrows the evidence under §8 item 3f.** The seven witnesses grade the pair.
   §4.1.1 step B and §9 obligation (f) already require the pair, so the binding is honestly
   discharged — but a promoted record must carry the limitation as machine-readable data, and §8
   item 1 now requires it.
2. **The charge material is specification, not contract.** `GenerateRequest` carries no charge, so
   M4, M5, C-1 and C-2 bind a future port and nothing today. That is stated repeatedly and is what
   makes them safe to freeze.
3. **The cumulative generator is still unobserved.** C-1's premise is re-derived from source on
   both sides and observed on one. `[UNVERIFIED by observation]`, recorded in §8 item 9(d).

None of the three is a reason to keep the document unfrozen; each is a reason the document already
gives the reader.
