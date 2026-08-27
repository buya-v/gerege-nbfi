package conformance

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// The implementation registry.
//
// The harness must be able to grade an implementation it does not import, because
// the port does not exist yet (task T10) and because the harness's independence
// from the port is the whole reason the pipeline has both. So the port registers
// itself and the harness looks it up by name; the harness never names a package
// that computes a schedule.
//
// When the Go port lands, exactly one line changes: a blank import in
// cmd/conformance/impl_hook.go, whose init() calls Register. Nothing in this
// package moves.

var (
	implMu sync.RWMutex
	impls  = map[string]contract.ScheduleGenerator{}
)

// Register makes a ScheduleGenerator available to the harness under name.
// Registering the same name twice panics: two implementations claiming one name
// would make the report's "implementation" line a lie.
func Register(name string, g contract.ScheduleGenerator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("conformance: implementation %q registered twice", name))
	}
	impls[name] = g
}

// Lookup returns the named implementation.
func Lookup(name string) (contract.ScheduleGenerator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	g, ok := impls[name]
	return g, ok
}

// RegisteredNames lists what is available to grade, for the report and for a
// legible error when nothing is.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for name := range impls {
		out = append(out, name)
	}
	sort.Strings(out)
	return out
}

// replayGenerator answers from a vector store: for each request it returns the
// expected schedule of the vector carrying that request.
//
// IT IS NOT A PORT AND IT MUST NEVER BE MISTAKEN FOR ONE. It computes nothing: no
// interest, no rate factor, no due date. It exists so the harness can be proven to
// go green and red BEFORE any implementation exists, by grading a pristine store
// against a perturbed copy of itself — which is the only honest way to demonstrate
// that a conformance harness can actually fail.
//
// It is available only under -self-test, and every line of the report in that mode
// says SELF-TEST.
type replayGenerator struct {
	byRequestKey map[string]replayAnswer
}

type replayAnswer struct {
	schedule contract.Schedule
	refusal  error

	// placeholders names the cells of schedule that came from nowhere: the
	// capture never recorded them, so the replay filled a stand-in. See
	// PlaceholderCells and contractFixesCellAtZero.
	placeholders PlaceholderCells
}

// PlaceholderCells reports which cells of the replay's answer are stand-ins
// rather than transcribed observations, so that the property invariants can
// decline to assert anything that reads one (finding T58-N2).
//
// This is the ONLY implementation of PlaceholderReporter and it must stay that
// way: a real port computes every cell, so it reports none and every invariant
// runs in full against it.
func (g *replayGenerator) PlaceholderCells(req contract.GenerateRequest) PlaceholderCells {
	return g.byRequestKey[requestKey(req)].placeholders
}

// contractFixesCellAtZero reports whether the FROZEN CONTRACT itself fixes this
// cell at 0 for this row kind, independently of every other cell in the schedule.
//
// This is the line between an answer and a placeholder, and it is the reason
// closing T58-N2 cost no check that currently passes. All 29 promoted parity
// vectors withdraw installment_number and interest_minor on their DISBURSEMENT
// row, because Path A's capture harness does not print either. For a DISBURSEMENT
// row the contract says, normatively:
//
//	"its InterestMinor is 0, and its InstallmentNumber is 0 because it is not
//	 payable" — contract.go:1509-1510 (and :1532 for DOWN_PAYMENT)
//
// So the replay's 0 there is not invented: it is the contract's own value, a
// CONSTANT, and grading it grades something real. admit.go already ratified
// exactly this argument for installment_number (finding T9-F1c, admit.go:772-778,
// "0 is the frozen contract's own value for a row that is not payable"); this
// function only states it once and applies it to interest as well.
//
// outstanding_principal_minor on a DISBURSEMENT row is DELIBERATELY NOT on this
// list, even though contract.go:1512-1513 fixes it too. It is fixed as a FUNCTION
// OF ANOTHER CELL OF THE SAME SCHEDULE — "IS THE AMOUNT ADVANCED, equal to this
// row's PrincipalMinor" — which is verbatim the thing balance_roll_forward
// asserts. Supplying it would make the invariant check the rig's own derivation
// and report HOLD every time, which is the circularity vector.go:329-336 already
// forbids a promotion task from committing in the store. A rule the harness
// derives is not an observation the harness may grade.
func contractFixesCellAtZero(kind contract.PeriodKind, field string) bool {
	switch kind {
	case contract.PeriodKindDisbursement, contract.PeriodKindDownPayment:
	default:
		return false
	}
	return field == FieldInstallmentNumber || field == FieldInterestMinor
}

func (g *replayGenerator) Generate(_ context.Context, req contract.GenerateRequest) (contract.Schedule, error) {
	a, ok := g.byRequestKey[requestKey(req)]
	if !ok {
		return contract.Schedule{}, fmt.Errorf(
			"replay self-test implementation: no vector in the replay store carries this request")
	}
	if a.refusal != nil {
		return contract.Schedule{}, a.refusal
	}
	return a.schedule, nil
}

// NewReplayImplementation builds the self-test implementation from a store.
func NewReplayImplementation(storeRoot, contextFilter string) (contract.ScheduleGenerator, int, error) {
	vectors, loadErrs, err := LoadStore(storeRoot, contextFilter)
	if err != nil {
		return nil, 0, err
	}
	if len(loadErrs) > 0 {
		return nil, 0, fmt.Errorf("replay store %s: %s could not be decoded: %w",
			storeRoot, loadErrs[0].Path, loadErrs[0].Err)
	}
	g := &replayGenerator{byRequestKey: map[string]replayAnswer{}}
	for _, v := range vectors {
		// NOTHING HERE MAY DROP A VECTOR SILENTLY (driver finding D-5).
		//
		// This loop used to `continue` on any parse failure. The consequence was
		// the harness's own cardinal sin: a vector that could not be loaded
		// vanished, and the run then reported "no vector in the replay store
		// carries this request" — absence of evidence dressed as evidence of
		// absence. The first vectors to hit it were the promoted captures with
		// unrecorded_fields on a DISBURSEMENT row, where MinorText("").Int64()
		// errors by design.
		//
		// So an UNRECORDED money cell is skipped AS A CELL — that is what
		// unrecorded_fields means, and diffSchedule never compares those cells —
		// and anything genuinely unparseable is a hard error naming the vector,
		// the period and the field.
		req, cerr := v.Request.ContractRequest()
		if cerr != nil {
			return nil, 0, fmt.Errorf(
				"replay store: vector %s (%s) request does not map onto the frozen contract: %w",
				v.CaseID, v.Path, cerr)
		}
		key := requestKey(req)
		if v.Expect.Kind == "refusal" {
			sent, serr := sentinelByName(v.Expect.Sentinel)
			if serr != nil {
				return nil, 0, fmt.Errorf("replay store: vector %s (%s) expect.sentinel: %w",
					v.CaseID, v.Path, serr)
			}
			g.byRequestKey[key] = replayAnswer{refusal: sent}
			continue
		}
		sched, placeholders, rerr := RecordedSchedule(v)
		if rerr != nil {
			return nil, 0, rerr
		}
		g.byRequestKey[key] = replayAnswer{schedule: sched, placeholders: placeholders}
	}
	return g, len(g.byRequestKey), nil
}

// RecordedSchedule rebuilds the schedule THE CAPTURE ITSELF RECORDED for one
// vector, together with the PlaceholderCells its own unrecorded_fields imply.
//
// It is the one place in the harness that turns `expect.periods` into a
// contract.Schedule, and it has two callers on purpose:
//
//   - NewReplayImplementation, which answers requests with it in self-test mode;
//   - CheckExemptionGrounding (exemption.go), which re-runs an exempted invariant
//     against it to ask whether the exemption is grounded in anything.
//
// ONE BUILDER, DELIBERATELY. If the exemption check built its own schedule it
// could disagree with the replay's about which cells are placeholders — and a
// disagreement about that is precisely the T9-F1b shape, one half of the harness
// policing a cell the other half resolves differently. The two now cannot drift.
//
// The returned schedule is the ORACLE'S OWN OUTPUT as transcribed, never a
// derivation: every cell comes from the file, and a cell the file withdrew is a
// declared placeholder rather than an invented number.
func RecordedSchedule(v *Vector) (contract.Schedule, PlaceholderCells, error) {
	var sched contract.Schedule
	placeholders := PlaceholderCells{}
	for i, ep := range v.Expect.Periods {
		kind, kerr := periodKindByName(ep.Kind)
		if kerr != nil {
			return contract.Schedule{}, nil, fmt.Errorf(
				"replay store: vector %s (%s) period %d kind: %w", v.CaseID, v.Path, i, kerr)
		}
		unrecorded := map[string]bool{}
		for _, f := range ep.UnrecordedFields {
			unrecorded[f] = true
			// FINDING T58-N2. diffSchedule always honoured unrecorded_fields.
			// The property invariants did not, and they read this same
			// schedule — so a cell the replay stands in for has to be
			// DECLARED, not merely skipped by the cell diff. Every withdrawn
			// cell is a placeholder except the ones the frozen contract fixes
			// at 0 for this row kind, where 0 is the contract's own value and
			// therefore a real answer.
			if !contractFixesCellAtZero(kind, f) {
				placeholders.Add(i, f)
			}
		}
		// The replay answers 0 (or the zero date) for a cell the capture never
		// recorded. The value is never compared — diffSchedule counts an
		// unrecorded cell as UNGRADED and skips it, and CheckInvariants now
		// declines to assert anything that reads one — so this is a
		// placeholder for a cell nobody observed, not an expectation.
		principal, e1 := replayMinorCell(v, i, "principal_minor", ep.PrincipalMinor, unrecorded)
		interest, e2 := replayMinorCell(v, i, "interest_minor", ep.InterestMinor, unrecorded)
		outstanding, e3 := replayMinorCell(v, i, "outstanding_principal_minor",
			ep.OutstandingPrincipalMinor, unrecorded)
		for _, err := range []error{e1, e2, e3} {
			if err != nil {
				return contract.Schedule{}, nil, err
			}
		}
		sched.Periods = append(sched.Periods, contract.Period{
			Kind:                      kind,
			InstallmentNumber:         ep.InstallmentNumber,
			FromDate:                  ep.FromDate.Contract(),
			DueDate:                   ep.DueDate.Contract(),
			PrincipalMinor:            principal,
			InterestMinor:             interest,
			OutstandingPrincipalMinor: outstanding,
		})
	}
	return sched, placeholders, nil
}

// replayMinorCell reads one money cell for the replay implementation: 0 for a
// cell the capture never recorded, the parsed integer otherwise, and a LOUD error
// naming the vector, the period and the field for anything else.
func replayMinorCell(v *Vector, period int, field string, text MinorText,
	unrecorded map[string]bool) (int64, error) {

	if unrecorded[field] {
		return 0, nil
	}
	val, err := text.Int64()
	if err != nil {
		return 0, fmt.Errorf(
			"replay store: vector %s (%s) period %d %s = %q: %w. If the capture never recorded this cell, "+
				"name it in that period's unrecorded_fields — a cell nobody observed is carried as "+
				"UNGRADED, never dropped and never invented",
			v.CaseID, v.Path, period, field, text, err)
	}
	return val, nil
}

// requestKey is a total, collision-free-enough key for a request. It is used only
// to look a request up in the replay store; nothing money-bearing depends on it.
func requestKey(r contract.GenerateRequest) string {
	key := fmt.Sprintf("%s|%s/%d|%d/%d/%s|%04d-%02d-%02d|%d|%d|%d|%d/%d|%d|%d|%d/%d|%d",
		r.TimeZone, r.Currency.Code, r.Currency.MinorUnitDigits,
		r.Rounding.SignificantDigits, r.Rounding.RateFactorScale, roundingModeText(r.Rounding.Mode),
		r.ScheduleStartDate.Year, r.ScheduleStartDate.Month, r.ScheduleStartDate.Day,
		r.NumberOfRepayments, r.RepaymentEvery, int32(r.RepaymentFrequencyUnit),
		r.AnnualNominalInterestRate.Numerator, r.AnnualNominalInterestRate.Denominator,
		int32(r.InterestMethod), int32(r.DayCount),
		r.DownPaymentPercentage.Numerator, r.DownPaymentPercentage.Denominator,
		r.InstallmentRoundingMultipleMinor)
	for _, d := range r.Disbursements {
		key += fmt.Sprintf("|D%04d-%02d-%02d:%d", d.Date.Year, d.Date.Month, d.Date.Day, d.AmountMinor)
	}
	return key
}

func roundingModeText(m contract.RoundingMode) string {
	switch m {
	case contract.RoundingHalfUp:
		return "HALF_UP"
	case contract.RoundingHalfEven:
		return "HALF_EVEN"
	}
	return fmt.Sprintf("RoundingMode(%d)", int32(m))
}

// FindRepoRoot walks up from start looking for a directory holding
// .softhouse/vectors.
//
// IT IS NOT THE HARNESS'S ROOT-RESOLUTION RULE ANY MORE, and a new caller
// almost certainly wants ResolveRepoRoot instead. `FindRepoRoot(".")` is how
// cmd/conformance used to choose the checkout it graded, which made the corpus,
// the no-float census tree, the contract.go hashed against the store pin and
// every capture_ref depend on WHERE THE CALLER HAPPENED TO BE STANDING. T165
// measured the consequence: one binary, compiled from a tree with an unratified
// edit to the frozen DEC-1 contract, exit 2 from its own tree and VERDICT: PASS
// from a clean sibling checkout.
//
// Two properties make it unsafe as a resolver and are retained because the
// cross-check line in the report needs to reproduce exactly what the old rule
// would have answered. First, the answer is the CWD's, not the binary's.
// Second, the climb is UNBOUNDED: from inside a worktree that has no
// .softhouse/vectors of its own it keeps going and returns the PARENT checkout,
// silently. Its one remaining caller is ResolveRepoRoot, which uses it to print
// "the tree you are standing in is not the tree that was graded".
func FindRepoRoot(start string) (string, error) {
	dir, err := filepath.Abs(start)
	if err != nil {
		return "", err
	}
	for {
		if st, serr := os.Stat(filepath.Join(dir, ".softhouse", "vectors")); serr == nil && st.IsDir() {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("no repository root with .softhouse/vectors found above %s", start)
		}
		dir = parent
	}
}
