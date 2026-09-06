package conformance

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// SchemaProbe is the minimal shape used to decide WHICH schema a file claims,
// without decoding it as any one context's vector.
type SchemaProbe struct {
	Schema string `json:"schema"`
}

// DeclaresSchema reports whether raw is a JSON object whose top-level "schema"
// member is exactly schema.
//
// THIS IS THE ROUTING PREDICATE, and it is deliberately the weakest possible
// test: it decodes one field, non-strictly, and answers yes/no. It must not
// validate, because a malformed vector has to reach its own loader and be
// reported there BY NAME, not fall back to another schema's loader.
func DeclaresSchema(raw []byte, schema string) bool {
	var p SchemaProbe
	if err := json.Unmarshal(raw, &p); err != nil {
		return false
	}
	return p.Schema == schema
}

// FileDeclaresSchema is DeclaresSchema over a path. An unreadable file does not
// declare the schema: it stays with the caller, which reports it.
func FileDeclaresSchema(absPath, schema string) bool {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return false
	}
	return DeclaresSchema(raw, schema)
}

// SchemaFilePaths walks storeRoot and returns the store-relative paths (slash
// separated, sorted) of every .json file that declares schema. The paths are
// DERIVED, not listed, so a vector added or removed later needs no edit in the
// caller.
func SchemaFilePaths(storeRoot, schema string) ([]string, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := filepath.Join(storeRoot, e.Name())
		files, ferr := os.ReadDir(dir)
		if ferr != nil {
			return nil, ferr
		}
		for _, f := range files {
			if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
				continue
			}
			if FileDeclaresSchema(filepath.Join(dir, f.Name()), schema) {
				out = append(out, filepath.ToSlash(filepath.Join(e.Name(), f.Name())))
			}
		}
	}
	sort.Strings(out)
	return out, nil
}

// VectorIdentity extracts the identity fields the generic store machinery needs
// from a context's vector type.
type VectorIdentity[T any] struct {
	Context func(*T) string
	CaseID  func(*T) string
	Path    func(*T) string
}

// SortVectors orders a vector population by (context, case_id, path) so a run's
// output is a function of the store's contents alone.
func SortVectors[T any](vs []*T, id VectorIdentity[T]) {
	sort.Slice(vs, func(i, j int) bool {
		if id.Context(vs[i]) != id.Context(vs[j]) {
			return id.Context(vs[i]) < id.Context(vs[j])
		}
		if id.CaseID(vs[i]) != id.CaseID(vs[j]) {
			return id.CaseID(vs[i]) < id.CaseID(vs[j])
		}
		return id.Path(vs[i]) < id.Path(vs[j])
	})
}

// DuplicateCaseIDs refuses a population carrying one case_id more than once.
// storeLabel is the context name ("charges", "provisioning", ...) used in the
// refusal; it is upper-cased for the store-defect sentence.
func DuplicateCaseIDs[T any](vs []*T, id VectorIdentity[T], storeLabel string) error {
	seen := map[string][]string{}
	for _, v := range vs {
		seen[id.CaseID(v)] = append(seen[id.CaseID(v)], id.Path(v))
	}
	var ids []string
	for cid, paths := range seen {
		if len(paths) > 1 {
			sort.Strings(paths)
			ids = append(ids, fmt.Sprintf("%s (%s)", cid, strings.Join(paths, ", ")))
		}
	}
	if len(ids) == 0 {
		return nil
	}
	sort.Strings(ids)
	return fmt.Errorf(
		"%s STORE DEFECT: case_id declared more than once: %s. A case_id is how a vector is cited "+
			"in a handoff, a gate and a review; two files answering to one id make every citation ambiguous",
		strings.ToUpper(storeLabel), strings.Join(ids, "; "))
}

// LoadStore walks the store root and loads every file that declares schema.
//
// contextFilter, when non-empty, selects a single context DIRECTORY to grade.
// The duplicate-case_id census is taken over the WHOLE population before the
// filter: the filter narrows what is GRADED, it never narrows what is CHECKED.
//
// decode loads one vector file and binds its store-relative path; id supplies
// the identity fields the census and sort read back. label is the context name
// used in error text.
func LoadStore[T any](storeRoot, contextFilter, schema, label string, id VectorIdentity[T], decode func(absPath, relPath string) (*T, error)) ([]*T, []LoadError, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, nil, fmt.Errorf("%s vector store %s: %w", label, storeRoot, err)
	}
	var all, graded []*T
	var loadErrs []LoadError
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		ctx := e.Name()
		selected := contextFilter == "" || ctx == contextFilter
		dir := filepath.Join(storeRoot, ctx)
		files, ferr := os.ReadDir(dir)
		if ferr != nil {
			return nil, nil, ferr
		}
		for _, f := range files {
			if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
				continue
			}
			abs := filepath.Join(dir, f.Name())
			if !FileDeclaresSchema(abs, schema) {
				continue
			}
			rel := filepath.Join(ctx, f.Name())
			v, verr := decode(abs, rel)
			if verr != nil {
				loadErrs = append(loadErrs, LoadError{Path: rel, Err: verr})
				continue
			}
			all = append(all, v)
			if selected {
				graded = append(graded, v)
			}
		}
	}
	SortVectors(all, id)
	SortVectors(graded, id)
	if derr := DuplicateCaseIDs(all, id, label); derr != nil {
		return graded, loadErrs, derr
	}
	return graded, loadErrs, nil
}
