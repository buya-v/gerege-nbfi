package ledger

import (
	"bytes"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// productRead is GET /loanproducts/{id}, cut down to the accounting mapping.
type productRead struct {
	ID                 json.Number                  `json:"id"`
	AccountingRule     struct{ ID json.Number }     `json:"accountingRule"`
	AccountingMappings map[string]AccountReadObject `json:"accountingMappings"`
	PaymentChannel     []struct {
		PaymentType       struct{ ID json.Number } `json:"paymentType"`
		FundSourceAccount AccountReadObject        `json:"fundSourceAccount"`
	} `json:"paymentChannelToFundSourceMappings"`
}

func loadProductRead(t *testing.T, id string) productRead {
	t.Helper()
	if st := captureStatus(t, id); st != 200 {
		t.Fatalf("%s: status %d, want 200", id, st)
	}
	var p productRead
	decodeCapture(t, id, &p)
	return p
}

// decodeRequest reads a committed REQUEST body from the capture rig's req/
// directory. Requests are the INPUT the oracle was given; reading them lets a
// test grade a write -> read round trip through the port rather than comparing
// the oracle's answer with itself.
// loadCreateRequest reads a request body and returns ONLY its numeric-valued
// keys, as their literal text. The bodies mix strings, numbers and booleans, so
// a map[string]json.Number cannot decode them; and the account slots are always
// numbers, so restricting to numbers is exactly the projection this needs.
func loadCreateRequest(t *testing.T, name string) map[string]string {
	t.Helper()
	var raw map[string]json.RawMessage
	decodeRequest(t, name, &raw)
	out := map[string]string{}
	for k, v := range raw {
		s := strings.TrimSpace(string(v))
		if s == "" || s[0] == '"' || s[0] == '{' || s[0] == '[' || s == "true" || s == "false" || s == "null" {
			continue
		}
		out[k] = s
	}
	return out
}

func decodeRequest(t *testing.T, name string, v any) {
	t.Helper()
	p := filepath.Join(repoRoot(t), ".softhouse", "capture", "tierA-a2", "req", name)
	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatalf("reading request %s: %v", name, err)
	}
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.UseNumber()
	if err := dec.Decode(v); err != nil {
		t.Fatalf("decoding request %s: %v", name, err)
	}
}

// slotsForRule enumerates the loan placeholders of one accounting rule.
func slotsForRule(rule AccountingRule) []Slot {
	var out []Slot
	if rule.IsAccrual() {
		for s := range accrualLoanNames {
			out = append(out, s)
		}
	} else {
		for s := range cashLoanNames {
			out = append(out, s)
		}
	}
	return out
}

// TestResolutionReproducesTheCapturedProductReads is the headline grading.
//
// For products 22 (cash) and 28 (accrual), it resolves EVERY placeholder of the
// product's accounting rule against the captured acc_product_mapping rows and
// compares the result, slot by slot, with what GET /loanproducts/{id} returned.
// Both directions are checked: every key the oracle emitted must resolve to
// that account, and every slot the port resolves must be a key the oracle
// emitted. A one-directional check would pass a port that silently resolved
// extra slots.
func TestResolutionReproducesTheCapturedProductReads(t *testing.T) {
	resolver, accounts, _ := tenant(t)

	cases := []struct {
		capture   string
		productID int64
		rule      AccountingRule
		wantSlots int
	}{
		{"A2-212-read-product22-channel-override", 22, AccountingRuleCashBased, 10},
		{"A2-213-read-product28-accrual", 28, AccountingRuleAccrualPeriodic, 13},
	}

	for _, c := range cases {
		p := loadProductRead(t, c.capture)
		if len(p.AccountingMappings) != c.wantSlots {
			t.Errorf("%s: oracle emitted %d mapped slots, expected %d",
				c.capture, len(p.AccountingMappings), c.wantSlots)
		}
		if got := p.AccountingRule.ID.String(); got != itoa(c.rule.StoredValue()) {
			t.Fatalf("%s: accountingRule %s, expected %d", c.capture, got, c.rule.StoredValue())
		}

		resolvedKeys := map[string]bool{}
		for _, slot := range slotsForRule(c.rule) {
			// paymentTypeID nil: the DEFAULT resolution, which is what
			// accountingMappings shows.
			acct, err := resolver.ResolveLoanProductAccount(c.productID, slot, nil)
			shape, haveShape := LoanSlotAPIShape(slot.Code(), c.rule)

			if err != nil {
				if !errors.Is(err, ErrProductToGLAccountMappingNotFound) {
					t.Errorf("%s slot %s: unexpected error %v", c.capture, slot.Name(), err)
					continue
				}
				// A miss must correspond to a key the oracle did NOT emit.
				if haveShape && shape.ReadKey != "" {
					if _, present := p.AccountingMappings[shape.ReadKey]; present {
						t.Errorf("%s: port missed slot %s but the oracle emitted %q",
							c.capture, slot.Name(), shape.ReadKey)
					}
				}
				continue
			}

			if !haveShape || shape.ReadKey == "" {
				t.Errorf("%s: port resolved slot %s but the port has no read key for it",
					c.capture, slot.Name())
				continue
			}
			want, present := p.AccountingMappings[shape.ReadKey]
			if !present {
				t.Errorf("%s: port resolved slot %s to GL %d, but the oracle emitted no %q key",
					c.capture, slot.Name(), acct.ID, shape.ReadKey)
				continue
			}
			resolvedKeys[shape.ReadKey] = true
			if got := acct.ReadObject(); got != want {
				t.Errorf("%s slot %s (%q): port %+v, oracle %+v",
					c.capture, slot.Name(), shape.ReadKey, got, want)
			}
			// And the account really is the one in the chart.
			chartAcct := accountByID(t, accounts.Accounts, want.ID)
			if chartAcct.GLCode != want.GLCode {
				t.Errorf("%s slot %s: chart glCode %q, oracle %q", c.capture, slot.Name(), chartAcct.GLCode, want.GLCode)
			}
		}

		for key := range p.AccountingMappings {
			if !resolvedKeys[key] {
				t.Errorf("%s: the oracle emitted %q and the port resolved nothing for it", c.capture, key)
			}
		}
	}
}

// TestPaymentChannelOverride grades STEP 2, and it grades it in BOTH
// directions on the same product: the override fires for payment type 1 and
// does NOT fire for payment type 2, which product 22 exhibits because it has
// exactly one payment-type row.
//
// This is not only a read-model check. A2-150-db-final-state.txt's journal
// entry dump shows the same two answers at POSTING time: loan transaction 1
// (A2-084, paymentTypeId 1) credited GL 16, and loan transaction 2 (A2-085,
// paymentTypeId 2) credited GL 2.
func TestPaymentChannelOverride(t *testing.T) {
	resolver, _, _ := tenant(t)

	p := loadProductRead(t, "A2-212-read-product22-channel-override")
	if len(p.PaymentChannel) != 1 {
		t.Fatalf("expected exactly one payment-channel override on product 22, got %d", len(p.PaymentChannel))
	}
	channel := p.PaymentChannel[0]
	paymentType := mustInt64(t, channel.PaymentType.ID.String())

	// The override fires.
	acct, err := resolver.ResolveLoanProductAccount(22, CashLoanFundSource, &paymentType)
	if err != nil {
		t.Fatalf("resolving FUND_SOURCE with payment type %d: %v", paymentType, err)
	}
	if got := acct.ReadObject(); got != channel.FundSourceAccount {
		t.Errorf("payment type %d: port %+v, oracle %+v", paymentType, got, channel.FundSourceAccount)
	}

	// A payment type with no row leaves the core row in place. Observed at
	// posting time as journal entry id 4 (loan transaction 2), account 2.
	other := int64(2)
	acct, err = resolver.ResolveLoanProductAccount(22, CashLoanFundSource, &other)
	if err != nil {
		t.Fatalf("resolving FUND_SOURCE with payment type %d: %v", other, err)
	}
	want := p.AccountingMappings["fundSourceAccount"]
	if got := acct.ReadObject(); got != want {
		t.Errorf("payment type %d should fall back to the core row: port %+v, oracle %+v", other, got, want)
	}

	// The override is consulted ONLY for the family reference slot. Give
	// LOAN_PORTFOLIO the overriding payment type and nothing must move.
	acct, err = resolver.ResolveLoanProductAccount(22, CashLoanLoanPortfolio, &paymentType)
	if err != nil {
		t.Fatalf("resolving LOAN_PORTFOLIO: %v", err)
	}
	if got := acct.ReadObject(); got != p.AccountingMappings["loanPortfolioAccount"] {
		t.Errorf("LOAN_PORTFOLIO must ignore the payment type; port %+v", got)
	}
}

// TestResolutionAtPostingTimeMatchesTheJournalEntries grades resolution against
// what the oracle ACTUALLY POSTED, not against a read model. The journal-entry
// section of A2-150-db-final-state.txt is the record.
func TestResolutionAtPostingTimeMatchesTheJournalEntries(t *testing.T) {
	resolver, _, _ := tenant(t)

	entries := parsePsqlTables(t, "A2-150-db-final-state.txt")["journal entries written by the A2 probes"]
	if len(entries.rows) != 6 {
		t.Fatalf("expected 6 journal entry rows, parsed %d", len(entries.rows))
	}

	// loan_transaction_id -> (product, payment type) from the capture requests
	// and run scripts:
	//   txn 1 = loan 1 (req/loan-080-on-product22-a.json)  disbursed A2-084, paymentTypeId 1
	//   txn 2 = loan 2 (req/loan-081-on-product22-b.json)  disbursed A2-085, paymentTypeId 2
	//   txn 4 = loan 4 (product 24, header account)        disbursed A2-091b, paymentTypeId 2
	pt1, pt2 := int64(1), int64(2)
	cases := []struct {
		txn         string
		productID   int64
		paymentType *int64
		debitSlot   Slot
		creditSlot  Slot
	}{
		{"1", 22, &pt1, CashLoanLoanPortfolio, CashLoanFundSource},
		{"2", 22, &pt2, CashLoanLoanPortfolio, CashLoanFundSource},
		{"4", 24, &pt2, CashLoanLoanPortfolio, CashLoanFundSource},
	}

	for _, c := range cases {
		var debitAccount, creditAccount int64
		var found int
		for i := range entries.rows {
			if entries.get(i, "loan_transaction_id") != c.txn {
				continue
			}
			found++
			id := mustInt64(t, entries.get(i, "account_id"))
			switch mustInt32(t, entries.get(i, "type_enum")) {
			case int32(EntryDebit):
				debitAccount = id
			case int32(EntryCredit):
				creditAccount = id
			}
		}
		if found != 2 {
			t.Fatalf("loan transaction %s: expected 2 journal entry rows, found %d", c.txn, found)
		}

		got, err := resolver.ResolveLoanProductAccount(c.productID, c.debitSlot, c.paymentType)
		if err != nil {
			t.Fatalf("txn %s debit slot: %v", c.txn, err)
		}
		if got.ID != debitAccount {
			t.Errorf("txn %s: port resolved %s to GL %d, the oracle POSTED the debit to GL %d",
				c.txn, c.debitSlot.Name(), got.ID, debitAccount)
		}
		got, err = resolver.ResolveLoanProductAccount(c.productID, c.creditSlot, c.paymentType)
		if err != nil {
			t.Fatalf("txn %s credit slot: %v", c.txn, err)
		}
		if got.ID != creditAccount {
			t.Errorf("txn %s: port resolved %s to GL %d, the oracle POSTED the credit to GL %d",
				c.txn, c.creditSlot.Name(), got.ID, creditAccount)
		}
	}
}

// TestResolutionIgnoresUsageAndDisabled: product 24's LOAN_PORTFOLIO maps to GL
// account 1, which is a HEADER account, and product 22's TRANSFERS_SUSPENSE
// maps to GL 17 "Disabled Asset". Neither is refused, and GL 1 was actually
// posted to.
func TestResolutionIgnoresUsageAndDisabled(t *testing.T) {
	resolver, accounts, _ := tenant(t)

	acct, err := resolver.ResolveLoanProductAccount(24, CashLoanLoanPortfolio, nil)
	if err != nil {
		t.Fatalf("product 24 LOAN_PORTFOLIO: %v", err)
	}
	if !acct.IsHeader() {
		t.Fatalf("expected product 24's LOAN_PORTFOLIO to be a HEADER account, got %v", acct.Usage)
	}
	if acct.ID != 1 {
		t.Errorf("expected GL 1, got %d", acct.ID)
	}

	// And the oracle really did post to it [A2-150 journal entry id 6].
	entries := parsePsqlTables(t, "A2-150-db-final-state.txt")["journal entries written by the A2 probes"]
	var postedToHeader bool
	for i := range entries.rows {
		if entries.get(i, "account_id") == "1" && entries.get(i, "account_usage") == "2" {
			postedToHeader = true
		}
	}
	if !postedToHeader {
		t.Error("expected the capture to show a posting to a HEADER account")
	}

	// Nothing in resolution reads `disabled` either. GL 17 is not disabled in
	// the final dump (A2-112 refused the attempt), so assert the code path
	// rather than the data: a disabled account still resolves.
	disabled := accountByID(t, accounts.Accounts, 17)
	disabled.Disabled = true
	accounts.Accounts = append([]GLAccount{disabled}, accounts.Accounts...)
	acct, err = resolver.ResolveLoanProductAccount(22, CashLoanTransfersSuspense, nil)
	if err != nil {
		t.Fatalf("product 22 TRANSFERS_SUSPENSE with a disabled account: %v", err)
	}
	if !acct.Disabled {
		t.Fatal("the resolver returned a different account than the disabled one it was pointed at")
	}
}

// TestMissingMappingRefusalsMatchTheOracleMessages grades the not-found path
// message for message.
func TestMissingMappingRefusalsMatchTheOracleMessages(t *testing.T) {
	resolver, _, mappings := tenant(t)

	// Product 46 is not in A2-072 (it was created later, by A2-7), so build its
	// rows from the REQUEST that created it. That makes this a genuine
	// write -> resolve -> read round trip rather than a comparison of the
	// oracle's answer with itself.
	req := loadCreateRequest(t, "a2-7-prod-210-cash-nine-mandatory.json")
	rows := mappings.Rows
	var mapped int
	for slot := range cashLoanNames {
		shape, ok := cashLoanSlotShape[slot]
		if !ok || shape.WriteParam == "" {
			continue
		}
		raw, present := req[shape.WriteParam]
		if !present {
			continue
		}
		accountID := mustInt64(t, raw)
		productID := int64(46)
		productType := ProductLoan.StoredValue()
		code := slot.Code()
		rows = append(rows, MappingRow{
			ID: 1000 + int64(code), GLAccountID: &accountID, ProductID: &productID,
			ProductType: &productType, FinancialAccountType: &code,
		})
		mapped++
	}
	if mapped != 9 {
		t.Fatalf("expected the A2-210 request to carry exactly the nine notNull() slots, mapped %d", mapped)
	}
	mappings.Rows = rows

	// The read-back must now agree, slot for slot.
	p := loadProductRead(t, "A2-211-read-product-nine-mandatory")
	if len(p.AccountingMappings) != 9 {
		t.Fatalf("A2-211 emitted %d slots, want 9", len(p.AccountingMappings))
	}
	for slot := range cashLoanNames {
		shape, ok := cashLoanSlotShape[slot]
		if !ok || shape.ReadKey == "" {
			continue
		}
		want, present := p.AccountingMappings[shape.ReadKey]
		if !present {
			continue
		}
		acct, err := resolver.ResolveLoanProductAccount(46, slot, nil)
		if err != nil {
			t.Errorf("product 46 slot %s: %v", slot.Name(), err)
			continue
		}
		if got := acct.ReadObject(); got != want {
			t.Errorf("product 46 slot %s: port %+v, oracle %+v", slot.Name(), got, want)
		}
	}

	// Now the two runtime misses, message for message.
	misses := []struct {
		capture   string
		productID int64
		slot      Slot
	}{
		{"A2-224-chargeoff-unmapped", 46, CashLoanChargeOffExpense},
		{"A2-225-goodwillcredit-unmapped", 46, CashLoanGoodwillCredit},
		{"A2-092-chargeoff-loan1-unmapped", 22, CashLoanChargeOffExpense},
	}
	for _, m := range misses {
		_, err := resolver.ResolveLoanProductAccount(m.productID, m.slot, nil)
		if err == nil {
			t.Errorf("%s: expected a not-found refusal", m.capture)
			continue
		}
		if !errors.Is(err, ErrProductToGLAccountMappingNotFound) {
			t.Errorf("%s: got %v", m.capture, err)
			continue
		}
		var body struct {
			Errors []struct {
				Dev  string `json:"developerMessage"`
				Code string `json:"userMessageGlobalisationCode"`
			} `json:"errors"`
		}
		decodeCapture(t, m.capture, &body)
		var le *LedgerError
		if !errors.As(err, &le) {
			t.Fatalf("%s: error is not a LedgerError", m.capture)
		}
		if le.Message != body.Errors[0].Dev {
			t.Errorf("%s: port message %q, oracle %q", m.capture, le.Message, body.Errors[0].Dev)
		}
		if le.Code != body.Errors[0].Code {
			t.Errorf("%s: port code %q, oracle %q", m.capture, le.Code, body.Errors[0].Code)
		}
	}
}

// renderedSlotName cuts the placeholder name back out of the oracle's message,
// so a test can compare what was RENDERED against what APPLIES without
// reaching into the resolver.
func renderedSlotName(t *testing.T, message string) string {
	t.Helper()
	const marker = " does not exist for an account of type "
	i := strings.Index(message, marker)
	if i < 0 {
		t.Fatalf("message %q is not the not-found message", message)
	}
	return message[i+len(marker):]
}

// TestApplicableSlotNameCarriesTheCallersFamily is the F-A regression test
// (A2-9's finding, fixed by A2-12).
//
// LedgerError.Message reproduces the oracle's own rendering, which for a LOAN
// always goes through AccrualAccountsForLoan and for a WORKING-CAPITAL LOAN
// always through CashAccountsForLoan, regardless of the product's accounting
// rule [VERIFIED: AccountingProcessorHelper.java:1208-1211 and :1024-1027].
// ApplicableSlotName exists to carry the OTHER name — the placeholder the
// caller actually holds. The two are the same thing at 19 of the 22 shared
// codes and DIFFER at 22, 24 and 25, which is trap 2 surfacing inside the
// oracle's own error path.
//
// Before the F-A fix ApplicableSlotName was re-derived from the bare integer
// code, so it equalled the rendered name unconditionally and the field carried
// no information at all. This test fails on that code.
func TestApplicableSlotNameCarriesTheCallersFamily(t *testing.T) {
	resolver, _, _ := tenant(t)

	// Product 9999 is in no acc_product_mapping row in any capture, so every
	// resolution below is a STEP 3 miss.
	const missingProduct = int64(9999)

	slots := make([]Slot, 0, 48)
	for s := range cashLoanNames {
		slots = append(slots, s)
	}
	for s := range accrualLoanNames {
		slots = append(slots, s)
	}
	if len(slots) != 48 {
		t.Fatalf("expected 48 (code, family) pairs across the two loan enums, got %d", len(slots))
	}

	entries := []struct {
		name    string
		resolve func(int64, Slot, *int64) (*GLAccount, error)
	}{
		{"loan", resolver.ResolveLoanProductAccount},
		{"workingcapitalloan", resolver.ResolveWorkingCapitalLoanProductAccount},
	}

	// LEG 1 — the field must equal the caller's own placeholder name, always.
	// This is the property; the codes below are the instances that bite.
	differed := 0
	for _, entry := range entries {
		for _, slot := range slots {
			_, err := entry.resolve(missingProduct, slot, nil)
			var le *LedgerError
			if !errors.As(err, &le) {
				t.Fatalf("%s %s: expected a LedgerError, got %v", entry.name, slot.Name(), err)
			}
			if le.ApplicableSlotName != slot.String() {
				t.Errorf("%s code %d: caller passed %q, ApplicableSlotName %q",
					entry.name, slot.Code(), slot.String(), le.ApplicableSlotName)
			}
			if renderedSlotName(t, le.Message) != le.ApplicableSlotName {
				differed++
			}
		}
	}
	// 3 per entry point: codes 22, 24 and 25, in the family the oracle does
	// NOT render through.
	if differed != 6 {
		t.Errorf("expected the rendered and applicable names to differ on exactly 6 of the 96 "+
			"(entry point, code, family) rows, got %d", differed)
	}

	// LEG 2 — the three colliding codes, named. On a CASH product the loan
	// path renders the ACCRUAL name, so the field must NOT agree with the
	// message. A field that agreed here would be the pre-fix defect.
	collisions := []struct {
		slot           Slot
		wantApplicable string
		wantRendered   string
	}{
		{CashLoanClassificationIncome, "CLASSIFICATION INCOME", "INCOME FROM CAPITALIZATION"},
		{CashLoanIncomeFromDiscountFee, "INCOME FROM DISCOUNT FEE", "BUY DOWN EXPENSE"},
		{CashLoanFeesReceivable, "FEES RECEIVABLE", "INCOME FROM BUY DOWN"},
	}
	for _, c := range collisions {
		_, err := resolver.ResolveLoanProductAccount(missingProduct, c.slot, nil)
		var le *LedgerError
		if !errors.As(err, &le) {
			t.Fatalf("code %d: expected a LedgerError, got %v", c.slot.Code(), err)
		}
		rendered := renderedSlotName(t, le.Message)
		if rendered != c.wantRendered {
			t.Errorf("code %d: rendered %q, want %q (the WIRE string — it must not move)",
				c.slot.Code(), rendered, c.wantRendered)
		}
		if le.ApplicableSlotName != c.wantApplicable {
			t.Errorf("code %d: ApplicableSlotName %q, want %q",
				c.slot.Code(), le.ApplicableSlotName, c.wantApplicable)
		}
		if le.ApplicableSlotName == rendered {
			t.Errorf("code %d: ApplicableSlotName equals the rendered name %q — the field carries "+
				"no information at exactly the code where trap 2 bites",
				c.slot.Code(), rendered)
		}
	}
}

// TestDuplicateMappingRowsRefuse grades the missing unique constraint. Product
// 27 holds two rows at (27, LOAN, FUND_SOURCE, payment type 1) pointing at GL
// 16 and GL 2, and the oracle refuses the disbursement rather than picking one.
func TestDuplicateMappingRowsRefuse(t *testing.T) {
	resolver, _, mappings := tenant(t)

	var dup int
	for _, r := range mappings.Rows {
		if r.ProductID != nil && *r.ProductID == 27 &&
			r.FinancialAccountType != nil && *r.FinancialAccountType == 1 &&
			r.PaymentTypeID != nil && *r.PaymentTypeID == 1 {
			dup++
		}
	}
	if dup != 2 {
		t.Fatalf("expected product 27 to carry 2 duplicate payment-type rows, found %d", dup)
	}

	paymentType := int64(1)
	_, err := resolver.ResolveLoanProductAccount(27, CashLoanFundSource, &paymentType)
	if err == nil {
		t.Fatal("expected a non-unique-result refusal, got an account — taking the first row " +
			"would be a silent, plausible, WRONG answer at exactly the point the oracle refuses")
	}
	if !errors.Is(err, ErrNonUniqueMappingResult) {
		t.Fatalf("got %v", err)
	}

	var body struct {
		Msg    string `json:"defaultUserMessage"`
		Errors []struct {
			Code string `json:"userMessageGlobalisationCode"`
		} `json:"errors"`
	}
	decodeCapture(t, "A2-086-disburse-loan3-dupchannel", &body)
	var le *LedgerError
	errors.As(err, &le)
	if le.Message != body.Msg {
		t.Errorf("port message %q, oracle %q", le.Message, body.Msg)
	}
	if le.Code != body.Errors[0].Code {
		t.Errorf("port code %q, oracle %q", le.Code, body.Errors[0].Code)
	}

	// The OTHER payment types on product 27 are unaffected: the refusal is per
	// query, not per product.
	other := int64(2)
	if _, err := resolver.ResolveLoanProductAccount(27, CashLoanFundSource, &other); err != nil {
		t.Errorf("product 27 with payment type 2 should still resolve: %v", err)
	}
}

// TestStepZeroWinsOutright grades the financial-activity branch: the account
// comes from acc_gl_financial_activity_account keyed on the activity ALONE.
func TestStepZeroWinsOutright(t *testing.T) {
	resolver, _, _ := tenant(t)

	rows := loadFinancialActivities(t)
	if len(rows) != 3 {
		t.Fatalf("expected 3 financial activity rows in the captured tenant, got %d", len(rows))
	}
	for _, row := range rows {
		acct, err := resolver.ResolveOrganisationAccount(row.Activity)
		if err != nil {
			t.Fatalf("resolving %s: %v", row.Activity.Name(), err)
		}
		if acct.ID != row.GLAccountID {
			t.Errorf("%s resolved to GL %d, the tenant maps it to GL %d", row.Activity.Name(), acct.ID, row.GLAccountID)
		}
	}

	// A miss is the typed financial-activity refusal, not a product-mapping
	// refusal. CASH_AT_TELLER is unmapped in this tenant.
	if _, err := resolver.ResolveOrganisationAccount(FinancialActivityCashAtTeller); !errors.Is(err, ErrFinancialActivityAccountNotFound) {
		t.Errorf("unmapped activity should raise the financial-activity refusal, got %v", err)
	}

	// The untyped classification a processor port would use.
	activity, isOrg, _, ok := ClassifyLoanPlaceholder(100, AccountingRuleCashBased)
	if !ok || !isOrg || activity != FinancialActivityAssetTransfer {
		t.Errorf("ClassifyLoanPlaceholder(100) = %v/%v/%v", activity, isOrg, ok)
	}
	_, isOrg, slot, ok := ClassifyLoanPlaceholder(1, AccountingRuleCashBased)
	if !ok || isOrg || slot.Name() != "FUND_SOURCE" {
		t.Errorf("ClassifyLoanPlaceholder(1) = %v/%v/%v", isOrg, slot, ok)
	}
	// Trap 2 at the classifier: code 24 names different placeholders under the
	// two rules.
	_, _, cashSlot, _ := ClassifyLoanPlaceholder(24, AccountingRuleCashBased)
	_, _, accrualSlot, _ := ClassifyLoanPlaceholder(24, AccountingRuleAccrualPeriodic)
	if cashSlot.Name() == accrualSlot.Name() {
		t.Errorf("code 24 should classify differently by rule; both gave %q", cashSlot.Name())
	}
}

// TestStepZeroIsAbsentFromTheWorkingCapitalLoanPath pins the divergence.
func TestStepZeroIsAbsentFromTheWorkingCapitalLoanPath(t *testing.T) {
	resolver, _, _ := tenant(t)
	// Nothing in the tenant is a working-capital-loan product, so every lookup
	// misses; the point is WHICH refusal comes back. On the loan path a
	// financial-activity code would never reach the mapping lookup at all —
	// here there is no such branch, so the code is treated as an ordinary
	// placeholder.
	_, err := resolver.ResolveWorkingCapitalLoanProductAccount(22, CashLoanFundSource, nil)
	if !errors.Is(err, ErrProductToGLAccountMappingNotFound) {
		t.Errorf("expected the typed not-found refusal on the working-capital path, got %v", err)
	}
}

// TestSavingsAndSharesMissesAreNotTypedRefusals pins the second divergence: the
// oracle dereferences nil there and returns HTTP 500, not a not-found.
func TestSavingsAndSharesMissesAreNotTypedRefusals(t *testing.T) {
	resolver, _, _ := tenant(t)
	for _, tc := range []struct {
		name string
		fn   func() (*GLAccount, error)
	}{
		{"savings", func() (*GLAccount, error) {
			return resolver.ResolveSavingsProductAccount(22, CashSavingsSavingsControl, nil)
		}},
		{"shares", func() (*GLAccount, error) {
			return resolver.ResolveShareProductAccount(22, CashSharesSharesEquity, nil)
		}},
	} {
		_, err := tc.fn()
		if errors.Is(err, ErrProductToGLAccountMappingNotFound) {
			t.Errorf("%s: a miss must NOT be the typed not-found refusal — the oracle "+
				"dereferences null there (AccountingProcessorHelper.java:1293, :1317)", tc.name)
		}
		if !errors.Is(err, ErrMappingNilDereference) {
			t.Errorf("%s: got %v", tc.name, err)
		}
	}
}

// TestSlotFamilyIsEnforcedAtTheEntryPoints proves the typed API refuses a
// cross-family call rather than silently keying on the wrong product_type.
func TestSlotFamilyIsEnforcedAtTheEntryPoints(t *testing.T) {
	resolver, _, _ := tenant(t)
	if _, err := resolver.ResolveLoanProductAccount(22, CashSavingsSavingsReference, nil); err == nil {
		t.Error("a savings slot must not be accepted by the loan resolver")
	}
	if _, err := resolver.ResolveShareProductAccount(22, CashLoanFundSource, nil); err == nil {
		t.Error("a loan slot must not be accepted by the shares resolver")
	}
}

// TestNullPaymentTypePolicyIsExplicit records that the contested reading is
// exposed and that, on the captured data, both readings agree — which is why
// no capture discriminates them.
func TestNullPaymentTypePolicyIsExplicit(t *testing.T) {
	for _, policy := range []NullPaymentTypePolicy{NullPaymentTypeMatchesIsNull, NullPaymentTypeMatchesNothing} {
		resolver, _, mappings := tenant(t)
		mappings.NullPaymentTypePolicy = policy
		acct, err := resolver.ResolveLoanProductAccount(22, CashLoanFundSource, nil)
		if err != nil {
			t.Fatalf("policy %d: %v", policy, err)
		}
		if acct.ID != 2 {
			t.Errorf("policy %d resolved product 22 FUND_SOURCE to GL %d, want 2", policy, acct.ID)
		}
	}

	// And the shape that WOULD separate them: a row with payment_type NULL but
	// charge_id set, at the fund-source placeholder. The CORE query cannot see
	// it (its predicate demands charge IS NULL) but the IS NULL reading of the
	// payment-type query CAN, because that query constrains only four columns
	// and leaves the other five discriminators unconstrained.
	//
	// The measured separation is sharper than "a different account": under the
	// IS NULL reading the payment-type query now matches TWO rows — the core
	// one and the charge one — so it becomes a NON-UNIQUE RESULT and the
	// posting is refused, while under the `= NULL` reading it matches nothing
	// and the core row stands. A refusal against a successful posting is not a
	// subtle difference, and NO CAPTURE EXERCISES IT.
	for _, tc := range []struct {
		policy    NullPaymentTypePolicy
		wantRefus bool
		wantID    int64
	}{
		{NullPaymentTypeMatchesIsNull, true, 0},
		{NullPaymentTypeMatchesNothing, false, 2},
	} {
		resolver, _, mappings := tenant(t)
		mappings.NullPaymentTypePolicy = tc.policy
		productID, productType, code := int64(22), ProductLoan.StoredValue(), CashLoanFundSource.Code()
		chargeID, accountID := int64(99), int64(17)
		mappings.Rows = append(mappings.Rows, MappingRow{
			ID: 9001, GLAccountID: &accountID, ProductID: &productID,
			ProductType: &productType, FinancialAccountType: &code, ChargeID: &chargeID,
		})
		acct, err := resolver.ResolveLoanProductAccount(22, CashLoanFundSource, nil)
		if tc.wantRefus {
			if !errors.Is(err, ErrNonUniqueMappingResult) {
				t.Errorf("policy %d: expected a non-unique-result refusal, got acct=%v err=%v",
					tc.policy, acct, err)
			}
			continue
		}
		if err != nil {
			t.Fatalf("policy %d: %v", tc.policy, err)
		}
		if acct.ID != tc.wantID {
			t.Errorf("policy %d resolved to GL %d, want %d", tc.policy, acct.ID, tc.wantID)
		}
	}
}

// TestMandatoryAtCreateIsNotTheRuntimeSet makes A2-7's measured finding
// executable.
func TestMandatoryAtCreateIsNotTheRuntimeSet(t *testing.T) {
	cash := MandatoryLoanSlotsAtCreate(AccountingRuleCashBased)
	want := []int32{1, 2, 3, 4, 5, 6, 10, 11, 12}
	if len(cash) != len(want) {
		t.Fatalf("cash mandatory set = %v, want %v", cash, want)
	}
	for i := range want {
		if cash[i] != want[i] {
			t.Fatalf("cash mandatory set = %v, want %v", cash, want)
		}
	}
	accrual := MandatoryLoanSlotsAtCreate(AccountingRuleAccrualPeriodic)
	if len(accrual) != 12 {
		t.Errorf("accrual mandatory set has %d entries, want 12 (the nine plus the three receivables): %v",
			len(accrual), accrual)
	}

	// Product 46 was created with exactly the nine and NOTHING ELSE, HTTP 200,
	// and then failed at runtime on two placeholders that are ignoreIfNull() at
	// creation. Both facts are captured.
	if st := captureStatus(t, "A2-210-create-cash-nine-mandatory"); st != 200 {
		t.Errorf("A2-210 status %d, want 200", st)
	}
	for _, id := range []string{"A2-224-chargeoff-unmapped", "A2-225-goodwillcredit-unmapped"} {
		if st := captureStatus(t, id); st != 404 {
			t.Errorf("%s status %d, want 404", id, st)
		}
	}
	for _, code := range []int32{CashLoanChargeOffExpense.Code(), CashLoanGoodwillCredit.Code()} {
		shape, _ := LoanSlotAPIShape(code, AccountingRuleCashBased)
		if shape.MandatoryAtCreate {
			t.Errorf("placeholder %d is ignoreIfNull() at create; the port must not mark it mandatory", code)
		}
	}
}

// TestWriteAndReadNamesDifferForEverySlot pins the boundary asymmetry A2-7
// measured, against the request and response bytes of the same call.
func TestWriteAndReadNamesDifferForEverySlot(t *testing.T) {
	req := loadCreateRequest(t, "a2-7-prod-210-cash-nine-mandatory.json")
	p := loadProductRead(t, "A2-211-read-product-nine-mandatory")

	var checked int
	for slot := range cashLoanNames {
		shape, ok := cashLoanSlotShape[slot]
		if !ok || shape.WriteParam == "" {
			continue
		}
		if _, present := req[shape.WriteParam]; !present {
			continue
		}
		checked++
		if shape.WriteParam == shape.ReadKey {
			t.Errorf("slot %s: write and read names are equal (%q); the oracle's are never equal",
				slot.Name(), shape.WriteParam)
		}
		if _, present := p.AccountingMappings[shape.ReadKey]; !present {
			t.Errorf("slot %s: read key %q absent from the oracle's response", slot.Name(), shape.ReadKey)
		}
		if _, present := p.AccountingMappings[shape.WriteParam]; present {
			t.Errorf("slot %s: the oracle's response carries the WRITE name %q", slot.Name(), shape.WriteParam)
		}
	}
	if checked != 9 {
		t.Fatalf("checked %d slots, want 9", checked)
	}

	// AN UNSET MAPPING FIELD IS ABSENT. Scalar and collection alike, and
	// NOTHING IS EVER null.
	//
	// This test asserts the CORRECTED rule. The A2-7 handoff (:210-212) prints
	// paymentChannelToFundSourceMappings, feeToIncomeAccountMappings and
	// penaltyToIncomeAccountMappings with the value null inside a JSON block
	// attributed to this very capture, and those three lines are not in the
	// capture. Asserted here against the BYTES so the fabrication cannot be
	// re-inherited by a later reader of the handoff.
	raw := captureBytes(t, "A2-211-read-product-nine-mandatory.json")
	if bytes.Contains(raw, []byte("null")) {
		t.Error("A2-211 contains the literal string \"null\"; the oracle omits unset keys entirely")
	}
	for _, absent := range []string{
		"goodwillCreditAccount", "chargeOffExpenseAccount",
		"paymentChannelToFundSourceMappings", "feeToIncomeAccountMappings", "penaltyToIncomeAccountMappings",
	} {
		if bytes.Contains(raw, []byte("\""+absent+"\"")) {
			t.Errorf("%q should be ABSENT from A2-211's read, not present in any form", absent)
		}
	}
	// The positive control, without which the assertion above proves only that
	// the port read an empty file: A2-212 HAS one payment-channel override, so
	// it DOES carry the key — as an array — and still has no "null" anywhere.
	raw212 := captureBytes(t, "A2-212-read-product22-channel-override.json")
	if !bytes.Contains(raw212, []byte("\"paymentChannelToFundSourceMappings\"")) {
		t.Error("A2-212 should carry paymentChannelToFundSourceMappings — it has an override")
	}
	if bytes.Contains(raw212, []byte("null")) {
		t.Error("A2-212 contains the literal string \"null\"")
	}
	// And the same holds on the accrual product, which has no overrides.
	raw213 := captureBytes(t, "A2-213-read-product28-accrual.json")
	if bytes.Contains(raw213, []byte("paymentChannelToFundSourceMappings")) {
		t.Error("A2-213 has no overrides, so the key must be absent")
	}
	if bytes.Contains(raw213, []byte("null")) {
		t.Error("A2-213 contains the literal string \"null\"")
	}
}

// TestSlotTypeValidationMatchesTheRefusalCaptures grades the write-path type
// check, including the exact message and the ASSET-OR-LIABILITY set.
func TestSlotTypeValidationMatchesTheRefusalCaptures(t *testing.T) {
	chart := loadChart(t)

	for _, tc := range []struct {
		capture   string
		accountID int64
	}{
		{"A2-214-create-fundsource-retyped", 2}, // Fund Source, retyped to INCOME
		{"A2-prod-063-map-wrong-type", 8},       // Interest On Loans, INCOME
	} {
		account := accountByID(t, chart, tc.accountID)
		err := ValidateLoanSlotAccountType(CashLoanFundSource.Code(), AccountingRuleCashBased, &account)
		if err == nil {
			t.Fatalf("%s: expected a type refusal for GL %d", tc.capture, tc.accountID)
		}
		var body struct {
			Errors []struct {
				Dev  string `json:"developerMessage"`
				Code string `json:"userMessageGlobalisationCode"`
			} `json:"errors"`
		}
		decodeCapture(t, tc.capture, &body)
		var le *LedgerError
		if !errors.As(err, &le) {
			t.Fatalf("%s: not a LedgerError", tc.capture)
		}
		if le.Message != body.Errors[0].Dev {
			t.Errorf("%s: port %q\noracle %q", tc.capture, le.Message, body.Errors[0].Dev)
		}
		if le.Code != body.Errors[0].Code {
			t.Errorf("%s: port code %q, oracle %q", tc.capture, le.Code, body.Errors[0].Code)
		}
	}

	// FUND_SOURCE accepts ASSET *or* LIABILITY, not ASSET alone.
	for _, id := range []int64{16 /* ASSET */, 6 /* LIABILITY */} {
		account := accountByID(t, chart, id)
		if err := ValidateLoanSlotAccountType(CashLoanFundSource.Code(), AccountingRuleCashBased, &account); err != nil {
			t.Errorf("GL %d (%v) should be accepted at FUND_SOURCE: %v", id, account.Classification, err)
		}
	}

	// A HEADER account is accepted: the write path validates the CLASSIFICATION
	// only, never the usage [OBSERVED: A2-prod-062-map-header-account, HTTP 200].
	if st := captureStatus(t, "A2-prod-062-map-header-account"); st != 200 {
		t.Errorf("A2-prod-062-map-header-account status %d, want 200", st)
	}
	header := accountByID(t, chart, 1)
	if !header.IsHeader() {
		t.Fatal("GL 1 should be a HEADER account")
	}
	if err := ValidateLoanSlotAccountType(CashLoanLoanPortfolio.Code(), AccountingRuleCashBased, &header); err != nil {
		t.Errorf("a HEADER ASSET account must be accepted at LOAN_PORTFOLIO: %v", err)
	}
}

func itoa(v int32) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	var buf [12]byte
	i := len(buf)
	for v > 0 {
		i--
		buf[i] = byte('0' + v%10)
		v /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}
