package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/ledger"
)

// EntryPoster is what a ledger implementation must be able to do for this
// harness to grade it.
//
// WHAT IT IS AND IS NOT. It is NOT "post a journal entry to a database" — the
// posting engine is slice A1 and does not exist. It is the value computation
// DEC-2 §4.3 and §4.4 actually specify and that this program can actually check
// against captured oracle bytes:
//
//	given the oracle's own major-unit wire CHARACTERS for each leg, the chart
//	rows the legs point at, and the entry's currency, produce the entry in
//	int64 minor units — or refuse it the way the oracle refuses it.
//
// Everything gradeable here follows from that: the conversion boundary (§4.3
// consequence 1 and 2), the double-entry sum (I-1), the split sum (I-2), and the
// two manual-entry refusals the oracle was observed to return.
//
// WHY THE INPUT CARRIES THE ORACLE'S TEXT AND THE OUTPUT CARRIES INTEGERS. That
// asymmetry is the whole non-circularity argument. If the vector supplied the
// integers and the implementation returned them, the comparator would be
// grading the vector against itself — the circularity the first store's
// registry.go forbids in as many words. The vector supplies characters; the
// implementation supplies integers; a port that routes MNT through a float64, or
// truncates the sixth decimal, or reads "270450.58" as 270450 produces a
// different integer and the comparator reports a money kill.
type EntryPoster interface {
	// PostEntry converts and validates one journal entry.
	//
	// A refusal is returned as (*Refusal, nil) rather than as an error: an
	// oracle-faithful refusal is a RESULT this harness grades cell by cell
	// (status, code, message), not a failure of the call. A returned error means
	// the implementation could not answer at all, which is a HARNESS-ERROR
	// outcome and never a pass.
	PostEntry(req Request) (PostedEntry, *Refusal, error)
}

// PostedEntry is an implementation's answer: the entry in integer minor units.
//
// NO BALANCE FIELD EXISTS ON THIS TYPE, AND THAT IS A DECISION, NOT AN
// OVERSIGHT. GATE G-12 is open on exactly this. A2-29 MEASURED
// acc_gl_journal_entry.{office,organization}_running_balance to be a SECOND
// SOURCE OF TRUTH rather than a cache — made to disagree with the derived sum by
// MNT 2,000,000.00 on the live oracle, surviving four organisation-wide
// recomputes, propagating into a freshly computed row because the recompute
// seeds from its own prior output, and served at the contract boundary flagged
// runningBalanceComputed: true. The driver's recommendation is (a) for behaviour:
// DERIVE, NEVER READ THOSE COLUMNS BACK. This type has nowhere to put one, so a
// port cannot satisfy this harness by reading a stored balance, and no vector in
// this schema can grade one.
type PostedEntry struct {
	TransactionID string

	// RequestedAmountMinor is the caller's requested transaction amount,
	// converted by the implementation. HasRequestedAmount says whether the
	// request carried one at all — a zero amount and an absent amount are
	// different facts and must not share an encoding (P-46: absent != null !=
	// empty).
	RequestedAmountMinor ledger.MinorUnits
	HasRequestedAmount   bool

	// Legs are in the order the vector supplied them. Order is graded: the
	// oracle's read-back order is stable by entry id and a port that reorders
	// legs is a port whose output cannot be diffed against the oracle's.
	Legs []PostedLeg

	TotalDebitsMinor  ledger.MinorUnits
	TotalCreditsMinor ledger.MinorUnits
}

// PostedLeg is one leg as the implementation computed it.
type PostedLeg struct {
	AccountID   int64
	AccountCode string
	Side        EntrySide
	AmountMinor ledger.MinorUnits
}

// ---------------------------------------------------------------------------
// The registry — DEC-2 precondition P-10
// ---------------------------------------------------------------------------
//
// P-10, in DEC-2's own words: "A mechanism that actually RUNS a named wrong
// implementation and shows it going red — either a ledger implementation
// registered under a name and selected with the binary's -impl flag, or a
// mutation harness. graded_against is a DECLARATIVE record and does not execute
// anything … Without this, the bottom-left cell [of §5.2 requirement 7's matrix]
// is satisfiable by writing a JSON row, which is P-22 in the one place §5.2 was
// written to close it."
//
// So: every name a vector's graded_against cites must be REGISTERED here,
// admit.go refuses one that is not, and `-ledger-impl <name>` runs it. A JSON
// row naming a wrong implementation nobody can execute is now an admissibility
// failure rather than an unfalsifiable claim.

var (
	implMu sync.RWMutex
	impls  = map[string]EntryPoster{}
	wrong  = map[string]string{}
)

// Register makes an EntryPoster available under name. Registering a name twice
// panics: two implementations answering to one name would make the report's
// "implementation" line a lie.
func Register(name string, p EntryPoster) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("ledger conformance: implementation %q registered twice", name))
	}
	impls[name] = p
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name, with
// the defect it embodies stated.
//
// It is a separate call from Register so that the report can say which
// implementations are known-wrong, and so that the default selection (below)
// can never pick one. A harness that could silently grade against a wrong
// implementation and report PASS would be worse than no harness.
func RegisterWrong(name, defect string, p EntryPoster) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, p)
}

// Lookup returns the named implementation.
func Lookup(name string) (EntryPoster, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	p, ok := impls[name]
	return p, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation, and
// the defect it embodies.
func IsRegisteredWrong(name string) (string, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	d, ok := wrong[name]
	return d, ok
}

// RegisteredNames lists every registered implementation, wrong ones included.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// CorrectImplementationNames lists the registered implementations that are NOT
// declared wrong. The default selection uses this list, so `-ledger-impl` must
// be given explicitly to grade against a wrong one.
func CorrectImplementationNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		if _, bad := wrong[n]; !bad {
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// ---------------------------------------------------------------------------
// THE TWO DATE REFUSALS OF validateBusinessRulesForJournalEntries [T295]
// ---------------------------------------------------------------------------
//
// The globalisation codes and message texts below are the ORACLE'S OWN WIRE
// BYTES, transcribed from the captured response bodies in
// .softhouse/capture/t287-closure-refusals/out/ (A1-02 and A2-01 respectively,
// errors[0].userMessageGlobalisationCode and errors[0].defaultUserMessage, which
// are byte-identical to developerMessage on both errors).
//
// THEY ARE NAMED CONSTANTS RATHER THAN INLINE LITERALS FOR ONE REASON: admit.go
// keys an ADMISSIBILITY rule on them — a vector expecting the future-date
// refusal must carry the business date, one expecting the closure refusal must
// carry the closing date, and the RELATION each asserts must be the one the
// source says produces that refusal. Two files agreeing on a string only because
// somebody typed it twice is how the two drift apart.
const (
	codeFutureDate = "error.msg.glJournalEntry.invalid.future.date"
	msgFutureDate  = "The journal entry cannot be made for a future date"

	codeAccountingClosed = "error.msg.glJournalEntry.invalid.accounting.closed"
	msgAccountingClosed  = "Journal entry cannot be made prior to last account closing date for the branch"
)

// isoBefore and isoAfter order two STRICT `yyyy-MM-dd` calendar dates.
//
// PLAIN STRING COMPARISON IS THE CORRECT COMPARISON HERE, and it is worth one
// paragraph rather than a reader's doubt. For zero-padded, fixed-width ISO-8601
// dates, lexicographic order IS chronological order: the fields run
// most-significant first and each has a fixed digit count, so a byte-wise
// comparison decides the year, then the month, then the day, in that order.
// admit.go enforces the strictness with a time.Parse round-trip
// (`2006-01-02` -> Format -> must equal the input), so a two-digit year or an
// unpadded month cannot reach this function from the store.
//
// WHY NOT time.Parse HERE. Because parsing returns an error, and an error on
// this path would have to become either a harness error or a silent false —
// one turns a comparison into a crash and the other turns it into a skipped
// rule. The format is a STORE-ADMISSIBILITY concern and it is enforced where
// admissibility is enforced.
//
// NO OFFSET, NO ZONE, NO TIMESTAMP. CLAUDE.md's non-negotiable is two zones and
// no DST, and the way that rule gets broken is a comparison that quietly needs
// an offset. These are calendar dates and nothing here has a time of day.
func isoBefore(a, b string) bool { return a < b }
func isoAfter(a, b string) bool  { return a > b }

// ---------------------------------------------------------------------------
// The reference implementation
// ---------------------------------------------------------------------------

// GoPoster is the Go port's answer, and every line of arithmetic in it comes
// from nexus/internal/apps/ledger — the ported package — not from this harness.
//
// THAT SEPARATION IS THE POINT AND IT IS NOT DECORATIVE. If this file did the
// conversion itself, the harness would be grading a copy of the port that lives
// inside the harness, which is exactly what impl_hook.go's doc comment in the
// first harness refuses to do ("a stub generator living here … would have been a
// schedule generator inside the harness that grades schedule generators"). The
// three calls below — MinorUnitsFromDecimalText, DoubleEntryBalances,
// SplitsSumToWhole — are the port's own functions.
type GoPoster struct{}

// NewGoPoster returns the port-backed implementation.
func NewGoPoster() EntryPoster { return GoPoster{} }

// PostEntry implements EntryPoster against the ported ledger package.
func (GoPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	chart := map[int64]Account{}
	for _, a := range req.Accounts {
		chart[a.ID] = a
	}

	// STEP 1 — CONVERT. The oracle's characters become int64 minor units, by
	// the port's own exact string arithmetic. A residue beyond the currency's
	// minor unit is REFUSED here, never truncated and never rounded (DEC-2 §4.3
	// consequence 2, predicate G-08).
	out := PostedEntry{TransactionID: req.TransactionID}
	if req.TransactionAmountMajorText != "" {
		amt, cerr := ledger.MinorUnitsFromDecimalText(
			req.TransactionAmountMajorText, req.Currency.MinorUnitDigits)
		if cerr != nil {
			return PostedEntry{}, nil, fmt.Errorf("transaction_amount_major_text: %w", cerr)
		}
		out.RequestedAmountMinor = amt
		out.HasRequestedAmount = true
	}
	legs := make([]ledger.PostingLeg, 0, len(req.Legs))
	for i, l := range req.Legs {
		acct, ok := chart[l.AccountID]
		if !ok {
			return PostedEntry{}, nil, fmt.Errorf(
				"leg %d points at GL account %d, which the vector's chart does not carry", i, l.AccountID)
		}
		amt, cerr := ledger.MinorUnitsFromDecimalText(l.AmountMajorText, req.Currency.MinorUnitDigits)
		if cerr != nil {
			return PostedEntry{}, nil, fmt.Errorf("leg %d: %w", i, cerr)
		}
		out.Legs = append(out.Legs, PostedLeg{
			AccountID:   l.AccountID,
			AccountCode: acct.Code,
			Side:        l.Side,
			AmountMinor: amt,
		})
		var side ledger.EntrySide
		switch l.Side {
		case SideDebit:
			side = ledger.EntryDebit
			out.TotalDebitsMinor += amt
		case SideCredit:
			side = ledger.EntryCredit
			out.TotalCreditsMinor += amt
		default:
			return PostedEntry{}, nil, fmt.Errorf("leg %d: unknown entry side %q", i, l.Side)
		}
		legs = append(legs, ledger.PostingLeg{Side: side, Amount: amt})
	}

	// STEP 1.5 — THE OPENING-BALANCE RULE: opening balances may not be defined
	// once journal entries have been posted. [T294]
	//
	// OBSERVED, not inferred. OB-01 POSTed
	// /journalentries?command=defineOpeningBalance on tenant `gerege`, where
	// financial-activity type 300 maps to GL 15 and 26 non-contra transaction
	// ids exist, and the oracle returned HTTP 403 with
	// error.msg.journalentry.defining.openingbalance.not.allowed and the
	// message "Defining Opening balances not allowed after journal entries
	// posted" — the source string at :814 and the wire string, character for
	// character.
	//
	// THE PREDICATE IS `NON-EMPTY`, NOT `NON-ZERO COUNT`, because that is what
	// :812 computes: `if (!CollectionUtils.isEmpty(transactionIds))`. The
	// vector carries the oracle's own list (request.posted_non_contra_
	// transaction_ids, transcribed from errors[0].args), so this port reads a
	// length rather than a boolean somebody derived for it.
	//
	// ⚠ THE SENTENCE ABOVE OVERCLAIMS, AND IS CORRECTED HERE RATHER THAN
	// DELETED, because it was quoted in T294's handoff §6 and in the vector's
	// own `_note` as the reason this vector is non-vacuous, and a reader who
	// meets it there must be able to find the correction. [T296 F-T296-2,
	// discharged by T305.] T296 mutated THIS FUNCTION in four arms and
	// re-graded the whole ledger corpus:
	//
	//	arm E  the rule moved BELOW the balance check   -> DIES
	//	arm A  match on req.Command alone, id list never read  -> SURVIVES
	//	arm B  match on the id list alone, command never read  -> SURVIVES
	//
	// So THIS PORT READS A LENGTH; NOTHING IN THIS STORE REQUIRES IT TO. Arm E
	// is the part of T294's claim that measured true — the ORDERING of this
	// rule against the balance rule really is graded, and it is the only
	// observed refusal precedence in the corpus. But the id list is INERT FOR
	// GRADING: a port that ignores it scores identically.
	//
	// WHAT THAT LET THROUGH — AND IT IS NOW CLOSED. Arm A refuses EVERY
	// defineOpeningBalance, including on an EMPTY ledger where the oracle
	// ACCEPTS (:812's CollectionUtils.isEmpty fall-through into the writes at
	// :742/:745). That is the headerRefusingPoster class — the reasonable thing
	// to do, which the oracle does not do. Only an ACCEPTING-side capture could
	// kill it, because every refusal capture in this corpus agrees with it.
	// T305 TOOK ONE: HTTP 200 and six journal entries on an empty ledger,
	// promoted as LDG-05-openingbalance-accepted-empty-ledger, and arm A is
	// registered here as `ledger-wrong-openingbalance-always-refusing` and dies
	// to it on leg_count while passing every other ledger vector.
	//
	// ⚠ AND THE SENTENCE THIS COMMENT OPENS WITH IS WRONG IN THE SAME WAY THE
	// ORACLE'S OWN MESSAGE IS. "Opening balances may not be defined once journal
	// entries have been posted" is :814's text and this corpus repeated it.
	// MEASURED [T305]: findNonContraTransactionIds EXCLUDES every transaction
	// that touches the contra account, and every entry an opening balance writes
	// touches it (:796) — so OPENING BALANCES DO NOT BLOCK EACH OTHER. Re-sending
	// byte-identical opening-balance bytes returned HTTP 200 again, having
	// REVERSED the previous opening balance first (:726-735). Only after a PLAIN
	// manual entry existed did the same bytes draw 403, with errors[0].args
	// carrying exactly that one transaction id. THE RULE IS "AFTER A NON-CONTRA
	// JOURNAL ENTRY".
	//
	// THE PREDICATE BELOW IS LEFT EXACTLY AS IT IS, AND IT WAS RIGHT ALL ALONG —
	// it reads `posted_non_contra_transaction_ids`, whose name carries the
	// distinction the prose lost. This is P-11 in one function: the code can be
	// RIGHT and its stated reason WRONG, and the reason is what the next
	// contributor checks.
	//
	// ITS POSITION IN THIS FUNCTION IS OBSERVED AND NOT CHOSEN, and that is the
	// one thing about it worth reading twice. OB-01's request body is UNBALANCED
	// BY EXACTLY ONE MINOR UNIT (debit 250000.25, credit 250000.24) — so the
	// oracle had two independent grounds to refuse it, and it returned THIS one.
	// Source agrees and says why: :717 runs BEFORE :724, and the balance check
	// is inside :724 (validateBusinessRulesForJournalEntries → :651
	// checkDebitAndCreditAmounts). A port that checks the balance first returns
	// error.msg.glJournalEntry.invalid.mismatch.debits.credits for this request
	// and diverges from the oracle on two of the three refusal cells. Unlike the
	// STEP 2 / STEP 3 precedence below, this ordering is NOT [UNVERIFIED]: one
	// captured request violates both rules and the oracle answered.
	if req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0 {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       "error.msg.journalentry.defining.openingbalance.not.allowed",
			Message:    "Defining Opening balances not allowed after journal entries posted",
		}, nil
	}

	// STEP 1.6 — THE FUTURE-DATE RULE. [T295]
	//
	// :629 `if (DateUtils.isDateInTheFuture(transactionDate))` ->
	// isAfterBusinessDate -> `isAfter(transactionDate, getBusinessLocalDate())`
	// [DateUtils.java:258-264]. STRICT: an entry dated ON the business date is
	// NOT future-dated and this rule does not fire on it.
	//
	// OBSERVED: A1-02 posted transactionDate 2026-08-24 against business date
	// 2026-08-23 and the oracle returned HTTP 403
	// error.msg.glJournalEntry.invalid.future.date. Promoted as LDG-REFUSE-05.
	//
	// THE BUSINESS DATE IS AN INPUT AND THIS FUNCTION READS NO CLOCK. An empty
	// BusinessDate means the vector asserts nothing about this rule and the rule
	// is SKIPPED — never "default to today", which would make the harness's
	// answer depend on the morning it ran, which is the exact defect T289 found
	// in T287's captures.
	if req.BusinessDate != "" && req.TransactionDate != "" &&
		isoAfter(req.TransactionDate, req.BusinessDate) {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       codeFutureDate,
			Message:    msgFutureDate,
		}, nil
	}

	// STEP 1.7 — THE ACCOUNTING-CLOSURE RULE, AND ITS BOUNDARY IS INCLUSIVE.
	// [T295]
	//
	// :634-639:
	//	final GLClosure latestGLClosure = getLatestGLClosureByBranch(officeId);
	//	if (latestGLClosure != null) {
	//	    if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
	//	        throw ... ACCOUNTING_CLOSED
	//
	// `DateUtils.isBefore(first, second)` is `first.isBefore(second)` for two
	// non-null LocalDates [DateUtils.java:296-298], so the negation refuses
	// whenever `closingDate >= transactionDate`, i.e. `transactionDate <=
	// closingDate`. AN ENTRY DATED **ON** THE CLOSING DATE IS REFUSED.
	//
	// THE WIRE MESSAGE DISAGREES WITH THE CODE AND THE CODE IS WHAT RUNS:
	// "Journal entry cannot be made PRIOR TO last account closing date for the
	// branch". A port written from that sentence gets `transactionDate <
	// closingDate` and ACCEPTS an entry dated on the closing date — which is
	// exactly the day a period-end adjustment carries. That port is registered
	// as `ledger-wrong-closure-boundary-exclusive` and LDG-REFUSE-04 kills it.
	//
	// OBSERVED: A2-01 posted transactionDate 2026-01-31 while the office's
	// latest GLClosure closed 2026-01-31 — the two EQUAL — and the oracle
	// returned HTTP 403 error.msg.glJournalEntry.invalid.accounting.closed. The
	// equal case is the only one that separates the two readings, and it is the
	// one that was captured.
	//
	// EMPTY LatestClosingDate IS THE ORACLE'S `latestGLClosure == null` BRANCH
	// (:635), not a missing input: the repository returns null when the office
	// has no closure, and this port then refuses nothing, exactly as :635 does.
	if req.LatestClosingDate != "" && req.TransactionDate != "" &&
		!isoBefore(req.LatestClosingDate, req.TransactionDate) {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       codeAccountingClosed,
			Message:    msgAccountingClosed,
		}, nil
	}

	// STEP 2 — THE MANUAL-ADJUSTMENT RULE, applied only to a MANUAL entry.
	//
	// OBSERVED, not inferred: A2-346 posted a debit leg at GL 18
	// (manual_journal_entries_allowed = false) and the oracle returned HTTP 403
	// with error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted.
	// The account attribute is DATA the vector transcribes (§4.5); the RULE is
	// what this port implements.
	//
	// THE ORDER OF THE TWO CHECKS IS OBSERVED, NOT CHOSEN. A2-346's request is
	// BALANCED, so it cannot separate the order on its own; but the oracle
	// returns the manual-adjustment error for it, and A2-344 — unbalanced, both
	// legs on manual-permitted accounts — returns the balance error. Neither
	// capture exercises a request that violates BOTH, so the precedence between
	// them is [UNVERIFIED] and no vector in this corpus asserts it. This code
	// checks manual-permission first only because that is the order the observed
	// pair is consistent with; a capture that violates both would settle it and
	// none exists.
	if req.ManualEntry {
		for i, l := range req.Legs {
			acct := chart[l.AccountID]
			if !acct.ManualEntriesAllowed {
				return PostedEntry{}, &Refusal{
					HTTPStatus: 403,
					Code:       "error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted",
					Message:    "Target account does not allow manual adjustments",
				}, nil
			}
			_ = i
		}
	}

	// STEP 3 — I-1, DOUBLE ENTRY, by the port's own function.
	//
	// NOTE WHAT IS **NOT** HERE: no HEADER-account refusal. A2-345 posted to
	// GL 1, a HEADER (summary) account, and the oracle returned HTTP 200. DEC-2
	// brief item (5): "A port that REFUSES summary-account postings therefore
	// DIVERGES FROM THE ORACLE. Do not 'improve on' the oracle." The temptation
	// to add three lines here is exactly the divergence the vector
	// LDG-04-header-account-accepted exists to catch.
	if err := ledger.DoubleEntryBalances(legs); err != nil {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       "error.msg.glJournalEntry.invalid.mismatch.debits.credits",
			Message:    "Sum of All Debits must equal the sum of all Credits for a Journal Entry",
		}, nil
	}

	// STEP 4 — AN ACCEPTED OPENING BALANCE POSTS TWO ENTRIES PER LEG, NOT ONE.
	// [T305, and it is OBSERVED — the first accepting-side observation this
	// program has ever taken.]
	//
	// saveAllDebitOrCreditOpeningBalanceEntries (:759-797) calls
	// helper.persistJournalEntry TWICE INSIDE THE PER-LEG LOOP: the leg's own
	// entry at :791, and its CONTRA entry on the financial-activity-300 account
	// with the opposite side at :796. defineOpeningBalance calls it twice, once
	// for the debits (:742) and once for the credits (:745).
	//
	// MEASURED, not read off the source: OB-ACCEPT-01 sent three legs — DEBIT
	// 250000.25 on GL 2, DEBIT 100000.37 on GL 3, CREDIT 350000.62 on GL 4 —
	// and the oracle wrote SIX journal entries on ONE transaction (the id is
	// server-assigned and differs on every re-run of the recipe; it is not a
	// graded cell and is not quoted here for that reason):
	//
	//	id 1  GL 2 T305-1000  DEBIT   250000.250000
	//	id 2  GL 1 T305-3000  CREDIT  250000.250000   <- contra, per leg
	//	id 3  GL 3 T305-1100  DEBIT   100000.370000
	//	id 4  GL 1 T305-3000  CREDIT  100000.370000   <- contra, per leg
	//	id 5  GL 4 T305-2000  CREDIT  350000.620000
	//	id 6  GL 1 T305-3000  DEBIT   350000.620000   <- contra, per leg
	//
	// [.softhouse/capture/t305-openingbalance-accepting-side/throwaway/out/
	//  OB-ACCEPT-01-readback-db.json, sha256 1911e2cf…0737db2]
	//
	// THE CONTRA IS PER LEG AND NOT SUMMED, and that is the whole reason the
	// capture carried THREE legs of DIFFERENT amounts rather than a tidy
	// one-debit-one-credit pair: a two-leg body cannot tell a per-leg contra
	// from a single netted one, because with one debit and one credit the two
	// answers are identical.
	//
	// WHY DEBITS BEFORE CREDITS, AND WHAT IS [UNVERIFIED] ABOUT IT. The oracle
	// runs the debit array (:742) before the credit array (:745), so this port
	// emits every debit leg with its contra and then every credit leg with its
	// contra, irrespective of the order the vector listed them in. OB-ACCEPT-01's
	// request happened to list its legs debits-first, so THE CAPTURE CANNOT
	// SEPARATE "source order" from "request order" — it is consistent with both.
	// The source can and does, so this follows the source and says so rather than
	// claiming the capture settled it.
	//
	// NOTHING ELSE IN THIS CORPUS REACHES THIS BRANCH: it runs only on
	// `command == defineOpeningBalance`, and the only other vector carrying that
	// command is LDG-REFUSE-03, which returns at STEP 1.5 above.
	if req.Command == "defineOpeningBalance" {
		contra, ok := chart[req.ContraGLAccountID]
		if !ok {
			// A HARNESS ERROR, never a refusal. The oracle resolves the contra
			// account at :708 BEFORE any of the rules above, so a vector that
			// reaches here without carrying the contra account in its chart has
			// described an observation nobody could have taken — and an error is
			// the outcome that can never be mistaken for a pass.
			return PostedEntry{}, nil, fmt.Errorf(
				"command is defineOpeningBalance and request.contra_gl_account_id %d is not in request.accounts: "+
					"the contra account is resolved at :708 and written on every leg at :796, so it cannot be absent",
				req.ContraGLAccountID)
		}
		expanded := make([]PostedLeg, 0, len(out.Legs)*2)
		var debits, credits ledger.MinorUnits
		for _, side := range []EntrySide{SideDebit, SideCredit} {
			for _, l := range out.Legs {
				if l.Side != side {
					continue
				}
				expanded = append(expanded, l)
				expanded = append(expanded, PostedLeg{
					AccountID:   contra.ID,
					AccountCode: contra.Code,
					Side:        oppositeSide(l.Side),
					AmountMinor: l.AmountMinor,
				})
				// Each pair is one debit and one credit of the same amount,
				// whichever way round the leg itself points, so both totals grow
				// by the leg amount. Integer minor units throughout; no
				// intermediate is anything but an int64.
				debits += l.AmountMinor
				credits += l.AmountMinor
			}
		}
		out.Legs = expanded
		out.TotalDebitsMinor = debits
		out.TotalCreditsMinor = credits
	}

	return out, nil, nil
}

// oppositeSide is the contra side :796 writes (getContraType, :799-805).
func oppositeSide(s EntrySide) EntrySide {
	if s == SideDebit {
		return SideCredit
	}
	return SideDebit
}

// ---------------------------------------------------------------------------
// The named WRONG implementations — DEC-2 §5.2 requirement 7, bottom-left cell
// ---------------------------------------------------------------------------
//
// Each of these is a defect a real port could plausibly ship, and each is
// EXECUTABLE: `-ledger-impl <name>` runs it against the pristine corpus and the
// run goes red. That is the difference between a graded_against row that is
// evidence and one that is a sentence.

// truncatingPoster drops everything after the decimal point.
//
// THE DEFECT: `int64(strings.Split(text, ".")[0])`, or an integer cast of a
// decoded float, or a DECIMAL(19,6) column read with rs.getLong. All three are
// real and the last one is not hypothetical — A2-29 MEASURED the oracle's own
// GLAccountReadPlatformServiceImpl.java:75,104 reading a numeric(19,6) with
// rs.getLong, truncating MNT 46,000.00 to 4600000 and serving it.
//
// WHY IT IS THE RIGHT WRONG IMPLEMENTATION FOR THIS CORPUS. Before A2-26 every
// ledger amount in the A2 captures was a WHOLE TUGRIK, so this defect was
// BYTE-INDISTINGUISHABLE from a correct port on every capture ever taken
// (DEC-2 §5.0.1). It is killable now, and only now, because the corpus finally
// carries legs at 270450.58, 22049.42, 100000.25, 25000.37, 125000.62,
// 889549.42, 20298.82 and 90151.76.
type truncatingPoster struct{}

func (truncatingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	base, ref, err := GoPoster{}.PostEntry(req)
	if err != nil || ref != nil {
		return base, ref, err
	}
	scale := ledger.MinorUnits(1)
	for i := 0; i < req.Currency.MinorUnitDigits; i++ {
		scale *= 10
	}
	out := PostedEntry{
		TransactionID:        base.TransactionID,
		RequestedAmountMinor: base.RequestedAmountMinor,
		HasRequestedAmount:   base.HasRequestedAmount,
	}
	for _, l := range base.Legs {
		l.AmountMinor = (l.AmountMinor / scale) * scale
		out.Legs = append(out.Legs, l)
		switch l.Side {
		case SideDebit:
			out.TotalDebitsMinor += l.AmountMinor
		case SideCredit:
			out.TotalCreditsMinor += l.AmountMinor
		}
	}
	return out, nil, nil
}

// headerRefusingPoster refuses a posting to a HEADER (summary) account.
//
// THE DEFECT: it is the reasonable thing to do and the oracle does not do it.
// A2-345 posted a debit leg at GL 1 — account_usage = 2, HEADER — and the oracle
// returned HTTP 200 and created the entry [OBSERVED]. A port that "improves on"
// the oracle here diverges from it, and a shadow-parity run would show the two
// systems disagreeing on a transaction the reference accepted.
type headerRefusingPoster struct{}

func (headerRefusingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	for _, l := range req.Legs {
		for _, a := range req.Accounts {
			if a.ID == l.AccountID && a.Usage == "HEADER" {
				return PostedEntry{}, &Refusal{
					HTTPStatus: 403,
					Code:       "error.msg.glJournalEntry.invalid.header.account",
					Message:    "Journal entries may not be posted to a summary account",
				}, nil
			}
		}
	}
	return GoPoster{}.PostEntry(req)
}

// manualPermissionIgnoringPoster never checks manual_journal_entries_allowed.
//
// THE DEFECT: the flag is a column a port can adopt from Fineract's schema and
// then never read. A2-346 is the capture that kills it.
type manualPermissionIgnoringPoster struct{}

func (manualPermissionIgnoringPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	r := req
	r.ManualEntry = false
	return GoPoster{}.PostEntry(r)
}

// openingBalanceUncheckedPoster defines opening balances without ever asking
// whether journal entries have already been posted.
//
// THE DEFECT: `defineOpeningBalance` looks like a seeding operation, and a port
// written from the endpoint's NAME implements seeding — resolve the contra
// account, reverse the previous contra entries, write the new ones. The guard
// that makes it refusable is a single line eleven lines above the first write
// (:717 `validateJournalEntriesArePostedBefore(contraId)`), it consults a
// repository query rather than the request, and NOTHING in the request body
// hints that it exists. It is exactly the shape of the flag
// manualPermissionIgnoringPoster drops: a rule that lives in the tenant, not in
// the payload, so a port can be complete against the API documentation and still
// have it missing.
//
// WHY IT IS NOT A DUPLICATE OF ANY EXISTING WRONG IMPLEMENTATION. It passes all
// four parity vectors and both pre-existing refusal vectors untouched — none of
// them is an opening-balance command — and it dies on LDG-REFUSE-03 alone. It is
// killed on refusal.code and refusal.message rather than on refusal.http_status,
// because OB-01's body was DELIBERATELY unbalanced (the write-fence: see the rig)
// so this implementation falls through to the balance rule and returns a
// DIFFERENT 403. That is the sharper kill, not the weaker one: a port can get the
// status right for the wrong reason, and the code is the cell that tells one 403
// from another.
type openingBalanceUncheckedPoster struct{}

func (openingBalanceUncheckedPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	r := req
	r.PostedNonContraTransactionIDs = nil
	return GoPoster{}.PostEntry(r)
}

// openingBalanceAlwaysRefusingPoster refuses EVERY defineOpeningBalance command
// — including on an empty ledger, where the reference oracle ACCEPTS.
//
// THIS IS T296'S ARM A, LIFTED OUT OF A REVIEW PROBE AND MADE EXECUTABLE. T296
// mutated GoPoster's STEP 1.5 predicate to `req.Command ==
// "defineOpeningBalance"` alone — never reading the posted-id list — and
// measured that it SURVIVED THE ENTIRE LEDGER CORPUS. Every refusal capture in
// this store AGREES with it, so no number of refusal vectors could ever kill it;
// only an ACCEPTING-side observation can, and until T305 took one there was
// none.
//
// THE DEFECT, AND IT IS THE MOST TEMPTING ONE ON THIS ENDPOINT. The guard at
// :717 consults a repository query, not the request body, so a port that has
// read the endpoint's documentation knows only that "opening balances are not
// allowed after journal entries have been posted" — the oracle's own message at
// :814 — and the safe-looking implementation of a rule you cannot evaluate is to
// refuse. It is `ledger-wrong-header-refusing` wearing different clothes: THE
// REASONABLE THING TO DO, WHICH THE ORACLE DOES NOT DO. Diverging from the
// oracle BY REFUSING is still diverging.
//
// AND THE MESSAGE IT COPIES IS ITSELF MISLEADING, WHICH IS WHY THE DEFECT IS SO
// EASY TO SHIP: T305 measured that opening balances do NOT block each other at
// all. Every entry an opening balance writes touches the contra account (:796),
// and findNonContraTransactionIds EXCLUDES contra transactions, so re-defining
// an opening balance REVERSES the previous one and posts a new one
// (OB-ACCEPT-02, HTTP 200 on byte-identical bytes). The rule is "after a
// NON-CONTRA journal entry", never "after any journal entry".
//
// KILLED BY: LDG-05-openingbalance-accepted-empty-ledger, on every cell of the
// entry it never produces. It passes every other ledger vector untouched,
// including LDG-REFUSE-03, whose refusal it reproduces exactly.
type openingBalanceAlwaysRefusingPoster struct{}

func (openingBalanceAlwaysRefusingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	if req.Command == "defineOpeningBalance" {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       "error.msg.journalentry.defining.openingbalance.not.allowed",
			Message:    "Defining Opening balances not allowed after journal entries posted",
		}, nil
	}
	return GoPoster{}.PostEntry(req)
}

// openingBalanceNoContraPoster accepts an opening balance and writes ONLY the
// legs the caller sent — no contra entry at all.
//
// THE DEFECT: the request body carries three legs and the endpoint is called
// "journalentries", so a port writes three journal entries. The contra entries
// are not in the payload, are not in the API documentation for this endpoint,
// and exist only because :796 writes one per leg against whatever account
// financial-activity type 300 happens to map to. A port that misses them
// produces a chart in which the opening balance's own equity side never appears
// — the trial balance is short by the whole opening position — while every leg
// the caller can see is byte-perfect.
//
// KILLED BY: LDG-05, on the leg count and on every cell of legs[1], legs[3] and
// legs[5]. It is the second half of the same capture: arm A gets the ACCEPT
// wrong, this one gets the ACCEPT'S CONTENT wrong.
type openingBalanceNoContraPoster struct{}

func (openingBalanceNoContraPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	// THE REFUSAL PATH IS LEFT INTACT ON PURPOSE. Blanking the command outright
	// would also skip STEP 1.5 and make this implementation die on
	// LDG-REFUSE-03 as well — which would make its kill indistinguishable from
	// `ledger-wrong-openingbalance-posted-entries-ignored`'s and turn two
	// registered defects into one. This one gets exactly ONE thing wrong.
	if req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0 {
		return GoPoster{}.PostEntry(req)
	}
	r := req
	r.Command = ""
	return GoPoster{}.PostEntry(r)
}

// futureDateIgnoringPoster never checks whether the entry is dated after the
// business date.
//
// THE DEFECT: `transactionDate` arrives in the request body and looks like the
// caller's business, so a port validates its FORMAT and posts it. The rule that
// makes a future date refusable is one line
// (:629 `if (DateUtils.isDateInTheFuture(transactionDate))`) that consults
// TENANT AMBIENT STATE — the business date — which appears nowhere in the
// payload and nowhere in the API documentation for this endpoint. It is the same
// shape as the flag manualPermissionIgnoringPoster drops and the query
// openingBalanceUncheckedPoster drops: a rule that lives outside the request.
//
// AND IT IS THE ONE A BACKDATING FEATURE INVITES. A port that supports
// backdated entries has already decided that `transactionDate` may differ from
// today; dropping the other half of that decision — that it may differ only
// DOWNWARD — is a single missing comparison, and it lets a caller post into a
// period that has not happened.
//
// HOW IT IS EXPRESSED: by clearing the input the rule reads, which is the
// established shape in this file (manualPermissionIgnoringPoster clears
// ManualEntry, openingBalanceUncheckedPoster clears the transaction-id list).
// The port then reaches STEP 1.6 with nothing to compare against and posts.
//
// WHY IT IS NOT A DUPLICATE: it passes all four parity vectors, both
// pre-T294 refusal vectors, LDG-REFUSE-03 and LDG-REFUSE-04 — LDG-REFUSE-04's
// transaction date is 2026-01-31 against a business date of 2026-08-23, so it is
// not future-dated and clearing the business date changes nothing there — and it
// dies on LDG-REFUSE-05 alone, on all three refusal cells, because A1-02's body
// is otherwise perfectly postable and this port posts it.
type futureDateIgnoringPoster struct{}

func (futureDateIgnoringPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	r := req
	r.BusinessDate = ""
	return GoPoster{}.PostEntry(r)
}

// closureBoundaryExclusivePoster reads the oracle's own error message and
// implements the boundary the message describes: STRICTLY `prior to`.
//
// THE DEFECT, AND IT IS THE MONEY-PATH FINDING OF THIS WHOLE ARM. The wire
// message is "Journal entry cannot be made PRIOR TO last account closing date
// for the branch". The code is
// `!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)`
// (:636), which refuses `transactionDate <= closingDate` — INCLUSIVE. The
// message and the code disagree about ONE DAY, and the day they disagree about
// is THE CLOSING DATE ITSELF, which is precisely the day a period-end adjustment
// carries. A port written from the message text FAILS OPEN there: it accepts a
// journal entry into a period the reference oracle had sealed, the two systems
// diverge on a transaction that a shadow-parity run would show one side
// accepting and the other refusing, and the divergence appears on month-end and
// not before.
//
// THIS IS NOT A HYPOTHETICAL READING OF THE MESSAGE. It is the reading the
// message's plain English gives, in a codebase where the message is the only
// documentation of the rule most porters will ever read.
//
// HOW IT IS EXPRESSED: the port's OWN predicate is the strict one, and where its
// predicate says "accept" it hands GoPoster a request with no closure at all, so
// GoPoster's inclusive comparison has nothing to fire on. The decision that
// differs is therefore this port's decision, made here, in one line.
//
// WHY IT IS NOT A DUPLICATE: it agrees with the reference implementation on
// every vector where the transaction date is strictly before the closing date —
// which is every pre-closure request a naive corpus would think to capture — and
// it dies on LDG-REFUSE-04 alone, the one capture taken ON the boundary.
type closureBoundaryExclusivePoster struct{}

func (closureBoundaryExclusivePoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	r := req
	if r.LatestClosingDate != "" && r.TransactionDate != "" &&
		!isoBefore(r.TransactionDate, r.LatestClosingDate) {
		// This port's rule says ACCEPT: the entry is not "prior to" the closing
		// date. Clearing the closure is how that decision reaches the shared
		// posting path.
		r.LatestClosingDate = ""
	}
	return GoPoster{}.PostEntry(r)
}

// nettingPoster sums every leg into one accumulator, treating a credit as a
// negative debit, and then reports totals from it.
//
// THE DEFECT: it makes I-1 pass by construction — debits "equal" credits because
// the port never computed two numbers to compare — and it reports both totals as
// the same netted figure. It is the shape DoubleEntryBalances' own doc comment
// warns about ("a negative debit is a credit wearing the wrong label"), turned
// into a whole implementation. It matches every per-leg cell and diverges on the
// two totals, which is precisely why Expect carries the totals separately.
type nettingPoster struct{}

func (nettingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	base, ref, err := GoPoster{}.PostEntry(req)
	if err != nil || ref != nil {
		return base, ref, err
	}
	var net ledger.MinorUnits
	for _, l := range base.Legs {
		switch l.Side {
		case SideDebit:
			net += l.AmountMinor
		case SideCredit:
			net -= l.AmountMinor
		}
	}
	base.TotalDebitsMinor = net
	base.TotalCreditsMinor = net
	return base, nil, nil
}

// codeIgnoringPoster resolves every account code to the empty string.
//
// THE DEFECT: a port that carries account IDs and never joins the chart. It is
// the STRUCTURAL counterpart of truncatingPoster and it exists so that
// requirement 7's structural half is killed by something, rather than being
// asserted.
type codeIgnoringPoster struct{}

func (codeIgnoringPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	base, ref, err := GoPoster{}.PostEntry(req)
	if err != nil || ref != nil {
		return base, ref, err
	}
	for i := range base.Legs {
		base.Legs[i].AccountCode = ""
	}
	return base, nil, nil
}

// splitDriftPoster keeps the entry internally balanced and moves ONE MINOR UNIT
// off the requested transaction total.
//
// THE DEFECT, AND WHY IT NEEDED ITS OWN IMPLEMENTATION: it is the only registered
// wrong implementation that PASSES I-1 AND FAILS I-2. Every leg still balances
// against every other leg — debits equal credits exactly — while the splits sum
// to one minor unit less than the caller asked for. Without it, I-2 would be a
// second green line that no implementation in this harness could turn red
// independently, which is P-22's "a control that cannot fail is worse than none"
// applied to an invariant rather than to a guard.
type splitDriftPoster struct{}

func (splitDriftPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	base, ref, err := GoPoster{}.PostEntry(req)
	if err != nil || ref != nil {
		return base, ref, err
	}
	if !base.HasRequestedAmount {
		return base, nil, nil
	}
	base.RequestedAmountMinor++
	return base, nil, nil
}

func init() {
	Register("ledger-go", NewGoPoster())
	RegisterWrong("ledger-wrong-split-drift",
		"keeps the entry internally balanced (I-1 holds) while the splits sum to ONE MINOR UNIT less "+
			"than the transaction amount the caller requested (I-2 fails). It is the implementation "+
			"that proves I-2 is not a restatement of I-1",
		splitDriftPoster{})
	RegisterWrong("ledger-wrong-truncating",
		"drops the minor units: reads the major-unit text as a whole number, the defect a whole-tugrik "+
			"corpus could not tell from a correct port",
		truncatingPoster{})
	RegisterWrong("ledger-wrong-header-refusing",
		"refuses a posting to a HEADER (summary) account, which the oracle ACCEPTS with HTTP 200 (A2-345) "+
			"- an 'improvement' on the oracle is a divergence from it",
		headerRefusingPoster{})
	RegisterWrong("ledger-wrong-manual-permission-ignored",
		"never reads acc_gl_account.manual_journal_entries_allowed, so it posts where the oracle refuses "+
			"with HTTP 403 (A2-346)",
		manualPermissionIgnoringPoster{})
	RegisterWrong("ledger-wrong-openingbalance-posted-entries-ignored",
		"defines opening balances without checking whether journal entries have already been posted, "+
			"so it never reaches validateJournalEntriesArePostedBefore's refusal (:717/:810-816) and "+
			"answers a defineOpeningBalance command the oracle refused with HTTP 403 "+
			"error.msg.journalentry.defining.openingbalance.not.allowed (T294, OB-01)",
		openingBalanceUncheckedPoster{})
	RegisterWrong("ledger-wrong-openingbalance-always-refusing",
		"refuses EVERY defineOpeningBalance command, including on an EMPTY ledger where the reference "+
			"oracle ACCEPTS (:812's CollectionUtils.isEmpty fall-through into the writes at :742/:745). "+
			"This is T296's arm A, which SURVIVED the whole ledger corpus until an accepting-side "+
			"observation existed: every refusal capture in this store agrees with it. Diverging from "+
			"the oracle BY REFUSING is still diverging (T305, OB-ACCEPT-01)",
		openingBalanceAlwaysRefusingPoster{})
	RegisterWrong("ledger-wrong-openingbalance-no-contra",
		"accepts an opening balance and writes ONLY the caller's legs, missing the CONTRA entry :796 "+
			"writes for each of them on the financial-activity-300 account -- so its trial balance is "+
			"short by the entire opening position while every leg the caller can see is byte-perfect "+
			"(T305, OB-ACCEPT-01: three legs in, SIX journal entries out)",
		openingBalanceNoContraPoster{})
	RegisterWrong("ledger-wrong-future-date-ignored",
		"never compares the entry's transaction date with the tenant's BUSINESS DATE, so it posts a "+
			"future-dated entry the oracle refused with HTTP 403 "+
			"error.msg.glJournalEntry.invalid.future.date (:629, DateUtils.isDateInTheFuture). The "+
			"business date is tenant ambient state and appears nowhere in the request body (T295, A1-02)",
		futureDateIgnoringPoster{})
	RegisterWrong("ledger-wrong-closure-boundary-exclusive",
		"implements the accounting-closure boundary as the oracle's own message text describes it "+
			"-- STRICTLY 'prior to' the closing date -- where :636 is "+
			"!DateUtils.isBefore(closingDate, transactionDate) and refuses transactionDate <= "+
			"closingDate INCLUSIVE. It therefore FAILS OPEN on an entry dated ON the closing date, "+
			"which is the day a period-end adjustment carries (T295, A2-01)",
		closureBoundaryExclusivePoster{})
	RegisterWrong("ledger-wrong-netting-totals",
		"nets credits against debits into one accumulator, so I-1 holds by construction and both totals "+
			"report the netted figure",
		nettingPoster{})
	RegisterWrong("ledger-wrong-code-ignored",
		"never joins the chart, so every resolved gl_account_code is empty",
		codeIgnoringPoster{})
}

// minorText renders minor units as the decimal-free integer STRING the schema
// stores. strconv.FormatInt, never a float formatter.
func minorText(m ledger.MinorUnits) string { return strconv.FormatInt(int64(m), 10) }
