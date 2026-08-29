# T440 — INDEPENDENT review of T424 (`softhouse/T424-t408-conditions`)

**STATUS: PROVISIONAL — points 1-5 driven, point 6 and the bar still outstanding.**

**PROVISIONAL VERDICT: APPROVED WITH CONDITIONS** (conditions being drafted)

## Checklist

- [x] 1. True cause of F-2 — both halves re-driven independently: **T424 CONFIRMED**
- [x] 2. pipefail rightmost-non-zero — verified from shell behaviour: **T424 CONFIRMED**
- [x] 3. Buffered-writer guard — four matrices re-run: **all reproduce**; construction attacked, 1 finding
- [x] 4. `PIPESTATUS` self-error — mechanism and repair confirmed; harness swept: **0 other sites**
- [x] 5. K8 / STATE-LOSS — census re-run both refs, cell for cell; **zero live sites CONFIRMED**;
      but the published DECOMPOSITION of the 29 is wrong (finding)
- [ ] 6. Open items confirmed by name
- [ ] BAR on T424 tree / merge result with `main`

Drives in `instruments/`, transcripts in `out/`. All scratch under `/tmp`.
