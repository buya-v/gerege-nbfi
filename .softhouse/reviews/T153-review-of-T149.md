# T153 — independent review of T149 (`softhouse/T149-halfup-tie-vector`)

Reviewer task **T153**, run `2026-08-21-run2-tierA-gl-accounting-A2`, branch
`softhouse/T153-review-t149`, forked from `main` @ `187e972`. Reviewed:
`softhouse/T149-halfup-tie-vector` @ `0b292c1` (two commits, fork point `82d31ee`),
read from the **branch** with `git show` / `git diff main...`, never from a worktree copy.

---

## VERDICT: **MICRO-FIX** — the vector is admissible, exact and discriminating; two prose claims in it overstate their own control

The promotion itself survives everything I could throw at it. I re-observed the tie live,
re-derived the entire schedule from first principles, re-ran all three red/green arms, and
re-ran conformance on a scratch merge into current `main`. **Every number in the vector is
right, and I found no defect in any money path.**

What I did find is two sentences — one in the vector's `_note`, one in the
`crosscheck-vs-patha.py` output that the `_note` and `t76/PROMOTION-DECISION.md` both
restate — that claim a **tighter control than the evidence has**. Neither changes a number.
Both are the class T149 itself named one level down: a claim about a control that the
control does not quite support. I measured the missing controls myself and **both
conclusions survive**, which is why this is a micro-fix and not a rejection.

Fix set out in §7. **≤ 10 lines, prose only, no number, no money logic, no `nexus/` byte.**

---

## 1. (a) The tie, re-observed live — T149's numbers reproduce, and its capture is byte-identical to mine

I did not take T149's capture on report. I wrote the request myself from the vector's own
declared inputs and posted it.

**The request I actually issued:**
`.softhouse/capture/pathb/t153/req/t153-reobs-p9.json`,
**sha256 `b126725ac3e27606805fe114617c3455ee93f342d9632dafca627bf78583ea42`**
(textually identical to T149's `t149/req/calc-t149-tie-p9.json`, sha256
`67abfa6b92c85ee5f54bf09a72dbaec40558512dcdc1afddd63a732e53139442`, except for a trailing
newline — `diff` reports only `\ No newline at end of file`).

Posted `POST /loans?command=calculateLoanSchedule`, `Fineract-Platform-TenantId: gerege`,
HTTP 200.

| arm | tenant | product | request sha256 | response sha256 | period-1 interest | total interest |
|---|---|---|---|---|---|---|
| HALF_UP | `gerege` | 9 (30/360) | `b126725a…` | **`39f56dc2…`** | **`20925.05`** | `140457.89` |
| HALF_UP | `gerege` | 11 (ACT/ACT, the pinned canary's product) | `7dd9f5ee…` | `39f56dc2…` | `20925.05` | `140457.89` |
| HALF_UP | `gerege` | 1 (ACT/ACT) | `d0894b4a…` | `39f56dc2…` | `20925.05` | `140457.89` |
| HALF_EVEN | `default` | 1 (ACT/ACT) | **`d0894b4a…`** | **`140ce792…`** | **`20925.04`** | `140457.88` |
| HALF_EVEN | `default` | 10 (gerege 11's twin) | `06c75954…` | `140ce792…` | `20925.04` | `140457.88` |

[VERIFIED: `.softhouse/capture/pathb/t153/out/`, digests in `t153/README.md`]

Three things fall out that are worth more than "T149 was right":

* **`39f56dc2c94a6da59235af7d0ecb7d51548bcf3f4d52730a94c864d7f65a3d25` is byte-for-byte
  T149's committed `t149/out/gerege/T149-TIE-P9-raw.json`**, and `140ce792ef4855a5…` is
  byte-for-byte its committed HALF_EVEN arm `out/default-HALF-EVEN-ARM/pmode2-default-raw.json`.
  Two independent captures, hours apart, on the same containers: identical bytes.
* **I got a cleaner counterfactual than T149 did.** T149's two arms are gerege product 11
  vs default product 10 — twins, but not the same row. Rows `d0894b4a…` above are the
  **same request bytes at the same product id** posted to the two tenants, and they
  separate `20925.05` from `20925.04`. That is a stronger form of T149's claim than T149
  made.
* Product ids do **not** align across tenants — id 9 on `default` is `T22 mode probe mult1`,
  not a 30/360 product, and it answers a different total (`140457.91`). Recorded in
  `t153/README.md` so the next Path B task does not step in it.

**The arithmetic, re-derived in integers, not accepted:**
`116,250,250 × 27/1500 = 4185009/2` — an **exact** half-minor-unit tie.
HALF_UP → `2092505` = `20925.05`; HALF_EVEN → `2092504` = `20925.04` (4 is even).
[VERIFIED: `t153/verify/rederive-schedule-exact.txt`]

**The rounding modes are the tenants' own, read from the rows:**
`c_configuration.rounding-mode` = **4** on `fineract_gerege`, **6** on `fineract_default`
[VERIFIED: live `psql`]. `MoneyHelper.PRECISION = 19` in the **deployed** jar, read by
`javap -constants -p` out of `BOOT-INF/lib/fineract-core-1.16.0-SNAPSHOT.jar` inside
`fineract-fineract-1` [VERIFIED], and in the pinned source
[VERIFIED: `fineract-core/…/MoneyHelper.java:35`]. So the production `MathContext` really
is `(19, HALF_UP)` on the arm that was promoted.

### 1.1 I re-derived the whole schedule, not just the tie

`t153/rederive-schedule-exact.py` rebuilds all 12 periods in **exact rational arithmetic**
(`fractions.Fraction`, no float anywhere including intermediates) from four inputs only —
principal `116250250` minor, `27/125` p.a. ÷ 12, n = 12, HALF_UP at 2 minor digits:

```
EMI (HALF_UP of the exact rational annuity) = 10858003 minor units
  period 1 … period 12   ok
  total interest  14045789   ok
```

**12 of 12 periods and the total agree with the vector in every money cell.** That is not a
transcription check — it is the vector re-derived from its own declared inputs, and it
means the oracle's answer here is the annuity, not an oracle quirk the port happens to
mimic.

### 1.2 Transcription: every recorded cell present, every withdrawn cell genuinely absent

`t153/verify-transcription.py` compares the vector against **my** capture, and also asserts
the converse — that nothing in `unrecorded_fields` was in fact emitted:

```
vector rows 13   response rows 13
MISMATCHES: 0
  sum(principal_minor) = 116250250   disbursed = 116250250
  sum(interest_minor)  = 14045789    declared total = 14045789
  final outstanding_principal = 0
  rows where principal + interest != total_due: none
```

The three withdrawn cells are honest. Path B's disbursement row is exactly
`{dueDate, principalDisbursed, principalLoanBalanceOutstanding, feeChargesDue,
feeChargesOutstanding, totalOriginalDueForPeriod, totalDueForPeriod,
totalOutstandingForPeriod, totalOverdue, totalActualCostOfLoanForPeriod, downPaymentPeriod}`
— **no `fromDate`, no `period`, no interest field** [VERIFIED: my own raw capture]. The
`vectors/README.md` field list T149 added is correct to the field.

Store-wide census on the merged tree: **42 of 43** parity vectors withdraw exactly
`{installment_number, interest_minor}`; `T149-PATHB-TIE` alone withdraws those plus
`from_date`; **0 other exceptions** [VERIFIED: mechanical census over
`.softhouse/vectors/loanschedule/*.json`]. T149's README edit is accurate.

---

## 2. (b) Both admissibility claims — VERIFIED, and T76's `PROMOTE NOTHING` is genuinely got past

### 2.1 Product 9 is genuinely 30/360 — VERIFIED from the row

```
id | name                      | days_in_month_enum | days_in_year_enum
 9 | T22 probe p09-sarp-360-30 |                 30 |               360
11 | T22 mode probe halfcent   |                  1 |                 1
```
[VERIFIED: `select … from m_product_loan` on `fineract_gerege`, live]

So `day_count: "FIXED_30_360"` in the vector **is what the oracle ran**, and the canary's
product 11 is indeed ACTUAL/ACTUAL. This is exactly the limb T76 refused `B-01` on —
*"writing `FIXED_30_360` anyway would state a product setting the oracle did not have"* —
and T149 answered it by changing the product rather than the transcription. Correct.

The byte-identity T149 offers alongside it is real and I observed it independently:
products 9 (30/360), 11 (ACT/ACT) and 1 (ACT/ACT) all return `39f56dc2…` at the tie
principal. **Worth stating plainly, because the vector does not:** this means the vector
**cannot discriminate day count** — a port that ran ACT/ACT on this shape would still pass
it. That is not a defect (the vector claims exactly one counterfactual, and it is not day
count), but a later task must not read `FIXED_30_360` here as coverage.

Test 1 and test 2 also hold on data I read myself: `capabilities.json` gives
`seams[path_b_server].status["schedule.core"] = "exercised"` and
`capabilities["schedule.core"].in_graded_domain = true`; `dec1_revision` is **12** in both
`capabilities.json` and the vector [VERIFIED].

### 2.2 The `interestCalculationPeriodMethod` closure — the measurement is real, the *statement of it* is not tight

T76's residual is quoted exactly: *"Whether SARP is behaviourally identical to unset is
**[UNVERIFIED]** — I did not test it, and no capture in this set can."*
[VERIFIED: `t76/PROMOTION-DECISION.md:48`]

The measurement reproduces. I posted the 1.2M control myself on product 9 and got
**`713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009`**, which is the digest
of the committed `pathb/out/B-01-baseline-raw.json` captured by T36 in a different fire, and
of T149's `T149-CTRL-P9-1M2-raw.json`. Total interest `144988.47` = **14,498,847** minor
units = the promoted Path A vector `P-MNT-1M2`'s
`observed_total_interest_minor` [VERIFIED].

**But the control is not as tight as it is described.** `P-MNT-1M2`'s
`schedule_start_date` is **2024-01-01** and its disbursement is 2024-01-01
[VERIFIED: the vector file]; T149's Path B control posts `expectedDisbursementDate:
"01 January 2026"` [VERIFIED: `t149/req/calc-t149-ctrl-p9-1m2.json`]. So **two** inputs
differ between the two observations, not one — ICPM *and* the schedule start year — and
2024 is a leap year while 2026 is not. The sentence

> *"With the day count controlled, ICPM is the only remaining difference and it moves nothing."*

is therefore **false as written**, in the vector's `_note`, in `crosscheck-vs-patha.py`'s
printed RESULT, and in the `t76/PROMOTION-DECISION.md` amendment.

**I measured the missing control rather than reasoning about it.** Product 9, MNT 1,200,000,
start 2026-01-01 vs start 2024-01-01 (client 2, activated 2023-01-01 — client 1 is activated
2026-01-01 and refuses a 2024 submission with
`error.msg.loan.submittal.cannot.be.before.client.activation.date`):

```
ctrl-p9-1m2-2026-c2   sha 713a3560…   p1 21600.00   total 144988.47
ctrl-p9-1m2-2024-c2   sha ff92fc5d…   p1 21600.00   total 144988.47
money-cell diffs 2026 vs 2024: 0
```

**The start year is inert on this shape**, so **the closure stands** — ICPM does move
nothing here. Only the claim of control was overstated. Fix in §7.

Also worth recording, and the `_note` does not say it: the two observations differ in the
**seam** as well (`path_a_embeddable` vs `path_b_server`). That difference is not
eliminable — it is the point of the comparison — but "the only remaining difference" reads
as though it were.

**Scope of the closure is correctly stated everywhere else.** "On this shape only",
"licenses nothing about a daily interest calculation", "does not reopen B-01..B-04" — all
present, and `B-01..B-04` really are still refused for their own reasons. T149 recorded the
amendment by **appending** to `t76/PROMOTION-DECISION.md` rather than editing T76's verdict
[VERIFIED: the diff is `@@ -105,3 +105,41 @@`, pure append]. That is the right move and I
want it noticed.

---

## 3. (c) The three red/green arms — reproduced, two of the three transcripts byte-identically

There is no `.softhouse/prove-redgreen.sh`; the driver is
`.softhouse/capture/pathb/t149/prove-redgreen.sh`. Re-run by me with `bash`, on the P-24
scratch merge, **exit 0**:

```
=== arm 1 — 42-vector store + M7 (the premise) ===
| `MONEY-QUANTIZATION-HALF-EVEN` (M7) | **KILLED** | 39 | 3 | T61-HE-A, T61-HE-B, T61-HE-C |
=== arm 2 — 43-vector store + M7 (RED) ===
| `MONEY-QUANTIZATION-HALF-EVEN` (M7) | **KILLED** | 39 | 4 | T149-PATHB-TIE, T61-HE-A, T61-HE-B, T61-HE-C |
=== arm 3 — 43-vector store, unmutated (GREEN) ===
    parity vectors          PASS 43   FAIL 0
VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5664 cells compared.
conformance exit=0
```

**All three arms reproduce exactly.** [VERIFIED: `t153/verify/redgreen-three-arms-rerun.txt`]

Stronger than "reproduce": after the re-run, `git status` showed
`premise-refuted-42-vector-store.txt` and `red-M7-43-vector-store.txt` **unmodified** — they
regenerated byte-for-byte — and the only diff in `green-conformance-43-vectors.txt` was the
worktree path on the `store` line. **`git status` on `nexus/` was empty**: the M7 mutation
reverted, nothing under `nexus/` is committed mutated.

I read the mutation rather than trusting its name. `M7` replaces
`roundHalfUpToInt(shifted).Int64()` in `rounding.go` with an explicit banker's-rounding
`QuoRem` + `Lsh(rem,1).Cmp(den)` + `quo.Bit(0)` block [VERIFIED:
`.softhouse/handoff/T61-mutations.py:136-152`]. It is genuine HALF_EVEN at the currency
quantization, not a stand-in.

The driver **asserts** — `'| 39 | 3 |'`, `'| 39 | 4 |'`, the killed-by list,
`'parity vectors          PASS 43   FAIL 0'`, `rc = 0` — and `fail()`s naming the arm
otherwise. It is not a proof that prints numbers and compares none.

**One residual risk in the rig, not a defect today.** Arm 1 parks the vector with `mv` and
restores it with a second `mv` before asserting anything. If the process is killed between
the two, the store is silently one vector short and the file sits at
`t149/.parked-vector.json` — **outside** `STORE_ROOT`, so no store guard fires and the next
conformance run reports a green `PASS 42` rather than an error. A `trap … EXIT` restore
would close it. Not raised as a finding against this promotion — the file is restored and
the store is intact, which I verified — but a later task touching this script should add
the trap.

---

## 4. (d) The `note` — it is TRUE, including the sentence T149 refused to write

The brief required the vector's note to say *"a port inheriting HALF_EVEN fails this vector
and passes every other one in the corpus."* **That sentence is false and T149 did not write
it.** Checked, claim by claim, against what it wrote instead:

| claim in `_note` | verdict |
|---|---|
| *"the first clause is true of the literal CHARACTERS 20925.05 and 20925.04"* | **TRUE** — `git grep -E "20925\.0[45]\|2092505\|2092504" main -- .softhouse/vectors/` returns **nothing**. |
| *"IT IS THE FOURTH VECTOR IN THIS STORE TO KILL THAT COUNTERFACTUAL, NOT THE FIRST"* | **TRUE** — `T61-HE-A/B/C` all carry `graded_against: MONEY-QUANTIZATION-HALF-EVEN` at margins **6, 4, 5** minor units on principals 1,000,541.50 / 1,000,052.50 / 1,000,089.50 [VERIFIED: the three vector files], and arm 1 above shows the 42-vector store already killing `M7`. |
| *"MEASURED BEFORE THIS VECTOR EXISTED: … parity PASS 39 FAIL 3, the three being exactly T61-HE-A/B/C"* | **TRUE** — reproduced, §3. |
| *"Every other parity vector in this store is path_a_embeddable"* | **TRUE** — census of `main`'s store: 46 files = **42 parity, all `path_a_embeddable`** + 4 `contract-refusal` [VERIFIED]. |
| *"MARGIN: … every one of them by exactly 1 minor unit, so the widest single-cell disagreement is 1"* | **TRUE** — my own arm diff over a wider cell set than T149's finds **23** diverging cells and the set of distinct \|delta\| is exactly `{1}`. (T149 counts **20** because its cell set omits `totalDueForPeriod`, `totalOutstandingForPeriod` and `totalActualCostOfLoanForPeriod`. Cell-set-dependent, not wrong; the load-bearing half — *all* deltas are 1 — holds.) |
| *"to_jsonb(m_product_loan) id 10 @ fineract_default against id 11 @ fineract_gerege, 89 columns compared, 1 differing, and the differing column is `id`"* | **TRUE** — re-run by me from the rows: **89 columns, 1 differing, `id` (10 vs 11)** [VERIFIED]. |
| *"(g) POST /loans?command=calculateLoanSchedule persists nothing"* | **TRUE** — `count(*) from m_loan` on `fineract_gerege` read 4 immediately before and 4 immediately after a re-post [VERIFIED]. |
| *"(f) request.time_zone is Asia/Ulaanbaatar and is OBSERVED"* | **TRUE** — `tenants.timezone_id` = `Asia/Ulaanbaatar` for `gerege` [VERIFIED]. |

**The one claim that does not hold as written:**

> *"both arms are observations of the reference oracle taken from ONE running JVM **differing
> in exactly one input**, the tenant's RoundingMode ordinal"*

`c_configuration` differs between the two tenants in **exactly one row** — `rounding-mode`
`6` vs `4` — and I verified that by diffing all **74** rows of both
[VERIFIED: full `c_configuration` diff, a single `71c71` hunk]. But the **`tenants` row**
differs in
`timezone_id` as well: **`Asia/Kolkata` on `default`, `Asia/Ulaanbaatar` on `gerege`**
(plus `name`, `id`, `oltp_id`, `report_id`, `created_date`) [VERIFIED]. So "the two tenants
differ in exactly one input" is not true; "they differ in exactly one **`c_configuration`**
input" is.

Whether the zone is inert here is **[UNVERIFIED]** — testing it would mean writing a tenant
row on the shared oracle, which I will not do. It is very likely inert (every date in the
request is explicit and the response carries no zone-dependent field), but "very likely" is
not a measurement and this file does not get to say it is one.

**This does not weaken the vector's grading power at all**, and that is the point worth
making: the vector's discrimination is established by the **M7 mutation** against the Go
port (§3), which does not depend on the two-tenant counterfactual in any way. The two-arm
observation is the *provenance* story, not the *grader*. Fix in §7.

### The pattern is already banked, correctly

`P-13` in `.softhouse/patterns.md:1160` — *"Grepping the store for a VALUE does not answer
what the store KILLS"* — is already on `main` and states the refutation accurately,
including that the count was never wrong and the inference was. Nothing to correct there.

---

## 5. (e) `nexus/` and the frozen contract — untouched, byte-identical

* `git diff --stat main...softhouse/T149-halfup-tie-vector -- nexus/` → **empty**.
* Tree object for `nexus/` is **`2b0f089a64adecb9a8999a93487523ede764e9c0` on both** `main`
  and the branch — byte-identical, not merely "no diff shown".
* `contract.go` blob is **`4bcbafaddd6014650375a315d346dbba284d5bb5` on both**.
* `dec1_revision` is **12** in `capabilities.json` and in the new vector; nothing in the
  33-file diff touches `contract.go`, `PIN.json`, `capabilities.json`, `gates.md`,
  `conformance.sh`, `attest_gate.py` or `preconditions.sh`.
* On the merged tree: `go build ./...` **rc 0**, `go test ./...` **all ok** (loanschedule
  7.8 s, conformance 24.9 s), `gofmt -l nexus` names **exactly**
  `nexus/internal/apps/loanschedule/contract/contract.go` — the **expected** state under
  gate **G-3**. I did not run `gofmt -w` on anything.

The only non-evidence source change in the whole branch is
`.softhouse/capture/pathb/t36/attest.py`, and it is additive: `CAPTURE_SETS` is a dict,
`PRODUCT_IDS` is `(1,2,3,4)` for both pre-existing sets — **behaviour-preserving** — and an
unknown set now `_abort`s where it previously fell through silently to `EMILOOP_CAPTURES`.
That is a latent bug closed, not introduced. `_abort` is defined at `:69`, used at `:152`
[VERIFIED]. Registering the set in the shared rig instead of forking a private
`t149/attest.py` is the right call under P-21.

**No-float discipline:** every new script reads money with `parse_float=str`
(`promote-vector.py:151,153`, `compare-arms.py:50,52,68,69`, `capture-halfeven-arm.sh:67`)
and scales major→minor by integer/string arithmetic. `guard_no_float_in_vectors` passed on
the merged store.

---

## 6. (f) P-24 scratch merge into **current** `main` — clean, and still PASS

`main` advanced past T149's fork point while this review ran: `82d31ee` → **`9308679`**
(`c5f0087`, `d3bf714`, `3a564c8`, `9308679`), touching only `.softhouse/gates.md`,
`program.json` and `tasks.json` — **nothing** under `.softhouse/vectors/`,
`.softhouse/capture/` or `nexus/` [VERIFIED: `git diff --stat`]. So T149's §8.5 P-24 claim
was made against an older `main` than the one it will merge into, and I re-tested it
against the current one.

`git checkout -b scratch/t153-p24 main` + `git merge --no-ff softhouse/T149-halfup-tie-vector`
→ **merges clean, no conflicts.** `main` itself was never touched. Then
`bash .softhouse/conformance.sh` (never `sh`):

**Probe line PRESENCE first — it is present, line 1 of the transcript, and line 6 of the
summary. Verbatim:**

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```
```
    oracle probe    UP
```

**Parity count: `parity vectors          PASS 43   FAIL 0`** — 42 → 43, and the new vector
is graded, not skipped:

```
T149-PATHB-TIE               parity           path_b_s... PASS             88        3
```

**Exit code: `0`.**
**Invariant violations: `0`.** And `invariant assertions    0 NOT RUN` — the third withdrawn
cell (`from_date` on the disbursement row) did **not** silence any assertion; the harness's
own line reads *"NONE — every invariant assertion ran, on cells somebody actually observed."*

Summary block, verbatim:

```
--- SUMMARY ---
    parity vectors          PASS 43   FAIL 0
    contract-refusal        PASS 4    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    self-test fixtures      PASS 1    FAIL 0   (hand-authored; EXCLUDED from the parity count)
    refused                 0   (no discriminating vector / seam blind — not a pass, not a failure)
    inadmissible            0
    harness errors          0
    cells compared          5664 graded, 87 ungraded (never recorded by the capture)
    kills named             103 money, 7 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0
    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)

VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5664 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

`bash .softhouse/conformance.sh --prove` → **`PROOFS: 21 passed, 0 failed`**, exit 0.

[VERIFIED: `t153/verify/p24-scratch-merge-conformance.txt`,
`t153/verify/conformance-prove-selftest.txt`]

The scratch branch was **deleted**; nothing was merged to `main`; `main` is where it was.

I also checked the harness does not special-case the new seam: `path_b_server` appears in
the Go tree **only** in `conformance_test.go` admissibility cases, never in the grading
engine — the seam reaches grading only as data through `capabilities.json`. A Path B vector
is graded by the same code path as a Path A one, which is why arm 2 can take it red.

---

## 7. The micro-fix — 4 lines of prose, no number, no money logic

Two sentences claim a control the evidence does not have. Both conclusions are correct and
I measured the gaps myself; only the wording needs to match what was actually held fixed.

**(i) `T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json`, `graded_against[0].evidence`** —
replace

> `two tenants differing in exactly one input -- the RoundingMode ordinal in c_configuration (gerege 4 = HALF_UP, default 6 = HALF_EVEN)`

with

> `two tenants differing in exactly one c_configuration input -- the RoundingMode ordinal (gerege 4 = HALF_UP, default 6 = HALF_EVEN); the tenants row also differs in timezone_id (Asia/Ulaanbaatar vs Asia/Kolkata), not measured here because the port-side M7 proof does not rest on this arm`

**(ii) the same file's `_note`, clause (b), and the identical sentence in
`crosscheck-vs-patha.py`'s printed RESULT and in the `t76/PROMOTION-DECISION.md`
amendment** — replace

> `With the day count controlled, ICPM is the only remaining difference and it moves nothing.`

with

> `With the day count controlled, ICPM is the only remaining CONTRACT input that differs; the schedule start year differs too (Path A 2024-01-01, Path B 2026-01-01) and T153 measured it inert on this shape -- 0 money-cell differences, t153/out/t153-ctrl-p9-1m2-{2026,2024}-c2-raw.json. Neither moves anything here.`

Mechanical, prose only, changes no number, no money logic, no `nexus/` byte, and does not
touch the `expect` block or any graded cell. Conformance cannot move: `_note`,
`graded_against[].evidence` and a script's stdout are not graded — but the fix should be
re-run through `bash .softhouse/conformance.sh` anyway, because "cannot move" is a
prediction and this pipeline grades predictions.

---

## 8. What I checked and found nothing wrong with

So silence is distinguishable from not looking:

* every `expect` cell against my own capture — **0 mismatches**, 13 rows, and every
  withdrawn cell genuinely absent from the response;
* the whole 12-period schedule re-derived in exact rationals — **12 of 12 + total**;
* the three red/green arms — **all three reproduce**, two transcripts byte-identically;
* `M7`'s source — genuine banker's rounding at the quantization site;
* `nexus/` tree hash, `contract.go` blob hash, `dec1_revision`, `go build`, `go test`,
  `gofmt -l` (G-3 expected state);
* the `attest.py` diff — additive, behaviour-preserving for `pathb`/`emiloop`, `_abort`
  defined before use;
* `parse_float=str` in every new script that touches money;
* the `vectors/README.md` edits — counts (43/4/1 = 48 files), cell totals (5,664 / 87),
  `--prove` (21/0), the Path B disbursement field list, "42 of the 43 withdraw exactly
  those two cells" (census: **0 exceptions**), "two counterfactuals contain no model";
* `capabilities.json` — seam `exercised`, capability `in_graded_domain: true`,
  `dec1_revision` 12;
* the HALF_EVEN arm's quarantine — `NOT-PRODUCTION-REPRESENTATIVE.txt`,
  `CAPTURED-FROM-TENANT: default`, no attestation;
* `t76/PROMOTION-DECISION.md` — pure append, T76's verdict not edited;
* the oracle's state — no container touched, no row written, `m_loan` count unchanged.

## 9. `[UNVERIFIED]` — what I could not establish

1. **Whether the two tenants' differing `timezone_id` is inert.** Testing it means writing
   a tenant row on the shared oracle. Not done, not guessed. The vector's grading power does
   not depend on it (§3).
2. **Whether `T149-PATHB-TIE` is precision-sensitive** (`MATHCONTEXT-PRECISION-12`). Not
   measured by T149 and not by me; `vectors/README.md` correctly counts it on neither side.
3. **`interestCalculationPeriodMethod` in general.** Closed on this shape only. I did not
   test a daily interest calculation, where the setting is live. T149's scoping is right and
   I am not widening it.
4. **Charges, holidays, working-day adjustment, multi-tranche on Path B.** None captured by
   T149, none by me. The seam is open; it is not surveyed.
5. **T149's source reading of `ProgressiveEMICalculator.addDisbursement:127-132`** as the
   only reader of ICPM on this path — I did not re-audit the call graph. The *behavioural*
   measurement stands on its own and does not need it.
6. **Cutover.** Untouched by this review. `VERDICT: PASS` means "matches the reference
   oracle on captured vectors, within the graded domain" and never "safe to cut over" — a
   hard `user` gate.

---

## 10. Bottom line

The plan-gate rule-1 violation was the driver's, not T149's, and the remedy was exactly
right: hold the promotion out of the graded corpus until an independent reviewer re-derives
it. **It survives that.** The vector is exact, it is genuinely admissible under T76's four
tests, it discriminates a real counterfactual under a real mutation, and it is the store's
first evidence that the Go port reproduces a **live server** response — 88 graded cells,
exact, on the seam a production deployment actually uses.

The two overstatements are worth fixing precisely **because** the vector is otherwise this
solid: a `_note` that claims a tighter control than it holds is the same failure mode T149
was commended for refusing, one layer down. Apply §7 and merge.

**MICRO-FIX → then APPROVED.**
