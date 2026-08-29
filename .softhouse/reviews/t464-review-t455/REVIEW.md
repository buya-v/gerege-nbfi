# T464 — INDEPENDENT REVIEW OF T455 (`softhouse/T455-t448-conditions`, 9 commits)

Reviewer: T464. Branch `softhouse/T464-review-t455`. Fork point `281170f0` (`main` at dispatch).
Work under review: `cbc8733c…570115935837a096deab8e670c69ced0279190f2` (three-dot).

**Every number in this file was re-derived here.** Where a figure is T455's or T448's and was
not re-measured, it says so by name. Instruments are in `instruments/`, transcripts in `out/`.
Every instrument takes its paths as arguments or assembles them from `S='.softhouse'` at run
time, so none of them spells a repo-relative literal that a dead-path census could read as
unresolvable.

---

## VERDICT: **APPROVED WITH CONDITIONS**

T455 was sent to close T448's conditions on T433. It closed them, and on the one question the
dispatch called the headline — *did T448's supplied repair actually close abuse case B?* — **T455
is right and T448 is wrong.** I re-derived that under two engines that share no primitive, and
found the case against T448's predicate is **stronger** than T455 stated it. The `(iv-a)`
fail-open is genuinely closed, refuses by both routes on the named assertion, and **does not
redden an honest tree**. `run-all.sh`'s green was bought by fixing the search: the adjudicated
pin is present ×1 and byte-identical at both refs. The disclosed out-of-scope `want_min` edit
was the right call, and I proved it three ways.

Six conditions follow. None of them reverses a T455 claim; two of them are places where a guard
T455 shipped does less than the sentence beside it says.

| id | severity | one line | evidence |
|---|---|---|---|
| **F-T464-1** | **MINOR** | Abuse B **re-opens through `printf`**, `>&2 echo` and `sys.stdout.write`. Section 10 exits **0**, `run-all.sh` exits **0**, and the regenerated transcript carries the false sentence **untagged ×1**. `printf` is already used 12× in one of the four guarded files and 5× in another. | `out/31-SEC10-PRINTF-EVASION.txt`, `out/60-SEC10-EVASION.txt` |
| **F-T464-2** | **MINOR** | The **fail-closed branch** of the new section-4 classifier is reachable **only by a crash**. A tracked non-JSON vector file containing a token raises `TypeError: 'int' object is not subscriptable`; the named assertion never runs, the `FAILURES:` tally never prints, and **15 of 25 checks are skipped**, including section 5's own controls (a)–(k). | `out/70-UNPARSEABLE-FAIL-CLOSED.txt` |
| **F-T464-3** | **LOW** | The shipped grader's own docstring still says `(iv-b2)` "lands in `(iv-a)`: reported UNGRADED, **exit 0**". At this ref it exits **1** — T455 measured that itself (its case 5). A stale sentence in the file whose whole subject is stale sentences. | `verify-capture-integrity.py:194-197` |
| **F-T464-4** | **LOW** | T455's handoff §10 attributes T448's wrong `all=2, both=1` figure to `30-t448-tag-abuse.sh`. It is not in that instrument. It is in `reviews/t448-review-t433/REVIEW.md:364`. | `grep -rn "all. = 2" .softhouse/reviews/t448-review-t433/` -> that one line |
| **F-T464-5** | **LOW** | **None of T455's four committed drive transcripts was taken at the branch tip** — they record `21a47a26` (commit 2) and `d41a018e` (commit 7) of 9. The three graded files happen to be byte-identical from commit 1 onward, so the evidence does cover the merged bytes, but a reader cannot tell that without running `git log -- <file>` themselves. | `out/20-IVA-DRIVE.txt`, recipe below |
| **F-T464-6** | **LOW** | The MATERIAL/PROSE discriminator is "the value contains any whitespace". An identifier-shaped value with one trailing space is reclassified PROSE, i.e. immaterial. The limit is not published beside the classifier (P-29). | `out/90-CLASSIFIER-SHAPES.txt` |

No money non-negotiable is touched. The diff is 2,623 added lines across 16 files, all under
`.softhouse/`; **zero** hits for `float`, `double precision`, `first_name`/`last_name`,
`Stripe`/`Plaid`, `ojdbc`/`oracle.jdbc`/`mysql`/`mariadb`/`:1521`. `conformance.sh`,
`.softhouse/bin/ready-tasks.py` and `.softhouse/hooks/` are **untouched** by this diff — the
scope bar T455 was given was respected, including the one file it went outside for, which it
disclosed by name (§6).

---

## 1. THE HEADLINE — T455 vs T448 ON CASE B. **T455 IS RIGHT.**

**T448 asserts** (`reviews/t448-review-t433/REVIEW.md:358-364`) that its one-predicate repair

```
both="$(grep -Ei "$IMPOSS" "$f" | grep -c "QUOTED-FALSE-CLAIM")"
all="$(grep -Eic "$IMPOSS" "$f")" ;  [ "$both" -ge 1 ] && [ "$both" = "$all" ]
```

closes abuse **B** because "case B fails it (`all` = 2, `both` = 1)".

**T455 asserts** the opposite: `all = both = 2`, so the predicate **passes** B.

**I re-derived it with two engines that share no primitive** — python's `re` module over the
mutated text, and real `grep` in a subprocess, on the same bytes. `instruments/40-t464-caseB-adjudication.py`,
`out/40-CASEB-ADJUDICATION-at-T433-tip.txt`, **EXIT 0**:

```
  run-all.sh CASE B (echo, tag in comment)       all=2   both=2  -> PASSES (T448's predicate does NOT catch it)
      python-re: all=2 both=2   grep: all=2 both=2   engines AGREE
        TAGGED | echo "  [QUOTED-FALSE-CLAIM]  commit. There is no committed baseline older than HEAD for those 632.\""
        TAGGED | echo "There is no committed baseline older than HEAD for those 632."  # QUOTED-FALSE-CLAIM
```

**Adjudication: T448's figure is wrong and T455's is right,** for exactly the reason T455 gives.
The smuggled line carries the tag in its **trailing shell comment**, on the *same source line*,
so `grep -c "QUOTED-FALSE-CLAIM"` counts it and `both` rises with `all`. A source-line grep
cannot distinguish "tagged because it is a quotation" from "tagged because someone appended a
comment"; only a predicate that reads what the line **prints** can. That is what T455 shipped as
PREDICATE 2, and it does catch B (§3).

T448 is right about **C**: `both = 0`, so the predicate catches it.

### And the case against T448's predicate is stronger than T455 said

T455 records that the quotation in `10-drive-conditions.sh` is line-wrapped, so a line-wise
matcher scores it **0/0 — indistinguishable from abuse C**. Confirmed, and the consequence is
worse than "indistinguishable". Run T448's predicate over all four in-scope files on an
**unmutated** tree at T433's tip:

```
  run-all.sh                  (UNMUTATED)  all=1 both=1  -> PASSES
  10-drive-conditions.sh      (UNMUTATED)  all=0 both=0  -> FAILS
  verify-capture-integrity.py (UNMUTATED)  all=0 both=0  -> FAILS
  12-relaunder-manifest.py    (UNMUTATED)  all=1 both=1  -> PASSES
```

**T448's supplied repair, shipped as written, would have been RED ON A CLEAN TREE for two of
the four files it guards** — because both of those files wrap their tagged quotation across
source lines (`10-drive-conditions.sh:224-227` splits at "…has no / baseline older than HEAD
anywhere…"; `verify-capture-integrity.py:123-125` splits at "which does not / exist and cannot
be manufactured here"). That is P-98's other sign: a control that refuses everything. T455's
de-wrapping of contiguous tagged blocks is not an embellishment; it is what makes the predicate
usable at all.

The dispatch says this is the second time this fire a worker has measured a reviewer's proposed
patch and found it wrong — T451 to T449, confirmed by an independent third. **That prior instance
is the dispatch's claim, not mine; I did not re-measure it.** What I did measure is this one, and
on this one the measuring worker is right. The rule T455 wrote for it — *a repair supplied by a
reviewer is a claim, not a result* — is the right lesson and I would record it.

**Reproduction**

```
git clone --shared <repo> /tmp/t433tip && cd /tmp/t433tip && git checkout --detach 3253358d
python3 <this dir>/instruments/40-t464-caseB-adjudication.py \
  .softhouse/reviews/A2-11/run-all.sh \
  .softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh \
  .softhouse/reviews/A2-11/verify-capture-integrity.py \
  .softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py \
  /tmp/t464-scratch.txt
```

---

## 2. `run-all.sh` — THE GREEN IS REAL, AND THE PIN DID NOT MOVE

`instruments/10-t464-runall-both-refs.sh`, `out/10-RUNALL-BOTH-REFS.txt`, **EXIT 0**. The pin is
measured **before** either run, because a green bought by moving a pin is not a green.

| | `run-all.sh` exit | deviations | section 9 | section 10 |
|---|---|---|---|---|
| **BEFORE** `cbc8733c`, unmodified `main` | **1** | 1 | **1 `*** MOVED ***`** | 0 |
| **AFTER** `57011593` | **0** | 0 | **0** | 0 |

The adjudicated pin `sec 9 0 python3 "$DIR/adjudicate-section1.py"`:

```
  cbc8733c : x1  at line 177
  57011593 : x1  at line 177
  sha256 of the pin line at BEFORE : 68743ce79174dcbc6b9180034c651315401374681175cbb1a3cf97b60e877500
  sha256 of the pin line at AFTER  : 68743ce79174dcbc6b9180034c651315401374681175cbb1a3cf97b60e877500
  OK   the pin line is BYTE-IDENTICAL across the two refs
```

**Present ×1 at both refs, on the same line number, byte-identical.** The `sec()` adjudication
function and the VERDICT block are untouched by the diff; the only changes to `run-all.sh` are
banner prose and the footer moved inside the teed block. The green was bought at the search.

**All seven BEFORE hits are prose**, exactly as T455 reports — re-read from the BEFORE
transcript rather than re-running T448's bisect (a second walk of the same path is not a second
derivation):

```
paymentChannelToFundSourceMappings v=1  .softhouse/vectors/capabilities-ledger.json
feeToIncomeAccountMappings         v=1  same file
penaltyToIncomeAccountMappings     v=1  same file
loanproduct                        v=4  capabilities-ledger.json + LDG-ACC-01/02/03
```
= 7, all inside JSON string values that are sentences.

### The fail-closed direction of the new classifier is real — but see F-T464-2

Controls (h) KEY→MATERIAL, (i) identifier-shaped VALUE→MATERIAL, (j) PROSE→immaterial-and-counted,
(k) unparseable→MATERIAL all drive the classifier in memory and all discriminate; and the new
positive control `_parsed_ok > 0` refuses a corpus in which nothing parsed, which is the
vacuous-pass direction. I re-drove the classifier on nine shapes and it behaves as documented:

```
identifier value (no ws)            -> material=[('VALUE-ID', '$.provenance.capture_ref')]
key                                 -> material=[('KEY', '$.expected.paymentChannel…')]
prose                               -> prose=[('PROSE', '$.evidence')]
unparseable (non-JSON)              -> material=[('UNPARSEABLE', 1)]
identifier value + TRAILING SPACE   -> prose=[('PROSE', '$.provenance.capture_ref')]     <- F-T464-6
```

All nine shapes are driven by `instruments/90-t464-classify-shapes.py` (`out/90-CLASSIFIER-SHAPES.txt`,
**EXIT 0**), which lifts `classify_occurrences` out of the shipped adjudicator rather than
re-implementing it.

The last row is the discriminator's blind spot (F-T464-6, LOW): materiality turns on
`any(ch.isspace() for ch in node)`, so one trailing space demotes an identifier to prose. It is a
stretch as an attack — a ref with a space in it is not a ref the harness would compare — but P-29
asks for the limit to be **published beside the classifier**, and it is not.

---

## 3. `(iv-a)` — CLOSED, AND THE CLEAN TREE STILL PASSES

I did **not** re-run T455's instrument. `instruments/20-t464-iva-drive.sh` is mine, fabricates
its own observation and launders its own manifest row. `out/20-IVA-DRIVE.txt`, **EXIT 0**:

```
  OK   case 1 BEFORE clean (calibration): grader exit 0
                 graded=632 of 632 post-fork; ungraded because born at the tip=0
  OK   case 2 BEFORE fabricated+laundered (FAIL-OPEN): grader exit 0
               UNGRADED-BORN-AT-TIP out/A2-999-T464-FABRICATED.json
                 graded=632 of 633 post-fork; ungraded because born at the tip=1
  OK   case 3 AFTER  fabricated+laundered (REFUSED): grader exit 1
       166:  FAIL  ARM F GRADED ITS WHOLE POPULATION — …
       212:FAILURES: 1
  OK   case 4 AFTER  clean tree (P-98 CONTROL): grader exit 0
                 graded=632 of 632 post-fork; ungraded because born at the tip=0
```

* **The fail-open reproduces at BEFORE at first hand**: a fabricated capture, born at the tip,
  with its manifest row laundered in the same commit, is left **UNGRADED** and the grader still
  **exits 0** — `graded=632 of 633`. That is a PASS reported over a row the arm never measured.
* **AFTER refuses**, `FAILURES: 1`, on the **named** assertion ("ARM F GRADED ITS WHOLE
  POPULATION"), not on some collateral check.
* **Case 4 is the half that matters (P-98).** The clean tree at AFTER is **identical** to the
  BEFORE control: exit 0, population 632, graded 632, at-tip 0. **The close costs nothing.** A
  close that reddens honest trees is a freeze, and this one is not.

### The adjudication table is falsifiable in three directions, not one

An exception list that could only ever say *yes* is the fail-open re-spelled.
`instruments/21-t464-adjudication-drive.sh`, `out/21-ADJUDICATION-DRIVE.txt`, **EXIT 0**:

| case | what | grader |
|---|---|---|
| 7a | the fabricated capture adjudicated by **name + digest** | **0**, and printed as adjudicated |
| 7b | its adjudicated **bytes** then changed | **1**, on "…adjudications are EXACTLY the ones adjudicated" |
| 7c | a **dead** entry naming nothing born at the tip | **1**, same assertion — a silent widening is caught |

7c is mine, not T455's, and it matters: a table keyed by name+digest that never noticed a stale
entry would grow into an amnesty. On a clean tree `ARM_F_BORN_AT_TIP_ADJUDICATED = {}`, so the
check is trivially satisfied there — which is why it has to be driven, and it is.

### The repair is inside the shipped grader, and something runs it (P-45)

Established by grep, not asserted (`out/30-SEC10-DRIVE.txt` prints the whole enumeration):

```
.softhouse/reviews/A2-11/run-all.sh:252:  sec 10 0 python3 "$DIR/verify-capture-integrity.py"
```

The grader is invoked by the runner that adjudicates it, and **exactly one** invocation is
adjudicated. That is the same call T433 got right for ARM F, and it is the right one here. The
enumeration also confirms the counterpart of F-4: **`conformance.sh` is not in the list.** The
chain is wired to a runner, and the runner is wired to a reviewer, not to the bar.

`C-T448-6` lands too, and is asserted rather than appended: the footer marker greps **0** in
`run-all.sh` at BEFORE and **1** at AFTER, its regenerated transcript carries it **×1** where the
BEFORE transcript carries **0**, and `verify-capture-integrity.py:1218-1223` fails section 10 if
the marker leaves `run-all.sh` (T455's drive case E).

The author's claim that section 10 "caught its own author three times" cannot be re-run, but it
is corroborated by three artefacts that only make sense if it happened: the section-10 fixture
sentence is **assembled from the pattern table** rather than typed (a literal would be an
untagged assertion in the guard's own source), the new `run-all.sh` banner lines are tagged, and
the two `want_min` changes exist because the wiring guard went red on the author's own additions.

---

## 4. F-T464-1 (MINOR) — ABUSE B RE-OPENS THROUGH `printf`

PREDICATE 2 is the predicate that closes B, and it closes B **for `echo` and `print(`**.
`emitted_payload()` recognises a line as an emitter only if the stripped line starts with
`echo ` or `print(`. Everything else "is not judged by the printed predicate at all" — the
docstring says so — and PREDICATE 1 does not see these lines either, because the tag **is** on
the source line.

`instruments/60-t464-sec10-evasion.py` lifts the real functions out of the shipped grader (no
re-implementation) and asks eight shapes. `out/60-SEC10-EVASION.txt`, **EXIT 0**:

```
  control: correctly tagged quotation        -> PASSES by -
  B  : echo, tag in trailing comment         -> CAUGHT by P2
  C  : quotation deleted, 3 bare tags        -> CAUGHT by P1
  B' : printf, tag in trailing comment       -> PASSES by -      <-- abuse B, re-achieved
  B'': `>&2 echo`, tag in trailing comment   -> PASSES by -      <-- abuse B, re-achieved
  B''': sys.stdout.write, tagged comment     -> PASSES by -      <-- abuse B, re-achieved
  B'''': heredoc body, untagged              -> CAUGHT by P1
  B''''': echo -e, tag in trailing comment   -> CAUGHT by P2
```

Driven **end to end**, not only in memory — `instruments/31-t464-sec10-printf-evasion.sh`,
`out/31-SEC10-PRINTF-EVASION.txt`:

```
  section-10 grader exit = 0   (0 means the smuggle EVADES both predicates)
  FAIL lines in the grader: 0
  run-all.sh exit = 0
  the REGENERATED transcript carries the sentence x2, of which x1 carry NO tag.
      UNTAGGED IN TRANSCRIPT: There is no committed baseline older than HEAD for those 632.
```

**This is the exact outcome T448 found and T455 shipped PREDICATE 2 to prevent**, reached
through a different emitter, with the whole runner green. And `printf` is not exotic: it is
already used **12×** in `10-drive-conditions.sh` and **5×** in `run-all.sh`, two of the four
files section 10 guards.

I rate it **MINOR**, not MAJOR, for two reasons: PREDICATE 1's blanket source-level negative
still catches every *untagged* re-assertion, so this requires a deliberate tag-in-a-comment; and
the artefact at risk is a correction record, not a money path. But the sentence *"Closes (B)"*
in the handoff and *"nothing this tooling PRINTS states one without the tag inside what it
prints"* in the banner are both broader than what was measured.

**Condition.** Either widen the emitter recogniser (`printf`, `>&2 echo`, `sys.stdout.write`,
and a shell-agnostic form for redirections), or publish the scope as a stated limit beside the
predicate in the form P-29 asks for: *the edit that should trip it but won't*. The second is
acceptable; the current text is not, because it states the general claim.

**Reproduction**

```
T464_SRC=<repo> T464_SCRATCH=/tmp/t464/sc T464_AFTER=57011593 \
  bash <this dir>/instruments/31-t464-sec10-printf-evasion.sh
```

---

## 5. F-T464-2 (MINOR) — THE FAIL-CLOSED BRANCH IS REACHABLE ONLY BY A CRASH

`classify_occurrences()` returns `[("UNPARSEABLE", <int count>)]` on the unparseable branch and
`[(kind, <str jsonpath>)]` on the parsed branch. The caller formats both with `where[:70]`.

The vector store already tracks exactly one non-JSON file, so the branch is **live**, not
hypothetical. `instruments/70-t464-unparseable-fail-closed.sh`, `out/70-UNPARSEABLE-FAIL-CLOSED.txt`,
**EXIT 1 (the finding)**:

```
  the tracked non-JSON file already in the vector store : .softhouse/vectors/README.md
  --- 1. CALIBRATION: adjudicate-section1.py exit = 0        (P-72: green before anything is planted)
  --- 2. PLANT THE TOKEN. adjudicate-section1.py exit = 1
        Traceback (most recent call last):
          File ".../adjudicate-section1.py", line 303, in <module>
            print("          %-8s %s  at %s" % (kind, rel, where[:70]))
        TypeError: 'int' object is not subscriptable

      reached the NAMED 'NO vector … USES any of these tokens' FAIL : x0
      died on a python traceback instead                            : x1
      printed its own FAILURES tally                                : x0
      checks that reported at all, before -> after                  : 25 -> 10
```

**The direction is still closed** — rc=1, so `run-all.sh` reads section 9 as `*** MOVED ***` and
the aggregate goes red. It is not a fail-open, and I want that stated plainly because the
severity turns on it. What is lost is everything else: the named assertion never runs, the
`FAILURES:` tally never prints, and **15 of the file's 25 checks are skipped**, including the
T374/T362 provenance arms and **section 5's controls (a)–(k)** — the file's own P-22 self-drives,
among them control (k), the one written to prove this very branch works.

So control (k) proves the **function** returns MATERIAL; the **arm** never gets to say so. That
is the gap P-22 names between a control that passes and a guard that works, and it is worth one
line of repair.

**Condition.** Make the unparseable branch return a string (e.g. `("UNPARSEABLE", "x%d raw" % n)`)
so the arm reaches its named assertion, and add the planted-token drive above as a fifth control
(l) alongside (h)–(k), so the **integration** is driven and not only the classifier.

---

## 6. THE `want_min` EDIT — **RIGHT CALL.** Measured three ways.

`instruments/80-t464-wantmin-judgement.sh`, `out/80-WANTMIN-JUDGEMENT.txt`, **EXIT 0**:

| | question | measured |
|---|---|---|
| A | as shipped, clean tree at T455's tip | guard **exit 0**, 0 BAD assertions |
| B | the two pins **reverted to exact `want`**, same clean tree | guard **exit 1** — `expected x1, got x2` and `expected x1, got x3` |
| C | as shipped, but the pinned tokens **removed from the grader** | guard **exit 1** — `expected at least x1, got x0` (both) |

**B says the edit was necessary, not convenient.** With the exact pins in place the tracked
guard is **RED on a clean tree** — which is the defect T455 was sent to fix in F-6, one file
over. **C says it is not a weakening.** `want_min <token> 1` still fires when the token
disappears, and *presence* is the entire claim these two assertions make: their labels are "ARM
F reports born-at-tip as UNGRADED" and "says what the baseline IS", neither of which is a claim
about a count.

The file's own comment, nine lines above the first of them, prescribes exactly this
(`30-t433-armf-wiring-guard.sh:48-50`): *"A minimum, never an exact count: P-29, a count is a
weak tripwire and pinning one here would go red on a comment being reworded, which is how a
guard gets deleted rather than fixed."*

**Should it have been filed instead of edited?** No, and the counterfactual is the argument:
filing it merges a tracked guard that is red on an honest tree, and the recorded history of this
program is that such a guard gets **pinned away or deleted**, not fixed. The edit is two lines,
mechanical, in the direction the file itself prescribes, disclosed by name in the handoff **and**
in an in-file comment, and driven both ways. That is the correct handling of a scope boundary,
not a breach of it. The guard's owner should confirm at merge; I would not hold the branch for it.

---

## 7. CARDINALS — RE-COUNTED UNDER A THIRD PRIMITIVE

`instruments/50-t464-cardinals.py`, `out/50-CARDINALS-at-T433-tip.txt`, **EXIT 0**. The corpus is
read out of the **commit** with `git ls-tree` + `git show`, so it shares neither `git grep`
(T455's LEG 1) nor `git ls-files` over the worktree (LEG 2), and a dirty checkout cannot flatter
it.

```
  run_case invocations in the SOURCE : 11        distinct case names in the OUTPUT : 11
  data rows in MATRIX.tsv            : 22        = cases x 2 refs
  driven by T433 : ['control', 'f1-13b-postfork-laundered-RESIDUAL']   ARGUED = 11 - 2 = 9
```

**11 cases / 22 rows / 9 argued** — T455's figures, T433's "13-case … other eleven" is wrong.

```
  invoking files : 14   invocation lines : 18   total mentions : 45
  of which T433's own: 3 files / 4 lines   ==> PRE-EXISTING : 11 files / 14 lines
```

**T448's 11 / 14 is confirmed a second time**, with the fourteen-file list printed beside the
count (a count with no list is the "17" again). The stated limit holds for my leg as well as
T455's two: `.sh` and `.py` only, and an invoker in another language is invisible to all three.

---

## 8. RESIDUALS — EACH CONFIRMED

* **The DETECTION half of `(iv-a)` cannot close internally, and the reduction of F-2 is
  HONEST.** The docstring at `verify-capture-integrity.py:155-186` states precisely which half
  closed and which did not, and names the external anchor at `(iv-a-anchor)`: re-observation
  against the pinned reference oracle (Fineract), digest-recorded, the procedure T357 ran for the
  four `obs/` files. My case 2/3 shows the distinction is real — the fabricated capture is still
  **not detected** at AFTER; what changed is that it can no longer be reported as a PASS. That is
  exactly the scope T455 claims and no more.
* **`conformance.sh` does not invoke this chain (F-4, still open).**
  `grep -c 'verify-capture-integrity\|A2-11/run-all' .softhouse/conformance.sh` → **0**.
  Unchanged by T455 (T454 held the file), and disclosed. The consequence, stated plainly: the
  whole ARM-F / section-10 chain is run by reviewers and instruments, **never by the bar**.
* **`conformance.sh`'s half of the section-4 search is still a raw substring match**, and the
  limit **is** stated at the site (`adjudicate-section1.py`, the comment above `chits =`):
  fail-closed, same false-positive class as F-6, demands a human.
* **T433's own record still carries the wrong cardinals**, outside T455's grant, corrected in
  `T433-CORRECTION.md` with the wrong numbers **quoted rather than deleted**. Confirmed:
  `handoff/T433-t423-c1.md:294,297` ("full 13-case matrix", "the other eleven") and
  `capture/t433-t423-c1/instruments/50-t433-runall-f1-13b-row.sh:11,17` ("the full 13-case
  matrix … 26 whole", "The other eleven rows").
* **T448's wrong `all/both` for case B is recorded, not edited.** Correct handling — a review is
  an append-only record of a reviewer's reasoning. But see **F-T464-4**: the figure is at
  `reviews/t448-review-t433/REVIEW.md:364`, and `grep -rn 'all=2\|both=1' reviews/t448-review-t433/`
  returns **that one line only**. It is **not** in `30-t448-tag-abuse.sh`, which computes no such
  pair. T455's handoff §10 names the wrong file. Fix the citation; the substance is unaffected.

### F-T464-3 (LOW) — a stale sentence in the file whose subject is stale sentences

`verify-capture-integrity.py:194-197`:

> `(iv-b2) …BUT ONLY WHILE THE SIMILARITY HOLDS. Rename the file AND replace its bytes wholly
> and git records a genuine ADD at the tip, which lands in (iv-a): reported UNGRADED, exit 0.`

At this ref it lands in `(iv-a)` and exits **1**. T455 measured that itself — its own
`out/20-IVA-CLOSE-DRIVE.txt` case 5: *"(iv-b2) rename+whole rewrite, at AFTER — grader exit = 1"*.
Twenty lines above, the same docstring correctly says the fail-open is closed. One paragraph was
updated and its neighbour was not. Repair: strike "exit 0" from `(iv-b2)`.

### F-T464-5 (LOW) — no committed drive transcript is taken at the branch tip

Every one of T455's four drive transcripts records a ref that is **not** the tip `57011593`:

```
out/20-IVA-CLOSE-DRIVE.txt      AFTER = 21a47a26   (commit 2 of 9)
out/10-RUNALL-AND-FOOTER.txt    AFTER = d41a018e   (commit 7 of 9)
out/30-TAG-BINDING-DRIVE.txt    ref   = d41a018e   (commit 7 of 9)
out/40-CARDINALS.txt            commit= d41a018e   (commit 7 of 9)
```

On its face that means the committed evidence does not cover the bytes being merged. It does,
and here is the measurement that rescues it — which I had to make, and which the handoff should
have made:

```
git log --oneline cbc8733c..57011593 -- .softhouse/reviews/A2-11/adjudicate-section1.py
git log --oneline cbc8733c..57011593 -- .softhouse/reviews/A2-11/verify-capture-integrity.py
git log --oneline cbc8733c..57011593 -- .softhouse/reviews/A2-11/run-all.sh
  -> all three: 140a7ae7 only  (commit 1 of 9)
```

All three graded files are **byte-identical from commit 1 through the tip**, so a drive at
commit 2 or 7 exercises exactly the merged bytes. I additionally re-drove `(iv-a)` (4 cases),
the adjudication table (3 cases), section 10 (A/B/C) and `run-all.sh` (both refs) **at the tip**
and every one holds. Repair: regenerate at the tip, or state the ref and this invariance in the
handoff. Do not leave the reader to derive it.

---

## 9. THE BAR

`TMPDIR=/tmp/t464-bar bash .softhouse/conformance.sh` — scratch **outside** the repository,
`bash` and never `sh`/`zsh`, on my own **committed** tree at `softhouse/T464-review-t455`.
`git status --porcelain` was **0 lines before and 0 lines after**.

**PROBE PRESENCE WAS TESTED BEFORE ITS VALUE** (P-84: absence is not `down`; `EXIT 2` with no
probe line is the guard working, and would be read as a money non-negotiable violation):

```
grep -c 'probe = '  ->  1
probe line, verbatim:
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```

```
BAR EXIT 0

VERDICT: PASS (exit 0) - 46 parity vectors match the pinned reference oracle, 7884 cells compared.
all 16 wrong ledger implementations DIED through this harness, not by hand.

fail-open frontier  : 1652 tracked .sh/.py inspected; frontier 11, pinned at 11, frontier == pinned
dead-path census    : T316-DEADPATH-CENSUS: corpus=1652 deadFiles=75 deadOccurrences=108
                      resolving=1561 indeterminate=122 prose=418
dead-path frontier  : GREEN, and the T323 reconciliation list is empty
host state in lint  : 18 sites, pinned at 18, census == pinned
```

**And on my own branch tip, separately** — T457's close of the bar-then-commit regress, so a
review that is green in the bar cannot be red the moment it is committed:

```
bash .softhouse/guards/check-dead-path-frontier.sh
T316-DEADPATH-CENSUS: corpus=1652 deadFiles=75 deadOccurrences=108 resolving=1561 indeterminate=122 prose=418
T316-DEADPATH-FRONTIER: GREEN rows=108 pinned=108 added=0 removed=0        EXIT 0
```

The census corpus grew **1641 -> 1652** for my eleven instruments and `deadOccurrences` did not
move: none of them spells a `.softhouse/` path literal (`grep -n '\.softhouse/' instruments/*`
is empty), and none of them assigns a literal `/tmp` path to a name (`grep -n '/tmp' instruments/*`
is empty — instrument `40-` REFUSES with exit 3 rather than defaulting its scratch path).

---

## 10. REPRODUCTION — EVERY INSTRUMENT IN THIS REVIEW

All of them take a source repo and a scratch directory **outside** it. `<D>` is this directory.
No instrument spells a repo-relative path as a literal (`grep -n '\.softhouse/' instruments/*` is
empty), so none of them can add a row to the dead-path frontier on a tree that does not carry
the branch under review.

```
REPO=<a clone of gerege-nbfi carrying softhouse/T455-t448-conditions>
B=cbc8733c ; A=570115935837a096deab8e670c69ced0279190f2

# run-all.sh at both refs, and the adjudicated pin at both refs
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/a T464_BEFORE=$B T464_AFTER=$A \
  bash <D>/instruments/10-t464-runall-both-refs.sh

# (iv-a): fail-open reproduced, closed, and the clean-tree control
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/b T464_BEFORE=$B T464_AFTER=$A \
  bash <D>/instruments/20-t464-iva-drive.sh

# the born-at-tip adjudication table, driven three ways
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/c T464_AFTER=$A \
  bash <D>/instruments/21-t464-adjudication-drive.sh

# section 10 A/B/C in situ, the printf evasion, and the P-45 invoker enumeration
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/d T464_AFTER=$A \
  bash <D>/instruments/30-t464-sec10-drive.sh
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/e T464_AFTER=$A \
  bash <D>/instruments/31-t464-sec10-printf-evasion.sh

# the case-B adjudication, two engines, at T433's tip
git -C $REPO worktree add /tmp/t433tip --detach 3253358d ; cd /tmp/t433tip
python3 <D>/instruments/40-t464-caseB-adjudication.py \
  .softhouse/reviews/A2-11/run-all.sh \
  .softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh \
  .softhouse/reviews/A2-11/verify-capture-integrity.py \
  .softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py \
  /tmp/t464-scratch.txt

# the cardinals, third primitive, at T433's tip
python3 <D>/instruments/50-t464-cardinals.py $REPO 3253358d \
  .softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh \
  .softhouse/capture/t393-t382-conditions/out/drive/MATRIX.tsv \
  .softhouse/capture/t433-t423-c1/

# section 10's emitter recogniser, eight shapes, in memory
python3 <D>/instruments/60-t464-sec10-evasion.py \
  $REPO/.softhouse/reviews/A2-11/verify-capture-integrity.py

# the unparseable / fail-closed branch, end to end
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/f T464_REF=$A \
  bash <D>/instruments/70-t464-unparseable-fail-closed.sh        # EXIT 1 is the finding

# the want -> want_min edit, judged three ways
T464_SRC=$REPO T464_SCRATCH=/tmp/t464/g T464_REF=$A \
  bash <D>/instruments/80-t464-wantmin-judgement.sh

# the F-6 structural classifier, nine shapes
python3 <D>/instruments/90-t464-classify-shapes.py \
  $REPO/.softhouse/reviews/A2-11/adjudicate-section1.py
```

`git clone --local --no-hardlinks` of this repository takes about 5 s and 400 MB; each
`run-all.sh` run takes about 75 s, so `10-` takes roughly 3 minutes and `30-`/`31-` a little
under 4 between them.

---

## 11. WHAT I WOULD TELL THE NEXT READER

T455's own closing paragraph is the right lesson and I am confirming it from outside: **a repair
supplied by a reviewer is a claim, not a result.** T448 handed down a predicate with a stated
measurement attached, and the measurement was wrong in one direction (it does not close B) and
catastrophic in the other (it would have been red on two honest files). The only reason anybody
knows that is that T455 **ran it** instead of pasting it.

The two conditions I am adding are the same shape one layer further in. T455 shipped PREDICATE 2
with the sentence *"nothing this tooling PRINTS states one without the tag inside what it
prints"*, and what it actually grades is `echo` and `print(`. And it shipped *"unparseable fails
CLOSED, never skipped"* with a control that drives the classifier and an arm that crashes before
it can say so. Neither is a fail-open. Both are a guard whose sentence is wider than its
measurement — which is precisely the defect this whole chain, from T423 through T433 to T448 to
T455, exists to prosecute.
