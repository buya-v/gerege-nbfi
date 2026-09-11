# Reproducing capture pass 3j (Path A) — the executable recipe

**Pass 3j is pass 3i's rig with one new case group**, exactly as pass 3i is pass 3h's. Everything
`README-pass3b.md` and `README-pass3i.md` say about the shape of the recipe — preconditions, output
paths, attestation, the log/JSON split — applies here unchanged. This file records only what
differs.

> "The oracle" is the Fineract reference implementation this program grades Go output against.
> Oracle Database is a prohibited product here. PostgreSQL is the only permitted database; this
> seam is a library call and opens no database connection at all. The recipe writes nothing to the
> running reference-oracle container, its PostgreSQL database, its `c_configuration` or any tenant.
> A parallel run holding that container is not touched by this seam.

## Run it

From the repo root:

```sh
sh .softhouse/capture/src/run-pass3j.sh
```

Optional environment: `PINNED_FINERACT`, `CAP_OUT_DIR`, `REF3B_JSON`, `REF3C_JSON`, `REF3E_JSON`,
`REF3G_JSON`.

It is a script, not a prose instruction: the seam byte-identity check exits 1 on breach, the
log/JSON split is built in (`grep -n '^{'` → `head`/`tail`, never a manual edit), and the
attestation sidecar is written by the same run that produced the capture.

## What differs from pass 3i

**Every precondition of pass 3i is kept and not one is weakened** — the image id, the pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, the clean checkout, the `cmp` byte identity, the
LITERAL seam sha256 `bf397f0b…`, the four calibration references and their literal sha256s, the
path-identity and mechanism columns, field separation (16), the hand-written precision table (17)
and the `-p12` classification (18). All **nine** rig calibrations are carried over unchanged, so the
pass still proves the rig reproduces the committed observations it inherited; all thirty-six of pass
3i's cases are carried over unchanged, so its preconditions 16/16b/17/18 keep every witness they
had. The additions are three cases and their three table entries.

One thing about the harness body differs, and it is forced by the bar rather than chosen: the three
handlers that wrap a measured seam call inside `Capture3j.java` were widened from
`catch (RuntimeException e)` to `catch (Throwable e)`. `java.lang.Error` — including the
`StackOverflowError` the reference `ProgressiveEMICalculator` is documented to throw on some inputs
(`ThrewOutcome.java`) — is not a `RuntimeException`, so a narrow handler silently converts a thrown
outcome into no outcome at all. `Capture3i.java` is in the narrow-catch lint's FROZEN set (it
produced committed evidence, so T114's standing ruling forbids editing it); a **new** rig is not, so
`guard_no_narrow_catch_in_capture_rigs` refused `Capture3j.java` until this was fixed. Only the
caught type changed: every handler body is byte-for-byte pass 3i's, so on the success path this
pass emits exactly the bytes pass 3i emitted. The re-run proves it — the canonical digest is
identical to the pre-fix run's, and all nine calibrations still reproduce cell for cell.

| # | check | source |
|---|---|---|
| 1–18 | identical to pass 3i, all carrying over | pass 3i (and earlier) |
| — | `EXPECTED_IDS` gains `LSCAP-DISB-P1`, `LSCAP-DISB-P3`, `LSCAP-DISB-BND` — 39 captures | pass 3j |
| — | `CASE_PRECISION` gains those three at 19 (hand-written, not defaulted) | pass 3j |
| — | `FIELD_SEPARATION` gains those three as `(2, None, None)` — the `prodDates` arm | pass 3j |

The three new ids do **not** end in `-p12`, so precondition 18 leaves them in
`parityCandidateCaptureIds`, not in `discriminationProbeCaptureIds`. The sidecar confirms it.

## Why this pass exists

Finding `F-2026-09-11-loanschedule-graded-coverage` §5.2. The committed loanschedule corpus reaches
every reference money rule **except one reachable path**: the Go port's `emi.go:1529`, the
`inPeriodM1` **non-first** arm. `inPeriodM1` is the M1 membership predicate `(FromDate, DueDate]`,
used by `findPeriodForBalanceChange` (`emi.go:1546`) to decide which repayment period a balance
change — here a disbursement — registers into. The first arm covers period 0; the non-first arm
fires only for a balance change dated in a **later** repayment period.

All fifty committed vectors disburse within period 0. The largest offset is `P-03`, disbursed
`2024-02-01`, which is period 0's *own* `DueDate` and therefore still period 0 under M1's inclusive
`<=`. `REFUSE-04` disburses on or after maturity and is refused by `generator.go:404-408`. **No
capture had a disbursement strictly after the first due date and before the last.**

## Group F — later-period disbursement

Three single-disbursement MNT loans, built with the existing `prodDates(...)` helper at the
production settings it already uses (MathContext precision 19, HALF_UP, tenant rounding ordinal 4,
DAYS_30 / DAYS_360, DECLINING_BALANCE, no down payment, no multiples-of). All three hold the loan
fixed — schedule start `2024-01-01`, 6 monthly repayments, principal **101,463,237 minor units**
(MNT 1,014,632.37, a deliberately non-round minor unit) at **7.0 %** per annum — and move **only**
the disbursement date:

| id | disbursed | where that is |
|---|---|---|
| `LSCAP-DISB-P1` | `2024-02-15` | strictly inside period 1 (window `2024-02-01`..`2024-03-01`) |
| `LSCAP-DISB-P3` | `2024-04-10` | strictly inside period 3 (window `2024-04-01`..`2024-05-01`) |
| `LSCAP-DISB-BND` | `2024-03-01` | exactly ON the second due date — period 1's `DueDate`, so M1's inclusive `<=` puts it in period 1; the boundary the triage names |

Contrast `P-03` (`2024-02-01`), which is period 0's `DueDate` and so remains period 0. These are the
shapes a grading run needs to reach the `emi.go:1529` non-first arm.

## What the pass found

**Nothing was refused and no schedule is all-zero.** All three cases generated cleanly at
`(19, HALF_UP)`, `stderr` is empty, and every amount below is the oracle's own emission quoted in
minor units.

| id | term (days) | total interest | total repayment | first disbursement row |
|---|---|---|---|---|
| `LSCAP-DISB-P1` | 182 | 1,493,428 | 102,956,665 | `2024-02-15` |
| `LSCAP-DISB-P3` | 182 | 1,007,438 | 102,470,675 | `2024-04-10` |
| `LSCAP-DISB-BND` | 182 | 1,483,976 | 102,947,213 | `2024-03-01` |

`LSCAP-DISB-P1` shows repayment period 1 (`dueDate 2024-02-01`) all-zero, then a `DISBURSEMENT`
row dated `2024-02-15`, then periods 2–6 amortizing — the disbursement lands inside period 1 and is
recognised there. `LSCAP-DISB-P3` is the deeper case: periods 1, 2 and 3 are all-zero, the
`DISBURSEMENT` row is dated `2024-04-10`, and periods 4–6 amortize. `LSCAP-DISB-BND` disburses on
`2024-03-01`: periods 1 and 2 are all-zero, the `DISBURSEMENT` row is dated `2024-03-01`, and
period 3 onward amortizes. This capture predicts nothing; it records what the oracle emitted.

## Verifying a re-run

Compare **`capturesCanonicalSha256`** in `out/capture-prod3j-attestation.json`:

```
2c2f1e4241e8af9794b5e5d56a68451f71805b0290c66717cc07167651e6b671
```

Stable across runs; the whole-file digest is not, because the attestation carries a UTC timestamp.
The run also writes `out/capture-prod3j-sha256.txt` over every output.

## Provenance of this run

* image `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`
* pinned Fineract `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (clean)
* harness `Capture3j.java`, seam class byte-identical to the pinned original,
  `seamClassSha256 = bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`
* 39 captures; effective MathContext `(19, HALF_UP ordinal 4)`; all nine rig calibrations reproduced
  their committed observations cell for cell.

**Nothing here is promoted to the parity vector store.** That is a separate gated decision; this
pass only produces the capture a later grading run works from.
