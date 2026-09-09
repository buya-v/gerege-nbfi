# T509 continued — finish the guard repair and prove it

WORKING DIRECTORY: /Users/buv/oh-gerege-t509  (branch fix/T509-guard-property)
NEVER commit to `main`. NEVER touch the other worktrees or the oracle.

## Where you are
Your previous session closed the UNDER-match: `balanceSynonymRe` now catches
`outstandingMinor` in emi.go alongside `outstandingLoanBalance` in loanproduct —
two ports of one Fineract method that had opposite verdicts decided by spelling.
You also added `ledger-invariants.baseline` so the drive-red control works on a
tree that is red by recorded decision. Both are COMMITTED (23966a65). Good work.

The guard now reports 42 findings, up from 4.

## What is NOT done
The OVER-match half. The four loanproduct schedule-intermediate sites are refused
today by recorded decision (T502/T505/T514/T516) ONLY BECAUSE no discriminator
exists. Your own baseline note says it: they "stay refused until a go/types
reachability discriminator exists".

Build that discriminator.

## The property it must implement
A write violates I-3 when the value is an AUTHORITATIVE BALANCE OVER A POSTING
STREAM — a running total that is the record of truth, derivable by summing
append-only postings.

It does NOT violate I-3 where no posting stream exists to derive from. A loan
SCHEDULE is a PROJECTION OF THE FUTURE; postings are RECORDS OF THE PAST.
Summation needs something to sum over; a projection has nothing.

Refinement already paid for: "it is a text blob, not a typed column" FAILS as an
argument — those cells serialise into m_loan_progressive_model.json_model and are
read back as starting state. Serialisation does not make a value authoritative.

You have go/types available; the guard already parses with it. Reachability is
the suggested route: does the written value reach persistence as an authoritative
balance, or does it die inside a projection?

## Non-negotiable
- The count of REAL violations must NOT fall because you softened a pattern. If
  your discriminator clears the four loanproduct sites, it must STILL catch
  every genuine stored balance — including m_wc_loan_balance (caught via the
  TABLE name) and the six composite-literal writes.
- Every case you clear becomes a NEW selftest case that must drive GREEN for the
  stated reason, and every case you keep must still drive RED. Show both.
- If you cannot build a sound discriminator, SAY SO AND CHANGE NOTHING. The four
  sites staying refused is an acceptable outcome. A guard that clears them on a
  weak argument is not.
- Do NOT edit the baseline to make anything pass. It fails in both directions by
  design; that is the point of it.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   cd .softhouse/guards/ledgerguard && go run . --selftest --repo /Users/buv/oh-gerege-t509
   cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t509/nexus
   bash .softhouse/conformance.sh

Report exit codes and the finding count by class, before and after. Never say
complete / done / goal achieved. A truthful refusal beats a guard that passes a
dirty tree.
