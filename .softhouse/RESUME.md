# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260903-170002` (local, oracle REACHABLE) — **CLOSED CLEAN. ZERO LIVE WORKERS.**

Eight tasks dispatched, eight completed, none killed. Every coder task got a paired independent
reviewer. **Three of the five reviews returned MAJORs and one returned REJECT.**

> # ⚠ THE BAR IS RED, AND IT IS RED **BY DESIGN**
>
> `bash .softhouse/conformance.sh` exits **2 with NO probe line** — a HARD guard failure, **NOT** an
> oracle outage (the oracle is UP). **Nothing may be parked for it.**
>
> `guard_ledger_invariants` refuses the tree. Four `loanproduct` sites are RED **deliberately**: two
> independent reviewers agree the code is right and the **guard** is wrong. **The bar cannot go green
> until T509 lands.**

## THE FINDING: the guard matches a SPELLING, not a PROPERTY

Wrong in **both directions** on a money non-negotiable. **Ten items**, each verified by ≥2 tasks or by
the driver reading source — consolidated in **T509, the program's critical path**. Order is fixed:
**repair the blindness FIRST**, then re-run the tree; that arm can only *add* findings. Never narrow a
money guard while it is known blind. T514 supplied the decisive design constraint: the `go/types`
discriminator **must fail closed on unresolved value flow**.

## What landed

| | |
|---|---|
| **Published** | Closed a **2.5-day fork** — 60 local commits that had never been pushed, plus the cloud fire's 37. `origin/main...main` = `0 0`. |
| **Merged** | **T503** (4 `OPAQUE-SQL` sites made statically readable, no DEC-2 exemption) + reviews **T504 / T505 / T506 / T513 / T514**. Merged tree: build rc=0, 0 test FAILs, **zero OPAQUE-SQL**, 14 → 9 sites. |
| **Held** | **T501+T510** (savings) and **T502+T511** (loanproduct) — all four on reviewer findings, none on a technicality. |

## Next fire — the queue, in order

1. **T509 — CRITICAL PATH.** The guard repair. Nothing in the program can be graded until it lands.
2. **T515** — rework T510. **Preserve its reversal repair** (T513 verified it and flagged it for
   preservation); the REJECT is about what was built on a half-ported classification. Port
   `SavingsAccountTransactionType.java:180-188` — the third arrow T510 stopped short of. That one root
   fixes ESCHEAT, deletes the hand-rolled hold special case, and **deletes G-25 and G-27**.
3. **T516** — T514's three blocking conditions on T511.
4. **T508** — the append-only ledger `INSERT` cannot execute. T506 found the origin: Fineract
   changeset `journal-entry-3` **renamed** `createdby_id`→`created_by`; the port copied the
   **pre-rename** spellings.
5. **T512** — the scope instrument `git diff --stat main..<branch>` cannot tell "the worker wrote it"
   from "main moved on". It produced a **false accusation in this fire**, which the driver published
   and T506 caught. Use the merge base.
6. **T507** — `m_savings_account_summary` may not exist in Fineract at all.

**Merge order when repairs land:** T515 → T510 → T501; T516 → T511 → T502.

## Gates

**G-25 / G-26 / G-27 resolved against the divergence — no user gate needed**, because the premise was
checkable and false. T510 claimed "Fineract contradicts itself"; it does not. G-27 must match the
oracle (a live money bug, 0 vs 50000000). G-26 survives as a MINOR representation gap.

**No `user` gate was crossed this fire.**

## Standing item for Buyan — no agent can clear it

15 consecutive fires over 2.5 days burned on `OAuth session expired`, and **nothing escalates a
zero-turn fire** (T493/T494). Every push in that window was rejected non-fast-forward while the
wrapper logged `failed` and continued, four times per fire. It self-repaired before this fire.
**The detection exists; the consequence does not.**
