# T442 — the C-T440-1 class, swept and adjudicated

**Instrument** `instruments/t442-selfmatching-probe-census.py` · **transcript** `out/T442-CLASS-SWEEP.txt`

> **The class.** An instrument that searches the repository with a probe token **spelled as a
> literal in its own tracked source** changes meaning the moment it is committed, because the
> search then finds the searcher. `t424-comment-claims-drive.sh` did exactly that and shipped a
> transcript its own committed code cannot produce (`C-T440-1`).

## Headline counts

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
what their search reports. All 4 invert. All 4 invert FAIL-CLOSED. 0 invert fail-OPEN.**
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
Nobody has done it yet; recorded so that the next reviewer can tell "nobody did this" from
"nobody looked".
