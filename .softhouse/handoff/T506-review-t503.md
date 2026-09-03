# T506 — handoff: independent review of T503

Branch: `softhouse/T506-review-t503`. Role: independent reviewer. Reviewed:
`softhouse/T503-opaque-sql` @ `c482b07d`. Full review:
`.softhouse/reviews/t506-review-t503/REVIEW.md`.

## VERDICT: ACCEPT WITH CONDITIONS

**The question the brief asked — readable, or merely invisible? — is answered READABLE,
and measured rather than reasoned.** I planted six defects into T503's repaired shapes and
ran the guard on each; all six were refused, four by name at the offending line. I planted
the same defects into `main` and **two were completely invisible**. Detection power went
UP. Probe transcript in REVIEW.md §2.

Nothing here blocks the merge of `c482b07d`, and `git merge-tree` shows the merge is clean.

## Findings

| # | Grade | Against | Summary |
|---|---|---|---|
| F-1 | **MAJOR** | driver / process | The `tasks.json` scope violation recorded against T503 **did not happen**. |
| F-2 | MINOR | T503 | `workingcapital/postgres.go:361-363` promises a const↔literal coupling that does not exist. |
| F-3 | MINOR | T503 | The new ledger test does not pin array→column alignment; two same-typed pairs transpose silently. |
| F-4 | MINOR | T503 | The new `m.Apply == nil` refusal has no test driving it red. |
| F-5 | MINOR | T503 (B-1) | B-1's proposed guard fix is labelled fail-CLOSED; measured, it is purely refusal-reducing. |
| F-6 | MINOR | reviewer-found | Third guard blind spot: `postgres.InsertReturningInt64` is a mutating wrapper the exec-family regex does not name. 20+ call sites. |

## THE ONE THING THE DRIVER MUST ACT ON — F-1

**T503 committed no `.softhouse/tasks.json`.** `git show --name-only --format= c482b07d`
returns five files and `tasks.json` is not one of them; `c482b07d` is the branch's only
commit. The divergence in `git diff main..softhouse/T503-opaque-sql` is **base drift** —
T503 branched at merge-base `1762794b` and `main` has since advanced two commits that
themselves edited `tasks.json`. The two-dot diff renders main's own later edits as the
branch's deletions.

The stated merge risk does not exist. Proven, not argued:
`git merge-tree --write-tree main softhouse/T503-opaque-sql` → rc 0, no conflict, tree
`c20c3c95`; `git diff --stat main c20c3c95` → exactly T503's five files, `tasks.json`
untouched. The reversion is reachable only by `git checkout <branch> -- .` or by rebuilding
the branch from a two-dot diff.

**The instrument is the defect, and it will fire again.** `tasks.json` prescribes
`git diff --stat main..<branch>` to every worker as the scope check. That reports every
file main has touched since the branch point as a violation by the branch — and the worst
offender is always `tasks.json`, because the driver edits it on every dispatch. The driver
made exactly this distinction correctly one note earlier (T502's note: *"base-vs-main drift
from merge-base 14cf6c1f, not its writing"*) and did not make it for T503.

Actions:
1. Correct T503's `note` in `main`'s `tasks.json` — it records misconduct that the commit
   does not contain, and that record is precedent for the next scope grading.
2. Replace the scope instrument with
   `git show --name-only --format= <branch> ^$(git merge-base main <branch>)`, or the
   three-dot form, in the task template.

*(My brief instructed me to record the scope violation as a finding. I am recording the
opposite because that is what the repository says. An independent reviewer that will not
contradict its brief on a checkable fact is not independent.)*

The **fifth file**, `journalentry_test.go`, *was* a genuine out-of-`files_hint` edit — and
T503 disclosed it in handoff §3 with a reason that holds (the old test pinned
`Count(sql,"VALUES")==1` and `len(args)==22`, which the change necessarily invalidates;
"do not edit outside scope" and "keep tests green" cannot both hold). Disclosed, argued,
correct. Not a finding. The *replacement* test is F-3.

## Conditions

- **C-1 (driver).** F-1: correct the note, replace the instrument.
- **C-2.** Fix or delete the false-coupling comment at `workingcapital/postgres.go:361-363`.
  One line; may ride any microfix.
- **C-3 (→ T508).** T508 already owns `journalentry_test.go`. While correcting the column
  names it must pin array→column alignment for the pairs in F-3: `args[4]`/`args[5]`
  (`reversed`/`manual_entry`, both `[]bool`) and `args[9]`/`args[10]`
  (`createdby_id`/`lastmodifiedby_id`, both `[]int64`) are unasserted, same-typed, and a
  swap passes `go build`, `go test` and `PREPARE`. Use a fixture with pairwise-distinct
  values and assert all eleven cells.
- **C-4 (→ T509).** Carry F-5 (B-1 is refusal-reducing, not fail-closed) and F-6 (the
  `InsertReturningInt64` wrapper gap) into T509's scope.

## T503's claims — all verified independently

1. **I-4 on `journalentry_postgres.go`.** Verified three ways of my own. (a) The statement
   is an `INSERT`/`SELECT`/`FROM unnest` with no `UPDATE`, `DELETE`, `TRUNCATE`,
   `ON CONFLICT` or `WHERE`. (b) The guard reads it and produces **zero `I4-DML`** — and
   probes A/B show it *would* fire on a planted `DELETE` or `ON CONFLICT DO UPDATE` at the
   new shape. (c) `PREPARE` against the oracle planner. Repo-wide:
   `grep -rniE "(update|delete|truncate)[^\"]{0,40}(acc_gl_journal_entry|journal_entr)" nexus/`
   returns five hits, **all comments**. I-4 holds over the Go tree as far as a source-level
   guard can see.
2. **`unnest` semantics preserved.** Same 13 columns, same order, arg order matches the
   alias list element-for-element with matching casts (table in REVIEW.md §3). No
   running-balance column reintroduced — and probe C proves the guard would now *catch*
   its reintroduction, which on `main` it could not. Amounts stay integer minor units:
   `MinorUnits` is `int64`, `FormatDecimal` is `strconv.FormatInt` plus integer `/` and
   `%`, and the exact decimal text is cast to `numeric` by Postgres. No float in Go or on
   the wire. Positional zip **verified by execution**: I ran the corrected statement inside
   `BEGIN…ROLLBACK` and read the failing row Postgres printed back — every value in its own
   column. Unequal array lengths pad with NULL, so a length mismatch is the *loud* failure;
   transposition is the silent one, which is F-3.
3. **`migrate.go:93` widens, not narrows.** Measured. Under `main`'s `SQL string` a
   `Migration{SQL: fmt.Sprintf(...)}` produces **no finding at all** at its own site; under
   `Apply func` the same dynamic migration produces `[OPAQUE-SQL]` at its own line. The
   literal case was already covered on both trees (the guard analyses every string literal
   independent of the call), so the widening is specifically in the dynamic case — the
   dangerous one. Caveat, which T503 also stated: the standing refusal at `migrate.go:93`
   is gone, converting unconditional noise into conditional coverage.
4. **No DEC-2 exemption, no guard amended.**
   `git diff --name-only main..c482b07d | grep -E 'guards|docs/adr|conformance.sh|patterns.md'`
   → NONE. The exemption is written in handoff §6 as the rejected alternative with its cost
   stated. This is the most important thing T503 did **not** do, and probe D shows the
   rejection was right on the merits.
5. **Its MAJOR is real, and I found stronger evidence than it did.** Re-ran the probes:
   the shipped statement fails `PREPARE` on `createdby_id`; with `created_by`/
   `last_modified_by` it plans clean but still omits `created_on_utc`,
   `last_modified_on_utc`, `submitted_on_date` (NOT NULL, no default) and **fails at
   execution** on the first; `main`'s form fails identically. **Beyond T503's evidence:**
   the pinned Fineract checkout says the same thing without the live instance —
   `.../parts/0025_add_audit_entries_to_journal_entry.xml` changeset `journal-entry-3`
   *renames* `createdby_id`→`created_by` and `lastmodifiedby_id`→`last_modified_by`, while
   `journal-entry-1`/`-5`/`-6` add the three NOT NULL columns. **That also names the origin
   T508 will want: the Go port copied Fineract's pre-rename column spellings** — it was
   written against a schema Fineract had already migrated away from. `id` is
   `is_identity=YES BY DEFAULT`, so its omission is correct. Zero callers confirmed:
   `NewPostgresJournalEntryRepository` appears only at its own definition.
6. **Both backlog items correctly characterised, and demonstrated rather than agreed with.**
   **B-2:** `balanceNameRe` is applied to `splitCols(m[3])` (columns) and `setColumns`,
   never to `m[2]` (the table). Probe G: adding a column named `closing_balance` to the
   *same* `m_wc_loan_balance` statement fires `[I3-SQL-BALANCE]` instantly, while the
   thirteen real columns produce nothing. T503's inference stands — **every I-3 finding
   this program has acted on is the subset whose columns happen to be spelled that way**,
   which is a property of Fineract's naming, not of the tree.
   **B-1:** confirmed by probe F — restoring `r.ctx` brings `OPAQUE-SQL` back even with a
   fixed literal, so the `ctx := r.ctx` local is load-bearing, not stylistic. Mislabel at
   F-5.

## The bar, re-run by me

`bash .softhouse/guards/check-ledger-invariants.sh` (bash, never sh/zsh) in a worktree
detached at `c482b07d`: **exit 1, 10 findings, ZERO `OPAQUE-SQL`, zero findings in any of
T503's files.** The ten are T501's and T502's, byte-identical on `main`. Census
`main`→`T503`: 379→377 SQL-shaped, 63→**64** DML verbs, 52→**53** name a table, 22→21
exec-family (19→**18** mutating), 210 files both. **Every cardinal T503 reported reproduces
exactly.** The 19→18 drop is the removed `tx.Exec(ctx, m.SQL)`, and probe D measures what
that trade bought: a net gain.

`go build ./...` rc 0. `go vet ./...` rc 0. `go test ./...` 20 packages ok, 0 FAIL.
`gofmt -l nexus` → the 4 pre-existing files T503 named, none of them its own. Guard
selftest: 15 cases, 14 RED, 1 GREEN, 1 failure — case (n) "the REAL Go tree must PASS" —
**identical on `main`**, so pre-existing and not T503's.

Toolchain: pinned `go1.26.6 darwin/arm64`. All oracle probes read-only, in `BEGIN…ROLLBACK`;
nothing written to `fineract_default`.

## Scope of this task

Two files only: `.softhouse/reviews/t506-review-t503/REVIEW.md` and this handoff.
`.softhouse/tasks.json` **not touched** — verify with
`git show --name-only --format= <this commit>`, not with a two-dot diff (F-1).

### F-1 reproduced live, on this branch, during this review

I branched at `cd277641`. While I was working, `main` advanced to `e8ecae75` (the T502
disposition), which edited `tasks.json`. So:

```
$ git diff --stat main..softhouse/T506-review-t503
 .softhouse/handoff/T506-review-t503.md        | 159 ++++++
 .softhouse/reviews/t506-review-t503/REVIEW.md | 694 ++++++++++++++++
 .softhouse/tasks.json                         |  14 +-     <-- NOT MINE
$ git show --name-only --format= <my commit>
 .softhouse/handoff/T506-review-t503.md
 .softhouse/reviews/t506-review-t503/REVIEW.md
```

**The reviewer who filed F-1 has now been accused of the same violation by the same
instrument, in the same session, for a commit that does not contain the file.** That is not
an anecdote — it is the whole finding, reproduced on demand, and it will recur on every
task whose branch outlives one driver commit. C-1 is not optional.
