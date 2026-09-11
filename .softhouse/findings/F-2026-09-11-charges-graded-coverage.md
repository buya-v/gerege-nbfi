# F-2026-09-11 — the `charges` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written. This run makes the `charges` corpus *measurable* and triages the result.
Grading anything it finds is a later run's work. **No candidate here is a defect.**
**Task:** `OH-CHCOV-AD`, bounded context `charges`, branch `feat/OHCHCOVad`.
**Found by:** Go coverage of the `charges` port, measured with the port as `-coverpkg`
and the **conformance package** as the test target — the instrument the driver
validated on the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`) and the
loan corpus (`F-2026-09-11-loan-graded-coverage.md`), not the grep it replaced.

## 1. The missing control, added

The map said the `charges` committed-store test was **ABSENT**, so coverage measured
from conformance meant nothing: without a store-driven test in the package, no vector
can move the number and every port function reads `0.0%` no matter how many vectors
exist.

Added `nexus/internal/apps/charges/conformance/committed_store_test.go` (commit
`853c127f`), modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against
  the reference `charges-go`, exactly as the grading binary does
  (`conformance/vector.go` `LoadStore`, `conformance/admit.go` `Admit`,
  `conformance/grade.go` `Run`);
* it **calls no port function directly** — every statement it reaches is reached
  *through the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors, and asserts every loaded
  vector is admissible, `Run` is not fatal, `VectorsLoaded != 0`,
  `parity_fail + refused + inadmissible + errored == 0`, and
  `invariant_violations == 0`;
* it pins the money-rule observation guard over the capability dimension
  (`committedChargeMoneyCapabilities = {flat-fee, percent-fee}`): the test fails if
  the corpus loses every vector exercising an arithmetic, so a later deletion is a
  failing test rather than a silent return to `0.0%`.

The committed corpus passes the reference:

    go run ./internal/apps/charges/conformance/cmd/conformance -root ..
    → VERDICT: PASS (exit 0)
      vectors_loaded=12 parity_pass=12 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=35 money_cells=11 invariant_violations=0

## 2. Measurement

The prescribed command (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/charges \
        -coverprofile=/tmp/c.cov ./internal/apps/charges/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

| run | test target | statements | total | functions at 0.0% |
|---|---|---:|---:|---:|
| no control (control file temporarily absent) | whole conformance package | — | 56.9% | 36 |
| **prescribed** (control present) | whole conformance package | — | **57.5%** | **36** |
| **vector-only** (control alone, all probes filtered out) | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | — | **41.2%** | **51** |

Two readings are reported because the package contains *both* the store-driven control
and `conformance_test.go`, whose probes construct `NewGoEvaluator()` and grade
hand-built vectors **by calling the port directly** (`conformance_test.go:283,320,345,
375,443,500`). That probe coverage is exactly the manufactured kind the brief forbids.
The **vector-only** row is therefore the honest "what the graded corpus reaches"
number; the prescribed package-wide row is the command the brief specifies and is the
one to compare against future changes. Neither row contains a `0.0%` **money rule**, and
the same cap branches are `0` in both (section 5).

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds case, each candidate is
checked against one question only:

> **Does the function implement a money rule?** If not — a getter, `String()`, enum
> decoder, status predicate, validation-list lookup, or error constructor — it is out
> of scope for grading and stays at `0.0%` without being a gap.
>
> If it *does* implement a money rule: **does an observation behind it already exist in
> a committed capture?** If yes, name the file and the figures a vector would take (a
> grading run the driver can dispatch next). If no, say what a capture would need.

## 4. Triage of the `0.0%` candidates

**No `0.0%` function implements a money rule.** All 36 functions at `0.0%` in the
prescribed run fall into the excluded classes:

| class | functions (`file:line`) |
|---|---|
| enum `StoredValue` / `Code` / `String` decoders | `applesto.go:40,48`; `calculationtype.go:58,60`; `paymentmode.go:28,36`; `timetype.go:106,108` |
| applies-to predicates | `applesto.go:67,68,69`; `charge.go:63,64,65` |
| validity / allowed-list lookups | `applesto.go:75`; `calculationtype.go:100`; `charge.go:74`; `timetype.go:166` |
| calculation-type predicates | `calculationtype.go:80,83,106,113`; `charge.go:80,84` |
| charge flag getters | `charge.go:57,58,59` |
| time-type predicates / helper | `timetype.go:135,139,140,141,145`; `charge.go:89` |
| payment-mode predicate | `paymentmode.go:52` |
| error constructors | `charge.go:39,48` |

The full list with `file:line` is Appendix A. Fifteen further functions are `0.0%` in
the **vector-only** run only (`calculationtype.go:50,88,94`; `charge.go:68,70`;
`timetype.go:97,127,128,129,130,131,132,133,137,158`) — all of the same non-money
classes; they are reached in the package-wide run only by the directly-calling probes.
Appendix B records them.

## 5. The finding — a money rule the corpus never reaches: the cap clamp

### 5.1 `money.go:86` `MinimumAndMaximumCap` — **OBSERVED but UNGRADED → gradeable without a capture**

*Rule.* The percentage-fee clamp. `feeFor` computes
`PercentageOf(base, percentage)` and then passes it through
`charges.MinimumAndMaximumCap(p, c.MinCap, c.MaxCap)`
(`conformance/impl.go:237` flat-branch, `:268`, `:307`, `:346`). The capability
registry's own `percent-fee` definition names it: the fee is
"`PercentageOf(base, percentage)` rounded HALF_UP to the currency's minor units,
**then capped**" (`.softhouse/capabilities-charges.json`). Money rule, integer minor
units.

*Why it is `0.0%` where it matters.* The function is `60.0%`, but its two cap branches
are **reached by no vector**:

* `money.go:87.45,89.3` — the `minCap` raise — **0 hits**
* `money.go:90.45,92.3` — the `maxCap` lower — **0 hits**

The covered blocks are only the fall-through (`money.go:86.91,87.45`,
`money.go:90.2,90.45`, `money.go:93.2,93.21`). The same two blocks are still `0` in the
**package-wide** run: the direct probes never supply a cap either. All 12 committed
vectors carry `min_cap_minor`/`max_cap_minor` absent (verified: no vector request key
set contains either field).

*Observation.* **Exists, and is committed.** The T51 sessions captured the oracle's cap
arithmetic on the **same pinned commit and tenant** as the corpus
(`.softhouse/capture/charges/out/t51/preconditions-T51.txt`: tenant `gerege`, jar
`git.commit.id 426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`,
`rounding-mode 4 HALF_UP`, PostgreSQL only). The pair to grade is the
**`chargeCalculationType 2` (PERCENT_OF_AMOUNT)** case, which the oracle computes once
on the loan principal, so it maps one-to-one onto a single-base vector:

**maxCap**

| item | value |
|---|---|
| capture (raw) | `.softhouse/capture/charges/out/t51/T51-TR-10-c2-maxcap-raw.json` |
| capture sha256 | `e72d8f14bbf7ebaecc02d5cb95b90d1d401e5891d07bf1803c475ba1b8f958c7` |
| case id | `T51-TR-10-c2-maxcap` |
| request | `.softhouse/capture/charges/req/calc-T51-TR-10-c2-maxcap.json` |
| charge def | `.softhouse/capture/charges/out/t51/req-create-c2-maxcap.json` (calc type 2, `maxCap: 5000`) |
| observed | `totalFeeChargesCharged = 5000.00` (`feeChargesDue = 5000.00` on the disbursement row) |
| vector figures | `calculation_type 2`, `amount_minor "0"`, `percentage 1234500` (1.2345%), `base_amount_minor "120000000"`, `max_cap_minor "500000"`, `fee_minor "500000"` |
| check | `PercentageOf(120000000, 1234500) = 1481400` (14,814.00) → `min(1481400, 500000) = 500000` ✓ |

**minCap**

| item | value |
|---|---|
| capture (raw) | `.softhouse/capture/charges/out/t51/T51-TR-12-c2-mincap-raw.json` |
| capture sha256 | `6340a095d2dad70bb74b412fde18c77921170fff37ea984f5c90fad3e14ae86b` |
| case id | `T51-TR-12-c2-mincap` |
| request | `.softhouse/capture/charges/req/calc-T51-TR-12-c2-mincap.json` |
| charge def | `.softhouse/capture/charges/out/t51/req-create-c2-mincap.json` (calc type 2, `minCap: 8000`) |
| observed | `totalFeeChargesCharged = 8000.00` (`feeChargesDue = 8000.00` on the disbursement row) |
| vector figures | `calculation_type 2`, `amount_minor "0"`, `percentage 100000` (0.1%), `base_amount_minor "120000000"`, `min_cap_minor "800000"`, `fee_minor "800000"` |
| check | `PercentageOf(120000000, 100000) = 120000` (1,200.00) → `max(120000, 800000) = 800000` ✓ |

*Why the `chargeCalculationType 2` captures and not the `5` ones.* The same T51
analysis captured `chargeCalculationType 5` (PERCENT_OF_DISBURSEMENT_AMOUNT) cap cases
(`T51-TR-09-c5-maxcap`, `T51-TR-11-c5-mincap`: `totalFeeChargesCharged = 13641.50` /
`24000.00` on three tranches). Those are **sums of per-tranche clamps** and are *not*
representable on the slice's single-base `feeFor`, which evaluates one `base_amount`
(`conformance/impl.go:237`). The type-2 cap is the *whole-loan* clamp
(`min(14814,5000)=5000`, `max(1200,8000)=8000`, per
`.softhouse/capture/charges/out/t51/ANALYSE2.txt`), so it transcribes cleanly.

*Verdict.* **Implemented, observed, ungraded.** Two short vectors — a near-copy of
`FC-03-pctamount-disbursement` with `max_cap_minor`/`min_cap_minor` added and
`fee_minor` set to the capped value — would take `MinimumAndMaximumCap` to `100%` and
close the one arithmetic the capability registry promises but no vector grades. This
is a grading run the driver can dispatch next; **no new capture is needed.** It is not
a defect: the cap arithmetic is present and the corpus simply never exercised it.

## 6. Secondary observation — `chargeCalculationType 5` is a declared capability with no vector

`calculationtype.go:88` `IsPercentageOfDisbursementAmount` is `0.0%` in the vector-only
run, because **no committed vector uses calculation type 5**: all 12 use type `1`
(flat) or `2` (PERCENT_OF_AMOUNT). The map's `percent-fee` capability explicitly covers
"PERCENT_OF_AMOUNT / PERCENT_OF_DISBURSEMENT", so the dispatch predicate (and its
`feeFor` branch) is reached only by a directly-calling probe — manufactured coverage.
T51 has type-5 observations (`.softhouse/capture/charges/out/t51/
T51-TR-01-c5-tranche-P3-raw.json`, `T51-TR-04-c5-onetranche-P3-raw.json`) that could
grade the dispatch. This is **lower value than the cap finding**: type 5 shares the
`PercentageOf` arithmetic with type 2, so it grades a predicate, not a new money rule.
Recorded so the driver can decide.

## 7. Other rule code the corpus never reaches (not money rules)

* `charge.go:104.25-107.4`, `:108.49-110.4`, `:112.45-115.4` — the **savings-charge**
  arms of `Validate` (`charge.go:98`, 55.6% vector-only). Ungraded because every
  committed vector is `applies_to 1` (loan); savings charge validation belongs to the
  `savings` context's corpus, not this one.
* `charge.go:120.54-122.4` — the `Validate` construction rule that an
  **overdue-instalment** charge must be a penalty. No committed vector uses time type
  `9` (`IsOverdueInstallment`); the observation would be a refusal, which is a capture,
  not money. Candidate only.
* `money.go:59.18-61.3` — `PercentageOf`'s int64-overflow error path: unreachable for
  the magnitudes `Admit` accepts (non-negative minor-unit strings); not a branch any
  vector can take.
* `money.go:74.19-76.3` / `:77.2,77.32` — `roundHalfAwayFromZero`'s negative-quotient
  arm: unreachable because `Admit` rejects negative `amount_minor`/`base_amount_minor`,
  so no admissible vector reaches it.
* The interest-based calculation types (`calculationtype.go:80`
  `IsPercentageOfAmountAndInterest`, `:83` `IsPercentageOfInterest`) are **out of the
  graded domain by design** — the capability registry's note states the Go slice cannot
  compute them without the loan's interest, so `Admit` refuses a fee vector that
  requires them. Their `0.0%` is not a gap.

## 8. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `MinimumAndMaximumCap` min branch | `money.go:87.45-89.3` | **yes** | **yes** — `t51/T51-TR-12-c2-mincap-raw.json` | **grade now** |
| `MinimumAndMaximumCap` max branch | `money.go:90.45-92.3` | **yes** | **yes** — `t51/T51-TR-10-c2-maxcap-raw.json` | **grade now** |
| `IsPercentageOfDisbursementAmount` | `calculationtype.go:88` | no (predicate); same arithmetic as type 2 | yes (type-5 captures) | low value, later |
| savings arms of `Validate` | `charge.go:104.25-107.4`, `108.49-110.4`, `112.45-115.4` | no | out of context | not this corpus |
| overdue-must-be-penalty rule | `charge.go:120.54-122.4` | no | no (needs a refusal capture) | needs capture |
| `PercentageOf` overflow | `money.go:59.18-61.3` | branch unreachable | n/a | not a gap |
| negative half-round arm | `money.go:74.19-77.32` | branch unreachable (non-negative minor units) | n/a | not a gap |
| 36 non-money `0.0%` functions | Appendix A | no | n/a | out of scope |

**No candidate is asserted to be a defect.** The cap clamp is the one implemented,
observed, ungraded **money rule**; it is holds-shaped and dispatchable without a
capture.

## 9. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued.
* No vector and no drive was written. `.softhouse/vectors/charges/` is unchanged.
* No port code changed. `.softhouse/guards/` (12 pairs) and
  `.softhouse/conformance.sh` (census 17) are untouched.
* No gap was graded; section 5 names the vectors a later run may write, and section 6–7
  name what would need a capture first.

## 10. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded
  run completed and the bar is refused by that recorded decision`. Verdict PASS (46
  parity vectors, 7884 cells; 1 recorded divergence). No `HARD guard failed`.
* `kills.sh charges charges-wrong-rounding-half-even <worktree>` → **1** (as before).
* `redcount.sh <worktree> charges` → **9** (all 9 charges drives kill).
* `capcount.sh <worktree> charges charges-go` → **0** (the reference fails no vector).
* `charges-go` on the committed store:
  `vectors_loaded=12 parity_pass=12 parity_fail=0`.
* The new test passes on the current tree; its coverage is vector-driven (measured with
  the control file temporarily withdrawn: 41.2% vector-only, and every number above is
  unchanged by the probes' manufactured reach except as noted).

## Appendix A — all 36 functions at `0.0%` in the prescribed run

`file:line` are lines in each file.

- `applesto.go:40` `StoredValue`
- `applesto.go:48` `String`
- `applesto.go:67` `IsClientCharge`
- `applesto.go:68` `IsSharesCharge`
- `applesto.go:69` `IsWorkingCapitalLoanCharge`
- `applesto.go:75` `ValidAppliesToStoredValues`
- `calculationtype.go:58` `Code`
- `calculationtype.go:60` `String`
- `calculationtype.go:80` `IsPercentageOfAmountAndInterest`
- `calculationtype.go:83` `IsPercentageOfInterest`
- `calculationtype.go:100` `IsAllowedClientChargeCalculationType`
- `calculationtype.go:106` `IsPercentageBased`
- `calculationtype.go:113` `HasInterest`
- `charge.go:39` `Error`
- `charge.go:48` `Error`
- `charge.go:57` `IsActive`
- `charge.go:58` `IsPenalty`
- `charge.go:59` `IsDeleted`
- `charge.go:63` `IsClientCharge`
- `charge.go:64` `IsSharesCharge`
- `charge.go:65` `IsWorkingCapitalLoanCharge`
- `charge.go:74` `IsAllowedClientChargeCalculationType`
- `charge.go:80` `IsPercentageOfApprovedAmount`
- `charge.go:84` `IsPercentageOfDisbursementAmount`
- `charge.go:89` `IsOverdueInstallment`
- `paymentmode.go:28` `StoredValue`
- `paymentmode.go:36` `String`
- `paymentmode.go:52` `IsPaymentModeAccountTransfer`
- `timetype.go:106` `Code`
- `timetype.go:108` `String`
- `timetype.go:135` `IsSpecifiedDueDate`
- `timetype.go:139` `IsShareAccountActivation`
- `timetype.go:140` `IsSharesPurchase`
- `timetype.go:141` `IsSharesRedeem`
- `timetype.go:145` `IsDisbursementOrTrancheDisbursementCharge`
- `timetype.go:166` `ValidLoanStoredValues`

## Appendix B — the 15 functions `0.0%` in the vector-only run but not above

These are reached in the prescribed run **only** by `conformance_test.go`'s direct port
calls (manufactured coverage), not by any vector. All are non-money classes.

- `calculationtype.go:50` `StoredValue` (enum decoder)
- `calculationtype.go:88` `IsPercentageOfDisbursementAmount` (calculation-type predicate — see §6)
- `calculationtype.go:94` `IsAllowedSavingsChargeCalculationType` (allowed-list)
- `charge.go:68` `IsAllowedSavingsChargeTime` (allowed-list)
- `charge.go:70` `IsAllowedSavingsChargeCalculationType` (allowed-list)
- `timetype.go:97` `StoredValue` (enum decoder)
- `timetype.go:127` `IsSavingsActivation` (time predicate)
- `timetype.go:128` `IsSavingsClosure` (time predicate)
- `timetype.go:129` `IsWithdrawalFee` (time predicate)
- `timetype.go:130` `IsSavingsNoActivityFee` (time predicate)
- `timetype.go:131` `IsAnnualFee` (time predicate)
- `timetype.go:132` `IsMonthlyFee` (time predicate)
- `timetype.go:133` `IsWeeklyFee` (time predicate)
- `timetype.go:137` `IsOverdraftFee` (time predicate)
- `timetype.go:158` `IsAllowedSavingsChargeTime` (allowed-list)
