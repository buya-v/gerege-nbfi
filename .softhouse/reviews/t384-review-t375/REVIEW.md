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

## 1. THE FOUR NEW FAIL-OPENS — RE-DRIVEN INDEPENDENTLY

*(section filled in as arms land — see `evidence/10-*` / `evidence/11-*`)*

---

## CONDITIONS

*(none recorded yet)*
