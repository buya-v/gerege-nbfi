# T177 — the reference oracle's `StackOverflowError` is a function of JVM STATE, not of the cell

Task `T177`, run `2026-08-21-run2-tierA-gl-accounting-A2`, branch
`softhouse/T177-stackoverflow-nondeterminism`. Gate **G-8**.

Reference oracle (Fineract) pinned checkout `/Users/buv/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, tree clean; image `fineract:latest` =
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`; seam
`EmbeddableProgressiveLoanScheduleGenerator.java` sha256
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — all re-verified inside the
runner before every one of the four matrices. **No database was opened and no server started**; the
running `fineract-*` containers were not touched. "The oracle" means the Fineract reference
implementation throughout; Oracle Database is prohibited in this program and appears nowhere here.

**T177 promotes nothing, grades nothing, and changed no gate, vector, task or handoff outside its
own.** It changes the *measurement*, not the *measured*.

---

## Headline

**The throw is not per-request noise, and it is not a property of the cell. It is a property of how
much optimising JIT compilation the JVM has done when the cell is asked.**

The disputed cell — **B = 10001 minor units, n = 3000, annual rate 600.0**, the one T159 observed
cleanly and T169 saw throw — was asked **107 times** (of **139** probe trials over all cells) across
**75 java processes**. Every count below is machine-derived by `analyze_t177.py`, not hand
arithmetic:

**COLD START** — the probe is the JVM's *very first* seam call, default `-Xss`, C2 on:

| cell | JVMs | observed | threw `StackOverflowError` |
|---|---|---|---|
| **the disputed cell** (B = 10001, n = 3000) | **33** | **0** | **33** |
| T159's detonation (B = 10001, n = 2000) | 9 | 0 | 9 |
| **G-8's headline cell** (B = 1001, n = 3000) | 9 | **9** | 0 |

**BY ATTEMPT NUMBER inside one JVM**, disputed cell, default `-Xss`, C2 on:

| attempt | JVMs | observed | threw |
|---|---|---|---|
| 1 | 43 | 4 † | 39 |
| 2 | 7 | 0 | 7 |
| 3 | 7 | 0 | 7 |
| 4 | 7 | 0 | 7 |
| **5** | **7** | **7** | **0** |
| 6 | 6 | 6 | 0 |
| 7 | 5 | 5 | 0 |
| 8 | 5 | 5 | 0 |

† the four attempt-1 observations are the three `warm-ctrl-50` JVMs and the one `t159prefix` JVM —
i.e. the disputed cell's first attempt, in a process that had already made 50 (or 24) seam calls on
*other* cells. **"Attempt 1" is not the same as "cold", and that gap is the whole finding.**

`[VERIFIED: out/ANALYSIS-ALL.txt "COLD START" and "ATTEMPT-INDEX TALLY" blocks; raw per-process
stdout under out/*/raw/]`

The transition inside a JVM is a **step function at exactly the same place in 7 of 7 independent
default-flag JVMs that asked the cell more than four times** — `XXXXoooo` — never a coin flip:

```
  matrixA   repeat-warm        run 0   seq0=0   XXXXoooo      elapsedMs: 14443,13848,13900,15975,91618,91745,91814,91779
  matrixA   repeat-warm        run 1   seq0=0   XXXXoooo      elapsedMs: 14366,13638,13623,15701,98934,98768,99187,98634
  matrixA   repeat-warm        run 2   seq0=0   XXXXoooo      elapsedMs: 11610,11151,11120,12911,90124,90026,89967,89543
  matrixA   repeat-warm        run 3   seq0=0   XXXXoooo      elapsedMs: 13682,13357,13421,15658,96991,96821,97199,96807
```
`[VERIFIED: out/ANALYSIS-matrixA.txt, extracted verbatim]`

---

## 1. Requirement 2 — the exact disputed cell, re-run, with the denominator

`fresh-single`: **20 fresh JVMs, 20 asked, 0 observed, 20 threw `java.lang.StackOverflowError`,
0 other.** Counting every cold start of this cell at the default stack size with C2 on — the 20,
plus the pilot's 3, plus 3 on a freshly spawned thread, plus the first attempt of each multi-attempt
JVM — the tally is **33 cold starts, 33 throws, 0 observations**
`[VERIFIED: out/ANALYSIS-ALL.txt "COLD START" block]`.

So the "intermittency" T169 reported is **not** per-request randomness. **From a cold JVM this cell
throws every time.** T159's clean observation was not luck; it was position.

## 2. What the outcome IS a function of — four things, each measured

### (a) Position in the JVM — the number of prior seam calls

`repeat:8` in 4 fresh JVMs, `thread:0:8` in 1, `repeat:6` in 1, `repeat:5` in the pilot: **7 of 7
JVMs flip from threw to observed at attempt 5 and never flip back.** In 107 trials of this cell no
`observed` was ever followed by a `threw` in the same process. `[VERIFIED: out/ANALYSIS-matrixA.txt,
out/ANALYSIS-matrixB.txt, out/ANALYSIS-matrixC.txt, out/ANALYSIS-pilot.txt]`

### (b) The warming does NOT have to be the disputed cell — but it has to be enough of it

A *different*, never-throwing cell (same principal, **n = 200**) run before the probe:

| warm calls on the n = 200 cell | JVMs | probe observed | probe threw |
|---|---|---|---|
| 1 | 3 | 0 | 3 |
| 10 | 3 | 0 | 3 |
| **50** | **3** | **3** | **0** |

`[VERIFIED: out/ANALYSIS-matrixA.txt, series warm-ctrl-1 / warm-ctrl-10 / warm-ctrl-50]`

So it is generic warm-up of the shared code path, not anything about the disputed inputs. Four
attempts at n = 3000 and fifty attempts at n = 200 buy the same thing.

### (c) Thread stack size, with the inputs held fixed

The disputed cell as the **first** seam call of a cold JVM, 2 fresh JVMs per stack size:

| `-Xss` | observed | threw |
|---|---|---|
| 512k | 0 | 2 |
| 1m | 0 | 2 |
| 2m | 0 | 2 |
| 4m | 0 | 2 |
| **8m** | **2** | **0** |
| **16m** | **2** | **0** |

`[VERIFIED: out/ANALYSIS-matrixB.txt]` The JVM's own measured default is
`ThreadStackSize = 2040` (KB ≈ 1.99 MB) on `OpenJDK 21.0.11 Zulu21.50+19-CA`
`[VERIFIED: out/jvm-defaults.txt]`. **A cell whose outcome moves with `-Xss` is not a cell whose
outcome is a property of its inputs.**

### (d) The optimising compiler (C2) is the warming agent

With C2 switched off — `-XX:TieredStopAtLevel=1` — the transition **never happens**:

```
  matrixC   c1only             run 0   seq0=0   XXXXXXXX      elapsedMs: 6157,6123,6115,6116,6129,6105,6117,6116
```
`[VERIFIED: out/ANALYSIS-matrixC.txt, extracted verbatim]` 8 attempts, 8 throws, and a flat elapsed
time — no warm-up at all.

And the **true depth reached at overflow varies within a single JVM as compilation proceeds, and
always exceeds the 1024 cap** — it does not rise monotonically; see the series below, where attempt 2
falls below attempt 1 [T182 micro-fix]. With HotSpot's 1024-frame
recording cap lifted (`-XX:MaxJavaStackTraceDepth=0`):

| attempt | outcome | true frames at overflow |
|---|---|---|
| 1 | threw | 5119 |
| 2 | threw | 4683 |
| 3 | threw | 4683 |
| 4 | threw | **8400** |
| 5 | **observed** | — |
| 6 | **observed** | — |

`[VERIFIED: out/matrixC/raw/depth-uncapped-0.stdout, tabulated in out/ANALYSIS-matrixC.txt]`
The same recursion goes **~1.8× deeper** (8400 vs 4683 frames) on the fourth attempt than on the
second, in the same JVM, on the same inputs; on the fifth it fits. Smaller compiled frames replacing
interpreted ones would explain that, and it is the standard explanation, but **T177 measured frame
depth, not frame size, and asserts no mechanism** — see "Hypotheses the data CANNOT separate".
**Every `errorStackDepthTotal` of exactly `1024` in this program's captures is HotSpot's recording
cap, not a depth.**

## 3. The direct reconciliation of T159 against T169

`matrix-c.txt` replays **T159's committed case list in T159's committed order** — the 24 sweep cells
that preceded `T159-R600p0-N3000-B10001` — under T177's own tenant ids, and then asks the disputed
cell.

* The prefix reproduces T159 **cell for cell**: the **only** two cells that threw are
  `N2000-B10001` (T159's 1st sweep cell) and `N3000-B100001` (T159's 5th) — exactly the two that
  threw in T159's committed capture — and **all 22 other cells match T159's committed
  `totalInterestAmount` digit for digit**, by extraction.
* The disputed cell, asked at position 25, is **observed, `846.70`** — T159's committed value.

`[VERIFIED: out/ANALYSIS-matrixC.txt money-check block, 24 comparisons, 0 mismatches;
out/matrixC/raw/t159prefix-0.stdout]`

**T159 and T169 did not disagree about the oracle. They asked the same cell at different points in a
JVM's warm-up curve, and the rig had no field in which to record that.**

## 4. The "throwing region" is not a region of the input space ALONE — it is a region of (inputs × JVM state)

*[T182 micro-fix: qualifier added. At one FIXED cold state this rig's own headline table shows
B = 1001 observed 9/9 and B = 10001 threw 33/33 at the same n — an input boundary. What is refuted
is a boundary asserted across UNEQUAL JVM states, which is what G-8 cited.]*

`T159-R600p0-N2000-B10001` — T159's detonation, the cell G-8's write-up cites as proof the throw is
"not monotone in n" — behaves exactly like the disputed cell:

* **cold start: 9 JVMs, 9 throws, 0 observations** (8 `red-cold` + the first attempt of `red-warm`);
* **warm: `XXXXoooo` in one JVM** (`red-warm`) — and from attempt 5 it returns
  `totalInterestAmount 776.46`.

`[VERIFIED: out/ANALYSIS-matrixB.txt, out/ANALYSIS-matrixC.txt]`

**T159 could never obtain a value for that cell; T177 obtained one four times.** So the pair
"(B=10001, n=2000) dies while (B=10001, n=3000) succeeds", which G-8 currently cites as evidence of
non-monotonicity in the inputs, is **an artefact of the two cells' positions in T159's run** — the
first was T159's sweep cell #1 and the second its #27. Under equal JVM state both throw (cold) and
both answer (warm).

**`776.46` is an OBSERVATION, not a vector.** It is recorded here so it is not lost; it must not be
promoted, and it is not comparable to any committed capture because no committed capture holds a
value for that cell.

## 5. A correction to the brief's premise, recorded rather than smoothed

The T177 brief states that the disputed cell `(B = 10001 minor units, n = 3000)` "is the cell behind
G-8's headline **MNT 10.01 residual at n=3000**." **It is not.** By extraction from the committed
T159 capture `[VERIFIED: out/ANALYSIS-t159-context.txt]`:

| cell | disbursed | totalPrincipalAmount | totalInterestAmount |
|---|---|---|---|
| `T159-R600p0-N3000-B10001` — the **disputed** cell | `100.01` | `100.01` | `846.70` |
| `T159-R600p0-N3000-B1001` — the **headline** cell | `10.01` | **`0.00`** | `15010.01` |

The MNT 10.01 residual belongs to **B = 1001 minor units**, not B = 10001. The disputed cell
amortizes fully and is not a family-B cell at all.

**This matters, and the news is good.** T177 asked the *actual* headline cell from **9 cold starts**
(8 `headline-cold` JVMs plus the first attempt of `headline-warm`): **9 observed, 0 threw**, and
`totalInterestAmount 15010.01` on **all 16** of its observations, matching T159's committed value by
extraction. `[VERIFIED: out/ANALYSIS-ALL.txt "COLD START" block and money block]` **G-8's headline
number is reproducible from a cold JVM and is not at risk from this defect.** T177 does not edit
G-8; T170 folds this in.

## 6. What the rig did, and what it counted

* **139 probe trials**, **348 seam calls** in total, across **75 java processes** and 4 matrices.
* **0 seam calls never reached**, **0 non-zero java exits**, **0 bytes of stderr on any process**,
  every process printed its footer. `[VERIFIED: out/ANALYSIS-ALL.txt P-40 block]`
* **0 trials errored for a reason unrelated to the throw.** There were none to classify — which is
  itself reported rather than assumed.
* **Calibration**: `CaptureT177` reproduces pass 3g's `T64-ZP-A` / `T64-ZP-B` — **131 totals and
  period rows compared, 0 differ** `[VERIFIED: out/ANALYSIS-calibration.txt]`.
* **Money**: **24 comparisons against committed T159 values, 0 mismatches**; the disputed cell
  returned `846.70` on **all 31** of its observations. When the oracle answers, it answers the same
  number. `[VERIFIED: out/ANALYSIS-ALL.txt money block]`
* T169's shared `lib/ThrewOutcome.java` and `lib/sweep_integrity.cell_outcome()` do the throw
  recording and the classification — not a local re-implementation. `check_no_narrow_catch.py` is
  clean with both new harnesses present: `67 total, 67 in FROZEN files (34 files), 0 NEW`
  `[VERIFIED: out/ANALYSIS-lint-no-narrow-catch.txt]`.

---

## Hypotheses the data CANNOT separate

* **The precise mechanism inside C2.** Frame-size reduction by compilation is *consistent* with every
  measurement (deeper true depth as attempts proceed; no transition with C2 off; `-Xss` moving the
  boundary), but T177 did **not** read compiled frame sizes, did not use `-XX:+PrintCompilation`, and
  does not assert which methods' compilation is decisive. `[UNVERIFIED]`
* **Whether the transition is at "attempt 5" or at a compilation threshold that attempt 5 happens to
  cross.** The measured default `Tier3InvocationThreshold = 200` / `Tier4InvocationThreshold = 5000`
  `[VERIFIED: out/jvm-defaults.txt]` are consistent with a counter-driven threshold, but T177 did not
  instrument the counters. The number **5** is a property of *this cell at n = 3000 on this image*,
  not a constant. `[UNVERIFIED as a general rule]`
* **Where the exact `-Xss` boundary lies.** Measured only that 4m throws and 8m observes, 2 JVMs each.
  The boundary between them was not bisected. `[UNVERIFIED]`
* **Whether de-optimisation can flip an observed cell back to throwing.** Never seen — no `o` was
  followed by an `X` in 139 trials — but no run was long enough or varied enough to force a
  de-optimisation. `[UNVERIFIED]`
* **Thread/connection dependence in the HTTP sense.** This seam is called **in-process**; there is no
  connection and no request. T177 varied *thread identity* (a fresh thread per probe) and found the
  transition unchanged, so the state is JVM-wide, not per-thread. Nothing here says anything about a
  *server-mode* Fineract under concurrent HTTP load. `[NOT MEASURED]`
* **Heap, GC state and container CPU count as factors.** Held constant, never varied.
  `nproc = 10`, cgroup `memory.max = max` `[VERIFIED: out/jvm-defaults.txt]`. `[UNVERIFIED]`
* **Whether any OTHER committed capture in this program is affected.** T177 re-asked only the cells
  named above plus T159's 24-cell prefix. It did **not** re-run T83, T84, T100 or T117.
  `[NOT RE-RUN]`
