# ERRATUM — the published K8 decomposition is `16 + 8 + 6 = 30`; measured, it is `13 + 10 + 6 = 29`

**`C-T440-2` (MINOR), re-measured and confirmed by T442.**
Drive `instruments/t442-k8-decomposition.sh` · transcript `out/T442-K8-DECOMPOSITION.txt`
(GREEN arm `disagreements=0`, RED arm `disagreements=3`).

> **T442 did not apply the correction.** The text lives in
> `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md`, which is outside this task's grant
> (`.softhouse/capture/t424/` only). The exact replacement text is below so that applying it is a
> paste. **Verdicts are unaffected** — every one of the 29 is still NOT state-loss, established
> independently by T440's own adjudicator.

## Where the wrong arithmetic actually lives

`git grep -n 'all sixteen\|the eight \`SWEEP'` over `.softhouse/` returns the decomposition in
**one file only**: `AUDIT-CLASS.md:106-108`. T440's condition says *"`AUDIT-CLASS.md` and the
handoff both"*; **I looked in `.softhouse/handoff/` and the sentence is not there** — `git grep`
for `all sixteen` under `.softhouse/handoff/` returns only unrelated T39/T242/T379 matches, and
T424's own handoff `T424-t408-conditions.md` states the K8 total (29) without decomposing it.
So there is **one** site to correct, not two.

## The measurement

Partition of the 29 rows in the `--- K8` block of `out/T424-CENSUS-after-with-K8.txt`,
taken by pattern from the transcript, not by eye:

| what | published | **measured (T442, and T440 independently)** |
|---|---|---|
| rows that are a `sel "S…"` call | 16 | **13** |
| rows that are `SWEEP_*=$((…))` counters | 8 | **10** |
| rows that are neither (parent-side assignments) | 6 | **6** |
| **total** | **30** ✗ | **29** ✓ — and it equals the census's own printed `== K8 SITES: 29` |

The residual six, printed in full by the drive so the cell is not a black box:

```
SWEEP_ERRF=$(mktemp "${TMPDIR:-/tmp}/casualty-sweep-stderr.XXXXXXXXXX") || {
SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?
if ! SWEEP_COMMIT=$(git rev-parse --short HEAD); then SWEEP_COMMIT="UNMEASURED"; fi
if ! SWEEP_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ); then SWEEP_DATE="UNMEASURED"; fi
SWEEP_UNTRACKED_N=$(git ls-files --others --exclude-standard .softhouse | grep -c .); _unt_rc=$?
case "$SWEEP_UNTRACKED_N" in ''|*[!0-9]*) SWEEP_UNTRACKED_N="UNMEASURED" ;; esac
```

## Why the cell said 16 — the error is a real conflation, and it is measured too

There **are** sixteen `sel` calls in `casualty-sweep.sh`. Three of them (`S1`, `S3`, `S7`) use
`-F` patterns carrying **no `|`**, so they never match `K8_RIGHT` and never reach the wide `K8`
list. **16 is a count of the FILE; 13 is the count IN THE CENSUS**, and the published row silently
swapped one for the other. Measured by the drive: `sel` calls in the file = 16, of those with no
pipe = 3, 16 − 3 = 13 = the census's `sel` rows.

The `8` has no such excuse, and it is wrong in **two** rows of `AUDIT-CLASS.md` (`:102` under
`K1+K7`, and `:107` under `K8`). Measured by the same drive: `SWEEP_*=$((…))` lines in
`casualty-sweep.sh` **today = 10**; **distinct counter variables = 3** (`SWEEP_REFUSED`,
`SWEEP_SELECTORS`, `SWEEP_DIDNOTRUN`); the same lines at `8fa677a6`, the last commit before T402,
**= 3**. So 8 is neither the before-count, nor the after-count, nor the number of distinct
counters. Unlike the 16, there is no conflation that explains it; it is simply a wrong cardinal,
and it does not match the list it claims to decompose.

## Replacement text for `AUDIT-CLASS.md:106-108`

Line 106 — replace `all sixteen \`sel "S…" …\` calls` and its cell with:

```
| the thirteen `sel "S…" …` calls that reach the wide list | K8 | **NOT state-loss.** All sixteen `sel` calls in the file are bare at column 0; thirteen of them appear in the wide `K8` list because each carries a `\|` **inside its own quoted ERE** — exactly the over-inclusion `K2`/`K3` have by design. `S1`, `S3` and `S7` use `-F` patterns with no `\|` and never reach it. The de-noised `K8s` view lists **none** of the sixteen. |
```

Line 107 — replace `the eight \`SWEEP_*=$((SWEEP_*+1))\` counters` with:

```
| the ten `SWEEP_*=$((SWEEP_*+1))` counter rows | K8 | **NOT state-loss.** `$((` is arithmetic expansion, not a subshell; the wide `K8` matches them on the `$(` prefix. Ten rows, incrementing three distinct counters. `K8s` excludes `$((` explicitly and lists none of them. |
```

And **`AUDIT-CLASS.md:102` carries the same wrong cardinal** — `` `SWEEP_*=$((SWEEP_*+1))` ×8 ``
under `K1+K7`. It should read **×10**.

Line 108 (the six parent-side assignments) is **correct as written** and needs no change.

Add, wherever the three rows are totalled: **`13 + 10 + 6 = 29`, which is the census's own
`== K8 SITES: 29`.** A decomposition that does not sum to its own total cannot do the job it
exists for — telling a maintainer that the census has been *fully* adjudicated.

## Acceptance test

```
bash .softhouse/capture/t424/instruments/t442-k8-decomposition.sh          # must exit 0
T442_K8_PUBLISHED=1 bash .softhouse/capture/t424/instruments/t442-k8-decomposition.sh   # must exit 1
git grep -c 'all sixteen `sel' -- .softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md  # must be 0
git grep -c 'x8\|×8' -- .softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md            # must be 0
```
