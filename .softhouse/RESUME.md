# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260905-1200` (cloud, 20:00 Asia/Ulaanbaatar, oracle UNREACHABLE) — **IN FLIGHT. TWO LIVE WORKERS.**

Written and pushed **BEFORE the first `git worktree add`**, per STEP 0's push-before-spawn obligation.
If you are reading this on a fresh session, treat **T536** and **T539** as `needs_retry` with
unverified completeness and look for their branches on origin before assuming nothing was done.

Lock taken from the previous **cloud** fire `cloud-20260904-1200` under **arm 5** — both signals
stale: `origin/main`'s tip was 22.55 h old and `started_at` 23.60 h old. **Arm 3 did not fire**
(23.60 h is under the 24 h ceiling), so this takeover rests on arm 5 alone. Arm 4 did not read HELD.
The lock was never released because that fire ended without deleting it — an exit-protocol miss, not
a live holder.

---

## THE HEADLINE IS UNCHANGED, AND THAT IS ITSELF THE NEWS

Five completed money-core commits still exist on exactly one laptop, and `main` still says they are
done. **Nothing has moved in the 24 h since the last fire measured it**, and the local Mac fire —
the only one that can reach the reference oracle — **has not published since 2026-09-03**. Two days.

Re-measured in this clone this fire, not inherited:

```
git rev-parse --verify -q <sha>^{commit}   # 857dd4d8 1abd3a11 84dc208e 5c4233fc 8ff5ff15 -> all ABSENT
python3 .softhouse/bin/ready-tasks.py      # exit 5, STEP 0 REFUSE, 21 unbacked claims
```

| Task | Recorded on main | Claimed commit | Reality on origin |
|---|---|---|---|
| **T509** | `done` — **THE CRITICAL PATH** | `857dd4d8` | **absent** |
| **T508** | `done` | `1abd3a11` | **absent** |
| **T515** | `done` | `84dc208e` | **absent** |
| T510 | `needs_retry` | `5c4233fc` | **absent** |
| T512 | `needs_conditions` | `8ff5ff15` | **absent** |

**Only Buyan can fix this**, from the Mac: `git push origin --all`. Until then the bar stays RED
(`conformance.sh` exits 2 with **no probe line** — a HARD guard failure, **not** an oracle outage),
three independent reviews (T520/T522/T523) stay parked as `branch_unpushed`, and T509 — the guard
repair on the critical path — cannot be reviewed by anyone.

**T527's guard now makes this refuse loudly instead of passing silently.** `ready-tasks.py` exits 5
at STEP 0 naming all 21 unbacked claims. That is the guard working as designed; it is not a new fault.

---

## Dispatched this fire (both `executor: agent`, `isolation: worktree`, offline-safe)

| Task | Branch | Model | What it must land |
|---|---|---|---|
| **T536** | `softhouse/T536-t528-conditions` | opus | T528's five conditions on T527's branch-published guard. **RE-DISPATCH** — the first attempt died with the previous fire's session having created nothing (every signal measured empty; the unstarted world, not an unpushed one). The point is F-1: `LANDING` is the DEFAULT anchor classification, so one reworded word launders a genuinely missing branch into the waivers. Invert the default if it can be done without losing the 66 legitimate waivers. |
| **T539** | `softhouse/T539-t538-conditions` | opus | T538's five conditions on T534. Contiguity is **not** an invariant — restate it as insertion-path-only while keeping the conclusion, and *support* it with the 18-site enumeration re-derived rather than re-asserted. Fix the axis-2 sentence, which currently names a GREEN case. Comments only. |

Paired independent reviewers **T537** (reviews T536, pre-existing) and **T540** (reviews T539, filed
this fire) dispatch after their subjects land.

**SCOPE GUARD, load-bearing again this fire:** no worker may touch `conformance.sh`,
`.softhouse/guards/ledgerguard/`, or `nexus/internal/apps/savings/`. All three are edited by the five
unpushed commits. A conflict against work that exists but cannot be read here is worse than the work
not being done.

**Fineract checkout pinned** to the commit of record `426a23544` this fire (it had drifted to
`74099701`). `InterestPeriod.java` measures **237 lines** there, matching T532's brief — so the
citation findings in this chain are graded against the right tree.

## Parked / not run this fire

| Task | Reason | Unparks when |
|---|---|---|
| T533 (FindInterestPeriod divergence vectors) | `oracle_unreachable` | next local fire |
| T535 (Lombok value vs Go pointer equality) | `oracle_unreachable` for (b)/(c); (a) is source-only and runnable | next local fire, or a later cloud fire for (a) |
| T532 (InterestPeriod citation sweep) | `serialised` — same `files_hint` as T539 | T539 merges |
| T520 (review T508) | `branch_unpushed` | `softhouse/T508-…` resolves on origin |
| T522 (review T515) | `branch_unpushed` | `softhouse/T515-…` resolves on origin |
| T523 (review T509) | `branch_unpushed` | `softhouse/T509-…` resolves on origin |
| T521 (restore `gerege` tenant) | `oracle_unreachable` | next local fire |

`branch_unpushed` is deliberately **not** `oracle_unreachable`. Three of these are a publishing
failure; misfiling a publishing failure as an outage is the exact reclassification error STEP 4 is
written to prevent.

## Gates

**No `user` gate crossed.** Open **contract** gates: **0** — `ready-tasks.py` inspected every id in
`program.json.gates_pending`. One RESERVED gate (**G-23**, the Nexus platform tree is not in this
repository) still awaits Buyan and blocks the Tier-C map-first audit from being anything more than a
source-side inventory.

## Standing items for Buyan — no agent can clear these

1. **`git push origin --all` from the Mac.** Five money-core commits, T509 the critical path, exist
   on one machine. Unchanged for 24 h. Until then three independent reviews cannot run and the bar
   cannot go green.
2. **The local fire has not published since 2026-09-03** — two days, four missed 08:00/14:00 slots.
   The cloud fire cannot substitute: it reaches no oracle, so no vector has been captured in that
   window either. Check the Mac is awake and the launchd agent is loaded.
3. Eighteen no-op fires over four days burned on `OAuth session expired`, and **nothing escalates a
   zero-turn fire** (T493/T494 still `pending`). The detection exists; the consequence does not.
