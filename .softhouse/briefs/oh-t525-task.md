# T525 — the remaining REAL I-3 breaches: investor and working-capital

WORKING DIRECTORY: /Users/buv/oh-gerege-t525  (branch fix/T525-investor-wc-i3)
NEVER commit to `main`. NEVER touch the other worktrees or the oracle.

## Your base
This branch is cut from `fix/T509-guard-property`, NOT from `main`, because the
repaired guard lives there. On `main` the guard reports 4 findings and cannot see
the ones you are here to fix. Confirm you see 42 before you start; if you see 4,
stop and say so.

## Why these and not the others
The guard reports 42 findings. Most are schedule intermediates whose status is
genuinely undecided — a previous session investigated and concluded, correctly,
that no sound discriminator can be built from the Go tree alone. Those stay.

These twelve are different. They are stored-balance WRITES TO PERSISTENCE, the
same class that was already repaired in savings (T501/T510/T515, merged):

  investor/postgres.go:108   INSERT populating the balance column
                             "fee_charges_outstanding_derived" on table
                             m_external_asset_owner_transfer_details  (5 findings)
  investor/postgres.go:199 :202 :205 :208 :211   field writes (5 findings)
  workingcapital/postgres.go:379   INSERT into m_wc_loan_balance — a STORED
                             BALANCE TABLE, caught via the TABLE name because
                             none of its 13 columns contains "balance"  (1)
  workingcapital/postgres.go:168   OPAQUE-SQL — assembled at run time, so the
                             guard cannot read it and will not certify it  (1)

Verify each yourself before acting:
  cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t525/nexus

## The ruling in force (R1 — do not relitigate)
The Go module NEVER writes a stored-balance column. Fineract derives those
columns BY WRITING them, nightly, from a batch job. CLAUDE.md says adopt
Fineract's SCHEMA; it does not say adopt Fineract's WRITE PATHS. Keeping a
column and never writing it is consistent. Writing it is not. Balances come from
folding the append-only rows.

Where Fineract models "not yet calculated" with a flag, that flag stays false —
that is the honest state, not a fudge.

The savings repair is your worked example. Read it:
  git -C /Users/buv/gerege-nbfi log --oneline --all --grep "savings I-3"
  nexus/internal/apps/savings/{postgres.go,summary.go,transaction.go}

## For OPAQUE-SQL (workingcapital:168)
The guard cannot read run-time-assembled SQL, so it refuses to certify it. That
is a refusal, not an accusation. Repair is to build the statement as a string
literal the guard can read — OR to state the exemption in DEC-2, which is a USER
GATE: if you conclude that, STOP, write the argument, change no code.

## What NOT to do
- Do not touch the schedule intermediates in loanproduct/ or loanschedule/.
- Do not edit .softhouse/guards/** — the guard and its baseline are not yours.
  If your repair changes the finding set, the baseline is updated by a separate
  reviewed step, not by you.
- Do not add an exemption anywhere to make something pass.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   cd .softhouse/guards/ledgerguard && go run . --root /Users/buv/oh-gerege-t525/nexus

Report the finding count by class before and after, and say plainly what now
derives each balance you stopped writing. Never say complete / done / goal
achieved. If you cannot repair one without changing behaviour, say so and leave
it — a truthful refusal beats a silent regression in money code.
