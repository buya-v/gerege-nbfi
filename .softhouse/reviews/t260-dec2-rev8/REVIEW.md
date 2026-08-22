# T260 — INDEPENDENT REVIEW of DEC-2 revision 8 (task `T255`, branch `softhouse/T255-dec2-rev8` @ `b334786`)

**VERDICT: RATIFY.** Nine findings, none of them an obligation move, none of them a reason to keep
DEC-2 at revision 7. Two MEDIUM findings are about the CHECKER and about how the document
DESCRIBES its own mechanism; they should be filed as conditions on the follow-up that wires the
checker, not as blockers on ratification. **Nothing blocks closure of `G-14`.**

Every figure below is stamped with the commit it was measured at (`P-69`) and re-measured at the
end. My worktree HEAD was `2f654ad`; `main` moved to `b40f341` during the review and the
load-bearing invariants were re-measured there (§11).

---

## 0. What I did NOT take on trust

I did not re-run T255's instruments and report their exit codes. I built my own, in
`.softhouse/reviews/t260-dec2-rev8/instruments/`, with transcripts in `evidence/`:

| instrument | what it derives |
|---|---|
| `10-section-identity-map.py` | partitions the WHOLE document by heading and reports IDENTICAL / CHANGED per section |
| `20-normative-set-diff.py` | sentence-level normative set difference with a **deliberately broader, non-modal-inclusive** predicate |
| `30-table-cell-census.py` | every pipe-table row in the document, cell by cell, plus a dedup-free multiset control |
| `40-citation-census.py` | independent re-count of the `path:NNNN` denominator |
| `50-collision-and-red-drive.sh` | the real T253 collision under **both** implementations, and the anchor mechanism driven RED three ways |
| `60-c-items-and-residuals.py` | C-1…C-8 against the landed bytes; every residual `conformance.sh:NNNN` printed and classified |
| `70-spotcheck-stale-sites.sh` | the four stale sites and **every anchor**, resolved with the document's own `git grep -n -F` recipe, `P-80` status classified |
| `80-` / `85-instrument-audit*.py` | T255's seven instruments scanned for `P-75`/`P-80`/`P-22` known-bad shapes, the second pass over executable code only |
| `90-per-section-line-delta.py` | for every changed section, the exact lines removed and added — the population I read by hand |

---

## 1. THE LOAD-BEARING CHECK — NO NORMATIVE OBLIGATION MOVED. Determination: **CONFIRMED.**

T255 proved this with three legs and named its own weakness: its six "obligation-bearing blocks"
are a **chosen** population, and an obligation phrased **without a modal verb** escapes LEG 2
entirely. I attacked exactly that, and I did not reuse its method.

### 1.1 P-67 — what fraction of the document T255 did NOT put under byte identity

Measured at `a71c140` by `40-`/`10-`, both terms:

| | lines | chars |
|---|---|---|
| **inside T255's LEG-1 byte-identity blocks** | 553 (**18.2 %**) | 50 079 (**20.1 %**) |
| **NOT inside them** | 2 486 (**81.8 %**) | 198 575 (**79.9 %**) |
| document total (revision 7) | 3 039 | 248 654 |

So **four fifths of DEC-2 was covered only by LEG 2 (modal lines) and LEG 1b (the seven §4.4
rows)**. T255's `[UNVERIFIED]` item 1 is therefore load-bearing, not decorative, and this review
had to close it independently. The sections T255 left outside byte identity that carry normative
or normative-adjacent content are: the **banner/status preamble**, **§0**, **§2.2**, **§4.4**,
**§4.4.1**, **§4.9**, **§5**, **§5.1**, **§5.2 outside requirements 1–7**, **§5.3 outside the
table**, **§5.4**, **§8.1**, **§8.2**, **§8.3**, **§10** — 15 sections.

### 1.2 My leg A — whole-document section identity (derived, not chosen)

`evidence/10-section-identity-map.txt`. Of 40 sections, **22 are byte-identical in their
entirety** — 972 of 3 039 lines (**32.0 %**), including §1, §1.1, §2.1, §2.3, §3.x, §4.1, §4.3,
§4.5, **§4.6**, §4.7, §4.8, **§4.10**, §5.0.1, §5.1.1, **§5.5**, §6, §7, §8, **§9**. 15 sections
changed. Both terms sum to the document; the instrument asserts that.

### 1.3 My leg B — EXHAUSTIVE table-cell census (this is where non-modal obligations live)

`evidence/30-table-cell-census.txt`. DEC-2 states most of its rule content in table cells, and a
cell that states a rule usually carries no modal verb. Population: **every** pipe-table row.

* rev7 **140** rows, rev8 **140** rows.
* **0 rows removed, 0 rows added.**
* **Exactly 4 rows changed** — `I-1`, `I-2`, `I-3`, `I-7`, all in §4.4 — and in each the **only**
  cell that moved is the last ("Graded today?"). Confirmed dedup-free by a multiset control that
  does no keying at all: exactly 4 rev7 rows have no exact twin in rev8, and they are those four.
* `I-7`'s obligation cells are byte-identical: cell 2 `` `Idempotency-Key` on every money-movement
  POST `` (sha `261c61542124`, 46 chars) and cell 4 (sha `5e956f8b0851`, 324 chars).
* **Every one of §5.3's ten precondition rows, §4.2's rows, §4.9's two taxonomy tables, §4.10's
  registry rows and §5.2's matrices is byte-identical.** This is a *stronger* result than T255's,
  and it is derived from the document rather than delimited by hand.

### 1.4 My leg C — normative set difference with a BROADER, non-modal predicate

`evidence/20-normative-set-diff.txt`. Sentence granularity (so a re-wrap is invisible and a
rewording inside a wrapped line is visible), citations normalised (so a citation-only edit is not
reported as a lost obligation), and the predicate extends T255's modal set with: **never, always,
is/are required to, is prohibited/forbidden/not permitted, mandatory, requirement/precondition
nouns, obligation nouns, subject-of-duty ("the port", "a conformant implementation", "the
adapter"), and imperative openers.**

* rev7 **219** normative sentences (T255's predicate found 87 lines — mine is **2.5×** the
  population). rev8 **248**.
* **LOST 14 — 8 MODAL, 6 NON-MODAL.** GAINED 43.
* **I adjudicated all 14 by hand.** Result:

| lost | site | disposition |
|---|---|---|
| L-M01 | banner headline + *"what a conforming port **must** do"* | the modal clause survives **verbatim** (probed: 1 occurrence rev7, 1 rev8) |
| L-M02 | status block, "Ratification requires a FURTHER review" | FACT — G-11 is closed; §5.3's own gating sentence is untouched |
| L-M03 | freshness-rule heading paragraph | re-emitted with the remedy performed (G-M04) |
| L-M04 | §4.4 `I-3` row | only the last cell moved; *"a ratifier **must not** read this row as having decided it"* survives (1→1) |
| L-M05 | §4.4 `I-7` row | only the last cell moved; the `Idempotency-Key` obligation cell is byte-identical |
| **L-M06** | **§4.4's rule paragraph** | **split into two sentences. Both obligations survive verbatim** — *"DEC-2 **obliges** I-1 through I-5 on any implementation"* (G-M09) and *"**I-3 and I-4 must be enforced by a harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement rather than a hope"* (G-M10). **The only clause deleted is the FACT *"and grades none of them today"***, and the added tail *"no growth of this corpus will ever discharge them"* **strengthens** it |
| L-M07 | §8.1's closing *"The two must never be confused"* | replaced by a **WIDER** warning: *"a citation of this document, **or of a green ledger section**, as evidence of ledger coverage is a misreading of **both**"* |
| L-M08 | §8.3 heading *"If ratified, these remain true and must not be misread"* | conditional → operative; *"must not be misread"* survives verbatim |
| L-N01 | §0's `A2-8` sentence | FACT, re-grounded and **the ungraded half named** (slot resolution still `in_graded_domain: false`) |
| L-N02 | §4.9 *"a representation for it is precondition **P-2** in §5.3"* | survives in substance: *"Precondition `P-2` was the representation this block said was missing; it exists."* |
| L-N03 | §5's `go test` citation sentence | CITATION + count corrected (see C-9) |
| L-N04 | §5.2's *"Nine open, one landed"* | retracted as a current fact, kept as revision 4's count; **the table is untouched** |
| **L-N05** | **§8.2's admissibility-standard enumeration** | **the one I went hunting for. All five elements survive verbatim** — §4.2's predicates, §4.6's A-1…A-4, §4.10's registry, §5.5's `graded_against`, **§5.2's requirements 1–7**. Only the tense moves (*"has an admissibility standard"* → *"had an admissibility standard **and used it**"*), and the sentence was always scoped to `A2-15`, which is `done`. The standard itself lives in §4.2/§4.6/§4.10/§5.5/§5.2, **all of which I proved byte-identical in the parts that state it**. NOT an obligation move |
| L-N06 | §8.2's *"`A2-15` cannot start without them"* | FACT (A2-15 ran). **The obligation was never here** — §5.3's own lead, *"`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are preconditions, not follow-ups"*, is **UNCHANGED**, and §5.3's new note refuses to certify discharge in terms: *"**A ratifier must read this note as 'the preconditions were addressed and the corpus is green', never as 'P-1…P-10 are discharged'.**"* That is a strengthening |

**The 16 GAINED modal sentences add no requirement on a port.** They are about readers,
resolvers, ratifiers and this document's own process. Two are new *self*-constraints (`G-M13`
"REQUIREMENTS 1–7 BELOW ARE NORMATIVE", `G-M14` the ratifier instruction) and both narrow what a
reader may conclude.

### 1.5 My leg D — the applier re-derivation, which makes the coverage question moot

`instruments/30-apply-revision-8.py` is content-addressed and carries **no line number**. I ran it
from revision 7 in a sandbox:

```
DEC-2 before: sha256 f02f7ff038afbf389bbd21a3fd40c55cc38cd88004e1833bded0f077f7957f44, 3039 lines
APPLIED: 43 of 43 hunks.
DEC-2 after:  sha256 09e456b887506288c642a595c8b4f39bdb7d34205a7cf5c8995b02057fab8164, 3542 lines
```

and `09e456b8…` is **byte-identical to the committed revision 8 blob**. So the entire +688/−185 is
accounted for by 43 named BEFORE→AFTER pairs; there is no hand edit outside them. Combined with
`90-per-section-line-delta.py`, which prints all **176 removed and 656 added non-blank lines**
grouped by section, **I read 100 % of the change**, not a sample.

**Determination: no field, no rounding rule, no obligation, no graded cell, no §4.2 predicate, no
§5.2 requirement, no §5.3 precondition row and no contract sentinel moved. `PIN-ledger.json` and
the vector store are not in the diff. Revision 8 is inside `G-14`'s recorded scope.**

---

## 2. FINDINGS

### F-T260-1 — MEDIUM. The anchor checker's population is 22 of the document's 25 anchors, and the gap is SILENT.

Measured at `b334786`. DEC-2 revision 8 contains **25** literal `[ANCHOR ` tokens.
`20-verify-anchors.py`'s regex —

```
ANCHOR_RE = re.compile(r"\[ANCHOR\s+(\S+?)\s+::\s+`([^`]+)`\]")
```

— requires `]` **immediately** after the closing backtick, and matches **22**. The three it misses:

1. the rule-1 **template** `[ANCHOR <repo-relative path> :: …]` — correctly skipped, but only by
   the accident that the placeholder contains a space;
2. **§4.4's `I-3` row**, live: `` [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`; MEASURED by `T255` at `a71c140`: `invariant violations 0`] ``
3. **§8.3's second bullet**, live: `` [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`; MEASURED by `T255` at `a71c140`] ``

Items 2 and 3 are **real citations in landing text that the checker never inspects**, and it
neither says so nor reconciles a count. The instrument's own docstring claims the opposite:

> *"This instrument reads its whole population **OUT OF THE DOCUMENT**, so a citation nobody
> remembered cannot be silently unchecked (P-66/P-70)."*

That claim is false as written. It is a memory-shaped hole in the instrument built to abolish
memory-shaped holes.

**Not a correctness defect today**: I resolved both by hand with the documented recipe —
`guard_ledger_invariants() {` returns exactly 1 match at `029439ba` — so they hold. **Fix (2
lines):** count `[ANCHOR ` literally and REFUSE with exit 2 when it ≠ `len(ANCHOR_RE.findall())`,
or widen the regex to allow a trailing `;` clause.

### F-T260-2 — MEDIUM. A NON-UNIQUE anchor degrades at **exit 0**, and the document claims otherwise.

This is the brief's question and it is the most important thing I found about the mechanism.
`evidence/50-collision-and-red-drive.txt`, driven in a sandbox against a copy of `conformance.sh`,
with an unmutated control that stays green:

| mutation | `20-verify-anchors.py` | **what a reader following `git grep -n -F` sees** |
|---|---|---|
| anchor **DELETED** (symbol renamed) | exit 1, `ROT … NOT PRESENT` | **0 matches, exit 1** — the reader gets NOTHING, loudly. Strictly better than a rotted line number, which resolves to a plausible neighbour |
| anchor **EDITED** (one space inserted: `() {` → `()  {`) | exit 1, `ROT` | **0 matches, exit 1** — same. But note: a line number would have survived this edit entirely (see the regression table below) |
| anchor **NON-UNIQUE** (a second definition or a commented copy) | exit 1, `AMBIG … 2 occurrences` | **2 matches, `git grep` EXITS 0 (SUCCESS)**, lines 1301 and 1302 printed. **Nothing tells the reader the citation is broken.** |

So **"elimination beats detection" is achieved for deletion and edit, and NOT achieved for
non-uniqueness.** The only thing that catches AMBIG is the hand-run checker, which is `FU-T255-1`.
The document's rule-4 sentence —

> **"An anchored document is correct with nothing running at all."**

— is therefore **overstated**, in the same direction and the same shape as the claims that got
revisions 2, 3 and 4 rejected. The accurate sentence is: *an anchored document FAILS VISIBLY AT
READ TIME with nothing running, except when an anchor has become non-unique, which only the checker
catches.* Degradation is **visible but unflagged**, not silent — which is why this is MEDIUM and
not HIGH: a duplicate anchor still shows the reader both candidate sites, one of which is right,
whereas a rotted line number shows one site, wrong.

### F-T260-3 — MEDIUM. The rule is adopted; it is applied to ~8 % of the perishable citations.

My independent census (`evidence/40-citation-census-rev7.txt`, `-rev8.txt`), both terms:

| | rev7 (`a71c140`) | rev8 |
|---|---|---|
| total `path:NNNN` citations | **117** | 110 |
| Fineract-pinned (do not drift) | 26 | 26 |
| **repo-pointing (perishable)** | **91** | **84** |

Revision 8 converts **7 of 91**. **38 bare `admit.go:N` / `vector.go:N` citations remain, ambiguous
between `loanschedule/conformance/` and `ledger/conformance/` as well as perishable** — the very
defect the banner names. T255 discloses this honestly (`FU-T255-2`, `FU-T255-3`, and §10's *"What
revision 8 does NOT claim"*), and its reason — *"converting 70 citations in the same fire that
lands the mechanism would have buried the mechanism"* — is sound. But rule 4's *"an anchored
document"* is a claim about **this** document, and this document is ~8 % anchored. The rule is
right; the self-description runs ahead of the application.

### F-T260-4 — LOW. The applier's refusal is NARRATED, not evidenced. (I evidenced it instead.)

T255 states the applier *"proved that by refusing on its first run (`H-6`'s BEFORE was missing two
spaces of list-continuation indent)"*. **There is no applier transcript under
`.softhouse/capture/t255-dec2-rev8/evidence/`** — the six evidence files are the census, the P-5
probe, the anchors, the red drive, the collision and the obligation diff. So the refusal is a
narrated claim.

I verified the **property** instead, which is stronger than the anecdote. Perturbing one BEFORE by
a single space:

```
  REFUSE  H-5c §4.4 lead paragraph — the 35th site …  matched 0 times (need exactly 1)
NOT WRITTEN: 1 of 43 hunks did not match exactly once.
applier exit=1
```

and the file's sha256 is the **perturbed input's**, not a partially-applied hybrid — it refuses
**atomically**. An applier that could be satisfied by a near-match is how 43 hunks go wrong
quietly; this one cannot be.

### F-T260-5 — LOW. 38 sites in the LANDED document attribute corrections to a revision it says never landed.

`evidence/60-…`. Revision 8 says, correctly: *"**Revision 7** — task `T247`, **PREPARED AND
REJECTED. IT WAS NEVER APPLIED TO THIS FILE.**"* It then carries **38** `revision 7` mentions, of
which several read as operative statements about the file in front of the reader:

* §4.9: *"**⚠ REVISION 7 CORRECTS THE GROUND OF THIS BLOCK AND KEEPS ITS CONCLUSION.**"*
* §4.4 `I-1` cell: *"**REVISION 7 CORRECTS WHAT REVISIONS 1–6 SAID HERE**"*
* §4.4 rule paragraph, §5.3's note header, §5.1's scope note, §2.2's lead.

This **is** disclosed — §10's revision-7 entry says *"**Revision 8 carries revision 7's substance
forward in full**, which is why so much of the text above is marked *'CORRECTED IN REVISION 7'*:
the wording is revision 7's and the evidence behind it has been re-measured at `a71c140`."* So it
is not a fresh falsehood. But it is the same **self-identification** family as the *"DRAFT
(revision 5)"* defect this gate exists over: a reader who lands in §4.9 without reading §10 is told
a revision corrects a block that the same document elsewhere says was never applied. Advisory.

### F-T260-6 — LOW. "T251's C-1…C-8" is a misattribution. T251 issued C-1…C-6.

Searched `.softhouse/reviews/t251-dec2-rev7/CORRECTED-HUNKS.md` and
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T251.md` (P-66: that is where I looked):
T251 produced findings **F-T251-1…F-T251-5** and corrected hunks **C-1…C-6**. **`C-7` and `C-8`
appear in neither**; the labels originate in the driver's dispatch in `.softhouse/tasks.json`
("applying T251's C-1..C-8"). T255's handoff presents the eight as T251's numbering. The
*substance* T255 assigned to C-7 (§8.3's *"the seventh guard"* ×2) and C-8 (the `admit.go` /
`vector.go:77-81` ambiguity) is the right reading of what was left, and both are applied. Only the
attribution is wrong — and it is wrong in the driver's brief too.

### F-T260-7 — LOW. §5.3 publishes a `-P` recipe in a document whose rule 1 says `-F`, and it is not the recipe that was run.

§5.3(i) reads *"`git grep -P '\bP-5\b' -- nexus/internal/apps/ledger` returns nothing (exit 1, a
REAL measured negative…)"*. Rule 1, 2 000 lines earlier, says *"**`-F`, never a bare `grep` and
never `rg`** (`P-75`)"*. Separately, the **measurement was actually taken with Python `re`**, not
with the published command (`15-p5-probe.py` uses `re.compile(r"\b" + escape(token) + r"\b")` over
`git ls-files` output).

I ran the published recipe at `2f654ad`: `git grep -c -P '\bP-5\b' -- nexus/internal/apps/ledger`
→ **exit 1, no output**; positive control `\bP-4\b` → **exit 0, 2 files**. So `-P` is supported
here, `\b` discriminates, and **the published recipe reproduces**. No factual defect; a rule/recipe
inconsistency in a document about citation discipline, and a recipe/measurement mismatch worth one
sentence.

### F-T260-8 — LOW, not against T255. `gates.md` §G-14 still records a route the driver superseded.

G-14's register text reads *"What G-14 still does block: any amendment to DEC-2 other than the
**prepare-only** route `T247` is on, and `T247` may not land its own revision."* T255's dispatch
told it to *"Prepare **AND LAND** DEC-2 revision 8 in ONE fire"*. T255 landed on a **branch**,
did not merge, and does not ratify — which honours the substance. **The register has not been
updated to record the amended route.** The driver should record that when it closes G-14. I could
not edit `gates.md` (held by another task this fire).

### F-T260-9 — LOW, pre-existing, advisory. §10's revision-4 entry is in the present tense.

*"**NOT RATIFIED; `A2-28` is NOT AUTHORISED to ratify it and does not**"* and *"Gate **G-11 stays
OPEN — NOT RATIFIABLE**"* sit inside §10's revision-4 history entry, in a document that now records
G-11 as **CLOSED — RATIFIED**. Present in revision 7 verbatim; **not introduced by revision 8** and
outside its 43 hunks. It reads as a record, so it is advisory only.

---

## 3. C-1 … C-8 + the 35th site — APPLIED / NOT APPLIED / APPLIED WRONG

Numbering is T255's mapping of the driver's labels (see F-T260-6). Evidence:
`evidence/60-c-items-and-residuals.txt`, `evidence/70-spotcheck-stale-sites.txt`.

| | item | verdict | evidence I produced |
|---|---|---|---|
| **C-1** | every `.softhouse/conformance.sh:NNNN` citation | **APPLIED — by ELIMINATION, not re-measurement** | rev7 carried 13 such lines, rev8 carries 9. **I printed and classified all 9: every one is a HISTORY quotation of what a past revision wrote**, and rule-2's exemption covers them. **Zero LIVE `conformance.sh:NNNN` citations remain.** This is the correct disposition — re-measuring would have bought one cycle |
| **C-2** | `L821`, the `I-3` row — *"is the seventh guard `run_guards` invokes"*, whose *"Graded today?"* answer is **NO and still correct**, so no wording sweep reaches it | **APPLIED** | cell-by-cell: cells 1–4 of the `I-3` row are **byte-identical** (sha `a48ac995c372` / `db456ea9374c` / `4a4396ea577b` / `3b909e9cac89`); only cell 5 moved, and the change is the citation → ANCHOR plus a retraction. The answer *"NO BY A VECTOR"* is preserved. **The falsehood was in the supporting citation and that is exactly what moved** |
| **C-3** | §4.4.1's fenced enumeration listing **seven** and **omitting `guard_no_fail_open_instruments`** | **APPLIED, and made DERIVED** | rev7 **never mentions `guard_no_fail_open_instruments` anywhere in 3 039 lines** (0 occurrences — measured). rev8's fence lists all **eight in source order** and I re-derived that order from `run_guards()`' body and compared: **equal**. The fence carries a machine sentinel and is re-parsed by the checker |
| **C-4** | the ordinal — the COUNT went false, the ordinal did not, and revision 7 switched counting basis silently | **APPLIED — and this is the subtlest one, so I verified T255's specific claim** | (a) **the count is kept**, in one token: `[DERIVED: run_guards invokes 8 \| tallies 7 \| \`guard_ledger_invariants\` is invocation #7 and tallied #6]` — **exactly one such token in the document**; (b) **both counting bases are in it**, and the checker re-derives *both* (`invoked.index+1` vs `#7`, `tallied.index+1` vs `#6`) so the basis **cannot be switched silently again**; (c) **the ordinal is never used as an identifier in prose**: all 3 remaining *"the seventh guard"* occurrences are quotations inside retractions (rule 3, §4.4.1's retraction, §8.3's retraction), and 0 are assertions. **Claim VERIFIED** |
| **C-5** | §5's heading, *"and today that is ZERO vectors"*, asserting what H-12 retracts 26 lines below | **APPLIED** | `## 5. What DEC-2 would be frozen against — and today that is ZERO vectors` → `## 5. What DEC-2 **is** frozen against — and **(revisions 1–7) "**today that is ZERO vectors**"**` — quoted as a past claim, retraction immediately below |
| **C-6 / C-7** | §8.3's *"the seventh guard"* ×2 → the NAME | **APPLIED** | both replaced by `guard_ledger_invariants`, with the basis-switch named at the point of correction |
| **C-8** | `admit.go:139-147` **ambiguous between two packages**; `vector.go:77-81` is really `:78-82` | **APPLIED at the sites revision 8 rewrites; the class is NOT closed** | the ambiguity is **named** in the banner (*"named a BARE `admit.go` that exists in TWO packages"*, 1 occurrence) and the rewritten sites are anchored. But **38 bare `admit.go:N` / `vector.go:N` citations survive** (39 in rev7) — see F-T260-3. Disclosed as `FU-T255-2` |
| **35th site** | §4.4's lead paragraph, *"none of them can be graded today"*, nine lines above the bullet corrected to *"YES, SINCE A2-15"* | **APPLIED, and named as the 35th site in the document** | the string is gone (rev7 1 → rev8 0); §4.4's lead now reads per-invariant, and §10 records the near-miss with the sweep rule that would have caught it |

### The four LIVE stale sites neither prior review enumerated — spot-checked (brief asked for ≥2; I did all four)

Resolved with `git grep -n -F`, **status classified** (`P-80`), against blob `029439ba` — verified
by `git hash-object` to be the same file T255 measured:

* **`go test` pair.** T255 claims the numbers *and the count* were wrong — *"there are FOUR
  occurrences, all comments, not two"*. **REPRODUCED**: `git grep -n -F 'go test'` returns **4**
  lines (`:465`, `:853`, `:856`, `:1780`), **4 of 4 on comment lines, 0 non-comment**. `:718` and
  `:721` now point at `guard_no_float_in_harness` commentary — stale, as claimed. The replacement
  anchor `so a Go-test-only guard is not a` resolves to exactly 1 line (`:856`).
* **`-context` citation.** `:1254` now points at a comment about the `I-3`/`I-4` guard's detection
  classes. The replacement anchor resolves to exactly 1 line — **`:1934`**, i.e. the old number was
  680 lines stale. Correct.
* **`:401` / `:411`.** **Both still TRUE** at this blob (`:401` is `NEXUS_DIR="$REPO_ROOT/nexus"`,
  `:411` is `CMD_PKG="…"`) and converted to anchors anyway. I endorse that: a citation that is
  correct today and perishable tomorrow is the class being eliminated.
* **`FU-A2-25-2`'s harness comment — the `exit 1` is a REAL MEASURED NEGATIVE, not an error.**
  `git grep -c -F 'records as not existing' -- .softhouse/conformance.sh` → **no output, exit 1**.
  My probe **aborts on any status > 1** and prints stderr, so an error could not have been read as
  an absence (`P-80`). Calibrated in the same run: a negative control (`ZZQQ-T260-…`) returns
  0/exit 1 and a positive control (`run_guards`) returns 8 lines/exit 0 — so the search machinery
  was demonstrably working when it returned the negative (`P-35`). I additionally probed the
  **wider** phrase in case only the tail was reworded: `the I-3/I-4 SOURCE GUARD that DEC-2`
  **still exists** at `:1250` — so the comment was *edited*, not deleted, and the specific
  falsehood *"records as not existing"* is what was removed. **`FU-A2-25-2` CLOSED is correct.**

### Every anchor, resolved by the document's own recipe

`evidence/70-spotcheck-stale-sites.txt`: **ok 22 / ROT 0 / AMBIG 0 / ERROR 0** (all four terms
printed, `P-67`). Plus the two the checker cannot see (F-T260-1), resolved by hand: both hold.

---

## 4. THE MECHANISM — ruling on the argued-down checker wiring: **UPHELD (P-81).**

The driver suggested wiring a line-number checker. T255 measured that suggestion and rejected it.
**I attacked all four legs of its argument and all four hold.**

**(1) The denominator reproduces.** My independent count: rev7 carries **117** `path:NNNN`
citations, **26** Fineract-pinned, **91** repo-pointing, against T255's 115 / 25 / 90. The ~2 %
gap is a regex-definition difference (I count a Liquibase `.xml` and two `.json` citations T255
did not); reclassifying the one Fineract migration `.xml` gives **exactly 90 repo-pointing**.
`verify-line-numbers.py`'s citation row-list `SH_ROWS` is **exactly 4 rows** — read, not inferred.
So wiring it would have **enforced 4 of ~90 while reading as though it enforced all**: a `P-45`
shape (a control that must be remembered) and a `P-66` shape (a hand-written population that
answers a question about its author's memory) in one instrument. T255's own checker derives its
population from the document — which is right in principle, and F-T260-1 is where that principle
is 22/25 rather than 25/25 in practice.

**(2) The false-positive claim is not hypothetical — I reproduced it, and it is WORSE than T255
said.** `evidence/50-collision-and-red-drive.txt`:

| `conformance.sh` under test | revision 8's anchors | `verify-line-numbers.py`'s 4 citation rows |
|---|---|---|
| **`a71c140` — the untouched merge-base, no T253 at all** | **exit 0**, all hold | **3 of 4 MOVED**, exit 1 (`:1300` ok) |
| **CLOUD `origin/softhouse/T253-harness-portability`** | **exit 0**, all hold | **4 of 4 MOVED**, exit 1 — **including `:1300`**, the definition row that survived every prior pass |
| **MAC `softhouse/T253b-harness-portability-mac`** (net zero lines, in-place) | **exit 0**, all hold | **3 of 4 MOVED**, exit 1 (`:1300` ok) |

**The fact T255 did not measure and I did: a wired line-number gate would already have been RED on
`main`, at the merge-base, before T253 touched anything.** Three of the four rows were stale at
`a71c140`. That is a stronger argument for elimination than the one T255 made, and it disposes of
any suggestion that the false-positive rate is a T253 artefact.

**(3) The amnesty life-cycle citation checks out.** The anchor
`[ANCHOR .softhouse/conformance.sh :: \`THE PIN REMAINS A FRONTIER, NOT AN AMNESTY.\`]` resolves to
exactly 1 line. The harness does document that shape.

**(4) The regressions, named — because an honest mechanism review names them too.**

| change to the cited file | line number | ANCHOR | which is worse |
|---|---|---|---|
| **insertion above** (the dominant real case) | breaks **silently**, resolves to a plausible neighbour | **immune** | line number, decisively |
| symbol **renamed** | breaks silently | breaks **loudly** (0 matches, exit 1) | line number |
| **whitespace / reformat** of the cited line (`gofmt`, `shfmt`, one space) | **survives** if nothing shifts | **BREAKS** — measured: `() {` → `()  {` produces ROT | **ANCHOR is worse.** Mitigated: it fails loud, and `conformance.sh` is not formatted |
| **reflow** of a wrapped construct | survives if line count holds | breaks if the substring spans the new break | ANCHOR (low exposure: all 25 are single-line substrings) |
| file **renamed / moved** | breaks | breaks — the anchor's *path* is equally perishable | tie; neither binds to file identity |
| anchor becomes **NON-UNIQUE** | unaffected | **degrades at exit 0, unflagged** (F-T260-2) | **ANCHOR is worse, and this one is not named in the document** |

**Net: the ANCHOR wins on the failure mode that actually occurred three revisions running, loses on
two the document does not name.** The rule is right. The self-description is one sentence too
strong.

### Ruling on the HAND-RUN checker (`FU-T255-1`, HIGH, self-declared): **MERGEABLE, with a named condition.**

*"I wrote the wiring but could not install it"* does **not** pass as installed, and I am not
letting it. But refusing to modify `.softhouse/conformance.sh` — held by T253 this fire and not in
T255's `files_hint` — is **correct behaviour**, not a shortfall; three workers last fire caused
damage by doing the opposite. What makes it mergeable now is that the document's correctness does
not depend on the checker for the failure mode that has actually occurred: I resolved **all 25
anchors by hand** with the documented recipe and every one holds, uniquely.

**What must be filed, and by when:**

1. **Next fire, after T253 merges** — a task that wires `guard_dec2_citations` into `run_guards()`
   using T255's pre-written body. It must, in the same change:
   * **fix F-T260-1** — reconcile the literal `[ANCHOR ` count against the parsed count and REFUSE
     (exit 2) on a mismatch, so no citation is silently outside the population;
   * **regenerate §4.4.1's DERIVED fence**, because wiring adds a **ninth** invocation and the
     fence will then correctly fail — T255 names this consequence itself, which is the right way
     round;
   * carry a **negative control** proving the guard can go red, per `P-22`.
2. **F-T260-2 is the one text change I would accept in DEC-2**, and it is one sentence: rule 4's
   *"An anchored document is correct with nothing running at all"* should name the AMBIG case. **I
   may not make it (A2-17)**, and I do not think it is worth another prepare/review cycle on its
   own — the cycle is what made revision 7 stale. Fold it into the wiring task.

---

## 5. Self-identification and §10 — **CLEAN.**

* *"DRAFT (revision 5)"* appears **3 times** in revision 8, all historical: **L188** (the status
  block's own note that revisions 6 and 7 misidentified the document), **L3070** and **L3110**
  (§10's revision-8 and revision-6 entries). **No live status line claims DRAFT.**
* The live status line reads: **"Status: RATIFIED at revision 5; now at REVISION 8. 22 August
  2026."** with *"`T255` does not ratify its own revision and does not claim to."* Correct.
* **§10 records revision 6, the REJECTED revision 7, and revision 8, accurately.** I verified the
  commit references it cites: `8e8d65d` = *"G-13 CLOSED — DEC-2 revision 6 RATIFIED and LANDED;
  G-14 RAISED"*; `cab9e82` (revision 5) at **2026-08-22 14:24:56 +0800** and `1325e8b` (`A2-15`
  promotes six ledger vectors) at **16:37:56 +0800** — **exactly 2 h 13 m 00 s**, the figure the
  banner and G-14 both quote.
* Revision 7's entry states it was never applied and that revision 8 carries its substance — which
  is what makes F-T260-5 advisory rather than a defect.

---

## 6. T255's own instruments — checked BEFORE its conclusions

`evidence/80-instrument-audit.txt` (line level) and `evidence/85-instrument-audit-ast.txt`
(executable code only, strings and comments removed by `tokenize`).

**Known-bad shapes in EXECUTABLE code across all seven instruments: 0.** No bare `grep`, no `rg`,
no `|| true`, no `|| echo`, no bare `except:`, no `shell=True`, no `check=False`, no
`# lint-failopen: ok` hatch. The 27 line-level hits are all inside module docstrings or inside the
applier's hunk **string literals** — i.e. inside DEC-2's own prose, which legitimately contains the
words `grep` and `rg` because it is a document about them. Reporting those would have been the
fabrication class this program names.

Positive notes: `20-verify-anchors.py` uses `str.count` rather than a regex, so the
`\b`-reads-as-literal-`b` class cannot arise; it carries **both** a negative and a positive
calibration control and voids its own results if either fails; it reserves **exit 2** for "could
not do the job" and never prints it as an absence; and it prints **every** residual
`conformance.sh:NNNN` line rather than counting them. `15-p5-probe.py` carries a negative control
(`P-99`), a positive control (the nine siblings) **and** a discrimination control run in a
population containing both `P-5` and `P-50` — that is better than the standard.

Two small gaps: `55-real-t253-collision.py` has no negative control (it relies on the checkers it
invokes carrying their own), and `15-p5-probe.py` uses `subprocess` without reading `.returncode`
— but it passes `check=True`, so a non-zero status **raises** rather than being swallowed, which
satisfies `P-80`.

**Fail-open linter, verified independently.** T255 reports the population rising **918 → 924**
with **frontier 11 == pinned 11**. Confirmed by counting tracked `.sh`/`.py` per ref:
`a71c140` = **918**; `ed686d7` (the commit that lands revision 8 and six instruments) = **924**;
`b334786` (which adds the seventh) = **925**. So 924 is the right figure for the transcript T255
committed, and the +6 is exactly its instruments. T255's `80-bar-postcommit.log` L86–87 reads
*"inspected 924 tracked .sh/.py file(s) … frontier 11, pinned at 11"* and L91 *"frontier == pinned
(all 11 rows, by path)"*. **None of its instruments joined the frontier.**

---

## 7. THE BAR — run by me, at `2f654ad`. **Probe-line PRESENCE stated first.**

| | |
|---|---|
| **PROBE LINE PRESENT?** | **YES.** `/tmp/t260/bar.log` **L92**: `conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`, restated at **L101** `oracle probe UP`. **Presence read before value (`P-83`)** — exit 0 alone would not have told me the probe ran, four exit-2 paths precede it including a failed HARD guard, and exit 3 is a wrong-interpreter refusal. I invoked it as `bash .softhouse/conformance.sh`, not `sh` |
| **verdict** | **L506 `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.`** Process exit **0** |
| **ledger** | parity **PASS 4 FAIL 0** · oracle-refusal **PASS 2 FAIL 0** · inadmissible **0** · harness errors **0** · **70 cells graded, 21 MONEY in `int64` minor units** · kills named 6 money / 10 structural · invariants **0 violations, 11 non-vacuous assertions, 10 INDEPENDENT** · exemptions 0 declared |
| **`guard_ledger_invariants`** | `ledger-invariants: PASS`, `invariant violations 0`, with both `NIL-COVERAGE` lines and the full 8-item `CANNOT-CATCH` block printed — matching what §4.4.1 says it does and does not buy |
| **fail-open frontier** | **918 tracked `.sh`/`.py` inspected, frontier 11, pinned at 11, `frontier == pinned (all 11 rows, by path)`.** 918 not 924 because my review instruments are untracked at run time — which is the same `P-66` reason T255 re-ran post-commit |
| **vector store** | `git rev-parse HEAD:.softhouse/vectors` = **`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`** — identical at `a71c140`, at `softhouse/T255-dec2-rev8` and at `main` `b40f341`. **UNMOVED** |

---

## 8. Scope re-check (cheap, as instructed)

At `b334786`, diffed against merge-base `a71c140`:

* **`.softhouse/conformance.sh` is not in the diff** — 0 paths. Blob `029439ba…` at `a71c140`, at
  `softhouse/T255-dec2-rev8` and at `main` `b40f341`: **identical**.
* **`.softhouse/vectors/` is not in the diff** — 0 paths; `PIN-ledger.json` untouched at
  `dec2_revision: 5`, which is right: admission compares **vector to pin** and never reads the ADR.
* **Exactly three top-level paths touched**: `docs/adr/DEC-2-gl-accounting-adapter.md` (1),
  `.softhouse/capture/t255-dec2-rev8/` (19), `.softhouse/handoff/T255-dec2-rev8.md` (1).
* Revision 8 is **not on `main`**: `main:docs/adr/…` is blob `26a06ef3…` (revision 7);
  `softhouse/T255-dec2-rev8:docs/adr/…` is `fd5e5718…`. The review still gates the merge.

---

## 9. G-14 — the driver's paragraph

**`G-14` is closeable on this artefact, and nothing blocks closure.** The gate's recorded test is
*"does the pending correction change what a conformant implementation must DO?"* — and the answer,
re-derived independently by four legs of mine rather than read from T255's, is **no**: 140 of 140
table rows survive with only the last cell of four §4.4 rows moved and `I-7`'s `Idempotency-Key`
cells byte-identical; all ten §5.3 precondition rows, §4.2's predicates, §4.6's A-1…A-4, §4.10's
registry, §5.2's requirements 1–7 and §5.5's `graded_against` are untouched; §4.4's two welded
obligations survive verbatim and are strengthened; the caution survives and is widened; and the
whole +688/−185 reproduces byte-for-byte from 43 content-addressed hunks, so nothing was
hand-edited outside them. The banner that made this gate a gate is now true and stamped, the
document no longer misidentifies itself, and the rot **mechanism** is fixed rather than the numbers
patched — a claim I tested by taking `conformance.sh` out of both live T253 branches and finding
revision 8 indifferent to both while the line-number citations it replaced go 3-of-4 and 4-of-4
stale, and stale even at the untouched merge-base. **Ratify.** File two conditions on the
follow-up that wires the checker, neither of which is a reason to hold the artefact: the checker's
population is 22 of 25 anchors and the gap is silent (F-T260-1), and a non-unique anchor degrades
at `git grep` exit 0 while rule 4 claims the document is *"correct with nothing running at all"*
(F-T260-2) — the one sentence in revision 8 I would soften, folded into that task rather than spent
on another prepare/review cycle. `PIN-ledger.json`, the vector store and `conformance.sh` are
untouched; **CUTOVER, regulatory acceptance and parallel-run sign-off remain hard `user` gates and
nothing here moves them.**

---

## 10. What I could NOT verify (P-40 — the count of what I skipped)

1. **The 26 Fineract-pinned citations** — not re-opened at checkout
   `426a23544e8426a38ae43ae404670a0a7e85b9eb`. They are pinned and do not drift, and `A2-19`/`A2-25`
   audited 47/47 exact; I inherited that.
2. **The 38 surviving bare `admit.go:N` / `vector.go:N` line citations** — counted, **not
   re-measured for staleness**. T255 declines the same (`FU-T255-2`, `FU-T255-3`). Some are
   certainly stale by now.
3. **`T243`'s authorship of `guard_no_fail_open_instruments`** — not traced with `git log -S`. The
   guard **exists and is invoked** (verified); the attribution rests on the harness's in-file
   comment, which is a transcription. T255 marks this `[UNVERIFIED]` itself.
4. **Whether any §5.3 precondition is *adequately* discharged** — nobody has done this;
   `FU-T247-3` stands and revision 8 explicitly does not claim it.
5. **§9's 13 `[UNVERIFIED]` items** — §9 is byte-identical between revisions, so unchanged; I did
   not re-derive them.
6. **T255's `50-red-drive.py` and `60-obligation-diff.py` were read but not re-executed** — I built
   independent equivalents (`50-collision-and-red-drive.sh`, `20-normative-set-diff.py`) instead,
   which is the point of an independent review.
7. **`.softhouse/gates.md` could not be amended** (held by another task), so F-T260-8 is filed as a
   recommendation rather than fixed.
8. **My BAR ran at `2f654ad`, not at `main` `b40f341`.** The load-bearing invariants were
   re-measured at `b40f341` (§11) and none moved.

---

## 11. P-69 — re-measured at the end of the review

| fact | value | measured at |
|---|---|---|
| DEC-2 revision 8 blob | `fd5e571839aefea088c790e33da538922b1e69dd`, sha256 `09e456b8…`, 3 542 lines | `b334786` |
| DEC-2 on `main` (still revision 7) | `26a06ef348aabecc27c7dba0ed46c6d589d133d6`, sha256 `f02f7ff0…`, 3 039 lines | `b40f341` |
| `.softhouse/conformance.sh` | `029439ba6124ed10394554cf5ac9128cf3c42100` — identical at `a71c140`, `b334786`, `b40f341` | `b40f341` |
| `.softhouse/vectors` tree | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — identical at all three | `b40f341` |
| cloud T253 `conformance.sh` | `fd25b910…`, **67 insertions / 59 deletions** vs `029439ba` | `origin/softhouse/T253-harness-portability` |
| mac T253b `conformance.sh` | `ae803297…`, **10 / 10**, 2 617 → 2 617 lines, net zero | `softhouse/T253b-harness-portability-mac` |
| anchors resolving uniquely | **22 checkable + 3 literal (2 live, resolved by hand) = 25/25 hold** | `b334786` / `029439ba` |
| table rows changed, whole document | **4 of 140**, last cell only | `b334786` |
