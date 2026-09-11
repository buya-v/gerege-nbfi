# OH-TDGRADE-BR — Tier D at scale: promote the replayed LoanRepaymentSchedule loans onto the loan seams. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-tdgrade` (branch `feat/OHTDGRADEbr`)
Work ONLY in that directory. **Take no captures. Start no container. No replay.** **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/findings/F-2026-09-11-tierd-mnt-uc6-promotion.md` and the OH-TDMNT-BO finding — how the first four
   Tier D vectors (`LN-TD-*`) were built and admitted. **Copy their shape and provenance exactly.**
2. `.softhouse/capture/tierd-feasibility/repayment-schedule-mnt/OWNER.md`, `summary-repsched.json`, the manifests,
   and `loans/loan-*/` — the per-loan read-backs of the 11 PASSED scenarios of `LoanRepaymentSchedule.feature`
   (MNT, tenant `tierd`, hash-verified by the driver: 402 entries, 0 mismatches).
3. `.softhouse/findings/F-2026-09-11-tierd-repsched-mnt-uc10.md` — UC10: the pinned build returns a period-2 split
   one unit off its own feature table, in EUR as in MNT. **The oracle's output is the observation; the feature
   table is not.** UC10's loan 10 read-back is gradeable like any other — extract it from the MNT replay log with
   `.softhouse/capture/tierd-feasibility/bin/extract.py` if it is not already under `loans/`, and say which.

## The task
Promote vectors from these loans onto EXISTING loan seams — chiefly `loan-schedule-amortization` (the whole
schedule's principal components summing to the disbursed principal) and `loan-schedule-interest` (a period's interest),
plus `loan-disbursement` where a loan has one. **Aim for one vector per distinct scenario shape** (not one per loan
if two loans are the same shape) — roughly 8–15 vectors. Name them `LN-TD-RS-<scenario>-<loan>-…`.
Transcribe only observed values, integer minor units. **Every refusal is a finding: record the rule, never relax it.**

Then: measure every loan drive WITHOUT and WITH the new vectors, and report which newly die. Cross-validation
vectors that kill nothing new are fine — say so plainly; do NOT register a drive to manufacture a kill.

## Non-negotiables
Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify after writing. **No Go change,
no new seam.** **Do not touch `.softhouse/guards/`** (baseline 8 pairs), `.softhouse/conformance.sh`, the capture
files (except adding UC10's extracted read-back, if you extract it, with its manifest line), or `.softhouse/maps/`.
**One bounded context: `loan`.** PostgreSQL only; **Oracle Database is prohibited.** Controls:
`loanschedule-wrong-days-in-year-365` → **48**.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~350 iterations. **Commit after every 2–3 vectors.**
**`git commit -F <file>`. Never commit TASK.md.**
