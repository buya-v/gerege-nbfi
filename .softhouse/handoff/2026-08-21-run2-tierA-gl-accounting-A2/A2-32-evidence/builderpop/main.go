// Command builderpop measures the POPULATION class I4-BUILDER inspects under a given root,
// independently of A2-31's probe and of the guard binary itself.
//
// A2-32 wrote this to verify A2-31's F-2(b) rather than take it on report. The three
// load-bearing pieces are copied VERBATIM from .softhouse/guards/ledgerguard/main.go:
//
//   - mutatingCallRe        (main.go:151)
//   - calleeName            (main.go:406-418)
//   - prunedDirs + walk     (main.go:161, 692-731)
//
// I4-BUILDER's population is the set of *ast.CallExpr under the root whose calleeName matches
// mutatingCallRe — exactly the analogue of OPAQUE-SQL's population (mutating driver calls),
// which the guard itself declares empty in a NIL-COVERAGE line. Whether a member of the
// population then also mentionsProtected() is the FINDING test, not the population test.
//
// Controls printed: total .go files and total calls, which must reproduce the guard's own
// CENSUS line on the same tree. If they do not, this probe is walking a different population
// and its zero means nothing.
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// VERBATIM from ledgerguard/main.go:151
var mutatingCallRe = regexp.MustCompile(`^(Update|Updates|UpdateAll|UpdateOne|UpdateMany|Delete|DeleteAll|DeleteOne|DeleteMany|Del|Remove|Truncate|Save|Upsert|SetColumn|Set)$`)

// VERBATIM from ledgerguard/main.go:156
var mutatingExecRe = regexp.MustCompile(`^(Exec|ExecContext|MustExec|MustExecContext|SendBatch|CopyFrom|Prepare|PrepareContext)$`)

// VERBATIM from ledgerguard/main.go:161
var prunedDirs = map[string]bool{".git": true, "vendor": true, "node_modules": true}

// VERBATIM from ledgerguard/main.go:406-418
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

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: builderpop <root>")
		os.Exit(2)
	}
	root := os.Args[1]

	files, calls, builderPop, execPop := 0, 0, 0, 0
	var hits []string
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
		files++
		pkgs[filepath.ToSlash(filepath.Dir(rel))] = true

		f, perr := parser.ParseFile(fset, path, src, parser.ParseComments)
		if perr != nil {
			return fmt.Errorf("%s: parse: %w", rel, perr)
		}
		ast.Inspect(f, func(n ast.Node) bool {
			ce, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			calls++
			name := calleeName(ce.Fun)
			if mutatingCallRe.MatchString(name) {
				builderPop++
				q := fset.Position(ce.Pos())
				hits = append(hits, fmt.Sprintf("%s:%d:%d  %s", rel, q.Line, q.Column, name))
			}
			if mutatingExecRe.MatchString(name) {
				execPop++
			}
			return true
		})
		return nil
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, "walk:", err)
		os.Exit(1)
	}

	sort.Strings(hits)
	fmt.Printf("root                            %s\n", root)
	fmt.Printf("CONTROL files (.go)             %d\n", files)
	fmt.Printf("CONTROL packages                %d\n", len(pkgs))
	fmt.Printf("CONTROL calls (*ast.CallExpr)   %d\n", calls)
	fmt.Printf("POPULATION OPAQUE-SQL  (mutatingExecRe)  %d\n", execPop)
	fmt.Printf("POPULATION I4-BUILDER  (mutatingCallRe)  %d\n", builderPop)
	for _, h := range hits {
		fmt.Printf("  I4-BUILDER population member: %s\n", h)
	}
}
