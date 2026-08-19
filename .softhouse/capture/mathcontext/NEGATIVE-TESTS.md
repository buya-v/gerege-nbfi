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

---

## CORRECTION BY T46 — what N4 actually proves (audit finding M-8)

**The section immediately below was wrong about which branch N4 fires, and the error mattered.**

`run-mathcontext.sh`'s payload-assertion block has a single `if` pair on the canary:

```python
must_throw = os.environ["EXPECT_CANARY_THROWS"] == "1"
if must_throw and not canary.startswith("THREW java.lang.IllegalStateException"):   # :157-160
    bad.append("the ambient-absence probe is VACUOUS: ...")
if not must_throw and canary.startswith("THREW"):                                    # :161-162
    bad.append("negative run: the canary DID throw when the run asserted it would not: ...")
```

N4 sets `T42_EXPECT_CANARY_THROWS=0`. So `must_throw` is **False**, and the branch that fires is
the second one — which is exactly what N4's own transcript records
(`out/negative/n4-canary-assertion-inverted.txt`: *"BREACH: negative run: the canary DID throw
when the run asserted it would not…"*). **N4 proves the canary really does throw. It does NOT
exercise the vacuity guard**, and the vacuity guard is the one that makes E1 falsifiable.

**Until T46, the vacuity guard had never been exercised.** It now has:

| # | breach injected | how | exit | first line of the breach |
|---|---|---|---|---|
| **N7** | **the vacuity guard** | `src/t46-negative-vacuity.sh` extracts the SHIPPED assertion block out of `run-mathcontext.sh` at run time (so the guard exercised is the committed one, not a copy that could drift) and runs it against a payload whose `ambientCanary` has been rewritten from `THREW java.lang.IllegalStateException: …` to `precision=19 roundingMode=HALF_UP`, with `EXPECT_CANARY_THROWS` left at its default **1** | **1** | `BREACH: the ambient-absence probe is VACUOUS: MoneyHelper.getMathContext() on an uninitialised tenant returned 'precision=19 roundingMode=HALF_UP' instead of throwing IllegalStateException. Every ABSENCE case is meaningless.` |
| **N8** | **the Path B slot assertion** (finding M-6) | `src/t46-assert-pathb-slot.sh` rewrites the `astore` that receives `getMathContext`'s result to an unused slot in a copy of the `javap` transcript | **1** | `BREACH: A2 assembleLoanScheduleFrom: slot 99 stored from getMathContext @31 is never loaded into an invoke whose descriptor takes a MathContext` (6 breaches in all) |
| **N9** | **the M-5 identity check** | `src/t46-negative-identity.sh` moves one money cell by one minor unit in the re-emission | **1** | `BREACH: T42-CAL /observed/periods[1]/interest: '0.58' -> '0.59'` |

Each of the three is paired with a **control leg on the uncorrupted artefact that must exit 0**,
so what is shown is that the guard *discriminates*, not merely that it can be made to complain.

N7 additionally proves it corrupted nothing else: **140,978 observed cells identical** between
the source payload and the canary-corrupted one.

Transcripts: `out/negative/t46-n7-vacuity-guard.txt`,
`analysis/t46-pathb-slot-assertion-output.txt`,
`out/negative/t46-n9-identity-check-failable.txt`. A fourth,
`out/negative/t46-n8-identity-check-rejects.txt`, is the transcript of the first re-emission run
being **rejected** by the identity check.

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

**N4 inverts that expectation and confirms the canary really does throw** — it fires the
*opposite* branch of the same `if`, not the vacuity guard quoted above. The vacuity guard itself
is exercised by **N7** (see the T46 correction section above); the original wording of this
paragraph, which said N4 fired the vacuity guard, was wrong. Between N4 and N7, "the shape
generated fine, so the ambient was never read" is no longer an unfalsifiable claim: N4 shows the
canary throws, N7 shows the run would be failed if it ever stopped throwing.

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
