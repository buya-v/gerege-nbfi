# Driver re-derivation — G-8's mechanism, from source, at pinned `426a23544`

**Fire** `20260820-200002` (local, oracle reachable). **Written by the `/softhouse-program` driver**, from
the pinned Fineract checkout only — not from T75's review, and not from any capture. Committed *before*
T83 or T84 reported, so it is falsifiable by both.

**Status: a HYPOTHESIS with citations, not a measurement.** Everything below marked `[VERIFIED]` is read
directly from the pinned source. The causal claim at the end is explicitly `[UNVERIFIED]` and T83/T84 are
asked to **refute** it.

## What the driver read

All in `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/RepaymentPeriod.java`
at pinned `426a23544`.

1. **The balance column is memoized, and its memo key omits `emi`.** [VERIFIED: `RepaymentPeriod.java:389-403`]

   ```java
   public Money getOutstandingLoanBalance() {
       if (outstandingBalanceCalculation == null) {
           outstandingBalanceCalculation = Memo.of(() -> {
               ...
                       .minus(getDuePrincipal(), getMc());          // :398
               return MathUtil.negativeToZero(calculatedOutStandingLoanBalance, getMc());
           }, () -> new Object[] { paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount });  // :400
       }
       return outstandingBalanceCalculation.get();
   }
   ```

   The memoized body **subtracts `getDuePrincipal()`** at `:398`. `emi` is **not** in the dependency
   array at `:400`.

2. **`getDuePrincipal()` is a direct function of `emi`.** [VERIFIED: `RepaymentPeriod.java:345-350`, `:293-295`]
   `getDuePrincipal()` = `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest() - getDueInterest()`,
   and `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest()` = `getEmi() + ...` at `:294`.

3. **The omission is asymmetric within the same class, so it is not a house convention.**
   [VERIFIED: `RepaymentPeriod.java:272-286`] `getDueInterest()`'s memo key is
   `{paidPrincipal, paidInterest, interestPeriods, futureUnrecognizedInterest, totalDisbursedAmount,
   fixedInterest, reAged, emi, interestPaymentGrace}` — **`emi` IS present.** Two memos in one class,
   both transitively depending on `emi`; one declares it, one does not.

4. **`emi` is a mutable field.** [VERIFIED: `RepaymentPeriod.java:58` `private Money emi;`, assigned at `:123`]

5. **`Memo` recomputes only when a declared dependency's hashCode changes.**
   [VERIFIED: `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/util/Memo.java`,
   `get()` / `checkDependencyChangedAndUpdate()`] An undeclared dependency changing therefore
   **cannot** invalidate the cached value. `RepaymentPeriod` is `@EqualsAndHashCode(exclude = {"previous"})`
   [VERIFIED: `:43`], so the `interestPeriods` element hashes are what would have to move.

## The hypothesis `[UNVERIFIED]`

If `getOutstandingLoanBalance()` is evaluated at any point while `emi` is still `0.00`, and `emi` is
subsequently raised to `0.01` by the final-period adjustment **without** any of the four declared
dependencies changing hash, then the cached balance is **frozen at its pre-adjustment value** and every
later read returns it. That would produce exactly the reported symptom: `emis [...,'0.01']` on the last
row while `balance` stays `0.01`.

The driver has **NOT** verified the call order in the EMI calculator that would be required for the memo
to be populated pre-adjustment. **That is the load-bearing step and it is unproven here.**

## The reframing this suggests — and why it matters to the options

Read T75's own captured rows again (`.softhouse/reviews/T75-pathA-multiplesof-review.md` §5):

- disbursement `0.01`;
- principal column `0.00 ×5` then `0.01` — **it sums to `0.01`, i.e. the principal column amortizes
  correctly and fully**;
- `totalOutstandingAmount "0"` — **the oracle's own total already says zero**;
- only the **balance** column stays at `0.01`.

So the schedule is **internally inconsistent with itself**, in one derived column, in a direction its own
totals contradict. If that holds up, G-8 is materially narrower than "the reference oracle does not
amortize principal to zero": it is "**the oracle's outstanding-balance column is stale with respect to its
own final EMI adjustment, while its principal column and its own totals are right.**"

That distinction changes what a remedy costs. A defect confined to one derived column, contradicted by the
same schedule's totals, is a far better fit for **option (a)** — promote the region with an explicit
exemption scoped to the balance column — than a genuine failure to amortize would be, and it makes the
exemption precisely specifiable instead of open-ended.

**It changes nothing about the gate.** Fineract is the oracle; an oracle defect is still authoritative
until a `user` decision says otherwise. **(b) and (c) remain hard `user` gates and no agent may cross them.**

## What T83 and T84 are asked to do with this

**Try to refute it.** Specifically:

- Does the principal column sum to the disbursed amount in **every** case in the failing region, or only
  in the ones T75 happened to print? If it ever fails to sum, the reframing above is **wrong** and G-8 is
  the broader finding after all.
- Does `totalOutstandingAmount` disagree with the balance column across the whole region?
- Is the balance read **order-dependent**? A memo-staleness defect predicts that a probe which reads the
  balance without first driving the EMI adjustment can differ from one that does. A genuine
  non-amortization predicts no order dependence at all. **This is the cleanest discriminator and it is
  cheap to run.**
- Verify or refute step 5's missing link: find whether the EMI calculator actually reads
  `getOutstandingLoanBalance()` before the final adjustment. Note `getInitialBalanceForEmiRecalculation()`
  at `:414-426` reads `getPrevious().get().getOutstandingLoanBalance()` **during** EMI recalculation —
  that is the driver's candidate for the populating call, and it is a candidate, not a finding.

**The boundary measurement must stand on its own without this note.** If T83's measured boundary depends
on believing the driver's mechanism, T83 has not measured a boundary.
