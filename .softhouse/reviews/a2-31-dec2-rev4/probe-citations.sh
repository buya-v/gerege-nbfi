#!/bin/bash
# A2-31 PROBE — resolve every Fineract file:line citation in DEC-2 rev 4 at the pinned
# checkout 426a23544e8426a38ae43ae404670a0a7e85b9eb, and PRINT THE BYTES, so the reviewer
# binds each citation BY CONTENT rather than trusting the line number.
# READ-ONLY: sed -n only, no -i anywhere, no redirection into the checkout.
set -u
FIN=/Users/buv/fineract
cd "$FIN" || exit 1
echo "pinned checkout HEAD: $(git rev-parse HEAD)"
echo
show() { # show <basename> <from> <to>
  local f="$1" a="$2" b="$3" p
  p=$(find "$FIN" -name "$f" -not -path '*/build/*' -not -path '*/.git/*' | head -1)
  echo "===== $f  lines $a-$b"
  echo "----- resolved to: ${p#$FIN/}"
  if [ -z "$p" ]; then echo "!!! FILE NOT FOUND"; return; fi
  sed -n "${a},${b}p" "$p" | cat -n | sed "s/^ *\([0-9]*\)\t/  /"
  echo
}
show AccountingConstants.java 37 62
show AccountingConstants.java 39 39
show AccountingConstants.java 48 48
show AccountingConstants.java 439 445
show AccountingConstants.java 95 122
show AccountingProcessorHelper.java 1185 1216
show AccountingProcessorHelper.java 1199 1206
show AccountingProcessorHelper.java 1213 1213
show AccountingProcessorHelper.java 1218 1238
show AccountingProcessorHelper.java 1340 1342
show AccountingProcessorHelper.java 1024 1027
show AccountingProcessorHelper.java 1208 1211
show AccountingProcessorHelper.java 1337 1337
show AccountingProcessorHelper.java 1026 1026
show AccountingProcessorHelper.java 1210 1210
show GLAccountReadPlatformServiceImpl.java 214 222
show GLAccountWritePlatformServiceJpaRepositoryImpl.java 151 159
show JournalEntry.java 79 79
show JournalEntry.java 91 91
show JournalEntryRepository.java 61 61
show LoanProductDataValidator.java 744 744
show PortfolioProductType.java 26 31
show PortfolioProductType.java 51 59
show ProductToGLAccountMappingWritePlatformServiceImpl.java 149 151
show ProductToGLAccountMappingWritePlatformServiceImpl.java 410 411
show ProgressiveLoanScheduleGenerator.java 83 83
show SavingsProductToGLAccountMappingHelper.java 192 193
show UpdateTrialBalanceDetailsTasklet.java 81 81
show 0001_initial_schema.xml 98 110
show 0001_initial_schema.xml 119 121
