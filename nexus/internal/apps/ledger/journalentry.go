package ledger

import "fmt"

// This file is slice A1: the journal-entry posting engine and the double-entry
// invariant it enforces. It is the write path the account model in glaccount.go
// exists to serve. It owns no arithmetic of its own beyond what money.go
// (MinorUnitsFromDecimalText) and this file's double-entry check already carry;
// balances are DERIVED from entries (G-12) and are never written here.

// Refusal codes and messages of the posting path. These are the oracle's wire
// contract, OBSERVED in committed captures, not inferred from source:
//
//	error.msg.journalentry.defining.openingbalance.not.allowed
//	    [OBSERVED: OB-01, LDG-REFUSE-03]
//	error.msg.glJournalEntry.invalid.future.date
//	    [OBSERVED: A1-02, LDG-REFUSE-05]
//	error.msg.glJournalEntry.invalid.accounting.closed
//	    [OBSERVED: A2-01, LDG-REFUSE-04]
//	error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted
//	    [OBSERVED: A2-346]
//	error.msg.glJournalEntry.invalid.mismatch.debits.credits
//	    [OBSERVED: A2-344, LDG-REFUSE-01]
//
// They are exported so the conformance harness can key admission rules and
// comparisons on one string rather than two files typing it twice.
const (
	CodeOpeningBalanceNotAllowed = "error.msg.journalentry.defining.openingbalance.not.allowed"
	MsgOpeningBalanceNotAllowed  = "Defining Opening balances not allowed after journal entries posted"

	CodeFutureDate = "error.msg.glJournalEntry.invalid.future.date"
	MsgFutureDate  = "The journal entry cannot be made for a future date"

	CodeAccountingClosed = "error.msg.glJournalEntry.invalid.accounting.closed"
	MsgAccountingClosed  = "Journal entry cannot be made prior to last account closing date for the branch"

	CodeManualAdjustment = "error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted"
	MsgManualAdjustment  = "Target account does not allow manual adjustments"

	CodeDebitCreditMismatch = "error.msg.glJournalEntry.invalid.mismatch.debits.credits"
	MsgDebitCreditMismatch  = "Sum of All Debits must equal the sum of all Credits for a Journal Entry"
)

// JournalRefusal is a posting refusal carrying the oracle's HTTP status, its
// globalisation code and its message text, exactly as the wire emitted them.
//
// Arg0Value is the value an implementation would put in errors[0].args[0].value
// on the two DATE refusals; it is empty on every other refusal. It is carried
// as a plain string because it is a calendar date rendered as `yyyy-MM-dd`, not
// a time instant (no offset, no zone, no clock).
type JournalRefusal struct {
	HTTPStatus int
	Code       string
	Message    string
	Arg0Value  string
}

// JournalEntryLeg is one RESOLVED leg of a posting: the account it hits, the
// side it lands on, the amount in integer minor units, and — for a leg that
// arrived through an accounting placeholder rather than a manual account choice
// — the Java constant name of that placeholder.
//
// A leg carries the full GLAccount, not a bare id, for one reason: STEP 2 (the
// manual-adjustment rule) reads ManualEntriesAllowed at posting time, and that
// is a fact about the account that a snapshot does not carry. The resolver (A2)
// already hands back a *GLAccount, so carrying it forward is free.
type JournalEntryLeg struct {
	Account  GLAccount
	Side     EntrySide
	Amount   MinorUnits
	SlotName string
}

// JournalEntry is one PERSISTED row of acc_gl_journal_entry — a single leg, the
// same atom the engine produces. It carries only the columns a money decision
// reads. The three running-balance columns (is_running_balance_calculated,
// office_running_balance, organization_running_balance) are DELIBERATELY absent:
// G-12 derives the trial-balance closing balance and this package writes no
// written-balance path.
type JournalEntry struct {
	ID            int64
	AccountID     int64
	OfficeID      int64
	CurrencyCode  string
	TransactionID string
	Reversed      bool
	ManualEntry   bool
	EntryDate     string // strict yyyy-MM-dd
	Side          EntrySide
	Amount        MinorUnits
}

// PostingCommand is the posting engine's input. It is the shape a caller builds
// after resolving every slot to an account; resolution is A2's job and is
// deliberately not repeated here.
//
// BusinessDate and LatestClosingDate are EMPTY when the caller asserts nothing
// about the future-date and accounting-closure rules respectively — the two
// rules are ambient-state preconditions lifted into the request as inputs, and
// an empty value means "skip this rule", never "read a clock".
type PostingCommand struct {
	OfficeID      int64
	CurrencyCode  string
	TransactionID string
	ManualEntry   bool

	TransactionDate   string // strict yyyy-MM-dd
	BusinessDate      string // empty = no future-date assertion
	LatestClosingDate string // empty = no closure at this office

	Command       string // "" or "defineOpeningBalance"
	ContraAccount GLAccount

	PostedNonContraTransactionIDs []string

	Legs []JournalEntryLeg
}

// PostingResult is the engine's accepted answer.
type PostingResult struct {
	TransactionID     string
	Legs              []JournalEntryLeg
	TotalDebitsMinor  MinorUnits
	TotalCreditsMinor MinorUnits
}

// Poster is the posting engine. It is stateless: every dependency a posting
// needs (the resolved accounts, the dates, the posted-transaction precondition)
// is already in PostingCommand.
type Poster struct{}

// NewPoster returns the posting engine.
func NewPoster() *Poster { return &Poster{} }

// Post validates and expands a posting. It returns a refusal for every
// oracle-faithful refusal and a non-nil error only for a caller defect — a
// request that could not have been observed (for example an opening-balance
// command with no contra account) — never for a posting the oracle would
// refuse.
func (Poster) Post(cmd PostingCommand) (PostingResult, *JournalRefusal, error) {
	legs := make([]PostingLeg, 0, len(cmd.Legs))
	var debits, credits MinorUnits
	for i, l := range cmd.Legs {
		switch l.Side {
		case EntryDebit:
			debits += l.Amount
		case EntryCredit:
			credits += l.Amount
		default:
			return PostingResult{}, nil, fmt.Errorf("leg %d: unknown entry side %d", i, int32(l.Side))
		}
		legs = append(legs, PostingLeg{Account: l.Account.Snapshot(), Side: l.Side, Amount: l.Amount})
	}

	// STEP 1.5 — THE OPENING-BALANCE RULE. Opening balances may not be defined
	// once a NON-CONTRA journal entry exists. The predicate is NON-EMPTY, not
	// non-zero, because the oracle computes CollectionUtils.isEmpty over the
	// findNonContraTransactionIds result.
	//
	// ITS POSITION IS OBSERVED: OB-01's request is UNBALANCED by exactly one
	// minor unit, so the oracle had two independent grounds to refuse it and
	// returned THIS one — :717 runs before the balance check inside :724.
	if cmd.Command == "defineOpeningBalance" && len(cmd.PostedNonContraTransactionIDs) > 0 {
		return PostingResult{}, &JournalRefusal{
			HTTPStatus: 403,
			Code:       CodeOpeningBalanceNotAllowed,
			Message:    MsgOpeningBalanceNotAllowed,
		}, nil
	}

	// STEP 1.6 — THE FUTURE-DATE RULE. STRICT: an entry dated ON the business
	// date is not future-dated. It echoes the TRANSACTION date, not the
	// business date it compared against.
	if cmd.BusinessDate != "" && cmd.TransactionDate != "" &&
		isoAfter(cmd.TransactionDate, cmd.BusinessDate) {
		return PostingResult{}, &JournalRefusal{
			HTTPStatus: 403,
			Code:       CodeFutureDate,
			Message:    MsgFutureDate,
			Arg0Value:  cmd.TransactionDate,
		}, nil
	}

	// STEP 1.7 — THE ACCOUNTING-CLOSURE RULE. INCLUSIVE boundary: an entry
	// dated ON the closing date is refused (transactionDate <= closingDate).
	// It echoes the CLOSING date, not the transaction date.
	if cmd.LatestClosingDate != "" && cmd.TransactionDate != "" &&
		!isoBefore(cmd.LatestClosingDate, cmd.TransactionDate) {
		return PostingResult{}, &JournalRefusal{
			HTTPStatus: 403,
			Code:       CodeAccountingClosed,
			Message:    MsgAccountingClosed,
			Arg0Value:  cmd.LatestClosingDate,
		}, nil
	}

	// STEP 2 — THE MANUAL-ADJUSTMENT RULE, applied only to a MANUAL entry.
	if cmd.ManualEntry {
		for i := range cmd.Legs {
			if !cmd.Legs[i].Account.ManualEntriesAllowed {
				return PostingResult{}, &JournalRefusal{
					HTTPStatus: 403,
					Code:       CodeManualAdjustment,
					Message:    MsgManualAdjustment,
				}, nil
			}
		}
	}

	// STEP 3 — I-1, DOUBLE ENTRY, by the port's own function. NOTE WHAT IS NOT
	// HERE: no HEADER-account refusal. A2-345 posted to a HEADER account and the
	// oracle returned HTTP 200.
	if err := DoubleEntryBalances(legs); err != nil {
		return PostingResult{}, &JournalRefusal{
			HTTPStatus: 403,
			Code:       CodeDebitCreditMismatch,
			Message:    MsgDebitCreditMismatch,
		}, nil
	}

	out := PostingResult{
		TransactionID:     cmd.TransactionID,
		Legs:              cmd.Legs,
		TotalDebitsMinor:  debits,
		TotalCreditsMinor: credits,
	}

	// STEP 4 — AN ACCEPTED OPENING BALANCE POSTS TWO ENTRIES PER LEG: the leg
	// itself, then its CONTRA entry on the financial-activity-300 account with
	// the opposite side. The contra is PER LEG and not summed. Debits are
	// emitted before credits, matching the oracle's debit-array-then-credit-array
	// order.
	if cmd.Command == "defineOpeningBalance" {
		if cmd.ContraAccount.ID == 0 {
			return PostingResult{}, nil, fmt.Errorf(
				"command is defineOpeningBalance but no contra account was resolved")
		}
		expanded := make([]JournalEntryLeg, 0, len(out.Legs)*2)
		var d2, c2 MinorUnits
		for _, side := range []EntrySide{EntryDebit, EntryCredit} {
			for _, l := range out.Legs {
				if l.Side != side {
					continue
				}
				expanded = append(expanded, l)
				expanded = append(expanded, JournalEntryLeg{
					Account: cmd.ContraAccount,
					Side:    OppositeSide(l.Side),
					Amount:  l.Amount,
				})
				d2 += l.Amount
				c2 += l.Amount
			}
		}
		out.Legs = expanded
		out.TotalDebitsMinor = d2
		out.TotalCreditsMinor = c2
	}

	return out, nil, nil
}

// OppositeSide is the contra side an opening-balance entry writes for a leg.
func OppositeSide(s EntrySide) EntrySide {
	if s == EntryDebit {
		return EntryCredit
	}
	return EntryDebit
}

// isoBefore and isoAfter order two STRICT `yyyy-MM-dd` calendar dates.
//
// Plain string comparison is correct here: for zero-padded, fixed-width ISO-8601
// dates, lexicographic order IS chronological order. Callers are responsible for
// the strictness of the format; this function does not parse and cannot fail.
func isoBefore(a, b string) bool { return a < b }
func isoAfter(a, b string) bool  { return a > b }
