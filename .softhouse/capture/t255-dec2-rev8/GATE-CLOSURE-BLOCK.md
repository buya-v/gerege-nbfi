# G-14 — closure block, written by `T255`

## Plainly: is G-14 closeable on this artefact?

**YES on the artefact; NO by my own act.**

`G-14`'s recorded scope is a STALE-EVIDENCE correction to `docs/adr/DEC-2-gl-accounting-adapter.md`
and nothing else. Revision 8 is **LANDED IN THAT FILE**, not proposed in a sidecar, and everything
the gate asked for is done and measured:

| what G-14 asked | state |
|---|---|
| correct the document **to what is true at the commit it is landed at** | **DONE.** Every measured claim re-taken by `T255` at `a71c140` from its own `VERDICT: PASS (exit 0)` run. Prepared AND landed in one fire, which is the only way that sentence can be satisfied. |
| move no obligation | **PROVED, three ways.** `instruments/60-obligation-diff.py` → `NO OBLIGATION MOVED: 0 finding(s)`. Per-hunk proof in `PER-HUNK-NO-OBLIGATION-MOVED.md`. |
| do not weaken the caution | **DONE and strengthened.** The old caution rested on a FALSE ground (*"nothing is graded"*); the new one rests on a true and narrower fact — **6 of 14 declared capabilities, both terms counted**, 8 declared out by name, `I-3`/`I-4` graded by no vector, `G-12` open, cutover a hard `user` gate. |
| do not move the vector store | **UNCHANGED.** `git rev-parse HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, read live. |
| the 35th site (§4.4's lead paragraph) | **CORRECTED**, and recorded as the 35th site in §10 so the near-miss is on the record. |
| the incomplete guard enumeration | **CORRECTED** — and, more to the point, made DERIVED, so it cannot go incomplete again without failing. |
| the ROT MECHANISM | **FIXED and DRIVEN RED.** See below. |

**Why NOT closeable by my act:** `T255` is the preparing task. Under the route `G-13` took, and
under CLAUDE.md's *Answering gates*, **ratification is the driver's act after an independent review
passes clean.** `T260` is that review. `T255` does not close its own gate and does not claim to.

## What remains before the driver closes G-14

1. **`T260`'s independent review passing clean.** It has been told to reject a revision 8 that
   leaves citations bound to line numbers; the ANCHOR/DERIVED mechanism and its red drive are the
   answer to that instruction, and they are meant to be attacked, not accepted.
2. **The driver's ratification**, `chosen_by: agent`, Buyan retaining veto.

## What is NOT in G-14's scope and is therefore still open

* **`FU-T247-2`** — two live falsehoods in `.softhouse/gates.md` (`:98`, inside G-11's own
  ratification block, and `:3561`). Another worker holds `gates.md`; it is not in my `files_hint`
  and I did not touch it. **NOT re-measured by me** — I state that rather than reporting an
  absence I did not look for.
* **`FU-T247-3`** — nobody has re-derived that each §5.3 precondition is *adequately* discharged.
  Revision 8 says so expressly, in §5.3, rather than letting a green corpus imply it.
* **`G-12`** — the running-balance columns. Untouched, and revision 8 keeps saying it is open.
* **`G-11`** — CLOSED, RATIFIED. Revision 8 records it correctly for the first time.
* **CUTOVER** — a hard `user` gate. Nothing here moves it, and revision 8 says so three times.

## The rot mechanism — what was chosen, and the argument

**Chosen: ELIMINATION first, a DERIVED checker second, wiring filed as a pre-written follow-up.**

The three options in the brief were: bind to a stable anchor; make citations derived and resolved at
read time; wire `verify-line-numbers.py` into something automatic. **The first two are adopted
together. The third is argued down, and here is the argument rather than the conclusion:**

1. **A wired LINE-NUMBER checker has a catastrophic false-positive rate, and false positives are how
   gates die.** It fires on every unrelated edit above every citation. `T253` rewrote ten `mktemp -t`
   sites in `.softhouse/conformance.sh` in this same fire, four of them above every guard citation
   DEC-2 carries. A wired line-number gate would have turned **every graded run in the program** RED
   for a documentation reason. A gate like that is pinned into an amnesty list within two fires —
   and this harness already documents that exact life-cycle in `FAILOPEN_PIN_FILE_LIST`. **A gate
   that must be suppressed to get work done is worse than no gate, because it looks like one.**

2. **An ANCHOR check has a near-zero false-positive rate**, because it fires only when the cited
   THING changes — which is when a citation should fire. That property is what would make wiring
   survivable. Measured: red-drive arm **R1** inserts 30 lines above every citation and the anchor
   checker stays **exit 0**, while the line-number checker goes red.

3. **Elimination needs no runner at all.** An anchored document is correct with nothing running. A
   checker is a *control*, and a control that must be remembered is `P-45` — five instances in this
   program, `manifest.py verify` silently RED across two merges being the canonical one. **Making
   the document unable to rot is strictly stronger than detecting that it has.**

4. **The population of a hand-written checker is its author's memory, not the document.**
   MEASURED at `a71c140`: `verify-line-numbers.py`'s `SH_ROWS` holds **4** rows; DEC-2 carried
   **115** `path:NNNN` citations, **90** of them into this repository. Wiring that checker would have
   enforced 4 of 90 while reading as though it enforced all of them. `20-verify-anchors.py` reads its
   whole population **out of the document**, so a citation nobody remembered cannot be silently
   unchecked (`P-66`).

5. **`P-79`, which is the general form.** A corrected cardinal rots wherever it was restated,
   exactly as a line number does. *"`run_guards` invokes seven guards"* was restated in the banner,
   in the `I-3` row, in §4.4.1 and in §8.1 — so one correction had to land in four places and never
   did. Revision 8 keeps **one** enumeration, in §4.4.1, marked `DERIVED-FROM-SOURCE: run_guards()`,
   re-parsed from the source and compared in order; every other site points at §4.4.1 by section
   number and restates no number. **The second site READS the first.**

6. **The ordinal is dropped as an identifier.** *"The seventh guard"* was TRUE on the
   all-invocations basis and FALSE on the tallied basis, and the basis was switched silently between
   revisions. Revision 8 uses the NAME everywhere in prose and publishes **both** ordinals in the
   `[DERIVED: …]` token, where both are re-derived and compared. That is `C-4` honoured: the count is
   kept, *"is the sixth"* is not published as prose, and an ordinal that is checked cannot go
   silently wrong.

**And the strongest single fact about this choice: the document ALREADY PRESCRIBED IT.** Revision 4
wrote, under the freshness rule, *"The mechanical remedy, **recommended and not performed here**
(`A2-25` FU-A2-25-3): cite function name plus a grep recipe rather than a bare line range … Revision
4 re-took them by hand; that does not scale and will go stale again."* It did. Twice more. **Revision
8 performs it.** This is not a new invention; it is a four-revision-old follow-up finally discharged.

### Red drive — a checker nobody has seen fail is unverified (P-22)

`instruments/50-red-drive.py`, transcript `evidence/50-red-drive-a71c140.txt`. Seven arms, all
against a scratch copy; the instrument asserts the real DEC-2 and the real `conformance.sh` are
byte-identical before and after, and they are.

| arm | perturbation | required | observed |
|---|---|---|---|
| **R0** | none | anchors exit 0 | **0** — and the line-number checker is ALREADY 3-of-4 stale at `a71c140`, isolating DEC-2 by restoring HEAD's blob so only `conformance.sh` varies |
| **R1** | **the T253 collision** — 30 lines inserted above every citation | anchors exit **0**, line numbers rot | **0 / rot.** The three numbers the review re-measured now read `local lint="…50-failopen-lint.py"`, `warn "…An empty frontier…"`, `warn "…the defect this guard exists to refuse."` — **plausible neighbours, so a reader is MISLED rather than STOPPED** |
| **R2** | the anchored function renamed | anchors exit 1, ROT | **1, ROT** |
| **R3** | an anchor's text duplicated | anchors exit 1, AMBIG | **1, AMBIG** |
| **R4** | a guard removed from `run_guards` | DERIVED count fails | **1, MISMATCH** |
| **R5** | two guards **reordered**, counts unchanged | DERIVED ORDER fails | **1** — a count-only check would have passed this, which is why the arm exists |
| **R6** | the DOCUMENT's own `[DERIVED: …]` token edited to claim 9 | fails | **1** — the document lying about the source is caught as readily as the reverse |

**`RED DRIVE: ALL ARMS BEHAVED AS REQUIRED`.**

### And then the REAL collision, not the simulation

`instruments/55-real-t253-collision.py`, transcript `evidence/55-real-t253-collision.txt`. R1 was my
*model* of what `T253` would do. This arm takes `.softhouse/conformance.sh` **straight out of
`origin/softhouse/T253-harness-portability`** — blob `fd25b910`, **67 insertions / 59 deletions**
against my `029439ba` — and runs revision 8's citations against it.

| | result |
|---|---|
| **revision 8's anchors + DERIVED facts** | **ALL HOLD. exit 0.** Nothing re-measured, nothing edited. `run_guards` moved from `:1548` to `:1556` and every tallied invocation moved with it; the document did not notice, because it does not contain those numbers. |
| **`verify-line-numbers.py`'s four `conformance.sh` rows** | **4 of 4 MOVED. exit 1.** Including **`:1300`, the definition row — the ONE row that had survived every prior pass.** Revision 7's citations would have been wrong in *every* position under T253, not three of four. |
| **and, again, the misleading resolutions** | `:1474` now reads `TIER2 .softhouse/capture/t234-…/00-engine-baseline.sh`; `:1494` reads an EMPTY LINE; `:1495` reads a comment about the linter's JSON destination. |

**This is the arm that settles it.** The defect was not modelled and defeated; it was met and
defeated. `T253` has not merged yet — `main:.softhouse/conformance.sh` still equals my fork's blob —
so the collision is still *pending*, and revision 8 is already indifferent to it.

### What the mechanism does NOT do, stated rather than implied

* **It is not wired into `conformance.sh`.** `.softhouse/conformance.sh` is `T253`'s this fire and is
  not in my `files_hint`; editing it would be the scope violation this program rejects. **Until it is
  wired, `20-verify-anchors.py` is a HAND-RUN checker, which is the `P-45` shape.** That is why
  elimination is the primary mechanism and the checker is explicitly the second line: **the document
  is correct even if the checker is never run again.** The wiring is filed as `FU-T255-1` with the
  call line pre-written, so it is a mechanical act for whoever next holds that file.
* **It does not convert every citation in DEC-2.** After revision 8: **108** `path:NNNN` citations
  remain, **25** Fineract-pinned (they do not drift), **9** lines of `conformance.sh` citations all
  of which are HISTORY quotations of what a past revision wrote — enumerated line by line in the
  checker's own output so a reviewer classifies them rather than trusting a count — and **~70**
  bare `admit.go` / `vector.go` / `grade.go` / `capability.go` basenames under `nexus/`. Those last
  are **ambiguous between two packages** as well as perishable, which is a second defect `C-8`
  named; they are filed as `FU-T255-2` with the measurement attached. **Both terms are counted and
  the residue is stated, not implied.**
* **It cannot tell whether the text a citation resolves to is what the citing sentence MEANT.** That
  is a human reading. What it can do is guarantee the citation still points at the thing it named.
