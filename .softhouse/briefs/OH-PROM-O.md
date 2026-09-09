# OH-PROM-O — promote the loan/workingcapital backlog on PROPERTIES, not on count

Worktree: `/Users/buv/oh-gerege-promo` (branch `feat/OHPROMo`)
Work ONLY in that directory.

## THE ORACLE IS BUSY. YOU MAY NOT CAPTURE. THIS IS ABSOLUTE.

Another agent (OH-INV-N) holds the Fineract instance and is **advancing the business date
and running COB** on it. Oracle state is therefore MOVING underneath you for this entire
run. Any capture you take would be an observation of a transient, inconsistent state, and
a vector built on it would poison the corpus in a way that is very hard to detect later.

**You will take no new captures. You will issue no POST, PUT or DELETE to the oracle. You
will not advance the business date.** A read-only health probe is permitted and nothing
else. Every vector you write is promoted from a capture **already committed** in
`.softhouse/capture/`. If you conclude a property needs a fresh capture, that is a
**finding to report, not a capture to take** — write it down and move on.

## What this task is

`loan` has 27 committed captures and 10 vectors; `workingcapital` has 12 and 5. That is
not automatically a backlog of 28 vectors waiting to be written. **Most of those captures
carry no distinct property, and several carry the SAME property as a vector that already
exists.** Your job is to find the properties that are genuinely uncovered and pin those.

**You are measured on defects provably caught, never on file count.** OH-DEEP-E was given a
vector-count target and produced 18 files carrying 10 distinct facts; eight were discarded
at review. The existing loan set already shows the failure mode starting — **four separate
`*-summary-total-outstanding` vectors** exist (L01, L03, L05, L06) and they pin one fact
four times. Do not add a fifth. If you find yourself writing "the same read-back for
another loan id", stop: that is cloning, and it will be discarded.

## The properties the driver has already confirmed are uncovered

These come from reading the committed captures. **Verify each against the capture before
you build on it** — do not take this list on trust, it is a starting point and it is short
on purpose.

### P1 — a waiver does NOT move the outstanding balance
`.softhouse/capture/loan/out/loan-1-transactions-after-raw.json` — transaction 13,
`Waive interest`, amount `1000.0`:

    id 13   Waive interest   amount=1000.0   outstandingLoanBalance=100000.0
                             interestPortion=1000.0   principalPortion=null

The balance is **unchanged** from the disbursement's `100000.0`, because
`outstandingLoanBalance` tracks **principal**, and a waiver settles interest. **A port that
reduces the outstanding balance by the waived amount is wrong**, and that is an easy and
natural mistake. `LN-L01-summary-total-outstanding-after-waiver` pins the *summary* after
the waiver; the **transaction-level allocation and the unmoved balance are not pinned by
anything.**

### P2 — an Accrual carries NO outstanding balance: `null`, not `0`
Same capture, transaction 2, `Accrual`, amount `6618.53`, `outstandingLoanBalance = null`
while `interestPortion = 6618.53`. **Null and zero are different observations** and a port
that emits `0` for an absent balance is wrong — this is one of the most common porting
defects there is, and here the oracle states it explicitly. Pin it, and register a drive
that returns `0` where the oracle returns absent.

### P3 — the running balance is DERIVED from principal portions only
Across the transaction sequence the balance moves only on transactions carrying a
`principalPortion`. That is **I-3 visible on the read path** — balances derived, never
written. A drive that stores the balance independently, or that lets it drift by folding
in interest/fee portions, should die on this vector.

### P4 — `workingcapital`
The driver has NOT surveyed these captures for properties. Ten are uncited:
`wc-loan-submit`, `wc-loan-approve`, `wc-loan-disburse`, `wc-loans-list`,
`wc-product-create`, `wc-products-list`, `loan-products-list`, `loan-products-template`,
`loans-template`, `near-breach-list`. **Several of these are almost certainly templates and
list endpoints carrying no money property at all.** Say so where it is true. `near-breach-list`
is the one whose NAME suggests a threshold property worth looking at first — a limit
comparison is exactly the kind of boundary a port gets wrong by one minor unit.

**A capture that carries no distinct property is a finding.** Record it, with the reason, so
the next agent does not re-survey it. "These 8 are templates with no money cell" is a
genuinely useful result and it is a fine outcome for most of P4.

## THE RULE ON INERT DRIVES — read it twice

**A drive that kills ZERO is a finding to resolve, never something to merge.** Resolve it
one of two ways, and say which in the commit message:
  * promote a vector that sees it, or
  * **delete the drive with the argument for why the defect is unobservable.**
Never let one merge inert. **Report the kill count for every drive you register.**

## Measuring it

`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh <worktree> <ctx>`.
**Repaired 2026-09-09** — they no longer print a silent `0` on failure; they exit 2 with
empty stdout and a reason on stderr. **An empty result means the MEASUREMENT FAILED. It is
not a zero-kill drive.** Control-test before trusting any number:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    redcount.sh <worktree> loanproduct                          -> 4

If a control is wrong, the instrument is wrong — not the tree. Current drive counts:
`loan` 5, `workingcapital` 4.

## Rules of evidence
- **Cite `file:line`** for any claim about what the port or the oracle computes or refuses.
  A claim without a file:line is not an argument.
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256` and a `citation` quoting the observed row. **Re-verify the sha256 after
  writing.** Nothing may be computed by a promotion — if the number is not in the capture,
  it does not go in the vector.
- Captures are JSON with **float-formatted** money (`100000.0`, `6618.53`). The vector
  stores **integer minor units** (`10000000`, `661853`). That conversion is a
  transcription, and it is the ONE place a residue can enter — see below.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, ever, **including
  intermediates** — no `float64`, no `math/big.Float`. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3); append-only (I-4). P3 is this invariant.
- **HALF_UP**, ordinal 4, precision 19, tz `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02;
  0.035 → .04 under both). The earlier brief OH-CAP-J stated this INVERTED; this form is
  correct.
- **Sub-minor residue is REFUSED** — ratified 2026-09-09, gate G-19, DEC-2 predicate G-08.
  If a capture value has more than 2 decimal places of significance, **REFUSE it — never
  write a parity vector for a residue value.** Record the observation and move on.
- **PostgreSQL only.** "The oracle" means the Fineract reference implementation, never
  Oracle Database, which is prohibited.
- **Two bounded contexts only: `loan` and `workingcapital`.** Wandering outside them is a
  rejection. In particular **do not touch `investor`** — another agent holds it.

## The bar, before you claim done
From the worktree: `go build ./...`, `go test ./...`, then `bash .softhouse/conformance.sh`.
Expect exit 2 as the §4.4.2 recorded decision with the ledger finding set at **exactly 12
(class, file) pairs** — that is green. Any other non-zero exit is a failure you must fix.
Report the kill count of every drive, and the sha256 of every capture a vector cites.
