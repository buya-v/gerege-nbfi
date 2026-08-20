## G-8 — TWO phenomena at the rounding floor, under one gate id

- **id**: G-8
- **class**: ENGINEERING to measure; the *remedy* is a DEC-n amendment, which is a hard `user` gate
- **task**: T75 (found the shape, and stated the family-A mechanism first), T83 (measured family A),
  T84 (reproduced T83, measured family B, and rejected T83's write-up), T100 (rewrote this section
  and re-measured both discriminators)
- **context**: tier0-harness-schedule-poc / loan-schedule
- **state**: **OPEN** — blocks nothing today
- **raised_by**: local fire 20260820-170001, from T75's approval of T74
- **recorded_in**: `.softhouse/gates.md`

### Read this first: G-8 is TWO phenomena, and a remedy for one is not a remedy for the other

Everything below is scoped to the family it was measured on. A sentence about family A is not a
sentence about family B, and neither is a sentence about the graded domain as a whole — the domain
is graded **by sampling**, and rate, principal and `NumberOfRepayments` are unbounded in it
[VERIFIED by T100 at `nexus/internal/apps/loanschedule/contract/contract.go:1163-1170`: *"are graded
by sampling rather than by enumeration … No claim is made that any un-sampled value is safe"*].

| | **FAMILY A — stale derived column** | **FAMILY B — genuine non-amortization** |
|---|---|---|
| principal column sums to the disbursed amount | **yes** | **NO — it sums to 0.00** |
| `totalPrincipalAmount` | = the disbursement | **0.00** |
| non-zero principal rows | exactly **one**, the last, carrying the whole disbursement | **none** |
| last row's interest | `0.00` | `0.01` |
| balance column | constant at the disbursed amount | constant at the disbursed amount |
| `totalOutstandingAmount` | `0` | `0` — **so this field does not discriminate** |
| forcing the oracle's own balance `Memo` to recompute | balance goes to **`0.00`** | **does not move** |
| the Go port | **diverges**, on exactly one cell per case | **reproduces it cell for cell — no divergence at all** |
| `invariant_exemptions` as a remedy | **inert** — the failure is a cell diff | **decisive** — the failure is purely invariant |
| measured at | **11** of the 12 annual rates swept (all but 600.0 %), `3 ≤ n ≤ 600`, **312 cells** | **one** annual rate (600.0 %), `104 ≤ n ≤ 250`, **29 cells** |

Cells behind that table: **312 family-A** (198 T83 + 111 T84 + 3 T100) and **29 family-B** (22 T84 +
7 T100), each re-derived from the committed raw captures by T100's own classifier
[`.softhouse/capture/t100-g8-rescope/src/classify_two_families.py`, `out/column-shape-{t83,t84,t100}.json`].
Every row of that table holds on **every** cell of its family in those captures — no exceptions, no
mixed cases. The two families are disjoint and each is internally uniform on what was swept.

**What was found originally.** T75 registered a prediction, committed it, and only then ran a
calibrated probe against the pinned oracle image (its calibrations reproduced `T64-ZP-A`/`T64-ZP-B`
cell-for-cell with zero input diffs). Result: **MNT 0.01 / 6 × 21.6 % at `MinorUnitDigits = 2` —
inside the graded domain, no multiples-of input involved — makes the reference oracle emit a
schedule whose balance column never reaches zero, `0.01` on every row including the last, while the
Go port returns `0`.** That shape is **family A** [VERIFIED by T100: `T100-FAMA-R21p6-N6-B2`, its
principal column sums to 2 minor units against a 2-minor-unit disbursement].

**Why it matters.** On family A this is a live port-vs-oracle divergence on an **admitted** shape,
and it sets two of this project's own rules against each other:

- *"Fineract is the oracle and fallback. No ported Go context is correct until its golden vectors match."*
- *"property invariants … principal amortizes to zero."*

**On family B it is worse and it is different: there is no port-vs-oracle divergence to arbitrate,
because the port agrees with the oracle — both emit a schedule that never repays the loan.** A
declared-divergence mechanism would have to be able to say *"both are wrong"*, which the harness
cannot express today.

Today `conformance.sh` reports PASS with 42 parity vectors and 0 invariant violations — **only
because no vector covers either family.** That is precisely the blind spot the conformance gate
exists to eliminate, so a green bar is not evidence against this finding.

---

## FAMILY A — the outstanding-balance column is STALE with respect to the oracle's own final EMI adjustment

### Discriminator for family A

A cell is family A when **all** of these hold, and they were checked on every cell claimed below:

1. the last emitted row carries a non-zero outstanding `balance`;
2. the REPAYMENT rows' `principal` column still **sums exactly to the disbursed amount** — in every
   family-A cell measured so far by exactly one non-zero principal row, the last, carrying the whole
   disbursement;
3. forcing the oracle's own balance `Memo` to recompute drives that balance to **`0.00`**.

Test 3 is the decisive one: it is what separates A from B, and it is the discriminator the driver's
re-derivation named in advance (*"a memo-staleness defect predicts [order dependence] … a genuine
non-amortization predicts no order dependence at all"*,
`.softhouse/reviews/driver-rederivation-20260820-200002-G8.md`).

### What was measured, and over what domain

**T83's sweep — 330 cells, all family A** [T83, branch `softhouse/T83-nonamortizing-boundary`;
reproduced by T84 byte-identically, canonical sha256 `01b41d9c…3101b`, 332 cases; re-classified a
third time by T100 from the same raw capture: **198 fail / 132 clean / 0 family B**]. Domain swept:
annual rates **{7.0, 16.8, 21.6, 36.0}** × repayment counts **{2, 3, 4, 6, 12, 24, 36, 56}**,
principal swept contiguously in minor units from 1 past the boundary (1..27 minor), every cell
emitted whether clean or not. All strictly inside the graded domain (MNT dp 2, single disbursement
on the schedule start date 2024-01-01, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down
payment, both multiples-of inputs null, `(19, HALF_UP)`).

**T84's extension — 111 further family-A cells** at annual rates **{0.12, 1.2, 3.6, 7.0, 12.0, 16.8,
21.6, 36.0, 48.0, 96.0, 300.0}** and terms up to **n = 600**, principals 1..100 000 minor.

**T100's confirmation — 3 family-A cells** re-asked with **different tenant ids**, in a **scrambled
order**, from its own capture (`out/capture-t100-raw.json`, canonical sha256 `314c4d55…2bfba`, rig
calibrations reproducing the committed `T64-ZP-A`/`T64-ZP-B` cell-for-cell with 0 input diffs):
21.6 % / n=6 / MNT 0.02, 3.6 % / n=360 / MNT 1.09, 0.12 % / n=600 / MNT 2.91 — all three fail, all
three sum, all three predicted in advance.

### The boundary table — MEASURED BY T83, over T83's grid only

"Failing" = the emitted schedule's LAST row carries a non-zero outstanding balance, which is exactly
the cell `principal_amortizes_to_zero` reads. **This table describes 4 rates × 8 terms and nothing
else**; T84's and T100's cells at other rates and longer terms are reported after it, and they move
the largest failing principal by more than an order of magnitude.

| rate % | n | principals swept (minor) | cases | LARGEST FAILING | SMALLEST CLEAN | contiguous |
|---|---|---|---|---|---|---|
| 21.6 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 21.6 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 21.6 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 21.6 | 24 | 1..13 | 13 | **9** (MNT 0.09) | **10** (MNT 0.10) | yes |
| 21.6 | 36 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |
| 21.6 | 56 | 1..21 | 21 | **17** (MNT 0.17) | **18** (MNT 0.18) | yes |
| 7.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 7.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 7.0 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 7.0 | 24 | 1..15 | 15 | **11** (MNT 0.11) | **12** (MNT 0.12) | yes |
| 7.0 | 36 | 1..20 | 20 | **16** (MNT 0.16) | **17** (MNT 0.17) | yes |
| 7.0 | 56 | 1..27 | 27 | **23** (MNT 0.23) | **24** (MNT 0.24) | yes |
| 16.8 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 16.8 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 16.8 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 16.8 | 24 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 16.8 | 36 | 1..18 | 18 | **14** (MNT 0.14) | **15** (MNT 0.15) | yes |
| 16.8 | 56 | 1..23 | 23 | **19** (MNT 0.19) | **20** (MNT 0.20) | yes |
| 36.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 36.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 36.0 | 12 | 1..8 | 8 | **4** (MNT 0.04) | **5** (MNT 0.05) | yes |
| 36.0 | 24 | 1..12 | 12 | **8** (MNT 0.08) | **9** (MNT 0.09) | yes |
| 36.0 | 36 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 36.0 | 56 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |

**T75's report is CONFIRMED and is a strict subset of this.** MNT 0.01/6, 0.02/6, 0.01/12 and
0.01/56 at 21.6 % all fail; 0.03/6 and above are clean **at 21.6 % / n = 6**.

**21.6 % is not load-bearing for family A** — family A exists at all 12 rates swept, from 0.12 % to
300.0 %. Across T83's grid the rate moves *where* the boundary sits and moves it DOWN as the rate
rises; the region is **empty at n = 2** at all four rates T83 tested, and grows with the term.

### The port divergence, family A only — ONE CELL PER CASE

On family A the divergence against the Go port is **the FINAL row's outstanding principal and
nothing else**: **198 divergent cells over T83's 198 failing cases** [T83, `out/port-vs-oracle.json`;
T84 re-ran it and got an identical file; port control on `T64-ZP-A`/`T64-ZP-B` = 0 mismatch cells;
the port refused nothing], plus **111 further divergent cases** in T84's own family-A sweep. T100
re-measured one of them through the real grader: `T100-FAMA-R3p6-N360-B109` grades **2525 cells with
exactly one diff — `row 360 outstanding_principal_minor: expected 109 minor units, got 0`**
[`out/exemption-demo-t100.json`]. The port amortizes; the oracle's balance column does not.

### The mechanism — FIRST STATED BY T75, and it applies to family A

**Attribution: the `:400` / `:1180` / `:1210` chain is T75's**, stated in `T75-pathA-multiplesof-review.md`
§5 one fire before the driver's re-derivation restated it, and T75 additionally carries the
`isFullyPaid()` step. It is not the driver's finding and this record previously failed to say so.

Source, re-verified line by line by T100 at the pinned commit `426a23544`:

- `RepaymentPeriod.getOutstandingLoanBalance()` is a `Memo` whose body subtracts `getDuePrincipal()`
  (`RepaymentPeriod.java:398`) — a direct function of `emi` — while its dependency array at **`:400`**
  is `{paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}` and **omits `emi`**;
- the sibling `getDueInterest()` memo **does** declare `emi` (`:278` opening, `:283`), so the
  omission is asymmetric inside one class;
- `isFullyPaid()` is `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())`,
  i.e. `0 == 0` when every EMI quantizes to zero [T75];
- `calculateLastUnpaidRepaymentPeriodEMI` (`ProgressiveEMICalculator.java:1160`) then takes its
  fallback, whose last filter at **`:1180`** is `rp.getOutstandingLoanBalance().isGreaterThanZero()`
  — which **populates the memo on the target period** — and **`:1210`** raises that period's EMI in
  the **same method** through a plain setter that invalidates nothing;
- the only three readers of `getOutstandingLoanBalance()` in the calculator are `:617`, `:1180`
  and `:1629`.

**The driver's candidate site is REFUTED** [T83, re-verified by T84 and again by T100]:
`RepaymentPeriod.getInitialBalanceForEmiRecalculation()` (`:413-426`) reads `getPrevious()`'s
balance and therefore can never populate the LAST period's memo.

### The mechanism is also OBSERVED, not only read — family A only

`ProbeOrderDep.java` / `ProbeOrderDep2.java` force the oracle's own balance `Memo` to recompute by
moving a DECLARED dependency (`paidPrincipal`) and moving it back to the same value.

- T83, on 5 of 5 family-A shapes: balance as emitted non-zero, balance after forced recompute
  **`0.00`**; 4 of 4 clean controls unmoved; path identity true on all 9.
- T84 re-ran T83's probe and reproduced 5/5 and 4/4.
- **T100 re-ran T84's probe itself** [`out/orderdep-t84probe-rerun-by-t100.json`]: the family-A cell
  `OD2-FAM1-R3p6-N360-B109` moves **`1.09` → `0.00`**; three clean controls (including an ordinary
  MNT 1,200,000 loan) unmoved; path identity true on all 7; `paidPrincipal` restored on all 7.

So **family A is precisely: the reference oracle's outstanding-balance column is stale with respect
to its own final EMI adjustment, while its principal column and its own totals are right.** That
sentence is true **of family A** — it was written into this file by T83 as a description of **all**
of G-8, and in that unscoped form it is **false**; see family B.

---

## FAMILY B — the principal column itself never repays the loan

### Discriminator for family B

A cell is family B when the REPAYMENT rows' `principal` column **does not sum to the disbursed
amount**. On every family-B cell measured so far it sums to **0.00** against a **0.01** disbursement,
`totalPrincipalAmount` reads `0.00`, **no** row carries a non-zero principal, the last row carries
`interest 0.01`, and forcing the memo to recompute **does not move the balance**. This is exactly
the test the driver's re-derivation named in advance as fatal to the family-A reframing when applied
to all of G-8: *"If it ever fails to sum, the reframing above is **wrong** and G-8 is the broader
finding after all."* It failed.

### What was measured, and over what domain — a MUCH narrower domain than family A

**T84 measured 22 family-B cells; T100 measured 7 more.** Union of what has been observed:

- annual rate **600.0 % — and no other rate has ever produced a family-B cell.** T84 swept 300.0 %
  with B = 2 through n = 204 and 300.0 % with B = 1 at six terms up to n = 260: the 300 % failures
  are **family A** (their principal column sums) [VERIFIED by T100's re-classification of T84's raw
  capture: 6 family-A cells at 300.0 %, 0 family-B].
- principal **MNT 0.01 (1 minor unit)** — no other principal has produced a family-B cell.
- repayment counts **n ∈ {104…122} ∪ {150, 200, 250}**: T84 measured 104…121 contiguously plus 150
  and 200 (22 cells, of which n = 108 and n = 120 were measured twice, once in each of its two
  probes, agreeing); **T100 added n = 122 and n = 250, which are above the top of n T84 swept, and
  both are family B.** At **n = 103** the same shape is **clean** [T84; re-measured by T100].

**The Go port reproduces family B cell for cell — 0 divergent cells** [T84 over all 22; T100 through
the real grader on `T100-FAMB-R600p0-N108-B1`: **761 graded cells, 0 cell diffs**]. On family B there
is **no oracle/port divergence at all**; both compute a schedule that does not repay the loan.

**Family B is NOT order-dependent** [T84, 3 of 3; **re-run by T100**, 3 of 3 unmoved at n = 104, 108,
120 while the family-A control in the same run moved 1.09 → 0.00]. So the family-A mechanism above
does **not** explain family B, and no claim is made that it does.

### What is NOT known about family B

- **Its cause.** T84 measured *that* it is not order-dependent and *that* the principal column sums
  to zero; it did not locate the code path, and neither did T100. `[UNVERIFIED]`
- **Whether it exists at any other rate, at any other principal, or below n = 104.** Every family-B
  cell ever measured is 600.0 % / MNT 0.01 / n ≥ 104. `[UNVERIFIED]`
- **Whether it terminates.** n = 250 fails; nothing above n = 250 has been asked. `[UNVERIFIED]`
- **`MinorUnitDigits ≠ 2`, and Path B / REST.** Not measured, by anyone. `[UNVERIFIED]`

---

## Option (a), RESCOPED — reachable today on family B, needs a port change on family A

Option (a) is *"promote a parity vector for the region with an explicit invariant exemption."*
Whether that works **depends entirely on which family the vector covers**, because
`invariant_exemptions` has power over invariant statuses and none over cell diffs
(`CheckInvariants` runs first, and the `len(diffs) > 0` early return short-circuits the **outcome**,
not the computation — `grade.go:488-493`; T83's earlier citation of `:487-497` as if the diff check
ran first was imprecise, per T84).

**Both halves below were measured by T100 in a single run, with the REAL `conformance.Run` and the
REAL Go port, over a throw-away store under `/tmp`, on two cells transcribed from T100's own
capture. Nothing was written to `.softhouse/vectors`; the corpus count did not change**
[`out/exemption-demo-t100.json`; T84 measured the family-B half first, on its own capture, and T100's
run reproduces its numbers].

| | **family B** (600.0 % / MNT 0.01 / n = 108) | **family A** (3.6 % / MNT 1.09 / n = 360) |
|---|---|---|
| graded cells | 761 | 2525 |
| cell diffs | **0** | **1** — `row 360 outstanding_principal_minor: expected 109, got 0` |
| without any exemption | **FAIL**, `principal_portions_sum_to_disbursed` and `principal_amortizes_to_zero` **VIOLATED** | **FAIL** on the cell diff, all six invariants **HOLD** |
| with exemptions | **PASS**, parityPass 1, 0 violations, **zero port change** | **FAIL — unchanged.** The exemptions register as EXEMPT and the cell diff still decides |
| admissible | yes, both variants | yes, both variants |

So:

- **On family B, option (a) is reachable TODAY** — with the existing mechanism, **no port change**,
  and no DEC-n amendment. The failure there is purely invariant, because the port agrees with the
  oracle. This is the cheap option the gate's earlier text said did not exist; it exists, on the
  family T83 never sampled.
- **On family A, option (a) still requires a port change**, exactly as T83 concluded. Its full shape
  is: change the port to emit the oracle's stale balance, *and then* carry the exemptions, because
  at that point the port's own output would violate them. That is a port change no agent has made or
  proposes to make unilaterally.

T83's sentence *"Option (a) is NOT reachable with the existing mechanism alone"* is therefore **true
of family A and false of family B**, and it was recorded here unscoped.

**A caveat on reading those runs:** each variant's process exit code is non-zero for a reason that
has nothing to do with G-8 — a one-vector scratch store trips the corpus-level coverage fatals
(`monthend.reanchor` has no killing vector there; "no parity vector was graded" when the only vector
fails). The **case outcome** and the invariant statuses in the table are the measurement; the exit
code of a scratch store is not.

Prepared and **NOT promoted**, for both families:
`.softhouse/capture/t83-nonamortizing/proposed-vector-{no-exemption,with-exemption}.json` (T83,
family A at 21.6 % / MNT 0.01 / n = 6), `.softhouse/reviews/T84-evidence/proposed-vector-family2-{no-exemption,with-exemption}.json`
(T84, family B).

---

## The bound on the failing principal, RESTATED OVER THE DOMAIN ACTUALLY SWEPT

This file previously said *"Every principal in the region is far below one MNT (the largest anywhere
in the sweep is MNT 0.23)"*. That was true of **T83's grid** and false as a statement about the
graded domain. Restated, with the domain named each time:

- **Over T83's grid** (rates {7.0, 16.8, 21.6, 36.0} × n ∈ {2…56}, principals 1..27 minor): the
  largest failing principal is **MNT 0.23**, at 7.0 % / n = 56.
- **Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates from 0.12 % to
  600.0 %; n from 1 to 600): the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600
  — **11.6× the old bound** [T84 measured it; **T100 re-measured that exact shape independently and
  reproduced it**, and measured MNT 2.92 clean at the same shape].
- **MNT 1.09 fails at 3.6 % p.a. over n = 360 — an ordinary 30-year monthly term at an ordinary
  rate** [T84; **re-measured by T100**, `T100-FAMA-R3p6-N360-B109`, with MNT 1.10 clean beside it].
  This is not sub-MNT dust and must not be described as such. It is still an absurdly small *loan*,
  but the shape that produces it is not absurd.
- The region **grows as the term lengthens and as the rate falls**: at 0.12 % the largest failing
  principal runs 59, 118, 176, 234, 291 minor units at n = 120, 240, 360, 480, 600 — i.e. ≈ n/2
  minor units, which is what the closed form below predicts in the limit r → 0
  [T100's re-derivation, `out/largest-failing.json`; every one of those bracketed by a measured clean
  cell one minor unit above].

**What was NOT swept, and therefore what this bound does not cover.** Only `MinorUnitDigits = 2`,
only MNT, only DAYS_30/DAYS_360, only MONTHS/1, only a single disbursement on the schedule start
date, no down payment, no charges, both multiples-of inputs null, only `(19, HALF_UP)`. Only twelve
annual rates were ever asked — {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6, 36.0, 48.0, 96.0, 300.0,
600.0} — out of a continuum; nothing between 3.6 % and 7.0 %, nothing between 96 % and 300 %,
nothing above 600 %, nothing at or below 0 %. **No term above n = 600 has ever been asked**, and
since the largest failing principal grows with n, **the measurement establishes no upper bound on
the failing principal over the graded domain as a whole** — only over the grid swept. The
practical reading — that no commercially realistic Mongolian loan *amount* has been observed to fail
— holds **over that grid**, and is not a proof about the domain.

## The closed form — TESTED AND FALSIFIED outside the sampled grid

T83 registered *"fails iff `B_minor × a(r,n) < 0.5`"*, where `a(r,n) = r/(1−(1+r)^−n)` and
`r = annual/100/12`, and **labelled it a HYPOTHESIS CONSISTENT WITH the measurement rather than a
measured fact**. **That call was right, and T84's measurement vindicated it.** On T83's own grid it
held on all 32 shapes, 106 of 106 registered predictions, 0 refuted [`check-prediction.py`, exit 0,
re-run by T84 with the same result].

**It is false outside that grid.** T100 evaluated it in **exact rational arithmetic** over all 342
non-calibration cells of T84's two captures: **320 held, 22 refuted, 0 exact ties**
[`src/closed_form_check.py`, `out/closed-form-check.json`]. **Every one of the 22 refutations is a
family-B cell** — 600.0 % / B = 1 / n ≥ 104 — where the closed form predicts CLEAN (the exact gap
`B·a − ½` is positive: `+2.429e-19` at n = 104, falling to `+3.025e-36` at n = 200) and the oracle
**fails**. The gap there is below the ulp of ½ at 19 significant digits, which is consistent with
the EMI quantizing to zero in the oracle's own `(19, HALF_UP)` arithmetic — offered as an
explanation, not as a verified mechanism `[UNVERIFIED]`.

**A count correction:** T84's write-up records **18** refutations; T100's exact-rational evaluation
over the same 342 cells finds **22**. The four extra are T84's own probe-1 tie cells
`T84-TIE-R600p0-N{108,120,150,200}-B1`, which `T84-evidence/prediction.json` registers as
`predictedFails: false` and which measured FAIL. Either count supports the same conclusion; 22 is
the number T100 can show.

**So: the closed form is a good description of family A on the grid where it was fitted, and it is
not a law. It does not predict family B at all.** No claim is made for any un-sampled rate, term or
day-count.

## The three options, still undecided — (b) and (c) remain a hard `user` gate

- **(a)** promote a parity vector for the region with an explicit invariant exemption. **Reachable
  today on family B with zero port change; requires a port change on family A.** Scope any decision
  to one family; a vector for one says nothing about the other.
- **(b)** refuse the region from the graded domain as a documented contract-refusal vector. Cheap in
  code for family A over the grid swept — but the region is **not** fully bounded (see the bound
  above: no term beyond n = 600 has been asked, and family B has been seen at only one rate), and it
  is a **graded-domain amendment**.
- **(c)** treat it as an oracle defect and diverge deliberately, keeping the port's `0`. That is what
  the port does *today, ungraded, on family A only* — **on family B the port emits the same
  non-amortizing schedule the oracle does, so there is nothing to diverge from and (c) does not
  describe family B at all.**

**(b) and (c) both amend the graded domain, which is a change to a ratified DEC-n — a hard `user`
gate no agent may cross.** Buyan decides. T83, T84 and T100 each analysed them and **decided none
and recommend none**; T100 attaches only the measurement and the scoping.

**What unblocks it**: a `user` decision, now on **two** phenomena rather than one. **What it
blocks**: nothing today — no vector covers either family and the conformance run is exit 0 without
them. **What it leaves uncovered**: on T84's accounting, **331 measured divergent-or-invalid cells**
sit outside the corpus — 309 family-A port-vs-oracle divergences (198 T83 + 111 T84) plus **22
family-B cells where the PORT ITSELF emits a schedule that does not repay the loan and no vector
says so**. The last 22 are the worse half.

**Conformance is unmoved by this rewrite**: `bash .softhouse/conformance.sh` → **VERDICT PASS, exit
0, 42 parity vectors, 5576 graded cells, 0 invariant violations**. Nothing was promoted; `PIN.json`
and `capabilities.json` are untouched.

### Evidence

**Family A, committed on `softhouse/T83-nonamortizing-boundary`** — `.softhouse/capture/t83-nonamortizing/`:
`PREDICTION.md`, `predicted-boundary.json`, `src/CaptureT83.java`, `src/run-t83.sh`,
`src/classify-boundary.py`, `src/check-prediction.py`, `src/ProbeOrderDep.java`,
`src/run-orderdep.sh`, `src/t83port.go.txt`, `src/run-port.py`, `src/t83grade.go.txt`,
`src/run-exemption-demo.py`, and under `out/`: `capture-t83-raw.json`,
`capture-t83-attestation.json`, `capture-t83-oracle-log.txt`, `measured-boundary.json`,
`port-vs-oracle.json`, `orderdep.json`, `exemption-demo.json`.

**Family B, committed on `softhouse/T84-review-t83`** (and copied unmodified onto
`softhouse/T100-g8-two-families` so these citations resolve) — `.softhouse/reviews/T84-evidence/`:
`PREDICTION.md`, `prediction.json`, `prediction2.json`, `src/CaptureT84.java`,
`src/CaptureT84B.java`, `src/ProbeOrderDep2.java`, `src/run-t84.sh`, `src/run-orderdep2.sh`,
`src/exemption-demo.py`, `src/classify.py`, `src/eval-probe{1,2}.py`,
`proposed-vector-family2-{no-exemption,with-exemption}.json`, and under `out/`:
`capture-t84-raw.json{,.gz}`, `capture-t84b-raw.json{,.gz}`, `port-vs-oracle.json`,
`orderdep2.json`, `exemption-demo.json`. Review: `.softhouse/reviews/T84-review-t83.md`.

**The two-family split, committed on `softhouse/T100-g8-two-families`** —
`.softhouse/capture/t100-g8-rescope/`: `PREDICTION.md` (registered in an ancestor commit),
`prediction.json`, `src/gencases.py`, `src/build_harness.py`, `src/CaptureT100.java`,
`src/run-t100.sh`, `src/postcheck.py`, `src/classify_two_families.py`, `src/column_shape.py`,
`src/closed_form_check.py`, `src/largest_failing.py`, `src/swept_domain.py`,
`src/exemption_demo_t100.py`, and under `out/`: `capture-t100-raw.json`,
`t83-reclassified.json`, `t84-reclassified.json`, `t100-classified.json`,
`column-shape-{t83,t84,t100}.json`, `closed-form-check.json`, `largest-failing.json`,
`orderdep-t84probe-rerun-by-t100.json`, `exemption-demo-t100.json`.
