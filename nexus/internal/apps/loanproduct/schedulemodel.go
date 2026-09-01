package loanproduct

import (
	"math/big"
	"time"
)

// ScheduleModel is the Go port of Fineract's
// ProgressiveLoanInterestScheduleModel: the mutable interest-schedule container
// the recomputation arithmetic walks. It holds an ordered repayment-period list,
// the rate-override table, the product's related detail, and the rounding /
// currency context every Money cell is produced under.
//
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:60-97 for the field list.]
//
// The oracle also carries a lastOverdueBalanceChange marker and a list of
// OverdueBalanceCorrection records used only by the deferral of unrecognized
// interest after a delinquency re-ageing. Those belong to the delinquency /
// re-ageing slice, not to the rate-factor recomputation, so this port defers
// them and refuses no arithmetic because of their absence.
type ScheduleModel struct {
	repaymentPeriods     []*RepaymentPeriod
	interestRates        []InterestRate // sorted by EffectiveFrom descending
	detail               LoanProductRelatedDetail
	installmentMultiples int64

	rounding Rounding
	currency Currency

	emiRecalculationEnabled bool
	copiedForCalculation    bool
}

// NewScheduleModel builds a schedule model over periods, seeding the modifier
// flags exactly as the oracle's two public constructors do
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:108-139].
//
// installmentAmountInMultiplesOf is carried for parity but, mirroring the
// generator's capture seam, is never read by the rate-factor recomputation.
func NewScheduleModel(periods []*RepaymentPeriod, detail LoanProductRelatedDetail,
	installmentAmountInMultiplesOf int64, rounding Rounding, currency Currency) *ScheduleModel {
	m := &ScheduleModel{
		repaymentPeriods:        append([]*RepaymentPeriod(nil), periods...),
		interestRates:           nil,
		detail:                  detail,
		installmentMultiples:    installmentAmountInMultiplesOf,
		rounding:                rounding,
		currency:                currency,
		emiRecalculationEnabled: true,
		copiedForCalculation:    false,
	}
	return m
}

// RepaymentPeriods returns the ordered installment windows, in schedule order.
func (m *ScheduleModel) RepaymentPeriods() []*RepaymentPeriod { return m.repaymentPeriods }

// Rounding returns the MathContext-equivalent carried by the model.
func (m *ScheduleModel) Rounding() Rounding { return m.rounding }

// Currency returns the monetary currency carried by the model.
func (m *ScheduleModel) Currency() Currency { return m.currency }

// Detail returns the product related detail carried by the model.
func (m *ScheduleModel) Detail() LoanProductRelatedDetail { return m.detail }

// Zero returns the currency- and rounding-correct zero money value.
func (m *ScheduleModel) Zero() Money { return moneyZero(m.currency, m.rounding) }

// GetInterestRate returns the annual nominal interest rate (in percent) in
// effect on effectiveDate: the most recent override with effectiveFrom <=
// effectiveDate, or the product's annual nominal rate when no override applies
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:199-210].
func (m *ScheduleModel) GetInterestRate(effectiveDate time.Time) *big.Rat {
	if len(m.interestRates) == 0 {
		return m.detail.AnnualNominalInterestRateMajor()
	}
	for _, ir := range m.interestRates {
		if compareDates(ir.EffectiveFrom, effectiveDate) <= 0 {
			return ir.Rate
		}
	}
	return m.detail.AnnualNominalInterestRateMajor()
}

// AddInterestRate records an interest-rate override effective from a date,
// keeping the table sorted by effective date descending
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:213-215].
func (m *ScheduleModel) AddInterestRate(effectiveFrom time.Time, rate *big.Rat) {
	m.interestRates = append(m.interestRates, InterestRate{EffectiveFrom: effectiveFrom, Rate: new(big.Rat).Set(rate)})
	// Insertion order after append is not guaranteed to be descending; sort the
	// small slice by effective date descending (stable tie-break not needed:
	// effective dates are unique per the oracle's TreeSet contract).
	for i := 1; i < len(m.interestRates); i++ {
		for j := i; j > 0 && m.interestRates[j].compare(m.interestRates[j-1]) < 0; j-- {
			m.interestRates[j], m.interestRates[j-1] = m.interestRates[j-1], m.interestRates[j]
		}
	}
}

// FindRepaymentPeriodByFromAndDueDate returns the period whose [from, due]
// window exactly matches the request, or — when no exact match exists — the
// first period that encompasses the requested range (the merged-stub fallback)
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:217-233].
func (m *ScheduleModel) FindRepaymentPeriodByFromAndDueDate(from, due time.Time) (*RepaymentPeriod, bool) {
	if due.IsZero() {
		return nil, false
	}
	for _, rp := range m.repaymentPeriods {
		if compareDates(rp.FromDate, from) == 0 && compareDates(rp.DueDate, due) == 0 {
			return rp, true
		}
	}
	for _, rp := range m.repaymentPeriods {
		if compareDates(rp.FromDate, from) <= 0 && compareDates(rp.DueDate, due) >= 0 {
			return rp, true
		}
	}
	return nil, false
}

// GetRelatedRepaymentPeriods returns the repayment periods whose due date is not
// before the supplied due date; a zero due date returns the whole schedule
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:235-241].
func (m *ScheduleModel) GetRelatedRepaymentPeriods(calculateFromRepaymentPeriodDueDate time.Time) []*RepaymentPeriod {
	if calculateFromRepaymentPeriodDueDate.IsZero() {
		return append([]*RepaymentPeriod(nil), m.repaymentPeriods...)
	}
	out := make([]*RepaymentPeriod, 0, len(m.repaymentPeriods))
	for _, rp := range m.repaymentPeriods {
		if compareDates(rp.DueDate, calculateFromRepaymentPeriodDueDate) >= 0 {
			out = append(out, rp)
		}
	}
	return out
}

// LoanTermInDays is the day span from the first period's from-date to the last
// period's due date (or 0 when the schedule is empty)
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:243-249].
func (m *ScheduleModel) LoanTermInDays() int64 {
	if len(m.repaymentPeriods) == 0 {
		return 0
	}
	first := m.repaymentPeriods[0]
	last := first
	if len(m.repaymentPeriods) > 1 {
		last = m.LastRepaymentPeriod()
	}
	return exactDifferenceInDays(first.FromDate, last.DueDate)
}

// StartDate is the first period's from-date, or the zero date when empty
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:251-253].
func (m *ScheduleModel) StartDate() time.Time {
	if len(m.repaymentPeriods) == 0 {
		return time.Time{}
	}
	return m.repaymentPeriods[0].FromDate
}

// MaturityDate is the last period's due date, or the zero date when empty
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:255-257].
func (m *ScheduleModel) MaturityDate() time.Time {
	if len(m.repaymentPeriods) == 0 {
		return time.Time{}
	}
	return m.LastRepaymentPeriod().DueDate
}

// ChangeOutstandingBalanceAndUpdateInterestPeriods applies a disbursement, a
// balance correction and a capitalized-income principal amount to the interest
// period containing balanceChangeDate, splitting the period when needed
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:259-265].
func (m *ScheduleModel) ChangeOutstandingBalanceAndUpdateInterestPeriods(balanceChangeDate time.Time,
	disbursedAmount, correctionAmount, capitalizedIncomePrincipal Money) (*RepaymentPeriod, bool) {
	rp, ok := m.findRepaymentPeriodForBalanceChange(balanceChangeDate)
	if !ok {
		return nil, false
	}
	m.updateInterestPeriodOnRepaymentPeriod(rp, balanceChangeDate, disbursedAmount, correctionAmount, capitalizedIncomePrincipal)
	return rp, true
}

// UpdateInterestPeriodsForInterestPause marks the interest-period segments
// overlapping [from, end] as paused and splits period boundaries so the pause
// window aligns to segment boundaries [VERIFIED:
// ProgressiveLoanInterestScheduleModel.java:267-276].
func (m *ScheduleModel) UpdateInterestPeriodsForInterestPause(from, end time.Time) (*RepaymentPeriod, bool) {
	if from.IsZero() || end.IsZero() {
		return nil, false
	}
	var first *RepaymentPeriod
	for _, rp := range m.repaymentPeriods {
		if compareDates(rp.FromDate, end) < 0 && compareDates(rp.DueDate, from) >= 0 {
			m.insertInterestPausePeriods(rp, from, end)
			if first == nil {
				first = rp
			}
		}
	}
	if first == nil {
		return nil, false
	}
	return first, true
}

// findRepaymentPeriodForBalanceChange returns the period whose window contains
// balanceChangeDate under the first-period-inclusive rule
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:278-284].
func (m *ScheduleModel) findRepaymentPeriodForBalanceChange(date time.Time) (*RepaymentPeriod, bool) {
	if date.IsZero() {
		return nil, false
	}
	for _, rp := range m.repaymentPeriods {
		if isInPeriod(date, rp.FromDate, rp.DueDate, rp.IsFirstRepaymentPeriod()) {
			return rp, true
		}
	}
	return nil, false
}

// updateInterestPeriodOnRepaymentPeriod applies the three amounts to the
// matching interest period, or inserts a new one when the change lands on a
// boundary that no existing segment's due-date matches
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:286-297].
func (m *ScheduleModel) updateInterestPeriodOnRepaymentPeriod(rp *RepaymentPeriod, date time.Time,
	disbursedAmount, correctionAmount, capitalizedIncomePrincipal Money) {
	isChangeOnMaturityDate := m.IsLastRepaymentPeriod(rp) && compareDates(date, rp.DueDate) == 0
	ip, ok := m.findInterestPeriodForBalanceChange(rp, date, isChangeOnMaturityDate)
	if ok {
		ip.AddDisbursementAmount(disbursedAmount)
		ip.AddCapitalizedIncomePrincipalAmount(capitalizedIncomePrincipal)
		ip.AddBalanceCorrectionAmount(correctionAmount)
		return
	}
	m.insertInterestPeriod(rp, date, disbursedAmount, correctionAmount, capitalizedIncomePrincipal)
}

// findInterestPeriodForBalanceChange returns the existing segment that should
// receive a balance change [VERIFIED: ProgressiveLoanInterestScheduleModel.java:299-311].
//
// A change on the maturity date reuses the last segment only when that segment
// is already zero-length (a credit activity on maturity); otherwise a new
// segment is created. Any other change reuses the segment whose due-date equals
// the change date.
func (m *ScheduleModel) findInterestPeriodForBalanceChange(rp *RepaymentPeriod, date time.Time,
	isChangeOnMaturityDate bool) (*InterestPeriod, bool) {
	if date.IsZero() {
		return nil, false
	}
	if isChangeOnMaturityDate {
		last := rp.LastInterestPeriod()
		if last.Length() == 0 {
			return last, true
		}
		return nil, false
	}
	for _, ip := range rp.InterestPeriods {
		if compareDates(date, ip.DueDate) == 0 {
			return ip, true
		}
	}
	return nil, false
}

// insertInterestPeriod splits the segment containing date and inserts a fresh
// empty segment after it [VERIFIED: ProgressiveLoanInterestScheduleModel.java:313-331].
func (m *ScheduleModel) insertInterestPeriod(rp *RepaymentPeriod, date time.Time,
	disbursedAmount, correctionAmount, capitalizedIncomePrincipal Money) {
	previous := m.findPreviousInterestPeriod(rp, date)
	originalDueDate := previous.DueDate
	newDueDate := m.calculateNewDueDate(previous, date)
	paused := previous.IsPaused()

	previous.SetDueDate(newDueDate)
	previous.AddDisbursementAmount(disbursedAmount)
	previous.AddCapitalizedIncomePrincipalAmount(capitalizedIncomePrincipal)
	previous.AddBalanceCorrectionAmount(correctionAmount)

	next := withEmptyInterestPeriod(rp, newDueDate, originalDueDate, paused)
	index := rp.interestPeriodIndex(previous)
	rp.InterestPeriods = append(rp.InterestPeriods, nil)
	copy(rp.InterestPeriods[index+2:], rp.InterestPeriods[index+1:])
	rp.InterestPeriods[index+1] = next
}

// insertInterestPausePeriods clamps the pause window into the period and then
// splits/adjusts segment boundaries so the pause aligns to them
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:342-352].
func (m *ScheduleModel) insertInterestPausePeriods(rp *RepaymentPeriod, pauseStart, pauseEnd time.Time) {
	effectivePauseStart := plusDays(pauseStart, -1)
	finalPauseStart := effectivePauseStart
	if compareDates(effectivePauseStart, rp.FromDate) < 0 {
		finalPauseStart = rp.FromDate
	}
	finalPauseEnd := pauseEnd
	if compareDates(pauseEnd, rp.DueDate) > 0 {
		finalPauseEnd = rp.DueDate
	}
	m.insertInterestPausePeriodsByAdjustedDates(rp, finalPauseStart, finalPauseEnd)
}

// insertInterestPausePeriodsByAdjustedDates ensures boundary segments exist at
// the pause start and end, then marks every segment inside the window as paused
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:333-341].
func (m *ScheduleModel) insertInterestPausePeriodsByAdjustedDates(rp *RepaymentPeriod, pauseStart, pauseEnd time.Time) {
	if !m.hasSegmentWithFromDate(rp, pauseStart) {
		m.insertInterestPeriod(rp, pauseStart, rp.Zero(), rp.Zero(), rp.Zero())
	}
	if !m.hasSegmentWithDueDate(rp, pauseEnd) {
		m.insertInterestPeriod(rp, pauseEnd, rp.Zero(), rp.Zero(), rp.Zero())
	}
	for _, ip := range rp.InterestPeriods {
		if compareDates(ip.FromDate, pauseStart) >= 0 && compareDates(ip.DueDate, pauseEnd) <= 0 {
			ip.SetPaused(true)
		}
	}
}

func (m *ScheduleModel) hasSegmentWithFromDate(rp *RepaymentPeriod, from time.Time) bool {
	for _, ip := range rp.InterestPeriods {
		if compareDates(ip.FromDate, from) == 0 {
			return true
		}
	}
	return false
}

func (m *ScheduleModel) hasSegmentWithDueDate(rp *RepaymentPeriod, due time.Time) bool {
	for _, ip := range rp.InterestPeriods {
		if compareDates(ip.DueDate, due) == 0 {
			return true
		}
	}
	return false
}

// findPreviousInterestPeriod returns the last segment whose window contains
// date (from < date <= due), or the first segment when none does
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:354-357].
func (m *ScheduleModel) findPreviousInterestPeriod(rp *RepaymentPeriod, date time.Time) *InterestPeriod {
	var found *InterestPeriod
	for _, ip := range rp.InterestPeriods {
		if compareDates(date, ip.FromDate) > 0 && compareDates(date, ip.DueDate) <= 0 {
			found = ip
		}
	}
	if found != nil {
		return found
	}
	return rp.FirstInterestPeriod()
}

// calculateNewDueDate clamps date into the segment's [from, due] window
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:452-455].
func (m *ScheduleModel) calculateNewDueDate(previous *InterestPeriod, date time.Time) time.Time {
	if compareDates(date, previous.FromDate) < 0 {
		return previous.FromDate
	}
	if compareDates(date, previous.DueDate) > 0 {
		return previous.DueDate
	}
	return date
}

// --- Totals -----------------------------------------------------------------

// TotalDueInterest is the sum of each period's due interest, floored at zero
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:368-371].
func (m *ScheduleModel) TotalDueInterest() Money {
	res := m.Zero()
	for _, rp := range m.repaymentPeriods {
		res = res.plus(rp.DueInterest())
	}
	return res.negToZero()
}

// TotalDuePrincipal is the sum of each period's principal-like credited amounts,
// floored at zero [VERIFIED: ProgressiveLoanInterestScheduleModel.java:378-381].
func (m *ScheduleModel) TotalDuePrincipal() Money {
	res := m.Zero()
	for _, rp := range m.repaymentPeriods {
		res = res.plus(rp.CreditedAmounts())
	}
	return res.negToZero()
}

// TotalPaidInterest is the sum of each period's paid interest, floored at zero
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:388-391].
func (m *ScheduleModel) TotalPaidInterest() Money {
	res := m.Zero()
	for _, rp := range m.repaymentPeriods {
		res = res.plus(rp.PaidInterest())
	}
	return res.negToZero()
}

// TotalPaidPrincipal is the sum of each period's paid principal, floored at zero
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:398-401].
func (m *ScheduleModel) TotalPaidPrincipal() Money {
	res := m.Zero()
	for _, rp := range m.repaymentPeriods {
		res = res.plus(rp.PaidPrincipal())
	}
	return res.negToZero()
}

// TotalCreditedPrincipal is the sum of each period's credited principal, floored
// at zero [VERIFIED: ProgressiveLoanInterestScheduleModel.java:408-410].
func (m *ScheduleModel) TotalCreditedPrincipal() Money {
	res := m.Zero()
	for _, rp := range m.repaymentPeriods {
		res = res.plus(rp.CreditedPrincipal())
	}
	return res.negToZero()
}

// TotalOutstandingPrincipal is total due principal minus total paid principal,
// floored at zero [VERIFIED: ProgressiveLoanInterestScheduleModel.java:412-414].
func (m *ScheduleModel) TotalOutstandingPrincipal() Money {
	return m.TotalDuePrincipal().minus(m.TotalPaidPrincipal()).negToZero()
}

// --- Lookup -----------------------------------------------------------------

// FindRepaymentPeriod returns the period whose window contains transactionDate
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:416-420].
func (m *ScheduleModel) FindRepaymentPeriod(transactionDate time.Time) (*RepaymentPeriod, bool) {
	for _, rp := range m.repaymentPeriods {
		if isInPeriod(transactionDate, rp.FromDate, rp.DueDate, rp.IsFirstRepaymentPeriod()) {
			return rp, true
		}
	}
	return nil, false
}

// IsEmpty reports whether no period carries a non-zero installment
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:426-430].
func (m *ScheduleModel) IsEmpty() bool {
	for _, rp := range m.repaymentPeriods {
		if !rp.Emi().IsZero() {
			return false
		}
	}
	return true
}

// LastRepaymentPeriod returns the final installment window; the caller must
// ensure the schedule is non-empty [VERIFIED: ProgressiveLoanInterestScheduleModel.java:433-435].
func (m *ScheduleModel) LastRepaymentPeriod() *RepaymentPeriod {
	return m.repaymentPeriods[len(m.repaymentPeriods)-1]
}

// IsLastRepaymentPeriod reports whether rp is the final installment window
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:437-439].
func (m *ScheduleModel) IsLastRepaymentPeriod(rp *RepaymentPeriod) bool {
	return m.LastRepaymentPeriod() == rp
}

// --- Copies -----------------------------------------------------------------

// DeepCopy returns a full copy of the model, preserving every paid and credited
// cell [VERIFIED: ProgressiveLoanInterestScheduleModel.java:141-145].
func (m *ScheduleModel) DeepCopy() *ScheduleModel {
	return m.copy(false)
}

// CopyWithoutPaidAmounts returns a copy with paid amounts zeroed
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:147-152].
func (m *ScheduleModel) CopyWithoutPaidAmounts() *ScheduleModel {
	return m.copy(true)
}

func (m *ScheduleModel) copy(zeroPaid bool) *ScheduleModel {
	c := &ScheduleModel{
		interestRates:           append([]InterestRate(nil), m.interestRates...),
		detail:                  m.detail,
		installmentMultiples:    m.installmentMultiples,
		rounding:                m.rounding,
		currency:                m.currency,
		emiRecalculationEnabled: m.emiRecalculationEnabled,
		copiedForCalculation:    zeroPaid,
	}
	var prev *RepaymentPeriod
	for _, rp := range m.repaymentPeriods {
		var cp *RepaymentPeriod
		if zeroPaid {
			cp = rp.copyWithoutPaidAmounts(prev)
		} else {
			cp = rp.copy(prev)
		}
		prev = cp
		c.repaymentPeriods = append(c.repaymentPeriods, cp)
	}
	return c
}

// --- Modifiers --------------------------------------------------------------

// DisableEMIRecalculation turns off the EMI-recalculation modifier
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:457-459].
func (m *ScheduleModel) DisableEMIRecalculation() { m.emiRecalculationEnabled = false }

// IsEMIRecalculationEnabled reports the EMI-recalculation modifier.
func (m *ScheduleModel) IsEMIRecalculationEnabled() bool { return m.emiRecalculationEnabled }

// IsCopy reports whether this model was produced by copyWithoutPaidAmounts.
func (m *ScheduleModel) IsCopy() bool { return m.copiedForCalculation }
