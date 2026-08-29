# T469 — independent adversarial review of T462 (`softhouse/T462-wallclock-refusal`, tip `04956e8b`)

**Under review** `.softhouse/bin/ready-tasks.py` — the resolver the driver runs every fire to
decide what to dispatch — plus `.softhouse/capture/t462-t456-conditions/`.
**RED** = `main:.softhouse/bin/ready-tasks.py` (blob `6f20b4573207`).
**GREEN** = `softhouse/T462-wallclock-refusal:.softhouse/bin/ready-tasks.py` (blob `f7d5f488…`).
**CAP8** = the pre-T451 count cap, rebuilt from RED's own bytes by a two-needle transform
whose uniqueness and liveness my instrument asserts before reporting
(`bin/mkcap8.py`, `variants/cap8.py`).

**Everything below was re-derived on my own fixture with my own instruments.** T462's numbers
and T456's numbers were both read as claims to be re-measured. Where I could not re-derive
something, I say so.

---

# VERDICT: **APPROVED WITH CONDITIONS**

The shipped resolver change is **correct, correctly reasoned, and correctly bounded.** I
reproduced C-T456-1 independently by slowing the host, reproduced T462's extension of it to the
arm nobody had driven, found a **new** case T462 did not have that sharpens it, and **could not
break the subset guarantee inside a single invocation of the probe** — which is exactly the
size T462 claimed for it. Both of T462's counter-intuitive derived conclusions (*a revert is
wrong*; *`timeout=15` must not be tightened*) **hold, and I drove both**. On the second one T462
is right and the task brief that filed `timeout=15` as a defect is **wrong about the remedy**.

Every condition below is about the **size of a claim** or about **one instrument's
self-description**, not about the bytes that ship. **Nothing blocks the merge.**

| id | severity | one line |
|---|---|---|
| **C-T469-1** | **MINOR** | The subset guarantee is stated one scope too large. `--deadline-secs` is a **process-global** deadline; the probe is per-task. Driven: 11 breaks over 12 cells. |
| **C-T469-2** | **MINOR** | The negative control **D-NULL is not behaviour-preserving** — it flips REFUSE→demote under a shared budget. So C-T456-2 is *not* repaired: the population is still self-selected. Driven. |
| **C-T469-3** | **MINOR** | The C-T456-7 repair ships a **new false historical claim**: the sweep line was **3125** on T451's own tree, never 3127. Also five citations were removed, not four. |
| **C-T469-4** | **LOW** | The C-T456-4 fix leaves **bare present-tense cardinals inside its own rewritten paragraphs**, and one of them measurably oscillated 15 → 16 → 15 during this review. |
| **C-T469-5** | **LOW** | Two `patterns.md:<line>` citations survive on the branch, both stale by 31 lines — the identical rot class, in the same file, undeclared. |
| **C-T469-6** | **LOW** | `floor invariant : OK` is a module-level *presence* check. Deleting the floor from the guard while keeping the constant leaves it printing OK. |
| **C-T469-7** | **LOW** | "ARM A is a transcription" is true but too small a declaration; the blind classes are nameable and one of them is the `none` route, which is outside the state space entirely. |

## Which direction I weight, and why the severities fall this way

Unchanged from T456 and I re-affirm it: **a wrong DEMOTE is worse than a wrong REFUSE**, because
a demotion offers a still-live line for re-dispatch and there is no note that recovers the lost
commits. T462's change moves the predicate strictly *away* from wrong demotes and never towards
them — I verified that on 12 cells and found **0** violations. That is why nothing here is MAJOR:
no finding of mine puts work at risk that the shipped diff does not already protect better than
`main` does.

---

# 0. Provenance and the bar

**The oracle was UP throughout.** `docker ps`: `fineract-fineract-1` and `fineract-db-1` both
`Up … (healthy)`; `actuator/health` → `{"status":"UP","groups":["liveness","readiness"]}`.
The SIGTERM incident T462 recorded did **not** recur under me.

**Bar on T462's branch tip, in a scratch clone OUTSIDE the repo** (`git clone --no-local` of the
repo into `mktemp -d`, `git checkout --detach 04956e8b`, `bash .softhouse/conformance.sh`):

```
PROBE PRESENCE CHECKED BEFORE ITS VALUE WAS READ:
$ grep -c 'probe = ' out/90-bar-t462-tip-04956e8b.txt
1
$ grep -n 'probe = ' out/90-bar-t462-tip-04956e8b.txt
243:conformance: reference oracle (https://localhost:8443/…/actuator/health) probe = up

conformance:   HARNESS-TEXT CENSUS: HEAD 04956e8bf474048956d81f39a76773da6744f611; tracked
conformance:   paths whose materialised bytes differ from HEAD: 0 …
conformance:   frontier == pinned (all 11 rows, by path).
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
BAR EXIT=0
```

**I graded the bytes, not the transcript.** T462's committed transcript
(`out/90-bar-committed-tree-43e21fd8.txt`) genuinely grades `43e21fd8` (its census line names that
sha, its probe line reads `up`, its verdict is PASS). My run grades `04956e8b`, the tip, which
adds only that transcript file. Both PASS with the probe **printed** and **up**. Claim confirmed.

The bar on **my own committed tree** is recorded at the foot of this document.

---

# 1. CLAIM 1 — C-T456-1 CONFIRMED, EXTENDED, and extended again by me

## 1.1 What I built, and why it is not T462's rig

`bin/10-fixture.sh` builds a synthetic repo with `git init` — **every path assembled from
`S=".$(printf 'softhouse')"`, no real `.softhouse/…` path spelled as a literal anywhere in
`bin/`.** `bin/gitwrap.sh` is a wrapper placed on the module's `GIT`; it sleeps before exec'ing
the real git and **logs every argv**, so probe counts are measured on the **host side** and a
module that lied in its own note could not move them. **The dead-path pin is not moved: nothing
in the predicate is edited, stubbed or monkeypatched** — only `set_repo()` (the module's own
public entry point) and `GIT`.

`bin/11-drive.py` refuses to report anything unless the wrapper is proved live first:

```
HOST LIVENESS  real git = /usr/bin/git ; wrapper = …/gitwrap.sh ; sleep = 3.2s
  fast leg: 8 git calls in 0.68s  -> 0.085s/call
  SLOW leg: 6 git calls in 20.55s -> 3.425s/call
  wrapper PROVED live: slow/fast = 40.3x ; argv log CAPTURING (8/6 calls)
```

An "unprobed" I did not cause cannot be reported, and a fabricated probe count of 0 cannot be
printed — the driver exits rather than report either. (It caught one real staging fault of mine:
a relative log path resolved against `cwd=repo`, which silently produced zeros. Recorded because
a reviewer instrument that fabricates is worse than none.)

## 1.2 The pre-T451 bound, established from git rather than assumed

`git show 0bf11587^:.softhouse/bin/ready-tasks.py`:

```
MAX_REFS_PROBED = 8
    for ref in refs[:MAX_REFS_PROBED]:
    if len(refs) > MAX_REFS_PROBED:  … "%d further name-matching ref(s) were NOT probed (cap %d)"
```

**A pure count cap at 8, with no clock arm at all.** So "the count cap it replaced" is 8, the
truncated set it produced is exactly `{refs at index >= 8}`, and `MIN_REFS_ALWAYS_PROBED = 8`
with the predicate `i >= 8` aligns with it **exactly, not approximately**. T462's CAP8 transform
is the right control and I rebuilt it independently.

## 1.3 The drive — `out/11-RED-vs-GREEN-vs-CAP8.txt`, six cases × two hosts × three variants

Sleep 3.2 s per git call. `probed` is counted from the wrapper's argv log.

| case | shape | host | CAP8 | RED | GREEN |
|---|---|---|---|---|---|
| **F2** | fan-out 2, carrier 2nd, branch PRUNED (`_absent_verdict`) | SLOW | **REFUSE** `relocated` (2) | **demote** `indeterminate` (1) | **REFUSE** `relocated` (2) |
| **F2S** | fan-out 2, carrier 2nd, branch **STANDING** (`stillborn-carried`) | SLOW | **REFUSE** `stillborn-carried` (2) | **demote** `indeterminate` (1) | **REFUSE** `stillborn-carried` (2) |
| **F8** | fan-out 8, carrier **8th (index 7)** — the floor boundary | SLOW | **REFUSE** (8) | **demote** (1) | **REFUSE** (8) |
| **F9** | fan-out 9, carrier 9th (index 8) | fast | **demote** (8) | REFUSE (9) | REFUSE (9) |
| **F9** | " | SLOW | demote (8) | demote (1) | demote (8) |
| **F1** | fan-out 1, carrier 1st — must-REFUSE control | both | REFUSE | REFUSE | REFUSE |
| **N** | fan-out 2, no carrier — must-DEMOTE control | both | demote | demote | demote |

**The finding reproduces, independently, on my own fixture.** RED probed **exactly 1** ref on
every slow case — two git calls at 3.2 s already exceed the 6.0 s ceiling, so the bound truncates
a **fan-out of two** after a single ref. On the fast host every one of those same cases comes out
REFUSE, so **the RED baseline genuinely had the opportunity to come out green and did not.**

**The second caller really was undriven before T462.** T456's own clock instrument names its
subject in its source: `BRANCH = "softhouse/T955-decoy-target"   # absent -- the
_absent_verdict leg`, one case only. The `stillborn-carried` arm at
`_branch_wip_core` had never been slowed by anyone. My **F2S** drives it from scratch and it
fails the same way — **CONFIRMED.**

**One case T462 did not have, and it is the sharpest.** **F8** — fan-out **8**, carrier
**eighth**. On a slow host RED probes 1 of 8 and destroys the work; CAP8 and GREEN probe all 8
and refuse. F8 also pins the floor's boundary condition: `i >= 8` leaves index 7 probed, which is
what `refs[:8]` did. A fixture whose largest fan-out is 2 cannot tell `>= 8` from `> 8`; F8 can.

---

# 2. CLAIM 2 — the fix and the exact size of its guarantee

## 2.1 The guarantee, re-derived

The claim: *the set of refs this probe leaves UNPROBED is a **subset** of the set the count cap
it replaced would have left unprobed, on every host and every budget.*

**Inside one invocation of `refs_carrying_content`, this is not merely true, it is EXACT.**
Re-derived from the loop rather than from the handoff:

* For `i < 8` neither bound truncates, and both variants issue the **same two `_run` calls in the
  same order with the same elapsed time before them** — so for fan-out ≤ 8 the two are not just
  subset-related, they are **identical**, verdict, note and all. My drive shows exactly that:
  probed(GREEN) = probed(CAP8) on F1 (1/1), F2 (2/2), F2S (2/2), N (2/2), F8 (8/8), on both hosts.
* For `i >= 8` the count cap **always** truncated, so any set GREEN leaves unprobed there is
  trivially a subset. F9 shows GREEN 9 vs CAP8 8 on a fast host — a strict **superset** of what
  was probed.

`LEG 2 — GREEN cells violating probed(GREEN) >= probed(CAP8): **0 of 12**.` RED violates it in
**5 of 6** slow cells. `LEG 3 — fast-host cells where GREEN's kind or polarity differs from RED:
**0 of 6**.` Clean-host behaviour is unchanged, which is the other half of the fix being safe.

**I tried to break it and could not — inside a probe.** A claim deliberately stated smaller than
the reviewer who asked for it is a virtue here, and this one is the provable size.

## 2.2 …but the sentence is one scope too large — **C-T469-1 (MINOR)**

`--deadline-secs` is **not per-probe**. `set_deadline()` writes a **module global**, `_run()`
reads it for **every call in the process**, and `refs_carrying_content` is invoked **once per
task** the resolver reconciles. So "on every host and **every budget**" is a claim about a
resolver *run*, and across a run it is **false**.

Construction (`bin/30-budget-fixture.sh`, `bin/31-budget-drive.py`, `bin/_two.py`): one process,
one budget, two tasks reconciled in order — a **sink** (T920, fan-out 20, all name-only) and then
a **victim** (T900, fan-out 2, carrier second, must REFUSE). The sink is where the two bounds
diverge: at fan-out ≥ 9 on a host fast enough not to trip the 6.0 s ceiling, the floored code
probes **more** refs than the cap did, and the excess comes out of the shared budget.

`out/32-budget-scan.txt`, host +0.02 s/git call, 3 repeats per deadline:

```
dline  variant sink   vict   sinkwall  victim kind      polarity
5.0    CAP8    8      2      2.92      relocated        REFUSE
5.0    GREEN   16     0      4.97      unverified       demote     <== BREAK
5.5    CAP8    8      2      3.03      relocated        REFUSE
5.5    GREEN   17     0      5.51      unverified       demote     <== BREAK
6.0    CAP8    8      2      3.08      relocated        REFUSE
6.0    GREEN   18     0      6.01      unverified       demote     <== BREAK

breaks: 11 over 12 cells
```

**CAP8's sink probes exactly 8 in every one of the 12 cells** (the hard cap) and finishes in
~2.9–3.1 s, leaving budget for the victim's two probes → `relocated` **REFUSE**. **The floored
code's sink probes 13–20**, consumes the entire budget, and the victim gets **0** probes →
`unverified` → **DEMOTE** on evidence the count cap refused to demote. That is a ref left
unprobed that CAP8 would have probed, and it is the destructive direction.

*Honesty note, because it changes how much weight this carries.* My **first** attempt at this
construction used a +0.15 s/call host and produced only 3 breaks over 18 cells, and a re-run of
the identical scan on a less loaded machine produced **0 over 15** — the flip band had moved. A
finding that survives one run and not the next is noise, so I re-derived the construction rather
than report the first one: a smaller per-call sleep lets CAP8's 8 refs finish cheaply while the
floored code still runs to its 6.0 s ceiling, which widens the band from ~0.5 s to ~3 s. What was
**never** noisy, in every cell of every run including the ones with zero breaks, is the mechanism:
`sink probes CAP8 = 8` against `sink probes GREEN = 9…20`. The excess consumption is deterministic;
only whether it lands on a verdict boundary is not.

**Three things make this MINOR rather than MAJOR, and I state all three:**

1. **It is not a regression introduced by this branch.** The extra consumption is T451's clock,
   already on `main`; RED behaves identically (my LEG 3: fast-host GREEN ≡ RED, 6/6). The floor
   neither causes it nor worsens it.
2. **It is unreachable on today's ref store.** It needs fan-out ≥ 9; the measured maximum on this
   repo is 2, and at fan-out ≤ 8 GREEN and CAP8 issue byte-identical call sequences.
3. **It is a defect in the SENTENCE, not in the diff.** Nothing here says the floor should not
   ship; it says the guarantee written beside it claims a scope the code does not have.

**Condition.** Scope the sentence: *"…on every host and every budget, **within one invocation of
this probe**"*, and record the cross-task residual — that `--deadline-secs` is process-global, so
a fan-out ≥ 9 task can starve a later task's probe. It costs one clause and it stops a future
reader inferring a run-level guarantee this does not have.

---

# 3. CLAIM 3 — the two derived conclusions. **Both hold. I drove both.**

## 3.1 "A revert is wrong" — **CONFIRMED**

`LEG 4`, case **F9 on a fast host**: CAP8 `indeterminate` **demote** (8 probed) while both RED and
GREEN return `relocated` **REFUSE** (9 probed). The carrier sorts ninth; the count cap cannot see
it and destroys the work. **T451's fail-open is real, reverting to the count cap re-opens a
different hole, and the floor is the only shape that keeps both.** Re-derived, not inherited.

## 3.2 "`timeout=15` must NOT be tightened" — **CONFIRMED, and the task brief's premise is the
one that is wrong**

The brief filed `timeout=15` as a defect because it is 2.5× the probe's own 6.0 s ceiling. T462
contradicted the filed premise. **T462 is right**, and here is the drive
(`bin/60-timeout-drive.py`, `out/60-timeout.txt`). GREEN-T3 is GREEN with the two per-call
timeouts inside `ref_content_evidence` cut 15 → 3, both sites asserted unique before writing; the
host is slowed to 4.0 s/call, i.e. into the band where the two differ:

```
variant      kind               polarity
CAP8         relocated          REFUSE    wall=33.07s
GREEN        relocated          REFUSE    wall=33.12s
GREEN-T3     indeterminate      demote    wall=22.55s
```

**Tightening the timeout demotes work that the untightened code refuses to demote**, because a
slow-but-successful probe becomes `rc=None` → `unprobed` → demote. It would make this probe do
**less** than the count cap did. T462's refusal is a conclusion, not an omission, and I endorse
it against the brief.

**Both are right about different things, and the record should say so.** The brief is correct
that the two bounds are inconsistent *as wall-clock bounds* — with the floor, the unbudgeted
worst case is 8 refs × 2 calls × 15 s. That is a **latency** defect. T462 is correct that the
**repair** is not to tighten it, because tightening converts latency into destruction.

**One qualification T462's text does not make, and should.** T462 names `--deadline-secs` as "the
correct lever" because it "is a genuine resource bound". It is — but it destroys by *exactly the
same mechanism*: `_run()` returns `rc=None` on budget exhaustion and clamps `timeout = min(timeout,
left)`, i.e. it **is** a tightened timeout, imposed by the caller. What makes it acceptable is not
that it is safer in polarity — it is not — but that **CAP8 and the floored code suffer it
identically per invocation**, so it does not break the subset relation. That is the argument;
the shipped text gives a weaker one. Folded into C-T469-1 rather than filed separately.

*(Also noted while planting: `timeout=15` has **five** call sites in this file, not two — three
are on the landed-work path. Neither T456 nor T462 is arguing about those, but the unbudgeted
worst case is correspondingly larger than either states.)*

---

# 4. CLAIM 4 — C-T456-2, and whether the cure escapes the disease. **It does not, yet.**

## 4.1 What reproduces

All of T462's factual claims about `bin/50-expected-verdicts.py` reproduce. Re-derived from the
instrument's **own axes** rather than from its banner or its transcript:

* `BRANCH` has **8** states, `LANDED` **4**, `REFS` **9** → **288**. ✓
* `EVIDENCE_CONSULTING = {"absent", "zero-ancestor"}` → 2 of 8 branch states → ARM B speaks on
  **2 × 4 × 9 = 72** and is **silent on 216**. `"commits-ahead"` is one of the six silent branch
  states, so **all 36 `commits` states are silent.** ✓ **216 and 36 confirmed by arithmetic from
  the instrument's constants, not from its output.**
* ARM A disagrees with the code on **0 of 288** on the shipped tree; D4 reddens A and B on **2**
  states, D5 on **8**, ARM C stays green for both; RED vs GREEN shows **0 polarity transitions
  over all 288 states** because the enumeration stubs `refs_carrying_content` wholesale. ✓
* D4 (`_branch_wip_core`) and D5 (`_absent_verdict`) are genuinely the **two distinct call sites**
  of `refs_carrying_content`. ✓
* ARM B's antecedents really are computed from the stubbed evidence coordinates and never from
  the returned kind or from a verdict table. **Its table-freedom is real**, as claimed.

## 4.2 The negative control is itself a defect — **C-T469-2 (MINOR)**

T462's repair of "the population was self-selected" rests on **D-NULL**: swapping the two
unconditional probe calls at the top of `_absent_verdict`, declared "a REAL edit to the same
routing region … that is behaviour-preserving", required to stay green, and scored
**"3 planted (2 defects, 1 non-defect), 2 caught, 1 correctly ignored."**

**D-NULL is not behaviour-preserving.** The two swapped calls share one wall-clock budget, so
their **order decides which one gets starved**. `bin/50-dnull-fixture.sh` builds a task whose work
**is on main** (so `landed_evidence` returns `merged`, a REFUSAL) with six further refs merely
naming it; `bin/51-dnull-drive.py` plants the swap on GREEN's own bytes (site asserted unique)
and drives it at 0.12 s/git call. `out/51-dnull.txt`:

```
deadline   variant        kind                 polarity
0.9        GREEN          merged               REFUSE
0.9        GREEN+D-NULL   indeterminate        demote     <== flips
1.2        GREEN          merged               REFUSE
1.2        GREEN+D-NULL   indeterminate        demote     <== flips
2.0        GREEN          merged               REFUSE
2.0        GREEN+D-NULL   indeterminate        demote     <== flips
5.0 / 30.0 both variants  merged               REFUSE
```

**REFUSE → demote, at three budgets, by a wall-clock bound starving a probe — which is C-T456-1's
own defect class**, reintroduced by the edit this branch calls its non-defect and requires to stay
green. The instrument passes it because **its state space has no time axis at all**.

**Consequence, and it is the point:** C-T456-2 is **not repaired**. The demonstrated population is
still **2 defects, 2 caught, 0 verified non-defects** — the specificity of the instrument is still
undemonstrated, which is exactly what "self-selected population" meant.

**Condition.** Withdraw or correct the scoreline (it is "3 planted, **3 defects**, 2 caught, **1
MISSED**"), and replace the control with an edit that preserves I/O while changing control flow —
a De Morgan rewrite of `if not complete or carriers is None or unprobed`, or hoisting an arm into
a helper. An edit that is inert *by construction* cannot calibrate anything; an edit that turns
out to be a defect calibrates it in the wrong direction.

## 4.3 What ARM A structurally cannot catch — **C-T469-7 (LOW)**

T462 declares "ARM A is a transcription and can be edited into agreement with a defect." True, and
too small. Read from the instrument's own source, ARM A compares **only `kind`**, over a state
space that models **8 of the 9 leading outcomes** of `_branch_wip_core`, with both evidence probes
replaced by argument-ignoring lambdas and `_case_clause` stubbed to `("","")`, and it **discards
the note text entirely**. Four blind classes follow, and they are nameable:

1. **the `none` route** — `if not branch: return "none"` is **not in the BRANCH axis at all**, so a
   routing defect on the isolation-violation signal is invisible by construction of the space.
   *(I confirmed this myself by reading the axis; it has no "no branch recorded" member.)*
2. **evidence-acquisition defects** — a probe called with the wrong argument still returns the
   stub's answer, so the enumeration cannot see it. One such defect is destructive.
3. **note-text defects** — which is **C-T456-5's own class**, the very finding this branch fixed.
4. **suffix production** — `_case_clause` is stubbed away, so T312's suffixes are unmodelled.

Five plants demonstrating (2)–(4) were driven by a delegated instrument under my direction and
came back green on every arm; **I did not personally re-run those five**, and I mark them as such.
Item (1) and §4.4 below I verified myself from the source.

## 4.4 `floor invariant : OK` is a presence check — **C-T469-6 (LOW)**

`constants_preflight()` parses the **module-level assignments** `MAX_REFS_PROBED`,
`MIN_REFS_ALWAYS_PROBED`, `REF_PROBE_SECONDS` and checks their relations
(`8 <= MIN < MAX`). It never inspects the truncation loop. **Delete `i >= MIN_REFS_ALWAYS_PROBED
and` from the guard while leaving the constant defined and the instrument still prints
`floor invariant : OK` and exits 0** — with the entire fix gutted. The floor **is** properly
driven, by `11-clock.py` and by my `11-drive.py`; the condition is that this line reads as more
assurance than it is, in the one instrument a later reader is most likely to run.

## 4.5 Is ARM B decorative?

**Partly, and its value is genuinely counterfactual.** It is silent on 216 of 288 states including
every `commits` state — confirmed. On the shipped tree its **marginal information over ARM A is
zero**: ARM A pins the kind on all 288 states, so B can only fire where A already fires, and in
both plants A and B caught the *same* state sets (2/2 and 8/8). B has never been the arm that
caught something A missed. That does **not** make it worthless — an invariant that cannot be
edited into agreement with the code is worth having precisely for the day someone edits A's table
— but "ARM B is the one that matters" oversells what has been demonstrated. T462's declaration
(open item 5) is honest and I am not filing a separate condition for it.

**One thing ARM B's own scoping deserves noting:** `EVIDENCE_CONSULTING` is a hand-maintained
one-line table that decides whether the table-free arm speaks at all, and the instrument never
verifies it. It is correct today. A routing change that made a seventh branch state consult the
ref store would fall silently outside ARM B. Recorded, not filed.

---

# 5. CLAIM 5 — the minors

## 5.1 C-T456-3 — **CONFIRMED**

T462's `bin/21-liveness.py` really does call `branch_wip` per (id, foreign-ref) pair and route on
the returned **kind**, not on status — verified by reading it and by re-running it. The old
artefact genuinely contradicts the sentence that cited it (`t451-t449-conditions/out/22-liveness.txt`
ends `non-terminal ids blocked by a FOREIGN-owned ref today: 4`, with four `<== LIVE FOREIGN-REF
REFUSAL` rows). The repointed citation supports its sentence.

> **Member set — non-terminal ids where a foreign ref actually buys a REFUSAL today = `{ }`.**
> Measured at tree `957941e3c1a1`, 710 live refs, 358 tasks. Unchanged from T462's measurement at
> `3f4e236ad458`; the only new row in the whole re-run is `T458 … kind=commits demote`, and `done`
> /terminal ids cannot enter the set.

T268 and T351 both return `commits`. This was verified **not** by trusting a transcribed arm list
but by tripwiring `ref_content_evidence`, `refs_carrying_content` and `refs_naming` and confirming
they are called **zero** times for both ids.

*Nit, not filed:* the docstring says "so the ref store is **never asked**". `ref_index()` **is**
read during `branch_wip` for both ids, via `case_variants`; it is the *content-carrying arm* that
is never reached. The operative sentence beside it ("the arm that consults the ref store is NOT
REACHED") is right; the parenthetical is loose.

## 5.2 C-T456-4 — mechanism **CONFIRMED**; the fix leaves the same rot inside itself — **C-T469-4 (LOW)**

**Mechanism confirmed.** `softhouse/T455-t448-conditions` no longer resolves —
`git show-ref | grep T455` is empty. `7f064835` is `Merge branch
'softhouse/T455-t448-conditions'`, bringing 10 tracked paths under that branch's own directory.
Create → merge → prune inside 24 hours, with the predicate untouched.

**Set B re-measured through T462's own instrument, on the live repo, today:**

> **MEASURED-AT** HEAD `319952da2d10`, resolver blob `6f20b4573207`, population **712 live refs,
> 212 ids nameable from a head, 79 (id, other-ref) pairs**
> **SET B = `{ }`, |B| = 0** — confirms T462.

**And a second, independent derivation of my own** (`bin/40-setA-census.py`, built from the two
regexes in `id_pattern()` and read through `git for-each-ref` + `git log` + `git diff` rather than
through the module — a different program over the same store, per T448's rule) at tree
`34fe206f8495`, 714 live refs: **SET A = 10 pairs, 10 of 10 FOREIGN-owned, every one carried by
the SUBJECT half.** The population differs from T462's by definition, not by disagreement (my
id-keying is narrower). **The SHAPE claim — every carrier is foreign work that merely names the id
— holds in my derivation at 10 of 10.** The adjudication against `anywhere` is sound and I endorse
it.

**The condition is what the fix left behind.** The rewritten paragraphs restate `|B|` correctly as
a member set with three dated trees — and then, in the same sentences, publish **bare
present-tense cardinals**:

* `ready-tasks.py:1305` — "…Re-check the SHAPE …, **and not the number. 15 pairs carry under the
  shipped code**…" — a bare cardinal in the sentence immediately after telling the reader not to
  trust cardinals.
* `:1321` and `:1363` — "**10 of the 15 current** carriers are foreign-owned".
* the same paragraph's "62 of 77" — I measure **64** of **79** today. (These two *are* marked "the
  counts are weather", which is the right treatment; the 15 and the 10-of-15 are not.)

**And the cardinal measurably oscillated inside this review.** T462 measured `|A| = 15`. A second
independent re-run of T462's instrument about an hour before mine, at tree `957941e3c1a1`, returned
**`|A| = 16`, 11 foreign**, with the extra member `(T458, softhouse/T468-review-t458)`. By the time
I re-ran it at `319952da2d10` that branch stood at **0 commits ahead of main**, so it carries
nothing and `|A|` was back to **15**. **15 → 16 → 15, in one afternoon, with the predicate
unchanged.** That is C-T456-4 reproducing *inside its own fix*, and T462 did not declare it.

**Two further stale cardinals survive in the same file, in scope, undeclared** — I measured both:

* `:1023` `(10,088 paths today)` — `git ls-tree -r --name-only main | wc -l` today = **10,372**.
* `:1035` `a measured maximum of 2 across all **705 live refs** in this repo today` — **714** today.

## 5.3 C-T456-5 — **CONFIRMED**

`main` says `AND IT IS UNSTARTED -- MEASURED, not assumed`; the branch replaces it with `AND NO
EVIDENCE OF WORK FOR IT WAS FOUND ANYWHERE THIS FUNCTION CAN LOOK`, explicitly flags itself as
"deliberately weaker", and names both falsifying shapes verbatim — the SHARED-files rescue ref
(T451 residual (a)) and the worker that is alive right now.

**And the new sentence is TRUE at the point the arm is reached**, which I checked by tracing rather
than by reading: the arm runs only after `landed_evidence` returned empty **and** `complete`, and
after `refs_carrying_content` returned no carriers **and** no `unprobed` — otherwise control has
already gone to `merged-unverified`, `stillborn-carried` or `indeterminate`. So every probe this
function has did run and found nothing, which is exactly what it asserts and no more.

## 5.4 C-T456-7 — repaired, but it ships a **new false claim** — **C-T469-3 (MINOR)**

**The repair itself is right, and removing the line numbers is a repair, not an evasion.** I argue
it: a line number is a *derived* coordinate over a file nobody promised to keep stable, and this
program has now watched it rot twice. The replacement citations are **text**, and the text is
**unique**: `git -C "$W" checkout -q -b "$WB"` matches **exactly one line** on `main`
(3188) — even the looser `checkout -q -b` matches one. `RECONCILE_DEADLINE_SECS` matches three
lines, all one story, and the surrounding claim ("only on the signal path") is true: two are inside
the SIG handler and the third is the sole `--deadline-secs` site. A citation that survives an edit
to the file it points into is strictly better than one that does not. **Deleting the numbers is the
repair.** Vindicated immediately: on `softhouse/T465-lock-frontier` the same text already sits at
3220.

**The defect is the story told about the rot.** The shipped comment says the line
*"was 3127 for T451, 3125 for T456 and 3188 for T462 **without the line ever being edited**"*.
Measured by me:

| tree | `git -C "$W" checkout -q -b "$WB"` |
|---|---|
| `0bf11587` — **T451's own first commit** | **3125** |
| `e0df51c5` — T451's tip | **3125** |
| `main` today | **3188** |

`git log -S'fire-program.sh:3127' -- .softhouse/bin/ready-tasks.py` returns **`0bf11587` alone**:
**`3127` was introduced by T451 and was never correct on any tree.** That is precisely what T456
said — *"`fire-program.sh:3127` — **the line is 3125**"*. T462 converted "a number that was wrong
when it was written" into "a number that rotted", and shipped the conversion as the lesson. Two
different defects with two different remedies; the comment teaches the wrong one.

**Also:** the branch removes **five** `fire-program.sh:<line>` citations, not four — `main` carries
them at lines 1051, 1243, 1429, 1686 and 1745, and the branch's count is **0**. The code change is
complete and correct; the handoff's "four" undercounts its own work.

## 5.5 Two survivors of the identical rot class — **C-T469-5 (LOW)**

On the branch, in the same file, undeclared:

* `:854` cites `.softhouse/patterns.md:1472` for **P-45** — P-45's heading is at
  `patterns.md:1503`; line 1472 is `/bin/sh`-is-bash-3.2 prose.
* `:2066` cites `.softhouse/patterns.md:442` for **P-22** — P-22's heading is at
  `patterns.md:473`; line 442 is neighbouring prose.

Both stale by 31 lines. Both quote the rule text alongside, so a reader can recover — but the
comment two lines from one of them says *"the rot itself is recorded … so the next author does not
re-introduce a line number"*, and two live instances of exactly that rot sit in the same file. Not
a demand to fix them here; a demand to **declare** them. (`patterns.md`'s own banner already
requires citing P-numbers by file and line, so these are load-bearing citations, not decoration.)

## 5.6 C-T456-6 declared OUT OF SCOPE — **HONEST, not convenient**

T462's `files_hint` in `.softhouse/tasks.json` is exactly `[".softhouse/bin/ready-tasks.py",
".softhouse/capture/t462-t456-conditions/"]`. `.softhouse/handoff/T350-reconcile-content.md` is in
neither, and the project's scope guard makes declaring-open the correct move.

**The check that decides it** is whether the same stale `0.083 s` figure also lives in the in-scope
file. It does appear once, at `ready-tasks.py:1020` — **and it is not a claim.** It is T451's
C-T449-6 note *narrating the duplication*: *"this comment used to say source 3 costs 0.070s and
T350's handoff said 0.083 s for the same call. They are one measurement … written down twice, and
P-80 says the second copy rots. So the number is not repeated as a decimal any more: it is a RANGE
with the instrument beside it."* **The in-scope file already refuses to carry the figure.**
"Out of scope" is honest.

*Adjacent rot nobody has filed, worth a task:* two rows below the `0.083 s` in
`T350-reconcile-content.md`, the same table still describes the ref probe as *"capped at
`MAX_REFS_PROBED = 8`, and anything beyond the cap is `indeterminate`, which demotes"* — behaviour
T451 removed and T462 has now re-shaped. A **larger** stale claim than the one that was filed, in
the same table.

---

# 6. CLAIM 6 — T462's declared open items

Each verified real and correctly bounded; **none is understated**, and one is understated *in
T462's own disfavour*, which I record as a credit rather than a condition.

| # | open item | my finding |
|---|---|---|
| 1 | fan-out > 8 on a slow host still demotes a position-≥9 carrier | **REAL.** F9 SLOW: GREEN demotes with 8 probed. CAP8 demotes it too. Correctly bounded as "the floor kills the regression, not the failure mode". |
| 2 | `timeout=15` exposure now up to 8 hung calls on the unbudgeted path | **REAL, and UNDERSTATED.** `timeout=15` has **five** call sites, three on the landed-work path; the true unbudgeted worst case is larger than 8 × 2 × 15 s. Folded into C-T469-1's condition. |
| 3 | `8` is a picked number tied to today's fan-out of 2 | **REAL and correctly reasoned.** It is picked so the subset property is *exact*, which I verified from `0bf11587^`'s `refs[:MAX_REFS_PROBED]`. Re-measure before raising it — agreed. |
| 4 | ARM A is a transcription | **REAL but too small** — see C-T469-7. |
| 5 | ARM B is silent on 216 of 288 states including all 36 `commits` states | **CONFIRMED exactly**, by arithmetic from the instrument's own axes (2 of 8 branch states consult evidence → 72 spoken, 216 silent; `commits-ahead` is 1 branch state → 36). |
| 6 | the generous SUBJECT half is still unnarrowed | **REAL and live.** In my own independent census, **10 of 10** carriers on the live store are foreign-owned and every one is bought by the SUBJECT half. This is the largest genuinely-open question about this predicate and it is correctly filed rather than smuggled. |
| 7 | C-T456-6 out of scope | **HONEST** — §5.6. |

---

# 7. What I re-derived, what I inherited, and what I left open

**Re-derived from scratch, with my own bytes and my own fixture:** the pre-T451 count-cap
semantics from `0bf11587^`; the CAP8 control; the slow-host reproduction of C-T456-1 on **both**
callers; the F8 boundary case; the probe counts (host-side, from the wrapper's argv log); the
subset property inside a probe; the fast-host equivalence of RED and GREEN; the "revert is wrong"
counter-case; the `timeout=15` adjudication; the D-NULL refutation; set B, set A and set C on the
live store, twice, through two different programs; the `fire-program.sh` line-number history; the
`patterns.md` citation staleness; the tracked-path and live-ref counts; the 288/72/216/36
arithmetic from the instrument's own axes; the `none`-route gap; `constants_preflight`'s presence
check; the bar on T462's tip in a clone outside the repo.

**Inherited and marked as such:** five of the ARM-A blind-class plants (§4.3 items 2–4) were driven
by a delegated instrument under my direction and I did **not** personally re-run them. I confirmed
the *structure* that makes them possible by reading the instrument; I do not assert their
transcripts as my own measurement.

**Left open, declared not argued shut:**

1. **The cross-task budget residual (C-T469-1) is not closed by anything here.** Its real remedy is
   to make the ordinary reconcile budgeted at all — a `fire-program.sh` change, out of my scope and
   out of T462's.
2. **I did not re-derive the 46 parity vectors** or anything downstream of the conformance bar; I
   ran the bar and read its verdict.
3. **I did not attack `refs_naming` / `RefIndex`.** My whole drive assumes the ref list and its
   sort order are right; if they are wrong, every number above is measuring the wrong population.
4. **My budget break is load-sensitive.** At the construction I settled on it is 11 of 12 cells and
   3 of 3 at deadlines 5.0/5.5/6.0; at my first, narrower construction it was 3 of 18 and then 0 of
   15 on a quieter machine. I report the **mechanism** (CAP8 sink = 8 probes, floored sink = 9–20,
   in every cell of every run) as established, and the **frequency in production** as unmeasured.
5. **Set A, set B and set C are all weather.** Every member set in §5.2 is quoted with the tree it
   was taken at, and one of them changed twice while I was writing this. Re-run, do not cite.

---

# 8. Reproduction

```
bash  .softhouse/reviews/t469-review-t462/bin/10-fixture.sh        <scratch>/fix
python3 .softhouse/reviews/t469-review-t462/bin/mkcap8.py          <variants>/red.py <variants>/cap8.py
python3 .softhouse/reviews/t469-review-t462/bin/11-drive.py        <variants> <scratch>/fix <out> 3.2
        # exit 1 == GREEN destroys work CAP8 preserved, or clean-host behaviour moved

bash  .softhouse/reviews/t469-review-t462/bin/30-budget-fixture.sh <scratch>/fixb
python3 .softhouse/reviews/t469-review-t462/bin/32-budget-repeat.py <variants> <scratch>/fixb <out> 0.02 4.5,5.0,5.5,6.0 3

bash  .softhouse/reviews/t469-review-t462/bin/50-dnull-fixture.sh  <scratch>/fixc
python3 .softhouse/reviews/t469-review-t462/bin/51-dnull-drive.py  <variants> <scratch>/fixc <out> 0.12
        # exit 1 == the 'negative control' destroys work

python3 .softhouse/reviews/t469-review-t462/bin/60-timeout-drive.py <variants> <scratch>/fix 4.0
python3 .softhouse/reviews/t469-review-t462/bin/40-setA-census.py   <repo>
```

`<variants>` holds `red.py` (`main:.softhouse/bin/ready-tasks.py`), `green.py`
(`softhouse/T462-wallclock-refusal:` same path), `cap8.py` (built by `mkcap8.py`) and
`branch_sweep.py`, which is **byte-identical on main and the branch**
(`60d9794cbcca4046c904a2a7ded96508f272be35bbbdfec6f51bcfb0c4b7c2ee`).

Every fixture path is assembled from a variable; `grep -rn '\.softhouse/' bin/` over this
review's instruments is empty — as it is over T462's, which I verified.

---

# 9. Bar on my own committed tree

```
$ git status --short              # empty: nothing uncommitted
$ git log --oneline -1
ef717b46 T469: independent review of T462 -- APPROVED WITH CONDITIONS

$ bash .softhouse/conformance.sh > /tmp/t469/bar-own.txt 2>&1 ; echo "BAR EXIT=$?"
BAR EXIT=0

PROBE PRESENCE CHECKED BEFORE ITS VALUE WAS READ:
$ grep -c 'probe = ' /tmp/t469/bar-own.txt
1
$ grep -n 'probe = ' /tmp/t469/bar-own.txt
220:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

conformance:   HARNESS-TEXT CENSUS: HEAD ef717b465d36f15a73b82d081fbdbfef184da47e; tracked paths
conformance:   whose materialised bytes differ from HEAD: 0 …
conformance:   frontier == pinned (all 11 rows, by path).
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
         IT EXCLUDES 1 RECORDED DIVERGENCE(S) — see THE DIVERGENCE CENSUS above.
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

Full transcript: `out/91-bar-t469-committed-tree.txt`, added in the follow-up commit, so the tree
the bar graded is the one named above and this section is not self-referential. `bash`, never
`sh`/`zsh`. The oracle was reachable and `up`; no exit-2 leg occurred.
