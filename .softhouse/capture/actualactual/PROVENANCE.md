# T48 — provenance of the ACTUAL/ACTUAL cross-year partial-period captures

**Task** T48, branch `softhouse/T48-actualactual-captures`, worker `test_writer`.
**Fire** local `20260819-*` on Buyan's Mac. **The reference oracle (Fineract) was reachable and every
number in this directory is an OBSERVATION made on it** — nothing is computed, extrapolated,
interpolated or authored, except where a block is explicitly labelled a RE-DERIVATION.

---

## THIS TASK CAPTURES. IT DOES NOT ADMIT.

> **Nothing here proposes admitting `DaysInYearCustomStrategy`, `DaysInYearType.ACTUAL`, or the
> cross-year partial-period arm to DEC-1's graded domain.** Admission would make
> `daysInYearCustomStrategy` live, which **DEC-1 §4.4 states is an AMENDMENT** — a gate no agent may
> cross. This pass takes raw observations of behaviour §4.9 currently refuses with
> `ErrNoDiscriminatingVector`, so that a later, properly-gated decision has evidence to work from.
> Capturing is in scope; admitting is not.

> **RAW OBSERVED FORM ONLY. NOTHING IS PROMOTED to the parity vector store and NOTHING is stored
> contract-shaped.** Gate **G-1 is open**; the contract *shape* is the thing still under review, so
> shaping a capture to it would prejudge that review. Every artefact here is either the harness's own
> JSON emission of oracle-returned `BigDecimal`s rendered with `toPlainString()`, or a raw HTTP
> response body plus its exact-text sidecar.

No file under `docs/adr/**` was touched by this task (T47 owns DEC-1 revision 10 concurrently).

---

## Pinned oracle — read from the oracle, not from config

| Fact | Value | How it was read |
|---|---|---|
| Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | `git -C /Users/buv/fineract rev-parse HEAD`, asserted by `src/run-actualactual.sh` step 1 |
| Pinned checkout clean | yes, `status --porcelain` empty | asserted by step 2 |
| Image | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | `docker image inspect`, asserted by step 3 |
| Jar sha256 | recorded per run in `out/t48-<set>-oracle-identity.txt` | `sha256sum /app/fineract-provider.jar` **inside the container** |
| Jar `git.properties` | recorded per run in the same file | read out of the deployed jar |
| JVM | recorded per run (`java -version` inside the container) | inside the container |
| `MoneyHelper.PRECISION` | **19**, read **in-process from the running oracle** and asserted `== 19` | `MoneyHelper.PRECISION` echoed into every payload |
| Classpath | **348 entries**, digest `68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f` | `ls BOOT-INF/lib/*.jar` inside the container |
| Prohibited engines | **0** `ojdbc` / `oracle` / `mysql` / `mariadb` entries on the classpath | asserted by step 12, run fails otherwise |
| Seam class | byte-identical to the pinned original, sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` | `diff` against the pin, asserted by step 4 |

**PostgreSQL is the only database engine in play.** The Path A / Path A2 seams reach **no database at
all**; the Path B leg reaches PostgreSQL 18.3 through `org.postgresql.Driver`. **"The oracle" here means
the Fineract reference implementation. Oracle Database is prohibited and appears nowhere.**

---

## Three seams, named apart — they are NOT equivalent

### Path A — the embeddable seam (`out/t48-seam.json`, 18 captures)

`EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)`, in process, the seam capture
passes 1/2/3, T37, T39 and T46 used.

**Observed limit, verified from source and then confirmed by observation:**
`LoanApplicationTerms`'s private `Builder` constructor
[VERIFIED: `LoanApplicationTerms.java:304-351`] **never copies** `builder.daysInYearCustomStrategy`
[VERIFIED: declared `:380`, set by the builder setter `:567-570`] into the field [VERIFIED: `:291`], so
`assembleFrom`'s `.daysInYearCustomStrategy(modelData.daysInYearCustomStrategy())` call
[VERIFIED: `:604`] is silently discarded and `toLoanConfigurationDetails()`
[VERIFIED: `:1746-1756`] passes `null` regardless. Captures `T48-AA-N3` (feeds `FEB_29_PERIOD_ONLY`)
and `T48-AA-N4` (feeds `FULL_LEAP_YEAR`) are **0 of 87 cells different from `T48-AA-1`**, which fed
nothing — the drop, observed.

### Path A2 — the `ProgressiveEMICalculator` seam (`out/t48-calc.json`, 27 captures)

`ProgressiveEMICalculator.generatePeriodInterestScheduleModel(...) + addDisbursement(...)`, driven with
a hand-built `LoanConfigurationDetails`. **This is the seam Fineract's own shipped unit tests use**
[VERIFIED: `ProgressiveEMICalculatorTest.java`], it is the only in-process seam on which
`daysInYearCustomStrategy` binds, and it exposes `InterestPeriod.getRateFactor()` — the direct output of
`rateFactorByRepaymentPartialPeriod` [VERIFIED: `ProgressiveEMICalculator.java:1969-1980`].

**Path A2 is a NEW SEAM, and promoting a capture path to a trusted source is a `user` decision**, not
this task's. What this pass can show, and does:

* it reproduces **five shipped Fineract test literals digit for digit** (`T48-CAL-S1`…`S5`, 28 asserted
  period rows, 0 mismatches) at the settings those tests declare, `(12, HALF_EVEN)`;
* it reproduces **two committed Path B observations** — B-03 `144,659.21` and B-04 `145,011.43`;
* on **12 of 12** shapes shared with the Path B leg below it agrees on the total interest **and period
  by period** [`analysis/PATHB-CROSSCHECK.txt`].

### Path B — the running server (`pathb/out/`, 13 captures)

`POST /loans?command=calculateLoanSchedule`, tenant **`gerege`** (`Asia/Ulaanbaatar`,
`c_configuration.rounding-mode = 4`), PostgreSQL 18.3. **The production wiring.**

**Additive only.** This leg created **no product and no charge**; it reuses products `7` / `3` / `4`
(`UNSET` / `FULL_LEAP_YEAR` / `FEB_29_PERIOD_ONLY`, all ACT/ACT + DAILY), asserted out of PostgreSQL
before use and re-asserted after. `m_loan` was **0 before and 0 after**; `m_product_loan` **16 before and
16 after**. The shared containers were never started, stopped, restarted, re-tenanted or written to.

`clientId 2` ("Path B Leap Fixture", activation `2023-01-01`) is used throughout: client 1 activates
`2026-01-01` and the oracle rejects any earlier `submittedOnDate` with HTTP 403
`error.msg.loan.submittal.cannot.be.before.client.activation.date` — observed, body kept.

---

## Settings actually in force

Everything except the `CALIBRATION` family ran at the **ratified production threaded `MathContext`
(19, HALF_UP)**. The `CALIBRATION` family ran at whatever the shipped literal it reproduces declares —
`(12, HALF_UP)` for the embeddable-seam literal, `(12, HALF_EVEN)` for the `ProgressiveEMICalculatorTest`
literals [VERIFIED: `ProgressiveEMICalculatorTest.java:76`, `:97-98`] — and every calibration capture
says so in its own payload. `run-actualactual.sh` **fails the run** if any non-calibration capture is at
anything other than `(19, HALF_UP)`, and if a calibration capture is at anything other than precision 12.

`MoneyHelper.PRECISION = 19` is a compile-time constant [VERIFIED: `MoneyHelper.java:35`, `:91-93`];
only the mode is tenant-configurable.

## No float, anywhere

Every money and ratio value in `out/*.json` is emitted as a **JSON string** produced by
`BigDecimal.toPlainString()` — never through a `double`, never rounded by the harness, never in
scientific notation. `run-actualactual.sh` assertion 13 walks the whole payload and **fails the run** on
any JSON float or any scientific-notation string.

The Path B responses are **float-shaped on the wire** (Fineract's REST layer serialises `BigDecimal` as a
JSON *number*) — finding **T44-X1**. Following T46's decision, the raw bytes are kept unmodified as the
canonical artefact and every one gets an **exact-text sidecar** `*-exact.json` in which every number is a
JSON string carrying the literal characters that were on the wire, produced with
`json.loads(text, parse_float=str, parse_int=str)` so no binary double is ever constructed. All 13
sidecars carry **zero** bare JSON numbers, checked by `analysis/pathb-crosscheck.py`.
