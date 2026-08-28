# T347 — INDEPENDENT REVIEW of T336 (`softhouse/T336-post-checkout-decision`, head `f86c2e4a`)

**Reviewer:** T347, fire `20260828-140005`, branch `softhouse/T347-review-t336`.
**Subject:** 18 files, +1627, no git hook installed, decision **(c)** — ship an after-the-fact
detector; reject (a), (b), (d).

## VERDICT — **ACCEPT WITH CONDITIONS**

T336's headline is a **measurement, not an absent log line**, and I reproduced it in this
fire through the real route on a spawn I did not stage. Its two deliverables are correct and
its self-reporting is unusually honest — it kept two of its own defective attempts in the
evidence rather than deleting them. Nothing in the code it shipped is wrong.

The conditions are about **what the branch does not say**: a residue class it created and did
not look for, a blind-spot cause that is incomplete in a way that changes the follow-up task,
and one word ("exhausts") that is not earned.

---

## 1. THE CENTRAL NEGATIVE — RE-DERIVED, NOT ACCEPTED

The brief is right that *"the harness runs no git hooks on the spawn route"* is exactly the
shape of claim that is wrong when the instrument was broken. So the recorded log lines were
not accepted; the control was re-run.

### 1.1 What I measured, in this fire

A logging `post-checkout` (three independent write targets, always `exit 0`) was live in
`/Users/buv/gerege-nbfi/.git/hooks/` for the whole window. Note it was **already there when I
started** — see §4, it is not mine.

| instant | event | post-checkout fired? |
|---|---|---|
| 14:07:29 | **a real `git worktree add`** by a live worker into `/private/tmp/t340-t258` | **YES** — `old=0000…0`, `isbranch=1` |
| 14:07:41 | worker `git checkout -b` in `agent-af8cbcb1cfe18931b` | **YES** |
| **14:07:51** | **harness `Agent` spawn — MY OWN worktree `agent-a75f8a5c86c8c2b7e`** | **NO** — nothing, in any of the three targets |
| 14:08:13 | my own `git checkout -b softhouse/T347-review-t336`, same worktree | **YES** — marker born 14:08:13 |
| 14:09:46 | worker `git checkout -b` in `agent-a81af6377829e0888` | **YES** |
| **14:10:35** | **harness `Agent` spawn I commissioned (`isolation: worktree`), read-only probe** | **NO** — probe reported the marker ABSENT in its own root at t0 |

The single most useful row is my own worktree, because it is a **self-contained control**: the
same directory, the same hook file, twenty-two seconds apart. The spawn wrote nothing; my own
`git checkout -b` wrote all three targets.

The 14:07:29 row is the control **T336 did not have**. T336's only genuine real-route
post-checkout positive is one `git checkout -b` at 12:03:18 (the 12:04:08 line in its log is a
hand-invocation with literal argv `0000 1111 1`, not a git event). Mine is a real
`git worktree add` — the *same command shape* as the spawn — firing in the *same shared
`.git/hooks`* twenty-two seconds before a spawn that fired nothing. That closes the gap.

Evidence: `out/live-postcheckout-commondir.log`, `out/probe-post-checkout-AS-FOUND.sh`.

### 1.2 Scratch derivation of the git behaviour itself (zero blast radius)

`probe/drive-t347-scratch.sh` → `out/scratch-git-behaviour.txt`, git 2.50.1 (Apple Git-155):

* **A.** `git worktree add -b` **does** fire `post-checkout` (`old=<null-sha>`, `isbranch=1`) and
  leaves `logs/HEAD` = *two* lines (null→sha with **no message**, then `reset: moving to HEAD`)
  plus a `branch: Created from …` branch reflog.
* **D.** `git worktree add -b` **does** fire `reference-transaction` with
  `0000… <sha> refs/heads/<branch>` in `prepared`.
* **E.** T280's **F-C reproduces**: a `post-checkout` that exits 1 → `rc=1`, and the branch, the
  populated tree and the admin dir are all created, `git status` works, and **a commit inside
  the "refused" worktree succeeds**. `probe/drive-t347-scratch.sh` case E.

So both hooks demonstrably run for the real commands on this git and this platform.

### 1.3 The one alternative explanation, closed

My probe agent, reasoning past its data, proposed that the harness might use
`git worktree add --no-checkout` and populate afterwards — in which case nothing is
"suppressed" and `post-checkout` is simply not applicable. **Refuted by scratch cases B and C:**
`--no-checkout` leaves a **one-line** `logs/HEAD` and an **empty** tree, and a following
`reset --hard` populates the tree but appends its line to a creation entry that is still alone
at the top. The harness worktree has case **A**'s two-line signature *and* a populated tree
*and* the branch reflog — the plain-`worktree add` signature, exactly as T336's
`out/reflog-signature.txt` says. **T336's shape-identity claim holds.** I record the refuted
hypothesis so it is not rediscovered.

What remains is what T336 flagged `[UNVERIFIED]`: *why* the hooks do not run (command-line
`-c core.hooksPath=…`, a git library, something else). `core.hooksPath` is unset at every
config origin and no `GIT_DIR`/`GIT_WORK_TREE` is exported into a worker
[re-verified by the probe agent]. Operationally it does not matter, and T336 says so.

### 1.4 "Three independent write targets" — the brief's suspicion does not land

They are genuinely independent. `G` in `probe/post-checkout-PROBE` is a **hard-coded absolute
path** (`/Users/buv/gerege-nbfi/.git`), not `$GIT_DIR`; `/tmp` is a second path; `$(pwd)` — the
new worktree — is a third; a stderr marker is a fourth channel. No shared `$GIT_DIR`
resolution, so the brief's "three targets that all depend on the same resolution are one
target" does not apply.

The residual limitation is different and is the reason the control matters: all three writes
live in **one script**, so they discriminate *"ran, and a path was denied"* from *"ran, and
wrote"* — not *"ran at all"*. Only the bracketing control does that, and I re-ran it.

---

## 2. FINDINGS

### F-T347-1 — CONFIRMED, no defect. The headline reproduces through the real route.
**Severity: none (adjudication in T336's favour).** §1 above. The claim *"the agent harness
creates worker worktrees without running git hooks at all"* is a measurement with a
command-shape-matched positive control, and it is now measured twice, six hours apart, by two
different tasks.

### F-T347-2 — CONFIRMED. F-C reproduces at its load-bearing core.
**Severity: none.** `rc=1`, worktree fully created and usable, commit succeeds inside it
(`out/scratch-git-behaviour.txt` case E). T336's claim 1 stands. Its F-C work ran entirely in a
`/tmp` scratch repo (`/private/tmp/t336-fc.X140dL`) — **no stray `T999`/`FAKE` branch exists in
the live repo**; I checked.

### F-T347-3 — CONFIRMED. `reference-transaction` in `prepared` genuinely vetoes.
**Severity: none.** `probe/drive-t347-reftxn-veto.sh` → `out/reftxn-veto.txt`. RED arm: exit 1 in
`prepared` on a `worktree-agent-*` ref → `fatal: ref updates aborted by hook`, **rc 255, branch
ABSENT, directory ABSENT, admin dir ABSENT**. CONTROL arm, same hook exiting 0 → rc 0,
everything created. T336's one positive-capability claim is real, and its uselessness here
follows from F-T347-1.

### F-T347-4 — **MAJOR.** T336's probe wrote into another live worker's tree, and the file is now COMMITTED.
`.T336-POSTCHECKOUT-FIRED` is an **added file in commit `cfe1885a`** on
`softhouse/rescued-agent-a932bd0ee5b1bb219-20260828-080001` (`out/marker-leak-scan.txt`).

Mechanism: T336's probe wrote `: > "$(pwd)/.T336-POSTCHECKOUT-FIRED"` on every checkout;
worker `agent-a932bd0ee5b1bb219` (T270) ran `git checkout -b` at 12:03:18 and received one; the
08:00 fire's rescue sweep `git add -A`'d it onto that worker's rescue branch.

T336's handoff says *"the live repo's `.git/hooks/` is byte-identical to how I found it"* and
*"No existing file in the repo was modified"*. Both are true and both are **beside the point**:
the residue of that mutation was never in `.git/hooks`. It was in the working trees of four
other live workers, and from there it entered the object database. **T336 did not look for it
and did not report it.** The byte-identity claim conceals this rather than answering it.

### F-T347-5 — **MAJOR (live; program-level, not T336's authorship).** The same practice is running under my task id and has leaked six more times.
A `post-checkout` headed *"T347 REVIEW PROBE … Installed by the T347 reviewer"* was live in
`.git/hooks` from **12:22:53** — **installed by someone other than me**; T347 did not begin
executing until 14:07:51. It dropped `.t347-postcheckout-marker` into every worktree that ran a
checkout, and the 12:24 rescue sweep committed it onto **seven** branches:

```
softhouse/rescued-agent-a2b34ba7fee3c2de6-20260828-080001
softhouse/rescued-agent-a414c482df5740790-20260828-080001
softhouse/rescued-agent-a4b1e3daa9362e909-20260828-080001
softhouse/rescued-agent-a70d9f6137d4ad21d-20260828-080001
softhouse/rescued-agent-a932bd0ee5b1bb219-20260828-080001   (+ .T336-POSTCHECKOUT-FIRED)
softhouse/rescued-agent-afc904cf109cb64cf-20260828-080001
softhouse/rescued-t339-base-20260828-080001
```

It also dropped one, untracked, into every batch-1 worktree of **this** fire — T339, T340,
T346, T323 and mine. Those will land on those review branches if any of them runs `git add -A`.

**What I did.** The probe is the instrument the brief demanded, so I used it, then preserved its
log as committed evidence (`out/live-postcheckout-commondir.log`), **removed it**, removed
`.git/t347-postcheckout-commondir.log` and my own marker, and proved the hooks directory is
back to a single live hook: `out/hooks-inventory-BEFORE-cleanup.txt` vs
`out/hooks-inventory-AFTER-cleanup.txt`. I did **not** touch other workers' trees.

**The rule neither task states, and which is the real lesson of both leaks:**
> *An observation hook installed in the shared `.git/hooks` writes into every other live
> worker's working tree. Write to `$GIT_COMMON_DIR` and `/tmp` only — never `$(pwd)`.*

### F-T347-6 — **MINOR**, but it changes T348. The blind spot is real; its stated CAUSE is incomplete.
T336 attributes the loss of spawn evidence to *"the exit protocol's own prune sweep"*, and FU-1
places the audit call before that sweep on exactly that reasoning.

**Measured this fire:** the worktree I spawned at **14:10:35** was gone from both
`.git/worktrees/` and `.claude/worktrees/` by **14:15** — mid-fire, no fire exit, no prune
sweep. The harness itself auto-cleans a worktree whose agent left it unchanged. The audit run
at 14:19 saw **five** subjects where six had been spawned.

So there is a **second destroyer, operating during the fire, that no placement inside
`fire-program.sh` can outrun**. FU-1's placement is still necessary. It is not sufficient, and
FU-2 (batch close) does not fully cover it either: **a worker that violates push-before-spawn
and then produces nothing is invisible to this detector at every placement.**

This must be written into the script's own BLIND SPOTS section, because the deliverable's own
standard is `patterns.md:661` — *"a tripwire with a stated blind spot is honest, a tripwire with
an unstated one is the vacuous guard of P-22"*.

### F-T347-7 — **MINOR.** *"That exhausts git"* is not earned; one interception point was never enumerated.
T336, and T349's brief quoting it, treat git hooks plus `PreToolUse` as the whole surface. A
**`git` PATH shim exported by `fire-program.sh` before it launches `claude`** is a third
candidate, neither tested nor rejected. Availability is genuinely unknown: T336's probe recorded
the *worker's* git as `/Applications/Xcode.app/…/git` (PATH-resolved), but the *harness's own*
git invocation was never observed — which is precisely the `[UNVERIFIED]` T336 flagged.

I am **not** recommending it: a shim on `git` has a catastrophic blast radius. I am saying
T349 should carry it as a candidate to **measure and reject on the record**, rather than
inherit as already closed.

### F-T347-8 — **Adjudication: (d) was NOT rejected too narrowly, and nothing in T349 can refute the rejection.**
The brief asked me to check whether T336's rejection of (d) rests on a claim T349 would
overturn. It does not: T336 pre-conditioned it — *"If it works, it obsoletes FU-1/FU-2 as the
primary control and they become the backstop."* T349's brief is correctly scoped to
evaluation-only and its five questions are the right ones (recovery, offline failure mode,
escape-hatch decay, call-path, cost).

On the substance I agree with **(c) over (d)**, for a reason T336 undersold and I verified by
running it from committed artefacts only (`out/redrive-audit-red-green.txt`):

| drive | expected | got |
|---|---|---|
| RED — commit → spawn → push +2 s | exit 1 | **exit 1**, naming the branch origin did not carry |
| GREEN — commit → push → spawn | exit 0 | **exit 0** |
| RED 2 — `LOCK` never published | exit 1 | **exit 1**, *"origin said NO FIRE WAS RUNNING"* |
| CONTROL — zero subjects | exit 2, never 0 | **exit 2** |
| CONTROL — all subjects unmapped | exit 2, never 0 | **exit 2**, *"NOTHING WAS ACTUALLY JUDGED … not a pass (P-22)"* |
| live repo, this fire, 5 spawns | judges them | **5 clean, exit 0** (`out/audit-live-this-fire.txt`) |

Every clean verdict prints *"THIS IS NOT ENFORCEMENT. Nothing prevented a violation; this run
only failed to find one, over subjects that still exist (P-45)."* A detector that refuses to
print PASS when it judged nothing, and that captions its own greens, is not the thing (d)
fears. **(d) was rejected on adequate grounds.**

### F-T347-9 — **MAJOR (program, not authorship).** The deliverable is invoked by nothing, in a task about guards invoked by nothing.
`grep -c` for `push-before-spawn|post-checkout|t336` in `.softhouse/conformance.sh`: **0**.
Nothing in `fire-program.sh` calls it. T348 is filed and `pending`, serialised behind T342 and
T343, and **depends on T347** — this review.

Until T348 lands, `.softhouse/hooks/push-before-spawn-audit.py` is another instance of **P-45** —
*"a guard that only works when someone remembers to run it enforces nothing"*, from the pattern
titled *"A test-only guard is not a guard"* [`patterns.md:1503-1506`] — shipped inside an
artefact written about P-45.

**This is not a rejection of T336.** The file lock was real (`fire-program.sh` was held by
T342), T336 was forbidden to apply the patch, and it said all of this in its own Blockers and in
the script's own docstring. The finding is a **standing condition on how the branch may be
described**: nothing may cite it as having given push-before-spawn mechanical backing.

### F-T347-10 — **MINOR.** Wrapping the live `reference-transaction` during a live fire was an unweighed risk.
For roughly eight minutes the shared repo's only live ref guard was a T336-authored wrapper —
installed non-atomically, running `IN=$(cat)` plus two appends plus a delegating pipe on **every
ref transaction of five concurrent workers**. T336 itself later proved that a
`reference-transaction` failure aborts `git worktree add` with rc 255 and nothing created
(F-T347-3): the failure mode of a bug in that wrapper was **bricking the fire** — the exact risk
the driver had gated the task on. The handoff does not weigh it.

The outcome was fine and the restore is **independently verifiable**, which I did rather than
take on trust: the live hook is **byte-identical** to what `branch_sweep.py`'s `HOOK_TEMPLATE`
generates — sha256 `e36a9becda1f8aa1d9feb01fa63270ca8dc2a2cbaf22a4c986afd92d006de270`, 549
bytes — and `branch_sweep.hook_status()` reports the T312 marker present and executable
(`out/hooks-inventory-AFTER-cleanup.txt`). That is a check against the **canonical generator**,
not against a private backup only T336 could see.

Exposed en route, **pre-existing and T312's, not T336's**: `hook_status()` authenticates the
guard by a **marker string in a comment**, so T336's wrapper reported as *"ref guard already
installed"* while being a different program. A forgeable attestation.

### F-T347-11 — **MINOR.** My own brief mis-cites a pattern id, and P-86 exists for exactly this.
The dispatch brief says *"P-80 — check the deliverable against its own rule."* `patterns.md`
**P-80** is *"A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the same
defect as the line number."* [`patterns.md:2775`] — no pattern in the file carries the gloss the
brief gives. The brief also glosses "P-83/P-84 — probe-line presence before value"; that is
**P-84** alone — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE
VALUE."* [`patterns.md:2813`]. **P-83** is *"two independent movements of one pinned number
reconcile by running, never by arithmetic"* [`patterns.md:2806`].

I followed the instructions as written in prose (F-T347-6 and F-T347-9 are the deliverable
checked against its own rule). Recorded under **P-86** — *"THE PATTERN IDS THEMSELVES ROTTED, IN
THE FILE THAT NAMES THE ROT"* [`patterns.md:2854`], whose rule is *"an ID IS A CARDINAL. Never
restate a pattern by number alone."*

### F-T347-12 — **NIT.** `float(a.since)` at `push-before-spawn-audit.py:224`.
A CLI epoch parse, not a monetary path, so no CLAUDE.md non-negotiable is touched — the audit
introduces no arithmetic of any kind on money, no schema column, no API field, no fixture.
Flagged only so a future float-literal census does not read it as one; `int()` removes the
question.

---

## 3. WHAT I DID NOT RE-DERIVE, AND WHERE I LOOKED

*"Not found" is a statement about the search, and this task's whole thesis is a "not found".*

**I did not re-derive `reference-transaction` non-invocation at the spawn instant.** Doing so
requires replacing the live `reference-transaction` — T312's case-shadow ref guard — with a
wrapper, and I measured in F-T347-3 that a misbehaving hook there aborts **every ref update in
the shared repo**. With four workers live I judged that risk unjustified for a claim that is
(a) corroborated — both hooks are discovered by the same `$GIT_COMMON_DIR/hooks` mechanism, and
`post-checkout` non-invocation is measured — and (b) not load-bearing, since T336's rejection of
(b) survives on grounds already established. T336 took that risk; I declined it and say so
rather than letting the reader assume both halves were re-measured.

**So the `reference-transaction` half of the headline rests on T336's committed log alone.**
Where I looked and what would have shown up: a `prepared`/`committed` pair carrying
`0000… <sha> refs/heads/worktree-agent-<id>` in `out/real-route-REFTXN-FIRED.log` across
11:57–12:03. Scratch case D proves that is the exact shape a real `git worktree add -b`
produces. There is none, while ordinary worker traffic is dense in the same window
(12:01:38, 12:03:16, 12:03:48, 12:04:28).

**Reproducibility of T336's evidence from committed artefacts, not `/tmp` residue** — the brief's
last attack, and it holds up. `/tmp/t336-hook-probe.log`, `/tmp/t336-reftxn-probe.log`,
`.git/T336-POSTCHECKOUT-FIRED.log` and `.git/T336-REFTXN-FIRED.log` are all **gone**. But the
drivers and the outputs are committed, and I re-drove the audit red/green **entirely from
`git show` of the branch** — no working copy, no `/tmp` residue (`out/redrive-audit-red-green.txt`;
the audit as committed is sha256 `12182224…`). The real-route logs cannot be re-derived, only
**re-measured**, which is what §1 is.

---

## 4. PROVENANCE OF THE T347 PROBE HOOK (the brief asked me to explain it)

`.t347-postcheckout-marker` carries my task id and leaked onto
`softhouse/rescued-t339-base-20260828-080001` at **12:24**, nearly two hours **before T347
began executing at 14:07:51**. The explanation is that the hook was installed at **12:22:53**
by the driver, in my name and ahead of my dispatch, so that the control would be armed and
running across this fire's spawns. That is why it was already logging when I arrived, and why
the 14:07:29 / 14:07:41 / 14:09:46 control lines exist at all.

It is a good instrument — it is the reason F-T347-1 has a command-shape-matched control — and
it is also F-T347-5: it contaminated seven committed branches and five live worktrees while
doing its job. Both things are true. It is now removed and the hooks directory is proven clean.

---

## 5. CONDITIONS OF ACCEPTANCE

1. **T348** must carry F-T347-6: a second, mid-fire destroyer of spawn evidence exists; *"before
   the prune sweep"* is necessary but **not sufficient**; a violating worker that produces
   nothing is invisible at every placement. The BLIND SPOTS section of
   `push-before-spawn-audit.py` must say so before the call site is wired.
2. **Driver, before merging this fire's batch 1:** check T339 / T340 / T346 / T323 branches for
   `.t347-postcheckout-marker`, and decide the disposition of the seven rescue branches listed
   in F-T347-5 that already carry it (and `.T336-POSTCHECKOUT-FIRED`).
3. **`.softhouse/hooks/README.md`** should gain the rule in F-T347-5 — an observation hook in the
   shared `.git/hooks` writes into every other live worker's tree; use `$GIT_COMMON_DIR` and
   `/tmp`, never `$(pwd)`. Neither T336 nor the T347 probe states it, and both leaked.
4. **T349** should carry the PATH-shim candidate (F-T347-7) to reject on the record, and the word
   *"exhausts"* should not be inherited unexamined.
5. **T343** must land T336's FU-4 — the false capability claims in `SKILL.md` STEP 0 (*"the hook
   that would enforce it at the instant it must hold"*) and in the header of
   `.softhouse/capture/t279-lock-partition/post-checkout` (*"Enforced at the instant it must
   hold"*, *"That is the difference between a convention and a precondition"*). **Verified as
   already assigned** — T343's description carries it verbatim and its `files_hint` includes
   T279's hook. Flagged only because every reader of STEP 0 until then reads a false statement.
6. **Nothing may describe this branch as having given push-before-spawn mechanical backing**
   until T348 lands (F-T347-9). T336's own text is already scrupulous about this; the condition
   is on everyone downstream.

None of the six is a defect in the code T336 shipped.

## 6. ENDORSEMENT OF T336's FU-5, sharpened

T336 proposes: *"A hook is not a guard until you have seen it fire on the route the system
actually uses."* **Endorsed** — three layers of this program believed a `post-checkout` gate was
available, and the route nobody drove was the only route that mattered. It is distinct from
P-45 (un-invoked) and P-22 (cannot fail): this guard was **correct, and mounted on a road no
traffic uses**.

Second candidate, from F-T347-4 and F-T347-5, and it earned itself twice in six hours:
*"A probe installed in shared state is a mutation of shared state. Its residue is not where you
installed it — it is wherever the probe writes, and on this pipeline that is other workers'
working trees, one `git add -A` away from the object database."*

## 7. VERIFICATION

* `bash .softhouse/conformance.sh` → **exit 0**; reference-oracle probe line **PRESENT** and
  reads `up` (`https://localhost:8443/fineract-provider/actuator/health`) — P-84 satisfied, this
  is a real green and not an unread absence. Full log: `out/conformance.txt`.
* No money path, schema column, API field or fixture is touched by T336 or by this review. No
  arithmetic on money is introduced. PostgreSQL only; nothing here touches a database.
* `.git/hooks` left with exactly one live hook, byte-identical to T312's canonical generator:
  `out/hooks-inventory-AFTER-cleanup.txt`.

## 8. ARTEFACT INDEX

| path | what |
|---|---|
| `probe/drive-t347-scratch.sh` | cases A–E: worktree-add vs `--no-checkout` vs reset, reftxn, F-C — throwaway repo |
| `probe/drive-t347-reftxn-veto.sh` | the reftxn veto RED arm and its permitting CONTROL |
| `out/scratch-git-behaviour.txt` | output of the above |
| `out/reftxn-veto.txt` | rc 255 / nothing created, vs the control |
| `out/live-postcheckout-commondir.log` | the live control log, preserved before the probe was removed |
| `out/probe-post-checkout-AS-FOUND.sh` | the probe hook exactly as I found it in `.git/hooks` |
| `out/redrive-audit-red-green.txt` | T336's audit re-driven from `git show` of the branch alone |
| `out/audit-live-this-fire.txt` | the audit against the live repo, this fire's 5 spawns |
| `out/marker-leak-scan.txt` | the seven branches carrying probe-marker residue |
| `out/hooks-inventory-BEFORE-cleanup.txt` / `-AFTER-` | byte-identity proof of the hooks directory |
| `out/conformance.txt` | `bash .softhouse/conformance.sh`, exit 0, probe up |
