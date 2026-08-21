package ledger

import "fmt"

// THE MAPPING RESOLUTION ORDER.
//
// This is the highest-value thing in the slice: which single GL account a
// posting hits. The oracle implements it FOUR TIMES — loan, working-capital
// loan, savings, shares — in AccountingProcessorHelper.java, with THREE
// different miss behaviours and THREE different charge-precedence chains, plus
// a fifth partial copy in InvestorAccountingHelper.java. A single parameterised
// resolver is the obvious Go shape AND UNIFYING THEM CHANGES BEHAVIOUR, so this
// file keeps them separate and states each divergence at the site.
//
// [VERIFIED: every algorithm below was re-derived from
// fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/
// service/AccountingProcessorHelper.java at the pinned sha by this worker,
// reading the methods end to end — :1185-1216 (loan product), :1010-1029
// (working-capital loan), :1271-1296 (savings product), :1298-1320 (shares
// product), :1218-1238 (loan charge), :1240-1269 (savings charge), :1322-1338
// (shares charge), :1340-1342 (isOrganizationAccount).]
//
// WHAT RESOLUTION NEVER READS, established by reading the methods end to end:
// GLAccount.disabled (a disabled account still receives postings if a mapping
// points at it), GLAccount.usage (a HEADER account is a valid posting target —
// OBSERVED: capture A2-091b disbursed loan 4 on product 24, whose
// LOAN_PORTFOLIO slot maps to GL account 1 "Assets", account_usage 2 = HEADER,
// and A2-150-db-final-state.txt shows the resulting journal entry id 6 posted
// to account 1), GLAccount.manualEntriesAllowed, the hierarchy or parent (there
// is NO roll-up, NO fallback to a parent account and NO inheritance of any
// kind), the office (financial activity mappings are tenant-global), and any
// fund (acc_product_mapping HAS NO FUND COLUMN — the only "fund source"
// concept is a placeholder, which is an account role, not a fund entity).

// ChargeRepository is the read surface the SAVINGS charge path needs, and only
// it. It exists because the savings charge chain has a precedence level the
// loan and shares chains do not: the GL account hung off the m_charge row
// itself OUTRANKS every mapping [VERIFIED: AccountingProcessorHelper.java:1255-1258].
type ChargeRepository interface {
	// ChargeAccountID returns m_charge.income_or_liability_account_id for a
	// charge, or nil when the charge carries no account. found is false when
	// the charge does not exist, which the oracle turns into a not-found
	// exception (findOneWithNotFoundDetection).
	ChargeAccountID(chargeID int64) (accountID *int64, found bool)
}

// GLAccountRepository resolves an account id to the account itself.
type GLAccountRepository interface {
	AccountByID(id int64) (*GLAccount, bool)
}

// Resolver answers "which GL account does this posting hit?".
//
// Charges is optional and is consulted ONLY by ResolveSavingsCharge. A nil
// Charges with a savings charge resolution is a programming error and is
// reported as such rather than silently skipping the precedence level — a
// silently-skipped precedence level is a wrong account, not a missing feature.
type Resolver struct {
	Mappings           MappingRepository
	FinancialActivities FinancialActivityRepository
	Accounts           GLAccountRepository
	Charges            ChargeRepository
}

// resolveOrganisationAccount is STEP 0, shared verbatim by the loan, savings
// and shares PRODUCT paths (and absent from the working-capital-loan path).
//
// If the placeholder code is one of the seven FinancialActivity values, the
// account comes from acc_gl_financial_activity_account keyed on the activity
// ALONE: productID and paymentTypeID are IGNORED on this branch
// [VERIFIED: AccountingProcessorHelper.java:1187-1190].
//
// handled is false when the code is not a financial activity, in which case the
// caller proceeds to STEP 1.
func (r *Resolver) resolveOrganisationAccount(code int32) (account *GLAccount, handled bool, err error) {
	activity, isActivity := FinancialActivityFromValue(code)
	if !isActivity {
		return nil, false, nil
	}
	row, err := r.FinancialActivities.FindByActivity(activity)
	if err != nil {
		return nil, true, err
	}
	if row == nil {
		return nil, true, newErr(ErrFinancialActivityAccountNotFound, "",
			"Financial Activity Account with Financial Activity Type %d does not exist", code)
	}
	acct, ok := r.Accounts.AccountByID(row.GLAccountID)
	if !ok {
		return nil, true, newErr(ErrGLAccountNotFound, "",
			"General Ledger account with identifier %d does not exist ", row.GLAccountID)
	}
	return acct, true, nil
}

func (r *Resolver) accountOfRow(row *MappingRow) (*GLAccount, error) {
	if row.GLAccountID == nil {
		// The entity permits a NULL gl_account_id. The oracle would
		// dereference it; this port reports it.
		return nil, newErr(ErrMappingNilDereference, "",
			"acc_product_mapping row %d has a NULL gl_account_id", row.ID)
	}
	acct, ok := r.Accounts.AccountByID(*row.GLAccountID)
	if !ok {
		return nil, newErr(ErrGLAccountNotFound, "",
			"General Ledger account with identifier %d does not exist ", *row.GLAccountID)
	}
	return acct, nil
}

// ResolveOrganisationAccount is STEP 0 as its own entry point.
//
// WHY IT IS A SEPARATE ENTRY POINT, AND WHAT THAT CHANGES. In the oracle,
// STEP 0 and STEP 1 share ONE untyped `accountMappingTypeId` int, and which
// branch runs is decided at runtime by asking whether
// FinancialActivity.fromInt(id) is non-null [VERIFIED:
// AccountingProcessorHelper.java:1187 calling :1340-1342]. That is reachable
// from a loan posting: CashBasedAccountingProcessorForLoan.java:469 passes
// FinancialActivity.ASSET_TRANSFER.getValue() straight into
// createCreditJournalEntryForLoan, which reaches
// getLinkedGLAccountForLoanProduct [VERIFIED: this worker's own grep of the
// callers].
//
// The oracle's single parameter is safe ONLY because the two integer spaces
// happen not to overlap, and NOTHING ENFORCES THAT (see
// assertPlaceholderDisjointness). This port splits the two, so the ambiguity
// cannot exist at a call site at all. A caller holding a raw integer — a
// port of one of the processors — uses ClassifyLoanPlaceholder to choose,
// which reproduces the oracle's decision exactly.
func (r *Resolver) ResolveOrganisationAccount(a FinancialActivity) (*GLAccount, error) {
	acct, _, err := r.resolveOrganisationAccount(a.StoredValue())
	return acct, err
}

// ClassifyLoanPlaceholder reproduces isOrganizationAccount for a caller that
// holds the oracle's untyped integer.
//
// rule is required for the slot arm, because of trap 2: codes 22, 24 and 25
// name different placeholders under cash and accrual, and 7/8/9 exist only
// under accrual.
func ClassifyLoanPlaceholder(code int32, rule AccountingRule) (activity FinancialActivity, isOrganisation bool, slot Slot, ok bool) {
	if a, isActivity := FinancialActivityFromValue(code); isActivity {
		return a, true, nil, true
	}
	if rule.IsAccrual() {
		s, found := AccrualLoanSlotFromCode(code)
		return 0, false, s, found
	}
	s, found := CashLoanSlotFromCode(code)
	return 0, false, s, found
}

// ResolveLoanProductAccount is getLinkedGLAccountForLoanProduct
// [VERIFIED: AccountingProcessorHelper.java:1185-1216].
//
//	STEP 0  financial activity wins outright, ignoring product and payment type
//	STEP 1  the CORE row: (product_id, product_type=LOAN, financial_account_type)
//	        with ALL SIX discriminators NULL
//	STEP 2  ONLY for the fund-source placeholder (code 1), a payment-type row
//	        REPLACES the core row if one exists; a non-existent payment-specific
//	        row silently leaves the core row in place
//	STEP 3  a miss is ProductToGLAccountMappingNotFoundException
//
// slot is typed, so a caller cannot pass a placeholder from another family or
// a bare integer. Both loan enums are accepted because both are stored under
// product_type = LOAN; that is exactly the collision trap 2 describes, and it
// is why the SLOT, not an int, is the parameter.
//
// GRADED against captures A2-084 (product 22, paymentTypeId 1 -> GL 16 via the
// override), A2-085 (product 22, paymentTypeId 2 -> GL 2, no override row),
// A2-224 and A2-225 (product 46, CHARGE_OFF_EXPENSE and GOODWILL_CREDIT ->
// 404), A2-086 (product 27, duplicate override rows -> non-unique result).
func (r *Resolver) ResolveLoanProductAccount(productID int64, slot Slot, paymentTypeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductLoan {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveLoanProductAccount called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveProductAccount(productID, ProductLoan, slot, paymentTypeID,
		true /* STEP 0 present */, false /* STEP 2 requires non-nil payment type */, true /* typed miss */)
}

// ResolveWorkingCapitalLoanProductAccount is
// getLinkedGLAccountForWorkingCapitalLoanProduct
// [VERIFIED: AccountingProcessorHelper.java:1010-1029].
//
// TWO DIVERGENCES from the loan path, both real and both preserved:
//   - THERE IS NO STEP 0. This path never consults financial activity accounts,
//     so placeholder code 100 on a working-capital loan is looked up as an
//     ordinary product placeholder and misses.
//   - STEP 2 additionally requires paymentTypeID != nil (:1015), which the loan
//     path does not. That makes the contested null-payment-type question
//     (see NullPaymentTypePolicy) unreachable on this path.
//
// [UNVERIFIED: no capture exercises the working-capital-loan path — the tenant
// has no working-capital-loan product.]
func (r *Resolver) ResolveWorkingCapitalLoanProductAccount(productID int64, slot Slot, paymentTypeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductLoan {
		// The oracle passes CashAccountsForLoan values here too — the enum is
		// the LOAN one; only the product_type used as the query key differs
		// [VERIFIED: :1012-1013 keys on
		// PortfolioProductType.WORKING_CAPITAL_LOAN.getValue()].
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveWorkingCapitalLoanProductAccount called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveProductAccount(productID, ProductWorkingCapitalLoan, slot, paymentTypeID,
		false /* NO STEP 0 */, true /* STEP 2 requires non-nil payment type */, true /* typed miss */)
}

// ResolveSavingsProductAccount is getLinkedGLAccountForSavingsProduct
// [VERIFIED: AccountingProcessorHelper.java:1271-1296].
//
// DIVERGENCE: STEP 3 DOES NOT EXIST. The oracle calls
// accountMapping.getGlAccount() with no null check (:1293), so a missing
// mapping surfaces as a NullPointerException / HTTP 500, NOT as
// error.msg.productToAccountMapping.not.found. This port returns
// ErrMappingNilDereference and records that the status code differs.
//
// Savings/deposit code is ported and NOT activated: the tenant licence is NBFI
// (ББСБ) and deposit-taking is prohibited (Law on Non-Banking Financial
// Activities Art. 12.1.3 / 12.1.4). This function is a pure value computation
// and exposes no endpoint.
func (r *Resolver) ResolveSavingsProductAccount(productID int64, slot Slot, paymentTypeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductSaving {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveSavingsProductAccount called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveProductAccount(productID, ProductSaving, slot, paymentTypeID,
		true, false, false /* NO typed miss */)
}

// ResolveShareProductAccount is getLinkedGLAccountForShareProduct
// [VERIFIED: AccountingProcessorHelper.java:1298-1320]. Same shape as savings:
// STEP 0 present, STEP 2 gated on SHARES_REFERENCE (code 1), and NO null check
// at :1317.
func (r *Resolver) ResolveShareProductAccount(productID int64, slot Slot, paymentTypeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductShares {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveShareProductAccount called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveProductAccount(productID, ProductShares, slot, paymentTypeID,
		true, false, false)
}

// resolveProductAccount carries the shape the four PRODUCT paths share. The
// three booleans are the three places they differ, and they are named at every
// call site rather than defaulted, so a future edit cannot make one path
// silently adopt another's behaviour.
func (r *Resolver) resolveProductAccount(
	productID int64,
	keyType PortfolioProductType,
	slot Slot,
	paymentTypeID *int64,
	step0Present bool,
	step2RequiresPaymentType bool,
	typedMiss bool,
) (*GLAccount, error) {
	code := slot.Code()

	if step0Present {
		acct, handled, err := r.resolveOrganisationAccount(code)
		if handled {
			return acct, err
		}
	}

	mapping, err := r.Mappings.FindCoreProductToFinAccountMapping(productID, keyType.StoredValue(), code)
	if err != nil {
		return nil, err
	}

	if slot.IsFamilyReferenceSlot() && !(step2RequiresPaymentType && paymentTypeID == nil) {
		override, err := r.Mappings.FindByPaymentType(productID, keyType.StoredValue(), code, paymentTypeID)
		if err != nil {
			return nil, err
		}
		if override != nil {
			mapping = override
		}
	}

	if mapping == nil {
		if typedMiss {
			return nil, r.mappingNotFound(keyType, productID, code)
		}
		return nil, newErr(ErrMappingNilDereference, "",
			"no acc_product_mapping row for product %d (%s) at placeholder %d; the reference oracle raises a NullPointerException here, not a typed refusal",
			productID, keyType, code)
	}
	return r.accountOfRow(mapping)
}

// mappingNotFound builds the ProductToGLAccountMappingNotFoundException.
//
// A DEFECT IN THE ORACLE IS REPRODUCED HERE DELIBERATELY. The loan path renders
// the placeholder name through AccrualAccountsForLoan ALWAYS, even for a
// cash-based product [VERIFIED: AccountingProcessorHelper.java:1208-1211], and
// the working-capital-loan path renders it through CashAccountsForLoan always
// [VERIFIED: :1024-1027]. Because the two enums are not co-extensive, each has
// codes the other lacks: AccrualAccountsForLoan has no 26, so a cash product
// missing its PENALTIES_RECEIVABLE mapping makes the ORACLE throw a
// NullPointerException from inside the error path instead of the intended
// not-found; symmetrically the working-capital path would NPE on 7, 8 or 9.
//
// [UNVERIFIED: reachability of either NPE. It needs a product with a missing
// mapping at a placeholder absent from the OTHER enum, and no capture does
// that. The rendering itself IS graded: A2-224 and A2-225 are cash-based
// product 46 and their messages read "CHARGE OFF EXPENSE" and "GOODWILL
// CREDIT", codes 16 and 13, which both enums share and both render identically
// — so those two captures confirm the message SHAPE and cannot discriminate
// which enum rendered it.]
// THE ONE PLACE THIS PORT DELIBERATELY DIVERGES, and it diverges only where the
// oracle CANNOT produce a message at all: when the rendering enum has no member
// at that code, the oracle's .toString() is called on a null and the client gets
// a NullPointerException instead of a refusal. This port falls back to the other
// loan enum's name and still returns the typed refusal. Everywhere the oracle
// CAN render, this port renders the identical string, including where the
// oracle's choice of enum is wrong.
//
// Both names are carried: Message is oracle-faithful, ApplicableSlotName is the
// truth, so a log or an operator can see the difference without the wire
// contract moving.
func (r *Resolver) mappingNotFound(keyType PortfolioProductType, productID int64, code int32) error {
	var rendered, applicable string
	cash, haveCash := CashLoanSlotFromCode(code)
	accrual, haveAccrual := AccrualLoanSlotFromCode(code)

	switch keyType {
	case ProductWorkingCapitalLoan:
		// [VERIFIED: AccountingProcessorHelper.java:1024-1027 renders through
		// CashAccountsForLoan, which has no 7, 8 or 9.]
		applicable = fallbackName(haveCash, cash, haveAccrual, accrual, code)
		if haveCash {
			rendered = cash.String()
		} else {
			rendered = applicable
		}
	default:
		// [VERIFIED: AccountingProcessorHelper.java:1208-1211 renders through
		// AccrualAccountsForLoan ALWAYS, even for a cash-based product, and
		// AccrualAccountsForLoan has no 26.]
		applicable = fallbackName(haveAccrual, accrual, haveCash, cash, code)
		if haveAccrual {
			rendered = accrual.String()
		} else {
			rendered = applicable
		}
	}

	err := newErr(ErrProductToGLAccountMappingNotFound, "A2-224-chargeoff-unmapped",
		"Mapping for product of type %s with Id %d does not exist for an account of type %s",
		keyType, productID, rendered)
	err.ApplicableSlotName = applicable
	return err
}

func fallbackName(havePrimary bool, primary Slot, haveOther bool, other Slot, code int32) string {
	if havePrimary {
		return primary.String()
	}
	if haveOther {
		return other.String()
	}
	return fmt.Sprintf("PLACEHOLDER %d", code)
}

// ResolveLoanCharge is getLinkedGLAccountForLoanCharges
// [VERIFIED: AccountingProcessorHelper.java:1218-1238].
//
//	core row; then IF chargeID != nil a charge-specific row for ANY placeholder
//	replaces it; then getGlAccount() WITH NO NULL CHECK (:1237).
//
// Note there is NO STEP 0 on any charge path and no payment-type override.
func (r *Resolver) ResolveLoanCharge(productID int64, slot Slot, chargeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductLoan {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveLoanCharge called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveChargeAccount(productID, ProductLoan, slot, chargeID, false)
}

// ResolveShareCharge is getLinkedGLAccountForShareCharges
// [VERIFIED: AccountingProcessorHelper.java:1322-1338].
//
// DIVERGENCE from the loan charge path: the charge-specific lookup runs
// UNCONDITIONALLY — there is no `chargeId != null` guard (:1331-1336). Under
// the JPQL `mapping.charge.id = :chargeId` a null argument matches nothing, so
// the observable effect is the same; the divergence is preserved because it is
// the kind of difference that stops being harmless the moment the query changes.
func (r *Resolver) ResolveShareCharge(productID int64, slot Slot, chargeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductShares {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveShareCharge called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	return r.resolveChargeAccount(productID, ProductShares, slot, chargeID, true)
}

func (r *Resolver) resolveChargeAccount(productID int64, keyType PortfolioProductType, slot Slot, chargeID *int64, unconditional bool) (*GLAccount, error) {
	mapping, err := r.Mappings.FindCoreProductToFinAccountMapping(productID, keyType.StoredValue(), slot.Code())
	if err != nil {
		return nil, err
	}
	if unconditional || chargeID != nil {
		specific, err := r.Mappings.FindByCharge(productID, keyType.StoredValue(), slot.Code(), chargeID)
		if err != nil {
			return nil, err
		}
		if specific != nil {
			mapping = specific
		}
	}
	if mapping == nil {
		return nil, newErr(ErrMappingNilDereference, "",
			"no acc_product_mapping row for product %d (%s) at charge placeholder %d; the reference oracle raises a NullPointerException here",
			productID, keyType, slot.Code())
	}
	return r.accountOfRow(mapping)
}

// ResolveSavingsCharge is getLinkedGLAccountForSavingsCharges
// [VERIFIED: AccountingProcessorHelper.java:1240-1269].
//
// THE SAVINGS CHARGE PATH HAS A PRECEDENCE LEVEL THE OTHER TWO DO NOT HAVE.
// For placeholder codes 4 and 5 it FIRST reads the GL account hung off the
// m_charge row itself and, if non-null, RETURNS IT IMMEDIATELY, outranking
// every mapping (:1255-1258). Neither the loan nor the shares path consults it.
// So "which income account does this fee credit?" is answered by three
// different precedence chains depending on the product family, and unifying
// them changes behaviour.
//
// The gate at :1253-1254 mixes enum families in one condition —
// CashAccountsForSavings.INCOME_FROM_FEES (4) OR
// CashAccountsForLoan.INCOME_FROM_PENALTIES (5) — and is correct only by the
// coincidence that CashAccountsForSavings.INCOME_FROM_PENALTIES is also 5. The
// in-source comment at :1251 ("Vishwas TODO: remove this condition as it should
// always be true") shows it was not meant to be selective. This port writes the
// condition as the SAVINGS codes 4 and 5, which is numerically identical and
// does not import a loan constant into a savings decision.
//
// The oracle dereferences chargeID with no null guard inside that branch
// (:1255 calls findOneWithNotFoundDetection(chargeId) unconditionally), unlike
// the loan path's chargeId != nil guard at :1229. [UNVERIFIED: what the oracle
// does when that branch is reached with a null chargeId — not traced, not
// probed.] This port returns a typed error rather than dereferencing nil.
//
// [UNVERIFIED end to end: no capture exercises any savings resolution — the
// tenant has no savings product, which is consistent with the NBFI licence.]
func (r *Resolver) ResolveSavingsCharge(productID int64, slot Slot, chargeID *int64) (*GLAccount, error) {
	if slot.ProductFamily() != ProductSaving {
		return nil, newErr(ErrMappingNilDereference, "",
			"ResolveSavingsCharge called with a %s slot (%s)", slot.ProductFamily(), slot.Name())
	}
	mapping, err := r.Mappings.FindCoreProductToFinAccountMapping(productID, ProductSaving.StoredValue(), slot.Code())
	if err != nil {
		return nil, err
	}
	if code := slot.Code(); code == CashSavingsIncomeFromFees.Code() || code == CashSavingsIncomeFromPenalties.Code() {
		if r.Charges == nil {
			return nil, newErr(ErrMappingNilDereference, "",
				"savings charge resolution at placeholder %d needs the charge repository: m_charge's own GL account outranks every mapping here", code)
		}
		if chargeID == nil {
			return nil, newErr(ErrMappingNilDereference, "",
				"savings charge resolution at placeholder %d reached with a nil charge id; the reference oracle dereferences it (AccountingProcessorHelper.java:1255)", code)
		}
		accountID, found := r.Charges.ChargeAccountID(*chargeID)
		if !found {
			return nil, newErr(ErrGLAccountNotFound, "",
				"Charge with identifier %d does not exist", *chargeID)
		}
		if accountID != nil {
			acct, ok := r.Accounts.AccountByID(*accountID)
			if !ok {
				return nil, newErr(ErrGLAccountNotFound, "",
					"General Ledger account with identifier %d does not exist ", *accountID)
			}
			return acct, nil
		}
		specific, err := r.Mappings.FindByCharge(productID, ProductSaving.StoredValue(), code, chargeID)
		if err != nil {
			return nil, err
		}
		if specific != nil {
			mapping = specific
		}
	}
	if mapping == nil {
		return nil, newErr(ErrMappingNilDereference, "",
			"no acc_product_mapping row for savings product %d at charge placeholder %d; the reference oracle raises a NullPointerException here",
			productID, slot.Code())
	}
	return r.accountOfRow(mapping)
}

// ReasonLookup is the FIFTH lookup shape: charge-off reasons, write-off reasons
// and the two classification dimensions.
//
// These do NOT go through the core row at all. Each keys on
// (product_id, product_type, <code_value_id>) and — critically — DOES NOT
// FILTER ON financial_account_type [VERIFIED:
// ProductToGLAccountMappingRepository.java:76-78, :109-111, :101-103, :105-107,
// reached from AccountingProcessorHelper.java:194, :199, :205, :207]. They
// return NULL on a miss with no exception; the null-handling is the caller's,
// outside this slice.
//
// [UNVERIFIED: what the oracle's callers do with a nil return — those callers
// are outside slice A2 and this worker did not trace them. So this port returns
// (nil, nil) and refuses to invent a policy.]
type ReasonLookup struct{ r *Resolver }

// Reasons exposes the fifth lookup shape.
func (r *Resolver) Reasons() ReasonLookup { return ReasonLookup{r: r} }

func (l ReasonLookup) ChargeOffReason(productID int64, keyType PortfolioProductType, reasonID int64) (*GLAccount, error) {
	return l.account(l.r.Mappings.FindChargeOffReasonMapping(productID, keyType.StoredValue(), reasonID))
}

func (l ReasonLookup) WriteOffReason(productID int64, keyType PortfolioProductType, reasonID int64) (*GLAccount, error) {
	return l.account(l.r.Mappings.FindWriteOffReasonMapping(productID, keyType.StoredValue(), reasonID))
}

func (l ReasonLookup) CapitalizedIncomeClassification(productID int64, keyType PortfolioProductType, classificationID int64) (*GLAccount, error) {
	return l.account(l.r.Mappings.FindCapitalizedIncomeClassificationMapping(productID, keyType.StoredValue(), classificationID))
}

func (l ReasonLookup) BuydownFeeClassification(productID int64, keyType PortfolioProductType, classificationID int64) (*GLAccount, error) {
	return l.account(l.r.Mappings.FindBuydownFeeClassificationMapping(productID, keyType.StoredValue(), classificationID))
}

func (l ReasonLookup) account(row *MappingRow, err error) (*GLAccount, error) {
	if err != nil || row == nil {
		return nil, err
	}
	return l.r.accountOfRow(row)
}

// InMemoryAccountStore is a GLAccountRepository over a slice.
type InMemoryAccountStore struct {
	Accounts []GLAccount
}

func (s *InMemoryAccountStore) AccountByID(id int64) (*GLAccount, bool) {
	for i := range s.Accounts {
		if s.Accounts[i].ID == id {
			a := s.Accounts[i]
			return &a, true
		}
	}
	return nil, false
}
