package loanproduct

import (
	"math/big"
	"time"
)

// InterestRate is Fineract's InterestRate record: a schedule-level rate
// override effective from a date [VERIFIED: InterestRate.java]. CompareTo orders
// by effectiveFrom ASCENDING; ScheduleModel stores them in descending order so
// that the first stream hit with effectiveFrom <= effectiveDate is the most
// recent override.
type InterestRate struct {
	EffectiveFrom time.Time
	// Rate is the annual nominal rate in PERCENT terms (a stored 12.000000% is
	// the rational 12), matching getAnnualNominalInterestRate()'s scale.
	Rate *big.Rat
}

// compare orders two interest rates by effectiveFrom DESCENDING, the ordering
// ScheduleModel iterates in.
func (r InterestRate) compare(other InterestRate) int {
	return -compareDates(r.EffectiveFrom, other.EffectiveFrom)
}
