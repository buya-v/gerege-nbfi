# OH-WOPAID-AU — CAPTURE ONLY. Write off a loan that has a FULLY PAID instalment.

Worktree: `/Users/buv/oh-gerege-wopaid` (branch `feat/OHWOPAIDau`)
Work ONLY in that directory. **You hold the oracle.** A parallel run (`OH-ORIGCOV-AT`) grades from
COMMITTED captures only and will not touch the oracle.

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout — do not
read or write there, and **never exercise the push gate**. The driver pushes.

## Read first — do not search
1. `.softhouse/maps/loan.md` — every loan capture, its OWNER title, and what the vectors cite.
2. `.softhouse/capture/loan11-writeoff-four-bucket/OWNER.md` — **the previous write-off capture. Copy its
   method, its endpoints and its layout.** It is the map for this run.

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE
**Do NOT write a vector. Do NOT register a drive. Do NOT touch any `.go` file.** A later run grades it
(`.softhouse/findings/F-2026-09-10-split-capture-from-grading.md`).

## WHY
`WriteOffOutstanding` [`nexus/internal/apps/loan/writeoff.go:36`] sums the four outstanding buckets over
every instalment that is **not** `ObligationsMet`. `OH-WOGRADE-W` graded the sum but could NOT grade the
skip: loan 11 had no fully paid instalment, so a port that forgets the skip sums the same rows and a
drive for it kills zero. **The skip is only observable on a write-off of a loan where at least one
instalment is fully paid and at least one is not.**

## THE OBJECTIVE
Find — or create — an ACTIVE loan whose schedule has **at least one instalment `complete: true`** and at
least one with outstanding principal, then **write it off**, capturing detail (with
`associations=all`, which carries the schedule), transactions and journal entries **before and after**.

* **Prefer an existing loan** (read-only probe first). Do NOT use loans 11 or 12 — their states are
  cited by committed vectors.
* If none exists, **create one on product 3** (accrual, the same mapping the write-off JE vector used):
  a client, a loan, disburse it dated far enough before the business date (2026-09-03 — verify it,
  never change it) that the first instalment is due, then **repay exactly the first instalment's total
  due** so it reads `complete: true`. Then write it off. Record every request body.
* Best evidence: the paid instalment carries non-zero principal AND interest, so a port that forgets
  the skip over-counts BOTH buckets.

## The path
1. Probe; choose the loan; record why. **Skim existing `req/` bodies for endpoint shapes** — do NOT read
   Fineract Java to rediscover an endpoint.
2. **`pg_dump -Fc` snapshot** of `fineract_gerege` from **`gerege-oracle-db`** (NOT `fineract-db-1` —
   stale; see `.softhouse/briefs/tools/README.md`) to `/Users/buv/gerege-oracle-snapshots/`. **Never
   commit a `.dump`.**
3. Capture before-state. **Commit.**  4. Repay if creating (capture). **Commit.**
5. Write off. Capture after-state. **Commit.**
6. `OWNER.md`: the loan, every instalment's four buckets and `complete` flag before, the write-off
   transaction's portions, the buckets after, the journal entries — and the one-line arithmetic showing
   the write-off amount equals the sum over the UNPAID instalments only.

**If the oracle refuses, THE REFUSAL IS THE RESULT** — capture status, error body, source line; commit;
stop. **Do not SQL-insert anything. Tenant `gerege` only — never `default`. SQL is read-only.**

## Rules of evidence
- Every capture record you will want cited must be **JSON** (a psql dump cannot be cited by a vector —
  the wire-float guard refuses it; keep SQL reads as corroboration only).
- **Request bodies must be BYTE-STABLE** under a binary-double round trip (`100.00` must not become
  `100.0`). **Check your own `req/` before committing.**
- Money is integer minor units in anything you write. Never write a sub-minor value.
- "The oracle" is the Fineract reference; **Oracle Database is prohibited.** PostgreSQL only.

## The bar and the budget
The bar must still pass: `go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY
with `§4.4.2-RECORDED-DECISION-EXIT`. ~400 iterations. **Commit after each step that saved files.**
**Write commit messages to a file (`git commit -F`). Never commit TASK.md or `.softhouse/maps/`.**
