# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260903-170002` (local, oracle REACHABLE) — **IN FLIGHT. T510 + T511 LIVE.**

> # ⚠ THE BAR IS RED ON A MONEY NON-NEGOTIABLE, AND IT IS NOW RED **BY DESIGN**
>
> `bash .softhouse/conformance.sh` exits **2 with NO probe line**. Per STEP 4 that is a HARD guard
> failure, **NOT** an oracle outage, and **nothing may be parked for it**. The oracle is UP.
>
> `guard_ledger_invariants` refuses the tree: **9 unique I-3 sites** (was 14). Four of them are RED
> **deliberately** — T502 argued, and its reviewer T505 agreed, that they are not balance writes, and
> the correct fix is to the **guard**, not the code. **The bar cannot go green until T509 lands.**

### The finding this fire actually produced

**`guard_ledger_invariants` detects how a thing is SPELLED, not what it DOES** — and it is wrong in
**both** directions on a money non-negotiable. Seven items, each verified by at least two independent
tasks or by the driver reading source. All are consolidated in **T509, which is now the program's
critical path**. Order is fixed: **repair the blindness FIRST**, then re-run the whole tree, because
that arm can only *add* findings. Never narrow a money guard while it is known blind.

### What landed

| | |
|---|---|
| **Published** | Closed a 2.5-day fork — 60 local commits that had **never** been pushed, plus the cloud fire's 37. `origin/main...main` = `0 0`. |
| **Merged** | **T503** (4 `OPAQUE-SQL` sites made statically readable, no DEC-2 exemption) + reviews **T504/T505/T506**. Merged tree: build rc=0, 0 test FAILs, **zero OPAQUE-SQL**. |
| **Held** | **T501** — real I-3 repair, but introduced a **reversal-blind fold** (reversed deposit *doubles*). **T502** — right conclusion, refuted reasoning, defeatable guard patch. |

### Live workers — DO NOT assume these finished

| Task | Branch | Base | What |
|---|---|---|---|
| T510 | `softhouse/T510-savings-fold-reversal` | `softhouse/T501-savings-i3` | Carry `is_reversed`/`is_reversal` through the fold; apply T504's 6 MINORs. Must not reinstate a stored balance. |
| T511 | `softhouse/T511-t505-conditions` | `softhouse/T502-loanproduct-i3` | Drop the refuted guard patch; restate the argument on the posting-stream ground. |

**Each is based on the held branch it repairs, not on `main`.** Merge order: T510 → then T501; T511 → then T502.

### Next fire picks up

1. **T509** — the guard repair. Critical path; nothing can be graded until it lands.
2. **T508** — the append-only ledger `INSERT` cannot execute (wrong column names, 3 missing NOT NULL). T506 found the origin: Fineract changeset `journal-entry-3` **renamed** `createdby_id`→`created_by` and the Go port copied the **pre-rename** spellings.
3. **T512** — the scope instrument `git diff --stat main..<branch>` cannot tell "the worker wrote it" from "main moved on". It produced a **false accusation against T503 in this fire**, which the driver published and T506 caught. Use the merge base.
4. **T507** — `m_savings_account_summary` may not exist in Fineract at all.

### If these tasks still say `in_progress` when you read this

Their worker was killed with its session. They are **not** running. Mark `needs_retry`, rescue what
is on each branch, treat completeness as unverified.

### Standing item for Buyan — no agent can clear it

15 consecutive fires over 2.5 days burned on `OAuth session expired`, and **nothing escalates a
zero-turn fire** (T493/T494). Every push in the same window was rejected and the wrapper logged
`failed` and continued. It self-repaired before this fire. The detection exists; the consequence
does not.
