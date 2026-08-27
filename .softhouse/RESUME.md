# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260827-230001` — IN FLIGHT — 6 WORKERS DISPATCHED, RECORD PUSHED BEFORE THE FIRST SPAWN

> **P-85 compliance:** this manifest, the lock, and the six `in_progress` rows in `tasks.json` were
> committed and **pushed before any worker was spawned**. If you are reading this and no fire is
> running, these six are **corpses, not workers**. Check each branch
> (`git log --oneline main..<branch>`) and demote anything empty to `needs_retry`.

---

## WHAT THIS FIRE FOUND AT PRE-FLIGHT

### The previous fire never got a turn — nothing advanced, and nothing was lost

Fire `20260827-200001` exited `rc=1` with **0 model turns**: the `seven_day` rate limit rejected it
outright (`resetsAt=1787835600`). The wrapper banner it left on the old manifest is accurate — the
window was spent on nothing. **This is not a crash and there is no WIP to rescue from it.**

`ready-tasks.py` at this fire's pre-flight: **0 in progress, 29 READY, 4 blocked, 0 open contract
gates, 0 dependency edges resolving nowhere.** The eight branches dispatched by fire
`20260823-140001` are gone or empty; this fire re-dispatches six of them as **fresh attempts, not
resumes**, and does not claim their earlier work exists.

### THE REFERENCE ORACLE WAS DOWN AT FIRE START, AND THIS FIRE BROUGHT IT UP

The fire opened with the oracle **UNREACHABLE** at
`https://localhost:8443/fineract-provider/actuator/health`, Docker running, Postgres healthy. Per the
fire contract that is **T1's job, not a park reason**. Measured before starting anything:

| fact | value |
|---|---|
| running before | `fineract-db-1` (`postgres:18.3`) **up 5 h, healthy**, `0.0.0.0:5432` |
| missing | `fineract-fineract-1` — the app container was simply not running |
| compose used | `/Users/buv/fineract/docker-compose-postgresql.yml` (**postgresql profile only**) |
| `FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME` | `org.postgresql.Driver` — asserted, not assumed |
| `FINERACT_HIKARI_JDBC_URL` | `jdbc:postgresql://db:5432/fineract_tenants` |
| prohibited-engine grep over the whole postgresql compose path | **clean** — no `ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql.cj`, `mariadb` |
| pinned Fineract commit | `426a23544` (verified in `/Users/buv/fineract`) |

The mariadb/mysql compose files were never invoked. See `.softhouse/reference-oracle.md` for the
connection facts recorded this fire.

---

## DISPATCHED THIS FIRE

| Task | Model | Branch | What it is |
|---|---|---|---|
| T309 | opus | `softhouse/t309-sigterm-reconcile-bypass` | The SIGTERM path bypasses T288's reconciler — the one case it was built for |
| T297 | opus | `softhouse/t297-review-t295` | INDEPENDENT review of T295 — attack the relational reframing |
| T298 | opus | `softhouse/t298-review-t256` | INDEPENDENT review of T256 — attack the self-locating activation line |
| T308 | opus | `softhouse/t308-review-t292` | INDEPENDENT review of T292 — attack the two theorems |
| T304 | opus | `softhouse/t304-evidence-destruction` | FU-T284-3: `rm -rf` over committed evidence is a four-instrument property |
| T299 | opus | `softhouse/t299-t256-namespace-collision` | `t256-*` capture namespace collision + a lint run that dirties tracked evidence |

**Held back deliberately, for file-overlap serialisation** (not blocked, not parked):
`T301` and `T302` both edit `.softhouse/bin/fire-program.sh`, which **T309 is rewriting** this fire.
`T303` and `T305` both edit `.softhouse/conformance.sh`. `T306` overlaps `T305` on
`nexus/internal/apps/ledger/`. These go out in a later batch this fire or the next one.

| T305 | opus | `softhouse/t305-openingbalance-accepting-side` | F-T296-2: the accepting-side opening-balance capture — **the oracle-dependent task** |

**T305 was held back until the health probe actually returned 200**, not dispatched on the assumption
that the bring-up would work. It went out at +80 s once `{"status":"UP"}` was observed. Its brief's date
claims are **stale and dangerous** — it says *"a1-02 arms 2026-08-24, TOMORROW"* and **today is
2026-08-27** — so the worker was told explicitly to re-measure the arming state with the expiry guard
rather than reason from any date in its own brief. `acc_gl_closure` is **0**, so a2-01/a2-02 would POST
two journal entries each if fired; the worker is told not to fire them.

## Pause reason

None yet — fire in flight. If this section still says this and no fire is running, the fire died
without reaching STEP 5.5 and every row above is a corpse.
