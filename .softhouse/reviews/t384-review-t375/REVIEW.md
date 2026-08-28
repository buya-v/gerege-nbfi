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

## CONDITIONS

*(none recorded yet)*
