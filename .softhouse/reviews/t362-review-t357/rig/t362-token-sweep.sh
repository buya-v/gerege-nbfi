#!/bin/bash
# T362 independent token sweep. Token list constructed by T362 from check-shape.py's
# three FAILING assertions and their surrounding subject matter, NOT reused from T357.
# Root derived from $0, never hard-coded: this file sits four levels below the
# checkout root, under .softhouse/reviews/t362-review-t357/rig.
W="$(cd "$(dirname "$0")/../../../.." && pwd)"
cat > /tmp/tok.txt <<'EOF'
paymentChannelToFundSourceMappings
feeToIncomeAccountMappings
penaltyToIncomeAccountMappings
accountingMappings
accountingRule
fundSourceAccount
loanPortfolioAccount
transfersInSuspenseAccount
interestOnLoanAccount
incomeFromFeeAccount
incomeFromPenaltyAccount
incomeFromRecoveryAccount
writeOffAccount
overpaymentLiabilityAccount
goodwillCreditAccount
chargeOffExpenseAccount
receivableInterestAccount
receivableFeeAccount
receivablePenaltyAccount
loanproduct
loanProduct
loanproducts
loanProducts
loan_product
m_product_loan
productId
product_id
check-shape
a2-11
A2-11
a2-7
A2-7
A2-211
tierA-a2
present and null
omitempty
serializeNulls
nine-mandatory
EOF
echo "TOKENS: $(grep -c . /tmp/tok.txt)  (T362-constructed, superset of T357's 7)"
echo "vectors files: $(find "$W/.softhouse/vectors" -type f | wc -l | tr -d ' ')"
echo
printf '%-38s %8s %10s %10s %10s\n' TOKEN vectors conf-main conf-T357 conf-T358
while IFS= read -r t; do
  [ -z "$t" ] && continue
  v=$(grep -rFo -- "$t" "$W/.softhouse/vectors/" 2>/dev/null | wc -l | tr -d ' ')
  cm=$(grep -Fo -- "$t" /tmp/conf-main.sh 2>/dev/null | wc -l | tr -d ' ')
  ct=$(grep -Fo -- "$t" /tmp/conf-t357.sh 2>/dev/null | wc -l | tr -d ' ')
  c8=$(grep -Fo -- "$t" /tmp/conf-t358.sh 2>/dev/null | wc -l | tr -d ' ')
  printf '%-38s %8s %10s %10s %10s\n' "$t" "$v" "$cm" "$ct" "$c8"
done < /tmp/tok.txt
echo
echo "=== POSITIVE CONTROL: tokens that MUST be present (proves the sweep can see) ==="
for t in loanschedule ledger principal_minor capture_ref; do
  v=$(grep -rFo -- "$t" "$W/.softhouse/vectors/" 2>/dev/null | wc -l | tr -d ' ')
  cm=$(grep -Fo -- "$t" /tmp/conf-main.sh 2>/dev/null | wc -l | tr -d ' ')
  printf '%-38s %8s %10s\n' "$t" "$v" "$cm"
done
