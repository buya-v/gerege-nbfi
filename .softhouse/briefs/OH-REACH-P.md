# OH-REACH-P — build LEG 2, the go/types reachability discriminator

Worktree: `/Users/buv/oh-gerege-reachp` (branch `feat/OHREACHp`)
Work ONLY in that directory. **This task needs no oracle.** Do not capture, do not POST.

## YOUR DELIVERABLE IS AN INSTRUMENT, NOT A GREEN BAR

Six I-3 sites in `nexus/` are **UNDECIDABLE** and have been for weeks. They are pinned in
`.softhouse/guards/ledger-invariants.baseline` and they are a **known, argued, test-pinned
red** — an acceptable state this programme chose deliberately. You are not being asked to
clear them. You are being asked to build the one mechanism that could decide them soundly.

**If your finished instrument reports UNRESOLVED for all six, THAT IS A SUCCESS.** It means
the sites stay refused on evidence instead of on the absence of a tool, and the next agent
inherits a discriminator instead of a question. **Clearing a site on weaker evidence is the
one outcome that would make this run a failure.**

The bar's ledger finding set must remain **exactly 12 (class, file) pairs** unless your
instrument PROVES a change, and any change to `ledger-invariants.baseline` is a reviewed
diff that must be argued in the commit message. Do not touch that file to make a number
move.

## The exact question, and it is narrow

`ledgerguard`'s `I3-COMPOSITE-BALANCE` fires on the ALLOCATED form `&T{Balance: v}`, because
allocation produces something that outlives the expression. It does **not** fire on:

    v := T{Balance: x}   // ... then a store of &v
    append(store.rows, T{Balance: x})

Following a value into a store requires `go/types`. That is LEG 2, and it does not exist.
`.softhouse/guards/ledgerguard/main.go:1350-1360` (CANNOT-CATCH item 10) and `:1352-1380`
(item 12) state the problem; read both before writing code.

**For each site, answer exactly one question:** does the value written there reach a
**persistence boundary** — a journal entry, a GL posting, or a column any aggregate reads
as an account balance?

The six sites (`.softhouse/guards/ledger-invariants.baseline`):

    I3-COMPOSITE-BALANCE  internal/apps/loanproduct/interestperiod.go
    I3-COMPOSITE-BALANCE  internal/apps/loanproduct/repaymentperiod.go
    I3-FIELD-WRITE        internal/apps/loanproduct/interestperiod.go
    I3-FIELD-WRITE        internal/apps/loanproduct/repaymentperiod.go
    I3-FIELD-WRITE        internal/apps/loan/charge.go
    I3-FIELD-WRITE        internal/apps/loanschedule/emi.go

The four `loanproduct` rows already have a recorded argument (T516 LEG 1 parity, executable
as `TestOutstandingLoanBalanceIsASweptSnapshot`). LEG 2 is the missing half.

## THE HARD DESIGN CONSTRAINT — this is the whole task

> **THE ANALYSIS MUST FAIL CLOSED ON UNRESOLVED VALUE FLOW.**

Recorded by T514, repeated at `main.go:1356`, and it is the trap:

> An analysis that answers "not persisted" on an edge it cannot resolve reintroduces the
> same fail-open one layer up, and — unlike a waiver, which is a visible document a human
> must amend — **a heuristic's failure produces NO ARTEFACT AT ALL.**

So your tool emits **three** verdicts per site, never two:

* `REACHES-PERSISTENCE` — a resolved path to a persistence boundary. The finding is REAL.
* `UNRESOLVED` — any edge the type checker cannot resolve: an interface method with more
  than one implementation in scope, a func value, a reflect call, a closure escaping into
  a field, a `any`-typed hop, a cgo or generated boundary. **This is the DEFAULT and it is
  never an acquittal.**
* `PROVABLY-NO-PERSISTENCE` — every path from the write to every use is resolved, and none
  reaches a boundary. This verdict requires the FULL closure to be resolved. If one edge in
  it is `UNRESOLVED`, **the whole site is `UNRESOLVED`.**

A site is cleared only by the third, and only with the closure printed so a human can read
what was actually proven.

### The heuristic you must NOT rebuild

A persistence-**surface** heuristic was proposed for this and **measured being defeated by a
single `git mv`** of an unrelated real savings balance write into a subdirectory
(T505 MAJOR-1). Anything keyed on **path, filename or package name** is defeated the same
way. `ledgerguard` itself is name-based and says so (CANNOT-CATCH item 11: "it has no type
checker", "two functions of the same name in different packages are ONE NAME to this
guard"). **Your tool exists precisely because names are not sound.** Resolve through
`go/packages` with `NeedTypes|NeedSyntax|NeedTypesInfo|NeedDeps`, and identify boundaries by
**types and objects** — `*sql.DB`/`*sql.Tx`/`pgx` method objects, the tree's SQL wrappers
resolved as `types.Object`, the journal-entry and GL-posting types — never by a string.

## Drive it RED before you believe it — three controls, all required

An instrument that only ever reports "fine" has not been tested. This directory's rule.

1. **A REAL positive.** Construct a case where a balance genuinely reaches a persistence
   boundary through the composite-literal-into-store form the guard admits it cannot see
   (`v := T{Balance: x}` then a store of `&v`, and `append(store.rows, T{Balance: x})`).
   Your tool MUST report `REACHES-PERSISTENCE`. If it does not, you have built nothing.
2. **THE `git mv` CONTROL — this one is mandatory and it is the point.** Reproduce T505
   MAJOR-1: take a real balance write, `git mv` it into a subdirectory, and re-run. **No
   verdict may change.** A tool whose answer moves when a file moves has failed, and this
   is the exact failure that killed the previous proposal.
3. **A FAIL-CLOSED control.** Construct a case with a deliberately unresolvable edge — an
   interface with two implementations in scope is the cheapest. Your tool MUST report
   `UNRESOLVED`, **not** `PROVABLY-NO-PERSISTENCE`. Then add the second implementation to a
   case that previously resolved and show the verdict DEGRADES from provable to unresolved.
   Fail-closed that is never observed failing closed is an assumption, not a property.

Put these in `testdata/`, as `ledgerguard` already does, and make them run in `go test`.

## Measuring it

`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh <worktree> <ctx>`,
`ohwatch.sh`. **Repaired 2026-09-09** — they no longer print a silent `0` on failure; they
exit 2 with empty stdout and a reason on stderr. **An empty result means the MEASUREMENT
FAILED; it is not a zero.** Control-test before trusting any number:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`** for every claim about what a value reaches or does not reach. A claim
  without a file:line is not an argument. For a `PROVABLY-NO-PERSISTENCE` verdict, print the
  resolved closure — every hop — because that verdict is the only one that can clear a red.
- **Never weaken a refusal to make the bar green.** A known red is an acceptable state; a
  green bar bought with a defeatable predicate is not (`main.go:1378`).
- Do not delete or rename a finding to make it disappear. The baseline fails in BOTH
  directions on purpose: a vanished row is treated as a silenced violation, and that ratchet
  has already caught one attempt to rename a site green (T502 B-2).

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**; no float in any money path, including intermediates.
- Balances are **derived, never written** (I-3); append-only (I-4). This task IS I-3.
- **HALF_UP**, ordinal 4, precision 19, tz `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **PostgreSQL only** — `pgx`. No MySQL/MariaDB/Oracle driver or dialect anywhere. "The
  oracle" means the Fineract reference implementation; **Oracle Database is prohibited.**
- **DEC-2 §4.4 is RATIFIED.** You may not amend it. Note CANNOT-CATCH item 9: a balance READ
  is not a write path, and raising a read to a refusal is an amendment routed as a `user`
  gate. Your tool answers the WRITE question only.

## The bar, before you claim done
From the worktree: `go build ./...`, `go test ./...`, then `bash .softhouse/conformance.sh`.
Expect exit 2 as the §4.4.2 recorded decision with the ledger finding set at **exactly 12
(class, file) pairs** — that is green, and it should still be 12 when you finish unless you
have PROVED otherwise and argued it. Report each of the six sites with its verdict, and the
result of all three red controls.
