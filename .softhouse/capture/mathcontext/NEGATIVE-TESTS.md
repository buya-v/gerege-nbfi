# T42 — proving the recipes and the control suite are failable

*An assertion suite that has never failed has not been tested* (`.softhouse/patterns.md`).
Six deliberately-wrong runs were executed by `src/run-negative-tests.sh`.
**All six exited non-zero and named the breach.** Transcripts: `out/negative/*.txt`.

| # | breach injected | how | exit | first line of the breach |
|---|---|---|---|---|
| N1 | wrong pin | `T42_EXPECT_COMMIT=000…0` | **1** | `BREACH: pinned checkout is at 426a2354…, expected 000…0` |
| N2 | wrong image id | `T42_EXPECT_IMAGE=sha256:111…1` | **1** | `BREACH: image id is sha256:e5963396…, expected sha256:111…1` |
| N3 | **seam-class drift** | one comment line appended to `src/EmbeddableProgressiveLoanScheduleGenerator.java`, then restored from the pinned original | **1** | `BREACH: seam class under src/ has DRIFTED from the pinned original -- the run would not have executed the oracle's code` |
| N4 | **the absence probe's own guard, inverted** | `T42_EXPECT_CANARY_THROWS=0` | **1** | `BREACH: negative run: the canary DID throw when the run asserted it would not: 'THREW java.lang.IllegalStateException: Rounding mode is not initialized for tenant: t42_canary_never_initialised'` |
| N5 | **the wiring, broken** | `-Dt42.breakWiring=true` silently turns the `PATH_B_AMBIENT_SOURCED_MC` cases into Path A cases | **1** | `BREACH: T42B-PB-ord1: PATH B wiring must hand the generator the AMBIENT context; ambient 'precision=19 roundingMode=DOWN' but effective 'precision=19 roundingMode=HALF_UP'` |
| N6 | **the control suite** | `controls.py` pointed at a payload with `T42-CAL.totalInterestAmount` changed `2.05 → 2.06` | **1** | `MISMATCH  C1 T42-CAL.totalInterestAmount: expected '2.05', observed '2.06'` |

N3 restored the seam byte for byte from the pinned original and the script re-asserts the digest
returned to `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`; the transcript
records `before` and `after`.

Not separately injected, because a passing run exercises the code path and each names its own
breach: non-zero container exit, non-empty stderr, unparseable JSON, a case echoing a threaded
context other than the one its id declares, a case echoing an ambient reading inconsistent with
its tenant ordinal, and the classpath driver scan (which reports `ZERO Oracle Database / MySQL /
MariaDB entries` from a real scan of the 348 classpath entries).

---

## N4 is the one that matters, and here is why

The central experiment in T42 is an **absence** probe: a tenant is put into
`ThreadLocalContextUtil` but `MoneyHelper.initializeTenantRoundingMode` is never called for it, so
any read of the ambient context throws. If the schedule still generates, the ambient context was
provably never consulted.

That argument is worth exactly nothing if the read does not actually throw. So the harness runs
an explicit canary first —

```
"ambientCanary": "THREW java.lang.IllegalStateException: Rounding mode is not initialized for tenant: t42_canary_never_initialised"
```

— and `run-mathcontext.sh` **fails the whole run** if the canary ever stops throwing:

> `BREACH: the ambient-absence probe is VACUOUS: MoneyHelper.getMathContext() on an uninitialised
> tenant returned … instead of throwing IllegalStateException. Every ABSENCE case is meaningless.`

N4 inverts that expectation and confirms the guard fires. Without N4, "the shape generated fine,
so the ambient was never read" would be an unfalsifiable claim.

## N5 is the second: the wiring assertion

`run-mathcontext2.sh` asserts that a Path B-wired case hands the generator a `MathContext`
**equal to the ambient reading** and a Path A-wired case hands it its own `(19, HALF_UP)`.
`-Dt42.breakWiring=true` makes the Path B cases construct their own context instead. The
assertion caught it on the first non-`HALF_UP` tenant. So the side-by-side wiring result in
`analysis/discriminate2-output.txt` is not an artefact of the two families being labelled
differently — the labels are checked against the object actually handed to the generator.

## Reproducing the negative runs

```sh
bash .softhouse/capture/mathcontext/src/run-negative-tests.sh
```

It prints one line per leg and exits 1 if **any** leg fails to fail. Recorded result:

```
legs that correctly failed: 6 ; legs that did NOT fail (bad): 0
```
