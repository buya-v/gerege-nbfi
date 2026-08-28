# T277 — shape-law salvage from the rejected `T241` branch

## What this directory is

A **re-runnable instrument**, not a transcribed table. `A guard that only works when someone
remembers to run it enforces nothing` is this program's most repeated lesson; the figures below are
**pinned inside the instrument** and it exits non-zero the moment any of them moves.

**One command runs all of it, positives AND negatives, and exits non-zero if any of them misbehaves:**

```bash
bash .softhouse/capture/t277-shapelaw-salvage/src/verify_t277.sh
```

It runs both instruments' self-tests, both censuses, the seven-cell dump, and **four deliberate
mutations that MUST trip** — including the cloud `T241`'s exact claim that law (ii) holds 220/220.
It contacts no oracle, reads no vector, and writes nothing inside the repository: mutants are built
in a scratch directory and deleted. **It is itself calibrated** — see
`evidence/71-verifier-meta-calibration.txt`, where a negative case repointed at a command that cannot
fail is caught as `DID NOT TRIP`, and a mutation whose anchor has moved makes the run `ABORT` rather
than score a trip it did not earn. *(A mutant that fails to build would otherwise make its case
"trip" for the wrong reason — a false green, and the same failure this whole task exists to correct.)*

The individual steps, if you want them one at a time:

```bash
# 1. prove the arithmetic primitives before believing any census
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py --selftest

# 2. the census itself, both scopes, human-readable   (exit 0 == every pin reproduced)
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py . --report

# 3. the same thing as JSON, with every row
python3 .softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py .

# 4. the seven counterexample cells, row by row, from the raw schedules
python3 .softhouse/capture/t277-shapelaw-salvage/src/dump_seven_t277.py .

# 5. the SECOND instrument — same seven, independently written arithmetic
python3 .softhouse/capture/t277-shapelaw-salvage/src/crosscheck_seven_t277b.py --selftest
python3 .softhouse/capture/t277-shapelaw-salvage/src/crosscheck_seven_t277b.py .

# 6. the I1q trap, reproduced on demand — this one MUST exit 1
python3 .softhouse/capture/t277-shapelaw-salvage/src/crosscheck_seven_t277b.py . --i1q-from-row
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

## Two instruments, because one instrument is one opinion

`T277`'s first worker was killed by a rate limit. The resuming worker **did not sign a transcript it
had not measured**, and wrote `src/crosscheck_seven_t277b.py`: a second census that imports nothing
from the first and re-derives the exact monthly rate fraction, `HALF_UP`, the 19-digit termination
test, the admission rule, the stuck-cell selector and both law forms **from scratch, by a different
route** (rate as an integer numerator over `10^k · 1200`; `HALF_UP` as `(2a + b) // 2b`). Two
separately written arithmetics on the same committed bytes agree on **296 / 220 / 76 / 213 / the same
seven**, on both disjointness intersections being **0**, and on header principal equalling the row sum
on all 296.

### `I₁q` is NOT observable in the emitted schedule — the trap that looks like independence

The obvious way to make a re-derivation "more independent" is to take `I₁q` from repayment row 1's
`interest` field rather than computing it. **That is invalid.** On a STUCK cell row 1 repays no
principal, so the oracle emits `interest == total == E` — the interest is **already clipped to the
instalment** and the deficit is carried, not shown. Deriving `δ` from that field forces `δ = 0` on
all 296 cells *by construction*, which then "refutes" law (ii) on **183** cells and reports the
disjointness as broken. **This is measured, not warned about**: `--i1q-from-row` reproduces the
collapse on demand (exit 1, `evidence/60-…`). Anyone reading `δ` off row 1 is measuring `E` twice.

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
| `src/crosscheck_seven_t277b.py` | the SECOND census — shares no line of code with the first |
| `src/verify_t277.sh` | **one command**: both instruments, both censuses, four mutations that must trip |
| `evidence/50-conformance-bar.log` | `bash .softhouse/conformance.sh`, first worker |
| `evidence/51-conformance-bar-second-worker.log` | the same bar re-run on the **delivered** tree, after both merges of `main` |
| `evidence/60-crosscheck-DEAD-END-i1q-from-row.txt` | the `I₁q`-from-the-schedule trap, reproduced, exit 1 |
| `evidence/61-crosscheck-second-instrument.txt` | the second instrument's self-test and census, exit 0 |
| `evidence/70-verify-all.txt` | `verify_t277.sh` on the delivered tree — 5 positives, 4 negatives, exit 0 |
| `evidence/71-verifier-meta-calibration.txt` | the verifier caught failing to catch: `DID NOT TRIP` and `ABORT` |

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
