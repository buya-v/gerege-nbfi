# T170 — the sentence-by-sentence scope rebuild G-8's STANDING RULE requires

Task `T170`, run `2026-08-21-run2-tierA-gl-accounting-A2`, branch `softhouse/T170-g8-rebuild`.

G-8's STANDING RULE, point 1: *"Nobody edits this section without rebuilding the sentence-by-sentence
scope table. Not a grep for the sentence you are changing — a rebuild, claim by claim, of what every
sentence asserts and the domain it was measured over."* This file is that rebuild.

## The denominator, stated before the verdicts (P-40)

Measured, not estimated, by `src/split_claims_t170.py` and `src/paragraphs_t170.py`:

| unit | on `main` (before) | on this branch (after) |
|---|---|---|
| line-level claim units in the two G-8 blocks | **747** | — |
| lines skipped (blank / fence / table separator / rule), with the reason recorded | **131** | — |
| **paragraph-level claim units** — one paragraph, bullet, table row or heading | **239** (28 headings, 154 prose/bullets, 57 table rows) | **322** |

**The 239 is the denominator every verdict below is stated against**, and all 239 were read. The
`.softhouse/gates.md` blocks it covers are located **by heading, not by line number**, so the count
cannot go stale: `## G-8 — TWO phenomena…` to `## G-9 — CLOSED…`, and `## G-8 — NOTICE, local fire
20260821-134344` to the next non-G-8 `##`.

## Verdict counts — COMPUTED, not counted by hand

`src/diff_units_t170.py` compares the two unit sets mechanically (`main`'s `gates.md` against this
branch's) and prints the arithmetic, because a hand count in this section has already been wrong
once (the 18-instead-of-22 refutation count) and a hand count is exactly what this rule exists to
prevent:

```
before_units                               239
after_units                                322
before_units_surviving_byte_identical      183
before_units_changed_or_removed             56
after_units_new                            139
```

So: **239 units read, 0 skipped without judging, 56 touched, 183 left byte-identical.** Of the 56:

| verdict | units |
|---|---|
| **FALSE as written — repaired** | **17** (enumerated below) |
| **TRUE but unscoped — re-scoped in place** | **21** (enumerated below) |
| headings, `task:`/`state:` bullets, the non-decision roster, the STANDING RULE's own occurrence count, and status lines that restated one of the above | **18** |

`after_units_new` = **139** is dominated by the THIRD OUTCOME block and by the four-shape PARTIAL
table; it also counts the FULL/PARTIAL bullets that replaced single sentences.

## What was FALSE and is repaired

Legend: **T159-n** = site *n* of T159's §9 list (the floor). ⭐ = **found by T170's own sweep, on
neither T117's nine nor T159's 25.**

| # | unit (identified by its claim, not by a line number) | what was false | repaired to |
|---|---|---|---|
| T159-1 | discriminator table, `principal column sums to the disbursed amount`, family B | *"NO — it sums to 0.00"* — unhedged, and false on 7 measurements over 4 partial shapes | FULL / PARTIAL split |
| T159-2 | same table, `totalPrincipalAmount` | *"0.00"* | FULL `0.00` · PARTIAL `0.02` / `0.04` / `0.05` / `1.66` |
| T159-3 | same table, non-zero principal rows | *"none"* | FULL none · PARTIAL exactly one, the last |
| T159-4 | same table, last row's interest | *"`0.01`"* — a statement about a 1-minor-unit disbursement, not about family B | scoped to B = 1 minor (150 of 209); 19 distinct values over the full shape; the four partial values given |
| T159-5 ⭐ | same table, `balance column`, family B | *"constant at the disbursed amount"* | FULL constant · PARTIAL two values |
| T159-6 | same table, `measured at`, family B | *"`104 ≤ n ≤ 250`, 29 cells"* | one rate, `104 ≤ n ≤ 3000`, principals 1…1001 minor, **209 cells** |
| T159-11 | "Discriminator for family B" opening paragraph | the whole description attached to the discriminator | rewritten as FULL and PARTIAL, with the four partial shapes tabulated |
| T159-12 | heading *"a MUCH narrower domain than family A"* | false in term (3000 vs 600) and in largest failing principal (1001 vs 291 minor) | narrower in rate and in the *number* of distinct failing principals; **wider** in term and in largest failing principal |
| T159-13 | *"T84 measured 22 family-B cells; T100 measured 7 more."* | incomplete | + T117's 155 and T159's 25 = **209**, over 190 distinct shapes |
| T159-14 | *"principal MNT 0.01 (1 minor unit) — no other principal has produced a family-B cell"* | false | **20** distinct principals, every one odd, 1 … 1001 minor, enumerated |
| T159-15 | *"repayment counts n ∈ {104…122} ∪ {150, 200, 250}"* | false | scoped to the four record captures, plus T117's and T159's term sets in full |
| T159-16 | *"Nothing above n = 250 has ever been asked at the family-B shape."* | false | asked to **n = 3000**; still family B there |
| T159-19 | *"Every family-B cell ever measured is 600.0 % / MNT 0.01 / n ≥ 104."* | the principal half is answered and the sentence is false | rate and lower-n halves kept as open questions; the principal half deleted, not softened |
| T159-20 | *"Whether it terminates. n = 250 fails; nothing above n = 250 has been asked."* | false | does not terminate at n = 3000; nothing above 3000 asked; the MNT 0.01 → 5.01 → 10.01 ladder recorded |
| T159-22 | *"No term above n = 600 has ever been asked"* | premise false | term premise corrected; **the conclusion (no upper bound established) is now confirmed by measurement rather than inferred** |
| T159-23 | option (b): *"no term beyond n = 600 has been asked, and family B has been seen at only one rate"* | term half false, rate half true | term half corrected; rate half kept; two further constraints added (third outcome; not an input-space region) |
| ⭐ M-8 | NOTICE: *"It is not monotone: (B=10001, n=2000) dies while (B=10001, n=3000) succeeds"* | **premise refuted by T177** — the two cells differ in run position, not behaviour | struck through in place with T177's measurement; the conclusion flagged as untested rather than as supported |

## What was TRUE but unscoped, and is re-scoped in place

| # | unit | scope added |
|---|---|---|
| T159-7 ⭐ | table row, memo recompute, family B | measured on 3 of the 29 record cells, all at 1 minor unit; unmeasured on the 180 new cells and on every partial cell |
| T159-8 | table row, the Go port, family B | 29 record cells (T84 22, T100 1, T101 re-grade 29); unmeasured on the 180 and on every partial cell |
| T159-9 ⭐ | table row, `invariant_exemptions` decisive | established on **one** full cell; "purely invariant" unmeasured on a partial cell |
| T159-10 ⭐ | *"Every row of that table holds on every cell of its family…internally uniform"* | scoped to the four record captures, with the count of rows that split and the count that are unmeasured |
| T159-17 | *"The Go port reproduces family B cell for cell — 0 divergent cells"* | scoped to 29; the gap named as the reason family B is called "both are wrong" |
| T159-18 ⭐ | *"Family B is NOT order-dependent"* | 3 cells, all at 1 minor unit; never tested on a partial cell or on the 180 |
| T159-21 | MNT 0.23 / MNT 2.91 / 12.65× | kept as **family-A** figures over the record union, and explicitly marked as no longer the G-8 record |
| T159-24 | the nine *"29 family-B cells"* / *"25 of the 29"* counts | each scoped to the four record captures; the closed form flagged as **never evaluated** on the 180 new cells |
| ⭐ M-1 | *"Cells behind that table: 312 family-A … and 29 family-B"* | 209 family-B, split 29 + 180, with T170's own re-derivation cited |
| ⭐ M-2 | *"the port agrees with the oracle — both emit a schedule that never repays the loan"* | scoped to 29; the partial shape and the 180 named as ungraded |
| ⭐ M-3 | *"On family B, option (a) is reachable TODAY … no port change"* | scoped to a **FULL** cell; on a partial cell it is unknown whether the failure is invariant-only or a cell diff |
| ⭐ M-4 | *"no commercially realistic Mongolian loan amount has been observed to fail — holds over that grid"* | restated over the enlarged grid, and explicitly marked as a statement that has already weakened three times |
| ⭐ M-5 | *"Today conformance.sh reports PASS with 42 parity vectors"* | **43 parity vectors, 5,664 cells**, measured by T170 on its own branch |
| ⭐ M-6 | *"Conformance is unmoved by this rewrite: … 42 parity vectors, 5576 graded cells"* | scoped to T140's rewrite; T170's own measurement added |
| ⭐ M-7 | the `.gz`-vs-extract warning's *"against the true 687 and 29"* | scoped to the four captures, with the 209 total pointed at |
| ⭐ M-9 | NOTICE headline bullets (*"MNT 5.01"*, *"by a factor of 501"*, *"B ≥ 1001 clean at all five terms asked"*) | each marked as T117's figure and pointed at T159's UPDATE; the "B ≥ 1001 clean" reading marked as a property of T117's probe set |
| ⭐ M-10 | the NOTICE block's `gates.md:NNN` citations | replaced by the name of the sentence or row, because T170's rebuild moved every line in G-8 |
| ⭐ M-11 | STANDING RULE's *"four separate times"* | **five**, with the fifth's mechanism described — a true sentence that went false when the measured set grew |
| ⭐ M-12 | NOTICE finding 2, *"Raised as T169"* | T169 landed; T177 then reconciled T159 against T169 |
| ⭐ M-13 | heading *"FAMILY B — the principal column itself never repays the loan"* | *"…does not repay the loan, in FULL or in PART"* |
| ⭐ M-14 | table row `totalOutstandingAmount` — *"`0` — so this field does not discriminate"* | true, and now measured on **all 209**: `totalOutstandingAmount` reads `0` on every family-B cell including all four partial shapes |

## What is NEW

**THE THIRD OUTCOME — the reference oracle can produce NO SCHEDULE AT ALL** (T159-25). A whole block,
sitting between the discriminator table and FAMILY A, because it is a property of *asking* the
oracle and belongs to neither family. It carries T159's two errored cells, the recursion frames, all
four of T177's measured dependencies (cold start, warm-up step function, `-Xss`, C2), the
refutation of the input-space framing, the T159/T169 reconciliation, the correction that the
throwing cell is **not** the headline cell and the headline cell is cold-safe, the
`errorStackDepthTotal: 1024` recording-cap note, five explicit `[UNVERIFIED]`s, and the pre-T169
rig note that makes every older *"0 errored"* unreadable as evidence.

Also new, as the STANDING RULE requires: **T170 added itself to the `task:` bullet and to the
non-decision roster**, and named T117, T159, T169 and T177 as having measured for this gate and
deliberately edited nothing in it.

## What this sweep structurally COULD NOT have found (P-26 / P-37 / P-33)

Stated as the rule requires, and none of it was fixed by T170:

1. **A restatement in another file.** T170 swept `.softhouse/gates.md` only, because that is the
   file it owns this fire. The family-B description, the "29 cells" counts and the MNT 2.91 record
   are restated in `.softhouse/patterns.md`, `.softhouse/program.json`, `.softhouse/tasks.json`,
   `.softhouse/obligations.md`, the `handoff/` corpus and `reviews/` — **another worker holds
   `patterns.md` this fire.** Raised as a follow-up, not taken.
2. **A claim restated as a chart or a diagram.** Nothing here parses images.
3. **A SILENCE where a scope qualifier ought to be.** This is the failure mode that produced the
   fifth occurrence in the first place, and a grep cannot see it. The 239-unit read is the only
   defence T170 had against it, and it is a human-judgement defence, not a mechanical one.
4. **A gitignored path** (P-33) — `grep` cannot see one.
5. **Anything about G-8's disposition.** T170 decided nothing.

## Provenance of every figure T170 carried in (P-46)

Every number in the rebuilt text was produced by `src/extract_t170.py` / `src/aggregate_t170.py`
reading the **raw** captures (the `.gz` wherever one exists — STANDING RULE 5) and nothing else:
no worker's analysis JSON, no handoff prose, no retyping. Money is parsed by splitting the oracle's
`BigDecimal.toPlainString()` on `.` and padding to the currency's dp; every residual is an **integer
subtraction in minor units**; the scripts contain no float on any path (STANDING RULE 4 / P-25).
Each input's sha256 and a canonical-over-`captures` digest are printed into `out/extract-t170.json`
with the canonicalisation recipe named (P-38).

The two figures **not** derived that way, and how they were obtained instead:

* **T177's counts** (33/33 cold, 9/9 headline, the `-Xss` table, 24 money comparisons, the frame
  depths) were extracted with `grep` from T177's committed `out/ANALYSIS-ALL.txt`,
  `out/ANALYSIS-matrixB.txt` and `out/ANALYSIS-matrixC.txt`. T170 did **not** re-run T177's rig.
* **43 parity vectors / 5,664 graded cells** is T170's own run of `bash .softhouse/conformance.sh`
  on this branch: VERDICT PASS, exit 0, 0 invariant violations, 0 assertions NOT RUN.
