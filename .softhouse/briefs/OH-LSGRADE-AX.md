# OH-LSGRADE-AX — grade the later-period disbursement from pass 3j. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lsgrade` (branch `feat/OHLSGRADEax`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver
pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/loanschedule.md` — vectors, admission, drives (8, in `cmd/conformance/impl_hook.go`).
2. `.softhouse/findings/F-2026-09-11-loanschedule-graded-coverage.md` §5.2 — the target.
3. `.softhouse/capture/README-pass3j.md` — the capture.

## The observation — committed, and driver-verified (all 6 output hashes OK)
`.softhouse/capture/out/capture-prod3j-raw.json`, cases `LSCAP-DISB-P1`, `LSCAP-DISB-P3`, `LSCAP-DISB-BND`
(start 2024-01-01, 6 monthly, 7.0%, MNT 1,014,632.37; disbursed 2024-02-15 / 2024-04-10 / 2024-03-01).
The oracle emits a zero pre-disbursement period, the disbursement, then partial-period interest
(e.g. P1 period 2 interest 3061.39). **Verify every cell against the file.**

## The task — ONE property
> **A disbursement dated inside a LATER repayment period registers into that period: earlier periods are
> zero, and interest accrues only from the disbursement date.**

Promote THREE vectors, one per case, each a faithful transcription of the whole observed schedule, in
exactly the form the existing parity vectors use. **Template: `.softhouse/vectors/loanschedule/
P-03-disbursement-on-repayment-due-date.json`** — the nearest committed shape (a disbursement not on the
start date). Copy its structure, its provenance fields and its attestation references; change the inputs
and the expected periods. The admission rules (`conformance/admit.go`, `GradedDomain`) are strict and
correct — **if a case is refused, the refusal is a finding: report which rule, do not relax it.**

**Measure** with the committed-store test (`-count=1`) that `emi.go:1529` (the `inPeriodM1` non-first
arm) is now reached. And run every loanschedule drive against the store WITHOUT and WITH the three
vectors — if none of the existing 8 newly dies on them, consider ONE drive: a port that registers a
later-period disbursement into period 0 (the first-arm-only reading of M1). Register it only if a new
vector kills it; measure it both ways.

## Measuring — THIS binary is different
`kills.sh loanschedule <impl> <worktree>` — this binary REJECTS `-root` and gates its verdict on
`-oracle-probe`; the tools handle both (repaired 2026-09-11). Controls: `loanschedule-wrong-days-in-year-365`
→ 45, `loanschedule-wrong-half-even` → 5. **An empty result means the MEASUREMENT FAILED.**

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; transcribe the capture's decimal strings exactly. No float anywhere.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. HALF_UP, precision 19.
- **Do not touch `.softhouse/guards/`** (12 pairs), `.softhouse/conformance.sh` (census **17**), the capture
  files, or `.softhouse/maps/`. "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- `capture_ref` must be the JSON capture record; `capture_sha256`; **re-verify after writing**.
- **One bounded context: `loanschedule`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure.** Note the loanschedule parity
count in the bar line (46 today) must rise by the vectors you add. ~400 iterations. **Commit by iteration
120.** **Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
