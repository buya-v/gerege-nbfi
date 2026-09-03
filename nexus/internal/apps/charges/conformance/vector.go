package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.charges.vector/v1"

// ChargesContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const ChargesContext = "charges"

// SeamChargeEvaluate is the one capture seam this schema grades: a charge
// definition and a base amount in, validation codes or a fee amount out.
const SeamChargeEvaluate = "charge-evaluate"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
//
// A vector's schema, its directory and the comparator that grades it name ONE
// context, and the check is stated in both directions so that copying a vector
// into a new directory and changing two strings cannot raise a parity count.
func SchemaContexts() []string { return []string{ChargesContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a charges vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// charges parity tally.
	ClassParity VectorClass = "parity"
)

// ExpectKind distinguishes the two shapes an oracle observation can take.
type ExpectKind string

const (
	// ExpectValidation expects an ordered list of construction-validation codes.
	ExpectValidation ExpectKind = "validation"

	// ExpectFee expects a valid charge and a computed fee in integer minor units.
	ExpectFee ExpectKind = "fee"
)

// OracleStamp records where and against what the expectation was captured.
type OracleStamp struct {
	Seam           string `json:"seam"`
	FineractCommit string `json:"fineract_commit"`
}

// ChargeRequest is the charge definition and base amount the implementation is
// graded on, in the stored/observable form the oracle works from.
//
// Monetary values are INTEGER STRINGS of minor units; Percentage is the integer
// micro-per-cent Percent (not money). The four enum fields carry stored values.
type ChargeRequest struct {
	Name            string  `json:"name"`
	CurrencyCode    string  `json:"currency_code"`
	AmountMinor     string  `json:"amount_minor"`
	Percentage      int64   `json:"percentage"`
	AppliesTo       int32   `json:"applies_to"`
	TimeType        int32   `json:"time_type"`
	CalculationType int32   `json:"calculation_type"`
	PaymentMode     int32   `json:"payment_mode"`
	MinCapMinor     *string `json:"min_cap_minor"`
	MaxCapMinor     *string `json:"max_cap_minor"`
	Penalty         bool    `json:"penalty"`
	Active          bool    `json:"active"`
	Deleted         bool    `json:"deleted"`
	BaseAmountMinor string  `json:"base_amount_minor"`
}

// ChargeExpect is what the oracle produced for the request.
type ChargeExpect struct {
	Kind            ExpectKind `json:"kind"`
	ValidationCodes []string   `json:"validation_codes"`
	FeeMinor        string     `json:"fee_minor"`
}

// Vector is one charges golden vector.
type Vector struct {
	Schema  string        `json:"schema"`
	CaseID  string        `json:"case_id"`
	Title   string        `json:"title"`
	Class   VectorClass   `json:"class"`
	Context string        `json:"context"`
	Note    string        `json:"_note"`
	Oracle  OracleStamp   `json:"oracle"`
	Request ChargeRequest `json:"request"`
	Expect  ChargeExpect  `json:"expect"`
	// CapabilitiesRequired states what this vector exercises, for the
	// capability registry's default-deny check.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as a charges vector.
type LoadError struct {
	Path string
	Err  error
}

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
//
// It runs BEFORE any typed decoding, so a float in a field the typed shape
// ignores is still caught. The rule is shared with the loanschedule and ledger
// harnesses; the code is not imported from either because this package is an
// independent schema and must not depend on the harnesses it sits beside.
func RejectFloatTokens(raw []byte) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	for {
		tok, err := dec.Token()
		if err != nil {
			if err.Error() == "EOF" {
				return nil
			}
			return fmt.Errorf("scanning for float tokens: %w", err)
		}
		n, ok := tok.(json.Number)
		if !ok {
			continue
		}
		s := n.String()
		if strings.ContainsAny(s, ".eE") {
			return fmt.Errorf(
				"FLOAT TOKEN %q in charges vector JSON: every number in a vector file must be an integer, "+
					"and every monetary value must be an integer STRING in minor units", s)
		}
	}
}

// schemaProbe is the minimal shape used to decide WHICH schema a file claims.
type schemaProbe struct {
	Schema string `json:"schema"`
}

// DeclaresChargesSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1. It decodes one field, non-strictly, and
// answers yes/no: a malformed charges vector must reach this loader and be
// reported here BY NAME, not fall back to another loader.
func DeclaresChargesSchema(raw []byte) bool {
	var p schemaProbe
	if err := json.Unmarshal(raw, &p); err != nil {
		return false
	}
	return p.Schema == SchemaV1
}

// FileDeclaresChargesSchema is DeclaresChargesSchema over a path. An unreadable
// file is NOT a charges file: it stays with the caller, which reports it.
func FileDeclaresChargesSchema(absPath string) bool {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return false
	}
	return DeclaresChargesSchema(raw)
}

// LoadVector reads and strictly decodes one charges vector file: a raw float
// scan first, then a typed decode with unknown fields disallowed.
func LoadVector(absPath, relPath string) (*Vector, error) {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return nil, err
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var v Vector
	if err := dec.Decode(&v); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("decode: trailing content after the vector object")
	}
	v.Path = relPath
	return &v, nil
}

// LoadStore walks the store root and loads every charges-schema .json under it.
//
// contextFilter, when non-empty, selects a single context directory. The
// duplicate-case_id census is taken over the WHOLE charges population before the
// filter: the filter narrows what is GRADED, never what is CHECKED.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, nil, fmt.Errorf("charges vector store %s: %w", storeRoot, err)
	}
	var all, graded []*Vector
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
			if !FileDeclaresChargesSchema(abs) {
				continue
			}
			rel := filepath.Join(ctx, f.Name())
			v, verr := LoadVector(abs, rel)
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
	sortVectors(all)
	sortVectors(graded)
	if derr := DuplicateCaseIDs(all); derr != nil {
		return graded, loadErrs, derr
	}
	return graded, loadErrs, nil
}

// DuplicateCaseIDs refuses a charges population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	seen := map[string][]string{}
	for _, v := range vs {
		seen[v.CaseID] = append(seen[v.CaseID], v.Path)
	}
	var ids []string
	for id, paths := range seen {
		if len(paths) > 1 {
			sort.Strings(paths)
			ids = append(ids, fmt.Sprintf("%s (%s)", id, strings.Join(paths, ", ")))
		}
	}
	if len(ids) == 0 {
		return nil
	}
	sort.Strings(ids)
	return fmt.Errorf(
		"CHARGES STORE DEFECT: case_id declared more than once: %s. A case_id is how a vector is cited "+
			"in a handoff, a gate and a review; two files answering to one id make every citation ambiguous",
		strings.Join(ids, "; "))
}

func sortVectors(vs []*Vector) {
	sort.Slice(vs, func(i, j int) bool {
		if vs[i].Context != vs[j].Context {
			return vs[i].Context < vs[j].Context
		}
		if vs[i].CaseID != vs[j].CaseID {
			return vs[i].CaseID < vs[j].CaseID
		}
		return vs[i].Path < vs[j].Path
	})
}
