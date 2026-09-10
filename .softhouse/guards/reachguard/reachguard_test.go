// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/main.go
package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// These are the THREE RED CONTROLS required before the instrument is believed. They run the
// shipped analysis path (load -> prepare -> build -> analyzeSites), not a re-implementation.
//
//  1. TestPositiveReachesPersistence  — a REAL positive must report REACHES-PERSISTENCE.
//  2. TestGitMVDoesNotMoveVerdict     — T505 MAJOR-1 reproduced: `git mv` must not move a verdict.
//  3. TestFailClosedDegrade           — a second interface implementation in scope must degrade
//                                       PROVABLY-NO-PERSISTENCE to UNRESOLVED, and an unresolved
//                                       control must never come back PROVABLY-NO-PERSISTENCE.

func fixtureRoot(t *testing.T, name string) string {
	t.Helper()
	abs, err := filepath.Abs(filepath.Join("testdata", name))
	if err != nil {
		t.Fatalf("resolving testdata/%s: %v", name, err)
	}
	if r, err := filepath.EvalSymlinks(abs); err == nil {
		return r
	}
	return abs
}

// analyze runs the shipped pipeline against a fixture module and returns the single site result.
func analyze(t *testing.T, root, relFile, class string) siteResult {
	t.Helper()
	pkgs, fset, err := load(root)
	if err != nil {
		t.Fatalf("load(%s): %v", root, err)
	}
	a := newAnalyzer(fset)
	a.prepare(pkgs)
	a.build()
	if a.seamBroken {
		t.Logf("note: fixture seam is broken (no tree seam package); verdicts stay fail-closed")
	}
	results := analyzeSites(a, root, []siteSpec{{Class: class, File: relFile}}, 400)
	if len(results) != 1 {
		t.Fatalf("expected exactly 1 site result, got %d", len(results))
	}
	return results[0]
}

func requireVerdict(t *testing.T, got siteResult, want Verdict) {
	t.Helper()
	if got.Verdict != want {
		t.Fatalf("[%s] %s: verdict = %s, want %s\n  causes:\n%v",
			got.Class, got.File, got.Verdict, want, got.Causes)
	}
}

// Control 1: THE REAL POSITIVE. Both composite-literal-into-store forms from T509 CANNOT-CATCH
// items 10 and 12 reach a database/sql Exec of a balance/GL statement, as does the direct field
// write whose containing struct is persisted. If any does not report REACHES-PERSISTENCE, the
// instrument has built nothing. Each form is a separate file so a union of sources cannot mask a
// broken one.
func TestPositiveReachesPersistence(t *testing.T) {
	root := fixtureRoot(t, "positive")
	cases := []struct{ file, class string }{
		{"positive.go", "I3-COMPOSITE-BALANCE"}, // v := Entry{...}; store(&v)
		{"append.go", "I3-COMPOSITE-BALANCE"},   // append(store.rows, Entry{...})
		{"fieldwrite.go", "I3-FIELD-WRITE"},     // v.Balance = x; store(v)
		{"nested.go", "I3-COMPOSITE-BALANCE"},   // store.Rows = []NestedRow{{Outstanding: x}}; store(store.Rows)
	}
	for _, c := range cases {
		t.Run(c.file, func(t *testing.T) {
			r := analyze(t, root, c.file, c.class)
			requireVerdict(t, r, Reaches)
			if r.Sink == "" {
				t.Fatalf("REACHES verdict without a boundary is not evidence")
			}
			t.Logf("positive boundary: %s", r.Sink)
		})
	}
}

// Control 2: THE `git mv` CONTROL (T505 MAJOR-1). A real balance write is git-moved one directory
// deeper and re-analysed. Neither verdict may change, and both must be REACHES-PERSISTENCE.
// Anything keyed on path/filename/package name fails here.
func TestGitMVDoesNotMoveVerdict(t *testing.T) {
	root := t.TempDir()
	if err := copyTree(fixtureRoot(t, "mv"), root); err != nil {
		t.Fatalf("copying mv fixture: %v", err)
	}
	if r, err := filepath.EvalSymlinks(root); err == nil {
		root = r
	}
	git := func(args ...string) {
		t.Helper()
		cmd := exec.Command("git",
			append([]string{"-c", "user.name=reachguard", "-c", "user.email=reachguard@example.invalid",
				"-c", "commit.gpgsign=false"}, args...)...)
		cmd.Dir = root
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v\n%s", args, err, out)
		}
	}
	git("init", "-q")
	git("add", "-A")
	git("commit", "-q", "-m", "fixture base")

	before := analyze(t, root, "ledger/ledger.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, before, Reaches)

	if err := os.MkdirAll(filepath.Join(root, "deep"), 0o755); err != nil {
		t.Fatal(err)
	}
	git("mv", "ledger/ledger.go", "deep/ledger.go")
	git("add", "-A")
	git("commit", "-q", "-m", "git mv ledger/ledger.go deep/ledger.go")
	// Prove the file really moved on disk, so a no-op cannot be mistaken for a stable verdict.
	if _, err := os.Stat(filepath.Join(root, "deep", "ledger.go")); err != nil {
		t.Fatalf("git mv did not move the file: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, "ledger", "ledger.go")); err == nil {
		t.Fatalf("git mv left the original file in place")
	}

	after := analyze(t, root, "deep/ledger.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, after, Reaches)

	if before.Verdict != after.Verdict {
		t.Fatalf("VERDICT MOVED WITH A `git mv`: before=%s after=%s", before.Verdict, after.Verdict)
	}

	// Path is only one of the three names T505 killed a surface heuristic on. Rename the package
	// clause too and prove the verdict is keyed on the driver method OBJECT, not on the package
	// name. A balance write is a balance write regardless of what its package is called.
	deepFile := filepath.Join(root, "deep", "ledger.go")
	body, err := os.ReadFile(deepFile)
	if err != nil {
		t.Fatal(err)
	}
	renamed := strings.Replace(string(body), "package ledger", "package ledgerdeep", 1)
	if renamed == string(body) {
		t.Fatalf("package rename did not apply; the package-name half of the control is not exercised")
	}
	if err := os.WriteFile(deepFile, []byte(renamed), 0o644); err != nil {
		t.Fatal(err)
	}
	renamedResult := analyze(t, root, "deep/ledger.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, renamedResult, Reaches)
	if renamedResult.Verdict != before.Verdict {
		t.Fatalf("VERDICT MOVED WITH A PACKAGE RENAME: before=%s after=%s", before.Verdict, renamedResult.Verdict)
	}
	t.Logf("git mv + package rename control: verdict stable at %s before and after", before.Verdict)
}

// Control 3a: the fully resolved negative. Every hop is resolved and none reaches a boundary, so
// the ONLY verdict that can clear a red is due — and its closure must be printed.
func TestResolvedIsProvablyNoPersistence(t *testing.T) {
	root := fixtureRoot(t, "resolved")
	r := analyze(t, root, "resolved.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, r, ProvablyNo)
	if len(r.Closure) == 0 {
		t.Fatalf("PROVABLY-NO-PERSISTENCE without a printed closure is an assertion, not a proof")
	}
	t.Logf("resolved closure (%d hop(s)): %v", len(r.Closure), r.Closure)
}

// Control 3b: FAIL-CLOSED, OBSERVED DEGRADING. The same site resolves to PROVABLY-NO with one
// interface implementation in scope, then must go UNRESOLVED once a second implementation exists.
// Fail-closed that is never observed failing closed is an assumption, not a property.
func TestFailClosedDegrade(t *testing.T) {
	root := t.TempDir()
	if err := copyTree(fixtureRoot(t, "resolved"), root); err != nil {
		t.Fatalf("copying resolved fixture: %v", err)
	}
	if r, err := filepath.EvalSymlinks(root); err == nil {
		root = r
	}

	before := analyze(t, root, "resolved.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, before, ProvablyNo)

	second := "package reachres\n\n" +
		"type secondImpl struct{}\n\n" +
		"func (secondImpl) Save(r Record) {}\n"
	if err := os.WriteFile(filepath.Join(root, "second.go"), []byte(second), 0o644); err != nil {
		t.Fatal(err)
	}

	after := analyze(t, root, "resolved.go", "I3-COMPOSITE-BALANCE")
	requireVerdict(t, after, Unresolved)
	t.Logf("fail-closed degrade: %s -> %s", before.Verdict, after.Verdict)
}

// copyTree copies a fixture tree (regular files only; fixtures contain no symlinks).
func copyTree(src, dst string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(target, data, info.Mode().Perm())
	})
}
