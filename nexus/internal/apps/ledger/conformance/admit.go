package conformance

import (
	"bytes"
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
	case ClassParity, ClassOracleRefusal, ClassDivergence:
	default:
		add("class %q is not one this schema knows (parity, oracle-refusal, divergence)", v.Class)
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
	//
	// [T429, G-22] THE NOTE CHECK BELOW IS NO LONGER THE ONLY ARM. It reads what
	// the author WROTE; the arm added after it reads what the author CAPTURED.
	// A2-29 section 6 item 1 -- "a ledger parity vector must not set
	// runningBalance=true or fetchRunningBalance=true" -- had been a sentence in
	// the gate register that nothing checked, and a rule enforced only by the
	// diligence of the person it constrains is not enforced (P-45).
	bad = append(bad, opts.OracleDerived.CaptureRuleReasons(opts.RepoRoot, v)...)
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
		// --- THE PER-LEG SLOT INPUTS, default-deny in BOTH directions [T391] --
		//
		// The rules below are what stop the accounting-path fields becoming a
		// hole, and they are the same shape T294 gave the opening-balance
		// inputs:
		//
		//   * a leg may carry an ACCOUNT ID or a SLOT CODE and NOT BOTH, because
		//     a leg that carries both hands the implementation the answer it was
		//     supposed to resolve, and the `gl_account_id` cell silently stops
		//     being an output;
		//   * a leg that carries NEITHER has said nothing about where it landed;
		//   * a slot code with no mapping table to resolve it through REFUSES,
		//     rather than reaching the port and becoming a harness error;
		//   * a mapping table on a vector NO leg resolves through REFUSES, so
		//     the field cannot accumulate on the manual corpus;
		//   * and the ENTRY-LEVEL slot_code must be 0 wherever per-leg codes are
		//     used. P-1's single slot_code names ONE slot and an accrual
		//     transaction spans SIX; two places to say which slot an entry used
		//     is two places that can disagree, and admit.go's job is that they
		//     cannot.
		anySlotLeg := false
		for i, l := range v.Request.Legs {
			switch {
			case l.SlotCode != 0 && l.AccountID != 0:
				add("request.legs[%d] carries BOTH gl_account_id %d AND slot_code %d. An "+
					"accounting-path leg names the SLOT and the implementation RESOLVES the account "+
					"through request.product_mappings; carrying the account too hands it the answer "+
					"and turns expect.legs[%d].gl_account_id from an output back into an echo",
					i, l.AccountID, l.SlotCode, i)
			case l.SlotCode == 0 && l.AccountID == 0:
				add("request.legs[%d] carries NEITHER a gl_account_id NOR a slot_code, so it does not "+
					"say where this leg landed or how it got there", i)
			case l.SlotCode < 0:
				add("request.legs[%d].slot_code is %d. A placeholder code is a positive "+
					"acc_product_mapping.financial_account_type", i, l.SlotCode)
			}
			if l.SlotCode != 0 {
				anySlotLeg = true
			}
		}
		if anySlotLeg && len(v.Request.ProductMappings) == 0 {
			add("request.legs carry per-leg slot codes and request.product_mappings is EMPTY. The " +
				"account is resolved by keying the product's OBSERVED acc_product_mapping rows with " +
				"the slot code; with no rows there is nothing to resolve through, and a vector that " +
				"cannot be resolved has not recorded an observation anybody can re-derive")
		}
		if anySlotLeg && v.Request.SlotCode != 0 {
			add("request.slot_code is %d AND request.legs carry per-leg slot codes. P-1's "+
				"entry-level slot_code names ONE slot and an accrual transaction spans SIX "+
				"(INTEREST_RECEIVABLE/FEES_RECEIVABLE/PENALTIES_RECEIVABLE against "+
				"INTEREST_ON_LOANS/INCOME_FROM_FEES/INCOME_FROM_PENALTIES on a single transaction "+
				"id). Leave the entry-level field 0 and let the legs carry it", v.Request.SlotCode)
		}
		// G-06.
		if v.Request.SlotCode == 1 && v.Request.PaymentTypeID == nil {
			add("G-06: slot_code 1 (FUND_SOURCE) with a nil payment_type_id is REFUSED. The oracle " +
				"issues the payment-type finder with a null argument and no null guard " +
				"(AccountingProcessorHelper.java:1199-1206), two readings of what that matches are " +
				"defensible, and no capture separates them")
		}
	}
	// --- the accounting-path inputs OUTSIDE the product block [T391] --------
	//
	// The rules above bind only where a product took part. These three bind
	// everywhere, because they are the ones that keep the fields from appearing
	// where no product did.
	{
		slotLegs := 0
		for _, l := range v.Request.Legs {
			if l.SlotCode != 0 {
				slotLegs++
			}
		}
		if slotLegs > 0 && v.Request.ProductID == 0 {
			add("request.legs carry %d per-leg slot code(s) and request.product_id is 0. A slot is a "+
				"PRODUCT's placeholder — acc_product_mapping is keyed on (product_id, product_type, "+
				"financial_account_type) — so a slot with no product is a key with a hole in it",
				slotLegs)
		}
		if slotLegs == 0 && len(v.Request.ProductMappings) > 0 {
			add("request.product_mappings carries %d row(s) and NO leg resolves through any of them. "+
				"An input nothing consumes is how the opening-balance fields would have accumulated "+
				"on the manual corpus, and it is refused here for the same reason",
				len(v.Request.ProductMappings))
		}
		seenSlot := map[int32]bool{}
		inChart := map[int64]bool{}
		for _, a := range v.Request.Accounts {
			inChart[a.ID] = true
		}
		for i, m := range v.Request.ProductMappings {
			if m.SlotCode <= 0 {
				add("request.product_mappings[%d].slot_code is %d; a placeholder code is positive",
					i, m.SlotCode)
			}
			if seenSlot[m.SlotCode] {
				add("request.product_mappings names slot_code %d twice. The oracle's own lookup is "+
					"getSingleResult() and a duplicate is an ERROR there, not a first-match "+
					"(A2-086-disburse-loan3-dupchannel); a vector carrying a duplicate is asserting "+
					"an observation the oracle would have refused", m.SlotCode)
			}
			seenSlot[m.SlotCode] = true
			if m.GLAccountID <= 0 {
				add("request.product_mappings[%d].gl_account_id is %d", i, m.GLAccountID)
				continue
			}
			if !inChart[m.GLAccountID] {
				add("request.product_mappings[%d] resolves slot %d to GL account %d, which is NOT in "+
					"request.accounts. A mis-keying port that lands on that row would then fail as a "+
					"HARNESS ERROR rather than as a graded cell difference, and a defect that shows "+
					"up as a crash is a defect the comparator did not catch",
					i, m.SlotCode, m.GLAccountID)
			}
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
	// description — defining opening balances after a NON-CONTRA journal entry
	// has been posted, an entry dated on or before the latest GLClosure, and a
	// future-dated entry — and T294 flipped the row to in_graded_domain TRUE on
	// the strength of the FIRST one only. [HISTORY, TRUE WHEN T296 WROTE IT AND NO
	// LONGER TRUE: at that moment the other two were captured raw in
	// .softhouse/capture/t287-closure-refusals and nothing promoted them. T295
	// promoted both, and T305 then captured the ACCEPTING side of the first.
	// See the adjudicated gate below.]
	//
	// [CORRECTED T322, and this is THE FIFTH SITE of a refuted rule. The first
	// shape above used to read "after journal entries have been posted" — the
	// oracle's own :814 message, which is WRONG: findNonContraTransactionIds
	// EXCLUDES every transaction that touches the contra account and every entry
	// an opening balance writes touches it (:796), so OPENING BALANCES DO NOT
	// BLOCK EACH OTHER [T305, OB-ACCEPT-02: byte-identical bytes, HTTP 200 a
	// second time, the first one REVERSED]. T305 corrected three sites, T320
	// found a fourth (the registry row's own `description`), and this comment is
	// the fifth — it is here BECAUSE it QUOTES that description, which is exactly
	// how a wrong first field propagates: the longest field gets the correction
	// and the shortest one gets copied. Both are fixed in T322's diff.]
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
		// WHAT THIS STORE HAS OBSERVED ON THIS ROW IS SIX VECTORS [T328; T306 read four,
		// and the ASYMMETRY it recorded IS NOW GONE — that asymmetry was the entire reason
		// its arms differed, so read this table before the paragraphs below, which are
		// kept as history]:
		//
		//   the defineOpeningBalance command — BOTH SIDES of :811's emptiness test
		//     LDG-REFUSE-03  REFUSAL   findNonContraTransactionIds NON-EMPTY  :717 -> :810-813
		//     LDG-05         ACCEPTED  findNonContraTransactionIds EMPTY, :812 falls through,
		//                              HTTP 200 and SIX journal entries for three request legs
		//   the CLOSURE boundary — BOTH SIDES of :636
		//     LDG-REFUSE-04  REFUSAL   txn ON the closing date, !isBefore(closing, txn)  :636
		//     LDG-06         ACCEPTED  txn one day AFTER the closing date, HTTP 200, three
		//                              journal entries and no contra expansion    [T327 B-1]
		//   the FUTURE-DATE guard — BOTH SIDES of :629-631
		//     LDG-REFUSE-05  REFUSAL   txn one day after the business date, isDateInTheFuture
		//     LDG-07         ACCEPTED  txn ON the business date, HTTP 200 — the only
		//                              observation here that tells isAfter from !isBefore,
		//                              i.e. a STRICT comparison from a non-strict one
		//                                                                        [T327 B-2]
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
		// ***** EVERYTHING FROM HERE TO THE PREDICATE IS T306's REASONING AND IS KEPT AS
		// HISTORY. ITS CONCLUSION -- "the date arms KEEP the expect.kind precondition" --
		// IS SUPERSEDED BY T328, whose own paragraph sits directly above the predicate. It
		// is left visible rather than deleted for the reason this store applies to every
		// refuted rule: it was quoted forward (in T306's handoff, in openingbalance_test.go
		// and in this file's own message string), and a reader who meets it there must be
		// able to find the correction. NOTE WHAT T328 MEASURED ABOUT IT: the edit this
		// paragraph prescribes -- "drop `v.Expect.Kind == \"refusal\"` from the date arms"
		// -- WOULD HAVE ADMITTED NEITHER PROMOTED VECTOR, because both preconditions it
		// names are the REFUSING-region comparisons. The instruction was right about WHEN
		// to widen and wrong about WHAT to widen. *****
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
		// ***** T328 WIDENED THE TWO DATE ARMS, DELIBERATELY, WITH THE CAPTURE IN HAND,
		// AND THE PRECONDITION IT DROPPED IS NOT THE ONE THE COMMENT ABOVE PREDICTED.
		// *****
		//
		// The prediction above was "drop `v.Expect.Kind == \"refusal\"` from the date
		// arms". THAT ALONE WOULD HAVE ADMITTED NOTHING, and it was measured before it was
		// argued: `preClosureInputs` is `!isoBefore(closing, txn)`, which is TRUE only when
		// the transaction date is ON OR BEFORE the closing date -- the REFUSING region.
		// T327's B-1 arm is dated ONE DAY AFTER the closing date, so preClosureInputs is
		// FALSE on it, and the same asymmetry holds for `futureDatedInputs` against B-2
		// (dated ON the business date, so isoAfter is false). Both promoted vectors sit in
		// the ACCEPTING region of their comparison, which is the whole reason they are
		// worth capturing, and the old predicate had no term that could ever be true for
		// them. Dropping the expect.kind precondition would have left the gate refusing
		// them and the task would have "widened" nothing [MEASURED:
		// .softhouse/capture/t328-date-rule-promotion/out/40-RED-door-is-closed-inadmissible.txt
		// -- both vectors INADMISSIBLE on this rule with the pre-T328 predicate].
		//
		// SO THE SHAPE IS NOW KEYED ON THE REGION, AND THE EXPECTATION MUST AGREE WITH THE
		// REGION. Four date shapes are observed on this row, not two, and the store now
		// carries a vector for each:
		//
		//   the CLOSURE boundary at :636, !isBefore(closingDate, transactionDate)
		//     txn <= closing   REFUSED   LDG-REFUSE-04 (txn ON the closing date, 403)
		//     txn >  closing   ACCEPTED  LDG-06 (closing 2026-08-26, txn 2026-08-27, 200)
		//   the FUTURE-DATE guard at :629-631, isAfter(transactionDate, businessDate)
		//     txn >  business  REFUSED   LDG-REFUSE-05 (business + 1, 403)
		//     txn <= business  ACCEPTED  LDG-07 (txn ON the business date, 200)
		//
		// [VERIFIED: the two acceptances are HTTP 200 in
		// .softhouse/capture/t327-closure-accepting-side/throwaway/out/
		// B1-ACCEPT-06-entry-one-day-after-closing-date.status and
		// B2-ACCEPT-01-entry-on-business-date.status, promoted by T328's builder.]
		//
		// THIS IS STILL KEYED ON THE REQUEST, WHICH IS T306-F-2's RULE AND IT SURVIVES.
		// The REGION is computed from the vector's own two dates by the same comparison the
		// oracle makes; expect.kind is then required to AGREE with the region, and
		// expect.refusal.code is still never read here. That is not "keying on the answer":
		// a vector claiming the oracle REFUSED where the store observed it ACCEPTING, or
		// ACCEPTED where the store observed it refusing, is claiming coverage of a shape
		// nobody captured, and the region is what says which. DEFAULT-DENY IS PRESERVED IN
		// BOTH DIRECTIONS and is exercised by
		// TestOpeningBalanceCapabilityIsScopedToTheObservedShape: a vector with NO date
		// inputs is still refused, an ACCEPTANCE in a REFUSING region is still refused, and
		// T328 adds the mirror arm -- a REFUSAL in an ACCEPTING region -- which the old
		// predicate also refused but for the accidental reason that it refused every
		// accepting-region shape.
		openingBalanceCommand := v.Request.Command == "defineOpeningBalance"
		closureInputs := v.Request.LatestClosingDate != "" && v.Request.TransactionDate != ""
		businessInputs := v.Request.TransactionDate != "" && v.Request.BusinessDate != ""
		preClosureInputs := closureInputs &&
			!isoBefore(v.Request.LatestClosingDate, v.Request.TransactionDate)
		futureDatedInputs := businessInputs &&
			isoAfter(v.Request.TransactionDate, v.Request.BusinessDate)
		postClosureInputs := closureInputs &&
			isoBefore(v.Request.LatestClosingDate, v.Request.TransactionDate)
		onOrBeforeBusinessDateInputs := businessInputs &&
			!isoAfter(v.Request.TransactionDate, v.Request.BusinessDate)
		// THE REFUSING REGION WINS WHEN BOTH APPLY, because the oracle refuses as soon as
		// EITHER guard fires: a vector that is past the closure but future-dated is a
		// refusal shape, not an accepting one.
		refusingRegion := preClosureInputs || futureDatedInputs
		acceptingRegion := (postClosureInputs || onOrBeforeBusinessDateInputs) && !refusingRegion
		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && refusingRegion) ||
			(v.Expect.Kind != "refusal" && acceptingRegion)
		if !observedShape {
			add("capabilities_required names %q on a vector whose request.command is %q, whose "+
				"expect.kind is %q, and whose date inputs are transaction_date %q, business_date %q, "+
				"latest_closing_date %q. THE SHAPES THIS STORE HAS OBSERVED ARE: the "+
				"defineOpeningBalance-after-a-NON-CONTRA-entry refusal at "+
				"JournalEntryWritePlatformServiceJpaRepositoryImpl.java:717 (LDG-REFUSE-03) and its "+
				"ACCEPTING side at :812 (LDG-05, HTTP 200 and six entries on an empty ledger) -- so on "+
				"that COMMAND either expectation is covered -- and BOTH SIDES OF BOTH DATE "+
				"BOUNDARIES: the PRE-CLOSURE refusal at :636 (LDG-REFUSE-04, transaction date ON the "+
				"closing date) with its ACCEPTING side one day later (LDG-06, HTTP 200), and the "+
				"FUTURE-DATED refusal at :629-631 (LDG-REFUSE-05, one day after the business date) "+
				"with its ACCEPTING side ON the business date (LDG-07, HTTP 200, which is the only "+
				"observation in this store that tells a STRICT comparison from a non-strict one). "+
				"THE CLAIM IS DECIDED BY THIS VECTOR'S REQUEST -- the same two date comparisons the "+
				"oracle makes -- and never by the refusal code it declares, because that is the "+
				"answer it is asking to be believed about. WHAT IS STILL REFUSED, and this is "+
				"default-deny rather than an oversight: a vector claiming this row with NO date "+
				"inputs and no opening-balance command (nothing decides it); a vector claiming the "+
				"oracle ACCEPTED with dates in a REFUSING region; and a vector claiming the oracle "+
				"REFUSED with dates in an ACCEPTING region. Each of those describes an observation "+
				"nobody took. A capture is not a vector: this gate keys on the STORE, never on the "+
				"contents of a capture directory",
				name, v.Request.Command, v.Expect.Kind, v.Request.TransactionDate,
				v.Request.BusinessDate, v.Request.LatestClosingDate)
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
	// -----------------------------------------------------------------------
	// THE ARG-ECHO SELECTOR: default-deny, and it is T294's refusal made a RULE
	// -----------------------------------------------------------------------
	//
	// T295 backlog B-3 asked for `errors[0].args` to be graded so that A2-02 —
	// whose captured body is byte-identical to A2-01's on all three existing
	// cells — becomes promotable. T294 had DELIBERATELY declined to grade its
	// OWN args on OB-01, where the field carries 26 LIVE TRANSACTION IDS. These
	// four rules are what make both positions hold simultaneously, and they are
	// stated as an ADMISSIBILITY rule rather than left to an author's judgement
	// precisely because T295 was right that a judgement is not inheritable.
	//
	//   (1) THE VOCABULARY IS CLOSED to the two SCALAR calendar dates this
	//       schema already declares. There is no selector that names a list, so
	//       OB-01's claim CANNOT BE WRITTEN DOWN in this schema at all.
	//   (2) EACH SELECTOR IS BOUND TO THE CODE ITS THROW SITE PAIRS IT WITH,
	//       and the binding is source-derived, not conventional:
	//         :631  FUTURE_DATE       <- transactionDate
	//         :637  ACCOUNTING_CLOSED <- latestGLClosure.getClosingDate()
	//       [VERIFIED: JournalEntryWritePlatformServiceJpaRepositoryImpl.java,
	//       pinned 426a23544.] A vector pairing them the other way is asserting
	//       an observation nobody took, exactly as a mis-ordered date relation
	//       is above.
	//   (3) IT IS REQUIRED, not optional, on those two codes. An optional cell
	//       is a cell an author can drop the day it becomes inconvenient, which
	//       is the deflation direction this store pins everything against.
	//   (4) IT IS FORBIDDEN on every other refusal code and on every
	//       non-refusal vector. LDG-REFUSE-03's code is
	//       error.msg.journalentry.defining.openingbalance.not.allowed, so this
	//       rule — not a reviewer's memory of T294 — is what keeps its 26-id
	//       list ungraded.
	//
	// THE SECOND, INDEPENDENT GROUND for (4), recorded here because it survives
	// even if someone later widens the vocabulary: LDG-REFUSE-03's
	// request.posted_non_contra_transaction_ids was TRANSCRIBED FROM
	// errors[0].args[0].value itself, so resolving a selector against it would
	// compare the captured body with a copy of itself. Both selectors admitted
	// below have provenance INDEPENDENT of the body being graded — the caller's
	// own committed .req bytes, and the create-closure request confirmed by SQL.
	if e := v.Expect.Refusal.ArgEcho; e != "" {
		if _, ok := ResolveArgEcho(e, v.Request); !ok {
			add("expect.refusal.arg_echo is %q. The vocabulary is CLOSED to %q and %q -- the two "+
				"SCALAR calendar-date inputs this schema declares, each with provenance independent "+
				"of the response body being graded. It is closed on purpose: `errors[0].args[0].value` "+
				"is a JSON STRING only when the oracle put a LocalDate there "+
				"[ApiParameterError.java:95-105 special-cases exactly that one type], and on OB-01 it "+
				"is an ARRAY of 26 LIVE TRANSACTION IDS. A selector naming tenant-mutable history is "+
				"not a selector this store admits", e, ArgEchoTransactionDate, ArgEchoLatestClosingDate)
		} else if v.Expect.Kind != "refusal" {
			add("expect.refusal.arg_echo is %q on a vector whose expect.kind is %q. errors[0].args "+
				"exists only on a refusal body; there is nothing for this selector to name",
				e, v.Expect.Kind)
		}
	}
	if v.Expect.Kind == "refusal" {
		want := ""
		switch v.Expect.Refusal.Code {
		case codeFutureDate:
			want = ArgEchoTransactionDate
		case codeAccountingClosed:
			want = ArgEchoLatestClosingDate
		}
		got := v.Expect.Refusal.ArgEcho
		switch {
		case want != "" && got != want:
			add("this vector expects %q and its expect.refusal.arg_echo is %q; it must be %q. The "+
				"throw site that raises this code constructs the exception with THAT date and no "+
				"other (:631 passes transactionDate, :637 passes "+
				"latestGLClosure.getClosingDate()), so the two refusals put DIFFERENT quantities in "+
				"the SAME wire field. A vector that omits the selector grades one cell fewer than the "+
				"capture supports; one that names the wrong input records an observation nobody took",
				v.Expect.Refusal.Code, got, want)
		case want == "" && got != "":
			add("this vector expects %q and carries expect.refusal.arg_echo %q. An arg echo is "+
				"admitted ONLY on %q and %q, whose throw sites pass a LocalDate that this schema "+
				"already declares as an input. Every other refusal in this corpus either carries no "+
				"args date or carries TENANT-MUTABLE HISTORY there -- LDG-REFUSE-03's is a list of 26 "+
				"live transaction ids, transcribed FROM the body being graded, and grading it would "+
				"pin a parity claim to a value any unrelated posting changes (T294, upheld by T307)",
				v.Expect.Refusal.Code, got, codeFutureDate, codeAccountingClosed)
		}
		if got != "" {
			if resolved, ok := ResolveArgEcho(got, v.Request); ok && resolved == "" {
				add("expect.refusal.arg_echo is %q and request.%s is EMPTY. The selector resolves to "+
					"nothing, so the comparator would grade the empty string against the empty string "+
					"-- a comparison that cannot fail, printed in the same words as one that can",
					got, got)
			}
		}
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
	case "port-refusal":
		bad = append(bad, divergenceReasons(v, opts)...)
	default:
		add("expect.kind %q is not one this schema knows (journal-entry, refusal, port-refusal)",
			v.Expect.Kind)
	}
	// THE OTHER DIRECTION. A divergence vector may not wear any other
	// expectation shape, and a non-divergence vector may not carry the oracle
	// acceptance block. Both are checked here rather than only inside
	// divergenceReasons, because a rule that only fires on the class it
	// describes cannot see a vector of another class that quietly grew the
	// field -- which is precisely how expect.legs would accumulate on refusal
	// vectors if the `case "refusal"` arm were the only guard.
	if v.Class == ClassDivergence && v.Expect.Kind != "port-refusal" {
		add("class divergence with expect.kind %q. A divergence records the ORACLE ACCEPTING a request "+
			"THIS PORT REFUSES; its only admissible expectation shape is \"port-refusal\", because "+
			"there is no port-side entry to describe and no port-side amount to grade", v.Expect.Kind)
	}
	if v.Class != ClassDivergence && !v.OracleAccepted.IsZero() {
		add("oracle_accepted is populated on a %q vector. It is the ORACLE'S side of a DIVERGENCE and "+
			"it carries an amount as CHARACTERS precisely because no int64 minor-unit cell can hold "+
			"it. Carrying it anywhere else records an unrepresentable observation that nothing grades "+
			"and nothing gates", v.Class)
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
		// AN ACCOUNTING-PATH LEG NAMES NO ACCOUNT AND THAT IS THE POINT, so the
		// chart rule below binds only on a leg that names one. The equivalent
		// guarantee for a slot leg is stronger, not weaker: the per-leg block
		// above requires EVERY mapping row's gl_account_id to be in the chart,
		// so whichever row a port keys to, the account it lands on resolves.
		// [T391]
		if l.SlotCode == 0 && !chart[l.AccountID] {
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

// MinPortRefusalMarker is the shortest phrase a divergence vector may declare as
// the marker of the port's refusal.
//
// A SHORT MARKER IS A COMPARISON THAT CANNOT FAIL, which is the one shape every
// vacuous guard in this program has had (P-35). "at" is contained in almost any
// English sentence; a two-character marker would let a port refuse for ANY
// reason and be graded as agreeing with the recorded divergence. Twelve
// characters is not a magic number -- it is the shortest length that excludes
// every fragment of the other refusal texts in this store and is comfortably
// shorter than the phrase the port actually emits.
const MinPortRefusalMarker = 12

// divergenceReasons is the admissibility rule set for the DIVERGENCE class.
// [T360, G-19]
//
// THE HARD PART OF THIS CLASS IS THAT IT MUST RECORD A VALUE NO int64 CAN HOLD,
// AND MUST DO SO WITHOUT PUTTING A FLOAT ANYWHERE NEAR A MONEY PATH. The rules
// below are how that is made safe rather than merely promised:
//
//   - THE MONEY CELLS ARE FORBIDDEN OUTRIGHT. expect.legs, expect.total_*_minor
//     and expect.refusal must all be empty. `amount_minor` cannot appear on a
//     divergence vector at all, so no author is ever placed in the position T352
//     was placed in -- having to write a number no system produced in order to
//     file the observation. It is not that the number is hard to choose; it is
//     that the field is not there.
//
//   - THE ORACLE'S VALUE IS CHARACTERS AND IS BYTE-CHECKED. Every entry of
//     oracle_accepted.observed_amount_texts must occur VERBATIM in the bytes of
//     the artefact provenance.capture_ref names. Not re-serialised, not
//     re-formatted, not "equal after parsing" -- the same bytes, found with
//     bytes.Contains. The one thing this rule cannot be satisfied by is a
//     transcription somebody typed.
//
//   - AND SO IS THE REQUEST'S. Every request leg's amount_major_text must occur
//     verbatim in the bytes of provenance.request_capture_ref. The two sides of
//     the divergence are then each anchored to their own capture, and the
//     characters the port converts are demonstrably the characters the caller
//     sent -- which for this vector are `100.125` (the request) against
//     `100.125000` (the readback), two different renderings of one observation
//     that a single "amount text" field would have quietly conflated.
//
//   - THE OBSERVATION MUST ACTUALLY BE UNREPRESENTABLE. At least one observed
//     text must carry a NON-ZERO digit beyond the currency's minor unit.
//     Otherwise it is an ordinary amount and the vector belongs in the parity
//     class -- a divergence badge on a representable value would be a way to
//     move a vector out of the parity tally and keep the run green.
//
//     THE SCAN IS PURE BYTES. It finds the '.', walks the fraction digits by
//     index and compares each byte with '0'. No strconv, no big.Float, no
//     division, no exponent -- nothing that could be called an intermediate
//     calculation on a money value. The amount is never a number in this
//     program.
func divergenceReasons(v *Vector, opts Options) []string {
	var bad []string
	add := func(f string, a ...any) { bad = append(bad, fmt.Sprintf(f, a...)) }

	if v.Class != ClassDivergence {
		add("expect.kind port-refusal on a %q vector; only a divergence vector records the ORACLE "+
			"ACCEPTING what this port REFUSES", v.Class)
	}

	// --- the money cells are not merely empty, they are FORBIDDEN ------------
	if len(v.Expect.Legs) > 0 {
		add("expect.legs has %d entries on a DIVERGENCE vector. There is no port-side entry: the port "+
			"REFUSED. And there is no oracle-side amount that can be written here either -- "+
			"expect.legs[].amount_minor is an int64 count of minor units and the value observed is "+
			"%v in a currency whose declared minor unit is %d. Writing 10012 or 10013 records a number "+
			"NEITHER SYSTEM PRODUCED, which is the exact way an unobserved figure enters a store",
			len(v.Expect.Legs), v.OracleAccepted.ObservedAmountTexts, v.Request.Currency.MinorUnitDigits)
	}
	if v.Expect.TotalDebitsMinor != "" || v.Expect.TotalCreditsMinor != "" {
		add("expect totals are set on a DIVERGENCE vector; the port posted nothing to total")
	}
	if v.Expect.Refusal != (Refusal{}) {
		add("expect.refusal is populated on a DIVERGENCE vector. That block is an ORACLE-OBSERVED wire " +
			"refusal -- HTTP status, globalisation code, message -- and the oracle did not refuse: it " +
			"returned 200. The port's own refusal goes in expect.port_refusal, which has no HTTP " +
			"status because a port refusal was never on a wire")
	}
	if v.Expect.HTTPStatus != 0 {
		add("expect.http_status is %d on a DIVERGENCE vector. `expect` is what the IMPLEMENTATION must "+
			"produce and this port produces no HTTP response at all; the ORACLE's status belongs in "+
			"oracle_accepted.http_status, where it is unmistakably an observation",
			v.Expect.HTTPStatus)
	}

	// --- the port's side ----------------------------------------------------
	marker := strings.TrimSpace(v.Expect.PortRefusal.Marker)
	switch {
	case marker == "":
		add("expect.port_refusal.marker is empty. The graded assertion would then be 'the port refused " +
			"for SOME reason', which any broken port satisfies -- an unknown account, a malformed " +
			"date. Default-deny")
	case len(marker) < MinPortRefusalMarker:
		add("expect.port_refusal.marker %q is %d characters and the minimum is %d. A short marker is "+
			"contained in almost any refusal text, so the cell would be a comparison that cannot fail",
			marker, len(marker), MinPortRefusalMarker)
	case v.Expect.PortRefusal.ObservedText == "":
		add("expect.port_refusal.observed_text is empty. The marker is a FRAGMENT and this is the whole " +
			"sentence it was cut from; without it a later reader cannot tell a re-worded refusal from " +
			"a port that stopped refusing")
	case !strings.Contains(v.Expect.PortRefusal.ObservedText, marker):
		add("expect.port_refusal.marker %q does not occur in expect.port_refusal.observed_text. The two "+
			"fields transcribe one refusal and a marker that is not in it was never cut from it",
			marker)
	}

	// --- the oracle's side --------------------------------------------------
	o := v.OracleAccepted
	if o.HTTPStatus < 200 || o.HTTPStatus > 299 {
		add("oracle_accepted.http_status %d is not a 2xx. This class exists for ORACLE-ACCEPTS / "+
			"PORT-REFUSES; an oracle that refused is class oracle-refusal, and a divergence recording "+
			"a refusal on the oracle side records the opposite of what was observed", o.HTTPStatus)
	}
	if strings.TrimSpace(o.WhyUnrepresentable) == "" {
		add("oracle_accepted.why_unrepresentable is empty. Every divergence vector has to say, in its " +
			"own file, why the observation could not be a PARITY vector -- otherwise the class becomes " +
			"a place to put parity failures somebody could not make pass")
	}
	if strings.TrimSpace(o.Gate) == "" {
		add("oracle_accepted.gate is empty. A recorded divergence with no gate is an open disagreement " +
			"between this port and the reference oracle that nobody owns, sitting in a GREEN corpus")
	}
	if len(o.ObservedAmountTexts) == 0 {
		add("oracle_accepted.observed_amount_texts is empty. The oracle's own characters ARE the " +
			"observation; without them this vector asserts a divergence and records nothing about it")
	}

	// THE UNREPRESENTABILITY TEST, ON BYTES. See this function's doc comment.
	residue := false
	for i, t := range o.ObservedAmountTexts {
		if strings.TrimSpace(t) == "" {
			add("oracle_accepted.observed_amount_texts[%d] is blank", i)
			continue
		}
		if hasResidueBeyondMinorUnit(t, v.Request.Currency.MinorUnitDigits) {
			residue = true
		}
	}
	if len(o.ObservedAmountTexts) > 0 && !residue {
		add("no entry of oracle_accepted.observed_amount_texts carries a NON-ZERO digit beyond %d "+
			"decimal places, so every value here IS representable as an int64 count of minor units. "+
			"This observation belongs in the PARITY class, where the port is graded against it. A "+
			"divergence badge on a representable amount moves a vector out of the parity tally and "+
			"leaves the run green", v.Request.Currency.MinorUnitDigits)
	}

	// --- both sides anchored to their own capture, BYTE FOR BYTE ------------
	bad = append(bad, verbatimInCapture(opts.RepoRoot, v.Provenance.CaptureRef,
		"oracle_accepted.observed_amount_texts", "provenance.capture_ref", o.ObservedAmountTexts)...)
	reqTexts := make([]string, 0, len(v.Request.Legs))
	for _, l := range v.Request.Legs {
		reqTexts = append(reqTexts, l.AmountMajorText)
	}
	bad = append(bad, verbatimInCapture(opts.RepoRoot, v.Provenance.RequestCaptureRef,
		"request.legs[].amount_major_text", "provenance.request_capture_ref", reqTexts)...)

	return bad
}

// hasResidueBeyondMinorUnit reports whether text carries a NON-ZERO digit past
// the currency's minor unit.
//
// BYTES ONLY, AND THAT IS THE WHOLE DESIGN. It finds the decimal point by index,
// walks the fraction one byte at a time and compares each byte with '0'. There is
// no strconv, no arithmetic, no division and no exponent anywhere in it, so a
// monetary value the store cannot represent is examined without ever becoming a
// number -- which is the only way to hold an observation like `100.125000` while
// obeying "no floating point in any monetary code path, including intermediate
// calculation".
//
// It is the same predicate ledger.MinorUnitsFromDecimalText applies before it
// refuses, re-implemented here for the same reason RejectFloatTokens is
// re-implemented rather than imported: the RULE is shared, and this package must
// be able to state it about a vector without asking a port to convert anything.
func hasResidueBeyondMinorUnit(text string, minorDigits int) bool {
	if minorDigits < 0 {
		return false
	}
	dot := strings.IndexByte(text, '.')
	if dot < 0 {
		return false
	}
	frac := text[dot+1:]
	if len(frac) <= minorDigits {
		return false
	}
	for i := minorDigits; i < len(frac); i++ {
		if frac[i] < '0' || frac[i] > '9' {
			// A non-digit past the minor unit is a malformed transcription, not
			// a residue. Say nothing here; the caller's blank/verbatim rules and
			// the capture byte check are what catch it.
			return false
		}
		if frac[i] != '0' {
			return true
		}
	}
	return false
}

// verbatimInCapture requires every text to occur BYTE FOR BYTE inside the
// artefact ref names, ON A TOKEN BOUNDARY.
//
// IT IS BYTE MATCHING AND NOTHING ELSE. Not "equal after parsing", not "equal
// after normalising", not "equal as numbers" -- any of which would put the
// observed amount through a numeric type on the way to being checked, and the
// value in question is one no numeric type in this program can hold. The claim
// being checked is exactly "these are the oracle's own characters", and the only
// honest test of that claim is to look for those characters.
//
// WHY IT IS NO LONGER A BARE bytes.Contains [T397, closing T387's F-T387-2].
// bytes.Contains accepts a PREFIX: "100.12" is contained in a capture holding
// "100.125", so a vector could cite a SHORTER number than the artefact carries
// and the verbatim check would say nothing. T387 drove that (attack A17) and
// found the class SELF-CORRECTING -- the port converts the representable
// "100.12" happily, posts, and the divergence comparator then FAILs the vector
// with `divergence.port_outcome: want "REFUSED", got "ACCEPTED"`, exit 1 -- which
// is why it was filed MINOR rather than as a fail-open. It is closed anyway, and
// the downstream self-correction is KEPT and asserted as a control
// (TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed), because a check
// that is only saved by a later check is one refactor away from being saved by
// nothing (P-45).
//
// THE FIX IS NOT A NUMERIC COMPARISON, AND THAT IS DELIBERATE. The obvious
// "proper" repair -- parse both sides and compare them as numbers -- is forbidden
// here by the first CLAUDE.md non-negotiable and by the whole premise of this
// class: no int64 holds 100.125, no float may touch it, and a parse would be the
// defect this file exists to prevent wearing the costume of a fix. So the
// boundary is decided by CLASSIFYING THE NEIGHBOURING BYTE, which needs no
// arithmetic: the match must not have a digit, a decimal point or a sign glued to
// its left, nor a digit, a decimal point or an exponent marker glued to its
// right. See tokenBoundedIndex.
func verbatimInCapture(repoRoot, ref, field, refField string, texts []string) []string {
	var bad []string
	if len(texts) == 0 {
		return nil
	}
	if strings.TrimSpace(ref) == "" {
		return []string{fmt.Sprintf(
			"%s is non-empty and %s names no artefact, so nothing can check that these are the "+
				"oracle's own characters rather than a transcription", field, refField)}
	}
	raw, err := os.ReadFile(filepath.Join(repoRoot, ref))
	if err != nil {
		return []string{fmt.Sprintf(
			"%s names %q and it cannot be read (%v), so the verbatim check on %s could not run. "+
				"ABSENT REFUSES: a check that did not run is not a check that passed",
			refField, ref, err, field)}
	}
	for i, t := range texts {
		if strings.TrimSpace(t) == "" {
			continue
		}
		if !bytes.Contains(raw, []byte(t)) {
			bad = append(bad, fmt.Sprintf(
				"%s[%d] is %q and those bytes DO NOT OCCUR in %s (%s). The field claims to hold the "+
					"characters the oracle emitted; if they are not in the artefact this vector cites, "+
					"they came from somewhere else",
				field, i, t, refField, ref))
			continue
		}
		// PRESENT, BUT PRESENT AS PART OF SOMETHING ELSE. Reported separately
		// from "not there at all" because the two are different mistakes: one is
		// a transcription from nowhere, the other is a TRUNCATION of the
		// artefact's own number, and a reader has to be able to tell them apart.
		if tokenBoundedIndex(raw, []byte(t)) < 0 {
			bad = append(bad, fmt.Sprintf(
				"%s[%d] is %q and those bytes occur in %s (%s) ONLY GLUED TO A LONGER NUMBER -- every "+
					"occurrence has a digit, a decimal point or a sign immediately beside it, so %q is "+
					"a PREFIX or a TAIL of an amount the artefact carries and NOT an amount the "+
					"artefact carries. A bare substring match would accept \"100.12\" against a "+
					"capture holding \"100.125\", which is a DIFFERENT VALUE cited as if it were the "+
					"oracle's own characters. The match must land on a token boundary "+
					"[T397, closing T387 F-T387-2]",
				field, i, t, refField, ref, t))
		}
	}
	return bad
}

// tokenBoundedIndex returns the offset of the first occurrence of needle in raw
// that is NOT glued to a neighbouring numeric byte, or -1 if every occurrence is.
//
// NO NUMBER IS FORMED ANYWHERE IN HERE. It does not parse needle, it does not
// parse raw, it does not compare magnitudes and it does not know what value
// either side denotes. It walks byte offsets and asks one question of the single
// byte on each side of a candidate match: "could this byte belong to the same
// numeric token?" That is a character-class test -- the same discipline
// hasResidueBeyondMinorUnit uses to find a residue without ever holding the
// amount as a number -- and it is the only kind of test this class may apply to a
// value no numeric type in this program can represent.
//
// ANY bounded occurrence is enough. A capture legitimately carries the same
// characters more than once -- both legs of a balanced entry do, and that is
// exactly the artefact this rule guards -- and one honest occurrence is the whole
// of the claim being made.
func tokenBoundedIndex(raw, needle []byte) int {
	if len(needle) == 0 {
		return -1
	}
	for off := 0; off+len(needle) <= len(raw); {
		rel := bytes.Index(raw[off:], needle)
		if rel < 0 {
			return -1
		}
		i := off + rel
		end := i + len(needle)
		leftOK := i == 0 || !numericLeftNeighbour(raw[i-1])
		rightOK := end == len(raw) || !numericRightNeighbour(raw[end])
		if leftOK && rightOK {
			return i
		}
		off = i + 1
	}
	return -1
}

// numericLeftNeighbour reports whether b, sitting immediately BEFORE a match,
// means the match is only the tail of a longer number.
//
// A digit or a decimal point continues the token ("00.125" inside "100.125"). A
// sign does not continue the digits but it changes the VALUE, so "100.125" cited
// against a capture that holds only "-100.125" is not the artefact's amount
// either, and it refuses. No arithmetic is performed to reach that conclusion --
// the sign is simply not accepted as a boundary.
func numericLeftNeighbour(b byte) bool {
	return (b >= '0' && b <= '9') || b == '.' || b == '-' || b == '+'
}

// numericRightNeighbour reports whether b, sitting immediately AFTER a match,
// means the match is only a prefix of a longer number.
//
// A digit or a decimal point continues the token -- this is the byte that makes
// "100.12" refuse against "100.125", which is T387's F-T387-2. 'e'/'E' is
// included because a JSON number may be written in exponent form and "100.12"
// against "100.12e3" is likewise not the artefact's amount; recognising the
// marker is a character test and forms no exponent.
func numericRightNeighbour(b byte) bool {
	return (b >= '0' && b <= '9') || b == '.' || b == 'e' || b == 'E'
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
