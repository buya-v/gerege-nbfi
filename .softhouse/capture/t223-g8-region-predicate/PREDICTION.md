# T223 — registered prediction, gate G-8: **the region as a PREDICATE, not as a rate and a term**

**Registered BEFORE any observation exists.** This file, `prediction.json` and everything under
`src/` are committed in a commit that is a **strict ancestor** of the commit carrying
`out/capture-t223-raw.json`. If that ancestry does not hold, this prediction is worthless and must
be treated as such (P-9).

The oracle is the **Fineract reference implementation** at pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, Path A embeddable seam, `(19, HALF_UP)`, MNT dp 2, in a
throw-away `docker run --rm` from the pinned image. No server is started and no database connection
is opened. *Oracle Database is a prohibited product in this program and appears nowhere in this
work.*

---

## 1. What T220 established, re-verified BY CONTENT here (not by line number)

Both sites still carry the quoted text at the quoted line at the pinned commit — re-opened by T223,
not copied from the brief:

| site | line | text found there |
|---|---|---|
| `ProgressiveEMICalculator.java` | **1962** | `.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());//` |
| `RepaymentPeriod.java` | **217** | `return interestPeriods.stream().map(InterestPeriod::getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add);` |

`:1962` occurs **twice** in that file — also at **`:1979`**, in `rateFactorByRepaymentPartialPeriod`.
G-1's record already names both. The G-8 shape reaches `:1962` (via
`rateFactorByRepaymentEveryMonth`, `:1925`), not `:1979`.  **[VERIFIED]**

## 2. A THIRD load-bearing site, which T220's note does not contain

`ProgressiveEMICalculator.checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (**`:1258-1308`**)
with `EmiAdjustment.shouldBeAdjusted()` / `adjustment()`
(`fineract-progressive-loan/.../calc/data/EmiAdjustment.java`). It re-runs up to **three** times and
**raises the instalment** when the residual carried to the final row is large relative to the
instalment. It is the only reason a cell whose instalment is at or below the first period's interest
can still amortize. **A predicate built on `:1962` + `:217` alone is wrong, and this file says so
before measuring anything.**  **[VERIFIED by reading the source at the pinned commit]**

## 3. THE PREDICATE

For the G-8 shape only — MONTHS / `repaymentEvery` 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360 /
single disbursement on the schedule start date 2024-01-01 / no down payment / no charges / both
multiples-of null / `(19, HALF_UP)` / `minorUnitDigits = 2` — define, in **integer minor units**:

- `r`  = the oracle's period-1 rate factor, computed through `:1962` (19 **decimal places**);
- `I₁` = `B_minor · r`, the **exact** first-period interest, as a `Fraction` — never rounded;
- `E_q` = the oracle's instalment, emulated digit-for-digit through `:1962` + `:217` +
  `:1816-1820` + `:1822-1828` + `:1838-1841`, then quantized to 2 places HALF_UP by `Money(..)`
  (`Money.java:40-53`). `src/emi_mechanism.py` is that emulation.

Then:

```
E_q >  I₁                       -> NOT family B   (every period leaves E_q - I₁ > 0 for principal)
E_q == I₁                       -> NOT family B   (no interest deficit accrues, so the final-row
                                                   residual is applied as PRINCIPAL)
E_q <  I₁                       -> FAMILY B, unless site 3 rescues it, which needs BOTH
                                     B_minor > floor(n/2)        (shouldBeAdjusted)
                                     2·B_minor >= n              (adjustment >= 1 minor unit)
```

### Why this is a derivation and not a curve fit

Exact annuity arithmetic gives `E_exact = I₁ / (1 − (1+r)^−n)`, so `E_exact > I₁` **strictly, for
every n**, by `I₁·(1+r)^−n/(1−(1+r)^−n)`. That excess decays **geometrically in n**. Family B is
what happens when the excess falls inside the resolution of the oracle's own 19-significant-digit
arithmetic and the computed instalment lands at or below `I₁`. Hence, in the phenomenon's own
variables:

- **the term enters only through `(1+r)^n` vs `10^19`** — the boundary term scales as
  `n* ≈ 19 / log₁₀(1+r)`, i.e. it is a property of the **RATE**, not of the principal;
- **the principal enters twice, and neither time as a magnitude**: once through **resonance**
  (`I₁` must sit on a quantization boundary — for `r = 1/2` that is exactly "`B_minor` odd", which
  is why all 20 family-B principals ever observed are odd), and once through the **site-3 rescue
  threshold `B_minor ≲ n/2`**, which puts a **ceiling** on the failing principal that does not
  depend on the rate at all.

`n* ≈ 19 / log₁₀(1+r)` evaluated at the rates this program has swept:
600 % → 108 · 300 % → 196 · 96 % → 568 · 48 % → 970 · 36 % → 1480 · 21.6 % → 2452 · 7 % → 7519.
**The sign and size of the accumulated error decide the last few periods, so `n*` is an ORDER, not
the boundary**; the emulator gives the boundary.

## 4. FALSIFIABLE CELL PREDICTIONS — every one on ground NOBODY HAS SWEPT

No rate other than **600.0 %** has ever been asked above `n = 600`; **300.0 %** has never been asked
above `n = 260`; **36.0 %** has never been asked above `n = 600`. Every cell below is therefore new.

| id | rate % | n | B (minor) | `E_q` predicted | `I₁` exact | **predicted** |
|---|---|---|---|---|---|---|
| `T223-R36p0-N1323-B50`  | 36.0  | 1323 | 50  | **2** | 3/2   | **NOT family B** |
| `T223-R36p0-N1324-B50`  | 36.0  | 1324 | 50  | **1** | 3/2   | **FAMILY B** — the boundary |
| `T223-R36p0-N1500-B50`  | 36.0  | 1500 | 50  | **1** | 3/2   | **FAMILY B** |
| `T223-R300p0-N500-B2`   | 300.0 | 500  | 2   | **1** | 1/2   | **NOT family B** |
| `T223-R300p0-N800-B2`   | 300.0 | 800  | 2   | **0** | 1/2   | **FAMILY B** |
| `T223-R300p0-N1200-B2`  | 300.0 | 1200 | 2   | **1** | 1/2   | **NOT family B** — non-monotone in n |
| `T223-R21p6-N3000-B250` | 21.6  | 3000 | 250 | **5** | 9/2   | **NOT family B** |

`T223-R36p0-N1324-B50` is the one that matters: **MNT 0.50 at 36.0 % p.a. — an ordinary Mongolian
NBFI consumer rate — predicted to produce a schedule that never repays a single minor unit.** Every
family-B cell in the record is at 600.0 %. If this reproduces, "family B is a 600 % phenomenon" is
dead.

`T223-R300p0-N800-B2` together with `N500` and `N1200` is the **band structure** T117 observed,
predicted in advance rather than described afterwards: family B is **not** a half-line in `n`.

### Also predicted, and stated so it can fail

- **P1** — every case emits exactly `n` REPAYMENT rows plus one DISBURSEMENT row.
- **P2** — on each predicted FAMILY B cell the REPAYMENT `principal` column sums to **0** minor
  units, `totalPrincipalAmount` reads `0.00`, and the `balance` column is constant at the disbursed
  amount.
- **P3** — on each predicted NOT-family-B cell the REPAYMENT `principal` column sums **exactly** to
  the disbursed amount.
- **P4 — an existence claim, so an empty measurement REFUTES rather than passes through** (T114's
  ruling): at least one probe cell is family B and at least one is not.
- **P5** — the rig calibrations `P-CAL-ZPA` / `P-CAL-ZPB` reproduce the already-promoted
  `T64-ZP-A` / `T64-ZP-B` cell for cell with zero input differences. If they do not, nothing else in
  this capture is admissible.

## 5. What this prediction does NOT claim

- **Nothing about the PARTIAL family-B shape.** The predicate is scoped to the FULL shape and is not
  evidence about the partial one either way.
- **Nothing about the THIRD OUTCOME.** A `StackOverflowError` is recorded as an observation, with the
  attempt count, and is never retried until it agrees.
- **Nothing about the Go port.** T223 grades no port and promotes no vector.
- **It is already known to be incomplete.** Validated against the 1,038 observed cells of the eight
  committed raw captures *before* this file was written, the emulated instalment `E_q` reproduces the
  oracle's period-1 instalment on **971 of 1,035** comparable cells; the **64** misses are all cells
  where site 3 raised the instalment. And the classification rule above **fails on at least one
  committed cell it should get right — `T159-R600p0-N1000-B801`**, where site 3's threshold says
  "rescued" and the oracle emitted family B. That discrepancy is recorded here, in advance, as an
  open defect of this predicate rather than discovered afterwards.
