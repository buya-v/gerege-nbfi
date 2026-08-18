# T29 — independent adversarial re-review of DEC-1 **revision 4**

| | |
|---|---|
| Task | T29 (attempt 2; attempt 1 killed mid-flight by an API 521, no verdict reached) |
| Artefacts reviewed | `docs/adr/DEC-1-schedule-generator-adapter.md` (revision 4, T28) and `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reference oracle | Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified: `git -C /home/user/fineract rev-parse HEAD`) |
| Live oracle | **NONE reachable** — no Docker, no PostgreSQL. **No new observation was taken, synthesised or implied.** |
| Evidence labelling | every finding is labelled **(a)** source re-derivation, **(b)** an already-committed prior observation, or **(c)** needs a fresh observation |

---

## 0. VERDICT

# ACCEPTED WITH REQUIRED CHANGES — **NOT ratifiable**

**Outstanding P0: 2.** Standing policy **P-2** is not satisfied; gate **G-1** must stay open.

| id | one line |
|---|---|
| **P0-T29-1** | `n` in the EMI re-adjust loop is specified as `NumberOfRepayments`; the oracle's `n` is `relatedRepaymentPeriods.size()`, and the two return **different money** on requests inside the graded domain — including the disbursement-window shape the Run-1 corpus already samples. |
| **P0-T29-2** | The **per-period interest computation is not specified anywhere in DEC-1**; the oracle's `balance × rateFactor ÷ lengthTillPeriodDueDate × length` and the textbook `balance × rateFactor` that DEC-1's prose actually describes diverge on 1.59 % of in-graded-domain shapes, and **all thirteen committed observations are consistent with both**. |

Also: **P1 ×2, P2 ×1** (§6). **No regression** of revision 3's P0-2 / P0-3 (§5). Build, vet, gofmt, tests: clean (§8).

This verdict is not a reflex. T28 did the work T26 asked for, and did it well: every step of §4.3.1 that I re-derived is correct as written, and every one of its ~20 `file:line` citations resolves exactly in the pinned checkout. The two P0s below are things **no previous review looked for**, because no previous review transcribed the document into a runnable model and ran it against the oracle's own arithmetic. That transcription is the experiment T28's own §4.3.1 "Provenance" paragraph proposes as the standard — *"the text alone, with nothing else supplied, determines the money"* — and revision 4 does not pass it.

---

## 1. The from-text transcription experiment

### 1.1 What was built

`.softhouse/reviews/t29-probe/t29_rederive.py` — a complete progressive-loan schedule generator in **exact integer minor units** (`Decimal` only for the two quantities DEC-1 explicitly calls *not money* — the per-period rate factor and the `fn` recurrence; **no `float` anywhere**). It was written from:

- ADR §2.1 (the recurrence, the interest-first / principal-balancing split, the final-period residual);
- ADR §4.1 + `contract.go`'s `Rounding` doc (the two rounding senses, the exact `1 + rateFactor`, the currency layer);
- ADR §4.2 + `Disbursement.Date` (the month-end step and re-anchor);
- ADR §4.3 (the residual `diff`, accumulated at currency scale);
- ADR §4.3.1 + `contract.go`'s `Period` doc (steps 1–8 of the re-adjust loop), transcribed **literally, without consulting the Java while transcribing**;
- ADR §4.9 / `DayCountFixed30Over360` (fixed 30/360, monthly).

It shares **no code** with `.softhouse/reviews/t26-probe/t26_rederive.py` or `.softhouse/reviews/t28-probe/t28_spec_check.py`. That independence mattered: T28's spec-check imports T26's surrounding machinery, so a defect in the *shared* machinery — or a defect in the *specification text* that T26's machinery silently papers over — could not surface there. Both of the P0s below live exactly in that blind spot. `.softhouse/capture/out/t21-probe-rederive.py` was **not** consulted (retracted, defective).

### 1.2 Result of the experiment

**The text alone does NOT determine the money.** Two independent implementers reading only DEC-1 revision 4 can produce different schedules, inside the graded domain, on ordinary Mongolian retail shapes.

Two separate reasons, graded P0 each (§2, §3). One of them — the value of `n` — is a **statement in the document that is false**; the other — the per-period interest arithmetic — is a **step the document never states at all**.

### 1.3 What the transcription *did* determine (the positive result)

Where the document is explicit, it is right. The source-faithful arm of the model reproduces **13 of 13** already-committed observations **digit-for-digit**, with no tolerance, in integer minor units — `.softhouse/reviews/t29-probe/t29_validate.py`, transcript in `t29-output.txt`. Evidence class **(b)** for the expectations, **(a)** for the model:

| shape | level / final / total interest | provenance of the expectation |
|---|---|---|
| 100 / 6 × 7.0 % | 17.01 / **17.00** / 2.05 | shipped fixture; ADR §4.3's `−0.01` residual |
| 1,014,632 / 6 × 7.0 % | **172,574.64** / **172,574.62** / **20,815.82** | `t23-probe2-output.txt` |
| 127,704 / 36 × 16.8 % | **4,540.30** / **4,540.06** / **35,746.56** | `t23-probe2-output.txt` |
| 135,623 / 6 × 7.0 % | 23,067.56 / 23,067.59 / 2,782.39 | `t23-probe2-output.txt` |
| 2,345,024 / 6 × 7.0 % | 398,855.60 / 398,855.63 / 48,109.63 | `t23-probe2-output.txt` |
| 167,299 / 6 × 21.6 % | 29,665.91 / 29,665.94 / 10,696.49 | `t23-probe2-output.txt` |
| 64,352 / 12 × 21.6 % | 6,010.61 / 6,010.55 / 7,775.26 | `t23-probe2-output.txt` |
| 1,000 / 18 × 18.5 % | 64.04 / 64.14 / 152.82 | `t23-probe2-output.txt` |
| 246,489 / 18 × 18.5 % | 15,786.24 / 15,786.14 / 37,663.22 | `t23-probe2-output.txt` |
| 16,838 / 36 × 16.8 % | 598.65 / 598.46 / 4,713.21 | `t23-probe2-output.txt` |
| 40,595 / 36 × 16.8 % | 1,443.28 / 1,443.47 / 11,363.27 | `t23-probe2-output.txt` |
| 1,200,000 / 6 × 21.6 % (Q0a) | 212,787.28 / 212,787.30 / 76,723.70 | `t23-probe-output.txt` |
| 1,200,000 / 6 × 21.6 %, **disbursement 2024-02-01** (Q0b) | 253,114.12 / 253,114.10 / 65,570.58 | `t23-probe-output.txt` |

The three triples the task named — `172,574.64 / 172,574.62 / 20,815.82`, `4,540.30 / 4,540.06 / 35,746.56`, `17.01 / 17.00 / 2.05` — are reproduced, **and reproduced only with the §4.3.1 loop body present** (with the loop removed the first becomes 172,574.63 and the second's total interest 35,746.69, exactly as §4.3 says). So revision 4's central P0-T26-1 fix is **substantively correct**: the loop's effect, as written, is the oracle's effect on the disbursement-on-schedule-start shapes the corpus covers.

The defects are at the two edges the text never nails down.

---

## 2. P0-T29-1 — `n` is specified as `NumberOfRepayments`, and it is not

**Class (a): source re-derivation, corroborated by committed observation (b). No new observation taken.**

### 2.1 The statement under review

ADR §4.3.1, line 280 — and `contract.go:1052-1054`, **verbatim**:

> `n` is the number of related repayment periods, **which inside the graded domain is `NumberOfRepayments`** [`ProgressiveLoanInterestScheduleModel.java:191-194`]

and ADR §4.3.1 step 6, line 325 / `contract.go:1099`:

> (`:1279-1286`: … inside the graded domain that is **ALL n periods**)

and ADR §9, clause (iv): "*making the divisor `n`*"; clause (iii): "`floor(n/2)`".

### 2.2 What the source says

`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` is reached from exactly one place, `:748-750`, and is handed `relatedRepaymentPeriods` computed at `:732`:

```java
:732  final List<RepaymentPeriod> relatedRepaymentPeriods =
          scheduleModel.getRelatedRepaymentPeriods(calculateFromRepaymentPeriodDueDate);
```

`EmiAdjustment` takes that list and defines `n` as its size:

```java
EmiAdjustment.java:54-56   private int numberOfRelatedPeriods() { return relatedRepaymentPeriods.size(); }
EmiAdjustment.java:32      double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
EmiAdjustment.java:39      return emiDifference.dividedBy(Math.max(1, numberOfRelatedPeriods() - uncountablePeriods));
```

`calculateFromRepaymentPeriodDueDate` is **never null** on this path. It is `getEffectiveRepaymentDueDate(scheduleModel, changedPeriod, disbursementDate)` [`:149-151` → `:250-263`], which always returns a `LocalDate`. Therefore:

```java
ProgressiveLoanInterestScheduleModel.java
:191   public List<RepaymentPeriod> getRelatedRepaymentPeriods(final LocalDate calculateFromRepaymentPeriodDueDate) {
:192       if (calculateFromRepaymentPeriodDueDate == null) {
:193           return repaymentPeriods;              // <-- the ONLY branch that returns all periods
:194       }
:195       return repaymentPeriods.stream()
:196           .filter(period -> !DateUtils.isBefore(period.getDueDate(), calculateFromRepaymentPeriodDueDate))
:197           .toList();
```

**The ADR's own citation, `:191-194`, is exactly the `null` branch — the one branch this path can never take.** The citation refutes the claim it supports.

The effective due date is derived like this [`:250-263`]: the disbursement's repayment period is found by `findRepaymentPeriodForBalanceChange` [`ProgressiveLoanInterestScheduleModel.java:238-245`] using `isInPeriod` [`LoanRepaymentScheduleProcessingWrapper.java:251-254`] — **`[from, due]` inclusive for the FIRST period, `(from, due]` for later ones**; and if the matched period's due date *equals* the disbursement date, the effective due date is pushed to the **next** period's due date. So:

| disbursement date | related periods | `n` |
|---|---|---|
| on `ScheduleStartDate` (inside period 1, not its due date) | all | `NumberOfRepayments` |
| **on period 1's due date** | 2 … N | **`NumberOfRepayments − 1`** |
| on period *j*'s due date | *j+1* … N | **`NumberOfRepayments − j`** |
| strictly inside period *j* (*j* > 1) | *j* … N | **`NumberOfRepayments − j + 1`** |

Every one of those rows is **inside the graded domain**, whose window predicate is `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment period's DueDate` (§3.1, `contract.go:653`).

### 2.3 It is not hypothetical — the corpus already samples it

Committed observation **(b)**, `.softhouse/reviews/t23-probe/t23-probe-output.txt` case **Q0b** (start 2024-01-01, disbursement 2024-02-01, MNT 1,200,000 / 6 × 21.6 %):

```
REPAYMENT #1 from=2024-01-01 due=2024-02-01 principal=0.00 interest=0.00 total=0.00
DISBURSEMENT             due=2024-02-01 principal=1200000.00
REPAYMENT #2 … #5  total=253114.12          REPAYMENT #6  total=253114.10
```

253,114.12 is the annuity over **five** periods, not six, and period 1 carries **no** installment — i.e. the level installment was computed over, and written to, the **related** list only. `contract.go:684` and ADR §5 both list this shape as sampled ("one schedule whose disbursement falls on a later repayment due date"). On this particular shape the guard does not fire under either reading (`|emiDifference| × 100 = 200` minor units; the threshold is 200 under `n=5` and 300 under `n=6`, and the test is strict `>`), so **the existing corpus cannot detect the error** — which is precisely the failure mode DEC-1 exists to prevent.

### 2.4 It moves money

Re-derivation **(a)**, `t29_sweep.py` experiment A, transcript `t29-output.txt`. 120,000 random in-graded-domain requests with the disbursement on period 1's or period 2's due date; **only the value of `n` is varied** (the rebuild semantics are identical in both arms, so nothing else can be responsible):

> **2,143 of 120,000 (1.79 %) return different money.**

Worked examples (re-derived, **not** observations — and deliberately offered as capture candidates, not as figures to be quoted as oracle output):

| shape (start 2024-01-01, single disbursement 2024-02-01) | source `n = 5` | text `n = 6` |
|---|---|---|
| MNT 10,548,069 / 6 × 16.8 % | level **2,199,038.75**, final **2,199,038.73** | level 2,199,038.74, final 2,199,038.77 |
| MNT 1,222,552 / 6 × 18.5 % | level **255,934.34**, final **255,934.32** | level 255,934.33, final 255,934.36 |
| MNT 13,549,647 / 6 × 21.6 % | level **2,858,005.77**, final **2,858,005.75** | level 2,858,005.76, final 2,858,005.79 |

The wider sweep also found shapes where **total interest** diverges by a minor unit, not only the per-period split.

### 2.5 Why this is P0 and not P1

It is the identical defect class T26 raised and T28 fixed, one level down. Revision 3 named the loop's trigger and not its effect; revision 4 names the effect but mis-defines the one quantity the effect is parameterised by. Both the guard threshold (`floor(n/2)`) and the adjustment divisor (`max(1, n − uncountablePeriods)`) read `n`, so a wrong `n` changes *whether* the loop fires and *by how much*. And the notion the correct definition depends on — "related repayment periods" — is **never defined anywhere in either artefact**, so even an implementer who distrusts the relative clause has nothing to implement.

The same root cause makes two further sentences wrong:

- step 6's "*inside the graded domain that is ALL n periods*" — `:1279-1286` overwrites only periods whose from-date and due-date are not before the **first related** period's, so on a later disbursement it is the related suffix, not all `N`. Q0b **(b)** shows period 1 keeping installment 0.00 through the whole computation.
- step 3's `uncountablePeriods := count(i : rows[i].totalPaid > original)` is counted over the **related** list [`:2027-2031`, argument at `:1785`], not over `rows`. Zero either way today, but the rule is written "so the rule stays true when payment history enters the contract" (consequence 1) — and as written it will not.

### 2.6 Required correction (both artefacts, stated identically)

1. **Define "related repayment periods" normatively**, once, and reference it from §4.3.1 and §9: *the repayment periods whose `DueDate` is not before the effective due date* [`ProgressiveLoanInterestScheduleModel.java:191-198`], where the effective due date is the due date of the repayment period containing the disbursement date — membership tested `[FromDate, DueDate]` for the first period and `(FromDate, DueDate]` for the rest [`:238-245`, `LoanRepaymentScheduleProcessingWrapper.java:251-254`] — **pushed to the next period's due date when the disbursement date equals that period's due date** [`ProgressiveEMICalculator.java:250-263`].
2. Replace "*which inside the graded domain is `NumberOfRepayments`*" with the true statement: **`n` equals `NumberOfRepayments` only when the disbursement falls strictly inside the first repayment period; otherwise it is smaller.** Delete the `:191-194` citation, which points at the unreachable `null` branch, and cite `:195-197`.
3. Restrict step 6's overwrite to the related periods, and correct the "ALL n periods" parenthetical.
4. State that the level installment itself is computed over, and written to, the related periods only [`:741` → `:1722-1741`], so period rows before the disbursement stay all-zero — the rule behind the already-observed Q0b row.
5. Say that `uncountablePeriods` is counted over the related list.
6. `contract.go:660-663`'s note ("`NumberOfRepayments == 1` … the loop cannot fire") should become "the loop cannot fire when **the related list has one element**", which is the reachable case (a disbursement on period `N−1`'s due date), not merely `NumberOfRepayments == 1`.

---

## 3. P0-T29-2 — the per-period interest computation is never specified

**Class (a): source re-derivation. The discriminating capture does not exist — class (c) for empirical confirmation.**

### 3.1 What the document says

Everything DEC-1 revision 4 says about how a period's interest is produced:

- ADR §2.1: "Per period, **interest is computed first and capped at the installment**; principal is the balancing non-negative remainder [`RepaymentPeriod.java:272-286`, `:345-350`]."
- `contract.go` `Period.PrincipalMinor`: the same sentence.
- `contract.go` `InterestMethodDecliningBalance`: "computes each period's interest **from the outstanding principal balance carried into that period**."
- `contract.go` `Rounding`: intermediates are rounded to `SignificantDigits` "after each multiplication and each division, **in the order the reference oracle performs them**"; a quantity becomes money when scaled to `MinorUnitDigits`.

There is **no formula**. The multiplication by the rate factor is never written down; where the currency rounding falls is never written down; and the order of operations is delegated to "the order the reference oracle performs them" — which is the one thing an implementer reading only DEC-1 cannot see. Contrast §4.1, which spells the **rate factor** out to four operations plus a `setScale`, and §4.3.1, which spells the **loop** out to eight steps. The split — the step that actually produces every number in the response — gets one clause.

### 3.2 What the source does

```java
InterestPeriod.java:145-158
    return baseAmount                                             // declining balance -> outstanding
        .multiply(getRateFactorTillPeriodDueDate(), getMc())      // (1)  at mc
        .divide(BigDecimal.valueOf(lengthTillPeriodDueDate), getMc())   // (2)  at mc
        .multiply(BigDecimal.valueOf(getLength()), getMc());      // (3)  at mc
```
summed at `RepaymentPeriod.java:252-257` through `Money.of(..., mc)` (currency scale, `Money.java:52`), capped at the installment at `:272-286`, principal balancing at `:345-350`, roll-forward clamped at `:389-403`.

Steps (2) and (3) **cancel algebraically** — inside the graded domain `lengthTillPeriodDueDate == getLength()` — but they do **not** cancel numerically: each is separately rounded to 19 significant digits. An implementer reading DEC-1 writes the textbook `interest = round_to_currency(balance × rateFactor)` and never performs them.

### 3.3 It moves money, and the corpus cannot see it

Re-derivation **(a)**, `t29_sweep.py` experiment C:

> **699 of 43,992 in-graded-domain shapes (1.59 %) return different money** between the oracle's arithmetic and the textbook reading.

And the discrimination test **(b)**: the textbook reading reproduces **all 13** committed observations, exactly as the oracle's does. The Run-1 corpus is blind to it.

Worked examples (re-derived, **not** observations — schedule start = disbursement date, ordinary single-disbursement loans, nothing exotic):

| shape | oracle arithmetic | textbook reading |
|---|---|---|
| MNT 13,202 / 6 × 16.8 %, start 2024-01-01 | final **2,309.38**, total interest **654.38** | final 2,309.39, total interest 654.39 |
| MNT 3,924,149 / 6 × 16.8 %, start 2024-01-31 | final **686,443.28**, total interest **194,510.78** | final 686,443.29, total interest 194,510.79 |
| MNT 1,814,727 / 6 × 21.6 %, start 2024-01-31 | final **321,792.34**, total interest **116,027.14** | final 321,792.35, total interest 116,027.15 |

### 3.4 Why this is P0

Judged by the standard **this document sets for itself**. §9 claims: *"The rounding policy is expressible without a Java `MathContext` in both of the senses the oracle uses it, so two implementations round identically **by specification rather than by coincidence**."* That claim is false for the per-period split. The divergence rate (1.59 %) is the same order as the one T26 graded P0 for the loop body, and the corpus's blindness is total rather than partial. `contract.go`'s own header says "**the doc comments in this file ARE the specification**"; a step that determines every response field and appears in no doc comment is not specified.

A defence is available and I considered it: `Rounding`'s doc says the order "is fixed by the algorithm, it is a conformance obligation, and it is proven by golden vectors." But it is *not* proven by these golden vectors — §3.3 shows all thirteen pass either way — and DEC-1's whole architecture (§3.1) is that anything the corpus cannot discriminate must be either specified normatively or refused. Here it is neither.

### 3.5 Required correction

State the per-period split normatively in ADR §4.3 (a subsection, in the shape §4.3.1 already uses) and on `Period.InterestMinor` / `Period.PrincipalMinor`, giving: the base amount (the outstanding balance carried into the period, `InterestPeriod.java:151`); the **three** `MathContext`-qualified operations in order — `× rateFactorTillPeriodDueDate`, `÷ lengthTillPeriodDueDate`, `× length` [`:154-157`] — with the note that they cancel algebraically and **not** numerically; the currency-scale rounding of the sum [`RepaymentPeriod.java:252-257`, `Money.java:52`]; the cap at the installment [`:272-286`]; the non-negative balancing principal [`:345-350`]; and the zero-clamped roll-forward [`:389-403`]. And add §8 backlog item **3b** — a vector that separates the round-trip (candidate in §7).

---

## 4. Per-item verification of revision 4's normative claims

Every claim the task named, checked against the pinned checkout. Class **(a)** throughout.

| claim | cited | verified |
|---|---|---|
| loop reachable on every ordinary generation | `:748-750`, gate `:732-735` | ✅ `if (onlyOnActualModelShouldApply) checkAndAdjustEmi…` at `:748-750`; `onlyOnActualModelShouldApply` = `isEmpty() ‖ INTEREST_RATE_CHANGE ‖ ADD_REPAYMENT_PERIODS ‖ isCopy()` at `:733-735` |
| the loop | `:1258-1308` | ✅ `do {` at `:1265`, `} while (adjustCounter <= 3);` at `:1308` |
| guard, three conjuncts | `EmiAdjustment.java:31-36` | ✅ `lowerHalf > 0.0 && !emiDifference.isZero() && |d|.multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalf))` |
| threshold **replaces**, not scales | `Money.java:220-222` → `:216-218` → ctor `:40-53`, `setScale` at `:52` | ✅ `copy(double)` → `copy(BigDecimal.valueOf(a))` → `new Money(currency, a, this.mc)`; the amount is replaced, then `setScale(decimalPlaces, mode)` — so `floor(n/2)` currency units flat, with **no** dependence on `InstallmentRoundingMultipleMinor` |
| magnitude and its rounding | `EmiAdjustment.java:38-40`, `Money.java:352-358` | ✅ `dividedBy(long)` short-circuits at 1 at `:353-355`; divides at `getMc()`, which is the **instance's own** `MathContext` (`Money.java:494-496`) and is the threaded one for every `Money` on this path — so §4.3.1 consequence 2's "divides at the threaded `MathContext`" is **correct** |
| `uncountablePeriods` | `:2027-2031` | ✅ `originalEmi.isLessThan(period.getTotalPaidAmount())`, i.e. `totalPaid > original`; identically 0 here. **Counted over the related list, not `rows`** — see §2.5 |
| `adjustedEmi` | `EmiAdjustment.java:42-44` | ✅ `originalEmi.plus(adjustment())` |
| installment-multiple pass is the identity | `:1270` → `:1761-1766` | ✅ `!= null && > 0 ? safeRoundingForEMI(...) : equalMonthlyInstallment` |
| break on equal | `:1271-1273` | ✅ |
| rebuild → residual | `:1274-1288` → `:1160-1219` | ✅ trial on a `deepCopy` at `:1274-1275`; `setEmi` on the date-predicated periods at `:1279-1286`; `calculateOutstandingBalance` `:1287`; `calculateLastUnpaidRepaymentPeriodEMI` `:1288`, defined at `:1160-1219` with `diff` at `:1202-1203`, applied `:1205`, stored `:1210` |
| adoption test, strict, discards | `:1289-1291`, `EmiAdjustment.java:46-48` | ✅ `if (!getEmiAdjustment(newModel…).hasLessEmiDifference(emiAdjustment)) break;` **before** the copy-back; `isLessThan`, so equality is not adoption |
| copy-back | `:1293-1306` | ✅ iterator over the new model's related periods, `setEmi`/`setOriginalEmi` back onto the live list, then `calculateOutstandingBalance` at `:1306` |
| three iterations, counter advances only on adoption | `:1262`, `:1307-1308` | ✅ at most three adopted moves |
| degenerate pair | `:1779` (`idx > 0`), `:1788` (`copy(0.0)`) | ✅ guard's second conjunct cannot pass. **But the reachable degenerate case is `|related| == 1`, not `NumberOfRepayments == 1`** — §2.6 item 6 |
| pair is `(n-2, n-1)` | `:1778-1785` | ✅ nothing is paid, so the scan returns the last adjacent pair — the same two rows under either reading of `n` |
| ACTUAL-arm correction (P1-T26-1) | `:1505-1507`, `:1526-1531`, `:1533-1539` | ✅ `partialPeriodCalculationNeeded = daysInYearType == ACTUAL && numberOfYearsDifferenceInPeriod > 0 && (…)`; an annual period always spans a year boundary, so `:1526-1531` returns and the `case ACTUAL` at `:1534-1535` is not evaluated — **given `daysInYearCustomStrategy = null`; see P1-T29-1** |
| `Money.java:220-222` is on the live path, `:134-148` are traps (P1-T26-2) | §8 item 7 | ✅ `copy(double)` builds the guard threshold at `EmiAdjustment.java:35` and the degenerate zero at `:1788`; the `double` arithmetic overloads are not reached |
| eighteen per-period divergences, not seventeen (P1-T26-3) | §4.1, §5, `contract.go` | ✅ corrected in all three places |
| graded-domain blocks identical (P2-T26-1) | ADR §3.1 / `contract.go:646-657` | ✅ twelve identical lines, `NumberOfRepayments` removed from both |
| tenant precision never read on a reached call site (P2-T26-2, ADR §4.1) | `Money.java:52`, `:103`, `:115`, `:160`, `:377` | ✅ argument holds: inside the graded domain `applyInstallmentAmountInMultiplesOf` is the identity, so the two-argument `Money.of` / `roundToMultiplesOf` sites are not reached; and `MoneyHelper.PRECISION` is the compile-time 19 [`:35`] anyway. **But `contract.go` still carries the old weak argument — P1-T29-2** |

### 4.1 Under-determination hunt — what came back clean

| step | verdict |
|---|---|
| rounding **direction** and **point** of the adjustment | determined — the closed form `sign(d)·(2|d|+d')//(2d')` is written out, and the currency layer is stated |
| tie-breaks | determined — `HALF_UP` only; `HALF_EVEN` explicitly refused and flagged as needing the tie rule restated |
| order of apply-and-recompute | determined — steps 6 → 7 → 8, with the residual re-applied inside the trial |
| what "adopt" means | determined — `rows = trial`; consequence 7 correctly says no port needs the copy machinery |
| iteration bound | determined — counter advances only on adoption, ≤ 3 |
| `break` means stop | determined — consequence 5 |
| guard conjuncts | determined — all three, in exact integers |
| degenerate case | determined **as written**, mis-parameterised by `n` (§2.5) |
| rate factor's `× actualDays ÷ calcDays` correction: performed or skipped? | **not a defect** — experiment B, 0 divergences in 22,740 in-graded-domain shapes at (19, HALF_UP). Recorded so the next reviewer need not re-ask |
| `n` | **P0-T29-1** |
| per-period interest arithmetic | **P0-T29-2** |

---

## 5. No-regression check on revision 3's P0-2 and P0-3

**PASS on all three counts.**

- **The deleted ordering clause has NOT returned.** Grepped for every phrasing — *"on or after the last"*, *"after every repayment row"*, *"sorts after every"*, *"third clause"*, *"after the last … due"* — across both artefacts. Four hits: ADR line 17 (revision history, describing the deletion), ADR line 408 and `contract.go:1258-1259` (the clause quoted **as deleted**, in the past tense, with the P0-2 attribution), and `contract.go:671` (the graded-domain refusal, which is the *replacement*, not the clause). Nowhere is it restated as a live rule.
- **The disbursement-window predicate is intact and identical in both artefacts**: `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment period's DueDate` (ADR §3.1 line 127, `contract.go:653`), with the semantic-not-static note and the `ErrNoDiscriminatingVector` refusal in both.
- **Error precedence is total and deterministic**: three sentinels, strictly ordered, "return the **first** applicable" (ADR §4.11, `contract.go:1344-1368`). Every refusal reason in the document maps to exactly one, and the wrapping (`ErrNoDiscriminatingVector` wraps `ErrUnsupportedConfiguration`) is consistent with collapsing to the stronger claim.
- **T28's new classification** — `NumberOfRepayments < 1` → `ErrInvalidRequest` — is stated in **both** artefacts (ADR §3.1 line 130, `contract.go:655-659` + the field doc at `:823-826`), is consistent with the precedence rule (rank 1 beats any graded-domain refusal), and is covered by `ErrInvalidRequest`'s own doc ("a non-positive amount or count"). ✅

Note in passing, since §2 touches it: the surviving sentence "`NumberOfRepayments == 1` is well formed and graded; the EMI re-adjust loop simply cannot fire on it" is **true**, but it names the wrong sufficient condition (§2.6 item 6). That is folded into P0-T29-1, not a separate finding.

---

## 6. Remaining findings

### P1-T29-1 — §4.4's reason for the `daysInYearCustomStrategy` pin is incomplete (T30's first fact, independently re-derived)

**Class (a).** §4.4 says: "*Its only effect is substituting a 365/366-day year for a period containing 29 February*". `FEB_29_PERIOD_ONLY` does a **second** thing: it is the third conjunct of `partialPeriodCalculationNeeded` —

```java
:1505  partialPeriodCalculationNeeded = daysInYearType == ACTUAL && numberOfYearsDifferenceInPeriod > 0
:1506      && (!DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY.equals(daysInYearCustomStrategy)
:1507          || isPeriodContainsFeb29(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate()));
```

— so under that strategy it **suppresses the cross-year partial-period arm** for any period containing no 29 February, sending the computation back through the `switch` at `:1533`. T30 is right, and I re-derived it rather than taking its word.

**Is it a P0 against revision 4? No — I disagree with promoting it that far.** The field is **pinned `null`** (§4.4 is normative and it is an obligation on both implementations), `DayCountActualActual` is refused outright (§4.9), and `FrequencyYears` is refused on **both** arms (§4.10) — so no statement in revision 4 becomes false about anything DEC-1 can be asked, and no money changes. But the §4.4 table's own charter is "*the reasons matter, because a future reader will use them to decide whether a pin can be relaxed*", and this reason is the one a future reader will rely on when `DayCountActualActual` enters the graded domain. It should be complete now.

**Correction.** State both effects in §4.4 and `contract.go`'s pinned-inputs list; and qualify §4.10 / `contract.go`'s `FrequencyYears` doc: the `case ACTUAL` arm at `:1534-1535` is unreachable for `FrequencyYears` **with `daysInYearCustomStrategy` pinned `null`** — under `FEB_29_PERIOD_ONLY` and a period without 29 February it is reachable again. Also correct §4.7's "*only under a daily interest calculation with an actual year*", which describes only the first effect.

### P1-T29-2 — `contract.go` still carries the weak argument the ADR now calls insufficient

**Class (a).** ADR §4.1 (revision 4, P2-T26-2) explicitly retires the calibration inference: *"That is not sufficient on its own … **The argument from source is sufficient.**"* But `contract.go:555-561` still says:

> The tenant PRECISION cannot be pinned the same way … Within the graded domain that is harmless, **and the evidence is direct**: the calibration capture ran with a threaded precision of 12 while the ambient tenant context was 19, and it reproduced the oracle's shipped conformance literal exactly, so no reached call site consulted the tenant-global PRECISION.

The two artefacts of one frozen contract now disagree about whether the same evidence is sufficient — and `contract.go`'s header says its doc comments *are* the specification. T26's P2-T26-2 was scoped to "§4.1 line 210", so T28 is not at fault for missing it; it is nonetheless a defect in revision 4 as it stands. **Correction:** replace `contract.go:557-561` with the source argument — inside the graded domain `applyInstallmentAmountInMultiplesOf` [`:1761-1766`] is the identity, so the tenant-global-precision call sites [`Money.java:103`, `:115`, `:160`, `:169`, `:377`] are not reached — and note that `MoneyHelper.PRECISION` [`:35`] is a compile-time 19 regardless.

### P2-T29-1 — §8 item 5 and §4.10's "largest un-re-derived hole" are stale (T30's second fact)

**Class (a) + (b).** §8 item 5 asks for "*an independent source re-derivation of the cross-year partial-period arm [`:1505-1507`, `:1526-1531`] — the largest un-re-derived hole in the evidence*", and §4.10 leans on that status to caveat Q3b. Task **T30** (merged to `main`) has done it: `calculatePeriodFractions` [`:1550-1568`] accumulates `Σ days(segment) / Year.length(year)`, segmented at the year boundary, and `rateFactorByRepaymentPartialPeriod` [`:1969-1980`] performs `repaymentEvery × cumulatedPeriodRatio` **with no `MathContext`** — deliberately exact, unlike every neighbouring operation. I read the source myself and confirm both. T30 reports captures `B-03`/`B-04` reproducing digit-for-digit (`.softhouse/handoff/T30-corpus-remainder.md`, `.softhouse/reviews/t30-probe/`).

Not a P0 or P1: nothing in revision 4 becomes false, and the effect is to make the document's evidence base **stronger** than it claims. **Correction:** re-word §8 item 5 (the *vectors* remain outstanding; the *re-derivation* is done) and drop §4.10's "largest un-re-derived hole" aside, citing T30 instead.

### Still open from earlier reviews, and correctly non-blocking

T23 P1-3 (a stated mechanism for **recording** a graded-domain widening — without it, "widening is not an amendment" is an unbounded licence) and T23 P1-4 (Path-B `interestCalculationPeriodMethod`). I re-affirm T26's judgement: neither blocks the freeze, and T23 P1-3 should be closed soon after ratification. Note that P0-T29-1 makes T23 P1-3 slightly more urgent: the graded domain's disbursement window is exactly the kind of quiet widening whose consequences nobody re-derived.

---

## 7. Anything that needs a FRESH ORACLE OBSERVATION

**No live oracle was reachable during this review, and none was contacted.** Every candidate below is a **re-derived shape to capture**, not an observation; the numbers this review prints for them are re-derivations and must never be promoted to the vector store.

| # | what it would settle | candidate shape (all at `(19, HALF_UP)`, MNT 2 dp, 30/360, monthly, declining balance, no down payment, no installment rounding) | status |
|---|---|---|
| 1 | a vector that **trips the EMI re-adjust guard** inside the graded domain (§8 item 3) | MNT 1,014,632 / 6 × 7.0 %, or MNT 127,704 / 36 × 16.8 % — both already *observed* by T23 and ready to promote | open, carried |
| 2 | a vector that **separates the adoption test** (§8 item 3a) | MNT 100,025 / 12 × 16.8 %, start 2024-01-01 (T26's re-derived candidate) | open, carried |
| 3 | **NEW** — separates `n = NumberOfRepayments` from `n = |related|` (P0-T29-1) | MNT 10,548,069 / 6 × 16.8 %, schedule start 2024-01-01, single disbursement **2024-02-01** | new |
| 4 | **NEW** — separates the per-period interest `÷ lengthTillPeriodDueDate × length` round-trip (P0-T29-2) | MNT 13,202 / 6 × 16.8 %, schedule start = disbursement 2024-01-01 | new |
| 5 | confirms the `FEB_29_PERIOD_ONLY` suppression behaviour when `DayCountActualActual` is admitted (P1-T29-1) | a one-year daily/ACT-ACT schedule with and without a 29 Feb period | deferred with `DayCountActualActual` |

Items 3 and 4 do **not** need to exist before ratification — see §9 — but they must exist before any `loanschedule` conformance PASS is claimed, on exactly the terms §8 item 3 already binds.

---

## 8. Non-negotiables, build, vet, gofmt, tests

| check | result |
|---|---|
| `go build ./...` | **clean** (exit 0) |
| `go vet ./...` | **clean** (exit 0) |
| `gofmt -l .` | **no files** |
| `go test ./...` | contract package has no test files; nothing fails |
| money as `int64` minor units | ✅ every `…Minor` field is `int64`; no decimal string, no float-backed decimal |
| `float32` / `float64` / `big.Float` in a money path | ✅ **none**. The only three occurrences in `nexus/` are inside prose that **prohibits** them (`contract.go:66`, `:1169-1170`) |
| my own probe scripts | ✅ `int` for money, `Decimal` only for the two quantities DEC-1 calls not-money; no `float` literal or cast anywhere |
| Oracle Database / MySQL / MariaDB tokens (`ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`) | ✅ **none** in the ADR, `nexus/`, or the probe directory |
| US payment rails / vendors (Stripe, Plaid, Lithic, Persona) | ✅ none |
| three-field Mongolian names | ✅ `first_name` / `last_name` appear only where they are **prohibited** (ADR line 373, `contract.go:86-87`) |
| hard-coded time-zone offsets | ✅ `"+08:00"` appears only in the sentence rejecting fixed offsets (`contract.go:761`); zones are IANA names |
| hard-coded payment threshold | ✅ `5,000,000` appears only as a **sampled principal** (ADR §5, `contract.go:684`) — not a rail threshold |
| insured / protected / guaranteed | ✅ named only in the "never to be added" list |
| terminology discipline ("reference oracle" vs "Oracle Database") | ✅ the ADR opens with the distinction and holds it throughout |

---

## 9. Should ratification wait on the guard / adoption-test vectors?

**No — I agree with T26 and with ADR §8 items 3 and 3a, and I would extend the binding rather than move it.**

Reasoning:

1. **Ratification freezes the shape and the normative text; vectors grade behaviour.** §3.1 makes growth of the graded domain explicitly *not* an amendment. Binding the freeze to a capture inverts the document's own architecture.
2. **No fire can take the capture today.** No Fineract instance, no Docker, no PostgreSQL. Making ratification wait on a capture that cannot be taken parks G-1 indefinitely, with no compensating safety, while the boundary the whole strangler plan hangs from stays unfrozen.
3. **The harm the vectors prevent is already prevented by the §8 item 3 binding** — no conformance PASS for `loanschedule`, and no cutover proposal, until at least one admissible vector trips the guard *and* one separates the adoption test. Cutover is a hard `user` gate regardless. A wrong port cannot reach production through a ratified-but-unvectored specification.
4. **The specification defects need no oracle.** Both P0s in this review were found and can be fixed by source re-derivation alone. That is the argument for fixing the text *now* and capturing *later*, not for delaying both.

**But extend the list.** §8 item 3's binding should be widened to four items, on identical terms, because both of my P0s are of exactly the class the corpus cannot currently see:

- **3** (existing) — a vector that trips the guard;
- **3a** (existing) — a vector that separates the adoption test;
- **3b** (new) — a vector that separates the per-period interest round-trip (§7 item 4);
- **3c** (new) — a vector in the **later-disbursement window** that trips the guard, separating `n = |related|` from `n = NumberOfRepayments` (§7 item 3).

Without 3c the graded domain contains a whole region — every disbursement after the first period's start — that the corpus samples for *ordering* and *term anchoring* but has never exercised for the *smoothing loop*. That is the same hole, in a different wall.

---

## 10. Artefacts

All under `.softhouse/reviews/t29-probe/`, **none run against a live oracle**:

| file | what it is |
|---|---|
| `t29_rederive.py` | the from-text transcription plus the source-faithful arm; exact integer minor units, no float; shares no code with the t26 or t28 probes |
| `t29_validate.py` | 13 already-committed observations, replayed against the source-faithful arm; expectations are **quoted**, never re-taken |
| `t29-output.txt` | transcript of both scripts |
| `t29_sweep.py` | experiments A (the `n` reading), B (the rate-factor day correction — clean), C (the interest round-trip) |

The attempt-1 WIP files `t29_from_text.py` and `t29_n_sweep.py` are **deleted**, so no unvalidated artefact is left in this directory looking authoritative.

---

## 11. Summary for the driver

- **VERDICT: ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable.** P-2 is not satisfied; G-1 stays open.
- **P0 outstanding: 2.** `n` is mis-defined as `NumberOfRepayments` (1.79 % of later-disbursement in-graded-domain shapes return different money, and the corpus already samples the shape class); and the per-period interest arithmetic is never specified (1.59 % divergence, invisible to all thirteen committed observations).
- **T28's work is sound as far as it goes.** Every step of §4.3.1 checks out against the pinned source, all its citations resolve, and the text reproduces the three named observation triples — but only where the disbursement opens the schedule and only once the interest formula is supplied from outside the document.
- **Revision 3's P0-2 and P0-3 are NOT regressed.** The deleted ordering clause has not returned in any phrasing; the disbursement window is intact; error precedence is total and deterministic; T28's `NumberOfRepayments < 1` classification is consistent and identically stated in both artefacts.
- **Neither fix needs an oracle.** Both are source re-derivation, supplied above with `file:line` and required wording. One more revision and one more independent review is a realistic estimate.
- **Do not wait on vectors to ratify** — but widen §8 item 3's conformance/cutover binding from two vectors to four.
