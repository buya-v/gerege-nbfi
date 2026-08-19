#!/usr/bin/env python3
"""T41 — contract.go edits, batch 4: remaining periodRatio/daysInMonth restatements."""
import io
import sys

P = "nexus/internal/apps/loanschedule/contract/contract.go"
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
    """// The 30 is the days-in-month multiplier — a hard-coded literal on this call
// site (:1413), the local daysInMonth on the recurrence call site (:1508, :1537),
// and exactly 30 on both under DayCountFixed30Over360.""",
    """// The 30 is the days-in-month multiplier — a hard-coded literal on this call
// site (:1413), the local daysInMonth on the recurrence call site (:1508, passed
// at :1537), and EXACTLY 30 ON BOTH ON EVERY PATH EITHER IS REACHABLE ON, not
// merely under DayCountFixed30Over360 (revision 8): :1537 is consumed only from
// the `case DAYS_30 ->` arm at :1536, which is precisely where :1508's ternary
// yields BigDecimal.valueOf(30). See Rounding.RateFactorScale.""",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
