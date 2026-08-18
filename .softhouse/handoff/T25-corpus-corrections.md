# T25 — corpus corrections (oracle-independent slice) — handoff

**Task:** T25, branch `softhouse/T25-corpus-corrections-oracle-indep`, worktree `/home/user/wt-T25`.
**Fire context:** cloud sandbox, **no live Fineract oracle reachable.** This slice does ONLY the
oracle-independent corrections carried by the T21 and T22 audits; every item needing a fresh oracle re-run is
PARKED with reason `oracle_unreachable`.

**Honesty invariant held:** no oracle value was synthesized, derived, or invented. Every number cited in a
correction is quoted from an artifact already committed on `main` (named per item below). Nothing was promoted
to the parity/vector store — this slice corrects the RECORD only.

---

## DONE — oracle-independent corrections applied

### T21 P0 item 1 — refuted precision "size-threshold" finding (both PASS3 reports)
- **Files:** `.softhouse/capture/PASS3-REPORT.md` and `.softhouse/capture/PASS3-REPORT-shared.md`
  (still byte-identical after edit; `diff` exit 0).
- **Before:** §"Finding — precision is load-bearing, but only above a size threshold" — claimed a 100-unit loan
  cannot show a p12-vs-p19 divergence while an 87M-unit loan does; "precision changes the schedule once the
  principal is large enough…"; "this matters directly for Mongolia, where ordinary principals are exactly in
  the range where it starts to bite."
- **After:** §"Finding — precision sensitivity is a rounding-boundary property, NOT a size threshold", with a
  CORRECTED banner and the oracle-observed statement: divergence at principal **4.00** on `36 × 16.8 %`
  (p12 `1.13` / p19 `1.14`) but **identical at 50,000,000** on that same shape; identical at **87,654,321** on
  `6 × 7.0 %` (`1,798,283.07` both) with first divergence on that shape at 131,433; the 87M divergence belongs
  to `18 × 18.5 %` (`13,393,481.05`/`.04` = `P-01`); **all four MNT captures p12/p19-identical**; no
  "small loans are safe" heuristic exists.
- **Evidence cited (committed):** `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt` (17 oracle rows;
  every value above is present in that file, verified line-by-line).

### T21 P1 item 5 — retract defective probe scripts + fix invariants X2
- **Retraction banners added** (files kept on-disk as a record, prefixed with a RETRACTED banner pointing at
  `T21-capture-pass3-audit.md` §9):
  - `.softhouse/capture/out/t21-probe-threshold.py`
  - `.softhouse/capture/out/t21-probe-rederive.py`
  - `.softhouse/capture/out/t21-probe-rederive2.py` (companion sharing the same defective model — the review
    names `t21-probe-rederive.py`; `rederive2` is the same author's part-2 and shares the defect, so it is
    retracted too. Its date-sequence / P-03 structural readings were CONFIRMED by the audit and that is noted
    in its banner.)
  - `.softhouse/capture/out/t21-probe-threshold-output.txt`, `…-rederive-output.txt`,
    `…-rederive2-output.txt` — each prepended with a plain-text RETRACTED banner (outputs of a defective
    model; not the oracle's answer).
- **`.softhouse/capture/out/t21-probe-invariants.py` fixed:**
  - Docstring corrected to state X1/X2 are **the author's own additions, NOT part of the six invariants**.
  - `X2` replaced with the position-aware roll-forward (the audit's `A3`): walk periods in emitted order,
    DISBURSEMENT adds, REPAYMENT subtracts and must equal that row's `balance`. The old X2 seeded at
    `disbursed` and spuriously failed P-03 (pre-disbursement snapshot row).
  - **Verified:** re-ran against `.softhouse/capture/out/capture-prod-raw.json` → all 12 captures PASS all of
    I1..I6, X1, X2 (P-03 now passes X2). Output confirms `ALL PASS`.

### T21 P1 item 6 — tasks.json miscount
- **File:** `.softhouse/tasks.json` (the T8 note, formerly "tasks.json:188").
- **Before:** "Pass 3 … 12 captures at PRODUCTION settings (19, HALF_UP), the first parity candidates. …
  All 12 pass all six property invariants."
- **After:** "**11** captures at PRODUCTION settings (19, HALF_UP) plus **ONE** calibration (P-CAL) at
  (12, HALF_UP) — 12 records in total, 11 parity candidates, P-CAL calibration only…"; and "All 12 records
  pass all six property invariants, **INDEPENDENTLY re-checked by the T21 audit** (not merely claimed by the
  capturing orchestrator)." JSON re-validated (`json.load` OK). Only the note text changed; structure intact.

### T21 P1 item 7 — RESUME.md threshold claim → **ALREADY CORRECT, SKIPPED (as instructed)**
- `.softhouse/RESUME.md` line 38 already states the size-threshold claim is **refuted** (principal 4.00
  divergence; none at 50M/87.65M; all four MNT p12/p19-identical). No "unaudited" text describing the
  threshold exists anywhere in RESUME.md (`grep -i unaudited` → no match). Line 44 already flags the defective
  scripts for retraction (T25). The orchestrator had already rewritten it; per the task's own instruction I did
  not fight the orchestrator for that file. **No change made.**

### T22 (oracle-independent items only)
- **P1 item 13 — I5 hard-coded to PASS (named item).** `.softhouse/capture/pathb/t22-probe/invariants.py`:
  the `verdict("I5", True, …)` that could never fail is replaced with a genuinely failable check driven by an
  `i5_fail` list; a DEFECT-CORRECTED docstring banner points at `T22-pathb-capture-audit.md` §9/§10 P1-13.
  **Verified:** re-ran against `pathb/out/B-01-baseline-raw.json` → `I5 … (0 break(s)) PASS`, `OVERALL: PASS`.
- **P1 item 13 (second clause) — misleading `halfeven` filename tag.** Added
  `.softhouse/capture/pathb/t22-probe/PROVENANCE-NOTE.md` recording that the `halfeven` tag names the mode the
  prior worker *discovered* (`c_configuration.rounding-mode = 6`), not a variant that was *run* — no script
  there changes the rounding mode — and that `invariants.py` was defective and is now fixed.
- **P0 item 1 — false round-up rule (refuted-claim fix).** `.softhouse/capture/pathb/PATHB-REPORT.md` Result 2:
  the sentence "The EMI is raised to the next multiple of 100" is corrected to "rounded to a multiple of 100",
  with a CORRECTED banner stating the true rule: round to the **NEAREST** multiple of
  `installmentAmountInMultiplesOf` under the **tenant rounding mode** (`ProgressiveEMICalculator.java:1770-1776`
  → `Money.java:163-171`) with a zero-guard. Cites the committed round-**down** observation
  `.softhouse/capture/pathb/t22-audit/out-rounddown/rounddown-gerege-raw.json` (principal 1,190,000: unrounded
  `111,148.35` → `111,100.00`) — verified that file is committed/tracked.
- **P0 item 2 — captures ran at HALF_EVEN (record correction).** `PATHB-REPORT.md` "not asserted" caveat
  corrected: the four captures ran on the `default` tenant at **HALF_EVEN** (rounding-mode 6), not HALF_UP; the
  mode is live on this path (`20,925.05` vs `20,925.04`); the four are mode-insensitive **only** on the strength
  of the committed fresh-tenant re-observation (`t22-audit/out-fresh-tenant/`, four identical SHA-256), not by
  assumption; still not production-settings parity vectors until the parked attestation/re-point items close.
- **P1 item 7 — FULL_LEAP_YEAR ≡ field-unset (documentation fix).** `PATHB-REPORT.md` Result 3 caveat: added a
  CLARIFIED banner that the two enum values are NOT symmetric — `FULL_LEAP_YEAR` is behaviourally identical to
  the field being unset (`DaysInYearType.java:81-86`), so `FEB_29_PERIOD_ONLY` alone discriminates and `B-04`
  is the only vector with power over the field; can only bite under DAILY + ACTUAL. Sourced from the committed
  T22 audit §5.

---

## PARKED — oracle-dependent, reason `oracle_unreachable`

These require a live/running reference oracle (Fineract) that this cloud sandbox cannot reach. The next
oracle-reaching (local) fire must pick them up. None was attempted; no value was synthesized.

**T21:**
- **P0 item 2** — attach the environment-attestation block to `capture-prod-raw.json` (Fineract commit, image
  digest, jar `git.properties`, in-container JVM string, classpath/source SHA-256s, runtime
  `MoneyHelper.PRECISION`, per-capture tenant rounding mode, capture-path label, UTC timestamp). Requires values
  read from a live container. `oracle_unreachable`.
- **P0 item 3** — emit `periodFromDate`, `feeAmount`, `penaltyAmount` (+ plan-level totals) and **re-run**
  `Capture3.java` in the pinned image. Re-capture. `oracle_unreachable`.
- **P0 item 4** — commit an executable pass-3 run recipe with the seam byte-identity check as a failing
  precondition; only meaningfully validated by running it against the oracle image. `oracle_unreachable`
  (the script could be drafted blind, but its correctness cannot be verified here and it is coupled to the
  re-run in item 3 — parked with items 2/3 so one oracle fire closes them together).
- **P1 item 8** — fix the harness to separate `CurrencyData.inMultiplesOf` from
  `installmentAmountInMultiplesOf`, then **capture** the `decimalPlaces == 0` multiples-of behaviour. Requires a
  capture. `oracle_unreachable`.
- **P1 item 9** — switch `BigDecimal` emissions to `toPlainString()` and print stack-trace frames on the error
  branch, then **re-run** so the artifact reflects it (audit `A5` confirms no present value is affected).
  Coupled to the re-run. `oracle_unreachable`.
- **P1 items 10, 11** — item 10 (record CurrencyData input deviation; P-03 `loanTermInDays`/emission-order
  mechanism notes) is arguably pure-text, but is source-descriptive documentation the audit already fully
  states; item 11 (add the `36 × 16.8 %` small-principal shape to the capture plan and capture it) needs a
  capture. Item 11 → `oracle_unreachable`. **Item 10 → NOT done in this slice** (out of the explicitly listed
  T25 items; low-risk, left for the same fire that does the re-run so the report's P0/P1 close as one edit).

**T22:**
- **P0 item 3** — attach a machine-readable attestation sidecar per Path B capture set. `oracle_unreachable`.
- **P0 item 4** — make `REPRODUCE.md` preconditions fail the run and add rounding-mode + timezone +
  `schema_connection_parameters` assertions. The assertions are tied to running the recipe against the oracle;
  parked with the re-point. `oracle_unreachable`.
- **P0 item 5** — fix the capture loop's `-o out/B-$n-*-raw.json` glob and capture `%{http_code}`. Coupled to
  a re-run of the capture recipe on the oracle. `oracle_unreachable`.
- **P0 item 6** — re-point Path B at a production-settings tenant (`gerege`, Asia/Ulaanbaatar, HALF_UP) and
  stop capturing on `default`; requires the running server. `oracle_unreachable`.
- **P1 items 8, 9, 11, 14** — record day-count preconditions from probes / add server-path citations already
  present in the committed audit are partly text, BUT items 11 (capture a vector forcing the EMI re-adjust loop
  to iterate) and 14 (independently re-derive B-03/B-04 — needs the DAILY cross-year arm) and 9/8 rest on probe
  captures. The capture-bearing ones → `oracle_unreachable`. Pure-text citation adds (P1-10, server-path line
  refs) were **not** applied in this slice — they are additive documentation the audit already records and were
  outside the explicitly-listed T25 items; left for the report's full close on the next fire.

---

## [UNVERIFIED] / missing-file notes

- **No missing files.** Every file named in the T21 review §10 and the T22 review §10 that this slice needed
  was present in the worktree: `t21-probe-threshold.py`, `t21-probe-threshold-output.txt`,
  `t21-probe-rederive.py`, `t21-probe-invariants.py` (plus `t21-probe-rederive2.py`/outputs),
  `t22-probe/invariants.py`, `PASS3-REPORT.md`, `PASS3-REPORT-shared.md`, `PATHB-REPORT.md`,
  `t22-audit/out-rounddown/rounddown-gerege-raw.json`, `t22v2` transcript
  (`.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt`), `tasks.json`, `RESUME.md`.
- **No `[UNVERIFIED]` values were introduced.** Every oracle number in every correction was confirmed present
  in a committed artifact before citing it (probe2 transcript re-grepped; round-down JSON confirmed tracked via
  `git ls-files`). No correction relies on a value this slice could not confirm against a committed file.
- **Scope note for the reviewer (T27):** this slice deliberately did NOT apply the additive/pure-text
  documentation sub-items (T21 P1-10, T22 P1-10 server-path citation refs) that are not in the explicit T25
  list and are cleanest folded into the same edit as the oracle re-run that closes each report's P0 list. They
  are recorded above so nothing is silently dropped.
