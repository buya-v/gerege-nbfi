# T64 — the prediction was RIGHT and one of its reasons was WRONG

**Written AFTER the capture. `PREDICTION.md` is deliberately left exactly as it was committed** —
rewriting it would destroy the only thing that makes it evidence, which is that git can show it
predates `run-pass3g.sh`. This file is the correction, and pattern **P-11** is why it exists:

> *The code can be RIGHT and its stated reason WRONG — and the reason is what the next contributor
> checks.*

## What was confirmed

All four schedules, cell for cell: **1,539 predicted cells, zero mismatches**
(`check-prediction.py` against `.softhouse/capture/out/capture-prod3g-raw.json`). Every claim in
PREDICTION.md **§3** stands, including the sharp one — that `T64-ZP-B`, one period shorter than
`T64-ZP-A`, comes back as a completely different schedule that pays off at period 15 and leaves 40
dead rows. The threshold `n ≥ 2·B` in **§2.5** is the right threshold.

## What was wrong

**PREDICTION.md §2.4 gives the wrong mechanism for that threshold.** It says the smoothing loop is
neutralised because `adjustment() = B/n` **quantizes to zero** and the loop then breaks at
`ProgressiveEMICalculator.java:1270-1273`. That is not what happens.

Re-derived from source afterwards, with `Money.copy(double)` actually opened:

```java
public boolean shouldBeAdjusted() {
    double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
    return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero() && emiDifference.abs()
            .multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));
}
```
[VERIFIED: `EmiAdjustment.java:31-36`]

```java
public Money copy(final double amount) { return copy(BigDecimal.valueOf(amount)); }
public Money copy(final BigDecimal amount) { return new Money(this.currency, amount, this.mc); }
```
[VERIFIED: `Money.java:216-222`]

**`copy(double)` REPLACES the amount; it does not scale it.** So the right-hand side is
`floor(n/2)` **whole currency units, flat** — it carries no dependence on the installment at all.
The left-hand side is `|emiDifference| × 100`
[VERIFIED: `Money.java:380-390`, `multipliedBy(long, mc)`]. In minor units the guard is therefore

> **`|emiDifference|_minor > floor(n/2)`**

and on a rounding-floor shape `|emiDifference|` is exactly the principal `B` in minor units, because
the final period's installment has absorbed the whole residual. So:

| | `|emiDiff|` | `floor(n/2)` | guard | outcome |
|---|---|---|---|---|
| `T64-ZP-A` (n=56) | 28 | 28 | `28 > 28` → **false** | loop never runs; 55 zero-principal rows |
| `T64-ZP-B` (n=55) | 28 | 27 | `28 > 27` → **true** | loop runs; pays off at period 15 |

**The gate is `shouldBeAdjusted()` returning false at `:1267-1269`, not the adjustment quantizing
away at `:1270-1273`.** Both readings happen to produce `n ≥ 2·B`, which is exactly why the wrong
one survived a ten-rate check: **agreement on the answer is not agreement on the mechanism.**

## The two rates where the predicted `n_min` was too high

PREDICTION.md §2.6 recorded, honestly, that the `n_min` bound was exact on 8 of 10 rates and an
over-estimate at 24 % (26 observed vs 50 derived) and 60 % (16 vs 20). The corrected mechanism gives
the **same** 8 of 10, so it does not explain those two either. What does: the loop has **four**
exits, and those two shapes leave through a different one — the trial is built, and the adoption
test `hasLessEmiDifference` [VERIFIED: `EmiAdjustment.java:45-47`, applied at
`ProgressiveEMICalculator.java:1288-1290`] rejects it, which **discards the trial and leaves the
live schedule at its pre-trial, zero-principal values**. `n ≥ 2·B` is therefore **sufficient and not
necessary**, under either reading. That was true of the original statement too and is repeated here
so the correction does not quietly acquire a claim the measurement never supported.

## Restatements of the wrong claim, and where they live

Per the standing rule — *grep the whole document for restatements of a corrected claim* — the wrong
mechanism appears in exactly two other places:

1. **`.softhouse/capture/src/Capture3g.java`, header comment.** It says
   `n > 2*B  so the EMI smoothing adjustment B/n quantizes to zero and the loop breaks`.
   **It has NOT been edited and must not be**: that file's sha256 is recorded inside the capture's
   own attestation block (`sources[].sha256` =
   `de75bfb8367a91abe10eda4f63577a093af3a90b4530c69963fce2dc50416b32`) and asserted by
   `run-pass3g.sh` precondition 4. Editing it would make the committed capture unverifiable in
   order to fix a comment. A reader who reaches that header is pointed here by this file and by the
   handoff.
2. **The commit message of `37886ac`.** Immutable by construction; corrected here.

The **promoted vectors do not carry the wrong mechanism** — their `_note` and `graded_against`
evidence state the `shouldBeAdjusted` form, and say in as many words that the prediction's reasoning
was wrong on this point.

## Why this is worth a file rather than a footnote

The misreading is not exotic. `originalEmi.copy(floor(n/2))` is a method called **on the
installment** taking **a count**, and reading it as "the installment times the count" is the natural
thing to do. It is what the author of this capture did, from these lines, before opening
`Money.java`. It is now a **named, measured counterfactual** in the store —
`ZP-GUARD-SCALES-THE-INSTALLMENT` — which all 32 previously-promoted parity vectors pass and
`T64-ZP-A`, `T64-ZP-C` and `T64-ZP-D` kill by 28, 17 and 36 minor units respectively.

The Go port already had the correct reading, with the correct citation, before this task started
[`nexus/internal/apps/loanschedule/emi.go:924-942`]. That is an independent confirmation of the
correction and a point in T10's favour — and it does not reduce the risk, because until this capture
**nothing in the corpus could have told the two readings apart.**
