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

**Attribution is a CONVENTION this policy mandates, not a property of the schema. [Corrected by T371;
found by T367 as F1.]** T363 argued here that attribution is *total* because every row in
`m_portfolio_command_source` carries an `Idempotency-Key`. That argument is a **tautology and the strong
claim under it is false**:

- `idempotency_key` is a **`NOT NULL`** column, so "all rows carry one" could not have come out any
  other way [VERIFIED: T371, live, `information_schema.columns`].
- Fineract **mints** a key when the caller sends no header —
  `IdempotencyKeyResolver.resolve → …orElseGet(idempotencyKeyGenerator::create)`,
  `create()` = `UUID.randomUUID().toString()` [VERIFIED: T371, `IdempotencyKeyResolver.java:36`,
  `IdempotencyKeyGenerator.java:25-29`, pinned `426a23544`].
- So most keys in this tenant name **nothing**. Re-derived by T371 with two independent classifiers
  that agree — UUID shape, and "carries a task token" — **20 of 359 rows name a task, 7 of them above
  the floor** [`.softhouse/capture/t371-t367-conditions/sql/q3-key-naming.sql`, output in that
  directory's `out/`]. Every remaining row is **unattributable forever**.

**This does not break the instrument, and knowing why matters.** A minted UUID matches no row in
`PROBES.tsv`, so an unrecorded probe is starred UNATTRIBUTED and the run exits 1. The instrument is
**fail-closed on the absence of a record**, which is the design; it was never fail-closed *because* the
column is populated. A prober who forgets the header still goes red — and is then unidentifiable, which
is the standing predicament of row 352.

So: a command names the task that fired it **if and only if the task named itself in the key**, which is
the obligation in `reference-oracle.md` POLICY § 2 and the reason that obligation is written down.

## Files

| path | what |
|---|---|
| `PROBES.tsv` | the floor and the attribution registry. **Append to this when you probe.** |
| `instruments/oracle-state-baseline.sh` | the derivation. Read-only. |
| `instruments/casualty-sweep.sh` | where I looked for things the movement invalidated: population, engine, flags, **16** selectors. **Repaired by T371 (T367 F2).** It now reads `git grep`'s exit status, calibrates on a known positive **and** a known negative, and has its own exit contract — `0` every selector ran / `2` no corpus / `3` calibration failed / `4` a selector DID NOT RUN. It still gates nothing; the exit code says whether the sweep is *admissible*, never whether a casualty exists. Red-driven both ways in `.softhouse/capture/t371-t367-conditions/out/DRIVE-SWEEP-FAILCLOSED.txt` |
| `CASUALTIES.md` | what the movement actually broke, what it did not, and the `t305`/`t327` decision |
| `out/GREEN-baseline.txt` | the instrument's green run, exit 0 |
| `out/RED-1-no-attribution.txt` | red drive: floor with no attribution rows → exit 1 |
| `out/RED-2-unreachable.txt` | red drive: database unreachable → exit 2, and NOT confused with exit 1 |
| `out/RED-3-wrong-interpreter.txt` | **the version that ADMITTED `sh`** — kept as the transcript of the defect |
| `out/RED-3b-wrong-interpreter-fixed.txt` | red drive: `sh` → exit 3 |
| `out/RED-4-one-unrecorded-probe.txt` | red drive: **one** forgotten probe, not a wholesale loss → exit 1, names it |
| `out/CASUALTY-SWEEP.txt` | the sweep output **as T363 ran it**. A dated transcript of the pre-repair instrument; deliberately not regenerated here. T371's post-repair run is `.softhouse/capture/t371-t367-conditions/out/CASUALTY-SWEEP-T371.txt` |
| `out/BAR-conformance.txt` | `bash .softhouse/conformance.sh` after the movement — PASS, exit 0 |

Four red drives, because a guard nobody has watched fail enforces nothing — and the third one caught a
real defect in this instrument before it was committed (see `CASUALTIES.md` § E).
