package conformance

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	shared "github.com/gerege/nexus/internal/conformance"
)

// Admit returns the ordered list of reasons a vector is INADMISSIBLE, empty if
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused,
// and a vector that fails to declare what it exercises, where it came from, or
// who grades it is refused rather than given the benefit of the doubt.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != PartiesContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, PartiesContext))
	}
	if v.CaseID == "" {
		problems = append(problems, "case_id is empty")
	}
	if v.Title == "" {
		problems = append(problems, "title is empty")
	}
	if v.Note == "" {
		problems = append(problems, "_note is empty: every vector must carry its provenance")
	}

	if v.Class != ClassParity {
		problems = append(problems, fmt.Sprintf("class %q: only %q vectors may be graded by this harness", v.Class, ClassParity))
	}
	if !IsSchemaSeam(v.Oracle.Seam) {
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only the client-status-ordinal, legal-form-ordinal and grouping-status-ordinal seams", v.Oracle.Seam))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	problems = append(problems, admitProvenance(v.Provenance, opts.RepoRoot)...)

	if v.TenantParams == nil {
		problems = append(problems, "tenant_params is missing: every parity vector must record the tenant context it was captured under")
	} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
		problems = append(problems, fmt.Sprintf(
			"tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
	} else if err := validateTenantParams(v.TenantParams); err != nil {
		problems = append(problems, err.Error())
	}

	if !IsVocabulary(v.Request.Vocabulary) {
		problems = append(problems, fmt.Sprintf(
			"request.vocabulary %q is not one of client-status, legal-form, grouping-status", v.Request.Vocabulary))
	} else if s := seamForVocabulary(v.Request.Vocabulary); v.Oracle.Seam != "" && s != v.Oracle.Seam {
		problems = append(problems, fmt.Sprintf(
			"request.vocabulary %q must grade against oracle.seam %q, got %q", v.Request.Vocabulary, s, v.Oracle.Seam))
	}
	if v.Request.Name == "" {
		problems = append(problems, "request.name is empty")
	}
	if v.Expect.Ordinal < 0 {
		problems = append(problems, fmt.Sprintf(
			"expect.ordinal %d is negative: Fineract enum ordinals are non-negative", v.Expect.Ordinal))
	}

	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// admitProvenance runs the shared parity-provenance admission (kind, capture_ref,
// sha256, case_id presence) and then adds the capture_case_id containment check
// the shared core leaves to the caller.
func admitProvenance(p Provenance, repoRoot string) []string {
	problems := shared.AdmitCaptureProvenance(shared.CaptureProvenance{
		Kind:          p.Kind,
		CaptureRef:    p.CaptureRef,
		CaptureSHA256: p.CaptureSHA256,
		CaptureCaseID: p.CaptureCaseID,
	}, repoRoot)
	if repoRoot != "" && p.CaptureRef != "" && p.CaptureCaseID != "" {
		abs := filepath.Join(repoRoot, filepath.FromSlash(p.CaptureRef))
		if raw, err := os.ReadFile(abs); err == nil {
			if !strings.Contains(string(raw), p.CaptureCaseID) {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_case_id %q does not appear in %q", p.CaptureCaseID, p.CaptureRef))
			}
		}
	}
	return problems
}

// validateTenantParams records the tenant context. The parties captures were
// taken under the gerege tenant; a vector must state the exact context, uniform
// with the money contexts even though parties grades no money.
func validateTenantParams(tp *TenantParams) error {
	var problems []string
	if tp.RoundingMode == "" {
		problems = append(problems, "tenant_params.rounding_mode is empty")
	}
	if tp.RoundingOrdinal == 0 {
		problems = append(problems, "tenant_params.rounding_ordinal is 0")
	}
	if tp.Precision == 0 {
		problems = append(problems, "tenant_params.precision is 0")
	}
	if tp.Currency == "" {
		problems = append(problems, "tenant_params.currency is empty")
	}
	if tp.MinorUnits == 0 {
		problems = append(problems, "tenant_params.minor_units is 0")
	}
	if tp.Timezone == "" {
		problems = append(problems, "tenant_params.timezone is empty")
	}
	if len(problems) > 0 {
		sort.Strings(problems)
		return fmt.Errorf("tenant_params: %s", strings.Join(problems, "; "))
	}
	return nil
}

// checkGradedAgainst refuses a graded_against name that no implementation
// registered, and a completely empty graded_against list.
func checkGradedAgainst(v *Vector) []string {
	var problems []string
	if len(v.GradedAgainst) == 0 {
		return []string{"graded_against is empty: a vector must name at least one registered implementation it grades"}
	}
	for _, name := range v.GradedAgainst {
		if _, ok := Lookup(name); !ok {
			problems = append(problems, fmt.Sprintf("graded_against %q is not a registered implementation", name))
		}
	}
	return problems
}
