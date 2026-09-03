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
// [VERIFIED: SavingsAccountTransactionType.java:24-47]
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

// IsAmountHold / IsAmountRelease / IsEscheat are the single-value predicates the
// folded classification below subtracts with
// [VERIFIED: SavingsAccountTransactionType.java:96-102, :164-174].
func (t SavingsAccountTransactionType) IsAmountHold() bool    { return t == TxnAmountHold }
func (t SavingsAccountTransactionType) IsAmountRelease() bool { return t == TxnAmountRelease }
func (t SavingsAccountTransactionType) IsEscheat() bool       { return t == TxnEscheat }

// EntryType returns the in-account CREDIT/DEBIT classification encoded on the
// enum's entryType field, mirroring the oracle's third constructor argument
// [VERIFIED: SavingsAccountTransactionType.java:36-54]. The balance-neutral and
// non-posting types (WAIVE_CHARGES, ACCRUAL, the transfer sub-states and
// WRITTEN_OFF) carry no entry type and return the zero TransactionEntryType.
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
// answers false to both, exactly as Fineract's null does. These are NOT the
// balance classification; the folded IsCredit/IsDebit below are defined in
// terms of them.
func (t SavingsAccountTransactionType) IsCreditEntryType() bool {
	return t.EntryType().IsCredit()
}

// IsDebitEntryType — see IsCreditEntryType.
func (t SavingsAccountTransactionType) IsDebitEntryType() bool {
	return t.EntryType().IsDebit()
}

// IsCredit and IsDebit are THE type-level balance classification — the third
// arrow of Fineract's chain, and the one this port previously stopped short of.
// Verbatim, with the oracle's own inline comments
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
// The chain is THREE calls deep. Fineract never folds on the raw entry-type
// field: every balance derivation goes through these two, which subtract the
// three balance-neutral types (AMOUNT_HOLD, AMOUNT_RELEASE, ESCHEAT). Binding a
// fold to EntryType() instead treats a hold as a debit, a release as a credit,
// and an escheat as a debit — which is how a port re-derives "a hold does not
// move the posted balance" by hand, gets it right for two types, and wrong for
// the third. ESCHEAT is excluded by the oracle on the same line as AMOUNT_HOLD.
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
