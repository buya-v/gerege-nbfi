#!/usr/bin/env python3
"""T41 edit batch 8 — section 8 items 3e/3f and the binding; section 5; section 6.

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
  DEC-1        BEFORE_SHA256 = 61b4d2e32c43e9e9ab2e2381606e1b617185ae6421655b8c02e50dae236ffa99
  DEC-1        AFTER_SHA256  = 3e475f1f313cee01e165a8783da54e658602ef49897dfeb5308e99fecd719bb2

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


NAME = 'edit8'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT8-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '61b4d2e32c43e9e9ab2e2381606e1b617185ae6421655b8c02e50dae236ffa99'
AFTER_SHA256 = \
    '3e475f1f313cee01e165a8783da54e658602ef49897dfeb5308e99fecd719bb2'

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


# --- section 8 item 3e -------------------------------------------------------
sub(
    "**3e. A vector whose SCHEDULE START and DISBURSEMENT DATE sit on different month-end "
    "anchors** — **added in revision 7** on re-review T34's P0-T34-1. It separates §4.1.1's "
    "**`periodRatio`** from the `RepaymentEvery` that revisions 1–6 wrote, and it is the **only "
    "one of the six with no capture at all**. The shape wanted:",

    "**3e. A vector whose SCHEDULE START and DISBURSEMENT DATE sit on different month-end "
    "anchors** — **added in revision 7** on re-review T34's P0-T34-1. It separates §4.1.1's "
    "**`periodRatio`** from the `RepaymentEvery` that revisions 1–6 wrote. **STATUS, revision 8: "
    "CAPTURED, NOT YET PROMOTED.** Task T39 captured **eight** shapes in the drift region — "
    "`T39-P0-A` (MNT 1,200,000 / 6 × 21.6 %, start `2024-01-28`, disbursement `2024-01-31` — the "
    "exact candidate this item named), `T39-P0-B`, `T39-P0-C`, `T39-P0-D`, `T39-P0-E`, "
    "`T39-P0-F`, `T39-P0-G`, `T39-P0-H` — plus three in-graded-domain controls **outside** the "
    "drift region on which all readings agree, which is what attributes the separation to the "
    "multiplier and not to the rig. Across the **415 cells where the two readings disagree** the "
    "oracle agrees with `periodRatio` on **415 of 415** and with `RepaymentEvery` on **0 of 415**, "
    "and the `periodRatio` reading reproduces **all 1,239 cells of all 15 parity-setting "
    "captures** with zero mismatches [VERIFIED: `.softhouse/capture/periodratio/`, attestation "
    "`ATTESTATION.md`, recipe `REPRODUCE.md`, analysis `analysis/discriminate-output.txt`]. "
    "**P0-T34-1 is settled empirically**, and revision 7's re-derived figures were right to the "
    "cent — this item's own candidate returned observed total interest **76,984.00** against the "
    "`RepaymentEvery` reading's **74,607.33**, and the larger sibling MNT 50,000,000 / 36 × "
    "21.6 % returned **18,659,151.45** against **18,260,183.72**, the **MNT 398,967.73** gap. "
    "These are **attested raw observations**; the promotion step is item 1. The shape wanted:",
)

sub(
    "**The region is small but ordinary** — 0.95 % of admissible same-month `(start, "
    "disbursement)` pairs, every one with a start day of 28/29/30, and month-end anchoring is "
    "routine in retail lending. **This item is the reason gate G-1 does not close on revision 7's "
    "evidence alone.** (Source: `.softhouse/reviews/T34-DEC-1-v6-rereview.md` §1, probes "
    "`.softhouse/reviews/t34-probe/` and `.softhouse/reviews/t38-probe/`. Every figure here is a "
    "re-derivation and none may be promoted to the vector store.)",

    "**The region is small but ordinary** — 0.95 % of admissible same-month `(start, "
    "disbursement)` pairs, every one with a start day of 28/29/30, and month-end anchoring is "
    "routine in retail lending. **Revision 7 said this item was the reason gate G-1 did not close "
    "on revision 7's evidence alone. That reason is now discharged as evidence and survives only "
    "as promotion**: the captures exist and they separate; what is missing is the item-1 "
    "promotion, which is what the binding actually requires. **Three of this item's re-derived "
    "claims became observations in revision 8**: there is no size threshold (MNT **100** still "
    "separates on 27 cells, observed `6.41` against `6.21` — capture `T39-P0-F`); the drift is "
    "not a January, leap-year or 31-day-month artefact (captures `T39-P0-G` March, `T39-P0-H` a "
    "30-day November, `T39-P0-E` the common year 2025); and the **due dates move too**, "
    "`loanTermInDays` **185** rather than 182 on `T39-P0-A`, which a three-scalar conformance "
    "check could never see (T39's N-5, N-6, N-7). (Sources: "
    "`.softhouse/reviews/T34-DEC-1-v6-rereview.md` §1, probes `.softhouse/reviews/t34-probe/` and "
    "`.softhouse/reviews/t38-probe/` — **re-derivations**; and "
    "`.softhouse/capture/periodratio/` — **observations**, quoted by capture id. The re-derived "
    "sweep counts remain re-derivations and none may be promoted to the vector store.)\n"
    "   **3f. A vector on the SAME month-end anchor whose repayment `FromDate` is a month's last "
    "day** — **split out of 3e in revision 8** on task T39's finding N-2. It separates §4.1.1 "
    "step B's **month-end special case** [`ProgressiveEMICalculator.java:1426-1436`, predicate at "
    "`:1432`] from the same routine with those four lines omitted — the most plausible mis-port "
    "of `calculatePeriodRatio`. **STATUS: CAPTURED, NOT YET PROMOTED.** Captures `T39-ME-A` (MNT "
    "3,924,149 / 6 × 16.8 %, start = disbursement `2024-01-31`), `T39-ME-B` (MNT 1,200,000 / "
    "6 × 21.6 %, same dates), `T39-ME-C` (the same in the **common** year 2023, identical to the "
    "cent) and `T39-ME-D` (seed day 30). Omitting the case makes `periodRatio` `[1,2,1,2,1,2]` "
    "where the oracle's is `[1,1,1,1,1,1]` — a **double month** on alternate periods, worth "
    "**MNT 83,959.76** on `T39-ME-A` and **MNT 33,177.27** on `T39-ME-B`. Across 4 shapes and "
    "**116 disagreeing cells** the oracle agrees **116 of 116** with the special case present and "
    "**0 of 116** with it omitted [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`].\n"
    "   **Why this is a SEPARATE item and not a second reading of 3e** — the reason is measured, "
    "not stylistic. The two questions are **disjoint in shape space**: over 51,729 same-month "
    "`(ScheduleStartDate ≤ Disbursement.Date)` pairs across 2023–2025 × terms {6, 12, 36} the "
    "special case fires on **210**, and on **0 of those 210** does "
    "`ScheduleStartDate ≠ Disbursement.Date`. The special case requires `calculateSeedDate` to "
    "return the schedule start — boundaries **on** the lattice — while 3e's drift requires them "
    "**off** it. On all 15 of T39's parity-setting captures exactly one of the two questions has "
    "any disagreeing cells at all. **So no single vector can discharge both, and a future "
    "\"one vector closes 3e and 3f\" proposal is refuted in advance** — the same measured "
    "refutation revision 6 recorded when it split 3d out of 3c, and revision 4 when it split 3a "
    "out of 3. (The 51,729-pair sweep is T39's **re-derivation**, re-runnable from "
    "`.softhouse/capture/periodratio/analysis/readings.py`; its raw output is not committed, so "
    "`[UNVERIFIED as a committed artefact]`, while the disjointness it asserts is "
    "`[VERIFIED: analysis/discriminate-output.txt]` on the 15 captured shapes.)",
)

# --- section 8 binding -------------------------------------------------------
sub(
    "**Binding, not a wish, widened in revision 5 from two vectors to four, in revision 6 to five "
    "and in revision 7 to six:** no conformance PASS may be claimed for `loanschedule`, and no "
    "cutover may be proposed, until at least one admissible vector trips the guard (3), one "
    "separates the adoption test (3a), one separates the per-period interest round-trip (3b), one "
    "trips the guard in the later-disbursement window (3c), one places the disbursement strictly "
    "inside a repayment period (3d), **and** one puts the schedule start and the disbursement date "
    "on different month-end anchors (3e). This is a UAT/cutover precondition, **not a ratification "
    "precondition** — the graded domain is designed to grow as vectors land, with no amendment "
    "(§3.1), and cutover is a hard `user` gate regardless. The binding is unchanged in kind from "
    "revision 3's, revision 4's, revision 5's and revision 6's; only its list of required vectors "
    "grew. **Revision 7 also states plainly what discharges it, because the distinction is now "
    "live:** five of the six shapes were **captured** by task T37 and all five **separate** — but "
    "the binding requires an **admissible vector**, and a raw attested observation is not one "
    "until item 1's promotion step is taken, which T37 recommends deferring until gate G-1 "
    "closes. **Captured is not promoted, and promoted is not cut over.**",

    "**Binding, not a wish, widened in revision 5 from two vectors to four, in revision 6 to five, "
    "in revision 7 to six and in revision 8 to SEVEN:** no conformance PASS may be claimed for "
    "`loanschedule`, and no cutover may be proposed, until at least one admissible vector trips "
    "the guard (3), one separates the adoption test (3a), one separates the per-period interest "
    "round-trip (3b), one trips the guard in the later-disbursement window (3c), one places the "
    "disbursement strictly inside a repayment period (3d), one puts the schedule start and the "
    "disbursement date on different month-end anchors (3e), **and** one puts a repayment "
    "`FromDate` on a month's last day with the two dates on the same anchor, separating step B's "
    "month-end special case (3f). This is a UAT/cutover precondition, **not a ratification "
    "precondition** — the graded domain is designed to grow as vectors land, with no amendment "
    "(§3.1), and cutover is a hard `user` gate regardless. The binding is unchanged in kind from "
    "revisions 3 through 7; only its list of required vectors grew, and revision 8's growth is a "
    "**split** of an existing item rather than a new rule (T39's N-2 measured that no one vector "
    "can serve both halves). **Revision 8 states plainly what discharges it, because the "
    "distinction is now the ONLY thing outstanding:** **all seven** shapes are now **captured** — "
    "five by task T37, two by task T39 — and **all seven separate**. But the binding requires an "
    "**admissible vector**, and a raw attested observation is not one until item 1's promotion "
    "step is taken, which T37 (F-3) and T39 (G-4) both recommend deferring until gate G-1 closes. "
    "**Captured is not promoted, and promoted is not cut over.** The binding is therefore "
    "**one promotion decision away from dischargeable**, and that decision is gated on this "
    "document being ratified — which is the loop revision 8 exists to let the driver close.",
)

# --- section 5 corpus table: RepaymentEvery row -----------------------------
sub(
    "It is the multiplier of the **recurrence's** `rateFactor` [`:1536` → `:1956-1958`]; the "
    "**interest** call site's multiplier is `periodRatio`, which equals it only on the lattice "
    "(§4.1.1, P0-T34-1). A value other than 1 therefore moves every period's interest **and** is "
    "the only way to reach `periodRatio`'s whole-period branch (§8 item 6).",

    "It is the multiplier of the **recurrence's** `rateFactor` [`:1536` → `:1956-1958`]; the "
    "**interest** call site's multiplier is `periodRatio`, which equals it only on the lattice "
    "(§4.1.1, P0-T34-1, **observed** by T39). A value other than 1 therefore moves every period's "
    "interest **and** is the only way to reach `periodRatio`'s whole-period branch "
    "[`:1457-1458`] (§8 item 6), which no capture on record exercises.",
)

# --- section 6 cross-seam consistency ---------------------------------------
sub(
    "**A future cross-seam comparison on a drifted-boundary shape (§8 item 3e) must not be "
    "expected to agree**, and if one is taken it grades the two arms against each other rather "
    "than grading a port.",

    "**A future cross-seam comparison on a drifted-boundary shape (§8 item 3e) must not be "
    "expected to agree**, and if one is taken it grades the two arms against each other rather "
    "than grading a port. **Revision 8 notes that the drifted-boundary shapes are no longer "
    "hypothetical** — T39 captured eight of them through the embeddable seam (`T39-P0-A`…`H`), so "
    "the cross-seam comparison this paragraph warns about is now cheap to run and should be "
    "labelled an arm-versus-arm measurement when it is.",
)

guard.commit(s)
print("\n".join(LOG))
