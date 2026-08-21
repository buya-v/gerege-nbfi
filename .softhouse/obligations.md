# Obligations register

Created by the `/softhouse-program` driver, local fire `20260821-134344`, to execute **P-5**
(`.softhouse/gates-proposed-answers.md`, Buyan, 21 Aug 2026):

> **A finding already covered by a passing vector is an obligation, not a blocker.** Record it, naming the
> vector that grades it, and close the task. **No third draft of a prose item.** **Money-changing findings
> are exempt** — they still block, still get fixed, still get re-reviewed. The test: *does it change a
> number the reference oracle would emit?*

This file is the destination P-5 prescribes. An entry here is **not** "wontfix" — it is a real finding whose
correctness is already guarded by something that runs, so it does not hold a tier open. Anything here may be
picked up by any later fire; nothing here may be cited as *proof* of a property.

**How the triage was applied.** Each open task was asked P-5's question. Seven answered *yes* and stay live
(§1). The rest are recorded below and their tasks closed `closed_as_obligation`. Two things this register
must not be used for: it does not retire the finding, and it does not license a later worker to describe the
guarded property as *proven* — the vector or guard named in the "graded by" column is the proof, and if that
column is empty the obligation is **ungraded** and says so.

---

## 1. NOT obligations — the money-exempt tail that stays live

These change, or can silently mis-decide, a number the reference oracle would emit. P-5's exemption applies
verbatim: they still block, and they are carried into the Tier A run rather than closed.

| id | finding | why it is money-exempt |
|---|---|---|
| **T149** | The corpus has **0 of 46 vectors carrying either tie answer**, so nothing in the parity corpus would notice a port that inherited Fineract's stock `HALF_EVEN`. | The ratified tenant parameter is `HALF_UP` (CLAUDE.md). A tie rounds to a *different minor unit* under the two modes — measured live: `1,162,502.50 × 0.018 = 20,925.045` → `20925.05` (gerege/HALF_UP) vs `20925.04` (default/HALF_EVEN). This is the first non-negotiable, ungraded. |
| **T143** | Both no-float guards inspect **identifiers**, so a float *literal* (`token.FLOAT`) such as `rate := 0.036 / 12.0` builds, passes `TestNoFloatInTheLoanScheduleTree`, and takes `conformance.sh` to exit 0. | A hole in the first non-negotiable in CLAUDE.md. Fix measured free today (0 float / 0 imaginary literals across the tree's 21 files). |
| **T132** | `guard_no_float_in_vectors` / `guard_no_float_in_harness` use bare `grep -Eq` with neither `LC_ALL=C` nor `-a`; one invalid byte before a float on the same line makes the guard **silently pass**. | Same non-negotiable, same guard. |
| **T145** | 74 of 240 `.py` files under `.softhouse/` call `json.load` with no `parse_float=`, so every money literal in a capture becomes a binary double on read. Worst: `capture/actualactual/analysis/discriminate.py:160` decides a money claim by **binary-float equality** and prints "ALL n PERIODS REPRODUCED DIGIT FOR DIGIT". | The analysis layer does not emit the port's numbers, but it *adjudicates parity claims about them*. This is the P-25 class that already put "18 instead of 22" into a gate write-up Buyan reads. |
| **T120** | The store and the float-guard disagree about what is in the store (`find` recursive vs `LoadStore` one level deep, bytewise suffix) and **nothing compares the counts**; five measured silent consequences. | A vector the float guard never inspects is a vector the money non-negotiable never covered. |
| **T116** | G-8 option (a) — promote a **family B** parity vector with an explicit invariant exemption (761 cells, 0 cell diffs). | Adds a graded vector in a region where "match the oracle" and "principal amortizes to zero" provably cannot both hold. |
| **T117** | Family B is measured at 29 cells and still **uncaused**; whether the failing principal can exceed **one minor unit** is the last open question that could move G-8's bound. | The answer is a money magnitude, and it changes the disclosure. |

> **G-8's options (b) and (c) remain hard `user` gates** and are untouched by any of the above.

---

## 2. Obligations — recorded, tasks closed

### 2.1 Guard and rig hardening (graded by a guard that runs today)

| id | obligation | graded by |
|---|---|---|
| **T97 / T113** | The interpreter guard's probe was a **negative** test; replaced with positive evidence (`conformance-psub-live` written across `<(...)`, read back, admitted only on string equality). The forgeable-token hole (`_conformance_psub_line` uninitialised inside the `eval`) was closed. | **MERGED and live**: `conformance.sh` interpreter guard, exit 3; T106's 8-assertion `prove-token-forgeable.sh` and T97's 13-assertion `prove-interpreter-guard.sh`. |
| **T151** | T138's eight findings — `prove-guards.sh`'s G-4 was green on a tree with `LC_ALL=C` removed from the scanner it guards; two "under adjudication by T108" comments were affirmatively wrong. | **MERGED this fire**: `capture/t91/t151-drive-g4.sh`, `t151-drive-g67.sh`, `t151-drive-vb.sh`, `t151-merge-check.sh`; `GUARDS-RED.txt` 17 legs exit 0. |
| **T152** | T135's three required changes to T99 — the `git merge-base main HEAD` anti-pattern (P-24, failed twice before) replaced by a literal fork sha; sweep patterns widened with the residual blind spot **stated**. | **MERGED this fire**: `capture/pathb/t99/FORK-POINT-SHA`, `prove-f1..f5`, `prove-p24-postmerge.sh`, `prove-sweep-patterns.sh`, `run-all.sh`. |
| **T105** | The harness report embeds the **absolute** store path, so two worktrees can never produce byte-identical output. | **Ungraded.** Byte-identity of harness output is used as evidence throughout this pipeline; this obligation weakens that evidence across worktrees and nothing currently detects it. Carry into Tier A. |
| **T126** | T109's residual class backlog — unread digests in 19 rigs, and `admit.go:594`. | Partially graded by the merged T109/T127 stream; the `admit.go:594` half is **T141** below. |
| **T141** | `admit.go:594` skips the capture-digest check on an empty string — a guard that cannot fail (P-22 class). | **Ungraded.** Real P-22 instance; carry into Tier A with T105. |
| **T133 / T137 / T148** | The two `charges/` copies of `preconditions.sh` never received T99b's F-5 liveness fix; `CANARY_EXPECT` is still env-overridable there; `charges/bin/attest.py` is a stale unrunnable fork. | Partially graded: the **enforced** path is `preconditions.sh:159-160 → exit 1 → attest.py:90/:95-98` (established by T142's correction of T109's escalated headline). The un-back-ported copies are the live residue. |
| **T139** | FU-1 — the identity/digest check on the sourced rig, the only thing that closes **N9/N10**. | **Ungraded. N9 and N10 remain OPEN** and their disclosures on `main` say so. This obligation must not be read as closing them. |
| **T144** | X-1 / X-2 / M-6 — two different stores, a `--prove` that skips the guards, a `selfcheck` nothing calls. | **Ungraded.** |
| **T142** | T127's seven micro-fixes to T109, including a zsh regression T109 introduced (`set -- $fork_line` does not word-split in zsh, so that row refuses the *correct* pin too). Its worker was killed mid-flight and **wrote no branch** — no work exists to rescue. | The escalated headline it was sent to correct **is already corrected on `main`** (see T133 row). The zsh row's zero discriminating power is recorded here rather than re-dispatched. |

### 2.2 Prose and evidence corrections (P-5 "no third draft")

| id | obligation | disposition |
|---|---|---|
| **T2** | Progressive-loan schedule behaviour extraction — rejected twice, parked by G-2 (CLOSED–DECLINED). | Specification of record is **DEC-1 rev 12** (ratified, frozen in `contract.go`), the 42-vector parity corpus, and T3b's re-review. `docs/analysis/progressive-schedule-behavior.md` carries a SUPERSEDED banner and inline CORRECTION blocks. |
| **T70 / T72 / T78** | Third, fourth and fifth drafts of the `futureUnrecognizedInterest` write-up. | **CLOSED by T88+T89 and merged.** P-5 names this exact chain as its motivating case. |
| **T100** | Rework G-8's write-up as two phenomena. | **Superseded** — G-8 was rewritten on `main` in `95ec06a` and the two-family split is live in `gates.md`. The A/B attribution error is annotated at `gates.md:978`. |
| **T92** | A committed capture artefact carries a false claim about its own preconditions (`Capture3i.java:442`). | Recorded. The claim is about a *precondition*, not a number; no vector rests on it. |
| **T94** | T75's review claims its probe is reproducible, but no probe artefact was ever committed. | Recorded. **The claim of reproducibility is withdrawn by this entry** — T75's probe is not reproducible until an artefact exists. |
| **T111** | T90's false sweep-completeness claim, and the frozen 26/4 comment. | Recorded; the completeness claim is **withdrawn**, not repaired. |
| **T93** | `vectors/README.md:607` said "all **36** promoted parity vectors". | **FIXED inline this fire** — and the substantive claim re-verified mechanically over the whole store: 42 parity vectors, 42 `DISBURSEMENT` periods, **0 exceptions**. |
| **T12 / T25 / T65 / T76 / T83 / T98** | Checkpoint drill (exercised), P0 application (applied), superseded fix rounds, a rejected re-capture, a rejected G-8 measurement whose **numbers T84 reproduced byte-identically** (`01b41d9c…`). | Closed. T83's numbers live on in T84's merged review evidence; only its write-up was rejected. |

---

## 3. What this register does not do

- It does not retire a finding. Every row above is still true.
- It does not license "proven". Where the **graded by** column reads *Ungraded*, the property is **not**
  established by anything that runs, and a later worker citing it as established is making the P-22 error
  this program has now hit five times.
- It does not touch **N9**, **N10**, or **G-8 (b)/(c)** — all open, all still open after this file.

---

## 4. Unmerged-branch register (repo-hygiene rule, 21 Aug 2026)

> *"A worktree with unmerged commits is a claim on attention. Each must end as merged, explicitly abandoned
> with a reason in `tasks.json`, or re-dispatched. Silent accumulation of unmerged branches hides lost work —
> the exact failure this program has already hit three times."* — `patterns.md`

The driver surveyed all 22 branches carrying commits not on `main` (fire `20260821-134344`) and found a real
instance of exactly the failure the rule names.

### 4.1 RECOVERED — six independent review documents were not on `main`

`main` carried the *fixes* those reviews forced but not the *reasoning that forced them*. For a pipeline whose
central control is an independent reviewer who re-derives money math, losing the review is losing the control.

| review | size | what it holds |
|---|---|---|
| `T67-review-of-T65` | 43 KB | + `T67-probe_test.go.txt` |
| `T79-review-t78` | 29 KB | the review that **refused the driver's bijection framing** (P-20) |
| `T101-review-of-T100` | 60 KB | |
| `T127-review-of-T109` | 57 KB | the zsh-regression finding |
| `T131-review-of-T108` | 41 KB | |
| `T135-review-of-T99` | 51 KB | + 26 executable evidence scripts (`T135-evidence/`) |

**All six recovered onto `main` this fire** — 296 KB of text and scripts, no raw dumps. Their raw
`capture/*/out/` trees were deliberately left on the branches per the hygiene rule (artefacts are stored as
recipe + SHA-256, not committed whole).

### 4.2 Capture-rig branches — held for the recipe/hash conversion, not abandoned

These carry capture rigs *and* large raw output trees. Merging them wholesale would violate the hygiene rule
that created this register; discarding them would lose the rigs. They are held pending a conversion pass that
lands `bin/` + recipe + SHA-256 and leaves `out/` regenerable.

| branch | commits | new files | note |
|---|---|---|---|
| `T40-charges-capture` | 10 | 149 | `charges/bin/` partly landed already via later tasks (see T133/T137/T148) |
| `T42-mathcontext-inforce` | 7 | 61 | the `(19, HALF_UP)` in-force evidence |
| `T39-periodratio-observation` | 6 | 47 | |
| `T22-pathb-audit-rescued` | 1 | 39 | |
| `T108-grep-adjudication` | 1 | 30 | the 360-cell grep matrix behind **T132** (money-exempt, §1) |
| `T109-fork-point-digest-compare` | 5 | 19 | superseded in substance by the merged T142/T127 corrections |
| `T21-pass3-audit-rescued` | 1 | 14 | |
| `T131-review-t108` | 2 | 30 | review **recovered** above; `t131-grep/` corpus held |

### 4.3 Explicitly abandoned, with reason

| branch | reason |
|---|---|
| `T38-dec1-v7`, `T38-dec1-v7-pass2` | Superseded by **DEC-1 revision 12**, ratified and frozen in `contract.go`. Revisions 6–8 are the cost P-4 was written to stop paying; keeping their branches live invites a ninth. |
| `T4-dec1-retry-rescued`, `T16b-capture-plan-corrections` | Single-file WIP against a superseded DEC-1 draft. |
| `T71-fui-marker-review` | Review **is** on `main`; the `futureUnrecognizedInterest` chain closed via T88+T89 (P-5's motivating case). |
| `rescued-agent-*-20260818-200001` (×2) | WIP from the 17:22 stranding on 2026-08-18; re-dispatched at the time and the successor work is merged. |
| `rescued-agent-a8581c69…`, `rescued-agent-a1be0f4d…` (`-20260821-080001`) | Single-file WIP from workers killed at the 08:00 fire's session limit. **T151 and T152 both completed and merged this fire**, so the successor work exists on `main`. |

Pruned this fire: `rescued-agent-a23f3059…-20260820-230001` and `T99-pathb-lower-findings` (clean, fully
merged, worktrees removed). **Nothing in §4.2 or §4.3 has been deleted** — every branch still exists and any
fire may revisit it.
