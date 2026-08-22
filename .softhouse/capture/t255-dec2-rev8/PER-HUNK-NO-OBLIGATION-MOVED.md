# T255 — DEC-2 revision 8: the per-hunk NO-OBLIGATION-MOVED proof

**Written so `T260` can RE-DERIVE it, not read it.** Every row below names the hunk, what it
changed, and the class of the change. The mechanical backing is
`instruments/60-obligation-diff.py`, whose transcript is `evidence/60-obligation-diff-a71c140.txt`
and whose verdict is **`NO OBLIGATION MOVED: 0 finding(s)`**.

Baseline for every comparison: `git show HEAD:docs/adr/DEC-2-gl-accounting-adapter.md` at
**`a71c140`**, sha256 `f02f7ff038afbf389bbd21a3fd40c55cc38cd88004e1833bded0f077f7957f44`, 3039
lines. Result: sha256 `09e456b887506288c642a595c8b4f39bdb7d34205a7cf5c8995b02057fab8164`, 3542
lines.

## The definition being tested

G-14's recorded scope is **NOTHING BUT DEC-2 ITSELF**, and within it: evidence, citations and false
statements of fact may be corrected; **nothing a conformant implementation must DO may move.** So
the test is not "did the text change" — 688 lines were inserted and 185 deleted. It is: **did any
proposition of the form "an implementation MUST …" change, weaken, narrow, or disappear.**

## Change classes used below

| class | meaning | permitted under G-14 |
|---|---|---|
| **FACT** | a claim about the state of the tree, the store or the harness | YES — this is what G-14 exists to correct |
| **CITATION** | a pointer to where evidence lives | YES |
| **RETRACTION** | a record that a past revision said something false | YES — required, in fact: the document's practice is restate-and-refute |
| **HEADING** | a section title carrying a present-tense state claim | YES, where the claim is a FACT |
| **OBLIGATION** | something an implementation must DO | **NO. If any row were this, revision 8 would be out of scope.** |

**No row below is class OBLIGATION.**

---

## Per hunk

| hunk | site | what moved | class | how it is proved |
|---|---|---|---|---|
| **H-0** | freshness rule's closing paragraph | the *"recommended and not performed here"* remedy is PERFORMED; the citation rule is written down | FACT + new process rule about **citations**, not about implementations | LEG 2: no modal line lost; the added modal lines are about resolvers and readers, not ports |
| **H-1a** | banner headline, lead, facts 1 and 2 | headline; *"Not one of them is currently checked by anything"*; fact 1's *"No `ledger` vector exists"*; fact 2's unscoped *"only accepted schema"* | FACT + RETRACTION | LEG 2 accounts the one lost modal line: *"what a conforming port **must** do"* is carried forward verbatim on its own line (visible in GAINED) |
| **H-1b** | banner fact 3 | three `conformance.sh` line numbers REMOVED, replaced by two ANCHORs and a pointer to §4.4.1's DERIVED block | CITATION | `evidence/20-verify-anchors-a71c140.txt`: both anchors resolve, uniquely |
| **H-1c** | banner fact 3 tail + fact 4 | adds *"`I-3` and `I-4` are graded by NO VECTOR"*; re-measures the store digest; corrects `vector.go:77-81` → anchored, and names the ambiguous bare `admit.go` | FACT + CITATION | the added sentence STRENGTHENS the reader's caution; it imposes nothing |
| **H-1d** | banner, the §8-will-be-misread paragraph | adds the third clause the paragraph omitted (the `I-3`/`I-4` walk) | FACT | it removes a self-inconsistency; no `must` in either side |
| **H-2** | banner's ratification paragraph | conditional → past tense; the caution is re-grounded on a true and narrower fact | FACT + the CAUTION, **kept and strengthened** | LEG 2 accounts the lost line; the replacement adds *"neither is a green ledger section"* and *"a PASS on its six vectors must never be cited as a cutover argument"* |
| **H-3** | status block | *"DRAFT (revision 5) … NOT RATIFIED"* → RATIFIED at 5, now at 8 | FACT (transcribed from `gates.md` / `program.json`, registers the ADR does not own) | LEG 2 accounts *"§5.3 names work that must land …"* as a FACT about §5.3's status; **§5.3's table is proved byte-identical in LEG 1** |
| **H-3b** | after the revision-5 paragraph | states the scope of revision 8 and that `PIN-ledger.json` stays at 5 | FACT | `PIN-ledger.json` is not in the diff; `git status --porcelain` shows only DEC-2 and the capture dir |
| **H-4** | §0 | *"contains exactly two context directories"* → three, with the resolution half of the gap still open | FACT | — |
| **H-5** | §2.2 | *"not gradeable today"* → graded, 21 money cells | FACT | — |
| **H-5b** | §4.2's closing sentence | *"answered no in §5"* → YES; explicitly adds *"The predicates themselves are UNCHANGED"* | FACT | **LEG 1: §4.2's predicate block is byte-identical, sha256 `46c34263214b0ff8`, 10069 chars** |
| **H-5c** | §4.4 lead paragraph (**the 35th site**) | *"and none of them can be graded today"* → per-invariant truth | FACT | — |
| **H-6** | §4.4's TODAY bullet | *"for every row the answer is NO"* → per-row | FACT | — |
| **H-7** | §4.4 `I-1` row, **cell 5 only** | NO → YES, with the four `int64` sums | FACT | **LEG 1b: cells 0–4 and 6 byte-identical; column 4 sha `8a456bb34dd4`** |
| **H-8** | §4.4 `I-2` row, **cell 5 only** | NO → YES on two of four, with `DEPENDENT`/`N/A` stated | FACT | **LEG 1b: column 4 sha `0a14b9a6c94c`** |
| **C-2** | §4.4 `I-3` row, **cell 5 only** | the supporting CITATION and the ordinal; **the answer "NO BY A VECTOR" is unchanged** | CITATION | **LEG 1b: column 4 sha `ff811cc89e26`; cell 5 is the only cell that moved** |
| **H-9** | §4.4 `I-7` row, **cell 5 only** | *"there is no `ledger` PASS"* → there is, and it still says nothing about `I-7` | FACT | **LEG 1b: column 4 — which carries the `Idempotency-Key` obligation — sha `6d1ca4cb9827`, identical** |
| **H-10** | §4.4's rule paragraph | **only** the clause *"and grades none of them today"*, plus the `I-2` denominator corrected from revision 7's "on four vectors" to "on three of the four" | FACT | **LEG 3: both obligations appear verbatim before and after.** The added tail (*"no growth of this corpus will ever discharge them"*) STRENGTHENS obligation 2 |
| **C-3a** | §4.4.1's guard enumeration | seven names → the complete eight, as a DERIVED-FROM-SOURCE block; the count and the citation corrected; the ordinal removed from prose | FACT + CITATION | `20-verify-anchors.py` re-derives the list from `run_guards()` and compares in order |
| **C-3b** | §4.4.1 *"The seventh does"* | ordinal → NAME; citation → ANCHOR; the quoted transcript kept and labelled as a stamped record | CITATION | anchor resolves uniquely |
| **H-11** | §4.9(b) | the GROUND moves; **the conclusion — every (b) row is ungraded — is kept** | FACT | — |
| **C-5** | §5's heading | *"and today that is ZERO vectors"* → quoted as a past claim | HEADING/FACT | — |
| **H-12** | §5's baseline prose | *"The `ledger` context has none"* → six | FACT | the fenced historical transcript above it is NOT touched |
| **C-9** | §5's `go test` citation | `:718`/`:721` → ANCHOR; *"both occurrences"* → four, all comments | CITATION + FACT | anchor resolves uniquely |
| **H-12b** | §5.1, appended | a scope note; **the heading and the five legs are NOT changed** | FACT | the heading string is unchanged in the diff |
| **C-10a** | §5.2's heading | *"DEC-2 grades nothing until it exists"* → quoted as a past claim | HEADING/FACT | — |
| **C-10b** | §5.2's *"(a) is adopted"* | a note that the machinery was built | FACT | **LEG 1: §5.2 requirements 1–7 byte-identical, sha256 `e6c3663f6eecfa75`, 20811 chars** |
| **H-13a** | §5.3, a note after the lead | states what is measured and, expressly, what is NOT certified | FACT | **LEG 1: the ten-row table byte-identical, sha256 `47065d5ee6867bba`, 4240 chars** |
| **H-13b** | §5.3's *"Nine open, one landed"* | retracted as a current fact, kept as revision 4's count | FACT | the table is untouched (above) |
| **C-11** | §5.4's `-context` citation | `:1254` → ANCHOR | CITATION | anchor resolves uniquely |
| **H-14a–d** | §8.1 | heading, preamble, facts 1–4, closing sentence | FACT + CITATION + RETRACTION | LEG 2 accounts the one lost modal line; the replacement widens it |
| **H-15a** | §8.2 | *"If ratified"* → *"Now that it is ratified"*; three bullets re-grounded | FACT | — |
| **H-15b** | §8.3 heading + first bullet | conditional → operative | HEADING/FACT | LEG 2 accounts the heading; *"must not be misread"* survives verbatim |
| **C-6/C-7/C-7b** | §8.3 second bullet | *"the seventh guard"* ×2 → the NAME | CITATION | — |
| **C-12** | §8.3's `FU-A2-25-2` note | the harness comment it describes is **GONE**; the note says so and closes the follow-up | FACT | `git grep -n -F 'records as not existing' -- .softhouse/conformance.sh` → **0 matches, exit 1**, a real measured negative (P-80) |
| **H-16 / H-16b** | §10 | entries for revision 6, the rejected revision 7, and revision 8; revision 5 no longer says *"this document"* | FACT | — |
| **C-13 / C-14** | §4.4's `NEXUS_DIR` and §5.1's `CMD_PKG` citations | `:401` / `:411` → ANCHOR. **Both were TRUE at `a71c140`** — converted anyway, because a citation that is correct today and perishable tomorrow is the class revision 8 exists to eliminate | CITATION | anchors resolve uniquely |

---

## What LEG 2 proves, and what it does not

`60-obligation-diff.py` collects every line in the document carrying normative modal language
(`must`, `shall`, `obliges`, `may not`, `is NORMATIVE`, `normative requirement`) and differences the
sets.

* **BEFORE: 87 distinct modal lines. AFTER: 95.** Both terms counted (`P-67`).
* **LOST: 8.** Every one is accounted, by name, with the hunk that owns it, in the instrument's own
  `ACCOUNTED` table — so the accounting is code a reviewer runs, not prose a reviewer trusts.
* **GAINED: 16**, all printed. An addition cannot relax an obligation; they are printed so `T260`
  can check that none INVENTS one. Reading them: they are about readers, resolvers, gates and this
  document's own process. **None is a new requirement on a port.**

**What it does not prove:** that no obligation was *reworded within a line that still contains a
modal*. That class is covered instead by LEG 1 (whole-block byte identity over every
obligation-bearing section) and LEG 1b (cell-by-cell identity over the invariant table). **The
three legs are complementary and no one of them is sufficient alone**, which is why all three run.

## The two things that could still be wrong, stated

1. **`[UNVERIFIED]` — that `BLOCKS` names every obligation-bearing block.** It names six. I chose
   them by reading the document's own section structure. LEG 2 is the arm that is supposed to catch
   an obligation living outside them, and it is a line-level check, not a semantic one.
2. **`[UNVERIFIED]` — that no obligation is expressed WITHOUT a modal verb.** A sentence like *"the
   port derives balances"* carries an obligation with no `must` in it. Neither leg would see it. I
   read every hunk's before/after by hand for this and found none, but a hand reading is not a
   proof, and it is exactly the class that has been missed here before.
