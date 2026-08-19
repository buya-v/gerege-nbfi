# T44 audit leg (charges) - live discrimination probes AP-1..AP-4

All four issued against the live pinned oracle, tenant `gerege`, POST /loans?command=calculateLoanSchedule (persists nothing).

## AP-1-sdd-pctinterest-inside-p1

charge 11 (PCT_OF_INTEREST, SPECIFIED_DUE_DATE) due 20 Jan 2026 - STRICTLY INSIDE period 1, separated path

sha256 `32c69475a19efa954ac324f80d44d873f8c9efaf87f3eb32e13dee7cf9042cbc`

| totalFee | totalPenalty | totalRepaymentExpected | landed in (period:fee minor) |
|---|---|---|---|
| 543707 | 0 | 135042554 | 1:543707 |

control totalRepaymentExpected = 134498847 ; control totalInterestCharged = 14498847

## AP-2-sdd-pctinterest-on-p1-duedate

charge 11 due 01 Feb 2026 = period 1 dueDate = period 2 fromDate, separated path

sha256 `32c69475a19efa954ac324f80d44d873f8c9efaf87f3eb32e13dee7cf9042cbc`

| totalFee | totalPenalty | totalRepaymentExpected | landed in (period:fee minor) |
|---|---|---|---|
| 543707 | 0 | 135042554 | 1:543707 |

control totalRepaymentExpected = 134498847 ; control totalInterestCharged = 14498847

## AP-3-sdd-pctinterest-on-p3-duedate

charge 11 due 01 Apr 2026 = period 3 dueDate = period 4 fromDate, separated path

sha256 `94ddeb09a8da4100be51fcd7dc72f1901609893d6612a04c988bd514a69dea98`

| totalFee | totalPenalty | totalRepaymentExpected | landed in (period:fee minor) |
|---|---|---|---|
| 543707 | 0 | 135042554 | 3:543707 |

control totalRepaymentExpected = 134498847 ; control totalInterestCharged = 14498847

## AP-4-b02-pctamtint-instalment

charge 5 (PCT_OF_AMOUNT_AND_INTEREST, INSTALMENT_FEE) on product 2 (installmentAmountInMultiplesOf=100), so EMI != principal+interest

sha256 `8063ad52e9049be62c05f5e15286f8c272b6939e50aa5e65caed08e75658ab2b`

| totalFee | totalPenalty | totalRepaymentExpected | landed in (period:fee minor) |
|---|---|---|---|
| 1660356 | 0 | 134496622 | 1:138387, 2:138387, 3:138387, 4:138387, 5:138387, 6:138387, 7:138387, 8:138387, 9:138387, 10:138387, 11:138387, 12:138099 |

control totalRepaymentExpected = 134496622 ; control totalInterestCharged = 14496622

## AP-4 - which base does PERCENT_OF_AMOUNT_AND_INTEREST INSTALMENT_FEE use?

| period | principalDue+interestDue | EMI (totalInstallmentAmountForPeriod) | 1.2345% of P+I | 1.2345% of EMI | observed fee | matches |
|---|---|---|---|---|---|---|
| 1 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 2 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 3 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 4 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 5 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 6 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 7 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 8 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 9 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 10 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 11 | 11210000 | 11210000 | 138387 | 138387 | 138387 | P+I/EMI |
| 12 | 11186622 | 11186622 | 138099 | 138099 | 138099 | P+I/EMI |

periods on which the two candidate bases give DIFFERENT answers: **0 of 12**

