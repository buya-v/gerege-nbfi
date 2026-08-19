# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260819-200001`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP all fire, **never restarted** (several captures' comparability rests on that).
  `fineract:latest` + `postgres:18.3`, both healthy. Pinned checkout `426a23544` clean. PostgreSQL only.
- **Six workers dispatched, six completed, all merged. Nothing lost, no isolation violation, no scope breach.**

---

# THE HEADLINE: **the program has its first conformance PASS — and the driver spent the rest of the fire proving how little that PASS meant**

```
VERDICT: PASS (exit 0) — 13 parity vectors match the pinned reference oracle, 1350 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

`go build` / `go vet` exit 0 · `go test ./...` green · `gofmt -l` only the frozen `contract.go` (G-3) ·
`--prove` **20/20** · 6/6 invariants hold · 0 inadmissible · 0 harness errors.

**Every number above was re-run by the driver, not accepted from a worker's report.**

## What actually happened, in order

**1. T8 — promotion.** All 11 pass-3b production candidates promoted as parity vectors (`P-CAL` correctly
excluded as calibration). The `UNBACKED in_graded_domain claims` line disappeared.

**2. T20 — the harness learned to express a non-money kill.** Driver finding **D-4**: the harness encoded
gradeability as strictly money-valued (`margin_minor > 0`), which made its **own** `UNBACKED …
monthend.reanchor` complaint *unsatisfiable* — the only graders for that capability kill on **dates**.

**3. T10 — the first Go port. `PASS` on the first run.**

**4. T9 — the independent review that made the PASS mean something.** Deliberately scoped to re-derive from
**Fineract source** rather than from DEC-1's prose, because three earlier parties had all used the same
document-based method. Verdict **ACCEPTED WITH REQUIRED CHANGES**, 9 findings, 3 × P1.

**5. T57 + T56 — both P1s closed in the same fire.**

**6. T11 — adversarial review of the port — IN FLIGHT at checkpoint.**

---

## The result worth carrying: **a green run is a claim about the CORPUS as much as about the port**

T10 mutated its own port into each named wrong implementation and re-ran the real harness. **Five died.
Four survived — three of which move money.**

The driver reproduced the worst survivor independently: **delete the entire EMI re-adjust smoothing loop →
`exit 0`, 11/11 PASS.** DEC-1 calls that loop a normative conformance obligation, *"not backlog"*.

So T57 captured the two shapes DEC-1 itself names, and **the driver then re-ran the identical mutation**:

| | before T57 | after T57 |
|---|---|---|
| smoothing loop deleted | **11/11 PASS, exit 0** | **FAIL, exit 1** — both new vectors, named cells and margins |

**That closed loop — mutate → find the blind spot → capture the shape → prove the mutation now dies — is the
transferable result of this fire.** It is recorded as pattern **P-3** in `.softhouse/patterns.md`.

### Three money-moving mutations STILL survive all 13 vectors — handed to T11

1. **textbook `balance × rateFactor`** — three rounded operations collapsed into one
2. **rate factor without the trailing `setScale`** — not vacuous (`…333332` vs `…3333`), but below the
   currency layer on every corpus shape at precision 19
3. **`periodRatio` → `RepaymentEvery`** — every promoted vector is on-lattice

**Conformance cannot tell you whether the port got these right.** T11 must decide each from source.

---

## The false-PASS path that existed for part of this fire — found, closed, and re-verified

T9's **F-1**: `unrecorded_fields` was an unguarded escape hatch. It withdrew all nine cells of the month-end
kill from `P-02`/`P-02b`, left `1999-01-01` in place, and got **11/11 PASS, exit 0, with
`monthend.reanchor killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY` still printed** — a capability reported as
graded by a counterfactual whose every cell had been withdrawn.

T56 closed it; **the driver reproduced the exact exploit against the fixed harness** — now `exit 2`, both
vectors `INADMISSIBLE`, with a diagnostic naming the offending `divergent_cells` entry and the
`unrecorded_fields` that withdraws it.

T56 also reported honestly that it **could not have both** a stronger `installment_number` check and an
admissible corpus, explained why, and chose a documented sentinel rather than quietly relaxing the rule.

---

## Folklore that died this fire — both were being carried by everyone, one was the driver's

T9 re-derived from source and found the corpus-checking consensus was built on two false beliefs:

- **The oracle does NOT use the closed-form EMI.** It folds `Π(1+rᵢ)·P / fn`, no `pow`
  [`ProgressiveEMICalculator.java:1838-1840`, fold at `:1819` — **driver-confirmed independently**].
- **There is NO "final principal := remaining balance."** Principal is always `EMI − interest`
  [`RepaymentPeriod.java:339-344`]; the residual lands on the **last unpaid period's EMI** [`:1191-1206`].
  **This was trap #4 in the brief the driver wrote for T10** — the driver was wrong and was corrected
  mid-flight.

Both reproduce the current corpus identically, **because every promoted vector runs `DAYS_30`/`DAYS_360` so
every rᵢ is equal.** They are not guaranteed to agree at precision 19 once the rᵢ differ.

**The G-4 hunt found nothing.** T9 audited DEC-1 rev 12 against source in six places and found **no**
disagreement. Where DEC-1 and the folklore differ, **DEC-1 matches the source.**

---

## Driver catches this fire — each re-derived, none accepted on report

- **D-4** — the harness could not express a structural (zero-money-margin) kill, making its own UNBACKED
  complaint unsatisfiable. Specified and routed; T8-promote corrected the spec (it is a **decode**-time
  change — `DisallowUnknownFields` — so an `admit.go`-only fix would not have landed it).
- **D-5, D-6** — latent harness defects that detonate on first real use: a replay loader with **three silent
  `continue` paths**, and a frozen `ParityPass == 0` assertion. Pattern **P-4**.
- **D-6's THIRD recurrence** — driver-found post-merge: `--prove` was 18/20, both failures **stale proofs**,
  one of them a hard-coded `parity vectors PASS 11` that T57 moved to 13. Driver fixed both to assert the
  **property**, and verified proof 1 still discriminates (`-impl=__none__` → 2, `-impl=loanschedule-go` → 0).
- **Independent re-derivation of all 11 pass-3b candidates** before any worker reported — 11/11 digit for
  digit — plus an independent third-converter transcription audit of the promoted files: **883 cells, 0
  mismatches**. `P-01`'s headline margin `65,885,070` confirmed exactly.

---

## THE NEXT FIRE STARTS HERE

1. **T11's verdict** (in flight at checkpoint — read its branch `softhouse/T11-go-port-review` and merge).
2. **The three surviving mutations.** If T11 confirms the port is correct from source, they are a **corpus**
   gap, not a port defect: capture the shapes that grade them. This is oracle-only work.
3. **T13** — `/softhouse-uat` — then **T14** (user gate: accept the PoC slice; **no cutover**) and **T15**.

---

## Open decisions for Buyan — **none blocking, four open**

- **G-2** (one parked task, T2), **G-3** (`gofmt` vs the frozen `contract.go` — driver recommends leaving it
  unformatted; the workaround is in force), **G-4** (DEC-1's ACT/ACT wording is known-wrong).
- **G-5 — NEW.** DEC-1 contradicts itself on a **zero interest rate**: the prose says outside the graded
  domain, the enumerated list has no rate predicate, `admit.go` implements the list — and `SELFTEST-01`, the
  harness's own self-test fixture, **is a zero-rate request**. A port following the prose fails the harness.
  T10 implemented the list and flagged it rather than amending DEC-1. Driver recommends making the prose
  match the list.
- **RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
  facts. **None is in Run 1's path.**

## Process defect to fix — it recurred THREE times in one fire

Workers were handed worktrees cut **before** the merge of the artefact they were to work on (T9's **F-9**,
T57's **N-5**, and again on T56). T9 was sent to review 11 promoted vectors and found only the four
`REFUSE-*` files; **it re-cut onto `main` itself.** A reviewer who graded what was in front of them would
have reviewed an empty corpus and reported it clean. Every brief now says *"verify your base first"*, but
that is a workaround — pattern **P-5** records the real fix.
