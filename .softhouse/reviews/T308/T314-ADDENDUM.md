# T314 ADDENDUM TO REVIEW T308 — F-T308-6 CLOSED, AND THE TWO WITHDRAWN DOWNGRADES RE-SCORED

*Worker T314, branch `softhouse/T314-witness-path-forgery`, run `2026-08-21-run2-tierA-gl-accounting-A2`.*
*This file AMENDS T308's REVIEW.md; it does not edit it. T308's review is committed evidence
(T114/T176) and `REVIEW.md` is left byte-for-byte alone.*

---

## 0. WHAT WAS DONE

F-T308-6 was raised by T308 and **established by construction**. T314 did not re-derive it — it
took T308's two attacks as arms and **closed** them, and it found that the half T308 flagged as
worse (`coverageDigest`) is worse than T308's own diagnosis of it.

* **The fix ships as a SUCCESSOR file**, `.softhouse/capture/t314-witness-path-forgery/check_verdict_predicate_agreement_t314.py`.
  T292's file is **not edited** — it is committed evidence, it is the file T308 measured, and it is
  outside T314's edit scope. `git diff` on `.softhouse/capture/t286-t268-retry/` is empty.
* **NOT WIRED, and must not be.** `T269` stays blocked: no R-VPA rule may be wired into
  `.softhouse/conformance.sh` until **T308-F7** exists (pin an expected-minimum `disagreements` /
  `acknowledged` in the wiring). **F-T290-1b is untouched and stays OPEN**, as T308 widened it.
* Reproduction:
  * `python3 .softhouse/capture/t314-witness-path-forgery/probe/t314_drive_red_witness_path.py` → **EXIT 0**
    (transcript `out/t314-drive-red-witness-path.txt`)
  * `python3 .softhouse/capture/t314-witness-path-forgery/probe/t314_render_path_injective.py` → **EXIT 0**
    (transcript `out/t314-render-path-injective.txt`)

---

## 1. THE ENCODING, AND WHY A NAIVE ESCAPE IS NOT IT

T308's suggested fix was *"render each path segment through `json.dumps` … Three lines (257, 260,
421)."* That is the right instinct and it is **not enough as three lines**, for a reason T314
measured rather than argued:

**The path was not only printed. It was also an IDENTITY.** `witnessed_objects` is a set of path
strings, and the census asks `owner not in witnessed_objects` where
`owner = spath.rsplit(".", 1)[0]` [VERIFIED: `check_verdict_predicate_agreement_t292.py:470-476`].
A key containing a `.` therefore steers a **set-membership test**, not a line of output. Escaping
the printer leaves that untouched. Driven as **arm A4**.

So the change is structural, not cosmetic:

> **The path is a TUPLE OF SEGMENTS** — `str` for an object member, `int` for an array index —
> carried through the traversal, used for every identity comparison, and turned into a string by
> **exactly one function, `render_path`, at the print boundary.**

```
path    ::= "$" segment*
segment ::= "#key" | "[" DIGIT+ "]" | "[" JSON-STRING "]"     JSON-STRING = json.dumps(k, ensure_ascii=True)
```

**INJECTIVITY, argued and then measured.** Every segment is `[`-delimited; inside it the first
character decides the case (`"` ⇒ member, digit ⇒ index, disjoint); a JSON string literal is
self-delimiting, so the token stream is uniquely parseable back to the tuple. Measured two ways
over a 12,735-tuple adversarial universe (alphabet includes `cells[0]`, `"`, `\`, `\n`, `.<key>`,
`a"]["b`, `P1_x=1;P2_y`, an astral-plane codepoint, and the empty key):

| encoding | collisions | T308 A1 | T308 A2 |
|---|---|---|---|
| T292 `path + "." + k` | **47** | COLLIDES | injects (3 lines) |
| **the naive fix — escape the newline only** | **47** | **COLLIDES — still fully alive** | 1 line |
| **T314 `render_path`** | **0** | differ | 1 line |

and constructively: `parse_path(render_path(t)) == t` for **12,735/12,735** tuples. *A left inverse
exists*, which is a proof of injectivity over the tested domain rather than a count of collisions
that happened not to occur.

**The naive-escape row is the argument.** `cells[0]` contains no character a newline-escape
touches. A1 is **an ambiguous grammar, not an unescaped character**, and only *delimiting* each
segment removes it.

**Stated no wider than it is.** A key may still *contain* text that looks like a witness line;
T308's A2 payload still renders, inside one quoted segment, on one line. Injectivity is a property
of the encoding, not of substring `grep`, and no encoding gives the second. The claim is exactly:
*one witness renders to exactly one line, and no two distinct traversals render to the same
string.* Naming is not verification — clause 1 of the floor is untouched and unbeatable.

---

## 2. THE `coverageDigest` — T308 WAS RIGHT THAT IT IS THE WORSE HALF, AND RIGHT FOR THE WRONG REASON

**What the digest is actually computed over** [VERIFIED: `check_verdict_predicate_agreement_t292.py:598-603`]:

```python
canon = ";".join(sorted("%s=%s" % (k, "1" if v else "0") for _, k, v in rep.witness))
return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]
```

**The path is discarded — `for _, k, v`.** So:

**(a) A1's digest collision is NOT a defect.** T308's §5c reads *"the one field that could have
separated them collides too"*, and §6 of the same review already records the opposite —
*"`coverage_digest` deliberately excludes the path … so the digest cannot be moved by containers
either"*. §6 is the correct reading. A1's two documents grade the **same (key, value) multiset**,
so an identical digest is **container-blindness working as designed**. Putting the path into the
digest would break the property the digest exists to have, and it would be the wrong fix. T314's
POST arm therefore **asserts the A1 digests still match** — that check is in the probe as a
regression guard, not as a leftover.

**(b) The real digest defect is that the CANON is itself an unescaped concatenation over
attacker-chosen keys**, with `;` as the record separator and `=` as the field separator, neither
forbidden in a JSON member name. **New, T314's arm A3:**

| document | witness | `coverageDigest` (T292) |
|---|---|---|
| `{"cells":[{"P1_x":true, "P2_y":true, "verdict":"AS PREDICTED"}]}` | **2** | `d99d1f0859310868` |
| `{"cells":[{"P1_x=1;P2_y":true, "verdict":"AS PREDICTED"}]}` | **1** | **`d99d1f0859310868`** |

Both keys auto-classify under `^P[0-9]+_`; both canons are the 11 bytes `P1_x=1;P2_y=1`. **A
document that graded ONE proposition produces the fingerprint of a document that graded TWO.** That
falsifies the digest's own docstring sentence — *"changes the moment the graded FACTS change"* —
and it is **strictly worse than A1**, whose two documents at least graded the same facts.

**And this is the point that is easy to miss while fixing the printing: escaping the display moves
this digest by not one bit.** The two are independent defects that happen to share a cause.

**Fix:** canonicalise as JSON — `json.dumps(sorted([k, bool(v)] for _, k, v in rep.witness),
ensure_ascii=True, separators=(",", ":"))` — so each key is quoted and escaped and none can span a
record boundary. The path stays excluded, deliberately. Post-fix the two A3 digests are
`841d203ad62a6a0b` and `fde6ff02936dcbb0`.

**Not changed, recorded rather than quietly fixed:** the digest stays truncated to 16 hex (64
bits). The threat that matters — make a forged document's digest equal a specific pinned one — is a
**second preimage at 2⁶⁴** and I did **not** demonstrate it. A birthday collision between two
documents an attacker controls *both* of is 2³², which is feasible but a weaker threat. Widening is
a follow-up, not a claim I can support. `[UNVERIFIED as exploitable]`

---

## 3. THE TWO WITHDRAWN DOWNGRADES, RE-SCORED

T308 withdrew both justifications when it falsified clause 2 and explicitly left the re-scoring
undone. Here it is. **Scored twice: as the tree stands today, and as it would stand if the rule
were wired** — because the second is the only score that will still be true when someone acts on it.

### 3a. §2 / CE3 (part of **F-T308-1**) — *"This is not a security hole … the witness path is printed, so the forgery is NAMED."*

**Re-derived severity: F-T308-1 STAYS MEDIUM. The conclusion survives; one of its two reasons did not.**

The withdrawn clause was never load-bearing on the *number*. F-T308-1 is a **proof defect**: the
theorem's own operation list is not a subset of its own hypothesis class. Its severity comes from
*"the docstring is what the sixth link will read, and it currently says `PROOF … []` under a
statement three of its own operations refute"* — and that is untouched by anything in F-T308-6.

The sentence *"this is not a security hole"* rested on **two** legs: (a) CE3 lands inside clause 1's
declared forgery floor — it must **assert** a `^P[0-9]+_` boolean; (b) it is at least **named**.
Leg (b) was false. **Leg (a) alone still carries the conclusion**, together with the fact — verified
by T308 by `git grep` — that the rule **has no caller**. So the conclusion stands and the comfort
does not.

**With T314 applied, leg (b) is repaired rather than merely withdrawn**, in the weaker form that is
now true: CE3's manufactured witness renders as
`$["t223RulePredictedRescue"]["P9_z"] = true`, which no other traversal can produce, so it is
printed **under its own name and cannot borrow a legitimate document's**. That is worth having and
it is not a detection claim.

**Still open, and T314 did not fix it** (not T314's finding; fixing another worker's finding inside
this diff would muddy the one change a reviewer needs to check): the docstring correction T308
specified. T314 **marks the paragraph false inline** rather than carrying it silently, so the sixth
link reads the warning and not the proof.

### 3b. §5b / **F-T308-5** — *"Severity is LOW because the smuggled key still has to assert a boolean fact … and the witness path is printed."*

**Re-derived severity: LOW → MEDIUM if the rule is ever wired; LOW today, on impact only.**
**Driven as arm A5.**

This one **does** move, and the reason is specific to it. F-T308-5 is not a proof defect — it is a
**fail-open in a named guard**. `key_class` implements the register's declared
`autoPredicatePattern` as `head[1:].isdigit()`, which is true for Unicode digits `[0-9]` does not
match. So `P²_x` **auto-classifies without being in the register**, `unclassifiedKeys=0`, and **G2 —
the guard T259 exists for, whose register says "UNCLASSIFIED is a REFUSAL, not a pass" — does not
fire on a key nobody classified.** Measured under BOTH rules, still open:

```
PRE  homoglyph `P²_x`  rc=0 unclassifiedKeys=0  line: $.cells[0].P²_x = true
POST homoglyph `P²_x`  rc=0 unclassifiedKeys=0  line: $["cells"][0]["P²_x"] = true
```

**Why the withdrawal hits this finding harder than CE3.** F-T308-5's LOW rested on visibility, and
the smuggled key here is **not merely attacker-chosen — it is chosen to be visually confusable with
a legitimate one**. Under T292 the printed line for `P²_x` is `$.cells[0].P²_x = true`, which a
human reader scanning a transcript does not distinguish from `P2_x`'s. The mitigation failed twice
over: once through the concatenation T308 found, and once through **homoglyph rendering**, which
T308 did not test.

* **Impact TODAY: LOW.** No caller [VERIFIED by T308, `git grep`]. Nothing reads this rule's exit
  code, so nothing can be fooled by it.
* **Impact IF WIRED: MEDIUM.** A document supplies coverage from a key **no register ever
  classified**, defeating the exact guard that was written to stop it, with no reliable
  transcript-level tell. It stays sub-HIGH because clause 1 still binds — the forger must **assert
  a boolean fact**, which is the acknowledged irreducible floor, and because the fix is one line:
  `re.match(reg["autoPredicatePattern"], key)`.
* **What T314 changes:** nothing about the defect. `render_path` uses `ensure_ascii=True`, so the
  smuggled key now prints as `"P²_x"` and is **unmistakable**. That restores the visibility leg
  and is the reason the wired score is MEDIUM rather than higher. **The `isdigit()` fix is still
  owed.** T314 marks it inline at G2.

### 3c. The general rule this pair produces

**A severity downgrade that cites a MITIGATION must test the mitigation in the same pass that cites
it.** T308's first pass used clause 2 twice, both times without driving it, and both citations were
false — one harmlessly (CE3's conclusion had a second leg) and one not (F-T308-5's did not). The
cheap discipline is: *if the reason a finding is LOW is a sentence in the code's own docstring, that
sentence is now part of the finding and must be driven RED before it is leaned on.*

---

## 4. THE SCRATCH FILE T308 COMMITTED — ADJUDICATED, NOT DELETED

`.softhouse/capture/t286-t268-retry/.t308-mut-4c4uwsr2/N3-void-acknowledgement-printed-but-not-COUNTED-legs.json`
(635 lines, 19,364 bytes) is in T308's merged diff while T308's report says *"no scratch leaked"*.

**What is actually true of it, verified:**

1. It was added in commit `5adc2834`, *"T308: point every transcript reference at a file that exists
   and is non-empty"*. That commit touches exactly two files, and its message describes only the
   other one — the `REVIEW.md` edit at line 226 renaming `out/t308-survivor-mutants.txt` to
   `out/t308-survivor-mutants-pass2-stale-label.txt` [VERIFIED: `git show 5adc2834`]. **The JSON was
   swept in by the staging, not committed on purpose.** The commit message does not mention it.
2. **Nothing references it.** `grep` across `.softhouse/reviews/T308/` and `.softhouse/handoff/`
   finds no occurrence of the filename or of `t308-mut-` outside `probe/t308_survivor_mutants.py`'s
   own `mkdtemp` prefix [VERIFIED]. So it is **not** the file that commit was fixing a reference to.
3. **The mechanism is a `.gitignore` that fenced the wrong prefix.**
   `.softhouse/reviews/T308/.gitignore` fences `.t308-*`; `.softhouse/capture/t286-t268-retry/.gitignore`
   fences **`.t292-*` only** [VERIFIED: both files read]. A T308 probe writing scratch under the
   *capture* directory was therefore unignored there. `probe/t308_survivor_mutants.py` at HEAD uses
   `dir=HERE.parent` (= `reviews/T308/`), which would **not** produce this path — and there are two
   survivor-mutant transcripts, `pass1` and `pass2-stale-label`, so **a superseded revision of that
   probe wrote into the capture dir** and its scratch outlived it. `[UNVERIFIED: the pass-1 source
   is not committed, so the `dir=` it used cannot be read back.]`
4. **Its content is a real, PARTIAL artifact** — an adversary legs record for mutant
   `N3-void-acknowledgement-printed-but-not-COUNTED`, with `pre_blob 86f4285`, `docs: 100`,
   `lost_refusals: []`, a populated `widenings` list, and **`"new_sha": ""`** — an empty new-side
   hash, i.e. the record of a run that did not complete its own pinning [VERIFIED: read].

**Recommendation — and the recommendation is NOT "delete it".**

* **Do not delete it unilaterally, and specifically not in this fire.** T304 is concurrently working
  the *"instruments that destroy committed evidence"* property. A worker quietly removing a
  committed file from a capture directory, in the same fire, is precisely the act that property
  exists to catch — and the deletion would be indistinguishable from the thing being guarded
  against. **Whatever is decided, it must be decided visibly.**
* **It is not evidence and must never be cited as such.** `new_sha` is empty. Anyone finding this
  file and reading a number out of it would be reading an aborted run. If it is kept, it should be
  kept **inert**: leave it exactly where it is and record here that it is a leaked partial.
* **Fix the CAUSE, which is one line and which nobody has done:** add `.t308-*` to
  `.softhouse/capture/t286-t268-retry/.gitignore`. That is an edit to a directory outside T314's
  scope, so T314 did **not** make it — it is filed as a follow-up. T314 fenced **its own** capture
  directory (`.t314-*`, `__pycache__/`) so it cannot repeat the pattern.
* **The disposition T314 recommends:** keep the file, unreferenced and unmoved, until T304's
  property lands; then let the owner of that property decide whether committed-but-inert scratch is
  in scope for removal, with the removal recorded in its own commit whose message says what is being
  removed and why. If it is removed sooner, it must be its own commit, named, and not folded into
  another change — which is the exact failure that put it here.

**The transferable finding:** T308's *"no scratch leaked"* was true of the directory T308 fenced and
false of the directory T308 wrote into. **A scratch fence is scoped to the directory it sits in; a
probe that writes outside its own tree is outside its own fence.** Assert "no scratch leaked" only
from `git status` over the whole tree, never from the presence of a `.gitignore`.
