#!/bin/sh
# T45 probe generator - P1-T43-2. Enumerates every ambient-MoneyHelper-reading path inside Money.java.
# Reads the pinned Fineract checkout only; writes nothing there.
FIN=${FIN:-/Users/buv/fineract}
M="$FIN/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java"

echo "T45 PROBE - P1-T43-2: the COMPLETE set of ambient-context reads inside Money.java"
echo "pinned checkout HEAD: $(git -C "$FIN" rev-parse HEAD)"
echo "Money.java line count: $(wc -l < "$M")"
echo
echo "== (a) every direct MoneyHelper read in Money.java"
grep -n 'MoneyHelper' "$M"
echo
echo "  103  Money.of(CurrencyData, BigDecimal)       -> getMathContext()     LISTED in rev 8"
echo "  115  Money.of(MonetaryCurrency, BigDecimal)   -> getMathContext()     LISTED in rev 8"
echo "  119  Money.zero(MonetaryCurrency)             -> getMathContext()     LISTED in rev 8"
echo "  131  Money.zero(CurrencyData)                 -> getMathContext()     *** NOT LISTED in rev 8"
echo "  154  roundToMultiplesOf(BigDecimal, Integer)  -> getRoundingMode()    LISTED in rev 8"
echo "  160  roundToMultiplesOf(Money, Integer)       -> getMathContext()     LISTED in rev 8"
echo "  495  getMc() null branch                      -> getMathContext()     LISTED in rev 8 (as the mechanism)"
echo
echo "== (b) every Money.of / Money.zero / roundToMultiplesOf call site inside Money.java, classified"
grep -n 'Money\.of(\|Money\.zero(\|roundToMultiplesOf(' "$M"
echo
echo "  Of these, the ones that route through the TWO-ARGUMENT Money.of and so read the ambient"
echo "  context regardless of the receiver's own mc:"
echo "    169  roundToMultiplesOf(Money,Integer,MathContext) return path       LISTED in rev 8"
echo "    233  plus(Iterable<? extends Money>)                                *** NOT LISTED in rev 8"
echo "    266  plus(double)                                                   *** NOT LISTED in rev 8"
echo "    377  multipliedBy(double)                                           LISTED in rev 8"
echo "  Every other call site in the file passes an explicit mc or getMc()."
echo
echo "== the three omissions, in full"
awk 'NR>=130 && NR<=132 {printf "  Money.java:%d  %s\n", NR, $0}' "$M"
echo
awk 'NR>=224 && NR<=234 {printf "  Money.java:%d  %s\n", NR, $0}' "$M"
echo
awk 'NR>=261 && NR<=267 {printf "  Money.java:%d  %s\n", NR, $0}' "$M"
echo
echo "== reachability of :130-132 on the progressive call graph"
E="$FIN/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java"
awk 'NR>=142 && NR<=144 {printf "  ProgressiveEMICalculator.java:%d  %s\n", NR, $0}' "$E"
awk 'NR>=155 && NR<=158 {printf "  ProgressiveEMICalculator.java:%d  %s\n", NR, $0}' "$E"
awk 'NR>=176 && NR<=182 {printf "  ProgressiveEMICalculator.java:%d  %s\n", NR, $0}' "$E"
echo "  -> :182 uses the ONE-ARGUMENT Money.zero(CurrencyData) = Money.java:130-132 -> :131 -> ambient."
echo "  -> gated on isAllowFullTermForTranche() at :142-144, which is a SS4.4 PIN, not a SS3.1 predicate."
echo
echo "== reachability of :224-234 and :261-267 - grep only, NOT a call-graph proof"
echo "  .plus( call sites in fineract-progressive-loan/src/main: $(grep -rn '\.plus(' "$FIN/fineract-progressive-loan/src/main/java/" | wc -l | tr -d ' ')"
echo "  none of them passes a collection or a double (see t45-plus-callsites.txt)"
echo "  [UNVERIFIED: reachability of Money.java:224-234 and :261-267 from generate(mc, modelData)]"
echo
echo "CONCLUSION: rev 8's list was short by three. Rev 9 states the list as a closed set over ONE FILE,"
echo "and rests the graded-domain conclusion on T42's ABSENCE test rather than on the list."
