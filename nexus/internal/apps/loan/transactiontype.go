package loan

import "fmt"

// LoanTransactionType is m_loan_transaction.transaction_type_enum — Fineract's
// LoanTransactionType. [VERIFIED: LoanTransactionType.java:25-82]
//
// TRAP — the stored values are NOT contiguous: there is no value 11. INVALID(0)
// through ACCRUAL(10) are contiguous, then INITIATE_TRANSFER resumes at 12 and
// the sequence continues to DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT(47) with no
// further gaps. Any port that maps these with an iota and forgets the 11 gap
// shifts every transfer/refund/chargeback value by one. The explicit table
// below preserves the gap.
type LoanTransactionType int32

const (
	TransactionInvalid LoanTransactionType = iota
	TransactionDisbursement
	TransactionRepayment
	TransactionContra
	TransactionWaiveInterest
	TransactionRepaymentAtDisbursement
	TransactionWriteoff
	TransactionMarkedForRescheduling
	TransactionRecoveryRepayment
	TransactionWaiveCharges
	TransactionAccrual
	TransactionInitiateTransfer
	TransactionApproveTransfer
	TransactionWithdrawTransfer
	TransactionRejectTransfer
	TransactionRefund
	TransactionChargePayment
	TransactionRefundForActiveLoan
	TransactionIncomePosting
	TransactionCreditBalanceRefund
	TransactionMerchantIssuedRefund
	TransactionPayoutRefund
	TransactionGoodwillCredit
	TransactionChargeRefund
	TransactionChargeback
	TransactionChargeAdjustment
	TransactionChargeOff
	TransactionDownPayment
	TransactionReage
	TransactionReamortize
	TransactionInterestPaymentWaiver
	TransactionAccrualActivity
	TransactionInterestRefund
	TransactionAccrualAdjustment
	TransactionCapitalizedIncome
	TransactionCapitalizedIncomeAmortization
	TransactionCapitalizedIncomeAdjustment
	TransactionContractTermination
	TransactionCapitalizedIncomeAmortizationAdjustment
	TransactionBuyDownFee
	TransactionBuyDownFeeAdjustment
	TransactionBuyDownFeeAmortization
	TransactionBuyDownFeeAmortizationAdjustment
	TransactionDiscountFee
	TransactionDiscountFeeAmortization
	TransactionDiscountFeeAdjustment
	TransactionDiscountFeeAmortizationAdjustment
)

var loanTransactionStoredValue = map[LoanTransactionType]int32{
	TransactionInvalid:                                 0,
	TransactionDisbursement:                            1,
	TransactionRepayment:                               2,
	TransactionContra:                                  3,
	TransactionWaiveInterest:                           4,
	TransactionRepaymentAtDisbursement:                 5,
	TransactionWriteoff:                                6,
	TransactionMarkedForRescheduling:                   7,
	TransactionRecoveryRepayment:                       8,
	TransactionWaiveCharges:                            9,
	TransactionAccrual:                                 10,
	TransactionInitiateTransfer:                        12,
	TransactionApproveTransfer:                         13,
	TransactionWithdrawTransfer:                        14,
	TransactionRejectTransfer:                          15,
	TransactionRefund:                                  16,
	TransactionChargePayment:                           17,
	TransactionRefundForActiveLoan:                     18,
	TransactionIncomePosting:                           19,
	TransactionCreditBalanceRefund:                     20,
	TransactionMerchantIssuedRefund:                    21,
	TransactionPayoutRefund:                            22,
	TransactionGoodwillCredit:                          23,
	TransactionChargeRefund:                            24,
	TransactionChargeback:                              25,
	TransactionChargeAdjustment:                        26,
	TransactionChargeOff:                               27,
	TransactionDownPayment:                             28,
	TransactionReage:                                   29,
	TransactionReamortize:                              30,
	TransactionInterestPaymentWaiver:                   31,
	TransactionAccrualActivity:                         32,
	TransactionInterestRefund:                          33,
	TransactionAccrualAdjustment:                       34,
	TransactionCapitalizedIncome:                       35,
	TransactionCapitalizedIncomeAmortization:           36,
	TransactionCapitalizedIncomeAdjustment:             37,
	TransactionContractTermination:                     38,
	TransactionCapitalizedIncomeAmortizationAdjustment: 39,
	TransactionBuyDownFee:                              40,
	TransactionBuyDownFeeAdjustment:                    41,
	TransactionBuyDownFeeAmortization:                  42,
	TransactionBuyDownFeeAmortizationAdjustment:        43,
	TransactionDiscountFee:                             44,
	TransactionDiscountFeeAmortization:                 45,
	TransactionDiscountFeeAdjustment:                   46,
	TransactionDiscountFeeAmortizationAdjustment:       47,
}

var loanTransactionCode = map[LoanTransactionType]string{
	TransactionInvalid:                                 "loanTransactionType.invalid",
	TransactionDisbursement:                            "loanTransactionType.disbursement",
	TransactionRepayment:                               "loanTransactionType.repayment",
	TransactionContra:                                  "loanTransactionType.contra",
	TransactionWaiveInterest:                           "loanTransactionType.waiver",
	TransactionRepaymentAtDisbursement:                 "loanTransactionType.repaymentAtDisbursement",
	TransactionWriteoff:                                "loanTransactionType.writeOff",
	TransactionMarkedForRescheduling:                   "loanTransactionType.marked.for.rescheduling",
	TransactionRecoveryRepayment:                       "loanTransactionType.recoveryRepayment",
	TransactionWaiveCharges:                            "loanTransactionType.waiveCharges",
	TransactionAccrual:                                 "loanTransactionType.accrual",
	TransactionInitiateTransfer:                        "loanTransactionType.initiateTransfer",
	TransactionApproveTransfer:                         "loanTransactionType.approveTransfer",
	TransactionWithdrawTransfer:                        "loanTransactionType.withdrawTransfer",
	TransactionRejectTransfer:                          "loanTransactionType.rejectTransfer",
	TransactionRefund:                                  "loanTransactionType.refund",
	TransactionChargePayment:                           "loanTransactionType.chargePayment",
	TransactionRefundForActiveLoan:                     "loanTransactionType.refund",
	TransactionIncomePosting:                           "loanTransactionType.incomePosting",
	TransactionCreditBalanceRefund:                     "loanTransactionType.creditBalanceRefund",
	TransactionMerchantIssuedRefund:                    "loanTransactionType.merchantIssuedRefund",
	TransactionPayoutRefund:                            "loanTransactionType.payoutRefund",
	TransactionGoodwillCredit:                          "loanTransactionType.goodwillCredit",
	TransactionChargeRefund:                            "loanTransactionType.chargeRefund",
	TransactionChargeback:                              "loanTransactionType.chargeback",
	TransactionChargeAdjustment:                        "loanTransactionType.chargeAdjustment",
	TransactionChargeOff:                               "loanTransactionType.chargeOff",
	TransactionDownPayment:                             "loanTransactionType.downPayment",
	TransactionReage:                                   "loanTransactionType.reAge",
	TransactionReamortize:                              "loanTransactionType.reAmortize",
	TransactionInterestPaymentWaiver:                   "loanTransactionType.interestPaymentWaiver",
	TransactionAccrualActivity:                         "loanTransactionType.accrualActivity",
	TransactionInterestRefund:                          "loanTransactionType.interestRefund",
	TransactionAccrualAdjustment:                       "loanTransactionType.accrualAdjustment",
	TransactionCapitalizedIncome:                       "loanTransactionType.capitalizedIncome",
	TransactionCapitalizedIncomeAmortization:           "loanTransactionType.capitalizedIncomeAmortization",
	TransactionCapitalizedIncomeAdjustment:             "loanTransactionType.capitalizedIncomeAdjustment",
	TransactionContractTermination:                     "loanTransactionType.contractTermination",
	TransactionCapitalizedIncomeAmortizationAdjustment: "loanTransactionType.capitalizedIncomeAmortizationAdjustment",
	TransactionBuyDownFee:                              "loanTransactionType.buyDownFee",
	TransactionBuyDownFeeAdjustment:                    "loanTransactionType.buyDownFeeAdjustment",
	TransactionBuyDownFeeAmortization:                  "loanTransactionType.buyDownFeeAmortization",
	TransactionBuyDownFeeAmortizationAdjustment:        "loanTransactionType.buyDownFeeAmortizationAdjustment",
	TransactionDiscountFee:                             "loanTransactionType.discountFee",
	TransactionDiscountFeeAmortization:                 "loanTransactionType.discountFeeAmortization",
	TransactionDiscountFeeAdjustment:                   "loanTransactionType.discountFeeAdjustment",
	TransactionDiscountFeeAmortizationAdjustment:       "loanTransactionType.discountFeeAmortizationAdjustment",
}

var loanTransactionName = map[LoanTransactionType]string{
	TransactionInvalid:                                 "INVALID",
	TransactionDisbursement:                            "DISBURSEMENT",
	TransactionRepayment:                               "REPAYMENT",
	TransactionContra:                                  "CONTRA",
	TransactionWaiveInterest:                           "WAIVE_INTEREST",
	TransactionRepaymentAtDisbursement:                 "REPAYMENT_AT_DISBURSEMENT",
	TransactionWriteoff:                                "WRITEOFF",
	TransactionMarkedForRescheduling:                   "MARKED_FOR_RESCHEDULING",
	TransactionRecoveryRepayment:                       "RECOVERY_REPAYMENT",
	TransactionWaiveCharges:                            "WAIVE_CHARGES",
	TransactionAccrual:                                 "ACCRUAL",
	TransactionInitiateTransfer:                        "INITIATE_TRANSFER",
	TransactionApproveTransfer:                         "APPROVE_TRANSFER",
	TransactionWithdrawTransfer:                        "WITHDRAW_TRANSFER",
	TransactionRejectTransfer:                          "REJECT_TRANSFER",
	TransactionRefund:                                  "REFUND",
	TransactionChargePayment:                           "CHARGE_PAYMENT",
	TransactionRefundForActiveLoan:                     "REFUND_FOR_ACTIVE_LOAN",
	TransactionIncomePosting:                           "INCOME_POSTING",
	TransactionCreditBalanceRefund:                     "CREDIT_BALANCE_REFUND",
	TransactionMerchantIssuedRefund:                    "MERCHANT_ISSUED_REFUND",
	TransactionPayoutRefund:                            "PAYOUT_REFUND",
	TransactionGoodwillCredit:                          "GOODWILL_CREDIT",
	TransactionChargeRefund:                            "CHARGE_REFUND",
	TransactionChargeback:                              "CHARGEBACK",
	TransactionChargeAdjustment:                        "CHARGE_ADJUSTMENT",
	TransactionChargeOff:                               "CHARGE_OFF",
	TransactionDownPayment:                             "DOWN_PAYMENT",
	TransactionReage:                                   "REAGE",
	TransactionReamortize:                              "REAMORTIZE",
	TransactionInterestPaymentWaiver:                   "INTEREST_PAYMENT_WAIVER",
	TransactionAccrualActivity:                         "ACCRUAL_ACTIVITY",
	TransactionInterestRefund:                          "INTEREST_REFUND",
	TransactionAccrualAdjustment:                       "ACCRUAL_ADJUSTMENT",
	TransactionCapitalizedIncome:                       "CAPITALIZED_INCOME",
	TransactionCapitalizedIncomeAmortization:           "CAPITALIZED_INCOME_AMORTIZATION",
	TransactionCapitalizedIncomeAdjustment:             "CAPITALIZED_INCOME_ADJUSTMENT",
	TransactionContractTermination:                     "CONTRACT_TERMINATION",
	TransactionCapitalizedIncomeAmortizationAdjustment: "CAPITALIZED_INCOME_AMORTIZATION_ADJUSTMENT",
	TransactionBuyDownFee:                              "BUY_DOWN_FEE",
	TransactionBuyDownFeeAdjustment:                    "BUY_DOWN_FEE_ADJUSTMENT",
	TransactionBuyDownFeeAmortization:                  "BUY_DOWN_FEE_AMORTIZATION",
	TransactionBuyDownFeeAmortizationAdjustment:        "BUY_DOWN_FEE_AMORTIZATION_ADJUSTMENT",
	TransactionDiscountFee:                             "DISCOUNT_FEE",
	TransactionDiscountFeeAmortization:                 "DISCOUNT_FEE_AMORTIZATION",
	TransactionDiscountFeeAdjustment:                   "DISCOUNT_FEE_ADJUSTMENT",
	TransactionDiscountFeeAmortizationAdjustment:       "DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT",
}

var loanTransactionFromStored = map[int32]LoanTransactionType{}

// StoredValue returns m_loan_transaction.transaction_type_enum.
func (t LoanTransactionType) StoredValue() int32 {
	v, ok := loanTransactionStoredValue[t]
	if !ok {
		panic(fmt.Sprintf("loan: unknown LoanTransactionType %d", int32(t)))
	}
	return v
}

// Code returns the i18n code emitted on the transaction read.
func (t LoanTransactionType) Code() string { return loanTransactionCode[t] }

func (t LoanTransactionType) String() string {
	if n, ok := loanTransactionName[t]; ok {
		return n
	}
	return fmt.Sprintf("LoanTransactionType(%d)", int32(t))
}

// LoanTransactionTypeFromStoredValue decodes transaction_type_enum. ok is false
// for INVALID(0), for the 11 gap, and for values >47, matching
// LoanTransactionType.fromInt's INVALID fallback
// [VERIFIED: LoanTransactionType.java:88-138].
func LoanTransactionTypeFromStoredValue(v int32) (LoanTransactionType, bool) {
	t, ok := loanTransactionFromStored[v]
	return t, ok
}

// The predicates below mirror LoanTransactionType's boolean helpers
// [VERIFIED: LoanTransactionType.java:160-295]. isRepaymentType is the union
// used by repayment-allocation code to decide which transactions consume a
// repayment schedule.

func (t LoanTransactionType) IsDisbursement() bool { return t == TransactionDisbursement }
func (t LoanTransactionType) IsRepaymentAtDisbursement() bool {
	return t == TransactionRepaymentAtDisbursement
}
func (t LoanTransactionType) IsRepayment() bool { return t == TransactionRepayment }
func (t LoanTransactionType) IsInterestPaymentWaiver() bool {
	return t == TransactionInterestPaymentWaiver
}
func (t LoanTransactionType) IsMerchantIssuedRefund() bool {
	return t == TransactionMerchantIssuedRefund
}
func (t LoanTransactionType) IsPayoutRefund() bool        { return t == TransactionPayoutRefund }
func (t LoanTransactionType) IsGoodwillCredit() bool      { return t == TransactionGoodwillCredit }
func (t LoanTransactionType) IsChargeRefund() bool        { return t == TransactionChargeRefund }
func (t LoanTransactionType) IsRecoveryRepayment() bool   { return t == TransactionRecoveryRepayment }
func (t LoanTransactionType) IsWaiveInterest() bool       { return t == TransactionWaiveInterest }
func (t LoanTransactionType) IsWaiveCharges() bool        { return t == TransactionWaiveCharges }
func (t LoanTransactionType) IsAccrual() bool             { return t == TransactionAccrual }
func (t LoanTransactionType) IsWriteOff() bool            { return t == TransactionWriteoff }
func (t LoanTransactionType) IsChargePayment() bool       { return t == TransactionChargePayment }
func (t LoanTransactionType) IsRefundForActiveLoan() bool { return t == TransactionRefundForActiveLoan }
func (t LoanTransactionType) IsIncomePosting() bool       { return t == TransactionIncomePosting }
func (t LoanTransactionType) IsChargeback() bool          { return t == TransactionChargeback }
func (t LoanTransactionType) IsChargeAdjustment() bool    { return t == TransactionChargeAdjustment }
func (t LoanTransactionType) IsChargeOff() bool           { return t == TransactionChargeOff }
func (t LoanTransactionType) IsReage() bool               { return t == TransactionReage }
func (t LoanTransactionType) IsReamortize() bool          { return t == TransactionReamortize }
func (t LoanTransactionType) IsDownPayment() bool         { return t == TransactionDownPayment }
func (t LoanTransactionType) IsAccrualActivity() bool     { return t == TransactionAccrualActivity }
func (t LoanTransactionType) IsInterestRefund() bool      { return t == TransactionInterestRefund }
func (t LoanTransactionType) IsAccrualAdjustment() bool   { return t == TransactionAccrualAdjustment }
func (t LoanTransactionType) IsCapitalizedIncome() bool   { return t == TransactionCapitalizedIncome }
func (t LoanTransactionType) IsCapitalizedIncomeAdjustment() bool {
	return t == TransactionCapitalizedIncomeAdjustment
}
func (t LoanTransactionType) IsContractTermination() bool { return t == TransactionContractTermination }
func (t LoanTransactionType) IsBuyDownFee() bool          { return t == TransactionBuyDownFee }
func (t LoanTransactionType) IsBuyDownFeeAdjustment() bool {
	return t == TransactionBuyDownFeeAdjustment
}
func (t LoanTransactionType) IsDiscountFee() bool { return t == TransactionDiscountFee }
func (t LoanTransactionType) IsDiscountFeeAmortization() bool {
	return t == TransactionDiscountFeeAmortization
}

// IsRepaymentType is the repayment-like union [VERIFIED: LoanTransactionType.java:200-203].
func (t LoanTransactionType) IsRepaymentType() bool {
	return t.IsRepayment() || t.IsMerchantIssuedRefund() || t.IsPayoutRefund() ||
		t.IsGoodwillCredit() || t.IsChargeRefund() || t.IsDownPayment() ||
		t.IsInterestPaymentWaiver() || t.IsChargeAdjustment()
}

func init() {
	for t, v := range loanTransactionStoredValue {
		if _, dup := loanTransactionFromStored[v]; dup {
			panic(fmt.Sprintf("loan: loan transaction encode table is not injective at %d", v))
		}
		loanTransactionFromStored[v] = t
	}
}
