# T57 — EMI re-adjust smoothing-loop parity vectors

Task **T57** (`test_writer`), run `2026-08-17-run1-harness-schedule-poc`, context `harness`.
Closes **F-2 (P1)** of `.softhouse/reviews/T9-harness-and-vectors-review.md` §3.2.

**Result: closed.** Two shapes captured from the live reference oracle (Fineract) through a pass-3c
extension of the pass-3b rig, both confirmed to trip the `EmiAdjustment` guard, both promoted as
`class: "parity"` vectors. The parity corpus goes **11 → 13**, `inadmissible 0`, and
`.softhouse/conformance.sh` still exits **2** because no implementation is registered.

---

## 0. Starting state, confirmed before anything else

T9's own finding F-9 was that its reviewer was handed a stale worktree. Checked first:

- **11 `P-*.json` files** in `.softhouse/vectors/loanschedule/` plus 4 `REFUSE-*.json`
  [VERIFIED: `ls`, and `.softhouse/conformance.sh` before the change reports 11 parity rows].
- Worktree HEAD `30a030e` "tasks: T8 promotion slice + T20 done and merged", i.e. **after** the T8
  and T20 merges.
- **The T9 review file was NOT in the worktree.** It is committed at `99a4181` on branch
  `softhouse/T9-harness-vectors-review`, one commit ahead of this worktree's HEAD, and was read from
  there with `git show 99a4181:.softhouse/reviews/T9-harness-and-vectors-review.md`
  [VERIFIED: `git log --oneline --all -- <path>` returns exactly that one commit]. Nothing else in
  the task depended on it being on disk, but **the near-miss T9 warned about recurred in a milder
  form** — a worker told "you should see file X" did not see file X. Flagged for the driver: the
  worktree-cut point and the branch merge order still disagree.
- Environment as given: oracle **UP**, image `sha256:e5963396…d270459a`, pinned Fineract
  `426a23544e8426a38ae43ae404670a0a7e85b9eb` **clean**, seam class byte-identical to the pinned
  original [VERIFIED: all four checked directly before the capture, and again by the rig].

---

## 1. The gap, restated in one line

DEC-1 obliges a port to reproduce
`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (`ProgressiveEMICalculator.java:1258-1309`,
called at `:749`), and **no promoted vector could tell whether it did**. T9 proved this by
re-derivation: its loop-omitting model reproduced all eleven.

**This task re-proved it independently and more directly.** `.softhouse/capture/emiloop/noloop_model.py`
is a no-loop model transcribed step for step from the pinned source; run as a CONTROL it reproduces
**every** principal, interest, outstanding-balance and total cell of **all eleven** promoted
vectors — ten in `analyse.py` stage 1, and `P-03` separately in `p03-control.py` because its
disbursement lands on repayment 1's due date so `n = 5`, not 6.

```
P-00          6  REPRODUCED     P-04t         6  REPRODUCED
P-01         18  REPRODUCED     P-MNT-5M     18  REPRODUCED
P-02          6  REPRODUCED     P-MNT-1M2    12  REPRODUCED
P-02b         6  REPRODUCED     P-MNT-50M    36  REPRODUCED
P-04f         6  REPRODUCED     P-MNT-4M999  18  REPRODUCED
P-03      (n=5)  REPRODUCED, all five paying rows
```

[VERIFIED: `.softhouse/capture/emiloop/analyse-output.txt`,
`.softhouse/capture/emiloop/p03-control-output.txt`.]

A model that omits the loop and reproduces the oracle exactly is a proof that the loop changed
nothing on those inputs. **T9's F-2 conclusion is correct.** See finding **N-1** below for the one
part of T9's *method* that does not generalise.

---

## 2. The capture recipe — pass 3c

`.softhouse/capture/src/run-pass3c.sh` with `.softhouse/capture/src/Capture3c.java` and the
existing, unmodified `EmbeddableProgressiveLoanScheduleGenerator.java`. Documented at
`.softhouse/capture/README-pass3c.md`.

**Nothing existing was edited.** `Capture3b.java`, `run-pass3b.sh` and every committed capture under
`.softhouse/capture/out/` are untouched [VERIFIED: `git status` shows them unmodified].

### Every precondition it enforces

The nine of pass 3b, carried over **verbatim, none weakened**, and two added:

| # | breach that fails the run | outcome on this run |
|---|---|---|
| 1 | docker missing, or the image absent | passed |
| 2 | image id ≠ `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | passed, exact match |
| 3 | pinned checkout missing, at another commit, or **dirty** | passed, `426a2354…` clean |
| 4 | **seam class differing from the pinned original by one byte** | passed, sha `bf397f0b…a80714` |
| 5 | container exits non-zero | passed |
| 6 | no JSON on stdout, or JSON that does not parse | passed |
| 7 | **stderr non-empty** | passed, stderr is the empty-file digest `e3b0c442…852b855` |
| 8 | wrong capture count, any `"observed": null`, any `error` key | passed, 4 captures, ids exactly as expected |
| 9 | effective `MathContext` not the ratified `(19, HALF_UP)` / RoundingMode **ordinal 4**; image `git.commit.id` disagreeing with the checkout; `git.dirty` not `false`; runner echo disagreeing with what the runner measured | passed; `effectiveMathContextPrecision 19`, `effectiveRoundingModeOrdinal 4`, `matchesRatifiedProductionSetting true` |
| **10** | **NEW** — either rig calibration failing to reproduce the committed pass-3b observation of the case it repeats, comparing `inputs` and `observed` as canonicalised JSON, cell for cell | passed, both |
| **11** | **NEW** — the calibration reference file missing, or not sha256 `8d23c48f…c945c79` | passed |

Also asserted per case, as in pass 3b: `ambientMoneyHelperPrecision == 19` and
`ambientMoneyHelperRoundingModeOrdinal == 4`, and the threaded rounding-mode ordinal is 4 on every
case including the precision-12 calibration.

### Run record

```
run id     pass3c-20260819T131157Z
capturedAt 2026-08-19T13:11:58.415371634Z
captures canonical sha256  6110d86734f17d16fd1f2cc6b154d069bcc9328ef3bc3b0eb9842682a65aea3e
raw json sha256            cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec
```

Artefacts: `capture-prod3c-raw.json`, `-raw.txt`, `-log.txt`, `-stderr.txt`,
`-attestation.json`, `-classpath-sha256.txt`, `-sha256.txt`, all under `.softhouse/capture/out/`.
The sidecar carries `productionSettingsCaptureIds` and `calibrationCaptureIds` with **pass 3b's
exact definitions** (keyed on MathContext precision ≠ 19), plus `calibrationRoleCaptureIds`,
`parityCandidateCaptureIds` and a `calibrationReport` array, because pass 3c carries a calibration
*at* the production precision that pass 3b's precision-keyed definition cannot see.

---

## 3. The calibration — what it reproduced, and that it matched

Two calibration cases, both with inputs **byte-identical to a committed pass-3b case, tenant id
included**, so each reproduction is of the same question rather than of a similar one.

| calibration | reproduces committed | MathContext | inputs identical | observed identical |
|---|---|---|---|---|
| `P-CAL` | pass 3b `P-CAL` | (12, HALF_UP) | **yes** | **yes** |
| `P-CAL-P00` | pass 3b `P-00` | **(19, HALF_UP)** | **yes** | **yes** |

The value reproduced is the C-00 baseline schedule: level installment **17.01**, final row total
**17.00**, principals 16.43 / 16.52 / 16.62 / 16.72 / 16.81 / 16.90, interest 0.58 / 0.49 / 0.39 /
0.29 / 0.20 / 0.10, total interest **2.05**, closing balance 0.00. The rig compares the whole
`observed` block, not those cells alone.

[VERIFIED: run stdout —
`calibration OK — P-CAL reproduced committed P-CAL … inputs and observed both identical`,
`calibration OK — P-CAL-P00 reproduced committed P-00 … inputs and observed both identical`;
and `calibrationReport` in `capture-prod3c-attestation.json`, both entries
`"observedIdentical": true`.]

> **N-2, honest caveat, P3.** The two calibrations produced the **same** `observedCanonicalSha256`
> (`6c052bda…618d59`): on this shape the observable 2-decimal output is identical at precision 12
> and at precision 19. So the calibration proves *the rig reproduces an already-known value* — which
> is what it is for — but it does **not** independently witness that the run was at precision 19.
> That comes from the attestation (`effectiveMathContextPrecision 19`,
> `matchesRatifiedProductionSetting true`) and from the per-case `mathContextPrecision` assertion,
> both machine-checked and both failing the run if wrong. The pre-existing corpus has the same
> property; recording it so no later reader over-reads the calibration.

### Cross-harness reproduction, unplanned but load-bearing

**The brief said these two shapes "have never been captured". That is not correct.** Task **T37**
captured both, at (19, HALF_UP), through a *different* Path A harness —
`.softhouse/capture/dec1-binding/out/t37-binding.json`, cases `T37-3-A` and `T37-3-B`. They were
never *promoted*, and T37's harness emits neither the in-container attestation nor the plan-level
`totalPrincipalAmount` / `totalFeeAmount` / `totalPenaltyAmount` / `totalOutstandingAmount` columns
that promotion needs, so pass 3c was still required. But the earlier captures make a free
independent control available, and it is clean:

```
P-EMI-6-1M014632 vs T37-3-A   ·   P-EMI-36-127704 vs T37-3-B
T37 cross-check: 478 cells compared, 0 mismatches
```

[VERIFIED: `.softhouse/capture/emiloop/t37-crosscheck-output.txt`.] Two independently written
harnesses, on the same seam, agree on every column both emit.

---

## 4. The guard — arithmetic, and it trips on both

`EmiAdjustment.shouldBeAdjusted` (`EmiAdjustment.java:31-36`):

```java
double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero()
    && emiDifference.abs().multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));
```

`Money.copy(double)` **replaces** the amount (`Money.java:220-222`), so the threshold is
`floor(n/2)` currency units flat and the test reduces to
**|lastEMI − penultimateEMI| in minor units > floor(n/2)**.

**Where it must be evaluated: on the PRE-ADJUSTMENT model.** The loop is called at
`ProgressiveEMICalculator.java:749`, *after* `calculateLastUnpaidRepaymentPeriodEMI` at `:747`. The
state its guard sees is exactly the no-loop schedule — raw recurrence EMI plus final-period
balancing. That is what the table below evaluates.

### `P-EMI-6-1M014632` — MNT 1,014,632 / 6 × 7.0 %

```
r  = 7.0/100 × 30/360, setScale(19, HALF_UP)            = 0.0058333333333333333
rateFactorPlus1N (folded, mc 19)                        = 1.035514403982984519
fnResult         (folded, mc 19)                        = 6.088183539940203430
raw EMI = 1.035514403982984519 × 1014632 / 6.088183539940203430, Money 2dp = 172,574.63
last-period balancing raises the final EMI to                                172,574.67
|lastEMI − penultimateEMI| = |172,574.67 − 172,574.63| = 0.04 = 4 MINOR UNITS
threshold = floor(6/2) = 3 currency units → 3 minor units
                          4 > 3  →  ***THE GUARD TRIPS***
```

### `P-EMI-36-127704` — MNT 127,704 / 36 × 16.8 %

```
r  = 16.8/100 × 30/360, setScale(19, HALF_UP)           = 0.0140000000000000000
rateFactorPlus1N (folded, mc 19)                        = 1.649553402432599470
fnResult         (folded, mc 19)                        = 46.39667160232853354
raw EMI = 1.649553402432599470 × 127704 / 46.39667160232853354, Money 2dp = 4,540.29
last-period balancing raises the final EMI to                                4,540.54
|lastEMI − penultimateEMI| = |4,540.54 − 4,540.29| = 0.25 = 25 MINOR UNITS
threshold = floor(36/2) = 18 currency units → 18 minor units
                          25 > 18  →  ***THE GUARD TRIPS***
```

**Both trip. F-2 is closed.** [VERIFIED: `.softhouse/capture/emiloop/analyse-output.txt`, stage 2.]

And the loop demonstrably *changed the schedule*: the oracle's observed level installment is
**172,574.64** and **4,540.30**, one minor unit above each raw recurrence value. A port that stopped
at the raw value is wrong on every row.

---

## 5. Finding N-1 (P2) — the guard must NOT be screened on the oracle's own output

T9's §3.2 table computed the guard on the **observed** (post-loop) schedules of the eleven promoted
vectors. That is the right *conclusion* by luck and the wrong *screen* in general, because the loop
exists precisely to shrink the residual the guard measures. Re-running the same screen on this
task's two shapes:

| shape | n | guard on the **no-loop** model | guard on the **observed** output |
|---|---|---|---|
| `P-EMI-6-1M014632` | 6 | \|Δ\| **4** > 3 → **TRIPS** | \|Δ\| 2 vs 3 → **does not trip** |
| `P-EMI-36-127704` | 36 | \|Δ\| **25** > 18 → **TRIPS** | \|Δ\| 24 vs 18 → still trips |

**T9's screen would have rejected `P-EMI-6-1M014632` as a non-tripping shape**, even though it is
one of the two shapes DEC-1 names and even though the loop plainly moves money on it. (The loop runs
at most three iterations and stops early when an iteration no longer reduces the difference —
`ProgressiveEMICalculator.java:1289-1292` — so it does not always drive the residual under the
threshold, which is why the 36-period shape still trips after the fact.)

The correct screen is the one used here: build the no-loop model, evaluate the guard on it, and
confirm the oracle's output differs. Recorded so a later capture-selection task does not re-inherit
the shortcut. **T9's conclusion is unaffected** — §1 above re-establishes it by direct
reproduction of all eleven.

---

## 6. The derived margins, with their arithmetic

The counterfactual is **`EMI-SMOOTHING-LOOP-OMITTED`**, capability `schedule.core`: a port that
implements the recurrence and the final-period balancing adjustment but omits the loop. It is a
claim about a wrong port, never about the oracle. The margin is the **widest single-cell
disagreement over the columns the harness actually grades** (`principal_minor`, `interest_minor`,
`outstanding_principal_minor`) — the same convention the committed corpus uses, e.g. P-00's
`STRAIGHT-LINE-PRINCIPAL-DIVISION` margin 24 is "widest disagreement, at paying period 1".

### `P-EMI-6-1M014632` — margin **5** minor units

Oracle level installment 172,574.64; counterfactual 172,574.63. **All 6 of 6 paying rows differ.**

```
 k   obs principal    cf principal   Δ | obs balance    cf balance     Δ
 1     166,655.95      166,655.94   +1 |  847,976.05    847,976.06    −1
 2     167,628.11      167,628.10   +1 |  680,347.94    680,347.96    −2
 3     168,605.94      168,605.93   +1 |  511,742.00    511,742.03    −3
 4     169,589.48      169,589.47   +1 |  342,152.52    342,152.56    −4
 5     170,578.75      170,578.74   +1 |  171,573.77    171,573.82    −5   ← widest
 6     171,573.77      171,573.82   −5 |        0.00          0.00     0
```

Widest cell: paying period 5, `outstanding_principal_minor`, oracle **17157377** vs counterfactual
**17157382** → `|17157377 − 17157382| = 5`. Interest cells all agree; total interest agrees at
20,815.82 — the loop redistributes here rather than changing the total.

### `P-EMI-36-127704` — margin **47** minor units

Oracle level installment 4,540.30; counterfactual 4,540.29. **All 36 of 36 paying rows differ.**
Principal diverges by 1–2 minor units per row and the **outstanding balance compounds**, 1, 2, 3 …
reaching 47 at paying period 35:

```
 k   obs principal    cf principal   Δ | obs balance    cf balance     Δ
 1       2,752.44        2,752.43   +1 |  124,951.56    124,951.57    −1
 …
35       4,415.80        4,415.78   +2 |    4,477.38      4,477.85   −47   ← widest
36       4,477.38        4,477.85  −47 |        0.00          0.00     0
total interest  35,746.56 (3,574,656 minor)  vs  35,746.69 (3,574,669 minor)   Δ 13
```

Widest cell: paying period 35, `outstanding_principal_minor`, oracle **447738** vs counterfactual
**447785** → `|447738 − 447785| = 47`.

Both are **money** kills: `kind` omitted, `margin_minor > 0`, no `divergent_cells`.

The two vectors also carry `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT` (margins 2
and 24) and `STRAIGHT-LINE-PRINCIPAL-DIVISION` (246,844 and 93,005), derived exactly as the
committed corpus derives them. Six new named money kills; the harness's counterfactual tally goes
24 → 30.

---

## 7. Against DEC-1 — corroborated, with one wording caution

**DEC-1's numbers reproduce exactly. There is no contradiction to report.**

| DEC-1, `contract.go:1655-1658` | observed / derived here | verdict |
|---|---|---|
| `MNT 1,014,632 / 6 × 7.0%`: oracle level installment **172,574.64** | observed row total **172,574.64** on paying periods 1–5 | **MATCHES** |
| same shape: no-loop model **172,574.63** | raw recurrence EMI **172,574.63** | **MATCHES** |
| same shape: "*every period shifts*" | 6 of 6 paying rows differ from the counterfactual | **MATCHES** |
| `MNT 127,704 / 36 × 16.8%`: oracle total interest **35,746.56** | observed `totalInterestAmount` **35,746.56** | **MATCHES** |
| same shape: no-loop model **35,746.69** | counterfactual total interest **35,746.69** | **MATCHES** |
| guard is `\|lastEMI − penultEMI\| × 100` vs `floor(n/2)` currency units, "3.00 for a 6-period loan, 18.00 for 36" | derived independently from `EmiAdjustment.java:31-36` and `Money.java:220-222`; thresholds 3 and 18 | **MATCHES** |
| "None of the twelve Run-1 captures trips this guard" | the no-loop model reproduces all eleven promoted vectors cell for cell | **MATCHES** |

**Caution, not a contradiction — for the driver, since DEC-1 is ratified.** DEC-1's `172,574.64 vs
172,574.63` and `35,746.56 vs 35,746.69` are the *illustrative divergences* it quotes (an
installment, a total), **not** the graded-cell margins. The margins promoted here are **5** and
**47**, both larger, because the harness grades per-row principal, interest and outstanding balance
and the divergence compounds. Anyone reading DEC-1's figures as the margins would understate the
kill by an order of magnitude on the 36-period shape. **No DEC-1 text is wrong; only a reading of it
would be.** No amendment is proposed and none is needed.

Deliberately **not** reconciled and left for the driver: DEC-1's line "None of the **twelve** Run-1
captures trips this guard" counts twelve pass-3b captures, of which `P-CAL` is a never-promotable
calibration; the promoted corpus is eleven. Cosmetic, and consistent either way.

---

## 8. The promoted vectors

| file | case id | rows | capability | counterfactuals |
|---|---|---|---|---|
| `P-EMI-6-1M014632-emi-smoothing-loop.json` | `P-EMI-6-1M014632` | 7 | `schedule.core` | loop-omitted **5**, final-balancing 2, straight-line 246,844 |
| `P-EMI-36-127704-emi-smoothing-loop.json` | `P-EMI-36-127704` | 37 | `schedule.core` | loop-omitted **47**, final-balancing 24, straight-line 93,005 |

Promotion script `.softhouse/handoff/T57-promote-emi-vectors.py`. Every `expect` cell is a value
literally present in `capture-prod3c-raw.json`; the only transformation is exact textual
major→minor scaling, carried alongside in the `*_major_text` cross-check fields. Each
`DISBURSEMENT` row marks exactly the two `unrecorded_fields` the existing corpus marks —
`installment_number` and `interest_minor` — because `LoanSchedulePlanDisbursementPeriod` is a Lombok
`@Data final class` with four fields, `periodNumber()` returns null and there is no interest
accessor. 26 ungraded cells store-wide, up from 22: 2 new disbursement rows × 2 cells.

---

## 9. Transcription audit

Three **independently written** minor-unit converters, deliberately using three different
techniques, all agreeing:

| converter | technique | where |
|---|---|---|
| promotion | textual split-and-pad on the decimal point | `T57-promote-emi-vectors.py` |
| audit | integer string splicing, no `Decimal`, no `Fraction` | `T57-transcription-audit.py` |
| cross-check | exact `Fraction` rational arithmetic | `t57-fraction-crosscheck.py` |

```
AUDIT P-EMI-6-1M014632-emi-smoothing-loop.json    155 cells compared, 0 mismatches
AUDIT P-EMI-36-127704-emi-smoothing-loop.json     695 cells compared, 0 mismatches
TOTAL                                             850 cells compared, 0 mismatches
Fraction cross-check:                             176 money cells, 0 mismatches
```

The audit also re-checks provenance (`capture_sha256` recomputed from the file, `captured_at` and
`fineract_commit` against the attestation), every request field against the capture's `inputs`, the
oracle's own principal + interest = total per row, all six whole-schedule invariants over the
**transcribed** expectation, and the `graded_against` shape rules (money kind, margin > 0,
`divergent_cells` empty, evidence non-empty). [VERIFIED:
`.softhouse/capture/emiloop/transcription-audit-output.txt`.]

**Float scan** — `.softhouse/handoff/T57-float-scan.py`, which both hooks `json.loads`'
`parse_float` and re-lexes the raw bytes with string literals blanked:

```
scanned 20 json files under .softhouse/vectors
bare JSON number tokens examined: 1715
ZERO bare JSON number tokens containing '.', 'e' or 'E'. PASS.
```

No float is constructed anywhere in the promotion path, in either direction.

---

## 10. Before / after

```
                          BEFORE            AFTER
parity vectors in store   11                13
inadmissible              0                 0
harness errors            16                18   (one per admitted vector; nothing to grade)
counterfactuals named     24 (21 money,     30 (27 money,
                              3 structural)      3 structural)
exit code                 2                 2    ← NOT a pass, and must not become one
```

`--self-test` (the harness graded against a reference implementation built from the vectors
themselves):

```
parity vectors    PASS 13   FAIL 0
contract-refusal  PASS 4    FAIL 0
self-test         PASS 1    FAIL 0
inadmissible 0    harness errors 0    invariant violations 0
cells compared    1350 graded, 26 ungraded      (was 1046 / 22)
VERDICT: SELF-TEST PASS (exit 0). The harness grades correctly. NOT a conformance PASS.
```

Every invariant holds on 14 of 14 vectors. `--prove`: **15 passed, 0 failed** — unchanged.

Toolchain (`. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`, go1.26.6):

```
go build ./...   OK
go test ./...    ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance  0.980s
gofmt -l .       internal/apps/loanschedule/contract/contract.go        (only, as gate G-3 expects)
```

`contract.go`, `PIN.json`, `capabilities.json` unmodified. Nothing under `nexus/` touched. No
existing capture or vector edited.

---

## 11. Findings for the driver

- **N-1 (P2)** — a candidate shape must be screened for the smoothing loop on the **pre-adjustment**
  model, not on the oracle's own output. T9's §3.2 screen would have rejected one of the two shapes
  DEC-1 names. §5 above. T9's *conclusion* stands; only the method does not generalise.
- **N-2 (P3)** — pass 3c's two rig calibrations produce byte-identical `observed` blocks, so the
  calibration does not itself witness precision 19. The attestation and the per-case assertion do.
  §3 above. The pre-existing corpus shares this property.
- **N-3 (P3)** — the brief's premise that these two shapes "have never been captured" is wrong: T37
  captured both. They had never been *promoted*, which is the real gap, and T37's harness lacks the
  columns and attestation promotion requires. Turned into a free cross-harness control, 478 cells,
  0 mismatches. §3 above.
- **N-4 (P3)** — DEC-1's quoted divergences are not the graded-cell margins; the real margins are 5
  and 47. §7. No amendment proposed.
- **N-5 (P2)** — this worktree did not contain `.softhouse/reviews/T9-harness-and-vectors-review.md`
  despite the brief saying it would; it was read from commit `99a4181`. The same class of problem as
  T9's own F-9. §0.
- **Coverage note.** T9's F-6 counted 9 distinct shapes behind 11 vectors. These two are genuinely
  new shapes, and they are the first in the store that grade a *behaviour* (the loop) rather than
  only an arithmetic path — so the honest count is now **11 distinct shapes behind 13 vectors**.

## 12. Reproducing all of it

```sh
sh    .softhouse/capture/src/run-pass3c.sh                       # capture (needs the oracle image)
python3 .softhouse/capture/emiloop/analyse.py                    # control, guard, margins
python3 .softhouse/capture/emiloop/p03-control.py                # the eleventh vector
python3 .softhouse/capture/emiloop/t37-crosscheck.py             # cross-harness reproduction
python3 .softhouse/handoff/T57-promote-emi-vectors.py            # promotion
python3 .softhouse/handoff/T57-transcription-audit.py P-EMI-6-1M014632-emi-smoothing-loop.json \
                                                      P-EMI-36-127704-emi-smoothing-loop.json
python3 .softhouse/handoff/t57-fraction-crosscheck.py
python3 .softhouse/handoff/T57-float-scan.py
.softhouse/conformance.sh --self-test && .softhouse/conformance.sh --prove
```
