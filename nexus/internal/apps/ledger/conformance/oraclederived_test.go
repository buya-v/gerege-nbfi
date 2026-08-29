package conformance

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// THE DRIVES FOR THE ORACLE-DERIVED COLUMN DECLARATION  [T429, G-22]
//
// A guard nobody has watched fail enforces nothing (P-45), and a control that
// cannot fail and one that refuses everything are the same defect (P-98). Every
// arm of the declaration is therefore driven RED here, and the GREEN control
// asserts the committed declaration still classifies every cell the comparator
// really emits.
//
// THE FIXTURE FOR THE CAPTURE ARM IS A REAL ORACLE RESPONSE, NOT A HAND-WRITTEN
// ONE. `.softhouse/capture/t429-oracle-derived-columns/out/T429-G02-je78-runningbalance.json`
// is the body the live reference oracle returned for
// `GET /journalentries/78?runningBalance=true` on 2026-08-29, captured by a
// GET-only rig. Its sibling `T429-G01-je78-default.json` is the SAME entry
// without the parameter. The pair is what makes the rule checkable at all: the
// three field names are in one body and in neither the other nor any other
// capture in this corpus.

const (
	t429CaptureWithParam    = ".softhouse/capture/t429-oracle-derived-columns/out/T429-G02-je78-runningbalance.json"
	t429CaptureWithoutParam = ".softhouse/capture/t429-oracle-derived-columns/out/T429-G01-je78-default.json"
)

func loadDeclaration(t *testing.T) *OracleDerivedRegistry {
	t.Helper()
	r, err := LoadOracleDerivedRegistry(filepath.Join(storeRoot(t), OracleDerivedFileName))
	if err != nil {
		t.Fatalf("the committed oracle-derived declaration does not load: %v", err)
	}
	return r
}

// mutateDeclaration writes the committed declaration to a temp dir with one
// textual perturbation applied, and returns the path. It FAILS LOUDLY if the
// text to replace is absent, so a drive cannot silently become a no-op.
func mutateDeclaration(t *testing.T, old, new string) string {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(storeRoot(t), OracleDerivedFileName))
	if err != nil {
		t.Fatalf("reading the declaration: %v", err)
	}
	if !strings.Contains(string(raw), old) {
		t.Fatalf("the perturbation text %q is NOT in the committed declaration, so this drive would "+
			"test nothing. The fixture has moved and the drive must move with it", old)
	}
	out := strings.Replace(string(raw), old, new, 1)
	p := filepath.Join(t.TempDir(), OracleDerivedFileName)
	if err := os.WriteFile(p, []byte(out), 0o644); err != nil {
		t.Fatalf("writing the mutated declaration: %v", err)
	}
	return p
}

// ---------------------------------------------------------------------------
// THE GREEN CONTROL
// ---------------------------------------------------------------------------

// TestCommittedDeclarationLoadsAndClassifiesEveryMeasuredCell is the control
// half of P-98: the healthy declaration must still account for EVERY cell the
// comparator emits, and the account must be non-empty.
func TestCommittedDeclarationLoadsAndClassifiesEveryMeasuredCell(t *testing.T) {
	r := loadDeclaration(t)

	measured := CellFields()
	if len(measured) == 0 {
		t.Fatal("the comparator emits ZERO cells, so every assertion here would hold over nothing (P-35)")
	}
	declared := map[string]bool{}
	for _, c := range r.GradedCells {
		declared[c.Cell] = true
	}
	for _, c := range measured {
		if !declared[c] {
			t.Errorf("the comparator emits %q and the declaration does not classify it", c)
		}
	}
	if len(r.GradedCells) != len(measured) {
		t.Errorf("declaration classifies %d cells, comparator emits %d", len(r.GradedCells), len(measured))
	}

	// THE MONEY CELL IS STILL GRADED. This is the assertion the whole task turns
	// on: nothing in T429 may move a money column out of the graded set.
	found := false
	for _, tb := range r.Tables {
		for _, c := range tb.Columns {
			if c.Column != "amount" {
				continue
			}
			found = true
			if c.Disposition != DispositionGraded {
				t.Fatalf("acc_gl_journal_entry.amount is declared %q, want GRADED", c.Disposition)
			}
			if c.GradedCell != "legs[].amount_minor" {
				t.Fatalf("amount is graded by %q, want legs[].amount_minor", c.GradedCell)
			}
		}
	}
	if !found {
		t.Fatal("the declaration does not mention acc_gl_journal_entry.amount at all")
	}

	if len(r.OracleDerivedColumnsOf()) != OracleDerivedColumnPin {
		t.Errorf("declares %d oracle-derived columns, pinned %d",
			len(r.OracleDerivedColumnsOf()), OracleDerivedColumnPin)
	}
	if len(r.ForbiddenCellNames()) == 0 {
		t.Error("the declaration forbids NO cell spellings, so the disjointness arm cannot fail")
	}
}

// TestHealthyCorpusIsAdmissibleUnderTheCaptureRule is the other half of the
// control: the rule must not refuse the corpus it was written for. A guard that
// refuses everything is as useless as one that refuses nothing.
func TestHealthyCorpusIsAdmissibleUnderTheCaptureRule(t *testing.T) {
	r := loadDeclaration(t)
	vs, _, err := LoadStore(storeRoot(t), "")
	if err != nil {
		t.Fatalf("LoadStore: %v", err)
	}
	if len(vs) == 0 {
		t.Fatal("ZERO ledger vectors, so this control passes over nothing (P-35)")
	}
	scanned, unreadable := 0, 0
	for _, v := range vs {
		if reasons := r.CaptureRuleReasons(repoRoot(t), v); len(reasons) > 0 {
			t.Errorf("%s is refused by the capture rule on the committed corpus: %v", v.CaseID, reasons)
		}
		for _, sc := range r.ScanCaptureRule(repoRoot(t), v) {
			switch sc.Outcome {
			case CaptureScanClean:
				scanned++
			case CaptureScanUnreadable:
				unreadable++
			}
		}
	}
	// ANTI-VACUITY: the rule must actually have READ something. A corpus in which
	// every citation is unreadable would produce zero refusals for the wrong
	// reason, and this test would be green over a check that never ran.
	if scanned == 0 {
		t.Fatalf("the capture rule read ZERO artefacts (%d unreadable). It cannot have passed; it did "+
			"not run", unreadable)
	}
	t.Logf("capture rule coverage on the committed corpus: scanned %d, unreadable %d", scanned, unreadable)
}

// ---------------------------------------------------------------------------
// RED DRIVE 1 — a vector captured WITH the forbidden parameter is INADMISSIBLE
// ---------------------------------------------------------------------------

func TestVectorCapturedWithRunningBalanceParameterIsRefused(t *testing.T) {
	r := loadDeclaration(t)
	root := repoRoot(t)

	// THE FIXTURE IS A REAL ORACLE BODY. Assert both directions of the pair
	// FIRST, because the drive is only meaningful if the two captures actually
	// differ in the way the rule assumes.
	with, err := os.ReadFile(filepath.Join(root, t429CaptureWithParam))
	if err != nil {
		t.Fatalf("the with-parameter fixture is missing: %v", err)
	}
	without, err := os.ReadFile(filepath.Join(root, t429CaptureWithoutParam))
	if err != nil {
		t.Fatalf("the without-parameter fixture is missing: %v", err)
	}
	for _, f := range r.CaptureRule.ForbiddenFieldNames {
		if !strings.Contains(string(with), f) {
			t.Fatalf("the ?runningBalance=true capture does NOT carry %q, so the fixture does not "+
				"demonstrate what the rule scans for", f)
		}
		if strings.Contains(string(without), f) {
			t.Fatalf("the DEFAULT capture carries %q, so presence of that field is not evidence the "+
				"parameter was set and the whole rule is unsound", f)
		}
	}

	refused := &Vector{CaseID: "T429-DRIVE-forbidden-capture",
		Provenance: Provenance{CaptureRef: t429CaptureWithParam}}
	reasons := r.CaptureRuleReasons(root, refused)
	if len(reasons) == 0 {
		t.Fatal("a vector citing a capture taken with ?runningBalance=true was NOT refused. A2-29 §6.1 " +
			"forbids exactly that capture and this is the arm that enforces it")
	}
	if !strings.Contains(strings.Join(reasons, " "), "organizationRunningBalance") {
		t.Errorf("the refusal does not name the field it found: %v", reasons)
	}

	// AND THE CONTROL, in the same test so the pair cannot drift apart: the same
	// entry captured WITHOUT the parameter is admissible.
	clean := &Vector{CaseID: "T429-DRIVE-clean-capture",
		Provenance: Provenance{CaptureRef: t429CaptureWithoutParam}}
	if reasons := r.CaptureRuleReasons(root, clean); len(reasons) != 0 {
		t.Fatalf("the SAME journal entry captured WITHOUT the parameter was refused: %v. A rule that "+
			"refuses a clean capture refuses everything, which is the same defect as refusing "+
			"nothing (P-98)", reasons)
	}
}

// TestUnreadableCitationIsReportedAndNotCountedClean guards the third state.
func TestUnreadableCitationIsReportedAndNotCountedClean(t *testing.T) {
	r := loadDeclaration(t)
	v := &Vector{CaseID: "T429-DRIVE-unreadable",
		Provenance: Provenance{CaptureRef: "A2-347-je-manual-readback.json"}}
	scans := r.ScanCaptureRule(repoRoot(t), v)
	if len(scans) != 1 {
		t.Fatalf("expected one scan, got %d", len(scans))
	}
	if scans[0].Outcome != CaptureScanUnreadable {
		t.Fatalf("a file-name-only citation scanned as %v, want CaptureScanUnreadable. Counting it "+
			"CLEAN would report a check that never ran as one that passed", scans[0].Outcome)
	}
	// It must NOT be a refusal either: the citation mode is a separate, already
	// pinned concern and this rule may not double-refuse it.
	if reasons := r.CaptureRuleReasons(repoRoot(t), v); len(reasons) != 0 {
		t.Fatalf("an unreadable citation produced a capture-rule refusal: %v", reasons)
	}
}

// ---------------------------------------------------------------------------
// RED DRIVE 2 — a MONEY column may not be moved out of the graded domain
// ---------------------------------------------------------------------------

// TestMoneyColumnCannotBeDeclaredOracleDerived is the arm that exists because
// the brief said, in terms: "If your reasoning would exempt a money column,
// stop: that is the failure this task exists to prevent, not a result."
//
// IT IS DRIVEN THROUGH THE JSON, which is the surface a later author would
// actually edit. The protection lives in Go, so the JSON edit does not take.
func TestMoneyColumnCannotBeDeclaredOracleDerived(t *testing.T) {
	for _, tc := range []struct{ name, col, disposition string }{
		{"amount as ORACLE_DERIVED", "amount", DispositionOracleDerived},
		{"amount as PROVENANCE", "amount", DispositionProvenance},
		{"account_id as ORACLE_DERIVED", "account_id", DispositionOracleDerived},
		{"type_enum as PROVENANCE", "type_enum", DispositionProvenance},
		{"transaction_id as ORACLE_DERIVED", "transaction_id", DispositionOracleDerived},
		{"reversed as PROVENANCE", "reversed", DispositionProvenance},
	} {
		t.Run(tc.name, func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join(storeRoot(t), OracleDerivedFileName))
			if err != nil {
				t.Fatalf("reading the declaration: %v", err)
			}
			var doc map[string]any
			if err := json.Unmarshal(raw, &doc); err != nil {
				t.Fatalf("unmarshal: %v", err)
			}
			tables := doc["tables"].([]any)
			cols := tables[0].(map[string]any)["columns"].([]any)
			hit := false
			for _, c := range cols {
				m := c.(map[string]any)
				if m["column"] != tc.col {
					continue
				}
				hit = true
				m["disposition"] = tc.disposition
				m["why"] = "injected by the T429 drive"
				delete(m, "graded_cell")
				delete(m, "why_no_cell_yet")
				if tc.disposition == DispositionOracleDerived {
					m["written_by"] = "injected"
					m["forbidden_cells"] = []any{"injected_cell_name_that_nothing_emits"}
				}
			}
			if !hit {
				t.Fatalf("column %q is not in the declaration, so this drive tests nothing", tc.col)
			}
			out, err := json.Marshal(doc)
			if err != nil {
				t.Fatalf("marshal: %v", err)
			}
			p := filepath.Join(t.TempDir(), OracleDerivedFileName)
			if err := os.WriteFile(p, out, 0o644); err != nil {
				t.Fatalf("write: %v", err)
			}
			_, lerr := LoadOracleDerivedRegistry(p)
			if lerr == nil {
				t.Fatalf("MOVING %q OUT OF THE GRADED DOMAIN BY EDITING THE JSON WAS ACCEPTED. Money "+
					"and structure are graded, ALWAYS; the protected set is hard-coded in "+
					"oraclederived.go precisely so a JSON edit cannot reach it", tc.col)
			}
			if !strings.Contains(lerr.Error(), "MONEY AND STRUCTURE ARE") {
				t.Errorf("the refusal does not say WHY: %v", lerr)
			}
		})
	}
}

// ---------------------------------------------------------------------------
// RED DRIVE 3 — the comparator growing a running-balance cell must REFUSE
// ---------------------------------------------------------------------------

// TestGradingAnOracleDerivedColumnRefusesTheRun is the arm that catches outcome
// (2) of the three the declaration exists to close: somebody "fixes" the port to
// write balances so a bar goes green.
//
// IT IS DRIVEN FROM THE MEASUREMENT SIDE. The comparator's vocabulary is not
// declared anywhere a test can edit, so the drive names an EXISTING measured
// cell as forbidden — which is exactly the state that would obtain if a
// running-balance cell were added and the declaration still forbade it. The
// check is disjointness, and this makes the two sets intersect.
func TestGradingAnOracleDerivedColumnRefusesTheRun(t *testing.T) {
	measured := CellFields()
	if len(measured) == 0 {
		t.Fatal("the comparator emits no cells; this drive would be vacuous")
	}
	victim := "legs[].amount_minor"
	found := false
	for _, c := range measured {
		if c == victim {
			found = true
		}
	}
	if !found {
		t.Fatalf("%q is no longer a measured cell; the drive must be re-aimed", victim)
	}

	p := mutateDeclaration(t,
		`"forbidden_cells": ["organization_running_balance", "organizationRunningBalance"`,
		`"forbidden_cells": ["`+victim+`", "organization_running_balance", "organizationRunningBalance"`)
	_, err := LoadOracleDerivedRegistry(p)
	if err == nil {
		t.Fatal("the declaration forbade a cell THE COMPARATOR EMITS and the run was NOT refused. " +
			"That is the state where somebody has started grading a column this program's " +
			"non-negotiables say the port must never write, and it must be exit 2")
	}
	if !strings.Contains(err.Error(), "THE COMPARATOR NOW EMITS CELL") {
		t.Errorf("the refusal does not name the collision: %v", err)
	}
}

// TestDeclaringACellTheComparatorDoesNotEmitRefuses is the inflation direction.
func TestDeclaringACellTheComparatorDoesNotEmitRefuses(t *testing.T) {
	p := mutateDeclaration(t,
		`{ "cell": "leg_count",`,
		`{ "cell": "legs[].organization_running_balance_minor", "grades": "a cell nothing compares" },
    { "cell": "leg_count",`)
	_, err := LoadOracleDerivedRegistry(p)
	if err == nil {
		t.Fatal("a declared graded cell that the comparator does not emit was ACCEPTED. A claim of " +
			"coverage with no comparison behind it is exactly the control that cannot fail (P-98)")
	}
}

// TestDroppingAMeasuredCellFromTheDeclarationRefuses is the deflation
// direction — the half that keeps this from becoming a rubber stamp.
func TestDroppingAMeasuredCellFromTheDeclarationRefuses(t *testing.T) {
	p := mutateDeclaration(t,
		`    { "cell": "legs[].amount_minor",         "grades": "acc_gl_journal_entry.amount, as an integer count of minor units" },
`, "")
	_, err := LoadOracleDerivedRegistry(p)
	if err == nil {
		t.Fatal("the declaration dropped a cell the comparator EMITS and was accepted. A new graded " +
			"cell must be classified before it is graded, and an unclassified one is an undeclared " +
			"region of the report")
	}
	if !strings.Contains(err.Error(), "MUST BE CLASSIFIED BEFORE IT IS GRADED") {
		t.Errorf("the refusal does not explain itself: %v", err)
	}
}

// TestPopulationPinsRefuseInBothDirections drives the counts.
func TestPopulationPinsRefuseInBothDirections(t *testing.T) {
	// DEFLATION: remove an ORACLE_DERIVED column entirely.
	p := mutateDeclaration(t, `        { "column": "office_running_balance", "disposition": "ORACLE_DERIVED"`,
		`        { "column": "office_running_balance", "disposition": "GRADED_GAP", "why_no_cell_yet": "injected"`)
	if _, err := LoadOracleDerivedRegistry(p); err == nil {
		t.Fatal("an ORACLE_DERIVED column was reclassified away and the pin did not move; a carve-out " +
			"can therefore shrink in silence")
	}
	// INFLATION: widen the carve-out by moving a free-text column into it.
	p = mutateDeclaration(t,
		`{ "column": "description", "disposition": "GRADED_GAP", "why_no_cell_yet": "Free text. Not money and not structure, but NOT exempt either: an oracle-authored comment is reproducible and could be graded." }`,
		`{ "column": "description", "disposition": "ORACLE_DERIVED", "why": "injected", "written_by": "injected", "forbidden_cells": ["injected_cell"] }`)
	if _, err := LoadOracleDerivedRegistry(p); err == nil {
		t.Fatal("the carve-out was WIDENED by one column and the run was not refused. Widening must " +
			"be a source edit a reviewer sees, never a JSON edit nobody does")
	}
}

// TestEveryDeclaredTableClassifiesEveryColumnItClaims closes the silent-skip
// hole: a table that declares 31 columns and lists 30 is silent about one.
func TestEveryDeclaredTableClassifiesEveryColumnItClaims(t *testing.T) {
	p := mutateDeclaration(t, `"column_count_observed": 31`, `"column_count_observed": 40`)
	if _, err := LoadOracleDerivedRegistry(p); err == nil {
		t.Fatal("a table declaring more columns than it classifies was accepted, so the declaration " +
			"can be silent about a column while looking complete")
	}
}

// TestOracleDerivedRowMustNameItsWriter — the carve-out rests entirely on the
// oracle writing the column out of band. A row that cannot say what writes it
// has not established the claim it is making.
func TestOracleDerivedRowMustNameItsWriter(t *testing.T) {
	r := loadDeclaration(t)
	for _, d := range r.OracleDerivedColumnsOf() {
		if strings.TrimSpace(d.Col.WrittenBy) == "" {
			t.Errorf("%s.%s is ORACLE_DERIVED and names no writer", d.Table, d.Col.Column)
		}
		if !strings.Contains(d.Col.WrittenBy, "job 9") {
			t.Errorf("%s.%s names writer %q, which does not mention job 9. Every column in this "+
				"carve-out was measured to move under 'Update Accounting Running Balances'; a row "+
				"attributed to something else needs its own evidence",
				d.Table, d.Col.Column, d.Col.WrittenBy)
		}
	}
}

// TestTheBlockIsRenderedEvenWithNoDeclaration guards outcome (3): the carve-out
// going unprinted is indistinguishable from there being none.
func TestTheBlockIsRenderedEvenWithNoDeclaration(t *testing.T) {
	empty := &Summary{}
	lines := empty.OracleDerivedLines()
	if len(lines) == 0 {
		t.Fatal("a summary with no declaration rendered NOTHING. Silence there restores exactly the " +
			"undeclared-ungraded-region state this file exists to remove")
	}
	joined := strings.Join(lines, "\n")
	if !strings.Contains(joined, "UNDECLARED UNGRADED REGION") {
		t.Errorf("the absent-declaration block does not say what its absence means:\n%s", joined)
	}

	full := &Summary{OracleDerived: loadDeclaration(t)}
	lines = full.OracleDerivedLines()
	joined = strings.Join(lines, "\n")
	for _, must := range []string{
		"organization_running_balance",
		"office_running_balance",
		"is_running_balance_calculated",
		"MONEY AND STRUCTURE ARE GRADED, ALWAYS",
		"GRADED_GAP",
		"A2-29",
	} {
		if !strings.Contains(joined, must) {
			t.Errorf("the rendered block does not mention %q:\n%s", must, joined)
		}
	}
}
