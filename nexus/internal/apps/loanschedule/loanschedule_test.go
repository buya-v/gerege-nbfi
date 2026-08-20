package loanschedule

import (
	"context"
	"errors"
	"math/big"
	"testing"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// These tests are NOT a substitute for the golden-vector conformance run, and
// nothing here may ever become one: an expectation this package writes about
// itself is not an observation of the reference oracle. They cover two things
// the corpus cannot:
//
//   - the exact-arithmetic and civil-date primitives, against values that are
//     properties of java.math.BigDecimal and java.time.LocalDate rather than of
//     any schedule; and
//   - the EMI re-adjust loop, which .softhouse/conformance.sh grades on NOTHING
//     because no promoted vector trips its guard. The two shapes at the bottom
//     are the reference oracle's own OBSERVED figures, recorded in the ratified
//     contract's doc comment on Period; they are cited there, not invented here.

func date(y, m, d int32) civilDate { return civilDate{Year: y, Month: m, Day: d} }

func rat(s string) *big.Rat {
	v, ok := new(big.Rat).SetString(s)
	if !ok {
		panic("bad rational literal " + s)
	}
	return v
}

func TestRoundSignificantKeepsSignificantDigitsNotPlaces(t *testing.T) {
	cases := []struct {
		in   string
		prec int32
		want string
	}{
		// The distinction this whole package turns on: on a rate-factor-sized
		// quantity a SCALE of 12 keeps 12 places while a PRECISION of 12 keeps 12
		// digits, and the leading zeros buy nothing.
		{"7/1200", 12, "0.00583333333333"},
		{"7/1200", 19, "0.005833333333333333333"},
		// Ties go away from zero. Note that the tie is decided at the digit the
		// PRECISION reaches, not at a fixed place: 0.005 to one significant digit
		// is 0.005, because the 5 IS the digit.
		{"5/1000", 1, "0.005"},
		{"15/100", 1, "0.2"},
		{"-15/100", 1, "-0.2"},
		{"15/1000", 1, "0.02"},
		// A carry that lengthens the integer part is the same NUMBER as Java's
		// 1.0E+1, which is all this package ever consumes.
		{"999/100", 2, "10"},
		{"0/1", 19, "0"},
	}
	for _, c := range cases {
		got := roundSignificant(rat(c.in), c.prec)
		if got.Cmp(rat(c.want)) != 0 {
			t.Errorf("roundSignificant(%s, %d) = %s, want %s", c.in, c.prec, got.RatString(), c.want)
		}
	}
}

func TestRoundScaleIsPlacesAndIsLossierThanPrecision(t *testing.T) {
	// The trailing setScale of the rate factor. At scale 12 a quantity of order
	// 0.0058 keeps only nine significant digits.
	x := rat("7/1200")
	if got := roundScale(x, 12); got.Cmp(rat("0.005833333333")) != 0 {
		t.Errorf("roundScale(7/1200, 12) = %s", got.RatString())
	}
	if got := roundScale(rat("1234"), -2); got.Cmp(rat("1200")) != 0 {
		t.Errorf("roundScale(1234, -2) = %s, want 1200", got.RatString())
	}
	if got := roundScale(rat("1250"), -2); got.Cmp(rat("1300")) != 0 {
		t.Errorf("roundScale(1250, -2) = %s, want 1300 (tie away from zero)", got.RatString())
	}
}

func TestDivideMinorHalfUpTiesAwayFromZero(t *testing.T) {
	cases := []struct{ amount, divisor, want int64 }{
		{5, 2, 3}, {-5, 2, -3}, {4, 2, 2}, {3, 2, 2}, {-3, 2, -2},
		{1, 3, 0}, {2, 3, 1}, {-2, 3, -1}, {7, 1, 7}, {0, 6, 0},
	}
	for _, c := range cases {
		if got := divideMinorHalfUp(c.amount, c.divisor); got != c.want {
			t.Errorf("divideMinorHalfUp(%d, %d) = %d, want %d", c.amount, c.divisor, got, c.want)
		}
	}
}

func TestPlusMonthsClampsLikeJavaTime(t *testing.T) {
	cases := []struct {
		from civilDate
		n    int64
		want civilDate
	}{
		{date(2024, 1, 31), 1, date(2024, 2, 29)},
		{date(2023, 1, 31), 1, date(2023, 2, 28)},
		{date(2024, 1, 30), 1, date(2024, 2, 29)},
		{date(2024, 3, 31), -1, date(2024, 2, 29)},
		{date(2024, 1, 31), 12, date(2025, 1, 31)},
	}
	for _, c := range cases {
		if got := plusMonths(c.from, c.n); compareDates(got, c.want) != 0 {
			t.Errorf("plusMonths(%s, %d) = %s, want %s",
				formatDate(c.from), c.n, formatDate(got), formatDate(c.want))
		}
	}
}

// TestMonthsBetweenIsThePackedRule pins the difference the month-end special
// case of periodRatio exists to compensate for. The packed rule is NOT "the
// largest k with seed + k months <= target": 2024-01-31 to 2024-02-29 is ZERO
// packed months (day 29 < day 31) where the clamped-step reading gives one.
func TestMonthsBetweenIsThePackedRule(t *testing.T) {
	cases := []struct {
		a, b civilDate
		want int64
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
				formatDate(c.a), formatDate(c.b), got, c.want)
		}
	}
}

func TestEpochDayRoundTrips(t *testing.T) {
	for _, d := range []civilDate{
		date(1970, 1, 1), date(2024, 2, 29), date(1899, 12, 31), date(2400, 3, 1), date(1600, 1, 1),
	} {
		if got := fromEpochDay(epochDay(d)); compareDates(got, d) != 0 {
			t.Errorf("epoch round trip of %s gave %s", formatDate(d), formatDate(got))
		}
	}
	if got := daysBetween(date(2024, 1, 1), date(2024, 7, 1)); got != 182 {
		t.Errorf("daysBetween 2024-01-01 -> 2024-07-01 = %d, want 182", got)
	}
}

// TestMonthEndReAnchorRemembersTheSeedDay is the date-column kill that carries
// zero money margin: under a fixed 30/360 day count every amount is
// date-independent, so a port that clamps and forgets the seed produces
// identical money and the wrong dates.
func TestMonthEndReAnchorRemembersTheSeedDay(t *testing.T) {
	got, err := repaymentDueDates(context.Background(), date(2024, 1, 31), 6, 1,
		contract.FrequencyMonths, date(2024, 1, 31))
	if err != nil {
		t.Fatal(err)
	}
	want := []civilDate{
		date(2024, 2, 29), date(2024, 3, 31), date(2024, 4, 30),
		date(2024, 5, 31), date(2024, 6, 30), date(2024, 7, 31),
	}
	for i := range want {
		if compareDates(got[i], want[i]) != 0 {
			t.Fatalf("period %d due %s, want %s (the clamped day is remembered in the SEED and never "+
				"becomes the new seed)", i+1, formatDate(got[i]), formatDate(want[i]))
		}
	}
	got30, err := repaymentDueDates(context.Background(), date(2024, 1, 30), 6, 1,
		contract.FrequencyMonths, date(2024, 1, 30))
	if err != nil {
		t.Fatal(err)
	}
	want30 := []civilDate{
		date(2024, 2, 29), date(2024, 3, 30), date(2024, 4, 30),
		date(2024, 5, 30), date(2024, 6, 30), date(2024, 7, 30),
	}
	for i := range want30 {
		if compareDates(got30[i], want30[i]) != 0 {
			t.Fatalf("seed-30 period %d due %s, want %s", i+1, formatDate(got30[i]), formatDate(want30[i]))
		}
	}
}

// baseRequest is a request strictly inside the graded domain.
func baseRequest(principalMinor int64, repayments int32, rate contract.Rate) contract.GenerateRequest {
	return contract.GenerateRequest{
		TimeZone:                  "Asia/Ulaanbaatar",
		Currency:                  contract.Currency{Code: "MNT", MinorUnitDigits: 2},
		Rounding:                  contract.Rounding{SignificantDigits: 19, RateFactorScale: 19, Mode: contract.RoundingHalfUp},
		ScheduleStartDate:         date(2024, 1, 1),
		Disbursements:             []contract.Disbursement{{Date: date(2024, 1, 1), AmountMinor: principalMinor}},
		NumberOfRepayments:        repayments,
		RepaymentEvery:            1,
		RepaymentFrequencyUnit:    contract.FrequencyMonths,
		AnnualNominalInterestRate: rate,
		InterestMethod:            contract.InterestMethodDecliningBalance,
		DayCount:                  contract.DayCountFixed30Over360,
		DownPaymentPercentage:     contract.Rate{Numerator: 0, Denominator: 1},
	}
}

// TestEMIReAdjustLoopReproducesTheOraclesObservedFigures is the only check in
// this repository that says anything at all about the EMI re-adjust smoothing
// loop.
//
// NO PROMOTED VECTOR TRIPS ITS GUARD -- the conformance run is silent about it,
// and a PASS there is not evidence that the loop is implemented at all. The two
// shapes below are the reference oracle's own figures, OBSERVED at (19, HALF_UP)
// strictly inside the graded domain and recorded in the ratified contract's doc
// comment on Period ("This moves money on ordinary loans"). They are quoted, not
// derived, and they are an ATTESTED READING OF A RATIFIED DOCUMENT rather than a
// promoted vector -- which is exactly why this lives in a test and not in the
// vector store.
func TestEMIReAdjustLoopReproducesTheOraclesObservedFigures(t *testing.T) {
	// MNT 1,014,632 / 6 * 7.0%: oracle level installment 172,574.64
	// (a model without the loop returns 172,574.63 and every period shifts).
	got, err := Generator{}.Generate(context.Background(),
		baseRequest(101463200, 6, contract.Rate{Numerator: 7, Denominator: 100}))
	if err != nil {
		t.Fatalf("shape 1: %v", err)
	}
	level := got.Periods[1].PrincipalMinor + got.Periods[1].InterestMinor
	if level != 17257464 {
		t.Errorf("MNT 1,014,632 / 6 * 7.0%%: level installment %d minor units, the oracle observed "+
			"17257464 (172,574.64). A model without the EMI re-adjust loop returns 17257463.", level)
	}

	// MNT 127,704 / 36 * 16.8%: oracle total interest 35,746.56
	// (a model without the loop returns 35,746.69).
	got, err = Generator{}.Generate(context.Background(),
		baseRequest(12770400, 36, contract.Rate{Numerator: 21, Denominator: 125}))
	if err != nil {
		t.Fatalf("shape 2: %v", err)
	}
	var totalInterest int64
	for _, p := range got.Periods {
		totalInterest += p.InterestMinor
	}
	if totalInterest != 3574656 {
		t.Errorf("MNT 127,704 / 36 * 16.8%%: total interest %d minor units, the oracle observed "+
			"3574656 (35,746.56). A model without the EMI re-adjust loop returns 3574669.", totalInterest)
	}
}

// TestRefusalPrecedence pins the contract's normative error precedence: a
// request refusable for more than one reason returns the FIRST applicable
// sentinel, strongest obstruction first, so both implementations return the same
// one and a request one refuses and the other answers can never be mistaken for
// a conformance failure.
func TestRefusalPrecedence(t *testing.T) {
	var g Generator
	annualHalfEven := baseRequest(120000000, 3, contract.Rate{Numerator: 27, Denominator: 125})
	annualHalfEven.RepaymentFrequencyUnit = contract.FrequencyYears
	annualHalfEven.Rounding.Mode = contract.RoundingHalfEven
	_, err := g.Generate(context.Background(), annualHalfEven)
	if !errors.Is(err, contract.ErrUnsupportedConfiguration) || errors.Is(err, contract.ErrNoDiscriminatingVector) {
		t.Errorf("annual on the fixed-30/360 arm together with HALF_EVEN must be exactly "+
			"ErrUnsupportedConfiguration (the oracle cannot be asked at all), got %v", err)
	}

	malformed := baseRequest(120000000, 0, contract.Rate{Numerator: 27, Denominator: 125})
	malformed.DayCount = contract.DayCountActualActual
	_, err = g.Generate(context.Background(), malformed)
	if !errors.Is(err, contract.ErrInvalidRequest) || errors.Is(err, contract.ErrUnsupportedConfiguration) {
		t.Errorf("NumberOfRepayments below 1 is a WELL-FORMEDNESS failure and wins over any "+
			"graded-domain refusal, got %v", err)
	}

	offset := baseRequest(120000000, 6, contract.Rate{Numerator: 7, Denominator: 100})
	offset.TimeZone = "UTC+8"
	if _, err := g.Generate(context.Background(), offset); !errors.Is(err, contract.ErrInvalidRequest) {
		t.Errorf("a fixed offset is not an IANA zone name, got %v", err)
	}

	for _, tz := range []string{"Asia/Ulaanbaatar", "Asia/Hovd", "UTC"} {
		ok := baseRequest(120000000, 6, contract.Rate{Numerator: 7, Denominator: 100})
		ok.TimeZone = tz
		if _, err := g.Generate(context.Background(), ok); err != nil {
			t.Errorf("time zone %q must be accepted, got %v", tz, err)
		}
	}
}

// TestGenerationIsDeterministic: an equal request yields an equal schedule, on
// every call. Cheap, and the contract requires it explicitly.
func TestGenerationIsDeterministic(t *testing.T) {
	req := baseRequest(5000000000, 18, contract.Rate{Numerator: 37, Denominator: 200})
	first, err := Generator{}.Generate(context.Background(), req)
	if err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 5; i++ {
		again, err := Generator{}.Generate(context.Background(), req)
		if err != nil {
			t.Fatal(err)
		}
		if len(again.Periods) != len(first.Periods) {
			t.Fatalf("run %d returned %d rows, first returned %d", i, len(again.Periods), len(first.Periods))
		}
		for j := range first.Periods {
			a, b := again.Periods[j], first.Periods[j]
			if a != b {
				t.Fatalf("run %d row %d differs from the first run", i, j)
			}
		}
	}
}
