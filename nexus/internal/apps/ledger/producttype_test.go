package ledger

import "testing"

// TRAP 1. The two directions are two functions, and they are tested separately
// because that is the only way the permutation can be seen: a round-trip test
// written against LOAN, SAVING and WORKING_CAPITAL_LOAN passes with a single
// shared table, and those are exactly the three members a first test reaches
// for.

func TestProductTypeStoredValuesMatchTheOracle(t *testing.T) {
	// [VERIFIED: PortfolioProductType.java:26-31, re-read at pinned sha
	// 426a23544e8426a38ae43ae404670a0a7e85b9eb by this worker]
	want := map[PortfolioProductType]int32{
		ProductLoan:               1,
		ProductSaving:             2,
		ProductClient:             5,
		ProductProvisioning:       3,
		ProductShares:             4,
		ProductWorkingCapitalLoan: 6,
	}
	for pt, v := range want {
		if got := pt.StoredValue(); got != v {
			t.Errorf("%v.StoredValue() = %d, want %d", pt, got, v)
		}
	}
}

func TestProductTypeDecodeIsTheTrueInverseOfEncode(t *testing.T) {
	for _, pt := range []PortfolioProductType{
		ProductLoan, ProductSaving, ProductClient,
		ProductProvisioning, ProductShares, ProductWorkingCapitalLoan,
	} {
		back, ok := ProductTypeFromStoredValue(pt.StoredValue())
		if !ok {
			t.Fatalf("ProductTypeFromStoredValue(%d) not ok", pt.StoredValue())
		}
		if back != pt {
			t.Errorf("round trip broken: %v -> %d -> %v", pt, pt.StoredValue(), back)
		}
	}
	if _, ok := ProductTypeFromStoredValue(7); ok {
		t.Error("ProductTypeFromStoredValue(7) should not decode")
	}
	if _, ok := ProductTypeFromStoredValue(0); ok {
		t.Error("ProductTypeFromStoredValue(0) should not decode")
	}
}

// TestFineractFromIntQuirkPermutesThreeFourFive is the whole point of trap 1.
// If this test ever passes with FineractFromIntQuirk == ProductTypeFromStoredValue,
// somebody has collapsed the two directions into one table and the port is
// silently wrong for provisioning, shares and client.
func TestFineractFromIntQuirkPermutesThreeFourFive(t *testing.T) {
	// [VERIFIED: PortfolioProductType.java:51-59 — case 3 -> CLIENT,
	// case 4 -> PROVISIONING, case 5 -> SHARES]
	quirk := map[int32]PortfolioProductType{
		1: ProductLoan,
		2: ProductSaving,
		3: ProductClient,
		4: ProductProvisioning,
		5: ProductShares,
		6: ProductWorkingCapitalLoan,
	}
	for v, want := range quirk {
		got, ok := FineractFromIntQuirk(v)
		if !ok {
			t.Fatalf("FineractFromIntQuirk(%d) not ok", v)
		}
		if got != want {
			t.Errorf("FineractFromIntQuirk(%d) = %v, want %v", v, got, want)
		}
	}

	// The damage: fromInt(x).getValue() != x for x in {3,4,5}, and it is a
	// 3-cycle 3 -> 5 -> 4 -> 3.
	cycle := map[int32]int32{3: 5, 4: 3, 5: 4}
	for in, wantOut := range cycle {
		got, _ := FineractFromIntQuirk(in)
		if got.StoredValue() != wantOut {
			t.Errorf("quirk cycle broken at %d: FineractFromIntQuirk(%d).StoredValue() = %d, want %d",
				in, in, got.StoredValue(), wantOut)
		}
	}

	// And it agrees with the true inverse on exactly 1, 2 and 6 — the worst
	// possible distribution, because those are the three a loan-shaped first
	// test exercises.
	var agree, disagree []int32
	for v := int32(1); v <= 6; v++ {
		q, _ := FineractFromIntQuirk(v)
		d, _ := ProductTypeFromStoredValue(v)
		if q == d {
			agree = append(agree, v)
		} else {
			disagree = append(disagree, v)
		}
	}
	if len(agree) != 3 || agree[0] != 1 || agree[1] != 2 || agree[2] != 6 {
		t.Errorf("expected the quirk to agree with the inverse on exactly {1,2,6}, got %v", agree)
	}
	if len(disagree) != 3 || disagree[0] != 3 || disagree[1] != 4 || disagree[2] != 5 {
		t.Errorf("expected the quirk to disagree on exactly {3,4,5}, got %v", disagree)
	}
}

// TestProductTypeStringMatchesJavaToString grades the refusal-message rendering
// against the oracle's own words.
func TestProductTypeStringMatchesJavaToString(t *testing.T) {
	// [OBSERVED: A2-224-chargeoff-unmapped — "Mapping for product of type LOAN
	// with Id 46 does not exist ..."]
	if got := ProductLoan.String(); got != "LOAN" {
		t.Errorf("ProductLoan.String() = %q, want %q", got, "LOAN")
	}
	// [VERIFIED: PortfolioProductType.java:44-46 — name().replace("_", " ")]
	if got := ProductWorkingCapitalLoan.String(); got != "WORKING CAPITAL LOAN" {
		t.Errorf("ProductWorkingCapitalLoan.String() = %q, want %q", got, "WORKING CAPITAL LOAN")
	}
}

func TestAccountingRuleCodesMatchTheCapturedProductReads(t *testing.T) {
	var cash struct {
		AccountingRule struct {
			ID   int32  `json:"id"`
			Code string `json:"code"`
			Val  string `json:"value"`
		} `json:"accountingRule"`
	}
	decodeCapture(t, "A2-212-read-product22-channel-override", &cash)
	if cash.AccountingRule.ID != AccountingRuleCashBased.StoredValue() ||
		cash.AccountingRule.Code != AccountingRuleCashBased.Code() ||
		cash.AccountingRule.Val != AccountingRuleCashBased.String() {
		t.Errorf("cash rule mismatch: capture {%d,%q,%q} vs port {%d,%q,%q}",
			cash.AccountingRule.ID, cash.AccountingRule.Code, cash.AccountingRule.Val,
			AccountingRuleCashBased.StoredValue(), AccountingRuleCashBased.Code(), AccountingRuleCashBased.String())
	}

	var accrual struct {
		AccountingRule struct {
			ID   int32  `json:"id"`
			Code string `json:"code"`
			Val  string `json:"value"`
		} `json:"accountingRule"`
	}
	decodeCapture(t, "A2-213-read-product28-accrual", &accrual)
	if accrual.AccountingRule.ID != AccountingRuleAccrualPeriodic.StoredValue() ||
		accrual.AccountingRule.Code != AccountingRuleAccrualPeriodic.Code() ||
		accrual.AccountingRule.Val != AccountingRuleAccrualPeriodic.String() {
		t.Errorf("accrual rule mismatch: capture {%d,%q,%q} vs port {%d,%q,%q}",
			accrual.AccountingRule.ID, accrual.AccountingRule.Code, accrual.AccountingRule.Val,
			AccountingRuleAccrualPeriodic.StoredValue(), AccountingRuleAccrualPeriodic.Code(), AccountingRuleAccrualPeriodic.String())
	}
}
