#!/usr/bin/env python3
"""T41 edit batch 12 — charges leak closure: 4.5, 6.1, 8 items 1/9, 9 obligations.

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
  DEC-1        BEFORE_SHA256 = ede0764bcc03da14cd84fc31c2760eac10a5743a46003c38fc5df50eb059c5bb
  DEC-1        AFTER_SHA256  = 46ec47a71151ab3cbf7d8291769a5335f1c309be27b1f6c8cb79d8f987a63ddc

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


NAME = 'edit12'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT12-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    'ede0764bcc03da14cd84fc31c2760eac10a5743a46003c38fc5df50eb059c5bb'
AFTER_SHA256 = \
    '46ec47a71151ab3cbf7d8291769a5335f1c309be27b1f6c8cb79d8f987a63ddc'

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


# --- 4.5's fee/penalty bullet -----------------------------------------------
sub(
    "- **No per-row fee or penalty.** Charges, rates and taxes are a Tier A bounded context, out "
    "of scope here; the oracle's fee and penalty columns are identically zero under the pinned "
    "configuration. Named in §6 as the highest forward risk. **This is now an OBSERVED fact "
    "rather than an inferred one, and it bounds what the corpus can grade:** pass 3b emits the "
    "two columns for the first time, and every `feeAmount` and `penaltyAmount` on every row of "
    "all twelve captures is `0.00`, as are both plan totals "
    "[`.softhouse/capture/out/capture-prod3b-raw.json`; T35]. **The Path-A corpus therefore has "
    "ZERO discriminating power over charges** — a port that mishandles fees passes every one of "
    "these captures. That is a property of the corpus, not of the contract, and it must travel "
    "with any vector-store record (§8 item 1).",

    "- **No per-row fee or penalty.** Charges, rates and taxes are a Tier A bounded context, out "
    "of scope here; the oracle's fee and penalty columns are identically zero under the pinned "
    "configuration. Named in §6 as the highest forward risk. **This is an OBSERVED fact rather "
    "than an inferred one, and it bounds what the corpus can grade:** pass 3b emits the two "
    "columns for the first time, and every `feeAmount` and `penaltyAmount` on every row of all "
    "twelve captures is `0.00`, as are both plan totals "
    "[`.softhouse/capture/out/capture-prod3b-raw.json`; T35]. **The Path-A corpus therefore has "
    "ZERO discriminating power over charges** — a port that mishandles fees passes every one of "
    "these captures — and that remains true: the embeddable seam's request record carries no "
    "charges at all, so **no** Path-A capture can ever grade one. That is a property of the "
    "corpus, not of the contract, and it must travel with any vector-store record (§8 item 1).\n"
    "  **Revision 8 adds what changed on the OTHER path.** Task T40 captured **21 non-zero-charge "
    "schedules on the running server** and observed that the quantities this contract does carry "
    "— `PrincipalMinor`, `InterestMinor`, `OutstandingPrincipalMinor` — and the level installment "
    "are **cell-for-cell identical to the zero-charge control on all 21**: a charge sits "
    "**alongside** the schedule, never inside it [VERIFIED: "
    "`.softhouse/capture/charges/out/INVARIANTS.md`, C8 and C9 PASS 21/21]. So this omission is "
    "no longer only *safe by scope*, it is **safe by observation**, and admitting charges later "
    "changes no field's meaning. The two decisions that observation forces — on the oracle's "
    "`totalRepaymentExpected`, and on a charge the oracle silently drops — are **§4.5.1**.",
)

# --- 6.1 ---------------------------------------------------------------------
sub(
    "- **6.1 Charges, fees, penalties, tax — the highest unmitigated risk.** The oracle's plan "
    "already has fee and penalty columns; when the charges context lands, a repayment row "
    "acquires further components. It is acceptable because charges are out of scope here, and "
    "because **the response was shaped so the addition is purely additive**: with no total-due "
    "column, no existing field's meaning changes when charges arrive. A total-due column would "
    "have changed meaning silently — the most dangerous kind of contract change, because it does "
    "not break a compile. The likeliest resolution is not amending `Period` at all but composing: "
    "charges computed by their own context and applied to a schedule. DEC-1 does not decide that; "
    "it does not foreclose it.",

    "- **6.1 Charges, fees, penalties, tax — the highest risk, and revision 8 is the first "
    "revision with EVIDENCE about it.** The oracle's plan already has fee and penalty columns; "
    "when the charges context lands, a repayment row acquires further components. It is "
    "acceptable because charges are out of scope here, and because **the response was shaped so "
    "the addition is purely additive**: with no total-due column, no existing field's meaning "
    "changes when charges arrive. A total-due column would have changed meaning silently — the "
    "most dangerous kind of contract change, because it does not break a compile. "
    "**That argument was a re-derivation through revision 7 and is now an OBSERVATION** (§4.5.1): "
    "across 21 charge-bearing captures the principal split, the interest, the outstanding "
    "principal and the level installment are cell-for-cell identical to the zero-charge control, "
    "so the additive shape is measured rather than hoped for [VERIFIED: "
    "`.softhouse/capture/charges/out/INVARIANTS.md`, C8/C9 PASS 21/21]. **Revision 8 also shows "
    "what a total-due column WOULD have cost**, from the oracle's own `totalRepaymentExpected`: "
    "it omits every charge applied in the main loop, fails `total == Σ row totals` on 15 of 21 "
    "observed captures, and means something different in the cumulative generator — the exact "
    "silent meaning-change this bullet predicted, seen in the wild (§4.5.1 decision C-1). The "
    "likeliest resolution is still not amending `Period` at all but composing: charges computed "
    "by their own context and applied to a schedule. DEC-1 does not decide that; it does not "
    "foreclose it. **The two things it does now decide** are that the oracle's "
    "`totalRepaymentExpected` is not carried and must be discarded, and that a charge the oracle "
    "silently drops is refused rather than reproduced (§4.5.1, C-1 and C-2).",
)

# --- section 8 item 1's "cannot grade" list ---------------------------------
sub(
    "and the discipline that any promoted record must carry, **as machine-readable data rather "
    "than prose**, what it cannot grade — `installmentAmountInMultiplesOf`, "
    "`daysInYearCustomStrategy`, fees, penalties, multi-disbursement, and (§4.1.1) `periodRatio`.",

    "and the discipline that any promoted record must carry, **as machine-readable data rather "
    "than prose**, what it cannot grade — `installmentAmountInMultiplesOf`, "
    "`daysInYearCustomStrategy`, fees, penalties, multi-disbursement, and, for any record taken "
    "before T39, `periodRatio` and §4.1.1 step B's month-end special case (§4.1.1, §8 items 3e "
    "and 3f). **Revision 8 adds one more field to that machine-readable block**: the **threaded** "
    "`MathContext` and the **ambient** `MoneyHelper` context as two separately labelled values, "
    "never one conflated \"captured at (19, HALF_UP)\" — §4.1.2.",
)

guard.commit(s)
print("\n".join(LOG))
