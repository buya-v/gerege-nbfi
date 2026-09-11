# OH-WOGRADE2-BE — a second write-off observation, on the existing seams. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wograde2` (branch `feat/OHWOGRADE2be`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver
pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/loan.md` — the seams `loan-writeoff-four-bucket` and the write-off journal seam, their
   vectors `LN-L11-writeoff-four-bucket-discharge.json` and `LN-L11-writeoff-journal-five-legs.json`.
2. `.softhouse/capture/loan-writeoff-paid-instalment/OWNER.md` — loan 13: one instalment complete, the
   write-off txn L57 = 9211512 / 561853 / 10000 / 5700 = 9789065, and five JE legs.

## The task — no port change, no new seam
Promote TWO vectors from loan 13, near-copies of the two LN-L11 write-off vectors:
* `LN-L13-writeoff-four-bucket-discharge.json` — request: the twelve instalments of the AFTER-REPAY schedule
  (`out/loan-13-after-repay-detail-raw.json`), with period 1 carrying `obligations_met: true` and its OBSERVED
  outstanding (0/0/0/0) — **transcribe the observed state; never combine a pre-repayment outstanding with a
  post-repayment flag** (the driver ruled that a synthesised input). Expect: the four portions of txn L57.
* `LN-L13-writeoff-journal-five-legs.json` — the five L57 legs, with product 3's mapping as LN-L11's vector
  cites it.

Measure every existing write-off drive (`loan-wrong-writeoff-*`, `loan-wrong-writeoff-journal-*`) WITHOUT and
WITH the two vectors and report the counts. **Register no new drive** unless a new vector kills one the old
corpus could not — and the ObligationsMet skip is inert by construction (recorded on the merge of
OH-WOPAID-AU): do NOT register a skip drive.

## Measuring
`kills.sh loan <impl> <worktree>`; controls `loanschedule-wrong-days-in-year-365` → **48**,
`parties-wrong-iota-ordinals` → 12. An empty result means the measurement FAILED.

## Non-negotiables
- Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, captures, or `.softhouse/maps/`.**
- **One bounded context: `loan`.** PostgreSQL only; **Oracle Database is prohibited.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **Commit by iteration 60.**
**`git commit -F <file>`. Never commit TASK.md.**
