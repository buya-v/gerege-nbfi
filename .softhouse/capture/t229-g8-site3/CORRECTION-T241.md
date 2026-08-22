# CORRECTION — `src/site3.py`'s TOTAL-INTEREST claim is FALSE, and what it actually computes

**Filed by `T241`. `src/site3.py` is NOT edited** — it is byte-identical to the copy in T229's
prediction commit `29ed78c`, which is the whole point of keeping it: it records what T229 ran, and a
prediction registered before a probe stops being a prediction the moment somebody edits it
afterwards. Per **T114's standing ruling and T176's prohibition**, committed evidence gets a
**labelled correction or a successor file**, never a silent edit that makes it agree with a later
document. This file is the label; `../t241-g8-evidence/src/rederive_t241.py` is the successor.

**This affects NO verdict, anywhere.** Not T229's, not T219's, not the conformance harness's. See
§4, which says exactly why and does not inflate it.

---

## 1. The claim, quoted from the artefact

`src/site3.py`, last line of the docstring section headed *THE LAW*:

> ```
>     TOTAL INTEREST = n*E + B  for any unrescued cell.
> ```

and the field it emits, `src/site3.py:210-211`:

> ```python
>         "predictedTotalInterestMinor": (None if outcome == "RESCUED_BY_SITE3"
>                                         else n * e + b_minor),
> ```

The same claim is therefore carried, as data, in **both** committed prediction files —
`prediction.json` here and `../t219-g8-residual/prediction.json` — and `src/site3.py` is
**byte-identical in both capture directories** (`sha256
36701476f41de4280bd51deee49ac26028b78a86ed52e0db0c4d89debddf1996`), which is why
`../t219-g8-residual/CORRECTION-T241.md` points here.

## 2. What is wrong with it

`n·E + B` is **the TOTAL REPAYMENT of the modelled schedule, not its total interest.** The
docstring derives that the last row's instalment is `E + B` while rows `1…n-1` pay `E`, so the
scheduled payments sum to `(n-1)·E + (E + B) = n·E + B` — and that sum is principal **plus**
interest. The field names it interest. The two coincide **only when the total principal repaid is
zero**, i.e. on a FULL family-B cell. On a **PARTIAL** cell the field overstates the interest by
exactly the principal the loan does repay.

**The corrected form, with its domain named** (a bare form is what produced this defect):

> Wherever **FACT A** holds — the last row's instalment exceeds `E` by exactly `B` —
> **TOTAL REPAYMENT = n·E + B**, hence
> **TOTAL INTEREST = n·E + B − TOTAL PRINCIPAL**, with `TOTAL PRINCIPAL = max(0, B_minor − n·δ)`.
> Where FACT A does **not** hold, **neither form applies** and neither may be quoted.

`.softhouse/gates.md` already states the corrected form (`n·E + B − principal`) in the *THE LAW*
block of *SITE 3, CHARACTERISED*; **the live gate text is right and this committed instrument is
wrong**, which is the reverse of this program's usual direction and is why it survived.

## 3. The measurement that establishes it — RE-DERIVED BY T241, NOT TRANSCRIBED

`T219` found this and declared it (handoff gap 8) rather than fixing it out of scope. Its
observations were taken against the **live reference oracle (Fineract)** at pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, `(19, HALF_UP)`, and are committed at **`6eacc06`** in
`../t219-g8-residual/out/capture-t219-raw.json.gz`. **T241 re-derived every number below itself**,
from the mechanism and from the `.gz` capture (STANDING RULE 5), reading none of T219's reported
figures — T219 explicitly warns that transcription is how this section acquires its defects.
Measured on branch `softhouse/T241-g8-evidence-hygiene`, forked from `main` at **`ea34404`**.
Reproduce with `python3 ../t241-g8-evidence/src/rederive_t241.py`.

**No oracle was contacted by T241** — the reference oracle was unreachable on the host this ran on,
so every observation here comes out of the committed `.gz` captures and nothing else.

### The two counterexamples, in integer minor units

At 600.0 % p.a., MONTHS / repaymentEvery 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360, so the period
rate factor is exactly `1/2` and `I₁ = B/2` exactly:

| | `T219-R600p0-N3000-B3001` | `T219-R600p0-N3000-B4499` |
|---|---|---|
| `n` | 3000 | 3000 |
| `B` (minor) | 3001 | 4499 |
| `I₁` exact (minor) | `3001/2` | `4499/2` |
| `I₁q` = HALF_UP(`I₁`) | **1501** | **2250** |
| `E` re-derived (minor) | **1500** (raw `15.00499999999999985`) | **2249** (raw `22.49499999999999977`) |
| `δ = I₁q − E` | **1** | **1** |
| `a = HALF_UP(B/n)` | 1 | 1 |
| guard 1 `B > ⌊n/2⌋` | true (3001 > 1500) | true (4499 > 1500) |
| guard 3 `a > δ` | **false** (1 > 1 is false) → **no rescue** | **false** → **no rescue** |
| TOTAL PRINCIPAL `= max(0, B − n·δ)` | `3001 − 3000 =` **1** | `4499 − 3000 =` **1499** |
| **`site3.py` says** `n·E + B` | `3000·1500 + 3001 =` **4503001** | `3000·2249 + 4499 =` **6751499** |
| **corrected** `n·E + B − principal` | `4503001 − 1 =` **4503000** | `6751499 − 1499 =` **6750000** |
| **OBSERVED** `totalInterestAmount` | `45030.00` → **4503000** | `67500.00` → **6750000** |
| observed `totalPrincipalAmount` | `0.01` → **1** | `14.99` → **1499** |
| observed `totalRepaymentAmount` | `45030.01` → **4503001** | `67514.99` → **6751499** |

Each observed total was **re-summed from the individual schedule rows** in integer minor units and
matches its own detail (3000 repayment rows each): interest `4503000` / `6750000`, principal `1` /
`1499`. **`site3.py`'s figure is, to the unit, the observed TOTAL REPAYMENT in both cells** — which
is the diagnosis, not a coincidence.

### The whole committed corpus says the same thing, and said it before T219 ran

Re-bucketed by T241 from **T229's own committed corpus census**,
`out/validate-corpus.json` (added at **`bb35cc8`**), 296 stuck cells drawn from the T117, T117-p2,
T159 and T223 raw captures:

| bucket | cells | FACT A holds | `n·E + B` = interest | `n·E + B − P` = interest | repayment = `n·E + B` |
|---|---|---|---|---|---|
| ALL stuck cells | 296 | 220 | **176** | **220** | **220** |
| `δ ≥ 1` | 183 | 183 | 176 | **183** | 183 |
| `δ = 0` | 113 | 37 | **0** | 37 | 37 |
| FACT A holds | 220 | 220 | 176 | **220** | **220** |
| FACT A fails | 76 | 0 | **0** | 0 | **0** |

Three things follow, and the third is the one to carry forward:

1. **The docstring's "for any unrescued cell" was already refuted by T229's own committed output**,
   on 120 of 296 cells, before T219 asked anything. `out/validate-corpus.json`'s summary records
   `interestLaw_holds: 176` against `stuckCellsExamined: 296` — the refutation was **in the
   evidence**, unread, because nothing quoted that count.
2. **It looked true because of what nobody had asked.** Every `δ ≥ 1` stuck cell in that corpus has
   an observed principal of **zero** (176 of them), so the two forms agree there. T219's `B3001` and
   `B4499` — and T229's own `B201`, `B251`, `B299` — are the first **PARTIAL** cells with a live
   observation, and they are exactly where the two forms come apart.
3. **The corrected form discriminates perfectly on FACT A**: `TOTAL REPAYMENT = n·E + B` holds on
   **220 of 220** cells where FACT A holds and **0 of 76** where it does not. So FACT A, not the
   word "unrescued", is the condition the law needs — and `δ = 0` is not a safe domain for either
   form (`n·E + B` holds on **0 of 113** there).

## 4. What this does NOT affect — stated plainly, and it is not more than this

- **No verdict.** Neither `src/classify_t229.py` nor `../t219-g8-residual/src/classify_t219.py`
  reads `predictedTotalInterestMinor` on any decision path; both grade a cell on
  `predictedOutcome` and `predictedTotalPrincipalMinor`. T229's "7 of 9 as registered" and T219's
  cell verdicts are unchanged by this correction.
- **No figure in `.softhouse/gates.md`.** The section states the corrected form and its four worked
  examples are right (re-checked by T241: `B201` `200·100 + 201 − 1 = 20200`; `B251`
  `200·125 + 251 − 51 = 25200`; `B299` `200·149 + 299 − 99 = 30000`; `B150`
  `1400·4 + 150 − 0 = 5750`; all four match the captured `totalInterestAmount`).
- **No vector, no cell, no store digest.** `.softhouse/vectors` is untouched by T241.
- **No re-opening of the Fineract source.** The source citations in `src/site3.py`'s docstring are
  T229's, bound by matched text at `426a23544…`; T241 did not re-open them.
  `[UNVERIFIED by T241 — inherited from T229.]`

## 5. Three further carriers of the same wrong law, found by T241 and NOT edited

Named here so the next reader is not surprised by them. **None is on a verdict path**, and all three
are committed evidence that records what its author ran, so all three are left byte-identical:

1. `src/classify_t229.py:105-106` and `../t219-g8-residual/src/classify_t219.py:109-110` — a
   **diagnostic** field `P2_totalInterestEqualsNEplusB`, computed from the observed row-1 total.
   Nothing reads it as a pass/fail, and it is already **recording the refutation**: in the committed
   `out/classify-t229.json` (commit `bb35cc8`, before T219 existed) `T229-R600p0-N200-B201` and
   `T229-R600p0-N200-B251` both read `"P2_totalInterestEqualsNEplusB": false` beside
   `"verdict": "AS PREDICTED"`, and `../t219-g8-residual/out/classify-t219.json` reads the same on
   `B3001` and `B4499` — while every FULL cell, e.g. `B2999`, reads `true`. **The instrument was
   telling the truth about its own docstring in the same file as the passing verdict.**
2. `src/validate_corpus.py:11` — the docstring line *"TOTAL INTEREST : n*E + B on every stuck
   cell"*, and its `interestPredicted` / `interestLawHolds` / `summary.interestLaw_holds`. The
   script's own committed output (§3) is the refutation of its own docstring; **no document quotes
   `interestLaw_holds`**, so nothing downstream is wrong.
3. `prediction.json` here and in `../t219-g8-residual/` — the emitted
   `predictedTotalInterestMinor` values. **These are registered pre-probe predictions and must never
   be edited**; where a cell is unrescued and its observed principal is non-zero, read the field as
   the predicted total *repayment*.
