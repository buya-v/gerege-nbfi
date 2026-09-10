# OH-GL-T evidence — byte-stable re-capture, and the kills each new vector scores

## 1. Oracle state verified live (read-only GETs), 2026-09-10

All values below came from `curl -sk` GETs against
`https://localhost:8443/fineract-provider/api/v1` (tenant `gerege`), saved under `/tmp/`
during this session. Nothing was written by the verification.

| fact | observed | source |
|---|---|---|
| product 3 `OHLGR-Accrual-Loan`, `ACCRUAL PERIODIC` | id 3, accountingRule id 3 `ACCRUAL PERIODIC` | `GET /loanproducts/3` |
| products 1 and 2 stay `NONE` | id 1 `T22 mode probe halfcent` NONE; id 2 `SEED-Probe-Loan` NONE | `GET /loanproducts/1,2` |
| GL accounts named `OHLGR-*` | **12** present, ids 5-16 (TASK.md said 11 — MORE than expected, not missing) | `GET /glaccounts`, `out/glaccounts-after-raw.json` |
| loans 10 and 11 Active | 10 `OHGLR-L01` Active; 11 `OHGLR-L02` Active | `GET /loans/10,11` |
| loan 10 fee 0, penalty 57.00 | feeChargesOutstanding 0.0, penaltyChargesOutstanding 57.0, totalOutstanding 106675.53 | `out/loan-10-raw.json` |
| loan 11 fee 100.00, penalty 57.00 | feeChargesOutstanding 100.0, penaltyChargesOutstanding 57.0, totalOutstanding 106775.53 | `GET /loans/11` |
| loan 12 `OHLGT-L03` fee 100.00, penalty 57.00 | feeChargesOutstanding 100.0, penaltyChargesOutstanding 57.0, totalOutstanding 106775.53 | `out/loan-12-raw.json` |
| business date 2026-09-02 | loan 12 `overdueSinceDate` absent; SDD charges still outstanding (loan created on business date 2026-09-02) | `out/loan-12-raw.json`, `bin/step02-loan.sh` |
| COB step `EXTERNAL_ASSET_OWNER_TRANSFER` at order 7 | order 7, alongside orders 1-7 | `GET /jobs/LOAN_CLOSE_OF_BUSINESS/steps` |

## 2. The re-capture is byte-stable (the P-25 defect this rig fixes)

Every reference request body under `req/` was re-parsed and re-serialised token by token:

    req files=5  numeric tokens=26  NOT byte-stable=0

The amounts are written as integers `100` (fee) and `57` (penalty); an integer is its own
shortest round-trip repr and survives the one genuine Java `double` on the POST /charges
path (`private double amount`, T186 §2.4). `100.00` would re-emit as `100.0` — that was the
reverted OH-GL-R defect. The full conformance run reports:

    wire-float round-trip guard — selftest OK, 13 cases
    CENSUS float-shaped tokens PRESENT 380, ALTERED by a binary-double round trip 0

## 3. Kills each new vector scores (instrument proven live in the same session)

    bash .softhouse/briefs/tools/kills.sh loan loan-wrong-summary-drops-fee        -> 1
    bash .softhouse/briefs/tools/kills.sh loan loan-wrong-summary-drops-penalty    -> 2
    # controls in the same context, same session:
    bash .softhouse/briefs/tools/kills.sh loan loan-wrong-summary-drops-principal  -> 7
    bash .softhouse/briefs/tools/kills.sh loan loan-wrong-summary-interest-not-outstanding -> 6

* `loan-wrong-summary-drops-fee` kills exactly `LN-L07` (fee 100.00 non-zero; every other
  summary vector in the corpus has fee 0, where dropping the term is invisible). This is
  the vector that closes `F-2026-09-09`.
* `loan-wrong-summary-drops-penalty` kills `LN-L07` (penalty 57.00) **and** `LN-L08`
  (fee 0, penalty 57.00) — the differently-shaped observation that discriminates the
  penalty term alone.
* The two controls kill 7 and 6, proving the instrument was live and the new vectors are
  in its corpus. A returned zero would have been a genuine measurement, not a dead tool.

## 4. Relationship to the reverted OH-GL-R salvage

The reverted run's artifacts are at
`/Users/buv/gerege-oracle-snapshots/gl-accounting-surface-evidence/`; its `bin/step0*.sh`
were the starting point. The defect was narrow (a non-byte-stable numeric token) and is
fixed by writing integer tokens, not by deleting `req/`. Both the request bytes and the
oracle responses commit.
