# F-2026-09-11 — the workingcapital graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written. This run makes the workingcapital corpus *measurable* and triages the result.
Grading any gap it finds is a later run's work, after a capture if one is needed.
**Task:** `OH-WCCOV-AE`, bounded context `workingcapital`, branch `feat/OHWCCOVae`.
**Found by:** Go coverage of the workingcapital port, measured with the port as
`-coverpkg` and the **conformance package** as the test target — the instrument the
driver validated on savings (`F-2026-09-10-savings-holds-ungraded.md`) and reused on
loan (`F-2026-09-11-loan-graded-coverage.md`).

## 1. The missing control, added

`workingcapital` read `0.0%` from conformance for *every* function while its six
committed vectors passed against the oracle — because the workingcapital conformance
package had **no test that drove the committed corpus through the grading path**
(the map records the committed-store test as `ABSENT`). Without one, no vector can
move the number, and the reading is meaningless.

Added `nexus/internal/apps/workingcapital/conformance/committed_store_test.go`,
modelled on `nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run`
  against the reference `workingcapital-go`, exactly as the grading binary does;
* it **calls no port function directly** — every statement it reaches is reached
  *through the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors, on any load/admit/fatal/
  parity/invariant error, and pins the two graded seams (list, detail) plus the
  nonzero-discount observation so a later deletion is a failing test.

The committed corpus passes:

    go run ./internal/apps/workingcapital/conformance/cmd/conformance -root ..
    → vectors_loaded=6 parity_pass=6 parity_fail=0 refused=0 inadmissible=0
      harness_error=0  graded_cells=62 money_cells=40 invariant_violations=0

Committed as `12e98460` (`OH-WCCOV-AE: make the workingcapital corpus measurable`).

## 2. Before / after

    go test -count=1 -coverpkg=./internal/apps/workingcapital \
        -coverprofile=/tmp/c.cov ./internal/apps/workingcapital/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

| | statements | coverage | functions at 0.0% |
|---|---:|---:|---:|
| before (no committed-store test) | 366 | 0.0% | 64 |
| after (test present) | 366 | **5.7%** | **53** |

The delta is deliberately small and narrow: **eleven** functions that the grading
path reaches only because a vector exercises them, all in `balance.go`:

* `balance.go:87` `ValidateGradedDomain` — via every detail vector
* `balance.go:121` `ApplyDisbursement` — via every detail vector
* `balance.go:135` `TotalPrincipalDue`, `:142` `PrincipalOutstanding`,
  `:148` `FeeOutstanding`, `:154` `PenaltyOutstanding`, `:160` `TotalOutstanding`,
  `:167` `TotalExpectedRepayment`, `:173` `TotalRepayment`,
  `:180` `UnrealizedIncomeFromDiscountFee`, `:184` `maxUnits`

**53 workingcapital functions remain at 0.0% from the graded corpus.** Full list in
the appendix. The test is vector-driven, not manufactured: with the whole committed
detail set removed the balance getters fall back to 0.0%; with the discount vector
removed the only nonzero-discount cell is no longer graded (the getters themselves
are still reached by the other detail vectors — the guard says exactly that, it does
not overclaim a 0.0% fall).

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the loan and holds cases, each
candidate is first filtered to the ones that implement a **money rule** (not a getter,
a `String()`, an enum decoder, a status predicate, an error constructor, or DB I/O).
For each survivor the only question asked is:

> **Does an observation behind it exist in the committed corpus?**

Where an observation *does* exist but is ungraded, the candidate is **holds-shaped**.
Where no observation exists, a capture is required before it can be graded at all.

### Corpus scope

The **graded workingcapital corpus** is the six vectors in
`.softhouse/vectors/workingcapital/`. Their capture refs are the only observations
in play:

    workingcapital/out/loans-list-raw.json                (WC-01, WC-05)
    workingcapital/out/wc-loan-detail-raw.json            (WC-02, WC-03, WC-04)
    wc-discount-nonzero/out/wc-loan-discount-detail-raw.json (WC-06)

The two detail captures serialise **the balance read-back only**. Their top-level key
set is `[id, accountNo, externalId, …, amortizationType, …, paymentAllocation,
timeline, disbursementDetails, balance, …, summary, …]`. There is **no
`transactions` array** anywhere in either, and no capture anywhere in the committed
tree observes a working-capital transaction or its allocation (a full scan for
`"transactions"` finds only core `loan`/`savings` captures; the only other files
naming working capital are the COB job-name lists under `capture/cob/`, which carry
no working-capital rows).

Two observations do exist inside that read-back and are the backbone of the
observations column below:

* **`paymentAllocation`** — the ordered rule list
  (`wc-loan-detail-raw.json`, key `paymentAllocation[0]`): `transactionType`
  `"DEFAULT"` with `paymentAllocationOrder` = `DUE_PENALTY`(1), `DUE_FEE`(2),
  `DUE_PRINCIPAL`(3), `IN_ADVANCE_PENALTY`(4), `IN_ADVANCE_FEE`(5),
  `IN_ADVANCE_PRINCIPAL`(6). **Cited by WC-02/03/04, and graded by none of them.**
* **`disbursementDetails[0]`** — one tranche, `principal`/`actualAmount` = 1000
  (`"100000"`), already graded by WC-03.

## 4. Triage of the money-rule candidates

`file:line` are lines in the file.

### 4.1 `transaction.go:26,32,38,50,60` — the allocation split: observation ABSENT, and no seam calls it

*Rule.* The money split of one working-capital transaction — exactly four portions
(principal, fee, penalty, overpayment), never interest:

* `transaction.go:26` `Total` — folds the four portions to the transaction amount;
* `transaction.go:32` `ForPrincipalAllocation` — principal-only;
* `transaction.go:38` `ForPortions` — explicit four-way split;
* `transaction.go:50` `ForChargeAccrual` — charge amount lands in fee or penalty
  (`isPenalty`), the rest zero;
* `transaction.go:60` `ForCreditBalanceRefund` — excess principal + overpayment.

These are the port's mirror of Fineract's `WorkingCapitalLoanTransactionAllocation`
factories (`WorkingCapitalLoanTransactionAllocation.java:62-71,73-83,98-107,112-121`,
cited in the file's own headers). Every one is integer minor units; no float.

*Why 0.0%.* Two independent blockers:

1. **No observation.** No committed capture contains a working-capital transaction or
   an allocation block. The graded detail read surfaces `balance` and
   `disbursementDetails`, never a transaction. The stored money terms these would be
   built from are the ones `F-2026-09-10-workingcapital-ungraded-terms.md` records as
   *always zero or absent*: `principal_paid`, `fee_paid`, `penalty_paid`,
   `overpayment_amount`.
2. **No caller.** A grep for the five functions across the non-test package finds only
   their own definitions — no seam, no `loadAllocation`, nothing calls them.
   `PostgresWorkingCapitalLoanTransactionRepository.loadAllocation`
   (`postgres.go:622`) assigns the four fields **directly**, not through `ForPortions`,
   and is itself unreachable from the vector harness (§4.3).

*What a capture would need.* A working-capital loan with a posted money-moving
transaction, read back with its allocation. The oracle write paths that set the four
buckets are the ones already located for the ungraded terms: repayment allocation
(`WorkingCapitalLoanBalanceUpdater.java:46` principal, `:47` fee, `:48` penalty,
`:49` overpayment), a charge accrual
(`WorkingCapitalLoanChargeWritePlatformServiceImpl.java:464` penalty, `:466` fee), and
a credit-balance refund (the overpayment bucket, `:49`). Because the REST detail read
does not expose transactions, the capture would also need a read-back that serialises
them (a transaction endpoint observation, or the committed `m_wc_loan_transaction`
plus `m_wc_loan_transaction_allocation` rows), **and** the harness would need a seam
that calls the factories. Until a vector reaches this block it is ungraded, and a
drive for it kills zero. **Not asserted to be a defect.**

### 4.2 `paymentallocationrule.go:32,52,76,87` + `allocationtype.go:86,94,97,102,108` — the allocation-order rule: OBSERVED but UNGRADED → holds-shaped, gradeable without a capture

*Rule.* A working-capital loan's payment-allocation order: a transaction type coupled
with the ordered buckets a repayment of that type follows (penalty before fee before
principal before in-advance, exactly once each). The port carries it as

* `paymentallocationrule.go:32` `JoinAllocationTypes` — list → DB string (join `,`,
  de-dup), mirroring `GenericEnumListConverter.java:43-57`;
* `paymentallocationrule.go:52` `SplitAllocationTypes` — DB string → ordered list,
  decoding each name (`:76` `workingCapitalPaymentAllocationTypeFromName`) and
  raising `:87` `(*unknownAllocationTypeError).Error` on an unknown name;
* `allocationtype.go:86` `String`, `:94` `Code`, `:97` `HumanReadableName`,
  `:102` `DueType`, `:108` `AllocationType` — the classification of each rule.

*Observation.* **Exists, and is committed.** `wc-loan-detail-raw.json` (cited by
WC-02/03/04) carries the `DEFAULT` rule as six ordered names —
`DUE_PENALTY`, `DUE_FEE`, `DUE_PRINCIPAL`, `IN_ADVANCE_PENALTY`, `IN_ADVANCE_FEE`,
`IN_ADVANCE_PRINCIPAL` — which are precisely the `String()` values
`SplitAllocationTypes` would decode and `AllocationType`/`DueType` would classify
(`DUE_*` → `loan.DueDue`; `IN_ADVANCE_*` → `loan.DueInAdvance`; suffix → penalty /
fee / principal).

*Verdict.* Holds-shaped: **implemented, observed, ungraded.** It is the strongest
next dispatchable grading run for this context because it needs **no capture**. It is
not an arithmetic money fold, though — the 0.0% functions are the list converter and
the enum surface, so grading it grades the decode/classification of the observed rule,
not a clamp or a sum. Described honestly as such.

*The grading run the driver can dispatch next.* A vector over the existing capture
`.softhouse/capture/workingcapital/out/wc-loan-detail-raw.json`, seam
`working-capital-loans-detail`, whose expected cell is the ordered figure list
`["DUE_PENALTY","DUE_FEE","DUE_PRINCIPAL","IN_ADVANCE_PENALTY","IN_ADVANCE_FEE",
"IN_ADVANCE_PRINCIPAL"]`. It requires one harness change (a detail cell that decodes
the observed `paymentAllocation`) so the vector reaches `SplitAllocationTypes` and the
classifiers *through `Run`* — no port function may be called directly, or the
coverage is manufactured. That vector also has a discriminating wrong implementation:
a port that reorders in-advance ahead of due, or drops a bucket, would fail it.

### 4.3 `postgres.go` (29 functions) — I/O and money codecs, not rules; unreachable by construction

`postgres.go:23` `money`, `:26` `moneyFromText`, `:31` `moneyPtr`, `:38` `datePtr`,
`:45` `int32Ptr`, `:52` `int64Ptr`, `:59` `nullString`, `:66` `nullDate`,
`:73` `nullInt64`, `:80` `nullInt`, `:102` `wcProductDetailArgs`, `:142`
`NewPostgresWorkingCapitalLoanRepository`, `:149` `Insert`, `:195` `FindByID`,
`:200` `FindByAccountNumber`, `:204` `findOne`, `:343` `UpdateStatus`, `:368`
`NewPostgresWorkingCapitalLoanBalanceRepository`, `:382` `FindByLoanID`, `:463`
`NewPostgresWorkingCapitalLoanDisbursementDetailsRepository`, `:468` `Insert`,
`:487` `FindByLoanID`, `:543` `NewPostgresWorkingCapitalLoanTransactionRepository`,
`:548` `Insert`, `:579` `FindByLoanID`, `:622` `loadAllocation`, `:667`
`NewPostgresWorkingCapitalLoanPaymentAllocationRuleRepository`, `:673` `Upsert`,
`:690` `FindByLoanID`.

These are the SQL read/write layer and its scalar codecs (`money` renders an exact
decimal string; `moneyFromText` parses one into `loan.MinorUnits`; the pointer and
null helpers convert). They implement **no money rule** — they move bytes to and from
Postgres. They are also **unreachable by construction**: the vector harness seeds
in-memory evaluators and never opens a database, so no capture can ever move them.
Out of triage scope; recorded only so the appendix is auditable.

### 4.4 `productdetails.go` (10 functions) — enum decoders and getters, not rules

`productdetails.go:36` `StoredValue`, `:38` `String`, `:48`
`WorkingCapitalLoanPeriodFrequencyTypeFromString`, `:74` `StoredValue`,
`:76` `String`, `:85` `IsEIR`, `:90` `WorkingCapitalAmortizationTypeFromString`,
`:120` `StoredValue`, `:122` `String`, `:134` `WorkingCapitalStartTypeFromString`.

Enum decoders, `String()`s and one predicate (`IsEIR`); no arithmetic. The graded
capture does observe their values (`amortizationType.code = "EIR"`, a repayment
frequency), but by the triage filter these are not money rules and are out of scope.

### 4.5 Cross-reference — the two uncovered `balance.go` statements are the refusal arms

Not a 0.0% function, but worth recording because it closes the loop: the only two
uncovered statements in an otherwise-reached `balance.go` are
`balance.go:101.19,103.4` and `balance.go:126.52,128.3` — the arms of
`ValidateGradedDomain` and `ApplyDisbursement` that **refuse** a balance carrying one
of the eleven stored money terms no capture can discriminate. They are exercised by
unit tests, not by vectors, and they need the same captures
`F-2026-09-10-workingcapital-ungraded-terms.md` already maps. Grading them is not a
coverage hole of the same kind; the refusal itself is the discipline.

## 5. Summary of triage

| candidate | file:line | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `Total` (allocation fold) | `transaction.go:26` | yes | **no** (no wc transaction anywhere) | needs capture + seam |
| `ForPrincipalAllocation` | `transaction.go:32` | yes | **no** | needs capture + seam |
| `ForPortions` | `transaction.go:38` | yes | **no** | needs capture + seam |
| `ForChargeAccrual` | `transaction.go:50` | yes | **no** (no accrual observed) | needs capture + seam |
| `ForCreditBalanceRefund` | `transaction.go:60` | yes | **no** (no refund observed) | needs capture + seam |
| `SplitAllocationTypes` | `paymentallocationrule.go:52` | converter of a money policy | **yes** (`paymentAllocation` order) | **gradeable now** (harness cell) |
| `JoinAllocationTypes` | `paymentallocationrule.go:32` | converter | yes (inverse of the same list) | gradeable now |
| `workingCapitalPaymentAllocationTypeFromName` | `paymentallocationrule.go:76` | decoder | yes | gradeable now |
| `unknownAllocationTypeError.Error` | `paymentallocationrule.go:87` | error ctor | n/a | not a rule |
| `String`/`Code`/`HumanReadableName` | `allocationtype.go:86,94,97` | getters | name yes; code/human no | not a rule |
| `DueType`/`AllocationType` | `allocationtype.go:102,108` | classifiers | yes (`DUE_*`/`IN_ADVANCE_*`) | gradeable now |
| 29 postgres helpers/repos | `postgres.go:23–690` | no (I/O) | unreachable by construction | not a rule |
| 10 productdetail decoders | `productdetails.go:36–134` | no (getters) | values observed, no rule | not a rule |

**No candidate here is asserted to be a defect.** The allocation split
(`transaction.go:26–60`) is the strongest "implemented and never observed" block;
the allocation-order rule (`paymentallocationrule.go` + `allocationtype.go`) is the
strongest "observed and ungraded" block and the only one that needs no capture.
The evidence, not this list, decides which become grading runs.

## 6. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` issued.
* No vector and no drive was written. `.softhouse/vectors/workingcapital/` is
  unchanged (six vectors, as committed).
* No port code changed. `.softhouse/guards/` and `.softhouse/conformance.sh` are
  untouched.
* No gap was graded; a future run must either add the harness cell (§4.2, no capture)
  or capture first where the observation is absent (§4.1).

## 7. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass.
* `bash .softhouse/conformance.sh` — **exit 2** as the recorded §4.4.2 decision;
  ledger findings at the baseline pairs; guard census 17. Verdict excluding the one
  recorded divergence: PASS.
* `kills.sh workingcapital workingcapital-wrong-discount-dropped-from-principal` →
  **1** (still kills).
* `redcount.sh <worktree> workingcapital` → **5** (every workingcapital drive still
  kills).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365` → **45**.
* `kills.sh parties parties-wrong-iota-ordinals` → **12**.
* `workingcapital-go` on the committed store: `vectors_loaded=6 parity_pass=6
  parity_fail=0 refused=0 inadmissible=0 harness_error=0`.
* New test passes on the current tree; with the detail vectors removed the balance
  coverage falls back — the number is vector-driven, not manufactured.

## Appendix — all 53 workingcapital functions still at 0.0% from the graded corpus

- `allocationtype.go:86` `String`
- `allocationtype.go:94` `Code`
- `allocationtype.go:97` `HumanReadableName`
- `allocationtype.go:102` `DueType`
- `allocationtype.go:108` `AllocationType`
- `paymentallocationrule.go:32` `JoinAllocationTypes`
- `paymentallocationrule.go:52` `SplitAllocationTypes`
- `paymentallocationrule.go:76` `workingCapitalPaymentAllocationTypeFromName`
- `paymentallocationrule.go:87` `Error`
- `postgres.go:23` `money`
- `postgres.go:26` `moneyFromText`
- `postgres.go:31` `moneyPtr`
- `postgres.go:38` `datePtr`
- `postgres.go:45` `int32Ptr`
- `postgres.go:52` `int64Ptr`
- `postgres.go:59` `nullString`
- `postgres.go:66` `nullDate`
- `postgres.go:73` `nullInt64`
- `postgres.go:80` `nullInt`
- `postgres.go:102` `wcProductDetailArgs`
- `postgres.go:142` `NewPostgresWorkingCapitalLoanRepository`
- `postgres.go:149` `Insert`
- `postgres.go:195` `FindByID`
- `postgres.go:200` `FindByAccountNumber`
- `postgres.go:204` `findOne`
- `postgres.go:343` `UpdateStatus`
- `postgres.go:368` `NewPostgresWorkingCapitalLoanBalanceRepository`
- `postgres.go:382` `FindByLoanID`
- `postgres.go:463` `NewPostgresWorkingCapitalLoanDisbursementDetailsRepository`
- `postgres.go:468` `Insert`
- `postgres.go:487` `FindByLoanID`
- `postgres.go:543` `NewPostgresWorkingCapitalLoanTransactionRepository`
- `postgres.go:548` `Insert`
- `postgres.go:579` `FindByLoanID`
- `postgres.go:622` `loadAllocation`
- `postgres.go:667` `NewPostgresWorkingCapitalLoanPaymentAllocationRuleRepository`
- `postgres.go:673` `Upsert`
- `postgres.go:690` `FindByLoanID`
- `productdetails.go:36` `StoredValue`
- `productdetails.go:38` `String`
- `productdetails.go:48` `WorkingCapitalLoanPeriodFrequencyTypeFromString`
- `productdetails.go:74` `StoredValue`
- `productdetails.go:76` `String`
- `productdetails.go:85` `IsEIR`
- `productdetails.go:90` `WorkingCapitalAmortizationTypeFromString`
- `productdetails.go:120` `StoredValue`
- `productdetails.go:122` `String`
- `productdetails.go:134` `WorkingCapitalStartTypeFromString`
- `transaction.go:26` `Total`
- `transaction.go:32` `ForPrincipalAllocation`
- `transaction.go:38` `ForPortions`
- `transaction.go:50` `ForChargeAccrual`
- `transaction.go:60` `ForCreditBalanceRefund`
