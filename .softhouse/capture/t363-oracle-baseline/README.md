# t363-oracle-baseline — the standing reference oracle's state, DERIVED

The oracle moved permanently on fire `20260828-140005` (T352, then T359). A journal entry has no
delete path, so the movement is forever. This directory is the machinery that stops that from being
discovered as an unexplained discrepancy two fires later.

**The canonical prose record is `.softhouse/reference-oracle.md`, § *The standing oracle MOVED* and
§ *POLICY — firing a probe at the SHARED reference oracle*.** This directory holds the instrument that
record points at, and the evidence behind it.

## Run it

```bash
bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh
```

Read-only — every statement it issues is a `SELECT`. It cannot move the thing it measures.

| exit | meaning |
|---|---|
| **0** | every row above the floor is attributed to a probe recorded in `PROBES.tsv` |
| **1** | **unattributed movement** — somebody wrote to the shared oracle without recording it; the orphaned rows are named |
| **2** | the tenant database was **unreachable**. Not a statement about the ledger, exactly as `conformance.sh` exit 2 is not a FAIL |
| **3** | wrong interpreter — you ran it with `sh` |

## The design, in one paragraph

**It grades attribution, not stillness.** The oracle is shared and probes are permanent, so *movement is
normal*; a check that refuses on movement fails closed forever, which is precisely the trap the `t305`
and `t327` rigs walked into. What is worth a red run is **movement nobody claimed**.

**It pins identities, never cardinals.** `PROBES.tsv` carries a floor expressed as **max ids on
append-only tables** — "row 64 was the last row before T352" is true forever — plus one attribution row
per deliberate write. Every count in the output is derived live on each run. Nothing here is a number a
future task must remember to update, because this program has been bitten by exactly that four times in
eight days: `capabilities-ledger.json` twice, `reference-oracle.md` three times, the driver's standing
baseline once.

**The registry's absence is what goes red.** A task that probes the oracle and does not append its rows
to `PROBES.tsv` makes the next run exit 1 with its own transaction ids printed. That is the enforcement,
and it is why the obligation is on the registry rather than on prose.

**Attribution is total because of a non-negotiable we already have.** `Idempotency-Key` is mandatory on
every money-movement POST, Fineract persists it on `m_portfolio_command_source`, and all 359 rows in
this tenant carry one [VERIFIED: T363, live]. So every command — **including every refusal** — names the
task that fired it, if the task named itself in the key.

## Files

| path | what |
|---|---|
| `PROBES.tsv` | the floor and the attribution registry. **Append to this when you probe.** |
| `instruments/oracle-state-baseline.sh` | the derivation. Read-only. |
| `instruments/casualty-sweep.sh` | where I looked for things the movement invalidated: population, engine, flags, 11 selectors |
| `CASUALTIES.md` | what the movement actually broke, what it did not, and the `t305`/`t327` decision |
| `out/GREEN-baseline.txt` | the instrument's green run, exit 0 |
| `out/RED-1-no-attribution.txt` | red drive: floor with no attribution rows → exit 1 |
| `out/RED-2-unreachable.txt` | red drive: database unreachable → exit 2, and NOT confused with exit 1 |
| `out/RED-3-wrong-interpreter.txt` | **the version that ADMITTED `sh`** — kept as the transcript of the defect |
| `out/RED-3b-wrong-interpreter-fixed.txt` | red drive: `sh` → exit 3 |
| `out/RED-4-one-unrecorded-probe.txt` | red drive: **one** forgotten probe, not a wholesale loss → exit 1, names it |
| `out/CASUALTY-SWEEP.txt` | the sweep output |
| `out/BAR-conformance.txt` | `bash .softhouse/conformance.sh` after the movement — PASS, exit 0 |

Four red drives, because a guard nobody has watched fail enforces nothing — and the third one caught a
real defect in this instrument before it was committed (see `CASUALTIES.md` § E).
