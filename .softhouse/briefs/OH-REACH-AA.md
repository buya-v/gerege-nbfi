# OH-REACH-AA — resolve `time` and `math/big`, and let the rest stay UNRESOLVED

Worktree: `/Users/buv/oh-gerege-reachaa` (branch `feat/OHREACHaa`)
Work ONLY in that directory. **No oracle.** Another run holds it; take no captures.

## Where reachguard stands

`.softhouse/guards/reachguard` is LEG 2, the go/types reachability discriminator for I-3
balance writes. Read `main.go` and `reachguard_test.go` before changing anything.

Current verdict on the six pinned I-3 sites:

    1 site(s) resolved to PROVABLY-NO-PERSISTENCE — a finding for review, not a waiver.
    THE RED STANDS on 5 site(s).

`OH-REACH-U` added binary-expression union semantics and a stdlib allow-list
(`fmt`, `strconv`, `strings`, `testing`) keyed on the callee package **path** through
`types.Object`. That cleared `loan/charge.go`. **Do not rebuild any of that.**

## THE MAP — the exact remaining blockers, already counted

`bash .softhouse/briefs/tools/reachguard.sh` on the current tree, unresolved reasons by
frequency:

    16  value passed into external package time, whose body this analysis did not open
    12  value passed into external package math/big, whose body this analysis did not open
    12  result of a call into external package math/big (provenance not opened)
     8  result of a call into external package time (provenance not opened)
     5  call through a func value (dynamic dispatch)
     4  value flows through a pointer dereference (points-to not resolved)

**`time` and `math/big` are ~48 of ~57 edges. They are your task. The other 9 are NOT.**

The allow-list lives at `main.go:1537` (`persistenceInertPkgs`), with the soundness rules
immediately above it at `:1523-1536`. Extend that map; do not invent a second mechanism.

## The two additions, and the trap in the second

1. **`time`** — a calendar/duration package with no store. Straightforward.

2. **`math/big` — READ THIS TWICE.** `big.Int` is this programme's money type, so a value
   passed into `math/big` is *money*. That is **fine**: the question is not whether the
   package touches money, it is whether the package can **persist** money. `math/big` opens
   no database, writes no journal entry, and owns no store. But:

   * **`big.Int` methods take POINTER RECEIVERS and MUTATE them** — `z.Add(x, y)` writes
     into `z`. `OH-REACH-U`'s existing rule refuses a callee with a **typed pointer
     parameter** as a conservative out-write guard, and a pointer receiver is the same
     shape. **If you relax that for `math/big`, the mutated receiver must keep its
     arg→receiver flow edge**, exactly as `OH-REACH-U` did for methods generally, or you
     will silently lose the path where the *result* of the arithmetic is what gets stored.
   * **The point of the whole tool is I-3: a derived balance being written.** The
     arithmetic that derives it runs through `math/big`. If pruning `math/big` loses the
     edge from operands to result, the tool stops seeing the very flow it exists to trace.
     **Your `pruning-must-not-lose-a-path` control is the one that catches this.**

## THE CONSTRAINT THAT OUTRANKS THE GOAL

> **THE ANALYSIS MUST FAIL CLOSED ON UNRESOLVED VALUE FLOW.**

`ledgerguard/main.go:1356`, recorded by T514:

> An analysis that answers "not persisted" on an edge it cannot resolve reintroduces the
> same fail-open one layer up, and — unlike a waiver, which is a visible document a human
> must amend — **a heuristic's failure produces NO ARTEFACT AT ALL.**

**Leave `call through a func value` and `pointer dereference` UNRESOLVED.** Dynamic
dispatch and unresolved points-to are exactly the edges this rule is about. Do not
approximate them, do not assume the common case, do not add a "usually safe" branch. If
those 9 edges keep all five sites UNRESOLVED, **that is a correct and successful outcome.**

**Clearing a site on weaker evidence is the one result that makes this run a failure.**

## Drive it RED — existing controls plus new ones

1. **All eight existing tests must still pass, unchanged**: `TestPositiveReachesPersistence`,
   `TestGitMVDoesNotMoveVerdict`, `TestResolvedIsProvablyNoPersistence`,
   `TestFailClosedDegrade`, `TestBinaryUnionOperandReachesPersistence`,
   `TestBinaryUnionUnresolvedOperandStaysUnresolved`,
   `TestPruningAllowListedDoesNotLoseStoredPath`,
   `TestFprintfIntoPersistenceWriterNotCleared`.
   **`TestGitMVDoesNotMoveVerdict` is mandatory** — any allow-list keyed on something a
   `git mv` can change dies the way T505 MAJOR-1 killed the predecessor heuristic.
2. **New, and both polarities:**
   * a `big.Int` arithmetic result that IS stored must report `REACHES-PERSISTENCE` — the
     arg→result edge survives pruning;
   * a `big.Int` value mutated through a pointer receiver and then stored must report
     `REACHES-PERSISTENCE`;
   * a value through `time` that is not stored stays clear, and one that IS stored is
     still `REACHES-PERSISTENCE`;
   * a **func-value** call must still report `UNRESOLVED` — prove the fail-closed edge you
     are deliberately not fixing.

## What SUCCESS looks like
Report each of the six sites **before and after**, and the unresolved-reason counts before
and after. Whatever the verdicts are, they must follow from the evidence. **Do not touch
`.softhouse/guards/ledger-invariants.baseline`** — exactly 12 (class, file) pairs. Do not
wire reachguard into `conformance.sh`.

## Rules of evidence
- **Cite `file:line`.** For any verdict that CHANGES, print the resolved closure, every hop.
- **Never weaken a refusal to move a number.** A known red is acceptable; a green bar bought
  with a defeatable predicate is not (`ledgerguard/main.go:1378`).

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- Balances **derived, never written** (I-3); append-only (I-4). This task IS I-3.
- **DEC-2 §4.4 is RATIFIED — you may not amend it.** CANNOT-CATCH item 9: a balance READ is
  not a write path; raising a read to a refusal is a `user` gate. Answer the WRITE question.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **exactly 12 pairs**, wrong-ledger census **17**. Run it
EARLY. ~500 iterations; **commit by iteration 150** even if incomplete.
