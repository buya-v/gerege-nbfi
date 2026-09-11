# OH-PROVEDGE-BA — CAPTURE ONLY. Provisioning at the UPPER band edges: 29, 59, 89 days overdue.

Worktree: `/Users/buv/oh-gerege-provedge` (branch `feat/OHPROVEDGEba`)
Work ONLY in that directory. **You hold the oracle server.** A parallel run (`OH-LREV-AZ`) is oracle-free.
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/provisioning.md`.
2. `.softhouse/capture/provisioning/ATTESTATION-OH3.md`, `req/ENT-02-create.json` (the entry-creation body
   the oracle ACCEPTED), `out/ENT-04-entry-loan-products-raw.json` (the read-back shape) — **your template.**
3. `.softhouse/capture/loan-writeoff-paid-instalment/req/` — loan submit/approve/disburse bodies the oracle
   ACCEPTED today (product 3). Adapt them to **product 2** (`SEED-Probe-Loan`, the one criteria 1 covers).

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE
**No vector, no drive, no `.go` file.**

## WHY
OH-PROVCRIT-AJ graded the age-band rule from ages 0/31/62/92, and its half-open drive dies only on the
LOWER edge (age 0). No observed age sits on an UPPER edge — 29 (STANDARD's maxAge), 59, 89 — so a port that
treats the upper bound as exclusive is indistinguishable. Criteria 1 bands: [0,29] [30,59] [60,89]
[90,36500] (verified live today).

## THE OBJECTIVE
Three ACTIVE loans on **product 2** whose **oldest unpaid instalment is exactly 29, 59 and 89 days overdue on
the provisioning date**, then ONE provisioning entry dated **the business date** (verify `GET /businessdate`
— expected 2026-09-03; never change it), read back per loan.
* Choose disbursement dates so the first instalment's due date is 29 / 59 / 89 days before that date, and
  make no repayment. **Confirm each loan's overdue age from the oracle's own read-back** (loan detail
  delinquency / summary) BEFORE creating the entry; if the oracle counts differently from your arithmetic,
  its count is the observation — adjust and record why.
* Create the entry with the ENT-02 body shape (`createjournalentries: false`), then read it back exactly as
  ENT-03/ENT-04 were read. **The existing product-2 loans will appear too, at their own new ages — keep them;
  they are observations.**
* If the oracle refuses the entry (e.g. one entry per date, or an entry already covers this date), **the
  refusal is the result** — capture it, find the rule in the source with `file:line`, commit, stop.

`pg_dump -Fc` snapshot of `fineract_gerege` from **`gerege-oracle-db`** (NOT `fineract-db-1`) to
`/Users/buv/gerege-oracle-snapshots/` first; **never commit a `.dump`.** **Commit after each step.**
Write `.softhouse/capture/provisioning-upper-edge/OWNER.md`: each loan, its due dates, the oracle-read overdue
age, and the category/percentage/amount the entry assigned — and state plainly, for each of 29/59/89, which
band the oracle put it in.

## Rules of evidence
- Every record a vector will cite must be **JSON**; SQL (read-only) is corroboration only.
- **Request bodies byte-stable.** Money in integer minor units in anything you write; never sub-minor.
- **Tenant `gerege` only — never `default`. SQL read-only. No SQL inserts.**
- "The oracle" is the Fineract reference; **Oracle Database is prohibited.** PostgreSQL only.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.**

## The bar and the budget
The bar must still pass: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~400 iterations.
**Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
