#!/usr/bin/env python3
"""T275 request bodies. WRITES ONLY NEW FILES AND REFUSES TO OVERWRITE ANY EXISTING ONE.

WHY THE REFUSAL IS THE POINT OF THIS FILE
-----------------------------------------
DEFECTS-FOUND-BY-REVIEW.md D-1: `mkreq2.py` OVERWROTE the request bodies that the
`attempt1-*` responses had already been captured against. Ten recipes in this directory
are therefore provably false -- each `.http` says `body-file: req/foo.json` and that file
no longer holds the bytes that produced the recorded response. The mechanism was not
malice or carelessness in the send; it was a GENERATOR THAT CLOBBERS.

So this generator cannot clobber. `w()` raises on an existing path. Re-running this script
against a tree it has already written is a no-op that exits 0 and prints `unchanged` for
every file, which is exactly the property a recipe needs in order to be re-issuable: the
bytes a reader regenerates today are the bytes that went over the wire, or the script
refuses to pretend otherwise.

Every filename is prefixed `t275-`. No file written here shares a name with any
pre-existing req/ body, so no earlier capture's recipe can be invalidated by running it.

MONEY. `principal` is a bare integer (minor-unit-safe: no decimal point, no exponent, no
float literal reaches JSON). `interestRatePerPeriod` is a RATE, not money, and is likewise
written as an integer. No monetary amount is decided by this script at all -- the charge
amounts exercised live in `m_charge` on the oracle and were put there by earlier fires.

GL account ids assumed (created by run-020-accounts.sh; re-verified against the live
oracle at T275 capture time and recorded in out/A2-500-db-mapping-before.txt):
   1 Assets                 ASSET   HEADER
   2 Fund Source            *** retyped ASSET -> INCOME by A2-111, see DEFECTS D-5 ***
   4 Loan Portfolio         ASSET   DETAIL
   6 Overpayment Liability  LIAB    DETAIL
   8 Interest On Loans      INCOME  DETAIL
   9 Income From Fees       INCOME  DETAIL
  10 Income From Penalties  INCOME  DETAIL
  11 Recoveries             INCOME  DETAIL
  13 Losses Written Off     EXPENSE DETAIL
  14 Goodwill Credit        EXPENSE DETAIL
  16 Fund Source Alternate  ASSET   DETAIL
  17 Disabled Asset         ASSET   DETAIL

GL 2 is DELIBERATELY NOT USED as a fund source by any product created here: A2-111 retyped
it to INCOME and G-10 ruled that products built for new observations use accounts the
oracle still accepts today. GL 16 is used instead.

CHARGE ids assumed, and VERIFIED against the live oracle before these bodies were sent
(see out/A2-520-db-fixtures.txt):
   1  T40 flat fee at disbursement            is_penalty=false  charge_time 1
   2  T40 flat fee per instalment             is_penalty=false  charge_time 8
   6  T40 PENALTY flat on specified due date  is_penalty=TRUE   charge_time 2

PARAMETER NAMES are not guessed. Every key below is the literal `getValue()` of a
constant in LoanProductAccountingParams
[VERIFIED: /Users/buv/fineract fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java,
`enum LoanProductAccountingParams`] -- in particular `writeOffReasonCodeValueId` and
`chargeOffReasonCodeValueId`, NOT the shorter `writeOffReasonId` / `chargeOffReasonId` that
the column names would suggest. A probe that sends a misspelled parameter is silently
ignored (out/A2-bad-053-unknown-param.json proves this oracle ignores unknown params at
HTTP 200) and would therefore be VACUOUS -- it would look like "the oracle has no
validation" when in fact nothing was tested. That is the P-22 class and it is why these
names were read out of the enum rather than inferred.
"""
import copy
import json
import os
import sys

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")

_written = 0
_unchanged = 0
_conflict = []


def w(name, obj):
    """Write req/<name>.json. NEVER overwrite; if the file exists, verify it already holds
    exactly these bytes and leave it alone, otherwise REFUSE and fail the run."""
    global _written, _unchanged
    assert name.startswith("t275-"), f"T275 bodies must be namespaced: {name}"
    path = os.path.join(REQ, name + ".json")
    payload = json.dumps(obj) + "\n"
    if os.path.exists(path):
        with open(path) as f:
            existing = f.read()
        if existing == payload:
            _unchanged += 1
            print("unchanged", name)
            return
        _conflict.append(name)
        print("CONFLICT ", name, "-- on-disk bytes differ from what this script would write")
        return
    with open(path, "w") as f:
        f.write(payload)
    _written += 1
    print("wrote    ", name)


# --------------------------------------------------------------------------- base bodies

BASE = {
    "shortName": None,
    "name": None,
    "description": "T275 capture: product-to-account mapping, charge dimension",
    "currencyCode": "MNT",
    "digitsAfterDecimal": 2,
    "inMultiplesOf": 0,
    "principal": 1200000,
    "numberOfRepayments": 6,
    "repaymentEvery": 1,
    "repaymentFrequencyType": 2,
    "interestRatePerPeriod": 0,
    "interestRateFrequencyType": 3,
    "amortizationType": 1,
    "interestType": 0,
    "interestCalculationPeriodType": 1,
    "transactionProcessingStrategyCode": "mifos-standard-strategy",
    "daysInYearType": 1,
    "daysInMonthType": 1,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
    "isInterestRecalculationEnabled": False,
}

# The ten mandatory CASH slots. GL 16 rather than GL 2 as fund source -- see the module
# docstring; GL 2 is the A2-111 retype and G-10 keeps new products off it.
CASH_MAP = {
    "fundSourceAccountId": 16,
    "loanPortfolioAccountId": 4,
    "transfersInSuspenseAccountId": 17,
    "interestOnLoanAccountId": 8,
    "incomeFromFeeAccountId": 9,
    "incomeFromPenaltyAccountId": 10,
    "incomeFromRecoveryAccountId": 11,
    "writeOffAccountId": 13,
    "goodwillCreditAccountId": 14,
    "overpaymentLiabilityAccountId": 6,
}


def prod(short, name, rule=2, extra=None):
    p = copy.deepcopy(BASE)
    p["shortName"] = short
    p["name"] = name
    p["accountingRule"] = rule
    if extra:
        p.update(extra)
    return p


# ============================================================== GROUP A -- product UPDATE
# CAPTURE-PLAN.md §5 row 1. req/upd-070-repoint-fundsource.json and
# req/upd-071-add-channel.json ALREADY EXIST, were written by an earlier fire and were
# never sent; they are NOT rewritten here (that would be the D-1 defect again). These two
# are the additional discriminators §5 did not have bodies for.

# A PUT that touches NO accounting parameter at all. If the mapping row ids churn anyway,
# then mapping replacement is a property of the UPDATE COMMAND, not of the accounting
# payload -- a port that rebuilds mappings only when an accounting field is present would
# then diverge on the identity values. If they do not churn, the replacement is scoped to
# the payload. Either answer is the observation; neither is assumed here.
w("t275-072-p23-description-only", {
    "description": "T275 unrelated-field update probe: no accounting parameter is present in this body",
    "locale": "en",
})

# An EMPTY paymentChannelToFundSourceMappings array. Delete-then-recreate and
# merge-by-key differ maximally here: under the first the channel row is deleted and
# nothing replaces it; under the second an empty list is a no-op and the row survives.
w("t275-073-p23-channel-empty", {
    "locale": "en",
    "paymentChannelToFundSourceMappings": [],
})

# ADDED AFTER READING THIS FIRE'S OWN GROUP-A RESULT, not before it. A2-503 showed the
# GENERIC fund-source slot is UPDATED IN PLACE -- mapping row id 12 survived while its
# gl_account_id went 2 -> 16 and the table's max(id) did not move. §5 named the row
# "delete-then-recreate", so on the generic slots §5's own framing is REFUTED by the
# oracle, and the interesting question moves to the LIST-VALUED dimension, where
# ProductToGLAccountMappingHelper.java:417/440 calls `deleteAll` / `delete`.
#
# This body re-points an EXISTING payment-channel row: same paymentTypeId (2), different
# account (GL 16 -> GL 17). If the row id survives, the list is merged by key like the
# generic slots. If a new id appears and the old one is gone, THAT is the delete-then-
# recreate §5 was reaching for, and it is scoped to the list dimension only.
w("t275-075-p23-channel-repoint", {
    "locale": "en",
    "paymentChannelToFundSourceMappings": [{"paymentTypeId": 2, "fundSourceAccountId": 17}],
})


# ================================================== GROUP B -- the CHARGE dimension (§5 r2)
# §5 recorded this as blocked: "needs an m_charge fixture; none exists on gerege". That is
# NO LONGER TRUE of this oracle -- 18 active LOAN charges exist, seeded by the T40/T48/T51
# Path B fires, two of them penalties. So the third resolution dimension (charge_id) is
# reachable with NO new fixture and is taken here. The fixture claim is re-verified at
# capture time in out/A2-520-db-fixtures.txt rather than trusted from §5 or from this note.

# The instrument: fee and penalty overrides pointed at accounts that are NOT the generic
# slots, so resolution can be DISTINGUISHED. Generic incomeFromFee is GL 9 and generic
# incomeFromPenalty is GL 10; the overrides send fee -> GL 11 (Recoveries, INCOME) and
# penalty -> GL 8 (Interest On Loans, INCOME). Both targets are INCOME DETAIL accounts, so
# a refusal cannot be attributed to account type.
w("t275-080-charge-mappings", prod(
    "T7A0", "T275 Charge Dimension Fee And Penalty", 2,
    dict(CASH_MAP,
         charges=[{"id": 1}, {"id": 6}],
         feeToIncomeAccountMappings=[{"chargeId": 1, "incomeAccountId": 11}],
         penaltyToIncomeAccountMappings=[{"chargeId": 6, "incomeAccountId": 8}])))

# A fee override naming a charge that is NOT attached to the product. Is the charge
# required to be one of the product's own charges, or is any charge id accepted?
w("t275-081-fee-charge-not-attached", prod(
    "T7A1", "T275 Fee Charge Not Attached", 2,
    dict(CASH_MAP,
         charges=[{"id": 1}],
         feeToIncomeAccountMappings=[{"chargeId": 2, "incomeAccountId": 11}])))

# A PENALTY override naming a charge whose is_penalty is FALSE (charge 1), and a FEE
# override naming a charge whose is_penalty is TRUE (charge 6). Both charges are attached.
# Is the penalty/fee character of the charge checked against the mapping key it appears
# under?
w("t275-082-penalty-mapping-on-fee-charge", prod(
    "T7A2", "T275 Penalty Mapping On Fee Charge", 2,
    dict(CASH_MAP,
         charges=[{"id": 1}, {"id": 6}],
         penaltyToIncomeAccountMappings=[{"chargeId": 1, "incomeAccountId": 8}],
         feeToIncomeAccountMappings=[{"chargeId": 6, "incomeAccountId": 11}])))

# A fee override pointed at an EXPENSE account (GL 13, Losses Written Off). §3 row 9
# captured GL-type checking on the generic slots; this asks whether the same check reaches
# the charge-scoped slots.
w("t275-083-fee-income-expense-account", prod(
    "T7A3", "T275 Fee Income Expense Account", 2,
    dict(CASH_MAP,
         charges=[{"id": 1}],
         feeToIncomeAccountMappings=[{"chargeId": 1, "incomeAccountId": 13}])))

# TWO fee overrides for the SAME chargeId, pointing at DIFFERENT accounts. This is the
# charge-dimension twin of prod-067-duplicate-channel, which the oracle accepted at HTTP
# 200 and which then detonated at resolution (§4.1). Same question, different dimension.
w("t275-084-duplicate-fee-charge", prod(
    "T7A4", "T275 Duplicate Fee Charge", 2,
    dict(CASH_MAP,
         charges=[{"id": 1}],
         feeToIncomeAccountMappings=[
             {"chargeId": 1, "incomeAccountId": 11},
             {"chargeId": 1, "incomeAccountId": 8},
         ])))


# ============================== GROUP C -- reason mappings, referential integrity (§5 r5)
# `acc_product_mapping.write_off_reason_id` has NO foreign key, while
# `charge_off_reason_id`, `capitalized_income_classification_id` and
# `buydown_fee_classification_id` all DO reference m_code_value
# [VERIFIED: live `\d acc_product_mapping` on fineract_gerege at T275 capture time,
# recorded in out/A2-520-db-fixtures.txt]. §5 said probing this "needs the
# write-off-reason fixture to probe a dangling id" -- but a DANGLING id needs no fixture
# BY DEFINITION. The seeded-value case (a mapping that actually resolves) does need
# m_code_value rows and is excluded; the dangling case does not and is taken here.
#
# m_code rows `WriteOffReasons` (id 26) and `ChargeOffReasons` (id 39) EXIST on this
# oracle and have ZERO m_code_value rows, so 999999 is dangling under either code.

w("t275-090-writeoff-reason-dangling", prod(
    "T7B0", "T275 WriteOff Reason Dangling", 2,
    dict(CASH_MAP,
         writeOffReasonsToExpenseMappings=[
             {"writeOffReasonCodeValueId": 999999, "expenseAccountId": 13}])))

# The same dangling id, but the expense slot is pointed at GL 9 (Income From Fees, INCOME
# DETAIL) rather than an expense account. Two rules are in play -- "the reason must exist"
# and "the account must be an Expense GL account" (§5 rows 3/4) -- and which message comes
# back tells us the ORDER they are evaluated in, which §5 could not ask without a fixture.
w("t275-091-writeoff-reason-dangling-nonexpense", prod(
    "T7B1", "T275 WriteOff Reason Dangling NonExpense", 2,
    dict(CASH_MAP,
         writeOffReasonsToExpenseMappings=[
             {"writeOffReasonCodeValueId": 999999, "expenseAccountId": 9}])))

# The charge-off twin. This column DOES carry an FK, so if the application check is absent
# the failure surfaces from PostgreSQL instead -- the A2-bad-045 pattern, where a missing
# validator leaks raw constraint text to the caller.
w("t275-092-chargeoff-reason-dangling", prod(
    "T7B2", "T275 ChargeOff Reason Dangling", 2,
    dict(CASH_MAP,
         chargeOffReasonToExpenseAccountMappings=[
             {"chargeOffReasonCodeValueId": 999999, "expenseAccountId": 13}])))

# The charge-off twin of the account-type question.
w("t275-093-chargeoff-reason-dangling-nonexpense", prod(
    "T7B3", "T275 ChargeOff Reason Dangling NonExpense", 2,
    dict(CASH_MAP,
         chargeOffReasonToExpenseAccountMappings=[
             {"chargeOffReasonCodeValueId": 999999, "expenseAccountId": 9}])))


# --------------------------------------------------------------------------------- report
print(f"\n{_written} written, {_unchanged} unchanged, {len(_conflict)} CONFLICT")
if _conflict:
    print("REFUSED to overwrite:", ", ".join(_conflict), file=sys.stderr)
    print("This script never clobbers a request body (D-1). Resolve by hand or rename.", file=sys.stderr)
    sys.exit(1)
