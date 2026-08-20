package loanschedule

import (
	"context"
	"math/big"
)

// The progressive-loan interest schedule model, and the EMI arithmetic over it.
//
// This is a port of the reference oracle's ProgressiveLoanInterestScheduleModel /
// RepaymentPeriod / InterestPeriod triple and of ProgressiveEMICalculator's
// declining-balance path, at pinned commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb.
//
// TWO STRUCTURAL DIFFERENCES FROM THE JAVA, BOTH DELIBERATE AND BOTH INERT:
//
//  1. The oracle memoises the derived quantities (RepaymentPeriod's four
//     Memo fields). Memo invalidates on the hash of its declared dependencies
//     [VERIFIED: Memo.java:56-72 recomputes whenever a dependency hash moves, and
//     InterestPeriod carries a generated equals/hashCode over its amounts,
//     InterestPeriod.java:40-43], so it is a pure cache. This port carries an
//     equivalent cache over the one derived quantity whose recomputation is not
//     O(1) -- the forward interest chain (see chainStep) -- and invalidates it by
//     PERIOD INDEX rather than by dependency hash. Revision 1 of this file
//     dropped the cache entirely and recomputed on every read; that is the same
//     FUNCTION at a materially different COST -- quadratic in NumberOfRepayments,
//     measured at 10.77 s for a 360-period schedule -- which is a defect in its
//     own right (T11 F-2). The cache is observationally inert, and
//     TestInterestChainMemoIsObservationallyInert grades that claim by generating
//     every swept shape twice, once with the memo on and once with it off, and
//     comparing cell for cell.
//  2. Every quantity the oracle carries as a Money is an int64 count of minor
//     units here. Money is a BigDecimal at the currency's scale plus a
//     MathContext [VERIFIED: Money.java:40-53], and at a fixed scale its add,
//     subtract, min, max and clamp are exact integer operations, so the two
//     representations agree cell for cell. Only the quantities the oracle carries
//     as a bare BigDecimal -- rate factors, growth factors, the EMI recurrence --
//     are rationals here, and each is rounded exactly where the oracle rounds it.

// interestPeriod is one segment of a repayment period.
// Port of InterestPeriod.
type interestPeriod struct {
	from, due civilDate

	// rateFactor is the segment's own rate factor, quantized to the request's
	// RateFactorScale [VERIFIED: ProgressiveEMICalculator.java:639-640 ->
	// :1486-1541]. The repayment period's growth factor sums these.
	rateFactor *big.Rat

	// rateFactorTillDue is the rate factor computed over
	// [segment FromDate, ENCLOSING REPAYMENT PERIOD DueDate]
	// [VERIFIED: ProgressiveEMICalculator.java:641-642 -> :1355-1418]. The
	// per-period interest reads this one, and it takes periodRatio as its
	// multiplier where the other takes RepaymentEvery.
	rateFactorTillDue *big.Rat

	// disbursedMinor is the principal registered ON this segment. It enters the
	// balance of the segment AFTER it, never this one
	// [VERIFIED: InterestPeriod.java:167-186].
	disbursedMinor int64

	// outstandingMinor is the balance carried INTO this segment.
	outstandingMinor int64
}

// repaymentPeriod is one installment window.
// Port of RepaymentPeriod.
type repaymentPeriod struct {
	from, due civilDate
	segments  []*interestPeriod
	emiMinor  int64

	// idx is this period's position in the model, cached so that the derived
	// quantities can walk the chain of previous periods without a linear search.
	idx int
}

// scheduleModel is the whole interest schedule under construction.
type scheduleModel struct {
	periods []*repaymentPeriod

	// ctx is the request's context, carried on the model so that a linear pass
	// over the periods can be abandoned when the caller has gone away.
	//
	// It is held here rather than threaded through the derived-quantity
	// accessors because those accessors ARE the money arithmetic: giving
	// duePrincipalMinor an error return would rewrite every expression in this
	// file, and rewriting money code to fix a liveness defect is a trade this
	// program does not make. Nothing here reads a clock, and cancellation never
	// changes a computed value -- it decides only whether a value is returned.
	ctx context.Context

	// cancelled is sticky: once the context has reported an error every later
	// check short-circuits, every loop unwinds, and generate discards the
	// half-built schedule and returns ctx.Err().
	cancelled bool

	// chain and chainValid are the memo over the forward interest chain. Entries
	// 0..chainValid-1 are valid, and chain[i] is keyed by POSITION in periods;
	// see chainStep and interestChainUpTo.
	chain      []chainStep
	chainValid int

	// minorDigits and precision are READ BY THE INTEREST FOLD (chainStep (a)) and
	// are model-wide, so no invalidateFrom index can cover a write to them. They
	// are set once in newScheduleModel and must never be written afterwards.
	minorDigits int32
	precision   int32 // Rounding.SignificantDigits
	scale       int32 // Rounding.RateFactorScale

	// rate is the nominal annual rate as the reference oracle holds it after
	// dividing the input percentage by 100 under the MathContext
	// [VERIFIED: ProgressiveEMICalculator.java:1318-1320].
	rate *big.Rat

	repaymentEvery int64

	// daysInMonth and daysInYear are the day-count constants of
	// DayCountFixed30Over360: 30 and 360. daysInMonth is 30 on BOTH rate-factor
	// call sites and on every path either is reachable on -- the local at
	// :1508 is consumed only from the `case DAYS_30 ->` arm at :1536, which is
	// precisely where that ternary yields 30, and the interest call site passes
	// the literal 30 at :1413.
	daysInMonth *big.Rat
	daysInYear  *big.Rat
}

// ---------------------------------------------------------------------------
// Cancellation. NEVER an answer device: with a live context every check below
// is a predictable false and the arithmetic runs exactly as it did before.
// ---------------------------------------------------------------------------

// ctxCheckStride bounds how much work runs between two reads of the context: a
// linear pass over the periods asks at most once every ctxCheckStride periods.
//
// It is a power of two so the test is a mask, and it is not 1 because
// context.Context.Err takes a mutex on a cancelCtx: putting that on the
// innermost step of the fold would charge every schedule for a liveness
// property only a cancelled schedule uses. At this port's measured per-period
// cost the 256-period stride bounds the tail latency of a cancelled call to a
// few milliseconds, far below any deadline a caller of a schedule service sets,
// and the whole of the corpus is 36 periods or fewer -- so on every graded shape
// the context is read exactly once per pass, at index 0.
const ctxCheckStride = 256

// checkCancel reports whether generation should be abandoned, reading the
// context at most once every ctxCheckStride periods and remembering the answer.
//
// When it returns true the caller unwinds, generate discards the half-built
// model and Generate returns ctx.Err() -- the bare context error, which is the
// convention the entry check at the top of Generate already established, and
// which is neither of the contract's three refusal sentinels because a cancelled
// request was not refused. The contract permits exactly this: "a purely
// computational implementation may honour cancellation and otherwise ignore it"
// (contract.ScheduleGenerator.Generate).
func (m *scheduleModel) checkCancel(i int) bool {
	if m.cancelled {
		return true
	}
	if m.ctx == nil || i&(ctxCheckStride-1) != 0 {
		return false
	}
	if m.ctx.Err() != nil {
		m.cancelled = true
		return true
	}
	return false
}

// ---------------------------------------------------------------------------
// The interest-chain memo
// ---------------------------------------------------------------------------

// chainStep is one memoised step of the forward interest chain: a period's
// calculated and due interest, and the unrecognized interest it carries into the
// period after it.
//
// This is the port's counterpart of the oracle's Memo over
// RepaymentPeriod.getCalculatedDueInterest / getDueInterest
// [VERIFIED: RepaymentPeriod.java:71-77 declares the four Memo fields -- :71, :73,
// :75, :77; :60-70 is originalEmi/paidPrincipal/paidInterest/
// futureUnrecognizedInterest/mc and was the wrong cite until T69. Memo.java:43-53
// re-reads the declared dependencies on every get and Memo.java:56-72 recomputes
// only when one of their hashes has moved]. The oracle invalidates by HASHING the
// dependencies; this port invalidates by PERIOD INDEX.
//
// THE RULE THAT MAKES INDEX INVALIDATION SOUND -- read this before adding a write.
//
// There are TWO obligations, not one. The memo is a map from a period INDEX to a
// money pair, so it can go wrong by holding a stale VALUE (a) and (b), or by being
// asked with the wrong KEY (c). A write-ordering rule alone does not cover (c).
//
//	(a) DEPENDENCY SET. The fold reads, for period i, exactly these STORED fields
//	    of periods 0..i: the model's periods slice; that period's due and emiMinor;
//	    its segments slice; and per segment from, due, outstandingMinor and
//	    rateFactorTillDue. It ALSO reads two MODEL-WIDE fields that no index can
//	    cover -- minorDigits, through segmentCalculatedInterest's majorFromMinor
//	    and interestChainUpTo's minorFromMajor, and precision, through
//	    segmentCalculatedInterest's three roundSignificant calls. Those two are
//	    set once in newScheduleModel's struct literal and MUST NEVER be written
//	    after it: a write to either invalidates the WHOLE chain, and there is no
//	    invalidateFrom(j) that expresses that. Per-tranche or per-period rounding
//	    would break this and needs a different mechanism, not a guard.
//	    (In-file references here are by FUNCTION NAME, not by line: this comment
//	    block is long enough that editing it moves every line number in the file,
//	    which is how the last set of self-cites went stale.)
//	    (Derived by reading interestChainUpTo and segmentCalculatedInterest, not
//	    from this comment. NOT read by the fold body: segment rateFactor, segment
//	    disbursedMinor -- which reaches the fold only after updateOutstandingBalances
//	    turns it into outstandingMinor -- and period from. Period idx is not read by
//	    the fold body either, but it is NOT free: see (c).)
//
//	(b) WRITE ORDERING -- A SUFFICIENT RULE, NOT AN "IF AND ONLY IF". The cached
//	    values stay fresh if every write to one of (a)'s PER-PERIOD fields on period
//	    j is PRECEDED by invalidateFrom(j') for some j' <= j, with no read of the
//	    chain in between. That is the discipline every live-model write site in this
//	    file follows, and it is what a new write site should follow.
//
//	    It is SUFFICIENT and NOT NECESSARY, and writing it as "if and only if" is
//	    false. What soundness actually needs is the weaker condition that
//	    m.chainValid <= j holds at the next chain read after the write. An
//	    invalidateFrom(j') with j' <= j ESTABLISHES that condition; CONSTRUCTION
//	    ALREADY SATISFIES IT. m.chainValid is zero-valued; interestChainUpTo trusts
//	    m.chain[last] only under `last < m.chainValid` and resumes only from
//	    `start = m.chainValid`; and invalidateFrom only ever LOWERS chainValid
//	    (`if i < m.chainValid`). So while chainValid == 0 nothing is trusted, the
//	    fold restarts at index 0, and an invalidateFrom call would be a no-op by
//	    its own guard.
//
//	    That is why the writes that BUILD a model carry no guard and are not
//	    defects: newScheduleModel (generator.go) fills m.periods and sets p.idx in
//	    a loop and allocates m.chain only AFTER that loop, and deepCopy hands the
//	    copy a fresh empty chain before writing the copy's periods and segments.
//	    DO NOT "FIX" THOSE SITES BY ADDING A GUARD. Guard any write that can run
//	    after a chain read -- which is every write on a model that has been handed
//	    to a caller.
//
//	(c) KEY INVARIANT -- what (b) does not cover and cannot. m.chain[i] is keyed by
//	    POSITION IN m.periods: interestChainUpTo's loop reads m.periods[i] and
//	    stores its answer at m.chain[i]. And p.idx is the key every lookup uses --
//	    calculatedDueInterestMinor and dueInterestMinor both call
//	    interestChainUpTo(p.idx) -- as do several of the guards themselves
//	    (invalidateFrom(p.idx) in calculateRateFactors and twice in
//	    adjustEMIIfNeeded; invalidateFrom(related[0].idx) in
//	    calculateLevelInstallment). Soundness therefore ALSO requires
//	    m.periods[i].idx == i
//	    for every i, and m.periods never reordered, spliced or shortened after
//	    construction. Write p.idx, or permute m.periods, and interestChainUpTo
//	    answers with ANOTHER PERIOD'S MONEY while rule (b) is satisfied at every
//	    step -- (b) never mentions idx, and permuting a slice whose per-period
//	    contents are unchanged can be done with a guard and still be wrong. This is
//	    why p.idx is assigned exactly once, in index order, in newScheduleModel,
//	    before m.chain exists, and why nothing in this package sorts, reverses,
//	    copies over or deletes from m.periods.
//
// DO NOT restate (b) as "no quantity of a later period appears anywhere in the
// fold, so step i is a function of periods 0..i and of nothing later". That
// sentence is true OF THE FOLD and FALSE OF THE COMPUTATION THE FOLD LIVES IN,
// and it is the sentence a future contributor would check a new write site
// against. The reference oracle propagates later periods onto earlier ones in at
// least four places, and this port reproduces three of them:
//
//   - the annuity fold. rateFactorN is a product over EVERY related period's rate
//     factor and fnResult a fold over the same list MINUS THE FIRST, and the single
//     resulting installment is written onto all of them, first included
//     [VERIFIED: ProgressiveEMICalculator.java:1722-1742 --- rateFactorN at :1725,
//     fnResult at :1726, the forEach/setEmi at :1736-1741; the reduces themselves
//     are at :1818-1819 (calculateRateFactorPlus1NForEmi, :1816-1820) and :1827
//     (calculateFnResultForEmi, :1822-1828), whose .skip(1) is at :1825; port:
//     calculateLevelInstallment].
//
//   - the EMI re-adjust smoothing loop. getEmiAdjustment scans FROM THE END and
//     returns lastPeriod.getEmi().minus(penultimatePeriod.getEmi()), and the
//     uniform installment derived from that tail residual is stamped onto every
//     related period starting at the earliest
//     [VERIFIED: :1258-1309, the scan at :1778-1789, the writes at :1279-1286 and
//     :1298-1304; port: adjustEMIIfNeeded].
//
//   - the final-period residual. diff is a WHOLE-SCHEDULE aggregate and :1165-1174
//     writes emi on ANY period whose outstanding principal exceeds a whole-schedule
//     total [VERIFIED: :1160-1219, diff at :1202-1203; port: applyFinalPeriodResidual].
//
//   - futureUnrecognizedInterest on period i is assigned the unrecognizedInterest
//     of a period at index > i -- getPeriodWithUnrecognizedInterest filters on
//     dueDate().isAfter(...) -- and that field is then added into
//     calculateCalculatedDueInterest [VERIFIED: :1243-1251 calling :1805-1814, the
//     isAfter filter at :1809; RepaymentPeriod.java:260]. NOT PORTED.
//
//     THE REASON IS NOT "NOTHING IS EVER PAID". That sentence stood here until
//     T69 and it is true but inert. unrecognizedInterest is calculatedDueInterest
//     minus dueInterest, clamped at zero [VERIFIED: RepaymentPeriod.java:381-383],
//     and dueInterest caps at emi + credited + futureUnrecognized [VERIFIED:
//     RepaymentPeriod.java:276-286, :293-295]. So on a ZERO-EMI period with
//     nothing paid it is strictly POSITIVE -- and zero-EMI periods are exactly
//     what applyFinalPeriodResidual's counterpart creates. Nothing being paid does
//     not close this.
//
//     WHAT CLOSES IT, AND WHY THE UPGRADE IS ALLOWED NOW. T69 left the argument
//     below marked [UNVERIFIED]: it still needed the tillDate period's OWN
//     unrecognized interest not to reach the periods after it through
//     RepaymentPeriod.java:261-263, and it named T66 to settle that by ORACLE
//     CAPTURE. T66 delivered both halves -- the step that closes the inheritance
//     route, and capture pass 3h, THE FIRST OBSERVATION OF THIS FIELD IN THE
//     PROGRAM. The upgrade from hypothesis to result is licensed BY THE CAPTURE,
//     never by the reading: the same reading without a capture was asserted once,
//     at T65, and rejected. Do not promote anything else in this block from
//     reading alone, and do not weaken the lapse list at the end.
//
//     PROVED -- from the pinned checkout 426a23544. Every line number below was
//     re-opened AGAIN at T72 and resolved to the method it lands in; nothing here
//     is transcribed on trust from an earlier handoff. Three numbers that T66's
//     handoff, PASS3H-REPORT.md and the driver's re-derivation all carried
//     (deepCopy :1226, the futureUnrecognizedInterest write :1250, the residual
//     assignment :1207) were corrected at T70 to :1224, :1246 and :1205 with
//     :1210, and T72 re-confirmed each against the pinned file. T72 also widens
//     InterestPeriod.java:168-186 to :168-188, the method's real span.
//
//     (a) THE DECISION RUNS ON A TILL-DATE-TRUNCATED DEEP COPY.
//     calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer
//     (:1221-1252) copies at :1224, then :1237 calls
//     calculateRateFactorForScheduleTillDateInclusive (:1791-1803), which sets
//     BOTH rateFactor and rateFactorTillPeriodDueDate to BigDecimal.ZERO on every
//     interest period with targetDate.isBefore(ip.getDueDate()) [VERIFIED: filter
//     :1799, zeroing :1800-1801], and InterestPeriod.getCalculatedDueInterest
//     multiplies by rateFactorTillPeriodDueDate [VERIFIED: InterestPeriod.java
//     :145-157, the multiply at :155]. So on the copy a period dated after
//     tillDate contributes exactly ZERO INTEREST OF ITS OWN. The
//     overdue-correction branch (:1229-1241) does not disturb that: the list it
//     tests is written only by addOverdueBalanceCorrection [VERIFIED: :372-382,
//     recording at ProgressiveLoanInterestScheduleModel.java:106-108], which no
//     origination path calls, and even when it fires the :1240 rebuild writes
//     outstandingLoanBalance only [VERIFIED: InterestPeriod.java:168-188] and
//     cannot restore a zeroed rate factor.
//
//     (b) tillDate IS ANCHORED AT THE DISBURSEMENT, NOT AT MATURITY -- AND WHICH
//     ANCHOR IS USED IS DECIDED BY A PRODUCT FLAG, NOT BY THE NUMBER OF
//     DISBURSEMENTS. addDisbursement (:137-153) branches at :142-144 on
//     isAllowFullTermForTranche() && numberOfRepayments > 0 &&
//     action == DISBURSEMENT [VERIFIED: :142-144]. THAT GUARD NEVER CONSULTS HOW
//     MANY DISBURSEMENTS THERE ARE. With the flag FALSE the else branch
//     (:145-151) passes getEffectiveRepaymentDueDate(...) -- the due date of the
//     period the disbursement lands in, or the NEXT period's due date when it
//     lands exactly on one [VERIFIED: :250-263] -- into
//     calculateEMIValueAndRateFactors (:718-728), which for DECLINING_BALANCE
//     dispatches at :723 to
//     calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod (:730-751)
//     and enters calculateLastUnpaidRepaymentPeriodEMI AT :747 with that due
//     date. Call that period's index f. With the flag TRUE -- on ANY number of
//     disbursements, INCLUDING EXACTLY ONE -- addFullTermTrancheDisbursement
//     (:155-174) runs instead and reaches :1160 at :247, inside
//     mergeNewScheduleModelWithExistingOne (:206-248), with tillDate =
//     operation.getSubmittedOnDate(), the disbursement DATE [VERIFIED: :247].
//     There is no f on that path and (b) is simply FALSE there. SO STEP (b) IS
//     PROTECTED BY THE FLAG PIN, CONDITION (1) BELOW -- NOT by the
//     single-disbursement predicate. (T67's replacement text cited :247 as the
//     ordinary path and was rejected for it; T70's rule then blamed :247 on
//     multi-tranche and was rejected for that. Resolve every citation you add
//     here to its enclosing method, AND every guard to its actual condition,
//     before you write it down.) With (a): on the copy, a period k > f
//     contributes S_k = 0.
//
//     (c) BEYOND f THE CHAIN IS A PURE NON-INCREASING CASCADE. With nothing paid,
//     no credit, no capitalized income, no fixed interest and futureUnrecognized
//     still zero, calculatedDueInterest reduces to cdi_k = S_k + u_(k-1)
//     [VERIFIED: RepaymentPeriod.java:252-265, the previous-period term at
//     :261-263], dueInterest to min(cdi_k, emi_k) [VERIFIED: :272-286, the min at
//     :280, with :293-295], and u_k = max(0, cdi_k - dueInterest_k) [VERIFIED:
//     :381-383]. So for k > f, u_k = max(0, u_(k-1) - emi_k), telescoping to
//     u_k = max(0, u_f - (sum of emi_j over f < j <= k)).
//
//     (d) AN AGGREGATE IDENTITY HAS JUST BEEN ENFORCED. :1189-1203 computes
//     diff = totalDisbursed + capitalizedIncome + creditedPrincipal +
//     totalDueInterest - totalEMI, and :1205 with :1210 assigns
//     emi_L := emi_L + diff on the selected last-not-fully-paid period L --
//     immediately before the :1217 lookup. So sum_j emi_j = P + I, with P the
//     disbursed principal and I the total due interest as measured on the real
//     model JUST BEFORE THE ASSIGNMENT [T66.md:96-97].
//
//     KEEP THAT QUALIFIER; IT IS LOAD-BEARING AND T70 DROPPED IT. getDueInterest
//     is memoised on a dependency key that INCLUDES emi [VERIFIED:
//     RepaymentPeriod.java:272-286, the Memo.of dependency array at :282-283], so
//     the :1210 write invalidates period L's memo and the total due interest a
//     lookup would return AFTER the assignment can differ from the I that went
//     into diff. The identity is a statement about the PRE-assignment I. It is
//     NOT true "at lookup time", and T70's wording said it was. The conclusion
//     survives -- (e) uses I only as a non-negative quantity dropped from a bound
//     [T66.md:110-115] -- but the sentence does not survive without the
//     qualifier. Note also that :1183-1184 RESETS that period's
//     futureUnrecognizedInterest to zero on entry, and it is the only period this
//     path can ever set.
//
//     (e) THEREFORE u_L = 0. emi_j = 0 for every j > L, because isFullyPaid() is
//     emiPlusCreditedAmountsPlusFutureUnrecognizedInterest == totalPaidAmount
//     [VERIFIED: RepaymentPeriod.java:371-373] and with nothing paid that is
//     emi_j == 0. AND emi_j = 0 for every j < f, which is the premise the whole
//     step turns on: getRelatedRepaymentPeriods keeps only dueDate >= tillDate
//     [VERIFIED: ProgressiveLoanInterestScheduleModel.java:191-198, filter at
//     :196] and the level installment is written only onto the list passed in
//     [VERIFIED: :1674 dispatching at :1680 to
//     calculateEMIOnActualModelWithDecliningBalanceInterestMethod (:1722-1742),
//     the forEach/setEmi at :1736-1741]. THAT WRITE PATH IS REACHED ONLY VIA
//     :741, under onlyOnActualModelShouldApply (:733-735) -- which is what
//     condition (2) is really protecting; see there. Hence sum of emi_j over
//     f < j <= L is (P + I) - emi_f, so u_L = max(0, u_f - (P + I) + emi_f),
//     which is 0 as soon as cdi_f <= P. CITE T66.md:100-108 FOR THIS STEP -- that
//     is the general-f form -- and T66.md:110-115 for the bound. Do NOT cite
//     PREDICTION.md's step (e) at PREDICTION.md:100-105: it states the sufficient
//     condition as cdi_f <= P + emi_f WITHOUT the "emi_j = 0 for j < f" premise,
//     so it is exact only at f = 0, and it now carries a dated CORRECTION block
//     saying so [PREDICTION.md:107-130]. Citing that form would import a
//     statement known to be incomplete.
//
//     (f) SO THE CASCADE IS DEAD FROM L ON: u_L = 0 => cdi_(L+1) = 0 => u_(L+1) =
//     0 => ... and getPeriodWithUnrecognizedInterest needs u > 0 STRICTLY AFTER L
//     [VERIFIED: :1805-1814, the u > 0 test at :1808, the isAfter at :1809].
//     There is no such period.
//
//     (g) THE FALLBACK SELECTOR CANNOT RESCUE IT. :1178-1181 fires only when the
//     :1176-1177 filter comes back EMPTY, and it then selects the LAST period,
//     after which nothing is strictly later.
//
//     THE BOUND IN (e) IS NOT TIGHT above a per-period rate factor of 1.00. Above
//     that the conclusion is carried by the capture and the census below, not by
//     the inequality. Do not restate it as a tight bound.
//
//     OBSERVED -- capture pass 3h, .softhouse/capture/PASS3H-REPORT.md and
//     .softhouse/capture/out/capture-prod3h-*. 18 cases, 416 mechanism rows read
//     off the oracle's OWN model through a delegating Proxy, with path identity
//     against the pristine seam on 18 of 18 and 8 of 8 rig calibrations
//     reproduced cell for cell (including the promoted T64-ZP-A and T64-ZP-B):
//     futureUnrecognizedInterest == "0.00", interestMovedUpward == false and
//     unrecognizedInterest == "0.00" on ALL 416. Five cases carry the full
//     structural precondition -- a vacuously fully-paid zero-EMI period STRICTLY
//     AFTER L: P-CAL-ZPB 40 such rows, T66-M-R12000 10, T66-M-DRIFT-R12000 10,
//     T66-M-DRIFT-R2400 3, T66-M-FLOOR-HR 3 -- and the two R12000 cases run at a
//     per-period rate factor of 10.00, ten times past (e)'s sufficient condition.
//     AND ALL 18 RAN allowFullTermForTranche = false, so this corpus observes the
//     :747 entry AND NOTHING ELSE. capturesCanonicalSha256
//     fdd751a209c9518b157ca6fd70aef06a91acff94953e1f8cc6c4d45162b90b73.
//     [VERIFIED at T72: every figure in this paragraph -- 18, 416, zero
//     exceptions on the three fields, 18 of 18 path identity, the five tails
//     40/10/10/3/3, and 18 of 18 inputs.allowFullTermForTranche == false -- was
//     re-derived from .softhouse/capture/out/capture-prod3h-raw.json at T72, and
//     the digest matches capture-prod3h-attestation.json:15.]
//
//     SEARCHED -- T66's port-side census over 21,060 admitted shapes: 9,437 carry
//     a zero-EMI period, 156 of those carry positive calculatedDueInterest, and 0
//     place such a period strictly after L. [VERIFIED: T66.md, re-run
//     independently by the driver in
//     .softhouse/reviews/driver-rederivation-20260820-140000.md. NOT re-run at
//     T70 or T72: the throwaway harness is preserved only as
//     .softhouse/capture/t66-unrecognized-interest/t66_search_test.go.txt.]
//
//     NOT CLAIMED, and do not let a later edit quietly claim it:
//
//     (i) THE COPY'S INTERNAL STATE WAS NEVER OBSERVED, by anyone. Pass 3h reads
//     the REAL model, so it establishes the OUTCOME of the one decision -- the
//     field write at :1246 is the LAST ACT on the real model of the outer :747
//     frame, because that frame's :1217 runs after any inner frame has returned,
//     and :1288's calls run on the smoothing loop's TRIAL copy -- and NOT the
//     copy's intermediate u_k cascade [PASS3H-REPORT.md:138-149]. DO NOT WRITE
//     "entered on the real model once, at :747". PASS3H-REPORT.md:141-143 says
//     exactly that, T70 inherited it verbatim, and it is FALSE: :1214 re-enters
//     :1160 on scheduleModel, the REAL model [VERIFIED: :1211-1215, the argument
//     at :1214]. Once-ness is not what the observation needs; LAST-ness is. That
//     upstream document is an attestation and is not edited from here, so it
//     still carries the false sentence. Steps (a)-(g) are proof; the 416 rows are
//     observation of the outcome. Keep the two apart.
//
//     (ii) THE RECURSIVE FRAME IS NOT COVERED DEDUCTIVELY, AND WHAT WOULD FIRE IT
//     IS NOW EXACTLY KNOWN. :1211-1215 re-enters :1160 -- on the real model, with
//     the same tillDate -- when getEmi() falls below
//     totalPaidAmount - totalCreditedAmount. ON THE GRADED DOMAIN THAT RIGHT-HAND
//     SIDE IS EXACTLY ZERO, TERM BY TERM, so the guard reduces to emi_L < 0:
//     totalPaidAmount is paidPrincipal + paidInterest [VERIFIED:
//     RepaymentPeriod.java:367-369], zero because nothing is paid; and
//     totalCreditedAmount is creditedPrincipal + creditedInterest -
//     creditedInterestMovedDueReAge - creditedPrincipalMovedDueReAge [VERIFIED:
//     RepaymentPeriod.java:357-359], whose first two terms are zero by the NO
//     CREDITED AMOUNTS condition and whose last two are zero by the NO RE-AGING
//     clause -- so it is zero termwise, not merely "zero when nothing is paid".
//     getEmi() at :1211 reads what :1210 has just written [VERIFIED: :1205-1213].
//     The port encodes that same test verbatim: the emiMinor < 0 clamp and the
//     depth+1 re-entry inside applyFinalPeriodResidual (cited by NAME, not by
//     line -- the number moves every time this comment does).
//
//     WHETHER emi_L CAN GO STRICTLY NEGATIVE ON AN ADMITTED SHAPE IS [UNVERIFIED]
//     AND IS NOT SETTLED HERE. Nothing on :1205 floors getEmi().add(diff, mc);
//     the only floor on that statement is the getFixedInterest() override at
//     :1206-1208, excluded by the NO FIXED INTEREST clause, and the earlier
//     :1165-1174 loop's floor is minimumEMI = paidInterest + paidPrincipal = 0
//     [VERIFIED: :1169-1172], which clamps THAT loop's subtraction and says
//     nothing about diff. The OUTER frame's :1217 lookup therefore runs after an
//     inner frame has re-established (d) on a possibly DIFFERENT L, and it is
//     [UNVERIFIED] that the recursive frame preserves (d) for the outer target.
//     T66 states (d) for a SINGLE entry into :1160; neither T66 nor the driver
//     analysed the recursive frame. Coverage is EMPIRICAL -- the census runs the
//     port's own residual with the recursion in place over 21,060 shapes with 0
//     firings. SETTLE IT BY CAPTURE, NOT BY READING. T70, T71 and the driver each
//     declined to settle it by reading and each was right to; the detector is one
//     integer, so hunt for an admitted shape whose residual drives the final
//     period's EMI strictly negative rather than arguing about it.
//
//     (iii) NOTHING HERE GENERALISES PAST THE GRADED DOMAIN.
//
//     THE RULE THIS PORT DEPENDS ON. Omitting futureUnrecognizedInterest and
//     interestMovedUpward is safe ONLY while EVERY one of the following holds.
//     Make any of them false and the argument above is VOID -- the field must be
//     ported BEFORE the wider shape is admitted, not after a vector goes red.
//     T70 numbered these (1)-(5) and its (1) named the WRONG GUARD, which is why
//     T71 rejected it; the flag pin is NEW here and takes (1), so T70's (1)-(5)
//     are (2)-(6) below, and (7)-(8) are new as well. Cross-references inside
//     this block name the conditions rather than numbering them, on purpose: a
//     number drifts, a name does not.
//
//     (1) allowFullTermForTranche IS FALSE -- THE FLAG PIN. This, and NOT the
//     disbursement count, is what protects step (b). The guard at :142-144 is
//     isAllowFullTermForTranche() && numberOfRepayments > 0 &&
//     action == DISBURSEMENT and NEVER CONSULTS THE DISBURSEMENT COUNT [VERIFIED:
//     :142-144]. Setting it true on an ORDINARY SINGLE DISBURSEMENT routes into a
//     full re-amortization through a synthetic terms object and a temporary
//     schedule model (:155-174) and reaches :1160 at :247 with tillDate = the
//     disbursement DATE -- which voids (b) outright, and voids (e)'s
//     "emi_j = 0 for j < f" premise as well, because the merge writes EMI onto
//     EXISTING periods:
//     existingRepaymentPeriod.get().setEmi(getEmi().add(newPrincipal.add(
//     newInterest))) [VERIFIED: :228], not onto a window list. The frozen
//     contract already states this pin and its reason [contract.go:1179 and
//     :1191-1202]: it is "a REAL BEHAVIOURAL PIN, not a dead field", "the guard
//     that consumes it never consults multi-disbursement at all", and the two
//     captures differing only in this flag that came out identical are "a
//     measurement, not a licence to ignore the flag".
//
//     HOW TO CHECK CONDITION (1), BECAUSE THE HARNESS CANNOT. The frozen contract
//     has NO FIELD for this flag, so GradedDomain neither tests it nor can
//     [VERIFIED: conformance/admit.go:999-1060 contains no such predicate; the
//     contract files the flag as a PIN, "NOT a section 3.1 graded-domain
//     predicate", contract.go:866-869]. The check is on the ORACLE RUN behind a
//     capture -- inputs.allowFullTermForTranche in the capture JSON -- and never
//     on the vector request, which cannot express it. A vector can therefore be
//     admitted, graded and GREEN while its oracle run took the :247 entry.
//
//     AND THE CORPUS ALREADY CONTAINS EXACTLY THAT.
//     .softhouse/vectors/loanschedule/P-04t-fulltermfortranche-true.json is class
//     "parity", has EXACTLY ONE disbursement, and its capture ran the flag TRUE,
//     so its oracle run went down :247 -- while all 18 pass-3h cases ran it FALSE
//     [VERIFIED at T72: the vector file's class and its single-element
//     request.disbursements; 18 of 18 inputs.allowFullTermForTranche == false in
//     capture-prod3h-raw.json]. Nothing is red, because P-04t's expected cells
//     are byte-identical to P-04f's and P-00's and the contract has no field to
//     tell the three apart. That is OUTPUT IDENTITY ON ONE SHAPE -- a
//     measurement, and NOT coverage. futureUnrecognizedInterest has never been
//     read on the :247 entry by anyone. DO NOT CITE P-04t AS EVIDENCE FOR
//     (a)-(g); it is evidence of the opposite, that the flag-true path is inside
//     the graded corpus and outside the observation. The harness records the same
//     live-and-schedule-neutral finding as T17-F3, marked NARROWED-BY-OBSERVATION
//     [conformance/structural.go:257-276].
//
//     (2) EXACTLY ONE DISBURSEMENT [conformance/admit.go:1018-1020, inside
//     GradedDomain :999-1060]. A SEPARATE condition from (1), protecting a
//     DIFFERENT step. With the flag false a SECOND disbursement still takes the
//     else branch (:145-151), but by then the model is no longer empty --
//     isEmpty() is "no period has a non-zero EMI" [VERIFIED:
//     ProgressiveLoanInterestScheduleModel.java:394-399] -- so unless every EMI
//     is still zero, onlyOnActualModelShouldApply is FALSE [VERIFIED: :733-735]
//     and the write path (e) depends on, :741's calculateEMIOnActualModel, is NOT
//     taken; :743's calculateEMIOnNewModelAndMerge runs instead. Periods before
//     the second disbursement's f also already carry EMI from the first, and each
//     disbursement brings its OWN tillDate into :747, so there is no single f.
//     contract.go:1330-1342 says multi-tranche is coming.
//
//     (3) NOTHING IS EVER PAID. A payment breaks "isFullyPaid() iff emi == 0" in
//     (e) and the reduction in (c).
//
//     (4) NO CREDITED PRINCIPAL OR INTEREST AND NO CAPITALIZED INCOME -- the NO
//     CREDITED AMOUNTS condition. Each is a term of diff and breaks the identity
//     in (d) [:1189-1203], and the first two are terms of totalCreditedAmount in
//     (ii) [RepaymentPeriod.java:357-359].
//
//     (5) NO FIXED INTEREST [RepaymentPeriod.java:259 -- the
//     add(getFixedInterest()) into calculatedDueInterest -- with
//     ProgressiveEMICalculator.java:1206-1208], NO RE-AGING, NO INTEREST PAUSE
//     [:1708-1720 with :1830-1832]. Each adds a non-zero term to cdi_k that (c)
//     assumes away; re-aging additionally makes the last two terms of
//     totalCreditedAmount non-zero in (ii). Note the FILE QUALIFIER on :259:
//     unqualified :N in this block means ProgressiveEMICalculator.java, where
//     :259 is the comment "// Currently N+1 scenario is not supported." inside
//     getEffectiveRepaymentDueDate -- not what is meant. T70 wrote it unqualified
//     and T71 rejected the citation.
//
//     (6) THE SEAM STAYS THE ORDINARY :747 ENTRY. Besides :747, :1160 has SIXTEEN
//     call sites [VERIFIED at T72: grep the name in the pinned file -- 17 call
//     lines plus the declaration at :1160].
//     THIRTEEN are post-origination operations, each with its own tillDate and
//     none of them reasoned about above: :368 addBalanceCorrection, :380
//     addOverdueBalanceCorrection, :404 payInterest, :442 payPrincipal, :505
//     addCredit, :626 getOutstandingAmountsTillDate, :698
//     recalculateScheduleModelTillDate, :868 changeDueDate, :879 and :937
//     re-amortization, :1091 re-age attach, :2024 interest pause, :2129
//     reAgeEqualAmortization.
//     ONE IS AN ORIGINATION CALL AND MUST NOT BE FILED WITH THEM. :247 is reached
//     from addDisbursement (:137-153) via :144 and :155-174: same loan, same
//     disbursement, same call, different branch. It is ORIGINATION, and the only
//     thing holding it off is condition (1). T70 listed :247 under
//     "post-origination operations" and phrased this condition as "the seam stays
//     a PURE ORIGINATION CALL"; that pair is what let a reader satisfy every
//     clause while standing on :247, and it is why T71 rejected the draft. Do not
//     restore either phrasing -- "this is origination" is NOT a reason to believe
//     :247 is unreachable.
//     THE REMAINING TWO are internal to this same generate pass and are NOT
//     covered by the observation: :1214, the self-recursion of (ii), and :1288,
//     the smoothing loop's trial copy, reached from :749 inside
//     checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods (:1258-1309) with
//     tillDate = relatedPeriodsFirstDueDate (:1278). T66 argues that (a)-(g)
//     carry over to the trial because that date equals
//     calculateFromRepaymentPeriodDueDate on the generate path; that is proof and
//     NOT observation [T66.md ## Unverified]. 13 + 1 + 2 = 16. If that arithmetic
//     stops reconciling, the call graph moved and this whole block is stale.
//
//     (7) THE OTHER FIVE PINNED ORACLE INPUTS STILL HOLD [contract.go:1173-1186]:
//     allowPartialPeriodInterestCalculation = true,
//     interestRecognitionOnDisbursementDate = false, fixedLength = null,
//     daysInYearCustomStrategy = null, currency.inMultiplesOf = null. NONE of
//     them was analysed against (a)-(g) by T66, T70 or T72; they are listed here
//     so that relaxing one is a DECISION and not an oversight. Relaxing any of
//     them puts this argument back in [UNVERIFIED] until it is re-argued or
//     captured. Condition (1) is the sixth pin, broken out above because it is
//     the one already violated inside the corpus.
//
//     (8) THE GRADED DOMAIN IS NOT WIDENED IN ANY OTHER RESPECT
//     [conformance/admit.go:999-1060]. (1)-(7) name the premises this argument
//     actually USES; they are not a complete characterisation of the graded
//     domain, and no one has checked (a)-(g) against a predicate that is not on
//     this list. Widening GradedDomain in any way at all -- down payments, a
//     different repayment frequency or unit, a different rounding mode, anything
//     -- is outside everything above. Re-argue it or capture it first. "The rule
//     does not mention it, so it must be fine" is exactly the reasoning this
//     condition exists to forbid.
//
//     This block establishes the :747 entry, on the domain fenced by (1)-(8), and
//     nothing else.
//
// So the memo does NOT cache the derivation of period i's state; it caches a pure
// function of the model's CURRENT STORED FIELDS for periods 0..i. Every one of
// those later->earlier influences that this port reproduces is realised as a WRITE
// to a stored field of an EARLIER period -- setEmi there, p.emiMinor here -- so
// following (b) at each of those write sites is enough for them, and no separate
// backward-dependency argument is needed or true. (b) is enough for THOSE SITES;
// it is not the whole soundness argument, which is (a), (b) and (c) together.
//
// This is the push form of what the oracle's Memo does by pulling: it re-hashes
// its declared dependencies on every get and never pushes an invalidation to a
// neighbour [VERIFIED: Memo.java:43-53].
//
// Every assignment in emi.go and generator.go was enumerated FROM THE WRITES and
// classified against (a), (b) and (c) -- independently at T65, at T67 and at T69,
// with the three enumerations agreeing on the SET of sites. The tables are in
// those handoffs. Deliberately stated without a count: any number here goes stale
// on the next line moved, and the enumeration, not the total, is the evidence.
type chainStep struct{ calculated, due, carried int64 }

// memoiseInterestChain switches the memo off. It is written only by this
// package's own differential test; it is not configuration, and no caller,
// request field or deployment can reach it.
var memoiseInterestChain = true

// invalidateFrom discards the memoised chain from period index i onward.
func (m *scheduleModel) invalidateFrom(i int) {
	if i < m.chainValid {
		m.chainValid = i
	}
}

// newInterestPeriod builds a segment with the oracle's initial amounts: rate
// factors BigDecimal.ZERO and every Money zero
// [VERIFIED: InterestPeriod.java:96-105, withEmptyAmounts].
func newInterestPeriod(from, due civilDate) *interestPeriod {
	return &interestPeriod{from: from, due: due, rateFactor: new(big.Rat), rateFactorTillDue: new(big.Rat)}
}

// newRepaymentPeriod builds a window carrying exactly one segment spanning the
// whole of it [VERIFIED: RepaymentPeriod.java:143-151, create].
func newRepaymentPeriod(from, due civilDate) *repaymentPeriod {
	return &repaymentPeriod{from: from, due: due, segments: []*interestPeriod{newInterestPeriod(from, due)}}
}

func (m *scheduleModel) deepCopy() *scheduleModel {
	out := &scheduleModel{
		minorDigits: m.minorDigits, precision: m.precision, scale: m.scale,
		rate: m.rate, repaymentEvery: m.repaymentEvery,
		daysInMonth: m.daysInMonth, daysInYear: m.daysInYear,
		periods: make([]*repaymentPeriod, 0, len(m.periods)),
		ctx:     m.ctx, cancelled: m.cancelled,
		// The copy starts on an EMPTY memo rather than a copy of this one. The two
		// models are equal at this instant so copying would also be correct, but
		// the trial is about to be rewritten period by period and an empty memo
		// cannot be stale.
		chain: make([]chainStep, len(m.periods)),
	}
	for _, p := range m.periods {
		q := &repaymentPeriod{from: p.from, due: p.due, emiMinor: p.emiMinor, idx: p.idx,
			segments: make([]*interestPeriod, 0, len(p.segments))}
		for _, s := range p.segments {
			t := *s
			q.segments = append(q.segments, &t)
		}
		out.periods = append(out.periods, q)
	}
	return out
}

// previous returns the period before p, or nil for the first
// [VERIFIED: RepaymentPeriod.java:449-451, isFirstRepaymentPeriod is
// previous == null].
func (m *scheduleModel) previous(p *repaymentPeriod) *repaymentPeriod {
	if p.idx <= 0 {
		return nil
	}
	return m.periods[p.idx-1]
}

// startDate is the model's own start: the FIRST repayment period's from-date
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:208-210].
func (m *scheduleModel) startDate() civilDate { return m.periods[0].from }

// ---------------------------------------------------------------------------
// Membership conventions. Named M1..M3 after the contract's normative list; each
// decides a different thing and they are NOT interchangeable.
// ---------------------------------------------------------------------------

// inPeriodM1 is [FromDate, DueDate] for the FIRST repayment period and
// (FromDate, DueDate] for every later one
// [VERIFIED: LoanRepaymentScheduleProcessingWrapper.java:251-254, reached from
// ProgressiveLoanInterestScheduleModel.java:243-244].
//
// Decides: which repayment period a balance change is registered into, hence the
// interest-period segmentation and the effective due date.
func inPeriodM1(target, from, due civilDate, isFirst bool) bool {
	if isFirst {
		return compareDates(target, from) >= 0 && compareDates(target, due) <= 0
	}
	return compareDates(target, from) > 0 && compareDates(target, due) <= 0
}

// inPeriodM3 is [FromDate, DueDate) -- from-inclusive, DUE-EXCLUSIVE
// [VERIFIED: ProgressiveLoanScheduleGenerator.java:306-307,
// !disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)].
//
// Decides: during which period's ITERATION the disbursement row is emitted and
// the disbursement registered. M1 and M3 disagree on exactly one date -- a
// disbursement dated on a repayment period's due date, which M1 puts in period j
// and M3 in period j+1. That single date is the whole of the row-ordering trap.
func inPeriodM3(target, from, due civilDate) bool {
	return compareDates(target, from) >= 0 && compareDates(target, due) < 0
}

// findPeriodForBalanceChange applies M1
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:238-245].
func (m *scheduleModel) findPeriodForBalanceChange(d civilDate) *repaymentPeriod {
	for i, p := range m.periods {
		if inPeriodM1(d, p.from, p.due, i == 0) {
			return p
		}
	}
	return nil
}

// relatedPeriods are the periods whose DueDate is NOT BEFORE the effective due
// date [VERIFIED: ProgressiveLoanInterestScheduleModel.java:190-197]. They are
// the ONLY periods the level installment is computed over and written to, and
// their count is the n of the EMI re-adjust loop -- never NumberOfRepayments.
func (m *scheduleModel) relatedPeriods(effectiveDue civilDate) []*repaymentPeriod {
	var out []*repaymentPeriod
	for _, p := range m.periods {
		if compareDates(p.due, effectiveDue) >= 0 {
			out = append(out, p)
		}
	}
	return out
}

// ---------------------------------------------------------------------------
// Disbursement registration
// ---------------------------------------------------------------------------

// addDisbursement registers the advance and recomputes the schedule.
//
// Port of ProgressiveEMICalculator.addDisbursement
// [VERIFIED: :124-152]. The effectiveDueDate branch at :128-133 requires a
// non-null interestCalculationPeriodMethod, which the capture seam's assembler
// never populates [VERIFIED: LoanApplicationTerms.java:579-606 sets no
// interestCalculationPeriodMethod], so the disbursement date is used unchanged.
// The addFullTermTrancheDisbursement arm at :141-145 is gated on
// allowFullTermForTranche, pinned false by the contract.
func (m *scheduleModel) addDisbursement(d civilDate, amountMinor int64) {
	owner := m.findPeriodForBalanceChange(d)
	if owner == nil {
		return
	}
	m.registerBalanceChange(owner, d, amountMinor)
	m.recalculate(m.effectiveRepaymentDueDate(owner, d))
}

// effectiveRepaymentDueDate: if the change lands exactly on the matched period's
// due date the calculation starts from the NEXT period's due date
// [VERIFIED: ProgressiveEMICalculator.java:249-262]. This is what takes the
// level installment off the periods that close before the money arrives.
func (m *scheduleModel) effectiveRepaymentDueDate(owner *repaymentPeriod, d civilDate) civilDate {
	if compareDates(owner.due, d) == 0 {
		if owner.idx+1 < len(m.periods) {
			return m.periods[owner.idx+1].due
		}
	}
	return owner.due
}

// registerBalanceChange puts the amount on the right segment, splitting one if
// the date falls strictly inside
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:245-296].
func (m *scheduleModel) registerBalanceChange(owner *repaymentPeriod, d civilDate, amountMinor int64) {
	// Every arm below writes this period's segments -- an amount, a moved due
	// date, or a whole new segment -- so the chain is stale from here on.
	m.invalidateFrom(owner.idx)
	isLast := owner.idx == len(m.periods)-1
	onMaturity := isLast && compareDates(d, owner.due) == 0

	if onMaturity {
		// A credit on the maturity date wants a zero-length segment, and reuses
		// one only if the last segment already is zero-length [:266-272].
		last := owner.segments[len(owner.segments)-1]
		if daysBetween(last.from, last.due) == 0 {
			last.disbursedMinor += amountMinor
			return
		}
	} else {
		// A segment that already ENDS exactly on the date takes the amount with
		// no split [:274-277].
		for _, s := range owner.segments {
			if compareDates(d, s.due) == 0 {
				s.disbursedMinor += amountMinor
				return
			}
		}
	}
	m.insertSegment(owner, d, amountMinor)
}

// insertSegment moves the containing segment's due date back to d, gives it the
// amount, and inserts a fresh segment [d, the original due date] after it
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:281-296].
func (m *scheduleModel) insertSegment(owner *repaymentPeriod, d civilDate, amountMinor int64) {
	idx := 0
	// findPreviousInterestPeriod: the LAST segment with from < d <= due, else the
	// first segment [VERIFIED: :327-330].
	found := false
	for i, s := range owner.segments {
		if compareDates(d, s.from) > 0 && compareDates(d, s.due) <= 0 {
			idx, found = i, true
		}
	}
	if !found {
		idx = 0
	}
	prev := owner.segments[idx]
	originalDue := prev.due
	// calculateNewDueDate clamps d into the segment's own window [:439-441].
	newDue := d
	if compareDates(d, prev.from) < 0 {
		newDue = prev.from
	} else if compareDates(d, prev.due) > 0 {
		newDue = prev.due
	}
	prev.due = newDue
	prev.disbursedMinor += amountMinor

	inserted := newInterestPeriod(newDue, originalDue)
	tail := append([]*interestPeriod{inserted}, owner.segments[idx+1:]...)
	owner.segments = append(owner.segments[:idx+1:idx+1], tail...)
}

// ---------------------------------------------------------------------------
// The declining-balance recalculation
// ---------------------------------------------------------------------------

// recalculate is calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod
// [VERIFIED: ProgressiveEMICalculator.java:729-752].
//
// onlyOnActualModelShouldApply is true here because the schedule model is empty
// at the initial disbursement of every loan (:731-734), which is the only
// operation the graded domain admits -- so both the actual-model EMI and the
// re-adjust loop run. The interest and principal moratorium arms are gated on a
// grace configuration the seam cannot express.
func (m *scheduleModel) recalculate(effectiveDue civilDate) {
	related := m.relatedPeriods(effectiveDue)
	// Each step below returns immediately on a cancelled model, so the sequence
	// unwinds without a check between every pair.
	for i, p := range related {
		if m.checkCancel(i) {
			return
		}
		m.calculateRateFactors(p)
	}
	m.updateOutstandingBalances()
	m.calculateLevelInstallment(related)
	m.updateOutstandingBalances()
	m.applyFinalPeriodResidual(0)
	m.adjustEMIIfNeeded(related)
}

// updateOutstandingBalances is calculateOutstandingBalance
// [VERIFIED: ProgressiveEMICalculator.java:1253-1255 ->
// InterestPeriod.updateOutstandingLoanBalance, InterestPeriod.java:166-186].
//
// The walk is strictly in order: a segment's opening balance is read off the one
// before it, and the FIRST segment of the FIRST repayment period is never
// assigned at all -- it keeps the zero it was constructed with, which is why a
// repayment row that closes before the disbursement reports zero rather than the
// principal awaiting advance.
func (m *scheduleModel) updateOutstandingBalances() {
	for i, p := range m.periods {
		if m.checkCancel(i) {
			return
		}
		for j, s := range p.segments {
			if j == 0 {
				if i == 0 {
					continue
				}
				prevPeriod := m.periods[i-1]
				prevSeg := prevPeriod.segments[len(prevPeriod.segments)-1]
				// The chain up to i-1 is read BEFORE period i is invalidated. The
				// hoist into a local is what makes that order explicit, and it is
				// what keeps this walk linear: the write below is to period i, the
				// guard is invalidateFrom(i), and the fold's steps 0..i-1 read no
				// stored field of period i or later (chainStep (a)), so the prefix
				// this read just paid for survives the write. This is chainStep (b)
				// applied at j' = j = i -- not a claim that period i cannot
				// influence period i-1; it can, by writing period i-1's fields,
				// which is a different site with its own guard.
				due := m.duePrincipalMinor(prevPeriod)
				m.invalidateFrom(i)
				s.outstandingMinor = maxInt64(0,
					prevSeg.outstandingMinor+prevSeg.disbursedMinor-due)
				continue
			}
			m.invalidateFrom(i)
			prevSeg := p.segments[j-1]
			s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor)
		}
	}
}

// segmentCalculatedInterest is the interest of ONE segment, in major units.
//
// [VERIFIED: InterestPeriod.java:143-158.] The three operations are rounded
// SEPARATELY and IN THIS ORDER. Operations (2) and (3) cancel algebraically --
// inside the graded domain lengthTillDue equals length on every segment carrying
// a balance -- and DO NOT cancel numerically at 19 significant digits. Collapsing
// them into the textbook balance * rateFactor is a named counterfactual.
func (m *scheduleModel) segmentCalculatedInterest(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	lengthTillDue := daysBetween(s.from, p.due)
	if lengthTillDue == 0 {
		return new(big.Rat)
	}
	base := majorFromMinor(s.outstandingMinor, m.minorDigits)
	t1 := roundSignificant(new(big.Rat).Mul(base, s.rateFactorTillDue), m.precision)
	t2 := roundSignificant(new(big.Rat).Quo(t1, ratInt64(lengthTillDue)), m.precision)
	t3 := roundSignificant(new(big.Rat).Mul(t2, ratInt64(daysBetween(s.from, s.due))), m.precision)
	return t3
}

// interestChainUpTo computes, in ONE forward pass, the calculated and due
// interest of every period up to and including index last, and returns that
// period's pair.
//
// The chain exists because a period's calculated interest carries the PREVIOUS
// period's UNRECOGNIZED interest -- interest that found no room in that
// period's installment [VERIFIED: RepaymentPeriod.java:255-257 adds
// getPrevious().get().getUnrecognizedInterest(), and :381-383 defines it as
// calculatedDueInterest minus dueInterest, clamped at zero]. The oracle
// expresses that as mutual recursion behind four memoised suppliers; without the
// memoisation the same recursion is exponential, so this port walks the chain
// forward instead. It is the same function, and reading only periods 0..last is
// enough because THIS FOLD reads no field of any period after last -- a
// statement about the fold's dependency set, which is enumerated on chainStep,
// and NOT a claim that no later period can influence an earlier one. Later
// periods influence earlier ones all over this file and all over the reference
// oracle; they do it by WRITING the fields listed there, which is why every such
// write ON A LIVE MODEL is preceded by invalidateFrom -- the writes that BUILD a
// model need no guard, and chainStep (b) says why. Note too that last is a KEY,
// not just a bound: it indexes m.chain and m.periods alike, so chainStep (c) --
// m.periods[i].idx == i, and no reordering -- is as load-bearing here as the
// dependency set. See chainStep before adding a write.
//
// That dependency set is what lets the walk be memoised as a PREFIX and resumed
// rather than restarted. Without the memo this function is O(n) on every read
// and the readers are themselves O(n) loops, which is the whole of the port's
// quadratic cost; with it, a forward pass over the periods pays for each step
// once. The memo changes no value: with memoiseInterestChain false the fold
// restarts at index 0 on every call, exactly as revision 1 did.
func (m *scheduleModel) interestChainUpTo(last int) (calculated, due int64) {
	start := 0
	var carriedUnrecognized int64
	if memoiseInterestChain {
		if last < m.chainValid {
			e := m.chain[last]
			return e.calculated, e.due
		}
		if m.chainValid > 0 {
			start = m.chainValid
			carriedUnrecognized = m.chain[start-1].carried
		}
	}
	for i := start; i <= last; i++ {
		if m.checkCancel(i) {
			// The memo keeps only the steps that COMPLETED, so it stays truthful;
			// the pair returned here is meaningless and every caller above is
			// unwinding to discard it.
			return calculated, due
		}
		p := m.periods[i]
		// SUM THE SEGMENTS, THEN MAKE IT MONEY -- exactly once, and in that order:
		// rounding each segment to the minor unit and then adding is a different
		// function [VERIFIED: RepaymentPeriod.java:246-252, Money.of(currency, sum,
		// mc) whose constructor applies the currency scale at Money.java:52].
		sum := new(big.Rat)
		for _, s := range p.segments {
			sum.Add(sum, m.segmentCalculatedInterest(p, s))
		}
		calculated = maxInt64(0, minorFromMajor(sum, m.minorDigits)+carriedUnrecognized)
		// CAP AT THE INSTALLMENT [VERIFIED: RepaymentPeriod.java:266-280]. Nothing
		// is ever paid on a schedule this contract generates, so the paid-amount
		// arms of that expression collapse to the min.
		due = maxInt64(0, minInt64(calculated, p.emiMinor))
		carriedUnrecognized = maxInt64(0, calculated-due)
		if memoiseInterestChain {
			m.chain[i] = chainStep{calculated: calculated, due: due, carried: carriedUnrecognized}
			m.chainValid = i + 1
		}
	}
	return calculated, due
}

func (m *scheduleModel) calculatedDueInterestMinor(p *repaymentPeriod) int64 {
	c, _ := m.interestChainUpTo(p.idx)
	return c
}

func (m *scheduleModel) dueInterestMinor(p *repaymentPeriod) int64 {
	_, d := m.interestChainUpTo(p.idx)
	return d
}

// duePrincipalMinor is the BALANCING non-negative remainder of the installment
// after interest -- ON EVERY ROW INCLUDING THE LAST
// [VERIFIED: RepaymentPeriod.java:339-344, getDuePrincipal is
// negativeToZero(emiPlusCreditedAmounts... minus getDueInterest())].
//
// THERE IS NO SPECIAL CASE THAT SETS THE FINAL ROW'S PRINCIPAL TO THE WHOLE
// REMAINING BALANCE. What makes the final row come out even is that the LAST
// UNPAID PERIOD'S INSTALLMENT absorbs the residual (see applyFinalPeriodResidual);
// the adjustment lands on the EMI and this expression is then applied to it
// unchanged. A port that special-cases the principal instead reproduces the same
// numbers on this corpus and is wrong in shape.
func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {
	return maxInt64(0, p.emiMinor-m.dueInterestMinor(p))
}

// outstandingLoanBalanceMinor is the balance AFTER this row is applied, clamped
// at zero [VERIFIED: RepaymentPeriod.java:387-401].
func (m *scheduleModel) outstandingLoanBalanceMinor(p *repaymentPeriod) int64 {
	last := p.segments[len(p.segments)-1]
	return maxInt64(0, last.outstandingMinor+last.disbursedMinor-m.duePrincipalMinor(p))
}

// initialBalanceMinor is the balance the level installment is computed from: the
// previous period's closing balance plus everything disbursed inside this one
// [VERIFIED: RepaymentPeriod.java:418-432].
func (m *scheduleModel) initialBalanceMinor(p *repaymentPeriod) int64 {
	var initial int64
	if prev := m.previous(p); prev != nil {
		initial = m.outstandingLoanBalanceMinor(prev)
	}
	for _, s := range p.segments {
		initial += s.disbursedMinor
	}
	return initial
}

// growthFactor is 1 PLUS THE SUM OF the period's segments' rate factors, added
// with no MathContext at all -- the additions are EXACT and the quantized rate
// factors' full width propagates into the recurrence
// [VERIFIED: RepaymentPeriod.java:214-217].
func (m *scheduleModel) growthFactor(p *repaymentPeriod) *big.Rat {
	out := big.NewRat(1, 1)
	for _, s := range p.segments {
		out.Add(out, s.rateFactor)
	}
	return out
}

// ---------------------------------------------------------------------------
// Rate factors
// ---------------------------------------------------------------------------

// calculateRateFactors fills both rate factors of every segment of p
// [VERIFIED: ProgressiveEMICalculator.java:636-644].
func (m *scheduleModel) calculateRateFactors(p *repaymentPeriod) {
	// Both rate factors are dependencies of the interest chain's step for this
	// period [VERIFIED: RepaymentPeriod.java:255-257 -> InterestPeriod.java:143-158].
	m.invalidateFrom(p.idx)
	for _, s := range p.segments {
		s.rateFactor = m.rateFactorForRecurrence(p, s)
		s.rateFactorTillDue = m.rateFactorForInterest(p, s)
	}
}

// rateFactorForRecurrence is calculateRateFactorPerPeriod's DAYS_30 arm
// [VERIFIED: ProgressiveEMICalculator.java:1486-1541, dispatch at :1536].
// Its multiplier is RepaymentEvery and its span is the segment's own window.
func (m *scheduleModel) rateFactorForRecurrence(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	return m.rateFactorByRepaymentPeriod(
		ratInt64(m.repaymentEvery),
		daysBetween(s.from, s.due),
		daysBetween(p.from, p.due))
}

// rateFactorForInterest is calculateRateFactorPerPeriodForInterest's DAYS_30 arm
// [VERIFIED: ProgressiveEMICalculator.java:1355-1418, dispatch at :1404-1413].
//
// It differs from the recurrence's factor in TWO arguments and only one of them
// is live: the MULTIPLIER is periodRatio, not RepaymentEvery, and the span runs
// from the segment's from-date to the ENCLOSING REPAYMENT PERIOD's due date. The
// days-in-month argument is 30 at both call sites on every reachable path, so a
// port must NOT "correct" it to differ between them.
func (m *scheduleModel) rateFactorForInterest(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	return m.rateFactorByRepaymentPeriod(
		m.periodRatio(p),
		daysBetween(s.from, p.due),
		daysBetween(p.from, p.due))
}

// rateFactorByRepaymentPeriod is the shared kernel
// [VERIFIED: ProgressiveEMICalculator.java:1947-1962].
//
//	if calculatedDaysInPeriod == 0 -> exactly ZERO, before any operation runs
//	fraction = daysInMonth * multiplier / daysInYear          (2 mc operations)
//	factor   = rate * fraction * actualDays / calculatedDays  (3 mc operations)
//	           then setScale(RateFactorScale, HALF_UP)
//
// The trailing setScale is a SCALE, not a precision: on a quantity of order
// 0.005 to 0.02 it is strictly lossier than the same count of significant
// digits, and the loss reaches a payable amount.
//
// The last two operations are a PRORATION whose denominator is the ENCLOSING
// REPAYMENT PERIOD's length and never the span's own. The ratio is 1 if and only
// if the span opens on that period's from-date; a disbursement dated strictly
// inside a period makes it strictly less than 1, and that term is the entire
// mechanism by which a mid-period advance is charged less than a full period.
func (m *scheduleModel) rateFactorByRepaymentPeriod(multiplier *big.Rat, actualDays, calculatedDays int64) *big.Rat {
	if calculatedDays == 0 {
		return new(big.Rat)
	}
	fraction := roundSignificant(new(big.Rat).Mul(m.daysInMonth, multiplier), m.precision)
	fraction = roundSignificant(new(big.Rat).Quo(fraction, m.daysInYear), m.precision)

	v := roundSignificant(new(big.Rat).Mul(m.rate, fraction), m.precision)
	v = roundSignificant(new(big.Rat).Mul(v, ratInt64(actualDays)), m.precision)
	v = roundSignificant(new(big.Rat).Quo(v, ratInt64(calculatedDays)), m.precision)
	return roundScale(v, m.scale)
}

// periodRatio is the interest call site's multiplier
// [VERIFIED: ProgressiveEMICalculator.java:1419-1459, seed at :1461-1481].
//
// It equals RepaymentEvery if and only if the period's window sits on the
// lattice ScheduleStartDate + j months. It leaves that lattice whenever the
// month-end re-anchor has moved a boundary, because the re-anchor is seeded on
// the DISBURSEMENT date while the seed here is the SCHEDULE START -- and that
// asymmetry between two seeds is the whole mechanism.
//
// Only the MONTHS arm is implemented: every other repayment unit is refused
// before any of this runs, and the YEARS arm of the enclosing dispatch throws in
// the oracle itself.
func (m *scheduleModel) periodRatio(p *repaymentPeriod) *big.Rat {
	seed := m.periodRatioSeed(p)

	// The whole-month count, by java.time's PACKED rule
	// (monthsUntil: (year*12 + month-1)*32 + day, difference divided by 32 and
	// truncated toward zero) [VERIFIED: DateUtils.java:308-317 ->
	// ChronoUnit.MONTHS.between].
	//
	// THE MONTH-END SPECIAL CASE at :1426-1436 is part of the rule, not an
	// optimisation: when the target is the last day of its month AND the seed's
	// day is later, the count is measured to the day AFTER the target. Keeping
	// the packed rule and dropping these four lines roughly DOUBLES periodRatio
	// on alternate periods.
	var months int64
	seedDay := seed.Day
	targetDay := p.from.Day
	if daysInMonth(p.from.Year, p.from.Month) == targetDay && seedDay > targetDay {
		months = monthsBetween(seed, plusDays(p.from, 1))
	} else {
		months = monthsBetween(seed, p.from)
	}

	multiplicator := months + 1
	cursor := p.from
	for compareDates(cursor, p.due) < 0 {
		cursor = plusMonths(seed, multiplicator)
		if compareDates(cursor, p.due) <= 0 {
			multiplicator++
			continue
		}
		fullPeriodDate := cursor
		multiplicator = multiplicator - months - 1
		cursor = plusMonths(seed, multiplicator)
		partial := daysBetween(cursor, p.due)
		whole := daysBetween(cursor, fullPeriodDate)
		// The division is the ONLY MathContext-rounded step; the addition of the
		// whole-period count is EXACT [:1451-1454].
		ratio := roundSignificant(new(big.Rat).Quo(ratInt64(partial), ratInt64(whole)), m.precision)
		return ratio.Add(ratio, ratInt64(multiplicator))
	}
	return ratInt64(multiplicator - months - 1)
}

// periodRatioSeed is calculateSeedDate [VERIFIED:
// ProgressiveEMICalculator.java:1461-1481]: the SCHEDULE START if the period's
// window lies exactly on the schedule-start lattice, otherwise the period's own
// from-date. BOTH conjuncts are required.
func (m *scheduleModel) periodRatioSeed(p *repaymentPeriod) civilDate {
	seed := m.startDate()
	multiplicator := int64(1)
	var calculated civilDate
	for {
		calculated = plusMonths(seed, multiplicator)
		multiplicator++
		if compareDates(calculated, p.due) >= 0 {
			break
		}
	}
	if compareDates(calculated, p.due) == 0 &&
		compareDates(plusMonths(calculated, -m.repaymentEvery), p.from) == 0 {
		return seed
	}
	return p.from
}

// ---------------------------------------------------------------------------
// The level installment
// ---------------------------------------------------------------------------

// calculateLevelInstallment is
// calculateEMIOnActualModelWithDecliningBalanceInterestMethod
// [VERIFIED: ProgressiveEMICalculator.java:1722-1741].
//
//	rateFactorN = product over the RELATED periods of their growth factors
//	fn          = fold over the related periods AFTER THE FIRST of
//	              fn' = 1 + fn * growth
//	EMI         = rateFactorN * openingBalance / fn
//
// Every one of those multiplications, divisions and additions is
// MathContext-qualified, INCLUDING the first product against BigDecimal.ONE: a
// growth factor is 1 plus a quantity of 19 decimal places, so it carries 20
// significant digits and the very first rounding is not a no-op.
//
// The installment is written onto the RELATED periods only. Rows before the
// first related period keep a ZERO installment and produce an all-zero row.
func (m *scheduleModel) calculateLevelInstallment(related []*repaymentPeriod) {
	if m.cancelled || len(related) == 0 {
		return
	}
	rateFactorN := big.NewRat(1, 1)
	for i, p := range related {
		if m.checkCancel(i) {
			return
		}
		rateFactorN = roundSignificant(new(big.Rat).Mul(rateFactorN, m.growthFactor(p)), m.precision)
	}
	fn := big.NewRat(1, 1)
	for i, p := range related {
		if i == 0 {
			continue
		}
		if m.checkCancel(i) {
			return
		}
		product := roundSignificant(new(big.Rat).Mul(fn, m.growthFactor(p)), m.precision)
		fn = roundSignificant(product.Add(product, big.NewRat(1, 1)), m.precision)
	}
	balance := majorFromMinor(m.initialBalanceMinor(related[0]), m.minorDigits)
	numerator := roundSignificant(new(big.Rat).Mul(rateFactorN, balance), m.precision)
	installment := roundSignificant(new(big.Rat).Quo(numerator, fn), m.precision)
	emi := minorFromMajor(installment, m.minorDigits)
	// The balance was read from the chain above; the installments are written
	// after it, so the invalidation belongs here and not before the read.
	m.invalidateFrom(related[0].idx)
	for _, p := range related {
		if emi >= 0 {
			p.emiMinor = emi
		}
	}
}

// applyFinalPeriodResidual is calculateLastUnpaidRepaymentPeriodEMI
// [VERIFIED: ProgressiveEMICalculator.java:1160-1219].
//
// THE FINAL ROW'S INSTALLMENT IS NOT THE LEVEL INSTALLMENT. It absorbs the whole
// residual, so its principal is the WHOLE REMAINING BALANCE rather than
// installment minus interest, and the schedule amortizes to exactly zero.
func (m *scheduleModel) applyFinalPeriodResidual(depth int) {
	if m.cancelled || depth > len(m.periods)+2 {
		return
	}

	// The oracle's guard at :1163-1174. totalDuePrincipal is the sum of the
	// periods' CREDITED AMOUNTS -- every disbursement, not the due principal
	// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:347-348 ->
	// RepaymentPeriod.getCreditedAmounts, :375-377]. Ported rather than dropped:
	// it is provably inert on an unpaid schedule and dropping a step because it
	// looks inert is how the two money defects of this program's first run
	// survived review.
	var totalDuePaidDiff int64
	for i, p := range m.periods {
		if m.checkCancel(i) {
			return
		}
		for _, s := range p.segments {
			totalDuePaidDiff += s.disbursedMinor
		}
	}
	for i, p := range m.periods {
		if m.checkCancel(i) {
			return
		}
		outstanding := m.duePrincipalMinor(p)
		if outstanding > totalDuePaidDiff {
			m.invalidateFrom(i)
			p.emiMinor -= outstanding - totalDuePaidDiff
			if p.emiMinor < 0 {
				p.emiMinor = 0
			}
		}
	}

	idx := m.findLastUnpaidPeriod()
	if idx < 0 {
		return
	}

	var totalDueInterest, totalEMI, totalDisbursed int64
	for i, p := range m.periods {
		if m.checkCancel(i) {
			return
		}
		totalDueInterest += m.dueInterestMinor(p)
		totalEMI += p.emiMinor
		for _, s := range p.segments {
			totalDisbursed += s.disbursedMinor
		}
	}
	m.invalidateFrom(idx)
	m.periods[idx].emiMinor += totalDisbursed + totalDueInterest - totalEMI
	if m.periods[idx].emiMinor < 0 {
		m.periods[idx].emiMinor = 0
		m.applyFinalPeriodResidual(depth + 1)
	}
}

// findLastUnpaidPeriod: the last period that is not fully paid, which on an
// untouched schedule means the last with a non-zero installment
// [VERIFIED: ProgressiveEMICalculator.java:1176-1181; isFullyPaid compares the
// installment against the total paid, RepaymentPeriod.java:361-363]. The fallback
// at :1178-1180 applies when every installment is zero.
func (m *scheduleModel) findLastUnpaidPeriod() int {
	for i := len(m.periods) - 1; i >= 0; i-- {
		if m.periods[i].emiMinor != 0 {
			return i
		}
	}
	for i := len(m.periods) - 1; i >= 0; i-- {
		if len(m.periods[i].segments) > 0 && m.outstandingLoanBalanceMinor(m.periods[i]) > 0 {
			return i
		}
	}
	return -1
}

// ---------------------------------------------------------------------------
// The EMI re-adjust smoothing loop
// ---------------------------------------------------------------------------

// emiAdjustment is getEmiAdjustment
// [VERIFIED: ProgressiveEMICalculator.java:1778-1789]: it scans from the END for
// the last ADJACENT pair in which NEITHER period is fully paid, and the scan
// requires idx > 0, so a single-element list falls to the degenerate branch whose
// difference is zero.
func emiAdjustment(list []*repaymentPeriod) (original, difference int64) {
	for idx := len(list) - 1; idx > 0; idx-- {
		last, penultimate := list[idx], list[idx-1]
		if last.emiMinor != 0 && penultimate.emiMinor != 0 {
			return penultimate.emiMinor, last.emiMinor - penultimate.emiMinor
		}
	}
	if len(list) == 0 {
		return 0, 0
	}
	return list[0].emiMinor, 0
}

// shouldBeAdjusted is EmiAdjustment.shouldBeAdjusted
// [VERIFIED: EmiAdjustment.java:31-36]. ALL THREE conjuncts are required.
//
// Money.copy(double) REPLACES the amount rather than scaling it
// [VERIFIED: Money.java:219-222], so the threshold is floor(n/2) whole currency
// units flat and the guard has no dependence on installment rounding. In minor
// units the comparison is |difference| * 100 against floor(n/2) * 10^minorDigits,
// and both sides are exact integers -- the doubles in the Java are an artefact of
// the reference implementation and are NOT reproduced.
func shouldBeAdjusted(n int, original, difference int64, minorDigits int32) bool {
	lowerHalf := int64(n / 2)
	if lowerHalf <= 0 || difference == 0 {
		return false
	}
	threshold := new(big.Int).Mul(big.NewInt(lowerHalf), pow10(minorDigits))
	left := new(big.Int).Mul(big.NewInt(absInt64(difference)), big.NewInt(100))
	return left.Cmp(threshold) > 0
}

// adjustEMIIfNeeded is checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
// [VERIFIED: ProgressiveEMICalculator.java:1258-1308].
//
// It runs on EVERY ordinary generation, not only when installment rounding is
// configured, and it moves money on ordinary loans. Five things it is easy to get
// wrong, each of which changes the schedule returned:
//
//   - THE DIVISOR IS n, the RELATED-period count, so the gap is spread across the
//     related periods rather than absorbed whole.
//   - THE TRIAL IS A REBUILD on a copy, not a patch: balances are recomputed and
//     the final-period residual re-applied before the trial is judged.
//   - THE ADOPTION TEST IS STRICT and its failure DISCARDS the trial, leaving the
//     live schedule at its pre-trial values. Equality is not adoption.
//   - break MEANS STOP. All four exits terminate the loop.
//   - THE COUNTER ADVANCES ONLY ON ADOPTION, and bounds the loop at three.
func (m *scheduleModel) adjustEMIIfNeeded(related []*repaymentPeriod) {
	if m.cancelled || len(related) == 0 {
		return
	}
	adjustCounter := 1
	for {
		// Once per OUTER iteration, which is the cadence the loop's own structure
		// offers: each iteration is a full rebuild on a copy, and the steps inside
		// it carry their own per-period checks.
		if m.checkCancel(0) {
			return
		}
		original, difference := emiAdjustment(related)
		if !shouldBeAdjusted(len(related), original, difference, m.minorDigits) {
			return
		}
		// uncountablePeriods counts periods whose total paid exceeds the original
		// installment [VERIFIED: :2027-2031]; it is identically zero on a schedule
		// this contract generates, and the divisor is therefore n.
		divisor := maxInt64(1, int64(len(related)))
		adjusted := original + divideMinorHalfUp(difference, divisor)
		// applyInstallmentAmountInMultiplesOf is the identity inside the graded
		// domain, where InstallmentRoundingMultipleMinor is 0 [:1270 -> :1761-1766].
		if adjusted == original {
			return
		}

		trial := m.deepCopy()
		firstFrom, firstDue := related[0].from, related[0].due
		for _, p := range trial.periods {
			if compareDates(p.from, firstFrom) >= 0 && compareDates(p.due, firstDue) >= 0 && adjusted >= 0 {
				trial.invalidateFrom(p.idx)
				p.emiMinor = adjusted
			}
		}
		trial.updateOutstandingBalances()
		trial.applyFinalPeriodResidual(0)
		if trial.cancelled {
			m.cancelled = true
			return
		}

		// The adoption test re-measures over the trial's FULL period list, not the
		// related sublist [:1289]; only the magnitude of the difference is read, so
		// the differing list does not matter.
		_, newDifference := emiAdjustment(trial.periods)
		if !(absInt64(newDifference) < absInt64(difference)) {
			return
		}

		var trialRelated []*repaymentPeriod
		for _, p := range trial.periods {
			if compareDates(p.from, firstFrom) >= 0 && compareDates(p.due, firstDue) >= 0 {
				trialRelated = append(trialRelated, p)
			}
		}
		for i, p := range related {
			if i >= len(trialRelated) {
				break
			}
			m.invalidateFrom(p.idx)
			p.emiMinor = trialRelated[i].emiMinor
		}
		m.updateOutstandingBalances()

		adjustCounter++
		if adjustCounter > 3 {
			return
		}
	}
}
