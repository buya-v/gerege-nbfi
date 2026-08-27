# T277 — shape-law salvage from the rejected `T241` branch

## What this directory is

A **re-runnable instrument**, not a transcribed table. `A guard that only works when someone
remembers to run it enforces nothing` is this program's most repeated lesson; the figures below are
**pinned inside the instrument** and it exits non-zero the moment any of them moves.

```bash
# 1. prove the arithmetic primitives before believing any census
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py --selftest

# 2. the census itself, both scopes, human-readable   (exit 0 == every pin reproduced)
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py . --report

# 3. the same thing as JSON, with every row
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py .

# 4. the seven counterexample cells, row by row, from the raw schedules
python3 .softhouse/capture/t277-shapelaw-salvage/src/dump_seven_t277.py .
```

Run from the repository root. Nothing here contacts the reference oracle, reads
`.softhouse/vectors/`, or touches `.softhouse/conformance.sh`.

## What it establishes

`.softhouse/gates.md`, under `## G-8 …` → `### THE LAW`, states the shape of an unrescued cell as
two laws. **Law (i) `last row EMI = E + B` holds. Law (ii) `TOTAL PRINCIPAL = max(0, B_minor − n·δ)`
is FALSE on seven cells** — every one FACT-A-true, every one at `δ = 1`, every one satisfying the
block's own `FULL family B` antecedent and therefore predicted to repay exactly zero, and every one
repaying a positive amount. The full finding, with the salvage/refutation split against the rejected
`T241` branch `df0aed2c`, is written up in `gates.md` under `#### CORRECTION (T277)`.

## Independence

The census imports **none** of: `t229-g8-site3/src/site3.py`, `t229-g8-site3/src/validate_corpus.py`,
`t229-g8-site3/src/emi_mechanism_t223.py`, the cloud branch's `rederive_total_interest_t241.py`, or
`T264`'s scripts. It reads only the committed raw `.json.gz` captures (STANDING RULE 5) and derives
every figure itself.

## Arithmetic discipline

**Integer minor units only.** Money strings are parsed to integers by string manipulation; rates are
carried as exact integer numerator/denominator pairs; `HALF_UP` is implemented on integers. The
`--selftest` arm proves the parser, the quantizer and the rate factor on hand-checked cases, and then
asserts **at AST level** that the file contains no float literal, no `float()`/`round()` call, no
true-division node, and no `decimal` / `fractions` / `math` import.

Two further self-imposed refusals:

- **Completeness.** `census()` raises rather than returning if `admitted + rejected != captures read`,
  so no capture can fall out of a branch and silently shrink the population.
- **Rate-factor exactness.** A cell whose monthly rate factor has no finite decimal expansion inside
  19 fractional digits is **excluded and counted**, never admitted — the oracle computes that factor
  at `(19, HALF_UP)` and `setScale(19)`, and this instrument cannot reproduce its `I₁q`. Exactly one
  cell is excluded on that ground: `T84-RP-R7p0-N56-B23` at 7.0 % p.a.

## Files

| file | what it is |
|---|---|
| `src/shapelaw_census_t277.py` | the census and the guard; all pins live here |
| `src/dump_seven_t277.py` | row-level dump of the seven counterexamples from the raw schedules |
| `evidence/00-selftest.txt` | the primitive self-test and AST attestation |
| `evidence/10-census-report.txt` | both scopes, every pin, the exception set — exit 0 |
| `evidence/20-seven-cells-raw-rows.txt` | the seven, principal column by principal column |
| `evidence/30-census.json` | the full machine-readable census, all 578 admitted rows |
| `evidence/40-negative-calibration.txt` | two deliberate mutations, both trip the guard, exit 1 |

## Two scopes, and why there are two

`t229corpus` — the **296** cells T229 actually measured and the cloud's T241 actually re-bucketed.
That is **not** "the corpus": it is the four raw captures that existed under `.softhouse/capture/`
when T229 ran (`T117`, `T117-p2`, `T159`, `T223`). Nothing in `gates.md`, in T229, or in either T241
says so, and the figure cannot be reproduced without knowing it. Pinned here explicitly. Its pins
come from figures **published before this instrument existed**, so reproducing them is independent
confirmation.

`all` — every committed raw capture in the repository today: **578** admitted stuck cells from 775
captures across 10 files. Its pins were taken from **this instrument's own first run**; no prior
document states them, so they are **regression pins, not independent confirmation**. Their value is
that **the law-(ii) exception set is still exactly the same seven** on a population 95 % larger.
