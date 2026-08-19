# T39 — provenance of the periodRatio observation captures

## What these are

Sixteen schedules **observed** from the pinned reference oracle (Fineract) through the Path-A
embeddable seam, taken to settle **P0-T34-1** — whether the `rateFactorTillPeriodDueDate`
multiplier is `periodRatio` (`ProgressiveEMICalculator.java:1404-1413`) or `RepaymentEvery`
(what DEC-1 §4.3.2 and `nexus/internal/apps/loanschedule/contract/contract.go:1455-1459` say) —
and to grade `calculatePeriodRatio`'s month-end special case (`:1426-1436`) deliberately rather
than incidentally.

## RAW OBSERVED FORM ONLY. Nothing is promoted.

**Gate G-1 is open and DEC-1 is UNRATIFIED.** The contract *shape* is precisely what is being
ratified, so storing a capture contract-shaped would beg the question this whole exercise
exists to answer. Therefore:

- everything here is stored in the harness's own raw JSON shape, with the oracle's own log
  lines kept verbatim beside it;
- **nothing is promoted to the parity vector store**, and no file here is a golden vector;
- no DEC-1 field name, type or ordering is assumed by the storage format;
- `.softhouse/reference-oracle.md`, `.softhouse/patterns.md`, `docs/adr/**` and `nexus/**` were
  **not edited by this task**. A sibling worker (T38) is revising DEC-1 to revision 7
  concurrently; this task reports observations to it and does not act on them.

## Observation vs re-derivation vs transcription

The three are kept apart everywhere in this directory, because conflating them is how a
plausible invented number reaches a vector store.

| kind | where it lives | how to tell |
|---|---|---|
| **OBSERVED** — emitted by the live pinned oracle | `out/*.json` | produced only by `src/run-periodratio.sh`; the harness `CapturePeriodRatio.java` computes nothing and asserts nothing |
| **RE-DERIVED** — computed by a model that never contacted an oracle | `analysis/readings.py`, `analysis/t34_model.py`, `analysis/t34_periodratio.py`, `analysis/select_shapes*.txt` | every one of those files says so at the top |
| **TRANSCRIBED** — copied from a source literal or a committed record, with `file:line` | `analysis/controls.py` | each expectation carries its `file:line` in a comment beside it |

**Nothing in this directory is synthesised, extrapolated or interpolated.** Behaviour that was
not captured is named as not captured in the handoff, not filled in.

## Lineage of the analysis models

`analysis/t34_model.py` and `analysis/t34_periodratio.py` are **byte-identical copies** of
`.softhouse/reviews/t34-probe/t34_model.py` and `.../t34_periodratio.py`, taken so this
directory is self-contained; their sha256s are in `ATTESTATION.md` §8 and the copies were
`diff`-ed clean against the originals before use. They are T34's transcriptions — one of DEC-1
revision 6 from its text alone, one of `calculatePeriodRatio`/`calculateSeedDate` from the
pinned source. `analysis/readings.py` adds one reading (R3: the same routine with the month-end
special case omitted) behind a `MARKED EDIT` comment, and a full-cell renderer.

Two independent cross-checks that the copies behave as T34's did, both re-derivations:

- T34 §1.4's named candidate shape re-derives to total interest **74,607.33** (DEC-1 as written)
  vs **76,984.00** (pinned source) here, exactly as T34 published.
- T34 §1.4's worst-gap shape re-derives to **18,260,183.72** vs **18,659,151.45**, gap
  **MNT 398,967.73**, exactly as T34 published.

## Money discipline

Integer minor units and exact decimal strings end to end. The harness renders every amount with
`BigDecimal.toPlainString()`; the analysis uses Python `decimal` at explicit contexts. There is
no `double`, `float`, `Double`, `Float`, `parseDouble` or `doubleValue()` on any amount path in
`src/`, and no `float` literal or `float()` call on a money path in `analysis/`.

## Database

This seam reaches no database at all — Path A runs in process, and no PostgreSQL connection is
opened. The PostgreSQL-only rule is unaffected; `run-periodratio.sh` additionally proves the
oracle's classpath carries **zero** Oracle Database / MySQL / MariaDB entries.

## Container discipline

Every container was `docker run --rm`, mounting only `.softhouse/capture/periodratio`. The
shared `fineract-fineract-1` / `fineract-db-1` containers — owned by a sibling worker this fire
— were **not** started, stopped, reconfigured or written to. `.softhouse/capture/src/`,
`.softhouse/capture/dec1-binding/`, `.softhouse/capture/out/`, `.softhouse/capture/pathb/` and
`.softhouse/capture/charges/` were not written to or compiled from; this task took **its own**
copy of the seam source and proved it byte-identical to the pinned original.
