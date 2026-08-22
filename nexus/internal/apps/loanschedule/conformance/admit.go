package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// Pin is the store-level pin file: the one place the corpus's comparability
// constants live, so that re-stamping the corpus after a ratified amendment is
// one edit rather than N.
type Pin struct {
	Schema string `json:"schema"`
	Note   string `json:"note"`

	// FineractCommit is the pinned reference-oracle commit every parity capture
	// must have been taken against. A capture from another build is not
	// comparable, whatever it says about itself.
	FineractCommit string `json:"fineract_commit"`

	// DEC1Revision is the ratified contract revision the corpus is expressed in.
	DEC1Revision int `json:"dec1_revision"`

	// ContractFile and ContractSHA256 pin the exact bytes of the frozen contract.
	//
	// The contract's package comment says its doc comments ARE the specification
	// and that "a shape change invalidates the conformance corpus". A digest is
	// therefore not pedantry: it is the mechanical form of that sentence. If the
	// frozen file changes at all, every vector in the store stops being known to
	// be expressed in the ratified shape, and the harness says so instead of
	// grading on.
	ContractFile   string `json:"contract_file"`
	ContractSHA256 string `json:"contract_sha256"`

	// ProductionRounding is the ratified tenant setting a parity vector must
	// have been captured at.
	ProductionRounding Rounding `json:"production_rounding"`

	// NeverPromotable lists capture case ids that are known probes or
	// calibrations and must never appear as a parity vector's capture_case_id,
	// whatever the file claims. It is a belt-and-braces denylist ON TOP of the
	// mechanical precision check, because a probe's identity is a fact worth
	// recording once rather than re-deriving.
	NeverPromotable []string `json:"never_promotable_capture_case_ids"`
}

// LoadPin reads the store pin file.
func LoadPin(path string) (*Pin, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	var p Pin
	if err := strictDecode(raw, &p); err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	if p.Schema != "gerege.loanschedule.pin/v1" {
		return nil, fmt.Errorf("store pin: schema %q unrecognised", p.Schema)
	}
	return &p, nil
}

// VerifyContractDigest checks the frozen contract file's bytes against the pin.
//
// The check deliberately reads the file as bytes and says nothing about
// formatting. In particular the harness NEVER runs gofmt over that path: gate
// G-3 records that `gofmt -l` reports contract.go, that the diff is
// doc-comment list normalisation, that it is semantically inert, and that it is
// deliberately NOT applied to a ratified artefact. Reformatting it would change
// this digest and, far worse, would be an unauthorised edit to the specification.
func VerifyContractDigest(repoRoot string, pin *Pin) error {
	path := filepath.Join(repoRoot, pin.ContractFile)
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("frozen contract: %w", err)
	}
	sum := sha256.Sum256(raw)
	got := hex.EncodeToString(sum[:])
	if got != pin.ContractSHA256 {
		return fmt.Errorf(
			"frozen contract %s digest %s does not match the store pin %s: the corpus is expressed in the "+
				"ratified DEC-1 shape and a change to that shape invalidates it. This is not a harness bug to "+
				"work around — either the edit needs a gate, or the corpus needs re-validating and the pin "+
				"re-stamping",
			pin.ContractFile, got, pin.ContractSHA256)
	}
	return nil
}

// Admit decides whether a vector may be graded at all, and by which rules.
//
// An INADMISSIBLE vector is never a FAIL and never a skip. It means the harness
// cannot make any statement about the implementation from this file, which is a
// defect in the corpus and makes the whole run untrustworthy.
func Admit(v *Vector, pin *Pin, repoRoot string) []string {
	var problems []string
	bad := func(format string, args ...any) {
		problems = append(problems, fmt.Sprintf(format, args...))
	}

	if v.Schema != VectorSchemaV1 {
		bad("schema %q, want %q", v.Schema, VectorSchemaV1)
	}
	if v.CaseID == "" {
		bad("case_id is empty")
	}
	if v.Context == "" {
		bad("context is empty")
	}
	dirOfFile := filepath.Dir(v.Path)
	if v.Context != dirOfFile {
		bad("context %q does not match the directory %q the file lives in", v.Context, dirOfFile)
	}
	// THE CONTEXT ALLOWLIST (A2-19 F1, re-measured by A2-20).
	//
	// The two checks above are jointly satisfiable by a file copy: `cp` a promoted
	// parity vector into a new directory, change `case_id` and `context` to the
	// new directory's name, and both pass — the context is non-empty and it does
	// equal the directory. The measured result on main's bytes was
	// `parity vectors PASS 44 FAIL 0`, `5711 cells`, exit 0, over a store whose
	// 44th vector was a loan schedule filed as `ledger`. See SchemaContexts() for
	// the full transcript and for why the refusal lives HERE.
	//
	// It is a refusal and not a warning for the reason at the head of this
	// function: the harness cannot make a statement about the implementation from
	// a file whose context is not one this schema grades, and a run containing one
	// is not a run whose numbers mean what they say.
	//
	// Guarded on non-empty so a vector with no context at all reports the one
	// precise defect it has, rather than that defect plus a derived echo of it.
	if v.Context != "" && !IsSchemaContext(v.Context) {
		bad("context %q is not a context this harness grades — %q accepts only %s. A vector "+
			"declaring an unknown context is INADMISSIBLE and not merely unmatched: the harness "+
			"would grade it by loanschedule rules against the loanschedule comparator while "+
			"reporting it under a heading that claims coverage of something else, which is how a "+
			"copied parity vector once raised the headline count to 44/5711. A second context "+
			"arrives as a second SCHEMA with its own comparator (DEC-2 §5.2), and it declares its "+
			"own contexts there — not by widening this list",
			v.Context, VectorSchemaV1, strings.Join(SchemaContexts(), ", "))
	}
	if v.DEC1Revision != pin.DEC1Revision {
		bad("dec1_revision %d, but the store is pinned to ratified revision %d",
			v.DEC1Revision, pin.DEC1Revision)
	}

	inSelfTestDir := dirOfFile == SelfTestDir

	// The class/directory/provenance lock. Both directions are checked, so
	// neither renaming a file nor relabelling a class can move a hand-authored
	// number into the parity corpus.
	switch v.Class {
	case ClassSelfTest:
		if !inSelfTestDir {
			bad("class %q must live under %s/ and this file is in %q", v.Class, SelfTestDir, dirOfFile)
		}
		if v.Provenance.Kind != ProvenanceHandAuthored {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceHandAuthored, v.Provenance.Kind)
		}
		if v.Provenance.Note != HandAuthoredNote {
			bad("class %q requires provenance.note to be exactly %q, got %q",
				v.Class, HandAuthoredNote, v.Provenance.Note)
		}
	case ClassParity:
		if inSelfTestDir {
			bad("a parity vector may not live under %s/: that directory is the hand-authored self-test area",
				SelfTestDir)
		}
		if v.Provenance.Kind != ProvenanceOracleCapture {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceOracleCapture, v.Provenance.Kind)
		}
		problems = append(problems, admitParityProvenance(v, pin, repoRoot)...)
	case ClassContractRefusal:
		if inSelfTestDir {
			bad("a contract-refusal vector may not live under %s/", SelfTestDir)
		}
		if v.Provenance.Kind != ProvenanceContract {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceContract, v.Provenance.Kind)
		}
		if strings.TrimSpace(v.Provenance.Citation) == "" {
			bad("class %q requires provenance.citation naming the ratified contract text that mandates the refusal",
				v.Class)
		}
		if v.Expect.Kind != "refusal" {
			bad("class %q requires expect.kind \"refusal\", got %q", v.Class, v.Expect.Kind)
		}
		if len(v.Expect.Periods) != 0 {
			bad("class %q must carry NO expected periods: it is derived from the contract, not observed, "+
				"so it may not contain a monetary value at all", v.Class)
		}
		if v.Oracle.Seam != "none" {
			bad("class %q requires oracle.seam \"none\": nothing was captured", v.Class)
		}
	default:
		bad("class %q is not one of %q, %q, %q", v.Class, ClassParity, ClassContractRefusal, ClassSelfTest)
	}
	if inSelfTestDir && v.Class != ClassSelfTest {
		bad("a file under %s/ may only carry class %q", SelfTestDir, ClassSelfTest)
	}

	switch v.Expect.Kind {
	case "schedule":
		if len(v.Expect.Periods) == 0 {
			bad("expect.kind \"schedule\" with no periods: there is nothing to compare")
		}
		if v.Expect.Sentinel != "" {
			bad("expect.kind \"schedule\" must not name a sentinel")
		}
	case "refusal":
		if _, err := sentinelByName(v.Expect.Sentinel); err != nil {
			bad("expect.sentinel: %v", err)
		}
	default:
		bad("expect.kind %q is neither \"schedule\" nor \"refusal\"", v.Expect.Kind)
	}

	// graded_against: the named counterfactuals this vector kills.
	if v.Class == ClassParity && len(v.GradedAgainst) == 0 {
		bad("a parity vector must carry at least one graded_against entry naming a WRONG " +
			"implementation it kills and the minor-unit margin. Gradeability is not a property of a " +
			"capture pair — LB-DEC31 reports zero cells differing across the day-count setting and still " +
			"kills a no-arm port by 6,015 minor units (finding T55-N1) — so a store that cannot name the " +
			"candidate defects a vector separates cannot express what it grades")
	}
	seenCF := map[string]bool{}
	for i, cf := range v.GradedAgainst {
		if strings.TrimSpace(cf.ID) == "" {
			bad("graded_against[%d] has no id", i)
		} else if seenCF[cf.ID] {
			bad("graded_against[%d] repeats counterfactual %q", i, cf.ID)
		}
		seenCF[cf.ID] = true
		if strings.TrimSpace(cf.Description) == "" {
			bad("graded_against[%d] (%s) has no description", i, cf.ID)
		}
		if strings.TrimSpace(cf.Evidence) == "" {
			bad("graded_against[%d] (%s) cites no evidence for its margin", i, cf.ID)
		}
		if cf.Capability == "" {
			bad("graded_against[%d] (%s) names no capability", i, cf.ID)
		} else if !containsString(v.CapabilitiesRequired, cf.Capability) {
			bad("graded_against[%d] (%s) grades capability %q, which is not in capabilities_required: "+
				"a vector cannot grade a capability it does not claim to exercise", i, cf.ID, cf.Capability)
		}
		problems = append(problems, admitCounterfactualKind(i, cf, v.Expect.Periods)...)
	}

	if v.RetiresWhenCapabilityGraded != "" && v.Class != ClassContractRefusal {
		bad("retires_when_capability_graded is only meaningful on a contract-refusal vector")
	}

	problems = append(problems, admitCorroborations(v)...)
	problems = append(problems, admitRequest(&v.Request)...)
	problems = append(problems, admitPeriods(v)...)
	// THE EXEMPTION CHECKS LIVE IN exemption.go (finding T220-N1). Two of them are
	// the ones that were always here — known invariant, non-empty reason — and the
	// third is the one that was missing: an exemption must be GROUNDED in a
	// violation the capture itself recorded, or it silences nothing and only moves
	// a count. See that file's head comment for why this is a refusal rather than
	// a report line.
	problems = append(problems, admitExemptions(v)...)
	return problems
}

// admitCounterfactualKind enforces the money/structural split (driver finding
// D-4).
//
// The structural form is STRICTLY HARDER to satisfy than the money form, and
// deliberately so. A money kill needs one number. A structural kill has no number
// — its margin is genuinely zero — so it must instead name every cell it diverges
// on, name only cells the harness actually compares, name no money column, and
// state both the wrong value and the observed one. If this ever becomes the easy
// path, it has been implemented wrongly: it exists so that P-02's due-date kill
// and P-03's row-order kill can be recorded HONESTLY, not so that a margin can be
// avoided.
//
// It takes the vector's own expected rows, not just their count, because finding
// T9-F1b showed that "names only cells the harness actually compares" was checked
// against the FIELD LIST and never against THIS VECTOR: a kill could name cells
// the same file had withdrawn from grading in unrecorded_fields.
func admitCounterfactualKind(i int, cf Counterfactual, periods []ExpectPeriod) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	switch cf.Kind {
	case "", CounterfactualMoney:
		margin, merr := cf.MarginMinor.Int64()
		switch {
		case merr != nil:
			bad("graded_against[%d] (%s) margin_minor: %v", i, cf.ID, merr)
		case margin <= 0:
			bad("graded_against[%d] (%s) margin_minor is %d: a candidate this vector separates by zero is "+
				"a candidate it does NOT kill, and recording one would reintroduce the false confidence "+
				"this field exists to remove. If the kill is real but moves no money — a wrong due date, a "+
				"wrong row order — it is a STRUCTURAL counterfactual: set kind %q, margin_minor \"0\", and "+
				"name the diverging cells in divergent_cells",
				i, cf.ID, margin, CounterfactualStructural)
		}
		if len(cf.DivergentCells) > 0 {
			bad("graded_against[%d] (%s) is a money counterfactual but lists divergent_cells %v: the money "+
				"form carries its kill in margin_minor. Naming cells here would let a reader think the "+
				"shape was graded too, when only the amount was", i, cf.ID, cf.DivergentCells)
		}

	case CounterfactualStructural:
		if string(cf.MarginMinor) != "0" {
			bad("graded_against[%d] (%s) is structural, so margin_minor must be exactly \"0\" and is %q: a "+
				"structural counterfactual moves NO money on this vector, and writing any other number "+
				"would be inventing a margin", i, cf.ID, cf.MarginMinor)
		}
		if len(cf.DivergentCells) == 0 {
			bad("graded_against[%d] (%s) is structural but names no divergent_cells. A structural kill has "+
				"no margin to carry its evidence, so it must name every cell it diverges on — "+
				"\"period[<n>].due_date\", \"period[<n>].from_date\", \"period[<n>].kind\" or %q — or it "+
				"claims a kill nothing can check", i, cf.ID, DivergentCellRowOrder)
		}
		seen := map[string]bool{}
		for j, cell := range cf.DivergentCells {
			if seen[cell] {
				bad("graded_against[%d] (%s) divergent_cells[%d] repeats %q", i, cf.ID, j, cell)
			}
			seen[cell] = true
			problems = append(problems, admitDivergentCell(i, cf.ID, j, cell, periods)...)
		}
		if !statesBothValues(cf.Evidence) {
			bad("graded_against[%d] (%s) is structural, so its evidence must state BOTH the value the "+
				"wrong implementation produces AND the value the oracle was observed to produce — a "+
				"structural kill has no number to carry that. The check is mechanical and crude: the "+
				"evidence must contain the word \"observed\" and one of \"instead\", \"rather than\", "+
				"\"wrong\" or \"emits\". Got: %q", i, cf.ID, cf.Evidence)
		}

	default:
		bad("graded_against[%d] (%s) kind %q is neither %q (the default when empty) nor %q",
			i, cf.ID, cf.Kind, CounterfactualMoney, CounterfactualStructural)
	}
	return problems
}

// admitDivergentCell checks one structural cell name.
func admitDivergentCell(i int, id string, j int, cell string, periods []ExpectPeriod) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }
	periodCount := len(periods)

	if cell == DivergentCellRowOrder {
		return nil
	}
	idx, field, form := ParseDivergentCell(cell)
	switch form {
	case DivergentCellNotACell:
		bad("graded_against[%d] (%s) divergent_cells[%d] %q is not a cell name: write "+
			"\"period[<n>].<field>\" or %q", i, id, j, cell, DivergentCellRowOrder)
		return problems
	case DivergentCellMalformed:
		bad("graded_against[%d] (%s) divergent_cells[%d] %q is malformed: write \"period[<n>].<field>\"",
			i, id, j, cell)
		return problems
	case DivergentCellBadIndex:
		bad("graded_against[%d] (%s) divergent_cells[%d] %q: the row index is not a canonical "+
			"non-negative integer", i, id, j, cell)
		return problems
	}
	if periodCount > 0 && idx >= periodCount {
		bad("graded_against[%d] (%s) divergent_cells[%d] %q names row %d, but this vector's expected "+
			"schedule has %d rows: a counterfactual cannot diverge on a cell that does not exist",
			i, id, j, cell, idx, periodCount)
	}
	if containsString(MoneyCellFields(), field) {
		bad("graded_against[%d] (%s) divergent_cells[%d] %q names a MONEY column. That is a money kill "+
			"wearing a structural label: record it as kind %q with the real margin_minor instead",
			i, id, j, cell, CounterfactualMoney)
		return problems
	}
	if !containsString(StructuralCellFields(), field) {
		bad("graded_against[%d] (%s) divergent_cells[%d] %q names field %q, which is not one of the "+
			"non-money cells this harness compares (%s). A cell the harness never compares cannot be the "+
			"site of a kill anything could detect",
			i, id, j, cell, field, strings.Join(StructuralCellFields(), ", "))
		return problems
	}

	// FINDING T9-F1b. The check above asks whether the harness compares this
	// field IN GENERAL. This one asks whether the vector compares it HERE.
	//
	// Both questions have to be asked, and only the first one was. A vector could
	// name period[2].due_date as the site of a structural kill while its own
	// expect.periods[2].unrecorded_fields withdrew due_date from grading — and
	// then report the capability as killed while grading none of the cells the
	// kill rests on. T9 did exactly that to all nine cells of
	// MONTHEND-CONTINUE-FROM-CLAMPED-DAY in P-02 and P-02b and still got 11/11
	// PASS at exit 0.
	//
	// A kill is a claim that a wrong implementation would be CAUGHT. A cell this
	// vector does not compare catches nothing, so naming it is not evidence, and
	// the store may not record it as though it were.
	if periodCount > 0 && idx < periodCount && containsString(periods[idx].UnrecordedFields, field) {
		bad("graded_against[%d] (%s) divergent_cells[%d] %q names a cell this vector's OWN "+
			"expect.periods[%d].unrecorded_fields WITHDRAWS from grading. A structural kill has no "+
			"margin to carry its evidence, so its whole claim is that these cells are compared — and "+
			"this one is not. Nothing would catch a port that got it wrong, yet the report would print "+
			"the capability as killed (finding T9-F1b). Either record the cell and grade it, or stop "+
			"claiming a kill that rests on it",
			i, id, j, cell, idx)
	}
	return problems
}

// DivergentCellForm is how ParseDivergentCell reports a cell name it could not
// resolve. There is one parser for divergent cell names in this harness and this
// is its vocabulary: two parsers that disagreed about what "period[2].due_date"
// means would be a defect of exactly the shape finding T9-F1b describes — one
// half of the harness policing a cell name the other half resolves differently.
type DivergentCellForm int

const (
	// DivergentCellWellFormed means idx and field are usable.
	DivergentCellWellFormed DivergentCellForm = iota
	// DivergentCellNotACell means the name has no "period[" prefix.
	DivergentCellNotACell
	// DivergentCellMalformed means the brackets or the "." are wrong.
	DivergentCellMalformed
	// DivergentCellBadIndex means the row index is not a canonical non-negative
	// integer.
	DivergentCellBadIndex
)

// ParseDivergentCell splits "period[<n>].<field>" into its row index and field.
//
// It does NOT range-check the index against any schedule and does not judge the
// field: those are policy, and policy belongs with the caller that has the vector
// in hand. DivergentCellRowOrder is not a per-row cell and is reported as
// DivergentCellNotACell; callers handle it before calling.
func ParseDivergentCell(cell string) (idx int, field string, form DivergentCellForm) {
	const prefix = "period["
	if !strings.HasPrefix(cell, prefix) {
		return 0, "", DivergentCellNotACell
	}
	rest := cell[len(prefix):]
	end := strings.IndexByte(rest, ']')
	if end < 0 || !strings.HasPrefix(rest[end:], "].") {
		return 0, "", DivergentCellMalformed
	}
	idxText, field := rest[:end], rest[end+2:]
	n, err := MinorText(idxText).Int64()
	if err != nil || n < 0 {
		return 0, "", DivergentCellBadIndex
	}
	return int(n), field, DivergentCellWellFormed
}

// statesBothValues is the crude mechanical test that a structural
// counterfactual's evidence names the wrong value and the observed one.
//
// It is prose matching and it knows it. The alternative was to leave the
// requirement as a sentence in a document, and a requirement nobody can fail is
// not a requirement. The error message names the exact words that satisfy it, so
// an author is never left guessing.
func statesBothValues(evidence string) bool {
	e := strings.ToLower(evidence)
	if !strings.Contains(e, "observed") {
		return false
	}
	for _, marker := range []string{"instead", "rather than", "wrong", "emits"} {
		if strings.Contains(e, marker) {
			return true
		}
	}
	return false
}

// admitCorroborations enforces finding T17-F2: a cross-check that covers part of
// a row may not be recorded as covering the row.
func admitCorroborations(v *Vector) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	for i, c := range v.Provenance.CorroboratedBy {
		src, ok := AttestationSourceByID(c.Source)
		if !ok {
			var known []string
			for _, s := range AttestationSources() {
				known = append(known, s.ID)
			}
			bad("provenance.corroborated_by[%d] cites source %q, which this harness does not know the "+
				"column coverage of (known: %s). A corroboration from an undeclared source is a claim the "+
				"harness cannot scope, and an unscoped corroboration is exactly what finding T17-F2 is "+
				"about", i, c.Source, strings.Join(known, ", "))
			continue
		}
		if _, err := periodKindByName(c.RowKind); err != nil {
			bad("provenance.corroborated_by[%d].row_kind: %v", i, err)
			continue
		}
		if len(src.ColumnsByRowKind[c.RowKind]) == 0 {
			bad("provenance.corroborated_by[%d]: source %q attests nothing at all about a %s row (it "+
				"attests: %s)", i, c.Source, c.RowKind, strings.Join(src.RowKinds(), ", "))
			continue
		}
		if len(c.Columns) == 0 {
			bad("provenance.corroborated_by[%d] claims no column: a corroboration that names no column "+
				"corroborates nothing", i)
		}
		for _, col := range c.Columns {
			if !IsPeriodColumn(col) {
				bad("provenance.corroborated_by[%d] claims column %q, which is not one of the ten period "+
					"columns (%s)", i, col, strings.Join(PeriodColumns(), ", "))
				continue
			}
			if !src.Attests(c.RowKind, col) {
				bad("provenance.corroborated_by[%d]: source %q DOES NOT ATTEST column %q on a %s row. It "+
					"attests %d of the %d period columns there (%s) and is silent on %s. A comparison "+
					"covering part of a row may not be recorded as covering the row — finding T17-F2. "+
					"Source: %s",
					i, c.Source, col, c.RowKind,
					len(src.ColumnsByRowKind[c.RowKind]), len(PeriodColumns()),
					strings.Join(src.ColumnsByRowKind[c.RowKind], ", "),
					strings.Join(src.Unattested(c.RowKind), ", "), src.Citation)
			}
		}
	}
	return problems
}

func admitParityProvenance(v *Vector, pin *Pin, repoRoot string) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	if v.Oracle.FineractCommit != pin.FineractCommit {
		bad("oracle.fineract_commit %q is not the pinned reference-oracle commit %q: a capture from a "+
			"different build is NOT COMPARABLE", v.Oracle.FineractCommit, pin.FineractCommit)
	}
	if v.Oracle.Seam == "" || v.Oracle.Seam == "none" {
		bad("a parity vector must name the capture seam it was observed through")
	}
	if v.Expect.Kind != "schedule" {
		bad("a parity vector must expect a schedule; a refusal is not an oracle observation")
	}

	// The structural probe guard. A capture taken at any MathContext other than
	// the ratified production setting is a DISCRIMINATION PROBE and can never be
	// a parity vector, because production never runs at that setting. The check
	// is on the RECORDED SETTINGS rather than on a label, so relabelling a probe
	// as parity cannot smuggle it in: the numbers themselves were produced at a
	// precision the check reads off the file.
	want := pin.ProductionRounding

	// The ambient context must be RECORDED, on every seam, before it is compared
	// to anything. Finding T17-F3, RESTATED — the original wording is refuted:
	//
	//   F3 as written asked C-00 to assert that MoneyHelper is NEVER statically
	//   initialised on the embeddable path. Capture pass 1's D-04 refutes it: with
	//   allowFullTermForTranche = true the embeddable path DID reach MoneyHelper
	//   and died with "No tenant context available. MoneyHelper requires a valid
	//   tenant context" (.softhouse/capture/PASS2-REPORT.md:34, MoneyHelper.java
	//   :178-179). The surviving, narrower claim is "not observed to be reached
	//   when the flag is FALSE" — which is a statement about the shapes captured,
	//   not a licence to leave the ambient MathContext unrecorded on a seam
	//   somebody believes never reads it.
	//
	// So an unrecorded ambient context is INADMISSIBLE for a parity vector, and
	// the message says why rather than reporting a bare mismatch against
	// production.
	if v.Oracle.AmbientMathContext == (MathContext{}) {
		bad("a parity vector must RECORD the ambient MathContext, and this one leaves it empty. Finding "+
			"T17-F3 as originally written — \"MoneyHelper is never statically initialised on the "+
			"embeddable path\" — is REFUTED BY OBSERVATION: capture pass 1's D-04 ran that path with "+
			"allowFullTermForTranche = true and died with \"No tenant context available. MoneyHelper "+
			"requires a valid tenant context\". The narrowed claim is only that the flag-FALSE branch is "+
			"not observed to reach it, and \"not observed in the shapes we captured\" is not "+
			"\"unreachable\": %s", claimText("T17-F3"))
	}
	if v.Oracle.ThreadedMathContext.Precision != want.SignificantDigits ||
		v.Oracle.ThreadedMathContext.RoundingMode != want.Mode {
		bad("threaded MathContext %s is not the ratified production setting (%d,%s): this is a "+
			"DISCRIMINATION PROBE, not a parity vector, and it may never be promoted as one",
			v.Oracle.ThreadedMathContext, want.SignificantDigits, want.Mode)
	}
	if v.Oracle.AmbientMathContext.Precision != want.SignificantDigits ||
		v.Oracle.AmbientMathContext.RoundingMode != want.Mode {
		bad("ambient MathContext %s is not the ratified production setting (%d,%s): which context scales a "+
			"value to currency precision is decided by the CONSTRUCTION, so an ambient setting that differs "+
			"from production makes the capture unrepresentative even when the threaded one matches",
			v.Oracle.AmbientMathContext, want.SignificantDigits, want.Mode)
	}
	if v.Request.Rounding.SignificantDigits != v.Oracle.ThreadedMathContext.Precision ||
		v.Request.Rounding.Mode != v.Oracle.ThreadedMathContext.RoundingMode {
		bad("request.rounding %s disagrees with the threaded MathContext %s the capture was taken at: "+
			"replaying a vector under a policy it was not captured at is meaningless",
			v.Request.Rounding, v.Oracle.ThreadedMathContext)
	}

	if v.Provenance.CaptureRef == "" {
		bad("a parity vector must cite provenance.capture_ref: the committed capture artefact its expected " +
			"values were transcribed from")
	} else {
		abs := filepath.Join(repoRoot, v.Provenance.CaptureRef)
		info, err := os.Stat(abs)
		switch {
		case err != nil:
			bad("provenance.capture_ref %q does not resolve to a file in this repository: %v",
				v.Provenance.CaptureRef, err)
		case info.IsDir():
			bad("provenance.capture_ref %q is a directory, not a capture artefact", v.Provenance.CaptureRef)
		case v.Provenance.CaptureSHA256 != "":
			raw, rerr := os.ReadFile(abs)
			if rerr != nil {
				bad("provenance.capture_ref %q unreadable: %v", v.Provenance.CaptureRef, rerr)
				break
			}
			sum := sha256.Sum256(raw)
			if got := hex.EncodeToString(sum[:]); got != v.Provenance.CaptureSHA256 {
				bad("provenance.capture_sha256 %s does not match the referenced capture (%s)",
					v.Provenance.CaptureSHA256, got)
			}
		}
	}
	if v.Provenance.CaptureCaseID == "" {
		bad("a parity vector must cite provenance.capture_case_id: a Path A capture file is a BUNDLE of " +
			"many cases and the file path alone does not identify the observation")
	}
	for _, denied := range pin.NeverPromotable {
		if v.Provenance.CaptureCaseID == denied {
			bad("capture case %q is on the store's never-promotable list (a probe or a rig calibration)", denied)
		}
	}
	return problems
}

func admitRequest(r *Request) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	if r.TimeZone == "" {
		bad("request.time_zone is empty")
	}
	if strings.ContainsAny(r.TimeZone, "+-") || strings.HasPrefix(r.TimeZone, "UTC") ||
		strings.HasPrefix(r.TimeZone, "GMT") {
		bad("request.time_zone %q looks like a fixed offset; the contract requires an IANA zone name", r.TimeZone)
	}
	if r.Currency.Code != strings.ToUpper(r.Currency.Code) {
		bad("request.currency.code %q must be upper case; the oracle's own fixture spells it lower case and "+
			"an adapter must not let that leak back out", r.Currency.Code)
	}
	if r.Currency.MinorUnitDigits < 0 {
		bad("request.currency.minor_unit_digits is negative")
	}
	if !r.ScheduleStartDate.Valid() {
		bad("request.schedule_start_date %s is not a real calendar date", r.ScheduleStartDate)
	}
	if len(r.Disbursements) == 0 {
		bad("request.disbursements is empty")
	}
	for i, d := range r.Disbursements {
		if !d.Date.Valid() {
			bad("request.disbursements[%d].date %s is not a real calendar date", i, d.Date)
		}
		amt, err := d.AmountMinor.Int64()
		if err != nil {
			bad("request.disbursements[%d].amount_minor: %v", i, err)
			continue
		}
		if amt <= 0 {
			bad("request.disbursements[%d].amount_minor must be > 0", i)
		}
	}
	if r.NumberOfRepayments < 1 {
		bad("request.number_of_repayments must be >= 1 (well-formedness, not a graded-domain predicate)")
	}
	if r.RepaymentEvery < 1 {
		bad("request.repayment_every must be >= 1")
	}
	if _, err := frequencyByName(r.RepaymentFrequencyUnit); err != nil {
		bad("request.repayment_frequency_unit: %v", err)
	}
	if _, err := dayCountByName(r.DayCount); err != nil {
		bad("request.day_count: %v", err)
	}
	if _, err := interestMethodByName(r.InterestMethod); err != nil {
		bad("request.interest_method: %v", err)
	}
	if _, err := roundingModeByName(r.Rounding.Mode); err != nil {
		bad("request.rounding.mode: %v", err)
	}
	problems = append(problems, admitRate("request.annual_nominal_interest_rate", r.AnnualNominalInterestRate)...)
	problems = append(problems, admitRate("request.down_payment_percentage", r.DownPaymentPercentage)...)
	if _, err := r.InstallmentRoundingMultipleMinor.Int64(); err != nil {
		bad("request.installment_rounding_multiple_minor: %v", err)
	}
	return problems
}

func admitRate(field string, r Rate) []string {
	var problems []string
	if r.Denominator <= 0 {
		problems = append(problems, fmt.Sprintf("%s: denominator must be > 0 (the Go zero value Rate{} is invalid)", field))
		return problems
	}
	if r.Numerator < 0 {
		problems = append(problems, fmt.Sprintf("%s: numerator must be >= 0", field))
	}
	if g := gcd(abs64(r.Numerator), r.Denominator); g != 1 {
		problems = append(problems, fmt.Sprintf(
			"%s: %s is not in lowest terms (gcd %d); canonical form is part of the contract so that one rate "+
				"has exactly one legal encoding", field, r, g))
	}
	return problems
}

func admitPeriods(v *Vector) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }
	digits := v.Request.Currency.MinorUnitDigits

	for i, p := range v.Expect.Periods {
		// unrecorded_fields is validated FIRST, because every check below has to
		// ask whether the cell it is about to inspect was withdrawn from grading.
		for _, f := range p.UnrecordedFields {
			if !unrecordablePeriodField(f) {
				bad("expect.periods[%d].unrecorded_fields names %q, which is not a cell a capture may "+
					"withdraw from grading. The withdrawable cells are exactly %s; %q is compared by "+
					"this harness and may never be withdrawn (finding T9-F1a)",
					i, f, strings.Join(UnrecordablePeriodFields(), ", "), f)
			}
		}
		recorded := func(field string) bool {
			for _, f := range p.UnrecordedFields {
				if f == field {
					return false
				}
			}
			return true
		}

		// kind is not withdrawable, so it is validated unconditionally.
		kind, kindErr := periodKindByName(p.Kind)
		if kindErr != nil {
			bad("expect.periods[%d].kind: %v", i, kindErr)
		}

		// FINDING T9-F1a, as a hard structural rule: "marked unrecorded means
		// EMPTY" now covers the NON-money cells too.
		//
		// Before this rule the check below existed only for the three money
		// columns, so from_date, due_date and installment_number could each be
		// simultaneously POPULATED and UNGRADED — a value in the file that
		// nothing compares. T9 demonstrated the consequence end to end: it wrote
		// 1999-01-01 into all nine cells that MONTHEND-CONTINUE-FROM-CLAMPED-DAY
		// names in P-02 and P-02b, withdrew every one of them, and the run still
		// reported "monthend.reanchor killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY"
		// and exited 0. A stored value nobody compares is indistinguishable from
		// an observation, which is the exact defect unrecorded_fields exists to
		// prevent — applied to the half of the row where the month-end capability
		// lives.
		//
		// For a date, EMPTY is the zero Date: absent from the JSON, or written as
		// {year:0, month:0, day:0}. Nothing else is a real calendar date anyway.
		for _, d := range []struct {
			field string
			date  Date
		}{
			{"from_date", p.FromDate},
			{"due_date", p.DueDate},
		} {
			if !recorded(d.field) {
				if d.date != (Date{}) {
					bad("expect.periods[%d].%s is marked unrecorded but carries the date %s. A cell "+
						"withdrawn from grading must be EMPTY: nothing compares it, so a value written "+
						"there is a claim no run can check and a later reader cannot tell it from an "+
						"observation (finding T9-F1a). Either record the date and grade it, or leave the "+
						"cell at the zero date", i, d.field, d.date)
				}
				continue
			}
			if !d.date.Valid() {
				bad("expect.periods[%d].%s %s is not a real calendar date", i, d.field, d.date)
			}
		}

		// installment_number, the one withdrawable cell whose Go type cannot tell
		// ABSENT from ZERO (finding T9-F1c). The documented sentinel for absent is
		// therefore 0 — the frozen contract's own value for a row that is not
		// payable (contract.go, Period.InstallmentNumber: "InstallmentNumber is 0
		// because it is not payable") — and the withdrawal is confined to exactly
		// the rows for which that sentence holds.
		//
		// So: a withdrawn installment_number must be 0, and only a DISBURSEMENT or
		// DOWN_PAYMENT row may withdraw it. A REPAYMENT row's installment number is
		// the dense 1..n sequence the contract mandates; it is never unobservable,
		// and letting one be withdrawn would reopen the hole this rule closes.
		if !recorded("installment_number") {
			if p.InstallmentNumber != 0 {
				bad("expect.periods[%d].installment_number is marked unrecorded but carries %d. The "+
					"sentinel for an unrecorded installment number is 0, because int32 cannot tell "+
					"absent from zero; any other value is a populated cell nothing compares "+
					"(finding T9-F1a/F1c)", i, p.InstallmentNumber)
			}
			if kindErr == nil && kind == contract.PeriodKindRepayment {
				bad("expect.periods[%d] is a REPAYMENT row and marks installment_number unrecorded. Only "+
					"a non-payable row (DISBURSEMENT, DOWN_PAYMENT) may withdraw it, because 0 is the "+
					"frozen contract's own value for exactly those rows and so stores no observation. A "+
					"repayment's installment number is the contract's dense 1..n sequence: it is always "+
					"determinable and withdrawing it would hide a real divergence (finding T9-F1a)", i)
			}
		}
		overScaled := map[string]bool{}
		for _, f := range p.OverScaledWireTextFields {
			if !containsString(MoneyCellFields(), f) {
				bad("expect.periods[%d].over_scaled_wire_text_fields names %q, which is not a money column "+
					"(%s): only a money column can be over-scaled, because only a money column has a "+
					"currency scale to exceed", i, f, strings.Join(MoneyCellFields(), ", "))
				continue
			}
			if overScaled[f] {
				bad("expect.periods[%d].over_scaled_wire_text_fields repeats %q", i, f)
			}
			overScaled[f] = true
		}
		problems = append(problems, admitRateFactor(i, p.ObservedRateFactor)...)
		type cell struct {
			field string
			minor MinorText
			text  string
		}
		cells := []cell{
			{"principal_minor", p.PrincipalMinor, p.PrincipalMajorText},
			{"interest_minor", p.InterestMinor, p.InterestMajorText},
			{"outstanding_principal_minor", p.OutstandingPrincipalMinor, p.OutstandingPrincipalMajorText},
		}
		anyRecorded := false
		for _, c := range cells {
			if !recorded(c.field) {
				if c.minor != "" || c.text != "" {
					bad("expect.periods[%d].%s is marked unrecorded but carries a value", i, c.field)
				}
				continue
			}
			anyRecorded = true
			got, err := c.minor.Int64()
			if err != nil {
				bad("expect.periods[%d].%s: %v", i, c.field, err)
				continue
			}
			if got < 0 {
				bad("expect.periods[%d].%s is negative; the contract carries direction in Kind, never a sign bit",
					i, c.field)
			}
			if c.text == "" {
				if overScaled[c.field] {
					bad("expect.periods[%d].%s is declared over-scaled but carries no wire text at all: "+
						"a declaration about characters nobody recorded is noise", i, c.field)
				}
				continue
			}

			// FINDING T17-F5, as a hard structural rule: a value with scale > the
			// currency's minor-unit digits routed into a money column is a HARNESS
			// BUG, not a rounding opportunity. The failure mode is a rig quietly
			// rounding an over-scaled value and thereby grading the port against a
			// number the oracle never produced.
			//
			// Non-zero excess digits are rejected by MinorFromMajorText below and
			// can never be admitted. All-zero excess digits convert EXACTLY, so
			// the value is usable — but only if the file says out loud that the
			// scale is wrong. Silence is what this rule removes.
			scale, serr := ScaleOfWireText(c.text)
			switch {
			case serr != nil:
				bad("expect.periods[%d].%s wire text: %v", i, c.field, serr)
			case scale > digits && !overScaled[c.field]:
				bad("expect.periods[%d].%s wire text %q has SCALE %d, above the currency's %d minor-unit "+
					"digits. A value with scale > %d routed to a money column is a harness bug, not a "+
					"rounding opportunity (finding T17-F5): a rig that rounded it would grade the port "+
					"against a number the oracle never produced. If the capture really emitted this scale "+
					"and the extra digits are all zero, the conversion is exact and the vector may keep it "+
					"— but it must SAY SO by naming %q in this row's over_scaled_wire_text_fields, so the "+
					"report can count it. If any extra digit is non-zero the value is an INTERMEDIATE that "+
					"escaped rounding and belongs in a decimal observation, never in a money column",
					i, c.field, c.text, scale, digits, digits, c.field)
			case scale <= digits && overScaled[c.field]:
				bad("expect.periods[%d].%s is declared over-scaled but its wire text %q has scale %d, "+
					"within the currency's %d minor-unit digits: a declaration that does not match the "+
					"text teaches a reader to ignore the declarations", i, c.field, c.text, scale, digits)
			}

			// The transcription cross-check: re-derive the integer from the
			// oracle's own emitted characters, by exact integer arithmetic.
			want, cerr := MinorFromMajorText(c.text, digits)
			if cerr != nil {
				bad("expect.periods[%d].%s wire text: %v", i, c.field, cerr)
				continue
			}
			if want != got {
				bad("expect.periods[%d].%s is %d minor units but the oracle's wire text %q converts to %d: "+
					"a transcription error, which no other check in this harness can see",
					i, c.field, got, c.text, want)
			}
		}
		if v.Class == ClassParity && !anyRecorded {
			bad("expect.periods[%d] records no monetary cell at all: it grades nothing", i)
		}
		if p.ObservedTotalDueMinor != nil {
			if _, err := p.ObservedTotalDueMinor.Int64(); err != nil {
				bad("expect.periods[%d].observed_total_due_minor: %v", i, err)
			}
		}
	}
	if v.Expect.ObservedTotalInterestMinor != nil {
		if _, err := v.Expect.ObservedTotalInterestMinor.Int64(); err != nil {
			bad("expect.observed_total_interest_minor: %v", err)
		}
	}
	if v.Expect.LastRepaymentDueDate != nil && !v.Expect.LastRepaymentDueDate.Valid() {
		bad("expect.last_repayment_due_date %s is not a real calendar date", v.Expect.LastRepaymentDueDate)
	}
	return problems
}

// admitRateFactor enforces finding T17-F6: a transcribed rate factor is a
// ROUNDING of the engine's value, so it may be recorded but never graded, and no
// vector may claim it is exact.
//
// The trap this closes: the corpus's rate factors were compared only after
// setScale(MoneyHelper precision, MoneyHelper rounding mode) with that precision
// mocked to 12, so a Go port diverging in digits 13 and beyond matches the
// transcription exactly. A harness that compared the field would be certifying
// twelve digits of a nineteen-digit quantity and printing a PASS.
func admitRateFactor(i int, rf *RateFactorObservation) []string {
	if rf == nil {
		return nil
	}
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	decl, declared := RoundedTranscriptionFor("rate_factor")
	if !declared {
		bad("expect.periods[%d].observed_rate_factor is recorded but this harness declares no rounded "+
			"transcription for \"rate_factor\": the rule that makes the field safe has been removed", i)
		return problems
	}
	if strings.TrimSpace(rf.Text) == "" {
		bad("expect.periods[%d].observed_rate_factor.text is empty", i)
	} else {
		scale, err := ScaleOfWireText(rf.Text)
		switch {
		case err != nil:
			bad("expect.periods[%d].observed_rate_factor.text: %v", i, err)
		case scale != rf.TranscribedAtScale:
			bad("expect.periods[%d].observed_rate_factor claims transcribed_at_scale %d but its text %q "+
				"carries %d fraction digits: a file may not claim more precision than it wrote down",
				i, rf.TranscribedAtScale, rf.Text, scale)
		case scale > decl.TranscribedScale:
			bad("expect.periods[%d].observed_rate_factor.text %q carries %d fraction digits, beyond the %d "+
				"the corpus's rate factors are rounded to (%s). Digits past the transcription scale were "+
				"not observed and may not be written down as though they were",
				i, rf.Text, scale, decl.TranscribedScale, decl.Citation)
		}
	}
	if rf.PrecisionStatus != PrecisionTranscribedRounded {
		bad("expect.periods[%d].observed_rate_factor.precision_status is %q; the only status this harness "+
			"accepts is %q. Exact rate-factor parity is %s from the oracle — %s. Recording a rate factor is "+
			"welcome; CLAIMING it is exact is a parity claim no capture in this corpus can support",
			i, rf.PrecisionStatus, PrecisionTranscribedRounded, decl.ParityStatus, decl.Trap)
	}
	if strings.TrimSpace(rf.Citation) == "" {
		bad("expect.periods[%d].observed_rate_factor cites no file:line: a transcription with no source is "+
			"indistinguishable from an invention", i)
	}
	return problems
}

func containsString(haystack []string, needle string) bool {
	for _, h := range haystack {
		if h == needle {
			return true
		}
	}
	return false
}

// UnrecordablePeriodFields are the per-row cells a capture may declare in
// unrecorded_fields — the cells for which "the capture did not record this" is a
// statement a capture can honestly make.
//
// `kind` is DELIBERATELY ABSENT, and its absence is a strengthening (finding
// T9-F1a). It used to be withdrawable and never should have been: the replay
// grader cannot even CONSTRUCT a row without a kind (registry.go resolves it with
// periodKindByName and hard-errors), every property invariant keys on it, row
// ordering is defined in terms of it, and no capture seam in this corpus omits
// it. A cell that cannot be absent must not be declarable absent — otherwise the
// declaration is a way to stop grading a cell that was in fact observed.
//
// Everything on this list carries a further "unrecorded means EMPTY" rule in
// admitPeriods. Being withdrawable is not permission to leave a value behind.
func UnrecordablePeriodFields() []string {
	return []string{
		"installment_number", "from_date", "due_date",
		"principal_minor", "interest_minor", "outstanding_principal_minor",
	}
}

func unrecordablePeriodField(f string) bool {
	return containsString(UnrecordablePeriodFields(), f)
}

// GradedDomain evaluates the GRADED DOMAIN predicate list from
// contract.GenerateRequest against a vector's request.
//
// One thing this function deliberately does NOT do: compute a due date. The last
// predicate ("ScheduleStartDate <= Disbursements[0].Date < the last repayment
// DueDate") needs the last repayment due date, and computing that would mean
// implementing the month-end stepping rule — which is the port's job (T10). A
// harness that contained a schedule generator would be one the port could borrow
// from, and the pipeline's independence is the whole reason the harness exists.
// So the last due date is READ from the vector: from the last repayment row of
// the expected schedule, or from expect.last_repayment_due_date on a refusal
// vector that has no schedule.
func GradedDomain(v *Vector) (bool, []string) {
	var out []string
	no := func(format string, args ...any) { out = append(out, fmt.Sprintf(format, args...)) }
	r := &v.Request

	if r.Currency.MinorUnitDigits != 2 {
		no("currency.minor_unit_digits is %d, graded domain requires 2 (at 0 a second rounding channel "+
			"switches on inside the oracle)", r.Currency.MinorUnitDigits)
	}
	if r.Rounding.SignificantDigits != 19 {
		no("rounding.significant_digits is %d, graded domain requires 19 (MoneyHelper.PRECISION is the "+
			"compile-time constant 19)", r.Rounding.SignificantDigits)
	}
	if r.Rounding.RateFactorScale != 19 {
		no("rounding.rate_factor_scale is %d, graded domain requires 19", r.Rounding.RateFactorScale)
	}
	if r.Rounding.Mode != "HALF_UP" {
		no("rounding.mode is %q, graded domain requires HALF_UP (Gerege's ratified tenant mode)", r.Rounding.Mode)
	}
	if len(r.Disbursements) != 1 {
		no("len(disbursements) is %d, graded domain requires exactly 1", len(r.Disbursements))
	}
	if r.RepaymentEvery != 1 {
		no("repayment_every is %d, graded domain requires 1", r.RepaymentEvery)
	}
	if r.RepaymentFrequencyUnit != "MONTHS" {
		no("repayment_frequency_unit is %q, graded domain requires MONTHS", r.RepaymentFrequencyUnit)
	}
	if r.InterestMethod != "DECLINING_BALANCE" {
		no("interest_method is %q, graded domain requires DECLINING_BALANCE", r.InterestMethod)
	}
	if r.DayCount != "FIXED_30_360" {
		no("day_count is %q, graded domain requires FIXED_30_360", r.DayCount)
	}
	if r.DownPaymentPercentage != (Rate{Numerator: 0, Denominator: 1}) {
		no("down_payment_percentage is %s, graded domain requires 0/1", r.DownPaymentPercentage)
	}
	if m, err := r.InstallmentRoundingMultipleMinor.Int64(); err != nil || m != 0 {
		no("installment_rounding_multiple_minor is %q, graded domain requires 0",
			r.InstallmentRoundingMultipleMinor)
	}

	// The semantic window predicate, evaluated from the vector rather than
	// computed.
	last := lastRepaymentDueDate(v)
	if last == nil {
		no("the graded domain's window predicate needs the last repayment due date and this vector does not " +
			"carry one: add expect.last_repayment_due_date (the harness will not compute it, because " +
			"computing it means implementing the month-end rule the port is graded on)")
	} else if len(r.Disbursements) == 1 {
		d := r.Disbursements[0].Date
		if r.ScheduleStartDate.Compare(d) > 0 {
			no("disbursement %s is before schedule_start_date %s: the oracle silently discards it into an "+
				"all-zero schedule, so the shape is outside the graded domain", d, r.ScheduleStartDate)
		}
		if d.Compare(*last) >= 0 {
			no("disbursement %s is on or after the last repayment due date %s: the oracle silently discards "+
				"it into an all-zero schedule", d, *last)
		}
	}
	return len(out) == 0, out
}

func lastRepaymentDueDate(v *Vector) *Date {
	if v.Expect.LastRepaymentDueDate != nil {
		d := *v.Expect.LastRepaymentDueDate
		return &d
	}
	var last *Date
	for i := range v.Expect.Periods {
		p := v.Expect.Periods[i]
		if p.Kind != "REPAYMENT" {
			continue
		}
		if last == nil || p.DueDate.Compare(*last) > 0 {
			d := p.DueDate
			last = &d
		}
	}
	return last
}

// ContractRequest converts a vector's request into the frozen contract type.
func (r *Request) ContractRequest() (contract.GenerateRequest, error) {
	freq, err := frequencyByName(r.RepaymentFrequencyUnit)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	dc, err := dayCountByName(r.DayCount)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	im, err := interestMethodByName(r.InterestMethod)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	mode, err := roundingModeByName(r.Rounding.Mode)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	multiple, err := r.InstallmentRoundingMultipleMinor.Int64()
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	out := contract.GenerateRequest{
		TimeZone: r.TimeZone,
		Currency: contract.Currency{
			Code:            r.Currency.Code,
			MinorUnitDigits: r.Currency.MinorUnitDigits,
		},
		Rounding: contract.Rounding{
			SignificantDigits: r.Rounding.SignificantDigits,
			RateFactorScale:   r.Rounding.RateFactorScale,
			Mode:              mode,
		},
		ScheduleStartDate:                r.ScheduleStartDate.Contract(),
		NumberOfRepayments:               r.NumberOfRepayments,
		RepaymentEvery:                   r.RepaymentEvery,
		RepaymentFrequencyUnit:           freq,
		AnnualNominalInterestRate:        r.AnnualNominalInterestRate.Contract(),
		InterestMethod:                   im,
		DayCount:                         dc,
		DownPaymentPercentage:            r.DownPaymentPercentage.Contract(),
		InstallmentRoundingMultipleMinor: multiple,
	}
	for _, d := range r.Disbursements {
		amt, aerr := d.AmountMinor.Int64()
		if aerr != nil {
			return contract.GenerateRequest{}, aerr
		}
		out.Disbursements = append(out.Disbursements, contract.Disbursement{
			Date:        d.Date.Contract(),
			AmountMinor: amt,
		})
	}
	return out, nil
}

func gcd(a, b int64) int64 {
	for b != 0 {
		a, b = b, a%b
	}
	if a < 0 {
		return -a
	}
	if a == 0 {
		return 1
	}
	return a
}

func abs64(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
