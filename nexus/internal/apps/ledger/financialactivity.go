package ledger

import "fmt"

// FinancialActivity is acc_gl_financial_activity_account.financial_activity_type
// — Fineract's FinancialActivity enum.
// [VERIFIED: AccountingConstants.java:437-445, re-read by this worker]
//
// Declaration order in the source is ASSET_TRANSFER, LIABILITY_TRANSFER,
// CASH_AT_MAINVAULT, CASH_AT_TELLER, OPENING_BALANCES_TRANSFER_CONTRA,
// ASSET_FUND_SOURCE, PAYABLE_DIVIDENDS — i.e. NOT value order. ordinal() would
// be wrong here in a way that changes which account a transfer posts to. The
// oracle's own fromInt is a HashMap on value and is therefore correct
// [VERIFIED: AccountingConstants.java:488-498]; this port stores the value
// table and derives the inverse from it, so the ordering cannot leak in.
type FinancialActivity int32

const (
	FinancialActivityAssetTransfer FinancialActivity = iota
	FinancialActivityLiabilityTransfer
	FinancialActivityCashAtMainVault
	FinancialActivityCashAtTeller
	FinancialActivityOpeningBalancesTransferContra
	FinancialActivityAssetFundSource
	FinancialActivityPayableDividends
)

type financialActivityDef struct {
	value          int32
	code           string
	name           string
	classification Classification
}

// financialActivityTable is the whole enum. The required Classification is not
// advisory: it is enforced on create and on update
// [VERIFIED: FinancialActivityAccountWritePlatformServiceImpl.java:84-90;
// OBSERVED: A2-fin-103-wrong-account-type, HTTP 403,
// error.msg.financialActivityAccount.invalid].
var financialActivityTable = map[FinancialActivity]financialActivityDef{
	FinancialActivityAssetTransfer:                 {100, "assetTransfer", "ASSET_TRANSFER", ClassificationAsset},
	FinancialActivityCashAtMainVault:               {101, "cashAtMainVault", "CASH_AT_MAINVAULT", ClassificationAsset},
	FinancialActivityCashAtTeller:                  {102, "cashAtTeller", "CASH_AT_TELLER", ClassificationAsset},
	FinancialActivityAssetFundSource:               {103, "fundSource", "ASSET_FUND_SOURCE", ClassificationAsset},
	FinancialActivityLiabilityTransfer:             {200, "liabilityTransfer", "LIABILITY_TRANSFER", ClassificationLiability},
	FinancialActivityPayableDividends:              {201, "payableDividends", "PAYABLE_DIVIDENDS", ClassificationLiability},
	FinancialActivityOpeningBalancesTransferContra: {300, "openingBalancesTransferContra", "OPENING_BALANCES_TRANSFER_CONTRA", ClassificationEquity},
}

var financialActivityFromValue = map[int32]FinancialActivity{}

// financialActivityCreatable is the CREATE validator's allowed list — SEVEN
// values [VERIFIED: FinancialActivityAccountDataValidator.java:62-66; OBSERVED
// verbatim in the refusal message of A2-fin-104-unknown-activity: "must be one
// of [ 100, 200, 101, 102, 300, 103, 201 ]"].
var financialActivityCreatable = []FinancialActivity{
	FinancialActivityAssetTransfer,
	FinancialActivityLiabilityTransfer,
	FinancialActivityCashAtMainVault,
	FinancialActivityCashAtTeller,
	FinancialActivityOpeningBalancesTransferContra,
	FinancialActivityAssetFundSource,
	FinancialActivityPayableDividends,
}

// financialActivityUpdatable is the UPDATE validator's allowed list — FIVE
// values. CASH_AT_MAINVAULT (101) and CASH_AT_TELLER (102) are CREATABLE BUT
// NOT SETTABLE ON UPDATE [VERIFIED: FinancialActivityAccountDataValidator.java:89-92,
// both halves of the list read by this worker; the omission is not a
// transcription slip]. An existing 101/102 mapping can still have its GL
// account changed, because that goes through the glAccountId branch (:95-98).
// [UNVERIFIED: no capture exercises it — this is a clean, cheap refusal vector
// nobody has taken: PUT with financialActivityId 101 should fail where POST
// with the same value succeeds.]
var financialActivityUpdatable = []FinancialActivity{
	FinancialActivityAssetTransfer,
	FinancialActivityLiabilityTransfer,
	FinancialActivityOpeningBalancesTransferContra,
	FinancialActivityAssetFundSource,
	FinancialActivityPayableDividends,
}

func init() {
	for a, def := range financialActivityTable {
		if _, dup := financialActivityFromValue[def.value]; dup {
			panic(fmt.Sprintf("ledger: financial activity value table is not injective at %d", def.value))
		}
		financialActivityFromValue[def.value] = a
	}
	assertPlaceholderDisjointness()
}

// StoredValue returns acc_gl_financial_activity_account.financial_activity_type.
func (a FinancialActivity) StoredValue() int32 { return financialActivityTable[a].value }

// Code returns the i18n code, e.g. "assetTransfer".
func (a FinancialActivity) Code() string { return financialActivityTable[a].code }

// RequiredClassification is the GLAccountType the mapped account must carry.
func (a FinancialActivity) RequiredClassification() Classification {
	return financialActivityTable[a].classification
}

// String reproduces the oracle's toString(): name() with underscores replaced
// by spaces [VERIFIED: AccountingConstants.java:467-470].
func (a FinancialActivity) String() string { return javaToString(financialActivityTable[a].name) }

// Name is the Java constant name with underscores intact.
func (a FinancialActivity) Name() string { return financialActivityTable[a].name }

// FinancialActivityFromValue reproduces FinancialActivity.fromInt
// [VERIFIED: AccountingConstants.java:488-498 — a HashMap on value, so it IS
// the true inverse of getValue(); contrast PortfolioProductType.fromInt, which
// is not].
func FinancialActivityFromValue(v int32) (FinancialActivity, bool) {
	a, ok := financialActivityFromValue[v]
	return a, ok
}

// IsCreatableActivityValue and IsUpdatableActivityValue expose the asymmetry.
func IsCreatableActivityValue(v int32) bool { return activityValueIn(financialActivityCreatable, v) }
func IsUpdatableActivityValue(v int32) bool { return activityValueIn(financialActivityUpdatable, v) }

func activityValueIn(list []FinancialActivity, v int32) bool {
	for _, a := range list {
		if a.StoredValue() == v {
			return true
		}
	}
	return false
}

// assertPlaceholderDisjointness is D-3 of docs/analysis/tierA-a2-behaviour.md
// §10, made executable.
//
// Resolution decides "is this an organisation-wide financial activity or a
// product placeholder?" by asking ONLY whether FinancialActivity.fromInt(id) is
// non-null [VERIFIED: AccountingProcessorHelper.java:1340-1342
// (isOrganizationAccount) called at :1187, :1274, :1301]. That works purely
// because the product placeholder codes (1..26) happen to be disjoint from
// {100,101,102,103,200,201,300}. NOTHING IN THE ORACLE ENFORCES THE
// DISJOINTNESS: adding a 27th loan placeholder is safe, and adding a 100th
// would be a SILENT TAKEOVER of ASSET_TRANSFER — every posting to that
// placeholder would go to the organisation's transfer account instead.
//
// So this port asserts it at construction. A collision is a panic at init, not
// a wrong posting at 3am.
func assertPlaceholderDisjointness() {
	activityValues := map[int32]FinancialActivity{}
	for a, def := range financialActivityTable {
		activityValues[def.value] = a
	}
	check := func(enumName string, codes []int32) {
		for _, c := range codes {
			if a, clash := activityValues[c]; clash {
				panic(fmt.Sprintf(
					"ledger: placeholder disjointness violated — %s carries code %d, which is also FinancialActivity %s; resolution would silently reroute every posting at that placeholder to the organisation account",
					enumName, c, a.Name()))
			}
		}
	}
	check("CashAccountsForLoan", codesOf(cashLoanNames))
	check("AccrualAccountsForLoan", codesOf(accrualLoanNames))
	check("CashAccountsForSavings", codesOf(cashSavingsNames))
	check("AccrualAccountsForSavings", codesOf(accrualSavingsNames))
	check("CashAccountsForShares", codesOf(cashSharesNames))
}

func codesOf[T ~int32](names map[T]string) []int32 {
	out := make([]int32, 0, len(names))
	for k := range names {
		out = append(out, int32(k))
	}
	return out
}

// FinancialActivityAccountRow is one row of
// acc_gl_financial_activity_account.
//
// The table has NO OFFICE COLUMN, despite its foreign key being named
// FK_office_mapping_acc_gl_account [VERIFIED: 0001_initial_schema.xml:98-110].
// Financial activity mappings are TENANT-GLOBAL. The uniqueness is
// single-column on financial_activity_type (inline, unnamed, :106-108), so
// there is exactly one GL account per activity for the whole tenant.
//
// gl_account_id is NOT NULL DEFAULT 0, which is a latent trap: 0 is not a valid
// account id, so any insert relying on the default violates the foreign key.
// This port models it as a plain int64 with no default and never writes 0.
type FinancialActivityAccountRow struct {
	ID          int64
	Activity    FinancialActivity
	GLAccountID int64
}

// FinancialActivityRepository is the STEP 0 read surface.
type FinancialActivityRepository interface {
	// FindByActivity returns the single row for an activity, or (nil, nil).
	FindByActivity(a FinancialActivity) (*FinancialActivityAccountRow, error)
}

// InMemoryFinancialActivityStore is a FinancialActivityRepository over a slice.
type InMemoryFinancialActivityStore struct {
	Rows []FinancialActivityAccountRow
}

// FindByActivity reproduces
// FinancialActivityAccountRepository.findByFinancialActivityType
// [VERIFIED: FinancialActivityAccountRepository.java:29-30]. The query returns
// a SINGLE entity, so a duplicate raises a non-unique-result error rather than
// picking one — uniqueness is enforced only by the DDL constraint, and the
// write service does no pre-check, catching the integrity violation instead
// [VERIFIED: FinancialActivityAccountWritePlatformServiceImpl.java:142-153].
func (s *InMemoryFinancialActivityStore) FindByActivity(a FinancialActivity) (*FinancialActivityAccountRow, error) {
	var found []FinancialActivityAccountRow
	for _, r := range s.Rows {
		if r.Activity == a {
			found = append(found, r)
		}
	}
	switch len(found) {
	case 0:
		return nil, nil
	case 1:
		row := found[0]
		return &row, nil
	default:
		return nil, newErr(ErrNonUniqueMappingResult, "",
			"More than one result was returned from Query.getSingleResult()")
	}
}

// ValidateFinancialActivityAccountCreate reproduces the CREATE validations that
// this slice owns: the activity must be one of the seven creatable values, and
// the GL account's classification must equal the activity's required type.
//
// It does NOT check usage. A HEADER account is accepted
// [OBSERVED: A2-fin-106-header-account — POST with GL account 15 (30000
// Equity, HEADER per A2-150-db-final-state.txt) for activity 300, HTTP 200,
// resourceId 4]. A port that added a detail-only rule would refuse input the
// oracle accepts.
func ValidateFinancialActivityAccountCreate(activityValue int32, account *GLAccount) error {
	if !IsCreatableActivityValue(activityValue) {
		return newErr(ErrValidation, "A2-fin-104-unknown-activity",
			"The parameter `financialActivityId` must be one of [ 100, 200, 101, 102, 300, 103, 201 ] .")
	}
	if account == nil {
		return newErr(ErrGLAccountNotFound, "A2-fin-105-missing-account",
			"General Ledger account with identifier does not exist ")
	}
	activity, _ := FinancialActivityFromValue(activityValue)
	if want := activity.RequiredClassification(); account.Classification != want {
		return newErr(ErrFinancialActivityAccountInvalid, "A2-fin-103-wrong-account-type",
			"Financial Activity '%s' with Id :%d' can only be associated with a Ledger Account of Type %s the provided Ledger Account '%s(%s)'  does not of the required type",
			activity.Code(), activityValue, want.Code(), account.Name, account.GLCode)
	}
	return nil
}

// ValidateFinancialActivityAccountUpdate is the UPDATE counterpart. The ONLY
// difference from create is the shorter allowed list — see
// financialActivityUpdatable.
func ValidateFinancialActivityAccountUpdate(activityValue int32, account *GLAccount) error {
	if !IsUpdatableActivityValue(activityValue) {
		return newErr(ErrValidation, "",
			"The parameter `financialActivityId` must be one of [ 100, 200, 300, 103, 201 ] .")
	}
	return ValidateFinancialActivityAccountCreate(activityValue, account)
}
