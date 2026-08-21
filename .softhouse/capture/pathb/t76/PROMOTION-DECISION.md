# T76 — promotion decision for the Path B capture set B-01..B-04

**VERDICT: PROMOTE NOTHING.** Not one of the four is promotable to
`.softhouse/vectors/loanschedule/` today, and the reason is never a defect in the captures — they
are sound, thrice-reproduced, invariant-clean and now attested. The reason is that **each of them
sets an input the ratified contract either pins to a constant or excludes from the graded domain**,
so a parity vector carrying its numbers would assert an answer where the contract requires
`ErrNoDiscriminatingVector`.

Promoting one anyway would be the exact failure this program exists to prevent: a corpus that says
PASS while the port and the oracle disagree about which inputs are live.

## The four tests a parity vector must pass

Sources, read this fire, not quoted from a summary:

1. **seam status** — `capabilities.json → seams[path_b_server].status[cap]` must be `exercised`
   for every capability the case requires. (`.softhouse/vectors/README.md`, "Capability classes".)
2. **graded domain** — `capabilities.json → capabilities[cap].in_graded_domain` must be `true`,
   otherwise the contract mandates a refusal. Nothing hard-codes this; it is data.
3. **expressible in the frozen shape** — the request must be transcribable into `GenerateRequest`
   **truthfully**, and must not contradict the contract's *pinned oracle inputs*
   (`contract.go:1174-1187`).
4. **`graded_against` non-empty** — a parity vector that kills no named wrong implementation "is a
   capture, not a grader" (README).

## Case by case

| | test 1 seam | test 2 graded domain | test 3 expressible | test 4 kills something new |
|---|---|---|---|---|
| **B-01** baseline | ✅ `schedule.core` exercised | ⚠️ n/a — but see below | ❌ | ❌ |
| **B-02** multiplesOf 100 | ✅ `installment.rounding.multiple` **exercised** | ❌ `in_graded_domain: false` | ❌ | ✅ (it would) |
| **B-03** `FULL_LEAP_YEAR` | ✅ `daysinyear.custom.strategy` **exercised** | ❌ two capabilities false | ❌ | ❌ (T22: ≡ field unset) |
| **B-04** `FEB_29_PERIOD_ONLY` | ✅ same | ❌ two capabilities false | ❌ | ✅ (it would) |

### B-01 — sound, and it grades nothing the store does not already grade

* Its product is `daysInYearType = 1` and `daysInMonthType = 1`, i.e. **ACTUAL/ACTUAL**
  [VERIFIED: `req/product-1-baseline.json`]. A truthful transcription must therefore write
  `day_count: "ACTUAL_ACTUAL"`, which the graded-domain predicate `DayCount ==
  DayCountFixed30Over360` [VERIFIED: `contract.go:1128`] puts **outside** the graded domain — the
  contract requires a refusal, and `REFUSE-01` already carries that refusal. Writing
  `FIXED_30_360` instead to slip past the predicate would state a product setting the oracle did
  not have; the numbers would match and the provenance would be a lie.
* Its request sets `interestCalculationPeriodType = 1` (SAME_AS_REPAYMENT_PERIOD), while the
  contract **pins** `interestCalculationPeriodMethod` **unset** as one of its six oracle-input
  constants [VERIFIED: `contract.go:1186-1187`]. Whether SARP is behaviourally identical to unset
  is **[UNVERIFIED]** — I did not test it, and no capture in this set can.
* **It kills nothing new.** I re-checked, in exact integer minor units, that B-01's money is
  identical to the ALREADY PROMOTED Path A vector `P-MNT-1M2` in all 12 periods (principal,
  interest, row total) and in total interest / total repayment — `t76/out/crosscheck.txt`,
  12 of 12 rows `ok`, total interest 14,498,847 minor units both sides. T22 §6 claimed this; I did
  not take its word for it.

### B-02 — the one that would grade something, blocked by a **ratified** decision

`installment.rounding.multiple` is `exercised` on `path_b_server`, so test 1 passes and Path B is
the only seam where it ever can. But:

* `in_graded_domain: false`, and the contract says so in its own words: *"InstallmentRoundingMultipleMinor
  stays in this contract and is refused for Run 1 (DEC-1 section 4.7) precisely because the field
  is money-moving one call away"* [VERIFIED: `contract.go:114-118`], with the graded-domain
  predicate `InstallmentRoundingMultipleMinor == 0` [VERIFIED: `contract.go:1130`].
* It carries B-01's ACT/ACT + SARP product shape too, so test 3 fails for the same two reasons.

**What it would be worth, measured today** (`t76/out/crosscheck.txt`, exact minor units): the field
moves **12 of 12 periods**; the level installment goes 11,208,237 → **11,210,000** minor units
(+1,763 each on periods 1-11) and the final installment 11,208,240 → **11,186,622** (−21,618);
total repayment −2,225. A port that ignored the field would be caught by 1,763 minor units in
period 1. That is a good grader, and it is unavailable until a **ratified** DEC-1 section is
amended — which CLAUDE.md reserves to a gate.

### B-03 / B-04 — outside the contract's input domain, not merely ungraded

The contract does not have a field for this input **and pins it to null**:

> `daysInYearCustomStrategy = null` … "*is PROVABLY inert within the graded domain, twice over* …
> It is NOT inert in general — through a running server, at a daily interest calculation with an
> actual/actual year, FEB_29_PERIOD_ONLY moves all twelve periods of a one-year schedule — **so it
> becomes a contract question the moment DayCountActualActual enters the graded domain, and not
> before.**" [VERIFIED: `contract.go:1183`, `:1246-1264`]

So promotion here is not a capability flag flip: it needs the frozen `GenerateRequest` to grow a
component, which CLAUDE.md makes a **hard `user` gate** ("A change to the contract is a `user`
task"). Both captures also run DAILY + ACT/ACT, so `daycount.actual.actual` — `in_graded_domain:
false` — would have to enter the graded domain first, exactly as the contract sequences it.

Measured today for the record (`t76/out/crosscheck.txt`): B-03 → B-04 moves **12 of 12 periods**,
total interest 14,465,921 → 14,501,143 minor units, **+35,222**. And T22's finding stands that
`FULL_LEAP_YEAR` is behaviourally identical to the field being unset, so **B-04 alone** carries the
discriminating power; B-03 is a control.

## The gate this raises — proposed **G-7**

Not raised as three gates, because they are one decision with an order:

1. **(prerequisite, already open as G-4)** does `DayCountActualActual` enter the graded domain?
   Nothing in B-03/B-04 is promotable before it does, by the contract's own sequencing.
2. **DEC-1 §4.7** — lift the Run-1 refusal of `InstallmentRoundingMultipleMinor` and flip
   `installment.rounding.multiple.in_graded_domain`? DEC-1 is **ratified**, so an agent may not
   amend it. Cost of not doing it: the only vectored grader for a money-moving product field stays
   on the shelf. **This is the cheapest of the three and unblocks B-02 alone.**
3. **Frozen contract shape** — does `GenerateRequest` grow a days-in-year-custom-strategy
   component, un-pinning `contract.go:1183`? **Hard `user` gate.** Nothing else unblocks B-04.

Until then the honest state of the store is the one it already reports: `REFUSE-01` refuses ACT/ACT,
and B-01..B-04 sit in `.softhouse/capture/pathb/` as **attested, admissible, unpromoted** evidence.

---

## AMENDED by T149, 2026-08-21 — the `[UNVERIFIED]` is closed, and B-01..B-04 are still refused

**Nothing above is withdrawn.** T76's verdict on these four captures stands: B-01 kills nothing
new and its product is ACT/ACT, B-02 needs a ratified DEC-1 §4.7 amendment, B-03/B-04 need the
frozen contract to grow a component. All three routes remain gate work.

What changed is the **residual question** in T76's own B-01 paragraph:

> *Its request sets `interestCalculationPeriodType = 1` (SAME_AS_REPAYMENT_PERIOD), while the
> contract **pins** `interestCalculationPeriodMethod` **unset** … Whether SARP is behaviourally
> identical to unset is **[UNVERIFIED]** — I did not test it, and no capture in this set can.*

**It is now closed by measurement, on this shape only.** T76 could not test it because B-01's
product is ACTUAL/ACTUAL, so any comparison against a fixed-30/360 Path A vector confounds two
settings. T149 posted the same request to product **9** (`T22 probe p09-sarp-360-30`, SARP +
fixed 30/360), which controls the day count and leaves ICPM as the only difference:

| observation | result |
|---|---|
| `T149-CTRL-P9-1M2` (product 9, SARP + 30/360, MNT 1,200,000) vs the **committed `B-01` capture** (product 1, SARP + ACT/ACT) | **byte-identical**, sha256 `713a3560…` |
| the same capture vs the **promoted Path A vector `P-MNT-1M2`** (ICPM unset, 30/360) | 12 of 12 rows agree in principal, interest, outstanding balance and row total; total interest `14,498,847` minor units both sides |

Transcript: `.softhouse/capture/pathb/t149/redgreen/crosscheck-vs-patha.txt`; script:
`t149/crosscheck-vs-patha.py`.

So on **this** shape — monthly, single disbursement on the schedule start date, declining balance —
`interestCalculationPeriodMethod = SAME_AS_REPAYMENT_PERIOD` moves nothing, and the mechanism is
visible in source: its only reader on this path is `ProgressiveEMICalculator.addDisbursement`
(`:127-132`), which resolves `effectiveDueDate` to the from-date of the first repayment period whose
due date is after the disbursement — which **is** the disbursement date when the loan is disbursed
on the schedule start. It licenses **nothing** about a daily interest calculation, where the setting
is live, and it is not a general finding about the pin.

That closure is what let T149 promote `T149-PATHB-TIE` — a **different** capture, on a
**fixed-30/360** product, that kills a named counterfactual. It does not reopen B-01..B-04.
