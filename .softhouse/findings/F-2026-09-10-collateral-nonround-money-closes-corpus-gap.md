# F-2026-09-10 — the collateral corpus's uniformity was closed with NON-ROUND oracle data, and four new drives now see it

**Status:** RESOLVED. This is the last residual of
`F-2026-09-10-drive-ratio-only-applies-to-rich-requests.md` (the corpus line
`collateral  4 vectors / 0 varying / 4 constant`) acted on.
**Subject capture:** `.softhouse/capture/collateral-nonround-money/` — committed at
`f51cea9f` **before grading**. Promoted vectors + drives committed at `0c63eb9d`.

## The residual, restated

`collateral` had 4 vectors and **ZERO varying request fields**. Every one named the same
entities — `link_id 2, client_id 5, collateral_id 2, product_id 2` — and the oracle held
exactly **one** collateral product:

    id 2  SEED-Collateral-Product  quality Good  basePrice 100000.00000  pctToBase 50.00000  unitType 1  MNT

`CL-04-valuation-read` grades `quantity 1.50000`, `total 150000.0000000000`,
`totalCollateral 75000.000000000000000` — both inputs round, and `pctToBase = 50.0` is
just halving. **A port that hardcoded the base price, hardcoded the percentage, or took a
`/2` shortcut computed the right answer on every vector, and no drive could catch it: no
drive can catch a port ignoring a field every vector holds fixed.** The root cause was
upstream of the vectors — the oracle's seed data was uniform.

## What was added to the oracle

One product and one client holding, captured end to end (`OWNER.md` in the capture dir):

    product id 3  OHK-Collateral-Nonround  basePrice 41850.08000  pctToBase 37.50000  unitType 1  MNT
    holding id 3  client 6 -> product 3    quantity 2.50000
                  total 104625.2000000000  totalCollateral 39234.450000000000000

### Choice of numbers, and the arithmetic (worked out BEFORE creating anything)

* **`basePrice 41850.08`** → scale-5 `4185008000` → minor `4185008`. The seed
  `100000.00` is a round whole-tugrik base price: it hides truncation (a whole-tugrik
  port drops nothing) and a hardcoded `100000`. `41850.08` ends in `.08`, so a coarse
  port loses a non-zero fraction.
* **`pctToBase 37.5`** → scale-5 `3750000`. The seed `50.00` is exactly a `/2` shortcut
  and exactly a round half, so a port that hardcodes `50` or computes `total/2` is
  invisible against every seed vector. `37.5` is NOT 50, so both defects go red. It is
  also non-integer, so an integer-only per-cent rendering fails.
* **`quantity 2.5`** → scale-5 `250000`. Not a whole number, so truncating the scale-5
  count to whole units changes the valuation.

      total           = 41850.08 × 2.5        = 104625.20
      totalCollateral = 104625.20 × 37.5/100  = 39234.45

  Scale-5: `10462520000` / `3923445000`. Minor units (MNT, 2): `10462520` / `3923445` —
  both whole, so there is **NO sub-minor residue** (G-19 / DEC-2 predicate G-08).
  Nothing was refused, and nothing was SQL-inserted. The oracle stored
  `104625.2000000000` and `39234.450000000000000`, exactly matching the worked arithmetic.
  Money is exact decimal text in the request, integer counts in the vectors; no float on
  any money path (HALF_UP, ordinal 4, precision 19, `Asia/Ulaanbaatar`).

## What was promoted into the corpus

* `CL-05-product-read-nonround.json` — product seam: `base_price 4185008000`,
  `pct_to_base 3750000`, `unit_type 1`, quality Good, currency MNT; capture
  `out/collateral-product-nonround-readback-raw.json`, sha256
  `aa8836dbd07598cd66c6957b38e22067f93b5e03c5daf8529a04e6c13c3c24cf`.
* `CL-06-valuation-read-nonround.json` — valuation seam: `quantity 250000`,
  `total 10462520000`, `total_collateral 3923445000`, `client_id 6`; capture
  `out/client-collateral-single-nonround-raw.json`, sha256
  `2d8514322f68ac3ae790bbacb3d08a7235548db833b81f0dbed375c3b793438a`.

Both hashes re-verified against the committed capture. Both vectors load:
`collateral-go` over the 6-vector store reports `vectors_loaded=6 parity_pass=6
parity_fail=0 refused=0 inadmissible=0 harness_error=0 graded_cells=25
invariant_violations=0`. Vector sha256:
`2b8ac11672cbaf5df5b0b6c31a68cbf5cadbde6b5fea0bc1ddd9084508751c6d` (CL-05),
`1e350baf18412e3e2b6bb7bb17d3309282d043d0859915a3eebb0a07c5e7c939` (CL-06).

## The four new drives, and proof each was inert before it was live

Registered in `nexus/internal/apps/collateral/conformance/impl.go`:

| drive | defect it embodies |
|---|---|
| `collateral-wrong-base-price-hardcoded` | product read writes the SEED `100000.00` for every product, ignoring `basePrice` |
| `collateral-wrong-pct-hardcoded` | product read writes the SEED `50.00000` for every product, ignoring `pctToBase` |
| `collateral-wrong-valuation-half` | valuation takes `total_collateral = total / 2` instead of applying `pctToBase` |
| `collateral-wrong-quantity-truncated` | single-row read truncates the scale-5 `quantity` to a whole unit and recomputes |

Measured against the **old 4-vector seed-only store** vs the **new 6-vector store**
(direct binary with `-store`, because `kills.sh` has no store flag; scratch roots
`/tmp/collateral-seed-only-store`, `/tmp/store-cl05`, `/tmp/store-cl06`):

| drive | seed-only(4) | full(6) | kills which vector |
|---|---:|---:|---|
| `collateral-wrong-base-price-hardcoded` | **0** | 1 | CL-05 only |
| `collateral-wrong-pct-hardcoded` | **0** | 1 | CL-05 only |
| `collateral-wrong-valuation-half` | **0** | 1 | CL-06 only |
| `collateral-wrong-quantity-truncated` | 1 | 2 | CL-04 + CL-06 |

The three **0-on-seed** drives are exactly the `/2` shortcut and the two hardcoded fields
the seed's `100000.00000` and `50.00000` could not distinguish. This is the measurement
that turns "the gap existed" into evidence: run against the seed-only store each of those
three binaries reports `parity_pass=4 parity_fail=0` and would have been an inert drive.
Against the full store each fails exactly the one new vector it is built to see.

**No coverage was manufactured.** `collateral-wrong-quantity-truncated` was already live at
**1** on the seed-only store (CL-04's `quantity 1.5` is already fractional), so its count
rises 1 → 2; the new vector adds attribution, not an artificial first kill. All four
pre-existing drives still kill (below). The two new vectors also discriminate some old
drives: `collateral-wrong-blank-quality` 1 → 2 (it blanks CL-05's quality too) and
`collateral-wrong-valuation-pct-scale` 1 → 2 (it mis-scales CL-06's `total_collateral`).

## Controls after the change (primary control: nothing regressed)

`kills.sh collateral <impl>` over the committed 6-vector store:

    collateral-go                                    0   (correct)
    collateral-wrong-blank-quality                   2
    collateral-wrong-type-id                         1
    collateral-wrong-fabricates-client-holding       1
    collateral-wrong-valuation-pct-scale             2
    collateral-wrong-base-price-hardcoded            1
    collateral-wrong-pct-hardcoded                   1
    collateral-wrong-valuation-half                  1
    collateral-wrong-quantity-truncated              2

* `go build ./...` exit 0; `go test ./...` all packages ok (collateral included).
* `collateral-go` passes all 6 vectors; the four pre-existing drives all still kill.
* `bash .softhouse/conformance.sh` — exit **2** as the recorded §4.4.2 decision, ledger
  findings == baseline, `CENSUS wrong ledger implementations` = **17** pinned, exemption
  and P-number pins unchanged. The no-float guard inspected 186 vector files and the
  wire-float round-trip census reported `ALTERED 0` across the capture records the store
  cites. No `.dump` committed; `ledger-invariants.baseline` and `conformance.sh` untouched.
* `req/` byte-stability re-checked independently: 3 numeric tokens, `BAD=0` (the product
  body sends `41850.08` / `37.5` as exact decimal **strings**; `quantity 2.5` is
  binary-exact).

## One bounded context

Every change is `collateral`: one capture directory, two vectors, one implementation
file. The snapshot
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohcolll-write-20260910T104559Z.dump`
(3,086,960 bytes, `PGDMP`, valid TOC) is not committed and is not a `.dump` in the tree.
