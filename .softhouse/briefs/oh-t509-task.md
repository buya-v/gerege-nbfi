# T509 — the ledger guard matches a SPELLING, not a PROPERTY

WORKING DIRECTORY: /Users/buv/oh-gerege-t509  (branch fix/T509-guard-property)
NEVER commit to `main`. NEVER touch the other worktrees or the oracle.

## What you are repairing
`.softhouse/guards/ledgerguard` enforces DEC-2 §4.4 I-3 ("balances are derived,
never written"). It is the ONLY mechanism that can enforce I-3 — no vector grades
it, because a vector is a snapshot of oracle output and a snapshot cannot observe
the ABSENCE of a write. It is currently wrong in BOTH directions.

You are repairing an enforcement mechanism on a money non-negotiable. The bar is
red and five good commits are held behind it. That is NOT a reason to make the
guard permissive. If your change makes the guard find FEWER real violations, you
have made things worse than the red bar.

## UNDER-MATCHING — it misses real violations (verified by T503/T505)
1. `m_wc_loan_balance` is a STORED BALANCE TABLE the guard cannot see:
   balanceNameRe tests COLUMN names, and none of its 13 columns contains
   'balance' — the TABLE NAME does.
2. `loanschedule/emi.go:1720-1721,:1726` ships the IDENTICAL roll-forward write
   GREEN, citing the same oracle method, with the field's own comment reading
   "the balance carried INTO this segment" — passing only because it is spelled
   `outstandingMinor`. CENSUS: 6 balance-in-substance assignments tree-wide; the
   guard reports 4.
3. Exactly 6 COMPOSITE-LITERAL writes to those fields go unflagged, one FOUR
   LINES from a refused site. The guard's own CANNOT-CATCH item 8 recommends
   "a constructor" — which is precisely the move that defeats it.
4. `m_loan_transaction.outstanding_loan_balance_derived`
   (LoanTransaction.java:127) is a real stored balance column reached via
   LoanBalanceService:174,194,203. T502 MISSED it; its conclusion survived BY
   LUCK rather than by the check it performed.

## OVER-MATCHING — the four loanproduct sites are NOT I-3 violations
  interestperiod.go:277,:288,:327 and repaymentperiod.go:562.

READ THIS REASONING, DO NOT INVENT YOUR OWN. T505 already refuted the obvious
argument: "it is a text blob, not a typed column" FAILS, because both cells lack
@JsonExclude and ARE serialised into m_loan_progressive_model.json_model and read
back as starting state.

The sound ground is: **THERE IS NO POSTING STREAM.** A schedule is a projection
of the FUTURE; postings are records of the PAST. "Derive by summation" needs
something to sum over, and a projection has nothing. I-3 binds where a posting
stream exists — the ledger, savings transactions — and cannot bind where none
does.

## What to build
Replace the spelling test with a property test. A write is an I-3 violation when
the value it produces is an AUTHORITATIVE BALANCE OVER A POSTING STREAM —
reaching persistence as such, or a column or table named for one — and is NOT a
projection intermediate. Detect regardless of identifier spelling, and catch
composite literals as well as assignments, and TABLE names as well as column
names.

## SELFTEST DISCIPLINE — non-negotiable
The guard already selftests (15 cases; 14 must drive it RED, 1 GREEN). Extend it.
Every under-match above becomes a NEW case that must drive the repaired guard RED,
and you must SHOW it going red BEFORE you claim the repair:
  - a stored balance reached only via the TABLE name
  - the emi.go roll-forward spelled `outstandingMinor`
  - a composite-literal write to a balance field
  - a constructor-shaped write (the move item 8 recommends)
And the four loanproduct schedule sites must drive it GREEN, for the posting-stream
reason, not because you softened a pattern.

The count of REAL violations must go UP (the census says 6 in substance, the guard
reports 4), not down. A repair that only clears the four you want cleared is a
bypass wearing a fix's clothes.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   cd .softhouse/guards/ledgerguard && go run . --selftest --repo /Users/buv/oh-gerege-t509
   cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t509/nexus
   bash .softhouse/conformance.sh

Report exit codes and the before/after violation counts by class. Never say
complete / done / goal achieved. If you cannot find a sound property test, say so
plainly and change nothing — a truthful refusal beats a guard that passes a dirty
tree.
