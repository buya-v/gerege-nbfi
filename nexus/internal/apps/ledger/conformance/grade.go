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
	// THE PROBE CARRIES BOTH LEG SHAPES — a leg that names its own account and a
	// leg RESOLVED FROM A SLOT — for the reason the refusal and divergence
	// probes below carry their selectors: the vocabulary is "what the comparator
	// CAN emit", and a branch no probe exercises would drop its cells silently.
	// [T391] It is still a probe: the numbers are meaningless, nothing here is
	// an observation and nothing is graded.
	probe := &Vector{
		Class: ClassParity,
		Request: Request{
			ProductID:      1,
			ProductType:    "LOAN",
			AccountingRule: "ACCRUAL_PERIODIC",
			SlotFamily:     "AccrualLoanSlot",
			Currency:       Currency{Code: "MNT", MinorUnitDigits: 2},
			Accounts: []Account{
				{ID: 1, Code: "X", ManualEntriesAllowed: true},
				{ID: 2, Code: "Y", ManualEntriesAllowed: true},
			},
			ProductMappings: []ProductMapping{
				{SlotCode: 7, GLAccountID: 2},
				{SlotCode: 3, GLAccountID: 2},
			},
			Legs: []RequestLeg{
				{AccountID: 1, Side: SideDebit, AmountMajorText: "1.00"},
				{AccountID: 1, Side: SideCredit, AmountMajorText: "1.00"},
				{SlotCode: 7, Side: SideDebit, AmountMajorText: "1.00"},
				{SlotCode: 3, Side: SideCredit, AmountMajorText: "1.00"},
			},
		},
		Expect: Expect{
			Kind:       "journal-entry",
			HTTPStatus: 200,
			Legs: []ExpectLeg{
				{AccountID: 1, Code: "X", Side: SideDebit, AmountMinor: "100", AmountMajorText: "1.00"},
				{AccountID: 1, Code: "X", Side: SideCredit, AmountMinor: "100", AmountMajorText: "1.00"},
				{AccountID: 2, Code: "Y", Side: SideDebit, AmountMinor: "100", AmountMajorText: "1.00",
					SlotName: "INTEREST_RECEIVABLE"},
				{AccountID: 2, Code: "Y", Side: SideCredit, AmountMinor: "100", AmountMajorText: "1.00",
					SlotName: "INTEREST_ON_LOANS"},
			},
			TotalDebitsMinor:  "200",
			TotalCreditsMinor: "200",
		},
	}
	got, _, _ := GoPoster{}.PostEntry(probe.Request)
	var s cellSink
	diffEntry(&s, probe, got)

	// THE REFUSAL PROBE CARRIES AN ARG-ECHO SELECTOR, and it has to: the arg
	// cell is emitted only when a selector is set, so a probe without one would
	// silently drop `refusal.arg0_value` from the vocabulary and every
	// divergent_cells entry naming it would become INADMISSIBLE. The probe's
	// job is to exercise EVERY branch the comparator has [T307].
	refProbe := &Vector{
		Class:   ClassOracleRefusal,
		Request: Request{TransactionDate: "2000-01-01"},
		Expect: Expect{Kind: "refusal", HTTPStatus: 403, Refusal: Refusal{
			HTTPStatus: 403, Code: "c", Message: "m", ArgEcho: ArgEchoTransactionDate}},
	}
	diffRefusal(&s, refProbe, &Refusal{
		HTTPStatus: 403, Code: "c", Message: "m", Arg0Value: "2000-01-01"})

	// THE DIVERGENCE PROBE, for the same reason the refusal probe carries an
	// arg-echo selector: the vocabulary is "what the comparator CAN emit", so a
	// branch that no probe exercises drops its cells silently and every
	// divergent_cells entry naming one becomes INADMISSIBLE. [T360]
	divProbe := &Vector{
		Class:  ClassDivergence,
		Expect: Expect{Kind: "port-refusal", PortRefusal: PortRefusal{Marker: "m"}},
	}
	diffDivergence(&s, divProbe, nil, fmt.Errorf("m"))

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
		// THE SLOT CELL, COMPARED ON EVERY LEG OF EVERY PARITY VECTOR AND NOT
		// ONLY WHERE A SLOT TOOK PART. [T391]
		//
		// A conditional cell would make the cell count a function of the
		// vector's content, and worse, it would make "this leg arrived through
		// no slot" UNGRADED rather than ASSERTED. On a manual entry the
		// expectation is "" and the implementation must produce "": a port that
		// invents a placeholder for a posting nobody routed through one is
		// wrong, and this cell says so. It is the same reasoning the Request
		// doc gives for keeping the product/slot fields on a manual vector —
		// "a schema that omits a field for the case that does not use it cannot
		// express the case that does".
		s.cmpStr(p+"slot_name", want.SlotName, have.SlotName)
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
//
// A FOURTH CELL IS COMPARED, AND ONLY WHEN THE VECTOR ASKS FOR IT  [T307, B-3].
// `refusal.arg0_value` is the oracle's `errors[0].args[0].value`. The vector
// does NOT carry the date: it carries a SELECTOR naming which input it already
// declares the oracle echoed, and the `want` side is RESOLVED from Request here.
// See Refusal.ArgEcho for the whole argument, including the two independent
// grounds on which OB-01's 26-id list stays ungraded.
//
// WHY THE CELL IS CONDITIONAL AND THAT IS NOT A HOLE. An unset selector is not a
// vector's choice: admit.go REQUIRES the selector on exactly the two refusal
// codes whose throw sites pass a LocalDate (:631, :637) and FORBIDS it on every
// other code, so "no selector" is a property of the refusal class, not a cell an
// author may decline. A vector that dropped it would be INADMISSIBLE, not
// quietly less-graded.
//
// IT REMAINS TRUE, AND T297's FINDING IS UNDISTURBED, that cmpMoney is
// unreachable from this function: the cell below goes through cmpStr, so a
// refusal vector still contributes ZERO money cells and
// EXEMPTION_PIN_LEDGER_MONEYCELLS does not move for one.
func diffRefusal(s *cellSink, v *Vector, got *Refusal) {
	wantArg, gradeArg := ResolveArgEcho(v.Expect.Refusal.ArgEcho, v.Request)
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
		if gradeArg {
			s.cmpStr("refusal.arg0_value", wantArg, "")
		}
		return
	}
	s.cmpInt("refusal.http_status", int64(v.Expect.Refusal.HTTPStatus), int64(got.HTTPStatus))
	s.cmpStr("refusal.code", v.Expect.Refusal.Code, got.Code)
	s.cmpStr("refusal.message", v.Expect.Refusal.Message, got.Message)
	if gradeArg {
		s.cmpStr("refusal.arg0_value", wantArg, got.Arg0Value)
	}
}

// diffDivergence grades a DIVERGENCE vector: the reference oracle ACCEPTED and
// this port must REFUSE. [T360, G-19]
//
// TWO CELLS, BOTH STRUCTURAL, AND ZERO MONEY CELLS. That is not a gap, it is the
// class's defining property. There is no port-side amount — the port refused —
// and the oracle-side amount is `100.125000` in a currency whose minor unit is
// 2, which no int64 count of minor units can hold. So this comparator never
// touches cmpMoney, `EXEMPTION_PIN_LEDGER_MONEYCELLS` does not move for a
// divergence vector, and the corpus's money-cell census stays a census of cells
// where a real integer comparison happened.
//
//	divergence.port_outcome         REFUSED / ACCEPTED
//	divergence.port_refusal_marker  the declared stable phrase, present or not
//
// THE FIRST CELL IS THE DIVERGENCE ITSELF and it is what kills a port that
// silently converges by rounding or truncating the residue. The second stops
// that kill being satisfied by ANY refusal: a port that refuses this request for
// an unrelated reason — an unknown account, a bad date — would otherwise be
// counted as agreeing with the recorded divergence when it does not.
//
// WHAT IS DELIBERATELY NOT COMPARED. Nothing on the ORACLE side. `OracleAccepted`
// is an observation, not an expectation of the port, and there is nothing there a
// port could be asked to reproduce. Its bytes are checked by Admit against the
// cited capture and are otherwise only printed.
//
// A GO ERROR FROM PostEntry IS A REFUSAL *ON THIS CLASS ONLY*, and gradeOne
// routes accordingly. That is the second half of T360's finding and it is stated
// here rather than in a handoff: on every OTHER class an error still means
// HARNESS-ERROR, because an implementation that cannot answer a parity vector has
// not refused it — it has failed. The class is what makes the same return value
// mean two different things, and that is exactly right: a divergence vector is
// the only place in this store where "the port would not answer" is the ANSWER.
func diffDivergence(s *cellSink, v *Vector, refusal *Refusal, err error) {
	outcome, text := "ACCEPTED", ""
	switch {
	case err != nil:
		outcome, text = "REFUSED", err.Error()
	case refusal != nil:
		outcome, text = "REFUSED", refusal.Message
	}
	s.cmpStr("divergence.port_outcome", "REFUSED", outcome)

	// THE MARKER CELL IS A CONTAINMENT TEST REPORTED AS AN EQUALITY. `want` is
	// the declared phrase; `got` is that same phrase when the port's refusal
	// carries it and the empty string when it does not. A reader of the diff
	// therefore sees the phrase that was missing, and the reason it was missing
	// is appended below with the port's whole text, so nobody has to re-run the
	// harness to find out what the port actually said.
	want := v.Expect.PortRefusal.Marker
	got := ""
	if want != "" && strings.Contains(text, want) {
		got = want
	}
	s.cmpStr("divergence.port_refusal_marker", want, got)
	if got != want {
		if outcome == "ACCEPTED" {
			s.diffs = append(s.diffs,
				"THE DIVERGENCE HAS MOVED: this port ACCEPTED a request it is recorded as REFUSING. "+
					"That is not automatically a fix -- a port that rounds or truncates a "+
					"sub-minor-unit residue also 'accepts' -- so gate "+v.OracleAccepted.Gate+
					" must be re-derived against the reference oracle before this vector is rewritten")
		} else {
			s.diffs = append(s.diffs,
				"the port refused, but not with the declared marker. Its whole refusal text was: "+text)
		}
	}
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

	ParityPass int

	// ParityFail is every ledger vector whose comparison against OBSERVED oracle
	// output failed, and it INCLUDES DivergenceFail. See the counting rule below.
	ParityFail int

	RefusalPass int
	RefusalFail int

	// DivergencePass and DivergenceFail are the THIRD class's own counters, and
	// they exist so that a divergence cannot be read as a parity result.  [T360]
	//
	// THE COUNTING RULE IS ASYMMETRIC, DELIBERATELY:
	//
	//   A DIVERGENCE PASS IS NOT A PARITY PASS. It is counted HERE and nowhere in
	//   ParityPass. `ledger parity PASS 7` means "seven vectors on which this port
	//   matched the reference oracle". On a divergence vector the port did NOT
	//   match the oracle -- it refused where the oracle accepted -- and folding
	//   that into the parity tally would let an OPEN DIVERGENCE inflate the
	//   number this program quotes as evidence that the port agrees with
	//   Fineract. That is the defect DEC-2 §5.1.1 retracts, one class over.
	//
	//   A DIVERGENCE FAIL *IS* ADDED TO ParityFail. A divergence vector that
	//   fails means the port's behaviour has moved relative to a recorded oracle
	//   observation, and the bar must go red. Two independent reasons, and the
	//   first is a fact about this repository rather than a preference:
	//   loanschedule/conformance/grade.go's ExitCode() computes the run's verdict
	//   from `s.Ledger.ParityFail + s.Ledger.RefusalFail`, and
	//   .softhouse/conformance.sh's wrong-implementation gate reads the same two
	//   printed FAIL figures to decide that a wrong port DIED. Both files are
	//   outside this package. A divergence failure that reached neither would be
	//   a vector that cannot turn anything red -- decoration. And the direction
	//   is the safe one: over-reporting a FAIL raises alarm, it never lowers it.
	//   The un-conflated form is a `.softhouse/conformance.sh` patch this task
	//   requested rather than applied (that file is held by another worker), and
	//   until it lands the divergence census below prints both numbers so the
	//   fold is visible on the same page as the figure it moved.
	DivergencePass int
	DivergenceFail int

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

	// Citations is every capture citation in the loaded corpus with the way its
	// PART TWO resolved on this run, and CitationsNameOnly is the size of its
	// weakest class: the resolutions that read ZERO bytes of the artefact and
	// compare two fields of one vector to each other.
	//
	// IT IS COUNTED AND PRINTED FOR THE SAME REASON DeclaredExemptions IS. A2-34
	// found part two resolving tautologically on three of these citations and
	// nothing in the run said so, because the check reported only pass/fail and
	// a check that cannot fail reports pass. The population is now visible on
	// every run and pinned by IDENTITY in admit.go, in both directions.
	Citations         []CitationResolution
	CitationsByBytes  int
	CitationsBySide   int
	CitationsNameOnly int
	CitationsUnres    int

	// NotGraded is this context's account of its own coverage gaps, DERIVED from
	// the capability registry on every run rather than hand-written beside it.
	//
	// It is a SUMMARY FIELD and not a report-time lookup so that the block is
	// computed by the package that owns the registry, at the moment the store is
	// loaded, with the vectors in hand — the account-activity annotation is
	// measured from those vectors. See notgraded.go.
	NotGraded []NotGradedCapability

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

	// THE NOT-GRADED BLOCK IS BUILT BEFORE ANY EARLY RETURN IN THIS FUNCTION, and
	// deliberately so. The declared gaps are a property of the REGISTRY, not of
	// whether this run managed to grade anything, and the run that most needs
	// its limits printed is the one that went wrong. Building it after the
	// `len(vectors) == 0` return would make the gaps disappear exactly when the
	// corpus did.
	//
	// SCOPE OF THAT CLAIM, STATED RATHER THAN LEFT TO BE ASSUMED — this is the
	// task that exists because a coverage claim was broader than what backed it.
	// It covers the early returns BELOW. It does NOT cover the one a level up:
	// the loanschedule harness returns a nil Summary before ever calling Run
	// when the ledger half of the store holds no file at all, and prints its
	// empty-store banner instead. So on a TOTALLY EMPTY ledger corpus the
	// declared gaps are still not printed. That state is exit 2 on the
	// population pins regardless [MEASURED at T242's own commit: the four LEDGER
	// pins mismatch and the run refuses], so nothing passes silently — but the
	// gaps are a registry property and printing them there would be strictly
	// better. Left alone because that early return is a deliberately distinct
	// report state the exemption-census deflation arm reads, and widening it is
	// a change to the loanschedule reporter rather than to this context.
	s.NotGraded = notGradedRows(opts.Registry, vectors)

	// THE DIVERGENCE POPULATION CENSUS RUNS HERE, ABOVE EVERY EARLY RETURN IN
	// THIS FUNCTION, and for the same reason the not-graded block does. [T360]
	//
	// The pinned population is a property of the CORPUS, not of whether this run
	// managed to grade anything, and the direction that most needs refusing is
	// DEFLATION -- a corpus from which the only record of an open port/oracle
	// disagreement has vanished. Below the `len(vectors) == 0` return, a store
	// that had lost EVERY ledger vector would satisfy the census by having
	// nothing in it, which is precisely the shape T160 and the exemption
	// deflation arm exist to refuse. Measured: with this call below the early
	// return, TestDivergencePopulationIsPinnedInBothDirections' deflation arm
	// reported `Fatal: []` over an empty store.
	s.Fatal = append(s.Fatal, divergenceCensus(vectors)...)

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
			switch v.Class {
			case ClassParity:
				s.ParityPass++
			case ClassDivergence:
				// NOT ParityPass. See DivergencePass.
				s.DivergencePass++
			default:
				s.RefusalPass++
			}
		case OutcomeFail:
			switch v.Class {
			case ClassParity:
				s.ParityFail++
			case ClassDivergence:
				// BOTH counters, deliberately. See DivergenceFail.
				s.DivergenceFail++
				s.ParityFail++
			default:
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

	// --- PART TWO OF THE CITATION: the census and both directions of its pin --
	//
	// Counted over every LOADED vector, not only the graded ones. The question
	// "how much of this corpus's provenance rests on a check that reads no
	// artefact bytes" is a question about the CORPUS, and an inadmissible vector
	// is still in it. (Kills are the opposite case and are credited only from a
	// graded vector, a few lines up -- deliberately, and for the opposite
	// reason: a kill is a claim about grading that happened.)
	loaded := make(map[string]bool, len(vectors))
	for _, v := range vectors {
		loaded[v.CaseID] = true
	}
	for _, v := range vectors {
		for _, cr := range CitationResolutions(v, opts.RepoRoot) {
			s.Citations = append(s.Citations, cr)
			switch cr.Mode {
			case CitationByBytes:
				s.CitationsByBytes++
			case CitationBySidecar:
				s.CitationsBySide++
			case CitationByNameOnly:
				s.CitationsNameOnly++
			default:
				s.CitationsUnres++
			}
		}
	}
	// DEFLATION. Inflation -- a name-only citation that is not pinned -- is
	// refused per vector by Admit and shows up as INADMISSIBLE. This is the
	// other direction, and it has no per-vector home because the thing that is
	// wrong is the PIN.
	s.Fatal = append(s.Fatal, StaleCitationPins(s.Citations, loaded)...)

	// --- THE DIVERGENCE POPULATION, PINNED BY IDENTITY IN BOTH DIRECTIONS -----
	//
	// [T360.] It is pinned HERE, in Go, and not in .softhouse/conformance.sh,
	// for two reasons. The practical one: that file is held by another worker
	// this fire and this task may not write it. The better one: a divergence
	// vector is the only thing in this store that records the port DISAGREEING
	// with the reference oracle, and both directions of drift are bad in a way
	// no other population is.
	//
	//   INFLATION -- a divergence appears that nobody raised a gate for -- means
	//   somebody filed a parity failure they could not make pass under a class
	//   whose PASS state is "the port refuses". That is the single most
	//   attractive way to make this bar green while the port is wrong, and it is
	//   why the class needs a pin at all.
	//
	//   DEFLATION -- a divergence disappears -- means an open, gated
	//   port/oracle disagreement stopped being recorded, with a GREEN run and
	//   nothing said. That is how G-19 would quietly cease to exist.
	//
	// Moving it is a source edit in the same commit as the vector, which a
	// reviewer sees.
	return s
}

// divergenceCensus is that rule. It is a free function so it can be called from
// above every early return in Run.
func divergenceCensus(vectors []*Vector) []string {
	divergences := 0
	for _, v := range vectors {
		if v.Class == ClassDivergence {
			divergences++
		}
	}
	if divergences == DivergencePinCount() {
		return nil
	}
	return []string{fmt.Sprintf(
		"DIVERGENCE POPULATION %d, PINNED %d. A `divergence` vector records the reference oracle "+
			"ACCEPTING a request this port REFUSES -- an OPEN, GATED disagreement, not a parity "+
			"pass. An ADDED one is the cheapest way there is to make this bar green while the port "+
			"is wrong, and a REMOVED one deletes the only record that the disagreement exists. Both "+
			"directions move DivergencePinCount in ledger/conformance/grade.go, in the SAME COMMIT "+
			"as the vector, deliberately. EXIT 2 -- no verdict is available. This is NOT a pass.",
		divergences, DivergencePinCount())}
}

// DivergencePinCount is the number of ClassDivergence vectors the ledger store
// is pinned to hold. See the census in Run for both directions of the argument.
//
// 0 -> 1 at T360: LDG-DIV-01, G-19, the reference oracle accepting a
// sub-minor-unit residue (`100.125000` MNT at declared decimalPlaces 2).
func DivergencePinCount() int { return divergencePinCount }

const divergencePinCount = 1

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

	// THE DIVERGENCE ROUTE IS TAKEN BEFORE THE ERROR ROUTE, AND ONLY ON THIS
	// CLASS. [T360, and it is the half T359's F-T359-1 diagnosed]
	//
	// `EntryPoster` documents `(*Refusal, nil)` as the refusal channel and a
	// returned `error` as "the implementation could not answer at all", which is
	// HARNESS-ERROR. `GoPoster.PostEntry` returns the sub-minor-unit residue
	// refusal down the ERROR leg (impl.go, the `MinorUnitsFromDecimalText` call
	// per leg), so a vector recording the oracle accepting a residue returned
	// HARNESS-ERROR and exit 2 -- a run with no verdict -- rather than a graded
	// outcome. That is what T352 hit and T359 reproduced.
	//
	// THE FIX IS NOT IN impl.go, AND SAYING SO IS THE POINT. T359 measured a
	// one-line change there that re-returns the residue refusal as a
	// `(*Refusal, nil)` with an invented `HTTP 422`. It works, and it is the
	// wrong place, for two reasons. (1) It fabricates a wire status the port
	// never had, in a store whose whole discipline is that it holds only
	// observed bytes. (2) It changes the meaning of that return for EVERY class:
	// a residue reaching a PARITY vector would then be graded as "the port
	// refused" instead of refusing the run, and a parity vector carrying an
	// amount the port cannot convert IS a harness error -- the corpus is broken,
	// not the port. The routing decision belongs to the CLASS, so it is made
	// here, where the class is known, and nothing about any other class moves.
	if v.Class == ClassDivergence {
		var ds cellSink
		diffDivergence(&ds, v, refusal, err)
		r.GradedCells = ds.graded
		r.MoneyCells = ds.money
		r.Detail = ds.diffs
		// NO INVARIANT RUNS HERE. AssertInvariants runs on what the
		// implementation POSTED, and on this class the implementation posted
		// nothing -- the correct outcome is a refusal. Asserting double-entry
		// balance over an empty entry would be a green line over no evidence.
		if len(r.Detail) > 0 {
			r.Outcome = OutcomeFail
		} else {
			r.Outcome = OutcomePass
		}
		return r
	}

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
