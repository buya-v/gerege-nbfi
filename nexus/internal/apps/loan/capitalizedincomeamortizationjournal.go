package loan

import "fmt"

// CapitalizedIncomeAmortizationAccountMapping is the GL account each portion
// slot of a CAPITALIZED-INCOME AMORTIZATION journal entry credits, plus the one
// account every portion debits, as the processor resolves them [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:308-502, pinned commit 426a23544].
//
// The port models the two observed dispatches of
// createJournalEntriesForCapitalizedIncomeAmortization, switched by the loan's
// charged-off state:
//
//   - loan NOT charged off: both the interest and fee portions credit
//     IncomeFromCapitalization, or WriteOff when the loan is marked written off;
//   - loan CHARGED OFF: both portions credit ChargeOffFraudExpense when the loan
//     is marked fraud, else ChargeOffExpense.
//
// In BOTH dispatches every portion debits DeferredIncomeLiability, merged into
// one total debit. Portions that resolve to the SAME account MERGE into one
// credit at the first slot's position (the processor's accountMap is a
// LinkedHashMap).
//
// The capitalized-income CLASSIFICATION branch (a non-empty
// classificationCodeValues, whose per-code mapping substitutes the credit
// account) and the charge-off-REASON branch (a non-null
// chargeOffReasonCodeValue, whose mapping substitutes the credit account) are
// NOT observed, so this mapping carries NO input for either: those branches
// cannot be expressed rather than being guessed.
type CapitalizedIncomeAmortizationAccountMapping struct {
	// IncomeFromCapitalization is the AccrualAccountsForLoan
	// .INCOME_FROM_CAPITALIZATION slot, credited with both portions when the
	// loan is NOT charged off and NOT written off.
	IncomeFromCapitalization string
	// DeferredIncomeLiability is the AccrualAccountsForLoan
	// .DEFERRED_INCOME_LIABILITY slot, debited ONCE with the sum of every
	// portion in both dispatches.
	DeferredIncomeLiability string
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// credited with both portions when the loan IS charged off and NOT fraud.
	ChargeOffExpense string
	// ChargeOffFraudExpense is the AccrualAccountsForLoan
	// .CHARGE_OFF_FRAUD_EXPENSE slot, credited with both portions when the loan
	// IS charged off AND fraud.
	ChargeOffFraudExpense string
	// WriteOff is the AccrualAccountsForLoan.LOSSES_WRITTEN_OFF slot, credited
	// with both portions when the loan is marked written off (and not charged
	// off).
	WriteOff string
}

// capitalizedIncomeAmortizationSlot is one portion in the processor's fixed
// visitation order. Both slots resolve to the SAME credit account and the SAME
// deferred-income-liability debit account, so they merge into one credit and one
// debit whenever both are positive.
type capitalizedIncomeAmortizationSlot struct {
	name   string
	amount MinorUnits
}

// CreateCapitalizedIncomeAmortizationJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForCapitalizedIncomeAmortization, dispatching to
// createJournalEntriesForLoanCapitalizedIncomeAmortization or
// createJournalEntriesForChargeOffLoanCapitalizedIncomeAmortization by the
// loan's charged-off state [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:308-502, pinned commit 426a23544].
// It is a pure function: the transaction's interest and fee portions (integer
// minor units), the loan's charged-off / fraud / written-off state and the
// resolved slot->account mapping in, journal-entry legs out — no clock, no I/O,
// no stored balance.
//
// It visits the two portion slots in the processor's order (interest, fees). For
// every slot whose portion is > 0 it CREDITS that slot's account for the loan's
// dispatch, MERGING the two portions into one credit when they share an account
// (they always do here), and DEBITS the same amount to DeferredIncomeLiability,
// likewise merged. It then posts every credit in insertion order, followed by
// every debit in insertion order: the observed posts read ONE credit then ONE
// debit.
//
// The account ids are the product's accountingMappings read back from the
// reference server, never invented. The port refuses, rather than guessing, a
// negative portion, a positive portion whose credit slot maps to no account or
// whose deferred-income-liability account is unmapped, and the impossible
// chargedOff && writtenOff state (the processor dispatches on exactly one).
func CreateCapitalizedIncomeAmortizationJournalEntryLegs(transactionID string, interest, fee MinorUnits, chargedOff, fraud, writtenOff bool, mapping CapitalizedIncomeAmortizationAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: capitalized-income-amortization journal entries need a transaction id")
	}
	if chargedOff && writtenOff {
		return nil, fmt.Errorf("loan: capitalized-income-amortization journal entries refuse a loan that is both charged off and written off: the processor dispatches on exactly one")
	}

	var creditAccount string
	switch {
	case chargedOff && fraud:
		creditAccount = mapping.ChargeOffFraudExpense
	case chargedOff:
		creditAccount = mapping.ChargeOffExpense
	case writtenOff:
		creditAccount = mapping.WriteOff
	default:
		creditAccount = mapping.IncomeFromCapitalization
	}

	slots := []capitalizedIncomeAmortizationSlot{
		{"INTEREST", interest},
		{"FEES", fee},
	}

	// creditByAccount/debitByAccount model the processor's GLAccountBalanceHolder
	// LinkedHashMaps: ordered sets of accounts keyed by the account, each
	// accumulating every portion that resolves to it, with the position of the
	// FIRST slot that named it.
	var creditOrder, debitOrder []string
	creditByAccount := map[string]MinorUnits{}
	debitByAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: capitalized-income-amortization slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if creditAccount == "" {
			return nil, fmt.Errorf("loan: capitalized-income-amortization slot %s has a positive portion %d but no mapped credit account", s.name, s.amount)
		}
		if mapping.DeferredIncomeLiability == "" {
			return nil, fmt.Errorf("loan: capitalized-income-amortization slot %s has a positive portion %d but no mapped deferred-income-liability account", s.name, s.amount)
		}
		if _, seen := creditByAccount[creditAccount]; !seen {
			creditOrder = append(creditOrder, creditAccount)
		}
		creditByAccount[creditAccount] += s.amount
		if _, seen := debitByAccount[mapping.DeferredIncomeLiability]; !seen {
			debitOrder = append(debitOrder, mapping.DeferredIncomeLiability)
		}
		debitByAccount[mapping.DeferredIncomeLiability] += s.amount
	}

	legs := make([]JournalEntryLeg, 0, len(creditOrder)+len(debitOrder))
	for _, account := range creditOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryCredit,
			Amount:        creditByAccount[account],
		})
	}
	for _, account := range debitOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        debitByAccount[account],
		})
	}
	return legs, nil
}
