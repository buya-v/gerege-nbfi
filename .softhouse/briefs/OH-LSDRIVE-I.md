# OH-LSDRIVE-I — 50 vectors, 2 drives. Prove the corpus discriminates. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lsdrive` (branch `feat/OHLSDRIVEi`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

## THE MEASUREMENT THAT MOTIVATES THIS

`loanschedule` holds **50 vectors — the largest corpus in the programme — and exactly TWO
deliberately-wrong implementations**:

    loanschedule-wrong-days-in-year-365   kills 45
    loanschedule-wrong-half-even          kills  5

45 + 5 = 50, so **every vector is killed by exactly one drive.** The corpus is broad in
INPUTS and narrow in DEFECTS PROVEN. A vector no drive can kill has not been shown to
discriminate anything — it is an assertion, not a test.

**Your job is to prove (or disprove) that these 50 vectors discriminate more than two
defect shapes.**

## THE MAP — the driver measured which inputs actually vary

A port that IGNORES a field can only be caught if the corpus VARIES that field. Distinct
values across the 50 vectors:

    VARIES                                      covered by a drive?
      disbursements                    39         no
      number_of_repayments             12         no
      schedule_start_date              11         no
      annual_nominal_interest_rate      6         no
      currency          MNT | USD       2         no
      repayment_frequency_unit  MONTHS | YEARS  2  no
      rounding      HALF_UP | HALF_EVEN 2         YES (wrong-half-even)
      day_count  ACTUAL_ACTUAL | FIXED_30_360 2   YES (wrong-days-in-year-365)

    CONSTANT — cannot discriminate anything, a port ignoring them passes all 50
      time_zone                        Asia/Ulaanbaatar
      repayment_every                  1
      interest_method                  DECLINING_BALANCE
      down_payment_percentage          0
      installment_rounding_multiple_minor  "0"

**Verify this table yourself before building on it.** It is a starting point; three of this
driver's briefs have been factually wrong this week and every one was caught by the agent
that checked.

## The task — ONE property, applied per field

> **For each VARYING field not yet covered, a port that IGNORES that field must DIE.**

Register a `loanschedule-wrong-*` drive per uncovered varying field. The two highest-value
first, because their money effect is largest:

* **`repayment_frequency_unit`** — a port that treats `YEARS` as `MONTHS` (or ignores the
  unit) computes a wildly different schedule. This is the single biggest money difference
  in the table.
* **`number_of_repayments`** — a port that uses a fixed count ignores 12 distinct values.

Then `annual_nominal_interest_rate`, `currency`, `schedule_start_date`, `disbursements` as
budget allows. **Order matters more than count: two drives that kill are worth more than
six that were never measured.**

## THE RULE ON INERT DRIVES — and here it is the POINT, not a footnote

**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument.**

**A zero here is a genuinely interesting result** and you must report it as one: it would
mean the corpus varies a field but no vector's OUTPUT depends on it — the field is
decorative at this seam. Say so plainly and record which field. Four runs in a row have
declined coverage they could not prove and recorded what a capture would need; that is the
standard.

**Report the kill count for every drive you register, and prove the instrument was live.**

## TOOLING TRAP — this one has bitten a measurement this week
**`loanschedule`'s conformance binary REJECTS `-root`**, unlike every other context's, which
REQUIRES it. The error texts differ (`flag provided but not defined: -root` vs
`-root is required`). `kills.sh` handles both; a hand-rolled `go run … -root …` silently
returns nothing and reads as "0 drives" — that exact mistake produced a wrong count for the
driver an hour ago. Use the tool.

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh loanschedule loanschedule-wrong-half-even          ->  5
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      ->  1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED, not a zero-kill drive.** If a control is wrong, the
instrument is wrong.

After your change, `loanschedule-go` must still pass **all 50** vectors and both existing
drives must still kill 45 and 5. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02).
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not weaken or delete an existing vector** to make a drive kill. If a drive cannot
  kill, that is the finding.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- Note the port already `ungraded()`-REFUSES `installment_rounding_multiple_minor` and
  `down_payment_percentage` when non-zero [`loanschedule/generator.go:380-387`] — that is
  CORRECT handling of a constant field, not a gap. **Do not "fix" it.**
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loanschedule`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit by iteration 120**, and commit each drive as it is measured rather
than batching — the last six runs committed at ~92-190 and every one that committed early
kept its work.
