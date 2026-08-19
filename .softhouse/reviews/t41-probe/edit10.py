#!/usr/bin/env python3
"""T41 edit batch 10 — insert section 4.5.1, the charges subsection (T40)."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()

ANCHOR = "### 4.6 Ordering: reproduce the oracle's emitted order"
if s.count(ANCHOR) != 1:
    sys.exit("anchor count %d" % s.count(ANCHOR))

NEW = r"""#### 4.5.1 Charges — the corpus's oldest blind spot, closed by observation, and the two decisions it forces (added in revision 8)

Every revision through 7 recorded the same fact: **every fee and every penalty in the entire
committed corpus is `0.00`**, so a port could have got charge handling arbitrarily wrong and
passed 100 % of it. Task T40 removed that blindness for the progressive `calculateLoanSchedule`
endpoint — **21 accepted captures plus one recorded refusal, on the running server (Path B), on
the `gerege` tenant at attested `MathContext(19, HALF_UP)`**, behind T36's preconditions script
re-run before every create and every capture (21 of 21 assertions PASS, five times) and behind a
**zero-charge control re-emitted input-for-input**: the four committed Path-B requests came back
with the four digests T36 attested, byte for byte [VERIFIED: `.softhouse/capture/charges/`,
`out/control/`, `out/attested/attestation.json`, `out/preconditions-T40.txt`]. The harness is
therefore not a variable, and every difference below is caused by the charge.

**Comparison shape, stated because it is load-bearing:** each response is flattened to **286
leaves** and every leaf compared against the control as an exact `Decimal` in integer minor units,
**zero tolerance**, distinguishing a moved number from a structural difference
[`.softhouse/capture/charges/bin/fullcell.py`, `out/FULLCELL.md`]. The three headline scalars —
level installment, final installment, total interest — are **identical to the control on all 21
captures**, so a three-scalar check would have seen none of this.

##### What was observed (five facts, none of them derivable from anything already in this document)

1. **Charges sit ALONGSIDE the EMI, never inside it.** `totalInstallmentAmountForPeriod` is
   `112,082.37` on periods 1–11 and `112,082.40` on period 12 on **all 21 captures** —
   cell-for-cell identical to the zero-charge control (invariant C9, PASS 21/21). What moves is
   `totalDueForPeriod`: on `FC-02` (flat MNT 2,500 per instalment) it is `114,582.37` and
   `114,582.40`. *Mechanism:* the EMI is fixed first —
   `emiCalculator.findRepaymentPeriod(...)` sets principal and interest
   [`ProgressiveLoanScheduleGenerator.java:125-138`] — and only then does
   `applyChargesForCurrentPeriod` add the charge [`:140`].
2. **Charges do not touch the money core.** `principalDue`, `principalOriginalDue`, `interestDue`
   and `principalLoanBalanceOutstanding` are cell-for-cell identical to the control on **all 21**
   (invariant C8, PASS 21/21) — including `FC-15`, which carries MNT 66,900 of fees and
   penalties. `Σ principalDue == totalPrincipalExpected` exactly on all 21 (C6): **principal still
   amortizes to zero in the presence of charges.**
3. **The fee and penalty columns are genuinely separate and additive within a period.** On
   `FC-15`, period 3 carries fee `2,500.00` and penalty `8,700.00` = `1,200 + 7,500`; the two
   kinds never mix columns, and `Σ feeChargesDue == totalFeeChargesCharged` exactly on all 21
   (C1, C2).
4. **The rounding locus is observable and differs between two charges describing the same
   thing.** "3.75 % of interest" totals **5,437.06** as a per-instalment charge (twelve roundings
   summed) and **5,437.07** as a specified-due-date charge (one rounding of the whole-term
   interest); 1.2345 % of amount-plus-interest gives **16,603.92** against **16,603.88**, four
   minor units apart. C1 passing is what pins it: the total is the **sum of the rounded parts**,
   never a re-rounded whole.
5. **Two silent charge-loss paths, both HTTP 200 and both byte-identical to the zero-charge
   control** — the loudest result T40 produced, and the subject of decision **C-2** below.

[VERIFIED throughout: `.softhouse/capture/charges/out/FULLCELL.md`, `out/FEECOLS.md`,
`out/INVARIANTS.md`, `out/DETERMINISM.txt`; every response issued three times and byte-identical
across all three issues.]

**Consequence for §4.5's response shape, and it is a confirmation rather than a change.** §4.5
carries no per-row fee or penalty and no level-installment field, and argued that charges would
therefore be **purely additive** when they arrive. Fact 1 is that argument's first empirical
support: the quantities this contract carries — `PrincipalMinor`, `InterestMinor`,
`OutstandingPrincipalMinor` — **do not move when a charge is applied**, so admitting charges later
changes no existing field's meaning. §6.1's forward-compatibility claim is upgraded from
re-derivation to observation accordingly.

##### Decision C-1 — `totalRepaymentExpected` is NOT carried, and revision 8 says which generator it would have meant

**The finding.** `totalRepaymentExpected` is **internally inconsistent with the periods it
summarises**. A charge applied in the main schedule loop — every instalment fee, every flat or
percent-of-amount specified-due-date charge, every penalty — raises `feeChargesDue` /
`penaltyChargesDue` and `totalDueForPeriod` on its period and raises `totalFeeChargesCharged` /
`totalPenaltyChargesCharged`, **but is not added to `totalRepaymentExpected`**. Invariant
`totalRepaymentExpected == Σ totalDueForPeriod` **FAILS on 15 of 21 captures**
[VERIFIED: `.softhouse/capture/charges/out/INVARIANTS.md`, C5]. `FC-15` is the sharpest: MNT
**66,900** of fees and penalties are shown as due across the rows and only the MNT 15,000
disbursement fee reaches the total — **MNT 51,900 visible in the rows and absent from the sum.**

**Mechanism, re-derived by this task from the pinned checkout, not read back from T40.**
`applyChargesForCurrentPeriod`'s body is exactly `addLoanCharges`, `addTotalFeeChargesCharged`,
`addTotalPenaltyChargesCharged` and nothing else [VERIFIED:
`ProgressiveLoanScheduleGenerator.java:367-382` — re-opened and read in full; there is no
`addTotalRepaymentExpected` call in it]. The running total is seeded with the disbursement charges
only — `final Money totalRepaymentExpected = chargesDueAtTimeOfDisbursement` [VERIFIED:
`LoanScheduleParams.java:211`, and identically at `:246`] — and thereafter accumulates
principal + interest per period [`ProgressiveLoanScheduleGenerator.java:137`]. The **only** charge
contribution after the seed comes from `updatePeriodsWithCharges` [`:486`], which serves just the
two *separated* calculation types. **The cumulative generator does the opposite:** it adds fee and
penalty to the running total on every period [VERIFIED:
`AbstractCumulativeLoanScheduleGenerator.java:504`]. **The two generators disagree**, so the field
does not have one meaning in Fineract at all.

**The decision (ENGINEERING/PRODUCT, `chosen_by: agent`, per CLAUDE.md §Answering gates — decided
here, not raised as a gate): the contract does NOT carry `totalRepaymentExpected`.** Four reasons,
in the order that decides it:

1. **§3.3 rule 4.** Inside the graded domain the contract carries **no charge input at all**, so
   `chargesDueAtTimeOfDisbursement` is zero and no separated charge exists; the oracle's field
   reduces to `Σ (principal + interest)` over the repayment rows, which is exactly the sum of
   `PrincipalMinor + InterestMinor`. It is **derivable**, and §4.5's standing rule excludes
   derivable aggregates.
2. **It has no single meaning to specify.** Carrying it would require choosing between two
   Fineract behaviours, and a vector would then pin whichever generator produced it. A field whose
   value depends on which implementation answered is the *opposite* of what a parity boundary is
   for.
3. **It is the silent-meaning-change §6.1 was shaped to avoid.** Today it equals the row sum;
   the moment charges are admitted it stops equalling it, **without any type changing and without
   any compile breaking**. §4.5 rejected a total-due column for precisely this reason, and this is
   the same hazard with the same shape.
4. **The `totalOutstandingAmount` precedent.** Revision 7 declined to carry a plan member that
   was structurally uninformative. This one is worse: it is informative-looking and *wrong*.

**Which generator's semantics the contract specifies, since the question must be answered rather
than dodged: the PROGRESSIVE one, unconditionally** — as every `file:line` in this document
already is. So **if** a later amendment ever carries this field, it carries the progressive
reading (`disbursement charges + Σ(principal + interest) + separated specified-due-date percentage
charges`), it says so on the field, and it is captured against the progressive generator. Revision
8 does not carry it.

**The alternative rejected, and why.** *Carry `TotalRepaymentExpectedMinor` on `Schedule` and
specify it as the progressive generator's value.* Rejected: it adds contract surface (a field, a
gate to change later, a vector-set invalidation) to express a quantity that is derivable today,
disputed between two generators, and destined to disagree with its own rows tomorrow. The
cheaper and more honest instrument is the obligation below.

**Obligations that follow (§9).** (a) The **Fineract-JVM adapter must DISCARD**
`totalRepaymentExpected`, exactly as it discards `totalOutstandingAmount` (§4.5). (b) It must
**never** be used as a cross-check invariant against the rows: an adapter or harness asserting
`totalRepaymentExpected == Σ row totals` will pass today and fail the day a charge exists, and
that assertion would be **wrong about the oracle, not about the port** — C5 fails on 15 of 21
observed captures. (c) A caller wanting a total repayable **sums the rows**, which §4.5 already
requires of every other aggregate.

##### Decision C-2 — a silently-dropped charge is REFUSED, never reproduced

**The finding: two paths on which the oracle accepts a charge with HTTP 200 and returns a schedule
byte-identical to the schedule with no charge at all.** Both are money-losing in the borrower's
favour and invisible to the API caller.

- **C-2a, off the end.** `FC-17` — a MNT 9,000 fee dated `01 March 2027`, two months past the
  final due date — returns the **control's own response digest** `713a3560…c062009`, with
  `totalFeeChargesCharged` `0.00`; 0 of 286 leaves moved. *Mechanism:* the only date guard is
  **one-sided** — it rejects a specified-due-date charge dated **before** the disbursement date
  and has no upper bound at all [VERIFIED: `LoanChargeValidator.java:59-67`, predicate at `:61`].
  The *before* case does throw, and T40 recorded it as a refusal rather than a capture: HTTP 403
  `error.msg.loanCharge.cannot.be.added.as.specified.due.date.outside.range` (`XR-01`).
- **C-2b, the first period on the separated path.** `FC-20` — 3.75 % of interest,
  `SPECIFIED_DUE_DATE`, due `01 January 2026`, the disbursement date — returns the **same control
  digest**, while `FC-11` (a **flat** charge, same due date, same everything else) returns
  `9,000.00` in period 1. **Two charges, one date, one paid and one lost, decided solely by
  calculation type.** *Mechanism:* `separateTotalCompoundingPercentageCharges` removes
  PERCENT_OF_INTEREST and PERCENT_OF_AMOUNT_AND_INTEREST specified-due-date charges from the main
  loop [VERIFIED: `ProgressiveLoanScheduleGenerator.java:492-504`], and
  `updatePeriodsWithCharges` applies them at [`:154`], **after** the loop at [`:116-145`], passing
  `scheduleParams.isFirstPeriod()` [`:479`, `:483`] — which by then is **false for every period**
  because `incrementInstalmentNumber()` has run once per period [`:143`, definition at
  `LoanScheduleParams.java:533-535`]. This is **M4's staleness** (§4.3.2): the inclusive lower
  bound that saves `FC-11` never applies, so a charge dated on the first period's `FromDate` falls
  outside `(FromDate, DueDate]` and is lost. `FC-19` — the same charge dated mid-period-6 — lands
  correctly, which isolates the fault to the first period's lower boundary rather than to the
  whole separated path.

**The decision (ENGINEERING, `chosen_by: agent`): the contract REFUSES a request whose charge the
oracle would silently drop. It does not reproduce the drop.** Stated now, before any charge field
exists, so it cannot be settled later by coincidence.

**Why refuse, given that §4.6 decided the opposite question the opposite way.** §4.6 chose to
*reproduce* the oracle's emitted order rather than refuse an input the oracle accepts, because
Fineract is the shadow-parity partner and a boundary that refuses what the oracle answers cannot
be run against the same traffic. **That argument turns on the oracle's answer carrying information
about the input.** Here it provably does not: the response is *byte-identical* to the response for
a request with no charge, so there is nothing to shadow-compare and no cell in which the two
implementations could be seen to agree or disagree about the charge. **This document has already
drawn exactly that line once, in exactly that situation:** §3.1 and §4.6 place a disbursement dated
before `ScheduleStartDate` or on/after the last due date **outside the graded domain and refuse it
with `ErrNoDiscriminatingVector`**, precisely because the seam silently discards it into an
all-zero schedule. A silently discarded **charge** is the same failure mode — HTTP 200, no error,
output indistinguishable from the input never having been given — and gets the same disposition.
Two further reasons, each sufficient on its own: a schedule that omits a fee the caller asked to
charge is a **money-losing silent wrong answer**, which is the single failure this contract exists
to prevent; and a borrower charged a fee that never appears on the schedule is a regulatory
exposure, not merely an engineering one.

**The alternative rejected.** *Reproduce the drop, so the Go module is bug-for-bug identical to
Fineract.* Rejected on the grounds above, and on one more: bug-for-bug parity is only meaningful
where a vector can witness it, and **no vector can witness this one** — the observation and the
control are the same bytes. Reproducing a behaviour no corpus can distinguish from its absence is
indistinguishable, forever, from not implementing it.

**Scope of C-2, stated exactly, because it must not be read as a widening.** `GenerateRequest`
carries **no charge field**, so neither shape is expressible in the contract domain today; C-2 is a
**forward disposition binding on whatever admits charges**, not a predicate added to §3.1. When
charges are admitted, the refusal takes `ErrNoDiscriminatingVector` by direct analogy with §3.1's
disbursement window — the request is well formed and computable, the oracle simply returns nothing
that grades it — subject to §4.11's precedence. **No type, field, enum member or graded-domain
predicate moves in revision 8 on account of charges**; see the end of this subsection.

##### What the charge corpus still CANNOT grade

Recorded here, in the same place §4.5 and §8 item 1 record the corpus's other blind spots, because
**coverage is what a corpus can distinguish and never what it contains**:

- **`chargeTimeType = OVERDUE_INSTALLMENT` (9) — the classic penalty — is entirely ungraded**, and
  it is the **most operationally important** penalty type. It is applied by the COB
  `Apply penalty to overdue loans` job against a *persisted, overdue* loan;
  `calculateLoanSchedule` persists nothing (`m_loan` count 0 after T40's whole run). Capturing it
  needs an approved and disbursed loan plus a business-date advance. `TO_BE_CAPTURED`.
- **Tranche charges** — `TRANCHE_DISBURSEMENT` (12) and `PERCENT_OF_DISBURSEMENT_AMOUNT` (5) — need
  `multiDisburseLoan = true`, which changes the schedule shape itself and would confound the
  controlled comparison. `TO_BE_CAPTURED`, in its own task.
- **`minCap` / `maxCap`** — a rounding-and-clamping surface and the most plausible remaining defect
  home — plus `taxGroupId`, `glAccountId`, `chargePaymentMode = ACCOUNT_TRANSFER`, `feeFrequency`
  and `feeInterval`: all unexercised. `TO_BE_CAPTURED`.
- **The cumulative generator.** Every T40 capture is `loanScheduleType = PROGRESSIVE`. Decision
  C-1 rests on the two generators disagreeing, and only the progressive side is observed; the
  cumulative side is **re-derived from source** [`AbstractCumulativeLoanScheduleGenerator.java:504`]
  and `[UNVERIFIED by observation]`.
- **Waiver, payment and the `getDueAmounts` path**, and everything about a charge on a *persisted
  and paid* loan. `feeChargesOutstanding == feeChargesDue` (C4) holds only because nothing has been
  paid.
- **A charge whose percentage lands on an exact half-cent tie**, which would pin the rounding mode
  *inside the charge arithmetic specifically*. T40 proved none exists against period 1's interest
  and did not search further. `TO_BE_CAPTURED`.
- **Path A cannot grade charges at all.** The embeddable seam's request record carries no charges,
  so every charge observation in this program is a **Path-B** observation. §4.5's statement that
  *the Path-A corpus* has zero discriminating power over charges is **unchanged and still true**.

##### Nothing in this subsection moves the contract's shape

**Checked deliberately, because admitting charges would be an amendment and this document is
unratified rather than amendable.** Revision 8 adds **no** type, **no** field, **no** enum member
and **no** graded-domain predicate on account of charges. `GenerateRequest` still carries no
charge; `Period` still carries no fee or penalty; §3.1's block is byte-identical to revision 7's.
What revision 8 adds is **specification and disposition**: M4 in §4.3.2's reconciliation, decisions
C-1 and C-2 above, the obligations in §9, and the blind spots in §8. **Were charges to be
admitted, that would be a contract widening and a gate** — §6.1 already names the likely resolution
as a composing context rather than an amendment to `Period`, and revision 8 does not foreclose or
prejudge it.

"""

s = s.replace(ANCHOR, NEW + ANCHOR)
io.open(P, "w", encoding="utf-8").write(s)
print("inserted 4.5.1")
