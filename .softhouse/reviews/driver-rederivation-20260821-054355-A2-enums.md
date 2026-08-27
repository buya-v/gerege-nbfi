# Driver re-derivation — the three "already measured" traps written into A2-8's brief

**Local fire `20260821-054355`. Pinned checkout `426a23544`.** Written BEFORE A2-8 is ever dispatched.

## Why this exists

The driver wrote three traps into A2-8's brief as *already measured facts*, on A2-1's authority. This
program's recurring defect (P-13, P-20 — six instances now, every one caught by a worker rather than
by the driver) is precisely **the driver restating a worker's finding slightly wrong and shipping the
restatement as a premise**. So each was re-derived from source before the brief can be acted on.

**Both A2-1 claims are CONFIRMED, exactly as stated. A third hazard was found that neither A2-1 nor
the driver had recorded.**

## Trap 1 — `PortfolioProductType.fromInt` is not the inverse of `getValue()` — CONFIRMED

`fineract-core/src/main/java/org/apache/fineract/portfolio/PortfolioProductType.java`
[VERIFIED: driver read of the pinned source, this fire]

| declared | `getValue()` | | `fromInt(v)` for v = | yields | whose `getValue()` is |
|---|---|---|---|---|---|
| LOAN | 1 | | 1 | LOAN | 1 ✓ |
| SAVING | 2 | | 2 | SAVING | 2 ✓ |
| PROVISIONING | 3 | | 3 | **CLIENT** | **5** ✗ |
| SHARES | 4 | | 4 | **PROVISIONING** | **3** ✗ |
| CLIENT | 5 | | 5 | **SHARES** | **4** ✗ |
| WORKING_CAPITAL_LOAN | 6 | | 6 | WORKING_CAPITAL_LOAN | 6 ✓ |

`fromInt(x).getValue() != x` for x ∈ {3, 4, 5}, and the damage is a **3-cycle: 3 → 5 → 4 → 3.** A Go
port that defines one integer↔enum mapping and uses it in both directions is silently wrong for
PROVISIONING, SHARES and CLIENT, and silently *right* for LOAN, SAVING and WORKING_CAPITAL_LOAN —
which is the worst possible distribution, because the products a first test exercises are the three
that work.

## Trap 2 — `CashAccountsForLoan` and `AccrualAccountsForLoan` collide at 22/24/25 — CONFIRMED

`fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java`
(cash: 23 members; accrual: 25 members) [VERIFIED: driver read of the pinned source, this fire]

Of the 22 integer codes the two enums share, **19 agree and exactly three disagree** — 22, 24 and 25,
precisely as A2-1 stated, no more and no fewer:

| code | `CashAccountsForLoan` | `AccrualAccountsForLoan` |
|---|---|---|
| 22 | `CLASSIFICATION_INCOME` | `INCOME_FROM_CAPITALIZATION` |
| 24 | `INCOME_FROM_DISCOUNT_FEE` | `BUY_DOWN_EXPENSE` |
| 25 | `FEES_RECEIVABLE` | `INCOME_FROM_BUY_DOWN` |

Note code 24: **an INCOME member in one enum and an EXPENSE member in the other.** A cross-mapping
there does not merely post to the wrong account, it posts to the wrong *side*.

## Trap 3 — NEW, found by this re-derivation, recorded by neither A2-1 nor the driver's own brief

**The name↔code relation is not a function in EITHER direction across the pair.** Two members carry
the same NAME at different CODES, while code 25 simultaneously carries two different names:

| name | code in `CashAccountsForLoan` | code in `AccrualAccountsForLoan` |
|---|---|---|
| `FEES_RECEIVABLE` | **25** | **8** |
| `PENALTIES_RECEIVABLE` | **26** | **9** |

So a port keying on the **code** cross-maps (25 = `FEES_RECEIVABLE` under cash, `INCOME_FROM_BUY_DOWN`
under accrual), *and* a port keying on the **name** cross-maps (`FEES_RECEIVABLE` = 25 under cash, 8
under accrual). **There is no single keying that is safe.** The only correct model is two entirely
separate types with no shared representation and no implicit conversion between them — which is
stronger than what A2-1's finding, or the driver's first draft of the A2-8 brief, actually asked for.
A2-8's brief has been amended to require it.

## Trap 4 — `acc_gl_journal_entry` carries no classification — NOT re-derived here

`[UNVERIFIED by the driver]`. This is A1's table, not A2's, and it was left alone deliberately rather
than half-checked. It stays in A2-8's brief attributed to A2-1, marked as A2-1's finding and not as a
driver-confirmed one. **A2-9 must not treat it as established.**
