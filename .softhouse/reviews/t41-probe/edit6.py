#!/usr/bin/env python3
"""T41 edit batch 6 — periodRatio leak closure: step B, 4.3.1, 4.3.2, 5, 6.

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
  DEC-1        BEFORE_SHA256 = 53d68a2d71630847ee331d0d20eb8212fd7b004575a1f5fb433888b140634e65
  DEC-1        AFTER_SHA256  = 6ae9a163512e617f201307c40bd6c54ad4c47ce536eee4616a72836a5ade5d22

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


NAME = 'edit6'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT6-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '53d68a2d71630847ee331d0d20eb8212fd7b004575a1f5fb433888b140634e65'
AFTER_SHA256 = \
    '6ae9a163512e617f201307c40bd6c54ad4c47ce536eee4616a72836a5ade5d22'

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


# --- 4.1.1 step B: the month-end special case, normative --------------------
sub(
    "**Step B — the whole-period offset `k`** [`:1423-1439`]. `k` is the whole months from the "
    "seed to the repayment period's `FromDate` (`ChronoUnit.MONTHS.between`, truncated toward "
    "zero), with an explicit **month-end special case** [`:1430-1433`]: when the period's "
    "`FromDate` is the **last day of its month** *and* the seed's day-of-month is **strictly "
    "later** than `FromDate`'s day-of-month, `k` is measured to `FromDate.plusDays(1)` instead.",

    "**Step B — the whole-period offset `k`** [`:1423-1439`]. `k` is the whole months from the "
    "seed to the repayment period's `FromDate` (`DateUtils.getExactDifference(seed, FromDate, "
    "MONTHS)`, truncated toward zero) [`:1435`], with an explicit **month-end special case** "
    "whose predicate revision 8 spells out literally, because omitting the case is the most "
    "plausible mis-port of this routine and it is worth six figures of tugriks "
    "[`:1426-1436`, predicate at `:1432`, effect at `:1433`]:\n\n"
    "```\n"
    "seedDateDay      = seed.getDayOfMonth()                                        # :1426\n"
    "targetDateDay    = repaymentPeriod.FromDate.getDayOfMonth()                    # :1427\n"
    "targetDateLastDay= lastDayOfMonth(repaymentPeriod.FromDate).getDayOfMonth()    # :1428-1429\n"
    "if targetDateLastDay == targetDateDay AND seedDateDay > targetDateDay:         # :1432\n"
    "    k = wholeMonths(seed -> repaymentPeriod.FromDate.plusDays(1))              # :1433\n"
    "else:\n"
    "    k = wholeMonths(seed -> repaymentPeriod.FromDate)                          # :1435\n"
    "```\n\n"
    "In words: when the period's `FromDate` is the **last day of its month** *and* the seed's "
    "day-of-month is **strictly later** than `FromDate`'s day-of-month, `k` is measured to "
    "`FromDate.plusDays(1)` instead. **These four lines are live, load-bearing and now OBSERVED** "
    "(revision 8; task T39): dropping them roughly doubles `periodRatio` on alternate periods and "
    "overcharges by **MNT 33,177.27** on a MNT 1.2 M six-month loan and **MNT 83,959.76** on a "
    "MNT 3.9 M one, with the oracle agreeing with the special-case-present routine on **116 of "
    "116** disagreeing cells and with the omitted routine on **0 of 116** [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**Reproducing this case is a Go-module obligation (§9) and it needs its own vector (§8 item "
    "3f), because no shape grades it and the multiplier together.**",
)

# --- 4.3.1: "the six the binding names" -------------------------------------
sub(
    "and that put the schedule start and the disbursement date on **different month-end anchors**, "
    "separating §4.1.1's `periodRatio` from `RepaymentEvery` (§8 item **3e**, added in revision 7) "
    "are the six the binding names. **Revision 7 records where they stand, and the distinction "
    "between the two states matters:** five of the six (3, 3a, 3b, 3c, 3d) were **captured from "
    "the pinned reference oracle by task T37** and every one of them separates the right reading "
    "from the wrong one (`.softhouse/capture/dec1-binding/`, analysis "
    "`analysis/discriminate-output.txt`); those captures are **attested raw observations and not "
    "yet admissible parity vectors** — the promotion step is §8 item 1 and belongs after gate G-1 "
    "(T37's F-3). Item **3e** has no capture at all. So **this rule is now witnessed but the "
    "binding is not discharged, and no conformance PASS for `loanschedule` may be read as "
    "evidence that a port implements it** until admissible vectors exist for all six.",

    "that put the schedule start and the disbursement date on **different month-end anchors**, "
    "separating §4.1.1's `periodRatio` from `RepaymentEvery` (§8 item **3e**, added in revision 7) "
    "and that put them on the **same** month-end anchor with a `FromDate` on a month's last day, "
    "separating §4.1.1 step B's month-end special case from its omission (§8 item **3f**, split "
    "out of 3e in revision 8) are the **seven** the binding names. **Revision 8 records where "
    "they stand, and the distinction between the two states matters:** **all seven** are now "
    "**captured from the pinned reference oracle** — 3, 3a, 3b, 3c and 3d by task T37 "
    "(`.softhouse/capture/dec1-binding/`, analysis `analysis/discriminate-output.txt`), and 3e "
    "and 3f by task T39 (`.softhouse/capture/periodratio/`, analysis "
    "`analysis/discriminate-output.txt`) — and every one of them separates the right reading from "
    "the wrong one. **But every one of those captures is an attested raw observation and NOT an "
    "admissible parity vector**; the promotion step is §8 item 1 and belongs after gate G-1 "
    "(T37's F-3, T39's G-4). So **all seven rules are now witnessed and the binding is still not "
    "discharged, and no conformance PASS for `loanschedule` may be read as evidence that a port "
    "implements any of them** until admissible vectors exist for all seven.",
)

# --- 4.3.1: the discriminate table's last row and its follow-up -------------
sub(
    "| **`RepaymentEvery` instead of `periodRatio` (P0-T34-1)** | **0 — THE CORPUS IS BLIND** | "
    "none exists; see §8 item **3e** |",

    "| **`RepaymentEvery` instead of `periodRatio` (P0-T34-1)** | **0 of those 21 — that corpus "
    "was blind**; **8 of T39's 16**, on 415 discriminating cells | `T39-P0-A`, cell "
    "`R1.interest` (`19,575.00` against the observed `20,250.00`) |\n"
    "| **`periodRatio` with the month-end special case omitted (T39 N-2)** | 0 of those 21; "
    "**4 of T39's 16**, on 116 discriminating cells | `T39-ME-B`, cell `R2.interest` |\n"
    "| charges folded INTO the EMI rather than beside it (T40 Q1) | 0 of those 21 — none carries "
    "a non-zero charge; **21 of T40's 21** | `FC-02`, cell `R1.totalDueForPeriod` |\n"
    "| `totalRepaymentExpected` == Σ period totals (T40 D-1) | not carried by this contract; "
    "**15 of T40's 21** as an oracle invariant | `FC-02`, plan total |",
)

sub(
    "The last row is the honest result and revision 7 states it rather than hiding it: correcting "
    "the multiplier makes the *document* right, and leaves the *corpus* unable to grade it. On the "
    "§8 item 3e candidate shape the two readings differ on 18 of 25 cells and by **MNT 2,376.67** "
    "in total interest — a re-derivation, recorded as a candidate shape to capture (§4.1.1).",

    "**Revision 7's last row read \"0 — THE CORPUS IS BLIND\", and revision 8 replaces it with an "
    "observation rather than leaving it as an admission.** T39 captured 16 shapes and T40 "
    "captured 21, and the four readings above now fail on real cells: the multiplier reading on "
    "**8 of T39's 16** across 415 discriminating cells (`periodRatio` 415 of 415, `RepaymentEvery` "
    "0 of 415), the month-end omission on **4 of 16** across 116 cells, and both charge readings "
    "on T40's set [VERIFIED: `.softhouse/capture/periodratio/analysis/discriminate-output.txt`; "
    "`.softhouse/capture/charges/out/FULLCELL.md`, `out/INVARIANTS.md`]. On the §8 item 3e "
    "candidate shape revision 7 re-derived a 18-of-25-cell, **MNT 2,376.67** separation; the "
    "oracle returned total interest **76,984.00** against the `RepaymentEvery` reading's "
    "**74,607.33** — the re-derivation was right to the cent, and it is now an **observation** "
    "[VERIFIED: capture `T39-P0-A`]. **Nothing about the binding changes:** these are attested "
    "raw observations, not admissible vectors, so a conformance PASS still grades none of it "
    "(§8 item 1).",
)

guard.commit(s)
print("\n".join(LOG))
