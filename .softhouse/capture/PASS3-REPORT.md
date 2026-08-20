# Capture pass 3 — the first captures at PRODUCTION settings (19, HALF_UP)

**Fire:** local `20260818-152328` (Buyan's Mac), 2026-08-18
**Executed by:** the orchestrator (vector capture touches the oracle, so it is orchestrator-only)
**Status:** RAW OBSERVED, **INDEPENDENTLY AUDITED by T21 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**;
the audit's oracle-independent corrections are applied in this document (see the CORRECTED banners below).
The T21 audit was itself re-checked by T27 (2026-08-18), which machine-verified every corrected number
against the committed oracle transcript.
**No vector promoted to the store; no gate answered.**

> **SUPERSEDED FOR ADMISSIBILITY PURPOSES BY PASS 3b — `PASS3B-REPORT.md` (T35, 2026-08-18).**
> The three P0 admissibility items this document used to list as open — T21 §10 **P0-2** (attestation
> block), **P0-3** (the missing `periodFromDate` / `feeAmount` / `penaltyAmount` columns and the plan
> totals), **P0-4** (the executable run recipe) — plus **P1-9** (`toPlainString()`, stack frames on the
> error branch) are **CLOSED**, against a live run of the pinned image on a local oracle-reaching fire.
> Pass 3b re-runs the SAME twelve cases through the SAME seam: **1560 of 1560 values pass 3 published are
> byte-identical, 0 changed**, and `capture-prod-raw.json` itself reproduced byte for byte
> (`sha256 11c5c74a…a732e2`) on that fire. **This document and its capture are unchanged and remain
> valid**; the admissible-form artefacts are `out/capture-prod3b-raw.json` and its sidecar
> `out/capture-prod3b-attestation.json`. **Still nothing is promoted** — see `PASS3B-REPORT.md` §6 for
> what continues to block the eleven `(19, HALF_UP)` records.

> ## `out/capture-prod-raw.json` IS **NON-PROMOTABLE** — SUPERSEDED, NOT DOUBTED
>
> **Recorded by task T74, 2026-08-20, after checking the claim rather than repeating it.**
>
> **No vector in `.softhouse/vectors/` derives from this capture, and none ever did.** T74 read every
> file in `.softhouse/vectors/loanschedule/` and resolved each one's `provenance.capture_ref`: 36
> parity vectors, naming `capture-prod3b-raw.json` (11), `capture-prod3c-raw.json` (2),
> `capture-prod3d-raw.json` (2), `capture-prod3e-raw.json` (14), `capture-prod3f-raw.json` (3) and
> `capture-prod3g-raw.json` (4); plus 4 `contract-refusal` vectors, which carry no capture at all.
> **`capture-prod-raw.json` appears nowhere**, in a `capture_ref` or anywhere else in any vector file.
>
> **The consequence, and it is the point of this banner.** T21 §10 **P0-2** (no attestation block),
> **P0-3** (no `periodFromDate` / `feeAmount` / `penaltyAmount`) and **P0-4** (no executable run recipe)
> were filed as items that *block promotion of a pass-3 capture*. Since nothing was ever promoted from
> one, they are **record hygiene, not promotion blockers**. Pass 3b already carries the attestation
> block and all three columns, and says so in the artefact itself
> (`"supersedes": "Capture3.java / capture-prod-raw.json — same twelve cases; adds attestation,
> periodFromDate, feeAmount, penaltyAmount, plan totals, toPlainString"`). **Pass 3 must NOT be re-run to
> retrofit fields into a superseded capture**; that would spend an oracle run to improve an artefact
> nothing reads.
>
> **P0-4 is closed for real, and not here.** The executable Path A recipe with the seam byte-identity
> check as a *precondition step that exits non-zero* — not a prose instruction — and with the log/JSON
> split built in is `.softhouse/capture/src/run-pass3i.sh`, whose lineage runs back through
> `run-pass3h.sh` … `run-pass3b.sh`. T74 falsified its guards rather than asserting them: a mutated seam
> in the repo fails precondition 4; a mutated seam in **both** copies with `git update-index
> --assume-unchanged` silencing the checkout — which defeats preconditions 3 and 4 together — fails the
> literal-digest precondition 4b added by pass 3i. Both transcripts are in the T74 handoff.
>
> **Every NUMBER in this document stands.** T21 reproduced the capture byte for byte, re-derived all
> twelve cases from the pinned Fineract source to the minor unit, and confirmed all six property
> invariants integer-exact. Pass 3b then re-observed the same twelve cases and matched **1560 of 1560**
> published values. This banner marks the FILE as an artefact nothing may be promoted from. It does not
> retract a single value in it, and the file stays on disk as the audited historical record.
>
> The mark also lives in `.softhouse/vectors/PIN.json`'s `note` and in `.softhouse/vectors/README.md`.
> It is deliberately **not** an entry in `PIN.json`'s `never_promotable_capture_case_ids`: that list is
> typed as *capture case ids* and consumed as such (`admit.go:603`, matched against
> `provenance.capture_case_id`), and the pin file's schema is closed by `DisallowUnknownFields`
> (`admit.go:60-66`), so a whole-file mark has no admissible home there. Pass 3's twelve case ids are
> shared with pass 3b, so denylisting them by id would wrongly refuse eleven already-promoted vectors.


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
  at 43,811 and 131,432, but **diverge at 131,433** — and that divergence is **per-period; the two
  total-interest figures are equal at `2696.43`** (the transcript's `IDENTICAL`/`DIFFERENT` verdict is a
  **full-schedule** string comparison, `T21v2Probe2.java:63-66`, not a totals comparison — T21 §6.2's own
  annotation, restored here per T27 RC-4). The 87-million divergence the old text cited belongs to
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

**Does not:** promote anything into the vector store. Pass 3 **has** since been independently audited — T21
(2026-08-18) ACCEPTED WITH REQUIRED CHANGES, and T27 re-checked that audit's corrections. The three P0
admissibility items that used to be open here (T21 §10 P0-2/P0-3/P0-4: no environment-attestation block on
`capture-prod-raw.json`, the per-period `periodFromDate`/`feeAmount`/`penaltyAmount` columns not emitted, no
executable run recipe) were **closed by T35 in pass 3b** — see `PASS3B-REPORT.md`. Closing them did **not**
promote anything: DEC-1 is at revision 6 and UNRATIFIED (gate G-1), and the seam's blind spots are unchanged,
so the eleven `(19, HALF_UP)` records remain **attested observations, not promoted parity vectors**.
(Pass 3 was captured while the audits of passes 1 and 2 — T18, T19 — were still in flight.) It also inherits
Path A's
proven blind spot untouched: `installmentAmountInMultiplesOf` is still dropped, and multi-disbursement is
still unreachable. Buyan's answer to that (expose the field, specify server semantics, **refuse** with
"unsupported: no discriminating vector" until a Path-B vector exists) stands unaffected by this pass.

## Consequence for the existing captures

Per Buyan's ratification note, the pass-1 and pass-2 captures should be **re-labelled `probe`, not
`parity`**, when the vector store is built — with the sole exception of `D-01-p19`, which sits at
production settings and is now corroborated by `P-01`. Pass 3 is the corpus a conformance run should
grade against once audited.
