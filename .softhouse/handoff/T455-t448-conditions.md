# T455 — T448's conditions on T433

Branch `softhouse/T455-t448-conditions`. Fork point `cbc8733c` (= `main` at dispatch).
Scope worked: `.softhouse/reviews/A2-11/`, `.softhouse/capture/t393-t382-conditions/`,
`.softhouse/capture/t455-t448-conditions/`, plus **one disclosed edit outside them** (§9).

Everything below was **re-derived here**. Where a number came from T448 and was not re-measured,
it says so by name.

---

## 1. DISPOSITION, ITEM BY ITEM

| id | severity | disposition |
|---|---|---|
| **C-T448-1** | **MAJOR** | **CLOSED.** The `(iv-a)` fail-open is closed inside the shipped grader, driven both ways, with the clean-tree control green. The DETECTION half is not closed and is named. |
| **C-T448-2** | MINOR | **CLOSED**, and the supplied repair was **corrected**: it closes (C) and does **not** close (B). Two predicates shipped, both driven RED. |
| **C-T448-3** | MINOR | **CORRECTED.** The reason was false; the decision was right. The real reason is recorded, and the defect it deferred is fixed here anyway. |
| **C-T448-4** | MINOR | **CORRECTED and F-5 CLOSED.** 11 cases, 22 rows, 9 argued, 9 grader runs — each measured from two artefacts. |
| **C-T448-5** | LOW | **MEASURED.** 11 pre-existing files / 14 pre-existing lines at T433's tip, reproduced under a primitive that is not `git grep`, **with the list printed beside the count**. |
| **C-T448-6** | LOW | **CLOSED.** The footer is now emitted inside the teed block, and section 10 fails if `run-all.sh` stops emitting it. |
| **F-6** | — | **FIXED AT THE SEARCH.** `run-all.sh` goes **EXIT 1 → EXIT 0**; section 9 goes **1 → 0**; the adjudicated pin `sec 9 0` is byte-identical at both refs. |
| **F-3** | — | **CLOSED** on T448's four drives, recorded in the grader's docstring and attributed to T448. Not re-driven — it is settled, and re-running a settled measurement is the same derivation twice. |

---

## 2. C-T448-1 (MAJOR) — the `(iv-a)` fail-open is CLOSED, and only the fail-open

T433 wrote — kept verbatim and tagged, in the grader's docstring and in `run-all.sh`'s banner:

> `[QUOTED-FALSE-CLAIM]` "Not closable by internal consistency — a fabricated observation is a
> `[QUOTED-FALSE-CLAIM]` claim about the oracle, and only the oracle can refute it."

**Two problems, one sentence.** *Detecting* a fabricated capture is external; T433 is right about
that half, and the anchor is now NAMED rather than left blank — **re-observation against the
pinned reference oracle (Fineract), digest-recorded**, the procedure T357 already ran for the four
`obs/` files on fire `20260828-140005`. *Refusing to exit 0 over a population the arm did not
measure* is internal, and **`verify-capture-integrity.py` already stated that rule** nine lines
above the born-at-tip branch, for the sibling `f_noborn` case: *"An arm that could not measure part
of its own population has not passed on it. REFUSED, never a pass."*

**Landed** in `verify-capture-integrity.py`:

* section 8 now digests each born-at-tip file and routes it through
  `ARM_F_BORN_AT_TIP_ADJUDICATED` (name → sha256 — a name-only table would let the bytes be
  swapped afterwards);
* **section 9 asserts `not f_at_tip`**, plus a MOVED check so a stale entry is a failure too;
* the PASS verdict no longer describes a non-zero born-at-tip count as a survivable boundary.

**DRIVEN BOTH WAYS, EIGHT CASES** — `instruments/20-t455-iva-close-drive.sh`,
`out/20-IVA-CLOSE-DRIVE.txt`, **exit 0**:

| # | case | ref | grader |
|---|---|---|---|
| 1 | clean tree — **calibration** | BEFORE | **0**, 632 graded, 0 at tip |
| 2 | fabricated observation born at the tip, manifest laundered | BEFORE | **0** — the fail-open, reproduced |
| 3 | the same tree | AFTER | **1**, on the named assertion, ×1 |
| 4 | `(iv-b2)` rename + whole rewrite | BEFORE | **0**, 1 at tip |
| 5 | the same | AFTER | **1**, same named assertion |
| 6 | **clean tree — THE CONTROL** | **AFTER** | **0**, pop 632, graded 632, at-tip 0 |
| 7a | the fabricated capture ADJUDICATED by name+digest | AFTER | **0**, named as adjudicated |
| 7b | its adjudicated BYTES then changed | AFTER | **1**, `BORN-AT-TIP ADJUDICATION MOVED` |

**Case 6 is the one that matters.** The close costs nothing: same exit code, same graded count as
the BEFORE control. A close that reddens honest trees is a freeze. **Cases 7a/7b are mine, not
T448's** — an adjudication list that could only ever say *yes* would be the fail-open re-spelled,
so the table is falsifiable in both directions before it is trusted.

**What is still open, stated so it cannot be read as closed:** a fabricated capture added at the
tip is **not detected** by this file. Nothing internal can detect it. What it can no longer do is
report it as a PASS.

---

## 3. C-T448-2 (MINOR) — the tag guard, repaired INSIDE the grader, and a correction to the repair

**Where it landed.** Not in a capture-directory guard — in **section 10 of
`verify-capture-integrity.py`**, which `run-all.sh` adjudicates as `sec 10 0`. P-45: a guard beside
the thing it guards enforces nothing. It is the same decision T433 got right about ARM F.

**RE-DERIVED, AND THE RE-DERIVATION FOUND SOMETHING.** T448 supplies

```
both="$(grep -Ei "$IMPOSS" "$f" | grep -c "QUOTED-FALSE-CLAIM")"
all="$(grep -Eic "$IMPOSS" "$f")" ;  [ "$both" -ge 1 ] && [ "$both" = "$all" ]
```

and states that case B fails it with `all` = 2, `both` = 1. **It does not.** The smuggled line
carries the tag in its trailing comment, so both greps count it: `all` = `both` = **2**, and the
predicate **PASSES**. Measured, as its own assertion, in `out/30-TAG-BINDING-DRIVE.txt` case B.
The review's own "add a third assertion that reads the output" is the part that actually closes B;
the one-predicate repair alone does not.

**A second thing the review's predicate misses: line wrapping.** A quotation of any length is
wrapped across source lines, so a line-oriented matcher cannot bind a tag to the text it tags.
Measured on `10-drive-conditions.sh`, whose tagged block splits the sentence at *"…has no /
baseline older than HEAD anywhere…"*: **no line carries the claim**, so a line-wise search scores
it 0 stated / 0 tagged — **indistinguishable from abuse (C), where the quotation is gone
entirely.** That is why the shipped predicate de-wraps contiguous tagged blocks.

**The two shipped predicates:**

1. **BINDING** — no *untagged* line states a false claim (T433's half, kept), **and** at least one
   **de-wrapped tagged block** still contains a claim verbatim. Closes (C).
2. **PRINTED** — every payload the tooling actually **emits** (`echo …` / `print(…)`, with
   out-of-quote trailing comments stripped) that states a claim must carry the tag **inside the
   payload**. Closes (B).

Plus the positive half (each corrected file still says what the baseline IS), a vacuity control
(at least one tagged claim is actually emitted, so predicate 2 has a population), and **four
in-memory self-drives** so the classifier is seen to accept a correct quotation, accept a wrapped
one, and reject both abuses, on every run.

**DRIVEN** — `instruments/30-t455-tag-binding-drive.sh`, **exit 0**:

| case | shipped section 10 | T433's own tag predicates | T448's one predicate |
|---|---|---|---|
| A control | **0** | green | PASS |
| B live echo, tag in a trailing comment | **1**, on PREDICATE 2 (and *not* on 1) | **both defeated** | **PASS — defeated** |
| C quotation deleted, 3 bare tags | **1**, on PREDICATE 1 | **positive half defeated** | FAIL — closed |
| D replacement text removed | **1**, on the POSITIVE half | — | — |
| E footer marker removed | **1**, on the footer assertion | — | — |
| **B0 / C0** — the same two abuses at `BEFORE`, where nothing can rescue T433's guard | — | **guard EXIT 0 on both** | — |

**B0/C0 exist because of a mistake I made and had to correct.** My first draft read T433's guard's
**exit code**. At my ref that guard exits 1 on B and C — but *transitively*, because it also RUNS
the shipped grader, which now catches them. Reading the exit code would have recorded "T433's
guard catches abuse B", which is false about the predicate under discussion. The drive now measures
the guard's **own assertions by name**, and B0/C0 reproduce T448's literal claim (**guard EXIT 0**)
at a ref with no section 10 in it.

---

## 4. C-T448-3 (MINOR) — the deferral reason was false; the real one, and the defect, both here

T433's handoff and `50-t433-runall-f1-13b-row.sh` treat section 9 as out of reach. **It is not:**
`adjudicate-section1.py` sits at `.softhouse/reviews/A2-11/adjudicate-section1.py`, and
`.softhouse/reviews/A2-11/` is one of T433's two `files_hint` entries — T433 edited three other
files in that same directory. Verified here against `.softhouse/tasks.json`.

**The decision was right and the reason was wrong.** The true reason: repairing section 9 needed a
**materiality adjudication** — does A2-11 F-1's wire-shape finding now touch a graded vector? —
which is a different question with a different risk profile from landing ARM F, and widening T433's
task to include it would have made one diff carry two unrelated arguments. *"Outside my assigned
paths"* is a load-bearing sentence in this pipeline; it is graded, and it gets copied forward.

That adjudication is made below, and the defect is fixed.

---

## 5. F-6 — the search was fixed. THE PIN WAS NOT MOVED.

**Re-derived, not inherited.** T433 found `run-all.sh` red on an unmutated `main`; T448 bisected it
to `25a8b7de` (T391) and called it a false positive. I re-derived the *cause* by reading **every
hit** rather than re-running the bisect (a second run of the same walk is not a second derivation):

| token | where it occurs | shape |
|---|---|---|
| `paymentChannelToFundSourceMappings` | `capabilities-ledger.json` `$.capabilities[6].evidence` | prose sentence |
| `feeToIncomeAccountMappings` | same field | prose sentence |
| `penaltyToIncomeAccountMappings` | same field | prose sentence |
| `loanproduct` | same field, plus `$.provenance.citation` in `LDG-ACC-01/02/03` | prose sentences |

**Seven occurrences, all inside JSON string values that are sentences**, and the sentences say in
terms that the capability is still UNGRADED and that product 63 has none of these mappings. The
check's claim is about the **graded corpus**. A sentence *about* a token is not a graded cell.

**The repair is structural, and it is intrinsic rather than a name-list.** The arm now parses each
JSON vector and classifies each occurrence:

* **KEY** — the token is (inside) an object key → **MATERIAL**;
* **VALUE-ID** — the token is inside an **identifier-shaped** value (no whitespace: a ref, a path,
  a code — the shapes the harness compares against the reference oracle) → **MATERIAL**;
* **PROSE** — the token is inside a value that is a sentence → **IMMATERIAL, counted and printed**.

A file that will not parse as JSON, and every non-JSON file, keeps the raw substring search and any
hit is **MATERIAL**: unparseable fails **closed**, never skipped. `conformance.sh` keeps the raw
search too, **and that limit is stated at the site** — a token written into a *comment* there would
redden this arm for exactly the reason the vector store just did. Fail-closed, but the same class.

**DRIVEN BOTH WAYS** — four new negative controls in the file's own section 5: (h) a token as a KEY
is MATERIAL; (i) as an identifier-shaped VALUE is MATERIAL; (j) inside a PROSE sentence is not, and
is counted; (k) an unparseable file is MATERIAL. A classifier with only (j) would be a hole; with
only (h)/(i) it would be the false positive it was written to remove.

**MEASURED, whole runner, both refs** — `instruments/10-t455-runall-and-footer.sh`,
`out/10-RUNALL-AND-FOOTER.txt`, **exit 0**:

| | `run-all.sh` exit | deviations | section 9 | section 10 |
|---|---|---|---|---|
| **BEFORE** (`cbc8733c`, unmodified) | **1** | 1 | **1 — `*** MOVED ***`** | 0 |
| **AFTER** (this branch) | **0** | 0 | **0** | 0 |

And the pin: `sec 9 0 python3 "$DIR/adjudicate-section1.py"` is present ×1 at **both** refs. A green
bought by moving a pin would show there.

---

## 6. C-T448-4 — the cardinals, and F-5

`instruments/40-t455-cardinals.sh`, **exit 0**. Every number from **two artefacts**, and the
instrument **exits 1 if they disagree**.

| T433 restated | **measured** | derivation |
|---|---|---|
| 13-case matrix | **11** | `grep -c '^run_case '` on the SOURCE **and** distinct case names in the committed `MATRIX.tsv` (the OUTPUT) — 11 and 11 |
| — | 22 data rows = 11 × 2 refs | `MATRIX.tsv` |
| 26 `run-all.sh` runs | **9 grader runs** | only the AFTER column can move; the column the matrix grades is one command's exit code |
| eleven argued | **nine** | 11 − `control` (calibration) − `f1-13b` (driven) |

**F-5 CLOSES AS MEASURED.** T448 ran all nine against the grader with ARM F present and all nine
reproduced T393's committed value (`out/50-F5-ARGUED-ROWS.txt` in T448's review). T433's
*conclusion* holds; its *cost estimate* was out by ~3×, and that estimate is what made it abandon a
re-run it could afford. **I did not re-drive the nine** — they are settled, and a third run of the
same measurement is not a third derivation.

Corrected in the in-grant record: `.softhouse/capture/t393-t382-conditions/out/T433-CORRECTION.md`,
with the wrong numbers **quoted, not deleted**.

---

## 7. C-T448-5 — the invoker figures, measured, with the list beside them

The **"17"** does not appear in T433's handoff. It is the **dispatch brief's** figure — a
driver-supplied cardinal echoed back as a finding — and it is the line count of a `grep` block with
no definition attached. So the definition is stated **before** the count: an *invocation line* is a
tracked, non-`out/` line in a `.sh`/`.py` that either runs the grader or binds its path for later
execution; a line that names it inside a quoted assertion string is a *mention*.

**Two legs that do not share a primitive:** `git grep` (git's own pathspec + regex engine) and a
python walk of `git ls-files` that never invokes `git grep`. They agree on every figure.

| measured at | invoking files | invocation lines | bare mentions |
|---|---|---|---|
| **T433's tip `3253358d`** | **14** | **18** | 45 |
| …of which T433's own instruments | 3 | 4 | — |
| **⇒ PRE-EXISTING** | **11** | **14** | — |
| this branch's tip | 22 | 33 | 69 |

**T448's 11 / 14 is confirmed**, by a decomposition the instrument computes rather than a total
someone edited by hand. Exactly **one** invocation is ADJUDICATED (`sec 10 0` in `run-all.sh`), and
that is the one P-45 is satisfied by. **The limit is stated:** both legs search `.sh` and `.py`
only; a future invoker in another language would be invisible to both, and that is a measurement
which goes stale, not a fact.

---

## 8. C-T448-6 — the footer is emitted, not appended

`run-all.sh`'s body is `{ … } | tee`, which truncates. Measured at `BEFORE`: T433's appended footer
greps **1 before the run and 0 after** — erased by the script it documents, with nothing asserting
it. The repair is **not** to re-append it: the footer is now **printed inside the teed block**, so
it is reproduced by construction (measured at AFTER: 0 before, **1** after), and **section 10 fails
if `run-all.sh` stops emitting it** (drive case E). A transcript cannot guard itself, so the
assertion lives in the grader.

`TRANSCRIPT-A2-11.txt` **is regenerated in this branch**, for the first time since T433 — because
it now **PASSES**. `sections run: 10  deviations: 0  RUN-ALL VERDICT: PASS`. T433 was right not to
commit a failing transcript over a review record; that reason has expired.

---

## 9. THE ONE EDIT OUTSIDE MY THREE DIRECTORIES, DISCLOSED BY NAME

`.softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh` — **two `want` → two
`want_min`**, nothing else.

Both were **exact-count** pins that my additions moved on a **clean tree**: a second mention of
`UNGRADED-BORN-AT-TIP` (the re-adjudication instructions for the new table) and two more of the
replacement sentence (section 10's `CORRECTED` table and its self-drive fixture). The claim those
two assertions make is **presence**, and it is unchanged.

**The file's own comment prescribes this fix**, nine lines above the first of them: *"A minimum,
never an exact count: P-29, a count is a weak tripwire and pinning one here would go red on a
comment being reworded, which is how a guard gets deleted rather than fixed."*

The two alternatives were worse: suppress the new mentions to satisfy a count (tuning the artefact
to the tripwire), or ship a tracked guard that is **RED on a clean tree** — the exact defect I was
sent to fix in F-6. Measured after the repair: the guard is **EXIT 0** on the control at this tip
(drive case A), and **EXIT 0** on the unmutated tree at `BEFORE` (case B0), so the change is not
load-bearing for any verdict in this handoff.

---

## 10. WHAT I COULD NOT CLOSE

* **The DETECTION half of `(iv-a)`.** A fabricated capture added at the tip with a laundered
  manifest row is still not *detected* by `verify-capture-integrity.py`, and cannot be — the file
  is offline by construction. The anchor is named at boundary `(iv-a-anchor)`: re-observation
  against the pinned reference oracle (Fineract), digest-recorded. **F-2 stays open, with its
  scope reduced to the half that is actually open.**
* **T433's own record.** `.softhouse/handoff/T433-t423-c1.md` (F-5's "13-case"/"eleven", F-2's
  "not closable", F-6's false deferral reason) and
  `.softhouse/capture/t433-t423-c1/instruments/50-t433-runall-f1-13b-row.sh`'s header still carry
  the wrong cardinals. Both are outside my grant; the corrections are recorded in
  `T433-CORRECTION.md` and here. **Filed as a follow-up.**
* **F-4 — `conformance.sh` still does not invoke this chain.** T454 holds that file this wave.
  Unchanged by me and unchanged by T433; the exact line to add is in
  `.softhouse/capture/t433-t423-c1/out/FOLLOWUP-conformance-line.md`. **Still open.**
* **T448's own instrument `30-t448-tag-abuse.sh` records `all=2, both=1` for case B.** That is
  wrong (§3). It is in `.softhouse/reviews/t448-review-t433/`, outside my grant, and reviews are
  append-only records of a reviewer's reasoning. **Recorded, not edited.**
* **The `conformance.sh` half of section 4's search** is still a raw substring match, so the same
  false-positive class can recur there. Stated at the site; fail-closed, so it demands a human
  rather than passing silently.
* **The `.sh`/`.py` limit** on the invoker enumeration (§7).

---

## 11. THE BAR, AND THE RUNNER

Run from `/tmp` — scratch **outside** the repository — `bash`, never `sh`/`zsh`, on a **committed,
clean** tree. `git status --porcelain` was 0 lines before and after.

```
BAR EXIT 0
grep -c 'probe = '  ->  1   (PRESENCE tested BEFORE the value was read: four exit-2 paths run
                             before the probe prints, and ABSENCE IS NOT `down`. P-84.)
probe line, verbatim:
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
fail-open frontier : 11, pinned at 11, frontier == pinned
dead-path census   : deadOccurrences 108
```

`bash .softhouse/reviews/A2-11/run-all.sh` — **EXIT 1 → EXIT 0**, section 9 **1 → 0**, all ten
sections as adjudicated, deviations 0.

---

## 12. ONE PARAGRAPH FOR THE NEXT READER

The task existed because T433 wrote *"not closable"* about a fail-open that closes with one
`check()` at zero cost — the same shape as the *"there is no baseline"* it was sent to correct.
Landing that check was the easy half. The instructive half is that **the guard caught its own
author three times**: section 10 failed on my own test fixtures because they asserted the false
claim untagged, then on a banner line I wrote that re-asserted it in an `echo`, and the wiring guard
went red because I had added a mention it counted exactly. Each time the honest move was to fix the
artefact, not the assertion. And the one thing to carry forward about **evidence**: I was handed
T448's repair predicate and it was wrong for one of the two abuses it was written for, and I only
know that because I ran it instead of pasting it. **A repair supplied by a reviewer is a claim, not
a result** — the same rule as a cardinal supplied by a driver.
