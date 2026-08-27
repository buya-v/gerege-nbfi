# T181 — independent review of T178 (`softhouse/T178-t47-rewriters-guarded`)

**Reviewer:** T181 · **Run:** `2026-08-21-run2-tierA-gl-accounting-A2`
**Fork point:** `git merge-base HEAD main` = `1672d857f42c7bfe20beec2c8f07e62484c7b469`; HEAD == main == `1672d85` at start.

## VERDICT: **MICRO-FIX**

The eight guards T178 shipped are **sound**, and I verified that exhaustively and independently
(89 cases, 0 not-as-expected). The live gate bypass T178 claims to have closed **was real**, and I
reproduced it from scratch. Two defects sit in the **ancillary record and tooling**, not in the guards:
a published split that contradicts T178's own committed transcript (a **number** — raised, not fixed),
and a **zero-inspection GREEN** in the census T178 proposes to promote to a hard verifier check
(**micro-fixed**, 6 lines of code, no measured number changed).

---

## P-59 — which diff form I had to use

**`git diff main...softhouse/T178-t47-rewriters-guarded` returned 0 bytes and read as clean.** T178 is
merged, so `git merge-base main softhouse/T178-t47-rewriters-guarded` **is the branch tip itself**
(`085e69d`), which collapses the three-dot form to nothing. `git diff main..<branch>` gives 3,456,807
bytes but is the reverse direction (main-ward changes), not T178's.

**Form actually used:** the merge commit's two parents.

```
merge commit 72ca1757285ea8e263dc6f1befa7b84833561dea
   parents   0c35634a05fb6a6322de47e0806353275d2d8f7d  085e69d7d1af313a533c93ce8d0524cc604a676d
   git diff 72ca175^1...72ca175^2   ->  181,003 bytes, 20 files changed, 2822 insertions(+), 96 deletions(-)
```

Handoff read from the branch (`git show <branch>:.softhouse/handoff/.../T178.md`), not from disk.

---

## Findings, ranked

### F-1 — MAJOR (number). The published split is wrong, and it contradicts T178's own transcript.

T178's handoff F-1 states: *"**21 target the ratified DEC-1; 4 target the frozen `contract.go`**"*.

**Independently re-derived (`t181-split-census.py`, `-output.txt`):**

| | files |
|---|---|
| DEC-1 only | **18** |
| `contract.go` only | **5** (`edit22.py`, `edit_go1..4`) |
| **both artefacts** | **2** (`edit18.py`, `edit21.py`) |
| **distinct files** | **25** |
| **targeting DEC-1** | **20** |
| **targeting `contract.go`** | **7** |
| **(file,artefact) pairs** | **27** |

This is an **exact match** with the T187 + T183 blind convergence. Third independent arrival, by a
third method: I read the target from the **guard constant that is the actual argument to the write
path** (`guard.RATIFIED_ADR` / `guard.FROZEN_CONTRACT`), not from the filename and not from name
mention.

**The total (25) is CORRECT in T178. Only the SPLIT is wrong.** That distinction matters and I grade
it accordingly: the remediation *population* was right, so **no file went unhardened as a result**.
This is a reporting defect, not a coverage defect.

**Two independent causes, and the second is the one worth carrying forward.**

**(a) The prose contradicts T178's own committed evidence.** `t178-wider-family-output.txt` — T178's
own transcript, committed on the branch — labels `edit22.py` as `contract.go`:

```
.softhouse/reviews/t41-probe/edit22.py   0  False  contract.go  2  0  0  1
```

Counting that transcript gives **20 DEC-1 / 5 contract.go**. The handoff says 21/4. `edit22.py` was
moved into the DEC-1 bucket **when the table was written up as prose** — its `editNN` filename reads
as a member of the `edit2..edit22` ADR series described in the same sentence. I reproduced T178's
classifier verbatim against its own pinned fork-point bytes and got 20/5, never 21/4
(`t181-split-census.py` section B). So the script was right and the sentence was wrong.

**(b) The classifier structurally cannot express "both".** Extracted from
`t178-wider-family.py`:

```python
tgt = GO_REL if (GO_REL in src and ADR_REL not in src) else ADR_REL
```

Single-valued, with the **ADR as the fallback branch**. `edit18.py` and `edit21.py` genuinely write
**both** artefacts — fork-point `edit18.py` calls `patch()` twice:

```python
patch("nexus/internal/apps/loanschedule/contract/contract.go", [ ... ])
patch("docs/adr/DEC-1-schedule-generator-adapter.md", [ ... ])
```

Both are silently recorded as DEC-1 only. The `write sites` column compounds it: it counts **AST write
nodes**, and the single `io.open(path,"w")` inside `patch()` is one node executed twice against two
different paths — so it reports `1`.

**Severity direction.** Both errors push the **same way**: they understate exposure of the
**frozen `contract.go`** (5 or 4 reported, 7 actual) — the higher-severity target, since it carries
**G-3** on top of the contract gate. An under-count of the more protected artefact is the wrong error
to make.

### F-2 — MAJOR (forward-looking). Zero-inspection GREEN in `t178-guard-census.py`. **MICRO-FIXED.**

`t178-guard-census.py` line 232 hard-wires its file set:

```python
files = sorted(glob.glob(os.path.join(SCAN, "t47_edit_*.py")))
```

and line 304 exited on `1 if (reachable or unmeasured or skipped) else 0`. With zero files matched,
every counter is 0 and the script **exits 0 — a confident PASS having inspected nothing.**

This is not hypothetical. **T178's own F-1 instructs the follow-up to point this census at the t41
family** (*"`t178-guard-census.py` and `t178-wider-family.py` are committed and ready to be pointed at
them"*), and **F-3 proposes promoting it to a HARD check in the verifier**. The t41 rewriters are named
`edit*.py`, so the glob matches none of them. Demonstrated against the **unhardened fork-point bytes**,
i.e. the state in which two of those files were live bypasses against the ratified DEC-1
(`t181-census-zero-inspection-output.txt`):

```
UNHARDENED t41 rewriters staged  : 25
of these, LIVE at the fork point : 2  (edit2.py, edit10.py)

   files measured        0
   files UNMEASURED      0
   unguarded + all anchors live (LIVE BYPASS)   0

census exit code                 : 0   <-- GREEN / PASS
```

**P-35: a check inspecting ZERO items is an ERROR, not a pass.** Had T187 followed T178's F-1 and
trusted the exit status, the two live bypasses would have been reported absent. (T187 did not — it
wrote its own census. The trap was laid but not sprung.)

**Micro-fix applied** to `t178-guard-census.py` (6 lines of code + comment; **no measured number
changed**): refuse an empty scan with exit 3 and a message naming the pattern and the directory.
This census is **live tooling slated for the verifier**, not frozen evidence — which is why I fixed it
rather than only raising it (T178 rightly declined to touch T167's superseded census on the opposite
reasoning).

**Driven both ways (P-22 — the fix is not asserted):**

| scan | before fix | after fix |
|---|---|---|
| default `t47-probe` (9 real files) | 9 measured, exit 0 | 9 measured, **exit 0** — unchanged |
| fork-point `t47-probe` (pre-fix bytes) | 1 live + 7 unguarded, exit 1 | 1 live + 7 unguarded, **exit 1** — still able to fail |
| `t41-probe` / any non-matching dir | 0 measured, **exit 0** | 0 measured, **exit 3** |

### F-3 — MINOR (observation, not a contradiction). RED-C input shape.

T178 reports RED-C as **8/8 truncated to 0 bytes**. I measured **1/8**
(`t181-drive-prefix-red-output.txt`). These do **not** conflict — they are **two different input
shapes**, and per P-58 the inputs must be counted before the votes are:

- T178 seeded each scratch target with **the blob that script's edit was written against**, so all
  eight pass their anchor check and reach `io.open(path,"w")` → 8/8 truncate.
- I seeded with **the CURRENT ratified/frozen artefact**, so seven exit 1 at the first dead anchor
  before opening anything; only the live one (`t47_edit_4.py`) reaches the write → 1/8 truncates,
  435,973 bytes → 0.

Both are correct. T178's handoff states its RED-C target, so this is a clarification for the record,
not a defect.

### F-4 — MINOR (reviewer's own tool, recorded because it generalises T183's D-3).

My **first** structural check for the shared-guard idiom scored **0 of 25 files as "one hop"** — i.e.
every file UNGUARDED — because it substring-matched
`os.path.dirname(os.path.abspath(__file__))` while the real idiom wraps that expression **across a
line break**. The files were guarded; **my detector was broken.** Only driving the behaviour caught it.

That is **T183's finding D-3 reproduced accidentally, in the reviewer's own tool**, which is evidence
that D-3 is a **general hazard of single-file guard detection**, not a one-off in T179's classifier.
Re-done on the AST; the corrected check reports 25 of 25. Recorded in the script's own comment.

---

## What I verified and found SOUND (honest negatives — so silence is distinguishable from not looking)

**The guards, driven by me, not by T178's prover.** A reviewer who runs the author's prover has
measured the author's prover. `t181-drive-guards.py` is written from the guard's stated contract and
drives the **real scripts at their real path**. `t181-drive-guards-output.txt`:

```
scripts driven                 : 8
cases run                      : 89
cases NOT AS EXPECTED          : 0
GREEN reproduced AFTER exactly : 8 of 8
BEFORE_SHA256 IS a committed blob: 8 of 8
```

- **C1–C3** no argv / target without token / wrong token → exit 2, 8/8.
- **C4** target = the **REAL** ratified DEC-1 or frozen `contract.go` → exit 2, artefact sha unchanged, 8/8.
- **C5** scratch copy of the **CURRENT** artefact → **exit 3, untouched, 8/8**. This is the control that
  actually closes the bypass, and it is content-based, so it holds under any path, name or tree.
- **C6** any target inside the repo working tree → exit 2, 8/8.
- **C7** `t178_guard.py` absent → **ImportError, exit 1, nothing written, 8/8** — the shared-guard
  idiom **fails closed**, which is the load-bearing risk of factoring the guard out.
- **C8** `.go` suffix refused outright by `t47_edit_7.py` (G-3) → exit 2.
- **G1 (P-50, falsifiable toward the FIX)** legitimate scratch target seeded from the pinned BEFORE
  blob → **exit 0 and the result equals `AFTER_SHA256` exactly, 8/8.** A guard that refuses everything
  is a brick, not a guard; G1 is what separates them.
- **G2** the same GREEN under `python3 -O` → exit 0, 8/8 — no bare `assert` is load-bearing.
- **G3** re-run on the already-edited file → exit 3 (no double edit). **G4** `--dry-run` → exit 0,
  nothing written.

I independently indexed **85** committed versions of the two artefacts and confirmed **all 8**
`BEFORE_SHA256` values are genuine committed blobs — T178's claim, verified rather than accepted.

**The live bypass was real, reproduced from scratch** (`t181-drive-prefix-red.py`):

```
t47_edit_4.py   RED-B current artefact   exit 0   YES   49dc8923 -> cabc2aeb   <<< LIVE GATE BYPASS
t47_edit_4.py   RED-C interrupt at O_TRUNC  -2    YES   435973 bytes -> 0 bytes  <<< TRUNCATED TO ZERO
```

Exit 0, no argv, on a scratch copy of the **current** ratified DEC-1 — matching T178's and the
driver's figures, arrived at through a third harness. The other seven are inert today (exit 1). The
`O_TRUNC` claim is confirmed: the artefact is emptied before a byte of replacement is written.

**The shared-guard idiom holds where T187 extended it** (`t181-drive-t41-idiom.py`), driven with the
**dangerous invocation** — no argv, cwd = repository root, which is exactly how the pre-fix t41
scripts were reachable since they hard-wired a *relative* path:

```
files driven                         : 25
refused with exit 2 (default-deny)   : 25
did NOT refuse                       : 0
reach guard by exactly ONE import hop: 25 of 25
contain an INLINE copy of the guard  : 0
```

`edit2.py`, `edit10.py` (the two formerly live) and `edit18.py`, `edit21.py` (the two-target scripts)
all refuse. Default-deny is safe at repo-root cwd because argv parsing happens **inside `guard.load()`
before the target is resolved or opened** — I confirmed that ordering by reading the guard and by the
artefacts not moving under 25 such invocations.

**The two-target demux is sound.** `edit18.py` / `edit21.py` rewrite `sys.argv` per session and call
`guard.load` / `guard.commit` once per artefact; `_STATE` is per-session and sequential, so there is no
cross-talk. Non-atomicity **across** the two files is documented explicitly in the file rather than
implied, and is fail-closed (a re-run refuses at exit 3).

**T178's own census does NOT have the D-3 defect.** It resolves the delegated guard correctly
(`GUARDED / guard.commit`), reports `files measured 9` and `files UNMEASURED 0` as **values**, and is
**proven able to fail** (fork-point scan → 1 live + 7 unguarded, exit 1). The D-3 misclassification was
T179's classifier and T167's sibling census, which T178 disclosed as F-2.

---

## Attribution — what T178 closed vs what T187 closed

Kept separate deliberately; neither task is credited with the other's work.

- **T178 closed** the **8** `t47-probe` rewriters (`t47_edit_2/3/4/4c/5/6/7/8`). Of these
  **`t47_edit_4.py` was a LIVE gate bypass against the ratified DEC-1**, reproduced by me. That is a
  genuine live closure, and it is T178's.
- **T178 FOUND but did not close** `t41-probe/edit2.py` and `edit10.py` — correctly, its scope guard
  forbade editing that directory — and raised them as F-1. **T187 closed them.** Confirmed from
  `edit2.py`'s own docstring (*"HARDENED BY T187 (21 August 2026)"*) and by my drive (both exit 2).
- **T178's guard module is the shared foundation for both families**: 8 `t47` scripts + 25 `t41`
  scripts = **33 files, one guard, zero inline copies**. `edit2.py` records that it *"REUSES T178's
  shared guard verbatim … introduces no third guard shape"*. That leverage is the strongest thing on
  this branch.
- T178's F-1 **under-reports the population it handed on** (F-1 above) and its recommended tool would
  have reported that population clean (F-2 above). The discovery was right; the handoff instrument was not.

---

## Safety — before / after

| artefact | before | after |
|---|---|---|
| `docs/adr/DEC-1-schedule-generator-adapter.md` | `49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab` | **identical** |
| `nexus/internal/apps/loanschedule/contract/contract.go` | `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` | **identical** |
| vector store (50 `.json`, tree digest) | `5d03795b604294af0f2da3c0df2afbc0d6abe38c3ee47761739fdc80cd4c6120` | **identical** |

The vector tree digest I measured in my own worktree **matches the driver's `main` measurement
exactly**; 50 `.json` files found via `find` (note `ls .softhouse/vectors/*.json` counts only 2 — the
store is nested, and a top-level glob is a false low count).

**No rewriter or promote script was ever executed from the repo root with a repo target.** Every
pre-fix drive ran from a throwaway scratch tree whose shape makes the scripts' own `dirname`-four-times
resolve to that scratch root; every post-fix drive targeted a file in a temp directory. Both artefacts
were re-hashed inside each harness and every run aborts if either moves.

**Go verifier** (repo-local toolchain via `. .softhouse/bin/go-env.sh`, invoked with `bash`):
`go build ./...` exit 0 · `go vet ./...` exit 0 · `gofmt -l .` names **exactly**
`internal/apps/loanschedule/contract/contract.go` — G-3, expected. **Never** `gofmt -w`. No Go file was
touched.

**Tooling provenance (P-33/P-58).** `grep` on this host is a shell function re-execing as **ugrep with
`-I`**; I used **`/usr/bin/grep` (BSD grep 2.6.0-FreeBSD) with `LC_ALL=C` and `-a`** for every text
count, on UTF-8 Python sources. All population and split numbers above come from **Python `ast` /
string membership**, not from any `grep`, precisely so the four-way count dispute is not re-run through
a fifth program.

---

## What I could NOT close

- **The six non-blob `AFTER_SHA256` values.** T178 flags these `[UNVERIFIED]`. I confirm only what my
  G1 measures: each is the deterministic output of the pre-fix script on the pinned BEFORE blob, 8/8
  exactly. I did **not** establish that any of those six states ever existed as a file on T47's disk,
  and I did not reconstruct T47's hand edits.
- **Exhaustiveness of the population.** `t178-wider-family.py` sweeps `.softhouse/` only and misses
  `sed -i`, shell `>`, `shutil.copy` and variable-mode writes — T178 says so. I did **not** re-run a
  whole-repo sweep; I relied on **T183's** (386 Python files / 280 write sites) for exhaustiveness and
  say so rather than implying I re-derived it. My own census covers the 25 t41 rewriters only.
- **T167's `t47_edit_1.py`.** Not re-verified beyond its census row (`GUARDED`, `os.replace`, content
  gate closed); it is out of T178's changed set.
- **No oracle, vector, capture or money arithmetic is involved anywhere in this task.** Nothing here
  bears on parity. I ran no oracle probe, so no oracle-down determination arises.

## Follow-ups raised (not made)

- **T181-A (P1).** Correct the recorded split to **20 DEC-1 / 7 `contract.go` / 2 both, 25 files, 27
  pairs** wherever T178's 21/4 was carried forward. A **number**, so out of micro-fix scope by rule.
- **T181-B (P2).** `t178-wider-family.py`'s `tgt` is single-valued with an ADR fallback and its
  `write sites` column counts AST nodes, not resolved targets. Any future use must emit a **set** of
  targets per file and resolve writes per call site. I did not modify it — it is committed evidence for
  T178's finding, and T178's own precedent (leaving T167's census untouched) applies.
- **T181-C (P2).** Before T178's F-3 is actioned, the census needs a **pattern/family argument**; with
  the micro-fix it now refuses an empty scan loudly instead of passing, but it still cannot *scan* the
  t41 family at all.
- **T181-D (P3).** The general rule behind F-4 and T183's D-3 is worth a `patterns.md` entry:
  *a guard-detector that reads one file textually will score a factored-out guard as UNGUARDED; detect
  on the AST, and always corroborate a structural verdict by driving the behaviour.* (`patterns.md` is
  held by another worker; candidate only.)

## Files authored by this review

All under `.softhouse/reviews/` plus the handoff. `t41-probe/`, `vectors/`, `nexus/`, `docs/adr/`,
`conformance.sh`, `fire-program.sh` and `*promote-vectors.py` untouched.

| file | what it is |
|---|---|
| `t47-probe/t181-split-census.py` + `-output.txt` | independent split re-derivation, and T178's own rule replayed on the fork point |
| `t47-probe/t181-drive-guards.py` + `-output.txt` | 89-case red/green battery against the 8 real scripts |
| `t47-probe/t181-drive-prefix-red.py` + `-output.txt` | pre-fix RED reproduction in scratch (live bypass + `O_TRUNC`) |
| `t47-probe/t181-drive-t41-idiom.py` + `-output.txt` | shared-guard idiom driven across all 25 t41 rewriters |
| `t47-probe/t181-census-zero-inspection.py` + `-output.txt` / `-POSTFIX-output.txt` | F-2 counterfactual, before and after the micro-fix |
| `t47-probe/t178-guard-census.py` | **MICRO-FIX** — empty scan now exits 3 (P-35). No measured number changed. |
