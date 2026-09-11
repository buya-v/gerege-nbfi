package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
	"sync"

	"github.com/gerege/nexus/internal/apps/loan"
	"github.com/gerege/nexus/internal/apps/workingcapital"
)

// WorkingCapitalEvaluator is what a working-capital implementation must be able
// to do for this harness to grade it. Two committed captures are graded through
// two seams: the loan list (GET /working-capital-loans) and the per-loan balance
// read-back (GET /working-capital-loans/{id}). The rows are the no-discount seed
// (m_wc_loan id 1, disbursed 1000.51) and the discount-nonzero facility (id 2,
// disbursed 1000, product discount 37.53, so totalDiscountFee 3753 and principal
// 103753). A loan-id request for a row that does not exist is an error, exactly
// as the port reads it.
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
	if err := b.ApplyDisbursement(loan.MinorUnits(100051), 0); err != nil {
		panic(fmt.Sprintf("workingcapital conformance: the pinned seed disbursement (100051, no discount) must be admitted by the graded domain: %v", err))
	}
	return b
}

// observedAllocationNames is the payment-allocation order the committed
// wc-loan-detail-raw.json records for the seeded loan, in the exact order the
// capture lists it under paymentAllocation[0].paymentAllocationOrder. It is a
// transcription of the observed names, not a computation: nothing here is
// derived from the port yet.
var observedAllocationNames = []string{
	"DUE_PENALTY",
	"DUE_FEE",
	"DUE_PRINCIPAL",
	"IN_ADVANCE_PENALTY",
	"IN_ADVANCE_FEE",
	"IN_ADVANCE_PRINCIPAL",
}

// seedAllocationRules turns the observed payment-allocation order into the
// typed rule the loan carries by decoding it through the port's OWN list
// converter. SplitAllocationTypes is the persistence read
// (GenericEnumListConverter.convertToEntityAttribute), so the sequence
// name -> converter -> typed order is the port's, not a restated table; the
// observed names are joined into the comma-separated stored form the converter
// consumes. A decode failure is fatal: the observed rule is known-good, so an
// error here is a port defect, not a data variant.
func seedAllocationRules() []workingcapital.WorkingCapitalLoanPaymentAllocationRule {
	types, err := workingcapital.SplitAllocationTypes(strings.Join(observedAllocationNames, ","))
	if err != nil {
		panic(fmt.Sprintf("workingcapital conformance: the observed payment-allocation order must decode: %v", err))
	}
	return []workingcapital.WorkingCapitalLoanPaymentAllocationRule{{
		ID:              1,
		LoanID:          1,
		TransactionType: "DEFAULT",
		AllocationTypes: types,
	}}
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
		ID:                     1,
		AccountNumber:          "000000001",
		ExternalID:             "SEED-WC-L01",
		ClientID:               5,
		LoanStatus:             status,
		Balance:                seededBalance(),
		PaymentAllocationRules: seedAllocationRules(),
		DisbursementDetails: []workingcapital.WorkingCapitalLoanDisbursementDetails{{
			ExpectedAmount: loan.MinorUnits(100051),
			ActualAmount:   loan.MinorUnits(100051),
		}},
	}
}

// seededDiscountBalance is the second committed m_wc_loan_balance state: the
// discount-nonzero facility (capture wc-discount-nonzero, loan id 2), disbursed
// 1000 on a product whose discount is 37.53 MNT. Derived through the port's own
// ApplyDisbursement(100000, 3753), the oracle's applyDisbursement sets
// totalDiscountFee = discount and principal = disbursed + discount
// [WorkingCapitalLoanBalance.java:115-120], landing on totalDiscountFee 3753 and
// principal 103753 exactly as the committed read-back records them.
func seededDiscountBalance() workingcapital.WorkingCapitalLoanBalance {
	var b workingcapital.WorkingCapitalLoanBalance
	if err := b.ApplyDisbursement(loan.MinorUnits(100000), loan.MinorUnits(3753)); err != nil {
		panic(fmt.Sprintf("workingcapital conformance: the discount-nonzero capture's disbursement (100000, discount 3753) must be admitted by the graded domain: %v", err))
	}
	return b
}

// seededDiscountLoan is the discount-nonzero facility row: m_wc_loan id 2,
// account 000000002, external id OHWCCAP-DISCNONZERO-L01, client id 5, status
// ACTIVE (stored 300), disbursed 1000 on 2026-09-03 with a product discount of
// 37.53 so its balance carries totalDiscountFee 3753 and principal 103753. The
// draw recorded one tranche of 1000.
func seededDiscountLoan() workingcapital.WorkingCapitalLoan {
	status, ok := loan.LoanStatusFromStoredValue(300)
	if !ok {
		panic("workingcapital conformance: discount-nonzero loan status 300 must decode to ACTIVE")
	}
	return workingcapital.WorkingCapitalLoan{
		ID:            2,
		AccountNumber: "000000002",
		ExternalID:    "OHWCCAP-DISCNONZERO-L01",
		ClientID:      5,
		LoanStatus:    status,
		Balance:       seededDiscountBalance(),
		DisbursementDetails: []workingcapital.WorkingCapitalLoanDisbursementDetails{{
			ExpectedAmount: loan.MinorUnits(100000),
			ActualAmount:   loan.MinorUnits(100000),
		}},
	}
}

// seededLoanByID returns the committed balance state a loan-id request selects.
// Ids 1 and 2 are the two captured rows; any other id is absent, which the
// evaluator reports as an error.
func seededLoanByID(id int64) (workingcapital.WorkingCapitalLoan, bool) {
	switch id {
	case 1:
		return seededLoan(), true
	case 2:
		return seededDiscountLoan(), true
	default:
		return workingcapital.WorkingCapitalLoan{}, false
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
		Allocation:   allocationReadBack(l),
	}
}

// allocationReadBack renders a loan's payment-allocation rule as the detail
// read-back serialises it: the transaction type and the ORDERED decode of its
// allocation buckets, each bucket carrying the name the read-back shows and the
// DueType/AllocationType the port classifies that name to. This is a
// decode/classification render — it moves no money. A loan carrying no rule
// renders no allocation block, exactly as the read-back omits it.
func allocationReadBack(l workingcapital.WorkingCapitalLoan) *PaymentAllocationExpect {
	if len(l.PaymentAllocationRules) == 0 {
		return nil
	}
	r := l.PaymentAllocationRules[0]
	out := &PaymentAllocationExpect{TransactionType: r.TransactionType}
	for _, t := range r.AllocationTypes {
		out.Rules = append(out.Rules, AllocationRuleExpect{
			Name:           t.String(),
			Code:           t.Code(),
			DueType:        t.DueType().String(),
			AllocationType: t.AllocationType().String(),
		})
	}
	return out
}

// goEvaluator is the port-backed working-capital loan read. The committed
// captures hold two rows: the no-discount seed (id 1, account 000000001,
// external id SEED-WC-L01, disbursed 1000.51) and the discount-nonzero facility
// (id 2, account 000000002, external id OHWCCAP-DISCNONZERO-L01, disbursed 1000
// with discount 3753, so principal 103753). The list read returns the seed's row
// cells (the list capture holds only loan 1) and the detail read the selected
// loan's balance read-back, both derived by running the port code over the
// captured state rather than restated constants.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() WorkingCapitalEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID <= 0 {
		return listRead(seededLoan()), nil
	}
	seed, ok := seededLoanByID(req.LoanID)
	if !ok {
		return Expect{}, fmt.Errorf(
			"workingcapital: loan id %d is not present in the pinned capture store (seeded ids are 1 and 2)",
			req.LoanID)
	}
	return Expect{Detail: balanceReadBack(seed)}, nil
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
	// The defect is scoped to the no-discount seed it was written against; the
	// discount-nonzero row is delegated to the correct read so this drive stays a
	// clean instrument over the whole store rather than a harness error.
	if req.LoanID != 1 {
		return goEvaluator{}.Evaluate(req)
	}
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
	// Scoped to the no-discount seed; the discount-nonzero row is delegated to
	// the correct read (see wrongEvaluator).
	if req.LoanID != 1 {
		return goEvaluator{}.Evaluate(req)
	}
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
	// Scoped to the no-discount seed; the discount-nonzero row is delegated to
	// the correct read (see wrongEvaluator).
	if req.LoanID != 1 {
		return goEvaluator{}.Evaluate(req)
	}
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
	// The defect lives on the list seam; every detail row is delegated to the
	// correct read, including the discount-nonzero row.
	if req.LoanID > 0 {
		return goEvaluator{}.Evaluate(req)
	}
	seed, err := requireSeedLoan(seededLoan(), req)
	if err != nil {
		return Expect{}, err
	}
	row := loanRowReadBack(seed)
	row.AccountNo = "000000005" // wrong: the borrowing client's account_no, not the loan row's
	return Expect{
		Loans:         []LoanExpect{row},
		TotalElements: 1,
	}, nil
}

// wrongDiscountDroppedFromPrincipalEvaluator is a DELIBERATELY WRONG
// implementation of the disbursement arithmetic: it stores the product discount
// in totalDiscountFee but sets principal to the DISBURSED AMOUNT ALONE, dropping
// the discount the oracle ADDS to principal
// [WorkingCapitalLoanBalance.java:115-120:
// this.principal = disbursedAmount.add(discount)]. Every balance the earlier
// captures held carried totalDiscountFee 0, so dropping the add changed nothing
// and the defect was invisible; the discount-nonzero facility (WC-06) pins
// principal 103753 and goes red on principal and on the outstanding/expected
// aggregates derived from it. Its no-discount detail read and its list read stay
// correct.
type wrongDiscountDroppedFromPrincipalEvaluator struct{}

func (wrongDiscountDroppedFromPrincipalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID <= 0 {
		return listRead(seededLoan()), nil
	}
	seed, ok := seededLoanByID(req.LoanID)
	if !ok {
		return Expect{}, fmt.Errorf(
			"workingcapital: loan id %d is not present in the pinned capture store (seeded ids are 1 and 2)",
			req.LoanID)
	}
	seed.Balance.Principal -= seed.Balance.TotalDiscountFee // wrong: principal = disbursed, not disbursed + discount
	return Expect{Detail: balanceReadBack(seed)}, nil
}

// allocationRulesOf returns the mutable allocation rule slice of a detail
// read-back, or nil when the read-back carries no payment-allocation block. The
// slice aliases the read-back, so a caller mutating an element changes the
// graded result.
func allocationRulesOf(got Expect) []AllocationRuleExpect {
	if got.Detail == nil || got.Detail.Allocation == nil {
		return nil
	}
	return got.Detail.Allocation.Rules
}

// wrongAllocationOrderFeeBeforePenaltyEvaluator is a DELIBERATELY WRONG
// implementation of the payment-allocation ORDER: it decodes the observed rule
// correctly but fills the DUE band fee-first, swapping DUE_FEE ahead of
// DUE_PENALTY. The bucket set is unchanged and the money read-back is untouched;
// WC-07 grades the rule positionally and goes red on rules[0].name and
// rules[1].name. This is the classic "order swapped within DUE" defect.
type wrongAllocationOrderFeeBeforePenaltyEvaluator struct{}

func (wrongAllocationOrderFeeBeforePenaltyEvaluator) Evaluate(req Request) (Expect, error) {
	got, err := goEvaluator{}.Evaluate(req)
	if err != nil {
		return got, err
	}
	if rules := allocationRulesOf(got); len(rules) >= 2 {
		rules[0], rules[1] = rules[1], rules[0] // wrong: DUE_FEE before DUE_PENALTY
	}
	return got, nil
}

// wrongAllocationInAdvanceAsDueEvaluator is a DELIBERATELY WRONG
// implementation of the allocation classification: it decodes the observed
// names but classifies every IN_ADVANCE_* bucket as DUE, collapsing the
// past-due/in-advance distinction. The names and order are untouched; WC-07
// grades each bucket's DueType and goes red on rules[3..5].due_type.
type wrongAllocationInAdvanceAsDueEvaluator struct{}

func (wrongAllocationInAdvanceAsDueEvaluator) Evaluate(req Request) (Expect, error) {
	got, err := goEvaluator{}.Evaluate(req)
	if err != nil {
		return got, err
	}
	for i, r := range allocationRulesOf(got) {
		if strings.HasPrefix(r.Name, "IN_ADVANCE") {
			allocationRulesOf(got)[i].DueType = "DUE" // wrong: in-advance decoded as due
		}
	}
	return got, nil
}

// wrongAllocationRoundTripDropsNameEvaluator is a DELIBERATELY WRONG
// implementation of the list converter: the name -> stored -> name round trip
// loses the last allocation name, so the decoded rule is one bucket short. On
// the graded read-back the converter's output is the decoded list, so the loss
// shows as a short list (five names, not six) and WC-07 grades
// allocation.rules.length and goes red. The de-dup variant is NOT expressed
// here: the observed rule carries six DISTINCT names, so the observation cannot
// discriminate a de-duplicating converter, and a drive that modelled one would
// kill zero.
type wrongAllocationRoundTripDropsNameEvaluator struct{}

func (wrongAllocationRoundTripDropsNameEvaluator) Evaluate(req Request) (Expect, error) {
	got, err := goEvaluator{}.Evaluate(req)
	if err != nil {
		return got, err
	}
	if rules := allocationRulesOf(got); len(rules) > 0 {
		got.Detail.Allocation.Rules = rules[:len(rules)-1] // wrong: the round trip dropped a name
	}
	return got, nil
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
	RegisterWrong("workingcapital-wrong-discount-dropped-from-principal",
		"stores the product discount in totalDiscountFee but sets principal to the disbursed amount alone, dropping the discount "+
			"the oracle adds (principal = disbursed + discount); invisible while every captured discount was 0, red on the "+
			"discount-nonzero facility WC-06, which pins principal 103753",
		wrongDiscountDroppedFromPrincipalEvaluator{})
	RegisterWrong("workingcapital-wrong-allocation-order-fee-before-penalty",
		"decodes the observed payment-allocation rule but fills the DUE band fee-first (DUE_FEE before DUE_PENALTY), swapping "+
			"the first two buckets; WC-07 grades the rule positionally and goes red on rules[0].name and rules[1].name",
		wrongAllocationOrderFeeBeforePenaltyEvaluator{})
	RegisterWrong("workingcapital-wrong-allocation-in-advance-as-due",
		"decodes the observed payment-allocation rule but classifies every IN_ADVANCE_* bucket as DUE, collapsing the "+
			"past-due/in-advance distinction; WC-07 grades each bucket's due_type and goes red on rules[3..5].due_type",
		wrongAllocationInAdvanceAsDueEvaluator{})
	RegisterWrong("workingcapital-wrong-allocation-round-trip-drops-name",
		"loses the last allocation name across the name -> stored -> name conversion, so the decoded rule is one bucket short; "+
			"WC-07 grades allocation.rules.length and goes red on five names instead of six (the de-dup variant is not modelled: "+
			"the observed names are distinct, so the observation cannot discriminate it)",
		wrongAllocationRoundTripDropsNameEvaluator{})
}
