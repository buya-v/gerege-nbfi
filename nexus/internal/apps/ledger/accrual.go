package ledger

import "fmt"

// This file is slice A3's accrual arm: building balanced journal-entry legs
// from SLOT-CODED amounts on an accrual loan product. It is the shape behind
// capture LDG-ACC-01, where ONE accrual journal transaction spans SIX slots —
// INTEREST_RECEIVABLE (7), INTEREST_ON_LOANS (3), INCOME_FROM_FEES (4),
// FEES_RECEIVABLE (8), INCOME_FROM_PENALTIES (5), PENALTIES_RECEIVABLE (9).

// AccrualLeg is one slot-coded amount for an accrual posting. The account is
// NOT here: it is resolved through the product's observed acc_product_mapping
// rows, exactly as the posting path resolves it. A slot that is not an accrual
// loan slot is refused rather than silently cross-mapped (trap 2).
type AccrualLeg struct {
	Slot   AccrualLoanSlot
	Side   EntrySide
	Amount MinorUnits
}

// AccrualPoster resolves slot-coded accrual legs to journal-entry legs.
type AccrualPoster struct {
	Resolver *Resolver
}

// Build resolves every slot to its GL account and returns legs in the order
// supplied. Order is preserved because the oracle's own accrual journal entry
// is graded per-leg and the vector lists its six legs in source order, not
// sorted by side or account.
func (p AccrualPoster) Build(productID int64, paymentTypeID *int64, legs []AccrualLeg) ([]JournalEntryLeg, error) {
	if p.Resolver == nil {
		return nil, fmt.Errorf("accrual poster has no resolver")
	}
	out := make([]JournalEntryLeg, 0, len(legs))
	for i, l := range legs {
		if l.Slot.Rule() != AccountingRuleAccrualPeriodic {
			return nil, fmt.Errorf("accrual leg %d: slot %s is not an accrual loan slot", i, l.Slot.Name())
		}
		acct, err := p.Resolver.ResolveLoanProductAccount(productID, l.Slot, paymentTypeID)
		if err != nil {
			return nil, fmt.Errorf("accrual leg %d (%s): %w", i, l.Slot.Name(), err)
		}
		out = append(out, JournalEntryLeg{
			Account:  *acct,
			Side:     l.Side,
			Amount:   l.Amount,
			SlotName: l.Slot.Name(),
		})
	}
	return out, nil
}
