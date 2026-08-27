package ledger

import "fmt"

// AccountingRule is the product's accounting rule: acc's AccountingRuleType.
// [VERIFIED: AccountingRuleType.java:29-32 — NONE(1), CASH_BASED(2),
// ACCRUAL_PERIODIC(3), ACCRUAL_UPFRONT(4)]
//
// It is load-bearing for TRAP 2: a stored acc_product_mapping row's
// financial_account_type is NOT decidable from the row alone, because for a
// LOAN product codes 22, 24 and 25 mean different things under cash and under
// accrual. You must read the product's accounting rule to know which enum the
// integer belongs to. That is why every Slot in this package carries its
// accounting rule with it and why there is no bare integer placeholder type.
type AccountingRule int32

const (
	AccountingRuleNone AccountingRule = iota
	AccountingRuleCashBased
	AccountingRuleAccrualPeriodic
	AccountingRuleAccrualUpfront
)

// accountingRuleStoredValue is the persisted / wire integer.
// [VERIFIED: AccountingRuleType.java:29-32]
var accountingRuleStoredValue = map[AccountingRule]int32{
	AccountingRuleNone:            1,
	AccountingRuleCashBased:       2,
	AccountingRuleAccrualPeriodic: 3,
	AccountingRuleAccrualUpfront:  4,
}

// accountingRuleCode is the i18n code the oracle emits in
// GET /loanproducts/{id} as accountingRule.code.
// [VERIFIED: AccountingRuleType.java:29-32; graded against captures
// A2-212-read-product22-channel-override (accountingRuleType.cash) and
// A2-213-read-product28-accrual (accountingRuleType.accrual.periodic)]
var accountingRuleCode = map[AccountingRule]string{
	AccountingRuleNone:            "accountingRuleType.none",
	AccountingRuleCashBased:       "accountingRuleType.cash",
	AccountingRuleAccrualPeriodic: "accountingRuleType.accrual.periodic",
	AccountingRuleAccrualUpfront:  "accountingRuleType.accrual.upfront",
}

var accountingRuleFromStored = map[int32]AccountingRule{}

func init() {
	for r, v := range accountingRuleStoredValue {
		if _, dup := accountingRuleFromStored[v]; dup {
			panic(fmt.Sprintf("ledger: accounting rule encode table is not injective at %d", v))
		}
		accountingRuleFromStored[v] = r
	}
}

// StoredValue returns the persisted integer for the accounting rule.
func (r AccountingRule) StoredValue() int32 {
	v, ok := accountingRuleStoredValue[r]
	if !ok {
		panic(fmt.Sprintf("ledger: unknown AccountingRule %d", int32(r)))
	}
	return v
}

// Code returns the oracle's i18n code, as emitted on the product read.
func (r AccountingRule) Code() string { return accountingRuleCode[r] }

// String reproduces the oracle's toString() — name() with underscores replaced
// by spaces [VERIFIED: AccountingRuleType.java:56-59].
func (r AccountingRule) String() string {
	switch r {
	case AccountingRuleNone:
		return "NONE"
	case AccountingRuleCashBased:
		return "CASH BASED"
	case AccountingRuleAccrualPeriodic:
		return "ACCRUAL PERIODIC"
	case AccountingRuleAccrualUpfront:
		return "ACCRUAL UPFRONT"
	default:
		return fmt.Sprintf("AccountingRule(%d)", int32(r))
	}
}

// AccountingRuleFromStoredValue decodes the persisted integer.
func AccountingRuleFromStoredValue(v int32) (AccountingRule, bool) {
	r, ok := accountingRuleFromStored[v]
	return r, ok
}

// IsAccrual reports whether the rule selects the ACCRUAL placeholder enum
// rather than the CASH one.
//
// ACCRUAL_UPFRONT falls through to the ACCRUAL_PERIODIC arm on the loan create
// path [VERIFIED: ProductToGLAccountMappingWritePlatformServiceImpl.java:149-246
// — the ACCRUAL_UPFRONT case has no body and drops into ACCRUAL_PERIODIC], so
// both accrual rules read the accrual enum. NONE writes no mappings at all
// [VERIFIED: same file, :75-76].
func (r AccountingRule) IsAccrual() bool {
	return r == AccountingRuleAccrualPeriodic || r == AccountingRuleAccrualUpfront
}
