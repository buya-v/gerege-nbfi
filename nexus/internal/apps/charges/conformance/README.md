# charges conformance harness

This package grades the Go port of `nexus/internal/apps/charges` against golden
vectors captured from the reference Fineract oracle. It is built on the same
shape as `loanschedule/conformance` and `ledger/conformance`: a second
schema/comparator, default-deny admission, a no-float guard, a capability
registry, and an explicit rule that a guard which inspects nothing is an error.

## What it grades

Two pure computations from the charges slice, which are all a captured charge
vector can observe:

1. **Construction validation** — the ordered list of `Charge.Validate()` codes
   (`validation_code_count`, `validation_codes[i]`). See `impl.go:goEvaluator`.
2. **Fee arithmetic** — the fee in integer minor units for a flat, percentage-of-
   amount or percentage-of-disbursement-amount charge (`fee_minor`, `fee_present`),
   including min/max capping. Rounding is HALF_UP, no float, big.Int throughout
   (`impl.go:feeFor`, `money.go`).

Each comparison is recorded by a single `cellSink`; `CellFields()` is **computed**
by running the comparator over probe pairs, never transcribed (`grade.go`).

## What it cannot grade

- **Interest-based fees** — `percent of amount and interest` and `percent of
  interest` need the loan's interest component, which a charge vector does not
  carry. A fee vector for those calculation types is inadmissible
  (`admit.go`).
- **Anything requiring a database** — there is no tenant, no schema, no
  persistence. The evaluator interface is the two pure computations above, not
  "save a charge" (`impl.go:ChargeEvaluator`).
- **Non-parity claims** — only `class: parity` on seam `charge.evaluate` is
  graded; everything else is refused by admission (`admit.go`).

## What it needs from a tenant

To be gradable with real (non-probe) vectors the store must contain:

- A **vector store** of `schema gerege.charges.vector/v1` files under
  `<repo>/.softhouse/vectors/charges`. An empty store is a *legitimate* state and
  produces exit 2 with `ZERO VECTORS FOUND` — never a pass over zero work
  (`grade.go:Run`).
- A **store pin** `PIN-charges.json` naming the Fineract commit the vectors were
  captured from; a vector whose `oracle.fineract_commit` does not match is
  inadmissible (`admit.go`, `capability.go:LoadPin`).
- A **capability registry** `capabilities-charges.json` mapping each
  `capabilities_required` name to a seam status. A name that is unknown, blind,
  or ungraded refuses the vector by default (`capability.go:Assess`).
- A **Go implementation** registered under the name each vector's
  `graded_against` cites; an unknown name is inadmissible and an unregistered
  implementation is a fatal reason (`impl.go`, `admit.go`).

The no-float guard reuses `loanschedule/conformance.ScanGoTreeForFloatingPoint`
over `nexus/` and runs on every invocation, with or without vectors
(`grade.go:Run`, `nofloat.go`).

## Exit codes

- `0` — every graded vector passed and at least one parity vector was graded.
- `1` — a money or cell mismatch, or an invariant violation.
- `2` — the harness, corpus, pin or registry is unusable, including an empty
  vector store.
