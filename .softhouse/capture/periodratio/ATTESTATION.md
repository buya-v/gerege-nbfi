# T39 — attestation for the periodRatio observation captures

Every claim below was executed on the local fire of **2026-08-19** and is reproduced by
`REPRODUCE.md`. An unattested capture is not admissible; this is that attestation.

## 1. Reference oracle identity

| Fact | Value | How it was checked |
|---|---|---|
| Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | `git -C /Users/buv/fineract rev-parse HEAD` — matches `.softhouse/reference-oracle.md`'s pin; asserted by `run-periodratio.sh` |
| Pinned checkout clean | yes | `git -C /Users/buv/fineract status --porcelain` → empty; asserted |
| Image tag | `fineract:latest` | |
| Image id | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | `docker image inspect`; asserted, and the container is launched **by image id**, not by tag |
| Image created | `2026-08-17T11:29:56.52027346Z` | `docker image inspect` |
| `/app/fineract-provider.jar` sha256 | `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9` | `sha256sum` inside a throwaway container (`out/t39-periodratio-oracle-identity.txt`) |
| **the jar's own `git.properties`** | `git.commit.id=426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.commit.id.describe=1.15.0-273-g426a235`, `git.build.version=1.16.0-SNAPSHOT`, `git.branch=develop`, `git.commit.time=2026-08-12T12:59+0000` | read from inside the jar — the **binary's own** testimony that it was built from the pin |
| **`git.dirty`** | **`false`** | same file — the jar was built from a clean tree |
| Capture path | **Path A — embeddable seam, in-process** | `docker run --rm`; no server started, no PostgreSQL contacted, no network needed |

## 2. Seam-class integrity — the precondition that would invalidate everything

```
diff .softhouse/capture/periodratio/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/\
org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```

**No output — byte-identical.** sha256
`bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`, which is also the digest
T37 recorded for the same file, from a different task and a different directory.

The copy under `src/` is **this task's own**. `.softhouse/capture/src/` and
`.softhouse/capture/dec1-binding/` (owned by other tasks) were not compiled from or written to.
The seam class is compiled from source because it is **not** bundled in
`/app/fineract-provider.jar`; everything else it calls comes from that jar.

This check is asserted on every run and was **proved failable** — see `NEGATIVE-TESTS.md` N4.

## 3. JVM identity

Read **inside** the container, entrypoint overridden so the image's JDWP agent does not bind
(`out/t39-periodratio-oracle-identity.txt`):

```
openjdk version "21.0.11" 2026-04-21 LTS
OpenJDK Runtime Environment Zulu21.50+19-CA (build 21.0.11+10-LTS)
OpenJDK 64-Bit Server VM Zulu21.50+19-CA (build 21.0.11+10-LTS, mixed mode, sharing)
```

The capture program echoes the same identity into its own payload: `javaVersion 21.0.11`,
`javaVmVersion 21.0.11+10-LTS`, `javaVmName OpenJDK 64-Bit Server VM`,
`javaVendor Azul Systems, Inc.`, `jvmFileEncoding UTF-8`.

**JVM flags:** the capture JVM is launched with **no `-D` flags at all** on a capture run
(`java -cp … CapturePeriodRatio`; `$T39_JAVA_PROPS` is empty and the payload records
`negativeTestTenantRoundingModeOrdinalOverride: null`,
`negativeTestMathContextPrecisionOverride: null`,
`negativeTestMathContextRoundingModeOverride: null`, each of which is asserted).
**`jvmUserTimezone` came back `null`**, not `UTC`: overriding the image entrypoint means
Fineract's own `-Duser.timezone=UTC` is not applied. Recorded rather than hidden. It is inert
for these captures — every date in request and response is an explicit civil date — but any
future capture of behaviour that depends on "today" must re-establish the zone explicitly. Each
case does pin a tenant timezone of `Asia/Ulaanbaatar` (`inputs.tenantTimeZone`).

## 4. The `MathContext` actually in force, as the oracle itself reports it

`MoneyHelper.PRECISION` read **from the running oracle** (not from source): **19**
(`moneyHelperPrecisionConstant` in the payload). Asserted.

Two independent witnesses to the mode, both from the oracle rather than from this harness:

1. **The oracle's own SLF4J log**, `out/t39-periodratio-log.txt` — sixteen lines, one per case:
   `Initialized rounding mode for tenant '<id>': HALF_UP`. **16 of 16** are `HALF_UP`
   (`RoundingMode` ordinal 4, the ratified Gerege mode). Asserted, count and value.
2. **`MoneyHelper.getMathContext()`**, echoed per case into `inputs.ambientMoneyHelperMathContext`:
   `precision=19 roundingMode=HALF_UP` on **all sixteen**. Asserted.

**Threaded `MathContext`:** `(19, HALF_UP)` on fifteen of sixteen cases, asserted per case. The
sixteenth, `T39-CAL`, is threaded at `(12, HALF_UP)` **deliberately** — it is the rig calibration
against the shipped test literal, is labelled as such in the payload, is the sole named exception
in the assertion script, and **can never be a parity vector**.

**A caveat this attestation states rather than glosses.** The *ambient* `MoneyHelper` context and
the *threaded* context are two different things, and on this seam only the threaded one moves the
money: with the tenant mode forced to `DOWN`, `MoneyHelper.getMathContext()` reported
`precision=19 roundingMode=DOWN` and **all sixteen observed blocks were byte-identical** to the
HALF_UP run, while forcing the *threaded* mode to `DOWN` moved **fifteen of sixteen**. Both are
asserted; only the second is a statement about the arithmetic. Evidence and figures:
`NEGATIVE-TESTS.md`.

## 5. Determinism

The whole capture was executed a **second time from a fresh container** after the final harness
edit. The JSON payload is **byte-identical**: `diff out/t39-periodratio.json
out/t39-determinism.json` → no output, and both hash to
`898435d89b58c1c61dd0b9d55b2bae38ab8fedd33f41d314ffea09b5c7e5b3a2`. The classpath listing is
byte-identical too. Only the log's wall-clock timestamps differ between runs.

A third datapoint: the capture had already been run before the harness gained its negative-test
hooks, and every `observed` block was identical then as well — the only diff was the one added
metadata line.

## 6. Calibration and reproduction controls — all four passed

Run by `analysis/controls.py`; output `analysis/controls-output.txt`. Expectations are
**transcribed** with `file:line`, never computed.

| Control | Expectation, and where it is transcribed from | Compared | Observed |
|---|---|---|---|
| **C1 calibration** `T39-CAL` — USD 100 / 6 × 7.0 % at `(12, HALF_UP)` | the shipped Fineract test literal, `EmbeddableProgressiveLoanScheduleGeneratorTest.java:44` (the MathContext), `:74-77` (totals), `:79-95` (rows) | 4 totals + 3 disbursement columns + 6 rows × 9 columns = **61 cells** | **all reproduced digit for digit.** NOT a parity vector — 12 is not the production precision |
| **C2 reproduction** `T39-CTL-Q0a` | committed observation **Q0a**, `.softhouse/reviews/t23-probe/t23-probe-output.txt:5-16` — a different harness, a different task | 4 totals + 2 disbursement columns + 6 rows × 6 columns = **42 cells** | **all reproduced digit for digit** |
| **C3 reproduction** `T39-CTL-1` | committed capture **T37-3-A**, `.softhouse/handoff/T37-dec1-binding-captures.md` item 3 | 4 totals + 6 rows × 6 columns = **40 cells** | **all reproduced digit for digit** |
| **C4 reproduction** `T39-ME-A` | committed capture **T37-3b-2**, same handoff, item 3b | the 3 scalars that handoff publishes for that shape | **all reproduced digit for digit** |

The harness is therefore not the variable.

## 7. No float, anywhere

Every amount is rendered with `BigDecimal.toPlainString()`. `src/CapturePeriodRatio.java`
contains no `float`, `double`, `Float`, `Double`, `parseDouble` or `doubleValue()` on any amount
path. `analysis/` uses Python `decimal` at explicit contexts only — no `float` literal and no
`float()` call on a money path. Amounts are compared as exact decimal strings, never numerically.

## 8. Classpath

348 entries, listed in `out/t39-periodratio-classpath.txt`, digest
`68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f` (identical on the determinism
re-run and on all three negative runs that got far enough to produce one).

**Zero** entries match `ojdbc|oracle|mysql|mariadb`, case-insensitively — asserted on every run.
No Oracle Database, MySQL or MariaDB driver is present. ("The oracle" in this program is the
Fineract reference implementation; Oracle Database is the prohibited product.)

## 9. File digests (sha256)

```
ba0cdcbf215930f3a017bb5e4a9c18c08a1d57b26a98ab2f7bdedb67d4dae77c  analysis/controls-output.txt
8d43bacc88ccc29985ae9fbc1cf46dbcb4b48d2c10fda079023d64fc09f59804  analysis/controls.py
3f620f24e7c4d0b831bb6521c503568680efd0b48f96a41a8a91c5691a8ca9bf  analysis/discriminate-output.txt
b094bcce2700455483671af773ce6e2a8a112e8a3b8c0dbe9a10ae87e180302c  analysis/discriminate.py
5c5c33a613a88dd66487674161a15319bf31d412293a8a367d46115a06d4e5a5  analysis/readings.py
102f5c79b96bc45641136cc1620f82ccc8bd55970ca5b4574b3f1c541bc9213a  analysis/select_shapes-output.txt
81881a14c9fd708a690735947d1b0e6cfafce638c4b39047e9f97069ed83664e  analysis/select_shapes.py
e83b7226c1d06b23f4e65c72fd351998537bdabc64319bc222796fc1f06cb8e9  analysis/t34_model.py
03fdf695df66dc1e599f66d72de43231ac728d6a4285137604de7ff763ee0d45  analysis/t34_periodratio.py
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t39-determinism-classpath.txt
0d1b1afa714cdcc59f8ca1c12c767b16f7d4631a6d2f49d1f788980378b0d6ad  out/t39-determinism-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t39-determinism-oracle-identity.txt
0b2f2720aa3205a9c20216b95de296e0ff65d989a11df5ce1c18422a68bfcc5a  out/t39-determinism-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t39-determinism-stderr.txt   (empty)
898435d89b58c1c61dd0b9d55b2bae38ab8fedd33f41d314ffea09b5c7e5b3a2  out/t39-determinism.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t39-neg5-classpath.txt
65cfd2cbb4a38c25629993ef00cab527b66d5ea0fb1dc561052d59c403f15ec6  out/t39-neg5-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t39-neg5-oracle-identity.txt
2580e965ad2fcab96466fe04e65f2987c477b47ecfdb231b21843ed9654adbb4  out/t39-neg5-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t39-neg5-stderr.txt   (empty)
242474f6e4cdd1d530b730d0b389e29c1a4a9cb5bddf2a0d7dacaa28b32ed469  out/t39-neg5.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t39-neg6-classpath.txt
3da98a0ac0e859466652a939ae1795c6a686a6525c45b33eee413bf4341ef1d0  out/t39-neg6-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t39-neg6-oracle-identity.txt
6f2397fc4c5cf309fa98d6105f1b7723f28a65d9a63ef193cb4496c70368d77e  out/t39-neg6-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t39-neg6-stderr.txt   (empty)
9a2be6ed1d67596e4ab7355fc0b96e7bcb6a92565e05da6b85f1ddf445aae1eb  out/t39-neg6.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t39-neg7-classpath.txt
6872f7336855f054521d812a5354542dda43121a2ebaa42f54ef0df1812e58db  out/t39-neg7-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t39-neg7-oracle-identity.txt
9e59fd12cfdc8ad47c5048d376392dca00c4d305a5bd8bb1dccd1971402a1c15  out/t39-neg7-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t39-neg7-stderr.txt   (empty)
bf0125a0915841932a1e4c874b4309866f52c005e7571019b863035eb82659e9  out/t39-neg7.json
68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f  out/t39-periodratio-classpath.txt
0d8c8e8097faa633b2e82436665e5bc3eb49f93a7ca3784d6847ec98a87fffb8  out/t39-periodratio-log.txt
f9439f09b3ce94c35494601816b24c6d3dcd3ad27ce2cdd729d70359e66ffe06  out/t39-periodratio-oracle-identity.txt
09ce7a2ced05944c7de8ccd01e2c874e40e2ac76bc1497809079f06508b41f43  out/t39-periodratio-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t39-periodratio-stderr.txt   (empty)
898435d89b58c1c61dd0b9d55b2bae38ab8fedd33f41d314ffea09b5c7e5b3a2  out/t39-periodratio.json
630754cf283cdd0dfebb1cf59585993d38d8d548c12e5d7cf462ad7875789278  src/CapturePeriodRatio.java
bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714  src/EmbeddableProgressiveLoanScheduleGenerator.java
bd3f1bfb3271083ca385d0d65ec2443f67432dd4e1ef177f3ac467a0aaa1c1a6  src/run-periodratio.sh
```

`ATTESTATION.md`, `REPRODUCE.md`, `PROVENANCE.md` and `NEGATIVE-TESTS.md` are not listed above
because they contain these digests. Regenerate with
`cd .softhouse/capture/periodratio && find . -type f | sort | xargs shasum -a 256`.

## 10. What this attestation does NOT claim

- **Nothing here is promoted to the vector store.** DEC-1 is at revision 6 and **UNRATIFIED**
  (gate G-1 open); while a contract gate is open, captures are stored in **raw observed form
  only**, because the contract shape is precisely what is being ratified. See `PROVENANCE.md`.
- Path A's known blind spot is unchanged: `installmentAmountInMultiplesOf` and
  `daysInYearCustomStrategy` are accepted and silently dropped by
  `LoanApplicationTerms.assembleFrom` (`.softhouse/reference-oracle.md`, Path A). Both are pinned
  to their inert values in every case here, so the blind spot is empty for these captures — a
  fact about these shapes, not about Path A.
- Six throwaway `--rm` containers were run. The shared `fineract-fineract-1` / `fineract-db-1`
  containers were **not** started, stopped, reconfigured or written to; a sibling worker owns
  them this fire.
- Sixteen captures grade sixteen shapes. They license no claim about an un-sampled
  `(ScheduleStartDate, DisbursementDate, principal, term, rate)` tuple.
