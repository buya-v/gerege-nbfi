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
		var sched contract.Schedule
		for i, ep := range v.Expect.Periods {
			kind, kerr := periodKindByName(ep.Kind)
			if kerr != nil {
				return nil, 0, fmt.Errorf("replay store: vector %s (%s) period %d kind: %w",
					v.CaseID, v.Path, i, kerr)
			}
			unrecorded := map[string]bool{}
			for _, f := range ep.UnrecordedFields {
				unrecorded[f] = true
			}
			// The replay answers 0 for a cell the capture never recorded. The
			// value is never compared — diffSchedule counts an unrecorded cell as
			// UNGRADED and skips it — so this is a placeholder for a cell nobody
			// observed, not an expectation.
			principal, e1 := replayMinorCell(v, i, "principal_minor", ep.PrincipalMinor, unrecorded)
			interest, e2 := replayMinorCell(v, i, "interest_minor", ep.InterestMinor, unrecorded)
			outstanding, e3 := replayMinorCell(v, i, "outstanding_principal_minor",
				ep.OutstandingPrincipalMinor, unrecorded)
			for _, err := range []error{e1, e2, e3} {
				if err != nil {
					return nil, 0, err
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
		g.byRequestKey[key] = replayAnswer{schedule: sched}
	}
	return g, len(g.byRequestKey), nil
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

// FindRepoRoot walks up from start looking for the directory that holds both
// .softhouse/vectors and the nexus module, so the harness and its Go test work
// from any working directory.
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
