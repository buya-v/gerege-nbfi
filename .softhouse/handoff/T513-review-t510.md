# T513 — handoff: independent review of T510

**Branch:** `softhouse/T513-review-t510`
**Review:** `.softhouse/reviews/t513-review-t510/REVIEW.md`
**Target:** T510 `softhouse/T510-savings-fold-reversal` @ `5c4233fc`, diffed against its base
`softhouse/T501-savings-i3` @ `2e1a09df` (never against `main`).

## VERDICT: REJECT

**One sentence:** the three oracle divergences are not justified — their shared premise
("Fineract contradicts itself") is false; **G-27 must match the oracle** (ESCHEAT moves neither
Fineract balance; T510 debits 500,000₮ and pins it with a test), **G-25's justification inverts
the non-negotiable it cites** (its fact is confirmed by live capture, but `running_balance_derived`
is an available-shaped chain, not the posted balance), and **G-26 rests on a contradiction that
does not exist** (Fineract is unambiguous; the gap is representational).

## The root cause, in one finding

T510 ported Fineract's credit/debit classification **halfway**. It followed
`SavingsAccountTransaction.isCredit() → isCreditType() → getTransactionType().isCredit()` and
stopped at the second arrow. The third is `SavingsAccountTransactionType.java:180-188`:

```java
public boolean isCredit() {  // AMOUNT_RELEASE is not credit, because the account balance is not changed
    return isCreditEntryType() && !isAmountRelease(); }
public boolean isDebit() {   // AMOUNT_HOLD, ESCHEAT are not debit, because the account balance is not changed
    return isDebitEntryType() && !isAmountOnHold() && !isEscheat(); }
```

Go's `EntryType()` is the raw constructor argument (`isCreditEntryType()`), which Fineract never
folds on. Measured on the branch tree: `IsDebit(ESCHEAT)` true vs Fineract false;
`IsDebit(AMOUNT_HOLD)` true vs false; `IsCredit(AMOUNT_RELEASE)` true vs false. Fixing this one
root fixes ESCHEAT, deletes the hand-rolled hold special case, and removes the need for two of the
three gates.

## Findings

| # | grade | finding |
|---|---|---|
| MAJOR-1 | blocking | `isCreditType()`/`isDebitType()` ported incompletely; `[VERIFIED:]` tag on a half-derivation. ESCHEAT wrong by the whole balance |
| MAJOR-2 | blocking | G-25/G-26/G-27 enter the durable program record on a false source claim |
| MAJOR-3 | blocking | G-25 invokes "holds alter `available` only" to refuse the column that *implements* it |
| MINOR-1 | — | the "per-row fact vs aggregate" rule is unsound: `cumulative_balance_derived` is a per-row stored balance the rule would admit. Correct criterion is provenance |
| MINOR-2 | — | INSERT omits **seven** NOT NULL no-default columns, not three; `created_date` (named as a blocker) is **nullable**. Disclosure is prominent, count taken from XML not schema |
| MINOR-3 | — | `HeldOf` fails **open** on a reversed release (measured: `HeldOf = 0, err = nil`), contradicting its "fails closed" claim. Oracle-faithful, but undocumented |

## Verified and upheld — do not re-litigate in the rework

- **RED evidence reproduced exactly** on the unmodified T501 tree: `AccountBalanceOf(undone
  deposit) = 20000000, want 0`. T510's figure to the digit.
- **Negative control genuinely discriminates** (P-45): planting `IsVoid() { return true }` fails
  `TestReversedAndReversalRowsAreVoidInEveryDerivation` on five assertions of the mixed stream.
- **`Effect()` rerooting** is structurally right; `INVALID(0)` correctly added.
- **The divergence-pinning test's oracle fixture is correct** — `{100000, 60000, 35000, 35321}`
  matches my live capture on the hold row.
- **MINOR-4's scope reasoning is honest**: Go `SavingsAccount` has 7 fields, none of the 6 needed.
  Warning is prominent; nothing calls `AvailableOf` (no production caller of any derivation).
- **Guard 8 findings / zero savings**, build green, tests green, no float, no insurance strings,
  ships disabled, scope clean (no `tasks.json`, no `guards/`) — all re-run independently.

## Live capture (new evidence, not previously in the program)

Built a savings account on the oracle instance (savings tables were empty). Raw observation:

| step | txn | type | `running_balance_derived` | `account_balance_derived` | `total_savings_amount_on_hold` |
|---|---|---|---|---|---|
| deposit 1000 | 1 | 1 | 1000.00 | 1000.00 | NULL |
| **hold 400** | 2 | **20** | **600.00** | **1000.00** | **400.00** |
| **release 400** | 11 | **21** | **1072.18** | **1072.18** | **0.00** |

Two consequences the program should keep: (1) the two columns are **different quantities** (posted
vs hold-net), not contradictory answers; (2) **interest was computed on ~1009.25, not on the
609.25 running balance**, so the G-25 divergence costs vector parity and statement rendering, *not*
interest amounts. The hold's `release_id_of_hold_amount` was back-filled to `11`, confirming
identity pairing is the oracle's real mechanism.

Footprint: client 1, savings product 1, savings account 1, 11 transactions in `fineract_default`.
Nothing in either repo modified; all Go probes were throwaway files under `/tmp`, none committed.

## Conditions for merge

1. Port `isCreditType()`/`isDebitType()` completely; delete the redundant hold special case. **Blocking.**
2. Delete G-27; fold ESCHEAT to zero; invert `TestEscheatDebitsThePostedBalance`. **Blocking.**
3. Rewrite G-25: drop the contradiction claim, drop the non-negotiable conflict, stop advertising
   `RunningBalancesOf` as `running_balance_derived`'s replacement, raise the faithful port as
   backlog, record the captured interest finding. **Blocking.**
4. Reclassify G-26 as a representation gap with an identified remedy.
5. Restate the readability criterion as provenance; name `cumulative_balance_derived`.
6. Correct the NOT NULL count to seven from `information_schema`; drop `created_date`.
7. Document or fix the reversed-release discharge.

**Preserve:** the reversal repair, the two flags + FK, `IsVoid()`, the `Effect()` rerooting, identity
pairing, `ErrOrphanRelease`, the negative control, and the divergence-pinning mechanism. The
rejection is about what was built on a half-ported classification, not about the repair T510 was
sent to make.

## Scope

Two files, both mine: `.softhouse/reviews/t513-review-t510/REVIEW.md` and this handoff.
`.softhouse/tasks.json` untouched. No source file modified.
