package ledger

import (
	"go/scanner"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TRAP 2, tested from both ends: the code is not a safe key, and the name is
// not a safe key either.

func TestLoanEnumsCollideAtTwentyTwoTwentyFourTwentyFive(t *testing.T) {
	// [VERIFIED: AccountingConstants.java:37-62 and :95-122]
	collisions := []struct {
		code        int32
		cashName    string
		accrualName string
	}{
		{22, "CLASSIFICATION_INCOME", "INCOME_FROM_CAPITALIZATION"},
		{24, "INCOME_FROM_DISCOUNT_FEE", "BUY_DOWN_EXPENSE"},
		{25, "FEES_RECEIVABLE", "INCOME_FROM_BUY_DOWN"},
	}
	for _, c := range collisions {
		cash, okC := CashLoanSlotFromCode(c.code)
		accrual, okA := AccrualLoanSlotFromCode(c.code)
		if !okC || !okA {
			t.Fatalf("code %d: expected both enums to carry it (cash ok=%v, accrual ok=%v)", c.code, okC, okA)
		}
		if cash.Name() != c.cashName {
			t.Errorf("cash %d = %q, want %q", c.code, cash.Name(), c.cashName)
		}
		if accrual.Name() != c.accrualName {
			t.Errorf("accrual %d = %q, want %q", c.code, accrual.Name(), c.accrualName)
		}
		if cash.Name() == accrual.Name() {
			t.Errorf("code %d is supposed to COLLIDE; both enums render %q", c.code, cash.Name())
		}
	}

	// Code 24 is the sharpest collision. What is VERIFIED from a writer: the
	// ACCRUAL side is written by saveLoanToExpenseAccountMapping, so its
	// create-time type check demands EXPENSE
	// [VERIFIED: ProductToGLAccountMappingWritePlatformServiceImpl.java:224-228].
	accrualShape, ok := LoanSlotAPIShape(24, AccountingRuleAccrualPeriodic)
	if !ok {
		t.Fatal("no accrual shape for code 24")
	}
	if len(accrualShape.AllowedClassifications) != 1 || accrualShape.AllowedClassifications[0] != ClassificationExpense {
		t.Errorf("accrual code 24 should demand EXPENSE, got %v", accrualShape.AllowedClassifications)
	}
	// What is NOT verified from a writer: the cash side has no create-path type
	// check at all, so the port records no allowed set for it rather than
	// inventing INCOME from the constant's name. The wrong-SIDE hazard is
	// therefore asserted on the two names, which is what the source supports:
	// INCOME_FROM_DISCOUNT_FEE against BUY_DOWN_EXPENSE at one code.
	cashShape, ok := LoanSlotAPIShape(24, AccountingRuleCashBased)
	if !ok {
		t.Fatal("no cash shape for code 24")
	}
	if len(cashShape.AllowedClassifications) != 0 {
		t.Errorf("cash code 24 has no create-path type check in the oracle; "+
			"the port must not invent one, got %v", cashShape.AllowedClassifications)
	}
}

func TestLoanEnumsDisagreeOnExactlyThreeOfTheirSharedCodes(t *testing.T) {
	// The census: of the codes both enums carry, 19 agree and exactly 3 differ.
	var shared, agree, differ int
	for v := int32(1); v <= 26; v++ {
		cash, okC := CashLoanSlotFromCode(v)
		accrual, okA := AccrualLoanSlotFromCode(v)
		if !okC || !okA {
			continue
		}
		shared++
		if cash.Name() == accrual.Name() {
			agree++
		} else {
			differ++
		}
	}
	if shared != 22 || agree != 19 || differ != 3 {
		t.Errorf("shared/agree/differ = %d/%d/%d, want 22/19/3", shared, agree, differ)
	}

	// The asymmetric members: accrual has 7, 8, 9 and no 26; cash has 26 and no
	// 7, 8, 9.
	for _, v := range []int32{7, 8, 9} {
		if _, ok := CashLoanSlotFromCode(v); ok {
			t.Errorf("CashAccountsForLoan should not carry %d", v)
		}
		if _, ok := AccrualLoanSlotFromCode(v); !ok {
			t.Errorf("AccrualAccountsForLoan should carry %d", v)
		}
	}
	if _, ok := AccrualLoanSlotFromCode(26); ok {
		t.Error("AccrualAccountsForLoan should not carry 26")
	}
	if _, ok := CashLoanSlotFromCode(26); !ok {
		t.Error("CashAccountsForLoan should carry 26")
	}
}

// TestNameIsNotAFunctionAcrossThePairEither is the third trap the driver's
// re-derivation added: keying on the NAME cross-maps too.
func TestNameIsNotAFunctionAcrossThePairEither(t *testing.T) {
	cases := []struct {
		name        string
		cashCode    int32
		accrualCode int32
	}{
		{"FEES_RECEIVABLE", 25, 8},
		{"PENALTIES_RECEIVABLE", 26, 9},
	}
	for _, c := range cases {
		cash, ok := CashLoanSlotFromCode(c.cashCode)
		if !ok || cash.Name() != c.name {
			t.Fatalf("cash %d should be %q, got %q (ok=%v)", c.cashCode, c.name, cash.Name(), ok)
		}
		accrual, ok := AccrualLoanSlotFromCode(c.accrualCode)
		if !ok || accrual.Name() != c.name {
			t.Fatalf("accrual %d should be %q, got %q (ok=%v)", c.accrualCode, c.name, accrual.Name(), ok)
		}
		if c.cashCode == c.accrualCode {
			t.Fatalf("%q is supposed to sit at DIFFERENT codes in the two enums", c.name)
		}
	}
}

func TestSlotStringReproducesJavaToString(t *testing.T) {
	// [OBSERVED: A2-224 "...for an account of type CHARGE OFF EXPENSE",
	// A2-225 "... GOODWILL CREDIT"]
	if got := CashLoanChargeOffExpense.String(); got != "CHARGE OFF EXPENSE" {
		t.Errorf("CashLoanChargeOffExpense.String() = %q", got)
	}
	if got := CashLoanGoodwillCredit.String(); got != "GOODWILL CREDIT" {
		t.Errorf("CashLoanGoodwillCredit.String() = %q", got)
	}
	if got := AccrualLoanChargeOffExpense.String(); got != "CHARGE OFF EXPENSE" {
		t.Errorf("AccrualLoanChargeOffExpense.String() = %q", got)
	}
}

func TestEveryFamilyReferenceSlotIsCodeOne(t *testing.T) {
	// [VERIFIED: AccountingProcessorHelper.java:1199, :1285, :1309 — the
	// payment-type override is gated on the family's code-1 placeholder in all
	// three families.]
	refs := []Slot{CashLoanFundSource, AccrualLoanFundSource, CashSavingsSavingsReference,
		AccrualSavingsSavingsReference, CashSharesSharesReference}
	for _, s := range refs {
		if !s.IsFamilyReferenceSlot() {
			t.Errorf("%T %s should be the family reference slot", s, s.Name())
		}
		if s.Code() != 1 {
			t.Errorf("%T %s has code %d, want 1", s, s.Name(), s.Code())
		}
	}
	nonRefs := []Slot{CashLoanLoanPortfolio, AccrualLoanFeesReceivable, CashSavingsSavingsControl, CashSharesSharesEquity}
	for _, s := range nonRefs {
		if s.IsFamilyReferenceSlot() {
			t.Errorf("%T %s should NOT be the family reference slot", s, s.Name())
		}
	}
}

func TestSlotProductFamilies(t *testing.T) {
	cases := []struct {
		slot Slot
		want PortfolioProductType
	}{
		{CashLoanFundSource, ProductLoan},
		{AccrualLoanFundSource, ProductLoan},
		{CashSavingsSavingsReference, ProductSaving},
		{AccrualSavingsInterestPayable, ProductSaving},
		{CashSharesSharesEquity, ProductShares},
	}
	for _, c := range cases {
		if got := c.slot.ProductFamily(); got != c.want {
			t.Errorf("%s.ProductFamily() = %v, want %v", c.slot.Name(), got, c.want)
		}
	}
}

func TestPlaceholderDisjointnessHolds(t *testing.T) {
	// assertPlaceholderDisjointness runs at init and panics on a collision, so
	// reaching this test at all is most of the evidence. Assert the property
	// directly too, so the test names what it defends.
	for v := int32(1); v <= 26; v++ {
		if _, clash := FinancialActivityFromValue(v); clash {
			t.Errorf("placeholder code %d collides with a FinancialActivity value; "+
				"resolution decides organisation-vs-product by that lookup ALONE "+
				"(AccountingProcessorHelper.java:1340-1342), so this would silently "+
				"reroute every posting at that placeholder", v)
		}
	}
}

// ---------------------------------------------------------------------------
// The cross-family conversion scan. See the trap-2 comment in slots.go for what
// this can and cannot guarantee.
//
// P-45: THIS IS NOT A HARNESS GUARD. .softhouse/conformance.sh does not run
// `go test`, and its guard_no_float_in_harness / guard_gofmt only walk
// nexus/internal/apps/loanschedule, so nothing in this package is covered by a
// HARD guard today. That gap is reported in the handoff as a follow-up rather
// than patched here, because conformance.sh is outside this task's files_hint.
// ---------------------------------------------------------------------------

var slotTypeNames = []string{
	"CashLoanSlot", "AccrualLoanSlot",
	"CashSavingsSlot", "AccrualSavingsSlot",
	"CashSharesSlot",
}

// findCrossFamilyConversions reports every `XSlot(` conversion applied to an
// identifier that belongs to a DIFFERENT slot family. It works on the token
// stream, so a mention inside a comment (this file is full of them) cannot trip
// it.
func findCrossFamilyConversions(src string) []string {
	var out []string
	fset := token.NewFileSet()
	file := fset.AddFile("scan.go", fset.Base(), len(src))
	var s scanner.Scanner
	s.Init(file, []byte(src), nil, 0) // mode 0: comments are NOT emitted
	type tok struct {
		t token.Token
		l string
	}
	var toks []tok
	for {
		_, tt, lit := s.Scan()
		if tt == token.EOF {
			break
		}
		toks = append(toks, tok{tt, lit})
	}
	familyOf := func(ident string) string {
		for _, prefix := range []string{"CashLoan", "AccrualLoan", "CashSavings", "AccrualSavings", "CashShares"} {
			if strings.HasPrefix(ident, prefix) {
				return prefix
			}
		}
		return ""
	}
	typeFamily := map[string]string{
		"CashLoanSlot": "CashLoan", "AccrualLoanSlot": "AccrualLoan",
		"CashSavingsSlot": "CashSavings", "AccrualSavingsSlot": "AccrualSavings",
		"CashSharesSlot": "CashShares",
	}
	for i := 0; i+2 < len(toks); i++ {
		if toks[i].t != token.IDENT {
			continue
		}
		want, isSlotType := typeFamily[toks[i].l]
		if !isSlotType {
			continue
		}
		if toks[i+1].t != token.LPAREN || toks[i+2].t != token.IDENT {
			continue
		}
		arg := toks[i+2].l
		got := familyOf(arg)
		if got != "" && got != want {
			out = append(out, toks[i].l+"("+arg+")")
		}
	}
	return out
}

func TestNoCrossFamilySlotConversion(t *testing.T) {
	// FIRST, DRIVE THE SCANNER RED (P-22). A guard that has never failed has
	// not been tested, and an assertion that cannot fail converts "not checked"
	// into "checked and fine".
	red := "package p\nvar bad = AccrualLoanSlot(CashLoanFeesReceivable)\n"
	if hits := findCrossFamilyConversions(red); len(hits) != 1 || hits[0] != "AccrualLoanSlot(CashLoanFeesReceivable)" {
		t.Fatalf("the scanner cannot detect the very edit it exists to detect: %v", hits)
	}
	// A same-family conversion is legitimate and must NOT be flagged, or the
	// guard would be noise and would be switched off.
	green := "package p\nvar ok = CashLoanSlot(CashLoanFundSource)\n"
	if hits := findCrossFamilyConversions(green); len(hits) != 0 {
		t.Fatalf("same-family conversion wrongly flagged: %v", hits)
	}
	// And a mention inside a COMMENT must not trip it, because slots.go's own
	// doc comment names the forbidden expression in order to forbid it.
	comment := "package p\n// AccrualLoanSlot(CashLoanFeesReceivable) is forbidden.\n"
	if hits := findCrossFamilyConversions(comment); len(hits) != 0 {
		t.Fatalf("a comment tripped the scanner: %v", hits)
	}

	// NOW RUN IT OVER THE PACKAGE.
	entries, err := os.ReadDir(".")
	if err != nil {
		t.Fatalf("readdir: %v", err)
	}
	var scanned int
	for _, e := range entries {
		if e.IsDir() || filepath.Ext(e.Name()) != ".go" {
			continue
		}
		b, err := os.ReadFile(e.Name())
		if err != nil {
			t.Fatalf("read %s: %v", e.Name(), err)
		}
		scanned++
		for _, hit := range findCrossFamilyConversions(string(b)) {
			t.Errorf("%s: cross-family slot conversion %s — "+
				"the two loan enums disagree at codes 22, 24 and 25, and at 24 an "+
				"INCOME role against an EXPENSE role, so this posts to the wrong side",
				e.Name(), hit)
		}
	}
	// A guard that inspects zero files must be an error, not a pass (P-22).
	if scanned == 0 {
		t.Fatal("the cross-family scan inspected zero files")
	}
}

// TestNoFloatingPointInThisPackage is the package-local no-float regression
// check. It walks the TOKEN stream, so the doc comments that name the forbidden
// types in order to forbid them do not trip it — a byte grep would fire on the
// prohibition itself.
//
// P-45 again: this is NOT a harness guard, because conformance.sh does not run
// `go test` and its own float guard is scoped to the loanschedule tree.
func TestNoFloatingPointInThisPackage(t *testing.T) {
	forbidden := map[string]bool{
		"float32": true, "float64": true,
		"complex64": true, "complex128": true,
		"ParseFloat": true, "FormatFloat": true, "AppendFloat": true,
	}

	scan := func(src string) []string {
		var out []string
		fset := token.NewFileSet()
		file := fset.AddFile("scan.go", fset.Base(), len(src))
		var s scanner.Scanner
		s.Init(file, []byte(src), nil, 0)
		for {
			_, tt, lit := s.Scan()
			if tt == token.EOF {
				break
			}
			if tt == token.IDENT && forbidden[lit] {
				out = append(out, lit)
			}
			// A float LITERAL is money-shaped even without a float type.
			if tt == token.FLOAT || tt == token.IMAG {
				out = append(out, lit)
			}
		}
		return out
	}

	// Drive it red first, on all three shapes it must catch.
	for _, red := range []string{
		"package p\nvar x float64\n",
		"package p\nvar x = 1.5\n",
		"package p\nimport \"strconv\"\nvar _ = strconv.ParseFloat\n",
	} {
		if hits := scan(red); len(hits) == 0 {
			t.Fatalf("the no-float scan cannot detect %q", red)
		}
	}
	// And prove it does NOT fire on a comment naming the forbidden type.
	if hits := scan("package p\n// float64 is forbidden here.\n"); len(hits) != 0 {
		t.Fatalf("a comment tripped the no-float scan: %v", hits)
	}

	entries, err := os.ReadDir(".")
	if err != nil {
		t.Fatalf("readdir: %v", err)
	}
	var scanned int
	for _, e := range entries {
		if e.IsDir() || filepath.Ext(e.Name()) != ".go" {
			continue
		}
		b, err := os.ReadFile(e.Name())
		if err != nil {
			t.Fatalf("read %s: %v", e.Name(), err)
		}
		scanned++
		if hits := scan(string(b)); len(hits) != 0 {
			t.Errorf("%s: floating-point token(s) %v — money is integer minor units, "+
				"with no float on any path including intermediate calculation", e.Name(), hits)
		}
	}
	if scanned == 0 {
		t.Fatal("the no-float scan inspected zero files")
	}
}
