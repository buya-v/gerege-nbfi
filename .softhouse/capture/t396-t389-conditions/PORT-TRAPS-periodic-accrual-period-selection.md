# PORT TRAPS — periodic-accrual PERIOD SELECTION

**Author:** T396, discharging T389 condition 2 (finding **m-3**).
**Pinned source:** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`. **Every line
number in this file was opened and read by T396 at that sha.** None is inherited from prose — that
inheritance is the defect class this file exists to repair (P-86).
**No money is expressed as a float anywhere in this document, and none of these traps requires
one.** All three are *calendar-date* and *configuration* traps; the amounts they change are
`BigDecimal` under the ratified production `MathContext (19, HALF_UP)`, and a Go port must carry
them as integer minor units.

---

## READ THIS FIRST — WHO IT IS FOR

**Anyone who does either of these:**

1. **Promotes T388's accrual observations into golden vectors** (`.softhouse/capture/t388-accrual-capture/`,
   journal entries 76–95, loan transactions 29–31, `ledger.accrual.entry`). The vector must pin the
   *right* predicate, or it will grade a Go port green on a rule Fineract does not implement.
2. **Ports `LoanAccrualsProcessingService` to Go** — program context **A2 / GL-accounting**
   (`.softhouse/program.json`, `fineract_paths` includes
   `fineract-accounting/src/main/java/org/apache/fineract/accounting/accrual` and
   `fineract-provider/src/main/java/org/apache/fineract/accounting/accrual`; the period-selection
   code itself lives in
   `fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanAccrualsProcessingServiceImpl.java`).

## WHY THIS FILE EXISTS

T388 explained the observed *"periods 1–3 accrued, periods 4–6 did not"* with the JPQL
`FIND_LOANS_FOR_PERIODIC_ACCRUAL` and its clause `ls.fromDate < :tillDate`.

**The conclusion was right; the citation was not.** That JPQL is
`select l from Loan l … where … and (exists (select ls.id from LoanRepaymentScheduleInstallment ls
where ls.loan.id = l.id …))` — `LoanRepository.LOANS_FOR_ACCRUAL:109-116` +
`FIND_LOANS_FOR_PERIODIC_ACCRUAL:117-118`, bound at `findLoansForPeriodicAccrual:261-264`. It
selects **loans**, not periods, and it is an `EXISTS`: one qualifying installment admits the whole
loan. On T388's loan 8, installment 1 (`fromDate 2026-01-15`) admits it, and the query is then
finished — it renders no verdict on period 4 at all.

**The per-period cutoff is `LoanAccrualsProcessingServiceImpl.getInstallmentsToAccrue:466-475`.**
A Go port written from the JPQL alone gets the right answer on T388's one observation and the
wrong answer in the three cases below.

---

## THE CODE, AS PINNED

`LoanAccrualsProcessingServiceImpl.java:447-464` — `calculateAccrualAmounts`:

```java
final int firstInstallmentNumber = fetchFirstNormalInstallmentNumber(loan.getRepaymentScheduleInstallments());   // :453
final LocalDate interestCalculationTillDate = loan.isProgressiveSchedule()
        && loan.getLoanProductRelatedDetail().isInterestRecognitionOnDisbursementDate() ? tillDate.plusDays(1L) : tillDate;   // :454-455
final List<LoanRepaymentScheduleInstallment> installments = isFinal ? loan.getRepaymentScheduleInstallments()
        : getInstallmentsToAccrue(loan, interestCalculationTillDate, periodic, chargeOnDueDate);                  // :456-457
final AccrualPeriodsData accrualPeriods = AccrualPeriodsData.create(installments, firstInstallmentNumber, currency);  // :458
for (LoanRepaymentScheduleInstallment installment : installments) {                                              // :459
    addInterestAccrual(loan, interestCalculationTillDate, scheduleGenerator, installment, accrualPeriods);        // :460
    addChargeAccrual(loan, tillDate, chargeOnDueDate, installment, accrualPeriods);                               // :461
}
```

`LoanAccrualsProcessingServiceImpl.java:466-475` — `getInstallmentsToAccrue`:

```java
final LocalDate organisationStartDate = this.configurationDomainService.retrieveOrganisationStartDate();         // :469
final int firstInstallmentNumber = fetchFirstNormalInstallmentNumber(loan.getRepaymentScheduleInstallments());    // :470
return loan.getRepaymentScheduleInstallments(i -> !i.isDownPayment()                                             // :471
        && (!chargeOnDueDate || (periodic ? !isBeforePeriod(tillDate, i, i.getInstallmentNumber().equals(firstInstallmentNumber))
                : isFullPeriod(tillDate, i)))                                                                    // :472-473
        && !isAfterPeriod(organisationStartDate, i));                                                            // :474
```

`LoanRepaymentScheduleProcessingWrapper.java:260-263`:

```java
public static boolean isBeforePeriod(LocalDate targetDate, LoanRepaymentScheduleInstallment installment, boolean isFirstPeriod) {
    LocalDate fromDate = installment.getFromDate();
    return isFirstPeriod ? DateUtils.isBefore(targetDate, fromDate) : !DateUtils.isAfter(targetDate, fromDate);
}
```

`LoanRepaymentScheduleProcessingWrapper.java:236-239`:

```java
public static int fetchFirstNormalInstallmentNumber(List<LoanRepaymentScheduleInstallment> installments) {
    return installments.stream().sorted(Comparator.comparing(LoanRepaymentScheduleInstallment::getInstallmentNumber))
            .filter(repaymentPeriod -> !repaymentPeriod.isDownPayment()).findFirst().orElseThrow().getInstallmentNumber();
}
```

`LoanAccrualsProcessingServiceImpl.java:1184-1187`:

```java
private boolean isChargeOnDueDate() {
    final String chargeAccrualDateType = configurationDomainService.getAccrualDateConfigForCharge();
    return !ACCRUAL_ON_CHARGE_SUBMITTED_ON_DATE.equalsIgnoreCase(chargeAccrualDateType);   // ACCRUAL_ON_CHARGE_SUBMITTED_ON_DATE = "submitted-date", :104
}
```

Reached from the periodic entry point:
`addPeriodicAccruals(LocalDate):120-140` → `:131 addPeriodicAccruals(tillDate, loan)` →
`:145-153` → `:152 addAccruals(loan, tillDate, /*periodic*/ true, /*isFinal*/ false,
/*addJournal*/ true, chargeOnDueDate)` → `:328-…` → `calculateAccrualAmounts`.
So on this path **`periodic = true` and `isFinal = false`**: the ternary at `:472-473` always takes
the `isBeforePeriod` branch, and `:456` always takes `getInstallmentsToAccrue`.

---

## TRAP A — the FIRST installment compares `<=`, every other one compares `<`

**Where it hides.** `isBeforePeriod` takes a third argument, `isFirstPeriod`, and switches
comparison on it (`LoanRepaymentScheduleProcessingWrapper.java:262`). Negated by `:472`:

| installment | kept when | boundary case `tillDate == fromDate` |
|---|---|---|
| **first non-down-payment** | `!DateUtils.isBefore(tillDate, fromDate)` → **`tillDate >= fromDate`** | **KEPT** |
| every other | `DateUtils.isAfter(tillDate, fromDate)` → **`tillDate > fromDate`** | **DROPPED** |

`DateUtils.isBefore(LocalDate,LocalDate):296-298` and `isAfter(LocalDate,LocalDate):300-302` are
strict, with asymmetric null handling (`isBefore(null, second)` is `true` when `second != null`;
`isAfter(first, null)` is `true` when `first != null`) — a Go port using `time.Time` comparisons
must reproduce that, not `IsZero()`-guess it.

**And "first" is not "number 1."** `fetchFirstNormalInstallmentNumber:236-239` sorts by installment
number and returns the first **non-down-payment** one. On a product with a down-payment installment,
the inclusive branch belongs to installment **2**, and installment 1 is excluded outright by
`!i.isDownPayment()` at `:471`.

**Go consequence.** A port that writes one comparison for all installments —
`if tillDate.After(inst.FromDate)` — differs from Fineract on exactly one input class:
`tillDate == firstNonDownPaymentInstallment.FromDate`, i.e. accruing *to the first period's start
date*, typically the disbursement date. Fineract accrues installment 1; the naive port accrues
nothing and writes no journal entry at all. Note the loan-level JPQL carries the **same** special
case (`ls.installmentNumber = (select min(lsi.installmentNumber) … where … lsi.isDownPayment = false)
and ls.fromDate = :tillDate`, `LoanRepository.java:118`), so the loan **is** selected and then
produces an empty installment set — a silent no-op, not an error.

**T388's observation does not cover this.** `tillDate = 2026-04-15` vs installment 1 `fromDate
2026-01-15`: strictly after, so both branches agree. **The capture is blind to trap A**, which is
precisely why a vector promoted from it must add a boundary case.

**Vector to add:** same loan, `tillDate` = first installment `fromDate`. Expect **one** accrual
transaction, not zero.

---

## TRAP B — one config row switches the date test OFF, at BOTH levels

**Where it hides.** `:472` reads `(!chargeOnDueDate || (…date test…))`. When `chargeOnDueDate` is
`false` the `||` **short-circuits true** and the date test is never evaluated: every
non-down-payment installment that is not before the organisation start date is returned —
**including installments entirely in the future.**

`chargeOnDueDate = isChargeOnDueDate()` (`:1184-1187`) is `false` exactly when the global
configuration `charge-accrual-date` equals `"submitted-date"` (case-insensitive).

- Seed default is `due-date`:
  `db/changelog/tenant/parts/0107_add_configuration_charges_accrual_date.xml`,
  `<column name="string_value" value="due-date"/>`, `enabled` true, `is_trap_door` false —
  **switchable at runtime.**
- Code default is also `due-date` when the stored value is blank:
  `ConfigurationDomainServiceJpa.getAccrualDateConfigForCharge:519-529`.

**The same flag also removes the LOAN-level cutoff.** `addPeriodicAccruals:126-127` passes
`!isChargeOnDueDate()` as the `futureCharges` bind:

```java
List<Loan> loans = loanRepositoryWrapper.findLoansForPeriodicAccrual(AccountingRuleType.ACCRUAL_PERIODIC, tillDate,
        !isChargeOnDueDate());
```

and `FIND_LOANS_FOR_PERIODIC_ACCRUAL` (`LoanRepository.java:117-118`) begins
`and (:futureCharges = true or ls.fromDate < :tillDate or (…))`. With `futureCharges = true` the
loan-level date test collapses to `true` as well.

| `charge-accrual-date` | `chargeOnDueDate` | `:futureCharges` | loan-level date test | period-level date test |
|---|---|---|---|---|
| `due-date` (seed default) | `true` | `false` | **applied** | **applied** |
| `submitted-date` | `false` | `true` | **bypassed** | **bypassed** |

**Go consequence.** A port that hard-codes the date predicate is not merely "unconfigured" — it is
**wrong for a whole tenant configuration Fineract ships as switchable**, and wrong in the expensive
direction: it under-accrues, omitting every future installment Fineract would have accrued. The
config flag must be a first-class input to the Go period selector, not a TODO.

**T388's observation does not cover this either.** The capture ran on the seed default, so both
date tests were live. **The capture is blind to trap B.**

**Vector to add:** the same loan and `tillDate` with `charge-accrual-date = submitted-date`. Expect
**six** accrual transactions, not three. (Changing a global configuration row moves shared oracle
state — that capture needs its own state-move record, and note the loan-level and period-level
effects are not separable by this flag.)

---

## TRAP C — `tillDate + 1 day` for interest and selection, unshifted `tillDate` for charges

**Where it hides.** `:454-455`:

```java
final LocalDate interestCalculationTillDate = loan.isProgressiveSchedule()
        && loan.getLoanProductRelatedDetail().isInterestRecognitionOnDisbursementDate() ? tillDate.plusDays(1L) : tillDate;
```

and then **two different dates flow onward from the same loop**:

| consumer | date it receives | line |
|---|---|---|
| `getInstallmentsToAccrue` (which installments accrue) | `interestCalculationTillDate` — **shifted** | `:457` |
| `addInterestAccrual` (how much interest) | `interestCalculationTillDate` — **shifted** | `:460` |
| `addChargeAccrual` (fees and penalties) | `tillDate` — **unshifted** | `:461` |

The predicate is `loan.isProgressiveSchedule() && loan.getLoanProductRelatedDetail().isInterestRecognitionOnDisbursementDate()`
— `Loan.isProgressiveSchedule:1816`;
`ILoanConfigurationDetails.isInterestRecognitionOnDisbursementDate:68` (implementation
`LoanConfigurationDetails.java:201`), declared as a `LoanProduct` constructor parameter at
`LoanProduct.java:285`. The consumer that receives the *unshifted* date is
`addChargeAccrual(Loan, LocalDate tillDate, boolean chargeOnDueDate, …):577-578`.

**Go consequence, two distinct failures from one omission.**

1. **A different installment set at every period boundary.** Under trap A's strict branch, a
   non-first installment with `fromDate == tillDate` is dropped — but on these products the
   selector sees `tillDate + 1`, which *is* after `fromDate`, so it is **kept**. T388's own
   `tillDate = 2026-04-15` is exactly such a boundary: on a progressive product with interest
   recognition on the disbursement date, installment 4 would have accrued too and the observation
   would read *"periods 1–4"*. A port carrying a single `tillDate` reproduces T388's capture and
   diverges by a whole installment on that product family.
2. **A different interest amount, from a one-day-wider window**, with charges still computed on the
   narrower one. A port that shifts `tillDate` once, at the top, and uses it everywhere will get
   interest right and **charges wrong** — the mirror-image bug, and the harder one to see, because
   the totals still balance.

**T388's observation does not cover this.** Product 63 is not a progressive product with
`isInterestRecognitionOnDisbursementDate`, so the shift never fired. **The capture is blind to trap
C.**

**Vector to add:** the same schedule on a progressive product with
`isInterestRecognitionOnDisbursementDate = true`, `tillDate` on a period boundary. Grade the
installment **set**, the interest amount **and** the charge amount separately — a vector that
grades only the total sum cannot discriminate failure (2).

---

## WHAT A PROMOTION TASK MUST NOT DO

- **Do not pin `ls.fromDate < :tillDate` as the accrual rule.** It is neither the whole rule nor
  the right layer. Pin `getInstallmentsToAccrue` (`:466-475`) + `isBeforePeriod` (`:260-263`), and
  say which of `periodic` / `isFinal` / `chargeOnDueDate` the vector holds fixed.
- **Do not promote T388's three transactions as the accrual rule's coverage.** They are one point
  in the input space, and all three traps above are outside it. State that in the vector's own
  notes so a later reviewer does not read three green cells as a proven predicate.
- **Do not treat `tillDate` as a scalar.** Between `addPeriodicAccruals` and `addChargeAccrual` it
  is clamped (`:350-352`, `tillDate = lastDueDate` when after the last due date) and conditionally
  shifted (`:454-455`). At least three distinct dates are in flight in one call.

## HOW EACH LINE HERE WAS CHECKED

Every file was opened at `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` with
`cat -n` / `sed -n` and the quoted text copied from that output. Caller enumeration used
`grep -rn --include='*.java' … | grep -v '/build/'` with the result read, not assumed. Where a
search returned nothing this file says so rather than reporting an absence as a fact.

**Files read:** `LoanAccrualsProcessingServiceImpl.java`, `LoanAccrualsProcessingService.java`,
`LoanRepaymentScheduleProcessingWrapper.java`, `LoanRepository.java`, `DateUtils.java`,
`ConfigurationDomainServiceJpa.java`, `0107_add_configuration_charges_accrual_date.xml`,
`ILoanConfigurationDetails.java`, `LoanProduct.java`, `AddPeriodicAccrualEntriesBusinessStep.java`.
