# Reproducing capture pass 3f (Path A) — the currency-quantization tie

**Pass 3f is pass 3e's rig with a new case list**, exactly as pass 3c is pass 3b's
(`README-pass3c.md`). `README-pass3b.md` still describes the recipe; everything it says about
preconditions, output paths and attestation applies here unchanged. This file records only what
differs.

> "The oracle" is the Fineract reference implementation this program grades Go output against.
> Oracle Database is a prohibited product here. PostgreSQL is the only permitted database; this
> seam is a library call and opens no database connection at all.

## Why it exists

Task **T61**, pattern **P-3**. The Go port was mutated into thirteen named wrong implementations
and each was run against the **real** harness at 29 promoted parity vectors. One survivor moves
money on ordinary MNT loans:

**`MONEY-QUANTIZATION-HALF-EVEN`** — a port that applies `HALF_EVEN` where the reference oracle
applies the **tenant's** rounding mode at `Money.java:52`. Buyan ratified `HALF_UP` (Fineract
`RoundingMode` ordinal 4) on 2026-08-18 and `CLAUDE.md` requires it pinned explicitly and never
inherited — *because `HALF_EVEN` is the reference oracle's own stock configuration default.* A
port that reads the default instead of the tenant pin, or that reaches for the banker's-rounding
primitive its standard library happens to offer, lands exactly there. **It passed all 29 promoted
vectors, exit 0.**

The two rules differ **only on an exact tie**, and only when the truncated value is even. Not one
of the 29 promoted vectors lands the quantization on a tie, so none of them could tell the two
apart.

## The shape, derived from source rather than searched for

On an on-lattice `FIXED_30_360` monthly loan at 21.6% the period-1 rate factor is exactly `0.018`,
so period-1 interest in **minor units** is `18*B/1000` for a principal of `B` minor units. That is
an exact half-minor-unit tie when

    18*B == 500 (mod 1000)      i.e.   B == 250 (mod 500)

and the two rules disagree when `floor(18*B/1000)` is **even**. `B = 100005250` satisfies both.
A 40,001-shape sweep of the port against the mutant then confirmed 104 separating shapes among
2,001 consecutive principals; three were put to the oracle.

## The seven cases

| id | role | MathContext | shape |
|---|---|---|---|
| `P-CAL` | RIG CALIBRATION | (12, HALF_UP) | 100 / 6 × 7.0 %, usd — inputs identical to pass 3b's `P-CAL` |
| `P-CAL-P00` | RIG CALIBRATION | (19, HALF_UP) | 100 / 6 × 7.0 %, usd — inputs identical to pass 3b's `P-00` |
| `P-CAL-EMI6` | RIG CALIBRATION | (19, HALF_UP) | MNT 1,014,632 / 6 × 7.0 % — inputs identical to pass 3c's `P-EMI-6-1M014632` |
| `P-CAL-LATQ0a` | RIG CALIBRATION **added by this pass** | (19, HALF_UP) | MNT 1,200,000 / 6 × 21.6 %, start = disb = 2024-01-01 — inputs identical to pass 3e's `P-LAT-Q0a` |
| `T61-HE-A` | parity candidate | (19, HALF_UP) | MNT 1,000,541.50 / 6 × 21.6 % |
| `T61-HE-B` | parity candidate | (19, HALF_UP) | MNT 1,000,052.50 / 6 × 21.6 % |
| `T61-HE-C` | parity candidate | (19, HALF_UP) | MNT 1,000,089.50 / 6 × 21.6 % |

**The fourth calibration is the one that matters most here.** `P-CAL-LATQ0a` is the **same
question** as all three candidates in every field but the principal — same lattice date, same
term, same rate, same currency, same MathContext — and its observation is *already a promoted
parity vector*. A rig that reproduces it is calibrated on exactly the arithmetic this promotion
rests on, not merely on something nearby.

## Run it

From the repo root:

```sh
sh .softhouse/capture/src/run-pass3f.sh
```

Optional environment: `PINNED_FINERACT`, `CAP_OUT_DIR`, `REF3B_JSON`, `REF3C_JSON`, and
`REF3E_JSON` (the pass-3e artefact the fourth calibration reproduces).

## What makes it fail

All of pass 3e's precondition breaches, **not one weakened**, with the calibration arm widened
from three references to four: any of the four RIG CALIBRATIONS failing to reproduce the committed
observation it repeats — `inputs` and `observed` compared as canonicalised JSON, cell for cell,
tenant id included — and any of the three calibration reference artefacts being missing or at the
wrong sha256:

```
capture-prod3b-raw.json  8d23c48fa13c04677b51bacdf07d101d6a061c79815d76b4983eccdbac945c79
capture-prod3c-raw.json  cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec
capture-prod3e-raw.json  8822699cc4505236c12ddd1f8156b273e0a88eaffb1ef73f73f409fc05104fc0
```

**A rig that cannot reproduce an already-known value is not trustworthy and nothing else from that
run may be believed.** If calibration fails, stop and report — never "fix" it by adjusting the
expected value.

Observed on the committed run: all four calibrations matched, inputs and observed blocks identical.

## Verifying a re-run

Compare **`capturesCanonicalSha256`** in `out/capture-prod3f-attestation.json`:

```
bcdd5e0e4bd22a36f1531f3b75052d3570e4348a810bcaf95bbbd65bdf3c07b6
```

Stable across runs; the whole-file digest is not, because the attestation carries a UTC timestamp.

## How the rig was built

`.softhouse/handoff/T61-sweep/build-pass3f.py` constructs `Capture3f.java` and `run-pass3f.sh`
**mechanically** from the pass-3e originals, and aborts if any substitution anchor fails to match.
That is deliberate: it makes "not one precondition was weakened" a property of the construction
rather than a claim in a comment. Re-running it reproduces both files.

## The prediction, and that it was registered first

`.softhouse/capture/t61-halfeven/PREDICTION.md` names the full schedule of all three shapes and one
sharp claim — that the oracle emits `18000.95` on period 1 of `T61-HE-B`, not `18000.94` — and it
was **committed one commit before this capture ran**. `check-prediction.py` compares the two:
**54 cells, 0 mismatches.** The git history is what makes that checkable rather than narrated.

## Analysis, not capture

`.softhouse/capture/t61-halfeven/out/t61-counterfactuals-pass3f.json` holds the **derived**
counterfactual: what a `HALF_EVEN` port emits, and therefore the margin. Nothing there is an
observation. Its control is the load-bearing part — with the mutation switched **off** the model
reproduces all **60** graded money cells of the three cases with **zero** mismatches, so the only
thing a reported margin can be measuring is the named change.
