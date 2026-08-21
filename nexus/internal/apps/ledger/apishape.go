package ledger

import "fmt"

// THE WRITE SHAPE AND THE READ SHAPE DIFFER FOR EVERY SINGLE SLOT.
//
// This was measured at the frozen adapter contract for the first time by task
// A2-7: before it, the loan-product mapping had been POSTed eleven times and
// READ ZERO TIMES in the whole corpus. A port that assumes the read mirrors the
// write is wrong on every slot.
//
// Four facts, all observed:
//
//  1. The write parameter and the read key differ for every slot:
//     fundSourceAccountId -> fundSourceAccount, writeOffAccountId ->
//     writeOffAccount, and so on for all thirteen
//     [VERIFIED: LoanProductAccountingParams (AccountingConstants.java:156-198)
//     against LoanProductAccountingDataParams (:216-245); OBSERVED: request
//     req/a2-7-prod-210-cash-nine-mandatory.json against response
//     out/A2-211-read-product-nine-mandatory.json].
//  2. The write takes a bare integer account id; the read returns an OBJECT
//     {id, name, glCode} and NOTHING ELSE — no type, no usage, no disabled, no
//     manualEntriesAllowed. A consumer of the product read CANNOT tell an
//     INCOME account from an ASSET one without a second call to
//     /glaccounts/{id} [OBSERVED: A2-211, A2-212, A2-213].
//  3. AN UNSET MAPPING FIELD IS ABSENT FROM THE READ. Scalar and collection
//     alike. NOTHING IS EVER null. [VERIFIED by this worker against the raw
//     bytes of out/A2-211-read-product-nine-mandatory.json: the literal string
//     "null" occurs ZERO times in the whole 7,489-byte response; the keys
//     paymentChannelToFundSourceMappings, feeToIncomeAccountMappings and
//     penaltyToIncomeAccountMappings occur ZERO times each; no top-level key
//     has a JSON null value. The positive control is A2-212, which HAS one
//     payment-channel override and therefore DOES carry
//     paymentChannelToFundSourceMappings — as an array, and still with no
//     "null" anywhere in the file. A2-213 likewise carries the key not at all.]
//
//     THIS CORRECTS AN INHERITED FABRICATION, recorded here so it cannot be
//     re-inherited. The A2-7 handoff prints those three keys with the value
//     null inside a JSON block attributed to capture A2-211, at
//     .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-7.md:210-212,
//     and builds its point (3) — "the collection-valued mapping fields behave
//     the opposite way" — on them. The lines are not in the capture. A Go type
//     that emitted those three keys as null would ship three keys the reference
//     oracle never emits: in Go that is exactly the difference between a field
//     with omitempty and one without, so it is a one-character contract defect
//     with no compiler signal. The rule is UNIFORM and SIMPLER than the
//     fabrication claimed.
//  4. The payment-channel override is stored in the SAME TABLE as the default,
//     discriminated by a nullable payment_type column, and the contract SPLITS
//     THEM INTO TWO DIFFERENTLY-SHAPED PLACES: the default stays in
//     accountingMappings.fundSourceAccount while the overrides become a list of
//     {paymentType, fundSourceAccount} pairs [OBSERVED: A2-212 — product 22's
//     accountingMappings.fundSourceAccount is GL 2 and its
//     paymentChannelToFundSourceMappings is [{paymentType 1, GL 16}], matching
//     the two acc_product_mapping rows in A2-072-db-product-mapping-rows.txt].
//
// AND THE GL ACCOUNT READ IS ASYMMETRIC THE OTHER WAY: it returns type and
// usage as {id, code, value} objects while the write takes bare integers
// [OBSERVED: A2-201, A2-012 against req/gl-010..gl-033.json].

// SlotAPIShape is one row of the loan-product accounting-mapping contract.
type SlotAPIShape struct {
	// WriteParam is the POST/PUT body key, e.g. "fundSourceAccountId".
	WriteParam string
	// ReadKey is the key inside accountingMappings on GET, e.g.
	// "fundSourceAccount". It is NEVER equal to WriteParam.
	ReadKey string
	// AllowedClassifications is the set the write-side type check accepts. An
	// empty slice means the write path applies NO type check at all.
	AllowedClassifications []Classification
	// MandatoryAtCreate is true where the create validator marks the parameter
	// notNull(); false where it marks it ignoreIfNull().
	MandatoryAtCreate bool
}

// loanSlotShapeByCode maps a LOAN placeholder code to its contract shape.
//
// It is keyed by CODE and by ACCOUNTING RULE, never by code alone, because of
// trap 2: code 22, 24 and 25 mean different things under cash and accrual, and
// the accrual-only codes 7, 8, 9 do not exist under cash. Two maps, not one.
var (
	cashLoanSlotShape = map[CashLoanSlot]SlotAPIShape{
		// FUND_SOURCE accepts ASSET *OR* LIABILITY, not ASSET alone
		// [VERIFIED: ProductToGLAccountMappingHelper.java:62 ASSET_LIABILITY_TYPES,
		// used by saveLoanToAssetOrLiabilityAccountMapping; OBSERVED verbatim in
		// A2-214 and A2-prod-063: "the expected account type was one among
		// accountType.asset or accountType.liability"].
		CashLoanFundSource:        {"fundSourceAccountId", "fundSourceAccount", []Classification{ClassificationAsset, ClassificationLiability}, true},
		CashLoanLoanPortfolio:     {"loanPortfolioAccountId", "loanPortfolioAccount", []Classification{ClassificationAsset}, true},
		CashLoanTransfersSuspense: {"transfersInSuspenseAccountId", "transfersInSuspenseAccount", []Classification{ClassificationAsset}, true},

		CashLoanInterestOnLoans:                  {"interestOnLoanAccountId", "interestOnLoanAccount", []Classification{ClassificationIncome}, true},
		CashLoanIncomeFromFees:                   {"incomeFromFeeAccountId", "incomeFromFeeAccount", []Classification{ClassificationIncome}, true},
		CashLoanIncomeFromPenalties:              {"incomeFromPenaltyAccountId", "incomeFromPenaltyAccount", []Classification{ClassificationIncome}, true},
		CashLoanIncomeFromRecovery:               {"incomeFromRecoveryAccountId", "incomeFromRecoveryAccount", []Classification{ClassificationIncome}, true},
		CashLoanIncomeFromChargeOffFees:          {"incomeFromChargeOffFeesAccountId", "incomeFromChargeOffFeesAccount", []Classification{ClassificationIncome}, false},
		CashLoanIncomeFromChargeOffInterest:      {"incomeFromChargeOffInterestAccountId", "incomeFromChargeOffInterestAccount", []Classification{ClassificationIncome}, false},
		CashLoanIncomeFromChargeOffPenalty:       {"incomeFromChargeOffPenaltyAccountId", "incomeFromChargeOffPenaltyAccount", []Classification{ClassificationIncome}, false},
		CashLoanIncomeFromGoodwillCreditInterest: {"incomeFromGoodwillCreditInterestAccountId", "incomeFromGoodwillCreditInterestAccount", []Classification{ClassificationIncome}, false},
		CashLoanIncomeFromGoodwillCreditFees:     {"incomeFromGoodwillCreditFeesAccountId", "incomeFromGoodwillCreditFeesAccount", []Classification{ClassificationIncome}, false},
		CashLoanIncomeFromGoodwillCreditPenalty:  {"incomeFromGoodwillCreditPenaltyAccountId", "incomeFromGoodwillCreditPenaltyAccount", []Classification{ClassificationIncome}, false},

		CashLoanLossesWrittenOff:      {"writeOffAccountId", "writeOffAccount", []Classification{ClassificationExpense}, true},
		CashLoanGoodwillCredit:        {"goodwillCreditAccountId", "goodwillCreditAccount", []Classification{ClassificationExpense}, false},
		CashLoanChargeOffExpense:      {"chargeOffExpenseAccountId", "chargeOffExpenseAccount", []Classification{ClassificationExpense}, false},
		CashLoanChargeOffFraudExpense: {"chargeOffFraudExpenseAccountId", "chargeOffFraudExpenseAccount", []Classification{ClassificationExpense}, false},

		CashLoanOverpayment: {"overpaymentLiabilityAccountId", "overpaymentLiabilityAccount", []Classification{ClassificationLiability}, true},

		// Codes 22..26 under CASH are NOT written by the loan-product create
		// path at all [VERIFIED: ProductToGLAccountMappingWritePlatformServiceImpl
		// .java:77-148, the whole CASH_BASED arm, contains no
		// CLASSIFICATION_INCOME, DEFERRED_INCOME_LIABILITY,
		// INCOME_FROM_DISCOUNT_FEE, FEES_RECEIVABLE or PENALTIES_RECEIVABLE
		// call]. They exist because other writers and readers use them:
		// CLASSIFICATION_INCOME (22) is the HARD-WIRED financial_account_type
		// for BOTH the capitalized-income and buy-down classification mappings
		// [VERIFIED: ProductToGLAccountMappingHelper.java:699], and
		// INCOME_FROM_DISCOUNT_FEE (24), FEES_RECEIVABLE (25) and
		// PENALTIES_RECEIVABLE (26) are read by the working-capital-loan
		// deferred-revenue processor [VERIFIED:
		// AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan
		// .java:142-144, :165-166, :188-189, :210-212, :223-224, :239-241, :485].
		//
		// AllowedClassifications is EMPTY for these, and that is a statement of
		// FACT, not a default: no create path applies a type check to them, so
		// there is nothing to reproduce. It is NOT a claim that any account
		// type is semantically appropriate. Filling these in from the constant
		// NAMES would be inventing a rule the oracle does not have.
		CashLoanClassificationIncome:    {"", "", nil, false},
		CashLoanDeferredIncomeLiability: {"deferredIncomeLiabilityAccountId", "deferredIncomeLiabilityAccount", nil, false},
		CashLoanIncomeFromDiscountFee:   {"incomeFromDiscountFeeAccountId", "incomeFromDiscountFeeAccount", nil, false},
		CashLoanFeesReceivable:          {"receivableFeeAccountId", "receivableFeeAccount", nil, false},
		CashLoanPenaltiesReceivable:     {"receivablePenaltyAccountId", "receivablePenaltyAccount", nil, false},
	}

	accrualLoanSlotShape = map[AccrualLoanSlot]SlotAPIShape{
		AccrualLoanFundSource:        {"fundSourceAccountId", "fundSourceAccount", []Classification{ClassificationAsset, ClassificationLiability}, true},
		AccrualLoanLoanPortfolio:     {"loanPortfolioAccountId", "loanPortfolioAccount", []Classification{ClassificationAsset}, true},
		AccrualLoanTransfersSuspense: {"transfersInSuspenseAccountId", "transfersInSuspenseAccount", []Classification{ClassificationAsset}, true},

		// The three receivables are ASSETS and are mandatory ONLY under accrual
		// [VERIFIED: ProductToGLAccountMappingWritePlatformServiceImpl.java:149-246
		// writes them on the accrual arm only; LoanProductDataValidator
		// validateForCreate marks them notNull() in the accrual block].
		AccrualLoanInterestReceivable:  {"receivableInterestAccountId", "receivableInterestAccount", []Classification{ClassificationAsset}, true},
		AccrualLoanFeesReceivable:      {"receivableFeeAccountId", "receivableFeeAccount", []Classification{ClassificationAsset}, true},
		AccrualLoanPenaltiesReceivable: {"receivablePenaltyAccountId", "receivablePenaltyAccount", []Classification{ClassificationAsset}, true},

		AccrualLoanInterestOnLoans:                  {"interestOnLoanAccountId", "interestOnLoanAccount", []Classification{ClassificationIncome}, true},
		AccrualLoanIncomeFromFees:                   {"incomeFromFeeAccountId", "incomeFromFeeAccount", []Classification{ClassificationIncome}, true},
		AccrualLoanIncomeFromPenalties:              {"incomeFromPenaltyAccountId", "incomeFromPenaltyAccount", []Classification{ClassificationIncome}, true},
		AccrualLoanIncomeFromRecovery:               {"incomeFromRecoveryAccountId", "incomeFromRecoveryAccount", []Classification{ClassificationIncome}, true},
		AccrualLoanIncomeFromChargeOffFees:          {"incomeFromChargeOffFeesAccountId", "incomeFromChargeOffFeesAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromChargeOffInterest:      {"incomeFromChargeOffInterestAccountId", "incomeFromChargeOffInterestAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromChargeOffPenalty:       {"incomeFromChargeOffPenaltyAccountId", "incomeFromChargeOffPenaltyAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromGoodwillCreditInterest: {"incomeFromGoodwillCreditInterestAccountId", "incomeFromGoodwillCreditInterestAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromGoodwillCreditFees:     {"incomeFromGoodwillCreditFeesAccountId", "incomeFromGoodwillCreditFeesAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromGoodwillCreditPenalty:  {"incomeFromGoodwillCreditPenaltyAccountId", "incomeFromGoodwillCreditPenaltyAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromCapitalization:         {"incomeFromCapitalizationAccountId", "incomeFromCapitalizationAccount", []Classification{ClassificationIncome}, false},
		AccrualLoanIncomeFromBuyDown:                {"incomeFromBuyDownAccountId", "incomeFromBuyDownAccount", []Classification{ClassificationIncome}, false},

		AccrualLoanLossesWrittenOff:      {"writeOffAccountId", "writeOffAccount", []Classification{ClassificationExpense}, true},
		AccrualLoanGoodwillCredit:        {"goodwillCreditAccountId", "goodwillCreditAccount", []Classification{ClassificationExpense}, false},
		AccrualLoanChargeOffExpense:      {"chargeOffExpenseAccountId", "chargeOffExpenseAccount", []Classification{ClassificationExpense}, false},
		AccrualLoanChargeOffFraudExpense: {"chargeOffFraudExpenseAccountId", "chargeOffFraudExpenseAccount", []Classification{ClassificationExpense}, false},
		// BUY_DOWN_EXPENSE is written ONLY when merchantBuyDownFee is true
		// (default true) [VERIFIED:
		// ProductToGLAccountMappingWritePlatformServiceImpl.java:65-72, :224-228].
		AccrualLoanBuyDownExpense: {"buyDownExpenseAccountId", "buyDownExpenseAccount", []Classification{ClassificationExpense}, false},

		AccrualLoanOverpayment:             {"overpaymentLiabilityAccountId", "overpaymentLiabilityAccount", []Classification{ClassificationLiability}, true},
		AccrualLoanDeferredIncomeLiability: {"deferredIncomeLiabilityAccountId", "deferredIncomeLiabilityAccount", []Classification{ClassificationLiability}, false},
	}
)

// LoanSlotAPIShape returns the contract shape for a loan placeholder under a
// given accounting rule. The rule is a REQUIRED argument, not an optional one:
// asking for "the shape of code 24" without it is the trap-2 question that has
// two answers.
func LoanSlotAPIShape(code int32, rule AccountingRule) (SlotAPIShape, bool) {
	if rule.IsAccrual() {
		s, ok := accrualLoanSlotShape[AccrualLoanSlot(code)]
		return s, ok
	}
	s, ok := cashLoanSlotShape[CashLoanSlot(code)]
	return s, ok
}

// MandatoryLoanSlotsAtCreate returns the placeholder codes the product-create
// validator marks notNull() for a given accounting rule.
//
// THE RUNTIME MANDATORY SET IS NOT THIS SET, and the difference is MEASURED,
// not inferred. Task A2-7 built product 46 with exactly these nine cash slots
// and no optional ones; the product was created HTTP 200 and then
// charge-off returned 404 "does not exist for an account of type CHARGE OFF
// EXPENSE" and goodwillCredit returned 404 "... GOODWILL CREDIT"
// [OBSERVED: A2-224-chargeoff-unmapped, A2-225-goodwillcredit-unmapped]. Both
// are ignoreIfNull() at creation.
//
//	{accounts required at RUNTIME} is NOT a subset of
//	{accounts required at PRODUCT CREATION}.
//
// FINERACT WILL CREATE A PRODUCT THAT CANNOT COMPLETE EVERY POSTING PATH. This
// port models that and does not "fix" it: tightening the create validator would
// refuse products the oracle accepts and would break shadow parity on the
// tenant's existing data.
//
// [UNVERIFIED: the reverse inclusion. A2-7 proved runtime is not a subset of
// creation; it did NOT prove creation is a subset of runtime, and no finite
// probe set can — that needs a path exercising each of the nine. Five of the
// nine (INTEREST_ON_LOANS, INCOME_FROM_FEES, INCOME_FROM_PENALTIES,
// OVERPAYMENT, TRANSFERS_SUSPENSE) were never posted to, because A2-7's probes
// used a 0% rate, no charges, no overpayment and no transfer. That absence is a
// fact about the probe set, not about the accounts.]
func MandatoryLoanSlotsAtCreate(rule AccountingRule) []int32 {
	var out []int32
	if rule.IsAccrual() {
		for s, shape := range accrualLoanSlotShape {
			if shape.MandatoryAtCreate {
				out = append(out, int32(s))
			}
		}
	} else {
		for s, shape := range cashLoanSlotShape {
			if shape.MandatoryAtCreate {
				out = append(out, int32(s))
			}
		}
	}
	sortInt32(out)
	return out
}

func sortInt32(xs []int32) {
	for i := 1; i < len(xs); i++ {
		for j := i; j > 0 && xs[j] < xs[j-1]; j-- {
			xs[j], xs[j-1] = xs[j-1], xs[j]
		}
	}
}

// ValidateLoanSlotAccountType reproduces getAccountByIdAndType's classification
// check [VERIFIED: ProductToGLAccountMappingHelper.java:727-736], including the
// oracle's message text, which is user-visible.
//
// IT IS A WRITE-PATH CHECK ONLY. Nothing validates the pairing on read, and
// that is GATE G-10: the oracle currently holds five loan products (22, 23, 24,
// 27, 28) whose FUND_SOURCE slot points at GL account 2, which was retyped
// ASSET -> INCOME underneath them by A2-111 (HTTP 200). The oracle serves those
// products without complaint (A2-212, HTTP 200) and REFUSES TO RE-CREATE the
// same mapping (A2-214, HTTP 403) — and because the read exposes no type
// (fact 2 above), the read-back structurally cannot reveal it.
//
// Two consequences a port must not stumble into, stated rather than decided:
//   - A Go implementation that validates slot types ON READ, or that
//     reconstructs a product by re-POSTing its own read-back, DIVERGES from the
//     oracle on the existing tenant data.
//   - Any parity vector taken from products 22, 23, 24, 27 or 28 is built on a
//     chart in that state and must say so.
//
// Note the message's missing space after the id ("with Id 2maps to") — it is
// the oracle's own text and is reproduced verbatim, because a port that tidies
// it changes a string a client may match on.
func ValidateLoanSlotAccountType(code int32, rule AccountingRule, account *GLAccount) error {
	shape, ok := LoanSlotAPIShape(code, rule)
	if !ok {
		return fmt.Errorf("ledger: no loan slot shape for placeholder %d under %s", code, rule)
	}
	if account == nil {
		return newErr(ErrGLAccountNotFound, "A2-fin-105-missing-account",
			"General Ledger account with identifier does not exist ")
	}
	if len(shape.AllowedClassifications) == 0 {
		return nil
	}
	for _, want := range shape.AllowedClassifications {
		if account.Classification == want {
			return nil
		}
	}
	return &LedgerError{
		Code:       fmt.Sprintf("error.msg.%s.invalid.account.type", shape.WriteParam),
		HTTPStatus: 403,
		Capture:    "A2-214-create-fundsource-retyped",
		Message: fmt.Sprintf("Passed in GLAccount %s with Id %dmaps to the account %s of type %s, the expected account type was one among %s",
			shape.WriteParam, account.ID, account.Name, account.Classification,
			joinClassificationCodes(shape.AllowedClassifications)),
	}
}

func joinClassificationCodes(cs []Classification) string {
	switch len(cs) {
	case 0:
		return ""
	case 1:
		return cs[0].Code()
	default:
		out := cs[0].Code()
		for _, c := range cs[1 : len(cs)-1] {
			out += ", " + c.Code()
		}
		return out + " or " + cs[len(cs)-1].Code()
	}
}

// AccountReadObject is the {id, name, glCode} object the loan-product read
// emits for a mapped slot. It carries NO type and NO usage, by construction:
// adding them here would make the port emit a richer object than the oracle and
// break the contract.
type AccountReadObject struct {
	ID     int64  `json:"id"`
	Name   string `json:"name"`
	GLCode string `json:"glCode"`
}

// ReadObject projects an account into the product read's slot shape.
func (a GLAccount) ReadObject() AccountReadObject {
	return AccountReadObject{ID: a.ID, Name: a.Name, GLCode: a.GLCode}
}

// EnumReadObject is the {id, code, value} object the GL ACCOUNT read emits for
// type and usage — a richer shape than the product read's slot object, and the
// other half of the boundary's asymmetry.
type EnumReadObject struct {
	ID    int32  `json:"id"`
	Code  string `json:"code"`
	Value string `json:"value"`
}

// ClassificationReadObject and UsageReadObject build the GL account read's enum
// objects. [OBSERVED: A2-201 — {"id":1,"code":"accountType.asset","value":"ASSET"}
// and {"id":1,"code":"accountUsage.detail","value":"DETAIL"}]
func (c Classification) ReadObject() EnumReadObject {
	return EnumReadObject{ID: c.StoredValue(), Code: c.Code(), Value: c.String()}
}

func (u Usage) ReadObject() EnumReadObject {
	return EnumReadObject{ID: u.StoredValue(), Code: u.Code(), Value: u.String()}
}
