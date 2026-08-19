#!/bin/sh
# T43 probe -- (a) the totalRepaymentExpected difference between the two generators,
# (b) the INSTALMENT-fee bypass of the M4 membership test.  Read-only, from source.
P=/Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.java
C=/Users/buv/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/AbstractCumulativeLoanScheduleGenerator.java
S=/Users/buv/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ScheduleCurrentPeriodParams.java
echo "=== every addTotalRepaymentExpected call, both generators ==="
grep -n "addTotalRepaymentExpected" $P $C
echo
echo "=== what the cumulative main loop adds (:352 -> ScheduleCurrentPeriodParams:144-146) ==="
sed -n '350,353p' $C
sed -n '144,146p' $S
echo
echo "=== progressive :486 vs cumulative :504 -- the SAME separated-path line ==="
sed -n '486p' $P
sed -n '504p' $C
echo
echo "=== getCumulativeAmountOfCharge: isDue is NOT consulted for an instalment fee ==="
sed -n '400,415p' $P
