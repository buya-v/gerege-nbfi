# T27 — independent review of the T25 capture-corpus corrections — handoff

**Task:** T27, branch `softhouse/T27-corpus-corrections-review`, worktree `/home/user/wt-T27`.
**Under review:** T25 commit `f8b9d52` (merged as `0c70c59`).
**Full review:** `.softhouse/reviews/T27-corpus-corrections-review.md`.
**Fire context:** cloud sandbox, **no live Fineract oracle reachable**. No oracle value was synthesized,
invented or extrapolated. Everything is re-derived from the pinned source at `/home/user/fineract`
@ `426a23544` or read from artifacts already committed on `main`.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

Every correction T25 applied is **correct, not merely present** — verified by re-derivation and by mutation
testing, not by agreeing with T25's account:

- All **16** oracle numbers in the rewritten PASS3 "rounding-boundary, not size-threshold" section were
  machine-matched against `t21v2-probe2-oracle-out.txt`. **No unconfirmable number.**
- **Both "fake PASS" defects are genuinely repaired.** I mutated committed captures by one minor unit and
  confirmed the repaired `I5` (Path B) and the replaced `X2` → position-aware `A3` (Path A) now **FAIL**,
  including on `P-03` — proving the new `X2` was not merely disabled for the capture that used to break it.
  The retracted naive `X2` still reproduces its known spurious `P-03` failure.
- **Round-up → round-to-nearest is right**, re-derived from `Money.java:163-171` /
  `ProgressiveEMICalculator.java:1770-1776` in the pinned source, and confirmed numerically with an annuity
  model calibrated against the committed `B-01` EMI: unrounded `111,148.35`, oracle applied `111,100.00`
  (round-up would have given `111,200`).
- **Count fix is right:** 11 captures at `(19, HALF_UP)` + 1 calibration (`P-CAL`) at `(12, HALF_UP)`, counted
  in `capture-prod-raw.json`. `tasks.json` still valid JSON.
- **Retraction banners are unmissable and correctly scoped** — the *oracle* transcript
  `t21-probe-oracle.txt` was correctly left un-retracted.

**Six required changes** (details, file:line and exact fix in the review §5):

1. **RC-1** — T25's edits left `PASS3-REPORT.md:5,114`, `PASS3-REPORT-shared.md:5,114`, `PATHB-REPORT.md:5,128-130,150-151`,
   `tasks.json:188` and `reference-oracle.md:202` self-contradictory: they still say "NOT YET INDEPENDENTLY
   AUDITED" / "not mechanically re-checked" while carrying the audits' own correction banners.
   `PATHB-REPORT.md:150-151` is now **factually false**.
2. **RC-2 — SILENT DROP: T22 P1-12** (state the residual-absorption rule normatively) appears in **neither**
   T25's DONE nor PARKED list. Fully oracle-independent; verified from source at
   `ProgressiveEMICalculator.java:1195-1205` (signed delta).
3. **RC-3 — MIS-PARKED:** T22 **P0-5**, **P1-8** (second half), **P1-9**, **P1-11** (first clause), **P1-14**
   (first clause) were parked `oracle_unreachable` but need **no oracle**. I settled P1-9 and half of P1-8
   here by SHA-256 over already-committed probes (`p05≡p06`, `p07≠p08`, `p09≡B-01`).
4. **RC-4** — `PASS3-REPORT.md:68` dropped T21's annotation that the 131,433 divergence is per-period
   (totals equal at `2696.43`).
5. **RC-5** — `t21v2-probe2-oracle-out.txt`, now the section's sole cited evidence, carries no provenance
   header (its sibling does).
6. **RC-6** — the round-down banner presents the model-derived `111,148.35` as a committed observation.

---

## Outstanding P0 count: **7**

| # | item | oracle needed? |
|---|---|---|
| T21 P0-2 | environment-attestation block on `capture-prod-raw.json` (absent — verified) | yes |
| T21 P0-3 | emit `periodFromDate` / `feeAmount` / `penaltyAmount` + plan totals and re-run (absent — verified) | yes |
| T21 P0-4 | executable pass-3 run recipe with a *failing* seam byte-identity precondition (absent — verified) | yes, to validate |
| T22 P0-3 | machine-readable Path B attestation sidecar (absent — verified) | yes |
| T22 P0-4 | `REPRODUCE.md` preconditions that fail the run (rounding-mode=4, tz, `schema_connection_parameters`) | partly |
| T22 P0-5 | fix `REPRODUCE.md:76` `-o out/B-$n-*-raw.json` glob; capture `%{http_code}` | **no — do it now** |
| T22 P0-6 | re-point Path B at the `gerege` tenant (Asia/Ulaanbaatar, HALF_UP) and re-capture | yes |

---

## The one sentence the driver needs

**No capture may be promoted to the parity vector store today** — seven P0 admissibility items remain open, so
the eleven Path A `(19, HALF_UP)` candidates and the four Path B captures stay *audited observations*, and
`P-CAL` plus every pass-1/pass-2 capture at precision 12 or 8 are **discrimination probes that may never be
promoted as parity vectors at all**.

## What can be done in the next CLOUD (oracle-unreachable) fire

RC-1, RC-2, RC-3, RC-4, and T22 P1-14's from-**source** re-derivation of `B-03`/`B-04` through the DAILY
cross-year partial-period arm (`ProgressiveEMICalculator.java:1400-1414`, `:1550-1568`) — the largest
remaining hole in the Path B evidence, and it needs no running server.

## Non-negotiables

Clean. No float in any money path (the only `float`/prohibited-engine/US-rail hits repo-wide are prohibition
statements in prose); integer minor units throughout; PostgreSQL only; MNT at 2 decimal places; all eleven
parity candidates at `tenantRoundingModeValue = 4`. `go build ./...` and `go vet ./...` exit 0.
Nothing was promoted, ratified, merged or pushed.
