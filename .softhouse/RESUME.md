# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260904-1200` (cloud, 20:00 Asia/Ulaanbaatar, oracle UNREACHABLE) — **IN FLIGHT. TWO LIVE WORKERS.**

Written and pushed **BEFORE the first `git worktree add`**, per STEP 0's push-before-spawn obligation.
If you are reading this on a fresh session, treat T526 and T527 as `needs_retry` with unverified
completeness and look for their branches before assuming nothing was done.

Lock taken from `local-launchd` fire `20260903-170002` under **arm 3 (CEILING)**: its `started_at`
was 27.5 h old, over the 24 h bound. Arm 5 corroborated — `origin/main`'s tip was 25.3 h old. No arm
read HELD.

---

## THE HEADLINE: FIVE COMPLETED COMMITS EXIST ON EXACTLY ONE LAPTOP, AND MAIN SAYS THEY ARE DONE

This is **P-85 one level up**. P-85 is *"two orchestrators held the lock at once, and the cause was an
unpushed in-flight state."* The same root cause has now destroyed the **reviewability** of five
completed tasks, and the record on `main` asserts the opposite.

Measured in this clone, not inferred:

```
git rev-parse --verify -q <sha>^{commit}   # for each sha below -> "Not a valid object name"
git ls-remote --heads origin 'refs/heads/softhouse/*'   # NOTHING numbered above T497
```

| Task | Recorded on main | Claimed commit | Reality on origin |
|---|---|---|---|
| **T509** | `done` — **THE CRITICAL PATH** | `857dd4d8` | **absent** |
| **T508** | `done` | `1abd3a11` | **absent** |
| **T515** | `done` | `84dc208e` | **absent** |
| T510 | `needs_retry` | `5c4233fc` | **absent** |
| T512 | `needs_conditions` | `8ff5ff15` | **absent** |

T502 / T511 / T516 / T519 survived **only** because their *merge* commits carried their content to
`main`. The rule that saved work was "merge and push"; the rule that lost it was "mark `done`, leave
it on a branch, review it next fire" — with no push in between. The three 2026-09-03 bookkeeping
commits (`a6f88805`, `f78ed058`, `a4b5ebac`) touch nothing but `LOCK`, `tasks.json` and
`reference-oracle.md`.

**Only Buyan can fix this**, from the Mac: `git push origin --all`.

### Consequence for the bar — it is RED, and NOT for the reason the last manifest said

`bash .softhouse/conformance.sh` exits **2 with no probe line** — a HARD guard failure, *not* an
oracle outage (STEP 4). Two distinct failures, both because T509 is not here:

1. `check-ledger-invariants.sh --selftest` **fails its own selftest**: case **(n) the REAL Go tree —
   must PASS: expected exit 0, got 1**. T509's replacement of case (n) with the committed fixture
   `ledgerguard/testdata/cleantree/` is **not on main** — that directory does not exist.
2. The guard REFUSES with **9 `I-3` findings** (4 `loanproduct`, 3 `savings` field writes, 2
   `savings` SQL balance writes). T509's repair, and T515's savings rework, are both unpushed.

**Nothing here may be parked as an oracle problem.** The oracle is irrelevant to all of it.

---

## Dispatched this fire (both `executor: agent`, `isolation: worktree`, offline-safe)

| Task | Branch | Model | What it must land |
|---|---|---|---|
| **T527** | `softhouse/T527-branch-published-guard` | opus | The guard that would have caught the above: refuse a task recorded terminal whose claimed branch/commit is absent from origin. Must **fail CLOSED** when origin is unreachable, and must be **wired** — six prior tasks in this program built a guard and wired it to nothing. |
| **T526** | `softhouse/T526-t519-residuals` | sonnet | T519's residuals in `loanproduct/`: two stale `[VERIFIED:]` citations, one loose `doc.go` claim, gofmt. |

Paired independent reviewers **T528** (reviews T527) and **T529** (reviews T526) are filed and
dispatch after their subjects land.

**SCOPE GUARD, and it is load-bearing this fire:** no worker may touch `conformance.sh`,
`.softhouse/guards/ledgerguard/`, or `nexus/internal/apps/savings/`. All three are edited by the five
unpushed commits. A conflict against work that exists but cannot be read here is worse than the work
not being done.

## Parked this fire

| Task | Reason | Unparks when |
|---|---|---|
| T520 (review T508) | `branch_unpushed` | `softhouse/T508-…` resolves on origin |
| T522 (review T515) | `branch_unpushed` | `softhouse/T515-…` resolves on origin |
| T523 (review T509) | `branch_unpushed` | `softhouse/T509-…` resolves on origin |
| T521 (restore `gerege` tenant) | `oracle_unreachable` | next local fire |

`branch_unpushed` is deliberately **not** `oracle_unreachable`. Three of these four are a publishing
failure; misfiling a publishing failure as an outage is the exact reclassification error STEP 4 is
written to prevent.

## Gates

**No `user` gate crossed.** `program.json.gates_pending` carried one entry that was a bare **string**
rather than a gate object, so `ready-tasks.py` could not read its state and reported it **OPEN**;
repaired to an object this fire (G-25/G-26/G-27, already resolved by T513 + T515). Open contract
gates: **0**.

## Standing items for Buyan — no agent can clear these

1. **`git push origin --all` from the Mac.** Five money-core commits, T509 the critical path, exist
   on one machine. Until then three independent reviews cannot run and the bar cannot go green.
2. Eighteen no-op fires over four days burned on `OAuth session expired`, and **nothing escalates a
   zero-turn fire** (T493/T494). The detection exists; the consequence does not. Unchanged.
