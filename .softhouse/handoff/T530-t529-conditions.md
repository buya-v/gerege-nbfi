# T530 — apply T529's two conditions on T526

Branch: `softhouse/T530-t529-conditions`
Reference oracle (Fineract) pinned commit of record: `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(confirmed by reading `/home/user/fineract/.git/HEAD` directly — this worktree is
isolated and refuses `git -C` against the shared Fineract checkout).

Target Java: `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/RepaymentPeriod.java`, **537 lines**.

## Tally

| | count |
|---|---|
| `RepaymentPeriod.java` citations checked (whole package) | **52** |
| moved (stale range corrected) | **38** |
| already correct | **12** |
| had no line range at all (`@Setter`), tightened to one | **2** |
| **substantive mismatches (Java does not support the Go sentence)** | **1** |

I did not sample. Every row below was re-derived from the pinned Java, then
re-checked a second time by a brace-counting script that derives each method's
signature-to-closing-brace span mechanically and matches it against every
citation in the package. That script found **five citations my first
grep-based enumeration missed** (they sit on comment continuation lines that do
not contain the word `VERIFIED`), which is why the total is 52 and not 47.
Final state: **0 unresolved**.

## Method spans, derived mechanically from the pinned file

`empty` 138-141 · `create` 143-151 · `copy` 153-171 · `copyWithoutPaidAmounts` 173-198 ·
`getPrevious` 200-202 · `getRateFactorPlus1` 209-214 · `calculateRateFactorPlus1` 216-218 ·
`getCalculatedDueInterest` 226-233 · `calculateFixedInterestTillDate` 235-250 ·
`calculateCalculatedDueInterest` 252-265 · `getDueInterest` 272-286 ·
`getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest` 293-295 · `getCalculatedDuePrincipal` 302-305 ·
`getCreditedPrincipal` 312-316 · `getCreditedInterest` 323-327 · `getCapitalizedIncomePrincipal` 334-338 ·
`getDuePrincipal` 345-350 · `getTotalCreditedAmount` 357-360 · `getTotalPaidAmount` 367-369 ·
`isFullyPaid` 371-373 · `getUnrecognizedInterest` 381-383 · `getCreditedAmounts` 385-387 ·
`getOutstandingLoanBalance` 389-403 · `addPaidPrincipalAmount` 405-407 · `addPaidInterestAmount` 409-411 ·
`getInitialBalanceForEmiRecalculation` 413-427 · `getZero` 429-431 · `getFirstInterestPeriod` 433-435 ·
`getLastInterestPeriod` 437-440 · `findInterestPeriod` 442-447 · `isFirstRepaymentPeriod` 449-451 ·
`getOutstandingInterest` 458-460 · `getOutstandingPrincipal` 462-464 · `resetDerivedComponents` 466-469 ·
`calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod` 476-492 · `getCurrency` 494-499 ·
`getEmi` 501-503 · `getOriginalEmi` 505-507 · `getPaidPrincipal` 509-511 · `getPaidInterest` 513-515 ·
`getFutureUnrecognizedInterest` 517-519 · `getTotalDisbursedAmount` 521-523 ·
`getTotalCapitalizedIncomeAmount` 525-527 · `getFixedInterest` 529-531 · `moveOutstandingDueToReAging` 533-536

## Full citation table

`repaymentperiod.go` (39 citations). "Drift" = true start − cited start.

| Go symbol | cited | true | drift | verdict |
|---|---|---|---|---|
| struct field list | 60-97 | **46-113** | −14 | MOVED — cited range omitted `previous`, `fromDate`, `dueDate`, `interestPeriods`, `emi` at the head and all five re-age/fixed-interest fields at the tail, every one of which IS in the Go struct |
| `NewRepaymentPeriod` / `create` | 141-147 | **143-151** | +2 | MOVED (141 is `empty`'s closing brace) |
| `Previous` / `getPrevious` | 214-216 | **200-202** | −14 | MOVED — cited range straddles `getRateFactorPlus1`'s brace and `calculateRateFactorPlus1` |
| `Emi` / `getEmi` | 417-419 | **501-503** | +84 | MOVED — cited range is inside `getInitialBalanceForEmiRecalculation` |
| `OriginalEmi` / `getOriginalEmi` | 421-423 | **505-507** | +84 | MOVED — same wrong method |
| `FirstInterestPeriod` | 292-294 | **433-435** | +141 | MOVED |
| `LastInterestPeriod` | 296-299 | **437-440** | +141 | MOVED |
| `RateFactorPlus1` | 218-229 | **209-218** | −9 | MOVED — cited range began on `calculateRateFactorPlus1`'s closing brace and ran into `getCalculatedDueInterest`'s memo key |
| `CalculatedDueInterest` | 232-241 | **226-233** | −6 | MOVED |
| `CalculateCalculatedDueInterest` | 262-272 | **252-265** | −10 | MOVED |
| `CalculateFixedInterestTillDate` | 243-261 | **235-250** | −8 | MOVED |
| `DueInterest` | 274-294 | **272-286** | −2 | MOVED |
| `EmiPlusCreditedAmounts…` | 299-301 | **293-295** | −6 | MOVED |
| `CalculatedDuePrincipal` | 306-309 | **302-305** | −4 | MOVED |
| `CreditedPrincipal` | 314-317 | **312-316** | −2 | MOVED |
| `CreditedInterest` | 322-325 | **323-327** | +1 | MOVED |
| `CapitalizedIncomePrincipal` | 330-333 | **334-338** | +4 | MOVED |
| `DuePrincipal` | 338-343 | **345-350** | +7 | MOVED |
| `TotalCreditedAmount` | 348-352 | **357-360** | +9 | MOVED |
| `TotalPaidAmount` | 357-359 | **367-369** | +10 | MOVED |
| `IsFullyPaid` | 361-363 | **371-373** | +10 | MOVED |
| `UnrecognizedInterest` | 369-371 | **381-383** | +12 | MOVED |
| `CreditedAmounts` | 373-375 | **385-387** | +12 | MOVED |
| `OutstandingLoanBalance` | 389-403 | 389-403 | 0 | ALREADY CORRECT (T526) |
| `AddPaidPrincipalAmount` | 405-407 | 405-407 | 0 | ALREADY CORRECT (T526) |
| `AddPaidInterestAmount` | 395-397 | **409-411** | +14 | MOVED — the driver's example, confirmed: 395-397 is inside `getOutstandingLoanBalance`'s body |
| `InitialBalanceForEmiRecalculation` | 399-415 | **413-427** | +14 | MOVED |
| `OutstandingInterest` | 420-422 | **458-460** | **+38** | MOVED — the driver's second example, confirmed |
| `OutstandingPrincipal` | 424-426 | **462-464** | +38 | MOVED |
| `ResetDerivedComponents` | 428-431 | **466-469** | +38 | MOVED |
| `calculateTotalDisbursedAndCapitalizedIncome…` | 436-449 | **476-492** | +40 | MOVED |
| `MoveOutstandingDueToReAging` | 450-453 | **533-536** | +83 | MOVED |
| `IsFirstRepaymentPeriod` | 206-208 | **449-451** | **+243** | MOVED |
| `FindInterestPeriod` | 436-443 | **442-447** | +6 | MOVED **+ SUBSTANTIVE MISMATCH — see finding 1** |
| `SetEmi` | *(no range)* | **57-58** | — | tightened: `@Setter` on the `emi` field |
| `SetOriginalEmi` | *(no range)* | **59-60** | — | tightened: `@Setter` on the `originalEmi` field |
| `copy` | 149-166 | **153-171** | +4 | MOVED |
| `copyWithoutPaidAmounts` | 168-194 | **173-198** | +5 | MOVED |
| `addBalanceCorrectionAmount(negated)` | 192-194 | 192-194 | 0 | ALREADY CORRECT (statement span inside `copyWithoutPaidAmounts`) |

Cross-file `RepaymentPeriod.java` citations (13, all in scope under `loanproduct/`):

| site | cited | true | verdict |
|---|---|---|---|
| `doc.go:125` | 389-403 | 389-403 | ALREADY CORRECT |
| `doc.go:174` | 173-197 | **173-198** | MOVED (off-by-one: cited range stopped on `return`, excluding the closing brace) |
| `doc.go:184` | 389-403 | 389-403 | ALREADY CORRECT |
| `doc.go:254` | 405-407 | 405-407 | ALREADY CORRECT |
| `interestperiod.go:82` | 389-403 | 389-403 | ALREADY CORRECT |
| `interestperiod.go:241` | 389-403 | 389-403 | ALREADY CORRECT |
| `interestperiod.go:251` | 405-407 | 405-407 | ALREADY CORRECT |
| `interestperiod.go:263` | 173-197 | **173-198** | MOVED (same off-by-one) |
| `interestperiod.go:320` | 192-194 | 192-194 | ALREADY CORRECT |
| `interestperiod_test.go:16` | 173-197 | **173-198** | MOVED (same off-by-one) |
| `interestperiod_test.go:40` | 405-407 | 405-407 | ALREADY CORRECT |
| `interestperiod_test.go:77` | 173-197 | **173-198** | MOVED (same off-by-one) |
| `interestperiod_test.go:117` | 192-194 | 192-194 | ALREADY CORRECT |

## T526's systemic claim is false, and the true cause is worse

T526 asserted "roughly a 12-14 line offset in this region." The drift column
above refutes it outright:

- it **changes sign** — −14 at the field list and `getPrevious`, +243 at `isFirstRepaymentPeriod`;
- it is **non-monotonic** — +141, then −9, then +1, then +38, then +6;
- it spans **−14 to +243**, a 257-line range in a 537-line file.

A single neighbouring check would have falsified it, exactly as the dispatch
note says.

**The correct diagnosis is not drift at all.** 34 of the 39 ranges in
`repaymentperiod.go` were wrong, and the only three that were right are the two
T526 derived by hand plus one statement span. A block of citations that is
~87% wrong with sign-changing, non-monotonic error was **never derived against
`426a23544`** — it was estimated, or taken from a different revision. That
distinction matters operationally: "drift" implies a correctable offset and
invites the next agent to apply one, which is precisely the reasoning that
produced these. There is no offset to apply. Each range must be read.

**Why they survived review:** the wrong ranges usually land on a
plausible-looking method. `Emi()` cited `:417-419`, which is inside
`getInitialBalanceForEmiRecalculation` — a method whose name contains "Emi".
`AddPaidInterestAmount` cited `:395-397`, inside a method that adds a paid
amount. They read as right to a sampling reviewer.

## Substantive findings

### Finding 1 (SUBSTANTIVE) — `FindInterestPeriod` diverges from the oracle on two axes

The Go sentence claimed the segment window is "inclusive on both ends". The
Java at the true span **does not support that**, so per the dispatch I did not
re-point the citation at something that happened to match. Both divergences are
real:

1. **Boundary rule.** The oracle filters with
   `isInPeriod(transactionDate, ip.getFromDate(), ip.getDueDate(), isFirstRepaymentPeriod() && interestPeriod.isFirstInterestPeriod())`
   [VERIFIED: `RepaymentPeriod.java:442-447`]. That fourth argument selects the
   rule: `isFirstPeriod ? isDateInRangeInclusive : isDateInRangeFromExclusiveToInclusive`
   [VERIFIED: `LoanRepaymentScheduleProcessingWrapper.java:251-254`]. So both
   ends are inclusive **only** for the first segment of the first repayment
   period; every other segment is **from-EXCLUSIVE**, due-inclusive. The Go
   loop is unconditionally inclusive on both ends, so a transaction dated
   exactly on a later segment's from-date is assigned to that segment, where
   the oracle assigns it to the **preceding** one.
2. **Which match is returned.** The oracle terminates with
   `.reduce((one, two) -> two)` — the **LAST** match. The Go loop returns the
   **first**.

This is a transaction-to-segment assignment rule, so it is money-adjacent.

**Latent, not live:** `FindInterestPeriod` has **no caller anywhere in the
module** (`grep -rn FindInterestPeriod nexus/` returns only its own definition
and doc comment). No captured vector can be moving today.

**What I did:** corrected the citation to `:442-447`, replaced the false
sentence, and added an explicit `DIVERGENCE FROM THE ORACLE — DO NOT CITE THIS
AS PARITY` block naming both axes with citations, plus the note that both
helpers needed for the repair already exist and are graded (`isInPeriod` and
`isDateInRangeFromExclusiveToInclusive` in `dates.go`,
`IsFirstInterestPeriod` in `interestperiod.go`).

**What I did NOT do, and why:** I did not change the behaviour. T530 is a
citation-integrity task; changing a segment-assignment rule moves numbers and
belongs in its own task with a golden vector against the oracle, reviewed by
someone briefed to re-derive the arithmetic rather than the citations.
**Recommend dispatching that fix.** The repair is small (swap the predicate for
`isInPeriod(...)` with `p.IsFirstRepaymentPeriod() && ip.IsFirstInterestPeriod()`,
and keep the last match rather than the first).

### Checked and cleared — not mismatches

Three things that looked like mismatches and are not. Recording them so the next
reader does not re-open them:

- **`create` leaves `creditedPrincipalMovedDueReAge` null; the Go constructor
  zeroes it.** The Java constructor assigns `creditedInterestMovedDueReAge`
  **twice** (`:134` and `:135`) and never assigns
  `creditedPrincipalMovedDueReAge`, which `create` also does not set — so it is
  genuinely null on a freshly created period, and Lombok's `@Getter` returns
  that null. It is nonetheless **observationally equivalent** to zero, because
  the only consumer is `getTotalCreditedAmount`'s `.minus(...)`, and
  `Money.minus(null, mc)` returns `this` [VERIFIED: `Money.java:273-276`];
  `Money.plus(null, mc)` likewise [VERIFIED: `Money.java:240-243`]. Go's
  zero-init matches. (The duplicated assignment is a real upstream Fineract
  bug, but it is inert here.)
- **`calculateFixedInterestTillDate` wraps with the 2-arg `Money.of`
  (`:245`), not `getMc()`.** The 2-arg overload delegates to
  `MoneyHelper.getMathContext()` [VERIFIED: `Money.java:102-104`]. Under the
  ratified tenant parameters that is `(19, HALF_UP)` — identical to the model's
  `mc` — so the Go `moneyOf(p.currency, p.rounding, v)` matches. Worth knowing
  that the two could diverge under a model `mc` differing from the tenant
  default; no such path exists in this port.
- **Money arithmetic on the roll-forward paths** (`OutstandingLoanBalance`,
  `CalculateCalculatedDueInterest`, `DueInterest`, `DuePrincipal`,
  `InitialBalanceForEmiRecalculation`) re-derived operation-for-operation
  against `:389-403`, `:252-265`, `:272-286`, `:345-350`, `:413-427` — summand
  order, `negativeToZero` placement and `max`/`min` operands all agree. No
  float anywhere; `big.Rat` exact sums normalised once at the `Money` boundary,
  matching the oracle's BigDecimal-then-`Money.of` shape.

## Condition 2 — the `doc.go` savings-fold sentence

Struck. The clause "a pure fold over a copy, not itself a write to stored
state, **the same shape as the four sites above**" was false for three of the
four writes, and I verified each receiver in the Go source rather than taking
T529's word:

- `savings/summary.go:52` — `func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary` — **value** receiver, returns a new summary. A fold over a copy.
- `interestperiod.go:272` — `func (ip *InterestPeriod) UpdateOutstandingLoanBalance()` — **pointer** receiver (two of the four flagged writes).
- `interestperiod.go:326` — `func (ip *InterestPeriod) AddBalanceCorrectionAmount(additional Money)` — **pointer** receiver.
- `repaymentperiod.go` `copyWithoutPaidAmounts` — writes into the fresh copy it just built. The only one comparable to the savings fold.

Replacement text does three things: removes the false clause; keeps the
surrounding argument intact; and adds a `DO NOT restate that parenthesis` note
explaining why the slip matters — it smuggled back the conflation the section
exists to refuse. The added text makes the point sharper by observing that if
receiver semantics *were* the criterion the verdicts would invert (the savings
fold, a value receiver, is the guard-flagged one; three of these four, pointer
mutations, are not).

**The load-bearing argument T529 independently verified is preserved verbatim
and unweakened:** the reachability of the folded `AccountBalance` field to
`account_balance_derived` via `PostgresSummaryRepository.Upsert`
[VERIFIED: `savings/postgres.go:113,120,149`], and the conclusion that
reachability — not the receiver — is why the savings site is guard-flagged and
this package's four are not. I did not touch `nexus/internal/apps/savings/`
(read only, to confirm the receiver).

## Discovered but NOT swept — recommend a follow-up task

**`interestperiod.go`'s `InterestPeriod.java` citations have the same defect,
and I did not repair them.** I ran the same mechanical span check against
`InterestPeriod.java` (**238 lines**) and got:

> **28 `InterestPeriod.java` citations in the package; 5 resolve to a method span; 23 do not.**

Roughly four of the 23 are legitimately not method spans (field-list and
annotation-block citations such as `:43-73`, `:48-60`, `:65-66`). That still
leaves ~19 suspect, and **10 of them cite lines past the end of a 238-line
file** and therefore cannot resolve to anything at all:
`:252-254`, `:256-259`, `:299-301`, `:303-305`, `:307-309`, `:311-313`,
`:315-317`, `:319-321`, `:323-325`, `:327-329`.

Three confirmed by reading:
- `interestperiod.go:144` — `Length` cites `:229-231`, which is `getRateFactor`.
- `interestperiod.go:150` — `LengthTillPeriodDueDate` cites `:233-235`, which is `getRateFactorTillPeriodDueDate`.
- `interestperiod.go:156` — `IsFirstInterestPeriod` cites `:252-254`, past EOF; the real `isFirstInterestPeriod` is at `:197-199`.

**I deliberately did not fix these.** A partial audit of a second file's
citation set reproduces exactly the defect under repair — it would make an
unswept remainder look accounted for, which is the specific failure T530 exists
to correct. This needs its own task, sized like T530 and reviewed the same way.

## Scope

Touched only:
- `nexus/internal/apps/loanproduct/repaymentperiod.go`
- `nexus/internal/apps/loanproduct/doc.go`
- `nexus/internal/apps/loanproduct/interestperiod.go` (one citation off-by-one)
- `nexus/internal/apps/loanproduct/interestperiod_test.go` (two citation off-by-ones)
- `.softhouse/handoff/T530-t529-conditions.md`

Not touched: `nexus/internal/apps/savings/`, `.softhouse/conformance.sh`,
`.softhouse/guards/ledgerguard/`. All changes are comments and doc strings —
**zero executable statements changed**, so no vector can move.

## Verification

- `go build ./...` — clean
- `go vet ./...` — clean
- `gofmt -l .` — 4 hits, all pre-existing and none in `loanproduct/`
  (`loanschedule/contract/contract.go`, `parties/client.go`, `parties/group.go`,
  `parties/legalform.go`); no new hits
- `go test ./internal/apps/loanproduct/...` — ok
- `go test ./...` — whole module green
- citation re-check script — **0 unresolved** across all 52 `RepaymentPeriod.java` citations

The repo-wide conformance bar is RED for an unrelated guard repair not on main;
not caused by this branch and not addressed here.

## Push proof

```
$ git ls-remote --heads origin refs/heads/softhouse/T530-t529-conditions
2c58c21b6dbeddf6c79a8e64c304f55bef904d9e	refs/heads/softhouse/T530-t529-conditions
```

The branch is on origin. (The hash above is the pre-amend commit; the amend that
inserted this proof block is pushed on top — re-run the command to see the
current head.)
