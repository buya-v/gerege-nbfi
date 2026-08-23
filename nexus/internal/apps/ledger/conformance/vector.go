// Package conformance is the GL/accounting context's golden-vector schema and
// comparator. It is the SECOND vector schema in this program, and it is a second
// schema on purpose rather than a widening of the first.
//
// DEC-2 §5.2 adopted disposition (a) — "the extension is a SECOND vector schema
// and a SECOND comparator, not a widening of the first" — and gave three reasons
// this package obeys literally:
//
//   - StructuralCellFields()'s safety property in the loanschedule harness is
//     "exactly the non-money cells the comparator actually compares". A union
//     list covering two comparators is a superset of what either compares, which
//     is finding T9-F1b. So this package declares its OWN cell vocabulary, and
//     CellFields() below is DERIVED from the comparator by construction: the
//     comparator appends through recordCell, and the vocabulary is the set
//     recordCell can emit.
//   - sentinelByName in the loanschedule harness returns contract.Err* values
//     imported from the FROZEN DEC-1 contract. A fourth sentinel would mean
//     editing contract.go, which is a DEC-1 amendment and a hard `user` gate.
//     This package imports nothing from nexus/internal/apps/loanschedule and
//     defines its own refusal shape (an ORACLE-OBSERVED HTTP refusal, which is
//     not a contract sentinel and is not confusable with one — DEC-2 P-2).
//   - The loanschedule schema's Request maps onto contract.GenerateRequest.
//     No ledger input has a field there; strict decode rejects every one of them
//     (DEC-2 §5.1 (2)).
//
// WHAT THIS PACKAGE MUST NEVER IMPORT. Not
// nexus/internal/apps/loanschedule/conformance and not
// nexus/internal/apps/loanschedule/contract. The dependency runs the other way:
// the loanschedule harness imports THIS package to route ledger-schema files to
// it. An import back would be a cycle, and — more to the point — it would be the
// widening DEC-2 rejected, arriving by the back door.
//
// WHAT IT SHARES WITH THE FIRST SCHEMA, and it is exactly DEC-2 §5.2's list:
// the store root, the file census, the duplicate-case_id check, the raw-token
// float scan (re-implemented here rather than imported, because importing it
// would be an import of the loanschedule package — the RULE is shared, the code
// is not) and the capability-registry DISCIPLINE (default-deny; see
// capability.go).
package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// SchemaV1 is the only schema string this package accepts.
//
// It is the string DEC-2 §5.2 names: "gerege.ledger.vector/v1".
const SchemaV1 = "gerege.ledger.vector/v1"

// LedgerContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const LedgerContext = "ledger"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
//
// THIS IS DEC-2 PRECONDITION P-9, discharged for the second schema. The
// loanschedule half was discharged by A2-20 (its SchemaContexts(), vector.go);
// the obligation transferred here the moment a second schema existed. The two
// checks are the same statement read in opposite directions — a vector's schema,
// its directory and the comparator that grades it name ONE context — and the
// defect they jointly close is the one A2-19/A2-20/A2-25 reproduced three times:
// copy a promoted parity vector into a new directory, change two strings, and
// the parity count this program quotes as evidence rises by one.
func SchemaContexts() []string {
	return []string{LedgerContext}
}

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a ledger vector file claims to be.
//
// THE CLASS SET IS NOT THE LOANSCHEDULE SET, and DEC-2 preconditions P-2 and P-3
// are why. P-3: "a class an observed non-schedule oracle answer can be filed
// under, since `parity` requires a schedule and `contract-refusal` requires
// oracle.seam == none". P-2: "an expectation shape for an oracle-faithful
// refusal — HTTP status, error code, message text — that is NOT one of the three
// contract sentinels and is NOT confusable with them".
type VectorClass string

const (
	// ClassParity is a ledger vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// ledger parity tally.
	ClassParity VectorClass = "parity"

	// ClassOracleRefusal is P-2 and P-3's answer, and the name is chosen to be
	// unmistakable: this is a refusal the ORACLE ACTUALLY RETURNED and that was
	// CAPTURED — an HTTP status and an error code observed on the wire — not a
	// refusal derived from a contract's normative text.
	//
	// It is deliberately NOT called "contract-refusal". In the loanschedule
	// store that name means the opposite thing: derived from the ratified
	// contract, oracle.seam == "none", no oracle output compared, tallied apart
	// from parity BECAUSE nothing was observed. Here an oracle refusal IS an
	// observation, it carries a capture citation, and it is a parity claim about
	// the port's refusal behaviour. Two classes with opposite provenance rules
	// must not share a name across two schemas in one store.
	ClassOracleRefusal VectorClass = "oracle-refusal"
)

// EntrySide is the DEBIT/CREDIT axis as the oracle spells it on the wire.
//
// The STORED VALUE, never the ordinal, and never a bare integer — DEC-2 §4.8.
// A vector writes "DEBIT" / "CREDIT"; nothing in this schema accepts 1 or 2.
type EntrySide string

const (
	SideDebit  EntrySide = "DEBIT"
	SideCredit EntrySide = "CREDIT"
)

// Valid reports whether s is one of the two sides the oracle emits.
func (s EntrySide) Valid() bool { return s == SideDebit || s == SideCredit }

// Provenance records where an expected value came from.
//
// THE THREE-PART CAPTURE CITATION IS MANDATORY ON EVERY LEDGER VECTOR, not only
// on one carrying an exemption. T233 imposed a resolving three-part citation on
// EXEMPTIONS in the loanschedule store — the artefact exists and is non-empty,
// the capture_case_id occurs in its bytes, and the re-run sentence is non-empty.
// This schema applies the same rule to EVERY parity and oracle-refusal vector,
// because the failure it closes ("a citation that names a file nobody checked
// resolves") is not specific to exemptions, and because this corpus is new
// enough that nothing has to be retro-fitted.
type Provenance struct {
	// Kind is "capture". There is no other admissible value: this schema has no
	// hand-authored and no contract-derived class, so a ledger vector that was
	// not observed from the oracle has no home here at all.
	Kind string `json:"kind"`

	// CaptureRef is the repo-relative path of the artefact carrying the RESPONSE
	// bytes this vector transcribes. PART ONE of the citation.
	CaptureRef string `json:"capture_ref"`

	// CaptureSHA256 is that artefact's digest, lower-case hex.
	CaptureSHA256 string `json:"capture_sha256"`

	// CaptureCaseID is the capture case id. PART TWO: it must OCCUR IN THE BYTES
	// of the artefact tree cited (the .http sidecar, since a JSON response body
	// does not name its own case id — see grounding.go for exactly which file is
	// searched and why that is the honest place to look).
	CaptureCaseID string `json:"capture_case_id"`

	// RequestCaptureRef is the artefact carrying the REQUEST bytes.
	//
	// DEC-2 brief item (2), A2-30: "the 147 pre-existing observations have NO
	// .req, so only the 44 new HTTP captures record wire bytes … a vector citing
	// a record with no request block is graded on LESS". Every vector in this
	// corpus cites one — either a `.req` body artefact for a POST, or the
	// `.http` request block for a GET, which for a body-less request IS the
	// complete wire request.
	RequestCaptureRef string `json:"request_capture_ref"`

	// RequestCaptureSHA256 is that artefact's digest.
	RequestCaptureSHA256 string `json:"request_capture_sha256"`

	// RequestCaptureCaseID is the request artefact's OWN capture case id.
	//
	// IT IS A SEPARATE FIELD BECAUSE THE TWO ARTEFACTS ARE SEPARATE CAPTURES.
	// A read-back vector cites the POST that created the entry and the GET that
	// read it back, and those are two case ids (A2-343 and A2-347, for example).
	// Checking one id against both artefacts would either pass vacuously on the
	// wrong one or fail on the right one, and a citation check that cannot be
	// satisfied by a correct citation is a check somebody will delete.
	RequestCaptureCaseID string `json:"request_capture_case_id"`

	// RerunInvariant is PART THREE: the sentence stating what re-running this
	// capture would have to reproduce for the vector to remain true. It must be
	// non-empty. It is prose and is never parsed — its job is to make the
	// promoter write down what would falsify the vector.
	RerunInvariant string `json:"rerun_invariant"`

	// Citation is free prose naming the task and the reasoning.
	Citation string `json:"citation"`
}

// OracleStamp records the reference-oracle build and seam.
type OracleStamp struct {
	FineractCommit string `json:"fineract_commit"`

	// Seam is one of DEC-2 §4.2 G-01's three: ledger_rest_admin,
	// ledger_rest_posting, ledger_db_readback. An absent or unknown seam
	// REFUSES — default-deny, §4.10.
	Seam string `json:"seam"`

	CapturedAt string `json:"captured_at"`
}

// Currency is the currency the entry is denominated in.
//
// DEC-2 §4.2 G-07 binds ONLY a vector that asserts a money cell, and every
// vector in this schema asserts one, so it binds all of them: Code == "MNT" and
// MinorUnitDigits == 2.
type Currency struct {
	Code            string `json:"code"`
	MinorUnitDigits int    `json:"minor_unit_digits"`
}

// Account is one GL account as the oracle's own capture recorded it.
//
// IT IS DATA, NOT AN EXPECTATION. DEC-2 §4.5: "the chart of accounts is DATA,
// not code — G-9, CLOSED". These rows are the input the port resolves AGAINST;
// they are transcribed from a capture and they are never graded, because grading
// a value the vector handed the implementation is the circularity
// registry.go:329-336 forbids in the first store.
//
// NO Classification FIELD EXISTS HERE, AND THAT IS DELIBERATE. See Vector.Note
// and the ExcludedFields doc comment: glAccountType is unstable across captures
// and this schema does not carry it in either direction.
type Account struct {
	ID   int64  `json:"id"`
	Code string `json:"gl_code"`
	Name string `json:"name"`

	// Usage is "DETAIL" or "HEADER" — DEC-2 §4.2 G-10, stored value never
	// ordinal (§4.8).
	Usage string `json:"usage"`

	// ManualEntriesAllowed is acc_gl_account.manual_journal_entries_allowed.
	// It is the input the manual-adjustment refusal rule reads.
	ManualEntriesAllowed bool `json:"manual_entries_allowed"`

	// Disabled is acc_gl_account.disabled.
	Disabled bool `json:"disabled"`
}

// RequestLeg is one leg of the posting AS REQUESTED, carrying the oracle's own
// major-unit decimal text and NOT a minor-unit integer.
//
// THIS IS THE HALF THAT MAKES THE MONEY CELL NON-CIRCULAR. DEC-2 §4.3
// normative consequence 1: "Read the literal characters, never a decoded
// number", and the conversion from major-unit decimal text to int64 minor units
// happens at the adapter edge. The vector supplies the CHARACTERS; the
// implementation performs the CONVERSION; the expectation records the INTEGER.
// A port that decodes through float64, truncates residue, or drops the minor
// digits produces a different integer and the comparator says so.
type RequestLeg struct {
	AccountID int64     `json:"gl_account_id"`
	Side      EntrySide `json:"entry_side"`

	// AmountMajorText is the oracle's emitted characters, exactly. For a POST
	// it is the request body's own token; for a read-back it is the response's.
	AmountMajorText string `json:"amount_major_text"`
}

// Request is the ledger input shape DEC-2 precondition P-1 specifies: "a request
// shape covering product id, product type, accounting rule, slot family, slot
// code, payment type id and seam".
//
// ALL SEVEN ARE PRESENT. The product/slot five are populated on an
// ACCOUNTING-PATH vector (an entry the oracle's own loan accounting produced)
// and are zero/empty on a MANUAL entry, where no product and no slot took part.
// They are not dropped for the manual case: a schema that omits a field for the
// case that does not use it cannot express the case that does.
type Request struct {
	// ProductID is the loan product the entry's accounting path resolved
	// through, or 0 on a manual entry.
	//
	// DEC-2 brief item (3) / G-10 option (c): a vector may be taken only from a
	// product the oracle would STILL ACCEPT today. Products 22, 23, 24, 27 and
	// 28 are INADMISSIBLE — observed 403 by re-sending each mapping
	// (A2-300..A2-315) — because GL account 2 was retyped ASSET->INCOME
	// underneath their live mappings. admit.go enforces this as a DENYLIST, not
	// as a comment.
	ProductID int64 `json:"product_id"`

	// ProductType is the stored-value spelling, "LOAN" — DEC-2 §4.2 G-02.
	ProductType string `json:"product_type"`

	// AccountingRule is the stored-value spelling: "CASH_BASED" or
	// "ACCRUAL_PERIODIC" — G-03. "ACCRUAL_UPFRONT" is refused for exactly one
	// reason and this schema states it where a reader will meet it: NO CAPTURE
	// EXISTS AT accountingRule = 4.
	AccountingRule string `json:"accounting_rule"`

	// SlotFamily is "CashLoanSlot" or "AccrualLoanSlot" — G-05. A bare integer
	// cannot select a family (DEC-2 §2.1) and this schema does not accept one.
	SlotFamily string `json:"slot_family"`

	// SlotCode is the placeholder code, or 0 on a manual entry.
	SlotCode int32 `json:"slot_code"`

	// PaymentTypeID is nil where the entry did not resolve through a payment
	// type. G-06 refuses a nil payment type on FUND_SOURCE (slot 1) because the
	// oracle's own behaviour there is genuinely undecided and no capture
	// separates the two readings.
	PaymentTypeID *int64 `json:"payment_type_id"`

	// Seam duplicates OracleStamp.Seam at the request level because P-1 names it
	// as a request field. admit.go requires the two to agree, so the duplication
	// cannot drift.
	Seam string `json:"seam"`

	OfficeID      int64    `json:"office_id"`
	Currency      Currency `json:"currency"`
	TransactionID string   `json:"transaction_id"`

	// ManualEntry is acc_gl_journal_entry.manual_entry.
	ManualEntry bool `json:"manual_entry"`

	// ---------------------------------------------------------------------
	// THE OPENING-BALANCE INPUTS — T289's date strategy (c), applied to a
	// STATE precondition instead of a date. [T294]
	// ---------------------------------------------------------------------
	//
	// T289's conclusion, reached over the closure/future-date captures and
	// binding on every refusal promoted after it: a refusal whose precondition
	// lives in AMBIENT ORACLE STATE and not in the request "will silently stop
	// testing what it claims"; the fix is to LIFT THE PRECONDITION INTO THE
	// VECTOR AS AN INPUT and never re-fire the probe at the oracle. It rejected
	// pinning the oracle's state and rejected recomputing the input at run time,
	// for reasons that transfer to this refusal unchanged.
	//
	// POST /journalentries?command=defineOpeningBalance
	// [JournalEntriesApiResource.java:211-212] reaches
	// defineOpeningBalance:703, which resolves the FinancialActivityAccount for
	// type 300 at :708-709 and then calls
	// validateJournalEntriesArePostedBefore(contraId) at :717. That guard
	// [:810-816] refuses whenever findNonContraTransactionIds(contraId) is
	// non-empty — a fact about the TENANT, not about the request. The three
	// fields below are that fact, made an input.
	//
	// EVERY EXISTING VECTOR LEAVES ALL THREE AT THEIR ZERO VALUES and admit.go
	// requires exactly that of a vector whose Command is empty, so a
	// manual-posting vector cannot acquire opening-balance semantics by
	// accident.

	// Command is the wire's `?command=` query parameter as a STORED VALUE
	// (DEC-2 §4.8 — never an ordinal, never a bool). Empty means the plain
	// create path, which is what every capture before T294 exercised.
	//
	// DEFAULT-DENY: admit.go admits "" and "defineOpeningBalance" and nothing
	// else, because those are the only two the corpus has observed.
	Command string `json:"command,omitempty"`

	// ContraGLAccountID is the GL account the financial-activity type 300
	// mapping resolves to — the `contraId` of :709. It is a FOREIGN KEY to
	// acc_gl_account.id, transcribed from
	// acc_gl_financial_activity_account.gl_account_id. It is not an amount, it
	// is never summed, and nothing in this harness treats it as money.
	//
	// IT IS AN INPUT AND NOT A CONVENIENCE. If the mapping does not resolve,
	// findByFinancialActivityTypeWithNotFoundDetection throws at :708 and the
	// oracle returns a DIFFERENT refusal, so a vector that does not record which
	// mapping was in force has not recorded which refusal it observed.
	//
	// THE NAME DELIBERATELY DOES NOT CONTAIN "BALANCE", AND THAT IS A FIX, NOT
	// AN EVASION. T294 first called it `OpeningBalanceContraAccountID` —
	// Fineract's own global-configuration name for the mapping is
	// `office-opening-balances-contra-account` — and the HARD ledger-invariants
	// guard refused the whole run on it (class I3-FIELD-WRITE,
	// `.softhouse/guards/ledgerguard/main.go`, whose surface is a case-
	// insensitive /balance/ over the identifier). The guard was RIGHT to fire
	// and the code was wrong: a field holding an ACCOUNT ID must not wear a
	// BALANCE's name. The precedent is LoanScheduleTreeRel, renamed by T166
	// because "a name that lies is how this hid". Note the direction — that
	// guard's own CANNOT-CATCH item 2 warns that RENAMING A BALANCE defeats it;
	// this is the opposite move, renaming a NON-balance so it stops reading as
	// one, and it removes a trap for the next task rather than setting one.
	ContraGLAccountID int64 `json:"contra_gl_account_id,omitempty"`

	// PostedNonContraTransactionIDs is findNonContraTransactionIds(contraId) as
	// the oracle itself reported it, transcribed from the refusal body's
	// errors[0].args.
	//
	// THE LIST AND NOT A BOOLEAN, for one reason: the oracle emitted the list,
	// and a vector that recorded `true` would be recording this promoter's
	// READING of the wire rather than the wire. The port is graded on the
	// PREDICATE (non-empty ⇒ refuse), which is what :812's
	// CollectionUtils.isEmpty computes; the members are evidence that the
	// predicate had something to be non-empty about.
	PostedNonContraTransactionIDs []string `json:"posted_non_contra_transaction_ids,omitempty"`

	// TransactionAmountMajorText is the amount THE CALLER ASKED FOR, in the
	// caller's own characters, taken from the recorded request body. Empty where
	// the request carried no single total.
	//
	// IT EXISTS TO MAKE I-2 INDEPENDENT OF I-1, and without it the two are the
	// same equation. On a journal entry with one leg on one side and N on the
	// other, "splits sum to the whole" reads whole == Σ splits where the whole IS
	// the lone leg — which is character-for-character what "debits equal credits"
	// asserts on that shape. Two green lines, one assertion, and no
	// implementation could ever fail one and pass the other. That is not a
	// vacuous check (it CAN fail) but it is a DEPENDENT one, and reporting it as
	// a second invariant would be counting one assertion twice.
	//
	// A LOAN REPAYMENT HAS A REAL SECOND TERM: the caller POSTs
	// {"transactionAmount": 300000} and the oracle's accounting produces credit
	// legs of 270450.58 + 22049.42 + 7500.00. Asserting that those splits sum to
	// THE AMOUNT THE CALLER ASKED FOR ties the journal entry to the request that
	// produced it, and a port whose entry balances internally while splitting a
	// different total fails I-2 and passes I-1.
	//
	// A MANUAL entry has no such term — its request body enumerates both sides —
	// so this field is empty there, I-2 falls back to the leg-derived shape, and
	// the report SAYS the assertion is dependent rather than letting a reader
	// count it as independent evidence.
	TransactionAmountMajorText string `json:"transaction_amount_major_text"`

	// Accounts is the chart rows the legs point at — DATA (§4.5), transcribed
	// from a capture, never graded.
	Accounts []Account `json:"accounts"`

	// Legs is the posting as requested, in the oracle's own major-unit text.
	Legs []RequestLeg `json:"legs"`
}

// ExpectLeg is one leg of the EXPECTED entry.
type ExpectLeg struct {
	AccountID int64     `json:"gl_account_id"`
	Code      string    `json:"gl_account_code"`
	Side      EntrySide `json:"entry_side"`

	// AmountMinor is THE GRADED MONEY CELL: an integer count of minor units, as
	// a JSON STRING. DEC-2 §4.3 normative consequence 4 and T186(c): "a stored
	// ledger vector carries money as a JSON STRING of integer minor units, never
	// as a JSON number".
	AmountMinor string `json:"amount_minor"`

	// AmountMajorText is the oracle's own emitted characters, kept as a
	// TRANSCRIPTION CROSS-CHECK ONLY and never as a grading standard — the
	// pairing DEC-2 §4.3 mandates, copied from the loanschedule store's
	// principal_minor / principal_major_text.
	AmountMajorText string `json:"amount_major_text"`

	// ExcludedFields names cells of THIS LEG that the capture recorded but this
	// vector declines to grade, with the reason living in Vector.Note.
	//
	// THE ONLY ADMISSIBLE MEMBER TODAY IS "gl_account_type", and admit.go
	// enforces that. A2-26 observed the identical journal-entry row rendering
	// ASSET in A2-088 (2026-08-21) and INCOME in A2-320 (2026-08-22), every
	// other cell byte-identical, six diff lines all inside glAccountType, WITH
	// NO ENTRY EDITED — because the field projects the ACCOUNT'S CURRENT
	// classification rather than the entry's, and GL account 2 was retyped
	// underneath it (G-10). A vector grading that cell would go RED on a
	// GL-account edit that touched no journal entry.
	//
	// An open-ended exclusion list would be a hole: any inconvenient cell could
	// be named and the corpus would quietly stop grading it. So the list is
	// CLOSED to one member, and widening it is a source edit a reviewer sees.
	ExcludedFields []string `json:"excluded_fields"`
}

// Refusal is the oracle-faithful refusal shape — DEC-2 precondition P-2.
//
// It is deliberately unlike a contract sentinel in every respect: it carries an
// HTTP status, the oracle's own globalisation code and the oracle's own message
// text, none of which a contract sentinel has, and it is compared as three
// separate cells so that a port matching the status while inventing the code is
// caught.
type Refusal struct {
	HTTPStatus int    `json:"http_status"`
	Code       string `json:"code"`
	Message    string `json:"message"`
}

// Expect is what the implementation must produce.
type Expect struct {
	// Kind is "journal-entry" or "refusal".
	Kind string `json:"kind"`

	HTTPStatus int `json:"http_status"`

	// Legs is populated on kind == "journal-entry" and empty on a refusal.
	Legs []ExpectLeg `json:"legs"`

	// TotalDebitsMinor and TotalCreditsMinor are DERIVED money cells: the
	// implementation sums its own converted legs and the comparator checks the
	// totals independently of the per-leg cells.
	//
	// They are not redundant with the legs. A port that converts every leg
	// correctly and then sums into a 32-bit accumulator, or that nets a negative
	// leg, matches every per-leg cell and diverges here.
	TotalDebitsMinor  string `json:"total_debits_minor"`
	TotalCreditsMinor string `json:"total_credits_minor"`

	// Refusal is populated on kind == "refusal" and zero otherwise.
	Refusal Refusal `json:"refusal"`
}

// Counterfactual names a wrong implementation this vector kills.
//
// DEC-2 §5.5 and precondition P-10. P-10 is the one this schema most has to
// respect: "graded_against is a DECLARATIVE record and does not execute
// anything … without this, the bottom-left cell is satisfiable by writing a JSON
// row". So Impl below is not prose — it must name an implementation REGISTERED
// in this package's registry, admit.go refuses a name that is not registered,
// and `-ledger-impl <name>` actually runs it.
type Counterfactual struct {
	// Impl is the registered name of the wrong implementation.
	Impl string `json:"impl"`

	// Kind is "money" or "structural".
	Kind string `json:"kind"`

	// MarginMinor is the minor-unit margin by which this vector kills that
	// implementation. It is "0" on a structural kill BY CONSTRUCTION and must be
	// non-zero on a money kill — DEC-2 §5.2 requirement 7: "reported as a money
	// kill with a non-zero margin_minor".
	MarginMinor string `json:"margin_minor"`

	// DivergentCells names the cells that differ. A cell named here that the
	// same vector EXCLUDED is INADMISSIBLE — finding T9-F1b, ported: the store
	// may not record a claim that is not evidence.
	DivergentCells []string `json:"divergent_cells"`

	Note string `json:"note"`
}

// Vector is one ledger file in the store.
type Vector struct {
	Schema string      `json:"schema"`
	CaseID string      `json:"case_id"`
	Ctx    string      `json:"context"`
	Class  VectorClass `json:"class"`
	Title  string      `json:"title"`

	// DEC2Revision is DEC-2 precondition P-7, decided.
	//
	// THE QUESTION P-7 ASKS: "what dec1_revision a NON-loanschedule vector
	// declares, given that it is checked per-vector against the single store
	// pin. A ledger vector asserting dec1_revision: 12 is asserting a
	// LOANSCHEDULE contract revision, which is semantically wrong."
	//
	// THE DECISION TAKEN HERE, with the alternative recorded: a ledger vector
	// declares `dec2_revision` and NEVER `dec1_revision`, and it is checked
	// against a pin in this package's own pin file rather than against
	// PIN.json's dec1_revision. Rejected alternative: reuse dec1_revision with a
	// note. That would put a DEC-1 revision number on a DEC-2 artefact, which is
	// precisely the semantic error P-7 names, and it would couple this corpus's
	// re-stamping to an amendment of the other context's contract.
	//
	// It carries NO contract DIGEST, and that is not an omission. DEC-2 §1.1:
	// this ADR "does not create or freeze a Go file, and could not"; there is no
	// counterpart file to pin, and there will not be one until a ledger contract
	// is frozen — a separate, later gate.
	DEC2Revision int `json:"dec2_revision"`

	// Note is free prose, never graded and never parsed.
	//
	// IT IS WHERE THE INSTABILITY RECORD LIVES, and DEC-2's brief for A2-15 is
	// explicit that a handoff is not good enough: "whichever it picks, the
	// instability must be recorded in the vector's OWN note — not only in a
	// handoff". admit.go therefore REQUIRES this field to be non-empty and, on a
	// vector that excludes gl_account_type, to actually mention it.
	Note string `json:"_note"`

	CapabilitiesRequired []string         `json:"capabilities_required"`
	Provenance           Provenance       `json:"provenance"`
	Oracle               OracleStamp      `json:"oracle"`
	Request              Request          `json:"request"`
	Expect               Expect           `json:"expect"`
	GradedAgainst        []Counterfactual `json:"graded_against"`

	// InvariantExemptions exists so that a vector CANNOT declare one silently.
	//
	// It is typed, decoded, and then REFUSED if non-empty. The loanschedule
	// harness has a whole grounding classifier behind its exemptions (T222,
	// T225, T230, T233) and this schema has none, so admitting an exemption here
	// would switch an invariant off with nothing at all checking that the thing
	// it excuses is visible in the record. Default-deny.
	//
	// Omitting the field instead would be worse, and that is why it is here: a
	// vector carrying `invariant_exemptions` would then die at strict decode
	// with `unknown field`, which reads as a typo rather than as a policy, and
	// the census below could not count the population at all.
	InvariantExemptions []Exemption `json:"invariant_exemptions"`

	// Path is the file the vector was loaded from, relative to the store root.
	Path string `json:"-"`
}

// Exemption is the shape a ledger vector would use to switch an invariant off,
// if this schema admitted one. It does not. See Vector.InvariantExemptions.
type Exemption struct {
	Invariant string `json:"invariant"`
	Reason    string `json:"reason"`
}

// Context returns the store context this vector claims.
func (v *Vector) Context() string { return v.Ctx }

// LoadError is one file that could not be read as a ledger vector.
type LoadError struct {
	Path string
	Err  error
}

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
//
// IT IS A RE-IMPLEMENTATION, NOT AN IMPORT, and the reason is the package
// boundary this file's doc comment states: importing the loanschedule harness's
// copy would make this package depend on the schema it exists to be independent
// of. The RULE is shared; sharing the code would not be sharing a rule, it would
// be a dependency.
//
// It runs BEFORE any typed decoding, so a float in a field the typed shape
// ignores is still caught.
func RejectFloatTokens(raw []byte) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	for {
		tok, err := dec.Token()
		if err != nil {
			if err.Error() == "EOF" {
				return nil
			}
			return fmt.Errorf("scanning for float tokens: %w", err)
		}
		n, ok := tok.(json.Number)
		if !ok {
			continue
		}
		s := n.String()
		if strings.ContainsAny(s, ".eE") {
			return fmt.Errorf(
				"FLOAT TOKEN %q in ledger vector JSON: every number in a vector file must be an integer, "+
					"and every monetary value must be an integer STRING in minor units "+
					"(DEC-2 §4.3 consequence 4, T186 category (c))", s)
		}
	}
}

// schemaProbe is the minimal shape used to decide WHICH schema a file claims,
// without decoding it as either.
type schemaProbe struct {
	Schema string `json:"schema"`
}

// DeclaresLedgerSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
//
// THIS IS THE ROUTING PREDICATE, and it is deliberately the weakest possible
// test: it decodes ONE field, non-strictly, and answers a yes/no question. It
// must not validate, because a MALFORMED ledger vector has to reach the ledger
// loader and be reported there BY NAME, not fall back to the other schema's
// loader and be reported as an unknown field.
//
// It returns false for anything that is not a JSON object, so a truncated or
// non-JSON file stays with the caller — which is correct: the first schema's
// loader will report it, the run is unusable either way, and neither loader
// silently drops it.
func DeclaresLedgerSchema(raw []byte) bool {
	var p schemaProbe
	if err := json.Unmarshal(raw, &p); err != nil {
		return false
	}
	return p.Schema == SchemaV1
}

// FileDeclaresLedgerSchema is DeclaresLedgerSchema over a path. An unreadable
// file is NOT a ledger file: it stays with the caller, which reports it.
func FileDeclaresLedgerSchema(absPath string) bool {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return false
	}
	return DeclaresLedgerSchema(raw)
}

// LoadVector reads and strictly decodes one ledger vector file.
//
// Two passes, for the same reason the first schema uses two: the raw token walk
// rejects any non-integer JSON number ANYWHERE in the document before any typed
// decoding, so a float in a field the typed shape ignores is still caught; then
// a typed decode with unknown fields disallowed, so a misspelled field is an
// error rather than a silently dropped input.
func LoadVector(absPath, relPath string) (*Vector, error) {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return nil, err
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var v Vector
	if err := dec.Decode(&v); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("decode: trailing content after the vector object")
	}
	v.Path = relPath
	return &v, nil
}

// LoadStore walks the store root and loads every ledger-schema .json under it.
//
// contextFilter, when non-empty, selects a single context directory. A filter
// naming a context this schema does not own yields zero ledger vectors, which is
// not an error here — the loanschedule half of the run reports its own emptiness.
//
// THE DUPLICATE-case_id CENSUS IS TAKEN OVER THE WHOLE LEDGER POPULATION, BEFORE
// THE FILTER, for the reason T123 established in the first store: the filter
// narrows what is GRADED, never what is CHECKED, and a store defect visible from
// one angle and not another is worse than one always visible.
//
// IT DOES NOT DEDUPLICATE ACROSS SCHEMAS, and it must not: the two case_id
// spaces are separate namespaces belonging to separate comparators. The
// cross-schema check that DOES matter — a file claiming one schema sitting in
// the other's directory — is closed by SchemaContexts() on both sides.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, nil, fmt.Errorf("ledger vector store %s: %w", storeRoot, err)
	}
	var all, graded []*Vector
	var loadErrs []LoadError
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		ctx := e.Name()
		selected := contextFilter == "" || ctx == contextFilter
		dir := filepath.Join(storeRoot, ctx)
		files, ferr := os.ReadDir(dir)
		if ferr != nil {
			return nil, nil, ferr
		}
		for _, f := range files {
			if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
				continue
			}
			abs := filepath.Join(dir, f.Name())
			if !FileDeclaresLedgerSchema(abs) {
				continue
			}
			rel := filepath.Join(ctx, f.Name())
			v, verr := LoadVector(abs, rel)
			if verr != nil {
				// NOT SKIPPED, EVEN OUTSIDE THE FILTER. A file that declares
				// this schema and cannot be read is this loader's problem
				// wherever it sits: the first schema's loader has already
				// handed it over, so if this one drops it too the file is on
				// disk, unloaded, and reported by nobody. That is driver
				// finding D-5 exactly.
				loadErrs = append(loadErrs, LoadError{Path: rel, Err: verr})
				continue
			}
			all = append(all, v)
			if selected {
				graded = append(graded, v)
			}
		}
	}
	sortVectors(all)
	sortVectors(graded)
	if derr := DuplicateCaseIDs(all); derr != nil {
		return graded, loadErrs, derr
	}
	return graded, loadErrs, nil
}

// LedgerFilePaths returns the store-relative paths of every .json under
// storeRoot that declares this schema.
//
// It exists for the FILE CENSUS in the first schema's harness, which requires
// every .json under the store root to be accounted for by somebody. Without
// this, promoting a ledger vector would make the census refuse the run — the
// census being right, and the promotion having failed to tell it anything.
func LedgerFilePaths(storeRoot string) ([]string, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := filepath.Join(storeRoot, e.Name())
		files, ferr := os.ReadDir(dir)
		if ferr != nil {
			return nil, ferr
		}
		for _, f := range files {
			if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
				continue
			}
			if FileDeclaresLedgerSchema(filepath.Join(dir, f.Name())) {
				out = append(out, filepath.ToSlash(filepath.Join(e.Name(), f.Name())))
			}
		}
	}
	sort.Strings(out)
	return out, nil
}

// DuplicateCaseIDs refuses a ledger population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	seen := map[string][]string{}
	for _, v := range vs {
		seen[v.CaseID] = append(seen[v.CaseID], v.Path)
	}
	var ids []string
	for id, paths := range seen {
		if len(paths) > 1 {
			sort.Strings(paths)
			ids = append(ids, fmt.Sprintf("%s (%s)", id, strings.Join(paths, ", ")))
		}
	}
	if len(ids) == 0 {
		return nil
	}
	sort.Strings(ids)
	return fmt.Errorf(
		"LEDGER STORE DEFECT: case_id declared more than once: %s. A case_id is how a vector is cited "+
			"in a handoff, a gate and a review; two files answering to one id make every citation ambiguous",
		strings.Join(ids, "; "))
}

func sortVectors(vs []*Vector) {
	sort.Slice(vs, func(i, j int) bool {
		if vs[i].Ctx != vs[j].Ctx {
			return vs[i].Ctx < vs[j].Ctx
		}
		if vs[i].CaseID != vs[j].CaseID {
			return vs[i].CaseID < vs[j].CaseID
		}
		return vs[i].Path < vs[j].Path
	})
}
