# T501 — the I-3 breach in savings: a stored, summed balance

WORKING DIRECTORY: /Users/buv/oh-gerege-t501
Git worktree on branch `fix/T501-savings-i3`. NEVER commit to `main`.
NEVER touch /Users/buv/gerege-nbfi or /Users/buv/oh-gerege-charges.

## Why this is the top priority
`bash .softhouse/conformance.sh` currently EXITS 2. The bar on `main` is RED, and
because a red tree cannot be attested, five good commits — including the T508
journal-entry repair — cannot be published. Turning this green releases them.

## The findings (verify them yourself; do not inherit the list)
Run: cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t501/nexus

Six are in savings. THE THREE THAT MATTER (I3-SQL-BALANCE):
  - postgres.go:113  INSERT INTO m_savings_account_summary populating `account_balance_derived`
  - postgres.go:113  the UPDATE arm assigning `account_balance_derived`
  - postgres.go:210  INSERT INTO m_savings_account_transaction populating `running_balance_derived`

And three I3-FIELD-WRITE:
  - postgres.go:243  `t.RunningBalance =`   in FindByAccountID   <- a DECODE path
  - postgres.go:302  `s.AccountBalance =`   in decodeSummary     <- a DECODE path
  - summary.go:53    `s.AccountBalance +=`  in Add               <- a pure fold on a VALUE receiver

## READ THE TRAP BEFORE YOU ARGUE WITH THE GUARD
The columns are spelled `..._derived`, and in Fineract they ARE derived — by being
WRITTEN, nightly, by a batch job. CLAUDE.md says adopt Fineract's PostgreSQL SCHEMA.
It does NOT say adopt Fineract's WRITE PATHS. Keeping the column and never writing
it is consistent. Writing it is not.

## RULING IN FORCE (R1, decided 2026-09-03 — do not relitigate)
The Go module NEVER writes a stored-balance column. The column keeps its schema
default. Where Fineract models "not yet calculated" with a flag, that flag stays
false, which is the honest state. Balances are obtained by folding the append-only
transaction rows, never by reading a stored sum.

If you conclude a column MUST be written, you are proposing a DEC-2 amendment.
That is a USER GATE: STOP, write the argument in your handoff, CHANGE NO CODE.

## The two DECODE paths need judgement, not reflex
:243 and :302 populate a struct from a row that was read back. Decide honestly
whether that is "writing a balance" or "materialising one that was read". If the
row's balance column is never written by us, what is being decoded, and should the
field exist at all? A constructor that DERIVES the value is the shape the guard
itself endorses; a setter is not.
`summary.go:53` is a fold on a VALUE receiver returning a new value — that is
derivation, not storage. If you keep it, make that obvious to a reader AND to the
guard; a composite literal return may serve better than `+=`.

## DONE means all of these exit 0. Paste RAW output including exit codes:
   cd nexus && go build ./... && go test ./...
   cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t501/nexus
   bash .softhouse/conformance.sh

The ledgerguard ALSO runs a selftest that asserts the real tree is clean. Both the
refusal list AND the selftest must pass. Do not make the tree pass by weakening the
guard: it is not yours to edit, and a guard that passes a dirty tree is worse than
a red bar.

## Reporting
Report exit codes. Never say complete / done / goal achieved. If a gate refuses,
fix the code. Never add an exemption. A truthful refusal beats a false pass.
Say plainly what you changed in the savings persistence model and what now derives
the balance.
