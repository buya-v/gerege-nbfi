# The landing sequence for `T375` → `T360` → `T387`, PRE-VERIFIED IN SCRATCH

Driver, fire `20260828-140005` iteration 3, while `T384` was still reviewing `T375`.
**Nothing here has been merged to `main`.** This is a measurement, so that the next driver — this one or
the next fire — can land the sequence without rediscovering any of it.

## The sequence, exactly

```
git merge softhouse/T375-t364-conditions      # rc 0, clean
git merge softhouse/T360-divergence-class     # rc 0, clean
git merge softhouse/T387-review-t360          # rc 0, clean
# then, BY NAME, never by line:
sed -i '' 's/^EXEMPTION_PIN_LEDGER_WRONGIMPLS=13$/EXEMPTION_PIN_LEDGER_WRONGIMPLS=14/' .softhouse/conformance.sh
```

**`T375` must land BEFORE `T360`**, because `T360` cannot bump a pin in a file another worker held.
**`T384` must APPROVE `T375` before any of it lands.** This document does not authorise the merge; it only
removes the guesswork from it.

## WHY "BY NAME, NEVER BY LINE" IS NOT PEDANTRY — three trees, three line numbers

| tree | line |
|---|---|
| `main` | **3923** |
| `softhouse/T375-t364-conditions` | **4469** |
| the combined `T375`+`T360`+`T387` merge result | **4476** |

`T375` raised this hazard from inside its own worktree, estimating the shift at ~90; it is **546** against
`main` and a **third** value again on the merge result. A `sed` anchored to `^EXEMPTION_PIN_LEDGER_WRONGIMPLS=13$`
changes **exactly one line** (`git diff --numstat` → `1 1`), verified. A line-number edit would have hit
unrelated code on every one of these trees.

This is **P-86** — a cardinal that names a location rots the moment anything above it moves — and it is the
third time in this fire that a line-number citation was caught before it did damage rather than after.

## MEASURED RESULT OF THE WHOLE SEQUENCE

`bash .softhouse/conformance.sh` on the pin-bumped merge result, from a clean committed tree:

```
EXIT 0
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value, P-84
VERDICT: PASS — 46 parity vectors / 7884 cells
ledger parity        PASS 7  FAIL 0      ← UNMOVED
ledger oracle-refusal PASS 6  FAIL 0     ← UNMOVED
ledger cells         144 graded, 39 MONEY ← money cells UNMOVED; +2 cells are the divergence vector's
LDG-DIV-01-oracle-accepts-sub-minor-unit-residue   divergence   PASS   2 cells (0 money)
KILLED  ledger-wrong-residue-rounding — exit 1, ledger parity FAIL 1
all 14 wrong ledger implementations DIED through this harness, not by hand
dead-path frontier GREEN, deadOccurrences 108, corpus 1395
```

**The divergence vector grades 2 cells and ZERO money cells.** That is the design holding: the oracle's
`100.125` is recorded as characters and byte-checked, never as a number, because no `int64` holds it.

## THE ASYMMETRY THE HARNESS NOW PRINTS, AND IT IS THE RIGHT ONE

> A DIVERGENCE IS NOT A PARITY PASS, and it is counted NOWHERE in `ledger parity PASS`.
> A DIVERGENCE FAIL *IS* ADDED TO `ledger parity FAIL`, deliberately and asymmetrically.

A divergence can therefore **never inflate** a pass count, but **can** redden the bar. That is the correct
direction for a claim-limiting class: it buys no credit and still carries risk.

## What this does NOT establish
Nothing about `G-19`, which stays OPEN. A green `LDG-DIV-01` means only *"the disagreement is still exactly
as recorded"* — the oracle still accepts a sub-minor-unit residue the port's reader still refuses.
