# T451 — T449's seven conditions on T350 (`.softhouse/bin/ready-tasks.py`)

**Branch** `softhouse/T451-t449-conditions`.
**Under change** `.softhouse/bin/ready-tasks.py` — the file every fire reads to decide
what to work on. Nothing else in the repo is touched except this task's own capture
directory. `conformance.sh` (T454) and `.softhouse/hooks/` (T453) are untouched.

**RED** is `git show main:.softhouse/bin/ready-tasks.py`, sha256 `e80196813ea210a0…`,
**byte-identical to the working-tree file at dispatch** — verified before the first edit
[`out/11-RED-baseline.txt` line 1–2, where RED and GREEN are the same sha]. Every module
in every instrument is loaded **by path**, never imported by name, so RED and GREEN are
the actual bytes and not a paraphrase.

---

## DISPOSITION, PER ITEM

| item | | disposition |
|---|---|---|
| **C-T449-1** | MAJOR | **FIXED.** The ancestor-of-main leg now consults the ref store. New kind `stillborn-carried` → **REFUSE**. Driven RED→GREEN, fixture case G. |
| **C-T449-2** | MAJOR | **RE-DERIVED AND THE PROPOSED PATCH REFUTED ON MEASURED DATA.** The anchor stays; the *comment* that argued against it was what was wrong, and the *note* that denied the mentioning path is now fixed to report it. Both directions driven. |
| **C-T449-3** | MINOR | **FIXED.** Cardinal re-counted at `b102875c` and corrected in the shipped comment: 337 `.md`, 229 bare, 29 `A2-n`, **79 inert** — not 313. |
| **C-T449-4** | LOW | **FIXED.** "every one" → 23 under `t286-t268-retry/` + 1 under `t291-review-t286/`, and the 24th *strengthens* the conclusion. |
| **C-T449-5** | LOW | **JUDGED AND FIXED.** A count cap on a safety refusal is not acceptable; the bound is now the resource it stood in for. Driven RED→GREEN, fixture case H. |
| **C-T449-6** | LOW | **FIXED.** Re-measured over 9 runs; the code now carries a range plus the command that retakes it, not a host-specific decimal. |
| **C-T449-7** | LOW | **ACKNOWLEDGED, NO BEHAVIOUR CHANGE, AND THE NOTE NOW SAYS SO.** Observed live again on all five of this wave's workers. |

Plus **one new finding of T451's own**, recorded and *not* fixed — see the residuals.

---

## C-T449-1 — the `stillborn` arm never consulted the ref store

### Re-derived, not inherited

`refs_carrying_content` had exactly one caller. So the moment `git rev-parse` resolved
the recorded branch, the ref store was out of the picture — and the shipped sweep
produces precisely that state: `fire-program.sh:3127` is
`git -C "$W" checkout -q -b "$WB"`, which moves a dead worker's uncommitted WIP onto a
rescue branch and **does not delete the task branch** that `git worktree add -b` left
parked at the driver's dispatch commit. "Branch parked" and "work carried on a ref" are
not alternatives; they are the same incident, and the arm saw only the half that says
nothing was done.

### RED, on my own fixture (built with `git init`, not cloned)

```
G/T900   task branch parked at dispatch commit AND a rescue ref carries the work
          RED    stillborn              DEMOTE
G2/T901  byte-identical evidence, recorded branch DELETED
          RED    relocated              REFUSE
```
[`out/11-RED-baseline.txt`] — identical content evidence, **opposite polarity**, decided
by nothing but whether the branch was deleted. The RED note says, verbatim:

> "the branch was cut from the driver's own dispatch commit and never moved. It reads as
> MERGED to `merge-base --is-ancestor` and **it is UNSTARTED**."

while `softhouse/rescued-t900-work-20260829` carries `.softhouse/capture/t900-work/out/wip.txt`.

### GREEN

```
G/T900   RED  stillborn         DEMOTE  ->  GREEN stillborn-carried REFUSE   <== CHANGED
G2/T901  RED  relocated         REFUSE  ->  GREEN relocated         REFUSE   (agrees)
```
[`out/12-GREEN-drive.txt`] The GREEN note names the ref, names the path, says
"**BUT IT IS NOT UNSTARTED, AND THIS ARM USED TO SAY IT WAS**", and tells the reader to
run `branch_sweep.py sweep` before touching the task.

### The three sub-cases and why each has the polarity it has

* **a ref CARRIES content → REFUSE**, as its own kind `stillborn-carried`. Not reused
  from `relocated`, because `relocated`'s text says *"the branch is gone under its
  RECORDED spelling"* and here the branch is standing. Swapping one false sentence for
  another is not a fix.
* **the ref probe DID NOT RUN → `indeterminate`, DEMOTE.** Deliberately the *less*
  generous choice, and the same action this arm already took, so nothing regresses. The
  absent leg already demotes on an unrun ref probe (T330: "an unrun probe must never buy
  a task a reprieve"), and this leg's evidence is **strictly weaker** than the absent
  leg's — a branch that provably never moved cannot have been merged-and-pruned. An arm
  may not be more generous than the arm above it on less evidence.
* **refs matched by NAME ONLY → `stillborn`, DEMOTE**, action unchanged, but the text now
  names them (fixture case N) instead of asserting a silence it never checked.

`reconcile_action`'s new arm is tested by **equality** and placed **first**, because the
tests below it are `startswith` — a kind that merely began with `stillborn` would have
fallen through to the bottom demote, i.e. a guard that compiles, reads fine and does
nothing. That trap is planted and caught as defect **D2** in `out/51-partition-red.txt`.

---

## C-T449-2 — the ref side argues generosity, then applies the strict anchor

The condition said: *re-derive it, drive it, and land it with both directions shown; do
not paste the reviewer's patch without reproducing why it is right.*

**I reproduced it, and it is not right. The patch is not landed.** Here is the evidence,
in the order it was taken.

### 1. The proposed patch, planted into the shipped bytes and driven

`bin/13-relaxed-probe.py` edits **one site**, verified unique before writing, and drives
both variants over the whole fixture [`out/13-relaxed-probe.txt`]:

```
case     what it is                                    SHIPPED(leading)   RELAXED(anywhere)
A/T339   the INCIDENT ref                              name-only demote   name-only demote
K/T945   work under another id's condition dir         name-only demote   relocated REFUSE  <==
K2/T946  case K with the task branch still parked      stillborn demote   stillborn-carried REFUSE  <==
R/T980   T981's COMMITTED review of T980               relocated REFUSE   relocated REFUSE
R2/T982  a SWEPT reviewer worktree, boilerplate subj.  name-only demote   relocated REFUSE  <==
S/T990   rescue ref touching only a SHARED file        stillborn demote   stillborn demote
E/T351   must-block control                            relocated REFUSE   relocated REFUSE
G/T900   case G                                        stillborn-carried REFUSE (both)
```

T449's verification reproduces exactly: K flips, T339 stays `name-only`. **And it costs
R2** — a reviewer's worktree swept by `fire-program.sh:3127`, whose subject is the
sweep's boilerplate naming nobody and whose only path is
`.softhouse/reviews/t983-review-t982/REVIEW.md`. Under `anywhere`, T982 is REFUSED
forever on the strength of somebody else's review of it. That is T339's defect restated
one level in: not "a NAME matched" but "a MENTION inside a path matched".

### 2. What it does to the LIVE ref store: nothing

Over all **705** live refs and all **84** `(id, other-ref)` pairs the reconciler could
ever be asked about, the relaxation adds **exactly 0** carriers. 15 pairs already carry
under the shipped code; the relaxation moves none of them
[`out/21-realrepo-evidence.txt`]. So it is a trade between two constructibles, neither
of which is live here.

*(My first census, `out/20-realrepo-census.txt`, measured only the PATH axis and found 7
pairs that flip. Driving the fixture then showed the SUBJECT half already makes those
refs carriers, so the 7 are not marginal. The corrected measurement is `out/21`. Recorded
because the first number was wrong and this program pays for numbers that get quietly
replaced.)*

### 3. The measurement that decides it

**The one REAL instance of case K's shape in this repo is already caught by the OWNING
anchor.** T428's swept ref carries

```
.softhouse/capture/t421-t406-conditions/out/T428-S01-counters.psql
```

— T428's work, filed under T421's directory, which is precisely case K — and it reads
**CARRIES** under `leading`, because a path *component* includes the **filename** and
this program names the file for its owner. T449's case K is invisible only because its
fixture filename is `work.txt`, which names nobody. **The premise that the OWNING anchor
cannot see work filed under another id's directory is refuted by the only real example of
it this repo has.**

Meanwhile the shape the relaxation would newly expose is the dominant one: 69 of the 84
pairs are name-only today, and the commonest cross-task object this program makes is one
task's review of another.

### 4. So what WAS broken, and is now fixed

The **comment**, and the **record**.

* The comment claimed a polarity the code never had. It now states the real asymmetry —
  which is between the two *signals*, not between the ref side and main. **SUBJECT** is
  generous (`anywhere`): a commit message is written by the worker doing the work, about
  the work. **PATH** is strict (`leading`): a component's leading id is this program's
  ownership convention and it holds on a ref for the same reason it holds on main.
* The note said *"no path in its diff vs main has a component naming T945"* over a diff
  containing `t944-t945-conditions/out/work.txt`. **That sentence was false**, and a false
  sentence in this file is the entire reason T350 exists. `ref_content_evidence` now
  returns `mentions`; `_mention_clause` names them, declines them, explains why, and tells
  the reader to look at those paths before re-dispatching. The verdict does not change;
  the claim does.

GREEN note for case K, verbatim excerpt [`out/12-GREEN-drive.txt`]:

> "…and NOT ONE of them OWNS any content belonging to it. … **DECLINED, AND NAMED SO
> NOBODY HAS TO TAKE THIS ON TRUST**: 1 path(s) in those ref(s) MENTION T945 inside a
> component that begins with ANOTHER id — `.softhouse/capture/t944-t945-conditions/out/work.txt`
> (on softhouse/rescued-t945-t944-conditions-20260829). … **READ THOSE PATHS BEFORE
> RE-DISPATCHING**: if the work really is this task's and merely landed under another
> id's directory, this demotion is wrong and the note is the only place that will tell you."

**If a reviewer disagrees with this call, the one-word patch is in
`bin/13-relaxed-probe.py` and the fixture that decides it is case R2.** The disagreement
is about which of two constructible shapes this program will produce first, and I have
argued from the ref store as it actually is.

---

## C-T449-3 — the "313 handoffs" cardinal

Re-counted at `b102875c`, the commit the shipped comment cites [`out/01-cardinals.txt`]:

| | shipped | measured |
|---|---|---|
| handoff paths tracked | 542 | **542** ✓ |
| of those, ending `.md` | (implied 542) | **337** |
| NOT ending `.md` — `continue`d past | — | **205** (114 `.txt`, 30 `.py`, 26 `.out`, 18 `.sh`, 11 `.zsh`, 2 `.go`, 1 each `.patch`/`.mod`/`.json`/`.gitkeep`) |
| bare `T###.md`, which key | 229 | **229** ✓ |
| `A2-<n>.md`, which also key | — | **29** |
| genuinely inert | **313** | **79** |

`313` is `542 − 229`. The finding (source 2 is near-inert) stands; the cardinal was wrong
by 4×, and the module's own runtime note prints the 337 that contradicts it *in the same
run*. The comment now carries the full breakdown and the one-line command that retakes
it. (At today's `main` the same arithmetic gives 318, which is how a rotting cardinal
behaves: it drifts with the tree while claiming to describe a pinned commit.)

## C-T449-4 — "every one under `t286-t268-retry/`"

24 total, **23** there, **1** under `.softhouse/reviews/t291-review-t286/out/rerun-t268-battery.txt`
[`out/01-cardinals.txt`]. The docstring now says so — and notes that the 24th
*strengthens* the argument, because it is owned by a **third** task, so the
mention-vs-ownership distinction is doing work across two owners rather than one.

## C-T449-5 — `MAX_REFS_PROBED = 8`

**Judgement, since the condition asked for one: a count cap on a safety refusal is not
acceptable.** T330's rule ("an unrun probe must never buy a task a reprieve") is about a
probe that *could not* run — git failed, the budget was spent. A count cap is different
in kind: it **manufactures** the ignorance and then applies the fail-closed rule to it,
and `8` is not a resource, it is a number somebody picked. On the one signal in this
module whose entire job is to *stop* a demotion, that converts REFUSE into proceed.

The bound is now the resource it was standing in for:

* `--deadline-secs`, already enforced per git call inside `_run()`, which returns
  `rc=None` the moment the budget is gone and lands each remaining ref in `unprobed`
  **with the reason named**; and
* `REF_PROBE_SECONDS = 6.0`, a ceiling on this probe's own wall clock, because
  `--deadline-secs` is **optional** (`fire-program.sh:2729` passes it only when
  `RECONCILE_DEADLINE_SECS` is set, so `DEADLINE` is often `None`).

`MAX_REFS_PROBED` survives only as a runaway guard at **512**, three orders of magnitude
above the measured maximum fan-out of **2** on this repo [`out/20-realrepo-census.txt`;
T449 measured 3 counting each id's own head, which I exclude because the real caller
does]. Truncation still degrades to `indeterminate`, which DEMOTES — what changed is that
truncation now requires time to have actually run out.

```
H/T950   9 name-matching refs, the only carrier LAST in sort order
          RED    indeterminate  DEMOTE  ->  GREEN relocated  REFUSE   <== CHANGED
```

## C-T449-6 — two spellings of one measurement

Re-measured over 9 runs, median/min/max [`out/30-cost.txt`]: source 3 ~0.09 s (10,088
paths today), source 2 ~0.04 s, **net ~0.05 s once per process**, `paths_naming` ~0.003 s
per task. The code no longer carries a decimal to be copied wrong; it carries a range and
`bin/30-cost.py`, which retakes it. The divergent figure in **T350's handoff** (0.083 s)
is on `main` and outside this task's scope — flagged as a residual below.

## C-T449-7 — a live worker before its first commit

Observed live again, on **all five** of this wave's workers, this branch included:

```
T451  WIP: STILLBORN … DEMOTED.   RECONCILE WOULD: demote to needs_retry
```

No behaviour change: nothing in `_branch_wip_core` can distinguish a live worker from a
dead one, and adding a liveness signal is a new signal, not a condition. What changed is
that the note now **says so**, in the record a human reads:

> "NOTE FOR THE READER (T451/C-T449-7): a worker that is ALIVE RIGHT NOW and has not yet
> made its first commit is byte-identical to this, and nothing in this function can tell
> them apart — the wrapper's `foreign_live_session_in_repo()` check is the only thing
> standing between this verdict and a live worker's branch."

---

## WHICH DIRECTION I FAIL IN, AND WHY

Both directions have destroyed work here, so this is stated as a rule rather than a
preference.

**The change makes exactly two verdicts more conservative and none less.** Every
transition is demote→REFUSE:

| | RED | GREEN |
|---|---|---|
| G — parked branch, ref carries the work | demote | **REFUSE** |
| H — carrier past the count cap | demote | **REFUSE** |

Nothing that refused before demotes now: C/T421, D/T428 (`merged`), E/T351, G2/T901
(`relocated`) are REFUSE before and after [`out/12-GREEN-drive.txt`]. And nothing that
demoted correctly stops demoting: B/T431 — the case T350 was filed for — A/T339, K, K2,
N, P and S all DEMOTE in both.

**So the residual failure direction is the refusal**, and its cost is a permanent
`in_progress` lie — STEP 5.5 item 4, the thing the driver of fire 20260828-140005 had to
override by hand. Three things bound it: the two new refusals both require a live ref to
**carry content**, which is a measured positive fact and not a name (T350's rule, kept);
the note in both cases names the ref, the path and the command to inspect it; and
`in_progress` is not terminal, so no downstream edge unblocks on it.

**Where I refused to buy safety with a false record.** The unrun-ref-probe case on the
stillborn leg could have been made to REFUSE — it would have looked more careful. It
demotes, because the absent leg (which has *more* evidence of a merge) already demotes
there, and an arm that is more generous on less evidence is how a lattice stops
partitioning.

---

## THE PARTITION PROPERTY — RE-RUN, AND SEEN TO FAIL

`bin/50-partition.py` enumerates **288** states — 8 branch × 4 landed-evidence × 9
ref-store — by **executing** `_branch_wip_core` and `reconcile_action` with the leaf
probes stubbed. Larger than T449's 256 because I carry an eighth branch state
(`rev-parse` rc=3) and a ninth ref state (index-unavailable), and my change makes far more
of the ancestor leg reachable.

```
                                  RED (main)   GREEN (this tree)
states enumerated                    288            288
states with NO usable verdict          0              0
states with TWO verdicts               0              0
arm-transcription MISMATCHES           0              0
exceptions raised                      0              0
redundant AGREEING arms                9              9   (pre-existing, both REFUSE)
```
[`out/50-partition.txt`]

**It partitions.** The redistribution is exact and conserved — RED's 9 `stillborn` states
become GREEN's 2 `stillborn` + 4 `stillborn-carried` + 3 additional `indeterminate`, and
the total stays 288 with every kind mapping to exactly one polarity.

The 9 "redundant agreeing arms" are pre-existing and present in RED too:
`merged-unverified` satisfies both `== "merged-unverified"` and `startswith("merged")`,
and both return REFUSE, so it is a redundant test rather than an ordering hazard. Reported
rather than swept into the "0".

**P-22 — the enumeration has been watched to FAIL.** `bin/51-partition-red.py` plants
three defects into copies of the shipped file, one at a time, verifying each planted
before running it [`out/51-partition-red.txt`]:

```
D1 arm returns the WRONG POLARITY                    CAUGHT  (4 transcription mismatches)
D2 arm DELETED -- falls through to the bottom demote CAUGHT  (4 transcription mismatches)
D3 T312 suffix no longer stripped                    CAUGHT  (8 states with two verdicts)
planted defects: 3, caught: 3, MISSED: 0
```

D2 is the exact trap the `reconcile_action` comment warns about. The instrument also
cross-checks its own transcription of the arm tests against what the real function
returns, so it cannot rot into a paraphrase that always agrees with itself (P-80).

---

## THE BAR, AND THE TOOL

*(filled in from the committed-tree run — see `out/90-bar-*.txt`)*

**`python3 .softhouse/bin/ready-tasks.py` on the live `tasks.json`.** `IN PROGRESS (5)` /
`READY (45)` / `BLOCKED (8)`, exit 0. Diffed against RED's output on the same tree: the
READY, BLOCKED, gates and edges sections are **byte-identical**, and the only differences
are the five in-progress workers' note *text*. Every kind is `STILLBORN` and every action
is `demote to needs_retry` in **both** — 5/5 identical
[`/tmp/t451/readylist.diff`, 16 lines, all note text].

**`--json` still parses.** `json.load` succeeds; keys `blocked`, `in_progress`, `ready`,
`unresolved_edges`; 45 / 5 / 8 / 0, agreeing with the text output.

**The bar's own reconciler guard, run directly against this tree's bytes**
[`out/40-ownership-selftest.txt`]:

```
GREEN LEG (shipped tool): 13/13 cells correct
RED LEG (planted T309 defect): 8/13 cells correct
SELFTEST OK: the planted T309 defect drives cell B' RED, and the shipped tool keeps it GREEN.
```

Unchanged from `main`'s result, so this change does not weaken the one guard standing
between this predicate and destroyed work.

---

## RESIDUALS — recorded, not closed

1. **The generous SUBJECT half already lets FOREIGN work block a demotion.** A finding of
   T451's own, not one of T449's conditions. **10 of the 15** `(id, ref)` pairs that carry
   on the live store today are foreign-owned review/retry branches whose commit subject
   names the task they are *about* — e.g. `T369: independent review of T351 -- REJECTED`
   would buy **T351** a `relocated` REFUSAL with **T369's** line
   [`out/21-realrepo-evidence.txt`]. **Not changed here**, on two measurements and one
   rule: every affected id is either absent from `tasks.json` or has a branch with commits
   ahead of `main`, so the ref arm is unreachable for all of them today
   [`out/22-liveness.txt`]; and narrowing the subject half is a behaviour change nobody has
   reviewed, which is the T306 class this task was told not to repeat. **File it.**
2. **Neither anchor sees a rescue ref whose diff touches only SHARED files.** A worker
   scoped to `ready-tasks.py` — T451's own scope — killed before its first commit leaves a
   diff naming no id at all, so its rescued work reads `name-only` and demotes. Fixture
   case **S**, demote under both anchors. `anywhere` would not have fixed it either.
3. **`main_tree()`'s cost is still spelled `0.083 s` in `.softhouse/handoff/T350-reconcile-content.md`**,
   which is on `main` and outside this task's scope. The code side is repaired; the handoff
   side is a one-line edit for whoever owns that file next.
4. **`REF_PROBE_SECONDS` introduces wall-clock nondeterminism** into a predicate that
   decides whether work is destroyed. It is the same nondeterminism `--deadline-secs`
   already had, it can only fire far outside the measured population (max fan-out 2 vs a
   6-second ceiling at ~0.1 s per ref), and truncation is declared in the note — but it is
   a trade, not a free win, and it is written down as one.

---

## INSTRUMENTS

| file | what it establishes |
|---|---|
| `bin/01-cardinals.py` | C-T449-3 and C-T449-4, re-counted at `b102875c` and at `main` |
| `bin/10-fixture.sh` | the synthetic repo: cases A, B, C, D, E, G, G2, K, K2, R, R2, S, H, N, P |
| `bin/11-drive.py` | RED vs GREEN over all 14 cases, with the verbatim notes |
| `bin/13-relaxed-probe.py` | T449's proposed patch, planted into the shipped bytes and driven both ways |
| `bin/20-realrepo-census.py` | the PATH axis over all 705 live refs — and the number I later corrected |
| `bin/21-realrepo-evidence.py` | the whole `ref_content_evidence`, shipped vs relaxed, over every live pair |
| `bin/22-liveness.py` | are the foreign-ref refusals reachable today? (no — and why) |
| `bin/30-cost.py` | C-T449-6, median/min/max over 9 runs |
| `bin/50-partition.py` | the 288-state enumeration, RED and GREEN, by execution |
| `bin/51-partition-red.py` | P-22: three planted defects, all three caught |

**Where I looked, for every "not found" above.** `.softhouse/bin/` (all `*.py`, `*.sh`),
`.softhouse/conformance.sh`, `.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py`,
the full `git ls-tree -r --name-only main`, all 705 live refs, and `.softhouse/tasks.json`.
No caller of `refs_carrying_content` or `ref_content_evidence` exists outside
`ready-tasks.py` itself; historical copies in `.softhouse/capture/t330-*/` call
`branch_wip`, `_absent_verdict` and `reconcile_action`, whose signatures are unchanged.
