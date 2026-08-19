#!/usr/bin/env python3
"""T41 edit batch 6 — periodRatio leak closure: step B, 4.3.1, 4.3.2, 5, 6."""
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

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
