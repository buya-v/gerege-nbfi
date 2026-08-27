# T71 — independent review of `softhouse/T70-fui-marker`

Run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`, role `reviewer`, model opus.
Reviewed `git diff main...softhouse/T70-fui-marker` at branch head `ffaaab8`, `main` at `786c43b`,
merge base `14c447b`. Reference oracle checkout `/Users/buv/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty.

> Terminology: "the oracle" is the **Fineract reference implementation** at the pinned commit.
> Oracle Database is prohibited in this program and nothing here touches a database.

Honesty rule: every claim below is marked `[VERIFIED: source]` or `[UNVERIFIED]`. Where I did not
look, I say so.

---

## Verdict

**REJECTED.**

Not for the executable change — there isn't one, and I re-verified that independently. The
deliverable here is a *rule* (P-13), and the rule is **not sufficient**: I can construct an
admission that satisfies every one of T70's five numbered conditions and still routes the
`futureUnrecognizedInterest` decision down a path that none of steps (a)–(g) covers. Worse, that
is not a hypothetical — **the graded corpus already contains such a vector, and it passes today**.
Condition (5) additionally asserts something false about `:247`, and that falsehood is exactly what
would keep a reader from noticing.

This is the same failure mode T67 caught in T65's replacement text (`p.idx` filed under "NOT read"
when it is the memo's lookup key): everything executable is right, the conclusion is right, and the
*rule the next contributor checks a new write site against* is not sufficient. Fourth draft
required.

Findings: **R-1 (P1, sufficiency + false statement)**, **R-2 (P2, mis-citation)**, **R-3 (P3,
precision loss)**, **R-4 (P3, internal inconsistency)**. Everything else in the block I checked is
clean, and a good deal of it is unusually well done — see the last two sections.

---

## Citations resolved, one line each

Unqualified `:N` means `ProgressiveEMICalculator.java`, the convention the block uses throughout
(and the convention T70's own handoff declares). Every line below I opened myself at `426a23544`
and walked up to its enclosing signature.

| citation | resolves to | verdict |
|---|---|---|
| `:142-144` | `addDisbursement` (private, `:137`) — the `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` guard | ✅ |
| `:145-151` | same method, the `else` (ordinary) arm; `getEffectiveRepaymentDueDate` at `:150` | ✅ |
| `:155-174` | `addFullTermTrancheDisbursement`; `mergeNewScheduleModelWithExistingOne` at `:173` | ✅ |
| `:206-248` | `mergeNewScheduleModelWithExistingOne` | ✅ |
| `:247` | inside that method — `calculateLastUnpaidRepaymentPeriodEMI(scheduleModel, operation.getSubmittedOnDate())` | ✅ line correct; **see R-1 for what the text says about it** |
| `:250-263` | `getEffectiveRepaymentDueDate`; `isEqual` `:252`, next-period return `:257`, fallback `:262` | ✅ |
| `:259` (in rule (4)) | `ProgressiveEMICalculator.java:259` is the comment `// Currently N+1 scenario is not supported.` | ❌ **R-2** |
| `:372-382` | `addOverdueBalanceCorrection`; `recordOverdueCorrection` at `:377` | ✅ |
| `:718-728` | `calculateEMIValueAndRateFactors`; `DECLINING_BALANCE` arm `:723` | ✅ |
| `:730-751` | `calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod` | ✅ |
| `:747` | the ordinary entry, arg `calculateFromRepaymentPeriodDueDate` | ✅ |
| `:749` | `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`, under `onlyOnActualModelShouldApply` | ✅ |
| `:1160` | `private void calculateLastUnpaidRepaymentPeriodEMI(model, tillDate)` | ✅ |
| `:1176-1177` | last-not-fully-paid selector (`filter(!isFullyPaid).reduce(second)`) | ✅ |
| `:1178-1181` | fallback selector, guarded on the filter being empty **and** `getTotalPaidPrincipal().isZero()` | ✅ |
| `:1183-1184` | `ifPresent` + `setFutureUnrecognizedInterest(zero)` | ✅ |
| `:1189-1203` | `mc`, `totalDueInterest`, `totalEMI`, `totalDisbursedAmount`, `totalCapitalizedIncome`, `diff` at `:1202-1203` | ✅ |
| `:1205` / `:1210` | `adjustedEmi = getEmi().add(diff, mc)` / `setEmi(adjustedEmi)` — T66/PASS3H's `:1207` was indeed the `getFixedInterest()` guard | ✅ **correction confirmed** |
| `:1206-1208` | the `getFixedInterest().isGreaterThanZero()` override of `adjustedEmi` | ✅ |
| `:1211-1215` | the self-recursion guard and the `:1214` recursive call | ✅ |
| `:1217` | `calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer(...)` | ✅ |
| `:1221-1252` | that method | ✅ |
| `:1224` | `scheduleModelCopy = scheduleModel.deepCopy(mc)` — `:1226` is a comment line | ✅ **correction confirmed** |
| `:1229-1241` | the overdue reverse/rebuild block | ✅ |
| `:1237` | `calculateRateFactorForScheduleTillDateInclusive(scheduleModelCopy, tillDate)` | ✅ |
| `:1240` | `calculateOutstandingBalance(scheduleModelCopy)` under `shouldResetOverdue` | ✅ |
| `:1246` | `repaymentPeriod.setFutureUnrecognizedInterest(period.getUnrecognizedInterest())` — `:1250` is a `}` | ✅ **correction confirmed** |
| `:1278` / `:1288` | `relatedPeriodsFirstDueDate` / the trial-copy entry, both in `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (`:1258-1309`) | ✅ |
| `:1674` / `:1680` | `calculateEMIOnActualModel` / its `DECLINING_BALANCE` dispatch | ✅ |
| `:1708-1720` / `:1830-1832` | `applyInterestMoratoriumIfRequired` / `getRateFactorPlus1ForEmi` | ✅ |
| `:1722-1742` / `:1736-1741` | `calculateEMIOnActualModelWithDecliningBalanceInterestMethod` / the `forEach`+`setEmi` onto the **passed list only** | ✅ |
| `:1791-1803`, `:1799`, `:1800-1801` | `calculateRateFactorForScheduleTillDateInclusive`; `targetDate.isBefore(ip.getDueDate())`; the two `BigDecimal.ZERO` writes | ✅ |
| `:1805-1814`, `:1808`, `:1809` | `getPeriodWithUnrecognizedInterest`; `isGreaterThanZero`; `isAfter` | ✅ |
| the 14 call sites in (5) | `:368` `addBalanceCorrection` (`:362`), `:380` `addOverdueBalanceCorrection` (`:372`), `:404` `payInterest` (`:385`), `:442` `payPrincipal` (`:408`), `:505` `addCredit` (`:498`), `:626` `getOutstandingAmountsTillDate` (`:621`), `:698` `recalculateScheduleModelTillDate` (`:647`), `:868` `changeDueDate` (`:831`), `:879` `updateModelRepaymentPeriodsDuringReAmortization` (`:872`), `:937` `…WithEqualInterestSplit` (`:884`), `:1091` `attachTemporaryScheduleModelReAgedPeriodsToExistingModel` (`:1039`), `:2024` `calculateRateFactorsForInterestPause` (`:2020`), `:2129` `reAgeEqualAmortization` (`:2079`), plus `:247` | ✅ every enclosing method matches the label |
| the arithmetic of (5) | `grep` returns 17 call lines besides the declaration; "besides `:747`, sixteen call sites", 14 + 2 | ✅ |
| `RepaymentPeriod.java:252-265`, `:261-263` | `calculateCalculatedDueInterest`; the `getPrevious().get().getUnrecognizedInterest()` term | ✅ |
| `RepaymentPeriod.java:272-286`, `:280`, `:293-295` | `getDueInterest` + memo; the `MathUtil.min`; `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest` | ✅ |
| `RepaymentPeriod.java:371-373`, `:381-383` | `isFullyPaid`; `getUnrecognizedInterest` | ✅ |
| `InterestPeriod.java:145-157`, `:155` | `getCalculatedDueInterest(method, length)`; `multiply(getRateFactorTillPeriodDueDate(), …)` | ✅ |
| `InterestPeriod.java:168-186` | `updateOutstandingLoanBalance` — the only field it assigns is `outstandingLoanBalance` | ✅ |
| `ProgressiveLoanInterestScheduleModel.java:106-108`, `:191-198`, `:196` | `recordOverdueCorrection`; `getRelatedRepaymentPeriods`; the `!isBefore(dueDate, d)` filter | ✅ |
| (a)'s "written only by `addOverdueBalanceCorrection`" | `grep overdueCorrections` in the model returns `:72` decl, `:107` the only `add`, `:111`/`:115` readers, `:123-126` the reverse/clear, `:133` the `deepCopy` carry-over | ✅ |
| `conformance/admit.go:1018-1020`, `:999-1060` | the `len(r.Disbursements) != 1` predicate inside `GradedDomain` | ✅ lines correct; **see R-1 for what the text infers from it** |
| `contract.go:1330-1342` | the `Disbursements` doc comment, "Multi-tranche disbursement … arrives with the loan lifecycle" | ✅ |
| `T66.md:100-108` / `:110-115` | step (e)'s general-`f` form / the `cdi_f ≤ P` bound | ✅ |
| `PREDICTION.md:100-105` / `:107-130` | the incomplete `cdi_f ≤ P + emi_f` form / the dated CORRECTION block | ✅ |
| `PASS3H-REPORT.md:138-149` | "What this pass does NOT establish" — real-model-not-the-copy, plus the lapse list | ✅ |

**One in-scope citation is wrong (R-2); every other one resolves to the method the text names.**
Three drifted numbers T70 claimed to correct (`:1224`, `:1246`, `:1205`/`:1210`) are corrected and
the corrections are right — I checked each against the pinned file, I did not take them on trust.

---

## Sufficiency: can I break the port while obeying every clause?

**Yes.** Here is the construction.

Admit a vector with **exactly one disbursement** and a product carrying
`allowFullTermForTranche = true`.

- Condition **(1)** — "EXACTLY ONE DISBURSEMENT" — satisfied. Literally one element.
- Condition **(2)** — nothing paid — satisfied.
- Condition **(3)** — no credits, no capitalized income — satisfied.
- Condition **(4)** — no fixed interest, no re-aging, no interest pause — satisfied.
- Condition **(5)** — "THE SEAM STAYS A PURE ORIGINATION CALL" — satisfied on its face: this *is*
  origination, it is a disbursement, and (5)'s own list tells the reader that the sites to worry
  about are "**post-origination** operations".

And yet: `addDisbursement` takes the tranche branch, because the guard is
`isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` and **never
consults how many disbursements there are** [VERIFIED: `ProgressiveEMICalculator.java:142-144`].
The call goes `:144 → addFullTermTrancheDisbursement (:155-174) → mergeNewScheduleModelWithExistingOne
(:206-248) → :247`, entering `calculateLastUnpaidRepaymentPeriodEMI` with
`tillDate = operation.getSubmittedOnDate()` — **the disbursement date, not the period due date**.

That voids step **(b)** outright, which is the anchor the whole cascade argument stands on. It also
voids step **(e)**'s "`emi_j = 0` for every `j < f`" premise, because the merge writes
`existingRepaymentPeriod.get().setEmi(getEmi().add(newPrincipal.add(newInterest)))` onto **existing**
periods [VERIFIED: `:228`], not onto a window list. Two of the seven proved steps are gone and no
clause of the rule told the reader to stop.

### R-1 (P1). The rule names the wrong guard, and (5) states a falsehood

Three separable defects, one root:

**(a) Condition (1)'s stated reason is false.** It says "Multi-tranche breaks (b) outright, because
the tranche branch enters `:1160` at `:247`". The tranche branch is not entered because of
multi-tranche; it is entered because of a **product flag**. This is P-11/P-12 in its textbook shape:
right conclusion (multi-tranche does break things), wrong reason, and the reason is what the next
contributor checks against.

**(b) The condition that actually protects (b) is missing.** What keeps `:247` out of the Go
module is the pin `allowFullTermForTranche = false`, and the port's own frozen contract already
says so, in terms that contradict T70's sentence [VERIFIED: `contract/contract.go:1179`, `:1191-1202`]:

> `allowFullTermForTranche = false` is a REAL BEHAVIOURAL PIN, not a dead field. … **the guard that
> consumes it never consults multi-disbursement at all** … **Setting it true on an ordinary single
> disbursement routes into a full re-amortization** through a synthetic terms object and a temporary
> schedule model (`:155-174`). … two captures differing only in this flag … are identical, so on this
> shape the alternative path coincides — **which is a measurement, not a licence to ignore the flag.**

T70's block never names the pin. A rule that omits the only condition standing between the reader
and the path it says is uncovered is not a rule.

**(c) Condition (5) says something false, and it is the load-bearing falsehood.** It writes:
"FOURTEEN belong to **post-origination** operations … `:247` tranche merge, …". `:247` is reached
from `addDisbursement`. It is an **origination** call. Filing it under "post-origination" is the
precise miscue that lets a reader satisfy "(5) THE SEAM STAYS A PURE ORIGINATION CALL" while
standing on `:247`. (T70's handoff records catching a *neighbouring* version of this — it removed
`:1214` and `:1288` from the post-origination list mid-flight. `:247` was left in.)

### This is not hypothetical — the corpus grades it today

`.softhouse/vectors/loanschedule/P-04t-fulltermfortranche-true.json` is a **parity vector, class
`parity`, currently PASSing** (I ran the harness; `P-04t` reports PASS, 47 cells). Its
`request.disbursements` has **exactly one element** and its own title records the capture condition
[VERIFIED: the vector file]:

> "allowFullTermForTranche = TRUE at the production MathContext. Observed output is byte-identical
> to P-04f and P-00, which is the evidence that the flag is INERT on this shape. **The contract has
> no field for it, so this vector's request is byte-identical to P-00's and P-04f's.**"

The harness prints the same fact in its own standing-claims section: "It IS reached when the flag is
true … the flag is confirmed live and schedule-neutral on a **single-disbursement** loan" (T17-F3,
`[NARROWED-BY-OBSERVATION]`).

So: a vector whose oracle run took the `:247` entry is inside the graded corpus, while the block
closes with "**This block is about the `:747` entry**" and all **18 of 18** pass-3h observation
cases ran with `allowFullTermForTranche = false` [VERIFIED: re-derived by me from
`.softhouse/capture/out/capture-prod3h-raw.json` — 18/18 `"allowFullTermForTranche": false`]. The
observation does not cover a path the corpus already grades, and the rule does not say so.

**Being fair about the blast radius, because the asymmetry cuts both ways.** P-04t's expected cells
are byte-identical to P-04f's, so **no money is wrong today** and no vector is red. The defect is in
the rule, not in the schedule. But P-13 is explicit that for a specification-bearing comment the
rule *is* the deliverable, and P-14 is explicit that "no vector distinguishes it" is a blind spot,
not an absence. A rule that would wave through the one shape it claims to forbid is a P1.

**What a fourth draft has to do** (not my job to write it, but the shape is forced):

1. Add a condition — `allowFullTermForTranche = false` — citing `contract.go:1179` / `:1191-1202`,
   and state that the guard at `:142-144` is a **product flag, not a disbursement count**.
2. Rewrite (1)'s justification: multi-tranche breaks (b) because each `addDisbursement` re-enters
   with **its own** `tillDate` (`:145-151`), not because it routes to `:247`.
3. Reclassify `:247` in (5): it is an **origination** entry gated by the flag, not a
   post-origination operation. Thirteen post-origination sites, not fourteen.
4. Say plainly that `P-04t` is graded and takes the `:247` entry, so the flag-true path is inside
   the corpus and outside the observation.

I did **not** attempt to determine whether `futureUnrecognizedInterest` actually stays zero on the
`:247` path — that would be settling it by reading, which is the move this whole task family exists
to forbid. It is a capture question. `[UNVERIFIED]`

---

## Proved vs observed vs assumed — is the separation honest?

Yes, and this part of the draft is genuinely good. Judged clause by clause:

- **PROVED (a)–(g)** are deductions from the pinned source, and every one of the mechanical steps I
  re-derived myself checks out. (a)'s overdue-branch dismissal is *better* than it needed to be: the
  zeroing at `:1237` happens **before** the `:1240` rebuild, and the rebuild only writes
  `outstandingLoanBalance` [VERIFIED: `InterestPeriod.java:168-188`], so a zeroed rate factor cannot
  be restored — the argument holds even without the "no origination path calls it" leg. Correctly
  labelled proof, not observation.
- **The (e) caveat is preserved, not smoothed.** "THE BOUND IN (e) IS NOT TIGHT above a per-period
  rate factor of 1.00. Above that the conclusion is carried by the capture and the census below, not
  by the inequality. Do not restate it as a tight bound." That is exactly the honest form, and it
  matches `T66.md:118-120` and `PREDICTION.md:128-130`. ✅
- **The `PREDICTION.md` warning is correct and non-obvious.** `PREDICTION.md:100-105` really does
  state the sufficient condition as `cdi_f ≤ P + emi_f` **without** the `emi_j = 0 for j < f`
  premise, and really does carry a dated CORRECTION block at `:107-130` saying it is exact only at
  `f = 0`. Telling a future reader to cite `T66.md:100-108` instead of the incomplete form is the
  right instruction and I could not fault it.
- **OBSERVED is observation, and every number is real.** I re-derived from
  `capture-prod3h-raw.json` independently: **18 cases**, **416 mechanism rows**, and on all 416
  rows `futureUnrecognizedInterest == "0.00"`, `interestMovedUpward == false`,
  `unrecognizedInterest == "0.00"` — **0 exceptions**; `pathIdentity.identical` true on **18/18**;
  8 `P-CAL-*` rig calibrations present (including `P-CAL-ZPA`/`P-CAL-ZPB`, the promoted
  `T64-ZP-A`/`T64-ZP-B`). Computing `L` as the last not-fully-paid period and counting zero-EMI rows
  strictly after it, **exactly five** cases carry the structural precondition, with tails
  **`P-CAL-ZPB` 40, `T66-M-R12000` 10, `T66-M-DRIFT-R12000` 10, `T66-M-DRIFT-R2400` 3,
  `T66-M-FLOOR-HR` 3** — the block's five names and five numbers, unchanged. `T66-M-R12000`'s inputs
  are `annualNominalInterestRate 12000`, `DAYS_30`/`DAYS_360`, monthly ⇒ per-period factor **10.00**
  ✅. `T66-M-DISB-ON-DUE` period 0 `emi == "0.00"` ✅ (the `f = 1` evidence). The digest
  `fdd751a2…b90b73` is the `capturesCanonicalSha256` in `capture-prod3h-attestation.json:15` and is
  independently restated in the driver re-derivation and `program.json`. ✅ Nothing inflated.
- **SEARCHED is attributed and disclaimed.** 21,060 / 9,437 / 156 / 0, credited to T66 and the
  driver, marked "**NOT re-run at T70**", with the reason (the harness survives only as
  `t66_search_test.go.txt`, which I confirmed exists). I did not re-run it either. ✅
- **NOT CLAIMED (i)** matches `PASS3H-REPORT.md:138-149` faithfully: the copy's internal `u_k`
  cascade was never observed by anyone, and the capture establishes the **outcome** of the one
  decision. Nothing in the block asserts anything about the copy's internal state. ✅ This was the
  specific thing I was asked to hunt for and I did not find it violated.
- **NOT CLAIMED (ii)** is marked `[UNVERIFIED]` where a weaker reviewer would have wanted a
  resolution. **That is correct behaviour and I am crediting it, not penalising it** — same as T63
  withdrawing its own finding and T69 refusing a third reason.
- **NOT CLAIMED (iii)** — the graded-domain limit — present. ✅

Two honesty defects, both minor, neither dressing empirical work as proof:

### R-3 (P3). (d) drops T66's qualifier and the sentence stops being true

(d) says "So at lookup time `sum_j emi_j = P + I`, with `P` the disbursed principal and `I` the
total due interest **as measured on the real model**". T66 wrote "`I = Σ_j dueInterest_j` as measured
on the real model **just before the assignment**" [VERIFIED: `T66.md:96-97`]. The qualifier is
load-bearing: `getDueInterest()` is memoised on a key that **includes `emi`** [VERIFIED:
`RepaymentPeriod.java:278-283`], so the `:1210` write invalidates period `L`'s memo and the
post-assignment total can strictly exceed the `I` that went into `diff`. At lookup time the identity
holds for the *pre-assignment* `I` only. The conclusion survives — (e) uses `I` only through
`I ≥ 0` — but the sentence as written is false at the moment it names.

### R-4 (P3). (i) and (ii) contradict each other

(i) says "on the generate path `:1160` is entered on the real model **once**, at `:747`". (ii) says
`:1211-1215` re-enters `:1160` — and it re-enters on `scheduleModel`, the **real** model, not a copy
[VERIFIED: `:1214` passes `scheduleModel`]. Both cannot be true. (i) is inherited verbatim from
`PASS3H-REPORT.md:141-143`, which predates the recursion finding, so this is P-12 again: the new
finding was added in (ii) and not swept back through the sentence it falsifies. The *conclusion* of
(i) survives — the outer frame's `:1217` is still the last act, so the observed value is still the
outcome of the last decision — but "entered … once" should read "the field write at `:1246` is the
last act on the real model, and the outer frame's `:1217` runs last even under (ii)".

### Premise list that lapses — present and correct

Multi-tranche (1), payments (2), credits **and** capitalized income (3), fixed interest / re-aging /
interest pauses (4). All six named premises from `PASS3H-REPORT.md:147-149` are present, plus the
seam condition (5) and the standing instruction that the field is ported **before** a wider shape is
admitted. ✅ The list is complete; R-1 is that condition (1)'s *reason* and condition (5)'s
*classification* are wrong, not that an item is missing from the list.

### R-2 (P2). `:259` in condition (4) resolves to a comment line

`(4) NO FIXED INTEREST [:259, :1206-1208]` (branch `emi.go:464`). Under the block's own convention —
unqualified `:N` = `ProgressiveEMICalculator.java`, used for `:1206-1208`, `:1708-1720` and
`:1830-1832` **in the same sentence** — `:259` is
`// Currently N+1 scenario is not supported.`, a comment inside `getEffectiveRepaymentDueDate`
[VERIFIED]. The intended referent is **`RepaymentPeriod.java:259`**,
`calculatedDueInterest = calculatedDueInterest.add(getFixedInterest())` [VERIFIED], which is what
T70's own handoff table records as the resolution. The handoff resolved it correctly and the comment
wrote it unqualified. Mechanical to fix; noted here because it lands in the paragraph whose own
instruction is "Resolve every citation you add here to its enclosing method before you write it
down", and because R-1 shows this block cannot afford a second cheap-looking citation error.

---

## F-2 and the orchestrator's reduction

**The reduction holds, and it holds more strongly than the orchestrator put it.** Checking each link
the orchestrator asked me to check rather than assume:

1. **Is `getEmi()` at `:1211` the post-`:1210` value?** Yes. `:1210` is `repaymentPeriod.setEmi(adjustedEmi)`
   and `:1211` reads `repaymentPeriod.getEmi()` on the same object [VERIFIED: `:1205-1213`].
2. **Is `totalPaidAmount` zero on the graded domain?** Yes —
   `getTotalPaidAmount() = getPaidPrincipal().plus(getPaidInterest())` [VERIFIED:
   `RepaymentPeriod.java:367-369`], and nothing is paid.
3. **Is `totalCreditedAmount` really zero on this path?** Yes, and it is *not* trivially so —
   `getTotalCreditedAmount() = creditedPrincipal + creditedInterest − creditedInterestMovedDueReAge
   − creditedPrincipalMovedDueReAge` [VERIFIED: `RepaymentPeriod.java:357-359`]. All four terms are
   zero on the graded domain: the first two by condition (3), the last two by condition (4)'s
   no-re-aging clause. So the RHS is exactly zero, not merely "zero when nothing is paid".

So on the graded domain the `:1211-1212` guard **is exactly `emi_L < 0`**. The refinement holds.

**And the port already encodes precisely that.** `applyFinalPeriodResidual` on the branch reads
`if m.periods[idx].emiMinor < 0 { m.periods[idx].emiMinor = 0; m.applyFinalPeriodResidual(depth + 1) }`
[VERIFIED: branch `nexus/internal/apps/loanschedule/emi.go:1206-1210`]. Same guard, same clamp,
same re-entry — so on the graded domain oracle and port agree on when the recursion fires, and F-2's
firing condition is a single sign test on one integer.

**Did T70 over- or understate F-2?** **Neither, materially.** (ii) already carries the parenthetical
"(zero when nothing is paid)", which is the reduction in weaker words, and it is careful to call the
coverage "empirical, not deductive" and to mark the preservation claim `[UNVERIFIED]`. I found
nothing overstated. What (ii) *misses* is the sharpening — it could say outright "on the graded
domain the guard reduces to `emi_L < 0`, and the port's own `emiMinor < 0` at the residual is the
same test", which would tell a future capture-writer exactly what to hunt for and would narrow F-2
from "the recursive frame" to "can the residual drive `emi_L` strictly negative on an admitted
shape". That is an improvement, not a correction, and I would not reject on it alone.

**Can `emi_L` go negative?** I did **not** establish it either way. `[UNVERIFIED]` What I can say is
that nothing structurally forbids it: `:1205`'s `add(diff, mc)` has no floor except the
`getFixedInterest()` override at `:1206-1208` (excluded by condition (4)), and the earlier
`:1165-1174` loop's floor is `minimumEMI = paidInterest + paidPrincipal = 0`, which clamps *that*
loop's subtraction but says nothing about `diff`. So the orchestrator is right not to assume it
cannot happen, and T70's F-2 ("find or construct an admitted shape on which `:1214` actually fires
— the port's `depth` parameter is the cheap detector") remains the right follow-up, phrased the
right way: **by capture, not by reading**.

**Does the comment need to change on account of F-2?** No. The rejection is R-1, not F-2.

---

## Verification exit codes

Sourcing `.softhouse/bin/go-env.sh` is **blocked in my sandbox** (the harness refuses a command that
runs a string through `.`). As permitted, I read the script and exported the same four variables by
hand — `GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go`, `GOPATH=…/gopath`,
`GOCACHE=…/gocache`, `GOMODCACHE=…/gomodcache`, with `$GOROOT/bin` prepended to `PATH` — and invoked
the toolchain by absolute path. `go version` = **`go1.26.6 darwin/arm64`**, the expected repo-local
toolchain. All runs on the branch head `ffaaab8` checked out into this worktree.

| check | exit | detail |
|---|---|---|
| `go build ./...` | **0** | no output |
| `go vet ./...` | **0** | no output |
| `go test ./... -count=1` | **0** | `loanschedule 8.494s ok`, `conformance 6.118s ok`, two packages with no test files |
| `.softhouse/conformance.sh` | **0** | **36 parity PASS / 0 FAIL**, 4 contract-refusal PASS, 1 self-test PASS, **4034 graded cells** (72 ungraded), 0 refused, 0 inadmissible, 0 harness errors, 0 invariant violations, 0 invariant assertions NOT RUN; reference-oracle probe **UP** |
| `.softhouse/conformance.sh --prove` | **0** | **PROOFS: 21 passed, 0 failed** |
| `gofmt -l nexus/internal` | 0 | names **exactly** `nexus/internal/apps/loanschedule/contract/contract.go` — the expected G-3 Option A state. `emi.go` is **not** listed. I did **not** run `gofmt -w` on anything. |

Every number matches T70's handoff and the driver's pre-T66 baseline. Nothing executable moved, and
the executable state is green — which is precisely why this rejection is about the prose.

---

## What I checked and found clean

So that silence is distinguishable from not looking:

- **Zero executable change, re-verified independently, two ways.**
  (i) `git diff main...softhouse/T70-fui-marker -- nexus/ | grep -E '^[+-]' | grep -v '^[+-][+-]' |
  grep -vcE '^[+-][[:space:]]*//'` → **0**.
  (ii) Comment-stripped comparison of `main:emi.go` against `branch:emi.go` → **`diff` exit 0**,
  **609 lines each** (**532** ignoring blank lines, which reconciles the orchestrator's figure with
  T70's — the two counts differ only in whether blank lines are dropped, and both say *identical*).
- **Scope.** `git diff main...branch --name-only` returns exactly two paths:
  `nexus/internal/apps/loanschedule/emi.go` and
  `.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T70.md`. Nothing else in the repo moved.
- **`contract.go` untouched** — absent from the diff, and `gofmt -l` still names it and only it.
- **No non-negotiable tripped.** No floating point introduced (nothing executable introduced at
  all); no MySQL/MariaDB/**Oracle Database** driver, dialect, `ojdbc`, `oracle.jdbc` or port 1521
  anywhere in the diff; no deposit/insured/protected/guaranteed language; no `first_name`/`last_name`;
  no hard-coded time-zone offset; no US payment rails. The diff is 213 changed lines of Go comment
  in one file.
- **The three claimed citation corrections are real corrections**, checked against the pinned file
  rather than against T70's word: `:1226` is a comment line and `deepCopy` is at `:1224`; `:1250` is
  a closing brace and the `setFutureUnrecognizedInterest` write is at `:1246`; `:1207` is inside the
  `getFixedInterest()` guard and the residual assignment is `:1205` with `setEmi` at `:1210`. F-1 is
  a genuine finding and its three named artefacts still carry the drifted numbers.
- **F-3 confirmed in passing:** `emi.go:594` cites `ProgressiveEMICalculator.java:1253-1255` for
  `calculateOutstandingBalance`; at `426a23544` the method is `:1254-1256` [VERIFIED]. Out of T70's
  scope, correctly left alone, correctly filed. I also noticed `emi.go:648` cites `:249-262` where
  `getEffectiveRepaymentDueDate` is `:250-263`, and `emi.go:728` cites `:729-752` where the method is
  `:730-751` — two more instances of the same one-off drift, both pre-existing and out of scope. F-3's
  proposed one-pass sweep of every `:N` in `emi.go`/`generator.go` is warranted; **on the evidence of
  R-2 it should cover the block T70 just wrote, not only the older text.**
- **F-4 confirmed as stated:** the oracle allocates the smoothing trial copy once, outside the loop
  [VERIFIED: `:1274-1276`, `if (newScheduleModel == null)`], where the port allocates inside
  (`emi.go:1324` on the branch). Inert today; still open; unchanged by T70.
- **What I did not do.** I did not re-run T66's 21,060-shape census. I did not re-run the pass-3h
  capture against a live oracle (I re-derived every claimed figure from the committed
  `capture-prod3h-raw.json` instead). I did not determine whether `emi_L` can be negative on an
  admitted shape, nor whether `futureUnrecognizedInterest` stays zero on the `:247` path — both are
  capture questions and settling either by reading is the failure mode this task family exists to
  prevent. I did not review the neighbouring bullets of the same doc comment (the annuity fold, the
  smoothing loop, the final-period residual, T69's `(a)/(b)/(c)` memo rules); they are byte-identical
  to `main` and outside this diff.

---

### Follow-ups this review adds

- **F-T71-1 (P1, `coder`).** Fourth draft of the `futureUnrecognizedInterest` block per R-1: add the
  `allowFullTermForTranche = false` condition citing `contract.go:1179`/`:1191-1202`; fix (1)'s
  justification; move `:247` out of "post-origination" in (5); state that `P-04t` is graded and takes
  the `:247` entry while 18/18 observation cases ran flag-false.
- **F-T71-2 (P2, `coder`).** R-2: qualify `:259` as `RepaymentPeriod.java:259` in condition (4).
- **F-T71-3 (P3, `coder`).** R-3 and R-4: restore T66's "just before the assignment" qualifier in
  (d); reword (i)'s "entered … once" so it does not contradict (ii).
- **F-T71-4 (P2, `test_writer`).** Sharpen F-2's target: on the graded domain the `:1211-1212` guard
  reduces to `emi_L < 0` (`totalCreditedAmount` is zero by conditions (3) **and** (4) —
  `RepaymentPeriod.java:357-359`), and the port encodes the identical test at `emi.go:1207`. The
  capture question is therefore "can the residual drive `emi_L` strictly negative on an admitted
  shape", which is a one-integer detector.
- **F-T71-5 (P2, `test_writer`/`driver`).** The `:247` entry is graded but never observed. Either
  extend a pass-3h-style capture to a flag-true single-disbursement shape (`P-04t`'s inputs), or
  record explicitly that `P-04t` is carried by output identity with `P-04f` alone and that its
  `futureUnrecognizedInterest` has never been read.
