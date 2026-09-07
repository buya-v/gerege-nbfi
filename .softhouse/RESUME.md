# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260906-2000` (cloud, 20:00 Asia/Ulaanbaatar, reference oracle UNREACHABLE) — **CLOSED CLEAN. ZERO LIVE WORKERS.**

5 dispatched / 5 completed / 0 killed. Every worker committed to its branch, every executable
claim was re-driven by the driver rather than read, and all six branches are merged and pushed.
Lock taken under **arm 0** (no `LOCK` file existed) and released before exit.

---

## THE HEADLINE: THE "STRANDED COMMITS" STORY WAS WRONG, AND IT HAD BEEN WRONG FOR TWO DAYS

`ready-tasks.py` had exited **5** on every fire since 2026-09-02, once naming **21** unbacked
claims, and every one of those fires read it the same way: *five money-core commits are stranded on
Buyan's laptop; only Buyan can push them.* Measured in a fresh clone this fire rather than
inherited:

| Task | Claimed sha | Reality on `origin` |
|---|---|---|
| **T509** — critical path | `857dd4d8` **dead** | **REPUBLISHED as `23966a65`**, ancestor of `origin/main` |
| **T508** | `1abd3a11` | **PUSHED INTACT**, ancestor of `origin/main` |
| **T515** | `84dc208e` | **PUSHED INTACT**, ancestor of `origin/main` |
| **T510** | `5c4233fc` | **PUSHED INTACT**, ancestor of `origin/main` |
| **T512** | `8ff5ff15` **dead** | **GENUINELY UNRECOVERED** |

**One republished under a new hash, three pushed intact, one lost.** The standing ask on Buyan —
`git push origin --all` from the Mac — had **already been satisfied two days earlier**; only the
manifest still said otherwise. `git rev-parse` cannot tell a re-hashed publish from work that never
existed, which is how three fires inherited the wrong story.

**STEP 0 now exits 0, `check-branch-published: CLEAN`** — and under T536's **tightened** classifier,
which is a stronger result than the CLEAN banked mid-fire under the loose one.

**ERRATUM, corrected within the fire.** The first version of this reconciliation said *four of five
were republished* and marked `1abd3a11` and `84dc208e` **dead** — carried from the stale manifest
**without measuring**, inside the very document written to correct claims carried without measuring.
Both resolve and are ancestors of `origin/main`. That correction is what unblocked T520 and T522.

### The one real loss

**T512's deliverable does not exist.** `.softhouse/bin/scope-check.sh` was never added on **any** of
3070 reachable commits. Reclassified `needs_retry`; a redo must re-derive from **P-41**, not from
T512's description of itself. Still live because of it: the two-dot `git diff main..<branch>` scope
form P-41 recorded as WRONG is **still prescribed** by `softhouse/SKILL.md` STEP 5.

---

## Merged this fire

| Task | What it landed |
|---|---|
| **T523** | **The program critical path is REVIEWED AT LAST.** ACCEPT WITH CONDITIONS on T509 with **four undeclared MAJORs**, two of them **fail-opens on "balances are derived, never written"**. Also settled the count dispute: 42 reproduces class-for-class at `23966a65`, 34 is the same denominator on today's main, and the guard source is **byte-identical** between `23966a65` and HEAD. |
| **T536** | T528's five conditions on the branch-published guard. Merged on T537's explicit recommendation. |
| **T537** | **CRITICAL: T536 closed a longer list, not a class.** 8 of 8 invented phrasings launder a missing branch; reproduced **on the real record** (T509 moved finding → waiver, 19→17). Stub arm defeated by a **three-line** stub. "66 of 73" not reproducible; true delta **77→68**. |
| **T551** | T548's three MAJORs on T532 — and it **refused one of them**, marking the trace `[UNVERIFIED]` rather than write a stronger claim as verified. |
| **T553** | The no-op-fire-streak vetoes **compose** now, and **the floor was not raised**. |
| **T522** | ACCEPT WITH CONDITIONS (PARTIAL) on T515. Both in-scope items clean; **MAJOR F-1**: the arm that gives held funds back is graded by nothing. |

## Filed this fire — the next fire's work, in priority order

| Task | Why it matters |
|---|---|
| **T555** | T523's nine conditions. **C-1 and C-2 are fail-opens on a money non-negotiable** and carry the urgency. |
| **T556** | T537's CRITICAL. Carries the one sentence that matters: adding the eight notes as `--selftest` cases is **necessary but not sufficient** and must not be offered as the repair — that is the move T527 **and** T528 both made. |
| **T560** | T522's F-1 — the mutation test is runnable **now**, with no oracle. |
| **T557 / T559** | Paired independent reviewers for T551 and T553. |
| **T558** | T553's declared residual, with three roads already measured dead. |
| **T554** | **Re-scoped and made to depend on T556**, per T537: shipped alone it closes 2 of 8 cases and would be reported as the class. |

## Parked — and the reasons are now measured, not inherited

| Task | Reason | Unparks when |
|---|---|---|
| **T520** | `oracle_unreachable` — **reason corrected this fire** from the false `branch_unpushed`. All its items need the live schema, and substituting source reading for `information_schema` is the exact method error T513 caught in T510. | next local fire |
| T533, T535 (b)/(c), T521 | `oracle_unreachable` | next local fire |
| T522's item 3 | `oracle_unreachable` — named residual, see below | next local fire |
| T547 | `serialised` — same `files_hint` as T551 | now unblocked (T551 merged) |

**T522's residual, verbatim, for the next oracle-reaching fire:** confirm the instance is on tenant
`gerege` (`rounding-mode = 4`, Asia/Ulaanbaatar — restored 2026-09-05 by OH-1, so this is cheap);
re-take CAPTURE-A and CAPTURE-B there **and commit the raw psql output**; take a **new CAPTURE-C**
with a deposit/hold/**release** chain, which does not exist today and is what F-1 needs; re-run the
`information_schema` recount; run the conformance harness; settle the `PAY_CHARGE` / null
`chargePaidBy` case.

**Reference oracle probe this fire:** `https://localhost:8443/…/actuator/health` → **HTTP 000**.
No conformance run, no vector captured, **nothing synthesised**. Conformance exit 2 is never a PASS.

## Gates

**No `user` gate crossed.** Open **contract** gates: **0**. **G-23** (RESERVED — the Nexus platform
tree is not in this repository) still awaits Buyan and still blocks the Tier-C map-first audit from
being more than a source-side inventory.

## Standing items for Buyan

1. **The `git push origin --all` ask is CLOSED.** It was satisfied two days ago; the manifest was
   stale. Nothing to do.
2. **T512 is a genuine loss**, already filed for redo. No decision needed.
3. **G-23 remains the only thing genuinely waiting on you.**
