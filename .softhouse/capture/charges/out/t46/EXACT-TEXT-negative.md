## Path B -- exact-text sidecars

| capture | bare JSON numbers | distinct literals | max scale | sidecar leaves | identity |
|---|---:|---:|---:|---:|---|
| (negative run: FC-01-flat-disbursement-raw.json leaf `currency` corrupted in memory) | | | | | |
| FC-01-flat-disbursement-raw.json | 319 | 61 | 2 | 336 | **LEAF SET DIFFERS** |
| FC-02-flat-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-03-pctamount-disbursement-raw.json | 319 | 61 | 6 | 336 | OK |
| FC-04-pctinterest-instalment-raw.json | 319 | 96 | 2 | 336 | OK |
| FC-05-pctamountinterest-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-06-penalty-inside-p3-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-07-fee-on-p3-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-08-penalty-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-09-pctamount-instalment-raw.json | 319 | 96 | 2 | 336 | OK |
| FC-10-pctamount-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-11-fee-on-disbursement-date-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-12-fee-on-final-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-13-fee-inside-p12-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-14-fee-inside-p1-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-15-combined-fee-and-penalty-raw.json | 319 | 80 | 2 | 336 | OK |
| FC-16-fee-on-p1-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-17-fee-after-final-duedate-raw.json | 319 | 59 | 2 | 336 | OK |
| FC-19-pctinterest-sdd-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-20-pctinterest-sdd-on-disb-raw.json | 319 | 59 | 2 | 336 | OK |
| FC-21-pctamtint-sdd-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate-raw.json | 319 | 77 | 2 | 336 | OK |
| T46-CH-01-defvsreq-pctinterest-raw.json | 319 | 96 | 2 | 336 | OK |
| T46-CH-02-defvsreq-flat-disb-raw.json | 319 | 60 | 2 | 336 | OK |
| T46-CH-03-tie-pctinterest-4725-raw.json | 319 | 96 | 2 | 336 | OK |
| T46-CH-04-tie-pctinterest-2025-raw.json | 319 | 96 | 2 | 336 | OK |
| T46-CH-05-defvsreq-pctamtint-raw.json | 319 | 75 | 2 | 336 | OK |
| T46-CH-06-defvsreq-pctamount-disb-raw.json | 319 | 61 | 3 | 336 | OK |
| T46-CH-07-defvsreq-penalty-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| B-01-baseline-raw.json | 319 | 59 | 2 | 336 | OK |
| B-02-multiplesof100-raw.json | 319 | 59 | 2 | 336 | OK |
| B-03-diycs-fullleapyear-raw.json | 324 | 59 | 2 | 341 | OK |
| B-04-diycs-feb29only-raw.json | 324 | 59 | 2 | 341 | OK |
| CTRL-B-01-raw.json | 319 | 59 | 2 | 336 | OK |
| FC-01-flat-disbursement-raw.json | 319 | 61 | 2 | 336 | OK |
| FC-02-flat-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-03-pctamount-disbursement-raw.json | 319 | 61 | 6 | 336 | OK |
| FC-04-pctinterest-instalment-raw.json | 319 | 96 | 2 | 336 | OK |
| FC-05-pctamountinterest-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-06-penalty-inside-p3-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-07-fee-on-p3-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-08-penalty-instalment-raw.json | 319 | 75 | 2 | 336 | OK |
| FC-09-pctamount-instalment-raw.json | 319 | 96 | 2 | 336 | OK |
| FC-10-pctamount-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-11-fee-on-disbursement-date-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-12-fee-on-final-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-13-fee-inside-p12-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-14-fee-inside-p1-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-15-combined-fee-and-penalty-raw.json | 319 | 80 | 2 | 336 | OK |
| FC-16-fee-on-p1-duedate-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-17-fee-after-final-duedate-raw.json | 319 | 59 | 2 | 336 | OK |
| FC-19-pctinterest-sdd-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-20-pctinterest-sdd-on-disb-raw.json | 319 | 59 | 2 | 336 | OK |
| FC-21-pctamtint-sdd-inside-p6-raw.json | 319 | 62 | 2 | 336 | OK |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate-raw.json | 319 | 77 | 2 | 336 | OK |
| XR-01-fee-before-disbursement-HTTP403.json | 0 | 0 | 0 | 10 | OK |
| attestation.json | 138 | 37 | 0 | 528 | OK |
| canary-halfcent-raw.json | 319 | 59 | 2 | 336 | OK |

Path B: 57 sidecars written; 17693 bare JSON number occurrences across 552 distinct literals in the raw captures.
Distinct literals whose TEXT a float round-trip would change (trailing zeros or redundant scale): 65

## Path A control -- must already be zero

| payload | bare JSON numbers outside metadata |
|---|---:|
| periodratio/t39-periodratio.json | 0 |
| periodratio/t46-periodratio-reemit.json | 0 |
| periodratio/t46-periodratio-arms.json | 0 |
| mathcontext/t42-mathcontext.json | 0 |
| mathcontext/t42-mathcontext2.json | 0 |

RESULT: 1 PROBLEM(S)
  ! FC-01-flat-disbursement-raw.json: sidecar leaf SET differs from the raw capture
