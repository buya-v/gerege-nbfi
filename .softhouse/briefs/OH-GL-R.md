# OH-GL-R — open the loan→GL posting surface with an ACCOUNTING-ENABLED product

Worktree: `/Users/buv/oh-gerege-glr` (branch `feat/OHGLr`)
Work ONLY in that directory. The oracle is UP.

## THE FACT THAT MOTIVATES THIS, ALREADY ESTABLISHED — do not re-derive it

`OH-INV-Q` drove a transfer through COB and it refused:

    ProductToGLAccountMappingNotFoundException: Mapping for product of type LOAN
    with Id 2 does not exist for an account of type LOAN PORTFOLIO
    [InvestorAccountingHelper.java:128]

The driver then found the root cause: `GET /loanproducts/2` reports
**`accountingRule: 1` — `NONE`**. The seed product `SEED-Probe-Loan` has accounting
DISABLED. The exception is downstream of that, not a missing row. **Four GL accounts
already exist** (`GET /glaccounts` → 4).

Consequence, and it is much larger than the investor question: with every seeded loan on
an accounting-NONE product, **the entire loan→GL / journal-entry posting surface is
unreachable**, which is very likely why the `ledger` context's vectors all go through the
direct `ledger_rest_posting` API instead of loan-driven postings.

## What you are building — ADDITIVE ONLY. This is the hard constraint.

**Create a NEW loan product with accounting enabled. Do not modify product 2, and do not
modify any existing loan.** Every committed capture was taken against the current
configuration and its provenance must stay untouched. Additive means: new GL accounts if
needed, new product, new client if needed, new loan. Nothing existing is edited.

If you find yourself issuing a `PUT` to `/loanproducts/2` or to any existing loan, **stop**
— that is the one thing this task must not do.

**Snapshot first:** `pg_dump -Fc` before any write. Keep it OUTSIDE the repo, under
`/Users/buv/gerege-oracle-snapshots/`. **Do not commit a `.dump`** — `*.dump` under
`capture/` is gitignored, and a database dump is operational insurance, not evidence.

## The path

1. **Inventory the chart of accounts.** `GET /glaccounts`. Four exist; determine their
   types and usage. Create only what is missing, and record what you created.
2. **Create a loan product with `accountingRule` = ACCRUAL_PERIODIC (3) or CASH (2)** —
   **choose, and record why in one line.** Prefer the one that produces the richest
   observable posting stream, and say what you rejected. It needs the full
   `accountingMappings` set: fund source, loan portfolio, interest on loans, income from
   fees, income from penalties, losses written off, overpayment liability.
3. **Create a client and a loan** on that product; approve and disburse it.
4. **Capture the GL surface.** `GET /journalentries?loanId=<id>` (and by transaction),
   `GET /loans/<id>/transactions`, `GET /glaccounts`. These are the observations.
5. **THEN, and only then**, the two follow-on questions below.

At every step, if the oracle refuses, **the refusal is the observation**: capture the
status and error body, record it, and continue with what remains.

## The properties to grade — PROPERTIES, NOT A VECTOR COUNT

**You are measured on defects provably caught, never on file count.** `OH-DEEP-E` was given
a count target and produced 18 files carrying 10 facts; eight were discarded.

The double-entry surface is where the real defects live, and these are genuinely
discriminating:

1. **Every journal entry batch BALANCES: sum(debits) == sum(credits), exactly, in integer
   minor units.** This is I-1/I-2 and it is the single most important property in the
   programme. A port that rounds one leg independently breaks it.
2. **A disbursement posts a specific DEBIT/CREDIT PAIR** — loan portfolio debited, fund
   source credited. Direction is a real defect: a port that inverts the pair still
   balances. Pin the direction, not just the amounts.
3. **Entry TYPE is an enum with an ordinal**, like every other Fineract enum this programme
   has ported. `parties-wrong-iota-ordinals` kills 12 for the same class of defect.
4. **The `entryType`/`glAccountType` pairing** — an income account credited where an asset
   account should be debited is a mapping defect that survives a balancing check.

Register a `ledger-wrong-*` or `loan-wrong-*` drive per property, in the context the
capture belongs to, and promote a vector only where the capture actually SEES it.

## THE RULE ON INERT DRIVES

**A drive that kills ZERO is a finding to resolve, never something to merge.** Either
promote a vector that sees it, or **delete it with the argument**. Say which, per drive.
**Report the kill count for every drive.** `OH-INV-Q` registered four, all scored zero, and
deleted all four with the argument — that is the standard, and it is a good outcome.

**Prove the instrument was live when a drive scores zero**, as `OH-INV-Q` did: run the
controls in the same session, and name an existing drive in the same context that still
kills. A zero from an untested instrument is worthless.

## The two follow-on questions, if step 4 succeeds

* **Investor Finding A.** With accounting live, re-run the COB transfer settlement
  (`OH-INV-Q` left the step configured at order 7 and the business date at 2026-09-02).
  If it settles, `GET /external-asset-owners/transfers/{id}/journal-entries` and show the
  posted amounts equal the **outstanding**, not 0.9725 × it. That confirms the documented
  purchase-price gap against live postings.
* **The fee/penalty blindness** (`.softhouse/findings/F-2026-09-09-fee-penalty-blind.md`).
  Every loan capture has `feeChargesOutstanding = 0` and `penaltyChargesOutstanding = 0`,
  so a port dropping either term from the four-term summary sum passes every vector. A
  loan with a **non-zero fee and a non-zero penalty that DIFFER from each other** (equal
  values let a term-swap defect survive) closes it. This is worth as much as the GL work.

## Measuring it

`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh`. **Repaired
2026-09-09**: no silent `0` — they exit 2 with empty stdout and a reason on stderr. **An
empty result means the MEASUREMENT FAILED, not a zero-kill drive.** Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`** for any claim about what the port or oracle computes or refuses.
  Line numbers must come from the FILE, not from a comment-stripped view — the driver got
  this wrong once and `OH-INV-Q` caught it.
- **Never synthesise a value you did not observe.** Configuring a product through the API
  and observing what Fineract computes is NOT synthesis. **SQL-inserting an
  `acc_product_mapping` row would be** — `OH-INV-Q` refused exactly that, correctly. Keep
  that line.
- **SQL is READ-ONLY.** Never write the `default` tenant. All writes go through the API.
- Every vector carries `capture_ref`, `capture_sha256`, `citation`; re-verify after writing.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **The ledger is double-entry and append-only.** Balances derived, never written (I-3).
  Corrections are reversing entries. This task is that invariant's home ground.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02).
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. Never vector a residue.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- Never describe savings as insured, protected or guaranteed. No deposit endpoint.

## The bar, before you claim done
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs**.
Report every drive's kill count and every capture's sha256, and state plainly what you
created in the oracle.

## Budget
~500 iterations. Two runs before you died on navigation and wrote nothing. **Take steps
1-4 FIRST.** If you are 150 iterations in without a posted journal entry or a recorded
refusal, stop exploring and write down what you have.
