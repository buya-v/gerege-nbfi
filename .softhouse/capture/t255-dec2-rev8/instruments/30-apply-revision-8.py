#!/usr/bin/env python3
"""T255 — apply DEC-2 revision 8 to docs/adr/DEC-2-gl-accounting-adapter.md.

EVERY HUNK IS CONTENT-ADDRESSED. There is not one line number in this file.
Each hunk names an EXACT substring of the live document and asserts it occurs
EXACTLY ONCE before replacing it. If the document has moved under this script,
it REFUSES; it never applies a hunk to a guessed position. (That is the same
property revision 8 gives the document's own citations, applied to the
instrument that lands it — P-22: the tool obeys the rule it installs.)

Run:  python3 .softhouse/capture/t255-dec2-rev8/instruments/30-apply-revision-8.py
Exit: 0 applied, 1 a hunk did not match exactly once, 2 could not run at all.
"""
import hashlib
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")

H = []


def hunk(name, before, after):
    H.append((name, before, after))


# ===========================================================================
# H-0  the freshness rule's own "recommended and not performed here"
# ===========================================================================
hunk(
    "H-0 citation convention (discharges FU-A2-25-3, which revision 4 recorded and never performed)",
    """> **The mechanical remedy, recommended and not performed here** (`A2-25` FU-A2-25-3): cite
> **function name plus a grep recipe** rather than a bare line range, or re-take every harness
> citation mechanically at ratification time. Revision 4 re-took them by hand; that does not scale
> and will go stale again.""",
    """> **⚠ THE MECHANICAL REMEDY IS PERFORMED IN REVISION 8. It was RECORDED IN REVISION 4 AND LEFT
> UNDONE, and the document then went stale twice more on exactly the citations it was about.**
> Revision 4 wrote here: *"The mechanical remedy, recommended and not performed here* (`A2-25`
> FU-A2-25-3)*: cite function name plus a grep recipe rather than a bare line range, or re-take
> every harness citation mechanically at ratification time. Revision 4 re-took them by hand; that
> does not scale and will go stale again."* **It went stale again. Twice.** Revision 7 re-took the
> `conformance.sh` citations by hand and they were stale before it could land; the revision that
> reviewed it re-took them again and *those* were stale at the next commit. **A line number is a
> PERISHABLE IDENTIFIER: every insertion above it invalidates it, including insertions that change
> nothing it refers to — and a dead line number resolves to a plausible NEIGHBOURING line, so a
> reader following one is MISLED rather than STOPPED.** That last property is why this is not
> clerical.
>
> ### The citation rule revision 8 adopts, and applies to itself
>
> **1. ANCHOR — a citation into a file in this repository is bound to CONTENT, never to a
> position.** It is written inline as
>
> ```
> [ANCHOR <repo-relative path> :: `<an exact substring, unique in that file>`]
> ```
>
> and it is resolved by the reader with a recipe that is always fresh:
> `git grep -n -F '<the substring>' -- <path>`. **`-F`, never a bare `grep` and never `rg`
> (`P-75`); and `git grep` exits 1 on NO MATCH and >1 on ERROR, so a resolver must classify the
> status and never print an error as an absence (`P-80`).** An anchor cannot rot from an edit above
> it, because it contains no "above". It rots only when the cited THING changes — which is exactly
> when a citation should rot.
>
> **2. DERIVED — a fact that is a PROPERTY OF THE SOURCE is written down ONCE and re-derived, never
> restated.** How many guards `run_guards` invokes, in what order, and which one is tallied Nth, are
> properties of `run_guards`' body. §4.4.1 carries them in a fenced block marked
> `DERIVED-FROM-SOURCE: run_guards()`, and
> `.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py` re-derives that block from
> `.softhouse/conformance.sh` and compares. **Every other site in this document points AT §4.4.1 by
> section number and restates no number** — `P-79`: never fix a rotted number, make the second site
> READ the first. A corrected cardinal rots in every place it was restated, exactly as a corrected
> line number does.
>
> **3. An ORDINAL IS NOT AN IDENTIFIER; THE NAME IS.** *"The seventh guard"* was true under one
> counting basis and false under another, and the basis was switched silently between revisions. The
> identifier used throughout this document is `guard_ledger_invariants`. Where a count is needed it
> is DERIVED (rule 2) and it states its basis.
>
> **4. WHY NOT SIMPLY WIRE A LINE-NUMBER CHECKER INTO THE HARNESS.** Because it would fire on every
> unrelated edit above every citation. `T253` rewrote ten `mktemp -t` sites in `.softhouse/conformance.sh`
> in the same fire that landed this revision, four of them above every guard citation this document
> carries. A wired line-number gate would have turned every graded run in the program RED for a
> reason that has nothing to do with what the citations say — and a gate with that false-positive
> rate is a gate that gets pinned into an amnesty list within two fires, which is a shape this
> harness already documents in `FAILOPEN_PIN_FILE_LIST`
> [ANCHOR .softhouse/conformance.sh :: `THE PIN REMAINS A FRONTIER, NOT AN AMNESTY.`]. **An anchored
> document is correct with nothing running at all.** A checker is a second line, never the line: a
> control that must be remembered is `P-45`, which this program has hit five times.
>
> **Two categories are still exempt, for the reasons revision 4 gave:** Fineract citations, pinned to
> checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`, which do not drift; and HISTORY blocks that
> QUOTE what a past revision wrote — rewording a quotation would falsify the record, so a stale
> `:NNNN` inside one is preserved deliberately and is labelled where it appears.""",
)

# ===========================================================================
# H-1  the banner headline + facts 1-4 + the "§8 will be misread" paragraph
# ===========================================================================
hunk(
    "H-1a banner headline and lead",
    """> # ⚠ NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL.
>
> **Read this before any other sentence in this document, and before quoting any number out of it.**
> Every claim below is a claim about what the reference oracle *does* and what a conforming port
> *must* do. **Not one of them is currently checked by anything.** Four separate facts, each
> measured by this task, not reasoned:
>
> 1. **No `ledger` vector exists.** `.softhouse/vectors/` holds `loanschedule/` and `_selftest/` and
>    nothing else [VERIFIED by this task: `ls .softhouse/vectors/`].
> 2. **No `ledger` vector is EXPRESSIBLE.** The store's only accepted schema is
>    `gerege.loanschedule.vector/v1`, its `Request`/`Expect` shapes are loan-schedule shapes, and its
>    cell whitelist is three loan-schedule cells — so **no `ledger` input and no `ledger` output can
>    be written down**. §5.1 establishes this in code, in five legs, all five of which an independent
>    review re-opened and confirmed. **This is not a gap somebody forgot to fill; it is machinery
>    that has not been built.**
>""",
    """> # ⚠ THE LEDGER IS GRADED NOW — BY SIX VECTORS, OVER 6 OF THE 14 CAPABILITIES IT DECLARES.
> # THAT IS NOT COVERAGE, AND A GREEN LEDGER SECTION IS NOT A CUTOVER ARGUMENT.
>
> **Read this before any other sentence in this document, and before quoting any number out of it.**
> Every claim below is a claim about what the reference oracle *does* and what a conforming port
> *must* do. **That framing is UNCHANGED by revision 8, and so is every obligation it introduces.**
>
> **⚠ RETRACTION, revision 7 — THIS BANNER'S HEADLINE WAS FALSE, AND IT CITED THE COMMAND THAT
> REFUTES IT.** Revisions 1–6 opened with *"**NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES
> THIS CONTEXT AT ALL.**"*, asserted *"**Not one of them is currently checked by anything**"*, and
> gave as fact 1 *"**No `ledger` vector exists.** `.softhouse/vectors/` holds `loanschedule/` and
> `_selftest/` and nothing else [VERIFIED by this task: `ls .softhouse/vectors/`]"*. **Every clause
> of that is false at this commit, and the whole refutation is to re-run the command the sentence
> itself names.** It is restated here rather than quietly reworded, because a silent reword would
> hide that this document opened with a falsehood, under an instruction to read it first, for two
> revisions.
>
> **THE CAUSE, NAMED RATHER THAN PATCHED — `P-69` at maximum blast radius.** Revision 5 landed at
> `cab9e82`, **2026-08-22 14:24:56 +0800**. `A2-15` promoted the six `ledger` vectors at `1325e8b`,
> **2026-08-22 16:37:56 +0800** — **2 h 13 m later** [MEASURED by `T247` at `9b6c596`,
> `git log -1 --format=%ci` on each commit; independently reproducing the figure `G-14` records].
> **Every sentence in the old banner was true when it was written.** The document had no mechanism
> that notices when the world moves underneath a claim it publishes as measured fact, and it placed
> the most perishable such claim exactly where every reader is told to begin. The freshness rule
> below makes staleness *visible*; it does not *prevent* it, and this is what that costs.
>
> **Four facts, RE-MEASURED by `T255` at commit `a71c140` from its own `VERDICT: PASS (exit 0)` run
> — taken, not inherited from the gate that commissioned this correction, and not inherited from
> revision 7's draft either:**
>
> 1. **SIX `ledger` vectors exist, and all six PASS.** `.softhouse/vectors/` holds **three** context
>    directories — `_selftest/`, `ledger/`, `loanschedule/` — and `ledger/` holds
>    `LDG-01-manual-je-3leg-minor-units`, `LDG-02-repayment-split-4leg-minor-units`,
>    `LDG-03-overpayment-4leg-minor-units`, `LDG-04-header-account-accepted`,
>    `LDG-REFUSE-01-unbalanced-by-one-minor-unit` and
>    `LDG-REFUSE-02-manual-adjustments-not-permitted` [MEASURED by `T255` at `a71c140`:
>    `ls .softhouse/vectors/` and `ls .softhouse/vectors/ledger/` — **the same command revisions 1–6
>    cited as proof of the opposite**]. On every run the harness prints, and pins:
>    **`ledger parity PASS 4 FAIL 0` · `ledger oracle-refusal PASS 2 FAIL 0` · `ledger inadmissible 0`
>    · `ledger harness errors 0` · `ledger cells compared 70 graded, of which 21 are MONEY cells in
>    int64 minor units` · `ledger invariants 0 violation(s), 11 non-vacuous assertion(s), of which 10
>    are INDEPENDENT`** [MEASURED by `T255` at `a71c140`]. **`I-1` and `I-2` are among what those
>    cells check**, per vector, with a hold that could only be passed by construction reported as
>    `DEPENDENT` rather than counted as evidence.
>
> 2. **A `ledger` vector IS expressible, because the machinery §5.2 named was BUILT — and §5.1's five
>    legs are untouched by that, which is the distinction this item now has to carry.** §5.1's claim
>    is, and remains, *"no `ledger` vector is expressible **against the frozen
>    `gerege.loanschedule.vector/v1` schema**"*, and that is **still true**: a `loanschedule`-schema
>    file dropped into `ledger/` is INADMISSIBLE by name
>    [ANCHOR nexus/internal/apps/loanschedule/conformance/admit.go :: `if v.Context != "" && !IsSchemaContext(v.Context) {`],
>    whose allowlist is
>    [ANCHOR nexus/internal/apps/loanschedule/conformance/vector.go :: `return []string{SelfTestDir, LoanScheduleContext}`].
>    What was false is this item's **unscoped restatement** — *"the store's only accepted schema is
>    `gerege.loanschedule.vector/v1`"* — and its conclusion, *"it is machinery that has not been
>    built"*. **The store accepts TWO schemas.** The second is **`gerege.ledger.vector/v1`**
>    [ANCHOR nexus/internal/apps/ledger/conformance/vector.go :: `const SchemaV1 = "gerege.ledger.vector/v1"`],
>    with its own `Request`/`Expect` shapes, its own class set (`parity`, `oracle-refusal`), its own
>    comparator and a cell whitelist derived from it, its own context allowlist
>    [ANCHOR nexus/internal/apps/ledger/conformance/vector.go :: `return []string{LedgerContext}`],
>    its own store pin (`PIN-ledger.json`, keyed on `dec2_revision`) and its own capability registry
>    (`capabilities-ledger.json`, schema `gerege.ledger.capabilities/v1`). **The machinery was named
>    in §5.2 and built by `A2-15`.** §5.3's revision-7 note records what that does and does **not**
>    certify about the ten preconditions, and a ratifier should read it there rather than infer it
>    here.
>""",
)

hunk(
    "H-1b banner fact 3 — the guard citation, now ANCHORED and DERIVED",
    """> 3. **A guard for `I-3` (balances are derived) and `I-4` (append-only) NOW EXISTS — revision 2 said
>    it did not, and that was true when revision 2 was written.** `run_guards` invokes **seven**
>    guards, not five; the seventh is `guard_ledger_invariants`, built by `A2-18` and **wired** by
>    `T208` [VERIFIED by `A2-28` at commit `2e97162`: `.softhouse/conformance.sh:1152-1187` defines
>    it, `:1189-1213` is `run_guards` invoking all seven, `:1209` is the invocation; `A2-28`'s own
>    unfiltered run prints `ledger-invariants: PASS` and `invariant violations 0` (MEASURED, §5.4)].
>    **This does
>    NOT mean the ledger is covered, and the guard says so itself**: its PASS text reads *"no""",
    """> 3. **A source guard for `I-3` (balances are derived) and `I-4` (append-only) RUNS ON EVERY
>    INVOCATION — AND NO VECTOR GRADES EITHER INVARIANT.** The guard is `guard_ledger_invariants`,
>    built by `A2-18` and **wired** by `T208`
>    [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`]. **§4.4.1 carries the ONE
>    DERIVED-FROM-SOURCE enumeration of what `run_guards` invokes, and this fact restates no count
>    from it** — `P-79`. `T255`'s own run prints `ledger-invariants: PASS` and
>    `invariant violations 0` [MEASURED by `T255` at `a71c140`].
>    **⚠ RETRACTION, revision 8 — WHAT REVISIONS 3–6 SAID HERE AND WHY IT IS NOT MERELY CORRECTED.**
>    They read *"`run_guards` invokes **seven** guards, not five; the seventh is
>    `guard_ledger_invariants`"* with `.softhouse/conformance.sh:1152-1187` / `:1189-1213` / `:1209`.
>    Those numbers were stamped at `2e97162`, are correct there, and were STALE by revision 7:
>    `T243` wired an eighth guard, `guard_no_fail_open_instruments`
>    [ANCHOR .softhouse/conformance.sh :: `guard_no_fail_open_instruments() {`]. **Revision 7 replaced
>    them with three FRESH line numbers, and those were stale before revision 7 could land. So was
>    the reviewer's re-measurement of them.** Revision 8 therefore does not correct the numbers; it
>    **removes them**, under the citation rule above. **An ordinal used as an identifier goes wrong
>    silently, and so does a line number. The identifier is the NAME.**
>    **This does
>    NOT mean the ledger is covered, and the guard says so itself**: its PASS text reads *"no""",
)

hunk(
    "H-1c banner fact 3 tail — add the no-vector-grades-I-3/I-4 sentence",
    """>    said *"three"* here and recorded `I4-BUILDER` as `[UNVERIFIED]`. §4.4.1 carries the retraction,
>    the class names, the measurement and the limits.
> 4. **The "PASS 46" everybody quotes is `loanschedule`'s.** All **46** promoted parity vectors are
>    in the `loanschedule/` directory [MEASURED by `A2-28` at commit `2e97162`; store tree
>    `73c3ea7b43dd75f04884072719a87fc8e1d255c1`]. **Zero of them touch a GL account, a mapping, a
>    financial activity or a journal entry.** **Revision 2 leaned on this as though the
>    `loanschedule/` directory boundary were ENFORCED. It was not** — that is exactly what item 2's
>    retraction is about, and it is why 43 became 44. **It is enforced now**, at admission, by an
>    allowlist tied to the schema rather than to the directory [VERIFIED by `A2-28`:
>    `nexus/internal/apps/loanschedule/conformance/vector.go:77-81`, `SchemaContexts()` returns
>    `{_selftest, loanschedule}`; `admit.go:139-147` refuses any other `context` as **INADMISSIBLE**].
>
>    **The count itself is a moving target and must be re-measured, never copied.** It was 43 when
>    revision 3 was drafted; `T116` promoted three vectors in the same fire and it is 46 now. Any
>    quotation of it in this document carries the commit it was measured at, and a ratifier who finds
>    a bare number without one should treat it as stale until re-run.""",
    """>    said *"three"* here and recorded `I4-BUILDER` as `[UNVERIFIED]`. §4.4.1 carries the retraction,
>    the class names, the measurement and the limits. **And note what the six new vectors did NOT
>    change: `I-3` and `I-4` are graded by NO VECTOR, because a vector is a snapshot of oracle output
>    and a snapshot cannot observe the ABSENCE of a write. No growth of this corpus will ever
>    discharge them.**
> 4. **The "PASS 46" everybody quotes is still `loanschedule`'s — and that matters MORE now, not
>    less.** All **46** promoted `loanschedule` parity vectors are in the `loanschedule/` directory,
>    and **zero of them touch a GL account, a mapping, a financial activity or a journal entry**
>    [RE-MEASURED by `T255` at `a71c140`; store tree
>    `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, `git rev-parse HEAD:.softhouse/vectors`].
>    **The `ledger` corpus is counted SEPARATELY and must be quoted separately**: the harness prints
>    it under its own heading, *"SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS"*, as **4 / 2 /
>    21**. A reader who cites `PASS 46` as evidence about the ledger is quoting the wrong number,
>    exactly as before; a reader who cites `4 / 2 / 21` as evidence that the ledger is covered is
>    making the new mistake this banner exists to prevent. **Revision 2 leaned on this as though the
>    `loanschedule/` directory boundary were ENFORCED. It was not** — that is exactly what item 2's
>    retraction is about, and it is why 43 became 44. **It is enforced now**, at admission, by an
>    allowlist tied to the schema rather than to the directory: `SchemaContexts()` returns
>    `{_selftest, loanschedule}`
>    [ANCHOR nexus/internal/apps/loanschedule/conformance/vector.go :: `func SchemaContexts() []string {`]
>    and the admission layer refuses any other `context` as **INADMISSIBLE**
>    [ANCHOR nexus/internal/apps/loanschedule/conformance/admit.go :: `strings.Join(SchemaContexts(), ", "))`].
>    **Revisions 1–7 cited these as `vector.go:77-81` and `admit.go:139-147`. The first was off by
>    one at this commit — `SchemaContexts()` begins at 78, and `:77` is a comment — and the second
>    named a BARE `admit.go` that exists in TWO packages** (`loanschedule/conformance/` and
>    `ledger/conformance/`), so it was ambiguous as well as perishable.
>
>    **The count itself is a moving target and must be re-measured, never copied.** It was 43 when
>    revision 3 was drafted; `T116` promoted three vectors in the same fire and it is 46 now. The
>    `ledger` figure was **zero when revision 5 was drafted and six 2 h 13 m later**, which is the
>    whole of `G-14`. Any quotation of either carries the commit it was measured at, and a ratifier
>    who finds a bare number without one should treat it as stale until re-run.""",
)

hunk(
    "H-1d banner — the §8-will-be-misread paragraph, completed",
    """> **§8 contains a sentence that is true and will be misread**, so it is contradicted here in
> advance: `conformance.sh`'s hard guards *do* walk `nexus/internal/apps/ledger/`. They walk it
> **for floating-point literals and `gofmt`**. That is not `I-3`. That is not `I-4`. A reader who
> takes "the guards cover the ledger tree" to mean the double-entry invariants are enforced has
> been misled by this document, and §8 now says so at the point of the claim.""",
    """> **§8 contains a sentence that is true and will be misread**, so it is contradicted here in
> advance: `conformance.sh`'s hard guards *do* walk `nexus/internal/apps/ledger/`. They walk it for
> **floating-point literals, `gofmt`, and — since `T208` — the source-level `I-3`/`I-4` walk of fact
> 3**. That last one is real and it is narrow; the first two are not `I-3` and are not `I-4` at all.
> **Revisions 1–6 omitted the third clause entirely, three paragraphs below their own fact 3 which
> said the guard runs — a self-inconsistency that predates `G-14`.** A reader who takes "the guards
> cover the ledger tree" to mean the double-entry invariants are enforced has been misled by this
> document, and §8 now says so at the point of the claim.""",
)

# ===========================================================================
# H-2  the banner's closing paragraph
# ===========================================================================
hunk(
    "H-2 what ratifying bought — and THE CAUTION",
    """> **What ratifying DEC-2 would and would not buy.** It would buy a written boundary and an
> admissibility standard. It would buy **no grading whatsoever** until the machinery in §5.3
> exists. Ratification is not coverage, and this document must never be cited as though it were.""",
    """> **⚠ WHAT RATIFYING DEC-2 BOUGHT — past tense, because it HAS been ratified, and because revisions
> 1–6 wrote this sentence in the conditional and left it there.** `G-11` is **CLOSED — RATIFIED**
> (revision 5, reviewed by `A2-33`, ratified by the driver `chosen_by: agent`; Buyan retains veto)
> [TRANSCRIBED from `.softhouse/gates.md` § `G-11`]. It bought a written boundary and an
> admissibility standard. Revisions 1–6 said it would buy **"no grading whatsoever until the
> machinery in §5.3 exists"** — **the machinery was then built and the grading exists**: 4 parity,
> 2 oracle-refusal, 21 money cells, every run.
>
> **THE CAUTION IS UNCHANGED AND IT IS NOW THE WHOLE POINT OF THIS BANNER. Ratification is not
> coverage, and neither is a green ledger section.** What is graded is **6 of the 14 capabilities
> `capabilities-ledger.json` declares**; **8 of 14 are declared OUT of the graded domain**, by name,
> and the harness prints all eight on every run, pass or fail, derived from that file so a gap
> cannot go unprinted [MEASURED by `T255` at `a71c140`, both terms counted — `P-67`: `len(capabilities)`
> is 14, `in_graded_domain: true` is 6, `false` is 8, and 6 + 8 = 14]. Ungraded, by name: **slot
> resolution** (the product→GL mapping chain, including payment-type precedence — the single largest
> thing this context does), **accrual entries**, **account transfers through `TRANSFERS_SUSPENSE`
> (gl 17)**, **charge-off**, **multi-currency entries**, **opening balances and `GLClosure`**,
> **reversals (`I-5`)**, and **running balances — on which `G-12` is OPEN, and on which `A2-29`
> measured the oracle's stored balance to be a SECOND SOURCE OF TRUTH rather than a cache, made to
> disagree with the derived sum by MNT 2,000,000.00 and surviving four organisation-wide
> recomputes**. Add to that: **no vector grades `I-3` or `I-4`** (fact 3), `I-6` is outside this
> contract's domain, and `I-7` lands on `A1` and the HTTP layer, not here.
>
> **So: this document must never be cited as evidence that the GL/accounting context is correct, and
> a PASS on its six vectors must never be cited as a cutover argument. CUTOVER IS A HARD `user`
> GATE and nothing in this document or in the harness moves it.**""",
)

# ===========================================================================
# H-3  the status block  (also: "DRAFT (revision 5), NOT RATIFIED")
# ===========================================================================
hunk(
    "H-3 status block",
    """**Status: DRAFT (revision 5), 22 August 2026, drafted by task `A2-32`. NOT RATIFIED. `A2-32` is NOT
AUTHORISED to ratify it and does not.** **Revision 4 (`A2-28`) was REJECTED** by independent review
(`A2-31`) on two findings, **both of them claims this document made about `main` that were false**;
**revision 3 (`A2-21`) was REJECTED** before it by `A2-25`; **revision 2 (`A2-16`) by `A2-19`**; and
**revision 1 (`A2-13`) by `A2-14`** (local fire `20260821-125942`). **Four revisions, four
rejections.** Gate **G-11 remains OPEN — NOT RATIFIABLE** in `.softhouse/gates.md` and
`.softhouse/program.json`. **Ratification requires a FURTHER independent review passing clean AFTER
revision 5** under standing policy **P-2**; until then `A2-15` (promote GL vectors) stays blocked,
and §5.3 names work that must land before `A2-15` could succeed even against a ratified contract.""",
    """**Status: RATIFIED at revision 5; now at REVISION 8. 22 August 2026.** Revision 8 is prepared AND
landed by task `T255` under gate **`G-14`**, in one fire, and is subject to independent review
(`T260`) before the driver ratifies it. **`T255` does not ratify its own revision and does not claim
to.**

**⚠ Revisions 6 and 7 identified this document as *"DRAFT (revision 5) … NOT RATIFIED"* while it
was a RATIFIED revision 6. Revision 8 corrects that.**

**`G-11` is CLOSED — RATIFIED.** Revision 5 (`A2-32`) was reviewed independently by `A2-33`, returned
APPROVED, and ratified by the driver `chosen_by: agent` under CLAUDE.md § *Answering gates*; **Buyan
retains veto and may reverse it** [TRANSCRIBED by `T255` at `a71c140` from `.softhouse/gates.md`
§ `G-11` and `.softhouse/program.json` — the two registers this line copies from and does not own].
**Revision 6** then landed under gate `G-13` (prepared by `T244`, reviewed by `T246`, two corrections
applied before landing), correcting §4.4's `I-5` row and §9 item 13. **`A2-15` is `status: done`** and
has promoted six `ledger` vectors [TRANSCRIBED from `.softhouse/tasks.json`; the vectors MEASURED by
`T255` at `a71c140`].

**Four revisions, four rejections, and they are why revisions 5–8 are trusted.** **Revision 4
(`A2-28`) was REJECTED** by independent review (`A2-31`) on two findings, **both of them claims this
document made about `main` that were false**; **revision 3 (`A2-21`) was REJECTED** before it by
`A2-25`; **revision 2 (`A2-16`) by `A2-19`**; and **revision 1 (`A2-13`) by `A2-14`** (local fire
`20260821-125942`). Revision 5 was ratified only after `A2-33` re-derived every load-bearing claim
rather than reading `A2-32`'s. **Revision 7 was PREPARED and REJECTED** by `T251` — not because any
obligation moved (none did) but because its freshly re-measured `conformance.sh` citations had gone
stale before it could land. **It was never applied to this file. Revision 8 is what landed**, and it
is why §4.4.1 no longer carries a line number.

**⚠ A ratified DEC-n may not be amended by an agent without a gate**, and that has not changed.
`G-14` is that gate, and its recorded scope is **NOTHING BUT THIS DOCUMENT**: evidence, citations and
false statements of fact may be corrected; **no normative obligation may move**. **CUTOVER,
regulatory acceptance and parallel-run sign-off remain hard `user` gates and nothing in this document
moves them.**

**⚠ A PROCESS DEFECT, RECORDED BECAUSE IT IS PART OF WHY THIS BANNER STAYED FALSE.** Revision 6
landed real content changes (§4.4's `I-5` row, §9 item 13) **without a §10 revision-history entry and
without updating this status block**. **Revision 8 adds §10 entries for revision 6, the rejected
revision 7, and revision 8.** A revision that does not stamp itself is a revision the next reader
cannot date.""",
)

hunk(
    "H-3b appended after the revision-5 change paragraph",
    """revision-5 entry lists every site each correction landed at, and `A2-32`'s handoff carries the sweep
population, the method, and what it skipped.""",
    """revision-5 entry lists every site each correction landed at, and `A2-32`'s handoff carries the sweep
population, the method, and what it skipped.

**Revision 8 changes EVIDENTIAL STATEMENTS ONLY, and it changes NO OBLIGATION.** Not one normative
`must`, not a contract sentinel, not a graded-domain predicate, not a §5.3 precondition, not a §4.2
predicate, not `PIN-ledger.json` — which stays at `dec2_revision: 5`, because admission compares the
VECTOR to the PIN and never reads this document
[ANCHOR nexus/internal/apps/ledger/conformance/admit.go :: `add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)`],
and nothing a vector asserts has changed. Its subject is two classes of defect and no others:
**(i)** claims this document published as CURRENTLY-TRUE MEASURED FACT that had gone false underneath
it — every one of them true when written; and **(ii)** the MECHANISM that let (i) happen three
revisions running, which is the line-number citation, now replaced by the ANCHOR/DERIVED rule above.
§10's revision-8 entry lists every site, and `T255`'s handoff carries a per-hunk proof that no
obligation moved.""",
)

# ===========================================================================
# H-4  §0
# ===========================================================================
hunk(
    "H-4 §0 opening",
    """`.softhouse/vectors/` contains exactly two context directories, `loanschedule/` and `_selftest/`
[VERIFIED: `ls .softhouse/vectors/`, by this task]. Task **A2-8** merged the port of the GL
account model, product-to-account mapping resolution and financial activity accounts to `main`,
and **not one parity vector grades it**. The conformance run reports `PASS 46`; all 46 are
`loanschedule`'s [MEASURED by `A2-28` at commit `2e97162`; the "not one grades the GL package" half
is VERIFIED BY A2-8, NOT RE-OPENED HERE — A2-8's own handoff says so plainly:
*"the harness does not grade this package at all"*].""",
    """**⚠ THIS SECTION RECORDS WHY THIS DOCUMENT WAS WRITTEN, AND THAT SITUATION HAS ENDED. Revision 7
re-measures it rather than deleting it, because the reason a contract exists is not made obsolete by
the contract working.**

**When DEC-2 was commissioned:** `.softhouse/vectors/` contained exactly two context directories,
`loanschedule/` and `_selftest/`. Task **A2-8** had merged the port of the GL account model,
product-to-account mapping resolution and financial activity accounts to `main`, and **not one
parity vector graded it** — `A2-8`'s own handoff said so plainly: *"the harness does not grade this
package at all"*. That is the gap this document was written to close.

**At `a71c140` it holds THREE** — `_selftest/`, `ledger/`, `loanschedule/` — and `ledger/` holds six
`LDG-*` vectors, four `parity` and two `oracle-refusal`, all passing [MEASURED by `T255` at
`a71c140`: `ls .softhouse/vectors/`]. The `loanschedule` conformance run still reports `PASS 46` and
all 46 are still `loanschedule`'s; the `ledger` corpus is reported separately as **4 / 2 / 21**.
**What has NOT changed is the part `A2-8` was pointing at:** the product→GL **slot resolver** — the
thing `A2-8` actually ported — is still graded by **no vector at all**; `capabilities-ledger.json`
carries `ledger.slot.resolution` with `in_graded_domain: false`, and the harness prints the reason on
every run. **Six vectors closed the journal-entry half of the gap and left the resolution half open.**""",
)

# ===========================================================================
# H-5  §2.2
# ===========================================================================
hunk(
    "H-5 §2.2 closing",
    """**What this does NOT rescue.** Being statable is not being graded. §5 establishes that no vector
asserting a money cell — or any other `ledger` cell — is currently expressible at all. `I-1` and
`I-2` are gradeable **from the data in hand and from nothing else that is missing except the
machinery**; they are not gradeable **today**. §4.4 now says that in those words.""",
    """**What this does NOT rescue — CORRECTED IN REVISION 7, and the correction is in the reader's
favour.** Revisions 1–6 wrote here that *"§5 establishes that no vector asserting a money cell — or
any other `ledger` cell — is currently expressible at all"*, and that `I-1` and `I-2` *"are not
gradeable today"*. **Both went false when the machinery §5.2 named was built.** `I-1` and `I-2` are
graded today, per vector, in `int64` minor units — **21 money cells across four parity vectors**
[MEASURED by `T255` at `a71c140`]. **Being statable was not being graded; now it is both, for these
two invariants and for nothing else in §4.4's table.** `I-3` and `I-4` remain gradeable only by a
source-level guard, because a vector is a snapshot of oracle output and a snapshot cannot observe the
absence of a write; `I-5`'s never-mutates half is unreachable for the same reason (§4.4, revision 6);
`I-6` is out of the contract's domain and `I-7` is not this contract's obligation. §4.4 says all of
this at the point of each claim.""",
)

# ===========================================================================
# H-5b  §4.2
# ===========================================================================
hunk(
    "H-5b §4.2",
    """cell, and the admission rule must evaluate them on exactly those vectors. Whether the *evaluation*
is expressible is a separate question, answered no in §5.""",
    """cell, and the admission rule must evaluate them on exactly those vectors. Whether the *evaluation*
is expressible is a separate question — **revisions 1–6 answered it "no in §5", and it is now YES:
four promoted vectors carry money cells and `G-07`/`G-08` are evaluated on them** [MEASURED by
`T255` at `a71c140`]. §5.1's narrower claim — that no such vector is expressible against the frozen
`gerege.loanschedule.vector/v1` schema — is unaffected and still stands (§5.1, §5.2). **The predicates
themselves are UNCHANGED by revision 7 and by revision 8.**""",
)

# ===========================================================================
# §4.4 lead paragraph — the 35th site
# ===========================================================================
hunk(
    "H-5c §4.4 lead paragraph — the 35th site (nine lines above H-7's cell)",
    """Most of the project's ledger invariants cannot be graded by a `ledger` vector, and **none of them
can be graded today**. Saying which, and saying why the two statements differ, is the honest half of
this contract.""",
    """Most of the project's ledger invariants cannot be graded by a `ledger` vector. **Revisions 1–6 added
*"and none of them can be graded today"*; CORRECTED IN REVISION 8 — `I-1` and `I-2` ARE graded now,
and the rest are not** [MEASURED by `T255` at `a71c140` from its own `VERDICT: PASS (exit 0)` run:
`I-1` (`double_entry_balances`) HOLDs INDEPENDENT on all four parity vectors; `I-2`
(`splits_sum_to_whole`) HOLDs INDEPENDENT on `LDG-02` and `LDG-03`, DEPENDENT on `LDG-01`, and is
reported **N/A on `LDG-04`**]. Saying which, and saying why the two statements differ, is the honest
half of this contract — and it matters **more** now than when nothing was graded, because a per-row
"NO" can no longer be excused by *"the machinery is missing"*.

**⚠ THIS PARAGRAPH IS THE 35th SITE, AND IT IS RECORDED AS SUCH.** Revision 7 corrected the bullet
nine lines below it and the `I-1`/`I-2` cells fifteen lines below it, and left this sentence
asserting the opposite — which would have made §4.4 contradict itself inside twenty lines. It was
found by `T251`'s independent review, not by the sweep that prepared revision 7, **and revision 7's
own sweep had PRINTED it**. The lesson is recorded as a rule in §10's revision-8 entry: *every hit a
sweep prints gets an explicit disposition, and an undisposed hit is a defect.*""",
)

# ===========================================================================
# H-6  §4.4's TODAY bullet
# ===========================================================================
hunk(
    "H-6 §4.4 TODAY bullet",
    """- **TODAY** — can that separation be written down as an admissible vector and evaluated by the
  grader? This is a question about the machinery, and for **every row in this table the answer is
  NO**, because no `ledger` vector of any shape is currently expressible (§5).""",
    """- **TODAY** — can that separation be written down as an admissible vector and evaluated by the
  grader? This is a question about the machinery. **Revisions 1–6 said the answer was NO for every
  row in this table, "because no `ledger` vector of any shape is currently expressible (§5)".
  CORRECTED IN REVISION 7: the machinery exists and the answer is now per-row.** `I-1` and `I-2` are
  **graded**; `I-3`, `I-4`, `I-5`, `I-6` and `I-7` are **not**, each for a reason column 5 states at
  the point of the claim, and none of those reasons is "the machinery is missing" any more
  [MEASURED by `T255` at `a71c140`; the harness prints an `INVARIANT … HOLD` line per vector, and
  marks a hold that no implementation could fail as `DEPENDENT` rather than counting it].""",
)

# ===========================================================================
# H-7 / H-8 / H-9 — the three table cells
# ===========================================================================
hunk(
    "H-7 I-1 row, final cell only",
    """| **NO.** §5 — no admissible vector can carry a money cell, or any `ledger` cell. |""",
    """| **YES, SINCE `A2-15` — AND REVISION 7 CORRECTS WHAT REVISIONS 1–6 SAID HERE, WHICH WAS *"NO. §5 — no admissible vector can carry a money cell, or any `ledger` cell."*** Four promoted `ledger` parity vectors each carry the assertion, and the harness reports it per vector as `INVARIANT double_entry_balances HOLD (2 assertion(s), INDEPENDENT)` — `LDG-01` debits `12500062` == credits `12500062` over 3 legs; `LDG-02` `30000000` over 4; `LDG-03` `100000000` over 4; `LDG-04` `10000025` over 2 — all in `int64` minor units [MEASURED by `T255` at `a71c140` from its own `VERDICT: PASS (exit 0)` run; `LEDGER money cells compared = 21 == pinned 21`]. **What that does and does not buy:** it grades `I-1` **on the four shapes those vectors record**, all MNT, all from `ledger_rest_posting`/`ledger_db_readback`, and on nothing else — no accrual, no transfer, no reversal, no multi-currency, no closure. **A green `I-1` is evidence about four entries, not about the ledger.** |""",
)

hunk(
    "H-8 I-2 row, final cell only",
    """| **NO.** Same reason. |""",
    """| **YES, ON TWO OF THE FOUR — AND THE HARNESS REFUSES TO COUNT THE OTHER TWO, WHICH IS THE POINT.** Revisions 1–6 said *"NO. Same reason."*, inheriting `I-1`'s now-dead ground. **`LDG-02` and `LDG-03` grade it INDEPENDENTLY**: the whole comes from the **recorded REQUEST**, not from a leg — `30000000 == sum of 3 splits` and `100000000 == sum of 3 splits`, `int64` minor units. **`LDG-01` reports `DEPENDENT` and `LDG-04` reports `N/A`**, and the harness says why in its own words: on `LDG-01` *"the whole here IS one of the entry's own legs, so this equation is character-for-character the one `I-1` already asserted … and no implementation can fail one and pass the other"*; on `LDG-04` a 2-leg entry *"is not a split shape … declared not-applicable rather than reported as a hold that nothing could fail"* [MEASURED by `T255` at `a71c140`]. **So the honest count is 2 independent assertions, not 4** — `P-35`, applied by the instrument to itself. **The defect this grades at all is real and was invisible before `A2-15`:** every journal entry in the A2 corpus had exactly two legs and every amount was a whole tugrik, so a port that dropped minor units was byte-indistinguishable from a correct one on every capture ever taken. |""",
)

hunk(
    "H-9 I-7 row, final cell only",
    """| **N/A** — and note that today there is no `ledger` conformance PASS to say nothing with. |""",
    """| **N/A** — and, CORRECTED IN REVISION 7, **there IS now a `ledger` conformance PASS, and it still says nothing whatever about `I-7`.** Revisions 1–6 read *"today there is no `ledger` conformance PASS to say nothing with"*. There is: 4 parity / 2 oracle-refusal / 21 money cells, green [MEASURED by `T255` at `a71c140`]. **The correction makes this row MORE important, not less** — the `Idempotency-Key` obligation is unmoved, no ledger vector tests it, and a green ledger section is now available to be misquoted as though it did. |""",
)

# ===========================================================================
# C-2 — the I-3 row's supporting citation
# ===========================================================================
hunk(
    "C-2 the I-3 row's supporting citation (its 'Graded today?' answer is NO and stays NO)",
    """`guard_ledger_invariants` (built by `A2-18`, **wired** by `T208`) is the seventh guard `run_guards` invokes and it walks the Go tree for a write path to a balance [VERIFIED by `A2-28` at commit `2e97162`: `.softhouse/conformance.sh:1152-1187` defines it, `:1209` invokes it; MEASURED: `invariant violations 0`].""",
    """`guard_ledger_invariants` (built by `A2-18`, **wired** by `T208`) is one of the guards `run_guards` invokes — **§4.4.1 carries the single DERIVED-FROM-SOURCE enumeration and this row restates no count from it (`P-79`)** — and it walks the Go tree for a write path to a balance [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`; MEASURED by `T255` at `a71c140`: `invariant violations 0`]. **⚠ Revisions 3–7 said *"is the seventh guard `run_guards` invokes"* here and cited `.softhouse/conformance.sh:1152-1187` / `:1209`. This row's *"Graded today?"* answer was NO and is still NO, so no wording sweep over the answer column ever reached the falsehood in its SUPPORTING CITATION — which is why revision 8 removes the line numbers rather than refreshing them.**""",
)

# ===========================================================================
# H-10  the rule paragraph — OBLIGATIONS CARRIED VERBATIM
# ===========================================================================
hunk(
    "H-10 the rule paragraph (both obligations carried forward verbatim)",
    """**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope.""",
    """**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context. **Revisions 1–6 added "and grades none of them today"; REVISION 7 CORRECTS
THAT CLAUSE AND ONLY THAT CLAUSE — it grades `I-1` on all four parity vectors and `I-2` on three of
the four, INDEPENDENTLY on two, and grades `I-3`, `I-4` and `I-5` by nothing** [MEASURED by `T255`
at `a71c140`; `LDG-04` reports `splits_sum_to_whole N/A` and `LDG-01` reports it `DEPENDENT`, which
is not a second piece of evidence — see the `I-2` row above]. **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope — **unchanged by revision 7, unchanged by revision 8, and unchanged BY the six
vectors**: a vector is a snapshot of oracle output and cannot observe the absence of a write, so no
growth of this corpus will ever discharge them.""",
)

# ===========================================================================
# C-3  §4.4.1 — the fenced enumeration, the arithmetic, "The seventh does"
# ===========================================================================
hunk(
    "C-3a §4.4.1 the guard enumeration — now DERIVED-FROM-SOURCE and COMPLETE (eight, not seven)",
    """**`run_guards` invokes SEVEN guards** [VERIFIED by `A2-28` at commit `2e97162`,
`.softhouse/conformance.sh:1189-1213`, opened and read line by line; the first short-circuits with
`exit` rather than joining the `failed` tally. An independent review counted this **two ways** —
`guard_*()` definitions in the file, and invocation sites inside `run_guards`'s body — and got seven
both times]:

```
  guard_graded_root_is_this_tree        # short-circuits: is $REPO_ROOT the tree being graded?
  guard_no_float_in_vectors
  guard_no_float_in_harness
  guard_gofmt
  guard_no_float_in_capture_requests
  guard_no_narrow_catch_in_capture_rigs
  guard_ledger_invariants               # I-3 / I-4 — A2-18, wired by T208
```

**Five of the seven still concern floating point, source formatting and exception scope, and a
sixth concerns the repo root. None of those six looks for:**""",
    """**THIS IS THE DOCUMENT'S ONLY ENUMERATION OF `run_guards`' INVOCATIONS. Every other section points
here by section number and restates no count from it (`P-79`).** The block below is **DERIVED FROM
SOURCE, NOT TRANSCRIBED**: `.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py`
re-parses `run_guards()`' body out of `.softhouse/conformance.sh`
[ANCHOR .softhouse/conformance.sh :: `run_guards() {`] and compares this list, IN ORDER, against it —
so a guard added, removed, renamed or reordered makes this block fail rather than lie. **It contains
no line number, so an edit ABOVE it cannot invalidate it.**

```
DERIVED-FROM-SOURCE: run_guards() in .softhouse/conformance.sh
verified by .softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py
  guard_graded_root_is_this_tree        # SHORT-CIRCUITS with `exit`; does NOT join the tally
  guard_no_float_in_vectors             # tallied
  guard_no_float_in_harness             # tallied
  guard_gofmt                           # tallied
  guard_no_float_in_capture_requests    # tallied
  guard_no_narrow_catch_in_capture_rigs # tallied
  guard_ledger_invariants               # tallied — I-3 / I-4, A2-18, wired by T208
  guard_no_fail_open_instruments        # tallied — T238's fail-open linter, wired by T243
```

[DERIVED: run_guards invokes 8 | tallies 7 | `guard_ledger_invariants` is invocation #7 and tallied #6]

**⚠ RETRACTION, revision 8 — THIS LIST WAS INCOMPLETE, AND IT READ AS AUTHORITATIVE.** Revisions
3–7 headed it *"`run_guards` invokes SEVEN guards"*, cited
`.softhouse/conformance.sh:1189-1213`, and listed **seven** names, **omitting
`guard_no_fail_open_instruments`** — which `T243` wired and which has been invoked on every run
since. The count and the citation are both fixed here, and **the ordinal is deliberately not
restated in prose anywhere else**: *"the seventh guard"* was TRUE on the all-invocations basis and
FALSE on the tallied basis, the basis was switched silently between revisions, and that is precisely
how an ordinal used as an identifier goes wrong without anyone noticing. **The identifier is the
NAME.** Both bases are given in the `[DERIVED: …]` token above so that no reader has to guess one,
and both are re-derived from source rather than remembered.

**Six of the eight concern floating point, source formatting, exception scope, the repo root and
fail-open instruments — a count DERIVED from the block above by subtraction, not independently
asserted. None of those six looks for:**""",
)

hunk(
    "C-3b §4.4.1 'The seventh does'",
    """**The seventh does, and this is what it actually delivers** [VERIFIED by `A2-28` at commit
`2e97162`: `.softhouse/conformance.sh:1152-1187`, the definition and its in-file commentary read in
full; MEASURED by `A2-28` at commit `2e97162` from its own unfiltered run, quoted verbatim]:""",
    """**`guard_ledger_invariants` does, and this is what it actually delivers** — named, not numbered,
for the reason the retraction above gives [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`],
its definition and in-file commentary read in full; the transcript below was MEASURED by `A2-28` at
commit `2e97162` from its own unfiltered run and is quoted verbatim as the record of that run —
`T255` re-ran the guard at `a71c140` and it still prints `ledger-invariants: PASS` with
`invariant violations 0`, over a census that has grown (56 Go files / 6 packages at `a71c140`,
against the 45 / 5 recorded below), **which is exactly why the transcript is labelled as a stamped
record and not as today's census**:""",
)

# ===========================================================================
# H-11  §4.9(b)
# ===========================================================================
hunk(
    "H-11 §4.9(b) block quote",
    """> **THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN.** The vector schema has exactly
> two expectation kinds, `schedule` and `refusal`, and `refusal` means one of the three **contract**
> sentinels above. There is no encoding for *"the oracle answered 404 with
> `error.msg.productToAccountMapping.not.found`"* — and filing it as a contract refusal would write
> this subsection's own named defect into the corpus. Establishing this is §5.1; a representation
> for it is precondition **P-2** in §5.3. **Every row of the (b) table is therefore ungraded today**,
> including the three `A2-224` / `A2-225` / `A2-092` message-for-message gradings, which exist as
> **Go tests** against committed bytes and not as vectors (§5).""",
    """> **⚠ REVISION 7 CORRECTS THE GROUND OF THIS BLOCK AND KEEPS ITS CONCLUSION. Revisions 1–6 said
> "THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN". It CAN, and it is.** An
> oracle-faithful refusal is now expressible and graded: the second schema carries
> `class: oracle-refusal` and an `expect.refusal` of **HTTP status + error code + message text**,
> explicitly not a contract sentinel, and two such vectors pass on every run —
> `LDG-REFUSE-01` (`403`, `error.msg.glJournalEntry.invalid.mismatch.debits.credits`, *"Sum of All
> Debits must equal the sum of all Credits for a Journal Entry"*) and `LDG-REFUSE-02` (`403`,
> `error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted`) [MEASURED by `T255`
> at `a71c140`]. The harness labels them, in its own words, *"an HTTP status and error code the
> ORACLE returned and a capture recorded — NOT a contract sentinel"*. **Precondition `P-2` was the
> representation this block said was missing; it exists.**
>
> **The conclusion is UNCHANGED and still true: every row of the (b) table above is ungraded today
> — for a different and narrower reason.** Neither promoted refusal is a (b) row. The (b) rows are
> mapping-not-found, duplicate mapping rows, the slot type check, the financial-activity
> duplicate/invalid pairing, and the GL-account refusal family — **all of them reached through slot
> resolution, and `capabilities-ledger.json` carries `ledger.slot.resolution` with
> `in_graded_domain: false`, so a vector claiming one would be REFUSED rather than graded**
> [MEASURED by `T255` at `a71c140`]. The three `A2-224` / `A2-225` / `A2-092` message-for-message
> gradings still exist as **Go tests** against committed bytes and not as vectors. **What blocks
> them now is a missing CAPTURE and a capability marked false, not a missing ENCODING** — and that
> distinction is the difference between "nobody has done it" and "it cannot be done", which this
> document has already been rejected once for collapsing (§5.1.1).""",
)

# ===========================================================================
# C-5  §5's heading
# ===========================================================================
hunk(
    "C-5 §5 heading — asserted the proposition H-12 retracts 26 lines below it",
    """## 5. What DEC-2 would be frozen against — and today that is ZERO vectors""",
    """## 5. What DEC-2 is frozen against — and (revisions 1–7) "today that is ZERO vectors\"""",
)

# ===========================================================================
# H-12  §5's baseline prose
# ===========================================================================
hunk(
    "H-12 §5 baseline prose",
    """`.softhouse/vectors/` holds **46 promoted parity vectors, all `loanschedule`** [MEASURED above; the
store's only context directories are `loanschedule/` and `_selftest/`]. **The `ledger` context has
none.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to
the minor unit; **DEC-2 would be frozen against a corpus that does not yet exist in the store.**""",
    """**⚠ RE-MEASURED IN REVISION 8, AND THE THIRD MOVE OF THIS BASELINE IS THE ONE THE NOTE BELOW DID
NOT ANTICIPATE — IT WAS A NEW CONTEXT, NOT A BIGGER COUNT. The heading of this section still carries
the old claim in quotation marks, and it is retracted here.** The transcript above is a stamped
historical baseline at store tree `73c3ea7b…` and is kept as such. **At `a71c140`** the store holds
**46 promoted `loanschedule` parity vectors** — still all `loanschedule`, still zero touching a GL
account — **and, separately, six `ledger` vectors: 4 `parity` + 2 `oracle-refusal`, 70 cells of which
21 are money**; store tree `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` [MEASURED by `T255` at
`a71c140`, `git rev-parse HEAD:.softhouse/vectors`].

Revisions 1–6 said *"**The `ledger` context has none**"* and *"DEC-2 **would be frozen against a
corpus that does not yet exist in the store**"*. **Both were true when written and both are false at
this commit.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to the minor
unit; **DEC-2 was ratified at revision 5 against a corpus that did not then exist, and the corpus
arrived 2 h 13 m later.** That ordering is not a defect — a contract must precede the vectors it
admits — but it is exactly the mechanism that made this document's opening banner false, and §5.2's
requirements were written against a **freshly measured** baseline rather than a literal for precisely
this reason.""",
)

# ===========================================================================
# the go-test citation (a live site neither review enumerated)
# ===========================================================================
hunk(
    "C-9 the `go test` citation — a live stale site neither review enumerated",
    """  guards.** `conformance.sh` never runs `go test`, so a regression in them does not turn the
  harness red [RE-VERIFIED by `A2-16`: the script contains **no** `go test` invocation — both
  occurrences of the string are comments, at `conformance.sh:718` and `:721`; its only Go command is
  a `go build` of the conformance `cmd` package — and it says so itself at `conformance.sh:721`,
  *"`conformance.sh` never runs `go test`, so a Go-test-only guard is not a guard"* (P-45). The line
  numbers moved between revisions; the fact did not.].""",
    """  guards.** `conformance.sh` never runs `go test`, so a regression in them does not turn the
  harness red [RE-MEASURED by `T255` at `a71c140`: the script contains **no** `go test` invocation —
  every occurrence of the string is a comment; its only Go command is a `go build` of the
  conformance `cmd` package — and it says so itself at
  [ANCHOR .softhouse/conformance.sh :: `so a Go-test-only guard is not a`]
  (P-45). **⚠ Revisions 1–7 cited `conformance.sh:718` and `:721` and said *"both occurrences"*.
  BOTH numbers were stale at `a71c140` — `:718` and `:721` are comments about
  `guard_no_float_in_harness` — and the count was stale too: there are FOUR occurrences of the
  string, all comments, not two. The prose that followed, *"the line numbers moved between
  revisions; the fact did not"*, was an accurate diagnosis paired with no remedy; revision 8 applies
  the remedy.].""",
)

# ===========================================================================
# H-12b  §5.1 scope note
# ===========================================================================
hunk(
    "H-12b §5.1 scope note appended (the heading itself is NOT changed)",
    """### 5.1 No `ledger` vector is expressible against the frozen vector schema — MEASURED

**This is finding R-1, and revision 1's central claim about it —** *"Disposition 3 needs no new
machinery, and that is the argument for it"* **— was false.** Revision 2 retracts it.""",
    """### 5.1 No `ledger` vector is expressible against the frozen vector schema — MEASURED

**⚠ READ THE SCOPE OF THIS HEADING, revision 7. The heading is CORRECT and is NOT changed.**
*"Against the frozen vector schema"* means against **`gerege.loanschedule.vector/v1`**, and within
that scope every one of §5.1's five legs is still true and was never falsified — a
`loanschedule`-schema file placed in `ledger/` is INADMISSIBLE by name. **What has changed is that a
SECOND schema now exists**, `gerege.ledger.vector/v1`
[ANCHOR nexus/internal/apps/ledger/conformance/vector.go :: `// It is the string DEC-2 §5.2 names: "gerege.ledger.vector/v1".`],
and a `ledger` vector is expressible and graded against **that** [MEASURED by `T255` at `a71c140`].
§5.2 named exactly this extension and adopted it; `A2-15` built it. **The banner's old item 2
restated this heading with the scope dropped, and that unscoped restatement is what revision 7
retracts — not this section.**

**This is finding R-1, and revision 1's central claim about it —** *"Disposition 3 needs no new
machinery, and that is the argument for it"* **— was false.** Revision 2 retracts it.""",
)

# ===========================================================================
# §5.2 heading and the "(a) is adopted" paragraph
# ===========================================================================
hunk(
    "C-10a §5.2 heading — a present-tense state claim that revision 7 relies on and contradicts",
    """### 5.2 The decision: EXTEND the machinery — and DEC-2 grades nothing until it exists""",
    """### 5.2 The decision: EXTEND the machinery — and (revisions 1–7) "DEC-2 grades nothing until it exists\"""",
)

hunk(
    "C-10b §5.2 '(a) is adopted' — the machinery WAS built; requirements 1-7 UNCHANGED",
    """**(a) is adopted. The machinery is named, it is not built here, and this document does not pretend
it is anywhere else either.** Three things follow, and revision 2 states all three as normative.""",
    """**(a) is adopted. The machinery is named, it is not built here, and this document does not pretend
it is anywhere else either.** Three things follow, and revision 2 states all three as normative.

> **⚠ REVISION 8: THE MACHINERY DESCRIBED BELOW WAS BUILT, AND THIS SECTION'S HEADING STILL CARRIES
> THE OLD CLAIM IN QUOTATION MARKS.** This section was written while `gerege.ledger.vector/v1` did
> not exist, and its heading and its *"not built here … nor anywhere else either"* framing are
> preserved as the record of the DECISION, not as a statement of today's world. `A2-15` built it;
> six vectors are promoted and green [MEASURED by `T255` at `a71c140`].
> **REQUIREMENTS 1–7 BELOW ARE NORMATIVE AND ARE UNCHANGED BY REVISION 7 AND BY REVISION 8** — not
> one word of them moves. They are the standard `A2-15`'s work is to be judged against, and §5.3's
> revision-7 note records that no task has yet re-derived that each was met.""",
)

# ===========================================================================
# H-13  §5.3
# ===========================================================================
hunk(
    "H-13a §5.3 preconditions note (the TEN-ROW TABLE IS NOT TOUCHED)",
    """`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.""",
    """`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.

> **⚠ STATUS RE-MEASURED IN REVISION 7 — AND READ WHAT THIS NOTE DOES *NOT* SAY.**
> **`A2-15` is `status: done` and has promoted six `ledger` vectors, all green** [MEASURED by `T255`
> at `a71c140`]. **The table below is UNCHANGED — no row, no identifier, no order, no DEPENDS-ON
> cell, and no `why` — because these are OBLIGATIONS and revisions 7 and 8 change no obligation.**
> What is corrected is the *factual* summary that used to follow the table, which said **"Nine open,
> one landed"**; that is false at this commit.
>
> **What IS measured:** the second schema's package addresses **P-1, P-2, P-3, P-4, P-6, P-7, P-9 and
> P-10 by name** — its `SchemaV1`, `Request`, `Refusal`, `ClassOracleRefusal`, `SchemaContexts` and
> `DEC2Revision` declarations, its `grade.go` comparator, its `capability.go` registry, its
> `impl.go` wrong-implementation set and its `admit.go` admission rules — and the harness demonstrates
> the two that a declaration alone could not: `P-4`'s comparator graded **70 ledger cells**, and
> `P-10`'s registry discovered **6** deliberately-wrong ledger implementations from the binary's own
> `-list-implementations` and **killed all six through the harness, not by hand** [MEASURED by
> `T255` at `a71c140`]. **Revision 8 gives these by NAME rather than by the `file:line` list revision
> 7 drafted**, under the citation rule at the head of this document: eleven perishable line numbers
> in one bracket is eleven chances to be wrong about nothing.
>
> **What is NOT measured, stated plainly rather than smoothed over:**
> **(i)** `P-5` is the one precondition the ledger package **names nowhere** —
> `git grep -P '\\bP-5\\b' -- nexus/internal/apps/ledger` returns nothing (exit 1, a REAL measured
> negative, not an error swallowed — `P-80`), across the tracked files of that package, while every
> one of its nine siblings `P-1`…`P-4` and `P-6`…`P-10` is found by the identical probe. Its
> substance is present and measurable (21 money cells, `int64` minor-unit strings paired with the
> oracle's own emitted characters as a transcription cross-check), but the marker every other
> precondition carries is absent.
> **(ii)** **REVISION 7 DOES NOT CERTIFY THAT ANY PRECONDITION IS *ADEQUATELY* DISCHARGED, AND
> NEITHER DOES REVISION 8.** That is a review of `A2-15`'s work; nobody has done it, and asserting it
> inside a ratified contract on the strength of source declarations would be a fresh unsupported
> inference of exactly the class that rejected this document three times. `FU-T247-3` files the
> re-derivation. **A ratifier must read this note as "the preconditions were addressed and the corpus
> is green", never as "P-1…P-10 are discharged".**""",
)

hunk(
    "H-13b §5.3 'Nine open, one landed'",
    """**Nine open, one landed.** P-6, P-1, P-7, P-2, P-3, P-4, P-5, P-9 and **P-10** remain; **P-8 is
done** and is kept in the table with its residue rather than deleted, so that a later reader can tell
"discharged, with limits" from "never required". **Revision 4 adds P-10 and renumbers nothing** — the
identifiers are referenced from six sections, the harness source and several handoffs, and the same
rule that protected P-1…P-9 in revision 3 protects them here.""",
    """**⚠ "Nine open, one landed" was revision 4's count and REVISION 7 RETRACTS IT AS A CURRENT FACT.**
It was true when written: at revision 4 only `P-8` had landed. At `a71c140` `A2-15` is done, six
vectors are promoted and green, and all ten preconditions are addressed — with the two caveats the
note above states and does not soften. **Rows are kept, never deleted, so a later reader can tell
"discharged, with limits" from "never required"** — the rule `P-8` established, now applied to all
ten. **Revision 4 added P-10 and renumbered nothing**; the identifiers are referenced from six
sections, the harness source and several handoffs, and the same rule that protected P-1…P-9 in
revision 3 protects them here, in revision 7 and in revision 8.""",
)

# ===========================================================================
# the -context citation
# ===========================================================================
hunk(
    "C-11 the `-context` citation",
    """- **`conformance.sh` passes `-context` only when it was given an argument:**
  `[ -n "$context" ] && args+=("-context=$context")` [VERIFIED by this task:
  `.softhouse/conformance.sh:1254`].""",
    """- **`conformance.sh` passes `-context` only when it was given an argument:**
  `[ -n "$context" ] && args+=("-context=$context")`
  [ANCHOR .softhouse/conformance.sh :: `[ -n "$context" ] && args+=("-context=$context")`].
  **⚠ Revisions 1–7 cited `.softhouse/conformance.sh:1254` for this. That line is a comment about
  the `I-3`/`I-4` guard's detection classes at `a71c140` — the citation is bound to the line it
  quotes now, and the quoted line IS the anchor.**""",
)

# ===========================================================================
# H-14  §8.1
# ===========================================================================
hunk(
    "H-14a §8.1 heading and preamble",
    """### 8.1 NOTHING GRADES THE LEDGER — say it here, not only in the banner

The banner at the head of this document says this. It is repeated here, at the end, because §8 is
what a ratifier reads last and because revision 1's §8 said something adjacent that a reader will
merge with it.

**Four facts. Each was RE-MEASURED by `A2-28` at commit `2e97162`, and fact 3's numerator was
RE-MEASURED AGAIN by `A2-32` at commit `33d19a6`; each carries the stamp of the task that took it.**
Revision 3 introduced this list as *"Four facts, each measured by this task"* while fact 3 contained
a figure nobody had ever measured (`A2-25` F-2; §4.4.1's `P-67` box) — **and revision 4 rewrote this
heading to promise the fix while fact 3 still carried an unmeasured numerator** (`A2-31` F-2). **A
heading that asserts measurement is a claim; it has now been wrong twice in this exact slot, and it
is checked here.**""",
    """### 8.1 WHAT GRADES THE LEDGER, AND WHAT DOES NOT — say it here, not only in the banner

**⚠ THIS SECTION'S HEADING READ "NOTHING GRADES THE LEDGER" IN REVISIONS 1–6, AND IT WAS FALSE.**
It is repeated at the end of the document, as it always has been, because §8 is what a ratifier
reads last and because revision 1's §8 said something adjacent that a reader will merge with it.
**It went false in the same instant the banner did**, and it is corrected in the same revision — a
correction landing where a reviewer NAMED it and not where the document RESTATES it is the defect
class that has rejected this document three times (`P-21`, `P-26`).

**Four facts. RE-MEASURED by `T255` at commit `a71c140`; each carries the stamp of the task that
took it.** Revision 3 introduced this list as *"Four facts, each measured by this task"* while fact 3
contained a figure nobody had ever measured (`A2-25` F-2; §4.4.1's `P-67` box) — **and revision 4
rewrote this heading to promise the fix while fact 3 still carried an unmeasured numerator**
(`A2-31` F-2) — **and revisions 5 and 6 left facts 1 and 2 asserting, under that same heading, a
world that had ceased to exist** (`T246` F-1; `G-14`) — **and revision 7 replaced fact 3's citations
with line numbers that were stale before it could land** (`T251` F-T251-1). **A heading that asserts
measurement is a claim; it has now been wrong four times in this exact slot, and revision 8 removes
the perishable identifier rather than refreshing it a fourth time.**""",
)

hunk(
    "H-14b §8.1 facts 1 and 2",
    """1. **Zero `ledger` vectors exist.** The store's only context directories are `loanschedule/` and
   `_selftest/`.
2. **Zero `ledger` vectors are EXPRESSIBLE** — §5.1, established in code in five legs, all five
   re-opened and confirmed by independent review. Preconditions P-1…P-5 (§5.3) do not exist.""",
    """1. **SIX `ledger` vectors exist and all six PASS: 4 `parity`, 2 `oracle-refusal`, 21 money cells in
   `int64` minor units.** The store's context directories are `_selftest/`, `ledger/` and
   `loanschedule/` [MEASURED by `T255` at `a71c140`].
   **⚠ RETRACTION, revision 7: revisions 1–6 wrote *"Zero `ledger` vectors exist. The store's only
   context directories are `loanschedule/` and `_selftest/`"* here, and the banner said the same and
   cited `ls .softhouse/vectors/` as its evidence.** `A2-15` promoted the six vectors **2 h 13 m**
   after revision 5 landed (`cab9e82` → `1325e8b`), and the claim then stood through revision 6,
   which corrected a different sentence in the same document. **It is restated rather than reworded
   because a silent downgrade would hide that this document told every reader, in its first
   instruction, to believe a fact its own cited command refutes.**
2. **A `ledger` vector IS expressible, against a SECOND schema — and §5.1's five legs are
   untouched.** `gerege.ledger.vector/v1`
   [ANCHOR nexus/internal/apps/ledger/conformance/vector.go :: `// SchemaV1 is the only schema string this package accepts.`],
   with its own request/expectation shapes, class set, comparator, cell whitelist, context
   allowlist, store pin and capability registry. §5.1's claim — *no `ledger` vector is expressible
   **against the frozen `gerege.loanschedule.vector/v1` schema*** — is **still true**, and the five
   legs that establish it were never falsified.
   **⚠ RETRACTION, revision 7: revisions 1–6 wrote *"Zero `ledger` vectors are EXPRESSIBLE …
   Preconditions P-1…P-5 (§5.3) do not exist."*** The preconditions are addressed; §5.3's revision-7
   note records exactly what that is measured to mean and — expressly — what it does **not**
   certify.""",
)

hunk(
    "H-14c §8.1 fact 3's guard citation",
    """   `run_guards` invokes **seven** guards, not five; the seventh is `guard_ledger_invariants`
   [`.softhouse/conformance.sh:1152-1187` defines it, `:1209` invokes it], built by `A2-18` and
   wired by `T208`, and `A2-28` measured `invariant violations 0` at commit `2e97162`.
   **⚠ Revision 2 said no such guard existed. That was true when written and is stale.**""",
    """   The guard is `guard_ledger_invariants`
   [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`], built by `A2-18` and wired by
   `T208`, and `T255` measured `invariant violations 0` at `a71c140`. **§4.4.1 carries the ONE
   DERIVED-FROM-SOURCE enumeration of `run_guards`' invocations and this fact restates no count from
   it (`P-79`)** — which is the whole point: revisions 3–7 restated *"seven … the seventh"* here as
   well as in the banner and in the `I-3` row, so one correction had to land in four places and
   never did.
   **⚠ Revision 2 said no such guard existed. That was true when written and is stale.**
   **⚠ REVISION 8 REMOVED THIS FACT'S LINE NUMBERS.** Revisions 3–6 cited
   `.softhouse/conformance.sh:1152-1187` / `:1209`, correct at `2e97162` and stale by revision 7;
   revision 7 replaced them with `:1300-1339` / `:1474-1500` / `:1494`, which were stale before it
   could land. **A citation that has to be re-taken every fire is not a citation.**""",
)

hunk(
    "H-14d §8.1 fact 4 and the closing sentence",
    """4. **The 46 passing parity vectors are `loanschedule`'s** [MEASURED by `A2-28` at commit `2e97162`;
   it was 43 at revision 3, and `T116` promoted three in between — **re-measure, do not copy**].
   None touches a GL account, a mapping, a financial activity or a journal entry. The directory
   boundary **was not enforced** when revision 2 leaned on it (fact 2's retraction); **it is enforced
   now**, at admission, by a context allowlist tied to the schema [`conformance/vector.go:77-81`,
   `admit.go:139-147`].

**Ratifying DEC-2 changes none of the four.** It writes down a boundary; it grades nothing. The two
must never be confused, and a citation of this document as evidence of ledger coverage is a
misreading of it.""",
    """4. **The 46 passing `loanschedule` parity vectors are still `loanschedule`'s** [RE-MEASURED by
   `T255` at `a71c140`; it was 43 at revision 3, and `T116` promoted three in between —
   **re-measure, do not copy**]. None touches a GL account, a mapping, a financial activity or a
   journal entry. The directory boundary **was not enforced** when revision 2 leaned on it (fact 2's
   retraction); **it is enforced now**, at admission, by a context allowlist tied to the schema
   [ANCHOR nexus/internal/apps/loanschedule/conformance/vector.go :: `// IsSchemaContext reports whether ctx is one of SchemaContexts().`].
   **The `ledger` corpus is counted separately — the harness heads it "SECOND SCHEMA, SECOND
   COMPARATOR, SEPARATE COUNTS" — and quoting either number for the other context is the error this
   fact exists to prevent.**

**⚠ THE CLOSING SENTENCE OF THIS SECTION IS REPLACED. Revisions 1–6 read: *"Ratifying DEC-2 changes
none of the four. It writes down a boundary; it grades nothing."*** DEC-2 **was** ratified, the
machinery it named **was** built, and it **does** grade — narrowly. **What survives, and is now the
load-bearing sentence of this document:** **grading 6 of 14 declared capabilities is not coverage.**
Eight capabilities are declared OUT of the graded domain by name — slot resolution, accrual,
transfers suspense, charge-off, multi-currency, opening balances and `GLClosure`, reversals, running
balances — `I-3` and `I-4` are graded by no vector, `G-12` is OPEN on the running-balance columns,
and **a citation of this document, or of a green ledger section, as evidence of ledger coverage is a
misreading of both.** Cutover remains a hard `user` gate.""",
)

# ===========================================================================
# H-15  §8.2 and §8.3
# ===========================================================================
hunk(
    "H-15a §8.2",
    """### 8.2 If ratified

- `.softhouse/vectors/ledger/` becomes a legal context directory **for the second schema, and only
  for it** — a `gerege.loanschedule.vector/v1` file placed there is INADMISSIBLE, by name, since
  `A2-20` [`admit.go:139-147`]. It **stays unusable until the §5.3 machinery lands**, at which point
  `conformance.sh ledger` becomes a meaningful command.
- `A2-15` has an admissibility standard: §4.2's predicates, §4.6's A-1…A-4, §4.10's registry, §5.5's
  `graded_against` requirement, and **§5.2's requirements 1–7** — the last two of which are a
  positive control (now **6a** on the same bytes and **6b** on the admission layer's own bytes) and
  a required RED demonstration, without which an extension that does nothing would satisfy the
  specification. **Nine of the ten §5.3 preconditions remain — P-1…P-7, P-9 and the new P-10; only
  P-8 has landed — and `A2-15` cannot start without them.**
- The GL/accounting context acquires a boundary a regulator can be shown. **"PASS 46" remains the
  only thing anyone can say about the ledger, and what it says is "this is about a different
  context"** [count MEASURED by `A2-28` at commit `2e97162`; it moves, the sentence does not].""",
    """### 8.2 Now that it is ratified

- **`.softhouse/vectors/ledger/` IS a legal context directory, for the second schema and only for
  it** — a `gerege.loanschedule.vector/v1` file placed there is INADMISSIBLE, by name, since `A2-20`
  [ANCHOR nexus/internal/apps/loanschedule/conformance/admit.go :: `"declaring an unknown context is INADMISSIBLE and not merely unmatched: the harness "+`],
  and the second schema's own `SchemaContexts()` returns `{ledger}`
  [ANCHOR nexus/internal/apps/ledger/conformance/vector.go :: `func SchemaContexts() []string {`].
  **⚠ Revisions 1–6 said it *"stays unusable until the §5.3 machinery lands, at which point
  `conformance.sh ledger` becomes a meaningful command"*. The machinery landed and the command is
  meaningful**: it grades 4 parity and 2 oracle-refusal vectors over 70 cells, 21 of them money
  [MEASURED by `T255` at `a71c140`].
- **`A2-15` had an admissibility standard and used it**: §4.2's predicates, §4.6's A-1…A-4, §4.10's
  registry, §5.5's `graded_against` requirement, and **§5.2's requirements 1–7** — the last two of
  which are a positive control (**6a** on the same bytes, **6b** on the admission layer's own bytes)
  and a required RED demonstration, without which an extension that does nothing would satisfy the
  specification. **That RED demonstration is now executed rather than declared: 6 deliberately-wrong
  ledger implementations, discovered from the binary's own `-list-implementations`, all 6 killed
  through the harness** [MEASURED by `T255` at `a71c140`]. **⚠ Revisions 1–6 closed this bullet with
  *"Nine of the ten §5.3 preconditions remain … and `A2-15` cannot start without them"*; `A2-15` is
  `done`. Read §5.3's revision-7 note for what that is measured to mean and what it does not
  certify.**
- The GL/accounting context has a boundary a regulator can be shown, **and now a small number a
  regulator can be shown too**. **⚠ Revisions 1–6 said *"'PASS 46' remains the only thing anyone can
  say about the ledger, and what it says is 'this is about a different context'"*. That is no longer
  the only thing — but the sentence's WARNING is intact and the new numbers need it more.** `PASS 46`
  is still about a different context. The ledger's own numbers are **4 / 2 / 21**, and they are about
  **six entries** [MEASURED by `T255` at `a71c140`; both counts move, the warning does not].""",
)

hunk(
    "H-15b §8.3 heading and first bullet",
    """### 8.3 If ratified, these remain true and must not be misread

- **A `ledger` conformance PASS would mean "matches the reference oracle on captured vectors, inside
  the graded domain".** It would not mean the ledger is correct, and it would mean nothing at all
  about savings, shares, working-capital loans, charges, reversals, holds, or nineteen of the
  twenty-three cash placeholder slots. **Today there is no such PASS to misread.**""",
    """### 8.3 These remain true and must not be misread

- **A `ledger` conformance PASS means "matches the reference oracle on captured vectors, inside the
  graded domain".** It does not mean the ledger is correct, and it means nothing at all about
  savings, shares, working-capital loans, charges, reversals, holds, or nineteen of the twenty-three
  cash placeholder slots. **⚠ Revisions 1–6 closed this bullet with *"Today there is no such PASS to
  misread."* THERE IS ONE NOW, and this bullet is therefore no longer hypothetical — it is the
  operative instruction for reading the harness output.** The graded domain is **6 of the 14
  capabilities `capabilities-ledger.json` declares**, both terms counted [MEASURED by `T255` at
  `a71c140`]; the harness prints all **8** ungraded ones on every run, pass or fail, derived from
  that file rather than hand-written, so a gap cannot go unprinted.""",
)

hunk(
    "C-6/C-7 §8.3 second bullet — 'the seventh guard', twice",
    """  **Revision 3 corrects revision 2's "and for nothing else", which was true when written**: the
  seventh guard exists now (§4.4.1). **It does not make the ledger covered** — its own transcript""",
    """  **Revision 3 corrects revision 2's "and for nothing else", which was true when written**:
  `guard_ledger_invariants` exists now (§4.4.1, which carries the only enumeration and the only
  count — `P-79`). **⚠ Revisions 3–7 called it *"the seventh guard"* here and again four lines
  below; revision 8 names it instead, because the ordinal was true on one counting basis and false
  on another and nothing in the sentence said which.** **It does not make the ledger covered** — its
  own transcript""",
)

hunk(
    "C-7b §8.3 second bullet closing sentence",
    """  `2e97162`]. **THAT FLOAT-AND-GOFMT COVERAGE IS NOT `I-3` AND IS NOT `I-4`; the SEPARATE seventh
  guard is what walks for those, and it DOES run.**""",
    """  `2e97162`]. **THAT FLOAT-AND-GOFMT COVERAGE IS NOT `I-3` AND IS NOT `I-4`; THE SEPARATE
  `guard_ledger_invariants` is what walks for those, and it DOES run**
  [ANCHOR .softhouse/conformance.sh :: `guard_ledger_invariants() {`; MEASURED by `T255` at
  `a71c140`].""",
)

hunk(
    "C-12 the FU-A2-25-2 stale harness comment — GONE at this commit, and said so",
    """  > **A stale harness comment survives outside this document and is raised, not fixed:**
  > `.softhouse/conformance.sh:1115-1116` still reads *"the I-3/I-4 SOURCE GUARD that DEC-2 §4.4
  > requires and §4.4.1 **records as not existing**"* [VERIFIED by `A2-28` at commit `2e97162`].
  > Harmless today, and it will mislead the next reader who follows it into DEC-2. It is `A2-25`'s
  > FU-A2-25-2 and it is **out of this task's scope** — `A2-28` touched no harness file.""",
    """  > **A stale harness comment survived outside this document and was raised, not fixed:**
  > `.softhouse/conformance.sh:1115-1116` read *"the I-3/I-4 SOURCE GUARD that DEC-2 §4.4 requires
  > and §4.4.1 **records as not existing**"* [VERIFIED by `A2-28` at commit `2e97162`; the line
  > numbers are preserved as A2-28 wrote them and are stale — this is a HISTORY quotation, which
  > revision 8's citation rule exempts]. It was `A2-25`'s FU-A2-25-2 and out of `A2-28`'s scope.
  > **⚠ REVISION 8: IT IS GONE.** `git grep -n -F 'records as not existing' -- .softhouse/conformance.sh`
  > returns **0 matches, exit 1** — a REAL measured negative, not an error read as an absence
  > (`P-80`) — at `a71c140`. Somebody removed it and nothing recorded that they had, which is the
  > mirror image of this document's own defect: **a follow-up that is discharged silently is as hard
  > to trust as a claim that goes stale silently.** `FU-A2-25-2` is CLOSED.""",
)

# ===========================================================================
# §10 — revision history
# ===========================================================================
hunk(
    "H-16 §10 revision history — entries for 6, the rejected 7, and 8",
    """## 10. Revision history

- **Revision 5 (this document)** — DRAFT, task `A2-32`, 22 August 2026, worktree at **`33d19a6`**.""",
    """## 10. Revision history

- **Revision 8 (this document)** — task `T255`, 22 August 2026, landed at **`a71c140`**, under gate
  **`G-14`**. **PREPARED AND LANDED IN ONE FIRE, which is the process half of the fix**: revision 7
  was prepared in one fire, `main` moved four merges under it, and its freshly re-measured citations
  were already stale at the commit where it would have landed — `G-14`'s own defect reproduced
  inside the fix for `G-14`.

  **What revision 8 changes: EVIDENCE, CITATIONS AND FALSE STATEMENTS OF FACT. NO OBLIGATION MOVES.**
  Not one normative `must`, not a contract sentinel, not a graded-domain predicate, not a §4.2
  predicate, not a §5.2 requirement, not a §5.3 precondition row, not `PIN-ledger.json`, not the
  vector store (`git rev-parse HEAD:.softhouse/vectors` =
  `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, unchanged). `T255`'s handoff carries a per-hunk
  no-obligation-moved proof that an independent reviewer can re-derive.

  **THE MECHANISM FIX, which is the part that matters more than any single hunk.** Revision 4
  recorded the remedy (`A2-25` FU-A2-25-3) and did not perform it. The document then shipped stale
  `.softhouse/conformance.sh` line citations in three consecutive passes — revisions 3–6 carried
  `:1152-1187`/`:1209`; revision 7 replaced them with `:1474`/`:1494`/`:1495` which an unrelated
  merge invalidated before it could land; and the review that caught that re-measured them to
  `:1504`/`:1524`/`:1525`, which were stale again by `a71c140`. **Revision 8 performs the remedy.**
  Citations into this repository are bound by **ANCHOR** (an exact, unique substring of the cited
  file, with a `git grep -n -F` recipe) and source-derived facts by **DERIVED** (§4.4.1's
  `DERIVED-FROM-SOURCE: run_guards()` block, re-derived and compared by
  `.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py`). The rule, and the argument
  for choosing elimination over a wired line-number checker, are at the head of this document under
  the freshness rule.

  **Sites corrected, by class.** *Banner:* headline, lead, facts 1–4, the §8-will-be-misread
  paragraph, the ratification paragraph. *Status block:* "DRAFT (revision 5) … NOT RATIFIED" while
  ratified at 6. *§0*, *§2.2*, *§4.2*. *§4.4:* the **lead paragraph** — the 35th site, nine lines
  above the bullet revision 7 corrected and left contradicting it — the TODAY bullet, the `I-1`,
  `I-2` and `I-7` cells, the `I-3` row's supporting citation (whose *"Graded today?"* answer is NO
  and stays NO, so no wording sweep over the answer column could ever reach it), and the rule
  paragraph. *§4.4.1:* the guard enumeration, which listed **seven** names and **omitted
  `guard_no_fail_open_instruments`** while reading as authoritative. *§4.9(b)*, *§5's heading*,
  *§5's baseline*, *§5.1's scope note*, *§5.2's heading and adoption paragraph*, *§5.3's note and
  count*, *§8.1*, *§8.2*, *§8.3*. Plus three live stale citations neither prior pass enumerated: the
  `go test` pair, the `-context` line, and `FU-A2-25-2`'s harness comment, **which is GONE** —
  measured, exit 1, a real negative.

  **The rule this revision adopts about sweeps, because both prior passes failed the same way:**
  *every hit a sweep prints gets an explicit disposition — corrected, HISTORY, or refused with a
  reason — and an undisposed hit is a defect.* Revision 7's own sweep printed §4.4's lead paragraph
  and §5.2's heading; neither reached its edit list.

  **What revision 8 does NOT claim.** It does not certify that any §5.3 precondition is adequately
  discharged (`FU-T247-3` stands). It does not convert every `path:NNNN` citation in this document:
  MEASURED at `a71c140` there are **115** such citations, of which **25** are Fineract-pinned and do
  not drift and **90** point into this repository; revision 8 converts the live
  `.softhouse/conformance.sh` citations and the `SchemaContexts()`/admission citations it rewrites,
  and the remainder — overwhelmingly bare `admit.go` / `vector.go` / `grade.go` basenames that are
  **ambiguous between two packages** as well as perishable — are enumerated in `T255`'s handoff as a
  follow-up. Both terms are counted; the residue is stated, not implied.

- **Revision 7** — task `T247`, **PREPARED AND REJECTED. IT WAS NEVER APPLIED TO THIS FILE.**
  Independent review `T251` returned MICRO-FIX/REJECT: the load-bearing check PASSED — **no
  obligation moved**, re-derived character by character on the rule paragraph and applied to all 17
  hunks, and the caution survived and was strengthened with both terms counted (14 declared
  capabilities, 6 graded, 8 declared out) — but its three re-measured `conformance.sh` line numbers
  were already stale at the commit it would have landed at, and it missed the §4.4 lead paragraph
  and §5.2's heading. **Revision 8 carries revision 7's substance forward in full**, which is why so
  much of the text above is marked *"CORRECTED IN REVISION 7"*: the wording is revision 7's and the
  evidence behind it has been re-measured at `a71c140`.

- **Revision 6** — task `T244`, reviewed by `T246`, landed under gate **`G-13`** at `8e8d65d`,
  22 August 2026. It corrected **§4.4's `I-5` row** (revisions 1–5 said *"The A2 corpus contains no
  reversal"*; it does — 8 rows carry `reversed = true`, re-derived live against the oracle by both
  `T244` and `T246`) and **§9 item 13**. **It landed with no §10 entry and no status-block update**,
  so this document identified itself as *"DRAFT (revision 5) … NOT RATIFIED"* while being a ratified
  revision 6. **This entry is written by revision 8 to close that gap.** A revision that does not
  stamp itself is a revision the next reader cannot date.

- **Revision 5** — DRAFT, task `A2-32`, 22 August 2026, worktree at **`33d19a6`**.""",
)

hunk(
    "H-16b §10 — the revision-5 entry no longer says 'this document'",
    """  **NOT RATIFIED; `A2-32` is NOT AUTHORISED to ratify it and does not, and says so in the status
  block, the banner and here.** Gate **G-11 stays OPEN — NOT RATIFIABLE** until a **further
  independent review passes clean AFTER revision 5**.""",
    """  **NOT RATIFIED WHEN DRAFTED; `A2-32` was NOT AUTHORISED to ratify it and did not, and said so in
  the status block, the banner and here.** Gate **G-11 stayed OPEN — NOT RATIFIABLE** until a
  **further independent review passed clean AFTER revision 5**. **`A2-33` performed it, returned
  APPROVED, and the driver ratified; `G-11` is CLOSED — RATIFIED** [recorded by revision 8; the
  registers are `.softhouse/gates.md` and `.softhouse/program.json`].""",
)


# ===========================================================================
# the two remaining LIVE conformance.sh line citations. Both were TRUE at
# a71c140 -- and that is exactly why they are converted: a citation that is
# correct today and perishable tomorrow is the class this revision exists to
# eliminate, not a class it gets to skip because it happens to be green.
# ===========================================================================
hunk(
    "C-13 NEXUS_DIR citation",
    """commit `2e97162`, re-opened rather than taken on the report: `conformance.sh:401` sets
`NEXUS_DIR="$REPO_ROOT/nexus"`;""",
    """commit `2e97162`, re-opened rather than taken on the report, and RE-MEASURED by `T255` at
`a71c140` where it still holds: the harness sets
[ANCHOR .softhouse/conformance.sh :: `NEXUS_DIR="$REPO_ROOT/nexus"`];""",
)

hunk(
    "C-14 CMD_PKG citation",
    """the real binary from `CMD_PKG` [`conformance.sh:411`], copy `.softhouse/vectors` to a temp store, add""",
    """the real binary from `CMD_PKG`
[ANCHOR .softhouse/conformance.sh :: `CMD_PKG="./internal/apps/loanschedule/conformance/cmd/conformance"`],
copy `.softhouse/vectors` to a temp store, add""",
)


def main():
    if not os.path.isfile(ADR):
        print("REFUSE (exit 2): %s not found" % ADR)
        return 2
    with open(ADR, encoding="utf-8") as fh:
        text = fh.read()
    before_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("DEC-2 before: sha256 %s, %d lines" % (before_sha, text.count("\n") + 1))
    print("")

    failed = 0
    for name, before, after in H:
        n = text.count(before)
        if n != 1:
            failed += 1
            print("  REFUSE  %-70s matched %d times (need exactly 1)" % (name[:70], n))
            continue
        text = text.replace(before, after, 1)
        print("  applied %s" % name)
    print("")
    if failed:
        print("NOT WRITTEN: %d of %d hunks did not match exactly once." % (failed, len(H)))
        return 1
    with open(ADR, "w", encoding="utf-8") as fh:
        fh.write(text)
    after_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("DEC-2 after:  sha256 %s, %d lines" % (after_sha, text.count("\n") + 1))
    print("APPLIED: %d of %d hunks." % (len(H), len(H)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
