# T219 — PRE-REGISTERED PREDICTION, G-8, the "MNT 10.01 at n = 3000" residual figure

**Registered BEFORE any cell was asked of the reference oracle.** This file and
`prediction.json` are committed in an ancestor of the commit that carries the capture, and the
driver may verify it with `git merge-base --is-ancestor <this commit> <capture commit>` (P-9).

The oracle here is the **Fineract reference implementation** at pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`. **Oracle Database is a prohibited product in this
program and appears nowhere in this work**: the rig opens no database connection and starts no
Fineract server; it runs the Path A embeddable seam inside a throw-away `docker run --rm`.

Every quantity below is in **integer minor units**. No floating point on any decision path.

---

## 1. The claim under test

`.softhouse/gates.md` G-8, at commit `2d41838cdbbe5332bd62deb5cdec9f52f3df91f3`, says in four
places that the largest unamortized residual on record is **MNT 10.01 at n = 3000**
(`T159-R600p0-N3000-B1001` — 1001 minor units disbursed at 600.0 % over 3000 monthly periods, all
3000 REPAYMENT rows at `principal 0.00`, balance frozen at `10.01`, `totalInterestAmount
15010.01`). The section also says, correctly, that this is *"the largest OBSERVED residual, NOT A
BOUND"*, and explains its growth as follows:

> *"The largest unamortized residual rose from MNT 0.01 to **MNT 5.01 at n = 1000** (T117) to
> **MNT 10.01 at n = 3000** (T159) — **each time because somebody asked a larger term**, and
> neither worker found a limit."*
> — gates.md, *What is NOT known about family B*, "Whether it terminates"

> *"The residual doubled when the term tripled, and it doubled because somebody asked a bigger
> question, not because a boundary was found."*
> — gates.md, *The bound on the failing principal*

**T219's thesis is that the causal attribution in those two sentences is wrong, and that the
domain attached to the figure names the wrong variable.** Under T229's rescue law — already in
this file, already measured 7-of-9 — the residual of an unrescued family-B cell is

```
residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)
```

so the residual is a function of **`B_minor` capped at `n·δ`**, not of `n`. The term enters only
as the *cap*. T117 and T159 each got a larger residual because each **asked a larger principal**
(501 minor, then 1001 minor); the larger term merely raised the cap far enough out of the way that
the principal they asked was the binding constraint. **At `n = 3000` and `δ = 1` the cap is 3000
minor units — MNT 30.00 — and T159 asked a principal that used one third of it.**

If that is right, the record residual can be tripled **at T159's own term, without asking a larger
term at all**, and the phrase "MNT 10.01 at n = 3000" is correct only over the domain
**`B_minor ≤ 1001`**, which nothing in the section states.

## 2. What is registered

Cells (`src/cells-t219.json`), all at **600.0 % p.a., MNT, dp 2, `(19, HALF_UP)`**, G-8 shape
(MONTHS / repaymentEvery 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360 / single disbursement on the
schedule start date / no down payment / no charges / both multiples-of null), start `2024-01-01`.
Every principal is **odd**, so at `r = 1/2` each satisfies the resonance condition
(`B_minor · r` lands on a half-minor-unit boundary).

Predictions are `prediction.json`, produced by **T229's committed `site3.py` unmodified**, whose
inputs come from T223's committed emulator. Nothing was fitted to any cell in this probe.

| cell | n | B minor | δ | a | **registered outcome** | principal repaid | total interest (minor) | **residual (minor)** |
|---|---|---|---|---|---|---|---|---|
| `T219-R600p0-N103-B1` | 103 | 1 | 0 | 0 | clean — last row carries all principal | 1 of 1 | 104 | 0 |
| `T219-R600p0-N104-B1` | 104 | 1 | 1 | 0 | **FAMILY B FULL** | 0 of 1 | 1 | 1 |
| `T219-R600p0-N108-B1` | 108 | 1 | 1 | 0 | **FAMILY B FULL** | 0 of 1 | 1 | 1 |
| `T219-R600p0-N3000-B1001` | 3000 | 1001 | 1 | 0 | **FAMILY B FULL** | 0 of 1001 | 1 501 001 | 1001 |
| `T219-R600p0-N3000-B1999` | 3000 | 1999 | 1 | 1 | **FAMILY B FULL** | 0 of 1999 | 2 998 999 | **1999** |
| `T219-R600p0-N3000-B2999` | 3000 | 2999 | 1 | 1 | **FAMILY B FULL** | 0 of 2999 | 4 499 999 | **2999** |
| `T219-R600p0-N3000-B3001` | 3000 | 3001 | 1 | 1 | **FAMILY B PARTIAL** | **1** of 3001 | 4 503 001 | **3000** |
| `T219-R600p0-N3000-B4499` | 3000 | 4499 | 1 | 1 | **FAMILY B PARTIAL** | **1499** of 4499 | 6 751 499 | **3000** |
| `T219-R600p0-N3000-B4501` | 3000 | 4501 | 1 | 2 | **RESCUED — amortizes** | 4501 of 4501 | not modelled | 0 |

> ### \*\*\* T271 CORRECTION — the "total interest (minor)" column above is the REPAYMENT figure \*\*\*
>
> **Added by T271 (B-1), after the capture, as a labelled correction. The table itself is left
> byte-for-byte as registered: it is committed evidence of what was predicted in advance, and
> T114/T176 forbid editing it into agreement.**
>
> The column was computed as `n·E + B`. **That is total REPAYMENT, not total interest** — the same
> error T259 ruled on for T229's `P2_totalInterestEqualsNEplusB` (`.softhouse/capture/`
> `t256-verdict-predicate/DECISION-verdict-vs-predicate.md`). Where principal is repaid, the
> registered figure overstates interest by exactly the principal repaid. Re-derived from the raw
> capture in integer minor units by
> `.softhouse/capture/t271-b1-t219/rederive_t219_carriers.py` — **3 of the 7 non-throwing cells
> are refuted, and NOTHING IN THIS DIRECTORY GRADED ANY OF THEM**, because the classifier's
> `verdict` reads only the outcome family and the principal repaid:
>
> | cell | registered "total interest" | **observed total interest** | corrected form |
> |---|---|---|---|
> | `T219-R600p0-N3000-B3001` | 4 503 001 | **4 503 000** | `n·E + B − principalRepaid` **holds** |
> | `T219-R600p0-N3000-B4499` | 6 751 499 | **6 750 000** | `n·E + B − principalRepaid` **holds** |
> | `T219-R600p0-N103-B1` | 104 | **13** | **neither form holds — see below** |
>
> **`T219-R600p0-N103-B1` is the row T259 did not expect and the reason this correction is not
> just T259's applied twice.** The identity `totalRepayment = n·E + B` silently presumes the
> **family-B EMI-plus-balloon structure**: every row totals `E` and the last totals `E + B`. This
> cell is the one registered as **clean**, and it amortises: measured from the raw gz, rows 1–13
> total `0.01` of pure interest, **row 14 of 103 carries the entire `0.01` of principal, and rows
> 15–103 are all zero**. Only 13 rows ever charge interest, so `n·E` overcounts by about eightfold
> and both the registered form (104) and T259's corrected form (103) miss an observed 13. The only
> statement that survives on every cell is `interest = totalRepayment − principalRepaid` with a
> **measured** `totalRepayment` (14 − 1 = 13), which is exact but says nothing predictive.
>
> **Same row, the outcome NAME.** "clean — last row carries all principal" is false in its literal
> reading: principal lands on **row 14 of 103**. `classify_t219.py`'s observed label
> `AMORTIZES_FULLY(last-row-only)` means "exactly one row carries principal", not "the last row
> does", so the two strings agree by an accident of naming.
>
> **Materiality: LOW, and G-8 is untouched.** Nothing in G-8 rests on the interest total or on
> which row carries the principal — only on **whether** the cell amortises, which it does, exactly
> as registered. The residual figures in the last column, F1–F4, the region boundary and the
> `δ ≤ 1` conjecture are all unaffected. **No region moves and no option (b)/(c) is reopened.**

Three roles:

- **`N103/N104/N108-B1` are the promoted-vector shapes.** `.softhouse/vectors` carries
  `T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct` (no exemption),
  `T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct` and `-108x600pct` (two invariant exemptions
  each). G-8's prose says the region at this shape **starts at n = 104** and that n = 103 is
  clean. These three cells test that prose against the live oracle. **Nothing here writes to
  `.softhouse/vectors`.**
- **`N3000-B1001` is T159's own record cell, re-asked under a NEW tenant id.** It is the control:
  if it does not come back FULL with residual 1001 and `totalInterestAmount 15010.01`, this whole
  probe is uninterpretable and T219 reports that instead.
- **`N3000-B1999 … B4501` are the record-moving cells and a boundary pair at a term 15× the one
  T229 tested.** `1.5·n = 4500`, so `4499` must fail and `4501` must be rescued if the ceiling
  `(δ + ½)·n` holds at n = 3000.

## 3. Falsification conditions, stated in advance

**T219's thesis is FALSIFIED if**, with the control cell reproducing:

- **F1** — no cell at n = 3000 leaves a residual **greater than 1001 minor units**. Then MNT 10.01
  is not merely the largest *observed* residual at n = 3000, it survives a deliberate attempt to
  beat it at that term, and the section's causal story about the term stands unrefuted.
- **F2** — `T219-R600p0-N3000-B2999` amortizes. That is the shape most exposed to T229's **gap 1**
  (the pre-rescue instalment `E` is an unverified input): if the oracle's true `E` is 1500 rather
  than the emulated 1499, then `δ = 0` and the cell is not family B at all. `T229-R600p0-N200-B199`
  refuted exactly this way, at `B_minor/n = 0.995`, and `B2999` sits at `0.9997`. **This is
  registered as the likeliest single refutation in the set.**
- **F3** — `T219-R600p0-N3000-B4501` comes back family B. Then the ceiling is not `(δ + ½)·n` and
  the conservative superset `B_minor < 1.5·n` that G-8 currently offers as the only statable region
  is wrong at n = 3000, which is a **more** serious finding than anything about the residual, and
  T219 reports it as such.
- **F4** — the PARTIAL cells (`B3001`, `B4499`) repay something other than 1 and 1499. That is
  T229's **gap 2** (a balance-reduction path no model here contains) showing up again, and it is
  recorded, not tuned away.

**T219 will NOT** recompute `δ` from an observed post-rescue instalment and declare the law
vindicated — the same circular move T229 explicitly refused.

## 4. What T219 does with each outcome, decided in advance

- **If F1 holds** (no residual above 1001 at n = 3000): the figure is **correct and its domain
  survives the test**. T219 names the domain — *"largest observed over the principals asked, the
  largest of which is 1001 minor units"* — states that the attempt to beat it at the same term was
  made and failed, and **does not edit the number**. This is the T101 F-8 correction shape.
- **If any cell at n = 3000 leaves a residual above 1001 minor units**: the figure is
  **superseded as the record**, T219 says so, names T159 as the measurement superseded and T219 as
  the superseding one, and **rewrites the causal sentences** — the residual grew with the
  **principal asked**, capped by `n·δ`, not with the term.
- **Either way**, `δ` observed on every cell is reported, because G-8's only statable region rests
  entirely on the unproven conjecture `δ ≤ 1`. **A `δ ≥ 2` observation anywhere in this probe would
  be the headline and T219 would report it above everything else.** T219 predicts `δ = 1` on all
  six family-B cells and `δ = 0` on `N103-B1`; **no cell in this probe was chosen to hunt for
  `δ ≥ 2`, and finding none is therefore NOT evidence that none exists.**

## 5. What this probe does NOT do

- It **promotes no vector**. `.softhouse/vectors` must be byte-unchanged at
  `73c3ea7b43dd75f04884072719a87fc8e1d255c1` at the end of T219.
- It **grades no Go port cell**. Whether the port reproduces any of these is untouched
  `[UNVERIFIED]`.
- It asks **one rate only — 600.0 %** — and one term family. It is not evidence about 36.0 %,
  300.0 %, or any unswept rate.
- It does **not** model the rescued branch: on `B4501` the registered claim is only *that* the cell
  amortizes, never what instalment it lands on.
- It asks **nothing above n = 3000**, deliberately: the whole point is that the record can move
  **without** asking a larger term, and asking one would confound the test.
- It says nothing about the **THIRD OUTCOME** (`StackOverflowError`), about `minorUnitDigits ≠ 2`,
  Path B / REST, other day-count conventions, down payments, charges or multiples-of.

## 6. Rig

`src/CaptureT219.java` is built from T229's committed `CaptureT229.java` by
`src/make_harness_t219.py`, which replaces **only** the probe-cell block and the class name. Both
rig calibrations are preserved: `P-CAL-ZPA` / `P-CAL-ZPB` are byte-identical in inputs to the
already-promoted `T64-ZP-A` / `T64-ZP-B` and must reproduce pass 3g's committed observed blocks
cell for cell, or the run is refused. Emission order is scrambled so predicted-family-B,
predicted-clean and predicted-rescued cells interleave. Tenant ids are all new (`t219_*`).
**The harness asserts nothing, predicts nothing and classifies nothing.**
