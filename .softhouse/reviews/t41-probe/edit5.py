#!/usr/bin/env python3
"""T41 edit batch 5 — T39: periodRatio is now OBSERVED; item 3e splits into 3e + 3f.

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
  DEC-1        BEFORE_SHA256 = ad51e78d8bf5e3d1007ff60d5eb26a23ef958d075236b0e49bf1cc8e28459644
  DEC-1        AFTER_SHA256  = 53d68a2d71630847ee331d0d20eb8212fd7b004575a1f5fb433888b140634e65

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


NAME = 'edit5'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT5-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    'ad51e78d8bf5e3d1007ff60d5eb26a23ef958d075236b0e49bf1cc8e28459644'
AFTER_SHA256 = \
    '53d68a2d71630847ee331d0d20eb8212fd7b004575a1f5fb433888b140634e65'

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


# =============================================================================
# 4.1.1 — the corpus-blindness paragraph
# =============================================================================
sub(
    "**The corpus is blind to this, and stayed blind through T37.** Checked two ways. "
    "**Directly:** across **all 35** committed captures — the twelve Path-A pass-3, the twelve "
    "pass-3b re-emissions and the eleven T37 binding captures — **not one repayment period has a "
    "`periodRatio` different from `RepaymentEvery`** "
    "[`.softhouse/reviews/t38-probe/t38-corpus-blind-output.txt`]. **Operationally:** the two "
    "readings return **identical money on all 21** captures at the production `MathContext` "
    "(eleven Path-A pass-3, ten T37 binding), so no cell of any of them separates them; and per "
    "T34 **0 of the 13** observations does either "
    "(`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`; "
    "`.softhouse/reviews/t34-probe/t34_corpus_blind.py`). Every one of them either has "
    "`ScheduleStartDate == Disbursements[0].Date`, so the two seeds coincide, or a schedule start "
    "on the 1st, so the re-anchor never fires. `P-02` (seed day 31) and `P-02b` (seed day 30) — "
    "the two captures §5 credits with grading the month-end rule — are exactly the aligned case. "
    "**This is the fifth consecutive round in which a reading reproduced the whole corpus and was "
    "still wrong**, and it is why §8 gains item **3e** and the binding widens to six vectors.",

    "**The corpus was blind to this through T37. Task T39 closed the blindness by OBSERVATION, "
    "and the observation says `periodRatio`** (revision 8). Both halves are stated, because the "
    "distinction is the whole lesson.\n\n"
    "**What the pre-T39 corpus could not see.** Checked two ways. **Directly:** across **all 35** "
    "committed captures of that era — the twelve Path-A pass-3, the twelve pass-3b re-emissions "
    "and the eleven T37 binding captures — **not one repayment period has a `periodRatio` "
    "different from `RepaymentEvery`** "
    "[`.softhouse/reviews/t38-probe/t38-corpus-blind-output.txt`]. **Operationally:** the two "
    "readings return **identical money on all 21** of them at the production `MathContext` "
    "(eleven Path-A pass-3, ten T37 binding), so no cell of any separates them; and per T34 "
    "**0 of the 13** observations does either "
    "(`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`; "
    "`.softhouse/reviews/t34-probe/t34_corpus_blind.py`). Every one either has "
    "`ScheduleStartDate == Disbursements[0].Date`, so the two seeds coincide, or a schedule start "
    "on the 1st, so the re-anchor never fires. `P-02` (seed day 31) and `P-02b` (seed day 30) — "
    "the two captures §5 credits with grading the month-end rule — are exactly the aligned case. "
    "**That was the fifth consecutive round in which a reading reproduced the whole corpus and "
    "was still wrong.**\n\n"
    "**What task T39 then observed on the pinned reference oracle.** Sixteen captures, one run, "
    "Path A, at attested threaded `(19, HALF_UP)` except one labelled `(12, HALF_UP)` calibration "
    "[VERIFIED: `.softhouse/capture/periodratio/out/t39-periodratio.json`, "
    "`ATTESTATION.md`, `REPRODUCE.md`]. On the **415 cells where the `periodRatio` and "
    "`RepaymentEvery` readings disagree**, across **8 drift shapes**, the oracle agrees with "
    "**`periodRatio` on 415 of 415** and with **`RepaymentEvery` on 0 of 415**; end to end the "
    "`periodRatio` reading reproduces **every cell of all 15 parity-setting captures — 1,239 "
    "cells — with zero mismatches** [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. **P0-T34-1 is settled "
    "empirically**, and this document's re-derived worst case is now an observed one: MNT "
    "**398,967.73** of total interest on `T39-P0-D` (start `2024-01-28`, disbursement "
    "`2024-01-31`, MNT 50,000,000, 36 × 21.6 %), observed **18,659,151.45** against the "
    "`RepaymentEvery` reading's 18,260,183.72 [VERIFIED: capture `T39-P0-D`]. Three further "
    "properties this subsection asserted from re-derivation are now observed too: **there is no "
    "size threshold** — `T39-P0-F` at MNT **100** still separates on 27 cells, observed total "
    "interest `6.41` against `6.21` [VERIFIED: capture `T39-P0-F`]; **the drift is not a "
    "January, leap-year or 31-day-month artefact** — it reproduces seeded in March, in a 30-day "
    "November and in the common year 2025 [VERIFIED: captures `T39-P0-G`, `T39-P0-H`, "
    "`T39-P0-E`]; and **the DUE DATES move, not only the money** — on `T39-P0-A` "
    "`loanTermInDays` is **185**, not the 182 the aligned shape gives [VERIFIED: capture "
    "`T39-P0-A`; T39's N-7]. Three controls outside the drift region reproduce committed records "
    "taken by **different harnesses on different tasks** digit for digit, so the rig is not the "
    "variable [VERIFIED: T39 §4, controls C1–C4].\n\n"
    "**The month-end special case of step B is OBSERVED to be live and load-bearing, and it is a "
    "SEPARATE question from the multiplier** (revision 8, on T39's N-2). Omitting the four lines "
    "at [`:1430-1433`] roughly **doubles** `periodRatio` on alternate periods: on `T39-ME-B` "
    "(start = disbursement `2024-01-31`, MNT 1,200,000, 6 × 21.6 %) the with-case ratios are "
    "`[1,1,1,1,1,1]` and the without-case ratios `[1,2,1,2,1,2]`, and the observed total interest "
    "is **76,723.70** against the omitted reading's 109,900.97 — an **MNT 33,177.27** overcharge, "
    "29 cells wide; `T39-ME-A` is worth **MNT 83,959.76** on one six-month MNT 3.9 M loan. Across "
    "4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special-case-present routine and **0 of 116** with the routine minus it [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**The two questions are DISJOINT in shape space and no single vector can grade both**: over "
    "51,729 same-month `(ScheduleStartDate ≤ Disbursement.Date)` pairs across 2023–2025 × terms "
    "{6, 12, 36}, the special case fires on **210**, and on **0 of those 210** does "
    "`ScheduleStartDate ≠ Disbursement.Date` — the special case needs `calculateSeedDate` to "
    "return the schedule start, i.e. boundaries **on** the lattice, while the multiplier drift "
    "needs them **off** it. The 15 captured shapes confirm it: on every one, exactly one of the "
    "two questions separates and the other has zero disagreeing cells. So **§8's item 3e splits "
    "into 3e (drift) and 3f (month-end), and the binding widens from six vectors to seven.** "
    "(The 51,729-pair sweep is T39's **re-derivation**, re-runnable from "
    "`.softhouse/capture/periodratio/analysis/readings.py`, and its raw output is not committed — "
    "`[UNVERIFIED as a committed artefact]`; the disjointness conclusion is corroborated by the "
    "15 captured shapes, which is `[VERIFIED: analysis/discriminate-output.txt]`.)\n\n"
    "**What is still NOT observed, stated so the correction does not overshoot.** T39 did not "
    "instrument `calculatePeriodRatio`, `calculateSeedDate` or the rate factor. What is observed "
    "is that the oracle's output is the one **only** a `periodRatio`-with-month-end-case "
    "execution produces and is not the one either alternative produces. That is a "
    "**discrimination**, not an internal observation, and the claim \"the special case fired on "
    "periods 2, 4 and 6\" remains a re-derivation [T39 §7]. `periodRatio`'s `YEARS`, `WEEKS` and "
    "`DAYS` arms [`:1405`, `:1407`, `:1408`] and its whole-period return branch [`:1457-1458`] "
    "remain **entirely uncaptured** (§8 item 6).",
)

guard.commit(s)
print("\n".join(LOG))
