# T27 — independent review of T25's capture-corpus corrections (promotability audit)

**Reviewer:** T27, isolated worktree `/home/user/wt-T27`, branch `softhouse/T27-corpus-corrections-review`,
2026-08-18.
**Under review:** commit `f8b9d52` ("T25 (oracle-independent slice)…"), merged as `0c70c59`.
**Subject files:** `.softhouse/capture/PASS3-REPORT.md`, `PASS3-REPORT-shared.md`,
`.softhouse/capture/pathb/PATHB-REPORT.md`, `.softhouse/capture/out/t21-probe-*.py|.txt`,
`.softhouse/capture/pathb/t22-probe/{invariants.py,PROVENANCE-NOTE.md}`, `.softhouse/tasks.json`,
`.softhouse/handoff/T25-corpus-corrections.md`.
**Reference oracle source:** pinned Fineract at `/home/user/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(verified: `git log -1` matches, working tree clean).

> **NO LIVE ORACLE WAS REACHED BY THIS REVIEW.** No Fineract instance and no PostgreSQL is running in this
> sandbox. **No oracle value was synthesized, invented or extrapolated.** Everything below is either
> (a) read from an artifact already committed on `main`, (b) re-derived from the pinned Fineract **source**,
> or (c) produced by my own scripts operating on committed artifacts. Items that can only be settled by a
> fresh observation are listed in §7 and are not treated as settled.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

**Every correction T25 applied is CORRECT, not merely present.** I re-checked each one against the evidence it
cites rather than against T25's account of it, and each survived:

- All **sixteen** oracle numbers in the rewritten PASS3 "rounding-boundary, not size threshold" section appear
  in `t21v2-probe2-oracle-out.txt` with the same verdict — machine-checked, not eyeballed (§2.1).
- The two "fake PASS" defects are **genuinely repaired**, proved by mutation: I corrupted committed captures by
  one minor unit and both repaired checks now FAIL where they previously could not (§2.3).
- The Path B round-up→round-to-nearest correction is **right**, and I re-derived it from the pinned source and
  from an independently calibrated annuity model rather than trusting the prose (§3.1).
- The `tasks.json` count is **right**: 11 at `(19, HALF_UP)` + 1 calibration at `(12, HALF_UP)`, counted in the
  capture JSON (§2.4).
- The retraction banners are **unmissable** and correctly scoped — the *oracle* transcript
  `t21-probe-oracle.txt` was correctly left un-retracted (§2.2).

It is **not CLEAN** for three reasons, none of which voids a number:

1. **One required change was silently dropped.** T22 P1-12 (state the residual-absorption rule normatively) is
   absent from T25's DONE list *and* from its PARKED list. It is fully oracle-independent. T25's handoff claims
   nothing was silently dropped; that claim is false (§4.1).
2. **Several oracle-INDEPENDENT items were mis-parked as `oracle_unreachable`.** T22 P0-5, P1-8 (second half),
   P1-9, P1-11 (first half) and P1-14 (first half) need no oracle at all — I settled P1-9 and half of P1-8
   myself, here, from committed artifacts. Parking them tells the next fire they are blocked when they are not
   (§4.2).
3. **T25's own edits left three documents self-contradictory.** Both PASS3 reports and `PATHB-REPORT.md` now
   carry "CORRECTED by the T21/T22 independent audit" banners *and* still say **"NOT YET INDEPENDENTLY
   AUDITED"** in their status line; `PATHB-REPORT.md` still says the invariants "were not mechanically
   re-checked" when T22 re-checked ten of them on all four captures. `tasks.json:188` says "Pass 3 is NOT yet
   audited (T21)" in the same sentence-run that cites T21's findings (§4.3).

**Promotability: NOTHING may be promoted to the parity vector store today. Seven P0 items remain open**
(three T21, four T22). The corpus record is now *honest about the money*; it is not yet *admissible*.

---

## 1. What I ran

All under `/home/user/wt-T27`. My scripts live in `.softhouse/reviews/t27-probe/` and each carries a banner
saying it was not run against a live oracle.

```sh
git -C /home/user/fineract log -1 --format='%H %cI'   # 426a23544e8426a38ae43ae404670a0a7e85b9eb, clean
diff .softhouse/capture/PASS3-REPORT.md .softhouse/capture/PASS3-REPORT-shared.md   # exit 0

python3 .softhouse/capture/out/t21-probe-invariants.py .softhouse/capture/out/capture-prod-raw.json
python3 .softhouse/reviews/t21v2/t21v2-invariants.py   .softhouse/capture/out/capture-prod-raw.json

python3 .softhouse/reviews/t27-probe/t27_mutate.py          # mutation testing of both repaired checkers
python3 .softhouse/reviews/t27-probe/t27_verify_claims.py   # 40 mechanical claim checks, exit 0

cd nexus && go build ./... && go vet ./...                  # both exit 0 (no Go changed on this branch)
```

`t27_verify_claims.py` reports **40/40 PASS, 0 failures**. `t27_mutate.py` reports
**ALL REPAIRED CHECKS ARE GENUINELY FAILABLE**.

---

## 2. T21 items — per-item disposition

### 2.1 P0-1 — the refuted "size threshold" finding — **CORRECTLY APPLIED**

`PASS3-REPORT.md:50-78` (and its byte-identical twin). I did not read-and-agree: I parsed the committed
transcript `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt` into a lookup table and asserted each
`(shape, principal) → (p12, p19, verdict)` triple the new text asserts. **All sixteen confirmed**, including
every number the brief named:

| claim in the new text | transcript row | confirmed |
|---|---|---|
| diverge at principal **4.00** on 36 × 16.8 %, `1.13` vs `1.14` | row 1 | ✅ |
| diverge again at 59, 72, 340, 426, 6,940 | rows 2–6 | ✅ |
| **identical at 50,000,000** on 36 × 16.8 %, `13,995,886.40` both | row 7 | ✅ |
| **identical at 87,654,321** on 6 × 7.0 %, `1,798,283.07` both | row 12 | ✅ |
| identical at 43,811 and 131,432, diverge at 131,433 | rows 8, 9, 10 | ✅ (see RC-4) |
| the 87M divergence belongs to 18 × 18.5 %, `13,393,481.05`/`.04` | row 15 | ✅ |
| **all four MNT captures p12/p19-identical** (1.2M; 4,999,999; 5M; 50M) | rows 16, 14, 13, 7 | ✅ |

**No number is unconfirmable.** I also verified the generating program is committed
(`.softhouse/reviews/t21v2/T21v2Probe2.java`) and that it pins tenant rounding mode **4 (HALF_UP)**,
`Asia/Ulaanbaatar`, MNT 2 dp, `DAYS_30`/`DAYS_360`, `DECLINING_BALANCE`, start 2024-01-01 — so the transcript's
settings are readable from source and match what the text claims. Reading that source also **explains** the
131,433 row: the `IDENTICAL`/`DIFFERENT` verdict is a **full-schedule** string comparison
(`T21v2Probe2.java:63-66`), not a totals comparison. See **RC-4**.

Cross-corroboration T25 did not cite but which holds: the *earlier* oracle transcript
`.softhouse/capture/out/t21-probe-oracle.txt` §C independently shows `36 × 16.8 %` principal **4** DIFFERENT
and `6 × 7.0 %` principal 87,654,321 SAME. The refutation is doubly witnessed.

### 2.2 P1-5 — retraction of the defective scripts — **CORRECTLY APPLIED**

Five files carry unmissable banners (`t21-probe-threshold.py`, `t21-probe-rederive.py`,
`t21-probe-rederive2.py` and the three `-output.txt` companions). Each names the defect
(no EMI smoothing pass; `Money.copy(double)` misread as a multiply), cites `T21-capture-pass3-audit.md` §9,
gives the refuting oracle value, and points at the superseding model. A later fire cannot silently reuse them.

I confirmed the defect from the pinned source myself: `Money.copy(double)` at
`Money.java:220-222` is `copy(BigDecimal.valueOf(amount))` — it **replaces** the amount, so
`EmiAdjustment`'s right-hand side is `Money(floor(n/2))`, not `EMI × floor(n/2)`. The retraction is
substantively right, not just procedurally present.

**Correctly NOT retracted:** `.softhouse/capture/out/t21-probe-oracle.txt`. That file is an **oracle**
transcript produced by `src/T21Probe.java` in the pinned image, not an output of the defective Python model.
Retracting it would have destroyed real evidence. T25 got this boundary right.

### 2.3 P1-5 (second half) — `t21-probe-invariants.py` `X2` — **CORRECTLY APPLIED, AND PROVED FAILABLE**

The docstring now says, at lines 7-9 and 17, that **`X1`/`X2` are the author's own additions and are NOT among
the six invariants** — the misleading "the six invariants… Plus two extra checks of my own" framing is gone.
`X2` is now the position-aware roll-forward, and I diffed it line-for-line against the audit's `A3`
(`t21v2-invariants.py:76-86`): **identical logic**.

I did not stop at "it prints ALL PASS". I mutated committed captures by one minor unit
(`t27_mutate.py`, byte-level text edit, `Decimal` arithmetic, **no float constructed anywhere**):

| mutation | expected | observed |
|---|---|---|
| `P-01` 4th repayment `balance` `70206261.08` → `.09` | X2 must FAIL | `X2 = !!`, rc=1 ✅ |
| `P-03` DISBURSEMENT `principal` `100.00` → `100.01` | X1 **and** X2 must FAIL | `X1 = !!`, `X2 = !!`, rc=1 ✅ |
| `P-MNT-5M` 1st repayment `total` +0.01 | I4 and I5 must FAIL | `I4 = !!`, `I5 = !!`, rc=1 ✅ |
| control: retracted **naive** X2 on unmutated `P-03` | must still spuriously FAIL | FAILS ✅ |

The `P-03` mutation matters most: it proves the new `X2` was not simply *disabled* for the capture that used to
break it. The control proves the repair changed the *formulation*, not the data.

I also ran the auditor's own independent checker: `t21v2-invariants.py` reports `SIX-CLAIMED verdict: ALL PASS`
on all twelve, with `A2` (the naive/retracted formulation) violated on `P-03` only — exactly the audit's story.

### 2.4 P1-6 — `tasks.json` count — **CORRECTLY APPLIED**

Counted in `capture-prod-raw.json`, not in prose:

- `mathContextPrecision = 19` **and** `tenantRoundingModeValue = 4`: **11** captures — `P-00`, `P-01`, `P-02`,
  `P-02b`, `P-03`, `P-04f`, `P-04t`, `P-MNT-1M2`, `P-MNT-4M999`, `P-MNT-50M`, `P-MNT-5M`.
- `mathContextPrecision = 12`: **1** — `P-CAL`.
- 12 records total. `json.load` on the edited `tasks.json` succeeds; 29 tasks intact; the diff touches only the
  note string.

The corroborating claim is also true: `P-CAL` and `P-00` have **byte-equal `observed` objects** and their
inputs differ only in `mathContextPrecision` (12 vs 19) and the synthetic tenant id.

### 2.5 P1-7 — `RESUME.md` — **CORRECTLY SKIPPED**

`RESUME.md:38` already states the refutation with the right numbers, and `grep -ci unaudited RESUME.md` → **0**.
The orchestrator had rewritten it in `95f3be9`, before T25. T25's "already correct, no change" is truthful.

### 2.6 P0-2, P0-3, P0-4 — **STILL OPEN, correctly parked**

Verified in the artifact, not assumed:

- No `attestation` key anywhere in `capture-prod-raw.json` (top-level keys are `pass`, `harness`,
  `moneyHelperPrecision`, `captures`). **P0-2 open.**
- Period objects expose only `{dueDate, principal, type}` / `{balance, dueDate, interest, periodNumber,
  principal, total, totalOutstandingBalance, type}`. **`periodFromDate`, `feeAmount`, `penaltyAmount` are
  absent. P0-3 open.**
- No `.sh`/`.bash` under `.softhouse/capture/`. **P0-4 open.**

These genuinely need the oracle. Parking is correct.

---

## 3. T22 items — per-item disposition

### 3.1 P0-1 — round-up → round-to-nearest — **CORRECTLY APPLIED**

**From the pinned source.** `Money.roundToMultiplesOf(Money, Integer)` at `Money.java:159-161` delegates to the
three-arg overload at `Money.java:163-171`, whose body is

```java
amountScaled = amountScaled.divide(inMultiplesOfValue, 0, mc.getRoundingMode()).multiply(inMultiplesOfValue);
```

— a divide to **scale 0 under the tenant rounding mode**, i.e. round to the **nearest** multiple, not up.
`ProgressiveEMICalculator.safeRoundingForEMI` at `:1770-1776` carries the zero-guard exactly as the correction
states. **Both cited line ranges are accurate in the pinned checkout.**

**From the committed observation, plus an independently calibrated model.** I did not take `111,148.35` on
faith. I built the annuity EMI at `MathContext(19, HALF_UP)`, **calibrated it against the committed `B-01`
observation** (model `112,082.37` = observed `112,082.37`), then applied it to the round-down probe's request
(`req/calc-prounddown.json`: principal 1,190,000, 12 × 21.6 %/yr):

| | value | source |
|---|---|---|
| unrounded EMI | `111,148.35` | re-derived here, model calibrated on `B-01` |
| oracle's applied EMI, periods 1–11 | `111,100.00` | **observed**, `out-rounddown/rounddown-gerege-raw.json` |
| a ROUND-UP rule would give | `111,200` | arithmetic |
| round-to-NEAREST under HALF_UP gives | `111,100` | arithmetic |

`111,100.00 < 111,148.35`. **Round-up is refuted; round-to-nearest reproduces the observation.** I also
confirmed periods 1–11 share exactly one EMI and it is a multiple of 100. The correction is right.

### 3.2 P0-2 — captures ran at HALF_EVEN — **CORRECTLY APPLIED**

Both supporting facts verified from committed artifacts:

- **The mode is live on this path.** `out-modeprobe2/pmode2-default-raw.json` period 1 interest `20,925.04`
  vs `out-modeprobe2/pmode2-gerege-raw.json` `20,925.05` on the same input (principal 1,162,502.50). Exactly
  the pair the corrected caveat cites.
- **The four captures are mode-insensitive by re-observation, not assumption.** SHA-256 of
  `out/B-0{1,2,3,4}-*-raw.json` equals SHA-256 of `t22-audit/out-fresh-tenant/B-0{1,2,3,4}-raw.json`, all four.
  They also equal `t22-audit/out-rerun-default/` and `t22-probe/out/calc-B-0*-halfeven-raw.json` — **four
  independent reproductions, byte-for-byte**.

The corrected caveat's careful phrasing ("admissible at `(19, HALF_UP)` only on the strength of that committed
re-observation… still **not** production-settings parity vectors") is exactly right and should not be softened.

### 3.3 P1-7 — `FULL_LEAP_YEAR` ≡ field-unset — **CORRECTLY APPLIED**

Verified two ways, neither of them by reading T22:

- **By SHA-256 over committed captures:** `t22-audit/out-probe/p07-raw.json` (DAILY, ACTUAL/ACTUAL,
  `daysInYearCustomStrategy` **absent** from the request) is **byte-identical** to
  `out/B-03-diycs-fullleapyear-raw.json` (`892dd6f537ef…`). `B-04` (`FEB_29_PERIOD_ONLY`) differs.
- **From the pinned source:** `FULL_LEAP_YEAR` has **no branch anywhere in the calculation**. A repo-wide grep
  of `fineract-progressive-loan/src/main` and `fineract-core/src/main` finds the constant only in its own enum
  declaration and javadoc; every behavioural site tests `FEB_29_PERIOD_ONLY`
  (`ProgressiveEMICalculator.java:1349`, `:1373`, `:1506`). `DaysInYearType.java:81-86` is
  `getNumberOfDays`, which has no custom-strategy branch — the cited range is accurate.

The banner's "`B-04` is the only vector with any discriminating power over this field" is therefore correct.

### 3.4 P1-13 — the hard-coded `I5` — **CORRECTLY APPLIED, AND PROVED FAILABLE**

The pre-T25 file really did carry `verdict("I5", True, "per-period principal+interest+fee+penalty==total")`
(confirmed by `git show f8b9d52^:…/t22-probe/invariants.py`). It is now `verdict("I5", not i5_fail, …)`.

Mutation test on the committed `B-01-baseline-raw.json`:

| mutation | result |
|---|---|
| control, unmutated | `I5 … PASS`, `OVERALL: PASS`, rc=0 |
| 2nd `interestDue` `19971.32` → `19971.33` | **`I5 … (1 break(s)) **FAIL**`**, rc=1 ✅ |
| 4th `principalLoanBalanceOutstanding` +0.01 | `S2 … (2 break(s)) **FAIL**`, rc=1 ✅ |

**I5 can now fail, and does.**

`PROVENANCE-NOTE.md` is accurate on both clauses. I grepped every script in `t22-probe/` — `repro.sh`,
`capture.sh`, `mkreq.py`, `mkcalc.py` — and **none** touches the rounding mode (the only mode references are in
`rederive.py`, the offline re-derivation model). And its claim that the directory's outputs "re-hash
byte-for-byte to the committed corpus" is true: I checked all four SHA-256s.

### 3.5 P0-3, P0-4, P0-5, P0-6 — **STILL OPEN**

Verified in the artifact:

- No attestation sidecar anywhere under `.softhouse/capture/pathb/`. **P0-3 open.**
- `REPRODUCE.md` contains no `rounding-mode` precondition, no timezone assertion, no
  `schema_connection_parameters` assertion. **P0-4 open.**
- `REPRODUCE.md:76` still reads `-o out/B-$n-*-raw.json`; `%{http_code}` appears nowhere. **P0-5 open**
  (and see RC-3 — this one needed no oracle).
- The four committed captures are still the `default`-tenant ones. **P0-6 open.**

---

## 4. NEW errors and silent drops introduced or left by T25

### 4.1 RC-2 — **T22 P1-12 was silently dropped**

T22 §10 P1-12: *"State the residual-absorption rule normatively in the report (not only as a worked example):
`lastEmi = emi + (P + ΣI − Σemi)`, `ProgressiveEMICalculator.java:1202-1205`. The delta is signed."*

`T25-corpus-corrections.md` mentions T22 items 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14 — **never 12**. It is
in neither the DONE list nor the PARKED list. `PATHB-REPORT.md` still gives the rule only as a worked example
(`:68-70`: "period 12 is principal `109,888.23` + interest `1,977.99` = `111,866.22`"). The handoff's
"[UNVERIFIED] / missing-file notes" section asserts nothing was silently dropped; that assertion is false.

This item is **100 % oracle-independent**. I confirmed the rule from the pinned source:
`ProgressiveEMICalculator.java:1195-1205` computes
`diff = totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal + totalDueInterest − totalEMI`, then
`adjustedEmi = repaymentPeriod.getEmi().add(diff, mc)` — a **signed** adjustment, exactly as T22 states.

### 4.2 RC-3 — items mis-parked as `oracle_unreachable` that need no oracle

T25 parked T22 "P1 items 8, 9, 11, 14" with the reasoning that they "rest on probe captures", and parked P0-5
as "coupled to a re-run of the capture recipe on the oracle". **The probe captures are already committed.** I
settled these here, from `t22-audit/out-probe/`, with no oracle:

| relation | SHA-256 | what it settles |
|---|---|---|
| `p05` (SARP, `FULL_LEAP_YEAR`) ≡ `p06` (SARP, `FEB_29_PERIOD_ONLY`) | `ff92fc5dfb8e…` both | **P1-8**: DIYCS is inert under `SAME_AS_REPAYMENT_PERIOD` |
| `p07` (DAILY, ACT/ACT) ≠ `p08` (DAILY, 360/30) | `892dd6f5…` vs `ff92fc5d…` | **P1-9**: day-count moves a progressive schedule under DAILY |
| `p09` (SARP, 360/30) ≡ `B-01` (SARP, ACT/ACT) | `713a3560…` both | **P1-9**: day-count inert under SARP |

Similarly: P0-5 (rewrite `-o out/B-$n-*-raw.json` as explicit filenames; add `-w '%{http_code}'`) is a text edit
to `REPRODUCE.md`. P1-11's *first* clause and P1-14's *first* clause are pure record statements. Only their
capture clauses are oracle-bound.

Parking an unblocked item as `oracle_unreachable` is not a neutral error in this program: the driver skips
parked items until an oracle fire, so these would sit blocked for no reason.

*(T21 P1-10 and T22 P1-10 are different: T25 explicitly recorded them as deferred in its handoff. Those are
deferred-and-recorded, not lost. Confirmed.)*

### 4.3 RC-1 — T25's edits left three documents self-contradictory

This is the failure mode the brief warned about, in its mirror form: the section named by the review was fixed,
but the **status claims elsewhere in the same document** were not, and the fix made them contradictory.

| file:line | stale text | why it is now wrong |
|---|---|---|
| `PASS3-REPORT.md:5` and `PASS3-REPORT-shared.md:5` | "RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**" | line 52 of the same file says "**CORRECTED by T21 audit (2026-08-18), P0 item 1**" |
| `PASS3-REPORT.md:114-115` (both twins) | "pass 3 has not been independently audited" | T21 audited it: ACCEPTED WITH REQUIRED CHANGES |
| `PATHB-REPORT.md:5` | "RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**" | lines 72 and 104 cite the T22 audit by name |
| `PATHB-REPORT.md:128-130` | "**Not audited.** … Treat every number here as observed-but-unaudited." | same |
| `PATHB-REPORT.md:150-151` | "**Property invariants were not mechanically re-checked** on these four captures… That is audit work." | **factually false** — T22 checked ten invariants mechanically on all four plus six probes (`t22-audit/t22_invariants.py`) |
| `tasks.json:188` | "Pass 3 is NOT yet audited (T21)." and "NOT audited - T22 raised." | the **same note** now says "INDEPENDENTLY re-checked by the T21 audit" and "corrected per T21 audit P1-6" |
| `reference-oracle.md:202` | Path B "**not audited**" | stale |

None of these is a false *money* claim, so this is a required change and not a rejection — but a driver reading
"NOT YET INDEPENDENTLY AUDITED" cannot tell that a P0 list exists, and a reader of `PATHB-REPORT.md:150` is
told evidence is missing that in fact exists.

### 4.4 RC-4 — one corrected claim lost the annotation that makes it exact

`PASS3-REPORT.md:67-68` (and twin): *"…identical at 43,811 and 131,432, but **diverge at 131,433**."*

The transcript's verdict at 131,433 is `DIFFERENT`, but the two **total interest** figures are equal
(`2696.43` both). `T21v2Probe2.java:63-66` shows the verdict is a **full-schedule** comparison, so the
divergence is per-period. T21 §6.2's own table annotates it "**DIFFERENT** (per-period, totals equal)"; the
correction dropped that. Since the surrounding sentences quote total interest, a reader can be misled.

### 4.5 RC-5 — the sole cited evidence for the corrected PASS3 section is unattested

`PASS3-REPORT.md:55-56` now names `t21v2-probe2-oracle-out.txt` as the source of every number in the section.
That file is **17 bare data rows with no provenance header** — no image digest, no Fineract commit, no JVM
string, no `MoneyHelper.PRECISION` line — unlike its sibling `t21v2-probe-oracle-out.txt:1-3`, which prints all
three. The generating source `T21v2Probe2.java` **is** committed and pins the settings, so the claim is not
floating; but by the capture plan's own §4.1 rule the artifact is not attested. Worth one line on the next
oracle fire.

### 4.6 RC-6 — the round-down banner blurs observed vs re-derived

`PATHB-REPORT.md:78-79`: *"the unrounded EMI `111,148.35` becomes **`111,100.00`** — rounded DOWN. Committed
observation: `…/rounddown-gerege-raw.json`."* `111,100.00` **is** observed; `111,148.35` is **model-derived**
(T22 §"Re-derived digit-for-digit by my model"). I re-derived it independently and it is correct — but the
sentence reads as though both came from the capture, and T25's handoff claims "every number cited in a
correction is quoted from an artifact already committed", which is not true of this one.

Related: the banner's "at `(19, HALF_UP)`" attribution for that probe rests on the filename (`…-gerege-…`) and
T22's prose. There is no attestation sidecar to confirm it — which is precisely T22 P0-3. (It does not change
the conclusion: at `111,148.35` the nearest multiple of 100 is `111,100` under HALF_UP *and* HALF_EVEN.)

---

## 5. Required changes

**RC-1 (record honesty).** Fix the stale status claims listed in §4.3, at each `file:line` given there.
Replace `PASS3-REPORT.md:5` / `PASS3-REPORT-shared.md:5` with, e.g.:
`**Status:** RAW OBSERVED, **INDEPENDENTLY AUDITED by T21 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**;
three P0 admissibility items open (T21 §10 P0-2/3/4). No vector promoted to the store; no gate answered.`
and the Path B equivalent citing T22 and its four open P0s. Delete or correct `PATHB-REPORT.md:150-151`
outright — it is false. **After editing, re-assert `diff PASS3-REPORT.md PASS3-REPORT-shared.md` exits 0.**

**RC-2 (silent drop).** Apply T22 P1-12 in `PATHB-REPORT.md` Result 2: state the residual-absorption rule
normatively — `lastEmi = emi + (P + ΣI − Σemi)`, delta **signed** — citing
`ProgressiveEMICalculator.java:1195-1205` (re-verified in the pinned checkout). Oracle-independent; do it now.

**RC-3 (unpark).** Move T22 **P0-5**, **P1-8** (probe citations `TP5`/`TP6` + `LoanProduct.java:462-472`),
**P1-9** (whole item — the evidence is in §4.2 above), **P1-11** first clause, **P1-14** first clause out of the
`oracle_unreachable` parking list. Fix `REPRODUCE.md:76` (`-o out/B-$n-*-raw.json` → explicit filenames) and add
`-w '%{http_code}'` in the same edit.

**RC-4 (exactness).** `PASS3-REPORT.md:68` and twin: append T21 §6.2's own annotation — "…but **diverge at
131,433** (per-period; the two total-interest figures are equal at `2696.43`)".

**RC-5 (provenance).** On the next oracle-reaching fire, re-emit `t21v2-probe2-oracle-out.txt` with the
provenance header its sibling already prints (image digest, pinned commit, JVM string,
`MoneyHelper.PRECISION`, per-run tenant rounding mode), or attach a sidecar.

**RC-6 (observed vs derived).** `PATHB-REPORT.md:78-79`: say "**re-derived** unrounded EMI `111,148.35`"
(citing T22's model) and reserve "committed observation" for `111,100.00`. Correct the handoff's blanket claim
that every cited number is quoted from a committed artifact.

---

## 6. Promotability verdict

**Production setting is `(19, HALF_UP)`.** `MoneyHelper.PRECISION = 19` is a compile-time constant and
`getMathContext()` = `new MathContext(19, tenantRoundingMode)`
[`fineract-core/…/MoneyHelper.java:35, 91-93`]; `HALF_UP` = `RoundingMode` ordinal **4** is the ratified tenant
setting. **Any capture at precision 12 or 8 is a DISCRIMINATION PROBE, never a parity vector.** This is not
negotiable and is not softened below.

### Promotable to the parity vector store TODAY

**None. Zero captures.**

### Never promotable as a parity vector

| capture | why |
|---|---|
| `P-CAL` (pass 3) | runs at `(12, HALF_UP)`. Rig **calibration** only; store tagged `calibration` or not at all |
| `C-00`, `D-01`, `D-02`, `D-03`, `D-04`, `D-01-p8`, `D-01-mnt` (passes 1–2) | precision 12 or 8 — discrimination probes, per CLAUDE.md |

### Parity CANDIDATES, all still blocked

**Path A, eleven at `(19, HALF_UP)`:** `P-00`, `P-01`, `P-02`, `P-02b`, `P-03`, `P-04f`, `P-04t`, `P-MNT-5M`,
`P-MNT-1M2`, `P-MNT-50M`, `P-MNT-4M999`. Blocked by **T21 P0-2, P0-3, P0-4**.
**Path B, four:** `B-01`, `B-02`, `B-03`, `B-04`. Blocked by **T22 P0-3, P0-4, P0-5, P0-6**.
*(`D-01-p19` from pass 1 sits at production settings and is corroborated byte-for-byte by `P-01`, but it
inherits the same missing attestation and missing columns; it is not separately promotable.)*

### Outstanding P0 items — **7**

| # | item | oracle needed? |
|---|---|---|
| T21 P0-2 | environment-attestation block on `capture-prod-raw.json` | **yes** |
| T21 P0-3 | emit `periodFromDate`, `feeAmount`, `penaltyAmount` (+ plan totals) and re-run | **yes** |
| T21 P0-4 | executable pass-3 run recipe with the seam byte-identity check as a *failing* precondition | **yes** (to validate) |
| T22 P0-3 | machine-readable attestation sidecar per Path B capture set | **yes** |
| T22 P0-4 | `REPRODUCE.md` preconditions that fail the run (rounding-mode = 4, tz, `schema_connection_parameters`) | partly — write now, validate on oracle |
| T22 P0-5 | fix the `-o out/B-$n-*-raw.json` glob; capture `%{http_code}` | **no** — do it now (RC-3) |
| T22 P0-6 | re-point Path B at a production-settings tenant (`gerege`, Asia/Ulaanbaatar, HALF_UP) and re-capture | **yes** |

**One sentence for the driver: no capture may be promoted, and the standing rule that nothing is promoted
until the P0 lists are discharged is unchanged and correct.**

---

## 7. Needs a fresh oracle observation (next local, oracle-reaching fire)

1. T21 P0-2 — attestation values readable only inside a live container.
2. T21 P0-3 — re-run `Capture3.java` with the three mandated per-period columns.
3. T21 P0-4 — validate the pass-3 run recipe against the pinned image.
4. T21 P1-8 — capture the `decimalPlaces == 0` multiples-of behaviour once `CurrencyData.inMultiplesOf` is
   separated from `installmentAmountInMultiplesOf` in the harness.
5. T21 P1-9 — re-run after switching emissions to `toPlainString()` (no present value is affected; the
   artifact must simply reflect it).
6. T21 P1-11 — capture the `36 × 16.8 %` small-principal shape; it diverges at principal **4.00** and is the
   cheapest known precision-seam discriminator.
7. T22 P0-3 / P0-4 / P0-6 — Path B attestation, failing preconditions, and re-capture on the `gerege` tenant.
8. T22 P1-11 — capture a vector that forces the EMI re-adjust loop (`ProgressiveEMICalculator.java:1258-1308`,
   ≤ 3 iterations) to iterate. It is unvectored and can absorb a `multiplesOf` rounding difference entirely.
9. RC-5 — re-emit `t21v2-probe2-oracle-out.txt` with a provenance header.
10. RC-6 — an attestation confirming the round-down probe really ran at `(19, HALF_UP)` (the conclusion is
    mode-robust either way; the *record* is not attested).

**Oracle-INDEPENDENT and still open** (do these without waiting): RC-1, RC-2, RC-3, RC-4, and T22 **P1-14's
re-derivation** — nobody has yet rebuilt `B-03`/`B-04` from source through the DAILY cross-year
partial-period arm (`ProgressiveEMICalculator.java:1400-1414`, `calculatePeriodFractions` `:1550-1568`). That
is a from-**source** exercise and needs no running server; it remains the largest hole in the Path B evidence.

---

## 8. Non-negotiables scan (CLAUDE.md)

| check | result |
|---|---|
| **Money as integer minor units; no float in any money path** | ✅ Go module: only two `float` hits, both in doc comments *prohibiting* float (`nexus/…/contract.go:66`, `:1027`). All money comparison in this review is `Decimal`/integer minor units. My own `t27_mutate.py` mutates **raw JSON text** with `Decimal` arithmetic — it constructs no float |
| **Prohibited DB engines** (`ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`) | ✅ Repo-wide grep: **every hit is a prohibition statement in prose** (`CLAUDE.md:23`, `patterns.md:38-39`, `reference-oracle.md:77-85`, audit checklists). Zero declarations, drivers, dialects or URLs |
| **PostgreSQL only** | ✅ Path B provenance records `org.postgresql.Driver`, `jdbc:postgresql://db:5432/fineract_tenants`, PostgreSQL 18.3. Path A opens no DB connection at all |
| **"oracle" terminology** | ✅ used throughout in the **test-oracle** sense (the pinned Fineract reference implementation). Oracle Database appears only where it is named as prohibited |
| **No US payment rails / vendors** | ✅ `stripe`/`plaid`/`lithic`/`persona` appear only in prohibition text and in reviewers' clean-scan records |
| **MNT** | ✅ ISO 4217 numeric 496, minor unit 2; every MNT capture uses `decimalPlaces = 2`. Round-down probe request carries `"currencyCode": "MNT", "digitsAfterDecimal": 2` |
| **Tenant parameters** | ✅ all eleven pass-3 parity candidates carry `tenantRoundingModeValue = 4` (HALF_UP) at precision 19; `P-CAL` is correctly labelled calibration |
| **Names are three fields** | ✅ only prohibition comments (`contract.go:86-87`); Path B fixtures use `fullname` (the oracle's own schema, not a Gerege surface) |
| **Deposits never "insured/protected/guaranteed"** | ✅ zero hits in the Go module |
| **Time zones** | ✅ no hard-coded offset introduced. Path B's `default` tenant is `Asia/Kolkata` — recorded as a defect (T22 P0-6), not accepted |
| **Nothing promoted / no contract-shaped storage** | ✅ this review promotes nothing, ratifies nothing, and writes no Go |
| **Go module still sound** | ✅ `go build ./...` and `go vet ./...` both exit 0 (no Go changed on this branch) |

---

## 9. What this review does NOT license

- **Any promotion.** Seven P0 items remain open; the corpus is a set of **audited observations**, not vectors.
- **Any cutover.** Unchanged hard `user` gate, and not in question here.
- **Ratifying or amending any DEC-n.** T24/T26 own DEC-1 v3; nothing here touches it.
- **Treating the `t21v2` transcripts as attested vectors.** They are audit evidence, not corpus entries.
- **Any "small loans are safe" shortcut.** Refuted at principal **4.00** — a Go port that gets the precision
  seam wrong can diverge on a four-unit loan.
- **Any claim about `installmentAmountInMultiplesOf` or `daysInYearCustomStrategy` from Path A.** Both are
  provably dropped by that seam; only Path B grades them, and only `B-04` grades the DIYCS field.

---

## Appendix — my scripts

`.softhouse/reviews/t27-probe/` (both carry a "NOT RUN AGAINST A LIVE ORACLE" banner):

- **`t27_mutate.py`** — mutation testing. Corrupts a committed capture by one minor unit via byte-level text
  edit and asserts the repaired checkers FAIL. Proves T22's `I5` and T21's `X2` are genuinely failable, and
  that the retracted naive `X2` still reproduces its known spurious `P-03` failure.
  Verdict printed: `ALL REPAIRED CHECKS ARE GENUINELY FAILABLE`.
- **`t27_verify_claims.py`** — 40 mechanical checks: report byte-identity; all sixteen transcript claims;
  the capture-count fix; that each P0 blocker is still open in the artifact; the round-down re-derivation with
  model calibration; the DIYCS/day-count SHA-256 relations; the fresh-tenant re-observation.
  Result: **40 PASS, 0 FAIL**.

Neither script writes to `.softhouse/capture/`; mutated files live in a temp directory and are never committed.
