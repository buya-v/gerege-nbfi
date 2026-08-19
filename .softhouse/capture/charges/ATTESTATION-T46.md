# `charges` — attestation corrections (T46), under T42's eight-point rule

**Task:** T46, branch `softhouse/T46-capture-corrections`. **Corrects:** T44 findings **A-1**, **A-2**,
**A-3**, **A-4**, **A-5**, **A-6**, **A-7**, **A-8**, **T44-X1** against `.softhouse/capture/charges/`.

**Reference oracle (Fineract) reachability, this fire: REACHABLE**
[VERIFIED: `curl -sk https://localhost:8443/fineract-provider/actuator/health` →
`{"status":"UP","groups":["liveness","readiness"]}`; `fineract-fineract-1` (`fineract:latest`) up 16 h
healthy, `fineract-db-1` (`postgres:18.3`) up 38 h healthy — run by this task].
Pinned checkout `/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status
--porcelain` empty [VERIFIED: asserted by `bin/run-preconditions.sh` on every capture below].

> **RAW OBSERVED FORM ONLY. NOTHING PROMOTED, NOTHING CONTRACT-SHAPED.** Gate **G-1** is open and DEC-1
> is unratified. Everything here is a raw HTTP response body, an exact-text sidecar derived from one, or
> provenance about how it was obtained.

**Additive only.** No charge definition was created, modified or deleted — T40's `m_charge` ids **1–12**
are used exactly as they stand. Nothing was restarted, re-tenanted, dropped or written to schema. The
only endpoint touched is `POST /loans?command=calculateLoanSchedule`, which persists nothing.
**The tenant was left exactly as found** [VERIFIED by this task, read-only SQL after every capture:
`psql -d fineract_gerege -tAc "select (select count(*) from m_charge), (select count(*) from m_loan),
(select count(*) from m_product_loan)"` → **`12|0|16`**]. PostgreSQL 18.3 is the only engine reached.

---

## 1. A-1 — the Path B wiring citation, which was entirely absent

T42's rule 4 requires that a Path B set **say and cite** why its ambient `MoneyHelper` reading is the
threaded object. T44 found **zero** grep hits for that citation anywhere in `capture/charges/` or its
handoff. Here it is, re-opened in the pinned checkout by this task rather than copied:

| site | line | what it does |
|---|---|---|
| `fineract-provider/.../loanschedule/service/LoanScheduleAssembler.java` | **:753** | `final MathContext mc = MoneyHelper.getMathContext();` |
| same | **:765** | `LoanScheduleModel loanScheduleModel = loanScheduleGenerator.generate(mc, loanApplicationTerms, loanCharges, detailDTO);` |
| same | **:777** | `final MathContext mc = MoneyHelper.getMathContext();` |
| same | **:797** | `final MathContext mc = MoneyHelper.getMathContext();` |
| `fineract-provider/.../loanaccount/service/LoanScheduleGeneratorServiceImpl.java` | **:44** | `final MathContext mc = MoneyHelper.getMathContext();` |

[VERIFIED: all five lines opened by this task in `/Users/buv/fineract` at the pinned commit.]

**Consequence, stated precisely.** On **Path B the ambient context IS the threaded object** — the REST
entry point reads `MoneyHelper.getMathContext()` and hands that very reference to `generate(mc, …)`. So
T40's ambient reading is admissible evidence about the arithmetic *here*, which is exactly the opposite
of the Path A situation (T42 E1: on Path A the ambient context is provably never read for a 2-dp
currency). T40's conclusion was right; only the justification was missing. It is no longer missing.

**And T46 found a second, sharper reason the ambient reading is load-bearing on this path** — see §4.

## 2. A-8 — one ambient witness, counted twice

T40's attestation lists the `c_configuration` row and the oracle's `MoneyHelper` initialisation log line
as two assertions. **They are one witness.** [VERIFIED: `fineract-core/.../MoneyHelper.java:59-64` —
`initializeTenantRoundingMode` computes `roundingMode`, writes `roundingModeCache.put(...)` and emits
the log line *from the same local*; `:74-82` `getRoundingMode()` reads that cache back; `:91-94`
`getMathContext()` is `mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION,
getRoundingMode()))`.] A configuration row proves what was *configured*, not what arithmetic is in force.

**Rule 6 is nonetheless satisfied for this set, and now doubly so.** T36's half-cent canary
(`20925.05`; `HALF_EVEN` would give `20925.04`) is behavioural evidence about the *tenant* arithmetic —
and T46 has now added **two half-cent ties inside the charge arithmetic itself** (§4), which is the
narrower thing T40 declared impossible.

## 3. A-3 — CLOSED. The **request** supplies the money; `m_charge.amount` is ignored

T40 set the per-request `amount` **equal** to the definition's `m_charge.amount` on all 21 captures, so
no capture could distinguish "the definition governs" from "the request governs". A Go port that read
the definition passed all 21 and was wrong.

Seven new captures make the two disagree. Full working: `out/t46/DEFVSREQ.txt`; requests
`req/calc-T46-CH-0*.json`; responses `out/t46/T46-CH-0*-raw.json`.

| capture | charge id (time, calc) | definition | request | if DEFINITION governs | if REQUEST governs | **OBSERVED** |
|---|---|---|---|---|---|---|
| `T46-CH-01` | 4 (8, 4) pct of interest | `3.750000` | `1.25` | `810.00` | `270.00` | **`270.00`** |
| `T46-CH-02` | 1 (1, 1) flat, disbursement | `15000.000000` | `7777.77` | `15000.00` | `7777.77` | **`7777.77`** |
| `T46-CH-03` | 4 (8, 4) pct of interest | `3.750000` | `0.021875` | `810.00` | `4.725` | **`4.73`** |
| `T46-CH-04` | 4 (8, 4) pct of interest | `3.750000` | `0.009375` | `810.00` | `2.025` | **`2.03`** |
| `T46-CH-05` | 5 (8, 3) pct of amount+interest | `1.234500` | `2.5` | `1383.65685765` | `2802.05925` | **`2802.06`** |
| `T46-CH-06` | 3 (1, 2) pct of amount, disbursement | `1.234500` | `0.5` | `14814.00` | `6000.000` | **`6000.000`** |
| `T46-CH-07` | 8 (8, 1) flat PENALTY per instalment | `1200.000000` | `333.33` | `1200.00` | `333.33` | **`333.33`** |

**Seven for seven: the request governs.** Across **four** `charge_calculation_enum` values (1 flat,
2 percent-of-amount, 3 percent-of-amount-plus-interest, 4 percent-of-interest), **two**
`charge_time_enum` values (1 disbursement, 8 instalment) and **both** fee and penalty.

*Mechanism, re-derived:* `ProgressiveLoanScheduleGenerator.java:445-446` and `:464-465` compute
`amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc)` — `getPercentage()` is
the `LoanCharge`'s own field, populated from the request, not from `m_charge`
[VERIFIED: lines opened by this task]. Flat charges take `loanCharge.amount()` /
`loanCharge.amountOrPercentage()` at `:412` and `:449`, same story.

**Corroboration.** T44's own audit probes AP-5 and AP-6 reached the same conclusion from different
values on a different task with no shared harness. Two independent looks agreeing is the strongest
signal this pipeline produces (`patterns.md`).

**Required consequence for admissibility, now discharged:** *the vector's fixture is the **request
bytes**, not the `m_charge` row.* `out/attested/attestation.json`'s `charges_as_persisted` block remains
load-bearing provenance for `charge_time_enum`, `charge_calculation_enum` and `is_penalty` — and is
load-bearing for **no money value in the set**.

**Still `TO_BE_CAPTURED`:** whether `m_charge.amount` governs when the request **omits** `amount`
entirely. Every capture in the corpus supplies it, so that branch is ungraded. `[UNVERIFIED]`

## 4. A-5 — CLOSED, and T40 §11's arithmetic proof is REFUTED

T40 §11 wrote: *"a tie needs `216 × p` to end in `…5` at the third decimal, and `216p` is even for every
terminating decimal `p`."* That is false — `p` is a decimal, not an integer, so `216p` need not be an
integer at all.

| capture | request percentage | exact product on period-1 interest `21600.00` | `HALF_UP` | `HALF_EVEN` | **OBSERVED** |
|---|---|---|---|---|---|
| `T46-CH-03` | `0.021875` | **`4.725`** exactly | `4.73` | `4.72` | **`4.73`** |
| `T46-CH-04` | `0.009375` | **`2.025`** exactly | `2.03` | `2.02` | **`2.03`** |

**Two exact half-cent ties, both resolved `HALF_UP`.** This is the in-charge-arithmetic rounding-mode
canary T40 declared impossible, and it is now an observation.

### The rounding locus, re-derived

T44 asked for it. It is **not** where a reader would guess.

1. `ProgressiveLoanScheduleGenerator.calculateInstallmentCharge` **:445-446** computes
   `amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc)` under the
   **THREADED** `mc`. At precision 19 that is exact for these inputs — `4.725000…`, no rounding.
2. The result is wrapped by **`Money.of(cumulative.getCurrency(), …)`** — the **two-argument** overload.
   `Money.getCurrency()` returns a `MonetaryCurrency` [`Money.java:55-57`], so this resolves to
   `Money.of(MonetaryCurrency, BigDecimal)` at **`Money.java:114-116`**, which supplies
   **`MoneyHelper.getMathContext()`** — the **AMBIENT** context.
3. The scale-2 rounding happens in `Money`'s private constructor, **`Money.java:52`**:
   `this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());`

[VERIFIED: every line opened by this task at the pinned commit.]

**So the rounding mode that decides a charge half-cent is the AMBIENT tenant rounding mode, not the
threaded one.** On Path B they coincide (§1), which is why the observation is `HALF_UP` either way — but
a Go port that threads one context and forgets the ambient fallback will get charge ties wrong while
getting interest right. This is `patterns.md`'s "hidden second rounding context" landing on charges.

**`TO_BE_CAPTURED`:** a shape that *separates* the ambient from the threaded rounding mode inside charge
arithmetic. It needs the two to differ, which on Path B means changing the tenant mode — a write to the
shared server this task is not permitted to make. `[UNVERIFIED as separated]`

## 5. A-4 — C5 is relabelled; it is a probe, never a conformance assertion

DEC-1 revision 8's ratified decision **C-1** obliges that *no adapter, harness or conformance check may
assert `totalRepaymentExpected` equals the sum of the rows*. Shipped as an invariant, C5 would make a
**correct** Go port fail 15 of 21.

`bin/t46-invariants.py` therefore splits the suite:

- **INVARIANTS** — `C1 C2 C3 C4 C6 C7 C8 C9 C10`. Only these set the exit code. **0 failures over 28
  captures** (T40's 21 plus T46's 7) [`out/t46/INVARIANTS-P5.md`].
- **PROBE P5** (was C5) — the **signed delta** `totalRepaymentExpected − Σ totalDueForPeriod`, in
  integer minor units, reported and never asserted. **20 of 28 captures show a non-zero delta**, from
  `−1,361` to `−5,190,000` minor units.

The suite is proved **failable**: `--negative` perturbs one leaf in memory and it exits 1 naming three
broken invariants [`out/t46/INVARIANTS-P5-negative.md`].

Worth stating because it is a new observation rather than an assumption: **C8 and C9 pass on all seven
T46 captures**, so charges still do not move principal, the outstanding balance or the EMI even when the
request amount disagrees with the definition and even at a tie — the seven new shapes are cell-for-cell
identical to the zero-charge control on `principalDue`, `principalOriginalDue`, `interestDue`,
`principalLoanBalanceOutstanding` and `totalInstallmentAmountForPeriod`.

T40's own `bin/invariants.py` is left as it stands — it is T40's committed evidence, it reproduces its
committed `out/INVARIANTS.md` byte-for-byte after the A-7 path fix [VERIFIED: `diff` silent, this task],
and its C5 failures are the observation that produced D-1. **What must not happen is C5 travelling
forward as a conformance check.** `bin/t46-invariants.py` is the suite that does.

## 6. A-2 — D-1's source citation was pointing at the site of AGREEMENT

T40's handoff cites `AbstractCumulativeLoanScheduleGenerator.java:504` as proof that the two generators
disagree. `:504` is inside `updatePeriodsWithCharges` — the **separated** path, which the progressive
generator has too (`ProgressiveLoanScheduleGenerator.java:486`). The correct citation is:

- cumulative **main loop**: `AbstractCumulativeLoanScheduleGenerator.java:392`
  `scheduleParams.addTotalRepaymentExpected(totalInstallmentDue)`, where `:352` sets
  `totalInstallmentDue = currentPeriodParams.fetchTotalAmountForPeriod()` and
  `ScheduleCurrentPeriodParams.java:144-145` defines that as
  `principalForThisPeriod.plus(interestForThisPeriod).plus(feeChargesForInstallment).plus(penaltyChargesForInstallment)`;
- progressive **main loop**: adds only `principalDue.plus(interestDue, mc)`.

**The conclusion is unchanged and true; only the pointer moves.** [VERIFIED by T44 on the pinned source
and re-checked by T44's parent auditor; **not independently re-opened by T46** — `[UNVERIFIED by this
task]`.]

## 7. A-6 — response scale is caller-controlled, and worse than recorded

T44 observed `0`, `15000`, `14814.000000` on the disbursement row. T46 adds a case that shows the scale
is not merely "the underlying `BigDecimal`'s" but **a function of the request literal**:

| capture | request `amount` | disbursement-row `feeChargesDue` on the wire |
|---|---|---|
| `T46-CH-02` | `7777.77` | `7777.77` (scale 2) |
| `T46-CH-06` | `0.5` | **`6000.000`** (scale 3) |
| `FC-03` (T40) | `1.2345` | `14814.000000` (scale 6) |

`0.5 % of 1200000.00` = `6000.000` — scale 3, because `1200000.00` (scale 2) × `0.5` (scale 1) = scale
3, and **nothing on the disbursement path wraps it in `Money`**, so the currency's 2 decimal places are
never applied [VERIFIED: raw bytes in `out/t46/T46-CH-06-defvsreq-pctamount-disb-raw.json`; the
instalment path *is* wrapped, §4 step 2, which is why `T46-CH-03` comes back at scale 2].

**Consequence for the port and for any conformance comparison: the disbursement-row charge is NOT at
currency scale, and comparing it as a number rather than as text will silently pass a port that emits
`6000.00`.** Response scale remains **ungraded** by any check in this corpus.

## 8. A-7 — the run recipe is runnable again

11 `bin/` files hard-coded T40's ephemeral worktree path. `bin/t46-fix-paths.py` rewrites the root to a
self-locating one (`${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}`; the Python tools use
`pathlib.Path(__file__).resolve().parents[4]`).

**Proved to change nothing:** the whole corpus was re-issued through the fixed scripts against the live
oracle and **21 of 21 responses came back BYTE-IDENTICAL** to T40's committed `out/fc/`
[`out/t46-reissue/IDENTITY.txt`, `bin/t46-reissue-identity.sh`]. That is also a **third** independent
issue of the corpus, on a different day by a different task, so it is determinism evidence in its own
right. `bin/invariants.py` likewise still reproduces `out/INVARIANTS.md` byte-for-byte.

## 9. T44-X1 — exact-text serialisation for Path B

**Decision, and what it does to already-committed records:**

1. **Raw response bytes stay canonical and are NOT rewritten.** They are what the oracle said; a JSON
   number literal on the wire is already exact text. The hazard is in the consumer.
2. Every Path B capture gains an **exact-text sidecar** `<name>-exact.json`, in which every JSON number
   is re-emitted as a JSON **string** carrying the wire literal byte for byte. **57 sidecars written**
   [`out/t46/EXACT-TEXT.md`, `bin/t46-exacttext.py`].
3. **No float is constructed producing them.** Python's decoder hands the *raw matched literal* to
   `parse_float` / `parse_int`, so `json.loads(text, parse_float=str, parse_int=str)` yields the original
   characters and never touches a binary double.
4. **Identity is proved, not asserted:** every sidecar is re-read and required to agree with its raw
   capture leaf-for-leaf as text, and to contain **zero** bare JSON numbers. All 57 pass; the check is
   failable (`--negative`, exit 1).
5. Measured independently by this task: **17,693 bare JSON number occurrences across 552 distinct
   literals** in the Path B captures (T44 measured 9,122 / 245 over the `fc` subset alone; T46's count
   spans `fc`, `control`, `attested` and `t46`). **65** distinct literals would have their **text**
   changed by a float round-trip. Path A control: **0** bare decimal numbers in any of the five Path A
   payloads.

**Admissibility rule that must travel with any promoted Path B vector:** *compared as exact decimal
text, never through a JSON number.* In Go that means never `encoding/json` into `interface{}` (which
yields `float64`); use `json.Number` or read the sidecar's strings.

---

## 10. What this set still cannot distinguish

Unchanged from T44 except where marked:

1. **One loan shape underneath all 28** — principal `1200000`, 21.6 %, 12 monthly periods,
   `01 January 2026`. Term, rate, frequency and anchoring are ungraded here.
2. **`m_charge.amount` when the request omits `amount`** — **new**, and the one thing §3 does not settle.
3. **Ambient vs threaded rounding mode inside charge arithmetic** — **new** (§4); needs the two to
   differ, which needs a tenant write.
4. **Response scale** (§7) — ungraded by every check in the set.
5. `chargeTimeType = OVERDUE_INSTALLMENT` (the operationally important penalty), tranche /
   multi-disbursement charges, `minCap` / `maxCap`, `taxGroupId`, `glAccountId`,
   `chargePaymentMode = ACCOUNT_TRANSFER`, `feeFrequency` / `feeInterval`.
6. The **cumulative** generator, `Asia/Hovd`, and anything requiring a persisted loan.
7. **`installmentAmountInMultiplesOf` is honoured or lost BY CALLER** — the REST
   `calculateLoanSchedule` path via `LoanScheduleAssembler` honours it [VERIFIED by this task:
   `out/control/B-02-multiplesof100-raw.json` period 1 `totalInstallmentAmountForPeriod` is
   **`112100.00`**, against `112082.37` in the `B-01` baseline];
   `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement`
   builds a `LoanRepaymentScheduleModelData` and calls `generate(mc, modelData)`, and
   `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` **never sets the
   field** [VERIFIED: `LoanApplicationTerms.java:579-606` opened by this task — the builder chain
   contains **zero** occurrences of `MultiplesOf`]. So DEC-1 must not state the field's
   behaviour unconditionally. (T44 finding **M-4**.)
8. **`FC-17` and `FC-20` are NEGATIVE vectors only** — both byte-identical to the zero-charge control,
   so an adapter that ignored the `charges` array entirely passes both.

---

## 11. Unverified

- **A-2's replacement citation** is T44's and T44's parent auditor's; **T46 did not re-open
  `AbstractCumulativeLoanScheduleGenerator.java:392` or `ScheduleCurrentPeriodParams.java:144-145`.**
  `[VERIFIED on T44's evidence; UNVERIFIED by this task]`
- **That "the request governs" holds for charge types not tried.** Observed on `charge_calculation_enum`
  1, 2, 3, 4 and `charge_time_enum` 1, 8. Enum values 5 (percent of disbursement amount) and 9 (overdue
  instalment), and `charge_time_enum` 2 (specified due date), were **not** re-tested with a disagreeing
  amount. `[VERIFIED on the seven captures; UNVERIFIED as a general rule]`
- **That the rounding locus in §4 is the ONLY one on the charge path.** It is the one the two observed
  ties went through. Caps, taxes and the separated path may add others. `[UNVERIFIED]`
- **That `HALF_UP` at a charge tie is the tenant mode rather than a coincidence.** The tenant mode was
  not moved (this task may not write the shared server), so the tie observations are consistent with
  `HALF_UP` and inconsistent with `HALF_EVEN`, but they do not *isolate* the mechanism.
  `[VERIFIED as an observation; UNVERIFIED as a controlled experiment]`
- **That 552 distinct literals is the complete set.** It is the set present in the committed Path B
  captures at their current magnitudes and scales. It says nothing about a larger payload, and "0 of
  them change value today" must never be read as "floats are safe here".
- **Note for the reviewer, so it is not mistaken for a violation:** the strings `ojdbc`, `oracle.jdbc`,
  `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver` appear in this set only inside `grep` patterns that
  assert those engines are **ABSENT**, and every such assertion observed **0** hits. The word "oracle"
  throughout means the **Fineract reference implementation**, never Oracle Database. The only database
  engine touched is **PostgreSQL 18.3**.
