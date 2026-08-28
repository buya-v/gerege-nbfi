# The program's own progress accounting is wrong, and it is what makes the migration look stalled

Measured by the driver of fire `20260828-140005` while the batch-1 workers were live. Nothing here changes
a gate; it changes what the next fire should believe about where the program is.

## What `program.json` reports

```
contexts: 17    done: 1
LOC total 854,323   done 182   (0.02%)
```

Read literally that says eleven days of fires have ported **182 lines**. It is not true.

## What is actually on `main`

| Go app | source LOC | test LOC |
|---|---|---|
| `nexus/internal/apps/ledger` | **8,155** | 5,596 |
| `nexus/internal/apps/loanschedule` | **14,662** | 7,222 |
| **total** | **22,817** | 12,818 |

And it is *graded*, not merely written: `bash .softhouse/conformance.sh` on `main` at 14:04 today returned
exit 0 with the probe line present reading `up`, **46 parity vectors / 7,884 cells / 0 FAIL / 0 inadmissible**,
of which **7 are LEDGER parity vectors and 39 are money cells in int64 minor units**, plus 6 oracle-refusal
vectors, with 11/11 deliberately-wrong ledger implementations dying.

## Where the discrepancy comes from

`main_loc` is only credited when a **whole context** flips to `done`. `tierA-gl-accounting` is 24,000
Fineract LOC carrying slices A1/A2/A3, and **all three still read `pending`** although A2 has produced the
8,155-line ledger above and its parity vectors. So the entire Tier-A GL effort scores **zero**, and the only
credited context is tier 0 at 182 LOC.

**This is a measurement defect, not a delivery one.** It has a cost: a driver reading the cursor sees a
stalled program and cannot tell harness debt from real absence of progress. Filed as **`T351`**.

## The finding that survives the correction

Over **385 distinct tasks ever filed** (current `tasks.json` plus every archived run):

| class (by `files_hint`) | all | terminal |
|---|---|---|
| harness / `.softhouse/` | 279 (72.5%) | 234 (**72.7%**) |
| port (`nexus/`) | 68 (17.7%) | 56 (17.4%) |
| vector | 29 (7.5%) | 24 (7.5%) |
| docs | 8 (2.1%) | 7 (2.2%) |

**Nearly three quarters of everything this program has completed is work on its own instruments.** And the
current queue continues it: of the **22 READY tasks** at the start of this fire, **zero** port Fineract code
and **zero** capture a vector. Every one is harness or process repair.

A fair defence exists and should be stated: the harness is the *grading instrument*, and a wrong instrument
produces confident wrong parity claims — which is the one failure this program cannot recover from, because
cutover is graded on it. The instrument code proper is also not large: `guards` 1,669 + `bin` 5,232 +
`conformance.sh` 4,132 ≈ **11,000 lines**. The other ~175k of `.sh`/`.py` under `.softhouse/` is *captured
evidence* (`capture/` 121k across 5,610 files, `reviews/` 53k across 1,450), which is the corpus, not machinery.

But the defence does not extend to *72.7% forever*, and it does not explain a READY queue with **no port and
no vector work in it at all** on the one fire type that can reach the oracle. The harness is now good enough
to grade 46 vectors green; the next fires should be spending that capability, not extending it.

## Driver decision (PRODUCT/ENGINEERING, `chosen_by: agent`, reversible by Buyan)

**From the next fire, an oracle-reachable fire must dispatch at least one vector-capture or port task before
any harness-debt task, unless the bar on `main` is RED.** Harness repair continues, but it stops being the
default. Recorded here rather than asked, per CLAUDE.md § Answering gates. Nothing in this touches cutover,
licensing or regulatory sign-off, all of which remain hard `user` gates.

---

## SUPERSEDED FIGURES — corrected 2026-08-28 by fire `20260828-140005` iter2

Two numbers in this file were wrong and are corrected here, at the place they are NAMED, rather than
retyped throughout (T248/T258/T340).

1. **"46 parity vectors … of which 7 are LEDGER" conflates two corpora that `conformance.sh` keeps
   separate.** T369 re-derived by RUNNING the bar and summing each corpus's own case table, and T370
   reproduced it independently. The figures are: **53 parity vectors / 0 FAIL**; **8,026 ALL-CLASS graded
   cells**; **7,980 cells graded BY PARITY VECTORS** — quote 7,980 whenever the sentence says "parity".
   loanschedule 51 rows → 7,884 cells (7,859 parity + 4 contract-refusal + 21 self-test fixture cells the
   harness itself labels EXCLUDED FROM THE PARITY COUNT); ledger 13 rows → 142 (121 parity + 21
   oracle-refusal). "46 parity vectors" is **loanschedule-only** and is correct only when scoped that way.

2. The `1.04%` figure produced by the first version of `progress-report.py` was a **49× overstatement** —
   it divided Go lines written by Fineract Java lines to port. T369 caught it (P0); T370 deleted the ratio
   rather than re-dividing it. The honest coverage figure is **0.02%**. The capture output at
   `.softhouse/capture/t351-progress-accounting/live-report-20260828.txt` still shows `1.04%` and is
   **deliberately left unedited** — it is a captured witness, and editing it to match a later truth would
   forge one.
