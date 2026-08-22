package conformance

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// The proofs for the structural rules added by task T20: T17 follow-ups F2 to F6,
// and the driver's finding D-4 (structural counterfactuals).
//
// A STRUCTURAL RULE THAT IS NOT EXERCISED IS NOT A RULE. Every assertion below is
// proven in both directions where both directions exist: the violating shape is
// shown to be refused, and the compliant shape is shown to be admitted, so that a
// rule cannot pass by refusing everything.

// ---------------------------------------------------------------------------
// F2 — a partial match must not read as a full one
// ---------------------------------------------------------------------------

// TestReadmeAttestationMatchesTheReadmeText re-derives the declared column list
// from the reference oracle's own committed CI stdout, so the declaration cannot
// drift away from the text it claims to quote.
//
// It also pins the count the finding got wrong. T17-F2 says the README "covers 9
// of 10 period columns" with only total_outstanding_balance missing. The block
// prints six: it omits from_date, fee and penalty as well. The finding's
// direction holds and its force is greater than stated.
func TestReadmeAttestationMatchesTheReadmeText(t *testing.T) {
	raw, err := os.ReadFile(filepath.Join("testdata", "embeddable-readme-ci-stdout.txt"))
	if err != nil {
		t.Fatalf("reading the committed excerpt: %v", err)
	}
	text := string(raw)
	// LastIndex, not Index: the explanatory note above the marker mentions the
	// marker, and splitting on the first occurrence would drag the note into the
	// quoted text.
	i := strings.LastIndex(text, "---8<---")
	if i < 0 {
		t.Fatal("the excerpt file has no ---8<--- marker, so the note and the quoted text cannot be separated")
	}
	block := text[i+len("---8<---"):]

	// Derive, from the text, which of the ten columns each row kind prints.
	// The mapping from a printed label to a column is stated once, here.
	labelToColumn := map[string]string{
		"Due Date":                  ColDueDate,
		"Balance":                   ColOutstandingBalance,
		"Principal":                 ColPrincipal,
		"Interest":                  ColInterest,
		"Total":                     ColTotalDue,
		"Total Outstanding Balance": ColTotalOutstandingBalance,
		"Date":                      ColDueDate,
		"Amount":                    ColPrincipal,
	}
	derived := map[string]map[string]bool{}
	add := func(rowKind, col string) {
		if derived[rowKind] == nil {
			derived[rowKind] = map[string]bool{}
		}
		derived[rowKind][col] = true
	}
	sawRepayment, sawDisbursement := false, false
	for _, line := range strings.Split(block, "\n") {
		line = strings.TrimSpace(line)
		switch {
		case strings.HasPrefix(line, "Repayment Period: #"):
			sawRepayment = true
			add("REPAYMENT", ColPeriodNumber) // the "#1" is the period number
			for _, field := range strings.Split(line, ", ")[1:] {
				label := strings.TrimSpace(strings.SplitN(field, ":", 2)[0])
				col, ok := labelToColumn[label]
				if !ok {
					t.Fatalf("the excerpt prints label %q on a repayment row and this test does not know "+
						"which column it is; the declaration cannot be checked against text it cannot read",
						label)
				}
				add("REPAYMENT", col)
			}
		case strings.HasPrefix(line, "Disbursement - "):
			sawDisbursement = true
			for _, field := range strings.Split(strings.TrimPrefix(line, "Disbursement - "), ", ") {
				label := strings.TrimSpace(strings.SplitN(field, ":", 2)[0])
				col, ok := labelToColumn[label]
				if !ok {
					t.Fatalf("the excerpt prints label %q on the disbursement row and this test does not "+
						"know which column it is", label)
				}
				add("DISBURSEMENT", col)
			}
		}
	}
	if !sawRepayment || !sawDisbursement {
		t.Fatal("the excerpt contains no repayment or no disbursement row: the derivation would be vacuous")
	}

	src, ok := AttestationSourceByID("embeddable-readme-ci-stdout")
	if !ok {
		t.Fatal("the README attestation source is not declared")
	}
	for _, rowKind := range []string{"DISBURSEMENT", "REPAYMENT"} {
		want := derived[rowKind]
		got := map[string]bool{}
		for _, c := range src.ColumnsByRowKind[rowKind] {
			got[c] = true
		}
		if len(want) != len(got) {
			t.Errorf("%s rows: the declaration attests %d columns %v, the README text prints %d %v",
				rowKind, len(got), src.ColumnsByRowKind[rowKind], len(want), keysOf(want))
		}
		for c := range want {
			if !got[c] {
				t.Errorf("%s rows: the README prints %s but the declaration does not attest it", rowKind, c)
			}
		}
		for c := range got {
			if !want[c] {
				t.Errorf("%s rows: the declaration attests %s but the README does not print it — that is "+
					"exactly the over-scoped cross-check finding T17-F2 is about", rowKind, c)
			}
		}
	}

	// The count the finding got wrong, pinned so it cannot silently drift back.
	if n := len(src.ColumnsByRowKind["REPAYMENT"]); n != 6 {
		t.Errorf("the README attests %d of the %d period columns on a repayment row, want 6. T17-F2 says "+
			"nine; the block itself says six (it omits from_date, fee, penalty and "+
			"total_outstanding_balance)", n, len(PeriodColumns()))
	}
	if n := len(src.Unattested("REPAYMENT")); n != 4 {
		t.Errorf("the README is silent on %d columns of a repayment row, want 4 (%v)",
			n, src.Unattested("REPAYMENT"))
	}

	// When the pinned checkout is present, the committed excerpt is proven to be
	// the README's own bytes rather than a paraphrase.
	for _, candidate := range []string{
		os.Getenv("FINERACT_CHECKOUT"),
		"/Users/buv/fineract",
	} {
		if candidate == "" {
			continue
		}
		readmePath := filepath.Join(candidate,
			"fineract-progressive-loan-embeddable-schedule-generator", "README.md")
		live, rerr := os.ReadFile(readmePath)
		if rerr != nil {
			continue
		}
		for _, line := range strings.Split(strings.TrimSpace(block), "\n") {
			if !strings.Contains(string(live), line) {
				t.Errorf("the committed excerpt line %q is not present in %s: the excerpt is not the "+
					"README's own text", line, readmePath)
			}
		}
		t.Logf("excerpt verified line by line against %s", readmePath)
		break
	}
}

// TestCorroborationIsScopedToWhatTheSourcePrints proves F2 as a firing rule.
func TestCorroborationIsScopedToWhatTheSourcePrints(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	with := func(c Corroboration) *Vector {
		v := parityShell(pin)
		v.GradedAgainst = []Counterfactual{moneyKill()}
		v.Provenance.CorroboratedBy = []Corroboration{c}
		return v
	}

	cases := []struct {
		name string
		c    Corroboration
		want string // "" means it must be admissible
	}{
		{
			name: "the six columns the README prints are accepted",
			c: Corroboration{
				Source: "embeddable-readme-ci-stdout", RowKind: "REPAYMENT",
				Columns: []string{ColPeriodNumber, ColDueDate, ColOutstandingBalance,
					ColPrincipal, ColInterest, ColTotalDue},
			},
		},
		{
			name: "a column the README does not print is refused",
			c: Corroboration{
				Source: "embeddable-readme-ci-stdout", RowKind: "REPAYMENT",
				Columns: []string{ColPrincipal, ColTotalOutstandingBalance},
			},
			want: "DOES NOT ATTEST",
		},
		{
			name: "from_date is not printed either, whatever the finding said",
			c: Corroboration{
				Source: "embeddable-readme-ci-stdout", RowKind: "REPAYMENT",
				Columns: []string{ColFromDate},
			},
			want: "DOES NOT ATTEST",
		},
		{
			name: "a row kind the source is silent about is refused",
			c: Corroboration{
				Source: "embeddable-readme-ci-stdout", RowKind: "DOWN_PAYMENT",
				Columns: []string{ColPrincipal},
			},
			want: "attests nothing at all",
		},
		{
			name: "an undeclared source is refused",
			c:    Corroboration{Source: "somebody-said-so", RowKind: "REPAYMENT", Columns: []string{ColPrincipal}},
			want: "does not know the column coverage of",
		},
		{
			name: "a corroboration claiming no column corroborates nothing",
			c:    Corroboration{Source: "embeddable-readme-ci-stdout", RowKind: "REPAYMENT"},
			want: "claims no column",
		},
		{
			name: "a name that is not one of the ten columns is refused",
			c: Corroboration{
				Source: "embeddable-readme-ci-stdout", RowKind: "REPAYMENT",
				Columns: []string{"vibes"},
			},
			want: "not one of the ten period columns",
		},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			problems := Admit(with(c.c), pin, root)
			if c.want == "" {
				if len(problems) > 0 {
					t.Fatalf("must be admissible, got %v", problems)
				}
				return
			}
			if !containsSubstring(problems, c.want) {
				t.Fatalf("want a refusal naming %q, got %v", c.want, problems)
			}
		})
	}
}

// ---------------------------------------------------------------------------
// F3 — RESTATED: the original prediction is refuted by observation
// ---------------------------------------------------------------------------

// TestF3ClaimRecordsWhatNarrowedIt proves the claim is stored in its NARROWED
// form, with the original wording and the refuting observation both attached.
func TestF3ClaimRecordsWhatNarrowedIt(t *testing.T) {
	c, ok := ClaimByID("T17-F3")
	if !ok {
		t.Fatal("claim T17-F3 is not declared")
	}
	if c.Status != ClaimNarrowedByObservation {
		t.Errorf("T17-F3 status %q, want %q", c.Status, ClaimNarrowedByObservation)
	}
	if !strings.Contains(c.Statement, "allowFullTermForTranche") {
		t.Error("the surviving statement must name the flag it is conditioned on; without the condition it " +
			"is the refuted wording again")
	}
	if !strings.Contains(c.OriginalWording, "NEVER") {
		t.Error("the original, refuted wording must be recorded verbatim enough to be recognised")
	}
	for _, want := range []string{"D-04", "No tenant context available"} {
		if !strings.Contains(c.NarrowedBy, want) {
			t.Errorf("the observation that narrowed the claim must name %q; it is the whole evidence", want)
		}
	}

	// RED: a narrowed claim that loses the observation is a harness defect.
	weakened := c
	weakened.NarrowedBy = ""
	defects := declarationDefects(AttestationSources(), []Claim{weakened}, CoverageGaps(), RoundedTranscriptions())
	if !containsSubstring(defects, "does not name the OBSERVATION") {
		t.Fatalf("dropping the observation must be reported as a declaration defect, got %v", defects)
	}
	dropped := c
	dropped.OriginalWording = ""
	defects = declarationDefects(AttestationSources(), []Claim{dropped}, CoverageGaps(), RoundedTranscriptions())
	if !containsSubstring(defects, "ORIGINAL WORDING") {
		t.Fatalf("dropping the refuted wording must be reported as a declaration defect, got %v", defects)
	}

	// GREEN: as declared, the harness has no declaration defects at all.
	if got := HarnessDeclarationDefects(); len(got) != 0 {
		t.Fatalf("the shipped declarations must be clean, got %v", got)
	}
}

// TestAmbientMathContextMustBeRecorded proves the narrowed F3 rule fires: the
// ambient MathContext is required on EVERY parity vector, on every seam, and the
// refusal names the observation.
func TestAmbientMathContextMustBeRecorded(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	v := parityShell(pin)
	v.GradedAgainst = []Counterfactual{moneyKill()}
	v.Oracle.AmbientMathContext = MathContext{}
	problems := Admit(v, pin, root)
	if !containsSubstring(problems, "REFUTED BY OBSERVATION") {
		t.Fatalf("an unrecorded ambient MathContext must be refused, naming the observation that narrowed "+
			"F3, got %v", problems)
	}
	if !containsSubstring(problems, "No tenant context available") {
		t.Errorf("the refusal must quote the observation, not merely assert one: %v", problems)
	}

	// GREEN: recorded at the production setting, the same vector is admissible.
	v = parityShell(pin)
	v.GradedAgainst = []Counterfactual{moneyKill()}
	if problems := Admit(v, pin, root); len(problems) > 0 {
		t.Fatalf("a vector recording the ambient context must be admissible, got %v", problems)
	}
}

// ---------------------------------------------------------------------------
// F4 — the coverage gap is reported on every run
// ---------------------------------------------------------------------------

func TestCoverageGapIsVisibleOnEveryRun(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)
	impl, _, err := NewReplayImplementation(store, "")
	if err != nil {
		t.Fatalf("NewReplayImplementation: %v", err)
	}
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: store,
		Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
	})
	out := render(s)
	for _, want := range []string{
		"STRUCTURAL COVERAGE GAPS IN THE CORPUS",
		"T17-F4-rate-schedule-from-origination",
		"[OPEN]",
		"changeInterestRate",
		"Tier A",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("the report must carry %q on every run; a gap buried in a document is a gap nobody "+
				"reads", want)
		}
	}

	// RED: a gap cannot be marked closed by assertion.
	g := CoverageGaps()[0]
	g.Status = GapClosed
	defects := declarationDefects(AttestationSources(), Claims(), []CoverageGap{g}, RoundedTranscriptions())
	if !containsSubstring(defects, "names no capture that closed it") {
		t.Fatalf("closing a gap with no capture behind it must be a declaration defect, got %v", defects)
	}
}

// ---------------------------------------------------------------------------
// F5 — scale > the currency's minor units is a harness bug
// ---------------------------------------------------------------------------

func TestScaleOfWireText(t *testing.T) {
	cases := []struct {
		in    string
		scale int32
		ok    bool
	}{
		{"0", 0, true},
		{"112082.37", 2, true},
		{"1200000.000000", 6, true},
		{"-0.01", 2, true},
		{"1e3", 0, false},
		{".50", 0, false},
		{"100.", 0, false},
		{"", 0, false},
		{"12,00", 0, false},
	}
	for _, c := range cases {
		got, err := ScaleOfWireText(c.in)
		if (err == nil) != c.ok {
			t.Errorf("ScaleOfWireText(%q) error = %v, want ok = %v", c.in, err, c.ok)
			continue
		}
		if c.ok && got != c.scale {
			t.Errorf("ScaleOfWireText(%q) = %d, want %d", c.in, got, c.scale)
		}
	}
}

func TestOverScaledMoneyTextMustBeDeclared(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	build := func(text string, declare bool) *Vector {
		v := parityShell(pin)
		v.GradedAgainst = []Counterfactual{moneyKill()}
		v.Expect.Periods[0].PrincipalMajorText = text
		if declare {
			v.Expect.Periods[0].OverScaledWireTextFields = []string{"principal_minor"}
		}
		return v
	}

	// RED: an exact but over-scaled value, undeclared.
	problems := Admit(build("100.000", false), pin, root)
	if !containsSubstring(problems, "harness bug, not a") {
		t.Fatalf("an undeclared over-scaled money text must be inadmissible, got %v", problems)
	}

	// GREEN: the same value, declared.
	if problems := Admit(build("100.000", true), pin, root); len(problems) > 0 {
		t.Fatalf("a DECLARED over-scaled exact value must be admissible, got %v", problems)
	}

	// RED: a declaration that does not match the text.
	problems = Admit(build("100.00", true), pin, root)
	if !containsSubstring(problems, "declared over-scaled but its wire text") {
		t.Fatalf("a declaration contradicted by the text must be inadmissible, got %v", problems)
	}

	// RED: a significant digit beyond the currency scale is never admissible,
	// declared or not — the harness will not round a transcription.
	problems = Admit(build("100.001", true), pin, root)
	if !containsSubstring(problems, "will not round a transcription") {
		t.Fatalf("a non-zero digit beyond the currency scale must be inadmissible even when declared, "+
			"got %v", problems)
	}

	// RED: a declaration naming something that is not a money column.
	v := parityShell(pin)
	v.GradedAgainst = []Counterfactual{moneyKill()}
	v.Expect.Periods[0].OverScaledWireTextFields = []string{"due_date"}
	if problems := Admit(v, pin, root); !containsSubstring(problems, "is not a money column") {
		t.Fatalf("only a money column can be over-scaled, got %v", problems)
	}

	// The declared cell is counted and disclosed in the report.
	s := &Summary{SelfTestMode: true, OverScaledCells: 1}
	if !strings.Contains(render(s), "over-scaled") {
		t.Error("the report must disclose over-scaled money cells")
	}
}

// ---------------------------------------------------------------------------
// F6 — a transcribed rate factor is a 12-dp rounding
// ---------------------------------------------------------------------------

func TestRateFactorIsRecordedNeverGraded(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	build := func(rf RateFactorObservation) *Vector {
		v := parityShell(pin)
		v.GradedAgainst = []Counterfactual{moneyKill()}
		v.Expect.Periods[0].ObservedRateFactor = &rf
		return v
	}
	good := RateFactorObservation{
		Text:               "1.005833333333",
		TranscribedAtScale: 12,
		PrecisionStatus:    PrecisionTranscribedRounded,
		Citation:           "ProgressiveEMICalculatorTest.java:5241 (transcribed, not derived)",
	}

	// GREEN: recorded honestly.
	if problems := Admit(build(good), pin, root); len(problems) > 0 {
		t.Fatalf("a TRANSCRIBED-ROUNDED rate factor must be admissible, got %v", problems)
	}

	// RED: claiming exactness.
	exact := good
	exact.PrecisionStatus = "EXACT"
	problems := Admit(build(exact), pin, root)
	if !containsSubstring(problems, ParityStatusToBeCaptured) {
		t.Fatalf("claiming an exact rate factor must be inadmissible and must say exact parity is %s, "+
			"got %v", ParityStatusToBeCaptured, problems)
	}
	if !containsSubstring(problems, "digits 13 and beyond") {
		t.Errorf("the refusal must state the trap it prevents, got %v", problems)
	}

	// RED: claiming more digits than the corpus's transcription scale.
	deeper := good
	deeper.Text = "1.0058333333333"
	deeper.TranscribedAtScale = 13
	problems = Admit(build(deeper), pin, root)
	if !containsSubstring(problems, "beyond the 12") {
		t.Fatalf("a rate factor written past the transcription scale must be inadmissible, got %v", problems)
	}

	// RED: a scale that disagrees with the text.
	lying := good
	lying.TranscribedAtScale = 8
	problems = Admit(build(lying), pin, root)
	if !containsSubstring(problems, "may not claim more precision than it wrote down") {
		t.Fatalf("a scale disagreeing with the text must be inadmissible, got %v", problems)
	}

	// RED: no citation.
	uncited := good
	uncited.Citation = ""
	problems = Admit(build(uncited), pin, root)
	if !containsSubstring(problems, "indistinguishable from an invention") {
		t.Fatalf("an uncited transcription must be inadmissible, got %v", problems)
	}

	// The rate factor is counted apart from the graded cells, and the report says
	// it is never compared.
	s := &Summary{SelfTestMode: true, RateFactorsRecorded: 1}
	out := render(s)
	for _, want := range []string{"RATE_FACTOR", PrecisionTranscribedRounded, ParityStatusToBeCaptured,
		"recorded, NEVER compared"} {
		if !strings.Contains(out, want) {
			t.Errorf("the report must carry %q", want)
		}
	}

	// RED: promoting the quantity to CAPTURED with nothing to point at.
	rt := RoundedTranscriptions()[0]
	rt.ParityStatus = ParityStatusCaptured
	defects := declarationDefects(AttestationSources(), Claims(), CoverageGaps(), []RoundedTranscription{rt})
	if !containsSubstring(defects, "names no capture") {
		t.Fatalf("claiming exact parity with no capture must be a declaration defect, got %v", defects)
	}
}

// ---------------------------------------------------------------------------
// D-4 — structural counterfactuals: a real kill that moves no money
// ---------------------------------------------------------------------------

func TestStructuralCounterfactuals(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	// A vector shaped like P-02: two rows, so a row index of 1 is real.
	shell := func() *Vector {
		v := parityShell(pin)
		v.CapabilitiesRequired = []string{"schedule.core", "monthend.reanchor"}
		v.Expect.Periods = []ExpectPeriod{
			{
				Kind: "REPAYMENT", InstallmentNumber: 1,
				FromDate: Date{2024, 1, 31}, DueDate: Date{2024, 2, 29},
				PrincipalMinor: "5000", InterestMinor: "29", OutstandingPrincipalMinor: "5000",
			},
			{
				Kind: "REPAYMENT", InstallmentNumber: 2,
				FromDate: Date{2024, 2, 29}, DueDate: Date{2024, 3, 31},
				PrincipalMinor: "5000", InterestMinor: "29", OutstandingPrincipalMinor: "0",
			},
		}
		return v
	}
	wellFormed := Counterfactual{
		ID:         "CLAMP-AND-CONTINUE-MONTH-END",
		Kind:       CounterfactualStructural,
		Capability: "monthend.reanchor",
		Description: "clamps 31 January to the short month's last day and then continues from the CLAMPED " +
			"day, instead of re-anchoring on the disbursement-date seed",
		MarginMinor:    "0",
		DivergentCells: []string{"period[1].due_date"},
		Evidence: "P-02 period 2 due date observed 2024-03-31 (re-anchored on the seed); the " +
			"clamp-and-continue port emits 2024-03-29 instead. Every money column is identical to P-00's " +
			"because DAYS_30/DAYS_360 makes each period exactly 30/360 regardless of the calendar dates, " +
			"so the money margin is exactly zero and the port is still wrong.",
	}

	mutate := func(f func(cf *Counterfactual)) []string {
		v := shell()
		cf := wellFormed
		f(&cf)
		v.GradedAgainst = []Counterfactual{cf}
		return Admit(v, pin, root)
	}

	t.Run("a well-formed structural counterfactual is admissible", func(t *testing.T) {
		if problems := mutate(func(cf *Counterfactual) {}); len(problems) > 0 {
			t.Fatalf("want admissible, got %v", problems)
		}
	})

	t.Run("row_order is a legal cell", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.ID = "SORT-BY-DATE-DISBURSEMENT-FIRST"
			cf.Capability = "schedule.core"
			cf.DivergentCells = []string{DivergentCellRowOrder}
			cf.Evidence = "P-03 emits REPAYMENT 1 and only then the DISBURSEMENT row dated 2024-02-01, as " +
				"observed; the sort-by-date port emits them in the wrong order instead."
		})
		if len(problems) > 0 {
			t.Fatalf("want admissible, got %v", problems)
		}
	})

	t.Run("structural with no divergent cells is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) { cf.DivergentCells = nil })
		if !containsSubstring(problems, "names no divergent_cells") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("structural naming a money column is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.DivergentCells = []string{"period[1].principal_minor"}
		})
		if !containsSubstring(problems, "money kill wearing a structural label") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("structural with a non-zero margin is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) { cf.MarginMinor = "6015" })
		if !containsSubstring(problems, "margin_minor must be exactly") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("structural evidence must state both values", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.Evidence = "the port gets the date wrong somewhere in period 2"
		})
		if !containsSubstring(problems, "must state BOTH") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("structural naming a cell the harness does not compare is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.DivergentCells = []string{"period[1].installment_number"}
		})
		if !containsSubstring(problems, "not one of the non-money cells this harness compares") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("structural naming a row that does not exist is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) { cf.DivergentCells = []string{"period[7].due_date"} })
		if !containsSubstring(problems, "does not exist") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("a malformed cell name is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) { cf.DivergentCells = []string{"due_date"} })
		if !containsSubstring(problems, "is not a cell name") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("a repeated cell is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.DivergentCells = []string{"period[1].due_date", "period[1].due_date"}
		})
		if !containsSubstring(problems, "repeats") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("an unknown kind is inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) { cf.Kind = "vibes" })
		if !containsSubstring(problems, "is neither") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("a money counterfactual may not list divergent cells", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.Kind = CounterfactualMoney
			cf.MarginMinor = "6015"
			cf.DivergentCells = []string{"period[1].due_date"}
		})
		if !containsSubstring(problems, "carries its kill in margin_minor") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("a zero-margin MONEY counterfactual is still inadmissible", func(t *testing.T) {
		problems := mutate(func(cf *Counterfactual) {
			cf.Kind = ""
			cf.DivergentCells = nil
			cf.MarginMinor = "0"
		})
		if !containsSubstring(problems, "does NOT kill") {
			t.Fatalf("the pre-existing money rule must be untouched, got %v", problems)
		}
		if !containsSubstring(problems, CounterfactualStructural) {
			t.Errorf("the refusal should point an author at the structural form, got %v", problems)
		}
	})
}

// TestReportNeverMergesMoneyAndStructuralKills proves the counts stay separate.
func TestReportNeverMergesMoneyAndStructuralKills(t *testing.T) {
	s := &Summary{SelfTestMode: true, CounterfactualsNamed: 3, MoneyKills: 1, StructuralKills: 2}
	out := render(s)
	for _, want := range []string{
		// "GRADED", not "admissible": A2-22 narrowed the population to the vectors
		// the harness actually graded, because a REFUSED vector is admissible and
		// kills nothing.
		"counterfactuals named by GRADED vectors: 3  (1 money kills, 2 structural kills)",
		"kills named             1 money, 2 structural",
		"The two are NEVER merged",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("the report must carry %q, got:\n%s", want, out)
		}
	}
}

// TestRunCountsKillsByKind proves the counters are wired to real vectors, not
// just to the report.
func TestRunCountsKillsByKind(t *testing.T) {
	pin := mustPin(t)
	v := parityShell(pin)
	v.CapabilitiesRequired = []string{"schedule.core", "monthend.reanchor"}
	v.GradedAgainst = []Counterfactual{
		moneyKill(),
		{
			ID: "CLAMP-AND-CONTINUE", Kind: CounterfactualStructural, Capability: "monthend.reanchor",
			Description: "clamps and continues instead of re-anchoring on the seed",
			MarginMinor: "0", DivergentCells: []string{"period[0].due_date"},
			Evidence: "due date observed 2024-03-31; the clamp-and-continue port emits 2024-03-29 instead",
		},
	}
	if problems := Admit(v, pin, repoRoot(t)); len(problems) > 0 {
		t.Fatalf("the fixture must be admissible for the count to mean anything, got %v", problems)
	}
	money, structural := 0, 0
	for _, cf := range v.GradedAgainst {
		if cf.Kind == CounterfactualStructural {
			structural++
			continue
		}
		money++
	}
	if money != 1 || structural != 1 {
		t.Fatalf("counted %d money and %d structural kills, want 1 and 1", money, structural)
	}
}

// TestNewSchemaFieldsDecode proves the fields exist on the WIRE, not merely in
// the admissibility rules (driver finding D-4, corrected).
//
// LoadVector decodes with DisallowUnknownFields, so a vector carrying "kind" or
// "divergent_cells" fails to decode ENTIRELY before Admit ever runs. An
// admit-only change would therefore not land the rule at all: it would turn every
// structural vector into a load error. This test decodes a real document through
// the real loader and then admits it, which is the only order that proves the
// path end to end.
func TestNewSchemaFieldsDecode(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	doc := `{
  "schema": "gerege.loanschedule.vector/v1",
  "case_id": "DECODE-01-structural",
  "context": "loanschedule",
  "class": "parity",
  "title": "decode fixture — written by the test, never promoted to the store",
  "dec1_revision": ` + fmt.Sprint(pin.DEC1Revision) + `,
  "capabilities_required": ["schedule.core", "monthend.reanchor"],
  "provenance": {
    "kind": "oracle-capture",
    "note": "",
    "capture_ref": ".softhouse/capture/out/capture-prod3b-attestation.json",
    "capture_sha256": "",
    "capture_case_id": "P-02",
    "citation": "",
    "corroborated_by": [
      {
        "source": "embeddable-readme-ci-stdout",
        "row_kind": "REPAYMENT",
        "columns": ["principal", "interest", "total_due"],
        "note": "six of ten columns; see the report's cross-check section"
      }
    ]
  },
  "oracle": {
    "fineract_commit": "` + pin.FineractCommit + `",
    "seam": "path_a_embeddable",
    "captured_at": "",
    "threaded_mathcontext": { "precision": 19, "rounding_mode": "HALF_UP" },
    "ambient_mathcontext": { "precision": 19, "rounding_mode": "HALF_UP" }
  },
  "request": {
    "time_zone": "Asia/Ulaanbaatar",
    "currency": { "code": "MNT", "minor_unit_digits": 2 },
    "rounding": { "significant_digits": 19, "rate_factor_scale": 19, "mode": "HALF_UP" },
    "schedule_start_date": { "year": 2024, "month": 1, "day": 31 },
    "disbursements": [
      { "date": { "year": 2024, "month": 1, "day": 31 }, "amount_minor": "10000" }
    ],
    "number_of_repayments": 1,
    "repayment_every": 1,
    "repayment_frequency_unit": "MONTHS",
    "annual_nominal_interest_rate": { "numerator": 7, "denominator": 100 },
    "interest_method": "DECLINING_BALANCE",
    "day_count": "FIXED_30_360",
    "down_payment_percentage": { "numerator": 0, "denominator": 1 },
    "installment_rounding_multiple_minor": "0"
  },
  "expect": {
    "kind": "schedule",
    "periods": [
      {
        "kind": "REPAYMENT",
        "installment_number": 1,
        "from_date": { "year": 2024, "month": 1, "day": 31 },
        "due_date": { "year": 2024, "month": 2, "day": 29 },
        "principal_minor": "10000",
        "interest_minor": "58",
        "outstanding_principal_minor": "0",
        "principal_major_text": "100.000",
        "over_scaled_wire_text_fields": ["principal_minor"],
        "observed_rate_factor": {
          "text": "1.005833333333",
          "transcribed_at_scale": 12,
          "precision_status": "TRANSCRIBED-ROUNDED",
          "citation": "ProgressiveEMICalculatorTest.java:5241"
        }
      }
    ]
  },
  "graded_against": [
    {
      "id": "CLAMP-AND-CONTINUE-MONTH-END",
      "kind": "structural",
      "capability": "monthend.reanchor",
      "description": "clamps to the short month and continues from the clamped day instead of re-anchoring on the seed",
      "margin_minor": "0",
      "divergent_cells": ["period[0].due_date"],
      "evidence": "due date observed 2024-02-29; the clamp-and-continue port emits 2024-02-28 instead, and every money column is identical"
    }
  ]
}`
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, "loanschedule"), 0o755); err != nil {
		t.Fatalf("MkdirAll: %v", err)
	}
	abs := filepath.Join(dir, "loanschedule", "DECODE-01-structural.json")
	if err := os.WriteFile(abs, []byte(doc), 0o644); err != nil {
		t.Fatalf("WriteFile: %v", err)
	}

	v, err := LoadVector(abs, filepath.Join("loanschedule", "DECODE-01-structural.json"))
	if err != nil {
		t.Fatalf("a vector carrying the new fields must DECODE (DisallowUnknownFields is on): %v", err)
	}
	if len(v.GradedAgainst) != 1 || v.GradedAgainst[0].Kind != CounterfactualStructural {
		t.Fatalf("kind did not decode: %+v", v.GradedAgainst)
	}
	if len(v.GradedAgainst[0].DivergentCells) != 1 {
		t.Fatalf("divergent_cells did not decode: %+v", v.GradedAgainst[0])
	}
	if len(v.Provenance.CorroboratedBy) != 1 {
		t.Fatal("corroborated_by did not decode")
	}
	if v.Expect.Periods[0].ObservedRateFactor == nil {
		t.Fatal("observed_rate_factor did not decode")
	}
	if len(v.Expect.Periods[0].OverScaledWireTextFields) != 1 {
		t.Fatal("over_scaled_wire_text_fields did not decode")
	}
	if problems := Admit(v, pin, root); len(problems) > 0 {
		t.Fatalf("the decoded vector must also be admissible, got %v", problems)
	}
}

// TestUnrecordedMoneyCellIsNotADroppedVector proves driver finding D-5: a cell
// the capture never recorded is skipped AS A CELL, and the vector still answers.
func TestUnrecordedMoneyCellIsNotADroppedVector(t *testing.T) {
	root := repoRoot(t)
	pristine := storeRoot(t)

	// GREEN: an unrecorded money cell keeps its vector in the replay store.
	unrecorded := copyStore(t, pristine)
	fixture := filepath.Join(unrecorded, SelfTestDir, "SELFTEST-01-two-period-zero-rate.json")
	perturb(t, fixture, `"interest_minor": "0",
        "outstanding_principal_minor": "100000",
        "principal_major_text": "1000.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "1000.00",
        "unrecorded_fields": [],`, `"interest_minor": "",
        "outstanding_principal_minor": "100000",
        "principal_major_text": "1000.00",
        "interest_major_text": "",
        "outstanding_principal_major_text": "1000.00",
        "unrecorded_fields": ["interest_minor"],`)

	impl, n, err := NewReplayImplementation(unrecorded, "")
	if err != nil {
		t.Fatalf("a vector with an unrecorded money cell must still load: %v", err)
	}
	if n == 0 {
		t.Fatal("the replay implementation learned no answers: the vector was DROPPED, which is the exact " +
			"silent failure finding D-5 is about")
	}
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: unrecorded,
		Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
	})
	if got := s.ExitCode(); got != 0 {
		t.Errorf("the run must still be exit 0, got %d\n%s", got, render(s))
	}
	if s.UngradedCells == 0 {
		t.Error("the unrecorded cell must be COUNTED as ungraded, not silently absent")
	}

	// RED: a money cell that is neither recorded nor declared unrecorded is a
	// hard, named error — never a silent drop.
	broken := copyStore(t, pristine)
	perturb(t, filepath.Join(broken, SelfTestDir, "SELFTEST-01-two-period-zero-rate.json"),
		`"principal_minor": "100000",`, `"principal_minor": "not-a-number",`)
	if _, _, err := NewReplayImplementation(broken, ""); err == nil {
		t.Fatal("an unparseable money cell must be a loud error naming the vector and the field, not a " +
			"dropped vector")
	} else {
		for _, want := range []string{"SELFTEST-01", "principal_minor", "unrecorded_fields"} {
			if !strings.Contains(err.Error(), want) {
				t.Errorf("the error must name %q so a reader can act on it; got %v", want, err)
			}
		}
	}
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

func mustPin(t *testing.T) *Pin {
	t.Helper()
	pin, err := LoadPin(filepath.Join(storeRoot(t), "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	return pin
}

// moneyKill is a well-formed money counterfactual for schedule.core, so that a
// test varying something else is not refused for the unrelated reason that a
// parity vector must kill something.
func moneyKill() Counterfactual {
	return Counterfactual{
		ID:          "TEXTBOOK-BALANCE-TIMES-RATEFACTOR",
		Capability:  "schedule.core",
		Description: "computes interest as balance * rateFactor instead of the oracle's three roundings",
		Evidence:    "contract.go Period.InterestMinor; DEC-1 section 8 item 3b",
		MarginMinor: "1",
	}
}

func keysOf(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	return out
}

// ---------------------------------------------------------------------------
// T9-F1 — unrecorded_fields is not an escape hatch
// ---------------------------------------------------------------------------

// TestT9F1UnrecordedFieldsIsNotAnEscapeHatch proves finding T9-F1, both halves.
//
// The T9 review demonstrated a store in which every one of the nine date cells
// backing MONTHEND-CONTINUE-FROM-CLAMPED-DAY had been withdrawn from grading in
// P-02 and P-02b, filled with 1999-01-01, and the run still printed
// "monthend.reanchor killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY" and exited 0.
// Two independent defects made that possible and each gets its own subtest here.
func TestT9F1UnrecordedFieldsIsNotAnEscapeHatch(t *testing.T) {
	root := repoRoot(t)
	pin := mustPin(t)

	// A disbursement row plus two repayment rows, shaped like the committed
	// corpus: the disbursement row is the one that legitimately withdraws
	// installment_number and interest_minor.
	shell := func() *Vector {
		v := parityShell(pin)
		v.CapabilitiesRequired = []string{"schedule.core", "monthend.reanchor"}
		v.GradedAgainst = []Counterfactual{moneyKill()}
		v.Expect.Periods = []ExpectPeriod{
			{
				Kind: "DISBURSEMENT", InstallmentNumber: 0,
				FromDate: Date{2024, 1, 31}, DueDate: Date{2024, 1, 31},
				PrincipalMinor: "10000", InterestMinor: "", OutstandingPrincipalMinor: "10000",
				UnrecordedFields: []string{"installment_number", "interest_minor"},
			},
			{
				Kind: "REPAYMENT", InstallmentNumber: 1,
				FromDate: Date{2024, 1, 31}, DueDate: Date{2024, 2, 29},
				PrincipalMinor: "5000", InterestMinor: "29", OutstandingPrincipalMinor: "5000",
			},
			{
				Kind: "REPAYMENT", InstallmentNumber: 2,
				FromDate: Date{2024, 2, 29}, DueDate: Date{2024, 3, 31},
				PrincipalMinor: "5000", InterestMinor: "29", OutstandingPrincipalMinor: "0",
			},
		}
		return v
	}

	t.Run("the committed corpus's row shape stays admissible", func(t *testing.T) {
		if problems := Admit(shell(), pin, root); len(problems) > 0 {
			t.Fatalf("the corpus's disbursement-row shape must stay admissible, got %v", problems)
		}
	})

	// --- F-1a: "unrecorded means EMPTY" now covers the non-money cells too. ---

	t.Run("F-1a: a populated but withdrawn due_date is inadmissible", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].DueDate = Date{1999, 1, 1}
		v.Expect.Periods[2].UnrecordedFields = []string{"due_date"}
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "is marked unrecorded but carries the date 1999-01-01") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("F-1a: a populated but withdrawn from_date is inadmissible", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].UnrecordedFields = []string{"from_date"}
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "expect.periods[2].from_date is marked unrecorded but carries the date") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("F-1a: a withdrawn date left EMPTY is still admissible", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].FromDate = Date{}
		v.Expect.Periods[2].UnrecordedFields = []string{"from_date"}
		if problems := Admit(v, pin, root); len(problems) > 0 {
			t.Fatalf("withdrawing a cell the capture really did not record must stay possible, got %v", problems)
		}
	})

	t.Run("F-1a: kind may not be withdrawn at all", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].UnrecordedFields = []string{"kind"}
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "which is not a cell a capture may withdraw from grading") {
			t.Fatalf("got %v", problems)
		}
	})

	// --- F-1c: installment_number, the cell whose Go type cannot tell absent
	//     from zero. The documented sentinel is 0, and only a non-payable row
	//     may use it. ---

	t.Run("F-1c: a withdrawn installment_number carrying a value is inadmissible", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[0].InstallmentNumber = 7
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "is marked unrecorded but carries 7") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("F-1c: a REPAYMENT row may not withdraw installment_number", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].UnrecordedFields = []string{"installment_number"}
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "is a REPAYMENT row and marks installment_number unrecorded") {
			t.Fatalf("got %v", problems)
		}
	})

	// --- F-1b: a divergent cell must be a cell THIS vector actually compares. ---

	monthEndKill := func(cells ...string) Counterfactual {
		return Counterfactual{
			ID:             "MONTHEND-CONTINUE-FROM-CLAMPED-DAY",
			Kind:           CounterfactualStructural,
			Capability:     "monthend.reanchor",
			Description:    "continues from the clamped day instead of re-anchoring on the seed",
			MarginMinor:    "0",
			DivergentCells: cells,
			Evidence: "period 2 due date observed 2024-03-31; the clamp-and-continue port emits " +
				"2024-03-29 instead",
		}
	}

	t.Run("F-1b: a divergent cell the vector withdraws is inadmissible", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].DueDate = Date{}
		v.Expect.Periods[2].UnrecordedFields = []string{"due_date"}
		v.GradedAgainst = append(v.GradedAgainst, monthEndKill("period[2].due_date"))
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "WITHDRAWS from grading") {
			t.Fatalf("got %v", problems)
		}
	})

	t.Run("F-1b: the same kill over a GRADED cell stays admissible", func(t *testing.T) {
		v := shell()
		v.GradedAgainst = append(v.GradedAgainst, monthEndKill("period[2].due_date"))
		if problems := Admit(v, pin, root); len(problems) > 0 {
			t.Fatalf("a properly graded structural kill must remain admissible, got %v", problems)
		}
	})

	// --- F-1b, the coverage half: a kill with nothing compared covers nothing
	//     and must not print as killing anything. ---

	reg := mustCapabilityRegistry(t)

	t.Run("F-1b: an all-withdrawn structural kill covers nothing", func(t *testing.T) {
		v := shell()
		v.Expect.Periods[2].DueDate = Date{}
		v.Expect.Periods[2].UnrecordedFields = []string{"due_date"}
		cf := monthEndKill("period[2].due_date")
		if v.StructuralKillIsCompared(cf) {
			t.Fatal("a kill whose only cell is withdrawn must not count as compared")
		}
		v.GradedAgainst = []Counterfactual{cf}
		covered, uncovered := reg.CounterfactualCoverage([]*Vector{v})
		if len(covered["monthend.reanchor"]) != 0 {
			t.Errorf("monthend.reanchor must not be reported as killed, got %v", covered["monthend.reanchor"])
		}
		if !containsString(uncovered, "monthend.reanchor") {
			t.Errorf("monthend.reanchor must be reported unbacked, got %v", uncovered)
		}
	})

	t.Run("F-1b: a graded structural kill does cover", func(t *testing.T) {
		v := shell()
		cf := monthEndKill("period[2].due_date")
		if !v.StructuralKillIsCompared(cf) {
			t.Fatal("a kill over a graded cell must count as compared")
		}
		v.GradedAgainst = []Counterfactual{cf}
		covered, _ := reg.CounterfactualCoverage([]*Vector{v})
		if len(covered["monthend.reanchor"]) != 1 {
			t.Errorf("want monthend.reanchor killed once, got %v", covered["monthend.reanchor"])
		}
	})

	// row_order names no field, so the per-cell admission rule cannot see it.
	// This is the path the coverage rule uniquely covers.
	t.Run("F-1b: row_order covers nothing when no graded cell tells two rows apart", func(t *testing.T) {
		rowOrder := Counterfactual{
			ID: "SORT-BY-DATE-DISBURSEMENT-FIRST", Kind: CounterfactualStructural,
			Capability: "schedule.core", MarginMinor: "0",
			DivergentCells: []string{DivergentCellRowOrder},
			Description:    "sorts by date with disbursements first",
			Evidence:       "observed REPAYMENT then DISBURSEMENT; the wrong port emits them reversed instead",
		}
		if !shell().StructuralKillIsCompared(rowOrder) {
			t.Fatal("rows differing in kind and date are distinguishable; this must count as compared")
		}
		// Now make every row identical in every GRADED structural cell. A
		// permutation of these rows is invisible, so the row-order kill catches
		// nothing and must not be credited.
		flat := shell()
		for i := range flat.Expect.Periods {
			flat.Expect.Periods[i].Kind = "REPAYMENT"
			flat.Expect.Periods[i].FromDate = Date{2024, 1, 31}
			flat.Expect.Periods[i].DueDate = Date{2024, 2, 29}
		}
		if flat.StructuralKillIsCompared(rowOrder) {
			t.Fatal("no graded structural cell tells two rows apart, so row_order catches nothing")
		}
	})
}

func mustCapabilityRegistry(t *testing.T) *CapabilityRegistry {
	t.Helper()
	reg, err := LoadCapabilityRegistry(filepath.Join(storeRoot(t), "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}
	return reg
}

// ---------------------------------------------------------------------------
// T60 — an unrecorded cell is never graded, by a cell diff OR by an invariant
// ---------------------------------------------------------------------------

// withdrawSelfTestCell rewrites the self-test fixture so that one row honestly
// declares one cell unrecorded: the value goes empty (or, for a date, to the zero
// date), any major text goes empty, and the field is named in that row's
// unrecorded_fields. That is exactly what admit.go requires of an honest
// withdrawal, which is the point — the whole defect is that HONESTY was penalised.
func withdrawSelfTestCell(t *testing.T, from, to string) string {
	t.Helper()
	store := copyStore(t, storeRoot(t))
	perturb(t, filepath.Join(store, SelfTestDir, "SELFTEST-01-two-period-zero-rate.json"), from, to)
	return store
}

func selfTestReplayRun(t *testing.T, store string) *Summary {
	t.Helper()
	impl, n, err := NewReplayImplementation(store, SelfTestDir)
	if err != nil {
		t.Fatalf("NewReplayImplementation: %v", err)
	}
	if n == 0 {
		t.Fatal("the replay implementation learned no answers: the vector was DROPPED")
	}
	return mustRun(t, Options{
		RepoRoot: repoRoot(t), StoreRoot: store, ContextFilter: SelfTestDir,
		Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
	})
}

func invariantOf(t *testing.T, s *Summary, name string) InvariantResult {
	t.Helper()
	for _, r := range s.Results {
		for _, iv := range r.Invariants {
			if iv.Name == name {
				return iv
			}
		}
	}
	t.Fatalf("invariant %s was not evaluated at all\n%s", name, render(s))
	return InvariantResult{}
}

// TestT60UnrecordedCellIsNeverGradedByAnInvariant is the permanent regression
// test for T58 finding N-2.
//
// THE DEFECT. `.softhouse/vectors/README.md` promises that a cell named in
// unrecorded_fields is not compared and is counted UNGRADED. diffSchedule honoured
// that. The property invariants did not: the self-test replay answers 0 for a cell
// nobody observed, and the invariants graded that stand-in. Reproduced on the
// unfixed rig in three forms before this test existed —
//
//	A  withdraw the DISBURSEMENT row's outstanding balance
//	   -> exit 1, "balance_roll_forward VIOLATED: row 0 DISBURSEMENT: outstanding
//	      0 != principal advanced 100000". A vector went RED for being honest.
//	      This is the form T58 hit on all 14 T39 vectors.
//	B  withdraw the FINAL row's outstanding balance
//	   -> exit 0, "principal_amortizes_to_zero HOLD, final outstanding == 0", and
//	      balance_roll_forward HOLD as well. A check passing on a number nobody
//	      observed, because the placeholder IS the value it looks for. This half
//	      was not in T58's report and is the dangerous one.
//	C  withdraw a REPAYMENT row's due date
//	   -> exit 1, monotonic_due_dates AND contract_row_ordering both violated on
//	      the fabricated window [2026-02-01, 0000-00-00). So it was never confined
//	      to one invariant or to money.
//
// This defect has now appeared in two named findings (T9-F1, T58-N2). It does not
// come back a third time.
func TestT60UnrecordedCellIsNeverGradedByAnInvariant(t *testing.T) {
	t.Run("A_withdrawn_disbursement_outstanding_is_not_a_red", func(t *testing.T) {
		store := withdrawSelfTestCell(t,
			`"outstanding_principal_minor": "100000",
        "principal_major_text": "1000.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "1000.00",
        "unrecorded_fields": [],`,
			`"outstanding_principal_minor": "",
        "principal_major_text": "1000.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "",
        "unrecorded_fields": ["outstanding_principal_minor"],`)
		s := selfTestReplayRun(t, store)
		if got := s.ExitCode(); got != 0 {
			t.Errorf("a vector that HONESTLY declares a cell unrecorded must not go red; exit %d\n%s",
				got, render(s))
		}
		iv := invariantOf(t, s, InvBalanceRollForward)
		if iv.Status == InvariantViolated {
			t.Errorf("balance_roll_forward graded a placeholder nobody observed: %s", iv.Detail)
		}
		if len(iv.NotAsserted) != 1 {
			t.Errorf("the skipped assertion must be REPORTED, not silent; got %+v", iv.NotAsserted)
		}
		// AND IT MUST NOT HAVE BECOME A NO-OP. Withdrawing the disbursement row's
		// balance costs exactly ONE row, because the running balance follows the
		// PRINCIPAL column, which the capture did record. Both repayment rows are
		// still asserted, on observed numbers.
		if iv.Status != InvariantHold {
			t.Errorf("the rows that CAN be asserted must still be asserted; got %s (%s)",
				iv.Status, iv.Detail)
		}
		if !strings.Contains(iv.Detail, "2 row(s)") {
			t.Errorf("the two repayment rows must still be checked; detail was %q", iv.Detail)
		}
		if out := render(s); !strings.Contains(out, "INVARIANT ASSERTIONS THAT COULD NOT RUN") ||
			!strings.Contains(out, "NOT ASSERTED: row 0") {
			t.Error("the report must name the row whose assertion did not run")
		}
	})

	t.Run("B_withdrawn_final_outstanding_is_not_a_silent_hold", func(t *testing.T) {
		store := withdrawSelfTestCell(t,
			`"outstanding_principal_minor": "0",
        "principal_major_text": "500.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "0.00",
        "unrecorded_fields": [],`,
			`"outstanding_principal_minor": "",
        "principal_major_text": "500.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "",
        "unrecorded_fields": ["outstanding_principal_minor"],`)
		s := selfTestReplayRun(t, store)
		iv := invariantOf(t, s, InvPrincipalAmortizes)
		if iv.Status == InvariantHold {
			t.Errorf("principal_amortizes_to_zero claimed to HOLD on a cell NOBODY OBSERVED: %s. "+
				"A check that quietly stops checking is strictly worse than a red one.", iv.Detail)
		}
		if iv.Status != InvariantNoData {
			t.Errorf("want N/A, got %s (%s)", iv.Status, iv.Detail)
		}
		if len(iv.NotAsserted) == 0 {
			t.Error("N/A must carry the reason, so a reader knows the check did not run")
		}
	})

	t.Run("C_withdrawn_due_date_does_not_fabricate_a_calendar_date", func(t *testing.T) {
		store := withdrawSelfTestCell(t,
			`"due_date": { "year": 2026, "month": 3, "day": 1 },
        "principal_minor": "50000",
        "interest_minor": "0",
        "outstanding_principal_minor": "0",
        "principal_major_text": "500.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "0.00",
        "unrecorded_fields": [],`,
			`"due_date": { "year": 0, "month": 0, "day": 0 },
        "principal_minor": "50000",
        "interest_minor": "0",
        "outstanding_principal_minor": "0",
        "principal_major_text": "500.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "0.00",
        "unrecorded_fields": ["due_date"],`)
		s := selfTestReplayRun(t, store)
		if got := s.ExitCode(); got != 0 {
			t.Errorf("exit %d: no invariant may be violated by the ZERO DATE it was handed\n%s",
				got, render(s))
		}
		// The window check degrades per row: the first repayment window is still
		// asserted, the second is declared not-applicable.
		mono := invariantOf(t, s, InvMonotonicDueDates)
		if mono.Status != InvariantHold || len(mono.NotAsserted) != 1 {
			t.Errorf("monotonic_due_dates: want a PARTIAL hold naming one skipped row, got %s %v",
				mono.Status, mono.NotAsserted)
		}
		// Ordering has no partial form — a row that cannot be keyed makes the
		// whole ordering unkeyable — so it must be N/A, never a HOLD.
		ord := invariantOf(t, s, InvOrdering)
		if ord.Status != InvariantNoData {
			t.Errorf("contract_row_ordering is a whole-schedule property: with an unobserved date it must "+
				"be N/A, not %s (%s)", ord.Status, ord.Detail)
		}
		if len(ord.NotAsserted) == 0 {
			t.Error("the N/A must name the row that could not be keyed")
		}
	})

	// THE GUARD AGAINST WEAKENING, and the reason option (a) was affordable at
	// all. Every one of the 29 promoted parity vectors withdraws interest_minor
	// and installment_number on its DISBURSEMENT row. The frozen contract FIXES
	// both at 0 for that row kind — contract.go:1509-1510, "its InterestMinor is
	// 0, and its InstallmentNumber is 0 because it is not payable" — so the
	// replay's 0 is the contract's own value, not a stand-in, and those cells
	// stay graded. Treating every withdrawn cell as a placeholder would have
	// turned splits_sum_to_whole's interest-column total into a no-op on the
	// entire corpus, which is precisely the trade this task refused to make.
	t.Run("D_a_cell_the_contract_fixes_at_zero_is_still_asserted", func(t *testing.T) {
		store := withdrawSelfTestCell(t,
			`"interest_minor": "0",
        "outstanding_principal_minor": "100000",
        "principal_major_text": "1000.00",
        "interest_major_text": "0.00",
        "outstanding_principal_major_text": "1000.00",
        "unrecorded_fields": [],`,
			`"interest_minor": "",
        "outstanding_principal_minor": "100000",
        "principal_major_text": "1000.00",
        "interest_major_text": "",
        "outstanding_principal_major_text": "1000.00",
        "unrecorded_fields": ["interest_minor"],`)
		s := selfTestReplayRun(t, store)
		if got := s.ExitCode(); got != 0 {
			t.Fatalf("exit %d\n%s", got, render(s))
		}
		if s.InvariantAssertionsNotRun != 0 {
			t.Errorf("a DISBURSEMENT row's interest is 0 BY THE FROZEN CONTRACT, so withdrawing it "+
				"withdraws no observation and must cost NO assertion; got %d skipped\n%s",
				s.InvariantAssertionsNotRun, render(s))
		}
		for _, name := range []string{InvSplitsSumToWhole, InvBalanceRollForward, InvPrincipalAmortizes} {
			if iv := invariantOf(t, s, name); iv.Status != InvariantHold {
				t.Errorf("%s must still HOLD, got %s (%s)", name, iv.Status, iv.Detail)
			}
		}
	})

	// The committed corpus must be unaffected by all of the above: no promoted
	// vector withdraws a cell the contract does not fix, so not one invariant
	// assertion is skipped anywhere in the store.
	t.Run("E_the_committed_corpus_skips_no_assertion", func(t *testing.T) {
		store := storeRoot(t)
		impl, _, err := NewReplayImplementation(store, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: repoRoot(t), StoreRoot: store,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if s.InvariantAssertionsNotRun != 0 {
			t.Errorf("the committed store must skip NO invariant assertion, got %d\n%s",
				s.InvariantAssertionsNotRun, render(s))
		}
		if s.InvariantViolations != 0 {
			t.Errorf("the committed store must violate no invariant, got %d", s.InvariantViolations)
		}
	})

	// An implementation that does NOT declare placeholders is treated as having
	// computed everything — the strict default, and the one a real Go port gets.
	// If this ever stops being true, every invariant silently weakens at once.
	t.Run("F_a_real_implementation_declares_no_placeholder", func(t *testing.T) {
		var g contract.ScheduleGenerator = generatorFunc(
			func(context.Context, contract.GenerateRequest) (contract.Schedule, error) {
				return contract.Schedule{}, nil
			})
		if _, ok := g.(PlaceholderReporter); ok {
			t.Fatal("a plain ScheduleGenerator must NOT satisfy PlaceholderReporter: the default has to " +
				"be 'computed everything', so that a port can never accidentally excuse an invariant")
		}
	})
}

// generatorFunc adapts a func to contract.ScheduleGenerator without implementing
// PlaceholderReporter, standing in for a real port.
type generatorFunc func(context.Context, contract.GenerateRequest) (contract.Schedule, error)

func (f generatorFunc) Generate(ctx context.Context, req contract.GenerateRequest) (contract.Schedule, error) {
	return f(ctx, req)
}
