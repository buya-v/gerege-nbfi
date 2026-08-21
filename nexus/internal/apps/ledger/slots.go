package ledger

import (
	"fmt"
	"strings"
)

// TRAP 2 LIVES IN THIS FILE. Read this comment before touching anything below.
//
// Fineract's accounting placeholders are FIVE separate Java enums, one per
// (product family, accounting rule), and their integer codes are NOT a shared
// namespace. The two loan enums in particular collide, and they collide in a
// way that cannot be repaired by choosing a different key:
//
//	code | CashAccountsForLoan       | AccrualAccountsForLoan
//	-----+---------------------------+---------------------------
//	   7 | (absent)                  | INTEREST_RECEIVABLE
//	   8 | (absent)                  | FEES_RECEIVABLE
//	   9 | (absent)                  | PENALTIES_RECEIVABLE
//	  22 | CLASSIFICATION_INCOME     | INCOME_FROM_CAPITALIZATION
//	  24 | INCOME_FROM_DISCOUNT_FEE  | BUY_DOWN_EXPENSE
//	  25 | FEES_RECEIVABLE           | INCOME_FROM_BUY_DOWN
//	  26 | PENALTIES_RECEIVABLE      | (absent)
//
// [VERIFIED: AccountingConstants.java:37-62 (cash, 23 members) and :95-122
// (accrual, 25 members), re-read line by line by this worker at the pinned sha.]
//
// Code 24 is the sharpest: INCOME_FROM_DISCOUNT_FEE is an INCOME role and
// BUY_DOWN_EXPENSE is an EXPENSE role, so a cross-map there posts to the WRONG
// SIDE of the ledger, not merely the wrong account.
//
// AND THE NAME IS NOT A SAFE KEY EITHER. FEES_RECEIVABLE is code 25 under cash
// and code 8 under accrual; PENALTIES_RECEIVABLE is 26 under cash and 9 under
// accrual. So keying on the CODE cross-maps and keying on the NAME cross-maps:
// there is no single keying that is safe, and the only correct model is
// separate types.
//
// WHAT THE COMPILER ENFORCES HERE, AND WHAT IT DOES NOT.
//
// Enforced by the compiler: the five slot types are distinct named types with
// distinct constant spaces and no shared parent enum. No IMPLICIT conversion
// exists in either direction; a function that takes a CashLoanSlot cannot be
// called with an AccrualLoanSlot; a map keyed by one cannot be indexed by the
// other; and the Slot interface below is closed by an unexported method, so a
// raw integer can never be passed where a placeholder is expected.
//
// NOT enforced by the compiler, stated plainly rather than papered over: Go
// permits an EXPLICIT numeric conversion between two named integer types, so
// AccrualLoanSlot(CashLoanFeesReceivable) compiles and yields
// AccrualLoanIncomeFromBuyDown. Nothing in the language can stop that. What
// this package does instead is (a) never write such a conversion, (b) provide
// no helper that would tempt one, and (c) ship TestNoCrossFamilySlotConversion
// in slots_test.go, which scans this package's own source for the pattern and
// has been driven RED against a synthetic sample. That test is a package-local
// regression check and NOT a harness guard: .softhouse/conformance.sh does not
// run `go test`, so it cannot fire there (P-45).

// Slot is one accounting placeholder: the acc_product_mapping
// .financial_account_type value TOGETHER WITH the (product family, accounting
// rule) pair that gives it meaning. A bare integer is never a Slot.
//
// The interface is closed: only the five concrete types in this file implement
// it, because slotFamilyMarker is unexported.
type Slot interface {
	// Code is the integer stored in acc_product_mapping.financial_account_type.
	// It is meaningful ONLY alongside ProductFamily and Rule.
	Code() int32

	// ProductFamily is the acc_product_mapping.product_type this slot's rows
	// are written and queried under.
	ProductFamily() PortfolioProductType

	// Rule is the accounting rule whose enum this slot belongs to. Slots whose
	// code means the same thing under cash and accrual still report the rule
	// they were declared under; the resolver never uses Rule as a query key,
	// only Code and ProductFamily, exactly as the oracle does.
	Rule() AccountingRule

	// IsFamilyReferenceSlot reports whether this is the family's fund-source /
	// reference placeholder — the ONLY placeholder for which a payment-type
	// override row is consulted. Its code is 1 in all three families that have
	// one [VERIFIED: AccountingProcessorHelper.java:1199 (loan, CashAccountsForLoan
	// .FUND_SOURCE), :1285 (savings, CashAccountsForSavings.SAVINGS_REFERENCE),
	// :1309 (shares, CashAccountsForShares.SHARES_REFERENCE)].
	IsFamilyReferenceSlot() bool

	// Name is the Java constant name, underscores intact.
	Name() string

	// String reproduces the oracle's toString(): the constant name with
	// underscores replaced by spaces. It is user-visible in the
	// ProductToGLAccountMappingNotFoundException message.
	String() string

	slotFamilyMarker()
}

// ---------------------------------------------------------------------------
// CashAccountsForLoan — [VERIFIED: AccountingConstants.java:37-62]
// 23 members. Note there is no 7, 8 or 9.
// ---------------------------------------------------------------------------

// CashLoanSlot is a placeholder of Fineract's CashAccountsForLoan enum. It is a
// DISTINCT TYPE from AccrualLoanSlot and the two must never be converted into
// one another — see the trap-2 comment at the top of this file.
type CashLoanSlot int32

const (
	CashLoanFundSource                       CashLoanSlot = 1
	CashLoanLoanPortfolio                    CashLoanSlot = 2
	CashLoanInterestOnLoans                  CashLoanSlot = 3
	CashLoanIncomeFromFees                   CashLoanSlot = 4
	CashLoanIncomeFromPenalties              CashLoanSlot = 5
	CashLoanLossesWrittenOff                 CashLoanSlot = 6
	CashLoanTransfersSuspense                CashLoanSlot = 10
	CashLoanOverpayment                      CashLoanSlot = 11
	CashLoanIncomeFromRecovery               CashLoanSlot = 12
	CashLoanGoodwillCredit                   CashLoanSlot = 13
	CashLoanIncomeFromChargeOffInterest      CashLoanSlot = 14
	CashLoanIncomeFromChargeOffFees          CashLoanSlot = 15
	CashLoanChargeOffExpense                 CashLoanSlot = 16
	CashLoanChargeOffFraudExpense            CashLoanSlot = 17
	CashLoanIncomeFromChargeOffPenalty       CashLoanSlot = 18
	CashLoanIncomeFromGoodwillCreditInterest CashLoanSlot = 19
	CashLoanIncomeFromGoodwillCreditFees     CashLoanSlot = 20
	CashLoanIncomeFromGoodwillCreditPenalty  CashLoanSlot = 21
	CashLoanClassificationIncome             CashLoanSlot = 22
	CashLoanDeferredIncomeLiability          CashLoanSlot = 23
	CashLoanIncomeFromDiscountFee            CashLoanSlot = 24
	CashLoanFeesReceivable                   CashLoanSlot = 25
	CashLoanPenaltiesReceivable              CashLoanSlot = 26
)

var cashLoanNames = map[CashLoanSlot]string{
	CashLoanFundSource:                       "FUND_SOURCE",
	CashLoanLoanPortfolio:                    "LOAN_PORTFOLIO",
	CashLoanInterestOnLoans:                  "INTEREST_ON_LOANS",
	CashLoanIncomeFromFees:                   "INCOME_FROM_FEES",
	CashLoanIncomeFromPenalties:              "INCOME_FROM_PENALTIES",
	CashLoanLossesWrittenOff:                 "LOSSES_WRITTEN_OFF",
	CashLoanTransfersSuspense:                "TRANSFERS_SUSPENSE",
	CashLoanOverpayment:                      "OVERPAYMENT",
	CashLoanIncomeFromRecovery:               "INCOME_FROM_RECOVERY",
	CashLoanGoodwillCredit:                   "GOODWILL_CREDIT",
	CashLoanIncomeFromChargeOffInterest:      "INCOME_FROM_CHARGE_OFF_INTEREST",
	CashLoanIncomeFromChargeOffFees:          "INCOME_FROM_CHARGE_OFF_FEES",
	CashLoanChargeOffExpense:                 "CHARGE_OFF_EXPENSE",
	CashLoanChargeOffFraudExpense:            "CHARGE_OFF_FRAUD_EXPENSE",
	CashLoanIncomeFromChargeOffPenalty:       "INCOME_FROM_CHARGE_OFF_PENALTY",
	CashLoanIncomeFromGoodwillCreditInterest: "INCOME_FROM_GOODWILL_CREDIT_INTEREST",
	CashLoanIncomeFromGoodwillCreditFees:     "INCOME_FROM_GOODWILL_CREDIT_FEES",
	CashLoanIncomeFromGoodwillCreditPenalty:  "INCOME_FROM_GOODWILL_CREDIT_PENALTY",
	CashLoanClassificationIncome:             "CLASSIFICATION_INCOME",
	CashLoanDeferredIncomeLiability:          "DEFERRED_INCOME_LIABILITY",
	CashLoanIncomeFromDiscountFee:            "INCOME_FROM_DISCOUNT_FEE",
	CashLoanFeesReceivable:                   "FEES_RECEIVABLE",
	CashLoanPenaltiesReceivable:              "PENALTIES_RECEIVABLE",
}

func (s CashLoanSlot) Code() int32                         { return int32(s) }
func (s CashLoanSlot) ProductFamily() PortfolioProductType { return ProductLoan }
func (s CashLoanSlot) Rule() AccountingRule                { return AccountingRuleCashBased }
func (s CashLoanSlot) IsFamilyReferenceSlot() bool         { return s == CashLoanFundSource }
func (s CashLoanSlot) Name() string                        { return slotName(cashLoanNames, int32(s), "CashAccountsForLoan") }
func (s CashLoanSlot) String() string                      { return javaToString(s.Name()) }
func (s CashLoanSlot) slotFamilyMarker()                   {}

// CashLoanSlotFromCode decodes a stored financial_account_type for a LOAN
// product whose accounting rule is CASH_BASED. It reproduces
// CashAccountsForLoan.fromInt [VERIFIED: AccountingConstants.java:79-89 — a
// HashMap keyed on value, so unlike PortfolioProductType.fromInt it IS the true
// inverse of getValue()], returning ok=false where the oracle returns null.
func CashLoanSlotFromCode(v int32) (CashLoanSlot, bool) {
	s := CashLoanSlot(v)
	_, ok := cashLoanNames[s]
	return s, ok
}

// ---------------------------------------------------------------------------
// AccrualAccountsForLoan — [VERIFIED: AccountingConstants.java:95-122]
// 25 members. It HAS 7/8/9 and has NO 26.
// ---------------------------------------------------------------------------

// AccrualLoanSlot is a placeholder of Fineract's AccrualAccountsForLoan enum.
// It is a DISTINCT TYPE from CashLoanSlot. They agree on 19 of the 22 codes
// they share and disagree on 22, 24 and 25; and the names FEES_RECEIVABLE and
// PENALTIES_RECEIVABLE sit at different codes in the two enums. Never convert.
type AccrualLoanSlot int32

const (
	AccrualLoanFundSource                       AccrualLoanSlot = 1
	AccrualLoanLoanPortfolio                    AccrualLoanSlot = 2
	AccrualLoanInterestOnLoans                  AccrualLoanSlot = 3
	AccrualLoanIncomeFromFees                   AccrualLoanSlot = 4
	AccrualLoanIncomeFromPenalties              AccrualLoanSlot = 5
	AccrualLoanLossesWrittenOff                 AccrualLoanSlot = 6
	AccrualLoanInterestReceivable               AccrualLoanSlot = 7
	AccrualLoanFeesReceivable                   AccrualLoanSlot = 8
	AccrualLoanPenaltiesReceivable              AccrualLoanSlot = 9
	AccrualLoanTransfersSuspense                AccrualLoanSlot = 10
	AccrualLoanOverpayment                      AccrualLoanSlot = 11
	AccrualLoanIncomeFromRecovery               AccrualLoanSlot = 12
	AccrualLoanGoodwillCredit                   AccrualLoanSlot = 13
	AccrualLoanIncomeFromChargeOffInterest      AccrualLoanSlot = 14
	AccrualLoanIncomeFromChargeOffFees          AccrualLoanSlot = 15
	AccrualLoanChargeOffExpense                 AccrualLoanSlot = 16
	AccrualLoanChargeOffFraudExpense            AccrualLoanSlot = 17
	AccrualLoanIncomeFromChargeOffPenalty       AccrualLoanSlot = 18
	AccrualLoanIncomeFromGoodwillCreditInterest AccrualLoanSlot = 19
	AccrualLoanIncomeFromGoodwillCreditFees     AccrualLoanSlot = 20
	AccrualLoanIncomeFromGoodwillCreditPenalty  AccrualLoanSlot = 21
	AccrualLoanIncomeFromCapitalization         AccrualLoanSlot = 22
	AccrualLoanDeferredIncomeLiability          AccrualLoanSlot = 23
	AccrualLoanBuyDownExpense                   AccrualLoanSlot = 24
	AccrualLoanIncomeFromBuyDown                AccrualLoanSlot = 25
)

var accrualLoanNames = map[AccrualLoanSlot]string{
	AccrualLoanFundSource:                       "FUND_SOURCE",
	AccrualLoanLoanPortfolio:                    "LOAN_PORTFOLIO",
	AccrualLoanInterestOnLoans:                  "INTEREST_ON_LOANS",
	AccrualLoanIncomeFromFees:                   "INCOME_FROM_FEES",
	AccrualLoanIncomeFromPenalties:              "INCOME_FROM_PENALTIES",
	AccrualLoanLossesWrittenOff:                 "LOSSES_WRITTEN_OFF",
	AccrualLoanInterestReceivable:               "INTEREST_RECEIVABLE",
	AccrualLoanFeesReceivable:                   "FEES_RECEIVABLE",
	AccrualLoanPenaltiesReceivable:              "PENALTIES_RECEIVABLE",
	AccrualLoanTransfersSuspense:                "TRANSFERS_SUSPENSE",
	AccrualLoanOverpayment:                      "OVERPAYMENT",
	AccrualLoanIncomeFromRecovery:               "INCOME_FROM_RECOVERY",
	AccrualLoanGoodwillCredit:                   "GOODWILL_CREDIT",
	AccrualLoanIncomeFromChargeOffInterest:      "INCOME_FROM_CHARGE_OFF_INTEREST",
	AccrualLoanIncomeFromChargeOffFees:          "INCOME_FROM_CHARGE_OFF_FEES",
	AccrualLoanChargeOffExpense:                 "CHARGE_OFF_EXPENSE",
	AccrualLoanChargeOffFraudExpense:            "CHARGE_OFF_FRAUD_EXPENSE",
	AccrualLoanIncomeFromChargeOffPenalty:       "INCOME_FROM_CHARGE_OFF_PENALTY",
	AccrualLoanIncomeFromGoodwillCreditInterest: "INCOME_FROM_GOODWILL_CREDIT_INTEREST",
	AccrualLoanIncomeFromGoodwillCreditFees:     "INCOME_FROM_GOODWILL_CREDIT_FEES",
	AccrualLoanIncomeFromGoodwillCreditPenalty:  "INCOME_FROM_GOODWILL_CREDIT_PENALTY",
	AccrualLoanIncomeFromCapitalization:         "INCOME_FROM_CAPITALIZATION",
	AccrualLoanDeferredIncomeLiability:          "DEFERRED_INCOME_LIABILITY",
	AccrualLoanBuyDownExpense:                   "BUY_DOWN_EXPENSE",
	AccrualLoanIncomeFromBuyDown:                "INCOME_FROM_BUY_DOWN",
}

func (s AccrualLoanSlot) Code() int32 { return int32(s) }

// ProductFamily is LOAN. Both loan enums are stored under product_type = 1; the
// accounting rule is NOT part of the storage key, which is exactly why the
// collision at 22/24/25 is dangerous.
func (s AccrualLoanSlot) ProductFamily() PortfolioProductType { return ProductLoan }
func (s AccrualLoanSlot) Rule() AccountingRule                { return AccountingRuleAccrualPeriodic }
func (s AccrualLoanSlot) IsFamilyReferenceSlot() bool         { return s == AccrualLoanFundSource }
func (s AccrualLoanSlot) Name() string {
	return slotName(accrualLoanNames, int32(s), "AccrualAccountsForLoan")
}
func (s AccrualLoanSlot) String() string    { return javaToString(s.Name()) }
func (s AccrualLoanSlot) slotFamilyMarker() {}

// AccrualLoanSlotFromCode reproduces AccrualAccountsForLoan.fromInt
// [VERIFIED: AccountingConstants.java:139-149 — HashMap on value].
func AccrualLoanSlotFromCode(v int32) (AccrualLoanSlot, bool) {
	s := AccrualLoanSlot(v)
	_, ok := accrualLoanNames[s]
	return s, ok
}

// ---------------------------------------------------------------------------
// CashAccountsForSavings — [VERIFIED: AccountingConstants.java:267-278]
// ---------------------------------------------------------------------------

// CashSavingsSlot is a placeholder of Fineract's CashAccountsForSavings enum.
//
// Savings/deposit code is IN SCOPE to port and OUT OF SCOPE to activate: the
// tenant licence is NBFI (ББСБ) and accepting deposits is prohibited by the Law
// on Non-Banking Financial Activities Art. 12.1.3 / 12.1.4. Nothing in this
// package exposes an endpoint or enables behaviour; it is a value type.
type CashSavingsSlot int32

const (
	CashSavingsSavingsReference          CashSavingsSlot = 1
	CashSavingsSavingsControl            CashSavingsSlot = 2
	CashSavingsInterestOnSavings         CashSavingsSlot = 3
	CashSavingsIncomeFromFees            CashSavingsSlot = 4
	CashSavingsIncomeFromPenalties       CashSavingsSlot = 5
	CashSavingsTransfersSuspense         CashSavingsSlot = 10
	CashSavingsOverdraftPortfolioControl CashSavingsSlot = 11
	CashSavingsIncomeFromInterest        CashSavingsSlot = 12
	CashSavingsLossesWrittenOff          CashSavingsSlot = 13
	CashSavingsEscheatLiability          CashSavingsSlot = 14
)

var cashSavingsNames = map[CashSavingsSlot]string{
	CashSavingsSavingsReference:          "SAVINGS_REFERENCE",
	CashSavingsSavingsControl:            "SAVINGS_CONTROL",
	CashSavingsInterestOnSavings:         "INTEREST_ON_SAVINGS",
	CashSavingsIncomeFromFees:            "INCOME_FROM_FEES",
	CashSavingsIncomeFromPenalties:       "INCOME_FROM_PENALTIES",
	CashSavingsTransfersSuspense:         "TRANSFERS_SUSPENSE",
	CashSavingsOverdraftPortfolioControl: "OVERDRAFT_PORTFOLIO_CONTROL",
	CashSavingsIncomeFromInterest:        "INCOME_FROM_INTEREST",
	CashSavingsLossesWrittenOff:          "LOSSES_WRITTEN_OFF",
	CashSavingsEscheatLiability:          "ESCHEAT_LIABILITY",
}

func (s CashSavingsSlot) Code() int32                         { return int32(s) }
func (s CashSavingsSlot) ProductFamily() PortfolioProductType { return ProductSaving }
func (s CashSavingsSlot) Rule() AccountingRule                { return AccountingRuleCashBased }
func (s CashSavingsSlot) IsFamilyReferenceSlot() bool         { return s == CashSavingsSavingsReference }
func (s CashSavingsSlot) Name() string {
	return slotName(cashSavingsNames, int32(s), "CashAccountsForSavings")
}
func (s CashSavingsSlot) String() string    { return javaToString(s.Name()) }
func (s CashSavingsSlot) slotFamilyMarker() {}

// ---------------------------------------------------------------------------
// AccrualAccountsForSavings — [VERIFIED: AccountingConstants.java:311-326]
// The same ten as cash plus 15..18. NO collision within the savings family.
// ---------------------------------------------------------------------------

// AccrualSavingsSlot is a placeholder of Fineract's AccrualAccountsForSavings
// enum. Unlike the loan pair, the savings pair does NOT collide: the accrual
// enum is a strict superset of the cash one. It is still a separate type,
// because "these two happen to agree today" is not a property a port should
// depend on and the loan pair proves what happens when the assumption fails.
type AccrualSavingsSlot int32

const (
	AccrualSavingsSavingsReference          AccrualSavingsSlot = 1
	AccrualSavingsSavingsControl            AccrualSavingsSlot = 2
	AccrualSavingsInterestOnSavings         AccrualSavingsSlot = 3
	AccrualSavingsIncomeFromFees            AccrualSavingsSlot = 4
	AccrualSavingsIncomeFromPenalties       AccrualSavingsSlot = 5
	AccrualSavingsTransfersSuspense         AccrualSavingsSlot = 10
	AccrualSavingsOverdraftPortfolioControl AccrualSavingsSlot = 11
	AccrualSavingsIncomeFromInterest        AccrualSavingsSlot = 12
	AccrualSavingsLossesWrittenOff          AccrualSavingsSlot = 13
	AccrualSavingsEscheatLiability          AccrualSavingsSlot = 14
	AccrualSavingsFeesReceivable            AccrualSavingsSlot = 15
	AccrualSavingsPenaltiesReceivable       AccrualSavingsSlot = 16
	AccrualSavingsInterestPayable           AccrualSavingsSlot = 17
	AccrualSavingsInterestReceivable        AccrualSavingsSlot = 18
)

var accrualSavingsNames = map[AccrualSavingsSlot]string{
	AccrualSavingsSavingsReference:          "SAVINGS_REFERENCE",
	AccrualSavingsSavingsControl:            "SAVINGS_CONTROL",
	AccrualSavingsInterestOnSavings:         "INTEREST_ON_SAVINGS",
	AccrualSavingsIncomeFromFees:            "INCOME_FROM_FEES",
	AccrualSavingsIncomeFromPenalties:       "INCOME_FROM_PENALTIES",
	AccrualSavingsTransfersSuspense:         "TRANSFERS_SUSPENSE",
	AccrualSavingsOverdraftPortfolioControl: "OVERDRAFT_PORTFOLIO_CONTROL",
	AccrualSavingsIncomeFromInterest:        "INCOME_FROM_INTEREST",
	AccrualSavingsLossesWrittenOff:          "LOSSES_WRITTEN_OFF",
	AccrualSavingsEscheatLiability:          "ESCHEAT_LIABILITY",
	AccrualSavingsFeesReceivable:            "FEES_RECEIVABLE",
	AccrualSavingsPenaltiesReceivable:       "PENALTIES_RECEIVABLE",
	AccrualSavingsInterestPayable:           "INTEREST_PAYABLE",
	AccrualSavingsInterestReceivable:        "INTEREST_RECEIVABLE",
}

func (s AccrualSavingsSlot) Code() int32                         { return int32(s) }
func (s AccrualSavingsSlot) ProductFamily() PortfolioProductType { return ProductSaving }
func (s AccrualSavingsSlot) Rule() AccountingRule                { return AccountingRuleAccrualPeriodic }
func (s AccrualSavingsSlot) IsFamilyReferenceSlot() bool {
	return s == AccrualSavingsSavingsReference
}
func (s AccrualSavingsSlot) Name() string {
	return slotName(accrualSavingsNames, int32(s), "AccrualAccountsForSavings")
}
func (s AccrualSavingsSlot) String() string    { return javaToString(s.Name()) }
func (s AccrualSavingsSlot) slotFamilyMarker() {}

// ---------------------------------------------------------------------------
// CashAccountsForShares — [VERIFIED: AccountingConstants.java:517-522]
// ---------------------------------------------------------------------------

// CashSharesSlot is a placeholder of Fineract's CashAccountsForShares enum.
// There is no accrual shares enum in this revision.
type CashSharesSlot int32

const (
	CashSharesSharesReference CashSharesSlot = 1
	CashSharesSharesSuspense  CashSharesSlot = 2
	CashSharesIncomeFromFees  CashSharesSlot = 3
	CashSharesSharesEquity    CashSharesSlot = 4
)

var cashSharesNames = map[CashSharesSlot]string{
	CashSharesSharesReference: "SHARES_REFERENCE",
	CashSharesSharesSuspense:  "SHARES_SUSPENSE",
	CashSharesIncomeFromFees:  "INCOME_FROM_FEES",
	CashSharesSharesEquity:    "SHARES_EQUITY",
}

func (s CashSharesSlot) Code() int32                         { return int32(s) }
func (s CashSharesSlot) ProductFamily() PortfolioProductType { return ProductShares }
func (s CashSharesSlot) Rule() AccountingRule                { return AccountingRuleCashBased }
func (s CashSharesSlot) IsFamilyReferenceSlot() bool         { return s == CashSharesSharesReference }
func (s CashSharesSlot) Name() string {
	return slotName(cashSharesNames, int32(s), "CashAccountsForShares")
}
func (s CashSharesSlot) String() string    { return javaToString(s.Name()) }
func (s CashSharesSlot) slotFamilyMarker() {}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

func slotName[T ~int32](names map[T]string, code int32, enumName string) string {
	if n, ok := names[T(code)]; ok {
		return n
	}
	return fmt.Sprintf("%s(%d)", enumName, code)
}

// javaToString reproduces Java's `name().replace("_", " ")`, which every one of
// these enums overrides toString() with [VERIFIED: AccountingConstants.java:70-73
// (cash loan), :131-134 (accrual loan), and the same shape in each of the
// others]. This is the exact text the oracle puts in the not-found refusal:
// "... does not exist for an account of type CHARGE OFF EXPENSE"
// [graded against capture A2-224-chargeoff-unmapped].
func javaToString(name string) string {
	return strings.ReplaceAll(name, "_", " ")
}
