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
)

// balanceNameRe is the balance-name matcher, for BOTH a Go identifier and a SQL column.
// Substring, not word-equality: `Balance`, `RunningBalance`, `closing_balance`,
// `account_balance_derived` and `balanceMinor` are all a balance, and every one of them has
// appeared in Fineract under one of those spellings.
var balanceNameRe = regexp.MustCompile(`(?i)balance`)

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
}

func (c *census) add(f finding) { c.Findings = append(c.Findings, f) }

// ---------------------------------------------------------------------------------------------
// SQL text analysis. Operates on a string the PARSER already isolated as a literal.
// ---------------------------------------------------------------------------------------------

func normalizeSQL(s string) string {
	return strings.ToLower(strings.Join(strings.Fields(s), " "))
}

func isBalanceName(s string) bool { return balanceNameRe.MatchString(s) }

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

	// I-3, persistence half: an UPDATE that assigns a balance column, on ANY table.
	if m := reUpdate.FindStringSubmatch(low); m != nil && confirmed {
		for _, col := range setColumns(low) {
			if isBalanceName(col) {
				c.add(finding{
					Class: "I3-SQL-BALANCE",
					Pos:   pos,
					Text:  short(raw),
					Why: "an UPDATE assigns the balance column " + strconv.Quote(col) + " on table " +
						strconv.Quote(m[3]) + where + ". CLAUDE.md non-negotiable: \"Balances are " +
						"derived, never written.\" Derive it by summation over the postings.",
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
	if sel, ok := first.(*ast.SelectorExpr); ok && sel.Sel.Name == "Background" {
		if len(call.Args) < 2 {
			return nil, false
		}
		return call.Args[1], true
	}
	return first, true
}

// ---------------------------------------------------------------------------------------------

func (c *census) scanFile(fset *token.FileSet, path, rel string, src []byte) {
	f, err := parser.ParseFile(fset, path, src, parser.ParseComments)
	if err != nil {
		c.ScanErrors = append(c.ScanErrors, fmt.Sprintf(
			"%s: could not be parsed (%v), so it has NOT been checked for I-3 or I-4", rel, err))
		return
	}
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

	// Every construct below is attributed to its enclosing top-level declaration, so that I-6
	// can ask "is this write inside a hold?".
	consumed := map[*ast.BasicLit]bool{}

	var enclosing string
	inspect := func(n ast.Node) bool {
		switch t := n.(type) {

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
		if holdFuncRe.MatchString(enclosing) {
			c.HoldFuncs++
			c.HoldFuncNames = append(c.HoldFuncNames, pos(fd.Pos())+"  "+enclosing)
		}
		ast.Inspect(fd, inspect)
	}
	// Pass 2: everything outside a function body (package-level var initialisers, consts).
	enclosing = ""
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
		c.scanFile(fset, path, rel, src)
		return nil
	})
	if err != nil {
		return c, fmt.Errorf("walking %s: %w", root, err)
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
  7. TWO MEASURED OVER-MATCHES, NAMED SO NOBODY REDISCOVERS THEM AS BUGS. (i) The DML-verb
     test fires on English prose: on nexus/ at the commit this guard was written, all three
     DML-classified literals are message text, not SQL — which is why every one is PRINTED
     with its position and why the NIL-COVERAGE notice keys on the narrower "names a table"
     count. (ii) The hold-name matcher fires on "...Holds" meaning "the property holds":
     nexus/internal/apps/ledger/slots_test.go:187 TestPlaceholderDisjointnessHolds is counted
     as a hold-named function. Neither over-match can produce a FINDING on its own — a finding
     additionally requires a protected table, a balance column, or a balance write — so both
     are noise in a count, never a false rejection.
  8. TESTS ARE INSPECTED, NOT EXEMPTED. A _test.go file that assigns a balance field as a
     FIXTURE is reported as a violation. That is fail-CLOSED by choice; if a legitimate
     fixture ever trips it, the fix is a constructor, not an exemption.`

func report(c *census) int {
	fmt.Printf("CENSUS ledger-invariants — inspected %d Go files / %d packages / %d funcs "+
		"(%d hold-named) / %d assignment or inc-dec statements / %d write targets / "+
		"%d string literals in %d concatenation groups / %d calls under %s (recursive, whole Go tree)\n",
		c.Files, len(c.PackageDirs), c.Funcs, c.HoldFuncs, c.Assigns, c.WriteTargets,
		c.StringLits, c.StringGroups, c.Calls, c.Root)
	fmt.Printf("CENSUS ledger-invariants SQL surface — %d SQL-shaped literals, of which %d carry a DML "+
		"verb (UPPER BOUND: English prose containing \"update\" satisfies it) and %d name an actual "+
		"table; %d exec-family calls (%d mutating). Findings: %d\n",
		c.SQLShaped, c.SQLDML, c.SQLDMLTabled, c.ExecFamily, c.MutatingExec, len(c.Findings))
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

	// (n) P-50 / P-56: GREEN ON THE TREE IT WILL ACTUALLY RUN AGAINST. This is not a synthetic
	//     fixture; it is nexus/, the population the wired guard would grade.
	if repoRoot != "" {
		real := filepath.Join(repoRoot, "nexus")
		if st, err := os.Stat(real); err == nil && st.IsDir() {
			runCase(t, "(n) the REAL Go tree at "+real+" — must PASS", real, 0, "")
		} else {
			t.fail("(n) the real Go tree was not found at " + real + "; the GREEN half was NOT run")
			fmt.Println("--- (n) the REAL Go tree — NOT FOUND ---")
			fmt.Println("  -> exit 1")
		}
	}

	// (o) a file that does not parse is REFUSED, never skipped.
	if d := scratch(t, true); d != "" {
		writeGo(t, d, "broken", "broken.go", "package broken\n\nfunc {{{\n")
		runCase(t, "(o) an unparseable Go file — refused, never skipped", d, 1, "")
		os.RemoveAll(d)
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
