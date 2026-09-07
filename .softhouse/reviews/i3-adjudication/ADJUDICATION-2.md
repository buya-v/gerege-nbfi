# I-3 adjudication, part 2 — loanproduct and loanschedule

_in progress_

Scope: the 12 unexamined I-3 sites in `nexus/internal/apps/loanproduct` (10) and
`nexus/internal/apps/loanschedule` (2). Every verdict cites code. `nexus/` and
`.softhouse/guards/` were not modified. The oracle is Apache Fineract at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`.

## Which of the ten loanproduct findings are the four blocked rows

The two-legs refusal in the baseline (`ledger-invariants.baseline`, block above rows 50-53)
and in `loanproduct/doc.go` ("The two 'balance'-named cells in this package are NOT ledger
balances") names FOUR sites, and only four. They are the package's four I3-FIELD-WRITE
findings:

- `interestperiod.go:430` and `:441` — the two branches of `UpdateOutstandingLoanBalance`
- `interestperiod.go:549` — `AddBalanceCorrectionAmount`
- `repaymentperiod.go:688` — `copyWithoutPaidAmounts`

Those four are the sites the baseline argument is about. For them the correct verdict is
UNDECIDABLE, and the reasoning is restated per-site below rather than re-argued from scratch:
the argument that they are not ledger balances rests on two legs, and the leg that would
settle the class — LEG 2, reachability, decided mechanically — has been commissioned,
investigated, and reported NOT CONSTRUCTIBLE with today's tooling (a go/types value-flow
analysis that fails closed on unresolved edges does not exist yet; the persistence-surface
heuristic proposed instead was MEASURED being defeated by one `git mv` of an unrelated real
savings write, T505 MAJOR-1). LEG 1 (parity) is executable and test-pinned and rules out the
derive-on-read repair, but it does not by itself settle whether the stored cells are ledger
balances. Nothing here manufactures a verdict for them.

The other SIX loanproduct findings are a different population and are not covered by that
argument. They are the I3-COMPOSITE-BALANCE sightings that T509's widening added
(`ledgerguard` selftest case (r)): the same two cells written by ALLOCATED composite
literals in three construction helpers —

- `interestperiod.go:614,:615` — `InterestPeriod.copy` (deep copy)
- `interestperiod.go:641,:642` — `withEmptyInterestPeriod` (the inserted empty segment)
- `repaymentperiod.go:96,:97` — `NewInterestPeriod` (the fresh period's first segment)

The baseline's argument text never names these six and nobody has adjudicated them
individually. They are decidable, and the verdict for all six is **C — PROJECTION
INTERMEDIATE**: each writes the projection's own starting state into a brand-new or freshly
deep-copied object that only the same projection will sweep and read, and none of them stores
the output of a derivation. The distinction from the four is drawn in the composite section
below; it is not receiver semantics and not "there is no posting stream" — both are retired
arguments in doc.go.

## loanproduct/interestperiod.go — I3-FIELD-WRITE, the refused sweep writes

### internal/apps/loanproduct/interestperiod.go:430 — I3-FIELD-WRITE
**Expression:** `ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().plus(previousInterestPeriod.DisbursementAmount()).plus(previousInterestPeriod.CapitalizedIncomePrincipal()).plus(previousInterestPeriod.BalanceCorrectionAmount()).minus(previous.DuePrincipal()).plus(previous.PaidPrincipal()).negToZero()` (the cross-period branch of `UpdateOutstandingLoanBalance`)
**Verdict:** UNDECIDABLE
**Argument:** This is one of the two branches of the Go port of `InterestPeriod.updateOutstandingLoanBalance` (InterestPeriod.java:166-186), the segment cell's ONLY refresh mechanism [VERIFIED: ProgressiveEMICalculator.java:1254-1256]. The written value is a genuine derivation — a roll-forward summation that folds, among its summands, the previous period's `PaidPrincipal`, a quantity the transaction processor accumulates from real LoanTransactions [VERIFIED: RepaymentPeriod.java:405-407; ProgressiveEMICalculator.java:421; AdvancedPaymentScheduleTransactionProcessor.java:929,:967,:2912]. The cell it lands on is a SWEPT SNAPSHOT that the oracle deliberately reads stale between explicit sweeps — RepaymentPeriod.copyWithoutPaidAmounts zeroes a summand of this expression and does not re-run it [VERIFIED: RepaymentPeriod.java:173-198]. So I-3's prescribed remedy ("derive by summation over the postings") cannot substitute for the stored cell: a derive-on-read shape returns a different number at every between-sweep point, and TestOutstandingLoanBalanceIsASweptSnapshot executes exactly that (after a −200.00 correction to a summand and no sweep, the stored cell still reads 90000 where a derivation reads 70000). That is LEG 1, and it rules out the repair, not the classification. What still separates "stored ledger balance" from "benign projection intermediate" is LEG 2 — whether the value reaches a journal entry, GL posting, or column any aggregate reads as an account balance. The forward trace terminates in DTOs carrying no @Entity/@Table/@Column and the calc package emits no journal entry (doc.go, evidence item 1), but that closure is hand-walked, not type-checked, and it is precisely the claim the go/types reachability discriminator was to decide mechanically — reported NOT CONSTRUCTIBLE, with the substitute persistence-surface heuristic MEASURED defeated by one `git mv` (T505 MAJOR-1). A verdict that cleared this site on the hand-walked closure would be the same failure mode one layer up. Evidence that would settle it: a type-checked forward reachability analysis, failing closed on unresolved value flow, that proves the cell's value does or does not reach a persisted balance column, journal entry, or GL posting in the tree.

### internal/apps/loanproduct/interestperiod.go:441 — I3-FIELD-WRITE
**Expression:** `ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().plus(previousInterestPeriod.BalanceCorrectionAmount()).plus(previousInterestPeriod.CapitalizedIncomePrincipal()).plus(previousInterestPeriod.DisbursementAmount()).negToZero()` (the within-period branch of `UpdateOutstandingLoanBalance`)
**Verdict:** UNDECIDABLE
**Argument:** The sibling branch of the same port of `InterestPeriod.updateOutstandingLoanBalance` (InterestPeriod.java:166-186), for segments that are not the first of their period. Identical shape to :430: a derived roll-forward written into the swept-snapshot cell the oracle refreshes only at explicit sweeps and reads stale in between. LEG 1 applies unchanged (the pinned test at interestperiod_test.go:46-90 makes the derive-on-read shape a failing build), and LEG 2 is the same hand-walked closure to DTOs with the same missing mechanical discriminator. Same settling evidence as :430. Not A: no persistence boundary is written — this value reaches no journal entry, GL posting, or Go balance column; the persistence the oracle gives these cells (m_loan_progressive_model.json_model) is the projection's own closed loop, written by the projection and reloaded as the same projection's starting state. Not D-with-comfort: the cell cannot be recomputed on read (that is the parity break), so it is not the charge.go shape where the invariant recompute and the stored field are asserted equal.

### internal/apps/loanproduct/interestperiod.go:549 — I3-FIELD-WRITE
**Expression:** `ip.balanceCorrectionAmount = ip.BalanceCorrectionAmount().plus(additional)`
**Verdict:** UNDECIDABLE
**Argument:** Go port of `InterestPeriod.addBalanceCorrectionAmount` (InterestPeriod.java:113-115). The cell is NOT a balance in the sense its name suggests — it is a SIGNED DELTA, one summand of the roll-forward in UpdateOutstandingLoanBalance beside disbursementAmount and capitalizedIncomePrincipal, whose Add* methods are not flagged; the oracle only ever adds a NEGATED amount to it [VERIFIED: ProgressiveEMICalculator.java:907,:922,:946,:952,:1124,:1129]. What trips the guard is the substring "balance" in the name, and what keeps the site red is exactly the same two-legs situation as :430/:441: the write is a derived sum into a live cell whose staleness is part of the algorithm (it feeds the swept snapshot), so the derive-on-read remedy changes money; and the reachability question that would settle the class is the unmechanized LEG 2. Note precisely what this does NOT claim: at :922 and :952 the negated amount IS a paid principal, a transaction-driven quantity — "signed delta" is a claim about sign discipline, not provenance (doc.go, evidence item 3). The value reaches no journal entry, GL posting, or account-balance column; the oracle's own persistence of the cell is the json_model closed loop. UNDECIDABLE for the same reason as :430/:441, with the same settling evidence (a failing-closed, type-checked reachability discriminator over LEG 2).

