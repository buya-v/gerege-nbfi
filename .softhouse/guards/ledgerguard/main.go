// Command ledgerguard is the source-level guard that DEC-2 §4.4 requires for I-3 and I-4.
//
// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/check-ledger-invariants.sh
//
// That one line is a machine-read row, not a comment for humans, and T358 added it. It answers
// guard_guards_dir_registration in .softhouse/conformance.sh, whose population now covers Go
// and Python as well as shell at any depth under the guards directory. This file is a checker
// that the conformance harness never names: the harness calls check-ledger-invariants.sh, and
// THAT script builds and runs this module. The guard re-verifies the row every graded run — the
// witness must exist, be tracked, not be this file, and literally name "main.go" (it does, at
// check-ledger-invariants.sh:67-68) — so this is a record that rots loudly, never an amnesty.
//
// WHAT THE ROW DOES NOT DO, said here so nobody over-reads it. Deleting it does NOT turn the bar
// red for this file: conformance.sh:1484 holds a `local ccsrc="…/ledgerguard/main.go"` on a
// non-comment line — a different guard reading THIS FILE'S TEXT, not anything that runs it — and
// the registration guard's invocation test is a substring match, so main.go would silently fall
// back to "INVOKED". The row is a TRUTH improvement, recording what actually reaches this
// checker, and T358's red drive pins that fallback in an arm rather than hiding it.
//
// ⚠ CORRECTION (T227, 22 August 2026). This line read "...the source-level guard that DEC-2
// §4.4.1 records as NOT EXISTING." That was TRUE THE DAY A2-18 WROTE IT and it is FALSE NOW.
// T208 wired this guard into run_guards; DEC-2 §8.3 retracted the claim; and §4.4.1 is today
// titled "THE GUARD I-3 AND I-4 REQUIRE — IT DID NOT EXIST, IT DOES NOW, AND WHAT IT CANNOT
// SEE" [VERIFIED: docs/adr/DEC-2-gl-accounting-adapter.md:821 on main]. The sentence is not
// deleted evidence — it is a live claim in a source comment, corrected in place and labelled.
// T224 swept the repository for this retracted claim and reported the population closed; its
// terms could not match this spelling ("not existING", not "not exist"). A2-31 found it here,
// on LINE 1 of the guard whose existence refutes it. See T227's handoff for the method defect.
//
// WHAT IT ENFORCES, AND WHERE THE TARGET COMES FROM
// -------------------------------------------------
// docs/adr/DEC-2-gl-accounting-adapter.md §4.4 states two invariants that a golden vector
// provably CANNOT grade, and names the only mechanism that can. Quoting the table rows:
//
//	I-3 | Balances are DERIVED, never written | "No write path to any balance column exists
//	    | in the Go tree" ... "Gradeable only by a source-level guard over the Go tree."
//	I-4 | The ledger is append-only            | "No UPDATE/DELETE against acc_gl_journal_entry
//	    | from application code" ... "'No update ever happened' is not observable from a capture."
//
// and §4.4.1 LISTED, item by item, what nothing in the repository looked for when this program
// was written — the list it exists to answer. (Tense corrected by T227: the same retracted claim
// as line 1, one paragraph over. The four items below are unchanged and still name the targets.)
//
//   - a write path to any balance column (that is I-3);
//   - an UPDATE or DELETE statement against acc_gl_journal_entry, or any Go call that would
//     emit one (that is I-4);
//   - a derived-balance function that caches instead of deriving;
//   - a correction path that mutates a leg instead of adding a reversing pair (that is I-5).
//
// CLAUDE.md's second non-negotiable is the same rule in the project's own words: "The ledger is
// double-entry and append-only. Balances are derived, never written. Corrections are reversing
// entries. Holds are postings and alter `available` only, never posted `balance`." The last
// clause is DEC-2's I-6, and this guard implements it as its own class even though DEC-2 files
// I-6 as OUT OF THE CONTRACT DOMAIN — the guard is a guard over the Go tree, not over DEC-2's
// contract domain, and the non-negotiable is repo-wide.
//
// I-5 (corrections are reversing entries) is DELIBERATELY NOT IMPLEMENTED as its own class.
// "Mutates a leg instead of adding a reversing pair" is only decidable once a leg type and a
// correction path exist; neither does today. What IS implemented — a write to a persisted
// journal row (I-4) and a write to a balance (I-3) — is the mechanical half of I-5, and the
// rest is recorded in the CANNOT-CATCH block this program prints on every run rather than
// claimed.
//
// DETECTED WITH THE PARSER, NOT A REGEX (P-48 rule 1)
// --------------------------------------------------
// Every Go-level decision here is taken on go/parser's AST: *ast.AssignStmt and *ast.IncDecStmt
// for a write, *ast.CallExpr for a call, *ast.BasicLit for a string, *ast.FuncDecl for the
// enclosing function. A regex over Go source would fire inside comments (this file's own
// doc comment names `acc_gl_journal_entry` four times) and would mistake `a.Balance == 0` for
// an assignment. Regexes are used for ONE job only — reading the SQL text INSIDE a string
// literal the parser already isolated — because the repository has no SQL parser and inventing
// one is not this task.
//
// GUARD SHAPE (P-35) — THE PART THAT MATTERS MOST
// ------------------------------------------------
// This guard makes a NEGATIVE assertion over a walk ("there is no balance write path"), which
// is exactly the shape that passes when the walk is empty. So every population it inspects is
// COUNTED and PRINTED, and ZERO IS AN ERROR on all of: Go files, packages, function
// declarations, assignment/inc-dec statements, and string literals. A file count alone cannot
// tell a whole-tree walk from a single-directory walk, which is why the package count is gated
// too (the T166 correction on the Go side).
//
// The counts are printed on ONE `CENSUS ledger-invariants — inspected N Go files ...` line so
// that the calling shim can PARSE THE NUMBER and compare it with a floor derived by a DIFFERENT
// PROGRAM (`git ls-files`) over the same population. Testing for the PRESENCE of a CENSUS line
// is what T194 found wrong inside the P-35 machinery itself; the shim reads the value.
//
// NIL COVERAGE IS REPORTED, NOT HIDDEN. The Go tree today contains no SQL of any kind and no
// database driver (`go.mod` has no `require` block at all). So the SQL half of this guard
// inspects a non-empty population of STRING LITERALS and finds zero SQL statements in it. That
// is a real negative, not a vacuous one — but it means the SQL classes are proven only by this
// program's own selftest and not by the tree. The report says so in those words, every run.
//
// Usage:
//
//	ledgerguard --root <dir>   exit 0 clean, exit 1 and name every site otherwise
//	ledgerguard --selftest --repo <repo-root>
//	                           drive every violation class RED and the real tree GREEN (P-22, P-50)
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"go/types"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// ---------------------------------------------------------------------------------------------
// The detection surface, declared as data so a reader can audit it without reading the walk.
// ---------------------------------------------------------------------------------------------

// protectedTableRe matches, inside SQL text, any table whose name carries `journal_entry`.
// It is DERIVED rather than an exact list so that `acc_gl_journal_entry`,
// `acc_gl_journal_entry_detail` and a renamed `gl_journal_entries` are all covered. The exact
// name DEC-2 names is acc_gl_journal_entry; the others are covered by construction.
var protectedTableRe = regexp.MustCompile(`(^|[^a-z0-9_])[a-z0-9_]*journal_entr(y|ies)[a-z0-9_]*([^a-z0-9_]|$)`)

// protectedGoNameRe matches a Go identifier or type naming the journal-entry row, for the
// query-builder / ORM surface where the table name never appears as SQL text at all.
var protectedGoNameRe = regexp.MustCompile(`(?i)journalentr(y|ies)`)

// mutatingVerbRe is the set of SQL verbs that can UNMAKE a committed row.
//
// INSERT IS DELIBERATELY ABSENT, and that absence is the whole content of "append-only":
// appending to acc_gl_journal_entry is the correct and required behaviour, so an INSERT
// against it must PASS. A guard that refused INSERT would refuse the only lawful write.
var mutatingVerbRe = regexp.MustCompile(`(^|[^a-z0-9_])(update|delete|truncate|drop|alter)([^a-z0-9_]|$)`)

// upsertRe is INSERT wearing an UPDATE's coat. `ON CONFLICT ... DO UPDATE` mutates a row that
// is already committed, so it belongs with the mutating verbs and not with INSERT.
var upsertRe = regexp.MustCompile(`on conflict.*do update`)

// sqlShapedRe decides whether a string literal is SQL AT ALL. It is the denominator of the
// SQL surface: literals that are not SQL-shaped are still inspected and still counted, they
// just cannot be DML.
var sqlShapedRe = regexp.MustCompile(`(^|[^a-z0-9_])(select|insert|update|delete|truncate|merge|with|create|alter|drop)( |$)`)

// secondKeywordRe confirms that an UPDATE/DELETE-looking literal is SQL rather than English.
// It is required for NON-protected tables only. For a protected table the verb alone is
// enough, deliberately: a string that says "cannot update acc_gl_journal_entry" is
// indistinguishable from SQL without semantics, and rephrasing the message costs nothing
// while missing a real UPDATE costs the ledger. That asymmetry is a CHOICE, stated here.
var secondKeywordRe = regexp.MustCompile(`(^|[^a-z0-9_])(set|where|values|returning|using|join|from|into)([^a-z0-9_]|$)`)

var (
	reUpdate     = regexp.MustCompile(`(^|[^a-z0-9_])update +(only +)?([a-z_][a-z0-9_.$]*)`)
	reDeleteFrom = regexp.MustCompile(`(^|[^a-z0-9_])delete +from +(only +)?([a-z_][a-z0-9_.$]*)`)
	reTruncate   = regexp.MustCompile(`(^|[^a-z0-9_])truncate +(table +)?([a-z_][a-z0-9_.$]*)`)
	reInsertCols = regexp.MustCompile(`(^|[^a-z0-9_])insert +into +([a-z_][a-z0-9_.$]*) *\(([^)]*)\)`)
	reSetClause  = regexp.MustCompile(`(^|[^a-z0-9_])set +(.*)$`)
	reSetTarget  = regexp.MustCompile(`([a-z_][a-z0-9_.$]*) *=`)
	reIdent      = regexp.MustCompile(`[a-z_][a-z0-9_.$]*`)
)

// balanceNameRe is the balance-name matcher, for BOTH a Go identifier and a SQL column.
// Substring, not word-equality: `Balance`, `RunningBalance`, `closing_balance`,
// `account_balance_derived` and `balanceMinor` are all a balance, and every one of them has
// appeared in Fineract under one of those spellings.
var balanceNameRe = regexp.MustCompile(`(?i)balance`)

// balanceSynonymRe is T509's answer to the measured UNDER-match, and it is the single most
// consequential line in this file, so the argument is written out rather than assumed.
//
// THE DEFECT IT CLOSES. `ledgerguard` refused four writes in `internal/apps/loanproduct`
// spelled `outstandingLoanBalance` while shipping the IDENTICAL roll-forward GREEN in
// `internal/apps/loanschedule/emi.go:1720,:1726`, spelled `outstandingMinor` — the same
// oracle method, cited in the Go file's own comment
// [VERIFIED: emi.go:1688-1690 cites ProgressiveEMICalculator.java:1253-1255 ->
// InterestPeriod.updateOutstandingLoanBalance, InterestPeriod.java:166-186], writing a field
// whose own declaration comment at emi.go:62 reads "outstandingMinor is the balance carried
// INTO this segment". Two ports of one Fineract method, opposite verdicts, decided by the
// SPELLING of the identifier. Found by T502, confirmed in full by T505 (MAJOR-3).
//
// WHY `outstanding` AND NOT SOMETHING WIDER. It is not a guess at English: it is the word
// Fineract itself uses for the stored, derived balances this guard exists to keep out of the
// Go tree. Every one of these is a real `@Column` on a real table in the pinned oracle:
//
//	m_loan_transaction.outstanding_loan_balance_derived  [VERIFIED: LoanTransaction.java:127]
//	m_loan.principal_outstanding_derived                 [VERIFIED: LoanSummary.java:62-63]
//	m_loan_charge.amount_outstanding_derived             [VERIFIED: LoanCharge.java:108]
//
// A guard whose stated target is "a stored, written balance" and which cannot see the word
// Fineract writes those columns with is not measuring its target.
//
// THE RESIDUAL, STATED. This is a NAME test and remains one; it is wider, not sound.
// `outstanding` can appear on a non-monetary field (`outstandingRequests`) and would be
// refused — fail-CLOSED, and the fix is a bare accumulator or a non-balance name, never an
// exemption. And the general defect is untouched: a stored balance called `Position` or `Net`
// is still invisible (CANNOT-CATCH item 2). This closes one MEASURED under-match; it does not
// close the class.
var balanceSynonymRe = regexp.MustCompile(`(?i)outstanding`)

// sqlKeywordNotATableRe is item 11: SQL keywords that can stand where a table name is expected
// and must never be REPORTED as one. `INSERT ... ON CONFLICT (k) DO UPDATE SET c = ...` makes
// the token after `update` the literal keyword `set`, and this guard used to print
//
//	an UPDATE assigns the balance column "account_balance_derived" on table "set"
//
// — a nonexistent table. The verdict happened to be right, which is exactly why it survived:
// a check reading the WRONG STRING still returns an answer, and the answer is unrelated to the
// property. That is T503's B-2 shape one layer down, and it matters here because T509 adds
// table-KEYED reasoning (I3-SQL-BALANCE-TABLE below), which would have consulted "set" for
// every upsert in the tree.
var sqlKeywordNotATableRe = regexp.MustCompile(`^(set|where|from|into|values|returning|using|join|only|table|select|conflict|do|nothing)$`)

// reInsertInto is the table-only INSERT matcher. reInsertCols requires a parenthesised column
// list; an `INSERT INTO t VALUES (...)` or an `INSERT INTO t SELECT ...` has none, and an
// upsert's table must still be resolvable in both shapes.
var reInsertInto = regexp.MustCompile(`(^|[^a-z0-9_])insert +into +([a-z_][a-z0-9_.$]*)`)

// sqlParamNameRe names the parameter of a repository-local wrapper that CARRIES SQL. It is
// how the wrapper discovery in discoverSQLWrappers decides which argument to read.
var sqlParamNameRe = regexp.MustCompile(`(?i)^(sql|query|stmt|statement|ddl|dml|q)$`)

// availableNameRe carves out I-6's lawful target. CLAUDE.md: holds "alter `available` only,
// never posted `balance`".
var availableNameRe = regexp.MustCompile(`(?i)available`)

// holdFuncRe matches a function name whose CAMEL OR SNAKE SEGMENT is "hold".
// It must not match `Threshold`, and the case in the second alternative is what stops it:
// `Threshold` has a lowercase `h` preceded by a letter.
var holdFuncRe = regexp.MustCompile(`(^|[^A-Za-z])[Hh]old|[a-z0-9]Hold`)

// mutatingCallRe is the query-builder / ORM verb set: a Go method name that means "unmake a
// row". It is applied to the LAST selector of a call, plus every selector in the receiver
// chain, so `db.Model(&JournalEntry{}).Delete(ctx)` is reached.
var mutatingCallRe = regexp.MustCompile(`^(Update|Updates|UpdateAll|UpdateOne|UpdateMany|Delete|DeleteAll|DeleteOne|DeleteMany|Del|Remove|Truncate|Save|Upsert|SetColumn|Set)$`)

// mutatingExecRe is the driver-level exec family that can EMIT arbitrary SQL. Read-only
// members (Query, QueryRow, ...) are counted but never flagged: an opaque SELECT cannot
// violate I-3 or I-4.
var mutatingExecRe = regexp.MustCompile(`^(Exec|ExecContext|MustExec|MustExecContext|SendBatch|CopyFrom|Prepare|PrepareContext)$`)
var readExecRe = regexp.MustCompile(`^(Query|QueryRow|QueryContext|QueryRowContext|QueryFunc|Select|Get)$`)

// prunedDirs are never walked. `vendor` is third-party code this project does not own;
// `testdata` is deliberately NOT here — a violation planted in testdata is still in the tree.
var prunedDirs = map[string]bool{".git": true, "vendor": true, "node_modules": true}

// ---------------------------------------------------------------------------------------------

type finding struct {
	Class string
	Pos   string
	Text  string
	Why   string
}

type census struct {
	Root          string
	Files         int
	PackageDirs   []string
	Funcs         int
	HoldFuncs     int
	HoldFuncNames []string
	SQLDMLSites   []string
	SQLDMLTabled  int
	Assigns       int // AssignStmt with a non-`:=` operator, plus IncDecStmt
	WriteTargets  int
	StringLits    int
	StringGroups  int
	SQLShaped     int
	SQLDML        int
	Calls         int
	ExecFamily    int
	MutatingExec  int
	PkgVars       int
	ScanErrors    []string
	Findings      []finding

	// T509 additions. Every one of these is a population this guard now inspects and did not
	// before; each is COUNTED so that a later regression shows up as a number going to zero
	// rather than as silence (P-35 applies to a new surface exactly as to an old one).
	CompositeLits int       // struct/composite literals seen
	CompositeKeys int       // keyed elements inside them — the denominator of I3-COMPOSITE-BALANCE
	Wrappers      []wrapper // repository-local functions that CARRY SQL to the driver
	WrapperCalls  int       // calls to them
	BalanceReads  []string  // SELECTs naming a balance column: named, counted, NOT refused
}

// wrapper is a function declared IN THIS TREE that forwards a SQL string to the database.
//
// WHY THIS TYPE EXISTS (T509 item 6, found by T506 as F-6). `mutatingExecRe` names the DRIVER
// methods. It does not name `postgres.InsertReturningInt64`
// [nexus/internal/platform/postgres/insert.go:12], which takes `sql string`, forwards it to
// `QueryRows` -> `db.Query`, and executes `INSERT ... RETURNING id` at 20+ call sites across
// branch / savings / origination / collateral / parties / investor / workingcapital. Two
// consequences, and the second is the serious one:
//
//	(i) `db.Query` IS A MUTATING CALL when the statement mutates. `readExecRe`'s premise —
//	    "an opaque SELECT cannot violate I-3 or I-4" — is sound about SELECTs and unsound
//	    about the method: Postgres executes `INSERT ... RETURNING` through the same call.
//	(ii) `savings/postgres.go:210` is one of this run's live I3-SQL-BALANCE findings and it is
//	    caught BY ACCIDENT: its SQL happens to be a literal, which the BasicLit walk reads on
//	    its own. Nothing recognised the CALL as mutating. Had its author spliced a column
//	    const in — the shape `workingcapital` used and T503 was sent to remove — the finding
//	    would have vanished with NO `OPAQUE-SQL` to replace it, and the bar would have gone
//	    green while the balance column was still written on every transaction.
//
// Wrappers are DISCOVERED from the tree, not listed. A list is a document that goes stale the
// day someone adds a second wrapper; discovery is recomputed on every run.
type wrapper struct {
	Name     string // the function's own name; calls are matched on the selector's last segment
	ArgIndex int    // position of the SQL argument in a call
	Param    string // the parameter's identifier, so a pass-through inside the wrapper is not
	// mistaken for an opaque call site
	Why string // what made it a wrapper, printed in the census
}

func (c *census) add(f finding) { c.Findings = append(c.Findings, f) }

// wrapper looks a callee name up in the set discovered from this tree.
func (c *census) wrapper(name string) (wrapper, bool) {
	for _, w := range c.Wrappers {
		if w.Name == name {
			return w, true
		}
	}
	return wrapper{}, false
}

// ---------------------------------------------------------------------------------------------
// SQL text analysis. Operates on a string the PARSER already isolated as a literal.
// ---------------------------------------------------------------------------------------------

func normalizeSQL(s string) string {
	return strings.ToLower(strings.Join(strings.Fields(s), " "))
}

// isBalanceName is the one predicate every balance decision in this file goes through — Go
// identifier, SQL column and (since T509) SQL table alike. It is `balance` OR one of the
// measured synonyms; see balanceSynonymRe for why the second arm exists and what it costs.
func isBalanceName(s string) bool {
	return balanceNameRe.MatchString(s) || balanceSynonymRe.MatchString(s)
}

// stmtTable resolves the TABLE a write statement targets, and it is the item-11 repair.
//
// It exists because `reUpdate` alone is wrong on a Postgres upsert: in
// `INSERT INTO t (...) VALUES (...) ON CONFLICT (k) DO UPDATE SET c = excluded.c`
// the token following `update` is the keyword `set`, so the old extractor reported
// `on table "set"`. The upsert arm is therefore resolved from the INSERT target, which is the
// row actually being mutated, and any keyword standing where a table name was expected is
// REFUSED AS A NAME rather than passed on (`ok=false`), so no caller can key on it.
//
// Returns (table, kind, ok). kind is one of "upsert", "update", "insert", "delete",
// "truncate" — the shape that decided the answer, printed in findings so a reader can check
// the parse instead of trusting it.
func stmtTable(low string) (string, string, bool) {
	accept := func(name, kind string) (string, string, bool) {
		if name == "" || sqlKeywordNotATableRe.MatchString(name) {
			return "", kind, false
		}
		return name, kind, true
	}
	// An upsert is an INSERT whose conflict arm mutates. The row is the INSERT's row.
	if upsertRe.MatchString(low) {
		if m := reInsertInto.FindStringSubmatch(low); m != nil {
			return accept(m[2], "upsert")
		}
	}
	if m := reUpdate.FindStringSubmatch(low); m != nil {
		return accept(m[3], "update")
	}
	if m := reInsertInto.FindStringSubmatch(low); m != nil {
		return accept(m[2], "insert")
	}
	if m := reDeleteFrom.FindStringSubmatch(low); m != nil {
		return accept(m[3], "delete")
	}
	if m := reTruncate.FindStringSubmatch(low); m != nil {
		return accept(m[3], "truncate")
	}
	return "", "", false
}

func setColumns(low string) []string {
	m := reSetClause.FindStringSubmatch(low)
	if m == nil {
		return nil
	}
	clause := m[2]
	for _, cut := range []string{" where ", " returning ", " from "} {
		if i := strings.Index(clause, cut); i >= 0 {
			clause = clause[:i]
		}
	}
	var out []string
	for _, mm := range reSetTarget.FindAllStringSubmatch(clause, -1) {
		out = append(out, mm[1])
	}
	return out
}

func splitCols(s string) []string {
	var out []string
	for _, p := range strings.Split(s, ",") {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

// analyseSQL classifies one string-literal group. `raw` is the decoded literal text, `pos` its
// position, `where` a human label for the enclosing function.
func (c *census) analyseSQL(raw, pos, where string) {
	low := normalizeSQL(raw)
	if !sqlShapedRe.MatchString(low) {
		return
	}
	c.SQLShaped++

	protected := protectedTableRe.MatchString(low)
	mutating := mutatingVerbRe.MatchString(low) || upsertRe.MatchString(low)
	if mutating || reInsertCols.MatchString(low) {
		c.SQLDML++
		// SQLDML IS AN UPPER BOUND AND MUST NOT BE READ AS "N REAL STATEMENTS EXIST".
		// English prose satisfies it: measured on nexus/ at this commit, all three
		// DML-classified literals are message text ("... NOT settable on update",
		// "DUPLICATE case_id ... update"). SQLDMLTabled is the narrow count — a DML verb from
		// which an actual TABLE NAME could be extracted — and it is what the NIL-COVERAGE
		// notice keys on, so a tree of prose can never look like a tree of SQL.
		if reUpdate.MatchString(low) || reDeleteFrom.MatchString(low) ||
			reTruncate.MatchString(low) || reInsertCols.MatchString(low) {
			c.SQLDMLTabled++
		}
		// NAMED, NOT JUST COUNTED. A DML count a reader cannot resolve to a site is a number
		// nobody can audit; every DML-classified literal is printed with its position so the
		// classifier's own false positives are visible rather than hidden inside a total.
		c.SQLDMLSites = append(c.SQLDMLSites, pos+"  "+short(raw))
	}

	// I-4. The ledger is append-only.
	if protected && mutating {
		c.add(finding{
			Class: "I4-DML",
			Pos:   pos,
			Text:  short(raw),
			Why: "an UPDATE/DELETE/TRUNCATE/DROP/ALTER (or an ON CONFLICT DO UPDATE) naming a " +
				"journal-entry table" + where + ". DEC-2 §4.4 I-4: the ledger is append-only — " +
				"\"No UPDATE/DELETE against acc_gl_journal_entry from application code\". " +
				"Corrections are REVERSING ENTRIES: append a new balanced pair, never unmake a " +
				"committed row. INSERT against this table is lawful and is not flagged.",
		})
	}

	confirmed := secondKeywordRe.MatchString(low)

	table, kind, tableOK := stmtTable(low)
	writes := mutating || reInsertInto.MatchString(low)

	// I-3, T509's TABLE arm. A write to a table whose NAME is a balance is a write to a stored
	// balance whatever its columns are called.
	//
	// THE MEASURED CASE. `nexus/internal/apps/workingcapital/postgres.go:379` upserts
	// `m_wc_loan_balance` — a stored, per-loan balance row — and this guard shipped it GREEN
	// because `balanceNameRe` was applied to `splitCols(m[3])` (the COLUMN list) and to
	// `setColumns(low)`, and NONE of the thirteen columns carries the string `balance`
	// (`principal`, `principal_paid`, `principal_adjustment`, `fee`, `fee_paid`, `penalty`,
	// `penalty_paid`, …). The TABLE NAME carries it. Found by T503 (B-2), mechanism
	// demonstrated by T506 (F-7) with a probe: adding a column literally named
	// `closing_balance` to that same statement made the guard fire instantly, while the
	// thirteen real columns never could. A check that looks at the wrong string still returns
	// an answer.
	//
	// READS ARE NOT REFUSED HERE — see the balance-read census below. Only a statement that
	// WRITES the row (insert / update / upsert / delete / truncate) reaches this arm.
	if writes && tableOK && isBalanceName(table) {
		c.add(finding{
			Class: "I3-SQL-BALANCE-TABLE",
			Pos:   pos,
			Text:  short(raw),
			Why: "a " + kind + " writes table " + strconv.Quote(table) + ", whose NAME is a balance" +
				where + ". CLAUDE.md non-negotiable: \"Balances are derived, never written.\" " +
				"A per-account row in a table called `..._balance` is a stored balance however its " +
				"columns are spelled — this is the m_trial_balance shape DEC-2 §4.4 I-3 names and §7 " +
				"refuses to port. Derive it by summation over the postings, or record the exemption " +
				"in DEC-2 (a `user` gate) rather than renaming the table.",
		})
	}

	// I-3, persistence half: an UPDATE (or an upsert's DO UPDATE) that assigns a balance
	// column, on ANY table. The table name comes from stmtTable, not from reUpdate's third
	// group — item 11: on an upsert that group is the keyword `set`.
	if (kind == "update" || kind == "upsert") && confirmed {
		named := strconv.Quote(table)
		if !tableOK {
			named = "an UNRESOLVED table (this guard could not parse a table name out of the " +
				"statement, and says so rather than printing the keyword it found there)"
		}
		for _, col := range setColumns(low) {
			if isBalanceName(col) {
				c.add(finding{
					Class: "I3-SQL-BALANCE",
					Pos:   pos,
					Text:  short(raw),
					Why: "an " + strings.ToUpper(kind) + " assigns the balance column " +
						strconv.Quote(col) + " on table " + named + where + ". CLAUDE.md " +
						"non-negotiable: \"Balances are derived, never written.\" Derive it by " +
						"summation over the postings.",
				})
			}
		}
	}
	// I-3, the m_trial_balance shape: a balance column POPULATED AT INSERT. DEC-2 §4.4 I-3
	// names this precisely — closing_balance is "a written, stored, UNSIGNED sum wearing a
	// balance's name", populated at INSERT, and is deliberately not ported (§7).
	if m := reInsertCols.FindStringSubmatch(low); m != nil {
		for _, col := range splitCols(m[3]) {
			if isBalanceName(col) {
				c.add(finding{
					Class: "I3-SQL-BALANCE",
					Pos:   pos,
					Text:  short(raw),
					Why: "an INSERT populates the balance column " + strconv.Quote(col) + " on table " +
						strconv.Quote(m[2]) + where + ". This is the m_trial_balance shape DEC-2 §4.4 " +
						"I-3 names and §7 refuses to port: a written, stored sum wearing a balance's " +
						"name. A stored balance is still a written balance.",
				})
			}
		}
	}
	// THE BALANCE-READ CENSUS (T509 item 8). NAMED, COUNTED, AND DELIBERATELY NOT REFUSED.
	//
	// T510 measured that I3-SQL-BALANCE fires only on a WRITE, never on a SELECT of a balance
	// column, and filed it as a blind spot. It is a real gap in coverage and it is now VISIBLE,
	// but it is not converted into a refusal, and the reason is a boundary this guard must not
	// cross on its own: DEC-2 §4.4 I-3's gradeable text is "No WRITE PATH to any balance column
	// exists in the Go tree." A SELECT is not a write path. Raising a read to a refusal is a
	// change to a ratified DEC-n, which CLAUDE.md routes as a `user` gate — not something a
	// guard patch may smuggle in.
	//
	// WHY IT IS STILL WORTH PRINTING, AND WHY THIS IS NOT AN AMNESTY. T501's ratified reasoning
	// is that "a decoded balance is a number this port did not derive, arriving through the
	// SELECT instead of the INSERT, and landing in a field callers then treat as authoritative."
	// That is where a real defect entered this tree. So every read of a balance-named column is
	// enumerated with its position on every run, pass or fail. Nothing that was refused before
	// is refused less; this only adds sight. The direction is stated so nobody quotes the census
	// as coverage: a listed site has been SEEN, not cleared.
	if !writes && strings.Contains(low, "select") {
		seg := low
		if i := strings.Index(seg, " from "); i > 0 {
			seg = seg[:i]
		}
		for _, id := range reIdent.FindAllString(seg, -1) {
			if isBalanceName(id) && !sqlKeywordNotATableRe.MatchString(id) {
				c.BalanceReads = append(c.BalanceReads, pos+"  "+id+"  "+short(raw))
				break
			}
		}
	}

	// A DELETE/TRUNCATE against a non-protected table is not this guard's business; it is
	// counted as DML and left alone. Say nothing you cannot justify.
	_ = reDeleteFrom
	_ = reTruncate
}

func short(s string) string {
	s = strings.Join(strings.Fields(s), " ")
	if len(s) > 140 {
		return s[:137] + "..."
	}
	return s
}

// ---------------------------------------------------------------------------------------------
// Go AST analysis.
// ---------------------------------------------------------------------------------------------

// writeTarget resolves the name being WRITTEN by an assignment LHS.
//
// THE DISTINCTION THAT KEEPS THIS GUARD FROM REFUSING THE CORRECT IMPLEMENTATION:
// a bare identifier is a local or a package variable, and `balance += leg.Amount` inside a
// summation loop is EXACTLY HOW A DERIVED BALANCE IS WRITTEN. Flagging it would refuse the
// only correct implementation. So a bare identifier at the top of the LHS is NOT a target.
// A FIELD (`x.Balance = ...`), a DEREFERENCE (`*bal = ...`) and an INDEX (`balances[id] = ...`)
// ARE targets, because each of them stores into something that outlives the expression.
//
// The residual, stated rather than hidden: a local struct used as an accumulator
// (`var acc struct{ Balance int64 }; acc.Balance += x`) is flagged. That is fail-CLOSED, and
// the fix is a bare accumulator, which is what the ported package already uses
// (nexus/internal/apps/ledger/money.go DoubleEntryBalances sums into `debit, credit`).
func writeTarget(e ast.Expr, indirect bool) (string, string, bool) {
	switch t := e.(type) {
	case *ast.ParenExpr:
		return writeTarget(t.X, indirect)
	case *ast.SelectorExpr:
		return t.Sel.Name, "field", true
	case *ast.StarExpr:
		return writeTarget(t.X, true)
	case *ast.IndexExpr:
		return writeTarget(t.X, true)
	case *ast.Ident:
		if indirect {
			return t.Name, "indirect", true
		}
		return "", "", false
	}
	return "", "", false
}

// concatLiterals flattens a `+` chain of string literals into one text, reporting whether any
// operand was NOT a literal. `"UPDATE " + table + " SET x=1"` yields the literal halves and
// opaque=true, which is what makes a builder-assembled statement visible as a blind spot
// instead of invisible.
func concatLiterals(e ast.Expr, lits *[]*ast.BasicLit, opaque *bool) string {
	switch t := e.(type) {
	case *ast.ParenExpr:
		return concatLiterals(t.X, lits, opaque)
	case *ast.BasicLit:
		if t.Kind != token.STRING {
			*opaque = true
			return ""
		}
		v, err := strconv.Unquote(t.Value)
		if err != nil {
			*opaque = true
			return ""
		}
		*lits = append(*lits, t)
		return v
	case *ast.BinaryExpr:
		if t.Op != token.ADD {
			*opaque = true
			return ""
		}
		return concatLiterals(t.X, lits, opaque) + concatLiterals(t.Y, lits, opaque)
	}
	*opaque = true
	return ""
}

// isPureStringLiteral reports whether an expression is entirely string literals joined by `+`.
func isPureStringLiteral(e ast.Expr) bool {
	var lits []*ast.BasicLit
	opaque := false
	concatLiterals(e, &lits, &opaque)
	return !opaque && len(lits) > 0
}

// readableVerbIsSelect reports whether the part of `e` this guard CAN read is a SELECT and
// carries no mutating verb anywhere in it.
//
// WHERE THIS IS USED AND WHY IT IS NOT A WEAKENING. It gates the wrapper arm only (T509 item
// 6). Before T509, a call to `postgres.QueryRows` or `postgres.InsertReturningInt64` was not
// inspected at all: the guard reached the database through `readExecRe`, which decides a call
// is read-only FROM THE METHOD NAME. Reading the statement's own leading verb out of the
// literal halves is STRICTLY STRONGER EVIDENCE than trusting a method name — `Query` executes
// `INSERT ... RETURNING` perfectly well, which is precisely how `InsertReturningInt64` writes
// rows — so a wrapper call whose readable text is a bare SELECT is held to a higher standard
// here than the driver call it forwards to, not a lower one.
//
// A call that fails this test is REFUSED as OPAQUE-SQL. That includes the case that matters:
// `INSERT INTO m_wc_loan (..., ` + wcProductDetailColumns + `) VALUES ...` at
// nexus/internal/apps/workingcapital/postgres.go:168 — an INSERT with a spliced, unreadable
// column list, routed through the wrapper, invisible to this guard until now.
func readableVerbIsSelect(e ast.Expr) bool {
	var lits []*ast.BasicLit
	opaque := false
	text := normalizeSQL(concatLiterals(e, &lits, &opaque))
	if len(lits) == 0 || text == "" {
		return false
	}
	if !strings.HasPrefix(text, "select") {
		return false
	}
	return !mutatingVerbRe.MatchString(text) && !upsertRe.MatchString(text) &&
		!reInsertInto.MatchString(text)
}

// calleeChain collects every selector name from a call's function expression, outermost last,
// plus every identifier and string literal reachable in the receiver chain. This is what makes
// `db.Model(&JournalEntry{}).Delete(ctx)` decidable without a type checker.
func calleeName(fun ast.Expr) string {
	switch t := fun.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.SelectorExpr:
		return t.Sel.Name
	case *ast.ParenExpr:
		return calleeName(t.X)
	case *ast.IndexExpr:
		return calleeName(t.X)
	}
	return ""
}

// mentionsProtected reports whether any identifier or string literal anywhere under `n` names
// the journal-entry row, by Go name or by SQL table name.
func mentionsProtected(n ast.Node) (string, bool) {
	hit := ""
	ast.Inspect(n, func(x ast.Node) bool {
		if hit != "" {
			return false
		}
		switch t := x.(type) {
		case *ast.Ident:
			if protectedGoNameRe.MatchString(t.Name) {
				hit = t.Name
			}
		case *ast.BasicLit:
			if t.Kind == token.STRING {
				if v, err := strconv.Unquote(t.Value); err == nil {
					if protectedTableRe.MatchString(strings.ToLower(v)) || protectedGoNameRe.MatchString(v) {
						hit = v
					}
				}
			}
		}
		return true
	})
	return hit, hit != ""
}

// sqlArgOf picks the argument of an exec-family call that carries the SQL, skipping a leading
// context. It is a heuristic and is used ONLY to decide whether the SQL is readable, never to
// decide that it is clean.
func sqlArgOf(call *ast.CallExpr) (ast.Expr, bool) {
	if len(call.Args) == 0 {
		return nil, false
	}
	first := call.Args[0]
	if id, ok := first.(*ast.Ident); ok && strings.Contains(strings.ToLower(id.Name), "ctx") {
		if len(call.Args) < 2 {
			return nil, false
		}
		return call.Args[1], true
	}
	// T509 item 7, from T503's B-1 — AND ITS DIRECTION STATED CORRECTLY, which is why this
	// comment is longer than the code.
	//
	// A repository that captures its context as a field and calls `db.Exec(r.ctx, <literal>, …)`
	// — an ordinary shape in this tree — used to be classed OPAQUE-SQL even though its SQL is a
	// plain literal, because only a bare `*ast.Ident` containing "ctx" or a selector named
	// `Background` was skipped. Widening the skip lets the classifier READ those statements.
	//
	// T503's handoff called this "fail-CLOSED in the right direction". IT IS NOT, and T506's F-5
	// is right: it is refusal-REDUCING. OPAQUE-SQL is a refusal-to-certify class, not a
	// detection class, so widening what counts as readable can only ever REMOVE refusals. The
	// justification is not "fail-closed" — it is "it removes a MEASURED FALSE POSITIVE over
	// statements the classifier was already reading, and every statement it makes readable is
	// then put through the full I-3/I-4 analysis rather than waved past." That is true and it is
	// sufficient. Recording it as fail-closed would have been the sentence a later reviewer
	// waved it through on, so it is recorded as what it is. Both polarities are pinned in the
	// selftest — case (h2) proves a literal behind a field context is READ, and case (h) proves
	// genuinely assembled SQL is still REFUSED.
	if sel, ok := first.(*ast.SelectorExpr); ok &&
		(sel.Sel.Name == "Background" || strings.Contains(strings.ToLower(sel.Sel.Name), "ctx")) {
		if len(call.Args) < 2 {
			return nil, false
		}
		return call.Args[1], true
	}
	return first, true
}

// ---------------------------------------------------------------------------------------------

// parsedFile is one Go file already turned into an AST. The walk parses EVERY file before
// ANY file is analysed, because wrapper discovery (see discoverSQLWrappers) is a whole-tree
// question: `postgres.InsertReturningInt64` is declared in one package and called from seven
// others, and a file-at-a-time walk can only ever see one of those two facts.
type parsedFile struct {
	path string
	rel  string
	file *ast.File
}

// discoverSQLWrappers finds every function in the tree that forwards a SQL string to the
// database, transitively, to a fixpoint.
//
// THE RULE, and it is deliberately narrow so that it names things rather than guessing:
// a function is a wrapper when it has a `string` parameter whose NAME is one of sql / query /
// stmt / statement / ddl / dml / q, AND its body calls either a driver method this guard
// already names (Exec / ExecContext / Query / QueryRow / …) or a wrapper already discovered.
// The fixpoint is what reaches `InsertReturningInt64` -> `QueryRows` -> `db.Query`.
//
// DIRECTION. This arm can only ADD call sites the guard inspects; it removes none. A call to a
// wrapper whose SQL argument is not a readable literal becomes OPAQUE-SQL, exactly as a call to
// `Exec` would — so the wrapper stops being a way around the check rather than becoming one.
//
// WHAT IT STILL CANNOT SEE, said here and repeated in CANNOT-CATCH: matching is by the callee's
// last selector segment, so two functions of the same name in different packages are one name
// to this guard; and a wrapper that takes its SQL under some other parameter name, or builds it
// internally from a struct field, is not discovered.
func discoverSQLWrappers(files []parsedFile) []wrapper {
	known := map[string]wrapper{}
	for {
		added := false
		for _, pf := range files {
			for _, d := range pf.file.Decls {
				fd, ok := d.(*ast.FuncDecl)
				if !ok || fd.Body == nil || fd.Type.Params == nil {
					continue
				}
				if _, seen := known[fd.Name.Name]; seen {
					continue
				}
				idx, param := -1, ""
				n := 0
				for _, fld := range fd.Type.Params.List {
					isString := false
					if id, ok := fld.Type.(*ast.Ident); ok && id.Name == "string" {
						isString = true
					}
					if len(fld.Names) == 0 {
						n++
						continue
					}
					for _, nm := range fld.Names {
						if isString && idx < 0 && sqlParamNameRe.MatchString(nm.Name) {
							idx, param = n, nm.Name
						}
						n++
					}
				}
				if idx < 0 {
					continue
				}
				why := ""
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					if why != "" {
						return false
					}
					call, ok := x.(*ast.CallExpr)
					if !ok {
						return true
					}
					callee := calleeName(call.Fun)
					if mutatingExecRe.MatchString(callee) || readExecRe.MatchString(callee) {
						why = "takes " + param + " string and calls the driver method " + callee + "()"
					} else if _, ok := known[callee]; ok {
						why = "takes " + param + " string and calls the wrapper " + callee + "()"
					}
					return true
				})
				if why == "" {
					continue
				}
				known[fd.Name.Name] = wrapper{Name: fd.Name.Name, ArgIndex: idx, Param: param, Why: why}
				added = true
			}
		}
		if !added {
			break
		}
	}
	out := make([]wrapper, 0, len(known))
	for _, w := range known {
		out = append(out, w)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

func (c *census) scanFile(fset *token.FileSet, pf parsedFile) {
	path, rel, f := pf.path, pf.rel, pf.file
	_ = path
	pos := func(p token.Pos) string {
		q := fset.Position(p)
		return fmt.Sprintf("%s:%d:%d", rel, q.Line, q.Column)
	}

	// Package-level mutable state whose name is a balance. A package-level balance is a
	// STORE, and it is a store whichever function writes it.
	for _, d := range f.Decls {
		gd, ok := d.(*ast.GenDecl)
		if !ok || gd.Tok != token.VAR {
			continue
		}
		for _, spec := range gd.Specs {
			vs, ok := spec.(*ast.ValueSpec)
			if !ok {
				continue
			}
			for _, name := range vs.Names {
				c.PkgVars++
				if isBalanceName(name.Name) {
					c.add(finding{
						Class: "I3-PKG-STATE",
						Pos:   pos(name.Pos()),
						Text:  "var " + name.Name,
						Why: "a package-level mutable variable whose name is a balance. That is a " +
							"balance STORE, and CLAUDE.md's non-negotiable is that balances are derived, " +
							"never written — a store exists to be written. Derive it per call from the " +
							"postings, or make it a const.",
					})
				}
			}
		}
	}

	// STRING CONSTANTS DECLARED IN THIS FILE, so that `const sql = "SELECT …"` followed by
	// `QueryRows(ctx, db, sql, …)` is READ rather than refused as unreadable. The guard already
	// analysed that literal — it walks every BasicLit — it simply could not connect the two,
	// and refusing there says "I cannot read this" about a statement printed in full three
	// lines above. Measured on nexus/: two sites, both plain SELECTs
	// (ledger/journalentry_postgres.go:99, ledger/closure.go:73).
	//
	// DIRECTION, STATED (same family as the sqlArgOf widening, same reasoning): this is
	// refusal-REDUCING, not fail-closed. It is justified because it removes a MEASURED false
	// refusal over text the classifier had already read in full, and every statement it makes
	// readable is then put through the whole I-3/I-4 analysis. CONST ONLY — never `var` — since
	// a const cannot be reassigned between its declaration and the call, and a var can. Scope is
	// this FILE; a const declared in a sibling file of the same package does not resolve, and
	// that residual is fail-CLOSED (it refuses).
	strConsts := map[string]ast.Expr{}
	ast.Inspect(f, func(n ast.Node) bool {
		gd, ok := n.(*ast.GenDecl)
		if !ok || gd.Tok != token.CONST {
			return true
		}
		for _, spec := range gd.Specs {
			vs, ok := spec.(*ast.ValueSpec)
			if !ok || len(vs.Names) != 1 || len(vs.Values) != 1 {
				continue
			}
			if isPureStringLiteral(vs.Values[0]) || readableVerbIsSelect(vs.Values[0]) {
				strConsts[vs.Names[0].Name] = vs.Values[0]
			}
		}
		return true
	})
	resolveConst := func(e ast.Expr) ast.Expr {
		if id, ok := e.(*ast.Ident); ok {
			if v, ok := strConsts[id.Name]; ok {
				return v
			}
		}
		return e
	}

	// Every construct below is attributed to its enclosing top-level declaration, so that I-6
	// can ask "is this write inside a hold?".
	consumed := map[*ast.BasicLit]bool{}

	var enclosing string
	var enclosingSQLParam string
	inspect := func(n ast.Node) bool {
		switch t := n.(type) {

		case *ast.UnaryExpr:
			// I3-COMPOSITE-BALANCE (T509 item 3). `&T{Balance: v}` ALLOCATES an object that
			// outlives the expression and initialises a balance-named field in it. That is the
			// same act as `p := &T{}; p.Balance = v`, which this guard already refuses — and
			// until now the two forms got opposite verdicts.
			//
			// THE MEASURED HOLE. `writeTarget` is applied only to *ast.AssignStmt and
			// *ast.IncDecStmt, so an *ast.KeyValueExpr inside a composite literal was invisible.
			// T502 found six such writes to the two fields this guard refuses IN THE SAME
			// PACKAGE — one of them four lines from a refused site — and T505 confirmed the
			// count exactly (interestperiod.go:281,282,306,307; repaymentperiod.go:96,97 on
			// main). The guard's objection was to the STATEMENT FORM, not to the act. Worse,
			// CANNOT-CATCH item 8 told a tripped author "the fix is a constructor, not an
			// exemption" — advice that pointed straight at this hole. Item 8 is corrected below.
			//
			// WHY `&` AND NOT EVERY COMPOSITE LITERAL, WHICH IS THE WHOLE DESIGN. The line is
			// writeTarget's own doctrine, applied unchanged: a bare identifier is not a target
			// because a local accumulator IS the derivation; a field, a dereference and an index
			// ARE, because each stores into something that outlives the expression. `&T{...}`
			// allocates exactly such a thing. A plain `T{Balance: Derive(legs)}` returned from a
			// presenter is a VALUE IN FLIGHT — the shape selftest case (k) requires to stay
			// green, and refusing it would refuse the only way to render a derived balance.
			//
			// THE RESIDUAL, STATED, because this is a name test wearing a shape test's coat:
			// `v := T{Balance: x}; store.p = &v` and `store.rows = append(store.rows,
			// T{Balance: x})` are stores this arm does not reach. It closes the MEASURED hole
			// and the advice that recommended it; it does not close the class. Following a
			// value into a store needs go/types — see CANNOT-CATCH item 10.
			if t.Op != token.AND {
				return true
			}
			cl, ok := t.X.(*ast.CompositeLit)
			if !ok {
				return true
			}
			for _, elt := range cl.Elts {
				kv, ok := elt.(*ast.KeyValueExpr)
				if !ok {
					continue
				}
				key, ok := kv.Key.(*ast.Ident)
				if !ok || !isBalanceName(key.Name) {
					continue
				}
				c.add(finding{
					Class: "I3-COMPOSITE-BALANCE",
					Pos:   pos(kv.Pos()),
					Text:  "&" + types.ExprString(cl.Type) + "{" + key.Name + ": " + short(types.ExprString(kv.Value)) + "}",
					Why: "a balance-named field is written by a COMPOSITE LITERAL that is then " +
						"ALLOCATED (`&T{...}`)" + inFunc(enclosing) + ". This is the same act as " +
						"`p := &T{}; p." + key.Name + " = ...`, which this guard refuses as " +
						"I3-FIELD-WRITE — it was invisible only because writeTarget is applied to " +
						"assignments and not to composite-literal keys. CLAUDE.md non-negotiable: " +
						"\"Balances are derived, never written.\" Derive by summation over the " +
						"postings. NOTE: moving the write into a constructor does NOT clear this, " +
						"and CANNOT-CATCH item 8 no longer recommends it.",
				})
			}

		case *ast.CompositeLit:
			// COUNTED, so the new class's denominator is visible and P-35 applies to it too:
			// a run reporting zero composite literals over a real Go tree has not inspected
			// them, and the gate in report() says so.
			c.CompositeLits++
			for _, elt := range t.Elts {
				if _, ok := elt.(*ast.KeyValueExpr); ok {
					c.CompositeKeys++
				}
			}

		case *ast.AssignStmt:
			if t.Tok == token.DEFINE {
				return true // `:=` declares; it cannot write to anything that already exists.
			}
			c.Assigns++
			for _, lhs := range t.Lhs {
				name, kind, ok := writeTarget(lhs, false)
				if !ok {
					continue
				}
				c.WriteTargets++
				c.checkBalanceWrite(name, kind, types.ExprString(lhs)+" "+t.Tok.String(), pos(lhs.Pos()), enclosing)
			}

		case *ast.IncDecStmt:
			c.Assigns++
			name, kind, ok := writeTarget(t.X, false)
			if ok {
				c.WriteTargets++
				c.checkBalanceWrite(name, kind, types.ExprString(t.X)+t.Tok.String(), pos(t.X.Pos()), enclosing)
			}

		case *ast.BinaryExpr:
			if t.Op != token.ADD {
				return true
			}
			var lits []*ast.BasicLit
			opaque := false
			text := concatLiterals(t, &lits, &opaque)
			if len(lits) == 0 {
				return true
			}
			for _, l := range lits {
				if consumed[l] {
					return true // already folded into an outer group
				}
			}
			for _, l := range lits {
				consumed[l] = true
			}
			c.StringGroups++
			c.analyseSQL(text, pos(t.Pos()), inFunc(enclosing))

		case *ast.CallExpr:
			c.Calls++
			name := calleeName(t.Fun)

			if mutatingExecRe.MatchString(name) || readExecRe.MatchString(name) {
				c.ExecFamily++
			}
			if mutatingExecRe.MatchString(name) {
				c.MutatingExec++
				arg, have := sqlArgOf(t)
				if have {
					// Same const resolution as the wrapper arm below, for the same reason and
					// with the same stated direction. `const s = "INSERT …"; db.Exec(ctx, s)`
					// is a statement this guard has already read in full; refusing it says "I
					// cannot read this" about text printed three lines above the call.
					arg = resolveConst(arg)
				}
				readable := have && isPureStringLiteral(arg)
				if name == "SendBatch" || name == "CopyFrom" {
					readable = false
				}
				if !readable {
					c.add(finding{
						Class: "OPAQUE-SQL",
						Pos:   pos(t.Pos()),
						Text:  types.ExprString(t.Fun) + "(...)",
						Why: "a mutating driver call whose SQL this guard CANNOT READ — it is assembled " +
							"at run time, or it is a batch/copy call carrying no SQL string. The guard " +
							"therefore cannot certify that it is not an UPDATE or DELETE against " +
							"acc_gl_journal_entry (I-4) or a write to a balance column (I-3). An " +
							"unreadable statement is refused rather than assumed clean: build the SQL as " +
							"a string literal, or state the exemption in DEC-2 and amend this guard.",
					})
				}
			}

			// T509 item 6 — the repository's OWN mutating wrappers, discovered from the tree.
			if w, ok := c.wrapper(name); ok {
				c.ExecFamily++
				c.WrapperCalls++
				var arg ast.Expr
				if w.ArgIndex < len(t.Args) {
					arg = resolveConst(t.Args[w.ArgIndex])
				}
				readable := arg != nil && (isPureStringLiteral(arg) || readableVerbIsSelect(arg))
				// PASS-THROUGH IS NOT OPACITY. Inside the wrapper itself the SQL argument IS
				// the wrapper's own `sql` parameter — `QueryRows(ctx, db, sql, ...)` in
				// InsertReturningInt64. Refusing there would refuse every wrapper for being a
				// wrapper, and would say nothing about any caller. The CALL SITES are what
				// carry the statement, and they are checked.
				if !readable && arg != nil && enclosingSQLParam != "" {
					if id, ok := arg.(*ast.Ident); ok && id.Name == enclosingSQLParam {
						readable = true
					}
				}
				if !readable {
					c.add(finding{
						Class: "OPAQUE-SQL",
						Pos:   pos(t.Pos()),
						Text:  types.ExprString(t.Fun) + "(...) [wrapper: " + w.Why + "]",
						Why: "a call to " + strconv.Quote(w.Name) + ", a function IN THIS TREE that " +
							"forwards a SQL string to the database (" + w.Why + "), whose SQL this " +
							"guard CANNOT READ. `mutatingExecRe` names the DRIVER methods only, so " +
							"routing a statement through a local wrapper used to make it invisible: " +
							"no OPAQUE-SQL, because the call name is unrecognised, and no literal to " +
							"read. A statement the guard cannot read cannot be certified free of an " +
							"UPDATE/DELETE against acc_gl_journal_entry (I-4) or a write to a balance " +
							"column (I-3). Build the SQL as a string literal at the call site.",
					})
				}
			}

			if mutatingCallRe.MatchString(name) {
				if hit, ok := mentionsProtected(t); ok {
					c.add(finding{
						Class: "I4-BUILDER",
						Pos:   pos(t.Pos()),
						Text:  types.ExprString(t.Fun) + "(...) -> " + short(hit),
						Why: "a query-builder/ORM call whose verb unmakes a row, naming the journal-entry " +
							"row. DEC-2 §4.4.1 asks for \"an UPDATE or DELETE statement against " +
							"acc_gl_journal_entry, OR ANY GO CALL THAT WOULD EMIT ONE\". This is the " +
							"second form. Corrections are reversing entries.",
					})
				}
			}
		}
		return true
	}

	// Pass 1: function bodies, so `enclosing` is set.
	for _, d := range f.Decls {
		fd, ok := d.(*ast.FuncDecl)
		if !ok {
			continue
		}
		c.Funcs++
		enclosing = fd.Name.Name
		enclosingSQLParam = ""
		if w, ok := c.wrapper(fd.Name.Name); ok {
			enclosingSQLParam = w.Param
		}
		if holdFuncRe.MatchString(enclosing) {
			c.HoldFuncs++
			c.HoldFuncNames = append(c.HoldFuncNames, pos(fd.Pos())+"  "+enclosing)
		}
		ast.Inspect(fd, inspect)
	}
	// Pass 2: everything outside a function body (package-level var initialisers, consts).
	enclosing = ""
	enclosingSQLParam = ""
	for _, d := range f.Decls {
		if _, ok := d.(*ast.FuncDecl); ok {
			continue
		}
		ast.Inspect(d, inspect)
	}

	// Pass 3: the string-literal COUNT and the singleton groups. Counted over the whole file
	// with go/ast, so it is the denominator of the SQL surface and can never be zero on a tree
	// that has string literals in it.
	ast.Inspect(f, func(n ast.Node) bool {
		bl, ok := n.(*ast.BasicLit)
		if !ok || bl.Kind != token.STRING {
			return true
		}
		c.StringLits++
		if consumed[bl] {
			return true
		}
		v, err := strconv.Unquote(bl.Value)
		if err != nil {
			return true
		}
		c.StringGroups++
		c.analyseSQL(v, pos(bl.Pos()), "")
		return true
	})
}

func inFunc(name string) string {
	if name == "" {
		return ""
	}
	return " in func " + name
}

func (c *census) checkBalanceWrite(name, kind, rendered, pos, enclosing string) {
	if !isBalanceName(name) {
		// I-6 also fires on a non-balance-named target only if it is a POSTED amount; there
		// is no such spelling to key on, so nothing is claimed here. See CANNOT-CATCH.
		return
	}
	c.add(finding{
		Class: "I3-FIELD-WRITE",
		Pos:   pos,
		Text:  rendered,
		Why: "a write to a " + kind + " named as a balance" + inFunc(enclosing) + ". CLAUDE.md " +
			"non-negotiable: \"Balances are derived, never written.\" DEC-2 §4.4 I-3: \"No write " +
			"path to any balance column exists in the Go tree.\" Derive by summation over the " +
			"postings; a bare local accumulator (`var debit, credit MinorUnits`) is the shape " +
			"nexus/internal/apps/ledger/money.go already uses and is NOT flagged.",
	})
	if enclosing != "" && holdFuncRe.MatchString(enclosing) && !availableNameRe.MatchString(name) {
		c.add(finding{
			Class: "I6-HOLD-BALANCE",
			Pos:   pos,
			Text:  rendered,
			Why: "a hold mutates a balance that is not `available`" + inFunc(enclosing) + ". " +
				"CLAUDE.md non-negotiable: \"Holds are postings and alter `available` only, never " +
				"posted `balance`.\" A hold must be posted and the effect derived.",
		})
	}
}

// ---------------------------------------------------------------------------------------------

func walk(root string) (*census, error) {
	c := &census{Root: root}
	pkgs := map[string]bool{}
	fset := token.NewFileSet()
	var files []parsedFile
	err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if prunedDirs[d.Name()] {
				return filepath.SkipDir
			}
			return nil
		}
		if !strings.HasSuffix(path, ".go") {
			return nil
		}
		rel, rerr := filepath.Rel(root, path)
		if rerr != nil {
			rel = path
		}
		rel = filepath.ToSlash(rel)
		src, rerr := os.ReadFile(path)
		if rerr != nil {
			return rerr
		}
		c.Files++
		pkgs[filepath.ToSlash(filepath.Dir(rel))] = true
		af, perr := parser.ParseFile(fset, path, src, parser.ParseComments)
		if perr != nil {
			c.ScanErrors = append(c.ScanErrors, fmt.Sprintf(
				"%s: could not be parsed (%v), so it has NOT been checked for I-3 or I-4", rel, perr))
			return nil
		}
		files = append(files, parsedFile{path: path, rel: rel, file: af})
		return nil
	})
	if err != nil {
		return c, fmt.Errorf("walking %s: %w", root, err)
	}
	// WHOLE-TREE PASS FIRST. Wrapper discovery must see every declaration before any call is
	// judged, or a call to a wrapper declared later in the walk order would be classified
	// against an incomplete set — a walk-order-dependent verdict, which is not a verdict.
	c.Wrappers = discoverSQLWrappers(files)
	for _, pf := range files {
		c.scanFile(fset, pf)
	}
	for p := range pkgs {
		c.PackageDirs = append(c.PackageDirs, p)
	}
	sort.Strings(c.PackageDirs)
	return c, nil
}

const cannotCatch = `CANNOT-CATCH — the honest limits of this guard, printed on every run, pass or fail:
  1. DYNAMIC SQL. A statement assembled at run time (fmt.Sprintf, strings.Builder, a query
     builder's own AST) is not readable as text. The guard converts that blind spot into a
     REFUSAL for the mutating driver family (class OPAQUE-SQL) — but only where it recognises
     the call. A mutating call through an interface method it does not name, or through
     reflection, is invisible.
  2. INDIRECTION THROUGH A NAME THAT IS NOT A BALANCE. A field called Amount, Total, Net or
     Position that IS a stored balance is not detected: the surface is the NAME, because
     without a type checker there is nothing else to key on. Renaming a balance defeats it.
     T509 WIDENED THE NAME, IT DID NOT FIX THE CLASS: "outstanding" now counts as a balance
     word alongside "balance", which closes the MEASURED case (two ports of one Fineract
     method, "outstandingLoanBalance" refused and "outstandingMinor" passed). Every other
     spelling is still invisible, and this item is why.
  3. STORED PROCEDURES, TRIGGERS AND MIGRATIONS. This guard walks Go only. An UPDATE inside a
     Liquibase changelog, a Postgres trigger or a hand-run psql script is out of its reach,
     and the schema is Fineract's, which HAS such objects.
  4. I-5. "A correction that mutates a leg instead of adding a reversing pair" is only
     decidable once a leg type and a correction path exist in the Go tree. Neither does. The
     mechanical half (a write to a committed row, a write to a balance) IS covered; the
     semantic half is not, and is not claimed.
  5. SEMANTICS OF DERIVATION. A function that CACHES a balance in a map keyed by account, then
     returns the cache, is caught only if the cache is named as a balance (class I3-PKG-STATE
     covers the package-level case). A struct-field cache inside a service object with a
     non-balance name is not.
  6. NON-GO CALLERS. Anything that reaches the database without going through this module.
  7. THREE MEASURED OVER-MATCHES, NAMED SO NOBODY REDISCOVERS THEM AS BUGS. (i) The DML-verb
     test fires on English prose: on nexus/ at the commit this guard was written, all three
     DML-classified literals are message text, not SQL — which is why every one is PRINTED
     with its position and why the NIL-COVERAGE notice keys on the narrower "names a table"
     count. (ii) The hold-name matcher fires on "...Holds" meaning "the property holds":
     nexus/internal/apps/ledger/slots_test.go:187 TestPlaceholderDisjointnessHolds is counted
     as a hold-named function. (iii) IT ALSO FIRES ON "...Holder", a third shape this list
     used to omit: nexus/internal/apps/loanproduct/repaymentperiod.go:486
     SetReAgedEarlyRepaymentHolder [T502 B-3, confirmed exactly by T505 §6 and T514]. None of
     the three can produce a FINDING on its own — a finding additionally requires a protected
     table, a balance column, or a balance write — so all are noise in a count, never a false
     rejection. The point of this list is completeness, so an incomplete list was itself the
     defect.
  8. TESTS ARE INSPECTED, NOT EXEMPTED. A _test.go file that assigns a balance field as a
     FIXTURE is reported as a violation. That is fail-CLOSED by choice; if a legitimate
     fixture ever trips it, the correct answers are a bare accumulator, a non-balance name for
     a non-balance quantity, or an argued DEC-2 exemption. ⚠ THIS ITEM USED TO SAY "the fix is
     a constructor, not an exemption" AND THAT WAS ADVICE FOR EVADING THIS GUARD: a composite
     literal's keys were invisible to writeTarget, so moving the write into a constructor
     silenced the finding while storing the identical value (T502 B-2; T505 §6 confirmed six
     such writes in the same package, one four lines from a refused site). T509 closed the
     allocated form — see class I3-COMPOSITE-BALANCE — and deleted the advice. The residual is
     item 10.
  9. THE BALANCE-READ CENSUS IS SIGHT, NOT ENFORCEMENT. Every SELECT naming a balance column
     is printed with its position and NONE is refused. DEC-2 §4.4 I-3's gradeable text is "No
     WRITE PATH to any balance column exists in the Go tree"; a read is not a write path, and
     raising it to a refusal is an amendment to a ratified DEC-n, which CLAUDE.md routes as a
     "user" gate. It is printed because T501's defect entered exactly there — a stored balance
     decoded on the way IN and then treated as authoritative. A site on that list has been
     SEEN, never cleared.
 10. THE STORE THAT A COMPOSITE LITERAL REACHES. I3-COMPOSITE-BALANCE fires on the ALLOCATED
     form "&T{Balance: v}", because allocation produces something that outlives the
     expression — writeTarget's own doctrine. It does NOT fire on "v := T{Balance: x}"
     followed by a store of "&v", nor on "append(store.rows, T{Balance: x})". Following a
     value into a store requires go/types, and there is a hard design constraint on that work
     recorded by T514 and repeated here because it is the trap: SUCH AN ANALYSIS MUST FAIL
     CLOSED ON UNRESOLVED VALUE FLOW. An analysis that answers "not persisted" on an edge it
     cannot resolve reintroduces the same fail-open one layer up, and — unlike a waiver, which
     is a visible document a human must amend — a heuristic's failure produces NO ARTEFACT AT
     ALL.
 11. WRAPPER DISCOVERY IS BY NAME AND BY PARAMETER NAME. A function is recognised as carrying
     SQL when it has a string parameter called sql/query/stmt/statement/ddl/dml/q and its body
     reaches a driver method or another discovered wrapper. Two functions of the same name in
     different packages are ONE NAME to this guard (it has no type checker), and a wrapper
     that names its parameter something else, or assembles the statement from a struct field
     rather than taking it as an argument, is not discovered at all.
 12. THE FOUR loanproduct SITES ARE A KNOWN, ARGUED, TEST-PINNED RED — NOT A GUARD DEFECT AND
     NOT AN ACCIDENT. interestperiod.go and repaymentperiod.go write schedule intermediates
     that are not ledger balances on the two legs that survive (T516): LEG 1 parity — applying
     I-3's remedy to the cell changes the money, because the oracle refreshes
     outstandingLoanBalance only at explicit sweeps and reads it stale in between, and this is
     executable, not argued (TestOutstandingLoanBalanceIsASweptSnapshot); and LEG 2
     reachability — the value reaches no journal entry, no GL posting and no column any
     aggregate reads as an account balance, its persistence being a closed loop written by the
     projection and reloaded as the same projection's starting state. The posting-stream test
     is RETIRED (T516), not merely demoted. They stay REFUSED because the only mechanism that
     could distinguish them soundly — LEG 2's go/types reachability discriminator — does not
     exist yet, and the persistence-surface heuristic that was proposed instead was MEASURED
     being defeated by a single git mv of an unrelated real savings balance write into a
     subdirectory (T505 MAJOR-1). A known red is an acceptable state; a green bar bought with
     a defeatable predicate is not.`

func report(c *census) int {
	fmt.Printf("CENSUS ledger-invariants — inspected %d Go files / %d packages / %d funcs "+
		"(%d hold-named) / %d assignment or inc-dec statements / %d write targets / "+
		"%d string literals in %d concatenation groups / %d calls under %s (recursive, whole Go tree)\n",
		c.Files, len(c.PackageDirs), c.Funcs, c.HoldFuncs, c.Assigns, c.WriteTargets,
		c.StringLits, c.StringGroups, c.Calls, c.Root)
	fmt.Printf("CENSUS ledger-invariants SQL surface — %d SQL-shaped literals, of which %d carry a DML "+
		"verb (UPPER BOUND: English prose containing \"update\" satisfies it) and %d name an actual "+
		"table; %d exec-family calls (%d mutating driver calls, %d calls to %d tree-local SQL "+
		"wrappers). Findings: %d\n",
		c.SQLShaped, c.SQLDML, c.SQLDMLTabled, c.ExecFamily, c.MutatingExec, c.WrapperCalls,
		len(c.Wrappers), len(c.Findings))
	fmt.Printf("CENSUS ledger-invariants composite surface — %d composite literals carrying %d keyed "+
		"elements (the denominator of I3-COMPOSITE-BALANCE); %d SELECT(s) naming a balance column "+
		"(NAMED, NOT REFUSED — see the balance-read note below)\n",
		c.CompositeLits, c.CompositeKeys, len(c.BalanceReads))
	for _, p := range c.PackageDirs {
		fmt.Printf("CENSUS   covered: %s\n", p)
	}
	// EVERY ITEM THE TWO NARROWEST SURFACES SAW, NAMED. These are the surfaces most likely to
	// be empty and most likely to over-match, so their members are listed and not merely
	// totalled: a reader can check each one by hand.
	for _, s := range c.SQLDMLSites {
		fmt.Printf("CENSUS   DML-classified literal: %s\n", s)
	}
	for _, s := range c.HoldFuncNames {
		fmt.Printf("CENSUS   hold-named func: %s\n", s)
	}
	for _, w := range c.Wrappers {
		fmt.Printf("CENSUS   tree-local SQL wrapper: %s (arg %d) — %s\n", w.Name, w.ArgIndex, w.Why)
	}
	// NAMED, NOT REFUSED, AND THE POLARITY SAID OUT LOUD ON THE LINE ITSELF so that no reader
	// can quote the count as coverage. DEC-2 §4.4 I-3 grades a WRITE path; a read is not one,
	// and raising it to a refusal is a DEC-n amendment, i.e. a `user` gate — not a guard patch.
	for _, s := range c.BalanceReads {
		fmt.Printf("CENSUS   balance column READ (seen, NOT refused — I-3 grades writes): %s\n", s)
	}

	rc := 0

	// P-35, applied to EVERY population this guard makes a negative assertion over.
	// A negative assertion is vacuously true on an empty walk, so an empty walk is an ERROR.
	type gate struct {
		n     int
		label string
	}
	for _, g := range []gate{
		{c.Files, "Go files"},
		{len(c.PackageDirs), "packages"},
		{c.Funcs, "function declarations"},
		{c.Assigns, "assignment or inc-dec statements"},
		{c.StringLits, "string literals"},
		// T509: the composite-literal surface is a population this guard now asserts an
		// absence over, so P-35 binds it exactly as it binds the others. A tree with no
		// composite literals at all has not been walked.
		{c.CompositeLits, "composite literals"},
	} {
		if g.n == 0 {
			fmt.Printf("REFUSED — INSPECTED ZERO %s under %s.\n", g.label, c.Root)
			fmt.Println("This guard asserts an ABSENCE (no balance write path, no UPDATE/DELETE against")
			fmt.Println("acc_gl_journal_entry). An absence is vacuously true over an empty population, so a")
			fmt.Println("count of zero is an ERROR, not a pass (P-35).")
			rc = 1
		}
	}

	if len(c.ScanErrors) > 0 {
		fmt.Println("REFUSED — a Go file in the derived set could not be parsed. A file that was not " +
			"parsed was not checked, and is never silently skipped:")
		for _, e := range c.ScanErrors {
			fmt.Println("  " + e)
		}
		rc = 1
	}

	if len(c.Findings) > 0 {
		sort.Slice(c.Findings, func(i, j int) bool {
			if c.Findings[i].Class != c.Findings[j].Class {
				return c.Findings[i].Class < c.Findings[j].Class
			}
			return c.Findings[i].Pos < c.Findings[j].Pos
		})
		fmt.Println("REFUSED — the double-entry invariants DEC-2 §4.4 obliges are violated in the Go tree:")
		for _, f := range c.Findings {
			fmt.Printf("  [%s] %s\n      %s\n      %s\n", f.Class, f.Pos, f.Text, f.Why)
		}
		rc = 1
	}

	// NIL COVERAGE. Reported loudly whether the run passes or fails: a surface with an empty
	// population has PROVEN NOTHING about this tree, and must never be quoted as though it had.
	if c.SQLDMLTabled == 0 {
		fmt.Printf("NIL-COVERAGE — the SQL surface inspected %d string literals and found ZERO SQL DML "+
			"statements of any kind under %s. This tree contains no SQL: the I-4 SQL classes "+
			"(I4-DML, I3-SQL-BALANCE) are proven by this program's --selftest and NOT by this tree. "+
			"Do not read this run as evidence that the SQL detector works on real ledger SQL; there "+
			"is none yet.\n", c.StringLits, c.Root)
	}
	if c.MutatingExec == 0 {
		fmt.Printf("NIL-COVERAGE — zero mutating driver calls (Exec/ExecContext/SendBatch/CopyFrom/" +
			"Prepare) exist under this root, so class OPAQUE-SQL inspected an empty population. " +
			"The Go module declares no database driver at all.\n")
	}
	if c.HoldFuncs == 0 {
		fmt.Printf("NIL-COVERAGE — zero hold-named functions exist under this root, so class " +
			"I6-HOLD-BALANCE inspected an empty population. I-6 is UNPROVEN on this tree.\n")
	}

	fmt.Println(cannotCatch)

	if rc == 0 {
		fmt.Printf("clean: no balance write path, no UPDATE/DELETE against a journal-entry table, and no "+
			"hold touching a posted balance, across %d Go files in %d packages.\n",
			c.Files, len(c.PackageDirs))
	}
	return rc
}

func check(root string) int {
	c, err := walk(root)
	if err != nil {
		fmt.Printf("REFUSED — the walk itself failed: %v\n", err)
		fmt.Println("A guard whose walk failed has inspected an unknown population. ERROR, not a pass.")
		return 1
	}
	return report(c)
}

// ---------------------------------------------------------------------------------------------
// Selftest — P-22 (drive it RED on every violation class) and P-50 (drive it GREEN on the tree
// it will actually run against, and on the clean equivalent of each planted defect).
// ---------------------------------------------------------------------------------------------

// ballast gives every scratch tree a non-empty population for all five P-35 gates, so that a
// RED case fails for the reason under test and never because the tree was too small.
const ballast = `package ballast

import "fmt"

type Row struct {
	AccountID int64
	AmountMinor int64
}

var rows []Row

func Total(in []Row) int64 {
	var total int64
	for _, r := range in {
		total += r.AmountMinor
	}
	return total
}

func Describe(r Row) string {
	s := "account"
	s = s + " row"
	return fmt.Sprintf("%s %d", s, r.AccountID)
}

// A composite literal, so the P-35 gate T509 added over that population is satisfied by
// the ballast and every RED case still fails for the reason under test.
func Sample() Row { return Row{AccountID: 1, AmountMinor: 100} }
`

func writeGo(t *testing_T, dir, pkg, name, body string) {
	d := filepath.Join(dir, pkg)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.fail("mkdir " + d + ": " + err.Error())
		return
	}
	if err := os.WriteFile(filepath.Join(d, name), []byte(body), 0o644); err != nil {
		t.fail("write " + name + ": " + err.Error())
	}
}

type testing_T struct{ fails []string }

func (t *testing_T) fail(s string) { t.fails = append(t.fails, s) }

func scratch(t *testing_T, withBallast bool) string {
	dir, err := os.MkdirTemp("", "ledgerguard")
	if err != nil {
		t.fail("mkdtemp: " + err.Error())
		return ""
	}
	if withBallast {
		writeGo(t, dir, "ballast", "ballast.go", ballast)
	}
	return dir
}

// runCase runs the guard over `dir`, prints the transcript the wrapper counts, and asserts the
// exit code AND — for a RED case — that the EXPECTED CLASS is what fired. An exit code alone
// would let a case "pass" because the P-35 gate tripped instead of the detector.
func runCase(t *testing_T, label, dir string, wantRC int, wantClass string) {
	runCaseText(t, label, dir, wantRC, wantClass, nil, nil)
}

// runCaseText is runCase plus assertions on the TEXT of the transcript. A class firing is not
// always the whole claim: item 11's repair is that the finding must NAME THE REAL TABLE and
// must never print the keyword `set` as one, and only a text assertion can pin that. `want`
// substrings must all appear; `reject` substrings must all be absent.
func runCaseText(t *testing_T, label, dir string, wantRC int, wantClass string, want, reject []string) {
	fmt.Printf("--- %s ---\n", label)
	out, rc := captureCheck(dir)
	fmt.Printf("  -> exit %d\n", rc)
	if rc != wantRC {
		t.fail(label + ": expected exit " + strconv.Itoa(wantRC) + ", got " + strconv.Itoa(rc))
		fmt.Println(indent(out))
		return
	}
	if wantClass != "" && !strings.Contains(out, "["+wantClass+"]") {
		t.fail(label + ": exited " + strconv.Itoa(rc) + " but class " + wantClass + " never fired")
		fmt.Println(indent(out))
		return
	}
	for _, w := range want {
		if !strings.Contains(out, w) {
			t.fail(label + ": the transcript never said " + strconv.Quote(w))
			fmt.Println(indent(out))
			return
		}
	}
	for _, r := range reject {
		if strings.Contains(out, r) {
			t.fail(label + ": the transcript said " + strconv.Quote(r) + ", which it must not")
			fmt.Println(indent(out))
			return
		}
	}
}

func indent(s string) string {
	var b strings.Builder
	for _, line := range strings.Split(strings.TrimRight(s, "\n"), "\n") {
		b.WriteString("      " + line + "\n")
	}
	return b.String()
}

func captureCheck(dir string) (string, int) {
	r, w, err := os.Pipe()
	if err != nil {
		return "pipe: " + err.Error(), 1
	}
	saved := os.Stdout
	os.Stdout = w
	rc := check(dir)
	os.Stdout = saved
	w.Close()
	buf := make([]byte, 0, 1<<16)
	tmp := make([]byte, 4096)
	for {
		n, rerr := r.Read(tmp)
		buf = append(buf, tmp[:n]...)
		if rerr != nil {
			break
		}
	}
	r.Close()
	return string(buf), rc
}

func selftest(repoRoot string) int {
	t := &testing_T{}

	// (a) I-3, the in-memory half: a balance FIELD incremented.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "acct", "acct.go", `package acct

type Account struct{ Balance int64 }

func Post(a *Account, amountMinor int64) {
	a.Balance += amountMinor
}
`)
		runCase(t, "(a) a balance field incremented — I-3", d, 1, "I3-FIELD-WRITE")
		os.RemoveAll(d)
	}

	// (b) I-4, UPDATE against the journal table.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "store", "store.go", `package store

const reverseSQL = "UPDATE acc_gl_journal_entry SET reversed = true WHERE id = $1"
`)
		runCase(t, "(b) UPDATE acc_gl_journal_entry — I-4", d, 1, "I4-DML")
		os.RemoveAll(d)
	}

	// (c) I-4, DELETE against the journal table.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "store", "store.go", `package store

const purgeSQL = "DELETE FROM acc_gl_journal_entry WHERE transaction_id = $1"
`)
		runCase(t, "(c) DELETE FROM acc_gl_journal_entry — I-4", d, 1, "I4-DML")
		os.RemoveAll(d)
	}

	// (d) I-6, a hold mutating a POSTED balance rather than `available`.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "hold", "hold.go", `package hold

type Savings struct {
	PostedBalance    int64
	AvailableBalance int64
}

func PlaceHold(s *Savings, amountMinor int64) {
	s.PostedBalance -= amountMinor
}
`)
		runCase(t, "(d) a hold mutating a posted balance — I-6", d, 1, "I6-HOLD-BALANCE")
		os.RemoveAll(d)
	}

	// (e) I-3, the m_trial_balance shape: a balance column populated at INSERT.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "tb", "tb.go", `package tb

const tbSQL = "INSERT INTO m_trial_balance (office_id, account_id, closing_balance) VALUES ($1,$2,$3)"
`)
		runCase(t, "(e) a balance column populated at INSERT — I-3", d, 1, "I3-SQL-BALANCE")
		os.RemoveAll(d)
	}

	// (f) I-3, an UPDATE assigning a balance column on a non-protected table.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "sav", "sav.go", `package sav

const upd = "UPDATE m_savings_account SET account_balance_derived = $1 WHERE id = $2"
`)
		runCase(t, "(f) UPDATE ... SET <balance column> — I-3", d, 1, "I3-SQL-BALANCE")
		os.RemoveAll(d)
	}

	// (g) I-4 through a query builder, where the table name never appears in SQL text.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "orm", "orm.go", `package orm

type DB struct{}

type JournalEntry struct{ ID int64 }

func (d DB) Model(v any) DB       { return d }
func (d DB) Delete(v any) error   { return nil }

func Purge(db DB, id int64) error {
	return db.Model(&JournalEntry{ID: id}).Delete(nil)
}
`)
		runCase(t, "(g) an ORM delete of a JournalEntry — I-4 via a builder", d, 1, "I4-BUILDER")
		os.RemoveAll(d)
	}

	// (h) the blind spot, converted into a refusal.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "dyn", "dyn.go", `package dyn

type Conn struct{}

func (c Conn) Exec(ctx any, sql string, args ...any) error { return nil }

func build(table string) string { return "UPDATE " + table + " SET x = 1" }

func Run(c Conn, ctx any, t string) error {
	return c.Exec(ctx, build(t))
}
`)
		runCase(t, "(h) dynamically built SQL in a mutating Exec — OPAQUE-SQL", d, 1, "OPAQUE-SQL")
		os.RemoveAll(d)
	}

	// (i) a package-level balance store.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "cache", "cache.go", `package cache

var runningBalance int64

func Bump(n int64) { runningBalance += n }
`)
		runCase(t, "(i) a package-level balance store — I-3", d, 1, "I3-PKG-STATE")
		os.RemoveAll(d)
	}

	// (j) THE DERIVATION ITSELF (the T166 shape): a violation three directories deep, in a
	//     package nobody named, must be reached.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, filepath.Join("a", "b", "c"), "deep.go", `package c

type Acct struct{ ClosingBalanceMinor int64 }

func Set(a *Acct, v int64) { a.ClosingBalanceMinor = v }
`)
		runCase(t, "(j) a violation three directories deep — the walk must reach it", d, 1, "I3-FIELD-WRITE")
		os.RemoveAll(d)
	}

	// (k) GREEN, and it must be green: every construct here is the CORRECT way to write the
	//     same thing, and a guard that refuses these is over-broad and useless.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "clean", "clean.go", `package clean

type Leg struct{ AmountMinor int64 }

type View struct{ Balance int64 }

// A bare local accumulator IS the derivation. It must not be flagged.
func Derive(legs []Leg) int64 {
	var balance int64
	for _, l := range legs {
		balance += l.AmountMinor
	}
	return balance
}

// A composite literal carrying a derived balance is a RETURN VALUE, not a store.
func Present(legs []Leg) View { return View{Balance: Derive(legs)} }

// A comparison is not a write.
func IsZero(v View) bool { return v.Balance == 0 }

// Appending to the journal is the ONLY lawful write to it, and must pass.
const appendSQL = "INSERT INTO acc_gl_journal_entry (account_id, type_enum, amount) VALUES ($1,$2,$3)"

// Reading a balance column is not writing one.
const readSQL = "SELECT outstanding_balance FROM m_loan_repayment_schedule WHERE loan_id = $1"

// "hold" must not be matched inside "Threshold".
func ThresholdFor(n int64) int64 { return n }
`)
		runCase(t, "(k) the CORRECT forms of every flagged construct — must PASS", d, 0, "")
		os.RemoveAll(d)
	}

	// (l) P-35: an empty tree is an ERROR, never a pass over no input.
	if d := scratch(t, false); d != "" {
		runCase(t, "(l) an empty tree — zero inspected is an ERROR", d, 1, "")
		os.RemoveAll(d)
	}

	// (m) P-35 again, one gate deeper: a tree with files and packages but NO functions,
	//     NO assignments and NO string literals. A file count alone would have passed this.
	if d := scratch(t, false); d != "" {
		writeGo(t, d, "hollow", "hollow.go", "package hollow\n")
		runCase(t, "(m) files and packages but zero funcs/assignments/literals — still an ERROR", d, 1, "")
		os.RemoveAll(d)
	}

	// (n) THE NEGATIVE CONTROL — a COMMITTED FIXTURE, not the real tree. T509 item 12.
	//
	//     This case used to assert "nexus/ must exit 0", and that assertion is not the guard's
	//     to make. When nexus/ acquired findings the guard was SUPPOSED to report, case (n)
	//     failed and the head printed "the guard FAILED ITS OWN SELFTEST … it can no longer be
	//     shown to refuse the defect it exists to refuse" — while all fourteen planted-defect
	//     cases had driven it RED correctly. A negative control must be a FIXED artefact the
	//     guard's authors own; case (n) was a moving target any commit could flip, it conflated
	//     "the instrument is untrustworthy" with "the tree has known findings", and it did so in
	//     the alarming direction. It was also unpassable by design going forward: the four
	//     loanproduct sites stay RED on a recorded decision (T502/T505/T514), so it could never
	//     have gone green again — P-45's shape, a check that cannot pass is a check that gets
	//     ignored.
	//
	//     A MISSING FIXTURE IS A FAILURE, NEVER A SKIP: the GREEN half of P-50 would otherwise
	//     silently stop running, which is the same defect one level up.
	if repoRoot != "" {
		fixture := filepath.Join(repoRoot, ".softhouse", "guards", "ledgerguard", "testdata", "cleantree")
		if st, err := os.Stat(fixture); err == nil && st.IsDir() {
			// THE FIXTURE'S OWN CONTENTS ARE CHECKED BEFORE IT IS TRUSTED, which is P-35 applied
			// to the negative control itself. "The fixture passed" is worth nothing if the
			// fixture has been reduced to one trivial file: the guard would still walk a
			// non-empty tree, still clear every P-35 gate on the ballast-sized population, and
			// still report GREEN — having demonstrated nothing. Each member below carries a
			// construct some class refuses in its incorrect form, so losing one silently
			// removes a whole over-match check.
			//
			// This list is also what makes main.go the honest REACHED-BY witness for those three
			// files under .softhouse/conformance.sh's guards-dir registration: it names them
			// because it genuinely requires them, not to satisfy a grep.
			for _, member := range []string{
				filepath.Join("ledger", "derive.go"),   // the derived-balance forms: bare accumulators
				filepath.Join("store", "store.go"),     // the lawful SQL forms, and the wrapper GREEN case
				filepath.Join("present", "present.go"), // the by-value composite literal that must not be refused
			} {
				if _, err := os.Stat(filepath.Join(fixture, member)); err != nil {
					t.fail("(n) the clean fixture is INCOMPLETE: " + member + " is missing (" +
						err.Error() + "). A negative control that lost a member proves less than " +
						"it claims and must never pass quietly.")
				}
			}
			runCase(t, "(n) the COMMITTED CLEAN FIXTURE at "+fixture+" — must PASS", fixture, 0, "")
		} else {
			t.fail("(n) the clean fixture was not found at " + fixture + "; the GREEN half was NOT run")
			fmt.Println("--- (n) the clean fixture — NOT FOUND ---")
			fmt.Println("  -> exit 1")
		}
	}

	// (o) a file that does not parse is REFUSED, never skipped.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "broken", "broken.go", "package broken\n\nfunc {{{\n")
		runCase(t, "(o) an unparseable Go file — refused, never skipped", d, 1, "")
		os.RemoveAll(d)
	}

	// ---------------------------------------------------------------------------------------
	// T509 — one case per blind spot closed. Every one of these passed BEFORE the repair.
	// ---------------------------------------------------------------------------------------

	// (p) THE TABLE NAME IS THE BALANCE. T503's B-2: m_wc_loan_balance has thirteen columns and
	//     not one of them contains "balance"; the TABLE does, and balanceNameRe was applied to
	//     the column list only.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "wc", "wc.go", `package wc

const upsertSQL = "INSERT INTO m_wc_loan_balance (wc_loan_id, principal, principal_paid, fee, penalty) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (wc_loan_id) DO UPDATE SET principal = excluded.principal"
`)
		runCaseText(t, "(p) a write to a table whose NAME is a balance — I-3", d, 1,
			"I3-SQL-BALANCE-TABLE",
			[]string{`"m_wc_loan_balance"`}, nil)
		os.RemoveAll(d)
	}

	// (q) THE UPSERT TABLE EXTRACTOR (item 11). The finding must name the real table. It used
	//     to print `on table "set"` — the keyword standing where the table name was expected —
	//     and the reject list is the whole point of this case.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "sav", "sav.go", `package sav

const upsertSummary = "INSERT INTO m_savings_account_summary (savings_account_id, account_balance_derived) VALUES ($1,$2) ON CONFLICT (savings_account_id) DO UPDATE SET account_balance_derived = excluded.account_balance_derived"
`)
		runCaseText(t, "(q) an upsert's balance column — the table must be NAMED, never \"set\"", d, 1,
			"I3-SQL-BALANCE",
			[]string{`"account_balance_derived"`, `"m_savings_account_summary"`},
			[]string{`on table "set"`})
		os.RemoveAll(d)
	}

	// (r) THE COMPOSITE-LITERAL FORM of a refused write. T502's B-2 / T505 §6: six of these sat
	//     unflagged in the same package as four refused assignments, one four lines away — and
	//     CANNOT-CATCH item 8 recommended exactly this move as "the fix".
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "ctor", "ctor.go", `package ctor

type Segment struct {
	OutstandingLoanBalance int64
	Rounding               int
}

func NewSegment(openingMinor int64) *Segment {
	return &Segment{OutstandingLoanBalance: openingMinor, Rounding: 4}
}
`)
		runCase(t, "(r) a balance written by an ALLOCATED composite literal — I-3", d, 1, "I3-COMPOSITE-BALANCE")
		os.RemoveAll(d)
	}

	// (s) THE SYNONYM. Two ports of one Fineract method got opposite verdicts because one field
	//     was spelled outstandingLoanBalance and the other outstandingMinor (T502 B-1, T505
	//     MAJOR-3). This is the second spelling.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "emi", "emi.go", `package emi

type seg struct{ outstandingMinor, disbursedMinor int64 }

func rollForward(s *seg, prev seg, dueMinor int64) {
	s.outstandingMinor = prev.outstandingMinor + prev.disbursedMinor - dueMinor
}
`)
		runCase(t, "(s) a balance spelled \"outstanding\" rather than \"balance\" — I-3", d, 1, "I3-FIELD-WRITE")
		os.RemoveAll(d)
	}

	// (t) THE MUTATING WRAPPER (T506 F-6). The exec-family regex names driver methods; this
	//     statement never reaches one under a name the regex knows, and its column list is
	//     spliced in, so before the repair there was NO finding of any class here — not an
	//     OPAQUE-SQL, not an I-3. The bar would have been green with the balance column written.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "repo", "repo.go", `package repo

type DB interface {
	Query(ctx any, sql string, args ...any) error
}

func QueryRows(ctx any, db DB, sql string, args []any) error { return db.Query(ctx, sql, args...) }

func InsertReturningInt64(ctx any, db DB, sql string, args ...any) (int64, error) {
	return 0, QueryRows(ctx, db, sql, args)
}

const cols = "savings_account_id, account_balance_derived"

func Save(ctx any, db DB, id, balanceMinor int64) (int64, error) {
	return InsertReturningInt64(ctx, db, "INSERT INTO m_savings_account_summary ("+cols+") VALUES ($1,$2) RETURNING id", id, balanceMinor)
}
`)
		runCase(t, "(t) a spliced INSERT routed through a tree-local wrapper — OPAQUE-SQL", d, 1, "OPAQUE-SQL")
		os.RemoveAll(d)
	}

	// (u) THE SAME WRAPPER, GREEN. P-50: a class that only ever fires has proved the guard
	//     noisy. An identical call whose statement is fully readable must PASS — and the
	//     wrapper's own pass-through of its `sql` parameter must not be refused either.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "repo", "repo.go", `package repo

type DB interface {
	Query(ctx any, sql string, args ...any) error
}

func QueryRows(ctx any, db DB, sql string, args []any) error { return db.Query(ctx, sql, args...) }

func InsertReturningInt64(ctx any, db DB, sql string, args ...any) (int64, error) {
	return 0, QueryRows(ctx, db, sql, args)
}

func Save(ctx any, db DB, id, amountMinor int64) (int64, error) {
	return InsertReturningInt64(ctx, db, "INSERT INTO m_loan_transaction (loan_id, amount) VALUES ($1,$2) RETURNING id", id, amountMinor)
}
`)
		runCase(t, "(u) the SAME wrapper with a readable statement — must PASS", d, 0, "")
		os.RemoveAll(d)
	}

	// (v) THE DIRECTION OF THE sqlArgOf WIDENING (item 7 / T506 F-5), pinned in BOTH polarities.
	//     A repository that carries its context as a FIELD and passes a plain literal must be
	//     READ (green here); genuinely assembled SQL is still REFUSED (case (h) above).
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "fieldctx", "fieldctx.go", `package fieldctx

type Conn struct{}

func (c Conn) Exec(ctx any, sql string, args ...any) error { return nil }

type repo struct {
	ctx any
	db  Conn
}

func (r repo) Append(id int64) error {
	return r.db.Exec(r.ctx, "INSERT INTO acc_gl_journal_entry (account_id) VALUES ($1)", id)
}
`)
		runCase(t, "(v) a literal behind a FIELD context — readable, must PASS", d, 0, "")
		os.RemoveAll(d)
	}

	// (w) READING A BALANCE COLUMN IS NOT WRITING ONE, and the census must SAY SO rather than
	//     leaving the reader to infer it from silence (item 8). Green, with the site named.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "read", "read.go", `package read

const q = "SELECT id, outstanding_loan_balance_derived FROM m_loan_transaction WHERE loan_id = $1"
`)
		runCaseText(t, "(w) a SELECT of a balance column — named in the census, NOT refused", d, 0, "",
			[]string{"balance column READ (seen, NOT refused"}, nil)
		os.RemoveAll(d)
	}

	// (x) THE COLUMN ITEM 4 NAMES. m_loan_transaction.outstanding_loan_balance_derived
	//     [VERIFIED: LoanTransaction.java:127] is a real stored balance column that T502's
	//     downstream check missed; its conclusion survived by luck rather than by the check it
	//     performed (T505 MINOR-2, confirmed by T514). This case proves the guard would refuse
	//     a Go write to it, so the coverage is DEMONSTRATED rather than assumed.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "lb", "lb.go", `package lb

const upd = "UPDATE m_loan_transaction SET outstanding_loan_balance_derived = $1 WHERE id = $2"
`)
		runCaseText(t, "(x) a write to m_loan_transaction.outstanding_loan_balance_derived — I-3", d, 1,
			"I3-SQL-BALANCE",
			[]string{`"m_loan_transaction"`}, nil)
		os.RemoveAll(d)
	}

	// THE REAL TREE — REPORTED AS AN OBSERVATION, ASSERTED AS NOTHING. This is what replaced
	// case (n)'s assertion. It still walks nexus/ on every selftest run, so a walk that stops
	// reaching it is visible, but its finding count is a FACT ABOUT THE TREE and never a
	// verdict on the instrument.
	if repoRoot != "" {
		real := filepath.Join(repoRoot, "nexus")
		if st, err := os.Stat(real); err == nil && st.IsDir() {
			out, rc := captureCheck(real)
			n := strings.Count(out, "\n  [")
			fmt.Printf("OBSERVATION the real Go tree at %s: exit %d, %d finding(s). "+
				"THIS IS NOT A SELFTEST ASSERTION — a finding here is a fact about the TREE, "+
				"never a verdict on the guard.\n", real, rc, n)
		} else {
			fmt.Printf("OBSERVATION the real Go tree was not found at %s; nothing observed. "+
				"Not a failure: the negative control is the committed fixture in case (n).\n", real)
		}
	}

	fmt.Println()
	fmt.Printf("ledgerguard selftest: %d failure(s)\n", len(t.fails))
	for _, f := range t.fails {
		fmt.Println("  FAIL " + f)
	}
	if len(t.fails) > 0 {
		return 1
	}
	return 0
}

// ---------------------------------------------------------------------------------------------

func main() {
	root := ""
	repo := ""
	self := false
	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--selftest":
			self = true
		case "--root":
			if i+1 < len(args) {
				i++
				root = args[i]
			}
		case "--repo":
			if i+1 < len(args) {
				i++
				repo = args[i]
			}
		default:
			fmt.Printf("ledgerguard: unknown argument %q\n", args[i])
			os.Exit(2)
		}
	}
	if self {
		os.Exit(selftest(repo))
	}
	if root == "" {
		fmt.Println("ledgerguard: --root is required. A guard with no root inspects nothing, and a guard")
		fmt.Println("that inspects nothing passes everything. This is an ERROR, not a pass (P-35).")
		os.Exit(2)
	}
	os.Exit(check(root))
}
