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
	return out, nil, nil
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
