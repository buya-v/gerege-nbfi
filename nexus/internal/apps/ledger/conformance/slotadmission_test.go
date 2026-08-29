package conformance

import (
	"strings"
	"testing"
)

// TestSlotAdmissionInputsAreDefaultDeny drives the per-leg and mapping-table
// admissibility rules T391 added with the accounting-path inputs.
//
// WHY THIS FILE EXISTS [T421, closing T406's F-T406-2]. T391 added ELEVEN
// default-deny branches to admit.go and shipped every one of them with no test.
// That contradicted three things T391 itself invoked: it modelled the rules
// explicitly on T294's opening-balance inputs, which carry sixteen `Admit(`
// drives in openingbalance_test.go; its own capsql-readonly.sh header cites P-45,
// "a guard nobody has watched fail enforces nothing", and then drives that guard
// RED; and the whole RegisterWrong apparatus (P-10) exists because a rule nothing
// executes is decoration. T406 drove all eleven by hand in a scratch worktree and
// found all eleven CORRECT — so this is a missing-evidence defect and not a
// behaviour defect, and the fix is to commit the drives so the next reader does
// not have to rediscover that they work, and so the next refactor of admit.go has
// something holding these branches in place.
//
// T406's finding names TEN branches. There are ELEVEN: the list omits the
// `product_mappings[i].gl_account_id <= 0` branch, which sits between the
// duplicate-slot check and the off-the-chart check and is the one that catches a
// mapping row whose account is missing entirely rather than merely unknown. It is
// driven here as arm 11.
//
// THE ANTI-VACUITY CONTROL IS THE FIRST SUB-TEST, for T294's reason: without it,
// a rule that refused EVERYTHING would satisfy every RED arm below while making
// the corpus inadmissible, and this file would report that as success (P-35).
//
// EVERY ARM ALSO ASSERTS THE REASON, NOT MERELY A REFUSAL. `Admit` returns a
// slice of reasons and a mutation can easily trip a rule other than the one under
// test — the negative-slot-code arm, for instance, sits in a `switch` whose first
// two cases would otherwise swallow it. Matching the reason text is what makes
// each arm a drive of ITS OWN branch.
//
// NOTHING HERE TOUCHES MONEY. Every mutation is to an account id, a slot code, a
// product id or the mapping table; no amount is read, written or compared, and no
// value in this file is ever a float.
func TestSlotAdmissionInputsAreDefaultDeny(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := pickAccountingPathVector(t, vs)

	t.Run("the committed accounting-path vector is ADMITTED", func(t *testing.T) {
		if reasons := Admit(base, opts); len(reasons) != 0 {
			t.Fatalf("the committed vector %s is REFUSED, so every RED arm below could be red for "+
				"that reason instead of for the rule it tests: %s",
				base.CaseID, strings.Join(reasons, "; "))
		}
	})

	// --- the three per-leg branches, which are one `switch` ------------------

	t.Run("1. a leg carrying BOTH gl_account_id and slot_code REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.Legs[0].AccountID = 41
		mustRefuseSlot(t, Admit(v, opts), "carries BOTH gl_account_id",
			"a leg that names the account AND the slot hands the implementation the answer it was "+
				"supposed to resolve, and expect.legs[0].gl_account_id silently stops being an output")
	})

	t.Run("2. a leg carrying NEITHER gl_account_id nor slot_code REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.Legs[0].SlotCode = 0
		mustRefuseSlot(t, Admit(v, opts), "carries NEITHER a gl_account_id",
			"a leg that names neither has said nothing about where it landed or how it got there")
	})

	t.Run("3. a NEGATIVE per-leg slot_code REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.Legs[0].SlotCode = -7
		mustRefuseSlot(t, Admit(v, opts), "A placeholder code is a positive",
			"acc_product_mapping.financial_account_type is a positive integer; a negative one names "+
				"no slot in either loan family")
	})

	// --- the two rules that bind where a product took part -------------------

	t.Run("4. per-leg slot codes with an EMPTY mapping table REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductMappings = nil
		mustRefuseSlot(t, Admit(v, opts), "request.product_mappings is EMPTY",
			"with no rows there is nothing to resolve the slot through, and the vector would reach "+
				"the port and become a HARNESS ERROR rather than a refusal")
	})

	t.Run("5. an ENTRY-LEVEL slot_code alongside per-leg codes REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.SlotCode = 7
		mustRefuseSlot(t, Admit(v, opts), "AND request.legs carry per-leg slot codes",
			"P-1's entry-level slot_code names ONE slot and an accrual transaction spans SIX; two "+
				"places to say which slot an entry used is two places that can disagree")
	})

	// --- the rules that bind everywhere, product or not ----------------------

	t.Run("6. per-leg slot codes with product_id 0 REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductID = 0
		mustRefuseSlot(t, Admit(v, opts), "request.product_id is 0",
			"acc_product_mapping is keyed on (product_id, product_type, financial_account_type), so "+
				"a slot with no product is a key with a hole in it")
	})

	t.Run("7. a mapping table NO leg resolves through REFUSES", func(t *testing.T) {
		v := pickManualVector(t, vs)
		v.Request.ProductMappings = []ProductMapping{
			{SlotCode: 7, GLAccountID: v.Request.Accounts[0].ID},
		}
		mustRefuseSlot(t, Admit(v, opts), "NO leg resolves through any of them",
			"an input nothing consumes is exactly how the opening-balance fields would have "+
				"accumulated on the manual corpus")
	})

	t.Run("8. a mapping row with slot_code 0 REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductMappings[0].SlotCode = 0
		mustRefuseSlot(t, Admit(v, opts), "a placeholder code is positive",
			"a mapping row that names slot 0 names no slot at all")
	})

	t.Run("9. a DUPLICATE slot_code in the mapping table REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductMappings[1].SlotCode = v.Request.ProductMappings[0].SlotCode
		mustRefuseSlot(t, Admit(v, opts), "names slot_code 1 twice",
			"the oracle's own lookup is getSingleResult() and a duplicate is an ERROR there, not a "+
				"first-match; a vector carrying one asserts an observation the oracle would have refused")
	})

	t.Run("10. a mapping row OFF THE CHART REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductMappings[0].GLAccountID = 9999
		mustRefuseSlot(t, Admit(v, opts), "which is NOT in",
			"a mis-keying port landing on that row would fail as a HARNESS ERROR rather than as a "+
				"graded cell difference, and a defect that shows up as a crash is one the comparator "+
				"did not catch — which is precisely the defect ledger-wrong-mapping-key-ignored "+
				"exists to be caught by")
	})

	t.Run("11. a mapping row with a NON-POSITIVE gl_account_id REFUSES", func(t *testing.T) {
		v := copyForMutation(base)
		v.Request.ProductMappings[0].GLAccountID = 0
		mustRefuseSlot(t, Admit(v, opts), "gl_account_id is 0",
			"the branch T406's finding does not list. A row with no account resolves to nothing, and "+
				"it must not fall through to the off-the-chart check, which would report the wrong "+
				"reason for the right refusal")
	})
}

// mustRefuseSlot asserts that reasons carries needle, and says WHY the rule exists
// when it does not. A drive whose failure message does not state the rule teaches
// the next reader to delete the arm.
func mustRefuseSlot(t *testing.T, reasons []string, needle, why string) {
	t.Helper()
	if !containsSubstring(reasons, needle) {
		t.Fatalf("ADMITTED, or refused for a DIFFERENT reason. Wanted a reason containing %q "+
			"because %s.\nreasons = %v", needle, why, reasons)
	}
	t.Logf("REFUSED as designed (reason contains %q)", needle)
}

// copyForMutation returns a Vector whose Legs, ProductMappings and Accounts are
// OWN COPIES.
//
// THIS IS NOT DEFENSIVE PADDING. `v := *base` is a shallow copy and every slice
// in it still shares the loaded store's backing array, so an arm that wrote
// `v.Request.Legs[0].AccountID` would mutate the vector every LATER arm reads —
// and the sub-tests would then pass or fail depending on the order they ran in.
// That is the failure mode a per-arm copy exists to make impossible.
func copyForMutation(base *Vector) *Vector {
	v := *base
	v.Request.Legs = append([]RequestLeg(nil), base.Request.Legs...)
	v.Request.ProductMappings = append([]ProductMapping(nil), base.Request.ProductMappings...)
	v.Request.Accounts = append([]Account(nil), base.Request.Accounts...)
	return &v
}

// pickAccountingPathVector returns a committed vector that actually carries
// per-leg slot codes and a mapping table, and FAILS if there is none.
//
// It selects by SHAPE rather than by case id: a file rename must not silently
// turn this whole file into a no-op, which is the vacuity P-35 names.
func pickAccountingPathVector(t *testing.T, vs []*Vector) *Vector {
	t.Helper()
	for _, v := range vs {
		if len(v.Request.ProductMappings) == 0 {
			continue
		}
		for _, l := range v.Request.Legs {
			if l.SlotCode != 0 {
				return v
			}
		}
	}
	t.Fatal("NO committed vector carries per-leg slot codes and a product mapping table, so every " +
		"arm in this file would have nothing to perturb. The accounting-path admission rules are " +
		"UNDRIVEN and this file must not report that as a pass")
	return nil
}

// pickManualVector returns a mutable copy of a committed vector with NO slot leg
// — the corpus the mapping-table field must not be able to accumulate on.
func pickManualVector(t *testing.T, vs []*Vector) *Vector {
	t.Helper()
	for _, v := range vs {
		slot := false
		for _, l := range v.Request.Legs {
			if l.SlotCode != 0 {
				slot = true
			}
		}
		if !slot && len(v.Request.ProductMappings) == 0 && len(v.Request.Accounts) > 0 {
			return copyForMutation(v)
		}
	}
	t.Fatal("NO committed vector is free of slot legs, so arm 7 has nothing to plant a mapping " +
		"table on")
	return nil
}
