# Reproducing capture pass 3c (Path A) — the EMI re-adjust smoothing loop

**Pass 3c is pass 3b's rig with a new case list.** `README-pass3b.md` still describes the recipe;
everything it says about preconditions, output paths and attestation applies here unchanged. This
file records only what differs.

Why it exists: T9's independent review, finding **F-2 (P1)**. DEC-1 makes the loop
`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
(`ProgressiveEMICalculator.java:1258-1309`, guard `EmiAdjustment.java:31-44`) a normative
conformance obligation — "a conformance obligation, not backlog", `contract.go:1660-1661` — and
**none of the eleven promoted parity vectors trips its guard**. Pass 3c captures the two shapes
DEC-1 itself names at `contract.go:1655-1658` so the loop can be graded.

## Run it

From the repo root:

```sh
sh .softhouse/capture/src/run-pass3c.sh
```

Optional environment: `PINNED_FINERACT`, `CAP_OUT_DIR` (as pass 3b), and `REF3B_JSON` (the
committed pass-3b artefact the calibration reproduces; default
`.softhouse/capture/out/capture-prod3b-raw.json`).

## The four cases

| id | role | MathContext | shape |
|---|---|---|---|
| `P-CAL` | RIG CALIBRATION | (12, HALF_UP) | 100 / 6 × 7.0 %, usd — inputs identical to pass 3b's `P-CAL` |
| `P-CAL-P00` | RIG CALIBRATION | (19, HALF_UP) | 100 / 6 × 7.0 %, usd — inputs identical to pass 3b's `P-00` |
| `P-EMI-6-1M014632` | parity candidate | (19, HALF_UP) | MNT 1,014,632 / 6 × 7.0 % |
| `P-EMI-36-127704` | parity candidate | (19, HALF_UP) | MNT 127,704 / 36 × 16.8 % |

## What makes it fail

All nine pass-3b precondition breaches, **not one weakened**, plus two added:

10. **either RIG CALIBRATION failing to reproduce the committed pass-3b observation of the case it
    repeats** — `inputs` and `observed` are compared as canonicalised JSON, cell for cell, tenant id
    included, so the reproduction is of the *same question* and not merely of a similar one. A rig
    that cannot reproduce an already-known value is not trustworthy and nothing else from such a run
    may be believed;
11. **the calibration reference itself missing or at the wrong sha256** — it must be
    `8d23c48f…c945c79`, the digest recorded in the `provenance` block of all eleven already-promoted
    parity vectors, so calibrating against it calibrates against exactly the bytes the existing
    corpus was transcribed from.

## Verifying a re-run

Compare **`capturesCanonicalSha256`** in `out/capture-prod3c-attestation.json`:

```
6110d86734f17d16fd1f2cc6b154d069bcc9328ef3bc3b0eb9842682a65aea3e
```

Stable across runs; the whole-file digest is not, because the attestation carries a UTC timestamp.

The sidecar also carries a `calibrationReport` array naming, for each calibration, which committed
capture it reproduced and from which file and digest.

## Cross-harness reproduction

Task **T37** captured these same two shapes through a *different* Path A harness
(`.softhouse/capture/dec1-binding/out/t37-binding.json`, cases `T37-3-A` and `T37-3-B`). Pass 3c
reproduces them on every column both harnesses emit — 478 cells, 0 mismatches:

```sh
python3 .softhouse/capture/emiloop/t37-crosscheck.py
```

T37's captures were never promoted and its harness emits neither the in-container attestation nor
the plan-level `totalPrincipalAmount` / `totalFeeAmount` / `totalPenaltyAmount` /
`totalOutstandingAmount` columns, which promotion needs. That, not the arithmetic, is what pass 3c
adds.

## Analysis, not capture

`.softhouse/capture/emiloop/` holds the derivation of the guard and of the
`EMI-SMOOTHING-LOOP-OMITTED` margins. Nothing there is an observation; it is a model of a **wrong
port**, kept separate from the capture on purpose. See
`.softhouse/handoff/T57-emi-smoothing-loop-vectors.md`.
