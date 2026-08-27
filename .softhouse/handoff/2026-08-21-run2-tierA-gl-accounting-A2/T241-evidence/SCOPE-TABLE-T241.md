# T241 — G-8 STANDING RULE 1: the sentence-by-sentence scope-table rebuild

**Measured at commit `2871f175ed6606d1f7b091e31c180917f3a3ff82`, BEFORE any edit to `gates.md`, as the
rule requires.** Fork point `git merge-base main HEAD` = `2871f175ed6606d1f7b091e31c180917f3a3ff82`
(fork point == HEAD; a clean fork). Re-measured after the edits at the bottom of this file (P-69).

## THE RULE, QUOTED VERBATIM

> 1. **Nobody edits this section without rebuilding the sentence-by-sentence scope table.** Not a
>    grep for the sentence you are changing — a rebuild, claim by claim, of what every sentence
>    asserts and the domain it was measured over. T129's rebuild ran to 117 rows and found six
>    failures, **all six of them scope or disposition statements in a section whose measurements are
>    perfect**. That ratio is the whole reason for this rule.

**T241 DID THE REBUILD. It did not argue that rule 3 discharges it.** The rule triggers on *editing*,
and T241 edits the section (the `## G-8-NOTICE` strike, the T241 discharge note beside T219's bullet,
and the two STANDING RULE 2 roster entries), so it fires directly. T219's declared substitution of a
rule-3 concept sweep is therefore **not** carried forward as precedent.

## THE DENOMINATOR — both terms of the ratio (P-67)

Instrument: `scope_table_t241.py` (python3 `re`; no `grep`, no `rg` — P-75). Output:
`scope-table-t241.json`.

| section | lines | claim units | scope-bearing | NOT scope-bearing |
|---|---|---|---|---|
| LIVE `## G-8 …` (1033–3120) | 2088 | **2129** | **693** | 1436 |
| `## G-8-NOTICE` (3293–3466) | 174 | **175** | **41** | 134 |

**A SECTION-BOUNDARY DEFECT FOUND IN THE PRIOR INSTRUMENT, AND MEASURED, NOT ASSERTED.**
`.softhouse/capture/t223-g8-region-predicate/src/scope_table_t223.py` bounds G-8 as
`## G-8 — TWO phenomena` … `## G-8-NOTICE`. Replaying T223's own enumeration logic verbatim against
`gates.md` **as it stood at T223's parent commit `557ed0ee^`** (`audit_t223_bounds_t241.py`):

```
  T223's block  (G-8 .. G-8-NOTICE)  : 1368 lines, 1416 claim units
  the ACTUAL G-8 live section        : 1196 lines, 1242 claim units
  FOREIGN text enumerated as G-8     :  172 lines,  174 claim units
      foreign: ## G-9 — CLOSED (chart of accounts) …
      foreign: ## G-10 — REFINED by its own independent review …
```

**`1416` reproduces T223's own reported figure exactly**, which confirms T223 measured at its fork
point (correct practice) — and confirms that **174 of those 1,416 units were G-9 and G-10, not G-8**.
The error is **OVER-scoped, not under-scoped**: T223 missed no G-8 sentence by this boundary; its
counts simply are not counts of G-8. `[VERIFIED: audit_t223_bounds_t241.py against
git show 557ed0ee^:.softhouse/gates.md]`

The naive alternative is worse: "end at the next `## `" covers **279 of G-8's 2088 lines (13 %)**,
because G-8 contains ten `## ` sub-headings of its own. T241's instrument ends at the next
`## G-<n>` **gate** heading, which has neither failure mode.

## P-58 — THE CENSUS ON TWO NAMED ENGINES

`census_two_engines_t241.sh`. Engine 1 `git grep -n -P` (PCRE). Engine 2 `/usr/bin/grep -n -E` (BSD
grep, ERE) over a `sed`-extracted range. Engine 3 (primary) python3 `re`. **No bare `grep`, no `rg`.**
Matching **lines**, at `2871f17`:

| net | LIVE `git grep -P` | LIVE `/usr/bin/grep -E` | NOTICE `git grep -P` | NOTICE `/usr/bin/grep -E` |
|---|---|---|---|---|
| R1 largest residual | 4 | 4 | 1 | 1 |
| R2 largest failing principal/disbursement | 7 | 7 | 1 | 1 |
| R3 MNT money figure | 117 | 117 | 12 | 12 |
| R5 total-interest / `n·E + B` identity | 9 | 9 | 1 | 1 |
| R10 the superseded `MNT 10.01` record | 14 | 14 | 6 | 6 |

**Both engines AGREE on every net, in both sections.**

**P-72 calibration ran first and DID ITS JOB.** The first version of this script used
`git grep -c -P … --no-index -- "$TMP/pos.txt"` with the scratch dir under `mktemp -d`. Every net
reported `git -P pos=0 neg=0` while `/usr/bin/grep -E` reported `pos=1 neg=0`, and the script
**ABORTED** instead of publishing five silent zeros. Cause, measured: `git grep --no-index` exits 128
with *"is outside the directory tree"* for a path outside the worktree, and `--no-index` must precede
the pattern. **A census that had skipped calibration would have reported "0 hits, both engines
consulted" and been believed.** Every net's positive and negative is a full sentence, and no negative
is a substring of its positive.

## THE HAND-DISPOSITIONED ROWS — the population rule 1 fires over for T241

The rule fires because **figures moved**: T219 moved three records, and T241 corrects a formula. The
readable population is therefore R1 + R2 + R5 (the record and formula nets) plus every `MNT 10.01`
site — **enumerated, not swept** (the program's stated preference where the population is readable).
**23 rows on R1/R2/R5 + 14 `MNT 10.01` lines in LIVE + 6 in NOTICE.** Each was opened and read in
context.

### LIVE section — 20 rows on R1/R2/R5

| line | what it asserts | domain it was measured over | disposition |
|---|---|---|---|
| 1152 | quotes *"largest unamortized residual is MNT 10.01 at n = 3000"* | — | **LEAVE.** It is the STANDING RULE's own worked example of the seventh mechanism; the quotation is the point. |
| 1384 | `totalInterestAmount 15010.01` from 9 cold starts | T159's cell, named | **LEAVE.** An observation, domain named. |
| 1508 | family-A record exceeded "by more than an order of magnitude" | family A, four record captures | **LEAVE.** Correct over its named family. |
| 1674 | T231 did not sweep for the largest failing disbursement at a short term | — | **LEAVE.** A declared non-look (P-70), correctly phrased as "does not know". |
| 1698 | wider in the largest failing principal — 4499 minor units | `104 ≤ n ≤ 3000`, 600.0 % | **LEAVE.** Current, domain named. |
| 1709 | T219 supersedes T159 as largest failing principal but not as … | named cells | **LEAVE.** Correct disposition. |
| 1712 | "largest failing principal" and "largest unamortized residual" stopped being the same number | since T229 | **LEAVE.** Correct and load-bearing. |
| 1875–1876 | the residual rose MNT 0.01 → 5.01 → 10.01 → **30.00** | each stamped with its worker and term | **LEAVE.** Current, and the causal half is already struck-and-corrected directly beneath. |
| 2292–2294 | **total interest is `n·E + B − principal`**, re-derived on B201/B251/B299/B150 | T229's four family-B cells | **LEAVE — AND THIS IS THE KEY ROW.** The LIVE text has carried the CORRECT formula since T231, with the arithmetic. Confirms the task's premise: the live text is right and only the committed instrument was wrong. |
| 2442 | `totalInterestAmount 15010.01`, 3000/3000 rows at zero principal | T159's cell | **LEAVE.** Observation. |
| 2549–2551 | T219's report of the `site3.py` defect and the correct form | B3001, B4499 | **LEAVE — and DISCHARGED.** T241 appends a labelled discharge note beneath it. |
| 2577 | largest failing principal **MNT 0.23** | 7.0 % / n = 56, T83's grid | **LEAVE.** Correct over its named domain (T223 and T228 both reached the same conclusion). |
| 2580 | largest failing principal **MNT 2.91** | 0.12 % / n = 600, family A | **LEAVE.** Same. |
| 2591–2592 | **MNT 10.01 at n = 3000** | explicitly *"ONLY over the principals those two captures asked, the largest of which is 1001 minor units"* | **LEAVE.** T219 already attached the correct axis and the pointer to MNT 30.00, in bold, in the same bullet. |
| 2599 | balance frozen at 10.01, `totalInterestAmount 15010.01` | T159's cell | **LEAVE.** Observation. |
| 2606 | `totalInterestAmount 2505.01` `[VERIFIED by T170]` | T117's cell | **LEAVE.** Observation, stamped. |
| 2658 | largest failing disbursement anywhere in the record is **MNT 44.99**, residual **MNT 30.00** | everything swept to date, and says so | **LEAVE.** Current, and the bullet explicitly says it is *"a weaker statement than it was"*. |

**LIVE result: 20 rows examined, 0 failures.** Compare T129: 6 failures in 117 rows.

### LIVE section — all 14 `MNT 10.01` lines

1049, 1152, 1377, 1672, 1704, 1876, 2153, 2390, 2440, 2592, 2607, 2615, 2663, 2723. **Every one is
either explicitly labelled superseded/historical, or a quotation carrying its correction in the same
sentence or the next.** **0 live bare claims.** The LIVE section is clean on this figure; T219 and
T231 did this properly.

### `## G-8-NOTICE` — 3 rows on R1/R2/R5, and the 6 `MNT 10.01` sites

| line | what it asserts | disposition |
|---|---|---|
| 3324 | "the largest failing principal **tracks the largest term asked**" | **LEAVE.** T117's reasoning, reported as T117's, and it is precisely the belief T219 falsified — the block is the exhibit. |
| 3385 | table row: T117 MNT 5.01 @ n=1000 · T159 MNT 10.01 @ n=3000 | **LEAVE.** Both measurements are correct and both reproduce. |
| 3427 | `totalInterestAmount 15010.01` from 9 cold starts | **LEAVE.** Observation. |
| 3297, 3317, 3385, 3396, 3398, 3509 | the six `MNT 10.01` sites | **LEAVE ALL SIX FIGURES.** See the argued decision in the handoff, §3. |
| **3396–3399** | ***"Any disclosure of G-8 MUST state the residual WITH ITS TERM"*** | **STRUCK, not deleted, with the correction beside it.** The only IMPERATIVE in the block. |

## WHAT THIS REBUILD COULD NOT HAVE FOUND (STANDING RULE 3 requires this to be written down)

1. **The 693 − 23 scope-bearing rows outside the moved-figure nets were NOT hand-dispositioned.**
   They were enumerated and counted, not read one by one. **This is a declared narrowing (P-40), and
   the residual is named: 670 LIVE rows and 38 NOTICE rows carrying a domain token that is not R1,
   R2, R5 or `MNT 10.01`.** Rule 1's trigger is "the section's figures moved"; the figures that moved
   are the three records and the total-interest formula, and those four nets are what was read in
   full. A rebuild that read all 693 in one task is not something T241 can honestly claim to have
   done. `[UNVERIFIED: that the other 670 rows are clean.]`
2. **A SILENCE.** P-26's own limit: a concept can be restated as an omitted qualification, and no net
   finds a missing sentence.
3. **A CHART or a COUNT IN A SUMMARY TABLE** elsewhere in the file restating a moved record.
4. **Everything outside `gates.md`.** T241's `files_hint` is the t229 capture dir and `gates.md`.
   T228 swept the rest at `617b8ea`; T241 did not re-run that sweep and does not vouch for it.
5. **Whether rule 1's "117 rows" is still the right denominator.** T129 got 117 with a narrower net;
   T223 got 1,416 (174 of them not G-8); T241 gets 2,129 units / 693 scope-bearing. **The three
   numbers are not comparable, and the rule quotes one of them as if it were a standard.** Recorded
   as a follow-up, not acted on.

## RE-MEASURED AFTER THE EDITS (P-69)

At the T241 commit (see handoff for the sha), the same instruments give:

| section | lines | claim units | scope-bearing |
|---|---|---|---|
| LIVE (1033–3168) | 2136 | 2179 | 715 |
| `## G-8-NOTICE` (3341–3562) | 222 | 222 | 62 |

Two-engine census after the edits: **both engines still AGREE on every net.** `MNT 10.01` in NOTICE
reads **7 lines: the 6 genuine SITES, unchanged** (`3369`, `3389`, `3457`, `3468`, `3470`, `3520`),
**plus 1 line of T241's own head pointer.**

**GETTING TO THAT NUMBER TOOK THREE ATTEMPTS INSIDE ONE TASK, AND THAT IS RECORDED HERE RATHER THAN
QUIETLY FIXED, BECAUSE IT IS A P-69 MECHANISM NOBODY HAD WRITTEN DOWN.** The first post-edit
re-measure read **7**; I wrote 7 down; adding one clarifying sentence to the pointer made it **8**;
correcting *that* by naming the six sites verbatim made it **9**. **A count of a file that includes
the sentence doing the counting is self-referential — it moves every time you edit that sentence, and
each correction can make it worse.**

**The fix was to stop stating a count in the file at all.** The in-`gates.md` pointer now states a
**BOUNDARY** instead of a number — *every genuine site lies strictly below this pointer; every
occurrence inside the pointer is navigation* — which is stable under any further editing of the
pointer. The lesson generalises past this block and is worth more than the count was:
**re-measure after your LAST edit, not your first, and never publish a figure whose subject includes
the text stating it.**
