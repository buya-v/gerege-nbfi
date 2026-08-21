# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-054355`, 2nd of the day, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **SEVEN WORKERS DISPATCHED, SEVEN COMPLETED, ZERO LIVE AT EXIT.** No isolation violation, no scope
  breach — every branch's scope verified by the driver with three-dot diffs, not taken from a report.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells graded, 87 ungraded
         contract-refusal 4 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0
         no-float census 5 Go packages / 42 Go files / 83505 tokens / 165 import specs
                         under nexus (RECURSIVE, WHOLE MODULE) — was 24 files under loanschedule
go1.26.6 (repo-local, `. .softhouse/bin/go-env.sh`): build 0 · vet 0 · test ok (incl. ledger)
gofmt -l names exactly contract.go — EXPECTED under G-3
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all seven**: `T157`, `T166`, `A2-12` (carrying `A2-8`), `T169`, `T163`, `T167`, `T161`.

---

# THE HEADLINE: the first non-negotiable in CLAUDE.md was enforced on ONE HARD-CODED SUBTREE, and the A2 ledger port sat entirely outside it

**Driver-measured, in a scratch worktree, before anything was merged.** With a `float64` money path planted
in `nexus/internal/apps/ledger/sub/` **and** an aliased-math float in `ledger/`:

```
main + A2-12, no T166 :  EXIT 0 · VERDICT: PASS · census line BYTE-IDENTICAL to baseline
                         ("24 Go files ... under nexus/internal/apps/loanschedule")
```

The harness passed **7,018 lines of new money code by never looking at them**, and the count was unchanged
*precisely because it never looked*. After T166 the same plants are refused, exit 2, named at
`file:line:col`, and the census reads **5 packages / 42 files / 165 import specs, recursive**.

**T166 also found a second hole INSIDE the tree that WAS guarded**, and the driver reproduced it: an
aliased `import m "math"` with `int64(m.Sqrt(m.Pi))` names no forbidden identifier and contains no float
literal, so it passed both existing arms from a directory the old guard *did* walk. Closed by banning the
`math` **package** via `go/parser` in ImportsOnly mode — not a list of its function names, because `Abs`
and `Rounding*` already appear 3 and 140 times as legitimate integer identifiers. `math/bits` and
`math/big` remain permitted.

## THE NEXT FIRE STARTS HERE

1. **`T178` — TREAT AS AN INCIDENT, NOT A CHORE.** `t47_edit_4.py`'s anchors are **LIVE in the ratified
   DEC-1 today**. The driver copied the current ADR to scratch, repointed the script, ran it: **exit 0,
   `edit4: ok`, sha256 `49dc8923…` → `cabc2aeb…`**. Running it in the repo silently rewrites a ratified
   DEC-n — a **hard user gate** — with no gate, no trap, no atomicity. `t47_edit_7.py` targets the frozen
   `contract.go`. Eight siblings total; do `edit_4` first.
2. **`T177`** — the oracle's `StackOverflowError` is **not a function of the cell's inputs alone**:
   `(B=10001, n=3000)` threw for T169 and was observed **cleanly** by T159, same pinned image. **This
   blocks sensible design of `T116` and G-8 option (a)** — a probe that asks each cell ONCE is measuring
   noise, not a boundary, and a vector promoted from an intermittently-throwing cell is not reproducible.
3. **`T170`** — G-8's write-up is wrong in ~25 places and Buyan reads it. `T169` is now done, so it is
   unblocked; fold in T177's finding before writing the third-outcome sentence.
4. **`T179`** — replace T156's regex guard-classifier with a parser-based check. It scored an unguarded
   rewriter of a ratified ADR as "guarded" **by the prose that file was writing**, and the same pattern
   text returns 3 matches in Python `re` and 0 in POSIX ERE.
5. **`T173`** (T163's and T169's new guards are wired into nothing automatic — P-45), then `T175`, `T171`,
   `T165`, `T160`, `T180`, `T174`, `T176`, `T172`, `T162`, `T168`, `T145`. `T116` stays parked behind T177.

---

## Four times a worker corrected the layer above it — this is the system working

- **`A2-12` overturned its own reviewer.** A2-9 measured the `ApplicableSlotName` defect at **3 of 48**;
  it is **6 of 96**. A2-9 swept only the loan entry point; the working-capital-loan path carries the
  **mirror-image** bug (an *accrual* caller getting the *cash* name at 22/24/25). **The driver re-ran the
  red probe itself** — restored only `resolve.go` from A2-8's bytes, kept A2-12's test, watched it fail
  with 13 assertion lines naming all six.
- **`T163` showed A2-11's committed prover EXITS 0 AGAINST THE DEFECTIVE SCRIPT** — driver-reproduced on
  main: `FAILURES: 0`, exit 0, assertions phrased *"PASS RED: resolve7.py accepts every one of them"*.
  They pass **because the bug is present**. → **P-50**.
- **`T157` showed T154's committed "fail-closed" claim is backwards** — it is fail-**open**. Driver
  reproduced it on a **second** grep implementation (ugrep 7.5.0 vs the worker's BSD grep), so it is
  binary-detection behaviour, not a vendor quirk. Reachability is an honest **measured negative**.
- **`T169` showed `0 errored` was UNFALSIFIABLE** across the program's entire history, by two independent
  routes. It then **refused to adjust the number**: T117's `287/287/0 errored` is *true about the run*;
  what is unsupported is the **inference** that the sweep covers its region. → **P-51**.

## Two workers found defects in their OWN instruments and reported them

- **`T161`**: its `sleep 5` trigger fired before the window opens at **12.34 s**, so **both arms reported
  "RIG INTACT" and proved nothing**. Now polls until the digest actually changes.
- **`T163`**: sabotage 4 of its own census found a hole in its own fix (R5 scoped only to classified wire
  writers) — recorded and closed rather than quietly patched.

## The driver's own error, recorded

The driver planted a 35th capture rig at T169's new lint; it was not flagged, which looked exactly like a
vacuous guard. **It was the driver's probe that was wrong** — the catch did not wrap a seam marker, and the
lint's own selftest case (c) deliberately asserts it must not be over-broad. Replanted correctly: refused,
exit 1, named at `file:line`. → **P-52**. Also: a final conformance run returned **exit 127** because the
driver launched it with the shell's cwd left in `nexus/`. 127 is "command not found", not a verdict; re-run
from the repo root it is exit 0.

## STANDING INSTRUCTIONS

- **Test the MERGE, not the branches (P-49, NEW).** T166 and A2-12 were each individually correct and
  individually green; merged they were a permanent HARD-guard failure, because A2-8's own float scanner
  writes its forbidden table with the spellings **unsplit** and T166's worktree never contained the ledger
  tree it was about to start guarding. **A guard's blast radius is not visible in the guard's own diff.**
- **`git diff main...branch` — THREE DOTS, always (P-41).** `main` moved **seven times** under workers this
  fire. **`/softhouse` SKILL.md STEP 5 says two dots and is WRONG.**
- **The Go module root is `nexus/`, NOT the repo root**, and **never pipe a build into `head`/`tail`** —
  you will read the pager's exit code, not the compiler's. The driver did exactly this again this fire.
  `. .softhouse/bin/go-env.sh` first, **from the repo root**.
- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's **refusal**. The
  oracle-down condition is exit 2 **AND a probe line actually PRINTED AND reading `down`** — test for the
  line's **presence** first.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED (P-22)** — and **a prover must be falsifiable toward the FIX, not
  only toward the defect (P-50)**. Assert internally that pre-fix goes RED *and* post-fix goes GREEN.
- **Before calling a guard broken because it ignored your probe, read its selftest (P-52).**
- **Detect code with a parser, not a regex (P-48).** Three separate instances this fire.
- **A quoted capture excerpt is a claim (P-46).** Quote by extraction, never by retyping.
- **Parity with an oracle bug beats a local improvement (P-47).**
- **An obligation is not a proof.** Where `obligations.md` says *Ungraded*, nothing catches the thing.

## What is NOT true, and must not be inferred from the green bar

**The A2 ledger port is graded by NO parity vector.** The 43 vectors are `loanschedule`'s. What changed
this fire is that the ledger tree **can no longer hide a float** — not that its behaviour has been proven
against the reference oracle. `G-10` is OPEN (the oracle serves product mappings whose GL account was
retyped underneath them and will not re-create them; the read-back structurally cannot reveal it).
