# F-2026-09-10 — the shares corpus's uniformity was closed with NON-ROUND oracle data, and a new drive now sees it

**Status:** RESOLVED. This is the residual of
`F-2026-09-10-drive-ratio-only-applies-to-rich-requests.md` acted on.
**Subject capture:** `.softhouse/capture/shares-nonround-money/` (committed before grading).

## The residual, restated

`shares` had 7 vectors and **11 CONSTANT request fields** — near-clones varying only
`kind`, `share_capital`, `dividend_amount`. Every money field was frozen at the seed
value (`unit_price`/`purchased_price` `"100.00"`, `total_shares` 1000, `purchased_shares`
100, `total_approved_shares` 100, MNT). **A port that hardcoded `unit_price = 100` passed
every vector, and no drive could catch it: no drive can catch a port ignoring a field
every vector holds fixed.** The root cause was upstream of the vectors — the oracle's
three seed products were identical (`unitPrice 100.0`, `totalShares 1000`, MNT).

## What was added to the oracle

One product and one Active account, captured end to end (`OWNER.md` in the capture dir):

    product id 4  OHK-Share-Nonround  unitPrice 137.50  shareCapital 188787.50  totalShares 1373  MNT
    account id 5  OHK-SHARE-ACCT      Active 300, purchase 137 shares @ 137.50 = 18837.50 (status 300)

`137.50` is **not** a round seed multiple: `100.00 × anything` is a multiple of 100 minor
units and hides both truncation (a whole-tugrik port drops the `.50`) and rounding (no tie
to resolve). `137.50 × 137 = 18837.50` ends in a half-tugrik residue a coarse port loses,
and `1373 = 137 × 10 + 3` so the account count does not divide the product total. It is
exact at 2dp, so it carries **no sub-minor residue** (G-19 / DEC-2 predicate G-08) and
nothing was refused or SQL-inserted. Money is integer minor units throughout
(`137.50 -> 13750`, `18837.50 -> 1883750`, `188787.50 -> 18878750`).

## What was promoted into the corpus

* `SH-08-share-product-nonround-money.json` — product seam, unit `13750`, capital
  `18878750`, total `1373`; capture `out/share-product-detail-raw.json`, sha256
  `40c2bcc65b16c5ee579dcbfe9a99e9f57d4e1d3b61a1b4c3125fb4f48dc1b7b1`.
* `SH-09-share-account-nonround-money.json` — account seam, status 300, approved 137,
  pending 0, purchased 137 @ `13750` = `1883750`, purchase status 300; capture
  `out/share-account-detail-raw.json`, sha256
  `3d1af6c9640dfa776856c7189e9eb051b24c76eac0dcaf76abe8596824c69c7b`.

Both hashes re-verified after the capture commit; both vectors load
(`vectors_loaded=9 parity_pass=9 parity_fail=0` under `shares-go`).

## The new drive, and proof it was inert before it was live

`shares-wrong-unit-price-hardcoded` (`nexus/internal/apps/shares/conformance/impl.go`)
writes the SEED `100.00` (10000 minor units) for every product and every purchase,
ignoring `request.unit_price` / `request.purchased_price`. Measured with
`kills.sh shares <impl>`:

| implementation | before promotion | after promotion |
|---|---:|---:|
| `shares-go` (control) | 0 | **0** |
| `shares-wrong-off-by-one` | 6 | 8 |
| `shares-wrong-status-iota-ordinal` | 3 | 4 |
| `shares-wrong-summary-approved-as-pending` | 2 | 3 |
| `shares-wrong-product-price-transposed` | 3 | 4 |
| `shares-wrong-zero-money-dropped` | 1 | **1** (unchanged) |
| `shares-wrong-unit-price-hardcoded` | — | **2** |

The new drive's two kills are exactly SH-08 and SH-09. **Proven live, not assumed:** run
against a scratch store containing **only the 7 seed vectors**, the same binary reports
`vectors_loaded=7 parity_pass=7 parity_fail=0` — it kills ZERO and would have been an inert
drive. Against the full 9-vector store it reports `parity_fail=2`. The corpus gap, not the
drive, was the missing instrument.

**No coverage was manufactured.** `shares-wrong-zero-money-dropped` stays at 1 because the
new vectors carry no zero money cell (the non-round cells are `13750`/`1883750`/`18878750`;
only SH-06's product carries `0.00`), so it is correctly left out of that drive's red set.
The other five existing drives all still kill (1–8).

## Controls after the change

* `go build ./...` and `go test ./...` (shares packages) pass.
* `kills.sh shares shares-go` = 0; the binary loads 9/9 parity, 0 refused, 0 inadmissible,
  `graded_cells=32 money_cells=14`.
* `bash .softhouse/conformance.sh` — exit 2 as the recorded §4.4.2 decision, ledger
  findings == baseline, census 17 wrong ledger impls, exemption pins (parity 10, refusal 6,
  money cells 63) unchanged. No `.dump` committed; no baseline or harness file touched.
