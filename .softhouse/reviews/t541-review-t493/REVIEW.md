# T541 — INDEPENDENT REVIEW of T493 (no-op / silent-fire escalation guard)

**Subject:** branch `softhouse/T493-zero-turn-escalation`, tip `d455dea5f355f30fd280bbd8de852ea99f3b7bce`
**Merge base:** `6aa31e5e1a9ee56387759ca298a3c8a6af35e5ab` (`git merge-base origin/main origin/softhouse/T493-zero-turn-escalation`)
**Reviewer worktree:** `/home/user/wt/T541`, branch `softhouse/T541-review-t493`
**Date:** 2026-09-05

---

## VERDICT: **ACCEPT WITH CONDITIONS**

The guard is real, it is wired, the call site **executes**, and it goes RED on all three recorded
outages and GREEN on three controls. It is **not** the eighth unwired guard — I ran the caller and
watched the guard escalate through it. T493's central design finding (that the brief's literal
question goes GREEN on the live outage) is **verified**, as is the producer trap, the shallow
refusal, and the `--now` as-of fix.

Two MAJOR findings stand against the *claims*, not the mechanism: I defeated the classifier by a
footprint attack that T493's "structurally impossible" framing does not cover, and I falsified its
bolded sensitivity claim with a counterexample on the same producer one day later. Seven MINOR
findings follow. None blocks the merge; all five conditions are text or one-line changes.

### Scope instrument used
Every span in this review was taken with the **merge-base form**. The naive
`origin/main..<branch>` form is the instrument that produced T512's filed false accusation twice;
it is not used here.

```
MB=$(git merge-base origin/main origin/softhouse/T493-zero-turn-escalation)   # 6aa31e5e
git diff $MB..origin/softhouse/T493-zero-turn-escalation
```

### Rigs built for this review
Three isolated clones under the scratchpad, none inside the shared checkout:
`full/` (complete clone at the T493 branch), `shallow/` + `shallow-a,b,c` (`--depth=60`),
`attack/` (crafted-history rig, four attack branches). All numbers below were produced in those
clones. **I did not read the handoff until after my own derivation was complete.**

---

## 1. THE DECIDING QUESTION (items 1, 2, 9) — the redesign was NECESSARY

T493 was briefed to answer *"were the last N fires no-ops?"* It replied that the question is
wrong, because outage #3 is fires that **do not run at all**, leaving nothing to classify. I tested
that by isolating axis 1 at the live instant.

```
$ ./.softhouse/guards/no-op-fire-streak.sh --producer local --ref 6aa31e5e --now 2026-09-05T12:17:56Z
  AXIS 1 no-op streak : 0 consecutive no-op fire(s) (threshold 6) -> ok
  AXIS 2 silence      : 49.1h since last REAL commit 5d7ef306 at 2026-09-03T11:09Z (threshold 18h) -> RED
  VERDICT: RED
```

**AXIS 1 ALONE READS `ok (0)` ON THE LIVE OUTAGE.** A guard built to the brief's literal wording
would have reported all-clear on the outage it was filed for. **T493's design finding is CONFIRMED
and the redesign is justified.** I re-derived the mechanism independently: the last local lock-take
is `33f283ed` at 2026-09-03T09:01Z and its open-ended window contains 30 real commits, so counting
no-op fires backward from the newest fire terminates at zero immediately. There are **no local
fires at all** after 2026-09-03 — nothing for a streak detector to grade.

### The producer trap — CONFIRMED

Same ref, same instant, only `--producer` changed:

```
--producer local  ->  AXIS 2 silence 49.1h -> RED    VERDICT: RED    exit 1
--producer any    ->  AXIS 2 silence  0.0h -> ok     VERDICT: GREEN  exit 0
```

The cloud fire commits throughout, so a guard watching the **ref** instead of a **producer** sees a
perfectly healthy repository during a 49-hour local outage. The mandatory `--producer` is
load-bearing, and deriving producer identity from the committer UTC offset (`+08:00` local /
`+00:00` cloud) rather than from subject text is the right call. Census at `6aa31e5e`:
2406 commits at `+08:00`, 120 at `+00:00`, no third offset.

---

## 2. ITEM 11 — THE THREE CORRECTIONS, RE-DERIVED FROM THE HISTORY

I wrote my own analyser (independent parser, my own bookkeeping path set, `--numstat`) rather than
running `derive-windows.py`. Verdicts:

### Correction 1 — outage #1 is 08-24/25/26, not 08-25/26 — **SURVIVES**

Per-UTC-day local-producer census:

| UTC day | fires | real | bookkeeping |
|---|---|---|---|
| 2026-08-23 | 5 | 96 | 13 |
| **2026-08-24** | **6** | **0** | **18** |
| **2026-08-25** | **6** | **0** | **18** |
| **2026-08-26** | **6** | **0** | **18** |
| 2026-08-27 | 6 | 149 | 17 |

2026-08-24 is a 6-fire / 0-real / 18-bookkeeping day, identical in shape to 08-25 and 08-26. The
driver's brief was short by a full day. **T493 is right; the record is now right.**

### Correction 2 — "18 fires" was 18 *commits* = 6 fires/day — **SURVIVES**; the counts 23/13 need a caveat

The fire signature is unambiguous in the log: lock take → `RESUME.md` reconcile → lock release,
three commits per fire, at 08/11/14/17/20/23 local. 6 fires/day × 3 commits = **18 commits/day**.
The driver read commits as fires and overstated the fire count threefold. **Confirmed.**

On the fire counts themselves, `13` is exact and `23` is instant-dependent:

```
$ nofs --producer local --ref 6aa31e5e --now 2026-08-27T06:00:00Z   # T493's RED-1 instant
  AXIS 1 no-op streak : 23   AXIS 2 : 95.2h      -> RED     [reproduces T493 exactly]
$ nofs --producer local --ref 6aa31e5e --now 2026-08-27T14:59:00Z   # peak of the same outage
  AXIS 1 no-op streak : 26                        -> RED
$ nofs --producer local --ref 6aa31e5e --now 2026-09-01T00:00:00Z   # T493's RED-2 instant
  AXIS 1 no-op streak : 13   AXIS 2 : 57.2h      -> RED     [reproduces T493 exactly]
```

My independent maximal-run scan agrees: outage #1's maximal consecutive no-op run is **26 fires**
(2026-08-23T09:00Z → 2026-08-27T15:00Z), outage #2's is **13** (2026-08-29T15:01Z →
2026-09-01T00:01Z), and there is a third 10-fire run (2026-09-01T15:01Z → 2026-09-03T09:01Z) that
the brief did not name. `23` is the streak **as of T493's chosen replay instant**, not the
outage's fire count. See **MINOR-1**.

### Correction 3 — the live outage anchors at `5d7ef306`, 49.1 h, not `10baca08` / ~50 h — **SURVIVES**

```
5d7ef306  2026-09-03T11:09:38Z  offset +08:00  REAL  files=[.softhouse/LOCK, .softhouse/tasks.json]
silence vs now=2026-09-05T12:17:56Z  =  49.14 h        [guard --json: "silence_hours": 49.14]
10baca08  2026-09-03T10:33:35Z  — real local work continued for 36 more minutes after it
```

The anchor correction is solid and matters: `10baca08` is not the last real local commit, so the
driver's escalation to Buyan named the wrong commit. `49.1 h` reproduces to my independent
`49.14 h`. **Confirmed.**

The sub-claim "**12 local commits follow `10baca08`**" is definition-dependent:

```
git log --no-merges --format=... 10baca08..6aa31e5e | grep -c '+08:00'   ->  10
git log            --format=... 10baca08..6aa31e5e | grep -c '+08:00'   ->  12   (incl. merges)
commits with a wall-clock timestamp strictly after 10baca08              ->   8
```

`12` is reachable only by counting merges under ancestry semantics — and two of the ten non-merge
commits (`fc35f4eb` 17:33+08, `0b5e8b81` 18:05+08) carry timestamps *earlier* than `10baca08`
(18:33+08); they are worker-branch commits merged in later. The guard's own instrument uses
`--no-merges` and would say 10. See **MINOR-2**. The material point of the correction is unaffected
by which of 8/10/12 you take.

---

## 3. ITEMS 4 & 7 — ATTACKING THE CLASSIFIER BY CONSTRUCTION

Rig: `attack/`, branches off `5d7ef306`, commits planted with controlled `GIT_COMMITTER_DATE`
at `+0800`, then the real guard run against each branch.

### Attack (a) — bookkeeping footprint, subject reads as real work — **DEFEATED**

```
subject: "T601: port fineract-savings interest posting to Go — 14 golden vectors captured
          against the reference oracle at (19,HALF_UP)"
files:   .softhouse/LOCK

$ nofs --ref attack --explain f29e9bd7
verdict   BOOKKEEPING   (decided from 1 changed path(s); subject text NOT consulted)
    self-churn  .softhouse/LOCK
```

### Attack (b) — real footprint, subject reads as pure bookkeeping — **DEFEATED**

```
subject: "softhouse: wrapper reconciled state after fire 20260905-080001 (exit-protocol enforcement)"
files:   nexus/README.md

$ nofs --ref attack --explain 7f9856bf
verdict   REAL   (decided from 1 changed path(s); subject text NOT consulted)
    carries  nexus/README.md
```

### Attack (c) — a full seven-fire synthetic no-op streak, every subject reading as real — **DEFEATED**

Seven planted fires whose subjects are `"T602: GL accounting journal-entry port — double-entry
invariant proven"`, `"T605: COB batch port — 42 golden vectors captured"` and similar; every fire
touches only `.softhouse/LOCK`:

```
$ nofs --producer local --ref attack2 --now 2026-09-04T23:00:00Z
  AXIS 1 no-op streak : 7 consecutive no-op fire(s) (threshold 6) -> RED
  AXIS 2 silence      : 35.8h -> RED
  VERDICT: RED   exit 1
```

A word-list guard goes GREEN on this branch. The footprint classifier does not. **T493's
structural claim about the two *predicted* attacks is verified by construction, not by reading.**

### Attack (d) — the footprint evasion — **SUCCEEDS. See MAJOR-1.**

### The 37 FN / 146 FP over 2,524 commits — **reproduced exactly**

I re-implemented the measurement with my own parser (`--numstat`, not `--name-only`) rather than
running `classifier-fp-fn.py`:

```
non-merge commits analysed at 6aa31e5e: 2524          [git rev-list --no-merges --count 6aa31e5e = 2524]
footprint truth: REAL=2231  BOOK=293

T493's stated word list : FN = 37 (1.47%)   FP = 146 (5.78%)   agreement 92.7%
T541 independent list   : FN = 29 (1.15%)   FP = 107 (4.24%)   agreement 94.6%
```

**37 and 146 reproduce to the commit.** The specific pair is word-list-dependent — a differently
worded list gives 29/107 — but the *claim* is robust: both reword attacks occur naturally, in the
hundreds, in commits nobody planted. Both of T493's cited natural examples check out:

```
$ nofs --ref 6aa31e5e --explain 7400d9f2
verdict BOOKKEEPING   self-churn .softhouse/LOCK
  ("iter4 dispatch VERIFIED — ten agent worktrees confirmed present by name")
$ nofs --ref 6aa31e5e --explain ffe24c01
verdict REAL          carries .softhouse/tasks.json
  ("wrapper reconciled state after fire 20260829-080002 (exit-protocol enforcement)")
```

---

## 4. ITEM 8 — THE `--now` AS-OF FILTER

**The bug was real.** I removed only the two-line as-of filter from a copy and re-ran T493's own
RED-1 replay:

```
$ cp guard /tmp/nofs-nofilter.sh   # then delete: commits = [c for c in commits if c['dt'] <= now]
$ /tmp/nofs-nofilter.sh --producer local --ref 6aa31e5e --now 2026-08-27T06:00:00Z
  AXIS 1 no-op streak : 11 -> RED
  AXIS 2 silence      : -173.2h since last REAL commit 5d7ef306 at 2026-09-03T11:09Z -> ok
```

Negative silence, axis 2 reporting **ok** on an outage, and axis 1 reading 11 instead of 23. The
fix is genuine and load-bearing.

**No other path can see the future.** I probed every route into the commit set:

```
$ nofs --ref 6aa31e5e --now 2026-08-27T06:00:00Z --explain 5d7ef306     # a FUTURE commit
REFUSE — no commit matching '5d7ef306' ...                              exit 2
$ nofs --ref 6aa31e5e --now 2026-08-27T06:00:00Z --explain 2b6cbe59     # a PAST commit
verdict REAL   carries .softhouse/tasks.json                            exit 0
$ nofs --ref 6aa31e5e --now 2026-01-01T00:00:00Z                        # before the root commit
REFUSE — no commits at or before --now ... (history begins 2026-08-17)  exit 2
```

`pool`, `reals`, `fires` and the report's `history: N commits` line are all derived after the
filter (2057 commits reported at `--now 2026-08-28`, 1331 at `--now 2026-08-27`, 2524 with no
`--now`). `silence` cannot be negative by construction because `last_real.dt <= now`.
Both refusals exit **2**, never 0.

---

## 5. ITEM 5 — THE SHALLOW-CLONE TRAP

I built my own `--depth=60` clone and first reproduced the silent failure the guard exists to
prevent:

```
$ git clone --depth=60 --branch softhouse/T493-zero-turn-escalation file:///home/user/gerege-nbfi/.git shallow
shallow=true  commits=167  oldest visible=2026-08-30T20:03:38+08:00
  --since=2026-08-29 -> 167 commits (rc=0)
  --since=2026-08-22 -> 167 commits (rc=0)
  --since=2026-08-15 -> 167 commits (rc=0)
  --since=2026-07-01 -> 167 commits (rc=0)
```

**Every window returns the same count with no error and rc 0**, and the oldest visible commit is
2026-08-30 — **outage #1 (08-24/25/26) is entirely invisible.** T493 reported 168 on its own clone;
I get 167 from a differently-targeted `--depth=60`. Immaterial: the phenomenon is identical and
confirmed.

Then the guard, on three copies of that shallow clone:

```
(a) shallow + --no-fetch
    REFUSE — history is SHALLOW and --no-fetch was given ...
    REFUSE IS NOT GREEN. No verdict was reached.                        exit 2
(b) shallow + origin set to file:///nonexistent/nope.git
    attempting 'git fetch --unshallow' ... REFUSE — history is STILL SHALLOW    exit 2
    (still shallow afterwards: true — it did not fake a recovery)
(c) shallow + reachable remote
    "unshallowed by this guard via 'git fetch --unshallow'"  167 -> 2976 commits
    AXIS 1 : 23 -> RED   AXIS 2 : 95.2h -> RED   exit 1
    — byte-identical verdict to the full clone at the same --now
```

**REFUSE is exit 2 in both blind cases, never 0**, and the recovery path reaches the same answer a
full clone does. This is the strongest part of the work.

---

## 6. ITEM 3 — RED/GREEN RE-DRIVEN ON REAL HISTORY

All six of T493's graded cases reproduce **exactly** at its stated instants, on my own clone:

| case | producer | `--now` | AXIS 1 | AXIS 2 | exit |
|---|---|---|---|---|---|
| RED-1 outage #1 | local | 2026-08-27T06:00:00Z | RED (23) | RED (95.2 h) | 1 |
| RED-2 outage #2 | local | 2026-09-01T00:00:00Z | RED (13) | RED (57.2 h) | 1 |
| RED-3 outage #3 **live** | local | 2026-09-05T12:17:56Z | **ok (0)** | **RED (49.1 h)** | 1 |
| GREEN-B control | cloud | 2026-09-04T13:40:00Z | ok | ok (0.0 h) | 0 |
| GREEN-C control | local | 2026-09-03T11:30:00Z | ok | ok (0.3 h) | 0 |
| GREEN (mine) productive day | local | 2026-08-28T23:59:00Z | ok | ok (4.6 h) | 0 |
| GREEN (mine) cloud, live instant | cloud | 2026-09-05T12:17:56Z | ok | ok (0.0 h) | 0 |

Plus a fourth RED I found that the brief did not name: **2026-09-02 is also a 6-fire / 0-real day**
(`--now 2026-09-02T23:59:00Z` → AXIS 1 = 7 → RED). The green controls are real controls: the same
instrument, same ref, same thresholds, returning exit 0.

---

## 7. ITEMS 2 & 6 — THE WIRING. **IT IS NOT THE EIGHTH UNWIRED GUARD.**

A diff that adds a call site is not evidence the call site runs, so I extracted the block verbatim
and executed it under the caller's own shell and flags:

```
$ sed -n '1689,1743p' .softhouse/bin/fire-program.sh > block.zsh
$ cat harness.zsh
  #!/bin/zsh
  set -uo pipefail            # byte-identical to fire-program.sh:17
  REPO="$1"; log(){ printf '%s %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
  log "harness: BEFORE the T493 block"; source "$2"
  log "harness: AFTER the T493 block — the fire CONTINUED (rc of block = $?)"
$ zsh harness.zsh <full-clone> block.zsh
```

Output, real guard against real history:

```
12:52:30Z harness: BEFORE the T493 block
12:52:33Z no-op-fire-streak[local]: **RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**
12:52:33Z   | AXIS 1 no-op streak : 0 consecutive no-op fire(s) (threshold 6) -> ok
12:52:33Z   | AXIS 2 silence      : 49.7h since last REAL commit 5d7ef306 ... -> RED
12:52:33Z   | VERDICT: RED — this producer is not advancing the migration
12:52:36Z no-op-fire-streak[cloud]: GREEN — that producer is advancing
12:52:36Z harness: AFTER the T493 block — the fire CONTINUED (rc of block = 0)
```

**The guard fires THROUGH the call site and the finding reaches the fire log.** Every branch drives
correctly, against stub guards returning each code:

| guard exit | call site behaviour | fire continues? |
|---|---|---|
| 0 | `GREEN — that producer is advancing` | yes |
| 1 | `**RED — …**` + full output tee'd line-by-line + `osascript` attempt | yes |
| 2 | `REFUSE (exit 2) — NO VERDICT WAS REACHED. This is NOT a pass.` | yes |
| 3 | `UNEXPECTED exit 3 — treat as no verdict, not as a pass` | yes |
| 141 | `UNEXPECTED exit 141 — …` (the SIGPIPE case the guard's own comment anticipates) | yes |
| absent / not `-x` | `guard NOT PRESENT or not executable at …` | yes |

**REFUSE is never reported as a pass.** The block never blocks the fire — verified, and correct,
since `fire-program.sh` runs `set -uo pipefail` with **no `-e`** (line 17), so a RED exit 1 out of
a command substitution cannot abort the wrapper. That is load-bearing and I checked it rather than
assuming it.

I also checked the silent-skip trap that would have made all of this decorative:

```
$ git ls-tree origin/softhouse/T493-zero-turn-escalation .softhouse/guards/no-op-fire-streak.sh
100755 blob c57ed377…   .softhouse/guards/no-op-fire-streak.sh
```

Mode **100755** in the tree, so the `[[ -x ]]` test passes after checkout on the Mac. Had it landed
644 the block would have logged "not executable" forever and this would have been guard number
eight. It did not.

### Is "covers 2 of 3 occurrences" accurate, or generous? — **ACCURATE, and if anything conservative**

I dated the first trip for each covered outage:

```
--now 2026-08-24T03:05Z -> AXIS 1 = 5 (ok)  but VERDICT already RED (axis 2)
--now 2026-08-24T06:05Z -> AXIS 1 = 6 -> RED                    outage #1 caught same day
--now 2026-08-30T09:05Z -> AXIS 1 = 5 (ok)  but VERDICT already RED (axis 2)
--now 2026-08-30T12:05Z -> AXIS 1 = 6 -> RED                    outage #2 caught same day
```

Both outages ran the local fire six times a day and the lock take/release commits prove those fires
reached the block's position in the file. Each would have escalated within hours of the outage
starting — days before the human found them by hand. Outage #3 is not covered and T493 says so in
the block's own comment and in the handoff, without being asked.

**On the circularity charge:** a guard whose only call site is inside the thing it monitors *is*
circular, and T493 states that plainly rather than claiming coverage it does not have — the comment
reads `CANNOT — the TOTAL SILENCE mode… Do not read this block as covering the live 2026-09-03
outage.` The non-circular direction is filed as **T543** (`executor: user`), with paste-ready
prompt text. That is the correct disposition: the local wrapper covers the cloud producer and the
no-op mode; only the cloud Routine can cover local silence. See **MINOR-6** and **MINOR-7** for two
reachability qualifications T493 did not name.

---

## 8. FINDINGS

### MAJOR-1 — The classifier IS defeatable: one valueless write per fire to any non-bookkeeping path drives it fully GREEN

T493's framing is that both reword attacks are structurally impossible because the subject is never
an input. That is true and I verified it. But the footprint is an input, and the footprint is
attackable. I planted eight consecutive fires that advance **nothing**, each adding one valueless
line to a non-bookkeeping tracked path:

```
per fire:  .softhouse/LOCK take
           docs/softhouse-migration-pipeline.md  +="\n<!-- heartbeat N -->\n"   <- the payload
           .softhouse/LOCK release

$ nofs --producer local --ref attack4 --now 2026-09-04T23:00:00Z
  in window    : 1375 real, 229 bookkeeping, 75 fire(s) graded
  AXIS 1 no-op streak : 0 consecutive no-op fire(s) (threshold 6) -> ok
  AXIS 2 silence      : 10.8h since last REAL commit e755018c -> ok
  VERDICT: GREEN — producer is advancing                              exit 0
```

**Eight no-op fires, zero real work, GREEN on both axes.** This is not purely hypothetical — the
wrapper is already close to it in production:

```
commits whose ONLY path is .softhouse/tasks.json : 344 of 2524 (13.6%)
  ... of which the subject says "reconciled"     :   9
```

`ffe24c01` is one of those nine — a wrapper *reconcile* whose sole file is `tasks.json`, scored
**REAL**, and it is the commit that anchors outage #2's silence window. If the wrapper's reconcile
step ever moves from `RESUME.md` to `tasks.json` (or writes both), every future no-op fire scores
real and **both axes go GREEN through an outage**. T493 disclosed the `tasks.json` judgement call
specifically and filed T545 for it; it did **not** disclose the general shape — that *any*
non-bookkeeping path with a valueless write defeats the guard entirely. B-11/P-104 is this
program's standing record that classifiers get defeated in practice, and "structurally impossible"
will be read more broadly than it is true.

**Condition C1.** Record this in the guard's `HOW A COMMIT IS CLASSIFIED` header beside the
impossibility claim: *reword attacks are structurally impossible; a footprint attack is not, and a
producer that writes one valueless line per fire outside the bookkeeping set defeats both axes.*
Fold the general shape into **T545**'s scope, which currently reads as being only about
`tasks.json`.

### MAJOR-2 — The bolded sensitivity claim "No verdict is sensitive to it" is false; I have a counterexample

Handoff §4.3 measures the `tasks.json` reclassification across six graded cases, prints
`RED-1 1→1 … GREEN-C 0→0 (all SAME)`, and then generalises in bold: **"No verdict is sensitive to
it."** At T493's own six instants that holds — I reproduced it, including GREEN-B staying GREEN at
2026-09-04T13:40Z. One day later on the same producer it does not:

```
RE='^\.softhouse/(LOCK|RESUME\.md|tasks\.json)$|^\.softhouse/(state|logs|runs)/'

--producer cloud --now 2026-09-05T12:17:56Z
  default                        : AXIS 2  0.0h -> ok    VERDICT: GREEN
  NOFS_BOOKKEEPING_RE="$RE"      : AXIS 2 22.7h -> RED   VERDICT: RED     <- FLIPS
```

The cause is structural, not incidental: the cloud fire's dispatch-record commits are
`LOCK + tasks.json` only —

```
6aa31e5e  .softhouse/LOCK .softhouse/tasks.json   "T493 DISPATCHED because its defect is live…"
c42cb236  .softhouse/LOCK .softhouse/tasks.json   "softhouse: T538 merged — contiguity is not…"
a19ea967  .softhouse/LOCK .softhouse/RESUME.md .softhouse/tasks.json
```

— so under T545's alternative **every cloud dispatch record becomes bookkeeping and the cloud
producer reads RED on an ordinary working day.** That is a false-alarm risk T545 must weigh, and
the handoff currently tells its adjudicator the choice is verdict-neutral. The measurement was
honest; the generalisation from six points is not supported.

**Condition C2.** Rewrite the claim to its true scope — *none of the six graded verdicts flips at
the instants graded* — and attach the counterexample above to **T545**.

### MINOR-1 — "23 consecutive no-op fires for outage #1" is instant-scoped; the guard reports 26

Handoff §correction 2 states 23 as the outage's fire count. 23 is the streak at
`--now 2026-08-27T06:00Z`; the maximal streak the guard itself reports for that outage is **26**
(`--now 2026-08-27T14:59Z`), and my independent maximal-run scan agrees (26 fires,
2026-08-23T09:00Z → 2026-08-27T15:00Z). Outage #2's 13 is both the replay value and the maximum, so
that one is exact. The driver has taken "23" into the record as *the* count.
**Condition C3.** State 26 as the outage's streak, or name the instant that produces 23.

### MINOR-2 — "12 local commits follow `10baca08`" holds only under ancestry-with-merges

`--no-merges` gives 10 (the guard's own view), wall-clock gives 8, ancestry-with-merges gives 12;
two of the ten (`fc35f4eb`, `0b5e8b81`) are *older* than `10baca08` by committer date. The
correction's substance is unaffected. **Condition C3.** Say which count is meant.

### MINOR-3 — the handoff points at the wrong task id

Handoff §7 and §"Authority" file the cloud-Routine work as **T542**. In `tasks.json` on `main`
that work is **T543** (`executor: user`); **T542** is an unrelated `money.go` citation task. A
reader following the handoff lands on the wrong task. **Condition C4.**

### MINOR-4 — the `--explain` refusal calls an as-of-filtered search "the full history"

```
$ nofs --ref 6aa31e5e --now 2026-08-27T06:00:00Z --explain 5d7ef306
REFUSE — no commit matching '5d7ef306' in 6aa31e5e (looked in the full --no-merges history
of 6aa31e5e, 1331 commits, oldest 2026-08-17T18:52:14+08:00)
```

The search set was 1331 of 2524 commits because `--now` filtered it, but the message says "the
full … history". Exactly where `--now` is in play, this tells an operator a commit is absent from
history when it is merely later. **Condition C5.** Say "as of `--now`" and print both counts.

### MINOR-5 — the header promises a truncation refusal that no code path can produce

The window block's comment says a lookback reaching past the start of history "gets the same
refusal", but `root_held = True` is a hard-coded constant that is never read, and `truncated` only
reaches the report:

```
$ nofs --producer local --ref 6aa31e5e --now 2026-08-28T23:59:00Z
  window : last 14 day(s) …   *** TRUNCATED: history begins inside the window ***
  VERDICT: GREEN                                                      exit 0
```

The **behaviour is correct** — a young repo should not refuse, and genuine blindness is caught at
STEP 0 — but the comment overstates it, and `root_held` and `future` are both dead. Non-blocking.

### MINOR-6 — `--probe` exits before the call site

`fire-program.sh:1679-1681` exits on `PROBE_ONLY` at line 1681; the guard block starts at 1689. The
touch-nothing health check is the natural place to ask "is the other producer alive?", and the
guard touches nothing (bar a possible self-unshallow). An operator probing the fire gets no streak
verdict. Non-blocking; worth considering when T543/T544 land.

### MINOR-7 — 15 `exit N` paths precede the call site

```
$ awk 'NR<1714 && /^[[:space:]]*exit [0-9]/ {print NR}' .softhouse/bin/fire-program.sh | wc -l
15
```

A fire that dies in preflight — e.g. the lock-reader self-test FATAL at 1670 — never runs the
guard, and a fire that *consistently* dies in preflight is itself an outage this guard would then
miss. This is a narrower instance of the circularity T493 correctly named for total silence, and it
does not affect outages #1 and #2 (their lock take/release commits prove those fires reached the
block). Worth one sentence in the block comment.

---

## 9. ITEM 10 — GRADING THE SELF-DECLARED 0/0

T493 declares its own classifier's FP/FN as **0/2524 by construction** and labels it *"a caveat
rather than a result"*, noting the footprint *is* the ground truth in that comparison so the number
is definitionally zero and proves nothing.

**The honesty is necessary and correct, but not sufficient on its own — and T493 knew that and
supplied the missing half itself.** A self-declared 0/0 is not grading; what makes it defensible is
that T493 graded the footprint classifier against **external** truth instead (the recorded outage
windows, where it must report 0 real, and the recorded productive windows, where it must report
many) and published the drives.

**Genuinely external grading was still owed, and this review discharges it — with a non-zero
result.** Four constructed attacks: (a) reword-to-real, (b) reword-to-bookkeeping, (c) a seven-fire
synthetic streak with all-real subjects — all three **defeated**; (d) the valueless-write footprint
evasion — **succeeds** (MAJOR-1). So the correct entry for the record is not 0/0 and not "immune":
it is *immune to subject rewording, defeatable by footprint padding, and the second half was found
by an external reviewer, not by self-report.* With MAJOR-1's condition applied, the disclosure
becomes complete and I regard item 10 as closed.

---

## 10. THE TWO THINGS T493 DID NOT DO

### The `update_trigger` refusal — **CORRECT. Uphold it.**

T493 held `update_trigger` and could have rewritten Buyan's scheduled Routine to add the
cross-fire call. It declined, on the grounds that its instructions came from the softhouse driver
**agent**, and an agent's message is not the user's consent.

That is right, and it is right for the reason it gives. No agent message is ever a user's approval;
silently rewriting a human's scheduled automation on another agent's say-so is not a worker's call
to make. Crucially, T493 did **not** use the refusal as cover for dropping the work: it wrote the
exact prompt text to paste, named the Routine, and specified the acceptance test (fire the Routine
manually while the local producer is RED and confirm the escalation appears in the report). The
driver filed it as **T543**, `executor: user`. Correct on both halves — refuse the act, deliver the
artefact. This is the behaviour the program should want, and the review record should say so.

### The `ready-tasks.py` declination — **SOUND, and declining to file was itself correct under P-89**

T493 argues `ready-tasks.py` answers "which tasks are runnable" and only ever runs *inside* a fire
that is already alive, so a liveness watchdog there reproduces P-45 exactly. I checked the shape of
the claim and agree: a watchdog whose only caller cannot execute during the outage it watches is
the defect, not the fix — filing it would have queued work whose completion produces a **ninth**
guard wired to a caller that cannot fire when it matters.

P-89 says *a paragraph is not a task* — it does not say every idea must become a task. It bites on
work that is **owed and deferred**, not on work that is **considered and rejected**. T493 wrote the
rejection and its reason into the handoff under a heading that says it is deliberate, which is the
P-89-compliant handling of a rejected idea: the record shows the decision and its reasoning, so a
later agent can overturn it without rediscovering it. Had it stayed silent, that would be the
defect. **Correct.**

For completeness, the work T493 *could not* do is filed rather than recommended — the P-89 test
that actually applies here:

```
T543 | pending | user  | WIRE THE CLOUD ROUTINE TO WATCH THE LOCAL FIRE — the only direction
                         that catches a total-silence outage
T544 | pending | agent | DRIVE THE osascript ESCALATION ON THE MAC — wired by T493, never executed
T545 | pending | agent | ADJUDICATE whether a tasks.json-only commit is bookkeeping or real work
```

Three dispatchable tasks with owners in `tasks.json`, not three paragraphs in a handoff. **P-89
satisfied.**

---

## 11. SCOPE AND THE NON-NEGOTIABLES

```
$ git diff --name-status 6aa31e5e..origin/softhouse/T493-zero-turn-escalation
M  .softhouse/bin/fire-program.sh
A  .softhouse/guards/no-op-fire-streak.sh
A  .softhouse/capture/t493-zero-turn-escalation/{classifier-fp-fn.py,classifier-fp-fn.txt,
     derive-windows.py,outage-windows.txt,red-green-drives.txt,shallow-refusal.txt,wiring-drives.txt}
A  .softhouse/handoff/T493-zero-turn-escalation.md
```

**10 files, every one inside T493's permitted paths.** `tasks.json` untouched — confirmed, and it
is why T493 could not file T543/T544/T545 itself. Forbidden-path grep (`ready-tasks.py`,
`check-branch-published.py`, `conformance.sh`, `guards/ledgerguard/`, `apps/savings/`,
`tasks.json`): **no match.** The driver's measurement stands.

**Money is integer minor units — SATISFIED.** Grepped on the diff regardless of task, as required:

```
$ git diff 6aa31e5e..<branch> | grep -nE '^\+.*(float|Float|\bdouble\b|decimal\.Decimal)'
846:+silence_h = float(os.environ['NOFS_A_SILENCE'])      # silence threshold, HOURS
848:+lookback  = float(os.environ['NOFS_A_LOOKBACK'])     # lookback window, DAYS
```

Both `float()` uses are **duration parameters, not money** — a threshold in hours and a window in
days. The only other arithmetic is `(now - last_real).total_seconds()/3600.0` (elapsed hours) and
integer commit counts. The guard reads git metadata only: shas, committer timestamps, paths, and
insertion/deletion counts. **No monetary value, amount, currency, schema column, API field or test
fixture appears anywhere in the diff.** Remaining `float` hits are prose about
`guard_no_float_in_vectors` (B-11) and the word "double-counts". Other non-negotiables grepped
(`first_name`/`last_name`, Stripe/Plaid/Lithic/Persona, `ojdbc`/`oracle.jdbc`/MySQL/MariaDB/`:1521`):
**no match.** Syntax: `bash -n` clean on the guard, `zsh -n` clean on `fire-program.sh`.

---

## 12. CONDITIONS

| # | From | Change |
|---|---|---|
| **C1** | MAJOR-1 | Record the footprint evasion in the guard header beside the "structurally impossible" claim; widen **T545** from `tasks.json` to the general shape. |
| **C2** | MAJOR-2 | Rescope "No verdict is sensitive to it" to the six graded instants; attach the cloud-producer counterexample to **T545**. |
| **C3** | MINOR-1,2 | State outage #1's streak as **26** (or name the instant giving 23); say which count "12 commits" means. |
| **C4** | MINOR-3 | Fix the handoff's **T542 → T543** cross-reference. |
| **C5** | MINOR-4 | `--explain` refusal must say "as of `--now`", not "the full history". |

MINOR-5, -6 and -7 are recorded, not conditions.

---

## 13. WHAT I RAN TO AGREE, WHERE I AGREE

An unsupported ACCEPT is worth nothing, so, explicitly: I did not take the handoff's word for any
number. I built three clones and an attack rig; I re-derived the 2,524 commit census, the per-day
outage table, the fire reconstruction, the 37/146 word-list rates and the 49.14 h silence with my
own parser; I removed the as-of filter to reproduce the -173.2 h bug it fixes; I built a
`--depth=60` clone and drove all three refusal paths; I planted four attack branches and defeated
three of them; and I extracted the call site and executed it under `zsh` against six different
guard exit codes. Every one of T493's six graded verdicts reproduced exactly at its stated
instants. The three corrections to the driver's numbers all survive re-derivation, with the two
scoping caveats in MINOR-1 and MINOR-2.

**The guard escalates. It is wired, the wiring runs, REFUSE is never a pass, and it would have
caught two of the three recorded outages within hours. Accept, with the five conditions above.**

---

## 14. PUSH PROOF

Review committed as `a3148e12645abc211699e9ccecb42568a892e3ec` and pushed to origin.

```
$ git push -u origin softhouse/T541-review-t493
To https://github.com/buya-v/gerege-nbfi
 * [new branch]        softhouse/T541-review-t493 -> softhouse/T541-review-t493

$ git ls-remote --heads origin softhouse/T541-review-t493
a3148e12645abc211699e9ccecb42568a892e3ec	refs/heads/softhouse/T541-review-t493
```

The branch reached origin.
