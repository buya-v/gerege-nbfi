# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260819-140003`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17 · **`tier0-harness-schedule-poc` is `active` again (was `blocked_on_gate`)**
- **Oracle**: UP all fire. `fineract:latest` + `postgres:18.3`, both healthy, **never restarted**. Pinned
  checkout `426a23544` clean throughout. PostgreSQL only; no prohibited engine anywhere.
- **Seven workers dispatched, SEVEN completed**, merged and verified. No worker lost, no isolation
  violation, no scope breach.

## THE HEADLINE: **DEC-1 REVISION 12 IS RATIFIED. G-1 IS CLOSED. It never reached Buyan.**

Ten independent rounds ran. The driver declined at revisions 8 and 10 on one consistent discriminator —
*a sentence known to be false was about to be frozen* — and both times the next revision proved the
sentence really was wrong. It ratified at revision 12 because **no known false sentence remains**.

**No round returned a bare CLEAN and the record does not claim one did.** T53 returned **no P0 and no P1**
with six P2 documentation-accuracy errata and *"apply the six, then ratify"*; T54 applied them; the driver
verified each mechanically. Full record in `docs/adr/DEC-1-schedule-generator-adapter.md` § *Ratification
record* and `.softhouse/gates.md` § *G-1 CLOSED*.

**Guardrails, each reproduced by the driver rather than taken on report:**
- **§3.1 and §4.1 byte-identical across revisions 10, 11 and 12** — sha256 `42b978e2abb9` / `b88faca50f22`.
  Those sections *are* the graded domain and the rounding decision, so this proves **no predicate moved**.
- **`contract.go` non-comment body byte-identical** — sha256 `2530f13ecad961f2` over 96 lines.
- **0 out-of-range citations**, sustained across T49 (155 distinct), T52 (171), T53 (47 added), T54 (24).

### What ratification does NOT mean
Not that `contract.go` **compiles** (see the toolchain gap below), not parity, not promotion of any vector,
not a cutover. `DayCountActualActual` is still refused with `ErrNoDiscriminatingVector`. **Buyan retains
veto and may reverse the ratification.**

## THE ONE THING THE NEXT FIRE SHOULD DO FIRST

**T7 — the golden-vector conformance harness + vector store.** It is unblocked for the first time in the
program and **T9–T15 all sit behind it**. Two constraints its author must not discover late:

1. **Charge conformance can only ever be graded on Path B.** `ProgressiveLoanScheduleGenerator.java:81`
   calls `generate(mc, loanApplicationTerms, null, null)` — `loanCharges` is **hard-wired `null`**, so the
   Path A embeddable seam is structurally blind to every charge (T50-N2, driver-verified by reading the line).
2. **NO GO TOOLCHAIN EXISTS ON THIS HOST** (below). The harness can be *designed*, and the corpus can now be
   *promoted*, but nothing can be *executed against Go* until a toolchain is installed.

**Promotion is now unblocked and is the highest-value oracle-free work available.** Until this fire the
corpus had to stay in raw observed form because *the shape was what was being ratified*. The shape is now
ratified, so raw captures can become promoted golden vectors — subject to T48-N4's trap (see below).

## BLOCKING ENVIRONMENT GAP — no Go toolchain

`go` is not on `PATH` and no Go installation exists on this host [VERIFIED by the driver this fire].
`nexus/internal/apps/loanschedule/contract/contract.go` holds **96 non-comment lines** of real Go and **has
never been compiled**; ten review rounds graded its comments and its shape, never whether it builds. A static
check found all three imports used and no duplicate top-level declarations — a heuristic, not a compile.

This blocks **T10** (the port), **T11**, **T13** (`/softhouse-uat`: `go build ./...`, `go test ./...`) and the
executable half of **T7**. A UAT that cannot run must **never** be recorded as a pass.

**It is not a RESERVED item** — no money, no endpoint, no third party. It was deliberately not done
unattended because installing software is a durable change to Buyan's machine rather than to this repo.
**Details and the fix in `.softhouse/reference-oracle.md`. A fire told "you may install a Go toolchain"
should just do it and record the version there.**

## What this fire established (all raw observed; PROMOTION now possible but NOTHING promoted yet)

| result | evidence |
|---|---|
| **N46-1 CONFIRMED BY OBSERVATION** — the **ambient** mode governs charge rounding, after two fires stuck at `TO_BE_CAPTURED` | 7/7 threaded columns move with the ambient mode, **0/7** ambient rows with the threaded one; confirmed twice independently (2,016 transcription cells + 1,400 reflection cells); **reachable at MNT scale — `1005025.12` vs `1005025.13`** |
| **The recorded blocker was REFUTED** | T46 and T48 both wrote "needs a tenant write"; `LoanScheduleAssembler:753` reads `getMathContext()` and `:765` threads **that same cached reference**, so a tenant write moves both axes together. **The experiment two fires waited for could never have worked** |
| **N46-3 CONFIRMED** | `percentageOf(x, p, 19)` takes the ambient mode 7/7; the `MathContext` overload the threaded one 7/7 |
| **The alias CROSSES CONFIGURATION SCOPES** | the value is a **tenant-global configuration** [`LoanScheduleAssembler.java:370-371`], not a product setting — **a port cannot fix it by wiring "the other product field"** |
| **Slot LIVE, setting INERT — two results that must not be collapsed** | both readers move money (79/153 and 52/164 cells); the product setting moves **0** cells across 8 shapes on products matched on 20 SQL columns; oracle matches **31 December** 6 of 6 |
| **The tenant-global flag is `false` on `gerege`** | T53, read-only `SELECT`; `ConfigurationDomainServiceJpa:296-300`. **So the alias has never been witnessed delivering a wrong value, and cannot be on this tenant** |
| **`chargeCalculationType` 5 separated — T48's premise was wrong twice** | a real tranche product is byte-identical to type 2 (**0 of 302 cells**); `LoanChargeAssembler:190-204` builds one charge per tranche so `Σ p·tᵢ = p·Σtᵢ`. **Linearity hid it, not the absence of tranches.** Breaks on tranches summing below principal (`12,345.00` vs `14,814.00`) and on `minCap`/`maxCap` |
| **`fixedLength` blocker found** | HTTP 403 *"only allowed for zero interest products"* [`LoanProductDataValidator.java:2784-2787`], `thereIsInterest` from the **request** — no product needed; moves exactly 3 cells at zero interest |

## Open findings the next reader must not lose

- **T50-N2 (P1)** — the Path A seam **can never exercise a charge**. Governs T7's design. Driver-verified.
- **T50-N1 (P1)** — `LoanApplicationTerms` computes the **down payment two different ways**: the Builder
  constructor threads `builder.mc` [`:329-338`]; the other constructor is **fully ambient** [`:862-869`].
  `LoanScheduleAssembler:548` takes the **ambient** one, Path A the **threaded** one. Driver re-derived.
- **A latent oracle defect is an ACTIVE port defect.** On the shipped server ambient and threaded are the
  *same object*, so Fineract is never wrong here. **It goes live the moment a port threads a context — the
  natural Go idiom.**
- **T48-N4's promotion trap** — the ACT/ACT arm **coincides exactly** with the plain branch when both years
  are 365, so a cross-year vector inside a run of non-leap years grades the arm **not at all**. Any promoted
  vector for it **must cross a leap boundary with a non-zero first segment.**
- **Tier B trap** — `(19, tenant mode)` is a **loan-path** rule. Savings/deposits use `DECIMAL64` and
  `MathContext(15|10, …)`; one precision-8 site is in **share accounts**.
- **N46-3's other five literal-19 `percentageOf` sites** — `[VERIFIED as grep]`, `[UNVERIFIED as behaviour]`.
- **`contract.go:1229`'s citation anchor** was fixed by the driver **before** the freeze. Any further
  `contract.go` change now needs a **gate**.

## Task state

| Task | State |
|---|---|
| T1, T3, T3b, T4, T5, **T6**, T16–T19, T21–T24, T26–T54 | **done** (43 of 54) |
| T25 | done_partial (oracle-free slice) |
| T2 | **parked** — unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| **T7** | pending — **THE BOTTLENECK**, now unblocked; T9–T15 behind it |
| T9–T15, T20 | pending |
| T8 | in_progress — captures taken, **no vector promoted** (promotion is now permitted) |

## Open decisions for Buyan

- **None blocking.** G-1 is closed; only **G-2** remains pending and it parks one task, not the program.
- **May I install a Go toolchain on this Mac?** Not reserved, but it is a durable change to your machine, so
  no fire has made one unattended. **Nothing compiles until it exists.**
- **The ratification is reversible.** The driver ratified DEC-1 revision 12 under P-2. If you would rather it
  had waited for a literal CLEAN round, say so and it can be un-ratified.
- **RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
  facts. None is in Run 1's path.

## Stranded-branch triage — CLOSED this fire

`softhouse/rescued-agent-a2027f85cea4effc9-*` — `.softhouse/reviews/t24-probe/**` **salvaged** (T24 was the
only round T23–T47 with no probe artefact on `main`; its output is observed oracle data at `(19, HALF_UP)`).
Its 37-line DEC-1 edit was **deliberately not taken** — v2-era, and it would have regressed the document.
`softhouse/rescued-agent-a353b03c0dea4dd41-*` — **not merged, by decision**: raw observations already on
`main`, attestations stale by T42's eight-point rule, `Capture3.java` a modification of a file T35/T36
rewrote. Kept on `origin` as the only copy. See `.softhouse/reviews/t24-probe/README-PROVENANCE.md`.

## If a fire dies mid-flight

Check each `softhouse/T*` branch for commits — every worker is told to commit early and often. A branch with
commits holds rescuable WIP: mark that task `needs_retry` with `note: worker killed mid-flight; rescued WIP
on <branch>, completeness unverified`. **Never leave it `in_flight`.** And **always check for an existing
`softhouse/<taskid>-*` branch before dispatching** — a previous fire left a *complete* T38 unmerged with
`tasks.json` still saying `pending`, and nearly redid fifteen commits of it.
