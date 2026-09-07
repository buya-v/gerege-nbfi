# T537 — INDEPENDENT REVIEW of T536

**Subject:** branch `softhouse/T536-t528-conditions` @ `18c64389123066e7a08fd474445527dbc68d1c2d`
**Verified on origin:** `git ls-remote --heads origin refs/heads/softhouse/T536-t528-conditions`
→ `18c64389123066e7a08fd474445527dbc68d1c2d	refs/heads/softhouse/T536-t528-conditions` [VERIFIED: command run 2026-09-06 from this worktree]
**Diff read:** `git diff main...18c64389` — 21 files, +2501/−93. Nothing outside `.softhouse/`;
`git diff main...18c64389 -- '*.go' '*.sql'` is **0 bytes**. [VERIFIED]
**Method:** T536's handoff was read only to learn what it CLAIMS. Every number below was
re-measured by executing the code on this branch. Reproduction scripts and raw transcripts
are committed under `.softhouse/capture/t537-review-t536/`.

---

## VERDICT: **ACCEPT WITH CONDITIONS**

The branch is a genuine, substantial improvement on `main` and reverting it would be worse
than merging it: T527's classifier misses twelve findings this one catches, and it *waives*
two incident branches (`T520 → softhouse/T508-…`, `T522 → softhouse/T515-…`) that T536
correctly refuses. Nine of T528's ten fail-closed arms held before and **all ten hold now**,
plus the two new ones T528 asked for. The scope is clean and no money non-negotiable is in
the diff.

But **the central question answers NO.** T536 closed a LONGER LIST, not a class. I invented
eight phrasings it has never seen, in this pipeline's own idiom, and **8 of 8 laundered a
genuinely missing branch** — and one of them does it **on the real record**, moving
`UNBACKED-BRANCH T509` out of the findings and into the waivers exactly as T528 did to T527.
Separately, the stub arm the wiring gained is **cosmetic**: a three-line stub that prints the
documented banner buys a pass.

CRITICAL ×1, MAJOR ×2, MINOR ×4. Conditions in §9, written so a follow-up task can be filed
verbatim.

---

## 1. THE CENTRAL QUESTION — a CLASS, or a LONGER LIST? **A longer list.**

### 1.1 Eight invented phrasings, 8 of 8 laundered

`.softhouse/capture/t537-review-t536/t537-attack.py`, transcript `t537-attack.txt`.

Every cell is the SAME fixture, the SAME genuinely-absent branch `softhouse/TN-never-pushed`,
and the SAME sha — `origin/main`'s own tip, an ancestor of `origin/main` by construction.
The note is the only variable. `rc=2` means the guard refused; `rc=0` means the missing
branch was waived.

```
$ python3 .softhouse/capture/t537-review-t536/t537-attack.py <worktree@18c64389>

N1-merges-clean-into-main-at                   rc=0  BREAK -- LAUNDERED
    note: COMPLETE, merges clean into main@15c8953f
N2-origin-main-tip-at-dispatch                 rc=0  BREAK -- LAUNDERED
    note: origin/main tip 124bb446 at dispatch; my work is still on the branch
N3-rebased-on-main-at                          rc=0  BREAK -- LAUNDERED
    note: DONE, rebased on main @ 746a07aa
N4-refutation-read-as-assertion                rc=0  BREAK -- LAUNDERED
    note: CORRECTION: the earlier note claiming this landed 4c90b9cc is WITHDRAWN and
          FALSE -- nothing from this task ever reached origin
N5-other-task-named-AFTER-without-a-preposition rc=0 BREAK -- LAUNDERED
    note: the merge commit 4c90b9cc that T400 landed is already on main; mine is not
N6-verified-against-main-at                    rc=0  BREAK -- LAUNDERED
    note: COMPLETE, verified against main @ 3eaaf6ab
N7-tip-of-the-base-branch                      rc=0  BREAK -- LAUNDERED
    note: stacked work; base branch tip c29eca8d, my commits sit above it
N8-merged-at-negated                           rc=0  BREAK -- LAUNDERED
    note: NOT merged at d0bc4e92 -- this branch is UNRECOVERED and must be re-run

RESULT: 8 of 8 third phrasings LAUNDERED a genuinely missing branch.
```

Each waiver prints, verbatim:

```
    branch absent from origin, but it is this task's own branch field and 15c8953f is an
    ancestor of origin/main (15c8953f36d9)
```

**Anti-vacuity, same fixture, same absent branch — all three must be RED and all three are:**

```
CTL-no-sha-at-all              rc=2  RED as required
CTL-T527s-own-R5-phrasing      rc=2  RED as required   ("merge base X")
CTL-T528s-own-F1-phrasing      rc=2  RED as required   ("merge-base commit X")
controls failing: 0 (must be 0)
```

So the fixture is not one that goes green regardless, and T527's and T528's phrasings are
genuinely closed. **The hole is elsewhere, and it is the same hole.** [VERIFIED: `t537-attack.txt`]

**Idiom provenance** — these are not invented English, they are sampled from real notes in
`.softhouse/tasks.json` at this commit:

| case | real note it is modelled on |
|---|---|
| N1 | T374: `"COMPLETE, 4 commits, merges clean into main@faf5746e"` |
| N2 | T335 `"main, head d09585f58"`, T375 `"main, head 2422adc96"` — with `tip` for `head`, and `head` IS a veto word while `tip` is a promotion |
| N4 | T503: `"THE DRIVER'S EARLIER NOTE ON THIS TASK WAS WRONG AND IS WITHDRAWN."` |
| N5 | T528's own case L with the attribution preposition dropped |
| N7 | T515: `"stack 78a17873/2e1a09df (T501) -> 5c4233fc (T510)"` |
| N8 | T536's own note on itself: `"branch … NEVER REACHED origin … Nothing to rescue."` |

### 1.2 The same move, on the REAL record — T528's demonstration reproduced against T536

`.softhouse/capture/t537-review-t536/t537-reword-real.py`, transcript `t537-reword-real.txt`.
The sha is `23966a65`, which fire `cloud-20260906-2000` measured this evening as T509's
**republished** landing (`.softhouse/observations/2026-09-06-republished-under-new-hash.md`).

```
git cat-file -t 23966a65 -> commit
git merge-base --is-ancestor 23966a65 origin/main -> exit 0 (0 = it IS on main)

BEFORE     findings=19  pruned-proved-waivers=68    T509 branch is: A FINDING

T509's note, first line, as recorded:
  landed 857dd4d8 on softhouse/T509-ledgerguard-blindspot (merge base 10baca08). …

T509's note, REWORDED by T537 into a base citation that denies landing:
  origin/main tip 23966a65 at dispatch; my work is still on the branch and has NOT been
  merged.

AFTER      findings=17  pruned-proved-waivers=69    T509 branch is: WAIVED

findings REMOVED by the rewording: 2
   -('UNBACKED-BRANCH', 'T509', 'softhouse/T509-ledgerguard-blindspot')
   -('UNBACKED-COMMIT', 'T509', '857dd4d8')
waivers GAINED by the rewording: 1
   +('T509', 'softhouse/T509-ledgerguard-blindspot')
```

A note whose plain English is *"my work is still on the branch and has NOT been merged"*
clears its own missing branch. This is T528 F-1, one generation on, on the same task.
[VERIFIED: `t537-reword-real.txt`; `tasks.json` was restored — the script asserts it]

### 1.3 Why it recurs — the mechanism, not the phrasings

`LANDING_PROMOTIONS` is a whitelist of **four sha-adjacent verb patterns**
(`landed X`, `merge[d] as|at|commit X`, `tip [is] X`, `VERB … @ X`) and `BASE_WORDS` is a
veto whitelist of about fifteen base-citation words. Both match **vocabulary in the
neighbourhood of a hex token**; neither models what the sentence asserts, who is speaking,
or in which polarity. So:

* `tip X` promotes whether the tip is **this branch's** or **main's** (N2, N7);
* `merged at X` promotes whether the sentence affirms or **negates** it (N8);
* `landed X` promotes whether the clause asserts it or **withdraws it as false** (N4);
* `VERB … @ X` promotes whether `@ X` is the work or the **target** it was verified/rebased
  against (N1, N3, N6);
* the different-task veto looks left for any task id, but right only for an attribution
  preposition — so `"that T400 landed"` is invisible (N5), which T536's own comment predicts
  ("a task id that merely FOLLOWS a sha is usually a co-actor") without measuring the cost.

T536's inversion is real and is worth keeping — **an anchor added tomorrow does inherit
REFERENCE and cannot silently clear a branch**, and I confirmed that: adding a new pattern to
`CLAIM_ANCHORS` alone cannot waive anything. But the source comment's headline —
*"So LANDING IS NOW EARNED, NOT ASSUMED"* — is **not** what the code does. It is earned by
**being spelled in one of four ways within one clause of a sha**, which is the same currency
the last two repairs were paid in.

**FINDING F-1 — CRITICAL.** The default was inverted; the *decision procedure* was not
changed. Free prose still decides whether a missing branch is forgiven.

---

## 2. RE-MEASURING THE TWO NUMBERS

Script `t537-measure.sh`, transcript `t537-measure.txt`. Both classifiers pointed at the
**same** record (the tree at `18c64389`) and the same origin state, so the classifier is the
only variable.

```
A. T527's checker (on main) over the record at 18c64389
   origin: 62 branches, main=b09d2dcf89e7 | records checked: 475
   backed: 49 branch(es) on origin, 77 pruned-but-proved-on-main, 117 commit(s) reachable
   WAIVED (merged-and-pruned, PROVED …): 77          findings: 7

B. T536's checker over the same record
   origin: 62 branches, main=b09d2dcf89e7 | records checked: 475
   backed: 49 branch(es) on origin, 68 pruned-but-proved-on-main, 134 commit(s) reachable
   WAIVED (merged-and-pruned, PROVED …): 68          findings: 19
```

### 2.1 The claim "66 of 73" — I cannot reproduce it, and the command named to reproduce it does not exist

`check-branch-published.py:272` states: *"these four carry 66 of the 73 legitimate
merged-and-pruned waivers (`--measure-waivers` reproduces the count)"*.

```
$ python3 …/check-branch-published.py --measure-waivers --repo …
usage error: unknown argument '--measure-waivers'
```
[VERIFIED: `t537-measure.txt` §E. `grep -n "measure-waivers" check-branch-published.py` returns
**one hit — the comment itself**; the CLI's argument list is
`--baseline --full-baseline --help --json --keep --repo --selftest --timeout --write-baseline`.]

Where 73 and 66 come from: they are two numbers measured under **different** conditions and
subtracted anyway.

| source | origin | records | pruned-proved waivers |
|---|---|---|---|
| `capture/t527-branch-published/report-on-main.txt` (T527, shipped) | 48 branches, `dd27570094fe` | 468 | **73** |
| `capture/t527-branch-published/t536-report-on-main.txt` (T536) | 55 branches, `c2127db33b76` | 475 | **66** |
| **T537, both classifiers, one record, one origin** | 62 branches, `b09d2dcf89e7` | 475 | **77 → 68** |

Controlled, the classifier costs **nine** waivers, not seven. [VERIFIED: `t537-measure.txt` §A–C]

### 2.2 The nine, and the two §5 does not name

```
LOST by T536's stricter classifier (in T527, not in T536):
T353  softhouse/T353-t342-conditions
T357  softhouse/T357-a2-11-section1-red
T358  softhouse/T358-t323-conditions
T361  softhouse/T361-review-t353
T375  softhouse/rescued-agent-ac5a2db446e903ba0-20260828-140005
T476  softhouse/T467-t464-conditions
T477  softhouse/T466-skipwt-smudge
T520  softhouse/T508-journalentry-insert-schema      <-- not in §5's census
T522  softhouse/T515-savings-classification-rework   <-- not in §5's census
GAINED by T536: (none)
```

The handoff §5 is titled *"the seven waivers that turned red"* and lists exactly the first
seven. T520 and T522 also turned red. Both are **correct** findings — they are 2026-09-04
incident branches and T527 was wrongly waiving them, which is a point in T536's favour — but
the census that claims to be exhaustive is short by two. [VERIFIED: `t537-waivers-t527.txt`
vs `t537-waivers-t536.txt`, `comm -23`]

I checked the seven that T536 does name. All four "field branch" cases (T353, T357, T358,
T361) carry notes reading *"COMPLETE on branch, head X … NOT MERGED"* — the branch is absent
from origin and the note itself denies landing, so refusing them is right, not a cost.
[VERIFIED: notes read from `tasks.json` at `18c64389`]

### 2.3 "Probe breaks closed: 7 of 7" — sustained, and the 7th IS honestly named

T528 built twelve cases and seven read as proof of landing (B, C, E, G, H, K, L). All seven
are now `--selftest` cases and all seven pass, including case **L** — the one T528's own
sizing left open. T536 states *"There is no 7th break I failed to close"* and that is
**true as stated**. [VERIFIED: `--selftest` transcript below; `t536-attack-after.txt`
reproduces 0 breaks of 12 and I re-ran the equivalent through the selftest]

`--selftest`: **44 cases, 0 failures**, 25.0 s wall clock, including
`G-BASELINE-EXCLUDES-INCIDENT` (314 entries, incident tasks present: none).
[VERIFIED: run from the worktree at `18c64389`]

The claim *"genuine findings that survived: 21 of 21, `F(old) − F(new)` is empty"* also
reproduces on my controlled run: T527's 7 findings are a strict subset of T536's 19.
[VERIFIED: `t537-measure.txt` §D and the two finding lists]

**FINDING F-3 — MAJOR.** The headline metric is not reproducible, the reproduction command
named in the source does not exist, the controlled delta is 9 not 7, and the "seven waivers
that turned red" census is short by two. In a guard whose thesis is *"the record asserted
something the tree does not support"*, that is the same defect one level in — which is
exactly what T528 F-6 was, and what T536 fixed elsewhere.

---

## 3. THE BASELINE FREEZE — driven, not read

Script `t537-freeze.py`, transcript `t537-freeze.txt`.

### 3.1 My own synthetic incident is NOT waived — the property holds

```
--- A. synthetic incident, id T9001 (nothing in this repo has ever used it)
A-T9001-above-the-line   id=T9001  freeze=T527 (bl.json)  waived=False want=False  PASS
      REFUSED T9001  softhouse/T9001-never-pushed   above the freeze line T527 -- this is a
      claim from AFTER the control existed, so it is a live incident, not history

--- B. anti-vacuity: a historical id must STILL be waivable
B-T42-historical         id=T42    freeze=T527 (bl.json)  waived=True  want=True   PASS

--- G. point --write-baseline at a FRESH file (no frozen_above in it)
G-fresh-baseline-file    id=T9002  freeze=T527 (module constant)  waived=False  PASS
```

### 3.2 The boundary cannot be moved by an ordinary regeneration — it holds

```
--- C. ORDINARY REGENERATION must not move the line
shipped frozen_above BEFORE: 'T527'  (314 waivers)
after ONE --write-baseline over the REAL record:
  frozen_above AFTER : 'T527'   (unchanged: True)
  findings REFUSED   : 9   (all nine 2026-09-04 incident subjects, named)

--- D. DELETING the baseline must not lift the line
load_frozen_above(<missing file>) -> 'T527' from module constant
regenerated-from-nothing: frozen_above='T527', 324 waivers, 9 refused
```

Deleting `baseline.json` falls back to the module constant; regeneration writes the line
back unchanged; the nine incident subjects are refused by name in both. **This is the
strongest part of the branch and it does what it says.** [VERIFIED: `t537-freeze.txt` §C, §D]

### 3.3 Two gaps the freeze does not cover

```
--- E. id-form gap: A2-999, an id nothing has ever used, but an A2-SHAPED one
E-A2-999   id=A2-999  freeze=T527  waived=True  want=False  *** FAIL
```

`task_ordinal` returns `(0, n)` for every `A2-<n>` and `(1, n)` for every `T<n>`, so **every
A2-shaped id sorts below every T id**, forever. The docstring's guarantee is *"an id it
cannot date cannot be shown to be historical"*; the uncovered case is an id it **mis-dates**.
The pipeline still carries `A2-` ids in the live record (`A2-34` is a `done` task), so this
is not a hypothetical shape.

**FINDING F-4 — MINOR.**

```
--- D (continued). findings this regeneration DID waive that the shipped file does not carry:
   NEW  T312  060f00330
   NEW  T312  c1a3888a
   NEW  T335  d09585f58
   NEW  T353  softhouse/T353-t342-conditions
   NEW  T357  softhouse/T357-a2-11-section1-red
   NEW  T358  softhouse/T358-t323-conditions
   NEW  T361  softhouse/T361-review-t353
   NEW  T375  softhouse/rescued-agent-…-20260828-140005
   NEW  T476  softhouse/T467-t464-conditions
   NEW  T477  softhouse/T466-skipwt-smudge
```

The first three are **the three genuine unpushed-work commit claims T528 F-4 fought to
surface and that this very branch detects for the first time**. Because their task ids are
historical, one `--write-baseline` run forgives all ten and stamps each with the boilerplate
`"pre-existing when this control was introduced (T527, 2026-09-04); no proof of landing
survives in git"` — a sentence that is false of `c1a3888a`. T536 correctly did **not**
regenerate the shipped baseline, so nothing is laundered today; the hazard is that the freeze
is by GENERATION and the guard's own *knowledge* advanced.

**FINDING F-5 — MINOR.** Freeze by KEY SET as well as by generation: an ordinary
regeneration should only ever be able to REMOVE entries.

*(Informational, not a finding: the boundary is inclusive — a finding with id exactly `T527`
is waivable. That is what "above the freeze line" says, and T527 is the guard's own task.)*

---

## 4. FAIL-CLOSED REGRESSION — T528's ten arms, re-run

Script `t537-failclosed.sh`, transcript `t537-failclosed.txt`. Every cell reads
`ready-tasks.py`'s **own** exit code (`0` = gate CLEAN, `5` = gate NOT CLEAN) except
FC2/FC3/FC4, which additionally read the checker directly so the distinct `2`/`3` verdicts
are visible rather than flattened to `5`.

```
FC0-control-clean-fixture                      PASS  (exit 0, saw "check-branch-published: CLEAN")
FC1-origin-unreachable                         PASS  (exit 5, saw "CANNOT ESTABLISH ORIGIN")
FC2-git-hangs-(checker-direct)                 PASS  (exit 3, saw "CANNOT ESTABLISH ORIGIN")
FC3-ls-remote-garbage-(checker-direct)         PASS  (exit 3, saw "ORIGIN LISTED NO BRANCHES")
FC4-ls-remote-partial-(checker-direct)         PASS  (exit 2, saw "UNBACKED-BRANCH")
FC5-archive-unparseable                        PASS  (exit 5, saw "UNREADABLE TASK RECORD")
FC6-archive-has-no-tasks-list                  PASS  (exit 5, saw "TASK RECORD HAS NO tasks LIST")
FC7-malformed-baseline                         PASS  (exit 5, saw "NOT a pass")
FC8-checker-raises-mid-run                     PASS  (exit 5, saw "NOT a pass")
FC9-checker-deleted                            PASS  (exit 5, saw "checker is not on disk")
FC10-silent-stub-over-a-dirty-record           PASS  (exit 5, saw "never printed its verdict line")
FC11-BANNER-stub-over-a-dirty-record           ***BREAK*** (exit 0)
FC12-current-tasks.json-unparseable            PASS  (exit 5, saw "UNREADABLE TASK RECORD")
```

**All ten of T528's arms hold.** FC10 is the arm T536 added (T528 F-5's silent stub) and it
works. FC12 is T528 F-7 — `main` exits 1 with a traceback, this branch exits **5**. FC11 is
mine and is §5.

**None of T528's ten had to be approximated away.** FC2 was reconstructed with a PATH shim
whose `git` sleeps 30 s against `--timeout 3`; FC3/FC4 with PATH shims that rewrite
`ls-remote`'s output; FC8 by injecting `raise RuntimeError` as the first statement of
`check()`. The one methodological difference from T528: T528 read `ready-tasks.py`'s exit
code for FC2/FC3/FC4 as well, which collapses `3` and `2` into `5`; I read both so the
distinctness is visible. That is a strengthening, not a substitution.

---

## 5. THE STUB ARM — **cosmetic**

`t537-stub-arm.sh` / `t537-stub-arm.txt`, and FC11 above end-to-end through `ready-tasks.py`.

The repair is `if res.returncode == 0 and CLEAN_VERDICT in res.stdout:` where
`CLEAN_VERDICT = "check-branch-published: CLEAN"`. The check is that the checker printed a
**string**. Here is the whole checker, replaced:

```python
#!/usr/bin/env python3
# T537 ADVERSARIAL STUB: prints the exact verdict line the gate looks for, checks nothing.
import sys
print("=" * 78)
print("check-branch-published: CLEAN")
print("=" * 78)
sys.exit(0)
```

Driving `branch_published_gate()` directly, over a record claiming
`softhouse/T999-never-pushed-anywhere` and `landed deadbeef`:

```
---- stub is 7 lines ----
==============================================================================
STEP 0 -- IS THE RECORD BACKED BY origin?  (T527, check-branch-published.py)
==============================================================================
==============================================================================
check-branch-published: CLEAN
==============================================================================

branch_published_gate() RETURNED: True
```

And end-to-end through the caller (FC11), with a **three-line** stub:

```
FC11-BANNER-stub-over-a-dirty-record   ***BREAK*** (exit 0 -- a 3-line stub printing the
                                       documented banner bought a PASS over a record whose
                                       branch was never pushed)
      STEP 0 -- IS THE RECORD BACKED BY origin?  (T527, check-branch-published.py)
      check-branch-published: CLEAN
      READY (0)
```

T536's docstring says *"A stub that prints nothing cannot forge that"* — which is literally
true and is exactly the size of the repair. It raised the cost of a de-facto disable from
**two lines to three**, and it published the incantation: the required string is a named
module constant, `CLEAN_VERDICT`, sitting in the docstring of the function it defeats.

**FINDING F-2 — MAJOR.** A banner is not evidence that the checker ran. The condition T528
asked for was "positive evidence the real checker ran"; a string the repo prints in three
places is negative evidence at best.

---

## 6. THE PROGRAM MUST STILL RUN — **it does**

`t537-program-runs.sh` / `t537-program-runs.txt`, against the real record at `18c64389`.

```
A. plain run
   exit code: 5      wall clock: 3.03 s      report lines: 404
     2: STEP 0 -- IS THE RECORD BACKED BY origin?
     5: check-branch-published: REFUSE -- 19 claim(s) origin has never heard of
   252: >>> THE RECORD BELOW CLAIMS WORK THAT origin HAS NEVER HEARD OF …
   257: IN PROGRESS -- ALREADY DISPATCHED, do not dispatch again (2)
   274: READY (64)
   370: BLOCKED (15)
   401: STEP 0 VERDICT: NOT CLEAN

B. --json
   exit 5, stdout 1439 bytes parses as JSON, stderr 21681 bytes
   keys: ['blocked','branch_published','in_progress','ready','unresolved_edges']
   branch_published: NOT_CLEAN     ready count: 64

C. checker --json in the exit-3 arm
   exit 3, stdout parses as JSON -> CANNOT_ESTABLISH_ORIGIN, banner on stderr   (T528 F-8 closed)

D. bypass hunt
   checker's accepted flags: --baseline --full-baseline --help --json --keep --repo
                             --selftest --timeout --write-baseline
   os.environ / getenv reads in either file: ONE, in the selftest fixture helper `_sh`
                                             (GIT_AUTHOR_* for the throwaway repos)
   offline / no-fetch / bypass / override / disable: comment text only, no code path
```

`READY` prints **through** the refusal at line 274 of 404 — T528 measured it at line 587 of
684, so T528 F-9 (the 314-line waiver dump) is genuinely closed. 3.03 s is not a fire the
driver will want to disable. **No bypass flag, no env var.** [VERIFIED: `t537-program-runs.txt`]

---

## 7. ONE MORE FINDING FROM THE MEASUREMENT — one branch, two verdicts

In the same report, `softhouse/T466-skipwt-smudge` is:

* **WAIVED** at line 173 under `T466` (its owner binds a landing sha to it), and
* **REPORTED UNBACKED** at line 28 under `T477`, which merely names it in prose.

Same for `softhouse/T467-t464-conditions` (waived under T467, reported under T476). Two of
the nineteen findings are this shape. T536's F-2 fix scopes proof per **(task, branch)** pair;
the correct scope is per **branch across the whole record** — a branch proved landed by its
owner is landed, and reporting it as missing under a task that only mentions it is the noise
the tool's own docstring warns about (*"one false name in a report about missing work is one
too many — it is exactly the sort of detail that lets a reader dismiss the other 300"*).

**FINDING F-6 — MINOR.** [VERIFIED: `t537-measure-t536.txt` lines 25, 28, 173, 175]

**FINDING F-7 — MINOR.** The source comment *"So LANDING IS NOW EARNED, NOT ASSUMED"*
(`check-branch-published.py:211`) overstates what §1 shows. The adjacent claim — *"A new
extraction anchor added tomorrow inherits REFERENCE and therefore cannot silently clear a
missing branch"* — is **true** and is the branch's real achievement; it should stay, and the
overstatement should go, or the next reviewer will read the class as closed.

---

## 8. POLARITY, AND WHETHER T554 AND F-1 ARE ONE DEFECT — **they are one defect**

The live evidence from fire `cloud-20260906-2000`: after reconciling five unbacked claims the
count went 8 → 3, and all three residuals were sentences **correctly recording that a sha is
dead** — e.g. *"the claimed commit 857dd4d8 is dead — `git cat-file -t` returns 'Not a valid
object name'"*. Filed as T554; not mine to fix.

**Does T536's anchor model have a place for polarity? No — none, by construction.**
`extract_claims` runs regexes over free text. The only things that can demote a match are
`BASE_WORDS` (fifteen base-citation nouns/verbs), the different-task veto, the all-digit veto
and `DIGEST_CONTEXT`. There is no negation term, no quotation term, no correction/withdrawal
term, and no notion of a sentence having a truth value. `not`, `never`, `false`, `withdrawn`,
`dead`, `UNRECOVERED` are not in any pattern in the file. [VERIFIED by loading the module and
scanning every compiled pattern in `CLAIM_ANCHORS`, `CLAIM_REGIONS`, `LANDING_PROMOTIONS`,
`LANDING_BINDINGS`, `BASE_WORDS`, `DIGEST_CONTEXT`, `OTHER_TASK_BEFORE`, `OTHER_TASK_AFTER`,
`BRANCH_RE`, `NOT_A_BRANCH` — **23 regex patterns, 0 containing any polarity token**]

**And I drove it, from the laundering side.** N4 and N8 are refutations:

* `"CORRECTION: the earlier note claiming this landed 4c90b9cc is WITHDRAWN and FALSE —
  nothing from this task ever reached origin"` → **the branch is WAIVED**
* `"NOT merged at d0bc4e92 — this branch is UNRECOVERED and must be re-run"` → **WAIVED**
* and on the real record: `"…my work is still on the branch and has NOT been merged"` →
  T509's branch moves from FINDING to WAIVER

**So the two defects are the same defect, and it is a single sentence:** the classifier
assigns a truth-conditional role to a hex token from *vocabulary in its neighbourhood*, with
no model of what the sentence asserts. T554 is that defect making the guard **too loud** (a
truthful denial re-tripping the commit arm). F-1 is that defect making the guard **too
quiet** (a truthful denial forgiving a missing branch). The second is strictly the more
dangerous, because it is silent.

**Which repair subsumes which — the driver needs this before it dispatches T554.**

* **The F-1 repair subsumes T554's WAIVER half completely.** If a branch may be waived only
  by structured evidence (a `landed_commit` field the merging fire writes, or a commit on
  `origin/main` whose message or trailer names the task id), then prose can no longer forgive
  anything and polarity stops mattering on that arm. Every one of N1–N8 goes red, refutations
  included.
* **The F-1 repair does NOT subsume T554's FINDING half.** A dead sha quoted inside a note
  that says it is dead still trips the **commit** arm, which asks only "does this exist on
  origin?" — a question polarity does not change the answer to. That residual is real and
  small.
* **The cheapest correct answer to the residual is a record convention, not a classifier
  change**, and tonight's fire found it by accident: refuted shas belong in an observation
  file, not in `tasks.json` notes — which is what
  `.softhouse/observations/2026-09-06-republished-under-new-hash.md` already did, and it is
  why the count fell to three rather than eight. If quoting a dead sha in a note is
  unavoidable, a single explicit marker the extractor honours (e.g. a `DEAD:` prefix, checked
  the way `DIGEST_CONTEXT` already is) is a one-line change and is the only *classifier*
  work T554 needs.

**Recommendation to the driver:** re-shape T554 as (a) a record-convention rule plus one
`DEAD:` context veto, and (b) make it DEPEND on the F-1 repair rather than run beside it —
because a polarity patch shipped alone would close N4 and N8 and leave N1, N2, N3, N5, N6 and
N7 open, and would then be reported as "polarity fixed". That is the third repair of this
same hole in three tasks.

---

## 9. FINDINGS AND CONDITIONS

| # | sev | finding |
|---|---|---|
| F-1 | **CRITICAL** | 8 of 8 invented phrasings launder a genuinely missing branch; one does it on the real record (T509, findings 19→17). LANDING is decided by sha-adjacent vocabulary, not by evidence. |
| F-2 | **MAJOR** | The stub arm is cosmetic: a 3-line stub printing `check-branch-published: CLEAN` exits 0 and the gate returns True over a never-pushed branch. |
| F-3 | **MAJOR** | "66 of 73" is not reproducible; `--measure-waivers` does not exist; the controlled delta is 9 not 7; §5's "seven waivers that turned red" is short by two (T520, T522). |
| F-4 | MINOR | `A2-999` — an id nothing has ever used — is dated as prehistory and is waivable. |
| F-5 | MINOR | An ordinary `--write-baseline` today adds 10 unreviewed waivers, including the three genuine unpushed-work commits this branch is the first to detect. |
| F-6 | MINOR | One branch, two verdicts in the same report (`softhouse/T466-skipwt-smudge` waived under T466, reported unbacked under T477; same for T467/T476). |
| F-7 | MINOR | The source comment "LANDING IS NOW EARNED, NOT ASSUMED" overstates what the code does. |

### CONDITIONS — file verbatim

1. **(F-1, CRITICAL) Take the waiver decision out of free prose.** The merged-and-pruned
   exemption must be provable only by STRUCTURED evidence, and prose must be reduced to
   raising the question, never answering it. Concretely: a branch may be waived only by
   (a) an explicit `landed_commit` / `merged_commit` FIELD on that task, or (b) a commit
   reachable from `origin/main` whose subject or trailer names the task id — never by a
   phrase in `note`. `LANDING_PROMOTIONS` and `LANDING_BINDINGS` are then deleted, not
   extended. *Checkable:* `.softhouse/capture/t537-review-t536/t537-attack.py` must report
   **0 of 8 laundered** with its three anti-vacuity controls still RED, and
   `t537-reword-real.py` must show T509's branch staying a FINDING after the rewording.
   Adding my eight notes as `--selftest` cases is necessary but **not sufficient** and must
   not be offered as the repair — that is the move T527 and T528 both made.

2. **(F-2, MAJOR) Make the wiring require evidence only a real run can produce.** Run the
   checker with `--json`, parse the document, and require at minimum: `verdict == "CLEAN"`,
   an `origin_main` that equals a sha `ready-tasks.py` obtains **itself** from
   `git ls-remote --heads origin refs/heads/main`, and a `checked_tasks` count not less than
   the number of terminal-status tasks `ready-tasks.py` counted in its own `load()`. A stub
   cannot forge those without doing the work. *Checkable:* cell FC11 of
   `.softhouse/capture/t537-review-t536/t537-failclosed.sh` must go to exit 5, and FC0 must
   still be exit 0.

3. **(F-3, MAJOR) Ship the flag or delete the claim, and recount apples-to-apples.**
   Either implement `--measure-waivers` or remove the parenthetical at
   `check-branch-published.py:272`. Re-measure the waiver delta with both classifiers over
   one record and one origin state and correct the number in the source comment and the
   handoff (my controlled run: 77 → 68). Extend the handoff §5 census from seven to nine,
   naming T520 and T522 and stating that both are correct refusals.

4. **(F-5 + F-4, MINOR) Freeze the baseline by KEY SET as well as by generation.**
   `--write-baseline` must refuse any finding whose `<task-id>\t<subject>` key is not already
   in the previous baseline, unless an explicit `--adopt-new` flag is passed, which must
   print every adopted key. Additionally, `task_ordinal` must not date an `A2-<n>` id as
   historical purely by form — bound it to the A2 ids the record actually contains, or refuse
   `A2-` ids above the highest one present. *Checkable:* `t537-freeze.py` cells E and D — E
   must become `waived=False`, and D must report **0** new keys without `--adopt-new`.

5. **(F-6, MINOR) Scope the proof per BRANCH across the whole record, not per (task, branch)
   pair.** A branch proved landed by any task that binds a landing sha to it is landed for
   every task that names it. *Checkable:* `softhouse/T466-skipwt-smudge` and
   `softhouse/T467-t464-conditions` must appear exactly once each in the report, as waivers.

6. **(F-7, MINOR) Correct the overstatement.** Replace *"So LANDING IS NOW EARNED, NOT
   ASSUMED"* with what is actually true and is worth keeping: *"A new EXTRACTION anchor
   inherits REFERENCE and cannot clear a missing branch. Promotion is still decided by four
   phrasings in free prose, and T537 measured eight more that defeat it."*

### For the driver, on T554

T554 and F-1 are **one defect** — see §8. Condition 1 subsumes T554's waiver half entirely.
T554 should be re-scoped to its residual (a `DEAD:`-style context veto on the commit arm plus
the record convention of keeping refuted shas in observation files) and made to **depend on**
condition 1, so that a polarity patch is not shipped alone and reported as the class being
closed.

---

## 10. WHAT I CHECKED AND FOUND NOTHING

* **Non-negotiables.** `git diff main...18c64389 -- '*.go' '*.sql'` is 0 bytes; no file
  outside `.softhouse/` is touched. No money path, no ledger code, no API surface, no
  `Idempotency-Key` path, no schema. Nothing to grade against the money rules.
* **Adapter contract.** Not touched; no DEC-n referenced or amended.
* **Database.** No driver, dialect, connection string or port appears in the diff.
* **Bypass surface.** §6D — no `--offline`, `--no-fetch`, `--skip`, `--force`, no env var.
  The single `os.environ` read is `GIT_AUTHOR_*` defaults inside the selftest fixture helper.
* **Self-record.** T536 did not edit `tasks.json` to record its own completion, so it did not
  create the exact claim the guard exists to catch.
* **`--selftest` integrity.** 44 cases / 0 failures; every RED is paired with a
  subject-removed GREEN; `_fixture` retries until no short sha is all-digit, which removes a
  real 2.3 %-per-sha flake rather than papering over one.
* **`baseline.json` diff.** Two added lines only (`frozen_above`, `frozen_above_note`); the
  314 waivers are byte-identical, highest id present is `T504`, entries above the freeze line:
  **none**. [VERIFIED: `t537-measure.txt` §F]

---

## 11. REPRODUCTION

All under `.softhouse/capture/t537-review-t536/`; `<WT>` is a worktree at `18c64389`.

```
python3 t537-attack.py        <WT>                    # §1.1  -> t537-attack.txt
python3 t537-reword-real.py   <WT>                    # §1.2  -> t537-reword-real.txt
sh      t537-measure.sh       <this-worktree> <WT>    # §2    -> t537-measure*.txt
python3 t537-freeze.py        <WT>                    # §3    -> t537-freeze.txt
sh      t537-failclosed.sh    <WT> <scratch>          # §4,§5 -> t537-failclosed.txt
sh      t537-stub-arm.sh      <scratch-root>          # §5    -> t537-stub-arm.txt
sh      t537-program-runs.sh  <WT> <outdir>           # §6    -> t537-program-runs.txt
python3 <WT>/.softhouse/bin/check-branch-published.py --selftest
```

`t537-reword-real.py` writes to `<WT>/.softhouse/tasks.json` and restores it in a `finally`;
it prints `tasks.json restored: True` on exit. Everything else works in `mkdtemp` fixtures.
