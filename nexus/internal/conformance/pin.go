package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
)

// Pin is the shared store-level comparability pin shape. It pins the Fineract
// commit a vector's oracle observation was taken from and the tenant context
// the capture was taken under. Each context keeps its own schema string and its
// own PIN file name; the shape is identical.
type Pin struct {
	Schema         string       `json:"schema"`
	Note           string       `json:"_note"`
	FineractCommit string       `json:"fineract_commit"`
	TenantParams   TenantParams `json:"tenant_params"`
}

// LoadPin reads a store pin. label is the context name used in the error text.
func LoadPin(path, schema, label string) (*Pin, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("%s pin: %w", label, err)
	}
	if err := RejectFloatTokens(raw, label); err != nil {
		return nil, fmt.Errorf("%s pin %s: %w", label, path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var p Pin
	if err := dec.Decode(&p); err != nil {
		return nil, fmt.Errorf("%s pin %s: decode: %w", label, path, err)
	}
	if p.Schema != schema {
		return nil, fmt.Errorf("%s pin %s: schema %q, want %q", label, path, p.Schema, schema)
	}
	if p.FineractCommit == "" {
		return nil, fmt.Errorf("%s pin %s: fineract_commit is empty", label, path)
	}
	if p.TenantParams == (TenantParams{}) {
		return nil, fmt.Errorf("%s pin %s: tenant_params is empty", label, path)
	}
	return &p, nil
}
