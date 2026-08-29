# T457 — independent review of T452 (`softhouse/T452-t447-conditions`, tip `dda1f031`)

**VERDICT: APPROVED WITH CONDITIONS.**

Eight conditions, all MINOR or LOW. **No MAJOR.** Nothing in this review overturns a T452 finding;
every substantive claim in the handoff reproduced, several of them by a route T452 did not use.
The conditions are about how three of the numbers are *worded* and *owned*, not about whether
they are right.

| | |
|---|---|
| is the NEW `t388` member real? | **YES — and I built the specimen T452 only inferred.** `exit 0` over a corpus of one file. |
| T457's own fail-OPEN count | **2** — the same two. I read all 35 A2 rows and found no third. |
| the 34 exposed A2 rows | **read; 22 independently carried by measurement, 10 are not searches at all, 3 hand-read. Zero additional members.** |
| K8 partition | **13 + 10 + 6 = 29**, re-derived by a *third* parser. Two sites. Confirmed. |
| the new K8 acceptance test | **genuinely non-vacuous** — driven RED (exit 1, 3 disagreements) on the un-repaired tree and GREEN beside it. |
| `F-T447-3` PIN-not-EXCLUDE | **correct decision.** Argued below, and corroborated by a measurement T452 did not take. |
| bar on T457's own committed work | see §9 |

Host: macOS 25.5.0 arm64, `bash 3.2.57(1)`, `git 2.50.1 (Apple Git-155)`, BSD `/usr/bin/grep`,
`python3`. Every scratch tree in `/tmp`, **outside the repository**, asserted by each instrument
before it writes. Base for the diff: `git merge-base main softhouse/T452-t447-conditions` =
**`cbc8733c`** (`main` has advanced past it; three-dot was used throughout).

---

## 1 · What I re-derived, and with what

Two derivations that share a primitive do not corroborate each other, so where T452 used
`git grep` I used something else.

| T452's claim | my route | outcome |
|---|---|---|
| `t388 :83` is SELF-ONLY, 1 carrier in a 194-file corpus | plain `grep -F` per file over `git ls-files`, **no `git grep` anywhere** | **reproduces exactly** |
| that row is a fail-open | a scratch git repo holding **only** the script — the specimen T452 never built | **EXIT 0**, `SWEEP CALIBRATE+: PASS — known positive matched 2 time(s)`, 18 selectors printing measured zeros |
| `a2-33` pre-repair goes green on a one-file corpus | same, built from `git show cbc8733c:…` rather than T452's evidence copy | **EXIT 0**, corpus 1, 34 patterns, `calibration=PASS` |
| the repair refuses that specimen | same specimen, repaired script | **exit 94** |
| the guard is *not* unfireable | relocate the task dir | **exit 92** (a2-33) / **exit 3** (t388) |
| 34 patterns byte-identical | `grep '^run '` both sides **plus a one-byte mutation control** | **identical, non-vacuously** |
| K8 = 13 + 10 + 6 = 29 | my own `awk` parser over the census's `--- K8` block | **agrees cell for cell**; the published `16+8+6=30` is wrong in all three cells and in the total |
| the classifier's own cardinals | re-ran `t452-classify-v2.py` at the committed tip | **every figure byte-identical**; only the tree qualifier moves (`cbc8733c+17_dirty` → `dda1f031_clean`) |
| all five of T452's drives | re-run at `dda1f031` | **exit 0, `disagreements=0`** each |

---

## 2 · The new `t388` member is REAL. Here is the specimen.

`.softhouse/capture/t388-accrual-capture/30-casualty-sweep-t388.sh:83` is
`git grep -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH"`, with both operands assigned as literals
at `:77`/`:78`; `-lt 1` aborts at `exit 3`. Enforced, PRESENT-direction.

**Carrier set, measured without `git grep`:** the corpus `.softhouse/capture/t388-accrual-capture/`
holds **194 tracked files**; **exactly one** carries the probe, and it is the script itself
(2 occurrences: its own header line and the assignment). Repo-wide at `cbc8733c` the probe
appears in that one file and nowhere else; the only other carriers at `dda1f031` are T452's own
two transcripts. Control: `SWEEP CALIBRATE` is carried by many files and is correctly *not*
reported self-only.

**Driven, not inferred.** A scratch git repo containing nothing but that script:

```
SPECIMEN tracked files: 1
population: 1 tracked files under .softhouse/
SWEEP CALIBRATE+: PASS -- known positive matched 2 time(s) in .softhouse/capture/t388-accrual-capture/
SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus
selectors run: 18   selectors that DID NOT RUN: 0
SPECIMEN EXIT=0
```

Eighteen selectors report `MEASURED ZERO -- engine ran over 1 tracked files … and matched
nothing`, under a calibration that certifies them, at exit 0. **That is the finding, and it is
the same reader-facing outcome the whole T238 repair block exists to remove.**

Two prior passes with purpose-built censuses missed it because **both operands are
variable-indirect**, and T442's census routes any `$`-bearing pattern to `RUNTIME` and counts it
safe on syntax alone. T452 closed that in pattern position *and* in pathspec position, and that
is what surfaced the row. Credit where it is due: this is the most consequential thing in the
task and it is correct.

Reproduction: `bash .softhouse/reviews/t457-review-t452/instruments/t457-failopen-redrive.sh
<subject-tree> cbc8733c` — arms A1/A2/A3.

---

## 3 · My own fail-OPEN count: **2**, and the definition I used

Stated before counting, and deliberately **not** T452's, so that agreement means something.
A row is FAIL-OPEN iff:

1. **ENFORCED** — its search result reaches a control-flow decision that can abort, refuse or
   return non-zero, read over **the whole enclosing block**, not a fixed line window (see
   `C-T457-3`: the window is where T452's mechanical cardinal is soft);
2. **PRESENT-DIRECTION** — the aborting branch is the one taken when the search finds *nothing*,
   so a passing run is a run that found something;
3. **NOT INDEPENDENTLY WITNESSED** — the asserted property can hold vacuously, i.e. every carrier
   of the probe *within the corpus the row's own assertion searches* is the searcher or its own
   task family, **or** every carrier anywhere is an artefact of the same task chain. Clause 3 is
   **stricter than T452's**, because T452's own handoff says its version is unsound.

Counting under that definition on `dda1f031`: **2** — `t388 :83` and `a2-33 sweep.sh` (the
latter repaired by T452). **The stricter clause 3 does not add a third member**; §4 is the work.

I did not adopt T452's definition and then check the count, and I do not think T452 tuned its
definition to the data either: the definition is stated in the instrument header *above the code
that implements it*, its clauses are the same three T447 argued for in the abstract before any
row was classified, and the two members it produces are the two candidates that were already on
the table. What I did find is that one *parameter* inside clause (1) moves the cardinal — that is
`C-T457-3`, and it is a disclosure defect, not a manufactured count.

---

## 4 · The author's declared hole: I read all 34. There is no third member.

> *"Clause (3) … treats a row as safe when ANY other file carries the probe — if those are all
> same-task transcripts in another directory, it is still effectively self-satisfying. 34 A2 rows
> are exposed to it; I re-read only the self-only/family-only rows, not all 34."*

Instrument: `instruments/t457-a2-clause3.py` · transcript `out/T457-A2-CLAUSE3.txt`.
For every row of the `A2. SELF + OTHERS` bucket it replays the row's own flags (parsed back off
T452's transcript) and partitions the carriers **by task namespace** — the two path components
under the instrument root — plus one bucket for carriers *outside* that root, which is the
strongest independence evidence there is: a file no task in this chain wrote.

```
T457-CLAUSE3-RESULT: tree=dda1f031_clean a2_rows=35 independent=22 not_a_search=10 hand_read=3
```

* **22 rows are INDEPENDENTLY CARRIED by measurement** — 10 of them by a carrier outside
  `.softhouse/` altogether, the other 12 across three or more foreign task namespaces. Two worth naming, because they are the two whose independence was
  least obvious from the transcript: `'corpus contains no reversal'` (419 carriers) originates in
  **`docs/adr/DEC-2-gl-accounting-adapter.md`** and in
  **`nexus/internal/apps/ledger/conformance/invariants.go`**, and
  `'CASUALTY SWEEP for the T352'` (12 carriers) originates in **T363's**
  `capture/t363-oracle-baseline/instruments/casualty-sweep.sh`, a different task from the T371
  drive that searches for it. Neither is self-satisfying under any reading of clause 3.
* **10 rows are not searches at all** — `say`/`echo`/`printf` message text whose *words* contain
  `git grep` / `git ls-files`. That includes all three `'ls-files,'` rows, one of which is
  `.softhouse/conformance.sh:1708` itself: `say "conformance:   $REPO_ROOT (git ls-files, whole
  repository); frontier $n, pinned at $p"`. See `C-T457-4`.
* **3 rows I would not let the instrument call safe**, all read by hand:
  * `capture/t424/instruments/t424-comment-claims-drive.sh:161` — `$g_literal` is the loop
    variable of a self-match **detector** iterating literals out of a subject file; probe
    `'#!/usr/bin/env bash'`, 372 carriers, unenforced. Not a class member.
  * `capture/t452-t447-conditions/instruments/t452-t388-vacuous-calibration.sh:104` — T452's own
    **P-22 non-vacuity control** (`CTRL='SWEEP CALIBRATE+'`), which asserts `> 1` carrier. It is
    the opposite of a self-satisfying probe by construction.
  * `reviews/a2-33-dec2-rev5/sweep.sh:94` — member #2, already adjudicated and already repaired.

**Conclusion: the residual T452 named is a real gap in the METHOD and empty as a FINDING on this
tree.** T452 could not say that; it can now, and the instrument that says it is committed.

---

## 5 · The other dispositions

### `F-T447-2` — CONFIRMED, and the new test is genuinely a test

`t457-k8-redrive.sh` re-derives the partition with a **third** parser (mine, over the census's
`--- K8` block) and gets `13 + 10 + 6 = 29`, equal to the census's own printed `== K8 SITES: 29`.
The 13 are exactly the 16 `sel` calls minus `S1`(`:692`), `S3`(`:694`), `S7`(`:702`), which carry
no `|` in their own ERE and so never reach the wide list; the 10 are the `SWEEP_*=$((…))` rows
over 3 distinct counters; the 6 residual are printed in full. The published `16 + 8 + 6 = 30` is
wrong in every cell and in the total.

The second site is real and was spelled as words:
`.softhouse/handoff/T424-t408-conditions.md` at `cbc8733c` reads *"**Sixteen** are the `sel`
calls … **Eight** are `SWEEP_*=$((…))` counters … **Six** are parent-side assignments"* — inside
a paragraph whose own opening sentence says *"All **29** adjudicated"*. `git grep 'all sixteen'`
could never reach it, and T442's recipe reproduces that blindness on a `/tmp` specimen (R2, `0`).

**And the test fails on the un-repaired tree.** Driven, not asserted, in a throwaway worktree
with the pre-repair handoff restored into it:

```
GREEN control (repaired handoff)  : exit=0 disagreements=0
RED     (pre-repair handoff)      : exit=1 disagreements=3
        measured LIVE site set == declared set   expected=same  actual=DIFFERENT  *** DRIVE DISAGREES
        handoff is NOT a live site               expected=0     actual=1          *** DRIVE DISAGREES
        handoff carries the CORRECTED cardinals  expected=3     actual=1          *** DRIVE DISAGREES
```

I also searched the spellings **T452's own detector cannot see** — `\bsel\b` misses
"sixteen SELECTORS", so the same argument that defeated T442 applies one turn further — over all
tracked instrument files, both cardinal cells, digits and words. **17 lines match the
`sixteen…selector` shape and 0 match `eight…counters`**, and every one of the 17 is a *correct*
statement — *"thirteen of the sixteen selectors are `-E`"*, *"all sixteen selectors ran"*. **No
third site.** The arm calibrates its own selector on a known positive before reporting, and it
reports rather than asserting a zero.

### `F-T447-3` — the PIN-not-EXCLUDE decision is CORRECT

I judge it right, on the author's first reason and on a second the author states but does not
demonstrate as sharply as it could have.

* **Self-exclusion is the immunisation anti-pattern the document itself names as the wrong
  repair.** Excluding one's own publication buys a stable number with a permanent blind spot
  under the excluded path — in the one document whose subject *is* blind spots. That trade is
  plainly bad, and `C-T440-1`'s whole lesson is that hiding the row from the census is not fixing
  the control.
* **The drift is a true change in the world**, not an instrument artefact. A newly tracked
  carrier really does change what an ABSENT-assertion measures. Excluding would have made the
  record stable by making it false.
* **And the "member set, not the cardinal" half is verifiable, which is what makes the decision
  more than a preference.** I re-ran `t452-classify-v2.py` at the committed tip and got
  `scripts=1791 searches=454 self_only=1 self_plus_others=35 family_only=2 fail_open=1` —
  **every cardinal byte-identical** to the transcript taken at `cbc8733c+17_dirty`, with only the
  tree qualifier differing. That is the drift-stability claim demonstrated on a *different* tree
  from the one the author demonstrated it on, and it holds because each member's test is relative
  to the corpus its own assertion searches, which no publication can enter. The three probes that
  *are* tree-wide do drift, exactly as predicted: `zzq-t379-nothing`, `zzz-no-such-string-t367`
  and `zzq_nonexistent` measure **8 / 8 / 11** at `cbc8733c` and **10 / 10 / 13** at `dda1f031`.
  See `C-T457-5` for what that does to the filings.

### `F-T447-4` / `F-T447-5` — confirmed at the exact lines

The three post-pipe self-exclusions exist and do what is claimed:
`capture/t244-dec2-rev6/sweep-reverify-sound-engines.sh:51` and `:58`
(`| /usr/bin/grep -v 't244-dec2-rev6'`), and `reviews/a2-31-dec2-rev4/probe-sweep.sh:27`
(`| grep -v 'a2-31-dec2-rev4/probe-sweep.sh'`). `immunised_postpipe=3` in 2 files reproduces, as
does the census-2-vs-row's-own-11 measurement for `a2-33`. One wording note in `C-T457-7`.

### `F-T447-7` — done

`git grep -c 'selfmatching-probe-census.sh' -- .softhouse` no longer returns either line of
`t424-comment-claims-drive.sh`. The three remaining occurrences are the T447 REVIEW, `tasks.json`
and T452's own handoff — all quoting the old name historically. Both of that file's drives re-run
at the tip: `t424-comment-claims-drive.sh` → **exit 0 `disagreements=0`**;
`t442-c1-reproduction-drive.sh` → **exit 0 `disagreements=0`**.

### Scope

18 files, all inside the grant. `.softhouse/conformance.sh` (T454), `.softhouse/bin/ready-tasks.py`
(T451) and `.softhouse/hooks/` (T453) are **untouched** — verified against the three-dot diff.
`.softhouse/handoff/T424-t408-conditions.md` is outside `files_hint` but is named verbatim in the
task's own `F-T447-2` text (*"fix BOTH sites"*), so it is in grant. No money path, no vector, no
schedule figure, no ledger code; the whole change is instruments, transcripts and prose. Nothing
in it touches an integer-minor-units rule, the ledger, `Idempotency-Key`, the tenant
`MathContext (19, HALF_UP)`, or any deposit-facing string.

---

## 6 · Conditions

### `C-T457-1` (MINOR) — the new member is called **STRICTLY VACUOUS** and it is not

`t452-t388-vacuous-calibration.sh` prints *"STRICTLY VACUOUS: it would pass over an empty
corpus"*, the handoff headline says *"SELF-ONLY, enforced, strictly vacuous"*, and
`FU-T452-1`'s title inherits it. **Relocate the script out of the corpus its own `CALIB_POS_PATH`
names and it exits 3** — the guard is fireable, on exactly the property T452 correctly identified
for `a2-33` (*"the guard is not unfireable — move the task directory and it does `exit 92` … what
it fires on is the reachability of 17 files"*). The same narrowing is owed to this row and was
not applied, and the asymmetry runs the wrong way: the member described *more* strongly is the
one whose limb was *not* driven.

The finding survives intact — one carrier is a strictly stronger claim than ten siblings, and the
sentence as literally written ("would pass over an empty corpus") is true. What must change is
the unqualified word, because it is now copied into a paste-ready task entry that the next owner
will act on.

**Repro:** `t457-failopen-redrive.sh <tree> cbc8733c`, ARM A2 →
`SWEEP ABORT (exit 3): CALIBRATION MISSED`, `expected=3 actual=3 OK`.
**Evidence:** `.softhouse/reviews/t457-review-t452/out/T457-FAILOPEN-REDRIVE.txt`.

### `C-T457-2` (MINOR) — the strongest evidence for the headline finding was never collected

`t452-t388-vacuous-calibration.sh` *infers* "it would keep passing over an otherwise empty corpus"
from a carrier count. It never builds the corpus. The sibling `a2-33` drive **does** build the
specimen (arm B) and that is what made `F-T447-1` settleable; P-22 is the program's own rule and
it applies to a fail-open exactly as it applies to a guard. I built it and it is `exit 0`
(§2). **Ask:** fold an arm of that shape into the drive before `FU-T452-1` is handed on, so the
next owner inherits a demonstration and not an inference — and so the drive would go RED if a
future edit made the calibration non-vacuous without anyone noticing.

**Repro:** ARM A1 of `t457-failopen-redrive.sh`.

### `C-T457-3` (MINOR) — the mechanical `fail_open` cardinal is an artefact of a tuned parameter

`direction_of()` reads direction *and* enforcement from a **fixed window of 8 lines** after the
search. Widen it with one `sed` and the published cardinal moves:

```
window  8 : fail_open=1  undecided=1     self_only=1 family_only=2
window 24 : fail_open=0  undecided=2     self_only=1 family_only=2
```

The A2 bucket shows the mechanism: at window 8 the classifier calls **6** A2 rows enforced; at
window 24 it calls **11**. A concrete miss is
`capture/t244-dec2-rev6/sweep-stale-reversal-reason.sh:69` — the search is at `:69`, the
`if [ "${C2:-0}" -lt 1 ] …` at `:75`, and the `exit 8` at `:79`, **ten lines below the search and
two lines outside the window**. The row is genuinely enforced and is reported `enforced: no`.

**The total of 2 survives**, and the reason it survives is the good design in the instrument:
`UNDECIDED` rows are printed in full and hand-adjudicated rather than counted safe, and the
`self_only` / `family_only` **member buckets are window-insensitive** — identical at 8 and at 24.
That is precisely "quote the member set, not the cardinal", the rule T452 argued for in
`F-T447-3`, applying to T452's own headline number one layer further in.

**Ask:** name the window as a limit in the instrument's own printed blind-spot list beside the
three T452 added, and print the member set on the RESULT line beside the cardinal so a cardinal
cannot be quoted without it.

**Repro:** ARM C of `t457-failopen-redrive.sh` (which refuses if its own `sed` selector goes
stale, rather than comparing a file with itself and reporting a stability it did not measure).

### `C-T457-4` (MINOR) — `searches=454` and "34 exposed A2 rows" both count non-searches

T452 names the *"a message string containing the words `git grep`"* false-positive class for the
`unresolved_var` bucket (24 of 29, honestly reported) and for no other bucket. It is not confined
to that bucket: **10 of the 35 A2 rows are `say`/`echo`/`printf` message text**, including all
three `'ls-files,'` rows and, most visibly, `.softhouse/conformance.sh:1708` itself. This inflates
a residual rather than hiding a defect, so it is a disclosure item and not a correctness one — but
the same limit applies to every bucket and is stated for one. **Ask:** move the sentence up to
where the detector is described, and report the count per bucket.

**Evidence:** the `NOT A SEARCH` block in `out/T457-A2-CLAUSE3.txt`.

### `C-T457-5` (MINOR) — `FU-T452-2/3/4` quote carrier counts already stale on the tree they ship in

Measured both ways: at `cbc8733c`, `zzq-t379-nothing` / `zzz-no-such-string-t367` /
`zzq_nonexistent` are carried by **8 / 8 / 11** tracked files — exactly the figures filed. At
T452's own committed tip `dda1f031` they are **10 / 10 / 13**, because committing T452's
transcripts added two carriers to each. That is `F-T447-3` — the finding T452 raised against T442
— recurring inside T452's own filings one layer in, which is the same shape as
`P-80`/`P-86`.

T452 is not blind to it: the entries say *"the count DRIFTS as the class is written about, which
is F-T447-3"*, and two of the three enumerate their carriers by name. But they carry **no sha**,
while the adjudication and the marker file were given `97bad8ed` in the same task. **Ask:** either
qualify the three entries with `cbc8733c`, or drop the cardinal and keep only the enumerated
member list — the figure T452 itself argues is the one to quote bare.

**Repro:** `git -C <tree-at-cbc8733c> grep -l -F zzq-t379-nothing -- . | wc -l` → 8;
same at `dda1f031` → 10.

### `C-T457-6` (MINOR) — two residuals were filed without a task id, and one is the live K8 site

Five residuals got `FU-T452-1..5`. Two did not, and are folded into *"whoever picks up the K8 and
census work"*:

* `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md:102,106,107` — the **one remaining LIVE
  K8 assertion site**, and
* `.softhouse/handoff/T442-t440-conditions.md:73-74`, which still prints
  `T442-CLASS-SWEEP-RESULT: scripts=1704 searches=399 self_only=2 … family_only=3 …` bare.

**Both are genuinely out of grant, not merely hard** — I checked: T452's `files_hint` is
`capture/t424/`, `capture/t452-t447-conditions/`, `reviews/a2-33-dec2-rev5/`, and the one handoff
T452 *did* repair is named verbatim in the task text while neither of these is. So the refusal to
edit them is right. But "fold it into whoever picks it up" is not an owner, and P-45's argument is
that an unowned obligation is not an obligation. The `AUDIT-CLASS.md` case is the sharper one: the
site table declares it `**OPEN**`, so `t452-k8-sites-drive.sh` exits **0 with the defect live** —
correct behaviour for a frontier pin, but the drive's own header calls it *"the acceptance test"*,
and a reader who sees `disagreements=0` may take the tree as clean. **Ask:** give both a
`FU-T452-n` id, and say in the drive's header that exit 0 means "the site set has not drifted",
not "the decomposition is correct everywhere".

### `C-T457-7` (LOW) — "two blind spots were added to the census's own block" is one

Handoff §5 says the census's *own printed blind-spots block* gained two, *"the second being that
the pathspec is variable-indirect too"*. The two headed `Named blind spots of this census — TWO
ADDED BY T452` are in `T442-CLASS-SWEEP-ADJUDICATION.md`; the census script itself gained three
`print()` bullets (flags, post-pipe immunisation, self-membership) and the pathspec-indirection
one is **not** among them. The census's pre-existing text does say *"a pathspec built at run
time"*, which is adjacent but is not the claim — "built at run time" is the *correct* shape,
"holds a same-file literal" is the blind spot. A reader who runs the census gets three bullets and
not the fourth. One `print()` line closes it.

### `C-T457-8` (LOW) — the handoff's bar block contains a line the bar transcript does not

Handoff §9 presents a five-line fenced block under *"BAR TRANSCRIPT:
`capture/t452-t447-conditions/out/T452-BAR.txt`"*. Four of the five check out verbatim or as
plain summary. The third does not:

```
T316-DEADPATH-FRONTIER: rows=108 pinned=108
```

`grep -n 'T316-DEADPATH' out/T452-BAR.txt` returns **one** line and it is
`T316-DEADPATH-CENSUS: corpus=1618 deadFiles=75 deadOccurrences=108 …`. The guard's probe line is
only re-echoed by `conformance.sh` on the *T323-reconciliation* branch; on the clean branch the
bar prints `dead-path frontier: GREEN, and the T323 reconciliation list is empty.` Nor is the
quoted string the guard's own format — run `check-dead-path-frontier.sh` directly and it prints
`T316-DEADPATH-FRONTIER: GREEN rows=108 pinned=108 added=0 removed=0`, with a verdict word and
two cardinals the quoted line does not have. **The frontier genuinely is at its pin** —
`deadOccurrences=108` and `frontier == pinned (all 11 rows, by path)` are both in the transcript,
so the claim is TRUE. What is wrong is that a summary block adopts
**probe-line syntax for a probe line the transcript does not contain**, in a chain whose founding
finding (`C-T440-1`) is *an instrument that shipped a transcript its own code cannot produce*.
Quote what the transcript prints. (My own §9 below is quoted line-for-line from `out/T457-BAR.txt`
for the same reason.)

### Not a condition, recorded

The handoff says *"**34** `A2` rows are exposed"*; the transcript's own header says
`A2. SELF + OTHERS … (35 rows, 21 files)` and my parser reads 35. I read all 35, so the
difference changes nothing, but the two figures should agree.

---

## 7 · Settled, and not reopened

`C-T440-1`; the red/green harness's non-vacuity; byte-for-byte reproduction of the class-sweep
transcript at `97bad8ed`; the 131 `runtime` rows (real blind spot 14); the 23 `unparsed` rows
(0 members); the corpus restriction to `.softhouse/` costing nothing; and `F-T442-1` /
`C-T440-6`. None was re-driven and none is disturbed by anything above.

---

## 8 · What I ran on my own instruments before committing

`P-22` applies to a reviewer's instruments too, and mine caught one of me.

* **My first cut of the 34-pattern byte-compare was itself fail-open.** The `sed` selector I used
  to extract the `run` rows matched **zero** lines on both sides, and `cmp` on two empty files
  printed `BYTE-IDENTICAL: yes`. A green nobody measured, in the review of a task about greens
  nobody measured. The committed arm now **refuses (exit 2)** below two extracted rows and carries
  a one-byte mutation control that must be detected.
* Every instrument takes its subject tree and its pre-repair ref as **required parameters** and
  exits 2 if either stops resolving — no defaults, so a stale input is a hard exit and never a
  silently skipped arm.
* **No path under the instrument root is spelled as a literal in any committed `.sh`/`.py` here.**
  Every one is assembled from `S='.softhouse'`, and both relocated destinations are built at run
  time (`$(dirname …)/t457-relocated-$$`). This is the reflex that refused the first committed bar
  of `T440`, `T446`, `T447`, `T448` and `T452`, and it is why the frontier below did not move.
* The window-sensitivity arm refuses if its own `sed` selector matches nothing, rather than
  comparing a file with itself and reporting stability.
* The alternative-spelling search calibrates its own selector on a known positive and **reports**
  rather than asserting a zero.

---

## 9 · The bar

Run with `bash`, never `sh`/`zsh`; on the finished **committed** tree; scratch in `/tmp`,
**outside the repository**. **Presence of the probe line was tested before its value was read** —
`grep -c 'probe = '` first, because absence is a harness failure and is not `down` (P-84).

**First run, on the substantive commit `673bc5cf`**, in a throwaway worktree at `/tmp/t457/bar`,
`TMPDIR=/tmp`, `git status --porcelain` = **0 paths before and 0 after**. Every line below is
quoted from `out/T457-BAR.txt`, not paraphrased (`C-T457-8` is why):

```
grep -c 'probe = ' -> 1     (PRESENCE tested FIRST; absence would be a harness failure, not `down`)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
conformance:   /tmp/t457/bar (git ls-files, whole repository); frontier 11, pinned at 11
conformance:   frontier == pinned (all 11 rows, by path).
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   T316-DEADPATH-CENSUS: corpus=1616 deadFiles=75 deadOccurrences=108 resolving=1545 indeterminate=121 prose=411
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
BAR EXIT=0
```

**`deadOccurrences` = 108** and **frontier `11 == 11`** — both at their pins, unmoved. The census
corpus went from **1,613** tracked `.sh`/`.py` under the instrument root at `cbc8733c` to
**1,616** here — my three committed instruments, measured, not assumed — and `deadFiles` /
`deadOccurrences` did **not** move, which is the measurement that says
this review's own instruments added no dead literal. That is not luck: every path they name is
assembled from `S='.softhouse'` and both relocated destinations are built at run time, precisely
because this guard has refused the first committed bar of five workers this fire on that reflex.

**Second run, on `c1d970b0`** — `out/T457-BAR-FINAL.txt`, `/tmp/t457/bar2`, 0 dirty before and
after — reproduces all four: `grep -c 'probe = ' -> 1`, `probe = up`,
`frontier 11, pinned at 11`, `deadOccurrences=108`, `VERDICT: PASS (exit 0) — 46 parity vectors …
7884 cells`, `BAR EXIT=0`.

**And the regress is closed rather than waved at.** Commits after a bar are the standing hole in
this pattern — the transcript can only ever describe the tree beneath it. The two commits this
branch adds on top of the last full bar are a prose edit to this file and an inert `.txt`, and
neither is in the census corpus (`git ls-files '.softhouse/*.py' '.softhouse/*.sh'`). The one
guard that could still have moved was therefore run **on the branch tip itself**, clean:

```
tip commit : 7fe72c1328a07702c300092b8d0698dacb06b6ac      dirty : 0
T316-DEADPATH-FRONTIER: GREEN rows=108 pinned=108 added=0 removed=0
T316-DEADPATH-CENSUS: corpus=1616 deadFiles=75 deadOccurrences=108 resolving=1545 indeterminate=121 prose=411
```

`out/T457-TIP-FRONTIER.txt`. Probe-line **presence** tested first (`grep -c … -> 1`), then value.
