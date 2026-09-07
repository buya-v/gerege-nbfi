package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/loan"
	shared "github.com/gerege/nexus/internal/conformance"
)

// LoanEvaluator is what a loan implementation must be able to do for this
// harness to grade it. The graded surface is the three capture seams:
//
//   - seam loan-repayment-allocation: the four-bucket greedy allocation of a
//     repayment across a single instalment's outstanding buckets, graded by
//     loan.AllocatePayment;
//   - seam loan-schedule-interest: the single-period interest of the
//     discriminating loan, the one cell the MANIFEST records as its rounding
//     surface (HALF_UP vs HALF_EVEN);
//   - seam loan-disbursement: the net disbursal amount, graded by
//     loan.NetDisbursalAmount.
type LoanEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]LoanEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a LoanEvaluator available under name.
func Register(name string, e LoanEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("loan conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e LoanEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (LoanEvaluator, bool) {
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

// mifosOrder is the repayment allocation order of the mifos-standard-strategy:
// penalties, then fees, then interest, then principal, each at the DUE due-type
// (the SEED-L03 repayment had no past-due or in-advance component, so the
// in-advance/past-due buckets are empty and irrelevant to the allocation).
var mifosOrder = []loan.PaymentAllocationType{
	loan.PaymentDuePenalty, loan.PaymentDueFee, loan.PaymentDueInterest, loan.PaymentDuePrincipal,
}

// parseMinorText parses a vector's monetary text field into integer minor units.
// The parse lives in nexus/internal/conformance; this wrapper adapts the shared
// int64 result to the loan MinorUnits type.
func parseMinorText(text string) (loan.MinorUnits, error) {
	n, err := shared.ParseMinorInt(text)
	if err != nil {
		return 0, err
	}
	return loan.MinorUnits(n), nil
}

// goEvaluator is the port-backed implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() LoanEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch {
	case req.Repayment != nil:
		return goRepayment(*req.Repayment)
	case req.Schedule != nil:
		return goSchedule(*req.Schedule, roundHalfUp)
	case req.Disburse != nil:
		return goDisburse(*req.Disburse)
	default:
		return Expect{}, fmt.Errorf("loan: request must set exactly one of repayment, schedule, disburse")
	}
}

func goRepayment(r RepaymentRequest) (Expect, error) {
	penalty, err := parseMinorText(r.Outstanding.Penalty)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(r.Outstanding.Fee)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(r.Outstanding.Interest)
	if err != nil {
		return Expect{}, err
	}
	principal, err := parseMinorText(r.Outstanding.Principal)
	if err != nil {
		return Expect{}, err
	}
	amount, err := parseMinorText(r.AmountMinor)
	if err != nil {
		return Expect{}, err
	}
	outstanding := loan.Allocation{Penalty: penalty, Fee: fee, Interest: interest, Principal: principal}
	alloc, leftover := loan.AllocatePayment(outstanding, amount, mifosOrder)
	return Expect{
		Allocation: &AllocationMoney{
			Penalty:   strconv.FormatInt(int64(alloc.Penalty), 10),
			Fee:       strconv.FormatInt(int64(alloc.Fee), 10),
			Interest:  strconv.FormatInt(int64(alloc.Interest), 10),
			Principal: strconv.FormatInt(int64(alloc.Principal), 10),
		},
		LeftoverMinor: strconv.FormatInt(int64(leftover), 10),
	}, nil
}

func goSchedule(s ScheduleRequest, round func(numerator, denominator *big.Int) int64) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalMinor)
	if err != nil {
		return Expect{}, err
	}
	interest := scheduleInterestMinor(int64(principal), s.RatePerAnnumPct, s.DaysInMonth, s.DaysInYear, round)
	return Expect{InterestMinor: strconv.FormatInt(interest, 10)}, nil
}

func goDisburse(d DisburseRequest) (Expect, error) {
	approved, err := parseMinorText(d.ApprovedPrincipalMinor)
	if err != nil {
		return Expect{}, err
	}
	charges, err := parseMinorText(d.ChargesDueAtDisbursementMinor)
	if err != nil {
		return Expect{}, err
	}
	net := loan.NetDisbursalAmount(approved, charges)
	return Expect{NetDisbursalMinor: strconv.FormatInt(int64(net), 10)}, nil
}

// scheduleInterestMinor ports the single-period interest of the MANIFEST's
// discriminating loan: interest = round(principal * ratePct * daysInMonth,
// 100 * daysInYear), the HALF_UP instance of
// interest = principal * (ratePct/100) * (daysInMonth/daysInYear).
//
// The loan slice does NOT own schedule generation (the loanschedule context
// does); this is the ONE cell the MANIFEST records as the loan context's
// discriminating rounding surface, not a port of the whole amortisation.
// The numerator is computed in big.Int so the rounding is exact for any
// captured magnitude, not merely the seed's.
func scheduleInterestMinor(principal, ratePct, daysInMonth, daysInYear int64, round func(numerator, denominator *big.Int) int64) int64 {
	num := new(big.Int).Mul(big.NewInt(principal), big.NewInt(ratePct))
	num.Mul(num, big.NewInt(daysInMonth))
	den := new(big.Int).Mul(big.NewInt(100), big.NewInt(daysInYear))
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
// red: the oracle posted 1000.51 under HALF_UP where HALF_EVEN would have
// posted 1000.50.
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
// discriminating schedule-interest cell with HALF_EVEN instead of HALF_UP, so a
// vector that asserts that cell goes red (100050 minor vs the oracle's 100051).
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Schedule != nil {
		return goSchedule(*req.Schedule, roundHalfEven)
	}
	return w.goEvaluator.Evaluate(req)
}

func init() {
	Register("loan-go", NewGoEvaluator())
	RegisterWrong("loan-wrong-half-even-schedule-interest",
		"rounds the discriminating schedule-interest cell with HALF_EVEN instead of HALF_UP, "+
			"so the pinned 1000.51 observation reads 1000.50 and the vector goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
