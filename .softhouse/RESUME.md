# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-134344`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **Seven workers dispatched, seven completed, ZERO LIVE AT EXIT.** No isolation violation, no scope breach —
  every branch's scope verified by the driver with three-dot diffs, not taken from a worker's report.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells graded, 87 ungraded
         contract-refusal 4 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0
         no-float census 24 Go files / 56295 tokens
go1.26.6 (repo-local, `. .softhouse/bin/go-env.sh`): build 0 · vet 0 · test ok
gofmt -l names exactly contract.go — EXPECTED under G-3
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire**: `A2-11`, `T154`, `T155`, `T156`, `T158`, `T117`, `T159`, `A2-9`.
**Held unmerged**: `A2-8` — the A2 port. See below; the reason is a precondition, not a defect.

---

# THE HEADLINE: the money non-negotiable is now genuinely enforced on `loanschedule` — and demonstrably NOT on the new ledger package

`T154`'s three guard legs had been sitting unmerged since last fire because they are money-path guard code
and their reviewer had not run. **`T155` ran, drove every single guard RED with its own poison written before
opening a single T154 fixture, and found two real defects** — one *introduced* by T154 and sharper than
T154's own self-criticism. The driver applied both and **drove them red itself**. That work is now on `main`.

**And in the same fire, `A2-9` proved the same guarantee does not extend to the code A2-8 just wrote.**

## THE NEXT FIRE STARTS HERE

1. **`T166` — DO THIS FIRST. It is the only thing between 6,065 lines of new money code and `main`.**
   Driver-verified at three sites: `conformance.sh:573` and `nofloat.go:62` (`LoanScheduleTreeRel`) and
   `guard_gofmt` at `:602` all scan **`internal/apps/loanschedule` only**. **A2-9 then measured a SECOND
   level**: A2-8's own in-package scans use `ReadDir(".")` and **skip directories** — it planted a `float64`
   in `ledger/sub/` and it passed the package test **and** `conformance.sh`. **So the red probe MUST be
   driven from a SUBDIRECTORY**; a fix that merely widens the top-level path list still passes A2-9's plant.
   Do **not** just add `ledger` as a second hard-coded path — that reproduces the defect for the next package.
2. **Then `A2-8`.** Apply A2-9's four non-money corrections to `softhouse/A2-8-ledger-port`, then merge:
   **F-A** `ApplicableSlotName` is **inert** (`resolveProductAccount` discards the typed slot, so
   `applicable == rendered` unconditionally — on a *cash* product at 22/24/25 it reports the *accrual* name,
   and no test reads it); **F-B** `glaccount.go:251-254` claims SQL `SUBSTRING` with negative length yields
   `''` — **PostgreSQL raises**, A2-9 ran it live, and the claim sits under a `[VERIFIED:]` marker;
   **F-C** a `[VERIFIED:]` count of 27 that measures **52**; **F-D** a correction misattributed to `f50e006`
   when it was already complete in `5d80a72`.
3. **`T170` — G-8's write-up is wrong in at least 25 places and Buyan reads it.** Depends on `T169`.
4. **`T169`** — the shared rig catches `RuntimeException`, not `Throwable`. This reaches **backwards** into
   committed evidence: four rigs inherit it, so some published "0 errored" claims may be unsupported.
5. Then: `T160` (deflation manifest), `T161` (the prover that corrupts the live rig), `T165`, `T167`, `T157`,
   `T163`/`T164`, `T168`, `T162`. `T116` is deliberately parked until the store-count work settles.

---

## G-8: the headline DOUBLED, and it is still not a bound

`T117` measured the failing principal at **MNT 5.01** and — correctly — **warned that it was the largest
OBSERVED, not a bound**, because nobody had ever asked above n = 1000. **`T159` asked. The residual doubled:
MNT 10.01 at n = 3000**, 3000 rows of `principal "0.00"`, balance frozen 2024→2274, MNT 15,010.01 of
scheduled interest, `totalPrincipalAmount 0.00`. **And n = 3000 is simply the largest term T159 asked.**

> **Any disclosure must state the residual WITH ITS TERM and still call it the largest OBSERVED.** Two
> independent workers have now raised the ceiling by asking a larger question and neither found a limit.

**THE REFERENCE ORACLE THROWS**, and nothing in the record says so: `java.lang.StackOverflowError` from
`ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI` recursing at `:1214` — **non-monotone**
(`B=10001, n=2000` dies; `n=3000` succeeds). **G-8 has no sentence for a third outcome in which no schedule
is produced**, and option (b) amends the graded domain, so it cannot be drafted without one.

## Four times a worker overturned the driver — this is the system working

- **`A2-11` found a FABRICATED capture excerpt in ALREADY-MERGED evidence.** A2-7's handoff quoted three keys
  as `null` from capture `A2-211`; those keys occur **0** times in that file and the literal string `null`
  occurs **0** times in it. A false rule was built on the invention, and **A2-8 was consuming it live**.
  Driver verified against raw bytes, corrected A2-8 mid-flight, struck the block. → **P-46**.
- **`A2-8` refused half a driver instruction.** The driver said to make missing-slot rendering "pick the
  family that actually applies"; that diverges from the oracle on an **observable string**. A2-8 declined and
  said so. A2-9 adjudicated it right — byte-identical to the oracle, reproducing even its missing space in
  `"with Id %dmaps to"`. → **P-47**.
- **`T155` found a defect in its OWN rig** (`FindRepoRoot(".")` resolves the graded root from the caller's
  CWD, so it was grading its worktree while the shell guards printed the scratch tree's paths) and **reported
  it** instead of quietly fixing it. → `T165`.
- **`T159` corrected the driver's own brief** (13 principals listed while claiming 14).

## STANDING INSTRUCTIONS

- **`git diff main...branch` — THREE DOTS, always (P-41).** `main` moved *five times* under workers this fire.
  **`/softhouse` SKILL.md STEP 5 says two dots and is WRONG.**
- **The Go module root is `nexus/`, NOT the repo root**, and **never pipe a build into `head`** — the driver
  did exactly this and read `head`'s exit code as the compiler's. `. .softhouse/bin/go-env.sh` first.
- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's **refusal**. The
  oracle-down condition is exit 2 **AND a probe line actually PRINTED AND reading `down`** — test for the
  line's **presence** first. **Exit 2 with the probe reading `up` happens** — the driver produced exactly
  that case this fire while driving D-1 red, and it means the corpus or a HARD guard is at fault.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED (P-22)** — six instances now, three of them inside a task sent to
  fix a previous one.
- **Detect code with a parser, not a regex (P-48).** Twice this fire a guard was kept green by prose in the
  file it was scanning — including prose the file was *writing into a ratified ADR*.
- **A quoted capture excerpt is a claim (P-46).** Quote by extraction, never by retyping, and `grep` the
  quoted strings against the artefact. *Prose gets argued with, numbers get re-derived, quotations get believed.*
- **Parity with an oracle bug beats a local improvement (P-47).**
- **An obligation is not a proof.** Where `obligations.md` says *Ungraded*, nothing catches the thing.
