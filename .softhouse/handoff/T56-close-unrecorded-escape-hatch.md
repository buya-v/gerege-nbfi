# T56 — closing the `unrecorded_fields` false-PASS path (T9 findings F-1a, F-1b, F-5)

Run `2026-08-17-run1-harness-schedule-poc`, context `harness`, role `test_writer`.
Branch `softhouse/T56-close-unrecorded-escape-hatch`.

Raised by `.softhouse/reviews/T9-harness-and-vectors-review.md` §4.1 (F-1), §4.3 (F-5), §7 items 1,
2 and 4.

**No vector file, `capabilities.json`, `PIN.json`, `contract/contract.go` or `impl_hook.go` was
touched.** [VERIFIED: `git diff --name-only main...HEAD` plus the working tree lists exactly
`conformance/admit.go`, `conformance/capability.go`, `conformance/vector.go`,
`conformance/structural_test.go`, `.softhouse/conformance.sh`.]

---

## 0. A process finding first: F-9 recurred, on this task

The brief said this worktree would be cut **after** the T8/T20/T9 merges and told me to confirm it.
It was not. The worktree was cut from `30a030e`, which is the T8/T20 merge point but **two commits
before** `d36fc53 merge T9`. The eleven `P-*.json` vectors were present; **the T9 review itself was
absent** — the very document the task is derived from.

[VERIFIED: `git merge-base --is-ancestor d36fc53 HEAD` → NO at start; `ls
.softhouse/reviews/T9-harness-and-vectors-review.md` → No such file.]

I fast-forwarded to `d36fc53` before reading anything. The only content in those two commits is the
review document itself, so the fast-forward could not have changed the artefact under change.

This is T9's own **F-9** happening again, one fire later, to the task that was written to fix F-9's
siblings. The remedy T9 proposed — "a review brief must name the branch, or the worktree must be cut
from the commit containing the artefact" — is evidently not yet mechanised. **Recommendation: the
worktree cut point should be a named commit in the task record, and the worker's first action should
be an assertion on it rather than a request to eyeball a directory listing.** A worker that had
skipped the confirmation step here would have read no T9 review at all and would have had to
reconstruct the finding from the driver's restatement — which the brief itself warns is "the
driver's restatement, not the source".

---

## 1. Baseline, recorded verbatim before any change

At `d36fc53`, toolchain `. .softhouse/bin/go-env.sh`, module root `nexus/`:

```
=== go build ===        (no output, exit 0)
=== go vet ===          (no output, exit 0)
=== gofmt -l . ===
internal/apps/loanschedule/contract/contract.go
=== go test ===
ok  	github.com/gerege/nexus/internal/apps/loanschedule/conformance	0.884s
?   	github.com/gerege/nexus/internal/apps/loanschedule/conformance/cmd/conformance	[no test files]
?   	github.com/gerege/nexus/internal/apps/loanschedule/contract	[no test files]
```

`gofmt -l` reporting exactly `contract/contract.go` and nothing else is the expected state under open
gate **G-3**. That file was never formatted, never opened for writing, and its SHA-256 still matches
`PIN.json` — the harness verifies that on every run and the run below is exit 2 for the registered-
implementation reason, not a digest reason.

```
$ .softhouse/conformance.sh
EXIT=2
    parity vectors          PASS 0    FAIL 0
    harness errors          16
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.

$ .softhouse/conformance.sh --prove
EXIT=0
PROOFS: 15 passed, 0 failed
```

Harness self-test over the pristine store, which is the number the changes must not move:

```
$ conformance -self-test
EXIT=0
    parity vectors          PASS 11   FAIL 0
    inadmissible            0
    cells compared          1046 graded, 22 ungraded (never recorded by the capture)
    monthend.reanchor      killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural], MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural]
```

---

## 2. T9's exploit, reproduced BEFORE the change

Reproduced exactly as §4.1 describes it: every one of the nine cells that
`MONTHEND-CONTINUE-FROM-CLAMPED-DAY` names in `divergent_cells`, in **both** `P-02` and `P-02b`, set
to `1999-01-01` and added to that row's `unrecorded_fields`. Scratch copy under `/tmp/t56/exploit-store`;
the committed store was never written to.

```
$ python3 /tmp/t56/exploit.py .softhouse/vectors /tmp/t56/exploit-store
  P-02-monthend-seed-day-31.json: 9 divergent cells set to 1999-01-01 AND withdrawn from grading
  P-02b-monthend-seed-day-30.json: 9 divergent cells set to 1999-01-01 AND withdrawn from grading

$ conf-before -self-test -store=/tmp/t56/exploit-store -replay-store=.softhouse/vectors
EXIT=0
P-02                         parity           path_a_e... PASS             38       11
P-02b                        parity           path_a_e... PASS             38       11
    monthend.reanchor      killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural], MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural]
    parity vectors          PASS 11   FAIL 0
    inadmissible            0
    cells compared          1028 graded, 40 ungraded (never recorded by the capture)
VERDICT: SELF-TEST PASS (exit 0). The harness grades correctly. NOT a conformance PASS.
```

[VERIFIED: reproduced end to end.] Every month-end date in the store is garbage, no month-end date is
compared, the report says the capability is killed, and the run exits 0. This is the defect class the
pipeline exists to prevent: **the harness reporting that it graded something it did not grade.**

## 3. The same exploit AFTER the change

```
$ conf-after -self-test -store=/tmp/t56/exploit-store -replay-store=.softhouse/vectors
EXIT=2
P-02                         parity           path_a_e... INADMISSIBLE      0        0  graded_against[2] (MONTHEND-CONTINUE-FROM...
P-02b                        parity           path_a_e... INADMISSIBLE      0        0  graded_against[2] (MONTHEND-CONTINUE-FROM...
    UNBACKED in_graded_domain claims: monthend.reanchor
    parity vectors          PASS 9    FAIL 0
    inadmissible            2
    cells compared          952 graded, 18 ungraded (never recorded by the capture)
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

The `killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY` line is **gone** and `monthend.reanchor` is
reported **UNBACKED**. Both defects fire independently on the same file — the refusal names both
`(finding T9-F1b)` on the counterfactual and `(finding T9-F1a)` on each populated-yet-withdrawn date.

Two refusal messages, verbatim, one of each kind:

```
graded_against[2] (MONTHEND-CONTINUE-FROM-CLAMPED-DAY) divergent_cells[0] "period[2].due_date" names
a cell this vector's OWN expect.periods[2].unrecorded_fields WITHDRAWS from grading. A structural
kill has no margin to carry its evidence, so its whole claim is that these cells are compared — and
this one is not. Nothing would catch a port that got it wrong, yet the report would print the
capability as killed (finding T9-F1b). Either record the cell and grade it, or stop claiming a kill
that rests on it

expect.periods[2].due_date is marked unrecorded but carries the date 1999-01-01. A cell withdrawn
from grading must be EMPTY: nothing compares it, so a value written there is a claim no run can check
and a later reader cannot tell it from an observation (finding T9-F1a). Either record the date and
grade it, or leave the cell at the zero date
```

**And the corpus is unaffected.** Pristine store, after the change:

```
$ conf-after -self-test
EXIT=0
    parity vectors          PASS 11   FAIL 0
    inadmissible            0
    cells compared          1046 graded, 22 ungraded (never recorded by the capture)
    monthend.reanchor      killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural], MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural]
```

1046 graded / 22 ungraded, byte-identical to the baseline. No committed vector was made inadmissible
and no cell moved between the graded and ungraded tallies.

---

## 4. What F-1a became in code

`nexus/internal/apps/loanschedule/conformance/admit.go`, in `admitPeriods`.

### 4a. The unrecordable set is now narrower than the graded set — `kind` is gone

`gradedPeriodField` is replaced by `UnrecordablePeriodFields()` /`unrecordablePeriodField`. The list
is `installment_number, from_date, due_date, principal_minor, interest_minor,
outstanding_principal_minor` — **`kind` is deliberately absent**, so it may never be declared
unrecorded at all.

Reasoning, all of it structural rather than stylistic:

- The replay grader cannot construct a row without a kind: `registry.go` resolves it with
  `periodKindByName` and returns a hard error. A cell the harness *cannot* treat as absent must not
  be *declarable* absent.
- Every property invariant keys on it (`invOrdering`'s kind rank; `contract_row_ordering`).
- No capture seam in this corpus omits it — the 22 genuine `unrecorded_fields` cells are
  `installment_number` and `interest_minor` only [VERIFIED: enumerated across all 11 files].

This is strictly stronger than what T9 asked for (it asked only that `kind` be *checked*), and it
costs the corpus nothing.

### 4b. `from_date` / `due_date`: unrecorded means the zero date

The old code validated `p.FromDate.Valid()` and `p.DueDate.Valid()` **unconditionally**, which is why
T9's exploit had to use a *valid* garbage date (`1999-01-01`) rather than an empty one. That check is
now conditional on the cell being recorded, and the withdrawn case gets the mirror rule: the date must
be the zero `Date{}` — absent from the JSON, or `{year:0,month:0,day:0}`. `Date{}.Valid()` is already
false, so no real date can satisfy it and nothing legitimate is inconvenienced.

Both directions are covered: a withdrawn date left empty **stays admissible**, because a capture that
genuinely did not record `from_date` (Path A pass 3 records only `{type, dueDate, principal}` on a
disbursement row — `vector.go`, `UnrecordedFields` doc comment) must still be promotable. Making
dates non-withdrawable outright would have been simpler and I rejected it for exactly that reason.

### 4c. `installment_number` — the decision, and why

**Decision: 0 is the documented sentinel for absent, and only a non-payable row may use it.** A
withdrawn `installment_number` must be exactly `0`, and the row's `kind` must be `DISBURSEMENT` or
`DOWN_PAYMENT`. A `REPAYMENT` row may not withdraw it at all.

T9 offered two options and **both break the committed corpus.** That is worth stating plainly because
the brief asked me to say so if it were true:

- All 11 vectors write `"installment_number": 0` **explicitly present in the JSON** on the
  DISBURSEMENT row, *and* name it in `unrecorded_fields` [VERIFIED: enumerated across all 11 files].
- Option (a), `*int32` with "unrecorded ⇒ nil": an explicit `0` decodes to a non-nil pointer, so all
  11 become INADMISSIBLE. A `json.RawMessage` / presence-tracking variant fails identically — the key
  *is* present.
- Option (b), remove it from the unrecordable set: all 11 name it in `unrecorded_fields`, so all 11
  become INADMISSIBLE with "not a cell a capture may withdraw".

So "keep the 11 admissible" and "adopt one of T9's two representations" are not jointly satisfiable
without a vector edit, which this task forbids.

**Why the sentinel is not a weakening.** Compare it against option (a) case by case. Withdrawn +
value `5`: (a) inadmissible, sentinel inadmissible. Withdrawn + `null`: (a) admissible/ungraded,
sentinel admissible/ungraded. Withdrawn + `0`: (a) inadmissible, sentinel admissible/ungraded — and
in that one differing case the stored value is the int32 zero, which conveys no observation. There is
**no defect option (a) catches that the sentinel misses**; (a) is stricter only about whether the
author must type `null` instead of `0` to prove they meant absent. The kind restriction then removes
the residual: `0` is the frozen contract's own value for exactly the rows permitted to use it
(`contract.go`, `Period.InstallmentNumber` — "InstallmentNumber is 0 because it is not payable"), so
the sentinel stores nothing the contract does not already fix, and a repayment row — where `0` would
be a *wrong* value hiding in an ungraded cell — cannot use it.

**The one thing the sentinel does not buy, stated openly.** Option (b) would additionally *grade* the
disbursement row's `0`, catching a port that emitted, say, `7` there. The sentinel leaves that cell
ungraded, exactly as today. That is a **coverage gap, not a false-PASS path** — it is unchanged from
the pre-T56 behaviour, so nothing regressed — and it is closable by a one-token edit to each vector
file that I am not permitted to make.

> **Recommendation for the next promotion task (P2, no gate needed):** drop the string
> `"installment_number"` from the DISBURSEMENT row's `unrecorded_fields` in all 11 vectors and remove
> `installment_number` from `UnrecordablePeriodFields()`. The value already present is `0`, which is
> what the contract mandates and what the replay emits, so the corpus stays green and 11 more cells
> become graded. T9's F-1c complaint that "the disclosure is unenforceable as written" is then
> resolved at the source rather than by sentinel, and the transcription notes in the vectors should
> be corrected at the same time: they say filling the cell "would be storing a derivation as an
> observation", but DEC-1's null→0 normalisation is part of the **grading standard**, not an oracle
> observation, so grading it is legitimate. I did not do this because it is a vector-file edit.

---

## 5. What F-1b became in code

Two independent rules, because T9 named two.

### 5a. Admission — `admit.go`, `admitDivergentCell`

`admitCounterfactualKind` and `admitDivergentCell` now take `[]ExpectPeriod` rather than a bare
`periodCount`. After a divergent cell passes the existing checks (well-formed, in range, not a money
column, a field the harness compares *in general*), one more is applied: **is it a cell this vector
compares *here*?** If `v.Expect.Periods[idx].UnrecordedFields` names the field, the vector is
INADMISSIBLE.

The old code (`admit.go:294` in T9's numbering) asked only the general question. That is the whole
gap: `StructuralCellFields()` says the harness compares `due_date`; it never said *this* vector does.

The cell-name parser was factored out into `ParseDivergentCell` / `DivergentCellForm` so that
admission and coverage resolve `"period[2].due_date"` through **one** parser. Two parsers that
disagreed about a cell name would be a defect of precisely the F-1b shape — one half of the harness
policing a name the other half resolves differently.

### 5b. Coverage — `vector.go`, `Vector.StructuralKillIsCompared`; wired in `capability.go`

`CapabilityRegistry.CounterfactualCoverage` now skips any structural counterfactual for which no
divergent cell is actually compared. Such a kill does not back its capability, does not appear in the
`killed by` line, and leaves the capability in the UNBACKED list (which is a `FatalReasons` entry
outside self-test mode).

`row_order` needed its own arm, and it is where this rule earns its place: it names no field, so the
per-cell admission rule in 5a structurally cannot see it. A row-order kill is credited only if **two
rows can be told apart by a graded structural cell.** Rows are compared pairwise by index, so a
schedule emitted in the wrong order surfaces as a wrong `kind` or a wrong date and nowhere else; if
every graded structural cell holds the same value on every row, a permutation is invisible and the
kill catches nothing.

**Honest note on redundancy.** Now that `kind` can never be withdrawn (§4a), the per-cell arm of
`StructuralKillIsCompared` can only return false on a vector that rule 5a *already* refuses. It is
defence in depth, and I kept it because T9 asked for it explicitly and because
`CounterfactualCoverage` is a public method callable on vectors that never went through `Admit`. The
`row_order` arm is **not** redundant. Both arms are covered by unit tests rather than by `--prove`,
because the redundant one is unreachable through a store file — which is itself the reason it cannot
be a `--prove` case, and I would rather say that than write a proof that quietly demonstrates rule 5a
while claiming to demonstrate 5b.

---

## 6. The new `--prove` cases

`--prove` went from **15 to 20**, all passing. [VERIFIED: `PROOFS: 20 passed, 0 failed`, exit 0.]

T9's F-5 was that all 15 existing proofs perturb the single hand-authored self-test fixture: none
touched a parity vector, none touched a date cell. Cases 15 and 16 close exactly that, reusing the
review's own mutations M2 and M4.

Every case runs against a scratch copy under the script's own `$tmp`, and each is guarded by
`assert_mutated` so a perturbation that silently failed to apply cannot produce a vacuous green.

| # | case | asserts | T9 origin |
|---|---|---|---|
| 15 | `T9-F5: a one-minor-unit perturbation of a PARITY vector goes red` | exit 1, `row 6 interest_minor: expected 13 minor units, got 12` | M2 |
| 16 | `T9-F5: a DATE cell of a PARITY vector goes red, naming the row and both dates` | exit 1, `row 2 due_date: expected 2024-03-29, got 2024-03-31` | M4 |
| 17 | `T9-F1a: a POPULATED non-money cell withdrawn from grading is inadmissible` | exit 2, `is marked unrecorded but carries the date 2024-01-31` | §4.1 F-1a |
| 18 | `T9-F1b: a structural kill naming a cell the vector withdrew is inadmissible` | exit 2, `WITHDRAWS from grading` | §4.1 F-1b |
| 19 | `T9-F1b: withdrawn cells STOP backing the kill; recorded ones still back it` | both directions, on report text | §7 item 2 |

Case 15 is deliberately a **consistent** perturbation (`interest_minor` 12→13 *and*
`interest_major_text` 0.12→0.13) so that the transcription cross-check is not what catches it — the
proof is about grading, not about transcription, and proof 5 already covers transcription.

Case 16 is the one the brief was right to want. `monthend.reanchor`'s counterfactual carries
`margin_minor` of exactly `0`; its entire kill lives in the date columns. Without this proof, "the
harness compares dates" rested on reading `diffSchedule`.

Case 17 isolates F-1a from F-1b on purpose: it withdraws the **disbursement row's** `due_date`, which
no counterfactual in the store names, so only the F-1a rule can fire.

Case 19 asserts on report text rather than exit code, because **the defect this task closes was never
visible in an exit code.** It checks both directions and would fail if either broke:

- over case 18's store: exit 2, `UNBACKED in_graded_domain claims: monthend.reanchor` present, and
  `killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY` **absent**;
- over the pristine store: exit 0, `parity vectors          PASS 11`, and `killed by
  MONTHEND-CONTINUE-FROM-CLAMPED-DAY` **present**.

A rule that refused both directions would be a rule that had simply broken grading, and case 19 is
what stops a later agent from "fixing" a red run that way.

### 6a. Red/green table — every case against the pre-fix and post-fix binaries

Both binaries built from this worktree; `conf-before` from the branch point, `conf-after` from HEAD.
All stores are `/tmp` scratch copies.

```
=== 15: parity money cell (M2) ===
  BEFORE  exit 1 | monthend kill printed: YES | parity vectors PASS 10 FAIL 1
  AFTER   exit 1 | monthend kill printed: YES | parity vectors PASS 10 FAIL 1
=== 16: parity DATE cell (M4) ===
  BEFORE  exit 1 | monthend kill printed: YES | parity vectors PASS 10 FAIL 1
  AFTER   exit 1 | monthend kill printed: YES | parity vectors PASS 10 FAIL 1
=== 17: F-1a, populated + withdrawn date ===
  BEFORE  exit 0 | monthend kill printed: YES | parity vectors PASS 11 FAIL 0
  AFTER   exit 2 | monthend kill printed: YES | parity vectors PASS 10 FAIL 0
=== 18: F-1b, withdrawn divergent cell (P-02 + P-02b) ===
  BEFORE  exit 0 | monthend kill printed: YES | parity vectors PASS 11 FAIL 0
  AFTER   exit 2 | monthend kill printed: no  | parity vectors PASS 9  FAIL 0
=== T9's FULL exploit, all nine cells, both files ===
  BEFORE  exit 0 | monthend kill printed: YES | parity vectors PASS 11 FAIL 0
  AFTER   exit 2 | monthend kill printed: no  | parity vectors PASS 9  FAIL 0
=== pristine (must stay green in both) ===
  BEFORE  exit 0 | monthend kill printed: YES | parity vectors PASS 11 FAIL 0
  AFTER   exit 0 | monthend kill printed: YES | parity vectors PASS 11 FAIL 0
```

**Read this table honestly.** Cases 15 and 16 are **exit 1 before and after**: the harness could
always catch these, exactly as T9 said. They are not new capability — they are new *evidence*, and
F-5 was a finding about evidence, not about behaviour. Cases 17, 18 and the full exploit are the real
red→green: **exit 0 → exit 2**, and in 18 the false `killed by` line disappears.

---

## 7. Unit tests

`conformance/structural_test.go`, `TestT9F1UnrecordedFieldsIsNotAnEscapeHatch`, 12 subtests, all
passing. They cover what `--prove` cannot reach through a store file, and each negative subtest
asserts on the refusal's own words rather than on a boolean.

```
--- PASS: TestT9F1UnrecordedFieldsIsNotAnEscapeHatch
    --- PASS: .../the_committed_corpus's_row_shape_stays_admissible
    --- PASS: .../F-1a:_a_populated_but_withdrawn_due_date_is_inadmissible
    --- PASS: .../F-1a:_a_populated_but_withdrawn_from_date_is_inadmissible
    --- PASS: .../F-1a:_a_withdrawn_date_left_EMPTY_is_still_admissible
    --- PASS: .../F-1a:_kind_may_not_be_withdrawn_at_all
    --- PASS: .../F-1c:_a_withdrawn_installment_number_carrying_a_value_is_inadmissible
    --- PASS: .../F-1c:_a_REPAYMENT_row_may_not_withdraw_installment_number
    --- PASS: .../F-1b:_a_divergent_cell_the_vector_withdraws_is_inadmissible
    --- PASS: .../F-1b:_the_same_kill_over_a_GRADED_cell_stays_admissible
    --- PASS: .../F-1b:_an_all-withdrawn_structural_kill_covers_nothing
    --- PASS: .../F-1b:_a_graded_structural_kill_does_cover
    --- PASS: .../F-1b:_row_order_covers_nothing_when_no_graded_cell_tells_two_rows_apart
```

The first subtest is the guard that matters most: it asserts the **committed corpus's row shape**
(disbursement row withdrawing `installment_number` + `interest_minor`) stays admissible, so a later
tightening of these rules cannot silently invalidate the store.

**A limitation, stated rather than hidden.** I could not run these subtests red against the pre-fix
sources in isolation: `ParseDivergentCell` and `StructuralKillIsCompared` are new API, so reverting
the source files breaks compilation of the test file. The red evidence for the admission rules is
therefore the binary-level table in §6a, which is stronger anyway — it runs the real `conf-before`
against the real exploit and shows exit 0.

---

## 8. Final verification, after all changes

```
=== go build ===        (no output, exit 0)
=== go vet ===          (no output, exit 0)
=== gofmt -l . (from nexus/) ===
internal/apps/loanschedule/contract/contract.go
=== go test ===
ok  	github.com/gerege/nexus/internal/apps/loanschedule/conformance	1.066s

$ .softhouse/conformance.sh
EXIT=2
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

`.softhouse/conformance.sh`'s full output is **byte-identical to the baseline** [VERIFIED: `diff`
against the baseline capture reports no differences]. The verdict text is intact and the run is still
exit 2 while no implementation is registered.

```
$ .softhouse/conformance.sh --prove
EXIT=0
PROOFS: 20 passed, 0 failed
```

`gofmt -l` still reports exactly `contract/contract.go` — the expected state under gate G-3. That
file was never formatted and never written.

---

## 9. Things I found that T9 missed or overstated — flagged, not worked around

1. **T9's F-1a field list is one field too long, in the harness's favour.** T9 says
   `unrecorded_fields` accepts "`kind`, `installment_number`, `from_date` and `due_date`" and asks for
   the empty-check to be extended to all four. For `from_date` and `due_date` the pre-existing
   *unconditional* `Valid()` check already forced a withdrawn date to be a **real calendar date** —
   which is why T9's exploit had to use `1999-01-01` rather than an empty one. So the pre-fix hole was
   narrower than "any value": it was "any *valid* value". That makes the finding **worse**, not better
   — a plausible-looking wrong date is far more dangerous in a vector file than an obviously empty one
   — but the mechanism deserves to be stated correctly.

2. **T9's proposed remedies for `installment_number` both break the committed corpus.** Neither
   `*int32` nor removal from the unrecordable set can be adopted without editing all 11 vector files,
   because the JSON key is *present* with value `0` on every disbursement row. T9 rated F-1c P2 and
   "benign" and did not notice that its own §7 item 1 could not be executed as written under the
   constraint that no vector may change. Details and the chosen third path in §4c.

3. **F-1b's coverage half is, on today's rules, redundant with its admission half** for per-cell
   kills — but not for `row_order`. See §5b. I have not seen this stated anywhere and it matters,
   because a later agent reading only "CounterfactualCoverage must require at least one compared cell"
   might delete the admission rule as duplicative. It is the admission rule that produces the exit-2
   refusal; the coverage rule alone would be suppressed in self-test mode by `opts.SelfTestMode` and
   T9's exploit ran in self-test mode.

4. **A second, untouched route to the same class of false claim.** `row_order` was the gap I closed
   in §5b, but the underlying observation generalises: a structural kill is only as good as the
   *distinguishing power* of the cells it names, not their count. A kill naming nine cells that all
   hold identical values across the rows in question is as empty as a kill naming none. I handled this
   for `row_order`; I did **not** attempt it for per-cell kills, because there the named cell is by
   construction the one that differs. Flagging it as a thing a future reviewer should probe rather
   than a defect I am claiming.

5. **Not a finding, but worth recording:** T9's §4.2 F-3 (fabricated margins, byte-identical clones)
   and F-6 (9 distinct shapes, not 11) are untouched by this task and remain open. Nothing here makes
   them harder or easier.

---

## 10. Claims ledger

- [VERIFIED] The worktree was cut before the T9 merge; fast-forwarded to `d36fc53` before reading.
- [VERIFIED] All 11 vectors carry `"installment_number": 0` **and** name it in `unrecorded_fields` on
  their DISBURSEMENT row; enumerated programmatically across every file.
- [VERIFIED] T9's exploit reproduced at exit 0 with 11/11 PASS and the `killed by` line printed; the
  same store refused at exit 2 with the line gone after the change.
- [VERIFIED] Pristine store unchanged: 11 PASS, 0 inadmissible, 1046 graded / 22 ungraded, before and
  after.
- [VERIFIED] `go build`, `go vet`, `go test` clean; `gofmt -l` reports only `contract/contract.go`;
  `.softhouse/conformance.sh` exit 2 with byte-identical output to baseline; `--prove` 20/20.
- [VERIFIED] No vector file, `capabilities.json`, `PIN.json`, `contract/contract.go` or
  `impl_hook.go` appears in this branch's diff.
- [UNVERIFIED — and deliberately so] Whether a port that emits a wrong `installment_number` on a
  disbursement row would be caught. It would not, before or after this change; see §4c and the
  recommendation there.
