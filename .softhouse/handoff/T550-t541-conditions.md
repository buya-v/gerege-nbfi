# T550 — T541's conditions on T493 applied: REAL is now EARNED, not inherited

**Branch:** `softhouse/T550-t541-conditions` (based on `main` at `a6b11f1b`)
**Worktree:** `/home/user/wt/T550`
**Subject review:** `.softhouse/reviews/t541-review-t493/REVIEW.md` (ACCEPT WITH CONDITIONS, C1–C5)
**Subject handoff:** `.softhouse/handoff/T493-zero-turn-escalation.md`
**Files changed:** `.softhouse/guards/no-op-fire-streak.sh`, `.softhouse/bin/fire-program.sh`,
`.softhouse/capture/t493-zero-turn-escalation/t550-*`, this handoff. Nothing else.

---

## 0. THE SHORT VERSION

T541 defeated T493's classifier by **footprint padding**: eight consecutive no-op fires, each
appending one valueless line to `docs/*.md`, read `AXIS 1 ok(0) / AXIS 2 ok(10.8h) / GREEN /
exit 0`. I reproduced that attack against the T493 guard before touching anything, and it
reproduces exactly.

The repair copies **T536's shape**, not T527's. T527 blocked one phrasing and T528 broke it with a
second; T536 closed the class by **inverting the default** — every extracted sha starts
`REFERENCE`, and `LANDING` must be *earned* by an explicit promotion surviving two vetoes. Here:

> **Every commit is BOOKKEEPING by default. `REAL` must be earned by an explicit promotion —
> a path on the declared MIGRATION SURFACE — surviving three vetoes.**

Five padding attacks were driven against both guards. **All five turn the streak GREEN on the T493
guard and RED on the T550 guard**, including two whose payload is novel on every beat, which no
repeat-detector can see. Every no-regression item T541 verified by drive is re-driven below and
holds, **to the figure**.

I did **not** close the class absolutely, and I do not claim to. §5 states exactly what is still
open and why no test over git metadata can close it.

---

## 1. MAJOR-1 — THE FOOTPRINT-PADDING CLASS

### 1.1 The attack rig

Isolated clone of this worktree; five branches planted off `5d7ef306` (the live outage anchor,
2026-09-03T11:09:38Z). Each branch carries **eight consecutive no-op fires** at `+0800`, three
commits per fire — `.softhouse/LOCK` take, one padding payload, `.softhouse/LOCK` release — exactly
the fire signature T541 established (6 fires/day, 3 commits each). Planting script committed as
`.softhouse/capture/t493-zero-turn-escalation/t550-plant-attacks.sh`; the full transcript is
`t550-padding-attacks.txt`.

| branch | payload, once per fire | who invented it |
|---|---|---|
| `attack-t541` | `+= "<!-- heartbeat N -->"` to `docs/softhouse-migration-pipeline.md` | **T541's exact attack** |
| `attack-mine-e` | `+= "// heartbeat N"` to `nexus/internal/apps/loanproduct/doc.go` — the same heartbeat aimed **inside** the surface | T550 |
| `attack-mine-f` | a **new file per fire**, `.softhouse/capture/heartbeat/beat-N.txt`, so no path ever repeats | T550 |
| `attack-mine-g` | **one novel substantive line** per fire inside the surface — no template repeat | T550 |
| `attack-mine-h` | **five novel substantive lines** per fire inside the surface — the hardest padding I could write | T550 |

`BEFORE` is the T493 guard extracted verbatim
(`git show a6b11f1b:.softhouse/guards/no-op-fire-streak.sh`); `AFTER` is the guard on this branch.
Both at `--producer local --now 2026-09-04T23:00:00Z`.

### 1.2 BEFORE — the T493 guard, defeated by all five

```
$ ./guard-BEFORE.sh --producer local --ref attack-t541 --now 2026-09-04T23:00:00Z
  in window    : 1375 real, 229 bookkeeping, 75 fire(s) graded
  AXIS 1 no-op streak : 0 consecutive no-op fire(s) (threshold 6) -> ok
  AXIS 2 silence      : 12.0h since last REAL commit 62bcac3a at 2026-09-04T11:02Z (threshold 18h) -> ok
  VERDICT: GREEN — producer is advancing                                   exit=0

$ ./guard-BEFORE.sh --producer local --ref attack-mine-e ...   AXIS 1 ok(0) / AXIS 2 ok(12.0h) / GREEN / exit 0
$ ./guard-BEFORE.sh --producer local --ref attack-mine-f ...   AXIS 1 ok(0) / AXIS 2 ok(12.0h) / GREEN / exit 0
$ ./guard-BEFORE.sh --producer local --ref attack-mine-g ...   AXIS 1 ok(0) / AXIS 2 ok(12.0h) / GREEN / exit 0
$ ./guard-BEFORE.sh --producer local --ref attack-mine-h ...   AXIS 1 ok(0) / AXIS 2 ok(12.0h) / GREEN / exit 0
```

`1375 real / 229 bookkeeping / 75 fires graded` is T541's own figure, reproduced to the commit. The
class is confirmed by drive, not by reading: **eight no-op fires, zero real work, GREEN on both
axes, exit 0** — for five different paddings, four of which T541 never wrote.

### 1.3 AFTER — the T550 guard, RED on all five

```
$ ./guard-AFTER.sh --producer local --ref attack-t541 --now 2026-09-04T23:00:00Z
  in window    : 881 earned-real, 723 bookkeeping, 75 fire(s) graded
  vetoed       : 8 null-payload, 54 repeat-payload, 67 thin-payload (<8 substantive lines)
                 — anchored commits that did NOT promote
  UNCLASSIFIED-PATH: 28 path(s) carried work in window but are not on the surface, so they never
                 promote: .softhouse/tasks.json x304, .softhouse/program.json x38, ...
  AXIS 1 no-op streak : 8 consecutive no-op fire(s) (threshold 6) -> RED
  AXIS 2 silence      : 12.0h since last commit carrying anything 62bcac3a (threshold 18h) -> ok
  AXIS 3 padded adv.  : 35.9h since last EARNED commit d355d422 (threshold 36h) -> ok
  VERDICT: RED — this producer is not advancing the migration               exit=1
```

| branch | BEFORE | AFTER |
|---|---|---|
| `attack-t541` (T541's exact attack) | AXIS 1 ok(0) · GREEN · **exit 0** | AXIS 1 **RED (8)** · RED · **exit 1** |
| `attack-mine-e` | AXIS 1 ok(0) · GREEN · exit 0 | AXIS 1 **RED (8)** · RED · exit 1 |
| `attack-mine-f` | AXIS 1 ok(0) · GREEN · exit 0 | AXIS 1 **RED (8)** · RED · exit 1 |
| `attack-mine-g` | AXIS 1 ok(0) · GREEN · exit 0 | AXIS 1 **RED (8)** · RED · exit 1 |
| `attack-mine-h` | AXIS 1 ok(0) · GREEN · exit 0 | AXIS 1 **RED (8)** · RED · exit 1 |

Which mechanism kills which attack, audited one commit at a time with `--explain`:

* `attack-t541` — **NO ANCHOR.** `docs/softhouse-migration-pipeline.md` is not on the migration
  surface, so the commit is never even offered for promotion. Note the shape of that statement:
  docs was not *added to a blocklist*, it was simply **never added to the allowlist**, and neither
  is any other path anybody invents.
* `attack-mine-e` — **VETO 3 THIN PAYLOAD** speaks first at the shipped floor
  (`1 substantive added surface line(s), floor is 8`). **VETO 2 kills it independently**: at
  `--min-subst-lines 1`, with VETO 3 disabled, the branch is still `AXIS 1 RED (7)` because
  `// heartbeat 1` and `// heartbeat 2` normalise to the same payload —
  `VETO 2 REPEAT PAYLOAD — normalised payload f54cf09c9d1f70a1 already promoted at 24bd36d5`.
  Only the first beat ever promotes.
* `attack-mine-f` — same on both counts (`already promoted at b5990039`), and the rotating filename
  buys nothing, because it is the **payload** that is normalised, not the path.
* `attack-mine-g` / `attack-mine-h` — novel on every beat, so **VETO 2 cannot see them at all**;
  nothing repeats. Killed by **VETO 3 THIN PAYLOAD**: 1 and 5 substantive added surface lines
  against a floor of 8.

Every one of those verdicts was audited one commit at a time with `--explain`, transcript in
`t550-padding-attacks.txt`. Each veto was also driven in isolation, so none of them is carried by
another.

### 1.4 The design — why `REAL` is now earned

```
DEFAULT   Every commit is BOOKKEEPING. Nothing is real by being seen.

ANCHOR    A commit is OFFERED for promotion only if at least one path it changes lies on the
          declared MIGRATION SURFACE (NOFS_SURFACE_RE):
              ^nexus/                                  the Go module — the product itself
              ^\.softhouse/(capture|vectors)/           captured oracle output, golden vectors
              ^\.softhouse/(handoff|reviews)/           worker and reviewer deliverables
              ^\.softhouse/(guards|bin)/                the enforcement and pipeline machinery
              ^\.claude/                                the pipeline's own skills
              ^docs/adr/                                ratified DEC-n contract records
          This is an ALLOWLIST. A path nobody enumerated does NOT promote, is printed as
          UNCLASSIFIED-PATH, and therefore fails toward RED (escalate), never toward GREEN.

VETO 1    NULL PAYLOAD.   The lines the commit ADDS to its surface paths are all blank or bare
                          markers. A change that adds no readable line advanced nothing.
VETO 2    REPEAT PAYLOAD. The added surface payload, normalised (case folded, whitespace
                          collapsed, digit/hex runs -> '#'), already promoted for this producer
                          inside the lookback window. A heartbeat beats once.
VETO 3    THIN PAYLOAD.   Fewer than NOFS_MIN_SUBST_LINES (8) substantive added surface lines.
                          A MATERIALITY floor: a size, not a shape — it names no path, no wording
                          and no attack already seen.
```

**Why this is the inversion and not another blocklist.** T493's rule was *"real unless every path
is in the self-churn set"* — a blocklist with a permissive default, whose escape set is infinite
(every path nobody listed). T550's rule is *"bookkeeping unless a path is in the surface set AND
the payload survives three vetoes"* — an allowlist with a refusing default, whose escape set is
finite and enumerated in one line of the guard, printed in every report. Adding a path to the
surface is a diff a reviewer sees; walking out of a blocklist is a filename nobody sees.

**Why the failure direction is safe.** For a liveness watchdog the conservative verdict is RED
(escalate), and every uncertainty in the new classifier resolves that way: an unknown path does not
promote, an unreadable payload does not promote, a crash now REFUSES (exit 2) instead of leaking
python's exit 1, which a caller reads as RED. The guard does not go quiet when it cannot decide.

**Why AXIS 2 deliberately keeps T493's old, forgeable rule.** AXIS 2 answers the weaker question
"has this producer committed *anything at all* beyond its own churn?", and it is **monotone: it can
only add RED**. The verdict is the OR of three axes, so a forged promotion can silence AXIS 2 but
cannot silence AXIS 1 or AXIS 3. Keeping it also preserves every silence figure T493 published and
T541 re-derived, so the two records still compare line for line (§4).

**AXIS 3 — PADDED ADVANCE (new).** Hours since the last EARNED promotion, default threshold 36 h.
It exists for the padder that never takes the lock — no fires to grade, so AXIS 1 sees nothing —
while committing continuously, so AXIS 2's clock never runs. That producer now reads RED after 36 h.

### 1.5 VETO 3's floor is MEASURED, not chosen

`.softhouse/capture/t493-zero-turn-escalation/t550-materiality-floor.py`, over the whole history:

```
local: fires=88   longest run of CLEARED-BUT-THIN(<=2 subst lines) fires = 0
       min over cleared fires of (max substantive lines in its promotions) = 12; cleared fires=36
cloud: fires=4    longest run of CLEARED-BUT-THIN fires = 0
       min over cleared fires of (max substantive lines in its promotions) = 27; cleared fires=4
```

The thinnest promotion that has **ever** cleared a fire in this repository carries **12**
substantive added surface lines. The shipped floor is **8** — a 1.5× margin under the observed
minimum, and the longest cleared-but-thin run in the entire history is **zero**. The full battery
was driven at floors 3 and 8 and every verdict and every figure is identical, so the floor costs
nothing measured. It was set from that measurement; it is not taste, and re-measuring it is one
command.

Data that killed a *better-sounding* design: I first tried requiring **protocol corroboration** —
a promotion must have arrived off `main`'s first-parent chain, i.e. authored on a branch and
merged, which a padding fire cannot forge without running the whole pipeline protocol. The history
refuses it. On 2026-09-01 the local producer landed **12 trunk-authored** commits — `nexus/go.mod`
+ `pgx` repositories, the A1 posting engine, the loan allocation arithmetic, the Tier-B ports, the
Tier-D vector mine — with **zero** off-first-parent commits that day. A corroboration rule would
have graded one of the most productive days in the program as a no-op streak. Recorded here so the
next agent does not re-derive it.

---

## 2. MAJOR-2 — THE FALSE BOLDED CLAIM, CORRECTED

**The claim as it stands** in `.softhouse/handoff/T493-zero-turn-escalation.md` §4.3, in bold:

> "No verdict is sensitive to it."

**That claim is false as written, and this is the corrected text.** Substitute it wherever the
original is cited:

> Reclassifying `.softhouse/tasks.json` from real to bookkeeping changes **no verdict at the six
> instants measured** (RED-1 1→1, RED-2 1→1, RED-3 1→1, GREEN-A 0→0, GREEN-B 0→0, GREEN-C 0→0). It
> is **not** verdict-neutral in general, and T541 has the counter-example: **one day later, on the
> cloud producer, it flips GREEN→RED — AXIS 2 goes from 0.0 h to 22.7 h at
> `--producer cloud --now 2026-09-05T12:17:56Z`.** The cause is structural, not incidental: the
> cloud fire's dispatch records are `.softhouse/LOCK` + `.softhouse/tasks.json` only (`6aa31e5e`,
> `c42cb236`, `a19ea967`), so under the alternative every cloud dispatch record becomes bookkeeping
> and the cloud producer reads RED on an ordinary working day. The measurement was honest; the
> generalisation from six points was not supported.

**Scope note, stated rather than quietly skipped.** My declared scope is the guard,
`fire-program.sh`, `.softhouse/capture/t493-zero-turn-escalation/` and this handoff.
`.softhouse/handoff/T493-zero-turn-escalation.md` is **not** in it, so I did not edit T493's file.
The correction lives here and in the guard's own header. Applying it in-file is a one-paragraph
append the driver can make in a scoped task; I flag it rather than doing it, because a scope
violation is a rejection in this program and a superseding record is not.

**What T550 does about the substance, so the false premise cannot bite twice.** T545 asks whether a
`tasks.json`-only commit is bookkeeping or real. **T550 answers it by construction and the answer
is bookkeeping**: `.softhouse/tasks.json` is not on the migration surface, so it never promotes.
That is deliberate — 344 of 2,524 commits are `tasks.json`-only, and `ffe24c01`, a wrapper
*reconcile* scored REAL under T493's rule, is the commit that anchors outage #2's silence window.

And the counter-example's own harm is neutralised rather than ignored: at
`--producer cloud --now 2026-09-05T12:17:56Z` the T550 guard reports

```
AXIS 2 silence     :  0.0h  -> ok      (carry rule, unchanged)
AXIS 3 padded adv. : 22.7h  -> ok      (earned rule, threshold 36h)
VERDICT: GREEN
```

T541's 22.7 h is now **printed as an observable on its own axis** with its own threshold, instead
of silently flipping the verdict. `--producer any` at the same instant still reads `0.0 h GREEN`,
so the producer trap is still demonstrable — see §4.

---

## 3. THE SEVEN MINORS

| # | T541's finding | Disposition |
|---|---|---|
| **MINOR-1** | "23 consecutive no-op fires for outage #1" is instant-scoped; the guard itself reports **26** | **Corrected text below.** Re-driven: `--now 2026-08-27T14:59:00Z` → AXIS 1 = **26**; `--now 2026-08-27T06:00:00Z` → **23**. |
| **MINOR-2** | "12 local commits follow `10baca08`" holds only under ancestry-with-merges | **Corrected text below.** `--no-merges` = 10 (the guard's own instrument), wall-clock = 8, ancestry-with-merges = 12. |
| **MINOR-3** | the handoff and the call-site comment file the cloud-Routine work as **T542**; it is **T543** | **Fixed in code.** `fire-program.sh` block comment now says T543 and records why (the driver renumbered T493's proposed ids because T542 — a `money.go` citation task — was already taken that fire). Handoff text corrected below. |
| **MINOR-4** | the `--explain` refusal calls an as-of-filtered search "the full history" | **Fixed in code**, drive in §4. |
| **MINOR-5** | the header promises a truncation refusal no code path can produce; `root_held` and `future` are dead | **Fixed in code.** `root_held` deleted; the comment now says the behaviour is correct and why (a young repo is not blind; genuine blindness is refused at STEP 0); `future` replaced by a live `n_filtered` count that MINOR-4's message prints. |
| **MINOR-6** | `--probe` exits before the call site | **Fixed in code**, drive in §4. |
| **MINOR-7** | 15 `exit N` paths precede the call site | **Recorded in the block comment** as a named CANNOT, alongside the total-silence CANNOT. |

**MINOR-1, corrected text.** Outage #1's **maximal** no-op-fire streak is **26**
(2026-08-23T09:00Z → 2026-08-27T15:00Z), which is what the guard reports at
`--now 2026-08-27T14:59:00Z`. The figure **23** is the streak **as of T493's chosen replay instant
`--now 2026-08-27T06:00:00Z`**, not the outage's fire count. Outage #2's **13** is both the replay
value and the maximum, so that one needs no caveat.

**MINOR-2, corrected text.** "**10** local non-merge commits follow `10baca08`" — that is the
guard's own instrument (`--no-merges`). Under ancestry *including merges* it is 12; by wall-clock
committer date it is 8, because two of the ten (`fc35f4eb` 17:33+08, `0b5e8b81` 18:05+08) are
worker-branch commits merged in later and carry timestamps *earlier* than `10baca08` (18:33+08).
The substance of the correction — `10baca08` is **not** the last real local commit, `5d7ef306` at
2026-09-03T11:09:38Z is, and the silence is 49.1 h — is unaffected by which count you take.

**MINOR-3, corrected text.** The cloud-Routine work (the only direction that catches a
total-silence outage) is **T543**, `executor: user`. Every reference to **T542** in T493's handoff
is wrong; T542 is an unrelated `money.go` citation task.

---

## 4. NO-REGRESSION — EVERY ITEM T541 VERIFIED BY DRIVE, RE-DRIVEN

Full transcripts: `t550-no-regression.txt`, `t550-refusals-and-asof.txt`,
`t550-wiring-and-refusals.txt`. Shipped defaults throughout: `--streak 6`, `--silence-hours 18`,
`--earned-silence-hours 36`, `--min-subst-lines 8`, `--lookback-days 14`, ref `6aa31e5e`.

```
case          now                    AXIS1   AXIS2       AXIS3       exit  verdict
RED-1         2026-08-27T06:00:00Z   23 RED  95.2h RED   95.2h RED   1     RED
RED-2         2026-09-01T00:00:00Z   13 RED  57.2h RED   57.3h RED   1     RED
RED-3  live   2026-09-05T12:17:56Z    0 ok   49.1h RED   49.2h RED   1     RED
GREEN-B       2026-09-04T13:40:00Z    0 ok    0.0h ok     0.1h ok    0     GREEN
GREEN-C       2026-09-03T11:30:00Z    0 ok    0.3h ok     0.4h ok    0     GREEN
GREEN-mine    2026-08-28T23:59:00Z    0 ok    4.6h ok     4.7h ok    0     GREEN
GREEN-cloud   2026-09-05T12:17:56Z    0 ok    0.0h ok    22.7h ok    0     GREEN
ANY-trap      2026-09-05T12:17:56Z    0 ok    0.0h ok    22.7h ok    0     GREEN
MAX-26        2026-08-27T14:59:00Z   26 RED 104.1h RED  104.2h RED   1     RED
RED-4 (T541)  2026-09-02T23:59:00Z    7 RED  35.4h RED   35.4h ok    1     RED
```

| # | Item that must still hold | Result |
|---|---|---|
| 1 | **`AXIS 1` alone reads `ok (0)` on the live outage** — the fact that justifies the two-axis design | **HOLDS.** RED-3: AXIS 1 `ok (0)`, verdict RED on AXIS 2/3 only. |
| 2 | **`--producer any` reads `0.0 h` GREEN at the same instant** (the producer trap) | **HOLDS, exactly.** ANY-trap: AXIS 2 `0.0h ok`, verdict GREEN, exit 0, while `--producer local` is RED at 49.1 h. This is why AXIS 2 kept the carry rule (§1.4). |
| 3 | **The `--now` filter admits no future-leak**; removing its two lines reproduces **−173.2 h** with AXIS 2 "ok" | **HOLDS.** Deleting the one line `commits = [c for c in commits if c['dt'] <= now]` from a copy gives `AXIS 1 = 11 RED / AXIS 2 = −173.2h ok / AXIS 3 = −173.1h ok`. Filter intact at the same instant: `23 / 95.2h / 95.2h`, all RED. `--explain` of a future commit REFUSES exit 2. |
| 4 | **Shallow REFUSES exit 2** under `--no-fetch` and under an unreachable remote, and **unshallows to a byte-identical verdict** | **HOLDS.** `--depth=60` clone: 179 commits, and `--since` 2026-08-29 / 08-22 / 08-15 / 07-01 all return 179 with rc 0 — the silent failure reproduced first. (a) `--no-fetch` → REFUSE **rc 2**. (b) unreachable remote → REFUSE **rc 2**, still shallow afterwards (no faked recovery). (c) reachable remote → unshallowed 179 → 3002 commits, and `diff` against the full clone at the same `--now` shows **no difference** on any line but the unshallow note. |
| 5 | **2,524 commits with 37 FN / 146 FP reproduce to the commit** | **HOLDS.** `classifier-fp-fn.py 6aa31e5e` (unmodified, so the record still reproduces): `non-merge commits analysed: 2524`, `FALSE NEGATIVE 37 (1.47%)`, `FALSE POSITIVE 146 (5.78%)`, agreement 92.7%. |
| 6 | **The wiring at `fire-program.sh` fires through the caller**, exits 2/3/141/absent never a pass, the fire always continues, guard committed `100755` | **HOLDS.** Block extracted verbatim and executed under `zsh` with `set -uo pipefail` (byte-identical to `fire-program.sh:17`): the real guard escalates through the call site and the fire continues (`rc of block = 0`). Stub guards returning 0/1/2/3/141, plus mode-644 and absent: every branch logs the right thing, REFUSE and every unexpected code are reported as **no verdict, not a pass**, and the fire continues in all seven. `git ls-tree HEAD` → `100755`. |

Two figures changed by design and are disclosed rather than buried: the `in window` census now
reads `earned-real / bookkeeping` under the new classifier (780 earned-real / 587 bookkeeping at the live
instant, against T493's 1375/229 on the attack branch), and `AXIS 2`'s label now says "since last commit carrying
anything" because that is what it measures. No graded verdict and no threshold figure moved.

Also re-driven, both fixed in code:

```
MINOR-4  BEFORE: REFUSE — no commit matching '5d7ef306' in 6aa31e5e (looked in the full
                 --no-merges history of 6aa31e5e, 1331 commits, ...)
         AFTER : REFUSE — no commit matching '5d7ef306' in 6aa31e5e AS OF --now
                 2026-08-27T06:00:00Z (looked in 1331 of 2524 --no-merges commits; 1193 later
                 commit(s) were excluded by --now; ...). 'Not found' here is a statement about
                 the search, not about the world.

MINOR-6  $ zsh harness.zsh <repo> block-def.zsh probe
         no-op-fire-streak[local](probe): **RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**
         no-op-fire-streak[cloud](probe): GREEN — that producer is advancing
         (before T550 the probe exited eight lines above the block and got no verdict at all)
```

And one refusal path that did **not** exist before: an analyser crash. `sys.excepthook` is now
installed as the first statement of the python block, so a malformed `NOFS_SURFACE_RE` REFUSES
**exit 2** instead of leaking python's own **exit 1**, which the call site reads as RED.

---

## 5. WHAT IS STILL OPEN — read this before trusting the guard

**The class is narrowed hard, and it is not closed absolutely.** Git history is entirely under the
producer's control, so no test over git metadata can make a promotion unforgeable, and I do not
claim one. What changed is (a) the **default** when the guard is unsure, and (b) the **cost** of
the forgery:

* **Before:** one appended line per fire, to any path nobody listed, in any file, forever.
* **After:** the padder must write, into `nexus/` or `.softhouse/capture|vectors|handoff|reviews|
  guards|bin/` or `.claude/` or `docs/adr/`, **at least 8 substantive lines that are novel on every
  beat**, every fire, forever — or land nothing for 36 hours and read RED on AXIS 3.

The residual is real and I drove it: at `--min-subst-lines 3` (below the shipped default),
`attack-mine-h` — five novel substantive lines per fire — reads **GREEN**. At the shipped 8 it reads
**RED**. So the residual is now *"a producer writing ≥8 novel substantive lines of product content
per fire, indefinitely"*, and at that point the attack costs what the work costs. That is where the
boundary belongs, and pushing it further is not this guard's job: whether that content is *correct*
is decided by `/softhouse-uat` (does the module build, do the vectors match the reference oracle)
and by the independent reviewer, and whether the branches it claims exist is decided by
`check-branch-published.py`. Three composing guards, none of which is asked to answer another's
question.

**Two blind spots inherited and one narrowed:**

* **Total silence is still not covered from the local side.** A fire that cannot run cannot report
  that it could not run. Only the cloud Routine can catch that; it is **T543**, `executor: user`.
* **A fire that dies in preflight never reaches the block.** 15 `exit N` paths precede it. Now
  named in the block comment, and partly mitigated: `--probe` reaches the guard, so an operator can
  get a verdict without the fire surviving to the lock. (MINOR-7.)
* **The migration surface is an allowlist, so it has blind spots by construction.** They are made
  visible rather than left to be discovered: every report prints `UNCLASSIFIED-PATH` with the top
  offenders and counts (`.softhouse/tasks.json x229`, `.softhouse/program.json x22`,
  `.softhouse/conformance.sh x11`, `.softhouse/gates.md`, `.softhouse/patterns.md`, …). Growing the
  surface is a deliberate diff, and that list is what tells you when to.

**One judgement a later agent may want to overturn, recorded so it need not be rediscovered:**
`.softhouse/patterns.md`, `.softhouse/gates.md` and `.softhouse/program.json` are **not** on the
surface. They carry genuine driver work, and a fire whose only output is a patterns entry now reads
as a no-op. I chose that deliberately — they are also the three most plausible padding targets after
`tasks.json`, and the measurement says nothing is lost: no recorded verdict moves, because no
recorded fire was ever cleared by one of them alone.

---

## 6. SCOPE AND THE NON-NEGOTIABLES

```
$ git diff --name-status a6b11f1b   (the branch base on main)
M  .softhouse/bin/fire-program.sh
M  .softhouse/guards/no-op-fire-streak.sh
A  .softhouse/capture/t493-zero-turn-escalation/t550-materiality-floor.py
A  .softhouse/capture/t493-zero-turn-escalation/t550-materiality-floor.txt
A  .softhouse/capture/t493-zero-turn-escalation/t550-no-regression.txt
A  .softhouse/capture/t493-zero-turn-escalation/t550-padding-attacks.txt
A  .softhouse/capture/t493-zero-turn-escalation/t550-plant-attacks.sh
A  .softhouse/capture/t493-zero-turn-escalation/t550-refusals-and-asof.txt
A  .softhouse/capture/t493-zero-turn-escalation/t550-wiring-and-refusals.txt
A  .softhouse/handoff/T550-t541-conditions.md
```

Every path is inside T550's declared scope. Forbidden paths — `.softhouse/bin/ready-tasks.py`,
`.softhouse/bin/check-branch-published.py` (read only, to copy T536's shape),
`.softhouse/conformance.sh`, `.softhouse/guards/ledgerguard/`, `nexus/internal/apps/savings/`,
`nexus/internal/apps/loanproduct/`, `.softhouse/tasks.json`, `.softhouse/LOCK`,
`.softhouse/RESUME.md`, `.softhouse/program.json` — **untouched**, confirmed by the diff above.

**Money is integer minor units — SATISFIED**, grepped on the diff regardless of task:

```
$ git diff a6b11f1b | grep -nE '^\+.*(float|Float|\bdouble\b|decimal\.Decimal)'
+silence_h = float(os.environ['NOFS_A_SILENCE'])            # HOURS, not money
+earned_h  = float(os.environ['NOFS_A_EARNED_SILENCE'])     # HOURS, not money
+lookback  = float(os.environ['NOFS_A_LOOKBACK'])           # DAYS, not money
```

All three are duration parameters — two thresholds in hours and a window in days — now annotated as
such at the point of use. The only other arithmetic is `(now - t).total_seconds()/3600.0` (elapsed
hours) and integer commit/line counts. The guard reads git metadata and diff text only: shas,
committer timestamps, paths, insertion/deletion counts and added lines. **No monetary value,
amount, currency, schema column, API field or test fixture appears anywhere in the diff.** Other
non-negotiables grepped (`first_name`/`last_name`, Stripe/Plaid/Lithic/Persona,
`ojdbc`/`oracle.jdbc`/MySQL/MariaDB/`:1521`): **no match.** Syntax: `bash -n` clean on the guard,
`zsh -n` clean on `fire-program.sh`.

**Runtime.** The guard now makes two passes over the history instead of one (the second is
`git log -p -U0` capped by `awk` at 200 added lines per commit, ~4.3M raw lines down to ~300k). End
to end it is ~9 s on 2,546 commits, against ~3 s before. The call site runs it twice per fire.
