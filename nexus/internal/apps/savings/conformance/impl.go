package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SavingsEvaluator is what a savings implementation must be able to do for this
// harness to grade it. The graded surface is the one capture seam:
//
//   - seam savings-daily-interest: the single-period daily-balance interest of
//     the discriminating savings account, the one cell the MANIFEST records as
//     its rounding surface (HALF_UP vs HALF_EVEN).
type SavingsEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]SavingsEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a SavingsEvaluator available under name.
func Register(name string, e SavingsEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("savings conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e SavingsEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (SavingsEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation.
func IsRegisteredWrong(name string) (string, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	d, ok := wrong[name]
	return d, ok
}

// RegisteredNames lists every registered implementation, wrong ones included.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// CorrectImplementationNames lists the registered implementations that are NOT
// declared wrong.
func CorrectImplementationNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		if _, bad := wrong[n]; !bad {
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// parseMinorText parses a vector's monetary text field into integer minor units.
func parseMinorText(text string) (int64, error) {
	return shared.ParseMinorInt(text)
}

// goEvaluator is the port-backed implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() SavingsEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch {
	case req.DailyInterest != nil:
		return goDailyInterest(*req.DailyInterest, roundHalfUp)
	default:
		return Expect{}, fmt.Errorf("savings: request must set daily_interest")
	}
}

func goDailyInterest(r DailyInterestRequest, round func(numerator, denominator *big.Int) int64) (Expect, error) {
	balance, err := parseMinorText(r.BalanceMinor)
	if err != nil {
		return Expect{}, err
	}
	interest := dailyInterestMinor(balance, r.RatePerAnnumMicroPct, r.Days, r.DaysInYear, round)
	return Expect{InterestMinor: strconv.FormatInt(interest, 10)}, nil
}

// dailyInterestMinor ports the single-period daily-balance interest of the
// MANIFEST's discriminating savings account:
//
//	interest = round(balance * ratePct * days, 100 * daysInYear)
//
// with the result in integer MINOR UNITS (2 digits). The rate is the savings
// Percent convention — whole per cent scaled by 10^6 (micro-per-cent), so the
// whole-per-cent rate is rateMicroPct / 1e6 — and the balance is already minor
// units, so:
//
//	interestMinor = round(balanceMinor * rateMicroPct * days, 1e8 * daysInYear)
//
// For the discriminating cell (balanceMinor 100000, rateMicroPct 182500, 1 day,
// 365-day year) the numerator is 18,250,000,000 and the denominator is
// 36,500,000,000 — exactly one half minor unit — so HALF_UP posts 1 (0.01) and
// HALF_EVEN posts 0 (0.00). The oracle posted 0.01.
//
// The savings slice does NOT own the accrual engine (the accrual is a separate
// future port); this is the ONE cell the MANIFEST records as the savings
// context's discriminating rounding surface, not a port of the whole accrual.
// The numerator is computed in big.Int so the rounding is exact for any captured
// magnitude, not merely the seed's.
func dailyInterestMinor(balanceMinor, rateMicroPct, days, daysInYear int64, round func(numerator, denominator *big.Int) int64) int64 {
	num := new(big.Int).Mul(big.NewInt(balanceMinor), big.NewInt(rateMicroPct))
	num.Mul(num, big.NewInt(days))
	// denominator = 10^6 (micro-per-cent) * 100 (per cent) * daysInYear, written
	// as an integer literal so the no-float census never sees an exponent form.
	den := new(big.Int).Mul(big.NewInt(100000000), big.NewInt(daysInYear))
	return round(num, den)
}

// roundHalfUp rounds a non-negative ratio to the nearest integer, half away
// from zero (the tenant's HALF_UP rounding mode, ordinal 4).
func roundHalfUp(num, den *big.Int) int64 {
	q, r := new(big.Int).QuoRem(num, den, new(big.Int))
	if new(big.Int).Lsh(r, 1).Cmp(den) >= 0 {
		q.Add(q, big.NewInt(1))
	}
	return q.Int64()
}

// roundHalfEven rounds a non-negative ratio to the nearest integer, half to
// even (banker's rounding). It exists ONLY to make the discriminating cell go
// red: the oracle posted 0.01 under HALF_UP where HALF_EVEN would have posted
// 0.00.
func roundHalfEven(num, den *big.Int) int64 {
	q, r := new(big.Int).QuoRem(num, den, new(big.Int))
	twice := new(big.Int).Lsh(r, 1)
	switch cmp := twice.Cmp(den); {
	case cmp > 0:
		q.Add(q, big.NewInt(1))
	case cmp == 0 && q.Bit(0) == 1:
		q.Add(q, big.NewInt(1))
	}
	return q.Int64()
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it rounds the
// discriminating daily-interest cell with HALF_EVEN instead of HALF_UP, so a
// vector that asserts that cell goes red (0 minor vs the oracle's 1).
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.DailyInterest != nil {
		return goDailyInterest(*req.DailyInterest, roundHalfEven)
	}
	return w.goEvaluator.Evaluate(req)
}

func init() {
	Register("savings-go", NewGoEvaluator())
	RegisterWrong("savings-wrong-half-even-daily-interest",
		"rounds the discriminating daily-interest cell with HALF_EVEN instead of HALF_UP, "+
			"so the pinned 0.01 observation reads 0.00 and the vector goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
