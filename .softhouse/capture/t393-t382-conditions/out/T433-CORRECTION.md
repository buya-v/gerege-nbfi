# T433 / C-T423-1 — the correction to T393's false impossibility, and where every echo of it is

**This file is the index. Read it before reading any transcript in this directory.**

## The claim, and that it is false

T393 asserted — in two tracked **executable** files, not only in prose — that no committed
baseline older than `HEAD` exists for the 632 post-fork captured oracle observations, and
reasoned from that impossibility that a committed mutation which also launders the matching
`MANIFEST.sha256` row could not be caught. The two sites, at the merge commit:

| site | text |
|---|---|
| `instruments/10-drive-conditions.sh:220` | *"…has no baseline older than HEAD anywhere in this repository. The docstring says so; this row is the evidence that it says so truly."* |
| `instruments/12-relaunder-manifest.py:14` | *"…there is no committed baseline older than HEAD for those 632 observations."* |

**It is false.** The baseline is **the blob at the commit that FIRST ADDED each observation**,
reachable with `git log --diff-filter=A -- <path>`. It is an object inside an *already
committed* commit, so rewriting `MANIFEST.sha256` inside the mutating commit cannot reach it;
only rewriting `main`'s history can move it.

It was **load-bearing, not a wording slip**: T393's handoff reasoned *from* the impossibility
to direct the next task to build a substitute artefact this repository already contained.

## The measurement — the WHOLE 632, not a sample

T433 re-established the fact rather than inheriting T423's 631/632 or the driver's 21-of-60
sample. Instrument: `.softhouse/capture/t433-t423-c1/instruments/00-t433-whole-632-birth-sweep.py`.
Transcript: `.softhouse/capture/t433-t423-c1/out/00-whole-632-sweep.txt`.

Two **independent derivations** of the birth commit — per-path `git log --diff-filter=A` and
one bulk newest-first walk — which the sweep REFUSES on if they disagree. They agreed 632/632.

| measured at tip `b102875c`, clean tree | count |
|---|---|
| post-fork population (at HEAD, absent at fork `12a7f8d9`) | **632** |
| born at a commit **strictly older** than the tip **and an ancestor** of it | **632** |
| born **at the tip** | **0** |
| still equal to the birth blob **by git OID** (birth tree vs HEAD tree) | **631** |
| still equal to the birth blob **by sha256** (birth bytes vs disk bytes) | **631** |
| **differ** | **1** |
| non-blob (symlink/gitlink) entries | 0 |
| distinct birth commits | 7 |

**The one non-equal observation is `out/A2-370-db-ledger-state.txt`.** Born `aae501b5`
("A2-26: raw-only ledger capture readiness"), legitimately re-captured the same day at
`32ba0fcd` ("A2-26: close the last two mandatory cash slots") with six further ledger rows
(48 → 54) and the double-entry table still balancing in integer minor units. It is
**adjudicated by digest in both directions** in `ARM_F_ADJUDICATED` in
`.softhouse/reviews/A2-11/verify-capture-integrity.py`.

## What was corrected, and where

**Executable sites (bytes changed):**

- `instruments/10-drive-conditions.sh` — the residual row's comment now states the baseline
  and its measurement; the case is renamed `f1-13b-postfork-laundered-CLOSED-BY-ARM-F` and its
  expectation moved from `0 0` (undetected at both refs) to **`0 1` (caught at AFTER)**. The
  DRIVE VERDICT text no longer names it as an exception.
- `instruments/12-relaunder-manifest.py` — the `f1-13b` paragraph quotes what it used to say,
  says it was false, and says what the baseline is. The script still launders, because
  laundering is exactly what ARM F must survive.
- `.softhouse/reviews/A2-11/verify-capture-integrity.py` — boundary item (i) rewritten; **ARM F
  landed as section 8**; new boundary item (iv) states ARM F's own misses by one.
- `.softhouse/reviews/A2-11/run-all.sh` — the section-10 banner quotes the false sentence,
  says it was false, and states the baseline and the measurement.

Each corrected source file **QUOTES the false text verbatim** rather than deleting it, so the
next reader is not left with a bare negation removed. Every quoted line carries the literal tag
`[QUOTED-FALSE-CLAIM]`, which is what lets a guard tell a quotation from an assertion by grep
alone — `30-t433-armf-wiring-guard.sh` asserts **both** that no *untagged* line asserts the
impossibility **and** that the tagged quote is still there, so silencing the guard by dropping
the quote fails the other half.

**Transcripts that echo the claim.** These are records of what the tooling *printed*, and a
record of a false statement is still evidence — deleting the line would destroy the proof that
this program shipped a false claim in tracked executables, which is what C-T423-1 exists to
record. So the bytes are **preserved** and an attributed correction footer is **appended in
band**, by `.softhouse/capture/t433-t423-c1/instruments/40-t433-annotate-echoing-transcripts.sh`
(idempotent, calibrated on a known positive per P-72, and it REFUSES if its sweep matches
nothing rather than reporting a clean repository).

**14 transcripts in scope were annotated** — transcript is
`.softhouse/capture/t433-t423-c1/out/40-transcript-annotation.txt`:

| transcript | line of the echo | handling |
|---|---|---|
| `out/03-runall-after-fix.txt` | 706 | footer appended |
| `out/drive/case-*-AFTER.txt` (11 files) | 706 / 709 / 713 | footer appended |
| `out/05-executable-diff.txt` | 489, 607, 757, 862 | footer appended — it is a `git diff` of T393's own commit, a historical object that cannot honestly be re-derived |
| `.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt` | 706 | footer appended. **NOT regenerated, and here is why:** `bash run-all.sh` on this tree records `RUN-ALL VERDICT: FAIL`, because **section 9 (`adjudicate-section1.py`) is adjudicated 0 and exits 1 on unmodified `main`** — measured at `b102875c` with no ARM F anywhere in the tree (`.softhouse/capture/t433-t423-c1/out/runall-row/runall-control-BEFORE.txt`). Regenerating would commit that failing transcript over a review record on a defect T433 did not cause and does not own. Filed as T433 follow-up **F-6**. |

**And the drives were re-run at the corrected bytes, into NEW directories** — T393's own
transcripts are left where they are, because overwriting them would erase the record of the
transition rather than document it:

| new artefact | what it is |
|---|---|
| `.softhouse/capture/t433-t423-c1/out/20-ARMF-IN-SITU-DRIVE.txt`, `…/out/armf-drive/` | ARM F's own RED→GREEN drive **in situ inside the shipped grader**, plus every miss-by-one T433 could construct |
| `.softhouse/capture/t433-t423-c1/out/50-RUNALL-f1-13b-ROW.txt`, `…/out/runall-row/` | the `f1-13b` row and the control, driven through the **whole `run-all.sh`** at both refs — the direct evidence for the ONE expectation T433 changed in `10-drive-conditions.sh` |

**T393's own `out/DRIVE.txt` and `out/drive/` are left exactly as T393 produced them.** T433
started a full 13-case re-drive of the matrix and **abandoned it**: 26 whole `run-all.sh` runs
was hours of wall clock. Only two rows can change colour when ARM F is added — `f1-13b`, which
ARM F is built to catch, and `control`, which must stay green — and **both were driven**. The
other eleven are argued, not measured, in `50-t433-runall-f1-13b-row.sh`'s header, and the full
re-run is filed as T433 follow-up **F-5**.

**Echoes OUTSIDE T433's scope, disclosed and NOT edited** — searched for with
`grep -rn "older than HEAD\|no committed baseline\|does not exist and cannot be manufactured"`
over the whole of `.softhouse/`, so this is a statement about that search, not about the world:

- `.softhouse/handoff/T393-t382-conditions.md:169` — T393's own handoff, the document that
  reasoned FROM the impossibility. **This is the most load-bearing surviving echo.**
- `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T374.md:240,266` — T374 stated it
  first, as a boundary rather than an impossibility.
- `.softhouse/reviews/t382-review-t374/REVIEW.md:159` — T382 restated T374's boundary.
- `.softhouse/reviews/t423-review-t393/` — quotes the claim **in order to refute it**; correct
  as it stands. Its `out/*-AFTER.txt` transcripts echo the old banner as a record.
- `.softhouse/tasks.json:6441` — the task text of C-T423-1 itself.

Handoffs are append-only records of a past worker's reasoning and are outside T433's assigned
paths; correcting them is a separate task, filed as a follow-up in T433's handoff.

## The arm

ARM F is **section 8 of `.softhouse/reviews/A2-11/verify-capture-integrity.py`**, which
`run-all.sh` invokes as adjudicated section 10. Driven RED then GREEN *in situ* by
`.softhouse/capture/t433-t423-c1/instruments/20-t433-armf-in-situ-drive.sh`; transcripts in
`.softhouse/capture/t433-t423-c1/out/`.

What it still does **not** reach is stated as boundary (iv) in that file and driven, not
asserted: an observation born **at the tip** has no baseline older than HEAD and is reported
`UNGRADED-BORN-AT-TIP` rather than counted as equal; and a rename-and-mutate in one commit
resets its own baseline into that same hole.
