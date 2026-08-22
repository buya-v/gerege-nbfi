# T260 — independent review of DEC-2 revision 8 (`T255`, `softhouse/T255-dec2-rev8` @ `b334786`)

**Branch:** `softhouse/T260-review-dec2-rev8`. **Not merged — the driver merges.**
**Fork point:** `2f654ad`. **VERDICT: RATIFY.** Full review: `.softhouse/reviews/t260-dec2-rev8/REVIEW.md`.

**I edited nothing T255 touched.** My diff is `.softhouse/reviews/t260-dec2-rev8/` and this handoff.
`docs/adr/DEC-2-gl-accounting-adapter.md`, `.softhouse/conformance.sh`, `.softhouse/gates.md`,
`.softhouse/capture/lib/`, `.softhouse/capture/tierA-a2/` and `.softhouse/capture/t229-g8-site3/`
are untouched on this branch (A2-17).

## The load-bearing check: NO OBLIGATION MOVED — confirmed on four independent legs

T255 proved it three ways and named its weakness: its six byte-identity blocks are a CHOSEN
population covering **18.2% of lines / 20.1% of chars**, and a non-modal obligation escapes its
LEG 2. I closed that gap with my own instruments:

1. **Section identity map** (derived, not chosen): 22 of 40 sections byte-identical entire — 32.0%
   of rev7's lines. 15 sections changed.
2. **Exhaustive table-cell census**: 140 rows before, 140 after, **0 removed, 0 added, exactly 4
   changed** (§4.4 `I-1`/`I-2`/`I-3`/`I-7`), **last cell only**, confirmed by a dedup-free multiset
   control. `I-7`'s `Idempotency-Key` cells byte-identical. All ten §5.3 precondition rows
   byte-identical.
3. **Normative set difference with a BROADER non-modal predicate** (never/always/is-required-to/
   prohibited/requirement-noun/subject-of-duty/imperative-opener): **219** rev7 normative sentences
   vs T255's 87 modal lines. **14 LOST — 8 modal, 6 non-modal — all adjudicated by hand.** The one
   I hunted for, §8.2's admissibility-standard enumeration, survives with all five elements verbatim.
   §4.4's two welded obligations survive verbatim and are strengthened.
4. **Applier re-derivation**: `30-apply-revision-8.py` run from rev7 reproduces the landed blob
   **byte-for-byte** (sha256 `09e456b8…`), 43/43 hunks. So 100% of the diff is 43 named
   BEFORE→AFTER pairs, and `90-per-section-line-delta.py` printed all 176 removed + 656 added lines
   for me to read. Not a sample.

## Findings (9; none an obligation move)

* **F-1 MEDIUM** — the anchor checker parses **22 of the document's 25** `[ANCHOR ` tokens. Two
  LIVE anchors (§4.4's `I-3` row, §8.3's second bullet) carry a trailing `; MEASURED by …` inside
  the bracket and are **silently outside the population**, contradicting the instrument's own
  P-66/P-70 claim. Both resolve correctly today (I checked by hand). 2-line fix.
* **F-2 MEDIUM** — **a NON-UNIQUE anchor degrades at `git grep` EXIT 0.** Driven red in a sandbox:
  DELETED → 0 matches/exit 1 (loud, better than a line number); EDITED (one space) → 0/exit 1;
  **NON-UNIQUE → 2 matches, exit 0, nothing flags it.** So rule 4's *"An anchored document is
  correct with nothing running at all"* is overstated. This is the one sentence in rev8 I would
  soften — fold it into the wiring task, not another prepare/review cycle.
* **F-3 MEDIUM** — the rule is adopted and applied to **7 of 91** repo-pointing `path:NNNN`
  citations; 38 bare `admit.go:N`/`vector.go:N` remain, ambiguous between two packages. Disclosed
  as FU-T255-2/3.
* **F-4 LOW** — the applier's first-run refusal is **narrated, not in the evidence**. I evidenced
  the property instead: a one-space perturbation → REFUSE, exit 1, **nothing written** (atomic).
* **F-5 LOW** — 38 sites attribute corrections to "REVISION 7", which the same document says was
  never applied. Disclosed at §10; same self-identification family as the DRAFT defect. Advisory.
* **F-6 LOW** — **"T251's C-1…C-8" is a misattribution: T251 issued F-T251-1…5 and C-1…C-6.** C-7
  and C-8 originate in the driver's dispatch. Substance right, attribution wrong — in the brief too.
* **F-7 LOW** — §5.3 publishes `git grep -P '\bP-5\b'` while rule 1 says `-F` never bare grep; and
  the measurement was actually taken with Python `re`. I ran the published recipe: it **reproduces**
  (exit 1; `-P` control on `P-4` returns 2 files).
* **F-8 LOW, not against T255** — `gates.md` §G-14 still records the **prepare-only** route while
  the dispatch told T255 to prepare AND land. T255 landed on a branch and did not ratify, which
  honours the substance. **Driver should record the amended route when it closes G-14.** I could
  not edit `gates.md`.
* **F-9 LOW, pre-existing** — §10's revision-4 entry is present-tense about G-11 being OPEN.

## C-1…C-8 + the 35th site

**C-1 APPLIED (by elimination — zero LIVE `conformance.sh:NNNN` remain; all 9 residuals printed and
classified HISTORY). C-2 APPLIED. C-3 APPLIED and made DERIVED (rev7 never named
`guard_no_fail_open_instruments` anywhere in 3039 lines; rev8's fence lists all eight in source
order, re-derived and compared). C-4 APPLIED — claim VERIFIED: count kept, both counting bases in
ONE re-derived token (`invokes 8 | tallies 7 | invocation #7 and tallied #6`), ordinal never
asserted in prose (all 3 survivors are quotations inside retractions). C-5 APPLIED. C-6/C-7
APPLIED. C-8 APPLIED at the rewritten sites; the class is NOT closed (38 bare citations survive).
35th site APPLIED and named as such.**

All four "live stale sites" spot-checked: `go test` = **4 occurrences, 4 of 4 comments** (count
reproduced); `-context` `:1254` → anchor resolves at **`:1934`** (680 lines stale); `:401`/`:411`
both still TRUE and converted anyway; **`FU-A2-25-2`'s comment GONE — 0 matches, exit 1, with my
probe ABORTING on any status >1 and calibrated by both a negative and a positive control, so the
absence is measured, not fabricated** (P-80). The wider phrase still exists at `:1250`, so the
comment was edited, not deleted — the specific falsehood is what went.

## The mechanism ruling: the argued-down wiring is **UPHELD (P-81)**

Denominator reproduces (my count 117/26/91 vs T255's 115/25/90; `SH_ROWS` is exactly 4 rows), so
wiring would have enforced 4 of ~90 while reading as though it enforced all. **The real collision
reproduces under BOTH T253 implementations — and the fact T255 did not measure: it is already RED
at the untouched merge-base.** Anchors exit 0 in all three columns; `verify-line-numbers.py` goes
**3/4 MOVED at `a71c140` with no T253 at all**, **4/4 under cloud T253 (including `:1300`)**, **3/4
under mac T253b**. Regressions named honestly: anchors are **worse** than line numbers for
whitespace/reformat (measured) and for non-uniqueness (F-2); decisively better for the insertion-
above case that actually occurred three revisions running.

**Hand-run checker (FU-T255-1): MERGEABLE with a condition.** Refusing to touch `conformance.sh`
while T253 holds it is correct behaviour, not a shortfall — and I resolved all 25 anchors by hand,
all hold. But "I wrote the wiring but could not install it" is not installed. **File, next fire
after T253 merges:** wire `guard_dec2_citations`, **fix F-1** (reconcile literal vs parsed anchor
count, refuse on mismatch), **regenerate §4.4.1's DERIVED fence** (wiring adds a ninth invocation
and the fence will correctly fail — T255 names this itself), carry a negative control (P-22), and
soften the F-2 sentence.

## BAR (probe presence FIRST)

**PROBE LINE PRESENT — YES**, L92 `reference oracle (…) probe = up`, L101 `oracle probe UP`;
presence read before value (P-83), invoked as `bash`, not `sh`. **`VERDICT: PASS (exit 0) — 46
parity vectors … 7884 cells`**, process exit 0. ledger 4/2/0/0, **70 cells, 21 MONEY int64**,
invariants 0 violations / 11 non-vacuous / 10 INDEPENDENT. Fail-open **918 inspected, frontier 11
== pinned 11** (918 not 924 because my instruments were untracked at run time — same P-66 reason
T255 re-ran post-commit). **T255's 918→924 verified by counting tracked `.sh`/`.py` per ref:
`a71c140`=918, `ed686d7`=924, `b334786`=925.** Vector store `13b8342e…` **unmoved** at all three refs.

## Scope (re-checked cheaply at the end)

Three top-level paths only: DEC-2 (1), `capture/t255-dec2-rev8/` (19), the handoff (1).
`.softhouse/conformance.sh` **not in the diff**, blob `029439ba…` identical at `a71c140`,
`b334786` and `main` `b40f341`. `.softhouse/vectors/` **not in the diff**; `PIN-ledger.json` stays
at `dec2_revision: 5`, correctly. Revision 8 is **not yet on `main`** — the review still gates.

## Follow-ups filed

* **FU-T260-1 (MEDIUM)** — anchor-checker population reconciliation (F-1). Blocks wiring.
* **FU-T260-2 (MEDIUM)** — DEC-2 rule 4's *"correct with nothing running at all"* must name the
  non-unique case (F-2). One sentence; must be a later task (A2-17 forbids me).
* **FU-T260-3 (LOW)** — record G-14's amended prepare-AND-land route in `gates.md` at closure (F-8).
* **FU-T260-4 (LOW)** — the 38 bare `admit.go`/`vector.go` citations: convert or measure (merges
  with FU-T255-2/3).

## Unverified (P-40)

26 Fineract-pinned citations not re-opened; 38 bare repo citations not re-measured for staleness;
`T243`'s authorship not traced with `git log -S`; §5.3 precondition adequacy not certified by
anyone (FU-T247-3 stands); §9's 13 `[UNVERIFIED]` items not re-derived (§9 is byte-identical);
T255's `50-` and `60-` read but not re-executed — I built independent equivalents instead; my BAR
ran at `2f654ad` and the invariants were re-measured at `b40f341`.
