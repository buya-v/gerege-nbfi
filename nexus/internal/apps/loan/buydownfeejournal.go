package loan

import "fmt"

// BuyDownFeeAccountMapping is the GL account each buy-down-fee leg slot
// resolves to for one loan product. The processor selects the debit slot as
// AccrualAccountsForLoan.BUY_DOWN_EXPENSE when the loan product's
// merchantBuyDownFee is set, else AccrualAccountsForLoan.FUND_SOURCE (resolved
// through the transaction's payment channel), and always credits
// AccrualAccountsForLoan.DEFERRED_INCOME_LIABILITY [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:530-551, pinned commit
// 426a23544].
type BuyDownFeeAccountMapping struct {
	// FundSource is the resolved AccrualAccountsForLoan.FUND_SOURCE slot: the
	// payment-channel account when the transaction's paymentTypeId has one, else
	// the product's fund source. It is debited with the amount on a
	// NON-merchant product.
	FundSource string
	// BuyDownExpense is the AccrualAccountsForLoan.BUY_DOWN_EXPENSE slot, debited
	// with the amount on a merchant product. A NON-merchant product has no
	// buy-down expense account, so it is empty there.
	BuyDownExpense string
	// DeferredIncomeLiability is the
	// AccrualAccountsForLoan.DEFERRED_INCOME_LIABILITY slot, always credited with
	// the amount.
	DeferredIncomeLiability string
}

// CreateBuyDownFeeJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForBuyDownFee
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:530-551, pinned commit
// 426a23544]. It is a pure function: the transaction id, an amount (the
// buy-down fee the product recognized), the loan's merchantBuyDownFee fact and
// the product's slot->account mapping in; journal-entry legs out — no clock, no
// I/O, no stored balance, integer minor units only.
//
// When the amount is > 0 it posts exactly two legs through the processor's
// helper.createJournalEntriesForLoan(debit, credit):
//
//  1. DEBIT the selected account with the amount — BUY_DOWN_EXPENSE when the
//     product is a merchant product, else the resolved FUND_SOURCE;
//  2. CREDIT DEFERRED_INCOME_LIABILITY with the amount.
//
// The debit is posted first, then the credit. A non-positive amount posts
// nothing, matching MathUtil.isGreaterThanZero.
//
// THE OBSERVED DOMAIN IS NARROW AND THIS PORT REFUSES ANYTHING OUTSIDE IT, by
// construction rather than by guessing: a negative amount is refused, and a
// positive amount with no debit account or no deferred-income account is
// refused. Because a NON-merchant product carries no buy-down expense account,
// a merchant=true input whose mapping has no buy-down expense account is
// refused rather than falling back to the fund source.
func CreateBuyDownFeeJournalEntryLegs(transactionID string, amount MinorUnits, merchant bool, mapping BuyDownFeeAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: buy-down-fee journal entries need a transaction id")
	}
	if amount < 0 {
		return nil, fmt.Errorf("loan: buy-down fee carries a negative amount %d", amount)
	}
	if amount == 0 {
		return nil, nil
	}

	debit := mapping.FundSource
	if merchant {
		debit = mapping.BuyDownExpense
	}
	if debit == "" {
		return nil, fmt.Errorf("loan: buy-down fee amount %d has no debit account (merchant %t)", amount, merchant)
	}
	if mapping.DeferredIncomeLiability == "" {
		return nil, fmt.Errorf("loan: buy-down fee amount %d has no deferred-income account", amount)
	}

	return []JournalEntryLeg{
		{
			TransactionID: transactionID,
			Account:       debit,
			Side:          JournalEntryDebit,
			Amount:        amount,
		},
		{
			TransactionID: transactionID,
			Account:       mapping.DeferredIncomeLiability,
			Side:          JournalEntryCredit,
			Amount:        amount,
		},
	}, nil
}
