# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260903-170002`, chain iteration 2 (local, oracle REACHABLE) — **IN FLIGHT. FIVE LIVE WORKERS.**

This manifest was written and pushed **BEFORE the first `git worktree add`**, per STEP 0's
push-before-spawn obligation. If you are reading it on a fresh session, five workers were dispatched
and may have been killed with their parent; treat every task below as `needs_retry` with unverified
completeness, and look for its branch before assuming nothing was done.

## Dispatched this iteration (all `executor: agent`, `isolation: worktree`, `model: opus`)

| Task | Branch | What it must land |
|---|---|---|
| **T509** | `softhouse/T509-ledgerguard-blindspot` | **CRITICAL PATH.** The guard repair — ten verified items. Fix the UNDER-matching FIRST, then re-run the tree. The four `loanproduct` sites stay RED. |
| **T515** | `softhouse/T515-savings-classification-rework` | Rework T510 (T513 REJECT). Port `SavingsAccountTransactionType.java:180-188` — the third arrow. Preserve the reversal repair. Delete G-25 and G-27. |
| **T516** | `softhouse/T516-t514-conditions` | T514's three blocking C-2 findings on T511. Promote the snapshot leg; the four sites stay RED. |
| **T508** | `softhouse/T508-journalentry-insert-schema` | The append-only ledger INSERT cannot execute — wrong column spellings plus three missing NOT NULL columns. Oracle is up; capture, never synthesise. |
| **T512** | `softhouse/T512-scope-instrument` | The scope instrument cannot tell "the worker wrote it" from "main moved on". Census every place the wrong form is prescribed. |

`T507` (savings schema) is deliberately **held**: its `files_hint` overlaps T515's
`nexus/internal/apps/savings/`. Serialised, not forgotten — dispatch it after T515 merges.

## THE BAR IS RED, AND IT IS RED BY DESIGN

`bash .softhouse/conformance.sh` exits **2 with NO probe line** — a HARD guard failure
(`guard_ledger_invariants`), **NOT** an oracle outage. The oracle is UP. **Nothing may be parked for
it.** The bar cannot go green until T509 lands.

## Next, after this batch

Each of the five gets a **paired independent reviewer** before any merge. Merge order when repairs
land: T515 → T510 → T501; T516 → T511 → T502. Then T507.

## Gates

**No `user` gate crossed.** G-25 / G-27 are to be DELETED by T515 (their premise was checkable and
false); G-26 survives as a MINOR representation gap.

## Standing item for Buyan — no agent can clear it

Eighteen no-op fires over four days burned on `OAuth session expired`, and **nothing escalates a
zero-turn fire** (T493/T494). The detection exists; the consequence does not.
