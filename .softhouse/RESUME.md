# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260827-230001`, CHAIN ITERATION 2 — **IN FLIGHT. 7 WORKERS DISPATCHED. NOT CLOSED.**

**If you are reading this and no `claude` process owns this repo, these seven workers are DEAD and their
worktrees hold uncommitted work.** Written and pushed BEFORE the first worker was spawned, per STEP 0's
standing obligation — a `HEAD` saying "closed clean, zero live workers" while workers run is an active lie to
the next orchestrator, and no freshness rule can read through it.

| Task | Branch prefix | Owns (sole writer this batch) |
|---|---|---|
| **T324** | `softhouse/T324-*` | `.softhouse/bin/fire-program.sh` |
| **T326** | `softhouse/T326-*` | `.softhouse/conformance.sh`, `guards/dead-path-frontier.{pin,sh}` |
| **T306** | `softhouse/T306-*` | `nexus/internal/apps/ledger/conformance/admit.go` |
| **T327** | `softhouse/T327-*` | `.softhouse/capture/t327-closure-accepting-side/` (**oracle capture**) |
| **T282** | `softhouse/T282-*` | `.softhouse/patterns.md` |
| **T272** | `softhouse/T272-*` | `.softhouse/bin/go-env.sh` |
| **T277** | `softhouse/T277-*` | `.softhouse/gates.md` |

The seven edit sets are **disjoint by construction** — that is why these seven and not others. `T301` and
`T279` also name `fire-program.sh` and were held back so **T324 owns it alone**; `T310`, `T311`, `T313`,
`T303`, `T267` also name `conformance.sh` and were held back so **T326 owns it alone**; `T310` also edits
`admit.go` and the same capability row as **T306**, and is held until that gate is settled once.

## THE ENVIRONMENT FACT THE FIRE ARGS GOT WRONG: THE ORACLE IS **UP**

The fire contract handed this iteration `ORACLE: UNREACHABLE`. **That is stale** — chain iteration 1 brought
the stack up on the postgresql compose profile and it is still healthy. Re-probed at this iteration's start,
not assumed:

```
curl -sk https://localhost:8443/fineract-provider/actuator/health
  → {"status":"UP","groups":["liveness","readiness"]}
docker ps → fineract-fineract-1  Up 2 hours (healthy)  0.0.0.0:8443->8443
            fineract-db-1        Up 7 hours (healthy)  0.0.0.0:5432->5432
```

So the fire contract's **REACHABLE** branch applies: *prioritise the vector-capture and conformance work that
ONLY this local fire can do.* Nothing was parked, and **`T327` was filed for exactly that reason.**

## THE NEW TASK, AND WHY IT IS THE POINT OF THE FIRE

**`T327` — capture the ACCEPTING side of the closure and business-date boundaries, on a throwaway instance.**

The store says in its own capability registry that this is missing, and says why it was never taken:
`ledger.refusal.parity` records both acceptances as `[UNVERIFIED]` "because capturing an acceptance means
POSTING A JOURNAL ENTRY THAT CANNOT BE DELETED", with exact request bodies sitting unfired in T295's
adjudication as backlog **B-1** and **B-2**.

**That objection has already expired and the registry knows it:** *"the throwaway rig is the route for both …
A journal entry still cannot be deleted; an INSTANCE can."* T295 was right on the rig it had; T305 then built
the rig that removes the price.

**What it buys is not tidiness — it is a live parity hole.** `LDG-REFUSE-04` and `LDG-REFUSE-05` pin only the
**refusing** side of two date rules, so **a port that refuses every dated entry passes both and survives the
whole corpus** — the exact mutant shape T305 killed for opening balances last iteration (T296 arm A). The
same hole is open on these two rules right now.

`T327` is **raw observed capture only**: no vector promotion, no `conformance.sh`, no `admit.go`. Promotion is
deliberately a separate follow-up, so the irreplaceable oracle bytes are banked regardless of how T306's gate
argument lands.

## TWO TASKS WERE UNBLOCKED, WITH THE REASON RECORDED SO IT CAN BE OVERTURNED

- **`T324`** (RESUME's own #1: HIGH, live in committed code, destroys work) was serialised behind `T323`
  because T323 "holds conformance.sh and **may also be touching wrapper wiring**". T323 is `needs_retry`; its
  retry `T326` does **not** name `fire-program.sh`. The edit sets are disjoint, so the serialisation had no
  remaining basis. **Dependency cleared.**
- **`T306`** was `blocked`. T320's unblock condition is a **work instruction addressed to T306 itself**, not a
  user gate and not a missing dependency: *drop the refusal-kind precondition, and conformance must still show
  11/11 wrong impls dying with LDG-05 admissible.* It is carried into the dispatch verbatim as a **refusal
  condition on T306's own output**.

## STANDING HAZARD — UNCHANGED, AND T327 IS DISPATCHED UNDER IT

Three of `T287`'s four probes are **ARMED** (`a1-02` armed 2026-08-24; `a2-01`/`a2-02` armed since T287
deleted the closure), and `acc_gl_closure` is **0**, so each would POST two journal entries into the
**standing** tenant. **A posted journal entry cannot be deleted.** Read
`.softhouse/capture/t287-closure-refusals/req/` — never POST from it. T327's brief prohibits it explicitly and
requires the standing tenant's counters recorded before and after: `acc_gl_journal_entry` 60/maxid 64,
`acc_gl_closure` 0, 26 distinct transaction ids, `m_portfolio_command_source` 352, `m_loan` 7, `m_office` 1.

## Pause reason

**None — work is in flight.** If this file is still the newest state and nothing is running, the fire was
killed mid-batch: treat every task above as `needs_retry`, not `in_progress`, and check each branch for
rescued WIP with `git log --oneline main..softhouse/<TASKID>-*` before re-dispatching. Note the case
convention: branches are **uppercase** `softhouse/T324-…`; a lowercase glob is the defect T308 caught and T312
closed with a `reference-transaction` hook.
