package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// isoDateLayout is the ONE date spelling this schema accepts, and it is the
// oracle's own `dateFormat` on every captured request body: "yyyy-MM-dd".
//
// It is used ONLY for validation, never for arithmetic. The comparator orders
// dates byte-wise (see isoBefore/isoAfter in impl.go); this constant is what
// makes that ordering sound, by refusing anything that is not zero-padded and
// fixed-width. The round trip -- Parse then Format then compare to the input --
// is deliberate: time.Parse alone accepts "2026-1-5" for this layout and would
// admit a string that compares wrong.
//
// NO ZONE AND NO OFFSET APPEARS HERE. CLAUDE.md: two time zones, no DST, never
// hard-code an offset. These are calendar dates.
const isoDateLayout = "2006-01-02"

// describeExpectation names, in one phrase, what a vector says the oracle
// answered -- for an error message that has to contrast it with what the source
// says the oracle would have answered instead.
func describeExpectation(v *Vector) string {
	if v.Expect.Kind == "refusal" {
		return fmt.Sprintf("expect.refusal.code %q", v.Expect.Refusal.Code)
	}
	return fmt.Sprintf("expect.kind %q (a POSTED ENTRY)", v.Expect.Kind)
}

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
	// --- the opening-balance inputs, default-deny in both directions [T294] --
	//
	// These three fields exist so that a refusal whose precondition lives in
	// AMBIENT TENANT STATE carries that state as an INPUT (T289's date strategy
	// (c), applied to state rather than to a date). The rules below are what
	// stops them becoming a hole:
	//
	//   * an unknown `command` REFUSES, rather than being ignored as a hint;
	//   * an opening-balance command with no contra mapping REFUSES, because
	//     :708 would have thrown a DIFFERENT error first and the vector would
	//     be describing an observation it did not take;
	//   * a NON-opening-balance vector carrying opening-balance inputs REFUSES,
	//     so the fields cannot accumulate silently on the vectors that predate
	//     them.
	switch v.Request.Command {
	case "", "defineOpeningBalance":
	default:
		add("request.command %q is not one this schema knows (\"\" for the plain create path, "+
			"\"defineOpeningBalance\" for POST /journalentries?command=defineOpeningBalance). ABSENT "+
			"REFUSES and UNKNOWN REFUSES: a command string nothing routes on is a field the comparator "+
			"would silently ignore", v.Request.Command)
	}
	if v.Request.Command == "defineOpeningBalance" {
		if v.Request.ContraGLAccountID <= 0 {
			add("request.command is defineOpeningBalance and "+
				"request.contra_gl_account_id is %d. "+
				"JournalEntryWritePlatformServiceJpaRepositoryImpl.java:708 resolves the "+
				"financial-activity type 300 mapping BEFORE the guard at :717, so if that mapping does "+
				"not resolve the oracle returns a DIFFERENT refusal and this vector describes an "+
				"observation nobody took", v.Request.ContraGLAccountID)
		}
		for i, id := range v.Request.PostedNonContraTransactionIDs {
			if strings.TrimSpace(id) == "" {
				add("request.posted_non_contra_transaction_ids[%d] is blank. It transcribes the oracle's "+
					"own errors[0].args and a blank member is a transcription defect, not an "+
					"observation", i)
			}
		}
	} else {
		if v.Request.ContraGLAccountID != 0 {
			add("request.contra_gl_account_id is set on a vector whose request.command "+
				"is %q. "+
				"The contra mapping is read only by defineOpeningBalance:708-709; carrying it anywhere "+
				"else records an input nothing consumes", v.Request.Command)
		}
		if len(v.Request.PostedNonContraTransactionIDs) > 0 {
			add("request.posted_non_contra_transaction_ids is non-empty on a vector whose "+
				"request.command is %q. findNonContraTransactionIds is read only by "+
				"validateJournalEntriesArePostedBefore, which only defineOpeningBalance reaches (:717)",
				v.Request.Command)
		}
	}

	// --- the capability claim is SCOPED TO THE OBSERVED SHAPE [T296] ---------
	//
	// `ledger.opening.balance.and.closure` names THREE shapes in its own
	// description — defining opening balances after journal entries have been
	// posted, an entry dated on or before the latest GLClosure, and a
	// future-dated entry — and T294 flipped the row to in_graded_domain TRUE on
	// the strength of the FIRST one only. [HISTORY, TRUE WHEN T296 WROTE IT AND NO
	// LONGER TRUE: at that moment the other two were captured raw in
	// .softhouse/capture/t287-closure-refusals and nothing promoted them. T295
	// promoted both, and T305 then captured the ACCEPTING side of the first.
	// See the adjudicated gate below.]
	//
	// THE FLIP IS MEASURED TO WIDEN THE GATE, and this rule is what puts the
	// width back. T296 built a closure-family refusal vector from T287's real
	// A1-01 artefacts (correct provenance sha256s, a non-empty graded_against)
	// and ran it against two registries that differ in that one boolean:
	//
	//     in_graded_domain FALSE  ->  INADMISSIBLE, the capability gate refuses
	//     in_graded_domain TRUE   ->  ADMITTED AND GRADED, 3 cells compared
	//
	// [.softhouse/reviews/T296/out/capgate-arm{A,B}-*.txt]. So before T294 the
	// registry refused an UNOBSERVED shape as DATA; after T294 only the row's
	// evidence PROSE said it should be refused, and P-89 is exactly that: "PROSE
	// DOES NOT FIRE ON THE NEXT FIRE."
	//
	// WHY THIS IS NOT THE FIX T289 FORBADE. T289 F-T289-4 settled that the row is
	// COHERENT AND MUST NOT BE RENAMED OR SPLIT, because defineOpeningBalance:703
	// reaches the same guard at :724 that the manual create path reaches at :157.
	// This rule renames nothing and splits nothing. The row stays one row and
	// keeps naming all three shapes; what is scoped is the CLAIM a vector may
	// make on it, and the scope is the one thing that was actually observed. When
	// a closure refusal IS promoted — T294 backlog (6) — this rule is what that
	// task must widen, deliberately and with the capture in hand, instead of
	// finding the door already open.
	for _, name := range v.CapabilitiesRequired {
		if name != "ledger.opening.balance.and.closure" {
			continue
		}
		// THE DRIVER WIDENED THIS AT A MERGE CONFLICT WITH NO REVIEWER AND FILED IT AS
		// T306. T306 ADJUDICATED IT: the widening was RIGHT TO HAPPEN and WRONG AS
		// WRITTEN, and this is the re-keyed form. Both defects were measured, not argued
		// [.softhouse/reviews/T306/out/].
		//
		//   T306-F-2  KEYED ON AN OUTPUT. Two of the driver's three arms read
		//     `v.Expect.Refusal.Code`, which is the ANSWER THE VECTOR CLAIMS, not a fact
		//     about the request the oracle was given. Measured (probe P5: LDG-REFUSE-04
		//     with request.latest_closing_date deleted): against the driver's predicate
		//     THIS GATE CONTRIBUTED NO REASON AT ALL — the only refusal came from the
		//     date-rule block ~80 lines below, so the gate's entire request-side check
		//     was delegated to a rule a later edit could relax without ever reading this
		//     one. Both date arms are now the SAME COMPARISON THE ORACLE MAKES, read off
		//     the vector's own inputs.
		//
		//   T306-F-1  THE COMMENT ASSERTED A CONTROL THAT WAS NOT FIRING. It read "a
		//     vector claiming this capability for a FOURTH shape -- most obviously an
		//     ACCEPTANCE -- is still refused, as DATA and not as prose (P-89)". Probe P2
		//     — LDG-01's real ACCEPTED 3-leg manual entry with this row added and
		//     request.command set to "defineOpeningBalance" — was ADMITTED AND GRADED,
		//     15 cells, 5 of them money. The gate never refused acceptances; it refused
		//     PLAIN-CREATE acceptances, and one request field bought the claim. That was
		//     P-89 one level up: prose claimed DATA was firing and it was not.
		//
		// WHAT THIS STORE HAS OBSERVED ON THIS ROW IS FOUR VECTORS, NOT THREE, AND THEY
		// ARE NOT SYMMETRICAL. The asymmetry IS the measurement and it is why the arms
		// differ:
		//
		//   the defineOpeningBalance command — BOTH SIDES of :811's emptiness test
		//     LDG-REFUSE-03  REFUSAL   findNonContraTransactionIds NON-EMPTY  :717 -> :810-813
		//     LDG-05         ACCEPTED  findNonContraTransactionIds EMPTY, :812 falls through,
		//                              HTTP 200 and SIX journal entries for three request legs
		//   the two DATE boundaries — REFUSING SIDE ONLY, accepting side still uncaptured
		//     LDG-REFUSE-04  REFUSAL   !isBefore(latestClosingDate, transactionDate)   :636
		//     LDG-REFUSE-05  REFUSAL   isDateInTheFuture(transactionDate)              :629-631
		//
		// [VERIFIED: JournalEntryWritePlatformServiceJpaRepositoryImpl.java at the pinned
		// commit 426a23544. :717 is validateJournalEntriesArePostedBefore(contraId) inside
		// defineOpeningBalance; :810-813 is that method, :811 the findNonContraTransactionIds
		// query and :812 the `if (!CollectionUtils.isEmpty(transactionIds))` whose FALSE
		// branch is LDG-05. :626 declares validateBusinessRulesForJournalEntries; the
		// future-date GUARD STATEMENT is :630 and :629 is its comment line — this store
		// cites it as ":629" throughout and that citation is one line high; :636 is
		// literally `if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate))`.]
		//
		// SO THE COMMAND ARM TAKES EITHER expect.kind AND THE DATE ARMS DO NOT. T306's
		// own first pass put `v.Expect.Kind == "refusal" &&` in front of ALL THREE arms,
		// which was correct on the store it could see and became WRONG the moment T305
		// landed: it would have made LDG-05 INADMISSIBLE and brought back to life the
		// mutant LDG-05 exists to kill — `ledger-wrong-openingbalance-always-refusing`,
		// T296 arm A, a port that REFUSES EVERY OPENING BALANCE and stays green on the
		// whole corpus [T320 finding T320-4, HIGH]. Dropping the precondition on THIS ONE
		// ARM is the widening T306's first pass said must arrive "deliberately and with
		// the capture in hand"; T305 put the capture in hand, so it arrives here and
		// nowhere else. The date arms KEEP it, and the reason CHANGED UNDER THIS TASK'S
		// FEET between its first commit and its merge — which is why the reason is
		// written out rather than left as "backlog B-1/B-2 is open":
		//
		//   WAS (true until T327 merged): "no capture in this store shows an entry
		//     ACCEPTED at either date boundary."  THAT CLAUSE IS NOW FALSE.
		//   IS: T327 FIRED BOTH BACKLOG ARMS AND BOTH RETURNED HTTP 200 — B-1, an entry
		//     dated one day AFTER the closing date (2026-08-27 vs a closure closed
		//     2026-08-26), and B-2, an entry dated ON the business date (2026-08-28)
		//     [VERIFIED: .softhouse/capture/t327-closure-accepting-side/throwaway/out/
		//      B1-ACCEPT-06-entry-one-day-after-closing-date.status = 200 and
		//      B2-ACCEPT-01-entry-on-business-date.status = 200]. So the BYTES exist.
		//   AND THE ARMS STILL KEEP THE PRECONDITION, because T327 PROMOTED NOTHING: the
		//     ledger store holds the same ten vectors it held before that merge, and not
		//     one of them is an acceptance at either date boundary. THE GATE KEYS ON THE
		//     STORE, NEVER ON THE CAPTURE DIRECTORY. A capture is an observation; a vector
		//     is a graded claim, and only the second is what a `capabilities_required`
		//     entry can honestly assert coverage of.
		//
		// SO THE NEXT WIDENING IS NOW EARNED AND UNCLAIMED, and it is exactly one edit:
		// when T327's B-1/B-2 bytes are PROMOTED to vectors, drop `v.Expect.Kind ==
		// "refusal"` from the date arms too — deliberately, in the promoting task, with
		// the capture in hand. Until then MUTANT W (the same drop, made early) is held
		// red by TestOpeningBalanceCapabilityIsScopedToTheObservedShape/"an ACCEPTANCE at
		// either DATE boundary REFUSES", and that red is CORRECT, not an obstacle
		// [.softhouse/reviews/T306/out/30-mutation-arms.txt].
		//
		// WHAT THIS STILL DOES NOT DO, stated rather than left to be discovered: it
		// cannot bind a TRANSCRIPTION to its capture. A vector whose provenance cites a
		// manual-adjustments capture, with only the refusal code and the three dates
		// edited to the closure shape, is admitted by this rule — its INPUTS really are
		// the pre-closure shape. No capability gate can catch that; only re-reading the
		// cited artefact can, and that is the citation rules' job, not this one's
		// [T306-F-6].
		openingBalanceCommand := v.Request.Command == "defineOpeningBalance"
		preClosureInputs := v.Request.LatestClosingDate != "" && v.Request.TransactionDate != "" &&
			!isoBefore(v.Request.LatestClosingDate, v.Request.TransactionDate)
		futureDatedInputs := v.Request.TransactionDate != "" && v.Request.BusinessDate != "" &&
			isoAfter(v.Request.TransactionDate, v.Request.BusinessDate)
		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))
		if !observedShape {
			add("capabilities_required names %q on a vector whose request.command is %q and whose "+
				"expect.kind is %q. THE SHAPES THIS STORE HAS OBSERVED ARE: the "+
				"defineOpeningBalance-after-a-NON-CONTRA-entry refusal at "+
				"JournalEntryWritePlatformServiceJpaRepositoryImpl.java:717 (LDG-REFUSE-03) and its "+
				"ACCEPTING side at :812 (LDG-05, HTTP 200 and six entries on an empty ledger) -- so on "+
				"that COMMAND either expectation is covered -- and the PRE-CLOSURE (:636) and "+
				"FUTURE-DATED (:629-631) REFUSALS (LDG-REFUSE-04, LDG-REFUSE-05), whose ACCEPTING "+
				"sides are CAPTURED BUT NOT PROMOTED. The claim on the two DATE shapes is decided by "+
				"THIS VECTOR'S REQUEST -- the same two date comparisons the oracle makes -- and never "+
				"by the refusal code it declares, because that is the answer it is asking to be "+
				"believed about. A vector outside those four -- an entry ACCEPTED at either date "+
				"boundary, most obviously -- would read as covered when it is not. T327 fired backlog "+
				"B-1 and B-2 and BOTH RETURNED HTTP 200, so the oracle bytes now EXIST "+
				"(.softhouse/capture/t327-closure-accepting-side/), but NO VECTOR carries them and this "+
				"gate keys on the STORE, never on the capture directory. PROMOTE THE CAPTURE FIRST, "+
				"then widen this rule",
				name, v.Request.Command, v.Expect.Kind)
		}
	}

	// --- the date inputs, default-deny in both directions [T295] ------------
	//
	// T289 ruled T287's four closure/future-date captures NON-PROMOTABLE AS
	// LITERAL-DATE VECTORS because the business date and the closing date lived
	// in PROSE. Lifting them into request.{transaction_date, business_date,
	// latest_closing_date} is the promotion; these rules are what stop the
	// lifted fields becoming a hole of their own. They are the mirror of the
	// opening-balance rules above and they close the same four failures:
	//
	//   * a MALFORMED date REFUSES, because isoBefore/isoAfter compare ISO
	//     strings byte-wise and that is only chronological for strict
	//     zero-padded `yyyy-MM-dd`;
	//   * a PRECONDITION WITHOUT ITS SUBJECT refuses, and a subject without its
	//     precondition refuses, so a boundary can never be recorded with nothing
	//     on one side of it;
	//   * a vector CLAIMING one of the two date refusals without carrying the
	//     input that decides it refuses -- the rule cannot be asserted without
	//     the state that produces it;
	//   * a vector whose dates say the ORACLE WOULD HAVE REFUSED IT EARLIER than
	//     the refusal it records refuses, because :629 runs before :636 and both
	//     run before everything in saveAllDebitOrCreditEntries, so such a vector
	//     describes an observation nobody took.
	for _, d := range []struct{ field, val string }{
		{"request.transaction_date", v.Request.TransactionDate},
		{"request.business_date", v.Request.BusinessDate},
		{"request.latest_closing_date", v.Request.LatestClosingDate},
	} {
		if d.val == "" {
			continue
		}
		t, perr := time.Parse(isoDateLayout, d.val)
		if perr != nil || t.Format(isoDateLayout) != d.val {
			add("%s %q is not a strict `yyyy-MM-dd` calendar date. The comparator orders these dates "+
				"BYTE-WISE, which is chronological order only for zero-padded fixed-width ISO-8601, so "+
				"an unpadded month or a two-digit year would not merely look wrong -- it would COMPARE "+
				"wrong and the vector would grade the opposite of what it claims", d.field, d.val)
		}
	}
	switch {
	case v.Request.TransactionDate != "" && v.Request.BusinessDate == "":
		add("request.transaction_date is %q and request.business_date is empty. The future-date rule "+
			"(:629 DateUtils.isDateInTheFuture -> isAfterBusinessDate) is decided by comparing the two, "+
			"and the reference implementation READS NO CLOCK: with no business date it SKIPS the rule. "+
			"A vector carrying a transaction date with no business date therefore records a subject "+
			"with no boundary, and grades one rule fewer than it appears to", v.Request.TransactionDate)
	case v.Request.BusinessDate != "" && v.Request.TransactionDate == "":
		add("request.business_date is %q and request.transaction_date is empty. The business date is a "+
			"PRECONDITION and nothing in this vector is subject to it", v.Request.BusinessDate)
	}
	if v.Request.LatestClosingDate != "" && v.Request.TransactionDate == "" {
		add("request.latest_closing_date is set and request.transaction_date is empty. The closure " +
			"boundary (:636) is compared against the transaction date and there is none")
	}
	switch v.Expect.Refusal.Code {
	case codeFutureDate:
		switch {
		case v.Request.TransactionDate == "" || v.Request.BusinessDate == "":
			add("this vector expects %q and does not carry both request.transaction_date and "+
				"request.business_date. That refusal IS the comparison of those two dates; claiming it "+
				"without them is claiming coverage nothing decides", codeFutureDate)
		case !isoAfter(v.Request.TransactionDate, v.Request.BusinessDate):
			add("this vector expects %q with request.transaction_date %q and request.business_date %q. "+
				"isDateInTheFuture is isAfter(transactionDate, businessDate) and is STRICT "+
				"[DateUtils.java:258-264], so on these two dates the oracle DOES NOT take that branch "+
				"and the vector records a refusal nobody observed",
				codeFutureDate, v.Request.TransactionDate, v.Request.BusinessDate)
		}
	case codeAccountingClosed:
		switch {
		case v.Request.TransactionDate == "" || v.Request.BusinessDate == "" ||
			v.Request.LatestClosingDate == "":
			add("this vector expects %q and does not carry all three of request.transaction_date, "+
				"request.business_date and request.latest_closing_date. The closing date DECIDES the "+
				"refusal (:636) and the business date is what shows the FUTURE-DATE guard at :629 -- "+
				"which runs first -- did not fire instead", codeAccountingClosed)
		case isoAfter(v.Request.TransactionDate, v.Request.BusinessDate):
			add("this vector expects %q with request.transaction_date %q AFTER request.business_date "+
				"%q. :629 runs BEFORE :634-639, so the oracle would have returned %q instead and this "+
				"vector describes an observation nobody took",
				codeAccountingClosed, v.Request.TransactionDate, v.Request.BusinessDate, codeFutureDate)
		case isoAfter(v.Request.TransactionDate, v.Request.LatestClosingDate):
			add("this vector expects %q with request.transaction_date %q AFTER "+
				"request.latest_closing_date %q. :636 is !DateUtils.isBefore(closingDate, "+
				"transactionDate), which refuses transactionDate <= closingDate; a date strictly after "+
				"the closing date is ACCEPTED and WRITES",
				codeAccountingClosed, v.Request.TransactionDate, v.Request.LatestClosingDate)
		}
	default:
		// THE OTHER DIRECTION, and it is the one that would rot silently. A
		// vector whose dates trip a guard the oracle checks FIRST cannot
		// legitimately record any later outcome -- not a posting, and not one of
		// the refusals raised further down. Gated on the plain create path
		// because :717 (defineOpeningBalance) runs BEFORE :724 and legitimately
		// pre-empts both date guards.
		if v.Request.Command == "" && v.Request.TransactionDate != "" && v.Request.BusinessDate != "" {
			if isoAfter(v.Request.TransactionDate, v.Request.BusinessDate) {
				add("request.transaction_date %q is AFTER request.business_date %q, so :629 refuses "+
					"this request with %q -- but this vector records %q. The first guard the oracle "+
					"reaches is the one it answers with",
					v.Request.TransactionDate, v.Request.BusinessDate, codeFutureDate,
					describeExpectation(v))
			} else if v.Request.LatestClosingDate != "" &&
				!isoBefore(v.Request.LatestClosingDate, v.Request.TransactionDate) {
				add("request.transaction_date %q is ON OR BEFORE request.latest_closing_date %q, so "+
					"the INCLUSIVE guard at :636 refuses this request with %q -- but this vector "+
					"records %q",
					v.Request.TransactionDate, v.Request.LatestClosingDate, codeAccountingClosed,
					describeExpectation(v))
			}
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
	bad = append(bad, citationReasons(opts.RepoRoot, v.CaseID, "provenance.capture_ref",
		v.Provenance.CaptureRef, v.Provenance.CaptureSHA256, v.Provenance.CaptureCaseID)...)
	bad = append(bad, citationReasons(opts.RepoRoot, v.CaseID, "provenance.request_capture_ref",
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
	//
	// THE ONE-LEG-IN-ONE-LEG-OUT ASSUMPTION IS TRUE OF THE PLAIN CREATE PATH AND
	// FALSE OF defineOpeningBalance, AND THAT WAS MEASURED, NOT ARGUED. [T305]
	//
	// saveAllDebitOrCreditOpeningBalanceEntries (:759-797) calls
	// helper.persistJournalEntry TWICE inside the per-leg loop — the leg at :791
	// and its CONTRA on the financial-activity-300 account at :796 — so an
	// accepted opening balance stores exactly 2*len(legs) journal entries.
	// OB-ACCEPT-01 sent three legs and the oracle wrote SIX entries
	// [.softhouse/capture/t305-openingbalance-accepting-side/throwaway/out/
	//  OB-ACCEPT-01-readback-db.json].
	//
	// SO THE RULE IS SCOPED RATHER THAN DROPPED, and the scoped form is STRICTER
	// than the general one, not weaker: on this command the expectation must
	// carry EXACTLY twice the request's legs. A vector that carried, say, four
	// expect legs for three request legs is refused here and would not have been
	// refused by a rule that merely stopped applying.
	//
	// WHY NOT INSTEAD PUT SIX LEGS IN request.legs. Because request.legs is the
	// INPUT the implementation converts, and the caller did not send six. Writing
	// the contra legs into the request would hand the port the answer it is
	// supposed to derive — the circularity DEC-2 forbids in as many words — and
	// would also make the request bytes and the vector's request disagree, which
	// is the one thing provenance exists to prevent.
	//
	// ONE BOOLEAN, READ BY ALL THREE LEG RULES [T306, closing T320-3]. T305 wrote the
	// condition out three times and the three copies were NOT complements: the
	// POSITIONAL amount_major_text pairing was skipped for `defineOpeningBalance`
	// REGARDLESS of expect.kind, while the MULTISET pairing that replaces it was
	// gated on `defineOpeningBalance` AND kind != "refusal". For a defineOpeningBalance
	// REFUSAL carrying expect legs, both were therefore off and the request/expect
	// amount cross-check was ABSENT ENTIRELY.
	//
	// MEASURED SEVERITY, because "a hole" and "an exploitable hole" are different
	// claims: that combination is ALREADY inadmissible one rule higher -- the
	// `case "refusal"` arm of the expect.kind switch refuses `len(v.Expect.Legs) > 0`
	// UNCONDITIONALLY ("a refused request created no entry"), so no vector could
	// reach the missing check without collecting that reason first. It is closed
	// anyway, as one variable rather than three copies, because the argument that it
	// is unreachable depends on a DIFFERENT rule staying exactly as it is, and that
	// is precisely the shape of dependency this file exists to refuse.
	obAcceptingLegs := v.Request.Command == "defineOpeningBalance" && v.Expect.Kind != "refusal"
	if len(v.Expect.Legs) > 0 {
		want := len(v.Request.Legs)
		if obAcceptingLegs {
			want = 2 * len(v.Request.Legs)
		}
		if len(v.Expect.Legs) != want {
			add("expect.legs has %d entries and request.legs has %d; on request.command %q an accepted "+
				"entry stores %d (saveAllDebitOrCreditOpeningBalanceEntries persists the leg at :791 AND "+
				"its contra at :796, inside the per-leg loop), and a length mismatch is a transcription "+
				"defect, not a divergence to grade",
				len(v.Expect.Legs), len(v.Request.Legs), v.Request.Command, want)
		}
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
		if !obAcceptingLegs &&
			i < len(v.Request.Legs) && v.Request.Legs[i].AmountMajorText != l.AmountMajorText {
			add("expect.legs[%d].amount_major_text %q and request.legs[%d].amount_major_text %q "+
				"disagree; both transcribe the same oracle characters",
				i, l.AmountMajorText, i, v.Request.Legs[i].AmountMajorText)
		}
	}
	// THE OPENING-BALANCE PAIRING IS BY MULTISET, NOT BY POSITION. [T305]
	//
	// :796 writes the contra entry with the SAME amount as its leg, so each
	// request amount must occur EXACTLY TWICE among the expect legs. It is
	// checked as a multiset rather than positionally because the oracle emits
	// all DEBIT legs (:742) before all CREDIT legs (:745) irrespective of the
	// order the request listed them in — OB-ACCEPT-01's request happened to be
	// debits-first, so the capture is consistent with both orderings and this
	// rule declines to assert the one it cannot see.
	if obAcceptingLegs && len(v.Expect.Legs) > 0 {
		count := map[string]int{}
		for _, l := range v.Expect.Legs {
			count[l.AmountMajorText]++
		}
		for i, l := range v.Request.Legs {
			count[l.AmountMajorText] -= 2
			if count[l.AmountMajorText] < 0 {
				add("request.legs[%d].amount_major_text %q occurs fewer than twice among the expect "+
					"legs. An accepted opening balance writes the leg at :791 and its contra at :796 "+
					"with the SAME amount, so every request amount must appear exactly twice",
					i, l.AmountMajorText)
			}
		}
		// SORTED, AND SURPLUS ONLY [T306, closing two T320 defects in T305's rule].
		//
		//   * `range` OVER A GO MAP IS RANDOMISED PER RUN. Appending to the reason
		//     slice inside it made the ORDER of an inadmissibility report vary run to
		//     run whenever two amounts were surplus at once. In a harness whose whole
		//     discipline is byte-stable transcripts, a report that reorders itself is a
		//     diff nobody can read and a guard nobody can pin.
		//   * A SHORTFALL IS NOT A SURPLUS. `left` is negative exactly when a request
		//     amount occurred FEWER than twice -- which the loop above has ALREADY
		//     reported, in its own words -- and printing it here produced the sentence
		//     "carry amount X -1 time(s) MORE than twice-per-request-leg allows". Only
		//     a genuine surplus is reported here now, so each defect is named once and
		//     named correctly.
		surplus := make([]string, 0, len(count))
		for text, left := range count {
			if left > 0 {
				surplus = append(surplus, text)
			}
		}
		sort.Strings(surplus)
		for _, text := range surplus {
			add("expect.legs carry amount %q %d time(s) more than twice-per-request-leg allows; the "+
				"only entries an accepted opening balance writes are the caller's legs and their "+
				"contras", text, count[text])
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
//
// AND THE FILE-NAME BRANCH IS NOW GATED RATHER THAN SILENTLY ALLOWED. See
// citationMode and citationNameOnlyPin below [T243, closing A2-34's F-3].
func citationReasons(repoRoot, vectorCaseID, field, ref, wantDigest, caseID string) []string {
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
	switch citationMode(repoRoot, ref, caseID) {
	case CitationByBytes, CitationBySidecar:
		return out
	case CitationByNameOnly:
		if _, pinned := citationNameOnlyPin[citationPinKey(vectorCaseID, field)]; pinned {
			return out
		}
		add("%s %q resolves PART TWO of its citation BY FILE NAME ONLY: the capture_case_id %q occurs "+
			"in neither the artefact's bytes nor the .http sidecar beside it, only in the artefact's "+
			"own file name -- which this citation SUPPLIED. That branch reads ZERO bytes of the "+
			"artefact: it compares two fields of this vector to each other, and it passes whenever the "+
			"ref was spelled from the case id, which is how every ref in this store is spelled. It is "+
			"therefore not evidence that the artefact answers to the case id, and it may not arrive "+
			"silently. Either file the id into the .http sidecar at capture time -- the rig can, the "+
			"oracle cannot -- or add this (case_id, field) pair to citationNameOnlyPin in admit.go "+
			"with its reason, which is a source edit a reviewer reads. A2-34 F-3, closed by T243",
			field, ref, caseID)
		return out
	}
	add("provenance.capture_case_id %q occurs neither in the bytes of %s (%q), nor in the .http sidecar "+
		"beside it, nor in its file name. The citation names an artefact that does not answer to the "+
		"case id it claims", caseID, field, ref)
	return out
}

// ---------------------------------------------------------------------------
// PART TWO OF THE CITATION: HOW IT RESOLVED, AND THE FRONTIER OF ITS WEAKEST
// BRANCH.  [T243, closing A2-34's F-3]
// ---------------------------------------------------------------------------
//
// THE FINDING. A2-34 reported that part two of T233's three-part citation
// "resolves by FILE NAME" on LDG-01/02/03's response artefacts, so the check
// "passes without demonstrating anything". T243 re-measured all TWELVE citations
// in the committed store and the finding holds, with one refinement worth
// having: it is the THIRD branch (file name), not the first (bytes), that
// carries those three -- the id is not in the response bytes at all.
//
//	LDG-01 capture_ref  A2-347-je-manual-readback.json           bytes NO  sidecar NO  name YES
//	LDG-02 capture_ref  A2-338-je-after-repayment-coverage.json  bytes NO  sidecar NO  name YES
//	LDG-03 capture_ref  A2-383-je-after-overpay.json             bytes NO  sidecar NO  name YES
//	LDG-04 capture_ref  A2-390-db-ledger-state-a2-15.json        bytes YES
//	the other eight citations                                    sidecar YES
//
// THE DECISION, AND THE ARGUMENT FOR IT. Part two is KEPT, not retired, and its
// weakest branch is CLASSIFIED, COUNTED, PRINTED and PINNED.
//
//  1. RETIRING IT WOULD LOSE A PROPERTY THE SHA256 DOES NOT CARRY. The digest
//     answers "are these the bytes this vector transcribed?". It cannot answer
//     "is this artefact the capture case the vector NAMES?", because a citation
//     that points at a DIFFERENT artefact and records THAT artefact's correct
//     digest satisfies the digest check completely. Part two is the only thing
//     that notices, and T243 drove exactly that case red through
//     conformance.sh before writing this paragraph. The two checks answer
//     different questions and neither subsumes the other, so "the sha256 makes
//     part two redundant" is FALSE.
//
//  2. BUT THE FILE-NAME BRANCH IS NOT A CHECK ON THE ARTEFACT. It reads none of
//     the artefact's bytes. It asks whether the ref string contains the case_id
//     string -- two fields of the same vector, written by the same author in
//     the same edit -- and in this store every ref is spelled
//     "<capture dir>/out/<case-id><ext>", so that branch cannot fail for any
//     citation written the ordinary way. That is the tautology A2-34 named, and
//     leaving it as an unmarked third alternative lets a name-only citation
//     arrive silently and be read as though it had resolved against bytes.
//
//  3. SO: name-only stays admissible ONLY for the pinned three, is refused for
//     anything else, and the population is printed on every run. BOTH
//     directions are gated -- a fourth name-only citation is INADMISSIBLE
//     (inflation), and a pinned one that starts resolving some stronger way is
//     a FATAL telling the author to delete the stale pin (deflation). The pin
//     is by (case_id, field) IDENTITY, not by count, so a swap that leaves the
//     total at three is caught too.
//
// WHY NOT SIMPLY REFUSE ALL THREE AND BE DONE WITH IT. Because that would make
// three of the four ledger PARITY vectors inadmissible over a gap in the
// CAPTURE RIG, not a defect in the vectors: the rig writes the case id into the
// .http sidecar for a request and not for a readback response. The repair
// belongs in the rig at the next capture. Until then the frontier is three, it
// is named in source with its reason, and it cannot grow without a source edit.
//
// LIMIT OF THIS CLASSIFICATION, MEASURED AND STATED (P-66). CitationBySidecar
// counts as stronger than name-only because it reads a SECOND file, one the rig
// wrote. It is not uniformly strong: on the six `.req` citations the id occurs
// in the sidecar only inside a `body-wire-bytes-artefact: <case-id>.req` line,
// which is itself a file name, one file over. That is still a second artefact
// attesting the link rather than a vector agreeing with itself -- which is the
// line drawn here -- but it is weaker than CitationByBytes, and this comment is
// where a reader finds that out instead of assuming otherwise.

// CitationMode records HOW part two of a capture citation resolved. It is a
// property of the RUN, not of the vector file, so it is recomputed every run.
type CitationMode string

const (
	// CitationByBytes: the case id occurs in the artefact's own bytes.
	CitationByBytes CitationMode = "ARTEFACT-BYTES"
	// CitationBySidecar: the case id occurs in the .http sidecar beside it.
	CitationBySidecar CitationMode = "HTTP-SIDECAR"
	// CitationByNameOnly: the case id occurs ONLY in the artefact's own file
	// name, which the citation itself supplied. ZERO bytes of the artefact were
	// read to reach this verdict.
	CitationByNameOnly CitationMode = "FILE-NAME-ONLY"
	// CitationUnresolved: it occurs in none of the three, or the artefact could
	// not be read. citationReasons refuses the vector.
	CitationUnresolved CitationMode = "UNRESOLVED"
)

// CitationResolution is one citation and the way it resolved on this run.
type CitationResolution struct {
	VectorCaseID string
	Field        string
	Ref          string
	CaseID       string
	Mode         CitationMode
}

// citationNameOnlyPin is the FRONTIER: the (vector case_id, provenance field)
// pairs whose part two is permitted to resolve by file name alone, each with
// its reason. Adding a row is a source edit; see the block above.
var citationNameOnlyPin = map[string]string{
	citationPinKey("LDG-01-manual-je-3leg-minor-units", "provenance.capture_ref"): "" +
		"A2-347-je-manual-readback.json is a GET /journalentries response body: the oracle emitted it " +
		"and cannot know our case id, and the rig's .http sidecar for a readback records the request " +
		"line but not the id. A rig gap, not a vector defect",
	citationPinKey("LDG-02-repayment-split-4leg-minor-units", "provenance.capture_ref"): "" +
		"A2-338-je-after-repayment-coverage.json: same shape, same rig gap as LDG-01",
	citationPinKey("LDG-03-overpayment-4leg-minor-units", "provenance.capture_ref"): "" +
		"A2-383-je-after-overpay.json: same shape, same rig gap as LDG-01",
}

func citationPinKey(vectorCaseID, field string) string { return vectorCaseID + "|" + field }

// CitationNameOnlyPinCount is the pinned population of file-name-only
// resolutions. conformance.sh needs no tenth census pin for it: the equality is
// gated inside this package, in both directions.
func CitationNameOnlyPinCount() int { return len(citationNameOnlyPin) }

// citationMode classifies one citation's part two. It is the SINGLE definition
// used both by the admissibility refusal and by the census, so the figure the
// report prints and the rule that refuses cannot drift apart.
func citationMode(repoRoot, ref, caseID string) CitationMode {
	if strings.TrimSpace(ref) == "" || caseID == "" || filepath.IsAbs(ref) {
		return CitationUnresolved
	}
	abs := filepath.Join(repoRoot, ref)
	raw, err := os.ReadFile(abs)
	if err != nil {
		return CitationUnresolved
	}
	if strings.Contains(string(raw), caseID) {
		return CitationByBytes
	}
	base := strings.TrimSuffix(abs, filepath.Ext(abs))
	base = strings.TrimSuffix(base, ".req")
	if side, serr := os.ReadFile(base + ".http"); serr == nil && strings.Contains(string(side), caseID) {
		return CitationBySidecar
	}
	if strings.Contains(filepath.Base(abs), caseID) {
		return CitationByNameOnly
	}
	return CitationUnresolved
}

// CitationResolutions classifies both of a vector's citations.
func CitationResolutions(v *Vector, repoRoot string) []CitationResolution {
	return []CitationResolution{{
		VectorCaseID: v.CaseID,
		Field:        "provenance.capture_ref",
		Ref:          v.Provenance.CaptureRef,
		CaseID:       v.Provenance.CaptureCaseID,
		Mode:         citationMode(repoRoot, v.Provenance.CaptureRef, v.Provenance.CaptureCaseID),
	}, {
		VectorCaseID: v.CaseID,
		Field:        "provenance.request_capture_ref",
		Ref:          v.Provenance.RequestCaptureRef,
		CaseID:       v.Provenance.RequestCaptureCaseID,
		Mode: citationMode(repoRoot, v.Provenance.RequestCaptureRef,
			v.Provenance.RequestCaptureCaseID),
	}}
}

// StaleCitationPins returns a reason for every pinned name-only citation that
// did NOT resolve name-only on this run, over the vectors actually loaded. This
// is the DEFLATION direction: a pin that no longer describes the corpus excuses
// a weakness that is not there, and the harness says so rather than quietly
// agreeing with itself.
//
// A pinned vector that is ABSENT from this run is deliberately NOT reported
// here. A missing ledger vector is caught, loudly and by count, by
// EXEMPTION_PIN_LEDGER_PARITY in conformance.sh; duplicating that refusal here
// would make a context-filtered run look like a stale pin.
func StaleCitationPins(res []CitationResolution, loaded map[string]bool) []string {
	var out []string
	seen := map[string]CitationMode{}
	for _, r := range res {
		seen[citationPinKey(r.VectorCaseID, r.Field)] = r.Mode
	}
	keys := make([]string, 0, len(citationNameOnlyPin))
	for k := range citationNameOnlyPin {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		caseID := k
		if i := strings.Index(k, "|"); i >= 0 {
			caseID = k[:i]
		}
		if !loaded[caseID] {
			continue
		}
		if m, ok := seen[k]; !ok || m != CitationByNameOnly {
			out = append(out, fmt.Sprintf(
				"citationNameOnlyPin carries %q, but part two of that citation resolved %s on this "+
					"run, not FILE-NAME-ONLY. The pin excuses a weakness that is no longer there: "+
					"DELETE that row from admit.go. A pin nothing needs is a sentence nothing checks",
				k, m))
		}
	}
	return out
}
