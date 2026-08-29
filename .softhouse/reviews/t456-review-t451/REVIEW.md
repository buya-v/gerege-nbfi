# T456 — independent review of T451 (`softhouse/T451-t449-conditions`, tip `de7c24b1`)

**Under review** `.softhouse/bin/ready-tasks.py` — the file every fire reads to decide what
to work on. **Merge base** `git merge-base main softhouse/T451-t449-conditions` =
`cbc8733c46cff515a2e48b5f3389ffbf514dc674`; all diffs three-dot from there.
**RED** = `cbc8733c:.softhouse/bin/ready-tasks.py`, sha256 `e80196813ea210a0…`, **byte-identical
to `main:` today** — verified, so T451's RED baseline is the right bytes.
**GREEN** = `de7c24b1:.softhouse/bin/ready-tasks.py`, sha256 `da9daeec15d3bb2f0d…`.

---

# VERDICT: **APPROVED WITH CONDITIONS**

**And the headline disagreement is settled in T451's favour: T449's `anywhere` patch must NOT
land.** I re-derived the counts, built R2 myself, and found a *live* counterexample T451 did
not have — which cuts the same way T451 argued.

| id | severity | one line |
|---|---|---|
| **C-T456-1** | **MAJOR** | `REF_PROBE_SECONDS` makes GREEN **demote** a task RED **refuses** to demote, on a 2-ref population, on a slow host. Driven. |
| **C-T456-2** | MINOR | The 288-state partition is a **well-formedness** check, not a correctness one: my fourth planted defect passes all five of its criteria clean. |
| **C-T456-3** | MINOR | A shipped docstring cites `out/22-liveness.txt` for a sentence that artefact contradicts on its face. The conclusion is true; the evidence trail is not. |
| **C-T456-4** | MINOR | "705 refs / 84 pairs / **exactly 0**" was true for one day. T451's own instrument, unmodified, now prints **1**. |
| **C-T456-5** | LOW | The `stillborn` note still says "**AND IT IS UNSTARTED — MEASURED, not assumed**" in the one case (fixture S) the author himself records as unmeasured. |
| **C-T456-6** | LOW | Residual 3 confirmed and still open: `0.083 s` in `.softhouse/handoff/T350-reconcile-content.md:246,251`, on `main`. |
| **C-T456-7** | LOW | `fire-program.sh:3127` — **the line is 3125**. Four new citations, all introduced by T451, one of them in a note a human reads at runtime. |

## Which direction I weight higher, and why it decides the severities

**A wrong DEMOTE, decisively.** A wrong REFUSE leaves a permanent `in_progress` lie (STEP 5.5
item 4) — visible in the ready list, annotated with the ref, the path and a recovery command,
and overridable by hand, which the driver of fire `20260828-140005` in fact did. A wrong
DEMOTE offers a **still-live line for re-dispatch**; a second worker forks or overwrites it and
there is no note that recovers the lost commits. That is T330's founding incident. So the one
finding on the demote side is MAJOR and every finding on the refusal side is MINOR or LOW,
even where the refusal-side findings are about a *record* — which is this file's whole subject.

---

# 1. THE HEADLINE — T451 vs T449 on the `anywhere` anchor

## 1.1 My own counts, from a different primitive

T451's `bin/20`/`bin/21` read the ref store through `branch_sweep.RefIndex` (a filesystem
walk). Mine (`bin/20-census.py`) reads it through `git for-each-ref` and re-implements both
anchors from the regexes in `id_pattern()`. T448's rule: two derivations sharing a primitive
are one derivation.

| | T451 (its day) | T456 (`bb51a610`, one day later) | note |
|---|---|---|---|
| live refs (`refs/heads`) | 705 | **708** | +3 |
| ids nameable from a head | 218 | 215 *(mine)* / **220** *(T451's rule, re-run)* | different id-keying, below |
| `(id, other-ref)` pairs | 84 | 143 *(mine)* / **86** *(T451's rule, re-run)* | mine is a superset |
| **carriers `anywhere` ADDS** | **0** | **1** *(both derivations)* | **the cardinal is stale** |
| max fan-out | 2 | **2** | ✓ |

The population difference is a definition, not a disagreement: T451 keys an id to a head only
when it is the head's **first** id (`ID.search(short)`), so `softhouse/T101-review-t100`
registers under T101 only. I key every id anywhere in the name. **Both derivations agree on
the number that matters**, because I re-ran `bin/21-realrepo-evidence.py` **unmodified** on
today's tree [`out/23-t451-bin21-rerun-today.txt`]:

```
live refs 708 ; ids nameable from a head 220 ; (id, other-ref) pairs 86
B. CARRY only under the PROPOSED `anywhere` -- what the patch would ADD: 1
   T448   ref=softhouse/T455-t448-conditions   ref-owner=T455   FOREIGN
        path .softhouse/capture/t455-t448-conditions/instruments/10-t455-runall-and-footer.sh
```

**Reproduction.** `git archive softhouse/T451-t449-conditions .softhouse/bin
.softhouse/capture/t451-t449-conditions | tar -x -C <scratch>`; symlink `.git`; then
`python3 .softhouse/capture/t451-t449-conditions/bin/21-realrepo-evidence.py .`.

That is **C-T456-4**: `exactly 0` had a half-life of one day. It is the same rotting-cardinal
class T451 filed as C-T449-3 against T350's `313`, and it wants the same remedy — the commit
beside the number, or a range plus the command.

## 1.2 …and the new instance lands on T451's side

`softhouse/T455-t448-conditions` carries four commits, **none of whose subject names T448**
(`T455: …` ×4), and four paths under `t455-t448-conditions/`. It is T455's work *about* T448's
conditions. Under `leading` T448 is name-only and demotes — correct. Under `anywhere`, **T448
would be REFUSED forever on T455's work**. That is fixture case R2 realised in the live store,
by a branch that did not exist when T451 wrote the argument. The cardinal aged badly; **the
adjudication aged well.**

## 1.3 The decisive T428 claim — checked against the ref, not the note

`bin/21-t428-anchor.py` → `out/21-t428-anchor.txt`. `softhouse/rescued-t428-t421tree-20260828-140005`:

* one commit, subject `RESCUED: WIP from a worker that never signalled done (fire 20260828-140005)` — **names no id**, so the generous SUBJECT half is mute;
* three paths, **all** under `.softhouse/capture/t421-t406-conditions/out/` — another id's directory, which is case K's shape exactly;
* filenames `T428-S01-counters.{psql,sql,txt}` — a path **component** is any component *including the filename*, so `leading.match("T428-S01-counters.psql")` fires. **CARRIES under the shipped anchor, 3/3 paths.**

**T451's Measurement 3 is correct.** T449's case K looked uncaught only because its fixture
filename was `work.txt`, which names nobody.

I did not stop at the one real ref. I built the same shape synthetically as fixture case
**KOWN/T947** — same "work under another id's condition dir", filename following this
program's owner-naming convention — and drove it through the shipped bytes:

```
KOWN/T947    RED relocated REFUSE      GREEN relocated REFUSE      RELAXED relocated REFUSE
K/T945       RED name-only demote      GREEN name-only demote      RELAXED relocated REFUSE  <== T449's patch changes this
```
[`out/11-drive.txt`]

So case K's *shape* is caught by the owning anchor whenever the file is named for its owner,
and T449's fixture differs from the real store in exactly the one attribute that decides it.

## 1.4 R2, constructed independently

`bin/10-fixture.sh` builds my own synthetic repo with `git init` (**every path through `$S`,
`$C`, `$R`, `$B` — never a literal `.softhouse/…`**), and `bin/11-drive.py` plants T449's
one-word patch into the shipped bytes (one site, **verified unique before writing** — the
first needle matched *two* sites, the main-side anchor in `paths_naming()` as well, and the
instrument refused rather than planting; that refusal is the instrument working) and drives
RED / GREEN / RELAXED over all eight cases:

| case | RED | GREEN | RELAXED (T449) | |
|---|---|---|---|---|
| G/T900 parked branch **and** a carrier ref | `stillborn` demote | **`stillborn-carried` REFUSE** | same | GREEN changed |
| G2/T901 same evidence, branch deleted | `relocated` REFUSE | `relocated` REFUSE | same | **agrees with G** |
| **R2/T982** swept *reviewer* worktree | name-only demote | name-only demote | **`relocated` REFUSE** | **the cost** |
| K/T945 case K, filename names nobody | name-only demote | name-only demote | **`relocated` REFUSE** | |
| KOWN/T947 case K, owner-named file | `relocated` REFUSE | `relocated` REFUSE | same | already caught |
| S/T990 shared-file rescue | `stillborn` demote | `stillborn` demote | `stillborn` demote | residual, unfixed by either |
| HLOAD/T955 carrier second in sort | `relocated` REFUSE | `relocated` REFUSE | same | *(fast host — see §2)* |
| E/T351 must-block control | `relocated` REFUSE | `relocated` REFUSE | same | control holds |

**R2 reproduces.** Under `anywhere`, T982 — a task whose only trace is somebody else's review
of it, carried on a rescue branch whose subject names nobody — becomes a **permanent refusal**.
`.softhouse/reviews/t983-review-t982/REVIEW.md` is the commonest cross-task object this program
makes: 69 of 84 pairs (T451) / **117 of 143** (mine) are name-only today, and the review branch
is the dominant shape among them.

## 1.5 Adjudication

**T451 is right and T449's patch must not land.** The premise it rests on — "the owning anchor
cannot see work filed under another id's directory" — is refuted by the only real instance in
this repo *and* by a synthetic I built independently. The patch buys **zero** carriers on the
live store and costs the R2 shape, of which a **live** example (T448 / T455) appeared within a
day of T451 writing the argument. `anywhere` on the PATH half would import T339's defect one
level in: not "a NAME matched" but "a MENTION inside a path matched".

The genuinely arguable part is the *reverse* direction, and T451 files it as its own residual:
the SUBJECT half is already `anywhere`, and it is the half doing all the foreign-ref work
(10 of 15 carriers on T451's day, 12 of 17 on mine). That asymmetry is the real open question
about this predicate, and it is correctly filed rather than smuggled in beside two MAJORs.

---

# 2. C-T456-1 (MAJOR) — the clock-bounded probe demotes work the count cap refused

## What T451 did

`MAX_REFS_PROBED = 8` → `512` (runaway guard only), plus `REF_PROBE_SECONDS = 6.0`, a ceiling
on the probe's own wall clock. The reasoning against a count cap is **right**: 8 is not a
resource, a count cap *manufactures* ignorance and then applies the fail-closed rule to it, and
on the one signal whose job is to *stop* a demotion that converts REFUSE into proceed. I agree
with the judgement. The **implementation** is where the finding is.

## The attack, and it lands

`bin/12-clock.py` makes the **host** slow, not the code: it points the module's `GIT` at a
wrapper that sleeps before exec'ing real git. Nothing is stubbed or monkeypatched in the
predicate; the only variable moved is how long git takes to answer — exactly the variable a
loaded CI box moves. Fixture **HLOAD/T955**: two name-matching refs (**the measured maximum
fan-out on the live repo**, i.e. the *ordinary* population), the only carrier **second** in
sort order, task branch absent.

```
RED    host=fast    relocated          REFUSE    (0.2s wall)
GREEN  host=fast    relocated          REFUSE    (0.2s wall)

RED    host=SLOW    relocated          REFUSE    (29.4s wall)
GREEN  host=SLOW    indeterminate      demote    (22.2s wall)
        note> ... 1 of 2 name-matching ref(s) were NOT probed: this probe's own 6.0s
              ceiling (REF_PROBE_SECONDS) was reached after 1 ref(s) ...
```
[`out/12-clock.txt`]

**On a slow host GREEN demotes a task RED refuses to demote.** The count cap could not truncate
a 2-ref population; the wall-clock bound can, on one slow probe.

## Why the handoff's defence does not hold

Residual 4 argues the bound "can only fire far outside the measured population (max fan-out 2
vs a 6-second ceiling at ~0.1 s per ref)". That is an argument **on the count axis** about a
bound **on the time axis**. On the time axis, fan-out 2 needs *one* slow probe, not eight refs.

The sharpest form is internal to the file: `ref_content_evidence` issues its two git calls with
**`timeout=15`** each. **The module's own per-call timeout is 2.5× the whole probe's 6.0 s
ceiling.** Any single git call that runs anywhere near the duration the code itself permits
guarantees truncation of every remaining ref. Two bounds in one file, inconsistent by
construction, on the predicate that decides whether work is destroyed.

And it is invisible to the safety argument offered for it: the 288-state partition **stubs
`refs_carrying_content`** — the very function whose truncation rule changed — so this state is
outside the enumeration entirely. It is also outside the fixture drive, which runs on a fast
host. The claim "**exactly two verdicts more conservative and none less**" is true of the
fixture and of the 288 states; it is **false of the predicate on a loaded host**.

## Condition

Keep a deterministic **floor** under the resource ceiling, so RED's behaviour is a strict
subset of GREEN's:

```python
if i >= MAX_REFS_PROBED:
    stopped = ...
elif i >= MIN_REFS_ALWAYS_PROBED and time.monotonic() - started > REF_PROBE_SECONDS:
    stopped = ...
```

with `MIN_REFS_ALWAYS_PROBED = 8` — the old cap, now a floor rather than a ceiling. Every ref
the old code probed is still probed; the clock only bounds fan-outs the old code truncated
anyway. `MAX_REFS_PROBED = 512` and `--deadline-secs` are untouched, so the runaway guard and
the process budget both survive. Then the handoff's failure-direction claim becomes true
unconditionally, and `bin/12-clock.py` in this review is the RED leg that proves it.

**Reproduction:**
```
python3 .softhouse/reviews/t456-review-t451/bin/10-fixture.sh /tmp/t456/fixture   # build
python3 .softhouse/reviews/t456-review-t451/bin/12-clock.py \
        <red.py> <green.py> /tmp/t456/fixture /tmp/t456/clock 3.5
# exit 1 == GREEN demotes where RED refuses
```
(`<red.py>` / `<green.py>` are the two `ready-tasks.py` versions staged beside a copy of
`branch_sweep.py`; the instrument aborts if the sleep wrapper does not actually sleep, so an
"unprobed" it did not cause cannot be reported.)

---

# 3. C-T456-2 (MINOR) — the partition, and my fourth planted defect

## It reproduces exactly

`bin/50-partition.py` on RED and GREEN [`out/50-partition-rerun.txt`]:

| | RED | GREEN |
|---|---|---|
| states enumerated | **288** (8 × 4 × 9) | **288** |
| no usable verdict | **0** | **0** |
| two verdicts | **0** | **0** |
| arm-transcription mismatches | **0** | **0** |
| exceptions | **0** | **0** |
| redundant *agreeing* arms | **9** (`merged-unverified` matches `==` and `startswith("merged")`, both REFUSE) | **9** |

Redistribution exact and conserved: RED's 9 `stillborn` → GREEN's **2 `stillborn` + 4
`stillborn-carried` + 3 additional `indeterminate`** (8 → 11); total 288; every kind maps to
exactly one polarity. **All of T451's partition numbers are confirmed.**

*A staging note, because it nearly became a false finding.* My first run put `red.py`/`green.py`
in a bare `/tmp` directory and reported **9 and 14 exceptions**
(`AttributeError: 'NoneType' object has no attribute 'short'`). That is `sys.path.insert(0,
dirname(__file__))` failing to find `branch_sweep.py` — **my staging, not the code**. With
`branch_sweep.py` beside the modules, 0/0. In the real code those states are unreachable
(`branch_sweep is None` ⇒ `ref_index()` None ⇒ all-None from `refs_carrying_content` ⇒
`indeterminate` before any `.short()` call), so they are stub-fed impossibilities. Recorded so
nobody re-finds it and files it.

## Failure direction, checked **per state** rather than per aggregate

The partition transcript prints counts per kind, which cannot distinguish "three states moved
demote→REFUSE" from "four moved that way and one moved back". `bin/50-direction.py` pairs the
**same state** in both legs [`out/50-direction.txt`]:

```
REFUSE   -> REFUSE   :  53
demote   -> REFUSE   :   4   <== more conservative
demote   -> demote   : 231
REFUSE -> demote (work-destroying) : 0
```

**Claim 4 confirmed at state granularity: nothing moved the destructive way** — inside this
enumeration. C-T456-1 is the state that did, and it is outside it.

## The fourth defect — **NOT CAUGHT**

T451 planted D1 (arm returns the wrong polarity), D2 (arm deleted → falls through to the
bottom demote) and D3 (T312 suffix no longer stripped), and caught 3 of 3. **All three are
`reconcile_action` arm defects, and all three break the lattice's *well-formedness*** — they
make a state have no verdict, two verdicts, or a verdict disagreeing with the instrument's
transcription of the arms. That is a self-selected population.

**D4 (mine) is a routing defect in `_branch_wip_core`**, not an arm defect: swap the order of
the two new tests, so `if carriers is None or unprobed:` is evaluated before `if carriers:`.
The lattice stays perfectly single-valued; `reconcile_action` is untouched, so the
transcription still agrees; no state gains or loses a verdict. What changes is that a state
where a live ref **carries content** *and* another ref went **unprobed** now DEMOTES instead of
REFUSING — the C-T449-1 fail-open reintroduced for the budget-starved subset, which is exactly
what `REF_PROBE_SECONDS` truncation produces.

`bin/51-plant-d4.py` [`out/51-plant-d4.txt`]. T451's enumeration on the planted file:

```
states enumerated             : 288
states with NO usable verdict : 0
states with TWO verdicts      : 0
arm-transcription MISMATCHES  : 0
exceptions raised             : 0
```

**All five criteria green.** Meanwhile my per-state check on the same file:

```
REFUSE -> demote (work-destroying) : 2
   ('zero-ancestor','none+complete','carr1 name0 unpr1')  stillborn-carried -> indeterminate
   ('zero-ancestor','none+complete','carr1 name1 unpr1')  stillborn-carried -> indeterminate
LEG 2 exit code: 1
```

The only trace in the partition output is a census line (`stillborn-carried 4 → 2`,
`indeterminate 11 → 13`) that a reader must notice by eye; the instrument renders no verdict
about it. **The 288-state enumeration is a well-formedness property, not a correctness one**,
and the handoff presents it as the safety argument for the change. It is a real and worthwhile
property — it is just not the one being claimed.

**Condition.** Give the enumeration a pinned per-state expected-polarity baseline (or diff the
new census against a committed one) so a routing change *fails* rather than shows up as a
number to eyeball. `bin/50-direction.py` in this review is a working instance; it exits 1 on
D4 and 0 on the shipped GREEN.

**Reproduction:**
```
python3 .softhouse/reviews/t456-review-t451/bin/51-plant-d4.py <green.py> \
        <T451 bin/50-partition.py> .softhouse/reviews/t456-review-t451/bin/50-direction.py /tmp/t456/d4
```

---

# 4. C-T449-1 — the `stillborn` arm: FIXED, and the record is true

`out/11-drive.txt`, `out/13-note-truth.txt`.

* **G/T900** (branch parked at the dispatch commit **and** a rescue ref carrying the work):
  RED `stillborn`/**DEMOTE** → GREEN `stillborn-carried`/**REFUSE**.
* **G2/T901** (byte-identical evidence, branch deleted): `relocated`/REFUSE before and after.
* **G and G2 now agree on polarity.** The defect — identical content evidence yielding opposite
  polarity decided by nothing but whether the branch was deleted — is closed.

**The note is TRUE, not merely different.** `bin/13-note-truth.py` checks each *assertion*
against git rather than reading the prose:

* every ref the note names **resolves**, and the carrier it names (`softhouse/rescued-t900-work-20260829`) genuinely **owns** the path it cites (`.softhouse/capture/t900-work/out/wip.txt`);
* every repo path the note names is **in that ref's diff**;
* the recovery command it prints (`python3 .softhouse/bin/branch_sweep.py sweep --pattern '*T900*' --counts`) names a tool that **exists in this repo**;
* the sentence RED got wrong — "It reads as MERGED … **and it is UNSTARTED**" — is **gone** from this arm and replaced by "BUT IT IS NOT UNSTARTED, AND THIS ARM USED TO SAY IT WAS".

**`FALSE OR UNSUPPORTED ASSERTIONS IN GREEN: 0`**, and the checker is calibrated: its P-22 RED
leg runs the same assertion against **main's bytes**, where case G's note asserts UNSTARTED
while a live ref carries the work, and **catches it**. A checker that has only ever printed 0
is not a checker.

*Two false findings this instrument produced and I fixed rather than shipped, recorded because
a reviewer instrument that fabricates is worse than none:* its first ref-regex matched
`.softhouse/bin/branch_sweep.py` as a *ref* (6 spurious FALSEs), and its path check counted
paths inside the backticked **recovery command** as claims about the ref's diff (2 more). Both
are in the file's comments.

The sub-case polarities are also right, and the reasoning is the part I checked hardest:
**an unrun ref probe on this leg demotes** (`indeterminate`), deliberately *less* generous than
a carrier. The argument — the absent leg has *strictly more* evidence of a merge and already
demotes on an unrun probe (T330), so this leg may not be more generous on less evidence — holds.

---

# 5. C-T456-3 (MINOR) — the citation contradicts the artefact it cites

**Where.** The shipped docstring of `ref_content_evidence`, residual (b), and the identical
sentence in the handoff:

> "every affected id either is absent from tasks.json or has a branch with commits ahead of
> main, so the ref arm is **unreachable for all of them today** [out/22-liveness.txt]"

**What the cited artefact actually prints** (`git show
softhouse/T451-t449-conditions:.softhouse/capture/t451-t449-conditions/out/22-liveness.txt`):

```
non-terminal ids blocked by a FOREIGN-owned ref today: 4
   ('T268', 'softhouse/t281-review-t268', 'T281', 'needs_retry')   <== LIVE FOREIGN-REF REFUSAL
   ('T268', 'softhouse/t286-t268-retry', 'T286', 'needs_retry')    <== LIVE FOREIGN-REF REFUSAL
   ('T351', 'softhouse/T369-review-t351', 'T369', 'needs_retry')   <== LIVE FOREIGN-REF REFUSAL
   ('T351', 'softhouse/T370-t351-retry', 'T370', 'needs_retry')    <== LIVE FOREIGN-REF REFUSAL
```

The artefact and the sentence citing it say opposite things. The cause: `bin/22-liveness.py`'s
`reachable` predicate is `status not in NOT_RUNNABLE` — it tests only the **first** disjunct and
never the second ("commits ahead of main"), so it answers a different question than the sentence
claims it answers.

**The conclusion is nevertheless TRUE, and I measured it with the right predicate.**
`bin/22-liveness.py` (mine) re-discovers the pairs from scratch over all 344 tasks and then
**calls `branch_wip`** to see which arm actually fires [`out/22-liveness.txt`]:

```
T268    needs_retry   commits   demote   ref arm: not    softhouse/t281-review-t268(T281), softhouse/t286-t268-retry(T286)
T351    needs_retry   commits   demote   ref arm: not    softhouse/T369-review-t351(T369), softhouse/T370-t351-retry(T370)
ids where a FOREIGN ref ACTUALLY buys a refusal today: 0
```

Both recorded branches have commits ahead of `main`, so `_branch_wip_core` returns `commits` and
the ref arm is never reached. **Unreachable today: confirmed.** Note also that the pair
population grew by **two** (T447/T452, T449/T451) in one day; both are `merged` and terminal, so
still unreachable — but "unreachable" here is a property of *this* `tasks.json` on *this* day,
not of the predicate, and the residual is correctly filed as a condition rather than fixed.

**Condition.** Re-take `bin/22-liveness.py` so it tests the disjunct it claims (call
`branch_wip`, or check commits-ahead), and re-cut `out/22-liveness.txt`; or reword the docstring
so it does not cite an artefact that reads the other way. The severity is that this is a
docstring in `ready-tasks.py`, which every future reviewer reads, and a record that contradicts
its own evidence is the exact class T451 filed against T350.

---

# 6. C-T456-5 (LOW) — the `stillborn` note still over-claims in fixture case S

Fixture **S/T990**: a worker scoped to a **shared file** (`.softhouse/bin/…` — T451's own scope
was such a file), killed before its first commit. The rescue ref
`softhouse/rescued-t990-shared-file-20260829` carries **real work**; its diff names no id
anywhere, so both anchors read name-only and the arm demotes. The verdict is right, and T451
records the gap as residual 2. But the emitted note says [`out/13-note-truth.txt`]:

> "**AND IT IS UNSTARTED — MEASURED, not assumed**: 1 live ref(s) carry id T990 IN THEIR NAME
> — softhouse/rescued-t990-shared-file-20260829 — and not one of them OWNS any content
> belonging to it."

What was measured is "no path in that ref's diff is OWNED by T990". "IT IS UNSTARTED" does not
follow, and the author's own residual 2 says why it does not. This is a weakened form of the
sentence T451 was sent to remove — improved (the ref is named, "MEASURED not assumed" is
qualified, and the reader is warned about live workers), but still stronger than its evidence
in the one arm where the evidence is known to be blind.

**Condition.** In the `name_only`-non-empty branch, say "**no evidence of work bearing this id
was found**" rather than "IT IS UNSTARTED", and point at fixture case S. Keep the wording as-is
in the `no refs at all` branch, where it is earned.

---

# 7. Cardinals, re-derived (C-T449-3 and C-T449-4: both exact)

`bin/01-cardinals.py` over `git ls-tree -r --name-only <commit>` [`out/01-cardinals.txt`]:

**At `b102875c`, the commit the shipped comment cites** — every figure matches T451:

| | shipped before T451 | T451 | T456 |
|---|---|---|---|
| handoff paths tracked | 542 | 542 | **542** ✓ |
| ending `.md` | — | 337 | **337** ✓ |
| NOT `.md` (loop `continue`s past) | — | 205 | **205** ✓ (114 `.txt`, 30 `.py`, 26 `.out`, 18 `.sh`, 11 `.zsh`, 2 `.go`, +4 singletons) |
| bare `T###.md` (DO key) | 229 | 229 | **229** ✓ |
| `A2-<n>.md` (DO key) | — | 29 | **29** ✓ |
| **genuinely inert** | **313** | **79** | **79** ✓ |

`313 = 542 − 229` exactly, i.e. the old figure counted all 205 non-`.md` files as handoffs using
the `<id>-<slug>.md` convention. T451's parenthetical "at today's main the same arithmetic gives
318" also reproduces: **547 − 229 = 318**, with the inert population now **84**. The correction
is right and the reason it was wrong is right.

**C-T449-4**: 24 tracked paths on main MENTION T268; **0** are OWNED by it; **23** under
`.softhouse/capture/t286-t268-retry/` and **1** under
`.softhouse/reviews/t291-review-t286/out/rerun-t268-battery.txt`. Identical at `b102875c` and at
today's `main`. The docstring's correction, and its point that a **third** owner strengthens the
mention-vs-ownership argument, both hold.

**C-T449-6**: the code no longer carries a copiable decimal; it carries a range plus
`bin/30-cost.py`. Correct remedy. **C-T456-6**: the divergent `0.083 s` is still on `main` at
`.softhouse/handoff/T350-reconcile-content.md:246` and `:251` — confirmed present, outside
T451's scope, correctly filed, and still needing an owner.

**C-T449-7**: acknowledged with no behaviour change, and the note now says so. I agree that
nothing in `_branch_wip_core` can distinguish a live pre-first-commit worker from a dead one,
and that adding a liveness signal is a new signal rather than a condition. The note names
`foreign_live_session_in_repo()` as the only thing standing between the verdict and a live
worker's branch, which is the honest statement.

---

# 8. Tool behaviour and scope

**`python3 .softhouse/bin/ready-tasks.py` on T451's tree** [`out/61-readylist-t451tree.txt`]:
**EXIT 0**, `IN PROGRESS (5)` / `READY (45)` / `BLOCKED (8)`. The READY list is sane — 45
plausible task lines, the `!! WORK BEARING id T286 IS ALREADY ON MAIN` flag raised with 27
owning paths, blocked edges resolved.

**`--json` parses** [`out/62-json-t451tree.json`]: `json.load` succeeds; keys `blocked`,
`in_progress`, `ready`, `unresolved_edges`; **45 / 5 / 8 / 0**, agreeing with the text output.

**RED vs GREEN on the same tree**: `diff` is **0 lines** today
[`out/60-readylist-RED-vs-GREEN.diff`]. T451 reported 8 lines / 2 hunks of note *text* on its
day; today the two outputs are byte-identical. Either way the change is behaviour-neutral on
the live queue, which is the property that matters for the file every fire reads.

**Scope: clean.** `git diff --stat cbc8733c...de7c24b1` touches only
`.softhouse/bin/ready-tasks.py`, `.softhouse/capture/t451-t449-conditions/**` and
`.softhouse/handoff/T451-t449-conditions.md`. `conformance.sh` (T454) and `.softhouse/hooks/`
(T453) are untouched, as declared.

**Dead-path frontier, on MY instruments** [`out/70-deadpath-calibration.txt`]: `deadOccurrences
108`, unchanged, with all 10 of my instruments staged and confirmed inside the census corpus
(`git ls-files '.softhouse/*.py' '.softhouse/*.sh'` → 10 of 1623). **Calibrated**: a dead
literal planted as a *code string* moves it to `deadFiles=76 deadOccurrences=109`; reverting
restores 75/108. (A first probe placed in a `#` comment did **not** move it — the census buckets
comment literals as `prose`. Recorded because stopping there would have made the 108
uninterpretable.) The pin was not touched.

---

# 9. WHERE I LOOKED — "not found" is a statement about the search

* **The ref store**: all 708 `refs/heads` via `git for-each-ref` (mine) and via
  `branch_sweep.RefIndex` (T451's `bin/21`, re-run unmodified). 766 refs across all namespaces
  (708 heads, 37 remotes, 21 `refs/rescue`) — **`refs_naming` reads `refs/heads` only**, so
  the 21 `refs/rescue/*` entries are outside the predicate's universe entirely; that is a
  pre-existing property of `RefIndex`, not something T451 changed, and I did not pursue it.
* **The whole tracked tree** at `b102875c` (9,730 paths) and at `main` `bb51a610` (10,088).
* **`.softhouse/tasks.json`** — all 344 tasks, each one's recorded branch resolved and passed
  through `branch_wip`.
* **The T451 branch**: full three-dot diff, all 10 instruments, all 15 output files, the handoff.
* **`.softhouse/capture/t316-dead-path-guards/census_dead_paths.py`** and
  `.softhouse/guards/check-dead-path-frontier.sh` for the frontier discipline;
  `.softhouse/capture/t238-failopen/instruments/sweeplib.sh` for the instrument shape.
* **`fire-program.sh`**: I read both cited lines. `:2729` is **right**
  (`[[ -n "${RECONCILE_DEADLINE_SECS:-}" ]] && args+=(--deadline-secs ...)`). `:3127` is
  **wrong** — see C-T456-7. I did not drive the fire itself, and do not claim to have.

---

# 9a. C-T456-7 (LOW) — `fire-program.sh:3127` is line **3125**

`grep -n 'checkout -q -b "$WB"' .softhouse/bin/fire-program.sh` → **3125**, on `main` **and**
on `softhouse/T451-t449-conditions` (the file is untouched by this branch, so it was 3125 when
T451 wrote the citation too). The string `3127` appears **4 times in GREEN and 0 times in RED**
— every one is new in this change:

```
ready-tasks.py:1243   reviewer's worktree swept by fire-program.sh:3127 gets the sweep's boilerplate
ready-tasks.py:1429   # CARRIES CONTENT for the id -- which is what fire-program.sh:3127's sweep
ready-tasks.py:1686   # fire-program.sh:3127 is `git -C "$W" checkout -q -b "$WB"`: it moves the dead
ready-tasks.py:1745   "fire-program.sh:3127 moves a dead worker's uncommitted WIP onto a "
```

`:1745` is inside the **`stillborn-carried` REFUSE note** — a string a human reads at the moment
they are being asked to adjudicate rescued work, pointing them two lines off. The sibling
citation `fire-program.sh:2729` in the same change is **correct**, which is what makes this a
transcription slip rather than a misreading.

This is the P-86 class the repo already carries a rule for (T326: *"that citation read
`conformance.sh:1715` until T326 measured it; the text is at :1727 and the cardinal was stale
by 12 lines on main BEFORE this guard was written"*), and it is the same class as C-T449-3 —
a cardinal restated away from its measurement — inside the change that corrected C-T449-3.

**Condition.** Either fix the four to `:3125`, or do what T326's rule actually recommends and
cite the **sentence** rather than the line: `git -C "$W" checkout -q -b "$WB"` is already quoted
at `:1686` and is greppable, stable and self-verifying in a way a line number is not.

**Reproduction.** `grep -n 'checkout -q -b "\$WB"' .softhouse/bin/fire-program.sh` and
`grep -n '3127' .softhouse/bin/ready-tasks.py` on the T451 tree.

---

# 10. THE BAR

`bash .softhouse/conformance.sh` on the **clean committed tree `5bddc3fb`** of
`softhouse/T456-review-t451` — this review's own bytes, not T451's. Scratch in
`/tmp/t456/bar`, **outside the repo** (`TMPDIR=/tmp/t456/bar`). `git status --porcelain`
was **empty before** the run and **empty after** it.

## EXIT 0

The probe was tested for **PRESENCE BEFORE ITS VALUE** — P-84, "absence is not `down`", and
"EXIT 2 WITH NO PROBE LINE" is the guard working:

```
$ grep -c 'probe = ' /tmp/t456/bar/bar-1.txt
1
```

**and only then read. Probe line, verbatim:**

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```

## The cardinals this review was required to confirm

```
conformance:   T316-DEADPATH-CENSUS: corpus=1623 deadFiles=75 deadOccurrences=108 resolving=1547 indeterminate=122 prose=411
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   ... frontier 11, pinned at 11
conformance:   frontier == pinned (all 11 rows, by path).
conformance:   reconciler ownership: GREEN 13/13 cells correct / RED 8/13 cells correct
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   all 16 wrong ledger implementations DIED through this harness, not by hand.
```

`deadOccurrences 108` ✓ · frontier `11 == 11` ✓ · reconciler ownership `GREEN 13/13 / RED 8/13`
✓ — the one guard standing between this predicate and destroyed work is unweakened, on a tree
carrying 10 new instruments. Host-state pin also unchanged at `18, pinned at 18`.

**The bar did not go red on my instruments.** Four workers this fire reddened
`guard_dead_path_frontier` with fixture literals spelling real `.softhouse/…` paths;
`bin/10-fixture.sh` builds every synthetic path from `S=".softhouse"` / `$C` / `$R` / `$B` and
adopts T238's `sweeplib.sh` shape — `set -euo pipefail`, and a **self-check that every branch
the fixture promises actually exists**, exiting 91 otherwise, so no driver can report over a
tree that was never built. The frontier pin was not touched, and the calibration in
`out/70-deadpath-calibration.txt` proves the census read my files rather than skipping them.

Full transcript: `out/90-bar-committed-tree-5bddc3fb.txt`, 860 lines.

---

# 11. INSTRUMENTS

| file | what it establishes |
|---|---|
| `bin/01-cardinals.py` | C-T449-3 and C-T449-4 re-derived at `b102875c` **and** at today's `main` |
| `bin/10-fixture.sh` | the reviewer's own synthetic repo: G, G2, R2, K, **KOWN**, S, **HLOAD**, E — paths through `$S`, self-checking |
| `bin/11-drive.py` | RED / GREEN / **T449-RELAXED** over all eight cases; plants the patch itself, one site, verified unique |
| `bin/12-clock.py` | **C-T456-1** — makes the HOST slow, not the code, and drives REFUSE→demote |
| `bin/13-note-truth.py` | every assertion in the G/G2 notes checked against git; calibrated by a RED leg it catches |
| `bin/20-census.py` | 708 refs / 143 pairs / 25 carriers / **1** relaxation-only, via `git for-each-ref` (a different primitive from T451's) |
| `bin/21-t428-anchor.py` | the decisive T428 ref, per path component, plus the filename counterfactual |
| `bin/22-liveness.py` | **C-T456-3** — reachability by calling `branch_wip`, which is the half T451's `out/22` did not measure |
| `bin/50-direction.py` | per-state polarity transitions RED↔GREEN; exits non-zero on any REFUSE→demote |
| `bin/51-plant-d4.py` | **C-T456-2** — the fourth planted defect, and the two legs that disagree about it |
