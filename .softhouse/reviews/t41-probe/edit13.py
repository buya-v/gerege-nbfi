#!/usr/bin/env python3
"""T41 edit batch 13 — section 8 item 9 (charges backlog); section 9 obligations.

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
  DEC-1        BEFORE_SHA256 = 46ec47a71151ab3cbf7d8291769a5335f1c309be27b1f6c8cb79d8f987a63ddc
  DEC-1        AFTER_SHA256  = d8c146642256bbe682ff97c5e3b7c952eaf9aa36df1a2d2fe831e607df089473

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


NAME = 'edit13'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT13-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '46ec47a71151ab3cbf7d8291769a5335f1c309be27b1f6c8cb79d8f987a63ddc'
AFTER_SHA256 = \
    'd8c146642256bbe682ff97c5e3b7c952eaf9aa36df1a2d2fe831e607df089473'

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


# --- section 8: new item 9 ---------------------------------------------------
sub(
    "8. **`fixedLength`**, **flat interest**, **holiday / non-working-day due-date adjustment**, "
    "and a **finer error taxonomy** — each a new field or member and each a gate, none required by "
    "any product today.",

    "8. **`fixedLength`**, **flat interest**, **holiday / non-working-day due-date adjustment**, "
    "and a **finer error taxonomy** — each a new field or member and each a gate, none required by "
    "any product today.\n"
    "9. **Charge captures — the corpus's oldest blind spot, now partly closed** (added in "
    "revision 8 from task T40). Twenty-one non-zero-charge schedules exist on the running-server "
    "path at attested `MathContext(19, HALF_UP)`, behind a passing preconditions script and a "
    "byte-identical zero-charge control [`.softhouse/capture/charges/`]. **They are attested raw "
    "observations, not admissible vectors, and nothing here is promoted** — item 1's rule "
    "applies. They are also **not** vectors *of this contract*: DEC-1 carries no charge field, so "
    "they grade the oracle's behaviour and the decisions in §4.5.1, not a port of `Generate`. "
    "**What they closed:** that a charge sits alongside the EMI and never inside it, that the "
    "principal split is untouched by a charge, that fee and penalty columns are separate and "
    "additive, that the per-instalment total is the sum of the rounded parts, that the charge "
    "membership rule is §4.3.2's **M4**, and the two silent-loss paths behind decision C-2. "
    "**What remains `TO_BE_CAPTURED`, in the order it is worth doing:** (a) "
    "`chargeTimeType = OVERDUE_INSTALLMENT` — the classic penalty, the most operationally "
    "important type, and entirely ungraded; it needs a persisted, disbursed loan and a "
    "business-date advance, so it belongs to a task that owns the server and can afford state; "
    "(b) charge `minCap` / `maxCap`, the most plausible remaining rounding-and-clamping defect "
    "home; (c) tranche charges — `TRANCHE_DISBURSEMENT` and `PERCENT_OF_DISBURSEMENT_AMOUNT` — "
    "which need `multiDisburseLoan = true` and belong in their own task because they change the "
    "schedule shape; (d) the whole set repeated against the **cumulative** generator, since "
    "decision C-1 rests on the two generators disagreeing and only the progressive side is "
    "observed; (e) `taxGroupId`, `glAccountId`, `chargePaymentMode = ACCOUNT_TRANSFER`, "
    "`feeFrequency` / `feeInterval`, waiver and payment; and (f) a percentage landing on an exact "
    "half-cent tie, which would pin the rounding mode inside the charge arithmetic specifically. "
    "**Path A can never discharge any of these** — the embeddable seam's request record carries "
    "no charges (§2.2, §4.5).",
)

# --- section 9: the multiplier obligation's blindness claim -----------------
sub(
    "**A port that writes `RepaymentEvery` on the interest call site returns different money on "
    "100 % of the shapes swept** — 480 of 480, worst total-interest gap MNT 398,967.73 (§4.1.1; a "
    "re-derivation, not an observation) — **and no capture in the corpus can detect it** (0 of 21 "
    "committed captures, 0 of 13 observations). That is why §8 item **3e** exists and why the "
    "binding is six vectors. All of it exact; no `float32`/`float64`/`big.Float` on this path.",

    "**A port that writes `RepaymentEvery` on the interest call site returns different money on "
    "100 % of the shapes swept** — 480 of 480, worst total-interest gap MNT 398,967.73 (§4.1.1; "
    "that sweep is a re-derivation) — **and revision 8 replaces revision 7's \"no capture can "
    "detect it\" with an observation**: task T39 captured 8 drift shapes and the oracle agrees "
    "with `periodRatio` on **415 of 415** discriminating cells and with `RepaymentEvery` on "
    "**0 of 415**, the worst gap observed at exactly the re-derived **MNT 398,967.73** "
    "[VERIFIED: captures `T39-P0-A`…`T39-P0-H`, "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. The 21 captures of the "
    "pre-T39 era still cannot see it, which is why the captures had to be taken. **The Go module "
    "must additionally reproduce (f) §4.1.1 step B's month-end special case** "
    "[`ProgressiveEMICalculator.java:1426-1436`, predicate at `:1432`, effect at `:1433`]: "
    "omitting those four lines roughly doubles `periodRatio` on alternate periods and overcharges "
    "by an observed **MNT 83,959.76** on one six-month MNT 3.9 M loan, refuted on 116 of 116 "
    "discriminating cells [VERIFIED: captures `T39-ME-A`…`T39-ME-D`]. That is why §8 has items "
    "**3e** and **3f** — the two questions are disjoint in shape space and no single vector "
    "grades both — and why the binding is **seven** vectors. All of it exact; no "
    "`float32`/`float64`/`big.Float` on this path.",
)

# --- section 9: totalOutstandingAmount obligation gains a sibling -----------
sub(
    "It is not a balance; no consumer may read meaning into it, and no scale-discipline invariant "
    "may be applied to it without deciding that case explicitly (§4.5).",

    "It is not a balance; no consumer may read meaning into it, and no scale-discipline invariant "
    "may be applied to it without deciding that case explicitly (§4.5).\n"
    "- The **Fineract-JVM adapter** must also **discard** the oracle plan's "
    "`totalRepaymentExpected` (added in revision 8, §4.5.1 decision C-1). On the progressive path "
    "it is seeded with the disbursement charges alone [`LoanScheduleParams.java:211`, `:246`], "
    "accumulates only principal + interest per period "
    "[`ProgressiveLoanScheduleGenerator.java:137`], and is **never** raised by "
    "`applyChargesForCurrentPeriod` [`:367-382`] — while the cumulative generator does raise it "
    "[`AbstractCumulativeLoanScheduleGenerator.java:504`], so the two generators disagree and the "
    "field has no single meaning. *Observed*: `totalRepaymentExpected == Σ totalDueForPeriod` "
    "**fails on 15 of 21** charge-bearing captures, with MNT 51,900 of one capture's charges "
    "visible in the rows and absent from the total [VERIFIED: "
    "`.softhouse/capture/charges/out/INVARIANTS.md`, C5]. **Neither the adapter, nor a harness, "
    "nor a conformance check may assert that this field equals the sum of the rows**: the "
    "assertion passes today only because the graded domain has no charges, and the day it fails "
    "it will be wrong about the **oracle**, not about the port. A caller wanting a total "
    "repayable sums the rows (§4.5).",
)

# --- section 9: capture-programme obligation --------------------------------
sub(
    "It must also carry, with any promoted record and as machine-readable data, what that record "
    "**cannot** grade: `installmentAmountInMultiplesOf`, `daysInYearCustomStrategy`, **fees and "
    "penalties** (every one in the Path-A corpus is `0.00`, observed), multi-disbursement, and "
    "**`periodRatio`** (§8 item 3e). A green conformance run over a corpus with a named blind "
    "spot is not evidence about that blind spot.",

    "It must also carry, with any promoted record and as machine-readable data, what that record "
    "**cannot** grade: `installmentAmountInMultiplesOf`, `daysInYearCustomStrategy`, **fees and "
    "penalties** (every one in the Path-A corpus is `0.00`, observed, and the seam's request "
    "record carries no charge at all, so no Path-A record can ever grade one), "
    "multi-disbursement, and — for any record taken before task T39 — **`periodRatio`** and "
    "**§4.1.1 step B's month-end special case** (§8 items 3e, 3f). **It must record the THREADED "
    "`MathContext` and the AMBIENT `MoneyHelper` context as two separately labelled fields** "
    "(§4.1.2); a record saying only \"captured at (19, HALF_UP)\" does not say which, and on "
    "Path A only the threaded one is evidence about the money. **Revision 8 adds a fourth "
    "closed prerequisite and a new open one:** task T39 closed §8 items 3e and 3f by capture and "
    "task T40 closed the charge blind spot for the progressive endpoint by capture (§8 item 9), "
    "while `chargeTimeType = OVERDUE_INSTALLMENT`, charge caps, tranche charges and the "
    "cumulative generator remain `TO_BE_CAPTURED`. A green conformance run over a corpus with a "
    "named blind spot is not evidence about that blind spot.",
)

guard.commit(s)
print("\n".join(LOG))
