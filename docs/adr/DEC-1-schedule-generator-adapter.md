# DEC-1 — Schedule-generator adapter contract

**Status: DRAFT — awaiting ratification (user gate T6)**

| | |
|---|---|
| Decision id | DEC-1 |
| Bounded context | `loanschedule` (loan repayment schedule generation) |
| Run | `2026-08-17-run1-harness-schedule-poc`, task T4 |
| Artefact ratified | `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reference oracle | Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| Input analysis | `docs/analysis/progressive-schedule-behavior.md` |
| Supersedes | — |

---

## 1. Amendment is a `user` decision gate

**Ratification of DEC-1, and any subsequent change to it, is a `user` decision gate. No agent may amend this ADR or the Go package it ratifies.**

This is not a style rule. It has teeth for three reasons:

1. **The contract is the strangler boundary.** Every call site in Gerege Nexus that needs a repayment schedule depends on `contract.ScheduleGenerator` and on nothing else. Both the Fineract-JVM adapter and the Go native module are written to this shape. A change to the shape is a simultaneous change to two implementations and every caller.
2. **The contract is the golden-vector encoding.** Each captured vector is a `GenerateRequest` and its oracle-produced `Schedule`. A field added, removed, renamed or retyped invalidates the corpus: the vectors must be re-captured against the reference oracle, and every parity claim already made is void until they are.
3. **The contract is what a regulator is shown.** The parity argument presented for FRC / parallel-run sign-off is "these two implementations answer the same question identically." That argument is only auditable if the question stopped moving.

An agent that believes the contract is wrong records the finding in the run's backlog and **stops**. It does not edit `contract.go`, and it does not work around the contract by adding a second entry point.

The scope of the gate is the whole of `contract.go`: identifiers, types, field order-independent semantics, doc comments (the doc comments *are* the specification — the rounding policy, the ordering rule and the sign convention exist nowhere else), and the enum value domains.

---

## 2. Context

The migration ports Fineract to Go one bounded context at a time behind a frozen adapter contract. The first context is loan repayment schedule generation, whose Fineract implementation is the progressive-loan embeddable schedule generator: a Spring-free entry point of roughly 182 lines wrapping the progressive-loan EMI calculator.

The reference oracle's own entry point is:

```java
LoanSchedulePlan generate(MathContext mc, LoanRepaymentScheduleModelData modelData)
```

with a 19-field input record and a plan carrying a heterogeneous list of disbursement / down-payment / repayment rows plus eight aggregate totals. That signature is unusable as a migration boundary as it stands:

- **`MathContext`** is a Java type; the precision and tie rule it carries are real inputs to the answer, but the class is not portable.
- **`BigDecimal` principal and a percentage-shaped `BigDecimal` rate** are the reference oracle's money and rate representations. This program's non-negotiable is integer minor units and no floating point anywhere on a money path.
- **`CurrencyData`, `DaysInMonthType`, `DaysInYearType`, `DaysInYearCustomStrategyType`, `InterestMethod`, `PeriodFrequencyType`** are Fineract types and enum names.
- **Dead and unreachable fields.** `allowFullTermForTranche` cannot be reached through the embeddable single-disbursement path at all; `daysInYearCustomStrategy` is unreachable under the fixed 360-day year; `allowPartialPeriodInterestCalculation` is a behaviour switch rather than a loan term.
- **Eight aggregate totals in the response**, every one of them a sum over the period rows.
- **No time zone anywhere**, only bare `LocalDate`.

The behavioural facts the contract must accommodate, all established by the input analysis against the pinned checkout:

- The level installment is produced by a **recurrence** (`fn_1 = 1`, `fn_k = 1 + fn_{k-1} × (1 + rateFactor_k)`), not by the closed-form annuity formula. The recurrence exists so that per-period rate factors may differ — interest pauses, rate changes — so the contract must not assume a single constant per-period rate.
- Intermediates are exact decimals rounded to a caller-supplied significant-digit count under a caller-supplied tie rule (12 digits `HALF_UP` in the shipped conformance test; 19 digits, tenant-configured tie rule, in the hosted application). Currency-scale rounding to the currency's minor unit happens **once**, when a quantity becomes money.
- The default day count is a **fixed 30/360** — not 30E/360, not 30/360 US — with an actual/actual path also present.
- Per period, **interest is computed first from the outstanding balance and principal is the balancing remainder** of the installment. The **last unpaid period absorbs the entire accumulated rounding residual** onto its installment, which is what forces total principal repaid to equal total principal advanced to the minor unit.

## 3. Decision

Adopt the Go package `github.com/gerege/nexus/internal/apps/loanschedule/contract` as the frozen adapter contract for the loan-schedule bounded context. Its whole surface is:

```go
type ScheduleGenerator interface {
    Generate(ctx context.Context, req GenerateRequest) (Schedule, error)
}
```

with request types `GenerateRequest`, `Currency`, `Rounding`, `Disbursement`, `Rate`, `CivilDate` and the enums `RepaymentFrequencyUnit`, `DayCountConvention`, `InterestMethod`, `RoundingMode`; response types `Schedule`, `Period`, `PeriodKind`; and the two sentinel errors `ErrInvalidRequest` and `ErrUnsupportedConfiguration`.

Thirteen request fields, seven response fields per row, one response field at the top level. Nineteen reference-oracle inputs and eleven reference-oracle response members reduce to that, and the reduction is justified field by field below.

### 3.1 Design rules applied

A field is in the contract if and only if:

1. it changes the numeric answer, **and**
2. it is a property of the loan being scheduled, not of the implementation computing it, not of a neighbouring bounded context, **and**
3. both implementations consume it, **and**
4. it cannot be recomputed from the other fields — with one stated exception, `OutstandingPrincipalMinor` (§4.3).

Where evolution was foreseeable and cheap, the contract prefers **widening a value domain over changing a shape**: an enum gains a member, a slice gains a legal cardinality. Both are still `user`-gated changes, but neither invalidates the struct layout, the wire encoding or a vector's field set. This is the single concession made to forward compatibility, and it is applied in exactly three places (`DayCountConvention`, `InterestMethod`, `Disbursements`), each argued in §6.

---

## 4. Field-by-field rationale

### 4.1 Request

| Field | Type | Units | Why it exists | Why this type |
|---|---|---|---|---|
| `TimeZone` | `string` | IANA zone name | Every civil date in the request and the response is a calendar day in some zone; leaving that implicit is how a UTC offset gets smuggled across a boundary. Downstream contexts (aging, COB) inherit the zone rather than guessing it. | An IANA name, never a fixed offset and never a `time.Time`. `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07); neither observes DST, so a named zone pins a civil day unambiguously. A `time.Time` would carry both a location and an instant, either of which can silently shift a due date across midnight. One zone per request, not one per date: a loan is scheduled in one place. |
| `Currency.Code` | `string` | ISO 4217 alpha-3 | An `int64` with no currency is meaningless, and a captured vector must be self-describing. | Alpha-3 (`"MNT"`; ISO 4217 numeric 496). The numeric code is a redundant second identifier and is omitted. Name, symbol and display label are presentation, not arithmetic, and are omitted. |
| `Currency.MinorUnitDigits` | `int32` | decimal places | It is the scale of the currency rounding layer — the point at which a computed quantity becomes a payable amount. Not hard-coded to 2 because the reference oracle's shipped conformance vectors are in USD and the field is a genuine input. | An integer exponent. MNT is 2: 1,250,000.00 MNT is `125000000`. Storage is 2 decimal places (ISO); the 0-decimal postfix display (`1,250,000₮`) is a UI concern and is not in the contract. |
| `Rounding.IntermediatePrecisionDigits` | `int32` | significant decimal digits | Changes the answer: the same loan at 12 and at 19 significant digits can differ by a minor unit. It must travel with the request so a vector records the policy it was captured under, and because a single compiled-in constant would be wrong for one of the two real configurations (hosted 19, embeddable test 12). | A count, not a scale. Significant digits, because that is what bounds a non-terminating division such as 30/360 or rate/100. |
| `Rounding.Mode` | `RoundingMode` | — | Tie-breaking changes the answer at the half. | A closed enum of two members (§5.2), not a Java `RoundingMode` and not a string. |
| `ScheduleStartDate` | `CivilDate` | civil date | Seeds the repayment period boundaries: period *n* is due this date advanced by *n* × `RepaymentEvery` frequency units. Distinct from a disbursement date because the two can legitimately differ, and collapsing them makes the boundary unable to express a loan whose repayments start on a different date from the advance. | `CivilDate` (§5.3). The month-end clamping rule (31 Jan +1 month = 28 Feb, then 28 Mar, not 31 Mar) is specified in its doc comment because Go's and Java's month arithmetic differ and both implementations must agree; it is covered by vectors. |
| `Disbursements` | `[]Disbursement` | — | The principal advanced and when. Without it there is no loan. | A slice with exactly one legal element today, rejected otherwise with `ErrUnsupportedConfiguration`. Argued in §6.1. |
| `Disbursement.Date` | `CivilDate` | civil date | Interest accrual and, if enabled, the down-payment period are anchored to it. | `CivilDate`. |
| `Disbursement.AmountMinor` | `int64` | minor units | The principal. | `int64` minor units. The reference oracle takes a `BigDecimal` in major units; converting at the adapter is the adapter's job and is exact in that direction (an integer count of minor units is always an exact decimal). No float, no decimal string. |
| `NumberOfRepayments` | `int32` | count | The term length in installments. | A count. Excludes any down-payment period, which is not a repayment. |
| `RepaymentEvery` | `int32` | count of frequency units | "Repayment every N months/weeks/days". | A count. Kept separate from the unit so that "every 2 weeks" needs no new enum member. |
| `RepaymentFrequencyUnit` | `RepaymentFrequencyUnit` | — | Selects both the period-stepping calendar unit and the day-count expansion of the interest fraction. | A closed enum of four members. The reference oracle's `PeriodFrequencyType` additionally carries `WHOLE_TERM` and `INVALID`; `INVALID` is a sentinel this contract expresses as a rejected request, and `WHOLE_TERM` is not reachable through the embeddable path. Passed as a `String` in the reference oracle and parsed by name — a stringly-typed input this contract refuses to inherit. |
| `AnnualNominalInterestRate` | `Rate` | dimensionless fraction per annum | The rate. | Exact integer rational in canonical lowest terms (§5.1). 24% p.a. is `Rate{24, 100}`; zero interest is `Rate{0, 1}` and is a supported, non-special-cased case. Explicitly a *fraction*, not the reference oracle's percentage-shaped decimal where `7.0` means 7% — that shape has produced a factor-of-100 error in every system that has ever carried it. |
| `InterestMethod` | `InterestMethod` | — | The response has no meaning without knowing which method produced it, and a vector must record it. | A closed enum with one legal member today (`InterestMethodDecliningBalance`); anything else is `ErrUnsupportedConfiguration`. Argued in §6.2. |
| `DayCount` | `DayCountConvention` | — | Converts the annual nominal rate into a per-period interest fraction. Changes every period's interest. | **One** enum, not the reference oracle's (days-in-month, days-in-year) pair. Argued in §6.3. |
| `DownPaymentPercentage` | `Rate` | dimensionless fraction of principal | Adds a down-payment row to the response and reduces the principal amortized across repayment periods. Since the response must model a down-payment row (the reference oracle emits one), the request must be able to ask for one, or the response has a row kind nothing can produce. | `Rate`, same exactness argument as the interest rate. `Rate{0, 1}` means none. **One field, not two**: the reference oracle carries both a boolean and a percentage, admitting the contradictory state "enabled at 0%". |
| `InstallmentRoundingMultipleMinor` | `int64` | minor units | Rounds the installment (and down payment) to a whole multiple — near-universal in Mongolian retail lending, where installments are quoted in whole 100 MNT. It changes the value of *every* row, so it cannot be layered on later without re-capturing every vector. | `int64` minor units; `0` means no rounding. Semantics pinned in the doc comment: nearest multiple under `Rounding.Mode`, never always-up or always-down, and a positive installment is never rounded to zero. |

**The known parity hazard this field carries, and how the contract disposes of it.** In the reference oracle the installment and the down payment round to a multiple through two different overloads: the down payment uses the threaded `MathContext`, the installment silently falls back to the tenant-global one, and outside an initialised tenant that fallback throws. The contract resolves this by fiat: **both use `Rounding.Mode`**, and the Fineract-JVM adapter is obliged to initialise its tenant rounding mode to `Rounding.Mode` before every call. That obligation is an adapter conformance requirement, verified by a vector that exercises a non-zero multiple. It is recorded in the backlog (§8) as work, not as an open question about the contract.

### 4.2 Deliberately absent from the request, and the constant the adapter pins

The Fineract-JVM adapter must construct a 19-field `LoanRepaymentScheduleModelData`. Six of its fields have no counterpart here. This table is normative: it is what makes the adapter fully determined by the contract, and a conformance obligation on the Go module to behave as if these constants held.

| Reference-oracle input | Pinned to | Why it is not a contract field |
|---|---|---|
| `allowFullTermForTranche` | `false` | Dead on the single-disbursement path — no builder setter reaches it. |
| `allowPartialPeriodInterestCalculation` | `true` | A behaviour switch, not a loan term. With a single disbursement and no mid-term rate change, interest sub-periods coincide with repayment periods and the switch is inert. Pinning it removes a degree of freedom that would otherwise need vectors on both settings. |
| `interestRecognitionOnDisbursementDate` | `false` | A behaviour switch shifting accrual by one day. Every planned vector pins it false. Named in §6 as a forward risk. |
| `fixedLength` | `null` | Overrides the final due date in days and interacts ambiguously with `NumberOfRepayments`. Niche; backlogged (§8). |
| `daysInYearCustomStrategy` | `null` | A leap-day override reachable only under an actual-days year, where it would arrive as a `DayCountConvention` member rather than a field (§6.3). |
| `currency.inMultiplesOf` | `null` | Applies only when the currency has zero decimal places. MNT is stored at 2, so it is inert. Distinct from `InstallmentRoundingMultipleMinor`, which is the loan-product rounding and *is* in the contract. |

Also absent, and never to be added here: borrower or party identity of any kind (a schedule generator does not need to know who is borrowing; should a party ever be required anywhere in this program, names are three fields — ovog, patronymic, given name — never `first_name` / `last_name`), loan or account identifiers, product catalogue references, tenant identifiers, business dates, charges, taxes, ledger accounts, and any notion of insurance, protection or guarantee.

### 4.3 Response

| Field | Type | Units | Why it exists | Why this type |
|---|---|---|---|---|
| `Schedule.Periods` | `[]Period` | — | The schedule. | A slice in a total, derivable order (§5.4). `Schedule` is a one-field struct rather than a bare `[]Period` so the response can gain a field in a later ratified version without changing the interface's return type. |
| `Period.Kind` | `PeriodKind` | — | The reference oracle's plan is a heterogeneous list of three row types (disbursement, down payment, repayment) distinguished by Java subclass. A Go contract expresses that with a discriminator rather than an interface with type assertions at every call site. | A closed enum of three members. It also carries the sign convention (§5.5). |
| `Period.InstallmentNumber` | `int32` | count | Identifies the payable installment. | A dense 1-based counter running across down-payment and repayment rows — verified against the reference oracle, which increments a single shared counter for both. `0` for a disbursement row, which is not payable; this is the one place a Java `null` is normalised, and it is normalised to a value that cannot collide with a real installment. |
| `Period.FromDate`, `Period.DueDate` | `CivilDate` | civil dates | Interest accrues over `[FromDate, DueDate)`; the amount falls due on `DueDate`. Both are outputs of the date-stepping rule, which is itself a parity target. | `CivilDate` in `TimeZone`. |
| `Period.PrincipalMinor` | `int64` | minor units | The principal component. | `int64` minor units, never negative. |
| `Period.InterestMinor` | `int64` | minor units | The interest component. | `int64` minor units, never negative; `0` on disbursement and down-payment rows. |
| `Period.OutstandingPrincipalMinor` | `int64` | minor units | The balance carried forward after this row. | `int64` minor units. **The one carried-but-arguably-derivable field**, kept for two reasons: the reference oracle clamps this roll-forward at zero rather than computing a pure running difference, so it and `advanced − Σ principal` are not provably identical in every configuration; and it is the field against which the per-period amortization invariant is checked without summing the whole schedule. |

### 4.4 Deliberately absent from the response

Every one of the reference oracle's eight aggregate totals, its currency echo, its loan term in days, its per-row total due and its per-row total outstanding are **sums or spans over the rows**. Carrying them would create a second source of truth: an implementation could be right about the split and wrong about the sum, and conformance would have to decide which is authoritative. Callers that want a total sum the rows.

Two omissions carry their own argument:

- **No level-installment (EMI) field.** The installment is `PrincipalMinor + InterestMinor` on any ordinary row. Omitting it is what makes the **final-period balancing residual expressible without loss**: the last unpaid period absorbs the whole accumulated rounding residual onto its installment, so its total differs from the others'. A separate EMI field would either contradict the last row or need a second "adjusted EMI" field beside it. With no EMI field, the residual is simply visible as the last row's split, and it is impossible to encode a schedule whose stated installment disagrees with its own split.
- **No per-row fee or penalty.** Charges, rates and taxes are a Tier A bounded context and are explicitly out of scope for DEC-1. The reference oracle's plan carries fee and penalty columns which are identically zero under this contract's pinned configuration, since no charge is ever attached. Named in §6 as the highest forward risk.

---

## 5. The load-bearing type decisions

### 5.1 Rates: exact integer rational, not basis points

`Rate{Numerator, Denominator}` is a dimensionless fraction in canonical lowest terms with `Denominator > 0`. 7% per annum is `Rate{7, 100}`.

**Why not a float.** Non-negotiable, and the reference oracle contains no float on this path either: the only `double` in the whole traced call chain is inside a JUnit assertion helper. A float rate would diverge from the oracle after enough compounding periods.

**Why not basis points.** An integer basis-point field cannot express a rate finer than 0.01%: 0.125% per annum is 12.5 basis points and has no integer encoding. That rate is nonetheless a perfectly ordinary decimal percentage the reference oracle consumes exactly. So the set of rates a rational expresses exactly is strictly larger than the set integer basis points express exactly, at a cost of one `int64`. Every rate in the planned vector matrix (24.00, 18.50, 21.75, 19.99, 16.40, 13.75, 12.00, 15.00, 30.00, 36.00, 0.00) is expressible in either representation; the argument for the rational is about the rates the contract must not be unable to carry later, given that adding a field is a `user` gate.

**Why canonical form is mandatory.** A rational has infinitely many spellings of the same value (`7/100`, `70/1000`, `14/200`). Requiring lowest terms with a positive denominator makes structural equality equal value, which matters because vector comparison and request deduplication are structural. `Rate{}` (0/0) is therefore invalid, and a zero rate is exactly `Rate{0, 1}` — consistent with the `Unspecified` enum zero values, so a never-populated request fails loudly instead of silently meaning "0% declining balance, 30/360, daily".

**Precision through the conversion.** The contract's job is to deliver the rate exactly to the arithmetic; what happens next is the rounding policy's job. The reference oracle divides the percentage by 100 and then multiplies by a day-count fraction, both under the intermediate rounding layer. A `Rate` reaches that arithmetic with zero prior loss, and the first rounding that occurs is one the contract specifies.

**One representable-domain constraint, stated honestly.** The Fineract-JVM adapter must render the rate as the decimal percentage its input record expects. A rate whose reduced denominator has a prime factor other than 2 or 5 (`Rate{1, 3}`) has no exact terminating decimal percentage and cannot be handed to the reference oracle without a rounding decision. Such a request must be rejected with `ErrUnsupportedConfiguration` rather than silently rounded. No real product quotes a rate of one third of one percent, and the restriction is a property of the reference oracle rather than of the representation — a basis-point field would hide the same limit behind a coarser one.

### 5.2 Rounding policy without a `MathContext`

Java's `MathContext` carries exactly two things: a significant-digit count and a tie-breaking rule. `Rounding` carries exactly those two things, as an `int32` and a closed enum. The Java class does not cross the boundary; its information content does.

The contract additionally specifies **where** rounding happens, because a precision alone is not a policy:

1. **Intermediate layer.** Every dimensionless intermediate — the per-period interest fraction, its running product, the `fn` recurrence, the level installment before it becomes money — is rounded to `IntermediatePrecisionDigits` significant decimal digits under `Mode` after each multiplication and each division. Intermediates are *ratios, not money*, and are explicitly not `int64` minor units. This is the single most important thing the contract says: a Go implementation that models intermediates as money, or as exact rationals rounded only at the end, will not match the oracle, because rounding to N significant digits at each division is observable in the result.
2. **Currency layer.** A quantity becomes money exactly once, when it is scaled to `Currency.MinorUnitDigits` decimal places under the same `Mode` and recorded as an `int64`. Money is never re-rounded after that.

**One mode, not two.** The reference oracle derives its currency-scale tie rule from the same source as its intermediate tie rule. Two independently settable modes would admit combinations no deployment can produce and would double the vector matrix.

**Why the mode enum has two members.** Each admitted mode is a distinct tie-breaking behaviour both implementations must prove identical against captured vectors. `RoundingHalfUp` reproduces the reference oracle's shipped conformance test; `RoundingHalfEven` is the other mode a financial deployment plausibly configures. The remaining five Java modes are not admitted: no product and no vector requires them, and each would be contract surface carrying an unproven claim. Admitting one later is a value-domain widening (§6.4).

**What is deliberately *not* a field: the order of rounding operations.** The order in which the schedule algorithm multiplies, divides and rounds is fixed by the algorithm, is documented in the input analysis, and is proven by golden vectors. It is a conformance obligation, not a parameter. A contract field for it would be a licence to disagree.

### 5.3 Dates: civil dates plus one named zone

`CivilDate{Year, Month, Day}` — a date on the proleptic Gregorian calendar with no time, no offset and no instant — plus one `TimeZone` IANA name on the request.

Not `time.Time`: it carries a location and an instant, either of which reintroduces a midnight-boundary bug or an implicit UTC. Not a date string: parsing is a second place to disagree. Not a hard-coded offset: `Asia/Ulaanbaatar` is +08 and `Asia/Hovd` is +07 today, and an offset literal encodes a fact about a zone into a field that should name the zone. Neither zone observes DST, so a named zone pins a civil day unambiguously — but the contract names zones rather than relying on that, because relying on it is how DST bugs are written.

The generation arithmetic itself is zone-free civil-date arithmetic. The zone is carried so that no caller can smuggle an implicit offset across the boundary, and so that downstream contexts inherit an explicit zone rather than guessing one. `CivilDate{}` is invalid.

### 5.4 Deterministic ordering

`Schedule.Periods` is ordered: non-decreasing by `DueDate`; ties broken by `Kind` (disbursement before down payment before repayment); remaining ties broken by ascending `InstallmentNumber`.

This is a **total order derived from the values themselves**, not from any implementation's loop structure, so two implementations agree on it without mirroring each other's control flow. It was checked against the reference oracle's emission order, including the case where a disbursement row falls inside a later repayment window and the case where a disbursement falls after the maturity date; the derived order reproduces the emitted order in both.

No map appears anywhere in the contract and no map iteration order is ever observable through it. Two `Schedule`s are equal when their `Periods` are element-wise equal in this order.

### 5.5 Sign convention

`PrincipalMinor` is never negative. On a disbursement row it is principal advanced **to** the borrower; on the other rows it is principal repaid **by** the borrower. The direction is carried by `Kind`, not by a negative number, so that no consumer can sum the column without first deciding what it is summing. This is the same discipline the ledger non-negotiable enforces elsewhere: direction is structural, never a sign bit.

---

## 6. Forward-compatibility analysis

The question: does this contract survive the arrival of GL/accounting (Tier A), the full loan lifecycle, and charges/rates/tax, without a shape change? Ordered by descending risk.

### 6.1 Multi-tranche disbursement — mitigated, shape holds

**Risk if unmitigated: certain.** Tranche machinery already exists in the reference oracle (`processDisbursements` over a list, a post-loop tranche pass, full-term re-amortization) and is merely unreachable from the embeddable single-disbursement entry point. It arrives with the loan lifecycle, which is Tier A, which is the next runs.

**Mitigation applied.** `Disbursements` is a slice from day one, with exactly one legal element today. Widening to *n* is a value-domain change: no struct changes, no field is added, no captured vector's field set moves. Turning a scalar pair into a list later would have been a shape change invalidating the whole corpus.

**Cost, stated plainly.** A slice that must have length one is a validation rule the contract must carry, and it is contract surface no Run-1 vector exercises. That is the price of not re-capturing every vector in Run 2, and it is the right trade because the arrival of tranches is not speculative — it is already-built oracle behaviour named in the analysis backlog.

`DownPaymentPercentage` stays a single top-level field under multi-tranche: the reference oracle computes the down payment per disbursement from one product-level percentage.

### 6.2 A second interest method (flat) — mitigated, shape holds

The flat-interest path is a materially different formula and is backlogged for its own analysis. Because `InterestMethod` is already a field, admitting it is an enum member, not a struct change. If the field did not exist, the contract would silently mean "declining balance forever" and every captured vector would be ambiguous about what produced it.

### 6.3 Further day-count conventions — mitigated, shape holds

The reference oracle carries a (days-in-month × days-in-year) cross product plus a leap-day override strategy. The contract collapses this to one `DayCountConvention` enum with the two conventions in use. Adding 30/365, ACT/360 or the leap-day variant is an enum member. Had the contract mirrored the oracle's pair, it would have carried three fields, admitted combinations no product uses, and still needed a fourth field for the override strategy.

The one thing lost: a combination outside the named set cannot be requested. That is intentional. A named convention is auditable; a pair of independently-set constants is a configuration puzzle.

### 6.4 The rounding mode's value domain — low risk, shape holds

The reference oracle's production tie rule is per-tenant configuration that the analysis could not trace and flagged unverified. If the reference instance turns out to be configured to a mode outside `{HalfUp, HalfEven}`, the contract needs a new enum member — a value-domain widening, still a `user` gate, but not a shape change and not a vector re-capture beyond the affected rows. Resolving the reference instance's actual tie rule is backlogged (§8) and should be settled before large-scale vector capture.

### 6.5 Charges, fees, penalties and tax — the highest unmitigated risk

**Named as the most likely cause of a future shape change.** The reference oracle's plan already has fee and penalty columns; when the charges context lands, a repayment row acquires further components and `Period` gains fields.

**Why it is nonetheless acceptable:**

- Charges are explicitly out of scope for DEC-1. Encoding zero-valued charge fields now would be building an out-of-scope context's data model on speculation, and the shape guessed today would very likely be wrong: a charge is not one number per period but a set of applied charges with types, timing and tax treatment.
- **The response was shaped so that the addition is purely additive.** Because there is no `TotalDueMinor` field, no existing field's meaning changes when charges arrive: `PrincipalMinor` and `InterestMinor` mean today exactly what they will mean then. Had the contract carried a total-due column, that column would have silently changed meaning — the most dangerous kind of contract change, because it does not break a compile.
- The likeliest resolution is not amending `Period` at all, but composing: charges are computed by their own context and applied to a schedule, leaving the schedule-generation boundary intact. DEC-1 does not decide that; it merely does not foreclose it.

### 6.6 Grace periods, interest pauses and mid-term rate changes — real, unmitigated

Interest-only grace, principal grace, an interest pause, and a rate change part-way through the term are loan-lifecycle features. The oracle's `fn` recurrence exists precisely to support per-period rate factors that differ, so the machinery is there; expressing them would need new request fields — most likely a list of dated term events.

Not mitigated speculatively, because the shape of such a list cannot be guessed without the analysis, and a wrong guess frozen into the contract is worse than an honest later amendment. `ScheduleStartDate` being independent of the disbursement date already covers the commonest simple case (repayments starting later than the advance).

### 6.7 `interestRecognitionOnDisbursementDate` — low risk, would be a new field

Pinned `false` (§4.2). If a product ever needs accrual from the disbursement date itself, that is one boolean field added. Cheap, but a `user` gate. It is not added now because no product requires it and no vector exercises it, and a boolean nobody sets is exactly the kind of surface this contract is trying not to accumulate.

### 6.8 GL and accounting (Tier A) — no risk to this contract

The ledger consumes a schedule; it does not change how a schedule is generated. Schedule generation posts nothing, so nothing about double-entry, holds or derived balances reaches this boundary. `Generate` remains a pure function.

### 6.9 What holds under all of the above

`Currency`, `Rounding`, `CivilDate`, `TimeZone`, `Rate`, the `int64` minor-unit money representation, the ordering rule and the `PrincipalMinor` / `InterestMinor` split. These are the fields a reviewer should be most confident in: none of them is a Fineract artefact, and none of them changes meaning when a neighbouring context arrives.

---

## 7. The switch mechanism (described, not implemented)

**Selection is per bounded context, from deployment configuration, resolved once at process start.**

- **Config key.** One key per bounded context, namespaced by context:
  `gerege.contexts.loanschedule.implementation`, whose value is `fineract_jvm` or `go_native`. The key is per context, never global, because the strangler pattern requires contexts to move independently; a single global switch would make the migration one all-or-nothing step.
- **Default.** Absent or unrecognised configuration resolves to `fineract_jvm` — the reference oracle — never to the Go module. An unconfigured deployment falls back to the implementation that is already the source of truth. An unrecognised value fails startup loudly rather than falling back silently.
- **Resolution.** A registry in the composition root maps the config value to an implementation and returns it as a `contract.ScheduleGenerator`. Resolution happens once, at startup, not per request: a per-request switch would make a single business operation's behaviour depend on when it ran, and would make an incident impossible to reconstruct.
- **Call sites.** Every caller depends on the interface only. No caller imports either implementation, branches on the config value, or type-asserts. This is what makes the switch a one-line configuration change rather than a code change, and it is a reviewable property: a caller importing an implementation package is a rejection.
- **Observability.** The resolved implementation is recorded at startup and carried on every generated schedule's audit trail, so any schedule can be attributed to the implementation that produced it. The mechanism for that recording is outside this contract; the requirement is not.
- **Configuration source.** Deployment configuration (environment or config file), per environment. Not a database row, not a runtime feature-flag service: the value must be reconstructible from the deployment artefact for an audit.

**What this section does not do.** It does not describe, plan or authorise changing the value in any live environment. **Flipping a context from `fineract_jvm` to `go_native` is a cutover, and cutover is a separate `user` decision gate** requiring passing vectors, a clean shadow-parity window and regulatory / parallel-run sign-off. DEC-1 defines only that a switch point exists and where it lives.

---

## 8. Backlog (out of scope)

Found while designing this contract; recorded, not acted on.

1. **The reference instance's actual rounding tie rule** is unverified (per-tenant configuration outside the analysed module). It determines whether `RoundingMode` needs a member beyond `HalfUp` / `HalfEven`. Should be settled before large-scale vector capture.
2. **The `InstallmentRoundingMultipleMinor` adapter obligation.** The Fineract-JVM adapter must initialise its tenant rounding mode to `Rounding.Mode` so the oracle's two divergent rounding call sites agree; otherwise a non-zero multiple either throws outside an initialised tenant or rounds the installment and the down payment under different tie rules. Needs a dedicated vector.
3. **Flat interest** — a materially different formula, needs its own behaviour analysis before `InterestMethod` gains the member.
4. **`fixedLength`** (force the total term length in days, overriding the final due date) — omitted as niche and ambiguous against `NumberOfRepayments`. If a product needs it, it is a new request field and a `user` gate.
5. **Grace periods, interest pauses, mid-term rate changes** (§6.6) — need analysis before any contract shape is proposed.
6. **Charges, fees, penalties, tax** (§6.5) — Tier A; likely a composing context rather than an amendment here.
7. **Holiday and non-working-day adjustment of due dates** — the reference oracle threads holiday details through date generation; not reachable from the embeddable entry point and not represented here. Relevant once a Mongolian public-holiday calendar governs due dates.
8. **Error taxonomy.** Two sentinels are deliberately all the contract carries. If operational experience shows callers need to distinguish rejection reasons, that is a `user`-gated widening.

---

## 9. Consequences

**Accepted:**

- Every caller in Gerege Nexus depends on one interface with one method, and both implementations are interchangeable behind it.
- Money is `int64` minor units across the whole boundary; no float, decimal string or float-backed decimal type exists in or is implied by the contract. Rates are exact rationals. Dates are civil dates in a named IANA zone.
- The rounding policy is expressible without a Java `MathContext`, so both implementations round identically by specification rather than by coincidence.
- The response expresses the per-period principal/interest split and the final-period balancing residual without loss, and cannot encode a schedule that contradicts itself, because every aggregate is derived rather than carried.
- Golden vectors have exactly one legal encoding, so vector comparison is structural equality.

**Costs, accepted knowingly:**

- Six reference-oracle inputs are pinned to constants (§4.2). If any needs to vary, that is a contract amendment and a `user` gate.
- Three places carry surface no Run-1 vector exercises — a one-element slice, a one-member interest-method enum, and a `DayCountConvention` with two members — bought deliberately to convert foreseeable shape changes into value-domain widenings.
- Charges will most likely require either an amendment to `Period` or a composing context (§6.5). This is the largest known unmitigated risk and is named rather than papered over.
- Callers wanting totals must sum the rows.

**Obligations created:**

- The Fineract-JVM adapter must pin the six constants in §4.2, must initialise its tenant rounding mode to `Rounding.Mode`, and must convert `int64` minor units and `Rate` to the oracle's decimal inputs without a float ever existing at the boundary.
- The Go module must reproduce the recurrence (not the closed-form annuity formula), the two-layer rounding at the specified points and in the specified order, the fixed-30/360 convention, Java's month-end clamping in date stepping, and the final-period residual absorption.
- **A PASS on conformance means "matches the reference oracle on captured vectors." It never means "safe to cut over."**
