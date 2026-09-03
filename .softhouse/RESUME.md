# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260902-2000` — CLOSED CLEAN. ZERO LIVE WORKERS. THREE REVIEWED STACKS MERGED.

> # ⚠ READ THIS BEFORE ANY OTHER LINE: THE LOCAL PIPELINE IS DEAD AND ONLY BUYAN CAN FIX IT
>
> **No fire has advanced this migration since 2026-08-29.** Measured on `origin/main` after
> `git fetch --unshallow` (the cloud clone arrives shallow at 60 commits, and the first version of this
> table was truncated at the graft — it said 14 real commits for 08-29 where the truth is 505):
>
> | Day | commits | bookkeeping no-ops | real work |
> |---|---|---|---|
> | 2026-08-25 | 3 | 3 | **0** |
> | 2026-08-26 | 18 | 18 | **0** |
> | 2026-08-27 | 104 | 16 | 88 |
> | 2026-08-28 | 566 | 7 | 559 |
> | 2026-08-29 | 513 | 8 | 505 |
> | 2026-08-30 | 18 | 18 | **0** |
> | 2026-08-31 | 18 | 18 | **0** |
> | 2026-09-01 | 2 | 2 | **0** |
>
> Eighteen consecutive local launchd fires (six a day) took the lock, ran the wrapper reconcile,
> released, and did nothing — about 90 seconds each. The wrapper classified the last one itself:
> ***"THE DRIVER PRODUCED 0 MODEL TURNS** and no quota rejection was recorded — cause UNKNOWN"*, rc=`1`.
>
> **It is not the quota.** `classify_driver_turns()` (`.softhouse/bin/fire-program.sh:2442`) emits a
> *different, named* line when a rate limit rejects a fire, and that line was not written. Zero assistant
> events with no rejection is the CLI failing to produce a turn at all.
>
> **AND IT IS THE SECOND OUTAGE, NOT THE FIRST.** 08-25/26 is the same shape — 21 fires, 0 real commits —
> and the program recovered on 08-27 with nothing recorded about why it stopped or restarted. So the
> failure recurs, and both times it passed unremarked. **The wrapper DETECTS a zero-turn fire; nothing
> ESCALATES one.** A fire that cannot run is exactly the fire that cannot report that it could not run,
> so the alarm cannot live inside the fire. Filed as **`T493`/`T494`**, with the good property that it can
> be driven RED/GREEN against *recorded truth*: 08-25/26 and 08-30/31/09-01 are known-RED windows and
> 08-27/28/29 known-GREEN.
>
> **WHAT BUYAN MUST DO — no agent can, the Mac mini is unreachable from the cloud sandbox:** read
> `/Users/buv/Library/Logs/gerege-nbfi/fire-20260901-080005.jsonl`, then run `claude -p "ok"` by hand and
> read the real error. An expired credential is the first hypothesis, not the established cause.
> **Until that host produces model turns again, the oracle-reaching half of this program is stopped** —
> no vector can be captured and no conformance verdict can be reached at all.

## Oracle state — MEASURED, NOT ASSUMED

`conformance.sh` on main at fire end: **EXIT 2, probe line PRESENT and reading `down`**, no HARD guard
failure. All three STEP-4 outage conditions hold. No Docker daemon, no PostgreSQL, `pg_isready` silent.
**VERDICT: UNUSABLE — THIS IS NOT A PASS**, and this fire never claimed one.

## What landed — three reviewed stacks, tree-attested

| Stack | Deliverable |
|---|---|
| `T487`+`T490`+`T495` | **`docs/analysis/tierA-a1-behaviour.md`** — slice A1, journal-entry posting: the double-entry engine and the money core of Tier A, which **had no behaviour document at all** while A2's has existed for eleven days |
| `T488`+`T491`+`T497` | **`docs/analysis/tierD-gl-corpus-capture-plan.md`** — 30 capture cases + attestation step + one de-scoped case, ranked for scarce oracle time |
| `T489`+`T492`+`T496` | **`docs/analysis/tierC-platform-gap-audit.md`** — 44 rows; **Tier C is a RANGE, ~33k–84k LOC, not 180k** |

**Merge attestation:** graded on the **merge result** in a scratch worktree outside the repo; landed tree
verified byte-identical to the graded tree **`265f9192b6eea682f8975ec57dfebf201442f7cd`**. Bar identical on
`main` and on the merge result — exit 2, probe present reading `down`, no HARD guard failure, every graded
census identical including `PNUMBER-CITATIONS`. **The only claim made: the merge moves nothing the bar can
still grade.** 7,305 insertions / 15 files.

## The findings a future fire must not lose

1. **A fifth binary-float money decision, and it ROUTES a posting.** `SavingsTransactionDTO.java:51`,
   `overdraftAmount.doubleValue() > 0`, reached from 8 call sites. The four `floatValue` sites take an
   absolute value; this one sends the posting to a **different GL account pair**. `T495` then proved by a
   **structural** sweep over all 63 scope files that there is **no sixth**, and that
   `new BigDecimal(double)` appears nowhere in scope.
2. **There are TWO rounding sites, not one.** `MathContext(19, HALF_UP)` is 19 **significant digits**;
   `numeric(19,6)` is 6 **decimal places**. The INSERT is the second, and it is the one that fixes the
   value parity is graded against. **`TDG-P1` (rank 1a) exists to observe what PostgreSQL does there —
   round, truncate or error — and no vector on an oracle-computed amount may be promoted until it is
   answered.** Unanswerable without a database.
3. **`tierB-branch` was MIS-SCOPED and is now fixed.** Its paths held only `fineract-branch`, whose
   `teller/service/` files are **interfaces**; the implementations are the 1,225 LOC in
   `fineract-provider` that the Tier C audit had classified away. As scoped it would have ported three
   interfaces with no implementations. Corrected to 5,162 LOC **before** anything was planned on it.
4. **Reversal MUTATES the original row**, in **five** mutually inconsistent shapes — one of which writes
   `reversed = true` onto a **newly created** row. Load-bearing against our append-only ledger.
5. **Before planning `tierB-branch`:** Fineract's timezone is **per-tenant**, `m_office` has no zone
   column, and `FineractPlatformTenant.getTimezoneId()` is its **sole** source. Ulaanbaatar (+08) and
   Hovd (+07) **cannot coexist in one tenant** as the schema stands — and branches are what span them.

## OPEN GATES — none blocks work today

`G-2`…`G-6`, `G-8`…`G-13`, `G-19`, `G-20` (**amended this fire**), `G-21`, `G-22`, **`G-23` (new, RESERVED)**,
**`G-24` (new, DECIDED by the driver — veto only)**. No CONTRACT gate open, no `user` gate crossed.

**`G-23` is the one for Buyan:** CLAUDE.md's Tier C rule is *"map onto Nexus first"* and **there is nothing
here to map onto** — `nexus/go.mod` has zero `require` directives, `go list` returns six packages that are
all Tier 0/A domain work or the conformance harness, `nexus/internal` holds only `apps/{ledger,loanschedule}`,
no `.gitmodules`, no second module. Found by `T489`, reproduced in full by `T492`, verified a third time by
the driver. Cost: 50,846 LOC unclassified, so Tier C is a 2.5× range instead of a number.

## NEXT FIRE STARTS HERE

1. **If you reach the oracle** — `TDG-P1` **first** (rank 1a): it unblocks a whole class of vectors and is
   four SQL statements. Then the capture plan in its stated order.
2. **`T500`** — the one round of this fire that landed **without its own reviewer**: the three repairs
   `T495`/`T496`/`T497`. Stated rather than hidden. Each **refuted** part of what it was asked to apply, and
   those refutations are unreviewed — starting with "there is no sixth float site".
3. **`T493`/`T494`** — make a no-op fire streak *escalate*. Four days were lost twice to a failure that was
   detected and never reported.
4. **`T498`** (G-12's strongest drift mechanism: a 10,000-row seed cap with a silent zero fallback — no
   prior corruption needed, no exception, no log line) and **`T499`** (B-11: make the float guard match the
   **shape** `\.(float|double)Value\s*\(`, not a word list — the mechanical form of P-104).
5. The 53 instrument tasks remain READY and were **deliberately not touched**: each must be graded on its
   merge result, and no trustworthy verdict exists while the bar is UNUSABLE.

## Pause reason
**Not paused. Fire closed clean, zero live workers, lock released.** The program's next move is gated on
one thing this driver cannot reach: the Mac mini producing model turns again.
