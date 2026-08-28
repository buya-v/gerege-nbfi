# T393 — T382's four conditions on T374, closed

**Branch:** `softhouse/T393-t382-conditions`.
**Target of the conditions:** `.softhouse/reviews/A2-11/verify-capture-integrity.py` (section 10)
and `.softhouse/reviews/A2-11/run-all.sh`, both merged at `01a7a05a`.
**Source review:** `.softhouse/reviews/t382-review-t374/REVIEW.md` (531 lines), read from `main`.

## VERDICT

All four conditions are closed inside the branch's own files. **F-4 first**, because it was the
one that reinstated the defect: section 10's baseline constant was an unchecked literal, and
T382's one-line move of it reproduced T362's F-1 end to end on the branch that fixes F-1.

**No new evidence artefact was built.** T382's FINDING 2 is correct and I re-verified every
count it rests on before relying on any of them.

---

## 0. I RE-VERIFIED T382's COUNTS FIRST. ALL OF THEM REPRODUCE.

The brief said to verify T382's manifest counts myself rather than build on them. Independent
enumeration, my own selector, `git ls-tree` at the literal fork sha and at HEAD, my own
manifest parser, digests recomputed from disk:

| what | T382 | T393 measured |
|---|---|---|
| observations tracked at the fork sha (ARM A population) | 403 | **403** |
| observations tracked at HEAD (ARM B population) | 1035 | **1035** |
| post-fork observations, invisible to ARM A | 632 | **632** |
| `MANIFEST.sha256` total rows | 1139 | **1139** |
| of which under `out/` or `req/` | 1035 | **1035** |
| tracked observations with NO manifest row | 0 | **0** |
| manifest rows naming NO tracked observation | 0 | **0** |
| manifest digest vs disk: agree / disagree / unreadable | 1035 / 0 / 0 | **1035 / 0 / 0** |
| post-fork observations covered by a manifest row | 632 of 632 | **632 of 632** |
| entries in the fork-sha manifest | 430 | **430** |
| of those under `out/` or `req/` | 403 | **403** |
| NOT under `out/` or `req/` (section 4's saturated set) | 27 | **27** |
| of the 27, byte-identical to the fork sha today | 25 | **25** |
| the differing set | `{CAPTURE-PLAN.md, cap.sh}` | **exactly those two** |

[VERIFIED: `.softhouse/capture/t393-t382-conditions/instruments/00-verify-t382-counts.py`,
transcript `out/00-t382-counts.txt`, **exit 0**, `FAILURES: 0`. It exits 1 if any number
disagrees, so a disagreement could not have been read as a pass.]

One measurement T382 did not report, which decided how far ARM C could reach
[`instruments/01-manifest-nonobs-shape.py`, `out/01-shape.txt`]: the manifest's **104 rows
outside `out/` and `req/` also all agree with disk**, and 1139 rows cover every tracked file
under the capture directory except `MANIFEST.sha256` itself (1140 − 1). The disk walk under
`out/` + `req/` found 1035 files, 0 untracked, 0 symlinks.

---

## 1. F-4 — THE CONSTANT THAT REINSTATED THE DEFECT. CLOSED TWO WAYS.

**What was wrong.** Section 4 ties its copy of the fork sha to another tracked file
(`check("prove-a2-7-additive.py hard-codes the literal sha", 'BASELINE = "%s"' % FORK in src)`).
Section 10 carried the same literal tied to **nothing**, and asserted nothing about ARM A's
population size. Move the constant forward one line to a commit that contains a mutation and
ARM A's population collapses 403 → 1035 onto ARM B's, the two arms stop being independent, and
the mutation ARM A caught a moment earlier is invisible — while section 4 prints
`DIFF out/A2-000-glaccounts-preexisting.http` **by name** and `run-all.sh` exits 0 printing
`RUN-ALL VERDICT: PASS`.

**The repair, in the spelling section 4 already uses.**

* `FORK_TIES` — the literal must appear in **two** tracked files, as `BASELINE = "<sha>"` in
  `.softhouse/capture/tierA-a2/prove-a2-7-additive.py` and as `FORK = "<sha>"` in
  `.softhouse/reviews/A2-11/verify-manifest-independently.py`. The needles are built from
  `FORK` at runtime, so moving `FORK` in this file alone breaks both ties and **REFUSES**.
* `FORK_OBS_PIN = 403` — ARM A's population cardinality. This is deliberately **not** the kind
  of pin section 4 has: 403 is a property of an **immutable commit**, so it cannot drift with
  the rig the way section 4's 571-vs-1139 manifest counts do. If it is not 403, either the
  constant moved or the selector stopped selecting, and both are instrument failures.
  `FORK_NONOBS_PIN = 27` is the same argument for ARM E's population.

Both are REFUSALS (exit 2), not failures: a calibration that cannot be confirmed has not
measured anything, and section 10 is adjudicated 0, so a refusal moves it and fails the
aggregate.

**Driven** — `f4b-move-fork-constant`, the mutation applied mechanically by
`13-move-fork-constant.py`, which REFUSES unless it matches exactly one
`FORK = "<40 hex>"` line (a "one-line move" is only one line if there is one line):

| case | ref | section 10 | run-all rc | run-all verdict | section 4 printed `DIFF out/A2-000-…` by name |
|---|---|---|---|---|---|
| `f4a-control-commit-mutate-forkobs` | BEFORE | 1 | 1 | FAIL | **1** |
| `f4a-control-commit-mutate-forkobs` | AFTER | 1 | 1 | FAIL | **1** |
| **`f4b-move-fork-constant`** | **BEFORE** | **0** | **0** | **PASS** | **1** |
| **`f4b-move-fork-constant`** | **AFTER** | **2** | **1** | **FAIL** | **1** |

**The `f4b` BEFORE row is T362's F-1 verbatim, reproduced on the branch that fixes F-1** — one
transcript containing all four of:

```
        DIFF out/A2-000-glaccounts-preexisting.http          <- section 4, BY NAME
      at the fork sha : 1035 observations  {'out': 906, 'req': 129}   <- ARM A collapsed
      at HEAD         : 1035 observations  {'out': 906, 'req': 129}
  10        0              0         as adjudicated
  RUN-ALL VERDICT: PASS
```
[VERIFIED: `out/drive/case-f4b-move-fork-constant-BEFORE.txt:288,693,694,746,749`.]

At AFTER the same mutation trips **four independent tripwires**, not one:

```
  REFUSED  .../prove-a2-7-additive.py does NOT carry `BASELINE = "2d132fb0…"`.
  REFUSED  .../verify-manifest-independently.py does NOT carry `FORK = "2d132fb0…"`.
  REFUSED  ARM A's population is 1035 observations, and it is PINNED at 403.
  REFUSED  ARM E's population is 104 entries, and it is PINNED at 27.
  VERDICT: REFUSED (exit 2). The instrument could not measure. This is NOT a pass,
  10        0              2         *** MOVED ***
  RUN-ALL VERDICT: FAIL — 1 section(s) moved off the adjudicated verdict.
```
[VERIFIED: `out/drive/case-f4b-move-fork-constant-AFTER.txt:875,876,877,883,900,903`.]

The `f4a` control is the row that keeps the `f4b` row honest: it is the **same committed
mutation without the constant move**, and ARM A catches it at **both** refs. So `f4b`'s BEFORE
`PASS` is caused by the constant move and by nothing else.

---

## 2. F-1 — THE FIVE UNCOVERED CASES. ALL FIVE CLOSED, EACH DRIVEN.

T374 disclosed **one** uncovered case (committed *mutation* of a post-fork observation).
T382 measured **four more** outside both arms and outside the disclosure. Root cause, and it is
T382's, restated because the repair follows from it: T374's own F-2 repair is the rule *"an
empty population is a SELECTOR failure, not a clean tree"* — and section 10 applied that rule
**at zero and stopped**. It never pinned the population's cardinality, so a shrink of up to 632
(both directories still non-empty, so the refusal never fires) or any growth passed.

**Two new arms close all five.** Neither needed a new artefact.

* **ARM C — the tracked `MANIFEST.sha256`, as a PATH-SET and as recomputed digests.** ARMs A
  and B compare files they were *handed* by a git listing; neither can see a file that was
  never handed to them, which is exactly why a committed deletion took the population
  1035 → 1034 and still said PASS. ARM C asserts `set(manifest out/req rows) == set(tracked
  observations)` in both directions and recomputes every digest from disk.
* **ARM D — the DISK, walked, with `lstat`.** ARMs A, B and C all start from a git or manifest
  listing, so an untracked fabricated observation is invisible to all three. And
  `open(path,"rb")` **follows symlinks**, so a regular file replaced by a symlink to identical
  bytes reported PASS. This arm starts from the disk and does not follow.

| T382 case | attack | BEFORE `4eeed2b3` | AFTER `fc51790d` | which arm catches it | closed against a laundered manifest? |
|---|---|---|---|---|---|
| 13 | committed **mutation** of a post-fork observation | **0 / run-all 0 / PASS** | **1 / run-all 1 / FAIL** | ARM C digest | no — see the residual |
| 14 | committed **DELETION** of a post-fork observation | **0 / 0 / PASS** | **1 / 1 / FAIL** | ARM C `ROW-WITHOUT-A-FILE` | no |
| 15 | committed **ADDITION** of a fabricated observation | **0 / 0 / PASS** | **1 / 1 / FAIL** | ARM C `ADDED-WITHOUT-A-ROW` | no |
| 16 | **UNTRACKED** fabricated observation in `out/` | **0 / 0 / PASS** | **1 / 1 / FAIL** | ARM D `UNTRACKED` | **yes, outright** |
| 09 | **SYMLINK** whose target has identical bytes | **0 / 0 / PASS** | **1 / 1 / FAIL** | ARM D `SYMLINK` | **yes, outright** |
| — | control, unmutated | 0 / 0 / PASS | 0 / 0 / PASS | — | — |

[VERIFIED: `out/drive/MATRIX.tsv`, per-case transcripts `out/drive/case-*.txt`, driver
transcript `out/DRIVE.txt` — **22 rows, `unexpected results: 0`, `DRIVE VERDICT: PASS`,
exit 0**. Each case prints its failure BY NAME; e.g. case 13 at AFTER prints
`MANIFEST MISMATCH out/A2-200-glaccounts-live-precheck.http` and
`RUN-ALL VERDICT: FAIL — 1 section(s) moved off the adjudicated verdict`.]

Cases 16 and 09 are closed **outright**: a fabricated file with a manifest row added for it
breaks the set equality instead, and a symlink is never a regular file whatever its target
says. Cases 13, 14 and 15 are closed against the un-laundered attack and *raised* against the
laundered one, which is the residual below.

### The residual, named exactly, and DRIVEN so the boundary statement is a measurement

**A committed change to a post-fork observation that ALSO rewrites its `MANIFEST.sha256` row in
the same commit is still undetected**, at both refs. ARM A has no fork blob for it, ARM B's
baseline *is* the mutated commit, ARM C sees a manifest that agrees, ARM D sees a tracked
regular file. Closing it needs a committed baseline **older than HEAD** for those 632
observations; none exists and none can be manufactured here.

What T393 changes is the **cost**: it was one file edit, it is now one file edit plus a matching
manifest row, both visible in one diff. The `f1-13b-postfork-laundered-RESIDUAL` row above is
that residual driven — expected **undetected at both refs**, and it is. A boundary statement
whose failing case was never run is a hope; this one is a measurement.

Two further boundaries, unchanged and restated: a mutation committed to the **fork sha itself**
is not reachable without rewriting `main`'s history; and the 403 fork-sha observations are
**fully covered against laundering** by ARM A, which recomputes from the git blob and never
reads a recorded digest (T382 matrix case 17).

---

## 3. F-3 — THE SATURATION CLASS, CLOSED AT ITS SECOND AND LAST LIVE SITE.

T382 audited every section's return-code arithmetic and found exactly one live saturated site
left: **section 4, over the 27 fork-sha manifest entries outside `out/` and `req/`** — `cap.sh`,
`env.sh`, `manifest.py`, `mkreq.py`…`mkreq6.py`, `rename1.py`, `show.py`, the five `run-*.sh`,
`sql/q1..q3`, the three `prove-*.py`, `CAPTURE-PLAN.md`, `DEFECTS-FOUND-BY-REVIEW.md`,
`FLAGGED-NOT-REPRODUCIBLE.txt`, `RED-GREEN-D2`, `RED-GREEN-D3`. These are the scripts that
**produced** the observations and the red/green evidence that grades them.

**ARM E** asks the same question where GREEN is the adjudicated value. It compares each of the
27 against its **immutable fork-sha blob**, so it also catches the laundered variant that ARM C
cannot: rewriting the current manifest does not change the blob at `12a7f8d9`.

The two known differences are adjudicated **by name AND by digest**, in both directions — the
fork digest must still be the fork digest and the disk digest must still be the disk digest — so
a *further* mutation of `CAPTURE-PLAN.md` or `cap.sh` moves the section, **and so does a revert
to the fork bytes**. That second half follows section 9's precedent for section 1's three
permanent failures: a vanished adjudicated red is a move too. The re-adjudication procedure and
the command that prints the new digests are written at the constant.

| case | attack | BEFORE `4eeed2b3` | AFTER `fc51790d` |
|---|---|---|---|
| `f3-commit-mutate-nonobs` | committed mutation of `manifest.py` — T382's own target, the script that WRITES the manifest | **0 / run-all 0 / PASS** | **1 / run-all 1 / FAIL** |
| `f3b-commit-mutate-nonobs-laundered` | the same, **with its `MANIFEST.sha256` row rewritten to match** | **0 / 0 / PASS** | **1 / 1 / FAIL** |

The `f3b` row is the reason ARM E is not a restatement of ARM C: ARM C reads the current
manifest and a laundered row satisfies it, while ARM E compares against the **blob at
`12a7f8d9`**, which no edit in the working tree can reach.

`run-all.sh`'s section 4 banner now states this in place of implying the split closed the
problem, and the docstring's DOES-NOT-COVER block was rewritten to name the measured set rather
than the one disclosed case.

---

## 4. THE `run-all.sh` WIRING QUESTION — SAFE? CHEAP? (RECOMMENDATION ONLY; NOT DONE)

**Confirmed on this branch:** `grep -c 'run-all.sh' .softhouse/conformance.sh` = **0**, and no
`A2-11` path appears in `conformance.sh` at all. Every section hardened here runs only when a
human runs the review rig by hand. That is **P-45**, it is **pre-existing and not T374's
doing**, and per the brief it is the **fifth** instance logged in this fire beside
`oracle-state-baseline.sh` (T390), `guard-probe-expiry.sh` (T311), T303 and T313.
`conformance.sh` is held by T404 this wave, so nothing was changed.

**Recommendation: WIRE `verify-capture-integrity.py` — NOT `run-all.sh` — and file it as a
task, not a sentence.**

*Safe to wire section 10 alone:*
* It writes **nothing**. No tracked file, no scratch file, no network.
* Its exit codes are already the shape the bar wants: 0 / 1 / 2 with **2 = REFUSED, never a
  pass**, and every failure named rather than counted.
* It carries **no fail-open**. I ran T238's linter on this tree: frontier **11 == pinned 11**,
  and **no `.softhouse/reviews/A2-11/` file and no T393 file is on it**
  [`out/04-failopen-lint.txt`]. T261's precondition — *an orphan may not acquire a caller until
  the fail-opens in it are repaired* — is therefore already met for this file.
* It is GREEN on a clean tree today, and its RED half is driven eleven ways above.

*NOT safe to wire `run-all.sh` as it stands, for a reason `conformance.sh` itself already
enforces elsewhere:* **`run-all.sh` rewrites a TRACKED file on every run** —
`.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt`, via `tee`, at minimum its
`generated <timestamp>` line. `guard_no_fail_open_instruments` deliberately diverts T238's
linter JSON to scratch with the comment *"a harness that rewrote a tracked file on every graded
run would dirty the tree it is grading"*. Wiring `run-all.sh` unchanged imports exactly that
defect into the bar. It is a small fix — a transcript-destination parameter defaulting to the
tracked path so hand runs are unchanged — but it is a change to another worker's file and it
must be **done before** the wiring, not with it.

*Cheap?* **Section 10 alone: yes, at a cost worth naming. `run-all.sh` entire: no.**

Measured on this host at load average **6.08** on 10 cores, on the clean tree:

```
bash .softhouse/reviews/A2-11/run-all.sh          51.76s user 49.23s system   1:51.32 total
python3 .../verify-capture-integrity.py           28.71s user 29.06s system   1:05.11 total
```

For scale, the bar's own guard-cost census on the same run reads **`15 guards timed, 70s total
wall, ceiling breaches 0, unbudgeted guards 0`**, with the most expensive single guard at 20s
against a 300s ceiling. **Wiring section 10 as it stands would roughly double the guards' total
wall time in one step**, and wiring `run-all.sh` would nearly treble it. That is the honest
number, and it is why the `git cat-file --batch` conversion belongs in the same task rather
than after it.

Section 10 spawns roughly 1465 `git show` subprocesses (403 + 1035 + 27). If it is wired into
the graded bar, that should become one `git cat-file --batch` stream in the same task — this is
a mechanical change with an obvious red drive (the arm must still catch each of the eleven
mutations above), and it is the difference between a bar that grows a minute and one that grows
a few seconds. **Do not do it as a drive-by**: the comparator is the thing under test.

*Filing, per P-89.* An unwired guard may merge, but **only against a filed, dispatchable task
with an owner, a dependency edge and a red-drive requirement** — "prose does not fire on the
next fire". Suggested task: *wire `verify-capture-integrity.py` into `conformance.sh` as a HARD
guard, after converting its arms to `git cat-file --batch`; owner = whoever holds
`conformance.sh`; depends on T393; red drive = re-run `10-drive-conditions.sh` with the
conformance guard in place and require the bar to go red on each of the eleven cases.* A second,
later task can wire `run-all.sh` once its transcript destination is a parameter.

---

## 5. THE BAR, ON A CLEAN TREE, AFTER `git add -A` AND COMMIT

`git status --porcelain` **empty** before the run. Never `sh` — `bash .softhouse/conformance.sh`.
**Read in the P-84 order, not the tempting one:** the probe line was tested for **PRESENCE**
first — `grep -c 'probe = '` returns **1**, so the line was printed — and only then for its
value.

```
BAR_EXIT=0
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
    parity vectors          PASS 46   FAIL 0        inadmissible 0
    cells compared          7884 graded, 93 ungraded
  exemption census READ: LEDGER parity vectors        = 7 == pinned 7
  exemption census READ: LEDGER oracle-refusal vector = 6 == pinned 6
  exemption census READ: LEDGER money cells compared  = 39 == pinned 39
    ledger inadmissible     0        ledger cells compared 144 graded, 39 MONEY cells
  all 14 wrong ledger implementations DIED through this harness, not by hand.
  CENSUS fail-open instruments — frontier 11, pinned at 11; frontier == pinned (all 11 rows, by path)
  CENSUS host state — sites that assign a literal /tmp path to a name: 18, pinned at 18; census == pinned
  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
  T316-DEADPATH-CENSUS: corpus=1401 deadFiles=75 deadOccurrences=108 resolving=1324 …
  GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0
  namespace: PASS — every task-id prefix shared by two directories carries its OWNER record.
```
[Transcripts: `out/07-CONFORMANCE.txt` and `out/08-CONFORMANCE-FINAL.txt`. **The bar was run
TWICE, and both are committed** — 07 after the code and the drive were committed, 08 after the
handoff was finished, so the graded tree in run 08 is the final tree with nothing outstanding
but the transcript run 08 itself writes. Both are EXIT 0 with the probe line present and every
pin equal; run 08 is the one to read. Recording both rather than only the later one, because
"the bar was green" and "the bar was green on the bytes you are about to merge" are different
claims and only the second one is worth anything.]

**Baseline held.** 46 parity / 7884 cells — unmoved. Fail-open 11 == 11, host-state 18 == 18,
dead-path frontier **GREEN at `deadOccurrences 108`** — exactly the pinned baseline, so the six
new tracked `.py`/`.sh` files I added contribute **zero** dead-path rows and zero fail-open
rows.

**TWO BASELINE FIGURES IN THE BRIEF HAVE MOVED, AND NEITHER MOVE IS MINE — STATED RATHER THAN
LEFT TO BE FOUND.** The brief pins `ledger 7/6/0/142/39` and T382's merge note says *13* wrong
ledger implementations. This run reads **144 ledger cells** and **14 wrong implementations**
(`pinned at 14`, and every `== pinned` comparison in the exemption census agrees, which is why
the bar is green). Both moved on `main` **before my fork point** — my base is `1eacb63e`,
which already carries the `T360-divergence-class + T387` merge that adds the divergence class
and its implementation. **Proof that it cannot be mine, by measurement rather than assertion:**
`git diff 1eacb63e --name-only` is 42 paths, and
`git diff 1eacb63e --name-only | grep -cE '\.go$|^nexus/|^\.softhouse/vectors/|ledger'` = **0**.
This branch touches no Go file, no vector, and nothing with `ledger` in its path. The `7 / 6 /
0 / 39` quarters of the baseline are all **unmoved and pinned**.

---

## 6. WHAT I CHANGED

| file | change |
|---|---|
| `.softhouse/reviews/A2-11/verify-capture-integrity.py` | two arms → five; `FORK` cross-checked against two tracked files; ARM A and ARM E populations pinned; manifest arm; disk walk; the 27 adjudicated; positive controls extended to all five arms; the DOES-NOT-COVER block rewritten to the measured set with the residual named |
| `.softhouse/reviews/A2-11/run-all.sh` | section 4 banner: the saturation is lifted for the 27 too, and what section 4 still uniquely carries is the drift measurement. section 10 banner: the five arms, the pin, the cross-check, and the residual |
| `.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt` | regenerated by `bash run-all.sh` (this file is rewritten by every run; that is disclosed at the site by T374's F-5 block) |
| `.softhouse/capture/t393-t382-conditions/**` | the instruments and every transcript cited above |

**Non-negotiables scanned across the whole diff.** No `float(`, no decimal literal, no
`round(`, no `%f` — the only numbers in this branch are `len()` counts and sha256 hex digests,
and **no monetary value is computed anywhere in it**, so `MathContext(19, HALF_UP)`
admissibility is not at stake. No MySQL / MariaDB / `ojdbc` / `oracle.jdbc` / port 1521. No
Stripe / Plaid / Lithic / Persona. No `first_name` / `last_name`. No insured / protected /
guaranteed string. No hard-coded UTC offset. No change to `.softhouse/vectors/`, to any DEC-n,
to the frozen adapter contract, to `.softhouse/conformance.sh`, to `.softhouse/guards/*`, or to
`.softhouse/bin/fire-program.sh`.

**Host-state and dead-path discipline.** No tracked byte of mine assigns a literal `/tmp` path
to a name — the drive takes the source repo, the scratch root, the output directory and **both**
commit-ishes as required parameters (`${T393_SRC:?}` …), and aborts rather than defaulting to
somebody's disk. Every `.softhouse/`-containing string literal I added names a tracked path or
carries a placeholder; the paths built from `$SRC` are `INDETERMINATE` to T316's census by
construction.

---

## 7. OPEN, AND WHO OWNS IT

1. **P-45 / the wiring.** Section 4 above. Not done — `conformance.sh` is T404's this wave.
   Needs filing as a task with an owner, not a paragraph.
2. **The disclosed residual** — a committed change to a post-fork observation with its manifest
   row rewritten in the same commit. Not closable from inside this rig.

   **T374's follow-up #1 is half right, and the half that is wrong is the half that matters.**
   It asks for *"a tracked `OBSERVATIONS.sha256` under `capture/tierA-a2`, regenerated only by
   an explicit capture task"* and calls it a **new evidence artefact**. T382 is right that the
   *digest list* already exists — `MANIFEST.sha256`, and I re-verified its coverage above, so
   the arm was cheap and should have been added rather than deferred. But the clause
   **"regenerated only by an explicit capture task"** describes a property `MANIFEST.sha256`
   does **not** have: `manifest.py` rewrites it, and `manifest.py` sits in the same directory
   as the observations it hashes. That clause is exactly what would close the residual, and it
   is genuinely new work — a baseline the capture scripts cannot rewrite. So the follow-up
   should not simply be struck: it should be **narrowed** to that clause, with the digest-list
   half marked done by ARM C.
3. **MERGE HAZARD — ARM C's set equality is now load-bearing on `MANIFEST.sha256`.** Any worker
   who adds or removes a file under `.softhouse/capture/tierA-a2/{out,req}/` must re-run
   `manifest.py` in the same commit, or section 10 goes red with `ADDED-WITHOUT-A-ROW` /
   `ROW-WITHOUT-A-FILE`. That is the intended behaviour — it is precisely T382's cases 14 and 15
   — but it is a new obligation on that directory and it should be in the merge notes.
4. **MERGE HAZARD — ARM E pins two digests.** A deliberate edit to
   `.softhouse/capture/tierA-a2/CAPTURE-PLAN.md` or `cap.sh` requires re-adjudicating
   `ADJUDICATED_DIFFERENT`. The procedure and the command are written at the constant.
5. **`prove-t374-fixes-can-fail.sh` re-run.** T374's own prover drives four cases against this
   file. I re-ran it after the rewrite; result in section 5 above.
6. **ARM B's `git show` still has no `try/except`, and that costs more now than when T382
   raised it.** T382 recorded this and classified it correctly as *fail-closed, not a defect*:
   a git failure raises, Python exits 1, and 1 is also the genuine-mutation code, so the
   aggregate still goes red. **With five arms that is now a bigger hole than with two**: an
   uncaught exception in ARM B means ARMs C, D and E never run and no verdict block is printed
   at all, so the operator sees a traceback instead of a named failure and cannot tell which
   population was actually compared. The repair is three lines — the same `except
   subprocess.CalledProcessError` ARM A and ARM E already carry, recording a named
   `b_unreadable` list. **Deliberately NOT done in this branch**, and the reason is not
   scope: changing the graded file after the drive ran would mean the committed matrix and the
   committed instrument were produced by different bytes, which is the exact disclosure T382
   had to make about its own attack matrix. It should be one small task with a red drive
   (make `git show HEAD:<path>` fail and require a named failure plus a verdict block, not a
   traceback), and the drive here re-run against it.
