package ledger

// G-12: DERIVE-ONLY BALANCES — the running-balance columns are never read or
// written.
//
// CLAUDE.md (non-negotiable): "The ledger is double-entry and append-only.
// Balances are derived, never written." The reference oracle does the opposite:
// it stores a denormalised running balance ON the posted acc_gl_journal_entry
// row and rewrites it in place, nightly, by
//
//	UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?,
//	  organization_running_balance=?, office_running_balance=?,
//	  last_modified_by=?, last_modified_on_utc=?  WHERE id=?
//
// [VERIFIED: JournalEntryRunningBalanceUpdateServiceImpl.java:163-165, pinned
// 426a23544], driven from scheduled job 9 "Update Accounting Running Balances"
// through AccountRunningBalanceUpdateTasklet -> updateRunningBalance(), outside
// the command bus.
//
// THIS PORT HONOURS THE NON-NEGOTIABLE. A pgx-backed journal-entry repository
// (slice A1) derives every balance from the append-only entries and must never
// SELECT, INSERT or UPDATE the three columns below. They stay in the adopted
// schema with their DDL defaults so the Go module and the oracle can share one
// PostgreSQL database, but the port neither reads nor writes them, and it never
// runs an equivalent of ACCOUNTING_RUNNING_BALANCE_UPDATE.
//
// This is the storage-layer half of the G-12 ruling. The shadow-parity half —
// excluding exactly these three columns on a row-level Go-vs-oracle diff — is
// enforced by the conformance package's oracle-derived-column registry
// (internal/apps/ledger/conformance/oraclederived.go), whose ORACLE_DERIVED
// population must stay equal to this list.

// RunningBalanceColumns are the acc_gl_journal_entry columns the reference
// oracle writes by job 9 and this port refuses to read or write, in the order
// the shadow-parity exclusion list uses. G-12. Editing this list is the only
// way to widen the storage-layer carve-out, and it is therefore kept as code
// rather than prose so a change is a visible source diff.
func RunningBalanceColumns() []string {
	return []string{
		"office_running_balance",
		"organization_running_balance",
		"is_running_balance_calculated",
	}
}
