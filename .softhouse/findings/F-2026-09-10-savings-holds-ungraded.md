# F-2026-09-10 — a CLAUDE.md non-negotiable is implemented and ungraded

**Status:** **RESOLVED 2026-09-10 by `OH-HOLDGRADE-S`.** The capture exists (taken by
`OH-HOLDCAP-R`); both observed states are promoted (SV-07 and SV-08); two drives are
live and proven to kill; and the conformance package now actually reaches the holds
rule, so the `0.0%`-from-conformance row this finding rests on is no longer true.
The correction below still stands — coverage, not a grep, was the instrument.
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

---

## RESOLVED — the hold is now graded, and the grading provably reaches the code

Grading half of the deliberate capture/grading split (`OH-HOLDCAP-R` captured; this run
graded). **No capture was taken, no POST/PUT/DELETE issued.** One bounded context,
`savings`; `.softhouse/guards/ledger-invariants.baseline` (12 pairs) and
`.softhouse/conformance.sh` (census 17) untouched.

### The observation, re-read and re-hashed

`.softhouse/capture/savings-hold-release/`, savings account 1. The hashes in the
promoted vectors were re-verified against the committed files after writing:

    sha256(.../out/savings-hold-after-hold-account-raw.json)
      = bb6b5d50f55e1e7373e318b68aade53a6e3d0b322fe3bfe5258d4fe035a8535f   == capture_sha256
    sha256(.../out/savings-hold-after-release-account-raw.json)
      = 19852ab0a45d3d2e3b7ce0d42d1b7b347f364ea2296fd7f4fd65f1f2c24f3336   == capture_sha256

The property was re-derived from the rows, not from the brief:

    AccountBalanceOf = 1000.00 + 0.16 + 0.15 = 1000.31 (100031)   hold contributes nothing
    HeldOf           = 137.29 (13729) after the hold, 0 after the release
    AvailableOf      = 100031 - 13729 = 86302 minor units, exact; no sub-minor residue

### What was promoted

* `.softhouse/vectors/savings/SV-07-hold-reduces-available-not-balance.json` — the
  after-hold read-back; pins hold-posts (id 6, type 20 `amountHold`), balance
  `100031` unmoved, held `13729`, available `86302`.
* `.softhouse/vectors/savings/SV-08-release-restores-available-not-balance.json` — the
  after-release read-back; hold id 6 discharged by release id 7 (FK
  `release_id_of_hold_amount`), held `0`, available restored to `100031`, balance still
  `100031`.

Both are parity vectors, seam `savings-hold-release`, capability
`hold-release-available-only`, `graded_against: savings-go`, with `capture_ref`,
`capture_sha256`, `capture_case_id`, and a `citation` naming the exact JSON fields and
the three pre-hold rows.

### The gap, proven the way four runs before this one did

Two drives registered in `nexus/internal/apps/savings/conformance/impl.go`:

* `savings-wrong-hold-folded-into-balance` — the **natural mistake**: the hold is folded
  into the posted balance, so `account_balance_minor` reads the oracle's *available*.
* `savings-wrong-hold-ignored` — the hold is ignored, so held stays 0 and available
  never falls.

Measured with `kills.sh` on this tree, with and without the two vectors:

| store | vectors | hold-folded-into-balance | hold-ignored |
|---|---:|---:|---:|
| without SV-07/SV-08 | 6 | **0** | **0** |
| with SV-07/SV-08 | 8 | **1** | **1** |

Zero then non-zero is the demonstration: the defect was invisible to every previously
captured cell, because a balance-moved-on-hold port computes `1000.31 - 137.29 = 863.02`
for the balance — which is exactly the observed *available*. The after-hold vector is the
one that sees it; the release vector completes limb 4.

### The coverage instrument, now live

The three functions read `0.0%` from conformance because the savings package had no
store-driven test: `go test ./internal/apps/savings/conformance/...` exercised only
hand-built probes, so no vector could ever move the number no matter how many were
promoted. Added `nexus/internal/apps/savings/conformance/committed_store_test.go`, which
loads the committed store, asserts every vector admissible, and grades the corpus against
`savings-go` through the same `LoadStore`/`Admit`/`Run` the binary uses — with an
anti-vacuity check and an assertion that the two hold-release vectors are present. This
matches the store-driven tests the ledger, loan, branch and loanproduct contexts already
carry; it does not call the hold functions directly, so it cannot manufacture coverage —
remove the vectors and the number falls back to 0.0%.

    go test -coverpkg=./internal/apps/savings -coverprofile=/tmp/c.cov ./internal/apps/savings/conformance/...

    function                    before       after
    AccountBalanceOf             0.0%        83.3%
    HeldOf                       0.0%        85.7%
    AvailableOf                  0.0%        75.0%

The remaining uncovered statements are paths the observation does not reach: the
`ErrOrphanRelease` arm and the negative-amount arm in `HeldOf`, and `AvailableOf`'s
error return. **No vector was fabricated for them** — there is no observation of an
orphan release in the corpus, and a drive for it would kill zero.

### Controls

* `savings-go` against the full store: `VERDICT: PASS`, `vectors_loaded=8 parity_pass=8
  parity_fail=0 refused=0 inadmissible=0 harness_error=0`, `graded_cells=15
  money_cells=13 invariant_violations=0`; `kills.sh savings savings-go -> 0`.
* The five pre-existing savings drives still kill:
  deposit-not-credited `3`, half-even-daily-interest `1`, interest-posting-debits `2`,
  iota-status-ordinal `2`, running-balance-before `3`.
* Full bar: `go build ./...` clean, `go test ./...` all packages ok,
  `bash .softhouse/conformance.sh` exit 2 as the recorded DEC-2 §4.4.2 decision,
  ledger-invariants `findings == baseline` (12 pairs), guard census 17.

### What this still does NOT grade

The withdrawable balance is not `AvailableOf` alone: Fineract subtracts
`min_required_balance` and `on_hold_funds_derived` too, neither of which is ported (see
`summary.go` `AvailableOf`). That is an account-model port, not a holds-rule repair, and
the capture does not carry those columns. It stays raised, not closed here.
