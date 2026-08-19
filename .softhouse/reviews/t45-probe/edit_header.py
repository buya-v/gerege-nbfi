p = 'docs/adr/DEC-1-schedule-generator-adapter.md'
s = open(p).read()

R = [
    ("**Status: DRAFT (revision 8) — the RATIFICATION CANDIDATE; awaiting independent re-review, then ratification. Revision 8 was written by task T41, which may revise this unratified draft but may NOT ratify it.**",
     "**Status: DRAFT (revision 9) — the RATIFICATION CANDIDATE. Revision 9 is an ERRATUM, not a rewrite: it carries the three P1s and three P2s of independent re-review T43 — which returned ACCEPTED WITH REQUIRED CHANGES with NO P0, the first round in eight without one — plus the three findings of capture audit T44 that touch this document. Revision 9 was written by task T45, which may revise this unratified draft but may NOT ratify it.**\n\n**Why revision 8 was not ratified on T43's review, stated so the delay is not read as a doubt about the money.** T43 found no reason not to ratify. The driver declined anyway, for one reason: **ratification FREEZES**, and a ratified DEC-n cannot be amended by an agent without a gate. P1-T43-3 was a known-wrong sentence about money — it named M4 as deciding where a *charge* lands, which would have put an instalment fee on one row instead of twelve. **Known-wrong sentences about money are not frozen.** Revision 9 exists to be the thing that can be."),
    ("| Run | `2026-08-17-run1-harness-schedule-poc`, task T4 (attempt 2); revision 3 by task T24; revision 4 by task T28; revision 5 by task T31; revision 6 by task T33; revision 7 by task T38; revision 8 by task T41 |",
     "| Run | `2026-08-17-run1-harness-schedule-poc`, task T4 (attempt 2); revision 3 by task T24; revision 4 by task T28; revision 5 by task T31; revision 6 by task T33; revision 7 by task T38; revision 8 by task T41; revision 9 by task T45 |"),
    ("DEC-1 revision 7 (superseded by revision 8 on the evidence of capture tasks T39 and T40, not by a review finding) |",
     "DEC-1 revision 7 (superseded by revision 8 on the evidence of capture tasks T39 and T40, not by a review finding); DEC-1 revision 8 (accepted-with-required-changes, **no P0**, by re-review T43) |"),
]
for a, b in R:
    assert s.count(a) == 1, (s.count(a), a[:60])
    s = s.replace(a, b)

entry = open('.softhouse/reviews/t45-probe/rev9-entry.md').read()
anchor = "- **Revision 8 (task T41)** applies the findings"
assert s.count(anchor) == 1
s = s.replace(anchor, entry + anchor)
open(p, 'w').write(s)
print('ok')
