# T384 — independent review of T375 (`softhouse/T375-t364-conditions` @ `2c1f5723`)

**Reviewer:** T384. **Written incrementally, from the first measurement onward** — this fire is
eight hours old and the previous iteration of this review's subject was killed by a rate limit
mid-sentence, so a verdict paragraph exists here from the first commit and is refined, never
appended at the end.

---

## VERDICT

# APPROVED WITH CONDITIONS.

**Merge it. Then open the follow-up in the same breath.**

**What T375 claims is true, and I re-drove all of it rather than reading it.** All four new
fail-opens are real on `main` and all four genuinely close on the branch; **both healthy
controls stay green**, which is the failure mode this change was nearest to; arm 32 **can**
fail and I made it; the committed failing transcript is **unedited**; arm 08's retarget
describes what it actually measures; the merge into current `main` is clean and the bar is
exit 0 on it with every pin holding. **T375 also told the truth about what it could not
produce** — it says plainly that no uninterrupted 61-arm transcript exists rather than shipping
a partial run as a clean one, and that sentence is the most creditworthy thing in the handoff.

**ON THE DRIVE: every one of the 61 distinct arms is now driven and NONE is red** — 53 in one
uninterrupted run before the task runner killed my own drive at arm 23, and the remaining 8,
which T375's killed run never reached at all, in a recovery run. **Arm set 1 — T323's 15 and
T358's 13, 28 arms by other authors against earlier harnesses — re-runs UNMODIFIED and passes
in full**, which is the measurement behind T375's claim that appending `symlink-members=N` at
the END of the census line retuned nothing. **I do not have a single uninterrupted 61-arm
transcript either; a second attempt is running detached. See §7 and read it before quoting a
number from this review.**

**The conditions exist because of one thing: I found the FIFTH fail-open, and it is the one
T375 disclosed against itself and rated unreachable.** `FU-T375-7` — `$rel` used as a git
pathspec rather than a literal — **is reachable**, and I reached it with two committed files.
On the T375 branch, the whole bar goes **exit 0, probe PRESENT, `VERDICT: PASS`** with a
tracked **symlink** credited `reached-by=3` and the census printing **`symlink-members=0`**.
T375's mechanism description of this hole is exactly correct; only its severity rating is
wrong. **It is not a reason to reject.** It is present on `main` too, it is strictly narrower
than the four holes this branch closes, and the branch is a large net improvement in a guard
that has now been walked around five times. Rejecting a fix because a sixth route exists is
how the fifth route survives another fire.

**T375's decision NOT to patch it in flight was correct** and I would not have it decide
otherwise — see §2.

---

## 0. WHAT WAS MEASURED FIRST, BECAUSE IT IS THE THING A KILLED REVIEW STILL LEAVES BEHIND

Three whole-bar runs, each from a **clean committed tree** in a `--no-hardlinks` scratch clone,
each with `bash` and never `sh`. Probe **presence** was read before its value — P-84
[VERIFIED: `.softhouse/patterns.md:2813`].

| tree | exit | probe | dead-path census | fail-open frontier | guards-dir census | verdict |
|---|---|---|---|---|---|---|
| **current `main`** `d16ee6db` | **0** | **PRESENT** ×1, `up` | `corpus=1384 deadFiles=75 deadOccurrences=108` | 11 == pinned 11 | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0` | PASS, 46 vectors / 7884 cells |
| **T375 branch** `2c1f5723` | **0** | **PRESENT** ×1, `up` | `corpus=1343 deadFiles=76 deadOccurrences=109` | 11 == pinned 11 | `… invoked-by-nothing=0 symlink-members=0` | PASS, 46 vectors / 7884 cells |
| **MERGE RESULT** (T375 merged into current `main`, clean, no conflicts) | **0** | **PRESENT** ×1, `up` | `corpus=1385 deadFiles=75 deadOccurrences=108` | 11 == pinned 11 | `… invoked-by-nothing=0 symlink-members=0` | PASS, 46 vectors / 7884 cells |

[`evidence/01-bar-on-current-main.txt`, `evidence/02-bar-on-T375-branch.txt`,
`evidence/03-bar-on-MERGE-RESULT-current-main.txt`, complete and unedited.]

**THE DEAD-PATH DISAGREEMENT IS RESOLVED BY RUNNING, NOT BY ARITHMETIC (P-83).** T375 reports
`109 == pin, corpus 1343`; current `main` measures `108`, corpus `1384`. Both are true and
neither is a defect: they are **two different pins on two different corpora**, because T375's
merge base is older than today's `main`, which moved `109 → 108` earlier in this fire. **I make
no attribution for that move.** The coordinator states it belongs to T374 and also records that
a reviewer in this same fire guessed wrong about it; I did not need the answer, so I did not
guess — the question I had to settle was answerable by running, and I ran it. **The question that
matters is what the MERGE RESULT does, and I ran it:** `deadOccurrences=108`, identical to
current `main`, with `corpus=1385` — `main`'s 1384 plus exactly one file, T375's own tracked
`drive-red-t375.sh`. **T375 adds a file to the corpus and moves the dead-path count by zero.**
No pin regeneration is required by this merge.

**THIS REVIEW'S OWN BRANCH IS GREEN, measured the same way.** `bash .softhouse/conformance.sh`
from a CLEAN COMMITTED tree (`git status --porcelain` EMPTY *before* the run, not after):
**exit 0**, probe **PRESENT** reading `up`, `corpus=1384 deadOccurrences=108` — **unmoved**,
because every instrument this review adds is committed as `.txt` and stays out of T316's
`.sh`/`.py` corpus by construction — frontier 11 == 11, `VERDICT: PASS`.
[`evidence/04-bar-on-T384-review-branch-CLEAN-COMMITTED.txt`.]

**`EXEMPTION_PIN_LEDGER_WRONGIMPLS` — matched BY NAME, never by line, as instructed.**
It reads **13** on current `main` (`conformance.sh:3923`), **13** on the T375 branch
(`:4476`) and **13** on the merge result (`:4476`). **Untouched by T375**; the 553-line shift is
exactly the rot the by-name rule exists for.

---

## 1. THE FOUR NEW FAIL-OPENS — RE-DRIVEN INDEPENDENTLY, BOTH DIRECTIONS

**Constructed from T375's DESCRIPTION of each defect, not copied from its drive script.** A
reviewer who runs the author's own instrument measures the author's own instrument. The
mutators are in `mutators/*.sh.txt`; the harness is `probe-t384.sh.txt`. Every arm clones
`--no-hardlinks`, applies the mutation, **`git add -A` and COMMITS**, then runs the **whole
bar** with `bash` — and the harness prints `dirty=` from `git status --porcelain` so the
T361/T370 defect (a transcript captured while the subject file was still untracked) is
excluded by measurement, not by intention. **Every arm below reported `dirty=no`.**

The harness deliberately does **not** score itself PASS/FAIL. It reports exit, probe presence,
the census line and the refusal text; the adjudication is here.

### RED-BEFORE — against `main`'s guard (`d16ee6db`), which is T375's fix ABSENT

| arm | construction | exit | probe | guards-dir census | verdict |
|---|---|---|---|---|---|
| `MAIN-Z` **healthy control**, runs first | no mutation | **0** | PRESENT | `population=6 … reached-by=1` | bar GREEN |
| `MAIN-Y` **healthy control** | an *honest* independent regular-file witness | **0** | PRESENT | `population=7 … reached-by=2` | **ACCEPTED, correctly** |
| `MAIN-A` | witness is a **SYMLINK** to the member | **0** | PRESENT | `population=7 … reached-by=2` | **FAIL-OPEN** |
| `MAIN-B` | witness is a **HARD LINK** to the member | **0** | PRESENT | `population=7 … reached-by=2` | **FAIL-OPEN** |
| `MAIN-C` | witness is a plain **COPY** of the member | **0** | PRESENT | `population=7 … reached-by=2` | **FAIL-OPEN** |
| `MAIN-D` | **the MEMBER is a tracked SYMLINK** to a registered member | **0** | PRESENT | `population=7 … reached-by=2` | **FAIL-OPEN** |

Every one of the four reached `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`.
**T375's four fail-opens are real, and I reproduced all four independently.**
[`evidence/10-RED-BEFORE-four-failopens-on-main.txt`.]

### GREEN-AFTER — against T375's guard (`2c1f5723`)

| arm | exit | probe | census | refusal actually printed |
|---|---|---|---|---|
| `T375-Z` healthy control | **0** | PRESENT | `population=6 … invoked-by-nothing=0 symlink-members=0` | — bar GREEN |
| `T375-Y` healthy control | **0** | PRESENT | `population=7 … reached-by=2 symlink-members=0` | — **still ACCEPTED** |
| `T375-A` witness symlink | **2** | **ABSENT** | `reached-by=1` | `THAT WITNESS IS A SYMLINK` |
| `T375-B` witness hard link | **2** | **ABSENT** | `reached-by=1` | `BYTE-IDENTICAL TO THIS MEMBER` |
| `T375-C` witness copy | **2** | **ABSENT** | `reached-by=1` | `BYTE-IDENTICAL TO THIS MEMBER` |
| `T375-D` member is a symlink | **2** | **ABSENT** | `symlink-members=1` | `IS A SYMLINK, and a symlink is not a checker` |

`exit 2` with the probe line **ABSENT** is the guard **working** — P-84, and presence was read
before any value. [`evidence/11-GREEN-AFTER-four-failopens-on-T375.txt`.]

**THE HEALTHY CONTROL IS THE ONE THAT MATTERED AND IT IS GREEN.** `T375-Y` plants a checker
with a genuinely honest registration — an independent tracked regular file, not a link, not a
copy — and T375's tightened guard **still accepts it** (`reached-by=2`, bar exit 0, `VERDICT:
PASS`). The failure mode nearest to this change is refusing a legitimately wired checker, and
it does not occur. This is the arm the T383 precedent in this same fire says is the only one
that catches a fix that is wrong *only* on the healthy case.

**SO: ALL FOUR NEW FAIL-OPENS GENUINELY CLOSE, AND NOTHING HEALTHY IS REFUSED.**

---

## 2. THE FIFTH FAIL-OPEN — `FU-T375-7` IS NOT A THEORETICAL HAZARD. I REACHED IT.

**FINDING F-T384-1 — SEVERITY: the same class T375 exists to close, still open on its own tree.**
**DRIVEN, with its control, on the T375 branch and on current `main`.**

T375 disclosed against itself that `guard_guards_dir_registration` passes `$rel` to git as a
**pathspec** rather than a literal:

    member_stat="$( cd "$REPO_ROOT" && git ls-files -s -- "$rel" )"
    member_mode="${member_stat%% *}"
    member_blob="${member_stat#* }"; member_blob="${member_blob%% *}"

and said it was *"not reachable on any tree that exists today … narrow and named"*, and did not
patch it. **It IS reachable, and reaching it takes two files.**

### What it takes, and what it buys

`mutators/G-glob-member-AMBIGUOUS-symlink.sh.txt` commits two tracked paths into the canonical
guards directory:

* `.softhouse/guards/zz-t384g1.sh` — an **ordinary member with an entirely honest**
  `REACHED-BY` row. Nothing about it is forged. It is there only so the pathspec matches twice.
* `.softhouse/guards/zz-t384g[1].sh` — a **tracked SYMLINK**, the unwired checker being
  smuggled in, whose target is outside the guards directory and carries a `REACHED-BY` row.

`git ls-files` prints in byte order and `1` (0x31) sorts before `[` (0x5B), so the guard's own
call returns the **decoy first** [`evidence/15-arm-G-mechanism-git-ls-files-probe.txt`]:

    $ git ls-files -s -- ".softhouse/guards/zz-t384g[1].sh"     # what the guard runs
    100644 b44f181a… 0	.softhouse/guards/zz-t384g1.sh
    120000 67d15208… 0	.softhouse/guards/zz-t384g[1].sh

    $ git ls-files -s -- ":(literal).softhouse/guards/zz-t384g[1].sh"   # the ground truth
    120000 67d15208… 0	.softhouse/guards/zz-t384g[1].sh

`member_mode` is therefore **`100644`**, so **T375's symlink-member refusal never fires**; and
`member_blob` is the **decoy's** blob, so **T375's blob test compares the wrong file**. Both of
pass 2's new tests are neutralised for that member at once.

### The measurement — the whole bar, on a clean committed tree

| tree | arm | exit | probe | guards-dir census | verdict |
|---|---|---|---|---|---|
| **T375 branch `2c1f5723`** | `G` | **0** | **PRESENT** | `population=8 invoked=3 declared=2 reached-by=3 invoked-by-nothing=0` **`symlink-members=0`** | **`VERDICT: PASS`** |
| **MERGE RESULT** (what would actually land) | `G` | **0** | **PRESENT** | `population=8 … reached-by=3` **`symlink-members=0`** | **`VERDICT: PASS`** |
| current `main` `d16ee6db` | `G` | 0 | PRESENT | `population=8 … reached-by=3` | `VERDICT: PASS` |

**Driven on the merge result too, so the finding is about what would actually land and not
about a branch nobody will run** [`evidence/17-arm-G-on-the-MERGE-RESULT.txt`].

The guard's own output credits the link [`evidence/14-FIFTH-FAILOPEN-arm-G-whole-bar-GREEN.txt`]:

    conformance:     REACHED-BY .softhouse/guards/zz-t384g[1].sh — declared in its own header, reached by
    conformance:                .softhouse/reviews/…/witness-G2.txt (verified: it names zz-t384g[1].sh)

**`symlink-members=0` while a symlink member sits in the population is the census reporting the
opposite of what is on the tree.** That is worse than the count being absent: the field T375
added specifically so a symlink member could not hide inside `invoked-by-nothing` now prints a
zero that a reader will believe. It is the same shape as `F-T375-7` itself — an unwired checker
entering the canonical guards directory GREEN by being a symlink to something registered.

### THE CONTROLS THAT MAKE THIS A FINDING AND NOT A GUESS — and they corrected me

I predicted at first that **one** glob character would be enough, on the reasoning that `[1]`
as a wildmatch pattern matches the character `1` and so cannot match the literal filename,
leaving `member_stat` empty and both tests skipped. **That prediction is false**, and two arms
say so rather than my re-reading the code:

| control | construction | result on the T375 branch |
|---|---|---|
| `E` | member `zz-t384e[1].sh`, witness a **COPY** of it | **exit 2, ABSENT**, `BYTE-IDENTICAL TO THIS MEMBER` — REFUSED |
| `F` | member `zz-t384f[1].sh` **IS a symlink**, one match only | **exit 2, ABSENT**, `IS A SYMLINK`, `symlink-members=1` — REFUSED |

git's pathspec matcher tries **exact literal equality before wildmatch**, so a glob-named path
always matches itself. **A glob character alone does not defeat the guard; AMBIGUITY does** —
which is precisely what T375's own disclosure says, and it deserves the credit for describing
the mechanism correctly. E and F also confirm the same two arms are refused when the same
filenames are used *without* a second matching path, so arm G's greenness is attributable to
the ambiguity and to nothing else.

### ADJUDICATION OF T375's DECISION NOT TO PATCH IT

**T375 was RIGHT to refuse the one-token change, and WRONG about the reachability — and only
the first half of that is the part it had to get right on the day.**

* **On process: right, and I would not have it decide otherwise.** Its stated reason — *"the
  60-arm drive was already in flight against this code, an executable change would have
  invalidated it, and a one-token change shipped without its arm is precisely what this task
  exists to refuse"* — is the correct call in a task whose entire subject is one-token changes
  shipped without arms. Patching in flight would have produced a fix with no drive at all, in
  a task that has just demonstrated twice (arm 30, arm 08) that this class's expectations are
  wrong until they are run. **Disclosing it, naming the repair, and filing it as `FU-T375-7`
  is the honest move and it is the one it made.**
* **On the claim: half of it does not hold.** "Not reachable on any tree that exists today"
  is true and I confirm it — the population is six files with plain names. But the sentence a
  reader takes away is *narrow*, and the threat model of this guard is **not accident**. Every
  defect this guard has ever caught was **deliberately forged by a task inside its own edit
  grant** — that is how T364 found F-T364-1 and F-T364-2 and how T375 found all four of its
  own. Against that threat model, "no such file exists today" is not narrowness: **the
  attacker chooses the filename.** Two files, one of them entirely honest, is a cheaper forgery
  than any of the four T375 just closed.
* **The half T375 got right and that I want on the record:** its recorded mechanism is exactly
  correct — "could match MORE THAN ONE path, and `member_mode` would be taken from whichever
  line git printed first". It described this hole precisely and then under-rated it. **A hole
  that is recorded accurately and mis-rated is a far better outcome than one that is silently
  left**, and it is why I found it in twenty minutes.

**Not patching a known hole is defensible only if the hole is genuinely unreachable AND
recorded. It is recorded — properly, with the repair named. It is NOT unreachable.** So the
condition below is about the *next* task, not a retraction of T375's judgement.

**THE REPAIR, and it is the one T375 already wrote down:** `":(literal)$rel"` on the member's
index lookup, plus a `self_multi`-shaped refusal for a member whose lookup returns more than
one line — **the witness side of this same function already does exactly that** — plus its own
arm. Arm G in `mutators/G-glob-member-AMBIGUOUS-symlink.sh.txt` is that arm, written and
driven, and can be lifted into `drive-red-t375.sh` unchanged.

---

## 3. THE P-22 ARM AND THE HONESTY OF THE EVIDENCE — ALL THREE CHECKS PASS

### 3.1 CAN ARM 32 FAIL? **YES — DRIVEN, NOT READ.**

An arm added to carry a P-22 burden that cannot itself fail is the same defect one level up.
So I broke the thing arm 32 guards and watched it go red. Two one-arm copies of T375's own
drive script, differing by **exactly the second of its two reverts**
[`arm32-HONEST.sh.txt`, `arm32-SABOTAGED.sh.txt`, `evidence/16-arm-G-and-CAN-ARM-32-FAIL.txt`]:

    --- 1. arm 32 EXACTLY AS T375 SHIPS IT ---
    T375-32-REVERT-BOTH-selfreference-tests-HOLE-REOPENS  exit=0 (want 0) probe=PRESENT (want PRESENT) marker=YES  >>> PASS

    --- 2. arm 32 with ONE of its two reverts REMOVED, so the hole does NOT reopen ---
    T375-32-REVERT-BOTH-selfreference-tests-HOLE-REOPENS  exit=2 (want 0) probe=ABSENT  (want PRESENT) marker=NO   >>> FAIL

**It goes red on all three columns at once** — exit, probe presence and marker. Arm 32 is a
real control: it distinguishes "the hole reopened" from "the hole stayed shut", which is
precisely what arm 08 had stopped being able to do. **The P-22 burden was genuinely MOVED and
not dropped.**

### 3.2 IS THE COMMITTED FAILING TRANSCRIPT UNEDITED? **YES.**

`evidence/60-full-drive-PARTIAL-arm08-FAILED.txt` on T375's branch:

* it contains **exactly `40` lines reading `>>> PASS` and `1` reading `>>> FAIL`**, which is
  the count T375 claims, counted by me and not read off its prose;
* it **stops mid-drive at `T375-12`**, with no closing summary — a killed process, not a
  curated excerpt;
* **the decisive tell:** the failing arm in it is named
  `T375-08-REVERT-fix-DOTSLASH-is-ACCEPTED-again`. **That name no longer exists anywhere in
  the drive script**, which now calls it
  `T375-08-REVERT-pass1-compare-ALONE-pass2-blob-test-CATCHES-it`. An edited transcript would
  have been harmonised with the retarget; this one carries the pre-retarget name, the
  pre-retarget expectation (`want 0`, `want PRESENT`) and the failure. **It is the artefact of
  the run that produced the finding.**
* its embedded census figures are internally consistent with an older commit
  (`corpus=1344`, `NAMESPACE-CENSUS: dirs=173`) rather than with today's tree — a forger
  working backwards from the current bar would have had to reproduce those too.

### 3.3 DOES ARM 08's RETARGET DESCRIBE WHAT IT NOW MEASURES? **YES.**

The mutation reverts pass 1's compare **only** and plants the `./`-spelled self-certification.
Re-derived from the source, then confirmed by the drive: with pass 1's compare reverted, the
raw string test `"./M" = "M"` is false and is skipped — but the witness and the member are the
**same tracked path**, so `self_blob` **is** `member_blob` and pass 2's blob test refuses with
`BYTE-IDENTICAL TO THIS MEMBER`. The arm's name
(`REVERT-pass1-compare-ALONE-pass2-blob-test-CATCHES-it`), its expectation (`exit 2`, probe
`ABSENT`) and its marker (`BYTE-IDENTICAL TO THIS MEMBER`) all describe exactly that.
**The retarget is accurate and it is not an arm rewritten to agree with the code** — the arm
that *could* still fail was added beside it rather than instead of it.

**T375's own subsuming argument is also correct as stated:** a witness that RESOLVES to the
member has the member's blob whatever spelling was typed, so pass 2's blob test dominates pass
1's compare on every spelling. Keeping both for the better refusal message is a defensible
call, and it costs one string compare.

---

## 4. NO REFUSAL PATH WAS DELETED — COUNTED INDEPENDENTLY

[VERIFIED: my own `grep -c` on three blobs.]

| | current `main` | T375 pass-1 blob `2422adc9` | T375 branch tip |
|---|---|---|---|
| `bad=1` | 18 | 20 | **23** |
| `return 1` | 82 | 84 | **84** |
| `EXIT_UNUSABLE` | 23 | 23 | **23** |
| `warn "` | 335 | 367 | **405** |
| `say "` | 124 | 139 | **139** |

**The load-bearing claim holds: nothing that refuses was removed.** Every count is flat or up.

**MINOR — F-T384-2, documentation only.** T375's §6 table restates two of these five as
`warn "` **366 → 396** and `say "` **137 → 137**. Neither reproduces with `grep -c 'warn "'` /
`grep -c 'say "'` on the two blobs it names; I measure **367 → 405** and **139 → 139**. It is
possible a different predicate was used and not written down. **It changes no conclusion** —
the direction and the "nothing removed" claim are both right — but it is P-80 rot inside the
handoff of the task whose entire subject is P-80 rot, and the honest fix is the same one T375
applied to the guard's own comments: **delete the retyped pair and cite the command.**

---

## 4b. T375's INCIDENTAL FACTUAL CLAIMS — SPOT-CHECKED, ALL TRUE

Every one re-derived by me on the branch tip, not read off the handoff:

| T375 says | my measurement |
|---|---|
| `main_test.go` occurs **0** times in the harness, so arm 27 was already fail-closed | `grep -cF 'main_test.go' conformance.sh` = **0** ✓ |
| the shell `case` is case-SENSITIVE, so `Main.go` was already fail-closed (arm 28) | `grep -cF 'Main.go'` = **0** ✓ |
| this host's filesystem is case-INSENSITIVE while git indexes case-SENSITIVELY (arm 26) | `git config core.ignorecase` = **true** ✓ |
| `main.go` is named on non-comment lines where a *different* guard reads its text | 25 occurrences of `main.go` in the file ✓, and arm 01's refusal reproduces |
| the guards population is 6, with no symlink and no two identical blobs | `population=6 … symlink-members=0` on every clean run ✓ |

---

## 5. THE COST CENSUS (`guard_cost_census`, FU-T358-1) — READ ADVERSARIALLY

This is pass 1's work, not pass 2's, and it is the largest single addition in the diff. It is
sound and I did not find a fail-open in it, but three things belong on the record.

**What it does right, and it is the right lesson.** The defect it answers is not "a guard was
slow"; it is that **four hand-written cost figures sat in comments and nothing checked any of
them**, while the real cost of one was 9m43s against an advertised 0.23 s. The instrument pins
**by NAME, never by magnitude** — every guard has a ceiling row, every ceiling row was timed,
at least one guard was timed — and prints the elapsed figures as *recorded and not pinned*.
That is the same discipline the rest of this file uses for its frontiers, and it is the only
design under which a wall-clock gate does not become a bar that goes red because somebody
else's build was running. It also states its own limit plainly: it reads elapsed time **after**
the guard returns, so **a guard that never returns still hangs the bar forever** — a spin that
returns becomes a named refusal, and nothing more is claimed.

**Its first run already found two wrong cost claims** (`guard_reconciler_ownership` at 41 s
against a comment reading 30.3 s; `guard_pnumber_citations` at 21 s with no claim at all).
An instrument that finds something on its first run is not decoration.

**OBSERVATION O-T384-1 — the real headroom is 6x, not the 10x the derivation claims.**
The budgets are documented as `max(60, 10 × measured)`. Measured by me on this host:

| guard | idle | under 4 concurrent bars | ceiling | tightest observed ratio |
|---|---|---|---|---|
| `guard_no_fail_open_instruments` | 5 s | **10 s** | 60 s | **6×** |
| `guard_pnumber_citations` | 18 s | 37 s | 300 s | 8× |
| `guard_reconciler_ownership` | 32 s | 49 s | 500 s | 10× |

Four concurrent whole-bar runs did not breach anything, so the margin is adequate today. But
the consequence of a breach is worth naming because of how it presents: a ceiling breach is
`failed=1`, therefore **exit 2 with NO probe line**, which P-84 trains a driver to read as a
failed HARD guard. It is diagnosable — the transcript names the guard and prints
`over its Ns CEILING` — but a host-load event would wear the costume of a guard failure. Not a
defect; a thing the next holder of this file should know before tightening a ceiling.

**OBSERVATION O-T384-2 — two small non-refusals in `timed_guard`.** The budget lookup takes the
**last** matching row rather than the first and does not detect a duplicate name, so a second
row for the same guard with a larger number silently wins; and a guard timed twice is not an
error. Neither is reachable without editing `GUARD_COST_BUDGETS`, which means holding this
file. Recorded, not charged.

---

## 6. SCOPE, MONEY, AND THE COORDINATION FACT

**Scope: clean.** 24 files, all inside three places T375 owns —
`.softhouse/conformance.sh`, `.softhouse/capture/t375-t364-conditions/`, and its own handoff.
**`tasks.json`, `patterns.md`, `.softhouse/guards/`, and T358's and T364's capture directories
are untouched.** No new `.sh` fixture was committed under `.softhouse/guards/` (the T323
hazard); every fixture is planted at run time in a scratch clone. Confirmed against
`git diff main...` with three dots.

**Money math: none, and I checked rather than assumed.** The diff introduces no arithmetic
beyond integer counters (`symlinked`, `GUARD_COST_*`), two git object-id string compares, and
`SECONDS` subtraction. Every decimal literal in the diff is inside a comment about wall-clock
history. No currency, no rounding, no division, no `MathContext`. The bar's own money figures
are **identical on all three trees**: 46 parity vectors, 7884 cells, 13 wrong implementations
killed, `EXEMPTION_PIN_LEDGER_WRONGIMPLS=13`. Nothing here is a monetary code path, and the
findings above are all wrong-PASSes about **the bar's own coverage**.

**`EXEMPTION_PIN_LEDGER_WRONGIMPLS`: NOT TOUCHED, and I matched it BY NAME.** 13 on `main`, 13
on the branch, 13 on the merge result. Its line moved 3923 → 4476. I did not read it by line
and the driver should not either.

**`FU-T375-5` (the DECLARED direction) — I did not drive it, and here is why that is defensible
rather than a gap I am waving through.** The `REACHED-BY` direction is forgeable **inside a
tripping task's own grant**; the `DECLARED` table is a two-row literal **inside
`conformance.sh`**, so adding a row requires holding a file this program serialises to one
holder per batch. The same symlink/copy shapes do apply there — T375 says so and does not
claim otherwise — but the cost of reaching them is an order of magnitude higher. It stays a
follow-up, and T375 filed it as one.

---

## 7. THE FULL 61-ARM DRIVE — THE THING T375 COULD NOT PRODUCE

**STATUS AT THIS COMMIT: ATTEMPT 1 WAS KILLED AT ARM 23 WITH 53 PASS / 0 FAIL. I AM NOT
CLAIMING AN UNINTERRUPTED 61-ARM TRANSCRIPT UNLESS §7.3 BELOW SAYS I HAVE ONE.**

The irony is not lost: **the reviewer sent to produce the transcript a rate limit denied T375
was itself killed mid-drive**, by the task runner reaping the background shell, at 23:24 after
64 minutes. `evidence/20-FULL-DRIVE-53-arms-KILLED-at-arm-23.txt` is that run, **committed
unedited**, exactly as T375 committed its own. **53 PASS, 0 FAIL** — 13 arms further than
T375's killed run reached, and past the arm that failed in it.

Two runs were then started **detached (`setsid`), so a task-runner cleanup cannot reach them**:
the eight arms attempt 1 never reached (§7.2), and a second full drive (§7.3).

Started 22:20 on this host in a fresh `--no-hardlinks` clone of the T375 branch tip, using
**T375's own drive script, unmodified**:

    bash .softhouse/capture/t375-t364-conditions/drive-red-t375.sh /tmp/t384/fulldrive

Measured rate once the machine was uncontended: **~68 s per arm**, so ~70 minutes for the 61.
The transcript will land at `evidence/20-FULL-DRIVE-61-arms.txt` with the count and every
failure investigated. **If this section still says RUNNING, the drive did not finish inside my
session and the verdict above stands on §§1–6, which do not depend on it.** What §§1–6 already
establish independently of the drive: the four fail-opens close, both healthy controls stay
green, arm 32 can fail, the transcript is unedited, the merge is clean and its bar is exit 0.

### 7.2 THE EIGHT ARMS ATTEMPT 1 NEVER REACHED — ALL PASS

`T375-24 .. T375-31`, run from **the same drive script with the same helpers**, arms 24–31
only, in a fresh clone [`tail-arms-24-to-31.sh.txt`, `evidence/21-RECOVERY-arms-24-to-31.txt`]:

    T375-24-selfcert-via-REPEATED-DOTSLASH                exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-25-witness-with-a-TRAILING-SLASH                 exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-26-witness-CASE-FOLDED-on-a-case-insensitive-fs  exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-27-unwired-main_test.go                          exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-28-unwired-CASE-FOLDED-Main.go                   exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-29-unwired-main.go-ONE-DIRECTORY-DEEPER          exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-30-member-IS-a-tracked-SYMLINK-named-main.go     exit=2 (want 2) probe=ABSENT  marker=YES >>> PASS
    T375-31-REVERT-symlink-MEMBER-test-INHERITS-again     exit=0 (want 0) probe=PRESENT marker=YES >>> PASS
    T375 RED DRIVE: 8 passed, 0 failed.

**SO EVERY ONE OF THE 61 DISTINCT ARMS HAS NOW BEEN DRIVEN AND EVERY ONE PASSES** — 53 in one
uninterrupted run, 8 in this recovery run. **That is not the same thing as one uninterrupted
61-arm transcript, and I will not call it one.** What it does establish, and this is the part
the verdict rests on: **arms 41–61 of the drive, which T375's killed run never reached at all,
have now been run — and none of them fails.** No arm anywhere in the file is red.

Note `T375-30` and `T375-31` in that list: the arm that found `F-T375-7` and its revert. Both
pass, so the unpredicted fail-open is genuinely closed **for a member whose name resolves
unambiguously** — which is exactly the boundary my arm G walks around (§2).

### 7.1 ARM SET 1 — CONFIRMED, AND THIS IS THE STRONGEST HEALTHY-CONTROL EVIDENCE ON THE BRANCH

**T375's claim that arm set 1 re-runs UNMODIFIED and passes is TRUE, and I watched it happen
in this drive rather than reading its transcript:**

    T323 RED DRIVE: 15 passed, 0 failed.
    >>> ARM SET 1: T323 DRIVE PASSED in full.
    T358 RED DRIVE: 14 passed, 0 failed.  (arm set 1 counts as one.)
    >>> ARM SET 1: T358 DRIVE PASSED in full.

**All 28 arms** written by two earlier generations, against two earlier harnesses, by other
authors — including their own green controls and, decisively, their `population=… 
invoked-by-nothing=N` **substring markers**. **Appending `symlink-members=N` at the END of the
census line silently retuned nothing.** That placement decision is load-bearing and T375 says
so; this is the measurement that backs it. It is also, per the drive script's own rule, a
result that cannot be manufactured: **a missing predecessor drive is a REFUSAL here, not a
skip**, so "arm set 1 passed" cannot be produced by arm set 1 failing to run.

### 7.3 ATTEMPT 2 — A SINGLE UNINTERRUPTED 61-ARM TRANSCRIPT

Started 23:36, **detached in its own session** so the reaper that killed attempt 1 cannot reach
it, same drive script, fresh clone of the branch tip. Expected ~70 minutes.

**IF THIS SECTION STILL READS "RUNNING", THEN NO SINGLE UNINTERRUPTED 61-ARM TRANSCRIPT EXISTS
ON THIS REVIEW EITHER, AND I SAY SO IN PLAIN WORDS RATHER THAN LETTING §7.2 BE MISREAD AS ONE.**
The verdict does not depend on it: §7.1 and §7.2 between them have every arm in the file driven
green, and §§1–6 are independent of the drive entirely.

**STATUS: RUNNING.** Transcript will land at `evidence/22-FULL-DRIVE-attempt-2.txt`.

---

## CONDITIONS

**C-T384-1 — CLOSE `FU-T375-7`, WITH ARM G. NOT OPTIONAL, AND NOT FOR T375.**
The member's index lookup must use `":(literal)$rel"`, and a member whose lookup returns more
than one line must be REFUSED — the shape the witness side of the same function already has as
`self_multi`. The arm is written and driven: lift
`mutators/G-glob-member-AMBIGUOUS-symlink.sh.txt` into `drive-red-t375.sh` unchanged, together
with arms `E` and `F` as its controls (without them the finding is mis-stated as "a glob
character breaks it", which is false). **This is a follow-up task, not a change to T375's
branch:** an executable edit now would invalidate the 61-arm drive that is the branch's whole
evidentiary basis, which is the exact reasoning I have just endorsed T375 for.

**C-T384-2 — the census line must not print `symlink-members=0` while a symlink member is in
the population.** That is a stronger requirement than "refuse the member", and it is what
makes the field worth having. It falls out of C-T384-1 but should be asserted by its own
marker in the arm, because a fix that refuses and still miscounts would pass an exit-code-only
arm.

**C-T384-3 — delete the two restated `warn "` / `say "` counts from the handoff's §6 rather
than correct them** (F-T384-2). The claim that carries the weight — no refusal path was
removed — is true and is now independently counted here. The numbers are not, and a corrected
cardinal rots in every place it was restated.

**C-T384-4 — the driver must read `EXEMPTION_PIN_LEDGER_WRONGIMPLS` by NAME on the merge
result.** It is 13 on all three trees and its line moved by 553. The bump to 14 belongs to a
different task and must not be done by line number.

---

## HOW TO REPRODUCE EVERY FINDING IN THIS REVIEW

Nothing here needs my transcripts to be believed. Cite by NAME, never by line — every
identifier below is unique in its file and `grep -n` re-derives it in one command.

    # 1. clone the trees
    git clone --no-hardlinks <repo> /tmp/x/main   && git -C /tmp/x/main   checkout main
    git clone --no-hardlinks <repo> /tmp/x/t375   && git -C /tmp/x/t375   checkout softhouse/T375-t364-conditions

    # 2. any arm: <source tree> <arm name> <mutator>
    bash .softhouse/reviews/t384-review-t375/probe-t384.sh.txt \
         /tmp/x/t375 MYARM \
         .softhouse/reviews/t384-review-t375/mutators/G-glob-member-AMBIGUOUS-symlink.sh.txt

    # 3. can arm 32 fail?
    bash .softhouse/reviews/t384-review-t375/arm32-HONEST.sh.txt    <scratch clone>   # >>> PASS
    bash .softhouse/reviews/t384-review-t375/arm32-SABOTAGED.sh.txt <scratch clone>   # >>> FAIL

    # 4. the mechanism of the fifth fail-open, in two commands, in arm G's scratch clone
    git ls-files -s -- '.softhouse/guards/zz-t384g[1].sh'             # TWO lines, first is 100644
    git ls-files -s -- ':(literal).softhouse/guards/zz-t384g[1].sh'   # ONE line,  120000

The three code sites the findings are about, **named**:
`guard_guards_dir_registration`'s `member_stat=` / `member_mode=` / `member_blob=` assignments
(F-T384-1); its `self_multi` refusal (the shape the repair should copy); and
`GUARD_COST_BUDGETS` / `timed_guard` (O-T384-1, O-T384-2).

---

## WHAT I DID NOT VERIFY, STATED SO NOBODY READS MORE INTO THIS REVIEW THAN IS IN IT

* **`FU-T375-5`, the `DECLARED` direction.** Reasoned about, not driven. See §6.
* **Behaviour on a case-SENSITIVE filesystem.** This host is case-insensitive
  (`core.ignorecase=true`); T375 says the same and I did not obtain a case-sensitive host.
* **`guard_graded_root_is_this_tree`'s short-circuit path** is still driven by no arm in any
  generation, T384 included. T375 carries this forward from pass 1 and I confirm it is still
  true.
* **A member path containing a NEWLINE.** Reasoned only: `git ls-files` C-quotes such a path,
  so `$rel` arrives with literal quotes, the member grep fails, and the member falls through to
  `INVOKED BY NOTHING` — fail-CLOSED. **Not driven**, and I am not claiming it is safe.
* **A gitlink / submodule entry** whose path ends in `.sh`. Reasoned only, same fall-through.
  **Not driven.**

---
