# T44 — INDEPENDENT AUDIT of the T40 charges capture set

**Leg:** `.softhouse/capture/charges/` (task T40, 21 captures + 1 refusal, Path B running oracle).
**Handoff under audit:** `.softhouse/handoff/T40-charges-capture.md`.
**Auditor write surface:** `.softhouse/capture/audit-t44/charges/` — nothing outside it was written.
**Oracle:** live `fineract-fineract-1` (`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`)
+ `fineract-db-1` (postgres:18.3), tenant `gerege`. "Oracle" throughout means the **Fineract reference
implementation**; Oracle Database is prohibited and appears nowhere in this audit except inside grep
patterns that assert its absence. PostgreSQL is the only engine touched.

---

## VERDICT — **ACCEPTED WITH REQUIRED CHANGES**

T40's numbers are sound. I re-derived every headline claim independently, re-issued 11 requests against the
live oracle and got byte-identity on all 11, and re-ran C1–C10 from my own implementation with results
identical to T40's cell for cell. The capture set is a real observation of the pinned oracle at
`MathContext(19, HALF_UP)` and it closes a genuine corpus blind spot.

Six findings require action before any of it is promoted. Two of them (A-2, A-3) are **material to how a Go
port would be graded**: one of T40's `[VERIFIED: file:line]` citations points at a line that says the
opposite of what is claimed, and the whole capture set carries an unstated confound — the money observed
came from the **request** `amount`, not from the charge definitions T40 attested with per-row SHA-256.

---

## Findings

### A-1 (P1) — the T42 rule-4 WIRING citation is entirely absent

T42's 8-point attestation rule (`.softhouse/reference-oracle.md`, "Which `MathContext` governs") says of
Path B: *"**Yes** — it *is* the threaded context. **Cite the wiring; never leave it implicit.**"* The wiring
is `LoanScheduleAssembler.java:753, :777, :797` and `LoanScheduleGeneratorServiceImpl.java:44`.

`grep -rn "LoanScheduleAssembler\|LoanScheduleGeneratorServiceImpl\|wiring\|threaded\|ambient"` over the
whole of `.softhouse/capture/charges/` **and** the T40 handoff returns **zero hits**
[VERIFIED: grep, exit 1, no output]. `out/attested/attestation.json` names its readings
`effective_math_context` with sources `"MoneyHelper.PRECISION read by javap…"` and `"MoneyHelper init line
emitted by THIS JVM run"` — both **ambient** readings, neither labelled as such, with no statement that on
Path B the ambient object *is* the one handed to `generate(mc, …)`.

T42 recorded that T36 "needs only the wiring citation added". T40 inherited T36's attestation generator and
inherited the omission. **Required change:** `attestation.json` gains an explicit
`mathcontext_wiring` block naming the four sites and the two contexts by T42's names, and the handoff §10
says which context it is reading.

### A-2 (P1) — `AbstractCumulativeLoanScheduleGenerator.java:504` does not say what the handoff claims

Handoff §7 D-1: *"The cumulative (non-progressive) generator does add them
[VERIFIED: `AbstractCumulativeLoanScheduleGenerator.java:504`], so **the two generators disagree**."*

I opened that line. It is
`scheduleParams.addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment));`
inside `updatePeriodsWithCharges`, operating on `nonCompoundingCharges` — i.e. **the separated-path site
that the progressive generator has too, verbatim, at `ProgressiveLoanScheduleGenerator.java:486`**
[VERIFIED: both files opened side by side; the two method bodies are the same shape]. Cited as evidence
that the generators *disagree*, `:504` is the one site where they **agree**.

The conclusion is nevertheless **true**, at a different line: the cumulative main loop does
`scheduleParams.addTotalRepaymentExpected(totalInstallmentDue)` at
[VERIFIED: `AbstractCumulativeLoanScheduleGenerator.java:392`], and `totalInstallmentDue` is
`currentPeriodParams.fetchTotalAmountForPeriod()` [VERIFIED: `:352`] =
`principalForThisPeriod.plus(interestForThisPeriod).plus(feeChargesForInstallment).plus(penaltyChargesForInstallment)`
[VERIFIED: `ScheduleCurrentPeriodParams.java:144-145`]. The progressive main loop adds only
`principalDue.plus(interestDue, mc)` [VERIFIED: `ProgressiveLoanScheduleGenerator.java:137`].

**Severity P1 because D-1 is the finding that drove T41's ratified DEC-1 decision C-1**, and a reader
checking the one citation offered for its most consequential half would conclude the opposite.
**Required change:** replace `:504` with `:392` + `ScheduleCurrentPeriodParams.java:144-145` in the handoff
and anywhere D-1 is restated.

### A-3 (P1) — the observed money came from the REQUEST amount, not from the attested charge definitions

Handoff §3: *"`amount` is **mandatory** on every element of the loan application's `charges` array… Every
request therefore repeats the definition's amount as exact decimal text."* That framing says the repetition
is a redundant echo. It is not — **the request value is authoritative and the definition's `amount` column
is ignored**, for both percentage and flat charges:

| probe | request | definition (`m_charge`) | observed |
|---|---|---|---|
| **AP-5** | `{"chargeId": 4, "amount": 0.001875}` | charge 4 = **3.750000 %** | period-1 fee **0.41**, not 810.00 |
| **AP-6** | `{"chargeId": 1, "amount": 12345.67}` | charge 1 = **15000.000000** | disbursement fee **12345.67**, `totalFeeChargesCharged` **12345.67** |

[VERIFIED: `out/probes/AP-5-halfcent-tie-in-charge-raw.json`, `out/probes/AP-6-flat-amount-override-raw.json`,
both HTTP 200 from the live oracle; definitions read from `m_charge` by `psql`.]

Consequence: `attestation.json`'s `charges_as_persisted` block — 12 rows each with a
`persisted_row_sha256` — is load-bearing provenance for `charge_time_enum`, `charge_calculation_enum` and
`is_penalty`, and is **not** load-bearing for a single money value in the set. And because T40 always made
the two equal, **no capture in the corpus can distinguish "the definition governs" from "the request
governs"**. A Go port that read the definition's amount would pass all 21 captures and be wrong.
**Required change:** the admissibility record states that the request bytes carry the charge amount, and
each vector's fixture is the request, not the definition row.

### A-4 (P1) — C5 is not an invariant; carried forward it becomes an assertion DEC-1 §9 forbids

C5 is stated as `totalRepaymentExpected == Σ totalDueForPeriod`. T41's ratified decision C-1
(`.softhouse/handoff/T41-dec1-v8.md`) obliges that *"no adapter, harness or conformance check may assert it
equals the sum of the rows"*.

Judged carefully, and in T40's favour on the facts: **C5 *failing* is exactly what produced D-1**, T40 ran
before T41 decided, and `bin/invariants.py` is demonstrably failable *because* C5 fails. As a
**discrimination probe** C5 is the single most valuable instrument in the set. As an **invariant** it is
wrong about the oracle, and its PASSes carry no information — the 6 captures where it passes pass for three
unrelated reasons (no charge landed at all: FC-17, FC-20; disbursement-only: FC-01, FC-03; separated-path
only: FC-19, FC-21), so a green C5 says nothing whatever about the port.

**Required change:** C5 must be relabelled a discrimination probe and must record the observed signed delta
`TRE − Σ rows` per capture (my `out/RECOMPUTE.md` §D-1 table has it: 0 on 6 captures, −543,706 to
−5,190,000 minor on the other 15) instead of PASS/FAIL. `bin/invariants.py` **must not** ship as the
conformance harness for a promoted charges corpus with C5 in it: a *correct* Go port, discarding
`totalRepaymentExpected` per DEC-1 C-1, would fail 15 of 21.

### A-5 (P2) — §11's arithmetic proof that no half-cent tie exists is FALSE, and I found one

Handoff §11: *"I looked for [a tie] against period 1's interest (21,600.00) and **proved arithmetically that
none exists at that base**: a tie needs `216 × p` to end in `…5` at the third decimal, and `216p` is even
for every terminating decimal `p`."*

`216 × p` is a decimal, not an integer; the parity argument does not apply to it. Ties exist. The smallest
family: write `p = m/10^n`; `charge × 1000 = 216000·m/10^n = 2^(6−n)·3^3·5^(3−n)·m`, which is odd-and-
divisible-by-5 for `n = 6`, `m = 125j`, `27j ≡ 5 (mod 10)`. `j = 15` gives `p = 0.001875 %` and
`charge = 0.405` exactly, with an **even** preceding cent digit — so it separates the modes.

Observed live on the corpus's own loan shape, product 1, period 1 [VERIFIED:
`out/probes/AP-5-halfcent-tie-in-charge-raw.json`, HTTP 200]:

```
"period":1, … "interestDue":21600.00, "feeChargesDue":0.41 …
```

`0.405 → 0.41` is **HALF_UP**; HALF_EVEN would give `0.40`. This is the behavioural rounding-mode canary
*inside the charge arithmetic* that T40 declared impossible at that base, obtained **without creating any
charge definition** (the request `amount` governs — finding A-3). §11's `TO_BE_CAPTURED` verdict was the
right call; its stated reason is wrong and would have told the next task not to look.

### A-6 (P2) — published tables silently re-scale the disbursement-row money; no T40 tool can see scale

The disbursement pseudo-period serialises its charge fields at the **scale of the underlying `BigDecimal`,
which varies by charge calculation type**, while instalment rows are 2-dp [VERIFIED, raw bytes]:

| capture | raw text in `periods[0]` |
|---|---|
| control B-01 | `"feeChargesDue":0` |
| FC-01 (FLAT) | `"feeChargesDue":15000` |
| FC-03 (PERCENT_OF_AMOUNT) | `"feeChargesDue":14814.000000` |

The handoff prints these as `15000.00`, `14,814.00` and `0.00`. `bin/fullcell.py`'s `d2()` formatter and
its `minor()` = `int(v*100)` comparison both normalise scale away, as does `bin/invariants.py` and as does
my own recomputation — **the entire T40 toolchain is blind to response scale**, and only the SHA-256
digests are not. For a set whose admissibility rests on byte-identity this matters: a Go adapter emitting
`14814.00` there is byte-different from the oracle. **Required change:** record the scale-passthrough as an
observed fact of the endpoint; do not let a promoted vector be graded only through minor-unit
normalisation.

### A-7 (P2) — the run recipe hard-codes an ephemeral worktree path

15 of the 19 files in `bin/` hard-code `W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513`
— T40's own per-fire worktree [VERIFIED: `grep -rl`]. That directory happens still to exist today, so the
scripts run; the moment softhouse prunes it the entire shipped recipe breaks, including `bin/capture.sh`,
`bin/control.sh`, `bin/lib.sh`, `bin/run-preconditions.sh` and all three analysis tools. Derive the root
from the script location instead.

### A-8 (P2) — two ambient witnesses presented as two rows (the T37 shape), though rule 6 is satisfied

Handoff §1 lists `c_configuration.rounding-mode = 4` and "mode in force this JVM run: HALF_UP (MoneyHelper
init line)" as separate assertions. They are not independent: the log line is `MoneyHelper` reporting what
it read from that very row. This is the pattern T42 flagged in T37 §5 ("two independent witnesses… both
ambient, i.e. one witness counted twice"). **T40 does not actually rest on it** — it carries the half-cent
canary as a genuinely independent behavioural witness (rule 6 satisfied, see CLEAN below) — so this is
presentational, not evidential. Label the two rows as ambient/config echoes.

---

## What I re-ran, and what it showed

### 1. Live re-issue of 11 requests, byte-verbatim (`bin/rerun.sh`, `out/RERUN.txt`)

`2026-08-19T01:25:59Z`. CTRL-B-01 from `.softhouse/capture/pathb/req/` plus FC-01, FC-04, FC-05, FC-11,
FC-15, FC-17, FC-19, FC-20, FC-21, FC-22 from `.softhouse/capture/charges/req/`, plus XR-01.

**11 of 11 charge/control responses are byte-identical to the committed captures; XR-01 reproduced HTTP 403
with the identical body digest `1af1083d…c9d1805`.** Every digest matched, including
`713a3560…c062009` for FC-17 and FC-20. T40's determinism claim holds under a *fourth* independent issue,
seventeen hours after the original run and from a different worktree and harness.

### 2. Failing-configuration test of the precondition suite (`out/PRECOND-default.txt`)

`bin/preconditions.sh` copied into my directory (byte-identical to the committed file **and** to
`.softhouse/capture/pathb/t36/preconditions.sh` — all three `sha256 9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54`,
so §1's "T36's script copied byte-verbatim" is **true**) and run against tenant **`default`**:

```
EXIT=1     PRECONDITIONS BREACHED: 5. DO NOT CAPTURE.
  FAIL  tenant timezone_id = 'Asia/Kolkata'
  FAIL  c_configuration.rounding-mode = '6' in fineract_default … 6 is HALF_EVEN
  FAIL  schema_connection_parameters = 'serverTimezone=UTC&…' — must be empty
  FAIL  running JVM initialized tenant 'default' at a mode other than HALF_UP: … HALF_EVEN
  FAIL  rounding-mode canary returned HTTP 404, not 200
```

**The suite is genuinely failable, exits non-zero, and names each breach — including via the behavioural
canary.** 16 PASS / 5 FAIL out of the 21 assertions; the committed `out/preconditions-T40.txt` shows 21/21
PASS on `gerege`. This is the strongest single clean result in the audit.

### 3. Five live discrimination probes (`bin/mkprobes.sh`, `bin/runprobes.sh`, `out/PROBES.md`)

Built by pure text substitution on committed request files; no JSON parse, no float. All HTTP 200.

| probe | charge | due date | result |
|---|---|---|---|
| **AP-1** | 11 (PCT_OF_INTEREST, SDD) | 20 Jan 2026, strictly inside period 1 | **lands in period 1**, 5,437.07 |
| **AP-2** | 11 | 01 Feb 2026 = p1 dueDate = p2 fromDate | **period 1** (digest identical to AP-1) |
| **AP-3** | 11 | 01 Apr 2026 = p3 dueDate = p4 fromDate | **period 3** |
| **AP-4** | 5 (PCT_OF_AMT+INT, instalment) on product 2 (`multiplesOf 100`) | — | base does **not** separate; see blind spots |
| **AP-5** | 4 with request amount `0.001875` | — | period-1 fee **0.41** from an exact `0.405` tie |

**AP-1/2/3 close T40's own `[UNVERIFIED]` item — in T40's favour.** T40 wrote it had not probed a separated
charge on an interior boundary and could not tell "period-1 lower bound only" from "the whole first period
is lost on the separated path". AP-1 and AP-2 land in period 1 and AP-3 in period 3, so the separated path
uses `(fromDate, dueDate]` for **every** period including period 1, and the **only** date it loses is
exactly period 1's `fromDate` (= the disbursement date). D-2b's scope is now observed, not inferred, and
T40's stale-`isFirstPeriod()` mechanism is confirmed.

### 4. Independent recomputation (`bin/audit_recompute.py`, `out/RECOMPUTE.md`)

Written from the stated definitions; `bin/invariants.py` was neither read for logic nor imported. Exact
`Decimal` (`parse_float=Decimal`), integer minor units, HALF_UP implemented as integer division — no float
is constructed anywhere.

**My C1–C10 table is identical to `out/INVARIANTS.md` cell for cell**: C1,C2,C3,C4,C6,C7,C8,C9,C10 PASS
21/21; **C5 FAIL on the same 15 captures, by name.**

My all-leaf flatten (336 leaves, dates as three leaves each) reproduces T40's moved-leaf counts **exactly**
on all 21 captures — 9, 80, 9, 80, 80, 8, 8, 80, 80, 8, 8, 7, 7, 8, 113, 8, **0**, 9, **0**, 9, 80 — and
`336 − 286 = 50 = 25 date arrays × 2`, which is precisely `fullcell.py` collapsing each date list to one
leaf. So T40's "286 leaves" **is** every leaf; there is no hidden coverage gap there.

### 5. Source citations opened in `/Users/buv/fineract` (read-only, no Gradle)

`ProgressiveLoanScheduleGenerator.java` `:116-145`, `:125-140`, `:137`, `:143`, `:154`, `:367-382`,
`:433-452`, `:454-468`, `:479`, `:483`, `:486`, `:492-504`; `LoanScheduleParams.java` `:211`, `:246`,
`:533-535`; `LoanCharge.java:371-373`; `LoanRepaymentScheduleProcessingWrapper.java:251-254`;
`LoanChargeValidator.java:59-67`; `AbstractCumulativeLoanScheduleGenerator.java:504`.

**All say what the handoff claims except `AbstractCumulativeLoanScheduleGenerator.java:504` (finding A-2).**
Two smaller notes, neither a finding on its own: a bare `` `:143` `` in §7 D-2b follows a
`LoanScheduleParams.java:533-535` citation but actually resolves to
`ProgressiveLoanScheduleGenerator.java:143` (LoanScheduleParams:143 is
`this.compoundedInLastInstallment = Money.zero(...)`); and §7's "the method body is `addLoanCharges`,
`addTotalFeeChargesCharged`, `addTotalPenaltyChargesCharged`, and nothing else" also elides the two
`cumulative*ChargesDueWithin` calls at `:372-377` — the *substance* (no `addTotalRepaymentExpected`) is
correct.

### 6. Live database state

```
m_charge 12 | m_loan 0 | m_loan_charge 0 | m_product_loan 16      (fineract_gerege, psql)
```
All 12 rows match §3's table exactly — id, name, `charge_time_enum`, `charge_calculation_enum`, `amount`,
`is_penalty`, `is_active`, `currency_code MNT`, `charge_applies_to_enum 1`, `charge_payment_mode_enum 0`.
Unchanged by my 17 POSTs: `calculateLoanSchedule` persists nothing, re-confirmed. **I created nothing —
no charge, no product, no tenant, no schema object, no id to record.**

---

## Checked and found CLEAN (clean checks are evidence too)

1. **Every published number I traced is observed or transcribed.** I spot-checked **>60** numbers across
   §§4–9 (`out/SPOTCHECK.txt`): the entire 13-row × 11-column FC-01 table including `loanTermInDays 365`
   and all five plan totals; FC-02's Q1 table; FC-15's whole Q6 table including the 8,700.00 period-3
   penalty, 45,000.00 fee total and 21,900.00 penalty total; all twelve FC-09 fees; all twelve FC-04 fees;
   FC-05's single distinct value 1,383.66; the 14,814.00 / 5,437.06 / 5,437.07 / 16,603.88 / 16,603.92
   pair-gaps; every `totalRepaymentExpected` in the §7 D-1 table; FC-11's `periods[0]` zero and period-1
   9,000.00. **Every one is a raw JSON leaf in `out/fc/`. Zero synthesised values found.**
2. **Q5 recomputed from first principles, independently.** All seven percentage bases reproduce exactly
   under integer-minor-unit HALF_UP: 1.2345 % × whole principal = 1,481,400 minor (FC-03, FC-10);
   0.5 % × each period's `principalDue` — all 12 match (FC-09); 3.75 % × each period's `interestDue` — all
   12 match, sum 543,706 (FC-04); 3.75 % × whole-term interest = 543,707 single rounding (FC-19);
   1.2345 % × each period's principal+interest — all 12 match, sum 1,660,392 (FC-05);
   1.2345 % × (principal + whole-term interest) = 1,660,388 (FC-21). **The rounding-locus claim is real**:
   543,706 ≠ 543,707 and 1,660,392 ≠ 1,660,388 are genuine one- and four-minor-unit separations.
3. **D-2a and D-2b byte-identity verified by my own SHA-256**, four ways: FC-17 and FC-20 in `out/fc/`, and
   again in `out/attested/`, and again on my live re-run — all `713a3560…c062009`, equal to the control and
   to `out/attested/CTRL-B-01-raw.json`.
4. **Determinism across all three committed issues**, my own digests: `out/fc/`, `out/fc-rerun/` and
   `out/attested/` agree on **21 of 21**, zero mismatches — plus my fourth issue (above).
5. **T42 rule 6 (behavioural canary) is satisfied.** `out/attested/canary-halfcent-raw.json` really contains
   `"interestOriginalDue":20925.05` on a period-1 principal of 1,162,502.50; `1,162,502.50 × 0.018 =
   20,925.045` exactly, so `20925.05` is HALF_UP and `20925.04` would be HALF_EVEN. It genuinely
   discriminates. The failing-configuration run (§2 above) shows the same canary firing as a FAIL.
6. **The control is not a variable.** T40's four control captures reproduce the committed Path B corpus, and
   my own re-issue of `calc-B-01-baseline.json` returns the identical digest.
7. **`bin/preconditions.sh` is byte-verbatim T36's** — three-way SHA-256 match, as §1 claims.
8. **No float, no prohibited engine, no prohibited pattern.** `out/SELFCHECK.txt`'s ten assertions match
   what I see in the tree: `fullcell.py`, `feecols.py`, `invariants.py` all force `parse_float=Decimal`;
   `attest-t40.py` forces `parse_float=str`; the tokens `ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql.cj`,
   `mariadb`, `go-sql-driver` occur only inside grep patterns asserting absence, and every such assertion
   observed 0 hits on the live container. No `first_name`/`last_name`; no insured/protected/guaranteed
   language; zone ids only, no hard-coded offset. My own tools are float-free by the same rule.
9. **The refusal is filed as a refusal.** XR-01 is HTTP 403, is excluded from the capture count, and is not
   in `out/fc/`; I reproduced it live.
10. **"286 leaves" is every leaf** — arithmetic in §4 above.
11. **Q1/Q2 hold under my own re-derivation.** `totalInstallmentAmountForPeriod` and the principal/interest/
    outstanding columns are identical to the control on all 21 captures (C8/C9 PASS 21/21 in *my*
    implementation); principal amortises to zero on all 21 (C6).
12. **Q4's interval rule holds and is now over-determined**, with AP-1/AP-2/AP-3 added to FC-07/11/12/13/14/16.
13. **The scope discipline is intact.** Nothing was promoted, nothing is contract-shaped, `docs/adr/**` was
    not touched, and the artefacts are raw HTTP bodies plus provenance, exactly as claimed.

---

## Admissibility verdict

**Admissible as RAW OBSERVATIONS today.** Admissible as **parity vectors once G-1 closes**, subject to A-1
through A-4 being applied, and only under these terms:

* **The vector is `(request bytes → response bytes)`.** Because of A-3 the charge amount lives in the
  request, not in the definition; a vector that carries only a `chargeId` is under-specified.
* **`totalRepaymentExpected` must be discarded**, per T41 decision C-1. **C5 must not ship as a conformance
  assertion** (A-4) — a correct port fails it on 15 of 21.
* **17 of the 21 captures are distinct.** FC-13≡FC-12, FC-14≡FC-11, FC-16≡FC-11, FC-20≡FC-17≡control.
  The four duplicates are worth keeping as *inputs* (different requests, same expected output — that is
  precisely the discrimination) but they add no output coverage.
* **FC-17 and FC-20 are admissible only as explicitly-labelled NEGATIVE vectors.** They are byte-identical
  to the zero-charge control, so **an adapter that ignored the `charges` array entirely would pass both**.
  They can never be cited as evidence that a port handles charges; they assert only "this input must
  produce the zero-charge output", which is exactly the oracle defect D-2a/D-2b. Whether the port
  reproduces the drop or rejects the input is a design decision that belongs in `gates.md` before either is
  promoted — T40 says so and it is right.

### Blind spots — what this corpus CANNOT distinguish

1. **One loan shape, full stop.** All 21 captures share a single
   `(principal, total interest, term days, instalments)` tuple: `(120,000,000 minor, 14,498,847 minor, 365,
   12)` [VERIFIED: `out/RECOMPUTE.md`]. Product 1, PROGRESSIVE, monthly, disbursed 01 Jan 2026. Nothing here
   grades charges against: non-monthly frequencies, multi-year terms, grace periods, down payments,
   multi-disbursement, `installmentAmountInMultiplesOf`, the leap-year `daysInYear` strategies that B-03/B-04
   exist to probe, or the 360-period regime where T42 showed threaded precision 19 vs 12 separates. A port
   could get every date-dependent charge rule wrong outside this one calendar and pass 21/21.
2. **No rounding-mode discrimination inside the charge arithmetic.** I searched every percentage rounding in
   the whole set for an exact half-unit tie: **0 of 39** [VERIFIED: `out/RECOMPUTE.md`]. Every committed
   charge amount lands where HALF_UP and HALF_EVEN agree. The corpus's only mode canary is a *different*
   loan shape on the interest path. My AP-5 (`0.001875 %` → `0.405` → `0.41`) supplies the missing one and
   should be captured properly.
3. **"Period principal + interest" vs "the EMI" is not separated by any observed shape.** I tried: AP-4 puts
   the instalment PCT_OF_AMOUNT_AND_INTEREST charge on product 2 (`multiplesOf 100`), and the two candidate
   bases still agree on **0 of 12** periods. The question is settled only by transcription
   (`ProgressiveLoanScheduleGenerator.java:437-443` uses `principalInterestForThisPeriod`), not by
   observation. A shape where EMI ≠ P+I is `TO_BE_CAPTURED`.
4. **"Definition amount" vs "request amount" is not separated** by any of the 21 (A-3); AP-5/AP-6 separate it.
5. **Response decimal scale is ungraded** by every T40 tool (A-6).
6. **Unexercised, as T40 states**: `OVERDUE_INSTALLMENT` (9) — the operationally most important penalty type;
   `TRANCHE_DISBURSEMENT` (12); `PERCENT_OF_DISBURSEMENT_AMOUNT` (5); `minCap`/`maxCap`; `taxGroupId`;
   `glAccountId`; `chargePaymentMode = ACCOUNT_TRANSFER`; `feeFrequency`/`feeInterval`; waiver, payment and
   `getDueAmounts`; the entire **cumulative** generator; `Asia/Hovd`. All `TO_BE_CAPTURED`.
7. **Nothing here observes a persisted loan.** C4 (`feeChargesOutstanding == feeChargesDue`) is true only
   because nothing has been paid; it is not an invariant of the domain.

---

## Unverified

* **`[UNVERIFIED]` — that A-3's override behaviour is uniform across all six charge calculation types.** I
  observed it for PERCENT_OF_INTEREST/INSTALMENT_FEE (AP-5) and FLAT/DISBURSEMENT (AP-6). I did not probe
  PERCENT_OF_AMOUNT, PERCENT_OF_AMOUNT_AND_INTEREST, or the SPECIFIED_DUE_DATE variants, and I did not read
  the deserialisation source. The two witnesses are enough to void the "redundant echo" framing; they are
  not enough to state a general rule.
* **`[UNVERIFIED]` — that AP-5's `0.001875 %` charge would be *accepted as a charge definition*.** I proved
  the arithmetic tie and observed the oracle answer `0.41` through the request-amount path. `m_charge.amount`
  is `numeric(19,6)` so the value is representable, but I did not create the row and did not test whether
  charge creation validates a percentage that small. I deliberately created nothing.
* **`[UNVERIFIED]` — that the scale-passthrough in A-6 is driven by the charge calculation type rather than
  by the request literal's own scale.** FC-01's request says `"amount": 15000` and the response says
  `15000`; AP-6's says `12345.67` and the response says `12345.67`; FC-03's says `1.2345` and the response
  says `14814.000000`. The percentage case clearly is not echoing the request scale, but I did not isolate
  which BigDecimal supplies the scale.
* **`[UNVERIFIED]` — that AP-1's and AP-2's shared digest means the charge landed in period 1 rather than
  the two documents coinciding for another reason.** Same caveat T40 raised for FC-11/14/16. Byte identity
  of the full response plus the period-1 `feeChargesDue` of 5,437.07 in both is strong, but I did not build
  a case that separates "same period" from "same everything".
* **`[UNVERIFIED]` — that no leaf outside my 336 exists.** My flatten walks the whole document, but a
  response shape with additional keys (a persisted loan, a different product) could carry leaves neither
  tool has ever seen.
* **`[UNVERIFIED]` — whether D-1 and D-2 are Fineract *bugs* or intended.** Same position as T40: the
  behaviour, the source path and the generator disagreement are verified; the word "defect" is a reading.
  With A-2 corrected, the disagreement between the two generators' main loops is now properly evidenced.
* **Note so it is not mistaken for a violation:** the strings `ojdbc`, `oracle.jdbc`, `:1521`,
  `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql` appear in this document and in
  `bin/preconditions-COPY.sh` only as **detection patterns asserting absence**. Every such assertion
  observed 0 hits. "Oracle" means the Fineract reference implementation throughout.

---

## Files in this audit directory

```
AUDIT-CHARGES.md                    this report
bin/audit_recompute.py              independent C1-C10 + leaf diff + Q5 + D-1 + blind-spot probe
bin/spotcheck.py                    provenance spot-check of §§4-9 published numbers
bin/rerun.sh                        live byte-verbatim re-issue of 11 committed requests
bin/mkprobes.sh                     builds AP-1..AP-4 by pure text substitution
bin/runprobes.sh                    issues AP-1..AP-4 against the live oracle
bin/analyse_probes.py               exact-Decimal analysis of the probes
bin/preconditions-COPY.sh           T36/T40's script, copied verbatim, run against tenant `default`
req/calc-AP-1..AP-6*.json           the six probe requests, as sent
out/RECOMPUTE.md                    independent recomputation output
out/SPOTCHECK.txt                   raw leaves behind every spot-checked number
out/RERUN.txt                       live re-issue transcript with digests both sides
out/PROBES.txt, out/PROBES.md       probe transcript and analysis
out/probes/*.json                   the six raw probe responses
out/PRECOND-default.txt             the failing-configuration precondition run (EXIT=1, 5 breaches)
```
