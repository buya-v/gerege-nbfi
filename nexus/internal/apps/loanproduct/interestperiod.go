package loanproduct

import (
	"math/big"
	"time"
)

// CITATION AUDIT — T532, swept 2026-09-05 against pinned Fineract
// 426a23544e8426a38ae43ae404670a0a7e85b9eb; RECORD CORRECTED by T551 on
// 2026-09-06 after independent review T548, against the same commit.
//
// InterestPeriod.java is 237 lines at that commit. Every [VERIFIED:
// InterestPeriod.java:a-b] span in this file was re-derived INDIVIDUALLY, by
// brace-counting the Java class body with comments and string literals stripped
// first, not by grep and not by applying an offset. 28 citations were found
// mechanically; 22 named the wrong lines and were repointed; 6 already resolved
// exactly and were left untouched.
//
// THERE IS NO OFFSET, and no future sweep should look for one. THE REASON FIRST
// RECORDED HERE WAS FALSE AND IS RETRACTED: this banner used to say the error
// "CHANGES SIGN across the file" and quote a range of "-94 to +69". It does not
// change sign. Re-derived as new_start - old_start over the pre-sweep file,
// EVERY InterestPeriod.java delta is <= 0:
//
//	-94  the eight nullToZero accessors  :299 :303 :307 :311 :315 :319 :323 :327
//	                                  ->  :205 :209 :213 :217 :221 :225 :229 :233
//	-69  getLength                       :229 -> :160
//	-69  getLengthTillPeriodDueDate      :233 -> :164
//	-69  updateOutstandingLoanBalance    :237 -> :168
//	-63  getCreditedAmounts              :256 -> :193
//	-59  getCalculatedDueInterest()      :193 -> :134
//	-58  getCalculatedDueInterest(m,len) :203 -> :145
//	-55  isFirstInterestPeriod           :252 -> :197
//	-52  the five add* mutators     :165 :169 :173 :177 :181 -> :113 :117 :121 :125 :129
//	 -3  the field block                 :48  -> :45
//	  0  withEmptyAmounts                :94  -> :94  (start held; only the end moved, 109 -> 106)
//
// Min -94, max 0, NO POSITIVE VALUE ANYWHERE. The single +13 the old wording
// folded into this table (:175 -> :188) is a MathUtil.java citation — A DIFFERENT
// FILE — and is not evidence about drift inside InterestPeriod.java. Mixing two
// files' deltas into one table is how the false claim was manufactured.
//
// THE CONCLUSION SURVIVES THE PREMISE, and this is the part to keep. No single
// offset explains this file, because the magnitudes range over 0, -3, -52, -55,
// -58, -59, -63, -69 and -94 and are non-monotonic in file order. An offset is
// defeated by SPREAD and non-monotonicity, not by a sign change. T530's
// refutation of T526's "12-14 line offset" therefore still stands, unaffected.
// A single citation past the end of the file remains sufficient evidence that its
// block was never derived against this commit; the remedy is to read each range,
// never to shift a block.
//
// THE 22 WRONG CITATIONS PARTITION EXACTLY. A closed partition is far stronger
// evidence than a list, because a list can silently omit a class and a closing
// sum cannot (T548 derived this; T551 re-derived it independently at 426a23544):
//
//	22 = 10 (wholly past EOF) + 1 (overrun) + 9 (real but WRONG MEMBER) + 2 (in file, wrong extent)
//
//	10 past EOF  :252-254 :256-259 :299-301 :303-305 :307-309 :311-313 :315-317
//	             :319-321 :323-325 :327-329        — all beyond line 237
//	 1 overrun   :237-250                          — :237 is the class's closing
//	                                                 brace; 238-250 do not exist
//	 9 wrong     :229-231  getRateFactor()
//	   member    :233-235  getRateFactorTillPeriodDueDate()
//	             :193-201  getCreditedAmounts 193-195 + isFirstInterestPeriod
//	                       197-199 + getCurrency() signature 201
//	             :203-219  getCurrency() close 203 + getCreditedPrincipal 205-207
//	                       + getCreditedInterest 209-211 + getDisbursementAmount
//	                       213-215 + getBalanceCorrectionAmount 217-219
//	             :165-167  tail of getLengthTillPeriodDueDate
//	             :169-171  head of updateOutstandingLoanBalance
//	             :173-175  body of updateOutstandingLoanBalance
//	             :177-179  body/close of updateOutstandingLoanBalance
//	             :181-183  else-branch of updateOutstandingLoanBalance
//	 2 extent    :48-60    a TRUNCATED field block (the block is :45-73)
//	             :94-109   both withEmptyAmounts overloads PLUS the head of
//	                       compareTo at :108-109
//
// THE WRONG-MEMBER CLASS IS THE DANGEROUS ONE, AND THE SWEEP BUILT TO FIND IT
// UNDER-COUNTED IT 4.5x. T532 reported TWO (:229-231, :233-235); there are NINE.
// The two reported are the two that happen to span a COMPLETE method — a
// narrowing T532 never states. All nine land wholly inside the 237-line file on a
// real member that is not the one the Go sentence above them describes, so a
// line-existence check passes on every one of them and an offset theory hides all
// nine. All nine were nevertheless corrected correctly and no number moved; what
// was wrong is the COUNT, checked in wearing a verified badge. Count this class
// by "does the span resolve to the member named above it", never by "is the span
// a whole method".
//
// NO RANGE WAS REPOINTED TO MAKE A MISMATCH DISAPPEAR. At every corrected span
// the Java supports the Go sentence above it, so this sweep records zero
// DIVERGENCE blocks. Three oracle asymmetries were checked and found benign;
// two of the three receipts were REWRITTEN by T551 because the mechanism they
// named was wrong (see UpdateOutstandingLoanBalance and AddBalanceCorrectionAmount
// below) — they are noted at their sites rather than silently smoothed over.
//
// Citations to files OTHER than InterestPeriod.java were NOT swept here. FOUR
// non-InterestPeriod files have had cited spans read directly: DateUtils and
// MathUtil (T532; MathUtil's four spans re-read by T551), Money.java (T532 added
// :236-238; T551 re-read it and added :40-53, :106-108, :126-128, :240-247,
// :253-259, :324-326, :442-448) and MoneyHelper.java (T551, :35 and :91-93). The
// old wording — "only the two that sit in this file's own prose (DateUtils,
// MathUtil)" — undercounted what had been checked. EVERY OTHER cited file
// remains UNAUDITED, and there are SEVEN of them, not the four the old
// enumeration named: RepaymentPeriod (unaudited except the single span :190-194
// that T551 read for the balance-correction receipt), ProgressiveEMICalculator,
// AdvancedPaymentScheduleTransactionProcessor (except :2845, likewise),
// LoanSchedulePlan, ProgressiveLoanScheduleGenerator,
// ProgressiveLoanInterestScheduleModel and
// InterestScheduleModelRepositoryWrapperImpl. Half-auditing a second file is the
// defect this task exists to repair, so they were left alone and filed instead.

// daysBetween returns the calendar-day difference between two dates using the
// same LocalDate epoch-day arithmetic DateUtils.getDifferenceInDays uses
// [VERIFIED: DateUtils.java:319-321], which delegates to
// DateUtils.getDifference(first, second, DAYS) and so evaluates
// DAYS.between(first, second) [VERIFIED: DateUtils.java:308-313]. The result
// is second - first, so a span that opens on first and closes on second has a
// positive length.
func daysBetween(first, second time.Time) int64 {
	return int64(dateOnly(second).Sub(dateOnly(first)) / (24 * time.Hour))
}

// dateOnly truncates a time.Time to its calendar date in UTC, matching the
// day-count convention used across the port (see nexus/internal/apps/loan).
func dateOnly(t time.Time) time.Time {
	y, m, d := t.Date()
	return time.Date(y, m, d, 0, 0, 0, 0, time.UTC)
}

// InterestPeriod is the Go port of Fineract's
// portfolio.loanproduct.calc.data.InterestPeriod: one segment of a repayment
// period over which a rate factor, an outstanding balance and the credited
// amounts are carried and recomputed after a transaction.
//
// [VERIFIED: InterestPeriod.java:45-73 for the field list] — the whole class
// body field block, from the @JsonExclude'd repaymentPeriod at :45-46 to
// isPaused at :72-73. The Java carries thirteen fields; this struct carries
// fourteen because the oracle's single MathContext field mc (:68-70) is split
// into rounding, and currency is the oracle's getCurrency() (:201-203, which
// reads getRepaymentPeriod().getCurrency()) hoisted to a field. That hoist is
// behaviour-preserving only while a model's currency is fixed after
// construction, which it is on every path in this package.
//
// It is the recomputation counterpart of the schedule GENERATOR's interest
// period: the generator in nexus/internal/apps/loanschedule builds a schedule
// from scratch, while this value object recomputes the due-interest, due-
// principal and outstanding-balance cells of an ALREADY-BUILT schedule after a
// repayment, disbursement, charge-back or interest-rate change.
type InterestPeriod struct {
	repaymentPeriod *RepaymentPeriod

	// FromDate and DueDate bound the segment.
	FromDate time.Time
	DueDate  time.Time

	// RateFactor and RateFactorTillPeriodDueDate are the segment's rate
	// factors, carried as exact rationals. A nil value is the oracle's null
	// BigDecimal and reads as zero.
	RateFactor                  *big.Rat
	RateFactorTillPeriodDueDate *big.Rat

	creditedPrincipal  Money
	creditedInterest   Money
	disbursementAmount Money

	// balanceCorrectionAmount and outstandingLoanBalance are NOT LEDGER
	// BALANCES, on two legs set out in doc.go, "THE TEST THAT DECIDES IT: TWO
	// LEGS". LEG 1, PARITY: the segment cell is a SWEPT SNAPSHOT the oracle
	// deliberately reads stale, so I-3's remedy "derive by summation" CHANGES
	// THE MONEY here — TestOutstandingLoanBalanceIsASweptSnapshot executes that
	// claim. LEG 2, REACHABILITY: neither cell reaches a journal entry, a GL
	// posting, or a column any aggregate reads as an account balance; the
	// forward trace terminates in DTOs and the calc package emits no journal
	// entry at all.
	//
	// TWO ARGUMENTS THAT DO NOT WORK, both tried here and both retired; doc.go
	// carries the counterexamples. (i) "It never becomes a database column" —
	// false: both cells ARE serialised into m_loan_progressive_model.json_model
	// (no @JsonExclude on InterestPeriod.java:65-66) and ARE read back as
	// starting state [VERIFIED: InterestScheduleModelRepositoryWrapperImpl.java:95,
	// :110-128]. (ii) "There is no posting stream behind it" — also false, and
	// refuted by UpdateOutstandingLoanBalance itself, which folds the previous
	// period's PaidPrincipal [VERIFIED: InterestPeriod.java:178], a quantity the
	// transaction processor accumulates from real LoanTransactions.
	//
	// balanceCorrectionAmount is a SIGNED DELTA applied to the schedule's
	// principal projection; the oracle only ever adds a negated amount to it
	// [VERIFIED: ProgressiveEMICalculator.java:907, :922, :946, :952, :1124,
	// :1129]. It is a summand of the roll-forward below, exactly like
	// disbursementAmount and capitalizedIncomePrincipal.
	//
	// outstandingLoanBalance is the principal base of THIS SEGMENT's
	// declining-balance interest arithmetic and nothing else
	// [VERIFIED: InterestPeriod.java:151]. Downstream it reaches only DTOs —
	// RepaymentPeriod.java:389-403 -> ProgressiveLoanScheduleGenerator.java:132
	// -> LoanScheduleModelRepaymentPeriod, and LoanSchedulePlan.java:65, :77.
	// No journal entry, no GL account, no posting. It is also a SWEPT SNAPSHOT,
	// refreshed only by UpdateOutstandingLoanBalance below; between sweeps the
	// oracle deliberately leaves it stale, so it is not equivalent to an
	// on-demand derivation and must not be replaced by one.
	balanceCorrectionAmount    Money
	outstandingLoanBalance     Money
	capitalizedIncomePrincipal Money

	rounding Rounding
	currency Currency

	// Paused mirrors InterestPeriod.isPaused.
	Paused bool
}

func (ip *InterestPeriod) zero() Money { return moneyZero(ip.currency, ip.rounding) }

// CreditedPrincipal returns creditedPrincipal, zero when absent
// [VERIFIED: InterestPeriod.java:205-207].
//
// The oracle reaches zero with MathUtil.nullToZero(field, getCurrency(),
// getMc()); this port reaches it by construction instead — every constructor in
// this file seeds all six Money cells with moneyZero — because Money is a value
// type here and the field cannot be null once built. Same observable, different
// mechanism. The six accessors below share this note.
func (ip *InterestPeriod) CreditedPrincipal() Money { return ip.creditedPrincipal }

// CreditedInterest returns creditedInterest, zero when absent
// [VERIFIED: InterestPeriod.java:209-211].
func (ip *InterestPeriod) CreditedInterest() Money { return ip.creditedInterest }

// DisbursementAmount returns disbursementAmount, zero when absent
// [VERIFIED: InterestPeriod.java:213-215].
func (ip *InterestPeriod) DisbursementAmount() Money { return ip.disbursementAmount }

// BalanceCorrectionAmount returns balanceCorrectionAmount, zero when absent
// [VERIFIED: InterestPeriod.java:217-219].
func (ip *InterestPeriod) BalanceCorrectionAmount() Money { return ip.balanceCorrectionAmount }

// OutstandingLoanBalance returns outstandingLoanBalance, zero when absent
// [VERIFIED: InterestPeriod.java:221-223].
func (ip *InterestPeriod) OutstandingLoanBalance() Money { return ip.outstandingLoanBalance }

// CapitalizedIncomePrincipal returns capitalizedIncomePrincipal, zero when absent
// [VERIFIED: InterestPeriod.java:225-227].
func (ip *InterestPeriod) CapitalizedIncomePrincipal() Money { return ip.capitalizedIncomePrincipal }

// RateFactorValue returns the segment's own rate factor, zero when null
// [VERIFIED: InterestPeriod.java:229-231].
func (ip *InterestPeriod) RateFactorValue() *big.Rat {
	if ip.RateFactor == nil {
		return new(big.Rat)
	}
	return ip.RateFactor
}

// RateFactorTillPeriodDueDateValue returns the rate factor measured to the
// enclosing repayment period's due date, zero when null
// [VERIFIED: InterestPeriod.java:233-235].
func (ip *InterestPeriod) RateFactorTillPeriodDueDateValue() *big.Rat {
	if ip.RateFactorTillPeriodDueDate == nil {
		return new(big.Rat)
	}
	return ip.RateFactorTillPeriodDueDate
}

// Length returns the segment length in days [VERIFIED: InterestPeriod.java:160-162].
//
// The previous span here, :229-231, resolved to a real method — but to
// getRateFactor(), not getLength(). A citation that lands on the wrong member is
// harder to catch than one past EOF, because it still resolves. This is one of
// NINE such citations in the pre-sweep file, not one of two: the banner above
// lists all nine and shows the 22 partitioning as 10 + 1 + 9 + 2.
func (ip *InterestPeriod) Length() int64 {
	return daysBetween(ip.FromDate, ip.DueDate)
}

// LengthTillPeriodDueDate returns the day span from the segment's from-date to
// the ENCLOSING repayment period's due date
// [VERIFIED: InterestPeriod.java:164-166]. The previous span, :233-235,
// resolved to getRateFactorTillPeriodDueDate() — again a real but wrong member.
func (ip *InterestPeriod) LengthTillPeriodDueDate() int64 {
	return daysBetween(ip.FromDate, ip.repaymentPeriod.DueDate)
}

// IsFirstInterestPeriod reports whether this is the repayment period's first
// interest period [VERIFIED: InterestPeriod.java:197-199].
func (ip *InterestPeriod) IsFirstInterestPeriod() bool {
	return ip == ip.repaymentPeriod.FirstInterestPeriod()
}

// CalculatedDueInterest returns the raw due-interest for the segment before it
// is wrapped in Money, following the oracle's getCalculatedDueInterest
// [VERIFIED: InterestPeriod.java:134-143]. A paused or re-aged period returns
// its credited interest unchanged; otherwise the credited interest is added to
// the period's interest due at the repayment due date and floored at zero.
func (ip *InterestPeriod) CalculatedDueInterest() *big.Rat {
	if ip.Paused || ip.repaymentPeriod.ReAged {
		return ip.CreditedInterest().major()
	}
	lengthTill := ip.LengthTillPeriodDueDate()
	interestDueTillRepaymentDueDate := ip.CalculatedDueInterestFor(
		ip.repaymentPeriod.InterestMethod(), lengthTill)
	return ratNegativeToZero(roundSignificant(
		new(big.Rat).Add(ip.CreditedInterest().major(), interestDueTillRepaymentDueDate),
		ip.rounding.Precision, ip.rounding.Mode))
}

// CalculatedDueInterestFor is getCalculatedDueInterest(method, lengthTillPeriodDueDate)
// [VERIFIED: InterestPeriod.java:145-158]: the three separately
// MathContext-rounded operations that turn the base amount into interest.
//
//	baseAmount * rateFactorTillPeriodDueDate / lengthTill * length
//
// A zero lengthTill returns exactly zero before any operation runs. FLAT reads
// the disbursed-and-capitalized total; DECLINING_BALANCE reads the outstanding
// balance.
func (ip *InterestPeriod) CalculatedDueInterestFor(method InterestMethod, lengthTillPeriodDueDate int64) *big.Rat {
	if lengthTillPeriodDueDate == 0 {
		return new(big.Rat)
	}
	var baseAmount *big.Rat
	switch method {
	case InterestFlat:
		baseAmount = ip.repaymentPeriod.
			calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod(ip).major()
	case InterestDecliningBalance:
		baseAmount = ip.OutstandingLoanBalance().major()
	default:
		panic("loanproduct: method not implemented: " + method.String())
	}

	v := roundSignificant(new(big.Rat).Mul(baseAmount, ip.RateFactorTillPeriodDueDateValue()),
		ip.rounding.Precision, ip.rounding.Mode)
	v = roundSignificant(new(big.Rat).Quo(v, new(big.Rat).SetInt64(lengthTillPeriodDueDate)),
		ip.rounding.Precision, ip.rounding.Mode)
	return roundSignificant(new(big.Rat).Mul(v, new(big.Rat).SetInt64(ip.Length())),
		ip.rounding.Precision, ip.rounding.Mode)
}

// ratNegativeToZero is MathUtil.negativeToZero over a bare BigDecimal: a value
// that is not greater than zero becomes ZERO
// [VERIFIED: MathUtil.java:188-190]. The previous span, :175-178, named
// MathUtil.nullToZero(BigDecimal) — a different method with different
// semantics. The sentence above was right; only the span was wrong.
func ratNegativeToZero(x *big.Rat) *big.Rat {
	if x.Sign() <= 0 {
		return new(big.Rat)
	}
	return x
}

// UpdateOutstandingLoanBalance rolls the previous segment's (or previous
// repayment period's) balance forward into this segment
// [VERIFIED: InterestPeriod.java:168-188].
//
// The first segment of a period seeds its balance from the previous period's
// last segment, subtracting the previous period's due principal and adding back
// its paid principal; a later segment seeds from the immediately preceding
// segment in the same period.
//
// ORACLE ASYMMETRY, CHECKED AND BENIGN: the first branch floors with the
// two-argument MathUtil.negativeToZero(Money, mc) at :173-178, the second with
// the one-argument MathUtil.negativeToZero(Money) at :183-186. Both call-site
// spans are correct as cited.
//
// THE MECHANISM AS FIRST WRITTEN HERE WAS WRONG AND IS RETRACTED (T551, review
// T548). It said the MathContext "only ever reaches the ZERO that is substituted
// for a negative value, never the value that is kept." It also reaches the
// PREDICATE. The two-argument form is
// `value == null || isGreaterThanZero(value, mc) ? value : Money.zero(value.getCurrencyData(), mc)`
// [VERIFIED: MathUtil.java:356-358], and isGreaterThanZero(Money, MathContext)
// [VERIFIED: MathUtil.java:368-370] delegates to Money.isGreaterThanZero(mc)
// [VERIFIED: Money.java:446-448]; the one-argument form instead uses the value's
// OWN mc [VERIFIED: MathUtil.java:351-353 -> Money.java:442-444].
//
// The conclusion holds anyway, on the mechanism rather than on the retracted
// wording: the predicate is isGreaterThan(Money.zero(getCurrencyData(), mc))
// [VERIFIED: Money.java:446-448], and Money.zero(CurrencyData, mc) constructs
// BigDecimal.ZERO [VERIFIED: Money.java:126-128], whose amount after the
// constructor's setScale is zero under EVERY rounding mode and every precision
// [VERIFIED: Money.java:40-53]. Both overloads therefore compare against the same
// zero and floor at the same zero, so negToZero below serves both branches.
//
// THE TWO ASSIGNMENTS BELOW ARE NOT LEDGER-BALANCE WRITES, and they are the
// reason the I-3 source guard refuses this package. The sites are left RED
// deliberately; nothing here was renamed to clear the bar.
//
// WHY THEY ARE NOT LEDGER-BALANCE WRITES — LEG 1, PARITY, and it is the
// load-bearing leg. I-3's remedy is "derive by summation over the postings."
// Applied to THIS cell that remedy CHANGES THE MONEY, because the cell is a
// swept snapshot the oracle deliberately reads stale; the mechanism is set out
// immediately below and TestOutstandingLoanBalanceIsASweptSnapshot executes it.
// A repair that moves numbers away from the reference oracle is not a repair.
//
// LEG 2, REACHABILITY: this value reaches no ledger balance to be one. Its whole
// downstream reach is InterestPeriod.java:151 (the declining-balance interest
// base) -> RepaymentPeriod.java:389-403 ->
// ProgressiveLoanScheduleGenerator.java:132 -> LoanScheduleModelRepaymentPeriod
// and LoanSchedulePlan.java:65, :77 — all DTOs, none carrying @Entity, @Table or
// @Column. No journal entry, no GL account, no posting anywhere on that path,
// and the calc package emits none at all.
//
// DO NOT SUBSTITUTE EITHER RETIRED ARGUMENT FOR THOSE. "It never becomes a
// column" is false, and so is "there is no posting stream": the expression below
// folds previous.PaidPrincipal() [VERIFIED: InterestPeriod.java:178], which
// ProgressiveEMICalculator.payPrincipal accumulates from real LoanTransactions
// [VERIFIED: RepaymentPeriod.java:405-407; ProgressiveEMICalculator.java:421;
// AdvancedPaymentScheduleTransactionProcessor.java:929, :967, :2912]. doc.go
// carries both counterexamples in full.
//
// LEG 1's MECHANISM: the cell cannot simply be derived on read.
//
// This function is the WHOLE refresh mechanism. The oracle calls it only from
// explicit sweeps [VERIFIED: ProgressiveEMICalculator.java:1254-1256, and the
// per-repayment-period sweeps at :1647, :1654 and :1667], and it deliberately
// leaves the cell unrefreshed in between — RepaymentPeriod.copyWithoutPaidAmounts
// zeroes each copied segment's balanceCorrectionAmount, which is a summand of
// the expression below, and does NOT re-run this function
// [VERIFIED: RepaymentPeriod.java:173-198]. So the value read between two sweeps
// is, by construction, not the value this expression would produce if evaluated
// at that moment. Turning the cell into an on-demand derivation would change the
// numbers at every such point, which is a parity break, not a repair.
//
// This is the opposite of RepaymentPeriod's derived cells: those carry an oracle
// Memo with an invalidation key, are observationally inert, and are therefore
// recomputed on every read by this port (see repaymentperiod.go). This cell has
// no invalidation key and is observationally live.
func (ip *InterestPeriod) UpdateOutstandingLoanBalance() {
	if ip.IsFirstInterestPeriod() {
		previous := ip.repaymentPeriod.Previous()
		if previous != nil {
			previousInterestPeriod := previous.LastInterestPeriod()
			ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().
				plus(previousInterestPeriod.DisbursementAmount()).
				plus(previousInterestPeriod.CapitalizedIncomePrincipal()).
				plus(previousInterestPeriod.BalanceCorrectionAmount()).
				minus(previous.DuePrincipal()).
				plus(previous.PaidPrincipal()).negToZero()
		}
		return
	}
	index := ip.repaymentPeriod.interestPeriodIndex(ip)
	previousInterestPeriod := ip.repaymentPeriod.InterestPeriods[index-1]
	ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().
		plus(previousInterestPeriod.BalanceCorrectionAmount()).
		plus(previousInterestPeriod.CapitalizedIncomePrincipal()).
		plus(previousInterestPeriod.DisbursementAmount()).negToZero()
}

// CreditedAmounts is the principal-like total: disbursement + credited
// principal + capitalized income principal [VERIFIED: InterestPeriod.java:193-195].
//
// The oracle folds these with MathUtil.plus(mc, disbursement, creditedPrincipal,
// capitalizedIncomePrincipal), a left fold in exactly that argument order
// [VERIFIED: MathUtil.java:404-410]; the chain below reproduces the order.
func (ip *InterestPeriod) CreditedAmounts() Money {
	return ip.DisbursementAmount().
		plus(ip.CreditedPrincipal()).
		plus(ip.CapitalizedIncomePrincipal())
}

// AddBalanceCorrectionAmount mutates balanceCorrectionAmount by adding the
// supplied amount [VERIFIED: InterestPeriod.java:113-115].
//
// ORACLE ASYMMETRY, CHECKED AND BENIGN: this is the ONE add* method whose Java
// body calls the two-argument MathUtil.plus(Money, Money) [VERIFIED:
// MathUtil.java:388-390]; its four siblings all pass getMc() to the
// three-argument overload [VERIFIED: MathUtil.java:392-394].
//
// THE FIRST RECEIPT WRITTEN HERE WAS UNSOUND AND IS RETRACTED (T551, review
// T548). It argued that the receiver "is this.getBalanceCorrectionAmount(),
// built with getMc() at :217-219." IT IS NOT BUILT WITH getMc(). That accessor
// is MathUtil.nullToZero(balanceCorrectionAmount, getCurrency(), getMc())
// [VERIFIED: InterestPeriod.java:217-219], which is
// nullToDefault(value, Money.zero(currency, mc)) [VERIFIED: MathUtil.java:338-340]
// over a bare `return value == null ? def : value` [VERIFIED:
// MathUtil.java:342-344]. getMc() reaches ONLY the substituted zero. When the
// field is non-null the accessor hands back the STORED Money, carrying whatever
// MathContext it was constructed with — and non-null is exactly what the guarded
// oracle call site reaches: RepaymentPeriod.copyWithoutPaidAmounts copies the
// interest period, then calls this method only inside
// `if (!interestPeriodCopy.getBalanceCorrectionAmount().isZero())`
// [VERIFIED: RepaymentPeriod.java:190-194]. The one step the old receipt leaned
// on is the one step that does not hold, and a money claim must never rest on an
// argument shown to be wrong — so it is replaced, not patched.
//
// THE SOUND RECEIPT. It needs no assumption about which MathContext the receiver
// carries, because on this path the MathContext's PRECISION never participates
// at all. Following the two-argument form to the bottom:
//
//	MathUtil.plus(Money, Money)  -> first.plus(second)          [VERIFIED: MathUtil.java:388-390]
//	Money.plus(Money)            -> plus(that, getMc())         [VERIFIED: Money.java:236-238]
//	Money.plus(Money, mc)        -> plus(that.getAmount(), mc)  [VERIFIED: Money.java:240-247]
//	Money.plus(BigDecimal, mc)   -> this.amount.add(amountToAdd), with NO MathContext
//	                                argument, then Money.of(currency, sum, mc)
//	                                                            [VERIFIED: Money.java:253-259]
//	Money.of(CurrencyData, BigDecimal, mc) -> new Money(...)    [VERIFIED: Money.java:106-108]
//	private Money(currency, amount, mc) -> amount.setScale(currency.getDecimalPlaces(),
//	                                getMc().getRoundingMode())  [VERIFIED: Money.java:40-53]
//
// The addition is EXACT BigDecimal arithmetic. The mc reaches one place only —
// the rounding mode of that single setScale — and there it cannot bite: every
// Money's amount was itself set to currency scale by that same constructor line,
// so the sum of two amounts at that scale is already at that scale and the
// setScale is a no-op. No rounding occurs, so a difference in rounding mode could
// not move the number even if one existed, and a difference in precision could
// not reach the arithmetic at all. That is why the two-argument and three-
// argument forms agree here, and why the exact minor-unit addition below matches
// all five siblings. (The no-op step assumes both operands carry the same
// CurrencyData decimalPlaces; Money.isSameCurrency compares only the currency
// CODE [VERIFIED: Money.java:324-326], and a single schedule model carries a
// single currency, so they do on every path in this package.)
//
// SECONDARY, AND DELIBERATELY HEDGED — do not promote it to load-bearing. In
// production every MathContext in this object graph is one memoised per-tenant
// instance: mathContextCache.computeIfAbsent(tenantId, k -> new
// MathContext(PRECISION, getRoundingMode())) with PRECISION a compile-time 19
// [VERIFIED: MoneyHelper.java:35, :91-93], so at the ratified tenant setting
// (19, HALF_UP) the receiver's mc and getMc() are the SAME OBJECT. That is a
// configuration fact, NOT a structural guarantee: fineract-progressive-loan does
// construct a MathContext that is not the cached one — `new
// MathContext(MoneyHelper.getMathContext().getPrecision(), RoundingMode.DOWN)`
// [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:2845]. Whether a
// Money carrying that context can reach this receiver was NOT established
// [UNVERIFIED]. The structural argument above does not depend on the answer.
//
// This asymmetry is recorded, not smoothed over: it is a real difference in the
// oracle's source that a reader of this port would otherwise have to rediscover.
//
// NOT A LEDGER-BALANCE WRITE, and left RED deliberately. LEG 2, REACHABILITY:
// this cell reaches no journal entry, no GL posting and no column any aggregate
// reads as an account balance — it is a summand of UpdateOutstandingLoanBalance's
// roll-forward, whose own reach terminates in DTOs. LEG 1, PARITY: the segment
// balance this summand feeds is a swept snapshot, so deriving it on read changes
// the numbers. See doc.go, "THE TEST THAT DECIDES IT: TWO LEGS".
//
// DO NOT restate this as "there is no posting stream behind it." That argument
// is retired and doc.go says why: at two of the six call sites below the amount
// added IS a negated paid principal, and paid principal is accumulated from real
// LoanTransactions [VERIFIED: ProgressiveEMICalculator.java:922, :952].
//
// balanceCorrectionAmount is a SIGNED DELTA, not a balance: every oracle caller
// adds a NEGATED amount to it
// [VERIFIED: ProgressiveEMICalculator.java:907, :922, :946, :952, :1124, :1129;
// RepaymentPeriod.java:192-194; ProgressiveLoanInterestScheduleModel.java:257,
// :290] — a claim about SIGN DISCIPLINE, never about provenance. It is one
// summand of UpdateOutstandingLoanBalance's roll-forward above,
// structurally identical to disbursementAmount and capitalizedIncomePrincipal,
// whose Add* methods the I-3 guard does not flag. This one is flagged because
// its name contains the substring "balance" — see doc.go.
func (ip *InterestPeriod) AddBalanceCorrectionAmount(additional Money) {
	ip.balanceCorrectionAmount = ip.BalanceCorrectionAmount().plus(additional)
}

// AddDisbursementAmount mutates disbursementAmount by adding the supplied amount
// [VERIFIED: InterestPeriod.java:117-119].
func (ip *InterestPeriod) AddDisbursementAmount(additional Money) {
	ip.disbursementAmount = ip.DisbursementAmount().plus(additional)
}

// AddCreditedPrincipalAmount mutates creditedPrincipal by adding the supplied
// amount [VERIFIED: InterestPeriod.java:121-123].
func (ip *InterestPeriod) AddCreditedPrincipalAmount(additional Money) {
	ip.creditedPrincipal = ip.CreditedPrincipal().plus(additional)
}

// AddCreditedInterestAmount mutates creditedInterest by adding the supplied
// amount [VERIFIED: InterestPeriod.java:125-127].
func (ip *InterestPeriod) AddCreditedInterestAmount(additional Money) {
	ip.creditedInterest = ip.CreditedInterest().plus(additional)
}

// AddCapitalizedIncomePrincipalAmount mutates capitalizedIncomePrincipal by
// adding the supplied amount [VERIFIED: InterestPeriod.java:129-132] — four
// lines in the oracle, not three like its siblings, because the getMc() argument
// wraps onto :131.
func (ip *InterestPeriod) AddCapitalizedIncomePrincipalAmount(additional Money) {
	ip.capitalizedIncomePrincipal = ip.CapitalizedIncomePrincipal().plus(additional)
}

// IsPaused mirrors InterestPeriod.isPaused()'s Lombok-generated reader over the
// @Setter'd isPaused field [VERIFIED: InterestPeriod.java:72-73].
func (ip *InterestPeriod) IsPaused() bool { return ip.Paused }

// SetDueDate mutates the segment's due date, mirroring the Lombok @Setter on
// dueDate [VERIFIED: InterestPeriod.java:50-52]. The class has no hand-written
// setter; :50 is the @Setter, :51 the @NotNull and :52 the field itself.
func (ip *InterestPeriod) SetDueDate(due time.Time) { ip.DueDate = due }

// SetPaused mutates the segment's paused flag, mirroring the Lombok @Setter on
// isPaused [VERIFIED: InterestPeriod.java:72-73].
func (ip *InterestPeriod) SetPaused(paused bool) { ip.Paused = paused }

// SetRateFactor mutates the segment's own rate factor, mirroring the Lombok
// @Setter on rateFactor [VERIFIED: InterestPeriod.java:54-55].
func (ip *InterestPeriod) SetRateFactor(f *big.Rat) { ip.RateFactor = f }

// SetRateFactorTillPeriodDueDate mutates the segment's rate factor measured to
// the enclosing repayment period's due date, mirroring the Lombok @Setter on
// rateFactorTillPeriodDueDate [VERIFIED: InterestPeriod.java:56-57].
func (ip *InterestPeriod) SetRateFactorTillPeriodDueDate(f *big.Rat) {
	ip.RateFactorTillPeriodDueDate = f
}

// copy is InterestPeriod.copy(repaymentPeriod, interestPeriod) — a deep copy
// rebound to rp [VERIFIED: InterestPeriod.java:86-92].
func (ip *InterestPeriod) copy(rp *RepaymentPeriod) *InterestPeriod {
	c := &InterestPeriod{
		repaymentPeriod:             rp,
		FromDate:                    ip.FromDate,
		DueDate:                     ip.DueDate,
		RateFactor:                  ratCopy(ip.RateFactor),
		RateFactorTillPeriodDueDate: ratCopy(ip.RateFactorTillPeriodDueDate),
		creditedPrincipal:           ip.CreditedPrincipal(),
		creditedInterest:            ip.CreditedInterest(),
		disbursementAmount:          ip.DisbursementAmount(),
		balanceCorrectionAmount:     ip.BalanceCorrectionAmount(),
		outstandingLoanBalance:      ip.OutstandingLoanBalance(),
		capitalizedIncomePrincipal:  ip.CapitalizedIncomePrincipal(),
		rounding:                    ip.rounding,
		currency:                    ip.currency,
		Paused:                      ip.Paused,
	}
	return c
}

// withEmptyInterestPeriod is InterestPeriod.withEmptyAmounts(repaymentPeriod,
// fromDate, dueDate, isPaused): every amount is zero and the rate factors are
// BigDecimal.ZERO, matching the oracle's three- and four-argument factories
// [VERIFIED: InterestPeriod.java:94-106] — the three-argument factory at
// :94-99 and the four-argument one at :101-106. The previous span, :94-109,
// overran both and swallowed the head of compareTo() at :108-111.
func withEmptyInterestPeriod(rp *RepaymentPeriod, from, due time.Time, paused bool) *InterestPeriod {
	zero := moneyZero(rp.currency, rp.rounding)
	return &InterestPeriod{
		repaymentPeriod:             rp,
		FromDate:                    from,
		DueDate:                     due,
		RateFactor:                  new(big.Rat),
		RateFactorTillPeriodDueDate: new(big.Rat),
		creditedPrincipal:           zero,
		creditedInterest:            zero,
		disbursementAmount:          zero,
		balanceCorrectionAmount:     zero,
		outstandingLoanBalance:      zero,
		capitalizedIncomePrincipal:  zero,
		rounding:                    rp.rounding,
		currency:                    rp.currency,
		Paused:                      paused,
	}
}

func ratCopy(r *big.Rat) *big.Rat {
	if r == nil {
		return nil
	}
	return new(big.Rat).Set(r)
}
