# OH-I3B — adjudicate the 12 remaining unexamined I-3 sites. CLASSIFY ONLY.

Repo: /Users/buv/oh-gerege-i3b   Branch: feat/OHI3B-adjudicate (checked out)

## RULE ONE

**Append each site's verdict the moment you decide it.** Create the file before any
analysis; commit every third site. An earlier attempt at the sibling task ran 633 events and
was killed with ZERO BYTES on disk because it composed at the end. Do not repeat that.

    mkdir -p .softhouse/reviews/i3-adjudication
    printf '# I-3 adjudication, part 2 — loanproduct and loanschedule\n\n_in progress_\n\n' \
      > .softhouse/reviews/i3-adjudication/ADJUDICATION-2.md

## Read first

`.softhouse/reviews/i3-adjudication/ADJUDICATION.md` — part 1, 21 sites, already merged. It
sets the standard: every verdict cites code, and a D verdict must say whether the port reads
the value back as authoritative or recomputes it. Follow its section format exactly.

## Your 12 sites

    4  loanproduct/interestperiod.go   I3-COMPOSITE-BALANCE
    3  loanproduct/interestperiod.go   I3-FIELD-WRITE
    2  loanproduct/repaymentperiod.go  I3-COMPOSITE-BALANCE
    1  loanproduct/repaymentperiod.go  I3-FIELD-WRITE
    2  loanschedule/emi.go             I3-FIELD-WRITE

List them with positions:

    cd .softhouse/guards/ledgerguard && go run . --root ../../../nexus

## What makes these different from part 1 — read this before you start

The baseline already carries an ARGUMENT for four of the loanproduct sites, and you must
engage with it rather than restate it. From `.softhouse/guards/ledger-invariants.baseline`:

    "Not ledger balances on the two legs that survive (T516): LEG 1 parity — applying I-3's
     remedy changes the money, because the oracle refreshes outstandingLoanBalance only at
     explicit sweeps and reads it stale in between (executable, not argued); and LEG 2
     reachability — the value reaches no journal entry, GL posting or column any aggregate
     reads as an account balance, its persistence being a closed loop written by the
     projection and reloaded as the same projection's starting state. They stay refused
     because the only mechanism that could distinguish them soundly is LEG 2's go/types
     reachability discriminator, which DOES NOT EXIST YET, and the persistence-surface
     heuristic proposed instead was MEASURED being defeated by one `git mv` (T505 MAJOR-1)."

So: **four of these are already known to be blocked on a discriminator that was
commissioned, investigated, and reported NOT CONSTRUCTIBLE.** For those, `UNDECIDABLE` with
that reasoning restated in your own words is the CORRECT answer. Do not manufacture a
verdict to look thorough.

But there are TEN loanproduct findings and only FOUR blocked rows. **Say which sites are
which.** The six that are not covered by that argument may well be decidable, and nobody has
looked.

`loanschedule/emi.go` has its own baseline note worth testing:

    "the roll-forward that is the twin of the loanproduct sites and shipped GREEN for two
     months because it is spelled outstandingMinor."

If it is genuinely the twin, say so and why. If the spelling is the only thing that made it
invisible and it is actually a different shape, that is a finding.

## Verdicts

  A. REAL VIOLATION — a derived balance reaches a persistence boundary.
  B. INPUT, NOT A BALANCE.
  C. PROJECTION INTERMEDIATE — written and reloaded by the same projection as its own
     starting state; reaches no journal entry, GL posting, or column read as a balance.
  D. PORTED SHAPE — cite the Fineract file:line AND say whether the port reads it back or
     recomputes.
  UNDECIDABLE — say exactly what evidence would settle it.

Part 1's investor sites were A because `investor/postgres.go` owns a persistence boundary;
its loan/charge.go sites were D because that slice owns NO persistence at all. Establish
which is true for each file here — do not assume either.

## Forbidden

* You may NOT delete a type, field, or citation to make a finding go away. A prior task did
  exactly that and it is evidence destruction.
* `nexus/` is READ-ONLY. `.softhouse/guards/` is READ-ONLY — under DEC-2 §4.4.2 obligation 3
  the baseline is not editable by whoever classifies the findings.
* **The finding count must still read 28 when you finish.** Verify and state it.

## Report

Verdict counts; which sites are blocked on the discriminator and which are not; and any site
you believe is a REAL violation. The last list matters most — part 1 found ten, and they were
repaired the same day.
