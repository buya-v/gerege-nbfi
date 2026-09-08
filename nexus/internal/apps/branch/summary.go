package branch

import "fmt"

// CashierSummaryTotals is the till summary a cashier-transaction row set
// derives: the four observed buckets (allocation, inward cash, outward cash and
// settlement) and the net till cash computed from them. Nothing here is stored —
// the totals are a pure fold over the append-only m_cashier_transactions rows,
// the same derived-read model as the savings running-total fold.
type CashierSummaryTotals struct {
	Allocation  MinorUnits
	InwardCash  MinorUnits
	OutwardCash MinorUnits
	Settlement  MinorUnits
}

// NetCash derives the net till cash from the four buckets. Fineract's cashier
// summary computes it as allocation plus inward cash minus outward cash minus
// settlement: the allocations a cashier received plus cash taken in at the till,
// less what was paid out and less what was settled back to the office float.
//
// [VERIFIED: TellerCashManagementReadPlatformServiceImpl — netCash =
// sumCashAllocation + sumInwardCash - sumOutwardCash - sumCashSettlement.]
func (t CashierSummaryTotals) NetCash() MinorUnits {
	return t.Allocation + t.InwardCash - t.OutwardCash - t.Settlement
}

// FoldCashierSummary derives a cashier summary from an append-only transaction
// row set, in the order the rows were observed. Each row feeds exactly one
// bucket by its transaction type (101 allocation, 102 settlement, 103 cash in,
// 104 cash out); an unknown type is refused rather than silently dropped, so a
// fold that loses a row is a fold the harness can catch.
func FoldCashierSummary(rows []CashierTransaction) (CashierSummaryTotals, error) {
	var totals CashierSummaryTotals
	for _, row := range rows {
		switch row.TxnType.ID {
		case TxnAllocate.ID:
			totals.Allocation += row.TxnAmount
		case TxnInwardCash.ID:
			totals.InwardCash += row.TxnAmount
		case TxnOutwardCash.ID:
			totals.OutwardCash += row.TxnAmount
		case TxnSettle.ID:
			totals.Settlement += row.TxnAmount
		default:
			return CashierSummaryTotals{}, fmt.Errorf(
				"branch: cashier transaction type %d does not feed a summary bucket", row.TxnType.ID)
		}
	}
	return totals, nil
}
