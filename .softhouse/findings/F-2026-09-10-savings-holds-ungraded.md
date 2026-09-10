# F-2026-09-10 — a CLAUDE.md non-negotiable is implemented and ungraded

**Status:** OPEN. Needs one oracle capture (dispatched as `OH-HOLDCAP-R`).
**Found by:** a technique not used before in this programme — measuring coverage of the
**port's own exported surface** rather than variation in the vectors' request.

## The measurement

    savings port: 78 exported functions
    referenced anywhere under internal/apps/savings/conformance/: 3
    UNEXERCISED: 75

Among the 75 is the entire hold/available implementation
[`nexus/internal/apps/savings/summary.go`]:

    AccountBalanceOf            :228   the derive-don't-store balance fold
    HeldOf                      :315
    AvailableOf                 :379
    HoldNetRunningBalancesOf    :504

`CLAUDE.md` line 14 makes this a **non-negotiable**:

> The ledger is double-entry and append-only. Balances are derived, never written.
> Corrections are reversing entries. **Holds are postings and alter `available` only, never
> posted `balance`.**

**That rule has a full implementation and no vector checks it.**

## Why no drive could have caught this

The corpus has **no observation of a hold at all**. Every apparent match in
`.softhouse/capture/savings/out/` is a *field* — `withholdTax` (10), `amountOnHold` (10),
`amountHold` (10), `transferOnHold` (4) — and a scan for a hold-flagged transaction type
across every savings capture finds **NONE**. Only one savings vector even mentions the
words, and it is `SV-01-daily-interest-rounding`, incidentally.

So this is not a drive gap and not a corpus-variation gap: it is an **absent observation**
behind an implemented rule. A drive that broke `AvailableOf` would kill zero, because
nothing calls it.

## Why the technique is worth keeping

Previous gap-finding here measured **inputs**: which request fields the corpus varies
(`F-2026-09-10-drive-ratio-only-applies-to-rich-requests`). That finds ports which ignore a
field. It cannot find code that is **never reached at all**.

Measuring the port's exported surface against what conformance references finds the second
kind, and it found a named non-negotiable on the first attempt. **Run it on the other
contexts.**

## What closes it

One capture: **place a hold on a savings account, then release it**, and read back the
account and its transactions. Two active accounts exist (id 1 balance 1000.31, id 2 balance
1000.01). Then the rule becomes gradeable in the form CLAUDE.md states it:

* the hold posts a transaction;
* `available` falls by the held amount;
* **the posted `balance` does NOT move**;
* release restores `available` and again leaves `balance` untouched.

A port that decrements `balance` on a hold — the natural mistake — is invisible today.

---

## CORRECTION AND A BETTER INSTRUMENT (same day)

The measurement above — *"78 exported, 3 referenced by conformance, 75 unexercised"* — was
a **grep for identifiers in the conformance package**, and it **over-claims**. Conformance
calls a handful of entry points which internally reach far more code, so "not referenced"
is not "not exercised". Applied across all contexts it produced alarming numbers (loan
151/165, ledger 133/146) that should NOT be acted on as they stand.

**The right instrument is Go's own coverage, measured with the port as `-coverpkg` and the
CONFORMANCE package as the test target:**

    go test -coverpkg=./internal/apps/<ctx> -coverprofile=/tmp/c.cov ./internal/apps/<ctx>/conformance/...
    go tool cover -func=/tmp/c.cov

That answers exactly the question worth asking — **which port code does the golden-vector
harness actually reach** — instead of a proxy for it.

### What it says here, and it sharpens the finding rather than weakening it

    function                    unit tests    from conformance
    AccountBalanceOf              100.0%          0.0%
    AvailableOf                   100.0%          0.0%
    HeldOf                         92.9%          0.0%
    HoldNetRunningBalancesOf       92.9%          0.0%

**The hold/available implementation is well UNIT-TESTED and completely UNREACHED by the
conformance harness.** That distinction is the whole thesis of this programme: a unit test
proves the code does what its author intended; **only a vector proves it matches the
oracle.** `CLAUDE.md` — "No ported Go context is correct until its golden vectors match
Fineract's captured outputs."

So the original conclusion holds — a named non-negotiable was ungraded — and the reason is
now stated precisely: **not untested, unGRADED.**

### The rule for reusing this

Use the coverage form, not the grep. Treat a `0.0%`-from-conformance function as a
**candidate**, then confirm the way the holds case was confirmed: **ask whether any
observation behind it exists in the corpus.** For holds the answer was no — every apparent
match was a field (`withholdTax`, `amountOnHold`), and no capture carried a hold-flagged
transaction type. That confirmation is what made it a finding rather than a number.
