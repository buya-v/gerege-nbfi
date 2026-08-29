# T402 — T386's `C-1`, and `FU-T386-1..8`

Branch `softhouse/T402-t386-conditions`. Subject: `C-1`/`F-1` from T386's review of T381 —
`.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh`.

**HEADLINE: `C-1` IS CLOSED, AND THE FIX T386 PROPOSED WOULD NOT HAVE CLOSED IT.**
`casualty-sweep.sh` is now **safe for `T399` to wire** — see §7 for the two conditions on how.

Everything below was **driven**. Where I quote a number I ran the thing that produced it, and
the instrument is committed beside this file. Three of my own errors are recorded in §9.

---

## 0. The answers, up front

| question | answer |
|---|---|
| **Did T386's `F-1b` reproduce at my HEAD?** | **YES**, before I changed anything. `casualty-sweep.sh` at `1eacb63e` hashes `1fa6acfe6a24588c…`, **byte-identical to the artefact T386 reviewed** — I hashed it rather than carrying the claim. T386's own drive re-run by me: `control_exit=0 control_mz=0 red_exit=0 red_mz=15 red_dnr=0`. Exactly as filed. |
| **Was T386's proposed five-line fix sufficient?** | **NO. Necessary, not sufficient — and this is the load-bearing result of the task.** I built the literal specimen and drove it: it still prints **fifteen** `MEASURED ZERO`s at exit 0. §2. |
| **Is `casualty-sweep.sh` safe for `T399` to wire now?** | **YES**, on the exit code, with the corpus cardinal cross-checked. §7. |
| **Did the class re-audit find anything new?** | **YES — `F-2`.** The corpus assertion, which T386's review names as *the bound* on `FU-T381-1`'s residual, **was itself fail-open**. §3. |
| **Does the healthy control still pass?** | **YES.** `exit 0, selectors=16, did_not_run=0, refused=0, calibration=yes`, zero `MEASURED ZERO` lines, on every run of every drive. §4. |
| **`FU-T386-1..8`** | **3 closed in source, 4 shipped as verified patches (out of grant), 1 proposed to the pattern holder.** §6. |
| **Bar** | `BAR_EXIT=0`, probe line **PRESENT** (`grep -c 'probe = '` = **1**) reading `up`, frontier 11/11, dead-path **GREEN 108**, `VERDICT: PASS — 46 parity vectors, 7884 cells`, all 14 wrong implementations dead. §8. |

---

## 1. RED — reproduced before anything was changed

Instrument `instruments/t402-errf-class-drive.sh`, transcript `out/T402-RED-errf-class-drive.txt`.
Ref `964b532e`, sweep sha256 `1fa6acfe6a24588c…`.

```
CONTROL (shim installed, nothing sabotaged)
  SWEEP-RESULT: selectors=16 did_not_run=0 calibration=yes exit=0
  control: exit=0  MEASURED-ZERO lines=0

ARM U  the scratch DIRECTORY removed at the calibration/selector boundary
       redirect fails ENOENT, cat fails ENOENT           -- T386's F-1b
  SWEEP-RESULT: selectors=16 did_not_run=0 calibration=yes exit=0
  exit=0  MEASURED-ZERO=15  DID-NOT-RUN=0

ARM R  the scratch FILE left readable, filled with STALE text, chmod 0444   [NEW]
       redirect fails EACCES -- the command never runs -- but cat SUCCEEDS
  SWEEP-RESULT: selectors=16 did_not_run=0 calibration=yes exit=0
  exit=0  MEASURED-ZERO=15  DID-NOT-RUN=0  stale text reprinted 16x

DRIVE-RESULT: mode=red … U_exit=0 U_mz=15 U_dnr=0 R_exit=0 R_mz=15 R_dnr=0
DRIVE-EXPECTATIONS-FAILED: 0
```

Fifteen selectors printed
`MEASURED ZERO -- engine ran over 8796 tracked files … and matched nothing` for searches that
never started, under a summary line declaring the run clean. Fifteen and not sixteen is
**derived, not chosen**: bash opens S1's redirect before the sabotage lands, so S1 alone
completes on an already-open descriptor. The count falls out of the mechanism.

ARM R's selector block is the worse of the two, because it is *quieter*:

```
    ENGINE STDERR on a search that DID complete (rc=1). NOT counted as a hit:
      ~ warning: STALE TEXT left by an earlier selector, not written by this search
    MEASURED ZERO -- engine ran over 8796 tracked files in the sweep corpus and matched nothing
```

— the instrument names a completion that never happened, and then denominates a zero in a
corpus it never searched.

---

## 2. **T386's PROPOSED FIX, MEASURED, AND IT IS NOT ENOUGH**

T386 wrote: *"`cat` fails in exactly the same circumstances the redirect fails … **Reading
`cat`'s status closes the whole finding**"*, and gave five lines.

I built that exact specimen — `instruments/t402-make-t386min.sh`, which applies the five lines at
both sites and **nothing else**, and **refuses** unless each anchor is found exactly once (a
builder that silently patches zero sites would let the drive report "the fix does not help" about
a fix that was never applied). Then I ran ARM R against it.

```
ARM M  (T386-min specimen, sha256 3be391d58824f32b…)
  SWEEP-RESULT: selectors=16 did_not_run=0 calibration=yes exit=0
  exit=0  MEASURED-ZERO=15  DID-NOT-RUN=0
```

**The premise is false.** `cat` and the `2>` redirect fail in *overlapping*, not identical,
circumstances. A file that exists and is readable but **not writable** — a tmp reaper that
recreates, a restrictive umask, a container image layer, a `chmod` — makes the redirect fail
`EACCES` while `cat` succeeds and hands back stale bytes.

> **READING A DOWNSTREAM READER'S STATUS DOES NOT MEASURE WHETHER THE WRITER'S REDIRECT WAS EVER
> OPENED.** The status you need is one bash consumed before your code ran.

So the repair does not check a reader. **It makes the channel's openability a measurement**, with
three independent checks, at both sites:

- **PRIME** — a run-time sentinel is written into the file *before* the search. If the file will
  not open for writing, the search is refused before the engine is asked anything.
- **READ** — `cat`'s status is read. *(T386's check, kept — it catches ARM U.)*
- **WITNESS** — if the sentinel **survives** the search, the shell never truncated the file, so
  the redirect was never opened and **the command never ran**, whatever status bash returned.

> **CORRECTED BY T424, closing `F-T408-1`.** This paragraph used to end *"this is the only one of
> the three that is a **positive proof** rather than an inference."* **It is not a proof.** WITNESS
> proves only *"the file at this path still holds my sentinel"*; *"the redirect was never opened"*
> follows from that **only if the path→inode binding held across the window**. State it as an
> **inference under path stability**, and name the two defeats T408 constructed:
>
> - **`A2`, mid-window SUBSTITUTION.** PRIME writes the sentinel to `F`; `F` is then replaced by a
>   different, unwritable file holding plausible stale text. The redirect fails for real, the
>   command never runs, and `_errf_read` returns **usable** — because the content is no longer the
>   sentinel. In `sel()` that is a fabricated `MEASURED ZERO`.
> - **`A3`, sentinel not alone.** The sentinel survives but something appended to the file. Exact
>   equality fails, WITNESS does not fire, same outcome.
>
> **The mechanism still stands, and the bound is honest:** neither defeat is a natural failure
> mode — both need an external agent inside a microsecond window — and in a whole-file run the
> resulting unwritable file makes the **next** selector's PRIME refuse, so the run exits 4 anyway
> and at most one selector can fabricate. T408 could not construct either at whole-file level.
> `A3` is closable (have `_errf_read` refuse when the text *contains* the sentinel rather than only
> when it *equals* it); `A2` is not closable without an inode check, which would add a new K1 site,
> so **leaving `A2` open and documented is the better trade**. T424 did not change the code here —
> only the claim, which is the part that was wrong.

The sentinel carries **no command substitution** — it is built from `$$`, `$RANDOM` and the
`mktemp` suffix already in hand. A `$(date …)` there would have been a new member of the very
class the repair exists to close.

### GREEN

```
DRIVE-RESULT: ref=d718ff72 mode=green control_exit=0 control_mz=0 control_sel=16
              U_exit=4 U_mz=0 U_dnr=16   R_exit=4 R_mz=0 R_dnr=15
DRIVE-EXPECTATIONS-FAILED: 0
```

`ARM U` refuses 16 and `ARM R` refuses 15, and **the difference is mechanical, not noise**: in
`ARM U` the directory is gone by the time S1's `_errf_read` runs, so the READ check catches S1
too; in `ARM R` S1 completes on an already-open descriptor and only S2–S16 fail to prime.

### The WITNESS branch is driven where neither whole-file arm reaches it

`ARM U` is caught by READ and `ARM R` by PRIME — **neither reaches WITNESS**, and an undriven
guard is a guard nobody has seen work. `instruments/t402-errf-helpers-drive.sh` extracts both
helpers **from git by name** (never by line number), prints their sha256 so it cannot grade an
edited copy, and puts each check in front of the state it exists to catch.
`out/T402-errf-helpers-drive.txt`, `cases_failed=0`:

| case | state | result |
|---|---|---|
| Z0 **control** | writable path | prime succeeds |
| Z4 | file `0444` | prime **REFUSES** |
| Z1 **control** | redirect opened, engine wrote a warning | read returns it **usable** |
| Z2 **control** | redirect opened, engine silent | read returns empty, **usable** |
| **Z3 WITNESS** | sentinel survived the search | **REFUSES** — "the command never ran" |
| Z5 | file removed | read **REFUSES** (`cat` failed) |
| Z6 | stderr *mentions* the sentinel | **not** defeated, **not** misfired — exact match |

Z1 and Z2 are there on purpose: T383 shipped a fail-open repair that refused every healthy run,
and a guard that refuses everything is the same defect wearing the opposite sign.

---

## 3. `F-2` — THE BOUND WAS ITSELF FAIL-OPEN. Found by auditing the CLASS.

T386 records `FU-T381-1`'s residual as *"bounded by the `:412` corpus assertion"*.

```
$ bash -c 'x=""; if [ "$x" -lt 1 ]; then echo ABORTED; else echo "FELL THROUGH"; fi'
bash: [: : integer expression expected
FELL THROUGH
$ bash -c 'x=""; [ "$x" -lt 1 ]; echo "[ ] returned $?"'
[ ] returned 2
```

The assertion read `if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]`. **`[` returns 2 on a
malformed comparison; `if` reads any non-zero as false; the abort does not fire.** The sweep would
then have run over a corpus nobody counted — and every `MEASURED ZERO` beneath it would have been
denominated in a number never taken.

> **THE CAUSE STATED HERE WAS WRONG, AND T424 CORRECTED IT — `F-T408-5`.** This paragraph used to
> read *"Had `git ls-files` failed, the sweep would have run over a corpus nobody counted."*
> **A failing `git ls-files` ABORTS.** `grep -c .` prints `0` for an empty stream, so the
> substitution captures the string `0`, `[ "0" -lt 1 ]` is **true**, and the abort fires. Driven
> by T408 and re-derived independently by T424
> (`.softhouse/capture/t424/instruments/t424-f2-true-cause.sh`, `arms_failed=0`;
> transcript `.softhouse/capture/t424/out/T424-F2-true-cause.txt`):
>
> | arm | captured | `[ … -lt 1 ]` | old block |
> |---|---|---|---|
> | `git ls-files` shim exits 128 | `[0]`, rc 1 | true | **ABORT (exit 2)** — the stated cause does not reproduce |
> | real `grep` on an invalid regex | `[]`, rc 2 | `[` returns **2** | — |
> | `grep` shim exits 2, no stdout | `[]`, rc 2 | `[` returns **2** | **FELL THROUGH** — the true cause |
>
> **The fall-through needs `grep` ITSELF to fail** (rc ≥ 2 with nothing on stdout): an invalid
> pattern, a broken locale, a missing binary, EMFILE. Mechanism right, exploit path right,
> attribution wrong. The finding and the repair are unaffected; the *explanation* was the defect,
> and it had been committed into the source comment as well, where the next reader would have
> reasoned from it. Both sites are now corrected.
>
> **And one correction to the correction.** T408 adds that the repair "now reads the pipeline
> status, so pipefail catches the `git ls-files` case as well". **T424 drove that false too:**
> `set -o pipefail` yields the status of the **rightmost** command that exited non-zero, and that
> is `grep -c .`'s `1`, not git's `128` — measured `rc=1`. A failing `git ls-files` is still caught
> by the **value** test, exactly as before; what the status read adds is the `grep`-failed case.

It is a command substitution inside a **numeric test** — neither of T381's two buckets, and not
in T386's list of six unaudited `$(…)` sites either. **It exists only because I audited the
class.** Repaired: counted once, pipeline status read, numeric shape validated, every consumer
reads `$SWEEP_CORPUS_N`. `FU-T381-1` closes with it — **the site is gone, not renumbered.**

---

## 4. The re-audit, by CLASS — `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md`

Instrument `instruments/t402-status-class-census.sh`; `out/T402-CENSUS-{before,after}.txt`.

> **A taxonomy narrower than the defect class does not find the defect. It certifies the part of
> the file the taxonomy could see.**

T381's audit classified *"every `2>/dev/null` and every pipeline"*, correctly. The class is
**every construct from which a status can be lost**. Seven kinds, enumerated mechanically, each
site printed **with its line text** so a reader adjudicates from the list and can cite by
**content** — T386 measured **14 of 16** of T381's line numbers as having moved (`P-86`).

| kind | | before | after |
|---|---|---|---|
| K1 | command substitution | 22 | 26 |
| K2 | pipeline | 31 *(9 operator-position)* | 32 *(16)* |
| K3 | output redirection | 40 *(36)* | 54 *(48)* |
| K4 | command-as-condition | 0 | 7 |
| K5 | assignment-masked status (`local x=$(…)`) | 0 | 0 |
| K6 | substitution in an ARGUMENT | **3** | **0** |
| K7 | arithmetic / numeric test | 28 | 44 |

**K2 and part of K3 were T381's two buckets. K1, K5, K6 and K7 had no row — and two of those
four were carrying live defects** (`C-1` in K1; `F-2` in K1∩K7).

The census **over-includes on purpose**: K2/K3 match `|` and `>` inside the selectors' own quoted
ERE patterns. Narrowing a census to fit the last defect is exactly how the last defect was
missed, so the wide list stays authoritative and a de-noised sub-view (`K2s`/`K3s`) is printed
beside it, explicitly labelled *not the census*.

Every site is adjudicated in `AUDIT-CLASS.md` as READ / FAIL-CLOSED / PROVENANCE / DIAGNOSTIC,
**including the two `$(date -u +%s)` sentinel components T386 listed but did not adjudicate**:
they are **fail-CLOSED**, because both sit on ANTI arms whose refusal condition is `n > 0`, so a
degraded sentinel can only ever make the arm *more* likely to abort. Left as-is deliberately.

**K6 → 0.** The `hits total` / `archived` / `LIVE` cardinals and the `commit` / `date` /
`population` provenance were command substitutions inside `printf` arguments — a position from
which **no `$?` can ever be consulted**, where an errored `grep -c` prints an *empty field* that
reads as a zero. They now have their statuses **and numeric shape** read, and print the word
`UNMEASURED` rather than a blank.

### The rule this file should be maintained under

Six of the seven previously-known instances in this file were **introduced by somebody repairing
the previous one**. That is not a property of `casualty-sweep.sh`; it is a property of the
repairs. The next task to touch it should run `t402-status-class-census.sh` on BEFORE and AFTER
and **give every new site in any moved kind a row**.

---

## 5. The healthy control

Demanded, and not negotiable in this fire. On every drive, on both refs, and standalone:

```
SWEEP CALIBRATE+F: PASS -- known positive matched 2 time(s) …
SWEEP CALIBRATE-F: PASS -- known negative matched 0 times, and the search RAN (rc=1)
SWEEP CALIBRATE+E: PASS -- -E interpreted it (2 hit(s)) and -F did not (0). They DISAGREE,
SWEEP CALIBRATE-E: PASS -- known negative matched 0 times under -E, and the search RAN (rc=1)
SWEEP OBSERVE: T238 hazard LIVE -- escaped=139 literal=139 AGREE while pcre=23110 DISAGREES,
SWEEP-RESULT: commit=d718ff72 corpus=8801 selectors=16 did_not_run=0 refused=0 calibration=yes exit=0
```

All sixteen selectors ran, all five arms passed, LIVE lists populated, **zero** `MEASURED ZERO`
lines. **The new refusals do not refuse a healthy fire.**

---

## 6. `FU-T386-1..8` — each one

| id | disposition |
|---|---|
| **`FU-T386-1`** `main:100` is fail-**CLOSED**, not fail-open | **PATCH SHIPPED, out of grant.** `patches/FU-T386-1-audit-main100-is-failclosed.patch` → `.softhouse/capture/t381-t379-conditions/AUDIT.md`. Records the correction *and the lesson* — `:100` is the positive arm, a discarded status there yields `n=0` which is its **refusal** condition, and **that same mechanism is what stopped half of `F-1`** (`P-72`). |
| **`FU-T386-2`** header contradicts itself | **CLOSED IN SOURCE.** Both sites rewritten. Not "FABRICATING" — the correct diagnosis is **recall loss**, and `t234-sweep-instrument-audit/HANDOFF.md` had it right with a `-P` control three hundred tasks ago. Not "returns zero SILENTLY" — on this corpus it returns **138** self-referential hits, which is *worse* than a zero because a zero at least reads as a finding. **The hazard is unchanged; only the diagnosis was wrong**, and the `sel()` refusal stays exactly as it is. |
| **`FU-T386-3`** `SWEEP OBSERVE` has no non-vacuity guard | **CLOSED IN SOURCE.** A third reading of the same escaped pattern under `-P`, which cannot agree with the other two on any corpus containing the word. Five outcomes now: `LIVE` *(escaped==literal, pcre differs)*, **`VACUOUS`** *(all three zero — no verdict printed)*, `INCONCLUSIVE`, `NOT REPRODUCING`, and **`NOT REPORTED`** when the `-P` control itself did not run. Measured healthy: `escaped=139 literal=139 pcre=23110`. **Still non-gating, deliberately** — a host without PCRE is not a reason to refuse the sweep, and `_calib_refuse` is *not* called here. |
| **`FU-T386-4`** a refusal is indistinguishable from a clean run | **CLOSED IN SOURCE.** `SWEEP_REFUSED` incremented at all three `sel()` refusal sites; `SWEEP-RESULT` gains **`refused=`** and **`corpus=`**, plus a stderr line when it is non-zero. |
| **`FU-T386-5`** cite by name, not by line | **PATCH SHIPPED**, and **largely mooted**: `FU-T381-1`'s site *no longer exists*, so it cannot be renumbered. `patches/FU-T386-5-cite-the-site-by-name-not-by-line.patch` restates it by name in T381's handoff and records `F-2`. |
| **`FU-T386-6`** `T371.md:146` is refuted by its own file | **PATCH SHIPPED.** `patches/FU-T386-6-t371-146-refuted-by-its-own-file.patch` — narrows the claim to "no **graded** artefact", which is what was meant and is true. |
| **`FU-T386-7`** the red drive exits 0 whatever its arms say | **PATCH SHIPPED, AND APPLIED TO MY OWN INSTRUMENTS FIRST.** All four T402 drives accumulate failures and `exit` on them. The patch for `t381-red-drives.sh` derives its verdict by re-reading the drive's **own transcript** rather than threading a counter through eleven branches — so an arm added tomorrow by an author who forgets is still caught, which is the failure mode that produced the finding. **All three outcomes driven**: clean → 0, failing → 1, **not wired → 2** (an unwired guard must not read as a pass). **⚠ SUPERSEDED BY T424 (`F-T408-4`): that patch RE-READ A LOG `tee` WAS STILL WRITING and is 8/8 FAIL-OPEN against a buffered writer.** Apply `.softhouse/capture/t424/patches/FU-T386-7-…AMENDED-BY-T424.patch` instead; see `patches/T424-SUPERSEDES-FU-T386-7.md`. |
| **`FU-T386-8`** doctrine, a line in `patterns.md` | **DEFERRED, with the text below.** `patterns.md` is held by **`T392`** this fire. Proposed: *"**When you re-frame an earlier measurement, cite its transcript or re-run it.** T234 measured the `git grep -E` `\b` hazard correctly — as RECALL LOSS, with a `-P` control — and recorded it. T238 re-framed it as the engine 'FABRICATING a hit', without citing T234, and three later tasks re-derived a weaker version of a result the program had already paid for. A re-framing that does not cite the transcript it supersedes is how a program loses a result it owns."* |

**Why four are patches and not edits.** T402's grant is
`.softhouse/capture/t363-oracle-baseline/instruments/` and its own capture directory. Those four
files sit in T381's capture directory and in two merged handoffs. The brief's own instruction for
`conformance.sh` — *"ship the exact patch as a request in your handoff"* — is the right discipline
here too, and the deliverable explicitly allows "closed **or** explicitly deferred with reason".
They are shipped **verified**, not merely written: `instruments/t402-verify-patches.sh`,
`out/T402-verify-patches.txt`, `VERIFY-RESULT: failures=0`. Apply with

```
git apply .softhouse/capture/t402-t386-conditions/patches/*.patch
```

---

## 7. **`T399`: `casualty-sweep.sh` IS NOW SAFE TO WIRE.** Two conditions on how.

T386's answer was *"Not yet. Wire it AFTER `C-1`."* `C-1` has landed, driven RED before GREEN,
with a healthy control on both sides. **My answer is YES**, with the two conditions T386 named and
one I add:

1. **Gate on the EXIT STATUS, not on the `SWEEP-RESULT` cardinals.** Exit `0` = every selector
   ran; `2` = corpus unusable; `3` = calibration failed; `4` = at least one selector did not run.
   That is exactly "was this sweep interpretable".
2. **Cross-check the declared selector count**, because a *deleted* selector still leaves a clean
   summary. `T399` should assert
   `selectors == $(grep -c '^sel "' casualty-sweep.sh)` — **and read that `grep`'s status**, since
   `grep -c` returns 1 on a count of zero and ≥2 on error. `refused=` (new) now distinguishes a
   refusal from a clean run, which it could not before.
3. **Never gate on LIVE hits.** A LIVE hit is a candidate for a human, not a failure. The file
   says so and it is right.

Two cautions I am handing over rather than solving:

- **The exit code is corpus-dependent by design** — S12–S16 hunt a *shape*, so committing a
  document containing `\b` inside a quoted selector will move it. **Gate it; do not pin its
  numbers.**
- **Runtime.** Sixteen `git grep` passes over **8 801** tracked files, plus **eight** calibration
  searches (I added the `-P` control). Budget it, or scope it.

---

## 8. The bar — clean tree, `bash`, never `sh`

`out/T402-BAR-branch.txt`, run at `fc18b148` with `git status --porcelain` **empty** before it
started, after `git add -A` and commit.

```
BAR_EXIT=0
grep -c 'probe = '  ->  1                                    <- PRESENCE tested before value (P-84)
:94   CENSUS fail-open instruments — inspected 1400 tracked .sh/.py file(s) …
:95   … frontier 11, pinned at 11
:100  frontier == pinned (all 11 rows, by path).
:163  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
:164  T316-DEADPATH-CENSUS: corpus=1400 deadFiles=75 deadOccurrences=108 …
:192  reference oracle (https://…/actuator/health) probe = up
:711  CENSUS wrong ledger implementations — discovered 14 registered as DELIBERATELY …
:728  all 14 wrong ledger implementations DIED through this harness, not by hand.
:698  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
```

**A final confirming run**, taken after this handoff was committed and from a tree that held
still start to finish, is `out/T402-BAR-final.txt` — it grades commit `0574a3b7` (this handoff).
Its exit code, its probe line and its two frontier lines are lines *in that file*, not claims in
this one: `BAR_EXIT=0`, `grep -c 'probe = '` = 1 reading `up`, frontier 11/11, dead-path GREEN
108, `VERDICT: PASS`, `git status --porcelain` empty both before and after. *(T386 paid twice for
the lesson that a bar run is a measurement of a tree, so the tree has to hold still for the
length of it.)*

**Baseline held exactly**: 46 parity / 7884 cells, frontier GREEN at `deadOccurrences 108`,
14 wrong implementations dead, pin 14. My **five** new `.sh` instruments entered the linter's
corpus and put **zero** rows on the fail-open frontier; my new files added **zero** dead paths.
Independently: `50-failopen-lint.py` over both instrument directories → `LINT: PASS`,
Tier 1 = 0, Tier 1B = 0, Tier 2 = 0.

---

## 9. Three of my own errors, recorded

1. **My drive's discriminator matched the repair's own refusal text.** `mz()` counted the bare
   string `MEASURED ZERO`; my refusal message contains *"1 is the status this file reads as a
   MEASURED ZERO"*. The first GREEN run therefore scored **16 fabricated measured-zeros against a
   file that fabricated none** — the same class of error as the one under test, in the instrument
   written to find it. **The drive caught it**, by reporting failure through its exit status,
   which is precisely what `FU-T386-7` asks of a drive. Counter now matches the fabricated
   *output* line. RED and GREEN were both **re-run** with the corrected instrument so they are
   comparable.
2. **I hard-coded the sabotage point at "after 7 calibration searches", then added an eighth
   calibration arm.** The 7 silently started landing somewhere else — a pinned cardinal rotting
   under an edit, `P-86` in miniature, inside my own drive. It is now **derived**: calibration
   runs `git grep -c`, selectors run `git grep -n`, so firing on the first `-n` lands at the
   boundary on any ref however many arms calibration grows.
3. **My first patch-verification attempt carried two dead lines** — a `git apply --directory=/`
   block whose result was discarded and a no-op `patch` invocation. Removed before the instrument
   was run or committed. Recorded because dead code in an instrument is how a reader concludes
   something was checked that was not.

*(T386 recorded four of its own. The convention is worth keeping.)*

---

## 10. Scope and non-negotiables

`git diff --name-only main...HEAD`: **one** file in the grant (`casualty-sweep.sh`) plus
`.softhouse/capture/t402-t386-conditions/` and this handoff.
**Untouched:** `.softhouse/conformance.sh` (T404's), `instruments/oracle-state-baseline.sh`
(T390's), `.softhouse/guards/`, `.softhouse/vectors/`, `.softhouse/bin/`, `.softhouse/patterns.md`
(T392's), `nexus/`, and every file the four patches target.

No money path, no ledger code, no schema, no database, no vector captured, promoted, edited or
re-graded, and no network beyond the bar's own health probe. No floating point. Nothing here
touches deposit-taking, savings wording, name fields, national-ID handling, time zones or payment
rails.

### What I could NOT test

- **The sabotages are shims, not a full disk.** The *mechanism* is driven end to end — ARM R's
  `EACCES` and ARM U's `ENOENT` are real filesystem errors, and Z3 drives the witness directly —
  but I did not exhaust a real filesystem to reach it. I claim the mechanism, not a field
  incidence rate.
- **One host only** (macOS, git 2.50.1, Apple Git-155). `-P` availability and `\b` behaviour are
  platform-regex properties; the `SWEEP OBSERVE` line prints them on every run precisely so a
  different host shows up in the transcript, and it now says `NOT REPORTED` rather than guessing
  when `-P` is unavailable.
- **I did not wire the sweep into `conformance.sh`** and therefore did not test `T399`'s gate.
  §7 is reasoning about a thing I did not build.
- I reached the reference oracle only through the bar's own probe.
