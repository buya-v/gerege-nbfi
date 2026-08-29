# T467 — T464's conditions on T455

Branch `softhouse/T467-t464-conditions`. Fork point `3f4e236a` (= `main` at dispatch, T455 and
T464 both merged). Scope worked: `.softhouse/reviews/A2-11/` and
`.softhouse/capture/t467-t464-conditions/`. **No edit outside those two directories except this
handoff file.** Nothing here is inherited: every cardinal was re-measured on the tree under test,
and where a figure came from T464 and I re-derived it, both are printed side by side.

---

## 1. DISPOSITION, ITEM BY ITEM

| id | severity | disposition |
|---|---|---|
| **F-T464-1** | MINOR | **CLOSED AS A CLASS.** The predicate no longer names an emitter. Five spellings driven RED at AFTER, four of them GREEN at BEFORE, plus the whole runner and the regenerated transcript at both refs, plus the clean-tree control end to end. |
| **F-T464-2** | MINOR | **CLOSED.** The fail-closed branch is reached BY A VALUE; the 15 checks the traceback used to skip all run; a new control drives the CONSUMER, which is where the defect actually lived. |
| **F-T464-3** | LOW | **CORRECTED, and the corrected sentence is MEASURED at this ref**, not copied from T455's table. |
| **F-T464-4** | LOW | **CONFIRMED and re-measured, corrected in the in-grant record. DECLARED OPEN** — T455's handoff is outside my grant and still carries the wrong location. |
| **F-T464-5** | LOW | **ADDRESSED BY CONSTRUCTION.** Every transcript carries a COVERAGE block naming the graded ref, the blob id of each graded file and the commit that last touched it. See §7 for the honest residue. |
| **F-T464-6** | LOW | **PUBLISHED, AND THE ONE-SPACE EVASION CLOSED.** The residual limit is asserted by a control so it cannot drift silently. |
| SETTLED | — | The T455-vs-T448 adjudication, `run-all.sh` BEFORE 1 / AFTER 0, the pin present ×1 at both refs, `want_min`, P-98 — **not reopened, not re-driven, not re-argued.** |

---

## 2. F-T464-1 — THE REACH, RE-DERIVED, THEN THE CLASS CLOSED

### 2.1 What I measured before I changed anything

T455's `emitted_payload` returned a payload only for a line whose stripped form starts with
`echo `, `echo\t` or `print(`. Everything else returned `None` and **was not judged by predicate 2
at all**.

**The reach, re-counted on the tree at `3f4e236a`** (T464 states 12 and 5; both confirmed, and the
instrument asserts them so a future tree that moves them goes red):

| | `printf` | `>&2` | `sys.stdout.write` |
|---|---|---|---|
| `10-drive-conditions.sh` | **12** | **5** | — |
| `run-all.sh` | **5** | 0 | — |
| `verify-capture-integrity.py` | 0 | 0 | **0** |
| `12-relaunder-manifest.py` | 0 | 0 | **0** |

So two of the three spellings T464 named are **already the idiom of two of the four guarded
files**; the third is a reach, and I drive it anyway. This is not "someone would have to invent a
way round" — it is the way those files already print.

**Each spelling driven at `3f4e236a` before any repair, section 10's own exit code:**

| smuggled as | BEFORE |
|---|---|
| `echo "<claim>"  # <tag>` | **1** — T455's close, working |
| `printf FMT "<claim>"  # <tag>` | **0 — through** |
| `>&2 echo "<claim>"  # <tag>` | **0 — through** |
| `sys.stdout.write("<claim>")  # <tag>` | **0 — through** |
| `_v = "<claim>"  # <tag>` then `os.write(1, _v.encode())` | **0 — through** |

**And the harm reproduced where it lands, which is not an exit code.** At BEFORE, with the
`printf` smuggle: `run-all.sh` **exits 0**, and the **regenerated `TRANSCRIPT-A2-11.txt` carries
the false sentence UNTAGGED ×1** (and tagged ×1, from the legitimate quotation). That is T464's
finding, at first hand.

### 2.2 The repair, and why it is not three more names

An emitter list is a list the next author extends without reading — that is the whole shape of
this finding. So `printed_payloads(text, rel)` **names no emitter**. It asks what a line CARRIES
to a reader:

* **python** — every string CONSTANT that is not a *docstring* and not a *bare string statement*,
  read from the **AST**. Comments are not in the tree at all, so they are excluded by
  construction. It never asks whether the constant reaches `print`, `sys.stdout.write`, a logger,
  a variable printed forty lines later, or `subprocess` running `printf`.
* **shell** — every quoted SEGMENT left after the out-of-quote `#` comment is cut.
* **a `.py` that will not PARSE** — falls back to the shell rule, so a syntax error cannot buy
  silence.

It is deliberately an **over-approximation in the payload direction**, which is the fail-closed
direction: a non-emitting line that merely *carries* a quoted claim (a grep pattern, a comparison
string) is judged as if it printed. **That cost is measured, not assumed** — on the four guarded
files at this ref it is **zero false positives**, and the clean tree is green through the whole
runner (§2.3, case G).

**The `os.write` fixture is the point of the exercise.** It is a spelling **nothing in this
repository uses**. If the predicate only caught the four spellings someone had thought of, the
class claim would be false and the next reviewer would arrive with a fifth.

### 2.3 DRIVEN — `instruments/10-t467-printed-class.sh`, `out/10-PRINTED-CLASS-DRIVE.txt`, **exit 0**

| case | BEFORE | AFTER |
|---|---|---|
| control, unmutated tree | grader **0**, 43 checks | grader **0**, 48 checks |
| `echo` | 1 (already caught) | **1**, PREDICATE 2 ×1, PREDICATE 1 ×0 |
| `printf` | **0** | **1**, PREDICATE 2 ×1, PREDICATE 1 ×0 |
| `>&2 echo` | **0** | **1**, PREDICATE 2 ×1, PREDICATE 1 ×0 |
| `sys.stdout.write` | **0** | **1**, PREDICATE 2 ×1, PREDICATE 1 ×0 |
| `os.write` (unused spelling) | **0** | **1**, PREDICATE 2 ×1, PREDICATE 1 ×0 |
| **T** whole runner + regenerated transcript, `printf` smuggle | `run-all.sh` **0**, transcript **UNTAGGED ×1** | `run-all.sh` **1**, section 10 row `*** MOVED ***` ×1 |
| **G** whole runner, **CLEAN TREE**, at AFTER | — | `run-all.sh` **0**, **deviations 0**, transcript untagged ×**0** |

**Case G is the load-bearing one.** Every red above is free if the predicate reddens honest trees
too. It does not: same exit code, same ten sections, zero deviations.

**"PREDICATE 1 ×0" is asserted in every case, not just observed.** The source line does carry the
tag, so the binding half must *not* fire — if it did, the two predicates would have collapsed into
one and the reason there are two would be gone.

**And the discrimination half runs on every execution of the grader**, in memory: a comment that
quotes the claim with the tag outside the quotes, and a docstring that does the same, must **not**
fire predicate 2. Without those two the new rule would flag every corrected file for carrying its
own correction, which is precisely how a guard gets deleted instead of fixed (P-29).

**One observation worth recording.** In the `os.write` case the smuggled raw write to fd 1
**corrupted the grader's own captured transcript** — the buffered `print` stream and the raw
`os.write` share a file offset, and the saved output ends mid-section-8 at 8,118 bytes against
~18,500 for its siblings. The verdict is unaffected (the `FAIL PREDICATE 2` line is present and
counted), but it is a small demonstration that an emitter outside the file's own convention does
damage beyond the sentence it smuggles.

---

## 3. F-T464-2 — A FAIL-CLOSED BRANCH MADE REACHABLE BY A VALUE

### 3.1 The defect, re-derived

`classify_occurrences`'s unparseable branch returned `[("UNPARSEABLE", text.count(tok))]` — an
**int** in the slot the other two branches fill with a JSON path — and the caller prints
`where[:70]`. Reproduced on a clone with one tracked non-JSON file under `.softhouse/vectors/`
carrying one of the seven tokens:

```
TypeError: 'int' object is not subscriptable
```

**The cardinals, re-derived rather than quoted:**

| | BEFORE |
|---|---|
| checks the file runs on a clean tree | **25** |
| checks executed on the crashing tree | **10** |
| **checks SKIPPED** | **15** |
| `FAILURES:` tally lines printed | **0** |
| the named section-4 assertion | **never runs** |
| section 5 controls **(a)–(k)** reached | **0 of 11 — including (k), the control FOR this branch** |

T464's figure of 15 is exact, and the 15 decompose as: the named corpus assertion, the
structural-parse positive control, the two provenance-ref checks, and all eleven negative
controls.

### 3.2 The repair

The branch returns a **location string** (`<raw substring, N hit(s), JSONDecodeError>`). The
fail-closed direction is now reached **by a value**: the named assertion FAILS, `FAILURES: 1`
prints, and every control still runs.

**And the more interesting half: why control (k) was true the whole time.** (k) inspects
`classify_occurrences`'s **return value**. The live arm does not stop there — it builds a row and
prints it. So the control covered half the code path and the defect lived in the other half. The
consumer is now factored out (`census` + `render_rows`, the exact functions the live arm calls)
and three new controls drive it:

* **(l)** the unparseable branch, through `census` + `render_rows`, yields a MATERIAL row and
  renders it **without raising**;
* **(l1)** every location this file emits is a `str` — the type the renderer slices;
* and section 4's banner states the whole story where the next reader will hit it.

### 3.3 DRIVEN — `instruments/20-t467-failclosed-by-value.sh`, `out/20-FAILCLOSED-BY-VALUE.txt`, **exit 0**

| case | BEFORE | AFTER |
|---|---|---|
| calibration, clean tree | exit 0, **25** checks, 11 controls | exit 0, **29** checks, 11 controls |
| tracked non-JSON vector with a token | exit 1 **by traceback**, **10 of 25** checks, `FAILURES:` ×**0**, named assertion ×**0**, controls **0 of 11** | exit 1 **by value**, traceback ×**0**, **29 of 29** checks, `FAILURES:` ×**1**, named assertion ×**1**, controls **11 of 11** |
| **clean tree at AFTER** | — | exit **0**, 29 checks, all **7** tokens still `MATERIAL=0` |
| identifier-shaped value with one trailing space (F-T464-6) | exit **0** — the evasion, reproduced | exit **1** on the named assertion |

**"15 of 25 skipped" and "29 of 29 run" are the same measurement taken twice**, on the same
mutated tree, at two refs. The clean-tree row is what stops the second from being bought by a
guard that simply always fails.

---

## 4. F-T464-6 — the discriminator, published AND tightened

The rule was "the value contains any whitespace ⇒ PROSE", so `"A2-99-<token> "` — identifier-shaped
apart from **one trailing space** — was graded immaterial. An evasion one whitespace character
wide is not a limit worth publishing; it is a bug. So:

* the value is **stripped** before the shape test (control **(l2)**, and driven through the live
  corpus walk as case 4 above: BEFORE exit 0, AFTER exit 1);
* **the residual limit is published in `classify_occurrences`'s docstring and in section 4's
  printed banner**, beside the classifier, per P-29: *a token inside a genuinely MULTI-WORD value
  is still graded PROSE*. If the harness ever compares a value with an interior space, a token
  hidden there would be counted as prose and would not redden this arm. The fix, if it ever
  matters, is to grade against the harness's comparison set rather than against the shape of the
  value;
* and control **(m)** asserts that limit, so it is a stated boundary rather than a silent drift.

---

## 5. F-T464-3 — the stale sentence, corrected AND measured

The docstring said of `(iv-b2)`: *"…lands in (iv-a): reported UNGRADED, exit 0."* At this ref
section 9 asserts `not f_at_tip`, so it exits 1.

**I did not re-quote T455's case 5.** Re-stating somebody else's measurement is the mistake in the
other direction. `instruments/30-t467-ivb2-consequence.sh`, `out/30-IVB2-CONSEQUENCE.txt`,
**exit 0**, at this ref:

| | measured |
|---|---|
| clean-tree calibration | exit **0**, born-at-tip **0** |
| git's own account of the rename+whole-rewrite commit | **ADD ×1, rename ×0** — the *premise* of the sentence, measured, not assumed |
| the grader on that tree | **exit 1**, named section-9 assertion ×1, still reported `UNGRADED-BORN-AT-TIP` ×1 |
| the shipped docstring | stale sentence ×**0**, corrected sentence ×**1** |

Half the old sentence was right and is kept: the observation *is* still reported UNGRADED. What
moved is the **consequence** — reporting it is no longer a pass.

---

## 6. F-T464-4 — the attribution, corrected in the in-grant record, and DECLARED OPEN

T455's handoff line 300 attributes T448's wrong `all=2, both=1` to `30-t448-tag-abuse.sh`.
**Measured here:**

* that instrument contains the word `both` exactly **twice** — line 16 is prose, line 87 is a
  `REFUSED:` message. **Neither is the figure.**
* the figure is at **`.softhouse/reviews/t448-review-t433/REVIEW.md:364`**, written
  ``Case B fails it (`all` = 2, `both` = 1); case C fails it (`both` = 0).``
* a `grep` for the literal `all=2` finds **nothing** in that whole review directory — the review
  writes it with spaces and backticks, which is presumably how the citation slid one file sideways.

The correction, with the wrong sentence **quoted rather than deleted**, is at
`.softhouse/capture/t467-t464-conditions/out/T455-ATTRIBUTION-CORRECTION.md`, following the
precedent T455 itself set with `T433-CORRECTION.md`.

**THIS IS DECLARED OPEN, NOT CLOSED.** `.softhouse/handoff/T455-t448-conditions.md` is outside my
two granted directories and still carries the wrong location. A reader who reaches that sentence
without reaching my correction will still open the wrong instrument. Closing it needs a grant that
includes `.softhouse/handoff/`.

---

## 7. F-T464-5 — coverage, stated in the transcript

Every one of the three transcripts ends with a **COVERAGE** block that prints, without the reader
running anything: the graded ref, and for each graded file its **blob id** and the commit that
**last touched** it at that ref.

**The honest residue, since this finding is exactly about not glossing one.** A transcript cannot
be taken at a commit that does not yet exist, because committing the transcript changes the tip.
So the transcripts record `a729a5db` (commit 2 of 3 on this branch); commit 3 adds only
`out/` transcripts and this handoff. The COVERAGE block makes that checkable in one command per
file rather than in a `git log` a reader has to think to run:

| file | blob at the graded ref |
|---|---|
| `.softhouse/reviews/A2-11/verify-capture-integrity.py` | `f233ff56b22fbffcf9478fe9c3b95ba3cec268af` |
| `.softhouse/reviews/A2-11/adjudicate-section1.py` | `dbaf35248d41af1c848f05d7896a1f6ab6ea4d78` |
| `.softhouse/reviews/A2-11/run-all.sh` | `3aee8cd13690b7fd3eb92ba3caa2a2f58453faa7` (last touched by T455's `140a7ae7` — untouched by me) |
| `.softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh` | `b193894bd608b2d40f55922fc69214e762fe2f33` (last touched by T433's `7df613d1` — untouched by me) |

`git rev-parse <branch tip>:<path>` printing the same blob is the whole check.

---

## 8. THE TRANSCRIPT, AND THE RUNNER

`TRANSCRIPT-A2-11.txt` is **regenerated in this branch**, because the two graded files changed and
a transcript that describes a previous version of the file it grades is the F-T464-3 defect wearing
a different hat. `bash .softhouse/reviews/A2-11/run-all.sh` at this tree: **exit 0**,
`sections run: 10  deviations: 0  RUN-ALL VERDICT: PASS`.

---

## 9. WHAT IS STILL OPEN — declared, not argued shut

* **A claim built at RUNTIME and printed through a variable** — `printf '%s' "$SENTENCE"` — carries
  no literal, so no static reader of the source can see it. Predicate 2 cannot reach it, and
  neither could any refinement of it that still reads source text. **Open by construction.**
* **A claim WRAPPED across two payloads.** Predicate 1 de-wraps contiguous tagged blocks and does
  see it; predicate 2 is per-payload and does not. A wrapped *untagged* claim is therefore caught
  by 1 and missed by 2 — which is survivable only because 1 exists. **Stated.**
* **Shell `#` inside an UNQUOTED word** (`${VAR#prefix}` written bare) truncates the line for
  `strip_trailing_comment`, so a payload after it on the same line is not seen. It does not occur
  in the four guarded files at this ref. **Not closed.**
* **The population is the four files in `CORRECTED` and nothing else.** A fifth file that quotes
  the false sentence is not graded by section 10 at all. That was true before me and still is.
* **`classify_occurrences`'s multi-word-value limit** (§4), asserted by control (m).
* **`conformance.sh`'s half of the section-4 search** is still a raw substring match — T455's open
  item, unchanged by me, and still fail-closed rather than silent.
* **The DETECTION half of `(iv-a)`** — unchanged, and unchangeable from inside an offline file.
* **F-T464-4's site in T455's handoff** (§6), outside my grant.
* **Section 4 walks the disk (`rglob`), not `git ls-files`.** An *untracked* file under
  `.softhouse/vectors/` is graded exactly like a tracked one. I noticed this while building the
  drive (the crash reproduces without committing anything) and left it alone: it is the
  fail-closed direction. **Recorded so the next reader does not have to rediscover it.**

---

## 10. THE BAR

Run from a scratch directory **outside** the repository, `bash` (never `sh`/`zsh`), on a
**committed, clean** tree. The probe line's **PRESENCE was tested before its value was read**
(P-84 — four exit-2 paths run before the probe prints, and absence is not `down`):

```
### git status --porcelain BEFORE the bar (must be 0 lines):
### lines: 0
### HEAD: 1afa5dba3f2b52ec68a421911dfa1b4f93784b39

grep -c 'probe = '  ->  1      (PRESENCE tested BEFORE the value was read)
probe line, verbatim:
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

VERDICT: PASS (exit 0) - 46 parity vectors match the pinned reference oracle, 7884 cells compared.
fail-open frontier : 11, pinned at 11, frontier == pinned
dead-path frontier : GREEN, rows=108 pinned=108 added=0 removed=0, reconciliation list empty
dead-path census   : corpus=1687 deadFiles=75 deadOccurrences=108
BAR EXIT 0
```

Full transcript: `.softhouse/capture/t467-t464-conditions/out/40-BAR.txt`, taken at commit
`1afa5dba` (commit 3 of 4). Commit 4 adds that transcript and this paragraph and nothing else --
no tracked file the bar grades moves between them, which the `git status --porcelain -> 0 lines`
line above is the calibration for.

---

## 11. ONE PARAGRAPH FOR THE NEXT READER

Both MINOR findings are the same defect at different altitudes: **a guard that was written against
an example rather than against a class.** T455 closed `echo` because `echo` was the abuse it was
shown; it wrote a control for the unparseable branch that examined the classifier because the
classifier was the code it had just written. Both are the natural move, and both leave a hole the
size of "the next spelling" and "the next line of the same function". The two repairs are the same
repair: **stop asking which construct, start asking what reaches the reader** — and **drive the
consumer, not the callee**. The check that would have caught T455 is cheap and I have added it in
both places: for every predicate, name the thing you are NOT enumerating, and write the control
against something outside your own list.
