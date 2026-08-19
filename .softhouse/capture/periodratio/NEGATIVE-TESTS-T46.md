# T46 — negative tests and determinism for the two new `periodratio` passes

`patterns.md`: *an assertion suite that has never failed has not been tested.* Every recipe added by
T46 was run in a deliberately wrong configuration and watched to exit non-zero naming the breach.

## Determinism

The `arms` pass was executed a **second time from a fresh throwaway container**
(`T46_OUT_PREFIX=t46-periodratio-arms-determinism`). The payload is **byte-identical**:

```
cmp out/t46-periodratio-arms.json out/t46-periodratio-arms-determinism.json   -> silent
sha256 eab5dc0cd8e9b74e428c9d8cd0d87a8ea72129c01fe1375ec679b624fb893fc4  (both)
```

The **exhaustive month-difference sweep** was likewise re-executed from a fresh throwaway container and
its output is byte-identical [`analysis/run-t46-monthdiff.sh`; `diff` silent against the first run].

The `reemit` pass has a stronger check than determinism: **2072 of 2072 values identical to T39's
committed payload**, taken on a different day through a different harness
[`analysis/t46_reemit_identity-output.txt`].

## N-T46-1 — the THREADED axis, the one that is evidence about money

`T46_JAVA_PROPS="-Dt46.mathContextRoundingMode=DOWN"` on the `arms` pass.
**Exit 1**, breaches on every generating case, read **off the `MathContext` object** rather than off the
case record — which is the whole point of the F39-3 fix:

```
BREACH: T46-ARM-CTL: THREADED rounding mode DOWN, expected HALF_UP
...
BREACH: T46-RE-2ME:  THREADED rounding mode DOWN, expected HALF_UP
BREACH: payload assertions failed
RUN INVALID -- capture is not admissible.
```

Recorded output: `out/t46-neg-threaded-run.txt`, payload `out/t46-neg-threaded.json`.

## N-T46-2 — the seam class

`T46_EXPECT_SEAM_SHA=deadbeef` on the `reemit` pass. **Exit 1** before any capture runs:

```
BREACH: seam class sha256 is bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714,
        expected deadbeef
RUN INVALID -- capture is not admissible.
```

Recorded output: `out/t46-neg-seam-run.txt`.

## What the negative legs do NOT prove

- **The AMBIENT axis was not exercised negatively by T46.** T39's N7 already did it
  (`-Dt39.tenantRoundingModeOrdinal`) and found all sixteen observed blocks byte-identical — which is
  the finding, not an omission: on Path A the ambient context does not move the money.
  `[VERIFIED by T39; not re-run by T46]`
- **The `--negative` legs of the two charge tools** (`bin/t46-invariants.py`, `bin/t46-exacttext.py`)
  live in the `charges` set and are recorded there.
- **No negative leg exercises the `T46-YR-*` throw path deliberately failing to throw.** If a future
  Fineract version adds a YEARS arm, these two captures become schedules and the recipe will report
  `9 generated, 2 threw` → `11 generated, 0 threw`, which the script prints but does not assert. That is
  a deliberate choice: asserting "it must throw" would freeze a defect. `[UNVERIFIED as a guard]`
