# T84 — independent review of T83 (gate G-8, the non-amortizing boundary)

Task **T84**, run `2026-08-17-run1-harness-schedule-poc`, fire `20260820-200002`, branch
`softhouse/T84-review-t83`. Reviewing **`softhouse/T83-nonamortizing-boundary`**, tip `db1f34b`,
7 commits, base `8da4b83`.

> **Note on the branch ref.** `refs/heads/softhouse/T83-nonamortizing-boundary` no longer exists in
> the shared ref db; the 7 commits do (`5695609 → 7a6b347 → ac1f38d → d10937d → 2d171f2 → e5af549 →
> db1f34b`, a linear chain off `8da4b83`). I recreated the ref locally at `db1f34b` and reviewed
> `git diff main...db1f34b`. `db1f34b` is **not** merged into `main`
> (`git merge-base --is-ancestor db1f34b main` → NO), notwithstanding `main`'s bookkeeping commit
> `2791bb4` "T83 done". [VERIFIED: `git show-ref`, `git log --graph --parents db1f34b`]

---

# VERDICT: **REJECTED**

Not for the measurement. **Every number T83 reported, I reproduced — most of them
byte-identically.** T83's rig is sound, its calibration is genuine, its boundary table is right, its
mechanism is real, and its prediction discipline is clean. I could not find a single arithmetic or
procedural defect in what it measured.

I am rejecting it for what it **wrote into `.softhouse/gates.md`** — the durable artefact Buyan will
read when he decides (a)/(b)/(c). T83 replaced G-8's open question with three **unscoped**
conclusions generalised from a 32-shape sample, and all three are false inside the graded domain. I
refuted each by measurement against the same pinned oracle, and one of them — the one this task
called "the single most consequential claim" — is refuted by running the **real** conformance
harness on a vector that **passes with an exemption and no port change at all**.

The driver's own re-derivation note set the test: *"Does the principal column sum to the disbursed
amount in **every** case in the failing region? **If it ever fails to sum, the reframing above is
wrong and G-8 is the broader finding after all.**"* [VERIFIED:
`.softhouse/reviews/driver-rederivation-20260820-200002-G8.md`, "What T83 and T84 are asked to do"].
It fails to sum on **22 measured graded-domain cells**. By the driver's own stated test, the
reframing is wrong and G-8 is the broader finding.

---

## 0. Environment, before and after

| | before | after |
|---|---|---|
| `fineract-fineract-1` | Up 2 days (**healthy**) | Up 2 days (**healthy**) |
| `fineract-db-1` | Up 3 days (**healthy**) | Up 3 days (**healthy**) |
| `https://localhost:8443/…/actuator/health` | `{"status":"UP",…}` | `{"status":"UP",…}` |
| `/Users/buv/fineract` HEAD | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | same |
| `/Users/buv/fineract` working tree | clean (0 lines porcelain) | clean |

[VERIFIED: `docker ps`, `curl`, `git -C /Users/buv/fineract`] Nothing was restarted, rebuilt, brought
down or re-seeded. No tenant was written. Every probe I ran used the **in-JVM Path A seam** — no
Fineract server, no database connection. PostgreSQL remains the only database in this program;
"oracle" throughout means the Fineract reference implementation, never Oracle Database.

---

# PART ONE — what T83 got right (all of it personally re-measured)

## 1.1 The capture reproduces **byte-identically**

I re-ran T83's recipe from its own committed sources, unmodified:

```
bash .softhouse/capture/t83-nonamortizing/src/run-t83.sh     # exit 0
capture OK: 332 cases, canonical sha256 01b41d9ca79e2625a3eb67041c247b5f05815fab72529c4fa7b4710c64e3101b
```

That digest is **character-for-character T83's reported `capturesCanonicalSha256`**, and a Python
comparison of the two `captures` arrays returns `True`. [VERIFIED: my run id `t83-20260820T123411Z`
vs T83's `t83-20260820T121525Z`] Preconditions all fired green: pinned image id
`sha256:e596339626bfca…0459a`, pinned commit `426a23544…`, clean tree, seam sha
`bf397f0b…a80714` against the literal, calibration reference `capture-prod3g-raw.json` at
`6e0c3701…7d91`, stderr empty, precision 19 / ordinal 4 flat on every case, graded-domain check on
every unvaried field.

## 1.2 The sweep is genuinely contiguous, complete, and correctly labelled

I did **not** use `classify-boundary.py`. I wrote my own classifier
(`.softhouse/reviews/T84-evidence/src/classify.py`) reading only the raw rows, in integer minor
units, with an added check T83's does not make: **that each capture's `id` agrees with its own
`inputs`** (rate, term, principal), so a mislabelled cell would abort rather than move a boundary.

| check | result |
|---|---|
| sweep cells emitted | **330** (+2 calibrations = 332) |
| FAIL / CLEAN / anomalies | **198 / 132 / 0** |
| shapes | **32** |
| sweeps with a missing principal (a silently skipped cell) | **0** |
| shapes where the failing set is NOT a contiguous prefix `{1…largest}` | **0** |
| cells where `id` disagrees with `inputs` | **0** |
| cells where the oracle's own disbursement row principal ≠ the requested B | **0** |

My `largestF` / `smallestC` columns are **identical to T83's boundary table on all 32 rows** —
including "none" at n = 2 at every rate, and MNT 0.23 (7.0 %, n = 56) as the largest failing
principal *in the sweep*. [VERIFIED: `/tmp/t84-classify.py` output, reproduced in
`.softhouse/reviews/T84-evidence/`]

**The sweep is not reported only by its positives.** Each shape is swept from 1 to between 4 and 5
minor units past its boundary, and every cell is present. I additionally probed principals **30, 50,
100, 1 000, 10 000 and 100 000** minor units on four of T83's shapes (`FAR`, 24 cells): **0 fail**.
The region does not reappear above the swept top. [VERIFIED: my probe 1]

## 1.3 The boundary is where T83 says it is, and it is not tenant- or order-dependent

The task asked me to construct the adjacent cases myself. I did — with a **different case list, a
different harness class, different tenant ids and reversed ordering** (`RP`, 12 cells): the
largest-failing and smallest-clean pair on six shapes, plus n = 2 and the n = 56 pair.

**All 12 reproduce T83's `observed` block cell-for-cell and classify identically.** [VERIFIED: my
probe 1, `T84-RP-*`] A rig whose answer moved with the tenant id would have voided the whole table;
it does not move.

## 1.4 The calibration is real, and it transfers

The concern the task raised is the right one, and the answer is favourable:

- the **reference** side is `.softhouse/capture/out/capture-prod3g-raw.json`, a **frozen committed
  artefact** produced by a *different* harness (`Capture3g.java`) in an earlier pass, pinned by
  literal sha256 in the runner — it is not regenerated by T83's code path;
- the **measured** side (`P-CAL-ZPA`/`ZPB`) goes through `prodDates(...)`, the **same constructor
  and the same emission path as every sweep cell** — which is exactly what makes it a calibration
  rather than a decoration [VERIFIED: `CaptureT83.java:152-157` vs `:184-197`];
- the comparison is the whole canonicalised `observed` block **and** the whole `inputs` block
  including `tenantId`, and the runner aborts the run on one cell of drift
  [VERIFIED: `run-t83.sh`, `CALIBRATIONS` block].

I went one further: **my own probe, with an entirely different case list, also reproduces
`T64-ZP-A`/`T64-ZP-B` cell-for-cell with 0 input diffs** — twice, on two independent runs. And the
Go port, an independent implementation, disagrees with those two shapes on **0 cells**. A defect
shared between `Capture3g.java` and `CaptureT83.java` and inherited by mechanical derivation is the
one residual risk the calibration cannot exclude; the port's agreement makes it remote. [VERIFIED:
my probe 1 & 2 preconditions; `port-vs-oracle.json` `calibrationMismatchCells: 0`]

## 1.5 The port comparison reproduces exactly

```
python3 .softhouse/capture/t83-nonamortizing/src/run-port.py
calibration mismatch cells (must be 0): 0
sweep cases: 330; with any cell mismatch: 198
cases where the ORACLE does not amortize but the PORT does: 198
every divergence confined to the outstanding-principal column: True
port refused: []
```

The regenerated `port-vs-oracle.json` is **identical to T83's committed one**. I also checked what
the summary does not state: **198 divergent cells over 198 cases — exactly one each — and every one
of them is on the final row.** [VERIFIED: my re-run + my own diff-shape check]

## 1.6 The mechanism is observed, and I confirm it a third time

`run-orderdep.sh` re-run: **5 of 5 failing shapes** go non-zero → `0.00` under a forced memo
recompute; **4 of 4 clean controls unchanged**; `paidPrincipal` restored and path identity true on
all 9. Same table as T83's, line for line. [VERIFIED: my run]

Source at pinned `426a23544`, opened by me:

| claim | verified |
|---|---|
| balance memo dependency array omits `emi` | **`RepaymentPeriod.java:400`** — `{ paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount }` ✅ |
| memoized body subtracts `getDuePrincipal()` | **`:398`** ✅ |
| `getDuePrincipal()` is a direct function of `emi` | **`:345-350`** via `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest()` ✅ |
| sibling `getDueInterest()` memo **does** declare `emi` | **`:272-283`** — `emi` is the 8th element at `:283` ✅ |
| pre-adjustment read | **`ProgressiveEMICalculator.java:1180`**, `.filter(rp -> rp.getOutstandingLoanBalance().isGreaterThanZero())` ✅ |
| the EMI raise, same method, after it | **`:1210`** `repaymentPeriod.setEmi(adjustedEmi);` ✅ |
| both inside `calculateLastUnpaidRepaymentPeriodEMI` | method opens at **`:1160`** ✅ |
| the only other readers in that class | **`:617`** (public query, off the generate path) and **`:1629`** (`firstRepaymentPeriod.getPrevious().map(rp -> … rp.getOutstandingLoanBalance())`, a *different* period) — `grep` returns exactly these three ✅ |
| **the driver's candidate site is REFUTED** | `getInitialBalanceForEmiRecalculation()` opens at **`:413`** and reads `getPrevious().get().getOutstandingLoanBalance()` at **`:416`**. The last period is no period's `previous`, so `:416` cannot populate the last period's memo. **T83's refutation is correct.** ✅ |

## 1.7 T83's exemption demo reproduces exactly

Both variants **FAIL identically** on `row 6 outstanding_principal_minor: expected 1 minor units,
got 0 (delta -1)`; without any exemption **all six invariants HOLD**; with it,
`principal_amortizes_to_zero` and `balance_roll_forward` read `EXEMPT` and the verdict is unchanged.
Harness citations all check out: `vector.go:684`/`:747`, `admit.go:235-241`,
`invariants.go:193-210`, `invariants.go:294-298`, `grade.go:489-493`. **On the shape T83 tested, its
claim is exactly right.** [VERIFIED: my re-run of `run-exemption-demo.py`]

## 1.8 Hygiene — all clean

| | |
|---|---|
| `git diff main...db1f34b -- .softhouse/vectors/` | **empty (0 lines)** ✅ nothing promoted |
| `git diff main...db1f34b -- nexus/ conformance/ '*.go'` | **empty** ✅ no port logic changed |
| `bash .softhouse/conformance.sh` | **PASS, exit 0, 42 parity vectors, 5576 cells, 0 invariant violations** ✅ unchanged |
| `gofmt -l ./nexus` | names **exactly** `nexus/internal/apps/loanschedule/contract/contract.go` ✅ expected under G-3; never `gofmt -w`'d |
| G-8 `state:` | **OPEN**, unchanged ✅ |
| (b) and (c) | analysed, **not decided**; the "hard `user` gate" sentence is preserved verbatim ✅ |
| prediction DAG | `5695609` (PREDICTION.md, `predicted-boundary.json`, `predict.py`) is a **strict ancestor** of all six evidence commits on a linear chain — checked by parent pointers, not timestamps ✅ |
| `check-prediction.py` | re-run: **106 held, 0 refuted, exit 0** ✅ |

T83's follow-up that **T75's probe source `CaptureF2.java` was never committed** is **correct**:
`git rev-list --all --objects | grep -i capturef2` returns nothing, and no T75 capture artefact
exists under `.softhouse/capture/`. `.softhouse/reviews/T75-pathA-multiplesof-review.md` §5's
reproducibility sentence is not currently true. [VERIFIED]

---

# PART TWO — the findings

My own probes: **249 cells** (canonical sha256 `3900a204…cbf17`) and **93 cells** (canonical sha256
`47611b04…23313`), both from a harness derived from `CaptureT83.java` with the case list replaced,
both passing T83's full precondition set including the two rig calibrations. My prediction was
committed as `e6d6a47`, **before** either probe was built or run, and both evidence commits are its
children.

**Domain check first, because everything below depends on it.** DEC-1 §3.1 and `contract.go`'s
graded-domain block list eleven predicates plus one semantic one, and **none of them bounds the
annual rate or `NumberOfRepayments`**. DEC-1 §3.1 says so in terms: *"Rates, principals, terms and
dates are continuous or unbounded; a corpus cannot enumerate them, so they are graded by
**sampling**."* [VERIFIED: `docs/adr/DEC-1-schedule-generator-adapter.md` §3.1;
`contract.go:1112-1131`] Consistently, the Go port answered **all 344** of my cells with **zero**
`ErrNoDiscriminatingVector` refusals, and the conformance harness **admitted** my proposed vector and
graded **761 cells** of it. Every cell below is inside the graded domain as this program defines and
enforces it.

---

## **P0-1 — G-8's rewritten definition is refuted. There is a second family, and in it the principal column genuinely does not amortize.**

`.softhouse/gates.md`, as T83 rewrote it, now states without qualification:

> *"So G-8 is precisely: **the reference oracle's outstanding-balance column is stale with respect to
> its own final EMI adjustment, on a bounded region at the rounding floor, while its principal column
> and its own totals are right.**"*

and the handoff says the same. **This is false inside the graded domain.**

**Counterexample family:** MNT 0.01, annual rate 600.0 %, `n ≥ 104` monthly repayments. Everything
else is T83's own graded-domain pin set (MNT dp 2, single disbursement on the 2024-01-01 schedule
start, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, both multiples-of null,
`(19, HALF_UP)`). I measured **22 such cells** (n = 104…121 contiguous, plus n = 150 and n = 200).

`T84B-NSW-R600p0-N108-B1`, in full [VERIFIED: my probe 2]:

```
totalDisbursedAmount   0.01
totalPrincipalAmount   0.00      <-- the oracle's own total says the principal was never repaid
totalInterestAmount    0.01
totalOutstandingAmount 0
rows 1..107   balance 0.01   principal 0.00   interest 0.00   total 0.00
row  108      balance 0.01   principal 0.00   interest 0.01   total 0.01
principal column sums to 0.00 against a 0.01 disbursement
```

Against T83's three "facts on all 198":

| T83's fact | in the second family |
|---|---|
| the principal column sums to the disbursed amount | **FALSE** — sums to `0`, on all 22 |
| `totalOutstandingAmount` reads `0` | true — which now makes the oracle's own total **wrong**, not right |
| the balance column is constant | true |
| every interest cell is `0.00` | **FALSE** — the final row carries `0.01` |

**And it is not a stale memo.** I re-ran T83's own `ProbeOrderDep` machinery, unchanged apart from
the shape list, on this family. The driver's stated discriminator was: *"A memo-staleness defect
predicts that a probe which reads the balance without first driving the EMI adjustment can differ…
**A genuine non-amortization predicts no order dependence at all.**"*

| shape | emitted | after forced recompute | order-dependent |
|---|---|---|---|
| `OD2-FAM2-R600p0-N104-B1` | 0.01 | **0.01** | **no** |
| `OD2-FAM2-R600p0-N108-B1` | 0.01 | **0.01** | **no** |
| `OD2-FAM2-R600p0-N120-B1` | 0.01 | **0.01** | **no** |
| `OD2-FAM1-R3p6-N360-B109` (family 1) | 1.09 | **0.00** | yes |
| `OD2-CLEAN-R600p0-N103-B1` (control, one repayment short) | 0.00 | 0.00 | no |
| `OD2-CLEAN-R3p6-N360-B110` (control) | 0.00 | 0.00 | no |
| `OD2-CLEAN-R21p6-N6-B120000000` (control, MNT 1,200,000) | 0.00 | 0.00 | no |

`paidPrincipal` restored and path identity true on all 7. **By the driver's own discriminator, this
is a genuine non-amortization, not a stale cache.** [VERIFIED: `/tmp/t84od/out/orderdep.json`]

**And the Go port reproduces it cell for cell.** On all 22, the port's schedule is
byte-for-byte the oracle's — **0 divergent cells** — including the `0.00` principal column. So this
is not a port-vs-oracle divergence at all; it is both implementations agreeing on a schedule that
does not repay the loan. [VERIFIED: my port run, 344 cells, `calibrationMismatchCells: 0`,
`refused: []`]

**Why this matters and is not a quibble.** G-8's whole remedial question is "how bad is this?".
T83's answer, now sitting in the gate record, is "one stale derived column, contradicted by the
oracle's own totals" — which is an argument *for* (a) and, on its own terms, an argument that (c) is
cheap. The second family is a different animal: a schedule whose principal column and whose own
`totalPrincipalAmount` both say the disbursed principal was never repaid, which no exemption scoped
"to the balance column" would cover, and which the port already reproduces silently today.

## **P0-2 — "`invariant_exemptions` is inert, so option (a) needs a port change" is refuted as a general claim. On the second family the exemption alone turns FAIL into PASS, with zero port change.**

This is the claim the task called the most consequential, and it is the one I attacked hardest.
`.softhouse/gates.md` now says:

> *"**Option (a) is NOT reachable with the existing mechanism alone.** Its full shape is: change the
> port to emit the oracle's stale balance, *and then* carry both exemptions … That is a **port
> change**."*

I built a parity vector for `T84B-NSW-R600p0-N108-B1` by the **same transcription code** T83 used
(`run-exemption-demo.py`'s `build()`, cells transcribed never computed, exact textual major→minor
scaling only), and graded it with the **real `conformance.Run` and the real Go port** over a scratch
store under `/tmp`. `.softhouse/vectors/` was neither read for content nor written; the corpus count
is unchanged.

```
=== NO-EXEMPTION ===
  exit 1  parityPass 0 parityFail 1 inadmissible 0 refused 0 invariantViolations 2
  T84-NONAMORT-B-NOEXEMPT -> FAIL (graded 761 cells, ungraded 2)
      detail: invariant principal_portions_sum_to_disbursed VIOLATED:
              principal advanced 1 minor units, principal repaid 0 minor units, difference -1
      detail: invariant principal_amortizes_to_zero VIOLATED:
              final row (REPAYMENT, due 2033-01-01) leaves 1 minor units outstanding, not 0
      invariant principal_portions_sum_to_disbursed  VIOLATED
      invariant principal_amortizes_to_zero          VIOLATED
      invariant balance_roll_forward                 HOLD
      invariant splits_sum_to_whole                  HOLD
      invariant monotonic_due_dates                  HOLD
      invariant contract_row_ordering                HOLD

=== WITH-EXEMPTION ===
  parityPass 1 parityFail 0 inadmissible 0 refused 0 invariantViolations 0
  T84-NONAMORT-B -> PASS (graded 761 cells, ungraded 2)
      invariant principal_portions_sum_to_disbursed  EXEMPT
      invariant principal_amortizes_to_zero          EXEMPT
      invariant balance_roll_forward                 EXEMPT
      … the other three HOLD
```

**761 graded cells, zero cell diffs, FAIL becomes PASS on the exemption alone.** No Go logic was
changed; `nexus/` was copied to `/tmp` and copied back nowhere. [VERIFIED:
`/tmp/t84-exemption-demo.json`, script archived at
`.softhouse/reviews/T84-evidence/src/exemption-demo.py`]

So the correct statement is the **scoped** one, and it is materially different from what is in the
gate record:

- on the sub-family where the port **diverges** (the stale-memo family — T83's 198 cells and 111 of
  mine), the divergence is a **cell diff**, exemptions have no power over cell diffs, and option (a)
  does require a port change;
- on the sub-family where the port **agrees** (the 22 cells above), there is **no** cell diff,
  `principal_amortizes_to_zero` and `principal_portions_sum_to_disbursed` fire against the *port's
  own output*, and `invariant_exemptions` is **exactly** the mechanism — reachable with no port
  change, no amendment, and no gate.

T83's reasoning for the general claim is stated explicitly in the handoff — *"**without** any
exemption all six invariants already HOLD because they read the **port's** output, which
amortizes"* — and that premise is simply not true across G-8. Where the port does not amortize, the
invariants do not hold, and the exemption is live. **The gate's recorded "cheap option" therefore
does exist; it exists on a part of the region T83 did not sample.**

## **P1-3 — "Every principal in the region is below MNT 0.25" is refuted by direct measurement.**

Handoff: *"**Every principal in the region is below MNT 0.25.**"* `gates.md`: *"**Every principal in
the region is far below one MNT** (the largest anywhere in the sweep is MNT 0.23). No commercially
realistic Mongolian loan amount is in it; the shapes are reachable only at the rounding floor."*

The parenthetical is true. The claim about *the region* is false, because the failure threshold
scales with the term: it is `0.5 / a(r,n)` and `a(r,n) → 1/n` as the rate falls, so the region grows
roughly like `n/2` minor units. Measured [VERIFIED: my probes 1 and 2]:

| annual % | n | largest **failing** principal | smallest clean |
|---|---|---|---|
| 3.6 | **360** (an ordinary 30-year monthly term) | **109 minor = MNT 1.09** | 110 |
| 1.2 | 360 | 151 = **MNT 1.51** | 152 |
| 0.12 | 360 | 176 = **MNT 1.76** | 177 |
| 3.6 | 600 | 139 = **MNT 1.39** | 140 |
| 1.2 | 600 | 225 = **MNT 2.25** | 226 |
| 0.12 | 600 | **291 = MNT 2.91** | 292 |

Every one bracketed on both sides by an emitted cell. `MNT 2.91` is **11.6×** the stated bound, and
`MNT 1.09` sits at a term (`n = 360`) that no one would call exotic. The *practical* conclusion —
that no realistic Mongolian loan **amount** is affected — survives; the **stated bound** does not,
and the shape of the region ("reachable only at the rounding floor", implying a fixed ceiling) is
wrong. A bound written into a gate record is load-bearing precisely because a later reader will not
re-derive it.

## **P1-4 — the closed form is refuted outside the sampled grid (18 measured cells). T83 was right to call it a hypothesis; the gate should now record that it was falsified.**

I registered in advance that the near-tie family `r = 1/(2B)` — where `B × a(r,n) → 0.5` **from
above** and the gap falls through the precision-19 floor — was where a closed form derived from
exact arithmetic would most likely part company with an oracle computing at `(19, HALF_UP)`. It did,
at exactly the predicted place:

| 600.0 % p.a., MNT 0.01 | `B·a − 0.5` | closed form | observed |
|---|---|---|---|
| n = 103 | +3.644e-19 | clean | clean |
| **n = 104** | **+2.429e-19** | **clean** | **FAILS** |
| n = 105 … 121 | +1.6e-19 … +2.5e-22 | clean | **FAILS (18 consecutive)** |

Over my 342 cells the closed form held on **324** and was refuted on **18**, all in this family; it
held on every one of the `RP`, `FAR`, `RATE`, `TERM` and `LONG` families (12 / 24 / 85 / 44 / 54).
[VERIFIED: exact-rational evaluation in `/tmp/t84-classify.py` and `/tmp/t84-eval*.py`]

**This is not a defect in T83's discipline** — it labelled the rule a hypothesis, scoped it to the
32 sampled shapes, and repeated the caveat in its Unverified section. That was the right call and it
is now vindicated. But `gates.md` currently records the rule with only "was NOT tested outside the 4
rates × 8 terms sampled" beside it; it should record that it has since been **tested and falsified**
there, or the next reader will treat 106/106 as licence. The 18 refuting cells are the same 18 that
carry P0-1's non-amortizing principal column, which is not a coincidence — the closed form breaks
exactly where the second family begins.

## P2-5 — one imprecise harness citation

Handoff and `gates.md`: *"`diffSchedule` decides FAIL before the invariant statuses are consulted
(`grade.go:487-497`)"*. In fact `CheckInvariants` runs **first**, at `grade.go:488`, and the
`if len(diffs) > 0 { … return r }` early-return at `:489-493` then short-circuits the **outcome**,
leaving the computed statuses reported but unable to change the verdict. The operative conclusion is
right; the sentence as written would mislead someone looking for where to intervene. [VERIFIED:
`grade.go:483-500`]

## P2-6 — provenance of the mechanism

`gates.md` attributes the `:400` / `:1180` / `:1210` chain to the driver's re-derivation, confirmed
by T83. It was in fact **first stated by T75** — `.softhouse/reviews/T75-pathA-multiplesof-review.md`
§5 already carries `:389-402`, the `:400` array, `:282-283` for the sibling memo, `isFullyPaid()` at
`:371-372` being `0 == 0` when every EMI quantizes to zero, the `:1178-1181` fallback, `:1180` as
"which populates the memo on the target period", and `:1210` as "a plain `@Setter` that invalidates
nothing". That is the whole causal chain, one fire earlier. T75's `isFullyPaid()` step is also the
piece that explains **why** the fallback fires, which neither the driver's note nor T83 carries — and
it is the piece that predicts the second family will behave differently, because there the final
row's interest is non-zero. Worth restoring to the record; T75 earns the credit and its extra step is
useful. [VERIFIED at every cited line]

---

# PART THREE — what I did NOT decide, and what I am not recommending

I analysed (b) and (c). **I decided neither and I recommend neither.** They amend the graded domain,
which is a change to a ratified DEC-n and a hard `user` gate. G-8's state stays **OPEN**.

I will say only what the measurement says about the option set, as fact and not as advice:

- **(a) is cheaper than T83 recorded on one sub-family and no cheaper on the other.** On the 22
  port-agreeing cells it is reachable today with an exemption and no port change (demonstrated
  above). On the stale-memo sub-family T83 is right that it needs a port change.
- Whichever option Buyan picks, the decision now has to cover **two** phenomena, not one. That is
  the substance of this rejection: T83 handed him a one-phenomenon decision.
- T83's own follow-up — that the harness has no way to say *"the oracle is wrong here and we know
  it"* — is strengthened by P0-1, because on the second family the **port** is wrong too, in the
  same direction, and nothing in the corpus would ever say so.

---

# What T83 must do to be accepted

Mechanical, and none of it re-measures anything T83 already got right:

1. **Re-scope the three unqualified sentences** in `.softhouse/gates.md` and in the handoff — the
   "G-8 is precisely…" definition (P0-1), the "option (a) is NOT reachable with the existing
   mechanism alone" conclusion (P0-2), and the "every principal in the region is far below one MNT"
   bound (P1-3) — so each says what it measured: *"on the 330 cells swept, at 4 rates × 8 terms ≤ 56,
   …"*.
2. **Record the second family** in G-8: 600.0 % p.a. / MNT 0.01 / n ≥ 104, 22 measured cells, port
   and oracle agreeing, principal column summing to zero, **not** order-dependent, and
   `invariant_exemptions` live on it. My captures are committed on this branch under
   `.softhouse/reviews/T84-evidence/out/` and the boundary at n = 103/104 is bracketed on both sides.
3. **Record that the closed form has now been falsified outside the sampled grid**, with the 18 cells
   (P1-4).
4. Fix the `grade.go` citation (P2-5) and restore T75's priority on the mechanism (P2-6).

Nothing needs re-capturing. The boundary table stands. The port comparison stands. The
order-dependence result stands, and is now known to be the discriminator **between** the two
families rather than the explanation of the whole gate.

---

# Cells I personally re-measured, and what I took on trust

**Re-measured (nothing here is taken from T83's numbers):**

- all **332** cases of T83's capture — re-run from its committed sources, canonical sha256 identical,
  `captures` arrays compared and equal;
- all **330** sweep classifications — my own classifier, my own id↔inputs consistency check, exact
  integer minor units, exact-rational closed-form evaluation;
- **342** new cells of my own across six attack families, two runs, both calibrated;
- the Go port on **344** cells (mine) and on all **332** of T83's (its script re-run, output
  identical to the committed file);
- **16** order-dependence shapes (T83's 9, re-run; 7 of mine on the second family and its controls);
- **4** graded vector variants through the real `conformance.Run` (T83's two, reproduced exactly; my
  two, new);
- `bash .softhouse/conformance.sh` end to end;
- every source citation in T83's handoff and in `gates.md`, opened at the pinned commit;
- the commit DAG by parent pointers; the `.softhouse/vectors/` and `nexus/` diffs; `gofmt -l`.

**Taken on trust (with the reason it is safe):**

- the internals of `classify-boundary.py` and `measured-boundary.json` — I did not audit them; I
  wrote an independent classifier instead and got the same 330/198/132/0 and the same 32-row table;
- the contents of `capture-t83-oracle-log.txt` and `capture-t83-stdout.txt` beyond the MoneyHelper
  attestation lines;
- the **mechanism of the second family** — I measured *that* it is not order-dependent and that the
  principal column sums to zero; I did **not** locate the code path that produces it. `[UNVERIFIED:
  the cause of the second family]`;
- **Path B / REST** behaviour — not measured, by me or by T83. Everything here is Path A.
  `[UNVERIFIED]`;
- whether the second family extends below n = 104 at other rates, or exists at `MinorUnitDigits`
  other than 2. `[UNVERIFIED]` — I bracketed it only at 600.0 % and 300.0 % (where at B = 2 it does
  **not** appear through n = 204).

**What would have made me approve:** if T83 had written its three conclusions as scoped to the 32
shapes it swept — *"on the region measured"* rather than *"G-8 is precisely"* — I would have
approved it, because the measurement itself is the best-evidenced artefact I have reviewed in this
program and I could not break a single number in it.
