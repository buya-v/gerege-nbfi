> **THIS IS ATTEMPT 1, AND IT GRADES T288's PRE-T309 BYTES.** It was written from a
> worktree forked at `5964ab5`, before T309 (`2dfbe422`) landed, and the attempt was
> killed before it could be reviewed. **Read
> [`REVIEW-A2.md`](REVIEW-A2.md) first** — attempt 2 grades T288 *as it stands on `main`
> after T309*, says which of F1-F4 below T309 closed (defect 1 only; F1, F2, F3 are all
> still open and F1 is now confirmed on real corpse data), and adds F5-F11. Everything
> below still stands on its own bytes.

---

# T302 — INDEPENDENT review of T288

**Subject** T288, "the wrapper repairs the exit-protocol lie instead of warning about it".
Merge `d8cf2c1`, worker commit `37425ee`, predecessor `83dd99a`. Files: `.softhouse/bin/fire-program.sh`
(+327), `.softhouse/bin/ready-tasks.py` (+378), a handoff and a drive harness.
Read from the merge commit on `main`, not from disk — T288's branch was merged and pruned.

**Reviewer** T302, branch `softhouse/T302-review-t288`, isolated worktree
`agent-af389a54fb1b2ca43`, forked from `5964ab5`.

## VERDICT: REJECTED

Four defects, three of them driven to bytes in this review, none of them the one already
filed as T309. Two are fail-OPEN in the direction that lets the reconciler act when it
should not, or record a false fact as evidence; one is fail-CLOSED into inertness, which is
the failure T288 was written to remove; one is a false claim printed into the tool the next
driver reads at STEP 0 — the P-45 lineage, in the fix for P-45.

T288's core judgement — REPAIR the two artefacts the next fire reads, rather than WARN —
is **right**, and should survive. What is rejected is the implementation of the evidence and
of the liveness gate. The remedy is bounded: roughly 25 lines across two files, plus one
filed task. It is above the MICRO-FIX ceiling and it is not mechanical, so it goes back.

---

## Bar

`bash .softhouse/conformance.sh` re-run by this reviewer, staged first, unpiped:

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
    oracle probe    UP
    parity vectors          PASS 46   FAIL 0
    cells compared          7884 graded, 93 ungraded
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
[exited with code 0]
```

**P-84** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."*
(`patterns.md:2782`). Read in that order: exit 0; probe-line **count 1**, PRESENT; value `up`.
Identical to the bar the driver recorded on `main` at my fork point (exit 0, probe present
reading `up`, 46 vectors / 7884 cells). Nothing in this review touches graded code, and none
of the findings below moves a money cell. [VERIFIED: run captured this fire]

---

## F1 — REJECT. The demotion note states the OPPOSITE of the truth for a branch that was MERGED, and offers merged work back for re-dispatch

**Where** `.softhouse/bin/ready-tasks.py`, `branch_wip()`, the `rev-list --count main..<branch>`
leg. Consumed by `reconcile()` (the note written into `tasks.json`) **and** by `main()` (the
`IN PROGRESS` listing every driver reads at STEP 0).

**Driven, not argued** — `.softhouse/reviews/T302/drive-branch-wip.sh`, transcript
`out/1-branch-wip-merged.txt`. A scratch repo with four `in_progress` tasks and real git history:

| task | ground truth | the note T288 writes |
|---|---|---|
| `T-merged` | one commit, **merged into main** by `git merge --no-ff` | *"exists at d0572f40e but has **NO commit ahead of main — nothing was ever committed to it**"* |
| `T-pruned` | one commit, merged into main, **branch then deleted** | *"**does not exist in this repo** — no WIP was found under that name"* |
| `T-real` (control) | one unmerged commit | *"has 1 commit(s) ahead of main, head e3d2a5c14"* — correct |
| `T-nobr` (control) | no branch recorded | *"suspect an isolation violation"* — correct |

Both false notes are written to `tasks.json`, both tasks are demoted to `needs_retry`, and
`needs_retry` is what offers a task to the next fire. So the next fire is invited to
**re-dispatch work that is already on `main`**, holding a note that says nothing was ever done.

**Re-derived.** `main..B` is `B` minus everything reachable from `main`. When `B` has been
merged, every commit of `B` **is** reachable from `main`, so the range is empty **because the
work landed**. `branch_wip` reads empty-range as "nothing was ever committed". The two states
are not distinguishable by that expression and never were. The discriminator was sitting in
the same repo: `git branch --merged main` printed `softhouse/T-merged` three lines above the
reconcile in the same transcript. `git merge-base --is-ancestor <B> main` is the one-line form.

**Is the window real?** Yes, and it is the routine one. This program merges each worker
branch and then updates `tasks.json` to `done`; a fire interrupted between those two steps
leaves `in_progress` + merged branch. That gap is repeated once per worker per fire — eight
times in the fire this review runs inside. Pruning after merge is this repo's stated habit
(this very task's brief: *"T288's branch was merged and pruned"*), which produces the
`T-pruned` row.

**Direction.** Fail-OPEN in the evidence: the confident, blaming answer is printed when the
truth is the opposite, and the consequence is duplicated work under a false record. A note
that cannot tell "merged" from "never started" must say so; it must not pick one.

**Remedy** (author's call, not a micro-fix): in `branch_wip`, before the `main..B` count,
ask `git merge-base --is-ancestor B main` and return a distinct kind — `merged` — with text
naming the merge. In the `absent` (branch gone) leg, say *"not found — this is what a MERGED
AND PRUNED branch also looks like; provenance UNVERIFIED"* rather than *"no WIP was found"*.
A task whose branch is merged should not be demoted to `needs_retry` at all without a louder
note, because `needs_retry` means "do it again".

---

## F2 — REJECT. The worktree sweep claims a rescue it did not perform, and T288 promoted that claim into `tasks.json`

**Where** `.softhouse/bin/fire-program.sh:891-901`. The rescue leg of the worktree sweep:

```
git -C "$W" checkout -q -b "$WB" 2>/dev/null        # rc discarded
git -C "$W" add -A >/dev/null 2>&1                  # rc discarded
git -C "$W" ... commit -q -m "RESCUED: ..." ...     # rc discarded
log "rescued $WN -> $WB"                            # printed unconditionally
```

**Driven** — `.softhouse/reviews/T302/drive-phantom-rescue.sh`, transcript
`out/2-phantom-rescue.txt`. Subject: a linked worktree holding an uncommitted deliverable,
with the stale `index.lock` a `git add` interrupted by SIGKILL leaves behind at
`.git/worktrees/<name>/index.lock`. Result:

```
checkout -b rc=128    add -A rc=128    commit rc=128
log line:  rescued agent-deadbeef -> softhouse/rescued-agent-deadbeef-20260823-140001
GROUND TRUTH: that branch DOES NOT EXIST; worktree still dirty [?? deliverable.md]
```

This is not a contrived fault. A SIGKILLed worker is exactly the population this sweep
serves, and any other cause with the same signature (read-only FS, disk full, a corrupt ref,
a `$WB` that already exists) produces the identical outcome — because the outcome does not
depend on **why** git failed. None of the three rcs is read.

**What makes it T288's problem and not just inherited debt.** T288 changed this loop: it
indexed it and added `RESCUE_PAIRS+=("$PRIOR=$WB")`, then handed those pairs to
`reconcile_tasks_json` (`:1032`) → `ready-tasks.py --rescue`, which writes into the task's
permanent note:

> *"Uncommitted WIP left in its worktree was swept onto `softhouse/rescued-agent-deadbeef-20260823-140001` by this fire's worktree sweep."*

An unread rc used to produce a wrong line in a log nobody reads. T288 promoted it to a
durable, evidence-shaped claim in `tasks.json` — the artefact T288 itself argues is the only
one the next fire believes. The blast radius went up; the verification did not.

**And the fix already exists 100 lines above, in the same function.** The MAIN-TREE rescue
at `:783-797` reads `ADD_RC` and `COMMIT_RC` and logs *"NOTHING was rescued"* on either
failure. T202's comment there describes this exact failure in the past tense — *"the guard
still logged `rescued: committed the leftovers`"* — and declares `POLARITY: fail-CLOSED`.
That fix was applied to one branch of the function and not the other. T202 called its own
find "THE UNFIXED TWIN … twenty lines below its patch and inside the same function". This is
the twin's twin.

**Direction.** Fail-OPEN. The reassuring answer is printed on failure, the deliverable stays
stranded, and the record says it was saved.

**Remedy.** Check all three rcs; on any failure log *"NOTHING was rescued"* naming the rc, and
**do not** append to `RESCUE_PAIRS` — an unverified rescue must not become evidence. Mirror
the `:783-797` shape verbatim.

---

## F3 — REJECT. `foreign_live_session_in_repo()` fails in BOTH directions from one line, and its declared polarity holds only for the case T288 measured

**Where** `.softhouse/bin/fire-program.sh:684-737`, filter at `:704`:
`[[ "${first:t}" == claude ]] || continue`.

**Declared contract, quoted from its own header** (`:679-683`):

> *"POLARITY: fail-CLOSED, three-valued. 0 = a live foreign session WAS found → caller must
> not reconcile. 1 = none found, and every candidate was decided → caller may reconcile.
> 2 = could not establish … Only 1 authorises the rewrite. **"I could not tell" is never
> spelled like "nobody".**"*

**Driven on its own bytes** — `.softhouse/reviews/T302/drive-probe.sh` cuts lines 684-737 out
of `fire-program.sh` and `eval`s them; the single edit (rebinding the absolute token
`/bin/ps`) is declared in the script. The subject is **this fire's own live driver, pid 4692**,
so `kill -0` succeeds and no candidate is discarded for the wrong reason. Transcript
`out/3-liveness-probe.txt`.

```
CASE 0 control, real ps + real lsof:  examined=1 in-repo=1  -> 0 REFUSE      (correct)
CASE 1 same live pid, f[3]="/Applications/Claude" (spaced install path;
       a `node .../cli.js` wrapper launch has the identical signature):
                                      examined=0 in-repo=0  -> 1 MAY RECONCILE
CASE 2 live claude, idle, cwd = the project root, NOT this fire:
                                      examined=1 in-repo=1  -> 0 REFUSE
CASE 3 control, T288's measured case, cwd = /Users/buv:
                                      examined=1 in-repo=0  -> 1 MAY RECONCILE (correct)
```

**F3a — fail-OPEN.** `:704` is a one-way filter. A process it does not recognise increments
neither `checked` nor `unknown`, so it can never reach `(( unknown )) && return 2`. With
`examined=0` the function falls through to `return 1` — the value that **authorises rewriting
`tasks.json`** — while a session that is genuinely working in the repo runs on. The evidence
string prints `examined=0` honestly; the return code does not, and `reconcile_tasks_json`
(`:1005-1016`) reads only the return code. This is precisely the sentence the header forbids:
`examined=0` is spelled like "nobody". Wrong direction, on the one leg the header itself calls
*"the only leg of the fix that can hurt if it is wrong"*.

**F3b — fail-CLOSED into inertness.** CASE 2. The cwd discriminator separates a session
**elsewhere on the filesystem** — that is the case T288 measured (pid 1207 at `/Users/buv`)
and it is the **only** case it measured. It does not separate an idle interactive `claude`
sitting in the project root from a fire that is working, because they are byte-identical to
this probe. `CLAUDE.md` documents `/softhouse` as an interactive entry point, so a session
with cwd = the repo root is normal usage, not an exotic one — and CASE 0 shows the fire's own
driver has exactly that cwd. For as long as such a terminal is open, the reconciler refuses
every fire. T288 replaced a warning nobody reads with a repair one open terminal disables.

**F3c — latent, and I mark it as such.** The whole design rests on T288's measurement that
*"there is NO process per worker … a subagent is in-process"*. That is a property of the
current harness, not a contract, and nothing in the repo pins it. If subagents ever move
out of process, every worker worktree — which lives at `$REPO/.claude/worktrees/…`, i.e.
**inside** `$REPO` — matches the in-repo test, and the reconciler goes permanently inert with
no signal. [UNVERIFIED whether the harness will change; VERIFIED that no assertion would catch it.]

**Remedy.** (i) Count anything the name filter rejects but that the caller cannot rule out —
or, better, decide candidacy on **cwd first** and treat any live process whose cwd is in the
repo and whose identity is not established as `unknown` → `return 2`. (ii) Give the fire a way
to identify **its own** sessions (the wrapper knows its driver's pid) so an in-repo session
that is not this fire's can be distinguished from one that is, instead of collapsing both to
REFUSE. (iii) Pin the in-process-subagent assumption somewhere that fails loudly.

---

## F4 — REJECT (P-45). `ready-tasks.py` tells every driver that a guard will fire, and it is the guard that did not fire

**Where** `.softhouse/bin/ready-tasks.py`, `main()`, added by T288:

```python
if live:
    print("  ^ If no fire is running right now, every line above is a DEAD dispatch")
    print("    and this section is lying to you. The wrapper repairs it on the way")
    print("    out: fire-program.sh runs `ready-tasks.py --reconcile` at fire exit,")
    print("    which rewrites these to needs_retry with the evidence in a note.")
```

This is printed **unconditionally**, in the tool a driver runs at STEP 0 to decide what to
dispatch. The claim is false on at least three paths:

1. **Any signal.** `on_signal()` (`:422-427`) is `stop_driver; release_lock; exit $rc`.
   `run_exit_guard` — which contains the reconcile at `:1032` **and the worktree sweep** — is
   called only from the chain-loop body at `:1116`. [VERIFIED: source, and by the tail of
   `~/Library/Logs/gerege-nbfi/fire-20260823-080004.log`, which ends
   `12:06:13 SIGTERM received … / 12:06:18 driver stopped … / 12:06:24 lock released` — no
   sweep line, no reconcile line, nothing after.] Already filed as **T309**; verified here in
   passing, not re-derived.
2. **Every REFUSE verdict** of `foreign_live_session_in_repo` — F3b, and the `rc=2` leg.
3. **Every REFUSE verdict** of `caller_is_lock_holder`.

**P-45** — *"a guard that only works when someone remembers to run it enforces nothing"*
(`patterns.md:1472`) — is quoted by T288's own handoff as the rule it exists to satisfy. This
line is its next generation: a guard that is **asserted** to run, in prose, to the exact reader
T288 identified as the only one that matters. T288's handoff also quotes **P-89** —
*"THREE ARTEFACTS SHIPPED WIRED TO NOTHING IN ONE FIRE … THE FIX IS A FILED TASK, NOT A
SENTENCE"* (`patterns.md:2904`), restated at `patterns.md:3008` as *"prose does not fire on the
next fire"* — and then adds prose that promises a fire.

**Remedy.** Make the sentence conditional on evidence, or delete it. The honest form names
what it cannot promise: *"the wrapper reconciles this at fire exit **on a normal exit only**,
and only when no live session is detected in this repo; a fire killed by a signal leaves these
lines standing."*

---

## Answering the brief's four questions directly

1. **Does `foreign_live_session_in_repo()` decide correctly, and which way does it fail?**
   Both ways, from one line. F3a is fail-OPEN (`examined=0` → authorise); F3b is fail-CLOSED
   into inertness. When `lsof` is missing or `/bin/ps` gives a one-line table it returns 2 —
   that leg is correct and correctly directioned, and I verified it is reachable (`:686-689`).
2. **Did the rescue sweep find WIP in the killed workers' worktrees?**
   **The sweep never ran.** It lives inside `run_exit_guard` alongside the reconciler, so the
   SIGTERM at 12:06:13 bypassed both. The `080004` log ends four lines later with no sweep
   output at all, and no `softhouse/rescued-agent-*-20260823-080004` branch exists (the six
   `…-20260822-140002` branches from the previous incident do). So the answer is neither
   "nothing to rescue" nor "the sweep looked and missed" — **it did not look.** That widens
   T309: the bypass costs *deliverables*, not only *status*, which is the more expensive half.
   *(I could not verify whether those four worktrees actually held WIP — worktree isolation
   blocks me from running `git -C` against them. [UNVERIFIED])*
3. **Is `caller_is_lock_holder()`'s refusal honest about what it cannot distinguish?**
   Mostly, with two gaps. (a) It opens with `if not os.path.exists(lock): return True,
   "no .softhouse/LOCK on disk -- nobody holds this repo"` — a **fail-OPEN**; absence of a lock
   file is not absence of a fire. Latent today (the wrapper's `release_lock` runs after
   `run_exit_guard`), but it is a direct hazard for T309: **if T309 places the reconcile after
   `release_lock` in `on_signal`, this gate goes vacuous.** T309 must reconcile BEFORE
   `release_lock`. (b) The claude-ancestor refusal says *"A driver or worker must not reconcile
   its own siblings"*, asserting a relationship it did not establish — it checked only that
   some ancestor is named `claude`, not that it has anything to do with this repo or this fire.
   Separately, `reconcile()` hard-codes *"the driver was already gone"* into every note; that
   function never checks driver liveness, so the sentence is an assertion about its caller.
4. **Is the repair's own output better heard than the WARN it replaced?**
   For the two **repairs**, yes, and this is T288's real contribution: the `tasks.json`
   demotions and the `RESUME.md` banner land in the two files the next fire actually opens,
   and both are self-clearing. For the two **refusals**, no — they go to `RECON_VERDICT` and
   the fire log, and `RECON_VERDICT` reaches `RESUME.md` **only if the banner is stamped**,
   which requires `RESUME.md` to be stale. A driver that rewrote `RESUME.md` but left tasks
   `in_progress` and then hit a REFUSE produces: a lying `tasks.json`, no banner, and the
   verdict in a log file — byte-for-byte the audibility of the WARN T288 replaced.

## What I checked and found CLEAN, so silence is distinguishable from not looking

- **Frozen adapter contract / DEC-n**: untouched. T288's 14 changed files contain no `.go`
  file, nothing under `nexus/`, and no DEC or contract file. [VERIFIED: `git show 37425ee --stat`]
- **Money non-negotiables**: not engaged. Zero occurrences of `float`/`double`/`Decimal` in
  either diff; no monetary path, schema column, API field or fixture is touched.
- **The zsh `local`-in-loop stdout leak** that T288 found and fixed inside its own new
  function does **not** recur in the worktree sweep loop it also edited. Measured on
  zsh 5.9 (arm64-apple-darwin25.0): bare `local P` inside a loop prints `P=<old value>`;
  `local P="v"` and `local -a A` / `local -a A=(...)` are silent. The sweep uses only the
  silent forms.
- **The `RESUME.md` banner strip.** `${RESUME_BODY#*$STALE_BANNER_CLOSE}` leaves the marker
  unquoted in a zsh pattern context, and the marker contains `<`, `!`, `>`. Driven: it strips
  correctly and banners do not stack. One residual nit, low: `RESUME_STALE` is set when the
  close marker appears **anywhere**, but the strip only fires when the open marker is at
  offset 0 — so a banner that is no longer first would stack rather than replace. Cosmetic.
- **The `t.get("branch") or ""` fix** T288 claims it made "in passing" is real and correct:
  `t.get("branch", <default>)` returns `None` for an explicit `"branch": null` because the
  default applies only to an absent key, and `None` was formatted as the string `"None"`.
  `or ""` collapses absent / null / empty to one spelling. [VERIFIED: diff and behaviour]
- **T288's citations.** `P-45` at `patterns.md:1472`, `P-89` at `:2904`, the restatement at
  `:3008`, and the skill quotation — softhouse-program `SKILL.md:234` *"NEVER exit with live
  workers — they die with you"*, item 4 *"A task whose worker you killed is not `in_progress`"*
  — all check out verbatim, including T288's correction that there is no STEP 5.4. Under
  **P-86** — *"AN ID IS A CARDINAL. Never restate a pattern id without the rule text beside it"*
  (`patterns.md:2823,2843`) — T288 quotes rule text beside every id it cites. Compliant.
- **`reconcile()`'s serialisation guard**: it compares the round-tripped canonical form to the
  raw bytes and warns before reflowing. Non-vacuous, correct direction.
- **`GUARD_HEAD_BEFORE_REPAIR`**: the chain-loop regression T288 found in its own change is
  genuinely fixed — `:1127` reads the pre-repair sha, so the wrapper's own commit cannot be
  mistaken for driver progress. Fallback to `HEAD` when unset is the pre-T288 behaviour.

## Adjacent observations — NOT part of the verdict

- **No automated check exercises any of this.** `grep -n "t288\|T288\|ready-tasks\|fire-program\|reconcile" .softhouse/conformance.sh` returns **nothing**, and T288's handoff declares
  `conformance.sh` "Not touched, by scope declaration". Its drive harness under
  `.softhouse/reviews/t288-drive/` runs only when someone remembers to run it — the literal
  text of P-45. `conformance.sh:910-912` states the standard the repo holds itself to:
  *"A wired guard that has been quietly neutered is worse than an unwired one, because it is
  believed (P-22). So the selftest … runs on every conformance run, not on the day someone
  remembers."* Three of the four defects above were found by running the code once; a wired
  selftest would have caught F2 and F3a. **This should be a filed task, not a sentence (P-89).**
  I have not filed it — task filing is the driver's, and `tasks.json` belongs to the live fire.
- **`fire-program.sh` is READ-ONLY to me this batch** (T309 owns the write). Nothing in this
  review modifies it. F2 and F3 are reported for the author of the next change to that file.
- **The chain loop's terminal-status list** (`:1140-1142`) treats `done, parked, rejected,
  superseded, done_partial, approved` as terminal. `tasks.json` today holds **16** tasks with
  status `merged` and 3 with `needs_retry`, neither of which is in that list, so the
  "no runnable work left" test can never fire while they exist. Pre-existing, not T288's, and
  bounded by `CHAIN_MAX=8`. Noted only so it is on the record.

## Evidence in this review

| path | what it is |
|---|---|
| `.softhouse/reviews/T302/drive-branch-wip.sh` | F1 — scratch repo, merged / pruned / unmerged / no-branch |
| `.softhouse/reviews/T302/out/1-branch-wip-merged.txt` | F1 transcript |
| `.softhouse/reviews/T302/drive-phantom-rescue.sh` | F2 — stale `index.lock`, the sweep's three commands verbatim |
| `.softhouse/reviews/T302/out/2-phantom-rescue.txt` | F2 transcript |
| `.softhouse/reviews/T302/drive-probe.sh` | F3 — the probe's own bytes, real live pid, 4 cases |
| `.softhouse/reviews/T302/out/3-liveness-probe.txt` | F3 transcript |
| `.softhouse/reviews/T302/NOTES-in-progress.md` | running notes, including the negative results |

Every drive writes to `/tmp` and reads the live repo only. None of them touches `tasks.json`,
`RESUME.md`, `LOCK`, `conformance.sh` or `fire-program.sh`.
