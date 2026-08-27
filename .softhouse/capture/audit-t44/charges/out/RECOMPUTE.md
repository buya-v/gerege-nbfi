# T44 audit leg (charges) - independent recomputation of T40's claims

Control: `out/control/B-01-baseline-raw.json`  sha256 `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009`

## Invariants C1-C10 (my own implementation, written from the stated definitions)

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

Totals: C1 PASS 21 / FAIL 0, C2 PASS 21 / FAIL 0, C3 PASS 21 / FAIL 0, C4 PASS 21 / FAIL 0, C5 PASS 6 / FAIL 15, C6 PASS 21 / FAIL 0, C7 PASS 21 / FAIL 0, C8 PASS 21 / FAIL 0, C9 PASS 21 / FAIL 0, C10 PASS 21 / FAIL 0

C5 FAILS on 15 captures: FC-02-flat-instalment, FC-04-pctinterest-instalment, FC-05-pctamountinterest-instalment, FC-06-penalty-inside-p3, FC-07-fee-on-p3-duedate, FC-08-penalty-instalment, FC-09-pctamount-instalment, FC-10-pctamount-inside-p6, FC-11-fee-on-disbursement-date, FC-12-fee-on-final-duedate, FC-13-fee-inside-p12, FC-14-fee-inside-p1, FC-15-combined-fee-and-penalty, FC-16-fee-on-p1-duedate, FC-22-penalty-instalment-plus-sdd-on-p3-duedate

## Leaf movement vs the zero-charge control (independent flatten)

| capture | leaves in doc | leaves in control | moved | structural diff |
|---|---|---|---|---|
| FC-01-flat-disbursement | 336 | 336 | **9** | 0 |
| FC-02-flat-instalment | 336 | 336 | **80** | 0 |
| FC-03-pctamount-disbursement | 336 | 336 | **9** | 0 |
| FC-04-pctinterest-instalment | 336 | 336 | **80** | 0 |
| FC-05-pctamountinterest-instalment | 336 | 336 | **80** | 0 |
| FC-06-penalty-inside-p3 | 336 | 336 | **8** | 0 |
| FC-07-fee-on-p3-duedate | 336 | 336 | **8** | 0 |
| FC-08-penalty-instalment | 336 | 336 | **80** | 0 |
| FC-09-pctamount-instalment | 336 | 336 | **80** | 0 |
| FC-10-pctamount-inside-p6 | 336 | 336 | **8** | 0 |
| FC-11-fee-on-disbursement-date | 336 | 336 | **8** | 0 |
| FC-12-fee-on-final-duedate | 336 | 336 | **7** | 0 |
| FC-13-fee-inside-p12 | 336 | 336 | **7** | 0 |
| FC-14-fee-inside-p1 | 336 | 336 | **8** | 0 |
| FC-15-combined-fee-and-penalty | 336 | 336 | **113** | 0 |
| FC-16-fee-on-p1-duedate | 336 | 336 | **8** | 0 |
| FC-17-fee-after-final-duedate | 336 | 336 | **0** | 0 |
| FC-19-pctinterest-sdd-inside-p6 | 336 | 336 | **9** | 0 |
| FC-20-pctinterest-sdd-on-disb | 336 | 336 | **0** | 0 |
| FC-21-pctamtint-sdd-inside-p6 | 336 | 336 | **9** | 0 |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | 336 | 336 | **80** | 0 |

## D-2a / D-2b - byte identity to the control, verified by my own sha256

| file | sha256 | == control |
|---|---|---|
| control B-01 (T40 control run) | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |
| FC-17 out/fc | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |
| FC-20 out/fc | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |
| FC-17 out/attested | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |
| FC-20 out/attested | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |
| CTRL-B-01 out/attested | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | YES |

## Determinism - three issues, my own digests

| capture | out/fc | out/fc-rerun | out/attested | all three identical |
|---|---|---|---|---|
| FC-01-flat-disbursement | `18bc7b0e30ed14d6` | `18bc7b0e30ed14d6` | `18bc7b0e30ed14d6` | yes |
| FC-02-flat-instalment | `eb121bcb048d9781` | `eb121bcb048d9781` | `eb121bcb048d9781` | yes |
| FC-03-pctamount-disbursement | `04c3c58545ca0c45` | `04c3c58545ca0c45` | `04c3c58545ca0c45` | yes |
| FC-04-pctinterest-instalment | `4b350ecf532bf892` | `4b350ecf532bf892` | `4b350ecf532bf892` | yes |
| FC-05-pctamountinterest-instalment | `2f2a242fa80ca563` | `2f2a242fa80ca563` | `2f2a242fa80ca563` | yes |
| FC-06-penalty-inside-p3 | `000f9f6bc6b73382` | `000f9f6bc6b73382` | `000f9f6bc6b73382` | yes |
| FC-07-fee-on-p3-duedate | `dffaf0001a4f3b31` | `dffaf0001a4f3b31` | `dffaf0001a4f3b31` | yes |
| FC-08-penalty-instalment | `a08d24d7042263e4` | `a08d24d7042263e4` | `a08d24d7042263e4` | yes |
| FC-09-pctamount-instalment | `090fce5d47b04d79` | `090fce5d47b04d79` | `090fce5d47b04d79` | yes |
| FC-10-pctamount-inside-p6 | `71c23d4d1795c0e6` | `71c23d4d1795c0e6` | `71c23d4d1795c0e6` | yes |
| FC-11-fee-on-disbursement-date | `d157b0a21c893ec0` | `d157b0a21c893ec0` | `d157b0a21c893ec0` | yes |
| FC-12-fee-on-final-duedate | `fbb8d67050a6672a` | `fbb8d67050a6672a` | `fbb8d67050a6672a` | yes |
| FC-13-fee-inside-p12 | `fbb8d67050a6672a` | `fbb8d67050a6672a` | `fbb8d67050a6672a` | yes |
| FC-14-fee-inside-p1 | `d157b0a21c893ec0` | `d157b0a21c893ec0` | `d157b0a21c893ec0` | yes |
| FC-15-combined-fee-and-penalty | `6dfe679c85915dbf` | `6dfe679c85915dbf` | `6dfe679c85915dbf` | yes |
| FC-16-fee-on-p1-duedate | `d157b0a21c893ec0` | `d157b0a21c893ec0` | `d157b0a21c893ec0` | yes |
| FC-17-fee-after-final-duedate | `713a35601b8909f4` | `713a35601b8909f4` | `713a35601b8909f4` | yes |
| FC-19-pctinterest-sdd-inside-p6 | `a214f3ae361dd2f1` | `a214f3ae361dd2f1` | `a214f3ae361dd2f1` | yes |
| FC-20-pctinterest-sdd-on-disb | `713a35601b8909f4` | `713a35601b8909f4` | `713a35601b8909f4` | yes |
| FC-21-pctamtint-sdd-inside-p6 | `52eb83b1ce973075` | `52eb83b1ce973075` | `52eb83b1ce973075` | yes |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | `f7c4d6a88d1d9f33` | `f7c4d6a88d1d9f33` | `f7c4d6a88d1d9f33` | yes |

Determinism mismatches: none

## Q5 - percentage bases and rounding locus, recomputed exactly (integer minor units, HALF_UP)

control totalInterestCharged (minor) = 14498847 ; principal (minor) = 120000000

| recomputation | expected (minor) | observed (minor) | agrees |
|---|---|---|---|
| FC-03 pct-of-amount DISBURSEMENT = 1.2345% x whole principal | 1481400 | 1481400 | YES |
| FC-10 pct-of-amount SDD, all of it in period 6 | 1481400 | 1481400 | YES |
| FC-09 0.5% of THAT PERIOD's principalDue, all 12 periods | all match | all match | YES |
| FC-04 3.75% of THAT PERIOD's interestDue, all 12 periods | all match | sum=543706 | differ |
| FC-19 3.75% of WHOLE-TERM interest, ONE rounding | 543707 | 543707 | YES |
| rounding-locus: FC-04 sum-of-12 vs FC-19 single (must differ) | 543706 | 543707 | differ |
| FC-05 1.2345% of period principal+interest, all 12 periods | all match | sum=1660392 | differ |
| FC-21 1.2345% of principal + WHOLE-TERM interest | 1660388 | 1660388 | YES |
| rounding-locus: FC-05 sum-of-12 vs FC-21 single (must differ) | 1660392 | 1660388 | differ |

### Would any of these percentage roundings discriminate HALF_UP from HALF_EVEN?

exact half-unit ties found in the charge arithmetic of the whole capture set: **0** []

=> no charge amount in this set is a rounding tie, so NO capture in the set discriminates
   HALF_UP from HALF_EVEN *inside the charge arithmetic*. The tenant canary is a separate shape.

## Q3/Q4 - which period each charge landed in (recomputed from the raw rows)

| capture | disb-period fee | per-period fee (period:minor) | per-period penalty | totalFee | totalPenalty | TRE |
|---|---|---|---|---|---|---|
| FC-01-flat-disbursement | 1500000 | - | - | 1500000 | 0 | 135998847 |
| FC-02-flat-instalment | 0 | 1:250000;2:250000;3:250000;4:250000;5:250000;6:250000;7:250000;8:250000;9:250000;10:250000;11:250000;12:250000 | - | 3000000 | 0 | 134498847 |
| FC-03-pctamount-disbursement | 1481400 | - | - | 1481400 | 0 | 135980247 |
| FC-04-pctinterest-instalment | 0 | 1:81000;2:74892;3:68675;4:62346;5:55902;6:49343;7:42665;8:35868;9:28948;10:21903;11:14732;12:7432 | - | 543706 | 0 | 134498847 |
| FC-05-pctamountinterest-instalment | 0 | 1:138366;2:138366;3:138366;4:138366;5:138366;6:138366;7:138366;8:138366;9:138366;10:138366;11:138366;12:138366 | - | 1660392 | 0 | 134498847 |
| FC-06-penalty-inside-p3 | 0 | - | 3:750000 | 0 | 750000 | 134498847 |
| FC-07-fee-on-p3-duedate | 0 | 3:900000 | - | 900000 | 0 | 134498847 |
| FC-08-penalty-instalment | 0 | - | 1:120000;2:120000;3:120000;4:120000;5:120000;6:120000;7:120000;8:120000;9:120000;10:120000;11:120000;12:120000 | 0 | 1440000 | 134498847 |
| FC-09-pctamount-instalment | 0 | 1:45241;2:46056;3:46885;4:47728;5:48588;6:49462;7:50352;8:51259;9:52181;10:53121;11:54077;12:55050 | - | 600000 | 0 | 134498847 |
| FC-10-pctamount-inside-p6 | 0 | 6:1481400 | - | 1481400 | 0 | 134498847 |
| FC-11-fee-on-disbursement-date | 0 | 1:900000 | - | 900000 | 0 | 134498847 |
| FC-12-fee-on-final-duedate | 0 | 12:900000 | - | 900000 | 0 | 134498847 |
| FC-13-fee-inside-p12 | 0 | 12:900000 | - | 900000 | 0 | 134498847 |
| FC-14-fee-inside-p1 | 0 | 1:900000 | - | 900000 | 0 | 134498847 |
| FC-15-combined-fee-and-penalty | 1500000 | 1:250000;2:250000;3:250000;4:250000;5:250000;6:250000;7:250000;8:250000;9:250000;10:250000;11:250000;12:250000 | 1:120000;2:120000;3:870000;4:120000;5:120000;6:120000;7:120000;8:120000;9:120000;10:120000;11:120000;12:120000 | 4500000 | 2190000 | 135998847 |
| FC-16-fee-on-p1-duedate | 0 | 1:900000 | - | 900000 | 0 | 134498847 |
| FC-17-fee-after-final-duedate | 0 | - | - | 0 | 0 | 134498847 |
| FC-19-pctinterest-sdd-inside-p6 | 0 | 6:543707 | - | 543707 | 0 | 135042554 |
| FC-20-pctinterest-sdd-on-disb | 0 | - | - | 0 | 0 | 134498847 |
| FC-21-pctamtint-sdd-inside-p6 | 0 | 6:1660388 | - | 1660388 | 0 | 136159235 |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | 0 | - | 1:120000;2:120000;3:870000;4:120000;5:120000;6:120000;7:120000;8:120000;9:120000;10:120000;11:120000;12:120000 | 0 | 2190000 | 134498847 |

## D-1 - totalRepaymentExpected vs the rows and vs the control

control totalRepaymentExpected (minor) = 134498847

| capture | totalFee | totalPenalty | TRE | TRE - control | Sum rows | TRE - Sum rows |
|---|---|---|---|---|---|---|
| FC-01-flat-disbursement | 1500000 | 0 | 135998847 | +1500000 | 135998847 | +0 |
| FC-02-flat-instalment | 3000000 | 0 | 134498847 | +0 | 137498847 | -3000000 |
| FC-03-pctamount-disbursement | 1481400 | 0 | 135980247 | +1481400 | 135980247 | +0 |
| FC-04-pctinterest-instalment | 543706 | 0 | 134498847 | +0 | 135042553 | -543706 |
| FC-05-pctamountinterest-instalment | 1660392 | 0 | 134498847 | +0 | 136159239 | -1660392 |
| FC-06-penalty-inside-p3 | 0 | 750000 | 134498847 | +0 | 135248847 | -750000 |
| FC-07-fee-on-p3-duedate | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-08-penalty-instalment | 0 | 1440000 | 134498847 | +0 | 135938847 | -1440000 |
| FC-09-pctamount-instalment | 600000 | 0 | 134498847 | +0 | 135098847 | -600000 |
| FC-10-pctamount-inside-p6 | 1481400 | 0 | 134498847 | +0 | 135980247 | -1481400 |
| FC-11-fee-on-disbursement-date | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-12-fee-on-final-duedate | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-13-fee-inside-p12 | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-14-fee-inside-p1 | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-15-combined-fee-and-penalty | 4500000 | 2190000 | 135998847 | +1500000 | 141188847 | -5190000 |
| FC-16-fee-on-p1-duedate | 900000 | 0 | 134498847 | +0 | 135398847 | -900000 |
| FC-17-fee-after-final-duedate | 0 | 0 | 134498847 | +0 | 134498847 | +0 |
| FC-19-pctinterest-sdd-inside-p6 | 543707 | 0 | 135042554 | +543707 | 135042554 | +0 |
| FC-20-pctinterest-sdd-on-disb | 0 | 0 | 134498847 | +0 | 134498847 | +0 |
| FC-21-pctamtint-sdd-inside-p6 | 1660388 | 0 | 136159235 | +1660388 | 136159235 | +0 |
| FC-22-penalty-instalment-plus-sdd-on-p3-duedate | 0 | 2190000 | 134498847 | +0 | 136688847 | -2190000 |

## What this capture set cannot distinguish (blind-spot probe)

distinct (principal, total interest, term days, #instalments) tuples across all 21 captures: **1**
  ('120000000', '14498847', '365', 12)

distinct response digests across the 21 captures: **17**
  COLLISION `d157b0a21c893ec0...` : FC-11-fee-on-disbursement-date, FC-14-fee-inside-p1, FC-16-fee-on-p1-duedate
  COLLISION `fbb8d67050a6672a...` : FC-12-fee-on-final-duedate, FC-13-fee-inside-p12
  COLLISION `713a35601b8909f4...` : FC-17-fee-after-final-duedate, FC-20-pctinterest-sdd-on-disb

