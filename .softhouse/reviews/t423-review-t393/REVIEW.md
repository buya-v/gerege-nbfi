# T423 — INDEPENDENT review of T393 (`softhouse/T393-t382-conditions`, 11 commits, tip `66ab2af9`)

> **This review was written by the SECOND T423 worker.** The first was killed mid-flight after
> committing four instruments and their transcripts at `a12a9a83` and **before writing any
> verdict** (`git ls-tree -r --name-only softhouse/T423-review-t393` carried no `REVIEW.md`).
> Under this program's rule a killed worker's output is a **hypothesis**, so every one of its
> instruments was re-run here and the agreement recorded per instrument. §1 is that reckoning.
> Everything from §5 on is new work the first worker did not do.

## VERDICT: **APPROVED WITH CONDITIONS**

T393 closes all four of T382's conditions. Every load-bearing number reproduces independently,
both F-4 arms reproduce **byte-identically to the first worker's transcripts and to T393's own
cited line numbers**, the merge into today's `main` is clean, and the bar is EXIT 0 with the
probe line present on T393's tree *and* on the merge result.

Four conditions follow. **C-1 is MAJOR** and it is a claim, not a code defect: T393 ships — in
two places — an **impossibility statement that is false**, and this review closes the case it
says cannot be closed, with a drive. None of the four blocks the merge; all four are cheap.

---

## 1. THE FIRST WORKER'S EVIDENCE, RE-RUN. ALL FOUR AGREE.

| instrument | committed transcript | my re-run | agrees? |
|---|---|---|---|
| `00-t423-independent-counts.py` | `out/00-t423-counts.txt`, `FAILURES: 0` | `out/T423-2-rerun-00-counts.txt`, exit 0 | **YES — byte-identical apart from the `ROOT` header line** (its root was the predecessor's now-gone worktree `agent-a75cccdd02b9587f5`; mine is `agent-a8c2fb441a2f25761`) |
| `10-t423-f4-rerun.sh` | `out/T423-MATRIX.tsv`, 6 rows, `unexpected results: 0` | re-run to `/tmp`, exit 0 | **YES — `diff` of the two matrices is EMPTY**, all six rows including the two probe shas being different commits each run |
| `20-t423-birth-blob-probe.py` | `out/20-birth-blob-probe.txt` | `out/T423-2-rerun-20-birth-blob-probe.txt` | **YES — byte-identical, whole file** |
| `30-t423-extra-drives.sh` | `out/T423-EXTRA-DRIVES.txt` | `out/T423-2-rerun-30-extra-drives.txt` | **YES — byte-identical, whole file**, both drives |

**No disagreement was found.** The predecessor's evidence is promoted from hypothesis to
finding. [VERIFIED: the transcripts named above, all in this directory.]

---

## 2. THE NUMBER SET EVERYTHING RESTS ON — RE-DERIVED INDEPENDENTLY

`00-t423-independent-counts.py` is a **second implementation**, not T393's
`00-verify-t382-counts.py` re-invoked: populations come from `git ls-tree` with the observation
directories **named on the command line** (T393 lists the whole capture directory and filters
the first path component in Python), the manifest goes through a different parser, digests are
recomputed with `hashlib` **and** cross-checked against coreutils `shasum` on a sample. It
exits 1 on any disagreement, so a disagreement could not read as a pass.

| what | T382 → T393 | T423 measured |
|---|---|---|
| ARM A population at the fork sha `12a7f8d9` | 403 | **403** |
| ARM B population at HEAD | 1035 | **1035** |
| post-fork observations (HEAD − fork) | 632 | **632** |
| `MANIFEST.sha256` rows | 1139 | **1139** |
| of which under `out/` or `req/` | 1035 | **1035** |
| tracked observations with NO row / rows naming NO file | 0 / 0 | **0 / 0** |
| manifest digest vs disk: agree / disagree / unreadable | 1035 / 0 / 0 | **1139 / 0 / 0 over ALL rows**, 1035 of them observations |
| post-fork observations covered by a row | 632 of 632 | **632 of 632** |
| fork-sha manifest rows / obs / non-obs | 430 / 403 / 27 | **430 / 403 / 27** |
| of the 27, byte-identical to the fork sha today | 25 | **25** |
| the differing set | `{CAPTURE-PLAN.md, cap.sh}` | **exactly those two** |

Two identities that make the set self-checking and that I re-derived rather than accepted:
`403 + 632 == 1035`, and `1139 == 1140 − 1` (every tracked file under the capture directory
except `MANIFEST.sha256`, which carries no row for itself). Both hold.
[VERIFIED: `out/T423-2-rerun-00-counts.txt`, exit 0, `FAILURES: 0`.]

**Clean.** T393 did not inherit a number it had not measured, and neither did I.

---

## 3. F-4 — THE CONDITION THAT REINSTATED THE ORIGINAL DEFECT. BOTH ARMS DRIVEN.

`10-t423-f4-rerun.sh` is a **second driver**: its own selector for the mutation target, its own
`perl` matcher for the one-line constant move, its own column parsers, and — the detail that
matters — a `sec4_named` counter **anchored to section 4's own output line** so that section
10's banner *quoting* the defect is not miscounted as section 4 *printing* it. (T393 had to fix
exactly that bug in its own driver at `094520e1`; the second driver does not share the code
that was fixed.)

| case | ref | section 10 | run-all rc | verdict | section 4 named `out/A2-000-…http` | ARM A pop |
|---|---|---|---|---|---|---|
| `f4a` control — mutate a fork-sha observation, constant NOT moved | BEFORE `4eeed2b3` | 1 | 1 | FAIL | 1 | 403 |
| `f4a` control | AFTER `fc51790d` | 1 | 1 | FAIL | 1 | 403 |
| **`f4b` — the ONE-LINE constant move** | **BEFORE** | **0** | **0** | **PASS** | **1** | **1035** |
| **`f4b`** | **AFTER** | **2** | **1** | **FAIL** | 1 | 1035 |
| `residual` — post-fork mutation, manifest row laundered in the same commit | BEFORE | 0 | 0 | PASS | 0 | 403 |
| `residual` | AFTER | 0 | 0 | PASS | 0 | 403 |

**The `f4b` BEFORE row is T362's F-1 reproduced verbatim in one transcript, and I confirmed it
line by line rather than by summary** — `out/T423-case-t423-f4b-move-fork-constant-BEFORE.txt`
line **288** `DIFF out/A2-000-glaccounts-preexisting.http`; lines **693/694** ARM A collapsed to
`1035 observations {'out': 906, 'req': 129}`, identical to ARM B; line **746** `10  0  0  as
adjudicated`; line **749** `RUN-ALL VERDICT: PASS`. Those are the same line numbers T393 cites
for its own transcript, independently produced.

**At the post-fix bytes the same move trips four independent tripwires**, and I counted them in
my own transcript rather than taking T393's word: `out/T423-case-t423-f4b-move-fork-constant-AFTER.txt`
lines **729** and **734** (the two `FORK_TIES` refusals), **751** (`ARM A's population is 1035
observations, and it is PINNED at 403`), **834** (`ARM E's population is 104 entries, and it is
PINNED at 27`), **883** `VERDICT: REFUSED (exit 2)`.

**The `f4a` control is what makes the `f4b` row mean anything** — same committed mutation, the
constant left alone, caught at *both* refs. So `f4b`'s BEFORE `PASS` is caused by the constant
move and nothing else. **F-4 is genuinely closed.** [VERIFIED: `out/T423-MATRIX.tsv`, re-run
`diff`-identical.]

### 3a. THE ATTACK T393's DRIVE DOES NOT COVER, AND WHICH I RAN: MOVE THE CONSTANT IN ALL THREE FILES

`f4b` moves the constant in **one** file, so both halves of the repair fire at once and the
transcript cannot distinguish "the ties caught it" from "the pins caught it". An attacker who
has read the file moves it in **all three** tracked files, which satisfies `FORK_TIES` entirely
and leaves only `FORK_OBS_PIN` / `FORK_NONOBS_PIN` standing. **That is the case that decides
whether F-4 is closed or merely inconvenienced, and neither T393 nor the first T423 worker ran
it.** I ran it: `instruments/50-t423-fork-tie-defeat.sh`, **results in §10 — the repair holds on
the population pins alone, with zero tie refusals.**

---

## 4. F-1 — THE TRUE SIZE OF THE RESIDUAL, AND WHERE I LOOKED

T374 disclosed **one** uncovered case; T382 measured **four more**; T393 closed all five (ARM C
for committed mutation/deletion/addition, ARM D with `lstat` for untracked fabrication and
same-bytes symlink) and disclosed one residual. I looked in four places for a sixth:

1. **The `f1-13b` laundered residual itself.** Real, and re-driven: `residual` rows above,
   `0 / PASS` at **both** refs. T393's disclosure of it is accurate. **But its accompanying
   impossibility claim is false — see C-1.**
2. **The tracked files in the capture directory that no arm reads.**
   `instruments/40-t423-ungraded-census.py`: of 1140 tracked files under
   `.softhouse/capture/tierA-a2`, ARMs A–D cover the 1035 under `out/`+`req/` and ARM E covers
   27 of the remaining 105. **78 are graded by no arm** — `MANIFEST.sha256` itself plus **77
   post-fork non-observation files**: `cap8.sh`, `cap9.sh`, `cap10.sh`, `mkreq7.py`,
   `resolve7.py`, `resolve8.py`, every `run-*.sh` that produced the 632 post-fork
   observations, six `sql/q*.sql`, and — note — **`prove-a2-7-additive.py`, one of the two
   files `FORK_TIES` anchors to**. Driven, not merely counted: see §6 DRIVE 1. **C-2.**
3. **Emptying or deleting `MANIFEST.sha256`.** Read from source: deletion → `refuse(...)`
   exit 2; emptying → `no_row` = 1035 → exit 1, and the ARM C positive control fails too.
   **No gap. Clean.**
4. **A symlinked *directory* under `out/`.** `os.walk` does not follow directory symlinks, so
   its contents would not be enumerated — but every tracked file beneath it then appears in
   `absent_on_disk` and ARM D fails by name. **No gap. Clean.**

---

## 5. C-1 (MAJOR) — T393 SHIPS AN IMPOSSIBILITY CLAIM THAT IS FALSE, AND I CLOSED THE CASE IT SAYS CANNOT BE CLOSED

**What is shipped, in two tracked places:**

* `verify-capture-integrity.py`, DOES-NOT-COVER block (i): *"Closing this needs a committed
  baseline OLDER than HEAD for the post-fork observations, **which does not exist and cannot be
  manufactured here**."*
* `run-all.sh`, section 10 banner: *"**There is no committed baseline older than HEAD for those
  632.**"*

The claim originates one task earlier — T374's follow-up #1 reads *"632 of the 1035 tracked
observations have no baseline older than HEAD"* — and T393 restated it as an **impossibility**
rather than testing it.

**Such a baseline does exist: the blob at the commit that FIRST ADDED each observation.** It is
immutable for precisely the reason ARM A's fork blob is immutable — reaching it requires
rewriting `main`'s history, not editing a working tree — and no same-commit manifest rewrite
touches it. It requires **no new artefact at all**.

**Measured, not argued** (`20-t423-birth-blob-probe.py`, re-run byte-identical): all 632
post-fork observations have a recorded `--diff-filter=A` add commit (0 missing, so no rename
hole), **631 of 632 still equal their birth blob** on a clean tree, and the single exception
`out/A2-370-db-ledger-state.txt` is adjudicable by digest exactly as ARM E already adjudicates
its two. Seven distinct birth commits cover the set.

**Driven both ways, because a proposal whose failing case was never run is a hope — T393's own
standard:**

| grader | on the CLEAN T393 tree | on a repo carrying the laundered residual |
|---|---|---|
| `verify-capture-integrity.py` (section 10) | exit 0, `VERDICT: PASS` | **exit 0, `VERDICT: PASS`** — the gap |
| proposed **ARM F**, `60-…-birth-arm-reaches-residual.py`, adjudication list EMPTY | exit 1, names `A2-370-db-ledger-state.txt` (**RED first, P-22**) | — |
| proposed **ARM F**, one digest pair adjudicated | **exit 0, `VERDICT: PASS`** | **exit 1, `LAUNDERED-OR-MUTATED out/A2-200-glaccounts-live-precheck.http`** |

[VERIFIED: `out/60-armf-clean-RED-unadjudicated.txt` (exit 1), `out/60-armf-clean-GREEN-adjudicated.txt`
(exit 0), `out/T423-ARMF-DRIVE.txt` (exit 0 — *both* directions as expected),
`out/T423-armf-section10-on-laundered.txt` (exit 0/PASS),
`out/T423-armf-armF-on-laundered.txt` (exit 1/FAIL). The laundered repository is a scratch
clone in `/tmp`; **no captured observation in any tracked tree was mutated.**]

**Why this is MAJOR rather than cosmetic.** This file's own contract is *"the boundary is
stated, not implied"*, and its docstring says an understated boundary *"is the defect this file
exists to punish"*. T382 punished T374 for exactly that. A **falsely absolute** boundary is the
same failure with the sign flipped, and it has a concrete cost already visible in the record:
T393's handoff §7.2 tells the next task that closing the residual *"is genuinely new work — a
baseline the capture scripts cannot rewrite"*, and directs the narrowed T374 follow-up #1 at
building one. **A 25-line arm over material already in the repository closes it.** Without this
correction the next worker builds an artefact it does not need.

Note the delicious symmetry, which is why the first worker went looking: T393's *own* correct
observation is that `MANIFEST.sha256` lacks the property "regenerated only by an explicit
capture task", because `manifest.py` sits in the same directory and rewrites it. The birth blob
has that property inherently — nothing in the working tree can reach it. **I confirm T393's
correction of T374's follow-up #1 is right, and that it stopped one step short of the answer.**

**CONDITION C-1.** Replace both impossibility sentences with the measurement, and file ARM F as
a dispatchable task (P-89: a paragraph is not a task) — or fold it into `T425`, which already
owns this file. Suggested drive: `bash 61-t423-armf-red-drive.sh` must stay exit 0, i.e. section
10 red on the laundered repo instead of the ARM F stand-in. **Do not fold it in as a drive-by:
the adjudication of `A2-370-db-ledger-state.txt` needs a stated reason, which I did not
establish** — I measured *that* it differs from its birth blob, not *why*. [UNVERIFIED: the
reason for that one legitimate change.]

---

## 6. C-2 (MINOR) — 77 POST-FORK CAPTURE SCRIPTS ARE GRADED BY NOTHING, AND THE BOUNDARY BLOCK DOES NOT SAY SO

ARM E's population is the **27** non-observation entries in the **fork-sha** manifest. The
manifest at HEAD holds **104**. The other **77** — the scripts that produced the 632 post-fork
observations and the red/green evidence that grades them — are read by no arm: ARM C filters to
`out/`+`req/`, ARMs A/B/D are `out/`+`req/` only, ARM E's population is the fork manifest, and
**section 4 compares fork-sha manifest entries, so a post-fork file is outside its third arm
too**.

Driven, not merely counted (`30-t423-extra-drives.sh`, DRIVE 1, target `cap8.sh` — tracked, has
a manifest row, outside ARM E): committed unlaundered mutation →
**section 10 = 0, run-all rc = 0, `RUN-ALL VERDICT: PASS`, and section 4 did not name it either
(`section4-named-it = 0`)**. Nothing in `run-all.sh` sees it. [VERIFIED: `out/T423-EXTRA-DRIVES.txt`
and my re-run `out/T423-2-rerun-30-extra-drives.txt`, transcript `out/T423-drive1-nonobs-postfork.txt`.]

This is **outside T382's condition** — F-3 named the 27 — so T393 did not fail to do assigned
work. What it did do is leave the population unnamed in a `DOES NOT COVER` block that names
much smaller gaps. **CONDITION C-2: name the 77 in the boundary block.** Closing it is a
one-line population change (ARM E over the *current* manifest's non-observation rows against
whichever baseline is available), but that is design work for `T425`, not a review demand.

---

## 7. C-3 and the two remaining judgements

**ARM B's missing `try/except` — T393's reasoning for NOT fixing it.** Confirmed present at
`verify-capture-integrity.py` ARM B: `at_head = git("show", "HEAD:" + rel)` with no handler,
where ARM A and ARM E both carry `except subprocess.CalledProcessError`. Driven by DRIVE 2 (a
`PATH` shim failing exactly one `git show HEAD:<path>`, which is the honest shape of a corrupt
object or a gc race, without corrupting a repository): **exit 1, traceback printed, ARM C / ARM
D / ARM E headers reached 0 times, no `FAILURES:` line, no `VERDICT:` line** — and exit 1 is
also the genuine-mutation code, so the operator cannot tell which population was compared.

**I accept T393's reason for not fixing it** — editing the graded file after the drive ran would
make the committed matrix and the committed instrument different bytes, which is the exact
disclosure T382 had to make about its own matrix. That is the right call and it is fail-closed.
**CONDITION C-3 (MINOR): it is filed nowhere executable.** `T425` is filed for the wiring;
nothing in `tasks.json` owns the ARM B repair. T393 itself invoked **P-89** — *"prose does not
fire on the next fire"* — for the wiring and then left this one as prose. File it, with the red
drive DRIVE 2 already provides.

**The wiring recommendation (T425), judged.** Sound, and correctly not acted on.
`grep -c 'run-all.sh' .softhouse/conformance.sh` = **0** on today's merge result, as is
`grep -c 'A2-11'` and `grep -c 'verify-capture-integrity'` — so every section four tasks have
hardened runs only by hand. The distinction T393 draws is right: `run-all.sh` rewrites the
**tracked** `TRANSCRIPT-A2-11.txt` on every run, which is the shape `guard_no_fail_open_instruments`
already diverts to scratch; section 10 writes nothing and already has 0/1/2 with 2 = REFUSED.
The cost argument holds at both ends: the bar's own census on my merge-result run reads
**`GUARD-COST CENSUS: 15 guards timed, 70s total wall, ceiling breaches 0, unbudgeted guards 0`**
— T393's quoted figure, still exact — and the `git show` count is **403 + 1035 + 27 + 1 = 1466**
by reading the loops, so "roughly 1465" is right. [UNVERIFIED: T393's `1:05` / `1:51`
wall-clock figures. I did not re-time them; this host was running drives throughout, and a
timing taken under contention would be a worse number than the one it disputed.]

**"Two moved baseline figures were not its own."** `git diff --name-only 1eacb63e <T393 handoff
commit 1fd1624f>` = **42** paths, of which `\.go$|^nexus/|^\.softhouse/vectors/|ledger` matches
**0**. Verified exactly. At the branch **tip** the figure is **43**, the extra path being
`out/08-CONFORMANCE-FINAL.txt` — the final-bar transcript committed after the handoff was
written. The zero-match result holds at both. **C-4 (LOW): the number is stale at the tip by
one, for a benign and self-evident reason.** Naming it because this program grades cited
numbers, not intentions.

---

## 8. THE TWO MERGE HAZARDS — REAL, AND NOT YET DANGEROUS

1. **ARM C's set equality is load-bearing on `MANIFEST.sha256`.** Confirmed by source and by
   T393's own driven cases 14/15: adding or removing any file under `tierA-a2/{out,req}` without
   re-running `manifest.py` **in the same commit** takes section 10 red with
   `ADDED-WITHOUT-A-ROW` / `ROW-WITHOUT-A-FILE`. Real, and it is the intended behaviour.
2. **ARM E pins two digests** (`CAPTURE-PLAN.md`, `cap.sh`) **in both directions**, so a
   deliberate edit *and* a revert to the fork bytes both move the section. Real. The
   distinction from ARM C is real too, and driven: ARM C reads the *current* manifest, so the
   `f3b` laundered mutation satisfies it, while ARM E compares against the blob at `12a7f8d9`,
   which no working-tree edit reaches. **ARM E is not a restatement of ARM C.**

**Is either live today? No.** I swept every unmerged `softhouse/*` branch for adds/removes
under `tierA-a2/{out,req}` and for touches to `MANIFEST.sha256`, `CAPTURE-PLAN.md` or `cap.sh`.
The only hits are `softhouse/rescued-agent-a4bdc82a96c0a241c-20260823-140001` and
`…-ac1fa12c69146149b-…`, which fork before the corpus existed and therefore show all 1035 as
"removed" against their merge base — an artefact of the three-dot diff, not an edit. **No live
branch touches the corpus**, and `main` has not touched `tierA-a2` since the merge base
(`git diff --name-only 1eacb63e main -- .softhouse/capture/tierA-a2/` = 0 paths).

**Where a merger will see them: the handoff, §7 items 3 and 4 — and nowhere else.** There is no
marker in `tierA-a2/` itself. Both hazards are conditional on a *future* commit, so this is not
blocking, but a `MANIFEST-IS-GRADED.md` beside the manifest would put the obligation where the
worker who breaks it is actually looking. **Recommendation, not a condition.**

---

## 9. IS MERGING T393 INTO TODAY'S `main` SAFE? YES — TESTED BY MERGING (P-24)

`main` **moved during this review**, from `683c8aff` to `e864dd3d` (T421 + T428 merged). Both
states were checked; the answer did not change.

* Merge base `1eacb63e`, unmoved. `main` has changed **535** paths since; T393 has changed 43.
  **The intersection is EMPTY** — no file is touched by both.
* Scratch merge of `66ab2af9` into `e864dd3d`, performed in a clone **in `/tmp`, outside the
  repository** (a nested checkout would make `guard_no_narrow_catch_in_capture_rigs` — which
  walks recursively rather than via `git ls-files` — exit the bar 2 through a HARD guard):
  **exit 0, no conflicts, `git status --porcelain` empty.**

### The bar, read in the P-84 order — PRESENCE of the probe line tested BEFORE its value

Both runs are from a clone in `/tmp`, `git status --porcelain` **empty** before each, invoked
as `bash .softhouse/conformance.sh` — never `sh`. Full transcripts committed here as
`out/T423-BAR-on-T393-tree.txt` and `out/T423-BAR-on-merge-result.txt`.

| | T393's tree `66ab2af9` alone | **merge result** `e864dd3d` + `66ab2af9` |
|---|---|---|
| `BAR_EXIT` | **0** | **0** |
| `grep -c 'probe = '` — **printed at all?** | **1 — PRESENT** | **1 — PRESENT** |
| probe value | `up` | `up` |
| VERDICT | `PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared` | same |
| parity vectors | PASS **46**, FAIL 0, inadmissible **0** | PASS **46**, FAIL 0, inadmissible **0** |
| cells compared | **7884** graded, 93 ungraded | **7884** graded, 93 ungraded |
| ledger parity / oracle-refusal / money cells | **7 == pinned 7** / **6 == pinned 6** / **39 == pinned 39** | **10 == pinned 10** / **6 == pinned 6** / **63 == pinned 63** |
| wrong ledger implementations dead | **14 == pinned 14** | **16 == pinned 16** |
| fail-open frontier / host-state census | **11 == pinned** / **18 == pinned** | **11 == pinned** / **18 == pinned** |
| dead-path frontier | **GREEN**, `deadOccurrences=108` | **GREEN**, `deadOccurrences=108`, T323 list empty |
| guard cost | 15 guards timed, 87s wall, 0 breaches | 15 guards timed, 70s wall, 0 breaches |

The T393-tree column reproduces T393's handoff §5 exactly (46 / 7884, ledger 7/6/39, frontier
11, host-state 18, `deadOccurrences 108`). **Every difference between the two columns is a
figure `main` moved on its own** — ledger parity 7 → 10, money cells 39 → 63, wrong
implementations 14 → 16 — and each of those is `== pinned` in the column it appears in, which
is the point: the pins moved *with* `main`, and T393 moves none of them.

**Re-baselined by running, as instructed.** T423's brief pins *ledger parity 10, money cells 63,
**15** wrong impls dead*. Today's `main` reads **16** — T421 added the sixteenth
(`ef4ae067 T421: F-T406-6 — the 16th wrong implementation, and the pin, in ONE commit`) and
merged while this review was running. **That move is `main`'s, not T393's**, by the same
measurement T393 used for the earlier move: T393's diff touches no `.go` file, no `nexus/`
path, no `.softhouse/vectors/` path and nothing with `ledger` in its name (`grep -c` = 0).

---

## 10. THE `f4c` DRIVE — MOVE THE CONSTANT IN ALL THREE FILES. **F-4 HOLDS ON THE PINS ALONE.**

`instruments/50-t423-fork-tie-defeat.sh`. Same committed mutation of
`out/A2-000-glaccounts-preexisting.http` as `f4b`, but the constant is moved in **all three**
tracked files — `verify-capture-integrity.py`, `prove-a2-7-additive.py`,
`verify-manifest-independently.py` — each substitution asserted before and after, so a
spelling that failed to match could not be mistaken for an attack that was repelled.

| ref | section 10 | run-all rc | verdict | section 4 named it | ARM A pop | **tie refusals** | **pin refusals** |
|---|---|---|---|---|---|---|---|
| BEFORE `4eeed2b3` | 0 | 0 | **PASS** | **0** | 1035 | 0 | 0 |
| AFTER `fc51790d` | **2** | 1 | **FAIL** | 0 | 1035 | **0** | **2** |

**Read the two right-hand columns.** At the post-fix bytes the cross-check is fully satisfied —
**zero** tie refusals — and section 10 refuses anyway, on `ARM A's population is 1035
observations, and it is PINNED at 403` (line 744) and `ARM E's population is 104 entries, and
it is PINNED at 27` (line 827). Section 10 is the **only** section that moves: `10  0  2  ***
MOVED ***` (line 895), every other section `as adjudicated`.

**And the BEFORE row is worse than `f4b`'s.** Moving the constant in all three files also moves
**section 4's own** baseline, so `sec4-named` drops from 1 to **0**: at the pre-fix bytes the
coordinated move is *completely silent* — every section reports `as adjudicated`, `RUN-ALL
VERDICT: PASS`, and **nothing in the rig names the mutated observation at all**. T362's F-1 with
the last witness removed.

**So the F-4 repair is not "three files instead of one".** The population pins are independent
of the ties and sufficient on their own, and the ties are the cheap outer layer. That is the
question `f4b` could not answer, because it fires both halves at once. **F-4 is closed, with a
tripwire to spare.** [VERIFIED: `out/T423-F4C-DRIVE.txt` exit 0,
`out/T423-case-f4c-all-three-{BEFORE,AFTER}.txt`.]

---

## 11. WHAT I CHECKED AND FOUND CLEAN, SO SILENCE IS NOT SILENCE

* **Money non-negotiable.** No `float(`, no `%f`, no `round(`, no decimal literal in any file
  T393 changed; the only numbers are `len()` counts and sha256 hex digests, and **no monetary
  value is computed, parsed or asserted anywhere on the branch**, so `MathContext(19, HALF_UP)`
  is not engaged. Re-grepped, not accepted. Likewise no MySQL / MariaDB / `ojdbc` /
  `oracle.jdbc` / 1521; no Stripe / Plaid / Lithic / Persona; no `first_name` / `last_name`; no
  insured / protected / guaranteed; no hard-coded UTC offset.
* **Scope.** No change to `.softhouse/conformance.sh`, `.softhouse/vectors/`,
  `.softhouse/guards/*`, any DEC-n, the frozen adapter contract, or `fire-program.sh`.
* **`P-<n>` tokens.** T393 cites P-22, P-24, P-25, P-40, P-45, P-46, P-84, P-89. **All eight
  are defined in `patterns.md`** (lines 473, 528, 550, 1463, 1503, 1508, 2813, 2935). No bare
  undefined token. Its reading of P-24 as *"a literal immutable sha, never `git merge-base`"* is
  supported by P-24's own rule text at `patterns.md:546-548`.
* **Host state.** No tracked byte T393 added assigns a literal `/tmp` path to a name; the
  drives take source, scratch, output and both commit-ishes as required parameters. The bar's
  host-state census is 18 == pinned on the merge result, so the six files T393 added contribute
  zero rows. Same discipline in every instrument this review adds.
* **The evidence was not touched.** Every mutation in this review was applied in a scratch
  clone under `/tmp`. `git status --porcelain` on `/tmp/t423rr/merge` and `/tmp/t423rr/t393tree`
  is empty; no captured observation in any tracked tree was modified.
* **ARM E vs ARM C.** Distinct, and the distinction is driven, not asserted (§8.2).
* **`MANIFEST.sha256` self-reference, empty-manifest, missing-manifest, symlinked-directory.**
  All four probed; no gap (§4.3, §4.4).

---

## 12. CONDITIONS, RATED, EACH WITH A DRIVE

| id | severity | condition | drive |
|---|---|---|---|
| **C-1** | **MAJOR** | The two shipped sentences claiming no committed baseline older than HEAD exists for the 632 post-fork observations are **false**. Replace them with the measurement, and file ARM F (or fold into `T425`) — do not let the next worker build an artefact the repository already contains. | `61-t423-armf-red-drive.sh` → exit 0 requires section 10 **PASS** and ARM F **FAIL-by-name** on the same laundered repository; once section 10 carries the arm, the drive requires section 10 itself to go red there. |
| **C-2** | MINOR | The `DOES NOT COVER` block does not name the **77** post-fork non-observation tracked files that no arm reads — including one of the two `FORK_TIES` anchors. Name them; closing them is `T425`'s design call. | `40-t423-ungraded-census.py` (census) + `30-t423-extra-drives.sh` DRIVE 1 (`cap8.sh` → section 10 = 0, run-all PASS, section 4 silent). |
| **C-3** | MINOR | ARM B's missing `try/except` is correctly **not** fixed on this branch, but is filed nowhere executable — P-89, which T393 invoked for the wiring and not for this. File it. | `30-t423-extra-drives.sh` DRIVE 2 (PATH shim): require a named failure and a `VERDICT:` block instead of a traceback, and ARM C/D/E headers reached. |
| **C-4** | LOW | The handoff's `42 paths` is `43` at the branch tip (`out/08-CONFORMANCE-FINAL.txt`). The load-bearing zero-match result is unaffected. | `git diff --name-only 1eacb63e 66ab2af9 \| grep -cE '\.go$\|^nexus/\|^\.softhouse/vectors/\|ledger'` → 0. |

**None blocks the merge.** T393 may merge; C-1 should be attached to `T425` before that task is
dispatched, because `T425` is the task C-1 would otherwise mislead.
