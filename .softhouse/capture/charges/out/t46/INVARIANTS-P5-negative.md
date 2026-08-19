NEGATIVE RUN: FC-01-flat-disbursement period-1 interestDue perturbed by +0.01 IN MEMORY (nothing on disk is touched)

## INVARIANTS -- a failure here is a statement about the reference oracle

| set | capture | C1 | C2 | C3 | C4 | C6 | C7 | C8 | C9 | C10 |
|---|---|---|---|---|---|---|---|---|---|---|
| T40 fc | FC-01-flat-disbursement | PASS | PASS | **FAIL** | PASS | PASS | **FAIL** | **FAIL** | PASS | PASS |
| T40 fc | FC-02-flat-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-03-pctamount-disbursement | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-04-pctinterest-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-05-pctamountinterest-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-06-penalty-inside-p3 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-07-fee-on-p3-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-08-penalty-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-09-pctamount-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-10-pctamount-inside-p6 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-11-fee-on-disbursement-date | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-12-fee-on-final-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-13-fee-inside-p12 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-14-fee-inside-p1 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-15-combined-fee-and-penalty | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-16-fee-on-p1-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-17-fee-after-final-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-19-pctinterest-sdd-inside-p6 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-20-pctinterest-sdd-on-disb | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-21-pctamtint-sdd-inside-p6 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T40 fc | FC-22-penalty-instalment-plus-sdd-on-p3-duedate | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-01-defvsreq-pctinterest | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-02-defvsreq-flat-disb | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-03-tie-pctinterest-4725 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-04-tie-pctinterest-2025 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-05-defvsreq-pctamtint | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-06-defvsreq-pctamount-disb | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| T46 A-3/A-5 | T46-CH-07-defvsreq-penalty-instalment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

## PROBE P5 (was C5) -- NOT AN INVARIANT, NOT A CONFORMANCE ASSERTION

`totalRepaymentExpected - sum(totalDueForPeriod)`, signed, in integer MINOR UNITS.
A **correct** Go port discards `totalRepaymentExpected` per DEC-1 revision 8's ratified
decision C-1, so a non-zero delta here is the ORACLE's behaviour, never a port defect.

| set | capture | delta (minor units) | reads as |
|---|---|---:|---|
| T40 fc | FC-01-flat-disbursement | 0 | rows and total AGREE |
| T40 fc | FC-02-flat-instalment | -3000000 | total OMITS charge money present in the rows |
| T40 fc | FC-03-pctamount-disbursement | 0 | rows and total AGREE |
| T40 fc | FC-04-pctinterest-instalment | -543706 | total OMITS charge money present in the rows |
| T40 fc | FC-05-pctamountinterest-instalment | -1660392 | total OMITS charge money present in the rows |
| T40 fc | FC-06-penalty-inside-p3 | -750000 | total OMITS charge money present in the rows |
| T40 fc | FC-07-fee-on-p3-duedate | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-08-penalty-instalment | -1440000 | total OMITS charge money present in the rows |
| T40 fc | FC-09-pctamount-instalment | -600000 | total OMITS charge money present in the rows |
| T40 fc | FC-10-pctamount-inside-p6 | -1481400 | total OMITS charge money present in the rows |
| T40 fc | FC-11-fee-on-disbursement-date | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-12-fee-on-final-duedate | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-13-fee-inside-p12 | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-14-fee-inside-p1 | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-15-combined-fee-and-penalty | -5190000 | total OMITS charge money present in the rows |
| T40 fc | FC-16-fee-on-p1-duedate | -900000 | total OMITS charge money present in the rows |
| T40 fc | FC-17-fee-after-final-duedate | 0 | rows and total AGREE |
| T40 fc | FC-19-pctinterest-sdd-inside-p6 | 0 | rows and total AGREE |
| T40 fc | FC-20-pctinterest-sdd-on-disb | 0 | rows and total AGREE |
| T40 fc | FC-21-pctamtint-sdd-inside-p6 | 0 | rows and total AGREE |
| T40 fc | FC-22-penalty-instalment-plus-sdd-on-p3-duedate | -2190000 | total OMITS charge money present in the rows |
| T46 A-3/A-5 | T46-CH-01-defvsreq-pctinterest | -181236 | total OMITS charge money present in the rows |
| T46 A-3/A-5 | T46-CH-02-defvsreq-flat-disb | 0 | rows and total AGREE |
| T46 A-3/A-5 | T46-CH-03-tie-pctinterest-4725 | -3173 | total OMITS charge money present in the rows |
| T46 A-3/A-5 | T46-CH-04-tie-pctinterest-2025 | -1361 | total OMITS charge money present in the rows |
| T46 A-3/A-5 | T46-CH-05-defvsreq-pctamtint | -3362472 | total OMITS charge money present in the rows |
| T46 A-3/A-5 | T46-CH-06-defvsreq-pctamount-disb | 0 | rows and total AGREE |
| T46 A-3/A-5 | T46-CH-07-defvsreq-penalty-instalment | -399996 | total OMITS charge money present in the rows |

P5: 20 of 28 captures show a non-zero delta. That count is a MEASUREMENT, not a verdict.

INVARIANT failures: 3
SUITE FAILED
