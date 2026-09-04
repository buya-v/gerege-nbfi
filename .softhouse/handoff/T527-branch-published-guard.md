# T527 — `check-branch-published.py`: REFUSE when the record claims work origin never heard of

**Branch:** `softhouse/T527-branch-published-guard`
**Base:** `origin/main` at `a95db897` (the worktree was created at `4394e141`, one commit behind; I
reset onto `origin/main` before starting). `origin/main` moved to `dd275700` during the run — other
fires were pushing — which changes nothing below except the `main=` sha printed in the transcripts.

---

## 1. What I measured, before building anything

Reproduced the driver's measurement. I am a worktree-isolated agent, so I ran each `rev-parse`
separately rather than in the driver's `for` loop; the object store is the same one
(`git rev-parse --git-common-dir` → `/home/user/gerege-nbfi/.git`).

| sha | `git rev-parse --verify -q <sha>^{commit}` |
|---|---|
| `1abd3a11` | exit 1 — **ABSENT** |
| `857dd4d8` | exit 1 — **ABSENT** |
| `5c4233fc` | exit 1 — **ABSENT** |
| `8ff5ff15` | exit 1 — **ABSENT** |
| `84dc208e` | exit 1 — **ABSENT** |

`git ls-remote --heads origin 'refs/heads/softhouse/*'` → 46 refs, highest task id **T497**
(`softhouse/T497-t491-conditions`). Nothing above T497 is on origin. Confirmed the notes on main:
T508/T509/T515 `done`, T510 `needs_retry`, T512 `needs_conditions`, each naming a branch and a sha.

**One measurement the brief did not mention, and it changes the tool's design: the clone was
SHALLOW.** `/home/user/gerege-nbfi/.git/shallow` held 4 grafts and `git rev-list --count origin/main`
was **153**. On a shallow clone "this sha does not resolve" is nearly meaningless — most of main's
own history does not resolve either — so ancestry against `origin/main` cannot decide anything.
`git fetch --unshallow origin` took **1.6 s** and yielded **2944** commits on main. **I ran that
unshallow against the shared object store**, which is additive (objects and `refs/remotes/origin/*`
only) but is a change to the environment outside my four files, so I am flagging it. The tool now
does the same thing itself, and REFUSES (exit 3) if the deepen fails.

---

## 2. What I built — `.softhouse/bin/check-branch-published.py`

Reads `.softhouse/tasks.json` **and** every `.softhouse/runs/*.tasks.json` archive (there is exactly
one, `2026-08-17-run1-harness-schedule-poc.tasks.json`, holding 153 records). 468 records are in a
checked status (`done`, `merged`, `needs_retry`, `needs_conditions`, `parked`).

**Claims are extracted from the fields `branch` / `branch_mac` / `branch_cloud` / `tip` /
`merged_commit` AND from the free-text `note`.** The free-text arm is load-bearing, not a nicety:
**not one of the five incident tasks has a `tip` or a `merged_commit` field.** All five carry their
sha in prose. A field-only reader scores this incident CLEAN.

**Verdicts.** `0` CLEAN · `2` REFUSE, each claim named · `3` REFUSE — CANNOT ESTABLISH ORIGIN
(distinct banner, distinct code) · `64` usage.

**Fail closed (P-45).** Before reading a single record the tool must (a) get a non-empty
`git ls-remote --heads origin`, (b) deepen the repo if shallow, (c) `git fetch` successfully, (d)
confirm every origin tip is now a local commit object, (e) find `origin/main`. Any of those failing
is exit 3 with `THIS IS NOT A PASS. Nothing was checked.` **There is deliberately no `--offline` or
`--no-fetch` flag** — that escape hatch is the P-91 burden inversion, and an offline pass here would
have scored this very incident green. Reachability is computed by `git rev-list` over the shas
`ls-remote` returned, never over `refs/remotes/origin/*`, so a stale remote-tracking ref cannot
widen the set.

**The three exemptions, all printed:**

1. **PRUNED-PROVED** — a branch absent from origin whose task claims a **LANDING** commit that is an
   ancestor of `origin/main` (`git merge-base --is-ancestor`). Never a note that says "merged".
2. **BASELINE** — enumerated below.
3. **UNCLASSIFIED-HEX** — hex tokens in notes that no claim anchor captured; counted, sampled and
   reasoned on every run (978 occurrences, 217 distinct on main today).

### The defect I shipped and then removed — read this one first

My first working build treated **every** anchored sha as proof of landing. T508's note says
`landed 1abd3a11 on softhouse/T508-... (Driver-verified scope (3 files, merge-base 10baca08))`, and
`10baca08` is a main commit, so **T508 CLEARED ITS OWN MISSING BRANCH**. A merge base is the one
commit guaranteed to be on main whether or not a line of the work ever landed. The tool now tags each
anchor `LANDING` or `REFERENCE`; only `LANDING` can prove. Regression control:
`R5-merge-base-does-not-prove-a-branch` (RED) paired with `R5-control-same-sha-claimed-as-LANDING`
(GREEN on the *same sha*, differing only in the claim verb).

### Why the commit extractor is context-anchored, and what that costs

A bare `\b[0-9a-f]{8}\b` over the notes yields 250 distinct tokens, 95 unresolvable — and **most of
those 95 are not commits at all**. Measured examples: `T84 "canonical sha256 01b41d9c…"`,
`T176 "sha256 fecea4b2…"`, `T487 "ATTESTED IDENTICAL to the graded tree,
265f9192b6eea682f8975ec57dfebf201442f7cd"`, `T228 "store 8968c559"`, and
`T1/T526 "Fineract commit 426a23544" / "pinned /home/user/fineract @ 426a23544"` — the pinned
**Fineract** checkout, a different repository. Date-shaped fire ids (`20260829`) are valid hex too.

So a token counts as a commit claim only inside a claim phrase (`landed X`, `merged as/at X`,
`commit X`, `tip X`, `@ X`, `<branch> (X)`, or a `stack …` clause), and all-digit tokens and
digest/foreign-repo contexts are vetoed. **THE BLIND SPOT IS REAL AND IS PRINTED:** a note claiming a
commit in a phrasing the anchor list does not know is *not checked*, and the run prints the count and
a sample of every unclassified token so the size of that gap is a number on screen. `5c4233fc` — one
of the five, named only inside T515's `stack 78a17873/2e1a09df (T501) -> 5c4233fc (T510) -> 84dc208e`
— is caught by the region anchor, and has its own selftest case (`R2b`).

### The baseline — the weakest part of this work, stated plainly

Run over the whole record with no baseline, the tool produces **332 findings**, of which **18 are the
incident** and 314 are historical: `A2-*` and `T38`…`T501` branches pruned long ago, landed by squash
commits that named neither the branch nor left a per-task artefact, plus 9 of their tip shas. Nothing
in git proves those landed. Refusing on all 332 every fire produces a report nobody reads, which is
P-45 from the other side.

So `.softhouse/capture/t527-branch-published/baseline.json` waives **314** items — **305
UNBACKED-BRANCH and 9 UNBACKED-COMMIT**. The 9 waived commits, named here because a waiver you have
to open a file to see is half a silent one:

`T122 7e49bd93` (archive) · `T329 61c0f382` · `T351 a0139c5d` · `T351 e10e3f07` · `T369 e10e3f07` ·
`T370 4925bbef` · `T472 0accb769` · `T473 4bce914a` · `T474 409c7693`

**Why a baseline is safe here:** every key is an exact `<task-id>\t<branch-or-commit>` pair. There is
no wildcard and no prefix, so waiving `T474\t409c7693` cannot waive `1abd3a11` or any commit that
does not exist yet. **Why it is still the weak point:** a *later* regeneration would waive whatever
is unbacked at that moment — that is how a baseline launders a fresh incident. Two things stand
against it: `--write-baseline` refuses **by name** to add T508/T509/T510/T512/T515/T520/T522/T523 or
the five shas (and prints what it refused — 18 items), and every waiver is printed on every run.
Neither substitutes for a reviewer reading a diff to `baseline.json` as a claim that work was lost.

### The report on `main` today

**18 findings, and they are exactly the incident and its dependents:**

```
UNBACKED-BRANCH  T508 softhouse/T508-journalentry-insert-schema     UNBACKED-COMMIT T508 1abd3a11
UNBACKED-BRANCH  T509 softhouse/T509-ledgerguard-blindspot          UNBACKED-COMMIT T509 857dd4d8
UNBACKED-BRANCH  T510 softhouse/T510-savings-fold-reversal          UNBACKED-COMMIT T512 8ff5ff15
UNBACKED-BRANCH  T512 softhouse/T512-scope-instrument               UNBACKED-COMMIT T515 2e1a09df
UNBACKED-BRANCH  T515 softhouse/T515-savings-classification-rework  UNBACKED-COMMIT T515 5c4233fc
UNBACKED-BRANCH  T520 softhouse/T508-journalentry-insert-schema     UNBACKED-COMMIT T515 78a17873
UNBACKED-BRANCH  T522 softhouse/T515-savings-classification-rework  UNBACKED-COMMIT T515 84dc208e
UNBACKED-BRANCH  T523 softhouse/T509-ledgerguard-blindspot          UNBACKED-COMMIT T520 1abd3a11
                                                                    UNBACKED-COMMIT T522 84dc208e
                                                                    UNBACKED-COMMIT T523 857dd4d8
```

T520/T522/T523 are the review tasks whose *subject* is the lost work; the tool finding them is
correct, not noise. Full transcript: `.softhouse/capture/t527-branch-published/report-on-main.txt`.

**This tool is therefore RED on main and stays red.** The repair is the driver's and is one of two
things: push those branches to origin, or correct the notes to say the work is UNRECOVERED. Editing
the tool is not the repair, and I did not touch `tasks.json` (out of scope, and it is owned by the
live fire).

---

## 3. Where I wired it

**`.softhouse/bin/ready-tasks.py`, new function `branch_published_gate(out=…)`, called on the FIRST
line of `main()`** — above the ready list, the in-progress list and the gate section, i.e. exactly
where the 2026-09-03 fire would have seen it. `fire-program.sh` calls this file only with
`--reconcile`, which runs on the signal path with a clamped budget; the gate is **not** wired there
and `--reconcile` never returns 5. The reader this is for is the orchestrator agent at STEP 0/1,
which runs report mode (`.claude/skills/softhouse-program/SKILL.md:183` prescribes it).

* Report mode: the checker's whole output is printed first, then a `>>>`-prefixed instruction to the
  driver, then the normal report, then the verdict is **repeated at the bottom** (the top is ~650
  lines away by then) and `main()` returns the new exit code **5**.
* `--json` mode: the gate report goes to **stderr** so it cannot corrupt the document, and the
  verdict rides in the JSON as `"branch_published": "CLEAN" | "NOT_CLEAN"`; exit is 5 when not clean.
* **Fail closed at the wiring layer too:** a missing checker, a `subprocess` failure, a 180 s
  timeout, or an unrecognised exit code all print NOT CLEAN and return 5. A wrapper that swallows the
  code reproduces P-45 one layer out.
* `5` is documented in the module docstring's exit-code table, alongside a T527 paragraph.

---

## 4. Showing it run **through the caller**

`.softhouse/capture/t527-branch-published/drive-wiring.sh` — four cells, each reading
**`ready-tasks.py`'s own exit code**, never the checker's. Transcript at
`.softhouse/capture/t527-branch-published/wiring.txt`.

```
T527 wiring drive -- every verdict below is ready-tasks.py's own exit code.

A. the real record, real origin
  A-real-repo-refuses: PASS  (ready-tasks.py exit 5, saw "check-branch-published: REFUSE")
     findings named: 18            [the 18 lines above]

B. origin unreachable -- must be a DISTINCT refusal, never a pass
  B-unreachable-fails-closed: PASS  (ready-tasks.py exit 5, saw "CANNOT ESTABLISH ORIGIN")

C. a record whose one branch IS on origin -- the control that must PASS
  C-clean-record-passes: PASS  (ready-tasks.py exit 0, saw "check-branch-published: CLEAN")

D. the checker deleted -- the WIRING's own fail-closed arm
  D-missing-checker-is-not-a-pass: PASS  (ready-tasks.py exit 5, saw "checker is not on disk")

0 cell(s) failed.
```

Cell C is the one that makes A, B and D mean anything: the wiring **can** go green, so a red is
information. Cell D removes the checker from a fixture that was otherwise passing.

Head of the real run, as the driver will see it:

```
$ python3 .softhouse/bin/ready-tasks.py --repo .      # exit 5
==============================================================================
STEP 0 -- IS THE RECORD BACKED BY origin?  (T527, check-branch-published.py)
==============================================================================
==============================================================================
check-branch-published: REFUSE -- 18 claim(s) origin has never heard of
==============================================================================
origin: 47 branches, main=dd27570094fe | records checked: 468 terminal-or-awaiting-review tasks
backed: 42 branch(es) on origin, 73 pruned-but-proved-on-main, 98 commit(s) reachable from an origin ref
```

`--json`: stdout stayed valid JSON, `branch_published = NOT_CLEAN`, `ready = 61`, exit 5.

---

## 5. `--selftest` — 23 cases, 0 failures

Full transcript `.softhouse/capture/t527-branch-published/selftest.txt`. Each RED case is paired with
a control that **removes its subject** and must go GREEN, so the RED is attributable to the subject
and not to the fixture.

```
GREEN CONTROLS -- the check must be able to PASS:
  G-CLEAN-branch-on-origin                   PASS  (rc=0 want=0)
  G-PRUNED-MERGED-proved-ancestor            PASS  (rc=0 want=0)
  G-PRUNED-anti-vacuity-proof-removed        PASS  (rc=2 want=2)
  G-not-terminal-status-is-not-checked       PASS  (rc=0 want=0)

RED CASES -- each must go RED, and each is re-run with its subject REMOVED:
  R1-branch-absent-from-origin               PASS  (rc=2 want=2)
  R1-control-subject-removed                 PASS  (rc=0 want=0)
  R2-sha-does-not-resolve                    PASS  (rc=2 want=2)
  R2-control-sha-removed-from-note           PASS  (rc=0 want=0)
  R2b-sha-only-in-a-stack-clause             PASS  (rc=2 want=2)
  R2b-control-stack-clause-removed           PASS  (rc=0 want=0)
  R3-sha-resolves-but-on-no-origin-ref       PASS  (rc=2 want=2)
  R3-control-same-note-with-a-pushed-sha     PASS  (rc=0 want=0)
  R4-origin-unreachable-is-exit-3            PASS  (rc=3 want=3)
  R4-control-origin-restored                 PASS  (rc=0 want=0)
  R4b-unreachable-dominates-a-dirty-record   PASS  (rc=3 want=3)
  R5-merge-base-does-not-prove-a-branch      PASS  (rc=2 want=2)
  R5-control-same-sha-claimed-as-LANDING     PASS  (rc=0 want=0)
  R6-control-digest-context-is-not-a-claim   PASS  (rc=0 want=0)
  R6-anti-vacuity-same-hex-without-the-digest-word PASS  (rc=2 want=2)
  R7-tip-field-is-read                       PASS  (rc=2 want=2)
  R7-control-tip-field-holds-a-pushed-sha    PASS  (rc=0 want=0)

EXEMPTION CONTROLS -- the waivers must waive exactly what they claim to:
  B-baseline-waives-only-the-named-subject   PASS  (rc=2 want=2)

INCIDENT CONTROL -- the shipped baseline must not waive the defect it was generated beside:
  G-BASELINE-EXCLUDES-INCIDENT               PASS  (314 entries, incident tasks present: none)

23 case(s), 0 failure(s)
```

The four cases the brief asked for are `R1` (branch that does not exist), `R2`/`R2b` (sha that does
not resolve), `R3` (sha resolves, on no origin ref) and `R4`/`R4b` (origin unreachable, distinct exit
3 — `R4b` proves the unreachable verdict **dominates**: a record full of unbacked claims still exits
3, not 2 and never 0). The must-PASS case is `G-PRUNED-MERGED-proved-ancestor`, with
`G-PRUNED-anti-vacuity-proof-removed` proving the pass came from the ancestry proof and not from the
branch being visible.

---

## 6. What I did NOT do, and what a reviewer should attack

* **I did not repair the record.** T508/T509/T510/T512/T515 remain claimed-but-unbacked in
  `tasks.json`. It is out of my scope and owned by the live fire. **The guard is red on main and will
  be red on every fire until the driver acts.**
* **I did not recover the five commits.** They are on a laptop; nothing here can reach them.
* **The baseline is the attack surface.** 314 waivers, 9 of them commits. I generated it from the
  current state and hand-checked the exclusions; I did **not** individually verify that each of the
  305 waived branches really landed — I verified only that git preserves no proof either way. Read
  §2's baseline paragraph as the honest statement of that.
* **The commit extractor is a whitelist of phrasings.** 217 distinct hex tokens are printed as
  UNCLASSIFIED and are NOT checked. I classified a sample by hand (digests, tree hashes, Fineract
  ids, fire dates) and found no missed commit claim, but I did not classify all 217. Where I looked:
  the `note` field of every checked record, via the contexts printed in the report.
* **The `stack` region anchor is greedy** (up to 240 chars or the next `.`/newline). It is why
  `5c4233fc` is caught; it is also why the all-digit and digest vetoes had to be applied *inside*
  regions — without them it reported `20260829` (a fire id) and a 40-char tree hash as lost commits.
* **`git fetch` runs on every report-mode `ready-tasks.py`.** It is additive (no `--prune`), took
  ~2.7 s end to end here, but it is a network call in a path that previously made none.
* **I unshallowed the shared object store** (§1). Additive, but it is a side effect outside my four
  files.
* No Go, no money code, no vectors touched. `conformance.sh`, `.softhouse/guards/ledgerguard/` and
  `nexus/internal/apps/savings/` were **not** opened or edited, per the scope guard.

## 7. Files

| path | |
|---|---|
| `.softhouse/bin/check-branch-published.py` | new, 660 lines incl. `--selftest` |
| `.softhouse/bin/ready-tasks.py` | `branch_published_gate()`, call at top of `main()`, exit 5, docstring |
| `.softhouse/capture/t527-branch-published/baseline.json` | 314 enumerated waivers |
| `.softhouse/capture/t527-branch-published/drive-wiring.sh` | four-cell wiring drive |
| `.softhouse/capture/t527-branch-published/selftest.txt` | 23-case transcript |
| `.softhouse/capture/t527-branch-published/wiring.txt` | wiring transcript |
| `.softhouse/capture/t527-branch-published/report-on-main.txt` | the 18 findings, in full |
| `.softhouse/handoff/T527-branch-published-guard.md` | this file |

## 8. Proof this branch is published

The whole task is about branches that were never pushed, so this is the one claim that must not be
taken on trust.

```
$ git push -u origin softhouse/T527-branch-published-guard
To https://github.com/buya-v/gerege-nbfi
 * [new branch]        softhouse/T527-branch-published-guard -> softhouse/T527-branch-published-guard
branch 'softhouse/T527-branch-published-guard' set up to track 'origin/softhouse/T527-branch-published-guard'.

$ git ls-remote --heads origin refs/heads/softhouse/T527-branch-published-guard
48c96cd165efc1d3294d5776d09174dcbfb19858	refs/heads/softhouse/T527-branch-published-guard
```

`48c96cd1` is the commit carrying the guard, the wiring, the baseline and the transcripts. This
handoff's own §8 update is a second commit on the same branch; re-run the `ls-remote` above to see
its sha, and run `.softhouse/bin/check-branch-published.py` — T527 is not in the baseline and is not
in the findings, because its branch is on origin.
