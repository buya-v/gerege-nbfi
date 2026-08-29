# T447 — independent review of T442 (`softhouse/T442-t440-conditions`, tip `c223a16b`)

**Reviewer** T447 · **branch** `softhouse/T447-review-t442` · **host** macOS 25.5.0 arm64,
`bash 3.2.57(1)`, `git 2.50.1 (Apple Git-155)`, `/usr/bin/grep` BSD 2.6.0-FreeBSD, `python3`.
All scratch under `/tmp/t447`, **outside the repository**. Diffs measured three-dot
(`git diff main...softhouse/T442-t440-conditions`); merge-base `b102875c`, six commits on the
branch, tip `c223a16b` — confirmed, and the driver's later `main` commits are not attributed here.

**Every number in this file was produced by running something on this host.** Where I reproduce
T442's number I say by what instrument; where I differ, that difference is the finding. Two of
my own hypotheses were falsified by my own drives and both runs are kept.

---

# VERDICT: **APPROVED WITH CONDITIONS**

The MAJOR condition — `C-T440-1` — is genuinely closed, and closed on the *right* property. I
reproduced the RED from committed bytes in my own clone, reproduced the GREEN in a second clone,
and proved the red/green harness non-vacuous with two mutations the author did not run. The K8
arithmetic is right to the last cell. `F-T442-1` is **upheld: the author is right and T440 was
wrong**, on evidence I measured myself. Scope is clean, no money path is touched.

Three things must not go to `main` as written: an erratum that rejects a **correct** reviewer
finding on a search artefact and would leave the defect in place; a headline class-sweep count
that does not reproduce on the tree it ships on; and a `0 fail-OPEN` claim whose search
demonstrably did not cover the row I found.

| # | finding | severity |
|---|---|---|
| `F-T447-1` | `0 fail-OPEN` is not *established*: one enforced PRESENT-assertion in the family-only shape sits in the variable-indirect blind spot and was never adjudicated | **MAJOR** |
| `F-T447-2` | T442 overturns T440's correct `C-T440-2` sub-claim on a search artefact; the wrong K8 decomposition is in **two** sites, and the erratum's acceptance test cannot see the second | **MAJOR** |
| `F-T447-3` | the published class-sweep counts do not reproduce on the branch tip — the census is a member of the class it censuses | **MAJOR** |
| `F-T447-4` | `immunised = 0` holds only for the `:!`-pathspec spelling; three rows in two files self-exclude by post-pipe `grep -v`, structurally invisible to the census | **MINOR** |
| `F-T447-5` | the census's `matching_files()` ignores the row's own flags, so its hit sets are not the row's hit sets (`a2-33`: census says 2 files, the row's own command says 11) | **MINOR** |
| `F-T447-6` | `C-T440-5`'s repaired guard has **no owner**: 0 occurrences live, 5 in an unapplied patch, and no open task applies it (P-45) | **LOW** |
| `F-T447-7` | the C-T440-1 comment block cites the census as `…-census.sh`; the file is `.py` — 2 occurrences, both in the block added to close C-T440-1 | **LOW** |

---

## 0 · What I re-derived and CONFIRMED

Listed first, because the bulk of T442 survives independent re-derivation.

| claim | my instrument | result |
|---|---|---|
| RED: shipped instrument on committed bytes → `disagreements=1`, exit 1 | fresh `git clone --no-local` of the repo, `git checkout --detach b102875c`, **0 dirty paths**, ran the drive | **exit 1, `disagreements=1`** — `out/T447-C1-RED-my-clone.txt` |
| GREEN: repaired instrument on committed bytes, clean detached clone | second fresh clone, `--detach origin/softhouse/T442-t440-conditions` (`c223a16b`), 0 dirty | **exit 0, `disagreements=0`** — `out/T447-C1-GREEN-my-clone.txt` |
| the reproduction harness passes | ran `t442-c1-reproduction-drive.sh` in my clone | **exit 0**, `T442-C1-REPRODUCTION-RESULT: disagreements=0` — `out/T447-REPRO-drive-my-clone.txt` |
| the class-sweep transcript | re-ran `t442-selfmatching-probe-census.py` at `97bad8ed` in my own clone | **byte-for-byte identical** to the shipped transcript below the repo-path line — `out/T447-CLASS-SWEEP-byte-diff-vs-shipped.txt` is **empty** |
| `scripts=1704` | independent enumeration of tracked candidate searchers over the **whole repo** | **1704**, and **0** of them outside `.softhouse/` — the corpus restriction costs nothing |
| `immunised=0` (`:!` pathspec) | my own detector over the whole line, whole repo | **0** — reproduces (but see `F-T447-4`) |
| K8 = `13 + 10 + 6 = 29` | hand count on `casualty-sweep.sh` + re-run of both drive arms | **16** `sel` calls, **3** with no `\|` → **13**; **10** `SWEEP_*=$((…))` lines; **3** distinct counters; **3** at `8fa677a6`; **6** residual; total **29** = the census's printed `K8 SITES: 29` |
| the three live unowned class members | `git grep` on `main` (`4e48b7e8`) | all three confirmed at the exact lines claimed — see §3 |
| `F-T442-1` (`C-T440-6` does not reproduce) | ran `t381-red-drives.sh` both ways on my tree | **`BEFORE_REF=main` → exit 2 "SAME FILE"**; **`BEFORE_REF=964b532e` → exit 4 at D-R2**. Author upheld — see §5 |
| `F-T424-N1` is filed nowhere | `grep -c` on `main` | `F-T424-N1` × **2** in `tasks.json` (both inside task descriptions), **0** in `obligations.md`, **0** in `gates.md` |
| `T445` holds `conformance.sh` | `tasks.json` | `T445` `in_progress`, `files_hint` includes `.softhouse/conformance.sh` — the contention claim is true |
| GNU `tee` still `[UNVERIFIED]` | grep for `tee`/`GNU` over the diff | **no claim made**; the only "GNU" strings are `/usr/bin/grep --version` output. Correctly left open |
| scope | `git diff --name-only main...HEAD` | **every** changed path is under `.softhouse/capture/t424/` or the T442 handoff. T442's grant in `tasks.json` is `['.softhouse/capture/t424/']` — clean |
| money non-negotiables | grep the added lines for float/decimal/money shapes | **no money path, no vector, no schedule figure touched**. The only decimal-looking strings are tool version numbers |

### The reproduction harness is NON-VACUOUS — verified by two mutations the author did not run

A red arm that cannot fail is the defect it exists to catch (P-22). I mutated
`t442-c1-reproduction-drive.sh` in `/tmp` and re-ran it against my clone:

```
MUT1  the ARM B injection NEUTERED (python writes the file back unchanged)
      -> the drive REFUSES, exit 2   (git commit finds nothing to commit)   out/T447-NONVACUITY-MUT1-injection-neutered.txt

MUT2  the injection LANDS but injects only a comment -- the defect is NOT re-introduced
      -> exit 1, T442-C1-REPRODUCTION-RESULT: disagreements=4               out/T447-NONVACUITY-MUT2-defect-not-injected.txt
         specimen token present in the SPECIMEN clone   expected=0 actual=1 *** DISAGREES
         ARM B disagreements > 0                       expected=yes actual=no *** DISAGREES
         ARM B exit                                    expected=1 actual=0  *** DISAGREES
         ARM B: the self-spelling check FIRED          expected=1 actual=0  *** DISAGREES
```

**ARM B cannot pass vacuously.** Reproduction: copy the drive to `/tmp`, replace the
`src[hits[0]] = "g_tok='%s' …"` line with `pass`, run with `T442_REPO=<clone>`.

### Byte-reproducibility of the re-captured transcript — not achieved, and not achievable

The task brief asks me to confirm the shipped transcript "regenerates byte-for-byte". It does
not, and it **cannot**: the run-time probe is a nonce and the `subject:` line prints an absolute
path. The author states this plainly and does not claim otherwise. My regenerated GREEN differs
from the shipped one in exactly four places — the added header block, the `subject:` absolute
path, the probe nonce, and the `ACTUAL EXIT=0` footer. **Every graded line, the `sha256
a6888119b0ae1ca1` of the subject and the `5500` line count are identical.** I record this as
*not a finding*: the pre-repair transcript was not byte-reproducible either (same `subject:`
line), the property that failed was verdict-reproduction-from-committed-bytes, and that property
now holds in two independent clones. The residual is that the machine check for it
(`t442-c1-reproduction-drive.sh`) is on no automatic path — see `F-T447-6`.

---

## 1 · `F-T447-1` — MAJOR. `0 fail-OPEN` is not established

**Evidence** `.softhouse/reviews/t447-review-t442/out/T447-VARINDIRECT.txt`,
`out/T447-FAILOPEN-A2-33.txt`, `out/T447-A2-33-HYPOTHESIS-FALSIFIED.txt`
**Instruments** `instruments/t447-variable-indirect-probes.py`, `instruments/t447-failopen-a2-33.sh`

T442 concedes its own blind spot in writing: *"The census's 131 'runtime' rows are counted safe on
syntax alone. A pattern held in a variable that was assigned from a literal earlier in the same
file would land there and would still be in the class."* I went and looked.

### First, the good news: the blind spot is 14 rows, not 131

My instrument re-opens T442's RUNTIME bucket (parsed 131, transcript declares 131 — refuses if
they differ), resolves one level of same-file dataflow, and partitions:

```
T447-VARINDIRECT-RESULT: reopened=131 novar=117 resolved=3 unresolved=11 class_members=3
```

* **117 rows carry no `$VAR` in pattern position at all** — they are in RUNTIME for other reasons
  (`ls-files` takes pathspecs not patterns; a literal under 2 chars; no self-matching literal).
  Not the blind spot.
* **11 rows** hold the pattern in a variable I could not resolve to a same-file literal. **I read
  every one by hand.** All are safe, and instructively so: `t371 $ABSENT` and `t388
  $CALIB_NEG_STR` are assembled at run time from `$$`/`$RANDOM`/`date` (the correct shape, already
  the house pattern); `t371 $BAD='['` is a malformed-pattern control; `t424 $g_tok` is T442's own
  repair; `a2-31 $pat` and `t244 $p` are loop variables over literal lists, both piped through a
  self-excluding `grep -v`; `a2-33 $ANTI_RE` is assembled by `printf 'zzq%snoSUCHtokenzzq' 'T238'`;
  `t440 $SENT` is extracted from the drive under test at run time. **0 fail-open.**
* **3 rows resolve to a same-file literal and self-match.** One (`t411 …reachability.sh:59
  $GREP='/usr/bin/grep'`) is a **false positive of my own instrument** — `$GREP` is the command,
  not the pattern; recorded because a review that hides its own misfires is not a measurement. One
  (`t424-comment-claims-drive.sh:161 $g_literal='#!/usr/bin/env bash'`) is T442's own deliberate
  demonstration arm. The third is the finding.

### The finding: `.softhouse/reviews/a2-33-dec2-rev5/sweep.sh:61`

```sh
CAL_RE='a2-33'
CAL_N=$(git grep -c -I -i -E "$CAL_RE" -- .softhouse/reviews/a2-33-dec2-rev5 | awk -F: '{s+=$NF} END{print s+0}')
if [ "${CAL_N:-0}" -lt 1 ]; then … exit 92 ; fi     # a PRESENT assertion, ENFORCED
…
out=$(git grep -n -I -i -E "$re" -- . 2>&1)          # the sweep proper: the WHOLE TREE
```

This is the P-72 **positive calibration** — *"Prove the instrument can find something BEFORE it
may report nothing"* — and it is enforced at exit 92. Measured (`out/T447-FAILOPEN-A2-33.txt`,
exit 0):

```
ARM A  as shipped                       : 73 matches across 11 files
ARM B  files OUTSIDE its own task dir   : 0        <- FAMILY-ONLY
ARM C  matches in the searcher alone    : 7        <- the searcher alone would satisfy it
ARM D  calibration corpus 17 tracked files vs the sweep's 9,730   <- a strict subset
ARM E  control, runtime-assembled absent token -> rc 1            <- engine is not matching all
```

T442's census prints, for exactly this shape:

> `*** EVERY match lies inside the searcher's OWN task directory: a PRESENT-assertion here would
> be satisfied only by the author's own artefacts — the VACUOUS-PASS / fail-OPEN shape.
> Adjudicate the direction.`

T442 flagged **3** family-only rows and adjudicated all three as ABSENT-assertions. **This is a
fourth, it is PRESENT-direction and enforced, and it was never flagged** — because the pattern is
spelled `$CAL_RE`, so the row went into the bucket counted safe on syntax alone. And the failure
it is supposed to catch is a **corpus-reach** failure: `sweep.sh`'s own header records that a
hard-coded, later-deleted worktree path made the sweep print `(no hits)` for all 34 patterns and
exit 0. A calibration whose corpus is the task's own 17 files cannot demonstrate that the sweep's
9,730-file corpus is reachable.

### What I got wrong, kept on the record

My first hypothesis was that this row is **vacuous** — satisfied by the searcher plus one sibling.
My own drive **falsified it** (`out/T447-A2-33-HYPOTHESIS-FALSIFIED.txt`, `disagreements=1`): ten
sibling files carry the token independently. The "2 files" I started from is the census's number,
and the census got it by re-running every candidate with `git grep -l -F` **case-sensitively**,
which is not this row's command (`-I -i -E`). See `F-T447-5`.

**So `0 fail-OPEN` is not falsified — it is not established.** The search behind it did not reach
this row, and by the census's own criterion this row requires adjudication.

**Condition.** Restate the headline in `T442-CLASS-SWEEP-ADJUDICATION.md`, the handoff **and the
marker file** as *"0 fail-open among rows whose pattern is a syntactic literal; the
variable-indirect residual is 14 rows, adjudicated separately"*, and adjudicate
`a2-33-dec2-rev5/sweep.sh:61` explicitly. The 14-row figure and the per-row readings above may be
taken from this review; the work of narrowing 131 → 14 is done.

**Reproduction.** `bash .softhouse/reviews/t447-review-t442/instruments/t447-failopen-a2-33.sh`
(exit 0 = the finding reproduces) and
`python3 .softhouse/reviews/t447-review-t442/instruments/t447-variable-indirect-probes.py <T442-CLASS-SWEEP.txt>`.

---

## 2 · `F-T447-2` — MAJOR. T442 overturns a **correct** reviewer finding on a search artefact

**Evidence** `out/T447-K8-HANDOFF-SITE.txt` · **instrument** `instruments/t447-k8-handoff-site.sh`
(exit 0 = the finding reproduces)

`ERRATUM-K8-DECOMPOSITION.md` says:

> *"`git grep` for `all sixteen` under `.softhouse/handoff/` returns only unrelated T39/T242/T379
> matches, and T424's own handoff `T424-t408-conditions.md` states the K8 total (29) without
> decomposing it. So there is **one** site to correct, not two."*

`.softhouse/handoff/T424-t408-conditions.md:233-236` reads:

> **All 29 adjudicated, and none is a live defect.** **Sixteen** are the `sel` calls, in the wide
> list only because each carries a `|` inside its own quoted ERE … **Eight** are `SWEEP_*=$((…))`
> counters, matched on the `$(` of an arithmetic expansion, which is not a subshell. **Six** are
> parent-side assignments …

That **is** the `16 + 8 + 6` decomposition. It is spelled as **words in running prose**, so
`git grep 'all sixteen'` — a search for the adjective phrase used in `AUDIT-CLASS.md`'s *table
cell* — could never have matched it. My drive runs T442's own recipe and confirms it returns 0,
then finds all three cardinals at lines 233 / 235 / 236.

**"Not found" is a statement about the search, never about the world.** T442 invokes that rule
correctly for its own class sweep and then breaks it here, against a reviewer who was right.

The consequence is operational, not rhetorical: the erratum's acceptance test is

```
git grep -c 'all sixteen `sel' -- …/AUDIT-CLASS.md   # must be 0
git grep -c 'x8\|×8'          -- …/AUDIT-CLASS.md   # must be 0
```

Its Acceptance-test block mentions the handoff **0** times (measured). Applying the erratum as
written therefore goes **green** with the wrong decomposition still on `main`.

**Condition.** Correct the erratum: **two** sites, not one. Add
`.softhouse/handoff/T424-t408-conditions.md:233-236` with paste-ready replacement text, and add
an acceptance check that covers it. T440's `C-T440-2` stands as written.

**What T442 got right and keeps.** The arithmetic is right in every cell and I re-derived all of
it by hand: 16 `sel` calls in the file, `S1`/`S3`/`S7` carry no `\|`, 16 − 3 = 13; 10 increment
lines today, 3 distinct counters, 3 lines at `8fa677a6`; 6 residual; **13 + 10 + 6 = 29**. The
second wrong `8` at `AUDIT-CLASS.md:102` (`×8` under `K1+K7`) is real and T440 did not name it —
**that** half of T442's contribution is a genuine improvement on the review.

---

## 3 · `F-T447-3` — MAJOR. The class-sweep counts do not reproduce on the tree they ship on

**Evidence** `out/T447-CLASS-SWEEP-rerun-at-97bad8ed.txt` vs
`out/T447-CLASS-SWEEP-rerun-at-branch-tip.txt`

```
at 97bad8ed (where the transcript was taken, and it reproduces BYTE-FOR-BYTE):
  scripts=1704 searches=399 self_only=2 self_only_files=2 self_plus_others=33
  family_only=3 unparsed=23 runtime=131 immunised=0 elsewhere=233

at c223a16b (the branch TIP — the tree the record ships on):
  scripts=1707 searches=401 self_only=0 self_only_files=0 self_plus_others=35
  family_only=0 unparsed=23 runtime=133 immunised=0 elsewhere=233
```

**Cause, measured.** By publishing the census transcript, the adjudication and the handoff, T442
made three new tracked carriers of the very probes it censuses:

```
$ git grep -l -F "zzq-t379-nothing" -- .softhouse      # at c223a16b
.softhouse/capture/t424/out/T442-CLASS-SWEEP-ADJUDICATION.md
.softhouse/capture/t424/out/T442-CLASS-SWEEP.txt
.softhouse/handoff/T442-t440-conditions.md
.softhouse/reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh
```

So the two `A1` rows acquire non-self carriers and demote to `A2`; `family_only` collapses to 0
because the new carriers lie outside the searchers' task directories. **The census is a member of
the class it censuses** — a record whose measurement changes the moment it is committed. That is
`C-T440-1`'s shape, one level up.

**Mitigation, and why this is not a repeat of `C-T440-1`.** The transcript's header **names its
commit** (`commit : 97bad8ed9c73…`), so it is not a false record and it reproduces exactly there
— I verified byte equality. What is unqualified is everything that *quotes* it: the
`T442-CLASS-SWEEP-ADJUDICATION.md` headline table (`A1 … 2 rows / 2 files`, `family-only … 3
rows`), the handoff's `T442-CLASS-SWEEP-RESULT` block, and the marker file's *"**4** instruments …
all 4 fail-CLOSED, 0 fail-OPEN"*. A reader who re-runs the census on `main` after merge gets
`self_only=0 family_only=0` and can reasonably conclude the class is empty.

**Condition.** Pin the counts to `97bad8ed` wherever they are quoted (adjudication table, handoff,
marker file), and state the direction of drift: *"re-running at or after `c223a16b` returns
`self_only=0 family_only=0` because this transcript is itself now a carrier of the probes; the
four members are unchanged and appear as `A2` rows."* Reproduction: check out `97bad8ed` and
`c223a16b` in separate clones and run `t442-selfmatching-probe-census.py` in each.

---

## 4 · `F-T447-4` — MINOR. `immunised = 0` is true of one spelling only

**Evidence** `out/T447-WIDEN-AND-IMMUNISE.txt` · **instrument** `instruments/t447-widen-and-immunise.py`

The census detects immunisation only as a `:!path` / `:(exclude)path` **pathspec**, and its
`cut_at_pipe()` truncates every line at the first unquoted `|` before anything else is looked at.
So the same dodge spelled as a post-filter is invisible **by construction**. Measured over the
whole repository, whole line:

```
T447-WIDEN-RESULT: tracked=9734 scripts=1704 inside_softhouse=1704 outside_softhouse=0
                   immunised_pathspec=0 immunised_postpipe=3 immunised_unresolved=0
```

```
.softhouse/capture/t244-dec2-rev6/sweep-reverify-sound-engines.sh:51  filters out 't244-dec2-rev6'
.softhouse/capture/t244-dec2-rev6/sweep-reverify-sound-engines.sh:58  filters out 't244-dec2-rev6'
.softhouse/reviews/a2-31-dec2-rev4/probe-sweep.sh:27  filters out 'a2-31-dec2-rev4/probe-sweep.sh'
```

Each excludes its own task directory or its own path from its own results — the *wrong repair*
the census exists to name, with the same consequence (everything else under the filtered name
stops being reported). The pathspec count of **0 is correct and I reproduce it**; what
over-generalises is the conclusion drawn from it: *"Nobody has done it yet; recorded so that the
next reviewer can tell 'nobody did this' from 'nobody looked'."*

**Condition.** Narrow the sentence to the mechanism searched, and record the three post-pipe rows
(they are measured above, so this is a paste). **Positive side note, worth keeping:** my widening
pass shows **0** candidate searchers outside `.softhouse/` in the whole repository — T442's corpus
restriction costs nothing, which the sweep asserted but did not measure.

---

## 5 · `F-T442-1` adjudicated — **the author is right, T440 was wrong**

**Evidence** `out/T447-FT442-1-BEFORE_REF-main.txt`, `out/T447-FT442-1-BEFORE_REF-964b532e.txt`

Measured on my tree, not taken from either account:

```
main:…/casualty-sweep.sh   blob b7893bd09e02a4da…
HEAD:…/casualty-sweep.sh   blob b7893bd09e02a4da…      IDENTICAL

BEFORE_REF=main       -> exit 2   "DRIVE ABORT (exit 2): BEFORE and AFTER are the SAME FILE."
                                  D-R2 (line 119+) is never reached; the guard is at line 87
BEFORE_REF=964b532e   -> exit 4   "D-R2 patch: expected 1 anti-calibration search line in
                                   BEFORE, found 0"
```

`t381-red-drives.sh` defaults `BEFORE_REF=main`, `AFTER_REF=HEAD`, and compares the two blobs of
`casualty-sweep.sh` **before** D-R2 runs. The verdict is therefore a pure function of whether the
tree's `main` and `HEAD` carry the same blob of that file. **T424's wording is true on the merged
tree; T440's is true on a tree where they differ; neither says so.**

I can add the mechanism T442 did not name. `casualty-sweep.sh` last changed at `1c71a1a2`, which
reached `main` with `c5a8b5c5 "Merge T424"`. `5c22d5e5 "Merge T440"` landed *after* it, so all of
T440's working commits (`9ddaf6d8`…`afe071d0`) predate the T424 merge — while T440 was measuring,
`main` did **not** yet carry T424's copy of the file and T440's own HEAD did. That is exactly the
tree on which the drive gets past the SAME-FILE guard and dies at D-R2 with exit 4. T440's branch
has since been deleted (`git rev-parse` fails for it in a fresh clone), so its tree cannot be
re-run — which is itself the argument for the tree-qualified wording T442 supplies.

**Upheld. `C-T440-6` is withdrawn; T424's original sentence stands, once tree-qualified.** The
substantive claim both accounts share — the drive cannot be run to completion on any available
ref, so `FU-T386-7`'s guard has nothing to grade — is confirmed by both of my runs.

---

## 6 · The three live, unowned class members — all three CONFIRMED, on `main` (`4e48b7e8`)

Measured with `git grep`, not read from the adjudication. **These are live defects on `main` that
no task owns; this review is the record that files them.**

| # | site | claimed | **measured by me** |
|---|---|---|---|
| 1 | `reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh:49,51` | probe `zzq-t379-nothing`, `rc=0`, sole match is the drive | `git grep -c -F "zzq-t379-nothing" -- .softhouse/` → **rc 0**; `git grep -l` → **1 file, the drive itself**. Its legend one line below reads `(1 == a MEASURED zero)` and it prints **0**. **CONFIRMED.** Direction ABSENT → the printed calibration is wrong, no verdict moves |
| 2 | `reviews/t367-review-t363/drive-sweep-failopen.sh:34,44` | arm B *"genuinely finds nothing"*, `rc=0`, 2 files | `git grep -l -F 'zzz-no-such-string-t367' -- .softhouse/` → **2 files**: the drive and `out/DRIVE-SWEEP-FAILOPEN.txt`. **CONFIRMED.** The drive's point (B and C indistinguishable) survives — 128 still differs from 0 — but its arm B no longer stands on an empty search |
| 3 | `reviews/t245-oracle-pin/measure.sh:131` | CALIB negative must print **0**, prints **5** | `git grep -F -l -a "zzq_nonexistent" HEAD -- .softhouse/ \| wc -l` → **5** (`t304` evidence tsv, `t323` evidence tsv, `T245.md`, `measure-output.txt`, `measure.sh`). **CONFIRMED.** |

Line numbers verified exactly as claimed. **One addition:** `measure.sh` has a *second*
anti-calibration site at **line 119** (`len(re.findall(b'zzq_nonexistent', pre))`) that T442 does
not mention; it scans a captured buffer rather than the tree, so it is not degraded, but a filing
that names only `:131` under-describes the file.

**Rating, and one wording disagreement.** T442 calls all four *"fail-CLOSED"*. For members 2 and 3
that is generous: no code reads the status, so nothing closes — they are **unenforced and
evidence-degrading**, and their degradation is silent to any automated consumer. T442 says as much
in the same sentence (*"the harm is that nothing aborts, so a reader can take the table below it
as calibrated when it is not"*), so this is a labelling nit, not a substantive disagreement.
**All three need filing as work; none is in `tasks.json` today.**

---

## 7 · `F-T447-6` — LOW. The `C-T440-5` guard has no owner (P-45)

**Measured on `main`:** `T381_DRIVE_INNER` occurs **0** times in
`.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh` and **5** times in
`.softhouse/capture/t424/patches/FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch`.
`FU-T386-7` occurs **1** time in `tasks.json`, inside `T424`'s description — and `T424` is
`merged`. **No open task applies this patch.**

I ran `t442-t440-lows-drive.sh` myself in my clone: **exit 0, `T442-LOWS-RESULT: disagreements=0`**
(`out/T447-LOWS-rerun.txt`), all nineteen arms as declared, including RED `T381_DRIVE_INNER=1 →
exit 0` (bypassed) → GREEN `→ exit 2` (refused), the forged `t424-inner:1` → exit 2, **and the
healthy control (clean body → exit 0)**, which is the arm that stops this being a guard that
refuses everything. The drive also *asserts* `the amended guard is NOT applied to the live file
expected=0` — the author bakes his own disclosure into a checked arm, which is the right way to
disclose it.

**I accept the disposition.** The artefact under condition *is* the patch; repairing the patch is
repairing the subject, and closing the surface while nothing runs is when it is cheapest. **But a
guard wired to nothing enforces nothing.** The residual is ownership, not correctness.

**Condition (LOW).** The driver must give the patch an owner — a `tasks.json` entry that applies
`FU-T386-7-…AMENDED-BY-T424.patch` (or formally retires it) — otherwise the parent-pid-bound
marker never runs. T442 could not do this: `tasks.json` is outside its grant.

---

## 8 · `F-T447-5` — MINOR. The census's hit sets are not the rows' hit sets

`matching_files()` re-runs **every** candidate as `git grep -l -F -e <lit>`, discarding the row's
own flags. For `a2-33-dec2-rev5/sweep.sh:61`, whose command is `git grep -c -I -i -E`, the census
would report **2** files where the row's own command matches **11**. The A1/A2 boundary is drawn
by this function, so `self_only=2` / `self_plus_others=33` are computed under a matcher that is
not the row's matcher. It happens not to move the four adjudicated members — I checked all three
family-only rows and the A2 present-assertions by hand — but the split is measured with the wrong
instrument and the next reader should know. **Condition:** record the limitation in the census's
own "blind spots" block, where the other five are already named honestly.

## 9 · `F-T447-7` — LOW. A citation to a file that does not exist

`t424-comment-claims-drive.sh:30` and `:135` both name the class census as
`t442-selfmatching-probe-census.**sh**`. The file is `t442-selfmatching-probe-census.**py**`. Two
occurrences, both inside the comment block added to close `C-T440-1`. Reproduction:
`git grep -c 'selfmatching-probe-census.sh' -- .softhouse` → **2**.

---

## 10 · The deferrals — every one is a grant problem, and nothing vanished

Checked against `tasks.json`, where T442's `files_hint` is `['.softhouse/capture/t424/']`:

| deferred | where it lives | genuine grant problem? |
|---|---|---|
| `AUDIT-CLASS.md` correction (`C-T440-2`) | `.softhouse/capture/t402-t386-conditions/` | **yes** — outside grant. Paste-ready text supplied |
| `casualty-sweep.sh` narrowed sentence (`C-T440-4`) | `.softhouse/capture/t363-oracle-baseline/instruments/` | **yes** — outside grant. Replacement printed verbatim in the transcript |
| `conformance.sh` (`C-T440-3`) | `.softhouse/conformance.sh` | **yes**, twice over — outside grant **and** `T445` is `in_progress` with it in `files_hint` (verified) |
| `FU-T424-N1` → `tasks.json` | `.softhouse/tasks.json` | **yes** — outside grant. Verified absent: `F-T424-N1` ×2 in `tasks.json` (descriptions only), ×0 in `obligations.md`, ×0 in `gates.md` |
| the three other class members | `reviews/t379…`, `reviews/t367…`, `reviews/t245…` | **yes** — other tasks' directories. All three re-measured above |
| marker file keeps a now-false filename | `capture/t424/out/…TRANSCRIPT-IS-NOT-REPRODUCIBLE.md` | **yes** — renaming needs the same commit to update `tasks.json`. Banner corrected inside; the file opens with `✅ RESOLVED BY T442` and explains the kept name. Acceptable |
| GNU `tee` | — | **correctly left `[UNVERIFIED]`**; no claim made |

**Nothing silently vanished.** Each deferral carries paste-ready text and an acceptance test. The
one exception is `F-T447-2`: the `AUDIT-CLASS.md` erratum is filed with an acceptance test that
does not cover the second site, so *that* deferral is incomplete as written.

---

## 11 · The bar

Run with `bash`, never `sh`/`zsh`; scratch in `/tmp/t447`, outside the repository; on the
committed review tree. **Presence of the probe line was tested before its value was read** —
`grep -c 'probe = '` first, because absence is a harness failure and is not `down`.

```
BAR TRANSCRIPT : out/T447-BAR.txt
grep -c 'probe = ' → 1          (PRESENCE tested first; absence would have been a harness failure, not `down`)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
all 16 wrong ledger implementations DIED through this harness, not by hand.
BAR EXIT=0
```

No money path, no vector, no schedule figure is touched by this branch or by this review; the
whole diff is instruments, transcripts and prose.

**The bar refused my first attempt, and that is recorded rather than hidden.** My
`t447-k8-handoff-site.sh` hard-coded the path of `ERRATUM-K8-DECOMPOSITION.md`, which exists only
on the branch under review, so `guard_dead_path_frontier` refused: `T316-DEADPATH-FRONTIER:
REFUSED rows=109 pinned=108 added=1 removed=0`, **BAR EXIT=2**. The guard's own prescription is
*"make the instrument REFUSE when no candidate resolves"* rather than pin the row, so the erratum
is now a **required argument** and the drive exits 2 without it (verified: `NO-ARG EXIT=2`). Same
repair T440 applied to its own hard-coded path (`045e509b` on `main`). The run above is the
re-run, on the clean committed tree, with the frontier back at 108.

---

## 12 · Conditions, restated for the driver

1. **`F-T447-2` (MAJOR)** — correct `ERRATUM-K8-DECOMPOSITION.md`: **two** sites, not one. Add
   `.softhouse/handoff/T424-t408-conditions.md:233-236` with replacement text and an acceptance
   check that reaches it. T440's `C-T440-2` stands.
2. **`F-T447-3` (MAJOR)** — pin the class-sweep counts to `97bad8ed` in the adjudication table,
   the handoff and the marker file, and state the drift at the tip (`self_only=0 family_only=0`).
3. **`F-T447-1` (MAJOR)** — restate `0 fail-OPEN` as *"0 among literal-pattern rows"*, record that
   the variable-indirect residual is **14** rows (not 131), and adjudicate
   `a2-33-dec2-rev5/sweep.sh:61` — an enforced PRESENT-assertion in the family-only shape.
4. **`F-T447-4` (MINOR)** — narrow the `immunised = 0` sentence to the `:!`-pathspec mechanism and
   record the three post-pipe self-exclusions.
5. **`F-T447-5` (MINOR)** — add `matching_files()`'s flag-blindness to the census's named blind
   spots.
6. **`F-T447-6` (LOW)** — give the `FU-T386-7 …AMENDED-BY-T424` patch an owner in `tasks.json`, or
   retire it. Driver-only work.
7. **`F-T447-7` (LOW)** — fix the two `…-census.sh` citations to `…-census.py`.
8. **Filing, driver-only** — `FU-T424-N1`, and the three live class members
   (`t379-anticalibration-drive.sh:49,51`, `t367 drive-sweep-failopen.sh:34,44`,
   `t245-oracle-pin/measure.sh:131` **and `:119`**) need `tasks.json` entries. T442 cannot add
   them.

Nothing here re-opens `C-T440-1`, the K8 arithmetic, or `F-T442-1`. Those are closed on evidence I
reproduced myself.
