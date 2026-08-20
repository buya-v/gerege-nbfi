---
name: softhouse-uat
description: Verifies the Gerege NBFI migration by building and testing the Go module and running the golden-vector conformance harness against the live Fineract oracle — HARD checks that must be zero (float in money paths, direct balance writes, broken double-entry) and conformance parity that must hold. Use when the user runs /softhouse-uat, asks to run UAT or acceptance checks, or wants to confirm a migration change did not regress parity with Fineract.
---

# /softhouse-uat — migration verification (Gerege NBFI variant)

**Project-scoped; overrides any global `softhouse-uat` inside this repository.**

The generic skill smoke-tests a running web system. Here, UAT means: **does the ported Go code build, pass its tests, and reproduce Fineract's behavior to the defined tolerance — with the ledger invariants intact?**

## Usage
- `/softhouse-uat` — run all checks
- `/softhouse-uat build` — build + unit tests only
- `/softhouse-uat conformance` — golden-vector parity vs the Fineract oracle only
- `/softhouse-uat hard` — the grepable HARD non-negotiable checks only

## What it runs

```bash
go build ./...
go test ./...
bash .softhouse/conformance.sh   # replays golden vectors through the Go module and diffs vs Fineract-captured expected outputs
```

Exit 0 = PASS, 1 = FAIL, 2 = could not run (e.g. oracle unreachable),
**3 = wrong interpreter — the harness never started.** Run it with `bash` (or
`./.softhouse/conformance.sh`).

The guard tests a **capability, never a shell's name**: before anything else the
harness must *observe* a token come back through `< <(…)`, the construct it is
built on. Anything that cannot deliver that token is refused up front with exit 3
— a shell that is not bash (`dash`, `zsh`, `ksh`, busybox `ash`), a bash with
process substitution switched off (bash 3.2 in POSIX mode, which is what **both**
`sh conformance.sh` and `bash --posix conformance.sh` give you on macOS), and a
restricted `bash -r`, which stops the probe from running at all. Where `/bin/sh`
**is** a bash 5.x — Fedora, RHEL, and any distro that links `sh` to bash —
`sh conformance.sh` is **admitted** and works, so "`sh` is refused" is not the
rule; "this shell could not be seen to do process substitution" is
[VERIFIED: T97 — bash 5.2.37 / 5.3.9 admitted plain, under `--posix`, and with
`argv[0]=sh`; bash 3.2.57 as `/bin/sh` refused; `bash -r` refused].

Exit 3 is **not** a verdict and **not** an oracle outage: nothing was graded and
the oracle was never contacted. Re-invoke under bash and grade again — never park
a task on it. Full table: `.softhouse/vectors/README.md`.

### HARD checks — must be zero

| Check | Why |
|---|---|
| `float` / `float64` / `double` / decimal-float in any money path | Money is integer minor units. Any float in a monetary calculation — including intermediate — is a correctness defect. |
| Direct write/UPDATE to a `balance` column | Balances are DERIVED from the append-only ledger, never written. |
| `UPDATE`/`DELETE` of a posted ledger entry | The ledger is append-only; corrections are reversing entries. |
| Hold that mutates `balance` (not `available`) | A hold must reduce available only; mutating posted balance is the exact defect that failed review twice on the sister project. |
| Money-movement POST without an `Idempotency-Key` | Mandatory on every money-movement endpoint. |

A HARD hit is a failure regardless of context. If a hit is a genuine false positive, **fix the checker's pattern** — never add an exception to make a failure disappear.

### Conformance checks — parity must hold

The golden-vector run replays each captured Fineract scenario (schedules, postings, EOD balances, provisioning) through the Go module and diffs the outputs to the defined rounding tolerance. **Every vector for a context already cut over must pass.** For a context still in shadow, report the diff count as the parity signal — it must trend to zero before that context can be proposed for cutover (a `user` gate).

### Property invariants — must hold

Double-entry always balances; principal amortizes to exactly zero; split amounts sum to the whole; no impossible negatives. These are checked by `go test` property tests and must pass.

## Steps
1. **Pre-flight** — confirm the Go module builds and the Fineract oracle is reachable (conformance needs it). If the oracle is down, `conformance` reports exit 2, not a false PASS.
2. **Run** the requested checks.
3. **Report** — per-check pass/fail with counts; for conformance, the per-context parity (pass / total vectors, diff count vs last run).
4. **On failure** — name the specific package/vector. Do not auto-weaken a test to pass. A HARD failure usually means a money-path defect; a conformance failure means the Go behavior diverges from Fineract — both are real.

## Limits — read before trusting a PASS

The HARD checks grep text: they prove certain wrong things are **absent**, not that the code is **correct**. Conformance proves parity **only for the scenarios the vectors cover** — an uncovered edge case can still be wrong. Neither catches a subtle money-math error the independent `reviewer` would (by re-derivation). **A PASS here means "builds, tests green, known-bad patterns absent, and matches Fineract on the captured vectors" — not "provably correct for all inputs," and never "safe to cut over."** Cutover is a separate `user` gate requiring a clean shadow-parity window and regulatory sign-off.
