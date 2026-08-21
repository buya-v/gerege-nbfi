#!/usr/bin/env python3
"""T41 edit batch 14 — header, revision-history entry for revision 8, section 5 capture sets.

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

MEASURED BY T187 ON SCRATCH COPIES, NOT ASSERTED.  INERT TODAY.  Against byte-identical scratch copies of the CURRENT artefacts the
PRE-FIX bytes exited 1 at an anchor (`FAIL: expected 1, found 0 for:`)
and left both copies byte-identical.  An anchor that does not match today is not a
guarantee for tomorrow - the ADR is a living artefact and a later revision can
restore a phrase - so this file is hardened regardless of whether it applies now.

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
  DEC-1        BEFORE_SHA256 = d8c146642256bbe682ff97c5e3b7c952eaf9aa36df1a2d2fe831e607df089473
  DEC-1        AFTER_SHA256  = 1644db02cc3a311cb699b1eb3543e5c4525aa2942de22a8f58264642586385b0

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


NAME = 'edit14'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT14-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    'd8c146642256bbe682ff97c5e3b7c952eaf9aa36df1a2d2fe831e607df089473'
AFTER_SHA256 = \
    '1644db02cc3a311cb699b1eb3543e5c4525aa2942de22a8f58264642586385b0'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


sub(
    "**Status: DRAFT (revision 7) — awaiting independent re-review, then ratification**",
    "**Status: DRAFT (revision 8) — the RATIFICATION CANDIDATE; awaiting independent re-review, "
    "then ratification. Revision 8 was written by task T41, which may revise this unratified "
    "draft but may NOT ratify it.**",
)

sub(
    "| Run | `2026-08-17-run1-harness-schedule-poc`, task T4 (attempt 2); revision 3 by task T24; "
    "revision 4 by task T28; revision 5 by task T31; revision 6 by task T33; revision 7 by task "
    "T38 |",
    "| Run | `2026-08-17-run1-harness-schedule-poc`, task T4 (attempt 2); revision 3 by task T24; "
    "revision 4 by task T28; revision 5 by task T31; revision 6 by task T33; revision 7 by task "
    "T38; revision 8 by task T41 |",
)

sub(
    "| Supersedes | DEC-1 revision 1 (rejected by review T5); DEC-1 revision 2 "
    "(accepted-with-required-changes by re-review T23); DEC-1 revision 3 "
    "(accepted-with-required-changes by re-review T26); DEC-1 revision 4 "
    "(accepted-with-required-changes by re-review T29); DEC-1 revision 5 "
    "(accepted-with-required-changes by re-review T32); DEC-1 revision 6 "
    "(accepted-with-required-changes by re-review T34) |",
    "| Supersedes | DEC-1 revision 1 (rejected by review T5); DEC-1 revision 2 "
    "(accepted-with-required-changes by re-review T23); DEC-1 revision 3 "
    "(accepted-with-required-changes by re-review T26); DEC-1 revision 4 "
    "(accepted-with-required-changes by re-review T29); DEC-1 revision 5 "
    "(accepted-with-required-changes by re-review T32); DEC-1 revision 6 "
    "(accepted-with-required-changes by re-review T34); DEC-1 revision 7 (superseded by revision "
    "8 on the evidence of capture tasks T39 and T40, not by a review finding) |",
)

# --- revision-history entry for revision 8 ----------------------------------
sub(
    "**Revision history.**\n\n- **Revision 7 (task T38)**",

    r"""**Revision history.**

- **Revision 8 (task T41)** applies the findings of the two capture tasks that landed in the same fire as revision 7 — **T39** (`periodRatio`, `.softhouse/capture/periodratio/`) and **T40** (charges, `.softhouse/capture/charges/`) — and folds in one re-derivation of this task's own that explains T39's most awkward finding. **No oracle observation was taken by this task**; every observation cited is quoted from a committed capture with its id, and every `file:line` below was re-opened in the pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` by this task. **No type, field set, enum member or graded-domain predicate moves in this revision** — §3.1's block is byte-identical to revision 7's.
  **P0-T34-1 is settled by OBSERVATION (§4.1.1, §4.3.1, §4.3.2, §8 item 3e, §9).** Revision 7 corrected the multiplier from source and recorded, honestly, that the corpus could not grade the correction — the `RepaymentEvery` reading failed **0 of 21** captures. Task T39 captured 16 shapes and the answer is `periodRatio`: on the **415 cells where the two readings disagree**, across 8 drift shapes, the oracle agrees with `periodRatio` **415 of 415** and with `RepaymentEvery` **0 of 415**, and the `periodRatio` reading reproduces **all 1,239 cells of all 15 parity-setting captures** with zero mismatches. Revision 7's re-derived figures were right to the cent — the worst case, **MNT 398,967.73** of total interest on a MNT 50 M / 36 × 21.6 % loan, is now observed. Three of the subsection's re-derived properties became observations too: **no size threshold** (MNT 100 still separates on 27 cells), **not a January/leap-year/31-day artefact**, and **the DUE DATES move** (`loanTermInDays` 185, not 182) — which a three-scalar conformance check could never see.
  **§8 item 3e SPLITS into 3e and 3f, and the binding widens from six vectors to SEVEN (T39's N-2).** `periodRatio`'s **month-end special case** [`ProgressiveEMICalculator.java:1426-1436`, predicate at `:1432`] is live, load-bearing and now observed: omitting it roughly doubles `periodRatio` on alternate periods and overcharges by **MNT 83,959.76** on one six-month MNT 3.9 M loan, refuted **116 of 116** discriminating cells. It cannot share a vector with 3e, and the reason is **measured**: over 51,729 same-month pairs × 3 terms the special case fires on **210**, and on **0 of those 210** does `ScheduleStartDate ≠ Disbursement.Date` — the two questions are disjoint in shape space. §4.1.1 step B now states the predicate literally and §9 gains obligation (f).
  **N-1: the P0's framing is NARROWED, in this document's favour (§4.1.1, §4.3.2, §9).** Revision 7 said "two arguments differ" and scoped the days-in-month argument's inertness to the graded domain. Re-derived here in full, it is inert **unconditionally**: `daysInMonth` [`:1508`] is consumed at exactly one place [`:1537`], inside the `case DAYS_30 ->` arm [`:1536`] where `:1508`'s ternary yields `BigDecimal.valueOf(30)` — the same literal the interest call site passes [`:1413`] — and on the other two enum values neither call site is reached with that argument at all (`ACTUAL` takes `:1534-1535` and `:1400-1402`; `INVALID` throws at `:1538` and `:1415-1416`). **There is exactly one numeric difference between the two call sites and it is the multiplier**, and a revision that also "corrected" the second argument would be wrong. Revision 8 also records one divergence from T39, which locates the assignment at `:1509` in prose while its own `[VERIFIED]` tag says `:1508`; **`:1508` is correct.**
  **P1-T39-1 — the finding that COSTS this document something (new §4.1.2, §4.1, §5, §8 items 1 and 2, §9).** T39 forced the tenant `RoundingMode` to `DOWN`, changed `MoneyHelper.getMathContext()` on the oracle's own testimony, and left **all 16 observed blocks byte-identical**; forcing the **threaded** mode moved **15 of 16**. So the SLF4J initialisation line and the echoed `MoneyHelper.getMathContext()` — which T37's attestation calls "the `MathContext` actually in force" — witness the **tenant configuration**, not the arithmetic. Every §4.1 sentence resting on the ambient reading is re-scoped, and new **§4.1.2** states the rule normatively, states what the ambient reading **is** still evidence of (tenant configuration; that the run would not throw; the arithmetic on **Path B**, where nothing threads a context; and `PRECISION` as a property of the deployed binary), and states it **falsifiably** so a sibling task can confirm or refute it. **This task also re-derived the mechanism T39 could not:** `Money` holds its own `MathContext` [`Money.java:32`] assigned at [`:42`], and `getMc()` is an **instance** method returning that field when non-null and `MoneyHelper.getMathContext()` only when null [`Money.java:494-496`] — so the constructor's currency-scale `setScale` at [`:52`] reads the **threaded** mode whenever one was threaded. Revision 7 cited `:52` as a tenant-global source; that was the imprecision, and the source now predicts T39's 0-of-16 / 15-of-16 split exactly.
  **T40 — the first charge observations in this program (new §4.5.1, §4.3.2 M4, §4.5, §6.1, §8 items 1 and 9, §9).** Twenty-one non-zero-charge schedules on the running-server path at attested `MathContext(19, HALF_UP)`, behind a zero-charge control that reproduced the four committed Path-B digests byte for byte. **Observed:** charges sit **alongside** the EMI and never inside it — principal split, interest, outstanding principal and level installment are cell-for-cell identical to the control on **all 21** — which upgrades §4.5's and §6.1's "purely additive" argument from re-derivation to observation. **Two decisions, both taken here rather than raised as gates, per CLAUDE.md §Answering gates. C-1: `totalRepaymentExpected` is NOT carried.** It omits every charge applied in the main loop [`ProgressiveLoanScheduleGenerator.java:367-382` never calls `addTotalRepaymentExpected`] while the cumulative generator adds them [`AbstractCumulativeLoanScheduleGenerator.java:504`] — **the two generators disagree**, `total == Σ row totals` fails on **15 of 21** observed captures, and on one capture MNT 51,900 of charges is visible in the rows and absent from the total. It is derivable inside today's graded domain, has no single meaning to specify, and is exactly the silent meaning-change §6.1 was shaped to avoid; the adapter must **discard** it and no invariant may assert it equals the row sum. Which generator the contract would have meant, stated rather than dodged: **the progressive one**. **C-2: a silently-dropped charge is REFUSED, never reproduced.** Two paths return HTTP 200 and a response byte-identical to the zero-charge control — a charge dated after the final due date (one-sided guard, [`LoanChargeValidator.java:59-67`]) and a percent-of-interest specified-due-date charge on the disbursement date (stale `isFirstPeriod()`, [`LoanScheduleParams.java:533-535`] versus [`ProgressiveLoanScheduleGenerator.java:143`]) — while an identical **flat** charge on that same date pays 9,000.00. Refusal follows §3.1's own precedent for a silently discarded **disbursement**; §4.6's "reproduce rather than refuse" argument does not reach it, because the oracle's answer provably carries no information about the input.
  **A FOURTH date-membership rule, M4 (§4.3.2, §9).** The specified-due-date membership rule is `[from, due]` for period 1 and `(from, due]` thereafter, observed and pinned by three byte-identical response groups. It shares **M1's predicate function** [`LoanRepaymentScheduleProcessingWrapper.java:251-254`] and is still a **different rule**, because M1 takes its "is first" input from the period's own `isFirstRepaymentPeriod()` [`ProgressiveLoanInterestScheduleModel.java:243`, `RepaymentPeriod.java:449-451`] while M4 takes it from the **mutable counter** `LoanScheduleParams.isFirstPeriod()` — correct inside the main loop, **stale on the separated path**, which is the whole of C-2b. All four are now stated in the one place §4.3.2 reconciles them, with which rule governs which field.
  **What revision 8 does NOT do.** It does not admit charges to the contract, does not add a charge field or predicate, does not promote any capture to the vector store, and does not ratify itself. The binding is now **one promotion decision away from dischargeable**: all seven of its shapes are captured and all seven separate, and what is missing is item 1's promotion, which is gated on this document.

- **Revision 7 (task T38)**""",
)

# --- section 5: three capture sets -> five ----------------------------------
sub(
    "**Three captures sets exist, and a ratifier should not confuse them.** (a) The twelve Path-A "
    "pass-3 captures and their pass-3b re-emission — the corpus §5 tabulates. (b) The four Path-B "
    "server-path captures, plus T36's nine EMI-loop probes. (c) The eleven **T37 binding "
    "captures** (`.softhouse/capture/dec1-binding/`), taken this same fire specifically to settle "
    "§8 items 3, 3a, 3b, 3c and 3d, of which ten are at `(19, HALF_UP)`. Revision 7's from-text "
    "model reproduces (a) and (c) **cell by cell** (§4.3.1). None of the three is a parity vector.",

    "**FIVE capture sets now exist, and a ratifier should not confuse them.** (a) The twelve "
    "Path-A pass-3 captures and their pass-3b re-emission — the corpus §5 tabulates. (b) The four "
    "Path-B server-path captures, plus T36's nine EMI-loop probes. (c) The eleven **T37 binding "
    "captures** (`.softhouse/capture/dec1-binding/`), taken to settle §8 items 3, 3a, 3b, 3c and "
    "3d, of which ten are at `(19, HALF_UP)`. (d) **Revision 8 adds** the sixteen **T39 "
    "`periodRatio` captures** (`.softhouse/capture/periodratio/`), of which fifteen are "
    "parity-setting and one is a labelled `(12, HALF_UP)` calibration, taken to settle §8 items "
    "3e and 3f. (e) And the twenty-one **T40 charge captures** "
    "(`.softhouse/capture/charges/`), Path B, which grade the oracle's charge behaviour and the "
    "decisions in §4.5.1 rather than any field of this contract — DEC-1 carries no charge. "
    "Revision 7's from-text model reproduces (a) and (c) **cell by cell** (§4.3.1) and revision "
    "8's extends that to (d) and the schedule core of (e). **None of the five is a parity "
    "vector**, and item 1's promotion step applies to all of them equally.",
)

guard.commit(s)
print("\n".join(LOG))
