package ledger

import (
	"fmt"
	"strings"
)

// Classification is acc_gl_account.classification_enum — Fineract's
// GLAccountType. [VERIFIED: GLAccountType.java:25-29 — ASSET(1), LIABILITY(2),
// EQUITY(3), INCOME(4), EXPENSE(5)]
//
// IT IS NOT THE DEBIT/CREDIT AXIS. Fineract's journal-entry column is called
// type_enum and holds CREDIT(1)/DEBIT(2) [VERIFIED: JournalEntry.java:87-88;
// JournalEntryType.java:23-24], and the GL account's column is ALSO mapped to a
// Java field called `type` [VERIFIED: GLAccount.java:73-74]. Two different axes
// wearing the same word is exactly how a port ends up posting an INCOME account
// as a credit because "type says 1". This package never uses the bare word
// "type" for either: the account carries a Classification, an entry carries an
// EntrySide, and no function converts between them.
//
// NOTHING IN SLICE A2 DERIVES A NORMAL BALANCE FROM Classification. A
// case-insensitive grep of the four A2 scope paths for debit/credit returns no
// sign convention [VERIFIED: docs/analysis/tierA-a2-behaviour.md §7, re-checked
// by this worker against the cited files]. A1 must derive the sign convention
// from JournalEntry/JournalEntryType directly, not from this type.
type Classification int32

const (
	ClassificationAsset Classification = iota
	ClassificationLiability
	ClassificationEquity
	ClassificationIncome
	ClassificationExpense
)

// classificationStoredValue is acc_gl_account.classification_enum.
// [VERIFIED: GLAccountType.java:25-29]
var classificationStoredValue = map[Classification]int32{
	ClassificationAsset:     1,
	ClassificationLiability: 2,
	ClassificationEquity:    3,
	ClassificationIncome:    4,
	ClassificationExpense:   5,
}

// classificationCode is the i18n code the oracle emits inside the
// {id, code, value} object on GET /glaccounts/{id}.
// [VERIFIED: GLAccountType.java:25-29; graded against captures
// A2-200-glaccounts-live-precheck and A2-201..A2-209b]
var classificationCode = map[Classification]string{
	ClassificationAsset:     "accountType.asset",
	ClassificationLiability: "accountType.liability",
	ClassificationEquity:    "accountType.equity",
	ClassificationIncome:    "accountType.income",
	ClassificationExpense:   "accountType.expense",
}

var classificationName = map[Classification]string{
	ClassificationAsset:     "ASSET",
	ClassificationLiability: "LIABILITY",
	ClassificationEquity:    "EQUITY",
	ClassificationIncome:    "INCOME",
	ClassificationExpense:   "EXPENSE",
}

var classificationFromStored = map[int32]Classification{}

// ClassificationMinValue and ClassificationMaxValue are the validator's range,
// computed in the oracle by a static block over values()
// [VERIFIED: GLAccountType.java:50-64 feeding GLAccountCommand.java:51-52], and
// observed as "The parameter `type` must be between 1 and 5"
// [capture A2-bad-046-type-9, A2-bad-047-type-0].
const (
	ClassificationMinValue int32 = 1
	ClassificationMaxValue int32 = 5
)

// StoredValue returns acc_gl_account.classification_enum.
func (c Classification) StoredValue() int32 {
	v, ok := classificationStoredValue[c]
	if !ok {
		panic(fmt.Sprintf("ledger: unknown Classification %d", int32(c)))
	}
	return v
}

// Code returns the i18n code emitted on the account read.
func (c Classification) Code() string { return classificationCode[c] }

// String returns the enum name, which is the `value` field of the read object
// and the word the mapping type-refusal message interpolates
// ("...maps to the account Fund Source of type INCOME...").
func (c Classification) String() string {
	if n, ok := classificationName[c]; ok {
		return n
	}
	return fmt.Sprintf("Classification(%d)", int32(c))
}

// ClassificationFromStoredValue decodes classification_enum. ok is false
// outside 1..5, matching GLAccountType.fromInt's null return
// [VERIFIED: GLAccountType.java:88-107].
func ClassificationFromStoredValue(v int32) (Classification, bool) {
	c, ok := classificationFromStored[v]
	return c, ok
}

// Usage is acc_gl_account.account_usage — Fineract's GLAccountUsage.
// [VERIFIED: GLAccountUsage.java:27-28 — DETAIL(1), HEADER(2)]
type Usage int32

const (
	UsageDetail Usage = iota
	UsageHeader
)

var usageStoredValue = map[Usage]int32{UsageDetail: 1, UsageHeader: 2}
var usageCode = map[Usage]string{
	UsageDetail: "accountUsage.detail",
	UsageHeader: "accountUsage.header",
}
var usageName = map[Usage]string{UsageDetail: "DETAIL", UsageHeader: "HEADER"}
var usageFromStored = map[int32]Usage{}

// UsageMinValue and UsageMaxValue are the validator's range
// [VERIFIED: GLAccountUsage.java:50-65 feeding GLAccountCommand.java:54-55],
// observed as "The parameter `usage` must be between 1 and 2"
// [capture A2-bad-048-usage-5].
const (
	UsageMinValue int32 = 1
	UsageMaxValue int32 = 2
)

// StoredValue returns acc_gl_account.account_usage.
func (u Usage) StoredValue() int32 {
	v, ok := usageStoredValue[u]
	if !ok {
		panic(fmt.Sprintf("ledger: unknown Usage %d", int32(u)))
	}
	return v
}

// Code returns the i18n code emitted on the account read.
func (u Usage) Code() string { return usageCode[u] }

func (u Usage) String() string {
	if n, ok := usageName[u]; ok {
		return n
	}
	return fmt.Sprintf("Usage(%d)", int32(u))
}

// UsageFromStoredValue decodes account_usage. ok is false outside 1..2,
// matching GLAccountUsage.fromInt's null return
// [VERIFIED: GLAccountUsage.java:67-70].
func UsageFromStoredValue(v int32) (Usage, bool) {
	u, ok := usageFromStored[v]
	return u, ok
}

func init() {
	for c, v := range classificationStoredValue {
		if _, dup := classificationFromStored[v]; dup {
			panic(fmt.Sprintf("ledger: classification encode table is not injective at %d", v))
		}
		classificationFromStored[v] = c
	}
	for u, v := range usageStoredValue {
		if _, dup := usageFromStored[v]; dup {
			panic(fmt.Sprintf("ledger: usage encode table is not injective at %d", v))
		}
		usageFromStored[v] = u
	}
}

// GLAccount is one row of acc_gl_account.
//
// Column widths follow the LIQUIBASE schema, not the JPA annotations, and the
// two disagree in BOTH directions: JPA says name length 45 / glCode length 100
// [VERIFIED: GLAccount.java:61-65] while Liquibase says VARCHAR(200) /
// VARCHAR(45) [VERIFIED: 0001_initial_schema.xml:53, :58] and the API validator
// agrees with Liquibase [VERIFIED: GLAccountCommand.java:43, :45-46; observed
// as "exceeds max length of 200" and "of 45" in captures A2-bad-052 and
// A2-bad-051]. Liquibase owns the schema, so the JPA lengths are dead metadata
// and a port that copied the entity annotations would truncate names at 45 and
// accept 100-character GL codes the database rejects.
type GLAccount struct {
	ID       int64
	ParentID *int64 // nullable
	// Hierarchy is the stored dot string. It is PRESENTATION ONLY: no money
	// decision anywhere reads it, there is no roll-up and no fallback to a
	// parent account [VERIFIED: it is read at exactly one site, the
	// nameDecorated SQL at GLAccountReadPlatformServiceImpl.java:49].
	Hierarchy            string
	Name                 string
	GLCode               string
	Disabled             bool
	ManualEntriesAllowed bool
	Classification       Classification
	Usage                Usage
	Description          string
	TagID                *int64 // nullable
}

// IsHeader and IsDetail mirror GLAccount.isHeaderAccount / isDetailAccount,
// which compare getValue() against the stored Integer and never ordinal()
// [VERIFIED: GLAccount.java:182-184, :199-201].
func (a GLAccount) IsHeader() bool { return a.Usage == UsageHeader }
func (a GLAccount) IsDetail() bool { return a.Usage == UsageDetail }

// GenerateHierarchy reproduces GLAccount.generateHierarchy
// [VERIFIED: GLAccount.java:186-197]:
//
//	child.hierarchy = parent.hierarchy + child.id + "."   (root: ".")
//
// State it precisely, because it is counter-intuitive: an account's OWN id
// appears in its own hierarchy string, and the ROOT's id never appears in any
// string. The oracle needs two flushes to build it, because the string embeds
// the id the database has just assigned
// [VERIFIED: GLAccountWritePlatformServiceJpaRepositoryImpl.java:96-100].
//
// Graded against capture A2-150-db-final-state.txt: id 1 (root) is ".", id 2
// (parent 1) is ".2.", id 4 (parent 3) is ".3.4.".
func (a *GLAccount) GenerateHierarchy(parent *GLAccount) {
	if parent == nil {
		a.Hierarchy = "."
		return
	}
	a.Hierarchy = fmt.Sprintf("%s%d.", parent.Hierarchy, a.ID)
}

// hierarchyDecorationRule is the 40-dot pad the oracle's SQL substrings from
// [VERIFIED: GLAccountReadPlatformServiceImpl.java:49 — a literal 40-character
// dot string]. It is reproduced as a constant rather than computed so that the
// CEILING is preserved: at depth 11 or more the oracle runs out of pad and the
// prefix stops growing.
const hierarchyDecorationRule = "........................................"

// NameDecorated reproduces the oracle's nameDecorated projection:
//
//	concat(substring('....(40 dots)....', 1,
//	       ((LENGTH(hierarchy) - LENGTH(REPLACE(hierarchy,'.','')) - 1) * 4)), name)
//
// i.e. depth = (count of '.' in hierarchy) - 1, and the name is prefixed with
// 4*depth dots [VERIFIED: GLAccountReadPlatformServiceImpl.java:49].
//
// Graded against capture A2-200-glaccounts-live-precheck for all 21 accounts,
// e.g. hierarchy "." -> "Assets", ".2." -> "....Fund Source",
// ".3.4." -> "........Loan Portfolio".
//
// Two edge behaviours are reproduced deliberately rather than "fixed":
//   - a hierarchy with zero dots yields depth -1, and SQL SUBSTRING with a
//     negative length yields the empty string, so the name is returned bare;
//   - beyond 10 levels the 40-dot pad is exhausted and the prefix saturates.
func (a GLAccount) NameDecorated() string {
	dots := strings.Count(a.Hierarchy, ".")
	width := (dots - 1) * 4
	if width <= 0 {
		return a.Name
	}
	if width > len(hierarchyDecorationRule) {
		width = len(hierarchyDecorationRule)
	}
	return hierarchyDecorationRule[:width] + a.Name
}

// PostedAccountSnapshot is the account identity a journal entry must carry WITH
// IT, captured at posting time.
//
// TRAP 3. acc_gl_journal_entry has no classification column; account_id is the
// only route to one [VERIFIED: JournalEntry.java:38-107 — the full column list
// is office_id, payment_details_id, account_id, currency_code, reversal_id,
// transaction_id, loan/savings/client/share_transaction_id, reversed,
// manual_entry, entry_date, type_enum, amount, description, entity_type_enum,
// entity_id, ref_num, submitted_on_date]. Classification is mutable on the
// account [VERIFIED: GLAccount.java:99-113, TYPE handled at :108] and the
// update path's only posted-history guard keys on USAGE, never on TYPE
// [VERIFIED: GLAccountWritePlatformServiceJpaRepositoryImpl.java:153-159; the
// identical journal-entries-exist query IS used on delete at :201-205, so it
// was available and was not applied to classification]. So in the oracle a
// posted entry re-renders under whatever classification the account carries
// TODAY — an append-only ledger displaying mutated history.
//
// This is observed, not merely derived: capture A2-111-update-retype-mapped is
// an HTTP 200 PUT retyping GL account 2 from ASSET to INCOME while five product
// mappings pointed at it, and capture A2-209b-read-gl2-retyped-fundsrc reads it
// back as INCOME. That is gate G-10.
//
// A1 owns the write path. A2 owns the account model A1 reads, so A2's job is to
// make the correct thing POSSIBLE: an entry that embeds this snapshot renders
// the same way forever. This package does not, and cannot, force A1 to use it.
type PostedAccountSnapshot struct {
	AccountID      int64
	GLCode         string
	Name           string
	Classification Classification
	Usage          Usage
}

// Snapshot captures the account identity for embedding on a posting.
func (a GLAccount) Snapshot() PostedAccountSnapshot {
	return PostedAccountSnapshot{
		AccountID:      a.ID,
		GLCode:         a.GLCode,
		Name:           a.Name,
		Classification: a.Classification,
		Usage:          a.Usage,
	}
}
