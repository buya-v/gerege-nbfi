package conformance

import (
	"fmt"
	"sort"
	"sync"
)

// InvestorEvaluator is what an investor implementation must be able to do for
// this harness to grade it. For this promotion the graded surface is the read
// of the one aggregate the capture recorded:
//
//   - seam external-asset-owner-transfer-read: given a loan id, return the
//     m_external_asset_owner_transfer row (transfer id, owner external id, loan
//     external id, transfer external id, purchase price ratio, status,
//     settlement date, effective-from and effective-to dates).
//
// The transfer-details arithmetic (ExternalAssetOwnerTransferDetails.
// DeriveTotalOutstanding, the sum of the four integer minor-unit buckets) is
// NOT graded here: the running oracle's m_external_asset_owner_transfer_details
// table is empty, so no read-back exposes a total-outstanding cell to
// transcribe, and inventing one would be a fabricated observation.
// purchase_price_ratio is a stored string the port performs no arithmetic on,
// so the transfer-read seam has no rounding surface.
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

// goEvaluator is the port-backed transfer read. The single row is the
// m_external_asset_owner_transfer row the running oracle returned for loan 6;
// loan 1 was read back as an EMPTY page (transfer-read-loan-1) and is answered
// as such. Every field is a faithful transcription of those captures, not a
// computed value.
type goEvaluator struct {
	transfers map[int64]transferRow
	// empties is the set of loans the oracle observed with NO transfer row.
	empties map[int64]struct{}
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
	}
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID <= 0 {
		return Expect{}, fmt.Errorf("investor: request must set a positive loan_id")
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

// wrongFabricateEvaluator is a DELIBERATELY WRONG implementation: it answers
// EVERY loan with the single stored transfer (loan 6's row), modelling a read
// that ignores the loan filter and returns the transfer it happens to hold. The
// oracle observed loan 1 as having NO transfer, so answering loan 1 with loan
// 6's row is a fabricated transfer — only a vector that asserts the empty page
// (INV-02) goes red.
type wrongFabricateEvaluator struct{ goEvaluator }

func (w wrongFabricateEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID <= 0 {
		return Expect{}, fmt.Errorf("investor: request must set a positive loan_id")
	}
	t, ok := w.transfers[6]
	if !ok {
		return Expect{}, fmt.Errorf("investor: loan id 6 was not returned by the oracle capture")
	}
	return toTransferExpect(t), nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it blanks the status
// cell on the transfer read, so any vector that asserts that cell goes red.
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	e.Status = ""
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
}
