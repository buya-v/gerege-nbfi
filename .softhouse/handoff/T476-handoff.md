# T476 — the repair pass on T467, under T472's MAJOR

Branch `softhouse/T476-t472-repair`, started from **T467's tip `6a345e4a`**, not from `main`.
T467 is deliberately unmerged; this branch carries **T467's work plus the repair** and is what
merges in its place. Scope worked: `.softhouse/reviews/A2-11/`,
`.softhouse/capture/t476-t472-repair/`, and this handoff. Nothing outside those.

**NOTHING BELOW IS INHERITED.** Every one of T472's findings was re-derived on a tree I built,
with the rules **lifted from their own blobs by AST** rather than retyped — grading a retyped
copy of a rule is grading the retyping. Where I disagree with T472 I say so with the drive
(§7).

---

## 1. VERDICT ON T472, ITEM BY ITEM

| id | severity | re-derived? | disposition |
|---|---|---|---|
| **C-T467-1** | **MAJOR** | **CONFIRMED, exactly** | **REPAIRED.** Both spellings reproduce at `6a345e4a` and are caught at my tip. The repair is structural, not another list of shapes. |
| **C-T467-2** | MINOR | **CONFIRMED for `%`-format and `bytes`; PARTLY REFUTED for f-strings** | **CLOSED for `%`, `bytes`, `+`, `.format()`; the f-string framing corrected (§7.1); the genuinely open residue re-stated and ASSERTED by a control.** |
| **C-T467-3** | MINOR | **CONFIRMED, member for member** | **PRICED AND PUBLISHED.** The six-file set is re-derived with its tree; T476 adds **zero** to it. |
| **C-T467-4** | LOW | **CONFIRMED** (15, not 11) | **RECORDED, not corrected** — the site is T467's handoff, outside the grant. |
| **C-T467-5** | LOW | **CONFIRMED, and it is worse than T472 said** | **CORRECTED IN CODE** (the loose form was in the check label too, not only in the handoff). |
| **C-T467-6** | LOW | **CONFIRMED** | **POINTER LEFT; DECLARED OPEN.** Needs a task with a grant over `.softhouse/handoff/`. |
| what T472 CONFIRMED | — | **RE-DRIVEN, unchanged** | Every F-T464-2 cardinal and control (l)'s falsifiability still hold at my tip. |

---

## 2. THE REPAIR I CHOSE, AND WHY — ON MEASURED EVIDENCE

T472 named two directions and picked neither: **union the predicates**, or **widen the
extractors**. I did **both, in a fixed order, and the order is the argument**:

> **ARM 1 is the union. The widenings sit on top of it. Nothing depends on a widening for the
> superset property, and nothing depends on the union for reach.**

### 2.1 Why the union is not optional

The failure T472 found is not "two shapes were missed". It is that **T467 replaced a rule
without ever measuring the replacement against it**, and then published a class claim. Any
repair that closes the two shapes T472 happened to find reproduces that method exactly: it
would be correct on the fixtures its author thought of, and its author would have no way to
know otherwise.

Keeping T455's `emitted_payload` verbatim as **ARM 1 of the union** makes
*"the new predicate sees everything the old one saw"* **true by construction, for all inputs**
— not true over 8 fixtures, or 249, or however many the next reviewer generates.

### 2.2 Why the union alone is not enough

Measured, at `6a345e4a`, on the generated matrix: the union closes the two regressions and
leaves `>&2 echo <unquoted words>  # <tag>` open, because that line is not `echo`-prefixed
either. It is the same argument T467 made about `printf`, pointed one token to the left. So
three widenings, each measured on its own:

| widening | what it closes | catches it earns on the 249-case matrix | **new false positives over 1,691 tracked files** |
|---|---|---|---|
| shell: the whole comment-stripped line, and `#` treated as POSIX word-start | unquoted words behind ANY emitter; a bare `${VAR#prefix}` earlier on the line | +5 (POSIX half alone) | **0** |
| shell: backslash-newline continuations joined, payload whitespace-normalised | a claim wrapped across a continuation, tagged or not | +14 / +14 | **0** |
| python: `bytes` Constants, and static folding of `+`, `%`, `.format()`, `.join()`, f-strings | `b"<claim>"` to fd 1; `"…%s…" % "…"`; `"a" + "b"` | +22 | **0** |

### 2.3 THE TRADE T472 WARNED ABOUT DID NOT MATERIALISE, AND THAT IS THE WHOLE ARGUMENT

T472's framing was: *union is cheap and monotonic but inherits T455's false positives;
widening is principled but every widening is a new false-positive surface.* **Both halves of
that trade are empirically zero here**, and this is what decided it:

* **the union inherits nothing**, because T455's rule flags **0** of the 1,687 tracked
  `.py`/`.sh` at `6a345e4a`. Re-derived, not quoted.
* **each widening costs nothing**, because the false-positive set is the SAME SIX FILES at
  every ablation point (§4). The ablation disables each arm **in the lifted code itself** and
  re-measures; `FP` never moves.

So there was no trade to make, and choosing "the cheap one" or "the principled one" would have
been a choice made in the absence of the measurement that dissolves the question. I took both.

### 2.4 THE UNCOMFORTABLE RESULT, REPORTED RATHER THAN BURIED

The ablation says something awkward about ARM 1: **disabling it loses NO catches on the
249-case matrix** (`catches delta +0`). The widened arms happen to cover the same shapes. An
arm that earns no catches looks exactly like a control that cannot fail (P-98), so I drove it:

`30-t476-superset-falsifiable.sh` unwires ARM 1 and changes nothing else. On a **clean** tree:

| | unmutated tip | ARM 1 unwired |
|---|---|---|
| section 10 exit | 0 | **1**, by a value, traceback ×0 |
| checks run | 53 | **53** — nothing skipped |
| SUPERSET CONTROL | PASS | **FAIL** |
| the REGRESSION SUITE check | PASS | **PASS — it does not move** |

**Read that last row.** With ARM 1 gone, all eight regression spellings are still caught, so a
worker who graded this repair the way T467 graded its own would see nothing wrong. The **only**
thing in the tree that sees the guarantee go is the SUPERSET CONTROL, and what it reddens on is
the python side, where the AST arm does not read raw source lines and nothing else does either.
That is precisely why ARM 1 stays: it is not there for catches, it is there so the relation is
a property of the code rather than of a fixture list.

The control is a **wiring tripwire**, described as one in the code, and deliberately stricter
than the semantic relation (it compares `(lineno, payload)` pairs, so a future author who
changes how payloads are represented is made to look). **The semantic property is measured
separately**, over the generated cross product — §3.

---

## 3. THE REGRESSION SUITE — DRIVEN, NOT CLAIMED

The acceptance test set for me was: *no spelling that `3f4e236a` caught may be missed at my
tip.* It is driven three ways, because one way is how this lineage got here.

### 3.1 THE GENERATED CROSS PRODUCT — `20-t476-population-cost.py`, EXIT 0

Not a hand list. A mechanical cross product of **emitter carrier × literal spelling × tag
placement** — 7 shell carriers × 5 shell literal forms and 6 python carriers × 8 python literal
forms, each in three tag placements: **249 cases**.

| | T455 `3f4e236a` | T467 `6a345e4a` | **T476** |
|---|---|---|---|
| cases caught, of 249 | 76 | 105 | **152** |
| **cases T455 catches and this ref MISSES** | — | **4** | **0** |
| correctly TAGGED quotations wrongly flagged | 0 | 0 | **0** |

**The four T467 loses** are exactly the two families T472 named, in both their carrier
spellings: `py/print/bytes/trailing-comment`, `py/print/decode/trailing-comment`,
`sh/echo/bare/trailing-comment`, `sh/echo-tab/bare/trailing-comment`.
**T476 loses none.** It gains **47** cases over T467.

### 3.2 SECTION 10's OWN SELF-DRIVE — five new checks, in the file, on every run

Eight spellings, each a live emitter with the tag in a trailing comment, asserted RED; plus:
predicate 1 must fire on **none** of them (or the two predicates would have collapsed into
one); the **superset** wiring tripwire; the **NUL-byte** fail-closed check; and the
**declared blind spot**, asserted so the docstring cannot drift away from the behaviour.
Section 10 runs **53** checks at my tip against **48** at T467's.

### 3.3 END TO END, WHERE THE HARM ACTUALLY LANDS — `10-t476-regression-suite.sh`, EXIT 0

An exit code is not the harm. The harm is a false sentence, untagged, in the artefact a reader
opens.

| case | T455 `3f4e236a` | T467 `6a345e4a` | **T476** |
|---|---|---|---|
| **U** `echo <words, UNQUOTED>  # <tag>`, section 10 | **exit 1** | **exit 0** | **exit 1** |
| **Q** the same line, words QUOTED, section 10 | exit 1 | exit 1 | exit 1 |
| **A2** `print(b"<claim>".decode())  # <tag>`, section 10 | **exit 1** | **exit 0** | **exit 1** |
| **U** through the whole runner | — | `run-all.sh` **exit 0**; transcript carries the sentence **UNTAGGED ×1** and its own verdict says **PASS** | `run-all.sh` **exit 1**; transcript carries it untagged ×1 and its own verdict says **FAIL** |
| **G** clean tree, whole runner | — | — | exit **0**, sections run **10**, deviations **0**, untagged ×**0** |

**Case Q is the control that gives case U its meaning**: the only difference between the caught
line and the missed line is one pair of quote characters. **Case G is the load-bearing green** —
a predicate that reddens honest trees is a freeze, not a guard.

**THE OBVIOUS EXPECTATION IS WRONG, AND I WROTE IT BEFORE I DROVE IT.** Section 10 grades
SOURCE; it cannot stop a live emitter from printing. The smuggled `echo` runs inside
`run-all.sh`'s own teed block, so the sentence reaches the transcript at BOTH refs. What
changes is what the transcript says about ITSELF: at T467 it carries a false sentence untagged
and calls the run a **PASS** — a publishable record of a lie; at T476 the same bytes are there
and the record says **FAIL**, so nobody can cite it. **The harm was never the echo. It was the
PASS.** My drive originally asserted `untagged ×0` at T476 and went BAD on it; the assertion
was wrong, not the repair, and it is now written the way the mechanism actually works.

#### 3.3.1 TWO defects in MY OWN instrument, found by driving it, and what it now refuses

The first run of this drive reported case A2 as `T455=0 T467=1` — **the finding inverted**. It
was not a finding. `PYANCHOR` was built with `$(printf 'import hashlib\nimport os\nimport
sys\n')`, and **command substitution strips trailing newlines**, so the smuggled line was
welded onto `import sys` and the mutated `.py` no longer PARSED. The grader then fell back to
its lexical rule, which sees the quoted claim, while T455's `print(`-prefix test no longer
matched a line starting `import sysprint(`. **The case had stopped testing the spelling it
names, and it said so by producing the wrong answer rather than by staying silent** — which is
the only reason it was caught.

Two changes: the anchor is `$'…'` (ANSI-C quoting, which keeps the byte), and the mutation now
**REFUSES with exit 3 unless the mutated `.py` still parses**. The second defect is the
transcript expectation immediately above. A mutation that breaks the parse
measures the fallback, not the spelling, and a case that measures the wrong thing must not be
able to report a number at all. Recorded here because a drive that is not itself driven is the
defect this whole lineage is about, one level further out.

---

## 4. THE FALSE-POSITIVE SET, RE-DERIVED, WITH ITS TREE

`20-t476-population-cost.py`, population = **every tracked `.py`/`.sh`** in the repository.

| tree | population | T455 flags | T467 flags | T476 flags |
|---|---|---|---|---|
| `6a345e4a` | 1,687 | **0** | **6** | — |
| `0d15e5c7` (the graded tip) | **1,691** | **0** | **6** | **6** |

**T476's delta against T467 is `+0 / −0`.** The set is member-for-member the one T472 named,
and I print the firing payload with it:

1. `capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh:89` — a grep pattern in `IMPOSS=`
2. `capture/t433-t423-c1/instruments/31-t433-wiring-guard-red-drive.sh:55` — a `printf` that PLANTS the sentence as a fixture
3. `capture/t433-t423-c1/instruments/40-t433-annotate-echoing-transcripts.sh:31` — a grep pattern in `PAT=`
4. `capture/t455-t448-conditions/instruments/30-t455-tag-binding-drive.sh:133` — `local imposs=`
5. `reviews/t448-review-t433/instruments/30-t448-tag-abuse.sh:48` — `FALSE_SENTENCE=`
6. `reviews/t464-review-t455/instruments/40-t464-caseB-adjudication.py:26,30` — `SENT=` / `IMPOSS=`

T472's reading of the set is right and worth repeating: **all six are tag-guard instruments
from this exact lineage** — the files a future task is most likely to add to `CORRECTED`. The
fix for each is one line (assemble the sentence from words), and **the four files T476 adds to
the population do exactly that and are flagged ×0**.

**The four guarded files are flagged ×0 on a clean tree** at every ablation point. That is the
number that decides whether the guard is usable at all.

### 4.1 ONE WIDENING I REJECTED, ON THE MEASUREMENT

Running the lexical shell arm over a `.py` that **parses** (as well as the AST arm) looks
strictly more fail-closed. Measured, it is not: false positives **6 → 9**, it flags
`verify-capture-integrity.py` itself — a **guarded** file, so the guard would be red on a clean
tree — and it fires on the **inert-docstring** control, which is exactly how a guard gets
deleted instead of fixed (P-29). **The AST arm is what makes "a docstring prints nothing"
expressible at all.** Recorded in the code beside the decision, with the numbers.

---

## 5. THE SENTENCE THAT MUST NOT ENTER THE RECORD

Shipped by T467 in `printed_payloads`'s docstring:

> `T467 / F-T464-1 — THE EMITTER CLASS, CLOSED.`

T472 is right: that is **an untagged false claim inside the file whose subject is untagged
false claims**, and no guard in this repository can see it, because it is not one of the five
`FALSE_CLAIMS` patterns. It is **corrected in code**. The docstring now states, in this order:

* **what regressed** — the two spellings, named, with which ref caught them;
* **what is closed** — three arms, named, and what each is for;
* **what it costs** — 6 of 1,691, the six named as a lineage, and the instrument that
  re-derives them, with the explicit warning that the number goes stale;
* **what was rejected and why** — the arm-3-on-parsing-python widening, with its numbers;
* **what stays open** — declared, and one of them asserted by a control.

**No class is claimed closed anywhere in the shipped text.** The other claims held to the same
standard, with the ones outside my grant recorded rather than edited, are in
`.softhouse/capture/t476-t472-repair/out/T467-HANDOFF-CORRECTIONS.md`.

---

## 6. THE LOWS AND THE CARRIED ITEMS

### 6.1 C-T467-4 — "11 controls" where the tree runs 15. CONFIRMED; RECORDED

`40-t476-failclosed-nonregression.sh` on a clean tree at my tip: **exit 0, 29 checks,
`(a)`–`(k)` = 11, ALL controls = 15.** T467's handoff §3.3 prints "11 controls" for AFTER,
dropping the qualifier its own instrument prints. The four missing are `(l)`, `(l1)`, `(l2)`,
`(m)` — the ones T467 added. **The site is outside my grant.**

### 6.2 C-T467-5 — the `os.write` claim. CONFIRMED, AND WORSE THAN T472 SAID

Re-counted at `6a345e4a`, excluding T467's own files: `os.write(` appears in **four** tracked
files — `t248-failopen-widen/…/10-c1-characterise.py:60`,
`t248-failopen-widen/…/40-red-drive.py:82`, `t270-superseded-trap/prove-t270-exempt-red.py:88`,
`t41-probe/t187-redgreen.py:154` — and **every one writes to a `mkstemp` fd, none to fd 1**.

T472 says the in-code sentence is accurate and only the handoff's short form is wrong. That is
right about the sentence and **incomplete about the code**: the **check's own label** read
*"a spelling NOBODY IN THIS REPOSITORY HAS USED"* — the loose form — and so did the comment
above the fixture. Both are in my grant and **both are corrected**, to name fd 1 and cite the
four pre-existing uses.

### 6.3 C-T467-6 / F-T464-4 — the pointer

Not editing another task's handoff was the right call and I have not. What I have done is
leave the pointer T472 asked for, in the two places a reader of this branch will land — this
handoff and `out/T467-HANDOFF-CORRECTIONS.md` §6 — together with the re-measured facts:
`30-t448-tag-abuse.sh` contains `both` twice (line 16 prose, line 87 a `REFUSED:` message) and
**neither is the figure**; the figure is in `.softhouse/reviews/t448-review-t433/REVIEW.md`;
`grep` for the literal `all=2` finds nothing in that review directory. The correction lives at
`.softhouse/capture/t467-t464-conditions/out/T455-ATTRIBUTION-CORRECTION.md`.

**THIS IS NOT CLOSED AND IS NOT CLAIMED CLOSED.** `.softhouse/handoff/T455-t448-conditions.md:300`
still carries the wrong location. A reader who opens it and stops there still gets the wrong
instrument. **It needs its own task, with a grant over `.softhouse/handoff/`.**

### 6.4 T472's OWN LEFT-OPEN ITEMS — three of them fell out of the construction, so I drove them

| T472 left open | driven here | outcome |
|---|---|---|
| the `${VAR#prefix}` lexer-truncation route | fixture V2 + `sh/paramexp/*` in the matrix | **REAL at `6a345e4a`, CLOSED at my tip** by treating `#` as a comment only at the start of a word — emitted as an ADDITIONAL payload, never a replacement, because in python `#` really does open a comment mid-word and a replacement would fail OPEN |
| the two-**line** wrapped payload | fixtures W2, W3 + `sh/*/continue/*` | **REAL, and T467's stated mitigation is FALSE** — see §7.2. Closed at my tip for the continuation form |
| `ast.parse` raising `ValueError` on a NUL byte | fixture D5, asserted in the file | **REAL. T472 reasoned it; it reproduces.** `printed_payloads` caught only `SyntaxError`, so a guarded `.py` with a NUL took the grader down by traceback — the F-T464-2 defect one file over. **Closed**: the fallback now catches `ValueError` too and the file falls back to the lexical rule |

---

## 7. WHERE I DISAGREE WITH T472 — TWO CORRECTIONS, BOTH MEASURED

T472's review is accurate on every cardinal I could reach, and the MAJOR is exactly right.
Two framings are not.

### 7.1 "f-strings" is not a blind family — the blind shape is narrower, and the reach figure overstates it

C-T467-2 lists three families that *"carry the whole claim in literals on ONE line and are
caught by neither predicate"*: `%`-formatting, **f-strings**, and `bytes` literals, with reaches
of 7,152 / 571, **2,491 / 170**, and 192 / 60. **All three reach figures reproduce exactly**
(I re-counted them). The **f-string** classification does not:

* `ast.walk` **descends into `JoinedStr`**, and its constant parts **are** `str` Constants. So
  an f-string whose constant parts carry the claim contiguously was **already caught at
  `6a345e4a`** — driven as fixture A5, CAUGHT at both refs, and as
  `py/*/fstring/trailing-comment` in the matrix, caught by T467.
* T472's own fixture A4 — `f"…older than {chr(72)}EAD for those 632."` — is blind **because the
  letter `H` is computed at runtime**, not because it is an f-string. It belongs to the
  runtime-assembly family, and for that family the sentence *"the literal is real and on one
  line"* is **not true**: part of the claim is not in the source bytes at all.
* Of the 2,491 f-strings, only **1,033 in 158 files** even have an interpolation *between* two
  constants — the only shape where a claim could be split — and being split additionally
  requires the claim to straddle it.

So: `%`-formatting and `bytes` were genuinely blind and are genuinely closed. The f-string half
of C-T467-2 is **a runtime-assembly case wearing an f-string**, and I have re-declared it that
way rather than claiming to have closed something that was not open.

### 7.2 T467's wrapped-payload mitigation is FALSE, not merely untested

T467 §9 declares: *"A claim WRAPPED across two payloads. Predicate 1 de-wraps contiguous tagged
blocks and does see it."* T472 records that it did not test the two-line form. **Driven here,
and predicate 1 does NOT see it**: `tagged_blocks` collects only lines that CONTAIN the tag and
feeds the POSITIVE half; predicate 1's NEGATIVE half is strictly per-line. A claim wrapped
across two source lines with the tag on neither, or only on the second, is invisible to **both**
predicates at `6a345e4a` (fixtures W2, W3; `sh/*/continue/untagged` in the matrix, where T467
catches **0** and T476 catches all). The continuation form is now closed by joining
backslash-newlines before lexing and normalising whitespace in the payload comparison.

---

## 8. WHAT T472 CONFIRMED — RE-DRIVEN AT MY TIP, UNCHANGED

`40-t476-failclosed-nonregression.sh`, **EXIT 0**. T476 touches a different file, and *"it did
not move"* is a claim about a tree, so it is measured rather than reasoned.

| | measured at my tip |
|---|---|
| clean tree | exit **0**, **29** checks, `(a)`–`(k)` **11**, ALL controls **15** |
| a TRACKED non-JSON vector carrying a token | exit **1 by a value**, traceback ×**0**, **29 of 29** checks, **11 of 11** controls `(a)`–`(k)`, `FAILURES:` ×**1**, named assertion ×**1** |
| **control (l)'s falsifiability** — T455's exact `int` return restored, **CLEAN** corpus | exit **1**, traceback ×**0**, 29 checks; **(k) PASSES** while **(l) and (l1) FAIL** |

The third row is the one that answers *"is (l) just (k) renamed"*, and it still answers it
**no** at my tip. F-T464-6's published limit and F-T464-5's coverage discipline are untouched.

---

## 9. WHAT IS STILL OPEN — DECLARED, NOT ARGUED SHUT

* **A fragment of the claim COMPUTED at runtime** — `f"…{chr(72)}EAD…"`, `printf '%s' "$SENTENCE"`.
  The bytes are not in the source, so no static reader of the source can see them. **Open by
  construction**, and it is the ONE spelling in the self-drive suite that goes through. It is
  **asserted by a check**, so if a later widening catches it the check goes RED and the
  docstring is wrong until someone updates it.
* **A payload split across two ADJACENT QUOTED WORDS on one line** — `echo "…for those " "632."`.
  Measured: **7 of the 249 generated cases**, all `sh/*/adjacent/trailing-comment`. **Missed by
  T455 too, so it is not a regression** — it is the residue T472 spotted incidentally at its
  case A6, and it is now enumerated instead of noticed.
* **A payload split across two SEPARATE COMMANDS** (not a continuation). De-wrapping across
  statement boundaries would join unrelated payloads into a claim neither of them makes.
* **The population is the four files in `CORRECTED` and nothing else.** A fifth file that quotes
  the false sentence is not graded by section 10 at all. True before T455, true now — and §4
  says which six files would need one line each before they could join it.
* **Six files flagged of 1,691.** Not false in the sense that matters (they do carry the
  sentence outside a tag) but they are not emitters. Repairable one line each; unrepaired.
* **`conformance.sh`'s half of the section-4 search** is still a raw substring match — T455's
  open item, untouched, still fail-closed rather than silent.
* **The DETECTION half of `(iv-a)`** — unchanged, and unchangeable from inside an offline file.
* **Section 4 walks the disk (`rglob`), not `git ls-files`.** T467 recorded it; T472 drove it;
  it is the fail-closed direction. Unchanged.
* **F-T464-4's site in T455's handoff**, and T467's handoff's own §1/§2.2/§3.3/§9 sentences —
  **outside my grant**; recorded in `out/T467-HANDOFF-CORRECTIONS.md`. **This needs a task.**
* **The SUPERSET CONTROL is a wiring tripwire, not an independent measurement**, and it is
  stricter than the semantic relation it protects. The semantic relation is measured by
  `20-t476-population-cost.py` over a generated matrix, and a matrix is still an enumeration.
  Stated so nobody reads the control as more than it is.

---

## 10. THE BAR

_(filled below — taken at the branch tip, `bash`, from a scratch directory outside the
repository, on a committed clean tree, with the probe line's PRESENCE tested before its value
was read.)_

### 4.2 COVERAGE — WHICH BYTES THE DRIVES ABOVE ACTUALLY GRADED (F-T464-5, the lesson in play)

All four drives were taken at **`0d15e5c7`**, the last commit that changes any graded byte. A
transcript cannot be taken at a commit that does not yet exist, so the commit carrying these
transcripts is necessarily later. The check is one command per file, and the blob ids the
drives printed are these:

| file | blob at `0d15e5c7`, printed by the drive |
|---|---|
| `.softhouse/reviews/A2-11/verify-capture-integrity.py` | `424309f356216c2f0286e5a6ddc7f7261448bc19` |
| `.softhouse/reviews/A2-11/run-all.sh` | `3aee8cd13690b7fd3eb92ba3caa2a2f58453faa7` (untouched by me) |
| `.softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py` | `ed8a29f6d96a018e9014b8f2d4f8eac0efb2a692` (untouched by me) |

`git rev-parse <branch tip>:<path>` printing the same blob is the whole check. The commits
after `0d15e5c7` add only `out/` transcripts, the regenerated `TRANSCRIPT-A2-11.txt`, this
handoff and the bar — no file any drive grades.

---

## 10a. A CANDIDATE PATTERN, FOR THE DRIVER TO NUMBER — `.softhouse/patterns.md` IS OUTSIDE MY GRANT

**A GUARD THAT REPLACES A GUARD MUST BE MEASURED AGAINST THE ONE IT REPLACED, AND THE ONLY
RELIABLE WAY TO DO THAT IS TO KEEP THE OLD ONE WIRED IN.** T433 → T448 → T455 → T467 is four
tasks of the same move: each read its predecessor's guard as too narrow, wrote a wider-looking
one, and graded the new one against fixtures it chose. T467 is the first where the replacement
was measurably NARROWER on two shapes — and it shipped a class claim beside it. Three things
follow, and all three are cheap:

1. **Grade the new rule against the OLD rule's catches, over a generated cross product**, not
   over hand-written fixtures. A hand list of shapes is how the belief forms in the first place.
2. **Keep the replaced rule as an arm of the new one.** Then "wider" is a property of the code.
   Expect the arm to earn zero catches; that is not a reason to remove it (§2.4).
3. **Price the new rule over the whole tracked population, not over the files it guards.**
   "Zero false positives" was true of four files and false of the rule.

Recorded here rather than in `patterns.md` because that file is outside this task's scope.

## 11. ONE PARAGRAPH FOR THE NEXT READER

T467's diagnosis was right and its method was the disease. It saw that an emitter list is a
list the next author extends without reading, and replaced it with a list of *syntactic shapes
it happened to think of* — then published a class claim that no measurement in the branch
supported. The check that would have caught it costs one line and nobody in this lineage had
run it: **assert that the new rule sees everything the old one saw.** I ran it, and the answer
was no. The repair is therefore not "three more shapes"; it is to keep the replaced rule wired
in as an arm so the relation is structural, and to treat every widening on top of it as a claim
with a price that has to be measured over the whole tracked population rather than over four
files. The price turned out to be **zero**, at every ablation point — which is a fact about
this repository at this moment, not a property, and `20-t476-population-cost.py` re-derives it
in one command. The one thing I would tell the next reviewer to attack first is §2.4: ARM 1
earns no catches on any matrix I could build, and if you can show the SUPERSET CONTROL cannot
fail for a reason I have not found, then the guarantee is decoration and this handoff is wrong.
