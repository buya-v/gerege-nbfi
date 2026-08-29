# T465 — the dead-path frontier is no longer a function of the fire-lock cycle

Branch `softhouse/T465-lock-frontier`. Conditions from `T461`'s independent review of `T453`.
**Everything below was measured on this tree.** Where T461 had already measured the same thing,
the figure is stated as agreeing rather than quoted, and the two places it disagrees are named.

---

## 1. What I MEASURED (C-T461-1), with the control and both arms

### 1a. The whole bar, which is the level the finding was stated at

`instruments/60-bar-on-a-released-tree.sh` runs `.softhouse/conformance.sh` twice against one
throwaway clone of one rev — first with the fire lock in the index, then with it removed by
`release_lock`'s own sequence (`rm -f`, stage the deletion, commit) — with the pinned Go
toolchain derived from the source repo's common dir and announced.

| tree | CONTROL: lock HELD | ARM: lock RELEASED |
|---|---|---|
| **`3f4e236a`** (base) | `exit=0 probe-lines=1 not-up=0  VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells` | **`exit=2 probe-lines=0`** |
| **`6ca0ea03`** (repaired) | `exit=0 probe-lines=1 not-up=0  VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells` | `exit=0 probe-lines=1 not-up=0  VERDICT: PASS` |

```
T465-BAR-RELEASED: rev=3f4e236a… control_exit=0 control_probes=1 arm_exit=2 arm_probes=0
T465-BAR-RELEASED: rev=6ca0ea03… control_exit=0 control_probes=1 arm_exit=0 arm_probes=1
```

The CONTROL runs FIRST and the instrument refuses if it is not clean: a bar that exits 2 for a
missing toolchain or an unreachable reference oracle is byte-indistinguishable from the finding,
and an arm nobody can interpret is worse than no arm.

### 1b. The guard, and the arm that decided the remedy

`instruments/10-lock-arms.sh`, two calibrations and four arms, against `3f4e236a`:

```
CALIB-MINUS                      exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
CALIB-PLUS                       exit=1  REFUSED rows=109 pinned=108 added=1  removed=0
ARM-A-LOCK-HELD                  exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
ARM-B-LOCK-RELEASED              exit=1  REFUSED rows=125 pinned=108 added=17 removed=0
ARM-C-PIN-AT-RELEASED            exit=0  GREEN   rows=125 pinned=125 added=0  removed=0
ARM-C-PIN-AT-RELEASED-LOCK-BACK  exit=1  REFUSED rows=108 pinned=125 added=0  removed=17
```

and against `6ca0ea03`:

```
CALIB-MINUS          exit=0  GREEN   rows=108 pinned=108 added=0 removed=0
CALIB-PLUS           exit=1  REFUSED rows=109 pinned=108 added=1 removed=0
ARM-A-LOCK-HELD      exit=0  GREEN   rows=108 pinned=108 added=0 removed=0
ARM-B-LOCK-RELEASED  exit=0  GREEN   rows=108 pinned=108 added=0 removed=0
ARM C SKIPPED — ARM B did not refuse, so there is no released-state frontier to pin.
```

**`CALIB-PLUS` is why `added=0` in the after-run means anything.** It plants an instrument naming
a path that is dead in every phase of the fire cycle, and the guard must go red on it. Without
that, "the guard reports no new rows" is indistinguishable from a guard that has stopped seeing.

**`ARM-C` is the finding that is mine and not T461's, and it is what decided the remedy.**
Pinned at 108 the guard refuses after every fire exit; pinned at 125 it refuses during every
fire, because the pin's own anti-amnesty rule makes `removed>0` a refusal. **The frontier has no
fixed point while any tracked instrument spells the lock path**, so *pinning is not a remedy that
exists here* — it is not that pinning would be poor practice, it is that there is no pin value
that is green in both states. That is why all 17 sites had to go, and why 14 of 17 was not an
option.

My numbers agree with T461's (`108 / 125 / added=17`), re-derived independently.

### 1c. The 17 members, quoted as a SET with its tree

At `3f4e236a`, with the lock out of the index (`out-before/arm-B-added-rows.txt`) — 17 rows,
17 distinct files:

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

A ROW IS A `(file, literal)` PAIR, NOT AN OCCURRENCE. Those 17 rows are **43 quoted literals**
across the 17 files (`fire-program.sh` alone has 4, `t172-probe/check-lock-exclusion-anchor.sh`
6), and removing a row means removing every occurrence in that file. 43 removed, 0 remain.

T461 said "16 of 17 predate T453's branch" and my set agrees on which one does not:
`t453-t450-conditions/instruments/drive-arms.sh`.

**One member is not what it looks like.** `run-ownership-matrix.py`'s row is `.softhouse/LOCK.`
— with a trailing full stop — because the literal is an English sentence, `"…a review commit does
not TOUCH .softhouse/LOCK."`, and the census's `.softhouse/`-rooted **trim** runs BEFORE the PROSE
test, so the whitespace that would have classified it as prose is trimmed away. Worth recording as
a property of the census: **the trim can manufacture a concrete-looking path out of prose whenever
the sentence's whitespace is all to the LEFT of the path.**

---

## 2. What I CHANGED, and why

### 2.1 The 17 sites — assembled from a variable, values unchanged and MEASURED unchanged

`instruments/20-assembly-parity.py` evaluates each repaired file's own declaration chain, in that
file's own interpreter (shebang-resolved for shell, AST-evaluated in an empty namespace for
Python), and compares against the literal read out of the base commit:

```
T465-ASSEMBLY-PARITY: files=17 sites=19 baseLiterals=43 headLiterals=0 mismatches=0
```

The calibration is enforced: **zero literals at BASE aborts at exit 92**, because a clean HEAD
proves nothing against a clean BASE.

**It caught a real defect of mine, which is the reason to have written it.** I reworded a prose
line in `t202-probe/patch.py` that turned out to sit **inside a `new = '''…'''` patch payload** —
i.e. inside the bytes that patch applied to `fire-program.sh`. The parity run reported
`assignment #5 differs`; I reverted the wording and spliced `@LOCK@` instead. Without the
instrument that would have shipped as "prose".

The declaration chain is **named, not swept**. An earlier draft handed every column-0 assignment
in a file to the interpreter and `fire-program.sh` answered `zsh:66: unmatched "` — a 3000-line
driver's declarations are not a self-contained prelude, and sweeping would also let an unrelated
later assignment silently redefine the name under test.

### 2.2 `fire-program.sh` — the one site with real blast radius

The two exit-protocol pathspecs (`git status --porcelain` DETECT and `git add -A` STAGE) now use
one declared `LOCK_EXCLUDE_PATHSPEC`. **Its fail direction is CLOSED at both sites and that is
stated in the file:** under `set -u` an unset name aborts, and an EMPTY value makes git refuse
the pathspec, which both sites already read out of `GS_RC` / `ADD_RC` and report as a refusal
("REFUSING to conclude the tree is clean" / "NOTHING was rescued"). Declaring the fragment once
also removes the drift T202 repaired, where the two sites disagreed about their subject.

### 2.3 `t172-probe/check-lock-exclusion-anchor.sh` — RE-SCOPED, not left to rot

This probe bound to the SPELT fragment, so the repair moved its subject. It now:

* locates the three declaration lines in the target, requires **exactly one** of each, and
  **evaluates them** to reconstruct the live pathspec — never transcribes it;
* compares that value once against an expected value assembled from `$SH_DIR`. **This is
  strictly stronger than the old per-site substring test**, because it catches a widening
  introduced AT THE DECLARATION, where no use site would show it;
* keeps the T215 categorical floor (`>=1 DETECT`, `>=1 STAGE`), which is what turns a widened
  USE site — which drops out of the census — into a named failure. That floor was belt-and-braces
  before; it is load-bearing now, and the file says so.

Driven against the live file: `VERDICT: PASS`, 2 sites (DETECT line 3023, STAGE line 3045),
reconstructed value `:(top,exclude).softhouse/LOCK`.

### 2.4 The minor conditions — what I DECIDED for each

**C-T461-4 (a `user` gate left as a handoff bullet) — RAISED as G-23 in `.softhouse/gates.md`.**
Decided the split the condition describes, and recorded the measured fact that changes the
instrument: **`pre-receive` is a GitHub *Enterprise Server* feature and does not exist on
github.com**, so `FU-T453-3`'s first-named instrument is unavailable and the realistic one is a
**branch ruleset**. ENGINEERING (design + drive against a throwaway bare remote) is not gated and
should be done; RESERVED is applying anything to live `origin`, for two reasons stated in the
gate — repo-admin rights the agent does not hold, and a required status check that no CI reports
locks Buyan out of his own `main`, which stops the whole program rather than one task. Driver
recommendation recorded `chosen_by: agent`; Buyan is asked exactly one question.

**C-T461-2 (one writer, zero readers) — DECIDED: READ IT, and make the other writer write it.**
The argument for reading rather than deleting: the row is the **only durable** record that a tree
was graded by reviewed bytes. The gate already warns at RUN time when running≠HEAD-blob, but that
is a line in a log nobody keeps; deleting the field would throw the durable half away to tidy the
ledger. That is m-3's own reasoning about `bypass.log`, applied one level down, and it would be
odd to answer the same shape two different ways in the same program.
So: `reconcile-pushed-trees.sh` gains **R3**, and `bar-attest.sh` writes `gate=`/`headblob=` onto
FULL rows — spelt with the SAME field names as the CHEAP rows, deliberately, so **one** reader
grades **both** kinds. Direction is asymmetric on purpose: `gate != headblob` is a FINDING
(exit 1); absent or `<unknown>` is COUNTED AND NAMED, never a refusal, because every row written
before this change has no fields and a census that goes red on its own history gets pinned away
within a fire.
Driven red, green and blank against a throwaway clone
(`instruments/30-r3-provenance-drive.sh`): `T465-R3-DRIVE: arms=3 misbehaved=0`. On the LIVE
ledger: `provenance-graded=7 provenance-unknown=21 provenance-drift=0`.

**C-T461-3 (FU-T453-1's blocker) — RE-DERIVED; it does not reproduce, and I say so.**
`instruments/40-cheap-tier-blocker.sh`, with a control:

```
CONTROL  caller's tree                            NAMESPACE-CENSUS: dirs=237
ARM      materialised HEAD~40, cheap-subset env   NAMESPACE-CENSUS: dirs=219
         rev-parse --show-toplevel -> /private/var/…/t465-cheaproot.…/tree
T465-CHEAP-ROOT: rev=HEAD~40 control=237 arm=219 distinguishable=YES
```

The instrument **refuses when the two arms agree** — my first run, against `HEAD`, came back
`distinguishable=NO` (both 237) and said so rather than claiming a result. It is a **small
change, not a design change**: the three exports `cheap-subset.sh` already makes are what
redirect `--show-toplevel`. What survives from T453 is the *obligation* — T165/T201 still require
the graded root to be read back and asserted — not the *blocker*. Correction filed at
`.softhouse/capture/t453-t450-conditions/CORRECTIONS-T465.md` (the T453 handoff itself is outside
my edit grant; see §5).

**C-T461-5 — RE-MEASURED, both halves.** `instruments/50-coverage-remeasure.py`, which CHECKS the
shipped `state_path()` case block before it computes anything and refuses if it has moved:

```
T465-COVERAGE: window=400 entries=630 cheap_shipped=335 cheap_captureonly=336
               captureEntries=27 reviewsEntries=43
```

* rule as shipped: **335/400 = 83.8 %**; rejected "exclude `capture/**` only": **336/400 =
  84.0 %** — **one commit**, not the three points "~87 %" implies.
* `(h2)` excludes `capture/` (27) **and** `reviews/` (43) = **70 entries**, not 27.
* Both figures are **upper bounds**: clause (k) is not modelled. The limit applies equally to
  both rules, which is what makes the *difference* sound.
* Corrected in the gate's own comment, with the note that entry count and commit count are
  different denominators and only the second decides the path a push takes.

**C-T461-6 — FIXED.** `$FIRE_MKTEMP` in the T453 reconcile block, with a comment recording that
it fails safe either way and this is a discipline repair.

**C-T461-7 — ANSWERED BY THE REPAIR, and the residue written down.** The objection was exact:
`CTRL-A-LOCK`'s seeded FULL row stood in for an attestation that could not exist, because a full
bar on that lock-deleted prep tree was `exit 2, no probe line` (§1a, left column, base row). After
the repair the same tree passes the full bar, so the seed now stands in for something achievable.
What is still true is that `seed_full` is a *seed* — it writes a row without running a bar — and
that limit is now stated in `drive-arms.sh` beside the function instead of being re-derivable.

---

## 3. THE FINAL BAR, probe PRESENCE shown before its value

Run on the committed tree of this branch, `ec709ee4`, working tree clean. (The census
corpus reads 1690 here and 1689 in the run one commit earlier: the sixth instrument,
`60-bar-on-a-released-tree.sh`, is a tracked `.sh` and joined the corpus between them.
It adds no dead row -- every path in it is assembled from `$SH_NAME`.)

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
  T316-DEADPATH-CENSUS: corpus=1690 deadFiles=75 deadOccurrences=108 resolving=1577
                        indeterminate=126 prose=427
  NAMESPACE-CENSUS: dirs=238 prefixed=215 unprefixed=23 collidingIds=2 declared=2
                    unclaimed=2 shortfallIds=0
  all 16 wrong ledger implementations DIED through this harness, not by hand.
```

**The pin was not touched.** `108` before, `108` after, `added=0 removed=0` in both lock states.

---

## 4. OPEN — declared, not argued shut

1. **A far better repair exists for the lock itself, and I did not take it.**
   `fire-program.sh`'s `lock_decide` already has arm 1, `FREE-released`, which reads a
   `released_at` field out of a lock file that EXISTS. So `release_lock` could **rewrite** the
   lock to a released state instead of deleting it, and `.softhouse/LOCK` would be permanently
   tracked — which removes the oscillation at its source rather than at 17 instruments, and stops
   the state set from carrying a `D` at every fire exit. **I did not do it**: the lock is the
   driver's file and explicitly out of my edit set, `push-before-spawn-audit.py` reads *absence*
   as meaningful, and the interaction with the ceiling and freshness arms is not something to
   change in the same commit as a census repair. **Worth a task.** My repair does not block it and
   is not made redundant by it — instruments should not spell transient paths either way.

2. **`reachability.sh` cites `fire-program.sh` line 224 by NUMBER** (`sed -n '224p'`) and has been
   wrong for many rewrites. It is P-86 exactly. It is in a file I edited and I left it: it is
   archived review evidence, unwired, and repairing it is a different job from this one. Flagging
   rather than fixing.

3. **`t172-probe/run-move-demo.sh` writes its mutant INSIDE the repo** —
   `${HERE}/fire-program.sh.MOVE-scratch-copy.sh` — so running it dirties a tracked directory.
   That is the T299 defect class. Untouched; I did not run it.

4. **Two selector disagreements with T461 that I did not chase.** T461 reports 629 name-status
   entries and `RESUME.md=90` over the same 400-commit window; my selector reports **630** and
   **92**. The three load-bearing figures (335, 336, 27+43) agree exactly. I state the difference
   rather than harmonising it, because I do not know which enumeration is right.

5. **R3 grades 7 rows and cannot grade 21.** Every FULL row written before this branch, and every
   CHEAP row written before T453, has no provenance fields. R3 counts them as `unknown` and says
   so; it does not refuse. That is deliberate, and it means **provenance coverage of the existing
   ledger is 25 %** and will only rise as new rows are written. Nobody should read
   `provenance-drift=0` as "the ledger is clean" — it is "the 7 rows that could be graded agreed".

6. **The cheap tier still runs exactly one guard.** C-T461-3 removes the stated blocker, but I did
   not extend the tier — that is FU-T461-3 and it needs the root readback designed with it
   (T165/T201). The measurement is in hand; the work is not done.

7. **G-23's ENGINEERING half is not done.** I raised the gate and split it; I did not design or
   drive the branch ruleset against a throwaway bare remote. That half needs no gate and is
   available to the next worker.

8. **`patch.py` no longer applies cleanly to today's `fire-program.sh`,** because I re-spelt the
   same two lines it patches. It is a record of what T202 did, not a re-runnable migration, and
   the file now says so. If somebody wants it re-runnable, that is a different decision.

9. **Clause (k) is not modelled in the coverage re-derivation** (§2.4). Both figures are ceilings.
   Modelling it means invoking `added-path-hazard.py` per commit against each pushed tree's own
   pin, which is a real instrument and a real cost; I judged the *difference* to be what the
   condition asked for. Someone who needs the absolute figure will have to pay for it.

---

## 5. Files changed

**The 17 repaired sites** — `bin/fire-program.sh`, `bin/ready-tasks.py`,
`hooks/push-before-spawn-audit.py`, `capture/t279-lock-partition/audit-this-fire.py`,
`capture/t319-reconciler-f5/run-ownership-matrix.py`,
`capture/t325-adopt-attestation/instruments/30-survey-drive.sh`,
`capture/t349-pretooluse-eval/probe/{replay-real-dispatches,spawn-gate-candidate}.py`,
`capture/t350-reconcile-content/bin/50-drive-reconcile.sh`,
`capture/t353-t342-conditions/bin/lock-host-census.sh`,
`capture/t453-t450-conditions/instruments/drive-arms.sh`,
`reviews/T189-probe/{hardening,reachability}.sh`,
`reviews/t172-probe/{check-lock-exclusion-anchor,run-move-demo}.sh`,
`reviews/t202-probe/{make-mutants-b.py,patch.py}` (all under `.softhouse/`).

**Also** — `.softhouse/hooks/bar-attest.sh` (writes provenance),
`.softhouse/hooks/reconcile-pushed-trees.sh` (R3),
`.softhouse/hooks/driver-push-gate.sh` (two corrected cardinals, comments only),
`.softhouse/gates.md` (G-23),
`.softhouse/capture/t453-t450-conditions/CORRECTIONS-T465.md` (new),
`.softhouse/capture/t465-lock-frontier/` (six instruments, README, `out/`, `out-before/`).

**NOT touched:** `.softhouse/LOCK`, `tasks.json`, `RESUME.md`, `program.json`, the dead-path pin,
`.softhouse/conformance.sh`, and `.softhouse/handoff/T453-gate-state-set.md` (outside my grant —
the corrections to `FU-T453-1` and the "~87 %" figure are filed in the T453 capture directory
instead). **The G-23 register table row and `program.json.gates_pending` are the driver's to
write; I appended the gate block only.**
