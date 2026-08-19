# T42 — provenance and storage form

## RAW OBSERVED FORM ONLY. Nothing here is promoted.

Gate **G-1 is open** and **DEC-1 is unratified**. The contract *shape* is what is being ratified,
so a contract-shaped capture would beg the question. Everything under this directory is stored in
the shape the oracle emitted it, keyed by an opaque case id, with the inputs echoed beside it.
**Nothing is in the parity vector store and nothing should be moved there by this task.**

## What these captures ARE

Discrimination probes about **which `MathContext` governs which arithmetic step**, and a search
for a shape on which threaded precision 19 separates from 12. They answer a question about the
*provenance rule for attestations*, not about the loan schedule contract.

Specifically:

- The **matrix** cases (`T42-MX-*`) deliberately run at non-ratified ambient rounding modes
  (`DOWN`, `UP`) and non-ratified threaded modes (`DOWN`), and two of them at a non-MNT-shaped
  currency (0 decimal places with `inMultiplesOf`). **None of these is production-representative
  and none may ever be promoted as a parity vector.** They exist to make an ambient read visible.
- The **absence** cases (`T42-MX-*-D`) run with `MoneyHelper` deliberately uninitialised. Two of
  them produce no schedule at all, only a stack trace. That stack trace *is* the finding.
- The **precision** cases (`T42-PREC-*`, `T42B-PREC-*`) run at threaded precision 12 and 8, which
  `CLAUDE.md` already records as discrimination probes rather than parity vectors, and at
  principals up to MNT 100,000,000,000,000 chosen to expose the arithmetic rather than to model a
  product.
- The **wiring** cases (`T42B-PA-*` / `T42B-PB-*`) differ only in where the `MathContext` came
  from. The `PB` family reproduces Path B's *wiring* on Path A's *transport*; it is **not** a Path
  B capture and must not be labelled one.

## The only cases that are production-representative

`T42-CTL-Q0a`, `T42-CTL-1`, `T42-CTL-P0A`, `T42-CTL-MEB` — the four reproduction controls, at the
ratified `(19, HALF_UP)` on MNT with 2 decimal places. They exist to prove this harness is not the
variable, and every one of them **already exists** in the committed corpus from T37 and T39.
Promoting them would duplicate, not add.

`T42-CAL` is the rig calibration at `(12, HALF_UP)` against a shipped USD test literal. It is
**never** a parity vector, exactly as T37's and T39's calibrations are not.

## Where the numbers came from

Every published number is either

- **observed** from a live run against the pinned oracle
  (commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`, image
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`), or
- **transcribed** from a source literal or a committed artefact, with `file:line` given.

Nothing is synthesised, extrapolated or interpolated. Uncovered behaviour is `TO_BE_CAPTURED` and
is listed in the handoff's coverage section.

## Directory discipline

This task wrote **only** `.softhouse/capture/mathcontext/**` and
`.softhouse/handoff/T42-mathcontext-inforce.md`. It read `.softhouse/capture/periodratio/`,
`/out/`, `/pathb/` and `/dec1-binding/` and wrote to none of them. `docs/adr/**` and `nexus/**`
were not touched (T41 owns them this fire). `.softhouse/reference-oracle.md`,
`.softhouse/patterns.md`, `.softhouse/tasks.json`, `.softhouse/program.json` and
`.softhouse/gates.md` were read and **not** edited; the corrections they need are reported in the
handoff for the orchestrator to apply.

The seam source under `src/` is this task's **own copy**, proved byte-identical to the pinned
original by `diff` and by sha256
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — the same digest T37 and T39
recorded independently. Sibling capture directories were never compiled from.
