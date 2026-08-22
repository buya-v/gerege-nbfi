// A2-31 PROBE — measure the population each of ledgerguard's SQL/builder/hold detection
// classes actually inspects on this tree. READ-ONLY: this program parses Go source and
// prints counts. It writes no file and mutates nothing.
//
// Why it exists: DEC-2 rev 4 §4.4.1 states `I4-BUILDER`'s population was "NOT established".
// P-67 says do not certify a ratio without counting both terms. This counts the term.
//
// The regexes, the callee-name resolution and the pruned-directory set are copied verbatim
// from .softhouse/guards/ledgerguard/main.go so the population measured here is the same
// population the guard walks.
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
	"strings"
)

var mutatingCallRe = regexp.MustCompile(`^(Update|Updates|UpdateAll|UpdateOne|UpdateMany|Delete|DeleteAll|DeleteOne|DeleteMany|Del|Remove|Truncate|Save|Upsert|SetColumn|Set)$`)
var mutatingExecRe = regexp.MustCompile(`^(Exec|ExecContext|MustExec|MustExecContext|SendBatch|CopyFrom|Prepare|PrepareContext)$`)
var holdFuncRe = regexp.MustCompile(`(^|[^A-Za-z])[Hh]old|[a-z0-9]Hold`)
var prunedDirs = map[string]bool{".git": true, "vendor": true, "node_modules": true}

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
	root := os.Args[1]
	fset := token.NewFileSet()
	files, calls, builder, execs, holds := 0, 0, 0, 0, 0
	hits := []string{}
	holdNames := []string{}
	names := map[string]int{}
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
		files++
		f, perr := parser.ParseFile(fset, path, nil, parser.ParseComments)
		if perr != nil {
			fmt.Println("PARSE ERROR", path, perr)
			return nil
		}
		ast.Inspect(f, func(n ast.Node) bool {
			switch t := n.(type) {
			case *ast.FuncDecl:
				if holdFuncRe.MatchString(t.Name.Name) {
					holds++
					p := fset.Position(t.Pos())
					rel, _ := filepath.Rel(root, p.Filename)
					holdNames = append(holdNames, fmt.Sprintf("%s:%d  %s", rel, p.Line, t.Name.Name))
				}
			case *ast.CallExpr:
				calls++
				name := calleeName(t.Fun)
				if mutatingExecRe.MatchString(name) {
					execs++
				}
				if mutatingCallRe.MatchString(name) {
					builder++
					names[name]++
					p := fset.Position(t.Pos())
					rel, _ := filepath.Rel(root, p.Filename)
					hits = append(hits, fmt.Sprintf("%s:%d  %s(...)", rel, p.Line, types.ExprString(t.Fun)))
				}
			}
			return true
		})
		return nil
	})
	if err != nil {
		fmt.Println("WALK ERROR", err)
		os.Exit(1)
	}
	fmt.Printf("root=%s\n", root)
	fmt.Printf("files=%d calls=%d\n", files, calls)
	fmt.Printf("OPAQUE-SQL population  (mutatingExecRe callee) = %d\n", execs)
	fmt.Printf("I4-BUILDER population  (mutatingCallRe callee) = %d\n", builder)
	fmt.Printf("I6-HOLD-BALANCE population (holdFuncRe funcdecl) = %d\n", holds)
	keys := []string{}
	for k := range names {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("  verb %-10s x%d\n", k, names[k])
	}
	sort.Strings(hits)
	for _, h := range hits {
		fmt.Println("    BUILDER-CALL", h)
	}
	for _, h := range holdNames {
		fmt.Println("    HOLD-FUNC", h)
	}
}
