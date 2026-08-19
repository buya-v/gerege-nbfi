#!/usr/bin/env python3
"""T41 edit batch 12 — charges leak closure: 4.5, 6.1, 8 items 1/9, 9 obligations."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
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

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
