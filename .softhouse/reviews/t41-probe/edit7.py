#!/usr/bin/env python3
"""T41 edit batch 7 — discriminate-table header and its lead-in; 4.3.2 status table."""
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
    "| wrong reading | captures failed, of 21 | first witness |",
    "| wrong reading | captures failed | first witness |",
)

sub(
    "- **discriminates**, cell by cell, every wrong reading the corpus can see. Of the seven "
    "readings put to it, six fail at least one committed capture and one does not "
    "[`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`]:",

    "- **discriminates**, cell by cell, every wrong reading the corpus can see. Of the seven "
    "readings T38 put to it, six failed at least one of the 21 committed captures of that era and "
    "one did not [`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`]. **Revision 8 "
    "extends the table with the readings T39's 16 and T40's 21 captures can now see**, and the "
    "\"captures failed\" column therefore names its denominator per row rather than assuming 21:",
)

# --- 4.3.2 status table ------------------------------------------------------
sub(
    "| the **`periodRatio` multiplier** of §4.1.1 | **NOT OBSERVED, and the corpus cannot see "
    "it** | §8 item **3e**, no capture exists |",

    "| the **`periodRatio` multiplier** of §4.1.1 | **OBSERVED** (revision 8), and the "
    "`RepaymentEvery` reading refuted on 415 of 415 discriminating cells across 8 shapes | "
    "captures `T39-P0-A`…`T39-P0-H` (§8 item **3e**) |\n"
    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes | captures `T39-ME-A`…`T39-ME-D` "
    "(§8 item **3f**) |",
)

sub(
    "**What is graded, and what is not — restated in revision 7, because the evidence base "
    "moved.** Until T37 every committed observation fell in the first two rows of the "
    "segmentation table. That is no longer true:",

    "**What is graded, and what is not — restated in revision 7 and again in revision 8, because "
    "the evidence base moved twice.** Until T37 every committed observation fell in the first two "
    "rows of the segmentation table; T37 broke that, and T39 then closed the last **NOT "
    "OBSERVED** row in this table. **Every rule §4.3.2 and §4.1.1 state normatively is now "
    "witnessed by at least one attested capture** — which is a statement about *evidence*, not "
    "about the binding, and §8 item 1's promotion step is still what stands between a capture and "
    "a graded rule:",
)

# --- 4.3.2's two honest qualifications --------------------------------------
sub(
    "Second, item **3e** has no capture at all, so **the `periodRatio` rule above remains "
    "specified-from-source and ungraded** on exactly the terms §4.3.1 states for the loop, and "
    "**no conformance PASS for `loanschedule` may be read as evidence that a port implements "
    "it.**",

    "Second — **and revision 8 changes only the first half of this sentence** — item **3e** now "
    "has captures (`T39-P0-A`…`T39-P0-H`) and its sibling **3f** has captures "
    "(`T39-ME-A`…`T39-ME-D`), so the `periodRatio` rule and its month-end special case are "
    "**observed**; but they are observed by attested raw captures, not by admissible vectors, so "
    "they remain **ungraded** on exactly the terms §4.3.1 states for the loop, and **no "
    "conformance PASS for `loanschedule` may be read as evidence that a port implements them.** "
    "**Captured is not promoted, and promoted is not cut over** — that sentence is now true of "
    "all seven binding items rather than five of six.",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
