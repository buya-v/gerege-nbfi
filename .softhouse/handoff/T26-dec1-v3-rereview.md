# T26 handoff — independent re-review of DEC-1 revision 3

**Full review:** `.softhouse/reviews/T26-DEC-1-v3-rereview.md`
**Branch:** `softhouse/T26-dec1-v3-rereview`
**Reviewer:** T26, independent, zero inherited context. Pinned oracle commit verified
(`426a23544e8426a38ae43ae404670a0a7e85b9eb`). **No live oracle was reachable; no new observation was
taken, and none is claimed.**

---

## VERDICT — **ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable**

**P0 outstanding: 1.** (New — found by this review, not carried from T23.)

> **The sentence the driver needs:** Revision 3 correctly establishes *that* the EMI re-adjust loop
> fires inside the graded domain and correctly states its guard, but never states what the loop then
> *does* — so two implementations can satisfy every sentence of DEC-1 revision 3 and still return
> different money on roughly one in eight in-graded-domain loans, which the Run-1 corpus provably
> cannot detect; **fix that one specification gap (no oracle needed) and DEC-1 is ratifiable.**

---

## T23's three P0s

| | Disposition |
|---|---|
| **P0-1** EMI re-adjust loop | Substantively **CORRECT** — reachability (`:749`, `onlyOnActualModelShouldApply`), guard (`|lastEMI − penultEMI| × 100 > floor(n/2)` currency units, `Money.copy(double)` **replaces**), placement (`contract.go` `Period` type doc, not a pinned-to-zero field), and the exact-integer/no-float rule are all independently re-derived and confirmed. **Incomplete** — see P0-T26-1. |
| **P0-2** disbursement window | **RESOLVED, cleanly.** Predicate is the exact union of the oracle's half-open windows; false ordering clause removed from both artefacts with **no restatement surviving anywhere**. |
| **P0-3** `FrequencyYears` + error precedence | **RESOLVED.** Precedence is total and deterministic; no refusal condition is classified inconsistently between the two artefacts. One P1 in the mechanism prose. |

## The outstanding P0

**P0-T26-1 — the EMI re-adjust loop is specified by its trigger, not its effect.** Unstated: the
adjustment magnitude `emiDifference ÷ max(1, n − uncountablePeriods)` and its rounding, the
apply-and-recompute step, the `|newDiff| < |oldDiff|` adoption test (`contract.go` never mentions it
at all), the break-on-equal test, and the guard's `floor(n/2) > 0` / `emiDifference ≠ 0` conjuncts.
Source re-derivation over 24,000 in-graded-domain shapes: the guard fires on **2,855**; an
implementation that omits the adoption test differs on **2,156** of them, one that absorbs the whole
residual differs on **699** — up to **0.13** in total interest on DEC-1's own worked example.
Reference model to transcribe: `.softhouse/reviews/t26-probe/t26_rederive.py::readjust_loop`, which
reproduces both committed T23 observations exactly and only with the loop body present.

## New defects T23 missed

- **P1-T26-1** — ADR line 381 / `contract.go:245` name the wrong ACTUAL arm: for an annual period the
  cross-year partial-period arm `:1505-1507 → :1526-1531` runs, not `:1534-1535` (which is
  unreachable for YEARS). Conclusion unaffected; contradicts `contract.go:317-319`.
- **P1-T26-2** — revision 3 now self-contradicts on `Money.java:220-222` (§8 item 7 calls it "not part
  of the calculation"; §4.3 makes it the guard's threshold constructor on the live path).
- **P1-T26-3** — "seventeen per-period divergences" still wrong in three places (T23 P1-1, carried).
- **P2-T26-1/2** — graded-domain block differs between ADR §3.1 and `contract.go`; §4.1's calibration
  inference is weaker than its (independently supportable) conclusion.

## Vector question

**Do NOT make ratification wait on capturing guard-tripping vectors.** Gating the freeze on evidence
collapses the two-domain structure DEC-1 is built on, and no cloud fire has reached a live oracle.
**Do** bind it where it belongs: no conformance PASS for `loanschedule` and no cutover proposal until
at least one admissible vector trips the guard **and** one separates the adoption test (first such
shape: MNT 100,025 / 12 × 16.8 %, start 2024-01-01 — the two existing candidate cases do **not**
separate it).

## Checks

`go build ./...` exit 0 · `go vet ./...` exit 0 · `gofmt -l .` empty · `go test ./...` no test files
(declarations-only package). Non-negotiable scan **PASS** on every item: no float on any money path
(the only `float32`/`float64` tokens are in prose prohibiting them), no Oracle Database / MySQL /
MariaDB token, no US rails, no `first_name`/`last_name`, no hard-coded offset or rail threshold, no
insurance language.

## Next task

One more revision applying **P0-T26-1** (mechanical, source-only, no oracle) plus the three P1s,
then one more independent review. Nothing else blocks ratification.
