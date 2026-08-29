# T442 — the C-T440-1 class, swept and adjudicated

**Instrument** `instruments/t442-selfmatching-probe-census.py` · **transcript** `out/T442-CLASS-SWEEP.txt`

> **The class.** An instrument that searches the repository with a probe token **spelled as a
> literal in its own tracked source** changes meaning the moment it is committed, because the
> search then finds the searcher. `t424-comment-claims-drive.sh` did exactly that and shipped a
> transcript its own committed code cannot produce (`C-T440-1`).

> ## TREE QUALIFICATION — **T452, 2026-08-29. `F-T447-3`. READ BEFORE QUOTING ANY NUMBER BELOW.**
>
> **Every count in this file is a fact about the commit it was taken on, and about no other.**
> The transcript it summarises was taken at **`97bad8ed`**, where it reproduces byte-for-byte
> (verified independently by T447). It does **not** reproduce at T442's own branch tip
> `c223a16b`, and the drift was measured:
>
> | | at `97bad8ed` | at `c223a16b` |
> |---|---|---|
> | `scripts` | 1704 | 1707 |
> | `searches` | 399 | 401 |
> | `self_only` (A1) | **2** | **0** |
> | `family_only` | **3** | **0** |
> | `runtime` | 131 | 133 |
>
> **Cause, measured:** publishing this adjudication, the transcript and the T442 handoff made
> them new *tracked carriers* of `zzq-t379-nothing` and `zzz-no-such-string-t367`. The A1 rows
> acquire non-self carriers and demote to A2; `family_only` collapses because the new carriers
> lie outside the searchers' task directories. **The census is a member of the class it
> censuses.** That is `C-T440-1`'s shape, one level up.
>
> **The drift is not an artefact — it is a true change in the world.** A new tracked carrier
> really does change what an ABSENT-assertion measures. So the counts were right when taken and
> are right now; what was wrong was quoting them **bare**.
>
> **T452's decision, and the argument for it (the condition asked for one).** *Pin, do not
> exclude.* Taking the census in a way that excludes its own publication would be the
> `:!`-pathspec self-exclusion this very file names as **the wrong repair** — it opens a hole
> under the excluded path, so a future instrument published there would never be censused. So:
> **(a)** every count carries its tree, here and in the marker file; **(b)** the figure quoted
> bare is instead the **MEMBER SET** — paths and lines — which does not drift when a transcript
> is committed, only bucket *labels* do. The four members below are unchanged at every tree
> measured so far. `t452-classify-v2.py` prints both, and prints its tree on the result line.
>
> The T442 handoff (`.softhouse/handoff/T442-t440-conditions.md`) also quotes these counts bare
> and is **outside T452's grant**; it is filed as a residual in T452's handoff.

## Headline counts

**All figures in this table were measured at `97bad8ed`** (see the tree-qualification block
above; at `c223a16b` and later, `self_only` and `family_only` read 0 for the reason given there).

| | |
|---|---|
| tracked files under `.softhouse/` | 9,645 |
| of them, scripts (`.sh` `.py` `.bash` `.zsh`, or a `#!` first line) | **1,704** |
| of those scripts, ones carrying at least one search | 142 |
| repository-search invocations found in them | **399** |
| **A1 — literal probe, searcher is the ONLY corpus file that carries it** | **2 rows / 2 files** |
| A2 — literal probe, searcher matches *and so do other files* | 33 rows |
| B — probe assembled at run time or otherwise non-literal (the repaired shape) | 131 rows |
| of B, unparsed by the tokeniser (a named blind spot, listed in the transcript) | 23 |
| C — searcher **excludes itself** by an explicit `:!` pathspec ("immunised") | **0** |
| D — search corpus does not contain the searcher | 233 rows |
| every match inside the searcher's own task directory ("family-only") | 3 rows |

**Adjudicated verdict: 4 instruments in `.softhouse/` spell a self-matching probe that changes
what their search reports. All 4 invert. All 4 invert FAIL-CLOSED. 0 invert fail-OPEN
— _among rows whose pattern is a syntactic literal_. See the restatement below: a fifth member
was found in the variable-indirect residual, it is PRESENT-direction and enforced, and it IS a
fail-open. [T452, `F-T447-1`]**
One of the four is `C-T440-1` itself and is repaired by this task; the other three are recorded
below and filed, not edited — they are other tasks' grants.

## The four, each measured

### 1. `capture/t424/instruments/t424-comment-claims-drive.sh` — **REPAIRED HERE**
Probe `zzq-no-such-token-t424`, searched over `.softhouse`, expected **absent**. Present, because
the instrument spelled it. `disagreements=1`, exit 1, against a committed transcript reading
`disagreements=0`. RED `out/T442-C1-RED.txt`; GREEN `out/T424-comment-claims.txt`; red/green
harness `out/T442-C1-REPRODUCTION.txt`. Probe now assembled at run time.

### 2. `reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh:49,51` — **LIVE, inverted**
```
git grep -c -F "zzq-t379-nothing" -- .softhouse/ >/dev/null 2>&1
printf '    git grep -c -F <absent> -- .softhouse/   rc = %s   (1 == a MEASURED zero)\n' "$?"
```
Measured today: **`rc=0`**, and `git grep -l` returns exactly one file — the drive itself. The
line exists to demonstrate that an *absent* pattern over a *real* pathspec returns 1, against a
malformed pathspec returning ≥2; it now prints 0, which is neither, under a legend that says 1
means a measured zero. **Fail-CLOSED / evidence-degrading:** no check reads that status, so no
verdict moves; what breaks is the calibration a reader is asked to trust. `git grep` still
returns 1 for a genuinely absent token, as T440 showed and as this task's repaired CLAIM 3 shows.

### 3. `reviews/t367-review-t363/drive-sweep-failopen.sh:34,44` — **LIVE, inverted**
Arm **B** is captioned *"a selector that IS valid and genuinely finds nothing"* and uses
`zzz-no-such-string-t367`. It does **not** find nothing: measured `rc=0`, two matching files —
the drive and its own transcript `out/DRIVE-SWEEP-FAILOPEN.txt`. The drive's point (B and C are
indistinguishable in the shipped sweep) survives, because the sweep discards the status either
way; the *demonstration* of it no longer stands on a genuinely empty search.

### 4. `reviews/t245-oracle-pin/measure.sh:131` — **LIVE, inverted**
```
echo -n "  CALIB negative  'zzq_nonexistent' @HEAD .softhouse/  : "; git grep -F -l -a "zzq_nonexistent" HEAD -- .softhouse/ | wc -l
```
A calibration whose whole job is to print **0**. It prints **5** today: `measure.sh`, its own
transcript, and three later files that copied the token while quoting the evidence. The positive
half of the calibration (`fineract_gerege`) is unaffected. **Fail-CLOSED in effect** (the
calibration visibly stops calibrating) but the harm is that nothing aborts, so a reader can take
the table below it as calibrated when it is not.

## The rows I looked at and dismissed, and why

`A1` began at 13 rows before the extractor was tightened to take only the **pattern operand** of a
grep-family call. The 11 dismissed were: pathspecs mistaken for probes (`git ls-files
'.softhouse/*.patch'` — `ls-files` takes no pattern); `echo`/`warn` message text containing a
backticked `` `git grep` ``; a `sed` script on the same line as a search; a pattern applied to a
*pipeline*, not the repository; a corpus given by a shell variable (`-- "$GATES"`); and one
`shapes/*.txt` specimen that `cd`s to a `/tmp` path that does not exist. Each was checked by
running the row's own command and comparing the hit set. The tightened extractor keeps two.

## The fail-OPEN half — where I looked, and what I did not find

Direction matters and the two are not symmetric:

* a probe expected **ABSENT** that self-matches → the check fires → **fail-CLOSED**: noisy,
  visible, harmless. All four findings above are this direction.
* a probe expected **PRESENT** that is satisfied by the searcher's own bytes → the assertion
  passes **vacuously** and says nothing about the corpus → **fail-OPEN**, silent. This is the
  dangerous half.

Searched for specifically, three ways:

1. **every A1 row** (searcher is the sole carrier) — a present-assertion here is vacuous by
   construction. Both A1 rows are absent-assertions. **0 fail-open.**
2. **the FAMILY-ONLY flag** — rows where every matching file lies inside the searcher's own task
   directory, i.e. the "claim confirmed by my own artefacts" shape. 3 rows, all three already
   adjudicated above as absent-assertions. **0 fail-open.**
3. **by hand over all 33 A2 rows** in the transcript, reading each row's surrounding three lines
   for what it does with the status. They are enumerations, engine cross-checks and printed
   counts; the present-assertions among them (`acc_gl_journal_entry` 747 files, `fineract_gerege`
   309 files, `\bmain\b` 58 files) are carried overwhelmingly by files other than the searcher.
   **0 fail-open.**

> ### RESTATED BY T452, 2026-08-29 — `F-T447-1`. **THIS IS NOT "ZERO FAIL-OPEN".**
>
> The correct headline is: **0 fail-open among rows whose pattern is a SYNTACTIC LITERAL.** The
> three searches listed above all ran over that population. The rows whose pattern is held in a
> variable were routed to bucket B and counted safe **on syntax alone** — the blind spot this
> file names two paragraphs down, in its own words. T447 re-opened bucket B and narrowed it from
> 131 rows to **14** that actually hold a pattern indirectly; T452 re-ran the whole
> classification with one level of same-file dataflow resolved, in pattern position **and in
> pathspec position**.
>
> **In that residual there is a fifth class member, and it IS a fail-open:**
> **`.softhouse/reviews/a2-33-dec2-rev5/sweep.sh` — the P-72 positive calibration**, pattern
> `$CAL_RE`, enforced at `exit 92`, corpus `-- .softhouse/reviews/a2-33-dec2-rev5` — **the
> searcher's own task directory** — while the sweep it certifies reads `-- .`, the whole tree.
> PRESENT-direction, enforced, family-only **by construction** (the pathspec confines it; no
> corpus can make it otherwise).
>
> **T452 drove it both ways rather than arguing it** (`instruments/t452-a2-33-failopen-drive.sh`,
> transcript `out/T452-A2-33-FAILOPEN.txt`, exit 0):
>
> * **FOR** — a scratch git repo containing **nothing but this script** runs green: corpus 1
>   file, `SWEEP CALIBRATE+: PASS`, 34 patterns reported, `SWEEP-RESULT … calibration=PASS`,
>   **exit 0**. The calibration certifies 34 negatives over a corpus consisting of the searcher.
>   That is the same reader-facing outcome as the deleted-worktree defect the T238 block was
>   written to remove.
> * **AGAINST** — the guard is not unfireable: move the task directory and it does `exit 92`. It
>   is a real guard, on a real property — the reachability of 17 files. It was never a guard on
>   the reachability of the ~9.7k the sweep reads.
>
> **Verdict: a real fail-open, narrowly, on the CORPUS-REACH limb** — the exact limb the T238
> repair exists for. The engine and pattern-language limbs are sound and are kept.
> **Repaired** by a second enforced limb (`exit 94`) that calibrates on the sweep's own corpus
> and requires a match **outside** the searcher's task directory. Driven: the repaired script
> refuses the one-file specimen at `94`, still exits 0 on the real tree, and all 34 patterns are
> byte-identical before and after.
>
> **T452's own fail-OPEN count, and the method**, is in
> `.softhouse/capture/t452-t447-conditions/` — `t452-classify-v2.py`, transcript
> `out/T452-CLASSIFY-V2.txt`, and the handoff `T452-t447-conditions.md`, which states the
> definition of "fail-open" before it counts.

**Zero fail-open instances found.** That is a statement about this search. It looked only at
tracked files under `.softhouse/`, only at grep-family invocations in command position, and it
cannot see: a search split across a continuation line, a pattern held in a variable that was
assigned from a literal earlier (131 such rows are counted SAFE and some may not be), a pathspec
built at run time, `find -exec grep`, a search performed by a non-script, or a search made through
a helper function this census does not know the name of. 23 lines could not be tokenised and are
listed by name in the transcript rather than dropped.

## The shape that did NOT appear, and is worth naming anyway

**`immunised = 0`.** No instrument in `.softhouse/` dodges the self-match by excluding itself from
its own pathspec (`:!path`). That is the *wrong* repair — it hides the instrument from the census
instead of fixing the control, and it silently un-scans everything else under the excluded path.
**No instrument does it BY THAT SPELLING**; recorded so that the next reviewer can tell "nobody
did this" from "nobody looked".

> **NARROWED BY T452 — `F-T447-4`. `immunised = 0` is true of ONE SPELLING.** The census detects
> immunisation only as a `:!path` / `:(exclude)path` **pathspec**, and `cut_at_pipe()` truncates
> every line at the first unquoted `|` before anything else is looked at — so the same dodge
> spelled as a **post-pipe filter** is invisible **by construction**. Measured over the whole
> repository, whole line (T447 `t447-widen-and-immunise.py`; re-measured by T452's
> `t452-classify-v2.py`): `immunised_pathspec` reproduces, and **three rows in two files**
> self-exclude by post-pipe `grep -v`:
>
> ```
> .softhouse/capture/t244-dec2-rev6/sweep-reverify-sound-engines.sh:51  filters out 't244-dec2-rev6'
> .softhouse/capture/t244-dec2-rev6/sweep-reverify-sound-engines.sh:58  filters out 't244-dec2-rev6'
> .softhouse/reviews/a2-31-dec2-rev4/probe-sweep.sh:27  filters out 'a2-31-dec2-rev4/probe-sweep.sh'
> ```
>
> Each excludes its own task directory or its own path from its own results — the wrong repair,
> with the same consequence. So the sentence that over-generalised is the *conclusion*, not the
> count: the pathspec figure is correct and reproduces.
>
> **Positive side note, kept:** T447's widening pass measured **0** candidate searchers outside
> `.softhouse/` in the whole repository, so this census's corpus restriction costs nothing —
> something the sweep asserted but did not measure.

## Named blind spots of this census — TWO ADDED BY T452

The five in the paragraph above stand. Two more, both found by T447, both about the census
measuring the rows with an instrument that is not the rows':

* **`matching_files()` discards the row's own flags** (`F-T447-5`). It re-runs **every**
  candidate as `git grep -l -F -e <lit>` — fixed-string and case-**sensitive**. For a row whose
  own command is `git grep -c -I -i -E`, that is a different search. Measured on
  `a2-33-dec2-rev5/sweep.sh`: the census reports **2** matching files where the row's own command
  matches **11**. Since the A1/A2 boundary is drawn by this function, `self_only` and
  `self_plus_others` are computed under a matcher that is not the row's matcher. It does not move
  any of the four members adjudicated above — each was re-checked by hand — but the split is
  measured with the wrong instrument and the next reader should know.
  `t452-classify-v2.py` parses `-i/-E/-F/-w/-P` off the row and replays them.
* **the PATHSPEC is variable-indirect too, not only the pattern.** Any pathspec containing a `$`
  was marked built-at-run-time and the row dropped. T452 hit this from the other side: hoisting a
  hard-coded task directory into `SELF_DIR=` — an ordinary tidy-up — would have made the
  `a2-33` row **invisible to the census that found it**. A repair that hides the repaired row
  from its own instrument is not a repair. `t452-classify-v2.py` resolves one level of same-file
  dataflow in pathspec position as well, and the `a2-33` drive asserts the repaired row is still
  visible.
