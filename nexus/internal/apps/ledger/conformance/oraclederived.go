package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
)

// ---------------------------------------------------------------------------
// THE ORACLE-DERIVED COLUMN DECLARATION  [T429, G-22]
// ---------------------------------------------------------------------------
//
// THE DIVERGENCE THIS FILE EXISTS FOR IS BETWEEN THE REFERENCE ORACLE AND THIS
// PROGRAM'S FIRST RULES, AND IT IS MEASURED, NOT SUSPECTED.
//
// CLAUDE.md: "The ledger is double-entry and append-only. Balances are derived,
// never written." The reference oracle (Fineract) does the opposite. It stores a
// denormalised running balance ON the posted journal-entry row and rewrites it
// IN PLACE, nightly, by
//
//	UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?,
//	  organization_running_balance=?, office_running_balance=?,
//	  last_modified_by=?, last_modified_on_utc=?  WHERE  id=?
//
// [VERIFIED: JournalEntryRunningBalanceUpdateServiceImpl.java:163-165, pinned
// 426a23544], driven from scheduled job 9 "Update Accounting Running Balances"
// through AccountRunningBalanceUpdateTasklet -> updateRunningBalance(), which is
// a Spring Batch tasklet and does NOT pass through the command bus.
//
// A GO PORT THAT HONOURS THE NON-NEGOTIABLE WILL NEVER WRITE THOSE COLUMNS, SO
// IT CAN NEVER MATCH THEM -- AND THAT MISMATCH IS THE PORT BEING RIGHT.
//
// Before this file, nothing said so. That left three bad outcomes available and
// this file closes each with a different mechanism:
//
//	(1) A PARITY RUN REDS ON A COLUMN THE PORT IS CORRECT TO REFUSE.
//	    Closed by the declaration existing at all, and by it being printed.
//
//	(2) SOMEBODY "FIXES" THE PORT TO WRITE BALANCES TO MAKE A BAR GREEN --
//	    violating a non-negotiable to move a number. Closed by
//	    forbiddenCellCheck: the moment a running-balance cell appears in the
//	    comparator's MEASURED vocabulary, the run refuses at exit 2. The guard
//	    fires on the exact event feared, and it fires on the MEASUREMENT rather
//	    than on a promise.
//
//	(3) THE COLUMNS ARE QUIETLY NEVER COMPARED -- an UNDECLARED UNGRADED REGION,
//	    which is how a port silently stops being graded. Closed by the block
//	    this file renders into the ledger report on EVERY run, pass or fail, and
//	    by the counts being pinned in Go so that widening the carve-out is a
//	    source diff a reviewer sees and never a silence.
//
// ---------------------------------------------------------------------------
// WHAT MAKES THIS DIFFERENT FROM A COMMENT SOMEBODY WROTE  (P-45, P-98)
// ---------------------------------------------------------------------------
//
// A guard that only works when someone remembers to run it enforces nothing, and
// a control that cannot fail and one that refuses everything are the same defect.
// Every check below is therefore MEASURED ON BOTH SIDES and drivable RED:
//
//   - THE GRADED VOCABULARY IS NOT DECLARED, IT IS MEASURED. CellFields() runs a
//     probe through the real comparator and collects the cell names the sink
//     actually emits. This file asserts SET EQUALITY between that measurement
//     and the declaration's `graded_cells`, in BOTH DIRECTIONS. A cell that
//     disappears from the comparator goes red (the "control that cannot fail"
//     direction). A cell that appears goes red until somebody classifies it (the
//     direction that catches a running-balance cell being added).
//
//   - THE MONEY AND STRUCTURE SET IS HARD-CODED HERE, IN GO, AND THE JSON CANNOT
//     OVERRIDE IT. moneyAndStructureColumns names the columns that may NEVER be
//     declared ORACLE_DERIVED or PROVENANCE. Editing the JSON to exempt `amount`
//     does not exempt `amount`; it refuses the run. That is the failure this task
//     existed to prevent, and prose could not have prevented it.
//
//   - THE COUNTS ARE PINNED IN GO in the same commit as the JSON, following
//     T360's DivergencePinCount precedent. They are pinned HERE rather than in
//     `.softhouse/conformance.sh` because that file is held by another worker
//     this fire, and because a carve-out's population belongs beside the code
//     that reads it.

// OracleDerivedFileName is the store-root file this registry is read from.
//
// IT IS A STORE-ROOT FILE, which means the loanschedule census
// (storeRootNonVectorFiles) refuses the store unless it is BOTH named there AND
// read by something. That is the answer to "what reaches this declaration":
// adding the file without wiring the loader makes the harness refuse.
const OracleDerivedFileName = "oracle-derived-columns.json"

// OracleDerivedSchemaV1 is the exact schema id this loader accepts.
const OracleDerivedSchemaV1 = "gerege.ledger.oracle-derived-columns.v1"

// The four dispositions. They are a CLOSED vocabulary: an unrecognised one
// refuses the run rather than defaulting to anything.
const (
	// DispositionOracleDerived -- the oracle's own denormalisation writes it,
	// the port must not, and a mismatch is the port being right.
	DispositionOracleDerived = "ORACLE_DERIVED"

	// DispositionProvenance -- audit metadata and storage identity. Ungraded for
	// a DIFFERENT reason: it records the ACT of recording rather than the fact
	// recorded, so two correct systems disagree on it by construction.
	DispositionProvenance = "PROVENANCE"

	// DispositionGraded -- money or structure, with a cell in the comparator's
	// measured vocabulary that actually compares it.
	DispositionGraded = "GRADED"

	// DispositionGradedGap -- money or structure with NO cell yet. THIS IS NOT AN
	// EXEMPTION AND IT IS PRINTED AS A GAP. The distinction is the whole point of
	// the fourth name: "we do not grade this because the port is right not to
	// produce it" and "we do not grade this yet" are different sentences, and
	// collapsing them is how an exemption list swallows a coverage gap.
	DispositionGradedGap = "GRADED_GAP"
)

// moneyAndStructureColumns is THE LINE THIS TASK MAY NOT CROSS, in source.
//
// Every column here is leg amount, account, debit/credit sense, transaction
// linkage, office, currency or reversal sense -- MONEY AND STRUCTURE. None of
// them may carry disposition ORACLE_DERIVED or PROVENANCE, in this file or any
// later edit of the JSON. The brief that produced this file said it plainly: "If
// your reasoning would exempt a money column, stop: that is the failure this task
// exists to prevent, not a result." A rule of that kind held only in prose is a
// rule the next author edits away in a JSON file without a reviewer noticing, so
// it is held here instead, where the diff is in Go.
//
// They may be GRADED or GRADED_GAP. The difference between those two is honest
// coverage reporting; the difference between either of them and an exemption is
// the thing being protected.
var moneyAndStructureColumns = map[string]string{
	"amount":                 "the leg amount -- integer minor units, the cell the whole corpus exists for",
	"account_id":             "the resolved GL account",
	"type_enum":              "debit/credit sense",
	"currency_code":          "the currency whose minor-unit digits scale the amount",
	"office_id":              "the posting office",
	"transaction_id":         "the transaction the legs belong to",
	"loan_transaction_id":    "transaction linkage to the loan context",
	"savings_transaction_id": "transaction linkage to the savings context",
	"client_transaction_id":  "transaction linkage to the client context",
	"share_transaction_id":   "transaction linkage to the share context",
	"payment_details_id":     "linkage to the payment detail that routed the posting",
	"entity_type_enum":       "which context the entry belongs to",
	"entity_id":              "which entity of that context",
	"reversed":               "whether this posting has been reversed",
	"reversal_id":            "which entry reverses it",
	"manual_entry":           "whether a human posted it directly",
	"entry_date":             "the accounting date the entry lands on",
	"transaction_date":       "the transaction's own date",
	"submitted_on_date":      "the date the posting was submitted",
}

// MoneyAndStructureColumnCount is pinned so that a column silently leaving the
// protected set is a red rather than a smaller map nobody counted.
const MoneyAndStructureColumnCount = 19

// The declaration's populations, pinned. Both directions are refusals: a
// disposition count that grows without this constant moving is a widened
// carve-out nobody reviewed, and one that shrinks is a declaration that quietly
// stopped covering a column.
const (
	OracleDerivedColumnPin = 3
	ProvenanceColumnPin    = 7
	GradedColumnPin        = 3
	GradedGapColumnPin     = 18
	DeclaredColumnPin      = 31
	GradedCellPin          = 14
)

// OracleDerivedColumn is one declared column of one table.
type OracleDerivedColumn struct {
	Column      string `json:"column"`
	Disposition string `json:"disposition"`
	Why         string `json:"why,omitempty"`

	// GradedCell is required on a GRADED row and forbidden on every other. It
	// must be a member of the comparator's MEASURED vocabulary.
	GradedCell string `json:"graded_cell,omitempty"`

	// WhyNoCellYet is required on a GRADED_GAP row and forbidden elsewhere.
	WhyNoCellYet string `json:"why_no_cell_yet,omitempty"`

	// WireField, WrittenBy and ForbiddenCells are the ORACLE_DERIVED row's
	// evidence and its guard. ForbiddenCells is REQUIRED and non-empty on such a
	// row: a derived column with no forbidden spellings would be a declaration
	// with nothing behind it.
	WireField      string   `json:"wire_field,omitempty"`
	WrittenBy      string   `json:"written_by,omitempty"`
	AlsoWrittenBy  string   `json:"also_written_by,omitempty"`
	ForbiddenCells []string `json:"forbidden_cells,omitempty"`
}

// OracleDerivedTable is one table's whole column declaration.
type OracleDerivedTable struct {
	Table               string                `json:"table"`
	ColumnCountObserved int                   `json:"column_count_observed"`
	Columns             []OracleDerivedColumn `json:"columns"`
}

// GradedCellDecl is one cell of the comparator's vocabulary, classified.
type GradedCellDecl struct {
	Cell   string `json:"cell"`
	Grades string `json:"grades"`
}

// RelatedShape is a denormalisation of the SAME SHAPE found elsewhere in the
// tenant schema and deliberately NOT declared, with the reason.
//
// IT IS PART OF THE DECLARATION RATHER THAN A FOOTNOTE because "not found" is a
// statement about the search and never about the world. Printing where the
// search looked and what it declined to declare is what stops the next reader
// assuming the ledger's three columns are the only three in the database.
type RelatedShape struct {
	Table          string   `json:"table"`
	Columns        []string `json:"columns"`
	WhyNotDeclared string   `json:"why_not_declared"`
}

// OracleStampDecl pins which oracle the measurements were taken from.
type OracleStampDecl struct {
	FineractCommit string `json:"fineract_commit"`
	Tenant         string `json:"tenant"`
	Database       string `json:"database"`
	PostgreSQL     string `json:"postgresql"`
	ObservedAtUTC  string `json:"observed_at_utc"`
	EvidenceDir    string `json:"evidence_dir"`
}

// CaptureRule is A2-29 section 6 item 1, made mechanical.
//
// "A ledger parity vector must not set runningBalance=true or
// fetchRunningBalance=true. Any capture that does is capturing a stale,
// oracle-internal accelerator, not a ledger fact."
//
// THAT RULE HAS EXISTED SINCE A2-29 AND NOTHING CHECKED IT. It lived in the gate
// register and in one vector's `_note`, where it is an assertion by the author
// that the author obeyed it. The fields below turn it into a check on the
// CAPTURE BYTES: the three response field names appear in a `/journalentries`
// body if and ONLY if the opt-in parameter was set [MEASURED T429: GET
// /journalentries/78 carries none of them; GET /journalentries/78?runningBalance=true
// carries all three], so their presence is proof of the parameter without the
// harness having to have seen the request.
//
// IT IS A POSITIVE RULE ON CAPTURE, NOT A CARVE-OUT ON GRADING, and that is
// deliberate: A2-29 recommended exactly this instrument and recommended AGAINST
// narrowing the graded domain, which is a hard `user` gate.
type CaptureRule struct {
	Why                 string   `json:"_why"`
	ForbiddenParameters []string `json:"forbidden_parameters"`
	ForbiddenFieldNames []string `json:"forbidden_response_field_names"`
}

// OracleDerivedRegistry is the loaded declaration.
type OracleDerivedRegistry struct {
	Schema        string               `json:"schema"`
	DeclaredBy    string               `json:"declared_by"`
	Gate          string               `json:"gate"`
	Note          string               `json:"_note"`
	Oracle        OracleStampDecl      `json:"oracle"`
	CaptureRule   CaptureRule          `json:"capture_rule"`
	GradedCells   []GradedCellDecl     `json:"graded_cells"`
	Tables        []OracleDerivedTable `json:"tables"`
	RelatedShapes []RelatedShape       `json:"related_shapes_found_but_not_declared"`
}

// LoadOracleDerivedRegistry reads and VALIDATES the declaration. Every error
// here is fatal to the run -- exit 2, no verdict -- because a carve-out that
// loaded partially is a carve-out nobody can state the boundary of.
func LoadOracleDerivedRegistry(path string) (*OracleDerivedRegistry, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("oracle-derived column declaration: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("oracle-derived column declaration %s: %w", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var r OracleDerivedRegistry
	if err := dec.Decode(&r); err != nil {
		return nil, fmt.Errorf("oracle-derived column declaration %s: decode: %w", path, err)
	}
	if r.Schema != OracleDerivedSchemaV1 {
		return nil, fmt.Errorf("oracle-derived column declaration %s: schema %q, want %q",
			path, r.Schema, OracleDerivedSchemaV1)
	}
	if err := r.validate(path); err != nil {
		return nil, err
	}
	return &r, nil
}

func (r *OracleDerivedRegistry) validate(path string) error {
	var bad []string
	add := func(f string, a ...any) { bad = append(bad, fmt.Sprintf(f, a...)) }

	if r.Oracle.FineractCommit == "" || r.Oracle.ObservedAtUTC == "" || r.Oracle.EvidenceDir == "" {
		add("the `oracle` stamp must carry fineract_commit, observed_at_utc and evidence_dir. A " +
			"declaration about what a running oracle does, with no record of WHICH oracle and WHEN, " +
			"is an assertion rather than a measurement")
	}
	if len(r.Tables) == 0 {
		add("declares no tables. A declaration that names nothing exempts nothing and hides everything")
	}
	if len(r.RelatedShapes) == 0 {
		add("declares no related_shapes_found_but_not_declared. The search for other denormalised " +
			"columns must be RECORDED even when it declines to declare them -- `not found` is a " +
			"statement about the search, never about the world")
	}
	for i, rs := range r.RelatedShapes {
		if rs.Table == "" || rs.WhyNotDeclared == "" {
			add("related_shapes_found_but_not_declared[%d] must name a table AND say why it is not "+
				"declared. A table listed with no reason is a table somebody meant to come back to", i)
		}
	}
	if len(r.CaptureRule.ForbiddenFieldNames) == 0 {
		add("capture_rule names no forbidden_response_field_names. A2-29 section 6 item 1 is the " +
			"POSITIVE RULE ON CAPTURE this declaration rests on -- without the field names there is " +
			"nothing to scan a capture for, and the rule stays what it has been since A2-29: a " +
			"sentence nobody checks (P-45)")
	}
	if len(r.CaptureRule.ForbiddenParameters) == 0 {
		add("capture_rule names no forbidden_parameters. The parameters are what a capture author " +
			"reads; the field names are what the scanner finds. Both belong in the record")
	}

	// --- THE MONEY AND STRUCTURE SET, PINNED --------------------------------
	if len(moneyAndStructureColumns) != MoneyAndStructureColumnCount {
		add("the in-source money/structure protected set holds %d columns, pinned %d. It is the one "+
			"thing in this mechanism the JSON cannot reach, so it is pinned separately",
			len(moneyAndStructureColumns), MoneyAndStructureColumnCount)
	}

	// --- THE GRADED VOCABULARY, SET-EQUAL WITH THE MEASUREMENT --------------
	measured := map[string]bool{}
	for _, c := range CellFields() {
		measured[c] = true
	}
	declared := map[string]bool{}
	for _, c := range r.GradedCells {
		if c.Cell == "" || c.Grades == "" {
			add("a graded_cells entry is missing `cell` or `grades`")
			continue
		}
		if declared[c.Cell] {
			add("graded_cells names %q twice", c.Cell)
		}
		declared[c.Cell] = true
		if !measured[c.Cell] {
			add("graded_cells declares %q, WHICH THIS COMPARATOR DOES NOT EMIT. The vocabulary is "+
				"MEASURED by running a probe through the real comparator (CellFields), so a declared "+
				"cell nothing compares is a claim of coverage that does not exist", c.Cell)
		}
	}
	for _, c := range CellFields() {
		if !declared[c] {
			add("the comparator EMITS cell %q and the declaration does not classify it. A NEW GRADED "+
				"CELL MUST BE CLASSIFIED BEFORE IT IS GRADED -- that is the direction of this check "+
				"that catches somebody adding a running-balance cell to make a bar green, and it is "+
				"also the direction that catches a cell being added with nobody deciding whether the "+
				"port is even supposed to produce it", c)
		}
	}
	if len(r.GradedCells) != GradedCellPin {
		add("declares %d graded cells, pinned %d. The comparator's vocabulary moving is a change to "+
			"WHAT IS GRADED, and it moves this constant in the same commit, deliberately",
			len(r.GradedCells), GradedCellPin)
	}

	// --- THE COLUMNS --------------------------------------------------------
	counts := map[string]int{}
	total := 0
	for _, t := range r.Tables {
		if t.Table == "" {
			add("a table entry has no name")
		}
		seen := map[string]bool{}
		for _, c := range t.Columns {
			total++
			if c.Column == "" {
				add("table %q declares a column with no name", t.Table)
				continue
			}
			if seen[c.Column] {
				add("table %q declares column %q twice", t.Table, c.Column)
			}
			seen[c.Column] = true
			counts[c.Disposition]++

			switch c.Disposition {
			case DispositionOracleDerived, DispositionProvenance:
				// THE PROTECTED SET. This is the refusal the whole file is for.
				if what, protected := moneyAndStructureColumns[c.Column]; protected {
					add("table %q column %q is declared %s. IT IS %s -- %s. MONEY AND STRUCTURE ARE "+
						"GRADED, ALWAYS: a money or structure column may be GRADED (a cell compares "+
						"it) or GRADED_GAP (no cell yet, and that is a COVERAGE GAP printed as one), "+
						"and it may never be moved out of the graded domain by editing this JSON. "+
						"This set is HARD-CODED in ledger/conformance/oraclederived.go and the "+
						"declaration cannot override it",
						t.Table, c.Column, c.Disposition, strings.ToUpper(c.Column), what)
				}
				if c.GradedCell != "" {
					add("table %q column %q is declared %s and also names graded_cell %q. A column "+
						"cannot be both outside the graded domain and compared by a cell",
						t.Table, c.Column, c.Disposition, c.GradedCell)
				}
				if c.WhyNoCellYet != "" {
					add("table %q column %q is declared %s and carries why_no_cell_yet, which belongs "+
						"only to a GRADED_GAP row", t.Table, c.Column, c.Disposition)
				}
				if c.Why == "" {
					add("table %q column %q is declared %s with no `why`. The two ungraded "+
						"dispositions are ungraded for DIFFERENT REASONS and each row must state its "+
						"own", t.Table, c.Column, c.Disposition)
				}
			case DispositionGraded:
				if c.GradedCell == "" {
					add("table %q column %q is declared GRADED and names no graded_cell. A column "+
						"declared graded with no cell behind it is a control that cannot fail (P-98)",
						t.Table, c.Column)
				} else if !measured[c.GradedCell] {
					add("table %q column %q is declared GRADED by cell %q, WHICH THIS COMPARATOR DOES "+
						"NOT EMIT. The claim is checked against the measurement, not taken",
						t.Table, c.Column, c.GradedCell)
				}
				if c.WhyNoCellYet != "" {
					add("table %q column %q is GRADED and carries why_no_cell_yet", t.Table, c.Column)
				}
			case DispositionGradedGap:
				if c.WhyNoCellYet == "" {
					add("table %q column %q is declared GRADED_GAP with no why_no_cell_yet. A gap "+
						"with no stated reason is indistinguishable from an exemption nobody argued for",
						t.Table, c.Column)
				}
				if c.GradedCell != "" {
					add("table %q column %q is GRADED_GAP and names a graded_cell", t.Table, c.Column)
				}
			default:
				add("table %q column %q declares disposition %q; the closed vocabulary is %s, %s, %s, %s",
					t.Table, c.Column, c.Disposition, DispositionOracleDerived, DispositionProvenance,
					DispositionGraded, DispositionGradedGap)
			}

			if c.Disposition == DispositionOracleDerived {
				if c.WrittenBy == "" {
					add("table %q column %q is ORACLE_DERIVED and does not say WHAT WRITES IT. The "+
						"carve-out rests entirely on the oracle writing it out of band; a row that "+
						"cannot name the writer has not established that", t.Table, c.Column)
				}
				if len(c.ForbiddenCells) == 0 {
					add("table %q column %q is ORACLE_DERIVED and names no forbidden_cells. Without "+
						"them the declaration is a sentence nothing enforces (P-45)",
						t.Table, c.Column)
				}
				for _, fc := range c.ForbiddenCells {
					if measured[fc] {
						add("THE COMPARATOR NOW EMITS CELL %q, WHICH THE DECLARATION FORBIDS BECAUSE "+
							"%s.%s IS ORACLE-DERIVED. Somebody has started GRADING a column this "+
							"program's non-negotiables say the port must NEVER WRITE (CLAUDE.md: the "+
							"ledger is append-only, balances are DERIVED, NEVER WRITTEN). Either "+
							"remove the cell, or take the carve-out to G-22 and let it be re-decided "+
							"in the open. EXIT 2 -- this is NOT a pass",
							fc, t.Table, c.Column)
					}
				}
			}
		}
		if t.ColumnCountObserved != 0 && t.ColumnCountObserved != len(t.Columns) {
			add("table %q says column_count_observed %d and declares %d columns. EVERY column of a "+
				"declared table must be classified, or the declaration is silent about the ones it "+
				"skipped -- which is the undeclared ungraded region this file exists to remove",
				t.Table, t.ColumnCountObserved, len(t.Columns))
		}
	}

	pins := []struct {
		disposition string
		pin         int
	}{
		{DispositionOracleDerived, OracleDerivedColumnPin},
		{DispositionProvenance, ProvenanceColumnPin},
		{DispositionGraded, GradedColumnPin},
		{DispositionGradedGap, GradedGapColumnPin},
	}
	for _, p := range pins {
		if counts[p.disposition] != p.pin {
			add("declares %d %s columns, PINNED %d. Widening a carve-out is a source edit a reviewer "+
				"sees; narrowing one silently is how a declared gap stops being declared. Both "+
				"directions move the pin in ledger/conformance/oraclederived.go, in the SAME COMMIT",
				counts[p.disposition], p.disposition, p.pin)
		}
	}
	if total != DeclaredColumnPin {
		add("declares %d columns in total, pinned %d", total, DeclaredColumnPin)
	}

	if len(bad) > 0 {
		sort.Strings(bad)
		return fmt.Errorf("oracle-derived column declaration %s:\n  - %s",
			path, strings.Join(bad, "\n  - "))
	}
	return nil
}

// ForbiddenCellNames returns every cell spelling the declaration forbids,
// sorted. Used by Admit to refuse a vector that tries to grade one.
func (r *OracleDerivedRegistry) ForbiddenCellNames() []string {
	if r == nil {
		return nil
	}
	set := map[string]bool{}
	for _, t := range r.Tables {
		for _, c := range t.Columns {
			if c.Disposition != DispositionOracleDerived {
				continue
			}
			for _, fc := range c.ForbiddenCells {
				set[fc] = true
			}
		}
	}
	out := make([]string, 0, len(set))
	for k := range set {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// IsForbiddenCell reports whether name is a spelling of an ORACLE_DERIVED column.
func (r *OracleDerivedRegistry) IsForbiddenCell(name string) bool {
	if r == nil {
		return false
	}
	for _, f := range r.ForbiddenCellNames() {
		if f == name {
			return true
		}
	}
	return false
}

// CaptureScanOutcome is what the capture rule could say about ONE cited
// artefact. The THREE states are kept distinct on purpose: "clean", "carries a
// forbidden field" and "could not be read" are three different facts, and
// collapsing the third into the first is how a check that did not run gets
// counted as a check that passed.
type CaptureScanOutcome int

const (
	// CaptureScanClean -- the bytes were read and carry no forbidden field.
	CaptureScanClean CaptureScanOutcome = iota
	// CaptureScanForbidden -- the bytes carry a forbidden field, so the capture
	// was taken with the opt-in parameter set.
	CaptureScanForbidden
	// CaptureScanUnreadable -- the citation does not resolve to bytes in this
	// checkout. THIS IS NOT A PASS and it is counted and printed separately.
	CaptureScanUnreadable
)

// CaptureScan is one vector's result under the capture rule.
type CaptureScan struct {
	CaseID  string
	Field   string
	Ref     string
	Outcome CaptureScanOutcome
	Detail  string
}

// ScanCaptureRule applies A2-29's positive rule on capture to one vector's cited
// artefacts.
//
// WHY IT SCANS THE RESPONSE BODY AND NOT THE REQUEST. The corpus does not always
// hold the request that produced a capture, and for the three oldest ledger
// vectors the citation is FILE-NAME-ONLY and resolves to no bytes at all. What
// it does hold is the oracle's own answer, and the three field names are present
// in that answer if and only if the opt-in parameter was set -- measured on this
// oracle at T429, both directions. So the response is the surface where the rule
// is CHECKABLE rather than merely stated.
//
// UNREADABLE IS REPORTED, NEVER SILENTLY SKIPPED. A vector whose citation names
// no bytes is returned as CaptureScanUnreadable and printed in the block, so the
// coverage of this rule is a number a reader sees rather than an impression.
func (r *OracleDerivedRegistry) ScanCaptureRule(repoRoot string, v *Vector) []CaptureScan {
	if r == nil || v == nil {
		return nil
	}
	var out []CaptureScan
	refs := []struct{ field, ref string }{
		{"provenance.capture_ref", v.Provenance.CaptureRef},
		{"provenance.request_capture_ref", v.Provenance.RequestCaptureRef},
	}
	for _, rf := range refs {
		if strings.TrimSpace(rf.ref) == "" {
			continue
		}
		raw, err := os.ReadFile(filepathJoin(repoRoot, rf.ref))
		if err != nil {
			out = append(out, CaptureScan{
				CaseID: v.CaseID, Field: rf.field, Ref: rf.ref,
				Outcome: CaptureScanUnreadable,
				Detail: "the citation does not resolve to bytes in this checkout, so the capture rule " +
					"COULD NOT RUN on it. That is not the same as it passing",
			})
			continue
		}
		hit := ""
		for _, f := range r.CaptureRule.ForbiddenFieldNames {
			if f != "" && bytes.Contains(raw, []byte(f)) {
				hit = f
				break
			}
		}
		if hit != "" {
			out = append(out, CaptureScan{
				CaseID: v.CaseID, Field: rf.field, Ref: rf.ref,
				Outcome: CaptureScanForbidden, Detail: hit,
			})
			continue
		}
		out = append(out, CaptureScan{
			CaseID: v.CaseID, Field: rf.field, Ref: rf.ref, Outcome: CaptureScanClean,
		})
	}
	return out
}

// CaptureRuleReasons turns a forbidden scan into admissibility reasons.
//
// A VECTOR CITING SUCH A CAPTURE IS INADMISSIBLE, NOT MERELY NOTED. The capture
// carries a column A2-29 measured to be a second source of truth that can be,
// and on this very oracle already was, wrong by MNT 2,000,000.00 while flagged
// computed:true -- and today carries a served balance of ZERO on an account
// holding 72,866.39. Promoting a vector from such a body is promoting the
// accelerator as if it were the ledger.
func (r *OracleDerivedRegistry) CaptureRuleReasons(repoRoot string, v *Vector) []string {
	var bad []string
	for _, sc := range r.ScanCaptureRule(repoRoot, v) {
		if sc.Outcome != CaptureScanForbidden {
			continue
		}
		bad = append(bad, fmt.Sprintf(
			"%s names artefact %q and THOSE BYTES CARRY %q. That field appears in an oracle response "+
				"if and ONLY if the capture set %s, which A2-29 section 6 item 1 forbids outright: "+
				"the running-balance columns are a SECOND SOURCE OF TRUTH, not a cache -- measured "+
				"disagreeing with the derived sum by MNT 2,000,000.00 while flagged computed:true, "+
				"and measured again at T429 serving 0.000000 for an account holding 72,866.39. A "+
				"vector promoted from such a body has captured a stale oracle-internal accelerator "+
				"and called it a ledger fact. RE-CAPTURE WITHOUT THE PARAMETER; do not exempt",
			sc.Field, sc.Ref, sc.Detail, strings.Join(r.CaptureRule.ForbiddenParameters, " / ")))
	}
	return bad
}

// filepathJoin keeps this file's only path join in one place so the capture rule
// and the citation checks cannot drift on how a ref is resolved.
func filepathJoin(root, ref string) string {
	if root == "" {
		return ref
	}
	return strings.TrimRight(root, "/") + "/" + strings.TrimLeft(ref, "/")
}

// OracleDerivedColumnsOf returns the ORACLE_DERIVED rows of every table, in file
// order.
func (r *OracleDerivedRegistry) OracleDerivedColumnsOf() []struct {
	Table string
	Col   OracleDerivedColumn
} {
	var out []struct {
		Table string
		Col   OracleDerivedColumn
	}
	if r == nil {
		return out
	}
	for _, t := range r.Tables {
		for _, c := range t.Columns {
			if c.Disposition == DispositionOracleDerived {
				out = append(out, struct {
					Table string
					Col   OracleDerivedColumn
				}{t.Table, c})
			}
		}
	}
	return out
}

// countBy returns how many columns carry a disposition.
func (r *OracleDerivedRegistry) countBy(disposition string) int {
	n := 0
	if r == nil {
		return 0
	}
	for _, t := range r.Tables {
		for _, c := range t.Columns {
			if c.Disposition == disposition {
				n++
			}
		}
	}
	return n
}

// OracleDerivedLines renders the carve-out block into the ledger report.
//
// PRINTED ON EVERY RUN, PASS OR FAIL, AND WHEN THE REGISTRY IS ABSENT. The
// absent case is NOT silent, for the reason no empty state in this report is
// silent: "there is no carve-out" and "nobody rendered the carve-out" have to be
// distinguishable, or the second hides behind the first -- and here the second
// would restore exactly the undeclared-ungraded-region state the file removes.
func (s *Summary) OracleDerivedLines() []string {
	out := []string{
		"    THE ORACLE-DERIVED COLUMN CARVE-OUT — where THIS PORT IS RIGHT NOT TO MATCH THE ORACLE.",
	}
	r := s.OracleDerived
	if r == nil {
		return append(out,
			"      (NO ORACLE-DERIVED DECLARATION IS LOADED. That is NOT the same state as there being",
			"      no carve-out, and it is the worse of the two: the reference oracle DOES write a",
			"      denormalised running balance onto posted journal-entry rows, so a harness that",
			"      cannot say which columns are excluded has an UNDECLARED UNGRADED REGION — which is",
			"      how a port silently stops being graded. Expected .softhouse/vectors/"+
				OracleDerivedFileName+".)",
			"")
	}

	derived := r.OracleDerivedColumnsOf()
	out = append(out,
		fmt.Sprintf(
			"      oracle-derived columns  %-4d (pinned %d)   provenance %d   graded %d   graded-gap %d",
			len(derived), OracleDerivedColumnPin, r.countBy(DispositionProvenance),
			r.countBy(DispositionGraded), r.countBy(DispositionGradedGap)),
		fmt.Sprintf(
			"      graded cell vocabulary  %-4d (pinned %d)   MEASURED from the comparator, not declared",
			len(CellFields()), GradedCellPin),
		"",
		"      CLAUDE.md, non-negotiable: THE LEDGER IS DOUBLE-ENTRY AND APPEND-ONLY; BALANCES ARE",
		"      DERIVED, NEVER WRITTEN. The reference oracle does the opposite — it stores a running",
		"      balance ON the posted row and job 9 'Update Accounting Running Balances' rewrites it in",
		"      place, nightly, by raw UPDATE ... WHERE id=?, outside the command bus. A port that",
		"      honours the non-negotiable will NEVER produce these columns, so it can never match",
		"      them, AND THAT MISMATCH IS THE PORT BEING RIGHT. They are excluded BY DESIGN:",
		"",
	)
	for _, d := range derived {
		out = append(out, fmt.Sprintf("      * %s.%s  ->  wire %q", d.Table, d.Col.Column, d.Col.WireField))
		out = append(out, wrapAt("WRITTEN BY: "+d.Col.WrittenBy, 96, "          ")...)
	}
	out = append(out,
		"",
		"      WHAT IS NOT IN THIS CARVE-OUT, said because a carve-out that nobody bounds grows.",
		"      MONEY AND STRUCTURE ARE GRADED, ALWAYS — leg amounts, GL account ids and codes,",
		fmt.Sprintf(
			"      debit/credit sense, transaction linkage. Those %d columns are protected IN GO",
			MoneyAndStructureColumnCount),
		"      (moneyAndStructureColumns, ledger/conformance/oraclederived.go): declaring one of them",
		"      ORACLE_DERIVED or PROVENANCE REFUSES THE RUN AT EXIT 2, and editing the JSON cannot",
		"      reach that rule. A money column can be GRADED or a printed GRADED_GAP; it can never",
		"      be exempt.",
		"",
		fmt.Sprintf(
			"      %d COLUMNS ARE GRADED_GAP — money or structure with NO CELL YET. THAT IS A COVERAGE",
			r.countBy(DispositionGradedGap)),
		"      GAP, NOT AN EXEMPTION, and it is printed here so the two never collapse into one:",
	)
	for _, t := range r.Tables {
		for _, c := range t.Columns {
			if c.Disposition == DispositionGradedGap {
				out = append(out, fmt.Sprintf("        - %s.%s", t.Table, c.Column))
			}
		}
	}
	out = append(out,
		"",
		"      THE SAME SHAPE ELSEWHERE IN THE TENANT SCHEMA, found and DELIBERATELY NOT DECLARED —",
		"      recorded because 'not found' is a statement about the search, never about the world:",
	)
	for _, rs := range r.RelatedShapes {
		cols := strings.Join(rs.Columns, ", ")
		if cols == "" {
			cols = "no such column — searched and found clean"
		}
		out = append(out, fmt.Sprintf("        - %s (%s)", rs.Table, cols))
		out = append(out, wrapAt(rs.WhyNotDeclared, 96, "            ")...)
	}

	// --- THE POSITIVE RULE ON CAPTURE, AND ITS MEASURED COVERAGE ------------
	clean, forbidden, unreadable := 0, 0, 0
	for _, sc := range s.CaptureScans {
		switch sc.Outcome {
		case CaptureScanClean:
			clean++
		case CaptureScanForbidden:
			forbidden++
		case CaptureScanUnreadable:
			unreadable++
		}
	}
	out = append(out,
		"",
		"      THE POSITIVE RULE ON CAPTURE — A2-29 §6.1, checked rather than promised since T429.",
		fmt.Sprintf(
			"      cited artefacts scanned  CLEAN %-4d FORBIDDEN %-4d UNREADABLE %d",
			clean, forbidden, unreadable),
		"      A ledger vector may not be captured with "+
			strings.Join(r.CaptureRule.ForbiddenParameters, " or ")+". The scanner looks for",
		"      "+strings.Join(r.CaptureRule.ForbiddenFieldNames, ", ")+" in the cited bytes:",
		"      those fields appear in an oracle response IF AND ONLY IF the parameter was set",
		"      [MEASURED T429: GET /journalentries/78 carries none of them; the same GET with",
		"      ?runningBalance=true carries all three]. A vector citing such a body is INADMISSIBLE.",
	)
	if unreadable > 0 {
		out = append(out, wrapAt(fmt.Sprintf(
			"UNREADABLE IS NOT A PASS. %d cited artefact(s) do not resolve to bytes in this checkout — "+
				"the file-name-only citations admit.go pins by (case_id, field) — so THIS RULE DID NOT "+
				"RUN ON THEM. The number is printed rather than folded into CLEAN, because a check "+
				"that did not run counted as one that passed is the shape every vacuous guard in this "+
				"program has had (P-35).", unreadable), 96, "        ")...)
	}
	out = append(out,
		"",
		fmt.Sprintf(
			"      OBSERVED FROM THE LIVE ORACLE %s, fineract %s, tenant %s, database %s.",
			r.Oracle.ObservedAtUTC, r.Oracle.FineractCommit[:9], r.Oracle.Tenant, r.Oracle.Database),
		"      Evidence: "+r.Oracle.EvidenceDir,
		"      THE DECLARATION IS NOT A RATIFIED DEC. It is raised under "+r.Gate+"; DEC-2 is ratified and",
		"      an agent may not amend it. See docs/adr/DEC-2-PROPOSED-REVISION-T429-oracle-derived-columns.md.",
		"",
	)
	return out
}
