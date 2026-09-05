# T552 — INDEPENDENT REVIEW OF T550 (no-op / silent-fire guard, classifier rebuilt after T541)

Subject: `softhouse/T550-t541-conditions`, tip `52cd7439057ec163d678c18d9f9147c61161a22c`.
Merge base with `main`: `a6b11f1be6bc2d8d6df5c14dd25ddd2705bb5ecd`.
Reviewer worktree: `/home/user/wt/T552`, branch `softhouse/T552-review-t550`.
Every figure below was re-derived by running the shipped artefact. Nothing is taken from the handoff.

## VERDICT: ACCEPT WITH CONDITIONS

The inversion is **real**, not a blocklist wearing a new name — I drove it with a path nobody has
ever committed and it fails toward RED (§1). T541's attack is dead. Every published number
reproduces except one unlabelled row. The materiality floor of 8 **survives re-derivation** and
costs **zero** false REDs over 459 hourly replays of the whole recorded history (§3).

Two MAJOR defects stand:

* **MAJOR-1 — VETO 2 and VETO 3 do not compose, and the floor is defeated at any value by
  repetition.** I held an eight-fire no-op streak GREEN with a payload of seven verbatim-repeated
  lines plus **one** novel line, and repeated the result against a floor of 40. The floor does not
  stop T550's own attack G; it only makes it verbose. The disclosed residual — "the attack costs
  what the work costs" — is false as measured.
* **MAJOR-2 — fail-closed is incomplete.** The exit-2 refusal covers every *analyser* crash (I drove
  seven; all exit 2). It does **not** cover the shell prologue: `mktemp` failure and any `--flag`
  given without its value exit **1**, which the call site logs as
  `**RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**`. A guard failure presenting as a finding
  is the exact defect T550 was credited with closing.

Conditions: fix both. Each is a small, local change and neither requires re-opening the design.

---

## 1. IS THE INVERSION REAL? — YES, AND THE SURFACE IS THE HOLE

### 1a. An unenumerated path fails toward RED (the decisive test)

I planted eight consecutive no-op fires whose only payload is **twelve novel, substantive prose
lines per fire** into `frobnicate/widgets/notes.md` — a path that has never existed in this
repository. Rig: `evidence/t552-plant.sh` (independently written; it reproduces T550's fire shape —
LOCK take → payload → LOCK release, +0800, 3 h apart, off the live outage anchor `5d7ef306`).

```
$ .softhouse/guards/no-op-fire-streak.sh --producer local --ref atk-unenumerated \
      --now 2026-09-04T23:00:00Z --no-fetch
  AXIS 1 no-op streak : 8 consecutive no-op fire(s) (threshold 6) -> RED
  VERDICT: RED — this producer is not advancing the migration                      exit=1

$ ... --explain 1a6a7bde
verdict   BOOKKEEPING   (decided from 1 changed path(s) and 0 added surface line(s))
reason    NO ANCHOR — no changed path is on the migration surface
    off-surface  frobnicate/widgets/notes.md
```

Control: the same branch on the T493 guard (`git show a6b11f1b:...`) is **GREEN exit 0**. Twelve
lines of genuinely novel prose per fire, forever, no longer promote. This is an allowlist with an
inverting default, not a renamed blocklist. **I agree with T550 on the central claim.**

### 1b. The harder version — the surface itself is forgeable, and it is cheap. DECIDED: it is the hole.

T550 states the residual as "a producer that writes NOVEL, SUBSTANTIVE content into `nexus/` or
`.softhouse/capture/` every fire, forever, still reads GREEN. At that point the attack costs what
the work costs." **That cost claim is wrong.** `substantive()` means "the line is not blank and is
not pure punctuation/comment decoration". It does not mean the line says anything.

`atk-mine-i` — eight fires, each appending eight two-character lines to
`.softhouse/capture/t552-i/beat.txt` (`aa ab ac ad ae af ag ah`, then `ba bb …`). **Sixteen bytes
per fire.**

```
$ ... --ref atk-mine-i --now 2026-09-04T23:00:00Z
  AXIS 1 no-op streak : 0 consecutive no-op fire(s) -> ok
  AXIS 3 padded adv.  : 12.0h since last EARNED commit b737ecaf -> ok
  VERDICT: GREEN — producer is advancing                                           exit=0
$ ... --explain b737ecaf
reason    ANCHOR on the migration surface + payload d1dee967ad6a942b
          (8 substantive added line(s), floor 8), all three vetoes survived
```

`nexus/` being on the surface is *not* the hole — junk Go there is at least as expensive as the
16 bytes above, and the surface must contain the product. The hole is that the floor measures
**line count**, and any surface path accepting free-form text (`.softhouse/capture/`,
`.softhouse/handoff/`, `.softhouse/reviews/`) makes a line free. Keep the surface; fix the floor
(MAJOR-1).

---

## 2. MAJOR-1 — THE SIXTH PADDING ATTACK **SUCCEEDS**: VETO 2 AND VETO 3 DO NOT COMPOSE

VETO 2 hashes the **whole** added-surface payload. VETO 3 counts substantive added lines as a
**multiset that admits verbatim duplicates**. So the two vetoes can be satisfied simultaneously and
cheaply: pad to the floor with a constant block, and defeat the digest with a single novel line.

`atk-mine-k` — eight no-op fires, each appending the identical seven lines `stable line a … g`
plus one novel line `novel <letter>`:

```
$ ... --ref atk-mine-k --now 2026-09-04T23:00:00Z --no-fetch
  AXIS 1 no-op streak : 0 -> ok       AXIS 3 : 12.0h -> ok
  VERDICT: GREEN — producer is advancing                                           exit=0
$ ... --explain 559bcbfc
reason    ANCHOR ... + payload 3b8727b176e1d689 (8 substantive added line(s), floor 8),
          all three vetoes survived
$ git show 559bcbfc --format='' -U0 | grep '^+'
+++ b/.softhouse/capture/t552-k/beat.txt
+stable line a
+stable line b
+stable line c
+stable line d
+stable line e
+stable line f
+stable line g
+novel h
```

**This is T550's own attack G — "ONE NOVEL SUBSTANTIVE line per fire" — restored.** The floor was
introduced precisely to kill G ("what stops a heartbeat whose content is NOVEL on every beat"). It
does not. It only requires the beat to be padded.

**Raising the floor does not help, at any value.** `atk-mine-k40` uses 39 verbatim-repeated lines
plus one novel line:

```
$ ... --ref atk-mine-k   --min-subst-lines 20  ->  AXIS 1: 8 no-op fires RED   exit=1
$ ... --ref atk-mine-k40 --min-subst-lines 40  ->  AXIS 1: 0 -> ok   VERDICT: GREEN  exit=0
```

The padder's cost scales in bytes of boilerplate, never in information. (Floor 200 reads RED only
because it exceeds `NOFS_PAYLOAD_CAP=200` — an artefact of the cap, not a defence.)

A supporting result, `atk-mine-j`, shows the required *rate* is also lower than the handoff implies:
eight consecutive no-op fires with the 16-byte promotion on **only fires 1 and 6** (the other six
carrying T541's valueless `docs/` line) is **GREEN exit 0** — AXIS 1 streak 2, AXIS 3 18.0 h. The
binding constraint is not "one promotion per fire" but "one promotion per `--streak` fires and per
`--earned-silence-hours`". Under shipped defaults and a 3 h fire cadence that is roughly one
16-byte promotion per 18 hours.

All four new branches are **GREEN on the T493 guard** as well, so this is not a regression T550
introduced — it is the class T550 claimed to have priced out of reach and has not.

**Fix.** Make VETO 3 count *novel* substantive lines, i.e. apply VETO 2's normalisation
**per line** and discount lines whose normalised form this producer has already promoted inside the
window. `atk-mine-k` then carries one novel line against a floor of eight and reads RED, while
legitimate work — whose thinnest recorded promotion carries 12 substantive lines and whose
in-window minimum is 151 (§3) — is untouched. `atk-mine-i` would still promote; that is the honest
residual, and it should be restated as "eight novel lines per fire", not "what the work costs".

---

## 3. THE MATERIALITY FLOOR OF 8 — **SURVIVES RE-DERIVATION**. All three numbers reproduce.

T550's own script reproduces to the commit, at their stated ref and at `origin/main`:

```
$ python3 .softhouse/capture/.../t550-materiality-floor.py ab925f2a /home/user/wt/T552
local: fires=88 longest run of CLEARED-BUT-THIN(<=2 subst lines) fires = 0 None
   min over cleared fires of (max substantive lines in its promotions) = 12; cleared fires=36
cloud: fires=4 ... = 0 None
   min over cleared fires of (max substantive lines in its promotions) = 27; cleared fires=4
```

I then re-derived it with an independently written analyser (`evidence/t552-floor.py`) that differs
deliberately in two ways: **it applies VETO 2** (T550's script sets `earned = anchor and subst`
only, i.e. it measures the floor against a classifier that is *not* the shipped one), and it applies
the 14-day lookback window the guard actually grades on.

```
local  fires(all)=88  fires(graded,14d)=64
  ALL FIRES    veto2 OFF (=T550 method) : cleared=36/88  min-over-cleared-fires(max)=12
  ALL FIRES    veto2 ON  (=shipped)     : cleared=36/88  min-over-cleared-fires(max)=12
  GRADED (14d) veto2 ON  (=shipped)     : cleared=13/64  min-over-cleared-fires(max)=151
     smallest ten per-fire maxima: [151, 157, 159, 161, 163, 195, 195, 199, 199, 200]
  floor sweep 1..40 (graded): cleared=13/64, longest-no-op-run=26 — CONSTANT at every floor
cloud  ALL FIRES veto2 ON: cleared=4/4  min=27 ; GRADED: cleared=1/1  min=179
```

* The true minimum is **12**, not below 8. **The floor produces no false REDs.**
* The floor is *load-bearing at exactly 8*: `atk-mine-i` (8-line payload) is GREEN at floor 8 and
  RED at `--min-subst-lines 9`.
* "The longest cleared-but-thin run is zero" holds and is implied by min = 12: no fire is thin at
  any floor ≤ 12, so the sweep is flat.
* The VETO 2 omission in T550's method is a real methodological gap but is **numerically inert** —
  36/12 either way. Recorded, not charged.

**Independent false-RED sweep** (`evidence/t552-sweep.py`) — both classifiers replayed hourly across
the entire recorded history:

```
local: 459 hourly instants replayed, 2 instants RED(new) but GREEN(old)
   2026-09-01T03Z .. 2026-09-01T04Z  (2h)  cause=AXIS1+AXIS3
cloud: 456 hourly instants replayed, 1 instant  RED(new) but GREEN(old)
   2026-08-17T14Z (repository birth: producer has never earned — RED by design)
```

Both local instants verified against the shipped guard, and both are **correct, not false**:

```
$ ... --producer local --ref origin/main --now 2026-09-01T03:00:00Z
  AXIS 1 : 14 consecutive no-op fire(s) -> RED
  AXIS 3 : 60.3h since last EARNED commit 9cce4c34 at 2026-08-29T14:43Z -> RED
  (T493 guard, same instant: GREEN — it cleared on tasks.json churn)
```

Sixty hours with nothing earned, cleared by the old guard on bookkeeping churn. That is the
tightening working. **Over 459 replays the new classifier is never wrong in the escalating
direction.** The floor of 8 stands as shipped; the defect is §2, not this number.

---

## 4. THE REJECTED DESIGN — **THE COUNTER-EXAMPLE IS REAL**

Claim: requiring a promotion to arrive off `main`'s first-parent chain would have graded
2026-09-01 — 12 trunk-authored commits of real Go work — as a no-op streak.

```
$ git rev-list --first-parent origin/main > /tmp/fp.txt
$ git log origin/main --no-merges --format='%H %cI %ae' \
      --since=2026-08-31T16:00:00Z --until=2026-09-01T16:00:00Z    # the +08 day
  total non-merge commits: 34   first-parent(trunk): 34   off-first-parent: 0
  by committer offset: {'+08:00': 34}
```

**Zero off-first-parent commits that day.** A corroboration rule would have promoted nothing on
2026-09-01 and the streak would have run. The "12" is the count of commits touching `nexus/` that
day (12 touch `nexus/`, 11 of them earn under the shipped classifier); every one is on the
first-parent chain. The rejection is recorded on true data. **I agree; the door should stay shut.**

---

## 5. AXIS 2's FORGEABLE RULE — **MONOTONICITY HOLDS**

Structural: `book_re` feeds only `c['carry']`, which feeds only `carrys` → AXIS 2, and the
`UNCLASSIFIED-PATH` report line. `axis1_red` and `axis3_red` never read it, and
`red = a1 or a2 or a3`. Driven, sweeping `NOFS_BOOKKEEPING_RE` from "matches everything" to
"matches nothing" at `--now 2026-09-05T13:00:00Z`:

| `NOFS_BOOKKEEPING_RE` | prod | AXIS 1 | AXIS 2 | AXIS 3 | earned-in-window | verdict |
|---|---|---|---|---|---|---|
| `.*` / `^` (everything is churn) | local | False (0) | **True** | True | 772 | RED |
| shipped default | local | False (0) | True | True | 772 | RED |
| `^zzz-never-matches$` (nothing is churn) | local | False (0) | **True** | True | 772 | RED |
| `.*` / `^` | cloud | False (0) | **True** | False | 28 | RED |
| shipped default | cloud | False (0) | **False** | False | 28 | GREEN |
| `^zzz-never-matches$` | cloud | False (0) | **False** | False | 28 | GREEN |

AXIS 1, AXIS 3 and the earned count are **invariant** across every input; only AXIS 2 moves, and
only ever from `False` toward `True` as the churn set widens. **No input makes AXIS 2 remove a RED.**
The argument holds and keeping T493's rule is safe. **I agree.**

---

## 6. MAJOR-2 — THE CRASH-MASKING FIX DOES NOT COVER EVERY CRASH PATH

The analyser half is genuinely closed. Seven distinct python-level crashes, all **exit 2** with the
`REFUSE IS NOT GREEN` banner:

```
bad NOFS_SURFACE_RE            rc=2   re.error: missing ), unterminated subpattern
bad NOFS_BOOKKEEPING_RE        rc=2   re.error: nothing to repeat
--silence-hours abc            rc=2   ValueError: could not convert string to float
--streak xyz                   rc=2   ValueError: invalid literal for int()
--min-subst-lines q            rc=2   ValueError
--lookback-days z              rc=2   ValueError
--now not-a-date               rc=2   ValueError: Invalid isoformat string
```

The **shell prologue** is not covered, and it runs before python is ever reached:

```
$ .../no-op-fire-streak.sh --producer local --ref origin/main --no-fetch --streak
  no-op-fire-streak.sh: line 212: $2: unbound variable                              rc=1
$ ... --ref            -> line 209: $2: unbound variable                            rc=1
$ ... --explain        -> line 216: $2: unbound variable                            rc=1
$ TMPDIR=/nonexistent-dir-xyz .../no-op-fire-streak.sh --producer local --ref origin/main
  mktemp: failed to create file via template '/nonexistent-dir-xyz/tmp.XXXXXXXXXX'  rc=1
```

`rc=1` is exactly what the call site reads as
`**RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**` (verified in §7). The `mktemp` path is
reachable in production — a full disk or an unwritable `TMPDIR` turns the guard's own failure into
a migration-outage alarm. The handoff generalises this at line 158 ("a crash now REFUSES (exit 2)
instead of leaking python's exit 1"); that sentence is true of the analyser and false of the shell.

Two further unguarded shell statements of the same class, not reachable today but of the same shape:
`RAW="$(mktemp)"` / `PAY="$(mktemp)"` (line 294) and
`OLDEST_ISO="$(git log "$REF" --format='%cI' | tail -1)"` (line 315) — under `set -euo pipefail` a
failure in either aborts the script with the failing command's status, not with 2.

**Fix.** Guard the option parser (`[ $# -ge 2 ] || refuse "…requires a value"` before each
`shift 2`), and append `|| refuse` to the `mktemp` and `OLDEST_ISO` assignments. Fail-closed is the
whole guard; it should not have a half.

---

## 7. NO REGRESSION — EVERY ITEM RE-DRIVEN

**The driver's two independent drives, reproduced.** `--producer local --ref origin/main`, live:

```
AXIS 1 : 0 -> ok
AXIS 2 : 50.7h since last carrying commit 5d7ef306 at 2026-09-03T11:09Z (18h) -> RED
AXIS 3 : 50.8h since last EARNED commit d355d422 at 2026-09-03T11:07Z (36h) -> RED
   earned by : .softhouse/reviews/t519-review-t516/REVIEW.md
VERDICT: RED                                                                       exit=1
--producer any, same instant: 0.1h / 0.1h, last earned 183855a1 -> GREEN            exit=0
```

(Driver measured 50.6 / 50.7 h; I measure 50.7 / 50.8 h six minutes later. Same anchors, same
verdicts.) This fire's own merge commit earns promotion — the control that an inverted default has
not simply relabelled everything as bookkeeping.

**The battery** (`--ref 6aa31e5e`, shipped defaults), re-driven row by row:

| case | now | AXIS 1 | AXIS 2 | AXIS 3 | exit | matches T550? |
|---|---|---|---|---|---|---|
| RED-1 | 2026-08-27T06:00Z | 23 RED | 95.2h RED | 95.2h RED | 1 | yes |
| RED-2 | 2026-09-01T00:00Z | 13 RED | 57.2h RED | 57.3h RED | 1 | yes |
| RED-3 | 2026-09-05T12:17:56Z | 0 ok | 49.1h RED | 49.2h RED | 1 | yes |
| GREEN-B *(as local)* | 2026-09-04T13:40Z | 0 ok | **26.5h RED** | 26.5h ok | **1** | **NO — see MINOR-1** |
| GREEN-B *(as cloud)* | 2026-09-04T13:40Z | 0 ok | 0.0h ok | 0.1h ok | 0 | yes |
| GREEN-C | 2026-09-03T11:30Z | 0 ok | 0.3h ok | 0.4h ok | 0 | yes |
| GREEN-mine | 2026-08-28T23:59Z | 0 ok | 4.6h ok | 4.7h ok | 0 | yes |
| GREEN-cloud | 2026-09-05T12:17:56Z | 0 ok | 0.0h ok | 22.7h ok | 0 | yes |
| ANY-trap | 2026-09-05T12:17:56Z | 0 ok | 0.0h ok | 22.7h ok | 0 | yes |
| MAX-26 | 2026-08-27T14:59Z | 26 RED | 104.1h RED | 104.2h RED | 1 | yes |
| RED-4-T541 | 2026-09-02T23:59Z | 7 RED | 35.4h RED | 35.4h ok | 1 | yes |

**AXIS 1 alone `ok(0)` on the live outage** — confirmed (RED-3 row and the live run): the outage is
caught by AXIS 2/AXIS 3 only, which is why the third axis exists.

**The `--now` as-of filter, removed from a copy** (`sed` on the single line
`commits = [c for c in commits if c['dt'] <= now]`), `--ref 6aa31e5e --now 2026-08-27T06:00:00Z`:

```
DELETED : AXIS 1 11 RED | AXIS 2 -173.2h ok | AXIS 3 -173.1h ok
INTACT  : AXIS 1 23 RED | AXIS 2   95.2h RED| AXIS 3   95.2h RED
```

Negative silence, both time axes reporting `ok` on an outage. **−173.2 h reproduced exactly.**

**Shallow refusal, both ways.** A `--depth=60` clone: 178 commits, and `--since=2026-08-29`,
`2026-08-22`, `2026-07-01` all return **178 with rc 0** — the trap is real.

```
(a) shallow + --no-fetch                 REFUSE ... answers for the shallow part only   rc=2
(b) shallow + origin file:///nonexistent REFUSE ... STILL SHALLOW after --unshallow     rc=2
                                          still shallow afterwards: true (no faked recovery)
(c) shallow + reachable remote           194 -> 3003 commits, shallow after: false      rc=1
    diff of (c) against the full clone at the same --now, ignoring the history line:
        NO DIFFERENCE
    (c)   history: 1331 non-merge commits ... unshallowed by this guard via 'git fetch --unshallow'
    full  history: 1331 non-merge commits ... repository was already complete
```

**Byte-identical verdict after unshallow.** Confirmed.

**2,524 / 37 FN / 146 FP.** `python3 .softhouse/capture/.../classifier-fp-fn.py 6aa31e5e` →
`non-merge commits analysed: 2524`, `FALSE NEGATIVE 37 (1.47%)`, `FALSE POSITIVE 146 (5.78%)`.
Reproduced.

**Wiring.** `_nofs_check` extracted verbatim from `fire-program.sh:1723-1752` and executed under
zsh with the caller's own flags (`set -uo pipefail`, no `-e`), against stub guards:

```
exit 0   -> GREEN            | fire CONTINUED (rc of block = 0)
exit 1   -> **RED …**        | fire CONTINUED
exit 2   -> REFUSE … NOT a pass | fire CONTINUED
exit 3   -> UNEXPECTED exit 3 — treat as no verdict, not as a pass | fire CONTINUED
exit 141 -> UNEXPECTED exit 141 …| fire CONTINUED
mode 644 -> guard NOT PRESENT or not executable | fire CONTINUED
absent   -> guard NOT PRESENT or not executable | fire CONTINUED
```

Every branch reaches the log, none is silent, and the fire continues in all seven.
`git ls-tree origin/softhouse/T550-t541-conditions .softhouse/guards/no-op-fire-streak.sh` →
`100755 blob 24092917…`. The guard is executable as committed.

**Scope.** `git diff --name-status $MB..origin/softhouse/T550-t541-conditions` → **10 files**, all
inside the permitted set (`.softhouse/guards/no-op-fire-streak.sh`, `.softhouse/bin/fire-program.sh`,
seven files under `.softhouse/capture/t493-zero-turn-escalation/`, its handoff). **The driver's
measurement is correct; scope is clean.**

---

## 8. THE FLAGGED JUDGEMENT — `patterns.md` / `gates.md` / `program.json` OFF THE SURFACE. **CORRECT, and here is the number T550 did not measure.**

The worry is a false RED: a fire that advanced only `patterns.md` now reads as a no-op. I measured
how often that has actually happened, over every fire in the recorded history:

```
local: fires=88 cleared=36 no-op=52
       of which the no-op fire DID touch patterns.md/gates.md/program.json:  0
cloud: fires=4  cleared=4  no-op=0                                            0
```

**Zero.** Every fire that has ever touched those three files also carried an earned promotion, so
excluding them has never cost a cleared fire. They are also the highest-frequency off-surface paths
in the window (`patterns.md x23`, `gates.md x16`, `program.json x38` at the T550 rig instant) — i.e.
exactly the cheap padding targets an allowlist should exclude. **Keep them off.** If a later agent
wants to overturn it, this is the number to beat; it is not a judgement call standing on taste.

---

## 9. COST — CONFIRMED, AND ACCEPTABLE

```
$ git rev-list --no-merges --count origin/main            2547
T550 guard (two history passes):  9.77 / 9.62 / 9.72 s
T493 guard (one history pass)  :  3.32 / 3.34 / 3.29 s
pass 2 alone (git log -p -U0 | awk):  4.66 s, 296,571 lines kept
```

T550's "~9 s vs ~3 s on 2,546 commits" is right. Twice per fire → ~19.5 s, up ~13 s. Judgement:
**acceptable.** It sits in preflight, before the lock, on a fire whose driver run is minutes to
hours; delaying the lock take by 20 s costs nothing and the guard is the thing that notices when the
run does not happen at all. Two caveats worth recording:

* it now also runs on `--probe`, so the "touch nothing, fast" health check goes from ~7 s to ~20 s;
* cost is linear in **total history**, not in the graded window — pass 2 reads every commit's diff
  though only 14 days are graded. This is not trivially prunable: VETO 2's `seen` map is seeded from
  pre-window history by design. At ~10k commits this is ~75 s per fire. Worth a `--since` bound with
  an explicit VETO 2 seeding pass before it becomes a problem.

---

## 10. THE SCOPE REFUSAL — **RIGHT, and the correction that replaced it is incomplete**

T550 declined to edit `.softhouse/handoff/T493-zero-turn-escalation.md` (where MAJOR-2's false
"No verdict is sensitive to it" lived) because it was outside its declared paths, and said so.
**That was the right call** — reaching outside a closed scope to fix prose is how a scope guard
stops meaning anything, and T550's actual repair answers the substance by construction
(`tasks.json` is off the surface, so the disputed reclassification no longer has a verdict to move).

The driver then made the correction directly. Observation, not a charge against T550: the correction
is **appended at line 407**, at the end of the file, while the false bolded claim still stands
unmarked at **line 178** where a reader meets it. `grep -n "No verdict is sensitive to it"` →
still present, no pointer. The cost of that claim was already paid once when it was copied into
T545's brief. A one-line in-place marker at §4.3 would close it.

---

## FINDINGS

| # | sev | finding |
|---|---|---|
| MAJOR-1 | MAJOR | VETO 2 (whole-payload digest) and VETO 3 (line count over a duplicate-admitting multiset) do not compose. Seven verbatim-repeated lines + one novel line clears the floor and defeats the digest: `atk-mine-k` holds an 8-fire no-op streak **GREEN exit 0**, and `atk-mine-k40` does the same against `--min-subst-lines 40`. T550's own attack G is restored; the disclosed residual "the attack costs what the work costs" is false. Fix: count *novel* substantive lines (per-line normalisation), not lines. |
| MAJOR-2 | MAJOR | Fail-closed is incomplete. Analyser crashes REFUSE exit 2 (7 driven), but the shell prologue leaks **exit 1** — which the call site logs as RED — on `mktemp` failure (`TMPDIR=/nonexistent…` → rc=1) and on any `--flag` given without its value (`--ref`/`--streak`/`--explain` → `$2: unbound variable`, rc=1). Handoff line 158 generalises the fix beyond what it covers. |
| MINOR-1 | MINOR | `t550-no-regression.txt` has no producer column and `GREEN-B` sits among local rows. T493 defines GREEN-B as **`--producer cloud`**. Read as local — the table's own convention, since it lists `GREEN-cloud` separately — GREEN-B is **26.5 h AXIS 2 RED, exit 1**, not `0.0h ok exit 0`. The figures are right for cloud; the row is unlabelled. |
| MINOR-2 | MINOR | The header says "Every figure below is the figure T493 published", but T493's **GREEN-A** (`local`, `2026-08-29T12:00Z`) is absent from the re-drive. I drove it: still GREEN exit 0 on both guards, so nothing is hidden — the record is just incomplete. |
| MINOR-3 | MINOR | Comment/code divergence at guard line 481-485. The comment promises "a digest that first appeared months ago must not silently veto today's work"; the code exempts only repeats that are *themselves* outside the window, so an in-window promotion **is** vetoed by a pre-window first occurrence. Measured today: **0 instances** (the repo has only 5 days of pre-window history). Goes live as history grows. |
| MINOR-4 | MINOR | `t550-wiring-and-refusals.txt` §3 cites `100755 blob c57ed377…` as proof the guard ships executable; the shipped blob is `24092917…`. The property holds (I checked `git ls-tree` on the tip) but the evidence names a superseded blob. |
| MINOR-5 | MINOR | `NOFS_PAYLOAD_CAP` is unvalidated and reaches awk raw. `NOFS_PAYLOAD_CAP=''` makes the awk comparison `n < cap` string-compare, dropping **every** payload line, so nothing can ever earn and AXIS 3 is permanently RED; `='abc'` silently disables the cap. Both fail toward escalation, so this is safe, not silent-green — but an env var should not be able to redefine the classifier without a word. |
| MINOR-6 | MINOR | Cost is linear in total history, not in the graded window (§9); `--probe` latency roughly triples. |
| MINOR-7 | MINOR | The guard-missing branch logs "no streak verdict **this fire**" even when called as `_nofs_check probe`; `$_nofs_when` is threaded through every other branch but not that one. |

## WHERE I AGREE, AND WHAT I RAN TO AGREE

* The inversion is real — `atk-unenumerated`, 12 novel prose lines/fire to a never-committed path, **RED exit 1** on the new guard and **GREEN exit 0** on T493's (§1a).
* T541's exact attack is dead — `atk-t541` **RED exit 1**, streak 8 (§2 rig).
* The floor of 8 is measured, not chosen, and produces **no false REDs** — 12 / 27 / zero-thin-run reproduce; independent re-derivation with VETO 2 applied gives the same numbers; a 459-instant hourly replay finds **2** new RED hours, both correct (§3).
* The corroboration rejection rests on true data — **0** off-first-parent commits on 2026-09-01 (§4).
* AXIS 2 is monotone — AXIS 1/AXIS 3/earned-count invariant across every `NOFS_BOOKKEEPING_RE` (§5).
* Every other published figure reproduces: the battery (10 of 11 rows), −173.2 h, the shallow refusal both ways with a byte-identical post-unshallow verdict, 2524/37/146, all seven wiring branches with the fire continuing, guard `100755`, scope 10 files clean (§7).
* Excluding `patterns.md` / `gates.md` / `program.json` from the surface has cost **zero** cleared fires in the whole history (§8).
* The scope refusal was right (§10).

## REPRODUCING THIS REVIEW

```
evidence/t552-plant.sh   <branch> <mode>   # modes: unenumerated mine-i mine-j mine-k mine-k40 t541
evidence/t552-floor.py   <ref> <cwd>       # floor re-derivation, VETO 2 applied, window applied
evidence/t552-sweep.py   <ref> <cwd>       # hourly false-RED sweep, both classifiers
```
