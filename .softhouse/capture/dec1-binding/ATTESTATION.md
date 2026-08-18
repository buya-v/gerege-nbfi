# T37 — attestation for the DEC-1 §8 binding captures

Every claim below was executed on the local fire of **2026-08-18** and is reproduced by
`REPRODUCE.md`. An unattested capture is not admissible; this is that attestation.

## 1. Reference oracle identity

| Fact | Value | How it was checked |
|---|---|---|
| Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | `git -C /Users/buv/fineract rev-parse HEAD` — matches `.softhouse/reference-oracle.md`'s pin |
| Pinned checkout clean | yes | `git -C /Users/buv/fineract status --porcelain` → empty |
| Image tag | `fineract:latest` | |
| Image id | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | `docker image inspect fineract:latest --format '{{.Id}}'` — matches `README-pass2.md`'s pin |
| Image created | `2026-08-17T11:29:56.52027346Z` | `docker image inspect` |
| `/app/fineract-provider.jar` sha256 | `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9` | `sha256sum` inside a throwaway container |
| Capture path | **Path A — embeddable seam, in-process** | `docker run --rm`; no server started, no PostgreSQL touched, no network |

## 2. Seam-class integrity — the precondition that would invalidate everything

```
diff .softhouse/capture/dec1-binding/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/\
org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```

**No output — byte-identical.** sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`.
The copy under `src/` is this task's own; `.softhouse/capture/src/` (owned by another worker
this fire) was not read from, written to, or compiled.

## 3. JVM identity

Read **inside** the container, entrypoint overridden so the JDWP agent does not bind:

```
openjdk version "21.0.11" 2026-04-21 LTS
OpenJDK Runtime Environment Zulu21.50+19-CA (build 21.0.11+10-LTS)
OpenJDK 64-Bit Server VM Zulu21.50+19-CA (build 21.0.11+10-LTS, mixed mode, sharing)
```

The capture program echoes the same identity into its own output block:
`javaVersion 21.0.11`, `javaVmVersion 21.0.11+10-LTS`, `javaVmName OpenJDK 64-Bit Server VM`,
`javaVendor Azul Systems, Inc.`, `jvmFileEncoding UTF-8`.

**`jvmUserTimezone` came back `null`**, not `UTC`: this throwaway container overrides the image
entrypoint, so Fineract's own `-Duser.timezone=UTC` flag is **not** applied. That is recorded
rather than hidden. It is inert for these captures — every date in the request and the response
is an explicit civil date, and DEC-1 §4.2 records the *observed* zone-independence — but any
future capture of a behaviour that depends on "today" must re-establish the zone explicitly.
Each case does pin a tenant timezone of `Asia/Ulaanbaatar` (`inputs.tenantTimeZone`).

## 4. The `MathContext` actually in force, as the oracle itself reports it

Two independent witnesses, both from the oracle rather than from this harness:

1. **The oracle's own SLF4J log**, `out/t37-binding-log.txt` — eleven lines, one per case:
   `Initialized rounding mode for tenant '<id>': HALF_UP`. Eleven of eleven are `HALF_UP`
   (`RoundingMode` ordinal 4, the ratified Gerege mode).
2. **`MoneyHelper.getMathContext()`**, echoed per case into
   `inputs.ambientMoneyHelperMathContext`: `precision=19 roundingMode=HALF_UP` on all eleven,
   and `moneyHelperPrecisionConstant: 19` at the top level — the compile-time constant
   `MoneyHelper.PRECISION` read from the running oracle, not from source.

**Threaded `MathContext`:** `(19, HALF_UP)` on ten of eleven cases. The eleventh, `T37-CAL`,
is threaded at `(12, HALF_UP)` **deliberately** — it is the rig calibration against the shipped
test literal, is labelled as such, and **can never be a parity vector**.

## 5. Determinism

The whole run was executed a second time from a fresh container. The JSON payload is
**byte-identical** (`diff` clean). Only the log's wall-clock timestamps differ.

## 6. Calibration and reproduction controls — both passed

| Control | Expectation | Observed |
|---|---|---|
| `T37-CAL` — shipped fixture, USD 100 / 6 × 7.0 %, `(12, HALF_UP)` | the shipped test literal: level 17.01, final 17.00, total interest 2.05, term 182, splits 16.43/0.58 … 16.90/0.10 | **all reproduced digit-for-digit** |
| `T37-CTL-Q0a` — MNT 1,200,000 / 6 × 21.6 %, `(19, HALF_UP)` | committed observation Q0a (`.softhouse/reviews/t23-probe/t23-probe-output.txt`): 212,787.28 / 212,787.30 / 76,723.70 | **reproduced digit-for-digit** |

## 7. No float, anywhere

Every amount is rendered with `BigDecimal.toPlainString()`; the harness contains no
`float`, `double`, `Float`, `Double`, `parseDouble` or `doubleValue()` on any amount path.
The analysis model uses Python `decimal` at explicit contexts only — no `float` literal, no
`float()` call on a money path.

## 8. File digests (sha256)

```
38c0c3fa44da48cb06ada92d177eb13ef55171aa929846ed1ba13a54b244516f  analysis/dec1_readings.py
7d5aab10044016849b0ab9d253e5e7646892b8c6987a2a75382dcd06592f6201  analysis/discriminate-output.txt
395e488872928c3361421644505ac49b38b9642356b89374d193529fc8781d70  analysis/discriminate.py
21b8a05dafc42e689c40cbcffecd16181c29d36a3313bedd263b9c54c4295a37  analysis/select_shapes-output.txt
c4ffa273fcb0f10ea079a744f32a48868e1bb79c9e98123eb04d98ffcabeb83d  analysis/select_shapes.py
24499511995c8810b3a0341c5f5203faa61b414ea79755cd4f50fa08a466b4f2  out/t37-binding-log.txt
cd78189eccbfa91803a0e88228977635e61d6f207939b854865755e26d2518f3  out/t37-binding-raw.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  out/t37-binding-stderr.txt   (empty)
f4019056510bddf95701a0df657d7f16f716cf373b9d725d7f8e868a1722ac12  out/t37-binding.json
2ef469870afed5c06bb7f64a9199f530c5143aeaf419e409fe8e87e59d521242  src/CaptureBinding.java
bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714  src/EmbeddableProgressiveLoanScheduleGenerator.java
```

`ATTESTATION.md`, `REPRODUCE.md` and `PROVENANCE.md` are not listed above because they
contain these digests.

## 9. What this attestation does NOT claim

- **Nothing here is promoted to the vector store.** DEC-1 is at revision 6 and **UNRATIFIED**
  (user gate G-1 open); while a contract gate is open, captures are stored in **raw observed
  form only**, because the contract shape is precisely what is being ratified.
- Path A's known blind spot is unchanged: `installmentAmountInMultiplesOf` and
  `daysInYearCustomStrategy` are accepted and silently dropped by
  `LoanApplicationTerms.assembleFrom` (`.softhouse/reference-oracle.md`, Path A). Both are
  pinned to their inert values in every case here, so the blind spot is empty for these
  captures — but that is a fact about these shapes, not about Path A.
- Two isolated containers were run; the shared `fineract-fineract-1` / `fineract-db-1`
  containers were **not** started, stopped, reconfigured or written to.
