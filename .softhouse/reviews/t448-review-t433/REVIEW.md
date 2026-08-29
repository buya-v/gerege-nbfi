# T448 — INDEPENDENT REVIEW of T433 (C-T423-1)

Reviewer: T448, `opus`. Branch `softhouse/T448-review-t433`.
Work under review: `softhouse/T433-t423-c1`, 9 commits, `b102875c..3253358d`
(`git merge-base main softhouse/T433-t423-c1` = `b102875c7e0d1b7f1ba4339180cedc5e207dfb11`;
three-dot diff = 70 files, +10757 / −30).

---

## VERDICT

> **APPROVED WITH CONDITIONS.**

T433's substantive work reproduces. I re-derived every headline number with an instrument that
does not share T433's primitive, and every one came back identical. The arm is where T433 says
it is, it is inside the shipped grader rather than beside it, its vacuity control fails when it
should, and its money claim survives an independent recomputation in integer minor units. The
one prediction T433 got wrong it recorded as wrong, which is the behaviour this program is
trying to buy.

The conditions are one MAJOR and four smaller items. **The MAJOR is not a broken measurement —
it is a declaration.** T433 says its open fail-open `(iv-a)` is "not closable by internal
consistency". I drove that claim and it is false as stated: *detecting* a fabrication does
need the oracle, but *refusing to exit 0 over a population the arm did not measure* is
internal, costs nothing on a clean tree, and is the rule the grader already applies to its own
sibling case nine lines earlier in the same file.

---

## 1. WHAT I RE-DERIVED, AND WITH WHAT

Everything below is measured on this worktree
(`/Users/buv/gerege-nbfi/.claude/worktrees/agent-a5f3d0743d5dea2cd`) and in scratch clones
under `/tmp/t448`, outside the repository.

### 1.1 The 632 — CONFIRMED, by a primitive T433 did not use

T433's two derivations (METHOD A per-path `git log --diff-filter=A`, METHOD B one bulk walk of
the same option) are **the same primitive read two ways**. `--diff-filter=A` is rename-aware,
which is exactly why `(iv-b)` came out `R` instead of `A` — so agreement between A and B is
weaker evidence than it looks, and re-running T433's script would have measured the script.

**METHOD C — tree containment.** Walk `git rev-list --reverse --topo-order <TIP>`; the first
commit in a topological order whose *tree* contains the path is the birth commit, and is an
ancestor of TIP by construction. `--diff-filter` is never used; rename detection cannot reach
it, because containment is a property of a tree and not of a diff.
Instrument: `instruments/00-t448-birth-sweep.py`. Transcript: `out/00-BIRTH-SWEEP.txt`.
(Calibrated first on two known positives — a non-empty fork tree, and a fork-era path that
must come out born at an ancestor of the fork — and refuses with exit 2 if either fails.)

| | T433 claims | **T448 measures (METHOD C)** |
|---|---|---|
| tracked observations at the tip | 1035 | **1035** |
| at the literal fork sha `12a7f8d9` | 403 | **403** |
| post-fork population | 632 | **632** |
| born strictly older than the tip **and** an ancestor of it | 632 | **632** |
| born **at the tip** | 0 | **0** |
| born at a non-ancestor | 0 | **0** |
| equal to the birth blob by **git OID** | 631 | **631** |
| equal by **sha256** of the bytes | 631 | **631** |
| **differ** | 1 | **1** |
| non-blob (symlink/gitlink) entries | 0 | **0** |
| distinct birth commits | 7 | **7** |

The one differing observation is the same one, with the same commit and the same two digests:
`out/A2-370-db-ledger-state.txt`, born `aae501b5`, birth sha256 `1ea4927a…`, disk `1c23375b…`.

**And METHOD A agrees with METHOD C on 632 of 632** (section 5 of the transcript). T433's
number is right; so, as it happens, is T433's method — but that is now measured against an
independent one rather than against its own twin.

### 1.2 The money — RE-DERIVED, not read

`out/A2-370-db-ledger-state.txt` is the only ledger assertion in this task, and T433 reports
it "still balancing in integer minor units". I recomputed it from the raw
`acc_gl_journal_entry` rows in **both** versions of the file.
Instrument: `instruments/10-t448-ledger-rederive.py`. Transcript: `out/10-LEDGER-REDERIVE.txt`.

Method: amounts converted to integer minor units **by string surgery** — the integer and
fractional parts are sliced as text and combined with integer arithmetic. `float()` and
`Decimal` are never called, because the non-negotiable forbids a binary float even in an
intermediate. The `JournalEntryType` ordinal is calibrated from the data (L1's Loan Portfolio
leg must be the DEBIT) rather than assumed, and a synthetic 1-minor-unit imbalance is pushed
through the same summing code and must be caught before any zero is reported (P-72).

| | birth blob `aae501b5` | tracked at HEAD |
|---|---|---|
| raw journal-entry legs | 48 | 54 |
| transactions | 21 | 23 |
| **imbalanced transactions** | **0** | **0** |
| legs with a residue **below** the MNT minor unit | **0** | **0** |
| summary rows contradicted by the recomputation | **0** | **0** |
| whole-ledger debit / credit, minor units | 1 093 166 950 / 1 093 166 950 | 1 197 166 950 / 1 197 166 950 |

The two new transactions, re-derived by hand as well as by instrument:

* **L26**, 2 legs — CREDIT Loan Portfolio 40 000.00, DEBIT Goodwill Credit 40 000.00 →
  `4 000 000` minor each side.
* **L27**, 4 legs — DEBIT Fund Source Alternate 1 000 000.00 = `100 000 000` minor; CREDIT
  889 549.42 + 20 298.82 + 90 151.76 = `88 954 942 + 2 029 882 + 9 015 176` =
  **`100 000 000`** minor. Exact, with no residue.

The diff between the two versions is **26 lines and purely additive**: two transactions added,
none removed, none altered (`ADDED ['L26','L27'] REMOVED [] ALTERED []`). That is the
append-only property the non-negotiable requires, and it is the thing that makes "legitimate
re-capture" the right adjudication rather than a convenient one. **T433's money claim is
CONFIRMED.**

### 1.3 ARM F's wiring — CONFIRMED, with one correction to the prose

* `=== 8. ARM F` is at `.softhouse/reviews/A2-11/verify-capture-integrity.py:712`, **inside**
  the shipped grader. Confirmed by reading the section, not by grepping for its name.
* `run-all.sh:229` is `sec 10 0 python3 "$DIR/verify-capture-integrity.py"`, and `sec`'s
  contract (`run-all.sh:17-22`) records the exit code against an adjudicated value, so any
  move fails `RUN-ALL VERDICT`. Confirmed.
* `10-drive-conditions.sh:241` now reads
  `run_case f1-13b-postfork-laundered-CLOSED-BY-ARM-F mut_commit_mutate_postfork_laundered 0 1`.
  **The `1` is ATTRIBUTED, not assumed.** T433's branch changes four files, so "it is 1 now" is
  not by itself an attribution. `instruments/60-t448-f113b-attribution.sh` builds T393's f1-13b
  mutation (post-fork observation mutated **and** its `MANIFEST.sha256` row rewritten in the
  same commit, via T393's own `12-relaunder-manifest.py`) and grades section 10 on it at **two
  refs**, transcript `out/61-F113B-ATTRIBUTION.txt`:

  | ref | section 10 | ARM F named it |
  |---|---|---|
  | `b102875c` — unmodified `main`, no ARM F | **0** | **0** |
  | `3253358d` — T433 tip, ARM F present | **1** | **1** |

  Both halves are load-bearing: a red BEFORE would mean T393's residual was never real, and a
  green AFTER would mean the arm does not reach it. So **removing ARM F does fail T393's own
  drive.** Confirmed.
* **Correction (C-T448-5 below):** the handoff's invoker table is not the complete set, and the
  figure "17 existing invocation sites" is not 17 pre-existing sites.

### 1.4 The vacuity control — RE-DRIVEN RED, independently

`instruments/20-t448-armf-drives.sh`, transcript `out/20-ARMF-DRIVES.txt`,
per-case `out/drives/`. My own orphan-commit construction, my own harness, calibrated on an
unmutated clone first (which grades exit 0, 632 graded).

```
vacuity-redrive   rc=1 FAIL  named=0 tip=10 moved=0 graded=0   expected 1  as expected
  OK  ARM F graded ZERO rows            (GRADED against a birth blob older than HEAD : 0  x1)
  OK  section 9's f_graded>0 control is the thing that FAILED   (FAIL  ARM F actually GRADED x1)
```

An arm that grades zero rows and reports success is the defect this whole task is about, and
the control that catches it has now been seen to fail by two independent hands.

### 1.5 The wiring guard — seen to FAIL by me, not only by its author

`out/60-WIRING-GUARD-RED-DRIVE.txt`. I removed the `=== 8. ARM F` marker from the grader in a
scratch clone and ran `30-t433-armf-wiring-guard.sh` against it: **EXIT 1**, on
`BAD  verify-capture-integrity.py carries ARM F as section 8 — expected x1, got x0`.
P-22 satisfied at first hand. (Two further red-drive attempts of my own are C-T448-2 below —
they did **not** go red, and that is the finding.)

### 1.6 F-6 — CONFIRMED, and attributed

Independently reproduced with three commands and no mutation of any kind, at the unmodified
`main` tip `b102875c`, with no ARM F in the tree:
`9  0  1  *** MOVED ***`, `sections run: 10  deviations: 1`,
`RUN-ALL VERDICT: FAIL — 1 section(s) moved`, process `EXIT=1`; **section 10 is `0`,
as adjudicated.** Transcript `out/70-F6-RUNALL-RED-ON-MAIN.txt`.

I then bisected the cause, which T433 did not: the token entered the vector store at
**`25a8b7de` (T391), 2026-08-29 01:31:12 +0800**; `adjudicate-section1.py` exits **0** at that
commit's parent and **1** at `main`. So the red is **hours old, not "for some time"** — and it
is a **false positive of section 9's own search**: the three key names appear in
`.softhouse/vectors/capabilities-ledger.json` only inside a free-text `evidence` field which
says in terms that the capability is still UNGRADED. Nothing about the graded corpus changed;
the search cannot tell a graded cell from a sentence about one.

T433's decision **not** to regenerate `TRANSCRIPT-A2-11.txt` over this is the right call and I
endorse it. Its stated *reason* for not fixing section 9 is wrong — see C-T448-3.

### 1.7 F-5's nine argued rows — MEASURED, and the argument HOLDS

T433 abandoned the full re-drive as "26 whole `run-all.sh` runs … hours of wall clock" and
argued the remaining rows. **The re-run is far cheaper than that**, because the column the
matrix grades is one command's exit code:

```
sec10="$(awk '/^  10 /{print $3}' ...)"      # run-all.sh's VERDICT table
sec 10 0 python3 "$DIR/verify-capture-integrity.py"
```

Grading that command directly on the same mutated clone yields the same number in ~1 minute
instead of ~7. Only the AFTER column can move (ARM F does not exist at BEFORE), so nine runs,
not twenty-six. `instruments/50-t448-f5-argued-rows.sh`, transcript `out/50-F5-ARGUED-ROWS.txt`:

| row | T393's committed `MATRIX.tsv` at AFTER | **T448 measures with ARM F present** |
|---|---|---|
| `control` (calibration) | 0 | **0** |
| `f1-13-commit-mutate-postfork` | 1 | **1** (ARM F also names it) |
| `f1-14-commit-delete-postfork` | 1 | **1** |
| `f1-15-commit-add-fabricated` | 1 | **1** |
| `f1-16-untracked-fabricated` | 1 | **1** |
| `f1-09-symlink-identical-bytes` | 1 | **1** |
| `f4a-control-commit-mutate-forkobs` | 1 | **1** |
| `f4b-move-fork-constant` | 2 | **2** |
| `f3-commit-mutate-nonobs` | 1 | **1** |
| `f3b-commit-mutate-nonobs-laundered` | 1 | **1** |

**Nine for nine. T433's argument was correct.** F-5 should now be closed as measured rather
than carried as a debt — see C-T448-4 for the two cardinals it got wrong on the way.

### 1.8 `(iv-c)` — DRIVEN four ways, and it is not a hole

T433 disclosed `(iv-c)` (delete and re-add) as open and **not driven**, and filed it as F-3.
I drove it, in four shapes, in `instruments/20-t448-armf-drives.sh`:

| construction | section 10 | ARM F |
|---|---|---|
| `ivc1` delete, re-add **byte-identical** | **0** | grades 632, names nothing |
| `ivc2` delete, re-add **mutated** + manifest laundered in the same commit | **1** | **NAMES the file** |
| `ivc3` delete, re-add identical, **then** mutate + launder in a third commit | **1** | **NAMES the file** |
| `ivc4` delete, re-add with **wholly new bytes** (no similarity) + laundered | **1** | **NAMES the file** |

The earliest ADD wins in every construction I could build, including the one where git's
history simplification had the best chance to hide it. `ivc1` exits 0 because **nothing
happened**: the bytes still equal the oracle capture, which is precisely what the arm asserts.
**F-3 is not an open fail-open** and should be closed, with these four rows as the evidence.

### 1.9 The surviving echoes — CONFIRMED out of grant, and the list is COMPLETE

T433's `files_hint` is `.softhouse/capture/t393-t382-conditions/` and
`.softhouse/reviews/A2-11/` (`.softhouse/tasks.json`, T433 entry). I re-ran the echo sweep on
T433's tree with its own broader pattern and listed every file outside those two directories
and outside T433's own capture dir. The result is exactly T433's disclosed list —
`handoff/T393-t382-conditions.md`, `handoff/…/T374.md`, `reviews/t382-review-t374/REVIEW.md`,
`reviews/t423-review-t393/**`, `tasks.json` — plus T433's own handoff, plus **one false
positive** (`reviews/t367-review-t363/drive-t305-t327-pins.sh:19`, an unrelated
`echo "    (no committed baseline)"`). **No undisclosed in-grant echo survives**, and every
named survivor is genuinely outside the grant rather than merely inconvenient. F-1 stands as
filed.

---

## 2. FINDINGS

### C-T448-1 — MAJOR — `(iv-a)` is NOT "not closable by internal consistency"; the fail-open closes at zero cost

**Evidence:** `out/40-IVA-CLOSABLE.txt`, `out/iva/`, `instruments/40-t448-iva-closable.sh`.

T433 writes: *"Not closable by internal consistency — a fabricated observation is a claim about
the oracle, and only the oracle can refute it."* That sentence runs two different problems
together:

1. **DETECTING that a capture is fabricated.** Genuinely external. T433 is right.
2. **REFUSING TO EXIT 0 over a population the arm did not measure.** Entirely internal — and
   `verify-capture-integrity.py` **already states the rule for it**, nine lines above the
   born-at-tip branch (`:754-760` vs `:769`), for the sibling case of a path with no recorded ADD commit:

```python
f_noborn = [p for p in f_post if p not in f_birth]
if f_noborn:
    refuse(...,
           "ARM F's baseline is not derivable for them, so ARM F did not grade them.",
           "An arm that could not measure part of its own population has not passed on it.",
           "REFUSED, never a pass.")
```

Nine lines later (`:769`), the same category gets the opposite treatment:

```python
    if b == head_sha:
        f_at_tip.append(name)      # printed, and nothing asserts it is empty
        continue
```

`f_at_tip` is printed and **no `check()` in section 9 asserts it is zero**. Section 9 asserts
`f_graded > 0`, which the fabrication satisfies (632 other rows graded fine).

**DRIVEN, five cases.** The patch under test is one `check(...)` call asserting `not f_at_tip`:

| # | case | grader | result |
|---|---|---|---|
| 1 | fabricated observation born at the tip **with a matching manifest row** | UNPATCHED | **rc=0** — T433's disclosed fail-open, reproduced (calibration) |
| 2 | the same tree | **PATCHED** | **rc=1**, on the named assertion, x1 |
| 3 | **clean tree** | **PATCHED** | **rc=0**; ARM F graded **632**, born at tip **0** |
| 4 | `(iv-b2)` rename + whole rewrite (the other route into `(iv-a)`) | UNPATCHED | **rc=0** |
| 5 | the same | **PATCHED** | **rc=1** |

Case 3 is the load-bearing one: **the close costs nothing.** On any tree where the captures
were committed before HEAD — which is every tree the grader is ever run on except the commit
that adds a capture — `f_at_tip` is already 0, as T433's own sweep and mine both measure. The
check fires only in the commit that actually adds a capture, which is the exact moment a human
is present to adjudicate it, in the same shape as the existing `ADJUDICATED_DIFFERENT` (ARM E) and `ARM_F_ADJUDICATED` tables.

**Why MAJOR and not MINOR.** A disclosed fail-open is a liability the next reader inherits with
a note attached; a fail-open disclosed *as unclosable* is one the next reader will not try to
close, because a previous task has already told them not to bother. That is the same failure
mode as C-T423-1 itself — an impossibility asserted rather than measured, foreclosing a cheap
correct fix — reproduced one layer in, in the artefact written to correct it. (P-12,
`patterns.md:315`: a right conclusion on a wrong reason recurs in the artefact written to
record it.)

**REPRODUCTION**

```
T448_SRC=<clone of this repo> T448_SCRATCH=/tmp/t448/scratch \
T448_OUT=/tmp/t448/iva T448_REF=<T433 tip 3253358d> \
bash .softhouse/reviews/t448-review-t433/instruments/40-t448-iva-closable.sh
```

**CONDITION.** Either land the `not f_at_tip` check in section 9 with an adjudication list for
legitimately new captures, or replace the sentence "not closable by internal consistency" with
what is actually true — *"the FABRICATION cannot be detected internally; the FAIL-OPEN can be
closed internally and was left open because <reason>"* — and say what the reason is. The
external anchor that closes half 1 is already in this program's vocabulary and should be named
in F-2: **re-observation against the pinned reference oracle (Fineract), digest-recorded**,
exactly as T357 did for the four `obs/` files on fire `20260828-140005` (sha256 match, 4 of 4).

---

### C-T448-2 — MINOR — the `[QUOTED-FALSE-CLAIM]` tag guard grades the TAG, not the tag's binding to the text, and both halves fall to a one-line edit

**Evidence:** `out/30-TAG-ABUSE.txt`, `out/tagabuse/`, `instruments/30-t448-tag-abuse.sh`.

The technique — keep the false sentence verbatim, tag it, and assert *both* that no untagged
line asserts it *and* that the quote survives — is **good, and I want it kept.** It is
strictly better than deleting the sentence. The **guard implementing it** is weaker than the
handoff claims. Its two predicates are:

```bash
got="$(grep -Ei "$IMPOSS" "$f" | grep -vc "QUOTED-FALSE-CLAIM")"     # negative half
q="$(grep -c "QUOTED-FALSE-CLAIM" "$f")" ; [ "$q" -ge 3 ]            # positive half
```

Both are token-level and line-level. Neither asserts that a tag and the quoted text are on the
same line **for the same reason**, and neither reads what the file **prints**.

**Case B — smuggle the claim back as a live, printed assertion.** Insert into `run-all.sh`,
inside the `{ … } | tee` block:

```bash
  echo "There is no committed baseline older than HEAD for those 632."  # QUOTED-FALSE-CLAIM
```

The guard reads the *source* line, sees the token, excludes it. The reader sees *stdout*, where
the comment does not appear. **Measured: wiring guard exit 0**, and `run-all.sh`'s own
regenerated transcript then carries the sentence twice, **one of them with no tag at all.**

**Case C — delete the quotation, keep the tag.** Remove every tagged quotation line and insert
three bare comments reading `# QUOTED-FALSE-CLAIM (tidied: the quotation was removed, the tag
was not)`. The verbatim sentence is now gone (`grep -c` = 0), tags = 3. **Measured: wiring
guard exit 0.** This is precisely the "bare negation removed" outcome red-drive **R3** exists
to prevent; R3 passes only because it deletes the tag *together with* the text, so it never
separates the two.

Calibration: case A, the unmutated tree, exits 0 first, so "the guard did not notice" is not
free.

**THE REPAIR, in one predicate** (both halves at once):

```bash
both="$(grep -Ei "$IMPOSS" "$f" | grep -c "QUOTED-FALSE-CLAIM")"   # tag AND text, same line
all="$(grep -Eic "$IMPOSS" "$f")"                                  # every line stating it
[ "$both" -ge 1 ] && [ "$both" = "$all" ]      # every statement is a tagged quotation,
                                               # and at least one tagged quotation exists
```

Case B fails it (`all` = 2, `both` = 1); case C fails it (`both` = 0). And add a third
assertion that reads `run-all.sh`'s **output** rather than its source, since the tag's whole
purpose is to mark text a reader will see.

**REPRODUCTION**

```
T448_SRC=<clone> T448_SCRATCH=/tmp/t448/scratch T448_OUT=/tmp/t448/tagabuse \
T448_REF=3253358d \
T448_GUARD=.softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh \
bash .softhouse/reviews/t448-review-t433/instruments/30-t448-tag-abuse.sh
```

`T448_GUARD` is a **parameter and not a literal on purpose**, and the reason is a finding
against my own first draft: the guard under test lives on `softhouse/T433-t423-c1` and is
absent from `main`, so spelling its path in a tracked instrument added a row to
`guard_dead_path_frontier` (108 → 109) and turned the bar **EXIT 2 with no probe line at all**.
That is the same shape the fire has been repairing in T446 and T447 all iteration. It was
repaired at the instrument, not pinned: the location is now supplied by the caller and a value
that does not resolve inside the checked-out tree is `exit 3`, never a skipped case. Measured
after the repair: `deadOccurrences=108`, frontier `11 == 11`. See §4.

---

### C-T448-3 — MINOR — F-6's stated reason for deferral is factually wrong

**Evidence:** `.softhouse/tasks.json` (T433 entry, `files_hint`);
`git ls-tree -r <T433 tip> -- .softhouse/reviews/A2-11`.

T433's handoff says section 9 "is `adjudicate-section1.py`, outside T433's assigned paths".
`adjudicate-section1.py` sits at `.softhouse/reviews/A2-11/adjudicate-section1.py`, and
`.softhouse/reviews/A2-11/` **is** one of T433's two `files_hint` entries — T433 edited three
other files in that same directory.

**I agree with the decision and reject the reason.** Repairing section 9 requires deciding a
materiality question (does A2-11 F-1's wire-shape finding now touch a graded vector? — see
§1.6, where the answer is "no, the search is wrong, not the world"), which is a different task
with a different risk profile, and the driver has it filed. But *"outside my assigned paths"*
is a load-bearing sentence in this pipeline, it is graded, and it is the kind of reason that
gets copied forward into the next handoff. State the real one: **it is a different defect
needing its own adjudication, and fixing it inside this task would have widened the scope.**

---

### C-T448-4 — MINOR — F-5 restates two cardinals wrongly and rests on a cost estimate that is an order of magnitude out

**Evidence:** `out/50-F5-ARGUED-ROWS.txt`;
`grep -c '^run_case ' .softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh`;
`.softhouse/capture/t393-t382-conditions/out/drive/MATRIX.tsv`.

* T433 calls it "T393's **full 13-case matrix**". It is **11** cases —
  `grep -c '^run_case '` = 11, and the committed `MATRIX.tsv` has 22 data rows = 11 × 2 refs.
* T433 says "the other **eleven** rows are argued". Two were driven, so **nine** were argued.
* T433 killed the re-drive as "26 whole `run-all.sh` runs … hours of wall clock". The matrix
  column is one command's exit code, so nine direct grader runs suffice — which is what I did,
  in about ten minutes total.

This is P-80 in miniature (a restated cardinal rots), inside the follow-up that exists to
record a gap in measurement. **The argument itself holds** — all nine rows measured exactly as
T393 recorded them — so the finding is about the bookkeeping, not the conclusion.

**CONDITION.** Close F-5 as measured, citing `out/50-F5-ARGUED-ROWS.txt`, and correct the two
counts wherever they were restated (handoff §4 F-5, and
`instruments/50-t433-runall-f1-13b-row.sh`'s header, which carries both).

---

### C-T448-5 — LOW — the invoker table is incomplete, the "17 sites" figure is not 17 pre-existing sites, and the enumeration is `.sh`-only

**Evidence:** `git grep -n "verify-capture-integrity" -- '*.sh' '*.py'` on the T433 tip;
`out/…` (T433's own `30-WIRING-GUARD.txt` §4).

The handoff's §3 "Wiring" table omits two real pre-existing invokers that T433's *own*
machine-generated enumeration does list:
`.softhouse/reviews/t382-review-t374/instruments/31-saturation-clean-target.sh:44` and
`.softhouse/reviews/t382-review-t374/instruments/10-attack-section10.sh:27`.

The figure **"17 existing invocation sites"** does **not** appear in T433's handoff — I checked;
it is the dispatch brief's summary, and it is the LINE COUNT of that enumeration block. Read as
"existing" it is wrong twice: three of the seventeen lines belong to **T433's own new
instruments**, and one of those (`30-t433-armf-wiring-guard.sh:111`) is a `want` assertion
*string*, not an invocation. The honest figures, measured on the T433 tip, are **11
pre-existing invoking `.sh` files across 14 pre-existing lines**. Direction of error is
conservative for the substantive claim, and the guard's own generated list is the authority,
so this is LOW — but a count standing beside a list whose length it restates is exactly the
shape that rots (P-80), and whoever carries the figure forward should carry 11/14.

Separately: the guard enumerates with `--include="*.sh"` only. No `.py` invokes the grader
today (I checked `'*.py'` as well as `'*.sh'`), but a future one would be invisible to the
wiring proof. Worth one word in the guard's own text.

---

### C-T448-6 — LOW — T433's correction footer in `TRANSCRIPT-A2-11.txt` is erased by the very script it documents, and nothing asserts it

**Evidence:** `out/71-TRANSCRIPT-FOOTER-IS-ERASED.txt`.

`run-all.sh`'s body is `{ … } | tee "$DIR/TRANSCRIPT-A2-11.txt"`, which truncates. Measured:
the footer marker greps **1** before a run and **0** after. Nothing in
`30-t433-armf-wiring-guard.sh` asserts any transcript's annotation — it checks four
executables.

LOW rather than higher because the regenerated transcript is produced by the **corrected**
`run-all.sh`, so the false sentence comes back **tagged** at line 711 and untagged nowhere.
What is lost is the attributed pointer to the sweep, the arm and the correction index.

---

## 3. WHAT I CHECKED AND FOUND CLEAN

* **Scope.** The diff touches `.softhouse/capture/t393-t382-conditions/`,
  `.softhouse/reviews/A2-11/`, T433's own `.softhouse/capture/t433-t423-c1/` and its own
  handoff. Nothing outside. No Fineract path touched, no Go code, no vector store, no
  `conformance.sh` (T445 holds it), no ratified DEC-n.
* **Money non-negotiables.** The only money artefact in the diff is the adjudication of
  `A2-370-db-ledger-state.txt`, re-derived above in integer minor units with no float anywhere
  in my own instrument either. No monetary code path is introduced by this task.
* **Prohibited engines.** No `ojdbc` / `oracle.jdbc` / `:1521` / MySQL / MariaDB token appears
  in the diff. No US payment rail, no `first_name`/`last_name`, no deposit-insurance language.
* **P-45.** ARM F is *inside* the grader `run-all.sh` adjudicates, not beside it. That is the
  right answer to the pattern, and it is the single best decision in this task. The one thing
  that is not wired — `conformance.sh` — is disclosed by name, with the exact line and the red
  drive its adopter must run (F-4). Correct handling.
* **P-22.** Every guard T433 ships has been seen to fail: ARM F (eight cases), the vacuity
  control (T433's and mine), the wiring guard (T433's four, plus mine).
* **The prediction T433 got wrong** — `(iv-b)`, where a high-similarity rename is REFUSED
  rather than missed — is recorded as wrong, in the docstring, in the drive's expectation and
  in the handoff. That is the honesty rule working, and it is why I believe the rest.

---

## 4. THE BAR, ON MY OWN COMMITTED WORK

Run from `/tmp` (scratch outside the repository), `bash`, never `sh`/`zsh`, on a committed
clean tree. Full transcript: `out/80-CONFORMANCE-BAR.txt`.

```
BAR EXIT 0
grep -c 'probe = '   ->  1      (tested that the line was PRINTED AT ALL, BEFORE its value was
                                 read — four exit-2 paths run before the probe prints, and
                                 ABSENCE IS NOT `down`. P-84.)
probe line, verbatim:
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
all 16 wrong ledger implementations DIED through this harness, not by hand.

fail-open frontier   : 11, pinned at 11, frontier == pinned (all 11 rows, by path)
dead-path census     : corpus=1582 deadFiles=75 deadOccurrences=108 resolving=1495 …
dead-path frontier   : GREEN, T323 reconciliation list empty
```

**My own seven instruments move neither figure — but only after a repair.** The fail-open
linter, run separately with my files tracked, reports corpus **1575 → 1581** (and 1582 in
the bar's own census, which counts the seventh instrument added after that lint) and frontier
**11 → 11**, with zero `t448` rows on the frontier: `out/81-FAILOPEN-LINT.txt`.
`deadOccurrences` stays at **108**.

**THE FIRST RUN OF THE BAR ON MY OWN COMMITTED TREE WAS `EXIT 2` WITH `probe = ` PRINTED ZERO
TIMES**, and it was my instrument that did it: `out/79-BAR-FIRST-RUN-REFUSED-BY-MY-OWN-INSTRUMENT.txt`.

```
> .softhouse/reviews/t448-review-t433/instruments/30-t448-tag-abuse.sh | .softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh
T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0
BAR EXIT 2      grep -c 'probe = ' -> 0
```

`30-t448-tag-abuse.sh:36` spelled the path of the guard it tests as a literal. That guard is on
`softhouse/T433-t423-c1` and **not on `main`**, so a tracked instrument on my branch carried a
dead path and moved `guard_dead_path_frontier` 108 → 109 — the same shape the fire has spent
this whole iteration repairing in T446 and T447, reproduced by the reviewer who was warned
about it. **Repaired at the instrument, not pinned** (commit `83d3c9c3`): the guard's location
is now a required caller-supplied parameter `T448_GUARD`, and a value that does not resolve
inside the checked-out tree is `exit 3` in `prepare()` — never a skipped case and never a pass,
which is the arm the frontier guard's own message asks for in exchange. Re-measured after the
repair: frontier `11 == 11`, `deadOccurrences=108`, dead-path frontier GREEN, bar `EXIT 0`.

Every instrument here takes its locations as required parameters (`${VAR:?…}`), writes no host
path, declares its engine, calibrates on a known positive before reporting any negative, and
exits 2 or 3 rather than 0 when it cannot measure.

**One note for the merger:** `main` advanced while this review ran (`ef97f3e3`, T445 + T446
merged), and that merge changes `.softhouse/conformance.sh`. My bar figures are against the
`conformance.sh` at my fork point `00b9f6d7`. The merge result must be re-barred against the
newer one; nothing in this branch touches `conformance.sh`, so no conflict is expected.

---

## 5. CONDITIONS, RESTATED AS WORK

| id | severity | condition |
|---|---|---|
| **C-T448-1** | **MAJOR** | Close `(iv-a)`'s **fail-open** with the `not f_at_tip` check plus an adjudication list, **or** replace "not closable by internal consistency" with the true statement and its real reason. Name re-observation against the pinned reference oracle (Fineract) as the external anchor for the detection half in F-2. |
| **C-T448-2** | MINOR | Repair the tag guard to assert the **binding** of tag to text (`both >= 1 && both == all`), and add an assertion over `run-all.sh`'s **output**, not only its source. |
| **C-T448-3** | MINOR | Correct F-6's deferral reason: `adjudicate-section1.py` **is** inside T433's `files_hint`. State the real reason. Section 9's repair is its own task — and it should fix the **search**, not move the pin (§1.6). |
| **C-T448-4** | MINOR | Close F-5 as measured (`out/50-F5-ARGUED-ROWS.txt`); correct "13-case" → 11 and "eleven argued" → nine wherever restated. |
| **C-T448-5** | LOW | Complete the invoker table; replace "17 existing invocation sites" with 11 files / 14 pre-existing lines; note the `--include="*.sh"` limit. |
| **C-T448-6** | LOW | Either guard the `TRANSCRIPT-A2-11.txt` footer or record that it is transient by design. |
| **F-3** | — | **Close it.** `(iv-c)` is driven four ways here and is not a fail-open (§1.8). |

---

## 6. ONE PARAGRAPH FOR THE NEXT READER

T433 was asked to correct a false impossibility and it did: the baseline it denied is real for
632 of 632, I re-derived that with a primitive T433 never used and got the same eleven numbers,
and the arm that uses it now lives inside the grader `run-all.sh` adjudicates rather than
beside it. The money it adjudicated balances in integer minor units in both versions and the
change is purely additive. The undriven boundary it disclosed, `(iv-c)`, turns out not to be a
hole at all; the argued rows it could not afford to measure turn out to be measurable in
minutes and all nine hold; the already-red runner it found on `main` is real, and is hours old
rather than ancient, and is a false positive of its own search. **The one thing to carry
forward is the shape of the MAJOR:** the task existed because a previous author wrote *"there
is no baseline"* instead of *"I did not find a baseline"*, and its own handoff then wrote
*"not closable"* instead of *"I did not close it"* — about a fail-open that closes with one
`check()` at zero cost on a clean tree. The lesson did not survive contact with the artefact
written to record it.
