# T350 — FU-T330-1: the reconciler's refusal is now bought with CONTENT, not with a NAME

**Branch** `softhouse/T350-reconcile-content` · **file changed** `.softhouse/bin/ready-tasks.py`
(sole writer this wave) · **evidence** `.softhouse/capture/t350-reconcile-content/`

---

## 1. The defect, restated from first-hand evidence in this repo

T330 gave `--reconcile` two ways to REFUSE a demotion. One of them, `relocated`, fired on
a **branch NAME**.

The refusal that filed this task is still readable, verbatim, in the `tasks.json` blob
committed at `ac72956b` (`softhouse: local fire lock (20260828-140005)`):

> `[T330-REFUSED-DEMOTION]` … REFUSE to demote — a live ref carrying this task's id exists
> under another name … **MEASURED: the branch is gone under its RECORDED spelling, but 1
> live ref(s) carry id T339 — `softhouse/rescued-t339-base-20260828-080001`.**

That ref's **entire** contribution, measured here:

```
$ git log --oneline main..softhouse/rescued-t339-base-20260828-080001
7e8825b9 RESCUED: WIP from a worker that never signalled done (fire 20260828-080001)
$ git diff --stat main...softhouse/rescued-t339-base-20260828-080001
 .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt | 260 ++++--------------
 .t347-postcheckout-marker                     |   1 +
 2 files changed, 42 insertions(+), 219 deletions(-)
```

A 219-line **deletion** from another task's transcript, and a marker belonging to **T347**.
Nothing whatsoever of T339. The ref is named for the **worktree directory**
`/private/tmp/t339-base` — and the thing that named it is **the wrapper's own worktree
sweep**. So the reconciler was reading its own sibling's naming convention back as
independent corroboration: one assertion, restated in a second place, then counted twice.
That is P-80's shape ("a corrected cardinal rots in every place it was restated") applied
to an authority instead of a number, and P-91's ("the escape is not a better pattern; it is
inverting the burden").

**And the same defect runs the other way, which is why "drop the refusal" is the wrong fix.**
All four cases were re-derived here from the repo, not inherited from the driver's table:

| case | what the record/instrument said | what the repo says | old verdict | new verdict |
|---|---|---|---|---|
| **T339** | `in_progress`, refusal note above | rescue ref carries **zero** t339 content; T339 had produced no review | `relocated` → **REFUSE** | `name-only-refs` → **DEMOTE** |
| **T431** | `ready-tasks.py`: "WIP: MERGED … The work LANDED. Do NOT read this as an unstarted task" | branch stood at `280817a1f`, whose own subject is *"softhouse: iter4 wave 2 — five dispatched, records pushed BEFORE the first worktree add"* — the **driver's dispatch commit**. `C-T407-1` (MAJOR) was **unstarted** | `merged` → **REFUSE** | `stillborn` → **DEMOTE** |
| **T421** | `needs_review`, branch field set, branch deleted | 70 tracked paths on main name t421, incl. 33 under `.softhouse/capture/t421-t406-conditions/`; `T421:` commit subjects on main | offered in **READY with no evidence line at all** | flagged **`!! WORK BEARING id T421 IS ALREADY ON MAIN`** |
| **T428** | `needs_retry`, "worker killed mid-flight … a killed worker is dead, not paused" | `softhouse/T428-review-t421` @ `8a6706c6` **is an ancestor of main**; 36 tracked paths name t428, incl. 35 under `.softhouse/reviews/t428-review-t421/` | offered in **READY with no evidence line at all** | flagged **`!! WORK BEARING id T428 IS ALREADY ON MAIN`** |

**T421 and T428 were not wrong ANSWERS. The reconciler was never ASKED.** `branch_wip()`
runs only for tasks whose status is `in_progress` — in `reconcile()`'s loop and in `main()`'s
IN PROGRESS section. A `needs_retry` or `needs_review` task is printed in READY as an id, a
model, a target and a title, and nothing else, and the driver dispatches from that list.
Establishing that by grep was the difference between fixing one direction and fixing both.

---

## 2. The predicate I chose, and the argument for it

> **A ref, a branch name, or an ancestry relation may withhold a demotion only by carrying
> CONTENT that plausibly belongs to the task.**

Concretely, evidence is one of:

* **ON MAIN** — a commit subject prefixed `<id>:` or `Merge <id>:`; **or** a tracked path on
  `main` with a **component that BEGINS with the id** (this program's directory convention:
  `.softhouse/capture/<id>-<slug>/`, `.softhouse/reviews/<id>-<slug>/`,
  `.softhouse/handoff/<id>-<slug>.md`).
* **ON A REF** — the ref's **own** diff vs main (three-dot `main...ref`, i.e. merge-base…ref,
  so the answer does not drift as main advances) contains such a path; **or** a commit in
  `main..ref` has a subject naming the id.

Three sub-decisions worth defending:

**(a) Nothing special-cases `rescued-*`.** Excluding the wrapper's own prefix by name would
be the same mistake one level out: the next sweep invents a new prefix and the guard
silently stops covering it. The content test does not care what the ref is called. This is
P-91's rule — invert the burden, do not enumerate the shapes.

**(b) OWNING vs MENTIONING, and it was forced by a measurement, not by taste.** The first
GREEN run of the READY flag fired on **T268**, a live unfinished task, citing 24 tracked
paths — every one of them under `.softhouse/capture/t286-t268-retry/`, which is **T286's**
capture directory, named for the task it retries. A mention is not a claim. Requiring the
path component to *begin* with the id drops that false positive and keeps every true one
(`t428-review-t421` counts for T428, and only mentions T421 — T421's own evidence is its
own `t421-t406-conditions/` directory). Mentions are still **printed** under `MENTIONING`
so the reader can see what the rule declined to count.

**(c) The `stillborn` arm exists because `merge-base --is-ancestor` answers a different
question than the one being asked.** `git worktree add -b <branch>` branches from wherever
the driver stands, which is a commit it has just pushed to `main`. A worker killed before
its first commit leaves a branch that is zero ahead of main and an ancestor of main and
carries **nothing**. "Ancestor of main" is not "the work landed".

---

## 3. Which direction I fail in, and why — it is NOT one direction

Both directions have destroyed value in this program (T324 lost work to a demotion; T339,
T431/C-T407-1 lost a task to a refusal). Picking one global polarity is what produced two
incidents pointing opposite ways. So the polarity is chosen **per kind of evidence**:

| situation | direction | why |
|---|---|---|
| content is **on main** | **REFUSE to demote** | Irreversible loss lives here — T324's demotion put 14 files / 2,338 insertions up for redoing. `main` is durable and the signal is a tracked object, not an assertion. Unchanged from T330. |
| the only signal is a **name** | **DEMOTE** | A name is not evidence at all. The cost of the wrong refusal is a permanent `in_progress` lie — STEP 5.5 item 4: *"Leaving it in_progress tells the next fire that work is happening when nothing is"* — which the driver of fire `20260828-140005` had to override by hand. |
| a probe **did not run** | fall back to the polarity of **the strongest signal that DID run**, never to the flattering one | *Absent* branch + unrun probes → `indeterminate` → **demote** (T330's rule, kept verbatim: "an unrun probe must never buy a task a reprieve"). *Ancestor-of-main* branch + unrun probes → `merged-unverified` → **withhold**, because "reachable from main" is a positive git fact that DID run, merely ambiguous — and reading an ambiguous positive as "nothing was done" is exactly the T324 accident. |
| a name-matching ref exists but could not be probed | **DEMOTE**, ref named loudly | Same rule as above: a refusal manufactured by a check that never ran is the accident this file exists to prevent. |

**The residual risk, stated and not papered over.** A task whose work landed on main under a
path that names no component for it *and* under a commit subject that does not name it
would be read `stillborn` and demoted. **Calibrated, not argued:** of the **175** local
heads in this checkout that the pre-T350 code called `merged` (0 ahead of main **and**
ancestor of main), **173 keep `merged`** because content on main corroborates them, and
exactly **2 flip to `stillborn`** — `softhouse/T350-reconcile-content` and
`softhouse/T412-driver-selfgrading`, both sitting at `b102875c` (fire 20260829-080002's
iter5 dispatch commit), i.e. **both are live instances of the T431 defect, caught on the
real repo right now**. Zero of the 173 real merges flip.
[`out/30-budget-and-calibration.txt`, and every flip is listed there rather than counted — P-80.]

Second residual: the READY flag is a **flag, not a filter**. This resolver will not withhold
a task from the driver on the strength of a path name; it prints what is on main and lets
the driver adjudicate — the same refusal-to-assert-a-review the reconciler makes.

---

## 4. RED first, then GREEN — P-22

Module under test is loaded **by path**, so RED runs the exact bytes on `main`
(`sha256 3d7fef80…`) and GREEN runs the bytes in this tree. T213's rule: the fixture and
the fire run the same file, not a copy.

The fixture (`bin/10-build-fixture.sh`) is a `--shared` clone with **all 686 heads
mirrored**, whose `main` is rewound to the exact commit the reconciler was standing on.
That matters: on **today's** main all four tasks carry `<TID>:` commit subjects, so the
current code answers `merged` for all four and **every defect is invisible**. *(The first
cut of the fixture also got this wrong in the other direction — `git clone` creates one
local head and the rest arrive as `refs/remotes/origin/*`, which `branch_sweep.RefIndex`
does not read, so both must-block controls came back "no live ref carries the id". A fixture
that cannot show the guard blocking is not a fixture.)*

### 4a. `branch_wip` + `reconcile_action` — `out/10-RED-before.txt` → `out/20-GREEN-after.txt`

```
                                                        RED (main)                  GREEN (this tree)
A/T339  name-only rescue ref, work NOT on main          relocated      REFUSE  →  name-only-refs  DEMOTE
B/T431  branch head IS the driver's dispatch commit     merged         REFUSE  →  stillborn       DEMOTE
C/T421  branch pruned post-merge, 33 files ON MAIN      merged         REFUSE  →  merged          REFUSE
D/T428  branch DELETED, 35 files ON MAIN                merged         REFUSE  →  merged          REFUSE
E/T351  CONTROL: live ref carries REAL t351 content     relocated      REFUSE  →  relocated       REFUSE
F/T442  CONTROL: live ref carries REAL t442 content     relocated      REFUSE  →  relocated       REFUSE
```

**A and E are indistinguishable under RED** — both `relocated`, both refusing — which *is*
the defect: a name is a name. Under GREEN they separate on content:
`softhouse/T351-progress-accounting` carries a commit main does not plus
`.softhouse/capture/t351-progress-accounting/…`; the T339 rescue ref carries neither.
**E and F are the "should block" cases the brief required** and they still block — the
refusal was not silently dropped.

### 4b. End to end through `reconcile()`, which is what actually writes

`out/12-RED-reconcile-before.txt` → `out/22-GREEN-reconcile-after.txt`. `wrapper` authority
is reached honestly (no `LOCK` on the fixture + `--no-live-session-established-out-of-band`);
nothing is forced past a guard.

```
RED   T339 in_progress -> in_progress  *** REFUSED TO DEMOTE ***
      T351 in_progress -> in_progress  *** REFUSED TO DEMOTE ***
      T431 in_progress -> in_progress  *** REFUSED TO DEMOTE ***
GREEN T339 in_progress -> needs_retry
      T351 in_progress -> in_progress  *** REFUSED TO DEMOTE ***      (control holds)
      T431 in_progress -> needs_retry
```

### 4c. The other direction — the READY listing

`out/11-RED-readylist-before.txt` → `out/21-GREEN-readylist-after.txt`. Fixture main = today's
tip; T421 and T428 branches deleted; controls T351 (work on a **ref**, not main) and T339x
(genuinely nothing).

```
RED    READY (4)
         T339x  … CONTROL -- genuinely unstarted
         T351   … CONTROL -- work lives on a live ref, NOT on main
         T421   … T406's six conditions on T391          <-- 70 paths on main. Nothing printed.
         T428   … INDEPENDENT review of T421             <-- 36 paths on main. Nothing printed.
GREEN  READY (4)
         T339x  (silent — correct)
         T351   (silent — correct: its work is on a ref, and this flag is about main)
         T421   !! WORK BEARING id T421 IS ALREADY ON MAIN: commit ffb52921c … 'T421: stop the
                   handoff counting its own commits …'
         T428   !! WORK BEARING id T428 IS ALREADY ON MAIN: commit 8a6706c60 … 'T428: independent
                   review of T421 -- APPROVED WITH CONDITIONS, four LOW findings'
```

### 4d. On the live repo, unprompted

`out/50-ready-list-BEFORE-first-commit.txt` — `python3 .softhouse/bin/ready-tasks.py` on the
real `tasks.json`, before this branch had a commit:

* `T350` and `T412` (both `in_progress`, both at `b102875c`) → **`WIP: STILLBORN … RECONCILE
  WOULD: demote to needs_retry`**. The code on `main` prints *"WIP: MERGED … The work
  LANDED. Do NOT read this as an unstarted task."* for both. Two live instances of the T431
  defect, in the current file, caught by the change.
* `T286` (`needs_retry`) → flagged: 27 tracked paths on main begin with `t286`, its branch
  is 2 commits **ahead** of main and **not** an ancestor of it. Partially landed, genuinely
  needs a human. That is the T421/T428 shape, live, and it printed nothing before.
* `T268` → **not** flagged (see §2b). 1 flag over 45 READY + 8 BLOCKED tasks.

`out/51-ready-list-AFTER-commit.txt` is the same command after this branch's first commit:
`T350` correctly moves `STILLBORN → COMMITS` ("1 commit(s) ahead of main, head 2979fdaaf"),
which is the negative control for the `stillborn` arm — it fires on a branch that has
contributed nothing and stops the moment one commit lands.

**Bar on the committed tree** — `out/60-bar-on-committed-tree.txt`:
`bash .softhouse/conformance.sh` → **EXIT 0**; `grep -c 'probe = '` → **1** (tested for
presence before its value was read);
`conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`;
`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
compared`; all 16 wrong ledger implementations died through the harness.

---

## 5. A probe that could not fire, found while measuring

T330's landed-work **Source 2** keys the index on `os.path.basename(path)[:-3]`, so it
matches only a handoff named **exactly** `<id>.md`. Measured on main at `b102875c`: **542**
handoff paths are tracked, **229** are bare `T###.md`, and **313** use the convention this
program has used all month — `T164-analyze7-float-guard.md`, and this very file,
`T350-reconcile-content.md`. For all 313 the source contributed nothing, and the absence
looked exactly like the absence of a handoff. P-22. Source 3 (path components) subsumes it;
Source 2 is kept because it is cheap and exact, with the limitation now stated in its own
note text (`… (EXACT \`<id>.md\` only -- see source 3 for the rest)`).

---

## 6. Cost — `out/30-budget-and-calibration.txt`

The T330 design constraint is that this runs inside a SIGTERM handler racing launchd's ~20 s
grace, so per-task `git` is forbidden. It is preserved:

| | |
|---|---|
| `landed_index()` (subjects + exact handoffs) | **0.217 s**, once per process |
| `main_tree()` (all 9,730 tracked paths on main) — **new** | **0.083 s**, once per process |
| the handoff-only listing it widens, for comparison | 0.041 s |
| `landed_evidence()` per task (lowercase prefilter, then regex on survivors) | **0.0034 s** |
| ref content probe | 2 git calls ≈ 0.16 s, **only** for refs that already matched by name — zero in the ordinary case, one in the T339 incident; capped at `MAX_REFS_PROBED = 8`, and anything beyond the cap is `indeterminate`, which **demotes** |

Net: **+0.083 s once** on the signal path, and per-task cost stays a dict lookup plus a
~3 ms scan. The READY listing pays ~0.18 s for 53 non-terminal tasks, and it is not on the
signal path.

---

## 7. Wiring — P-45, established by grep, not asserted

`out/40-wiring-proof.txt`:

1. `.softhouse/launchd/mn.gerege.nbfi.softhouse-program.plist:14` → `/bin/zsh -lc
   .../.softhouse/bin/fire-program.sh`, on a `StartCalendarInterval` (08:00 …). Unattended.
2. `fire-program.sh:2732` → `/usr/bin/python3 "$SCRIPT_DIR/ready-tasks.py" "${args[@]}"`,
   inside `reconcile_tasks_json()` (defined `:2692`), which is called from **both** the
   normal tail (`:3242`) and the SIGNAL path (`:2151`).
3. `.claude/skills/softhouse-program/SKILL.md:183` — *"**Use `python3
   .softhouse/bin/ready-tasks.py`** rather than eyeballing `tasks.json`"* — the driver's
   STEP 1, which is what reaches `main()` and therefore the READY flag.
4. Inside the module: `landed_evidence()` is called at `:1305` (`_absent_verdict`), `:1458`
   (the ancestor-of-main leg) and `:1863` (`_landed_flag` in `main()`);
   `refs_carrying_content()` at `:1306`; and `reconcile()` turns a kind into an action at
   `:1634` through `reconcile_action()` **only** — it does not re-derive, so the fixture and
   the fire ask the same bytes (T213).

**Where I looked, for the "not found" statements:** `.softhouse/launchd/*.plist`,
`.softhouse/bin/fire-program.sh`, `.claude/skills/softhouse-program/SKILL.md`,
`.softhouse/bin/*.py`, `docs/`, `.softhouse/*.md`. No invoker outside those was searched for.

---

## 8. Scope

`.softhouse/bin/ready-tasks.py` and `.softhouse/capture/t350-reconcile-content/` only, plus
this handoff. `.softhouse/conformance.sh` (T445) and `.softhouse/bin/fire-program.sh` were
**not** touched — verify with `git diff --name-only main..HEAD`.

## 9. What I did NOT do — for whoever picks up T403

* `refs_naming()` is unchanged: it is still the cheap, pure-filesystem **name index**, and
  it is still the right first filter. Only what is done with its output changed.
* This does not promote anything to `done`/`merged`. A refusal still leaves `in_progress`
  with `[T330-REFUSED-DEMOTION]` for a human, and the READY flag is advisory. Asserting a
  review that did not happen, from a SIGTERM handler, remains out of bounds (P-22).
* The two `stillborn` branches the calibration found on the live repo — `T412`'s and (until
  this commit) mine — are a **records** repair the driver owns; this worker must not edit
  `tasks.json`, which the live fire owns.
* `T403` is the reconciler's other half and was held out of this wave only because T350 owns
  this file. `stillborn` is precisely the "killed worker vs worker that never existed"
  distinction T403 is filed for, so T403 should start from `_branch_wip_core`'s
  ancestor-of-main leg rather than from scratch.
