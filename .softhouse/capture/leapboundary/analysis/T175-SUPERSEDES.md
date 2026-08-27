# T175 — the invariant and worst-delta legs of `t55-analyse.py` are SUPERSEDED by `t55-invariants-v2.py`

## Which one is authoritative

| file | status |
|---|---|
| `t55-invariants-v2.py` | **AUTHORITATIVE for invariant I6 and for the worst-money-delta figure.** |
| `t55-analyse.py` | **RETAINED, BYTE-IDENTICAL.** Still authoritative for the discrimination table, the branch re-derivation, the gradeability table, the T48 anchor and the exact-text sidecars — none of which T175 touched. Its **I6 verdict and its `max minor u` column are superseded.** |
| `T55-ANALYSIS.txt` | **RETAINED, BYTE-IDENTICAL.** True about the run it records. |

The successor **imports the original by path** and reuses its `load`, `cells`, `MONEYISH`,
`SHAPES` and `PAIRS`. It does not fork a second copy of them — two copies of a claim is one
claim and one time bomb (P-27).

## Why the original is retained rather than fixed

It produced committed evidence (`T55-ANALYSIS.txt`, and the `out/*-exact.json` sidecars every
later comparison reads), and under T114's ruling committed evidence is not edited in place.

sha256 of the original, recorded before and after all T175 work, unchanged:

    abf4494a4ce9147419021ca83fe91c6818717ff747fdf127cee1bfef826dfe05  t55-analyse.py

## The defects — two, in the same file

**`t55-analyse.py:350-353`**, inside invariant I6, *"every money cell is at most 2 dp (MNT
minor unit)"*:

            try:
                exp = -Decimal(v).as_tuple().exponent
            except Exception:
                continue

A money cell whose text will not parse as a `Decimal` is dropped and **I6 passes without it**.
Nothing is printed and nothing is counted. With every cell unparseable, I6 reports `ok` over an
empty denominator — a vacuous pass on the first non-negotiable in `CLAUDE.md`.

**`t55-analyse.py:163-168`**, inside `diff()`, computing the worst money delta of a pair:

                try:
                    delta = abs((Decimal(av) - Decimal(bv)) / MINOR)
                    if delta > worst:
                        worst, worst_cell = delta, k
                except Exception:
                    pass

A cell whose delta cannot be computed can never become the worst, so the published
`max minor u` column silently **understates**.

## How much of the money surface the first defect actually hides

`T175-red/field-census.py` enumerates it instead of assuming it (transcript:
`T175-red/field-census-output.txt`). For capture `LB-LEAPIN-p7`, planting the unparseable
three-decimal-place value `"1,200,000.000"` in every MONEYISH cell in turn — 32 plants:

* **24 are SWALLOWED SILENTLY**, I6 = `ok`, on a value that is a real breach;
* **8 crash loudly** because an *unguarded* `Decimal()` in I1/I2/I3/I5/I7 reaches them first;
* **0 are reported by I6.**

The swallowed 24 include `plan.totalRepaymentExpected`, `plan.totalPrincipalDisbursed`,
`plan.totalPrincipalExpected`, `plan.totalFeeChargesCharged` and
`plan.totalPenaltyChargesCharged` — plan-level totals a reader would quote. Note also that the
**disbursement row** is
split out at `t55-analyse.py:312-316` and I1/I3/I5/I7 never iterate it, while `cells()` keeps
it as `row0`: for that row, `:352` is the only money check there is.

This census also **refuted the first draft of the red probe**, which planted in
`totalInterestCharged` and got a crash rather than a swallow, because I5 reads that field
unguarded at `:342`. The defect is real; the field you pick decides whether you can see it.

## What the successor changes, and nothing else

1. **Skip register.** Every swallowed item is named — capture id, cell key, exact raw text,
   exception type and message — and counted. Printed on every run, including a clean one.
2. **Unparseable is a VIOLATION, not a skip.** A money cell whose text is not an exact decimal
   breaches the non-negotiable as surely as one with three decimal places, and a non-zero
   swallow count fails the run.
3. **Zero inspected is an ERROR (P-35).** The I6 denominator and the money-delta denominator
   are asserted non-zero **and printed**, per capture and in total.
4. **`cells()`'s own silent narrowing is measured.** `cells()` keeps only `str`/`bool` leaves,
   so a JSON null, a bare number or a nested object is dropped before I6 ever runs — a second,
   structurally different way for the denominator to shrink invisibly. Reported as
   `MONEYISH leaves dropped by cells() before I6`.
5. **I1–I5 and I7 are still run from the original, unmodified**, so a violation elsewhere is
   still surfaced. Only the original's I6 verdict is ignored.

`decimal.Decimal` only, from exact decimal text, deltas in integer minor units. No float
anywhere, including intermediates (P-25).

## What it reports on the committed corpus

    captures loaded            : 33 of 33 requested
    money cells I6 INSPECTED   : 1236
    money cells I6 SWALLOWED   : 0
    MONEYISH leaves dropped by cells() before I6: 0
    money deltas CONSIDERED    : 212
    money deltas SWALLOWED     : 0
    T175 SUCCESSOR: PASS

and every `max minor u` figure reproduces `T55-ANALYSIS.txt` exactly (97 / 8783 / 2911 / 3105 /
41328 / 17783). The committed I6 claim and the committed magnitudes are **still supported** —
now measured rather than assumed.

## Driven red

`T175-red/drive-red.sh` (run with **bash**), transcript at `T175-red/drive-red-output.txt`,
exits 0 with all legs as predicted:

* **A** original vs the clean corpus → I6 `ok` (baseline).
* **B** original vs a *parseable* 3-dp plant → I6 **VIOLATED**. The original is not simply
  broken; it catches what it can parse. That is what makes leg C damning.
* **C** original vs the *unparseable* 3-dp plant → I6 **`ok`**, and all seven invariants `ok`.
  **The defect, demonstrated.**
* **D** successor vs the same plant → exit 1, names `plan.totalRepaymentExpected` and the
  literal text `1,200,000.000`; skip register shows 3 items = 1 × I6 + 2 × worst-delta (the
  `:167` site firing on the same input — the probe's own prediction of "1" was corrected to
  "3" on measurement, and the correction is recorded in the probe).
* **E** (the other half, P-50) successor vs the clean corpus → exit 0, 1236 cells inspected.
* **F** successor vs an empty corpus → exit 1, "ZERO captures loaded", "I6 is VACUOUS".

The wrapper also sha256s `t55-analyse.py` before and after and asserts byte-identity.

## Reproduce

    bash    .softhouse/capture/leapboundary/analysis/T175-red/drive-red.sh
    python3 .softhouse/capture/leapboundary/analysis/T175-red/field-census.py
    python3 .softhouse/capture/leapboundary/analysis/t55-invariants-v2.py
