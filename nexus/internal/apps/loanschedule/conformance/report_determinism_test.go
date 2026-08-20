package conformance

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

// TestReportIsByteIdenticalAcrossRenders is the regression guard for finding T90.
//
// THE DEFECT IT GUARDS. WriteReport used to `range` s.CounterfactualCoverage, a
// map, so Go's randomised iteration order moved the "killed by" lines between two
// runs of ONE binary on ONE store. Measured on main's bytes: 30 runs, 2 distinct
// sha256, split 26/4 (T81 measured 23/7 and T86 27/3 on the same defect). That is
// not cosmetic in this pipeline, which uses byte-identity of harness output as
// evidence that a change was inert.
//
// THIS GUARD HAS BEEN DRIVEN RED. Re-pointed at the pre-fix loop it fails on the
// first render pair: with twelve keys the runtime randomises both the start
// offset and the traversal, so 200 renders agreeing is not a thing that happens.
// The transcript of that red run is in the T90 handoff. A guard nobody has
// watched fail is not a guard (P-22).
func TestReportIsByteIdenticalAcrossRenders(t *testing.T) {
	// Twelve capabilities, declared in an order that is neither sorted nor
	// reverse-sorted, with ids likewise out of order, so this fails both if the
	// KEYS are unsorted and if the IDS within a key are.
	coverage := map[string][]string{
		"schedule.core":       {"Z-KILL", "A-KILL", "M-KILL [structural]"},
		"monthend.reanchor":   {"MONTHEND-CONTINUE-FROM-CLAMPED-DAY", "MONTHEND-CONTINUE-FROM-CLAMPED-DAY"},
		"daycount.days30":     {"D30-KILL"},
		"daycount.days360":    {"D360-KILL"},
		"rounding.halfup":     {"HU-KILL"},
		"precision.p19":       {"P19-KILL"},
		"downpayment.enabled": {"DP-KILL"},
		"charges.flat":        {"CF-KILL"},
		"charges.percent":     {"CP-KILL"},
		"zeroprincipal.guard": {"ZP-KILL"},
		"rowkind.ordering":    {"RO-KILL [structural]"},
		"seam.pathb":          {"PB-KILL"},
	}
	s := &Summary{
		StoreRoot:              "/store",
		ImplementationName:     "test",
		OracleProbe:            "up",
		CounterfactualCoverage: coverage,
	}

	const renders = 200
	first := render(s)
	for i := 1; i < renders; i++ {
		if got := render(s); got != first {
			t.Fatalf("WriteReport is NOT byte-reproducible: render %d differs from render 0. An unsorted "+
				"map iteration reached the report, and every proof in this program that rests on diffing "+
				"one harness run against another is weakened by it.\n--- render 0 ---\n%s\n--- render %d ---\n%s",
				i, first, i, got)
		}
	}

	// And the order is the DOCUMENTED one, not merely some fixed one: keys
	// ascending byte-wise, ids ascending byte-wise within the line. A test that
	// asserted only "stable" would pass on whatever order the runtime froze.
	var printedKeys []string
	for _, line := range strings.Split(first, "\n") {
		i := strings.Index(line, " killed by ")
		if i < 0 || !strings.HasPrefix(line, "    ") {
			continue
		}
		key := strings.TrimSpace(line[:i])
		printedKeys = append(printedKeys, key)
		ids := strings.Split(line[i+len(" killed by "):], ", ")
		if !sort.StringsAreSorted(ids) {
			t.Errorf("counterfactual ids for %q are not in ascending order: %v", key, ids)
		}
	}
	if len(printedKeys) != len(coverage) {
		t.Fatalf("report printed %d coverage lines, want %d", len(printedKeys), len(coverage))
	}
	if !sort.StringsAreSorted(printedKeys) {
		t.Errorf("coverage lines are not in ascending capability order: %v", printedKeys)
	}
}

// TestDeclarationDefectsAreReportedInAStableOrder covers the SECOND unsorted
// iteration T90's sweep found: declarationDefects ranged an AttestationSource's
// ColumnsByRowKind. Every string it appends is printed as a "HARNESS DECLARATION
// DEFECT" fatal reason, so an unsorted range reorders a FATAL-REASONS BLOCK
// between two runs — the section a reader is most likely to be diffing.
//
// With the SHIPPED declaration that loop emits nothing, which is why the defect
// was invisible and why no test over the shipped data could have found it. So
// this hands the validator a weakened source with three defective row kinds, the
// only shape in which the order is observable at all. Driven RED against the
// pre-fix loop; transcript in the T90 handoff.
func TestDeclarationDefectsAreReportedInAStableOrder(t *testing.T) {
	weakened := AttestationSource{
		ID:       "t90-bad-row-kinds",
		Citation: "synthetic, for this test only",
		ColumnsByRowKind: map[string][]string{
			"BOGUS_ZEBRA":  {ColDueDate},
			"BOGUS_AARDV":  {ColDueDate},
			"BOGUS_MIDDLE": {ColDueDate},
		},
		Caveats: []string{"synthetic"},
	}
	first := declarationDefects([]AttestationSource{weakened}, Claims(), CoverageGaps(), RoundedTranscriptions())
	if len(first) < 3 {
		t.Fatalf("the weakened source must report one defect per bogus row kind; got %d: %v", len(first), first)
	}
	for i := 0; i < 200; i++ {
		got := declarationDefects([]AttestationSource{weakened}, Claims(), CoverageGaps(), RoundedTranscriptions())
		if strings.Join(got, "\n") != strings.Join(first, "\n") {
			t.Fatalf("declarationDefects is not order-stable: call %d differs.\nfirst: %v\ngot:   %v",
				i, first, got)
		}
	}
	// And stable in the DOCUMENTED order: row kinds ascending byte-wise.
	var seen []string
	for _, d := range first {
		for _, rk := range []string{"BOGUS_AARDV", "BOGUS_MIDDLE", "BOGUS_ZEBRA"} {
			if strings.Contains(d, rk) && (len(seen) == 0 || seen[len(seen)-1] != rk) {
				seen = append(seen, rk)
			}
		}
	}
	if !sort.StringsAreSorted(seen) {
		t.Errorf("row kinds are reported in %v, want ascending order", seen)
	}
}

// TestCapabilityRegistryErrorNamesTheSameDefectEveryTime covers the THIRD site:
// LoadCapabilityRegistry ranged a seam's status map and RETURNED on the first bad
// entry, so a registry with several defective entries named one of them at
// random. Which registries are REJECTED never depended on the order — every path
// there returns an error — so this pins WHICH defect is named, and nothing else.
func TestCapabilityRegistryErrorNamesTheSameDefectEveryTime(t *testing.T) {
	path := filepath.Join(t.TempDir(), "capabilities.json")
	registry := `{
  "schema": "` + CapabilityRegistrySchema + `",
  "note": "synthetic registry for T90's determinism guard",
  "dec1_revision": 0,
  "capabilities": [
    {"name": "known.capability", "description": "d", "in_graded_domain": false, "evidence": "synthetic"}
  ],
  "seams": [
    {"name": "seam.a", "description": "d", "status": {
       "zzz.unknown.capability": "exercised",
       "mmm.unknown.capability": "exercised",
       "aaa.unknown.capability": "exercised"
    }}
  ]
}`
	if err := os.WriteFile(path, []byte(registry), 0o644); err != nil {
		t.Fatalf("WriteFile: %v", err)
	}
	_, err := LoadCapabilityRegistry(path)
	if err == nil {
		t.Fatal("a seam referencing an unknown capability must be a hard error")
	}
	first := err.Error()
	if !strings.Contains(first, "aaa.unknown.capability") {
		t.Errorf("the error must name the lexicographically first offending capability, got: %s", first)
	}
	for i := 0; i < 200; i++ {
		_, err := LoadCapabilityRegistry(path)
		if err == nil {
			t.Fatal("a seam referencing an unknown capability must be a hard error")
		}
		if err.Error() != first {
			t.Fatalf("LoadCapabilityRegistry names a different defect between runs:\nfirst: %s\ngot:   %s",
				first, err.Error())
		}
	}
}
