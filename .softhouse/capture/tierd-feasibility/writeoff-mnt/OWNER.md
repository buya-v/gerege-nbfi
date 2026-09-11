# OWNER — writeoff-mnt capture (OH-TIERD10-CA)

Replay of `fineract-e2e-tests-runner/src/test/resources/features/LoanWriteOff.feature`
with the Feign capture on, in the throwaway reference-oracle tenant `tierd` (MNT).

## Ownership rule

Cucumber ran scenarios sequentially in file order (`--max-workers=1`) and each scenario
creates exactly one loan; loans are numbered by the resourceId returned by `POST /loans`.
Therefore **scenario S*k* owns loan *k*** and **every body under `loans/loan-*k*/`**.
This is corroborated, not merely assumed:
- 12 scenarios, 12 loans, one `create` per loan (counts agree);
- the `clientId` in each `loan-<k>-create-request.json` equals *k*, so the loan the
  runner created for scenario *k* is the loan numbered *k*;
- the product each scenario names in the feature matches its loan's `loanProductName`
  (table below);
- `manifest-writeoff.json` enumerates every file with `loan_id`, `source_line`, `url`,
  `sha256` and the oracle's HTTP status.

`manifest-writeoff.json` (all 12 loans, `committed: true` on each) and
`manifest-writeoff-passed.json` are identical here because **all 12 scenarios passed**.

## Scenario -> loan -> read-backs

Read-back files are the `detail-*` bodies (loan detail / associations / transactions);
command bodies (`create`/`approve`/`disburse`/`repayment`/`charge-off`/`writeoff`
request+response) are captured alongside so a copy is self-contained. Exact names are in
the manifest. Amounts in these bodies are the oracle's verbatim text, never re-serialised.

| scenario | tag | feature line | loan | product | read-backs | committed files | result |
|----------|-----|-------------:|-----:|---------|-----------:|----------------:|--------|
| S1 | C2934 | 5 | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 11 | 22 | PASSED |
| S2 | C2935 | 25 | 2 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 10 | 21 | PASSED |
| S3 | C2936 | 45 | 3 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 11 | 22 | PASSED |
| S4 | C4006 | 64 | 4 | `LP1_INTEREST_FLAT` | 14 | 27 | PASSED |
| S5 | C4007 | 100 | 5 | `LP1_INTEREST_FLAT` | 12 | 23 | PASSED |
| S6 | C4010 | 126 | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1` | 17 | 26 | PASSED |
| S7 | C4011 | 193 | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` | 20 | 31 | PASSED |
| S8 | C4012 | 281 | 8 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON` | 13 | 26 | PASSED |
| S9 | C4013 | 330 | 9 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 15 | 30 | PASSED |
| S10 | C4111 | 368 | 10 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP` | 11 | 18 | PASSED |
| S11 | C4112 | 401 | 11 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP` | 11 | 18 | PASSED |
| S12 | C4113 | 434 | 12 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` | 11 | 18 | PASSED |

Total: 12 scenarios / 12 loans / 282 bodies, 282 committed.

## Scenario outcomes

All 12 scenarios passed; 0 failed. No scenario in this capture failed, so there is no
failed-scenario exclusion to make.

- **S1 C2934 — PASSED.** `As a user I want to do Write-off a loan and verify that undo repayment post write-off results in error`
- **S2 C2935 — PASSED.** `As a user I want to do Write-off a loan and verify that backdate repayment post write-off results in error`
- **S3 C2936 — PASSED.** `As a user I want to do Write-off a loan and verify that undo write-off results in error`
- **S4 C4006 — PASSED.** `Verify accounting journal entries are not duplicated during write-off in case the cumulative loan was already charged-off`
- **S5 C4007 — PASSED.** `Verify accounting journal entries during write-off when cumulative loan was not charged-off before`
- **S6 C4010 — PASSED.** `Verify accounting journal entries are not duplicated during write-off in case the progressive loan was already charged-off`
- **S7 C4011 — PASSED.** `Verify accounting journal entries are not duplicated during write-off in case the progressive loan was already charged-off after repayment`
- **S8 C4012 — PASSED.** `Verify accounting journal entries during write-off in case the progressive loan was already charged-off and then charge-off is undone`
- **S9 C4013 — PASSED.** `Verify accounting journal entries are not duplicated during write-off in case the progressive reverse-replayed fraud loan was charged-off`
- **S10 C4111 — PASSED.** `Verify GL entries for Write Off reason mapping - UC1: Write off, LP with write off reason mapping, NO write off reason to expense account`
- **S11 C4112 — PASSED.** `Verify GL entries for Write Off reason mapping - UC2: Write off, LP with write off reason mapping, with write off reason: Bad Debt`
- **S12 C4113 — PASSED.** `Verify GL entries for Write Off reason mapping - UC3: Write off, LP without write off reason mapping, with write off reason: Bad Debt`

## `/journalentries` and product mappings (the type join)

`journalentries/loan-<id>/` holds the runner's `GET /journalentries?transactionId=L<id>`
responses, extracted from the raw Feign log by `extract-journalentries.py` (copied from
chargeoff-mnt; logic unchanged): **19** responses over **9** loans, sha256 in
`journalentries-manifest.json`. Every leg's `entityId` is its directory's loan.
Re-hashed after writing: all 19 responses match their manifest sha256.

Every leg carries only `transactionId` = `L<loanTransactionId>`; the transaction **type**
comes only from the loan read-backs under `loans/`
(`loans/loan-<id>/loan-<id>-detail-associations-transactions-*.json`,
`transactions[].id -> transactions[].type.code`). The join is in
`journalentry-type-join.json` / `.md`. **64 legs, 0 unmatched.**

| transaction type | value | loans | transactions | legs |
|------------------|-------|-------|--------------|-----:|
| `loanTransactionType.chargeOff` | Charge-off | 4, 6, 7, 8, 9 | L15, L21, L26, L30, L35, L36 | 33 |
| `loanTransactionType.disbursement` | Disbursement | 4, 5 | L13, L17 | 4 |
| `loanTransactionType.writeOff` | Close (as written-off) | 4, 5, 6, 7, 8, 9, 10, 11, 12 | L16, L18, L22, L27, L31, L37, L39, L41, L43 | 27 |

### `writeOff` on a charged-off loan — `createJournalEntriesForWriteOffsWhenLoanIsChargedOff`

**Yes — observed.** 4 of the 9 `writeOff` transactions reverse a charge-off: their
legs CREDIT the Credit Loss/Bad Debt accounts that the earlier `chargeOff` transaction
debited (and DEBIT `Written off`), instead of crediting Loans Receivable / Interest-Fee
Receivable as an ordinary write-off does. The type join names the branch
`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`
[AccrualBasedAccountingProcessorForLoan.java:1616] for these.

| loan | `writeOff` tx | date | amount (minor) | charged-off loan |
|-----:|---------------|------|---------------:|------------------|
| 4 | L16 | 2023-3-1 | 114300 | yes |
| 6 | L22 | 2024-3-1 | 101222 | yes |
| 7 | L27 | 2024-3-1 | 8504 | yes |
| 9 | L37 | 2024-2-3 | 75000 | yes |

### loan 4, `writeOff` `L16` (2023-3-1), 114300 minor

| entry | account code | account name | amount (minor) |
|-------|--------------|--------------|---------------:|
| CREDIT | 744007 | Credit Loss/Bad Debt | 100000 |
| CREDIT | 404001 | Interest Income Charge Off | 3000 |
| CREDIT | 404008 | Fee Charge Off | 11300 |
| DEBIT | e4 | Written off | 114300 |

### loan 6, `writeOff` `L22` (2024-3-1), 101222 minor

| entry | account code | account name | amount (minor) |
|-------|--------------|--------------|---------------:|
| CREDIT | 744007 | Credit Loss/Bad Debt | 100000 |
| CREDIT | 404001 | Interest Income Charge Off | 1222 |
| DEBIT | e4 | Written off | 101222 |

### loan 7, `writeOff` `L27` (2024-3-1), 8504 minor

| entry | account code | account name | amount (minor) |
|-------|--------------|--------------|---------------:|
| CREDIT | 744007 | Credit Loss/Bad Debt | 8357 |
| CREDIT | 404001 | Interest Income Charge Off | 147 |
| DEBIT | e4 | Written off | 8504 |

### loan 9, `writeOff` `L37` (2024-2-3), 75000 minor

| entry | account code | account name | amount (minor) |
|-------|--------------|--------------|---------------:|
| CREDIT | 744037 | Credit Loss/Bad Debt-Fraud | 75000 |
| DEBIT | e4 | Written off | 75000 |

The remaining `writeOff` transactions were ordinary write-offs (no charge-off to
reverse): loans 5, 8, 10, 11, 12.
Loan 8 is the instructive case: its transaction list contains a `chargeOff` (`L30`),
but the charge-off was undone, so its `writeOff` (`L31`) credits Loans Receivable /
Interest-Fee Receivable — the join, not the mere presence of a chargeOff, decides.

### Accounting shapes observed

| shape | `writeOff` txs | loans |
|-------|---------------:|-------|
| charged-off reversal: C Credit Loss/Bad Debt, D Written off | 4 | 4, 6, 7, 9 |
| ordinary: C Loans Receivable + Interest/Fee Receivable, D Written off | 4 | 5, 8, 10, 12 |
| non-charged-off debit to Credit Loss (write-off reason map) | 1 | 11 |

### Product mappings

`product-mappings/create-request-<name>.json` holds the accepted create request of every
product the loans use (7 products), read from THIS replay's log by
`extract-product-mappings.py` (account ids differ between replays, each throwaway seeds
its own GL). sha256 in `product-mappings/manifest.json`; re-hashed: all 7 match.

- `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` — `product-mappings/create-request-LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION.json`
- `LP1_INTEREST_FLAT` — `product-mappings/create-request-LP1_INTEREST_FLAT.json`
- `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1` — `product-mappings/create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1.json`
- `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` — `product-mappings/create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF.json`
- `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON` — `product-mappings/create-request-LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON.json`
- `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP` — `product-mappings/create-request-LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP.json`
- `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` — `product-mappings/create-request-LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP.json`

