package conformance

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
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
		"counterfactuals named by admissible vectors: 3  (1 money kills, 2 structural kills)",
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
