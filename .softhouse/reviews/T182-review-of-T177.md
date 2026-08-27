# T182 — independent review of T177: what the StackOverflowError work ESTABLISHED, and what it only RE-OBSERVED

Task `T182`, run `2026-08-21-run2-tierA-gl-accounting-A2`, branch `softhouse/T182-review-t177`.
Worktree `/Users/buv/gerege-nbfi/.claude/worktrees/agent-a97674ad61c4da58d`. Reviewing
`softhouse/T177-stackoverflow-nondeterminism` (commit `a570296`, already merged into `main` — so
`git diff main...softhouse/T177-…` is **empty** and the reviewable diff is `dfa1bfa..a570296`; noted
because P-41's three-dot rule silently yields nothing once the branch has landed).

I did not plan or perform T177's work. "The oracle" throughout means the **Fineract reference
implementation**; Oracle Database is prohibited in this program and was not used. **PostgreSQL is
the only permitted database and no database was opened by this review.** No server was started; the
running `fineract-*` containers were not touched.

---

## The distinction this review exists to draw

T177's measurements are real, its raw evidence is complete, and every number I re-derived from the
committed bytes matches. What I checked is whether the **causal** sentence it is being used to
support — *"JIT compilation state, not input, determines the throw"* — is **established** by those
measurements or merely **consistent** with them. The answer is split, and the split matters, because
one half of it has already propagated verbatim into `gates.md`.

---

## Claim-by-claim: ESTABLISHED / RE-OBSERVED / OVERSTATED

### 1. "From a cold JVM the disputed cell throws every time" — **ESTABLISHED**

Re-derived by me from the committed raw stdout with a script that deliberately does **not** import
`analyze_t177.py` or `lib/sweep_integrity`, so the agreement is not circular
(`.softhouse/reviews/T182-evidence/t182_independent_tally.py`):

```
processes with a header: 75 ; trials: 348 ; probe trials: 139
COLD START (seq==0), keyed by (cell, EXACT jvm flags):
   T177-CELL-R600p0-N2000-B10001      flags=(none)                       observed=0   threw=9
   T177-CELL-R600p0-N3000-B1001       flags=(none)                       observed=9   threw=0
   T177-PROBE-R600p0-N3000-B10001     flags=(none)                       observed=0   threw=32
   T177-PROBE-R600p0-N3000-B10001     flags=-XX:MaxJavaStackTraceDepth=0 observed=0   threw=1
```

`[VERIFIED]` 75 processes, 348 trials, 139 probes — T177's denominators are exact. Plus my own two
fresh JVMs below. The negative arm exists and fired the other way (`headline-cold` 9/9 observed), so
this is not a guard that cannot fail (P-22).

**One disclosure gap.** T177's "**33** cold starts, default `-Xss`, C2 on" is **32** JVMs at
genuinely default flags **plus one** carrying `-XX:MaxJavaStackTraceDepth=0`. The flags column in
`ANALYSIS-ALL.txt` says "default `-Xss` … C2 on", which is true of that JVM but conceals that it was
not a default-flag process. Immaterial to the claim — a trace-recording cap cannot change whether a
throw happens — but it is a pooled denominator presented as a homogeneous one.

### 2. The within-JVM step at attempt 5 — **ESTABLISHED as a step; the number 5 is RE-OBSERVED**

My independent tally:

```
  disputed-cell JVMs (C2 on) with >4 attempts: flip exactly at attempt 5 = 7, other = 0
  processes whose probe string is LITERALLY "XXXXoooo" (any cell, any flags) = 6
```

**7 of 7 flip at attempt 5 and none reverses — confirmed.** T177's *phrasing* is loose in two ways
that a reader will take literally:

* the literal string `XXXXoooo` appears in **6** processes, only **5** of which are the disputed
  cell (`repeat-warm` ×4, `thread-repeat` ×1); the sixth is `red-warm`, a *different* cell. The other
  two of the seven printed `XXXXoo` (`depth-uncapped`, 6 attempts) and `XXXXo` (`pilot-repeat`, 5
  attempts) — they are shorter plans, not different behaviour;
* the review doc calls them "7 of 7 independent **default-flag** JVMs", but one of the seven carries
  `-XX:MaxJavaStackTraceDepth=0`. Six are default-flag.

The **substance** (a step, at the same index, never reversing) holds 7/7 and I reproduced it. The
**string** claim is 5/7. T177's §2(a) enumerates the seven honestly; only the headline compresses.

**Is 5 stable, or one warm-up path?** All seven are the same cell, same image, same host, same
ambient load. T177 marks "attempt 5 vs a compilation threshold attempt 5 crosses" `[UNVERIFIED]`,
which is the correct call. **What T177 left on the table is that its own committed data brackets the
threshold**, with no new oracle time:

| condition | prior *inner-period* iterations before the probe | probe outcome |
|---|---|---|
| `warm-ctrl-1` | 1 × 200 = 200 | threw 0/3 observed |
| `warm-ctrl-10` | 10 × 200 = 2,000 | threw 0/3 observed |
| `warm-ctrl-50` | 50 × 200 = 10,000 | **observed 3/3** |
| `repeat:*` attempts 1–4 | 4 × 3,000 = 12,000 | **observed from attempt 5** |

The two flipping conditions both sit at ≈10–12k prior iterations; the two non-flipping ones at 200
and 2,000. The threshold therefore lies between 2,000 and 10,000 — **bracketing the measured
`Tier4InvocationThreshold = 5000`** `[VERIFIED: out/jvm-defaults.txt]`. This is a genuinely
*establishing* argument for the C2 attribution and it is derivable from T177's committed bytes.
`[INFERENCE by T182 — it assumes the hot method is invoked ~once per repayment period; I did not
instrument the invocation counters, so it is corroboration, not proof.]`

### 3. "`-XX:TieredStopAtLevel=1` proves the warming agent is the optimising compiler" — **RE-OBSERVED, on n = 1 JVM; I raised it to n = 3**

This is the weakest link in T177 and it carries the paper's causal sentence.

**What else that flag changes.** `TieredStopAtLevel=1` is not a single-variable control. It changes,
at minimum: the compilation tier reached (C1 only, no C2); therefore inlining depth; therefore
compiled frame size; therefore the number of Java frames a fixed stack holds; and the run's speed
(a flat ~6.1 s per attempt against ~11–15 s for a default-JIT throw — i.e. C1-only reaches overflow
**faster**, which is what a *larger* frame predicts). It does **not** disable interpreter profiling,
code-cache warming, data-cache warming, or GC state, so it *does* discriminate the C2 hypothesis
from the generic "repetition warms something" hypothesis. That discrimination is real and is the
control's actual value.

**What it does not do** is isolate *which* of the tier / inlining / frame-size changes is decisive.
T177 says exactly this and marks the mechanism `[UNVERIFIED]` — correctly. So the honest statement
is **"the transition requires C2"**, not "C2's frame-size reduction is the mechanism". T177's
headline says the first; its section title (d) *"The optimising compiler (C2) is the warming agent"*
edges toward the second, and the review doc then pulls it back explicitly ("asserts no mechanism").
Net: honestly scoped, if the reader reaches the qualifier.

**Sample size.** T177's `c1only` is **one** JVM. A single process is one draw from whatever else
varies on a loaded 10-CPU host, and "**never** happens at all" is a universal written over n = 1.
I re-ran it in **two further fresh JVMs: both `XXXXXXXX`, 16/16 threw, 0 observed**, flat elapsed
6024–6103 ms — matching T177's 6105–6157 ms. **The control now stands at 3 JVMs / 24 attempts /
24 throws.** So the claim is no longer *re-observed on one draw*; the replication is what promotes
it. `[VERIFIED by T182, `.softhouse/reviews/T182-evidence/out-t182/raw/t182-c1only-{0,1}.stdout`]`

### 4. "The throwing region is not a region of the input space" — **OVERSTATED, and contradicted by T177's own data**

This is my principal finding.

T177 shows that the **two B = 10001 cells** (n = 2000 and n = 3000) behave *identically* under
matched JVM state — both throw cold, both answer from attempt 5. That legitimately refutes the
specific premise G-8 rested on, namely *"(B=10001, n=2000) dies while (B=10001, n=3000) succeeds"*.
**That refutation stands and I confirm it.**

It does **not** support the general sentence T177 draws from it, and which T170 has already copied
into `gates.md`:

> *"Therefore 'the throwing region' is not a region of the input space at all. Any sentence whose
> premise is a boundary in (B, n) is refuted at the premise."*

T177's own headline table falsifies that. **At one fixed JVM state — cold, first seam call, default
`-Xss`, C2 on — the outcome is a function of the inputs and of nothing else:**

| cell, same rate, same n = 3000, same cold state | cold JVMs | observed | threw |
|---|---|---|---|
| B = 1001 minor units | 9 | **9** | 0 |
| B = 10001 minor units | 33 | 0 | **33** |

That is a boundary in the input space, exhibited at a stated JVM state, with a denominator, in
T177's own evidence. The correct claim is: **the throw is a function of (inputs × JVM state), and no
boundary is meaningful unless the JVM state is fixed and stated.** T177 *writes* that correct
formulation — in follow-up 1 — and then contradicts it in Impact §1:

> *"any design that asks each cell **once** is measuring where the sweep's own warm-up curve crossed
> that cell"*

A cold-start-per-cell probe asks each cell exactly once and is the design T177 itself recommends as
maximally reproducible. The sentence needs "**once inside a shared JVM**". As written, the two
sections of the same document disagree.

**Consequence for the driver:** T159's follow-up 5 ("bound the throwing region") should be
**re-scoped, not cancelled**. T177's own data already contains two points of a cold-start boundary.

### 5. "`errorStackDepthTotal: 1024` is HotSpot's recording cap, not a depth" — **ESTABLISHED**, and by a stronger argument than T177 gives

`errorStackDepthTotal` is emitted as `t.getStackTrace().length`
[`.softhouse/capture/lib/ThrewOutcome.java:121,128`]. HotSpot truncates the backtrace it records at
throw time to `MaxJavaStackTraceDepth`, whose default is **1024** — and that default is not assumed
here, it is read out of the pinned image itself:

```
     intx MaxJavaStackTraceDepth                   = 1024                                      {product} {default}
```
`[VERIFIED: out/jvm-defaults.txt]`

T177's argument is "we lifted the cap and saw >1024". Mine is stronger and needs no extra run — from
my independent grouping of every throw by exact flags:

```
   flags=-Xss512k                         distinct depths=[1024]
   flags=-Xss4m                           distinct depths=[1024]
   flags=-XX:MaxJavaStackTraceDepth=0     distinct depths=[4683, 5119, 8400]
```

**An 8× change in thread stack size cannot leave the true depth at overflow bit-identical.** A
recorded value that is invariant at exactly 1024 across a 512k→4m stack sweep, and only ever differs
when the cap flag is lifted, is a cap. `[VERIFIED by T182 from the committed raw.]` The
reinterpretation is a **measurement**, not an inference, and every capture in this program that
carries a flat 1024 must be read that way.

### 6. "The true depth at overflow RISES as compilation proceeds" — **NOT ESTABLISHED; the series is not monotone**

The series, which I re-read from the raw bytes myself
(`out/matrixC/raw/depth-uncapped-0.stdout`):

```
"errorStackDepthTotal": 5119
"errorStackDepthTotal": 4683
"errorStackDepthTotal": 4683
"errorStackDepthTotal": 8400
```

5119 → 4683 is a **fall of 8.5 %**, then flat, then a jump. The word "rises" is wrong for this
series, and it appears in T177's handoff, in T177's review doc, in the commit message, and — copied
— in `gates.md` ("the true depth reached at overflow **rises** as compilation proceeds — 5119, 4683,
4683, then 8400"). The review doc's own prose then compares **8400 vs 4683** ("~1.8× deeper") rather
than 8400 vs the first attempt's 5119 (1.64×), which is the pairing that makes the rise look clean.

What the data supports: **the true depth at overflow VARIES within a single JVM on identical inputs,
by a factor of ~1.8 between its extremes, and always exceeds the 1024 recording cap.** That alone
carries the argument — depth on fixed inputs is not a constant, therefore the throw is not a
property of the inputs. n = **1 JVM, 4 data points**. No second JVM was run at `MaxJavaStackTraceDepth=0`.

### 7. "T159 and T169 never disagreed about the oracle" — **ESTABLISHED for the disputed cell**

I re-extracted T159's committed capture myself, independently of T177's `t159_context.py`
(`.softhouse/reviews/T182-evidence/t182_t159check.py`):

```
n cases 49
errored 2 ['T159-R600p0-N2000-B10001', 'T159-R600p0-N3000-B100001']
T159-R600p0-N3000-B1001  error= None {'totalDisbursedAmount': '10.01', 'totalPrincipalAmount': '0.00', 'totalInterestAmount': '15010.01'}
T159-R600p0-N3000-B10001 error= None {'totalDisbursedAmount': '100.01', 'totalPrincipalAmount': '100.01', 'totalInterestAmount': '846.70'}
T159-R600p0-N2000-B10001 error= java.lang.StackOverflowError: null {...None...}
index of disputed: 26
index of red: 2
```

`[VERIFIED]` Exactly the two cells T177 names threw in T159; the replay reproduced exactly those two
and matched 22 others digit for digit. The reconciliation holds.

**One numbering slip.** T177 describes the pair as "sweep cell **#1** vs **#27**". With the two
calibration cases at positions 0–1, the red cell is **sweep #1 / overall #3** and the disputed cell
is **sweep #25 / overall #27** — T177's own `matrix-c.txt` says "the **24** sweep cells that
preceded" it, i.e. sweep #25. The two figures are on different numbering bases. Cosmetic; no
conclusion moves.

### 8. "When the oracle answers at all, it answers with the same number" — **ESTABLISHED within warm state; across cold-vs-warm it rests on ONE cell**

Verified: every observed trial of every cell in T177's corpus carries a single distinct
`totalInterestAmount` **and** `totalPrincipalAmount`, all money emitted as JSON **strings**, never
floats, every trial at `precision=19 roundingMode=HALF_UP` ambient and explicit
`[VERIFIED by T182's independent tally and by re-running `check_claims_t177.py`: 9 claims, 0 FAILED].`

The scope limit T177 does not state: **the disputed cell has no cold observation at all** — it
throws 33/33 cold, so all 31 of its observations are warm. The only cell observed in *both* states is
the headline cell B = 1001 (9 cold + 7 warm, `15010.01` on all 16). So "the money does not depend on
JVM state" is measured across the cold/warm boundary on **one cell**. Highly plausible — JIT is not
permitted to change `BigDecimal` results — but it is n = 1 cell, not 107 trials.

---

## My own reproduction — my numbers next to T177's

Ran T177's committed `run-t177b.sh` unmodified, my own matrix
(`.softhouse/reviews/T182-evidence/t182-matrix.txt`), fresh JVMs, same pinned image
`sha256:e596339626bf…0459a`, same pinned Fineract `426a23544` (clean), same seam sha
`bf397f0b…0714`. Output written to `/tmp` only; **no byte under `.softhouse/capture/` was
modified** — `shasum -c MANIFEST.sha256` passes on all **196** files before and after.

| condition | T177 | **T182 (mine)** | agree? |
|---|---|---|---|
| headline cell B=1001, n=3000, **cold**, default flags | 9 JVMs → 9 observed, 0 threw; `totalInterestAmount 15010.01`, `totalPrincipalAmount 0.00` | **4 JVMs → 4 observed, 0 threw; `15010.01` / `0.00` on all 4** | **yes** |
| disputed cell B=10001, n=3000, **cold**, default flags | 32 default-flag JVMs → 0 observed, 32 threw, `errorStackDepthTotal 1024` | **2 JVMs → 0 observed, 2 threw, `errorStackDepthTotal 1024`** | **yes** |
| disputed cell, `repeat:6` in one JVM | step at attempt 5, `XXXXoo` | **`XXXXoo` — threw, threw, threw, threw, observed, observed; elapsed 11926, 11266, 11239, 13177, 82165, …** | **yes** |
| disputed cell, `-XX:TieredStopAtLevel=1`, `repeat:8` | **1 JVM** → 8/8 threw, flat ~6.1 s | **2 further JVMs → `XXXXXXXX` and `XXXXXXXX`, 16/16 threw, 0 observed; elapsed 6143/6080/6058/6081/6083/6084/6089/6062 and 6094/6065/6050/6072/6024/6050/6103/6042 ms** | **yes** |

My raw evidence: `.softhouse/reviews/T182-evidence/out-t182/` — 9 java processes, 28 seam calls,
all exit 0, all stderr empty, all footers printed; `attestation.json` records the same image id,
pinned commit, seam sha and both harness shas as T177's runs.

**T177's headline reproduces on every condition I tested.**

* **The cold-safety of G-8's headline cell — the one claim on which a money result depends —
  reproduced on the first attempt, 4/4, in JVMs T177 never ran, at `0.00` principal against `10.01`
  disbursed and `15010.01` interest every time.**
* **The step at attempt 5 reproduced exactly** (`XXXXoo`), with the same signature elapsed jump
  (11.9/11.3/11.2/13.2 s throwing → 82.2/82.4 s observing).
* **The `TieredStopAtLevel=1` control, T177's weakest link at n = 1, survived independent
  replication and is now n = 3 JVMs, 24 attempts, 24 throws, 0 observations** — with the flat
  ~6.1 s elapsed reproduced to within 100 ms of T177's. The **causal attribution to C2 is
  substantially better supported after this review than before it**, which is the outcome I was
  least expecting; I record it as readily as I would have recorded a failure to reproduce.
* Pooling my 8 disputed-cell attempts across >4-attempt JVMs with T177's, the step-at-5 count is
  now **8 of 8 JVMs, 0 exceptions.**

---

## Does this touch G-8's MONEY claim at all?

**No. Not one digit of it.** Being precise, because the task brief says a lot rests on this:

* **G-8's money claim** is that the reference oracle emits a schedule that does not amortize the
  principal — family B: `totalPrincipalAmount` `0.00` (FULL) or short of the disbursement (PARTIAL).
  Its headline instance is `T159-R600p0-N3000-B1001`: **MNT 10.01 disbursed, `0.00` principal
  repaid, `15010.01` interest.**
* **T177's finding is entirely about WHETHER the oracle answers**, never about WHAT it answers. Its
  own money check (24 comparisons, 0 mismatches) and my independent re-derivation both show a single
  distinct value per cell across every observation.
* **T177 strengthens G-8's headline rather than touching it.** The headline cell is observed **9/9
  from cold** in T177 and **4/4 from cold** in my re-run, at `0.00` principal against `10.01`
  disbursed every time. That is the family-B FULL shape, reproduced from the most reproducible JVM
  state there is.
* **T177's corpus independently re-exhibits family B on five further cells** — `B=503, n=1000`
  (`0.00` / `2515.03`), `B=501, n=2000` (`0.00` / `5005.01`), `B=1` at n ∈ {360, 361, 364, 389,
  1200, 2000, 3000} (`0.00`), and the PARTIAL shape at `B=999, n=2000` (`1.66` against `9.99`
  disbursed) — all matching T159's committed values `[VERIFIED by T182's independent tally]`.
* **The sentence T177 refutes is not a money sentence.** *"It is not monotone: (B=10001, n=2000)
  dies while (B=10001, n=3000) succeeds"* is a claim about the **throw**, inside G-8's THIRD-OUTCOME
  block. Refuting it changes what may be said about crashes. **It changes nothing about
  amortization.**
* **And the disputed cell was never a family-B cell.** `T159-R600p0-N3000-B10001` amortizes fully —
  `totalPrincipalAmount 100.01` against `100.01` disbursed `[VERIFIED by T182 from T159's committed
  `.gz`]`. Neither is `B=10001, n=2000`: when T177 finally got it to answer, principal was `100.01`
  against `100.01`, full amortization `[VERIFIED by T182's tally]`. **Both cells in the refuted
  sentence are family-A-shaped, fully-amortizing cells.** So the refutation cannot reach family B
  even by accident.

**T177's correction of its own brief is right, and I verified it end to end**: MNT 10.01 is
B = 1001, not B = 10001; the driver's brief conflated two ids differing by one digit; T177 refused
the premise and probed the real cell. That is the single most valuable thing in the task.

**The one thing G-8 does lose:** the *evidence* for "cannot be excluded by bounding the inputs" in
the third-outcome block. The conclusion may still be true — nobody has tested it — but it no longer
rests on the two-cell comparison. T177 says exactly this.

---

## `errorStackDepthTotal`: cap or depth — my derivation

1. The field is `Throwable.getStackTrace().length` at the catch site
   [`.softhouse/capture/lib/ThrewOutcome.java:121,128`] `[VERIFIED by reading the source]`.
2. HotSpot fills the backtrace at construction and truncates it at `MaxJavaStackTraceDepth`.
3. That flag's value **in the pinned image** is `1024 {product} {default}`, read from the image's own
   `-XX:+PrintFlagsFinal` dump, not from documentation `[VERIFIED: out/jvm-defaults.txt]`.
4. Across **every** default-and-`-Xss` series — 512k, 1m, 2m, 4m, and the JVM default 2040k — the
   recorded value is **exactly 1024, with zero variance**, over ~72 throws. An 8× change in stack
   size cannot leave the true overflow depth unchanged to the frame.
5. With `-XX:MaxJavaStackTraceDepth=0` the same rig records 4683 / 5119 / 8400.

(1)–(5) settle it: **1024 is the cap.** Follow-up 5 of T177 ("any future rig that cares about depth
must set `-XX:MaxJavaStackTraceDepth=0`") is correct and should reach `patterns.md`.

What is **not** settled: the *uncapped* series' shape (see claim 6), and whether the depth reported
for a throw at 512k versus 4m differs at all — that was never measured, only capped away.

---

## Sample sizes per headline

| headline | trials | **independent JVMs** | rests on |
|---|---|---|---|
| cold start always throws (disputed cell) | 33 | 33 (32 default-flag + 1) | broad |
| cold start always answers (headline cell B=1001) | 9 | 9 | **n = 9**, + my 4 |
| step at attempt 5, never reverses | 46 probe trials | **7** | **n = 7** |
| warm-up need not be the same cell (50 prior calls flip it) | 9 | 9 (3 per arm) | **n = 3 per arm** |
| `-Xss` moves it (8m/16m observe, ≤4m throws) | 12 | 2 **per stack size** | **n = 2 per point** |
| **"never happens under `TieredStopAtLevel=1`"** | 8 | **1** | **n = 1 JVM in T177 → n = 3 / 24 attempts after my replication** |
| **true depth 5119/4683/4683/8400** | 4 | **1** | **n = 1 JVM, 4 points** |
| money invariant across cold vs warm | 16 | 9 cold + 1 warm | **n = 1 cell** |

T177 discloses every one of these denominators in its per-series table — **nothing is hidden**. But
three headline sentences are written in universal form ("**never** happens", "the depth **rises**",
"the throwing region is **not** a region of the input space") on top of n = 1, n = 1 and a two-cell
comparison respectively, and two of the three have already been copied into `gates.md` in that
universal form.

---

## What I checked and found clean

* **DEC-1 unchanged**, before and after my work:
  `49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab  docs/adr/DEC-1-schedule-generator-adapter.md`
  **contract.go unchanged**:
  `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139  nexus/internal/apps/loanschedule/contract/contract.go`
  Both match the expected prefixes `49dc8923…` / `0db73d4a…`. **No contract change; no `user` gate crossed.**
* **`MANIFEST.sha256` verifies — all 196 files, 0 failures**, before and after my re-run. My run
  wrote only to `/tmp/t177probe/out/t182/`.
* **T177's diff scope is clean**: `.softhouse/capture/t177-so-nondeterminism/**`,
  `.softhouse/reviews/T177-…md`, and its own handoff. It touched **no** `gates.md`, `patterns.md`,
  `tasks.json`, `program.json`, no vector, no Go source, no other worker's handoff.
* **No money-math defect.** No float anywhere: every money field is a JSON **string**; the harness
  carries no floating-point literal; all money is built from integer minor units via
  `new BigDecimal(int).movePointLeft(2)`. Re-verified mechanically —
  `check_claims_t177.py` → *"emitted money fields that are JSON floats rather than strings: got 0"*.
* **Production `MathContext`.** All 348 trials ran at `precision=19 roundingMode=HALF_UP`, both
  ambient and explicit — 0 exceptions. This corpus is at the ratified tenant setting.
* **P-35 (zero-inspected is an ERROR)** is honoured in `analyze_t177.py`, `calibrate_t177.py` and
  `check_claims_t177.py`; my own tally script exits non-zero on zero trials read for the same reason.
* **P-22 (a control that cannot fail)** — the design has both arms: `warm-ctrl-1`/`-10` are the
  negative arm and threw; `headline-cold` is the falsifier for "everything throws cold" and observed.
  The instrument can go both ways and did.
* **P-46 quote check** re-run by me: *"5 fenced line(s) checked, 0 not found in any committed
  transcript"*, exit 0. Every fenced transcript line in T177's prose exists byte-for-byte in
  committed evidence.
* **Catch discipline**: `lib/ThrewOutcome.isFatal()` re-throws `VirtualMachineError` other than
  `StackOverflowError`; both harnesses catch `Throwable`; `check_no_narrow_catch.py` reports
  `0 NEW`. A throw cannot be silently reclassified as an observation.
* **P-40 accounting**: 348 asked / 348 emitted / 0 never reached; 0 non-zero exits; 0 bytes of
  stderr; every process printed a footer. I re-checked footers independently — none missing.
* **Calibration before conclusion**: `T64-ZP-A`/`T64-ZP-B` reproduced, 131 totals and period rows
  compared, 0 differ.
* **No prohibited database.** No Oracle Database artefact, no MySQL/MariaDB driver, no port 1521,
  anywhere in T177's diff or in my re-run. No database was opened at all.

---

## Unverified

* **Which of C2's effects is decisive** (frame size vs inlining vs tier). Neither T177 nor I read
  compiled frame sizes or used `-XX:+PrintCompilation`. `[UNVERIFIED]`
* **My ≈10,000-iteration bracket** for the warm-up threshold assumes the hot method is invoked
  roughly once per repayment period. I did not instrument the counters. `[INFERENCE, not measured]`
* **Whether the cold-start boundary in (B, n) is well-behaved** beyond the two points T177's own data
  supplies. I did not sweep it. `[NOT MEASURED]`
* **Whether de-optimisation can flip an observed cell back to throwing.** Not seen in T177's 139
  trials or my 16; no run was long enough to force one. `[UNVERIFIED]`
* **Whether other committed captures (T83, T84, T100, T117) are affected.** Not re-run by T177 or by
  me. `[NOT RE-RUN]`
* **Server-mode Fineract under HTTP load.** Nothing here transfers. `[NOT MEASURED]`
* **I did not re-run T177's matrix A under the B runner**, so I inherit T177's own disclosed gap:
  the two runners' equivalence rests on reading the diff, not on a controlled A/B. I did read
  `build_harness_t177b.py`'s `verify_pair()` and `ANALYSIS-harness-pair.txt` (22 added / 1 removed,
  all inside allowed hunks) and found nothing wrong, but that is a reading, not an execution.
  `[UNVERIFIED by execution]`
