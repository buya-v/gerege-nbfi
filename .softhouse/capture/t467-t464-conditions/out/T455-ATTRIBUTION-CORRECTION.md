# T467 / F-T464-4 — a misattribution in T455's handoff, corrected in the in-grant record

**The wrong sentence is QUOTED, not deleted.** T455's handoff, section 10 ("WHAT I COULD NOT
CLOSE"), at **line 300** of `.softhouse/handoff/T455-t448-conditions.md`, says:

> * **T448's own instrument `30-t448-tag-abuse.sh` records `all=2, both=1` for case B.** That is
>   wrong (§3). It is in `.softhouse/reviews/t448-review-t433/`, outside my grant, and reviews are
>   append-only records of a reviewer's reasoning. **Recorded, not edited.**

## What is right, and what is wrong

**RIGHT:** the figure itself is wrong, and T455 measured that correctly. The smuggled line in case
B carries the tag in its trailing comment, so both greps count it: `all` = `both` = 2 and T448's
one-predicate repair **PASSES** case B. Re-derived under a third engine by T464, who reports
`all=both=2` and T448's predicate passing. **That adjudication is settled in T455's favour and is
not reopened here.**

**WRONG:** the *location*. The figure is not in the instrument.

## Measured, at this branch's fork point

| claim | measurement | result |
|---|---|---|
| the figure is in `30-t448-tag-abuse.sh` | `grep -c 'both'` on that instrument | **2 hits, neither is the figure** — line 16 is prose ("…and both are DRIVEN here…"), line 87 is a REFUSED message ("…carrying both $GUARD and $RUNALL"). No `all` = / `both` = figure anywhere in the file. |
| where it actually is | `grep -n 'Case B fails it'` on the review | **`REVIEW.md:364`** |
| the exact text at that line | read | ``Case B fails it (`all` = 2, `both` = 1); case C fails it (`both` = 0). And add a third`` |

A `grep` for the literal `all=2` finds **nothing** anywhere in that review directory, because the
review writes it with spaces and backticks. That is presumably how the attribution slid one file
sideways: the figure was quoted from memory of its *shape*, not from its *site*.

## Why this correction lives here and not in T455's handoff

`.softhouse/handoff/T455-t448-conditions.md` is **outside T467's two granted directories**
(`.softhouse/reviews/A2-11/` and `.softhouse/capture/t467-t464-conditions/`), and the pipeline
treats an out-of-grant edit as a scope violation. It also follows the precedent T455 itself set
for exactly this situation — `.softhouse/capture/t393-t382-conditions/out/T433-CORRECTION.md`,
"with the wrong numbers **quoted, not deleted**".

**SO THIS IS DECLARED OPEN, NOT CLOSED.** T455's handoff still carries the wrong location. A
reader who reaches that sentence without reaching this file will still go looking in the wrong
instrument. Closing it needs either a grant that includes `.softhouse/handoff/`, or the same
follow-up route T455 used for T433's record.

## The generalisation, since this is the third time round the same loop

T433 mis-stated its own cardinals; T448 mis-stated the value of a predicate it supplied; T455
mis-stated where a figure it correctly refuted was written; and T464 caught it by opening the file.
The invariant is not "reviewers are careless". It is that **a citation is a measurement**, and an
unrun `grep -n` is an unmeasured claim in exactly the way an unrun predicate is.
