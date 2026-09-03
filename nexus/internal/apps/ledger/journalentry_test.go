package ledger

import (
	"context"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// These tests hold the A1 engine's two structural invariants directly — the
// double-entry check and the refusal precedence — plus the persistence layer's
// argument builder, without a database. The end-to-end parity and mutation grading
// lives in the conformance harness; these pin the engine the harness now calls.

func testAccount(id int64, code string) GLAccount {
	return GLAccount{
		ID:                   id,
		GLCode:               code,
		Name:                 code,
		ManualEntriesAllowed: true,
		Usage:                UsageDetail,
	}
}

func testLeg(account GLAccount, side EntrySide, amount MinorUnits) JournalEntryLeg {
	return JournalEntryLeg{Account: account, Side: side, Amount: amount}
}

// TestPosterRefusesUnbalancedPosting drives the double-entry invariant through
// the engine rather than through DoubleEntryBalances directly.
func TestPosterRefusesUnbalancedPosting(t *testing.T) {
	asset := testAccount(2, "1000")
	income := testAccount(4, "4000")
	cmd := PostingCommand{
		TransactionID: "T1",
		Legs: []JournalEntryLeg{
			testLeg(asset, EntryDebit, 100),
			testLeg(income, EntryCredit, 99),
		},
	}
	_, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal == nil || refusal.Code != CodeDebitCreditMismatch {
		t.Fatalf("refusal = %+v, want the debit/credit mismatch code", refusal)
	}
	if refusal.HTTPStatus != 403 {
		t.Errorf("HTTP status = %d, want 403", refusal.HTTPStatus)
	}
}

// TestPosterOpeningBalanceRefusalPrecedesBalanceRule pins the observed refusal
// precedence: OB-01's request is UNBALANCED by one minor unit yet the oracle
// returned the opening-balance refusal, because that rule runs before the
// balance check.
func TestPosterOpeningBalanceRefusalPrecedesBalanceRule(t *testing.T) {
	asset := testAccount(2, "1000")
	income := testAccount(4, "4000")
	cmd := PostingCommand{
		Command:       "defineOpeningBalance",
		TransactionID: "OB-01",
		Legs: []JournalEntryLeg{
			testLeg(asset, EntryDebit, 100),
			testLeg(income, EntryCredit, 99),
		},
		PostedNonContraTransactionIDs: []string{"X", "Y"},
	}
	_, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal == nil || refusal.Code != CodeOpeningBalanceNotAllowed {
		t.Fatalf("refusal = %+v, want the opening-balance code (balance check must NOT fire first)", refusal)
	}
}

// TestPosterExpandsOpeningBalanceContraPerLeg holds the accepted-opening-balance
// shape: every leg gets its own opposite-side contra on the financial-activity
// account, debits are emitted before credits, and the expansion stays balanced.
func TestPosterExpandsOpeningBalanceContraPerLeg(t *testing.T) {
	contra := testAccount(1, "3000")
	gl2 := testAccount(2, "1000")
	gl3 := testAccount(3, "1100")
	gl4 := testAccount(4, "2000")
	cmd := PostingCommand{
		Command:       "defineOpeningBalance",
		TransactionID: "OB-ACCEPT",
		ContraAccount: contra,
		Legs: []JournalEntryLeg{
			testLeg(gl2, EntryDebit, 25000025),
			testLeg(gl3, EntryDebit, 10000037),
			testLeg(gl4, EntryCredit, 35000062),
		},
	}

	result, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal != nil {
		t.Fatalf("unexpected refusal: %+v", refusal)
	}
	if len(result.Legs) != 6 {
		t.Fatalf("expanded legs = %d, want 6 (one contra per leg)", len(result.Legs))
	}
	// Debits before credits, contra per leg.
	wantFirst := []struct {
		account int64
		side    EntrySide
		amount  MinorUnits
	}{
		{2, EntryDebit, 25000025},
		{1, EntryCredit, 25000025},
		{3, EntryDebit, 10000037},
		{1, EntryCredit, 10000037},
		{4, EntryCredit, 35000062},
		{1, EntryDebit, 35000062},
	}
	for i, w := range wantFirst {
		l := result.Legs[i]
		if l.Account.ID != w.account || l.Side != w.side || l.Amount != w.amount {
			t.Errorf("leg %d = (%d, %v, %d), want (%d, %v, %d)",
				i, l.Account.ID, l.Side, l.Amount, w.account, w.side, w.amount)
		}
	}
	// After contra expansion every original leg contributes one debit AND one
	// credit of its amount, so both totals equal the sum of all three legs.
	if result.TotalDebitsMinor != 70000124 || result.TotalCreditsMinor != 70000124 {
		t.Errorf("totals = %d / %d, want 70000124 / 70000124 (balanced after contra)",
			result.TotalDebitsMinor, result.TotalCreditsMinor)
	}
}

// TestBuildJournalEntryInsertArgsPinsTheColumnArrays asserts the arguments the
// persistence layer binds — THIRTEEN parallel column arrays, one element per
// entry, with the amount rendered back to exact decimal text — without touching
// a database. (Eleven until T508 added the audit instant and the business date.)
//
// IT CANNOT, AND NEVER COULD, DETECT A COLUMN NAME THAT DOES NOT EXIST. [T508]
// Every assertion here is about the ARGUMENTS; the column list lives in the SQL
// literal, which this test does not read. That is why `createdby_id` — a column
// present in no schema — survived here for two task generations with this test
// green. TestAppendExecutesAgainstTheRealSchema below is the one that can.
//
// WHAT THIS TEST NO LONGER PINS, AND WHY THAT IS NOT A LOSS. [T503] It used to
// reconstruct the SQL string and assert its shape, because the statement was
// assembled at run time and existed nowhere a reader could see it. The
// statement is now a fixed literal at the single call site in
// journalentry_postgres.go Append, so it is read directly from source — by a
// reviewer and by the I-3/I-4 guard, which is what the guard demanded. A test
// that re-derived it would only be asserting a copy against itself. The row
// count moved out of the SQL and into these arrays, which is exactly what this
// test now pins.
func TestBuildJournalEntryInsertArgsPinsTheColumnArrays(t *testing.T) {
	entries := []JournalEntry{
		{
			AccountID:     2,
			OfficeID:      1,
			CurrencyCode:  "MNT",
			TransactionID: "T1",
			EntryDate:     "2026-08-24",
			Side:          EntryDebit,
			Amount:        25000025,
		},
		{
			AccountID:     1,
			OfficeID:      1,
			CurrencyCode:  "MNT",
			TransactionID: "T1",
			EntryDate:     "2026-08-24",
			Side:          EntryCredit,
			Amount:        25000025,
		},
	}

	args := buildJournalEntryInsertArgs(entries, 1, 1, "2026-09-03T10:39:49.289487Z", "2026-09-03")
	if got := len(args); got != 13 {
		t.Fatalf("arg count = %d, want 13 column arrays ($1..$13)", got)
	}

	// Every array must be the same length as the batch, or unnest would zip
	// rows out of alignment and a leg would be written against another leg's
	// account.
	for i, a := range args {
		n := reflect.ValueOf(a).Len()
		if n != len(entries) {
			t.Errorf("arg $%d has %d elements, want %d (one per entry)", i+1, n, len(entries))
		}
	}

	if got := args[3].([]string); got[0] != "T1" || got[1] != "T1" {
		t.Errorf("transaction_id array = %q, want both legs on T1", got)
	}
	if got := args[8].([]string); got[0] != "250000.25" || got[1] != "250000.25" {
		t.Errorf("amount array = %q, want exact decimal text for 25000025 minor units", got)
	}
	if got := args[0].([]int64); got[0] != 2 || got[1] != 1 {
		t.Errorf("account_id array = %v, want [2 1] in entry order", got)
	}
	if got := args[7].([]int32); got[0] != int32(EntryDebit) || got[1] != int32(EntryCredit) {
		t.Errorf("type_enum array = %v, want [debit credit] in entry order", got)
	}
	if got := args[6].([]string); got[0] != "2026-08-24" || got[1] != "2026-08-24" {
		t.Errorf("entry_date array = %q, want the strict yyyy-MM-dd text both legs carry", got)
	}
	// $12 feeds BOTH created_on_utc and last_modified_on_utc, so one array holds
	// one instant repeated per entry. The oracle writes the same instant to both
	// columns on insert.
	if got := args[11].([]string); got[0] != "2026-09-03T10:39:49.289487Z" || got[1] != got[0] {
		t.Errorf("audit_on_utc array = %q, want the one UTC instant on every leg", got)
	}
	// $13 is submitted_on_date, which is the BUSINESS date and is NOT entry_date.
	// These two fixtures differ on purpose: the oracle capture that settled this
	// had entry_date 2026-08-24 and submitted_on_date 2026-09-03.
	if got := args[12].([]string); got[0] != "2026-09-03" || got[1] != "2026-09-03" {
		t.Errorf("submitted_on_date array = %q, want the business date on every leg", got)
	}
	if entryDates, submitted := args[6].([]string), args[12].([]string); entryDates[0] == submitted[0] {
		t.Fatalf("the fixture no longer separates entry_date from submitted_on_date (%q); "+
			"this test cannot detect a port that conflates them", submitted[0])
	}
}

// TestAppendRefusesWhenSubmittedOnDateIsNotResolvable pins the fail-closed
// branch. submitted_on_date is NOT NULL with no default and the oracle fills it
// from the tenant's BUSINESS date, which this package cannot invent — so an
// unconfigured repository must refuse rather than write a guessed date.
//
// The refusal happens BEFORE any statement is sent, which is why this test needs
// no database and passes a nil postgres.DB: reaching the driver would panic.
func TestAppendRefusesWhenSubmittedOnDateIsNotResolvable(t *testing.T) {
	entries := []JournalEntry{{
		AccountID: 2, OfficeID: 1, CurrencyCode: "MNT", TransactionID: "T1",
		EntryDate: "2026-08-24", Side: EntryDebit, Amount: 25000025,
	}}

	r := NewPostgresJournalEntryRepository(context.Background(), nil)
	if err := r.Append(entries); err == nil {
		t.Fatal("Append with no tenant location and no business date returned nil; " +
			"it must refuse rather than invent submitted_on_date")
	}

	// An ill-formed explicit business date is refused too — the column is a
	// `date`, and a value Postgres would reject should not reach Postgres.
	r.SetBusinessDate("2026-2-3")
	if err := r.Append(entries); err == nil {
		t.Fatal("Append accepted a non-zero-padded business date; want a refusal")
	}
	r.SetBusinessDate("2026-02-30")
	if err := r.Append(entries); err == nil {
		t.Fatal("Append accepted 2026-02-30 as a business date; want a refusal")
	}
}

// TestSubmittedOnDateComesFromTheTENANTZone holds the rule that the business
// date is a tenant-zone calendar date, not a UTC one. The instant chosen is
// 2026-09-03T17:30:00Z, which is still 3 September in UTC but already
// 4 September in Asia/Ulaanbaatar (+08) and in Asia/Hovd (+07) — the only two
// zones CLAUDE.md permits. A port that stamped the UTC date would write the
// wrong day for every posting made after 16:00 UTC.
func TestSubmittedOnDateComesFromTheTENANTZone(t *testing.T) {
	instant := time.Date(2026, 9, 3, 17, 30, 0, 0, time.UTC)

	for _, tc := range []struct{ zone, want string }{
		{"Asia/Ulaanbaatar", "2026-09-04"},
		{"Asia/Hovd", "2026-09-04"},
	} {
		loc, err := time.LoadLocation(tc.zone)
		if err != nil {
			t.Fatalf("LoadLocation(%q): %v", tc.zone, err)
		}
		r := NewPostgresJournalEntryRepository(context.Background(), nil)
		r.SetAuditClock(func() time.Time { return instant })
		r.SetTenantLocation(loc)

		got, err := r.resolveSubmittedOnDate()
		if err != nil {
			t.Fatalf("%s: resolveSubmittedOnDate: %v", tc.zone, err)
		}
		if got != tc.want {
			t.Errorf("%s: submitted_on_date = %q, want %q (the UTC date %q would be wrong)",
				tc.zone, got, tc.want, instant.Format("2006-01-02"))
		}
	}

	// An explicit business date wins, which is the oracle's
	// isBusinessDateEnabled() branch.
	loc, err := time.LoadLocation("Asia/Ulaanbaatar")
	if err != nil {
		t.Fatalf("LoadLocation: %v", err)
	}
	r := NewPostgresJournalEntryRepository(context.Background(), nil)
	r.SetAuditClock(func() time.Time { return instant })
	r.SetTenantLocation(loc)
	r.SetBusinessDate("2026-08-31")
	got, err := r.resolveSubmittedOnDate()
	if err != nil {
		t.Fatalf("resolveSubmittedOnDate: %v", err)
	}
	if got != "2026-08-31" {
		t.Errorf("submitted_on_date = %q, want the pinned COB business date 2026-08-31", got)
	}
}

// TestAuditUTCTextIsMicrosecondUTC pins the rendering of created_on_utc /
// last_modified_on_utc: normalised to UTC whatever zone the clock returns, and
// TRUNCATED to microseconds because that is `timestamptz`'s resolution — a
// nanosecond-bearing literal would be reinterpreted by the server.
func TestAuditUTCTextIsMicrosecondUTC(t *testing.T) {
	loc, err := time.LoadLocation("Asia/Ulaanbaatar")
	if err != nil {
		t.Fatalf("LoadLocation: %v", err)
	}
	// 18:39:49.289487999 +08 is 10:39:49.289487999 UTC.
	got := time.Date(2026, 9, 3, 18, 39, 49, 289487999, loc).UTC().Format(auditUTCLayout)
	if want := "2026-09-03T10:39:49.289487Z"; got != want {
		t.Errorf("audit text = %q, want %q", got, want)
	}
}

// --- the database-backed leg -------------------------------------------------

// TestAppendExecutesAgainstTheRealSchema is the test whose ABSENCE let a
// non-executable INSERT sit in the money core unnoticed. Every other test in
// this package asserts arguments or pure functions; none of them could ever have
// caught `createdby_id`, a column that exists in no schema, or three missing NOT
// NULL columns.
//
// It runs only when PGDATABASE and PGUSER are set, and it always ROLLS BACK, so
// it can point at the reference oracle's own database without leaving a row
// behind. When those variables are unset it SKIPS with a message that names what
// went unchecked — a skip is not a pass and must not read like one.
func TestAppendExecutesAgainstTheRealSchema(t *testing.T) {
	if os.Getenv("PGDATABASE") == "" || os.Getenv("PGUSER") == "" {
		t.Skip("SKIPPED, NOT PASSED: PGDATABASE/PGUSER unset, so the acc_gl_journal_entry " +
			"INSERT was NOT executed against any schema. Column names and NOT NULL " +
			"coverage are unverified in this run.")
	}

	ctx := context.Background()
	pool, err := postgres.NewPool(ctx, postgres.ConfigFromEnv())
	if err != nil {
		t.Fatalf("connect: %v", err)
	}
	defer pool.Close()

	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatalf("begin: %v", err)
	}
	// Never commit. The ledger is append-only and this is a live schema.
	defer func() { _ = tx.Rollback(ctx) }()

	// Bind to whatever account/office the target database actually has, so the
	// foreign keys hold without this test seeding anything.
	var accountID, officeID, userID int64
	if err := tx.QueryRow(ctx, `SELECT (SELECT id FROM acc_gl_account ORDER BY id LIMIT 1),
	                                   (SELECT id FROM m_office ORDER BY id LIMIT 1),
	                                   (SELECT id FROM m_appuser ORDER BY id LIMIT 1)`).
		Scan(&accountID, &officeID, &userID); err != nil {
		t.Skipf("SKIPPED, NOT PASSED: %s has no GL account / office / user to bind the "+
			"foreign keys to (%v), so the INSERT was NOT executed", os.Getenv("PGDATABASE"), err)
	}

	loc, err := time.LoadLocation("Asia/Ulaanbaatar")
	if err != nil {
		t.Fatalf("LoadLocation: %v", err)
	}
	instant := time.Date(2026, 9, 3, 10, 39, 49, 289487000, time.UTC)

	r := NewPostgresJournalEntryRepository(ctx, tx)
	r.SetAuditIDs(userID, userID)
	r.SetAuditClock(func() time.Time { return instant })
	r.SetTenantLocation(loc)

	const txnID = "T508-EXEC-PROBE"
	entries := []JournalEntry{
		{AccountID: accountID, OfficeID: officeID, CurrencyCode: "MNT", TransactionID: txnID,
			EntryDate: "2026-08-24", Side: EntryDebit, Amount: 25000025},
		{AccountID: accountID, OfficeID: officeID, CurrencyCode: "MNT", TransactionID: txnID,
			EntryDate: "2026-08-24", Side: EntryCredit, Amount: 25000025},
	}
	if err := r.Append(entries); err != nil {
		t.Fatalf("Append against the real schema: %v", err)
	}

	// Read the rows back through the repository's own read surface, so the
	// amount round-trips integer minor units -> numeric(19,6) -> minor units.
	got, err := r.FindByTransactionID(txnID)
	if err != nil {
		t.Fatalf("FindByTransactionID: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("read back %d rows, want 2", len(got))
	}
	for i, e := range got {
		if e.Amount != 25000025 {
			t.Errorf("row %d amount = %d minor units, want 25000025 (numeric(19,6) round-trip)", i, e.Amount)
		}
		if e.EntryDate != "2026-08-24" {
			t.Errorf("row %d entry_date = %q, want 2026-08-24", i, e.EntryDate)
		}
	}
	if got[0].Side != EntryDebit || got[1].Side != EntryCredit {
		t.Errorf("sides = %v/%v, want DEBIT(2) then CREDIT(1) in insert order", got[0].Side, got[1].Side)
	}

	// The three columns the statement could not previously supply, read straight
	// from the row rather than from the repository's typed view.
	var createdOnUTC, lastModifiedOnUTC time.Time
	var submittedOnDate time.Time
	var createdDate, lastModifiedDate *time.Time
	if err := tx.QueryRow(ctx, `SELECT created_on_utc, last_modified_on_utc, submitted_on_date,
	                                   created_date, lastmodified_date
	                            FROM acc_gl_journal_entry WHERE transaction_id = $1 ORDER BY id LIMIT 1`, txnID).
		Scan(&createdOnUTC, &lastModifiedOnUTC, &submittedOnDate, &createdDate, &lastModifiedDate); err != nil {
		t.Fatalf("read audit columns: %v", err)
	}
	if !createdOnUTC.Equal(instant) {
		t.Errorf("created_on_utc = %s, want %s", createdOnUTC.UTC(), instant)
	}
	if !lastModifiedOnUTC.Equal(createdOnUTC) {
		t.Errorf("last_modified_on_utc = %s, want it equal to created_on_utc %s on insert",
			lastModifiedOnUTC.UTC(), createdOnUTC.UTC())
	}
	if want := "2026-09-03"; submittedOnDate.Format("2006-01-02") != want {
		t.Errorf("submitted_on_date = %q, want %q (the business date, NOT entry_date)",
			submittedOnDate.Format("2006-01-02"), want)
	}
	// The oracle leaves the legacy pair NULL on this table; so must this port,
	// or every Go-written row differs from every oracle-written row.
	if createdDate != nil || lastModifiedDate != nil {
		t.Errorf("created_date = %v, lastmodified_date = %v; the oracle leaves both NULL on "+
			"acc_gl_journal_entry", createdDate, lastModifiedDate)
	}
}
