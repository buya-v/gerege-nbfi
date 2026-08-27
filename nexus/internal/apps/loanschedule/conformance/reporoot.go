package conformance

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

// THE REPOSITORY ROOT IS ANCHORED TO THE TREE THE BINARY WAS COMPILED FROM,
// NEVER TO THE CALLER'S WORKING DIRECTORY.
//
// WHAT WENT WRONG (T165, measured — see the handoff for the transcripts).
// cmd/conformance used to open with `conformance.FindRepoRoot(".")`, so every
// path-resolved gate in this harness was decided by wherever the caller
// happened to be standing:
//
//   - opts.StoreRoot        — WHICH vector corpus is graded
//   - the no-float census   — WHICH Go tree is inspected for floating point
//   - VerifyContractDigest  — WHICH contract.go is hashed against the store pin
//   - admitParityProvenance — WHICH tree the capture_ref files are read from
//
// None of those is the tree the binary was built from, and nothing compared the
// two. Two runs of ONE binary, differing only in `cd`:
//
//	$ cd /tmp/T165-scratch && ./conf -oracle-probe=up
//	  * frozen contract …/contract.go digest d540867… does not match the store pin 0db73d4…
//	  VERDICT: UNUSABLE (exit 2)
//	$ cd <a clean sibling checkout> && ./conf -oracle-probe=up
//	  VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle
//
// The binary in both lines was compiled from the tree carrying an unratified
// edit to the FROZEN DEC-1 contract artefact. A `cd` turned a hard `user`-gate
// refusal into a green run, and the green run said nothing at all about which
// contract.go it had hashed. The identical shape held for the no-float census:
// a binary compiled with `0.036 / 12.0` in it reported exit 2 from its own tree
// and VERDICT: PASS from the sibling. That is the defect class this program
// keeps rediscovering — not a crash, not a red, but a check that silently
// grades something OTHER than the thing under test and reports success.
//
// This is not hypothetical arithmetic about worktrees. This program runs a
// dozen checkouts under .claude/worktrees/, the driver's own shell keeps its
// working directory ACROSS tool calls (it once ran a merge inside the Fineract
// checkout for exactly that reason), and several rescued worktrees have no
// .softhouse/vectors of their own — from inside one of those, the old upward
// walk escaped the worktree entirely and graded the MAIN checkout, printing
// VERDICT: PASS with main's store, main's contract and main's source tree while
// the caller stood in a different tree on a different branch.
//
// THE RULE NOW. The root is derived from the compiled-in source path of THIS
// FILE (runtime.Caller), because the only tree a conformance verdict can
// honestly describe is the tree whose bytes went into the binary. The walk is
// BOUNDED — up to the enclosing Go module root, whose module path must be the
// expected one, then exactly one level to the repository root — so it can never
// escape a checkout into a parent checkout the way the old unbounded search for
// .softhouse/vectors could. If .softhouse/vectors is not there, that is a
// REFUSAL naming the path, never a reason to keep climbing.
//
// There is NO working-directory fallback. An explicit -repo-root flag or
// CONFORMANCE_REPO_ROOT env var overrides the anchor (a binary whose source
// tree has moved, or a -trimpath build, has no anchor to use), and an override
// is printed as an override with the anchor beside it. Everything else refuses.
// The CWD is still resolved, but ONLY as a cross-check that is printed: a
// reader must be able to see, in the report, that the tree they were standing
// in is not the tree that was graded.

// GoModuleDirRel is the module directory inside the repository, and
// GoModulePath is the module path go.mod must declare. Both are asserted, not
// assumed: a positive check ("this really is the nexus module") is the only
// kind that cannot pass vacuously (P-35).
const (
	GoModuleDirRel = "nexus"
	GoModulePath   = "github.com/gerege/nexus"
)

// RepoRootSource names how the graded repository root was decided.
type RepoRootSource string

const (
	// RepoRootFromBuildAnchor is the normal path: the compiled-in source path of
	// this file located the module, and the module located the repository.
	RepoRootFromBuildAnchor RepoRootSource = "build-anchor"
	// RepoRootFromFlag is an explicit -repo-root.
	RepoRootFromFlag RepoRootSource = "flag -repo-root"
	// RepoRootFromEnv is an explicit CONFORMANCE_REPO_ROOT.
	RepoRootFromEnv RepoRootSource = "env CONFORMANCE_REPO_ROOT"
)

// RepoRootResolution is the full, printable account of how the root was chosen.
//
// Every field exists to be REPORTED. A root that is merely correct is not
// enough — the pre-T165 harness was correct in the common case too, and that is
// precisely why nobody noticed the uncommon one. The report prints the root,
// how it was obtained, the anchor it came from, and what the working directory
// WOULD have resolved to, on every run, passing or failing.
type RepoRootResolution struct {
	// Root is the absolute repository root the run grades. Authoritative.
	Root string

	// Source says which rule produced Root.
	Source RepoRootSource

	// AnchorFile is the compiled-in source path this file was built from, and
	// AnchorRoot is the repository root it resolved to. Both are recorded even
	// when an explicit override won, so an override that disagrees with the
	// compiled bytes is visible rather than silent.
	AnchorFile string
	AnchorRoot string
	AnchorErr  string

	// CWD is the process working directory and CWDRoot is what the pre-T165
	// upward walk from "." would have returned — the tree the old harness would
	// have graded. Cross-check only; NEVER authoritative.
	CWD     string
	CWDRoot string
	CWDErr  string
}

// CWDAgrees reports whether the working directory resolves to the same
// repository that is actually graded. False is not an error; it is the state
// the pre-T165 harness could not tell you it was in.
func (r RepoRootResolution) CWDAgrees() bool {
	return r.CWDRoot != "" && r.CWDRoot == r.Root
}

// buildAnchorFile is the compiled-in absolute path of THIS source file.
//
// It is a func rather than a package-level var so the frame it reports is
// unambiguous: runtime.Caller(0) names the file containing the call, and the
// call is here.
func buildAnchorFile() (string, bool) {
	_, file, _, ok := runtime.Caller(0)
	if !ok || file == "" {
		return "", false
	}
	return file, true
}

// repoRootFromAnchor turns a compiled-in source path into a repository root, or
// explains in one sentence why it cannot.
//
// Bounded on purpose. It climbs to the FIRST enclosing go.mod, verifies the
// module path, takes exactly one step to the parent, and then REQUIRES
// .softhouse/vectors to be a directory there. It does not keep climbing. The
// unbounded climb is what let a worktree with no vector store of its own hand
// the whole run to the parent checkout without a word.
func repoRootFromAnchor(anchorFile string) (string, error) {
	if !filepath.IsAbs(anchorFile) {
		return "", fmt.Errorf("the compiled-in source path %q is not absolute, so this binary carries no "+
			"usable build anchor (a -trimpath build does this); pass -repo-root or set CONFORMANCE_REPO_ROOT",
			anchorFile)
	}
	if _, err := os.Stat(anchorFile); err != nil {
		return "", fmt.Errorf("the tree this binary was compiled from is gone: %q: %w; "+
			"pass -repo-root or set CONFORMANCE_REPO_ROOT to say which checkout to grade", anchorFile, err)
	}

	modDir, err := findModuleDir(filepath.Dir(anchorFile))
	if err != nil {
		return "", err
	}
	if got, err := goModulePath(filepath.Join(modDir, "go.mod")); err != nil {
		return "", err
	} else if got != GoModulePath {
		return "", fmt.Errorf("the go.mod above the build anchor declares module %q, want %q: "+
			"%s is not the module this harness grades", got, GoModulePath, modDir)
	}
	if base := filepath.Base(modDir); base != GoModuleDirRel {
		return "", fmt.Errorf("the module directory is %q, want a directory named %q directly under the "+
			"repository root: %s", base, GoModuleDirRel, modDir)
	}

	root := filepath.Dir(modDir)
	vectors := filepath.Join(root, ".softhouse", "vectors")
	st, err := os.Stat(vectors)
	if err != nil {
		return "", fmt.Errorf("the checkout this binary was compiled from has no vector store at %s: %w. "+
			"THE SEARCH STOPS HERE ON PURPOSE — climbing further would grade a DIFFERENT checkout's corpus "+
			"against this checkout's code, which is what T165 found the old FindRepoRoot(\".\") doing",
			vectors, err)
	}
	if !st.IsDir() {
		return "", fmt.Errorf("%s exists but is not a directory", vectors)
	}
	return root, nil
}

// findModuleDir walks up from dir to the first directory containing go.mod.
func findModuleDir(dir string) (string, error) {
	start := dir
	for {
		if st, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil && !st.IsDir() {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("no go.mod found at or above %s", start)
		}
		dir = parent
	}
}

// goModulePath reads the module line out of a go.mod.
func goModulePath(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("go.mod: %w", err)
	}
	for _, line := range strings.Split(string(raw), "\n") {
		// Fields, not a prefix test: `modulefoo` has the prefix "module" and is
		// not a module line, and a prefix test would have accepted it.
		fields := strings.Fields(strings.TrimSpace(line))
		if len(fields) >= 2 && fields[0] == "module" {
			return fields[1], nil
		}
	}
	return "", fmt.Errorf("%s declares no module path", path)
}

// validateExplicitRoot checks an operator-supplied root as strictly as the
// anchor is checked. An override is a smaller blast radius than a CWD default
// only if it is verified; an unverified -repo-root is the same defect with a
// flag on it.
func validateExplicitRoot(root string) (string, error) {
	abs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	st, err := os.Stat(filepath.Join(abs, ".softhouse", "vectors"))
	if err != nil {
		return "", fmt.Errorf("%s is not a repository root for this harness: %w", abs, err)
	}
	if !st.IsDir() {
		return "", fmt.Errorf("%s/.softhouse/vectors is not a directory", abs)
	}
	if _, err := os.Stat(filepath.Join(abs, GoModuleDirRel, "go.mod")); err != nil {
		return "", fmt.Errorf("%s has no %s/go.mod: %w", abs, GoModuleDirRel, err)
	}
	return abs, nil
}

// ResolveRepoRoot decides which repository this run grades, and records enough
// to print the decision.
//
// Precedence: -repo-root, then CONFORMANCE_REPO_ROOT, then the build anchor.
// There is deliberately no fourth rule. When none of the three yields a root the
// run REFUSES with the anchor's own diagnosis, because a harness that cannot say
// which tree it is grading must not grade one.
func ResolveRepoRoot(flagValue string) (RepoRootResolution, error) {
	var r RepoRootResolution

	// The anchor is computed FIRST and ALWAYS, even when an override will win,
	// so that the report can show an override diverging from the compiled bytes.
	if file, ok := buildAnchorFile(); ok {
		r.AnchorFile = file
		if root, err := repoRootFromAnchor(file); err == nil {
			r.AnchorRoot = root
		} else {
			r.AnchorErr = err.Error()
		}
	} else {
		r.AnchorErr = "runtime.Caller reported no source file for this binary"
	}

	// The working directory is resolved for the cross-check line only. This is
	// the ONLY place "." is consulted, and its answer is never assigned to Root.
	if cwd, err := os.Getwd(); err == nil {
		r.CWD = cwd
		if cwdRoot, cerr := FindRepoRoot(cwd); cerr == nil {
			r.CWDRoot = cwdRoot
		} else {
			r.CWDErr = cerr.Error()
		}
	} else {
		r.CWDErr = err.Error()
	}

	envValue := os.Getenv("CONFORMANCE_REPO_ROOT")
	switch {
	case flagValue != "":
		root, err := validateExplicitRoot(flagValue)
		if err != nil {
			return r, fmt.Errorf("-repo-root: %w", err)
		}
		r.Root, r.Source = root, RepoRootFromFlag
	case envValue != "":
		root, err := validateExplicitRoot(envValue)
		if err != nil {
			return r, fmt.Errorf("CONFORMANCE_REPO_ROOT: %w", err)
		}
		r.Root, r.Source = root, RepoRootFromEnv
	case r.AnchorRoot != "":
		r.Root, r.Source = r.AnchorRoot, RepoRootFromBuildAnchor
	default:
		return r, errors.New("cannot determine WHICH repository to grade: " + r.AnchorErr +
			". This harness no longer falls back to the working directory — a conformance verdict names " +
			"a tree, and grading whichever tree the caller happened to stand in is how a run certifies " +
			"code it never inspected (T165)")
	}
	return r, nil
}
