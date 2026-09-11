package loan

import "fmt"

// ChargedOffWriteOffPortions is the money a write-off on a loan MARKED CHARGED
// OFF reverses per ledger slot, in integer minor units. It is the Go port of
// the five BigDecimal fields createJournalEntriesForWriteOffsWhenLoanIsChargedOff
// reads off the write-off transaction — principal, interest, fees, penalties and
// overPayment [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1616-1694, pinned commit
// 426a23544].
//
// A slot is reversed only when its portion is > 0 (MathUtil
// .isGreaterThanZero); a zero portion contributes neither an amount nor an
// account to the posting. Every field is an integer MinorUnits value: no float
// and no sub-minor residue can enter this path (G-19 / DEC-2 G-08).
type ChargedOffWriteOffPortions struct {
	Principal   MinorUnits
	Interest    MinorUnits
	Fee         MinorUnits
	Penalty     MinorUnits
	Overpayment MinorUnits
}

// Total returns the sum of every portion, in integer minor units. It is the
// amount of the ONE debit a charged-off write-off posts to the losses-written-off
// account.
func (p ChargedOffWriteOffPortions) Total() MinorUnits {
	return p.Principal + p.Interest + p.Fee + p.Penalty + p.Overpayment
}

// ChargedOffWriteOffAccountMapping is the GL account each charged-off write-off
// portion slot CREDITS for one loan product, as GET /loanproducts/{id}
// .accountingMappings returns it (the AccrualAccountsForLoan slots the processor
// resolves through getLinkedGLAccountForLoanProduct).
//
// A charged-off write-off reverses the earlier charge-off: it CREDITS the
// charge-off expense/income accounts the charge-off debited and DEBITs the
// losses-written-off account ONCE with the sum of every discharged portion
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1637-1692].
//
// The processor resolves a FUND_SOURCE debit slot too, but only the CREDIT map
// is iterated: the fund-source debits it accumulates are NEVER posted, so this
// mapping carries no fund-source slot.
type ChargedOffWriteOffAccountMapping struct {
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// credited with the principal portion on a non-fraud loan.
	ChargeOffExpense string
	// ChargeOffFraudExpense is the AccrualAccountsForLoan
	// .CHARGE_OFF_FRAUD_EXPENSE slot, credited with the principal portion when
	// the loan is marked fraud.
	ChargeOffFraudExpense string
	// IncomeFromChargeOffInterest is the AccrualAccountsForLoan
	// .INCOME_FROM_CHARGE_OFF_INTEREST slot, credited with the interest portion.
	IncomeFromChargeOffInterest string
	// IncomeFromChargeOffFees is the AccrualAccountsForLoan
	// .INCOME_FROM_CHARGE_OFF_FEES slot, credited with the fee portion.
	IncomeFromChargeOffFees string
	// IncomeFromChargeOffPenalty is the AccrualAccountsForLoan
	// .INCOME_FROM_CHARGE_OFF_PENALTY slot, credited with the penalty portion.
	IncomeFromChargeOffPenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion.
	Overpayment string
	// LossesWrittenOff is the AccrualAccountsForLoan.LOSSES_WRITTEN_OFF slot,
	// debited ONCE with the sum of every discharged portion.
	LossesWrittenOff string
}

// chargedOffWriteOffSlot is one portion/account pair in the processor's fixed
// visitation order.
type chargedOffWriteOffSlot struct {
	name    string
	amount  MinorUnits
	account string
}

// CreateChargedOffWriteOffJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForWriteOffsWhenLoanIsChargedOff [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1616-1694, pinned commit
// 426a23544]. It is a pure function: portions (integer minor units), the loan's
// fraud flag and a slot->account mapping in, journal-entry legs out — no clock,
// no I/O, no stored balance.
//
// It visits the five slots in the processor's order (principal, interest, fees,
// penalties, overpayment), and for every slot whose portion is > 0 CREDITS the
// slot's mapped account, MERGING into the first slot that already named the
// same account (the LinkedHashMap accountMap), so two portion slots that resolve
// to one GL account post ONE credit for their sum at the first slot's position.
// The principal slot credits the FRAUD expense account when the loan is marked
// fraud, else the ordinary charge-off expense account.
//
// It then posts ONE debit of the total to the losses-written-off account. The
// debit is LAST: the oracle posts it after the credit loop and NEVER posts the
// FUND_SOURCE debits populateCreditDebitMaps accumulates (only the credit map is
// iterated) [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1667-1693].
//
// It refuses, rather than inventing, a negative portion, a positive portion
// whose slot maps to no account, and a positive total with no losses-written-off
// account.
func CreateChargedOffWriteOffJournalEntryLegs(transactionID string, portions ChargedOffWriteOffPortions, fraud bool, mapping ChargedOffWriteOffAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: charged-off write-off journal entries need a transaction id")
	}

	principalCredit := mapping.ChargeOffExpense
	if fraud {
		principalCredit = mapping.ChargeOffFraudExpense
	}
	slots := []chargedOffWriteOffSlot{
		{"CHARGE_OFF_EXPENSE", portions.Principal, principalCredit},
		{"INCOME_FROM_CHARGE_OFF_INTEREST", portions.Interest, mapping.IncomeFromChargeOffInterest},
		{"INCOME_FROM_CHARGE_OFF_FEES", portions.Fee, mapping.IncomeFromChargeOffFees},
		{"INCOME_FROM_CHARGE_OFF_PENALTY", portions.Penalty, mapping.IncomeFromChargeOffPenalty},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}

	// accountMap is a LinkedHashMap: an ordered set of accounts keyed by the
	// account, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: charged-off write-off slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.account == "" {
			return nil, fmt.Errorf("loan: charged-off write-off slot %s has a positive portion %d but no mapped account", s.name, s.amount)
		}
		if _, seen := byAccount[s.account]; !seen {
			order = append(order, s.account)
		}
		byAccount[s.account] += s.amount
	}

	legs := make([]JournalEntryLeg, 0, len(order)+1)
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryCredit,
			Amount:        byAccount[account],
		})
	}

	total := portions.Total()
	if total == 0 {
		return legs, nil
	}
	if mapping.LossesWrittenOff == "" {
		return nil, fmt.Errorf("loan: charged-off write-off total %d has no losses-written-off account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.LossesWrittenOff,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
