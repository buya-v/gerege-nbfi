# T43 — Independent re-review of DEC-1 revision 8 (the ratification candidate)

| | |
|---|---|
| Task | T43 |
| Target | `docs/adr/DEC-1-schedule-generator-adapter.md` revision 8 (written by T41) + `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reference oracle | Fineract, pinned checkout `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `git rev-parse HEAD` in the pinned checkout] |
| Method | Re-derivation from the pinned source; independent re-opening of every load-bearing `file:line`; an independently written from-text model of §4.2's re-anchor and §4.1.1 steps A–C replayed against committed captures; independent digest verification of the committed capture corpus |
| Oracle contacted | **No.** No container started, no Gradle run, no HTTP request. Every observation cited is quoted from a committed capture with its id. |
| Branch | `softhouse/T43-dec1-v8-rereview` |
| Probes | `.softhouse/reviews/t43-probe/` |

---

## 0. VERDICT

**ACCEPTED WITH REQUIRED CHANGES.**

**No P0. No rejection-grade finding.** Nothing below moves money inside the graded
domain, nothing below changes a type, a field, an enum member or a graded-domain
predicate, and nothing below makes the specification incomplete for a port operating
inside the Run-1 graded domain. Under §1 and standing policy P-2 the driver may take
the ratification decision on this review; the three P1s are corrections revision 9
should carry, not obstacles to ratification.

Stated plainly, because "not CLEAN" and "not ratifiable" are different things: **this
review found no reason not to ratify.** It found three places where a `[VERIFIED]`
citation, or an enumeration presented as exhaustive, does not say what the sentence
attached to it claims — all three in content that is new in revision 8, all three in
the charge / `MathContext` material no prior round has examined.

| id | grade | section | one line |
|---|---|---|---|
| **P1-T43-1** | P1 | §4.5.1 C-1, §8 item 9, §9, revision history | `AbstractCumulativeLoanScheduleGenerator.java:504` is cited three times as the line on which the cumulative generator differs from the progressive one; it is the line they **share**. The conclusion is right, the citation refutes it. |
| **P1-T43-2** | P1 | §4.1.2, §4.1 | The enumeration "the ambient context is reached at **exactly** these call sites" omits three sites in `Money.java`, and its closing sentence ("every remaining site sits on the installment-multiple or `multipliedBy(double)` path, which the graded domain excludes") is false of one of them. |
| **P1-T43-3** | P1 | §4.3.2 M4 row, §9 membership obligation | M4 is stated as deciding "which repayment row a **CHARGE** lands on". An `INSTALMENT_FEE` charge never consults the membership test at all and lands on **every** row. Observed in the corpus and re-derived from source. |
| **P2-T43-1** | P2 | §4.5.1 C-1 | The stated progressive `totalRepaymentExpected` semantics omit the down-payment term at `ProgressiveLoanScheduleGenerator.java:345`. |
| **P2-T43-2** | P2 | revision history vs §4.1.1 / §8 3e | Two different cell counts for the same corpus (1,224 vs 1,239) with no statement that they are different comparison shapes. |
| **P2-T43-3** | P2 | §4.3.1 discriminate table | First-witness cell for `n = NumberOfRepayments` given as `T37-3c` `R2.principal`; the committed probe output it cites names `R2.balance`. |

---

## 1. P1-T43-1 — C-1's distinguishing citation is the line the two generators SHARE

**Section:** §4.5.1 "Decision C-1", the paragraph headed *"Mechanism, re-derived by this
task from the pinned checkout, not read back from T40"*; repeated in §4.5.1's
"What the charge corpus still CANNOT grade" bullet 4, in §9's `totalRepaymentExpected`
obligation, and in the revision-8 history entry.

**What the document says.**

> The **only** charge contribution after the seed comes from `updatePeriodsWithCharges`
> [`:486`], which serves just the two *separated* calculation types. **The cumulative
> generator does the opposite:** it adds fee and penalty to the running total on every
> period [VERIFIED: `AbstractCumulativeLoanScheduleGenerator.java:504`]. **The two
> generators disagree**, so the field does not have one meaning in Fineract at all.

**Re-derivation.** `AbstractCumulativeLoanScheduleGenerator.java:488-508` is that
generator's `updatePeriodsWithCharges`, and it is character-for-character the same
method as `ProgressiveLoanScheduleGenerator.java:470-490`. Line for line:

```
ProgressiveLoanScheduleGenerator.java:486
    scheduleParams.addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment));
AbstractCumulativeLoanScheduleGenerator.java:504
    scheduleParams.addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment));
```

[VERIFIED: `.softhouse/reviews/t43-probe/t43-charge-membership-output.txt`, section
"progressive :486 vs cumulative :504 — the SAME separated-path line"; both files
re-opened in the pinned checkout.] Both iterate `nonCompoundingCharges` only — the
separated set built by `separateTotalCompoundingPercentageCharges`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:492-504`] — so `:504` is **not**
"on every period" and it is **not** a difference from the progressive generator.

The line that actually distinguishes them is the cumulative generator's **main loop**:

```
AbstractCumulativeLoanScheduleGenerator.java:352
    final Money totalInstallmentDue = currentPeriodParams.fetchTotalAmountForPeriod();
AbstractCumulativeLoanScheduleGenerator.java:392
    scheduleParams.addTotalRepaymentExpected(totalInstallmentDue);
ScheduleCurrentPeriodParams.java:144-146
    public Money fetchTotalAmountForPeriod() {
        return this.principalForThisPeriod.plus(interestForThisPeriod)
               .plus(feeChargesForInstallment).plus(penaltyChargesForInstallment);
    }
```

[VERIFIED: all three re-opened in the pinned checkout;
`.softhouse/reviews/t43-probe/t43-charge-membership-output.txt`.] Against the
progressive generator's `:137`,
`scheduleParams.addTotalRepaymentExpected(principalDue.plus(interestDue, mc))`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:137`], which carries no charge term.

**So the conclusion "the two generators disagree" is TRUE and decision C-1 stands
unchanged** — but its stated evidence, read literally, says the opposite of what it is
cited for, and a reader who re-derives from the given `file:line` (which is exactly
what `patterns.md` requires of the next reviewer) will find the argument collapses.

**Corroborated by the document's own capture corpus, which also shows the document
knows the true shape elsewhere.** In T40's captures the two *separated*-path charges —
the only ones `:486` touches — are precisely the two that **pass** invariant C5:
`FC-19` (`totalRepaymentExpected` 1,350,425.54 = control 1,344,988.47 + fee 5,437.07)
and `FC-21` (1,361,592.35 = 1,344,988.47 + 16,603.88), while every main-loop charge
capture fails it [VERIFIED: `.softhouse/capture/charges/out/attested/*-raw.json`, read
directly by this review; `out/INVARIANTS.md` C5, 15 of 21 FAIL]. §4.5.1's own
parenthetical definition of the progressive reading already includes the separated
term, so the defect is confined to the *contrast* sentence and its citation.

**Money moved: none.** The contract discards the field.

**Required change.** Replace the `:504` citation with
`AbstractCumulativeLoanScheduleGenerator.java:352` and `:392` plus
`ScheduleCurrentPeriodParams.java:144-146` at all three sites (§4.5.1 mechanism,
§4.5.1 blind-spot bullet, §9 obligation) and in the revision-8 history entry, and say
explicitly that `:504` and the progressive `:486` are the same separated-path line so a
later reader does not re-raise this.

---

## 2. P1-T43-2 — §4.1.2's "exactly these call sites" is incomplete by three, and its closing sentence is false of one of them

**Section:** §4.1.2, the bullet beginning *"The ambient context is reached at exactly
these call sites"*, and its closing bullet *"Every remaining site sits on the
installment-multiple or `multipliedBy(double)` path, which the graded domain
excludes"*; the same enumeration also appears in §4.1's "One mode, not three".

**What the document enumerates.** Two-argument `Money.of` [`:102-104`, `:114-116`],
`Money.zero(currency)` [`:118-120`], static `roundToMultiplesOf(BigDecimal, Integer)`
[`:150-157`, `:154`], `roundToMultiplesOf(Money, Integer)` [`:159-161`], the
three-argument form's return path [`:163-170`, `:169`], `multipliedBy(double)`
[`:372-378`, `:377`], and — added in revision 8 from T42 — the constructor's call to
the two-argument `roundToMultiplesOf` [`Money.java:50` → `:154`].

**Re-derivation of the complete set.** Every direct `MoneyHelper` read in `Money.java`
[VERIFIED: `.softhouse/reviews/t43-probe/t43-ambient-sites-output.txt`]:

```
103  Money.of(CurrencyData, BigDecimal)      -> MoneyHelper.getMathContext()
115  Money.of(MonetaryCurrency, BigDecimal)  -> MoneyHelper.getMathContext()
119  Money.zero(MonetaryCurrency)            -> MoneyHelper.getMathContext()
131  Money.zero(CurrencyData)                -> MoneyHelper.getMathContext()   <-- NOT LISTED
154  roundToMultiplesOf(BigDecimal, Integer) -> MoneyHelper.getRoundingMode()
160  roundToMultiplesOf(Money, Integer)      -> MoneyHelper.getMathContext()
495  getMc()  (the null branch)              -> MoneyHelper.getMathContext()
```

plus the instance methods that route through the **two-argument** `Money.of` and so
read the ambient context regardless of the receiver's own `mc`:

```
233  plus(Iterable<? extends Money>)  -> Money.of(getCurrencyData(), total)      <-- NOT LISTED
266  plus(double)                     -> Money.of(getCurrencyData(), newAmount)  <-- NOT LISTED
377  multipliedBy(double)             -> Money.of(getCurrencyData(), newAmount)      (listed)
169  roundToMultiplesOf(Money,Integer,MathContext) return path                       (listed)
```

[VERIFIED: `Money.java:224-234`, `:249-267`, `:372-378`, all re-opened in the pinned
checkout.] The enumeration is short by **three**: `Money.java:130-132`, `:224-234`,
`:261-267`.

**And one of the three is reached on the progressive calculator's own call graph.**

```
ProgressiveEMICalculator.java:182
    .seedDate(firstDisbursedPeriodStartDate)
    .inArrearsTolerance(Money.zero(loanProductRelatedDetail.getCurrencyData()))
```

— the **one-argument** overload, i.e. `Money.java:130-132` → `:131` → the ambient
context [VERIFIED: `ProgressiveEMICalculator.java:176-182`, re-opened here;
`.softhouse/reviews/t43-probe/t43-ambient-sites-output.txt`]. It sits inside
`buildLoanApplicationTerms`, called only from `addFullTermTrancheDisbursement`
[`:155-174`], which is entered only when `isAllowFullTermForTranche()` is true
[`:142-144`].

That is neither "the installment-multiple path" nor "the `multipliedBy(double)` path",
and — this is the load-bearing part — **`allowFullTermForTranche` is a §4.4 *pin*, not
a §3.1 graded-domain predicate.** §3.1's twelve-line block does not mention it. So
§4.1.2's closing sentence, which attributes the exclusion of every remaining site to
*the graded domain*, is false as written. The correct statement is the one the
document already learned to make for `Money.java:50`: the site is real, it is on the
Path-A call graph, and it is excluded **by a pin** — "a materially weaker reason than
'no such site exists'", in revision 8's own words. Revision 8 had to add that caveat
once, from T42; it is missing a second time on the same enumeration.

**The conclusion (P4) still stands, and by observation rather than by the
enumeration.** T42's absence probe gave each shape an uninitialised tenant so any
ambient read throws, and 11 of 13 shapes generated fine; the 2 that threw are
`zeroDpMultiples100` and `zeroDpMultiples100DownPayment`, both 0-decimal-place shapes
that `Currency.MinorUnitDigits == 2` excludes, and both threw at exactly
`MoneyHelper.java:79` ← `Money.roundToMultiplesOf(Money.java:154)` ←
`Money.<init>(Money.java:50)` [VERIFIED:
`.softhouse/capture/mathcontext/analysis/discriminate-output.txt` lines 40–105, read
directly by this review]. So no in-graded-domain Path-A shape reads the ambient
context. **The defect is in the source argument, not in the answer** — and §4.1
explicitly says the source argument is what makes the claim sufficient.

**Money moved: none inside the graded domain.**

**Required change.** Add `Money.java:130-132`, `:224-234` and `:261-267` to the
enumeration in §4.1.2 (and to §4.1's parallel list); name
`ProgressiveEMICalculator.java:182` as the reachable consumer of `:130-132`; and
restate the closing bullet as "every remaining site is excluded either by the graded
domain (§3.1) **or by a §4.4 pin** — `allowFullTermForTranche == false` in the case of
`:182` — the second being the weaker of the two reasons."

---

## 3. P1-T43-3 — M4 does not decide which row an INSTALMENT charge lands on; nothing decides it

**Section:** §4.3.2, the M4 row of the four-rule reconciliation table ("which
repayment row a **CHARGE** lands on — the `feeChargesDue` / `penaltyChargesDue`
columns and `totalDueForPeriod`"), and §9's date-membership obligation, which repeats
it ("which decides **which row a CHARGE lands on**").

**Re-derivation.** All charge attribution goes through one routine:

```java
// ProgressiveLoanScheduleGenerator.java:400-415
private Money getCumulativeAmountOfCharge(..., boolean isFirstPeriod, LoanCharge loanCharge, ...) {
    boolean isDue = loanCharge.isDueInPeriod(periodStart, periodEnd, isFirstPeriod);   // :403  <- M4
    if (loanCharge.isInstalmentFee() && isInstallmentChargeApplicable) {               // :404
        cumulative = calculateInstallmentCharge(principalInterestForThisPeriod, ...);  // :405
    } else if (loanCharge.isOverdueInstallmentCharge() && isDue && ...) { ...          // :406
    } else if (isDue && ...isPercentageBased()) { ...                                  // :408
    } else if (isDue) { ...                                                            // :411
    }
    return cumulative;
}
```

[VERIFIED: `ProgressiveLoanScheduleGenerator.java:400-415`, re-opened in the pinned
checkout; `.softhouse/reviews/t43-probe/t43-charge-membership-output.txt`.]

`isDue` — which is M4 — is computed at `:403` and **is not read by the
`isInstalmentFee()` arm at `:404-405`.** An `INSTALMENT_FEE` charge is therefore applied
to **every** repayment period unconditionally, with no date-membership test of any
kind. M4 governs only the three `isDue`-gated arms: `OVERDUE_INSTALLMENT`,
percentage-based `SPECIFIED_DUE_DATE`, and flat `SPECIFIED_DUE_DATE`.

**Observed, in the corpus revision 8 was written from.** The number of charge-bearing
cells per capture separates the two behaviours cleanly: `FC-02` (flat,
`INSTALMENT_FEE`) moves **12** charge cells — one per repayment row — while `FC-07`
(flat, `SPECIFIED_DUE_DATE`, dated on period 3's due date) moves **1**
[VERIFIED: `.softhouse/reviews/t41-probe/t41-discriminate-output.txt`, "charge cells"
column; corroborated by `.softhouse/capture/charges/out/FULLCELL.md`, 80 vs 8 leaves
moved]. Independently: `FC-15`'s per-instalment fee is 2,500.00 on every one of the
twelve rows while its `SPECIFIED_DUE_DATE` penalty of 7,500.00 appears on period 3
alone [VERIFIED: `.softhouse/capture/charges/out/attested/FC-15-combined-fee-and-penalty-raw.json`,
read directly by this review — period 3 `feeChargesDue` 2,500.00, `penaltyChargesDue`
8,700.00 = 1,200 + 7,500].

**Why this is P1 and not editorial.** §4.3.2 introduces the table with *"A port that
assumes one convention throughout is wrong somewhere"* and calls it *"the one place
they are reconciled"*, and §9 turns it into a standing obligation. A port that later
admits charges and implements the table as written applies M4 to an instalment fee and
puts it on **one** row instead of twelve — on `FC-02`'s shape that is MNT 27,500 of fee
lost on a MNT 1.2 M loan, and it is precisely the class of defect the table exists to
prevent. The document does carry the correcting fact, but only obliquely and in a
different subsection (§4.5.1 fact 4's "twelve roundings summed"), never in the
reconciliation table or the obligation.

**Money moved inside the graded domain: none** — `GenerateRequest` carries no charge.
Money moved for the audience the rule is written for: the whole difference between a
charge on one row and a charge on `NumberOfRepayments` rows.

**Required change.** Qualify M4 in the §4.3.2 table and in §9: M4 decides the row for
`isDue`-gated charges (`SPECIFIED_DUE_DATE`, `OVERDUE_INSTALLMENT`) only; an
`INSTALMENT_FEE` charge bypasses the membership test entirely
[`ProgressiveLoanScheduleGenerator.java:403-405`] and is applied to every repayment
row. Consider stating "no membership test at all" as the fifth convention, since the
table's stated purpose is that a port must not assume one convention throughout.

---

## 4. P2 findings

**P2-T43-1 — C-1's stated progressive semantics omit the down-payment term.**
§4.5.1 says the progressive reading is
`disbursement charges + Σ(principal + interest) + separated specified-due-date percentage charges`.
There is a fourth contributor: `scheduleParams.addTotalRepaymentExpected(downPaymentAmount)`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:345`, inside the
`isDownPaymentEnabled()` branch at `:332-347`]. Inert inside the graded domain
(`DownPaymentPercentage == Rate{0, 1}`), but the sentence is a forward statement about
what a later amendment would carry, and there it is wrong. Add the term.

**P2-T43-2 — two cell counts for one corpus.** The revision-8 history entry credits
T41's model with reproducing "the 15 parity-setting T39 captures (**1,224** cells)",
while §4.1.1 and §8 item 3e say the `periodRatio` reading reproduces "all **1,239**
cells of all 15 parity-setting captures". 1,239 is what T39's own analysis reports and
what its per-capture table sums to (61 × 13 + 115 + 331)
[VERIFIED: `.softhouse/capture/periodratio/analysis/discriminate-output.txt` summary
table, re-summed by this review]. Both figures are presumably right for their own leaf
sets, but the document does not say they are different comparison shapes, and a reader
checking one against the other finds a 15-cell discrepancy. State the leaf set with
each count. (The 4,578 total is arithmetically consistent with the 1,224 figure:
39 + 712 + 776 + 1,224 + 1,827 = 4,578 [VERIFIED: arithmetic]. The same sentence says
"four corpora" and then lists five items; editorial.)

**P2-T43-3 — a stale first-witness cell.** §4.3.1's discriminate table gives the
`n = NumberOfRepayments` reading's first witness as `T37-3c`, cell `R2.principal`. The
revision-8 probe output the table is otherwise sourced from names `T37-3c cell
R2.balance` [VERIFIED: `.softhouse/reviews/t41-probe/t41-discriminate-output.txt`
line 16]. Carried forward unchanged from revision 7. Editorial.

---

## 5. What I checked and found CLEAN

Recorded so silence is distinguishable from not looking.

### 5.1 Citations re-opened in the pinned checkout and found correct

Every one of the following was re-opened by this review, not taken from any prior
review's word. **All correct.**

- **Rate factor and the two senses of `MathContext`:** `ProgressiveEMICalculator.java:1950-1963`
  (`rateFactorByRepaymentPeriod`, the guard at `:1953-1955`, the four `mc` operations
  and the trailing `setScale(mc.getPrecision(), …)` at `:1956-1962`), the second
  occurrence at `:1969-1980` (`:1976-1979`), and `:1922-1927`
  (`rateFactorByRepaymentEveryMonth`, `daysInMonth` → `repaymentPeriodMultiplierInDays`,
  `repaymentEvery` → `repaymentEvery`, exactly as §4.1.1's table says).
- **The two day counts:** `:1367-1368` / `:1369-1370` (interest call site) and
  `:1500-1501` / `:1502-1503` (recurrence call site). Numerator/denominator roles as
  stated; the zero guard at `:1953-1955` returns `BigDecimal.ZERO` before any operation.
- **The multiplier and the days-in-month argument (P0-T34-1, N-1).** `:1404-1413`
  passes `periodRatio` and the literal `BigDecimal.valueOf(30)`; `:1536-1537` passes
  `repaymentEvery` and `daysInMonth`; `daysInMonth` is declared at **`:1508`** (the
  document is right and T39's prose `:1509` is wrong) and is used at exactly one place,
  `:1537`, inside the `case DAYS_30 ->` arm at `:1536` where `:1508`'s ternary yields
  30; `ACTUAL` takes `:1534-1535` and `:1400-1402`; `INVALID` throws at `:1538` and
  `:1415-1416`; and `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` has
  **exactly two** call sites, `:1412` and `:1536` [VERIFIED: `grep -rn` over the whole
  checkout]. **§4.1.1's unconditional narrowing is correct**, and so is its instruction
  that a port must NOT "correct" the second argument.
- **`periodRatio`:** `calculatePeriodRatio` `:1419-1459`, `calculateSeedDate`
  `:1461-1481` with `scheduleModel.getStartDate()` at `:1462` and
  `ProgressiveLoanInterestScheduleModel.java:209-211` confirming that is the first
  repayment period's `FromDate`; both conjuncts of the fall-back at `:1477-1480`; the
  month-end special case at `:1426-1436` with the predicate at `:1432` and the effect
  at `:1433`; the walk at `:1441-1458` with the division at `:1453` as the only
  `MathContext`-rounded operation and the `.add` at `:1454` exact; the whole-period
  return at `:1457-1458`.
- **`getExactDifference` → `ChronoUnit.MONTHS.between`:** `DateUtils.java:308-317`
  (`getExactDifference` → `getDifference` → `unit.between(first, second)`). The
  document's `[UNVERIFIED in this checkout]` tag on the packed formula itself is the
  honest label and is correctly applied.
- **Dates:** `DefaultScheduledDateGenerator.java:168-176` (the re-anchor, exactly the
  Java quoted in §4.2), called at `:130-131`, step at `:128-129`,
  `getRepaymentPeriodDate` at `:311-333`, `fixedLength` at `:62-65` / `:108-111` /
  `:184-188`; the seed is the disbursement date [`LoanApplicationTerms.java:583-589`].
- **Per-period interest:** `InterestPeriod.java:145-158` — the exact-zero guard at
  `:146-148`, the `DECLINING_BALANCE` base at `:151`, and the three separately
  `mc`-rounded operations at `:155`, `:156`, `:157` **in that order**; `getLength`
  `:160-162`; `getLengthTillPeriodDueDate` `:164-166`; `updateOutstandingLoanBalance`
  `:168-188` with the disbursement entering the **later** segment at `:174` and `:186`.
- **Row assembly:** `RepaymentPeriod.java:149` (one interest period by default),
  `:216-217` (growth factor is `reduce(BigDecimal.ONE, BigDecimal::add)`, no
  `MathContext`), `:252-257` + `:264` (sum then one `Money.of`, clamped), `:272-286`
  (memoised `getDueInterest`, `MathUtil.min` cap), `:345-350` (balancing principal),
  `:389-403` with the `negativeToZero` at **`:399`**, `:449-451`
  (`isFirstRepaymentPeriod()` is `previous == null`).
- **The EMI re-adjust loop:** `ProgressiveEMICalculator.java:1258-1308` in full —
  `:1262` counter, `:1265`/`:1307-1308` the `do…while (adjustCounter <= 3)`, `:1266`
  `getEmiAdjustment`, `:1267-1269` guard, `:1270` multiple pass, `:1271-1273`
  break-on-equal, `:1274-1276` deep copy, `:1279-1286` the overwrite set with all four
  conjuncts, `:1287` balances, `:1288` residual, `:1289-1291` the **strict** adoption
  test with the break **before** the copy-back at `:1293-1305`, `:1306`, `:1307`.
  `getEmiAdjustment` `:1778-1789` — the scan `for (idx = size-1; idx > 0; --idx)` at
  `:1779`, the pair at `:1781`/`:1783`, the return at `:1784-1785`, the degenerate
  `copy(0.0)` branch at `:1788`. `getUncountablePeriods` `:2027-2031` with the test
  `originalEmi.isLessThan(totalPaidAmount)`. `EmiAdjustment.java:31-36`
  (`Math.floor(n/2.0)` at `:32`, all three conjuncts at `:33-35`, `copy(lowerHalf)` at
  `:35`), `:38-40`, `:42-44`, `:46-48`, `:54-56`. Call site `:749` gated on
  `onlyOnActualModelShouldApply` (`:733-735`), related list built at `:732`,
  `calculateEMIOnActualModel` at `:741`. **Every line number in §4.3.1's normative
  block is right.**
- **The final-period residual:** `calculateLastUnpaidRepaymentPeriodEMI` `:1160-1219`,
  `diff` at `:1202-1203`, applied at `:1205`, stored at `:1210`.
- **Related periods:** `ProgressiveLoanInterestScheduleModel.java:191-194` (the `null`
  branch this path cannot take), `:195-197` (M2), `getEffectiveRepaymentDueDate`
  `:250-263` with the next-period step at `:252-262`.
- **Membership rules M1/M3/M4:** `LoanRepaymentScheduleProcessingWrapper.java:251-254`
  (`isFirstPeriod ? inclusive : fromExclusiveToInclusive`), reached from
  `ProgressiveLoanInterestScheduleModel.java:238-245` with `period.isFirstRepaymentPeriod()`
  at `:243`; `ProgressiveLoanScheduleGenerator.java:307-308` with the `continue` at
  `:309`; `LoanCharge.java:371-373` and `LoanScheduleParams.java:533-535`
  (`1 == instalmentNumber`), with `instalmentNumber` initialised to 1 at
  `LoanScheduleParams.java:170`/`:204`/`:239` and incremented at `:430`.
- **The M4 staleness mechanism.** Re-derived independently and **confirmed**:
  `applyChargesForCurrentPeriod` runs at `:140`, `incrementInstalmentNumber()` at
  `:143`, so inside the loop `isFirstPeriod()` is true for period 1;
  `updatePeriodsWithCharges` runs at `:154`, **after** the loop at `:116-145`, so
  `isFirstPeriod()` is false for every period at `:479`/`:483`. A separated charge
  dated on period 1's `FromDate` therefore falls outside `(FromDate, DueDate]` and is
  lost. **The mechanism §4.5.1 C-2b gives is exactly right**, and it is correctly
  stated in terms of the first period's `FromDate` rather than only the disbursement
  date, which matters because §3.1 admits `ScheduleStartDate < Disbursements[0].Date`.
- **`totalOutstandingAmount`:** `ProgressiveLoanScheduleGenerator.java:157`, `:159-164`,
  `LoanSchedulePlan.java:43`. Literal `BigDecimal.ZERO`, as stated.
- **Row shapes:** `LoanSchedulePlan.java:52-56` (disbursement row emits
  `principalDisbursed` as **both** principal and outstanding), `:57-65` (down-payment
  row), `LoanSchedulePlanDownPaymentPeriod.java:33`; the down-payment balance formula
  `outstandingBalance.plus(disbursedAmount, mc).minus(downPaymentAmount, mc)` at
  `ProgressiveLoanScheduleGenerator.java:340-343`, and the multiple-rounding call site
  at `:335-338`.
- **`Money` / `MoneyHelper`:** `Money.java:32`, `:42`, `:48-51`, `:50`, `:52`,
  `:102-104`, `:114-116`, `:118-120`, `:150-157`, `:154`, `:159-161`, `:163-170`,
  `:212-222`, `:352-358`, `:372-378`, `:494-496`; `MoneyHelper.java:35`
  (`PRECISION = 19`), `:74-82`, `:91-93`. All correct. §4.1.2's mechanism — `getMc()`
  is an **instance** method and `:52` therefore reads the **threaded** mode whenever one
  was threaded — is correct as re-derived here, and it does predict T39's 0-of-16 /
  15-of-16 split.
- **`LoanChargeValidator.java:59-67`, predicate at `:61`.** The guard is
  `isSpecifiedDueDate() && DateUtils.isBefore(dueDate, disbursementDate)` — **one-sided,
  with no upper bound**, exactly as C-2a says.
- **The seam's dropped components (§2.2).** `LoanApplicationTerms.java:579-607` builds
  through the `Builder`; the private copy constructor `:304-351` copies neither
  `installmentAmountInMultiplesOf` nor `daysInYearCustomStrategy` — nor
  `interestCalculationPeriodMethod`, which §4.4 correctly records as "pinned by
  omission". Verified line by line.

### 5.2 Claims verified against the committed corpus by this review, independently

- **§8's binding: all seven items captured, all seven separate.** Checked item by item
  against `.softhouse/reviews/t41-probe/t41-discriminate-output.txt` and
  `.softhouse/capture/periodratio/analysis/discriminate-output.txt`:
  3 → `T37-3-A`, `T37-3-B`; 3a → `T37-3a` (and only `T37-3a`, a pure discriminator);
  3b → `T37-3b`, `T37-3b-2`; 3c → `T37-3c`, `T37-3c-2`; 3d → `T37-3d`, `T37-3d-2`;
  3e → `T39-P0-A`…`H`; 3f → `T39-ME-A`…`D` **plus** `P-02`, `P-02b`, `T37-3b-2`.
  **T41's claim is true.**
- **415 of 415 / 0 of 415, and 116 of 116 / 0 of 116.** Read directly from T39's
  summary table and re-summed by this review; the 15 parity-setting captures total
  1,239 cells (61 × 13 + 115 + 331) and every one reproduces under the `periodRatio`
  reading. **The disjointness claim is visible in the same table**: every capture has a
  non-zero disagreeing-cell count in exactly one of the two columns and zero in the
  other, on all 15.
- **`totalRepaymentExpected == Σ totalDueForPeriod` fails 15 of 21**, and on `FC-15`
  the gap is exactly MNT 51,900.00: `totalRepaymentExpected` 1,359,988.47 against
  `Σ totalDueForPeriod` 1,411,888.47, computed by this review from the raw capture in
  exact `Decimal`. `totalFeeChargesCharged` 45,000.00 + `totalPenaltyChargesCharged`
  21,900.00 = **66,900.00**, of which only the 15,000.00 disbursement fee reaches the
  total. **Every figure in §4.5.1's C-1 is right.**
- **C-2's premise, verified by digest.** `CTRL-B-01-raw.json`,
  `FC-17-fee-after-final-duedate-raw.json` and `FC-20-pctinterest-sdd-on-disb-raw.json`
  all hash to `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009`
  [VERIFIED: `shasum -a 256`, run by this review]. Byte-identical, so the oracle's
  answer provably carries no information about the charge. §4.5.1's argument that
  §4.6's "reproduce rather than refuse" does not reach this case is sound, and the
  analogy to §3.1's silently-discarded disbursement is exact.
- **T40's control reproduces T36's four Path-B digests byte for byte.** All four
  compared by `shasum -a 256` in this review: `B-01` `713a3560…c062009`,
  `B-02` `9de8757d…d99d02f8`, `B-03` `892dd6f5…f7da58bf`, `B-04` `c80f62b0…65c724a80`,
  identical between `.softhouse/capture/charges/out/control/` and
  `.softhouse/capture/pathb/t36/out/recapture-gerege/`. **The harness is not a
  variable**, as §4.5.1 claims.
- **§4.5.1 fact 4's rounding-locus figures.** 3.75 % of interest is **5,437.06** as a
  per-instalment charge (`FC-04`) and **5,437.07** as a specified-due-date charge
  (`FC-19`); 1.2345 % of amount-plus-interest is **16,603.92** (`FC-05`) against
  **16,603.88** (`FC-21`). Read from the raw captures by this review.
- **T42's absence probe.** 11 of 13 generated fine; the 2 that threw are the two 0-dp
  `inMultiplesOf` shapes, both at `MoneyHelper.java:79` ← `Money.java:154` ←
  `Money.java:50`. §4.1.2's rendering of that result is accurate and does not overstate.

### 5.3 An independent from-text model, and what it settles

`.softhouse/reviews/t43-probe/t43_stepb.py` transcribes **§4.2's step-and-re-anchor and
§4.1.1's steps A, B and C from the document text alone**, in exact integer and
civil-date arithmetic with no float anywhere, and replays it against two committed
captures [VERIFIED: `.softhouse/reviews/t43-probe/t43-stepb-output.txt`]:

- **`T39-ME-B`** (start = disbursement 2024-01-31): my model gives `periodRatio`
  `['1','1','1','1','1','1']` with the special case and `['1','2','1','2','1','2']`
  without it — **exactly T39's observed R2 and R3 vectors.**
- **`T39-P0-A`** (start 2024-01-28, disbursement 2024-01-31): my model derives the
  boundaries `01-28, 02-29, 03-31, 04-30, 05-31, 06-30, 07-31` and the ratios
  `1+1/29, 1+2/31, 1, 1+1/31, 1, 1+1/31` — **exactly the observed
  `1.03448275862068965517, 1.06451612903225806452, 1, 1.03225806451612903226, 1,
  1.03225806451612903226`.**
- **Finding F-1 is independently confirmed.** On all six periods of `T39-ME-B`, the
  packed rule **with** the special case and the clamped-step rule **without** it return
  the identical `k` (0, 1, 0, 3, 0, 5). So the two readings really are
  indistinguishable while the case is present and diverge the instant it is dropped,
  exactly as revision 8 says — and §4.1.1's instruction ("implement the packed rule
  WITH the special case, or the clamped-step rule WITHOUT it") is the right way to
  state it. `MONTHS.between(2024-01-31, 2024-02-29)` is 0 under the packed rule and 1
  under the clamped-step rule, as the document's worked example says [re-derived here;
  the packed formula itself is `[UNVERIFIED in this checkout]`, as revision 8 correctly
  labels it].

**This is the surface T41 got wrong on its first attempt, and revision 8's second
attempt is right.**

### 5.4 Structural claims verified by diff

- **"No type, field set, enum member or graded-domain predicate moves in this
  revision."** `git diff c32d507..HEAD -- nexus/…/contract.go`, filtered to
  non-comment lines, is **empty**: every change in revision 8's `contract.go` is a
  doc-comment change [VERIFIED: run by this review].
- **"§3.1's block is byte-identical to revision 7's."** Diffed directly against
  revision 7 at `c32d507`: **identical** [VERIFIED].
- **"This block and `contract.go`'s are now identical."** Content-identical; the only
  differences are comment-column alignment and `≤` rendered `<=` [VERIFIED:
  `contract.go:902-912`].
- **Is revision 8's new content (charges) inside the domain the predicate admits?**
  **No, and correctly so.** `GenerateRequest` has no charge field, so no request in the
  contract domain carries a charge, and §4.5.1 says exactly that ("neither shape is
  expressible in the contract domain today; C-2 is a forward disposition binding on
  whatever admits charges, not a predicate added to §3.1"). The predicate and the new
  content are consistent.

### 5.5 Surfaces named as least examined — worked and found clean

- **The down-payment path.** `:331-347` re-derived: `Money.zero(currency, mc)` at
  `:331` (threaded), `MathUtil.percentageOf(…, mc)` at `:333-334`, the multiple pass at
  `:335-338`, the row at `:340-343` carrying
  `outstandingBalance + disbursed − downPayment`, `addTotalRepaymentExpected` at `:345`
  and `incrementInstalmentNumber()` at `:346`. §4.5's statement is correct; the only
  gap is P2-T43-1, which is about `totalRepaymentExpected`, not the row.
- **Currency / scale handling.** The single currency-scale rounding point is
  `Money.java:52`, `setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())`,
  guarded by the `inMultiplesOf` branch at `:48-51` which `MinorUnitDigits == 2`
  excludes. §4.3.2 step 1's "sum, then make it money" is exactly
  `RepaymentPeriod.java:252-257` — the `reduce(BigDecimal.ZERO, BigDecimal::add)`
  happens **inside** the `Money.of(...)` argument, so the currency-scale rounding is
  applied once to the sum, not per interest period. Correct as specified.
- **The balance roll-forward and its zero clamp.** Both clamps re-derived:
  `RepaymentPeriod.java:399` (`negativeToZero` on the repayment period's outstanding)
  and `InterestPeriod.java:173`/`:183` (`negativeToZero` on each interest period's
  carried balance). §4.3.2 step 4a's formula matches `:389-403` for a single
  disbursement with nothing paid, and step 4b's sequencing argument (`:132` inside the
  period's own iteration vs `:351` inside `processDisbursements`, called at `:121-122`
  and gated on M3 at `:307-309`) is correct line for line.
- **The `SAME_AS_REPAYMENT_PERIOD` branch.** I opened this expecting a gap and did not
  find one. `calculateRateFactorPerPeriodForInterest` has an early return at
  `:1377-1388` that bypasses `periodRatio`, `daysInYear` and `daysInMonth` entirely
  when `interestCalculationPeriodMethod.isSameAsRepaymentPeriod()`, and the recurrence
  entry point has the same at `:1510-1521`. **§4.9 already states this correctly**,
  including that the two seams agree on `rateFactor` for monthly
  (`30 × RepaymentEvery ÷ 360` ≡ `RepaymentEvery ÷ 12` at the same precision —
  re-derived here and true, since `BigDecimal.divide` rounds by value) and that they
  agree on `rateFactorTillPeriodDueDate` **if and only if
  `periodRatio == RepaymentEvery`**. §4.4's "pinned by omission" entry for
  `interestCalculationPeriodMethod` is correct: the seam's `Builder` never sets it, so
  `:1377`/`:1510` short-circuit on Path A. The Path-A/Path-B asymmetry this creates is
  named, scoped and correct.
- **The per-row cumulative `totalOutstanding` in the plan.** Seeded from
  `totalRepaymentExpected` and decremented per row [`LoanSchedulePlan.java:48-49`,
  `:68`, `:78`], so it inherits C-1's defect. I checked whether §4.5's justification for
  omitting it ("sums or spans over the rows") is falsified by the charge captures: it is
  **not**, because that cumulative field exists only in the `LoanSchedulePlan` shape,
  which only the Path-A seam produces, and Path A can carry no charge. (The Path-B API's
  `totalOutstandingForPeriod` is per-period, not cumulative — verified from `FC-15`.)
  Clean, but worth a line if charges ever reach the plan shape.
- **The four membership rules, checked for a fifth and for cross-talk.** M1↔M3 disagree
  on exactly one date, as stated, and the document reconciles them. M2 is a filter
  rather than a date-membership rule in the same sense, but it carries its own predicate
  and citation and is not confusable. `isInPeriodFromInclusiveToExclusive`
  [`LoanRepaymentScheduleProcessingWrapper.java:256-258`] is a genuinely different
  predicate but is reached only from `ProgressiveEMICalculator.java:162`, on the
  `allowFullTermForTranche` arm §4.4 pins false. The one real gap is P1-T43-3.

---

## 6. What this review did NOT do

- **No oracle contact of any kind.** No container, no Gradle, no HTTP. Every
  observation is quoted from a committed capture with its id and, where I re-computed
  it, from the raw JSON read directly.
- **No full-corpus replay.** I built a from-text model of §4.2 + §4.1.1 only (steps A–C
  and the re-anchor) and replayed it against two captures. I did **not** rebuild the
  whole schedule pipeline. Per T41's own F-1, full-corpus reproduction proves little,
  so the budget went to re-derivation from source and to the shapes that discriminate.
- **I did not audit the captures against the live oracle.** That is T44's task this
  fire. Where I verified a capture I verified it against *itself* (digests, arithmetic
  between committed fields) or against the pinned source, never against the oracle.
- **`Money.java:224-234` and `:261-267` reachability.** I established that both read the
  ambient context and that neither is in the document's enumeration. I did **not**
  establish whether either is reached from the progressive calculator; T42's absence
  probe says no in-graded-domain shape reads the ambient context at all, which settles
  the conclusion but not the reachability question for those two lines specifically.
  `[UNVERIFIED: reachability of Money.java:224-234 and :261-267 on the Path-A call graph]`
- **The cumulative generator is still unobserved.** My P1-T43-1 re-derivation of
  `AbstractCumulativeLoanScheduleGenerator.java:352`/`:392` is from source only; §8 item
  9(d) already records that the cumulative side has no capture, and that remains true.
  `[UNVERIFIED by observation]`

---

## 7. Note for the driver

The three P1s are all of one kind: **a sentence is right and the evidence pinned under
it is not.** None changes a number a Go port must produce inside the Run-1 graded
domain; none touches `contract.go`; none is rejection-grade. If the driver ratifies on
this review, the corrections belong in a revision-9 erratum that reopens no decision —
and P1-T43-3 in particular should be carried, because it is the one that would mis-price
a future charge-bearing port, and §9 has already turned M4 into a standing obligation.
