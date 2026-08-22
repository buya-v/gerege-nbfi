package conformance

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// THE STORE FILE CENSUS — the two enumerators of the vector store must agree,
// and until T154 nothing compared them.
//
// `.softhouse/conformance.sh`'s guard_no_float_in_vectors enumerates the store
// with `find "$STORE_ROOT" -name '*.json' -type f` — RECURSIVE, case-SENSITIVE
// glob, no symlink following. LoadStore reads ONE LEVEL DEEP, skips anything
// os.ReadDir does not report as a directory, and matches the ".json" suffix
// BYTEWISE. Each therefore has files the other cannot see, and NO COUNT WAS EVER
// COMPARED, so every disagreement was silent.
//
// SIX MEASURED CONSEQUENCES on the pre-fix harness, all with the committed
// corpus otherwise intact [VERIFIED: .softhouse/capture/t154-nofloat/drive-leg3.sh,
// transcript out/leg3-RED-before-fix.txt — the PRE column of every row]:
//
//	F-1  a symlinked EXTRA context directory holding a float:  exit 0, 42/5576
//	     — invisible to `find` (no -L) AND to LoadStore (a symlink is not IsDir)
//	F-2  a vector one directory too deep:                      exit 0, 42/5576
//	     — `find` sees it, LoadStore does not, so it is silently NOT graded and
//	       the corpus count does not move when somebody "promotes" it
//	F-3  T154-UPPER.JSON carrying a float:                     exit 0, 42/5576
//	     — `*.json` is case-sensitive to fnmatch and HasSuffix is bytewise, so
//	       this file is a vector to NEITHER enumerator
//	F-4  P-00 and p-00, case-only case_id variants:            exit 0, 43/5623
//	F-5  NFC and NFD spellings of one case_id:                 exit 0, 44/5670
//	     — and the two rows RENDER IDENTICALLY in the report
//	M-5  a .json at the STORE ROOT other than PIN.json / capabilities.json:
//	     never decoded by Go at all, so the shell guard — the one T154 leg 1
//	     showed a single invalid byte defeats — was the ONLY float check
//	     covering it. Measured with the harness BINARY, so the shell guard was
//	     not in the circuit at all: a store-root file with a float behind an
//	     invalid byte took the pre-fix binary to exit 0.
//	     [CORRECTION, T154, against its own first draft] This block first said
//	     the shell guard was the only float check for EVERY store-root .json.
//	     That is false for the two the store actually has: LoadPin
//	     (admit.go:58) and LoadCapabilityRegistry (capability.go:110) each call
//	     RejectFloatTokens on their own bytes. The claim holds only for a
//	     store-root file that is neither of them — and the census now refuses
//	     those outright, so the case stops existing rather than being covered.
//
// F-4 and F-5 are the dangerous pair: they do not hide a defect, they INFLATE
// the two numbers this program quotes as its evidence of coverage, and every
// other check stays green while they do it.
//
// THE RULE, PHRASED POSITIVELY (P-35). The census does not look for bad files.
// It enumerates the store and requires every `.json` under the root to be
// ACCOUNTED FOR — loaded as a vector, or named on the short allowlist of
// non-vector files, or already reported as a load error. Anything else is a
// refusal. "Zero files seen" is an error, not a pass.

// storeRootNonVectorFiles are the only `.json` files permitted at the store
// root. They are configuration, not vectors: LoadStore never decodes them, and
// Run reads them by name (LoadPin, LoadCapabilityRegistry).
//
// THE LIST IS EXACT-CASE ON PURPOSE. `pin.json` is not `PIN.json`; on a
// case-insensitive filesystem the two names address one file, and on a
// case-sensitive one they address two. Requiring the exact bytes means the
// census's answer does not depend on which filesystem the store is sitting on.
// A2-15 adds the LEDGER context's two store-root files. They are configuration
// for the SECOND schema (nexus/internal/apps/ledger/conformance) exactly as the
// first two are for this one: LoadStore never decodes them and the ledger
// harness reads them by name. DEC-2 precondition P-6 decided that the ledger
// context gets its OWN capability file rather than rows appended to
// `capabilities.json`, whose schema id is a hard constant naming this context
// and whose `dec1_revision` is a DEC-1 revision number; the decision and the
// rejected alternative are recorded in that package's capability.go.
var storeRootNonVectorFiles = []string{
	"PIN.json", "capabilities.json",
	"PIN-ledger.json", "capabilities-ledger.json",
}

// caseIDRune reports whether r may appear in a case_id.
//
// ASCII letters, digits, dot, underscore and hyphen. All 47 committed vector
// files use ids inside this set [VERIFIED: T154 measured 47 of 47, transcript
// .softhouse/capture/t154-nofloat/out/leg3-*.txt section 1], so the rule costs
// the corpus nothing and closes F-5 outright: two Unicode normalisations of one
// id cannot both exist if neither can exist.
func caseIDRune(r rune) bool {
	switch {
	case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9':
		return true
	case r == '.' || r == '_' || r == '-':
		return true
	}
	return false
}

// CaseIDIntegrity refuses a store whose case_ids are not distinguishable to a
// reader of the report.
//
// TWO RULES, AND THEY CLOSE DIFFERENT HOLES.
//
//   - CHARSET. A case_id outside [A-Za-z0-9._-] is refused. This closes F-5: the
//     report prints the case_id and nothing else, so "P-NFC-é" spelled NFC and
//     the same id spelled NFD are two distinct keys that render as the same
//     glyphs. Measured: both graded, 44 parity vectors / 5670 cells, no warning.
//     Normalising instead of refusing would be a choice about WHICH id is the
//     real one, made by the harness, invisibly — the same argument that makes
//     DuplicateCaseIDs a refusal rather than a de-duplication.
//   - CASE FOLDING. Two ids differing only in letter case are refused. This
//     closes F-4: P-00 and p-00 both graded at 43 parity / 5623 cells. The
//     inflation is the point — a store that accidentally holds one case twice
//     reports MORE coverage than it has, which is the failure mode
//     DuplicateCaseIDs exists to prevent, arriving through a spelling it did not
//     check.
//
// It is a separate function from DuplicateCaseIDs because the two say different
// things: that one is "one id, two files"; this one is "two ids a reader cannot
// tell apart".
func CaseIDIntegrity(vectors []*Vector) error {
	var problems []string

	byFold := map[string]map[string][]string{} // lowercased id -> id -> paths
	for _, v := range vectors {
		if v.CaseID == "" {
			problems = append(problems, fmt.Sprintf("%s declares an EMPTY case_id", v.Path))
			continue
		}
		if bad := strings.Map(func(r rune) rune {
			if caseIDRune(r) {
				return -1
			}
			return r
		}, v.CaseID); bad != "" {
			problems = append(problems, fmt.Sprintf(
				"%s declares case_id %q, which contains %q — a case_id must match [A-Za-z0-9._-]+ so that "+
					"two ids cannot render identically in the report (a Unicode NFC/NFD pair does exactly that)",
				v.Path, v.CaseID, bad))
			continue
		}
		fold := strings.ToLower(v.CaseID)
		if byFold[fold] == nil {
			byFold[fold] = map[string][]string{}
		}
		byFold[fold][v.CaseID] = append(byFold[fold][v.CaseID], v.Path)
	}

	for _, fold := range sortedKeysOfFold(byFold) {
		spellings := byFold[fold]
		if len(spellings) < 2 {
			continue
		}
		var parts []string
		for _, id := range sortedKeysOfPaths(spellings) {
			paths := append([]string(nil), spellings[id]...)
			sort.Strings(paths)
			parts = append(parts, fmt.Sprintf("%q (%s)", id, strings.Join(paths, ", ")))
		}
		problems = append(problems, fmt.Sprintf(
			"case_ids differing only in letter case: %s. Both grade, and both add to the parity-vector and "+
				"graded-cell totals", strings.Join(parts, " AND ")))
	}

	if len(problems) == 0 {
		return nil
	}
	sort.Strings(problems)
	return fmt.Errorf(
		"CASE_ID INTEGRITY — %s. This run is REFUSED and NOTHING WAS GRADED: exit 2, which is not a PASS",
		strings.Join(problems, "; "))
}

func sortedKeysOfFold(m map[string]map[string][]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func sortedKeysOfPaths(m map[string][]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// StoreFileCensus requires every `.json` under storeRoot to be accounted for.
//
// accountedErrs are the files LoadStore already reported as load errors; they
// are known to the run and are not censused a second time. Everything else must
// be either a loaded vector at exactly one level below the root, or one of
// storeRootNonVectorFiles at the root itself.
//
// WHAT IT REFUSES, AND WHY EACH IS A REFUSAL RATHER THAN A WARNING:
//
//   - A SYMLINK anywhere under the store root. Both enumerators skip symlinks
//     and they skip DIFFERENT things when one appears, so the store's contents
//     stop being a function of the store. A warning would leave the run reporting
//     a coverage number computed over an unknown set.
//   - A DIRECTORY inside a context directory. LoadStore cannot reach it, so
//     anything in it is silently ungraded — including a vector somebody believes
//     they promoted.
//   - A `.json` (matched case-INSENSITIVELY) that no vector claims. This is the
//     rule that does the work: UPPER.JSON, a nested vector, a store-root file,
//     and anything reachable only through a symlink all land here.
//
// HOW IT CLOSES M-5, STATED EXACTLY.
//
//   - For a store-root `.json` that is NOT on the allowlist, the census refuses
//     the run. That is the whole of M-5: such a file was never decoded by Go, so
//     the shell guard leg 1 defeated was the only thing covering it. It now
//     cannot be present at all, which is stronger than checking it.
//   - For the two files that ARE on the allowlist, the census reads them and
//     runs RejectFloatTokens. This is BELT AND BRACES, not the closure: LoadPin
//     (admit.go) and LoadCapabilityRegistry (capability.go) already call
//     RejectFloatTokens on their own bytes, so a float in PIN.json was already
//     refused before T154 [VERIFIED: the pre-fix binary reports FLOAT TOKEN
//     "19.0" for a doctored PIN.json — .softhouse/capture/t154-nofloat/out/
//     leg3-GREEN-after-fix.txt, section 3b]. What this adds is that the check
//     now also runs under LoadStore alone — which is how every test reaches the
//     store — and that it binds ANY file later added to the allowlist, rather
//     than depending on whoever adds it remembering to write a loader that
//     checks.
//
// alsoClaimed names store-relative paths that a DIFFERENT schema's loader has
// taken responsibility for. It is VARIADIC so that every existing call site —
// fifteen in store_integrity_test.go alone — keeps compiling and keeps meaning
// exactly what it meant: "nothing else claims anything".
//
// WITHOUT IT, PROMOTING THE FIRST LEDGER VECTOR WOULD MAKE THIS CENSUS REFUSE
// THE RUN, and the census would be RIGHT: a .json under the store root that this
// loader did not load is, from here, indistinguishable from a vector somebody
// believes they promoted and nothing grades. The fix is not to loosen the
// census; it is to let the other loader SAY it has the file.
func StoreFileCensus(storeRoot string, loaded []*Vector, accountedErrs []LoadError,
	alsoClaimed ...string) error {

	claimed := make(map[string]string, len(loaded)+len(accountedErrs)+len(alsoClaimed))
	for _, rel := range alsoClaimed {
		claimed[filepath.ToSlash(rel)] = "loaded by the ledger schema's own loader"
	}
	for _, v := range loaded {
		claimed[filepath.ToSlash(v.Path)] = "loaded as vector " + v.CaseID
	}
	for _, le := range accountedErrs {
		claimed[filepath.ToSlash(le.Path)] = "already reported as a load error"
	}
	allowedRoot := make(map[string]bool, len(storeRootNonVectorFiles))
	for _, n := range storeRootNonVectorFiles {
		allowedRoot[n] = true
	}

	var problems []string
	seenJSON := 0

	walkErr := filepath.WalkDir(storeRoot, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, rerr := filepath.Rel(storeRoot, path)
		if rerr != nil {
			return rerr
		}
		rel = filepath.ToSlash(rel)
		if rel == "." {
			return nil
		}
		// WalkDir reports a symlink by its OWN type and never follows it, which
		// is exactly the behaviour that made F-1 invisible. Name it and stop.
		if d.Type()&fs.ModeSymlink != 0 {
			problems = append(problems, fmt.Sprintf(
				"%q is a SYMLINK. The vector store must be plain files and plain directories: `find` (without "+
					"-L) and os.ReadDir both skip a symlink, and they skip different things when one appears, "+
					"so the store's contents stop being a function of the store", rel))
			return nil
		}
		if d.IsDir() {
			if strings.Contains(rel, "/") {
				problems = append(problems, fmt.Sprintf(
					"%q is a directory INSIDE a context directory. The store is exactly two levels — "+
						"<root>/<context>/<vector>.json — and LoadStore reads one level down, so nothing "+
						"below here is ever loaded or graded", rel))
				return filepath.SkipDir
			}
			return nil
		}
		// Case-INSENSITIVE, because the mismatch between a case-sensitive glob
		// and a bytewise suffix test is the whole of F-3.
		if !strings.EqualFold(filepath.Ext(d.Name()), ".json") {
			return nil
		}
		seenJSON++
		if strings.Contains(rel, "/") {
			if _, ok := claimed[rel]; ok {
				return nil
			}
			problems = append(problems, fmt.Sprintf(
				"%q is a .json under the store root that the harness DID NOT LOAD. Every vector file must be "+
					"loaded and graded, or the corpus counts describe a different set of files than the one on "+
					"disk", rel))
			return nil
		}
		if !allowedRoot[d.Name()] {
			problems = append(problems, fmt.Sprintf(
				"%q sits at the STORE ROOT and is not one of %s. LoadStore reads only files INSIDE a context "+
					"directory, so a .json here is never decoded, never graded, and never float-checked by Go",
				rel, strings.Join(storeRootNonVectorFiles, ", ")))
			return nil
		}
		// M-5: the allowlisted root files are the ones Go never decoded. Check
		// them here, so the defeatable shell guard is no longer the only float
		// check that covers them.
		raw, rerr := os.ReadFile(path)
		if rerr != nil {
			problems = append(problems, fmt.Sprintf("%q could not be read: %v", rel, rerr))
			return nil
		}
		if ferr := RejectFloatTokens(raw); ferr != nil {
			problems = append(problems, fmt.Sprintf("%q: %v", rel, ferr))
		}
		return nil
	})
	if walkErr != nil {
		return fmt.Errorf("the store file census could not enumerate %s: %w", storeRoot, walkErr)
	}
	if seenJSON == 0 {
		return fmt.Errorf(
			"THE STORE FILE CENSUS SAW ZERO .json FILES under %s. A census that inspects nothing accounts "+
				"for everything, so this is an ERROR and not a pass", storeRoot)
	}
	if len(problems) > 0 {
		sort.Strings(problems)
		return fmt.Errorf(
			"STORE FILE CENSUS — %d .json files were found under %s and %d of them are unaccounted for: %s. "+
				"The shell float guard enumerates this store with `find -name '*.json' -type f` (recursive, "+
				"case-sensitive, no symlink following) and LoadStore reads one level down matching the suffix "+
				"bytewise; where the two disagree, a file is graded by neither, checked by neither, or counted "+
				"twice. This run is REFUSED and NOTHING WAS GRADED: exit 2, which is not a PASS",
			seenJSON, storeRoot, len(problems), strings.Join(problems, "; "))
	}
	return nil
}
