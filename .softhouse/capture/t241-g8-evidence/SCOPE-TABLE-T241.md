# T241 — G-8 STANDING RULE 1: the sentence-by-sentence scope-table rebuild `T219` declared it had not done

`T219` moved three records in the G-8 section and **declared** that it had substituted a concept
sweep for the rebuild the rule asks for. It said so rather than letting the sweep narrow silently
(P-40), which is why this is a task and not a defect. **T241 does the rebuild.** This file is the
disposition; `src/scope_table_t241.py` is the instrument and `out/scope-table-t241.json` its output.

## 1. The rule, quoted

`.softhouse/gates.md`, *STANDING RULE — how to edit this section (adopted at T140, proposed by
T129)*, item 1:

> 1. **Nobody edits this section without rebuilding the sentence-by-sentence scope table.** Not a
>    grep for the sentence you are changing — a rebuild, claim by claim, of what every sentence
>    asserts and the domain it was measured over. T129's rebuild ran to 117 rows and found six
>    failures, **all six of them scope or disposition statements in a section whose measurements are
>    perfect**. That ratio is the whole reason for this rule.

and item 3, which governs how the sweep inside it is built:

> 3. **Sweep for the concept, never for the wording** (P-21 / P-26) — including your own change of
>    mind. […] **A site list handed to you by a reviewer is a starting point, never the sweep** […]
>    Then **write down what the sweep could not have found**.

What `T219` recorded against itself (handoff gap 10):

> **STANDING RULE 1** asks for a full sentence-by-sentence scope-table rebuild before editing.
> **T219 did not do a 117-row rebuild.** It did a declared **concept sweep** (rule 3) with
> `git grep -n -P` […] over `MNT 10\.01`, `1001 minor`, `MNT 5\.01`, `largest.{0,60}residual` and
> `largest failing (principal|disbursement)`, and dispositioned every hit. **That is narrower than
> rule 1 asks for and is declared as such.**

**Decision: DO THE REBUILD, do not amend the rule.** The rebuild found something the concept sweep
could not have reached (§4), so the rule earned its cost on this very run, and there is no case for
weakening it. Recorded `chosen_by: agent` per CLAUDE.md's answering gates — an ENGINEERING call.

## 2. The instrument

`src/scope_table_t241.py` is a **successor** to `T223`'s
`.softhouse/capture/t223-g8-region-predicate/src/scope_table_t223.py`, which is **not edited**
(T114/T176). The enumeration, the sentence splitter and the section boundaries are T223's, unchanged,
so the two runs are comparable. **What T241 changes is the concept set**, and that is the point: a
scope table is only as wide as its concept set, and T223's eleven patterns were built around the
concept T223 was killing ("family B lives at 600 %"). T223's eleven are carried verbatim as
`C-01…C-11` so nothing T223 caught is lost; `C-12…C-22` are added for the concepts `T219`'s edit
moved — the residual/record figures in every historical value, the **wrong-axis shape itself** (a
figure with a term attached), the rescue ceiling in all three of its forms, the `δ ≤ 1` conjecture,
the options (b)/(c) prohibition, the TOTAL-INTEREST law, the port-grading claims, and a coarse outer
net for unscoped universals and bare measurement verbs.

Measured at `.softhouse/gates.md` on branch `softhouse/T241-g8-evidence-hygiene`, forked from `main`
at **`ea34404`** (fork point measured, not assumed — P-71):

| PRE-EDIT, at `ea34404` | LIVE G-8 (`gates.md:1033-3292`) | `## G-8-NOTICE` (`3293-3466`) |
|---|---|---|
| lines | 2260 | 174 |
| claims enumerated | **2322** | **179** |
| scope-bearing claims flagged | **730** | **63** |

**Both runs are committed**, because a count in this section must name the run that produced it:
`out/scope-table-t241-preedit.json` is the section as it stood at the fork point, and
`out/scope-table-t241.json` is the re-run **after** T241's edits — **2397 / 209 claims and
749 / 76 flagged**. Re-running on the edited file is also the cheapest check that an edit did not
silently drop a scope-bearing claim (T223's practice, kept): the flagged set **grew by 33 and lost
nothing**. One string differs — *"just got three times wider at a term this file had already
declared measured"* lost a trailing `**` when T241's roster sentence was appended inside the same
bold run — and **the claim is still flagged**, at `gates.md:2929` post-edit. Reproduce with
`python3 src/scope_table_t241.py <(git show ea34404:.softhouse/gates.md) …` or the two-argument form
documented in the script.

For comparison: T129's rebuild ran **117** flagged rows over a section a fraction of this size, and
T223's ran **94** (pre-edit) / **113** (post-edit) over 1368 lines with eleven concepts. The section
has since roughly doubled and the concept set has doubled; **730 is the same rule applied to a bigger
document, not a different rule.**

## 3. How the 730 were dispositioned — and what was NOT hand-read

**Declared, so nobody reads this as more than it is** (P-40, P-66/P-70):

| tier | concepts | rows | treatment |
|---|---|---|---|
| **A** | `C-09` `C-12` `C-13` `C-14` `C-15` `C-16` `C-17` `C-18` — figures, superlatives, the term-axis shape, the ceiling, the conjecture, the `user`-gate prohibition, the interest law | **255** | **every row hand-read by T241**, in full, against the measurement it rests on |
| **B** | `C-01…C-08` `C-10` `C-11` `C-19` `C-22` — rate/term cardinality universals, definitional statements, port-grading claims, instalment values | **202** | **read as a block, not row by row.** These are the concepts `T223` and `T231` rebuilt; every one carries a `[VERIFIED …]` / `[UNVERIFIED]` / "used to read" label already. `[UNVERIFIED by T241 that each is individually sound.]` |
| **C** | `C-20` `C-21` only — a bare universal (`every`, `never`, `all N`) or a bare measurement verb, with no figure, no term and no bound | **273** | **mechanically bucketed, not read.** This is the outer net; it fires on prose like *"every one of those bracketed by a measured clean cell"*. `[UNVERIFIED by T241.]` |

The 63 `## G-8-NOTICE` rows were enumerated separately and are dispositioned in §5.

**Tier A result: ONE failure in 255.** Every residual, ceiling, count and boundary figure in the
section reproduces against the evidence it cites. Specifically re-derived by T241 in integer minor
units (`src/rederive_t241.py`): the four `n·E + B − principal` worked examples at `gates.md:2292-2293`
(`B201` 20200 · `B251` 25200 · `B299` 30000 · `B150` 5750, all matching the captured
`totalInterestAmount`); `δ = 1` on `B2999`/`B3001`/`B4499`, hence the residual `min(B, n·δ)` = 2999 /
3000 / 3000, hence **MNT 30.00 on two cells and MNT 29.99 as the largest FULL residual**; the
`1.5·n` ceiling landing at 4500 with `4499` family B; `MNT 5.40 = 1.5 × 360` minor units at
`n = 360`; and the `δ` histogram behind *"296 corpus cells"* (113 at `δ = 0`, 183 at `δ = 1`). The
ratio T129 observed holds again: **the measurements are perfect and the one failure is a scope
statement.**

## 4. THE ONE FAILURE — and it is the exact claim the instrument defect is, one level up

**`gates.md:2283` at `ea34404`** (line numbers in this file drift by design — the claim is the
citation, the coordinate has a shelf life), the lead sentence of *THE LAW*'s unrescued-shape block:

> The shape of an **unrescued** cell follows from FACT A plus the deficit carry:
> ```
> last row EMI = E + B ;   TOTAL PRINCIPAL = max(0, B_minor − n·δ)
> ```

**The word `unrescued` is the wrong antecedent.** The shape follows from **FACT A**, and FACT A does
not hold on every unrescued cell. Re-derived by T241 from T229's own committed corpus census
(`.softhouse/capture/t229-g8-site3/out/validate-corpus.json`, commit `bb35cc8`, 296 stuck cells):

| | cells | FACT A holds | `last row EMI = E + B`, i.e. repayment `= n·E + B` |
|---|---|---|---|
| `δ ≥ 1` | 183 | **183** | **183** |
| `δ = 0` | 113 | **37** | **37** |

So on **76 unrescued stuck cells** — all of them `δ = 0`, e.g. `T117-NC-R600p0-N398-B1` where the
last row's total is **one minor unit BELOW** `E`, not `B` above it — the block's first line does not
describe the schedule at all. The two lines beneath it are already scoped `δ ≥ 1` and are
**untouched and correct**; `TOTAL PRINCIPAL = max(0, B − n·δ)` is also correct at `δ = 0` (113 of
113). **Only the antecedent of the first line is over-broad.**

This is the **fifth mechanism** in the STANDING RULE's own list — a sentence whose domain is wider
than the measurement under it — and it is **the same defect as the one T241 was sent to annotate in
`src/site3.py`** (*"TOTAL INTEREST = n*E + B for any unrescued cell"*), in the same word, one level
up. The correction applied to `gates.md` is a **labelled T241 clause naming the antecedent**, in the
T101 F-8 shape: **the domain is named, no figure is changed, and the sentence says what it used to
read.**

**Why the concept sweep could not have found it, and the rebuild did.** The sentence contains **no
money figure, no term, no superlative and no rate**. `MNT 10\.01`, `1001 minor`, `MNT 5\.01`,
`largest.{0,60}residual` and `largest failing (principal|disbursement)` — T219's five patterns —
match none of it, and no widening of a *figure*-shaped pattern would. It is reachable only by asking
every sentence what its domain is, which is what item 1 asks for and what item 3 alone does not.
**That is the case for keeping rule 1 as written, and it is a measured case rather than an
argument.**

## 5. `## G-8-NOTICE` — 63 flagged rows, and the decision T241 made about them

Enumerated separately because T223's run stopped at that heading and a decision about a block is not
creditable without an enumeration of it. All 63 are historical restatements inside a block whose own
heading reads *"(SUPERSEDED — historical record; the LIVE G-8 section is above)"*. **`MNT 10.01` as
the residual appears at six lines** — `3297`, `3317`, `3385`, `3396`, `3398`, `3424`, all at
`ea34404` — and the
different figure `MNT 15,010.01` (that cell's scheduled interest, still correct) at `3388` and
`3427`. T241 changed none of the eight.

**Decision: add ONE labelled pointer, change NOTHING that the block says.** Reasoning and the
rejected alternative are recorded in `gates.md` beside the pointer itself and in T241's handoff. In
short: five of the six are **measurements in the past tense** and are inert under the header, but
`:3396` and `:3398` are an **IMPERATIVE addressed to future readers** (*"Any disclosure of G-8 must
state the residual WITH ITS TERM"*), and an instruction is not made historical by a header — every
restatement in this program obeyed it, correctly, and reproduced the wrong axis. A pointer adds what
is known now without altering a syllable of what was said then; that is the T114/T176 shape, and the
block already contains in-place corrections labelled by T170 and T177, so annotating it is the
file's own practice, not a departure from it.

`T228` reached this block in its sweep (13 hits, lines 3293-3466), **honoured T219's decision, did
not touch it**, and recorded that `:3396` is T241's to weigh. `T228`'s gates.md diff is empty —
verified by T241 at `git show 617b8ea --name-only`, which lists four files and `gates.md` is not one.
So nothing here overrides a T228 edit; there is none.

## 6. What this rebuild could NOT have found (STANDING RULE 3)

- **It is scoped to `.softhouse/gates.md`**, and within it to the `## G-8` section and the
  `## G-8-NOTICE` block. It did not look at `patterns.md`, `obligations.md`,
  `gates-proposed-answers.md`, `program.json`, `tasks.json`, `docs/`, any handoff or review, or the
  `T116-G8-FAMB-*` vector reason strings. **T241 cannot say a stale claim is absent from any of
  those** — P-70. (`T228` swept several of them for three named concepts and declared its own gaps.)
- **A concept nobody named.** The 22 patterns are the concepts T223, T229, T219, T231 and T241
  knew to look for. **Tier C is an outer net for unscoped universals, and it was bucketed, not
  read** — a false claim carrying no figure, no term and no universal would sit in tier B or C and
  be missed.
- **A SILENCE.** P-26's own warning: a concept can be restated as a chart, as a count in a summary
  table, or as **a missing qualification**. An enumeration of sentences cannot enumerate the
  sentence that is not there.
- **It re-derived money, not source.** Every figure T241 re-derived came from the committed `.gz`
  captures and from the mechanism. **The Fineract source citations behind FACT A, FACT B and the law
  were NOT re-opened**; they remain T229's, bound by matched text at `426a23544…`.
  `[UNVERIFIED by T241.]`
- **It graded nothing.** No port run, no capture, no vector, and **the reference oracle (Fineract)
  was unreachable on this host** — so no observation in this rebuild is newer than the captures it
  reads.
