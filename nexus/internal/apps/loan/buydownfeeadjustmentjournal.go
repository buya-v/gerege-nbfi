package loan

import "fmt"

// BuyDownFeeAdjustmentAccountMapping is the GL account each buy-down-fee
// ADJUSTMENT leg slot resolves to for one loan product. The adjustment is the
// mirror of the buy-down fee: it always DEBITS
// AccrualAccountsForLoan.DEFERRED_INCOME_LIABILITY and CREDITS the slot selected
// by the loan product's merchantBuyDownFee — AccrualAccountsForLoan.BUY_DOWN_EXPENSE
// when it is set, else AccrualAccountsForLoan.FUND_SOURCE (resolved through the
// transaction's payment channel) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:552-575, pinned commit 426a23544].
type BuyDownFeeAdjustmentAccountMapping struct {
	// DeferredIncomeLiability is the
	// AccrualAccountsForLoan.DEFERRED_INCOME_LIABILITY slot, always debited with
	// the amount.
	DeferredIncomeLiability string
	// BuyDownExpense is the AccrualAccountsForLoan.BUY_DOWN_EXPENSE slot, credited
	// with the amount on a merchant product. A NON-merchant product has no
	// buy-down expense account, so it is empty there.
	BuyDownExpense string
	// FundSource is the resolved AccrualAccountsForLoan.FUND_SOURCE slot: the
	// payment-channel account when the transaction's paymentTypeId has one, else
	// the product's fund source. It is credited with the amount on a
	// NON-merchant product.
	FundSource string
}

// CreateBuyDownFeeAdjustmentJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForBuyDownFeeAdjustment
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:552-575, pinned commit
// 426a23544]. It is a pure function: the transaction id, an amount (the
// adjustment the product recognized), the loan's merchantBuyDownFee fact and the
// product's slot->account mapping in; journal-entry legs out — no clock, no I/O,
// no stored balance, integer minor units only.
//
// When the amount is > 0 it posts exactly two legs through the processor's
// helper.createJournalEntriesForLoan(debit, credit), the mirror of the
// buy-down-fee entry:
//
//  1. DEBIT DEFERRED_INCOME_LIABILITY with the amount;
//  2. CREDIT the selected account with the amount — BUY_DOWN_EXPENSE when the
//     product is a merchant product, else the resolved FUND_SOURCE.
//
// The Java local is named debitAccountType but it is passed as the CREDITED
// account; the helper's parameter order is (accountTypeToBeDebited,
// accountTypeToBeCredited), so the deferred-income-liability debit comes first
// and the selected account is credited. A non-positive amount posts nothing,
// matching MathUtil.isGreaterThanZero.
//
// THE OBSERVED DOMAIN IS NARROW AND THIS PORT REFUSES ANYTHING OUTSIDE IT, by
// construction rather than by guessing: a negative amount is refused, and a
// positive amount with no credit account or no deferred-income account is
// refused. Because a NON-merchant product carries no buy-down expense account,
// a merchant=true input whose mapping has no buy-down expense account is refused
// rather than falling back to the fund source.
func CreateBuyDownFeeAdjustmentJournalEntryLegs(transactionID string, amount MinorUnits, merchantBuyDownFee bool, mapping BuyDownFeeAdjustmentAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: buy-down-fee adjustment journal entries need a transaction id")
	}
	if amount < 0 {
		return nil, fmt.Errorf("loan: buy-down-fee adjustment carries a negative amount %d", amount)
	}
	if amount == 0 {
		return nil, nil
	}

	credit := mapping.FundSource
	if merchantBuyDownFee {
		credit = mapping.BuyDownExpense
	}
	if credit == "" {
		return nil, fmt.Errorf("loan: buy-down-fee adjustment amount %d has no credit account (merchant %t)", amount, merchantBuyDownFee)
	}
	if mapping.DeferredIncomeLiability == "" {
		return nil, fmt.Errorf("loan: buy-down-fee adjustment amount %d has no deferred-income account", amount)
	}

	return []JournalEntryLeg{
		{
			TransactionID: transactionID,
			Account:       mapping.DeferredIncomeLiability,
			Side:          JournalEntryDebit,
			Amount:        amount,
		},
		{
			TransactionID: transactionID,
			Account:       credit,
			Side:          JournalEntryCredit,
			Amount:        amount,
		},
	}, nil
}
