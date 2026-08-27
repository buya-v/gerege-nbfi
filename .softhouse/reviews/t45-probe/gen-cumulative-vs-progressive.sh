#!/bin/sh
# T45 probe generator. Reads the pinned Fineract checkout only; writes nothing there.
FIN=${FIN:-/Users/buv/fineract}
A="$FIN/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/AbstractCumulativeLoanScheduleGenerator.java"
P="$FIN/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.java"
S="$FIN/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ScheduleCurrentPeriodParams.java"

echo "T45 PROBE - P1-T43-1: is AbstractCumulativeLoanScheduleGenerator.java:504 a DIFFERENCE, or the line the two generators SHARE?"
echo "pinned checkout HEAD: $(git -C "$FIN" rev-parse HEAD)"
echo
echo "== progressive :486"; sed -n '486p' "$P"
echo "== cumulative  :504"; sed -n '504p' "$A"
echo "== md5 of each line"
printf '  progressive:486  %s\n' "$(sed -n '486p' "$P" | md5)"
printf '  cumulative :504  %s\n' "$(sed -n '504p' "$A" | md5)"
echo
echo "== whole-method diff: cumulative updatePeriodsWithCharges (488-508) vs progressive (470-490)"
diff "/dev/fd/3" "/dev/fd/4" 3<<EOF1 4<<EOF2
$(sed -n '488,508p' "$A")
EOF1
$(sed -n '470,490p' "$P")
EOF2
echo "  (differences above are parameter TYPES only - MonetaryCurrency vs CurrencyData, and the mc-carrying Money.of; the addTotalRepaymentExpected line is identical)"
echo
echo "== THE REAL DIFFERENCE - cumulative main loop folds the period's charges into the period total first"
awk 'NR==349 || NR==352 || NR==392 {printf "  AbstractCumulativeLoanScheduleGenerator.java:%d  %s\n", NR, $0}' "$A"
awk 'NR>=144 && NR<=146 {printf "  ScheduleCurrentPeriodParams.java:%d  %s\n", NR, $0}' "$S"
echo
echo "== progressive counterpart - :137 has no charge term, :367-382 never calls addTotalRepaymentExpected"
awk 'NR==137 || NR==140 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s\n", NR, $0}' "$P"
awk 'NR>=367 && NR<=382 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s\n", NR, $0}' "$P"
echo
echo "== P2-T43-1: the down-payment term revision 8's C-1 semantics omitted"
awk 'NR>=332 && NR<=347 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s\n", NR, $0}' "$P"
echo
echo "== P1-T43-3: getCumulativeAmountOfCharge - isDue is computed at :403 and the isInstalmentFee arm at :404-405 does not read it"
awk 'NR>=400 && NR<=415 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s\n", NR, $0}' "$P"
echo
echo "== P1-T43-3, the two isInstallmentChargeApplicable sources"
awk 'NR==373 || NR==376 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s   <- main loop: hard-coded true\n", NR, $0}' "$P"
awk 'NR==479 || NR==483 {printf "  ProgressiveLoanScheduleGenerator.java:%d  %s   <- separated path\n", NR, $0}' "$P"
echo
echo "CONCLUSION: :504 == :486 byte for byte. C-1's conclusion stands; its revision-8 citation did not."
