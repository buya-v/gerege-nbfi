#!/usr/bin/env python3
"""T41 edit batch 4 — leak-grep closure for the N-1 correction: 4.3.2 and section 9."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:220]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- 4.3.2 restatement -------------------------------------------------------
sub(
    "The `30` above is the days-in-month multiplier. On this call site it is the literal "
    "`BigDecimal.valueOf(30)` [`:1413`]; on the recurrence call site it is `daysInMonth` "
    "[`:1508`, `:1537`], which is also exactly 30 under `DayCountFixed30Over360` — see §4.1.1 for "
    "why that second difference is inert inside the graded domain.",

    "The `30` above is the days-in-month multiplier, and it is **the same 30 on both call sites, "
    "unconditionally** (revision 8, narrowing revision 7 on task T39's N-1). On this call site it "
    "is the literal `BigDecimal.valueOf(30)` [`:1413`]; on the recurrence call site it is "
    "`daysInMonth` [`:1508`, passed at `:1537`], and `:1537` is reachable **only** from the "
    "`case DAYS_30 ->` arm at `:1536`, in which `:1508`'s ternary yields `BigDecimal.valueOf(30)`. "
    "So the two arguments are numerically identical wherever either call site is reached — see "
    "§4.1.1 for the full derivation, including why the difference cannot become live outside the "
    "graded domain either. **The multiplier is the one live difference between the two call "
    "sites.**",
)

# --- section 9 obligation (e) ------------------------------------------------
sub(
    "and (e) the days-in-month multiplier as **30** on both call sites under "
    "`DayCountFixed30Over360` [`:1413`, `:1508`, `:1537`].",

    "and (e) the days-in-month multiplier as **30** on both call sites [`:1413`, `:1508`, "
    "`:1537`] — under `DayCountFixed30Over360` and, revision 8 adds, on **every** path either "
    "call site is reachable on, because `:1537` is consumed only from the `case DAYS_30 ->` arm "
    "at `:1536` where `:1508` yields the literal 30 (§4.1.1). **A port must NOT \"correct\" this "
    "second argument to differ between the call sites**; only the multiplier differs.",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
