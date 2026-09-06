package floatguard

import (
	"fmt"
	"go/parser"
	"go/scanner"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// THE NO-FLOAT GUARD, OVER THE GO TOKEN STREAM.
//
// CLAUDE.md's first non-negotiable: money is integer minor units, and there is
// no floating point in any monetary code path — including intermediate
// calculation. This file is the executable form of that sentence for the Go
// module.
//
// WHY IT LIVES HERE AND NOT ONLY IN A TEST. Until T154 the only Go-side guard
// was TestNoFloatInTheLoanScheduleTree, and `.softhouse/conformance.sh` does not
// run `go test` — it builds and runs the harness binary. So a violation could
// take conformance.sh to exit 0 even on a day somebody did run the tests. The
// census is a package function called by BOTH the test and Run, so the same
// scan gates the test suite AND the conformance verdict, and there is exactly
// one implementation of the rule. The same reasoning is why T166's widening had
// to land HERE and in conformance.sh's own shell guard, and NOT in the ledger
// package's in-package scans: those are `go test` checks, conformance.sh never
// runs `go test`, and a test-only guard is not a guard (P-45).
//
// WHAT ROOT IT BINDS, AND WHY THAT ROOT IS DERIVED (T166).
//
// Until T166 this rule bound ONE HARD-CODED SUBTREE, `nexus/internal/apps/loanschedule`,
// at three sites: this variable, `guard_no_float_in_harness` and `guard_gofmt`
// in conformance.sh. The consequence was measured, not theorised: with a float
// LITERAL, a float IDENTIFIER at a package root, and a float identifier in a
// SUBDIRECTORY all planted under `nexus/internal/apps/ledger/`, a full
// `bash .softhouse/conformance.sh` run produced output BYTE-IDENTICAL to the
// clean baseline — `VERDICT: PASS (exit 0)`, 5664 cells graded, "24 Go files /
// 56295 tokens" [VERIFIED: T166 red probe; `diff` of the clean and planted run
// logs returned exit 0. The subdirectory half was independently measured first
// by A2-9, finding F-E, with `nexus/internal/apps/ledger/sub/zz_sub.go`].
// The guard was silent precisely because it never looked, which is this
// program's signature failure: a green that means less than it appears to.
//
// The fix is NOT a second hard-coded path. Adding `ledger` beside `loanschedule`
// reproduces the defect for the next package and every package after it (P-26:
// sweep the concept, not the sentence). The root is therefore the GO MODULE
// ROOT and the walk is recursive, so the guarded set is DERIVED from what is on
// disk: a new package is covered BY DEFAULT wherever in the module it lands, at
// whatever nesting depth, and there is no list for anyone to forget to update.
//
// WHY THE MODULE ROOT AND NOT `nexus/internal/apps`. A2-9's F-E prescribed
// "recursive, rooted at internal/apps", which would have covered `ledger` and
// `ledger/sub`. The module root is one level wider and is chosen because
// `internal/apps` is itself a hard-coded path: a package landing at
// `nexus/internal/domain/` or `nexus/pkg/` would be silently uncovered, and
// SILENT is the defect class, not the particular directory. Today the two roots
// select the identical file set — every .go file in the module is under
// `internal/apps` — so the wider root costs nothing and removes the next
// omission in advance.
//
// THERE IS NO EXEMPTION LIST, DELIBERATELY. An allowlist is the mechanism that
// rots: an entry added for one honest reason outlives the reason, and nothing
// ever revisits it. The two exemptions this guard grants are structural
// properties of the token stream rather than entries in a table — comments are
// skipped by the scanner, and a decimal inside a string literal is token.STRING —
// and both are asserted by the guard's own test rather than assumed.
//
// WHAT IT INSPECTS, AND WHY BOTH HALVES ARE NEEDED.
//
//   - IDENTIFIERS. The named floating-point types and the strconv helpers that
//     produce them. This half has existed since T7.
//   - LITERALS — token.FLOAT and token.IMAG. This half is T154's, closing
//     T143/M-3. It is the hole that mattered: `rate := 0.036 / 12.0` declares no
//     forbidden identifier at all. Go infers an untyped float constant, the
//     arithmetic is IEEE-754 binary floating point, and the identifier scan sees
//     nothing. Measured before the fix, with that exact expression added to the
//     tree: `go build` exit 0, `go test -run TestNoFloatInTheLoanScheduleTree`
//     ok, `bash .softhouse/conformance.sh` exit 0 with no diagnostic
//     [VERIFIED: T134's guard register, .softhouse/nonnegotiable-guard-audit.md
//     row M-3; re-observed by T154, .softhouse/capture/t154-nofloat/out/].
//     The rule was "no floating point"; the guard implemented "no float-typed
//     identifiers" (P-35's second question: does the guard detect every FORM the
//     violation can take?).
//
// WHY THE TOKEN STREAM AND NOT A BYTE GREP (P-48 — detect code with a parser).
// The frozen contract's doc comments NAME the forbidden types in order to forbid
// them, so a byte grep fires on the prohibition itself, and a guard that fires on
// its own rule is a guard somebody switches off. go/scanner in mode 0 skips
// comments entirely, and it classifies a number inside a string as token.STRING —
// so neither a doc comment nor a decimal money fixture like "1250000.00" can trip
// it, with no exemption list to rot. Twice in the last fire a guard was kept green
// by PROSE in the file it was scanning, so the parser-based leg is the one to
// widen when there is a choice, and T166 widened it first and furthest.
//
// THE EVASIONS THAT REMAIN, ENUMERATED (T166). A guard whose limits are not
// written down gets over-trusted, which is how the last two of these were found
// the hard way. What this scan CANNOT see, and why:
//
//   - A float64 acquired by TYPE INFERENCE from a symbol declared elsewhere:
//     `v := somepkg.Rate()` where Rate returns a float64. No forbidden IDENT and
//     no FLOAT token appear at the use site. This is CLOSED TRANSITIVELY, not
//     directly: every package in the module is inside the guarded root, so the
//     DECLARATION is scanned and flagged even though the use is not. The
//     condition that keeps it closed is that go.mod declares no third-party
//     requires [VERIFIED: T166 read nexus/go.mod — module, `go 1.23`, no require
//     block] and that no package escapes the root, which
//     `every_go_package_in_the_module_is_covered` asserts. Add a dependency and
//     the class REOPENS; closing it directly needs a type-checked scan (go/types
//     with a source importer), which is a larger change than this one.
//   - A float64 produced by DECODING: encoding/json unmarshals a number into an
//     `any` as float64 with no float token anywhere. In the vector loader this is
//     already closed by construction rather than by scanning —
//     `dec.UseNumber()` plus RejectFloatTokens, which rejects any non-integer
//     JSON number in any field [VERIFIED: vector.go:768-773 and RejectFloatTokens].
//     Elsewhere in a future package it would be open, and `any` on a money path
//     is the shape to look for in review.
//   - unsafe pointer punning, reflection, and cgo. Nothing textual can see these.
//     The module imports none of them today; an import ban is the mechanism if
//     that changes, and forbiddenImportPaths is where it goes.
//
// The one class this scan is NOT the right tool for at all is the CROSS-FAMILY
// ENUM conversion A2-9 enumerated in finding F-F. That is a typing question, the
// compiler catches part of it (duplicate map keys, duplicate switch cases), and
// no token or import scan can reach the rest. It is recorded here so the next
// reader does not look for it in the wrong guard.
//
// PHRASED POSITIVELY (P-35). It reports what it INSPECTED — packages, files,
// tokens, identifiers, numeric literals — and every caller asserts a positive
// fact about those counts. Zero files scanned is an ERROR, never a pass, and so
// is zero PACKAGES. "I found nothing wrong" is vacuous on no input, which is the
// single shape shared by every vacuous guard this program has found. The PACKAGE
// count is T166's addition, because a file count alone cannot tell "the whole
// module was walked" apart from "one directory was walked and the rest of the
// module was never opened" — and the second is exactly the state the old root
// left this repository in while printing a healthy-looking 24.

// GuardedGoTreeRel is the tree the no-float rule binds, relative to the
// repository root. It is the GO MODULE ROOT, walked recursively, and it is the
// same tree `guard_no_float_in_harness` and `guard_gofmt` walk in
// .softhouse/conformance.sh — all three sites now derive their set from this one
// concept instead of each naming a subtree of its own.
//
// IT WAS CALLED LoanScheduleTreeRel UNTIL T166, AND THE NAME WAS PART OF THE
// DEFECT. A reader of grade.go saw `LoanScheduleTreeRel` and read it as a
// deliberate scoping decision rather than as the accident it was. A name that
// lies is how this hid, so the rename is not cosmetic.
var GuardedGoTreeRel = "nexus"

// forbiddenFloatIdentifiers is the identifier half of the rule.
//
// THE SPLIT STRING LITERALS ARE LOAD-BEARING, NOT A STYLE. `guard_no_float_in_harness`
// in conformance.sh strips comments and then byte-greps the remaining source for
// these very spellings. Written whole, this map would make THIS file a permanent
// failure of that guard. Split, the bytes never appear contiguously and the Go
// scanner still sees one string constant each.
//
// T166 widened that shell guard to the whole module, so this property now
// protects this file against a guard whose root no longer merely HAPPENS to
// contain it. Any future file that must name a forbidden spelling in code owes
// the same split; that is the principled answer, and it is the reason no
// exemption entry was needed for this file when the root grew.
var forbiddenFloatIdentifiers = map[string]bool{
	"float" + "32": true, "float" + "64": true,
	"complex" + "64": true, "complex" + "128": true,
	"Float": true, "Float" + "32": true, "Float" + "64": true,
	"Parse" + "Float": true, "Format" + "Float": true, "Append" + "Float": true,
	"Decimal": true,
}

// forbiddenImportPaths closes an EVASION CLASS AS A SET rather than one spelling
// at a time (P-26), and it is why T166 added an import leg at all.
//
// THE EVASION. The identifier arm matches an IDENT exactly. `x := math.Sqrt(y)`,
// `x := math.Pi`, `x := math.MaxFloat64`, `math.Inf(1)`, `math.Round(y)` produce
// or name IEEE-754 doubles while the only IDENTs present are `math` and a
// function name that is in no list — and none of them is a token.FLOAT either.
// So neither existing arm sees any of them.
//
// WHY A NAME LIST WOULD BE THE WRONG FIX. Enumerating `Sqrt`, `Pi`, `Round`,
// `Abs`, `Inf`, `NaN`, `MaxFloat64`, `Float64bits` … is the P-26 failure in its
// pure form: it closes the members somebody thought of, leaves the rest of the
// package open, and collides immediately with legitimate integer identifiers
// already in this module — `Abs` appears 3 times on `math/big.Int` and
// `Rounding*` appears 140 times [VERIFIED: T166 grep over
// nexus/internal/apps/loanschedule]. Banning the PACKAGE closes every member,
// present and future, in one rule with nothing to keep updated.
//
// `math` IS the floating-point package: every function in it takes or returns
// float64, and its only common integer use — `math.MaxInt64` / `math.MinInt64` —
// is a named constant a money package can write itself or take from
// `math/bits`. `math/big` and `math/bits` are NOT banned: big.Int is how this
// module does exact integer arithmetic, and `big.Float` is already blocked by
// the `Float` identifier. No file in the module imports plain `math` today
// [VERIFIED: T166, `grep -rn '"math"' nexus/` returns only `"math/big"`], so
// this rule costs nothing and forecloses the class in advance.
//
// DETECTED WITH A PARSER, NOT A REGEX (P-48). go/parser in ImportsOnly mode
// yields the import specs structurally, so a path named in a comment, in a
// string, or in a `//go:` directive cannot trip it, and a package aliased to
// something else cannot hide from it.
var forbiddenImportPaths = map[string]string{
	"math": "the math package is the floating-point package: every function in it takes or returns " +
		"a 64-bit IEEE-754 double, and `x := math.Sqrt(y)` or `x := math.Pi` names no forbidden " +
		"identifier and contains no floating-point literal, so neither other arm of this guard sees " +
		"it. Use math/big for exact integer arithmetic; math/bits and math/big are NOT banned",
}

// FloatingPointCensus is what the scan INSPECTED and what it found. Every field
// is a positive count; a caller that reports "clean" without also reporting
// PackagesScanned and FilesScanned has reported nothing.
type FloatingPointCensus struct {
	Root string

	// PackagesScanned is the number of DIRECTORIES under Root that held at
	// least one .go file. T166's addition: see the file comment — a file count
	// alone cannot distinguish a full-module walk from a single-directory walk.
	PackagesScanned int
	FilesScanned    int
	TokensScanned   int

	// PackageDirs is every scanned directory, slash-separated and relative to
	// Root, sorted. Reported so a reader can see the SET that was covered and
	// not merely its size — including NESTED directories, whose absence from
	// the in-package scans was A2-9's finding F-E.
	PackageDirs []string

	// IdentifierViolations, LiteralViolations and ImportViolations are
	// "<file>:<line>:<col>: …" strings, sorted, one per occurrence.
	IdentifierViolations []string
	LiteralViolations    []string
	ImportViolations     []string

	// ImportsScanned is how many import specs the parser leg read. Positive
	// phrasing again: an import arm that reports zero violations over zero
	// imports has checked nothing, and every Go file in this module imports
	// something.
	ImportsScanned int

	// ScanErrors are malformed-source diagnostics from go/scanner. A file that
	// cannot be tokenised has NOT been checked, so these are violations of the
	// guard's own precondition and are reported as such rather than ignored.
	ScanErrors []string
}

// Violations is every reason the tree fails the rule, in a stable order.
func (c FloatingPointCensus) Violations() []string {
	out := make([]string, 0,
		len(c.ScanErrors)+len(c.IdentifierViolations)+len(c.LiteralViolations)+len(c.ImportViolations))
	out = append(out, c.ScanErrors...)
	out = append(out, c.IdentifierViolations...)
	out = append(out, c.LiteralViolations...)
	out = append(out, c.ImportViolations...)
	return out
}

// Summary is the positive sentence: what was inspected and what each count was.
func (c FloatingPointCensus) Summary() string {
	return fmt.Sprintf(
		"inspected %d Go packages / %d Go files / %d tokens / %d import specs under %s: %d forbidden identifiers, %d floating-point or imaginary literals, %d forbidden imports, %d unscannable files",
		c.PackagesScanned, c.FilesScanned, c.TokensScanned, c.ImportsScanned, c.Root,
		len(c.IdentifierViolations), len(c.LiteralViolations), len(c.ImportViolations), len(c.ScanErrors))
}

// ScanGoTreeForFloatingPoint tokenises every .go file ANYWHERE under root —
// recursively, at every nesting depth — and censuses the forbidden identifiers
// and the floating-point and imaginary LITERALS.
//
// RECURSION IS THE POINT, NOT AN IMPLEMENTATION DETAIL. A2-9's finding F-E
// measured two in-package scans built on `os.ReadDir(".")` that `continue` on
// `e.IsDir()`: a float in ANY subdirectory had zero coverage from either. This
// function uses filepath.WalkDir and descends, and its test plants a violation
// two directories deep to keep it that way.
//
// It returns an error only when the walk itself failed, when it scanned zero
// files, or when it scanned zero packages. A tree that scans clean returns a
// census whose counts a caller must still check — this function deliberately
// does not decide the verdict, because the test and the conformance run word it
// differently.
func ScanGoTreeForFloatingPoint(root string) (FloatingPointCensus, error) {
	c := FloatingPointCensus{Root: root}
	pkgDirs := map[string]bool{}
	err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		raw, rerr := os.ReadFile(path)
		if rerr != nil {
			return rerr
		}
		c.FilesScanned++
		dir := filepath.Dir(path)
		if rel, relErr := filepath.Rel(root, dir); relErr == nil {
			pkgDirs[filepath.ToSlash(rel)] = true
		} else {
			pkgDirs[filepath.ToSlash(dir)] = true
		}
		// THE IMPORT LEG (T166). Parsed, not grepped — see forbiddenImportPaths.
		// A file whose imports cannot be parsed has NOT been checked for them,
		// so that is recorded as a ScanError rather than skipped.
		pfset := token.NewFileSet()
		if af, perr := parser.ParseFile(pfset, path, raw, parser.ImportsOnly); perr != nil {
			c.ScanErrors = append(c.ScanErrors, fmt.Sprintf(
				"%s: the import block could not be parsed (%v), so this file has NOT been checked for "+
					"forbidden imports", path, perr))
		} else {
			for _, spec := range af.Imports {
				c.ImportsScanned++
				importPath, uerr := strconv.Unquote(spec.Path.Value)
				if uerr != nil {
					c.ScanErrors = append(c.ScanErrors, fmt.Sprintf(
						"%s: import path %s could not be unquoted (%v), so it has NOT been checked",
						pfset.Position(spec.Pos()), spec.Path.Value, uerr))
					continue
				}
				if why, bad := forbiddenImportPaths[importPath]; bad {
					c.ImportViolations = append(c.ImportViolations, fmt.Sprintf(
						"%s: forbidden import %q: %s (CLAUDE.md, first non-negotiable: money is integer "+
							"minor units and no floating-point value may appear on a money path, "+
							"including for intermediate calculation)",
						pfset.Position(spec.Pos()), importPath, why))
				}
			}
		}

		fset := token.NewFileSet()
		file := fset.AddFile(path, -1, len(raw))
		var sc scanner.Scanner
		sc.Init(file, raw, func(pos token.Position, msg string) {
			c.ScanErrors = append(c.ScanErrors,
				fmt.Sprintf("%s: could not be tokenised (%s), so it has NOT been checked for floating point", pos, msg))
		}, 0) // mode 0: comments are skipped entirely
		for {
			pos, tok, lit := sc.Scan()
			if tok == token.EOF {
				break
			}
			c.TokensScanned++
			switch {
			case tok == token.FLOAT || tok == token.IMAG:
				// THE T143/M-3 HOLE. A literal carries no identifier, so the
				// identifier arm below never sees it. `0.036`, `1e-4`, `3i` and
				// `0x1p-2` are all this token class.
				c.LiteralViolations = append(c.LiteralViolations, fmt.Sprintf(
					"%s: floating-point literal %q: money is integer minor units, and no floating-point value may "+
						"appear on a money path — including for intermediate calculation (CLAUDE.md, first non-negotiable)",
					fset.Position(pos), lit))
			case tok == token.IDENT && forbiddenFloatIdentifiers[lit]:
				c.IdentifierViolations = append(c.IdentifierViolations, fmt.Sprintf(
					"%s: identifier %q: no floating-point type may appear on a money path, "+
						"including for intermediate calculation", fset.Position(pos), lit))
			}
		}
		return nil
	})
	if err != nil {
		return c, fmt.Errorf("walking %s for the no-float census: %w", root, err)
	}
	for dir := range pkgDirs {
		c.PackageDirs = append(c.PackageDirs, dir)
	}
	sort.Strings(c.PackageDirs)
	c.PackagesScanned = len(c.PackageDirs)
	if c.FilesScanned == 0 || c.PackagesScanned == 0 {
		return c, fmt.Errorf(
			"the no-float census scanned %d Go packages / %d Go files under %s: a guard that inspects nothing "+
				"passes everything, so this is an ERROR and not a pass", c.PackagesScanned, c.FilesScanned, root)
	}
	sort.Strings(c.ScanErrors)
	sort.Strings(c.IdentifierViolations)
	sort.Strings(c.LiteralViolations)
	sort.Strings(c.ImportViolations)
	return c, nil
}
