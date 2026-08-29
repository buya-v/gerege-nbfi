# T440 — INDEPENDENT review of T424 (`softhouse/T424-t408-conditions`)

**VERDICT: `APPROVED WITH CONDITIONS`** — six conditions, one MAJOR, two MINOR, three LOW.
Every condition is driven; every clean result below names the instrument that produced it.

Reviewer: T440, branch `softhouse/T440-review-t424`.
Subject: `git diff main...softhouse/T424-t408-conditions` at `a504b59d`, and T424's handoff read
**from the branch** (`git show softhouse/T424-t408-conditions:.softhouse/handoff/…`).

**Nothing below is inherited.** Every cardinal T424 states that I rely on, I re-derived with an
instrument I wrote, from primitives, before reading T424's transcript for it. My instruments are
in `instruments/`, my transcripts in `out/`. Host: macOS 25.5.0 arm64, `bash 3.2.57(1)`,
`git 2.50.1 (Apple Git-155)`, `/usr/bin/grep` BSD, `/usr/bin/tee` BSD. All scratch — including two
`git worktree` checkouts and one throwaway git repo — was created under `/tmp`, never inside the
repository, so `guard_no_narrow_catch_in_capture_rigs` (which walks recursively) was not tripped:
both bar runs report `EXCLUDED 0 other checkout root(s): none`.

---

## 1. Verdict at a glance

| # | brief item | outcome |
|---|---|---|
| 1 | true cause of `F-2`, both halves | **T424 CONFIRMED**, independently re-derived |
| 2 | `pipefail` returns the rightmost non-zero | **T424 CONFIRMED** from shell behaviour; placement right; one over-broad sentence → `C-T440-4` |
| 3 | buffered-writer guard, four matrices | **all four reproduce**; construction sound; one env-bypass surface → `C-T440-5` |
| 4 | the `PIPESTATUS` self-error | mechanism, status and repair **CONFIRMED**; harness swept, **0** other sites |
| 5 | K8 / STATE-LOSS | census reproduces cell for cell; **zero live sites CONFIRMED** by my own adjudicator; but the published decomposition of the 29 is wrong → `C-T440-2` |
| 6 | what T424 left open | all confirmed; two closed by me; `F-T424-N1` reproduces and is **not filed as work** → `C-T440-3` |
| BAR | T424's tree **and** the merge with `main` | both exit 0; merge shows **16 of 16** as required |
| new | T424's own `t424-comment-claims-drive.sh` **fails on the tree it ships in** | **`C-T440-1` (MAJOR)** |

---

## 2. Conditions

### `C-T440-1` — MAJOR. `t424-comment-claims-drive.sh` exits **1** on the tree it ships in, and its shipped transcript says it exits 0.

CLAIM 3's "no match" probe is:

```
git grep -q 'zzq-no-such-token-t424' -- .softhouse > /dev/null 2>&1; g_absent=$?
```

That literal is **committed, tracked, inside the drive's own source**, so `git grep` matches the
drive itself and returns **0**, not 1. `check "no match -> 1"` therefore fails,
`T424-COMMENT-CLAIMS-RESULT: disagreements=1`, and the drive **exits 1** — `*** THIS DRIVE FAILED.`

[VERIFIED: `out/T440-F-T440-1.txt`; re-run of the shipped instrument on `/tmp/t440/wt-t424` at
`a504b59d` and on the merge worktree. `git grep -n 'zzq-no-such-token-t424' -- .softhouse` returns
one hit, `…/t424-comment-claims-drive.sh:103`, rc 0.]

The shipped transcript records the opposite [VERIFIED:
`.softhouse/capture/t424/out/T424-comment-claims.txt:44,47,53-54` → `no match : rc=1`,
`OK`, `disagreements=0`, `Every claim came out as declared.`]. That transcript can only have been
taken while the instrument was still **untracked** — `git grep` does not search untracked files.

**Bounded, so the finding is not overstated.** CLAIM 3 itself is TRUE. Probed with a token built
at run time so it cannot be in any file: genuine no-match → **1**, invalid pattern → **128**,
genuine match → **0** [VERIFIED: `out/T440-F-T440-1.txt`]. The defect is in the **probe**, not in
the claim, and the other two claims and the other three T424 drives are unaffected
(`t424-f2-true-cause.sh` → `arms_failed=0` exit 0; `t424-buffered-writer-drive.sh` →
`arms_failed=0` exit 0; `t424-k8-discrimination.sh` → `arms_failed=0` exit 0; all re-run by me
[VERIFIED: `out/T440-rerun-f2tc.txt`, `out/T440-rerun-bwd.txt`, `out/T440-rerun-k8disc.txt`]).

**Why MAJOR anyway.** This is a red arm that is red for the wrong reason — the exact defect
class of point 4 — and a published measurement whose own recipe no longer reproduces — the exact
defect class of `F-T424-N1`, which T424 raised against somebody else's file. Anyone who re-runs
T424's evidence gets a hard failure and no way to tell "T424's claims are false" from "T424's
probe collided with itself". The whole subject of this branch is that a statement about the world
must keep reproducing.

**Drive:** `instruments/f-t440-1.sh`. **Close it by** building the sentinel at run time
(`tok="zzq-$$-$RANDOM-$(date +%s)"`) or excluding the instrument from the pathspec, and
**re-capturing `out/T424-comment-claims.txt` on the committed tree**, which is the half that makes
the transcript honest.

### `C-T440-2` — MINOR. The published decomposition of the 29 K8 sites is `16 + 8 + 6 = 30`, and both non-six cells are wrong.

`AUDIT-CLASS.md` and the handoff both split the 29 as *"all sixteen `sel` calls"* + *"the eight
`SWEEP_*=$((…))` counters"* + *"the six parent-side assignments"*. That is 30, not 29, and it does
not match the list. Measured over the census's own K8 block:

| what | AUDIT-CLASS.md / handoff | **measured by T440** |
|---|---|---|
| rows that are a `sel` call | 16 | **13** |
| rows that are `SWEEP_*=$((…))` | 8 | **10** |
| rows that are neither | 6 | **6** |
| total | **30** ✗ | **29** ✓ |

[VERIFIED: `out/T440-k8-29-rows.txt` — all 29 rows enumerated verbatim from
`out/T440-census-after.txt`'s `--- K8` block and partitioned mechanically.]

The likely origin is a real conflation: there **are** sixteen `sel` calls in the file, but only 13
reach the wide K8 list — `S1`, `S3` and `S7` use `-F` patterns with no `|` in them, so they never
match `K8_RIGHT`. [VERIFIED: those three selector lines carry no `|`.]

**This does not disturb the verdicts.** Every one of the 29 is still NOT state-loss, and I
established that independently (§5). What it disturbs is the table a future maintainer uses to
check the census has been *fully* adjudicated: a decomposition that does not sum to its own total
cannot do that job. **Close it by** correcting the two cells to 13 and 10 in `AUDIT-CLASS.md` and
in the handoff.

### `C-T440-3` — MINOR. `F-T424-N1` was rightly not edited, and is now not filed anywhere.

**Leaving it was RIGHT, and I verified the reason rather than accepting it.** `T431` is
`in_progress` on branch `softhouse/T431-t407-conditions` and carries `.softhouse/conformance.sh`
in its `files_hint` [VERIFIED: `.softhouse/tasks.json`]. `conformance.sh` was genuinely contended
and the region is not T424's grant. Editing it would have been the wrong call.

**But it is now nowhere.** `grep -c 'FU-T424\|F-T424' .softhouse/tasks.json` → **1**, and that one
occurrence is inside T440's own description [VERIFIED]. No `FU-T424-*` appears in
`.softhouse/obligations.md` or `.softhouse/gates.md` [VERIFIED: grep, no output]. A finding that
lives only in a handoff paragraph is a finding that evaporates at the next fire.

**The finding itself reproduces, exactly as T424 states.** `conformance.sh:1299` says, in the
present tense and with its own recipe, that *"`CONFORMANCE_REPO_ROOT` and `-repo-root` each occur
ZERO times in it (measured … `LC_ALL=C grep -c`; both returned 0, exit 1)"*. Running that recipe
today:

```
LC_ALL=C /usr/bin/grep -c 'CONFORMANCE_REPO_ROOT' conformance.sh  -> 22, exit 0
executable (non-comment) lines only                               -> 16
LC_ALL=C /usr/bin/grep -c -- '-repo-root'          conformance.sh ->  2, exit 0
executable (non-comment) lines only                               ->  0
```

[VERIFIED: run against `/tmp/t440/wt-t424/.softhouse/conformance.sh`, and reproduced by T424's own
`t424-comment-claims-drive.sh` CLAIM 2 in my re-run.] The paragraph describes the **pre-repair**
hole and the repair `T201` shipped is what made it false — a one-sentence fix (past tense, name
the commit at which it held). **Close it by** filing it as a task for the `conformance.sh` owner.

### `C-T440-4` — LOW. The new `pipefail` sentence in the shipped comment is over-broad, and the abort message it defends misattributes one case.

The comment says *"`set -o pipefail` does **NOT** surface a failing `git ls-files` here."* That
holds only when git fails **with no output**. When `git ls-files` fails *after* emitting lines,
`grep -c .` succeeds (rc 0), pipefail's rightmost non-zero is **git's own 128**, `_corpus_rc=128`,
and the block aborts printing:

```
SWEEP ABORT (exit 2): the corpus COUNT DID NOT RUN (rc=128).
```

[VERIFIED: `out/T440-F2b.txt` — `pipefail git(128, 3 lines) | grep -c .(0) -> captured=[3] rc=128`,
shipped block exit 2.] The count *did* run; git failed. **Fail-CLOSED, so this is not a hole** —
but it is a message that states the wrong cause, one line below a comment correcting a message
that stated the wrong cause. **Close it by** narrowing the sentence to the no-output case, or by
naming what rc 128 means.

### `C-T440-5` — LOW. An exported `T381_DRIVE_INNER` disables the amended guard entirely.

The amended guard gates the whole grader on `[ -z "${T381_DRIVE_INNER:-}" ]`. With
`T381_DRIVE_INNER=1` exported, a specimen carrying a failing arm exits **0** instead of 1
[VERIFIED: `out/T440-attack.txt`, A2 — normal invocation exit 1, bypassed invocation exit 0].

Rated LOW, not MAJOR, for three measured reasons: the name is internal; T402's guard had the
**mirror-image** surface (it was gated on `T381_DRIVE_LOG` being *set*, so unsetting it skipped
the guard), so this is a residual and not a regression; and every *other* misuse I tried
fails **closed** — a `T381_DRIVE_LOG` pointing at an unwritable path exits **2**
[VERIFIED: same transcript]. **Close it by** having the outer set `T381_DRIVE_INNER=$$` and the
inner refuse unless it equals `$PPID`, or by documenting the surface in the patch comment.

### `C-T440-6` — LOW. One factual slip in T424's Unverified section.

T424 writes that with `BEFORE_REF=main`, `t381-red-drives.sh` *"refuses (BEFORE and AFTER are the
same file)"*. Measured on **T424's own tree** and on the **merge result**, it does not: it aborts
at **D-R2, exit 4** — `D-R2 patch: expected 1 anti-calibration search line in BEFORE, found 0` —
the same place and the same status as with `BEFORE_REF=964b532e`
[VERIFIED: `/tmp/t440/t381-t424-main.txt`, `/tmp/t440/t381-main.txt`]. The substantive claim (the
drive cannot be run to completion on any available ref, so `FU-T386-7`'s guard has nothing to
grade yet) **stands and is confirmed**. Only the stated reason for one of the two refs is wrong.

---

## 3. Point 1 — the true cause of `F-2`, re-derived from primitives

`instruments/f2.sh`, transcript `out/T440-F2.txt`, **`T440-F2-DRIVE-RESULT: arms_failed=0`,
exit 0**. Written from scratch; T424's `t424-f2-true-cause.sh` was not used and was read only
afterwards. The OLD block is extracted **by content** from `8fa677a6` (the last commit before
T402), the NEW block **by content** from the shipped file, and each extraction refuses unless its
anchor matches exactly once.

**The primitives** [VERIFIED: `out/T440-F2.txt` PART 0]:

```
true | grep -c .                     -> captured=[0] rc=1     grep -c . PRINTS 0 for an empty stream
git(FAILS rc=129) | grep -c .        -> captured=[0] rc=1     NOT EMPTY. This is the point.
REAL grep, INVALID REGEX             -> captured=[]  rc=2     EMPTY. This is the true cause.
[ "0" -lt 1 ] -> TRUE  (rc 0)   the abort FIRES
[ ""  -lt 1 ] -> FALSE (rc 2)   the `if` reads non-zero as false -> FALLS THROUGH
```

**Both halves, end to end, under PATH shims** [VERIFIED: same transcript PARTS 1–2]:

| arm | OLD block (pre-T402) | SHIPPED block |
|---|---|---|
| `git ls-files` shim exits 128, prints nothing | **ABORT, rc 2** — *T402's stated cause does not reproduce* | ABORT, rc 2, via the VALUE test |
| `grep` shim exits 2, prints nothing | **FELL THROUGH, rc 0** — *the true cause, reproduced* | ABORT, rc 2, naming `the corpus COUNT DID NOT RUN (rc=2)` |
| healthy | FELL THROUGH, rc 0 (non-vacuous) | FELL THROUGH, rc 0 (non-vacuous) |

I added one arm T424 did not: I checked that the shipped block does **not** print
`COUNT DID NOT RUN` on a failing `git ls-files` — i.e. that its message matches its cause. It does
not, correctly. (The partial-output case where it *does* is `C-T440-4`.)

**T424's correction is right, and the correction is right at all three sites.** The shipped
comment in `casualty-sweep.sh`, `T402-t386-conditions.md` §3 and `AUDIT-CLASS.md` §2 now all state
the true cause. The executable block is untouched, which is correct: the repair was never wrong.

**This is the third attribution in the chain, and I could not falsify it.** Checked
deliberately, since the brief warns that a wrong correction is worse than the error.

## 4. Point 2 — `pipefail` returns the rightmost **non-zero** status

Verified from the shell, not from the claim [VERIFIED: `out/T440-F2.txt` PART 0b]:

```
pipefail  (exit 128) | (exit 1)   -> rc=1      rightmost wins over a larger left status
pipefail  (exit 1)   | (exit 128) -> rc=128    reversed: it is POSITION, not magnitude
pipefail  (exit 3)   | (exit 0)   -> rc=3      rightmost NON-ZERO: a trailing 0 does not mask it
```

The third arm is the one that matters and neither T408 nor T424 drove it: `pipefail` is *not*
"the last command's status", it is "the last **non-zero** status", so T424's wording is precisely
correct where a looser wording would have been wrong. And in the real pipeline,
`git(129) | grep -c .(1)` → **rc 1**, git's status discarded [VERIFIED: same transcript].
**T408's `F-T408-5` remark is false and T424's correction of it holds.**

**Placement: right.** The sentence sits in `casualty-sweep.sh` immediately beside the guard whose
value test it defends. That is the only place a reader minded to delete the value test will be
looking; a correction filed only in a handoff would not have reached them. T408's review is not on
`main` (`softhouse/T408-review-t402` is not an ancestor), so its false sentence is not reachable
from the graded tree and needs no separate correction.

## 5. Point 3 — the buffered-writer guard

### All four matrices re-run — every arm reproduces

Re-ran the shipped `t424-buffered-writer-drive.sh` against T424's tree
[VERIFIED: `out/T440-rerun-bwd.txt`, drive exit 0, `arms_failed=0 runs_per_arm=8`; guard patch
sha256 `f3c67070ad883a64` (old) and `458753830160eb59` (new), both extracted by content]:

| matrix | arm | measured by T440 |
|---|---|---|
| RED, T402 | failing arm / BSD `tee` | 8/8 exit **1** — correct |
| RED, T402 | failing arm / 1 MiB buffered stand-in | 8/8 exit **0** — **FAIL-OPEN, reproduced** |
| RED, T402 | healthy / both writers | 8/8 exit 0 — correct passes |
| RED, T402 | drive dies early | 8/8 exit 4 — guard never reached |
| GREEN, T424 | failing arm / buffered stand-in | 8/8 exit **1** — the proof |
| GREEN, T424 | failing arm / BSD `tee` | 8/8 exit **1** |
| GREEN, T424 | healthy / both writers | 8/8 exit **0** — not vacuous |
| GREEN, T424 | aborted run / both writers | 8/8 exit **2** — refuses |
| e2e | real `t381-red-drives.sh`, unpatched / +T402 / +T424(tee) / +T424(buffered) | 4 / 4 / **2** / **2** |

### Attacking the construction

`instruments/attack.sh`, transcript `out/T440-attack.txt`. **One finding (`C-T440-5`); the
construction itself holds.**

- **"bash waits for every pipeline member" — TRUE in the forms used here, and I made it
  falsifiable.** I built a writer that consumes stdin, then **sleeps one second after its producer
  has exited**, then writes. After the pipeline returned, the payload was present and one second
  had elapsed — for a bare `producer | writer LOG` and for the guard's exact
  `cmd 2>&1 | writer LOG` form, with `PIPESTATUS=(0 0)` [VERIFIED]. So the file is complete by the
  line after the pipeline, whatever the writer's buffering. **The fix is structural.**
- **`shopt -s lastpipe` is the one option that changes who runs the last member.** It does not
  exist in `bash 3.2` on this host, is off by default everywhere, and appears in neither the patch
  nor the drive [VERIFIED].
- **The sentinel check is exactly-once, and non-vacuous.** A drive printing `END OF DRIVES.`
  **twice** makes the guard refuse at **2**; a healthy drive printing it once passes at **0**
  [VERIFIED]. "Truncated" and "doubled" are both refused, and neither can be mistaken for a pass.
- **A transcript that will not open refuses at 2** rather than passing [VERIFIED].
- **The env-bypass** is `C-T440-5`.

### What one host still leaves open — and I could not narrow it

**There is no GNU coreutils `tee` on this host** (`gtee` absent; no
`…/coreutils/libexec/gnubin/tee`) [VERIFIED: `out/T440-attack.txt` A4]. T424's declared bound —
*"the buffered writer is a stand-in, not a measurement of GNU coreutils"* — **stands, and T440
could not narrow it either.** What is proved on this host is the thing that actually matters and
is writer-independent: the amended guard's verdict does not vary with the writer, and the old
one's does. What is still unproved by anyone is any claim about a specific `tee` binary on a
specific platform. That is honestly stated in the branch and I am restating it rather than letting
the re-run imply more coverage than it has.

**One further limit, which T424 states and I confirm:** the amended guard is shipped as a
**patch**, not applied. `git apply --check` is **rc 0** against the merge result [VERIFIED], but
nothing in the tree executes it today, and `t381-red-drives.sh` cannot reach `END OF DRIVES.` on
any ref (`C-T440-6`, `FU-T424-2`). So the guard is proved on synthetic bodies plus the real
drive's real early death, and not on a full healthy run of the real drive.

## 6. Point 4 — the `PIPESTATUS` self-error, confirmed and swept

`instruments/pipestatus.sh` + `pipestatus2.sh`, transcripts `out/T440-pipestatus.txt`,
`out/T440-pipestatus2.txt`.

**The mechanism is exactly as T424 describes** [VERIFIED]:

```
after `sh -c "exit 7" | sh -c "exit 0"`   PIPESTATUS=(7 0)  len=2
after `a=${PIPESTATUS[0]}`                PIPESTATUS=(0)    len=1   a=7
```

The assignment is itself a command and **replaces** the array with its own status.

**The status it dies with is 1 — in the form that actually occurs.** This is the load-bearing
half of T424's claim and it is form-dependent, so I measured it four ways rather than one
[VERIFIED: `out/T440-pipestatus2.txt`]:

```
defective shape in a SCRIPT FILE, `bash def.sh`   -> exit 1     <- the form T424 hit
same body via `bash -c '…'`                       -> exit 127   <- a bash 3.2 quirk, NOT the form here
a plain unbound variable in a script file         -> exit 1
a genuine "caught a failing arm"                  -> exit 1     <- INDISTINGUISHABLE
```

So the defective guard died with **1**, byte-identical to a real catch, and its RED arms scored
8/8 for the wrong reason. **T424's account of its own error is correct.** Without `set -u` the
same bug is *silent*: the second read yields the empty string and a numeric test on it then
returns 2 — worse, not better.

**The repair is correct.** `_t424_pipe=( "${PIPESTATUS[@]}" )` copies the whole array in one
statement; both members are then readable [VERIFIED]. The patch also carries `:-1` defaults on
both reads, so an unexpected shape fails closed.

**The sweep — the part of point 4 that could have found something.** `instruments/ps-census.py`
walks every tracked `.sh` / `.bash` / `.py` / `.patch` file and flags a second `PIPESTATUS` read
with **no intervening pipeline** (correcting for a pipeline earlier on the same line, and treating
`p=( "${PIPESTATUS[@]}" )` as safe). The denominator is printed, because a sweep reporting "0
found" without saying how many it looked at is the fail-open it is hunting.

```
T440-PS-CENSUS-RESULT: scanned=1468  withps=19  defective=0  safe_whole=1
```

[VERIFIED: `out/T440-ps-census.txt`, all 19 files listed by name with their mention counts.]
**Zero other instances of the shape in the harness.** The one whole-array copy is T424's repair.
Every other site reads exactly one `PIPESTATUS[0]` per pipeline, which is safe. This is the
result I would most have liked to be non-empty, and it is empty.

## 7. Point 5 — K8 / STATE-LOSS, re-run and re-adjudicated

### The census reproduces cell for cell, on both refs

Re-ran T424's amended `t402-status-class-census.sh` myself
[VERIFIED: `out/T440-census-before.txt`, `out/T440-census-after.txt`]:

| ref | `K1..K7` | `K8` wide | `K8s` de-noised |
|---|---|---|---|
| BEFORE `964b532e` (sha `1fa6acfe…`) | `22 / 31 / 40 / 0 / 0 / 3 / 28` | **17** | 1 |
| AFTER `HEAD` (sha `63e05208…`) | `26 / 32 / 54 / 7 / 0 / 0 / 44` | **29** | **6** |

`K1..K7` match T402/T408 exactly, and `K8 17 → 29` and `K8s = 6` match T424 exactly. The census's
own intersection guard prints both halves (`state-mutating lines: 65 ; subshell-bearing lines:
50`), so an empty intersection could not be confused with a census that stopped measuring — a good
construction, and it is in the census everyone runs rather than in an addendum nobody does, which
was the right call.

### "Zero live state-loss sites" — confirmed by an adjudicator that is not T424's

`instruments/k8-adjudicate.sh` does **not** use T424's regex. It enumerates every call of every
state-mutating function and every `SWEEP_*` assignment, and asks of each whether it executes in a
subshell [VERIFIED: `out/T440-k8-adj-after.txt`]:

```
calls to sel()            : 16   non-bare: 0
calls to calibrate()      :  1   non-bare: 0
calls to _calib_refuse()  :  7   non-bare: 0
calls to engine_count()   :  9   non-bare: 0
SWEEP_* assignment lines  : 32   assignments executing in a CHILD: 0
state-mutating function invoked from inside $( ) anywhere : none
```

Same result on the BEFORE ref. **Zero live `STATE-LOSS` sites, before and after — confirmed
independently.**

**My adjudicator is non-vacuous, and I proved that rather than asserting it.** In a throwaway git
repo **under `/tmp`** I respelled `S16` as `sel … | cat`; my adjudicator flags it
(`*** 730 BARE + PIPED INTO SOMETHING`) and T424's `K8s` view moves **6 → 7** on the same specimen
[VERIFIED: `out/T440-rerun-k8disc.txt` and the RED-specimen run]. So the new kind discriminates,
`K8s` is the discriminating view exactly as T424 says, and the wide `K8` does not move — also
exactly as T424 says, and stated in the census rather than hidden.

The one thing wrong here is the arithmetic of the published decomposition — `C-T440-2`.

## 8. Point 6 — what T424 left open, confirmed by name

| item | T440's finding |
|---|---|
| `t309-…/patch6.py` background-job text, liveness `[UNVERIFIED]` | **CLOSED BY T440, benign.** The emitted text *is* live: `.softhouse/bin/fire-program.sh:2151` carries `( reconcile_tasks_json "$@"; print -r -- "$RECON_VERDICT" > "$vf" ) &` verbatim. But the read is at **:2171-2172**, after `wait_bounded "$job"` (:2153) **and** `wait "$job"` (:2169) — the writer has exited. If the job is killed at its budget, `$vf` is absent and `RECON_VERDICT` becomes `UNKNOWN — … treat tasks.json as UNVERIFIED`. Fail-closed. **Same construction as T424's own fix; no defect.** [VERIFIED: source at those lines] |
| `t309-…/patch5.py` | **NOT LIVE.** Its bare `( reconcile_tasks_json "$@" ) &` occurs **0** times in `fire-program.sh`; patch6 superseded it. [VERIFIED: `grep -cF`] |
| `t284-…/30-red-drive.sh` latent `K8` | **CONFIRMED, exactly as stated.** `pass`/`bad` mutated inside `arm()` (:123-124); the verdict comes from `$bad` (:294), **not** from re-reading `$TRANSCRIPT`; all `arm` call sites are bare — a grep for a piped or preceded `arm` returns nothing. Latent, not live. [VERIFIED] |
| `F-T424-N1` (`CONFORMANCE_REPO_ROOT` "occurs ZERO times") | **REPRODUCES.** 22 whole-file / 16 executable-only, not 0. Leaving it unedited was **RIGHT** (T431 is `in_progress` and owns `conformance.sh`) — but it is filed nowhere. `C-T440-3`. |
| `t381-red-drives.sh` never run to completion | **CONFIRMED** on T424's tree and on the merge result; both refs abort at D-R2 exit 4. One stated reason is wrong — `C-T440-6`. |
| T408's `A2`/`A3` WITNESS defeats not re-derived by T424 | **CONFIRMED AT SOURCE BY T440, so the residual is smaller than T424 left it.** `_errf_read` tests `[ "$t" = "$SWEEP_ERRF_SENTINEL" ]` — **exact equality**, so `A3` (sentinel present but not alone) defeats it as described; and it reads `$SWEEP_ERRF` **by path** with no inode check, so `A2` (mid-window substitution) is structurally possible as described. [VERIFIED: `casualty-sweep.sh:214`, `:189`, `:206-215`.] T424 weakened the claim from *"positive proof"* to *"inference under path stability"* with both defeats named — a change **in the conservative direction**, which is safe whether or not T408's exact harness was right. `FU-T424-3`'s proposed close (match *contains* rather than *equals*) is correct for `A3`. |
| T424's neighbour census | **REPRODUCES.** 1459-file denominator; S-A 23 `tee` sites / **0** read their target; S-B 3 files with background jobs; S-C `conformance.sh` 0/0; S-D 9 patches, 2 hits (T402's defect, T424's fix). The S-D bucket is the one that matters — an executables-only census would have returned a clean zero for the very defect it hunts. [VERIFIED: re-run] |

---

## 9. The bar — T424's tree **and** the merge result

Both runs on a clean tree, in `/tmp` worktrees, **`probe = ` PRESENCE tested before its value**
(four exit-2 paths, including a failed HARD guard, run before it prints, so "probe != up" would
otherwise be trivially true against nothing at all).

| figure | T424's tree (`a504b59d`) | **merge with `main` `e4bde474`** | required |
|---|---|---|---|
| exit | **0** | **0** | 0 |
| `grep -c 'probe = '` | **1** | **1** | ≥ 1 **first** |
| the probe line | `:201 … probe = up` | `:201 … probe = up` | `up` |
| VERDICT | PASS, **46** vectors, **7884** cells | PASS, **46** vectors, **7884** cells | unmoved |
| **wrong ledger implementations** | **15 of 15** | **16 of 16** | **16** ✓ |
| `ledger parity` | PASS 10 FAIL 0 | PASS 10 FAIL 0 | — |
| LEDGER money cells | 63 == pinned 63 | 63 == pinned 63 | — |
| dead-path frontier | GREEN, `frontier == pinned (all 11 rows)` | GREEN, `frontier == pinned (all 11 rows)` | — |
| `T316-DEADPATH-CENSUS` | corpus 1459, **deadOccurrences 108** | corpus 1500, **deadOccurrences 108** | 108 |
| narrow-catch census | — | 63 `.java`, `EXCLUDED 0 other checkout root(s): none` | — |

[VERIFIED: `out/T440-BAR-t424tree.txt` (750 lines, `T424TREE_BAR_EXIT=0`) and
`out/T440-BAR-merge.txt` (751 lines, `MERGE_BAR_EXIT=0`).]

**The merge result shows 16 of 16, so the brief's stated failure condition did not occur.** T424's
own 15/15 is explained exactly as the brief predicted — it forked before `T421` merged — and the
merge picks up the sixteenth without any change to T424's artefacts. The merge itself is clean, no
conflicts. The pinned `deadOccurrences` held at 108 in both runs: T424's seven new artefacts add
**zero** dead-path occurrences and zero frontier rows. The corpus figure moved (1459 → 1500) and
that is a derived floor, not a pin.

---

## 10. Checked and found clean — so silence is distinguishable from not looking

- The three corrected sites for `F-2` (source comment, `T402` handoff §3, `AUDIT-CLASS.md` §2) all
  now state the driven cause, and the **executable block is untouched** — the repair was never
  what was wrong. [VERIFIED: `git diff main...` on all three files]
- `AUDIT-CLASS.md`'s new `STATE-LOSS` verdict is correctly argued as **not** a flavour of
  FAIL-OPEN: a state-loss site can consult every status it has and still lose the answer. Adding
  the *verdict* alongside the *kind* is the right shape, and the maintenance rule's two new
  clauses ("audit the diff for lost STATE too", "drive the cause, not only the effect") are the
  two lessons this branch actually paid for.
- The `T424-SUPERSEDES-FU-T386-7.md` DO-NOT-APPLY marker exists, names the replacement path, says
  the two patches conflict and why, and explicitly keeps T402's patch as the record of the finding
  it did close. A defective patch sitting beside a corrected one with no marker would have been a
  fail-open by documentation; it is not.
- The amended patch applies clean: `git apply --check` **rc 0** on the merge result. [VERIFIED]
- `FU-T386-7` is marked **SUPERSEDED** in `T402-t386-conditions.md`'s follow-up table, with the
  replacement path inline. [VERIFIED: diff]
- Every T424 instrument extracts the text it grades **by content** and refuses unless the anchor
  matches exactly once. [VERIFIED by reading each extraction guard: `t424-f2-true-cause.sh`,
  `t424-buffered-writer-drive.sh` (both patches, plus a truncation check on each extraction),
  `t424-k8-discrimination.sh`, `t424-comment-claims-drive.sh`'s `locate()`. I did **not** feed
  each one a deliberately non-unique anchor; that is `[UNVERIFIED]` and the refusals are read,
  not driven.] No line numbers are load-bearing anywhere in the branch, which is the point
  `T404`'s +75-line insertion had already made expensively.
- No money path, no ledger code, no vector, no schema and no Go source is touched by this branch.
  It is entirely harness, capture artefacts and documentation. No non-negotiable is engaged:
  no float, no balance write, no deposit string, no currency handling, no US rail, no non-Postgres
  driver. [VERIFIED: `git diff main... --stat`, 22 files, all under `.softhouse/`]
- Scope: every changed path is inside `.softhouse/capture/…`, `.softhouse/handoff/…` or T424's own
  `capture/t424/` directory. `conformance.sh` and `t381-red-drives.sh` are **not** modified, which
  matches T424's declared restraint and the contention facts I verified.

## 10a. An error of T440's own, recorded rather than quietly fixed

My first draft of `instruments/f-t440-1.sh` **hardcoded** the path of the drive it grades,
`.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh`. That file exists only on the
branch under review, so on **T440's own branch** it is a dead repo-path reference:
`guard_dead_path_frontier` refused, `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1
removed=0`, and the bar exited **2** [VERIFIED: `out/T440-BAR-own-RED.txt:181,190,219,221`].

The tempting fix was to spell the literal in pieces so the census would not see it. That is
gaming a guard this program has paid for twice, and it is the same move as a red arm that is red
for the wrong reason. **The path is now a required argument with no default, and the script
refuses when it does not resolve** — which is the remedy the guard itself names in its refusal
text. The transcript in `out/T440-F-T440-1.txt` is a re-run of the corrected instrument, so the
instrument shipped and the instrument graded are the same file.

Worth stating because it is the branch's own lesson landing on its reviewer: an instrument that
names an artefact existing only on one branch has made a claim about the world that stops
reproducing the moment it leaves that branch.

## 11. What T440 did not do

- `[UNVERIFIED]` **any specific `tee` binary.** No GNU coreutils on this host; T424's bound stands
  unnarrowed.
- **One host**, the same one T424 used. Both bar runs, all drives, all censuses.
- I did not grade the other 57 candidate comment lines in `conformance.sh`. T424's comment hunt is
  a sample and I confirmed the sample, not the population.
- I did not rebuild T408's `A2`/`A3` defeat harness either. I confirmed both defeats' **mechanisms
  at source** (§8), which is strictly more than T424 had, and less than a drive.
- The amended guard is not applied anywhere, so no claim is made about its behaviour inside a
  *completing* run of `t381-red-drives.sh` — nobody can make that claim until `FU-T424-2` is
  closed.

---

## 12. Verdict

**`APPROVED WITH CONDITIONS`.**

The three corrected mis-attributions are all correct, and I could falsify none of them. The
buffered-writer guard is fixed **by construction** — I built a writer that writes a full second
after its producer dies and confirmed the shell waits for it — not by a bigger buffer and not by a
sleep. The `PIPESTATUS` self-error is real, its status genuinely is `1` in the form that occurred,
the repair is right, and the harness carries **no** other instance of the shape. The K8 kind is in
the census everyone runs, it discriminates, and "zero live state-loss sites" survives a second,
independently-constructed adjudicator. Both bars are green and the merge shows the required 16.

Against that: one MAJOR — a T424 drive that **fails on the tree it ships in**, with a shipped
transcript saying it passes, caused by a probe colliding with its own committed source; and a
published K8 decomposition that does not add up to its own total. Neither touches a shipped
repair; both touch the *evidence*, which on this branch is the deliverable.

| condition | rating | one-line close |
|---|---|---|
| `C-T440-1` | **MAJOR** | run-time sentinel in `t424-comment-claims-drive.sh`; **re-capture the transcript on the committed tree** |
| `C-T440-2` | MINOR | correct the K8 decomposition to **13 / 10 / 6** in `AUDIT-CLASS.md` and the handoff |
| `C-T440-3` | MINOR | file `F-T424-N1` as a task for the `conformance.sh` owner |
| `C-T440-4` | LOW | narrow the `pipefail` sentence to the no-output case, or name what rc 128 means |
| `C-T440-5` | LOW | close or document the `T381_DRIVE_INNER` env bypass |
| `C-T440-6` | LOW | correct the `BEFORE_REF=main` statement in T424's Unverified section |
