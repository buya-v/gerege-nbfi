package savings

import "fmt"

// TransactionEntryType is the in-account classification of a savings
// transaction's effect on the account balance. It is the Go port of Fineract's
// TransactionEntryType.
// [VERIFIED: TransactionEntryType.java:24-31 — CREDIT(1), DEBIT(2)].
//
// Unlike the two stored-value enums around it there is no nested table: the
// values are contiguous, so an iota with an explicit +1 base is the contract.
type TransactionEntryType int32

const (
	EntryCredit TransactionEntryType = iota + 1
	EntryDebit
)

var transactionEntryTypeName = map[TransactionEntryType]string{
	EntryCredit: "CREDIT",
	EntryDebit:  "DEBIT",
}

func (t TransactionEntryType) String() string {
	if n, ok := transactionEntryTypeName[t]; ok {
		return n
	}
	return fmt.Sprintf("TransactionEntryType(%d)", int32(t))
}

func (t TransactionEntryType) IsCredit() bool { return t == EntryCredit }
func (t TransactionEntryType) IsDebit() bool  { return t == EntryDebit }

// SavingsAccountTransactionType is m_savings_account_transaction.transaction_type_enum
// — Fineract's SavingsAccountTransactionType.
// [VERIFIED: SavingsAccountTransactionType.java:35-54]
//
//	INVALID(0)                       DEPOSIT(1)
//	WITHDRAWAL(2)                    INTEREST_POSTING(3)
//	WITHDRAWAL_FEE(4)                ANNUAL_FEE(5)
//	WAIVE_CHARGES(6)                 PAY_CHARGE(7)
//	DIVIDEND_PAYOUT(8)               ACCRUAL(10)
//	INITIATE_TRANSFER(12)            APPROVE_TRANSFER(13)
//	WITHDRAW_TRANSFER(14)            REJECT_TRANSFER(15)
//	WRITTEN_OFF(16)                  OVERDRAFT_INTEREST(17)
//	WITHHOLD_TAX(18)                 ESCHEAT(19)
//	AMOUNT_HOLD(20)                  AMOUNT_RELEASE(21)
//
// The values are NOT contiguous: there is no 9 or 11, and 20/21 are the
// hold/release pair that moves a ledger-side hold without moving the account's
// balance. An iota would silently misalign every value from ACCRUAL onward, so
// the explicit StoredValue table below is the contract.
type SavingsAccountTransactionType int32

const (
	TxnInvalid SavingsAccountTransactionType = iota
	TxnDeposit
	TxnWithdrawal
	TxnInterestPosting
	TxnWithdrawalFee
	TxnAnnualFee
	TxnWaiveCharges
	TxnPayCharge
	TxnDividendPayout
	TxnAccrual
	TxnInitiateTransfer
	TxnApproveTransfer
	TxnWithdrawTransfer
	TxnRejectTransfer
	TxnWrittenOff
	TxnOverdraftInterest
	TxnWithholdTax
	TxnEscheat
	TxnAmountHold
	TxnAmountRelease
)

var savingsTxnStoredValue = map[SavingsAccountTransactionType]int32{
	TxnInvalid:           0,
	TxnDeposit:           1,
	TxnWithdrawal:        2,
	TxnInterestPosting:   3,
	TxnWithdrawalFee:     4,
	TxnAnnualFee:         5,
	TxnWaiveCharges:      6,
	TxnPayCharge:         7,
	TxnDividendPayout:    8,
	TxnAccrual:           10,
	TxnInitiateTransfer:  12,
	TxnApproveTransfer:   13,
	TxnWithdrawTransfer:  14,
	TxnRejectTransfer:    15,
	TxnWrittenOff:        16,
	TxnOverdraftInterest: 17,
	TxnWithholdTax:       18,
	TxnEscheat:           19,
	TxnAmountHold:        20,
	TxnAmountRelease:     21,
}

var savingsTxnName = map[SavingsAccountTransactionType]string{
	TxnInvalid:           "INVALID",
	TxnDeposit:           "DEPOSIT",
	TxnWithdrawal:        "WITHDRAWAL",
	TxnInterestPosting:   "INTEREST_POSTING",
	TxnWithdrawalFee:     "WITHDRAWAL_FEE",
	TxnAnnualFee:         "ANNUAL_FEE",
	TxnWaiveCharges:      "WAIVE_CHARGES",
	TxnPayCharge:         "PAY_CHARGE",
	TxnDividendPayout:    "DIVIDEND_PAYOUT",
	TxnAccrual:           "ACCRUAL",
	TxnInitiateTransfer:  "INITIATE_TRANSFER",
	TxnApproveTransfer:   "APPROVE_TRANSFER",
	TxnWithdrawTransfer:  "WITHDRAW_TRANSFER",
	TxnRejectTransfer:    "REJECT_TRANSFER",
	TxnWrittenOff:        "WRITTEN_OFF",
	TxnOverdraftInterest: "OVERDRAFT_INTEREST",
	TxnWithholdTax:       "WITHHOLD_TAX",
	TxnEscheat:           "ESCHEAT",
	TxnAmountHold:        "AMOUNT_HOLD",
	TxnAmountRelease:     "AMOUNT_RELEASE",
}

var savingsTxnFromStored = map[int32]SavingsAccountTransactionType{}

// StoredValue returns m_savings_account_transaction.transaction_type_enum.
func (t SavingsAccountTransactionType) StoredValue() int32 {
	v, ok := savingsTxnStoredValue[t]
	if !ok {
		panic(fmt.Sprintf("savings: unknown SavingsAccountTransactionType %d", int32(t)))
	}
	return v
}

func (t SavingsAccountTransactionType) String() string {
	if n, ok := savingsTxnName[t]; ok {
		return n
	}
	return fmt.Sprintf("SavingsAccountTransactionType(%d)", int32(t))
}

// SavingsAccountTransactionTypeFromStoredValue decodes
// m_savings_account_transaction.transaction_type_enum. ok is false outside the
// legal values, matching SavingsAccountTransactionType.fromInt's INVALID
// fallback [VERIFIED: SavingsAccountTransactionType.java:50-93].
func SavingsAccountTransactionTypeFromStoredValue(v int32) (SavingsAccountTransactionType, bool) {
	t, ok := savingsTxnFromStored[v]
	return t, ok
}

// IsAmountHold / IsAmountRelease / IsEscheat are the three single-value
// predicates the folded classification below subtracts with
// [VERIFIED: SavingsAccountTransactionType.java:164-174 — isEscheat(),
// isAmountOnHold(), isAmountRelease()].
func (t SavingsAccountTransactionType) IsAmountHold() bool    { return t == TxnAmountHold }
func (t SavingsAccountTransactionType) IsAmountRelease() bool { return t == TxnAmountRelease }
func (t SavingsAccountTransactionType) IsEscheat() bool       { return t == TxnEscheat }

// EntryType returns the RAW third constructor argument of the oracle's enum —
// Fineract's Lombok-generated `getEntryType()`
// [VERIFIED: SavingsAccountTransactionType.java:36-54, :62-63].
//
// ⚠ THIS IS NOT THE CLASSIFICATION ANY FINERACT BALANCE DERIVATION FOLDS ON,
// AND READING IT AS ONE WAS THE ROOT DEFECT T515 REPAIRS. Fineract never folds
// on the raw field: every caller goes through `isCredit()`/`isDebit()` below,
// which subtract three types from it. See those two methods.
//
// EIGHT types pass `null` as that argument and so carry no entry type,
// returning the zero TransactionEntryType: INVALID(0), WAIVE_CHARGES(6),
// ACCRUAL(10), INITIATE_TRANSFER(12), APPROVE_TRANSFER(13),
// WITHDRAW_TRANSFER(14), REJECT_TRANSFER(15) and WRITTEN_OFF(16). INVALID(0)
// belongs on that list — it is the value FromStoredValue refuses, but a
// zero-valued SavingsAccountTransactionType is the Go zero value and so is what
// an uninitialised struct carries, which makes it the one that most needs to
// fold to nothing rather than to a credit.
func (t SavingsAccountTransactionType) EntryType() TransactionEntryType {
	switch t {
	case TxnDeposit, TxnInterestPosting, TxnDividendPayout, TxnAmountRelease:
		return EntryCredit
	case TxnWithdrawal, TxnWithdrawalFee, TxnAnnualFee, TxnPayCharge,
		TxnOverdraftInterest, TxnWithholdTax, TxnEscheat, TxnAmountHold:
		return EntryDebit
	default:
		return 0
	}
}

// IsCreditEntryType / IsDebitEntryType test the RAW entry-type field, and are
// the port of the oracle's methods of the same names
// [VERIFIED: SavingsAccountTransactionType.java:83-89]:
//
//	isCreditEntryType() = entryType != null && entryType.isCredit()
//	isDebitEntryType()  = entryType != null && entryType.isDebit()
//
// The `!= null` guard is the zero TransactionEntryType here: EntryCredit(1) and
// EntryDebit(2) are the only non-zero values, so a type with no entry type
// answers false to both, exactly as Fineract's null does.
//
// These are NOT the balance classification. They are exported because the
// folded IsCredit/IsDebit below are defined in terms of them, and because a
// reader comparing this file to the Java needs both levels visible to see that
// the fold is present.
func (t SavingsAccountTransactionType) IsCreditEntryType() bool {
	return t.EntryType().IsCredit()
}

// IsDebitEntryType — see IsCreditEntryType.
func (t SavingsAccountTransactionType) IsDebitEntryType() bool {
	return t.EntryType().IsDebit()
}

// IsCredit and IsDebit are THE type-level balance classification — the third
// and final arrow of Fineract's chain, and the one this port previously
// stopped short of. Verbatim, with the oracle's own inline comments
// [VERIFIED: SavingsAccountTransactionType.java:180-188]:
//
//	public boolean isCredit() {
//	    // AMOUNT_RELEASE is not credit, because the account balance is not changed
//	    return isCreditEntryType() && !isAmountRelease();
//	}
//
//	public boolean isDebit() {
//	    // AMOUNT_HOLD, ESCHEAT are not debit, because the account balance is not changed
//	    return isDebitEntryType() && !isAmountOnHold() && !isEscheat();
//	}
//
// # WHY THIS IS THE WHOLE OF T515
//
// The chain is THREE calls deep and T510 walked two of them:
//
//	SavingsAccountTransaction.isCredit()   = isCreditType() && !isReversed() && !isReversalTransaction()
//	SavingsAccountTransaction.isCreditType() = getTransactionType().isCredit()   <- T510 stopped here
//	SavingsAccountTransactionType.isCredit() = isCreditEntryType() && !isAmountRelease()
//
// [VERIFIED: SavingsAccountTransaction.java:786-799 for the first two lines;
// SavingsAccountTransactionType.java:180-188 for the third.] Because the Go
// port bound its classification to the RAW entry-type field, AMOUNT_HOLD and
// AMOUNT_RELEASE came back as debit/credit and had to be excluded by a
// hand-maintained list at each fold site — and ESCHEAT, which the oracle
// excludes by name on the very same line as AMOUNT_HOLD, was missing from that
// list. The oracle had implemented "holds do not move the posted balance" all
// along; the port re-derived it, got it right for two types and wrong for the
// third.
//
// # THE ORACLE SAYS THE SAME THING TWICE, AND IT WAS OBSERVED, NOT ARGUED
//
// [VERIFIED: live oracle capture, tenant `default`, Fineract @ 426a23544,
// PostgreSQL `gerege-oracle-db`/`fineract_default`, 2026-09-03 — savings
// account 2, product 2 (MNT, nominal_annual_interest_rate 0.000000, dormancy
// tracking active), escheated by the stock `Update Savings Dormant Accounts`
// job (jobId 21), which is the only caller of SavingsAccount.escheat.
//
// The instance runs tenant `default` on Asia/Kolkata with
// `c_configuration.rounding-mode = 6` (HALF_EVEN), not the ratified
// (19, HALF_UP) / Asia-Ulaanbaatar — so it is **[UNVERIFIED at the ratified
// setting]** and is not a parity vector. It is decisive anyway for the question
// asked here, which is whether an ESCHEAT row moves a balance AT ALL: the two
// amounts are exact whole-unit quantities, no midpoint arises for a rounding
// mode to decide, and the observation is that both stored balances are
// numerically UNCHANGED by a 500,000.00 escheat:
//
//	m_savings_account_transaction
//	  id 12  type  1 (DEPOSIT)  amount 500000.000000  running_balance_derived 500000.000000
//	  id 13  type 19 (ESCHEAT)  amount 500000.000000  running_balance_derived 500000.000000
//	m_savings_account
//	  id 2   status_enum 600 (CLOSED)  sub_status_enum 300 (ESCHEAT)
//	         account_balance_derived 500000.000000
//
// Both of Fineract's stored balances are UNMOVED by an ESCHEAT for the whole
// balance. The running balance did not move because ESCHEAT matches NEITHER
// branch of recalculateDailyBalances — isDebit() excludes it by name and the
// loop carries an explicit `|| transaction.isAmountOnHold()` term to re-admit
// holds but NO `|| isEscheat()` term [VERIFIED: SavingsAccount.java:902,912].
// The account balance did not move because ESCHEAT appears in none of the nine
// terms of updateSummary [VERIFIED: SavingsAccountSummary.java:96-112] and
// falls to `default: break;` in updateSummaryWithPivotConfig, and none of the
// thirteen calculators of SavingsAccountTransactionSummaryWrapper mentions it
// [VERIFIED: that file read end to end — it names no transaction type outside
// DEPOSIT, DIVIDEND_PAYOUT, WITHDRAWAL, INTEREST_POSTING, WITHDRAWAL_FEE,
// ANNUAL_FEE, the charge/waiver pairs, OVERDRAFT_INTEREST and WITHHOLD_TAX].
//
// So there is no contradiction in Fineract to choose sides in, and no gate to
// raise: escheat moves nothing, in both of the oracle's derivations and in the
// oracle's own running instance. Gates G-25 and G-27 were deleted on this
// evidence.
func (t SavingsAccountTransactionType) IsCredit() bool {
	return t.IsCreditEntryType() && !t.IsAmountRelease()
}

// IsDebit — see IsCredit.
func (t SavingsAccountTransactionType) IsDebit() bool {
	return t.IsDebitEntryType() && !t.IsAmountHold() && !t.IsEscheat()
}

func init() {
	for t, v := range savingsTxnStoredValue {
		if _, dup := savingsTxnFromStored[v]; dup {
			panic(fmt.Sprintf("savings: transaction type encode table is not injective at %d", v))
		}
		savingsTxnFromStored[v] = t
	}
}
