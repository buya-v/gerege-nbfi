# T481 — independent adversarial review of T476

**Target** `softhouse/T476-t472-repair`, tip **`36e01f25`** (5 commits on top of T467's
`6a345e4a`; the branch carries **T467's work plus the repair** and merges in T467's place).
**Refs used throughout:** `3f4e236a` = the emitter rule (T455, and `main` at T467's dispatch),
`6a345e4a` = the payload rule (T467), `36e01f25` = the union (T476's tip).
Read from the branches with `git show` / `git diff`; every figure below is from an instrument
in `.softhouse/reviews/t481-review-t476/instruments/`, run on trees I built.

## VERDICT: **APPROVED WITH CONDITIONS**

**The regression is gone.** Re-derived, not inherited: over a **1,992-case** cross product of
my own construction — eight times T476's population, with three tag placements, three shell
literal spellings, three python literal spellings, five python carriers, two shell carriers
and a **file-type axis** that T476's generator does not have — the set of cases the T455 rule
catches and the T476 rule misses is **empty**, and so is the set of cases T467 catches and
T476 misses. End to end, at three refs, the two named spellings behave exactly as T476
reports.

**This stack is safe to merge.** It is strictly greener than `main` on the spellings that are
reachable, it does not add one false positive to the tracked population, the bar is EXIT 0 at
its tip on my own run, and every cardinal T472 confirmed still reproduces at that tip. The
conditions below are about **what the shipped text claims for the control that protects the
repair**, not about the repair.

| id | severity | one line |
|---|---|---|
| **C-T476-1** | **MAJOR** | The SUPERSET CONTROL detects **one** edit — removal of the seeding line. Empty ARM 1, or narrow it, and the control stays **GREEN** and section 10 exits **0**. The handoff's "the only thing in the tree that sees the guarantee go is the SUPERSET CONTROL" is false for both. |
| **C-T476-2** | MINOR | ARM 1 re-imports an inert-context false positive T467 did not have — a `print(`-prefixed line **inside a docstring** — which is the exact category §4.1 cites to reject a different widening. The shipped inert-docstring control cannot see it. |
| **C-T476-3** | MINOR | "correctly TAGGED quotations wrongly flagged: **0**" is a fact about 249 cases. Member set of 8 shapes at the tip where a *printed, correctly tagged* quotation is flagged, plus 2 constructed. **New since T467: 0** — so a published sentence to correct, not a regression. |
| **C-T476-4** | LOW | `out/T467-HANDOFF-CORRECTIONS.md:62` cites a measurement "at `07aa5a86`" — a real object that is **not an ancestor of this branch** (an orphaned pre-amend commit). The figures reproduce at the tip; the citation points at a tree no reader can reach. |
| **C-T476-5** | LOW | §7.1's account of *why* T467 was blind is narrower than the mechanism. An f-string split by a **static** interpolation — nothing computed, all bytes in the source — is clear at T467 too. T476's headline is right; its explanation is not the general one. |
| **C-T476-6** | LOW | The VACUITY CONTROL's published cardinal moved **2 → 8** and its label still says "quotation **lines**". Measured, it is **8 payloads over 2 source lines** — the same union multiplicity commit `0d15e5c7` deduped for the reported SITES and did not dedupe here. |

**What survives attack, and survives it well:** the repair itself. The union is a superset of
the rule it replaced **by construction** — `printed_payloads` seeds itself from
`emitter_payloads` and thereafter only appends — and I verified the arm is behaviourally
`emitted_payload` lifted from `3f4e236a`, with **0 disagreements on 144 probe lines**. The
three widenings cost **+0 / −0** false positives on the whole tracked population at both refs.
Every published measurement I could re-derive reproduced, several of them to the digit.

---

## 0. WHAT I RE-DERIVED, AND WHAT I DID NOT

**Re-derived at first hand, on trees I built, with every rule LIFTED FROM ITS OWN BLOB BY AST**
(grading a retyped copy of a rule is grading the retyping):

* ARM 1's behavioural identity with `emitted_payload` at `3f4e236a`, over 144 probe lines;
* a **1,992-case** generated cross product at three refs, with axes T476 does not enumerate;
* the ARM-1 ablation, in the lifted code, split by whether what it decides is a catch or a
  false positive; and the same question on **constructed** inputs when the matrix said nothing;
* the SUPERSET CONTROL under **three** mutations, each independently proved not to be a no-op;
* the false-positive population at **1,687** and **1,691** tracked `.py`/`.sh`, member for
  member, all three rules;
* the three reach cardinals, and the narrow f-string count under four readings;
* the widening T476 **rejected**, by mutating the lifted code, over the 1,687 population;
* section 10's check count at all three refs; the end-to-end U/Q/A2 cases at all three refs and
  the whole runner at two;
* the whole fail-closed non-regression suite, including control (l)'s falsifiability;
* the parse-fallback's exception surface over ten probes;
* `bash .softhouse/conformance.sh` on **T476's tip `36e01f25`** in a scratch clone outside the
  repository, and on my own committed tree.

**NOT re-derived — stated so it is not read as verified:**

* T476's own instruments. I ran none of them; every figure here is from mine.
* The `(iv-b2)` rename-and-whole-rewrite drive (T472 did not rebuild it either; I did not).
* The `TRANSCRIPT-A2-11.txt` byte diff against a clean regeneration at the tip — my clean-tree
  runner arm measures `deviations: 0` and untagged ×0, which is the property that matters, but
  I did not diff the committed transcript line by line as T472 did at `6a345e4a`.
* `conformance.sh`'s raw-substring half, and the DETECTION half of `(iv-a)` — declared open by
  T476, unchanged, not driven by me.
* Whether `07aa5a86`'s tree differs from `eb57a88d`'s in any graded byte. I established only
  that it is **not on the branch**.

---

## 1. CLAIM 1 — THE REPAIR CHOICE AND THE TWO MEASUREMENTS UNDER IT. **BOTH HOLD.**

`30-t481-population.py`, EXIT 0, `out/30-POPULATION.txt`.

| tree | population | T455 flags | T467 flags | T476 flags |
|---|---|---|---|---|
| `6a345e4a` | **1,687** | **0** | **6** | **6** |
| `36e01f25` | **1,691** | **0** | **6** | **6** |

* **(i) the union inherits nothing.** T455's rule flags **0 of 1,687** and **0 of 1,691**.
  Reproduced.
* **(ii) every widening costs nothing.** T476's delta against T467 is **+0 / −0**, and the
  member SET is the same six T472 named — re-derived at `36e01f25`, with the firing payload:

  1. `.softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh:89` — `IMPOSS=`
  2. `.softhouse/capture/t433-t423-c1/instruments/31-t433-wiring-guard-red-drive.sh:55` — a `printf` that plants the sentence as a fixture
  3. `.softhouse/capture/t433-t423-c1/instruments/40-t433-annotate-echoing-transcripts.sh:31` — `PAT=`
  4. `.softhouse/capture/t455-t448-conditions/instruments/30-t455-tag-binding-drive.sh:133` — `local imposs=`
  5. `.softhouse/reviews/t448-review-t433/instruments/30-t448-tag-abuse.sh:48` — `FALSE_SENTENCE=`
  6. `.softhouse/reviews/t464-review-t455/instruments/40-t464-caseB-adjudication.py:26,30` — `SENT=` / `IMPOSS=`

  The four guarded files are flagged **0** times on a clean tree.

So the trade T472 warned about does measure to zero **on this corpus at this moment**, and
T476's choice — take both, union first — rests on numbers that are correct. The docstring says
in terms that this is a measurement that goes stale; that qualification is doing real work,
and C-T476-2 is the first place it comes due.

**ARM 1 IS THE RULE IT CLAIMS TO BE.** `10-t481-matrix-and-arm1.py` §0: over 144 probe lines
crossing four indentations, six leading tokens and six tails, `emitter_payloads` at `36e01f25`
and `emitted_payload` at `3f4e236a` **disagree on 0**. So "kept verbatim" is right in
substance (the code is restructured from a per-line function to a whole-text enumerator; the
rule is identical).

**THE SUPERSET RELATION IS PROVABLE BY READING, NOT ONLY BY MATRIX.** `printed_payloads` is
`out = list(emitter_payloads(text))`, then `return out + python_payloads(text)` or a loop that
only **appends**. Predicate 2 is a per-payload test (`states_a_false_claim(squeeze(p)) and TAG
not in p`) and `squeeze` only widens matching. `FALSE_CLAIMS`, `TAG` and
`strip_trailing_comment` are byte-identical at both refs. So *every* catch of T455's rule is a
catch of T476's, for all inputs — not for 249 of them, and not for my 1,992. That is the
strongest thing in this branch and it is correctly identified as such.

### 1.1 THE REJECTED ALTERNATIVE — RE-DERIVED, AND IT REPRODUCES EXACTLY

`90-t481-rejected-widening.py`, EXIT 0. The widening (run the lexical arm over a `.py` that
parses) is built by **mutating the lifted code**, and the mutation is proved non-vacuous on a
probe before anything is counted. Over the **1,687** population:

| | files flagged |
|---|---|
| shipped | **6** |
| widened | **9** |

added: `.softhouse/reviews/A2-11/verify-capture-integrity.py` (a **guarded** file — the guard
would be red on a clean tree), `.softhouse/reviews/t423-review-t393/instruments/20-t423-birth-blob-probe.py`,
`.softhouse/reviews/t423-review-t393/instruments/60-t423-birth-arm-reaches-residual.py`.
The widened rule **fires on the shipped inert-docstring fixture**; the shipped rule does not.
**Every number in that published sentence reproduces.** The rejection is well-founded.

---

## 2. CLAIM 2 — THE REGRESSION SUITE. **THE 0-MISS CLAIM HOLDS UNDER MY OWN ATTACK.**

`10-t481-matrix-and-arm1.py`, EXIT 0, `out/10-MATRIX.txt`. My generator is not T476's. Where
T476 enumerates 7 shell carriers × 5 shell literals and 6 python carriers × 8 python literals
in 3 tag placements (249), mine enumerates **9 shell carriers × 10 shell literals** and
**11 python carriers × 11 python literals** in **6 tag placements**, each python case in
**two file states** — parsing and non-parsing — for **1,992** cases.

**The axes T476's population cannot express, and now does:** `heredoc` and `tee` carriers;
`sys.stderr.write`, `raise`, `return`, a dict value and a **bare string expression statement**
as python carriers; ANSI-C `$'…'`, backslash-escaped words, mixed quoting, an adjacent-word
split at the **last** word, and a two-command variable assembly as shell literals; implicit
adjacent concatenation, `" ".join([…])` and a two-slot `%`-tuple as python literals; the tag
on the **preceding** line, on the **following** line, and inside the payload's **second**
element; and a `.py` that does **not parse**, which takes the lexical fallback.

| | T455 `3f4e236a` | T467 `6a345e4a` | **T476 `36e01f25`** |
|---|---|---|---|
| cases caught, of 1,992 | 699 | 896 | **1,054** |
| **cases T455 catches and this ref MISSES** | — | **5** | **0** |
| cases T467 catches and this ref misses | — | — | **0** |
| grading RAISED | 0 | 0 | **0** |

**The 0 is the acceptance test and it holds.** The five T467 loses are the two families T472
named, in every carrier spelling my matrix reaches:
`{py/print/bytes/trailing-comment, py/print/decode/trailing-comment,
sh/echo/bare/trailing-comment, sh/echo-tab/bare/trailing-comment,
sh/tee/bare/trailing-comment}` — the fifth is a carrier T476's generator does not have, and it
is the same defect, so T476's "exactly the two families" is right and its count of 4 is a fact
about its own 249.

**AND THE MATRIX CANNOT FALSIFY THE CLAIM, WHICH IS THE POINT.** Given §1's four-line proof, no
population can produce a T455-catch that T476 misses. The matrix is therefore not the evidence
for the superset relation; it is the evidence for everything else — the T467 delta, the
discrimination half, and the ablation. **That is the correct division of labour and T476 states
it**, and it is the reason the self-selected-population defect (T451→T456, T462→T469) does not
apply to the 0-miss figure here: the figure is not a generalisation from the population.

### 2.1 MY OWN GENERATOR HAD A DEFECT, AND I FOUND IT BY RUNNING IT

My first run reported **44 "correctly tagged payloads wrongly flagged, new since T467"**. It
was not a finding. Three literal spellings (`concat`, `implicit`, `join`) computed the two
halves of the sentence **once, from the untagged form**, and so silently discarded the tag the
placement had just inserted: those cases were untagged and were being graded as tagged.
Repaired at the instrument — the halves are now a function of the string passed in — and the
44 went to **0**. Recorded rather than quietly fixed, because a reviewer whose drive is not
itself driven is the defect this whole lineage is about.

### 2.2 END TO END, WHERE THE HARM LANDS

`60-t481-end-to-end.sh`, `out/60-END-TO-END.txt`.

| case | T455 `3f4e236a` | T467 `6a345e4a` | **T476 `36e01f25`** |
|---|---|---|---|
| **U** `echo <words, UNQUOTED>  # <tag>`, section 10 | exit **1** | exit **0** | exit **1** |
| **Q** the same line, words QUOTED, section 10 | exit 1 | exit 1 | exit 1 |
| **A2** `print(b"<claim>".decode())  # <tag>`, section 10 | exit **1** | exit **0** | exit **1** |

Case Q is what makes case U mean *one pair of quote characters*, and it holds. The whole-runner
and clean-tree arms are in §7.

---

## 3. CLAIM 4 — IS ARM 1 LOAD-BEARING? **YES — AND EVERY INPUT IT DECIDES IS A FALSE POSITIVE.**

This is the item T476 asked to be attacked first, and it is worth the billing. The answer is
sharper than T476's own, in both directions.

**Over the 1,992-case matrix, ARM 1 decides NOTHING.** `10-t481-matrix-and-arm1.py` §3 unwires
ARM 1 in the lifted code: predicate-2 cases lost = **0**; whole-verdict cases lost = **0**.
T476's §2.4 reproduces, on a population eight times larger.

**So I stopped enumerating and constructed.** `20-t481-arm1-decides.py` builds the two families
where ARM 1 *must* differ from the other arms, from the shape of the code rather than from a
list of shapes: ARM 1 reads **physical** lines where every other arm reads
continuation-**joined** ones, and ARM 1 is a **lexical** rule that runs over a `.py` that
**parses**, where the AST arm marks docstrings inert. Both families produce inputs ARM 1
decides:

| constructed case | what the reader of the output sees | with ARM 1 | without | correct? |
|---|---|---|---|---|
| **C1** claim complete on continuation line 1, **tag printed** on line 2 | the claim **and** the tag | FLAG | clear | flagging is **WRONG** |
| **C2** the same, tag also in a trailing comment | the claim and the tag | FLAG | clear | **WRONG** |
| **C3** claim on line 1, ordinary text on line 2, tag in a comment | the claim, untagged | FLAG | FLAG | ARM 1 decides nothing |
| **D1** a `print(`-prefixed line inside a **function docstring** | **nothing** | FLAG | clear | **WRONG** |
| **D2** the same inside a **module docstring** | nothing | FLAG | clear | **WRONG** |
| **D3** the same, tagged inside that docstring | nothing | FLAG | clear | **WRONG** |
| **E1/E2** a live untagged print / a correctly tagged print | — | FLAG / clear | FLAG / clear | the calibration (P-72) |

**ARM 1 earns 0 catches and causes 5 false positives.** The instrument refuses unless E1 (a
known positive) is flagged and E2 (a known negative) is clear, so its negatives are not the
negatives of a probe that cannot speak.

**What that means for "superset by construction".** It is **not decoration** — ARM 1 changes
the rule's behaviour on real inputs — but it is not insurance against a missed catch either,
because on every input I can construct or generate the widened arms already dominate it. Its
value is exactly and only what T476 says: it removes the need to trust that analysis. That is
a legitimate engineering position and I would keep the arm. What it is **not** is free: it is
paid for in the false-positive direction, and §4 is the bill.

---

## 4. C-T476-1 (MAJOR) — THE SUPERSET CONTROL DETECTS ONE EDIT, AND THE TEXT CLAIMS MORE

`50-t481-control-can-fail.sh` (EXIT 1 by design — two mutations did not behave as the shipped
text says) and `51-t481-mutations-are-real.py` (EXIT 0 — **every mutation is proved to change
the arm or the union before any verdict is reported**, because a green control on a mutation
that never applied is a broken instrument, not a finding).

The check counts reproduce first: section 10 runs **43** checks at `3f4e236a`, **48** at
`6a345e4a`, **53** at `36e01f25`, all exit 0.

| mutation | what it does | ARM 1 after | section 10 | checks | SUPERSET CONTROL | REGRESSION SUITE |
|---|---|---|---|---|---|---|
| — | unmutated tip | 3 payloads on the probe | exit **0** | 53 | PASS | PASS |
| **M1** | the seeding line `out = list(emitter_payloads(text))` → `out = []` | untouched; union on a `.py` **2 → 1** | exit **1**, traceback ×0 | 53 | **FAIL** | PASS |
| **M2** | the arm returns `[]` for every input | **0 payloads** | exit **0** | 53 | **PASS** | PASS |
| **M3** | the arm keeps `echo `, drops `echo\t` and `print(` | **1 payload** | exit **0** | 53 | **PASS** | PASS |

**M1 is T476's drive and it reproduces exactly.** M2 and M3 are the finding.

**Why.** The control asserts `set(emitter_payloads(t)) <= set(printed_payloads(t, rel))`, and
`printed_payloads` **is seeded from `emitter_payloads`**. The relation is therefore a tautology
for *any* implementation of the arm: shrink the arm and the inclusion gets easier. The control
can fail on exactly one edit — deletion of the seeding — and on nothing else. It is not, as the
handoff has it, "deliberately stricter than the semantic relation": in the direction that
matters — the arm ceasing to be T455's rule — it is **vacuous**.

**And nothing else in the tree sees it.** Under M2 and M3 the REGRESSION SUITE still passes
(the widened arms cover its eight spellings on their own — T476 says so), the eight explicit
spelling checks still pass, and section 10 exits **0**. So the handoff's §2.4 sentence

> "The **only** thing in the tree that sees the guarantee go is the SUPERSET CONTROL"

is **false for two of the three ways to destroy the guarantee**: under M2 and M3 *nothing* in
the tree sees it go. The shipped check label compounds this by naming
`emitter_payloads` "the REPLACED rule (T455's `echo`/`print(` matcher)" — an **identity claim
the control does not verify**. The identity holds today; I measured it (§1). Nothing in the
tree measures it tomorrow.

**Why this is MAJOR and not a nit.** The arm's own docstring tells the next author it "earns no
catches"; the ablation table tells them the same; §2.4 tells them the control will catch them
if they touch it. Two of those three sentences are true and the third is the one that would
have to hold for the first two to be safe to publish. This is the same shape as the finding
T476 was dispatched to repair — a claim published beside a rule that the measurement does not
support — one level further out, and it lands in the file whose subject is exactly that.

**Why it does not block merge.** The guarantee holds at the shipped tip; the defect is in the
durability of the guarantee, and it is strictly better than `main`, where there is no guarantee
and no control at all.

**The remedy is small, and I drove enough to say so.** Either (a) grade ARM 1 against something
independent of the union — assert it fires on the three prefixes and not on a fourth, over the
fixture set, which M3 would redden — or (b) correct the label and §2.4 to say what the control
actually detects: *removal of the seeding line, and nothing else.* I did not implement either;
I review, I do not fix.

---

## 5. C-T476-2 (MINOR) — ARM 1 RE-IMPORTS THE INERT-DOCSTRING FALSE POSITIVE T467 DID NOT HAVE

`20-t481-arm1-decides.py`, three-ref arm, and `90-t481-rejected-widening.py`.

| constructed case | T455 | T467 | **T476** |
|---|---|---|---|
| D1 a `print(`-prefixed line inside a **function docstring** | FLAG | **clear** | **FLAG** |
| D2 the same inside a **module docstring** | FLAG | **clear** | **FLAG** |
| D3 the same, tagged inside that docstring | FLAG | **clear** | **FLAG** |

A docstring prints nothing, so flagging it is wrong. This is not new to the lineage — it is
T455's behaviour, restored by keeping T455's rule — but it **is new relative to T467**, and it
is the one place where "the union inherits nothing" is a statement about the corpus rather than
about the rule.

**The sharp edge is that §4.1 rejects a different widening for this exact reason:**

> "Running it there raises the false-positive count from 6 to 9, flags THIS FILE … and fires on
> the **inert-docstring** control, which is precisely how a guard gets deleted instead of fixed
> (P-29). **The AST arm is what makes 'a docstring prints nothing' expressible at all.**"

ARM 1 *is* a lexical arm running over a `.py` that parses. It is narrower — only lines whose
first token is `echo `, `echo\t` or `print(` — but on those lines it does not know what a
docstring is. Measured side by side at the tip:

* shipped rule on the **shipped** inert-docstring fixture → **clear**
* widened rule on the same fixture → **FLAGS**
* shipped rule on a docstring **whose line starts with `print(`** → **FLAGS**

So the last sentence quoted above is true of ARM 2 and false of the union that contains ARM 1.
The shipped inert-docstring control cannot see this because its fixture has no `print(`-
prefixed line; adding one is a one-line change and would make the residue visible instead of
latent. Zero occurrences in the tracked population today (T455's rule flags 0 of 1,691), so
there is no live harm — which is why this is MINOR and not MAJOR.

---

## 6. C-T476-3 (MINOR) — THE DISCRIMINATION FIGURE DOES NOT GENERALISE

T476 publishes "correctly TAGGED quotations wrongly flagged: **0**" for all three refs over its
249 cases. Over my 1,992 the figure is **8**, and the member SET at `36e01f25` is:

```
sh/command/wordsplit/tag-inside-2nd     sh/heredoc/wordsplit/tag-inside-2nd
sh/echo/wordsplit/tag-inside-2nd        sh/printf/wordsplit/tag-inside-2nd
sh/echo-tab/wordsplit/tag-inside-2nd    sh/stderr-echo/wordsplit/tag-inside-2nd
sh/eval/wordsplit/tag-inside-2nd        sh/tee/wordsplit/tag-inside-2nd
```

— `echo "<claim> " "[<tag>]"`, where the quoted-segment arm offers the first segment on its own
and that segment carries the claim without the tag, while the line as printed carries both.
Plus the constructed C1/C2 of §3 (the claim complete on continuation line 1, the tag printed on
line 2).

**New since T467: 0.** Every one of these is flagged at `6a345e4a` as well, so **this is not a
regression** and it does not touch the merge. What needs correcting is the published sentence:
the 0 is a property of a population that has no `wordsplit` spelling and no `tag-inside-2nd`
placement, and it reads as a property of the rule. The direction is fail-closed (over-tagging),
the corpus has none of these shapes, and the fix for any real instance is one line — which is
why this is MINOR.

---

## 7. CLAIM 5 — THE TWO SELF-DISCLOSED DEFECTS, AND THE CONCLUSION DRAWN FROM THE SECOND

**Defect 1, the stripped newline.** Confirmed by construction rather than by re-breaking it: my
own end-to-end drive uses ANSI-C quoting for the python anchor and **independently refuses
(exit 3) unless the mutated `.py` still parses**, and it planted case A2 at all three refs
without refusing. A mutation that breaks the parse measures the lexical fallback, not the
spelling it names; the repair is the right one and it is the right *shape* of repair — the case
can no longer report a number for a thing it is not running. **Disclosing this was worth more
than the defect cost**, and it is the second time in two commits that this branch's own drive
caught its author.

**Defect 2, and T476's conclusion.** Re-driven, `60-t481-end-to-end.sh`, **EXIT 0** — the same
tree, the same smuggled unquoted `echo`, through the whole runner at two refs:

| ref | runner exit | untagged sentences in `TRANSCRIPT-A2-11.txt` | the transcript's own verdict |
|---|---|---|---|
| `6a345e4a` | **0** | **1** | **PASS** ×1, FAIL ×0 |
| `36e01f25` | **1** | **1** | PASS ×0, **FAIL** ×1 |
| **case G** — clean tree at `36e01f25`, whole runner | **0** | **0** | sections run **10**, deviations **0** |

Case G is the load-bearing green: a predicate that reddens honest trees is a freeze, not a
guard, and this one does not.

**T476's conclusion — "the harm was never the echo, it was the PASS" — is right, and it is the
correct reframing.** Section 10 grades **source**; it has no mechanism to stop a live emitter
inside `run-all.sh`'s own teed block, so the bytes reach the transcript at both refs and any
expectation of `untagged ×0` at the repaired ref is an expectation about a thing the guard does
not do. What the guard buys is that the run which printed the false sentence **cannot be cited
as a pass**.

**One limit T476 does not state, and I will.** The protection is for a reader who reads the
verdict. A reader who opens the transcript, finds the sentence and quotes it is misled at
**both** refs — the repair moves the record, not the bytes. T476 says "the same bytes are
there", so nothing here is concealed; but "the harm was never the echo" is one degree stronger
than the measurement, and the measurement is "the harm that this guard can reach was the PASS".

---

## 8. CLAIM 3 — WHERE T476 DISAGREES WITH T472. **ADJUDICATED.**

`40-t481-adjudicate-t476-vs-t472.py`, `out/40-ADJUDICATE.txt`. Cells name which predicate
fires.

### 8.1 f-strings — **T476 wins the headline; its explanation is narrower than the mechanism (C-T476-5, LOW)**

| case | T455 | T467 | T476 |
|---|---|---|---|
| **F1** f-string, claim **contiguous**, tag in a trailing comment | P2 | **P2** | P2 |
| **F2** f-string split by a **computed** value `{chr(72)}` (T472's A4) | clear | clear | clear |
| **F3** f-string split by a **static** interpolation `{'H'}` | clear | **clear** | **P2** |
| **F4** the same claim in a plain `str` (calibration) | P2 | P2 | P2 |

* **T476 is right** that f-strings are not a blind family: `ast.walk` descends into `JoinedStr`
  and F1 was already caught at `6a345e4a`. T472's C-T467-2 listed the family too broadly.
* **T476's explanation is not the general one.** F3 has nothing computed at runtime — the
  letter is a string constant, every byte is in the source — and T467 is blind to it exactly as
  it is to A4. So T467's f-string blindness was to the **split**, of which a computed value is
  one cause and a constant interpolation is another. "A4 belongs to the runtime family" is true
  of A4 and false as an account of the blindness.
* **The code is right either way.** T476 closes the static half through `_fold` and declares
  only the runtime half open, and the shipped docstring's open-item wording ("a fragment of the
  claim COMPUTED at runtime") is accurate **for T476's own rule**. Only §7.1's account of T467
  is narrow. Hence LOW.

**The reach cardinals.** Re-counted at `6a345e4a` from the blobs: `"literal" % …` **7,152 sites
in 571 files**; f-strings **2,491 in 170**; `bytes` literals **192 in 60**. **All three match
T472's published figures exactly**, as T476 says.

**The narrow f-string count.** `31-t481-fstring-count.py` enumerates four readings of "an
interpolation BETWEEN two constants": a `FormattedValue` with a `Constant` on both sides gives
**1,031 / 158**; ">= 1 `FormattedValue` and >= 2 `Constant`s" and ">= 1 `Constant` before and
after" both give **1,033 / 158**. **T476's 1,033 reproduces** under two of the four; the
residual was my definition, not its arithmetic. Recorded so nobody reads 1,031 as a correction.

### 8.2 T467's wrapped-payload mitigation — **T476 is right: it is FALSE, not merely untested**

| case | T455 | T467 | T476 |
|---|---|---|---|
| **W1** wrapped over a continuation, tag in a comment on **both** lines | clear | **clear** | **P2** |
| **W2** wrapped over a continuation, tag in a comment on the **second** line | clear | **clear** | **P2** |
| **W3** wrapped over a continuation, **no tag anywhere** | clear | **clear** | **P2** |
| **W4** wrapped over two **separate commands**, no tag (declared open) | clear | clear | clear |

T467 §9 declares *"a claim WRAPPED across two payloads … predicate 1 de-wraps contiguous tagged
blocks and does see it."* **It does not.** `tagged_blocks` collects only lines that CONTAIN the
tag and feeds the POSITIVE half; predicate 1's NEGATIVE half is strictly per-line. W3 is the
decisive row: the sentence reaches the reader with **no tag anywhere in the file** and neither
predicate at `6a345e4a` says so. T472 recorded that it had not tested the two-line form; T476
tested it and found the mitigation false. **A declared mitigation that is false is worse than an
omission**, because it is the sentence a later reader stops at — and T476 is right to say so in
those terms. W4 is open at all three refs, as declared.

---

## 9. CLAIM 6 — THE CORRECTIONS, HELD TO THEIR OWN STANDARD

* **`THE EMITTER CLASS, CLOSED` is gone.** Every surviving occurrence in the branch tree is a
  **quotation inside a correcting context** — `verify-capture-integrity.py:1298`
  ("That sentence was FALSE"), `T476-handoff.md:224`, `out/T467-HANDOFF-CORRECTIONS.md:25`.
  **No class is claimed closed anywhere in the shipped text.** Verified by search over the tip.
* **The `os.write` correction.** Re-counted at `36e01f25`, excluding T467's and T476's own
  files: `os.write(` appears in **four** tracked files —
  `capture/t248-failopen-widen/instruments/10-c1-characterise.py:60`,
  `capture/t248-failopen-widen/instruments/40-red-drive.py:82`,
  `capture/t270-superseded-trap/prove-t270-exempt-red.py:88`,
  `reviews/t41-probe/t187-redgreen.py:154` — and **every one writes to a `tempfile.mkstemp`
  fd**; none writes to fd 1. The corrected check label names fd 1 and cites the four. Accurate.
* **Recording rather than editing C-T467-4 and T467's handoff sentences was right.** T455 set
  the precedent, T467 followed it twice, T472 endorsed it, and the grant is explicit. The
  residue T476 names is real and is the strongest argument for the follow-up task: because T467
  is merged **through** this branch, the merged tree will carry both `T467-handoff.md`'s
  "CLOSED AS A CLASS" and the correction, and a reader who greps the handoff directory finds the
  false claim first. That is an obligation on the program, not a condition on T476.
* **C-T476-4 (LOW), and it is the one correction that does not meet its own standard.**
  `out/T467-HANDOFF-CORRECTIONS.md:62` reads *"Re-measured at `07aa5a86` …: exit 0, 29 checks,
  (a)–(k) = 11, ALL controls = 15."* `07aa5a86` is a real commit object with the same subject
  line as `eb57a88d` — an **orphaned pre-amend commit**, and
  `git merge-base --is-ancestor 07aa5a86 softhouse/T476-t472-repair` says **NO**. The figures
  themselves reproduce at the tip (§10), so the substance is right; the citation points at a
  tree no reader can reach and that `git gc` will remove. In a lineage whose recurring LOW is
  "a published cardinal that stopped matching the tree", a cardinal cited against an
  unreachable tree belongs in the same box.

### 9.1 C-T476-6 (LOW) — THE REGENERATED TRANSCRIPT, AND ONE CARDINAL IN IT

The committed `TRANSCRIPT-A2-11.txt` diff between `6a345e4a` and `36e01f25` is a genuine
regeneration and nothing else: a timestamp, two host paths, the five new checks, the corrected
`os.write` label — and **one moved number that is not a new check**:

```
  VACUITY CONTROL … emitted tagged quotation lines: 2   ->   8
```

`95-t481-vacuity-cardinal.py`, over the four guarded files:

| ref | as the file counts it (per **payload**) | distinct **source lines** |
|---|---|---|
| `6a345e4a` | 2 | 2 |
| `36e01f25` | **8** | **2** |

The check is `> 0` and is unaffected; the **printed cardinal** is. `_emitted_tagged` increments
once per payload and the union offers one source line as several payloads. Commit `0d15e5c7`
recognised exactly this multiplicity and deduped the reported **SITES** for `printed_untagged`
— *"the union offers one line as several payloads, so a count of payloads would read like a
count of lines and be several times larger"* — and did not apply the same dedupe here, where the
label still says **lines**. It is the same sentence, one counter over. LOW, and a one-line fix.

### 9.2 THE MERGE ITSELF

No path this branch changes has been touched on `main` since the fork point `3f4e236a`:
`git log 3f4e236a..main -- <the 23 paths>` is empty. The merge is clean; the branch is simply
behind `main`, which is why `git diff main..` looks enormous.

---

## 10. CLAIM 7 — NON-REGRESSION ON WHAT T472 CONFIRMED. **RE-DRIVEN, UNCHANGED.**

`70-t481-failclosed-nonregression.sh`, **EXIT 0**, `out/70-FAILCLOSED.txt`, all at `36e01f25`.

| arm | measured |
|---|---|
| clean tree | exit **0**, **29** checks, `(a)`–`(k)` **11**, ALL controls **15**, tracebacks **0** |
| a TRACKED non-JSON vector carrying the token | exit **1 by a value**, tracebacks **0**, **29 of 29** checks, `(a)`–`(k)` **11 of 11**, `FAILURES:` ×**1**, the named assertion ×**1** |
| **control (l)'s falsifiability** — T455's exact `int` return restored, **CLEAN** corpus | exit **1**, tracebacks **0**, 29 checks; **(k) PASSES** while **(l) and (l1) FAIL** |

Row 3 is the one that answers *"is (l) just (k) renamed"*, and it still answers **no** at a tip
whose payload predicate has been rewritten around it. The controls are counted **by their own
printed labels**, so a renamed or reordered control is a miss and not a silent pass; the arm-C
edit refuses if its anchor is absent.

**One correction to my own first run, recorded rather than presented as a finding.** I first
counted the named assertion by its sentence and got **2**; the adjudicator prints it once as a
`FAIL  ` line and once in its `FAILURES:` list. T476's ×1 is right under its own counting. My
expectation was mis-specified, not its figure.

### 10.1 THE PARSE FALLBACK — ATTACKED, NOTHING ESCAPED

`80-t481-fallback-exhaustive.py`, EXIT 0. T476 widened the fallback from `SyntaxError` to
`(SyntaxError, ValueError)` because `ast.parse` raises `ValueError` on a NUL. I asked whether
that is the complete set, over ten probes: NUL, a lone surrogate, a form feed, 200 and 2,000
nested parentheses, 2,000 nested list displays, a 5,000-deep unary chain, plain unparseable
text, a BOM, and a NUL in a comment. `ast.parse` raised `ValueError`, `SyntaxError` and
`UnicodeEncodeError`; **`UnicodeEncodeError` is a subclass of `ValueError`**, so all ten were
graded and **nothing escaped**. The instrument is calibrated in both directions (P1 exercises
the ValueError path, P8 the SyntaxError path). This is a negative about my probes, not a proof
about the exception surface, and I say so.

---

## 11. THE BAR

**Run with `bash`** (never `sh`/`zsh` — exit 3 is a wrong-interpreter refusal and says nothing
about corpus or oracle), from a scratch directory **outside** the repository, on a committed
clean tree. The probe line's **PRESENCE was tested before its value was read** (P-84): four
exit-2 paths run before the probe prints, so an absent line is not "down".

**On T476's tip `36e01f25`,** in a scratch clone outside the repository — graded on the bytes,
not on T476's transcript:

```
grep -c 'probe = '  ->  1        (PRESENCE tested BEFORE the value was read)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   T316-DEADPATH-CENSUS: corpus=1691 deadFiles=75 deadOccurrences=108 resolving=1594 indeterminate=126 prose=428
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
BAR EXIT 0
```

Identical to the figures T476 reports at `5c47377f` — 46 vectors, 7,884 cells, corpus 1,691,
deadFiles 75, deadOccurrences 108 — so commit 5's added transcript does not move the census, and
T476's `git status --porcelain -> 0 lines` calibration for that paragraph holds.

**T476's recorded EXIT 2 is handled correctly.** Its first run at the same tip was exit 2 with
the probe line **PRESENT ×1 reading `down`**, with `docker ps` and `curl` evidence of a
container mid-restart. That is a real outage, it is not a pass, and recording it rather than
discarding it is the right handling — a discarded red run is how a green one stops meaning
anything. The oracle was `Up (healthy)` and `{"status":"UP"}` before every run of mine.

**On my own committed tree:** `out/BAR-T481-OWN-TREE.txt` — see §11.1.

---

## 12. WHAT I LEAVE OPEN

* The `TRANSCRIPT-A2-11.txt` byte-level diff against a clean regeneration at the tip. My
  clean-tree runner arm measures the properties (`deviations: 0`, untagged ×0); I did not
  reproduce T472's two-line host-path diff.
* Whether `07aa5a86`'s tree differs from `eb57a88d`'s in any graded byte — I established only
  that it is not on the branch.
* `conformance.sh`'s raw-substring half of the section-4 search, and the DETECTION half of
  `(iv-a)`. Declared open by T455, T467 and T476; unchanged; not driven by me.
* The exception surface of `ast.parse` beyond my ten probes, and on Python versions other than
  the 3.9.6 on this host.
* Whether any of the six flagged files should be repaired. T476 prices them and leaves them;
  so do I.
* F-T464-4's uncorrected site in `.softhouse/handoff/T455-t448-conditions.md:300`, and T467's
  own handoff sentences. **Both need a task with a grant over `.softhouse/handoff/`** — T476
  says so and I concur; it is an obligation on the program, not a condition on this branch.
* Whether the SUPERSET CONTROL should be strengthened or its label narrowed (C-T476-1). I drove
  the defect; I did not implement either remedy, and I do not fix another task's files.

## 13. ONE PARAGRAPH FOR THE NEXT READER

T476 was sent to repair a guard that had replaced its predecessor without measuring the
replacement against it, and it repaired that properly: it kept the replaced rule wired in, so
the superset relation is a property of four lines of code rather than of anybody's fixture
list, and it priced three widenings over the whole tracked population instead of over the four
files they guard. Every one of those measurements reproduces, several to the digit, and the
regression is gone under a population eight times the size of the one T476 built. What it then
did was publish, beside that guarantee, a control that protects it against exactly one edit —
and describe the control as stricter than the relation it guards. **Empty ARM 1 and the control
is green; narrow ARM 1 to two thirds of its prefixes and the control is green; section 10 exits
0 in both cases and nothing else in the tree moves.** That is the same disease one level
further out, in the same file, and it is worth naming precisely because everything else in this
branch is a model of how to do this: the arm that carries the guarantee earns **zero** catches
on 1,992 generated cases and on every input I could construct, its only measurable effect is
five false positives, and the one check that was supposed to make it safe to keep is a
tautology in the direction that matters. **Keep the arm. Fix the control, or stop claiming it
does more than it does.**
