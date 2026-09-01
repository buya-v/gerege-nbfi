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
// in integer minor units. Reversed entries are excluded — a reversal negates its
// original and contributes nothing to the closing position.
func DeriveTrialBalance(entries []JournalEntry) map[int64]TrialBalanceLine {
	out := make(map[int64]TrialBalanceLine)
	for _, e := range entries {
		if e.Reversed {
			continue
		}
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
