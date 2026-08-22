# T219 — handoff

**Task:** T116's third follow-up. Determine **by measurement against the live reference oracle**
whether T159's `MNT 10.01 at n = 3000` residual figure is still correct, and whether T116's promoted
vectors sit where G-8's prose says the region is.

**Branch:** `softhouse/T219-g8-residual-measurement`
**Pre-registration commit:** `741c6483a5b4785490c44da38e323019a4faa17d`
**Capture commit:** `6eacc067ec891cb20fe385a9965bb2331e17973d`
**gates.md edit commit:** `ff9b1a1934cd3faef142341b9a010d5bb4b2d755`
`git merge-base --is-ancestor 741c648 6eacc06` → **exit 0.**

**Fork point — a discrepancy the driver should note.** The dispatch brief said the fork point is
`8611e754`. `git rev-parse HEAD` in this worktree at start was
**`2d41838cdbbe5332bd62deb5cdec9f52f3df91f3`**, and `git merge-base HEAD main` returned the same —
i.e. HEAD was `main`'s tip, the BAR commit. **T219 never saw `8611e754` and cannot say what it is.**
Every "measured at" stamp below is against `2d41838` (P-69).

---

## 1. VERDICT

**The figure is a CORRECT MEASUREMENT whose stated domain names the WRONG VARIABLE, and it is
SUPERSEDED AS THE RECORD by T219's own measurement at the same term.**

Both halves matter and neither is the other:

- **T159's measurement is not superseded.** T219 re-asked `T159-R600p0-N3000-B1001` under a new
  tenant id and got 1001 minor units unamortized, 3000 of 3000 REPAYMENT rows at `principal 0.00`,
  `totalInterestAmount 15010.01` — T159's committed value to the minor unit. It was the control and
  it reproduced.
- **The figure's domain was wrong.** G-8 insisted, in bold, that the residual be *"stated with its
  term, always"*, and every restatement obeyed. The residual of an unrescued family-B cell is
  `min(B_minor, n·δ)` — **a function of the PRINCIPAL, capped by `n·δ`.** T117 and T159 topped out at
  principals of 501 and 1001 minor units. At n = 3000 with δ = 1 the cap is **3000 minor units**, and
  T159 used one third of it.

**So the record moved without a larger term being asked:**

| figure | was | **is** | cell |
|---|---|---|---|
| largest unamortized residual | MNT 10.01 at n = 3000 | **MNT 30.00, still at n = 3000** | `T219-R600p0-N3000-B3001` and `-B4499` |
| largest **FULL** family-B residual | MNT 10.01 | **MNT 29.99** | `T219-R600p0-N3000-B2999` |
| largest failing **disbursement** | 1001 minor (MNT 10.01) | **4499 minor (MNT 44.99)** | `T219-R600p0-N3000-B4499` |

**Which measurement supersedes which:** T219 supersedes **T159** as the holder of the residual record
and the largest-failing-principal record, and supersedes **T231's** sentence *"They are NOT the
largest residual on record; that is still MNT 10.01 at n = 3000"*. It supersedes **no measurement**:
T117's MNT 5.01, T159's MNT 10.01 and T229's MNT 2.99 are each still exactly what those workers
observed. **What is falsified is the causal prose** — *"each time because somebody asked a larger
term"* and *"the residual doubled when the term tripled"*.

**The MNT 0.23 / MNT 2.91 / MNT 5.01 figures were NOT touched.** Each is correct over its named
domain, exactly as T223 left them.

---

## 2. Pre-registered prediction

`.softhouse/capture/t219-g8-residual/PREDICTION.md` + `prediction.json`, committed at
**`741c6483`**. Predictions came from **T229's committed `site3.py`, unmodified**; nothing was fitted
to any cell. Falsification conditions **F1–F4** were stated in advance, as was what T219 would do
with each outcome, including *"if the figure is right, name the domain and do not edit it."*

**F2 was registered as the likeliest single refutation** (`B2999` sits at `B/n = 0.9997`, the same
neighbourhood where `T229-R600p0-N200-B199` refuted at 0.995). **F2 did not fire.** The cell that
refuted was `B1999`, which was not the one flagged.

---

## 3. Measurement transcript

Live reference oracle (Fineract), 2026-08-22. Pinned image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`; pinned checkout
`/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, **`git status --porcelain` = 0
lines**; seam sha `bf397f0b29e6…` byte-identical to the pinned file; `ThrewOutcome.java`
`de816eb33044…`; calibration reference `capture-prod3g-raw.json` `6e0c37019095…`. Path A embeddable
seam in a throw-away `docker run --rm`. **`(19, HALF_UP)`**, MNT dp 2, tenant ids all new (`t219_*`),
emission order scrambled. Rig built from T229's `CaptureT229.java` by `src/make_harness_t219.py`,
which replaces only the probe-cell block and the class name.

**Both rig calibrations reproduced** `T64-ZP-A` / `T64-ZP-B` — `inputs` identical, `observed`
identical under a canonical dump (`sort_keys=True`, `separators=(',',':')`), in every run.

### Run 1 — default `-Xss`, every cell asked EXACTLY ONE TIME

```
cell                       n     B     E_obs  δ  a  observed              repaid       RESIDUAL   totInterest
T219-R600p0-N103-B1        103   1     1      0  0  clean (last row only) 1 of 1       0          13
T219-R600p0-N104-B1        104   1     0      1  0  FAMILY B FULL         0 of 1       1          1
T219-R600p0-N108-B1        108   1     0      1  0  FAMILY B FULL         0 of 1       1          1
T219-R600p0-N3000-B1001    3000  1001  500    1  0  FAMILY B FULL         0 of 1001    1001       1501001
T219-R600p0-N3000-B2999    3000  2999  1499   1  1  FAMILY B FULL         0 of 2999    2999       4499999
T219-R600p0-N3000-B3001    3000  3001  1500   1  1  FAMILY B PARTIAL      1 of 3001    3000       4503000
T219-R600p0-N3000-B4499    3000  4499  2249   1  1  FAMILY B PARTIAL      1499 of 4499 3000       6750000
T219-R600p0-N3000-B4501    3000  4501  —      —  —  THREW StackOverflowError
T219-R600p0-N3000-B1999    3000  1999  —      —  —  THREW StackOverflowError
```

All money in **integer minor units**. `E_obs` is the observed row-1 total and equals the emulated
`E` on all 7 observed cells. `totInterest` matches `n·E + B − principal` on all 7.

### Run 2 — the two throwing cells re-asked after 50 T177 warm-up calls

**Both threw again.** 50 warm-up cells (ZP-A shape, n = 56), 0 threw. **T177 measured that recipe at
3/3 on the (B = 10001, n = 3000) cell and it did not generalise here.** T177's warm-up cell was at
n = 200 and T219's at n = 56; whether the warm-up must be deep in `n` is `[UNVERIFIED — T219 did not
vary it, and this is one run against T177's, not a refutation of T177]`.

### Run 3 — the two throwing cells under `-Xss16m` (T177 measured 8m/16m observe 2/2 from cold)

```
T219-R600p0-N3000-B4501    amortizes fully, 4501 of 4501, 19 non-zero principal rows (rows 1..19), E_obs 2252
T219-R600p0-N3000-B1999    amortizes fully, 1999 of 1999, 19 non-zero principal rows (rows 1..19), E_obs 1000
```

`-Xss` is **not a production setting** and no parity claim rests on it. **Every residual figure in
this handoff and in G-8 comes from run 1, at default flags.** Run 3's money is used for exactly two
statements: that `B4501` amortizes, and that `B1999` amortizes.

**Runs 2 and 3 are second and third asks of two cells and are declared as such.** Nothing observed in
run 1 was re-asked, revised or replaced.

### Score: 8 of 9 as registered, 1 REFUTED

**`T219-R600p0-N3000-B1999`** was registered FAMILY B FULL and amortizes. The emulator supplied
`E = 999` → `δ = 1`, `a = 1`, `a > δ` false, no rescue. Observed row-1 total is **1000 = I₁q**. **This
is T229's gap 1 at a third cell**, alongside `T229-R600p0-N200-B199` and `T229-R36p0-N1400-B1450`.
**T219 refuses the circular move** of recomputing `δ` from the observed post-rescue row and declaring
the law vindicated — row 1 of a rescued cell is POST-rescue, and no instrument in this program
observes the pre-rescue instalment. `[UNVERIFIED — whether the pre-rescue E for B1999 was 999 or
1000.]`

**What the refutation does not touch:** `B2999`, one cell away at the same `a = 1`, came back FULL
with `E = 1499` exactly as emulated. The record-moving cells do not stand on the input that failed.

---

## 4. The domain, named

The correct domain statement for T159's figure, which G-8 now carries:

> **Over the union that includes T117's and T159's captures — and ONLY over the principals those two
> captures asked, the largest of which is 1001 minor units — the largest unamortized residual is
> MNT 10.01 at n = 3000.**

And the general form, which is what should be quoted going forward:

> The unamortized residual of an unrescued family-B cell is **`min(B_minor, n·δ)`**. The term is the
> **cap**, not the variable. Any residual figure must state **the principals asked**, not only the
> term.

---

## 5. Do the promoted vectors sit where G-8's prose says the region is? — YES, RE-OBSERVED LIVE

| vector | shape | cells compared | diffs |
|---|---|---|---|
| `T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct` | n = 103, **no exemption** | **729** | **0** |
| `T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct` | n = 104, 2 exemptions | **736** | **0** |
| `T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct` | n = 108, 2 exemptions | **764** | **0** |

**The comparator was calibrated on a known negative before it was believed (P-72), and it needed to
be.** The raw capture and the vector do **not** share field names — capture: `type` / `principal` /
`interest` / `balance` as decimal strings; vector: `kind` / `principal_minor` / `interest_minor` /
`outstanding_principal_minor` as integer minor units. **T219's FIRST comparator matched by name,
compared ZERO cells and printed "REPRODUCED" on all three.** The committed version
(`src/check_promoted_t219.py`) asserts, before reporting anything, that a deliberate one-minor-unit
corruption of the last row's interest raises a diff. It also normalises exactly one encoding
difference — the DISBURSEMENT row's absent `total`, which the vector encodes as JSON `null` and the
capture as a missing key — and that normalisation fires only when **both** sides are the absent
marker.

The predicate also accounts for all three without being asked to: n = 103 → `E = 1 = I₁q`, `δ = 0`,
last row carries the whole principal; n = 104 and n = 108 → `E = 0`, `I₁q = 1`, `δ = 1`,
`B_minor = 1 ≤ n·δ` — FULL family B. `.softhouse/vectors` was **read only** and is byte-unchanged.

---

## 6. Second finding: the `(δ + ½)·n` ceiling is now measured at a SECOND term

T229 landed the rescue boundary within one minor unit at n = 200 (`299` family B, `301` amortizes;
law says `1.5·n = 300`). **T219 repeated it at n = 3000**: law says `1.5·n = 4500`, observed
**`4499` family B and `4501` amortizes.** Two boundaries an order of magnitude apart, each registered
in an ancestor commit, each landing within one minor unit.

**This STRENGTHENS the conservative superset `B_minor < 1.5·n` and does NOT prove it.** It says
nothing about `δ ≤ 1`. **T219 registered in advance that it chose no cell to hunt for `δ ≥ 2`**, so
its 8 observations of `δ ∈ {0, 1}` are **not** evidence for the conjecture and are not offered as
any. **Options (b) and (c) still must not be put to Buyan**, and T219 makes no recommendation on
either.

---

## 7. What I changed in `.softhouse/gates.md`

All inside the **G-8 section** plus its row in the file's top summary table. Nothing else in the file
was touched.

1. **New subsection** *THE RESIDUAL RECORD, RE-MEASURED* after *SITE 3, CHARACTERISED*.
2. **Summary table row for G-8** (line 30).
3. **Task roster** — T219 added, with what it did.
4. **"wider in the largest failing principal"** 1001 → **4499 minor units**, with the superseding
   note and the warning that "largest failing principal" and "largest unamortized residual" stopped
   being the same number when T229 measured a PARTIAL cell.
5. **"Whether it terminates"** — the causal half struck by measurement.
6. **The main residual bullet** in *The bound on the failing principal* — domain qualifier added;
   *"the residual doubled when the term tripled"* struck; *"MNT 10.01 is the largest OBSERVED"*
   updated.
7. **"the practical reading"** — largest failing disbursement 1001 → 4499 minor; the margin restated
   as ≈ 22,000× and explicitly attributed to the **mechanism** argument rather than the sweep.
8. **T231's *"that is still MNT 10.01 at n = 3000"*** — corrected.
9. **Census counts** — 26 → **29** distinct principals; the family A/B comparison table's 600.0 % row
   212 → **215** cells and `principals 1 … 1001` → `1 … 4499`; total 216 → **219**.
10. **THE THIRD OUTCOME block** — the "MNT 10.01 residual" definite description scoped to T159's cell.
11. **SITE 3 gaps** — gap 1's "wrong on 2 of 9" → 3 cells across two probes; gap 3's probe-cell count.
12. **The Buyan ceiling paragraph** and **T229's boundary sentence** — the n = 3000 confirmation.
13. **The sub-ulp warning** — MNT 10.01 → MNT 30.00.
14. **STANDING RULE — a SEVENTH mechanism**, and the preamble count six → seven.
15. **Non-decision roster** — T219 added.

### The seventh mechanism, because it is the transferable part

The first six failure modes were: family inversion; a float in an analysis script; an unscoped
"largest n"; a stale `tasks.json` disposition; **a sentence with no scope**; and **a predicate with
an unmeasured input**. T219's is none of them:

> **A sentence WITH a scope, whose scope is on the wrong axis.** `MNT 10.01 at n = 3000` obeyed every
> remedy the section had already adopted — it was stated with its term, always, in bold, and every
> restatement complied. It was still wrong, because nobody asked *"is the term the variable this
> number is a function of?"*, and the section's own law, two screens away, already answered no.
>
> **The clause: when you attach a domain to a measurement, name the variable the measurement is a
> FUNCTION of, not the variable you happened to vary.** And the test that catches it: **try to beat
> the record with the labelled variable held FIXED.** If you can, the label was wrong.

---

## 8. BAR, observed on this branch at `ff9b1a1`

- oracle probe line **PRESENT**, reading **`up`** / `UP`
- **`VERDICT: PASS (exit 0)`**
- **46** parity vectors PASS / 0 FAIL, **7884** cells
- **0** inadmissible, **0** harness errors, **0** invariant violations
- **4 EXEMPTED BY A VECTOR** / **4 GROUNDED** / **0 UNGROUNDED** / **0 UNDETERMINED-ON-THE-RECORD**
- `--prove`: **23 `PROOF OK`, 0 failures**, exit 0
- `go build ./...` exit 0 · `go vet ./...` exit 0 · `go test -count=1 ./...` ok (all packages)
- `gofmt -l .` → exactly `internal/apps/loanschedule/contract/contract.go` (1 file, G-3; never
  `gofmt -w`)
- `git rev-parse HEAD:.softhouse/vectors` = **`73c3ea7b43dd75f04884072719a87fc8e1d255c1`** —
  **UNCHANGED BY T219**

Re-run after the `gates.md` edits: identical.

---

## 9. Gaps I leave behind — and what I did NOT look at (P-40)

**Not looked at at all** (so the T228 concept sweep must not be narrowed by this handoff):

- **Every gate other than G-8.** T219 opened no other section of `gates.md` and read no other gate.
- **`.softhouse/patterns.md`** — read for P-26 / P-40 / P-66/70 / P-67 / P-69 / P-72 only. **T219
  proposed no new pattern**, though the seventh mechanism above is pattern-shaped and the driver may
  want it as one.
- **The `## G-8-NOTICE` block** (from line ~3238) — read, and **deliberately NOT edited.** It carries
  `MNT 10.01 at n = 3000` in at least five places including a *"Any disclosure of G-8 must state the
  residual WITH ITS TERM"* instruction. Its own header says **SUPERSEDED — historical record; the
  LIVE G-8 section is above**, so those figures are a record of what was said then, which is the
  treatment T231 applied. **A reviewer who disagrees should treat this as a live decision, not an
  oversight.**
- **`nexus/`, the harness, `.softhouse/vectors/`, `.softhouse/conformance.sh`** — not edited. Go code
  was built/vetted/tested only.
- **T229's `site3.py`** — used unmodified as an oracle for predictions; **not edited** (see the
  defect below).

**Open, and named:**

1. **`T219-R600p0-N3000-B1999`'s pre-rescue `E` is unknown** (999 or 1000). Gap 1 now has three
   cells. `[UNVERIFIED]`
2. **The Go port is not graded on any T219 cell.** `B3001` and `B4499` are **PARTIAL**, the shape on
   which "the port agrees with the oracle" has never been checked at all. **The three record-moving
   cells are therefore NOT option-(a) candidates on today's evidence.** `[UNVERIFIED]`
3. **`n·δ` as the residual cap was measured at n = 3000 and at no other term.** Whether the cap is
   `n·δ` elsewhere is `[UNVERIFIED]` by T219.
4. **One rate only — 600.0 %.** T219 is not evidence about 36.0 %, 300.0 % or any unswept rate, and
   asked nothing at n = 200, so it says nothing about the largest failing disbursement at a short
   term.
5. **Nothing above n = 3000 has still been asked**, by anyone.
6. **`δ ≥ 2` was not hunted.** Registered in advance. The conjecture is exactly as unproven as it was.
7. **T177's 50-call warm-up recipe did not reproduce on these two cells.** One run, one warm-up shape
   (n = 56 vs T177's n = 200). Not a refutation of T177 and not offered as one. `[UNVERIFIED]`
8. **A defect in T229's committed rig, found and NOT fixed** (out of T219's scope):
   `.softhouse/capture/t229-g8-site3/src/site3.py`'s docstring and its `predictedTotalInterestMinor`
   field both assert *"TOTAL INTEREST = n*E + B for any unrescued cell"*. **False on a PARTIAL cell:**
   `B3001` observed `4503000` against `n·E + B = 4503001`; `B4499` observed `6750000` against
   `6751499`. The correct form is `n·E + B − principal`, which **`gates.md` already states** in the
   T231 re-derivation and which matches all four T219 cells exactly. **It affects no verdict here**
   — the classifier compares principal and outcome, not that field. **Someone should fix `site3.py`
   or annotate it**, because the next worker will read that docstring as the law.
9. **T219 did not re-open the Fineract source.** Every source citation in *SITE 3, CHARACTERISED*
   remains T229's, `[UNVERIFIED by T219]`.
10. **STANDING RULE 1** asks for a full sentence-by-sentence scope-table rebuild before editing.
    **T219 did not do a 117-row rebuild.** It did a declared **concept sweep** (rule 3) with
    `git grep -n -P` (PCRE2 — `-E` is unusable here, T232; calibrated first on the known positive
    `\bMNT 10\.01\b`, 18 hits) over `MNT 10\.01`, `1001 minor`, `MNT 5\.01`,
    `largest.{0,60}residual` and `largest failing (principal|disbursement)`, and dispositioned every
    hit. **That is narrower than rule 1 asks for and is declared as such.**

---

## 10. Grep engine, for anyone reproducing the sweep

`grep` on PATH is **ugrep 7.5.0** (`+neon/AArch64`, `-P:pcre2jit`). `git grep -E` reads `\b` as a
literal `b` here and returns **zero silently** (T232); every sweep above used **`git grep -n -P`**
and was calibrated on a known positive first.
