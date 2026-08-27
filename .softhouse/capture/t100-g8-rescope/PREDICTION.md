# T100 — prediction, registered BEFORE the probe was built or run

Task T100 (rewrite of gate G-8's write-up), branch `softhouse/T100-g8-two-families`, run
`2026-08-17-run1-harness-schedule-poc`. This file and `prediction.json` are committed in a commit
that is an ancestor of every commit carrying `src/CaptureT100.java`, `src/run-t100.sh` or anything
under `out/`. If the commit graph does not show that, this prediction is worthless and the
measurement below should be read as unregistered.

## Why T100 measures anything at all

T100's job is a WRITE-UP, not a measurement: T83 measured family A, T84 measured family B, and both
measurements have been reproduced. But the G-8 section will now assert a **two-family split**, and
that split is the load-bearing new claim. I will not restate someone else's numbers as the basis of
a claim I am making. So I re-ask the oracle for a small set of cells chosen to be the DISCRIMINATOR
between the two families, plus two cells **outside** the domain either T83 or T84 swept, with
**different tenant ids** and in a **deliberately scrambled order**.

## What I predict, and what would refute me

15 cases. All inside DEC-1's graded domain (MNT, dp 2, single disbursement on the schedule start
date 2024-01-01, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, both multiples-of
inputs null, `(19, HALF_UP)`), plus the two rig calibrations `P-CAL-ZPA` / `P-CAL-ZPB` which must
reproduce the committed pass-3g `T64-ZP-A` / `T64-ZP-B` cell for cell or the run is refused.

`fails` = the LAST emitted row carries a non-zero outstanding `balance`.
`family` = **A** if the REPAYMENT rows' `principal` column still sums to the disbursed amount;
**B** if it does not.

| case | rate % | n | B (minor) | predicted `fails` | predicted family | basis |
|---|---|---|---|---|---|---|
| T100-FAMB-R600p0-N200-B1 | 600.0 | 200 | 1 | yes | B | T84 measured it |
| T100-FAMA-R3p6-N360-B110 | 3.6 | 360 | 110 | no | — | T84 measured it |
| T100-FAMB-R600p0-N104-B1 | 600.0 | 104 | 1 | yes | B | T84 measured it |
| T100-CTRL-R21p6-N12-B120000000 | 21.6 | 12 | 120000000 | no | — | ordinary MNT 1,200,000 loan |
| T100-FAMB-R600p0-N103-B1 | 600.0 | 103 | 1 | no | — | T84 measured it clean |
| T100-FAMA-R3p6-N360-B109 | 3.6 | 360 | 109 | yes | A | T84 measured it |
| T100-FAMB-R600p0-N121-B1 | 600.0 | 121 | 1 | yes | B | T84's top swept n |
| T100-FAMA-R21p6-N6-B2 | 21.6 | 6 | 2 | yes | A | T75/T83 measured it |
| T100-FAMB-R600p0-N150-B1 | 600.0 | 150 | 1 | yes | B | T84 measured it |
| T100-FAMA-R21p6-N6-B3 | 21.6 | 6 | 3 | no | — | T83 measured it clean |
| T100-FAMB-R600p0-N108-B1 | 600.0 | 108 | 1 | yes | B | T84 measured it |
| **T100-FAMB-R600p0-N122-B1** | 600.0 | 122 | 1 | **yes** | **B** | **EXTRAPOLATION — n above T84's swept top** |
| **T100-FAMB-R600p0-N250-B1** | 600.0 | 250 | 1 | **yes** | **B** | **EXTRAPOLATION — n above T84's swept top** |
| T100-FAMA-R0p12-N600-B291 | 0.12 | 600 | 291 | yes | A | T84 measured it |
| T100-FAMA-R0p12-N600-B292 | 0.12 | 600 | 292 | no | — | T84 measured it clean |

**The two rows in bold are the only genuinely open ones.** They are the cells that decide whether
family B is a bounded island at `104 ≤ n ≤ 121` plus two probes, or a half-line in `n`. If either
comes back CLEAN, then family B is NOT monotone in `n` and any sentence in `gates.md` of the form
"600.0 % / MNT 0.01 / n ≥ 104" is wrong as written and must be narrowed to the measured set.

**Two further ways this prediction can be refuted, and I will report either if it happens:**

1. any family-B cell coming back with its principal column summing to the disbursed 1 minor unit
   (that would make it family A and collapse the split T100 is writing up);
2. any family-A cell coming back with a principal column that does NOT sum (that would break the
   discriminator in the other direction).

I am NOT predicting the interest column, the totals, or any cell of any clean case beyond
`fails = no`; those are recorded as measured, not as predictions.

## What this probe is not

It promotes nothing. It writes no vector, opens no database connection, starts no Fineract server,
and touches no running container's state: the rig is the in-JVM Path A seam T83 and T84 both used,
launched as a throw-away `docker run --rm` from the pinned image. "The oracle" here is the Fineract
reference implementation, never Oracle Database.
