package provisioning

import "fmt"

// ReserveInput is one per-loan-product provisioning row: the storage layer
// fills it from the oracle's loan-overdue query and hands it to
// GenerateReserveEntries. It carries the matched criteria definition's
// percentage and account pair, so the computation is a pure function of the
// row and needs no further lookup.
//
// [VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.LoanProductProvisioningEntryMapper.java:73-91
// for the row shape — office_id, product_id, currency_code, numberofdaysoverdue,
// category_id, provision_percentage, outstandingbalance, liability_account,
// expense_account, criteriaid.]
type ReserveInput struct {
	OfficeID         int64
	CurrencyCode     string
	ProductID        int64
	CategoryID       int64
	OverdueInDays    int64
	Percentage       Percent
	Balance          MinorUnits // total_outstanding_derived, already in minor units
	LiabilityAccount int64
	ExpenseAccount   int64
	CriteriaID       int64
}

// ReserveEntry is the aggregated reserve amount for one distinct
// (criteria, office, currency, product, category, overdue band, account pair)
// combination — the Go port of LoanProductProvisioningEntry.
// [VERIFIED: LoanProductProvisioningEntry.java — @Table(name =
// "m_loanproduct_provisioning_entry"), fields office/currency/product/category/
// overdue_in_days/reseve_amount/liability/expense/criteria.]
type ReserveEntry struct {
	OfficeID         int64
	CurrencyCode     string
	ProductID        int64
	CategoryID       int64
	OverdueInDays    int64
	ReservedAmount   MinorUnits
	LiabilityAccount int64
	ExpenseAccount   int64
	CriteriaID       int64
}

// reserveKey is the aggregation key ported from
// LoanProductProvisioningEntry.partialHashCode
// [VERIFIED: LoanProductProvisioningEntry.java:129-134 — entry, criteriaId,
// office, currencyCode, loanProduct, provisioningCategory, overdueInDays,
// liabilityAccount, expenseAccount]. The parent history entry is identical for
// every row in a single generation pass, so it is omitted from the key here;
// everything else is what distinguishes one persisted reserve entry from the
// next.
type reserveKey struct {
	CriteriaID       int64
	OfficeID         int64
	CurrencyCode     string
	ProductID        int64
	CategoryID       int64
	OverdueInDays    int64
	LiabilityAccount int64
	ExpenseAccount   int64
}

// PercentageFunc computes one input row's reserve amount from its outstanding
// balance and the matched band's percentage. The port's own function is
// PercentageOf; GenerateReserveEntriesWith exists so a conformance wrong-drive
// can grade the reserve arithmetic under a DIFFERENT rounding function without
// re-implementing (and silently diverging from) the aggregation key below.
type PercentageFunc func(balance MinorUnits, percentage Percent) (MinorUnits, error)

// GenerateReserveEntries ports ProvisioningEntriesWritePlatformServiceJpaRepositoryImpl.
// generateLoanProvisioningEntry [VERIFIED: ...Impl.java:166-214]: for each
// input row it computes the reserve amount with Money.percentageOf and then
// merges rows that share a partial hash key by summing their reserved amounts.
//
// The result is returned in a deterministic order: first-seen input order of
// the distinct keys, which the oracle does not guarantee (it returns a HashSet)
// but which makes the port reproducible for tests. A caller that needs the
// oracle's unspecified ordering must sort independently.
func GenerateReserveEntries(inputs []ReserveInput) ([]ReserveEntry, error) {
	return GenerateReserveEntriesWith(inputs, PercentageOf)
}

// GenerateReserveEntriesWith is GenerateReserveEntries with the per-row
// percentage function supplied. Correct callers pass PercentageOf; only the
// conformance wrong-drives pass a mis-rounded variant.
func GenerateReserveEntriesWith(inputs []ReserveInput, percentageOf PercentageFunc) ([]ReserveEntry, error) {
	byKey := make(map[reserveKey]int) // key -> index into out
	var out []ReserveEntry

	for _, in := range inputs {
		amount, err := percentageOf(in.Balance, in.Percentage)
		if err != nil {
			return nil, fmt.Errorf("provisioning: reserve amount for product %d: %w", in.ProductID, err)
		}

		key := reserveKey{
			CriteriaID:       in.CriteriaID,
			OfficeID:         in.OfficeID,
			CurrencyCode:     in.CurrencyCode,
			ProductID:        in.ProductID,
			CategoryID:       in.CategoryID,
			OverdueInDays:    in.OverdueInDays,
			LiabilityAccount: in.LiabilityAccount,
			ExpenseAccount:   in.ExpenseAccount,
		}

		if idx, ok := byKey[key]; ok {
			out[idx].ReservedAmount += amount
			continue
		}

		byKey[key] = len(out)
		out = append(out, ReserveEntry{
			OfficeID:         in.OfficeID,
			CurrencyCode:     in.CurrencyCode,
			ProductID:        in.ProductID,
			CategoryID:       in.CategoryID,
			OverdueInDays:    in.OverdueInDays,
			ReservedAmount:   amount,
			LiabilityAccount: in.LiabilityAccount,
			ExpenseAccount:   in.ExpenseAccount,
			CriteriaID:       in.CriteriaID,
		})
	}
	return out, nil
}
