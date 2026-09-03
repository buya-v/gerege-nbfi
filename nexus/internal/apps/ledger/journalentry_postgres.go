package ledger

import (
	"context"
	"fmt"
	"time"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL write/read surface for slice A1. It follows the
// package rule laid out in postgres.go: no concrete pgx type is named here, and
// a postgres.DB (Querier + Executor) captured at construction carries every
// statement. The import graph stays ledger -> internal/platform/postgres -> pgx.

// JournalEntryRepository is the persistence surface the posting path owns. Its
// methods carry no context.Context for the same reason the A2 read surfaces do:
// the repository captures the context it was constructed with.
type JournalEntryRepository interface {
	Append(entries []JournalEntry) error
	FindByTransactionID(transactionID string) ([]JournalEntry, error)
}

// auditUTCLayout renders an audit instant the way `timestamptz` stores it:
// microsecond resolution, explicit offset, so no PostgreSQL session `TimeZone`
// setting can reinterpret it. The value is always normalised to UTC first, so
// the offset this prints is always `Z`.
//
// Microseconds, not nanoseconds, because PostgreSQL `timestamp with time zone`
// HAS microsecond resolution — a nanosecond-bearing literal would be silently
// rounded by the server, and a value that changes on the way in is a value no
// test can pin. Go's `.000000` TRUNCATES rather than rounds, which is the same
// direction PostgreSQL's own text input takes.
const auditUTCLayout = "2006-01-02T15:04:05.000000Z07:00"

// PostgresJournalEntryRepository persists acc_gl_journal_entry rows.
type PostgresJournalEntryRepository struct {
	ctx context.Context
	db  postgres.DB

	// Audit columns are a user-context concern, not a money concern, and the
	// posting engine does not carry them. A caller that wants real audit trail
	// sets these once at construction; the default is the oracle's system user.
	//
	// COLUMN NAMES [T508]. These bind `created_by` and `last_modified_by`, which
	// are what the table actually calls them. Until T508 the statement named
	// `createdby_id` / `lastmodifiedby_id`, which exist nowhere in the schema:
	// `PREPARE` against the reference oracle's own database answered
	// `ERROR: column "createdby_id" of relation "acc_gl_journal_entry" does not
	// exist`. The oracle's mapping is
	// AbstractAuditableWithUTCDateTimeCustom -> AuditableFieldsConstants
	// CREATED_BY_DB_FIELD = "created_by", LAST_MODIFIED_BY_DB_FIELD =
	// "last_modified_by".
	createdByID      int64
	lastModifiedByID int64

	// auditClock supplies created_on_utc / last_modified_on_utc. It is a field
	// rather than a direct time.Now() call so a test can pin the instant; the
	// value is normalised to UTC by Append regardless of what the clock returns,
	// because the oracle's own provider is
	// DateUtils.getAuditOffsetDateTime() = OffsetDateTime.now(ZoneOffset.UTC).
	auditClock func() time.Time

	// businessDate and tenantLocation are the two ways submitted_on_date can be
	// resolved, and they mirror the oracle's two branches exactly — see
	// resolveSubmittedOnDate. Both are unset by default and Append REFUSES until
	// one is supplied: the business date is tenant state this package cannot
	// invent, and `submitted_on_date` is NOT NULL with no default.
	businessDate   string
	tenantLocation *time.Location
}

// NewPostgresJournalEntryRepository builds the journal-entry persistence
// surface. createdByID and lastModifiedByID default to the oracle's system user
// (1) when zero.
//
// The returned repository is NOT yet usable for Append: submitted_on_date has
// no safe default (see resolveSubmittedOnDate), so a caller must first call
// SetTenantLocation or SetBusinessDate. That is deliberate — the alternative
// defaults are all wrong in a way no error message would reveal.
func NewPostgresJournalEntryRepository(ctx context.Context, db postgres.DB) *PostgresJournalEntryRepository {
	return &PostgresJournalEntryRepository{
		ctx:              ctx,
		db:               db,
		createdByID:      1,
		lastModifiedByID: 1,
		auditClock:       time.Now,
	}
}

// SetAuditIDs overrides the created-by / last-modified-by audit columns.
func (r *PostgresJournalEntryRepository) SetAuditIDs(createdByID, lastModifiedByID int64) {
	r.createdByID = createdByID
	r.lastModifiedByID = lastModifiedByID
}

// SetAuditClock overrides the clock behind created_on_utc / last_modified_on_utc.
// A nil clock is ignored so a caller cannot disarm the audit stamp by accident.
func (r *PostgresJournalEntryRepository) SetAuditClock(now func() time.Time) {
	if now != nil {
		r.auditClock = now
	}
}

// SetTenantLocation supplies the tenant's IANA zone, from which
// submitted_on_date is derived when no explicit business date is pinned.
//
// It takes a *time.Location — a zone, never an offset — because CLAUDE.md
// forbids hard-coding an offset and because Mongolia runs two zones,
// Asia/Ulaanbaatar (+08) and Asia/Hovd (+07). Which one a deployment uses is
// configuration, not a constant.
func (r *PostgresJournalEntryRepository) SetTenantLocation(loc *time.Location) {
	r.tenantLocation = loc
}

// SetBusinessDate pins an explicit business date (strict `yyyy-MM-dd`) for
// submitted_on_date, overriding SetTenantLocation. This is the branch the
// oracle takes when the `enable_business_date` configuration is on: the COB
// business date, which can legitimately lag the tenant's wall-clock date.
func (r *PostgresJournalEntryRepository) SetBusinessDate(date string) {
	r.businessDate = date
}

// resolveSubmittedOnDate produces the strict `yyyy-MM-dd` text for
// acc_gl_journal_entry.submitted_on_date.
//
// WHAT THE ORACLE DOES, and why this is not entry_date. The oracle sets the
// column in the JournalEntry constructor:
//
//	this.submittedOnDate = DateUtils.getBusinessLocalDate();
//	    [fineract-accounting/.../journalentry/domain/JournalEntry.java:136]
//
// and getBusinessLocalDate() is ThreadLocalContextUtil.getBusinessDate()
// [DateUtils.java:238-240], whose map is built by
// BusinessDateReadPlatformServiceImpl.getBusinessDates() [:72-83]:
//
//	LocalDate tenantDate = DateUtils.getLocalDateOfTenant();   // LocalDate.now(tenant zone)
//	businessDateMap.put(BUSINESS_DATE, tenantDate);
//	if (configurationDomainService.isBusinessDateEnabled()) { ...overwrite from m_business_date... }
//
// So: today in the TENANT's zone, overridden by the configured business date
// when that feature is on. The two branches below are those two branches.
//
// It is emphatically NOT entry_date. A capture from the running oracle settles
// that by observation rather than by reading: a manual journal entry posted
// with transactionDate 2026-08-24 landed with entry_date = 2026-08-24 and
// submitted_on_date = 2026-09-03, the day it was posted.
//
// THERE IS NO DEFAULT, and that is the whole point. A UTC-clock default would
// hard-code an offset in all but name and would silently write yesterday's or
// tomorrow's date for a +08 tenant across the day boundary; defaulting to
// entry_date would write a value the oracle never writes. Refusing is the only
// answer that cannot be silently wrong.
func (r *PostgresJournalEntryRepository) resolveSubmittedOnDate() (string, error) {
	if r.businessDate != "" {
		if !isStrictISODate(r.businessDate) {
			return "", fmt.Errorf("ledger: business date %q is not a strict yyyy-MM-dd calendar date", r.businessDate)
		}
		return r.businessDate, nil
	}
	if r.tenantLocation != nil {
		return r.auditClock().In(r.tenantLocation).Format("2006-01-02"), nil
	}
	return "", fmt.Errorf(
		"ledger: submitted_on_date is not resolvable: acc_gl_journal_entry.submitted_on_date is NOT NULL " +
			"with no default, and the oracle fills it from DateUtils.getBusinessLocalDate() " +
			"[JournalEntry.java:136], which is tenant state this package cannot invent — " +
			"call SetTenantLocation (the tenant's IANA zone) or SetBusinessDate (an explicit COB date) first")
}

// isStrictISODate reports whether s is exactly a `yyyy-MM-dd` calendar date.
// It parses rather than pattern-matches, so 2026-02-30 is rejected, and it
// re-renders and compares so a non-zero-padded spelling cannot slip through.
func isStrictISODate(s string) bool {
	t, err := time.Parse("2006-01-02", s)
	return err == nil && t.Format("2006-01-02") == s
}

const journalEntryColumns = `id, account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date::text, type_enum, amount::text`

// Append writes every entry in ONE multi-row INSERT, so a transaction's legs
// commit or roll back together. The running-balance columns are deliberately
// omitted — their defaults apply, and G-12 forbids this port from writing them.
//
// THE STATEMENT IS A FIXED STRING LITERAL AND THAT IS LOAD-BEARING. [T503]
// It used to be assembled at run time — one `($n,$n,…)` tuple per entry joined
// into a VALUES list — which made it a statement no source-level reader could
// read, and the I-3/I-4 guard refused it as OPAQUE-SQL: it could not certify
// that the ledger's own write path was not an UPDATE or a DELETE against
// acc_gl_journal_entry. The row count now lives in the ARGUMENTS (eleven
// parallel arrays, unnested by Postgres into rows) instead of in the SQL, so
// the arity is fixed at eleven placeholders whatever the batch size, the whole
// statement is one literal a reader can check against DEC-2 I-4 by eye, and it
// is still exactly ONE statement — the all-or-nothing property is unchanged.
//
// `unnest` over N arrays zips them positionally, so column i of row j is
// element j of array i. The amount arrays carry EXACT DECIMAL TEXT and are cast
// to numeric by Postgres; no float exists on this path at any point.
//
// THE STATEMENT COULD NOT EXECUTE UNTIL T508, and both defects predate T503 —
// they were merely unreadable, and PostgresJournalEntryRepository still has no
// caller and no test that reaches a database, so nothing ever ran it. Both were
// re-proved against the reference oracle's own PostgreSQL 18.3 before this fix,
// not taken on report:
//
//  1. WRONG COLUMN NAMES. It named `createdby_id` / `lastmodifiedby_id`.
//     `PREPARE` on the live schema: `ERROR: column "createdby_id" of relation
//     "acc_gl_journal_entry" does not exist`. The same PREPARE of the PRE-T503
//     statement (commit 8bb0fad8) fails identically, which is what makes this
//     pre-existing rather than a T503 regression. Correct names, read from
//     information_schema: `created_by`, `last_modified_by`.
//
//  2. THREE MISSING NOT NULL COLUMNS WITH NO DEFAULT. With the names corrected
//     the statement PREPAREs clean and then fails at EXECUTE. Enumerated one at
//     a time inside rolled-back transactions, the table refuses in this order:
//     `created_on_utc`, then `last_modified_on_utc`, then `submitted_on_date`.
//     Adding the third makes the INSERT succeed, which is how the set is known
//     to be complete rather than merely longer.
//
//     COUNTED FROM `information_schema`, NOT FROM THE LIQUIBASE XML. The table
//     has THIRTEEN NOT NULL columns with no default in total; the corrected
//     statement omitted FOUR of them, and one of those four is `id`, which is
//     `GENERATED BY DEFAULT AS IDENTITY` and so is supplied by the server. Three
//     is therefore the number of columns this statement had to gain.
//
// AND TWO COLUMNS WERE DROPPED. The statement used to write CURRENT_TIMESTAMP
// into `created_date` and `lastmodified_date`. The oracle leaves both NULL on
// this table: JournalEntry extends AbstractAuditableWithUTCDateTimeCustom, whose
// only date columns are `created_on_utc` / `last_modified_on_utc`, and the
// oracle's own hand-written journal-entry INSERT
// [SavingsSchedularInterestPoster.java:164-170] does not name the legacy pair
// either. Observed, not merely read: a journal entry posted through the running
// oracle landed with created_date = NULL and lastmodified_date = NULL. Writing
// them would have made every Go-written row differ from every oracle-written row
// in a shadow-parity run, on a column carrying no information.
//
// STILL EXACTLY ONE STATEMENT, STILL AN INSERT. DEC-2 I-4 forbids UPDATE and
// DELETE against acc_gl_journal_entry; corrections are reversing entries. Nothing
// here writes a balance column either (I-3): office_running_balance and
// organization_running_balance keep their schema defaults of 0.
func (r *PostgresJournalEntryRepository) Append(entries []JournalEntry) error {
	if len(entries) == 0 {
		return nil
	}
	submittedOnDate, err := r.resolveSubmittedOnDate()
	if err != nil {
		return fmt.Errorf("ledger: append journal entries: %w", err)
	}
	// One instant for the whole batch. The oracle stamps each entity separately
	// at flush, so its two legs differ by microseconds (observed: .289487 vs
	// .294834 on one transaction) — a difference that carries no information,
	// cannot be reproduced deterministically, and no vector can pin. What the
	// capture DOES pin is that the value is UTC and that created_on_utc equals
	// last_modified_on_utc on insert; both hold here, the latter structurally,
	// because one array feeds both columns.
	auditUTC := r.auditClock().UTC().Format(auditUTCLayout)
	// A local, because the guard's argument heuristic skips a leading context
	// only when it is a bare identifier; `r.ctx` would be mistaken for the SQL
	// argument and the literal below would go unread. Named backlog item in the
	// T503 handoff — the heuristic should also skip a ctx-named selector.
	ctx := r.ctx
	args := buildJournalEntryInsertArgs(entries, r.createdByID, r.lastModifiedByID, auditUTC, submittedOnDate)
	if _, err := r.db.Exec(ctx, `INSERT INTO acc_gl_journal_entry (account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date, type_enum, amount, created_by, last_modified_by, created_on_utc, last_modified_on_utc, submitted_on_date)
		SELECT e.account_id, e.office_id, e.currency_code, e.transaction_id, e.reversed, e.manual_entry,
		       e.entry_date::date, e.type_enum, e.amount::numeric, e.created_by, e.last_modified_by,
		       e.audit_on_utc::timestamptz, e.audit_on_utc::timestamptz, e.submitted_on_date::date
		FROM unnest($1::bigint[], $2::bigint[], $3::text[], $4::text[], $5::boolean[], $6::boolean[],
		            $7::text[], $8::integer[], $9::text[], $10::bigint[], $11::bigint[],
		            $12::text[], $13::text[])
		     AS e(account_id, office_id, currency_code, transaction_id, reversed, manual_entry,
		          entry_date, type_enum, amount, created_by, last_modified_by,
		          audit_on_utc, submitted_on_date)`, args...); err != nil {
		return fmt.Errorf("ledger: append journal entries: %w", err)
	}
	return nil
}

// FindByTransactionID returns every leg of one transaction, in id order.
func (r *PostgresJournalEntryRepository) FindByTransactionID(transactionID string) ([]JournalEntry, error) {
	const sql = `
		SELECT ` + journalEntryColumns + `
		FROM acc_gl_journal_entry
		WHERE transaction_id = $1
		ORDER BY id`
	var out []JournalEntry
	err := postgres.QueryRows(r.ctx, r.db, sql, []any{transactionID}, func(s postgres.RowScanner) error {
		var e JournalEntry
		var amountText string
		if err := s.Scan(&e.ID, &e.AccountID, &e.OfficeID, &e.CurrencyCode, &e.TransactionID,
			&e.Reversed, &e.ManualEntry, &e.EntryDate, &e.Side, &amountText); err != nil {
			return err
		}
		amt, err := MinorUnitsFromDecimalText(amountText, MNTMinorDigits)
		if err != nil {
			return fmt.Errorf("ledger: journal entry %d amount %q: %w", e.ID, amountText, err)
		}
		e.Amount = amt
		out = append(out, e)
		return nil
	})
	if err != nil {
		return nil, err
	}
	return out, nil
}

// buildJournalEntryInsertArgs is a pure function so the arguments Append binds
// can be asserted without a database. It returns the THIRTEEN column arrays the
// statement in Append unnests, in placeholder order ($1..$13); every array has
// one element per entry and they are positionally aligned, so element j of each
// is column j of the row that entry j becomes.
//
// Thirteen arrays feed FOURTEEN columns: $12 (auditUTC) is selected twice, once
// into created_on_utc and once into last_modified_on_utc, because the oracle
// writes the same instant to both on insert.
//
// The amount is rendered to exact decimal text from integer minor units and
// cast to numeric by Postgres. It is never a float in Go and never a float on
// the wire.
func buildJournalEntryInsertArgs(entries []JournalEntry, createdByID, lastModifiedByID int64, auditUTC, submittedOnDate string) []any {
	n := len(entries)
	accountID := make([]int64, n)
	officeID := make([]int64, n)
	currencyCode := make([]string, n)
	transactionID := make([]string, n)
	reversed := make([]bool, n)
	manualEntry := make([]bool, n)
	entryDate := make([]string, n)
	typeEnum := make([]int32, n)
	amount := make([]string, n)
	createdBy := make([]int64, n)
	lastModifiedBy := make([]int64, n)
	auditOnUTC := make([]string, n)
	submittedOn := make([]string, n)
	for i, e := range entries {
		accountID[i] = e.AccountID
		officeID[i] = e.OfficeID
		currencyCode[i] = e.CurrencyCode
		transactionID[i] = e.TransactionID
		reversed[i] = e.Reversed
		manualEntry[i] = e.ManualEntry
		entryDate[i] = e.EntryDate
		typeEnum[i] = int32(e.Side)
		amount[i] = e.Amount.FormatDecimal(MNTMinorDigits)
		createdBy[i] = createdByID
		lastModifiedBy[i] = lastModifiedByID
		auditOnUTC[i] = auditUTC
		submittedOn[i] = submittedOnDate
	}
	return []any{
		accountID, officeID, currencyCode, transactionID, reversed, manualEntry,
		entryDate, typeEnum, amount, createdBy, lastModifiedBy,
		auditOnUTC, submittedOn,
	}
}
