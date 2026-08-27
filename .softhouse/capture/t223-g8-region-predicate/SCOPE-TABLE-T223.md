# T223 — sentence-by-sentence scope rebuild of G-8, done BEFORE editing the section

STANDING RULE item 1 requires a rebuild, claim by claim, of what every sentence in the G-8 section
asserts and the domain it was measured over — not a grep for the sentence being changed. Item 3
requires the sweep to be for the **concept**, never the wording, and requires writing down **what the
sweep could not have found**.

## The rebuild

`src/scope_table_t223.py` enumerates the whole section (`## G-8 — TWO phenomena …` down to
`## G-8-NOTICE`), splits it into claims (table rows and bullets kept whole, prose split at sentence
boundaries), and tests each against a **concept** pattern set that is deliberately wider than the
sentence being changed — it catches every restatement of "family B lives at 600 %", "one annual
rate", "no other rate", every rate-count claim, every statement of the region by a term threshold,
and every bound on the failing principal or residual.

Measured on the section as it stood at `fdddd1c`:

| | |
|---|---|
| section lines | **1368** (`gates.md:923-2290`) |
| claims enumerated | **1416** |
| scope-bearing claims flagged | **94** |
| claims T223's measurement makes FALSE | **6** |
| claims whose FIGURE is right but whose DOMAIN was unnamed | **0 new** (the MNT 0.23 / MNT 2.91 / MNT 10.01 bullets already name theirs, per T101 F-8; T223 adds no larger residual and **left all three figures alone**) |

Machine output: `out/scope-table-t223.json`. **Note which tree it describes**: the numbers in the
table above were measured on the section **before** T223's edit (`fdddd1c`); the committed
`out/scope-table-t223.json` is the **re-run after** the edit — **1570 lines / 1610 claims / 113
scope-bearing**. Both are stated because a count in this section must name the run that produced it,
and re-running the script on the edited file is also the cheapest check that the edit did not lose a
scope-bearing claim: the flagged set grew (94 → 113) and nothing dropped out of it.

## The six claims T223 falsifies, and the disposition of each

| # | claim, as it stood | disposition |
|---|---|---|
| 1 | *"annual rate **600.0 % — and no other rate has ever produced a family-B cell**"* | **corrected in place**, with what it used to read. The rest of that bullet (T84's 41 clean 300 % cells) is untouched and still correct — the predicate says why. |
| 2 | *"**Whether it exists at any other RATE**, or below n = 104 … Every family-B cell ever measured is at **600.0 %**"* | **struck, not softened.** The RATE half is ANSWERED; the "below n = 104" half is split out and stays `[UNVERIFIED]`. |
| 3 | discriminator table row *"measured at … **one** annual rate (600.0 %) … **209 cells**"* | **corrected to three rates / 212 cells**, and the row says what it used to read. |
| 4 | *"Family B is still narrower in **rate** — one annual rate against eleven … **20** (all odd)"* | **corrected to three against eleven / 22 principals**, with a note that "all odd" was the resonance condition's shadow at `r = 1/2`, not a law. |
| 5 | *"principal: **20 distinct values, every one ODD**"* | **superseded by an explanation, not a counterexample.** Its own hedge — *"an observation over 209 cells, not a law"* — was right. |
| 6 | option (b)'s *"The other half — **family B has been seen at only one rate** — is unchanged and still true."* | **struck**, with the consequence for how option (b) must be drafted. |

## What this sweep COULD NOT have found (STANDING RULE item 3)

Written down because a site list is a starting point, never the sweep:

1. **Restatements of "600 % only" that name neither a rate nor family B** — e.g. a sentence that says
   "the region" or "this shape" and relies on context. The pattern set is lexical; a purely
   anaphoric restatement is invisible to it. T223 read the section end to end as well, and found
   none, but **that is a human read and not a measurement**.
2. **The same claim living OUTSIDE the G-8 section.** The script's domain is `gates.md:923-2290`
   only. Sibling records that restate it — `.softhouse/patterns.md`, `.softhouse/obligations.md`,
   the `T116-G8-FAMB-*` vector reason strings, `.softhouse/gates-proposed-answers.md`, earlier
   handoffs — are **NOT swept by this run**. The promoted vectors' reason strings in particular say
   *"It is NOT a statement that 600.0 % p.a. is exempt"*, which is still true and still correct, but
   nothing here checked whether any sibling document carries the falsified universal. **Recorded as
   a follow-up, deliberately not fixed by widening this diff.**
3. **Whether any claim in the section is false for a reason T223 did not measure.** The rebuild tests
   claims against T223's own measurement and against the domain each claim names. A claim that is
   wrong for an unrelated reason passes through.
4. **Anything about the PARTIAL shape, the THIRD OUTCOME, or the Go port.** T223 measured none of
   them, so no claim about them was re-derived, confirmed, or doubted.
