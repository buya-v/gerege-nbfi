# T177 — is the reference oracle's `StackOverflowError` a function of the cell's inputs alone?

Task `T177`, run `2026-08-21-run2-tierA-gl-accounting-A2`, gate **G-8**.

## The disputed observation

| run | cell | outcome |
|---|---|---|
| T159 | `T159-R600p0-N3000-B10001` — B = 10001 minor units, n = 3000, annual rate 600.0 | **observed**, `totalInterestAmount 846.70` |
| T169 | `T169-TWIN-R600p0-N3000-B10001` — the same three inputs | **threw** `java.lang.StackOverflowError` |

Same pinned image `sha256:e596339626bf…0459a`, same pinned Fineract `426a23544e84`, same seam
`EmbeddableProgressiveLoanScheduleGenerator` sha256 `bf397f0b…0714`, same production
`MathContext (19, HALF_UP)`. T169 recorded the disagreement and refused to guess a cause. T177
measures it.

## The rig

`src/CaptureT177.java` — a **trial runner**, not a capture rig. It **promotes nothing**. The `Case`
record, `prodDates(...)`, every input field and the seam call itself are copied verbatim from the
committed `CaptureT169Post.java`, so a trial here is the same evaluation T159 and T169 made. Throw
handling is the shared `.softhouse/capture/lib/ThrewOutcome.java` (T169): `catch (Throwable)`, the
fatal rule, and the same recorded field names. Money is integer minor units throughout
(`new BigDecimal(10001).movePointLeft(2)`); there is no floating-point literal, field or
intermediate anywhere in the rig.

The only deliberate differences from `CaptureT169Post`:

1. **Output shape** — one JSON object per line (JSONL), so 150 trials do not emit 450,000 period
   rows. Period rows are emitted only for the two calibration cells, where they are the evidence.
2. **A plan driver** — `single`, `repeat:K`, `warm:M:K`, `t159prefix:K`, `thread:BYTES:K`, `calib`.

`run-t177.sh` re-verifies the same preconditions as `run-t159.sh` / `run-t169.sh` (image id, pinned
commit + clean tree, seam byte-identity **and** literal digest, shared-lib digest) on every run, then
compiles **once** inside one throw-away `docker run --rm` and launches **many separate `java`
processes** inside it. Every matrix row with `RUNS > 1` is therefore that many genuinely **fresh
JVMs**, at the cost of a single `javac`. It does **not** abort on a non-zero java exit or non-empty
stderr, for T169's reason — a run that died is a result this probe is measuring — and both are
recorded per process in `out/*/run-index.txt` and classified separately by the analyzer.

It opens **no database connection**, starts **no Fineract server**, and touches none of the running
`fineract-*` containers. "The oracle" here is the Fineract reference implementation; Oracle Database
is a prohibited product in this program and appears nowhere in this work.

## Calibration — run before any conclusion was drawn

`calibrate_t177.py` reproduces the two committed pass-3g cells `T64-ZP-A` / `T64-ZP-B` and compares
**totals and every period row**, by extraction from `.softhouse/capture/out/capture-prod3g-raw.json`,
never by a retyped literal (P-46). Zero fields compared is an ERROR, not a pass (P-35).

## The matrices

| file | what it separates |
|---|---|
| `matrix-pilot.txt` | calibration + a cost measurement, before spending oracle time |
| `matrix-a.txt` | pure per-request nondeterminism vs position-in-JVM; and whether warming with a *different*, non-throwing cell is enough |
| `matrix-b.txt` | stack size (`-Xss`), thread identity (fresh thread per probe), true depth at overflow (`MaxJavaStackTraceDepth=0`), and the JIT (`TieredStopAtLevel=1`) |
| `matrix-c.txt` | the direct reconciliation: T159's committed case order, replayed |

## The analyzer

`analyze_t177.py` tallies **probe trials with denominators**, prints the outcome **as a function of
probe index within the JVM**, checks every observed probe against T159's committed
`totalInterestAmount` **extracted from the committed capture**, and enforces:

* **P-40** — each java process has an expected trial count derived from its plan; trials never
  reached because the JVM died are counted as `NOT-REACHED`, never folded into an outcome.
* **P-35** — zero trials parsed is an ERROR, not a clean run.
* Run-level anomalies (non-zero exit, non-empty stderr, missing footer) are reported **separately**
  and never folded into `observed` or `threw`.

## Evidence

Raw per-process stdout/stderr, the run index, the container console and the attestation for every
matrix are committed under `out/`. The findings are in
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md`.
