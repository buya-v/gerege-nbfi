# ERRATUM — the published K8 decomposition is `16 + 8 + 6 = 30`; measured, it is `13 + 10 + 6 = 29`

**`C-T440-2` (MINOR), re-measured and confirmed by T442.**
Drive `instruments/t442-k8-decomposition.sh` · transcript `out/T442-K8-DECOMPOSITION.txt`
(GREEN arm `disagreements=0`, RED arm `disagreements=3`).

> ## ERRATUM TO THE ERRATUM — **T452, 2026-08-29. `F-T447-2`.**
>
> **The paragraph this erratum originally carried — *"So there is **one** site to correct, not
> two"* — was WRONG, and it was wrong for the reason this program keeps writing down and then
> forgetting: "not found" is a statement about the search, never about the world.**
>
> T442 searched `.softhouse/handoff/` for the adjective phrase `all sixteen` — the spelling used
> in `AUDIT-CLASS.md`'s *table cell* — and found nothing. The handoff spells the same
> decomposition as **words in running prose**, at
> `.softhouse/handoff/T424-t408-conditions.md:233,235,236`, so that search could never have
> reached it. **T440's `C-T440-2` stands as written: two sites.**
>
> The operational consequence was worse than the wording. This erratum's original acceptance
> test mentioned the handoff **zero** times, so applying the erratum as written would have gone
> **green with the defect still on `main`**.
>
> **T452 re-derived the partition rather than inheriting it** — from the subject file
> (`16` `sel` calls, `S1`/`S3`/`S7` carry no `|` → `13`; `10` counter lines; `3` distinct
> counters) and, independently, from the K8 block of the census transcript (`13` `sel` rows,
> `10` counter rows, `6` residual). Both routes give **`13 + 10 + 6 = 29`**, equal to the
> census's own printed `== K8 SITES: 29`. T442's arithmetic is right in every cell; only its
> *site count* was wrong.
>
> **Site 2 is now REPAIRED** in `.softhouse/handoff/T424-t408-conditions.md`. Site 1
> (`AUDIT-CLASS.md`) remains outside T452's grant, exactly as it was outside T442's, and its
> paste-ready replacement text is unchanged below.
>
> Drive: `.softhouse/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh`
> · transcript `.softhouse/capture/t452-t447-conditions/out/T452-K8-SITES.txt`.

> **T442 did not apply the correction to `AUDIT-CLASS.md`.** The text lives in
> `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md`, which is outside T442's grant and
> outside T452's (`.softhouse/capture/t424/`, `.softhouse/capture/t452-t447-conditions/`, the
> `a2-33` sweep site and this handoff only). The exact replacement text is below so that
> applying it is a paste. **Verdicts are unaffected** — every one of the 29 is still NOT
> state-loss, established independently by T440's own adjudicator.

## Where the wrong arithmetic actually lives — the DECLARED SITE SET

The drive asserts **set equality** against this table; it does not count. A site that is
repaired must lose its row **in the same commit**, or the table starts excusing a defect that is
no longer there — the same discipline `conformance.sh`'s fail-open frontier pin uses. A site
that appears and is not in the table turns the drive RED.

<!-- T452-SITE-TABLE-BEGIN — parsed by t452-k8-sites-drive.sh. Rows are `path` in backticks. -->

| site | lines | state |
|---|---|---|
| `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md` | 102, 106, 107 | **OPEN** — outside every grant so far; paste-ready text below |

<!-- T452-SITE-TABLE-END -->

**Repaired and therefore absent from the table above:**
`.softhouse/handoff/T424-t408-conditions.md:233-236` — corrected by T452, 2026-08-29. It is not
excluded from the search; it drops out **by measurement**, because the corrected prose no longer
carries the defect shape.

### Files that QUOTE the wrong cardinals in order to correct or to test them

These are not sites. The list is declared here rather than inside the drive so that it cannot be
widened by an author trying to go green, and the drive REFUSES a stale entry — one that matches
no file — so the exclusion list cannot outlive what it excuses.

<!-- T452-QUOTING-FILES-BEGIN -->

- `.softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md`
- `.softhouse/capture/t424/instruments/t442-k8-decomposition.sh`
- `.softhouse/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh`
- `.softhouse/capture/t452-t447-conditions/out/T452-K8-SITES.txt`
- `.softhouse/reviews/t447-review-t442/REVIEW.md`
- `.softhouse/reviews/t447-review-t442/instruments/t447-k8-handoff-site.sh`
- `.softhouse/reviews/t447-review-t442/out/T447-K8-HANDOFF-SITE.txt`
- `.softhouse/tasks.json`

<!-- T452-QUOTING-FILES-END -->

## The measurement

Partition of the 29 rows in the `--- K8` block of `out/T424-CENSUS-after-with-K8.txt`,
taken by pattern from the transcript, not by eye:

| what | published | **measured (T442; re-derived independently by T440 and by T452)** |
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

## Replacement text for `.softhouse/handoff/T424-t408-conditions.md:233-236` — **APPLIED by T452**

Recorded so the correction is auditable without a diff. The original read
*"… are the `sel` calls … are `SWEEP_*=$((…))` counters … are parent-side assignments"* with the
cardinals sixteen / eight / six. It now reads:

```
**All 29 adjudicated, and none is a live defect.** Thirteen of the sixteen `sel` calls reach the
wide list, because each of those carries a `|` **inside its own quoted ERE** — the same deliberate
over-inclusion `K2` and `K3` have; `S1`, `S3` and `S7` use `-F` patterns with no `|` and never
reach it, so **16 is a count of the FILE and 13 is the count IN THE CENSUS**.
Ten are `SWEEP_*=$((…))` counter rows over three distinct counters, matched on the `$(` of an
arithmetic expansion, which is not a subshell. Six are parent-side assignments (…) whose command
runs in a subshell but whose **assignment happens in the parent**. `13 + 10 + 6 = 29`, which is
the census's own printed `== K8 SITES: 29`.
```

## Acceptance test — **it must reach BOTH sites, and it must search WORDS as well as digits**

The original acceptance test below mentioned the handoff zero times. That is the defect
`F-T447-2` names, so the site-set drive is now the primary check and the two `git grep` lines are
kept only as a cheap smoke test of site 1.

```
# PRIMARY — set equality over ALL tracked .softhouse/ files, both spellings, calibrated:
bash .softhouse/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh     # must exit 0

# the partition itself, by T442's independent transcript route:
bash .softhouse/capture/t424/instruments/t442-k8-decomposition.sh                    # must exit 0
T442_K8_PUBLISHED=1 bash .softhouse/capture/t424/instruments/t442-k8-decomposition.sh  # must exit 1

# site 1 smoke test, valid ONLY once AUDIT-CLASS.md is corrected (it is not, yet):
git grep -c 'all sixteen `sel' -- .softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md  # must be 0
git grep -c 'x8\|×8' -- .softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md            # must be 0

# site 2, already applied by T452 — and note it is asserted by SHAPE, not by phrase:
bash .softhouse/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh 2>&1 \
  | grep 'handoff is NOT a live site'                                               # must say OK
```
