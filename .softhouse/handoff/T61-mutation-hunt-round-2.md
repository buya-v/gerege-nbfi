# T61 — mutation hunt, round 2

Branch `softhouse/T61-mutation-hunt-round-2`. Context `tier0-harness-schedule-poc` / loan schedule.
Pattern **P-3**: mutate the port into a named wrong implementation → run the **real** harness → a
survivor is a blind spot in the **corpus** → capture the separating shape from the live reference
oracle → promote → prove the mutation now dies.

> "The oracle" is the Fineract reference implementation. Oracle Database is prohibited and appears
> nowhere in this work. PostgreSQL is the only permitted database; the Path A seam is a library
> call and opens no connection at all.

---

## HEADLINE

**Parity 29 → 32. One more money-moving mutation is dead. And the fire's primary hypothesis was
answered — with a NO, backed by measurement rather than by a null sweep result.**

```
VERDICT: PASS (exit 0) — 32 parity vectors match the pinned reference oracle, 2495 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

`go build` 0 · `go vet` 0 · `go test ./...` green · `--prove` **20/20** · 6/6 invariants hold ·
0 inadmissible · 0 harness errors · 0 invariant assertions not-run · pinned Fineract checkout
clean · oracle **never restarted** (up 39 h through this task).

---

## Base verification (P-5) — and it went stale UNDER me

At start: `67bee40`, 29 promoted parity vectors, `.softhouse/capture/` carrying `periodratio`,
`emiloop`, `leapboundary`, `actualactual`, `src`. Correct base, verified before a line was written.

**T59 and T60 then merged into `main` while this task ran.** Detected at verification time by
`git diff --stat main -- nexus/` showing changes I had not made. Rebased onto `e42c3c5` and
**re-ran everything** — build, vet, test, conformance, `--prove`, and the whole mutation table.

That mattered, twice:

* **T60** rewrote the invariant layer around unrecorded cells. My three vectors carry unrecorded
  cells on the disbursement row, so their invariant result is only meaningful on the new layer.
  Re-run: `balance_roll_forward` holds 33, and the new *"invariant assertions that could not run"*
  section reports **NONE**.
* **T59** added in-loop cancellation checks to `emi.go`, which **broke three mutation anchors**
  (M1, M3, M9). The runner reported `ANCHOR MISS` loudly and refused to score them rather than
  silently reporting a survivor. Re-anchored against T59's code and re-run. **Every number in the
  table below is from the rebased tree.**

An anchor-based mutation runner that silently no-ops is the D-5/P-4 failure mode; this one is
built so that a missed anchor is a loud non-result, never a green.

---

## STEP 1 — the RESUME's caveat, checked empirically. It is NOT stale.

`.softhouse/RESUME.md` records that the closed-form-EMI folklore and the oracle's fold "reproduce
the current corpus identically, **because every promoted vector runs `DAYS_30`/`DAYS_360` so every
rᵢ is equal**". T55 and T58 had promoted 18 vectors since, so this had to be re-established rather
than assumed.

**All 29 promoted parity vectors, inspected file by file:**

| property | count |
|---|---|
| `day_count = FIXED_30_360` | **29 of 29** |
| `repayment_frequency_unit = MONTHS` | **29 of 29** |
| `repayment_every = 1` | **29 of 29** |
| `day_count = ACTUAL_ACTUAL` | **0** |

So every rᵢ is `rate × 30/360` — **identical across every period of every promoted vector**. The
caveat holds exactly as written. (T55's 33 leap-boundary captures and T48's 58 ACT/ACT captures are
real, but **none is promoted**: `capabilities.json → daycount.actual.actual.in_graded_domain` is
`false`, and `REFUSE-01` stands.)

The three vectors T61 adds are also `FIXED_30_360`/`MONTHS`/`1`, so the property is now **32 of
32**. Widening it is the follow-up work described under *Gates and backlog*.

---

## STEP 2 — thirteen mutations, all run against the REAL harness

`.softhouse/handoff/T61-mutations.py` — each mutation is a literal source substitution with a
unique anchor, applied to the committed tree, scored by `.softhouse/conformance.sh`, and reverted
unconditionally in a `finally`. Four were already dead going in (T57/T58); these thirteen are new.

### The before/after kill table

| mutation | at 29 vectors | at 32 vectors |
|---|---|---|
| `CLOSED-FORM-POW-EMI` (M1) | PASS, exit 0 | PASS, exit 0 — **survives, and provably cannot be killed in this graded domain** |
| `FN-FOLD-OUTER-ROUNDING-DROPPED` (M2) | PASS, exit 0 | PASS, exit 0 — survives, same reason |
| `RATEFACTORN-FIRST-MULTIPLY-UNROUNDED` (M3) | PASS, exit 0 | PASS, exit 0 — survives, same reason |
| `GROWTH-FACTOR-MC-ROUNDED-ADD` (M4) | PASS, exit 0 | PASS, exit 0 — survives, same reason |
| `PERIODRATIO-MONTHEND-SPECIAL-CASE-DROPPED` (M5) | **6 FAIL, exit 1** | **6 FAIL, exit 1** |
| `INTEREST-RATE-FACTOR-SPAN-ENDS-AT-SEGMENT-DUE` (M6) | PASS, exit 0 | PASS, exit 0 — **structurally unreachable** |
| **`MONEY-QUANTIZATION-HALF-EVEN` (M7)** | **PASS, exit 0** | **3 FAIL, exit 1** — `T61-HE-A`, `T61-HE-B`, `T61-HE-C` |
| `UNRECOGNIZED-INTEREST-CARRY-DROPPED` (M8) | PASS, exit 0 | PASS, exit 0 — **structurally unreachable** |
| `FINAL-RESIDUAL-OVERSHOOT-GUARD-DROPPED` (M9) | PASS, exit 0 | PASS, exit 0 — **structurally unreachable** |
| `FINAL-ROW-PRINCIPAL-IS-WHOLE-REMAINING-BALANCE` (M10) | PASS, exit 0 | PASS, exit 0 — **identically equal, never killable by a schedule** |
| `EMI-ADJUST-GUARD-BOUNDARY-INCLUSIVE` (M11) | PASS, exit 0 | PASS, exit 0 — open |
| `EMI-ADJUST-LOOP-BOUNDED-AT-ONE-PASS` (M12) | **7 FAIL, exit 1** | **7 FAIL, exit 1** |
| `SEGMENT-INTEREST-DIVIDE-AND-MULTIPLY-SWAPPED` (M13) | **2 FAIL, exit 1** | **2 FAIL, exit 1** |

**Three of the thirteen were already graded by the corpus as it stood** — M5 (the four-line
month-end special case at `PEC:1426-1436`), M12 (the smoothing loop's three-adoption bound) and
M13 (the order of the divide and the multiply in `InterestPeriod.java:143-158`). That is a fact
about the corpus worth recording as loudly as the survivors: T57's and T58's vectors are doing
work beyond the mutations they were captured for.

---

## The primary hypothesis, answered: **NO, and here is the measurement**

The brief's headline hypothesis was that `CLOSED-FORM-POW-EMI` is the corpus's biggest blind spot
and that a capture could close it. The first half is true. **The second half is not, and the
reason is quantitative, not a shrug at a null result.**

**Sweep.** `.softhouse/handoff/T61-sweep/` builds a scratch copy of the port (never the committed
tree), applies a mutation, and diffs whole schedules across a grid of on-lattice MNT shapes.

> `M1`, `M2`, `M3`, `M4`: **0 separating shapes out of 40,001** consecutive principals at n=6,
> 21.6 %. `M6`: 0 of 402 even with the disbursement moved to mid-period. `M11`: 0 of 72,003.
> `M7`, by contrast: **104 of 2,001** — which is what a genuinely reachable defect looks like.

**Measurement, which is the part that settles it.**
`.softhouse/handoff/T61-sweep/emi-magnitude.py` re-derives the level installment both ways in exact
rational arithmetic at `(19, HALF_UP)` and prints the gap:

| rate | n | EMI gap, **minor units** | distance to the nearest half-minor-unit boundary |
|---|---|---|---|
| 21.6 % | 6 | **0** | 2.6e-01 |
| 21.6 % | 12 | 2.0e-11 | 2.8e-01 |
| 7.0 % | 6 | 9.0e-11 | 2.1e-02 |
| 18.5 % | 360 | 2.6e-11 | 6.3e-02 |

**The perturbation is ~1e-11 minor units — about thirteen orders of magnitude below one cent.**
A shape can only convert it into a payable difference by sitting within 1e-11 of a rounding
boundary; the chance is ~2e-11 per shape, so finding one needs ~5×10¹⁰ shapes, and the vector you
found would be a knife edge that graded nothing anybody could reason about.

**M2, M3 and M4 are the same class** — they move where a rounding sits inside the fold, and under
equal rᵢ that is a last-place perturbation of the same size.

### So what WOULD separate them, exactly

The fold and the closed form are **mathematically identical when every rᵢ is equal**, and differ
only in rounding path. They become genuinely different functions **only when the rᵢ differ**.
Working out from `ProgressiveEMICalculator.java`, inside DEC-1's contract domain there is exactly
one way to make them differ:

* `MONTHS` + `FIXED_30_360` → `r = rate × 30/360`, every period. Equal. *(the whole corpus)*
* `DAYS` / `WEEKS` + `FIXED_30_360` → `rate × repayEvery/360`, `rate × 7·repayEvery/360`. Equal.
* multiple interest sub-periods inside one repayment period → the segments' rate factors **sum**
  back to the whole-period factor (verified by hand at precision 19), and in any case a
  pre-disbursement segment always carries a zero balance under a single disbursement.
* **`ACTUAL_ACTUAL` across two calendar years of DIFFERING LENGTH** → `rate × 30/366` in a leap
  year against `rate × 30/365` in a common one, and the per-calendar-year fraction accumulation
  at `PEC:1550-1566` for a period that straddles the boundary. **The rᵢ differ in the fourth
  significant digit.** This is the only route.

**That is precisely the shape the RESUME predicted, and it is outside the graded domain today** —
`capabilities.json` has `daycount.actual.actual.in_graded_domain: false`, `REFUSE-01` stands, and
the port hard-refuses at `generator.go:357`. Closing this blind spot is therefore **not a capture
task at all**: it needs the ACT/ACT arm PORTED first. Raised below as **B-1**, with an acceptance
test that is already written.

I deliberately did **not** spend the oracle on ACT/ACT captures this fire: 58 Path A ACT/ACT
captures and 33 Path B leap-boundary captures already sit uncommitted-to-the-store in
`.softhouse/capture/actualactual/` and `leapboundary/`, so the next task's bottleneck is the port,
not the observation.

---

## STEP 3 — the capture, and the prediction it confirmed

The oracle was spent on the one survivor that **is** killable by an ordinary MNT loan.

### Prediction, registered BEFORE the capture

`.softhouse/capture/t61-halfeven/PREDICTION.md` was committed in `d543fd0`, **one commit before**
`run-pass3f.sh` ran. It names the full schedule of all three shapes and one sharp claim:

> **the oracle will emit `18000.95` on period 1 of `T61-HE-B`, not `18000.94`.**

Derived from source, not searched for: on this lattice the period-1 rate factor is exactly `0.018`,
so period-1 interest in minor units is `18·B/1000` — an exact tie when `B ≡ 250 (mod 500)`, and the
two tie rules differ when `⌊18B/1000⌋` is even. `B = 100005250` gives `1800094.5` with `1800094`
even.

**The oracle confirmed it. `check-prediction.py`: 54 cells, 0 mismatches.**

```
p1  interest  predicted = OBSERVED 1800095   HALF_EVEN port would emit 1800094   margin 1
```

### The capture recipe

`.softhouse/capture/README-pass3f.md`. **Pass 3f is pass 3e's rig with a new case list**, the same
relationship pass 3c has to pass 3b. It was built **mechanically** by
`.softhouse/handoff/T61-sweep/build-pass3f.py`, which aborts if any substitution anchor fails —
so *"not one precondition was weakened"* is a property of the construction, not a claim in a
comment.

```
sh .softhouse/capture/src/run-pass3f.sh
capturesCanonicalSha256: bcdd5e0e4bd22a36f1531f3b75052d3570e4348a810bcaf95bbbd65bdf3c07b6
```

### RIG CALIBRATION report — four, one more than pass 3e

| calibration | reproduces | from | precision | inputs identical | observed identical |
|---|---|---|---|---|---|
| `P-CAL` | `P-CAL` | `capture-prod3b-raw.json` | 12 | yes | yes |
| `P-CAL-P00` | `P-00` | `capture-prod3b-raw.json` | 19 | yes | yes |
| `P-CAL-EMI6` | `P-EMI-6-1M014632` | `capture-prod3c-raw.json` | 19 | yes | yes |
| **`P-CAL-LATQ0a`** *(added by this pass)* | `P-LAT-Q0a` | `capture-prod3e-raw.json` | 19 | yes | yes |

The fourth is the one that matters. `P-LAT-Q0a` is the **same question** as all three candidates in
every field but the principal — same lattice date, same term, same rate, same currency, same
MathContext — and its observation is already a promoted parity vector. The rig is calibrated on
exactly the arithmetic this promotion rests on, not on something merely nearby. Comparison is
canonicalised JSON, cell for cell, **tenant id included**.

### The three shapes

| id | principal | term | rate | widest M7 margin |
|---|---|---|---|---|
| `T61-HE-A` | MNT 1,000,541.50 | 6 | 21.6 % | **6 minor** |
| `T61-HE-B` | MNT 1,000,052.50 | 6 | 21.6 % | **4 minor** |
| `T61-HE-C` | MNT 1,000,089.50 | 6 | 21.6 % | **5 minor** |

Ordinary, on-lattice, strictly inside the graded domain, identical to the promoted `P-LAT-Q0a` in
every field but the principal.

---

## STEP 4 — promotion, audit, and the loop closed

**Counterfactual, with its control.**
`.softhouse/capture/t61-halfeven/out/t61-counterfactuals-pass3f.json`:

```
3 cases, 60 graded money cells, baselineMismatches 0
```

With the mutation switched **off**, the model reproduces every one of the 60 cells the oracle
emitted. So the only thing a reported margin can be measuring is the named change. (T58's
discipline; a counterfactual whose unmutated form did not reproduce the oracle would be measuring
its own defect and calling it a margin.)

**Promotion.** `.softhouse/handoff/T61-promote-vectors.py`, mechanical. It refuses to write a
margin it cannot find in the counterfactual report, refuses a case on `PIN.json`'s denylist, and
refuses anything not at `(19, HALF_UP)` in both dimensions.

**Transcription audit.** `.softhouse/handoff/T61-transcription-audit.py` — an independently written
second converter, plus a round trip back to the oracle's own emitted characters:

```
T61 TRANSCRIPTION AUDIT — 3 vectors, 291 cells checked, 0 mismatches
```

It also re-checks, mechanically: `capture_ref` resolves and its recorded sha256 matches the file on
disk; `capture_case_id` names a case **inside** it; the request round-trips against the capture's
own inputs including the rate as an exact rational; both MathContexts are `(19, HALF_UP)` and agree
with `request.rounding`; and **no JSON number in any vector file carries `.`, `e` or `E`**.

**No `PIN.json` change was needed.** No `capabilities.json` change was needed. `REFUSE-01`
untouched. `contract.go` untouched, never `gofmt`ed. `.softhouse/vectors/README.md` untouched —
T60 owns it and did in fact edit it this fire, so leaving it alone avoided a real collision.

**The loop closes:**

| mutation | at 29 vectors | at 32 vectors |
|---|---|---|
| `MONEY-QUANTIZATION-HALF-EVEN` | **PASS, exit 0** | **3 FAIL, exit 1** |

---

## The survivors, honestly classified

**Not all survivors are the same kind of thing, and calling them all "blind spots" would be
false.** Three of these cannot be killed by any schedule vector, ever, and saying so is a
stronger result than leaving them on a to-do list.

### Provably unreachable inside the contract domain — close these as NOT-A-GAP

* **M6 `INTEREST-RATE-FACTOR-SPAN-ENDS-AT-SEGMENT-DUE`.** The span distinction only bites on a
  segment that both precedes a later segment and carries a balance. Under a **single**
  disbursement — which the graded domain requires, `multi.tranche.disbursement` being refused —
  every pre-disbursement segment carries a **zero** balance (`updateOutstandingBalances`: the first
  segment of the first period keeps its constructed zero, and every earlier period closes at
  zero). Zero balance ⇒ zero interest ⇒ the rate factor is never read. Confirmed: 0 of 402
  separating shapes with the disbursement moved 10 days into period 1. **It becomes gradeable only
  if multi-tranche enters the contract domain.**
* **M8 `UNRECOGNIZED-INTEREST-CARRY-DROPPED`.** The carry is `max(0, calculated − due)` and
  `due = min(calculated, emi)`, so it is non-zero only where a period's interest **exceeds** its
  installment. On a fully amortizing declining-balance schedule `EMI = P·r(1+r)ⁿ/((1+r)ⁿ−1) > P·r =
  interest₁` for every n ≥ 1, and pre-disbursement rows carry zero of both. **Identically zero on
  every schedule this contract can express.** It becomes gradeable only with payments, grace or
  reschedule — Tier A.
* **M10 `FINAL-ROW-PRINCIPAL-IS-WHOLE-REMAINING-BALANCE`.** `applyFinalPeriodResidual` makes the
  total of all installments equal disbursed + due interest, so the last row's `EMI − interest` is
  **identically** its opening balance. The two readings are the same number on any schedule where
  `principal_amortizes_to_zero` holds — which the harness checks on every vector. **This is a
  shape defect that no schedule vector can ever catch**, and the port's own doc comment says so.
  It would diverge under partial payment, outside the contract. Leaving it "open" would imply a
  vector could close it; it cannot.

### Genuinely open, and now sized

* **M1 / M2 / M3 / M4** — the fold-vs-closed-form family. Open, and **not closable inside
  `FIXED_30_360`** (measured above). Blocked on porting the ACT/ACT arm: **B-1**.
* **M11 `EMI-ADJUST-GUARD-BOUNDARY-INCLUSIVE`** — `>` vs `>=` on the smoothing guard. It differs
  only when `|EMI_last − EMI_penult|` in minor units is **exactly** `⌊n/2⌋ × 100` (for n=6, exactly
  MNT 3.00). Unlike M1 that is an exact **integer** coincidence, so it is reachable in principle
  rather than 13 orders of magnitude away. **0 separating shapes in 72,003** on-lattice shapes
  (three rates, n=6, principal step 25 minor units). Still open, and the right next move is a
  targeted solve — pick n and rate, then solve for the principal that puts the difference on the
  boundary — rather than more sweeping. **B-2**.

---

## Gates and backlog

**No gate is raised by this task.** Nothing here contradicts DEC-1, `contract.go` is untouched, no
`user` decision was crossed, and the four standing gates (G-2, G-3, G-4, G-5) are unaffected.

* **B-1 — port the ACT/ACT arm, then close the fold-vs-closed-form blind spot.** The largest
  documented blind spot in the corpus is **not closable by capture**; it needs
  `partialPeriodCalculationNeeded` / `calculatePeriodFractions` /
  `getFractionPeriodDueDateForEndOfYear` / real `Year.length()` denominators implemented in the
  port, `generator.go:357`'s refusal lifted, `capabilities.json →
  daycount.actual.actual.in_graded_domain` flipped, and `REFUSE-01` retired (it already carries
  `retires_when_capability_graded`, so the harness will say so by itself). The oracle evidence
  largely **already exists**: 58 Path A captures in `.softhouse/capture/actualactual/` and 33
  Path B leap-boundary captures in `leapboundary/`. **Acceptance test, ready to run:**
  `python3 .softhouse/handoff/T61-mutations.py M1 M2 M3 M4` must go from `SURVIVES` to `KILLED`.
  Promotion condition is the corrected one in `capabilities.json` — the period must span two
  calendar years of **differing length**; the older "non-zero first segment" wording is too strong
  (T55-N1).
* **B-2 — M11's guard boundary.** Solve for the shape rather than sweep for it.
* **B-3 — close M6, M8, M10 as NOT-A-GAP in `capabilities.json`.** They are currently
  indistinguishable, in any written record, from mutations nobody has got to yet. A line of
  evidence each would stop a future fire re-hunting them. *(Not done here: `capabilities.json` was
  outside this task's declared scope and T60 was editing the store's docs in parallel.)*
* **B-4 — the sweep rig is reusable.** `.softhouse/handoff/T61-sweep/run-sweep.py M<n> --n … --rates
  … --p-from …` builds base and mutant scratch copies and diffs whole schedules. Cost is roughly
  n^2.4 per shape, so keep n small and the principal range wide.

---

## Reverted, and proven reverted

Every mutation is applied to the committed tree and reverted in a `finally` block; the runner
re-runs conformance afterwards and prints the result. **No mutant code is committed:**

* `git status --porcelain` — empty.
* `git diff main -- nexus/` — **empty**. Not one byte of the port changed on this branch.
* grep for every mutant construct (`Bit(0)`, `adjustCounter > 1`, `_ = seedDay`,
  `_ = totalDuePaidDiff`, `_ = carriedUnrecognized`, `Cmp(threshold) >= 0`) over `nexus/` —
  no hits outside pre-existing enum and doc-comment text.
* `.softhouse/conformance.sh` with the true implementation — **exit 0**.

Prohibited-technology scan over everything added: no `ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql.cj`,
`mariadb`, `go-sql-driver/mysql`, Stripe/Plaid/Lithic/Persona. Money is `int64` minor units
throughout; the only rational arithmetic is `math/big.Rat` and Python `fractions.Fraction`, both
exact. **`float(` appears nowhere in any file this task added** — an early draft of the
transcription audit carried a `float(0)` in dead code and of the magnitude script a `%e` format;
both were removed and the scientific-notation renderer rewritten in exact integer arithmetic.

*(One pre-existing `BigDecimal.valueOf(7.0)` survives in `Capture3f.java`'s calibration cases. It is
carried **verbatim** from `Capture3b/3c/3e.java` and must stay byte-identical or the calibration
cannot reproduce the committed observation. It is oracle-side fixture input, it long predates this
task, and changing it would break precondition 10.)*

---

## Verification transcript

```
go build ./...   exit 0
go vet ./...     exit 0
go test ./...    ok  loanschedule 2.665s · ok loanschedule/conformance 1.891s

.softhouse/conformance.sh                       EXIT=0
    parity vectors          PASS 32   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    refused                 0
    inadmissible            0
    harness errors          0
    cells compared          2495 graded, 64 ungraded (never recorded by the capture)
    kills named             89 money, 7 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0
    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)

VERDICT: PASS (exit 0) — 32 parity vectors match the pinned reference oracle, 2495 cells compared.

.softhouse/conformance.sh --prove                PROOFS: 20 passed, 0 failed
python3 .softhouse/handoff/T61-transcription-audit.py    291 cells, 0 mismatches
python3 .softhouse/capture/t61-halfeven/check-prediction.py   54 cells, 0 mismatches
git -C /Users/buv/fineract status --porcelain    (empty)
git -C /Users/buv/fineract rev-parse HEAD        426a23544e8426a38ae43ae404670a0a7e85b9eb
docker ps                                        fineract-fineract-1 Up 39 hours (healthy)
                                                 fineract-db-1       Up 2 days  (healthy)
```

The reference oracle was **not** restarted, rebuilt, or brought down. The capture runs a
`docker run --rm` against the pinned **image**; the long-running containers were never touched.
