# T382 — independent review of T374 (`softhouse/T374-t362-conditions` @ `f4157d42`)

**Reviewer:** T382, branch `softhouse/T382-review-t374`.
**Target:** `softhouse/T374-t362-conditions` @ `f4157d42`, read **from the branch**
(`git show <branch>:<path>`, `git diff main...<branch>` — three dots), never from disk.
**Scope of the target:** T374 applies T362's F-1..F-6 to T357's A2-11 work, and absorbs a
dead-path frontier pin move 109 → 108.

## VERDICT: **APPROVED WITH CONDITIONS**

The work is sound, driven RED before repair, and every claim I re-derived reproduced. The
F-1 fix is real and I could not defeat it by any *accidental* corruption of the corpus. The
conditions are all about **the size of the disclosed gap**, which the coordinator asked me to
size independently: it is **larger than T374 states**, and the artefact T374 says is needed to
close it **already exists in the repository**.

Nothing here is a money-math defect. Nothing here violates a non-negotiable. Nothing here is
a regression against `main`. All four conditions are closable inside this branch's own files.

---

## What I ran (every finding below has a driven reproduction with a control)

All work in throwaway clones under `/tmp`; **no live worker's tree was touched**, and I wrote
nothing outside `.softhouse/reviews/t382-review-t374/` plus the handoff file
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T382.md` the brief authorises.

**My own frontier discipline.** Staging these instruments first moved the dead-path census
109 → 114: five literals naming scratch-clone decoys and `verify-capture-integrity.py`, which
lives only on T374's branch and is therefore genuinely a dead path on a main-based branch.
I did **not** touch `.softhouse/guards/dead-path-frontier.pin` — outside my grant, and the
wrong repair. The literals are assembled from variables instead (the truthful classification:
they are scratch-clone paths, not paths of this commit), the reason is stated at each site, and
the attack matrix was re-run afterwards. `check-dead-path-frontier.sh` on this branch:
`T316-DEADPATH-FRONTIER: GREEN rows=109 pinned=109 added=0 removed=0`.

**The bar caught ME, and I repaired rather than pinned.** The first conformance run on my
committed branch came back **EXIT 2 with NO probe line** — under **P-84** a failed HARD guard,
not an oracle outage, and I read it that way. Cause, named by the guard itself:

```
conformance: CENSUS host state in the lint corpus — 156 repo-wide search instrument(s) …
             sites that assign a literal /tmp … path to a name: 20, pinned at 18
+.softhouse/reviews/t382-review-t374/instruments/20-frontier-census.sh | O=/tmp/t382-out
+.softhouse/reviews/t382-review-t374/instruments/20-frontier-census.sh | SC=/tmp/t382-pin
conformance: EXIT 2 — no verdict is available. This is NOT a pass.
```
[VERIFIED: `out/CONFORMANCE-RED-hoststate.txt`.] Only `20-frontier-census.sh` was in the
guard's corpus (it is the only one of my nine that does a repo-wide `git grep`). Repairing
*only* the site the guard happened to look at would be the exact P-45 shape this review charges
T374 with, so **all nine** instruments were repaired identically: the scratch clone and the
output directory are now required parameters (`${T382_CLONE:?…}`, `${T382_OUT:?…}`) with no
literal path in any tracked byte. I did **not** touch `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` — that
lives in `.softhouse/conformance.sh`, which another worker holds, and pinning would have been
the wrong repair anyway. `20-frontier-census.sh` and `70-my-own-frontier.sh` were then **re-run
from the repaired bytes**, so their committed transcripts are re-derivable.

**And the bar caught a vacuous pass in one of my own instruments.** The first version of
`70-my-own-frontier.sh` guessed at the census JSON layout, found nothing, and printed
`count: 0  total rows: 0` over a census that had 114 rows. That is the defect this review
prosecutes, in my own file. It now REFUSES on an unrecognised layout or a zero-row census, and
I drove the reader RED on a planted row before trusting it (`rows contributed by this
review: 1`, rc=1) — the clean run reports `0 mine / 109 total`, `rc=0`
[VERIFIED: `out/OWN-FRONTIER.txt`].

**Disclosure about that substitution — stated, not hidden (T356/P-22 spelling).** The full
21-row matrix in `out/ATTACK-MATRIX-RUN1.txt` was produced by the **pre-substitution spelling**
of `10-attack-section10.sh`. The substitution is:

```
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
  ->  A2DIR=".softhouse/reviews/A2-11" ;  INT="$A2DIR/verify-capture-integrity.py"
"$SC/.softhouse/capture/tierA-a2/<name>"
  ->  CAPDIR=".softhouse/capture/tierA-a2" ;  "$SC/$CAPDIR/<name>"
```

— pure shell parameter expansion to the identical strings, so it is **output-neutral by
construction**. I did not leave that as an argument: the re-run reproduced rows **00–03
identically** (`0/0`, `1/1`, `1/1`, `1/1`) before I stopped it, and I stopped it because the
host load average was 15 with four other workers live and the mandatory conformance run needed
the CPU. Evidence: `out/ATTACK-MATRIX-RUN2-partial.txt`,
`out/attack-results-RUN2-partial.tsv`. **This is the one place in this review where the
committed instrument and the committed transcript were produced by different bytes**, and the
difference is named above in full. Nothing else here has that property.

| instrument | what it drives | transcript |
|---|---|---|
| `instruments/00-populations.sh` | reproduces T374's 403 / 1035 / 632 population split | `out/POPULATIONS.txt` |
| `instruments/10-attack-section10.sh` | **21-case attack matrix** against `verify-capture-integrity.py`, each with a control | `out/ATTACK-MATRIX-RUN1.txt`, `out/cases/case-*.txt` |
| `instruments/20-frontier-census.sh` | **F-2 by running** (P-83): census + T326 regenerator at main, at T374, and at the merge result | `out/FRONTIER.txt` |
| `instruments/30-saturation-audit.sh` | audits section 4's residual saturation and the untracked-file case through the whole runner | `out/SATURATION.txt` |
| `instruments/31-saturation-clean-target.sh` | the same on a target that is currently byte-identical, so the before/after is unambiguous | `out/SATURATION-CLEAN.txt` |
| `instruments/40-rerun-t374-prover.sh` | re-runs T374's own `prove-t374-fixes-can-fail.sh` on the merge result, independently | `out/PROVER-RERUN.txt` |
| `instruments/50-manifest-covers-postfork.py` | measures whether T374's follow-up #1 artefact is genuinely new | `out/MANIFEST-COVERAGE.txt` |
| `instruments/60-defeat-arm-a-baseline.sh` | tries to neuter ARM A by moving its own baseline constant | `out/DEFEAT-BASELINE.txt` |
| `instruments/70-my-own-frontier.sh` | names every dead-path row **my own review** contributes, before I commit | `out/census-mine.txt` |
| `instruments/90-collect-transcripts.sh` | copies the cited transcripts out of `/tmp` into the grant | — |

Control run, unmutated, on the T374 **merge result** (`main` + `T374`, merged clean):

```
bash .softhouse/reviews/A2-11/run-all.sh        EXIT=0
  1..10 all "as adjudicated"    sections run: 10    deviations: 0
  RUN-ALL VERDICT: PASS
section 10:  fork sha 403 {'out':327,'req':76}   HEAD 1035 {'out':906,'req':129}
             ARM A 403/403 identical   ARM B 1035/1035 identical   FAILURES: 0
```
[VERIFIED: `out/00-baseline-runall.txt`] — T374's counts reproduce **exactly**.

---

## F-1 — the evidence-integrity control. ATTACKED, 21 cases.

### It holds against every accidental-corruption shape

| # | attack (working tree) | expected | GOT |
|---|---|---|---|
| 01 | one line appended to a fork-sha observation (T362's exact shape) | 1 | **1** |
| 02 | ONE byte flipped in the MIDDLE of a fork-sha observation | 1 | **1** |
| 03 | a fork-sha observation deleted | 1 | **1** |
| 04 | a fork-sha observation replaced by an EMPTY file | 1 | **1** |
| 05 | one line appended to a POST-FORK observation | 1 | **1** |
| 06 | ONE byte flipped in the middle of a POST-FORK observation | 1 | **1** |
| 07 | a POST-FORK observation deleted | 1 | **1** |
| 08 | a POST-FORK observation emptied | 1 | **1** |
| 10 | replaced by a SYMLINK to different bytes | 1 | **1** |
| 11 | replaced by a SYMLINK to `/dev/null` | 1 | **1** |
| 12 | **COMMITTED** append to a fork-sha observation | 1 | **1** (ARM A) |
| 17 | observation mutated **AND** `MANIFEST.sha256` updated to match (laundering) | 1 | **1** (ARM A) |
| 19 | the `FORK` baseline constant swapped for a nonexistent sha | 2 REFUSED | **2** |
| 00 / 18 / 20 | controls, unmutated, before and after every mutation | 0 | **0** |

[VERIFIED: `out/ATTACK-MATRIX-RUN1.txt`, per-case transcripts
`out/cases/case-NN-*.txt`.] Case 17 is worth naming: **laundering the manifest does not help** — ARM
A recomputes from the git blob and never reads the recorded digest.

### FINDING 1 (MODERATE) — the uncovered set is LARGER than T374 discloses

T374's `Unverified` block discloses exactly one uncovered case:

> the **632** observations captured *after* the fork sha have no committed baseline older than
> HEAD, so a committed **mutation** of one of those is outside both arms.

Confirmed — and **four** more shapes are outside both arms and outside the disclosure.

| # | attack | T374 disclosure | GOT |
|---|---|---|---|
| 13 | **COMMITTED mutation** of a post-fork observation | disclosed | **0 — undetected** |
| 14 | **COMMITTED DELETION** of a post-fork observation | *not disclosed* | **0 — undetected** |
| 15 | **COMMITTED ADDITION** of a fabricated observation into `out/` | *not disclosed* | **0 — undetected** |
| 16 | a fabricated observation left **UNTRACKED** in `out/` | *not disclosed* | **0 — undetected** |
| 09 | observation replaced by a **SYMLINK to identical bytes** | *not disclosed* | **0 — undetected** |

The 14/15 pair is the sharp one, because the instrument **prints its own population moving and
still says PASS**:

```
case 14 (committed deletion):   at HEAD : 1034 observations {'out': 905, 'req': 129}
                                ARM B enumerated 1034 ... FAILURES: 0 ... VERDICT: PASS (exit 0)
case 15 (committed fabrication): at HEAD : 1036 observations {'out': 907, 'req': 129}
                                 ... FAILURES: 0 ... VERDICT: PASS (exit 0)
control:                         at HEAD : 1035 observations {'out': 906, 'req': 129}
```
[VERIFIED: `out/cases/case-14-COMMIT-delete-postforkobs.txt`, `out/cases/case-15-COMMIT-add-fabricated.txt`,
`out/cases/case-00-CONTROL-unmutated.txt`.]

**Why this matters and is not pedantry.** T374's own F-2 repair is the rule *"an empty
population is a SELECTOR failure, not a clean tree"*. Section 10 applies that rule at zero and
**stops there**. A population that silently shrank by up to **632** — every post-fork
observation, leaving only the 403 ARM A protects, with both `out/` and `req/` still non-empty
so the refusal never fires — or grew by any number of fabricated files, is the same class of
selector failure one step short of empty, and section 10 passes it.
The positive control that would have caught the shrink — `set(fork_paths) <= set(head_paths)` —
protects only the 403; the 632 have no cardinality assertion at all.

T374's own prover states the principle and then applies it to one arm only — case 2's banner
reads *"a comparator that only diffs existing files would report 'all identical' over a
shrinking population"* [VERIFIED: `out/PROVER-RERUN.txt:35-36`]. That is exactly right, and it
is enforced against a **working-tree** deletion and not against a **tracked-set** one.

Case 09 is minor but real: `open(path, "rb")` follows symlinks, so a regular file replaced by a
symlink whose target has identical bytes reports PASS. The bytes are right *at that instant*;
the file is no longer the tracked object and its content is thereafter controlled from outside
the repository.

**CONDITION 1.** Restate section 10's boundary (P-40) to name the measured set, not just the
mutation case: committed mutation, committed deletion, committed addition, untracked addition,
and same-bytes symlink substitution are all outside the two arms.

### FINDING 2 (MODERATE) — the closing artefact is NOT new; it is already tracked

T374's follow-up #1:

> A tracked `OBSERVATIONS.sha256` under `capture/tierA-a2` … Deliberately NOT done here: it is
> a **new evidence artefact**, not a repair of a filed finding.

Measured on the merge result:

```
tracked observations under out/ + req/       : 1035
  of which POST-FORK (arm A is blind to them): 632
MANIFEST.sha256 total rows                   : 1139
  of which out/ or req/ rows                 : 1035
tracked observations with NO manifest row    : 0 []
manifest rows naming NO tracked observation  : 0 []
manifest digest vs disk: agree 1035, DISAGREE 0, unreadable 0
POST-FORK observations covered by a manifest row: 632 of 632
```
[VERIFIED: `out/MANIFEST-COVERAGE.txt`, `instruments/50-manifest-covers-postfork.py`.]

`.softhouse/capture/tierA-a2/MANIFEST.sha256` **already is** a tracked, pinned, per-file digest
list whose out/req row-set is **exactly** the tracked observation path-set, with every digest
agreeing with disk. A third arm in `verify-capture-integrity.py` that asserts
`set(manifest_obs_rows) == set(tracked_obs_paths)` and recomputes each digest would close
cases **14, 15 and 16 outright** and raise case 13 from "append one line" to "append one line
**and** rewrite the manifest row". That is a repair inside the filed finding, not a new
artefact — and it costs one loop over a file the rig already writes.

**CONDITION 2.** Either add that arm, or correct follow-up #1 to say the artefact exists and
name why the arm was still deferred. As written the follow-up over-states the cost of closing
the gap, which is how a follow-up ages into never.

### FINDING 3 (MODERATE) — the saturation defect is repaired at ONE site; section 4 still absorbs 27 files

The coordinator's P-45 question, driven rather than argued. I audited **every** section's
return-code arithmetic, not just section 4:

| section | adjudicated | saturated? |
|---|---|---|
| 3, 5, 6, 7, 8, 9, **10** | 0 | **no** — any extra failure moves the section |
| 1 | 1 | **no** — section 9 pins its three failures and goes red on a fourth *or* a vanished one |
| 2 | 1 | shape yes, **inert** — every input is `git show <FORK>:…` / `git ls-tree <FORK>`; there is no disk read in the whole file, so nothing short of rewriting history can add a fourth failure |
| **4** | 1 | **YES, and live** — see below |

Aggregate arithmetic is clean: `sec()` records `(n, expected, actual)`, the verdict block counts
a deviation in **either** direction, and `SECTIONS -ne 10` is fail-closed and was moved with the
new section. Section 4 is still adjudicated RC 1 and still carries four live arms. Section 10 covers `out/` and `req/` only. Measured
difference:

```
entries in the fork-sha manifest       : 430
  of those under out/ or req/ (sec 10) : 403
  NOT under out/ or req/ (sec 4 ONLY)  :  27
```
— `cap.sh`, `env.sh`, `manifest.py`, `mkreq.py` … `mkreq6.py`, `rename1.py`, `show.py`,
`run-020-accounts.sh` … `run-120-delete-update.sh`, `sql/q1..q3*.sql`,
`prove-cap-transport-red.py`, `prove-manifest-blind-red.py`, `prove-manifest-red.py`,
`CAPTURE-PLAN.md`, `DEFECTS-FOUND-BY-REVIEW.md`, `FLAGGED-NOT-REPRODUCIBLE.txt`,
`RED-GREEN-D2-cap-transport.txt`, `RED-GREEN-D3-manifest-blindness.txt`.

These are the scripts that **produced** the observations and the red/green evidence that
grades them. Driven, on a target that is currently byte-identical (`manifest.py` — the script
that writes the manifest):

```
CONTROL   section 4 EXIT=1   byte-identical 428  DIFFER 2  manifest agrees 430
                             run-all EXIT=0   4 "as adjudicated"  10 "as adjudicated"
MUTATED   section 4 EXIT=1   byte-identical 427  DIFFER 3  manifest agrees 429
                             DIFF manifest.py / MANIFEST MISMATCH manifest.py
                             section 10 EXIT=0
                             run-all EXIT=0   deviations: 0   RUN-ALL VERDICT: PASS
```
[VERIFIED: `out/SATURATION-CLEAN.txt`, `out/sat31-*.txt`; the same result with laundering
(`out/sat-04-runall-laundered.txt`) and with an untracked fabricated `.http` in `out/`
(`out/sat-05-runall-untracked.txt`).]

That is **T362's F-1 verbatim**, one directory over: section 4 names the mutation, the section
cannot get redder, and the aggregate prints PASS. T374's fix is correct and it is where T362
pointed; the class is not closed. `verify-capture-integrity.py`'s boundary statement says it
does not cover *other capture directories, `.softhouse/vectors/`, or `obs/`* — it does **not**
say that section 4's byte-identity arm over these 27 in-directory files remains saturated, and
`run-all.sh`'s section 4 banner now reads as though the split closed the problem.

**CONDITION 3.** Either widen section 10 to the remaining 27 fork-sha manifest entries (the
population is already enumerated by section 4 and 25 of the 27 are byte-identical today; the
2 known differences, `CAPTURE-PLAN.md` and `cap.sh`, would be adjudicated exactly as section 4
adjudicates them), **or** state in both the docstring and the section 4 banner that the
saturation is only lifted for `out/` and `req/`.

### FINDING 4 (MODERATE) — section 10's baseline constant has no cross-check, and moving it reproduces T362's F-1 end to end

Section 4 ties its `FORK` literal to another tracked file: arm 0 asserts
`prove-a2-7-additive.py hard-codes the literal sha`. `verify-capture-integrity.py` carries the
same literal with **no tie to anything**, and no assertion on the ARM A population's
cardinality. Result of moving that one constant forward to a commit that contains a mutation
(see `out/DEFEAT-BASELINE.txt` for the driven run):

```
### 1. commit a mutation of a FORK-SHA observation (control repro of matrix case 12)
  section 10 EXIT=1        DIFFER : 1
    MUTATED .softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http
  FAIL  NO captured oracle observation that existed at the fork sha has been MUTATED

### 2. now move section 10's OWN baseline forward to the commit that contains it
  FORK = "4b81baa31ec8caa0004e0972510abb701f20af92"   <- the probe commit
  section 10 EXIT=0
      at the fork sha : 1035 observations  {'out': 906, 'req': 129}
      at HEAD         : 1035 observations  {'out': 906, 'req': 129}
      DIFFER          : 0
  PASS  NO captured oracle observation that existed at the fork sha has been MUTATED
```

One constant moved and ARM A's population collapses onto ARM B's — 403 → 1035, the two arms
stop being independent, and the mutation ARM A caught a moment earlier is invisible. Through
the whole runner, on T374's own branch:

```
### 3. and the whole runner
  run-all EXIT=0
  4         1              1         as adjudicated
  10        0              0         as adjudicated
  sections run: 10    deviations: 0
  RUN-ALL VERDICT: PASS
  --- does section 4 (saturated) still print the mutation by name? ---
        DIFF CAPTURE-PLAN.md
        DIFF cap.sh
        DIFF out/A2-000-glaccounts-preexisting.http
```
[VERIFIED: `out/DEFEAT-BASELINE.txt`.]

**That is T362's F-1 verbatim, reproduced on the branch that fixes it** — section 4 printing
`DIFF out/A2-000-glaccounts-preexisting.http` **by name** while `run-all.sh` exits 0 and prints
`RUN-ALL VERDICT: PASS`. The difference is that before T374 it took zero changes to the rig; now
it takes one, to a constant nothing checks. That is a real narrowing and I say so — but a
tripwire whose calibration is a bare unchecked constant is a tripwire with a switch on it, and
section 4 already demonstrates the cheap fix by tying its own copy of the same literal to
`prove-a2-7-additive.py`.

It is visible in a diff, so it is a *tripwire* weakness rather than an exploit; but the whole
value of section 10 is as a tripwire. A one-line assertion — `len(fork_paths) == 403` — closes
it, and would also have caught FINDING 1's cases 14/15 on the ARM A side.

**CONDITION 4.** Pin the ARM A population cardinality (`403`) and/or assert that `FORK` equals
the literal carried by `verify-manifest-independently.py`, in the same spelling section 4
already uses.

### Context the driver should weigh when scheduling the conditions

`run-all.sh` is **not invoked by `.softhouse/conformance.sh`** — `grep -c 'run-all.sh'
.softhouse/conformance.sh` = 0. Section 10 therefore runs only when somebody runs the A2-11
review rig by hand. That is pre-existing structure, not something T374 introduced, and it is
**not** a finding against T374; it does mean the F-1 repair improves an instrument the graded
bar never executes, which is the P-45 shape one level up. Worth a follow-up somewhere, owned by
whoever owns `conformance.sh` (T375's file — untouched by both T374 and me).

---

### T374's own prover reproduces independently

I re-ran `prove-t374-fixes-can-fail.sh` on the merge result, in a clone I made, not the
author's worktree:

```
############ SUMMARY   PASS=28   FAIL=0
T374 PROVER: PASS — every fix on this branch was driven RED on real bytes, and the
clean tree is still GREEN. Nothing in the working tree was mutated at any point.
--- working tree after the prover ---
 M .softhouse/capture/t374-t362-conditions/out/30-case0-F6-fresh-clone-GREEN.txt
 M .../31-case1-F1-mutated-observation-now-FATAL.txt
 M .../35-case5-F2-empty-vector-store-REFUSED.txt
 M .../36-case6-F3-fixed-synthetic-base.txt
 M .../37-case7-GREEN-again.txt
```
[VERIFIED: `out/PROVER-RERUN.txt`, `out/40-prover-wrapper-and-tree-state.txt`.] **28/28, exit 0**, and the tracked
evidence it rewrites is exactly the set T374's F-5 block discloses
(`capture/t374-t362-conditions/out/**`, with its revert). The disclosure is accurate.

## F-2 — the pin that moves DOWN. Resolved BY RUNNING (P-83), not by arithmetic.

`main` carries **109** rows; T374 ships **108**. The row delta, enumerated:

```
--- rows on main but NOT on T374 (REMOVED) ---
.softhouse/reviews/A2-11/verify-manifest-independently.py | .softhouse/A2-7-capture-mandatory-accounts
--- rows on T374 but NOT on main (ADDED) ---
   (none)
```

Exactly one row, and its cause is measured, not inferred. On `main`,
`verify-manifest-independently.py:74` and `:143` read

```python
git("rev-list", "--count", FORK + "..softhouse/A2-7-capture-mandatory-accounts")
git("diff", "--name-status", FORK + "...softhouse/A2-7-capture-mandatory-accounts")
```

The string literals `"..softhouse/…"` / `"...softhouse/…"` **contain the substring
`.softhouse/`**, so the census picks them up, collapses the `..` segments lexically, and
records the dead literal `.softhouse/A2-7-capture-mandatory-accounts`. F-6 replaced the branch
name with the literal sha `b3f2d9b2…`, the `..softhouse/` literal disappeared, and the row went
with it. `audit-float.py`'s `BRANCH = "softhouse/A2-7-…"` never produced a row — no leading dot
— which is why the delta is one row and not two. [VERIFIED: `out/FRONTIER.txt` §5, §6, and
`git grep` of `origin/main`.]

**What I expect the merge-result regeneration to produce — measured, not predicted.** I ran the
T326 regenerator in `--check` mode in all three conditions:

| condition | census `deadOccurrences` | committed pin rows | `10-regen-pin.py --check` |
|---|---|---|---|
| `main` (`5626b71b`, current) | **109** | 109 | **rc=0 IDENTICAL** |
| `softhouse/T374-t362-conditions` (`f4157d42`) | 108 | **108** | **rc=0 IDENTICAL** |
| **merge result** (`main` + T374) | 108 | **108** | **rc=0 IDENTICAL** |

[VERIFIED: `out/FRONTIER.txt` §1–§4; `T316-DEADPATH-CENSUS: corpus=1348 deadFiles=76
deadOccurrences=109 …` at main.]

So: **108 is what the regenerator produces on the merge result, byte-identical to the pin T374
ships.** The shrink is genuine, `added=0`, and no hand-picking is required. I am not resolving
the pin — that is the driver's job via
`.softhouse/capture/t326-frontier-host-state/instruments/10-regen-pin.py` — I am reporting that
running it on the merge result is expected to be a **no-op**, and that if it is *not* a no-op
the cause is another wave-3 branch, not T374.

Note for the driver: `main` moved from `05ce01de` to `5626b71b` **during** this review and the
result above is measured against `5626b71b`. If more branches land before T374 merges, re-run
the regenerator; T374's own blocker note says exactly this and it is correct.

---

## F-3, F-4, F-5, F-6 — re-derived

- **F-3** (false negative-control message). The repair replaces the live-transcript base with a
  fixed `SYNTH_BASE` that shares no bytes with the run. `parse_verdict` takes the first
  `FAILURES: n` line, so the defect is exactly as diagnosed and the fix is the right shape:
  a pure function given a pure input. **Accepted.**
- **F-4** (one of two ref fields). The new regex is `"(?:request_)?capture_ref"`. I enumerated
  every `capture_ref`-shaped field name actually present in the vector store:
  `grep -rhoE '"[a-z_]*capture_ref[a-z_]*"' .softhouse/vectors/ | sort | uniq -c` →
  **65 `"capture_ref"`, 13 `"request_capture_ref"`, nothing else**. The fix is **complete**, not
  merely wider. **Accepted.**
- **F-5** (silent tracked-file rewrite). The disclosure now prints at the site with its exact
  revert, and T374 discloses its own two rewrite paths. My own control runs reproduced the
  dirty `TRANSCRIPT-A2-11.txt` and the printed NOTE. **Accepted.**
- **F-6** (local-only ref). Verified independently from my worktree:
  `git rev-parse softhouse/A2-7-capture-mandatory-accounts` = `b3f2d9b26c347c31fae17a835b458e6b0485d710`,
  and both that sha and the fork sha `12a7f8d9…` are ancestors of `main`. `audit-float.py` and
  `verify-manifest-independently.py` both now REFUSE by name when the object is absent, instead
  of aborting on a traceback, and `audit-float.py` additionally refuses on an empty audited
  population rather than reporting "A2-7 added no Python". **Accepted.**

## Non-negotiables scanned across the diff

Diff restricted to the executable surface (`reviews/A2-11/*`, `prove-t374-fixes-can-fail.sh`,
973 lines): no `float(` call, no decimal literal, no `round(`, no `%f`; no
MySQL/MariaDB/`ojdbc`/`oracle.jdbc`/port 1521; no Stripe/Plaid/Lithic/Persona; no
`first_name`/`last_name`; no insured/protected/guaranteed string; no hard-coded UTC offset.
No change to `.softhouse/vectors/`, to any DEC-n, to the frozen adapter contract, to
`.softhouse/conformance.sh` or to `.softhouse/bin/fire-program.sh`.

**Money math is not engaged.** T374 computes no monetary value; the only numbers are `len()`
counts and sha256 digests. I say that rather than claiming to have re-derived arithmetic that
does not exist here. `MathContext(19, HALF_UP)` admissibility is not at stake on this branch.
The rule that *is* at stake — and that this branch defends — is the one upstream of all of it:
that the captured oracle observations we grade against are the bytes the oracle returned.

## What I could NOT test, and why

- **Whether another wave-3 branch also regenerates the pin.** Four other workers are live in
  this repo and `main` moved under me mid-review. Measured at `main` = `5626b71b` only.
- **Whether an ARM B `git show HEAD:<path>` failure is distinguishable from a real FAIL.** ARM
  B's `git()` call has no `try/except` (ARM A's does), so a failure raises and Python exits 1 —
  the same code as a genuine mutation. Fail-closed, so not a defect; I did not construct a
  repository state that makes `git show HEAD:<tracked path>` fail.
- **A mutation committed to the fork sha itself.** Rewriting `12a7f8d9…` is not reachable
  without rewriting `main`'s history; I tested the reachable version instead — swapping the
  constant (case 19: REFUSED) and moving it forward (FINDING 4).
