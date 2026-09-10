// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/briefs/tools/reachguard.sh
//
// reachguard — LEG 2: the go/types reachability discriminator for I3 balance writes.
//
// WHAT THIS IS. `ledgerguard` decides whether a balance-named field is WRITTEN by looking at
// syntax and names. It cannot follow a value INTO a store, because doing that needs a type
// checker (T509 CANNOT-CATCH item 10, stated at ledgerguard/main.go:1351-1360). This program
// is the missing follow: for a write site it asks exactly one question —
//
//	does the value written here reach a PERSISTENCE BOUNDARY?
//
// where a persistence boundary is a journal entry, a GL posting, or a column any aggregate
// reads as an account balance.
//
// THE HARD DESIGN CONSTRAINT (T514; ledgerguard/main.go:1356): THE ANALYSIS MUST FAIL CLOSED
// ON UNRESOLVED VALUE FLOW. A tool that answers "not persisted" on an edge it cannot resolve
// reintroduces the same fail-open one layer up, and — unlike a waiver, which is a visible
// document a human must amend — a heuristic's failure produces NO ARTEFACT AT ALL. So every
// site gets exactly one of three verdicts, never two:
//
//	REACHES-PERSISTENCE   a RESOLVED path to a boundary. The finding is REAL.
//	UNRESOLVED            an edge the type checker cannot resolve. THIS IS THE DEFAULT.
//	PROVABLY-NO-PERSISTENCE  the FULL closure resolved and none reaches a boundary. Only this
//	                      verdict can clear a red, and only with the closure printed.
//
// if any edge in the closure is unresolved the whole site is UNRESOLVED, even if no path
// reaches a boundary. An `interface` method with more than one implementation in scope, a
// func value, a reflect call, a closure escaping into a field, an `any`-typed hop, a cgo or
// generated boundary — each is UNRESOLVED by construction, and reaching one taints every site
// whose flow it is on.
//
// BOUNDARIES ARE TYPES AND OBJECTS, NEVER STRINGS. The predecessor proposal keyed the
// persistence SURFACE on path/filename/package name and was MEASURED defeated by a single
// `git mv` of a real savings balance write into a subdirectory (T505 MAJOR-1). This program
// resolves the module through golang.org/x/tools/go/packages with
// NeedTypes|NeedSyntax|NeedTypesInfo|NeedDeps and identifies the driver seam by the RECEIVER'S
// TYPE (pgx / database/sql method objects, and this tree's platform/postgres Exec/Query
// objects) and the journal-entry/GL-posting types by their types.Object identity. Moving a
// file changes neither, so a verdict cannot move when a file moves.
//
// WHAT THIS PROGRAM DOES NOT DO, STATED SO IT IS NOT MISTAKEN FOR COVERAGE.
//   - It does not decide the four loanproduct sites by fiat. It runs the closure and reports
//     what the closure actually resolves.
//   - A driver call whose SQL it cannot resolve is UNRESOLVED, never acquitted.
//   - It answers the WRITE question only. DEC-2 §4.4 item 9: a balance READ is not a write
//     path, and raising a read to a refusal is a DEC-n amendment routed as a `user` gate.
//
// Usage:
//
//	reachguard --root <module dir> [--sites <file>] [--json]
//
// Exit: 0 every site PROVABLY-NO-PERSISTENCE; 1 at least one site REACHES or UNRESOLVED
// (i.e. the red stands); 2 unusable (does not compile / cannot load / selector empty) —
// never a pass.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/constant"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"golang.org/x/tools/go/packages"
)

// ---------------------------------------------------------------------------------------------
// Verdicts
// ---------------------------------------------------------------------------------------------

type Verdict int

const (
	Reaches Verdict = iota
	Unresolved
	ProvablyNo
)

func (v Verdict) String() string {
	switch v {
	case Reaches:
		return "REACHES-PERSISTENCE"
	case Unresolved:
		return "UNRESOLVED"
	case ProvablyNo:
		return "PROVABLY-NO-PERSISTENCE"
	}
	return "?"
}

type cause struct {
	Pos    token.Position
	Reason string
}

func (c cause) String() string {
	return fmt.Sprintf("%s: %s", c.Pos, c.Reason)
}

// ---------------------------------------------------------------------------------------------
// The value-flow graph. A node is an abstract location (a variable/parameter/result, a struct
// field, a container element, a composite literal, a call result). Edges are RESOLVED flows.
// `unresolved` records, per node, flows the builder could not resolve; reaching such a node
// makes a site UNRESOLVED. `sinks` records, per node, a boundary the value reaches.
// ---------------------------------------------------------------------------------------------

type nodeInfo struct {
	Key   string
	Label string
	Type  types.Type
	Pos   token.Pos
}

type graph struct {
	fset       *token.FileSet
	nodes      map[string]*nodeInfo
	edges      map[string]map[string]struct{}
	rev        map[string]map[string]struct{}
	unresolved map[string][]cause
	sinks      map[string][]cause
	stringVals map[string]map[string]struct{}
}

func newGraph(fset *token.FileSet) *graph {
	return &graph{
		fset:       fset,
		nodes:      map[string]*nodeInfo{},
		edges:      map[string]map[string]struct{}{},
		rev:        map[string]map[string]struct{}{},
		unresolved: map[string][]cause{},
		sinks:      map[string][]cause{},
		stringVals: map[string]map[string]struct{}{},
	}
}

func (g *graph) ensure(key, label string, t types.Type, pos token.Pos) string {
	if _, ok := g.nodes[key]; !ok {
		g.nodes[key] = &nodeInfo{Key: key, Label: label, Type: t, Pos: pos}
	}
	return key
}

func (g *graph) addEdge(from, to string) {
	if from == "" || to == "" || from == to {
		return
	}
	m, ok := g.edges[from]
	if !ok {
		m = map[string]struct{}{}
		g.edges[from] = m
	}
	m[to] = struct{}{}
	r, ok := g.rev[to]
	if !ok {
		r = map[string]struct{}{}
		g.rev[to] = r
	}
	r[from] = struct{}{}
}

func (g *graph) addUnresolved(node, reason string, pos token.Pos) {
	if node == "" {
		return
	}
	g.unresolved[node] = append(g.unresolved[node], cause{Pos: g.fset.Position(pos), Reason: reason})
}

func (g *graph) addSink(node, reason string, pos token.Pos) {
	if node == "" {
		return
	}
	g.sinks[node] = append(g.sinks[node], cause{Pos: g.fset.Position(pos), Reason: reason})
}

func (g *graph) addString(node, val string) {
	if node == "" {
		return
	}
	m, ok := g.stringVals[node]
	if !ok {
		m = map[string]struct{}{}
		g.stringVals[node] = m
	}
	m[val] = struct{}{}
}

// ---------------------------------------------------------------------------------------------
// The analyzer
// ---------------------------------------------------------------------------------------------

type analyzer struct {
	fset    *token.FileSet
	pkgs    []*packages.Package
	allPkgs []*packages.Package

	modulePath string
	g          *graph

	fileInfo map[string]*types.Info // fset filename -> type info

	// function bodies and their return expressions, keyed by the declared object
	funcBody   map[*types.Func]*ast.BlockStmt
	funcReturn map[*types.Func][]ast.Expr

	// method implementation index over the module's own named types
	implIndex map[string][]*types.Func // method name -> concrete methods (module only)

	// persistence seam, resolved by types.Object identity — never by a name match on nexus code.
	driverObjects map[*types.Func]bool // driver/seam methods and functions
	persistFuncs  map[*types.Func]bool // module funcs that (transitively) reach a driver object
	boundaryTypes map[types.Type]bool  // named types carried into the seam, keyed by identity
	seamNotes     []string             // object-identity resolutions that FAILED, reported loudly

	// seamBroken is set when the tree's own persistence seam was FOUND but an object in it did
	// not resolve (a renamed/removed DB/Querier/Executor/InsertReturningInt64/QueryRows). The
	// boundary set is then incomplete, so NO site may be reported PROVABLY-NO-PERSISTENCE: an
	// incomplete boundary set is exactly the fail-open the three-verdict rule exists to prevent.
	// This is fail-closed at the boundary layer as well as at the flow layer (T514).
	seamBroken bool

	callDone map[token.Pos]bool
	litDone  map[token.Pos]bool

	currentFunc *types.Func
}

func newAnalyzer(fset *token.FileSet) *analyzer {
	return &analyzer{
		fset:          fset,
		g:             newGraph(fset),
		fileInfo:      map[string]*types.Info{},
		funcBody:      map[*types.Func]*ast.BlockStmt{},
		funcReturn:    map[*types.Func][]ast.Expr{},
		implIndex:     map[string][]*types.Func{},
		driverObjects: map[*types.Func]bool{},
		persistFuncs:  map[*types.Func]bool{},
		boundaryTypes: map[types.Type]bool{},
		callDone:      map[token.Pos]bool{},
		litDone:       map[token.Pos]bool{},
	}
}

// ---------------------------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------------------------

func load(root string) ([]*packages.Package, *token.FileSet, error) {
	fset := token.NewFileSet()
	cfg := &packages.Config{
		Mode: packages.NeedName | packages.NeedFiles | packages.NeedImports |
			packages.NeedTypes | packages.NeedSyntax | packages.NeedTypesInfo |
			packages.NeedDeps | packages.NeedModule,
		Dir:  root,
		Fset: fset,
		// The analyser resolves SSA-free name/object identity itself; it does not need the source
		// of test variants, but test files are part of the module's type graph and their absence
		// can change interface-implementation counts (the fail-closed closure), so include them.
		Tests: true,
	}
	pkgs, err := packages.Load(cfg, "./...")
	if err != nil {
		return nil, nil, err
	}
	if packages.PrintErrors(pkgs) > 0 {
		return nil, nil, fmt.Errorf("the target module did not type-check")
	}
	return pkgs, fset, nil
}

func (a *analyzer) prepare(pkgs []*packages.Package) {
	a.pkgs = pkgs
	// The target module's path comes from the ROOT packages only. A transitive dependency can
	// be visited first and carries its own Module, so taking the first non-nil Module during
	// the visit would silently make the module filter match nothing.
	for _, p := range pkgs {
		if p.Module != nil && p.Module.Path != "" {
			a.modulePath = p.Module.Path
			break
		}
	}
	packages.Visit(pkgs, nil, func(p *packages.Package) {
		a.allPkgs = append(a.allPkgs, p)
		if p.TypesInfo != nil {
			for _, f := range p.Syntax {
				a.fileInfo[a.fset.File(f.Pos()).Name()] = p.TypesInfo
			}
		}
	})
	if a.modulePath == "" {
		for _, p := range a.allPkgs {
			if p.Module != nil && p.Module.Path != "" {
				a.modulePath = p.Module.Path
				break
			}
		}
	}
	a.indexFunctions()
	a.indexImpls()
	a.indexBoundaries()
}

func (a *analyzer) infoFor(pos token.Pos) *types.Info {
	f := a.fset.File(pos)
	if f == nil {
		return nil
	}
	return a.fileInfo[f.Name()]
}

func (a *analyzer) inModule(p *packages.Package) bool {
	return a.modulePath != "" && (p.PkgPath == a.modulePath || strings.HasPrefix(p.PkgPath, a.modulePath+"/"))
}

func (a *analyzer) indexFunctions() {
	for _, p := range a.allPkgs {
		if p.TypesInfo == nil || !a.inModule(p) {
			continue
		}
		for _, f := range p.Syntax {
			for _, d := range f.Decls {
				fd, ok := d.(*ast.FuncDecl)
				if !ok || fd.Body == nil {
					continue
				}
				obj, _ := p.TypesInfo.Defs[fd.Name].(*types.Func)
				if obj == nil {
					continue
				}
				a.funcBody[obj] = fd.Body
				a.collectReturns(obj, fd.Body)
			}
		}
	}
}

// collectReturns walks a function body (including nested func literals) and records the
// expressions of every `return` that belongs to the TOP-LEVEL function. Nested closures get
// their own synthetic key, but their returns are not attributed to the enclosing function.
func (a *analyzer) collectReturns(fn *types.Func, body *ast.BlockStmt) {
	var walk func(n ast.Node)
	walk = func(n ast.Node) {
		ast.Inspect(n, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.FuncLit:
				return false // a nested closure's returns are not this function's
			case *ast.ReturnStmt:
				a.funcReturn[fn] = append(a.funcReturn[fn], x.Results...)
			}
			return true
		})
	}
	walk(body)
}

// indexImpls builds, for the module's own concrete named types, an index from method NAME to
// the concrete method objects. A single match resolves an interface call; zero or more than
// one is UNRESOLVED (T514's explicit rule: "an interface method with more than one
// implementation in scope").
func (a *analyzer) indexImpls() {
	for _, p := range a.allPkgs {
		if !a.inModule(p) || p.Types == nil {
			continue
		}
		scope := p.Types.Scope()
		for _, name := range scope.Names() {
			obj := scope.Lookup(name)
			tn, ok := obj.(*types.TypeName)
			if !ok {
				continue
			}
			named, ok := tn.Type().(*types.Named)
			if !ok {
				continue
			}
			if _, isIface := named.Underlying().(*types.Interface); isIface {
				continue
			}
			ms := types.NewMethodSet(named)
			for i := 0; i < ms.Len(); i++ {
				sel := ms.At(i)
				f, ok := sel.Obj().(*types.Func)
				if !ok {
					continue
				}
				a.implIndex[f.Name()] = append(a.implIndex[f.Name()], f)
			}
		}
	}
}

// indexBoundaries resolves the persistence seam by types.Object identity. It never matches a
// filename, a directory or a type NAME in nexus code: the driver methods are the method sets of
// the driver packages, the tree's SQL seam is the method set of its own interface OBJECTS
// (looked up in the seam package's scope, so a rename fails loudly), and the boundary TYPES are
// derived from the parameters of functions that actually reach a driver object.
func (a *analyzer) indexBoundaries() {
	a.driverObjects = map[*types.Func]bool{}

	// (a) external driver packages. driver methods are identified by the identity of the
	// package that defines them (database/sql, jackc/pgx), then by method-set membership.
	for _, p := range a.allPkgs {
		if p.Types == nil || !isExternalDriverPkg(p.PkgPath) {
			continue
		}
		scope := p.Types.Scope()
		for _, name := range scope.Names() {
			tn, ok := scope.Lookup(name).(*types.TypeName)
			if !ok {
				continue
			}
			for _, t := range []types.Type{tn.Type(), types.NewPointer(tn.Type())} {
				ms := types.NewMethodSet(t)
				for i := 0; i < ms.Len(); i++ {
					if f, ok := ms.At(i).Obj().(*types.Func); ok && isDriverMethodName(f.Name()) {
						a.driverObjects[f] = true
					}
				}
			}
		}
	}

	// (b) the tree's own SQL seam: resolve the interface and function OBJECTS in the seam
	// package's scope. If the package is present but an object is gone, that is a seam
	// resolution FAILURE and it is reported (never silently treated as "no boundary").
	for _, p := range a.allPkgs {
		if p.Types == nil || !isSeamPkg(p.PkgPath) {
			continue
		}
		scope := p.Types.Scope()
		for _, nm := range []string{"DB", "Querier", "Executor"} {
			tn, ok := scope.Lookup(nm).(*types.TypeName)
			if !ok {
				a.seamNotes = append(a.seamNotes, "seam "+p.PkgPath+"."+nm+" is gone")
				continue
			}
			iface, ok := tn.Type().Underlying().(*types.Interface)
			if !ok {
				a.seamNotes = append(a.seamNotes, "seam "+p.PkgPath+"."+nm+" is no longer an interface")
				continue
			}
			for i := 0; i < iface.NumMethods(); i++ {
				a.driverObjects[iface.Method(i)] = true
			}
		}
		for _, nm := range []string{"InsertReturningInt64", "QueryRows"} {
			if f, ok := scope.Lookup(nm).(*types.Func); ok {
				a.driverObjects[f] = true
			} else {
				a.seamNotes = append(a.seamNotes, "seam "+p.PkgPath+"."+nm+" is gone")
			}
		}
	}

	// (c) module funcs that (transitively) reach a driver object — the tree's SQL wrappers,
	// discovered by the call graph, not by their names or their parameters' names.
	a.persistFuncs = map[*types.Func]bool{}
	for changed := true; changed; {
		changed = false
		for fn, body := range a.funcBody {
			if a.persistFuncs[fn] {
				continue
			}
			if a.bodyReachesDriver(body) {
				a.persistFuncs[fn] = true
				changed = true
			}
		}
	}

	// (d) boundary types are the named struct types carried by persistence functions. Derived
	// from the objects, not from their names: whatever a writer sends into the seam is a
	// boundary, even if it is not spelled JournalEntry.
	a.boundaryTypes = map[types.Type]bool{}
	for fn := range a.persistFuncs {
		sig, ok := fn.Type().(*types.Signature)
		if !ok {
			continue
		}
		if sig.Recv() != nil {
			collectNamedStructs(sig.Recv().Type(), a.boundaryTypes)
		}
		for i := 0; i < sig.Params().Len(); i++ {
			collectNamedStructs(sig.Params().At(i).Type(), a.boundaryTypes)
		}
	}

	// A seam that was found but did not fully resolve leaves the boundary set incomplete. Mark
	// the analysis broken so the site loop cannot return PROVABLY-NO-PERSISTENCE from it.
	if len(a.seamNotes) > 0 {
		a.seamBroken = true
	}
}

func (a *analyzer) bodyReachesDriver(body *ast.BlockStmt) bool {
	found := false
	ast.Inspect(body, func(n ast.Node) bool {
		if found {
			return false
		}
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		fn, _, kind, _ := a.resolveCallee(call)
		if kind == resolveStatic && fn != nil && (a.driverObjects[fn] || a.persistFuncs[fn]) {
			found = true
			return false
		}
		return true
	})
	return found
}

func collectNamedStructs(t types.Type, out map[types.Type]bool) {
	if t == nil {
		return
	}
	switch u := t.Underlying().(type) {
	case *types.Pointer:
		collectNamedStructs(u.Elem(), out)
	case *types.Slice:
		collectNamedStructs(u.Elem(), out)
	case *types.Array:
		collectNamedStructs(u.Elem(), out)
	case *types.Map:
		collectNamedStructs(u.Elem(), out)
	case *types.Struct:
		if n, ok := t.(*types.Named); ok {
			out[n] = true
		}
	}
}

func isExternalDriverPkg(p string) bool {
	return p == "database/sql" || strings.Contains(p, "jackc/pgx")
}

func isSeamPkg(p string) bool {
	return strings.HasSuffix(p, "/internal/platform/postgres")
}

// ---------------------------------------------------------------------------------------------
// Node keys
// ---------------------------------------------------------------------------------------------

func (a *analyzer) varNode(v *types.Var) string {
	if v == nil {
		return ""
	}
	if v.IsField() {
		key := fmt.Sprintf("f#%d#%s", v.Pos(), v.Name())
		return a.g.ensure(key, "field "+v.Name(), v.Type(), v.Pos())
	}
	key := fmt.Sprintf("v#%d#%s", v.Pos(), v.Name())
	if v.Pkg() != nil {
		key = fmt.Sprintf("v#%s#%d#%s", v.Pkg().Path(), v.Pos(), v.Name())
	}
	return a.g.ensure(key, "var "+v.Name(), v.Type(), v.Pos())
}

func (a *analyzer) fieldNode(v *types.Var) string {
	if v == nil {
		return ""
	}
	key := fmt.Sprintf("f#%d#%s", v.Pos(), v.Name())
	return a.g.ensure(key, "field "+v.Name(), v.Type(), v.Pos())
}

func (a *analyzer) litNode(lit *ast.CompositeLit) string {
	t := a.typeOf(lit)
	key := fmt.Sprintf("c#%d", lit.Pos())
	return a.g.ensure(key, "composite "+typeStr(t), t, lit.Pos())
}

func (a *analyzer) resultNode(call *ast.CallExpr) string {
	t := a.typeOf(call)
	key := fmt.Sprintf("r#%d", call.Pos())
	return a.g.ensure(key, "result of call", t, call.Pos())
}

func (a *analyzer) elemNode(t types.Type) string {
	if t == nil {
		return ""
	}
	elem := elementType(t)
	if elem == nil {
		return ""
	}
	key := fmt.Sprintf("e#%s", types.TypeString(t, nil))
	return a.g.ensure(key, "element of "+typeStr(t), elem, token.NoPos)
}

func (a *analyzer) unknownNode(pos token.Pos, label string) string {
	key := fmt.Sprintf("u#%d#%s", pos, label)
	return a.g.ensure(key, "unknown "+label, nil, pos)
}

func typeStr(t types.Type) string {
	if t == nil {
		return "<nil>"
	}
	return types.TypeString(t, nil)
}

func elementType(t types.Type) types.Type {
	switch u := t.Underlying().(type) {
	case *types.Slice:
		return u.Elem()
	case *types.Array:
		return u.Elem()
	case *types.Map:
		return u.Elem()
	case *types.Chan:
		return u.Elem()
	}
	return nil
}

func deref(t types.Type) types.Type {
	if p, ok := t.Underlying().(*types.Pointer); ok {
		return p.Elem()
	}
	return t
}

func (a *analyzer) typeOf(e ast.Expr) types.Type {
	info := a.infoFor(e.Pos())
	if info == nil {
		return nil
	}
	return info.Types[e].Type
}

func (a *analyzer) isBoundary(t types.Type) bool {
	if t == nil {
		return false
	}
	if a.boundaryTypes[t] {
		return true
	}
	switch u := t.Underlying().(type) {
	case *types.Pointer:
		return a.isBoundary(u.Elem())
	case *types.Slice:
		return a.isBoundary(u.Elem())
	case *types.Array:
		return a.isBoundary(u.Elem())
	case *types.Map:
		return a.isBoundary(u.Elem())
	}
	return false
}

// ---------------------------------------------------------------------------------------------
// Building the graph
// ---------------------------------------------------------------------------------------------

func (a *analyzer) build() {
	for _, p := range a.allPkgs {
		if p.TypesInfo == nil || !a.inModule(p) {
			continue
		}
		for _, f := range p.Syntax {
			for _, d := range f.Decls {
				switch x := d.(type) {
				case *ast.FuncDecl:
					if x.Body == nil {
						continue
					}
					obj, _ := p.TypesInfo.Defs[x.Name].(*types.Func)
					if obj == nil {
						continue
					}
					a.currentFunc = obj
					a.walkBody(x.Body)
				case *ast.GenDecl:
					a.processGenDecl(p.TypesInfo, x)
				}
			}
		}
	}
	a.propagateStrings()
}

// walkBody processes one function body. Nested func literals are processed as captures: a
// value captured by a closure can escape through it, so the captured variable is marked
// UNRESOLVED rather than followed.
func (a *analyzer) walkBody(body *ast.BlockStmt) {
	outer := a.currentFunc
	ast.Inspect(body, func(n ast.Node) bool {
		switch x := n.(type) {
		case *ast.FuncLit:
			a.processFuncLit(x)
			return false
		case *ast.AssignStmt:
			a.processAssign(x)
		case *ast.ReturnStmt:
			for _, r := range x.Results {
				a.emit(r)
			}
		case *ast.RangeStmt:
			a.processRange(x)
		case *ast.GoStmt:
			a.processCall(x.Call)
			for _, arg := range x.Call.Args {
				for _, n := range a.emit(arg) {
					a.g.addUnresolved(n, "value passed to a goroutine (concurreny boundary)", x.Pos())
				}
			}
		case *ast.DeferStmt:
			a.processCall(x.Call)
			for _, arg := range x.Call.Args {
				for _, n := range a.emit(arg) {
					a.g.addUnresolved(n, "value passed to a deferred call (deferred evaluation boundary)", x.Pos())
				}
			}
		case *ast.CallExpr:
			a.processCall(x)
		case *ast.CompositeLit:
			a.processLit(x)
		case *ast.TypeAssertExpr:
			for _, n := range a.emit(x.X) {
				a.g.addUnresolved(n, "value flows through a type assertion", x.Pos())
			}
		}
		return true
	})
	a.currentFunc = outer
}

func (a *analyzer) processFuncLit(lit *ast.FuncLit) {
	info := a.infoFor(lit.Pos())
	if info == nil {
		return
	}
	// Captures: every identifier resolving to a variable declared OUTSIDE the literal's
	// extent is captured. A captured value can escape through the closure; mark it unresolved.
	ast.Inspect(lit.Body, func(n ast.Node) bool {
		id, ok := n.(*ast.Ident)
		if !ok {
			return true
		}
		v, ok := info.Uses[id].(*types.Var)
		if !ok || v.IsField() {
			return true
		}
		if v.Pos() < lit.Pos() || v.Pos() > lit.End() {
			node := a.varNode(v)
			a.g.addUnresolved(node, "value captured by a closure (escape boundary)", id.Pos())
		}
		return true
	})
	// Process the literal body as its own function context (its locals are keyed by position, so
	// this does not collide with the enclosing function).
	outer := a.currentFunc
	a.currentFunc = nil
	a.walkBody(lit.Body)
	a.currentFunc = outer
}

func (a *analyzer) processGenDecl(info *types.Info, gd *ast.GenDecl) {
	if gd.Tok != token.VAR && gd.Tok != token.CONST {
		return
	}
	for _, spec := range gd.Specs {
		vs, ok := spec.(*ast.ValueSpec)
		if !ok {
			continue
		}
		for i, name := range vs.Names {
			v, _ := info.Defs[name].(*types.Var)
			if v == nil {
				continue
			}
			target := a.varNode(v)
			if i < len(vs.Values) {
				a.bindValues([]string{target}, vs.Values[i], vs.Values[i].Pos())
			} else if len(vs.Values) == 1 {
				a.bindValues([]string{target}, vs.Values[0], vs.Values[0].Pos())
			}
		}
	}
}

func (a *analyzer) processAssign(st *ast.AssignStmt) {
	if len(st.Lhs) == len(st.Rhs) {
		for i := range st.Lhs {
			targets := a.targets(st.Lhs[i])
			a.bindValues(targets, st.Rhs[i], st.Pos())
		}
		return
	}
	if len(st.Rhs) == 1 {
		// tuple assignment, e.g. a, b := f()
		a.emit(st.Rhs[0])
		src := a.valueNodes(st.Rhs[0])
		for i := range st.Lhs {
			for _, t := range a.targets(st.Lhs[i]) {
				for _, s := range src {
					a.g.addEdge(s, t)
				}
			}
		}
		return
	}
	for i := range st.Lhs {
		if i < len(st.Rhs) {
			a.bindValues(a.targets(st.Lhs[i]), st.Rhs[i], st.Pos())
		}
	}
}

func (a *analyzer) bindValues(targets []string, rhs ast.Expr, pos token.Pos) {
	src := a.valueNodes(rhs)
	if lit, ok := rhs.(*ast.CompositeLit); ok {
		a.processLit(lit)
		src = append(src, a.litNode(lit))
	}
	for _, t := range targets {
		tt := a.nodeType(t)
		for _, s := range src {
			a.g.addEdge(s, t)
			if a.isBoundary(tt) {
				a.g.addSink(s, "value written into boundary type "+typeStr(tt), pos)
			}
			if tt != nil && types.IsInterface(tt.Underlying()) {
				a.g.addUnresolved(s, "value stored in interface type "+typeStr(tt)+" (an any-typed hop)", pos)
			}
		}
	}
	if s, ok := stringLiteral(rhs); ok {
		for _, t := range targets {
			a.g.addString(t, s)
		}
	}
}

func (a *analyzer) nodeType(key string) types.Type {
	if n, ok := a.g.nodes[key]; ok {
		return n.Type
	}
	return nil
}

func (a *analyzer) processRange(st *ast.RangeStmt) {
	t := a.typeOf(st.X)
	if t == nil {
		return
	}
	elem := a.elemNode(t)
	keyT := keyType(t)
	if st.Key != nil {
		if keyT == nil {
			for _, n := range a.emit(st.Key) {
				a.g.addUnresolved(n, "range key over an unresolved container type", st.Pos())
			}
		} else if v, ok := a.identVar(st.Key); ok && v != nil {
			a.g.addEdge(a.elemNodeOf(keyT), a.varNode(v))
		}
	}
	if st.Value != nil {
		if elem == "" {
			for _, n := range a.emit(st.Value) {
				a.g.addUnresolved(n, "range value over an unresolved container type", st.Pos())
			}
		} else if v, ok := a.identVar(st.Value); ok && v != nil {
			a.g.addEdge(elem, a.varNode(v))
		}
	}
	// iterating a map with interface keys/values is a dynamic boundary
	if _, isMap := t.Underlying().(*types.Map); isMap {
		a.g.addUnresolved(elem, "range over a map (dynamic container)", st.Pos())
	}
}

func (a *analyzer) elemNodeOf(t types.Type) string {
	key := fmt.Sprintf("e#%s", types.TypeString(t, nil))
	return a.g.ensure(key, "element of "+typeStr(t), t, token.NoPos)
}

func keyType(t types.Type) types.Type {
	if m, ok := t.Underlying().(*types.Map); ok {
		return m.Key()
	}
	return nil
}

func (a *analyzer) identVar(e ast.Expr) (*types.Var, bool) {
	id, ok := e.(*ast.Ident)
	if !ok {
		return nil, false
	}
	info := a.infoFor(id.Pos())
	if info == nil {
		return nil, false
	}
	v, ok := info.Uses[id].(*types.Var)
	if !ok {
		return nil, false
	}
	return v, true
}

// ---------------------------------------------------------------------------------------------
// Expression -> source locations
// ---------------------------------------------------------------------------------------------

// binaryValueNodes models a *ast.BinaryExpr. A binary expression's value is DERIVED from BOTH
// operands, so its flow is the UNION of the operands' flows: `a + b` reaches a boundary iff `a`
// or `b` does. This is union, never intersection — returning BOTH operand node sets means a
// resolved sink on either operand is found, and an operand that is itself unresolved carries its
// cause into the result's provenance so the site stays UNRESOLVED. The binary expression adds no
// flow of its own and no unresolved edge of its own.
//
// Modelled for the arithmetic/bitwise, comparison and logical operators. For a comparison the
// result is a bool that does not carry the amount, so union is an over-approximation there too;
// over-approximation can only add flow (turning a clear into a refusal), never remove it, so it
// cannot turn an unresolved edge into a clear. Any operator outside the set below stays
// UNRESOLVED rather than guessed.
func (a *analyzer) binaryValueNodes(x *ast.BinaryExpr) []string {
	if !isModelledBinaryOp(x.Op) {
		n := a.unknownNode(x.Pos(), "unmodelled-binary-op")
		a.g.addUnresolved(n, fmt.Sprintf("unmodelled binary operator %s", x.Op), x.Pos())
		return []string{n}
	}
	out := a.valueNodes(x.X)
	out = append(out, a.valueNodes(x.Y)...)
	return out
}

func isModelledBinaryOp(op token.Token) bool {
	switch op {
	case token.ADD, token.SUB, token.MUL, token.QUO, token.REM,
		token.AND, token.OR, token.XOR, token.SHL, token.SHR, token.AND_NOT,
		token.EQL, token.NEQ, token.LSS, token.LEQ, token.GTR, token.GEQ,
		token.LAND, token.LOR:
		return true
	}
	return false
}

// valueNodes returns the set of locations whose current value is the value of expr. It is the
// forward half of the flow relation. Anything it cannot model yields an "unknown" node, whose
// taint is UNRESOLVED.
func (a *analyzer) valueNodes(e ast.Expr) []string {
	switch x := e.(type) {
	case *ast.ParenExpr:
		return a.valueNodes(x.X)
	case *ast.Ident:
		return a.identNodes(x)
	case *ast.SelectorExpr:
		if info := a.infoFor(x.Pos()); info != nil {
			if s, ok := info.Selections[x]; ok && s.Kind() == types.MethodVal {
				// a method value captures its receiver: dynamic dispatch, unresolved by construction
				for _, r := range a.valueNodes(x.X) {
					a.g.addUnresolved(r, "method value captures its receiver (dynamic dispatch)", x.Pos())
				}
				n := a.unknownNode(x.Pos(), "method-value")
				a.g.addUnresolved(n, "a method value escapes (dynamic dispatch)", x.Pos())
				return []string{n}
			}
		}
		return a.selectorNodes(x)
	case *ast.StarExpr:
		n := a.unknownNode(x.Pos(), "deref-value")
		a.g.addUnresolved(n, "value flows through a pointer dereference (points-to not resolved)", x.Pos())
		return []string{n}
	case *ast.UnaryExpr:
		if x.Op == token.AND {
			return a.valueNodes(x.X)
		}
		return nil
	case *ast.CompositeLit:
		return []string{a.litNode(x)}
	case *ast.CallExpr:
		return []string{a.resultNode(x)}
	case *ast.IndexExpr:
		return []string{a.elemNode(a.typeOf(x.X))}
	case *ast.IndexListExpr:
		return []string{a.elemNode(a.typeOf(x.X))}
	case *ast.SliceExpr:
		return a.valueNodes(x.X)
	case *ast.TypeAssertExpr:
		n := a.unknownNode(x.Pos(), "type-assertion")
		a.g.addUnresolved(n, "value flows through a type assertion", x.Pos())
		return []string{n}
	case *ast.BinaryExpr:
		return a.binaryValueNodes(x)
	case *ast.BasicLit:
		return nil
	case *ast.FuncLit:
		n := a.unknownNode(x.Pos(), "func-literal-value")
		a.g.addUnresolved(n, "a closure value escapes (a func value the checker cannot resolve)", x.Pos())
		return []string{n}
	case *ast.FuncType:
		return nil
	default:
		n := a.unknownNode(e.Pos(), "unmodelled-expr")
		a.g.addUnresolved(n, fmt.Sprintf("unmodelled expression %T", e), e.Pos())
		return []string{n}
	}
}

// emit additionally processes any calls reachable in expr, then returns the same nodes.
func (a *analyzer) emit(e ast.Expr) []string {
	ast.Inspect(e, func(n ast.Node) bool {
		switch x := n.(type) {
		case *ast.CallExpr:
			a.processCall(x)
		case *ast.CompositeLit:
			a.processLit(x)
		}
		return true
	})
	return a.valueNodes(e)
}

func (a *analyzer) identNodes(id *ast.Ident) []string {
	if id.Name == "_" {
		return nil
	}
	info := a.infoFor(id.Pos())
	if info == nil {
		return nil
	}
	switch obj := info.Uses[id].(type) {
	case *types.Var:
		return []string{a.varNode(obj)}
	case *types.Func:
		return []string{a.funcValueNode(obj)}
	case *types.Const:
		return nil
	case *types.TypeName:
		return nil
	default:
		return nil
	}
}

func (a *analyzer) funcValueNode(fn *types.Func) string {
	key := fmt.Sprintf("fn#%s#%d#%s", pkgPath(fn), fn.Pos(), fn.Name())
	return a.g.ensure(key, "func "+fn.Name(), fn.Type(), fn.Pos())
}

func (a *analyzer) selectorNodes(sel *ast.SelectorExpr) []string {
	info := a.infoFor(sel.Pos())
	if info == nil {
		return nil
	}
	if s, ok := info.Selections[sel]; ok {
		switch obj := s.Obj().(type) {
		case *types.Var:
			if obj.IsField() {
				return []string{a.fieldNode(obj)}
			}
			return []string{a.varNode(obj)}
		case *types.Func:
			return []string{a.funcValueNode(obj)}
		}
	}
	switch obj := info.Uses[sel.Sel].(type) {
	case *types.Var:
		if obj.IsField() {
			return []string{a.fieldNode(obj)}
		}
		return []string{a.varNode(obj)}
	case *types.Func:
		return []string{a.funcValueNode(obj)}
	}
	return nil
}

// ---------------------------------------------------------------------------------------------
// Assignment targets
// ---------------------------------------------------------------------------------------------

func (a *analyzer) targets(e ast.Expr) []string {
	switch x := e.(type) {
	case *ast.ParenExpr:
		return a.targets(x.X)
	case *ast.Ident:
		if x.Name == "_" {
			return nil
		}
		info := a.infoFor(x.Pos())
		if info == nil {
			return nil
		}
		if v, ok := info.Defs[x].(*types.Var); ok {
			return []string{a.varNode(v)}
		}
		if v, ok := info.Uses[x].(*types.Var); ok {
			return []string{a.varNode(v)}
		}
		return nil
	case *ast.SelectorExpr:
		info := a.infoFor(x.Pos())
		if info == nil {
			return nil
		}
		if s, ok := info.Selections[x]; ok {
			if v, ok := s.Obj().(*types.Var); ok && v.IsField() {
				return []string{a.fieldNode(v)}
			}
		}
		if v, ok := info.Uses[x.Sel].(*types.Var); ok && v.IsField() {
			return []string{a.fieldNode(v)}
		}
		return nil
	case *ast.StarExpr:
		// storing through a pointer dereference: points-to is not resolved, so the store is
		// UNRESOLVED rather than assumed local.
		n := a.unknownNode(e.Pos(), "deref-target")
		a.g.addUnresolved(n, "value stored through a pointer dereference (points-to not resolved)", e.Pos())
		return []string{n}
	case *ast.IndexExpr:
		return []string{a.elemNode(a.typeOf(x.X))}
	case *ast.IndexListExpr:
		return []string{a.elemNode(a.typeOf(x.X))}
	default:
		n := a.unknownNode(e.Pos(), "unmodelled-target")
		a.g.addUnresolved(n, fmt.Sprintf("unmodelled assignment target %T", e), e.Pos())
		return []string{n}
	}
}

// ---------------------------------------------------------------------------------------------
// Composite literals
// ---------------------------------------------------------------------------------------------

func (a *analyzer) processLit(lit *ast.CompositeLit) {
	if a.litDone[lit.Pos()] {
		return
	}
	a.litDone[lit.Pos()] = true
	t := a.typeOf(lit)
	litNode := a.litNode(lit)
	if a.isBoundary(t) {
		a.g.addSink(litNode, "value is a "+typeStr(t)+" (a persistence boundary type)", lit.Pos())
	}
	st := structType(t)
	for idx, el := range lit.Elts {
		switch kv := el.(type) {
		case *ast.KeyValueExpr:
			name := keyIdent(kv.Key)
			var f *types.Var
			if st != nil && name != "" {
				if _, fv := lookupField(st, name); fv != nil {
					f = fv
				}
			}
			src := a.emit(kv.Value)
			if f != nil {
				fn := a.fieldNode(f)
				for _, s := range src {
					a.g.addEdge(s, fn)
					a.g.addEdge(fn, litNode)
					if a.isBoundary(t) {
						a.g.addSink(s, "value written into boundary type "+typeStr(t)+" field "+f.Name(), kv.Pos())
					}
					if types.IsInterface(f.Type().Underlying()) {
						a.g.addUnresolved(s, "value written into interface-typed field "+f.Name()+" (an any-typed hop)", kv.Pos())
					}
				}
			} else {
				// keyed element of a map/array/slice (or a struct field the checker did not
				// name): the element is part of the container value. Without this edge an
				// element's balance cannot reach a store of the container — a fail-open.
				for _, s := range src {
					a.g.addEdge(s, litNode)
				}
			}
		default:
			src := a.emit(el)
			if st != nil && idx < st.NumFields() {
				f := st.Field(idx)
				fn := a.fieldNode(f)
				for _, s := range src {
					a.g.addEdge(s, fn)
					a.g.addEdge(fn, litNode)
					if a.isBoundary(t) {
						a.g.addSink(s, "value written into boundary type "+typeStr(t)+" field "+f.Name(), el.Pos())
					}
					if types.IsInterface(f.Type().Underlying()) {
						a.g.addUnresolved(s, "value written into interface-typed field "+f.Name()+" (an any-typed hop)", el.Pos())
					}
				}
			} else {
				// element of a slice/array literal, or an unresolvable element position: the
				// element is part of the container value (fail-closed, over-approximate).
				for _, s := range src {
					a.g.addEdge(s, litNode)
				}
			}
		}
	}
}

func structType(t types.Type) *types.Struct {
	if t == nil {
		return nil
	}
	if s, ok := t.Underlying().(*types.Struct); ok {
		return s
	}
	return nil
}

func lookupField(st *types.Struct, name string) (int, *types.Var) {
	for i := 0; i < st.NumFields(); i++ {
		f := st.Field(i)
		if f.Name() == name {
			return i, f
		}
	}
	for i := 0; i < st.NumFields(); i++ {
		f := st.Field(i)
		if !f.Embedded() {
			continue
		}
		if inner := structType(f.Type()); inner != nil {
			if _, v := lookupField(inner, name); v != nil {
				return i, v
			}
		}
	}
	return -1, nil
}

func keyIdent(e ast.Expr) string {
	if id, ok := e.(*ast.Ident); ok {
		return id.Name
	}
	return ""
}

// ---------------------------------------------------------------------------------------------
// Calls
// ---------------------------------------------------------------------------------------------

func (a *analyzer) processCall(call *ast.CallExpr) {
	if a.callDone[call.Pos()] {
		return
	}
	a.callDone[call.Pos()] = true

	for _, arg := range call.Args {
		a.emit(arg)
	}

	fn, recvExpr, check, reason := a.resolveCallee(call)
	if check == resolveUnresolved {
		for _, arg := range call.Args {
			for _, n := range a.valueNodes(arg) {
				a.g.addUnresolved(n, reason, call.Pos())
			}
		}
		if recvExpr != nil {
			for _, n := range a.valueNodes(recvExpr) {
				a.g.addUnresolved(n, reason, call.Pos())
			}
		}
		a.g.addUnresolved(a.resultNode(call), reason, call.Pos())
		return
	}
	if check == resolveBuiltin {
		a.processBuiltin(call)
		return
	}
	if check == resolveConversion {
		rnode := a.resultNode(call)
		for _, arg := range call.Args {
			for _, n := range a.valueNodes(arg) {
				a.g.addEdge(n, rnode)
			}
		}
		return
	}
	if !a.inModuleFunc(fn) {
		if a.isDriverCall(fn) {
			a.driverCall(call, fn)
			return
		}
		a.externalCall(call, fn, recvExpr)
		return
	}

	// Resolved to exactly one static function or method in the target module.
	if a.isDriverCall(fn) {
		a.driverCall(call, fn)
	}

	sig := fn.Type().(*types.Signature)
	if recvExpr != nil && sig.Recv() != nil {
		a.bindArg(a.valueNodes(recvExpr), a.varNode(sig.Recv()))
	}
	params := sig.Params()
	for i, arg := range call.Args {
		var pt types.Type
		if sig.Variadic() && i >= params.Len()-1 {
			pt = params.At(params.Len() - 1).Type()
			if s, ok := pt.(*types.Slice); ok {
				pt = s.Elem()
			}
		} else if i < params.Len() {
			pt = params.At(i).Type()
		}
		nodes := a.valueNodes(arg)
		if pt != nil {
			var pv *types.Var
			if sig.Variadic() && i >= params.Len()-1 {
				pv = params.At(params.Len() - 1)
			} else if i < params.Len() {
				pv = params.At(i)
			}
			if pv != nil {
				a.bindArgTyped(nodes, a.varNode(pv), pt, call.Pos(), arg.Pos())
			}
		}
	}

	// Return values flow to the call's result.
	rnode := a.resultNode(call)
	for _, ret := range a.funcReturn[fn] {
		for _, n := range a.emit(ret) {
			a.g.addEdge(n, rnode)
		}
	}
}

type resolveKind int

const (
	resolveStatic resolveKind = iota
	resolveBuiltin
	resolveConversion
	resolveUnresolved
)

func (a *analyzer) resolveCallee(call *ast.CallExpr) (*types.Func, ast.Expr, resolveKind, string) {
	fun := unparen(call.Fun)
	switch x := fun.(type) {
	case *ast.Ident:
		info := a.infoFor(x.Pos())
		if info == nil {
			return nil, nil, resolveUnresolved, "call through an expression the checker cannot resolve"
		}
		switch obj := info.Uses[x].(type) {
		case *types.Func:
			return obj, nil, resolveStatic, ""
		case *types.Builtin:
			return nil, nil, resolveBuiltin, ""
		case *types.TypeName:
			// a conversion T(x) is a value-preserving identity for flow purposes
			return nil, nil, resolveConversion, ""
		case *types.Var:
			return nil, x, resolveUnresolved, "call through a func value (dynamic dispatch)"
		default:
			return nil, x, resolveUnresolved, "call through an unresolved callee"
		}
	case *ast.SelectorExpr:
		info := a.infoFor(x.Pos())
		if info == nil {
			return nil, x, resolveUnresolved, "method call the checker cannot resolve"
		}
		if s, ok := info.Selections[x]; ok {
			if f, ok := s.Obj().(*types.Func); ok {
				if f.Type().(*types.Signature).Recv() != nil && types.IsInterface(deref(s.Recv())) {
					return a.resolveInterfaceMethod(f, x.X)
				}
				return f, x.X, resolveStatic, ""
			}
			return nil, x, resolveUnresolved, "call through a field or method value"
		}
		if f, ok := info.Uses[x.Sel].(*types.Func); ok {
			return f, nil, resolveStatic, ""
		}
		return nil, x, resolveUnresolved, "call through an unresolved selector"
	case *ast.IndexExpr:
		return a.resolveCallee(&ast.CallExpr{Fun: x.X, Args: call.Args})
	case *ast.IndexListExpr:
		return a.resolveCallee(&ast.CallExpr{Fun: x.X, Args: call.Args})
	case *ast.ParenExpr:
		return a.resolveCallee(&ast.CallExpr{Fun: x.X, Args: call.Args})
	default:
		return nil, fun, resolveUnresolved, "call through an unresolved callee"
	}
}

// resolveInterfaceMethod resolves an interface method with EXACTLY ONE implementation in the
// module. Zero implementations, or more than one, is UNRESOLVED — T514's rule, and this is the
// fail-closed direction that makes the discriminator worth having.
func (a *analyzer) resolveInterfaceMethod(f *types.Func, recv ast.Expr) (*types.Func, ast.Expr, resolveKind, string) {
	// the tree's own SQL seam is a driver boundary regardless of how many pooled/transaction
	// types implement it; classify it as static against its own object and let driverCall decide.
	if a.isDriverObject(f) {
		return f, recv, resolveStatic, ""
	}
	var matches []*types.Func
	for _, cand := range a.implIndex[f.Name()] {
		if types.Identical(cand.Type(), f.Type()) {
			matches = append(matches, cand)
		}
	}
	switch len(matches) {
	case 0:
		return nil, recv, resolveUnresolved, "interface method " + f.Name() + " has NO implementation in scope"
	case 1:
		return matches[0], recv, resolveStatic, ""
	default:
		return nil, recv, resolveUnresolved, fmt.Sprintf("interface method %s has %d implementations in scope (dynamic dispatch)", f.Name(), len(matches))
	}
}

func (a *analyzer) bindArg(src []string, dst string) {
	for _, s := range src {
		a.g.addEdge(s, dst)
	}
}

func (a *analyzer) bindArgTyped(src []string, dst string, pt types.Type, callPos, argPos token.Pos) {
	for _, s := range src {
		a.g.addEdge(s, dst)
		if a.isBoundary(pt) {
			a.g.addSink(s, "value flows into a persistence-boundary parameter of type "+typeStr(pt), argPos)
			continue
		}
		if pt != nil {
			if _, ok := pt.Underlying().(*types.Signature); ok {
				a.g.addUnresolved(s, "func value passed as an argument (dynamic dispatch)", argPos)
				continue
			}
		}
		if pt != nil && types.IsInterface(pt.Underlying()) {
			a.g.addUnresolved(s, "value flows into interface type "+typeStr(pt)+" (an any-typed hop)", argPos)
			continue
		}
		if a.isBoundary(a.nodeType(dst)) {
			a.g.addSink(s, "value flows into persistence-boundary type "+typeStr(a.nodeType(dst)), callPos)
		}
	}
}

func (a *analyzer) processBuiltin(call *ast.CallExpr) {
	fun := unparen(call.Fun)
	id, ok := fun.(*ast.Ident)
	if !ok {
		return
	}
	switch id.Name {
	case "append":
		if len(call.Args) == 0 {
			return
		}
		dstT := a.typeOf(call.Args[0])
		dst := a.elemNode(dstT)
		ifaceElem := false
		if e := elementType(dstT); e != nil && types.IsInterface(e.Underlying()) {
			ifaceElem = true
		}
		for _, arg := range call.Args[1:] {
			for _, s := range a.valueNodes(arg) {
				a.g.addEdge(s, dst)
				if ifaceElem {
					a.g.addUnresolved(s, "value appended to an interface-typed container "+typeStr(dstT)+" (an any-typed hop)", call.Pos())
				}
			}
		}
	case "copy":
		if len(call.Args) >= 2 {
			dstT := a.typeOf(call.Args[0])
			dst := a.elemNode(dstT)
			ifaceElem := false
			if e := elementType(dstT); e != nil && types.IsInterface(e.Underlying()) {
				ifaceElem = true
			}
			for _, s := range a.valueNodes(call.Args[1]) {
				a.g.addEdge(s, dst)
				if ifaceElem {
					a.g.addUnresolved(s, "value copied into an interface-typed container "+typeStr(dstT)+" (an any-typed hop)", call.Pos())
				}
			}
		}
	case "make", "new", "len", "cap", "delete", "close", "print", "println", "panic", "recover", "min", "max", "clear":
		// no flow
	default:
		for _, arg := range call.Args {
			for _, s := range a.valueNodes(arg) {
				a.g.addUnresolved(s, "value flows through builtin "+id.Name, call.Pos())
			}
		}
	}
}

// ---------------------------------------------------------------------------------------------
// Persistence boundaries: the driver seam and SQL classification
// ---------------------------------------------------------------------------------------------

func pkgPath(fn *types.Func) string {
	if fn == nil || fn.Pkg() == nil {
		return ""
	}
	return fn.Pkg().Path()
}

// inModuleFunc reports whether fn's body was parsed and opened by this analysis. Anything
// outside the target module is an UNRESOLVED edge by construction (fail-closed): this program
// did not read that body, so it cannot claim the value does not persist there.
func (a *analyzer) inModuleFunc(fn *types.Func) bool {
	if fn == nil || fn.Pkg() == nil {
		return false
	}
	p := fn.Pkg().Path()
	return p == a.modulePath || strings.HasPrefix(p, a.modulePath+"/")
}

// persistenceInertPkgs is the allow-list of standard-library package PATHS that cannot carry a
// value to a persistence boundary. It is keyed on the callee package's PATH as resolved through
// its types.Object (fn.Pkg().Path()), never on a name spelled in the source: a module package
// somewhere else on disk named `fmt` has a different path and is NOT matched. Each entry states,
// in one line, why the package cannot persist.
//
// The list is deliberately short. A package belongs here only if none of its exported functions
// can write a value to a database, a journal entry or a GL posting. Even then, a call is pruned
// only when it is PURE WITH RESPECT TO PERSISTENCE (see persistenceInert): a call that hands the
// callee an io.Writer is NOT pruned, because that writer is the caller's and can be a store
// (this is why fmt.Fprint* is refused); a callee with a typed pointer parameter is refused as a
// conservative out-write guard UNLESS its package is marked pointerParamsAreOperands, in which
// case the pointer slots are arithmetic operands/mutated results rather than arbitrary caller
// destinations and the caller must preserve their flow (see modelOutWrites). The variadic ...any
// of the fmt Scan family is not a typed pointer, but the package owns no store, so a scanned
// value stays in caller memory and cannot reach a boundary.
type inertPkg struct {
	why string
	// pointerParamsAreOperands marks a package whose typed-pointer parameters and pointer
	// receivers are arithmetic operands or mutated results, not arbitrary out-writes owned by
	// the caller. Relaxing the pointer-parameter guard for such a package is sound only because
	// the pruner then RECONNECTS every input to every mutable slot (modelOutWrites), so a value
	// the callee writes through a pointer cannot lose its path to a later store. It must remain
	// false for any package whose pointer parameters could be the caller's own destinations.
	pointerParamsAreOperands bool
}

var persistenceInertPkgs = map[string]inertPkg{
	"fmt":     {why: "owns no persistence store; its output goes to an io.Writer/io.Reader or to caller pointers (the Scan family), never to a database, journal or posting. Calls handed an io.Writer are excluded below (Fprint*) because that writer is the caller's and can be the store"},
	"strconv": {why: "pure numeric/string conversions with no I/O at all"},
	"strings": {why: "pure string transformations with no I/O at all"},
	"testing": {why: "formats and buffers test output for the test log; it opens no database, journal or posting"},
	// time is a calendar/duration package: it performs no I/O and owns no database, journal or
	// posting. Its values (Time, Duration, Location) are plain in-memory structs. It has typed
	// pointer parameters (time.Date's *Location, time.Time.In/ParseInLocation) but those are
	// read-only timezone operands, never destinations; marking the package reconnects them.
	"time": {why: "calendar/duration arithmetic over in-memory values with no store and no I/O", pointerParamsAreOperands: true},
	// math/big is this programme's money-arithmetic package, but the question is not whether it
	// touches money — it is whether it can PERSIST money. It opens no database, writes no
	// journal entry and owns no store. Its Int/Rat methods take pointer receivers and MUTATE
	// them (z.Add(x, y) writes z), and some take pointer operands (QuoRem's remainder), so the
	// pointer-parameter guard is relaxed ONLY together with modelOutWrites, which keeps the
	// arg->receiver and input->mutable-slot edges that carry the arithmetic RESULT to a store.
	"math/big": {why: "arbitrary-precision integer/rational arithmetic in caller memory; no I/O and no store of any kind", pointerParamsAreOperands: true},
}

// ioWriterIface resolves the io.Writer interface OBJECT from the loaded dependency graph. It is
// found by package path, not by a source name, so an unrelated interface named Writer does not
// match.
func (a *analyzer) ioWriterIface() *types.Interface {
	for _, p := range a.allPkgs {
		if p.PkgPath != "io" || p.Types == nil {
			continue
		}
		tn, ok := p.Types.Scope().Lookup("Writer").(*types.TypeName)
		if !ok {
			continue
		}
		if iface, ok := tn.Type().Underlying().(*types.Interface); ok {
			return iface
		}
	}
	return nil
}

// persistenceInert reports whether a call into fn may be PRUNED from the unresolved flow. It is
// true only when BOTH hold:
//
//	(a) fn's package path is on the allow-list above, resolved through fn's types.Object; and
//	(b) fn is pure with respect to persistence: it takes no io.Writer-implementing parameter
//	    and, unless its package's entry sets pointerParamsAreOperands, no pointer parameter. A
//	    writer parameter can be an arbitrary destination (this is why fmt.Fprintf is NOT pruned),
//	    and for an ordinary package a pointer parameter is an out-write whose flow this program
//	    does not model, so it is left UNRESOLVED rather than assumed harmless. For a package
//	    whose pointer slots are arithmetic operands the guard is relaxed, and externalCall then
//	    calls modelOutWrites to reconnect every input to every mutable slot so no such flow is
//	    lost.
//
// A receiver is not a parameter and is not screened here: a method such as (*strings.Builder).WriteString
// may write its argument into the receiver, so the caller adds argument->receiver edges for every
// pruned method unless the receiver's own package is on trustReceiverNoPersistPkgs (testing), whose
// receiver provably cannot hold a value on a path to a store.
func (a *analyzer) persistenceInert(fn *types.Func) bool {
	if fn == nil || fn.Pkg() == nil {
		return false
	}
	entry, ok := persistenceInertPkgs[fn.Pkg().Path()]
	if !ok {
		return false
	}
	sig, ok := fn.Type().(*types.Signature)
	if !ok {
		return false
	}
	iw := a.ioWriterIface()
	for i := 0; i < sig.Params().Len(); i++ {
		pt := sig.Params().At(i).Type()
		if pt == nil {
			continue
		}
		if _, isPtr := pt.Underlying().(*types.Pointer); isPtr && !entry.pointerParamsAreOperands {
			return false
		}
		if iw != nil && types.Implements(pt, iw) {
			return false
		}
	}
	return true
}

// trustReceiverNoPersistPkgs are packages whose receiver types provably cannot carry a value
// to a store, so a pruned method from them needs no arg->receiver edges. Only testing is
// trusted: a *testing.T buffers a test log and is never handed to a driver. Every other
// allow-listed method (e.g. (*strings.Builder).WriteString) still gets receiver-write edges,
// because its receiver can hand the value on to a persistence path.
var trustReceiverNoPersistPkgs = map[string]bool{"testing": true}

// receiverTrustedNoPersist reports whether fn is a method whose receiver type's package is in
// trustReceiverNoPersistPkgs, resolved through the receiver's types.Object (by package path,
// never by a source-level name).
func receiverTrustedNoPersist(fn *types.Func) bool {
	sig, ok := fn.Type().(*types.Signature)
	if !ok || sig.Recv() == nil {
		return false
	}
	return trustReceiverNoPersistPkgs[typePkgPath(sig.Recv().Type())]
}

func typePkgPath(t types.Type) string {
	if p, ok := t.(*types.Pointer); ok {
		t = p.Elem()
	}
	if n, ok := t.(*types.Named); ok && n.Obj() != nil && n.Obj().Pkg() != nil {
		return n.Obj().Pkg().Path()
	}
	return ""
}

func (a *analyzer) externalCall(call *ast.CallExpr, fn *types.Func, recvExpr ast.Expr) {
	p := pkgPath(fn)
	if a.persistenceInert(fn) {
		// The callee's package cannot persist a value. The call is not a boundary, so the
		// arguments are not tainted by leaving the module, and there is no unresolved edge of
		// its own. The result, if any, is a NEW value DERIVED from the inputs: carry the flow
		// forward (union) so that a later persistence of the derived value is still seen.
		// Pruning one path never drops another.
		//
		// A method may also write its inputs into its receiver (strings.Builder.WriteString is
		// the canonical case), so when there is a receiver we add arg->receiver edges as well.
		// This over-approximates — a reader method gains edges it does not need — but it keeps
		// the write-into-receiver flow from being dropped, which is the only direction that
		// could hide a persistence. Over-approximation can only add flow, never clear a site.
		//
		// The one exception is a receiver whose own package is trusted not to persist
		// (testing): a value logged into a *testing.T cannot reach a store, so connecting
		// formatted arguments to t would only add false refusals. See trustReceiverNoPersist.
		if a.typeOf(call) != nil {
			res := a.resultNode(call)
			var recvNodes []string
			if recvExpr != nil {
				recvNodes = a.valueNodes(recvExpr)
				for _, n := range recvNodes {
					a.g.addEdge(n, res)
				}
			}
			modelRecvWrite := recvExpr != nil && !receiverTrustedNoPersist(fn)
			for _, arg := range call.Args {
				for _, n := range a.valueNodes(arg) {
					a.g.addEdge(n, res)
					if modelRecvWrite {
						for _, rn := range recvNodes {
							a.g.addEdge(n, rn)
						}
					}
				}
			}
		}
		// A relaxed package (math/big, time) may also write an input through a pointer operand,
		// not only through its receiver. Without points-to we cannot tell which slot is written,
		// so reconnect every input to every mutable slot: over-approximation adds flow and can
		// never clear a site, but dropping these edges could lose the path where the RESULT of
		// the arithmetic is what gets stored.
		if entry, ok := persistenceInertPkgs[p]; ok && entry.pointerParamsAreOperands {
			a.modelOutWrites(call, fn, recvExpr)
		}
		return
	}
	reason := "value passed into external package " + p + ", whose body this analysis did not open"
	if recvExpr != nil {
		for _, n := range a.valueNodes(recvExpr) {
			a.g.addUnresolved(n, reason, call.Pos())
		}
	}
	for _, arg := range call.Args {
		for _, n := range a.valueNodes(arg) {
			a.g.addUnresolved(n, reason, arg.Pos())
		}
	}
	a.g.addUnresolved(a.resultNode(call), "result of a call into external package "+p+" (provenance not opened)", call.Pos())
}

// persistenceMutableTarget reports whether a parameter or receiver of type t is a slot the
// callee can mutate through the caller's reference: a pointer, slice, map, channel or interface.
// A value of basic or struct type is a copy and cannot carry a mutation back to the caller.
func persistenceMutableTarget(t types.Type) bool {
	if t == nil {
		return false
	}
	switch t.Underlying().(type) {
	case *types.Pointer, *types.Slice, *types.Map, *types.Chan, *types.Interface:
		return true
	}
	return false
}

// modelOutWrites conservatively preserves the flow a pruned callee can perform into a
// caller-visible mutable slot. Every input (receiver and arguments) is connected to every
// mutable slot (a pointer/reference receiver and any pointer/reference argument). This
// over-approximates the callee's writes; over-approximation can only add flow, so it can never
// turn an unresolved or reaching site into a clear.
func (a *analyzer) modelOutWrites(call *ast.CallExpr, fn *types.Func, recvExpr ast.Expr) {
	sig, ok := fn.Type().(*types.Signature)
	if !ok {
		return
	}
	var sources []string
	if recvExpr != nil {
		sources = append(sources, a.valueNodes(recvExpr)...)
	}
	for _, arg := range call.Args {
		sources = append(sources, a.valueNodes(arg)...)
	}
	var targets []string
	if recvExpr != nil && sig.Recv() != nil && persistenceMutableTarget(sig.Recv().Type()) {
		targets = append(targets, a.valueNodes(recvExpr)...)
	}
	params := sig.Params()
	for i, arg := range call.Args {
		var pt types.Type
		if sig.Variadic() && i >= params.Len()-1 {
			pt = params.At(params.Len() - 1).Type()
			if s, ok := pt.(*types.Slice); ok {
				pt = s.Elem()
			}
		} else if i < params.Len() {
			pt = params.At(i).Type()
		}
		if persistenceMutableTarget(pt) {
			targets = append(targets, a.valueNodes(arg)...)
		}
	}
	for _, s := range sources {
		for _, t := range targets {
			if s != t {
				a.g.addEdge(s, t)
			}
		}
	}
}

func (a *analyzer) isDriverObject(fn *types.Func) bool {
	return fn != nil && a.driverObjects[fn]
}

func isDriverMethodName(n string) bool {
	switch n {
	case "Exec", "ExecContext", "Query", "QueryContext", "QueryRow", "QueryRowContext",
		"SendBatch", "CopyFrom", "Prepare", "Begin", "BeginTx":
		return true
	}
	return false
}

func (a *analyzer) isDriverCall(fn *types.Func) bool {
	return a.isDriverObject(fn)
}

// driverCall classifies a call into the persistence seam. If the SQL is resolvable and names a
// balance column or a journal/GL table, the call is a boundary (sink). If the SQL cannot be
// resolved, the value is UNRESOLVED — never acquitted.
func (a *analyzer) driverCall(call *ast.CallExpr, fn *types.Func) {
	sql, sqlKnown := a.sqlText(call)
	balanceBearing := false
	if sqlKnown {
		balanceBearing = sqlBearing(sql)
	}
	for _, arg := range call.Args {
		for _, n := range a.argSinkNodes(arg) {
			if !sqlKnown {
				a.g.addUnresolved(n, "value bound to a driver call whose SQL could not be resolved", call.Pos())
				continue
			}
			if balanceBearing {
				a.g.addSink(n, "value bound to a driver call writing a balance/journal boundary: "+firstLine(sql), call.Pos())
			} else {
				a.g.addUnresolved(n, "value bound to a driver call; the target column is not statically known to be a non-balance column", call.Pos())
			}
		}
	}
}

// argSinkNodes returns the argument's value nodes plus its container element node: a value that
// flowed into a slice/map element of an argument has also reached the driver call.
func (a *analyzer) argSinkNodes(arg ast.Expr) []string {
	ns := a.valueNodes(arg)
	if et := a.typeOf(arg); et != nil {
		if e := elementType(et); e != nil {
			if n := a.elemNode(et); n != "" {
				ns = append(ns, n)
			}
		}
	}
	return ns
}

// sqlText finds the SQL string of a driver call and returns the union of its possible literal
// values. Wrappers pass the SQL through parameters, so the string flow (propagateStrings) is
// consulted, not just a literal at the call site.
func (a *analyzer) sqlText(call *ast.CallExpr) (string, bool) {
	var parts []string
	for _, arg := range call.Args {
		info := a.infoFor(arg.Pos())
		if info == nil {
			continue
		}
		if _, ok := info.Types[arg].Type.Underlying().(*types.Basic); !ok {
			continue
		}
		if info.Types[arg].Type.String() != "string" {
			continue
		}
		if vals, ok := a.stringsOf(arg); ok {
			parts = append(parts, vals...)
		}
	}
	if len(parts) == 0 {
		return "", false
	}
	return strings.Join(parts, " "), true
}

func (a *analyzer) stringsOf(e ast.Expr) ([]string, bool) {
	if s, ok := stringLiteral(e); ok {
		return []string{s}, true
	}
	var nodes []string
	switch x := e.(type) {
	case *ast.Ident:
		nodes = a.identNodes(x)
	case *ast.SelectorExpr:
		nodes = a.selectorNodes(x)
	case *ast.BinaryExpr:
		if x.Op == token.ADD {
			left, lok := a.stringsOf(x.X)
			right, rok := a.stringsOf(x.Y)
			if lok && rok {
				var out []string
				for _, l := range left {
					for _, r := range right {
						out = append(out, l+r)
					}
				}
				return out, true
			}
		}
	}
	var out []string
	for _, n := range nodes {
		for v := range a.g.stringVals[n] {
			out = append(out, v)
		}
	}
	if len(out) == 0 {
		return nil, false
	}
	return out, true
}

var balanceWords = []string{"balance", "outstanding"}
var journalWords = []string{"journal_entry", "gl_journal", "acc_gl", "gl_posting", "posting"}

func sqlBearing(sql string) bool {
	s := strings.ToLower(sql)
	for _, w := range balanceWords {
		if strings.Contains(s, w) {
			return true
		}
	}
	for _, w := range journalWords {
		if strings.Contains(s, w) {
			return true
		}
	}
	return false
}

// propagateStrings pushes literal string values along the resolved edges to a fixpoint, so a
// wrapper's `sql` parameter learns the literal its caller passed.
func (a *analyzer) propagateStrings() {
	for changed := true; changed; {
		changed = false
		for from, dsts := range a.g.edges {
			vals, ok := a.g.stringVals[from]
			if !ok {
				continue
			}
			for d := range dsts {
				m, ok := a.g.stringVals[d]
				if !ok {
					m = map[string]struct{}{}
					a.g.stringVals[d] = m
				}
				for v := range vals {
					if _, seen := m[v]; !seen {
						m[v] = struct{}{}
						changed = true
					}
				}
			}
		}
	}
}

func stringLiteral(e ast.Expr) (string, bool) {
	switch x := e.(type) {
	case *ast.BasicLit:
		if x.Kind == token.STRING {
			if v := constant.MakeFromLiteral(x.Value, token.STRING, 0); v.Kind() == constant.String {
				return constant.StringVal(v), true
			}
		}
	case *ast.ParenExpr:
		return stringLiteral(x.X)
	case *ast.BinaryExpr:
		if x.Op == token.ADD {
			l, lok := stringLiteral(x.X)
			r, rok := stringLiteral(x.Y)
			if lok && rok {
				return l + r, true
			}
		}
	}
	return "", false
}

func unparen(e ast.Expr) ast.Expr {
	for {
		p, ok := e.(*ast.ParenExpr)
		if !ok {
			return e
		}
		e = p.X
	}
}

func firstLine(s string) string {
	s = strings.TrimSpace(s)
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		s = s[:i]
	}
	if len(s) > 90 {
		s = s[:90] + "..."
	}
	return s
}

// ---------------------------------------------------------------------------------------------
// Site detection and verdicts
// ---------------------------------------------------------------------------------------------

type siteSpec struct {
	Class string
	File  string
}

type siteResult struct {
	Class   string
	File    string
	Verdict Verdict
	Sources int
	Sink    string
	Causes  []cause
	Closure []string
}

// isBalanceName mirrors ledgerguard's balance surface: `balance` or the measured synonym
// `outstanding` (T509). This is the NAME half; the reachability is the type half.
func isBalanceName(s string) bool {
	l := strings.ToLower(s)
	return strings.Contains(l, "balance") || strings.Contains(l, "outstanding")
}

func (a *analyzer) detectFieldWrites(file *ast.File) []string {
	var out []string
	ast.Inspect(file, func(n ast.Node) bool {
		var lhs []ast.Expr
		switch x := n.(type) {
		case *ast.AssignStmt:
			lhs = x.Lhs
		case *ast.IncDecStmt:
			lhs = []ast.Expr{x.X}
		default:
			return true
		}
		for _, e := range lhs {
			if f := a.balanceFieldOf(e); f != nil {
				out = append(out, a.fieldNode(f))
				// A field is part of its base value. If the whole base struct is later stored
				// (db.Exec(..., v) / &v / appending v), a write that touches only the field would
				// otherwise be invisible to the flow and could be acquitted as PROVABLY-NO. Link
				// the write to the base expression's value nodes as well: this over-approximates,
				// which is sound, where the field-only view under-approximates, which is fail-open.
				if sel, ok := unparen(e).(*ast.SelectorExpr); ok {
					out = append(out, a.valueNodes(sel.X)...)
				}
			}
		}
		return true
	})
	return out
}

func (a *analyzer) balanceFieldOf(e ast.Expr) *types.Var {
	sel, ok := unparen(e).(*ast.SelectorExpr)
	if !ok {
		return nil
	}
	info := a.infoFor(sel.Pos())
	if info == nil {
		return nil
	}
	if s, ok := info.Selections[sel]; ok {
		if v, ok := s.Obj().(*types.Var); ok && v.IsField() && isBalanceName(v.Name()) {
			return v
		}
	}
	if v, ok := info.Uses[sel.Sel].(*types.Var); ok && v.IsField() && isBalanceName(v.Name()) {
		return v
	}
	return nil
}

func (a *analyzer) detectCompositeBalances(file *ast.File) []string {
	var out []string
	ast.Inspect(file, func(n ast.Node) bool {
		lit, ok := n.(*ast.CompositeLit)
		if !ok {
			return true
		}
		info := a.infoFor(lit.Pos())
		if info == nil {
			return true
		}
		st := structType(a.typeOf(lit))
		if st == nil {
			return true
		}
		for _, el := range lit.Elts {
			kv, ok := el.(*ast.KeyValueExpr)
			if !ok {
				continue
			}
			name := keyIdent(kv.Key)
			if name == "" || !isBalanceName(name) {
				continue
			}
			if _, f := lookupField(st, name); f != nil {
				out = append(out, a.fieldNode(f))
			}
		}
		return true
	})
	return out
}

// verdictFor implements the three-verdict, fail-closed rule. It computes the forward closure of
// the written value (where it flows) and then the backward closure of that whole set (everything
// that flowed into anything the value touches). A resolved sink anywhere in the forward closure
// is REACHES-PERSISTENCE. Otherwise a single UNRESOLVED edge anywhere in the influenced region
// makes the whole site UNRESOLVED. PROVABLY-NO-PERSISTENCE requires the ENTIRE region resolved.
func (a *analyzer) verdictFor(sources []string, limit int) (Verdict, string, []cause, []string) {
	fwd := map[string]bool{}
	queue := append([]string{}, sources...)
	sink := ""
	for len(queue) > 0 {
		n := queue[0]
		queue = queue[1:]
		if fwd[n] {
			continue
		}
		fwd[n] = true
		if sink == "" {
			if c := a.g.sinks[n]; len(c) > 0 {
				sink = c[0].String()
			}
		}
		for d := range a.g.edges[n] {
			if !fwd[d] {
				queue = append(queue, d)
			}
		}
	}

	// Influenced region: the forward closure plus every node that can reach it. A verdict about
	// the written value is unsound if ANY provenance edge into its uses is unresolved.
	region := map[string]bool{}
	for n := range fwd {
		region[n] = true
		queue = append(queue, n)
	}
	for len(queue) > 0 {
		n := queue[0]
		queue = queue[1:]
		for d := range a.g.rev[n] {
			if !region[d] {
				region[d] = true
				queue = append(queue, d)
			}
		}
	}
	var causes []cause
	for n := range region {
		causes = append(causes, a.g.unresolved[n]...)
	}

	closure := a.closureOf(fwd, limit)
	if sink != "" {
		return Reaches, sink, dedupCauses(causes), closure
	}
	if len(causes) > 0 {
		return Unresolved, "", dedupCauses(causes), closure
	}
	return ProvablyNo, "", nil, closure
}

// closureOf prints the resolved hops deterministically so a PROVABLY-NO verdict is auditable.
func (a *analyzer) closureOf(set map[string]bool, limit int) []string {
	keys := make([]string, 0, len(set))
	for n := range set {
		keys = append(keys, n)
	}
	sort.Slice(keys, func(i, j int) bool { return a.nodeSortKey(keys[i]) < a.nodeSortKey(keys[j]) })
	var out []string
	for _, n := range keys {
		if len(out) >= limit {
			break
		}
		if ni, ok := a.g.nodes[n]; ok {
			out = append(out, fmt.Sprintf("%s  [%s]", ni.Label, a.fset.Position(ni.Pos)))
		}
	}
	return out
}

func (a *analyzer) nodeSortKey(k string) string {
	if ni, ok := a.g.nodes[k]; ok {
		return a.fset.Position(ni.Pos).String() + "#" + k
	}
	return k
}

func dedupCauses(in []cause) []cause {
	seen := map[string]bool{}
	var out []cause
	for _, c := range in {
		k := c.String()
		if seen[k] {
			continue
		}
		seen[k] = true
		out = append(out, c)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].String() < out[j].String() })
	return out
}

// ---------------------------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------------------------

func defaultSites() []siteSpec {
	return []siteSpec{
		{"I3-COMPOSITE-BALANCE", "internal/apps/loanproduct/interestperiod.go"},
		{"I3-COMPOSITE-BALANCE", "internal/apps/loanproduct/repaymentperiod.go"},
		{"I3-FIELD-WRITE", "internal/apps/loanproduct/interestperiod.go"},
		{"I3-FIELD-WRITE", "internal/apps/loanproduct/repaymentperiod.go"},
		{"I3-FIELD-WRITE", "internal/apps/loan/charge.go"},
		{"I3-FIELD-WRITE", "internal/apps/loanschedule/emi.go"},
	}
}

func readSites(path string) ([]siteSpec, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []siteSpec
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		f := strings.Fields(line)
		if len(f) != 2 {
			return nil, fmt.Errorf("bad site line %q: want CLASS<TAB>path", line)
		}
		out = append(out, siteSpec{Class: f[0], File: filepath.ToSlash(f[1])})
	}
	return out, nil
}

func main() {
	root := flag.String("root", "nexus", "module directory to analyse")
	sitesFile := flag.String("sites", "", "optional site list: CLASS<TAB>relpath per line")
	asJSON := flag.Bool("json", false, "emit JSON")
	limit := flag.Int("closure", 120, "max closure nodes printed per site")
	srcOnly := flag.Bool("only", false, "only report sites that are UNRESOLVED/REACHES")
	flag.Parse()

	sites := defaultSites()
	if *sitesFile != "" {
		var err error
		sites, err = readSites(*sitesFile)
		if err != nil {
			fmt.Fprintln(os.Stderr, "reachguard: reading sites:", err)
			os.Exit(2)
		}
	}
	if len(sites) == 0 {
		fmt.Fprintln(os.Stderr, "reachguard: the site selector is EMPTY. That is a selector failure, not a clean tree. EXIT 2.")
		os.Exit(2)
	}

	pkgs, fset, err := load(*root)
	if err != nil {
		fmt.Fprintln(os.Stderr, "reachguard: cannot load", *root, ":", err)
		fmt.Fprintln(os.Stderr, "reachguard: without a type-checked module this program inspects nothing. EXIT 2 — NOT a pass.")
		os.Exit(2)
	}

	a := newAnalyzer(fset)
	a.prepare(pkgs)
	a.build()

	absRoot, _ := filepath.Abs(*root)
	results := analyzeSites(a, absRoot, sites, *limit)

	worst := ProvablyNo
	for _, r := range results {
		if r.Verdict == Reaches {
			worst = Reaches
		} else if r.Verdict == Unresolved && worst != Reaches {
			worst = Unresolved
		}
	}

	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(results)
	} else {
		report(results, *srcOnly)
	}
	if worst != ProvablyNo {
		os.Exit(1)
	}
}

// analyzeSites runs detection and the fail-closed verdict for each site. It is shared by main and
// by the three red controls in reachguard_test.go, so the controls exercise the SAME code path the
// instrument ships, not a re-implementation. If the persistence seam did not fully resolve
// (seamBroken), no verdict may be PROVABLY-NO-PERSISTENCE: the boundary set is incomplete.
func analyzeSites(a *analyzer, absRoot string, sites []siteSpec, limit int) []siteResult {
	results := make([]siteResult, 0, len(sites))
	for _, s := range sites {
		abs := filepath.Join(absRoot, filepath.FromSlash(s.File))
		file := a.fileByAbs(abs)
		if file == nil {
			results = append(results, siteResult{Class: s.Class, File: s.File, Verdict: Unresolved,
				Causes: []cause{{Reason: "site file is not part of the loaded module (site selector failure, not an acquittal)"}}})
			continue
		}
		var sources []string
		switch s.Class {
		case "I3-FIELD-WRITE":
			sources = a.detectFieldWrites(file)
		case "I3-COMPOSITE-BALANCE":
			sources = a.detectCompositeBalances(file)
		default:
			results = append(results, siteResult{Class: s.Class, File: s.File, Verdict: Unresolved,
				Causes: []cause{{Reason: "unknown class " + s.Class}}})
			continue
		}
		sources = dedupNodes(sources)
		if len(sources) == 0 {
			results = append(results, siteResult{Class: s.Class, File: s.File, Verdict: Unresolved,
				Causes: []cause{{Reason: "no write of this class was found in the site file — detection failure, never an acquittal"}}})
			continue
		}
		v, sink, causes, closure := a.verdictFor(sources, limit)
		if a.seamBroken && v == ProvablyNo {
			v = Unresolved
			causes = append([]cause{{Reason: "the persistence seam did not resolve (see seam notes): the boundary set is incomplete, so no site can be PROVABLY-NO-PERSISTENCE"}}, causes...)
		}
		results = append(results, siteResult{Class: s.Class, File: s.File, Verdict: v, Sources: len(sources),
			Sink: sink, Causes: causes, Closure: closure})
	}
	return results
}

func (a *analyzer) fileByAbs(abs string) *ast.File {
	abs = canonicalPath(abs)
	for _, p := range a.allPkgs {
		if p.TypesInfo == nil {
			continue
		}
		for _, f := range p.Syntax {
			if canonicalPath(a.fset.File(f.Pos()).Name()) == abs {
				return f
			}
		}
	}
	return nil
}

// canonicalPath cleans a path and resolves symlinks. macOS temp directories (/var/folders) are
// symlinked to /private/var, and go/packages may hand back either form; without this the
// fixture controls would silently read as "site file is not part of the loaded module".
func canonicalPath(p string) string {
	p = filepath.Clean(p)
	if r, err := filepath.EvalSymlinks(p); err == nil {
		return filepath.Clean(r)
	}
	return p
}

func dedupNodes(in []string) []string {
	seen := map[string]bool{}
	var out []string
	for _, s := range in {
		if s == "" || seen[s] {
			continue
		}
		seen[s] = true
		out = append(out, s)
	}
	return out
}

func report(results []siteResult, only bool) {
	fmt.Printf("reachguard — LEG 2 value-flow reachability (module loaded with go/packages NeedTypes|NeedSyntax|NeedTypesInfo|NeedDeps)\n")
	fmt.Printf("VERDICTS ARE FAIL-CLOSED: UNRESOLVED is the default and is never an acquittal.\n\n")
	nReach, nUnres, nProv := 0, 0, 0
	for _, r := range results {
		switch r.Verdict {
		case Reaches:
			nReach++
		case Unresolved:
			nUnres++
		case ProvablyNo:
			nProv++
		}
		if only && r.Verdict == ProvablyNo {
			continue
		}
		fmt.Printf("  [%s] %s\n", r.Class, r.File)
		fmt.Printf("      VERDICT: %s   (write sites resolved: %d)\n", r.Verdict, r.Sources)
		if r.Verdict == Reaches {
			fmt.Printf("      boundary: %s\n", r.Sink)
		}
		if len(r.Causes) > 0 {
			shown := r.Causes
			if len(shown) > 12 {
				shown = shown[:12]
			}
			for _, c := range shown {
				fmt.Printf("      unresolved: %s\n", c)
			}
			if len(r.Causes) > len(shown) {
				fmt.Printf("      unresolved: ... %d more\n", len(r.Causes)-len(shown))
			}
		}
		if r.Verdict == ProvablyNo {
			fmt.Printf("      RESOLVED CLOSURE (every hop, %d node(s)):\n", len(r.Closure))
			for _, c := range r.Closure {
				fmt.Printf("        %s\n", c)
			}
		}
		fmt.Println()
	}
	fmt.Printf("SUMMARY: %d REACHES, %d UNRESOLVED, %d PROVABLY-NO-PERSISTENCE — of %d site(s)\n",
		nReach, nUnres, nProv, len(results))
	if nProv > 0 {
		// A PROVABLY-NO verdict is a FINDING for review, not a waiver: clearing a recorded red is
		// a human act (an explicit baseline diff), never this program's. Say so instead of
		// claiming no site was cleared, which stopped being true the moment a closure resolved.
		fmt.Printf("%d site(s) resolved to PROVABLY-NO-PERSISTENCE — a finding for review, not a waiver.\n", nProv)
	}
	if nReach+nUnres > 0 {
		fmt.Printf("THE RED STANDS on %d site(s).\n", nReach+nUnres)
	}
}
