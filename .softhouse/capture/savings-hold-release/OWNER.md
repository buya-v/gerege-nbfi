# OWNER — savings-hold-release

**Subject:** the first live observation of the savings **hold/release** pair, so a
CLAUDE.md non-negotiable stops being implementation-without-evidence:

> **Holds are postings and alter `available` only, never posted `balance`.**
> (`CLAUDE.md` line 14)

Before this capture, every apparent "hold" in the savings corpus was a *field*
(`withholdTax`, `amountOnHold`, `amountHold`, `transferOnHold`); no capture
carried a hold-flagged transaction type. This is the first one.

**Oracle:** Fineract reference implementation, tenant `gerege`, containers
`gerege-oracle-db` (postgres) + `gerege-oracle-app` (fineract).
**Business date observed:** 2026-09-03 (COB date 2026-09-02).
**Snapshot (pre-write):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohholdcap-write-20260910T130551Z.dump`
(4,769,006 bytes, magic `PGDMP`, `pg_restore -l` = 2,505 TOC entries). Not committed.

## Status

**Complete.** Hold placed (`out/savings-hold-holdAmount-*`), account and
transactions read back after the hold, hold released, account and transactions
read back after the release. All HTTP 200. No refusal.

The deliverable is a **three-point read-back of account 1** (1 = before,
2 = after hold, 3 = after release), so a later run can check all four limbs of
the rule:

1. the hold **posts a transaction** — an `AMOUNT_HOLD` row appears;
2. **`available` falls** by the held amount — `863.02` from `1000.31`;
3. **posted `balance` does NOT move** — stays `1000.31`;
4. **release restores `available`** — back to `1000.31`, `balance` still `1000.31`.

## Account used, and why

Two active accounts existed (verified read-only in `m_savings_account`):

| id | client | status | posted balance | note |
|---|---|---|---|---|
| **1** | 5 | Active | **1000.31** | product 1, monthly interest posting — **used** |
| 2 | 6 | Active | 1000.01 | product 2, daily interest posting — untouched |

Account **1** was chosen because its product posts interest **monthly**, so no
interest accrual can move the cells between the three read-backs (no COB is run);
its last transaction is the 2026-09-01 interest posting, so a transaction dated at
the business date 2026-09-03 clears the
"amount can be put on hold only after last transaction" rule
(`SavingsAccountTransactionDataValidator.java:307-310`).

## The arithmetic (worked out BEFORE writing anything)

Posted balance = **1000.31 MNT = 100031 minor units** (MNT = ISO 496, minor unit 2).

Hold amount **137.29 MNT = 13729 minor units** — **non-round** (whole-tugrik
portion 137, residue .29), strictly less than the balance, so a port that
truncates to whole tugrik, or that decrements the posted balance, is visible.

    posted balance        1000.31  -> 100031 minor units
    hold (user hold)       137.29  ->  13729 minor units
    available after hold   863.02  ->  86302 minor units   (100031 - 13729)

Every cell is a whole number of minor units — **no sub-minor residue**
(G-19 refuses it; DEC-2 predicate G-08). This is why the amount is not round.

The oracle's own hold algebra predicts the same thing:
`SavingsAccountWritePlatformServiceJpaRepositoryImpl.holdAmount()`
(`SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1875-1894`) sets the
transaction running balance to `accountBalance - amount` (= 863.02) and calls
`account.holdAmount(amount)` — it never touches `accountBalance`.

## Three-point read-back (observed)

Source artifacts (all HTTP **200**): `out/savings-hold-{before,after-hold,after-release}-account-raw.json`
and `out/savings-hold-{before,after-hold,after-release}-transactions-raw.json`
(the two GETs return the same body shape; `?associations=all` is kept so the
summary and the transaction list are in one document).

| point | `summary.accountBalance` | `summary.availableBalance` | held (`m_savings_account.total_savings_amount_on_hold`) | hold/release tx |
|---|---|---|---|---|
| before | 1000.31 | 1000.31 | — (null) | none |
| after hold | **1000.31** (unmoved) | **863.02** (-137.29) | **137.29** | id **6**, enum **20**, amount **137.29**, runningBalance **863.02** |
| after release | **1000.31** (still unmoved) | **1000.31** (restored) | **0.00** | id **6** now `release_id 7`; release row id **7**, enum **21**, amount **137.29**, runningBalance **1000.31** |

### After the hold (observed)

* `GET /savingsaccounts/1?associations=all` -> 200
  (`out/savings-hold-after-hold-account-raw.json`):
  `summary.accountBalance = 1000.31`, `summary.availableBalance = 863.02`.
  The summary exposes `accountBalance` and `availableBalance` but **not** the
  held figure — the held amount is only visible through the `AMOUNT_HOLD`
  transaction row and the read-only DB column.
* transaction list now: `(id, amountHold, amount, runningBalance)` =
  `(6, true, 137.29, 863.02)`, plus `(2, false, 0.16)`, `(3, false, 0.15)`,
  `(1, false, 1000.0)`.
* read-only DB cross-check (`out/db-after-hold.txt`):

      m_savings_account : 1|1000.310000|137.290000
      m_savings_account_transaction (id|type|amount|running_balance|release_id|is_reversed|is_reversal):
        1|1|1000.000000|1000.000000|0|f|f
        2|3|0.160000|1000.310000|0|f|f
        3|3|0.150000|1000.150000|0|f|f
        6|20|137.290000|863.020000|0|f|f

  `transaction_type_enum 20` is the oracle's `AMOUNT_HOLD`. `account_balance_derived`
  is **1000.31**, unmoved by the hold; `total_savings_amount_on_hold` is 137.29.

### After the release (observed)

* `POST /savingsaccounts/1/transactions/6?command=releaseAmount` -> 200
  (`out/savings-hold-releaseAmount-raw.json`):
  `{"officeId":1,"clientId":5,"savingsId":1,"resourceId":7}` — the release row is
  transaction id **7**.
* `GET /savingsaccounts/1?associations=all` -> 200
  (`out/savings-hold-after-release-account-raw.json`):
  `summary.accountBalance = 1000.31`, `summary.availableBalance = 1000.31` —
  available is restored and the posted balance still has not moved.
* transaction list now: `(id, amountHold, amountRelease, amount, runningBalance, releaseTransactionId)` =
  `(7, false, true, 137.29, 1000.31, 0)`, `(6, true, false, 137.29, 863.02, **7**)`,
  `(2, false, false, 0.16, ...)`, `(3, false, false, 0.15, ...)`, `(1, false, false, 1000.0, ...)`.
  The hold row id 6 now points at its release via `releaseTransactionId = 7`.
* read-only DB cross-check (`out/db-after-release.txt`):

      m_savings_account : 1|1000.310000|0.000000
      m_savings_account_transaction (id|type|amount|running_balance|release_id|is_reversed|is_reversal):
        1|1|1000.000000|1000.000000|0|f|f
        2|3|0.160000|1000.310000|0|f|f
        3|3|0.150000|1000.150000|0|f|f
        6|20|137.290000|863.020000|7|f|f
        7|21|137.290000|1000.310000|0|f|f

  `transaction_type_enum 21` is the oracle's `AMOUNT_RELEASE`. The hold row id 6
  carries `release_id_of_hold_amount = 7`; the account's
  `total_savings_amount_on_hold` is back to **0**, and `account_balance_derived`
  is **1000.31** throughout — before, during, and after the hold.

### Before the hold (observed)

* `GET /savingsaccounts/1?associations=all` -> 200
  (`out/savings-hold-before-account-raw.json`):
  `summary.accountBalance = 1000.31`, `summary.availableBalance = 1000.31`,
  `summary.totalDeposits = 1000.0`; transactions `(2, 0.16)`, `(3, 0.15)`, `(1, 1000.0)`;
  no hold transaction.
* read-only DB cross-check (`out/db-before.txt`): `m_savings_account : 1|1000.310000|`
  (held column null); the same three pre-hold transaction rows as the after-hold
  table above, without hold row id 6. Their dates are `(2, 2026-09-01 Interest
  posting)`, `(3, 2026-08-01 Interest posting)`, `(1, 2026-07-02 Deposit)`.

## Endpoints driven

| step | endpoint | status | artifact |
|---|---|---|---|
| account before | `GET /savingsaccounts/1?associations=all` | 200 | `out/savings-hold-before-account-raw.json` |
| transactions before | `GET /savingsaccounts/1?associations=transactions` | 200 | `out/savings-hold-before-transactions-raw.json` |
| **place hold** | `POST /savingsaccounts/1/transactions?command=holdAmount` | 200 `{"resourceId":6,...}` | `out/savings-hold-holdAmount-raw.json` (`req/savings-hold-holdAmount.json`) |
| account after hold | `GET /savingsaccounts/1?associations=all` | 200 | `out/savings-hold-after-hold-account-raw.json` |
| transactions after hold | `GET /savingsaccounts/1?associations=transactions` | 200 | `out/savings-hold-after-hold-transactions-raw.json` |
| **release hold** | `POST /savingsaccounts/1/transactions/6?command=releaseAmount` | 200 `{"resourceId":7,...}` | `out/savings-hold-releaseAmount-raw.json` (`req/savings-hold-releaseAmount.json`) |
| account after release | `GET /savingsaccounts/1?associations=all` | 200 | `out/savings-hold-after-release-account-raw.json` |
| transactions after release | `GET /savingsaccounts/1?associations=transactions` | 200 | `out/savings-hold-after-release-transactions-raw.json` |

Scripts: `bin/step01-before-and-hold.sh`, `bin/step02-release.sh`
(phase 2 is separate so the run could commit between the hold and the release).

### Request shapes (from the oracle's own source)

* hold — `POST .../transactions?command=holdAmount`. Required body fields:
  `transactionAmount` (positive) and `transactionDate` (not null); also
  `locale`/`dateFormat`. `reasonForBlock` is **required** by
  `SavingsAccountTransactionDataValidator.validateHoldAndAssembleForm()`
  (`SavingsAccountTransactionDataValidator.java:245-247`: `notBlank()` with no
  `ignoreIfNull`). `lienAllowed` is sent explicitly `false`; the non-lien branch
  only checks `amount <= withdrawable balance` (`:268-280`), here 137.29 <= 1000.31.
* release — `POST .../transactions/{transactionId}?command=releaseAmount`
  (`SavingsAccountTransactionsApiResource.java:375`). The transaction id is in
  the **path**; the release date is the business date, not a body field
  (`SavingsAccountTransactionDataValidator.validateReleaseAmountAndAssembleForm():335-336`).
  The only accepted body field is `externalId`; body must be non-blank, so the
  body is the empty JSON object `{}`.

## Byte-stability of `req/`

Every money value in `req/` is a quoted decimal string; the only non-string is
`lienAllowed:false`. No `json.dumps` of a parsed number, so no `100.00 -> 100.0`
class drift.

    req/savings-hold-holdAmount.json   {"transactionDate":"03 September 2026","transactionAmount":"137.29","locale":"en","dateFormat":"dd MMMM yyyy","lienAllowed":false,"reasonForBlock":"OH-HOLDCAP-R reference-oracle hold/release capture"}
    req/savings-hold-releaseAmount.json  {}    (2 bytes, no trailing newline)

## Safety

Tenant `gerege` only; SQL was read-only; nothing was SQL-inserted. No `.dump` is
committed. No `.go` file, guard, or `ErrNoGradedCapture` refusal was touched.

## What the grading run inherits

* Account **1**, client 5, product 1, business date 2026-09-03.
* Hold transaction id **6**, `transaction_type_enum` **20** (`AMOUNT_HOLD`),
  amount **137.29 MNT = 13729 minor units**.
* The rule's four limbs are all observable from `out/`:
  `available` 1000.31 -> 863.02 -> (release) back; `accountBalance` 1000.31 at
  every point; a hold row with `amountHold=true`.
* `summary.availableBalance = summary.accountBalance - held`; the held figure
  itself is in the DB evidence (`total_savings_amount_on_hold`) and the
  `AMOUNT_HOLD` transaction row.
