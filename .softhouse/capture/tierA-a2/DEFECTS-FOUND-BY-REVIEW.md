# Defects in this capture rig, found by the independent review (A2-4)

**Read this before citing anything under `out/`.** Recorded by the driver, local fire `20260821-134344`,
from `.softhouse/reviews/A2-4-review-of-A2-3.md` (verdict **MICRO-FIX**). The captured bytes are **immutable
evidence and have not been altered** — that is why these defects are recorded here rather than patched into
the artefacts, which would also invalidate `MANIFEST.sha256`.

## What the review CONFIRMED — the corpus is real

- **24 of 27** non-`attempt1` refusal recipes re-issued **byte-identically ~17 hours later**. The three that
  differed each became a finding (a burned identity value in leaked PostgreSQL text; a recorded 404 that is
  now 403 because the capture's *own* account retype reordered validation).
- Nothing fabricated. Nothing promoted to `.softhouse/vectors/`. No money value decided in binary float.
- The Path B preconditions gate was driven **RED** on tenant `default` (exit 1, 5 breaches, on the JVM's own
  `HALF_EVEN` line) and on a nonexistent tenant (exit 1, 10 breaches, with an explicit *"INSPECTED NOTHING"*
  refusal). All four canary attacks were refused. The zero-input class is **closed** in that rig.

## D-1 — the 10 `attempt1-*` recipes are PROVABLY FALSE. Do not cite them.

`mkreq2.py` **overwrote the request bodies** the `attempt1-*` responses were captured against. Each
`attempt1-*.http` carries a `body-file:` pointer to `req/…json`, and that file no longer holds the body that
produced the recorded response. The visible symptom: a recorded **400 saying `isInterestRecalculationEnabled`
is mandatory** is paired with a body that **contains** it.

- The 30 `attempt1-*` files (10 recipes × `.http` / `.json` / `.status`) are **real oracle refusals** — the
  bytes came from the oracle — but their **recipes do not regenerate them**, and they are **not evidence
  about slice A2**. A2-3 labelled them "not evidence about slice A2", which was right, and preserved them
  rather than quietly redoing them, which was also right. What it did not know is that their recipes had been
  invalidated.
- **A recipe that cannot regenerate its output is a defect in the recipe** (21 Aug hygiene rule). These are
  retained, not deleted, because deleting evidence to make a rig look clean is worse — but nothing downstream
  may treat an `attempt1-*` recipe as reproducible.

## D-2 — `cap.sh`'s transport-failure handler CANNOT FIRE (P-22 class)

`set -e` terminates the shell at `code=$(curl …)`, so `rc=$?`, the diagnostic message and the `rm -f "$OUT"`
that follow are **unreachable**. Driven against an unreachable endpoint: **a stale body and a stale status
survive under a FRESH `captured-at-utc`** — precisely the artefact the `rm -f` exists to prevent.

**This is the dangerous one for future captures**: it can silently present old bytes as newly observed. Fix
before the next capture task uses this rig.

## D-3 — `manifest.py verify` is three kinds of blind

1. **Vacuous on empty input** — `OK: 0 files match`, exit 0.
2. **Non-recursive** — a fabricated observation dropped in `out/<subdir>/` is laundered as verified.
3. **Covers neither `CAPTURE-PLAN.md` (which carries all seven findings), nor the rig, nor itself.** The
   reviewer appended *"MNT rounds HALF_EVEN and money may be stored as float"* to the analysis doc and
   `verify` stayed **GREEN**.

`prove-manifest-red.py` does reproduce exactly as claimed (mutate / delete / add all caught) — it proves the
hash comparison works, not that the manifest covers what matters.

## D-4 — finding 2's characterisation is WRONG (the premise is right)

A2-3: *"the oracle can create a product that can never disburse."* The premise holds — two mapping rows
persist, no unique constraint in the deployed DDL, and the 403 replays byte-identically. But the reviewer
**disbursed loan 3 on that same product at HTTP 200 by omitting `paymentTypeId`**. Only the **duplicated
payment-type path** detonates. The product is not bricked.

## D-5 — finding 7 is WORSE than stated, and it touches a non-negotiable

`acc_gl_journal_entry` stores **no classification**, so already-posted entries **retroactively re-render**
under a retyped account: entries 4 and 7 read `ASSET` at capture and read `INCOME` now. **An append-only
ledger that displays mutated history.** CLAUDE.md: *the ledger is double-entry and append-only; corrections
are reversing entries.* The Go port must carry the classification **on the entry**, not resolve it through a
mutable account row. This is a design input to slice **A1**, not a defect in this capture.

## Reviewer's own disclosure

Its control disbursement moved loan 3 to active and created journal entries 9 and 10. No other rows created
or deleted, no container touched, nothing promoted. PostgreSQL-only re-verified: 0 prohibited-engine hits,
PostgreSQL 18.3.
