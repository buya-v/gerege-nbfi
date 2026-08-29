# T424 — T408's conditions on T402: a wrong attribution in shipped source, and a guard that fails open on a buffered writer

Branch `softhouse/T424-t408-conditions`. Subject: what `T402` landed at `eb005ba8`, as reviewed
by `T408`. **The two conditions aimed at `T399`'s gate (`C-T408-1`, `C-T408-2`) are recorded on
`T399` and were not touched here.**

Every claim below is tagged `[VERIFIED: <source>]` or `[UNVERIFIED]`. Where a number would rot, the
instrument that re-derives it is named instead of the number.

**T408's review is NOT on `main`** — `softhouse/T408-review-t402` is not an ancestor of `main`
[VERIFIED: `git merge-base --is-ancestor` → NOT-MERGED; `ls .softhouse/reviews/t408-review-t402` →
No such file or directory]. I read it from the branch (`git show softhouse/T408-review-t402:…`) and
re-derived every cardinal I relied on rather than inheriting it.

---

## Changes Made

| # | file | what changed |
|---|---|---|
| 1 | `.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh` | **the shipped `F-2` source comment**: the false attribution corrected, the true cause written in with its drive, and the `pipefail` inference that does not hold named. Comment-only; the executable block is untouched. |
| 2 | `.softhouse/handoff/T402-t386-conditions.md` | §3's `F-2` attribution corrected; §2's *"positive proof"* claim about WITNESS corrected to an inference under path stability, with both defeats named; the `FU-T386-7` row marked SUPERSEDED. |
| 3 | `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md` | `F-2`'s attribution corrected here too; **`K8` state-loss kind** added to the taxonomy table; **`STATE-LOSS`** added to the verdict vocabulary with the reason it is not a flavour of FAIL-OPEN; every `K8` site adjudicated; the maintenance rule extended by two clauses. |
| 4 | `.softhouse/capture/t402-t386-conditions/instruments/t402-status-class-census.sh` | `K8` added to the census itself (**not** a parallel census in my own directory — an addendum nobody runs is the P-45 defect this program keeps paying for), plus the de-noised `K8s` discriminating view. `K1..K7` untouched. |
| 5 | `.softhouse/capture/t424/patches/FU-T386-7-…AMENDED-BY-T424.patch` | the amended `FU-T386-7` patch. `git apply --check` **rc=0 clean** against this tree [VERIFIED: `build-patch.sh` output]. |
| 6 | `.softhouse/capture/t402-t386-conditions/patches/T424-SUPERSEDES-FU-T386-7.md` | a DO-NOT-APPLY marker beside the superseded patch. A defective patch sitting next to a corrected one with no marker is a fail-open by documentation. |
| 7 | `.softhouse/capture/t424/instruments/`, `out/` | four drives and their transcripts (below). |

**Not changed, deliberately:** `.softhouse/conformance.sh` (contended this fire — `T431` at the
witness lookup) and `.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh`
(another task's capture directory; `T408` ruled that shipping rather than applying was correct for
exactly this reason, and I kept that ruling).

### How I located every site — by content, never by line number

`T404`'s +75-line insertion rotted seven citations in `conformance.sh`, so nothing here is cited by
number. The exact searches:

- `grep -n "had failed\|FELL THROUGH\|returns 2 on a malformed" casualty-sweep.sh` → the `F-2`
  comment block. Confirmed unique before editing.
- `grep -c -F 'SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?'` → **1**; the
  drive refuses unless that anchor matches exactly once.
- `grep -n "positive proof" T402-t386-conditions.md` → the WITNESS claim.
- `grep -n "FU-T386-7" T402-t386-conditions.md` → the row to mark superseded.
- `grep -c -F 'if [ -n "${T381_DRIVE_LOG:-}" ] && [ -f "${T381_DRIVE_LOG:-}" ]; then'` inside
  T402's patch → **1**; guard extraction refuses otherwise.
- `grep -c -F 'set -uo pipefail'` and `grep -c -F 'echo "END OF DRIVES."'` in
  `t381-red-drives.sh` → **1** each; the patch builder refuses otherwise.
- `sel "S16 status-enum prose` → **1**; the K8 discrimination drive refuses otherwise.

---

## The true cause of F-2, driven

Instrument `.softhouse/capture/t424/instruments/t424-f2-true-cause.sh`; transcript
`out/T424-F2-true-cause.txt`; `T424-F2-DRIVE-RESULT: arms_failed=0`, drive exit **0**. It extracts
the SHIPPED block from `casualty-sweep.sh` by content and refuses if the anchor is not unique, and
it reports failure through its own exit status.

**The primitive that decides it** [VERIFIED: `out/T424-F2-true-cause.txt`, PART 0]:

```
true | grep -c .            -> captured=[0] rc=1
git-that-fails | grep -c .  -> captured=[0] rc=1   <- NOT EMPTY. This is the point.
REAL grep, INVALID REGEX    -> captured=[]  rc=2   <- EMPTY. This is the true cause.
[ "0" -lt 1 ] -> TRUE  -- the abort FIRES
[ ""  -lt 1 ] -> FALSE -- the abort does NOT fire ([ ] returned 2)
```

**Eight end-to-end arms, all as declared** [VERIFIED: same transcript, PARTS 1–3]:

| arm | old block | new block |
|---|---|---|
| `git ls-files` shim exits 128, prints nothing | **ABORT, rc 2** — *the stated cause does not reproduce* | ABORT, rc 2 |
| `grep` shim exits 2, prints nothing | **FELL THROUGH, rc 0** — *the true cause* | ABORT, rc 2, `the corpus COUNT DID NOT RUN (rc=2)` |
| healthy | passes through | passes through |

So: **`grep -c .` prints `0` for an empty stream**, which means a failing `git ls-files` still hands
the test the string `"0"`, and `[ "0" -lt 1 ]` is true. Emptying the substitution — which is what
makes `[` return 2 and the `if` fall through — needs **`grep` itself** to fail: invalid pattern,
broken locale, missing binary, EMFILE. `T402`'s mechanism and repair were right; its **attribution**
was wrong, and the wrong attribution had been committed into the source comment. Corrected at all
three sites: the source comment, the handoff §3, and `AUDIT-CLASS.md` §2.

**A third mis-attribution, found by this drive and not previously noticed.** `T408`'s own `F-T408-5`
says the repair "now reads the pipeline status, so pipefail catches the `git ls-files` case as
well". **It does not.** `set -o pipefail` returns the status of the **rightmost** command that
exited non-zero, and that is `grep -c .`'s `1`, not git's `128`
[VERIFIED: `out/T424-F2-true-cause.txt`, PART 0: `pipefail: git(128) | grep -c .(1) -> captured=[0] rc=1`].
A failing `git ls-files` is caught by the **value** test exactly as before; what the status read
adds is the `grep`-failed case. That correction is written into the source comment too, because it
is the sentence a future reader would otherwise use to justify deleting the value test.

**Bar impact of the change: none.** It is comment text. The sweep still runs clean after it:
`SWEEP-RESULT: commit=009fae83 corpus=9237 selectors=16 did_not_run=0 refused=0 calibration=yes exit=0`,
all four CALIBRATE arms PASS [VERIFIED: run at that commit; `bash -n` clean].

---

## The buffered-writer drive

Instrument `.softhouse/capture/t424/instruments/t424-buffered-writer-drive.sh`; transcript
`out/T424-buffered-writer-drive.txt`; `arms_failed=0 runs_per_arm=8`, drive exit **0**.

**Neither guard is retyped.** Both are extracted by content from the shipped patch files — T402's
from `…/t402-t386-conditions/patches/FU-T386-7-…patch` (sha256 `f3c67070ad883a64`), mine from
`…/t424/patches/…AMENDED-BY-T424.patch` (sha256 `458753830160eb59`) — and extraction refuses unless
each anchor matches exactly once.

**The adversary is `T408`'s, made harsher.** `instruments/t424-buffered-tee-standin.py` is the same
construction, with a **1 MiB** file buffer instead of 64 KiB, so a whole realistic transcript fits
inside it and **nothing reaches the file until `close()`** — while stdout stays flushed, so the
failing arm is *visible on screen* the whole time the guard is reading a file that does not have it.

**RED — T402's shipped guard** [VERIFIED: transcript PART 1, 8 runs per arm]:

| arm | result |
|---|---|
| failing arm / host `tee` (BSD) | **8/8 exit 1** — correct. This is the case that was tried. |
| failing arm / buffered stand-in | **8/8 exit 0** — FAIL-OPEN. `T408` measured 3/3; I measured 8/8. |
| healthy / host `tee` | 8/8 exit 0 — correct pass |
| healthy / buffered stand-in | 8/8 exit 0 — correct pass |

**GREEN — the amended guard, same writers, same bodies** [VERIFIED: transcript PART 2]:

| arm | result |
|---|---|
| failing arm / **buffered stand-in** | **8/8 exit 1** — *the proof, on the case that broke it* |
| failing arm / host `tee` (BSD) | **8/8 exit 1** — the control that already worked, still green |
| healthy / buffered stand-in | 8/8 exit **0** — not vacuous |
| healthy / host `tee` | 8/8 exit **0** — not vacuous |
| drive dies early / either writer | 8/8 exit **2** — refuses rather than congratulating |

**The fix is structural, not a bigger buffer and not a sleep.** The script now **owns its
transcript**: the outer invocation re-execs itself, captures the run, and grades the file only
*after the writer has exited* — which the shell guarantees, because `bash` waits for every member of
a pipeline. There is no concurrent writer left to race, so there is no buffering behaviour left to
depend on. Two fail-closed checks sit beside it: the transcript must carry the drive's own
`END OF DRIVES.` sentinel **exactly once** (stdio flushes in order, so a transcript that reaches the
sentinel carried every earlier arm verdict), and the inner run's own status is read. `| tee` is no
longer prescribed to the caller and is no longer load-bearing.

**End-to-end on the real artefact** [VERIFIED: transcript PART 3]: with `BEFORE_REF=964b532e` the
real `t381-red-drives.sh` aborts at D-R2 (its BEFORE specimen has rotted) and exits **4**. With
T402's guard the exit is still 4 — **the tail guard is never reached**, which means on this tree it
is never exercised at all, so its buffering dependence would have been discovered by nobody. With
the amended guard the run refuses at **2** on both writers, naming the reason.

**Honest limits.** One host (macOS, BSD `tee`, `git 2.50.1`). The buffered writer is a **stand-in**,
not a measurement of GNU coreutils — same bound `T408` declared, and it is the right one. What is
proved is that the amended guard's verdict **does not vary with the writer**; what is not proved is
any claim about a particular `tee` binary.

**Row 5 of PART 1 is recorded so the finding is not overstated:** a drive that dies early is *not* a
fail-open in T402's guard. Every abort in `t381-red-drives.sh` uses a non-zero `exit`
[VERIFIED: `grep -n "^ *exit " t381-red-drives.sh` → only `exit 2` and `exit 4` paths], so the guard
is skipped and the script's own status is non-zero. I looked for that fail-open and did not find
it; I am saying so rather than banking it.

---

## What my own fix misses by one

### My own error, caught by my own control — and it is the same defect

The first amended guard read `_t424_inner_rc=${PIPESTATUS[0]}` and then `${PIPESTATUS[1]}` on the
next line. **`x=${PIPESTATUS[0]}` is itself a command and replaces `PIPESTATUS` with a one-element
array**, so the second read was an unbound variable, and under `set -u` bash killed the script with
status **1** — which looks *exactly* like a guard that caught a failing arm. The RED arms scored a
perfect 8/8 for the wrong reason. **The healthy control is what caught it** (8/8 exit 1 where 0 was
required) [VERIFIED: the first drive run, `arms_failed=6`, transcript superseded; the cause is
recorded in the shipped patch comment beside the fix]. A guard that refuses everything and a guard
that cannot fail are the same defect wearing opposite signs — `P-98`, paid for again, in the patch
written to close a fail-open.

### Neighbour census — guards that read a file another process is writing

Instrument `instruments/t424-neighbour-census.sh`; transcript `out/T424-neighbour-census.txt`.
Corpus **1457 tracked `.sh`/`.py` files under `.softhouse/`** — the denominator is printed, because a
census reporting "0 found" without saying how many it looked at is the fail-open it is hunting.

| search | result |
|---|---|
| **S-A** scripts that `tee` to a file and then read that same file | 23 files contain a `tee <file>`; **0** of them read the target. |
| **S-B** background jobs (`… &`, excluding `&&`/`2>&1`/`>&2`) | **3** files. `fire-program.sh` has 3 such lines and **`wait`s for every one before reading the file** — `wait_bounded "$job"` then `[[ -r "$vf" ]]`, and `wait "$DRIVER_JOB_PID"` then reading `$DRIVER_RC_FILE`. That is the same construction I chose, already the house pattern. `t309-…/patch5.py`, `patch6.py` are patch *generators* whose `&` lines are text destined for `fire-program.sh`; **not closed, and named here** — I did not verify that the text they emit still matches what `fire-program.sh` contains. `[UNVERIFIED]` |
| **S-C** `conformance.sh` itself | **0 tee sites, 0 background jobs.** The bar carries none of this class. |
| **S-D** shipped `.patch` files — *where the defect actually lived* | 9 tracked patches; **2** hits: T402's (the defect) and mine (the fix). A census over executable files only would have returned a clean zero for the very defect it is hunting, which is why S-D exists. |

**Named and not closed:**

- `t309-sigterm-reconcile-bypass/patch5.py`, `patch6.py` — background-job text in patch generators,
  0 `wait` statements in `patch6.py`'s own text. Whether the emitted text is still live in
  `fire-program.sh` is `[UNVERIFIED]`; I did not open the merge.
- `t284-schema2-callsites/instruments/30-red-drive.sh` — **not** an instance of this class (its
  verdict comes from `$bad`, a counter, not from re-reading `$TRANSCRIPT`), but it *is* a latent
  `K8`: `pass`/`bad` are incremented inside a function, and running `arm` in a subshell would
  discard them. All calls are bare today. `[VERIFIED: grep of that file]`

### Neighbour hunt — shipped comments whose stated cause I can falsify

Instrument `instruments/t424-comment-claims-drive.sh`; transcript `out/T424-comment-claims.txt`;
`disagreements=0`, drive exit **0**. Selection stated in the instrument: I searched `conformance.sh`
for comment lines matching
`^#.*(returns? [0-9]|exits? [0-9]|rc *= *[0-9]|prints? (0|nothing|empty)|pipefail|PIPESTATUS)`
(60+ lines) and kept the ones whose truth does not depend on a machine I do not have. **I did not
grade all 5,357 lines**, and I am not claiming the three below are the only ones.

| claim | verdict |
|---|---|
| *"In a UTF-8 locale BSD grep goes blind to the part of ONE LINE at and to the right of an invalid byte: count 0, exit 1, NO diagnostic. `LC_ALL=C` fixes that; `-a` does NOT."* | **REPRODUCES**, all four sub-claims, on `/usr/bin/grep 2.6.0-FreeBSD`. |
| *"`git grep` exits 1 on NO MATCH and >1 on ERROR, so the 1 is an ABSENCE and not a failure."* | **REPRODUCES**: no match → 1, invalid pattern → 128, match → 0. `git 2.50.1`. |
| *"`CONFORMANCE_REPO_ROOT` and `-repo-root` each occur ZERO times in it (measured … both returned 0, exit 1)."* | **`F-T424-N1` — DOES NOT REPRODUCE.** Re-running the stated recipe returns a **non-zero** count for `CONFORMANCE_REPO_ROOT`, on the whole file *and* on executable lines only. |

**`F-T424-N1`, stated carefully.** The paragraph is describing the pre-repair hole and was true when
written; the repair it argues for is what made it false. But the sentence is in the **present
tense** and carries its **own reproduction recipe**, so a reader who runs that recipe gets a
contradiction and no way to tell a stale sentence from a regressed harness. Same shape as `F-2`:
the finding is right and the *statement about the world* has gone wrong. **Not closed by me** —
`conformance.sh` is contended this fire and that region is not T424's. The correction is one
sentence: put it in the past tense and name the commit at which it held. Counts are deliberately not
pinned in this handoff (`P-86`).

### The taxonomy gap — K8, added and driven

`K1..K7` all enumerate ways an **exit status** is lost; `sel()`'s integrity also rests on **state
written into globals**, and a subshell discards that. `K8` and the `STATE-LOSS` verdict now exist in
`AUDIT-CLASS.md`, and `K8` is in the census itself.

**Re-measured on both refs** [VERIFIED: `out/T424-CENSUS-before-with-K8.txt`,
`out/T424-CENSUS-after-with-K8.txt`]: `K1..K7` reproduce `T402`/`T408` **cell for cell**
(before `22/31/40/0/0/3/28`, after `26/32/54/7/0/0/44`). `K8`: **17 before, 29 after**.

> **CORRECTED 2026-08-29 by T452 [`C-T440-2` / `F-T447-2`].** The paragraph below carried the
> published K8 split, whose three cells summed to **thirty** — not to this paragraph's own total
> of twenty-nine. `T442`'s erratum concluded that split lived in **one** site because
> `git grep 'all sixteen'` over `.softhouse/handoff/` returned nothing; here it was spelled as
> **words in running prose**, so that search could never have reached it. **`T440` was right:
> two sites.** The corrected partition, re-derived by `T452` from the subject file and again,
> independently, from the census transcript, is **`13 + 10 + 6 = 29`**.
> The superseded sentence is preserved verbatim in `git` history and quoted in
> `.softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md`; it is deliberately **not** re-spelled
> here, because re-planting the defect shape in the repaired file is how a corrected cardinal
> comes back (`P-80`). Drive:
> `.softhouse/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh`.

**All 29 adjudicated, and none is a live defect.** Thirteen of the sixteen `sel` calls reach the
wide list, because each of those carries a `|` **inside its own quoted ERE** — the same deliberate
over-inclusion `K2` and `K3` have; `S1`, `S3` and `S7` use `-F` patterns with no `|` and never
reach it, so **16 is a count of the FILE and 13 is the count IN THE CENSUS**.
Ten are `SWEEP_*=$((…))` counter rows over three distinct counters, matched on the `$(` of an
arithmetic expansion, which is not a subshell. Six are parent-side assignments (`SWEEP_ERRF=$(mktemp …)`,
`SWEEP_CORPUS_N=…`, …) whose command runs in a subshell but whose **assignment happens in the
parent**. `13 + 10 + 6 = 29`, which is the census's own printed `== K8 SITES: 29`.
**Live `STATE-LOSS` sites: zero, before and after** — measured, not assumed.

**The new kind is not decorative, and that is driven** — `instruments/t424-k8-discrimination.sh`,
transcript `out/T424-k8-discrimination.txt`, `arms_failed=0`. The specimen is built and graded in a
scratch git repo **under `/tmp`**, never inside this one:

```
GREEN (unmodified)  K8 wide = 29   K8s de-noised = 6    (no sel line listed)
RED   (S16 | cat)   K8 wide = 29   K8s de-noised = 7    (S16 listed)
```

The **wide** `K8` cannot discriminate — every `sel` line is already in it through the pipe in its own
pattern — and that is stated in the census rather than hidden. The **de-noised `K8s` view** is the
discriminator, exactly as `K2s`/`K3s` are for `K2`/`K3`, and it moves `6 → 7` the instant one
selector is spelled `sel … | cat`. This does **not** supersede `C-T408-2`, which remains mandatory on
`T399`: a census is read by a person, and the cardinal cross-check is read by the gate.

### WITNESS is an inference, not a proof

Corrected in the handoff, with both of `T408`'s defeats named — `A2` mid-window path substitution and
`A3` sentinel-not-alone — and with the bound stated honestly: neither is a natural failure mode, both
need an external agent inside a microsecond window, and in a whole-file run the next selector's PRIME
refuses, so the run exits 4 and at most one selector can fabricate. `A3` is closable by matching
*contains* rather than *equals*; `A2` is not closable without an inode check that would add a new
`K1` site, so leaving it open and documented is the better trade. **I changed the claim, not the
code** — the code was not what was wrong.

---

## Bar figures

`bash .softhouse/conformance.sh` on the finished, COMMITTED tree — see the block appended below at
the end of the run. All scratch worktrees were created under `/tmp`, never inside the repository
(`guard_no_narrow_catch_in_capture_rigs` walks recursively, so a nested checkout would trip a HARD
guard and exit 2 before the probe line prints).

Run **twice**, both times with `git status --porcelain` **empty** before starting: once at
`b9b8a3ef` (`out/T424-BAR.txt`) and again at `4a2d95cb`, the commit that carries this handoff
(`out/T424-BAR-final-commit.txt`). **Every figure below is identical in both runs**, so the
handoff text itself moved nothing. Both transcripts are 749 lines.

```
BAR_EXIT=0
grep -c 'probe = '  ->  1                       <- PRESENCE tested BEFORE value (P-84)
:201  reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
:713  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle,
                               7884 cells compared.
```

| pin the guards printed | measured | fire-start baseline | moved? |
|---|---|---|---|
| bar exit | **0** | 0 | no |
| `probe = ` lines present | **1**, reading `up` | 1, `up` | no |
| parity vectors / cells | **46 / 7884** | 46 / 7884 | no |
| `ledger parity` | **PASS 10 FAIL 0** | 10 | no |
| LEDGER money cells compared | **63 == pinned 63** | 63 == pinned | no |
| wrong ledger implementations killed | **15 of 15**, all through the harness | 15 | no |
| dead-path frontier | **11, pinned at 11** — `frontier == pinned (all 11 rows, by path)` | 11 == 11 | no |
| `T316-DEADPATH-CENSUS` | `deadFiles=75 **deadOccurrences=108** resolving=1397 indeterminate=117 prose=380` | 108 | no |
| tmp-path census | 18, pinned at 18; `census == pinned (all 18 sites, by path and source line)` | — | no |
| narrow-catch census | inspected 63 `.java` ≥ 63 tracked | — | no |
| dead-path frontier verdict | `GREEN, and the T323 reconciliation list is empty` | GREEN | no |

**Nothing on the fire-start baseline moved.** The one figure that did move is the dead-path
census **corpus**, `1410 → 1459` — that is the tracked-file denominator growing as this fire's
branches land, and it is a *derived floor*, not a pin. The pinned figure beneath it,
`deadOccurrences`, held at **108**, so my seven new artefacts added **zero** dead-path occurrences
and zero frontier rows.

**Every scratch worktree was created under `/tmp`** (`mktemp -d "${TMPDIR:-/tmp}/…"` in all four
drives; the K8 discrimination drive's scratch **git repo** is also under `/tmp`). Nothing nested a
checkout inside the repository, so `guard_no_narrow_catch_in_capture_rigs` — which walks
recursively rather than via `git ls-files` — was not tripped. **The `probe = ` line was PRINTED**;
its presence was tested before its value, because four exit-2 paths (including a failed HARD guard)
run before it prints, which would make "probe != up" trivially true against nothing at all.

---

## Unverified

- **The buffered writer is a stand-in, not a `tee` binary.** No claim is made about GNU coreutils'
  actual buffering. What is measured is that the amended guard's verdict does not vary with the
  writer, and that the old one's does. `[UNVERIFIED: any specific tee implementation]`
- **One host.** macOS, BSD `tee`, `/usr/bin/grep 2.6.0-FreeBSD`, `git 2.50.1`, `bash` (never `sh`).
- **`t309-…/patch5.py` / `patch6.py`** — I did not verify whether the background-job text they emit
  is still live in `fire-program.sh`. Named, not closed.
- **The comment-claim hunt is a sample, not a census.** Three claims driven out of 60+ candidate
  lines; I am not claiming the other 57 are sound.
- **`t381-red-drives.sh` was never run to completion** on any ref available to me: with
  `BEFORE_REF=main` it refuses (BEFORE and AFTER are the same file) and with `BEFORE_REF=964b532e`
  it aborts at D-R2 because its BEFORE specimen has rotted. So the GREEN arms of the amended guard
  are proved on synthetic bodies that reproduce the real drive's output shape, plus the real drive's
  real early death — **not** on a full healthy run of that drive, which I could not produce.
- **The bar was last run at `4a2d95cb`.** Commits after it (`2d271edf` and any that carry this
  sentence) add only handoff prose and a copy of the bar transcript — no instrument, no guard, no
  vector, no code. That last delta is `[UNVERIFIED]` by a bar run, and it is stated rather than
  glossed, because "the tree I graded" and "the tree I shipped" being the same thing is exactly the
  kind of claim this task is about.
- **I did not re-derive `T408`'s `A2`/`A3` defeats myself.** I corrected the claim to match what
  `T408` measured; I did not rebuild its defeat harness. `[UNVERIFIED by T424: the two WITNESS defeats]`

---

## Follow-ups

- **`FU-T424-1` (MINOR, named, not closed).** `F-T424-N1` — the `CONFORMANCE_REPO_ROOT` "occurs ZERO
  times" sentence in `conformance.sh` no longer reproduces its own recipe. One-sentence fix, past
  tense plus the commit at which it held. For the owner of that region; `conformance.sh` was
  contended this fire.
- **`FU-T424-2` (MINOR).** `t381-red-drives.sh`'s D-R2 BEFORE specimen has rotted — the drive cannot
  reach `END OF DRIVES.` on any ref I tried, so **`FU-T386-7`'s guard has nothing to grade yet**.
  Whoever applies the amended patch should fix the specimen in the same change, or the newly-honest
  exit status will only ever say `2`.
- **`FU-T424-3` (MINOR).** `A3` (WITNESS defeated by an appended sentinel) is closable by having
  `_errf_read` refuse when the text *contains* the sentinel rather than only when it *equals* it.
  `T408` flagged this as optional hardening; it flips T402's `Z6`, which is unreachable in practice
  because the sentinel carries `$$` and `$RANDOM`. Not done here — it is a code change to a merged
  repair, and the claim, not the code, was what `T424` was asked to correct.
- **`FU-T424-4` (INFO).** `t284-…/30-red-drive.sh` is a latent `K8`: `pass`/`bad` counters mutated
  inside `arm()`. All calls are bare today. Worth a `K8` row if that file is ever restructured.
- **`FU-T424-5` (INFO).** The `K8` census over-includes by design and its wide count cannot
  discriminate; the discriminating view is `K8s`. Anyone gating on `K8` must gate on `K8s`, and
  neither is a substitute for `C-T408-2`.
