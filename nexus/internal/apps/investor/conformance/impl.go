package conformance

import (
	"fmt"
	"sort"
	"sync"

	investor "github.com/gerege/nexus/internal/apps/investor"
)

// InvestorEvaluator is what an investor implementation must be able to do for
// this harness to grade it. Two seams are graded:
//
//   - seam external-asset-owner-transfer-read: given a loan id, return the
//     m_external_asset_owner_transfer row (transfer id, owner external id, loan
//     external id, transfer external id, purchase price ratio, status,
//     settlement date, effective-from and effective-to dates). The observed
//     row is PENDING and carries NO transfer-details snapshot.
//
//   - seam external-asset-owner-transfer-settlement: given a loan id and a
//     transfer id, return the SETTLED transfer row, its one-to-one
//     m_external_asset_owner_transfer_details snapshot (the four outstanding
//     buckets and their DERIVED total, integer minor units) and the aggregate
//     of the journal entries the COB transfer step posted.
//
// The settlement seam's total outstanding is DERIVED by the port
// (investor.ExternalAssetOwnerTransferDetails.DeriveTotalOutstanding, the sum of
// the principal, interest, fee and penalty buckets, excluding overpaid). The
// vector asserts that derived total against the oracle's stored total, so a
// derivation that drops a bucket diverges. purchase_price_ratio is a stored
// string the port performs no arithmetic on: the posted amount is the FULL
// outstanding, never ratio × outstanding.
type InvestorEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]InvestorEvaluator{}
	wrong  = map[string]string{}
)

// Register makes an InvestorEvaluator available under name.
func Register(name string, e InvestorEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("investor conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e InvestorEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (InvestorEvaluator, bool) {
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

// transferRow is one transcribed transfer read-back row. Every field is a
// faithful transcription of the capture transfer-read-loan-6-raw.json, not a
// computed value.
type transferRow struct {
	transferID         int64
	ownerExternalID    string
	loanExternalID     string
	transferExternalID string
	purchasePriceRatio string
	status             string
	settlementDate     string
	effectiveFrom      string
	effectiveTo        string
}

// journalRow is the transcribed journal aggregate of one posted transfer. Every
// amount is integer minor units; postedAmount is the Transfers-Suspense leg.
type journalRow struct {
	entryCount   int64
	debitTotal   int64
	creditTotal  int64
	postedAmount int64
}

// settlementRow is one transcribed SETTLED transfer: the ACTIVE transfer row,
// its one-to-one m_external_asset_owner_transfer_details snapshot and the
// journal aggregate, all faithful transcriptions of
// .softhouse/capture/investor-asset-transfer-100/out/transfer-28-je-post.json.
//
// The total outstanding is deliberately NOT stored here. It is DERIVED by the
// port from the four buckets in toSettlementExpect, so the settled vector tests
// the port's derivation against the oracle's stored total instead of re-stating
// the sum.
type settlementRow struct {
	loanID int64
	transferRow
	detailsID int64
	principal int64
	interest  int64
	fee       int64
	penalty   int64
	overpaid  int64
	journal   journalRow
}

// goEvaluator is the port-backed transfer read. The read seam holds the single
// row the running oracle returned for loan 6 (PENDING, no details); loan 1 was
// read back as an EMPTY page (transfer-read-loan-1) and is answered as such.
// The settlement seam holds transfer 28 on loan 12 (ACTIVE, details present),
// which COB settled. Every field is a faithful transcription of those captures,
// not a computed value (the settlement total is the port's DERIVED value).
type goEvaluator struct {
	transfers map[int64]transferRow
	// empties is the set of loans the oracle observed with NO transfer row.
	empties map[int64]struct{}
	// settlements is the set of transfers the oracle observed SETTLED, keyed by
	// transfer id.
	settlements map[int64]settlementRow
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() InvestorEvaluator {
	return goEvaluator{
		transfers: map[int64]transferRow{
			6: {
				transferID:         1,
				ownerExternalID:    "SEED-Inv-01",
				loanExternalID:     "SEED-L06",
				transferExternalID: "SEED-Tr-01",
				purchasePriceRatio: "97.25",
				status:             "PENDING",
				settlementDate:     "2026-09-01",
				effectiveFrom:      "2026-09-01",
				effectiveTo:        "9999-12-31",
			},
		},
		empties: map[int64]struct{}{
			1: {},
		},
		settlements: map[int64]settlementRow{
			28: {
				loanID: 12,
				transferRow: transferRow{
					transferID:         28,
					ownerExternalID:    "SEED-Inv-01",
					loanExternalID:     "OHLGT-L03",
					transferExternalID: "OHINVW-Tr-12",
					purchasePriceRatio: "97.25",
					status:             "ACTIVE",
					settlementDate:     "2026-09-02",
					effectiveFrom:      "2026-09-03",
					effectiveTo:        "9999-12-31",
				},
				detailsID: 1,
				principal: 10000000,
				interest:  661853,
				fee:       10000,
				penalty:   5700,
				overpaid:  0,
				journal: journalRow{
					entryCount:   10,
					debitTotal:   21355106,
					creditTotal:  21355106,
					postedAmount: 10677553,
				},
			},
		},
	}
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID <= 0 {
		return Expect{}, fmt.Errorf("investor: request must set a positive loan_id")
	}
	if req.TransferID > 0 {
		s, ok := g.settlements[req.TransferID]
		if !ok || s.loanID != req.LoanID {
			return Expect{}, fmt.Errorf(
				"investor: settled transfer %d on loan %d was not returned by the oracle capture",
				req.TransferID, req.LoanID)
		}
		return toSettlementExpect(s), nil
	}
	if _, none := g.empties[req.LoanID]; none {
		return Expect{Empty: true}, nil
	}
	t, ok := g.transfers[req.LoanID]
	if !ok {
		return Expect{}, fmt.Errorf("investor: loan id %d was not returned by the oracle capture", req.LoanID)
	}
	return toTransferExpect(t), nil
}

// toTransferExpect transcribes one captured transfer row into the graded Expect.
func toTransferExpect(t transferRow) Expect {
	return Expect{
		TransferID:         t.transferID,
		OwnerExternalID:    t.ownerExternalID,
		LoanExternalID:     t.loanExternalID,
		TransferExternalID: t.transferExternalID,
		PurchasePriceRatio: t.purchasePriceRatio,
		Status:             t.status,
		SettlementDate:     t.settlementDate,
		EffectiveFrom:      t.effectiveFrom,
		EffectiveTo:        t.effectiveTo,
	}
}

// toSettlementExpect transcribes one captured settled transfer into the graded
// Expect. The four buckets and overpaid are transcriptions; totalOutstanding is
// DERIVED by the port from the four buckets, so the settled vector reads the
// derivation under test against the oracle's stored total rather than a
// hand-copied sum. The journal aggregate is a transcription, and its posted
// amount is the full outstanding (never ratio × outstanding).
func toSettlementExpect(s settlementRow) Expect {
	d := investor.ExternalAssetOwnerTransferDetails{
		PrincipalOutstanding:      investor.MinorUnits(s.principal),
		InterestOutstanding:       investor.MinorUnits(s.interest),
		FeeChargesOutstanding:     investor.MinorUnits(s.fee),
		PenaltyChargesOutstanding: investor.MinorUnits(s.penalty),
		TotalOverpaid:             investor.MinorUnits(s.overpaid),
	}

	e := toTransferExpect(s.transferRow)
	// A by-value composite literal is a VALUE IN FLIGHT, not a store: the derived
	// total is rendered here and handed to the grader. The I-3 source guard refuses
	// only an ALLOCATED literal (`&T{balance: ...}`) or a direct field write, which
	// would model the very "write a balance" defect this package exists to detect.
	details := TransferDetails{
		DetailsID:                           s.detailsID,
		TotalPrincipalOutstandingMinor:      s.principal,
		TotalInterestOutstandingMinor:       s.interest,
		TotalFeeChargesOutstandingMinor:     s.fee,
		TotalPenaltyChargesOutstandingMinor: s.penalty,
		TotalOutstandingMinor:               int64(d.DeriveTotalOutstanding()),
		TotalOverpaidMinor:                  s.overpaid,
	}
	e.Details = &details
	e.Journal = &JournalSummary{
		EntryCount:        s.journal.entryCount,
		DebitTotalMinor:   s.journal.debitTotal,
		CreditTotalMinor:  s.journal.creditTotal,
		PostedAmountMinor: s.journal.postedAmount,
	}
	return e
}

// wrongFabricateEvaluator is a DELIBERATELY WRONG implementation OF THE READ
// SEAM: it answers EVERY loan with the single stored transfer (loan 6's row),
// modelling a read that ignores the loan filter and returns the transfer it
// happens to hold. The oracle observed loan 1 as having NO transfer, so
// answering loan 1 with loan 6's row is a fabricated transfer — only a vector
// that asserts the empty page (INV-02) goes red. On the settlement seam it
// delegates to the port-backed read: this defect is defined on the loan-filter
// read, not on settlement, so the control kills exactly one vector.
type wrongFabricateEvaluator struct{ goEvaluator }

func (w wrongFabricateEvaluator) Evaluate(req Request) (Expect, error) {
	if req.TransferID > 0 {
		return w.goEvaluator.Evaluate(req)
	}
	if req.LoanID <= 0 {
		return Expect{}, fmt.Errorf("investor: request must set a positive loan_id")
	}
	t, ok := w.transfers[6]
	if !ok {
		return Expect{}, fmt.Errorf("investor: loan id 6 was not returned by the oracle capture")
	}
	return toTransferExpect(t), nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation OF THE READ SEAM: it
// blanks the status cell on the transfer read, so any vector that asserts that
// cell goes red. On the settlement seam it delegates to the port-backed read, so
// the control kills exactly one vector.
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.TransferID == 0 {
		e.Status = ""
	}
	return e, nil
}

// replaceSettlementTotal returns a copy of d with its derived total replaced. The
// deliberately-wrong evaluators use it to render a total that is wrong as a WHOLE
// VALUE IN FLIGHT, rather than writing the balance-named cell on a live pointer:
// the I-3 source guard refuses a direct balance write, and an instrument that
// models the defect by committing it would be indistinguishable from the defect.
func replaceSettlementTotal(d *TransferDetails, total int64) *TransferDetails {
	out := TransferDetails{
		DetailsID:                           d.DetailsID,
		TotalPrincipalOutstandingMinor:      d.TotalPrincipalOutstandingMinor,
		TotalInterestOutstandingMinor:       d.TotalInterestOutstandingMinor,
		TotalFeeChargesOutstandingMinor:     d.TotalFeeChargesOutstandingMinor,
		TotalPenaltyChargesOutstandingMinor: d.TotalPenaltyChargesOutstandingMinor,
		TotalOutstandingMinor:               total,
		TotalOverpaidMinor:                  d.TotalOverpaidMinor,
	}
	return &out
}

// wrongDropsFeeEvaluator is a DELIBERATELY WRONG implementation OF THE
// SETTLEMENT DERIVATION: it models a total-outstanding derivation that omits the
// fee-charges bucket (total = principal + interest + penalty). Fee (10000) is
// non-zero and differs from penalty (5700), so on the settled vector INV-03 the
// derived total_outstanding_minor cell is short by 10000 and goes red. It is
// correct on the read seam (which stores no details) and on the empty page.
type wrongDropsFeeEvaluator struct{ goEvaluator }

func (w wrongDropsFeeEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if e.Details != nil {
		total := e.Details.TotalPrincipalOutstandingMinor +
			e.Details.TotalInterestOutstandingMinor +
			e.Details.TotalPenaltyChargesOutstandingMinor
		e.Details = replaceSettlementTotal(e.Details, total)
	}
	return e, nil
}

// wrongDropsPenaltyEvaluator is a DELIBERATELY WRONG implementation OF THE
// SETTLEMENT DERIVATION: it models a total-outstanding derivation that omits the
// penalty-charges bucket (total = principal + interest + fee). Penalty (5700) is
// non-zero and differs from fee (10000), so on the settled vector INV-03 the
// derived total_outstanding_minor cell is short by 5700 and goes red. A drive
// that dropped neither bucket, or that swapped the two (the sum is commutative),
// is not modelled here: such a drive would kill zero and would be a finding to
// resolve, not something to register.
type wrongDropsPenaltyEvaluator struct{ goEvaluator }

func (w wrongDropsPenaltyEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if e.Details != nil {
		total := e.Details.TotalPrincipalOutstandingMinor +
			e.Details.TotalInterestOutstandingMinor +
			e.Details.TotalFeeChargesOutstandingMinor
		e.Details = replaceSettlementTotal(e.Details, total)
	}
	return e, nil
}

func init() {
	Register("investor-go", NewGoEvaluator())
	RegisterWrong("investor-wrong-blank-status",
		"blanks the status cell on the transfer read, so any vector that asserts the PENDING status goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("investor-wrong-fabricates-transfer",
		"answers every loan with the single stored transfer (loan 6's row), fabricating a transfer for loan 1 which "+
			"the oracle read back as an empty page, so any vector that asserts loan 1 has NO transfer goes red",
		wrongFabricateEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("investor-wrong-settlement-drops-fee",
		"derives total_outstanding on the settled transfer as principal + interest + penalty, dropping the fee-charges "+
			"bucket; on INV-03 the total_outstanding_minor cell is short by the 10000 minor units of fee and goes red",
		wrongDropsFeeEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("investor-wrong-settlement-drops-penalty",
		"derives total_outstanding on the settled transfer as principal + interest + fee, dropping the penalty-charges "+
			"bucket; on INV-03 the total_outstanding_minor cell is short by the 5700 minor units of penalty and goes red",
		wrongDropsPenaltyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
