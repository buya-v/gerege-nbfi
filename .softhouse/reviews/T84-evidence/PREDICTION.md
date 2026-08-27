# T84 — prediction, registered BEFORE the re-probe was built or run

Task **T84**, independent review of **T83** (gate **G-8**). Committed in its own commit, whose
child commits carry the evidence. Nothing below was back-fitted.

## What I am predicting

T83 registered the closed form **`B_minor × a(r,n) < 0.5`** (with `a(r,n) = r/(1−(1+r)^−n)`,
`r = annual/100/12`) as a **hypothesis**, explicitly scoped to the 4 rates × 8 terms it sampled.
My re-probe attacks it **outside** that grid, at rates and terms T83 never touched but which the
ratified graded domain admits (`contract.go`: the graded-domain predicate list bounds neither the
annual rate nor `NumberOfRepayments`, beyond `NumberOfRepayments >= 1` as a well-formedness rule).

`prediction.json` carries `predictedFails` for each of the **249** cells, from the closed form,
computed in exact rational arithmetic. **99 are predicted to fail**, 150 to be clean.

## The five attacks, and what each would show

1. **`RP` (12 cells)** — T83's own boundary cells, re-asked with **different tenant ids** and in
   **reverse order**. If the answer moves, T83's rig has a tenant- or order-dependence and the
   whole boundary table is void. Predicted: identical to T83's classification.
2. **`FAR` (24 cells)** — principals 30 … 100 000 minor units on four T83 shapes, far above the
   swept top. T83 swept only ~4 minor units past its boundary; a region that reappears higher up
   would make "contiguous prefix" false. Predicted: all clean.
3. **`RATE` (90 cells)** — five annual rates T83 never sampled (1.2, 3.6, 12.0, 48.0, 96.0).
4. **`TERM` (48 cells)** — eight repayment counts T83 never sampled (1, 5, 7, 30, 60, 120, 240,
   360) at 21.6 %.
5. **`LONG` (54 cells)** — the **boundedness attack**. G-8 as T83 rewrote it says "Every principal
   in the region is far below one MNT". The closed form itself says otherwise once the term is
   long and the rate low, because the failure threshold is `0.5 / a(r,n)` and `a → 1/n` as `r → 0`.
   At 3.6 % / n = 360 the closed form puts the largest failing principal at **B = 109 minor =
   MNT 1.09**; at 0.12 % / n = 360 at **B = 176 = MNT 1.76**. Both shapes are inside the graded
   domain. **I predict the region extends well above MNT 0.25, and that the sentence in G-8 is an
   over-generalisation from a 32-shape sample.**
6. **`TIE` (21 cells)** — the near-tie family. Choosing the annual rate so that `r = 1/(2B)`
   exactly (600 % for B = 1, 300 % for B = 2) makes `B × a(r,n) → 0.5` **from above** as `n` grows,
   with the gap falling to ~1e-19 near `n ≈ 108` (600 %) and `n ≈ 196` (300 %) — i.e. down to the
   ratified precision-19 floor. This is where a closed form derived from exact arithmetic is most
   likely to part company with an oracle that computes at `(19, HALF_UP)`. Predicted: clean
   everywhere, but this is the cell family I most expect to break.

## Registered thresholds (largest failing B by the closed form)

| annual % | n=6 | n=12 | n=56 | n=120 | n=240 | n=360 |
|---|---|---|---|---|---|---|
| 0.12 | 2 | 5 | 27 | 59 | 118 | **176** |
| 1.2 | 2 | 5 | 27 | 56 | 106 | **151** |
| 3.6 | 2 | 5 | 25 | 50 | 85 | **109** |
| 21.6 | 2 | 5 | 17 | 24 | 27 | 27 |

## Also predicted

- T83's committed `out/capture-t83-raw.json` will re-capture **byte-identically** from its own
  committed sources against the pinned image, or its calibration gate will refuse the run.
- `bash .softhouse/conformance.sh` will be **PASS, exit 0, 42 parity vectors, 0 invariant
  violations**, unchanged by anything in T83.
