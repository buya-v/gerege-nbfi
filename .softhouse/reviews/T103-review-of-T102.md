# T103 — independent review of T102 (`softhouse/T102-literal-fork-sha`)

**Reviewer:** T103, spawned fresh, no planning context.
**Subject:** T102's change and T102's evidence. T82's code was reviewed by T87 and is not re-reviewed here,
except where T102 edited `T82.md` or where T87's outstanding items M-1 / M-2 land.
**Branch under review:** `softhouse/T102-literal-fork-sha` @ `61e710255e5ffce70b9694cc62990acd88d17b03`,
based on `softhouse/T82-pass3i-defects` @ `55409cfda225518d014a0d203dc4b36191a045a8`.
**Method:** re-run, not read. Every number below was produced by a command I ran in this review.

## VERDICT: **MICRO-FIX**

Four mechanical documentation edits (F-2 ×3 sites, F-3 ×1 sentence), **≤10 lines, no number, no money
logic, no executable path**. None is a merge blocker; the driver may apply them on merged main.

**The substantive fix is correct and is verified in the state that matters.** I reproduced all four cells
of T102's matrix by my own constructions, drove all four refusals red myself, and independently confirmed
the one claim that came from the worker rather than the brief (a scratch worktree cannot reproduce the
defect). T102's committed transcripts are genuine: three of the four are **byte-identical** to my own runs
after root normalisation, and the fourth differs in exactly one line — the merge commit sha, which must
differ by construction.

**T82 + T87 + T102 are SAFE TO MERGE TOGETHER into main.** See the closing section for what to re-verify
after merging.

---

## 1. The fork point, measured independently

```
$ git merge-base main softhouse/T82-pass3i-defects
8da4b831b96a146c2b46ad34d85ed098395de160
$ git merge-base main softhouse/T102-literal-fork-sha
8da4b831b96a146c2b46ad34d85ed098395de160
```

**Equals T102's literal.** [VERIFIED: my own `git merge-base`, run twice.]

`main` **moved under me during this review** — `2efed5d6cb1b6de45e2d8dc7cb8a39893e5aa564` →
`2755999b00959bcd8668a78cb5d8fcf7a0927a90` (sibling worker T90 landing in the same fire). I re-measured
after the move: the fork point is **unchanged**. That is the property the pin is supposed to have, and I
observed it happening rather than arguing it. [VERIFIED: `git rev-parse main` before and after; second
`git merge-base` above.]

Corroborated by content, not only by ref arithmetic — all **three** files the rig extracts from the
baseline differ from the shipping bytes, so every counterproof is over a genuinely different codebase:

| file | BASE @ `8da4b83…` | shipping on branch |
|---|---|---|
| `.softhouse/capture/src/run-pass3i.sh` | `d84ec7bf9888…84e0d3` | `3ca0d3f6380a…fe2a519` |
| `.softhouse/handoff/T74-promote-vectors.py` | `27bb20b4161b…87c3d1` | `efcfcfa59305…5a94e4` |
| `.softhouse/capture/t74-multiplesof/build-counterfactuals.py` | `e7aee9173359…aceac3f` | `b1e9f6087f93…0ed9f1` |

[VERIFIED: my own `git show <sha>:<path> | shasum -a 256` vs `shasum -a 256 <path>` on the branch tree.]
T102's transcript prints only the first two; I checked the third because a non-discriminating third
baseline would have silently weakened the D-1/D-2 counterproofs. It discriminates.

---

## 2. My own merge states, built two ways

I never touched the real `main`. Everything below is a throwaway `git clone --local` of this repo under
`/tmp`, plus detached worktrees of those clones. All removed at the end.

### Construction 1 — clone, `git merge` into the clone's own `main` (two-parent merge)

| # | rig | where | `main` | `merge-base main HEAD` | result |
|---|---|---|---|---|---|
| 1 | pre-fix (`merge-base main HEAD`) | detached worktree @ `55409cf` | `2755999b` | `8da4b83` (real fork point) | **25 as expected, 0 not** — exit 0 |
| 2 | pre-fix | clone B, `main` = merge of main+T82 = `f91e6db` | `f91e6db` | **`f91e6db` — the merge itself** | **18 as expected, 7 not** — exit 1 |
| 3 | post-fix (literal) | detached worktree @ `61e7102` | `2755999b` | (unused) | **25 as expected, 0 not** — exit 0 |
| 4 | post-fix | clone A, `main` = merge of main+T102 = `507dfae` | `507dfae` | (unused) | **25 as expected, 0 not** — exit 0 |

[VERIFIED: my own runs; transcripts `/tmp/t103-{prefix,postfix}-{branch,merged}.txt` produced in this
review.]

### Construction 2 — clone, `main` **forced to be the branch tip** (a fast-forward-shaped merge)

`git checkout -B main <tip>`, so `main == HEAD == the branch`. A different topology from construction 1,
and it exercises the same failure:

| clone | `main` forced to | rig | result |
|---|---|---|---|
| D | `55409cf` (T82 head) | pre-fix | **18 as expected, 7 not** — exit 1; BASE `run-pass3i.sh` = `3ca0d3f6…` (the fixed bytes) |
| E | `61e7102` (T102 head) | post-fix | **25 as expected, 0 not** — exit 0; BASE = `8da4b83…`, `d84ec7bf…` |

[VERIFIED: my own runs.]

### Construction 3 — merge at the newest `main`, then merge T87 as well

After `main` advanced to `2755999b` I merged T102 into a fresh clone's `main` (`5061983c`), ran the rig:
**25/25, exit 0**; then merged `softhouse/T87-review-t82` on top (`3651312a`), ran it again:
**25/25, exit 0**. [VERIFIED: my own runs.]

**Three independent constructions, same answer.** Claim (d) holds.

### The seven, by label

Exactly the seven COUNTERPROOF rows, and **no GUARD, CONTROL or REGRESSION row moved** — the signature of
a baseline defect rather than a guard defect:

```
:45  E-1 COUNTERPROOF — the SAME unregistered id through the FORK POINT'S REAL pre-T82 bytes
:128 E-3 COUNTERPROOF — the SAME both-arms capture through the FORK POINT'S chained comparison
:157 D-1 COUNTERPROOF — the FORK POINT accepts it and writes the hard-coded FIXED_30_360
:181 D-1 COUNTERPROOF — the FORK POINT accepts it and writes the hard-coded {0, 1}
:217 D-2 COUNTERPROOF — the FORK POINT accepts it and writes a NULL repayment interval
:253 D-2 COUNTERPROOF — the FORK POINT accepts it, writes installment_number 0 and promotes six vectors
:277 D-2 COUNTERPROOF — the FORK POINT accepts that too
```

Every one expected exit 0 and got exit 1. [VERIFIED: line numbers are into my own
`/tmp/t103-prefix-merged.txt`.] Matches T102's claim (d) label for label.

### The mechanism, in one number — claim (f)

| run | `merge-base main HEAD` | extracted BASE `run-pass3i.sh` sha256 |
|---|---|---|
| branch, pre-fix | `8da4b83…` | `d84ec7bf9888…84e0d3` |
| my scratch merge, pre-fix | `f91e6db…` (the merge commit) | `3ca0d3f6380a…fe2a519` |

`3ca0d3f6…` is the sha256 the **same transcript** prints on line 2 for the branch's own *shipping*
`run-pass3i.sh`. The counterproof was diffing the fixed code against itself. [VERIFIED: lines 2 and 7 of
`/tmp/t103-prefix-merged.txt`.] Claim (f) holds, on my merge as well as T102's.

---

## 3. Claim (c) — a scratch WORKTREE cannot reproduce the defect. **CONFIRMED.**

This is the load-bearing claim that came from the worker, not the brief, so I built it myself.

```
$ git worktree add --detach /tmp/t103-wt-scratch main     # in a throwaway clone, main = 2755999b
$ cd /tmp/t103-wt-scratch && git merge origin/softhouse/T82-pass3i-defects
$ git rev-parse HEAD          fb9e8f1e439e89203fdd05fe2444395b4ff0f572   (the merge)
$ git rev-parse main          2755999b00959bcd8668a78cb5d8fcf7a0927a90   (STILL the pre-merge tip)
$ git merge-base main HEAD    2755999b00959bcd8668a78cb5d8fcf7a0927a90
$ bash prove-guards-go-red.sh
  fork-point (BASE)   2755999b00959bcd8668a78cb5d8fcf7a0927a90
  BASE run-pass3i.sh  sha256 d84ec7bf9888…84e0d3          <-- the REAL pre-fix bytes
  T82 guard proofs: 25 as expected, 0 not as expected      (exit 0)
```

[VERIFIED: my own run.] The PRE-FIX rig passes **25/25 in a worktree merge**, for the wrong reason: the
ref `main` still names the pre-merge tip, that tip still carries the pre-T82 bytes, so the counterproofs
compare against real old code by accident.

**One precision T102's write-up is slightly loose about, and I checked it rather than assume:** in the
worktree case `merge-base main HEAD` resolves to **main's tip**, not to the fork point — because after the
merge `main` is an ancestor of `HEAD`. T102's handoff says it "resolves to `ab2de89` — the old, pre-fix
main", which is exactly right in substance; the `FORK-POINT-SHA` header's phrasing "resolves to the real
fork point" would be the loose reading, and it does not appear there. No finding.

**Consequence, stated plainly:** a reviewer who had used a worktree — the obvious, cheap, in-repo way to
test this — would have reported a false green for the third time. T102's headline finding is true, and it
is the most valuable thing in the task.

---

## 4. Reproducing 18/7 with my own hands, from real bytes

Done, twice (clone B two-parent merge; clone D forced fast-forward). I restored the pre-fix rig by
checking out the actual pre-T102 commit `55409cf` rather than trusting any saved transcript, so the "before"
is git's bytes, not T102's. **18 as expected, 7 not as expected, exit 1**, both times. This is what makes
the change a fix rather than a no-op (P-22 / the T85 lesson).

**Evidence-integrity check on T102's committed transcripts.** I diffed my runs against
`T102-merge-acceptance/*.txt` after normalising the repo root:

| transcript | result |
|---|---|
| `postfix-branch.txt` | **byte-identical** to my run |
| `postfix-merged.txt` | **byte-identical** to my run |
| `prefix-branch.txt` | **byte-identical** to my run |
| `prefix-merged.txt` | identical **except one line**: `fork-point (BASE) ff73824…` (T102's merge) vs `f91e6db…` (mine) — differs by construction |
| `TRANSCRIPT.txt` | **byte-identical** to my post-fix branch run |
| `no-fallback.txt` | messages and exits identical to my own four refusal runs |

[VERIFIED: `diff` after `sed` root substitution; commands in `/tmp/t103-cmp3.sh`.] **T102 did not fabricate
or edit its transcripts.** I also re-checked T102's own claim (e) on its own artefacts: `postfix-branch.txt`
vs `postfix-merged.txt`, root-normalised, `diff` **exit 0** — byte-identical. Claim (e) holds.

---

## 5. The four no-fallback refusals, driven red by me

Venue: the post-fix **merged** clone, so the refusals were exercised in the state that matters.

| # | input | exit | stdout bytes | proof rows run |
|---|---|---|---|---|
| 1 | file missing | **2** | 0 | **0** |
| 2 | `not-a-sha` | **2** | 0 | **0** |
| 3 | `8da4b83` (7 hex) | **2** | 0 | **0** |
| 4 | `deadbeef…deadbeef` (40 hex, not a commit) | **2** | 0 | **0** |

[VERIFIED: my own runs, `/tmp/t103-refusals.sh`. "stdout bytes = 0" is the strong form of "no proof row
ran" — the rig had not even printed its header.] Claim (b) holds. Each message names the file and says why
there is no fallback.

### Hunting a fifth input that gets past them

| # | input | outcome | assessment |
|---|---|---|---|
| 5a | empty file (0 bytes) | **exit 2**, 0 rows | refused |
| 5b | only comments and blank lines | **exit 2**, 0 rows | refused |
| 5c | two shas, fork point first, main tip second | **accepted**, uses the **last** line, 25/25 | documented format; sha is echoed in the header. **F-6, P4** |
| 5d | sha of a **tree** | **exit 2**, 0 rows | refused — `^{commit}` does the work |
| 5e | sha of an **annotated tag** peeling to the fork point | **accepted**, 25/25, correct bytes | **not a defect** — a tag object id is itself immutable and peels deterministically |
| 5f | the **correct** sha in UPPERCASE hex | **exit 2**, 0 rows | false refusal, but fails **safe**. **F-5, P4** |
| 5g | correct sha + trailing spaces + CRLF | **accepted**, correct sha | handled |
| 5h | a valid commit that **predates the three files** (root commit) | `git show` writes `fatal:` to stderr, script continues (`set -u`, no `set -e`), three **empty** baseline files (`e3b0c442…` = sha256 of empty), **18/7, exit 1** | **F-4, P3** |
| 5i | **current `main` tip** — a valid commit, not the fork point | **accepted**, **green 25/25** | **F-3, P2** |

[VERIFIED: all nine run by me, `/tmp/t103-fifth.sh`.]

---

## 6. Can the baseline still follow `main`? — sweep

Grepped the **post-fix branch tree**, not just the rig directory, for `merge-base`, `main:`, `main^`,
`main~`, `origin/main`, `refs/heads/main`, `HEAD~`, `HEAD^`, `@{`, `git describe`, `for-each-ref`,
`symbolic-ref`, `rev-parse main`.

**Executable uses of a moving ref in the rig: ZERO.** Every remaining hit in
`prove-guards-go-red.sh`, `prove-promote-guards.py`, `mutate.py` is inside a comment, a docstring or an
error string, and every one of them is a **prohibition** ("never `main:`"). [VERIFIED: my own grep.]

`BASE` is not environment-overridable — `FORK_SHA_FILE="$HERE/FORK-POINT-SHA"` (`:65`) and `BASE=…`
(`:74`) are unconditional assignments, no `${…:-}` default, no `export`. `ROOT` is derived from the
script's own location, not from a ref. [VERIFIED: my own grep of `:32,33,65,74`.]

Outside the rig, two historical probes **do** execute a moving ref — `.softhouse/reviews/t45-probe/t45_normdiff.py:33`
and `.softhouse/reviews/t47-probe/t47_normdiff.py:33`, both `subprocess.run(["git","show",f"main:{DOC}"])`.
These are **frozen records of past DEC-1 re-reviews**, already on `main`, untouched by this branch, and
their subject (`docs/adr/DEC-1-…md`) is not this rig's baseline. Not T102's to fix; flagged so the fact is
on the record, and see follow-up 4.

### Ruling on `T82.md:522` — **T102's call was RIGHT**

The line T102 deliberately left:

```
`conformance.sh:68,100` on `main`) [VERIFIED: `git show main:.softhouse/conformance.sh`]
```

I rule this **correct to leave as `main:`**, on three grounds:

1. It is a claim **about main's current state** ("T81's guard has since merged to main"), not a baseline
   pin. Freezing it to a literal sha would *weaken* it to "the guard was there at commit X".
2. The claim is monotone: it stays true as main advances, and the cited command **self-verifies** when
   re-run. That is the exact opposite of the counterproof baseline, where re-running post-merge makes the
   command refute its own finding.
3. Nothing executable depends on it.

I verified the claim rather than only its shape: on today's `main`, `conformance.sh:68` is
`EXIT_WRONG_INTERPRETER=3` and `:100` is `exit "$EXIT_WRONG_INTERPRETER"`; the branch's own copy has no
such symbol, so `T82.md`'s statement that this branch predates the guard is also true; and after merging,
the merged tree keeps main's guarded copy. In a throwaway clone I ran `sh .softhouse/conformance.sh`
deliberately and got **exit 3** with the documented message. [VERIFIED: my own `git show main:`, `grep`,
and one deliberate `sh` invocation in `/tmp/t103-cloneA`.]

**Caveat, non-blocking:** the fragile part of that citation is not the ref, it is `:68,100` — line numbers
into a file that can move on main. They resolve **today**. If `conformance.sh` is edited they silently
become off-by-N inside a `[VERIFIED:]` block, which is precisely the M-1 defect class. Citing the symbol
`EXIT_WRONG_INTERPRETER` instead of the line numbers would close it. Follow-up, not a finding against T102.

---

## 7. Does T102's sweep have T82's P-12 shape-dependence? — **No.**

Test: replay T102's stated patterns against the **pre-fix** tree (`55409cf`) and check they surface every
site T102 claims to have found.

```
prove-promote-guards.py:11     `git show $(git merge-base main HEAD):…`     <- named by the brief
prove-promote-guards.py:200    error message, same form                     <- named by the brief
prove-guards-go-red.sh:47      the comment justifying the wrong form
prove-guards-go-red.sh:52      BASE="$(git -C "$ROOT" merge-base main HEAD)"  <- the load-bearing one
mutate.py:13                   `git show main:…run-pass3i.sh`               <- NOT in the brief
T82.md:46                      "the immutable fork point, git merge-base main HEAD"  <- NOT in the brief
T82.md:124                     same form in the counterproof evidence row   <- NOT in the brief
T82.md:304                     [VERIFIED:] provenance command               <- NOT in the brief
T82.md:521                     `git show main:.softhouse/conformance.sh`    <- deliberately left
```

[VERIFIED: my own grep against `/tmp/t103-wt-prefixbranch`.] **All nine sites surface, including the three
T102 says the brief did not name.** Claim (g) holds.

**Why this sweep is structurally safer than T82's census sweep.** T82's regexes searched for a *phrasing*
of a count, so a markdown-table rendering of the same census escaped them — P-12 inside the task assigned
to close P-12. T102 searched for the **executable ref syntax itself** (`main:`, `merge-base`). A moving-ref
baseline cannot be re-rendered into a different shape and still be a moving-ref baseline: the string has to
be there for git to run it. The blind spot T102 declares (limitation 1: a ref assembled from fragments, a
variable, `git log -1 --format=%H`, a tag) is real and is the honest statement of the limit. I read all
five rig scripts end to end and found none of those.

---

## 8. T87's outstanding items — **M-1 and M-2 are both FIXED on this branch head**

They were **not** lost when T102 superseded T98's approach. T102 is a superset of `55409cf`, which is
T98's head.

### M-1 — six off-by-one `main:` citations inside a `[VERIFIED:]` block. **FIXED, and correct.**

I re-read the fork-point bytes myself rather than trusting the correction:

```
$ git show 8da4b831b96a146c2b46ad34d85ed098395de160:.softhouse/handoff/T74-promote-vectors.py | sed -n '253,261p'
253:            row = {
254:                "kind": p["type"],
255:                "installment_number": p.get("periodNumber") or 0,
…
260:            if p.get("periodNumber") is None:
261:                unrecorded.append("installment_number")
```

[VERIFIED: my own run of exactly that command.] `:255` / `:260` / `:261` are right; `:254` is
`"kind": p["type"],` as the correction says. The corrected citations are live in
`prove-promote-guards.py:137,138,225,226` and in `T82.md`'s `[VERIFIED:]` block.

**And T102 improved the fix beyond what M-1 asked:** the provenance command in that block now uses the
**literal sha**, so it is re-runnable post-merge. Under T98's form the same block would have shown the
**fixed** source lines after merge and appeared to refute the finding it supports. That is finding (g)'s
third site and it is genuinely closed. I ran the command post-merge-equivalent and got the pre-fix lines.

### M-2 — `T82.md` printing `1093/47/622` against `SWEEP.txt`'s figures. **FIXED, in the stronger way.**

The transcription is **deleted**, not updated: `T82.md:393-400` now says "The counts are not restated
here… read them from the artefact", which removes the drift class instead of resetting it. [VERIFIED: my
own read of `T82.md:393-400` and grep — the only surviving occurrences of `1093 / 47 / 622` are the two
places that describe it as the *stale* set.]

**But the artefact it now points at is itself stale — see F-1.**

---

## 9. Findings

### F-1 (P3) — `SWEEP.txt` no longer matches its own commit, and the handoff tells the reader to trust it

`T82.md` instructs: *"read them from the artefact: `$ head -9 …/SWEEP.txt`"*. On the shipped tree:

| | committed `SWEEP.txt` | `sweep-census.py` re-run on the same commit |
|---|---|---|
| prose files (TIER 1) | 164 | **166** |
| other files (TIER 2) | 1778 | **1784** |
| TIER 1 hits | 1106 | **1107** |
| PASS B | 49 | 49 |
| PASS C | 627 | **628** |

[VERIFIED: my own `python3 sweep-census.py .` in `/tmp/t103-wt-postfixbranch`; two consecutive runs
byte-identical, so this is drift, not nondeterminism.] Re-run on the **pre-fix** tree (`55409cf`) the
script reproduces the committed file exactly (164/1778/1106/49/627), so T98 generated it correctly and
**T102's own two new prose files** (`T102.md`, `T102-merge-acceptance/README.md`) moved it.

Curiosity worth recording: `1107/49/628` are the very figures T87 quoted for `SWEEP.txt` in M-2.

**The honest reading is that this invariant is unmaintainable as stated.** The census counts are a
property of the whole repo tree, so *any* later commit — including this review file — staleness them.
Regenerating is a treadmill. The durable fix is to have `SWEEP.txt` record the commit it was generated at,
exactly as `FORK-POINT-SHA` does, and to have `T82.md` say "as of commit X" rather than implying currency.
**Recommended as a follow-up, not required for merge.**

### F-2 (P3, part of the MICRO-FIX) — the documented recovery command does not work

`T102` replaced `git show $(git merge-base main HEAD):…` with `git show $(cat …/FORK-POINT-SHA):…` in
three places. That command **fails**, because `cat` emits the file's 25-line comment header:

```
$ git show $(cat .../FORK-POINT-SHA):.softhouse/capture/src/run-pass3i.sh
fatal: failed to stat '# T102 — THE COUNTERPROOF BASELINE, AS A LITERAL IMMUTABLE SHA.
#
# This is the fork point of `softhouse/T82-pass3i-defects` from `main`: the last commit that
```

[VERIFIED: my own run.] Sites:

- `mutate.py:14` — docstring.
- `prove-promote-guards.py:11-12` — module docstring.
- `prove-promote-guards.py:206-207` — the **operator-facing** `SystemExit` message, i.e. the one place a
  human is actively being told how to recover.

The working forms both exist already: the rig's own
`grep -vE '^[[:space:]]*(#|$)' FORK-POINT-SHA | tail -n 1`, and the literal sha as used in `T82.md:304`.
**Fix: use the literal sha in the three message/doc strings** (mechanical, no number changes — the sha is
already printed elsewhere in each file's neighbourhood). Mildly ironic given T102's own finding (g) was
that a non-re-runnable provenance command is a defect; the same standard applies to its replacement.

### F-3 (P2, part of the MICRO-FIX) — "nothing can detect a wrong-but-valid pin" is **false as stated**

`T102.md` §Unverified says the rig *"cannot detect a sha that exists and is the **wrong** fork point —
**nothing can**"*. I demonstrated the failure (case 5i: pinning `main`'s tip is silently accepted and
scores a **green 25/25**), and I also demonstrated that something **can** detect it: the rig already
**computes and prints** `BASE run-pass3i.sh sha256` and `BASE promote-vectors sha256` — it simply never
**compares** them. Pinning the two expected sha256s alongside the sha would refuse a wrong-but-valid
baseline before any proof row runs.

This is the exact shape recorded in **P-22**: *"a canary that printed a sha256 without ever comparing it
certified `HALF_UP` on a HALF_EVEN JVM"*. Here the literal pin makes it defence-in-depth rather than an
active defect, so it is not a rejection — but an **overclaimed impossibility inside the artefact a
decision-maker reads** is a P-23 write-up defect, and it is one sentence.

**Micro-fix: correct that sentence.** Closing the hole properly (comparing the sha256s) is a follow-up,
not a micro-fix.

### F-4 (P3) — a valid commit that lacks the baseline files is not refused, only mis-scored

`prove-guards-go-red.sh` runs under `set -u` **without** `set -e`. If `BASE` is a real commit that does not
contain the three extracted paths, `git show` writes `fatal:` to stderr and the script **continues** with
three **empty** files (`e3b0c442…`), scoring **18/7, exit 1**. Not a false green — but the score is
**indistinguishable from the merge-state defect it exists to diagnose**, so an operator would misdiagnose
it. Three `git show … || { echo FATAL…; exit 2; }` guards would name it. Follow-up.

### F-5 (P4) — the correct sha in UPPERCASE hex is refused

`case "$BASE" in *[!0-9a-f]* )` rejects `8DA4B831…`, which git itself accepts. Fails **safe** (exit 2, no
rows), so not a defect; recorded only so nobody is surprised.

### F-6 (P4) — two shas in the file silently take the last

Documented behaviour ("the last remaining line"), and the chosen sha is echoed in the transcript header, so
it is visible. A *prepend*-shaped edit after a rebase would silently mis-baseline. Recorded, not charged.

### Non-findings, stated so silence is distinguishable from not looking

Refused correctly: empty file; comments-only; tree sha. Handled correctly: trailing whitespace; CRLF.
Accepted and **harmless**: an annotated tag object's sha (the tag object id is itself immutable and peels
deterministically). No guard predicate was touched — the only executable change in the whole branch's rig
is how `BASE` is obtained. `prove-promote-guards.py`'s changes are a docstring and a message string;
`mutate.py`'s is a docstring.

---

## 10. Invariants

| invariant | result |
|---|---|
| `git diff main...softhouse/T102-literal-fork-sha -- .softhouse/vectors/` | **EMPTY** [VERIFIED: `--stat` produced no output] |
| `PIN.json`, `capabilities.json` | **untouched** — absent from the name-only diff |
| `nexus/` | **untouched** — `git diff main...branch -- nexus/` empty |
| `contract.go` | **byte-identical to main**, sha256 `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` on both sides [VERIFIED: my own `shasum` of the file and of `git show main:…`] |
| `gofmt -l nexus/` | names **exactly** `internal/apps/loanschedule/contract/contract.go` — the expected **G-3** state, not a defect; `gofmt -w` was **not** run |
| `go build ./...` | **exit 0** |
| `go test ./...` | **ok** `loanschedule` 8.698s, **ok** `conformance` 8.121s, 2 packages with no test files |
| `bash .softhouse/conformance.sh` on **merged main + T102** | **VERDICT: PASS, exit 0** — 42 parity PASS / 0 FAIL, 4 contract-refusal, 1 self-test, **5576 graded cells**, 84 ungraded, 0 refused, 0 inadmissible, 0 harness errors, **0 invariant violations**, 0 assertions NOT RUN |
| `bash .softhouse/conformance.sh` on **merged main + T102 + T87** | **VERDICT: PASS, exit 0** — same figures |
| `sh .softhouse/conformance.sh` (throwaway clone, deliberate) | **exit 3**, `EXIT 3 — wrong interpreter` — the T81 guard, not an oracle outage |
| money non-negotiables | **not engaged.** Grep over T102's added lines for `float32/float64/big.Float/first_name/last_name/insured/guaranteed/ojdbc/oracle.jdbc/mysql/mariadb/:1521/Stripe/Plaid/FixedZone/+08:00/+07:00`: **no hits**. No vector, no capture, no schedule arithmetic, no rounding. The only numbers this branch moves are git object ids. |
| oracle | **never contacted.** The rig is `git show` + `python3`; `conformance.sh` grades against committed vectors. No HTTP, no Docker command, no DB, no restart, no write. |
| hedged `[VERIFIED]` tags in `T102.md` | **none** [VERIFIED: my own grep for `not independently / cited by / assum / believ / presum / should / likely / appears` inside `[VERIFIED…]`] |
| scratch cleanup | five throwaway clones and three detached worktrees under `/tmp`, all removed; my worktree clean |

---

## 11. Safe to merge?

**YES — T82 + T87 + T102 are safe to merge together into main.**

- `softhouse/T87-review-t82` adds exactly two files (`T87.md`, `T87-review-t82.md`, 692 insertions) and
  touches nothing T102 touches. I performed the full three-way merge (current `main` + T102 + T87) in a
  throwaway clone: **both merges clean, no conflicts**, rig **25/25 exit 0**, conformance **PASS exit 0 /
  42 vectors / 5576 cells / 0 invariant violations**. [VERIFIED: my own runs.]
- T102 contains T82 and T98 in its history (`61e7102` → `a48da58` → `dd69927` → `55409cf` → `849d618` →
  `0101fbb` → `402a1da`), so merging T102 merges T82's reviewed work with it.

### What the driver must re-verify **on merged main, before pushing**

Per **P-24**, re-run the *artefact*, not only conformance:

1. `bash .softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh` → must print
   **`25 as expected, 0 not as expected`**, exit 0, and the header must read
   `fork-point (BASE) 8da4b831b96a146c2b46ad34d85ed098395de160  [LITERAL, from FORK-POINT-SHA …]`
   with `BASE run-pass3i.sh sha256 d84ec7bf…`. **If `BASE` prints anything other than `8da4b83…`, stop** —
   the pin has been bypassed.
2. `bash .softhouse/conformance.sh` → `VERDICT: PASS`, exit 0, 42 parity, 5576 graded cells, 0 invariant
   violations. **`bash`, never `sh`** — `sh` gives exit 3, wrong interpreter, which is *not* an oracle
   outage.
3. `gofmt -l nexus/` → must name **exactly** `nexus/internal/apps/loanschedule/contract/contract.go`.
   Do not "fix" it (G-3).
4. **Re-measure the pin if the branch is rebased before merge.** `git merge-base main softhouse/T82-pass3i-defects`
   must still be `8da4b831b96a146c2b46ad34d85ed098395de160`; if history is rewritten the rig aborts
   loudly (exit 2, "not a commit"), which blocks rather than mis-baselines.
5. Optionally apply the MICRO-FIX (F-2's three doc/message sites, F-3's one sentence) directly on merged
   main — they are documentation only and cannot change the score.

### Follow-ups for the postmortem

1. **F-3's real closure:** pin the expected `BASE` sha256s next to the sha in `FORK-POINT-SHA` and have the
   rig **compare** them. The rig already computes both. This closes the one hole the four refusals cannot
   see, and it is the P-22 lesson applied to T102's own artefact.
2. **F-4:** three `|| { echo FATAL; exit 2; }` guards on the `git show` extractions, so a baseline missing
   the files is *named* rather than mis-scored as 18/7.
3. **F-1:** give `SWEEP.txt` a generating-commit header; stop implying its counts are current.
4. `.softhouse/reviews/t45-probe/t45_normdiff.py:33` and `t47-probe/t47_normdiff.py:33` still execute
   `git show main:…`. Frozen historical probes, but if either is ever re-run to re-verify a DEC-1 claim it
   will silently compare the current main rather than revision 8. Worth a banner.
5. **T102's two candidate patterns are both worth adopting**, and I confirm both by measurement:
   *"a rig whose result depends on the repository's merge state must be run in BOTH states, and the strong
   form of the claim is byte-identical transcripts, not a matching score"*, and *"a scratch worktree is not
   a scratch merge — `git worktree add --detach <tmp> main` leaves `main` at the pre-merge tip and hides
   this defect class entirely."* The second is the one that would have saved two previous attempts.

---

## 12. What I could NOT verify

- **[UNVERIFIED]** the driver's original "18 as expected, 7 not as expected" from *its* merge of T82+T87.
  I reproduced 18/7 from my own merges (T82 alone, two topologies) and the seven rows match by label, but
  I did not re-create the driver's exact merge commit.
- **[UNVERIFIED]** that **25/25 is the *correct* score** rather than the *expected* one. I inherited
  T82/T98's guard predicates and expected exit codes and did **not** re-derive whether each guard tests
  what its label claims — that was T87's job and is outside this review. My claim is only that the score no
  longer depends on merge state, and that the seven counterproofs now run against genuinely different
  pre-fix bytes.
- **[UNVERIFIED]** that no moving-ref baseline exists outside `.softhouse/` and this branch's 25 files. I
  swept the branch tree's `*.sh`/`*.py`/`*.json`; I did not audit `.claude/skills/` or `docs/` for
  semantically-assembled refs with no textual match.
- **[UNVERIFIED]** behaviour under a three-way or octopus merge. I measured three topologies (two-parent
  merge, forced fast-forward, and a second two-parent merge at a later main), all consistent. The literal
  pin is insensitive to topology by construction, but construction is an argument, not a measurement.
- **[UNVERIFIED]** anything about the Fineract reference oracle. This review contacted **no** oracle, no
  container and no database; nothing here is a claim about Fineract behaviour or about any money value.
