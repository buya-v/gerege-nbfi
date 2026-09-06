# T553 — T552's conditions on T550: the vetoes now COMPOSE, and fail-closed has no half

Branch `softhouse/T553-t552-conditions`. Upstream review: `.softhouse/reviews/t552-review-t550/REVIEW.md`.
Files touched: `.softhouse/guards/no-op-fire-streak.sh`, `.softhouse/bin/fire-program.sh`,
`.softhouse/capture/t493-zero-turn-escalation/` (rigs + transcripts), this handoff. Nothing else.

## The composition rule I am fixing (one sentence)

**Each veto must be applied to the residue the previous veto leaves, never to the raw payload — VETO 1
leaves the substantive lines, VETO 2 leaves the NOVEL ones, and VETO 3's materiality floor is counted
over that novel residue — so payload that VETO 2 would reject wholesale can no longer be counted
toward the floor by mixing one novel line into it.**

T552's hypothesis ("VETO 3 counts lines over a multiset admitting duplicates, so payload VETO 2 would
reject wholesale still counts toward the floor once mixed with one novel line") is **CONFIRMED by
driving**, not assumed: `atk-mine-k` promotes with 8 substantive lines of which exactly **1** is novel
(`--explain` below), and after the fix the same commit reads
`VETO 3 THIN PAYLOAD — 1 NOVEL substantive added surface line(s) of 8`.

What I did **not** do, because T552 already measured that it does nothing: raise the floor. The floor
stays at **8**, re-measured under the new rule and unchanged (§ Negative control).

### What the guard does now

* `norm_line` = case-folded + whitespace-collapsed, **digits preserved** (novelty, per line).
* VETO 2a — T550's whole-payload digest, digit-collapsed, kept verbatim in effect.
* VETO 2b — per-line novelty: a line whose normalised form this producer has already put on the
  surface is **spent** (recorded for every anchored commit with substantive payload, promoted or not,
  and deduplicated within the commit). Empty residue ⇒ REPEAT LINES, no promotion.
* VETO 3 — floor counted over the novel residue only.
* Novelty is a structural property (has this producer emitted this line before?), **not a list of
  things to reject** — B-11 / P-104's word-list trap does not apply: no path, no wording, no shape is
  named anywhere in the rule.

### The one design decision inside the fix, and it was forced by a driven FALSE RED

My first implementation reused T550's digit-collapsing normalisation **per line**. It made the
negative control go RED: twelve rows of a captured numeric table differ only in their numbers, so all
twelve collapse to ONE line and a genuinely productive 12-line capture read as `1 NOVEL ... floor is 8`.

```
=== atk-legit          exit=1          <-- FALSE RED, first attempt at the fix
reason    VETO 3 THIN PAYLOAD — 1 NOVEL substantive added surface line(s) of 12
```

A captured numeric table is the most ordinary shape on this migration surface, so that normalisation
cannot be the novelty test. Keeping the digits costs **nothing** against a padder — the cheapest known
padding (`atk-mine-i`, two-character lines) never needed a digit — so digit-collapsing removed real
work and no attack. Per-line novelty therefore preserves digits; the whole-payload digest still
collapses them. Both are driven below (`atk-mine-knum` prices the counter-padding shape this admits).

---

## Each attack, driven BEFORE and AFTER

Rig: `.softhouse/capture/t493-zero-turn-escalation/t553-plant-attacks.sh` — an **independent re-plant**,
because T552's own rig lived in a reviewer worktree that no longer exists here
(`ls /home/user/wt` → `No such file or directory`). Eight consecutive no-op fires off the live outage
anchor `5d7ef306`, +0800, 3 h apart, graded at `--now 2026-09-04T23:00:00Z`.
**The re-plant is byte-faithful to T552's**: my `atk-mine-k` promotion hashes to payload digest
`3b8727b176e1d689` and `atk-mine-i` to `d1dee967ad6a942b` — the exact two digests printed in T552
REVIEW §1b and §2. Full transcript: `t553-attacks-before-after.txt`. BEFORE = `git show HEAD:` of the
shipped guard; AFTER = this branch.

| attack | shape | BEFORE | AFTER |
|---|---|---|---|
| `atk-mine-k` | 7 verbatim-repeated + **1 novel** line/fire | **GREEN exit 0** (streak 0) | **RED exit 1** (streak 7) |
| `atk-mine-k40` `--min-subst-lines 40` | 39 verbatim-repeated + 1 novel, floor raised to 40 | **GREEN exit 0** | **RED exit 1** |
| `atk-mine-k` `--min-subst-lines 20` | floor raised to 20 | RED exit 1 | RED exit 1 |
| `atk-mine-k` `--min-subst-lines 2` | floor lowered to 2 | **GREEN exit 0** | **RED exit 1** (1 novel < 2) |
| `atk-mine-i` | 8 two-character novel lines/fire | GREEN exit 0 | **GREEN exit 0 — RESIDUAL** |
| `atk-mine-j` | the `mine-i` promotion on 2 of 8 fires | GREEN exit 0 (streak 2, 18.0 h) | **GREEN exit 0 — RESIDUAL** |
| `atk-mine-knum` (new) | 7 **counter** lines + 1 novel | GREEN exit 0 | GREEN exit 0 — RESIDUAL, priced below |
| `atk-mine-min` (new) | 8 **one-character** novel lines/fire | GREEN exit 0 | GREEN exit 0 — the residual's floor price |
| `atk-mine-rot` (new) | `mine-k`'s payload into a **new file every fire** | **GREEN exit 0** | **RED exit 1** (streak 7) |
| `atk-repeat` (new) | the same 8 lines every fire, no novel line | RED exit 1 | RED exit 1 (VETO 2a) |
| `atk-unenumerated` | 12 novel prose lines to a never-committed path | RED exit 1 | RED exit 1 |
| `atk-t541` | T541's valueless `docs/` line | RED exit 1 | RED exit 1 |
| `atk-legit` | 12 novel capture rows/fire | GREEN exit 0 | **GREEN exit 0** |
| `atk-legit-boiler` | 6-line fixed header + 12 novel rows/fire | GREEN exit 0 | **GREEN exit 0** |

### MAJOR-1 — `atk-mine-k`, the composition defect

BEFORE (shipped guard):

```
$ .../no-op-fire-streak.sh --producer local --ref atk-mine-k --now 2026-09-04T23:00:00Z --no-fetch
  AXIS 1 no-op streak : 0 consecutive no-op fire(s) (threshold 6) -> ok
  AXIS 3 padded adv.  : 12.0h since last EARNED commit d3ba8dee -> ok
  VERDICT: GREEN — producer is advancing                                          exit=0
$ ... --explain d3ba8dee
verdict   REAL (earned)
reason    ANCHOR on the migration surface + payload 3b8727b176e1d689
          (8 substantive added line(s), floor 8), all three vetoes survived
$ ... --ref atk-mine-k40 --min-subst-lines 40   ->  AXIS 1: 0 -> ok  GREEN         exit=0
$ ... --ref atk-mine-k   --min-subst-lines 2    ->  AXIS 1: 0 -> ok  GREEN         exit=0
$ ... --ref atk-mine-k   --min-subst-lines 20   ->  AXIS 1: 8 -> RED               exit=1
```

(The floor is a lever the padder simply steps over: raising it to 20 catches the 8-line `k` shape only
because `k` was built for a floor of 8 — `k40`, built for 40, walks past 40. Lowering it to 2 lets `k`
through as well. That is T552's point, reproduced in both directions.)

AFTER (this branch):

```
$ ... --ref atk-mine-k --now 2026-09-04T23:00:00Z --no-fetch
  AXIS 1 no-op streak : 7 consecutive no-op fire(s) (threshold 6) -> RED
  VERDICT: RED — this producer is not advancing the migration                     exit=1
$ ... --explain d3ba8dee
verdict   BOOKKEEPING
reason    VETO 3 THIN PAYLOAD — 1 NOVEL substantive added surface line(s) of 8
          (the other 7 were already on this producer's surface), floor is 8
payload   8 substantive added surface line(s), 1 of them novel for this producer
          (VETO 3 counts the NOVEL residue, not the raw multiset)
$ ... --ref atk-mine-k40 --min-subst-lines 40   ->  AXIS 1: 7 -> RED               exit=1
$ ... --ref atk-mine-k   --min-subst-lines 2    ->  AXIS 1: 7 -> RED               exit=1
```

The first fire of each attack still promotes (its lines are genuinely new); fires 2..8 carry one novel
line each and are vetoed, which is why the streak is 7 rather than 8. Seven ≥ the threshold of 6, so
the streak trips. `atk-mine-k40`'s streak is 7 for the same reason.

### T550's original property is preserved, not merely claimed

`atk-repeat` — the same eight lines every fire, no novel line at all — is RED on both guards, and the
new guard names the right veto rather than falling through to the floor:

```
$ ... --ref atk-repeat --explain 6f9e3d64
reason    VETO 2 REPEAT PAYLOAD — normalised payload 1918124713eabb98 already used at c792c527
          by this producer
payload   8 substantive added surface line(s), 0 of them novel for this producer
```

So all four classifier outcomes — NO ANCHOR, VETO 1, VETO 2a, VETO 2b/VETO 3 — are driven, not just
the one the review named.

### The residual — MEASURED, not characterised

T550 stated its residual as "the attack costs what the work costs"; T552 measured that FALSE at 16
bytes per fire. Here is mine, with numbers, all driven:

* **`atk-mine-i` still promotes** — 8 two-character novel lines per fire = **16 characters of payload,
  24 bytes on disk**, and holds the eight-fire no-op streak GREEN exit 0.
* **`atk-mine-min` prices the floor of the residual.** The cheapest promotion this guard admits is
  exactly `--min-subst-lines` lines that are new to this producer, so I drove it: eight **one-character**
  lines per fire — **8 bytes of content, 16 bytes with newlines**
  (`git show 9e5c241f -U0 | grep -c '^+[^+]'` → 8; the same lines are 8 bytes) — GREEN exit 0.
* **`atk-mine-knum` shows what the digit-preserving choice admits**: 7 lines of a running counter +
  1 novel line, GREEN exit 0. It is **not cheaper** than `mine-i` — a counter makes all 8 lines novel,
  so it pays the same 8-novel-line price — but it is honest to record that after this fix, padding with
  a counter is not free padding, it is novelty.
* **Rotating the PATH does not refresh novelty.** `atk-mine-rot` writes `mine-k`'s payload into a new
  file every fire (T541's and T550's `mine-f` shape crossed with `k`): **GREEN exit 0 before, RED exit 1
  after**. The ledger is keyed on line content per producer, not on path, so a padder cannot buy
  novelty with `mkdir`.
* **`atk-mine-j` prices the RATE**: the promotion on only **2 of 8 fires** is GREEN (AXIS 1 streak 2,
  AXIS 3 18.0 h). The binding constraint is one promotion per `--streak` fires **and** per
  `--earned-silence-hours`, i.e. under shipped defaults and a 3 h cadence roughly one promotion per
  15–18 h. Over a 14-day window that is ~23 promotions × 8 lines = **~184 lines, ~184 bytes, for a
  fortnight of forged health**.

So the class is **NOT closed** and I am not claiming it is. What the fix removed is the ability to pay
in **boilerplate**: before, a padder needed 1 novel line and any amount of copy-paste; now every line
it presents must be new to it. The remaining price — 8 novel lines per promotion, minimum 8 bytes —
is cheap and I have measured it rather than called it "the cost of the work". No test over git
metadata can distinguish generated text from work; the composing controls for *worthless but novel*
content are `.softhouse/bin/check-branch-published.py` and the independent reviewer, and this guard
says so in its header.

## MAJOR-2 — fail-closed has no half

Sweep: `t553-failclosed.sh` → `t553-failclosed.txt`, both guards, 21 cases. `rc=1` is a **verdict**;
only `rc=2` is "no verdict".

```
--streak with no value                         before_rc=1  after_rc=2  ok
--ref with no value                            before_rc=1  after_rc=2  ok
--explain with no value                        before_rc=1  after_rc=2  ok
--producer / --now / --min-subst-lines / --lookback-days /
  --silence-hours / --earned-silence-hours, each with no value
                                               before_rc=1  after_rc=2  ok
unwritable TMPDIR (mktemp fails)               before_rc=1  after_rc=2  ok
NOFS_PAYLOAD_CAP=abc (cap silently disabled)   before_rc=0  after_rc=2  ok
NOFS_PAYLOAD_CAP=0                             before_rc=1  after_rc=2  ok
NOFS_PAYLOAD_CAP=-5                            before_rc=1  after_rc=2  ok
--min-subst-lines 0 (floor silently disabled)  before_rc=0  after_rc=2  ok
unknown argument / unknown producer / missing ref / 4 analyser crashes
                                               before_rc=2  after_rc=2  ok
```

Two cases beyond T552's list, found by sweeping rather than by reading: `NOFS_PAYLOAD_CAP=0` and `=-5`
made awk drop **every** payload line, so nothing could earn and the guard reported **RED exit 1** — a
guard misconfiguration presenting as a migration outage, the same defect one level down; and
`--min-subst-lines 0` silently turned VETO 3 off and returned **GREEN exit 0**, which is the worse
direction. Both now REFUSE.

Changes: `say`/`refuse` moved above the option parser; `need_val` guards every `shift 2`; both
`mktemp`s and the oldest-commit read `|| refuse`; the EXIT trap is armed before the first `mktemp` so a
refusal between the two still cleans up; `NOFS_PAYLOAD_CAP` validated before it reaches awk;
`min_subst < 1` refuses; and the analyser is run inside an `if` so any status outside {0,1,2} — an OOM
kill's 137, a segfault's 139 — becomes REFUSE with the raw status printed instead of aborting under
`set -e` with a number a caller could read as a finding. **No bypass flag, no env var, no exemption
was added** (P-45); every new path is a REFUSE, and REFUSE is not GREEN.

One correction to MINOR-5, measured on the shipped guard: its `NOFS_PAYLOAD_CAP=''` half does **not**
reproduce. `PAYLOAD_CAP="${NOFS_PAYLOAD_CAP:-200}"` substitutes the default for an *empty* value as
well as an unset one, so the empty string never reaches awk (`before_rc=0`, 703 earned-real in window,
identical to the default). The `abc` half is real and is now refused.

## Negative control — legitimate fires still pass

Four independent controls; **no false RED in any of them.**

**1. Hourly replay of the whole recorded history, both classifiers** (`t553-sweep.py`, an independent
re-implementation of both classifiers so a mistake in the guard cannot hide inside its own control):

```
run 1 — origin/main at 2,587 non-merge commits
  local: 482 hourly instants replayed   RED(new)/GREEN(old): 0    GREEN(new)/RED(old): 0
  cloud: 482 hourly instants replayed   RED(new)/GREEN(old): 0    GREEN(new)/RED(old): 0
run 2 — origin/main at 2,600 (another worker in this fire pushed mid-task; re-run for that reason)
  local: 483 hourly instants replayed   RED(new)/GREEN(old): 0    GREEN(new)/RED(old): 0
  cloud: 483 hourly instants replayed   RED(new)/GREEN(old): 0    GREEN(new)/RED(old): 0
```

**1,930 replayed instants across two states of the history, zero verdict changes.** T552's requirement
— "there are NO FALSE REDS today and your change must not introduce any — re-run that replay" — is met
with a stronger statement: the new classifier does not change a single hourly verdict, in either
direction, over the whole recorded history.

**2. The materiality floor, re-derived under the novel-residue rule** (same script):

```
local  ALL FIRES    NEW rule: cleared=36/89  min-over-cleared-fires(max NOVEL lines)=12
       GRADED (14d) NEW rule: cleared=11/60  min = 104   smallest ten=[104,134,141,147,151,160,177,186,199,200]
cloud  ALL FIRES    NEW rule: cleared=5/5    min = 27
       GRADED (14d) NEW rule: cleared=2/2    min = 155
```

**12 and 27 — the same two numbers T550 measured over the raw multiset and T552 re-derived**
(`t550-materiality-floor.py` reproduces `12; cleared fires=36` / `27; cleared fires=4` in this
checkout). Counting novelty instead of lines costs the real corpus **nothing**: every fire that ever
cleared carries at least 12 NOVEL lines in its best promotion, so the floor of 8 keeps its 1.5x margin.

**3. T493/T550's whole published battery, re-driven through BOTH guards** (`t553-battery.sh`), 12 rows
+ 12 live spot instants on `origin/main`: **24 of 24 AGREE, 0 DIFFER** — every exit code identical.
The full table is in `t553-negative-control.txt` §4.
(Full record, with the MINOR-1 correction placed in-place above T550's own table and every other MINOR
answered case by case: `t553-minor-corrections.txt`.)
This also settles two of T552's MINORs by driving them:
`GREEN-B` as **cloud** = exit 0 and as **local** = exit 1 (MINOR-1: the row is a cloud row and the
table had no producer column), and `GREEN-A` (`local`, `2026-08-29T12:00Z`) = exit 0 on both guards
(MINOR-2: absent from T550's re-drive, present now).

**4. Two synthetic productive fires**, because a control drawn only from history cannot show what a
*new* legitimate shape does. `atk-legit` (12 novel capture rows per fire) and `atk-legit-boiler` (a
fixed 6-line header **plus** 12 novel rows per fire — the shape a novelty rule is most likely to
false-RED on) are both **GREEN exit 0**, and the boilerplate case explains as
`12 NOVEL of 18 substantive added line(s), floor 8` — the header is discounted, the work is counted.

**5. The live margin, from the shipped `--json` on this fire's own history** — the most recent earned
cloud promotion on `origin/main` reports
`"last_earned_substantive_lines": 138, "last_earned_novel_lines": 125` against
`"min_novel_substantive_lines": 8`. Real work sits ~15x above the floor even after novelty is
discounted; the padder sits exactly on it.

**How many legitimate fires, and where from.** 89 local + 5 cloud recorded fires in this repository's
own history (`origin/main`, 2,587 non-merge commits when I started, 2,600 when I finished — another
worker in this fire pushed; 2026-08-17 → 2026-09-06), of which 36 local + 5 cloud ever cleared; every
one of them re-graded under the new rule, plus 1,930 hourly instants, plus 24 driven battery rows,
plus the 2 synthetic productive branches. No oracle was needed for any of it.

## Timing

Same host, same clone, `--ref origin/main` (2,587 non-merge commits), three runs each, wall clock:

```
BEFORE (shipped guard) : 10.88 / 11.01 / 10.90 s
AFTER  (this branch)   : 11.32 / 11.37 / 11.62 s
```

**+0.45 s, ~+4%.** The novelty test adds one blake2b per substantive added line over ~300k lines; the
digit-collapsed shape is derived from the per-line form so the lowercase and whitespace passes are not
paid twice (`line_forms`). An earlier draft that normalised each line twice cost +1.1 s (11.78 / 11.97
/ 12.31 s) — measured, then removed. The guard runs twice per fire, so the fire pays ~+0.9 s.

## Unverified

* `[UNVERIFIED: oracle_unreachable]` — nothing in this task needs the reference oracle (Fineract); no
  vector, money path or schedule arithmetic is touched. I did not probe it.
* `[UNVERIFIED]` **zsh syntax of `fire-program.sh`.** `command -v zsh` is empty in this sandbox, so I
  could not run `zsh -n`. The change there is one log string using `$_nofs_when`, a variable already
  in scope in that function. I drove all seven wiring branches by extracting `_nofs_check` and running
  it under **bash with a two-line `print -r --` shim** (`t553-wiring.sh`): exits 0/1/2/3/141, mode 644,
  and absent all log correctly, the fire continues in every branch, and the guard-missing branch now
  names `(probe)` / `(fire)` (T552 MINOR-7).
* `[UNVERIFIED]` T552's `evidence/t552-plant.sh`, `t552-floor.py`, `t552-sweep.py` could not be
  inspected — `/home/user/wt` does not exist on this machine. My rigs are independent re-plants, and
  the payload-digest match (`3b8727b176e1d689`, `d1dee967ad6a942b`) is the evidence that they
  reproduce the same shapes.
* The residual figures are minima **as driven on this rig**; a padder could vary the shape further. I
  claim only what the transcripts show.

## Blockers

None. No contract change, no `user` gate, no oracle dependency, nothing outside `files_hint`.

## Follow-ups (backlog — deliberately NOT in this diff)

* **T552 §10 / MINOR (out of scope):** `.softhouse/handoff/T493-zero-turn-escalation.md` still carries
  the false bolded claim "No verdict is sensitive to it" at ~line 178, with the correction appended at
  ~line 407 where a reader meets it last. That file is not in this task's `files_hint`; it needs a
  one-line in-place marker at §4.3.
* **T552 MINOR-4:** `t550-wiring-and-refusals.txt` §3 cites blob `c57ed377…` as proof the guard ships
  `100755`; the shipped blob was `24092917…` and is different again on this branch. The property holds
  (`git ls-tree` on this branch shows `100755`); the citation names a superseded blob. I did not edit
  T550's transcript to avoid rewriting another task's record — a correction note belongs beside it.
* **T552 MINOR-6 / §9:** cost is linear in TOTAL history, not in the graded window, because the
  novelty ledger (like VETO 2's map before it) is seeded from all prior history by design. At ~10k
  commits this is ~75 s per fire. The fix is a `--since` bound with an explicit seeding pass; it is a
  design change, not a tweak, and it should be measured before it is needed.
* The novelty ledger never expires a line. That is deliberate and fail-closed, and it costs zero today
  (964-instant replay). If the repository ever legitimately re-adds a large deleted file, that commit
  will not promote; the fire clears on anything else it carries. Worth re-measuring at ~10k commits.
