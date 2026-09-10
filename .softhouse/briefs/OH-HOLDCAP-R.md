# OH-HOLDCAP-R — CAPTURE ONLY. Place a hold on a savings account and release it.

Worktree: `/Users/buv/oh-gerege-holdcap` (branch `feat/OHHOLDCAPr`)
Work ONLY in that directory. **You hold the oracle.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's
checkout — do not read or write there, and **never exercise the push gate**. The driver
pushes. (See `.softhouse/briefs/README.md`.)

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE

**Do NOT write a vector. Do NOT register a drive. Do NOT touch any `.go` file.** A later
run grades what you capture. This split is deliberate: a run asked to design an oracle
write *and* grade it was killed at 251 iterations having produced nothing, while the same
objective split in two was finished in ~64
(`.softhouse/findings/F-2026-09-10-split-capture-from-grading.md`).

## WHY THIS ONE MATTERS

`.softhouse/findings/F-2026-09-10-savings-holds-ungraded.md`: the savings port exports 78
functions and conformance references **three**. Among the 75 unexercised is the entire
hold/available implementation [`nexus/internal/apps/savings/summary.go`]:

    AccountBalanceOf :228   HeldOf :315   AvailableOf :379   HoldNetRunningBalancesOf :504

And `CLAUDE.md` line 14 is a **non-negotiable**:

> **Holds are postings and alter `available` only, never posted `balance`.**

**That rule has a full implementation and no observation behind it.** Every apparent
"hold" in the existing savings captures is a *field* (`withholdTax`, `amountOnHold`,
`amountHold`, `transferOnHold`); a scan for a hold-flagged transaction type across every
savings capture finds **NONE**. **You are capturing the first one.**

## THE OBJECTIVE

**Place a hold on an active savings account, read back the account and its transactions,
then release the hold and read back again.**

Two active accounts exist — verify before using them:

    id 1  client 5  Active  balance 1000.31
    id 2  client 6  Active  balance 1000.01

The read-backs must let a later run check all four parts of the rule:

1. the hold **posts a transaction**;
2. **`available` falls** by the held amount;
3. **the posted `balance` does NOT move**;
4. **release restores `available`** and again leaves `balance` untouched.

So capture the account **before**, **after the hold**, and **after the release** — and the
transaction list at each point. A port that decrements `balance` on a hold is the natural
mistake and is invisible without step 3.

**Choose a NON-ROUND hold amount** that is strictly less than the balance — a round one
hides truncation as `100000.00` did in the loan schedule. **Work the arithmetic out first**:
the resulting cells must be whole minor units, because **G-19 REFUSES sub-minor residue**
and a careless amount creates oracle state that cannot be vectored at all.

## The path
1. Probe the oracle; confirm the two accounts and find the hold endpoint. **Skim
   `.softhouse/capture/savings/req/` for the endpoint shapes and move on** — do NOT read
   Fineract Java to rediscover an endpoint; that consumed a whole run this week.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. Capture before-state. Place the hold. Capture after-hold. Release. Capture after-release.
4. **COMMIT AS YOU GO** — commit the before-state and the hold as soon as you have them,
   then the release. Do not wait for the whole sequence.

**If the oracle refuses at any step, THE REFUSAL IS THE RESULT.** Capture the status, the
error body and the source line, commit that, and stop. `OH-INV-Q` and `OH-INV-W2` both
delivered exactly that and both merged. **Do not SQL-insert anything.**

## What the grading run needs from you
An `OWNER.md` recording: the account and amounts used, the arithmetic, which read-backs are
in `out/`, **and the observed `balance` / `available` / held figures at each of the three
points** so the next run can pin them without re-deriving. Leave a map as good as the one
`OH-WC-S` left.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip — integer tokens
  or strings, never `json.dumps` of a parsed number. A salvage was **reverted** this week
  over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death; `C-c` does not rescue it.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Capture directory named for its **SUBJECT** with an `OWNER.md`.
- Never synthesise a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; MNT = ISO 496, minor unit 2.
- **Balances are DERIVED, never written; holds alter `available` only.** This capture is
  that rule's first evidence — do not disturb it by editing anything.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Never describe member savings as insured, protected or guaranteed.** An NBFI exposes no
  deposit endpoint; this is a REFERENCE-ORACLE capture for parity only, not a product.
- **Do not touch** `.softhouse/guards/ledger-invariants.baseline`, `.softhouse/conformance.sh`,
  or **any `.go` file**.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar and the budget
You change no Go code, so the bar should be untouched: run `bash .softhouse/conformance.sh`
**once at the end** — exit 2 as the §4.4.2 recorded decision, ledger findings **12 pairs**,
census **17**.

~500 iterations. **If the hold is not placed by iteration 100, stop and commit what you
have with a note on what blocked you.**
