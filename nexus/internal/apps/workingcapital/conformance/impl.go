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
// account 000000001 (the borrowing client's account is 000000005), client id 5,
// external id SEED-WC-L01, status ACTIVE. The status is set by decoding the
// stored ordinal 300, the value a row of m_wc_loan carries. The seeded draw
// (wc-loan-disburse) recorded one disbursement tranche of 1000.51, so the loan
// carries that tranche in DisbursementDetails; the tranche's calendar dates are
// not exercised on the graded read-back, which serialises no date cell.
func seededLoan() workingcapital.WorkingCapitalLoan {
	status, ok := loan.LoanStatusFromStoredValue(300)
	if !ok {
		panic("workingcapital conformance: seeded loan status 300 must decode to ACTIVE")
	}
	return workingcapital.WorkingCapitalLoan{
		ID:            1,
		AccountNumber: "000000001",
		ExternalID:    "SEED-WC-L01",
		ClientID:      5,
		LoanStatus:    status,
		Balance:       seededBalance(),
		DisbursementDetails: []workingcapital.WorkingCapitalLoanDisbursementDetails{{
			ExpectedAmount: loan.MinorUnits(100051),
			ActualAmount:   loan.MinorUnits(100051),
		}},
	}
}

// loanRowReadBack renders the cells of the seeded loan's LIST row. The list
// read serialises no money cell, so only the row identity cells are present:
// the row id, the loan row's own account number, the borrowing client's id, the
// external id and the status code.
func loanRowReadBack(l workingcapital.WorkingCapitalLoan) LoanExpect {
	return LoanExpect{
		ID:         strconv.FormatInt(int64(l.ID), 10),
		ExternalID: l.ExternalID,
		Status:     l.LoanStatus.Code(),
		AccountNo:  l.AccountNumber,
		ClientID:   strconv.FormatInt(l.ClientID, 10),
	}
}

// statusOrdinalReadBack renders the stored status ordinal a row of m_wc_loan
// carries. The status the read-back derives its code from and the ordinal a
// separate serialiser reads from the stored row must agree; pinning both is how
// a status-ordinal drift (a row left at approved while the enum reads ACTIVE)
// is caught.
func statusOrdinalReadBack(s loan.LoanStatus) (string, string) {
	ord := strconv.FormatInt(int64(s.StoredValue()), 10)
	active := "false"
	if s.IsActive() {
		active = "true"
	}
	return ord, active
}

// disbursementReadBack renders the seeded draw's disbursement tranche as the
// read-back serialises it in "disbursementDetails": the tranche's expected
// principal and its recorded actualAmount, as integer minor-unit strings. A
// loan with no recorded tranche renders no block.
func disbursementReadBack(l workingcapital.WorkingCapitalLoan) *DisbursementExpect {
	if len(l.DisbursementDetails) == 0 {
		return nil
	}
	t := l.DisbursementDetails[0]
	return &DisbursementExpect{
		Principal:    strconv.FormatInt(int64(t.ExpectedAmount), 10),
		ActualAmount: strconv.FormatInt(int64(t.ActualAmount), 10),
	}
}

// balanceReadBack renders the cells of the seeded loan's balance read-back that
// this harness grades, as integer minor-unit strings: the row id, its status
// code and stored ordinal, and the tranche the draw recorded.
func balanceReadBack(l workingcapital.WorkingCapitalLoan) *DetailExpect {
	b := l.Balance
	ord, active := statusOrdinalReadBack(l.LoanStatus)
	return &DetailExpect{
		ID:            strconv.FormatInt(int64(l.ID), 10),
		Status:        l.LoanStatus.Code(),
		StatusOrdinal: ord,
		StatusActive:  active,
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
		Disbursement: disbursementReadBack(l),
	}
}

// goEvaluator is the port-backed working-capital loan read. The pinned capture
// holds exactly one seeded working-capital loan — id 1, account 000000001,
// external id SEED-WC-L01, client id 5, status ACTIVE (stored 300), disbursed
// 1000.51 with no discount. The list read returns the row's list cells and the
// detail read its balance read-back, both derived by running the port code over
// the seeded state rather than restated constants.
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
		Loans:         []LoanExpect{loanRowReadBack(seed)},
		TotalElements: 1,
	}, nil
}

// listRead renders the seeded loan's list read; the detail read is evaluated by
// the receiver. Every deliberately wrong implementation below shares the
// correct list read unless the defect it simulates lives on the list seam.
func listRead(seed workingcapital.WorkingCapitalLoan) Expect {
	return Expect{
		Loans:         []LoanExpect{loanRowReadBack(seed)},
		TotalElements: 1,
	}
}

// requireSeedLoan validates a loan-id request against the pinned capture's one
// seeded loan and returns the seeded loan to read back.
func requireSeedLoan(seed workingcapital.WorkingCapitalLoan, req Request) (workingcapital.WorkingCapitalLoan, error) {
	if req.LoanID > 0 && req.LoanID != seed.ID {
		return seed, fmt.Errorf(
			"workingcapital: loan id %d is not present in the pinned capture store (only id %d is seeded)",
			req.LoanID, seed.ID)
	}
	return seed, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it treats the
// outstanding principal as PRINCIPAL REDUCED BY WHAT WAS PAID OUT OF ORDER — it
// returns the total_outstanding cell one minor unit short of the oracle's
// 1000.51 (i.e. 1000.50), so a detail vector asserting the captured total goes
// red. Its list read keeps the captured external id so list vectors still pass
// under it: the seeded loan really is SEED-WC-L01.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	seed, err := requireSeedLoan(seededLoan(), req)
	if err != nil {
		return Expect{}, err
	}
	if req.LoanID > 0 {
		d := balanceReadBack(seed)
		d.Balance.TotalOutstanding = "100050" // wrong: HALF_DOWN-style shorting of the outstanding penny
		return Expect{Detail: d}, nil
	}
	return listRead(seed), nil
}

// wrongTrancheDroppedEvaluator is a DELIBERATELY WRONG implementation of the
// draw write path: disbursing credits the balance row but never records the
// m_wc_loan_disbursement_detail tranche row, so the detail read-back renders no
// "disbursement" block even though the balance moved. WC-03 pins the tranche
// cells the seeded draw must have recorded and goes red under it.
type wrongTrancheDroppedEvaluator struct{}

func (wrongTrancheDroppedEvaluator) Evaluate(req Request) (Expect, error) {
	seed, err := requireSeedLoan(seededLoan(), req)
	if err != nil {
		return Expect{}, err
	}
	if req.LoanID > 0 {
		seed.DisbursementDetails = nil // wrong: the draw never wrote the tranche row
		return Expect{Detail: balanceReadBack(seed)}, nil
	}
	return listRead(seed), nil
}

// wrongStatusOrdinalEvaluator is a DELIBERATELY WRONG implementation of the
// status read-back: the code and active flag are derived from an enum that says
// ACTIVE, but the serialised status_id is read from the stored row, which the
// disburse step left stale at 200 (approved). WC-04 pins the stored ordinal 300
// and the active flag and goes red on the ordinal under it.
type wrongStatusOrdinalEvaluator struct{}

func (wrongStatusOrdinalEvaluator) Evaluate(req Request) (Expect, error) {
	seed, err := requireSeedLoan(seededLoan(), req)
	if err != nil {
		return Expect{}, err
	}
	if req.LoanID > 0 {
		d := balanceReadBack(seed)
		d.StatusOrdinal = "200" // wrong: stale m_wc_loan.loan_status_id left at approved
		return Expect{Detail: d}, nil
	}
	return listRead(seed), nil
}

// wrongListRowMappingEvaluator is a DELIBERATELY WRONG implementation of the
// list read: the row mapper emits the client's account number (000000005, the
// row's clientAccountNo) in place of the loan row's own account_no
// (000000001). The list row therefore names the wrong account while the detail
// read stays correct. WC-05 pins account_no and goes red under it.
type wrongListRowMappingEvaluator struct{}

func (wrongListRowMappingEvaluator) Evaluate(req Request) (Expect, error) {
	seed, err := requireSeedLoan(seededLoan(), req)
	if err != nil {
		return Expect{}, err
	}
	if req.LoanID > 0 {
		return Expect{Detail: balanceReadBack(seed)}, nil
	}
	row := loanRowReadBack(seed)
	row.AccountNo = "000000005" // wrong: the borrowing client's account_no, not the loan row's
	return Expect{
		Loans:         []LoanExpect{row},
		TotalElements: 1,
	}, nil
}

func init() {
	Register("workingcapital-go", NewGoEvaluator())
	RegisterWrong("workingcapital-wrong-total-outstanding",
		"returns the balance read-back's total_outstanding as 100050 minor (1000.50) instead of the oracle's 100051 (1000.51), "+
			"so a detail vector asserting the captured total_outstanding goes red",
		wrongEvaluator{})
	RegisterWrong("workingcapital-wrong-tranche-dropped",
		"credits the disbursed balance but never records the m_wc_loan_disbursement_detail tranche row, so the detail read-back "+
			"renders no disbursement block; a vector pinning the seeded tranche's principal/actual_amount goes red",
		wrongTrancheDroppedEvaluator{})
	RegisterWrong("workingcapital-wrong-status-ordinal",
		"serialises the detail read-back's status_id from a stored row left stale at 200 (approved) while code/active read ACTIVE; "+
			"a vector pinning the stored ordinal 300 and the active flag goes red",
		wrongStatusOrdinalEvaluator{})
	RegisterWrong("workingcapital-wrong-list-row-mapping",
		"emits the borrowing client's account_no (000000005) for the loan row's own account_no (000000001) on the list read; "+
			"a list vector pinning account_no goes red",
		wrongListRowMappingEvaluator{})
}
