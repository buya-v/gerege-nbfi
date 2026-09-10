# OWNER — collateral-nonround-money

**Subject:** a collateral product whose money inputs are NOT the seed's round
`basePrice 100000.00` / `pctToBase 50.00`, linked to a client with a non-whole
scale-5 `quantity`, so the collateral corpus finally varies `base_price`,
`pct_to_base`, `quantity`, `total` and `total_collateral` and a port that
hardcodes any of them, or that takes a `/2` shortcut, goes red.

**Oracle:** Fineract reference implementation, tenant `gerege`, containers
`gerege-oracle-db` (postgres) + `gerege-oracle-app` (fineract).
**Business date:** not used — the collateral read path is date-free.
**Snapshot (pre-write):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohcolll-write-20260910T104559Z.dump`
(3,086,960 bytes, `PGDMP`, `pg_restore -l` valid, 2,515 TOC entries). Not committed.

## What was created

| object | id | fields observed |
|---|---|---|
| collateral product `OHK-Collateral-Nonround` | **3** | `basePrice 41850.08000`, `pctToBase 37.50000`, `unitType 1`, `currency MNT`, `quality Good` |
| client collateral (client **6**, product 3) | **3** | `quantity 2.50000`; computed `total 104625.2000000000`, `totalCollateral 39234.450000000000000` |

DB verification after the write:

```
id|name                    |base_price   |pct_to_base|unit_type|currency
2 |SEED-Collateral-Product |100000.00000 |50.00000   |1        |93
3 |OHK-Collateral-Nonround |41850.08000  |37.50000   |1        |93

id|client_id|collateral_id|quantity
2 |5        |2            |1.50000
3 |6        |3            |2.50000
```

## Choice of numbers, and the arithmetic (worked out BEFORE creating anything)

* **`basePrice 41850.08` → `4185008000` scale-5, `4185008` minor units.** The
  seed `100000.00` is a round whole-tugrik base price: it hides truncation (a
  whole-tugrik port drops nothing) and a hardcoded `100000` port. `41850.08`
  ends in `.08`, so a coarse port loses a non-zero fraction.
* **`pctToBase 37.5` → `3750000` scale-5.** The seed `50.00` is exactly a `/2`
  shortcut and exactly a round half, so a port that hardcodes `50` or computes
  `total/2` is invisible against every seed vector. `37.5` is NOT 50, so both
  defects go red. It is also non-integer, so an integer-only per-cent rendering
  fails.
* **`quantity 2.5` → `250000` scale-5.** Not a whole number, so truncating the
  scale-5 count to a whole unit (`2.5 -> 2`) changes the valuation.

    total            = 41850.08 × 2.5       = 104625.20
    totalCollateral  = 104625.20 × 37.5/100 = 39234.45

  Scale-5 counts: `total 10462520000`, `totalCollateral 3923445000`.
  Minor units (MNT, 2): `10462520`, `3923445` — both whole, so there is
  **NO sub-minor residue** (G-19 / DEC-2 predicate G-08). Nothing was refused.
  Money is exact decimal text in the request and integer counts in the vectors;
  no float appears on any money path.

## Endpoints driven (every request/response committed)

| step | endpoint | status | artifact |
|---|---|---|---|
| list products (pre) | `GET /collateral-management` | 200 | `out/collateral-products-pre-raw.json` |
| create product | `POST /collateral-management` | 200 `{"resourceId":3}` | `out/collateral-product-nonround-raw.json` |
| link to client | `POST /clients/6/collaterals` | 200 `{"resourceId":3,"clientId":6}` | `out/client-collateral-nonround-raw.json` |
| client page (post) | `GET /clients/6/collaterals` | 200 `[]` | `out/client-collateral-page-post-raw.json` |
| **valuation read-back** | `GET /clients/6/collaterals/3` | 200 | `out/client-collateral-single-nonround-raw.json` |
| product read-back | `GET /collateral-management/3` | 200 | `out/collateral-product-nonround-readback-raw.json` |
| list products (post) | `GET /collateral-management` | 200 | `out/collateral-products-post-raw.json` |

Script: `bin/step01-capture.sh` (re-runnable: product keyed on name, holding on
`(client_id, collateral_id)`).

Read-backs:
* product 3 — `basePrice 41850.08000`, `pctToBase 37.50000`, `unitType "1"`,
  `currency "MNT"`, `name "OHK-Collateral-Nonround"`, `quality "Good"`, `id 3`.
* holding 3 — `quantity 2.50000`, `total 104625.2000000000`,
  `totalCollateral 39234.450000000000000`, `clientId 6`, `id 3`.

## Cited capture hashes (re-verify after writing)

```
aa8836dbd07598cd66c6957b38e22067f93b5e03c5daf8529a04e6c13c3c24cf  out/collateral-product-nonround-readback-raw.json
2d8514322f68ac3ae790bbacb3d08a7235548db833b81f0dbed375c3b793438a  out/client-collateral-single-nonround-raw.json
cce1dc6edf3120d7957ae3d634287c5dc04dde839b455032f2b32e59dd694119  out/collateral-products-post-raw.json
4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945  out/client-collateral-page-post-raw.json
```

## Byte-stability of `req/`

The product body sends `basePrice`/`pctToBase` as exact decimal **strings**
(`"41850.08"`, `"37.5"`) — the oracle's Jackson `BigDecimal` deserializer accepts
them and stored `41850.08000`/`37.50000` exactly, so no money value is ever a
JSON float. `quantity` is `2.5`, a binary-exact value whose shortest round-trip
spelling is `2.5` (Go `encoding/json` and Python `repr` agree). A structural
round-trip check plus a shortest-double token check across `req/` reports
`BAD=0`: no `100.00 -> 100.0` class drift, no float token drift.

## Safety

Tenant `gerege` only; SQL was read-only; nothing was SQL-inserted. No `.dump` is
committed.
