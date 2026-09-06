# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260906-2000` (cloud, 20:00 Asia/Ulaanbaatar, reference oracle UNREACHABLE) — **IN FLIGHT. TWO LIVE WORKERS.**

Written and pushed **BEFORE the first `git worktree add`**, per STEP 0's push-before-spawn obligation.
If you are reading this on a fresh session, treat **T523** and **T537** as `needs_retry` with
unverified completeness and look for their branches on origin before assuming nothing was done.

Lock taken under **arm 0** — no `LOCK` file existed at fire start. The local fire `20260906-200001`
took its lock at `eb3f6f6d`, ran a full iteration (OH-CORE merged) and **released it cleanly** at
`5d82ce6d`, 20:04:41 +0800. No takeover, no contested signal, nothing stale. First uncontested lock
acquisition in some days, and it is worth noting because the last three fires all had to reason about
a lock somebody else abandoned.

---

## THE HEADLINE: THE RECORD IS BACKED BY origin FOR THE FIRST TIME IN FOUR FIRES

`ready-tasks.py` now prints **`check-branch-published: CLEAN`** and the STEP 0 refusal is gone.
It had exited **5** on every fire since 2026-09-02, at one point naming **21** unbacked claims, and
every one of those fires read the refusal the same way: *five money-core commits are stranded on
Buyan's laptop and only Buyan can push them.*

**That reading was half wrong, and the wrong half was the load-bearing half.** Measured in this
clone at `origin/main = 3644eab3`, not inherited from the manifest:

| Task | Claimed sha | Reality on origin |
|---|---|---|
| **T509** — the critical path | `857dd4d8` **dead** | **PUBLISHED as `23966a65`**, ancestor of `origin/main` |
| **T508** | `1abd3a11` **dead** | handoff tracked on `origin/main` |
| **T515** | `84dc208e` **dead** | handoff tracked on `origin/main` |
| **T510** | `5c4233fc` | **PUBLISHED**, ancestor of `origin/main`; handoff tracked |
| **T512** | `8ff5ff15` **dead** | **NOTHING. GENUINELY UNRECOVERED.** |

**Four of the five were republished under new hashes.** The Mac re-created the work as fresh commits
instead of pushing the original branches, so the shas and branch pointers died in the rewrite while
the substance travelled. `git rev-parse` cannot tell that apart from work that never existed — the
same blindness `check-branch-published.py` exists for, arriving from the opposite direction.

Substance verified rather than assumed, for T509: `balanceSynonymRe` is at
`origin/main:.softhouse/guards/ledgerguard/main.go:199` and is wired into the predicate at `:341`.

**So the standing ask on Buyan — `git push origin --all` from the Mac — is CLOSED for four of five,
and it was already closed two days ago; the manifest just kept saying otherwise.** Full measurement:
`.softhouse/observations/2026-09-06-republished-under-new-hash.md`.

### The one real loss

**T512's deliverable does not exist** — `.softhouse/bin/scope-check.sh` and `scope-check-demo.sh`
were never added on any ref (`git log --all --diff-filter=A -- '*scope-check*'` over all **3070**
reachable commits: empty). Reclassified `needs_conditions` → **`needs_retry`**. A redo must
re-derive the instrument from **P-41**, not from T512's description of it.

**Still live because of it:** the two-dot `git diff main..<branch>` scope form that P-41 recorded as
WRONG is *still prescribed* by `softhouse/SKILL.md` STEP 5, since its replacement never landed.

---

## Dispatched this fire (both `executor: agent`, `isolation: worktree`, `opus`, offline-safe)

Both are INDEPENDENT reviews that had been unrunnable, and both became runnable **only because of
this fire's reconciliation** — neither needs the reference oracle.

| Task | Branch | What it must land |
|---|---|---|
| **T523** | `softhouse/T523-review-t509` | **UNPARKED.** Independent review of T509 — the money non-negotiable guard that went 10 findings → 42, on the program critical path, and has never been reviewed. Parked as `branch_unpushed` for two fires on the belief the diff was unreadable; it is readable at **`23966a65`** on `origin/main`. Central risk is **false positives dressed as rigour**. Note a live discrepancy for it to settle: the driver recorded *Findings: 42* at the dead sha, and this fire's run of `check-ledger-invariants.sh` on current main shows a SQL-surface census line reading *Findings: 34*. |
| **T537** | `softhouse/T537-review-t536` | **RE-DISPATCH** (attempt 2). Independent review of T536 — did the anchor repair close a CLASS or a longer list of phrasings? The previous attempt's worker was killed mid-flight by fire `20260906-200001` and produced nothing recoverable. The subject is readable: `softhouse/T536-t528-conditions` resolves on origin at `18c64389`. |

**SCOPE GUARD:** neither worker may write outside its own `files_hint`
(`.softhouse/reviews/t523-review-t509/`, `.softhouse/reviews/t537-review-t536/`, plus its handoff).
Neither may edit `conformance.sh`, `nexus/**`, or the guards they are grading.

## Filed this fire

- **T554** — `check-branch-published.py` **cannot tell an assertion from a documented refutation**.
  Hit by the driver while doing the reconciliation above: the first pass drove unbacked claims 8 → 3
  and **all three residuals were sentences correctly recording that a sha is dead**. That makes one
  of the two legitimate exit-5 repairs (*correct the note to say the work is UNRECOVERED*)
  unperformable in the record the guard reads, leaving only laundering or draining the record.
  Depends on T537. Explicitly **not** to be repaired with a negation word list — that is B-11/P-104
  one level up.

## Parked / not run this fire

| Task | Reason | Unparks when |
|---|---|---|
| T533 (FindInterestPeriod divergence vectors) | `oracle_unreachable` | next local fire |
| T535 (Lombok value vs Go pointer equality) | `oracle_unreachable` for (b)/(c); (a) is source-only | next local fire, or a later cloud fire for (a) |
| T521 (restore `gerege` tenant) | `oracle_unreachable` | next local fire |
| T546 (skill files do not document exit 5) | `dependency` — needs T537 | T537 lands |

Reference oracle probe this fire: `https://localhost:8443/fineract-provider/actuator/health` →
**HTTP 000, unreachable**. Expected in the cloud sandbox; every vector-capture and conformance task
parks under `oracle_unreachable` and nothing was synthesised.

## Gates

**No `user` gate crossed.** Open **contract** gates: **0** — `ready-tasks.py` inspected every id in
`program.json.gates_pending`. **G-23** (RESERVED — the Nexus platform tree is not in this repository)
still awaits Buyan and still blocks the Tier-C map-first audit from being more than a source-side
inventory.

## Standing items for Buyan

1. **The `git push origin --all` ask is CLOSED for four of the five commits** — it was satisfied two
   days ago and the manifest simply had not been re-measured. Nothing to do.
2. **T512 is a genuine loss** and needs no decision — it is filed for redo.
3. The local fire is publishing again (OH-SEED, OH-PROV, OH-CORE all merged 2026-09-05/06), so the
   two-day publishing outage is over.
