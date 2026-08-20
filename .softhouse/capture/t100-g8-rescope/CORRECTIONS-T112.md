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

**Only `n = 250` is.** T84 swept `n = 150` and `n = 200` at 600.0 % / MNT 0.01, so its largest `n`
is **200**. `n = 122` is one above T84's **contiguous** top of 121, which is a different and much
weaker claim.

[VERIFIED by T112, re-derived in integer minor units from the committed raw captures: T84's `n` at
600.0 % / MNT 0.01 is {60} ∪ {88…121} ∪ {150, 200}; T100's is {103, 104, 108, 121, 122, 150, 200,
250}.]

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

**G-8 remains OPEN.** Options (b) and (c) amend the graded domain of a ratified DEC-n and are hard
`user` gates; nothing here decides them.
