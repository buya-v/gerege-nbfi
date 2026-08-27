# T39 — proving `run-periodratio.sh` is failable

*An assertion suite that has never failed has not been tested* (`.softhouse/patterns.md`).
Seven deliberately-wrong runs were executed. **All seven exited non-zero and named the breach.**
Every transcript below is the script's real output.

| # | breach injected | how | exit | first line of the breach |
|---|---|---|---|---|
| N1 | wrong pin | `T39_EXPECT_COMMIT=000…0` | **1** | `BREACH: pinned checkout is at 426a2354…, expected 000…0` |
| N2 | **dirty** checkout | `T39_FINERACT_DIR` → a scratch repo with an uncommitted edit | **1** | `BREACH: pinned checkout is DIRTY:  M a.txt` |
| N3 | wrong image id | `T39_EXPECT_IMAGE=sha256:111…1` | **1** | `BREACH: image id is sha256:e5963396…, expected sha256:111…1` |
| N4 | **seam-class drift** | one comment line appended to `src/EmbeddableProgressiveLoanScheduleGenerator.java`, then restored | **1** | `93d92 < // deliberate drift …` then `BREACH: seam class under src/ has DRIFTED from the pinned original` |
| N5 | wrong **ambient** MathContext | `-Dt39.tenantRoundingModeOrdinal=1` (DOWN) | **1** | `BREACH: T39-CAL: effective MoneyHelper MathContext is 'precision=19 roundingMode=DOWN', expected 'precision=19 roundingMode=HALF_UP'` (×16 cases) |
| N6 | wrong **threaded** precision | `-Dt39.mathContextPrecision=12` | **1** | `BREACH: T39-CTL-Q0a: threaded precision 12, expected 19` (×15 cases) |
| N7 | wrong **threaded** rounding mode — the behavioural canary | `-Dt39.mathContextRoundingMode=DOWN` | **1** | `BREACH: T39-CAL: threaded rounding mode DOWN, expected HALF_UP` (×16 cases) |

N1–N3 and N5–N7 also fail the "a negative-test override was left set" assertion, which exists so
that a run whose flags were tampered with cannot pass even if every other check is satisfied.

Not separately injected, because the script's own successful run demonstrates the code path:
non-zero container exit (5), non-empty stderr (6), unparseable JSON (7) and null observations (8)
are each asserted on every run and each names its own breach; the classpath check (12) reports
`ZERO Oracle Database / MySQL / MariaDB entries` from a real scan of the 348 classpath entries.

## The behavioural canary, and the surprise in it

`patterns.md` asks for a canary that changes **money**, not a configuration row, because
*a configuration row proves what was configured, not what arithmetic is actually in force*.
Running the canary produced a result worth recording in its own right.

| axis moved | assertion fires | **does the emitted money move?** |
|---|---|---|
| tenant `RoundingMode` ordinal 4 → 1 (N5) — the **ambient** `MoneyHelper` context | yes, on all 16 | **NO. 0 of 16 observed blocks differ, byte for byte** |
| threaded `MathContext` precision 19 → 12 (N6) | yes, on 15 (T39-CAL already runs at 12) | **NO. 0 of 16 observed blocks differ** |
| threaded `MathContext` rounding mode HALF_UP → DOWN (N7) | yes, on all 16 | **YES. 15 of 16 blocks move**, e.g. `T39-CTL-Q0a` total interest `76723.70` → `76723.65`; `T39-CAL` `2.05` → `2.02`; `T39-P0-D` `18659151.45` → `18659151.44` |

So on this seam and on these sixteen shapes:

1. **The arithmetic in force is the THREADED `MathContext`, not the ambient `MoneyHelper` one.**
   Setting the tenant rounding mode to `DOWN` changed `MoneyHelper.getMathContext()` to
   `precision=19 roundingMode=DOWN` on the oracle's own testimony and changed **nothing** in the
   output. The ambient context is still worth attesting — it is the oracle's own witness that the
   tenant was configured as ratified — but it is **not** evidence about the arithmetic that
   produced these numbers. Only the threaded context is.
   [VERIFIED: `out/t39-neg5.json` vs `out/t39-periodratio.json`, all 16 `observed` blocks byte-equal]
2. **Precision 12 and precision 19 are indistinguishable on these sixteen shapes.** That is a
   coverage statement about these shapes, not a general one: the rate factor is `setScale`d to
   the precision as a *scale*, and the residual is below one minor unit at these magnitudes.
   A shape that separates 12 from 19 is `TO_BE_CAPTURED`.
   [VERIFIED: `out/t39-neg6.json` vs `out/t39-periodratio.json`]

## Reproducing the negative runs

```sh
CAP=.softhouse/capture/periodratio
T39_EXPECT_COMMIT=0000000000000000000000000000000000000000 T39_OUT_PREFIX=t39-neg1 bash $CAP/src/run-periodratio.sh; echo $?
T39_EXPECT_IMAGE=sha256:1111111111111111111111111111111111111111111111111111111111111111 \
  T39_OUT_PREFIX=t39-neg3 bash $CAP/src/run-periodratio.sh; echo $?
T39_JAVA_PROPS="-Dt39.tenantRoundingModeOrdinal=1" T39_OUT_PREFIX=t39-neg5 bash $CAP/src/run-periodratio.sh; echo $?
T39_JAVA_PROPS="-Dt39.mathContextPrecision=12"     T39_OUT_PREFIX=t39-neg6 bash $CAP/src/run-periodratio.sh; echo $?
T39_JAVA_PROPS="-Dt39.mathContextRoundingMode=DOWN" T39_OUT_PREFIX=t39-neg7 bash $CAP/src/run-periodratio.sh; echo $?
```

N2 needs a scratch git repo with an uncommitted change (never the pinned checkout — it is
read-only for this program); N4 needs a byte appended to the seam copy and then restored, which
`shasum -a 256` must return to
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`.

`out/t39-neg5.json`, `out/t39-neg6.json` and `out/t39-neg7.json` are kept as the evidence for the
canary table. N1–N4 fail before any payload is produced, by design.
