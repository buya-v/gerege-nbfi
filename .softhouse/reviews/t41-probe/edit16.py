#!/usr/bin/env python3
"""T41 edit batch 16 — F-2 corrections at their actual wording."""
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


sub(
    "with the oracle agreeing with the special-case-present routine on **116 of 116** disagreeing "
    "cells and with the omitted routine on **0 of 116** [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**Reproducing this case is a Go-module obligation (§9) and it needs its own vector (§8 item "
    "3f), because no shape grades it and the multiplier together.**",

    "with the oracle agreeing with the special-case-present routine on **116 of 116** disagreeing "
    "cells and with the omitted routine on **0 of 116** [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**And the OLDER corpus was never blind to this one** (revision 8's own spec-check probe, "
    "finding **F-2**): the special-case-omitted reading also fails **3 of the 21 pre-T39 "
    "production-setting captures** — `P-02`, `P-02b` and `T37-3b-2`, the three whose "
    "`ScheduleStartDate` sits on a month end [VERIFIED: "
    "`.softhouse/reviews/t41-probe/t41-discriminate-output.txt`]. §5 credits `P-02` and `P-02b` "
    "with grading §4.2's **re-anchor**; they grade step B's special case as well, which no "
    "previous revision had measured. **Reproducing this case is a Go-module obligation (§9) and "
    "it still needs its own vector (§8 item 3f), because no shape grades it and the multiplier "
    "together — but its evidence is older and wider than T39, which makes 3f the best-witnessed "
    "of the seven binding items.**",
)

# --- 4.3.2's status table row -----------------------------------------------
sub(
    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes | captures `T39-ME-A`…`T39-ME-D` "
    "(§8 item **3f**) |",

    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes — **and separately refuted by 3 "
    "of the 21 pre-T39 captures**, which no previous revision had measured | captures "
    "`T39-ME-A`…`T39-ME-D`; also `P-02`, `P-02b`, `T37-3b-2` (§8 item **3f**) |",
)

# --- 4.3.1's discriminate table: add the month-end row and correct denominators
sub(
    "| **`periodRatio` with the month-end special case omitted (T39 N-2)** | 0 of those 21; "
    "**4 of T39's 16**, on 116 discriminating cells | `T39-ME-B`, cell `R2.interest` |",

    "| **`periodRatio` with the month-end special case omitted (T39 N-2)** | **3 of those 21** "
    "(`P-02`, `P-02b`, `T37-3b-2`) and **4 of T39's 15** parity-setting captures, on 116 "
    "discriminating cells | `P-02`, cell `R1.balance` |",
)

# --- section 8 item 3f: correct "no shape grades it" and add the older evidence
sub(
    "Across 4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special case present and **0 of 116** with it omitted [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`].",

    "Across 4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special case present and **0 of 116** with it omitted [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. **Revision 8's own "
    "probe adds three more witnesses, from the OLDER corpus** (finding F-2): the omitted reading "
    "also fails `P-02`, `P-02b` and `T37-3b-2` [VERIFIED: "
    "`.softhouse/reviews/t41-probe/t41-discriminate-output.txt`]. So **seven** committed captures "
    "separate this rule, which is more than any other binding item has — and it is still "
    "undischarged, because none of the seven is promoted. **That contrast is the clearest "
    "statement available of what item 1 is for.**",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
