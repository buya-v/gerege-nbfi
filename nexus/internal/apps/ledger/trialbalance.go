package ledger

// This file is slice A3's trial-balance arm, and it is DERIVE-ONLY (G-12).
//
// The oracle keeps a written running balance on every acc_gl_journal_entry row
// (office_running_balance, organization_running_balance) and serves the trial
// balance from the LAST row per account. That written balance is exactly what
// G-12 forbids this port from producing: a written balance drifts, and the
// drift is invisible until a period-end report is wrong. The port derives the
// closing balance from the entries themselves, so a trial-balance line is a
// pure function of the entries and nothing else.

// TrialBalanceLine is one account's derived closing position.
type TrialBalanceLine struct {
	AccountID    int64
	TotalDebits  MinorUnits
	TotalCredits MinorUnits
}

// Net returns the account's closing balance: debits minus credits. The sign is
// the account's natural-side convention, not a judgement: an ASSET account runs
// a debit balance, a LIABILITY or EQUITY account runs a credit balance.
func (l TrialBalanceLine) Net() MinorUnits { return l.TotalDebits - l.TotalCredits }

// DeriveTrialBalance reduces a set of journal entries to one line per account,
// in integer minor units. EVERY entry is included: the Reversed flag does not
// change a line.
//
// WHY THE FLAG IS NOT A SIGN. When the oracle reverses an entry it does NOT
// rewrite the original row into its negation. It leaves the row in place, MARKs
// it reversed, and adds a counter-entry of the opposite side; the counter-entry
// is what cancels the position. There are two reversal paths and they agree:
//
//   - MANUAL. revertJournalEntry
//     [JournalEntryWritePlatformServiceJpaRepositoryImpl.java:380-429] persists,
//     for each original, a counter-entry of the opposite side on a FRESH
//     transaction id (:402-422), then flags the original setReversed(true)
//     (:423). The counter-entry is never flagged. Observed live on JE 141/142:
//     both read reversed=true with reversal_id set while the unflagged
//     counter-entries 143/144 were posted on transaction id a2b7964aa51b, a new
//     id, not the original's a2b795dca42b, and the originals' account, side,
//     amount and date are otherwise unchanged
//     [.softhouse/capture/tb-manual-reversal/step03-readback/sql-rows.txt].
//   - LOAN. createJournalEntryForReversedLoanTransaction [:359-378] adds the
//     same opposite-side counter-entries on the SAME transaction id and flags
//     NOTHING (:369-377).
//
// THE ORACLE'S TRIAL BALANCE SUMS EVERY ROW AND HAS NO `reversed` PREDICATE.
// findTrialBalanceLinesForDate [JournalEntryRepository.java:52-66] is
// SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END) ...
// GROUP BY office, glAccount, ... . Under BOTH paths the counter-entry cancels
// the original, so summing everything nets a reversed pair to zero. SKIPPING
// THE FLAGGED ROW DOES NOT: it drops one leg of the pair and keeps the other,
// removing the reversed position TWICE. That double removal is the defect this
// comment exists to prevent — account 6 reads -1234567 and account 10 +1234567
// on rows 141-144 where the oracle's rule gives 0 and 0. The loan path never
// tripped it because it flags nothing, so a port that skipped flagged rows
// looked correct on every loan-reversal capture; only the manual path, which
// flags the original AND adds an unflagged counter-entry, exposes it.
func DeriveTrialBalance(entries []JournalEntry) map[int64]TrialBalanceLine {
	out := make(map[int64]TrialBalanceLine)
	for _, e := range entries {
		line := out[e.AccountID]
		line.AccountID = e.AccountID
		switch e.Side {
		case EntryDebit:
			line.TotalDebits += e.Amount
		case EntryCredit:
			line.TotalCredits += e.Amount
		}
		out[e.AccountID] = line
	}
	return out
}
