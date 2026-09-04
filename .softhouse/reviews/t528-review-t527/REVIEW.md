# T528 — independent review of T527, the branch-published guard

Reviewer: T528. Subject: `48c96cd1` + `f7e8014a` on `softhouse/T527-branch-published-guard`,
merged to `origin/main` at `21e735ae`.
Reviewed on `origin/main` in an isolated worktree. Everything below was **re-derived by
running the tool**, not read out of the handoff; the handoff was opened last, only to check
whether it claims anything I disproved (§7).

## VERDICT: ACCEPT WITH CONDITIONS

The guard is real. It is red on `main` today, it names all five incident tasks and their
three dependents, it is wired into the thing the orchestrator actually runs, it has no
escape hatch, and it fails closed on every arm I could attack but one. Reverting it would
be strictly worse than keeping it.

But it closes **the incident that happened**, not **the class**. Three MAJOR findings below
are all the same shape: a control that recognises the 2026-09-04 incident by name or by
phrasing, and lets the next one through. That is the exact critique T527 levels at the rest
of the toolchain, one level in. Conditions 1–3 close the class; they are sized against the
real record so they are affordable, not aspirational.

---

## Branch proof (the thing this guard exists to enforce)

```
$ git ls-remote --heads origin refs/heads/softhouse/T528-review-t527
a6c4f7372ab04038e6c106b8f25adaa99fa25144	refs/heads/softhouse/T528-review-t527
```

This review is of the guard that exists *because* five branches were never pushed. The
branch above is on origin, checked by the tool being reviewed and not by assertion. The
commit carrying this file is `a6c4f737`; a later commit adds this proof block itself, so
the tip moves — `git ls-remote` above is the claim, and it is re-runnable.

---

## Findings

### F-1 — MAJOR. `LANDING` is the DEFAULT, so the R5 fix closed one phrasing, not the class. A one-word edit to T509's note on `main` clears its missing branch today.

T527 shipped a defect and removed it: the first build let any anchored sha prove landing, so
T508's own note — citing `merge-base 10baca08` — cleared its own missing branch. The fix
tags each anchor `LANDING` or `REFERENCE`, and `R5-merge-base-does-not-prove-a-branch` is
the regression control.

**The fix is a phrase blocklist with a fail-OPEN default.** `CLAIM_ANCHORS` has exactly two
`REFERENCE` entries (`merge[ -]base <sha>`, `based? on <sha>`); every other anchor, and the
whole `stack …` region, is `LANDING`. So any base citation phrased in a way those two
patterns miss is read as proof that the work landed.

I built a fixture whose branch is genuinely absent from origin and whose note names a sha
that IS on `origin/main` — a legitimate reference commit, i.e. the T508 shape. Twelve
phrasings, `probes/attack.py`, transcript `probes/out-attack.txt`:

| case | note | got | want |
|---|---|---|---|
| A | `done and scope-checked (merge base X)` | 2 REFUSE | 2 — R5's shipped control, holds |
| **B** | `done; merge-base commit X, scope clean` | **0 CLEAN** | 2 |
| **C** | `branched from main @ X; work is on the branch` | **0 CLEAN** | 2 |
| **E** | `based on softhouse/TP-pushed (X) -- stacked on top` | **0 CLEAN** | 2 |
| **G** | `reviewed T400 which landed X; my own work is on the branch` | **0 CLEAN** | 2 |
| **H** | `diverges from origin/main at commit X` | **0 CLEAN** | 2 |
| **K** | `stack X (T400 base) -> my work` | **0 CLEAN** | 2 |
| **L** | `supersedes the work merged as X by T400` | **0 CLEAN** | 2 |
| D, F, J | `forked at X` / `rebased onto X` / `cherry-picked from X` | 2 REFUSE | 2 |
| I | `landed X on softhouse/TN-never-pushed` | 0 CLEAN | 0 — legitimate |

**Seven breaks.** Case B is the load-bearing one: it is `merge-base commit X` — the same
semantic content as T508's own note, one word apart, and it defeats the control written to
stop it.

This is not hypothetical. **I reproduced it on the real record.** T509's note on `main`
reads `landed 857dd4d8 on softhouse/T509-ledgerguard-blindspot (merge base 10baca08)`.
Changing exactly `(merge base 10baca08)` → `(merge-base commit 10baca08)`, nothing else:

```
before:  UNBACKED-BRANCH  T509  softhouse/T509-ledgerguard-blindspot   (21 findings)
after :  WAIVED (merged-and-pruned, PROVED)  T509  softhouse/T509-ledgerguard-blindspot
         (20 findings)
```

T527 tells the reader the repair is one of two things: push the branch, or correct the note
to say UNRECOVERED. **There is a third the tool does not name and cannot detect: reword the
note.** For a task whose sha is not itself unbacked, that reword is a complete silencing.
(`tasks.json` was restored; `git status` clean.)

**The mechanism that closes it — measured, not guessed.** The naive rule ("a sha proves
landing only when the phrase binds it to a branch this task claims") destroys 71 of the 73
legitimate PRUNED-PROVED waivers, because the pipeline's own merge vocabulary is
`MERGED at <sha> by fire …`, which names no branch. Unaffordable. The affordable form is a
**dominant REFERENCE veto plus two demotions** (`probes/measure2.py`,
`probes/out-proposed-fix.txt`):

* **V** — a sha whose preceding ~40 chars contain a base-citation word
  (`merge base|based on|branched from|forked|diverges|rebased onto|ahead of|behind|head|hiding`)
  is `REFERENCE` regardless of which anchor caught it;
* **V2** — a sha preceded within ~40 chars by a *different* task id is `REFERENCE`;
* **D1** — `commit <sha>` demoted `LANDING` → `REFERENCE` (it carries 1 of 81 legitimate
  proofs and is what lets case B through);
* **D2** — the `stack …` region demoted to `REFERENCE` (it is a dependency chain of *other*
  tasks' commits, by construction a base description);
* **D3** — `<branch> (<sha>)` proves `LANDING` only when `<branch>` is one this task claims.

Cost on the real record: **66 of 73 PRUNED-PROVED waivers survive; 7 become findings.**
Effect on the probe: **6 of 7 breaks close and all four legitimate phrasings stay green**
(`landed X on <branch>`, `MERGED at X by fire …`, `COMPLETE @ X`, `tip X`). Case L
(`merged as X by T400` — the other task's id *follows* the sha) still leaks; V2 needs a
trailing arm as well as a leading one. That is honest sizing, not a finished patch.

**Small enough to be a condition**, because the anchor table is one data structure and the
selftest already has the paired-control shape to extend.

### F-2 — MAJOR. `proved_on_main` is scoped per TASK, not per BRANCH. One landing sha waives every branch the task names — including another task's branch. Live on `main` right now.

`check()` collects `proved_on_main` across the whole task, then the branch loop does
`if proved_on_main:` for **every** branch that task claims. A task that names two branches
and landed one waives both. A review or repair task that mentions the branch it reviewed
waives that branch too.

On `main` today (`probes/unc2.py` inputs, `--json` output):

```
T375  landing sha waives  softhouse/T375-t364-conditions
                     AND  softhouse/rescued-agent-ac5a2db446e903ba0-20260828-140005
T476  landing sha waives  softhouse/T476-t472-repair
                     AND  softhouse/T467-t464-conditions      <- T467's branch
T477  landing sha waives  softhouse/T477-t473-repair
                     AND  softhouse/T466-skipwt-smudge        <- T466's branch
```

T466's and T467's branches are being cleared by T476's and T477's landing commits. This is
the same cross-task leak as F-1 case G, reached through the data structure rather than the
regex. It matters because the incident's own dependents (T520/T522/T523) name the incident
branches in *their* notes: if any of those three had a landing sha of its own on main, it
would waive the incident branch it names. The guard survives on `main` today by luck of
which tasks happened to land.

Fix is small and local: make `proved_on_main` a map from branch → proving sha, populated
only by an anchor that binds the sha to that branch (D3 above), and fall back to the
task-wide set only for the task's own `branch`/`branch_mac`/`branch_cloud` fields.

### F-3 — MAJOR. The baseline lock-out protects the eight known task ids and five known shas, and nothing else. Incident #2 is laundered by one `--write-baseline` run, which prints a reassuring "REFUSED TO WAIVE 0 finding(s)".

T527 discloses this risk in the module docstring and the handoff. **Disclosure is not
mitigation**, and the brief is right to ask what happens to incident number two. I measured
it (`probes/incident2.py`, `probes/out-incident2.txt`). A new task `T540` records a branch
and a commit that never reached origin:

```
1. before any baseline        -> exit 2
     UNBACKED-BRANCH  T540  softhouse/T540-critical-path
     UNBACKED-COMMIT  T540  deadbe1f
2. --write-baseline           -> exit 0
     WAIVE  UNBACKED-COMMIT  T540  deadbe1f
     WAIVE  UNBACKED-BRANCH  T540  softhouse/T540-critical-path
     REFUSED TO WAIVE 0 finding(s) -- these are the 2026-09-04 incident and no
     regeneration may launder them:
3. re-run                     -> exit 0  CLEAN
```

The "REFUSED TO WAIVE 0" line is the worst part: it reads as an assurance in a run that
just laundered a lost critical path. `INCIDENT_TASKS` / `INCIDENT_SHAS` are hardcoded
tuples of the incident that already happened — a blocklist, protecting against exactly one
event.

Also, the lock-out is **case-sensitive on the task id**: a record spelling the id `t508`
(this repo already carries lowercase branch names such as `softhouse/t297-review-t295`)
gets its branch waived; only the sha lock-out holds, and only because it matches the
subject rather than the id.

**The mechanism that closes it, and it is genuinely small: freeze the baseline by
generation, not by name.** Record in `baseline.json` a `frozen_above` marker — the highest
task id present when the file was first written (`T527`) — and have `--write-baseline`
refuse to waive any finding whose task id sorts above it, or whose id does not parse as a
known historical form. A historical claim has, by definition, a historical id; a future
incident is by construction above the line and becomes unwaivable without a human editing
`frozen_above`, which is a one-line diff a reviewer will see. This closes the class, is
~10 lines, and needs one selftest case ("a finding above the freeze line is refused by
`--write-baseline`"). It costs nothing legitimate.

### F-4 — MINOR. Three genuine unpushed-work commit claims are sitting in the 217-token "NOT CHECKED" bucket. The handoff's "found no missed commit claim" is not sustained.

I sampled the bucket properly rather than eyeballing it (`probes/unc2.py`). Headline first:
the printed figure **overstates** the blind spot — 978 occurrences / 217 distinct, but the
same sha is reported both as a finding and as unclassified when it appears twice in one
note. Filtering to *(task, sha)* pairs that are checked nowhere, and to tokens that resolve
to no commit here, the true residue is **41 distinct tokens**.

Of those 41 the overwhelming majority is safe — md5/sha256 file digests, capture digests,
request shas, blob hashes from the smudge-forgery work (`committed 6cfe77d5, on disk
52ac335f`), and the pinned Fineract commit. **Three are not:**

```
T335  "branch softhouse/T335-rvpa-list-traversal has 3 commit(s) ahead of main,
       head d09585f58"                                    <- an unpushed branch HEAD
T312  "exactly 2 shadow groups, T297 hiding c1a3888a (4 commits) and T305 hiding
       060f00330 (8), both diverged"                      <- two unpushed shadow heads
```

None of `softhouse/T335-*`, `softhouse/t297-*`, `softhouse/t305-*` is on origin
(`git ls-remote` returns nothing for them), and all three tasks' branches are **in the
baseline**. So both arms miss the same claim: the anchor list has no `head X` / `hiding X`
phrasing, and the baseline waives the branch. **F-3 and F-4 compound** — this is what an
unchecked bucket beside a waived branch looks like when a real claim is in it.

Not MAJOR, because these are historical and the branch arm did produce the finding before
the baseline swallowed it. But the handoff's "I classified a sample by hand … and found no
missed commit claim" should be corrected: there are missed commit claims, and they are the
exact shape the guard exists for.

### F-5 — MINOR (tending MAJOR). The wiring believes any exit-0, including a two-line stub that prints nothing. That is a de-facto disable.

`branch_published_gate()`'s docstring promises: "If the checker is missing, unreadable,
times out or answers with a code this function does not recognise, that is NOT a pass."
Cell D of `drive-wiring.sh` covers *deleted*. It does not cover *replaced*. Replacing
`check-branch-published.py` with

```python
import sys
sys.exit(0)
```

makes `ready-tasks.py` exit **0** on a record whose branch was never pushed
(`probes/fc2.py`, cell I2). The wiring already captures `res.stdout` and prints it; it just
does not read it.

T527 is right that there is no `--offline` flag (I grepped: no `--offline`, `--no-fetch`,
`--skip`, `--force`, and no env-var bypass in either file). But the escape hatch it refused
to build exists anyway as a file overwrite, and this program's recorded failure mode is a
red guard being "fixed" rather than the red thing. Two lines close it: require
`"check-branch-published: CLEAN"` in `res.stdout` before believing `returncode == 0`.

### F-6 — MINOR. The inline comment at `check-branch-published.py:519` states the opposite of what the code does.

```python
# --- commit arm. Never baselined; see the module docstring.
```

The commit arm **is** baselined — the baseline is applied at line 566 "to both arms alike",
and `baseline.json` contains 9 `UNBACKED-COMMIT` entries (T122, T329, T351 ×2, T369, T370,
T472, T473, T474). A reviewer who trusts that comment believes the commit arm is
un-waivable. In a guard whose whole thesis is "the record asserted something the tree does
not support", a comment asserting something the code does not do is the same defect one
level in.

### F-7 — MINOR. A malformed *current* `tasks.json` exits 1 with a traceback, not the documented 5.

The checker handles it correctly (exit 3, `UNREADABLE TASK RECORD`) and the gate prints
`>>> THE CHECK COULD NOT LOOK`, but `ready-tasks.py` then crashes in its own `load()` on the
same file and exits **1**. Fail-closed (non-zero, loud), so not a hole — but the exit-code
table added by T527 documents 5, and a caller keying on `== 5` misreads it. A malformed
*archive* under `runs/` is handled correctly and does exit 5.

### F-8 — MINOR. `check-branch-published.py --json` emits prose on stdout and JSON on stderr in the exit-3 arm.

```
$ check-branch-published.py --repo /tmp --json    # rc=3
==============================================================================
check-branch-published: REFUSE -- CANNOT ESTABLISH ORIGIN
```

`ready-tasks.py --json` is unaffected (F-11 below confirms it stays valid), but a caller
parsing the checker's own stdout gets a banner exactly in the arm it most needs to detect.

### F-9 — MINOR. 570 lines of STEP 0 precede the ready list on every run, 314 of them baseline waivers — and `SKILL.md` never mentions exit 5.

The tool argues, correctly, that "an unreadable report is an unread one" — and then prints
every one of the 314 baseline waivers on every invocation. On the real repo the ready list
starts at line 587 of 684. Print the count and a pointer; put the full enumeration behind a
flag or leave it in the committed file where it already lives.

Relatedly: `.claude/skills/softhouse/SKILL.md` and `softhouse-program/SKILL.md` tell the
driver to run `ready-tasks.py` but say nothing about exit 5 or the STEP 0 block. T527's own
`P-45` argument — a guard nobody is told to honour enforces nothing — applies to the
procedure as well as the code. The refusal is loud enough that an agent reading the output
will see it, which is why this is MINOR and not MAJOR.

### F-10 — MINOR. The deepen is a silent write inside a report.

`establish_origin()` runs `git fetch --unshallow` and `git fetch +refs/heads/*:refs/remotes/origin/*`
without printing that it did. The STEP 0 block never tells its reader that the report
mutated the object store. One line of output.

---

## Checks that came back CLEAN

Listed because "finding nothing" is only legitimate when the checks are named — and because
several of these are the arms the brief asked me to go past.

**F-11 — the shallow correction is sound (item 5): right call, adequately bounded.**
Built a real shallow clone (`--depth 1` over `file://`; note `--depth` is silently ignored
for local-path clones, which is how a casual test would miss this) with a
merged-then-pruned branch (`probes/shallow.py`, `probes/out-shallow.txt`):

| | result |
|---|---|
| full clone, control | exit 0 CLEAN |
| shallow, tool as shipped | exit 0 CLEAN, `is-shallow` flips `true`→`false` — it **deepened** |
| shallow, `fetch --unshallow` forced to fail | **exit 3** `REPOSITORY IS SHALLOW AND COULD NOT BE DEEPENED` |
| shallow, the `is-shallow-repository` probe forced to fail so the tool believes it is deep | **exit 2** with a false finding — loud, **not** a silent mis-answer |

It deepens-or-refuses as claimed, and the one path where the probe itself fails errs toward
refusal rather than a quiet pass. On the side effect: unshallowing the **shared** object
store is outside the four declared files, and T527 flagged it. I judge it the **right call,
adequately bounded** — ancestry is genuinely undecidable across a graft boundary, the
alternative (refuse) would halt the program on every CI clone, the fetch is additive with
no `--prune`, and the refuse arm exists for when it cannot. The only debt is F-10, that it
happens without saying so.

**F-12 — fail-closed beyond the one driven cell (item 4).** `probes/failclosed.py`,
`probes/fc2.py`. Every cell reads `ready-tasks.py`'s own exit code, not the checker's.

| injury | result |
|---|---|
| control: uninjured clean fixture | **0** — the control that can PASS |
| `git` hangs (PATH shim sleeping past `--timeout 3`) | **3** CANNOT ESTABLISH ORIGIN |
| `ls-remote` exits 0 with garbage on stdout | **3** `ORIGIN LISTED NO BRANCHES` |
| `ls-remote` exits 0 with a partial ref set (main only) | **2** REFUSE — loud, never a pass |
| archive `runs/*.tasks.json` unparseable | **5** `UNREADABLE TASK RECORD` |
| archive with no `tasks` list | **5** `TASK RECORD HAS NO tasks LIST` |
| malformed `baseline.json` | **5** (checker tracebacks; wrapper catches the unknown code) |
| checker raises **mid-run** (injected inside `check()`) | **5** `exited 1, which this wrapper does not recognise. NOT a pass.` |
| checker deleted | 5 (T527's cell D, reproduced) |

Nine of ten arms fail closed. The tenth is F-5. Note two of these were my own test-design
errors first time round — `chmod 000` does nothing when running as root, and a `raise`
appended after `SystemExit` never executes; both cells were rebuilt before being scored.

**F-13 — merging it does not make the program unworkable (item 6).** On the real repo:
`ready-tasks.py` exits 5 in **2.65 s** and still prints the whole report — `IN PROGRESS (2)`
at line 570, **`READY (62)` at line 587**, `BLOCKED (14)` at line 657, verdict repeated at
681. The driver can read and act on the READY list through the refusal. In `--json` mode
stdout parses as JSON, carries `"branch_published": "NOT_CLEAN"` alongside `ready`, the
2,236-byte report goes to stderr, and the exit code is 5. `--reconcile` is dispatched in
`cli()` before `main()`, so it does not run the gate — matching the docstring. **The escape
is repair, not a flag:** no `--offline`, `--no-fetch`, `--skip`, `--force`, no env-var
bypass (F-5 is the unintended one).

**F-14 — `--selftest` reproduces**: 23 cases, 0 failures, including
`G-BASELINE-EXCLUDES-INCIDENT` (314 entries, incident tasks present: none). Every RED is
paired with a subject-removed GREEN; the anti-vacuity case
`G-PRUNED-anti-vacuity-proof-removed` is the right instinct and does its job.

**F-15 — the guard is red on `main` and names the incident**: exit 2, **21 findings** —
`UNBACKED-BRANCH` for T508, T509, T510, T512, T515 plus the three dependents T520, T522,
T523, and `UNBACKED-COMMIT` for the shas. (The driver saw 18; the count has grown with
later records, not shrunk.)

**F-16 — scope (item 7), merge-base form.**
`git diff --stat $(git merge-base 21e735ae^1 21e735ae^2)...f7e8014a` = **8 files, all under
`.softhouse/`**: the two tools, five capture files, one handoff. `nexus/`, `conformance.sh`
and `.softhouse/guards/ledgerguard/` are untouched. No Go, no schema, no vectors.

**F-17 — money non-negotiables.** No monetary code path in the diff. The only `float(` is
`--timeout` parsing, which is a duration, not money. No `first_name`/`last_name`, no
hard-coded tz offset, no MySQL/MariaDB/Oracle driver or dialect, no US rails/vendors, no
deposit-insurance language. Clean.

---

## §7 — the handoff, read last

Honest and unusually self-aware; §6 "what a reviewer should attack" pointed at two of the
three MAJORs before I found them, which is to its credit. Two claims do not survive:

1. **"217 distinct hex tokens … I classified a sample by hand … and found no missed commit
   claim."** Not sustained — F-4 names three (`d09585f58`, `c1a3888a`, `060f00330`), all
   claims about branches that are not on origin. Correct the sentence.
2. **"The tool now tags each anchor LANDING or REFERENCE; only LANDING can prove."** True as
   written, but presented as if the class were closed; F-1 shows seven paraphrases still
   read as LANDING, one of them a one-word variant of T508's own note. The residual belongs
   in §6 next to the baseline paragraph.

Everything else I checked in it holds: the shallow measurements, the wiring cells, the
selftest transcript, the scope statement, and the ls-remote proof in §8.

---

## CONDITIONS

Each is independently checkable. 1–3 close the class; 4–5 are cheap and close real holes.

1. **Flip the classifier default to `REFERENCE`.** Apply the dominant base-citation veto V,
   the different-task veto V2 (with a **trailing** arm as well as a leading one, so case L
   closes), and demotions D1/D2/D3 from F-1. *Checkable:* `probes/attack.py` must report
   **0 breaks** (all 12 cases), `--selftest` must stay green, and the PRUNED-PROVED count on
   `main` must land at ≥66 of 73 with the newly-red branches enumerated rather than
   baselined blind. Add the seven attack notes to `--selftest` as paired
   RED/subject-removed-GREEN cases, so the class has a regression control and not just
   `merge base`.

2. **Scope `proved_on_main` per branch (F-2).** A landing sha may waive only a branch the
   same phrase binds it to, or the task's own `branch`/`branch_mac`/`branch_cloud` field.
   *Checkable:* T476 no longer waives `softhouse/T467-t464-conditions`, T477 no longer
   waives `softhouse/T466-skipwt-smudge`, and a new selftest case asserts a two-branch task
   with one landing sha waives exactly one branch.

3. **Freeze the baseline by generation, not by name (F-3).** Add `frozen_above` to
   `baseline.json`; `--write-baseline` refuses any finding whose task id sorts above it, and
   says so. Also case-fold the `INCIDENT_TASKS` comparison. *Checkable:*
   `probes/incident2.py` must report `INCIDENT #2 … still refused` at step 3, and the
   lowercase-`t508` cell at step 5 must show the branch KEPT, not WAIVED.

4. **Make the wiring verify the checker actually answered (F-5).** Require
   `"check-branch-published: CLEAN"` in the checker's stdout before treating `returncode == 0`
   as a pass. *Checkable:* `probes/fc2.py` cell I2 (silent exit-0 stub over a dirty record)
   must make `ready-tasks.py` exit 5, and `drive-wiring.sh` gains a fifth cell for it.

5. **Correct the two false statements and say what the tool did (F-6, F-10, and §7).** Fix
   the `:519` "Never baselined" comment; print the fetch/unshallow when it happens; correct
   the handoff's "found no missed commit claim" and name `d09585f58` / `c1a3888a` /
   `060f00330` as the counter-examples. *Checkable:* by reading the diff.

**Not conditions, recorded as debt:** F-7 (exit 1 vs 5 on a malformed current `tasks.json`),
F-8 (`--json` prose on stdout in the exit-3 arm), F-9 (the 314-line waiver dump and the
`SKILL.md` silence on exit 5). None of them lets a false claim through; all three are worth
a follow-up task.

---

## One sentence for the driver

Keep it, keep it red, and do not let the note-rewording path in F-1 become the repair —
the record is corrected by pushing the branches or by writing UNRECOVERED, and this review
exists partly to make sure that a third option is not quietly available.
