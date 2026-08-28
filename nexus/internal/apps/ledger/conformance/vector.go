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

	// ClassDivergence is a RECORDED, GATED PARITY DIVERGENCE: the reference
	// oracle ACCEPTED a request this port REFUSES. It is the third class, it was
	// added by T360 for G-19, and every word of the sentence above is load
	// bearing.
	//
	// WHY IT IS NOT `parity`. A parity vector says "the oracle produced THIS and
	// the port must produce it too". Here the port produces NOTHING: it refuses.
	// There is no port-side money value to compare, so there is nothing to put
	// in expect.legs[].amount_minor, and — this is the whole reason the class
	// exists — THERE COULD NOT BE. The oracle accepted `100.125000` in a
	// currency whose declared minor unit is 2. `amount_minor` is an int64 count
	// of minor units (parseMinor, ledger.MinorUnits) and NO int64 equals
	// 100.125. `10012` and `10013` are both numbers neither system produced.
	// T352 wrote `10013` into a candidate vector to find out what the harness
	// would do with it and correctly declined to promote the file; T359
	// reproduced the HARNESS-ERROR and diagnosed the routing half of it.
	//
	// WHY IT IS NOT `oracle-refusal`. That class means THE ORACLE REFUSED and
	// the port must refuse identically. Here the oracle ACCEPTED. Filing this
	// under that name would record the opposite of what was observed.
	//
	// WHAT IT GRADES, AND WHAT IT DELIBERATELY DOES NOT. It grades TWO
	// STRUCTURAL CELLS about the PORT — that the port refused at all, and that
	// its refusal carries the declared stable marker — and it grades ZERO MONEY
	// CELLS, because there is no port-side amount and the oracle-side amount is
	// unrepresentable. The oracle's side is carried as OracleAcceptance: raw
	// observed CHARACTERS, byte-checked against the cited capture, never parsed,
	// never converted, never compared.
	//
	// THE COUNTING RULE, AND IT IS ASYMMETRIC ON PURPOSE (see Summary):
	// a divergence PASS is counted in `ledger divergence PASS` and NOWHERE in
	// `ledger parity PASS` — the port did not match the oracle, so it gets no
	// parity credit — while a divergence FAIL is ALSO added to `ledger parity
	// FAIL`, so the bar goes red. A divergence is never evidence FOR the port
	// and always evidence AGAINST it when it moves.
	ClassDivergence VectorClass = "divergence"
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

	// SlotCode is the acc_product_mapping.financial_account_type this leg
	// ARRIVED THROUGH, or 0 on a leg no slot took part in. [T391]
	//
	// -----------------------------------------------------------------------
	// WHY THE SLOT IS PER LEG WHEN P-1 PUT IT ON THE REQUEST
	// -----------------------------------------------------------------------
	//
	// Request.SlotCode exists and names ONE slot. That was right for the shape
	// P-1 imagined and it is not enough for the shape the oracle actually
	// produced: ONE ACCRUAL JOURNAL TRANSACTION SPANS SIX SLOTS. L29 debits
	// INTEREST_RECEIVABLE (7), FEES_RECEIVABLE (8) and PENALTIES_RECEIVABLE (9)
	// and credits INTEREST_ON_LOANS (3), INCOME_FROM_FEES (4) and
	// INCOME_FROM_PENALTIES (5), on one transaction id.
	//
	// capabilities-ledger.json's `ledger.slot.resolution` row named this exact
	// obstruction and named it correctly: "doing so needs a request shape whose
	// slot_code names ONE slot, and every entry in the multi-leg corpus spans
	// several". The answer is not to pick one leg; it is to put the slot where
	// the slot is, which is on the leg.
	//
	// Request.SlotCode is NOT removed and is NOT repurposed. admit.go requires
	// it to be 0 on a vector that carries per-leg slot codes, with the reason
	// stated there: two places to say which slot an entry used is two places
	// that can disagree, and the entry-level one cannot express six.
	//
	// -----------------------------------------------------------------------
	// A LEG CARRIES EXACTLY ONE OF: AN ACCOUNT ID, OR A SLOT CODE
	// -----------------------------------------------------------------------
	//
	// THIS IS THE WHOLE NON-CIRCULARITY ARGUMENT FOR THE SLOT CELLS, and it is
	// the same argument the money cells rest on. A MANUAL leg names the account
	// the poster chose, because that is what a manual posting is. An
	// ACCOUNTING-PATH leg names the SLOT and NOT the account: the account is
	// what the implementation must RESOLVE, through the product's own observed
	// acc_product_mapping rows (Request.ProductMappings) and the slot family the
	// product's accounting rule selects.
	//
	// So on an accounting-path vector `expect.legs[].gl_account_id` and
	// `expect.legs[].gl_account_code` stop being copies of an input and become
	// OUTPUTS. A port that resolves slot 8 to the wrong account now differs from
	// the expectation; before this field existed it could not, because the
	// vector handed it the answer.
	SlotCode int32 `json:"slot_code,omitempty"`
}

// ProductMapping is ONE OBSERVED acc_product_mapping row: the (product, slot) ->
// GL account fact the oracle itself holds. [T391]
//
// IT IS AN INPUT, TRANSCRIBED, NEVER DERIVED. The rows a vector carries are read
// off `GET /loanproducts/{id}`'s `accountingMappings` at the contract boundary
// the vector declares, cross-checked against a read-only SELECT over
// acc_product_mapping. Nothing in this harness computes one.
//
// WHY THE WHOLE TABLE AND NOT JUST THE SIX ROWS THE ENTRY USED. Because the
// resolution the port performs is a LOOKUP IN A TABLE, and a table containing
// only the rows the answer needs is not a lookup, it is the answer. Carrying the
// product's complete mapping means a port that mis-keys — that reads the row for
// slot 7 when asked for slot 8, or that takes the first row, or that ignores the
// key entirely — lands on a DIFFERENT account and the comparator says so.
//
// THE FAMILY IS NOT IN THE KEY, AND THAT IS THE TRAP THIS TYPE EXISTS INSIDE.
// acc_product_mapping is keyed on (product_id, product_type, financial_account_type)
// and NOT on the accounting rule, so the CASH enum and the ACCRUAL enum share one
// integer space with different meanings at 7, 8, 9, 22, 24, 25 and 26. A port can
// therefore resolve the RIGHT ACCOUNT while naming the WRONG SLOT. That is
// exactly T242's error (A2-34 F-4) in port form, it is registered as
// `ledger-wrong-slot-family-blind`, and the only cell that catches it is
// ExpectLeg.SlotName.
type ProductMapping struct {
	// SlotCode is acc_product_mapping.financial_account_type. It is an integer
	// SLOT CODE and nothing in this harness treats it as money.
	SlotCode int32 `json:"slot_code"`

	// GLAccountID is acc_product_mapping.gl_account_id.
	GLAccountID int64 `json:"gl_account_id"`
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

	// ---------------------------------------------------------------------
	// THE DATE INPUTS — T289's date strategy (c), applied to the DATES it was
	// written for. [T295]
	// ---------------------------------------------------------------------
	//
	// T294 applied T289's rule to a STATE precondition. These three fields are
	// the same rule applied to the case that produced it. T289's finding, over
	// T287's four closure/future-date captures, was that all four are
	// NON-PROMOTABLE AS LITERAL-DATE VECTORS: the business date and the closing
	// date lived in PROSE, so the vector's truth depended on what day it was
	// read, and "a vector whose truth depends on today's date is a vector that
	// turns into a false parity claim on a specific morning with nobody
	// watching".
	//
	// AND THE FAILURE IS NOT QUIET. Every one of T287's four probes is an
	// otherwise VALID, BALANCED, POSTABLE manual journal entry on
	// manual-permitted DETAIL accounts; the only thing refusing it is a
	// precondition in the ORACLE. When the precondition lapses the request does
	// not stop being interesting — IT BECOMES A SUCCESSFUL WRITE, and a posted
	// journal entry cannot be deleted (P-92: "a probe whose safety comes from an
	// EXTERNAL PRECONDITION rather than from its own content is a loaded
	// weapon"). Lifting the precondition into the vector is therefore not a
	// tidiness move: it is what lets the vector be RE-GRADED against a port
	// forever without ever being RE-FIRED at the oracle.
	//
	// WHAT THE THREE FIELDS ARE, in the source's own terms
	// [VERIFIED: JournalEntryWritePlatformServiceJpaRepositoryImpl.java:626-640,
	// pinned 426a23544, reached from :157 on the create path and from :724 on
	// the defineOpeningBalance path]:
	//
	//	:628  final LocalDate transactionDate = command.getTransactionDate();
	//	:629  if (DateUtils.isDateInTheFuture(transactionDate)) -> FUTURE_DATE
	//	:634  final GLClosure latestGLClosure =
	//	        this.glClosureRepository.getLatestGLClosureByBranch(command.getOfficeId());
	//	:635  if (latestGLClosure != null) {
	//	:636    if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate))
	//	          -> ACCOUNTING_CLOSED
	//
	// TransactionDate is the request's own field. BusinessDate is what
	// DateUtils.isDateInTheFuture reads — isAfterBusinessDate ->
	// isAfter(date, getBusinessLocalDate()) [DateUtils.java:258-264] — and it is
	// TENANT AMBIENT STATE, not a request field. LatestClosingDate is what :634
	// reads, and it is TENANT AMBIENT STATE too. Both are here so that a port is
	// graded on the PREDICATE and never on a clock.
	//
	// ALL THREE ARE STRICT `yyyy-MM-dd`, admit.go enforces it with a
	// time.Parse round-trip, and NOTHING HERE IS A TIMESTAMP OR AN OFFSET.
	// CLAUDE.md's non-negotiable is two zones and no DST; a date that carried an
	// offset would be inviting one to be hard-coded. The zone is where the
	// business date was DERIVED (Asia/Ulaanbaatar, recorded in the citation),
	// not something this schema stores.

	// TransactionDate is the entry date the caller asked for — `transactionDate`
	// on the wire, `command.getTransactionDate()` at :628.
	//
	// It is the SUBJECT of both date rules. A vector that carries either
	// precondition without carrying this has recorded a boundary with nothing on
	// either side of it, and admit.go refuses that pairing in both directions.
	TransactionDate string `json:"transaction_date,omitempty"`

	// BusinessDate is the oracle's business date AT THE MOMENT OF CAPTURE, made
	// an input.
	//
	// EMPTY MEANS "THIS VECTOR ASSERTS NOTHING ABOUT THE FUTURE-DATE RULE", and
	// the reference implementation then SKIPS that rule rather than reading a
	// clock. That is deliberate and it is the whole point: a port that fell back
	// to time.Now() would re-introduce exactly the ambient dependence T289
	// rejected, and a harness that let it would be grading the calendar. Every
	// vector predating T295 leaves it empty, and admit.go requires a vector
	// EXPECTING the future-date refusal to carry it, so the rule cannot be
	// claimed without the input that decides it.
	//
	// ON THIS TENANT IT IS DERIVED, NOT PINNED, AND THE CITATION SAYS SO:
	// `enable-business-date` is `f` and `m_business_date` is empty, so
	// BusinessDateReadPlatformServiceImpl seeds BUSINESS_DATE with
	// DateUtils.getLocalDateOfTenant() — today in the TENANT zone. That is
	// precisely why it must be transcribed into the vector: a derived value is
	// one that MOVES.
	BusinessDate string `json:"business_date,omitempty"`

	// LatestClosingDate is getLatestGLClosureByBranch(officeId).getClosingDate()
	// at the moment of capture — the ACCOUNTING_CLOSED precondition, made an
	// input.
	//
	// EMPTY MEANS "NO GLClosure EXISTS AT THIS OFFICE", which is the oracle's own
	// `latestGLClosure != null` branch at :635 and not a P-46 conflation: the
	// oracle has exactly two states here, a closure exists or it does not, and
	// the repository returns null for the second. There is no third "closure
	// exists with an unknown date" state to lose.
	//
	// THE COMPARISON IT FEEDS IS INCLUSIVE AND THE ORACLE'S OWN MESSAGE SAYS
	// OTHERWISE. :636 is `!DateUtils.isBefore(closingDate, transactionDate)`,
	// and DateUtils.isBefore(first, second) is `first.isBefore(second)` for two
	// non-null dates [DateUtils.java:296-298], so the guard refuses whenever
	// `transactionDate <= closingDate` — an entry dated ON the closing date is
	// REFUSED. The wire message is "Journal entry cannot be made PRIOR TO last
	// account closing date for the branch". A port written from the message text
	// gets a strict `<` and FAILS OPEN on exactly the day a period-end
	// adjustment carries. LDG-REFUSE-04 is the vector that kills that port, and
	// `ledger-wrong-closure-boundary-exclusive` is that port, executable.
	LatestClosingDate string `json:"latest_closing_date,omitempty"`

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

	// ProductMappings is the product's OBSERVED acc_product_mapping table, and
	// it is the lookup an accounting-path leg's account is RESOLVED through.
	// [T391]
	//
	// EMPTY ON EVERY VECTOR THAT PREDATES T391, and admit.go requires exactly
	// that of a vector with no per-leg slot code, so the field cannot accumulate
	// silently on the manual corpus — the same default-deny-in-both-directions
	// shape T294 gave the opening-balance inputs.
	ProductMappings []ProductMapping `json:"product_mappings,omitempty"`
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

	// SlotName is THE GRADED SLOT CELL: the Java constant name of the
	// placeholder this leg arrived through, DECODED BY THE IMPLEMENTATION on the
	// slot family the product's accounting rule selects. "" means no slot took
	// part, which is what a MANUAL entry is. [T391]
	//
	// -----------------------------------------------------------------------
	// WHY THE NAME AND NOT THE CODE
	// -----------------------------------------------------------------------
	//
	// The code is the INPUT (RequestLeg.SlotCode). Grading it would be grading
	// the vector against itself — the circularity this schema's money cells were
	// designed to avoid, in a second place. The NAME is an OUTPUT: it exists
	// only after the implementation has chosen a family and decoded the integer
	// through it, and the two loan families do not agree.
	//
	// CashAccountsForLoan HAS NO 7, 8 OR 9 AT ALL; AccrualAccountsForLoan does,
	// and calls them INTEREST_RECEIVABLE, FEES_RECEIVABLE and
	// PENALTIES_RECEIVABLE. The same two names, FEES_RECEIVABLE and
	// PENALTIES_RECEIVABLE, sit at 25 and 26 in the cash enum.
	//
	// [VERIFIED AT 426a23544 BY SYMBOL RATHER THAN BY LINE. The two enums are
	// `AccountingConstants.CashAccountsForLoan` (values 1-6 and 10-26, with
	// FEES_RECEIVABLE(25) and PENALTIES_RECEIVABLE(26)) and
	// `AccountingConstants.AccrualAccountsForLoan` (INTEREST_RECEIVABLE(7),
	// FEES_RECEIVABLE(8), PENALTIES_RECEIVABLE(9)). T391 cited the first half of
	// that pair as `AccountingConstants.java:79-89`, which is the cash enum's
	// `intToEnumMap`/`fromInt` block and contains no enum constant whatsoever —
	// T406's F-T406-3, re-verified by T421 against the pinned checkout. The
	// range was copied from slots.go:170, where it is CORRECT because it cites
	// `fromInt`, and re-attached there to a claim about the constants. That is
	// how a line citation rots: not by the file moving, but by the range being
	// carried to a neighbouring claim. Cite the symbol. Ported at
	// nexus/internal/apps/ledger/slots.go].
	//
	// -----------------------------------------------------------------------
	// THIS IS THE CELL THAT GRADES THE SLOT RATHER THAN THE ACCOUNT
	// -----------------------------------------------------------------------
	//
	// T242's correction (A2-34 F-4) is the reason it exists. The harness printed
	// "gl 18, 22 and 16 carry ZERO journal entries" on every run as measured
	// fact while gl 16 had SIXTEEN, because ONE GL ACCOUNT BACKS SEVERAL SLOTS:
	// gl 16 is PENALTIES_RECEIVABLE (slot 9) on accrual product 28 AND
	// FUND_SOURCE (slot 1) on ten cash products, and every one of its rows
	// arrives through the latter. A corpus that grades only the account
	// reproduces that error: it cannot tell "landed on a receivable account"
	// from "arrived through a receivable slot".
	//
	// AND THE DEFECT IT CATCHES IS ONE NO OTHER CELL CAN. acc_product_mapping is
	// keyed on the raw integer with the accounting rule NOT in the key, so a
	// family-blind port resolves the RIGHT ACCOUNT and every other cell on this
	// leg matches. `ledger-wrong-slot-family-blind` is that port, it is
	// byte-identical to the reference implementation on all seven pre-T391
	// parity vectors, and `legs[i].slot_name` is the only cell it dies on.
	SlotName string `json:"slot_name"`

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
//
// ---------------------------------------------------------------------------
// THE FOURTH CELL, AND WHY IT IS A SELECTOR AND NOT A DATE  [T307, B-3]
// ---------------------------------------------------------------------------
//
// T295 filed B-3: grade `errors[0].args`, because two real captures are
// unpromotable without it — A2-02's response body is BYTE-IDENTICAL to A2-01's
// on all three cells above despite a different transactionDate, and A1-01
// differs from A1-02 in `args` alone. T294 had DELIBERATELY REFUSED to grade its
// own `args` on OB-01, where the field enumerates 26 LIVE TRANSACTION IDS and
// changes with any unrelated posting to the tenant. Both are right, and the
// shape below is what lets both be right at once.
//
// THE FIELD BELOW IS NOT THE DATE. It names WHICH INPUT THE VECTOR ALREADY
// DECLARES the oracle echoed into `errors[0].args[0].value`. The comparator
// RESOLVES the named input from Request and compares that against what the
// implementation produced, so no calendar literal is ever written into an
// expectation and the claim survives re-capture on any dates whatsoever.
//
// THE SOURCE FACT IT ENCODES, which is what makes it a claim about the ORACLE
// and not about one afternoon's tenant state
// [VERIFIED: JournalEntryWritePlatformServiceJpaRepositoryImpl.java:630-638,
// pinned 426a23544]:
//
//	:631  FUTURE_DATE       is constructed with `transactionDate`
//	:637  ACCOUNTING_CLOSED is constructed with `latestGLClosure.getClosingDate()`
//
// THE SAME WIRE FIELD MEANS DIFFERENT THINGS IN THE TWO REFUSALS. A2-02 is the
// only capture in this corpus that separates them: it posted 2026-01-15 against
// a closure dated 2026-01-31 and the oracle echoed 2026-01-31 — the CLOSING
// date, not its own transaction date.
//
// THE ADMISSIBILITY VOCABULARY IS CLOSED TO TWO NAMES, both of which are
// SCALAR CALENDAR DATES that this schema ALREADY declares as inputs, and
// admit.go binds each to the refusal code the source pairs it with. An
// unrecognised selector is refused; a selector on any other refusal code is
// refused; a selector on a non-refusal vector is refused. Default-deny.
//
// WHY OB-01 STILL CANNOT BE GRADED, on TWO independent grounds, so T294's
// refusal is UPHELD as a RULE rather than re-taken as a judgement:
//
//  1. STRUCTURAL. `args[0].value` is a JSON ARRAY there, not a scalar. It is an
//     array because ApiParameterError special-cases exactly one type — a
//     LocalDate becomes a `yyyy-MM-dd` STRING and everything else is handed to
//     Gson as-is [ApiParameterError.java:95-105], and :815 passes a
//     `List<String>` as one vararg Object. There is no selector in the closed
//     vocabulary that names a list, so the claim CANNOT BE WRITTEN DOWN.
//  2. PROVENANCE. Even if one existed, LDG-REFUSE-03's
//     request.posted_non_contra_transaction_ids was itself TRANSCRIBED FROM
//     `errors[0].args[0].value` (T294 handoff §6, provenance table). Resolving a
//     selector against it would compare the captured body with a copy of itself
//     — the harness checking its own transcription, which is the circularity
//     registry.go refuses — and it is tenant-mutable besides.
//
// Both selectors below pass the mirror of (2): request.transaction_date comes
// from the caller's own committed `.req` wire bytes and
// request.latest_closing_date from `req/a2-00-create-closure.json` plus the
// live `acc_gl_closure` read. Neither is read out of the body being graded.
//
// THE ZONE/CLOCK DETERMINATION, made BEFORE the cell was wired because T329
// showed that two Fineract fields spelled the same can be different quantities
// on different clocks, and grading a wall-clock-derived date as a literal bakes
// an up-to-8-hour window into a parity vector:
//
//   - THE RENDER READS NO CLOCK. `DateTimeFormatter("yyyy-MM-dd").format(LocalDate)`
//     [ApiParameterError.java:97-99]. A java.time.LocalDate has no instant and
//     no zone; a date-only pattern over it is a pure field render.
//   - transaction_date: parsed by `LocalDateTime.parse(s, fmt).toLocalDate()`
//     [JsonParserHelper.java:544-547, 558-586] — NO ZoneId, NO Instant. On a
//     `yyyy-MM-dd` body with `dateFormat: yyyy-MM-dd` the path is the identity
//     on the caller's characters. CLOCK: none.
//   - latest_closing_date: `GLClosure.closingDate` is a LocalDate on
//     `@Column(name = "closing_date")`, set from the same parse
//     [GLClosure.java:53-54, 70-72]. CLOCK: none.
//   - AND THE TWO CLOCK-DERIVED DATES IN THIS ARM ARE NOT IN `args` AT ALL:
//     request.business_date (DateUtils.getLocalDateOfTenant, tenant zone) and
//     `glclosures.createdDate` (audit insert, JVM zone, T329). :631 echoes the
//     transaction date and NOT the business date it just compared against, so
//     the guard that READS the wall clock does not ECHO it. That is checkable at
//     :631 rather than true-today.
type Refusal struct {
	HTTPStatus int    `json:"http_status"`
	Code       string `json:"code"`
	Message    string `json:"message"`

	// ArgEcho is the EXPECTATION side of `errors[0].args[0].value`, and it is a
	// SELECTOR — "transaction_date" or "latest_closing_date" — never a date.
	// Empty means this vector grades no args cell, which is the state every
	// refusal vector other than the two DATE refusals is required to be in.
	ArgEcho string `json:"arg_echo,omitempty"`

	// Arg0Value is the ANSWER side: what an implementation actually put in
	// `errors[0].args[0].value`.
	//
	// IT CARRIES NO JSON NAME ON PURPOSE, and that is the load-bearing half of
	// this design rather than a serialisation detail. `json:"-"` plus this
	// package's strict decode means a vector file that tries to write
	// `"arg0_value": "2026-01-31"` dies at load with an UNKNOWN FIELD. The store
	// therefore CANNOT express a graded date literal here even deliberately, so
	// the "grade the relation, never the calendar" rule is enforced by the type
	// and not by a reviewer noticing.
	Arg0Value string `json:"-"`
}

// Arg echo selectors. The vocabulary is CLOSED: admit.go refuses anything else.
const (
	// ArgEchoTransactionDate — :631 constructs FUTURE_DATE with the submitted
	// transactionDate.
	ArgEchoTransactionDate = "transaction_date"

	// ArgEchoLatestClosingDate — :637 constructs ACCOUNTING_CLOSED with
	// latestGLClosure.getClosingDate(), NOT with the submitted date.
	ArgEchoLatestClosingDate = "latest_closing_date"
)

// ResolveArgEcho returns the request input a refusal's arg-echo selector names.
//
// It is the ONLY place a selector becomes a value, so the comparator, the
// admissibility rule and every test agree by construction rather than by three
// authors typing the same switch.
func ResolveArgEcho(sel string, req Request) (string, bool) {
	switch sel {
	case ArgEchoTransactionDate:
		return req.TransactionDate, true
	case ArgEchoLatestClosingDate:
		return req.LatestClosingDate, true
	default:
		return "", false
	}
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

	// PortRefusal is populated on kind == "port-refusal" -- a DIVERGENCE vector --
	// and zero otherwise. It is the PORT's side of a divergence: what this Go
	// port must do with a request the reference oracle ACCEPTED.
	PortRefusal PortRefusal `json:"port_refusal"`
}

// PortRefusal is what a DIVERGENCE vector requires of the PORT.
//
// IT IS A DIFFERENT TYPE FROM Refusal AND THAT IS THE POINT. Refusal is an
// ORACLE-OBSERVED wire refusal: an HTTP status, a Fineract globalisation code
// and a message, every one of them transcribed from a captured response body. A
// PORT refusal was never on a wire. It has no HTTP status, no globalisation
// code, and inventing either would be putting a fabricated observation into a
// store whose entire discipline is that it holds only observed bytes.
//
// T359's measured scratch-copy patch made exactly that trade -- it re-routed the
// port's residue refusal as a `*Refusal` carrying `HTTP 422` -- and 422 is a
// number no oracle, no port and no wire ever produced. This type has nowhere to
// put one.
//
// IT ALSO HAS NOWHERE TO PUT AN AMOUNT, in any spelling. There is no numeric
// field on it at all.
type PortRefusal struct {
	// Marker is a STABLE SUBSTRING of the refusal the port emits, and it is the
	// graded cell.
	//
	// WHY A MARKER AND NOT THE WHOLE TEXT. The port's refusal is produced by
	// `ledger.MinorUnitsFromDecimalText` as a plain `fmt.Errorf`, in a package
	// this vector schema does not own. Grading its complete wording would pin
	// this corpus to a sentence any unrelated edit re-flows, and the store would
	// then go red for a reason that has nothing to do with money. Grading a
	// declared, load-bearing PHRASE keeps the assertion on the thing that
	// matters -- that the port refused FOR THE RESIDUE, and did not refuse for
	// some unrelated reason and get counted as agreeing by accident.
	//
	// IT IS NOT OPTIONAL. admit.go requires it non-empty on every divergence
	// vector and at least MinPortRefusalMarker characters long, because a short
	// marker is contained in almost any message and would be a comparison that
	// cannot fail.
	Marker string `json:"marker"`

	// ObservedText is the port refusal's FULL text as it stood when this vector
	// was written, recorded for the reader and NEVER GRADED.
	//
	// It is here for the same reason amount_major_text sits beside amount_minor
	// on a parity leg: so a human meeting this file can see the whole thing the
	// marker was cut out of, and so a later reader can tell "the wording
	// changed" from "the port stopped refusing". The comparator never reads it.
	ObservedText string `json:"observed_text"`
}

// OracleAcceptance is THE ORACLE'S SIDE OF A DIVERGENCE, and it is a type in
// which NO MONEY VALUE CAN BE HELD.
//
// THE PROBLEM IT SOLVES, stated exactly. The reference oracle accepted, stored
// and served back `100.125000` MNT while the same response declared
// `"decimalPlaces": 2` [OBSERVED: T352-A09-residue-3dp-readback-cited.json,
// re-read live and byte-identical by T360; independently re-derived by T359 at
// `300.6255545` -> `300.625555`]. The store's money cell is
// `ExpectLeg.AmountMinor`, an integer STRING parsed to `ledger.MinorUnits`
// (`int64`). NO int64 EQUALS 100.125. Any number written there is a number
// neither system produced, and writing one is the exact way an unobserved
// figure enters a corpus.
//
// SO THE OBSERVATION IS RECORDED AS CHARACTERS, AND THE TYPE FORBIDS ANYTHING
// ELSE. Every field below is a `string` or a plain HTTP status `int`. There is
// no float64, no json.Number, no widened decimal, no big.Rat, and no
// "amount"-named numeric of any kind. Nothing in this package parses
// ObservedAmountTexts, converts it, compares it against a port value, or feeds
// it to arithmetic: grep the identifier and every use is a byte comparison, a
// digit scan or a print. That is what makes recording an unrepresentable
// observation safe -- the value is never a NUMBER in this program, at any
// point, including intermediate calculation.
//
// AND IT IS BYTE-CHECKED RATHER THAN TRUSTED. admit.go requires every entry of
// ObservedAmountTexts to occur VERBATIM in the bytes of the artefact
// provenance.capture_ref names, so "these are the oracle's own characters" is a
// checkable claim and not a transcription anybody has to be believed about.
type OracleAcceptance struct {
	// HTTPStatus is the status THE ORACLE returned. It is an acceptance, so
	// admit.go requires 200..299 -- a divergence vector whose oracle side is a
	// refusal is a vector filed under the wrong class.
	HTTPStatus int `json:"http_status"`

	// ObservedAmountTexts are THE ORACLE'S OWN CHARACTERS for the amount(s) it
	// accepted and served back, verbatim, one entry per distinct rendering.
	//
	// NEVER PARSED. NEVER CONVERTED. NEVER COMPARED TO A PORT VALUE. The only
	// things this package does with them are: (1) `bytes.Contains` against the
	// cited capture artefact, (2) a digit scan that decides whether a non-zero
	// digit lies beyond the currency's minor unit -- carried out on bytes, with
	// no numeric conversion of any kind -- and (3) printing them.
	ObservedAmountTexts []string `json:"observed_amount_texts"`

	// WhyUnrepresentable is the vector's own sentence saying why this
	// observation cannot be a parity vector. Required non-empty: a divergence
	// filed without it is a parity vector somebody could not make pass.
	WhyUnrepresentable string `json:"why_unrepresentable"`

	// Gate is the open gate this divergence belongs to -- "G-19" today. Required
	// non-empty, because a divergence with no gate is a defect nobody owns, and
	// a corpus that can hold one silently is worse than one that cannot hold it
	// at all.
	Gate string `json:"gate"`
}

// IsZero reports whether nothing at all was written into this block. It exists
// because OracleAcceptance carries a slice and so is not comparable with ==; the
// alternative -- comparing the fields at each call site -- is three copies of one
// rule, which is the shape T306 found had drifted apart in the leg checks.
func (o OracleAcceptance) IsZero() bool {
	return o.HTTPStatus == 0 && len(o.ObservedAmountTexts) == 0 &&
		o.WhyUnrepresentable == "" && o.Gate == ""
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

	CapabilitiesRequired []string    `json:"capabilities_required"`
	Provenance           Provenance  `json:"provenance"`
	Oracle               OracleStamp `json:"oracle"`
	Request              Request     `json:"request"`

	// OracleAccepted is populated on a DIVERGENCE vector and MUST be zero on
	// every other class -- admit.go refuses it in both directions, so the field
	// cannot accumulate silently on the vectors that predate it.
	//
	// IT SITS ON THE VECTOR AND NOT ON Expect DELIBERATELY. Expect is "what the
	// implementation must produce". The oracle's acceptance is not an
	// expectation of the port at all -- it is the OBSERVATION the divergence is
	// a divergence FROM -- and putting it under `expect` would invite a later
	// reader, or a later comparator, to grade the port against it. There is
	// nothing here a port could be asked to reproduce.
	OracleAccepted OracleAcceptance `json:"oracle_accepted"`

	Expect        Expect           `json:"expect"`
	GradedAgainst []Counterfactual `json:"graded_against"`

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
