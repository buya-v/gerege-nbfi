# Capture pass 3 — the first captures at PRODUCTION settings (19, HALF_UP)

**Fire:** local `20260818-152328` (Buyan's Mac), 2026-08-18
**Executed by:** the orchestrator (vector capture touches the oracle, so it is orchestrator-only)
**Status:** RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**. No vector promoted to the store; no gate answered.

## Why pass 3 exists

Buyan ratified the tenant parameters on 2026-08-18 (`.softhouse/gates-proposed-answers.md`): **rounding
mode HALF_UP**, **licence NBFI (ББСБ)**. Precision was not a choice to make — `MoneyHelper.PRECISION = 19`
is a compile-time constant and `getMathContext()` returns `new MathContext(19, tenantRoundingMode)`
[`MoneyHelper.java:35, 91-93`]. So the **production `MathContext` is `(19, HALF_UP)`**.

Passes 1 and 2 ran almost entirely at precision **12 or 8** — precisions production never runs. They did
their job: they proved the precision ambiguity moves money. But that makes them **discrimination probes,
not parity vectors**. Pass 3 is the first capture set at the settings the Go module will actually have to
match, on both the parameter path and the ambient `MoneyHelper` path (tenant rounding mode set to
`HALF_UP(4)` in every case, so the ambient context is `(19, HALF_UP)` too).

Provenance is unchanged from pass 2 and re-asserted per run — same image digest
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, same pinned commit
`426a23544`, same Zulu 21.0.11, same Path A seam (in-process, no database). Reproduction commands:
`.softhouse/capture/README-pass2.md`, substituting `Capture3.java`.

**Artefacts:** `src/Capture3.java`, `out/capture-prod-raw.json` (12 captures),
`out/capture-prod-log.txt`, `out/capture-prod-stderr.txt`.

## The rig is calibrated — three independent harnesses now agree

`P-CAL` deliberately runs at `(12, HALF_UP)`, **not** production settings, because that is what the shipped
test expectation was produced at. It is the rig calibration, not a parity vector.

| Check | Result |
|---|---|
| `P-CAL` (pass 3) vs `C-00` (pass 1) — every period, every column | **identical** |
| `P-01` (pass 3) vs `D-01-p19` (pass 1), both at `(19, HALF_UP)` | **identical** |

The first line means a third independently written harness reproduces the shipped literal. The second
means two harnesses agree at production settings on the configuration that started this whole question.
Neither was assumed; both were compared digit-for-digit.

## Property invariants — all 12 captures pass

Checked mechanically on every capture: principal amortizes to exactly zero; `sum(principal)` equals the
disbursed amount; `sum(interest)` equals `totalInterestAmount`; `sum(total)` equals `totalRepaymentAmount`;
each period's principal + interest equals its total; and disbursed + interest equals total repayment.
**12 of 12 PASS, no exceptions.** These are integer-exact checks on the emitted decimal strings — no
tolerance was applied, because none should be needed.

## Finding — precision sensitivity is a rounding-boundary property, NOT a size threshold

> **CORRECTED by T21 audit (2026-08-18), P0 item 1.** An earlier version of this section claimed precision
> is "load-bearing, but only above a size threshold" — that a 100-unit loan cannot show a p12-vs-p19
> divergence while an 87-million-unit loan does. **The oracle refutes that claim.** The corrected,
> oracle-observed statement follows. Every value below is quoted from the committed oracle transcript
> `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt`; none is re-run or derived here.

`P-00` (the calibration loan at precision **19**) is **identical** to `P-CAL` (the same loan at precision
**12**), every period, every column. But precision sensitivity is a **rounding-boundary property of the
`(principal, n, rate)` triple, not a function of principal magnitude.** The oracle, run at
`MathContext(12, HALF_UP)` vs `MathContext(19, HALF_UP)` with everything else fixed, shows:

- On the `36 × 16.8 %` shape — the shape of `P-MNT-50M` — the two precisions **diverge at principal 4.00**
  (p12 total interest `1.13` vs p19 `1.14`), and diverge again at 59, 72, 340, 426, 6,940 — yet are
  **identical at principal 50,000,000** (`13,995,886.40` on both). Divergence at 4.00 and identity at
  50,000,000 on the *same shape* is the direct contradiction of any size threshold.
- On the `6 × 7.0 %` shape the two are **identical at principal 87,654,321** (`1,798,283.07` on both) and
  at 43,811 and 131,432, but **diverge at 131,433**. The 87-million divergence the old text cited belongs to
  the `18 × 18.5 %` shape (`13,393,481.05` p12 vs `13,393,481.04` p19 — `P-01`), not to magnitude.
- **All four MNT captures are p12/p19-identical** (1,200,000; 4,999,999; 5,000,000; 50,000,000). Pass 3
  therefore supplies **no evidence** that Mongolian loan sizes are precision-sensitive; the earlier sentence
  claiming they are "exactly in the range where it starts to bite" is contradicted by pass 3's own captures.

The port consequence is the opposite of reassuring: **no "small loans are safe" heuristic exists** — a Go
implementation that gets the precision seam wrong can diverge on a 4-unit loan. The conformance corpus must
cover *shape* (number of periods, rate) as deliberately as it covers size. `P-01` is a witness that
sensitivity occurs at realistic sizes; `P-MNT-50M` is a witness that it does not always. Both are in the
corpus, which is correct — the corpus is fine; only the earlier prose about it was wrong.

## The MNT-scale parity candidates

First captures at realistic Mongolian loan sizes. The corpus's largest literal principal anywhere is
`245,000`; these run 5× to 200× beyond it. Recorded as **observed**, never extrapolated.

| Capture | Loan | Term (days) | Total interest | Total repayment |
|---|---|---|---|---|
| `P-MNT-1M2` | MNT 1,200,000 / 12 × 21.6 % | 366 | `144,988.47` | `1,344,988.47` |
| `P-MNT-4M999` | MNT 4,999,999 / 18 × 18.5 % | 547 | `763,994.20` | `5,763,993.20` |
| `P-MNT-5M` | MNT 5,000,000 / 18 × 18.5 % | 547 | `763,994.33` | `5,763,994.33` |
| `P-MNT-50M` | MNT 50,000,000 / 36 × 16.8 % | 1096 | `13,995,886.40` | `63,995,886.40` |

`P-MNT-4M999` and `P-MNT-5M` straddle the MNT 5,000,000 RTGS/ACH+ threshold this program treats as
significant. They are **schedule** vectors, not a payment-rail test — captured so that a later rail
decision has observations on both sides rather than an extrapolation. The threshold itself stays in
config and is never hard-coded.

## Other production-settings observations

- **`P-03` ordering boundary at production settings.** Same shape pass 1 observed at precision 12: a
  zero-valued `REPAYMENT` period 1 dated `2024-02-01` emitted **before** the `DISBURSEMENT` period on the
  same date, real repayments numbered 2..6, totals `1.76` interest on `101.76`. Buyan chose option (a),
  reproduce the oracle's emitted order, so this is the vector that pins it.
- **`P-04f` vs `P-04t`** are identical at production settings too — consistent with pass 2. Captured at
  `true` per G-1 item 5's answer, so the behaviour is documented rather than assumed dormant. Still says
  nothing about multi-disbursement, which Path A cannot express.
- **`P-02` / `P-02b`** month-end re-anchoring reproduces at production precision.

## What this pass does and does not license

**Does:** establish the first parity-candidate corpus at the ratified production settings; re-calibrate
the rig from a third harness; confirm two harnesses agree at `(19, HALF_UP)`; supply the first
MNT-scale observations; and demonstrate all six property invariants hold on every capture.

**Does not:** promote anything into the vector store — pass 3 has not been independently audited, and the
audits of passes 1 and 2 (T18, T19) were still in flight when it was captured. It also inherits Path A's
proven blind spot untouched: `installmentAmountInMultiplesOf` is still dropped, and multi-disbursement is
still unreachable. Buyan's answer to that (expose the field, specify server semantics, **refuse** with
"unsupported: no discriminating vector" until a Path-B vector exists) stands unaffected by this pass.

## Consequence for the existing captures

Per Buyan's ratification note, the pass-1 and pass-2 captures should be **re-labelled `probe`, not
`parity`**, when the vector store is built — with the sole exception of `D-01-p19`, which sits at
production settings and is now corroborated by `P-01`. Pass 3 is the corpus a conformance run should
grade against once audited.
