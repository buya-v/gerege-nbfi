# T462 — T456's conditions on T451

Branch `softhouse/T462-wallclock-refusal`. Scope: `.softhouse/bin/ready-tasks.py` and
`.softhouse/capture/t462-t456-conditions/`. Everything below was **re-derived on this
tree with my own fixture and my own instruments**; T456's numbers were read as a claim
to be re-measured, never as an input.

---

## C-T456-1 (MAJOR) — CONFIRMED, then fixed, then driven both ways

### What I measured, before touching a line

Method copied from T456 because it is the thing that makes the drive credible: **the
HOST is slowed, not the code.** A shell wrapper on the module's `GIT` sleeps before
exec'ing the real git, the instrument proves the wrapper actually slept before believing
any verdict taken through it, and the predicate under test is byte-identical to main's.

My fixture is my own (`bin/10-fixture.sh`, five cases) and adds two things T456's did
not have:

* **F2S** — the same evidence with the task branch **STANDING** at the dispatch commit,
  i.e. the `stillborn-carried` arm. T456 drove only `_absent_verdict`. Both callers of
  `refs_carrying_content` are affected and only one had ever been driven.
* **F9** — fan-out **9** with the only carrier ninth. A fixture whose largest fan-out is
  2 cannot tell a floor of 8 from a floor of 1000, and it cannot show what T451's change
  was *for*.

A third variant is the control T456 did not have: **CAP8**, the pre-T451 count cap
rebuilt from main's own bytes by a transform (`MAX_REFS_PROBED` 512→8, clock arm
disabled) whose liveness the instrument asserts before reporting.

**RED baseline — `out/11-RED-baseline.txt`, sleep 3.2 s/git call, exit 1:**

| case | shape | CAP8 (fast) | RED (fast) | CAP8 (SLOW) | RED (SLOW) |
|---|---|---|---|---|---|
| F2 | fan-out 2, carrier 2nd, branch PRUNED | REFUSE `relocated` | REFUSE `relocated` | **REFUSE** `relocated` 26.7 s | **demote** `indeterminate` 19.8 s |
| F2S | fan-out 2, carrier 2nd, branch STANDING | REFUSE `stillborn-carried` | REFUSE | **REFUSE** `stillborn-carried` 23.2 s | **demote** `indeterminate` 16.6 s |
| F9 | fan-out 9, carrier 9th, branch PRUNED | **demote** `indeterminate` | **REFUSE** `relocated` | demote (8 probed) | demote (1 probed) |
| F1 | fan-out 1, carrier 1st (must-REFUSE control) | REFUSE | REFUSE | REFUSE | REFUSE |
| N | fan-out 2, no carrier (must-DEMOTE control) | demote | demote | demote | demote |

Probe counts on the SLOW host, RED: **1** on every case. The bound truncated a **fan-out
of two** after a single git call, because `ref_content_evidence` makes two calls per ref
and 2 × 3.2 s already exceeds the 6.0 s ceiling. **The finding reproduces, independently,
and it reproduces on the arm T456 never drove.**

F9 on a **fast** host is the other half and it decides the shape of the fix: **CAP8
demotes where RED refuses.** T451's fail-open is real. A revert reinstates it. So the fix
cannot be "put the count cap back".

### The fix I derived, and the exact guarantee it buys

`MIN_REFS_ALWAYS_PROBED = 8`, as the **first conjunct** of the clock arm:

```python
elif (i >= MIN_REFS_ALWAYS_PROBED
        and time.monotonic() - started > REF_PROBE_SECONDS):
```

I **CONFIRM** T456's proposal, and I state the guarantee smaller than T456 stated it,
because that is the size that is provable:

> the set of refs this probe leaves UNPROBED is a **subset** of the set the count cap it
> replaced would have left unprobed, on every host and every budget.

Proof, and it is short: for `i < 8` neither bound truncates, so both probe unless `_run`
itself returns `rc=None` — which the count cap suffered identically, since the
`--deadline-secs` clamp lives in `_run` and predates both. For `i >= 8` the count cap
**always** truncated while this may not. Subset of the truncated set ⇒ no verdict can
move REFUSE→demote for want of a probe the old bound would have made.

It does **not** say the clock can never destroy work. F9 is the counter-example and it is
in the fixture on purpose.

### GREEN drive — `out/12-GREEN-drive.txt`, exit 0, three PASS legs

| case | CAP8 SLOW | RED SLOW | GREEN SLOW |
|---|---|---|---|
| F2 | REFUSE (2 probed) | demote (1) | **REFUSE (2)** 27.0 s |
| F2S | REFUSE (2) | demote (1) | **REFUSE (2)** 23.3 s |
| F9 | demote (8) | demote (1) | demote (**8**) 56.9 s |
| F1 | REFUSE (1) | REFUSE (1) | REFUSE (1) |
| N | demote (2) | demote (1) | demote (2) |

* **LEG 1, fast host** — GREEN's kind and polarity are identical to RED on all 5 cases,
  and every variant matches the expectation written down *before* the run. Clean-host
  behaviour unchanged. Corroborated end-to-end on the live repo: `out/60-readylist-RED-
  vs-GREEN.diff` is 16 lines over a 97-line report and **every one of them is the
  C-T456-5 sentence rewrite**; the verdict-kind census is identical
  (`out/62-readylist-census.txt`).
* **LEG 2, slow host** — no case where CAP8 refuses and GREEN demotes.
* **SUBSET** — GREEN's probe count ≥ CAP8's on every case and both hosts, 10/10.

### The `timeout=15` half of C-T456-1 — a derived REFUSAL to change it

T456's sharpest form is right: `ref_content_evidence`'s per-call `timeout=15` is 2.5×
the whole probe's 6.0 s ceiling, so one call can blow the budget by itself. I did **not**
tighten it, and this is a conclusion, not an omission:

**Every second cut off that timeout converts a slow-but-successful probe into `rc=None`,
which lands the ref in `unprobed`, which DEMOTES.** Tightening it breaks the subset
guarantee *in the destructive direction* — it would make this probe do LESS than the
count cap did, not more. The correct lever is `--deadline-secs`, which is a genuine
resource bound, is enforced inside `_run` for every call, and is the caller's to set.

The cost of the floor is real and is written into the code rather than hidden: on the
**unbudgeted** path the worst case rises from roughly one ceiling plus one hung call to
`MIN_REFS_ALWAYS_PROBED` hung calls. Measured shape of that cost in the transcript: F9 on
the slow host is 56.9 s for GREEN vs 9.9 s for RED.

---

## C-T456-2 (MINOR, methodological) — CONFIRMED and repaired at a new instrument

T451's five criteria — every state has a verdict, no state has two *disagreeing*
verdicts, the arm transcription agrees with `reconcile_action`, the T312 suffixes do not
change a polarity, nothing raises — are **all** properties of the verdict SPACE. None is
a property of the ROUTING. A defect that re-routes a state from one well-formed kind to
another is invisible to all five **by construction**, and T451's D1/D2/D3 all broke
well-formedness, so "3 planted, 3 caught" was a self-selected population.

I could not edit T451's instrument (out of scope) so I wrote
`bin/50-expected-verdicts.py`, which **says this in its own docstring** and adds two
arms. `out/50-expected-verdicts.txt`, exit 0:

| plant | ARM A (per-state expected kind) | destructive | ARM B (table-free invariants) | ARM C (T451's five) |
|---|---|---|---|---|
| clean | green | green | green | green |
| **D4** — T456's arm swap in `_branch_wip_core` | **RED, 2 states** | **2** | **RED, 2** | green |
| **D5** — mine: `relocated` arm deleted from `_absent_verdict` | **RED, 8 states** | **8** | **RED, 8** | green |
| **D-NULL** — negative control | green | green | green | green |

* **ARM A** is a per-state expected-kind table transcribed from the **docstrings**, and
  it is honest that a transcription can be edited into agreement with a defect. On the
  shipped tree it disagrees with the code on **0 of 288** states.
* **ARM B** is the one that matters: three table-free polarity invariants, each from a
  recorded incident — *B1 carriers present ⇒ never demote* (C-T449-1), *B2 work on main
  ⇒ never demote* (T324/T319), *B3 all probes ran and found nothing ⇒ MUST demote*
  (T330). B1 catches D4 with no table at all. An invariant that cannot be edited into
  agreement with the code is worth more than a table that can.
* **D5 is mine and it is in the caller D4 does not touch**, so the population is no
  longer one reviewer's single shape.
* **D-NULL is the other half of the fix to a self-selected population**: a real edit to
  the same routing region (the two unconditional probe calls at the top of
  `_absent_verdict`, swapped) that is behaviour-preserving. It stays green on every arm.
  An instrument that reddens there is crying wolf and its greens mean nothing either.
  **3 planted (2 defects, 1 non-defect), 2 caught, 1 correctly ignored.**

**ARM B is scoped, and the scoping is declared:** the invariants are asserted only on the
**72 of 288** states whose branch coordinate actually consults the evidence (`absent`,
`zero-ancestor`). In the other 216 `_branch_wip_core` returns before either probe runs,
so the LANDED/REFS coordinates are cross-product artefacts the real function never saw —
T449's own correction, which T451 recorded and applied to its stubs. Unscoped, ARM B
reported 204 "violations", every one of them a fact about my staging. That intermediate
result is why the restriction is printed with a count rather than asserted.

**And note what the enumeration says about my own MAJOR fix: nothing.**
`out/52-t456-direction-rerun.txt` reports **0 polarity transitions of any kind** between
RED and GREEN over all 288 states, and `out/51-t451-partition-rerun.txt` is green on
both. The enumeration stubs `refs_carrying_content`, so the entire
`MIN_REFS_ALWAYS_PROBED` change is invisible to it. The evidence for C-T456-1 is the
slow-host drive, and nothing else could have been.

---

## C-T456-3 (MINOR) — CONFIRMED; citation replaced with evidence that supports it

The shipped docstring cited `t451-t449-conditions/out/22-liveness.txt` for "the ref arm
is unreachable for all of them today". That artefact's own last line is `non-terminal ids
blocked by a FOREIGN-owned ref today: 4`, with four `<== LIVE FOREIGN-REF REFUSAL` rows.
A reader following the citation finds the opposite of the sentence carrying it.

The sentence can still be true, and it is — but only via a question that artefact never
asked. **Reachability is decided by the KIND `branch_wip` returns, not by the status.**
`bin/21-liveness.py` calls `branch_wip` for every (id, foreign-ref) pair on the live repo
(`out/21-liveness.txt`, measured at `3f4e236ad458`, 707 live refs, 356 tasks, 61 ids with
a foreign ref naming them):

> **member set — non-terminal ids where a foreign ref actually buys a REFUSAL today
> (ref arm REACHED **and** polarity REFUSE **and** still runnable) = `{ }`.**

The two non-terminal ids with foreign refs are the tree, not a count:

| id | status | recorded branch | kind | foreign refs |
|---|---|---|---|---|
| T268 | `needs_retry` | `softhouse/t268-rvpa-failopen` | `commits` → demote | `softhouse/t281-review-t268` (T281), `softhouse/t286-t268-retry` (T286) |
| T351 | `needs_retry` | `softhouse/T351-progress-accounting` | `commits` → demote | `softhouse/T369-review-t351` (T369), `softhouse/T370-t351-retry` (T370) |

Both return `commits`, so the ref store is **never asked**. The docstring now cites
`t462-t456-conditions/out/21-liveness.txt` and says "empty ON THIS TREE", not
"unreachable" — each of those ids becomes reachable the moment its recorded branch is
pruned or parked at a dispatch commit, which this program's own sweep does routinely.

---

## C-T456-4 (LOW) — CONFIRMED as a cardinal that rots; **and it rotted again, back**

`bin/20-relaxation-members.py` prints set B (pairs that carry **only** under the rejected
`anywhere` relaxation) as a **member set with the tree it was measured at**, plus a
named-pair audit. `out/20-relaxation-members.txt`, at `3f4e236ad458`, 707 live refs, 210
ids nameable from a head, **77** (id, other-ref) pairs:

| tree | B | \|B\| |
|---|---|---|
| 2026-08-28, T451 | `{ }` | 0 |
| 2026-08-29 (morning), T456 | `{ (T448, softhouse/T455-t448-conditions) }` | 1 |
| **2026-08-29 (afternoon), T462** | **`{ }`** | **0** |

**and the predicate did not change once in that window.** The named-pair audit says
exactly why the member left: it is not that the pair became name-only — **the ref no
longer exists.** `softhouse/T455-t448-conditions` was merged (`7f064835 Merge branch
'softhouse/T455-t448-conditions'`, 10 tracked paths under its own directory on main) and
then pruned. Create → merge → prune, in under 24 hours. **A cardinal over a live ref
store measures the ref store's weather, and the docstring published it as a fact.**

What did **not** move is the argument, and that is what the docstring now tells a reader
to re-check: **every member B has ever had is FOREIGN work that merely names the id.**
T455's branch carried T455's work *about* T448's conditions; under `anywhere`, T448 would
have refused to demote forever on somebody else's branch. **The cardinal aged badly in
one day; the adjudication aged well, and the one live instance the rot produced BACKS
T451.** Set A (carriers under the shipped code) is 15 pairs, 10 of them foreign-owned,
listed by member in the artefact; set C is 62.

---

## C-T456-5 (LOW) — CONFIRMED and fixed

The `stillborn` arm still opened `AND IT IS UNSTARTED -- MEASURED, not assumed`. It now
reads `AND NO EVIDENCE OF WORK FOR IT WAS FOUND ANYWHERE THIS FUNCTION CAN LOOK`, names
the two shapes that make the old sentence false — (i) T451 residual (a), a rescue ref
whose diff touches only SHARED files, and (ii) a worker that is alive right now — and
then says "here is exactly what WAS looked at". This is the whole of the live-repo output
diff (`out/60-readylist-RED-vs-GREEN.diff`).

## C-T456-7 (LOW) — CONFIRMED, and fixed by removing line numbers, not by updating them

`fire-program.sh:3127` was 3127 for T451, **3125** for T456, and is **3188** today —
without the line ever being edited. `:2729` is now **2792**. All four citations now name
the **text**: `git -C "$W" checkout -q -b "$WB"` for the sweep, and the variable
`RECONCILE_DEADLINE_SECS` for the budget. The rot itself is recorded in the comment so
the next author does not re-introduce a line number.

## C-T456-6 (LOW) — NOT DONE, and it is OUT OF SCOPE, not overlooked

`main_tree()` is still cited at `0.083 s` in `T350-reconcile-content.md`. That file is
neither `ready-tasks.py` nor my capture directory. **Declared open**, not argued shut.

---

## What changed

* `.softhouse/bin/ready-tasks.py`
  * `MIN_REFS_ALWAYS_PROBED = 8`, with the derivation, the exact subset guarantee, the
    reason the count cap is not simply restored, the reason `timeout=15` is *not*
    tightened, and the stated cost on the unbudgeted path.
  * the floor as the first conjunct of the clock arm in `refs_carrying_content`, and the
    truncation note now states that the first 8 are probed regardless of the clock.
  * `refs_carrying_content` docstring: the bound is time **with a count floor under it**.
  * `ref_content_evidence` docstring: MEASUREMENT 1 restated as a member set with three
    dated trees; MEASUREMENT 3's ratio kept and its counts marked as weather; residual
    (b)'s citation repointed at evidence that supports it, with the old artefact's
    contradiction named.
  * the `stillborn` note's `IT IS UNSTARTED` sentence replaced.
  * four `fire-program.sh:<line>` citations replaced by text citations.
* `.softhouse/capture/t462-t456-conditions/` — 5 instruments, 10 artefacts. Every fixture
  path is assembled from `S=".softhouse"`; `grep -rn '\.softhouse/' bin/` is empty.

## OPEN — declared, not argued shut

1. **Fan-out > 8 on a slow host still demotes a carrier at position ≥ 9.** F9, both in
   CAP8 and in GREEN. The floor bounds the regression, not the failure mode. Closing it
   needs either a probe order that puts likely carriers first, or a rule that truncation
   with *any* unprobed ref refuses rather than demotes — the second inverts T330 and is a
   behaviour change nobody has reviewed.
2. **`timeout=15` still exceeds `REF_PROBE_SECONDS` by 2.5×,** and under the floor the
   unbudgeted worst case is now up to `MIN_REFS_ALWAYS_PROBED` hung calls. I argued above
   that it must not be tightened; I did **not** argue that the exposure is acceptable.
   The lever is `--deadline-secs`, which `fire-program.sh` passes only on the signal path
   (`RECONCILE_DEADLINE_SECS`). Making the ordinary reconcile budgeted is a
   `fire-program.sh` change and out of my scope.
3. **`8` is still a number somebody picked** — it is now picked for a stated reason (it
   is the bound being replaced, so the subset property is exact), but the *right* floor
   is a function of the real fan-out distribution, which is 2 today and unmeasured
   tomorrow. Re-measure before raising it.
4. **ARM A is a transcription and can be edited into agreement with a defect.** ARM B
   exists because of that, but ARM B is only three sentences. More invariants would be
   better; I did not invent ones I could not tie to a recorded incident.
5. **ARM B is silent on 216 of 288 states**, including all 36 `commits` states. A real
   world where a branch has commits ahead of main *and* a rescue ref carries more is not
   modelled by this enumeration at all, in T451's, T456's or mine.
6. **The generous SUBJECT half is still unnarrowed** (T451 residual (b)). The member set
   is empty today; it is empty because of branch lifecycle, which C-T456-4 just
   demonstrated is weather.
7. **C-T456-6** — the stale `0.083 s` in `T350-reconcile-content.md`, out of scope here.

---

## Bar transcript — run on the COMMITTED tree

**One incident, recorded rather than quietly retried.** The first run on the committed
tree came back **exit 2, UNUSABLE — probe = `down`**. It was not my change: `docker ps`
showed `fineract-fineract-1  Exited (143)` — SIGTERM — about a minute earlier, while the
pre-commit run minutes before had read `up`. I restarted `fineract-db-1` and
`fineract-fineract-1`, waited on `actuator/health`, and re-ran. Every guard was already
green in the exit-2 run; the only failing arm was oracle reachability, and that run's own
text says so (`the reference oracle is UNREACHABLE: conformance is exit 2, which is not a
PASS and never becomes one`). **Whoever else is running in this repo should know the
oracle went down under them.**

```
$ git status --short           # empty: nothing uncommitted
$ git log --oneline -1
43e21fd8 T462: a safety refusal bounded by wall clock -- CONFIRMED, floored, driven both ways

$ bash .softhouse/conformance.sh > /tmp/t462/bar-committed.txt 2>&1 ; echo "BAR EXIT=$?"
BAR EXIT=0

PROBE PRESENCE CHECKED BEFORE ITS VALUE WAS READ:
$ grep -c 'probe = ' /tmp/t462/bar-committed.txt
1
$ grep -n 'probe = ' /tmp/t462/bar-committed.txt
219:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

conformance:   HARNESS-TEXT CENSUS: HEAD 43e21fd8323fce26d6b321db6b751252ed125854; tracked paths whose materialised bytes
conformance:   differ from HEAD: 0 — SUBSTITUTED by another index entry's blob
conformance:   0, uncommitted edits 0, deleted 0.

conformance:   frontier == pinned (all 11 rows, by path).
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
         IT EXCLUDES 1 RECORDED DIVERGENCE(S) — see THE DIVERGENCE CENSUS above.
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.

conformance:   all 16 wrong ledger implementations DIED through this harness, not by hand.
```

Full transcript: `out/90-bar-committed-tree-43e21fd8.txt` (added in the follow-up commit,
so the tree the bar graded is the one named above and this line is not self-referential).
