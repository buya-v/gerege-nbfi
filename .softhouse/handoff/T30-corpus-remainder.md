# T30 — oracle-free corpus remainder — handoff

**Task:** T30, branch `softhouse/T30-corpus-remainder-oracle-free`, worktree `/home/user/wt-T30`.
**Input of record:** `.softhouse/reviews/T27-corpus-corrections-review.md` (authoritative), plus
`.softhouse/reviews/T22-pathb-capture-audit.md` and `T21-capture-pass3-audit.md`.
**Fire context:** cloud sandbox, **no live reference oracle (Fineract) reachable** — no Docker, no PostgreSQL
on `:5432`.

> **NO ORACLE OBSERVATION WAS MADE, AND NO ORACLE VALUE WAS SYNTHESIZED, INVENTED OR EXTRAPOLATED.**
> Everything below is either (a) read from an artifact already committed on `main`, (b) re-derived from the
> pinned Fineract **source** at `/home/user/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
> (verified `git log -1`, tree clean), or (c) produced by my own script operating on committed artifacts.
>
> **NOTHING WAS PROMOTED** to the parity vector store. T27's verdict stands unchanged: nothing is promotable
> today. This task corrected the *record*.

---

## Headline: the B-03 / B-04 consistency verdict — **CONSISTENT**

T22 P1-14's first clause — the item T27 called "the largest remaining hole in the Path B evidence" — is
**closed**. `B-03` and `B-04` are now rebuilt **from the pinned source** through the DAILY / `ACTUAL`-`ACTUAL`
arm, including the cross-year partial-period branch (`ProgressiveEMICalculator.java:1372-1374`, `:1393-1398`,
`calculatePeriodFractions` `:1550-1568`) that T22's model did not cover.

| capture | `MathContext` | verdict |
|---|---|---|
| `B-03` `FULL_LEAP_YEAR` | `(19, HALF_EVEN)` — the mode these captures actually ran at | **RE-DERIVED DIGIT-FOR-DIGIT** (12/12 periods + both totals) |
| `B-03` `FULL_LEAP_YEAR` | `(19, HALF_UP)` — ratified production mode | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `B-04` `FEB_29_PERIOD_ONLY` | `(19, HALF_EVEN)` | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `B-04` `FEB_29_PERIOD_ONLY` | `(19, HALF_UP)` | **RE-DERIVED DIGIT-FOR-DIGIT** |

**The committed `B-03`/`B-04` observations ARE consistent with the from-source re-derivation. There is no
adverse finding to report on those numbers.** Script, citations and full transcript:
`.softhouse/reviews/t30-probe/` (`README.md`, `t30_rederive_b03_b04.py`, `t30-rederive-output.txt`).
The script carries a "NOT RUN AGAINST A LIVE ORACLE" banner and is read-only w.r.t. `.softhouse/capture/`.

Two normative facts it establishes that were **not in the record before** (both DEC-1-relevant, see §5):

1. **`FEB_29_PERIOD_ONLY` does two things, not one.** Besides capping days-in-year at 365 for a period that
   contains no 29 February, it **suppresses the cross-year partial-period calculation** for that period —
   `partialPeriodCalculationNeeded = ACTUAL && yearsDiff > 0 && (strategy != FEB_29_PERIOD_ONLY ||
   periodContainsFeb29)`. In this corpus that is exactly period 12 (2024-12-01 → 2025-01-01):
   `B-03` takes the partial arm, `B-04` does not. A port implementing only the day-count cap returns `B-03`'s
   period-12 numbers for `B-04` and fails.
2. **The partial arm is a sum of per-year day fractions**, `Σ days(segment) / Year.length(year)` split at
   31 December — for `B-03` period 12, `30/366 + 1/365` → rate factor `0.0182966988…` where the non-partial
   arm gives `31/366 → 0.0182950819…`. Its `interestFractionPerPeriod` multiply is **exact**, deliberately
   without the `MathContext` (`rateFactorByRepaymentPartialPeriod` `:1965-1978`), unlike its neighbours.

By-product: identical output at HALF_UP and HALF_EVEN is a **from-source** demonstration that these two
captures are mode-insensitive, which now corroborates T22's fresh-tenant re-observation instead of the record
resting on that re-observation alone. It does **not** make them parity vectors — T22 P0-3/P0-4/P0-6 still
block promotion.

---

## 1. The silently dropped item — T22 P1-12 — **DONE**

Re-derived from the pinned source myself before writing it: `calculateLastUnpaidRepaymentPeriodEMI`
accumulates `Σ dueInterest` (`:1190-1191`), `Σ EMI` (`:1192-1194`), `totalDisbursed` (`:1195-1197`),
`totalCapitalizedIncome` (`:1198-1200`); forms `diff` at **`:1202-1203`**; applies it at **`:1205`** via
`repaymentPeriod.getEmi().add(diff, mc)`. Signed, under the tenant `MathContext`.

- **`PATHB-REPORT.md:68-70`** — before: the rule appeared **only** as a worked example ("period 12 is
  principal `109,888.23` + interest `1,977.99` = `111,866.22`").
- **`PATHB-REPORT.md:79-102`** (after) — a **NORMATIVE RULE** block stating
  `lastUnpaidPeriod.emi ← lastUnpaidPeriod.emi + (totalDisbursed + totalCapitalizedIncome +
  totalCreditedPrincipal + Σ dueInterest − Σ EMI)`, with the three things the "whatever is left" reading
  loses: the delta is **signed** (`+` on `B-01`, `−` on `B-02`, `+0.05` on `B-03`, `−0.05` on `B-04` — the
  last two newly witnessed by my re-derivation); it lands on the last **unpaid** period (`:1176-1181`); and it
  adjusts the **EMI**, after which the interest/principal split is re-taken by the ordinary rules.

**Not applied to DEC-1 — T28 owns `docs/adr/DEC-1-schedule-generator-adapter.md` and
`nexus/internal/apps/loanschedule/contract/contract.go`, and neither file was touched by this task.** The
DEC-1-destined wording is in §5 below.

## 2. T22 P0-5 — mis-parked, needed no oracle — **DONE**

- **`REPRODUCE.md:76`** — before: `-o out/B-$n-*-raw.json` inside a `for n in 01 02 03 04` loop. A shell glob
  in an output path cannot expand against a file that does not exist yet, so `curl` creates files named
  literally `B-01-*-raw.json`. **The committed recipe could not reproduce the committed corpus.**
- **`REPRODUCE.md:71-110`** (after) — a CORRECTED banner explaining the defect, then a loop that names every
  output file explicitly, captures **`-w '%{http_code}'`**, prints the status per capture and **exits 1 on any
  status other than 200** with "the file in out/ is an ERROR BODY, not a capture. Do not commit it, and do not
  treat it as an observation." Also emits `sha256sum out/B-0*-raw.json` with the four committed digests
  inline, so a re-run is checked for byte identity rather than eyeballed. Parameter expansion dry-run
  verified under `sh`.
- Left explicitly open **in the file itself** (`REPRODUCE.md:105-110`): T22 P0-4's fail-the-run preconditions
  (`rounding-mode` = 4, tenant timezone, empty `schema_connection_parameters`) — written against a running
  server, parked with the P0-6 re-point.

## 3. The other mis-parked items — **DONE**

- **T22 P1-8, second clause** — `PATHB-REPORT.md:177-192`. The `SAME_AS_REPAYMENT_PERIOD` short-circuit is a
  theorem about the code (`:1377-1383`, `:1510-1516`, days-in-year hard-set to `12` before the strategy is
  used), the `ACTUAL` half of the precondition is enforced at product creation (`LoanProduct.java:462-472`),
  and the probe citations T27 settled by SHA-256 are folded in as a table rather than redone:
  `p05 ≡ p06` (`ff92fc5dfb8e…`) and `p07 ≡ B-03` (`892dd6f5…`). **I re-ran the hashes myself to confirm
  before recording them.**
- **T22 P1-9** — `PATHB-REPORT.md:194-203`. Day-count is **live under DAILY** (`p07 ≠ p08`,
  `892dd6f5…` vs `ff92fc5d…`) and **inert under SARP** (`p09 ≡ B-01`, `713a3560…`). T27's settled result
  folded in, hashes re-confirmed here.
- **T22 P1-11, first clause** — `PATHB-REPORT.md:293-306`. The EMI re-adjust loop
  (`ProgressiveEMICalculator.java:1258-1308`, ≤ 3 iterations) recorded as **unpinned contract behaviour**:
  it adopts a re-rounded EMI only if the last-vs-penultimate gap shrinks (`:1289-1291`) and can absorb a
  `multiplesOf` rounding difference entirely (T22's negative probe `out-modeprobe/`). Its entry condition
  `|emiDifference| × 100 > originalEmi.copy(floor(n/2))` is recorded with the trap spelled out:
  **`Money.copy(double)` REPLACES the amount** (`Money.java:219-221` → `:215-217`), so the RHS is `Money(6)`,
  **not** `EMI × 6` — the misreading that got three T21 probe scripts retracted. On all four Path B captures
  the residual is `±0.05`, so `5 > 6` is false and the loop does not fire (which is why the from-source
  re-derivations reproduce them without modelling it). *The capture that would pin the loop stays PARKED —
  it needs the oracle.*
- **T22 P1-14, first clause** — `PATHB-REPORT.md:205-235` plus `.softhouse/reviews/t30-probe/`. See the
  headline above.
- **T22 P1-10 (bonus, oracle-free, previously deferred)** — `PATHB-REPORT.md:135-146`. The report cited only
  the Path A *defect*; it now carries the server-path citations, **all in the PROGRESSIVE generator**
  (`ProgressiveLoanScheduleGenerator.java:108-110` and `:81-82` — both verified in the pinned checkout —
  `ProgressiveEMICalculator.java:1761-1776`, `:1330-1353`, `:1160-1219`, `:1258-1308`, `Money.java:159-171`,
  `DaysInYearType.java:81-86`). T19 item 5 exists because this omission produced cumulative-generator
  citations last time.

## 4. Self-contradictions — **DONE** (twins verified byte-identical)

| file:line | before | after |
|---|---|---|
| `PASS3-REPORT.md:5` (+ twin) | "RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**" | "RAW OBSERVED, **INDEPENDENTLY AUDITED by T21 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**"; names the three open P0s (T21 §10 P0-2/3/4), notes T27's re-check, keeps "no vector promoted, no gate answered" |
| `PASS3-REPORT.md:114` → now `:122-128` (+ twin) | "pass 3 has not been independently audited" | "Pass 3 **has** since been independently audited — T21 … and T27 re-checked that audit's corrections — but three P0 admissibility items are still open … Until they close, the eleven `(19, HALF_UP)` records are **audited observations, not admissible parity vectors**" |
| `PATHB-REPORT.md:5` | "RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**" | "**INDEPENDENTLY AUDITED by T22 … ACCEPTED WITH REQUIRED CHANGES**"; three P0s open (P0-3/4/6), **P0-5 closed by T30** |
| `PATHB-REPORT.md:128-130` → now `:253-261` | "**Not audited.** … Treat every number here as observed-but-unaudited." | "**Audited — ACCEPTED WITH REQUIRED CHANGES, and still not promotable.**" — states what the audit found, that **no number was voided**, and that what is missing is *admissibility*, not correctness |
| `PATHB-REPORT.md:150-151` → now `:281-292` | "**Property invariants were not mechanically re-checked** … That is audit work." — **factually FALSE** | Retracted in place and replaced: T22's `t22_invariants.py` ran **ten** invariants (I1–I6, S1–S4) on all four captures and six probes, **all PASS**; T27 then proved them *failable* by one-minor-unit mutation. The old sentence is quoted and marked false so the retraction is auditable. |
| `reference-oracle.md:202` | Path B "**not audited**" | "**INDEPENDENTLY AUDITED by T22 … ACCEPTED WITH REQUIRED CHANGES**", re-checked by T27, `B-03`/`B-04` re-derived by T30; three P0s open; "audited observations, **nothing promoted**" |

`diff .softhouse/capture/PASS3-REPORT.md .softhouse/capture/PASS3-REPORT-shared.md` → **exit 0** (re-asserted
after every edit; the twin is written by `cp`, so byte identity is structural, not hoped for).

### One more instance of the same defect, found by me and fixed — `PASS2-REPORT.md`

Not on T27's list, and not in my brief. `PASS2-REPORT.md:5` said "RAW OBSERVED, **NOT YET INDEPENDENTLY
AUDITED** — pending task T19" and `:147` said "(T19 audit pending)" — in a document that **already carries a
"CORRECTIONS — imposed by the T19 independent audit" section at `:168`**. Exactly the RC-1 shape. I checked
first that T19's corrections really are applied there (they are, all six, at `:168-208`) before touching the
status line; had they not been, I would have left it and reported instead.

- `PASS2-REPORT.md:5` → "**INDEPENDENTLY AUDITED by T19 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**",
  pointing at the CORRECTIONS section, and restating the harder constraint that survives the audit entirely:
  all 13 captures ran at `(12, HALF_UP)`, so **by CLAUDE.md they are discrimination probes and can never be
  parity vectors**. The edit is marked as made by T30.
- `PASS2-REPORT.md:153-155` → "(the T19 audit has since landed — ACCEPTED WITH REQUIRED CHANGES, see
  CORRECTIONS below — and pass 2's precision-12 captures are probes, never parity vectors)".

## 5. Honesty defects — **DONE**

- **`PASS3-REPORT.md:68` → now `:73-76`** (+ twin). Before: "…identical at 43,811 and 131,432, but **diverge
  at 131,433**." After: the same, plus T21 §6.2's restored annotation — "**per-period; the two total-interest
  figures are equal at `2696.43`**", with the mechanism named: the transcript's `IDENTICAL`/`DIFFERENT`
  verdict is a **full-schedule** string comparison (`T21v2Probe2.java:63-66`), not a totals comparison. The
  surrounding sentences quote total interest, so without this a reader is actively misled.
- **`PATHB-REPORT.md:78-79` → now `:116-130`** — the round-down banner. Before, one sentence ran the two
  provenances together and ended "Committed observation: `…/rounddown-gerege-raw.json`", presenting the
  model-derived `111,148.35` as though the capture carried it. After, a four-row table splits them
  explicitly: `111,100.00` = **OBSERVED** (committed capture); `111,148.35` = **DERIVED, NOT OBSERVED**
  (re-derived by T22's model and independently by T27 after calibrating on the committed `B-01` EMI) — with
  the reason it can never be observed stated plainly: **the oracle never emits the unrounded EMI**. The
  round-up/round-nearest lines are labelled "arithmetic on the derived value". The banner also now records
  that the `(19, HALF_UP)` attribution for that probe rests on the filename and prose, not on an attestation
  — that is T22 P0-3 — while noting the conclusion is mode-robust either way.

---

## The exact `tasks.json` wording the orchestrator must apply

**I did not edit `.softhouse/tasks.json` — the orchestrator owns it.** Three stale claims live in the **`T8`**
task's `note` (the long `||`-separated string; T27 cited it as `tasks.json:188`). Apply these three verbatim
substring replacements; nothing else in the note or file needs to change.

**1.** replace
`Pass 3 is NOT yet audited (T21).`
with
`Pass 3 is INDEPENDENTLY AUDITED - T21 (2026-08-18), verdict ACCEPTED WITH REQUIRED CHANGES; the audit's oracle-independent corrections are applied (T25, completed by T30) and the audit itself was re-checked by T27. THREE P0 admissibility items remain open (T21 P0-2 attestation block, P0-3 the missing periodFromDate/feeAmount/penaltyAmount columns, P0-4 the executable run recipe), each needing a live oracle, so the eleven (19, HALF_UP) records are audited observations, NOT admissible parity vectors.`

**2.** replace
`NOT audited - T22 raised.`
with
`INDEPENDENTLY AUDITED - T22 (2026-08-18), verdict ACCEPTED WITH REQUIRED CHANGES, re-checked by T27. No captured number was voided; all four reproduce byte-for-byte three ways including on a fresh (19, HALF_UP) tenant, and B-03/B-04 are now re-derived digit-for-digit from the pinned source (T30, .softhouse/reviews/t30-probe/). T22 P0-5 (the broken -o out/B-$n-*-raw.json glob, missing %{http_code}) is CLOSED by T30. THREE P0 items remain open - P0-3 attestation sidecar, P0-4 fail-the-run preconditions, P0-6 re-point at a production-settings tenant - each needing a live oracle.`

**3.** replace
`NEITHER pass is audited yet (T18, T19) and NO vector has been promoted to the store.`
with
`Both passes have since been audited (T18, T19), each ACCEPTED WITH REQUIRED CHANGES, and NO vector has been promoted to the store. Independently of those audits, passes 1-2 ran at precision 12/8 and are therefore discrimination probes that may NEVER be promoted as parity vectors.`

After applying, re-validate with `python3 -c "import json; json.load(open('.softhouse/tasks.json'))"`.

---

## Still PARKED — `oracle_unreachable`

Unchanged from T27 §7; none of these can be done without a live reference oracle, and **none was attempted or
simulated**.

| item | why the oracle is required |
|---|---|
| **T21 P0-2** | attestation values are readable only inside a live container |
| **T21 P0-3** | re-run `Capture3.java` emitting `periodFromDate` / `feeAmount` / `penaltyAmount` + plan totals |
| **T21 P0-4** | the run recipe can be drafted blind but is only meaningful once validated against the pinned image |
| **T21 P1-8** | capture `decimalPlaces == 0` multiples-of behaviour after separating `CurrencyData.inMultiplesOf` |
| **T21 P1-9** | re-run after switching emissions to `toPlainString()` (no present value affected) |
| **T21 P1-10, P1-11** | P1-10 remains deferred-and-recorded (T25); P1-11 needs the `36 × 16.8 %` small-principal capture |
| **T22 P0-3** | machine-readable attestation sidecar per Path B capture set |
| **T22 P0-4** | preconditions must be validated against a running server; parked with P0-6 (drafted-open note left in `REPRODUCE.md:105-110`) |
| **T22 P0-6** | re-point Path B at the `gerege` tenant (Asia/Ulaanbaatar, HALF_UP) and re-capture |
| **T22 P1-11, second clause** | capture a vector that forces the EMI re-adjust loop to iterate — the behaviour is now *recorded*, still *unvectored* |
| **T27 RC-5** | re-emit `t21v2-probe2-oracle-out.txt` with the provenance header its sibling prints |
| **T27 RC-6, attestation half** | an attestation confirming the round-down probe ran at `(19, HALF_UP)`; the conclusion is mode-robust, the *record* is not attested |

**Outstanding P0 count is now 6, down from 7** — T22 P0-5 is closed. Promotability is unchanged:
**nothing may be promoted to the parity vector store today.**

---

## Recommendations destined for DEC-1 — deliberately NOT applied (T28 owns those files)

I did not touch `docs/adr/DEC-1-schedule-generator-adapter.md` or
`nexus/internal/apps/loanschedule/contract/contract.go`. **T28's DEC-1 v4 landed on `main` after my branch
point** (`0717442`), so I read it out of `main` (`git show main:docs/adr/…`, read-only) before writing this
list, to avoid handing back recommendations it already carries.

**Already carried by DEC-1 v4 — do NOT re-raise:** the final-period residual defined rather than named (§4.3);
the EMI re-adjust loop specified by trigger **and** effect, including `Money.copy(double)` replacing the
amount (§4.3.1, §8 item 7, §11); `FULL_LEAP_YEAR` ≡ the field being unset (§4.7 note at `:433`); the
round-to-nearest `installmentAmountInMultiplesOf` rule.

**Genuinely new, and destined for the next revision:**

1. **DEC-1 v4's own largest evidence gap is now closed** — but the document does not know it yet. §8 item 5
   lists as still-open: *"`DayCountActualActual` vectors, and an independent source re-derivation of the
   **cross-year partial-period arm** [`:1505-1507`, `:1526-1531`] — the largest un-re-derived hole in the
   evidence"*, and §4.10 flags that **Q3b's schedule came out of that arm**. **T30 has now re-derived that arm
   from source and reproduced two committed oracle captures through it digit-for-digit**
   (`.softhouse/reviews/t30-probe/`). The next revision should cite it and strike item 5's second clause.
   *(The vectors clause of item 5 stays open: `B-03`/`B-04` are `DayCountActualActual` observations but are
   not promotable — T22 P0-3/P0-4/P0-6.)*
2. **`daysInYearCustomStrategy = FEB_29_PERIOD_ONLY` has TWO effects, not one.** v4 §4.7/§4.10 describe only
   the day-count substitution ("substituting a 365/366-day year for a period containing 29 February"). It
   **also suppresses the cross-year partial-period calculation** for a period containing no 29 February —
   `partialPeriodCalculationNeeded` (`:1372-1374` / `:1505-1507`) has
   `(strategy != FEB_29_PERIOD_ONLY || periodContainsFeb29)` as its third conjunct. A port that implements
   only the substitution returns `B-03`'s period-12 numbers for `B-04` and fails the one vector in the corpus
   that grades the field. This interacts with v4 §4.10's `FrequencyYears` reasoning: an annual period always
   crosses a year boundary, so `partialPeriodCalculationNeeded` is *always* true there **only while the
   strategy is not `FEB_29_PERIOD_ONLY`** — with that strategy and no 29 February in the period, the arm v4
   calls unreachable (`case ACTUAL` at `:1534-1535`) becomes reachable again.
3. **The cross-year partial-period rule, normatively** — `Σ days(segment) / Year.length(year)`, segmented at
   31 December (`calculatePeriodFractions` `:1550-1568`; the split date is `(year+1)-01-01` when
   `isInterestRecognitionOnDisbursementDate` is true, `:1578-1584`), then `rate × fraction` followed by
   `setScale(19, mode)` (`:1965-1978`). Two traps for the Go module: the `interestFractionPerPeriod` multiply
   is **exact**, deliberately outside the `MathContext`, unlike every neighbouring operation; and the trailing
   `setScale(mc.getPrecision(), …)` is **decimal places, not significant digits** — v4 §4.9 already names this
   pattern at `:1976-1979` as one of only two occurrences in Fineract main code, so the arm is now witnessed
   against real captures rather than only read.
4. **Worked numbers the next revision can quote** (all re-derived, and each matching a committed observation):
   `B-03` period 12 rate factor `0.0182966988…` from `30/366 + 1/365` under the partial arm, against
   `0.0182950819…` (`31/366`) if the arm is skipped; `B-04` period 12 `0.0183452054…` (`31/365`) with the arm
   suppressed. Signed final-period residuals `+0.05` (`B-03`) and `−0.05` (`B-04`), both below the
   `floor(n/2) = 6` re-adjust guard, so the loop provably does not fire on either.

---

## Non-negotiables scan (CLAUDE.md)

| check | result |
|---|---|
| Money as integer minor units; **no float in any money path** | ✅ My re-derivation is exact `Decimal` end to end, parsed with `parse_float=Decimal, parse_int=Decimal`; the only `float` tokens in it are the prohibition sentence in its docstring and that `parse_float` argument, which exists to *prevent* floats. Every comparison is integer minor units, **no tolerance**. |
| Prohibited DB engines (`ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`) | ✅ Scanned every file I touched or created: **zero new hits**; every pre-existing hit is a prohibition statement in prose (`REPRODUCE.md:18`, `PASS2-REPORT.md:26`, `reference-oracle.md:77-85,109`). |
| PostgreSQL only | ✅ nothing changed; Path B provenance still records `org.postgresql.Driver`, `jdbc:postgresql://db:5432/…`, PostgreSQL 18.3 |
| "oracle" terminology | ✅ used only in the **test-oracle** sense (the pinned Fineract reference implementation); Oracle Database appears only where named as prohibited |
| No US payment rails / vendors | ✅ zero hits in anything I wrote |
| MNT | ✅ ISO 4217 numeric 496, minor unit 2; the Path B products carry `digitsAfterDecimal: 2`, `inMultiplesOf: 0` |
| Production `MathContext` | ✅ `(19, HALF_UP)` treated as the target throughout; `MoneyHelper.PRECISION = 19` handled as the compile-time constant it is; **no capture at precision 12 or 8 was described as anything but a discrimination probe** — and `PASS2-REPORT.md` now says so on line 5 |
| Three-field Mongolian names | ✅ untouched; Path B fixtures use the oracle's own `fullname` column, not a Gerege surface |
| No hard-coded timezone offset or payment threshold | ✅ none introduced; the `Asia/Kolkata` tenant remains recorded as a **defect** (T22 P0-6), not accepted |
| Nothing promoted / no contract-shaped storage / no gate answered | ✅ no vector promoted, no DEC-n touched, no cutover implied, no `user` gate crossed |
| Go module | ✅ no Go changed; `go build ./...` exits 0 |

## Boundaries respected

- **No file outside `/home/user/wt-T30` was written.** `/home/user/gerege-nbfi` and every other worktree
  untouched; `/home/user/fineract` read-only.
- **`docs/adr/DEC-1-schedule-generator-adapter.md` and `nexus/internal/apps/loanschedule/contract/contract.go`
  NOT edited** — T28 owns them (§5 carries what would otherwise have gone there).
- **`.softhouse/tasks.json` NOT edited** — the orchestrator owns it; exact wording supplied above.
- Nothing merged, pushed, or promoted; `main` untouched.
