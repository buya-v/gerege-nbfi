package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/loan"
	"github.com/gerege/nexus/internal/apps/workingcapital"
)

// WorkingCapitalEvaluator is what a working-capital implementation must be able
// to do for this harness to grade it. The graded surface is the seeded
// working-capital loan (m_wc_loan id 1) seen through two capture seams: the
// loan list (GET /working-capital-loans) and the per-loan balance read-back
// (GET /working-capital-loans/1). A loan-id request for a row that does not
// exist is an error, exactly as the port reads it.
type WorkingCapitalEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]WorkingCapitalEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a WorkingCapitalEvaluator available under name.
func Register(name string, e WorkingCapitalEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("workingcapital conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e WorkingCapitalEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (WorkingCapitalEvaluator, bool) {
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

// RegisteredNames lists every registered implementation.
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

// seededBalance is the one m_wc_loan_balance state the pinned capture holds,
// transcribed from wc-loan-detail-raw.json: a 1000.51 disbursement with no
// discount fee, zero principal paid and zero overpayment. The stored columns
// the oracle serialises as the response "balance" block are reproduced by
// DERIVING the state through the port's own ApplyDisbursement — the graded
// detail read exercises the port's disbursement arithmetic and its
// outstanding/due getters, never a transcribed constant.
func seededBalance() workingcapital.WorkingCapitalLoanBalance {
	var b workingcapital.WorkingCapitalLoanBalance
	b.ApplyDisbursement(loan.MinorUnits(100051), 0)
	return b
}

// seededLoan is the working-capital loan row of the pinned capture: id 1,
// account 000000001, external id SEED-WC-L01, status ACTIVE. The status is set
// by decoding the stored ordinal 300, the value a row of m_wc_loan carries.
func seededLoan() workingcapital.WorkingCapitalLoan {
	status, ok := loan.LoanStatusFromStoredValue(300)
	if !ok {
		panic("workingcapital conformance: seeded loan status 300 must decode to ACTIVE")
	}
	return workingcapital.WorkingCapitalLoan{
		ID:            1,
		AccountNumber: "000000001",
		ExternalID:    "SEED-WC-L01",
		LoanStatus:    status,
		Balance:       seededBalance(),
	}
}

// balanceReadBack renders the cells of the seeded loan's balance read-back that
// this harness grades, as integer minor-unit strings.
func balanceReadBack(l workingcapital.WorkingCapitalLoan) *DetailExpect {
	b := l.Balance
	return &DetailExpect{
		ID:     strconv.FormatInt(int64(l.ID), 10),
		Status: l.LoanStatus.Code(),
		Balance: BalanceExpect{
			Principal:                       strconv.FormatInt(int64(b.Principal), 10),
			PrincipalPaid:                   strconv.FormatInt(int64(b.PrincipalPaid), 10),
			TotalDisbursement:               strconv.FormatInt(int64(b.TotalDisbursement), 10),
			TotalDiscountFee:                strconv.FormatInt(int64(b.TotalDiscountFee), 10),
			PrincipalOutstanding:            strconv.FormatInt(int64(b.PrincipalOutstanding()), 10),
			TotalExpectedRepayment:          strconv.FormatInt(int64(b.TotalExpectedRepayment()), 10),
			TotalRepayment:                  strconv.FormatInt(int64(b.TotalRepayment()), 10),
			TotalOutstanding:                strconv.FormatInt(int64(b.TotalOutstanding()), 10),
			UnrealizedIncomeFromDiscountFee: strconv.FormatInt(int64(b.UnrealizedIncomeFromDiscountFee()), 10),
		},
	}
}

// goEvaluator is the port-backed working-capital loan read. The pinned capture
// holds exactly one seeded working-capital loan — id 1, external id
// SEED-WC-L01, status ACTIVE (stored 300), disbursed 1000.51 with no discount.
// The list read returns the row's list cells and the detail read its balance
// read-back, both derived by running the port code over the seeded state rather
// than restated constants.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() WorkingCapitalEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	seed := seededLoan()
	if req.LoanID > 0 {
		if req.LoanID != seed.ID {
			return Expect{}, fmt.Errorf(
				"workingcapital: loan id %d is not present in the pinned capture store (only id %d is seeded)",
				req.LoanID, seed.ID)
		}
		return Expect{Detail: balanceReadBack(seed)}, nil
	}
	return Expect{
		Loans: []LoanExpect{{
			ID:         strconv.FormatInt(int64(seed.ID), 10),
			ExternalID: seed.ExternalID,
			Status:     seed.LoanStatus.Code(),
		}},
		TotalElements: 1,
	}, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it treats the
// outstanding principal as PRINCIPAL REDUCED BY WHAT WAS PAID OUT OF ORDER — it
// returns the total_outstanding cell one minor unit short of the oracle's
// 1000.51 (i.e. 1000.50), so a detail vector asserting the captured total goes
// red. Its list read keeps the captured external id so list vectors still pass
// under it: the seeded loan really is SEED-WC-L01.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	seed := seededLoan()
	if req.LoanID > 0 {
		d := balanceReadBack(seed)
		d.Balance.TotalOutstanding = "100050" // wrong: HALF_DOWN-style shorting of the outstanding penny
		return Expect{Detail: d}, nil
	}
	return Expect{
		Loans: []LoanExpect{{
			ID:         strconv.FormatInt(int64(seed.ID), 10),
			ExternalID: seed.ExternalID,
			Status:     seed.LoanStatus.Code(),
		}},
		TotalElements: 1,
	}, nil
}

func init() {
	Register("workingcapital-go", NewGoEvaluator())
	RegisterWrong("workingcapital-wrong-total-outstanding",
		"returns the balance read-back's total_outstanding as 100050 minor (1000.50) instead of the oracle's 100051 (1000.51), "+
			"so a detail vector asserting the captured total_outstanding goes red",
		wrongEvaluator{})
}
