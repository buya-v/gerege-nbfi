# Corrections applied to the G-8 write-up after this capture was taken (T112)

T101 reviewed T100's G-8 rewrite and **REJECTED it on three write-up sentences**, none of them a
measurement. T101 re-derived every load-bearing number in this directory independently, over a
**wider** cell set than T100 swept (687 swept cells / 312 family A / 29 family B, all ten
discriminator rows holding on 341 of 341 classified cells), and it held. **Nothing in
`out/capture-t100-raw.json` or in any number this capture produced is retracted.**

T112 applied the corrections to the authoritative text in **`.softhouse/gates.md` § G-8**. This
file records what in *this directory* still carries superseded phrasing, and why it was not
edited.

## Left byte-identical on purpose

- **`PREDICTION.md` and `prediction.json`** — a registered prediction, committed as a strict
  ancestor of the evidence commit. Its immutability is a property T101 verified (`34e973f` is a
  strict, never-amended ancestor of `6b0c1da`). **Amending it retroactively would destroy the only
  thing that makes it evidence.** Its row for `T100-FAMB-R600p0-N122-B1` reads
  *"EXTRAPOLATION — n above T84's swept top"*. See the correction below; the prediction's
  *outcome* (family B, fails) held.
- **`src/CaptureT100.java` (header, lines 18-19), `src/build_harness.py` (lines 41-42) and
  `src/gencases.py` (line 30)** — these are the sources that were actually executed to produce
  `out/capture-t100-raw.json`. Editing even a comment would leave the committed capture no longer
  byte-reproducible from the committed sources, which is worth more than a tidy comment. They
  carry the same superseded phrasing as the prediction.

## The correction those four files still predate — T101 F-4

They say the two added cells `n = 122` and `n = 250` are **"above the top of n that T84 swept"**.

**Only `n = 250` is, and only at this shape.** T84 swept `n = 150` and `n = 200` at
600.0 % / MNT 0.01, so its largest `n` **at 600.0 % / MNT 0.01** is **200**. `n = 122` is one above
T84's **contiguous** top of 121, which is a different and much weaker claim.

**Scope this, always.** T84's largest `n` **anywhere** is **600**, at 0.12 % / 1.2 % / 3.6 %
(`T84B-XL-R0p12-N600-B291`), so the unqualified sentence *"T84's largest n is 200"* is **false** and
must never be written. It was written unqualified into `gates.md` by the F-4 fix itself and was
corrected by T122 — T114 F-T114-2.

[VERIFIED by T112, re-derived in integer minor units from the committed raw captures: T84's `n` at
600.0 % / MNT 0.01 is {60} ∪ {88…121} ∪ {150, 200}; T100's is {103, 104, 108, 121, 122, 150, 200,
250}. Re-derived again by T122 over T84's full n-set across both captures: max **600** overall, max
**200** at the family-B shape.]

## The other corrections, for completeness

They land in `.softhouse/gates.md` § G-8 and do not touch this directory's numbers:

- **F-1 (P1)** — "family A exists at all 12 rates swept" is false; it exists at **11 of 12**, and
  **not** at 600.0 %, the rate that defines family B.
- **F-2** — "11.6× the old bound" lost its antecedent when the rewrite deleted every mention of
  MNT 0.25. Against the bound the section actually states (MNT 0.23) the ratio is **12.65×**; the
  gate now gives both absolute figures instead.
- **F-3** — the exit-code caveat was false for three of the four exemption-demo variants.
  `Summary.ExitCode()` returns 1 on `ParityFail`/`InvariantViolations` **before** it reads
  `FatalReasons` [`nexus/internal/apps/loanschedule/conformance/grade.go:154-160`], so those three
  exits **are** the G-8 finding. Only `FAMILY-B-WITH-EXEMPTION`'s exit 2 is the unrelated
  one-vector-store coverage fatal. This directory's own `out/exemption-demo-t100.json` records the
  four exit codes as 1 / 2 / 1 / 1 and is the evidence for the corrected wording.
- **F-5** — the T75 shape (MNT 0.01 / n = 6 / 21.6 %) was cited to the neighbouring cell
  `T100-FAMA-R21p6-N6-B2` (MNT 0.02). The right citation is `T83-SW-R21p6-N6-B1`.
- **F-6** — "331 divergent-or-invalid cells" is T84's narrower accounting; over this section's own
  union it is **341** (312 family A + 29 family B).
- **F-7** — "0.03/6 and above are clean" extends past the swept principals (1..6 minor at that
  shape).
- **F-8** — T83's terms are the eight discrete values {2, 3, 4, 6, 12, 24, 36, 56}, not the
  contiguous range "2…56".

## KNOWN DEFECTS in the executed probe sources — recorded by T122, deliberately NOT fixed

Found by T114 (F-T114-5, F-T114-6), re-verified by T122. **Do not edit these files.** They are the
sources that were actually executed to produce the committed captures; editing one — even a comment
— leaves the capture no longer byte-reproducible from its own sources, which is the same reasoning
that keeps the four files above byte-identical. **A future re-run must fix both FIRST, in a new pass
with new ids, writing to a new `out/` directory.**

### D-1 — a live `float()` in an analysis script, contradicting the file's own header

`.softhouse/capture/t83-nonamortizing/src/classify-boundary.py`

- **`:20`** — *"Money is read as INTEGER MINOR UNITS throughout … **Nothing here constructs a
  float.**"*
- **`:102`** — `for (rate, n), rs in sorted(by_shape.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):`

The header is false. This is **P-25 in a live file** — the very rule this gate's own write-up exists
to teach, sitting inside this gate's own evidence set. It is also **P-22**: an absolute honesty claim
in a header that nobody drove red.

**No published result is affected**, measured rather than asserted. T122 copied the script unmodified
to a scratch directory, built a variant differing **only** in that one sort key
(`fractions.Fraction(str(...))` for `float(...)`), and ran both against
`out/capture-t83-raw.json`: the emitted `measured-boundary.json` files are **identical**, the stdout
boundary tables are **identical row for row**, and the unmodified run reproduces the committed
`out/measured-boundary.json` **exactly**. The `float()` is a sort key over annual-rate *labels* only
— no money value is converted and no classification, comparison or count reads it — and the four
labels T83 swept (7.0, 16.8, 21.6, 36.0) order identically under either key.

**A re-run must fix `:102` (or `:20`) before it re-emits.** The header must become true or the key
must become exact; leaving both is what lets the next reader trust an absolute claim that is false.

### D-2 — `closed_form_check.py` exits non-zero on its own all-clean path

`.softhouse/capture/t100-g8-rescope/src/closed_form_check.py:83` computes
`min(abs(r['gap_float']) for r in refuted)` with no guard for an empty `refuted`, so an input with
**zero** refutations exits **1** with `ValueError: min() arg is an empty sequence`.

**No recorded number is affected.** Every count prints *before* the crash, and this directory's
committed `out/closed-form-check.json` was written by the 342-cell T84 run, where `refuted` has 22
members and the crash path is not taken. T122 re-ran the script **unmodified** from a scratch copy
(sha256 `55ecbc8f633765522ddcd7b038a3aaa46de6d5ec9c1b6be4489c21c6fdbae2f6`, byte-identical to the
committed source; the committed `out/` was not touched):

```
$ python3 <scratch>/closed_form_check.py .../capture-t83-raw.json
cells evaluated (calibrations excluded): 330 / HELD 330 / REFUTED 0 / exact ties 0
ValueError: min() arg is an empty sequence      line 83          EXIT=1
$ python3 <scratch>/closed_form_check.py .../capture-t84-raw.json.gz .../capture-t84b-raw.json.gz
cells evaluated: 342 / HELD 320 / REFUTED 22 / exact ties 0
smallest |gap| among refuted: 3.025e-36   largest: 2.429e-19    EXIT=0
   -> output byte-identical to the committed out/closed-form-check.json
```

The hazard is a **signalling** one: a script whose job is to report refutations returns a *failure*
exit on the *clean* input, which a future re-runner will read as "the check failed" when it means
"there was nothing to report". A re-run must guard the empty list before it re-emits.

**G-8 remains OPEN.** Options (b) and (c) amend the graded domain of a ratified DEC-n and are hard
`user` gates; nothing here decides them.
