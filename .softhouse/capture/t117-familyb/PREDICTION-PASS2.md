# T117 PASS 2 — REGISTERED PREDICTION: how far up in principal does family B go?

**Registered BEFORE the pass-2 probe ran**, in a commit that is a strict ancestor of any pass-2
observation. Pass 1's observations are already committed (`f1ed3c4`) and are the *input* to this
prediction; nothing about pass 2's own cells is known when this is written.

## Why pass 2 exists

Pass 1's registered prediction said the failing principal could not exceed one minor unit, and
**that was refuted**: family B was observed at **B = 3** (MNT 0.03) and **B = 5** (MNT 0.05).

So the pass-1 answer to T117's question (ii) is *yes, it exceeds one minor unit* — but pass 1
establishes **no upper bound whatever**. B = 5 is simply the largest principal the brief asked it to
try. `gates.md` currently tells Buyan that family B is a **one-rate, one-principal** phenomenon at
MNT 0.01; that sentence is now wrong, and the sentence that replaces it needs a magnitude. Pass 2
supplies the measurement for that magnitude, and **decides nothing about the gate** — G-8's options
(b) and (c) amend the graded domain and are a hard `user` gate; option (a) is T116's.

## What pass 1 observed that this prediction rests on

All from the committed pass-1 capture, re-derived in integer minor units / `fractions.Fraction`:

1. **122 of 122 family-B cells** have `B·r` a **half-integer** number of minor units. At 600.0 %
   p.a. the monthly rate `r = 1/2` exactly, so this condition is exactly **"B is odd"**.
2. **Zero** family-B cells have `B·r` an integer (B even).
3. The condition is **necessary but not sufficient**: **62 of the 80 non-family-B cells also have
   odd B**. Which terms fall in a family-B band varies with B — B = 3 failed at
   n ∈ {108, 121, 150, 250, 1000} and was clean at {104, 300, 500}; B = 5 failed at
   {104, 108, 121, 150, 250, 1000} and was clean at {300, 500}.
4. On every family-B cell, every intermediate row's `total` equals **`floor(B·r)`** — the
   half-minor-unit tie is emitted **downward**; on the clean odd-B cells it is `ceil(B·r)`.

This is a **description of emitted values**, not a mechanism. Family B's cause remains
`[UNVERIFIED]`, pass 2 does not look for it, and no sentence below should be read as locating it.

## What pass 2 asks — 87 probe cases + the 2 standing rig calibrations

| leg | cells | what |
|---|---|---|
| **OL** | 65 | odd ladder **B ∈ {7, 9, 11, 21, 51, 101, 501, 1001, 10001, 100001, 1000001, 100000001, 120000001}** × n ∈ {108, 121, 150, 250, 1000} — the five terms at which **both** B = 3 and B = 5 were family B in pass 1. The top of the ladder is **MNT 1,200,000.01**: the program's standard ordinary-loan control amount plus one minor unit. |
| **BC** | 12 | contiguous **B = 6…20 at n = 150** (the three already in OL at that term are not duplicated), so the odd/even structure is visible directly rather than inferred. |
| **EC** | 8 | even control **B ∈ {100, 1000, 10000, 100000}** × n ∈ {150, 250}. |
| **RP** | 2 | pass-1 cells re-asked under new tenant ids: (B = 5, n = 104) family B, and (B = 3, n = 300) clean. |

Largest principal asked: **120,000,001 minor units = MNT 1,200,000.01.**

## THE PREDICTIONS

### Q1 — family B reaches every odd B in the ladder. **Confidence: HIGH up to B = 101, MODERATE above it.**

At least one of the five terms is family B for **each** of the 13 odd principals, including
B = 120,000,001 (MNT 1,200,000.01). The relative correction `(2/3)^n` that separates `B·a(r,n)` from
its limit `B·r` does not depend on B, and the ulp of `B·r` scales with B, so the tie condition
should not weaken as B grows. **Registered as `predictedFamily: "B"` on all 65 OL cells** — a
deliberately aggressive per-cell call, since pass 1 proved oddness is not sufficient per cell. I
expect some OL cells to be clean; the prediction that matters is the **per-B** one.

*Falsified by*: any odd B in the ladder that is clean at all five terms.

### Q2 — the largest failing principal will be MNT 1,200,000.01. **Confidence: moderate.**

i.e. the top of the ladder itself, not something below it. If Q1 holds this follows.

*Falsified by*: the largest family-B principal being anything other than 120,000,001 minor units.

### Q3 — every EVEN B is clean at every n asked. **Confidence: HIGH.**

All 8 EC cells and all 7 even BC cells (B = 6, 8, 10, 12, 14, 16, 18, 20) are clean.

*Falsified by*: any even-B cell that is family B.

### Q4 — strict odd/even alternation on the contiguous BC run at n = 150. **Confidence: high.**

B = 7, 9, 11, 13, 15, 17, 19 family B; B = 6, 8, 10, 12, 14, 16, 18, 20 clean. (B = 7, 9, 11 at
n = 150 are carried by OL, not duplicated in BC.)

*Falsified by*: any break in the alternation at n = 150.

### Q5 — the family-B row shape generalises. **Confidence: high.**

On every pass-2 family-B cell: the REPAYMENT `principal` column sums to `0`,
`totalPrincipalAmount` is `0.00`, the final `balance` equals the disbursement, and every
intermediate row's `total` equals `floor(B·r)` = `(B−1)/2` minor units.

*Falsified by*: any family-B cell that deviates.

### Q6 — the RP leg reproduces pass 1. **Confidence: high.**

`T117P2-R600p0-N104-B5` byte-identical in its `observed` block to pass 1's
`T117-BS-R600p0-N104-B5`, and `T117P2-R600p0-N300-B3` to `T117-BS-R600p0-N300-B3`, under disjoint
tenant ids.

## What pass 2 CANNOT establish, whatever it returns

- **Nothing at any rate but 600.0 %.** The odd/even structure is a statement about `r = 1/2`. At
  another rate the half-integer condition picks out a different residue class of B, and pass 1's
  own record shows the condition is not sufficient. **No sentence in the handoff may generalise
  this to another rate**, and in particular T84's 41 clean cells at 300.0 % / B = 2 are consistent
  with either outcome here.
- **Nothing above B = 120,000,001** and nothing between the ladder rungs; nothing above n = 1000;
  nothing at terms other than the five asked, per B.
- **Nothing about family B's cause.** Still `[UNVERIFIED]`.
- **Nothing about how the Go port behaves** on these cells. Pass 1 and pass 2 measure the reference
  oracle only. `gates.md` records 0 port/oracle divergence on the family-B cells *measured so far*;
  whether that holds at these principals is **not measured here** and must not be assumed.
- **Nothing about G-8's disposition.** T117 decides none of its options, recommends none, and
  pre-implements none.

One framing note, so the magnitude is not over-read: the implausible input in these cells is the
**rate**, 600.0 % p.a., not the amount. Pass 2 measures how large the *amount* can be at that rate;
it says nothing about whether any rate a Mongolian NBFI would actually offer reaches the region.
