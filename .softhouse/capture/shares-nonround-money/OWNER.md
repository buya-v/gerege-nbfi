# OWNER — shares-nonround-money

**Subject:** a share product whose money fields are NOT the seed 100.00 / 1000,
opened into an Active share account with a real purchase, so the shares corpus
finally varies `unit_price`, `share_capital`, `total_shares`, `purchased_price`,
`purchased_amount` and the approved/purchased share count.

**Oracle:** Fineract reference implementation, tenant `gerege`, container
`gerege-oracle-db` (postgres:18.3) + `gerege-oracle-app` (fineract:latest).
**Business date used:** `2026-09-03` (never `now`).
**Snapshot (pre-write):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohsharesk-write-20260910T101407Z.dump`
(3,081,584 bytes, `PGDMP`, `pg_restore -l` valid). Not committed.

## What was created

| object | id | money fields observed |
|---|---|---|
| share product `OHK-Share-Nonround` | **4** | `unitPrice 137.50`, `shareCapital 188787.50`, `totalShares 1373`, `totalSharesIssued 1373`, `currency MNT` |
| share account `OHK-SHARE-ACCT` (client 6, savings 2) | **5** | status `300` Active; `totalApprovedShares 137`, pending `0`; purchase `137` shares @ `137.50` = `18837.50`, purchase status `300` Approved |

### Choice of numbers, and why

* **Unit price `"137.50"` → `13750` minor units.** The seed price is `100.00`
  for every product and every purchase, so `100.00 × anything` is a multiple of
  100 minor units and hides truncation (whole-tugrik port drops the `.50`) and
  rounding (a half-up defect has no tie to resolve). `137.50` ends in `.50`, so
  the purchase total `137 × 137.50 = 18837.50` carries a half-tugrik residue a
  coarse port loses. It is exact at 2dp, so it is vectorable and creates **no
  sub-minor residue** (G-19 / DEC-2 G-08 satisfied).
* **Totals `1373` (issued `1373`)** → share capital `137.50 × 1373 = 188787.50`.
* **Purchase count `137`.** `1373 = 137 × 10 + 3`, so the account's approved /
  purchased count does not divide the product's total. The share counts vary too.
* All money is carried as exact decimal **text** (`"137.50"`) and written as
  **integer minor units** in vectors (`13750`, `1883750`, `18878750`). No float
  in any path.

## Endpoints driven (every request/response committed)

| step | endpoint | status | artifact |
|---|---|---|---|
| list products (pre) | `GET /products/share` | 200 | `out/shares-products-list-pre-raw.json` |
| create product | `POST /products/share` | 200 `{"resourceId":4}` | `out/share-product-create-raw.json` |
| list accounts (pre) | `GET /accounts/share?limit=100` | 200 | `out/shares-accounts-list-pre-raw.json` |
| submit account | `POST /accounts/share` | 200 `{"resourceId":4}` | `out/share-account-submit-raw.json` |
| approve | `POST /accounts/share/4?command=approve` | 200 | `out/share-account-approve-raw.json` |
| activate (first try) | `POST /accounts/share/4?command=activate` | **400 REFUSED** | `out/share-account-activate-refused-note-raw.json` |
| pre-activate read | `GET /accounts/share/5?associations=all` | 200 | `out/share-account-detail-pre-activate-raw.json` |
| activate (corrected) | `POST /accounts/share/5?command=activate` | 200 | `out/share-account-activate-raw.json` |
| product detail (read-back) | `GET /products/share/4` | 200 | `out/share-product-detail-raw.json` |
| account detail (read-back) | `GET /accounts/share/5?associations=all` | 200 | `out/share-account-detail-raw.json` |
| list products (post) | `GET /products/share` | 200 | `out/shares-products-list-post-raw.json` |
| list accounts (post) | `GET /accounts/share?limit=100` | 200 | `out/shares-accounts-list-post-raw.json` |

Script: `bin/step01-capture.sh` (re-runnable: product keyed on name, account
keyed on `externalId` within the Active list).

## Two oracle behaviours the capture surfaced (both real observations)

1. **`activate` REFUSES an unsupported `note` parameter** (HTTP 400):
   ```json
   {"developerMessage":"The request was invalid. ...","httpStatusCode":"400",
    "defaultUserMessage":"Validation errors exist.",
    "userMessageGlobalisationCode":"validation.msg.validation.errors.exist",
    "errors":[{"developerMessage":"The parameter note is not supported.",
    "defaultUserMessage":"note","userMessageGlobalisationCode":"error.msg.parameter.unsupported",
    "parameterName":"note","args":[]}]}
   ```
   `approve` accepts `note`; `activate` does not. The seed activate body omits
   it. Preserved as `out/share-account-activate-refused-note-*` / the matching
   `req/`. The corrected activate then succeeded (200).
2. **The share-account list is Active-only.** `GET /accounts/share` returned
   `totalFilteredRecords 2` (accounts 2 and 3) while account 1 was Pending (100)
   and account 4 Approved (200); after account 5 activated it returned 3. A
   non-Active account is invisible to the list, which is why the first
   idempotence lookup missed account 4 and a second account (id 5) was opened on
   the same product. Both are on product 4; **account 5 is the Active, captured
   observation** cited by the vectors. Account 4 remains Approved (200).

## Oracle state, verified before and after

Before (three seed products, all `unit_price 100.00`, `total_shares 1000`, MNT):

```
id|name            |total_shares|issued_shares|unit_price|capital_amount|currency
1 |SEED-Share-Prod |1000        |0            |100.00    |0.00          |MNT
2 |SEED-Share-Prod-2|1000       |(null)       |100.00    |1.00          |MNT
3 |SEED-Share-Product|1000      |1000         |100.00    |100000.00     |MNT
```

(The corpus claim is exact on `unit_price`, `total_shares` and currency; the
`capital_amount`/`issued_shares` columns already differed, so the frozen money
cells are `unit_price` — and the derived `capital_amount` — not the raw column.)

After (additive; only product 4 + account 5 matter):

```
id|name              |total_shares|issued_shares|unit_price|capital_amount|currency
4 |OHK-Share-Nonround|1373        |1373         |137.50    |188787.50     |MNT
```

```
id|account_no|external_id     |client|product|status_enum|savings
1 |000000001 |SEED-SHARE-ACCT-1|5   |1      |100 (Pending)|1
2 |000000002 |SEED-SHARE-ACCT-2|5   |2      |300 (Active) |1
3 |000000003 |SEED-SHARE-ACCT  |6   |3      |300 (Active) |2
4 |000000004 |OHK-SHARE-ACCT   |6   |4      |200 (Approved)|2
5 |000000005 |OHK-SHARE-ACCT   |6   |4      |300 (Active) |2
```

Transaction store `m_share_account_transactions` for account 5:
`total_shares 137 | unit_price 137.50 | amount 18837.50 | amount_paid 18837.50
| status_enum 300 | type_enum 500`, matching the API read-back exactly.

## Cited capture hashes (re-verify after writing)

```
40c2bcc65b16c5ee579dcbfe9a99e9f57d4e1d3b61a1b4c3125fb4f48dc1b7b1  out/share-product-detail-raw.json
3d1af6c9640dfa776856c7189e9eb051b24c76eac0dcaf76abe8596824c69c7b  out/share-account-detail-raw.json
```

Read-backs:
* product 4 — `unitPrice 137.5`, `shareCapital 188787.5`, `totalShares 1373`,
  `totalSharesIssued 1373`, currency `MNT`.
* account 5 — `status.id 300`, `summary.totalApprovedShares 137`,
  `summary.totalPendingForApprovalShares 0`, `purchasedShares[0]`:
  `numberOfShares 137`, `purchasedPrice 137.5`, `amount 18837.5`,
  `amountPaid 18837.5`, `status.id 300`, `type.id 500`,
  `currentMarketPrice 137.5`.

## Byte-stability of `req/`

Every money value is a JSON **string** with the exact stored decimal text
(`"137.50"`), every count an integer token; nothing is round-tripped through
`json.dumps` of a parsed number. `grep -n '137\.5[^0]' req/` finds nothing, and
no request body contains a non-integer JSON number token.

## Safety

Tenant `gerege` only; SQL was read-only; nothing was SQL-inserted. No `.dump`
is committed. No member savings or share capital is described as insured,
protected or guaranteed.
