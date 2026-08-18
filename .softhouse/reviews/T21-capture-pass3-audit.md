# T21 — independent audit of capture pass 3

**Auditor:** T21-v2 reviewer, isolated worktree `softhouse/T21-capture-pass3-audit-v2`, 2026-08-18.
**Under audit:** `.softhouse/capture/PASS3-REPORT.md` (identical to `PASS3-REPORT-shared.md`, `diff` exit 0),
`.softhouse/capture/src/Capture3.java`, `.softhouse/capture/out/capture-prod-{raw.json,log.txt,stderr.txt}`.
**Reference oracle:** pinned Fineract `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(read-only, working tree clean), image `fineract:latest` =
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`.
**Scratch:** `/tmp/t21v2/**`. **No file under `.softhouse/capture/` was modified by this audit.**
My own artefacts live under `.softhouse/reviews/t21v2/`.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

Every **number** in pass 3 survives audit, and survives it harder than any previous pass. I re-ran
`Capture3.java` unmodified in the pinned image and the JSON is **byte-identical** to the committed file
(SHA-256 `11c5c74a…a732e2` on both). I then re-derived **all twelve** captures from the pinned Fineract
*source* in a model I wrote myself — not the earlier T21 worker's — and matched every period, every column,
every total, **to the minor unit**, including the four MNT-scale schedules and the P-03 pre-disbursement
boundary. The six property invariants the report claims hold integer-exact on all twelve, checked by my own
script. `P-CAL` reproduces the shipped test literal digit for digit and `P-01` is byte-identical to pass-1
`D-01-p19`.

It is **not** ACCEPTED outright for three reasons, in descending order of seriousness.

1. **PASS3-REPORT.md §"Finding — precision is load-bearing, but only above a size threshold" is FALSE, and
   the oracle says so.** The oracle's own p12-vs-p19 pair **diverges at principal 4.00** on the
   `36 × 16.8 %` shape — the very shape of `P-MNT-50M` — while it is **identical at principal 50,000,000**
   on that same shape, and **identical at principal 87,654,321** on the `6 × 7.0 %` shape. There is no size
   threshold. Divergence is a rounding-boundary property of the `(principal, n, rate)` triple, not a
   magnitude property of the principal. Worse, the sentence "this matters directly for Mongolia, where
   ordinary principals are exactly in the range where it starts to bite" is contradicted by pass 3's *own*
   MNT captures: all four are p12/p19-**identical**.
2. **Pass 3 inherits, unfixed, three of T18's four P0 admissibility blockers and T19's required change 10.**
   No environment-attestation block; `fromDate`, `fee` and `penalty` still not emitted though the plan
   mandates them and the oracle exposes them; no pass-3 run recipe committed; error branch still discards
   the stack trace; `BigDecimal.toString()` still used instead of `toPlainString()`; and the harness still
   cannot express `CurrencyData.inMultiplesOf` independently of `installmentAmountInMultiplesOf`. By the
   capture plan's own §4.1 rule these are **not yet admissible vectors**, however good the numbers are.
3. **Downstream text already over-states the corpus.** `.softhouse/tasks.json:188` says pass 3 is
   "12 captures at PRODUCTION settings (19, HALF_UP)". It is **eleven**; `P-CAL` runs at `(12, HALF_UP)` and
   is calibration, not parity. The report itself is correct on this point (`PASS3-REPORT.md:30-31`); the
   task note is not.

None of these voids a number. All are fixable; (2) needs one re-run of the JVM.

---

## 1. What I re-ran, exactly

Every command below was executed by me during this audit. `$W` = the repo worktree root.

**Provenance.**
```sh
docker image inspect fineract:latest --format '{{.Id}}'
# -> sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a   (matches)
git -C /Users/buv/fineract log -1 --format='%H %cI'
# -> 426a23544e8426a38ae43ae404670a0a7e85b9eb 2026-08-12T14:59:16+02:00
git -C /Users/buv/fineract status --short          # -> empty (clean)
shasum -a 256 $W/.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java \
  /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
# -> bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714  twice; diff exit 0
```
The seam-class byte-identity check is load-bearing exactly as T18 said: the embeddable module is not
bundled in `/app/fineract-provider.jar`, so it must be compiled from the pinned source.

**Reproduction (P0 item 1 of the brief).**
```sh
mkdir -p /tmp/t21v2/src /tmp/t21v2/out
cp $W/.softhouse/capture/src/Capture3.java                             /tmp/t21v2/src/
cp $W/.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java /tmp/t21v2/src/
docker run --rm --user 0 --entrypoint sh -v /tmp/t21v2:/cap fineract:latest -c '
  set -e; mkdir -p /work && cd /work
  unzip -q /app/fineract-provider.jar -d /work/jar
  CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
  mkdir -p /work/classes
  javac -nowarn -cp "$CP" -d /work/classes /cap/src/Capture3.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
  java  -cp "/work/classes:$CP" Capture3 > /cap/out/capture-prod-raw.json 2> /cap/out/capture-prod-stderr.txt'
# then the README-pass2 log/JSON split, then:
diff /tmp/t21v2/out/capture-prod-raw.json $W/.softhouse/capture/out/capture-prod-raw.json   # -> no output
```

**Independent re-derivation, invariants, cross-pass, oracle probes** — all under
`.softhouse/reviews/t21v2/`:
```sh
python3 .softhouse/reviews/t21v2/t21v2-rederive.py   .softhouse/capture/out/capture-prod-raw.json
python3 .softhouse/reviews/t21v2/t21v2-invariants.py .softhouse/capture/out/capture-prod-raw.json
python3 .softhouse/reviews/t21v2/t21v2-crosspass.py
python3 .softhouse/reviews/t21v2/t21v2-threshold.py                     # model-located candidates only
# oracle probes, same recipe as above but compiling T21v2Probe.java / T21v2Probe2.java:
#   outputs: .softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt, t21v2-probe2-oracle-out.txt
```

**Reproduction result: byte-for-byte PASS.**

| Artefact | Committed | My re-run | Result |
|---|---|---|---|
| `capture-prod-raw.json` | 48,716 B, sha256 `11c5c74a…a732e2` | 48,716 B, same sha256 | **byte-identical** |
| `capture-prod-log.txt` | 12 `MoneyHelper` lines, 12 distinct tenant ids | same 12 lines, same order | identical modulo timestamps |
| `capture-prod-stderr.txt` | 0 bytes | 0 bytes | identical |

The prior T21 worker's `t21-probe-repro-json.json` is also byte-identical to both
[`diff` exit 0] — so its reproduction step is confirmed, independently, by mine.

---

## 2. Per-capture table

Twelve captures in total, **eleven** of them parity candidates; `P-CAL` is calibration. (The brief's
"all 12 + P-CAL" phrasing implies thirteen — there are twelve records including `P-CAL`.)

| id | MathContext | ccy | reproduced byte-for-byte | six invariants | my source re-derivation | role |
|---|---|---|---|---|---|---|
| `P-CAL` | (12, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | **CALIBRATION ONLY — never a parity vector** |
| `P-00` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-01` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | parity candidate (≡ pass-1 `D-01-p19`) |
| `P-02` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match (dates re-derived from source) | parity candidate |
| `P-02b` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-03` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match (5-installment EMI + zero snapshot) | parity candidate — see §4 |
| `P-04f` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-04t` | (19, HALF_UP) | usd | ✅ | ✅ all 6 | ✅ full match | parity candidate (≡ `P-04f`) |
| `P-MNT-5M` | (19, HALF_UP) | MNT | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-MNT-1M2` | (19, HALF_UP) | MNT | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-MNT-50M` | (19, HALF_UP) | MNT | ✅ | ✅ all 6 | ✅ full match | parity candidate |
| `P-MNT-4M999` | (19, HALF_UP) | MNT | ✅ | ✅ all 6 | ✅ full match | parity candidate |

Observed totals, as emitted (no value below is derived by me):

| id | term (days) | disbursed | interest | repayment |
|---|---|---|---|---|
| `P-CAL` / `P-00` / `P-02` / `P-02b` / `P-04f` / `P-04t` | 182 | 100.00 | 2.05 | 102.05 |
| `P-01` | 547 | 87654321.00 | 13393481.04 | 101047802.04 |
| `P-03` | 182 | 100.00 | 1.76 | 101.76 |
| `P-MNT-5M` | 547 | 5000000.00 | 763994.33 | 5763994.33 |
| `P-MNT-1M2` | 366 | 1200000.00 | 144988.47 | 1344988.47 |
| `P-MNT-50M` | 1096 | 50000000.00 | 13995886.40 | 63995886.40 |
| `P-MNT-4M999` | 547 | 4999999.00 | 763994.20 | 5763993.20 |

The report's MNT table (`PASS3-REPORT.md:67-72`) matches this exactly.

---

## 3. Calibration and cross-pass identity — both PASS

**`P-CAL` reproduces the shipped literal, digit for digit.** I compared it against the source test, not
against C-00, so this is a second independent confirmation:
`EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92` asserts term 182, disbursed 100.00, interest
2.05, repayment 102.05, and the six splits `16.43/0.58`, `16.52/0.49`, `16.62/0.39`, `16.72/0.29`,
`16.81/0.20`, `16.90/0.10` with balances `83.57/67.05/50.43/33.71/16.90/0.00` and total-outstanding
`85.04/68.03/51.02/34.01/17.00/0.00`. `P-CAL` emits precisely those values.

**`P-CAL` is correctly labelled.** `PASS3-REPORT.md:30-31` states it runs at `(12, HALF_UP)` and "is the rig
calibration, not a parity vector"; `Capture3.java:23-27` says the same in the harness header; the emitted
`inputs.mathContextPrecision` is `12`, so a downstream consumer can tell mechanically. **One downstream
document does treat it as one** — see required change P1-6.

**Cross-pass identity — all confirmed by structural comparison of the whole `observed` block:**

| pair | result |
|---|---|
| `P-CAL` (pass 3) vs `C-00` (pass 1) | **IDENTICAL** — every period, every column |
| `P-01` (pass 3) vs `D-01-p19` (pass 1) | **IDENTICAL** — every period, every column |
| `P-00` vs `P-CAL` | **IDENTICAL** (so precision is a no-op at C-00 inputs — the report is right) |
| `P-04f` vs `P-04t` vs `P-00` | **IDENTICAL** |
| `P-01` vs `D-01` (pass 1, precision 12) | **DIFFERENT** — `13393481.04` vs `13393481.05`; periods 5, 17, 18 move principal/interest and every period's `totalOutstandingBalance` shifts by 0.01 |

The `inputs` blocks of `P-CAL`/`C-00` and `P-01`/`D-01-p19` differ only in the four fields pass 1 had no
concept of (`tenantId`, `tenantRoundingModeValue`, `ambientMoneyHelperMathContext`, `currencyInMultiplesOf`).
Nothing load-bearing differs.

---

## 4. Independent re-derivation from the pinned source

I wrote `.softhouse/reviews/t21v2/t21v2-rederive.py` from the Fineract source alone. It does **not** import
or reuse `t21-probe-rederive.py`; I read each arithmetic step out of the pinned checkout and cited it in the
module docstring. It reproduces **all twelve captures exactly** — every `dueDate`, `principal`, `interest`,
`total`, `outstandingBalance`, plus `totalInterestAmount`, `totalRepaymentAmount` and `loanTermInDays`:

```
P-CAL FULL MATCH (EMI=17.01)          P-MNT-5M    FULL MATCH (EMI=320221.91)
P-00  FULL MATCH (EMI=17.01)          P-MNT-1M2   FULL MATCH (EMI=112082.37)
P-01  FULL MATCH (EMI=5613766.78)     P-MNT-50M   FULL MATCH (EMI=1777663.51)
P-04f FULL MATCH  P-04t FULL MATCH    P-MNT-4M999 FULL MATCH (EMI=320221.84)
P-02  FULL MATCH  P-02b FULL MATCH    P-03        FULL MATCH (EMI=20.35)
```

The brief asked for at least one MNT-scale schedule; all four are matched, including the 36-period
`P-MNT-50M`, which is the longest and most rounding-sensitive schedule in the corpus.

### The final-installment residual-absorption rule, from source

**`ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI`,
`ProgressiveEMICalculator.java:1160-1219`.** After every period has been assigned the common EMI, the whole
residual is absorbed into the **last not-fully-paid** repayment period's EMI in a single addition:

```java
// ProgressiveEMICalculator.java:1190-1203
Money totalDueInterest      = Σ rp.getDueInterest()                        // :1190-1191
Money totalEMI              = Σ rp.getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest()  // :1192-1194
Money totalDisbursedAmount  = Σ ip.getDisbursementAmount()                 // :1195-1197
Money totalCapitalizedIncome= Σ ip.getCapitalizedIncomePrincipal()         // :1198-1200
Money diff = totalDisbursedAmount.plus(totalCapitalizedIncome, mc)
                                 .plus(scheduleModel.getTotalCreditedPrincipal(), mc)
                                 .plus(totalDueInterest, mc)
                                 .minus(totalEMI, mc);                     // :1202-1203
Money adjustedEmi = repaymentPeriod.getEmi().add(diff, mc);                // :1205
repaymentPeriod.setEmi(adjustedEmi);                                       // :1210
```

The target period is selected at `:1176-1181` (last `!isFullyPaid()`; on a fresh schedule that is simply the
last period). It is emphatically **not** a "last principal = whatever balance remains" rule: the rule adjusts
the last **EMI**, and the principal then falls out of `duePrincipal = EMI − dueInterest`
[`RepaymentPeriod.java:345-350`] with `dueInterest = min(calculatedDueInterest, EMI)`
[`RepaymentPeriod.java:272-286`]. That is why `P-CAL`'s last installment is `17.00`, not `17.01`, and why
`P-MNT-4M999`'s totals end `…93.20` while `P-MNT-5M`'s end `…94.33`.

A **second** smoothing pass follows it, `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
[`ProgressiveEMICalculator.java:1258-1309`], gated on
`EmiAdjustment.shouldBeAdjusted()` [`EmiAdjustment.java:31-36`]:
`floor(n/2) > 0 && diff ≠ 0 && |lastEmi − penultimateEmi| × 100 > Money(floor(n/2))`.
Note the right-hand side: `originalEmi.copy(lowerHalfOfRelatedPeriods)` **replaces** the amount
[`Money.java:216-222`], so the threshold is the bare number `floor(n/2)` in currency units — **not**
`EMI × floor(n/2)`. It re-runs at most three times (`:1308`) and backs out if the difference did not shrink
(`:1289-1291`). This pass fires on none of the twelve pass-3 captures, but it **does** fire on nearby inputs,
and getting it wrong is exactly what broke the prior worker's model (§6).

### Two structural facts I confirmed from source while doing this

- **P-03's emission order has a mechanism.** `ProgressiveLoanScheduleGenerator.java:116-145`: the per-period
  loop calls `processDisbursements` at the **top** of each iteration (`:121`) and appends the repayment row
  at `:141`. A disbursement dated on period 1's *due* date is therefore applied during iteration **2**, after
  period 1's (all-zero) row has already been appended. The oracle's emitted order is a consequence of loop
  placement, not a sort. Buyan's option (a) — reproduce it — is pinned by this vector.
- **`loanTermInDays` is measured from the SCHEDULE start, not the disbursement date.**
  `ProgressiveLoanInterestScheduleModel.java:200-207` →
  `getExactDifferenceInDays(firstPeriod.getFromDate(), lastPeriod.getDueDate())`. P-03's `182` is
  2024-01-01 → 2024-07-01. This is correct behaviour, **not** a defect, and the prior worker's note on it is
  confirmed.

---

## 5. Invariants — I re-checked all six myself, on all twelve

`.softhouse/reviews/t21v2/t21v2-invariants.py`, written from scratch: parses every money string to **integer
minor units** and applies **no tolerance anywhere**. It checks the six the report claims (R1–R6) plus six of
my own (A1–A6).

```
capture         R1  R2  R3  R4  R5  R6  A1  A2  A3  A4  A5  A6   six-claimed  all
P-CAL            .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-00             .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-01             .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-02             .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-02b            .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-03             .   .   .   .   .   .   . !!!   .   .   .   .   PASS         FAIL
P-04f            .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-04t            .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-MNT-5M         .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-MNT-1M2        .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-MNT-50M        .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
P-MNT-4M999      .   .   .   .   .   .   .   .   .   .   .   .   PASS         PASS
SIX-CLAIMED verdict: ALL PASS
```

- **R1** final `balance` = 0; **R2** Σ principal = disbursed; **R3** Σ interest = `totalInterestAmount`;
  **R4** Σ total = `totalRepaymentAmount`; **R5** per period principal + interest = total;
  **R6** disbursed + interest = repayment.
- **A1** Σ DISBURSEMENT principal = disbursed. **A2** *naive* balance roll-forward (start at `disbursed`,
  subtract each repayment principal) — this is the prior worker's `X2`. **A3** *position-aware* roll-forward
  (walk the emitted list; DISBURSEMENT adds, REPAYMENT subtracts). **A4** `totalOutstandingBalance`
  roll-forward. **A5** every money string is exactly `currencyDecimalPlaces` decimals and carries no exponent
  — no `toString()` scientific notation escaped into any capture. **A6** no negative money anywhere.

All twelve pass **all six claimed invariants, integer-exact**. `A2` fails on `P-03` only, and that is a
defect in `A2`'s formulation — see §6.1.

---

## 6. The two load-bearing questions

### 6.1 `P-03` / invariant `X2` — the orchestrator's claim stands; the prior worker's `X2` is malformed

**Verdict on the report's claim ("all 12 captures satisfy all six property invariants, integer-exact"):
CONFIRMED.**
**Verdict on the prior worker's `X2` failure: REPRODUCED as a fact, but it is an artefact of the
invariant, not a defect in the capture. The brief's premise — that an `X2` failure would falsify the
report — is itself wrong.**

Three findings, in order:

1. **`X2` is not one of the six.** `t21-probe-invariants.py`'s own docstring lists `I1..I6` as "the six
   invariants (as specified in the T21 brief)" and then says "*Plus two extra checks of my own: X1, X2*".
   `X2` is the prior worker's invention. Its failing therefore cannot, by construction, contradict a claim
   about the six. I re-ran that script and reproduce its output exactly (`P-03` `!!` on `X2`, everything else
   `OK`), so the observation is real — it is the inference drawn from it in the brief that does not follow.

2. **`X2` as written is wrong for this schedule shape.** It seeds the running balance at
   `totalDisbursedAmount` and then subtracts each repayment's principal. `P-03`'s first emitted period is a
   **pre-disbursement snapshot**: `{periodNumber: 1, dueDate: 2024-02-01, balance: 0.00, principal: 0.00,
   interest: 0.00, total: 0.00, totalOutstandingBalance: 101.76}` emitted **before** the
   `DISBURSEMENT 2024-02-01 100.00` row. At that instant nothing has been disbursed, so `balance = 0.00` is
   the *correct* value; `X2` expects `100.00` and fails on the first comparison. The invariant assumes the
   disbursement precedes all repayment rows — an assumption `P-03` was captured specifically to break.

3. **The correctly formulated version holds on all twelve, `P-03` included.** My `A3` walks the emitted list
   in order and lets a `DISBURSEMENT` row *add* to the running balance:
   `0 − 0 = 0.00 ✓`, `+100.00`, `100.00 − 19.77 = 80.23 ✓`, `− 19.88 = 60.35 ✓`, `− 20.00 = 40.35 ✓`,
   `− 20.11 = 20.24 ✓`, `− 20.24 = 0.00 ✓`. My `A4` (`totalOutstandingBalance` roll-forward) also holds on
   `P-03`, starting from `101.76` and landing on `0.00`.

So: **the capture is sound, the report's invariant claim is true, and the prior worker's `X2` needs
replacing with `A3` before anyone runs it again.** The zeroed period-1 row is genuine oracle behaviour with a
source mechanism (`ProgressiveLoanScheduleGenerator.java:116-145`, §4), and `loanTermInDays = 182` measured
from the schedule start is likewise correct (`ProgressiveLoanInterestScheduleModel.java:200-207`).

### 6.2 The size-threshold claim — **REFUTED by the oracle**

**Verdict: REFUTED.** Not "unsupported" — actively contradicted, by the pinned oracle, at three separate
points.

Method, as the brief required: my model located candidates; **only the oracle's answers are quoted below**.
Before relying on the model I established it reproduces the oracle on all twelve pass-3 captures (§4), and
then I ran **17 further oracle points** through the seam and confirmed the model called every one of them
correctly. Full transcript: `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt`.

Oracle observations, `MathContext(12, HALF_UP)` vs `MathContext(19, HALF_UP)`, everything else fixed
(2024-01-01 start, monthly, DAYS_30/DAYS_360, DECLINING_BALANCE, 2 decimals):

| shape | principal | p12 total interest | p19 total interest | oracle verdict |
|---|---|---|---|---|
| 36 × 16.8 % | **4** | `1.13` | `1.14` | **DIFFERENT** |
| 36 × 16.8 % | 59 | `16.52` | `16.51` | **DIFFERENT** |
| 36 × 16.8 % | 72 | `20.13` | `20.14` | **DIFFERENT** |
| 36 × 16.8 % | 340 | `95.16` | `95.15` | **DIFFERENT** |
| 36 × 16.8 % | 426 | `119.20` | `119.18` | **DIFFERENT** |
| 36 × 16.8 % | 6,940 | `1942.66` | `1942.65` | **DIFFERENT** |
| 36 × 16.8 % | **50,000,000** (`P-MNT-50M`) | `13995886.40` | `13995886.40` | **IDENTICAL** |
| 6 × 7.0 % | 100 (`P-CAL`/`P-00`) | `2.05` | `2.05` | IDENTICAL |
| 6 × 7.0 % | 43,811 | `898.82` | `898.82` | IDENTICAL |
| 6 × 7.0 % | 131,432 | `2696.42` | `2696.42` | IDENTICAL |
| 6 × 7.0 % | **131,433** | `2696.43` | `2696.43` | **DIFFERENT** (per-period, totals equal) |
| 6 × 7.0 % | **87,654,321** | `1798283.07` | `1798283.07` | **IDENTICAL** |
| 18 × 18.5 % | 199,999 | `30559.63` | `30559.63` | IDENTICAL |
| 18 × 18.5 % | 4,999,999 (`P-MNT-4M999`) | `763994.20` | `763994.20` | IDENTICAL |
| 18 × 18.5 % | 5,000,000 (`P-MNT-5M`) | `763994.33` | `763994.33` | IDENTICAL |
| 12 × 21.6 % | 1,200,000 (`P-MNT-1M2`) | `144988.47` | `144988.47` | IDENTICAL |
| 18 × 18.5 % | 87,654,321 (`P-01`) | `13393481.05` | `13393481.04` | **DIFFERENT** |

What this destroys, sentence by sentence:

- *"precision changes the schedule once the principal is large enough that 12 significant digits stop covering
  the intermediate products"* — **false**. At `36 × 16.8 %` the smallest divergent principal is **4.00**
  (400 minor units), and the divergence there is not marginal: it moves 0.01 of interest, shifts every
  period's `totalOutstandingBalance`, and changes period 17's split from `0.11/0.03` (p12) to `0.10/0.04`
  (p19) and the final installment from `0.23` to `0.24`.
- *"A 100-unit loan cannot show it; an 87-million-unit loan does."* — **both halves false as stated**. A
  4.00-unit loan shows it (at 36 periods); an 87,654,321-unit loan does **not** show it at `6 × 7.0 %`. The
  87-million observation belongs to the `18 × 18.5 %` shape, not to the magnitude.
- *"this matters directly for Mongolia, where ordinary principals are exactly in the range where it starts to
  bite"* — **contradicted by pass 3's own captures**. All four MNT captures — 1.2M, 4,999,999, 5M and 50M —
  are p12/p19 **identical**. Pass 3 supplies no evidence at all that MNT-scale loans are precision-sensitive.
- The one thing that **is** established, and should replace the whole section: *at production settings the
  arithmetic is sensitive to `MathContext` precision on some `(principal, n, rate)` triples and insensitive
  on others; sensitivity is a rounding-boundary property and is not monotone in principal.* `P-01` is a
  witness that it happens at realistic sizes; `P-MNT-50M` is a witness that it does not always. Both are
  in the corpus, which is a good thing — the corpus is fine, the prose about it is not.

Practical consequence for the port, and it is the opposite of reassuring: **no cheap "small loans are safe"
heuristic exists.** A Go implementation that gets the precision seam wrong can diverge on a 4-unit loan. The
conformance corpus must therefore cover *shape* (number of periods, rate) as deliberately as it covers size,
and the `36 × 16.8 %` shape at small principals is now a known-good discriminator worth capturing.

---

## 7. The two dropped inputs, re-tested at `(19, HALF_UP)` — **CONFIRMED, both**

Both differential and mechanism, at the ratified production `MathContext`, through the Path A seam.
Transcript: `.softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt`, sections B, C, D.

**Differential (oracle, `(19, HALF_UP)`, distinct tenant per run, rounding mode HALF_UP(4)):**

| probe | result |
|---|---|
| MNT 50,000,000 / 36 × 16.8 %, `installmentAmountInMultiplesOf` **null vs 100** | **IDENTICAL** |
| MNT 50,000,000 / 36 × 16.8 %, `installmentAmountInMultiplesOf` **null vs 100000** | **IDENTICAL** |
| MNT 50,000,000 / 18 × 16.8 %, ACTUAL/ACTUAL over leap 2024, `daysInYearCustomStrategy` **null vs FULL_LEAP_YEAR** | **IDENTICAL** |
| …same, **null vs FEB_29_PERIOD_ONLY** | **IDENTICAL** |
| MNT 5,000,000 / 18 × 18.5 %, **`CurrencyData.inMultiplesOf` null vs 100 at `decimalPlaces = 0`** | **DIFFERENT** — total interest `763994` vs `764100`; all 18 periods differ |

`installmentAmountInMultiplesOf = 100000` on a 1,777,663.51 EMI is not a rounding no-op by any reading, so
this differential is probative in a way T19 showed the pass-2 evidence was not.

**Mechanism, read reflectively out of the seam's own assembly path at `(19, HALF_UP)`:**

```
modelData.installmentAmountInMultiplesOf() = 999
modelData.daysInYearCustomStrategy()       = FULL_LEAP_YEAR
modelData.currency().getInMultiplesOf()    = 777
terms.installmentAmountInMultiplesOf (reflected)                = null
terms.daysInYearCustomStrategy       (reflected)                = null
terms.getInstallmentAmountInMultiplesOf()                       = null
terms.toLoanConfigurationDetails().getDaysInYearCustomStrategy()= null
terms.getSeedDate()                                             = 2024-01-01
```

And in source, confirmed by my own reading:

- **`installmentAmountInMultiplesOf`** — the field exists (`LoanApplicationTerms.java:217`) but the `Builder`
  has **no setter for it at all**, and `assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
  (`:579-607`) builds exclusively through the `Builder`. The only assignments are in the long positional
  constructors (`:828`), which this path never reaches. It is structurally unreachable, not merely unset.
- **`daysInYearCustomStrategy`** — worse, because it *looks* wired. `assembleFrom` **does** call
  `.daysInYearCustomStrategy(modelData.daysInYearCustomStrategy())` (`:604`), and the `Builder` **does**
  store it (`:380`, setter `:567-568`) — but the private constructor `LoanApplicationTerms(Builder)`
  (`:304-351`) **never copies it out of the builder**. The single `this.daysInYearCustomStrategy =`
  assignment in the class is at `:881`, in a positional constructor. This is a hand-maintained builder copy
  with a silently skipped entry, exactly the defect class T19 named.
- The one *capturable* multiples-of behaviour is the `CurrencyData.inMultiplesOf` channel, gated on
  `currency.getDecimalPlaces() == 0` (`Money.java:48-51`) — and it moves money at that setting, as the fifth
  row above shows. MNT is minor unit 2, so this channel is inert for us in production, but it is the only
  multiples-of path Path A can exercise.

**So the established finding survives at production settings unchanged: the seam accepts a 19-component
`LoanRepaymentScheduleModelData` and honours 17.** For those two inputs the Path A corpus has **zero**
discriminating power — a Go port that honours them and one that ignores them produce identical vectors and
both pass. (Path B, captured after pass 3 and audited separately under T22, reaches them through the running
server; nothing here contradicts that, and the two results are complementary: the *server* honours what the
*seam* drops.)

---

## 8. Applying T18's and T19's lists to pass 3

### T18's P0 list

| T18 P0 | status in pass 3 | evidence |
|---|---|---|
| 1. Machine-readable **environment-attestation block** in the artefact | **NOT FIXED** | `capture-prod-raw.json` top level is `{pass, harness, moneyHelperPrecision, captures}` — no `attestation` object. Partial credit: `moneyHelperPrecision: 19` is now stamped at runtime, and each capture carries `tenantId`, `tenantRoundingModeValue` and `ambientMoneyHelperMathContext` — a real improvement over pass 1, but not the block plan §4.1 requires (no image digest, no `git.properties` commit, no JVM string, no classpath hashes, no UTC timestamp, no capture-path label) |
| 2. **Committed reproducible run recipe** | **PARTIALLY FIXED** | `PASS3-REPORT.md:22-23` points at `README-pass2.md` "substituting `Capture3.java`". That is a prose instruction, not a committed script, and there is no `README-pass3.md`. The seam byte-identity check is still a manual habit, not a step that fails the run |
| 3. **Emit `periodFromDate`, `feeAmount`, `penaltyAmount`** | **NOT FIXED** | `Capture3.java` emits `periodNumber, dueDate, balance, principal, interest, total, totalOutstandingBalance` and nothing else. The oracle has them: `LoanSchedulePlan.java:70,74,75` populates `fromDate`/`fee`/`penalty`, and my probe read them straight off (`from=2024-01-01 … fee=0.00 pen=0.00`). The shipped test asserts `periodFromDate` on all seven C-00 periods (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:104`). Without `fromDate` no vector can catch a period-boundary error in the Go port |
| 4 (T18 P1-5). **Print the stack trace on the error branch** | **NOT FIXED** | `Capture3.java` catch block keeps only `e.getClass().getName()` and `e.getMessage()`. No pass-3 capture errored, so nothing was lost this time |

### T18's P1 items that bear on pass 3

| item | status |
|---|---|
| 6. `toPlainString()` everywhere | **NOT FIXED** — still `StringBuilder.append(BigDecimal)`. My check `A5` confirms **no capture is affected today** (every money string is plain, exactly 2 dp), so this is a latent channel, not a present corruption |
| 7. Record `CurrencyData.inMultiplesOf` in `inputs` | **NOMINALLY FIXED, SUBSTANTIVELY NOT** — `currencyInMultiplesOf` is emitted, but from the *same* variable as `installmentAmountInMultiplesOf` (see T19-10 below) |
| 8. Record the C-00 input deviation | **NOT FIXED** — `Capture3.java` passes `new CurrencyData(code, code, 2, null, code, code)`; the shipped test passes `("usd","US Dollar",2,null,"usd","$")`. Non-load-bearing (only `code`, `decimalPlaces`, `inMultiplesOf` are read on this path) but still undocumented in `PASS3-REPORT.md` |

### T19's required changes

Items 1–9 are corrections to `PASS2-REPORT.md`'s *text* and are not inherited by pass 3. **Item 10 is**, and
it is the one that matters:

> **T19-10. "Separate the two multiples-of fields in any future harness."** — **NOT FIXED.** `Capture3.java`
> constructs `new CurrencyData(code, code, digits, c.installmentMultiplesOf(), …)` **and** passes
> `c.installmentMultiplesOf()` as the model's `installmentAmountInMultiplesOf`, **and** emits both JSON keys
> from that same field. The harness structurally cannot vary the two independently. Inert for pass 3 (all
> twelve pass `null`), but it means the one *capturable* multiples-of behaviour — the `decimalPlaces == 0`
> channel my probe showed moves money — cannot be captured by this harness at all.

Pass 3 **does** satisfy T19's item 4 in spirit: it is the corpus captured at `(19, HALF_UP)`, and the report
states the precision explicitly.

---

## 9. Where the prior T21 worker's WIP is wrong

Said plainly, because the brief asked and because the next fire will otherwise re-use it.

1. **`t21-probe-rederive.py` never applies the EMI smoothing pass.** It computes a boolean
   `emi_adjust_triggered` and returns it; `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
   (`ProgressiveEMICalculator.java:1258-1309`) is never executed. Its schedules are therefore only correct
   on inputs where that pass does not fire.
2. **Its trigger formula is wrong even as a flag.** It uses
   `abs(emi_diff) * 100 > periods[-2]["emi"] * lower_half`. The source is
   `emiDifference.abs().multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods))`
   [`EmiAdjustment.java:33-35`], and `Money.copy(double)` **replaces** the amount
   [`Money.java:216-222`] — so the right-hand side is `Money(floor(n/2))`, not `EMI × floor(n/2)`.
3. **Consequence: `t21-probe-threshold-output.txt` reports divergences the oracle does not have.** Its
   headline "6 × 7.0 % smallest divergent principal ≤ 400000: **43811**" is **wrong**: the oracle emits
   *identical* schedules at 43,811 (I ran it). My model — which does implement the smoothing pass — gives
   **131,433**, and the oracle confirms 131,432 identical / 131,433 different. Its `1e2` "3/225 divergent"
   rows for the 36 × 16.8 % shape are, by luck, in the right direction: the oracle *does* diverge at 4, 59,
   72, 340, 426.
4. **What of its work I confirmed and adopt:** its byte-for-byte reproduction of the capture
   (`t21-probe-repro-json.json`) is correct — I re-ran the capture myself and got the same bytes; and its
   `P-03` structural reading (zeroed pre-disbursement period 1, `loanTermInDays` from the schedule start) is
   correct, which I verified against source rather than against its script.

Net: **the prior worker's conclusion that P-03 fails "invariant X2" is factually reproducible but
analytically void**, and **its threshold probe is unusable as evidence** because the model under it is wrong
on precisely the code path that decides these cases.

---

## 10. Required changes

**P0 — blocks any promotion of a pass-3 capture to the vector store.**

1. **Correct or delete `PASS3-REPORT.md` §"Finding — precision is load-bearing, but only above a size
   threshold"** (`:50-60`), and the same section in `PASS3-REPORT-shared.md`. It is refuted by the oracle
   (§6.2). Replace with the observed statement: precision sensitivity is a rounding-boundary property of the
   `(principal, n, rate)` triple, not a function of size; the oracle diverges at principal **4.00** on
   36 × 16.8 % and is identical at **50,000,000** on that same shape and at **87,654,321** on 6 × 7.0 %; and
   **all four MNT captures are p12/p19-identical**, so pass 3 supplies no evidence that Mongolian loan sizes
   are precision-sensitive. Cite `t21v2-probe2-oracle-out.txt`.
2. **Attach the environment-attestation block** to `capture-prod-raw.json` as a top-level `attestation`
   object, per plan §4.1: Fineract commit, image digest, the jar's `git.properties` `git.commit.id`, JVM
   string read inside the container, SHA-256 of the compiled sources and of the classpath entries, runtime
   `MoneyHelper.PRECISION`, per-capture tenant rounding mode, capture path (`Path A — embeddable seam`), and
   a UTC timestamp. Until it exists the plan's own rule makes these inadmissible, however sound the numbers.
3. **Emit `periodFromDate`, `feeAmount`, `penaltyAmount`** (and, cheaply, the plan-level
   `totalPrincipalAmount`, `totalFeeAmount`, `totalPenaltyAmount`, `totalOutstandingAmount`) and re-run.
   They exist on the oracle's objects; the shipped test asserts `periodFromDate`; without it no vector can
   catch a period-boundary error.
4. **Commit a pass-3 run recipe** as an executable script, with the seam byte-identity check as a
   **precondition step that fails the run** rather than a prose instruction, and with the log/JSON split
   built in.

**P1 — correctness of the record; do before pass 3 is cited by any downstream task.**

5. **Delete or rewrite `t21-probe-threshold.py` / `-output.txt` and `t21-probe-rederive.py`**, or prefix each
   with a retraction pointing at §9. As they stand they are on `main` and a later fire will reuse them.
   `t21-probe-invariants.py`'s `X2` must be replaced with the position-aware roll-forward (`A3` in
   `t21v2-invariants.py`) and its docstring corrected to say `X1`/`X2` are the author's own additions, not
   part of the six.
6. **Fix `.softhouse/tasks.json:188`**: pass 3 is **11** captures at `(19, HALF_UP)` plus **one** calibration
   at `(12, HALF_UP)`, not "12 captures at PRODUCTION settings". Same note should say the six invariants were
   independently re-checked by T21, not merely claimed.
7. **Fix `.softhouse/RESUME.md:34`**: the threshold claim is now **tested and REFUTED**, not "unaudited".
   Replace it with the corrected statement from item 1.
8. **Fix T19-10 in the harness**: give `CurrencyData.inMultiplesOf` and `installmentAmountInMultiplesOf`
   separate fields in `Case`, in the model construction and in the emitted JSON. Then capture the
   `decimalPlaces == 0` multiples-of behaviour, which is the only multiples-of path Path A can reach and does
   move money: at MNT 5,000,000 / 18 × 18.5 % with `decimalPlaces = 0`, the oracle emits total interest
   **`763994`** at `inMultiplesOf = null` and **`764100`** at `inMultiplesOf = 100`, with all 18 periods
   differing (`t21v2-probe-oracle-out.txt` §B).
9. **Switch every `BigDecimal` emission to `toPlainString()`** and **print the top frames of the stack trace**
   on the error branch. Neither affects any pass-3 value (`A5` confirms), both are cheap.
10. **Record in `PASS3-REPORT.md`** (a) the `CurrencyData` input deviation from the shipped test
    (`("usd","usd",…)` vs `("usd","US Dollar",…,"$")`), non-load-bearing but undocumented; (b) that
    `P-03`'s `loanTermInDays = 182` is measured from the **schedule start**, not the disbursement date
    [`ProgressiveLoanInterestScheduleModel.java:200-207`], so no later reader mistakes it for a defect;
    (c) that `P-03`'s emission order is caused by `processDisbursements` running at the top of the period
    loop [`ProgressiveLoanScheduleGenerator.java:116-145`].
11. **Add the `36 × 16.8 %` small-principal shape to the capture plan.** It is now a demonstrated
    discriminator for the precision seam at principals as small as 4.00 — far cheaper and far more sensitive
    than the 87-million probes the corpus currently relies on.

---

## 11. What may and may not be promoted

**May be promoted to the parity corpus once the P0 items are done — the eleven `(19, HALF_UP)` captures:**
`P-00`, `P-01`, `P-02`, `P-02b`, `P-03`, `P-04f`, `P-04t`, `P-MNT-5M`, `P-MNT-1M2`, `P-MNT-50M`,
`P-MNT-4M999`. Each reproduces byte-for-byte, satisfies all six invariants integer-exact, and is
independently re-derived from the pinned source to the minor unit by a model I wrote. `P-01` additionally
carries a cross-harness corroboration (byte-identical to pass-1 `D-01-p19`).

**May NOT be promoted as a parity vector, ever:** **`P-CAL`.** It runs at `(12, HALF_UP)`, a precision
production never runs. It is the rig calibration and must be stored — if at all — tagged
`calibration`, alongside its provenance (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92`). The
report labels it correctly; `tasks.json:188` does not (P1-6).

**May not be promoted yet, all eleven, until the P0 list is closed.** Not because a number is doubted — I
doubt none of them — but because the capture plan's §4.1/§4.2 admissibility rules are unmet: no attestation
block, three mandated per-period columns missing, no executable run recipe. They are **audited observations**
of the reference oracle at production settings: the best evidence this program has, and not yet vector-store
entries.

**Nothing here licenses:**

- **any conclusion about `installmentAmountInMultiplesOf` or `daysInYearCustomStrategy` from pass 3.** Both
  are provably discarded by the Path A seam at `(19, HALF_UP)` (§7); the eleven candidates have **zero**
  discriminating power over them. A conformance run that passes on this corpus has said nothing about either.
- **any "small loans are safe" simplification** in the Go port. Refuted at principal 4.00 (§6.2).
- **treating "vectors pass" as "the contract is covered."** The seam honours 17 of 19 components. That is a
  defect in the *rig*, and DEC-1 must not be frozen in a form that assumes seam-captured vectors cover the
  contract's input domain.
- **ratifying or amending DEC-1, or anything under `docs/adr/`.** G-1 remains a `user` CONTRACT gate; nothing
  in this audit is stored in contract-shaped form, and no Go was written.
- **cutover of anything.** Unchanged, and not in question here.

---

## 12. Provenance and non-negotiables check

| check | result |
|---|---|
| Money as integer minor units | every value in this audit was parsed to integer minor units before comparison; **no floating-point appears in `Capture3.java`, in my re-derivation, or in my invariant checker** (`Decimal`/`BigDecimal` only) |
| Prohibited DB engines | classpath carries `postgresql-*.jar` only; no `ojdbc`/`oracle.jdbc`/mysql/mariadb anywhere; **this seam opens no database connection at all** — `Capture3.java` imports no JDBC/JPA type and stderr is 0 bytes |
| PostgreSQL-only | unaffected; `fineract-db-1` is `postgres:18.3`, the only DB container running |
| "oracle" | used throughout in the **test-oracle** sense (the pinned Fineract reference implementation). Oracle Database appears nowhere |
| MNT | ISO 4217 numeric 496, minor unit 2 — all four MNT captures use `currencyDecimalPlaces = 2` |
| Tenant parameters | every capture sets `tenantRoundingModeValue = 4` (HALF_UP) and the emitted `ambientMoneyHelperMathContext` reads `precision=19 roundingMode=HALF_UP`, matching `MoneyHelper.java:35,91-93` |
| Contract-shaped storage | none produced; this audit writes only review/handoff prose and probe scripts |
