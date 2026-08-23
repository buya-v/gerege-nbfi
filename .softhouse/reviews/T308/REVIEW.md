# T308 — INDEPENDENT review of T292 (R-VPA lineage, link 5)

**Reviewer:** T308, branch `softhouse/T308-review-t292`, forked at `5964ab5`.
**Under review:** T292, merged to `main` at `37aa6b8` (branch pruned; diff read from the merge,
`git diff b0f32ec 37aa6b8` — 23 files, 4818 insertions, 0 deletions).

**VERDICT: SPLIT.**

| part of the branch | verdict |
|---|---|
| the rule `check_verdict_predicate_agreement_t292.py` — the WITNESS-SET formulation, the guards, the exit protocol, the read-integrity layer | **APPROVED.** Independently measured better than all three predecessors on **both** axes and on the control. The streak is broken. |
| **THEOREM 1** ("container-blindness", with `PROOF … []`) | **REJECTED as written.** False on **3 of the 4** container operations it itself names; one of them flips **REFUSED → GREEN**, the direction its own corollary denies. |
| **THEOREM 2** ("guard #10's ambition is a MEASURED IMPOSSIBILITY") | **REJECTED as scoped.** A separator exists, needs no register change and no external declaration, and refuses **10/10** of T291's header fixtures while permitting **both** committed corpora. Constructed and measured here. |
| **"THE ZERO IS CALIBRATED"** (`LOST REFUSALS: 0` over 325 documents) | **REJECTED.** The zero is a **tautology of the shipped rule**, not a measurement, and the calibration measures a rule that is not the shipped rule. Five mutants of **T259's own founding defect** survive T292's unmodified adversary with **0 failing legs**. |

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

## 3. FINDING F-T308-2 — "MEASURED IMPOSSIBILITY" IS PROVED ABOUT THE WRONG RULE CLASS; A SEPARATOR EXISTS

**Severity: MEDIUM (claim overreach — the strongest word in the branch is the least supported).**
**Reproduction: `python3 .softhouse/reviews/T308/probe/t308_theorem_b_counterrule.py` → EXIT 0.**
**Transcript: `out/t308-theorem-b.txt`.**

T292's claim: promoting `headerAffirmations` to a refusal *"refuses X5, X5b AND
classify-t229.json … Guard #10's ambition is unreachable by any container-blind rule … Separating
X5 from classify-t229.json requires an EXTERNAL declaration of which containers hold graded
records; that changes `boolean-key-register.json`'s contract."*

I did not argue with this. I **built the separator.**

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

**Why this matters and what it does NOT mean.** T292's sentence is *literally* true: no
**container-blind** rule can separate X5 from `classify-t229.json`, because the two documents are
identical under a container-blind reading. But **guard #10 is a DETECTION guard**, and the central
thesis of this very branch is that detection is entitled to be container-aware — `walk_objects` is
total and the docstring calls it *"the DETECTION side, generous, as it should be."* The
impossibility was therefore proved about a rule class guard #10 never needed to belong to. The
honest statement is:

> *No container-blind rule can separate them, and I chose not to make guard #10 container-aware.*

That is a **design decision**, and T292 did not record it as one. It recorded it as a theorem.

**I am not asking for G10-SIBLING to ship.** I measured its limit in the same run and printed it:
the row `EVASION-header-moved-INSIDE-the-records-list` — `{"cells":[{"verdict":"AS PREDICTED"},
{"P2_x":false,"verdict":"REFUTED"}]}` — scores **census 1, sibling 0**. Moving the header into the
records container defeats it, exactly as **P-91** predicts: *"a guard phrased as a STRUCTURAL
PATTERN over the shape of its input can always be re-nested one level out, so enumerating shapes
that COUNT and refusing the unmatched is a losing method no matter how carefully each shape is
chosen."* The finding is that **"impossible" is the wrong word for something a 20-line predicate
does on this corpus.**

### 3b. Sub-finding (LOW): the "5" in the impossibility argument is measured with the wrong instrument

The docstring says *"Measured, by `probe/census_real_corpus.py`: classify-t229.json contains **5**
such affirmations (3 cells + 2 calibration)."* The **shipped rule prints 3**:

```
T259-VPA: GREEN files=1 … headerAffirmations=3 …      [VERIFIED, run by me]
```

`census_real_corpus.py` counts a witness only for keys matching `^P[0-9]+_` and ignores the
register's three PREDICATE entries `inputsIdentical` / `observedIdentical` / `threwIdentical`, so
it wrongly treats the two `calibration` rows as ungraded. Under the rule's **own** witness
definition those rows grade three facts each and are not header affirmations. The argument
survives (3 committed rows still go red), but the number quoted in support of it was produced by a
different predicate than the one that ships, and both the docstring and the merge message mix them.

---

## 4. FINDING F-T308-3 — `LOST REFUSALS: 0` IS A TAUTOLOGY OF THE SHIPPED RULE, AND THE CALIBRATION MEASURES A DIFFERENT RULE

**Severity: HIGH (the headline number of the branch).**
**Reproduction: read the two lines below; corroborated by T292's own committed transcripts and by
`out/t308-survivor-mutants.txt`.**

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
**Transcript: `out/t308-survivor-mutants.txt` (pass 1, with an inverted gate, preserved at
`out/t308-survivor-mutants-pass1.txt` — see §7).**

T292's eight kill targets attack COVERAGE (M1/M2/M3), READ INTEGRITY (M4/M5/M10/M6), the EXIT
PROTOCOL (M7) and DETECTION BREADTH (M9). **Not one attacks the GATE** — the disjunction in `main`
that turns counted refusals into exit 1. So I planted the lineage's *founding* defect there
instead: **the refusal is printed in the body and the exit code stays GREEN** (T259's defect, per
P-91: *"`T259` shipped a rule that printed `REFUSED NIL COVERAGE` in its body and **exited
GREEN**"*), once at each of five guards, and ran **T292's unmodified adversary** against each.

| mutant | disposition | LOST REFUSALS | failing legs |
|---|---|---|---|
| `N1` unacknowledged disagreement printed but not COUNTED (G5) | **SURVIVED** | 0 | **0** |
| `N2` mute refutation printed but not COUNTED (G6) | **SURVIVED** | 0 | **0** |
| `N3` void acknowledgement printed but not COUNTED (G4) | **SURVIVED** | 0 | **0** |
| `N4` unclassified verdict word printed but not COUNTED (G1) | **SURVIVED** | 0 | **0** |
| `N5` unclassified boolean key printed but not COUNTED (G2) | **SURVIVED** | 0 | **0** |
| `N6` CONTROL — drop `nil` from the same disjunction | KILLED | 0 | 11 |

`N6` is the positive control and it dies, so the harness is not simply passing everything: `nil`
is the one term in that disjunction the **post-condition independently re-checks**, which is
precisely why it is the one term the adversary can see.

`N1` driven on `A10-CONTROL-genuine-unacknowledged-disagreement` — a fixture **already in T292's
own corpus**:

```
SHIPPED : rc=1  T259-VPA: REFUSED … disagreements=1 acknowledged=0 unacknowledged=1 … witness=1
N1      : rc=0  T259-VPA: GREEN   … disagreements=1 acknowledged=0 unacknowledged=0 … witness=1
```

The mutant prints `disagreements=1, acknowledged=0, unacknowledged=0` **and exits GREEN**. That is
T259's founding defect, reproduced inside the instrument built to prove it cannot recur, and
T292's adversary passes it **82/0/0**.

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
`out/t308-survivor-mutants-pass1.txt`; the gate is now "non-zero if ANY kill target survived."

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
  separation under **P-81** (*"an error is not a measured negative"*).
* **The exit protocol is right.** `--help` returns 2 with no probe line; `add_help=False` plus the
  `SystemExit` catch covers both argparse exits. `PYTHONOPTIMIZE=2` still refuses, because the
  post-condition is an `if`, not an `assert`.
* **Read-once is real:** one `read_bytes()`, sha of that buffer, parse of that buffer. The
  acknowledgement pin covers the bytes that were graded.
* **No ratified DEC-n changed**; no vector, no Go file, no `nexus/` path in the diff.
* **The branch's self-recorded defects are honest and complete as far as I could check** — I found
  no defect T292 concealed. Every finding above is about a claim T292 **made**, not about a defect
  it hid.

---

## 9. WHAT THE NEXT LINK MUST NOT INHERIT

1. `LOST REFUSALS: 0` **must not be quoted again as evidence.** It is `|∅|`. (§4)
2. Guard #10 is **not impossible**; it is **not container-aware**, by a choice nobody wrote down.
   (§3)
3. Theorem 1's operation list must be narrowed to what the adversary actually generates. (§2)
4. **The adversary needs an expected-verdict oracle.** Four properties that are all satisfied by a
   rule that refuses nothing is how five guards' worth of founding defect walked through. (§5)
5. **F-T290-1b remains open under this rule** — T292 says so plainly and drives it rather than
   assuming it, and `T269` must still not wire any R-VPA rule until T290's floor on
   `disagreements` exists. I confirmed the statement is present and is driven
   (`out/f-t290-1b-driven.txt`); I did **not** independently re-derive T290's floor, and say so.

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
* **Observation** — `classify-t219.json` carries **4 unacknowledged disagreements** under both the
  T259 and T292 rules. Pre-existing, outside T292's scope, unreviewed by anyone.
