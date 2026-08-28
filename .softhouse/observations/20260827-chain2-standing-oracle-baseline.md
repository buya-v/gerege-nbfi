# Standing reference-oracle baseline — fire `20260827-230001`, chain iteration 2

Measured by the **driver**, independently of `T327`, at the moment `T327` was dispatched. It exists so
that T327's "I did not write to the standing oracle" claim is **checkable against a figure T327 did not
supply**, rather than against T327's own before-reading. A capture task attesting to its own baseline is
attesting to nothing.

## Command, verbatim

```
docker exec fineract-db-1 psql -U postgres -d fineract_gerege -At -c "…"
```

Note the database name: tenant id `gerege` maps to database **`fineract_gerege`**, not `gerege`
(recorded in `reference-oracle.md`; a script written against `gerege` errors).

## Observed

| counter | value |
|---|---|
| `acc_gl_journal_entry` | **60**, maxid **64** |
| `acc_gl_closure` | **0** |
| distinct `transaction_id` | **26** |
| `m_portfolio_command_source` | **352** |
| `m_loan` | **7** |
| `m_office` | **1** |

**Every figure is identical to the one T305 left and the one this fire opened on.** The ledger has not
moved across chain iteration 1's container bring-up, its capture work, or the iteration boundary.

## Why `acc_gl_closure = 0` is the dangerous number here

It is the **arming condition** for two of T287's four probes. With no closure row present, `a2-01` and
`a2-02` no longer refuse — they would be **ACCEPTED**, and each would POST two journal entries that
**cannot be deleted**. `a1-02` armed on 2026-08-24 by calendar. Only `a1-01` is still safe, and it arms
2026-12-31.

So the correct reading of `acc_gl_closure = 0` is not "clean" but **"three of four probes are live"**.
`.softhouse/capture/t287-closure-refusals/req/` must never be POSTed. T327's brief prohibits it by name
and requires its own requests to be new files under its own capture directory.

## What T327 must show against this

T327 was dispatched to capture the **accepting** side of the closure and business-date boundaries
(T295 backlog B-1 and B-2) on a **throwaway instance on port 8444**, never against 8443. Its handoff must
reproduce all six counters after its run. **Any movement in any of them is a finding, not a rounding
error** — and the one to watch hardest is `acc_gl_closure`, because B-1 requires a `GLClosure` to exist
and the only correct place for that row is the throwaway tenant.
