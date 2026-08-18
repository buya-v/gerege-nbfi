# Capture pass 3b — pass 3 with the Path A admissibility defects closed

**Task:** T35, branch `softhouse/T35-patha-admissibility`, 2026-08-18.
**Fire:** local, on Buyan's Mac. The reference oracle (Fineract) was **reachable**, which is why these
items could finally be done — they had been parked `oracle_unreachable` across several fires.
**Status:** RAW OBSERVED. **Nothing promoted.** DEC-1 is at revision 6 and UNRATIFIED (gate G-1), so
captures stay in raw observed form; promotion is not this task's to make.

**What it closes:** T21 §10 **P0-2** (attestation block), **P0-3** (the three missing per-period columns
and the plan totals), **P0-4** (an executable run recipe validated against the pinned image), and **P1-9**
(`toPlainString()`, stack frames on the error branch). Each is closed against a live run, not a draft.

**What it deliberately does not do:** it does not modify `Capture3.java` or `capture-prod-raw.json`. Pass 3
stays exactly as committed, so its byte-for-byte reproducibility — re-confirmed on this fire — survives, and
pass 3b can be compared against it value for value.

---

## 1. The artefacts

| file | what it is |
|---|---|
| `src/Capture3b.java` | pass 3's twelve cases, input for input, plus the attestation block, the missing columns and `toPlainString()` |
| `src/run-pass3b.sh` | the executable recipe. Run `sh .softhouse/capture/src/run-pass3b.sh` from the repo root |
| `out/capture-prod3b-raw.json` | the capture, with a top-level `attestation` object |
| `out/capture-prod3b-attestation.json` | the **machine-readable sidecar**, next to the captures |
| `out/capture-prod3b-log.txt` | the oracle's own `MoneyHelper` SLF4J lines, kept — they independently corroborate the mode per tenant |
| `out/capture-prod3b-stderr.txt` | 0 bytes. A non-empty stderr fails the run |
| `out/capture-prod3b-classpath-sha256.txt` | sha256 of every classpath entry the run compiled and ran against |
| `out/capture-prod3b-sha256.txt` | sha256 of every output |
| `out/t35-byte-identity.py` | pass 3 vs pass 3b, value for value |
| `out/t35-newcolumn-checks.py` | checks that only exist now the new columns do |

---

## 2. Attestation — T21 P0-2

Measured **inside the container, during the run**. Everything an in-container process cannot know (the
docker image id, the host checkout) is echoed under `runnerSupplied` and labelled an echo, never a
measurement; the runner asserts those independently and fails the run on mismatch.

| attested value | observed |
|---|---|
| image ref / id | `fineract:latest` / `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| **Fineract commit built into the image** (`BOOT-INF/classes/git.properties`) | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`, describe `1.15.0-273-g426a235` |
| pinned checkout commit, tree state | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, clean — **the same commit**, so image and source agree |
| `/app/fineract-provider.jar` sha256 / size | `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9` / 230,485,171 B |
| JVM | OpenJDK 64-Bit Server VM `21.0.11+10-LTS`, Zulu, vendor Azul Systems; Linux aarch64 |
| JVM input flags | **none** — `inputArgumentCount = 0`. No `-D`, no `-XX`, nothing that could move arithmetic |
| file.encoding / locale / default TZ | `UTF-8` / `en_US` / `GMT` (the seam is `LocalDate`-based; recorded for completeness, not because it is load-bearing) |
| `MoneyHelper.PRECISION` | **19** |
| effective `MathContext` for a tenant initialised with value 4 | **precision 19, `HALF_UP`, RoundingMode ordinal 4** |
| matches the ratified production setting | **true** |
| seam class sha256, both sides | `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` — byte-identical to the pinned original |
| harness sha256 | `982e4da341d1cdb5dcd43eb1b2488d843dd6360ca5764a7d42e2b671722f29ff` |
| classpath | **350** entries, aggregate digest recorded, per-entry digests in `out/capture-prod3b-classpath-sha256.txt` (350 lines) |

The oracle's own log lines are kept — **13** of them: one per capture tenant (12), all reading
`Initialized rounding mode for tenant \`cap_p_*\`: HALF_UP`, plus one for the attestation's own probe
tenant `attest_probe`. They are an independent corroboration of the mode that does not depend on the
harness's own reporting.

**Per capture**, the artefact now also carries `ambientMoneyHelperPrecision`,
`ambientMoneyHelperRoundingMode`, `ambientMoneyHelperRoundingModeOrdinal` and
`mathContextRoundingModeOrdinal`, so a downstream consumer can tell mechanically what each record ran at.
All twelve: ambient `(19, HALF_UP, ordinal 4)`. Eleven at explicit `mc = (19, HALF_UP, ordinal 4)`; `P-CAL`
at explicit `mc = (12, HALF_UP)` — the rig calibration, unchanged and still **never** a parity vector.

**The run did NOT run at a different setting.** Had it done so, that would have been recorded as a finding;
the recipe also fails the run in that case rather than leaving a mislabelled artefact behind.

---

## 3. Byte-identity against the committed corpus — the thing most worth finding

Two checks, in order.

**3.1 Pass 3 reproduces, byte for byte, on this fire.** `Capture3.java` unmodified, same recipe:
`sha256 11c5c74a27aa1d9e91b9eacf20e36e469bc5e34e3943e00b1543ad3671a732e2` — **identical** to the committed
`out/capture-prod-raw.json` and to the digest the T21 audit recorded. So the baseline is sound before
anything is compared against it.

**3.2 Pass 3b vs pass 3, value for value** (`out/t35-byte-identity.py`):

```
compared 1560 values published by pass 3, across 12 captures
  IDENTICAL      : 1560
  RENDERING-ONLY : 0
  VALUE CHANGED  : 0
  DROPPED by 3b  : 0
  ADDED by 3b    : 12  (keys pass 3 never emitted for that period type)
VERDICT: PASS
```

**No number pass 3 published changed.** Not one, in either direction. The twelve additions are the
`balance` (`outstandingLoanBalance`) on each DISBURSEMENT row, which pass 3 emitted for repayment and
down-payment rows but not for disbursement rows.

**T21 P1-9 — `toPlainString()` changed nothing, not even rendering.** `RENDERING-ONLY : 0` says the
`BigDecimal.toString()` and `toPlainString()` renderings were already identical on every value in this
corpus. That confirms the audit's `A5` finding (no scientific notation had escaped) from the other
direction, and it means the switch is a latent-channel fix, not a correction.

**Stability of the re-run.** The recipe was run **three** times. The whole-file digest moves each time
because the attestation carries a UTC timestamp; the digest that matters —
`capturesCanonicalSha256 = 02e94174cda26540e882d6da0f0ac3aabc02923ddf501a4dde90fd7d60aa38ec`, the
canonicalised `captures` array — was **identical on all three runs**, and the two artefacts differ in
nothing but `capturedAtUtc` and `runId`.

**Invariants re-run on the new artefact.** `t21v2-invariants.py`: `SIX-CLAIMED verdict: ALL PASS` on all
twelve, with `A2` violated on `P-03` alone — exactly the pass-3 result, and exactly the artefact of `A2`'s
formulation that the T21 audit diagnosed (§6.1). `t21-probe-invariants.py` (with T25's repaired `X2`):
`ALL PASS` on all twelve.

---

## 4. The new columns — T21 P0-3

Emitted from the oracle's own objects: `periodFromDate`, `feeAmount`, `penaltyAmount`
[`LoanSchedulePlanRepaymentPeriod.java:26-38`], `periodFromDate` on disbursement and down-payment rows
[`LoanSchedulePlanDisbursementPeriod.java:26-30`, `LoanSchedulePlanDownPaymentPeriod.java:26-33`], and the
plan totals `totalPrincipalAmount`, `totalFeeAmount`, `totalPenaltyAmount`, `totalOutstandingAmount`
[`LoanSchedulePlan.java:36-43`].

Checks that were impossible before and pass now (`out/t35-newcolumn-checks.py`, all twelve captures):

- **N1 period-boundary contiguity** — for consecutive repayment periods, `fromDate[i] == dueDate[i-1]`.
  This is precisely the class of error the audit said no vector could catch without the column.
- **N2** the first repayment period's `fromDate` equals the schedule generation start date. On `P-03` that
  is `2024-01-01` while the disbursement row sits at `2024-02-01` — the pre-disbursement snapshot is now
  visible in the data instead of having to be inferred.
- **N3** every `feeAmount`/`penaltyAmount` is exactly `currencyDecimalPlaces` decimals, plain, non-negative.
- **N4** `totalFeeAmount` = Σ`feeAmount`, `totalPenaltyAmount` = Σ`penaltyAmount`, integer minor units.
- **N5** `totalPrincipalAmount` = Σ repayment `principal` = `totalDisbursedAmount`.

Observed values: every `feeAmount` and `penaltyAmount` is `0.00` (144 of each), and both plan totals are
`0.00` on all twelve. That is expected — no charge is attached on this path — and it is now **observed**
rather than assumed. It also means the corpus still has **zero discriminating power over charges**: a Go
port that mishandles fees would pass every one of these vectors.

### New finding — `totalOutstandingAmount` is a hard-coded zero, and its scale is 0

Emitted as `"0"` on **all twelve** captures — scale 0, unlike every other money string in the artefact,
which is scale 2. The mechanism is not rounding:

```java
// ProgressiveLoanScheduleGenerator.java:156-157
final BigDecimal totalPrincipalPaid = BigDecimal.ZERO;
final BigDecimal totalOutstanding   = BigDecimal.ZERO;
```

and that constant is passed straight through to `LoanScheduleModel.from(...)`
[`ProgressiveLoanScheduleGenerator.java:159-164`] and out via `LoanSchedulePlan.totalOutstandingAmount`
[`LoanSchedulePlan.java:43, 85-96`]. [VERIFIED: pinned checkout, both files.]

Two consequences worth carrying forward:

1. **The field carries no information on this path.** It is not "the schedule's outstanding total"; it is
   the literal `BigDecimal.ZERO`. Nobody should read meaning into it, and a Go port must emit zero there.
2. **It breaks the scale-discipline invariant the audit's `A5` asserts** — but `A5` never saw it: `A5`
   inspects `{principal, interest, total, balance, totalOutstandingBalance}` plus three plan totals only
   [`t21v2-invariants.py:96-101`]. A future scale check must decide explicitly whether `"0"` is acceptable
   at that key. **We do not assert an expected value for it here**; it is reported as observed (`N6`).

---

## 5. The run recipe — T21 P0-4

`src/run-pass3b.sh`, run from the repo root, **validated by running it against the pinned image** (three
times). It fails the run — non-zero exit, and refuses to leave a capture behind that a later reader could
mistake for a good one — on each of:

1. docker missing or the image absent;
2. **image id ≠ the pinned digest**;
3. pinned checkout missing, at the wrong commit, or with a **dirty working tree**;
4. **seam-class drift** — `cmp` against the pinned original; any difference and the run would not have been
   executing the oracle's code;
5. non-zero container exit;
6. no JSON on stdout, or JSON that does not parse;
7. **non-empty stderr** — a stack trace where a capture was expected;
8. wrong capture count, any `"observed": null`, or any `error` key present;
9. the effective `MathContext` not being `(19, HALF_UP)` / ordinal 4, the image's `git.commit.id` not
   matching the pinned checkout, `git.dirty` not `false`, or the runner's echoed attestation disagreeing
   with what the runner itself measured.

**The T22 P0-5 defect class, checked for deliberately.** A shell glob in an output path cannot expand
against a file that does not exist yet, so `-o out/X-*.json` makes the tool create a file named literally
`X-*.json`. **Every output path in this recipe is a literal filename**; there is no `*` and no `?` in any
redirect target. The same discipline is applied to the two other scripts this task added
(`src/run-rc6-rounddown-attestation.sh`, `.softhouse/reviews/t21v2/run-probe2-attested.sh`), and the RC-6
script additionally captures `%{http_code}` and treats any non-200 body as an error body, not a capture.

Every output is hashed into `out/capture-prod3b-sha256.txt`, and the sidecar carries both the per-file
digests and the run-stable `capturesCanonicalSha256`, so a re-run is **verified rather than eyeballed**.

---

## 6. Admissibility verdict

**The three T21 Path A P0 items are closed. The eleven `(19, HALF_UP)` records are still NOT promoted, and
this task does not promote them.**

What has changed: the eleven are now attested, carry every column the capture plan mandates, and are
produced by a committed recipe that has been run. What has not changed:

- **DEC-1 is at revision 6 and UNRATIFIED (gate G-1).** Captures stay in raw observed form until the
  contract they would be graded against is settled. Promotion is not an agent-side clerical step.
- **The seam's blind spots are unchanged and are a property of the rig, not of the run.** Path A accepts a
  19-component `LoanRepaymentScheduleModelData` and honours 17; `installmentAmountInMultiplesOf` and
  `daysInYearCustomStrategy` are provably dropped [T21 §7]. The eleven have **zero** discriminating power
  over either field, and now demonstrably none over charges either. "Vectors pass" must never be read as
  "the contract is covered".
- **T21 P1-8 remains open** — the harness still cannot vary `CurrencyData.inMultiplesOf` independently of
  `installmentAmountInMultiplesOf` (T19-10), so the one multiples-of channel Path A can reach is still
  uncapturable. Inert for these twelve (all pass `null`), but it is the reason the `decimalPlaces == 0`
  behaviour is unvectored.
- **T21 P1-11 remains open** — the `36 × 16.8 %` small-principal shape, which the oracle diverges on at
  principal **4.00**, is still not in the capture set.
- **`P-CAL` is never promotable** as a parity vector. It runs at `(12, HALF_UP)`.
- **Path B is a separate list.** T22 P0-3, P0-4, P0-6 remain open; only T27 RC-6's attestation half is
  closed by this task (`out/t35-rc6-rounddown-attestation.json`).

---

## 7. What this pass does not license

- Any promotion to the parity vector store, of anything, by anyone reading this document.
- Any cutover. Unchanged hard `user` gate.
- Ratifying or amending DEC-1.
- Any conclusion about `installmentAmountInMultiplesOf`, `daysInYearCustomStrategy`, charges, fees,
  penalties or multi-disbursement drawn from a Path A vector.
- Any "small loans are safe" shortcut — refuted by the oracle at principal 4.00
  (`.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt`, now carrying its provenance header).
