# T536 — T528's five conditions on T527's branch-published guard

Branch: `softhouse/T536-t528-conditions`. Files touched: `.softhouse/bin/check-branch-published.py`,
`.softhouse/bin/ready-tasks.py`, `.softhouse/capture/t527-branch-published/`, this handoff.
Nothing else — `conformance.sh`, `.softhouse/guards/ledgerguard/`, `nexus/internal/apps/savings/`,
`tasks.json`, `LOCK`, `RESUME.md`, `program.json` are untouched (`git show --stat` on the
commits below is the proof, and §9 re-states it).

**The record is still broken and this tool still refuses.** `check-branch-published.py`
exits 2 on `main`; `ready-tasks.py` exits 5. All 21 of the genuine findings survive —
none disappeared, and the count went UP, to 31. Making it green was never the job.

---

## 1. The two numbers, re-measured here, with the commands

Both tools run back to back against the same `origin` state (`origin/main = c2127db33b76`),
so the comparison is not against a remembered figure:

```
$ git show HEAD:.softhouse/bin/check-branch-published.py > /tmp/old-cb.py   # T527, as shipped
$ python3 /tmp/old-cb.py --repo /home/user/wt/T536 --json > m-old.json      # exit 2
$ python3 .softhouse/bin/check-branch-published.py --repo /home/user/wt/T536 --json > m-new.json
                                                                            # exit 2
$ python3 - <<'PY'   # set-compare PRUNED-PROVED waivers and findings
  P = {(w['task'], w['branch']) for w in d['waived'] if w['kind'] == 'PRUNED-PROVED'}
  F = {(f['kind'], f['task'], f['subject']) for f in d['findings']}
PY
```

| | measured |
|---|---|
| **Legitimate merged-and-pruned waivers retained** | **66 of 73** |
| **Probe breaks closed** (`probes/attack.py`, 12 cases) | **7 of 7** |
| genuine findings that survived | **21 of 21** — `F(old) - F(new)` is empty |
| findings total | 21 → **31** (7 newly-red branches + 3 newly-detected commit claims) |

T528 sized the fix at 66/73 and 6/7. I hit **66/73 and 7/7**: the seventh break, case L
(`supersedes the work merged as X by T400`), closes because condition 1 asked for a
**trailing** arm on the different-task veto and I built one. **There is no 7th break I
failed to close.** What I do owe honestly is §5, the seven waivers that turned red, and
§8, what this guard still cannot see at all.

---

## 2. BEFORE and AFTER probe transcripts

Committed in full under `.softhouse/capture/t527-branch-published/`:
`t536-attack-{before,after}.txt`, `t536-incident2-{before,after}.txt`,
`t536-failclosed-{before,after}.txt`, `t536-fc2-{before,after}.txt`,
`t536-reword-before.txt` / `t536-reword.txt`, `t536-incident3.txt`, `t536-selftest.txt`,
`t536-wiring.txt`, `t536-report-on-main.txt`.

### `probes/attack.py` — the classifier

```
$ python3 .softhouse/reviews/t528-review-t527/probes/attack.py \
      .softhouse/bin/check-branch-published.py
```

| case | note | BEFORE | AFTER | want |
|---|---|---|---|---|
| A | `done and scope-checked (merge base X)` | 2 | 2 | 2 |
| **B** | `done; merge-base commit X, scope clean` | **0 BREAK** | **2** | 2 |
| **C** | `branched from main @ X; work is on the branch` | **0 BREAK** | **2** | 2 |
| D | `forked at X, 3 commits on top` | 2 | 2 | 2 |
| **E** | `based on softhouse/TP-pushed (X) -- stacked on top` | **0 BREAK** | **2** | 2 |
| F | `rebased onto X after the merge of T400` | 2 | 2 | 2 |
| **G** | `reviewed T400 which landed X; my own work is on the branch` | **0 BREAK** | **2** | 2 |
| **H** | `diverges from origin/main at commit X` | **0 BREAK** | **2** | 2 |
| I | `landed X on softhouse/TN-never-pushed` | 0 | 0 | 0 — legitimate, must PASS |
| J | `cherry-picked from X` | 2 | 2 | 2 |
| **K** | `stack X (T400 base) -> my work` | **0 BREAK** | **2** | 2 |
| **L** | `supersedes the work merged as X by T400` | **0 BREAK** | **2** | 2 |
| | | **7 break(s)** | **0 break(s)** | |

### `probes/incident2.py` — laundering a fresh incident

```
BEFORE                                    AFTER
1. before any baseline    -> exit 2       1. -> exit 2 (same two findings)
2. --write-baseline       -> exit 0       2. wrote 0 waiver(s); REFUSED TO WAIVE 2:
     WAIVE UNBACKED-COMMIT T540 deadbe1f       KEEP UNBACKED-COMMIT T540 deadbe1f
     WAIVE UNBACKED-BRANCH T540 ...            "above the freeze line T527 -- this is a
     REFUSED TO WAIVE 0 finding(s) ...          claim from AFTER the control existed, so
3. re-run                 -> exit 0 CLEAN      it is a live incident, not history"
   INCIDENT #2 IS NOW LAUNDERED           3. re-run -> exit 2
                                             INCIDENT #2 IS NOW still refused
5. lowercase `t508`:                      5. lowercase `t508`:
     WAIVED: [UNBACKED-BRANCH t508 ...]        WAIVED: []
     KEPT  : [UNBACKED-COMMIT t508 ...]        KEPT  : both, "2026-09-04 incident task"
```

Both of T528's condition-3 checkables now hold.

### The driver's own F-1 reproduction — rewording T509's note

`t536-reword.py` runs the **real record** twice, in memory, without touching
`tasks.json`: once as written, once with `(merge base 10baca08)` → `(merge-base commit
10baca08)` — the driver's one-word edit. It prints the number of substitutions it actually
applied, so it cannot pass vacuously.

```
BEFORE (T527 as shipped, t536-reword-before.txt):
  as written : 21 finding(s); UNBACKED-BRANCH T509 present: True
  one word   : 20 finding(s); UNBACKED-BRANCH T509 present: False
  substitutions applied: 1
  silenced by the reword: [('UNBACKED-BRANCH','T509','softhouse/T509-ledgerguard-blindspot')]

AFTER (t536-reword.txt):
  as written : 31 finding(s); UNBACKED-BRANCH T509 present: True
  one word   : 31 finding(s); UNBACKED-BRANCH T509 present: True
  substitutions applied: 1
  IDENTICAL: the reword silences nothing.
```

---

## 3. F-1 — I inverted the default. What it cost.

**Yes, the default is inverted, and that is the substance of this task.** T527's table was
`(role, pattern)` pairs with two `REFERENCE` entries and everything else — including the
whole `stack …` region — `LANDING`. That is a blocklist of phrasings, and a blocklist of
phrasings closes the phrasings someone thought of. T527's R5 closed one. This is the third
repair in a row on the same hole, so closing one more phrasing was not an acceptable
outcome.

Extraction and proof are now two different questions:

* `CLAIM_ANCHORS` / `CLAIM_REGIONS` carry **no role at all**. They decide only whether a
  hex token is a **commit claim** — i.e. must exist and be reachable from an origin ref.
  Every extracted sha starts `REFERENCE`.
* `LANDING_PROMOTIONS` (4 patterns) and `LANDING_BINDINGS` (2) are the **only** route to
  `LANDING`, and both are subject to two **dominant** vetoes.

The property that matters: **a new extraction anchor added tomorrow inherits `REFERENCE`
and therefore cannot silently clear a missing branch.** Under T527 the documented growth
path ("adding an anchor is a one-line change") added a *LANDING* anchor by default — the
growth path itself was the hole. I added two anchors under this rule (`head X`, `hiding X`,
from T528 F-4) and they could not have caused a false waiver even if I had got them wrong.

Promotions (measured against the real record; these four carry all 66 surviving waivers):
`landed X` · `merged as|at|commit X` · `tip [is] X` ·
`(COMPLETE|COMPLETED|DONE|MERGED|LANDED|DELIVERED|APPROVED) … @ X`. A **bare** `@ X` now
extracts but does not promote, because `branched from main @ X` is that shape (case C).

Bindings (prove ONE branch, never the task): `landed X on <branch>` · `<branch> (X)`.
A bound span is excluded from the unbound pass, or F-2 would reopen through the very
phrase that names the branch.

Vetoes, both dominant over any promotion:

* **V** — a base-citation word (`merge base|based on|branched from|forked|diverges|
  rebased onto|cherry-picked|ahead of|behind|hiding|head|supersedes|cut from|stacked on|
  on top of`) in the left context.
* **V2** — a **different** task id beside the sha. Leading arm (case G) and trailing arm
  (case L). The task's own claimed branch names are masked out first, because the `T476`
  inside `softhouse/T476-t472-repair` is this task speaking, not another task.

**Two precision rules I had to add that T528's sizing did not contain**, both found by
measuring rather than reasoning — my first cut scored **62 of 73**, not 66:

1. **The veto gap must not step over another sha.** `6 commits on top of T466 11afb281,
   tip a6bf50a3` — `on top of` describes `11afb281`, not `a6bf50a3`, and a 40-char window
   that reaches across `11afb281` cost T477 its own legitimate waiver. `_veto_gap()` now
   refuses a window containing another hex token, a `.` or a newline.
2. **The trailing V2 arm is narrower than the leading one.** A task id that merely
   *follows* a sha is usually a co-actor: `MERGED at 01a7a05a with T382` is T374's own
   merge commit landed alongside T382, and a bare trailing arm cost that waiver for
   nothing. Only an **attribution** preposition (`by|for|from|belonging to|owned by`)
   transfers ownership — which is exactly case L's shape, `merged as X by T400`.

Regression control: the seven attack notes are now `--selftest` cases
`A5b-B…A5b-L`, each paired with `A5b-GREEN-genuine-landing` and three more GREEN cases
covering the phrasings the pipeline actually writes (`MERGED at X by fire …`,
`COMPLETE @ X`, `tip X`), plus four more (`A5b-ii-*`) driving T536's own two residual
rules in both directions — see §10. Selftest: **23 cases → 44 cases, 0 failures**, run
three times consecutively to prove it is not flaky.

One thing I had to fix to make that claim true: `_fixture` now retries until none of its
four short shas is **all digits**. A hex short sha is all-digit about 2.3% of the time and
this tool vetoes all-digit tokens on purpose (`20260829` is its own fire-id format), so a
GREEN case whose proving sha landed all-digit failed for a reason unrelated to what it
tested. A control that fails at random teaches its next reader to re-run it, which is how
a control stops being one.

---

## 4. F-2 — the proof is scoped to the branch

`proved_on_main` (a list, applied to every branch the task named) is replaced by two
structures: `proved_bound` (branch → sha, populated only by a phrase that names both) and
`proved_task_wide` (unbound landings, which may waive **only** a branch the task names in
its own `branch`/`branch_mac`/`branch_cloud` field).

T528's two named checkables:

```
$ python3 .softhouse/bin/check-branch-published.py --json | ...
  UNBACKED-BRANCH  T476  softhouse/T467-t464-conditions
      ... this task's landing sha 36e01f25 proves only the branch(es) it names in a
      branch field, not this one (T536/F-2)
  UNBACKED-BRANCH  T477  softhouse/T466-skipwt-smudge
      ... this task's landing sha a6bf50a3 proves only the branch(es) ... (T536/F-2)
```

T476 no longer waives T467's branch; T477 no longer waives T466's. Selftest case
`A5c-two-branches-one-landing-waives-exactly-one` asserts the shape, with
`A5c-control-the-landing-branch-alone-is-CLEAN` as its paired green.

## 5. The seven waivers that turned red — each one, and why it is correct

The condition says the newly-red branches must be **enumerated rather than baselined
blind**. None of the seven is in `baseline.json` (checked: no key for T353/T357/T358/
T361/T375/T476/T477), so all seven are printed as findings on every run.

| task | branch | what was "proving" it under T527 |
|---|---|---|
| T353 | `T353-t342-conditions` | `head 539a7201 (branched from T342 @ d870db1d)` — **d870db1d is T342's base.** A base citation, and another task's commit. |
| T357 | `T357-a2-11-section1-red` | `APPROVED by T362 @ 1f90ee76` — **T362's** review commit. |
| T358 | `T358-t323-conditions` | `ACCEPT-WITH-CONDITIONS by T364 @ 137f6e15` — **T364's** commit. |
| T361 | `T361-review-t353` | `sha256(fire-program.sh @ 539a7201)` — a sha inside a **digest expression**, which happens also to be T353's head. |
| T375 | `rescued-agent-ac5a2db…` | a **second** branch; T375's landing sha proves its own branch field only (F-2). |
| T476 | `T467-t464-conditions` | **T467's** branch, cleared by T476's commit (F-2, named in the review). |
| T477 | `T466-skipwt-smudge` | **T466's** branch, cleared by T477's commit (F-2, named in the review). |

Four of the seven were cross-task proofs and one was a digest. They are not a cost of the
fix so much as five more instances of the defect, previously counted as waivers.

Three findings are also **gained** on the commit arm, and they are T528 F-4's three by
name — `d09585f58` (T335), `c1a3888a` and `060f00330` (T312). I added `head X` / `hiding X`
extraction anchors, so they are no longer sitting silently in the NOT-CHECKED bucket.
All three are claims about branches that are not on origin, which is exactly what this
tool exists to find.

---

## 6. F-3 — the baseline is frozen by generation, and here is the fresh incident

`baseline.json` gains `frozen_above: "T527"`; `check-branch-published.py` gains
`FROZEN_ABOVE = "T527"` as the fallback. `--write-baseline` refuses any finding whose task
id sorts above the line, **or whose id it cannot date at all**. `INCIDENT_TASKS` /
`INCIDENT_SHAS` comparisons are case-folded. The freeze line is printed on every run and
at the top of every `--write-baseline`.

The reassuring line is gone: `REFUSED TO WAIVE 0 finding(s) — these are the 2026-09-04
incident and no regeneration may launder them` no longer prints over a run that laundered
something. Zero refusals now says, in as many words, that it is a statement about **this
run** and not an assurance.

**The fresh synthetic incident, in no blocklist** —
`.softhouse/capture/t527-branch-published/t536-incident3.py`, transcript
`t536-incident3.txt`. T528's probe used `T540`, which is now named in a review, a handoff
and this program's prose; a fix that special-cased it would have scored green. This uses
**`T791`**, which appears in no blocklist, no review and no baseline:

```
INCIDENT #3 -- a task id in no blocklist, no review and no baseline (T791)
  1. fresh incident refused before any baseline         PASS exit 2
       UNBACKED-BRANCH T791 softhouse/T791-lost-critical-path
       UNBACKED-COMMIT T791 c0ffee11
     FREEZE LINE: T527 (from module constant).
     KEEP UNBACKED-COMMIT T791 c0ffee11  above the freeze line T527 -- this is a claim
          from AFTER the control existed, so it is a live incident, not history
  2. --write-baseline REFUSES to waive it               PASS waived=0 kept=2
  3. re-run after the regeneration is STILL red         PASS exit 2
  4. the baseline file contains no T791 key             PASS 0 key(s) total
  5. deleting baseline.json does not lift the freeze line  PASS waived=0, re-run exit 2
  6. lowercase `t508` is KEPT, not WAIVED               PASS waived=0 kept=2
  7. ANTI-VACUITY: a HISTORICAL id (T42) is still waivable PASS waived=1, re-run exit 0
  0 cell(s) failed.
```

Cell 5 is the one that is not in T528's sizing and I judge load-bearing: if the freeze line
lived **only** in `baseline.json`, `rm baseline.json && --write-baseline` would reset it,
which is a one-command laundering route. It falls back to the module constant instead.
Cell 7 is the anti-vacuity control — a freeze that refuses everything is a broken tool, not
a frozen one, so a historical id must still be waivable. Selftest adds the same four cells
(`F-above-the-line-is-REFUSED`, `F-below-the-line-is-waivable`,
`F-undatable-id-is-REFUSED`, `F-case-folded-incident-id-is-REFUSED`).

---

## 7. The MINORs

* **F-5 (condition 4) — the wiring now reads the answer, not just the exit code.**
  `branch_published_gate()` requires `check-branch-published: CLEAN` in the checker's
  stdout before believing `returncode == 0`. `probes/fc2.py` cell I2 (a two-line
  `sys.exit(0)` stub over a dirty record): **`ready-tasks.py` 0 → 5.** `drive-wiring.sh`
  gains cell **E**, which replaces the checker with that stub over a record whose branch
  was never pushed — so the only way the cell can go green is the stub being believed.
* **F-6 — the `:519` comment.** `# --- commit arm. Never baselined` said the opposite of
  what the code does (`baseline.json` carries 9 `UNBACKED-COMMIT` entries: T122, T329,
  T351 ×2, T369, T370, T472, T473, T474). Replaced with the truth and the reason it
  matters.
* **F-10 — the deepen/fetch is announced.** `establish_origin()` takes an `announce`
  callback; every write it performs prints in the report (`WROTE: git fetch origin
  +refs/heads/* … additive, no --prune`, and the `--unshallow` line when it fires) and
  rides in `--json` as `writes`.
* **F-4 / §7 correction.** T527's handoff says "I classified a sample by hand … and found
  no missed commit claim". **That sentence is wrong.** The counter-examples are
  `d09585f58` (T335, an unpushed branch HEAD), `c1a3888a` and `060f00330` (T312, two
  unpushed shadow heads). All three now produce findings.
* **§7 second correction.** T527's "the tool now tags each anchor LANDING or REFERENCE;
  only LANDING can prove" was true as written but presented as if the class were closed.
  It was not: seven paraphrases read as LANDING, one of them a one-word variant of T508's
  own note. §3 above is the replacement claim, and it is a claim about a **default**, not
  about a list.

**Debt T528 recorded and I closed anyway** (all three are cheap and none changes a
verdict): **F-7** — a malformed *current* `tasks.json` exited 1 with a traceback; it now
exits **5**, the code the table documents (`failclosed.py` cell E: FAIL exit 1 → PASS exit
5). **F-8** — the `--json` exit-3 arm put prose on stdout and JSON on stderr; they are now
the same way round as every other arm. **F-9** — the report printed all 314 baseline
waivers on every run; it now prints 12, the count, and a pointer to the committed file,
with `--full-baseline` to restore the enumeration. On the real repo: **684 lines → 406,
READY list at line 306 instead of 587.**

I did **not** touch `SKILL.md`'s silence on exit 5 (F-9's second half): `.claude/skills/`
is outside this task's declared file scope.

---

## 8. WIRED, and driven through the caller

```
$ python3 .softhouse/bin/ready-tasks.py
==============================================================================
STEP 0 -- IS THE RECORD BACKED BY origin?  (T527, check-branch-published.py)
==============================================================================
check-branch-published: REFUSE -- 31 claim(s) origin has never heard of
origin: 54 branches, main=c2127db33b76 | records checked: 475 terminal-or-awaiting-review
backed: 49 branch(es) on origin, 66 pruned-but-proved-on-main, 124 commit(s) reachable
baseline freeze line: T527 (from baseline.json) -- a claim from a LATER generation
                      cannot be baselined.
  WROTE: `git fetch origin +refs/heads/*:refs/remotes/origin/*` -- additive, no --prune.
...
  IN PROGRESS (2) at line 289 | READY (64) at line 306 | BLOCKED (15) at line 378
==============================================================================
STEP 0 VERDICT: NOT CLEAN -- check-branch-published.py did not say CLEAN.
==============================================================================
$ echo $?
5
```

### The ten fail-closed arms, re-run

`probes/failclosed.py` + `probes/fc2.py` + `drive-wiring.sh`. Every cell reads
**`ready-tasks.py`'s own** exit code except J/K/L, which drive the checker directly.

| # | injury | T527 | T536 |
|---|---|---|---|
| 1 | control: uninjured clean fixture | 0 | **0** — the control that can PASS |
| 2 | `git` hangs (PATH shim sleeping past `--timeout 3`) | 3 | **3** |
| 3 | `ls-remote` exits 0 with garbage on stdout | 3 | **3** `ORIGIN LISTED NO BRANCHES` |
| 4 | `ls-remote` exits 0 with a partial ref set (main only) | 2 | **2** — loud, never a pass |
| 5 | archive `runs/*.tasks.json` unparseable (fc2 F2) | 5 | **5** |
| 6 | archive with no `tasks` list (fc2 F3) | 5 | **5** |
| 7 | malformed `baseline.json` | 5 | **5** |
| 8 | checker raises **mid-run**, injected inside `check()` (fc2 H2) | 5 | **5** |
| 9 | checker **deleted** (wiring cell D) | 5 | **5** |
| 10 | checker **replaced** by a silent `sys.exit(0)` stub, dirty record | **0** ← the hole | **5** |
| + | malformed *current* `tasks.json` (F-7) | **1 + traceback** | **5** |
| + | `--json` stays parseable, `branch_published=NOT_CLEAN` | 5 | **5** |

Nine of ten fail-closed under T527; **ten of ten now**. `probes/failclosed.py` still
reports its cells F and H as FAIL — those two are the test-design errors T528 documents
and rebuilt (`chmod 000` does nothing as root; a `raise` after `SystemExit` never runs);
the rebuilt forms are fc2's F2/F3/H2 above and all pass.

`drive-wiring.sh`: **5 cells, 0 failed** (A real repo → 5 REFUSE, 31 findings named;
B origin unreachable → 5; C clean record → 0 CLEAN; D checker deleted → 5; **E silent stub
→ 5**).

### What this guard still cannot see — stated because "not found" is a statement about the search

I looked for the residual by re-running the `UNCLASSIFIED-HEX` bucket after adding the two
F-4 anchors, and by reading `check()`'s two arms. Two blind spots remain, both now written
into the module docstring rather than left implicit:

1. **A task that claims nothing loses nothing, as far as this tool can tell.** Both arms
   are driven by what the record *says*. A terminal task with no branch field and a note
   naming neither a branch nor a sha is invisible to the branch arm and the commit arm
   alike. The `UNCLASSIFIED-HEX` count measures the part of the blind spot that has hex in
   it; silence in the record is the part that has nothing to count.
2. **A promotion phrasing nobody has written yet is REFERENCE, so a genuine landing in a
   novel phrasing becomes a false finding, not a false pass.** That is the correct
   direction for this error, and it is the price of the inversion: the tool now errs
   toward refusing, and the repair for a false finding is to add a promotion pattern in a
   diff a reviewer reads.

---

## 9. Scope and the non-negotiables

`git show --stat` on both commits: six files, all under `.softhouse/`
(`bin/check-branch-published.py`, `bin/ready-tasks.py`,
`capture/t527-branch-published/**`, `handoff/T536-t528-conditions.md`). **Not touched:**
`conformance.sh`, `.softhouse/guards/ledgerguard/`, `nexus/`, `.softhouse/tasks.json`,
`.softhouse/LOCK`, `.softhouse/RESUME.md`, `.softhouse/program.json`.

No monetary code path in this diff. The only `float(` in either tool is `--timeout`
parsing, which is a duration, not money — `grep -n 'float\|Decimal\|/ 100\|\* 100'` over
the diff returns that one line. No `first_name`/`last_name`, no hard-coded timezone
offset, no MySQL/MariaDB/Oracle driver or dialect, no US rails or vendors, no
deposit-insurance language. Nothing here goes near Go, the schema, or a vector.

## 10. What a reviewer should attack first

1. **The promotion list is now the whole trust boundary.** Four unbound patterns and two
   bindings decide every waiver. `APPROVED` in the `@` verb list is the one I added beyond
   T528's measured set (it recovers T387, and the case is `APPROVED WITH CONDITIONS @
   026954a4`, this pipeline's own voice). If that verb is wrong, it is wrong in the
   fail-open direction. I drove the obvious attack rather than reasoning about it —
   `APPROVED T400's work @ <base sha>` REFUSES (V2's leading arm), and it is now the
   permanent selftest case `A5b-ii-APPROVED-carrying-another-task`, paired with
   `A5b-ii-GREEN-APPROVED-own-work`. What I have **not** enumerated is every verb×veto
   combination; six verbs times two vetoes is a bigger surface than four cases.
2. **`_veto_gap()`'s "another sha in the gap" rule.** It is what recovered T477 and T374,
   and it is a heuristic: `based on <base>, tip <own>` deliberately promotes the second
   sha, and that is selftest `A5b-ii-GREEN-base-sha-then-own-tip`, with
   `A5b-ii-base-word-adjacent-still-vetoes` as its RED pair. The residual risk is a note
   that names a base sha and then a *genuinely unrelated* sha inside 40 characters. I
   searched the real record for that shape — the seven surviving base-citation contexts
   are all in §5's table and none has it — but I did not prove one cannot exist.
3. **`frozen_above` is enforced against `--write-baseline` only.** A human editing
   `baseline.json` by hand still waives anything; the freeze makes the laundering *visible*
   in a diff, it does not make it impossible. T528's own framing, and I have not improved
   on it.
4. **Seven waivers turned red and I argue all seven were wrong before.** §5 is the
   argument; the notes are quoted there and re-readable in `tasks.json`. If any of the
   seven is a genuine landing I have mis-scored, it becomes a false finding in a report
   that is already red, which is noise on top of a refusal rather than a silenced claim.

---

## 11. Branch proof — this handoff's own subject matter, applied to itself

This program has lost five completed tasks to unpushed branches, and this task exists
because of a guard built to catch exactly that. So the claim is not made in prose:

```
$ git push -u origin softhouse/T536-t528-conditions
 * [new branch]        softhouse/T536-t528-conditions -> softhouse/T536-t528-conditions

$ git ls-remote --heads origin softhouse/T536-t528-conditions
6a37b7b273e02df25cc8f777501c81acd99b3552	refs/heads/softhouse/T536-t528-conditions
```

`6a37b7b2` is the commit carrying the work; this final commit appends the proof block, so
the tip moves past it. The `ls-remote` above is the claim and it is re-runnable — which is
the same standard `check-branch-published.py` holds every other task to, and the reason
`landed <sha> on <branch>` in a note is not, and was never, evidence.
