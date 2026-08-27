# T308 — INDEPENDENT review of T292 (R-VPA lineage, link 5)

**Reviewer:** T308, branch `softhouse/T308-review-t292`, forked at `5964ab5`.
**Under review:** T292, merged to `main` at `37aa6b8` (branch pruned; diff read from the merge,
`git diff b0f32ec 37aa6b8` — 23 files, 4818 insertions, 0 deletions).

**VERDICT: SPLIT.**

| part of the branch | verdict |
|---|---|
| the rule `check_verdict_predicate_agreement_t292.py` — the WITNESS-SET formulation, the guards, the exit protocol, the read-integrity layer | **APPROVED.** Independently measured better than all three predecessors on **both** axes and on the control. The streak is broken. |
| **THEOREM 1** ("container-blindness", with `PROOF … []`) | **REJECTED as written.** False on **3 of the 4** container operations it itself names; one of them flips **REFUSED → GREEN**, the direction its own corollary denies. |
| **THEOREM 2, clause 1** — the FORGERY FLOOR ("the only remaining way to raise coverage is to ASSERT A FACT, which no rule reading only (document, register) can distinguish from a true one") | **UPHELD.** I could not raise coverage without asserting a boolean fact under a predicate-classified key, and I agree no (document, register) rule can grade the fact's truth. |
| **THEOREM 2, clause 2** — the NAMING ("…and every witness path is printed so a forgery is NAMED") | **REJECTED. Falsified by construction (§5c, F-T308-6).** A line is printed; it does not *name* the forgery. The path is an **unescaped concatenation of attacker-chosen key strings**, so a forged document can be made to print a witness line **byte-identical** to a legitimate document's (**and with an identical `coverageDigest`**), and a key containing a newline **injects extra witness lines the document never earned**. |
| **THE "MEASURED IMPOSSIBILITY"** (guard #10) | **SPLIT.** The *scoped* half — no **container-blind** rule separates X5 from `classify-t229.json` — is **upheld**. The half that routes the work out of scope — *"separating them requires an EXTERNAL declaration … a change to `boolean-key-register.json`'s contract"* — is **REFUTED BY CONSTRUCTION**: a separator built here needs no external input at all and refuses **10/10** of T291's header fixtures while permitting **both** committed corpora. |
| **"THE ZERO IS CALIBRATED"** (`LOST REFUSALS: 0` over 325 documents) | **REJECTED.** The zero is a **tautology of the shipped rule**, not a measurement, and the calibration measures a rule that is not the shipped rule. Five mutants of **T259's own founding defect** survive T292's unmodified adversary with **0 failing legs**. |
| **F-T290-1b still open** (the precondition on `T269`) | **CONFIRMED, and WIDER than T290 stated** (§9.5, re-derived from scratch). `rep.disagreements` is **not a term in the gate** — read at source, then driven. For a document **not pinned in the acknowledgement register the erasure needs ONE file edit, not two**. **`T269` remains blocked.** |

**A numbering correction, made rather than hidden.** My first pass labelled the guard-#10
impossibility "THEOREM 2" and reviewed it twice (§3 and, by implication, the verdict row), while
the brief's THEOREM 2 is the **forgery floor**, whose second clause went **untested**. The table
above restores the brief's numbering. §3 is unchanged in substance and now reads under its own
name; §5c is the clause that was missing.

Nothing here blocks the merge that already happened: the rule **has no caller anywhere**
[VERIFIED: `git grep -n check_verdict_predicate_agreement_t292` returns hits only inside
`.softhouse/capture/t286-t268-retry/`, `.softhouse/handoff/`, and this review], so no green
anywhere in the program currently depends on it. The findings are about what the **next** link
in this lineage will read and believe.

---

## 0. THE BAR, RE-RUN BY ME

`bash .softhouse/conformance.sh`, staged tree, on this branch at the fork point.

```
EXIT 0
probe line PRESENT — "reference oracle (https://localhost:8443/…/actuator/health) probe = up"
parity vectors PASS 46   FAIL 0
cells compared 7884 graded, 93 ungraded
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared
```

[VERIFIED: `out/bar-t308-fork-point.txt`.] Matches the value the driver stated. **P-84 applied
in the stated order** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT
THE VALUE"* — the probe line's **PRESENCE** was read first, then its value; it was present, so
`up` is a reading and not an assumption.

**And again on the FULLY COMMITTED tree** — every probe, transcript and this REVIEW.md staged and
committed, since ledgerguard reads via `git ls-files` and an unstaged file is an unmeasured one
[VERIFIED: `out/bar-t308-final-committed-tree.txt`]:

```
EXIT 0
line 103  reference oracle (https://localhost:8443/…/actuator/health) probe = up   (PRESENT)
line 490  parity vectors          PASS 46   FAIL 0
line 496  cells compared          7884 graded, 93 ungraded
line 512  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle
```

**Unmoved by this branch**: `46 / 7884`, identical to the fork point. This review adds only files
under `.softhouse/reviews/T308/`.

---

## 1. SCOPE AND THE NON-NEGOTIABLES — what I checked, so silence is distinguishable from not looking

| check | result |
|---|---|
| `conformance.sh` touched? | **No.** Not in the merge's file list [VERIFIED: `git diff --stat b0f32ec 37aa6b8`]. |
| `admit.go`, `.softhouse/bin/fire-program.sh` touched? | **No.** Not in the file list. |
| frozen adapter contract / DEC-n touched? | **No.** Every changed path is under `.softhouse/capture/t286-t268-retry/` or `.softhouse/handoff/`. No Go, no vectors, no `nexus/`. |
| T259's rule byte-identical (it is both committed evidence and the PRE pin)? | **Yes.** `git hash-object .softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py` = `86f42859a1492409de9c052caf9ecbde15791212`, matching the pinned PRE blob `86f4285` [VERIFIED, run by me]. |
| register / acknowledgements edited? | **No.** Not in the file list. |
| floating point anywhere in the new code? | **None.** The only occurrences of `float` are the *refusal* (`_assert_no_float`, `isinstance(v, float) → RuleError`) and its docstrings [VERIFIED: `grep -nE "float" …_t292.py`]. `parse_float=Decimal` on the parse. This is the CLAUDE.md non-negotiable — *"Money is integer minor units. No floating-point in any monetary code path … including intermediate calculation"* — and the branch **strengthens** it: `M10` drives NaN/Infinity entering a GREEN run **as floats** on the PRE arm, and it is killed. |
| Cyrillic / three-field names | Handled deliberately: `read_bytes()` + explicit `.decode("utf-8")`, stdout reconfigured. `A6` carries `ovog` / `etsgiinNer` / `ner` and is driven under `LC_ALL=C`. Matches *"Names are three fields — ovog (clan), patronymic, given name"*. |
| any caller wired? | **None** [VERIFIED, git grep]. T292's own claim on this point is true. |

**No non-negotiable is violated by this branch.** The findings below are about the *claims*, not
about the money rules.

**One `files_hint` path in my own brief does not exist on `main`.**
`.softhouse/capture/t268-rvpa-failopen/` is absent from the working tree. It was created by
`81eb16f` on branch `softhouse/t268-rvpa-failopen`, which is **not an ancestor of `main`**
[VERIFIED: `git merge-base --is-ancestor 81eb16f main` → 1; `git branch -a --contains 81eb16f`
lists only `softhouse/t268-rvpa-failopen` and a rescue branch]. T268 was rejected by T281 and never
landed, so its capture directory exists only on that branch. I reviewed nothing in it; I used the
branch only to extract the **T268 arm blob** for §7. Stated so the empty scope entry is not read
as an unexamined one.

---

## 2. FINDING F-T308-1 — THEOREM 1 IS FALSE ON THREE OF THE FOUR OPERATIONS IT NAMES

**Severity: MEDIUM (proof defect; one instance in the unsafe direction).**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_theorem_a.py` → EXIT 1.**
**Transcript: `out/t308-theorem-a.txt`.**

The theorem, verbatim from the rule's docstring:

> Let T be any CONTAINER-ONLY rewriting of D: **wrap a value in a list; wrap it in an object under
> a fresh key**; re-nest to any depth; promote the root into a list; turn `{k: v}` into `[{k: v}]`;
> any composition of these. … Then `W(T(D),R)` and `W(D,R)` have **the same cardinality and the
> same multiset of (key, value) pairs**.
> PROOF. W's membership test reads exactly two things: (a) is this value a `bool` LEAF, and (b)
> does R classify **its key** as PREDICATE. **Neither consults container structure.** []

I applied the named operations and read the probe line on both sides:

| case | D | T(D) | verdict |
|---|---|---|---|
| **CE1** wrap a bool leaf in a list | `rc=0 GREEN witness=1` | `rc=1 REFUSED witness=0` | NOT INVARIANT |
| **CE2** wrap a bool leaf in an object under a fresh non-predicate key | `rc=0 GREEN witness=1` | `rc=1 REFUSED witness=0` | NOT INVARIANT |
| **CE3** wrap a **DESCRIPTIVE** bool leaf in an object under a fresh key matching `^P[0-9]+_` | `rc=1 REFUSED witness=0` | `rc=0 GREEN witness=1` | **NOT INVARIANT, REFUSED → GREEN** |
| CTRL promote the root into a list | `rc=0 GREEN witness=1` | `rc=0 GREEN witness=1` | invariant |

Re-derived: step (b) of the proof — *"does R classify **its key** as PREDICATE"* — **is** a
container-structural read. A bool leaf's key is the binding supplied by its immediate parent
object; a leaf inside a list has no key at all. So the sentence *"Neither consults container
structure"* is false as stated. The correct, weaker theorem is: **W is blind to container
structure ABOVE the leaf's immediate key binding.**

CE1/CE2 fail in the **fail-closed** direction and cost nothing in safety. **CE3 does not.** It is
`{"t223RulePredictedRescue": true}` → `{"t223RulePredictedRescue": {"P9_z": true}}`: a pure
container insertion, verbatim the theorem's own operation *"wrap it in an object under a fresh
key"*, which manufactures a witness and flips the document from REFUSED to GREEN. It is rescued
only by the theorem's **second** hypothesis (*"adds or removes no registered predicate key"*) —
i.e. **the theorem's own operation list is not a subset of its own hypothesis class.**

**This is not a security hole.** CE3 lands inside the forgery floor T292 declares (*"the ONLY way
to raise coverage is to … ASSERT A FACT"*) and the witness path is printed, so the forgery is
NAMED. And T292's **adversary is honest about the same restriction** — it states outright that
wrappers are inserted only at positions already holding a dict or a list, because *"wrapping a
SCALAR would detach a leaf from its object … asserting invariance over it would be asserting
something false"*, and its object wrappers use `_w<n>` / `_h<n>` keys.

**So the defect is exactly this: the ADVERSARY's scope is right and the RULE's docstring theorem
is not scoped to match it.** The docstring is what the sixth link will read, and it currently
says `PROOF … []` under a statement three of its own operations refute.

**Required (≤10 lines, mechanical):** restate the theorem's operation set as *"inserted only at
positions already holding a dict or a list, with wrapper keys that are neither registered nor
`^P[0-9]+_`-shaped"* — the adversary's wording — and change *"Neither consults container
structure"* to *"Neither consults container structure above the leaf's own key binding."*

---

### 2b. THE SIX SHAPES NOBODY HAD TRIED — DRIVEN, AND THEY DO **NOT** BREAK IT

**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_theorem1_novel_shapes.py` → EXIT 0.**
**Transcript: `out/t308-theorem1-novel-shapes.txt`.** The verdict column carries the finding, not
the exit code.

Pass 1 attacked Theorem 1 with four operations. The brief named six more, plus two T291 attacks to
re-run. All ten driven against `BASE = {"cells":[{"P1_principalAmortizesToZero":true,
"verdict":"AS PREDICTED"}]}` (rc=0, witness=1, digest `8c87330d77282c8d`):

| shape | operation | rc | witness | verdict |
|---|---|---|---|---|
| S1 | a key that is itself a container | — | — | **NOT EXPRESSIBLE** |
| S2 | a bool leaf under a non-string key | — | — | **NOT EXPRESSIBLE** |
| S2b | the string `"true"` used as an object KEY | 1 | 1 | INVARIANT |
| S3 | the whole document is the bare literal `true` | 1 | 0 | not invariant — **and fail-closed** |
| S4 | 12 levels of nesting, each adding an empty `{}` and `[]` | 0 | 1 | **INVARIANT** |
| S5 | the same key name reused at three DIFFERENT depths | 0 | 1 | **INVARIANT** |
| S5b | CONTROL — the same PREDICATE key at two depths | 0 | **2** | not invariant (it *adds an assertion*; proves the counter is live) |
| S6 | anchors / aliases | — | — | **NOT EXPRESSIBLE** |
| S7 | whole document promoted into a top-level ARRAY | 0 | 1 | **INVARIANT** |
| S8 | list-of-lists, depth 4 | 0 | 1 | **INVARIANT** |

**"Not expressible" is a statement about the search, not a shrug.**
* **S1/S2** — RFC 8259: a JSON member name **must** be a string. `json.loads` cannot produce a
  non-string key, so the shape does not exist in this loader's input language. The nearest
  expressible thing is S2b, driven.
* **S6** — the loader is `json.loads(text, parse_float=Decimal, parse_constant=_refuse_constant,
  object_pairs_hook=_no_duplicate_keys)` [VERIFIED: `check_verdict_predicate_agreement_t292.py:220-222`,
  read by me] and there is **no `yaml` import in the file** [VERIFIED: grep]. Anchors are not
  admitted, so they cannot move coverage.

**This is a result FOR T292, and I record it as one.** Of the five genuinely container-only shapes
(S2b, S4, S5, S7, S8), **all five are invariant** — including 12 levels of empty-container nesting
and the top-level array that killed earlier links. The two that moved are not container-only
rewritings: S3 destroys the document (and **refuses**, the safe direction), and S5b is my own
positive control, which *adds an assertion* and must move.

**So F-T308-1 does not widen.** After ten shapes, the *only* counterexample class remains the one
§2 names: **the leaf's immediate key binding**. Theorem 1 with that one correction applied appears
to be true, and I attacked it harder than its author did.

---

## 3. FINDING F-T308-2 — "MEASURED IMPOSSIBILITY" IS PROVED ABOUT THE WRONG RULE CLASS; A SEPARATOR EXISTS

**Severity: MEDIUM (claim overreach — the strongest word in the branch is the least supported).**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_theorem_b_counterrule.py` → EXIT 0.**
**Transcript: `out/t308-theorem-b.txt`.**

**Read the claim in two halves, because only one of them is wrong.**

* **Half A, SCOPED — upheld.** *"no container-blind predicate separates a header from a
  legitimately un-graded record"* (handoff §5a). **True, and I do not dispute it.** Under a
  container-blind reading X5's header and `classify-t229.json`'s `RESCUED_BY_SITE3` rows are the
  same object. T292 measured this properly with `negative_result_header_affirmations.py`.
* **Half B, UNSCOPED — REFUTED BY CONSTRUCTION.** *"Separating them requires an **external
  declaration** of which containers hold graded records — i.e. a change to
  `boolean-key-register.json`'s contract, which is **committed evidence outside T292's
  `files_hint`**. Specified in §7, not done here."* (handoff §5a, verbatim.)

Half B is what routes the work to a later task and out of scope. **It is false.** I did not argue
with it; I **built the separator**, using nothing but the document itself.

**G10-SIBLING.** For every affirmative word (as a value **or** as a mapping key) whose immediately
owning object contributed no witness: let `C` be the container that directly holds that owning
object. **PERMIT** iff `C` directly holds at least one object that **did** contribute a witness;
**REFUSE** otherwise. No register change. No external declaration. No new input. ~20 lines.

Measured over T291's ten committed fixtures, both committed corpora, and four controls:

| document | T292's shipped CENSUS | G10-SIBLING |
|---|---|---|
| `T291/H1`, `N6`, `X1`, `X2`, `X3`, `X4`, **`X5`**, **`X5b`**, `X7`, `X8` | 1 each | **1 each — REFUSE** |
| `A7-affirmation-as-a-mapping-key` | 1 | **1 — REFUSE** |
| **`REAL/classify-t229`** (committed, correct) | **3** | **0 — PERMIT** |
| `REAL/classify-t219` | 0 | 0 — PERMIT |
| `A9-CONTROL-genuine-green`, `A10-CONTROL-unacknowledged-disagreement` | 0 | 0 — PERMIT |

Graded against guard #10's own stated ambition: **T292's census promoted to a refusal → 1
violation** (it turns `classify-t229.json` red, exactly as T292 says). **G10-SIBLING → 0
violations.**

**What this does and does not overturn.** Half A stands. **Half B does not:** G10-SIBLING consults
no external declaration, reads no file the rule does not already read, and requires no change to
`boolean-key-register.json` — so the statement that separation *"requires an external declaration
… i.e. a change to `boolean-key-register.json`'s contract"* is refuted by a running program. And
because Half B is the sentence that moves the work outside `files_hint` and defers it to §7/T269,
**the deferral is unsupported by the reason given for it.**

The gap between the two halves is a **category error**, not a proof error. Half A restricts to
**container-blind** rules. But **guard #10 is a DETECTION guard**, and the central thesis of this
very branch is that detection is entitled to be container-aware — `walk_objects` is total and the
docstring calls it *"the DETECTION side, generous, as it should be."* The impossibility was proved
about a rule class guard #10 never needed to belong to. The honest statement is:

> *No container-blind rule can separate them, and I chose not to make guard #10 container-aware.*

That is a **design decision**, and T292 did not record it as one. It recorded it as a theorem and
routed the consequence out of scope.

**I am not asking for G10-SIBLING to ship.** I measured its limit in the same run and printed it:
the row `EVASION-header-moved-INSIDE-the-records-list` — `{"cells":[{"verdict":"AS PREDICTED"},
{"P2_x":false,"verdict":"REFUTED"}]}` — scores **census 1, sibling 0**. Moving the header into the
records container defeats it, exactly as **P-91** predicts: *"a guard phrased as a STRUCTURAL
PATTERN over the shape of its input can always be re-nested one level out, so enumerating shapes
that COUNT and refusing the unmatched is a losing method no matter how carefully each shape is
chosen."* The finding is that **"impossible" is the wrong word for something a 20-line predicate
does on this corpus.**

### 3b. Sub-finding (LOW): the rule's docstring and its own handoff disagree on the number, 5 vs 3

* **rule docstring:** *"Measured, by `probe/census_real_corpus.py`: classify-t229.json contains
  **5** such affirmations (3 cells + 2 calibration) and classify-t219.json contains **0**."*
* **handoff §5a:** *"Measured by `probe/census_real_corpus.py`: `classify-t229.json` carries **3**
  such affirmations under the committed register, `classify-t219.json` carries **0**."*
* **the shipped counter, run by me:** `T259-VPA: GREEN files=1 … headerAffirmations=3 …`

**The handoff is right and the docstring is wrong.** `census_real_corpus.py` counts a witness only
for keys matching `^P[0-9]+_`; it ignores the register's three PREDICATE entries `inputsIdentical`
/ `observedIdentical` / `threwIdentical`, so it treats the two `calibration` rows as ungraded and
prints `Q3 free-floating affirmations : 5`. Under the rule's **own** witness definition those rows
grade three facts each and are not header affirmations. The impossibility argument survives either
way (three committed rows still go red), but the docstring quotes a number produced by a weaker
predicate than the one that ships — the same species of mismatch this whole lineage is about, at
one-tenth the stakes.

---

## 4. FINDING F-T308-3 — `LOST REFUSALS: 0` IS A TAUTOLOGY OF THE SHIPPED RULE, AND THE CALIBRATION MEASURES A DIFFERENT RULE

**Severity: HIGH (the headline number of the branch).**
**Reproduction: read the two lines below; corroborated by T292's own committed transcripts and by
`out/t308-survivor-mutants-pass2-stale-label.txt`.**

The adversary's lost-refusal test is `PRE refuses ∧ NEW greens ∧ NEW witness < 1`
[VERIFIED: `probe/adversary_t292.py`, the `PROP-C` block —
`if pre_refuses and base_new["rc"] == 0: if int(base_new["witness"] or 0) < 1:
lost_refusals.append(...) else: widenings.append(...)`].

The shipped rule's exit path is
[VERIFIED: `check_verdict_predicate_agreement_t292.py:541,548,595`]:

```python
541  refused = bool(rep.unacknowledged or rep.unclassified_keys or rep.unclassified_verdicts
                    or rep.void_acks or rep.mute_refutations or nil)
548  if not refused and (len(rep.witness) < 1 or rep.nil_files or rep.files < 1):
         ... return 2
595  return 1 if refused else 0
```

**Therefore `rc == 0 ⟹ len(witness) ≥ 1`, unconditionally, for every possible input.** The
conjunction `rc == 0 ∧ witness < 1` is unsatisfiable. **`lost_refusals` cannot be non-empty for
the shipped rule, for any document, ever.** "325 documents through both arms, ZERO lost refusals"
is the cardinality of a provably empty set. It is not evidence about those 325 documents.

**The calibration does not rescue it — it confirms it.** `prove_adversary_sees_a_lost_refusal.py`
had to plant **M1 *and* M8**, and its own docstring says why: *"`M1` … IS killed — but it is
killed by the post-condition … so `rc == 0` never happens and the lost-refusal counter still reads
**0**. The kill is real and the counter is still unexercised."* M8 is the deletion of the
post-condition. So the calibration demonstrates the counter can count **on a rule that has no
post-condition** — i.e. on T259/T268/T286, not on T292. The merge message's *"the ZERO IS
CALIBRATED, which is the part that matters"* does not follow from it.

**Corroborated by T292's own committed evidence.** In `out/mutants-t292.txt`, **all eight killed
mutants report `LOST REFUSALS: 0`**, including:

```
KILLED   M3-nil-coverage-gated-globally-not-per-file  …  LOST REFUSALS: 0
           FAILED  [PROP-D] BATCH evidence-first refuses (T268 F-1) -- rc=0 nilFiles=0
```

**M3 *is* T268's F-1** — the second fail-open in this lineage and the exact defect the
lost-refusal criterion was invented by T281 to catch. It was caught by a **hand-written PROP-D
batch leg**, not by the criterion. Under T292's redefinition, **T281's rejection of T268 would not
reproduce from the criterion T281 used.**

**Where the 48 non-empty cases went.** The committed
`out/t292-adversary-legs.json` records `lost_refusals: 0` and **`widenings: 48`** [VERIFIED, read
by me], and widenings do **not** fail the run (`rc = 1 if (L.failed or L.skipped or
lost_refusals) else 0` — `adversary_t292.py:605`). The distinct fixtures in that bucket, counted by
me, are `A11-FLOOR` (10), `A6-cyrillic` (7), `A7-affirmation-as-a-mapping-key` (9),
`A9-CONTROL-genuine-green` (9), and — the ones that matter — **`T291/X5` (3) and `T291/X5b`
(10)** — the fixtures that killed T286. Every case where PRE refused and NEW greened was routed to
the non-failing bucket by a test the post-condition makes unconditional.

**What IS load-bearing and should be quoted instead:** `PROP-B` (no vacuous green, asserted on
every document) and the post-condition itself. Those are real and they pass. The zero is not a
second, independent confirmation of them; it is the same fact restated as a count.

---

## 5. FINDING F-T308-4 — FIVE MUTANTS OF T259'S FOUNDING DEFECT SURVIVE T292'S OWN ADVERSARY, WITH ZERO FAILING LEGS

**Severity: HIGH (this is the brief's question answered: the counter is sensitive to the planted
defect and blind to a different one).**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_survivor_mutants.py --seeds 3`.**
**Transcripts of record: `out/t308-survivor-mutants-pass1.txt` and
`out/t308-survivor-mutants-pass2-stale-label.txt`. Both carry the identical finding — five
survivors, zero failing legs. Each also carries a defect of MY OWN, named in its filename and
described in §7; the probe now on disk has both fixed, and a pass 3 was killed unfinished when the
host went to load 24 with eight workers live. `out/t308-survivor-mutants.txt` was therefore
DELETED rather than committed at zero bytes: a zero-byte transcript in an evidence directory is
worse than an absent one.**

T292's eight kill targets attack COVERAGE (M1/M2/M3), READ INTEGRITY (M4/M5/M10/M6), the EXIT
PROTOCOL (M7) and DETECTION BREADTH (M9). **Not one attacks the GATE** — the disjunction in `main`
that turns counted refusals into exit 1. So I planted the lineage's *founding* defect there
instead: **the refusal is printed in the body and the exit code stays GREEN** (T259's defect, per
P-91: *"`T259` shipped a rule that printed `REFUSED NIL COVERAGE` in its body and **exited
GREEN**"*), once at each of five guards, and ran **T292's unmodified adversary** against each.

| mutant | disposition | LOST REFUSALS | failing legs | reproduction: SHIPPED → MUTANT |
|---|---|---|---|---|
| `N1` unacknowledged disagreement printed but not COUNTED (G5) | **SURVIVED** | 0 | **0** | `rc=1` → **`rc=0`** |
| `N2` mute refutation printed but not COUNTED (G6) | **SURVIVED** | 0 | **0** | `rc=1` → **`rc=0`, body still prints REFUSED** |
| `N3` void acknowledgement printed but not COUNTED (G4) | **SURVIVED** | 0 | **0** | not reproduced (a void ack needs the acknowledged path *and* different bytes; I would not edit committed evidence to get it) |
| `N4` unclassified verdict word printed but not COUNTED (G1) | **SURVIVED** | 0 | **0** | `rc=1` → **`rc=0`, body still prints REFUSED** |
| `N5` unclassified boolean key printed but not COUNTED (G2) | **SURVIVED** | 0 | **0** | `rc=1` → **`rc=0`, body still prints REFUSED** |
| `N6` CONTROL — drop `nil` from the same disjunction | KILLED | 0 | 11 | `rc=1` → `rc=2` (the post-condition catches it) |

**Three of the five print `REFUSED` in the body and exit `0`.** That is not an analogy to T259's
founding defect; it is the same sentence — P-91: *"`T259` shipped a rule that printed
`REFUSED NIL COVERAGE` in its body and **exited GREEN**."*

`N6` is the positive control and it dies, so the harness is not simply passing everything: `nil`
is the one term in that disjunction the **post-condition independently re-checks**, which is
precisely why it is the one term the adversary can see.

`N1` driven on `A10-CONTROL-genuine-unacknowledged-disagreement` — a fixture **already in T292's
own corpus**:

```
SHIPPED : rc=1  T259-VPA: REFUSED … disagreements=1 acknowledged=0 unacknowledged=1 … witness=1
N1      : rc=0  T259-VPA: GREEN   … disagreements=1 acknowledged=0 unacknowledged=0 … witness=1
```

The mutant prints `disagreements=1, acknowledged=0, unacknowledged=0` **and exits GREEN** — the
probe line contradicts itself on its own face — while the body above it still prints
`*** DISAGREEMENT [UNACKNOWLEDGED] … NO ACKNOWLEDGEMENT. This row asserts its prediction held
while recording that one of its own predicates did not … do not summarise past it.` (For `N1` the
printed evidence is that block rather than the literal word `REFUSED`, which is why the table's
"body still prints REFUSED" column marks `N2`/`N4`/`N5` and not `N1`.) That is T259's founding
defect, reproduced inside the instrument built to prove it cannot recur, and T292's adversary
passes it **82/0/0**.

**Why every property misses it.** PROP-A is an *invariance* over container rewritings — the mutant
is perfectly invariant (`rc=0` everywhere), so PROP-A passes. PROP-B requires `rc==0 ⟹ witness ≥
1` — the witness is 1, so PROP-B passes. PROP-C requires `witness < 1` — see §4, unsatisfiable.
PROP-D **does** carry expected-REFUSE legs — but **all eight of them are degenerate empty
documents** (`null`, `[]`, `{}`, `7`, `"x"`, `true`, `[1,2,3]`, `[null,null]` →
`NEG degenerate … -> 1, probe PRESENT`), and **every one of them refuses through `nil`**, the
single term in the `refused` disjunction that the post-condition independently re-checks. That is
the whole explanation of the table above: `N6` drops `nil` and dies on eleven of those legs;
`N1`…`N5` drop the other five terms, for which **no leg anywhere asserts a verdict**. `A10` — a
genuine unacknowledged disagreement, already in T292's corpus — appears only in the invariance and
vacuity populations, never with an expected `rc`.

**The structural gap: T292's adversary has no expected-verdict oracle.** It checks *shape
invariance*, *non-vacuity*, *non-regression against PRE*, and *exit-protocol separation* — four
properties, none of which is *"this document must REFUSE, and here is why."* Every one of them is
satisfied by a rule that refuses nothing except empty documents.

**Required to close:** an `EXPECT` column on the fixture corpus (`A1`…`A13`, the T291 fixtures,
the two real corpora) asserting `rc` per fixture, and at least one mutant in `mutants_t292.py` that
drops a term from the `refused` disjunction other than `nil`. This is not a micro-fix; it is a
task.

---

## 5b. FINDING F-T308-5 — THE AUTO-CLASSIFIER IS WIDER THAN THE PATTERN THE RULE REFUSES TO GUESS AT

**Severity: LOW. Inherited from T259, not introduced by T292 — reported because T292 is the file
that will be installed.**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_unicode_digit_predicate.py`.**
**Transcript: `out/t308-unicode-digit-predicate.txt`.**

`load_registers` refuses to run unless the register declares exactly
`"autoPredicatePattern": "^P[0-9]+_"` — *"refusing to guess"*. `key_class` then implements that
pattern as `head[1:].isdigit()`. **`str.isdigit()` is true for Unicode digits `[0-9]` does not
match.** Measured:

| key | `re.match("^P[0-9]+_")` | `head[1:].isdigit()` | rule's verdict |
|---|---|---|---|
| `P2_x` | True | True | GREEN, witness=1 |
| `P²_x` (superscript two) | **False** | **True** | **GREEN, witness=1, unclassifiedKeys=0** |
| `P٢_x` (Arabic-Indic two) | **False** | **True** | **GREEN, witness=1, unclassifiedKeys=0** |
| `zz_x` (control) | False | False | REFUSED, **unclassifiedKeys=1** |

The control fires, so the probe is not vacuous. **G2 — the guard T259 exists for, whose register
says *"Everything else is UNCLASSIFIED until written down here, and UNCLASSIFIED is a REFUSAL, not
a pass"* — does not fire on a key nobody classified**, and the document buys coverage from it.
The rule *verifies the pattern string at startup and then does not implement it*.

Severity is LOW because the smuggled key still has to assert a boolean fact, which is the declared
forgery floor, and the witness path is printed. It is inherited: the pinned T259 blob `86f4285`
carries the identical `head[1:].isdigit()` at its line 151 [VERIFIED: `git cat-file blob 86f4285`].
**Fix is one line:** `re.match(reg["autoPredicatePattern"], key)`.

---

## 5c. FINDING F-T308-6 — "EVERY WITNESS PATH IS PRINTED SO A FORGERY IS **NAMED**" IS FALSE. THE NAME IS NOT A NAME.

**Severity: MEDIUM — and it is load-bearing on THIS REVIEW, because my own first pass used the
naming clause twice to downgrade a severity without ever testing it.**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_witness_path_forgery.py` → EXIT 0.**
**Transcript: `out/t308-witness-path-forgery.txt`.**

T292's floor has two clauses. Clause 1 — *coverage can only be raised by ASSERTING A FACT, and no
rule reading only (document, register) can tell a forged fact from a true one* — **I uphold it**;
I could not raise the witness count any other way, and the truth of an asserted boolean is simply
not in the rule's input. Clause 2 is the mitigation that makes clause 1 tolerable:

> *…and every witness path is printed, so a forgery is **NAMED**.*

**A floor that names forgeries is only as good as the naming.** The naming, read at source
[VERIFIED, all five lines quoted from `check_verdict_predicate_agreement_t292.py`]:

```python
257          yield from walk_objects(x, path + "." + k)      # naive concatenation
260          yield from walk_objects(x, path + "[%d]" % i)
421      rep.witness.append(("%s.%s" % (opath, k), k, v))
562  for wpath, wkey, wval in rep.witness:
563      print("      %s = %s" % (wpath, "true" if wval else "false"))
```

The printed path is a **string concatenated from untrusted key names**, emitted with **no
escaping, no quoting and no length cap**. Two attacks follow directly, and both land.

**A1 — COLLISION. Two different documents, one byte-identical name.**

| document | printed witness line | `coverageDigest` | rc |
|---|---|---|---|
| CTRL `{"cells": [{"P1_principalAmortizesToZero": true, "verdict": "AS PREDICTED"}]}` | `$.cells[0].P1_principalAmortizesToZero = true` | `8c87330d77282c8d` | 0 |
| **A1** `{"cells[0]": {"P1_principalAmortizesToZero": true, "verdict": "AS PREDICTED"}}` | `$.cells[0].P1_principalAmortizesToZero = true` | **`8c87330d77282c8d`** | 0 |

A top-level key **literally named `cells[0]`** renders as the path of an object at index 0 of a
list named `cells`. The documents differ in bytes; **the naming does not differ at all — and
neither does the digest T292 offers as the pinnable fingerprint of what was graded.** So the
forgery is printed *under a legitimate document's name*, and the one field that could have
separated them collides too.

**A2 — INJECTION. The forger chooses what the extra lines say.**
A container key containing a newline splits one witness line into several:

```
  WITNESS -- predicate reads : 1   (THE coverage metric)
      $.z
      $.cells[0].P7_reconciledAgainstOracle = true      <- FABRICATED. Never asserted, never graded.
      x.P1_principalAmortizesToZero = true
```

**Three printed witness lines against a reported witness count of 1.** The middle line names a
predicate `P7_reconciledAgainstOracle` the document never asserted and the register never
classified. A reader auditing the naming — which is precisely the reader clause 2 promises to
protect — reads a graded fact that does not exist.

**What this does and does not mean.** It is **not** a defect in any money path and it is **not**
exploitable today: the rule still **has no caller anywhere** [VERIFIED, git grep, §0]. What it
does is remove the mitigation. Clause 1 says forged coverage is *unpreventable*; clause 2 said it
is *at least visible*. It is not reliably visible.

**Two of my own severities move because of it, and I restate them rather than leave them
standing:**

* **§2 CE3** — I wrote *"This is not a security hole … the witness path is printed, so the forgery
  is NAMED."* The first half stands (no caller; fail-closed elsewhere); **the reason I gave for it
  does not.** CE3's manufactured witness is nameable-over, like any other.
* **§5b F-T308-5** — I wrote *"Severity is LOW because the smuggled key still has to assert a
  boolean fact, which is the declared forgery floor, and the witness path is printed."* The
  homoglyph key `P²_x` is **exactly** an attacker-chosen key string, so it reaches the printer
  through the same unescaped path. **F-T308-5 stays LOW on impact (no caller) but its stated
  justification is withdrawn.**

**Fix (mechanical, ≤10 lines):** render each path segment through `json.dumps` rather than raw
concatenation, so `cells[0]` prints as `"cells[0]"` and a newline prints as `\n`. Three lines
(257, 260, 421). Both A1 and A2 become visible immediately. **I did not apply it** — the rule is
T292's committed evidence and outside my edit scope.

---

## 6. THE PARTITION QUESTION — IS THE SEPARATION STRUCTURAL, OR TWO NAMES IN ONE FUNCTION?

**Verdict: STRUCTURAL, for the quantity that gates. Verified by reading and by measurement.**

The two purposes are **not** in two functions — the witness is appended inside the `walk_objects`
loop of `check_file`. So the "separation" is not a separation of *code*. But that is not what the
trade required. The trade required a **shared tunable**: `walk_rows` was **partial**, and its
partiality was a single dial that detection wanted turned up and coverage wanted turned down.
After T292:

* **the shared component is `walk_objects`, and it is TOTAL** — every dict at every depth through
  every container. A total traversal **has no dial**. Widening it is impossible; narrowing it is
  `M9`, which is killed. So the shared component cannot carry a trade.
* **the gating quantity is `len(rep.witness)`**, whose membership test reads `isinstance(v, bool)`
  and `key_class(reg, k)`, and nothing else. `opath` enters only the *printed* path string.
* **`coverage_digest` deliberately excludes the path** (`keyed on (key, value) and NOT on path`),
  so the digest — the thing PROP-A compares — cannot be moved by containers either. Measured:
  the CTRL row of `out/t308-theorem-a.txt` shows an identical digest across a root-promotion.
* **the container-keyed set `witnessed_objects` exists, but it feeds ONLY the census**, which
  gates nothing.

The one residual coupling is the one F-T308-1 names: the leaf's **immediate key binding** is
container structure, and CE1/CE2/CE3 move it. It is a genuine coupling, it is one level deep
rather than unbounded, and it is not a *dial* — you cannot tune it to trade detection against
coverage.

**The word "bracket" does not appear in the coverage predicate.** Checked, and stated precisely,
because my own first draft of this paragraph over-claimed: `grep -in bracket` finds the word **four
times in the file** — all four in the docstring prose (lines 22, 56, 57, 58), none in any executable
line and none in the witness membership test. T292's claim is scoped to the *predicate* and is
exactly true; "it appears nowhere in the file" would have been false, and I nearly wrote it.

---

## 7. DID IT BREAK THE STREAK? — YES. MEASURED ON BOTH AXES, FOUR ARMS, PINNED BLOBS

**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_both_axes.py`.**
**Transcript: `out/t308-both-axes.txt`.**

Arms unpacked from pinned blobs and run **inside the repo** (all four resolve `repo_root()` by
walking up from their own location):

```
ARM T259  86f42859a1492409de9c052caf9ecbde15791212   (the PRE pin)
ARM T268  0607ecdb943e84c0ad2ae9f16cd79fc702847c3d   (81eb16f:…/check_verdict_predicate_agreement.py)
ARM T286  4f844ed2409bbcde3add574a1160601f4e55b06d   (73483f5:…/check_verdict_predicate_agreement.py)
ARM T292  f6ee6d2dca179992c53ecf8b2c76a194a34678ef   (shipped)
```

| arm | **STRICTNESS** (58 documents that grade nothing → must REFUSE) | **GENEROSITY** (17 real disagreements, re-nested → must REFUSE) | CONTROL (4 → must GREEN) |
|---|---|---|---|
| T259 | 48/58 | 15/17 | 2/4 |
| T268 | **12/58** | 16/17 | 3/4 |
| T286 | 37/58 | 16/17 | 3/4 |
| **T292** | **56/58** | **17/17** | **3/4** |

`vs T259 +8 / +2 / +1 · vs T268 +44 / +1 / 0 · vs T286 +19 / +1 / 0`.

*Population caveat, stated rather than hidden:* the strictness population is 10 T291 fixtures +
4 seeds × 3 nesting modes × 4 depths = 58, and the three modes coincide at depth 0, so 8 of the 58
are duplicates of another entry. That inflates the denominator by 8 and changes no comparison —
**all four arms are graded on the byte-identical population**, so the deltas stand.

**T292 is at or above every predecessor on both axes and on the control. The trade is not visible
on these populations.** The table also reproduces the lineage's history independently: T268 traded
44 points of strictness for 1 point of generosity, and T286 bought 25 of them back — which is
exactly the diagnosis T292 wrote down, now measured by a third party rather than argued.

T292's only two strictness misses are `T291/X5` and `T291/X5b` — precisely guard #10, disclosed in
the branch, and precisely what G10-SIBLING closes (§3). Its one control miss,
`REAL/classify-t219` (`rc=1`, 4 unacknowledged disagreements), is **pre-existing and not T292's**:
the T259 arm refuses it too. Filed as an observation, not a finding.

**A defect in MY OWN instrument, recorded rather than tidied away.** The first draft of
`t308_both_axes.py` re-serialised the committed corpora into a temp path. That changes both the
relative path and the sha256, so every acknowledgement block stopped applying and **all four arms
"refused committed correct evidence"** — an artefact that would have been reported as a finding
had I read the number instead of the direction. Draft-1 transcript preserved at
`out/t308-both-axes-DRAFT1-instrument-defect.txt`; the corpora are now graded **in place**.
Likewise, pass 1 of `t308_survivor_mutants.py` **exited 0 while reporting five survivors**, because
the author had written his prediction into the gate — the lineage's founding shape, in the
instrument written to find the lineage's founding shape. Preserved at
`out/t308-survivor-mutants-pass1.txt`; the gate is now "non-zero if ANY kill target survived", and
pass 2 duly exited **1**. Pass 2 then printed a per-guard reproduction number under the label
**`A10 driven through the mutant`** — a cardinal beside the wrong name, which is `P-86`'s exact
species. Preserved at `out/t308-survivor-mutants-pass2-stale-label.txt`; the label now names the
document actually driven. **Three instrument defects in three probes, all mine, all found by
reading an output that made no sense rather than by re-reading code** — which is the same way T292
found its own five, and is the most transferable thing in either report.

---

### 7b. T292's headline invariance claim REPRODUCES, and I extended it

I re-ran T292's **unmodified** adversary myself, at the default `--seeds 40` rather than the `12`
its committed transcript used (`out/adversary-t292.txt` line 5: *"rng seed 292, **12** container
mutations per seed doc, up to depth 6"* → 25 bases + 25×12 = **325 documents**, exactly as
claimed — the figure is honest):

```
T292 ADVERSARY: 82 passed, 0 failed, 0 SKIPPED   over 1025 documents
LOST REFUSALS: 0
EXIT 0
```

[VERIFIED: `out/t308-adversary-rerun.txt`, run by me, `--seeds 40`, 25 bases + 25×40 = 1025.]
**PROP-A container invariance holds over three times as many generated rewritings as T292
measured, with no failing leg and nothing skipped.** The `LOST REFUSALS: 0` on that line is the
tautology of §4 and carries no information; the `82 passed, 0 failed, **0 SKIPPED**` does, and it
is the number T286 could not honestly quote (P-91's corollary: *"the battery returns exit 0 with
legs SKIPPED … A test rig is inside the trust boundary of the thing it grades; check that it
cannot pass vacuously before quoting its counts"*). T292's rig **cannot** pass vacuously — `rc = 1
if (L.failed or L.skipped or lost_refusals)` — and I confirmed the skip count is zero on my own
run, not on T292's.

---

## 8. WHAT I CHECKED AND FOUND CLEAN

So that silence is distinguishable from not looking:

* Every `[VERIFIED]` claim in the T292 handoff I sampled traced to real source: the PRE pin blob,
  the absence of a caller, `conformance.sh` untouched, the register untouched, `M5`'s
  reclassification (I re-read the three-arm reasoning and it is correct — `_assert_no_float` is
  load-bearing, `parse_constant` is belt-and-braces).
* **Guards fire and are non-vacuous.** G1/G2/G5/G6 all produce a REFUSED exit on documents I
  constructed; G3 (nil coverage) is per-file and I confirmed the per-file gating is real
  (`witness_at_entry`, not a global `if not rep.witness`); G7 read-integrity refuses duplicate
  keys, NaN/Infinity and non-UTF-8 with **exit 2 and no probe line**, which is the correct
  separation.
* **The P-numbers T292 cites are the right ones, checked against `patterns.md` and not inherited**
  — which matters, because **P-86** is *"THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES
  THE ROT"*, and its lesson is that *"every prompt wrote out the **full rule text** beside the id
  rather than the id alone… The number was decoration; the sentence carried the instruction."*
  - **P-84** — T292 writes *"P-84: test the line's PRESENCE first, then its VALUE"*; `patterns.md`
    P-84 is *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."*
    Correct id, faithful text.
  - **P-91** — T292 quotes it verbatim in its opening docstring. Correct.
  - **P-81** — T292 writes *"(P-81: an error is not a measured negative)"*. That sentence is
    **T292's gloss, not P-81's headline**; `patterns.md` P-81 is *"THE FAIL-OPEN GUARD CAUGHT
    THREE WORKERS' OWN INSTRUMENTS IN ONE FIRE…"*, whose worked example is *"**`git grep` exits 1
    on NO MATCH and >1 on ERROR**, so a bad pathspec printed the same reassuring absence as a
    genuine no-match"* — i.e. the gloss is a faithful restatement of the rule even though it is
    not the sentence. No misdirection; noted only because P-86 exists.
* **The exit protocol is right.** `--help` returns 2 with no probe line; `add_help=False` plus the
  `SystemExit` catch covers both argparse exits. `PYTHONOPTIMIZE=2` still refuses, because the
  post-condition is an `if`, not an `assert`.
* **Read-once is real:** one `read_bytes()`, sha of that buffer, parse of that buffer. The
  acknowledgement pin covers the bytes that were graded.
* **No ratified DEC-n changed**; no vector, no Go file, no `nexus/` path in the diff.
* **The branch's self-recorded defects are honest and complete as far as I could check** — I found
  no defect T292 concealed. Every finding above is about a claim T292 **made**, not about a defect
  it hid. Handoff §5c is the strongest part of the branch: it carries explicit `[UNVERIFIED]` on
  *"the generator's family is the whole family"*, `[NOT MEASURED]` on the `/dev/full` ENOSPC path,
  and `[UNVERIFIED]` on TOCTOU — three places a weaker handoff would have written a plausible
  value. §5c's own caveat *"coverage is invariant under **container** rewriting, proved; it is not
  claimed invariant under arbitrary rewriting"* is very nearly the correction F-T308-1 asks for; it
  is in the handoff and **not** in the rule's docstring, which is where the theorem lives.
* **The scope claims in handoff §6 are all true, re-checked by me and not inherited:**
  `conformance.sh` unchanged, T259's file byte-identical at blob `86f42859…`, register and
  acknowledgements unmodified, no Go, no vector, no pin moved. The §6 note that `run.sh` originally
  diffed against a **moving `main`** instead of the fork point — and thereby accused its own author
  of a scope violation — is a real instrument defect, correctly diagnosed and correctly fixed to
  `git merge-base HEAD main`.

---

## 9. WHAT THE NEXT LINK MUST NOT INHERIT

1. `LOST REFUSALS: 0` **must not be quoted again as evidence.** It is `|∅|`. (§4)
2. Guard #10 is **not impossible**; it is **not container-aware**, by a choice nobody wrote down.
   (§3)
3. Theorem 1's operation list must be narrowed to what the adversary actually generates. (§2)
4. **The adversary needs an expected-verdict oracle.** Four properties that are all satisfied by a
   rule that refuses nothing is how five guards' worth of founding defect walked through. (§5)
5. **F-T290-1b remains open under this rule — and it is WIDER than T290 stated.** See §9.5,
   which replaces pass 1's admission that it had not re-derived the floor. It has now been
   re-derived from scratch.
6. **The witness path does not name a forgery.** Do not reuse "the path is printed" as a
   mitigation for anything until it is escaped. (§5c)

---

## 9.5. F-T290-1b RE-DERIVED FROM SCRATCH — OPEN, WIDER THAN T290 SAID, AND `T269` STAYS BLOCKED

**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_f290_1b_independent.py` → EXIT 0.**
**Transcript: `out/t308-f290-1b-independent.txt`.**

Pass 1 accepted T292's own driver and wrote *"I did not independently re-derive T290's floor."*
That admission is now discharged. I did not re-run T292's script as evidence; I **read the gate**
and then **built my own fixtures**, because T292's driver attacks the *pinned* corpus
`classify-t229.json` and therefore inherits T290's framing that this is necessarily a **two-file**
edit.

**Step 1 — read the gate before driving it** [VERIFIED, quoted by the probe from source]:

```python
541  refused = bool(rep.unacknowledged or rep.unclassified_keys or rep.unclassified_verdicts
542                 or rep.void_acks or rep.mute_refutations or nil)
```

**`rep.disagreements` is not a term.** It is counted (`:445`), printed (`:564`, `:590`) and
**never gates**. So no document can be refused for having *lost* a disagreement — this is settled
by reading, before any run.

**Step 2 — drive it on fixtures I built:**

| arm | document | rc | disagreements | unack | witness | `coverageDigest` |
|---|---|---|---|---|---|---|
| **CONTROL** | `{"cells":[{"P1_principalAmortizesToZero": false, "verdict":"AS PREDICTED"}]}` | **1 REFUSED** | 1 | 1 | 1 | `714a61bc28e9d46b` |
| **ERASED** | the same, `"verdict"` rewritten to `"REFUTED"` | **0 GREEN** | **0** | 0 | 1 | **`714a61bc28e9d46b`** |

The control fires, so the probe is not vacuous.

**Three things follow, and the second is new.**

1. **F-T290-1b is open under T292's rule.** Confirmed, agreeing with T292's own honest finding.
2. **It is WIDER than T290 stated.** T290 framed it as the *consistent two-file edit* — retro-edit
   the evidence **and** re-pin the register. That two-file requirement is an **artefact of
   attacking evidence that happens to be pinned.** For a document **not** in the acknowledgement
   register, erasing a disagreement is a **ONE-FILE edit**: nothing is re-pinned, no register is
   touched, `voidAcks=0`, and the run is GREEN. The register is not a precondition of the attack;
   it is only a precondition of the attack *on pinned evidence*.
3. **T292's own contribution does not reach it.** `witness` is unchanged **and `coverageDigest` is
   byte-identical** across the erasure — so "pin the digest", which does catch the *predicate*
   half (T292's ARM 3), is blind to the *verdict-word* half. T292 reports this correctly; I
   confirm it on fixtures of my own.

**WHAT THE FLOOR MUST LOOK LIKE** (the brief asked, so I answer rather than defer). Nothing inside
a rule reading only `(document, register)` can supply it — the rule cannot know how many
disagreements a corpus *ought* to contain. So the floor belongs to the **wiring**, not the rule:

> For each graded corpus, the caller pins an **expected minimum `disagreements`** — and, separately,
> an expected `acknowledged` — and **REFUSES when the run reports fewer**. A corpus known to carry
> three acknowledged disagreements must go red the moment it reports two. Pin it beside the
> existing `coverageDigest` pin, which already covers the predicate half; the two together close
> both halves of the consistent edit.

Note the asymmetry that makes this safe to specify now: a floor on `disagreements` can only ever
**add** refusals, so it cannot re-open any fail-open — which is the property every previous fix in
this lineage failed to have.

**VERDICT ON THE PRECONDITION: `T269` REMAINS BLOCKED.** T292 is right, it drove the claim rather
than assuming it, and I have now driven it a second way. **No R-VPA rule may be wired — including
this one — until that floor exists.** I am not able to report the unblocking the brief asked me to
report loudly if I found it; I did not find it, and the hole is one file wider than the lineage
believed.

---

## 10. SPLIT VERDICT, RESTATED

**APPROVED:** the rule, the guards, the exit protocol, the read-integrity layer, the scope
discipline, and — measured independently, on both axes, against three pinned predecessor blobs —
**the claim that this link broke the streak.** That claim is the one I most expected to fail and it
held.

**REJECTED:** Theorem 1 as written (§2), Theorem 2 as scoped (§3), and the calibrated-zero claim
(§4, §5). None of the three is a defect in the rule's behaviour; all three are defects in what the
branch **says about** its behaviour, and this lineage's own history is that the next link inherits
the words.

Follow-ups this review does not perform and files instead:
* **T308-F1** — narrow Theorem 1's operation set to the adversary's (≤10 lines, mechanical).
* **T308-F2** — record guard #10 as a DECISION ("detection may read containers; we chose not to")
  or adopt G10-SIBLING with its measured limit stated.
* **T308-F3** — delete or redefine `LOST REFUSALS`; it cannot fire on a rule with the
  post-condition.
* **T308-F4** — give the adversary an expected-verdict oracle and add a `refused`-disjunction
  mutant other than `nil`.
* **T308-F5** — enforce `autoPredicatePattern` with `re.match`, not `str.isdigit()` (one line;
  also applies to the pinned T259 file, which must NOT be edited — fix it in the successor only).
* **T308-F6** — escape the witness path (`json.dumps` per segment, lines 257 / 260 / 421) so that
  a forged path cannot collide with a legitimate one or inject lines. Until then, **"the witness
  path is printed" is not a mitigation and must not be cited as one.** (§5c)
* **T308-F7** — the floor on `disagreements` that `T269` is blocked on: pin an **expected minimum
  `disagreements` and `acknowledged` per graded corpus in the WIRING**, and refuse when the run
  reports fewer. Specified in §9.5. It can only add refusals, so it cannot re-open a fail-open.
* **Observation** — `classify-t219.json` carries **4 unacknowledged disagreements** under both the
  T259 and T292 rules. Pre-existing, outside T292's scope, unreviewed by anyone.
