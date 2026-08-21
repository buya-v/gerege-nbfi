package ledger

import (
	"encoding/json"
	"errors"
	"testing"
)

func TestFinancialActivityValuesMatchTheOracle(t *testing.T) {
	// [VERIFIED: AccountingConstants.java:437-445, re-read by this worker]
	want := []struct {
		activity       FinancialActivity
		value          int32
		code           string
		classification Classification
	}{
		{FinancialActivityAssetTransfer, 100, "assetTransfer", ClassificationAsset},
		{FinancialActivityCashAtMainVault, 101, "cashAtMainVault", ClassificationAsset},
		{FinancialActivityCashAtTeller, 102, "cashAtTeller", ClassificationAsset},
		{FinancialActivityAssetFundSource, 103, "fundSource", ClassificationAsset},
		{FinancialActivityLiabilityTransfer, 200, "liabilityTransfer", ClassificationLiability},
		{FinancialActivityPayableDividends, 201, "payableDividends", ClassificationLiability},
		{FinancialActivityOpeningBalancesTransferContra, 300, "openingBalancesTransferContra", ClassificationEquity},
	}
	for _, w := range want {
		if got := w.activity.StoredValue(); got != w.value {
			t.Errorf("%s value = %d, want %d", w.activity.Name(), got, w.value)
		}
		if got := w.activity.Code(); got != w.code {
			t.Errorf("%s code = %q, want %q", w.activity.Name(), got, w.code)
		}
		if got := w.activity.RequiredClassification(); got != w.classification {
			t.Errorf("%s required classification = %v, want %v", w.activity.Name(), got, w.classification)
		}
		back, ok := FinancialActivityFromValue(w.value)
		if !ok || back != w.activity {
			t.Errorf("FinancialActivityFromValue(%d) = %v/%v", w.value, back, ok)
		}
	}

	// The declaration order in the source is NOT value order, so an ordinal()
	// port would pick the wrong account. Assert the property that makes that
	// impossible here: the value table is what decides, and it is not sorted.
	if FinancialActivityLiabilityTransfer.StoredValue() < FinancialActivityCashAtMainVault.StoredValue() {
		t.Error("the premise has changed: LIABILITY_TRANSFER(200) is declared BEFORE " +
			"CASH_AT_MAINVAULT(101) in the oracle, which is why ordinal() would be wrong")
	}
}

// TestCreateAndUpdateAllowedListsDiffer pins the genuine asymmetry: 101 and 102
// are creatable and NOT settable on update.
func TestCreateAndUpdateAllowedListsDiffer(t *testing.T) {
	// [VERIFIED: FinancialActivityAccountDataValidator.java:62-66 (seven) vs
	// :89-92 (five), both halves read by this worker]
	for _, v := range []int32{100, 200, 101, 102, 300, 103, 201} {
		if !IsCreatableActivityValue(v) {
			t.Errorf("%d should be creatable", v)
		}
	}
	for _, v := range []int32{101, 102} {
		if IsUpdatableActivityValue(v) {
			t.Errorf("%d is creatable but NOT settable on update", v)
		}
	}
	for _, v := range []int32{100, 200, 300, 103, 201} {
		if !IsUpdatableActivityValue(v) {
			t.Errorf("%d should be settable on update", v)
		}
	}
	if IsCreatableActivityValue(99) || IsCreatableActivityValue(1) {
		t.Error("only the seven values are creatable")
	}
}

// TestUnknownActivityRefusalMatchesTheOracleMessage grades the create
// validator's list against the oracle's own words, which enumerate the values
// in DECLARATION order rather than numeric order.
func TestUnknownActivityRefusalMatchesTheOracleMessage(t *testing.T) {
	err := ValidateFinancialActivityAccountCreate(99, nil)
	if !errors.Is(err, ErrValidation) {
		t.Fatalf("got %v", err)
	}
	var body struct {
		Errors []struct {
			Dev string `json:"developerMessage"`
		} `json:"errors"`
	}
	decodeCapture(t, "A2-fin-104-unknown-activity", &body)
	var le *LedgerError
	errors.As(err, &le)
	if le.Message != body.Errors[0].Dev {
		t.Errorf("port %q\noracle %q", le.Message, body.Errors[0].Dev)
	}
}

// TestActivityClassificationRefusalMatchesTheOracleMessage grades F6.
func TestActivityClassificationRefusalMatchesTheOracleMessage(t *testing.T) {
	chart := loadChart(t)
	// A2-fin-103 posted activity 100 (ASSET_TRANSFER) with GL account 6
	// (Overpayment Liability, LIABILITY).
	account := accountByID(t, chart, 6)
	if account.Classification != ClassificationLiability {
		t.Fatalf("GL 6 should be LIABILITY, got %v", account.Classification)
	}
	err := ValidateFinancialActivityAccountCreate(100, &account)
	if !errors.Is(err, ErrFinancialActivityAccountInvalid) {
		t.Fatalf("got %v", err)
	}
	var body struct {
		Errors []struct {
			Dev  string `json:"developerMessage"`
			Code string `json:"userMessageGlobalisationCode"`
		} `json:"errors"`
	}
	decodeCapture(t, "A2-fin-103-wrong-account-type", &body)
	var le *LedgerError
	errors.As(err, &le)
	if le.Message != body.Errors[0].Dev {
		t.Errorf("port %q\noracle %q", le.Message, body.Errors[0].Dev)
	}
	if le.Code != body.Errors[0].Code {
		t.Errorf("port code %q, oracle %q", le.Code, body.Errors[0].Code)
	}
}

// TestActivityAcceptsAHeaderAccount grades the ABSENCE of a usage check. The
// oracle accepted GL account 15 (30000 Equity, HEADER) for activity 300.
func TestActivityAcceptsAHeaderAccount(t *testing.T) {
	if st := captureStatus(t, "A2-fin-106-header-account"); st != 200 {
		t.Fatalf("A2-fin-106-header-account status %d, want 200", st)
	}
	chart := loadChart(t)
	equity := accountByID(t, chart, 15)
	if !equity.IsHeader() || equity.Classification != ClassificationEquity {
		t.Fatalf("GL 15 should be a HEADER EQUITY account, got %v/%v", equity.Usage, equity.Classification)
	}
	if err := ValidateFinancialActivityAccountCreate(300, &equity); err != nil {
		t.Errorf("a HEADER account must be accepted; the oracle validates classification only: %v", err)
	}
	// And the tenant really holds that mapping.
	var found bool
	for _, row := range loadFinancialActivities(t) {
		if row.Activity == FinancialActivityOpeningBalancesTransferContra && row.GLAccountID == 15 {
			found = true
		}
	}
	if !found {
		t.Error("expected activity 300 -> GL 15 in the captured tenant")
	}
}

// TestActivityCreateResponsesMatch grades the accepted creates.
//
// A2-fin-101 IS DELIBERATELY EXCLUDED, and the exclusion is the finding. It
// posted activity 100 (ASSET_TRANSFER, which demands an ASSET) with GL account
// 2, and the oracle accepted it — because GL 2 was an ASSET at that moment.
// A2-111 retyped GL 2 to INCOME afterwards, so replaying that request against
// the chart in A2-150 is refused. Grading it here would look like a port defect
// and is in fact a TEMPORAL mismatch between two committed captures of the same
// tenant: the request is from before the retype and the chart is from after it.
// The phenomenon itself is asserted in
// TestTheTenantsAssetTransferAccountIsNoLongerAnAsset. P-32, again, and this
// time it bit inside a test rather than inside a document.
func TestActivityCreateResponsesMatch(t *testing.T) {
	chart := loadChart(t)
	for _, tc := range []struct {
		capture       string
		activityValue int32
		requestFile   string
	}{
		{"A2-fin-100-liability-transfer", 200, "fin-100-liability-transfer.json"},
	} {
		if st := captureStatus(t, tc.capture); st != 200 {
			t.Errorf("%s status %d, want 200", tc.capture, st)
			continue
		}
		var req struct {
			FinancialActivityID json.Number `json:"financialActivityId"`
			GLAccountID         json.Number `json:"glAccountId"`
		}
		decodeRequest(t, tc.requestFile, &req)
		if mustInt32(t, req.FinancialActivityID.String()) != tc.activityValue {
			t.Fatalf("%s: request activity %s, expected %d", tc.capture, req.FinancialActivityID, tc.activityValue)
		}
		account := accountByID(t, chart, mustInt64(t, req.GLAccountID.String()))
		if err := ValidateFinancialActivityAccountCreate(tc.activityValue, &account); err != nil {
			t.Errorf("%s: the oracle ACCEPTED this and the port refuses it: %v", tc.capture, err)
		}
	}
}

// TestFinancialActivityLookupIsSingleResult pins the uniqueness semantics: the
// query returns one entity, so a duplicate row is a query-time refusal.
func TestFinancialActivityLookupIsSingleResult(t *testing.T) {
	store := &InMemoryFinancialActivityStore{Rows: []FinancialActivityAccountRow{
		{ID: 1, Activity: FinancialActivityAssetTransfer, GLAccountID: 2},
		{ID: 2, Activity: FinancialActivityAssetTransfer, GLAccountID: 16},
	}}
	if _, err := store.FindByActivity(FinancialActivityAssetTransfer); !errors.Is(err, ErrNonUniqueMappingResult) {
		t.Errorf("a duplicate activity row must refuse, not pick one: %v", err)
	}
	row, err := store.FindByActivity(FinancialActivityCashAtTeller)
	if err != nil || row != nil {
		t.Errorf("a miss should be (nil, nil), got %v/%v", row, err)
	}
}

// TestTheTenantsAssetTransferAccountIsNoLongerAnAsset is G-10 reaching the
// financial-activity table as well as the product mappings.
//
// The tenant maps ASSET_TRANSFER (100) to GL account 2, and the create
// validator demands an ASSET. GL account 2 was retyped to INCOME afterwards, so
// the mapping the oracle HOLDS is one the oracle would now REFUSE TO CREATE —
// the same shape as A2-214, on a different table. Recorded so nobody takes a
// vector from the tenant's financial activity accounts without saying so.
func TestTheTenantsAssetTransferAccountIsNoLongerAnAsset(t *testing.T) {
	chart := loadChart(t)
	var mapped int64
	for _, row := range loadFinancialActivities(t) {
		if row.Activity == FinancialActivityAssetTransfer {
			mapped = row.GLAccountID
		}
	}
	if mapped == 0 {
		t.Fatal("expected the tenant to map ASSET_TRANSFER")
	}
	account := accountByID(t, chart, mapped)
	if account.Classification == ClassificationAsset {
		t.Skip("the tenant's ASSET_TRANSFER account is still an ASSET; this test records " +
			"the retyped state and there is nothing to record")
	}
	if err := ValidateFinancialActivityAccountCreate(100, &account); err == nil {
		t.Errorf("GL %d is %v and ASSET_TRANSFER demands ASSET, so re-creating this "+
			"mapping must be refused — the tenant holds a state it cannot be asked to create",
			mapped, account.Classification)
	}
}
