package conformance

import (
	"context"
	"fmt"
	"path/filepath"

	shared "github.com/gerege/nexus/internal/conformance"
)

// Outcome is the verdict of grading one vector.
type Outcome string

const (
	OutcomePass         Outcome = "PASS"
	OutcomeFail         Outcome = "FAIL"
	OutcomeInadmissible Outcome = "INADMISSIBLE"
	OutcomeRefused      Outcome = "REFUSED"
	OutcomeError        Outcome = "HARNESS-ERROR"
)

// Options configures a conformance run.
type Options struct {
	RepoRoot           string
	StoreRoot          string
	ContextFilter      string
	Implementation     InvestorEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; investor re-uses them unchanged.
type Summary = shared.Summary

// vectorResult is one vector's grading outcome.
type vectorResult struct {
	CaseID              string
	Outcome             Outcome
	Problems            []string
	Reasons             []string
	GradedCells         int
	InvariantViolations int
	Diffs               []string
}

// gradeOne admits, checks capabilities, evaluates and compares one vector.
func gradeOne(v *Vector, opts Options) vectorResult {
	r := vectorResult{CaseID: v.CaseID}

	if problems := Admit(v, opts); len(problems) > 0 {
		r.Outcome = OutcomeInadmissible
		r.Problems = problems
		return r
	}

	if opts.Registry != nil {
		if verdict := opts.Registry.Assess(v.Oracle.Seam, v.CapabilitiesRequired); !verdict.Gradeable {
			r.Outcome = OutcomeRefused
			r.Reasons = verdict.Detail
			return r
		}
	}

	got, err := opts.Implementation.Evaluate(v.Request)
	if err != nil {
		r.Outcome = OutcomeError
		r.Reasons = []string{err.Error()}
		return r
	}

	diffs := compareTransferExpect(v.Expect, got)
	// A read-seam row vector grades the nine transcribed row cells; an empty-page
	// vector grades the one presence cell (loan has no transfer). A settlement
	// vector additionally grades details presence, the seven details cells,
	// journal presence and the four journal cells.
	switch {
	case v.Oracle.Seam == SeamExternalAssetOwnerTransferSettlement:
		r.GradedCells = 22 // 9 row + details_presence + details_id + 5 details money cells (incl. overpaid) + journal_presence + entry_count + debit_total + credit_total + posted_amount
	case v.Expect.Empty:
		r.GradedCells = 1 // page_presence (empty page)
	default:
		r.GradedCells = 9 // transfer_id, owner_external_id, loan_external_id, transfer_external_id, purchase_price_ratio, status, settlement_date, effective_from, effective_to
	}
	r.Diffs = diffs

	invs := AssertInvariants(v, got)
	for _, iv := range invs {
		if iv.Status == InvariantViolated {
			r.InvariantViolations++
			r.Diffs = append(r.Diffs, fmt.Sprintf("invariant %s: %s", iv.Name, iv.Detail))
		}
	}

	if len(r.Diffs) > 0 || r.InvariantViolations > 0 {
		r.Outcome = OutcomeFail
	} else {
		r.Outcome = OutcomePass
	}
	return r
}

// compareTransferExpect compares an expected transfer read-back against the
// evaluated one. Every field is a verbatim transcription; none is money in
// integer minor units, so the cells are plain string/integer comparisons.
//
// The page's content presence is compared FIRST: the oracle returned one row
// for loan 6 and an empty page for loan 1, and those are different facts. When
// the expected and evaluated presence disagree no row cells are compared — the
// page cardinality is the discriminating cell and a row-cell listing across a
// presence mismatch would be noise, not information.
func compareTransferExpect(want Expect, got Expect) []string {
	if want.Empty != got.Empty {
		if want.Empty {
			return []string{fmt.Sprintf(
				"page: expected an EMPTY page (loan has no transfer); implementation returned a transfer row (transfer_id %d)", got.TransferID)}
		}
		return []string{"page: expected a transfer row; implementation returned an EMPTY page"}
	}
	if want.Empty {
		return nil
	}

	var diffs []string
	if want.TransferID != got.TransferID {
		diffs = append(diffs, fmt.Sprintf("transfer_id: want %d, got %d", want.TransferID, got.TransferID))
	}
	if want.OwnerExternalID != got.OwnerExternalID {
		diffs = append(diffs, fmt.Sprintf("owner_external_id: want %q, got %q", want.OwnerExternalID, got.OwnerExternalID))
	}
	if want.LoanExternalID != got.LoanExternalID {
		diffs = append(diffs, fmt.Sprintf("loan_external_id: want %q, got %q", want.LoanExternalID, got.LoanExternalID))
	}
	if want.TransferExternalID != got.TransferExternalID {
		diffs = append(diffs, fmt.Sprintf("transfer_external_id: want %q, got %q", want.TransferExternalID, got.TransferExternalID))
	}
	if want.PurchasePriceRatio != got.PurchasePriceRatio {
		diffs = append(diffs, fmt.Sprintf("purchase_price_ratio: want %q, got %q", want.PurchasePriceRatio, got.PurchasePriceRatio))
	}
	if want.Status != got.Status {
		diffs = append(diffs, fmt.Sprintf("status: want %q, got %q", want.Status, got.Status))
	}
	if want.SettlementDate != got.SettlementDate {
		diffs = append(diffs, fmt.Sprintf("settlement_date: want %q, got %q", want.SettlementDate, got.SettlementDate))
	}
	if want.EffectiveFrom != got.EffectiveFrom {
		diffs = append(diffs, fmt.Sprintf("effective_from: want %q, got %q", want.EffectiveFrom, got.EffectiveFrom))
	}
	if want.EffectiveTo != got.EffectiveTo {
		diffs = append(diffs, fmt.Sprintf("effective_to: want %q, got %q", want.EffectiveTo, got.EffectiveTo))
	}
	diffs = append(diffs, compareDetails(want.Details, got.Details)...)
	diffs = append(diffs, compareJournal(want.Journal, got.Journal)...)
	return diffs
}

// compareDetails compares a settlement seam's details snapshot. Presence is the
// first graded fact: the read seam observed no details row, so an implementation
// that invents one (or that drops a row the oracle observed) diverges before any
// cell is compared. All six amounts are integer minor units.
func compareDetails(want, got *TransferDetails) []string {
	switch {
	case want == nil && got == nil:
		return nil
	case want == nil:
		return []string{"details: expected ABSENT (a PENDING transfer has no details row); implementation returned a details snapshot"}
	case got == nil:
		return []string{"details: expected a details snapshot; implementation returned none"}
	}
	var diffs []string
	if want.DetailsID != got.DetailsID {
		diffs = append(diffs, fmt.Sprintf("details.details_id: want %d, got %d", want.DetailsID, got.DetailsID))
	}
	for _, c := range []struct {
		name      string
		want, got int64
	}{
		{"total_principal_outstanding_minor", want.TotalPrincipalOutstandingMinor, got.TotalPrincipalOutstandingMinor},
		{"total_interest_outstanding_minor", want.TotalInterestOutstandingMinor, got.TotalInterestOutstandingMinor},
		{"total_fee_charges_outstanding_minor", want.TotalFeeChargesOutstandingMinor, got.TotalFeeChargesOutstandingMinor},
		{"total_penalty_charges_outstanding_minor", want.TotalPenaltyChargesOutstandingMinor, got.TotalPenaltyChargesOutstandingMinor},
		{"total_outstanding_minor", want.TotalOutstandingMinor, got.TotalOutstandingMinor},
		{"total_overpaid_minor", want.TotalOverpaidMinor, got.TotalOverpaidMinor},
	} {
		if c.want != c.got {
			diffs = append(diffs, fmt.Sprintf("details.%s: want %d, got %d", c.name, c.want, c.got))
		}
	}
	return diffs
}

// compareJournal compares a settlement seam's journal aggregate. Presence is
// graded first, then the entry count and the three money cells. All amounts are
// integer minor units.
func compareJournal(want, got *JournalSummary) []string {
	switch {
	case want == nil && got == nil:
		return nil
	case want == nil:
		return []string{"journal: expected ABSENT; implementation returned posted journal entries"}
	case got == nil:
		return []string{"journal: expected posted journal entries; implementation returned none"}
	}
	var diffs []string
	for _, c := range []struct {
		name      string
		want, got int64
	}{
		{"entry_count", want.EntryCount, got.EntryCount},
		{"debit_total_minor", want.DebitTotalMinor, got.DebitTotalMinor},
		{"credit_total_minor", want.CreditTotalMinor, got.CreditTotalMinor},
		{"posted_amount_minor", want.PostedAmountMinor, got.PostedAmountMinor},
	} {
		if c.want != c.got {
			diffs = append(diffs, fmt.Sprintf("journal.%s: want %d, got %d", c.name, c.want, c.got))
		}
	}
	return diffs
}

// Run loads the store, runs the no-float census and grades every vector.
//
// IT NEVER RETURNS A PASS OVER ZERO VECTORS AND IT NEVER MAKES ONE UP.
func Run(ctx context.Context, opts Options) (*Summary, error) {
	_ = ctx
	s := &Summary{SelfTestMode: opts.SelfTestMode}

	census, err := ScanGoTreeForFloatingPoint(filepath.Join(opts.RepoRoot, GuardedGoTreeRel))
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf("no-float census: %v", err))
	} else {
		s.NoFloatCensus = census
		for _, viol := range census.Violations() {
			s.FatalReasons = append(s.FatalReasons, viol)
		}
	}

	vectors, loadErrs, err := LoadStore(opts.StoreRoot, opts.ContextFilter)
	s.LoadErrors = loadErrs
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}
	s.VectorsLoaded = len(vectors)

	if len(vectors) == 0 {
		where := opts.StoreRoot
		if opts.ContextFilter != "" {
			where = filepath.Join(opts.StoreRoot, opts.ContextFilter)
		}
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf(
			"ZERO VECTORS FOUND under %s: an empty vector set is exit 2. A harness that reported PASS over "+
				"zero vectors would be the single worst outcome available to it.", where))
		return s, nil
	}

	if opts.Implementation == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO IMPLEMENTATION REGISTERED: there is nothing to grade. This is exit 2, not a pass over zero work.")
		return s, nil
	}
	if opts.Pin == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO STORE PIN: the pin (PIN-investor.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-investor.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}

	for _, v := range vectors {
		r := gradeOne(v, opts)
		s.GradedCells += r.GradedCells
		s.InvariantViolations += r.InvariantViolations
		switch r.Outcome {
		case OutcomePass:
			s.ParityPass++
		case OutcomeFail:
			s.ParityFail++
		case OutcomeRefused:
			s.Refused++
		case OutcomeInadmissible:
			s.Inadmissible++
		case OutcomeError:
			s.Errored++
		}
	}
	return s, nil
}
