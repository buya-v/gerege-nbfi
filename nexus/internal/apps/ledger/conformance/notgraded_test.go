package conformance

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// The tests A2-34 F-5 says did not exist.
//
// `TestCellVocabularyIsDerivedFromTheComparator` derives the CELL vocabulary
// from the comparator, and A2-34's finding was precisely that "there is no
// equivalent deriving the GAP block from the registry". These are it.
//
// EVERY ONE OF THEM IS A RED DRIVE (P-22). A test that only asserts the block
// contains the eight rows that happen to be in the file today would pass just as
// well over a hardcoded block — which is exactly the artefact being replaced. So
// each test below CHANGES the registry and requires the rendered block to change
// with it: plant a row and it must appear, remove a row and it must disappear.
// A report nobody has seen change is not derived from anything.

// notGradedNames extracts the printed capability names from a rendered block.
//
// It parses the RENDERED TEXT rather than the intermediate slice on purpose: the
// intermediate slice being right while the renderer drops rows is the defect
// class this file exists to catch, and reading the struct would not see it.
func notGradedNames(lines []string) []string {
	var out []string
	for _, l := range lines {
		t := strings.TrimSpace(l)
		if !strings.HasPrefix(t, "* ") || !strings.HasSuffix(t, " — NOT IN THE GRADED DOMAIN") {
			continue
		}
		out = append(out, strings.TrimSuffix(strings.TrimPrefix(t, "* "),
			" — NOT IN THE GRADED DOMAIN"))
	}
	return out
}

func renderFrom(reg *CapabilityRegistry, vs []*Vector) []string {
	s := &Summary{NotGraded: notGradedRows(reg, vs)}
	return s.NotGradedLines()
}

// TestEveryDeclaredGapIsPrinted is F-5 as a gate.
//
// THE COUNT IS ASSERTED AGAINST THE REGISTRY, never against a literal. A literal
// would have to be edited by the same person who added the row, which is the
// hand-maintenance this whole change removes.
func TestEveryDeclaredGapIsPrinted(t *testing.T) {
	vs, opts := loadCommitted(t)
	reg := opts.Registry

	declared := reg.NotGradedCapabilities()
	if len(declared) == 0 {
		t.Fatal("the committed registry declares NO not-graded capability, so every assertion in " +
			"this file would pass over nothing (P-35)")
	}

	printed := notGradedNames(renderFrom(reg, vs))
	if len(printed) != len(declared) {
		t.Fatalf("the registry declares %d in_graded_domain:false capabilities and the report prints "+
			"%d. This is A2-34 F-5 exactly: printed %v", len(declared), len(printed), printed)
	}
	got := map[string]bool{}
	for _, n := range printed {
		got[n] = true
	}
	for _, c := range declared {
		if !got[c.Name] {
			t.Errorf("capability %q is declared in_graded_domain:false and is NOT PRINTED. A declared "+
				"gap the report does not print is a gap that will be forgotten", c.Name)
		}
	}

	// THE TWO A2-34 CAUGHT, NAMED. Not because the loop above misses them — it
	// does not — but because a future edit that drops them should fail with
	// their names in the message rather than with an arithmetic mismatch.
	for _, want := range []string{"ledger.slot.resolution", "ledger.reversal.entry"} {
		if !got[want] {
			t.Errorf("%q is not printed. It is one of the two rows the hand-written block dropped "+
				"(A2-34 F-5), and one of them was added by the task that reported all of them printed",
				want)
		}
	}
	t.Logf("%d declared, %d printed: %s", len(declared), len(printed), strings.Join(printed, ", "))
}

// TestPlantingANotGradedRowMakesItAppear is the RED DRIVE in the additive
// direction: the report must move when the registry moves.
func TestPlantingANotGradedRowMakesItAppear(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := notGradedNames(renderFrom(opts.Registry, vs))

	planted := *opts.Registry
	planted.Capabilities = append(append([]Capability{}, opts.Registry.Capabilities...), Capability{
		Name:           "ledger.t242.planted.canary",
		Description:    "A row planted by TestPlantingANotGradedRowMakesItAppear.",
		InGradedDomain: false,
		Evidence:       "PLANTED. If this string is not printed, the block is not derived.",
	})

	after := notGradedNames(renderFrom(&planted, vs))
	if len(after) != len(base)+1 {
		t.Fatalf("planted one in_graded_domain:false row; printed rows went %d -> %d, want %d. "+
			"The block is NOT derived from the registry", len(base), len(after), len(base)+1)
	}
	found := false
	for _, n := range after {
		if n == "ledger.t242.planted.canary" {
			found = true
		}
	}
	if !found {
		t.Fatalf("the planted row is absent from the rendered block: %v", after)
	}

	// AND THE EVIDENCE TEXT TRAVELS WITH IT. A block that printed the name and
	// dropped the reason would satisfy the count and still lose the gap.
	plantedFlat := strings.Join(strings.Fields(strings.Join(renderFrom(&planted, vs), "\n")), " ")
	if !strings.Contains(plantedFlat, "If this string is not printed, the block is not derived") {
		t.Error("the planted row's evidence is not rendered; only its name is")
	}
}

// TestRemovingANotGradedRowMakesItDisappear is the RED DRIVE in the subtractive
// direction, and it is the half that matters more: a block that only ever grows
// could be an append-only hardcoded list.
func TestRemovingANotGradedRowMakesItDisappear(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := notGradedNames(renderFrom(opts.Registry, vs))

	const drop = "ledger.charge.off"
	trimmed := *opts.Registry
	trimmed.Capabilities = nil
	for _, c := range opts.Registry.Capabilities {
		if c.Name == drop {
			continue
		}
		trimmed.Capabilities = append(trimmed.Capabilities, c)
	}
	if len(trimmed.Capabilities) != len(opts.Registry.Capabilities)-1 {
		t.Fatalf("%q is not in the committed registry, so this test removed nothing and would "+
			"pass vacuously", drop)
	}

	after := notGradedNames(renderFrom(&trimmed, vs))
	if len(after) != len(base)-1 {
		t.Fatalf("removed one in_graded_domain:false row; printed rows went %d -> %d, want %d",
			len(base), len(after), len(base)-1)
	}
	for _, n := range after {
		if n == drop {
			t.Fatalf("%q was removed from the registry and is STILL PRINTED. The block is "+
				"hardcoded", drop)
		}
	}
}

// TestFlippingIntoTheGradedDomainRemovesTheRow drives the third direction: the
// selector itself. A block derived from `len(Capabilities)` rather than from
// `in_graded_domain` would pass both tests above and fail this one.
func TestFlippingIntoTheGradedDomainRemovesTheRow(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := notGradedNames(renderFrom(opts.Registry, vs))

	flipped := *opts.Registry
	flipped.Capabilities = nil
	hit := false
	for _, c := range opts.Registry.Capabilities {
		if c.Name == "ledger.multi.currency.entry" {
			c.InGradedDomain = true
			hit = true
		}
		flipped.Capabilities = append(flipped.Capabilities, c)
	}
	if !hit {
		t.Fatal("ledger.multi.currency.entry is not in the committed registry; this test is vacuous")
	}
	after := notGradedNames(renderFrom(&flipped, vs))
	if len(after) != len(base)-1 {
		t.Fatalf("flipped one row into the graded domain; printed rows went %d -> %d, want %d",
			len(base), len(after), len(base)-1)
	}
}

// TestUnpostedSlotAccountActivityIsMeasuredFromTheStore is F-4 as a gate.
//
// This is the assertion whose absence let "gl 18, 22, 16 have ZERO journal
// entries" print on every run while gl 16 was a promoted leg of three of the
// four parity vectors in the same report.
func TestUnpostedSlotAccountActivityIsMeasuredFromTheStore(t *testing.T) {
	vs, opts := loadCommitted(t)
	rows := notGradedRows(opts.Registry, vs)

	var accrual *NotGradedCapability
	for i := range rows {
		if rows[i].Name == "ledger.accrual.entry" {
			accrual = &rows[i]
		}
	}
	if accrual == nil {
		t.Fatal("ledger.accrual.entry is not a not-graded row; this test is vacuous")
	}
	if len(accrual.Slots) == 0 {
		t.Fatal("ledger.accrual.entry declares no unposted_slots, so the account-activity " +
			"measurement runs over nothing (P-35)")
	}

	// THE SLOT NAMES ARE DECODED, NOT TRANSCRIBED. If somebody changes a
	// slot_code, the name changes with it; if they change it to a code the
	// oracle's enum does not define, the LOADER refuses (see the loader test
	// below) and this never runs.
	byName := map[string]NotGradedSlot{}
	for _, s := range accrual.Slots {
		byName[s.SlotName] = s
	}
	for _, want := range []string{"INTEREST_RECEIVABLE", "FEES_RECEIVABLE", "PENALTIES_RECEIVABLE"} {
		if _, ok := byName[want]; !ok {
			t.Errorf("the accrual row does not declare a %s slot; declared: %v", want, byName)
		}
	}

	// THE FINDING ITSELF. PENALTIES_RECEIVABLE is backed by gl 16, and gl 16 is
	// NOT an unused account: it is a leg of three parity vectors. The block must
	// SAY so. An implementation that reported it as untouched is the false
	// sentence, restored.
	pen, ok := byName["PENALTIES_RECEIVABLE"]
	if !ok {
		t.Fatal("no PENALTIES_RECEIVABLE slot")
	}
	if len(pen.PromotedLegCases) == 0 {
		t.Fatalf("gl %d backs PENALTIES_RECEIVABLE and the harness measured NO promoted leg on it. "+
			"A2-34 F-4 measured 16 journal entries on that account and three promoted parity "+
			"vectors carrying it as a leg. Either the store changed or the measurement is broken",
			pen.GLAccountID)
	}

	// FLATTENED BEFORE MATCHING. The block is word-wrapped, so a sentence that
	// is certainly printed may straddle a line break — this assertion is about
	// what the block SAYS, not about where the wrapper put the newlines. (Caught
	// by this test failing on its first run against a renderer that was correct:
	// the phrase below wraps after "THE SLOT IS".)
	rendered := strings.Join((&Summary{NotGraded: rows}).NotGradedLines(), "\n")
	flat := strings.Join(strings.Fields(rendered), " ")
	if !strings.Contains(flat, "THE SLOT IS UNPOSTED; THE ACCOUNT IS NOT EMPTY") {
		t.Error("the rendered block does not distinguish an unposted SLOT from an empty ACCOUNT, " +
			"which is the conflation that made the old sentence false")
	}
	for _, c := range pen.PromotedLegCases {
		if !strings.Contains(flat, c) {
			t.Errorf("vector %q carries a leg on gl %d and the block does not name it",
				c, pen.GLAccountID)
		}
	}

	// AND THE OTHER TWO MUST STILL READ AS UNTOUCHED-BY-THE-CORPUS. Without
	// this, an implementation that annotated every slot as busy would pass the
	// assertion above and say nothing.
	for _, want := range []string{"INTEREST_RECEIVABLE", "FEES_RECEIVABLE"} {
		if n := len(byName[want].PromotedLegCases); n != 0 {
			t.Errorf("%s (gl %d) is reported with %d promoted leg(s); the committed corpus has none",
				want, byName[want].GLAccountID, n)
		}
	}
	t.Logf("PENALTIES_RECEIVABLE -> gl %d, promoted legs: %v",
		pen.GLAccountID, pen.PromotedLegCases)
}

// TestSlotAccountActivityTracksTheStore drives the measurement RED by moving
// the store rather than the registry: point a declared slot at an account the
// corpus DOES use, and the annotation must flip.
func TestSlotAccountActivityTracksTheStore(t *testing.T) {
	vs, opts := loadCommitted(t)

	// gl 18 has no promoted leg today. Re-point it at gl 4 (LOAN_PORTFOLIO,
	// carried by LDG-02 and LDG-03) and the same code must now report it busy.
	moved := *opts.Registry
	moved.Capabilities = nil
	for _, c := range opts.Registry.Capabilities {
		if c.Name == "ledger.accrual.entry" {
			slots := append([]UnpostedSlot{}, c.UnpostedSlots...)
			for i := range slots {
				if slots[i].GLAccountID == 18 {
					slots[i].GLAccountID = 4
				}
			}
			c.UnpostedSlots = slots
		}
		moved.Capabilities = append(moved.Capabilities, c)
	}

	rows := notGradedRows(&moved, vs)
	for _, r := range rows {
		if r.Name != "ledger.accrual.entry" {
			continue
		}
		for _, s := range r.Slots {
			if s.GLAccountID != 4 {
				continue
			}
			if len(s.PromotedLegCases) == 0 {
				t.Fatal("gl 4 is a leg of LDG-02 and LDG-03 and the annotation reports no promoted " +
					"leg on it. The account-activity figure is NOT measured from the store")
			}
			t.Logf("gl 4 correctly reported busy: %v", s.PromotedLegCases)
			return
		}
	}
	t.Fatal("the re-pointed slot did not appear in the rendered rows")
}

// TestRegistryRefusesAnUndecodableSlotCode is the load-time gate: the slot name
// printed in the report is DERIVED, so a code with no name refuses the run.
func TestRegistryRefusesAnUndecodableSlotCode(t *testing.T) {
	// AccrualAccountsForLoan has 25 members and NO 26 [VERIFIED:
	// AccountingConstants.java:95-122, and slots.go's own comment says so].
	for _, tc := range []struct {
		name string
		slot UnpostedSlot
		want string
	}{
		{"undefined code", UnpostedSlot{ProductID: 28, AccountingRule: "accrual",
			SlotCode: 26, GLAccountID: 18}, "DOES NOT DEFINE"},
		{"unknown rule", UnpostedSlot{ProductID: 28, AccountingRule: "savings",
			SlotCode: 7, GLAccountID: 18}, "accounting_rule"},
		{"zero product", UnpostedSlot{ProductID: 0, AccountingRule: "accrual",
			SlotCode: 7, GLAccountID: 18}, "product_id"},
		{"zero account", UnpostedSlot{ProductID: 28, AccountingRule: "accrual",
			SlotCode: 7, GLAccountID: 0}, "gl_account_id"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			path := writeRegistryWithSlot(t, "ledger.accrual.entry", false, tc.slot)
			_, err := LoadCapabilityRegistry(path)
			if err == nil {
				t.Fatalf("the registry loaded with %+v. An unchecked slot reaches the report as a "+
					"name nobody verified", tc.slot)
			}
			if !strings.Contains(err.Error(), tc.want) {
				t.Errorf("refused, but not for the stated reason: %v", err)
			}
		})
	}

	// THE ANTI-VACUITY CONTROL. If the writer produced a registry that refused
	// for some unrelated reason, every case above would pass while testing
	// nothing.
	ok := writeRegistryWithSlot(t, "ledger.accrual.entry", false, UnpostedSlot{
		ProductID: 28, AccountingRule: "accrual", SlotCode: 9, GLAccountID: 16})
	if _, err := LoadCapabilityRegistry(ok); err != nil {
		t.Fatalf("the CONTROL registry — a well-formed slot — was refused: %v. Every refusal above "+
			"is therefore unproven", err)
	}
}

// TestRegistryRefusesUnpostedSlotsOnAGradedCapability: a slot the corpus never
// posted through cannot belong to a capability the corpus grades.
func TestRegistryRefusesUnpostedSlotsOnAGradedCapability(t *testing.T) {
	path := writeRegistryWithSlot(t, "ledger.journal.entry.readback", true, UnpostedSlot{
		ProductID: 28, AccountingRule: "accrual", SlotCode: 9, GLAccountID: 16})
	_, err := LoadCapabilityRegistry(path)
	if err == nil {
		t.Fatal("a capability marked in_graded_domain:true declared unposted_slots and the " +
			"registry loaded")
	}
	if !strings.Contains(err.Error(), "in_graded_domain TRUE") {
		t.Errorf("refused for the wrong reason: %v", err)
	}
}

// writeRegistryWithSlot copies the committed registry into a temp file, attaches
// one unposted slot to the named capability, and returns the path.
//
// IT COPIES THE REAL FILE rather than hand-building a minimal one, so the loader
// under test walks the same shape it walks in production.
func writeRegistryWithSlot(t *testing.T, capName string, graded bool, slot UnpostedSlot) string {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(storeRoot(t), CapabilityFileName))
	if err != nil {
		t.Fatalf("reading the committed registry: %v", err)
	}
	var doc map[string]any
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatalf("decoding the committed registry: %v", err)
	}
	caps, _ := doc["capabilities"].([]any)
	hit := false
	for _, c := range caps {
		m, _ := c.(map[string]any)
		if m["name"] != capName {
			continue
		}
		hit = true
		m["in_graded_domain"] = graded
		m["unposted_slots"] = []any{map[string]any{
			"product_id":      slot.ProductID,
			"accounting_rule": slot.AccountingRule,
			"slot_code":       slot.SlotCode,
			"gl_account_id":   slot.GLAccountID,
		}}
	}
	if !hit {
		t.Fatalf("capability %q is not in the committed registry", capName)
	}
	out, err := json.Marshal(doc)
	if err != nil {
		t.Fatalf("encoding: %v", err)
	}
	path := filepath.Join(t.TempDir(), CapabilityFileName)
	if err := os.WriteFile(path, out, 0o600); err != nil {
		t.Fatalf("writing: %v", err)
	}
	return path
}
