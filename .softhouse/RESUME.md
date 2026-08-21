# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-054355`, 3rd of the day, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **EIGHT WORKERS DISPATCHED, EIGHT COMPLETED, EIGHT MERGED, ZERO LIVE AT EXIT.** No isolation
  violation, no scope breach — every branch's scope verified by the driver with three-dot diffs.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells compared
         invariant violations 0
         CENSUS narrow-catch     57 .java files / 20 dirs (EXCLUDED 1 other checkout root)
         CENSUS wire-float       320 request bodies / 3976 tokens / 6 rigs / 10 req dirs
         no-float census         5 Go packages / 42 Go files / 165 import specs under nexus
go build 0 · go vet 0 · go test 0
gofmt -l names exactly contract.go — EXPECTED under G-3
DEC-1 49dc8923… and contract.go 0db73d4a… UNMOVED before, during and after every merge
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all eight**: `T173`, `T175`, `T177`, `T178`, `T179` (batch 1), `T170`, `T171`,
`T172` (batch 2).

---

# THE HEADLINE: T177 settled the StackOverflowError, and it was never about the inputs

**107 trials of the disputed cell (B=10001, n=3000) across 75 fresh JVMs.**

| condition | JVMs | observed | threw |
|---|---|---|---|
| cold start (JVM's first seam call, default `-Xss`) | **33** | **0** | **33** |
| attempts 1–4 inside one JVM | 7 each | 0 | 7 each |
| **attempt 5 and later** | **7** | **7** | **0** |

A step function, `XXXXoooo` in 7 of 7 JVMs, never reversing in 107 trials. It moves with `-Xss`
(8m and 16m are observed) and **never happens at all** under `-XX:TieredStopAtLevel=1`.

**Consequences, each of which invalidates something the record asserted:**

1. **T159 and T169 never disagreed about the oracle.** Replaying T159's committed case list in its
   committed order reproduces T159 cell-for-cell.
2. **"The throwing region" is not a region of the input space.** Any probe mapping a boundary by
   asking each cell ONCE is measuring its own warm-up curve. G-8's "not monotone in n" premise is
   **refuted**, not merely imprecise.
3. **`errorStackDepthTotal: 1024` everywhere in this program is HotSpot's recording cap, not a
   depth.** True depth at overflow rises 5119 → 4683 → 4683 → 8400 within one JVM.
4. **T177 corrected the driver's own task brief.** The disputed cell is **not** the cell behind
   G-8's MNT 10.01 headline — that is **B = 1001**, probed directly: **9 cold starts, 9
   observations, `15010.01` every time. The headline is cold-safe.**

## THE SECOND HEADLINE: the driver's merge caught two defects no branch could show

T173 drove its guards red and green and ran the full harness on a **scratch merge** — all green. The
driver re-ran the *identical* harness on **real merged `main`**: **exit 2, and NO probe line.** Per the
standing rule that is a **HARD-guard failure, not an oracle outage** — nothing was parked.

- **Defect A** — the narrow-catch lint walked `.claude/worktrees/`: **43 other checkouts of this repo**,
  1954 `.java` files, **2292 refusals, all 2292 outside this commit's own content**. A scratch tree
  cannot show this, because it has no `.claude/worktrees/` — **the property that makes a scratch tree
  clean is what hides a whole-repo walk's scope defect.** → **P-56**. Census 1954/622 → **57/20**.
- **Defect B** — the census-presence check **inverted itself**. `CENSUS` is the *first* line printed, so
  `grep -q` exited immediately, `printf` took **EPIPE**, and `set -o pipefail` flipped the test to
  "printed NO CENSUS LINE" **when the line was line 1**. Harmless at 36 KB, wrong at 320 KB — the
  anti-silent-guard machinery failed **precisely when a guard had a lot to say**. → **P-57**.

Both fixed in `e93afc9`, both driven red **and** green. **Raised as `T188` so the driver's own fix is
independently reviewed** — a driver fix is not exempt.

## THE NEXT FIRE STARTS HERE

1. **`T187` — A LIVE GATE BYPASS, AND BIGGER THAN T178 WAS.** T178 hardened 8 rewriters; the
   population is **27, not 9**. `.softhouse/reviews/t41-probe/` holds **21 more** that open the
   ratified DEC-1 at a *relative* path with `io.open(P,"w")` (`O_TRUNC` — the ADR is emptied before a
   byte is written), and **exactly one of the 29 files there contains any guard node at all**.
   **Two are LIVE today**: the driver re-ran the anchor test read-only, **without executing
   anything**, and `edit2.py`'s and `edit10.py`'s anchors each occur **exactly once** in the current
   ADR — which is the only precondition either script checks, and neither takes argv.
   **Three independent counts disagree (T178 21+4, driver 21, T179 17+5) — state your rule and
   re-derive; inherit none of them.**
2. **`T188`** — review the driver's own merge fix. Specifically: the exclusion predicate compares
   `relpath(full, root)` to the literal `.claude/worktrees` — **what happens when `root` is itself
   inside a worktree, which is the normal case for every worker?** And sweep `conformance.sh` for
   other `| grep -q` / `| head` shapes under `pipefail` (the driver fixed only the one that bit it).
3. **`T189`** — the grep dispute is **NOT settled** and the record must not say it is. Two positives
   (T157, a previous driver) versus two negatives (T171's own 6×18 sweep, and this driver's).
   Driver-measured: invalid UTF-8 suppresses **nothing** in three locales, seekable or piped; a real
   **NUL** yields `Binary file … matches` with lines suppressed — **a third mode, `DIRTY` non-empty
   but carrying a message instead of paths.** `grep` also resolves to a **shell function wrapper** on
   this host and `ugrep` is not on `PATH`, so the four attempts may not have invoked the same binary.
4. **`T186`** — money on the capture wire in major-unit decimal (11 `req` bodies at
   `"principal": 1162502.5`, driver-confirmed; 38 files across the whole capture tree).
5. Then `T165`, `T174`, `T176`, `T180`, `T160`, `T164`, `T162`, `T168`, `T145`, and the five paired
   reviewers `T181`–`T185`. `T116` stays parked behind T177's finding, which **re-scopes it**: promote
   only from a stated JVM state (cold-start-per-cell recommended).

---

## Four workers corrected the layer above them, and two corrected themselves

- **`T177` corrected the driver's brief** — the disputed cell is not the headline cell, and it probed
  the real one rather than answering the question as asked.
- **`T178` found its own brief was too small** — 9 became 27, driver-corroborated read-only.
- **`T175` disagreed with T169's census on both numbers** — 29 sites / 5 load-bearing, not 11 / 2 —
  because T169's net was `except Exception`/bare `except` only and every narrow-clause swallow was
  invisible to it. It also found the t44 defect had silently swallowed **18 real committed files**,
  not merely a planted one.
- **`T171` reported a NEGATIVE that undercut its own task** — it could not reproduce the bug it was
  sent to write up, said so, and the driver's own measurement agreed with it.
- **`T170` caught an overstatement it had introduced itself**, in its own re-read, and recorded it.
- **`T179` found T156's sweep had scored ITSELF** as a guarded mutator of the vector store, on its own
  regex literals and print strings, while performing zero mutations.

## STANDING INSTRUCTIONS

- **Test the merge WHERE IT RUNS, not in a scratch tree (P-56, NEW).** A scratch worktree's cleanliness
  is exactly what hides a whole-repo walk's scope defect. Both of this fire's merge defects were green
  in the scratch merge and red on real `main`.
- **Under `pipefail`, never `| grep -q` or `| head` (P-57, NEW).** The early-exiting consumer poisons
  the pipeline status via EPIPE. Use `grep -c` and test the count. **Size a red probe from the real
  artefact** — 36 KB fits the pipe buffer and "proves" the bug absent.
- **`git diff main...branch` — THREE DOTS, always (P-41).** `main` moved **eight times** under workers
  this fire. **`/softhouse` SKILL.md STEP 5 says two dots and is WRONG.**
- **The Go module root is `nexus/`, NOT the repo root**; `. .softhouse/bin/go-env.sh` first, **from the
  repo root**; never pipe a build into `head`/`tail`.
- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's refusal. The
  oracle-down condition is exit 2 **AND a probe line actually PRINTED AND reading `down`** — test for
  the line's **presence** first. **This fire hit exit 2 with no probe line and correctly parked
  nothing.**
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED (P-22)**, and **a prover must be falsifiable toward the FIX,
  not only toward the defect (P-50)**.
- **Detect code with a parser, not a regex (P-48).** **A version string is not provenance** (P-55).
- **A quoted excerpt is a claim (P-46).** Quote by extraction, never by retyping.

## What is NOT true, and must not be inferred from the green bar

**The A2 ledger port is still graded by NO parity vector.** The 43 vectors are `loanschedule`'s. What
this fire added is that the capture rigs can no longer hide a wire-side float or a narrowed seam
handler, and that the guards now run on the path that executes — **not** that ledger behaviour has been
proven against the reference oracle. `G-10` remains OPEN. **`gates.md` still has TWO `## G-8`
headings** (both predate T170; the NOTICE block is marked SUPERSEDED but not yet merged into the
rebuilt section).
