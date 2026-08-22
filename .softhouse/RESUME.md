# RESUME manifest — gerege-nbfi Fineract→Go migration

**IN FLIGHT — DO NOT TAKE THE LOCK.** Local fire `20260822-060013` is LIVE with workers dispatched.
This manifest is published BEFORE the first worker was spawned, per **P-85** (the 2026-08-22 double-holder
incident: the previous local fire committed its in-flight state and never pushed it, so a cloud fire read a
`HEAD` saying "closed clean, zero live workers" while five workers were running, took the lock on the 6 h
staleness rule, and its own workers' branches were destroyed with its sandbox).

## Fire facts

- Host: Buyan's Mac. **Reference oracle (Fineract): REACHABLE** at `https://localhost:8443`. PostgreSQL up.
  Pinned Fineract checkout `426a23544`. No prohibited engine port open.
- Lock taken at `2026-08-22T06:00:13Z`, pushed at `c0e88c6` before any dispatch.
- **Baseline BAR run by the driver at `c0e88c6`, on the live oracle, before dispatch:**

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0)
  46 parity vectors · 7884 cells compared
  LEDGER  4 parity · 2 oracle-refusal · 21 money cells   (all 9 census pins == pinned)
  fail-open frontier  11 == pinned 11
  6/6 deliberately-wrong ledger implementations KILLED through the harness
  vector store  13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

Log committed at `.softhouse/capture/bar-baseline-20260822-060013.log`.

## DISPATCH RECORD — five workers, worktree-isolated, opus

| Task | Branch | Scope (files_hint) |
|---|---|---|
| **T255** | `softhouse/T255-dec2-rev8` | `docs/adr/DEC-2-gl-accounting-adapter.md`, `.softhouse/capture/t255-dec2-rev8/` |
| **T253** | `softhouse/T253-harness-portability` | `.softhouse/conformance.sh`, `.softhouse/bin/go-env.sh`, `.softhouse/capture/t253-portability/` |
| **T250** | `softhouse/T250-tenant-attestation` | `.softhouse/capture/lib/`, `.softhouse/capture/t250-tenant-attestation/` |
| **T259** | `softhouse/T259-verdict-predicate` | `.softhouse/capture/t229-g8-site3/`, `.softhouse/capture/t256-verdict-predicate/` |
| **T164** | `softhouse/T164-analyze7-float-guard` | `.softhouse/capture/tierA-a2/` |

Paired independent reviewers registered at dispatch (plan gate rule 1): **T254**→T253, **T260**→T255,
**T261**→T250, **T262**→T259, **T263**→T164.

**Contention honoured:** only ONE task in this batch touches `conformance.sh` (T253). `T257`, `T258`, `T226`,
`T235`, `T160`, `T192`, `T195` all contend for it and were deliberately held back. `T145` (`.softhouse/capture/`
whole) contends with T250/T164/T259 and was held back. `T174` contends with T164 and was held back.

**Deliberate collision, briefed as such:** T253 edits `conformance.sh` in the same fire that T255 must land
DEC-2 revision 8 with correct `conformance.sh` citations. T255 was told this explicitly. If revision 8's
citations rot because T253 merged, that is not bad luck — it is proof the citation-rot MECHANISM fix failed,
which is the load-bearing half of T255's brief. T260 grades it on exactly that.

## If this fire died here

Every task above is `in_progress` in `tasks.json` with its branch recorded. A worker killed mid-flight is
**not** `in_progress` — the next holder must mark it `needs_retry` with
`note: worker killed mid-flight; completeness unverified`, and check `git branch --list 'softhouse/*'` and
`git ls-remote --heads origin` for rescued WIP before re-dispatching from scratch.

## Gate state, unchanged by this dispatch

**G-14 OPEN** — DEC-2's opening banner is false in its ground. Recorded scope: **NOTHING BUT DEC-2 ITSELF**
(driver decision, independently confirmed by T249, merged `bfde578`). Go under `nexus/` remains permitted.
**G-4, G-5, G-8, G-10, G-12** also open; **G-4 and G-5 are hard `user` gates**. G-8 options (b)/(c) must not
be put to Buyan, unconditionally, with no expiry. The gate register at the top of `gates.md` is authoritative.
