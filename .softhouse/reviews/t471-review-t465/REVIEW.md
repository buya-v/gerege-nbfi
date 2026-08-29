# T471 — independent adversarial review of T465 (`softhouse/T465-lock-frontier`, tip `b9b37f9c`)

**VERDICT: APPROVED WITH CONDITIONS.**

Three MINOR conditions and five LOW. **Nothing blocks the merge.** The two questions the task
put at the centre both come back in T465's favour, and I re-derived both rather than reading
them:

* **Does a lock-released tree genuinely grade green now? YES.** Measured at the WHOLE-BAR level,
  not at the guard: `b9b37f9c` with `.softhouse/LOCK` removed by `release_lock`'s own sequence
  exits **0**, prints **one** probe line, `probe = up`, `VERDICT: PASS … 46 parity vectors …
  7884 cells`. The same arm at the base `3f4e236a` exits **2** with **zero** probe lines. The
  driver's fire exit stops reddening the bar.
* **Does the no-fixed-point derivation survive attack? YES as to the remedy; the WORDING is
  over-broad.** No *static* pin value is green in both lock states — I drove all four cells plus
  my own two calibrations. But "pinning is not a remedy that exists here" is not exhaustive: a
  lock-state-conditional pin and a census-level exclusion are third options T465 neither named
  nor refuted. Both are worse, and T465 took the guard's own printed remedy #1, so the
  *decision* stands. LOW-1.

Everything below states what I re-derived, what I could not, and what I left open. Where a
cardinal is quoted it is quoted **with its tree**, because two of them had rotted.

---

## 0. What I ran, and where

All drives are against a **throwaway clone made with `git clone --no-local`** at
`/tmp/t471-scratch/clone`, with each rev materialised as a detached worktree of that clone —
**outside the graded repository**. `.softhouse/LOCK` in this repo was never deleted, moved or
modified; a live fire is holding it. The dead-path pin was not touched. I edited none of T465's
files.

Instruments (all in this review directory; every one assembles `.softhouse` from a variable,
P-103):

| instrument | what it establishes |
|---|---|
| `instruments/10-lock-arms-rederive.sh` | the guard's two arms per tree, from the tree, with the lock control read first |
| `instruments/20-armc-and-calibrations.sh` | ARM-C, plus **my own** K+/K− calibrations on the same materialised tree |
| `instruments/30-literal-cardinals.py` | quoted-literal cardinals with the census's `LITERAL_RE` imported **by value from the rev under test** |
| `instruments/31-lock-occurrences.py` | the same, with the census's own `classify()` and `<dot>/`-rooted trim, by **importing the census module out of the materialised tree** |
| `instruments/40-parity-can-fail.sh` | four arms proving T465's parity instrument can go RED, and that its calibration fires |
| `instruments/50-coverage-independent.py` | C-T461-5's cardinals, with `state_path()`'s arms **parsed out of the shipped gate**, not transcribed |
| `instruments/60-anchor-probe-can-fail.sh` | three RED arms on the re-scoped `check-lock-exclusion-anchor.sh` — a drive T465 did not run |

---

## 1. CLAIM 1 — the coupling and the repair. **CONFIRMED, at the bar, all four cells.**

I drove the whole bar four times, each on its own worktree of the throwaway clone. Probe-line
**presence** was tested before any value was read (P-84).

| tree | lock HELD | lock RELEASED |
|---|---|---|
| `3f4e236a` (base) | `BAR_EXIT=0`, probe-lines=**1**, `probe = up`, `VERDICT: PASS … 46 parity vectors … 7884 cells`, `corpus=1684` | **`BAR_EXIT=2`, probe-lines=0** |
| `b9b37f9c` (tip)  | `BAR_EXIT=0`, probe-lines=**1**, `probe = up`, `VERDICT: PASS … 46 … 7884`, `corpus=1690` | **`BAR_EXIT=0`, probe-lines=1, `probe = up`, `VERDICT: PASS … 46 … 7884`** |

At the released tip, `git ls-files -- .softhouse/LOCK` returns **0 paths** — the arm really is a
lock-released tree, not a mislabelled control.

**Better than a control: the failure is ATTRIBUTED.** T465 justified its control by saying a
`exit 2` for a missing toolchain is byte-indistinguishable from the finding. It need not be. In
`out/bar-base-RELEASED.txt` the only hard-guard failure in the whole run is, at lines 264-265:

```
T316-DEADPATH-FRONTIER: REFUSED rows=125 pinned=108 added=17 removed=0
conformance: guard_dead_path_frontier FAILED. Full guard transcript above.
```

with `guard-cost: PASS` and every other guard clean above it. So the base-released `exit 2` is
*caused by* the lock release, and the tip-released `exit 0` is *caused by* the repair. I ran the
HELD control anyway; it is green, as T465 reports.

**The corpus movement `1689 → 1690` and T465's explanation: CONFIRMED exactly.** Measured off the
commits, not the transcript: `6ca0ea03` corpus = **1689**, `ec709ee4` = **1690**, `b9b37f9c` =
**1690**; the single `.py`/`.sh` added between the first two is
`.softhouse/capture/t465-lock-frontier/instruments/60-bar-on-a-released-tree.sh`, and the last
commit changes only `.softhouse/handoff/T465-handoff.md`. The frontier is 108 at `b9b37f9c` in
**both** lock states, so that instrument adds no dead row, as claimed.

---

## 2. CLAIM 2 — the no-fixed-point derivation. **SURVIVES. The wording does not.**

### 2a. Re-driven, three trees, with calibrations that could have failed

`instruments/20-armc-and-calibrations.sh`. The K+ / K− pair runs **on the same materialised tree,
in the same invocation, before the arms**, and the script **aborts** if either comes out the
wrong colour — so the GREENs below are not GREENs that could not have gone RED.

At `3f4e236a`:

```
ARM=A-LOCK-HELD                   exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
ARM=Kplus-PLANTED                 exit=1  REFUSED rows=109 pinned=108 added=1  removed=0
ARM=Kminus-REVERTED               exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
ARM=B-LOCK-RELEASED               exit=1  REFUSED rows=125 pinned=108 added=17 removed=0
ARM=C1-PIN-AT-RELEASED            exit=0  GREEN   rows=125 pinned=125 added=0  removed=0
ARM=C2-PIN-AT-RELEASED-LOCK-BACK  exit=1  REFUSED rows=108 pinned=125 added=0  removed=17
```

At `b9b37f9c`: `A` GREEN, `K+` REFUSED added=1, `K−` GREEN, `B-LOCK-RELEASED` **GREEN
108/108** — so ARM-C is vacuous and my instrument says so rather than reporting a green.

My K+ plants a literal naming a path dead in **every** phase of the fire cycle, and the guard
attributes exactly one new row. My figures agree with T465's and with T461's; none was inherited.

### 2b. "14 of 17 was never an option" — CORRECT, and it is a deduction, not a measurement

The guard is strict set equality against the pin, refusing on `added>0` **and** on `removed>0`.
If `k` of the 17 rows survive a partial repair, the released frontier is `108+k` and the held
frontier is `108`; a single pin value cannot equal both while `k>0`. So any non-empty residue
oscillates, and only removing all 17 makes the frontier invariant. Sound.

### 2c. Where I attack it: the dichotomy is NOT exhaustive (LOW-1)

T465's own sentence — *"there is no pin value that is green in both states"* — is exact and
survives. The gloss around it, *"pinning is not a remedy that exists here"*, is broader than what
was proven. Two options exist and were not enumerated:

1. **A lock-state-aware pin.** Whether `.softhouse/LOCK` is in the index is a property of the
   commit, so a pin selected by that property would not violate T326's host-independence rule.
   It would be green in both states.
2. **A census-level exclusion** of the lock path from the DEAD bucket, as a declared transient.

Both are worse, and I say so with the guard's own text rather than by preference: option 1 makes
17 rows a standing amnesty in one of the two states, which is precisely the shape
`THE PIN IS A FRONTIER, NOT AN AMNESTY` forbids, and it would mask a genuinely new dead-lock-path
site; option 2 makes a whole class of false claim invisible. And option 3 — assemble the path
from a variable — is **remedy #1 of the three the guard itself prints on every refusal**. T465
took the sanctioned remedy. The decision is right; the sentence should be narrowed to the claim
that was actually proven.

---

## 3. CLAIM 3 — the repair's arithmetic and its parity proof

### 3a. The 17-row member SET: **CONFIRMED EXACTLY, at tree `3f4e236a`**

Measured with the census's own selector, trim and `classify()`, imported out of the materialised
tree (`instruments/31-lock-occurrences.py`). 17 rows, 17 distinct files:

```
.softhouse/bin/fire-program.sh                                           | .softhouse/LOCK
.softhouse/bin/ready-tasks.py                                            | .softhouse/LOCK
.softhouse/capture/t279-lock-partition/audit-this-fire.py                | .softhouse/LOCK
.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py            | .softhouse/LOCK.
.softhouse/capture/t325-adopt-attestation/instruments/30-survey-drive.sh | .softhouse/LOCK
.softhouse/capture/t349-pretooluse-eval/probe/replay-real-dispatches.py  | .softhouse/LOCK
.softhouse/capture/t349-pretooluse-eval/probe/spawn-gate-candidate.py    | .softhouse/LOCK
.softhouse/capture/t350-reconcile-content/bin/50-drive-reconcile.sh      | .softhouse/LOCK
.softhouse/capture/t353-t342-conditions/bin/lock-host-census.sh          | .softhouse/LOCK
.softhouse/capture/t453-t450-conditions/instruments/drive-arms.sh        | .softhouse/LOCK
.softhouse/hooks/push-before-spawn-audit.py                              | .softhouse/LOCK
.softhouse/reviews/T189-probe/hardening.sh                               | .softhouse/LOCK
.softhouse/reviews/T189-probe/reachability.sh                            | .softhouse/LOCK
.softhouse/reviews/t172-probe/check-lock-exclusion-anchor.sh             | .softhouse/LOCK
.softhouse/reviews/t172-probe/run-move-demo.sh                           | .softhouse/LOCK
.softhouse/reviews/t202-probe/make-mutants-b.py                          | .softhouse/LOCK
.softhouse/reviews/t202-probe/patch.py                                   | .softhouse/LOCK
```

**at tree `b9b37f9c`: 0 rows, 0 files, 0 occurrences.** Rows only at base: 17. Rows only at head:
0. T465's trailing-full-stop observation about `run-ownership-matrix.py` reproduces: the row is
`.softhouse/LOCK.` because the `<dot>/`-rooted trim runs before the PROSE test and the sentence's
whitespace is all to the left of the path. That is a real property of the census and worth the
paragraph T465 gave it.

### 3b. **"43 quoted literals" is REFUTED. The tree carries 35.** (MINOR-2)

```
T471-OCCURRENCES: baseFiles=17 baseOccurrences=35 baseRows=17
                  headFiles=0 headOccurrences=0 headRows=0 removedOccurrences=35 remain=0
```

The handoff states it as a fact about the tree: *"Those 17 rows are 43 quoted literals across the
17 files."* They are 35. The `43` is `20-assembly-parity.py`'s **per-SITE** sum, and
`fire-program.sh` has **three** rows in its `SITES` table. Re-running T465's own instrument prints
the double-count in plain sight — the same file, three times:

```
  OK       .softhouse/bin/fire-program.sh
           SH_DIR,LOCK_REL                       base literal(s) removed: 4
  OK       .softhouse/bin/fire-program.sh
           SH_DIR,LOCK_REL,LOCK_EXCLUDE_PATHSPEC base literal(s) removed: 4
  OK       .softhouse/bin/fire-program.sh
           SH_DIR,LOCK_REL,LOCK                  base literal(s) removed: 4
```

`35 + 8 = 43`, and the per-file figures T465 cites as evidence (`fire-program.sh` 4,
`check-lock-exclusion-anchor.sh` 6) both match my measurement exactly — it is only the total that
is wrong. The instrument's calibration banner prints the same overstated number
(*"the base commit spells 43 lock literal(s) across 17 file(s)"*), which is a claim about the
tree, not about the calibration.

**This does not change anything that matters.** `0 remain` is confirmed; the row set is confirmed;
the calibration's purpose (non-zero at BASE) is unaffected. But the task asked for both cardinals
to be graded against the tree, and one of them is wrong, in a program that has had cardinals rot
twice in 24 hours.

### 3c. Does the parity instrument evaluate in the target's interpreter? **Partly.** (LOW-3)

* The **15 `shell` rows**: yes. It reads the shebang, extracts the *named* column-0 declaration
  lines from the file under test, and runs them through that interpreter. That is the file's own
  interpreter on the file's own bytes — though on a *reconstructed prelude*, not the file's
  execution context.
* The **`python` and `strings` rows**: no. They `ast.parse` the file and evaluate top-level
  `Assign` nodes in an empty namespace, silently `continue`-ing on any node that raises. That is
  a MODEL of Python, so it proves agreement with a model. The docstring and the handoff both say
  so parenthetically, so it is disclosed rather than hidden — but the handoff's headline sentence
  ("in that file's own interpreter") reads stronger than what runs.

### 3d. **Can it go RED? YES — I drove it.** (`instruments/40-parity-can-fail.sh`)

```
ARM=BASELINE    exit=0   probe-lines=1   files=17 sites=19 baseLiterals=43 headLiterals=0 mismatches=0
ARM=K-PAYLOAD   exit=1   probe-lines=1   !! .softhouse/reviews/t202-probe/patch.py: assignment #5 differs
ARM=K-VALUE     exit=1   probe-lines=1   !! check-lock-exclusion-anchor.sh: SH_DIR,EXPECT_PATHSPEC =
                                            ':(top,exclude).softhouse/LOCK*', expected ':(top,exclude).softhouse/LOCK'
ARM=K-CALIB     exit=92  probe-lines=0   (base == head: nothing to have removed)
T471-PARITY-CANFAIL: arms=4 misbehaved=0
```

`K-PAYLOAD` reworded **one word** inside a `new='''…'''` patch payload in `patch.py` and produced
`assignment #5 differs` — **byte-identical to the specimen T465 reports catching mid-repair**.
That is as close to reproducing an uncommitted intermediate state as is available, and it
corroborates the account. `K-CALIB` confirms the 92 arm fires and prints **no** probe line.

### 3e. The `patch.py` specimen's final bytes: **CONFIRMED CORRECT**

Independent of T465's instrument. I took the head file, deleted the added prelude, replaced
`'''.replace("@LOCK@", LOCKPATH)` with `'''`, and substituted the literal back for `@LOCK@`. The
result is **byte-identical to the base file** apart from one blank line my regex ate. The `old`
and `new` patch payloads round-trip exactly; nothing was silently reworded.

### 3f. NEW FINDING — a name collision the parity instrument cannot see (MINOR-1)

T465 introduced, at `fire-program.sh:39-46` (tree `b9b37f9c`):

```
39: SH_DIR='.softhouse'                       # repo-relative home of this program's instruments
40: LOCK_REL="$SH_DIR/LOCK"                   # repo-relative lock path
41: LOCK="$REPO/$LOCK_REL"                    # absolute lock path (unchanged value)
46: LOCK_EXCLUDE_PATHSPEC=":(top,exclude)$LOCK_REL"
```

**`LOCK_REL` already exists in this file, with a different meaning.** At `:1716` (base `:1685`,
pre-existing, *not* introduced by T465):

```
1716:   LOCK_REL="$(lock_released_at)"
```

That is a **global** assignment — two-space indent inside a top-level `if [[ -f "$LOCK" ]] && (( ! FORCE ))`,
not inside a function and not `local`. From that point on the global named "repo-relative lock
path" at line 40 holds an ISO timestamp.

**No live breakage today**, and I checked rather than assumed: `LOCK` (`:41`) and
`LOCK_EXCLUDE_PATHSPEC` (`:46`) are both frozen at start-up, long before `:1716` runs, and every
read of `LOCK_REL` after `:1716` (`:1720`, `:1724`, `:1733`) wants the `released_at` semantics.
`zsh -n` parses clean. So this is a landmine, not a fire.

**Why it is a condition anyway.** It sits in the file with the largest blast radius in the
program, it was introduced by a change whose whole warrant is *"values unchanged and MEASURED
unchanged"*, and **the instrument that measured it cannot see this class**: `shell_value()`
requires *exactly one COLUMN-0 declaration* of each name, and `:1716` is indented, so it passes
the precondition. The next editor who reaches for `$LOCK_REL` in the exit protocol gets a
timestamp and a comment that tells them it is a path.

---

## 4. CLAIM 4 — the minors

### C-T461-5 — **every cardinal reproduces EXACTLY** (independent selector)

`instruments/50-coverage-independent.py` **parses** `state_path()`'s arms out of the shipped gate
(a transcription can agree with a stale copy; a parse cannot) and applies them with `fnmatch`:

```
T471-COVERAGE: ref=3f4e236a tip=3f4e236a window=400 entries=630 cheapShipped=335
               cheapCaptureOnly=336 captureEntries=27 reviewsEntries=43
               capturePlusReviews=70 lockEntries=122
```

`335/400 = 83.8 %` shipped, `336/400 = 84.0 %` capture-only, **difference = ONE commit**,
`27 + 43 = 70`. All four figures agree with T465's. Both are ceilings; clause (k) is unmodelled
in mine too, and my instrument prints that limit beside the figures.

**This also settles T465's OPEN #4, in T465's favour, which T465 declined to claim.** My selector
independently reports **entries = 630** (T461 said 629) and **`RESUME.md` = 92 entries in 92
commits** (T461 said 90). T465 was right to state the disagreement rather than harmonise it, and
was right on both counts.

### C-T461-6 — **CONFIRMED FIXED**

`fire-program.sh:1367-1374` at `b9b37f9c` carries the `[T465 / C-T461-6]` comment and
`RECON_TMP="$($FIRE_MKTEMP "${TMPDIR:-/tmp}/fire-reconcile.XXXXXXXXXX" …)"`. At `3f4e236a` the
file's only `$FIRE_MKTEMP` uses are `:678` and `:1046`; the reconcile block was a bare `mktemp`.

### C-T461-3 — **the mechanism is CONFIRMED; the blocker as stated does not hold**

`.softhouse/hooks/cheap-subset.sh:78-80` exports `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE`.
Those three are exactly what redirects `git rev-parse --show-toplevel`, so a `read-tree` +
`checkout-index` materialisation is **not** invisible to git — it is a work tree declared by
environment instead of by `.git`. T453's stated blocker is therefore not there, and "small
change, not design change" is the right characterisation. That T465's instrument *refuses* when
the arms agree — and did so on its own first run — is the right shape and is visible in its
source.

**RE-DRIVEN** (`out/cheap-root-T471.txt`), against `HEAD~40` of the tip worktree:

```
T465-CHEAP-ROOT: rev=HEAD~40 control=238 arm=220 distinguishable=YES
   rev-parse --show-toplevel -> /private/var/.../t465-cheaproot.<...>/tree
```

**The delta is 18, exactly as T465 measured; the absolute pair is `238/220` where T465 reports
`237/219`.** That is the caller's own tree moving by one directory between their run and mine —
the same nightly rot that produced this review's other cardinal findings — and it does not touch
the conclusion, because the conclusion is the *difference*.

### C-T461-7 — **CONFIRMED, and my own base-released bar is the evidence**

The objection was that `CTRL-A-LOCK`'s seeded FULL row stood in for an attestation that could not
exist. My base-released bar is exactly that tree: `BAR_EXIT=2`, no probe line, the frontier the
only failure. After the repair the same tree passes the full bar. The repair removes the
objection; T465 correctly declines to claim more, and writes the residue (`seed_full` is a seed)
into `drive-arms.sh` beside the function.

### C-T461-2 / R3 — **the honesty holds**

Code read at `b9b37f9c`. `t` is set in the outer loop; the inner `while` reads from a **file**,
not a pipe, so the counters survive (no P-57 subshell trap). Direction is as documented:
`gate != headblob` → finding, exit 1; absent or `<…>` → counted and named, never a refusal. The
`PKNOWN == 0` branch says *"a MEASURED absence of the fields … never a clean provenance result"*,
and the `RECONCILED CLEAN` line names the split (`graded on N`, `M carried no usable fields`)
rather than folding them together. **The instrument does not overstate.**

I could not reproduce `7 / 21 / 0` — the window derives from the live reflog. I did re-derive the
ledger's shape, which is the fact the claim rests on: `.git/softhouse-driver-gate/attest.tsv`
carries **45 rows — 33 CHEAP, 12 FULL — and exactly 12 rows carry `gate=`, all 12 of them CHEAP.
Zero FULL rows carry any grader identity.** That is C-T461-2's premise, measured.

One naming note, **not** a condition: a FULL row's `gate=` is the sha of `bar-attest.sh` while a
CHEAP row's `gate=` is the sha of `driver-push-gate.sh`. R3 only ever compares the two fields
*within* one row, so the semantics is coherent ("the grader that wrote this row, running bytes vs
HEAD blob") — but the field now denotes *whichever* grader wrote the row, and that is worth one
sentence wherever a reader is pointed at it. T465 argues the choice explicitly; I accept it.

### C-T461-4 → G-23 — **classification is CORRECT** (LOW-5 on the citation only)

Graded against `CLAUDE.md` § Answering gates. The gate does the thing that rule most cares about:
it **splits**, declares the ENGINEERING half *"not gated and should be done"*, sets
`blocks: nothing today`, records a `chosen_by: agent` recommendation, and asks Buyan exactly one
question. That is the opposite of over-escalation — the factory is not parked, and a reviewer
looking for "a RESERVED item dressed as ENGINEERING" does not find one either: applying a ruleset
to live `origin` genuinely cannot be supplied by reasoning.

**LOW-5:** the CLAUDE.md clause cited — *"anything that would … bind Gerege to a third party"* — is
a stretch. GitHub is already in use; nothing new is being bound. The two reasons that actually
carry the escalation are stated in the same paragraph and are the real ones: repo-admin rights
the agent does not hold, and a required status check that no CI reports locking Buyan out of his
own `main`. The classification is right; the citation is loose.

**[NOT RE-VERIFIED]** that `pre-receive` is GitHub Enterprise Server only. It matches my knowledge
and I attempted no network lookup. It is also not load-bearing: the gate's answer would be the
same either way, since the RESERVED half is about touching live `origin`.

### Corrections to T453 filed in the capture directory — **right call**

`.softhouse/handoff/T453-gate-state-set.md` is outside T465's grant. Rewriting another task's
handoff is worse than filing beside its evidence, and `CORRECTIONS-T465.md` names the drive for
each of the three corrections and says which figures it did not chase. Correct restraint.

---

## 5. CLAIM 5 — the nine open routes

**None is understated.** I checked the three the task named and two more.

### OPEN #1 — the better repair at the source. **The deferral is CORRECT. Judged, with evidence.**

`release_lock` could rewrite the lock to a released state instead of deleting it, making
`.softhouse/LOCK` permanently tracked and removing the oscillation at its source. T465 did not
take it. That is restraint, not an undone fix, and the decisive evidence is in the tree:

1. **It would silently disarm a live arm.** `push-before-spawn-audit.py:judge()` reads the lock's
   **absence** as the finding — `if blob(repo, commit, LOCK_REL) is None: bad.append("no
   .softhouse/LOCK on origin -- origin said NO FIRE WAS RUNNING")`. A permanently tracked lock
   makes that predicate never fire again. Repairing it belongs in the same change, and it is a
   different change.
2. **`.softhouse/LOCK` is the driver's file** and explicitly outside T465's edit set; a live fire
   is holding it as I write.
3. **`lock_decide`'s `FREE-released` is one of six arms** interacting with the ceiling and
   freshness thresholds (`LOCK_RELEASE_SKEW_SECS` and friends, validated at the top of the file
   with `EX_CONFIG 78`). Changing lock lifecycle semantics inside a census repair is exactly the
   merge nobody could review.
4. **The census repair is not made redundant by it.** An instrument should not spell a transient
   path in either world.

**The one thing I would change:** T465 writes *"Worth a task."* That is the same shape T465 itself
raised as G-23 against T453 — a route that lives only in a handoff bullet is a route nobody will
be asked about. **File it.** (LOW-2.)

### OPEN #2, #3, #9 — confirmed as stated

* `reachability.sh` still carries, at `b9b37f9c`, `:60 LIVE_LINE=$(sed -n '224p' ".../bin/fire-program.sh")`
  and `:61 echo "  live line 224: $LIVE_LINE"`. P-86 exactly. **Both this file and
  `check-lock-exclusion-anchor.sh` are UNWIRED**: `grep -c` for either name over
  `.softhouse/conformance.sh` is **0**, and nothing under `guards/`, `bin/` or `hooks/` references
  them. Flagging rather than fixing is right for archived, unreachable review evidence, and it is
  why MINOR-3 is MINOR and not MAJOR.
* `run-move-demo.sh` still writes `${HERE}/fire-program.sh.MOVE-scratch-copy.sh` **inside the
  repo**. T299 class. Untouched and declared.
* Clause (k) unmodelled: correct, and my independent re-derivation carries and prints the same
  limit.

### §2.3's re-scoped probe was shipped GREEN-ONLY. I drove it RED. (MINOR-3)

T465 re-scoped `check-lock-exclusion-anchor.sh` — a real design change, moving it from a per-site
substring test to a reconstructed-value test — and reports **one** drive: *"Driven against the
live file: VERDICT: PASS"*. A re-scoped probe shipped only green is the shape this program keeps
rejecting. `instruments/60-anchor-probe-can-fail.sh`, against scratch copies outside the repo:

```
ARM=GREEN    exit=0   VERDICT: PASS -- all 2 live LOCK-exclusion site(s) hold (DETECT=1, STAGE=1)
ARM=K-DECL   exit=1   FAIL: the DECLARED pathspec is [:(top,exclude).softhouse/LOCK*], not the
                            expected [...LOCK] -- WIDENED ... where neither use site would show it
ARM=K-USE    exit=1   FAIL: zero DETECT-classified sites found -- the guard appears to have been
                            removed entirely, not merely mutated
ARM=K-DUP    exit=2   ERROR: expected EXACTLY ONE column-0 declaration ... found 2. REFUSING
T471-ANCHOR-CANFAIL: arms=4 misbehaved=0
```

So T465's claim — that the new value check is *"strictly stronger than the old per-site substring
test, because it catches a widening introduced AT THE DECLARATION, where no use site would show
it"* — is now **measured**, and the T215 categorical floor really is load-bearing: widening a use
site drops it out of the census and the floor names it. The condition is that this evidence
should have shipped with the change; it now exists and should be cited.

### §2.2's fail-closed claim — **CONFIRMED by measurement, not by reading**

`fire-program.sh:17` is `set -uo pipefail`, so an unset `LOCK_EXCLUDE_PATHSPEC` aborts. For the
empty case I measured git rather than trusting the comment:

```
git status --porcelain -- ':(top)' ""                                 -> rc=128
git status --porcelain -- ':(top)' ":(top,exclude).softhouse/LOCK"    -> rc=0
```

and both sites read their rc (`GS_RC`, `ADD_RC`) and report a refusal. Fail direction closed at
both, as the file says.

### One LOW in the re-scoped probe (LOW-4)

```
LIVE_PATHSPEC=$(REPO='' ; eval "$DECL_TEXT" ; print -r -- "${(P)DECL_NAME}")
EVAL_RC=$?
```

`$?` after a command substitution assignment is the status of the **last** command in the
subshell — `print` — so `EVAL_RC` is essentially always 0 and the "could not evaluate" arm is
dead code. The fail direction is still closed, because the value comparison immediately below
catches a wrong or empty reconstruction. Worth repairing so the arm means what it says.

---

## 6. Conditions

| # | severity | condition | the drive that establishes it |
|---|---|---|---|
| **MINOR-1** | MINOR | `fire-program.sh` now has **two** globals named `LOCK_REL` with different meanings — T465's new `:40` (the path) and the pre-existing `:1716` (`released_at`). Rename one. The parity instrument cannot see this class: its precondition is *exactly one COLUMN-0 declaration* and `:1716` is indented. | grep of all `LOCK_REL` sites at `b9b37f9c` and `3f4e236a`; `zsh -n` clean; every post-`:1716` read confirmed to want the timestamp, so no live breakage — a landmine, not a fire |
| **MINOR-2** | MINOR | **"17 rows = 43 quoted literals" is wrong; the tree carries 35.** Correct the handoff, the capture README, and `20-assembly-parity.py`'s calibration banner, which prints the same overstated claim about the tree. `43` is the per-SITE sum; `fire-program.sh`'s 4 literals are counted three times. | `T471-OCCURRENCES: baseOccurrences=35 ... remain=0` (census semantics, census module imported from the rev); T465's own instrument printing `base literal(s) removed: 4` three times for one file; `35 + 8 = 43` |
| **MINOR-3** | MINOR | `check-lock-exclusion-anchor.sh` was **re-scoped and shipped with a green drive only.** Adopt a red drive for it. | `T471-ANCHOR-CANFAIL: arms=4 misbehaved=0` — K-DECL, K-USE and K-DUP all fire; the evidence now exists at `instruments/60-anchor-probe-can-fail.sh` and `out/anchor-*.txt` |
| **LOW-1** | LOW | Narrow *"pinning is not a remedy that exists here"* to what was proven: **no STATIC pin value** is green in both states. A conditional pin and a census-level exclusion exist and were not enumerated (both are worse; say why rather than omitting them). | ARM-C1/C2 drive; the guard's own `A FRONTIER, NOT AN AMNESTY` text |
| **LOW-2** | LOW | **File OPEN #1 as a task.** "Worth a task" in a handoff bullet is the exact process defect T465 raised as G-23 against T453. | `push-before-spawn-audit.py:judge()` reads the lock's absence — the interaction that makes it a real task and not a one-liner |
| **LOW-3** | LOW | The parity instrument's `python`/`strings` rows AST-evaluate in an empty namespace — a model of Python, not the file's interpreter. Disclosed parenthetically; the handoff's headline sentence should match. | source read of `python_value()` / `python_strings()` |
| **LOW-4** | LOW | `EVAL_RC=$?` after a command substitution in `check-lock-exclusion-anchor.sh` captures `print`'s status, so the eval-failure arm is dead. Fail direction still closed by the value comparison. | source read at `b9b37f9c` |
| **LOW-5** | LOW | G-23 cites *"bind Gerege to a third party"*; the reasons that actually carry the escalation (admin rights the agent lacks; locking `main`) are stated in the same paragraph and are the real ones. Classification is right; the citation is loose. | `CLAUDE.md` § Answering gates, RESERVED list |

**No MAJOR. Nothing blocks the merge.**

---

## 7. What I could NOT re-derive, stated rather than implied

* **`provenance-graded=7 / unknown=21 / drift=0` on the live ledger.** The window derives from the
  live reflog and I did not run a modified hook against the live repository. I re-derived the
  premise instead: 45 rows, 33 CHEAP + 12 FULL, 12 rows carry `gate=`, all 12 CHEAP, zero FULL.
* **The mid-repair `patch.py` defect as it actually existed.** It was never committed. I confirmed
  the final bytes round-trip to base exactly, and reproduced the instrument's reaction to that
  defect class — same file, same message, `assignment #5 differs`.
* **`pre-receive` availability on github.com.** Not independently verified; no network lookup
  attempted. Not load-bearing for G-23's answer.
* **T465's `60-bar-on-a-released-tree.sh` itself.** I wrote my own arms rather than running theirs,
  which is the point of an independent review. I verified its effect on the corpus (`+1`, no dead
  row) but did not audit its internals.

## 8. Declared open, by me

1. The census's `LITERAL_RE` pairs quotes **globally over the file**, not per line, so which
   literals it sees can depend on quote parity earlier in the file. I noticed this while
   reconciling a per-file count and did not chase it. It does not affect this verdict — the guard
   is the arbiter and it is GREEN in both lock states at `b9b37f9c` — but it is a property of the
   instrument that decides the colour of the bar, and somebody should measure it.
2. `50-coverage-remeasure.py` models clause `*/req/*` as `"/req/" in path or
   path.startswith("req/")`. The shipped bash `case` arm `*/req/*` requires a leading `/`, so the
   model is very slightly **wider** than the rule. It changes none of the four figures on this
   window (my parser-based instrument, which does not add that arm, reproduces all four exactly),
   but it is a divergence between a model and its subject.
3. I did not attempt a fifth bar cell (tip HELD → released → HELD again across one worktree), i.e.
   a full fire cycle rather than two static states. The guard-level `C2` arm covers the return
   leg; the bar-level return leg is untested.

---

## 9. The bar on THIS review's own committed tree

Run with `bash`, never `sh`/`zsh`. Probe-line **presence** tested before its value (P-84).
Transcript at `out/bar-T471-own-tree.txt`.

```
$ bash .softhouse/conformance.sh ; echo "BAR_EXIT=$?"
BAR_EXIT=0

$ grep -c 'probe = ' <transcript>          # PRESENCE first
1

$ grep -a 'probe = ' <transcript>          # only then the value
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

$ grep -a 'VERDICT' <transcript>
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
  T316-DEADPATH-CENSUS: corpus=1693 deadFiles=75 deadOccurrences=108 resolving=1594
                        indeterminate=126 prose=428
  NAMESPACE-CENSUS: dirs=240 prefixed=217 unprefixed=23 collidingIds=2 declared=2
                    unclaimed=2 shortfallIds=0
```

**The pin was not touched**: `108` before, `108` after, `added=0 removed=0`. The corpus reads
1693 because this review adds seven tracked `.py`/`.sh` instruments; **none of them adds a dead
row** — every path they name under the softhouse directory is assembled from a variable at run
time (P-103, which is the pattern the work under review exists to serve). `.softhouse/LOCK` was
never deleted, moved or modified in this repository; every lock-state drive ran in a throwaway
clone materialised outside it.

**ORACLE NOTE.** The reference oracle was reachable for every bar in this review. The one `exit 2`
recorded here — `out/bar-base-RELEASED.txt` — is **not** an outage: it prints **no** probe line,
it is preceded by `T316-DEADPATH-FRONTIER: REFUSED rows=125 pinned=108 added=17 removed=0` and
`guard_dead_path_frontier FAILED`, and it is the guard working exactly as P-84 describes. No PASS
is reported anywhere in this review on a run where the oracle was down.

### 9a. Re-read on the branch tip

The bar in §9 ran on `b3d92c31`. It was re-run on `f102a68f`, the tip that carries the
cheap-root drive, and is green there too (`out/bar-T471-branch-tip.txt`):

```
BAR_EXIT=0
grep -c 'probe = '  ->  1
conformance: reference oracle (https://localhost:8443/...) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
T316-DEADPATH-CENSUS: corpus=1693 deadFiles=75 deadOccurrences=108 resolving=1594
                      indeterminate=126 prose=428
```

The corpus does not move between the two runs, and that is a property rather than a
coincidence: the census selector is `git ls-files '<dot>/*.py' '<dot>/*.sh'`, and everything
`f102a68f` adds is `.md` or `.txt`. The final commit below adds only this paragraph and one
transcript, so the same argument covers it — which is exactly the reasoning I checked and
confirmed for T465's own `1689 → 1690` explanation in §1.
