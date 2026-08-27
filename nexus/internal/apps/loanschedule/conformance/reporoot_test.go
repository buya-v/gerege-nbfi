package conformance

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// These tests are a SECOND line, not the guard. The guard is that
// cmd/conformance calls ResolveRepoRoot and has no working-directory fallback
// to reach; conformance.sh never runs `go test` (P-45), so a test-only check
// would gate nothing. What these add is the regression statement: the resolved
// root does not move when the working directory does.

// newRepoFixture builds a minimal but STRUCTURALLY REAL checkout: <root>/nexus
// with a go.mod declaring the expected module path, and <root>/.softhouse/vectors.
func newRepoFixture(t *testing.T, root, modulePath string, withVectors bool) string {
	t.Helper()
	pkgDir := filepath.Join(root, GoModuleDirRel, "internal", "apps", "loanschedule", "conformance")
	if err := os.MkdirAll(pkgDir, 0o755); err != nil {
		t.Fatal(err)
	}
	gomod := "module " + modulePath + "\n\ngo 1.23\n"
	if err := os.WriteFile(filepath.Join(root, GoModuleDirRel, "go.mod"), []byte(gomod), 0o644); err != nil {
		t.Fatal(err)
	}
	anchor := filepath.Join(pkgDir, "reporoot.go")
	if err := os.WriteFile(anchor, []byte("package conformance\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if withVectors {
		if err := os.MkdirAll(filepath.Join(root, ".softhouse", "vectors"), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	return anchor
}

func TestRepoRootFromAnchorResolvesItsOwnCheckout(t *testing.T) {
	root := t.TempDir()
	anchor := newRepoFixture(t, root, GoModulePath, true)

	got, err := repoRootFromAnchor(anchor)
	if err != nil {
		t.Fatalf("repoRootFromAnchor: %v", err)
	}
	want, err := filepath.EvalSymlinks(root)
	if err != nil {
		t.Fatal(err)
	}
	gotEval, err := filepath.EvalSymlinks(got)
	if err != nil {
		t.Fatal(err)
	}
	if gotEval != want {
		t.Fatalf("anchored root = %s, want %s", gotEval, want)
	}
}

// THE BOUNDED-WALK TEST, and the one that names the defect directly.
//
// An inner checkout with a nexus module but NO vector store of its own, nested
// inside an outer checkout that HAS one. That is not a hypothetical shape: this
// repository carries rescued worktrees under .claude/worktrees/ with no
// .softhouse/vectors, sitting inside the main checkout which has one. The old
// unbounded climb answered "the outer store" and said nothing; the anchored
// resolver must REFUSE and name the path it stopped at.
func TestRepoRootFromAnchorDoesNotEscapeIntoAParentCheckout(t *testing.T) {
	outer := t.TempDir()
	if err := os.MkdirAll(filepath.Join(outer, ".softhouse", "vectors"), 0o755); err != nil {
		t.Fatal(err)
	}
	inner := filepath.Join(outer, "inner")
	anchor := newRepoFixture(t, inner, GoModulePath, false)

	// The old rule, reproduced here so the test states the contrast rather than
	// asserting the new behaviour in a vacuum.
	escaped, err := FindRepoRoot(filepath.Dir(anchor))
	if err != nil {
		t.Fatalf("precondition: the old unbounded walk should still find the OUTER store: %v", err)
	}
	if escaped == inner {
		t.Fatalf("precondition failed: the fixture does not reproduce the escape (got %s)", escaped)
	}

	got, err := repoRootFromAnchor(anchor)
	if err == nil {
		t.Fatalf("repoRootFromAnchor returned %s; it must REFUSE when the compiled tree has no vector store, "+
			"never climb into %s", got, escaped)
	}
	if !strings.Contains(err.Error(), filepath.Join(inner, ".softhouse", "vectors")) {
		t.Fatalf("the refusal must name the path it stopped at; got: %v", err)
	}
}

func TestRepoRootFromAnchorRejectsAForeignModule(t *testing.T) {
	root := t.TempDir()
	anchor := newRepoFixture(t, root, "example.com/not/nexus", true)

	if _, err := repoRootFromAnchor(anchor); err == nil {
		t.Fatal("a go.mod declaring a different module path must not be accepted as this harness's module")
	}
}

func TestRepoRootFromAnchorRejectsAMissingOrRelativeAnchor(t *testing.T) {
	if _, err := repoRootFromAnchor("github.com/gerege/nexus/internal/x/y.go"); err == nil {
		t.Fatal("a non-absolute compiled-in path (a -trimpath build) must refuse, not be joined onto the CWD")
	}
	if _, err := repoRootFromAnchor(filepath.Join(t.TempDir(), "gone.go")); err == nil {
		t.Fatal("an anchor whose source file no longer exists must refuse")
	}
}

func TestValidateExplicitRootIsCheckedAsStrictlyAsTheAnchor(t *testing.T) {
	root := t.TempDir()
	newRepoFixture(t, root, GoModulePath, true)
	if _, err := validateExplicitRoot(root); err != nil {
		t.Fatalf("a well-formed root must be accepted: %v", err)
	}

	noVectors := t.TempDir()
	newRepoFixture(t, noVectors, GoModulePath, false)
	if _, err := validateExplicitRoot(noVectors); err == nil {
		t.Fatal("-repo-root pointing at a tree with no vector store must be refused, not trusted for being explicit")
	}

	noModule := t.TempDir()
	if err := os.MkdirAll(filepath.Join(noModule, ".softhouse", "vectors"), 0o755); err != nil {
		t.Fatal(err)
	}
	if _, err := validateExplicitRoot(noModule); err == nil {
		t.Fatal("-repo-root pointing at a tree with no nexus/go.mod must be refused")
	}
}

func TestGoModulePath(t *testing.T) {
	dir := t.TempDir()
	write := func(body string) string {
		p := filepath.Join(dir, "go.mod")
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
		return p
	}

	if got, err := goModulePath(write("module github.com/gerege/nexus\n\ngo 1.23\n")); err != nil || got != GoModulePath {
		t.Fatalf("goModulePath = %q, %v; want %q, nil", got, err, GoModulePath)
	}
	// A prefix test would have accepted this. Fields does not.
	if got, err := goModulePath(write("modulegithub.com/gerege/nexus\n")); err == nil {
		t.Fatalf("`modulegithub.com/...` is not a module line; got %q", got)
	}
	if _, err := goModulePath(write("go 1.23\n")); err == nil {
		t.Fatal("a go.mod with no module line must be an error")
	}
}

// THE REGRESSION TEST. The resolved root must be a property of the BINARY, not
// of the process's working directory.
func TestResolveRepoRootIsIndependentOfTheWorkingDirectory(t *testing.T) {
	t.Setenv("CONFORMANCE_REPO_ROOT", "")

	fromPackageDir, err := ResolveRepoRoot("")
	if err != nil {
		t.Fatalf("ResolveRepoRoot from the package directory: %v", err)
	}
	if fromPackageDir.Source != RepoRootFromBuildAnchor {
		t.Fatalf("source = %q, want %q — the anchor is the only rule that should apply with no override",
			fromPackageDir.Source, RepoRootFromBuildAnchor)
	}
	if !fromPackageDir.CWDAgrees() {
		t.Fatalf("precondition: `go test` runs in the package directory, so the cross-check should agree here "+
			"(root %s, cwd root %s)", fromPackageDir.Root, fromPackageDir.CWDRoot)
	}

	// Now stand somewhere with no repository above it at all — the shape that
	// used to make cmd/conformance exit 2 with "no repository root found".
	// os.Chdir rather than t.Chdir: this module is go1.23 and t.Chdir landed in
	// go1.24. The restore is deferred so no later test in this package inherits
	// a moved working directory — which would be this very defect, injected into
	// the suite that exists to catch it.
	origWD, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if cerr := os.Chdir(origWD); cerr != nil {
			t.Fatalf("could not restore the working directory to %s: %v", origWD, cerr)
		}
	})
	if err := os.Chdir(t.TempDir()); err != nil {
		t.Fatal(err)
	}

	fromElsewhere, err := ResolveRepoRoot("")
	if err != nil {
		t.Fatalf("ResolveRepoRoot from an unrelated directory: %v", err)
	}
	if fromElsewhere.Root != fromPackageDir.Root {
		t.Fatalf("the graded root MOVED with the working directory: %s -> %s",
			fromPackageDir.Root, fromElsewhere.Root)
	}
	if fromElsewhere.CWDAgrees() {
		t.Fatal("precondition: the cross-check should now DISAGREE, otherwise this test proves nothing")
	}
	if fromElsewhere.CWDRoot != "" || fromElsewhere.CWDErr == "" {
		t.Fatalf("the cross-check must record that the cwd resolves to no repository; got root %q err %q",
			fromElsewhere.CWDRoot, fromElsewhere.CWDErr)
	}
}

func TestResolveRepoRootRefusesAnUnusableExplicitOverride(t *testing.T) {
	bad := t.TempDir()
	if _, err := ResolveRepoRoot(bad); err == nil {
		t.Fatal("-repo-root at a directory that is not a checkout must refuse")
	}
	t.Setenv("CONFORMANCE_REPO_ROOT", bad)
	if _, err := ResolveRepoRoot(""); err == nil {
		t.Fatal("CONFORMANCE_REPO_ROOT at a directory that is not a checkout must refuse")
	}
}

// The report must SAY which tree was graded, on every run. A resolution that is
// correct but unprinted is what let the pre-T165 defect survive: the passing
// report was byte-indistinguishable from an honest one.
func TestReportAlwaysNamesTheGradedRootAndTheCrossCheck(t *testing.T) {
	cases := []struct {
		name string
		res  RepoRootResolution
		want []string
	}{
		{
			name: "anchored and agreeing",
			res: RepoRootResolution{
				Root: "/repo", Source: RepoRootFromBuildAnchor,
				AnchorFile: "/repo/nexus/x.go", AnchorRoot: "/repo",
				CWD: "/repo/nexus", CWDRoot: "/repo",
			},
			want: []string{"repo root       /repo", "BUILD ANCHOR", "cwd cross-check: SAME"},
		},
		{
			name: "anchored and diverging",
			res: RepoRootResolution{
				Root: "/repo", Source: RepoRootFromBuildAnchor,
				AnchorFile: "/repo/nexus/x.go", AnchorRoot: "/repo",
				CWD: "/other/nexus", CWDRoot: "/other",
			},
			want: []string{"cwd cross-check: DIFFERENT", "/other", "PRE-T165"},
		},
		{
			name: "explicit override diverging from the compiled bytes",
			res: RepoRootResolution{
				Root: "/repo", Source: RepoRootFromFlag,
				AnchorFile: "/build/nexus/x.go", AnchorRoot: "/build",
				CWD: "/repo", CWDRoot: "/repo",
			},
			want: []string{"EXPLICIT OVERRIDE", "OVERRIDE DIVERGES FROM THE COMPILED BYTES", "/build"},
		},
		{
			name: "programmatic caller, nothing recorded",
			res:  RepoRootResolution{},
			want: []string{"resolution NOT RECORDED"},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var sb strings.Builder
			p := func(format string, args ...any) {
				sb.WriteString(strings.TrimRight(fmt.Sprintf(format, args...), "\n") + "\n")
			}
			writeRepoRootLines(p, &Summary{RepoRoot: tc.res.Root, RepoRootRes: tc.res})
			out := sb.String()
			if out == "" {
				t.Fatal("writeRepoRootLines printed nothing; every arm must speak")
			}
			for _, w := range tc.want {
				if !strings.Contains(out, w) {
					t.Errorf("output does not mention %q:\n%s", w, out)
				}
			}
		})
	}
}
