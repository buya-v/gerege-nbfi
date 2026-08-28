# DO NOT APPLY `PROPOSED-impl-refusal-routing.patch`

**Written by the `/softhouse-program` driver, local fire `20260828-140005`, as condition C3 of
`T414`'s review of `T398`. It is deliberately a NEW file: `REVIEW.md` and the patch are committed
evidence and are not edited in place.**

## The one sentence that matters

`PROPOSED-impl-refusal-routing.patch` in this directory is a **78-line, `git apply`-able diff that
grades BACKWARDS**. Applying it makes a **wrong** port pass and the **correct** port fail. It must
not be applied under either option of `G-19`, and the condition its own header sets — *"lands only
if (a) is chosen"* — is **not** a safe gate.

## Why the header is the hazard rather than the mitigation

The patch header reads, in part:

> So this patch lands only if (a) is chosen, and the HTTP status and code below are placeholders a
> real change must settle.

That reads as a *precondition satisfied by a future decision*. A later reader who finds `G-19`
resolved as option (a) would take the header at its word and apply it. **`P-100` establishes the
patch is wrong under BOTH options**, so there is no future state of `G-19` in which applying it is
correct. The caution has a shape that expires; the defect does not.

## The measurement, and why the original measurement was not wrong

`T359` measured this patch correctly. Against the stuck candidate vector it does exactly what it
says: the vector grades `FAIL`, exit 1, no schema change. **That measurement reproduces exactly.**

`T360` declined to apply it on reasoning alone. `T387` then ran the same patch against **both** a
correct and a deliberately wrong implementation:

| implementation | candidate vector | ledger parity | exit |
|---|---|---|---|
| `ledger-go` (**CORRECT**) | FAIL | PASS 7 **FAIL 1** | **1** |
| `ledger-wrong-residue-rounding` (**WRONG**) | **PASS** | PASS 8 FAIL 0 | **0** |

The wrong port passes and **greens the bar**, matching an `amount_minor` of `10013` that neither
system ever produced, and inflating money cells 39 → 43. The correct port reddens it.

**This is the whole lesson, and it is why `T359` was not careless:** verifying that a fix makes the
failing case fail is *not* verifying that it grades correctly. From one implementation the two are
**indistinguishable** — the signal is identical from that side. `T359` ran one implementation and
got a true measurement of a backwards fix.

Two corollaries, found by `T387` and named by neither `T359` nor `T360`: a remedy that leaves the
correct implementation at a permanent baseline `FAIL 1` makes any `kills >= 1` criterion **vacuous**;
and a diff appended **unconditionally** means no vector shape can ever be green, so the gate it
serves could only ever be a permanently red bar.

## What still stands

**The diagnosis stands. Only the patch is condemned.** `T359`'s underlying finding — that the port's
residue refusal surfaces as a `HARNESS-ERROR` rather than something gradeable — is real and remains
open under `G-19`. A future fix must be driven against **at least one correct and one deliberately
wrong implementation**, with the correct one passing and the wrong one dying.

## Provenance

- Pattern: `P-100` in `.softhouse/patterns.md` (filed by `T398`, reviewed by `T414`).
- Adjudication: `.softhouse/reviews/t387-review-t360/REVIEW.md` §1.2.
- Original measurement: `REVIEW.md` in this directory, finding `F-T359-1`.
- `G-19` is recorded OPEN in `.softhouse/program.json` and `.softhouse/gates.md`.
