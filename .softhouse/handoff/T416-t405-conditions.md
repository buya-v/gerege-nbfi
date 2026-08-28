# T416 — T405's conditions on T397

Branch `softhouse/T416-t405-conditions`. Grant: `loanschedule/conformance/report.go`,
`ledger/conformance/admit.go` and their tests, `.softhouse/capture/t416-t405-conditions/`.

`.softhouse/conformance.sh` **was not edited** — it is held by T404. F-T405-4 ships as a REQUEST,
driven red first: `.softhouse/capture/t416-t405-conditions/REQUEST-conformance-sh-divergence-pin.md`.

**T391 LANDED ON `main` MID-TASK** (merge `e0eb4fe2`) and moved `EXEMPTION_PIN_LEDGER_PARITY`
7 → 10, `_MONEYCELLS` 39 → 63, `_WRONGIMPLS` 14 → 15. `main` was merged into this branch and
**every drive was re-run against the merged tree**. Both the pre- and post-merge transcripts are
committed, so the two readings cannot be mistaken for a disagreement. Nothing below is carried
forward by arithmetic.

Every cardinal T405 reports was **re-derived by running**, not inherited. Where I reproduce one it
is because I measured it; where I contradict T405 I say so. (I do not, on any of the six.)

---

## F-T405-5 — MAJOR, AND A MONEY DEFECT. CLOSED.

### The defect, confirmed at the site T405 names

`report.go`'s exit-1 arm summed `s.ParityFail + s.ContractFail + s.SelfTestFail` — the
**loanschedule** counters only — while `ExitCode()` reaches 1 for the ledger half through a
*separate* arm reading `s.Ledger.ParityFail + s.Ledger.RefusalFail` and
`s.Ledger.InvariantViolations`, which contributes to none of those three.

**The line-number adjudication is confirmed.** On pre-T397 `main`, `report.go:592` is the
**exit-0** prose line (`This means "matches the reference oracle …"`) — the line T397's task text
named and the line T397 fixed. The exit-1 sentence is a **different `case` arm** and T397's diff
adds and removes no line touching it. T398's follow-up attached this symptom to the wrong line;
T405 corrected it and I confirm the correction. **The site is cited by name here, not by number,
because these numbers move: it is the `case code == 1:` arm of `WriteReport`'s verdict switch.**

### RED before / GREEN after — UNIT

New file `nexus/internal/apps/loanschedule/conformance/verdict_fail_ledger_test.go`.
**This is the ledger-only FAIL fixture T405 says did not exist**, and its absence is exactly why
the defect survived: every prior test of this block reaches the exit-0 arm, so the exit-1 sentence
was one no test could make wrong (**P-45**).

Transcripts: `out/F-T405-5-RED-before.log`, `out/F-T405-5-GREEN-after.log`.

| arm | before | after |
|---|---|---|
| `ledger_parity_fail_only` (the MONEY row) | FAIL | PASS |
| `ledger_refusal_fail_only` | FAIL | PASS |
| `ledger_divergence_fail_is_counted_once` | FAIL | PASS |
| `ledger_invariant_violation_only` | FAIL | PASS |
| `ledger_parity_and_refusal_and_invariant` | FAIL | PASS |
| `both_halves` (all six figures distinct) | FAIL | PASS |
| `..._SaysWhichHalfFailed/ledger_only` | FAIL | PASS |
| `..._SaysWhichHalfFailed/no_ledger_half_says_so` | FAIL | PASS |
| the four LOANSCHEDULE-only control arms | **PASS** | **PASS** |

8 RED before, 0 after. The four loanschedule-only arms are green in **both** directions, which is
the control that the fix **ADDS** the ledger figures rather than replacing the loanschedule ones —
an arm that only asserted the ledger number would pass on an implementation that had dropped the
other three counters entirely.

`ledger_divergence_fail_is_counted_once` is there because ledger `grade.go` already folds a
divergence FAIL into `Ledger.ParityFail` by its own stated asymmetric counting rule. Adding
`DivergenceFail` again would report one failing vector as two, in the one class this program is
most careful about counting.

### RED before / GREEN after — THE REAL CORPUS

Instrument `t416-e5drive.sh`. Two binaries differing **only** in `report.go` (one built from
`main`'s bytes, one from this branch), the **correct** `ledger-go` port, **no `-ledger-impl` flag**,
three one-cell mutations of the parity vector `LDG-01-manual-je-3leg-minor-units`, each reverted
with `git checkout --`. Transcripts `out/e5-*.log`, summary `out/E5-REBASELINED.txt`.

Post-merge (T391 landed):

| mutated cell | class | ledger census | BEFORE | AFTER |
|---|---|---|---|---|
| `legs[0].gl_account_code` | structural | `parity PASS 9 FAIL 1` | `— 0 mismatched vector(s)` | `— 1 mismatched vector(s)` |
| `legs[0].amount_minor` | **MONEY, margin −1 minor unit** | `parity PASS 9 FAIL 1` | `— 0 mismatched vector(s)` | `— 1 mismatched vector(s)` |
| `total_debits_minor` | **MONEY, margin −1 minor unit** | `parity PASS 9 FAIL 1` | `— 0 mismatched vector(s)` | `— 1 mismatched vector(s)` |
| *(unmutated control)* | — | `parity PASS 10 FAIL 0` | exit 0, PASS | exit 0, PASS |

Pre-merge the same three rows read `parity PASS 6 FAIL 1` against a 7-vector ledger corpus, which
is T405's own figure reproduced exactly. Transcript `out/e4-*.log` / the first `E5` run.

The money row in full, AFTER:

```
LDG-01-manual-je-3leg-minor-units   parity   ledger_rest_posting   FAIL   18 cells (5 money)
    legs[0].amount_minor: MONEY want 10000026, got 10000025 (margin -1 minor units)
ledger parity           PASS 9    FAIL 1
VERDICT: FAIL (exit 1) — 1 mismatched vector(s), 0 invariant violation(s).
         LEDGER 1 mismatch(es), 0 invariant violation(s)  |  LOAN SCHEDULE 0 mismatch(es), 0 invariant violation(s).
         The per-vector rows above name every failing cell, and MONEY cells are marked
         MONEY there with their margin in minor units.
```

### What was added beyond the count

The **split line**, because a corrected total alone still sends a reader to the wrong half of a
700-line report. It is printed from the same fields the total is summed from, so the two cannot
drift — a second, independently maintained count there is the defect this block had just finished
being. And with **no ledger half at all** the line says
`no ledger half ran in this configuration, so this counts LOAN SCHEDULE only`, because "zero
ledger failures" and "the ledger half did not run" are different facts; both states are asserted.

Two helpers, `ledgerMismatches()` and `ledgerInvariantViolations()`, exist so the sentence and
`ExitCode()` read the **same expression** rather than two expressions that agreed by coincidence.

---

## F-T405-2 / F-T405-3 — THE ALLOWLIST. BOTH CLOSED.

### Decision: INVERT TO AN ALLOWLIST. (ENGINEERING, `chosen_by: agent`.)

The alternative the task offers — justify the blacklist against the actual capture alphabet — was
**measured and rejected on the evidence**. Across the 37 artefacts the vector store actually cites,
a numeric run is neighboured by **43 distinct bytes on the left and 37 on the right**. The
blacklist named 4 and 4. So **39 left bytes and 33 right bytes admitted by default**, including
`,` (5,186 occurrences to the right of a numeric run, 276 to the left), `_`, ` `, and a trailing
`+`. That is not a set anybody enumerated; it is the complement of one, and the complement of a
small set is where the holes were.

### The twelve rows, re-derived rather than inherited

Every one of T405's twelve reproduced exactly against the tree before I changed anything, plus its
MNT control and its one correctly-refused row. Then flipped:

| row | before | after |
|---|---|---|
| `{"formatted":"1,250,000.00"}` / `250,000.00` | ADMITS | **REFUSES** |
| `{"formatted":"1,100.12"}` / `100.12` | ADMITS | **REFUSES** |
| `{"formatted":"100.12-"}` / `100.12` | ADMITS | **REFUSES** |
| `{"formatted":"100.12+"}` / `100.12` | ADMITS | **REFUSES** |
| `{"formatted":"1 250 000.00"}` / `250 000.00` | ADMITS | **REFUSES** |
| `{"raw":100_125}` / `125` | ADMITS | **REFUSES** |
| `Total posted was 100.125. See note.` | REFUSES | **ADMITS** |
| `note=paid+100.125&locale=en` | REFUSES | **ADMITS** |
| `{"formatted":"100.125EUR"}` | REFUSES | **ADMITS** |
| `id-100.125` | REFUSES | **ADMITS** |
| `range 50.00-100.125` | REFUSES | **ADMITS** |
| `T352-amount-100.125.req` | REFUSES | **ADMITS** |
| `{"formatted":"100.125MNT"}` *(the pair's control)* | ADMITS | ADMITS |
| `16,-100.125,DEBIT` *(T405: correctly refused)* | REFUSES | REFUSES |
| all 10 live capture shapes | ADMIT | ADMIT |

**All six F-T405-3 false refusals are verified CLOSED. None is left open.** The currency asymmetry
is closed and now asserted **as a pair**, so `…EUR` and `…MNT` cannot diverge again.

### The shape

`namedDelimiter` enumerates what **terminates** a numeric token — ASCII letters, non-grouping
whitespace, an explicit ASCII punctuation allowlist, and every byte ≥ 0x80. Six bytes cannot be
classified from themselves and each is decided by **one further byte**:

- `,` ` ` `_` — a group separator only in a `digit SEP digit` context;
- `.` — continues the number only when a digit follows;
- `-` `+` — a **sign** (value-changing) only where there is no token beside it to separate; a
  **separator** where an identifier or a number sits on its far side;
- `e` `E` — an exponent marker only where an exponent shape follows.

A byte in none of those classes is **not** a boundary and the occurrence **REFUSES**. That is the
inversion, and `TestAnUnnamedByteRefusesRatherThanAdmits` asserts it directly on eight control
bytes, both sides, with a named-delimiter control so the test is not a function that refuses
everything.

**NO FLOAT, NO PARSE, NO `strconv`, NO ARITHMETIC ON THE AMOUNT.** Every test is "is this byte in
`'0'..'9'`" or "is this byte a letter". The only arithmetic is on byte offsets (`i-1`, `i-2`,
`end+1`, `end+2`). Swept independently over the whole diff for
`float|strconv|parse|json.Number|big\.|math\.|atoi|itoa`: the hits are comment text stating the
prohibition. The bar's four no-float guards and the in-report census pass.

### The ambiguity, decided and recorded

`16,100.125,DEBIT` (CSV field separator) and `1,100.125` (thousands separator) are the same bytes
in the same order and nothing local separates them. **Both refuse.** A CSV artefact would have to
widen its citation — exit 2, named reason, fixed in the same fire. The other direction is a wrong
amount accepted, silently, as the reference oracle's own characters for money. Those costs are not
symmetric. `TestTheAmbiguousGroupSeparatorResolvesTowardRefusal` records the choice so it cannot be
reversed by accident, and asserts the unambiguous JSON forms still admit.

### The healthy control (P-98)

A control that refuses everything is the same defect as one that cannot fail, so the table carries
**10 live-capture-alphabet rows that must ADMIT** — measured, not guessed: across the 37 cited
artefacts the bytes actually observed beside a cited amount text are ` ` and `:` on the left and
newline, `)`, `,` and `}` on the right. The table also has its own anti-vacuity arm: it fails if
either direction is empty. And the whole store still measures **`ledger inadmissible 0`**, across
T391's three new accrual vectors as well.

### RED / GREEN

New file `nexus/internal/apps/ledger/conformance/verbatimallowlist_test.go` (kept separate from
`verbatimboundary_test.go` so T397's own drive stays byte-identical as the record of what T397
fixed). Run against `main`'s `admit.go`: **31 subtests RED** (12 boundary rows, 16 unnamed-byte
rows, 1 ambiguity). Against this branch: **67 subtests PASS, 0 FAIL**, including every one of
T397's own rows in `TestTheBoundaryRuleFormsNoNumber` and both layers of its P-45 control.
Transcripts `out/F-T405-2-3-RED-before.log`, `out/F-T405-2-3-GREEN-after.log`.

---

## F-T405-4 — the divergence-class pin. REQUEST, driven red.

Re-derived (`t416-e4drive.sh`, `out/e4-*.log`, `out/E4-REBASELINED.txt`), and **T405's narrowing
against its own first statement is confirmed**:

| store state | declared | parity | refusal | money cells | inadmissible | divergence PASS | the four pins |
|---|---|---|---|---|---|---|---|
| baseline | 0 | 10 | 6 | 63 | 0 | 1 | GREEN, correctly |
| **DIVERGENCE vector inadmissible** | 0 | 10 | 6 | 63 | **1** | **0** | **GREEN — the hole** |
| PARITY vector inadmissible | 0 | **9** | 6 | **58** | 1 | 1 | RED — already caught |

`inadmissible` is **not** unpinned in general. The hole is **specific to the divergence class**:
the one class T397 routes a new refusal into, and the one whose disappearance moves no pinned
number. `grep -c` over `.softhouse/conformance.sh` returns **0** for `ledger inadmissible`, for
`INADMISSIBLE` and for `divergence vectors` — the bar reads neither figure anywhere.

**Decision: pin it.** `EXEMPTION_PIN_LEDGER_INADMISSIBLE=0` and
`EXEMPTION_PIN_LEDGER_DIVERGENCE_PASS=1`, both **measured by RUNNING** (P-83), read by the existing
`_census_one` in the existing `_cmp` block. Three hunks, full patch text and both `sed` expressions
in `REQUEST-conformance-sh-divergence-pin.md`. The extractions were driven against the three real
transcripts (`out/PINREQ-drive.txt`): the four existing pins stay GREEN on the divergence mutation
while the two proposed pins go RED; both sets green on the unmutated store (healthy control); the
parity row is the specificity control.

---

## F-T405-6 — the false claim, corrected, and the branch behind it

T397's comment said the verdict qualifier and the census "can never disagree about how many there
are". **T405 is right that this is false.** `recordedDivergences()` sums the ledger's **GRADED**
counters; the census prints `(pinned n)` from `DivergencePinCount()`, the **LOADED** population.
A divergence vector that loads and is then refused admission is in the second and not the first —
driven above: `divergence vectors PASS 0 FAIL 0 (pinned 1)`.

The comment now states the narrower thing that **is** true: this figure and the census's own
PASS/FAIL pair read the same two fields, so *those* cannot drift; the pin is a third number and is
tested separately.

I also took T405's behavioural remedy, because the coupling resolved toward the
**safer-sounding** sentence: with zero graded divergences the exit-0 arm printed
`NO DIVERGENCE IS RECORDED in this store` over a store pinned to hold one. That state now has its
own words — `THIS STORE IS PINNED TO HOLD n DIVERGENCE VECTOR(S) AND THIS RUN GRADED NONE OF THEM`.
T397's own subtest asserted the false sentence, so its **expectation** was corrected rather than
the test deleted, and it now follows `DivergencePinCount()` instead of hard-coding today's value —
at a zero pin the original sentence is correct again and the arm asserts it. Real store unaffected:
`IT EXCLUDES 1 RECORDED DIVERGENCE(S)`, exit 0.

---

## SCOPE, and the `admit.go` lines for the serial merge against T391

`git diff main...HEAD -- .softhouse/conformance.sh` is **0 lines**. No other bounded context
entered. Files changed outside the grant: **none**.

**`admit.go` — the exact lines touched, against `main` before my merge:**

| main lines | what |
|---|---|
| **1332–1334** | inside `tokenBoundedIndex`: the two `leftOK`/`rightOK` neighbour calls and the `if`, replaced by `if leftDelimits(raw, i) && rightDelimits(raw, end)` |
| **1342–1352** | the whole of `numericLeftNeighbour` and its doc comment, replaced |
| **1354–1364** | the whole of `numericRightNeighbour` and its doc comment, replaced |

Nothing else in the file. **T391's hunks are at 182–243, 243–300 and 981** (the per-leg slot
block, the outside-the-product block, and the one-line `if l.SlotCode == 0 && !chart[...]` change).
I read `git diff main...softhouse/T391-accrual-promotion -- '*admit.go'` before touching the file
and kept the change disjoint. Verified by `git merge-tree`: `admit.go` is "changed in both" with
**zero conflict markers**, and the merge has since been performed and is green.

---

## VERIFICATION

```
go build ./...            exit 0, no output
go test -count=1 ./...
    ok  github.com/gerege/nexus/internal/apps/ledger                          0.462s
    ok  github.com/gerege/nexus/internal/apps/ledger/conformance              4.668s
    ok  github.com/gerege/nexus/internal/apps/loanschedule                    3.356s
    ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance       30.185s
```

Transcripts `out/go-build.txt`, `out/go-test.txt`.

**Bar** — `bash .softhouse/conformance.sh` (never `sh`) from a clean tree after `git add -A` and
commit. Transcript `out/BAR-t416.log`. See the final section of this file for the post-merge run.

`P-<n>` tokens used: P-1, P-02, P-03, P-22, P-35, P-45, P-66, P-83, P-89, P-98, P-8, P-9, P-10 —
all defined in `.softhouse/patterns.md` (`ids=98`). No bare token for a pattern that does not
exist; the bar's `PNUMBER-CITATIONS` gate is `VERDICT PASS`.
