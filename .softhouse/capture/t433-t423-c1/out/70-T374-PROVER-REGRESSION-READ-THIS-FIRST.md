# T374's wired prover, run at BOTH refs — ARM F changed nothing, and the 5 failures pre-date it

`.softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh` runs
`verify-capture-integrity.py` four times, so landing ARM F inside that grader could have
broken it. It was therefore run **at both refs**, and the second run is the control that makes
the first interpretable.

| run | ref | result | transcript |
|---|---|---|---|
| with ARM F | `7df613d1` (T433) | **PASS=23 FAIL=5** | `70-t374-prover-regression.txt` |
| **pre-ARM-F control** | `b102875c` (unmodified `main` tip, clone at `/tmp`) | **PASS=23 FAIL=5** | `71-t374-prover-at-PRE-ARMF-ref.txt` |

**The same 23 pass and the same 5 fail, by name, at both refs.** This is a MEASUREMENT, not an
inference from the deviation arithmetic: the prover was cloned to `/tmp/t433-preref`, detached
at `b102875c`, and run there, so `SRC` — which it derives from its own location — was the
pre-ARM-F tree.

The five, identical in both runs:

```
FAIL  (0)  run-all.sh in a fresh clone, no local ref                 rc=1 (wanted 0)
FAIL  (0)  10 sections recorded, 0 deviations
FAIL  (1b) run-all.sh AGGREGATE now fails on a mutated observation   rc=2 (wanted 1)
FAIL  (7)  run-all.sh green again after every mutation is reverted   rc=1 (wanted 0)
FAIL  (7)  10/10 as adjudicated, 0 deviations
```

**Every one is an assertion about `run-all.sh`'s AGGREGATE exit code or its deviation count.
Not one is about section 10's own exit code**, and all four section-10 assertions — (1a)
mutated observation → 1, (2) deleted observation → 1, (3) empty population → 2, (4a) missing
baseline → 2 — **PASS at both refs, with ARM F present.**

## The cause: section 9

`run-all.sh` sets its exit code to the **deviation count** (`echo "$DEVIATIONS" > "$STATUS.rc"`,
`run-all.sh:262`). **Section 9 (`adjudicate-section1.py`) is adjudicated `0` and exits `1`** on
an unmutated tree at `b102875c` — measured directly in
`.softhouse/capture/t433-t423-c1/out/runall-row/runall-control-BEFORE.txt`, a clone of
unmodified `main` with no ARM F anywhere in it. So every deviation count is one higher than
T374 pinned:

- a clean tree: 0 → **1** deviation, so `rc=1` where T374 wanted `0` — cases (0) and (7);
- a mutated observation: section 10 correctly goes red as T374 intended, 1 → **2** deviations,
  so `rc=2` where T374 wanted `1` — case (1b).

This is filed as T433 follow-up **F-6**. It is orthogonal to ARM F, it is not T433's to fix
(section 9 is `adjudicate-section1.py`, outside T433's assigned paths), and it means
`run-all.sh` has been reporting `RUN-ALL VERDICT: FAIL` on `main` without anyone recording it.
