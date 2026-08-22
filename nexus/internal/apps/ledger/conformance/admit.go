package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Admit returns every reason this vector may not be graded. An empty slice
// means admissible.
//
// DEFAULT-DENY THROUGHOUT. Every rule below is phrased as "this must be true",
// never as "this must not be wrong", because every vacuous guard this program
// has found was a NEGATIVE assertion (P-35).
func Admit(v *Vector, opts Options) []string {
	var bad []string
	add := func(f string, a ...any) { bad = append(bad, fmt.Sprintf(f, a...)) }

	// --- schema, context, class ------------------------------------------
	if v.Schema != SchemaV1 {
		add("schema %q, want %q", v.Schema, SchemaV1)
	}
	// P-9, the second schema's half. See SchemaContexts().
	if !IsSchemaContext(v.Ctx) {
		add("context %q is not a context THIS SCHEMA grades (have: %s). A vector's schema, its directory "+
			"and the comparator that grades it must name ONE context",
			v.Ctx, strings.Join(SchemaContexts(), ", "))
	}
	dir := filepath.ToSlash(filepath.Dir(v.Path))
	if dir != v.Ctx {
		add("context %q but the file sits in directory %q; the two must agree", v.Ctx, dir)
	}
	switch v.Class {
	case ClassParity, ClassOracleRefusal:
	default:
		add("class %q is not one this schema knows (parity, oracle-refusal)", v.Class)
	}
	if v.CaseID == "" {
		add("case_id is empty")
	}
	if strings.TrimSpace(v.Title) == "" {
		add("title is empty")
	}

	// --- the pin ---------------------------------------------------------
	if opts.Pin != nil {
		if v.DEC2Revision != opts.Pin.DEC2Revision {
			add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)
		}
		if v.Oracle.FineractCommit != opts.Pin.FineractCommit {
			add("oracle.fineract_commit %q but the store pins %q",
				v.Oracle.FineractCommit, opts.Pin.FineractCommit)
		}
		// DEC-2 brief item (3) and G-10 option (c), as a DENYLIST rather than a
		// comment: products 22, 23, 24, 27 and 28 were OBSERVED to be
		// inadmissible today by re-sending each mapping (A2-300..A2-315, all
		// 403), because GL account 2 was retyped ASSET->INCOME underneath their
		// live mappings and the oracle will not re-create the state it holds.
		for _, p := range opts.Pin.InadmissibleProductIDs {
			if v.Request.ProductID == p {
				add("request.product_id %d is on the store's INADMISSIBLE PRODUCT denylist: the oracle "+
					"itself refuses to re-create this product's mapping today (403, observed by "+
					"re-sending it), so a vector taken from it cannot be re-derived. G-10 option (c)", p)
			}
		}
	}

	// --- the note, and the glAccountType instability record ---------------
	//
	// DEC-2's brief for A2-15, item (1), is explicit that a handoff is not
	// enough: "whichever it picks, the instability must be recorded in the
	// vector's OWN note -- not only in a handoff". So this is checked, not
	// trusted.
	if strings.TrimSpace(v.Note) == "" {
		add("_note is empty. This schema requires the note because the facts that have to travel with a " +
			"ledger vector -- which cells are excluded and why, and what this vector does NOT grade -- " +
			"have no other structured home, and a fact recorded only in a handoff is a fact the next " +
			"reader of the file will not have")
	}
	excludes := false
	for _, l := range v.Expect.Legs {
		for _, f := range l.ExcludedFields {
			if f != "gl_account_type" {
				add("excluded_fields carries %q; the only cell this schema permits a vector to exclude is "+
					"gl_account_type, and widening that set is a source edit a reviewer sees rather than "+
					"a JSON edit nobody does", f)
			}
			excludes = true
		}
	}
	if excludes && !strings.Contains(v.Note, "glAccountType") {
		add("this vector excludes gl_account_type and its _note does not mention glAccountType. The " +
			"exclusion exists because A2-26 observed the identical row rendering ASSET in A2-088 and " +
			"INCOME in A2-320 with every other cell byte-identical and NO entry edited; a reader who " +
			"meets the exclusion without the reason will read it as a convenience")
	}

	// --- G-12: the running-balance columns may not be graded ---------------
	//
	// The schema has no field for them (see PostedEntry's doc comment), so this
	// is belt and braces on the NOTE rather than on the data: a vector that
	// talks about grading a running balance is a vector written by somebody who
	// did not read G-12.
	for _, s := range []string{"office_running_balance", "organization_running_balance"} {
		if strings.Contains(v.Note, "grades "+s) {
			add("the _note claims to grade %s. GATE G-12 is OPEN and A2-29 MEASURED that column to be a "+
				"SECOND SOURCE OF TRUTH, not a cache: it was made to disagree with the derived sum by "+
				"MNT 2,000,000.00 on the live oracle, survived four organisation-wide recomputes and "+
				"propagated into a freshly computed row. No vector may grade it", s)
		}
	}

	// --- graded domain, DEC-2 §4.2 ----------------------------------------
	switch v.Oracle.Seam {
	case "ledger_rest_admin", "ledger_rest_posting", "ledger_db_readback":
	default:
		add("oracle.seam %q is not one of G-01's three (ledger_rest_admin, ledger_rest_posting, "+
			"ledger_db_readback). ABSENT REFUSES: default-deny, DEC-2 §4.10", v.Oracle.Seam)
	}
	if v.Request.Seam != v.Oracle.Seam {
		add("request.seam %q and oracle.seam %q disagree; P-1 names the seam as a request field and the "+
			"stamp records it, and two copies of one fact must not be able to drift",
			v.Request.Seam, v.Oracle.Seam)
	}
	// G-07 binds every vector in this schema, because every vector in this
	// schema asserts a money cell.
	if v.Request.Currency.Code != "MNT" {
		add("request.currency.code %q; G-07 admits only MNT, the only currency any captured journal "+
			"entry is denominated in", v.Request.Currency.Code)
	}
	if v.Request.Currency.MinorUnitDigits != 2 {
		add("request.currency.minor_unit_digits %d; G-07 admits only 2",
			v.Request.Currency.MinorUnitDigits)
	}
	if v.Request.ProductID != 0 {
		// The accounting-path predicates bind only where a product took part.
		if v.Request.ProductType != "LOAN" {
			add("request.product_type %q; G-02 admits only LOAN", v.Request.ProductType)
		}
		switch v.Request.AccountingRule {
		case "CASH_BASED", "ACCRUAL_PERIODIC":
		default:
			add("request.accounting_rule %q; G-03 admits CASH_BASED and ACCRUAL_PERIODIC. "+
				"ACCRUAL_UPFRONT is refused for one reason and it is EVIDENTIAL, not source-based: no "+
				"capture exists at accountingRule = 4", v.Request.AccountingRule)
		}
		switch {
		case v.Request.AccountingRule == "CASH_BASED" && v.Request.SlotFamily != "CashLoanSlot":
			add("G-05: accounting_rule CASH_BASED requires slot_family CashLoanSlot, got %q",
				v.Request.SlotFamily)
		case v.Request.AccountingRule == "ACCRUAL_PERIODIC" && v.Request.SlotFamily != "AccrualLoanSlot":
			add("G-05: accounting_rule ACCRUAL_PERIODIC requires slot_family AccrualLoanSlot, got %q",
				v.Request.SlotFamily)
		}
		// G-06.
		if v.Request.SlotCode == 1 && v.Request.PaymentTypeID == nil {
			add("G-06: slot_code 1 (FUND_SOURCE) with a nil payment_type_id is REFUSED. The oracle " +
				"issues the payment-type finder with a null argument and no null guard " +
				"(AccountingProcessorHelper.java:1199-1206), two readings of what that matches are " +
				"defensible, and no capture separates them")
		}
	}
	// G-09 / G-10 over the chart rows the vector supplies.
	for _, a := range v.Request.Accounts {
		switch a.Usage {
		case "DETAIL", "HEADER":
		default:
			add("account %d usage %q; G-10 admits DETAIL and HEADER, as STORED VALUES and never as "+
				"ordinals (DEC-2 §4.8)", a.ID, a.Usage)
		}
	}

	// --- the three-part capture citation, T233's rule applied to every vector -
	if v.Provenance.Kind != "capture" {
		add("provenance.kind %q; this schema admits only \"capture\". It has no hand-authored class and "+
			"no contract-derived class: a ledger vector that was not observed from the oracle has no "+
			"home here", v.Provenance.Kind)
	}
	bad = append(bad, citationReasons(opts.RepoRoot, "provenance.capture_ref",
		v.Provenance.CaptureRef, v.Provenance.CaptureSHA256, v.Provenance.CaptureCaseID)...)
	bad = append(bad, citationReasons(opts.RepoRoot, "provenance.request_capture_ref",
		v.Provenance.RequestCaptureRef, v.Provenance.RequestCaptureSHA256,
		v.Provenance.RequestCaptureCaseID)...)
	if strings.TrimSpace(v.Provenance.RerunInvariant) == "" {
		add("provenance.rerun_invariant is empty. PART THREE of the citation: a citation that names an " +
			"artefact but never says what re-running it would have to reproduce cannot be checked by " +
			"re-running it")
	}

	// --- exemptions: default-deny -----------------------------------------
	if len(v.InvariantExemptions) > 0 {
		add("this vector declares %d invariant_exemptions and THIS SCHEMA ADMITS NONE. The loanschedule "+
			"schema has a grounding classifier behind its exemptions (T222/T225/T230/T233) that decides "+
			"GROUNDED / UNDETERMINED-ON-THE-RECORD / UNGROUNDED against the recorded output; this schema "+
			"has no such classifier, so admitting an exemption would switch an invariant off with "+
			"nothing checking that the thing it excuses is visible in the record. Re-observe rather than "+
			"exempt (P-8)", len(v.InvariantExemptions))
	}

	// --- capabilities ------------------------------------------------------
	if len(v.CapabilitiesRequired) == 0 {
		add("capabilities_required is empty. Default-deny: a vector that names no capability has not " +
			"said what its capture seam had to be able to see, and the registry cannot refuse it")
	}
	if opts.Registry != nil {
		bad = append(bad, opts.Registry.Refusals(v)...)
	}

	// --- the expectation ---------------------------------------------------
	switch v.Expect.Kind {
	case "journal-entry":
		if v.Class != ClassParity {
			add("expect.kind journal-entry on a %q vector; only a parity vector asserts an entry", v.Class)
		}
		if len(v.Expect.Legs) < 2 {
			add("expect.legs has %d entries. A journal entry with fewer than two legs is not double "+
				"entry, and nothing in the captured corpus has one", len(v.Expect.Legs))
		}
		if v.Expect.HTTPStatus != 200 {
			add("expect.http_status %d on a journal-entry expectation; the observed accept status is 200",
				v.Expect.HTTPStatus)
		}
		if v.Expect.Refusal != (Refusal{}) {
			add("expect.refusal is populated on a journal-entry expectation; the two are exclusive")
		}
	case "refusal":
		if v.Class != ClassOracleRefusal {
			add("expect.kind refusal on a %q vector; an observed refusal is class oracle-refusal", v.Class)
		}
		if len(v.Expect.Legs) > 0 {
			add("expect.legs is non-empty on a refusal expectation. A refused request created no entry, " +
				"so a leg here would be an amount nobody observed -- the exact way an unobserved number " +
				"enters a store")
		}
		if v.Expect.TotalDebitsMinor != "" || v.Expect.TotalCreditsMinor != "" {
			add("expect totals are set on a refusal expectation; a refused request has no totals")
		}
		if v.Expect.Refusal.HTTPStatus < 400 {
			add("expect.refusal.http_status %d is not an error status", v.Expect.Refusal.HTTPStatus)
		}
		if v.Expect.Refusal.HTTPStatus != v.Expect.HTTPStatus {
			add("expect.http_status %d and expect.refusal.http_status %d disagree",
				v.Expect.HTTPStatus, v.Expect.Refusal.HTTPStatus)
		}
		if strings.TrimSpace(v.Expect.Refusal.Code) == "" {
			add("expect.refusal.code is empty. The oracle's globalisation code is the cell that tells " +
				"one 403 from another, and a refusal vector that grades only the status grades almost " +
				"nothing")
		}
	default:
		add("expect.kind %q is not one this schema knows (journal-entry, refusal)", v.Expect.Kind)
	}

	// --- legs: the money pairing, and the request/expect correspondence ----
	if len(v.Expect.Legs) > 0 && len(v.Expect.Legs) != len(v.Request.Legs) {
		add("expect.legs has %d entries and request.legs has %d; the comparator diffs them positionally "+
			"and a length mismatch is a transcription defect, not a divergence to grade",
			len(v.Expect.Legs), len(v.Request.Legs))
	}
	chart := map[int64]bool{}
	for _, a := range v.Request.Accounts {
		chart[a.ID] = true
	}
	for i, l := range v.Request.Legs {
		if !l.Side.Valid() {
			add("request.legs[%d].entry_side %q is neither DEBIT nor CREDIT", i, l.Side)
		}
		if !chart[l.AccountID] {
			add("request.legs[%d] points at GL account %d and request.accounts does not carry it. The "+
				"chart is DATA the vector transcribes (DEC-2 §4.5) and a leg the chart cannot resolve "+
				"would make the implementation guess", i, l.AccountID)
		}
		if strings.TrimSpace(l.AmountMajorText) == "" {
			add("request.legs[%d].amount_major_text is empty. It is the ORACLE'S OWN CHARACTERS and it "+
				"is the whole input to the conversion this vector grades", i)
		}
	}
	for i, l := range v.Expect.Legs {
		if !l.Side.Valid() {
			add("expect.legs[%d].entry_side %q is neither DEBIT nor CREDIT", i, l.Side)
		}
		if _, err := parseMinor(l.AmountMinor); err != nil {
			add("expect.legs[%d].amount_minor: %v. Money in a stored vector is an integer STRING of "+
				"minor units (DEC-2 §4.3 consequence 4, T186 category (c))", i, err)
		}
		if strings.TrimSpace(l.AmountMajorText) == "" {
			add("expect.legs[%d].amount_major_text is empty. The pairing is mandatory: the graded value "+
				"is the minor-unit integer and the major-unit text is the transcription cross-check", i)
		}
		if i < len(v.Request.Legs) && v.Request.Legs[i].AmountMajorText != l.AmountMajorText {
			add("expect.legs[%d].amount_major_text %q and request.legs[%d].amount_major_text %q "+
				"disagree; both transcribe the same oracle characters",
				i, l.AmountMajorText, i, v.Request.Legs[i].AmountMajorText)
		}
	}
	if v.Expect.Kind == "journal-entry" {
		if _, err := parseMinor(v.Expect.TotalDebitsMinor); err != nil {
			add("expect.total_debits_minor: %v", err)
		}
		if _, err := parseMinor(v.Expect.TotalCreditsMinor); err != nil {
			add("expect.total_credits_minor: %v", err)
		}
	}

	// --- graded_against: P-10, and T9-F1b ---------------------------------
	if len(v.GradedAgainst) == 0 {
		add("graded_against is empty. A vector that kills no named wrong implementation is a capture, " +
			"not a grader, and the store must not pretend otherwise")
	}
	sawMoney := false
	for i, cf := range v.GradedAgainst {
		if _, ok := Lookup(cf.Impl); !ok {
			add("graded_against[%d] names implementation %q, which is NOT REGISTERED. DEC-2 "+
				"precondition P-10: graded_against is a declarative record and does not execute "+
				"anything, so a name nobody can run makes the claim unfalsifiable. Register it in "+
				"impl.go and it becomes selectable with -ledger-impl", i, cf.Impl)
		} else if _, isWrong := IsRegisteredWrong(cf.Impl); !isWrong {
			add("graded_against[%d] names %q, which is registered as a CORRECT implementation. A "+
				"counterfactual must name an implementation declared wrong", i, cf.Impl)
		}
		switch cf.Kind {
		case "money":
			sawMoney = true
			m, err := parseMinor(cf.MarginMinor)
			if err != nil {
				add("graded_against[%d].margin_minor: %v", i, err)
			} else if m == 0 {
				add("graded_against[%d] is a MONEY kill with margin_minor 0. A money kill with a zero "+
					"margin is a structural kill wearing the wrong label, and DEC-2 §5.2 requirement 7 "+
					"requires a NON-ZERO margin_minor on the money half", i)
			}
		case "structural":
			if cf.MarginMinor != "0" {
				add("graded_against[%d] is a STRUCTURAL kill with margin_minor %q; it is zero by "+
					"construction", i, cf.MarginMinor)
			}
		default:
			add("graded_against[%d].kind %q; this schema knows \"money\" and \"structural\"", i, cf.Kind)
		}
		if len(cf.DivergentCells) == 0 {
			add("graded_against[%d] names no divergent_cells", i)
		}
		for _, c := range cf.DivergentCells {
			if !IsCellField(c) {
				add("graded_against[%d] names divergent cell %q, which THIS COMPARATOR DOES NOT COMPARE "+
					"(it compares: %s). A store that records a kill on a cell nothing compares has "+
					"recorded a claim that is not evidence -- finding T9-F1b",
					i, c, strings.Join(CellFields(), ", "))
			}
			if c == "gl_account_type" {
				add("graded_against[%d] names gl_account_type as a divergent cell. DEC-2 §5.2 "+
					"requirement 7: glAccountType MAY NOT be a perturbation cell, because a red on an "+
					"unstable cell demonstrates that the corpus is not reproducible, not that the "+
					"comparator works", i)
			}
		}
	}
	if v.Class == ClassParity && !sawMoney {
		add("this is a PARITY vector and it names no MONEY kill. DEC-2 §5.2 requirement 7, revision 4: " +
			"the disjunction that made the money half optional is replaced by a conjunction, because a " +
			"ledger corpus whose money cells only ever kill structurally has graded no amount")
	}
	return bad
}

// citationReasons resolves one two-part artefact citation and returns every
// reason it does not.
//
// T233's rule, applied to every ledger vector: (1) the artefact EXISTS and is
// NON-EMPTY; (2) its digest matches; (3) the capture_case_id OCCURS IN ITS BYTES
// or in the .http sidecar beside it.
//
// WHY THE SIDECAR IS ACCEPTED FOR (3), STATED RATHER THAN QUIETLY ALLOWED. A
// JSON response body does not name its own capture case id -- the oracle emitted
// it and knows nothing about our naming. The capture rig writes the id into the
// FILE NAME and into the `.http` block beside it. Requiring the id inside the
// response bytes would be requiring the oracle to cooperate with our filing
// system, which no honest capture can do; requiring it in the sidecar checks the
// thing that is actually checkable -- that the artefact this vector names is the
// one the capture rig filed under that id.
func citationReasons(repoRoot, field, ref, wantDigest, caseID string) []string {
	var out []string
	add := func(f string, a ...any) { out = append(out, fmt.Sprintf(f, a...)) }
	if strings.TrimSpace(ref) == "" {
		add("%s is empty. A vector with no capture behind it has not observed anything", field)
		return out
	}
	if filepath.IsAbs(ref) {
		add("%s %q is ABSOLUTE. A citation must be repo-relative or it resolves against whichever "+
			"checkout the reader happens to stand in", field, ref)
		return out
	}
	abs := filepath.Join(repoRoot, ref)
	st, err := os.Stat(abs)
	if err != nil {
		add("%s %q does not resolve under the graded repository root: %v", field, ref, err)
		return out
	}
	if st.IsDir() {
		add("%s %q is a DIRECTORY, not a capture artefact", field, ref)
		return out
	}
	if st.Size() == 0 {
		add("%s %q is an EMPTY file. An empty artefact resolves and proves nothing", field, ref)
		return out
	}
	raw, rerr := os.ReadFile(abs)
	if rerr != nil {
		add("%s %q is unreadable: %v", field, ref, rerr)
		return out
	}
	sum := sha256.Sum256(raw)
	got := hex.EncodeToString(sum[:])
	if !strings.EqualFold(got, wantDigest) {
		add("%s %q digests to %s and the vector records %s. The artefact has changed since the vector "+
			"was written, so the vector's numbers describe bytes that are no longer there",
			field, ref, got, wantDigest)
	}
	if caseID == "" {
		add("provenance.capture_case_id is empty, so nothing ties %s to a capture case", field)
		return out
	}
	if strings.Contains(string(raw), caseID) {
		return out
	}
	// Fall back to the .http sidecar beside the artefact.
	base := strings.TrimSuffix(abs, filepath.Ext(abs))
	base = strings.TrimSuffix(base, ".req")
	side, serr := os.ReadFile(base + ".http")
	if serr == nil && strings.Contains(string(side), caseID) {
		return out
	}
	if strings.Contains(filepath.Base(abs), caseID) {
		return out
	}
	add("provenance.capture_case_id %q occurs neither in the bytes of %s (%q), nor in the .http sidecar "+
		"beside it, nor in its file name. The citation names an artefact that does not answer to the "+
		"case id it claims", caseID, field, ref)
	return out
}
