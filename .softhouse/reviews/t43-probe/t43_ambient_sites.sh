#!/bin/sh
# T43 probe -- re-derive the COMPLETE set of ambient (MoneyHelper) reads in Money.java
# from the pinned checkout, and compare against DEC-1 rev 8 section 4.1.2's enumeration.
# Read-only. No Gradle. No oracle.
M=/Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java
echo "--- direct MoneyHelper reads in Money.java ---"
grep -n "MoneyHelper.getMathContext()\|MoneyHelper.getRoundingMode()" $M
echo
echo "--- instance methods routing through the TWO-ARG Money.of (=> ambient) ---"
grep -n "Money.of(getCurrencyData(), [A-Za-z]*)$\|Money.of(getCurrencyData(), total)" $M
echo
echo "--- callers of the one-arg Money.zero(CurrencyData) on the progressive path ---"
grep -rn "Money.zero(loanProductRelatedDetail.getCurrencyData())" /Users/buv/fineract/fineract-progressive-loan/src/main
