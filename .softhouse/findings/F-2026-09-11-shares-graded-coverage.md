# F-2026-09-11 — the `shares` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no `POST`/`PUT`/`DELETE` was
issued, no vector and no drive was written, and no port code changed. This run makes the
`shares` corpus *measurable* and triages the result. Grading anything it finds is a later
run's work.
**Task:** `OH-SHCOV-AI`, bounded context `shares`, branch `feat/OHSHCOVai`.
**Found by:** Go coverage of the `shares` port, measured with the port as `-coverpkg` and
the **conformance package** as the test target — the instrument validated on the
savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`) and the loan / charges /
working-capital corpora, not the grep it replaced.

## 1. The missing control, added

The map said the `shares` committed-store test was **ABSENT** (`.softhouse/maps/shares.md`),
so coverage measured from conformance meant nothing: without a store-driven test in the
package, no vector can move the number and every port function reads `0.0%` no matter how
many vectors exist.

Added `nexus/internal/apps/shares/conformance/committed_store_test.go` (commit `7de5217a`),
modelled on `nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` (`conformance/vector.go:229`)
  → `Admit` (`conformance/admit.go`) → `Run` (`conformance/grade.go:148`) against the
  reference `shares-go`, exactly as the grading binary does;
* it **calls no port function directly** — the file contains no `shares.` identifier; every
  statement it reaches is reached *through the vectors*, because `Admit`/`Run` are the
  harness that consumes them, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors (P-35); every loaded vector must be
  admissible; `Run` must not be fatal; `VectorsLoaded != 0`; and
  `parity_fail + refused + inadmissible + errored == 0` with `invariant_violations == 0`;
* it pins a **money-observation guard**: every committed seam
  (`share-account`, `share-dividend`, `share-product`, `vector.go:22,28,33`) must still have
  at least one vector, so deleting the last vector of a seam is a failing test rather than a
  silent return to `0.0%` conformance coverage of that rule.

The committed corpus passes the reference:

    go run ./internal/apps/shares/conformance/cmd/conformance -root ..
    → VERDICT: PASS (exit 0)
      vectors_loaded=9 parity_pass=9 parity_fail=0 refused=0 inadmissible=0 harness_error=0
      graded_cells=32 money_cells=14 invariant_violations=0
      nofloat: packages=48 files=382 tokens=398456 imports=1116 violations=0

## 2. Measurement

The prescribed command (from `nexus/`), then the same command with only the store-driven
test selected. Use private profile paths: `conformance.sh` writes its own scratch profile to
`/tmp/c.cov` (§8), so reading that path after a census run yields another context's coverage.

    go test -count=1 -coverpkg=./internal/apps/shares \
        -coverprofile=/tmp/shares_pkg.cov ./internal/apps/shares/conformance/...
    go test -count=1 -coverpkg=./internal/apps/shares \
        -coverprofile=/tmp/shares_vo.cov -run '^TestCommittedCorpusPassesTheReferenceImplementation$' \
        ./internal/apps/shares/conformance/...
    go tool cover -func=/tmp/shares_pkg.cov | awk '$3=="0.0%"'   # 17
    go tool cover -func=/tmp/shares_vo.cov  | awk '$3=="0.0%"'   # 17, same set

| run | test target | coverage | functions at 0.0% |
|---|---|---:|---:|
| package-wide (prescribed) | whole conformance package | **19.0%** | **17** |
| **committed-store only** | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | **17.9%** | **17** |

**The honest "what the graded corpus reaches" figure is the committed-store-only row
(17.9%).** The package also contains `conformance_test.go`, whose nine hand-built probes
(`conformance_test.go:42,95,147,188,230,237,244,294,339`) are graded through
`NewGoEvaluator()` / `gradeOne` (`conformance_test.go:469-527`). Unlike the `charges`
package, no test in `shares` calls the port package directly — but those probes are still
*not committed vectors*, so their coverage is not corpus coverage. The `0.0%` set is
**identical** in both runs; the delta is branch-only, reached by two hand-built probe paths:

* `money.go:79.21,83.4` — the sub-minor-unit **residue refusal** — `0 → 1`, from
  `TestAdmitDefaultDeny` feeding a hand-made `"10000.005"` (`conformance_test.go:614`);
* `status.go:37.10,38.35` — `ShareAccountStatusFromInt`'s **default** arm — `0 → 1`, from
  the same test feeding `account_status_id 0` (`conformance_test.go:609`).

That is why `money.go:45` moves `70.3% → 73.0%` and `status.go:25` moves `28.6% → 42.9%`
between the rows. No money rule appears only because a probe reaches it: the money-rule
`0.0%` set below is the same under both readings.

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds case, each candidate is checked
against one question only:

> **Does the function implement a money rule?** If not — a getter, `String()`, status
> predicate, enum decoder, or error constructor — it is out of scope for grading and stays
> at `0.0%` without being a gap.
>
> If it *does* implement a money rule: **does an observation behind it already exist in a
> committed capture?** If yes, name the file and the figures a vector would take (a grading
> run the driver can dispatch next). If no, say what a capture would need.

An answer of "the observation exists but no admissible vector can consume it" is a distinct
third outcome — it is the `shares` case — and is stated as such rather than run together
with "needs a capture".

## 4. Triage of the `0.0%` candidates

`file:line` are lines in the file. All seventeen are listed in Appendix A.

### 4.1 Money-rule candidates

**`money.go:19` `FormatDecimal` — the only pure money rule at `0.0%`.** Renders integer
minor units into exact major-unit decimal text (the inverse of the port's parser). Its only
callers are the PostgreSQL write path (`postgres.go:99` `InsertMarketPrice`, `postgres.go:248`
and `postgres.go:249` in the transaction `Insert`) and the port's own unit test
(`nexus/internal/apps/shares/shares_test.go:44`, which round-trips `5` → `"0.05"`). It is
reached by **no** grading path: the evaluator only ever parses
(`impl.go:133,137,149,164,168` call `MinorUnitsFromDecimalText`), and `Admit` only validates
the parse (`admit.go:125,128,151,170,173`). See §5.1.

**`postgres.go:116` `findMarketPrices` and `postgres.go:257` `FindByAccount` — money-rule-
bearing persistence.** Both read `::text` money columns and normalise them through
`MinorUnitsFromDecimalText` (`postgres.go:126`, `postgres.go:273`, `postgres.go:278`), and
`FindByAccount` additionally decodes `ShareAccountTransactionTypeFromInt` / `PurchaseStatusFromInt`
(`postgres.go:271-272`). They are reachable only with a live PostgreSQL; the vector harness
opens no database. No committed capture carries the raw `m_share_product_market_price.share_value`
or `m_share_account_transactions.*` columns. See §5.2.

**Not money rules (persistence plumbing):** the three constructors
(`postgres.go:30,170,237`), the inserts (`postgres.go:35,95,107,175,242`), the two
`FindByID` readers (`postgres.go:53,193`), `findCharges` (`postgres.go:140`) and
`nullIfEmpty` (`postgres.go:292`). Two of the inserts render money
(`InsertMarketPrice` at `postgres.go:95` via `postgres.go:99`; the transaction `Insert` at
`postgres.go:242` via `:248-249`) but a write is not a graded seam.

### 4.2 Excluded classes

| class | functions (`file:line`) |
|---|---|
| enum getter | `status.go:130` `StoredValue` |
| enum decoder | `status.go:133` `ShareAccountTransactionTypeFromInt` |

`ShareAccountTransactionTypeFromInt` (`status.go:133`) is an enum decoder, not a money rule,
and it has **no observation behind it**: the port's `ShareAccountTransactionType` values are
`1..9` (`status.go:116-127`), while the only `type` id the corpus carries anywhere is
`purchasedShares[0].type.id = 500`
(`.softhouse/capture/shares-nonround-money/out/share-account-detail-raw.json`, code
`purchasedSharesType.purchased`). That 500 is Fineract's **`PurchasedSharesStatusType.PURCHASED`**,
a different enum: the oracle sets the transaction's `type_enum` from
`PurchasedSharesStatusType` (`ShareAccountTransaction.java:86,106,116` in the pinned tree).
So 500 is not a `ShareAccountTransactionType` value, and no capture observes `1..9`.

## 5. The finding — what the corpus never reaches, and why

### 5.1 `money.go:19` `FormatDecimal` — observed, implemented, unit-tested, and unreachable by any admissible vector

*Rule.* Exact money serialisation: an integer minor-unit count → major-unit decimal text with
exactly `minorDigits` fraction digits. Money rule, integer minor units, no float.

*Why it is `0.0%` where it matters.* The graded seam is **one-directional**: `Request` carries
decimal text and `Expect` carries integer minor-unit *strings* (`vector.go:106-151`); no field
on either side holds rendered decimal text, and neither the evaluator nor `Admit` ever calls
`FormatDecimal`. So no admissible vector can reach the inverse direction. This is the
`shares` analogue of the savings hold — implemented, unit-tested
(`shares_test.go:44`), and `0.0%` from the golden-vector harness — but the blocker is the
**seam's direction**, not a missing observation.

*Observation.* **Exists, and is committed, as raw text.** The captures hold exactly the
decimal strings `FormatDecimal` must reproduce for the vectors' minor units:

| capture | figures (oracle text) |
|---|---|
| `.softhouse/capture/shares/out/share-account-detail-raw.json` | `purchasedShares[0].purchasedPrice "100.00"`, `.amount "10000.00"`, `.chargeAmount "0.00"`, `.amountPaid "10000.00"` |
| `.softhouse/capture/shares-nonround-money/out/share-account-detail-raw.json` | `purchasedPrice "137.50"`, `amount "18837.50"`, `chargeAmount "0.00"`, `amountPaid "18837.50"`, `currentMarketPrice "137.50"` |
| `.softhouse/capture/shares/out/share-product-detail-raw.json` | `unitPrice "100.00"`, `shareCapital "100000.00"` |
| `.softhouse/capture/shares-nonround-money/out/share-product-detail-raw.json` | `unitPrice "137.50"`, `shareCapital "188787.50"` |
| `.softhouse/capture/shares/out/shares-products-list-raw.json` | `unitPrice "100.00"`, `shareCapital "0.00"`, `"1.00"`, `"100000.00"` |

Each is the canonical rendering of the corresponding transcribed minor units
(`10000`, `1000000`, `0`, `13750`, `1883750`, `18878750`, …), so the observation is real.

*Verdict and what closes it.* **A vector alone cannot grade it, and the needed captures are
already committed** — this is not a capture gap. Grading `FormatDecimal` requires one of:

1. a **serialization seam output**: a vector that gives the minor units and expects the
   formatted text (the figures above are the expectations), which is a conformance/seam
   extension, not a new capture; or
2. a **PostgreSQL round-trip test** over `InsertMarketPrice` / the transaction `Insert`
   (`postgres.go:95,242` → `FormatDecimal` at `:99,248-249`) reading the stored column back —
   the instrument §5.2 needs anyway.

### 5.2 The DB read path that also normalises money — needs a database instrument, not a capture

`findMarketPrices` (`postgres.go:116`) and `FindByAccount` (`postgres.go:257`) are the only
other money-rule-bearing `0.0%` functions: they read `::text` money columns and normalise
through `MinorUnitsFromDecimalText` (`postgres.go:126,273,278`). They are structurally
outside the golden-vector harness — it never opens a connection — and the committed captures
are REST projections, not the raw `m_share_product_market_price` / `m_share_account_transactions`
rows they read. **No capture exists behind them, and a capture of the REST surface would not
reach them.** A PostgreSQL integration test (or a seam that reads those rows) is required.

### 5.3 The parser's refusal branches — unreachable by design, not merely ungraded

`MinorUnitsFromDecimalText` (`money.go:45`) is reached (`70.3%` corpus-only), but eleven of
its branches are `0` hits, including the one money rule among them — the **sub-minor-unit residue
refusal** at `money.go:79.21,83.4`. Its only observation in a committed capture is the
*command* `.softhouse/capture/shares/req/share-dividend-create.json`
(`dividendAmount "0.005"`), not a read-back: the stored read-back
(`.softhouse/capture/shares/out/shares-product-dividends-raw.json` `amount "0.010000"`)
carries no nonzero digit beyond 2dp. The harness refuses a residue-bearing vector at
admission (`conformance_test.go:614-617` asserts `"10000.005"` is refused), and
`capabilities-shares.json` records the HALF_UP rounding of `0.005 → 0.01` as a **later slice,
outside the graded domain**. So this branch cannot be graded by any admissible vector, and a
capture cannot help (MNT is 2dp, so the oracle never stores residue).

## 6. Adjacent evidence (recorded, NOT this triage's action)

These are observations that no vector uses but that sit behind functions which are **not**
`0.0%` (the parser and the status decoders are already reached), so they are not candidates
under §3. Recorded because the evidence is committed:

* `.softhouse/capture/shares-nonround-money/out/share-account-detail-pre-activate-raw.json`
  carries `status.id 200` (`shareAccountStatusType.approved`). **No vector cites this file.**
  It would exercise `status.go:29.11,30.36`, a branch of a status decoder (excluded class).
* The purchased money fields `chargeAmount`, `amountPaid` and `currentMarketPrice` (e.g.
  `chargeAmount "0.00"`, `amountPaid "18837.50"`, `currentMarketPrice "137.50"` in the
  non-round account capture) are carried by no vector. They are not behind a `0.0%`
  function; `MinorUnitsFromDecimalText` is already reached.
* **Enum divergence from the pinned oracle (out of this run's scope, recorded for the
  driver).** The port's `ShareAccountStatusType` maps `400 → Rejected` (`status.go:33-34`),
  but the pinned `ShareAccountStatusType.java` has `REJECTED(500)` (no 400) and no `500`
  case exists in the port; likewise the port's `PurchaseStatus` is `100/200/300/400`
  (`status.go:51-57`) while the column is set from `PurchasedSharesStatusType`
  (`100/300/400/500/600/700`, `ShareAccountTransaction.java:85-153`), so the observed
  `purchasedShares[0].status.id 300` is labelled `Rejected` in the port though the oracle
  calls it `approved`. The integer round-trips through `StoredValue()`, so every current
  vector still passes; no corpus observation pins 400, 500 or the transaction type ids, so
  the corpus cannot see it. This is a correctness question, not a coverage gap, and **this
  run does not act on it.**

## 7. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` issued.
* No vector and no drive was written; `.softhouse/vectors/shares/` is unchanged (9 files).
* No port code changed. `.softhouse/guards/` (12 pairs) and `.softhouse/conformance.sh`
  (census 17) are untouched.
* No gap was graded; the one ungraded money rule needs a seam or a DB instrument, not a
  capture.

## 8. Controls

* `go build ./...` — clean; `gofmt -l internal/apps/shares/` — clean.
* `go test ./...` — all packages pass; the committed-store test passes `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `§4.4.2-RECORDED-DECISION-EXIT`; no `HARD guard failed`; guard/exemption census unchanged
  (census 17).
* `kills.sh shares shares-wrong-off-by-one <worktree>` → **8** (non-empty; the measurement
  is alive).
* `redcount.sh <worktree> shares` → **6** — every registered `shares-wrong-*` drive still
  kills.
* `capcount.sh <worktree> shares shares-go` → **0** — the reference fails no committed
  vector.
* `shares-go` on the committed store: `vectors_loaded=9 parity_pass=9 parity_fail=0`.
* Note for re-runs: `conformance.sh` writes its own scratch profile to `/tmp/c.cov`, so the
  coverage commands must use a private `-coverprofile` path or the reading is another
  context's (observed and re-measured; §2 numbers are from private files).

## Appendix A — all 17 functions at `0.0%` in BOTH runs

`file:line` are lines in each file.

- `money.go:19` `FormatDecimal` — **money rule** (§5.1)
- `postgres.go:30` `NewPostgresShareProductRepository`
- `postgres.go:35` `Insert`
- `postgres.go:53` `FindByID`
- `postgres.go:95` `InsertMarketPrice`
- `postgres.go:107` `InsertCharge`
- `postgres.go:116` `findMarketPrices` — **money-rule-bearing persistence** (§5.2)
- `postgres.go:140` `findCharges`
- `postgres.go:170` `NewPostgresShareAccountRepository`
- `postgres.go:175` `Insert`
- `postgres.go:193` `FindByID`
- `postgres.go:237` `NewPostgresShareAccountTransactionRepository`
- `postgres.go:242` `Insert`
- `postgres.go:257` `FindByAccount` — **money-rule-bearing persistence** (§5.2)
- `postgres.go:292` `nullIfEmpty`
- `status.go:130` `StoredValue` — enum getter
- `status.go:133` `ShareAccountTransactionTypeFromInt` — enum decoder

## Appendix B — port functions the committed corpus DOES reach (committed-store-only run)

    money.go:45      MinorUnitsFromDecimalText              70.3%
    status.go:22     ShareAccountStatusType.StoredValue     100.0%
    status.go:25     ShareAccountStatusFromInt              28.6%
    status.go:60     PurchaseStatus.StoredValue             100.0%
    status.go:63     PurchaseStatusFromInt                  33.3%
    status.go:96     ShareAccountDividendStatus.StoredValue 100.0%
    status.go:99     ShareAccountDividendStatusFromInt      66.7%
    total:                                                    17.9%

The corpus reaches the three read-back normalisations the context ports — the account,
purchase and dividend stored-value mappings, and the exact-money parser's happy path. That
is what `shares` is for: normalising oracle read-backs into the port's vocabulary.

## Appendix C — `FormatDecimal` block coverage (both runs)

    money.go:19.59,22.9    neg test          0
    money.go:22.9,24.3     negate            0
    money.go:25.2,26.35    scale loop init   0
    money.go:26.35,28.3    scale *= 10       0
    money.go:29.2,30.21    integer part      0
    money.go:30.21,32.31   fraction branch   0
    money.go:32.31,34.4    zero-pad loop     0
    money.go:35.3,35.21    append fraction   0
    money.go:37.2,37.9     sign test         0
    money.go:37.9,39.3     prepend minus     0
    money.go:40.2,40.10    return            0

Every block is `0` in both the package-wide and the committed-store-only run.
