package loanproduct

import (
	"math/big"
	"testing"
	"time"
)

// ---------------------------------------------------------------------------
// Shared test fixtures. Golden decimal strings below were generated
// independently with Python's decimal module (precision 19, ROUND_HALF_UP or
// ROUND_HALF_EVEN), which implements the same IEEE-854/BigDecimal semantics as
// java.math.BigDecimal for the four operations the recomputation performs.
// ---------------------------------------------------------------------------

func testRounding() Rounding { return Rounding{Precision: 19, Mode: RoundHalfUp} }
func testHalfEven() Rounding { return Rounding{Precision: 19, Mode: RoundHalfEven} }
func testCurrency() Currency { return Currency{Code: "USD", MinorDigits: 2} }

func date(y int, m time.Month, d int) time.Time {
	return time.Date(y, m, d, 0, 0, 0, 0, time.UTC)
}

func rat(s string) *big.Rat {
	r, ok := new(big.Rat).SetString(s)
	if !ok {
		panic("bad decimal literal in test: " + s)
	}
	return r
}

func assertRat(t *testing.T, got *big.Rat, want string) {
	t.Helper()
	w := rat(want)
	if got == nil || got.Cmp(w) != 0 {
		t.Fatalf("rate factor = %v, want %s", got, want)
	}
}

func testDetail() LoanProductRelatedDetail {
	return LoanProductRelatedDetail{
		InterestPeriodFrequencyType:           PeriodMonths,
		AnnualNominalInterestRate:             12_000_000, // 12.000000% per annum
		InterestMethod:                        InterestDecliningBalance,
		InterestCalculationPeriodMethod:       InterestCalcDaily,
		AllowPartialPeriodInterestCalc:        true,
		RepayEvery:                            1,
		RepaymentPeriodFrequencyType:          PeriodMonths,
		NumberOfRepayments:                    2,
		DaysInMonthType:                       DaysInMonth30,
		DaysInYearType:                        DaysInYear360,
		InterestRecalculationEnabled:          true,
		Currency:                              testCurrency(),
		DaysInYearCustomStrategy:              DaysInYearFullLeapYear,
		InterestRecognitionOnDisbursementDate: false,
	}
}

// ---------------------------------------------------------------------------
// Rate-factor kernel golden values
// ---------------------------------------------------------------------------

func TestRateFactorByRepaymentPeriodGolden(t *testing.T) {
	cases := []struct {
		name       string
		rate       *big.Rat
		multiplier int64
		repayEvery int64
		daysInYear int64
		actualDays int64
		calcDays   int64
		rounding   Rounding
		want       string
	}{
		{
			name:       "12pct monthly 30/360 full period",
			rate:       new(big.Rat).Quo(ratInt64(12), ratInt64(100)),
			multiplier: 30, repayEvery: 1, daysInYear: 360,
			actualDays: 30, calcDays: 30, rounding: testRounding(),
			want: "0.0100000000000000000",
		},
		{
			name:       "18pct monthly 30/365 31-day period",
			rate:       new(big.Rat).Quo(ratInt64(18), ratInt64(100)),
			multiplier: 30, repayEvery: 1, daysInYear: 365,
			actualDays: 31, calcDays: 31, rounding: testRounding(),
			want: "0.0147945205479452055",
		},
		{
			name:       "10pct monthly 30/360 every-2-months prorated 28/30",
			rate:       new(big.Rat).Quo(ratInt64(10), ratInt64(100)),
			multiplier: 30, repayEvery: 2, daysInYear: 360,
			actualDays: 28, calcDays: 30, rounding: testRounding(),
			want: "0.0155555555555555556",
		},
		{
			name:       "12pct half-even tie",
			rate:       new(big.Rat).Quo(ratInt64(12), ratInt64(100)),
			multiplier: 30, repayEvery: 1, daysInYear: 360,
			actualDays: 30, calcDays: 30, rounding: testHalfEven(),
			want: "0.0100000000000000000",
		},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := rateFactorByRepaymentPeriod(c.rate, ratInt64(c.multiplier), ratInt64(c.repayEvery),
				c.daysInYear, c.actualDays, c.calcDays, c.rounding)
			assertRat(t, got, c.want)
		})
	}
}

func TestRateFactorByRepaymentPeriodZeroCalculatedDays(t *testing.T) {
	got := rateFactorByRepaymentPeriod(ratInt64(12), ratInt64(30), ratInt64(1), 360, 0, 0, testRounding())
	if got.Sign() != 0 {
		t.Fatalf("zero calculated days must yield zero, got %v", got)
	}
}

func TestRateFactorByRepaymentPartialPeriodGolden(t *testing.T) {
	rate := new(big.Rat).Quo(ratInt64(12), ratInt64(100))
	// 1/12 rounded to 19 significant digits is the cumulated period ratio the
	// ACTUAL-convention fractions would hand the partial kernel.
	cumulated := rat("0.08333333333333333333")
	got := rateFactorByRepaymentPartialPeriod(rate, ratOne(), cumulated, ratOne(), ratOne(), testRounding())
	assertRat(t, got, "0.0100000000000000000")
}

func TestCalculatePeriodFractionsGolden(t *testing.T) {
	m := NewScheduleModel([]*RepaymentPeriod{}, testDetail(), 0, testRounding(), testCurrency())
	// 2023-06-01 -> 2024-06-01: 213 days of 2023's 365 plus 153 days of 2024's
	// 366, each rounded before summation.
	got := calculatePeriodFractions(m, date(2023, 6, 1), date(2024, 6, 1))
	assertRat(t, got, "1.001594430720862340")
}

func TestCalculatePeriodRatioGolden(t *testing.T) {
	// A stub first period is the one shape that walks the fractional-trailing-
	// period arm: the from-date sits on the schedule-start lattice but the due
	// date is before the next lattice step, so the ratio is days-in-stub /
	// days-in-full-period rather than a whole number.
	m := NewScheduleModel(
		[]*RepaymentPeriod{NewRepaymentPeriod(nil, date(2023, 1, 1), date(2023, 1, 15),
			NewMoney(10000, testCurrency(), testRounding()), testRounding(), testCurrency(), InterestDecliningBalance)},
		testDetail(), 0, testRounding(), testCurrency())

	rp := m.RepaymentPeriods()[0]

	cases := []struct {
		from, due time.Time
		want      string
	}{
		{date(2023, 1, 1), date(2023, 1, 15), "0.4516129032258064516"},
		{date(2023, 1, 1), date(2023, 1, 20), "0.6129032258064516129"},
		{date(2023, 1, 1), date(2023, 2, 1), "1"},
	}
	for _, c := range cases {
		rp.FromDate = c.from
		rp.DueDate = c.due
		got := calculatePeriodRatio(m, rp, PeriodMonths, testRounding())
		assertRat(t, got, c.want)
	}
}

// ---------------------------------------------------------------------------
// Date helper semantics
// ---------------------------------------------------------------------------

func TestIsInPeriod(t *testing.T) {
	from := date(2024, 1, 1)
	to := date(2024, 2, 1)
	cases := []struct {
		target time.Time
		first  bool
		want   bool
	}{
		{date(2024, 1, 1), true, true}, // first period is inclusive of its from-date
		{date(2024, 1, 1), false, false},
		{date(2024, 1, 2), false, true},
		{date(2024, 2, 1), false, true}, // due date is inclusive in every period
		{date(2024, 2, 2), false, false},
		{date(2023, 12, 31), true, false},
	}
	for _, c := range cases {
		if got := isInPeriod(c.target, from, to, c.first); got != c.want {
			t.Errorf("isInPeriod(%s, %s, %s, first=%v) = %v, want %v",
				c.target.Format("2006-01-02"), from.Format("2006-01-02"), to.Format("2006-01-02"), c.first, got, c.want)
		}
	}
}

func TestExactDifference(t *testing.T) {
	a := date(2024, 1, 31)
	b := date(2024, 2, 29)
	if got := exactDifference(a, b, PeriodMonths); got != 0 {
		t.Errorf("exactDifference(months) = %d, want 0 (packed rule)", got)
	}
	if got := exactDifference(a, b, PeriodDays); got != 29 {
		t.Errorf("exactDifference(days) = %d, want 29", got)
	}
	if got := exactDifference(a, b, PeriodWeeks); got != 4 {
		t.Errorf("exactDifference(weeks) = %d, want 4", got)
	}
}

func TestMonthsBetweenPackedRule(t *testing.T) {
	cases := []struct {
		a, b time.Time
		want int
	}{
		{date(2024, 1, 31), date(2024, 2, 29), 0},
		{date(2024, 1, 31), date(2024, 3, 31), 2},
		{date(2024, 1, 1), date(2024, 3, 1), 2},
		{date(2024, 1, 15), date(2024, 3, 14), 1},
		{date(2024, 3, 1), date(2024, 1, 1), -2},
	}
	for _, c := range cases {
		if got := monthsBetween(c.a, c.b); got != c.want {
			t.Errorf("monthsBetween(%s, %s) = %d, want %d",
				c.a.Format("2006-01-02"), c.b.Format("2006-01-02"), got, c.want)
		}
	}
}

// ---------------------------------------------------------------------------
// End-to-end recomputation over a split period
// ---------------------------------------------------------------------------

func TestCalculateRateFactorForPeriodsAfterSplit(t *testing.T) {
	r := testRounding()
	cur := testCurrency()
	detail := testDetail()

	rp := NewRepaymentPeriod(nil, date(2023, 1, 1), date(2023, 2, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)
	m := NewScheduleModel([]*RepaymentPeriod{rp}, detail, 0, r, cur)

	// A mid-period disbursement on 2023-01-16 splits the single segment into
	// [Jan 1, Jan 16] and [Jan 16, Feb 1].
	if _, ok := m.ChangeOutstandingBalanceAndUpdateInterestPeriods(date(2023, 1, 16),
		moneyZero(cur, r), moneyZero(cur, r), moneyZero(cur, r)); !ok {
		t.Fatal("balance change was not applied")
	}

	CalculateRateFactorForPeriods(m.RepaymentPeriods(), m)

	if len(rp.InterestPeriods) != 2 {
		t.Fatalf("interest periods after split = %d, want 2", len(rp.InterestPeriods))
	}

	// Recurrence factor measures from the segment's from-date to its due date
	// (15 days / 31 days); interest factor measures from the segment's
	// from-date to the ENCLOSING period's due date (31 days / 31 days for the
	// first segment). The second segment ends on the period's due date, so the
	// two factors coincide there.
	assertRat(t, rp.InterestPeriods[0].RateFactorValue(), "0.0048387096774193548")
	assertRat(t, rp.InterestPeriods[0].RateFactorTillPeriodDueDateValue(), "0.0100000000000000000")
	assertRat(t, rp.InterestPeriods[1].RateFactorValue(), "0.0051612903225806452")
	assertRat(t, rp.InterestPeriods[1].RateFactorTillPeriodDueDateValue(), "0.0051612903225806452")
}

func TestCalculateOutstandingBalanceRollsAcrossPeriods(t *testing.T) {
	r := testRounding()
	cur := testCurrency()
	detail := testDetail()

	rp1 := NewRepaymentPeriod(nil, date(2023, 1, 1), date(2023, 2, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)
	rp2 := NewRepaymentPeriod(rp1, date(2023, 2, 1), date(2023, 3, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)

	rp1.InterestPeriods[0].AddDisbursementAmount(NewMoney(100000, cur, r)) // 1000.00
	rp2.InterestPeriods[0].AddDisbursementAmount(NewMoney(50000, cur, r))  // 500.00

	m := NewScheduleModel([]*RepaymentPeriod{rp1, rp2}, detail, 0, r, cur)
	CalculateOutstandingBalance(m)

	// The first segment of the first period has no predecessor, so its
	// outstanding balance is untouched. The first segment of the second period
	// rolls in the previous period's closing disbursement (1000.00) minus the
	// previous period's due principal (its 100.00 EMI with no accrued
	// interest), yielding 900.00.
	if got := rp2.InterestPeriods[0].OutstandingLoanBalance().Minor(); got != 90000 {
		t.Fatalf("second period outstanding = %d minor units, want 90000", got)
	}
}
