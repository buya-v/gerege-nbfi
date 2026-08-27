# T117 — REGISTERED PREDICTION, gate G-8, family B's extent

**Registered BEFORE the probe ran.** This file and `prediction.json` are committed in a **strict
ancestor** of the commit that carries any observation. If you are reading this in the same commit as
a capture, the registration is void and nothing below may be treated as a prediction.

Task **T117**. The probe T101 suggested and T112 carried forward as its follow-up 5.
Reference oracle: Fineract, pinned commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`, image
`sha256:e596339626bf…0459a`, Path A embeddable seam, `(19, HALF_UP)`, MNT dp 2.
("Oracle" here is the Fineract reference implementation. Oracle Database is a prohibited product
and appears nowhere in this probe, which opens no database connection at all.)

---

## 0. Which family is which — checked against `gates.md` before writing a word

The A/B attribution has been stated backwards in this program three times, so it is restated here
from the discriminator tables in `.softhouse/gates.md` § *"Read this first: G-8 is TWO phenomena"*:

- **FAMILY A** — the REPAYMENT rows' `principal` column **sums to the disbursed amount**; the
  outstanding-balance column is stale; the Go port **diverges on exactly ONE cell per case** (final
  row `outstanding_principal_minor`, e.g. expected 109 got 0). Measured at 11 of the 12 rates swept,
  **never at 600.0 %**.
- **FAMILY B** — the `principal` column **does not sum** (it sums to `0.00` against a `0.01`
  disbursement); `totalPrincipalAmount` is `0.00`; the last row carries `interest 0.01`; forcing the
  balance memo to recompute does not move it; **the Go port reproduces it cell for cell, 0 diffs**.
  Measured only at **600.0 % / MNT 0.01 / n ≥ 104**, 29 cells.

This probe is about **family B**.

## 1. What is being asked, and why these cells

**(i) half-line in n, or bounded island?** Every family-B cell ever measured lies at
n ∈ {104…122} ∪ {150, 200, 250}; **nothing above n = 250 has ever been asked at this shape**
[`gates.md`, *"What is NOT known about family B"*]. Leg **NC** asks n = 300…400 **contiguously**
(101 cells), leg **NL** asks a ladder n = 410, 420, …, 1000 (60 cells), and leg **NT** asks
n = 995…999 **contiguously** (5 cells) so that contiguity is tested at the **top** of the range as
well as at the bottom.

**(ii) can the failing principal exceed ONE MINOR UNIT?** Every family-B cell ever measured is at
**B = 1 minor unit**. Leg **BS** asks **B = 2, 3, 4, 5** minor units at
n ∈ {104, 108, 121, 150, 250, 300, 500, 1000} — 32 cells spanning the whole known family-B region
and the new range above it.

Plus leg **CTRL**: n = 103 (measured clean by T84) and n = 250 (measured family B by T100), re-asked
under new tenant ids, so the probe carries its own reproduction of both sides of the known boundary.
Plus the rig's two standing calibrations `P-CAL-ZPA` / `P-CAL-ZPB`, which must reproduce pass 3g's
`T64-ZP-A` / `T64-ZP-B` cell for cell or the run is refused.

**200 probe cases + 2 calibrations = 202.** The exact id list, in emission order, is
`prediction.json`; the scramble is `random.Random(20260821).shuffle` over the leg-ordered list.

## 2. The reasoning the prediction rests on — exact rational arithmetic, no float

T83's closed form (a **hypothesis**, already falsified on family B, but the right coordinate to
think in): the cell's EMI quantizes to zero when `B · a(r, n) < ½` in **minor units**, where
`a(r, n) = r / (1 − (1+r)^−n)` and `r = annual/100/12`.

At **600.0 % p.a., `r = 1/2` exactly**, so `(1+r)^−n = (2/3)^n` and

```
B · a(1/2, n)  =  (B/2) / (1 − (2/3)^n)   →   B/2   as n → ∞, from ABOVE.
```

Computed in `fractions.Fraction` by `src/threshold_exact.py`
(`out/threshold-exact.json`, committed with this prediction):

| B (minor) | `B·a − ½` at n = 104 | at n = 300 | at n = 1000 | distance from the ½ threshold |
|---|---|---|---|---|
| **1** | `+2.4292883e-19` | `+7.4403315e-54` | `+4.0523873e-177` | **razor's edge** — converges to ½ exactly |
| 2 | `+0.5` | `+0.5` | `+0.5` | a **whole minor unit** above ½ |
| 3 | `+1.0` | `+1.0` | `+1.0` | — |
| 4 | `+1.5` | `+1.5` | `+1.5` | — |
| 5 | `+2.0` | `+2.0` | `+2.0` | — |

(The `+2.429e-19` at B = 1, n = 104 reproduces T122's committed exact figure for that cell, which is
this script's own calibration against the record.)

**B = 1 at 600.0 % is the only principal in the whole rate column whose `B·a` converges to exactly
½.** That is the coincidence family B sits on. For B ≥ 2 the quantity is not near the threshold at
all — it is a full minor unit or more above it, and it does not move with n.

Two facts from the committed corpus that this reasoning must not contradict, and does not:

- **B = 2 at 600.0 % is already measured CLEAN** at n ∈ {60, 90, 108, 120, 150, 200} — six cells in
  `capture-t84-raw.json.gz`, `totalPrincipalAmount 0.02`, final balance `0.00`
  [VERIFIED: read from the committed `.gz`, integer minor units, this fire].
- **B = 1 at 600.0 % is clean for n ≤ 103 and family B for 104 ≤ n ≤ 250**, and the exact gap
  `B·a − ½` is **strictly positive and strictly decreasing** across that range. Nothing about the
  quantity turns around above n = 250.

## 3. THE PREDICTIONS

### P1 — (i) family B is a HALF-LINE in n, not a bounded island. **Confidence: high.**

All **166** B = 1 cells at n ∈ [300, 1000] (legs NC + NL + NT) come back **family B**: the REPAYMENT
`principal` column sums to `0.00` against a `0.01` disbursement, `totalPrincipalAmount` is `0.00`,
the final row's `balance` is `0.01`. **Zero clean cells, zero family-A cells, zero errors.**

*Falsified by*: any single B = 1 cell at n ≥ 300 that is clean, or family A, or errors.

### P2 — (ii) the failing principal CANNOT exceed one minor unit at 600.0 %. **Confidence: high.**

**None of the 32 B ∈ {2,3,4,5} cells is family B.** Every one has a REPAYMENT `principal` column
summing exactly to its disbursement (2, 3, 4 or 5 minor units), and `totalPrincipalAmount` equal to
that disbursement.

*Falsified by*: any B ≥ 2 cell whose REPAYMENT principal column does not sum to its disbursement.

### P3 — the B ≥ 2 cells are CLEAN, not family A. **Confidence: MODERATE — registered as the weak one.**

All 32 B ∈ {2,3,4,5} cells have final `balance` `0.00`. This is the prediction I expect to be wrong
if any is: B = 3, 4 and 5 have **never** been asked at 600.0 % at any n, family A is a memo-staleness
phenomenon whose trigger is only partly understood, and family A has never been observed at 600.0 %
— which is itself a fact about a rate column that was only ever asked at B ∈ {1, 2}. A family-A cell
here would be a **new** fact (family A at 600.0 %) and would not touch P1 or P2.

### P4 — the exact row shape of a family-B cell at n ≥ 300. **Confidence: high.**

Every B = 1, n ≥ 300 cell: `totalPrincipalAmount` `"0.00"`, `totalInterestAmount` `"0.01"`,
`totalRepaymentAmount` `"0.01"`, `totalOutstandingAmount` `"0"` (scale 0, per the known
`BigDecimal.ZERO` passthrough); REPAYMENT rows 1…n−1 each carry `principal "0.00"`,
`interest "0.00"`, `total "0.00"`, `balance "0.01"`, `totalOutstandingBalance "0.01"`; row n carries
`interest "0.01"`, `total "0.01"`, `balance "0.01"`, `totalOutstandingBalance "0.00"`.

*Falsified by*: any deviation in any of those cells. This is the sharpest of the four and the
cheapest to refute.

### P5 — the CTRL leg reproduces the committed corpus. **Confidence: high.**

`T117-CTRL-R600p0-N103-B1` is clean (`totalPrincipalAmount "0.01"`, `totalInterestAmount "0.13"`,
final balance `"0.00"`); `T117-CTRL-R600p0-N250-B1` is family B. Both under tenant ids
(`t117_ctrl_*`) disjoint from T84's and T100's.

### P6 — the number that matters, stated plainly. **Confidence: high.**

**The largest failing principal observed anywhere in this probe is 1 minor unit (MNT 0.01).**
Family B stays confined to sub-minor-unit dust across the entire probe.

*Falsified by*: any family-B cell with a disbursement above 1 minor unit.

## 4. What this probe CANNOT establish, whatever it returns

Stated in advance so it cannot be quietly dropped afterwards (P-26).

- **Nothing above n = 1000**, and no half-line claim is a proof — 166 observed cells are 166 observed
  cells. "Half-line" below means "no upper edge was found where one was looked for".
- **Nothing between the NL rungs.** n = 411…419, 421…429, … are **not asked**. Contiguity is
  established only on 300…400 and 995…999.
- **Nothing at B > 5**, nothing at a non-integer-minor principal, nothing at any rate but 600.0 %.
- **Nothing about family B's CAUSE.** Still `[UNVERIFIED]`, and this probe does not look for it.
- **Nothing about `MinorUnitDigits ≠ 2`, Path B / REST, charges, holidays, or down payments.**
- **Nothing about gate G-8's disposition.** Options (b) and (c) amend the graded domain and are a
  hard `user` gate; option (a) is T116's. T117 decides none of them, recommends none of them, and
  pre-implements none of them.

## 5. Discipline this probe binds itself to

- Money is **integer minor units or `fractions.Fraction`/`Decimal`** in every script, including the
  ones that only *count* (P-25). `json.load` is called with `parse_float=Decimal` wherever a capture
  is read, or the money is read from JSON **strings** and split on `.` into integers.
- **Every skip is counted and named** (P-40). The postcheck refuses the run unless the emitted id
  list equals `/tmp/t117-ids.json` exactly, in order; the analysis reports
  `asked / observed / errored / missing` for every leg.
- No existing script that produced committed evidence is edited; the harness is derived
  **mechanically** from the committed `CaptureT100.java` (T114's standing ruling).
- No vector is added, no `PIN.json` / `capabilities.json` / `contract.go` / DEC-n is touched, and
  `gofmt -w` is never run.
