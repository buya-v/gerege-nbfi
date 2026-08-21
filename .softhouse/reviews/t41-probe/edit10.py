#!/usr/bin/env python3
"""T41 edit batch 10 — insert section 4.5.1, the charges subsection (T40).

HARDENED BY T187 (21 August 2026) - P-22, P-48 rule 4.  This file REUSES T178's
shared guard verbatim (`../t47-probe/t178_guard.py`, itself T167's shape).  It
introduces no third guard shape and contains no copy of the guard.

AS SHIPPED BY TASK T41 this file ended in

    io.open(<a hard-wired repo-relative path>, "w", encoding="utf-8").write(s)

with no authorisation, no content gate, no atomicity and no trap.  `io.open(p,
"w")` opens with O_TRUNC, so the target was EMPTIED before a single byte of
replacement text was written, and any interruption from that instant until the
last flush left it truncated or half-edited.  Its target was the RATIFIED DEC-1.
Amending a ratified DEC-n, or the frozen adapter contract that gate G-3 forbids
even `gofmt -w` from touching, is a hard `user` gate under CLAUDE.md.  An unguarded
rewriter aimed at either is a GATE BYPASS whether or not anybody runs it.

MEASURED BY T187 ON SCRATCH COPIES, NOT ASSERTED.  THIS SCRIPT IS A LIVE GATE BYPASS.  With cwd set to a scratch tree holding a
byte-identical copy of the CURRENT ratified DEC-1 (sha256
49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab)
the PRE-FIX bytes exited 0, printed `inserted 4.5.1`, and moved that copy to
sha256 905dbcaeca44fb2d5d93f4ef1fec90f830808e90effee3c03c0654fa076d2c5c.
Its ONLY precondition was an anchor count of 1; it took no argv; so `python3 edit10.py`
from the repository root would have amended a RATIFIED DEC-n in place, silently.
The mutation was performed on a SCRATCH COPY only - the repository artefacts were
re-hashed before and after and did not move.

THE EDIT ITSELF DID NOT CHANGE.  Every anchor and every replacement string
below is byte-for-byte T41's.  What changed is the head and the tail: the
hard-wired target and the unguarded read are gone (the target now arrives from
argv under default-deny authorisation, and there is deliberately NO override
that reaches a ratified or frozen artefact); the write is atomic (`mkstemp` in
the target's own directory, `st_dev` compared, `fsync`, `os.replace`) and is
gated on sha256 BOTH on the target read and on the candidate text.  There is no
bare `assert` anywhere - `python3 -O` strips those - and every refusal is an
explicit exit.

PINNED CONTENT GATE, AND THIS IS WHAT ACTUALLY CLOSES THE BYPASS.
  DEC-1        BEFORE_SHA256 = 4e682455ed4e712f86f3c156db7a4af1891364dde47c58dd4060e649d11c1b7a
  DEC-1        AFTER_SHA256  = 3da914cebede41a41fa095a1d0c49c4fdddc4ac844c988cfd2e820ca93b6a15a

HOW THE PINNED PAIR WAS DERIVED, RE-MEASURABLE BY ANYONE.  BEFORE_SHA256 is the
target's state at THIS script's position in T41's own edit chain, obtained by
replaying every T41 rewriter in commit order on scratch copies seeded from
  ADR          `git show 3594820^:docs/adr/DEC-1-schedule-generator-adapter.md`
               (sha256 35e513cdec69913caed759daee92626f2248c5c6fe2ca9ead6ed9968dc5f78e2)
  contract.go  `git show e96541d^:nexus/internal/apps/loanschedule/contract/contract.go`
               (sha256 c7cb53819bf0dea5c0327d3b4dc997a6f1feb14137e1c551059185bad0721a82)
AFTER_SHA256 is this script's DETERMINISTIC OUTPUT on that exact input, measured
by T187 - not a committed blob, because T41's commits carried hand edits
alongside the scripts' output.  The replayed chain is nevertheless faithful to
history where it can be checked: it reproduces the COMMITTED contract.go blobs
at b299ade (0e5468c470...) and at 0881cc0^ (4f986bb157...) exactly.

The ratified DEC-1 on `main` is sha256
  49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab
and the frozen contract.go is
  0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139
NEITHER is any BEFORE_SHA256 above, so no run of this file can reach either
artefact's CURRENT contents even if every other guard were stripped.

Guard, exit codes and the argv-token rationale: `../t47-probe/t178_guard.py`.
  0 ok / dry-run ok
  1 anchor mismatch (the edit does not apply)
  2 refused - authorisation, or target policy
  3 refused - unexpected target content (target sha != BEFORE_SHA256)
  4 refused - candidate content is not the historical result
  5 refused - temp file not on the target's filesystem
  6 post-write verification failed
"""
import os
import sys

# T178's guard is the ONE guard this program has, and it lives beside the
# t47-probe scripts.  It is resolved from THIS FILE's own location - never from
# the cwd, never from PYTHONPATH - so it cannot be shadowed.  A missing or
# unimportable guard raises ImportError and this script exits non-zero having
# written nothing: it fails CLOSED.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "t47-probe"))
import t178_guard as guard  # noqa: E402


NAME = 'edit10'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT10-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '4e682455ed4e712f86f3c156db7a4af1891364dde47c58dd4060e649d11c1b7a'
AFTER_SHA256 = \
    '3da914cebede41a41fa095a1d0c49c4fdddc4ac844c988cfd2e820ca93b6a15a'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

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
guard.commit(s)
print("inserted 4.5.1")
