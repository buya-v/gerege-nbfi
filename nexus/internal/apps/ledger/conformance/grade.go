package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"github.com/gerege/nexus/internal/apps/ledger"
)

// Outcome is what happened to one ledger vector.
type Outcome string

const (
	OutcomePass         Outcome = "PASS"
	OutcomeFail         Outcome = "FAIL"
	OutcomeInadmissible Outcome = "INADMISSIBLE"
	OutcomeError        Outcome = "HARNESS-ERROR"
)

// ---------------------------------------------------------------------------
// The cell vocabulary, DERIVED from the comparator
// ---------------------------------------------------------------------------
//
// DEC-2 precondition P-4: "a comparator for ledger outputs, and a cell whitelist
// DERIVED FROM IT rather than authored beside it … the whitelist's meaning is
// 'what the comparator compares' (T9-F1b)".
//
// So this file does not carry a hand-written list. `cellSink` is the ONLY route
// by which the comparator can record a compared cell, every comparison below
// goes through it, and CellFields() returns what a comparison run over a probe
// entry actually emitted. A cell the comparator stops comparing disappears from
// the vocabulary automatically; a cell somebody adds to a list without wiring it
// cannot appear at all.

// cellSink collects the names of the cells one comparison compared.
type cellSink struct {
	names  []string
	diffs  []string
	graded int
	money  int
}

// cmpStr compares one non-money cell and records that it was compared.
func (s *cellSink) cmpStr(name, want, got string) {
	s.names = append(s.names, name)
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %q, got %q", name, want, got))
	}
}

// cmpInt compares one non-money integer cell.
func (s *cellSink) cmpInt(name string, want, got int64) {
	s.names = append(s.names, name)
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %d, got %d", name, want, got))
	}
}

// cmpMoney compares one MONEY cell in int64 minor units and returns the signed
// margin in minor units.
//
// IT IS A SEPARATE METHOD FROM cmpInt ON PURPOSE. DEC-2 §5.5 and §5.2
// requirement 7: the transcript must show a money divergence "reported as a
// money kill with a non-zero margin_minor, not as a structural cell difference",
// because "a ledger corpus whose money cells only ever kill structurally has
// graded no amount" (finding D-4). Two methods, two counters, two report lines.
func (s *cellSink) cmpMoney(name string, want, got ledger.MinorUnits) ledger.MinorUnits {
	s.names = append(s.names, name)
	s.graded++
	s.money++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf(
			"%s: MONEY want %d, got %d (margin %d minor units)", name, want, got, got-want))
		return got - want
	}
	return 0
}

// CellFields returns the complete set of cell names this comparator can compare.
//
// It is COMPUTED by running the comparator over a probe pair that exercises
// every branch, not transcribed. The probe is deliberately tiny and its numbers
// are meaningless: nothing here is an observation and nothing is graded — it
// exists only so the vocabulary is a function of the code.
func CellFields() []string {
	probe := &Vector{
		Class: ClassParity,
		Request: Request{
			Currency: Currency{Code: "MNT", MinorUnitDigits: 2},
			Accounts: []Account{{ID: 1, Code: "X", ManualEntriesAllowed: true}},
			Legs: []RequestLeg{
				{AccountID: 1, Side: SideDebit, AmountMajorText: "1.00"},
				{AccountID: 1, Side: SideCredit, AmountMajorText: "1.00"},
			},
		},
		Expect: Expect{
			Kind:       "journal-entry",
			HTTPStatus: 200,
			Legs: []ExpectLeg{
				{AccountID: 1, Code: "X", Side: SideDebit, AmountMinor: "100", AmountMajorText: "1.00"},
				{AccountID: 1, Code: "X", Side: SideCredit, AmountMinor: "100", AmountMajorText: "1.00"},
			},
			TotalDebitsMinor:  "100",
			TotalCreditsMinor: "100",
		},
	}
	got, _, _ := GoPoster{}.PostEntry(probe.Request)
	var s cellSink
	diffEntry(&s, probe, got)

	refProbe := &Vector{
		Class:  ClassOracleRefusal,
		Expect: Expect{Kind: "refusal", HTTPStatus: 403, Refusal: Refusal{HTTPStatus: 403, Code: "c", Message: "m"}},
	}
	diffRefusal(&s, refProbe, &Refusal{HTTPStatus: 403, Code: "c", Message: "m"})

	seen := map[string]bool{}
	var out []string
	for _, n := range s.names {
		// A per-leg cell is emitted once per leg; the VOCABULARY is the cell,
		// not the occurrence, so the index is stripped here and nowhere else.
		n = stripLegIndex(n)
		if !seen[n] {
			seen[n] = true
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// stripLegIndex turns "legs[3].amount_minor" into "legs[].amount_minor".
func stripLegIndex(n string) string {
	i := strings.Index(n, "[")
	j := strings.Index(n, "]")
	if i < 0 || j < i {
		return n
	}
	return n[:i+1] + n[j:]
}

// IsCellField reports whether name is a cell this comparator compares. A
// divergent_cells entry naming anything else is INADMISSIBLE — a store that
// records a kill on a cell nothing compares has recorded a claim that is not
// evidence (T9-F1b).
func IsCellField(name string) bool {
	for _, c := range CellFields() {
		if c == name {
			return true
		}
	}
	return false
}

// ---------------------------------------------------------------------------
// The comparator
// ---------------------------------------------------------------------------

// diffEntry compares an expected journal entry with the one an implementation
// produced. Every comparison goes through the sink.
func diffEntry(s *cellSink, v *Vector, got PostedEntry) ledger.MinorUnits {
	var maxMargin ledger.MinorUnits
	s.cmpInt("leg_count", int64(len(v.Expect.Legs)), int64(len(got.Legs)))
	n := len(v.Expect.Legs)
	if len(got.Legs) < n {
		n = len(got.Legs)
	}
	for i := 0; i < n; i++ {
		want, have := v.Expect.Legs[i], got.Legs[i]
		p := fmt.Sprintf("legs[%d].", i)
		s.cmpInt(p+"gl_account_id", want.AccountID, have.AccountID)
		s.cmpStr(p+"gl_account_code", want.Code, have.AccountCode)
		s.cmpStr(p+"entry_side", string(want.Side), string(have.Side))
		wm, err := parseMinor(want.AmountMinor)
		if err != nil {
			s.diffs = append(s.diffs, fmt.Sprintf("%samount_minor: %v", p, err))
			continue
		}
		if m := s.cmpMoney(p+"amount_minor", wm, have.AmountMinor); absMinor(m) > absMinor(maxMargin) {
			maxMargin = m
		}
	}
	wd, derr := parseMinor(v.Expect.TotalDebitsMinor)
	wc, cerr := parseMinor(v.Expect.TotalCreditsMinor)
	if derr == nil {
		if m := s.cmpMoney("total_debits_minor", wd, got.TotalDebitsMinor); absMinor(m) > absMinor(maxMargin) {
			maxMargin = m
		}
	}
	if cerr == nil {
		if m := s.cmpMoney("total_credits_minor", wc, got.TotalCreditsMinor); absMinor(m) > absMinor(maxMargin) {
			maxMargin = m
		}
	}
	return maxMargin
}

// diffRefusal compares an expected oracle refusal with the one an
// implementation produced. Three cells, deliberately: a port that matches the
// HTTP status while inventing the globalisation code is not matching the oracle.
func diffRefusal(s *cellSink, v *Vector, got *Refusal) {
	if got == nil {
		s.diffs = append(s.diffs,
			"expected an ORACLE REFUSAL and the implementation returned a posted entry instead")
		// The cells are still NAMED so the vocabulary is complete even on this
		// path, and still COUNTED, because "the implementation answered the
		// wrong shape" is a comparison that ran and failed, not one that was
		// skipped.
		s.cmpInt("refusal.http_status", int64(v.Expect.Refusal.HTTPStatus), 0)
		s.cmpStr("refusal.code", v.Expect.Refusal.Code, "")
		s.cmpStr("refusal.message", v.Expect.Refusal.Message, "")
		return
	}
	s.cmpInt("refusal.http_status", int64(v.Expect.Refusal.HTTPStatus), int64(got.HTTPStatus))
	s.cmpStr("refusal.code", v.Expect.Refusal.Code, got.Code)
	s.cmpStr("refusal.message", v.Expect.Refusal.Message, got.Message)
}

func parseMinor(s string) (ledger.MinorUnits, error) {
	if s == "" {
		return 0, fmt.Errorf("empty minor-unit string")
	}
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("%q is not an integer count of minor units: %w", s, err)
	}
	return ledger.MinorUnits(n), nil
}

func absMinor(m ledger.MinorUnits) ledger.MinorUnits {
	if m < 0 {
		return -m
	}
	return m
}

// ---------------------------------------------------------------------------
// Grading one vector
// ---------------------------------------------------------------------------

// Result is one graded ledger vector.
type Result struct {
	CaseID  string
	Context string
	Class   VectorClass
	Path    string
	Seam    string
	Outcome Outcome
	Detail  []string

	GradedCells int
	MoneyCells  int

	// Invariants are the property invariants asserted on THIS vector.
	Invariants []InvariantResult
}

// Options configures a ledger grading run.
type Options struct {
	RepoRoot           string
	StoreRoot          string
	ContextFilter      string
	Implementation     EntryPoster
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
}

// Summary is the ledger half of a conformance run.
//
// ITS COUNTS ARE ITS OWN AND ARE NEVER FOLDED INTO THE LOANSCHEDULE PARITY
// COUNT. DEC-2 §5.2 requirement 6a: "the summary must report the ledger vector
// under its own comparator and its own count — NOT folded into
// `parity vectors PASS <B.parity>` … A submission where B.parity becomes
// B.parity + 1 has reproduced the defect §5.1.1 retracts."
type Summary struct {
	ImplementationName  string
	ImplementationWrong string

	ParityPass   int
	ParityFail   int
	RefusalPass  int
	RefusalFail  int
	Inadmissible int
	Errored      int

	GradedCells int
	MoneyCells  int

	MoneyKills      int
	StructuralKills int

	InvariantViolations int
	InvariantAssertions int

	// IndependentAssertions is the subset of InvariantAssertions that could have
	// gone RED while every other invariant on the same entry stayed GREEN. See
	// InvariantResult.Independent: two green lines are not two checks unless this
	// number says so.
	IndependentAssertions int

	// DeclaredExemptions is the ledger corpus's exemption population.
	//
	// IT IS COUNTED EVEN THOUGH IT MUST BE ZERO, and that is the point. The
	// first store learned (T220-N1, T222, T230, T233) that an exemption
	// population which is not COUNTED can drift in both directions with nothing
	// noticing. This schema refuses exemptions outright — so the honest census
	// is "0, and the harness gates that it is 0", not "the question does not
	// arise". conformance.sh pins this figure for EQUALITY exactly as it pins
	// the loanschedule four.
	DeclaredExemptions int

	Results    []Result
	LoadErrors []LoadError
	Fatal      []string
}

// ExitWorthy reports whether the ledger half of the run should make the whole
// run non-zero.
func (s *Summary) ExitWorthy() bool {
	return s.ParityFail > 0 || s.RefusalFail > 0 || s.Inadmissible > 0 ||
		s.Errored > 0 || s.InvariantViolations > 0 || len(s.LoadErrors) > 0 || len(s.Fatal) > 0
}

// Run loads and grades the ledger half of the store.
//
// IT NEVER RETURNS A "PASS" OVER ZERO VECTORS AND IT NEVER MAKES ONE UP. A store
// with no ledger vector at all yields an empty Summary with zero of everything,
// and the CALLER decides what that means — which is correct, because before this
// task there were no ledger vectors and the run was legitimately green without
// them. What it will not do is report a ledger verdict over an empty population.
func Run(opts Options) *Summary {
	s := &Summary{ImplementationName: opts.ImplementationName}
	if s.ImplementationName == "" {
		s.ImplementationName = "(none)"
	}
	if d, bad := IsRegisteredWrong(opts.ImplementationName); bad {
		s.ImplementationWrong = d
	}

	vectors, loadErrs, err := LoadStore(opts.StoreRoot, opts.ContextFilter)
	s.LoadErrors = loadErrs
	if err != nil {
		s.Fatal = append(s.Fatal, err.Error())
		return s
	}
	if len(vectors) == 0 {
		return s
	}
	if opts.Implementation == nil {
		s.Fatal = append(s.Fatal,
			"LEDGER VECTORS ARE PRESENT AND NO LEDGER IMPLEMENTATION IS REGISTERED: there is nothing to "+
				"grade them against. This is exit 2, not a pass over an ungraded corpus.")
		return s
	}

	for _, v := range vectors {
		r := gradeOne(v, opts)
		s.Results = append(s.Results, r)
		s.GradedCells += r.GradedCells
		s.MoneyCells += r.MoneyCells
		s.DeclaredExemptions += len(v.InvariantExemptions)
		for _, iv := range r.Invariants {
			s.InvariantAssertions += iv.Assertions
			if iv.Independent {
				s.IndependentAssertions += iv.Assertions
			}
			if iv.Status == InvariantViolated {
				s.InvariantViolations++
			}
		}
		switch r.Outcome {
		case OutcomePass:
			if v.Class == ClassParity {
				s.ParityPass++
			} else {
				s.RefusalPass++
			}
		case OutcomeFail:
			if v.Class == ClassParity {
				s.ParityFail++
			} else {
				s.RefusalFail++
			}
		case OutcomeInadmissible:
			s.Inadmissible++
		case OutcomeError:
			s.Errored++
		}
		// KILLS ARE CREDITED ONLY FROM A GRADED VECTOR. Finding A2-19 F3 and
		// A2-22-F3, ported: a vector the harness declined to grade, or could not
		// complete, kills nothing, and crediting its declared kills is how a run
		// that graded nothing reported every capability backed.
		if r.Outcome == OutcomePass || r.Outcome == OutcomeFail {
			for _, cf := range v.GradedAgainst {
				if cf.Kind == "money" {
					s.MoneyKills++
				} else {
					s.StructuralKills++
				}
			}
		}
	}
	return s
}

func gradeOne(v *Vector, opts Options) Result {
	r := Result{
		CaseID:  v.CaseID,
		Context: v.Ctx,
		Class:   v.Class,
		Path:    v.Path,
		Seam:    v.Oracle.Seam,
	}
	if reasons := Admit(v, opts); len(reasons) > 0 {
		r.Outcome = OutcomeInadmissible
		r.Detail = reasons
		return r
	}
	got, refusal, err := opts.Implementation.PostEntry(v.Request)
	if err != nil {
		r.Outcome = OutcomeError
		r.Detail = []string{err.Error()}
		return r
	}

	var s cellSink
	switch v.Expect.Kind {
	case "refusal":
		diffRefusal(&s, v, refusal)
	default:
		if refusal != nil {
			s.diffs = append(s.diffs, fmt.Sprintf(
				"the implementation REFUSED a request the oracle ACCEPTED (HTTP %d %s): %s",
				refusal.HTTPStatus, refusal.Code, refusal.Message))
			s.cmpInt("leg_count", int64(len(v.Expect.Legs)), 0)
		} else {
			diffEntry(&s, v, got)
		}
	}
	r.GradedCells = s.graded
	r.MoneyCells = s.money
	r.Detail = s.diffs

	// THE INVARIANTS RUN ON WHAT THE IMPLEMENTATION RETURNED, never on what the
	// vector recorded. An invariant asserted over the vector's own numbers would
	// be the harness checking its own transcription — the circularity the first
	// store's registry.go refuses.
	if v.Expect.Kind != "refusal" && refusal == nil {
		r.Invariants = AssertInvariants(got)
	}
	for _, iv := range r.Invariants {
		if iv.Status == InvariantViolated {
			r.Detail = append(r.Detail, "INVARIANT "+iv.Name+" VIOLATED: "+iv.Detail)
		}
	}

	if len(r.Detail) > 0 {
		r.Outcome = OutcomeFail
		return r
	}
	r.Outcome = OutcomePass
	return r
}
