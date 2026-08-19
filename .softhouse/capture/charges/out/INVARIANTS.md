| capture | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 |
|---|---|---|---|---|---|---|---|---|---|---|
| FC-01-flat-disbursement | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-02-flat-instalment | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-03-pctamount-disbursement | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-04-pctinterest-instalment | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-05-pctamountinterest-instalment | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-06-penalty-inside-p3 | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-07-fee-on-p3-duedate | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-08-penalty-instalment | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-09-pctamount-instalment | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-10-pctamount-inside-p6 | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-11-fee-on-disbursement-date | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-12-fee-on-final-duedate | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-13-fee-inside-p12 | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-14-fee-inside-p1 | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-15-combined-fee-and-penalty | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-16-fee-on-p1-duedate | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| FC-17-fee-after-final-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-19-pctinterest-sdd-inside-p6 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-20-pctinterest-sdd-on-disb | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-21-pctamtint-sdd-inside-p6 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | PASS | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | PASS | PASS |

C5 is expected to fail wherever a per-period charge is excluded from
totalRepaymentExpected. Those failures are the finding, not a defect in this tool.

total assertion failures: 15
