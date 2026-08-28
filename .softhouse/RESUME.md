# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005` — **CLOSED CLEAN. NO LIVE WORKERS. Bar GREEN on `main`.**

Every worker dispatched this fire was awaited. Nothing is running. `tasks.json` has **zero** tasks in
`in_progress`.

```
bash .softhouse/conformance.sh   →  EXIT 0
  probe line PRESENT (presence tested BEFORE value, P-83) reading "up"
  VERDICT: PASS — 46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible
  LDG-05 PASS | LEDGER parity 7 == pinned | money cells 39 == pinned | 13/13 wrong impls dying
  dead-path frontier 109 == pin | fail-open frontier 11 == pinned | host-state 18 == pinned
zsh .softhouse/bin/fire-program.sh --probe  →  lock self-test ROWS=27 FAIL_OPEN=0 FAIL_SHUT=0
```

---

## DO THIS FIRST — `main` carries a bar-bricking hazard that a finished branch already fixes

**`T364`.** T323's merged `guard_guards_dir_registration` uses a git pathspec `*` that **crosses `/`**, so
**any task that adds an ordinary `.sh` fixture anywhere under `.softhouse/guards` — including inside the
`ledgerguard` Go module — drives the whole bar to exit 2.** T337 proved it by planting one line. It is
**fail-CLOSED**, so it cannot produce a false PASS, and that is the only reason the driver left it rather
than merging T358 unreviewed. **`T358` (branch `softhouse/T358-t323-conditions`, head `34303ea2`) already
fixes it and is complete.** T364 reviews it; then merge.

## Then, in order
`T362` (review T357) → `T365` (a zero-value `released_at` still frees a live lock) → `T366` (land T361's
rescued review) → `T363` → `T360` → `T354` → `T355` → `T356`.

---

## Complete, committed, NOT merged — three branches

| Task | Branch | Head | Waiting on |
|---|---|---|---|
| `T358` | `softhouse/T358-t323-conditions` | `34303ea2` | `T364` |
| `T357` | `softhouse/T357-a2-11-section1-red` | `85a30a79` | `T362` |
| `T361` | `softhouse/T361-review-t353` | `b4bf2abf` | `T366` |

### ⚠ A GIT TRAP THE DRIVER CREATED, MEASURED, AND IS HANDING OVER RATHER THAN LEAVING TO BE DISCOVERED

The driver merged T361 (`380f0d64`) and then **reverted** it (`2fa4015b`) when it turned the bar red.

```
git merge-base --is-ancestor softhouse/T361-review-t353 main   →  TRUE
git ls-files | grep -c t361-review-t353                        →  0
```

**The branch's commits are in `main`'s history; its files are not.** `git merge softhouse/T361-review-t353`
will say **"Already up to date"** and restore **nothing**. Revert the revert, or cherry-pick `b4bf2abf`'s
tree. **Verify by file count, never by merge output.**

---

## What this fire did

**12 branches merged**, bar re-run by the driver on every merge result and green each time:
`T340`, `T347`, `T258`, `T336`, `T339`, `T270`, `T337`, `T323`, `T359`, `T352`, `T361`(reverted), `T342`+`T353`.

**The result that matters is not harness work.** `T352` captured the **first parity divergence ever recorded
in this program**: the reference oracle **accepts** a sub-minor-unit residue — `100.125` MNT → HTTP 200,
stored `numeric(19,6)` at scale 6, the response still declaring `decimalPlaces 2` — which the Go port's
**reader** refuses. `T359` re-derived it with its own transaction at `300.6255545`, a value chosen so HALF_UP
separates from **both** HALF_EVEN and truncation. Raised as **G-19**.

## The driver's own errors this fire, all caught by workers, all recorded

1. Told four reviewers the frontier was **109** when the fail-open frontier is **11** (`T340`).
2. Dispatch notes said `T340`/`T339` "never started". Both had run (`T340` F-7).
3. **G-19 was raised with a `MAJOR` finding that is false** — "the schema cannot represent the divergence";
   it is one line of port code, `impl.go:276-279` — **and asked Buyan to ratify what DEC-2 `:971-976`
   already ratifies** (`T359`). Corrected in place, both struck visibly.
4. Framed the `date -j` defect as live on the cloud fire; it is **latent** (`T353`).
5. Called a commit a DISPATCH RECORD while leaving the task `pending` with no branch.
6. **Merged `T361` unreviewed as a rescue and it turned `main` RED** on two HARD guards. Merge reverted, work
   preserved, filed as `T366`. The rescue was right; merging it unreviewed was not.

## Push-before-spawn
**Obeyed on all 7 dispatch batches**, minimum margin **+66 s** on batch 1. Still a convention with **zero**
mechanical backing — `T336`/`T347` established that both git-side mechanisms are dead (the post-checkout hook
does not run on the harness spawn route at all; `reference-transaction` can veto but is never invoked).

## Pause reason
**None. The fire finished its work and closed.** `G-19` is OPEN for Buyan and **blocks nothing**.
