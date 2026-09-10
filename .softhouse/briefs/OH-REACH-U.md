# OH-REACH-U — make reachguard able to CLEAR, without letting it fail open

Worktree: `/Users/buv/oh-gerege-reachu` (branch `feat/OHREACHu`)
Work ONLY in that directory. **No oracle.** Another run holds it; take no captures.

## What exists, and what it cannot yet do

`OH-REACH-P` built `.softhouse/guards/reachguard` — LEG 2, the go/types reachability
discriminator for I-3 balance writes. It works, it is committed, and its three red controls
pass. **Read `main.go` and `reachguard_test.go` before changing anything.**

Its result on the six pinned I-3 sites is **all six UNRESOLVED**, and that was the correct
outcome: UNRESOLVED is never an acquittal, so the sites stay refused on evidence rather
than on the absence of a tool.

But the merge recorded a limitation, and closing it is your task:

> The unresolved reasons are coarse: `unmodelled expression *ast.BinaryExpr` and
> `value passed into external package fmt` dominate. Until they are addressed the tool can
> fail closed on real code but **cannot yet CLEAR any of it** — LEG 2 is buildable rather
> than finished.

Observed reasons on the real tree, from `reachguard.sh`:

    emi.go:1730,1735,1809,1814,1876 …  unmodelled expression *ast.BinaryExpr
    conformance/money.go:38,45,49,53   result of a call into external package fmt
    conformance/money.go:55            result of a call into external package strconv
    charge_test.go:134,140,143,149     value passed into external package testing

## THE CONSTRAINT THAT OUTRANKS THE GOAL

> **THE ANALYSIS MUST FAIL CLOSED ON UNRESOLVED VALUE FLOW.**

Recorded by T514, at `ledgerguard/main.go:1356`:

> An analysis that answers "not persisted" on an edge it cannot resolve reintroduces the
> same fail-open one layer up, and — unlike a waiver, which is a visible document a human
> must amend — **a heuristic's failure produces NO ARTEFACT AT ALL.**

So every increment below must make the tool resolve **more edges soundly**, never make it
*assume* an edge is safe. **If you cannot model something soundly, it stays UNRESOLVED.**

**Clearing a site on weaker evidence is the one outcome that makes this run a failure.**
It is entirely acceptable to finish with all six still UNRESOLVED and a better-instrumented
tool. Do not reach for a cleared site.

## The two increments

### 1. Model binary expressions
`*ast.BinaryExpr` is the dominant unresolved reason. A binary expression's value flow is
the **union of its operands'** flows: `a + b` reaches a boundary iff `a` or `b` does. Model
that, soundly, for the arithmetic and comparison operators. If an operand is itself
unresolved, **the result stays UNRESOLVED** — union, not intersection.

### 2. Prune provably-non-persisting stdlib packages
`fmt`, `strconv`, `strings`, `testing` cannot persist a value to a database, a journal
entry or a GL posting. A value passed into `fmt.Sprintf` does not thereby reach a
persistence boundary.

**This is the increment most likely to be got wrong, so bound it explicitly:**
* Allow-list by **package path**, resolved through `types.Object`, never by name matching.
* Only functions that are **pure with respect to persistence** — they may read the value
  and return a derived one. `fmt.Fprintf(w, …)` writes to an `io.Writer`, which **can** be
  anything; do not blanket-clear the `Fprint*` family by package alone.
* Keep the list **short and justified in a comment**, one line per package saying why it
  cannot persist.
* A value RETURNED from such a call is a new value; if the original also flows elsewhere,
  that other flow is still analysed.

## Drive it RED — the existing controls must still pass, plus a new one

1. **All existing tests still pass**, unchanged: `TestPositiveReachesPersistence`,
   `TestGitMVDoesNotMoveVerdict`, `TestResolvedIsProvablyNoPersistence`,
   `TestFailClosedDegrade`. If your change makes any of them pass for a *different reason*,
   say so.
2. **A NEW fail-closed control for each increment**, and this is the point of the task:
   * a binary expression **one of whose operands reaches a boundary** must report
     `REACHES-PERSISTENCE` — union semantics, proven, not assumed;
   * a binary expression with an **unresolved** operand must stay `UNRESOLVED`;
   * a value passed to an allow-listed package **and also** stored must still report
     `REACHES-PERSISTENCE` — pruning one path must not lose another;
   * `fmt.Fprintf` into a writer that **is** a persistence sink must NOT be cleared.
3. **`TestGitMVDoesNotMoveVerdict` is still mandatory.** T505 MAJOR-1 killed the
   predecessor heuristic; any allow-list keyed on anything a `git mv` can change fails the
   same way.

## What SUCCESS looks like

Fewer UNRESOLVED **reasons**, each remaining one more specific, with the six sites' verdicts
**whatever the evidence says** — very possibly still all six UNRESOLVED. Report the before
and after verdict for each of the six, and the reason counts.

**Do not touch `.softhouse/guards/ledger-invariants.baseline`.** The finding set must stay
exactly 12 (class, file) pairs. Do not wire reachguard into `conformance.sh` — six
UNRESOLVED verdicts would turn a recorded red into a hard guard failure without deciding
anything.

## Measuring it
`.softhouse/briefs/tools/kills.sh`, `redcount.sh`, `reachguard.sh`. **Repaired 2026-09-09**:
no silent `0` — they exit 2 with empty stdout and a reason on stderr. Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`** for every claim about what a value reaches. For any verdict that
  CHANGES, print the resolved closure — every hop.
- **Never weaken a refusal to make a number move.** A known red is an acceptable state; a
  green bar bought with a defeatable predicate is not (`ledgerguard/main.go:1378`).

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- Balances **derived, never written** (I-3); append-only (I-4). This task IS I-3.
- **DEC-2 §4.4 is RATIFIED and you may not amend it.** Note CANNOT-CATCH item 9: a balance
  READ is not a write path, and raising a read to a refusal is a `user` gate. Your tool
  answers the WRITE question only.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs**.
Report each of the six sites before/after, and every new control with its polarity.
