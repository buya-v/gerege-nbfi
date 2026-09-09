# OH-I3 — adjudicate 21 I-3 sites. WRITE EACH VERDICT THE MOMENT YOU REACH IT.

Repo: /Users/buv/oh-gerege-i3   Branch: feat/OHI3-adjudicate (checked out)

## RULE ONE, AND IT OUTRANKS EVERYTHING BELOW

**Append each site's verdict to the document as soon as you decide that site.**
Never hold findings in your head to compose a document at the end.

A previous attempt at THIS EXACT TASK ran 633 events, read both trees correctly, reached
real conclusions — and was killed with ZERO BYTES ON DISK, because it was told to produce
one document at the end. Every conclusion it reached was lost. That was the brief's fault,
and this line is the fix.

Create the file FIRST, before any analysis:

    mkdir -p .softhouse/reviews/i3-adjudication
    printf '# I-3 site adjudication\n\n_in progress; each site appended as it is decided_\n\n' \
      > .softhouse/reviews/i3-adjudication/ADJUDICATION.md

Then append one section per site, immediately, as you finish it. `git add` + `git commit`
after **every third site** — small commits, not one at the end. If you are killed at site
9, sites 1-9 must survive.

## The situation

`ledgerguard` reports 38 findings. All 12 of their (class, file) pairs ARE in
`.softhouse/guards/ledger-invariants.baseline`, so the publication ratchet passes. But the
baseline is PAIR-GRANULAR — one row covers ELEVEN sites in loan/charge.go. Those individual
sites have never been examined. That is your job.

List them with positions:

    cd .softhouse/guards/ledgerguard && go run . --root ../../../nexus

## Your 21 sites

    11  internal/apps/loan/charge.go            I3-FIELD-WRITE
    10  internal/apps/investor/postgres.go      I3-SQL-BALANCE (5) + I3-FIELD-WRITE (5)

Do loan/charge.go FIRST and commit it before starting investor. Half the work committed
beats all of it lost.

## The question, per site

I-3 is: **balances are DERIVED, never written.** For each site pick one verdict and give a
short argument citing the code:

  A. REAL VIOLATION — a derived balance reaches a persistence boundary. Needs repair.
  B. INPUT, NOT A BALANCE — a value a pure computation reads FROM, or a request/DTO field.
  C. PROJECTION INTERMEDIATE — written and reloaded by the same projection as its own
     starting state; reaches no journal entry, GL posting, or column read as an account balance.
  D. PORTED SHAPE — a faithful port of a Fineract column Fineract itself stores. Cite the
     Java file and line, AND say whether the Go port reads it back as authoritative or
     recomputes it. A citation without that distinction is not an answer.

"I cannot classify this without a go/types reachability analysis" is a CORRECT answer for a
site that genuinely needs one — four loanproduct rows are already blocked on exactly that.
Record the block; do not invent confidence.

## Section format — append this per site, verbatim shape

    ### <file>:<line> — <class>
    **Expression:** `<the offending expression>`
    **Verdict:** <A|B|C|D|UNDECIDABLE>
    **Argument:** <2-4 sentences citing code; for D cite Fineract file:line and say
    whether the port reads it back or recomputes>

## Absolutely forbidden

A previous task in this programme made a finding disappear by DELETING the ported type and
its `[VERIFIED:]` citation. That is evidence destruction, not adjudication.

* You may NOT delete a type, field, or citation to make a finding go away.
* You may NOT edit `nexus/` at all — read-only.
* You may NOT edit `.softhouse/guards/` — the baseline is not editable by whoever
  classified the findings (DEC-2 §4.4.2 obligation 3).

**The finding count must still read 38 when you finish.** Verify it and state it.

## Finish with

A SUMMARY section counting each verdict, and an explicit list of every site you could not
decide with what evidence would settle it. Then a final commit.

## Report

Verdict counts, the undecidable list, and any site you believe is a REAL violation. That
last list matters more than length — getting it right beats getting it long.
