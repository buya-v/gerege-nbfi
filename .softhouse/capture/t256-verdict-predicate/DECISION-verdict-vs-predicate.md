# T259 — Is the VERDICT field wrong, or is the PREDICATE misstated? The argued decision

**Task:** T259. **Branch:** `softhouse/T259-verdict-predicate`. **Model:** opus.
**Everything below is stamped to HEAD `a71c1408d3315493bca763472598680c85b9ad0b`** unless another
commit is named. Vector store at that commit:
`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — **not touched by T259**.

---

## 0. The ruling in one paragraph

**The PREDICATE is the broken half. The verdict field is not.** P2's third conjunct as registered —
`totalInterestAmount = n·E + B` — is arithmetically wrong; `n·E + B` is the total **repayment**
column, and the interest column is `n·E + B − principalRepaid`. `classify_t229.py`'s
`P2_totalInterestEqualsNEplusB` is a **correct measurement of an incorrect claim**. Making
`verdict` consult it, which is the obvious "fix", would print **three false REFUTED verdicts** on
cells where the registered law held to the minor unit. That is the losing side and it is stated in
full at §4. **But the verdict field is defective in a second, weaker, real sense**: it is named
`verdict` while grading only the §2 cell table, and nothing in the directory said so — so a reader
who saw `AS PREDICTED` beside `P2_…: false` had no way to tell whether the row was fine or the
summary was lying. The fix therefore lands in three places: the graded proposition is now
**written down** (`acknowledged.json:gradedProposition`), the disagreement is **acknowledged in
writing** rather than silently outranked, and a rule (**R-VPA**) makes any future instance
**impossible to print silently**.

---

## 1. The re-derivation, done before the driver's figure was accepted (P-69)

### 1.1 Where I looked (P-66/P-70)

| what | path | how |
|---|---|---|
| the recorded rows | `.softhouse/capture/t229-g8-site3/out/classify-t229.json` | read in full; recounted by `rederive_counts_t259.py` |
| how `verdict` is computed | `.softhouse/capture/t229-g8-site3/src/classify_t229.py` | read in full (91 lines) |
| what P2 registered | `.softhouse/capture/t229-g8-site3/PREDICTION.md` §2, bullet **P2** | read |
| the registered inputs | `.softhouse/capture/t229-g8-site3/prediction.json`, `src/cells-t229.json` | read |
| T241's correction | `PREDICTION.md` banner + `src/site3.py` banner (merged `d20836e`) | read |
| whether a manifest pins the bytes | `t177-so-nondeterminism/MANIFEST.sha256`, `tierA-a2/MANIFEST.sha256` | §5 |
| who else has the shape | all 1,499 JSON files under `.softhouse/capture/` | `census_verdict_shape.py`, §6 |

### 1.2 The count — mine, independently

`rederive_counts_t259.py` re-reads the bytes (sha256
`f831736f07f1a6fecd4ee69b5a1de8dac0abcae89210f997e72526070f62821a`, git blob
`2f740a8bd064fae24bb80a3e1da439dd73c2f72b` at HEAD `a71c140`) and reports:

```
rows in file                                   : 9
rows CARRYING  P2_totalInterestEqualsNEplusB   : 6
rows LACKING   P2_totalInterestEqualsNEplusB   : 3
... of the carriers, value false               : 5
... of the carriers, value true                : 1
... of the FALSE rows, verdict AFFIRMATIVE     : 3
... of the FALSE rows, verdict NEGATIVE        : 2
```

**The driver's "five and three" is CONFIRMED, exactly.** The five are `-B199`, `-B1450`, `-B251`,
`-B201`, `-B299`; the three affirmative ones are `-B251`, `-B201`, `-B299`, which is the driver's
list. Nothing to correct.

**One thing the driver's two numbers do not say, and this task should:** the key is **absent
entirely on three further rows** — `-B301`, `-B2150`, `-B303`, all `RESCUED_BY_SITE3`, all
`AS PREDICTED`. `classify_t229.py` computes the P2 block only `if p["predictedOutcome"] !=
"RESCUED_BY_SITE3"`. That is correct and deliberate (P2 is scoped "on every unrescued cell"), but
it means the denominator is 6, not 9 — so "five of nine rows" would be the wrong sentence, and
"five of the six rows that carry the key" is the right one. Both terms counted (P-67).

### 1.3 How `verdict` is ACTUALLY computed, and which predicates it reads

From `src/classify_t229.py`, verbatim:

```python
    pp = p["predictedTotalPrincipalMinor"]
    if p["predictedOutcome"] == "RESCUED_BY_SITE3":
        row["verdict"] = "AS PREDICTED" if obs.startswith("AMORTIZES_FULLY") else "REFUTED"
    else:
        ok = (obs == p["predictedOutcome"] if p["predictedOutcome"].startswith("FAMILY_B")
              else obs.startswith("AMORTIZES_FULLY"))
        ok = ok and row["observedPrincipalMinor"] == pp
        row["verdict"] = "AS PREDICTED" if ok else "REFUTED"
    # P2: ...  on unrescued cells only
    if p["predictedOutcome"] != "RESCUED_BY_SITE3":
        row["P2_emiDifferenceEqualsB"] = ...
        row["P2_emiObservedEqualsPredicted"] = ...
        row["P2_totalInterestEqualsNEplusB"] = ...
```

**`verdict` reads exactly two things:** the observed OUTCOME family against `predictedOutcome`,
and `observedPrincipalMinor == predictedTotalPrincipalMinor`. It reads **no `P`-prefixed
predicate**, and it **cannot** — every one of them is assigned *after* `verdict` is already in the
row. `P1` and `P3`–`P6` are not even computed per row. So the answer to "which predicates does
`verdict` read?" is: **none of the registered P-predicates. Zero.**

Those two things it does read are precisely the two graded columns of `PREDICTION.md` §2's
nine-cell table ("**T229 predicts**" and "principal (minor)"). So the field is not incoherent — it
computes a well-defined proposition. It just is not the proposition its name implies.

### 1.4 The measurement that decides the case

`rederive_counts_t259.py` also re-derives, per row, in integer minor units only, the **corrected**
third conjunct `totalInterest == n·E_observed + B − principalRepaid`:

| row | registered P2₃ | **corrected** P2₃ | verdict |
|---|---|---|---|
| `T229-R600p0-N200-B199`  | false | **false** | REFUTED |
| `T229-R36p0-N1400-B1450` | false | **false** | REFUTED |
| `T229-R600p0-N200-B251`  | false | **true**  | AS PREDICTED |
| `T229-R600p0-N200-B201`  | false | **true**  | AS PREDICTED |
| `T229-R36p0-N1400-B150`  | true  | **true**  | AS PREDICTED |
| `T229-R600p0-N200-B299`  | false | **true**  | AS PREDICTED |

> **Under the REGISTERED predicate, predicate and verdict agree on 3 of 6 carriers.
> Under the CORRECTED predicate they agree on 6 of 6 — perfectly, in both directions.**

That is the whole argument in one table, and it is measured, not asserted. A field that is
"deliberately tracking a different proposition" would be expected to disagree with a *correct*
predicate somewhere. This one does not disagree anywhere. The disagreement was manufactured
entirely by the arithmetic slip in the registered claim.

---

## 2. The decision

**The registered predicate P2, third conjunct, is WRONG. The `verdict` values stand, all nine of
them.** No row in `classify-t229.json` needs its verdict revised, and no cell of T229's
registered law is refuted by this.

Corollary, and the part that is genuinely a verdict-side defect: **`verdict` grades the §2 cell
table and nothing else, and until T259 that fact was written down nowhere.** It is now written
down, in `acknowledged.json` under `gradedProposition`, and R-VPA prints it beside every
disagreement it reports.

---

## 3. Why this is not T241's finding restated

T241 established that the **formula** `predictedTotalInterestMinor` is mislabelled, and annotated
`site3.py` and `PREDICTION.md`. T241 explicitly did not expand scope to the verdict field.

T259 adds three things T241 did not:

1. **Which half is broken, argued and measured** (§1.4). T241 said "P2's other two conjuncts
   STAND"; it did not settle whether `verdict` should have consulted P2. The 6/6-vs-3/6
   concordance table settles it — and settles it *against* the intuitive answer.
2. **A rule instead of a note.** T241's correction is prose in two files. Prose does not fire on
   the next capture. R-VPA does.
3. **A second, previously unreported instance** (§6): `classify-t219.json` carries the same shape
   on **three distinct rows / four predicate-verdict pairs**, and appears in no handoff either.

---

## 4. THE LOSING SIDE, stated in full

The rejected reading is: **"`verdict` is the broken half; it should be the conjunction of every
registered predicate the row computed, so `AS PREDICTED` over `P2_…: false` is simply a false
verdict."** It is a serious position and here is the strongest case for it:

- P1–P6 are introduced in `PREDICTION.md` under the heading *"Also predicted, and stated so it can
  fail"*. Something registered so it can fail, that then fails, and is then reported as having not
  failed, is on its face a broken verdict, whatever the arithmetic behind it.
- The word `verdict`, unqualified, in a file whose only purpose is to grade a registered
  prediction, does claim the whole prediction. Names are part of the interface.
- The pattern library is full of guards that "computed the right thing and reported the wrong
  thing" (P-22, P-45). Choosing the reading that leaves the summary line intact is exactly the
  move that lets those survive, so the prior should be against it.

**Why it loses, on the evidence and not on preference:**

1. **It would print three FALSE REFUTATIONS.** Under it, `-B201`, `-B251`, `-B299` become REFUTED.
   All three had the predicted family AND the predicted principal to the minor unit (1, 51, 99 —
   numbers PREDICTION.md says "no rule anyone has written predicts at all"). Recording a
   successful novel prediction as a refutation because the *predictor's* arithmetic was wrong
   elsewhere is a worse error than the one being fixed, and it is not reversible by a later reader
   who only sees the REFUTED.
2. **The disagreement vanishes under the corrected predicate — 6/6, both directions (§1.4).**
   If `verdict` were tracking some genuinely different proposition, a corrected P2 would still
   disagree with it somewhere. It does not, anywhere. There is one error here, not two.
3. **A conjunction is only as sound as its weakest conjunct.** ANDing an unaudited predicate into
   the verdict makes every future arithmetic slip in a predicate into a fabricated refutation. The
   asymmetry matters in this program: a spurious REFUTED on a *rescue-region* cell is exactly the
   kind of artefact that would put pressure on G-8's region boundary, and G-8's boundary must move
   only on real evidence.
4. **It is unimplementable without breaking T114/T176 anyway.** `verdict` is written by
   `classify_t229.py`, which produced committed evidence at `bb35cc8`. Changing what it computes
   means either retro-editing that script (prohibited) or writing a successor — and a successor
   that ANDs in a predicate now known to be wrong is not worth writing.

**What the losing side is RIGHT about, and which is kept:** the unqualified word `verdict` did
overclaim, and a false predicate beside an affirmative verdict must never again be silent. Both
are addressed — by declaring the graded proposition and by R-VPA — without adopting the fix that
would have produced the false refutations.

---

## 5. T114/T176 — the manifest check, done before choosing the route (as T236 did)

**Question: do the bytes of `classify-t229.json` or `site3.py` sit under a manifest?**

| manifest | mentions `t229-g8-site3` | rc |
|---|---|---|
| `.softhouse/capture/t177-so-nondeterminism/MANIFEST.sha256` | **0** | 1 — a REAL measured negative, not an error (P-80) |
| `.softhouse/capture/tierA-a2/MANIFEST.sha256` | **0** | 1 — same |

And `git grep -F f831736f07f1a6fe…` (the file's own sha256) over the whole tracked tree returns
**rc 1 — no tracked file records it**. So: **no manifest pins these bytes.** Note the caution the
brief raised: `manifest.py verify` under `tierA-a2/` was silently RED across two merges, so a
manifest's *silence* proves nothing — but this is not silence, it is **absence of coverage**, which
is a different and weaker fact and is recorded as such.

**Consequence for the route.** Since no manifest pins them, nothing mechanical would have caught a
retro-edit. The bytes were protected only by convention and by git history. **T259 therefore adds
the pin that was missing**: `acknowledged.json` records `sha256
f831736f07f1a6fecd4ee69b5a1de8dac0abcae89210f997e72526070f62821a`, and R-VPA voids the whole
acknowledgement block and turns the rows RED if a single byte changes. Driven red twice
(`Va-byte-pin-whitespace-only-mutation` on a **whitespace-only** change, `Vb` on a semantic one).

**Route chosen: labelled sidecar, zero edits to the evidence.** `classify-t229.json`,
`classify_t229.py`, `prediction.json`, `cells-t229.json` and `site3.py` are **untouched by T259** —
see §7.

---

## 6. What R-VPA is, and the tail it found (P-78 applied to my own fix)

**R-VPA:** a row may not carry an affirmative verdict over a predicate it recorded as false,
unless a sha-pinned acknowledgement says why. Fail-closed in four directions — an unrecognised
verdict word, an unregistered boolean key, and a nil population are all **refusals**, and
acknowledgements are pinned to bytes. Full statement in the module docstring of
`check_verdict_predicate_agreement.py`; red-driven in `red/drive-red.sh` (14 legs, 14 pass).

**P-78 says: after you register a prediction, grep for who READS it.** Applied to T259's own fix,
via `census_verdict_shape.py` over **1,499** JSON files under `.softhouse/capture/`:

- **12** files carry the classification shape; **1,451** do not; **36** were skipped as
  unparseable (raw gzip/NDJSON captures) and are counted, not waved past (P-40).
  [figures as printed in `run-output.txt:139-159`, the committed transcript]
- **8 disagreements total.** Three are T229's known rows. **Four are in
  `.softhouse/capture/t219-g8-residual/out/classify-t219.json`** — rows `T219-R600p0-N103-B1`
  (two predicates), `T219-R600p0-N3000-B4499`, `T219-R600p0-N3000-B3001`. One is T259's own
  deliberate red fixture.
- `t219-g8-residual/` is **outside T259's write scope**, so it is measured, reported, and
  **left exactly as it is**. Backlog item B-1 in the handoff.

**And the honest half of P-78, about T259 itself:** *nothing currently reads R-VPA's output
automatically.* `.softhouse/conformance.sh` is held by T253 this fire and T259 may not touch it.
`run.sh` exists and exits non-zero on refusal, but no probe line invokes it yet. Until it is wired,
R-VPA is in exactly the condition it was written to condemn — a measurement nobody reads. That is
backlog item B-2, and it is named here rather than left to be discovered.

---

## 7. Materiality — LOW, and verified rather than asserted

**Nothing moves.** Specifically:

- **No verdict moves.** All nine `verdict` values in `classify-t229.json` stand. T259's ruling is
  that they were already right.
- **No vector moves.** `git rev-parse HEAD:.softhouse/vectors` =
  `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at the start and at the end of this task. T259 writes
  no file under `.softhouse/vectors/`.
- **G-8's region boundary is untouched.** T259 read `gates.md` for context and wrote nothing to it.
  It proposes no change to the region, to the conservative superset `B_minor < 1.5·n`, or to the
  status of the unproven conjecture `δ ≤ 1`. **G-8 options (b) and (c) are not raised, not
  referenced as live, and not put to Buyan — unconditionally and with no expiry.**
- **No gate conclusion moves.** Nothing in `.softhouse/gates.md` reads
  `P2_totalInterestEqualsNEplusB`; `gates.md` already carries the CORRECT interest form (T241
  established this and it was re-checked here), so the live text was never wrong.
- **No promoted figure, no oracle capture, no Go code, no `nexus/**` file is involved.**

**What DOES change:** four sidecar files and a rule, plus the fact that a fifth thing —
`classify-t219.json` — is now known to carry the same shape. The value of this task is the
**shape**, not the blast radius, and inflating a hygiene finding is itself a defect in this
program.

**What it does NOT establish:** that any other verdict in the corpus is correct; that P1, P3, P4
or P5 were ever evaluated (they were not — see §1.3); that the calibration statuses are consulted
by anything (they are not); or anything whatsoever about parity, cutover, or the Go port.
