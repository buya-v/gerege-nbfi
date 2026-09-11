package loan

import "fmt"

// AccrualPortions is the money an accrual or accrual-adjustment transaction
// accrues per ledger slot, in integer minor units. It mirrors the
// interestPortion, feeChargesPortion and penaltyChargesPortion the loan
// read-back carries on the transaction; there is no principal or overpayment
// field because createJournalEntriesForAccruals posts none.
type AccrualPortions struct {
	Interest MinorUnits
	Fee      MinorUnits
	Penalty  MinorUnits
}

// AccrualAccountMapping is the resolved GL account each accrual slot posts to
// for one loan product. The receivable slots are the product's
// INTEREST_RECEIVABLE, FEES_RECEIVABLE and PENALTIES_RECEIVABLE accounts; the
// income slots are INTEREST_ON_LOANS, INCOME_FROM_FEES and
// INCOME_FROM_PENALTIES. The port takes them resolved: it does not read the
// product, a tax branch or any charge-specific mapping.
type AccrualAccountMapping struct {
	ReceivableInterest string
	ReceivableFee      string
	ReceivablePenalty  string
	InterestOnLoans    string
	IncomeFromFee      string
	IncomeFromPenalty  string
}

// CreateAccrualJournalEntryLegs ports the observed, tax-free shape of
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForAccruals
// [AccrualBasedAccountingProcessorForLoan.java:2015-2087, dispatch :79-81,
// pinned commit 426a23544] for the transaction types ACCRUAL and
// ACCRUAL_ADJUSTMENT.
//
// The interest group posts first, when interest > 0: an accrual DEBITs
// INTEREST_RECEIVABLE then CREDITs INTEREST_ON_LOANS, and an adjustment posts
// the SAME pair with the accounts swapped (DEBIT INTEREST_ON_LOANS, CREDIT
// INTEREST_RECEIVABLE). Both go through helper.createJournalEntriesForLoan,
// which posts the debit first.
//
// The fee group then the penalty group follow, each only when its portion > 0,
// through helper.createJournalEntriesForLoanCharges
// [AccountingProcessorHelper.java:393-435], which posts the CREDIT first and
// the DEBIT second: an accrual CREDITs INCOME_FROM_FEES and DEBITs
// FEES_RECEIVABLE (penalties: INCOME_FROM_PENALTIES and PENALTIES_RECEIVABLE),
// and an adjustment swaps the sides. The fee and penalty groups are SEPARATE
// helper calls, so they never merge with each other even when they name the
// same accounts.
//
// The tax branch and the charge-specific GL mappings are NOT observed and are
// not expressible here: the port takes resolved product accounts and no tax or
// charge input. A negative portion, or a positive portion with no account for
// the side it needs, is refused rather than posted. Every amount is an integer
// MinorUnits; no float is involved.
func CreateAccrualJournalEntryLegs(transactionID string, adjustment bool, portions AccrualPortions, mapping AccrualAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: accrual journal entries need a transaction id")
	}
	if portions.Interest < 0 || portions.Fee < 0 || portions.Penalty < 0 {
		return nil, fmt.Errorf(
			"loan: accrual journal entries refused a negative portion (interest %d, fee %d, penalty %d)",
			portions.Interest, portions.Fee, portions.Penalty)
	}

	legs := make([]JournalEntryLeg, 0, 6)

	// Interest: helper.createJournalEntriesForLoan posts debit first, and the
	// adjustment swaps which account is the debit.
	if portions.Interest > 0 {
		debit, credit := mapping.ReceivableInterest, mapping.InterestOnLoans
		if adjustment {
			debit, credit = mapping.InterestOnLoans, mapping.ReceivableInterest
		}
		if debit == "" {
			return nil, fmt.Errorf("loan: interest accrual %d has no debit account", portions.Interest)
		}
		if credit == "" {
			return nil, fmt.Errorf("loan: interest accrual %d has no credit account", portions.Interest)
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: transactionID, Account: debit, Side: JournalEntryDebit, Amount: portions.Interest},
			JournalEntryLeg{TransactionID: transactionID, Account: credit, Side: JournalEntryCredit, Amount: portions.Interest},
		)
	}

	// Fees: helper.createJournalEntriesForLoanCharges posts CREDIT first, then
	// the DEBIT. The adjustment swaps which account is the credit. This group
	// is a separate helper call from the penalty group below, so they never
	// merge.
	if portions.Fee > 0 {
		debit, credit := mapping.ReceivableFee, mapping.IncomeFromFee
		if adjustment {
			debit, credit = mapping.IncomeFromFee, mapping.ReceivableFee
		}
		if credit == "" {
			return nil, fmt.Errorf("loan: fee accrual %d has no credit account", portions.Fee)
		}
		if debit == "" {
			return nil, fmt.Errorf("loan: fee accrual %d has no debit account", portions.Fee)
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: transactionID, Account: credit, Side: JournalEntryCredit, Amount: portions.Fee},
			JournalEntryLeg{TransactionID: transactionID, Account: debit, Side: JournalEntryDebit, Amount: portions.Fee},
		)
	}

	// Penalties: the same charge helper, CREDIT first then DEBIT, its own
	// separate call.
	if portions.Penalty > 0 {
		debit, credit := mapping.ReceivablePenalty, mapping.IncomeFromPenalty
		if adjustment {
			debit, credit = mapping.IncomeFromPenalty, mapping.ReceivablePenalty
		}
		if credit == "" {
			return nil, fmt.Errorf("loan: penalty accrual %d has no credit account", portions.Penalty)
		}
		if debit == "" {
			return nil, fmt.Errorf("loan: penalty accrual %d has no debit account", portions.Penalty)
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: transactionID, Account: credit, Side: JournalEntryCredit, Amount: portions.Penalty},
			JournalEntryLeg{TransactionID: transactionID, Account: debit, Side: JournalEntryDebit, Amount: portions.Penalty},
		)
	}

	return legs, nil
}
