# T384 — independent review of T375 (`softhouse/T375-t364-conditions` @ `2c1f5723`)

**Reviewer:** T384. **Written incrementally, from the first measurement onward** — this fire is
eight hours old and the previous iteration of this review's subject was killed by a rate limit
mid-sentence, so a verdict paragraph exists here from the first commit and is refined, never
appended at the end.

---

## VERDICT (provisional until every section below is marked DRIVEN)

**APPROVED WITH CONDITIONS.** — see the CONDITIONS section at the foot; refined as sections land.

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
merge base is older than today's `main`, which moved `109 → 108` earlier in this fire (T374's
change, and the attribution is not mine to make — I did not need it). **The question that
matters is what the MERGE RESULT does, and I ran it:** `deadOccurrences=108`, identical to
current `main`, with `corpus=1385` — `main`'s 1384 plus exactly one file, T375's own tracked
`drive-red-t375.sh`. **T375 adds a file to the corpus and moves the dead-path count by zero.**
No pin regeneration is required by this merge.

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
| current `main` `d16ee6db` | `G` | 0 | PRESENT | `population=8 … reached-by=3` | `VERDICT: PASS` |

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

## CONDITIONS

*(none recorded yet)*
