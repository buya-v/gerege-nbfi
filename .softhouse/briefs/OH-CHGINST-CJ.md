# OH-CHGINST-CJ — charges: grade the "% loan amount + interest" INSTALMENT fee per period. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-chginst` (branch `feat/OHCHGINSTCJ`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Everything you need is named below. **Do not read findings, maps or other vectors beyond what is listed. Start
writing within 20 iterations. Commit after the first vector passes.** One bounded context: `charges`.

## The property (one)
The charges seam `charge-evaluate` today REFUSES an interest-based calculation type
(`nexus/internal/apps/charges/conformance/admit.go:128-133`; `impl.go:221-241` `feeFor` returns ok=false): "not
computable from a base amount alone". For an INSTALMENT fee (`time_type` 8) it IS computable from the period:
`LoanRepaymentScheduleProcessingWrapper.getInstallmentFee` / `getBaseAmount`
[`/Users/buv/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/LoanRepaymentScheduleProcessingWrapper.java:212-234`,
read-only, pinned 426a23544]: base = the period's principal + the period's interest charged for
PERCENT_OF_AMOUNT_AND_INTEREST (calculation type 3); fee = base × percentage / 100, rounded HALF_UP to the currency's
minor unit when it is added to the Money accumulator (`Money` constructor setScale, `Money.java:52`) — i.e. exactly
`charges.PercentageOf` (`nexus/internal/apps/charges/money.go:48`) of (principal + interest). No min/max cap is
applied on this path (the observed charge has none).
Extend the seam: add `interest_amount_minor` (the PERIOD's interest) to `ChargeRequest` (`vector.go:100-114`, next
to `base_amount_minor`, which carries the PERIOD's principal); in `admit.go` admit calculation type 3 ONLY with
time_type 8, both amounts present, and no caps; in `feeFor` compute `PercentageOf(base + interest, percentage)`.
PERCENT_OF_INTEREST (type 4) is NOT observed: it stays refused. Every existing vector must keep passing unchanged.

## Drive
ONE drive `charges-wrong-instalment-interest-ignored` in `nexus/internal/apps/charges/conformance/impl.go` (model on the
drives at `impl.go:457-560`; register the same way): computes the type-3 fee from the principal alone.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/charges-installment-fee-mnt/` (read its OWNER.md header, ~30 lines). The charge from the loan read-back's `charges[]` entry whose
`chargeTimeType.code` ends `instalmentFee` (`percentage` 1.0 = 1%, encode it the way `FC-09-pctamount-instalment-p2.json`
does: micro-per-cent 1000000); the period's `principalDue`, `interestDue`, `feeChargesDue` from
`repaymentSchedule.periods[]` of the same file. Currency MNT.
| vector | read-back (sha256) | period | principal + interest → fee | why |
| --- | --- | --- | --- | --- |
| TD-CHG-loan-6-pct-amount-interest-p1 | `loans/loan-6/loan-6-detail-associations-all-1.json` (be587349…ca37) | 1 | 16.41 + 0.59 → 0.17 | principal alone would give 0.16 |
| TD-CHG-loan-6-pct-amount-interest-p6 | same file | 6 | 16.94 + 0.10 → 0.17 | 0.1704 HALF_UP |
| TD-CHG-loan-3-pct-amount-p2 | `loans/loan-3/loan-3-detail-associations-all-1.json` (f97f890f…1b03) | 2 | principal 16.54 → 0.17 (type 2, existing path, interest NOT added) | 0.1654 HALF_UP; truncation gives 0.16 |
Copy the shape and provenance of `.softhouse/vectors/charges/FC-09-pctamount-instalment-p2.json`, but provenance names
the THROWAWAY tenant `tierd`, image `sha256:e596339626bf…`, Asia/Ulaanbaatar, rounding 4, feature
LoanChargesInstallmentFee.feature. Raw bodies carry decimal major units — convert to integer minor units by exact decimal
parsing, never float. If an observation cannot be reproduced from the observed inputs, THAT is the finding — stop.

## Deliver
The extended seam, three vectors, the one drive; the capability entry in `.softhouse/capabilities-charges.json`
(`percent-amount-interest-instalment-fee`, `in_graded_domain: true`). Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh charges charges-wrong-instalment-interest-ignored <worktree>`: ≥1 with, 0 without),
and the control `charges-wrong-rounding-half-even` must still read 1. `capcount.sh <worktree> charges charges-go` must
be 0. Coverage of `feeFor` from the committed-store test (`-count=1`).

## Non-negotiables
Integer minor units; no float anywhere, including parsing. `capture_ref` a JSON record + `capture_sha256`. **Do not
touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps, or any other context. PostgreSQL
only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
