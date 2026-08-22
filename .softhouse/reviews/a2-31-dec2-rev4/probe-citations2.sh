#!/bin/bash
# A2-31 PROBE (part 2) — the citations whose basename is ambiguous, resolved by the
# path the ADR itself gives, or by picking the DOMAIN class rather than a test double.
# READ-ONLY.
set -u
FIN=/Users/buv/fineract
echo "pinned checkout HEAD: $(cd "$FIN" && git rev-parse HEAD)"
echo
echo "===== all JournalEntry.java under the checkout (excluding build/)"
find "$FIN" -name JournalEntry.java -not -path '*/build/*' -not -path '*/.git/*' | sed "s#$FIN/##"
echo
JE="$FIN/fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntry.java"
echo "===== domain JournalEntry.java :79 and :91"
sed -n '75,95p' "$JE"
echo
echo "===== grep 'reversed' and 'amount' @Column in domain JournalEntry.java"
grep -n 'reversed\|name = "amount"' "$JE" | head
echo
echo "===== case-insensitive 'classification' occurrences in domain JournalEntry.java"
grep -ic 'classification' "$JE"
echo
echo "===== office_running_balance / organization_running_balance in domain JournalEntry.java"
grep -n 'running_balance\|RunningBalance' "$JE" | head
echo
SCH="$FIN/fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml"
echo "===== provider tenant 0001_initial_schema.xml :96-125 (the ADR's own full path)"
sed -n '96,125p' "$SCH"
echo
echo "===== AccountingConstants.java :704 (GOODWILL_CREDIT claim) -- and LoanProductDataValidator :704"
sed -n '700,710p' "$FIN/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanproduct/serialization/LoanProductDataValidator.java"
echo
echo "===== GLAccountWritePlatformServiceJpaRepositoryImpl.java :201-203"
sed -n '199,205p' "$FIN/fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java"
echo
echo "===== SavingsProductToGLAccountMappingHelper.java :313-314"
sed -n '310,316p' "$FIN/fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/service/SavingsProductToGLAccountMappingHelper.java"
echo
echo "===== ProductToGLAccountMappingRepository.java findCoreProductToFinAccountMapping"
grep -n -A 12 'findCoreProductToFinAccountMapping' "$(find "$FIN" -name ProductToGLAccountMappingRepository.java -not -path '*/build/*' | head -1)" | head -30
