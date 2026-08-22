# DEC-2 revision 7 — PREPARED, NOT LANDED

**Prepared by `T247` at commit `9b6c596c2b66769e7b7e7b5c2ca012b7f3df122a`.**
**`T247` did NOT edit `docs/adr/DEC-2-gl-accounting-adapter.md` and is not authorised to.** This file
is the proposed text and the edit list; landing it is the driver's act after an independent review,
by the route `G-13` took.

Ground for every figure: `.softhouse/capture/t247-dec2-rev7/EVIDENCE.md` (E-1 … E-9) and the full
harness transcript `bar-9b6c596.log`.

**SCOPE OF THIS REVISION, stated up front so a reviewer can grade it against a boundary:**
revision 7 changes **evidential statements only**. It changes **no obligation** — not one normative
`must`, not a sentinel, not a graded-domain rule, not a §5.3 precondition, not a §4.2 predicate, not
`PIN-ledger.json`. Two candidate obligation-shaped changes were identified and **deliberately
refused**; they are in `## B. What revision 7 must NOT do` and are raised as follow-ups instead.

---

## A. The site-by-site edit list

Line numbers **RE-MEASURED by `T247` at `9b6c596`** by direct enumeration of the file, not inherited
from `T246`, `gates.md` or the brief. **All seven line numbers `T246` reported (L3, L7, L10, L815,
L819, L825, L2437) and the eighth it reported at L87 are CONFIRMED unmoved at `9b6c596`** — `T246`'s
list is accurate as far as it goes. What it does **not** cover is the second half of this table.

Classification:
* **FALSE** — asserted as a currently-true measured fact, and false at `9b6c596`. Must be corrected.
* **STALE-STAMPED** — carries an older `[MEASURED at <sha>]` stamp and is wrong at `9b6c596`. Under
  the document's own freshness rule (L106-113) it is "a claim to re-run", not a lie — but revision 7
  is the re-measure moment, so it is corrected.
* **TRUE, RE-STAMP** — still true; only the stamp moves.
* **HISTORY — DO NOT TOUCH** — a record of what a past revision said. Correcting it would falsify
  the record; the document's own established practice is to restate and refute, never to reword.

### A.1 — sites `T246` named (all eight confirmed)

| # | line | classification | what it says now | disposition |
|---|---|---|---|---|
| 1 | **L3** | **FALSE** | `⚠ NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL.` | replaced by hunk **H-1** |
| 2 | **L7** | **FALSE** | *"Not one of them is currently checked by anything."* | **H-1** |
| 3 | **L10-11** | **FALSE** | fact 1, *"No `ledger` vector exists … [VERIFIED by this task: `ls .softhouse/vectors/`]"* | **H-1** |
| 4 | **L815** | **FALSE** | *"for **every row in this table the answer is NO**, because no `ledger` vector of any shape is currently expressible (§5)"* | **H-6** |
| 5 | **L819** | **FALSE** | I-1 column 5: *"**NO.** §5 — no admissible vector can carry a money cell, or any `ledger` cell."* | **H-7** |
| 6 | **L825** | **FALSE** | I-7 column 5: *"**N/A** — and note that today there is no `ledger` conformance PASS to say nothing with."* | **H-9** |
| 7 | **L2437** | **FALSE** | §8.3: *"**Today there is no such PASS to misread.**"* | **H-15** |
| 8 | **L87** | **FALSE** | *"until then `A2-15` (promote GL vectors) stays blocked"* — `A2-15` is `status: done` | **H-3** |

### A.2 — sites `T246` did NOT name. Nine more, found by concept sweep (P-26), not by wording

| # | line | classification | what it says now | disposition |
|---|---|---|---|---|
| 9 | **L12-17** | **FALSE as written** | banner fact 2: *"the store's only accepted schema is `gerege.loanschedule.vector/v1`"* and *"it is machinery that has not been built"* | **H-1**. **The store accepts TWO schemas** (E-4). §5.1's own narrower heading stays true — see #18. |
| 10 | **L37-42** | **STALE-STAMPED** | banner fact 3: *"`run_guards` invokes **seven** guards … the **seventh** is `guard_ledger_invariants`"*, `:1152-1187` / `:1189-1213` / `:1209` | **H-1**. At `9b6c596`: **eight invoked** (one short-circuiting + seven tallied), `guard_ledger_invariants` is the **sixth tallied**, at `:1494`; defined `:1300-1339`; `run_guards` `:1474-1500` (E-5). |
| 11 | **L54-62** | **TRUE, RE-STAMP** | banner fact 4: *"The 'PASS 46' everybody quotes is `loanschedule`'s"* | **H-1**. Still true and now **more** load-bearing: the ledger's counts are printed separately (4 / 2 / 21). |
| 12 | **L69-73** | **INCOMPLETE (LOW)** | *"`conformance.sh`'s hard guards do walk `nexus/internal/apps/ledger/`. They walk it **for floating-point literals and `gofmt`**."* | **H-1**. Omits the seventh guard that the banner's own fact 3, three paragraphs above, says runs — a self-inconsistency that predates G-14. |
| 13 | **L75-77** | **FALSE** | *"**What ratifying DEC-2 would and would not buy.** … It would buy **no grading whatsoever** until the machinery in §5.3 exists."* | **H-2**. DEC-2 **is** ratified (`G-11` CLOSED — RATIFIED, rev 5, `A2-33`) and the machinery exists. |
| 14 | **L247-253** | **FALSE** | §0: *"`.softhouse/vectors/` contains **exactly two context directories** … [VERIFIED: `ls .softhouse/vectors/`]"* and *"**not one parity vector grades it**"* | **H-4** |
| 15 | **L458-461** | **FALSE** | §2.2: *"§5 establishes that no vector asserting a money cell — or any other `ledger` cell — is currently expressible at all … they are not gradeable **today**"* | **H-5** |
| 16 | **L708-711** | **FALSE** | §4.2: *"Whether the *evaluation* is expressible is a separate question, **answered no in §5**."* | **H-5b** |
| 17 | **L820** | **FALSE** | I-2 column 5: *"**NO.** Same reason."* — inherits L819's dead reason | **H-8** |
| 18 | **L827-828** | **FALSE** | the rule paragraph: DEC-2 *"**obliges** I-1 through I-5 … and **grades none of them today.**"* | **H-10**. **This is the one to read most carefully — see B-1.** |

### A.3 — the same staleness further down. A document goes stale on a DATE, not in a paragraph (P-26)

| # | line | classification | what it says now | disposition |
|---|---|---|---|---|
| 19 | **L1304-1311** | **GROUND FALSE, CONCLUSION TRUE** | §4.9(b): *"THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN"*; *"Every row of the (b) table is therefore ungraded today"* | **H-11**. Exactly revision 6's shape (E-8): an oracle-faithful refusal IS expressible and IS graded, and the (b) rows are *still* all ungraded, for a different reason. |
| 20 | **L1449-1452** | **FALSE** | §5: *"`.softhouse/vectors/` holds **46 promoted parity vectors, all `loanschedule`** … **The `ledger` context has none.** … DEC-2 would be frozen against a corpus that does not yet exist in the store."* | **H-12**. The fenced transcript above it (L1435-1447) is a **stamped historical baseline** (`73c3ea7b…`) and is NOT touched. |
| 21 | **L1504** | **TRUE — KEEP** | §5.1 heading, *"No `ledger` vector is expressible **against the frozen vector schema**"* | **NO EDIT.** Correctly scoped to `gerege.loanschedule.vector/v1`; still true. **H-12b** adds one stamped sentence pointing at the second schema so a reader does not read the heading unscoped. |
| 22 | **L1626** | **TRUE — KEEP** | §5.1.1, *"**What is true.** §5.1's heading: no `ledger` vector is EXPRESSIBLE against the frozen vector schema"* | **NO EDIT**, same reason. |
| 23 | **L2021-2024** | **FALSE as fact / OBLIGATION as text** | §5.3 heading and *"`A2-15` **cannot promote** a `ledger` vector until **all** of the following exist"* | **H-13** adds a stamped note. **The ten preconditions themselves are NOT touched** — see B-2. |
| 24 | **L2044-2048** | **FALSE** | *"**Nine open, one landed.**"* | **H-13** |
| 25 | **L2345-2357** | **FALSE** | §8.1 heading *"NOTHING GRADES THE LEDGER"* + its measurement preamble | **H-14** |
| 26 | **L2359-2360** | **FALSE** | §8.1 fact 1, *"Zero `ledger` vectors exist."* | **H-14** |
| 27 | **L2361-2362** | **FALSE** | §8.1 fact 2, *"Zero `ledger` vectors are EXPRESSIBLE … Preconditions P-1…P-5 (§5.3) **do not exist**."* | **H-14** |
| 28 | **L2372-2399** | **STALE-STAMPED** | §8.1 fact 3, the guard citations again | **H-14** (same re-measure as #10) |
| 29 | **L2400-2405** | **TRUE, RE-STAMP** | §8.1 fact 4 | **H-14** |
| 30 | **L2407-2409** | **FALSE** | *"**Ratifying DEC-2 changes none of the four.** It writes down a boundary; **it grades nothing.**"* | **H-14** |
| 31 | **L2411-2416** | **FALSE** | §8.2: `ledger/` *"**stays unusable until the §5.3 machinery lands**, at which point `conformance.sh ledger` becomes a meaningful command"* | **H-15** |
| 32 | **L2421-2422** | **FALSE** | *"**Nine of the ten §5.3 preconditions remain** … and `A2-15` **cannot start** without them."* | **H-15** |
| 33 | **L2423-2425** | **FALSE** | *"**'PASS 46' remains the only thing anyone can say about the ledger**"* | **H-15** |
| 34 | **L2434-2437** | **FALSE** | §8.3, *"Today there is no such PASS to misread."* | **H-15** |

### A.4 — sites that are HISTORY. Enumerated so a reviewer can see they were considered and refused

`L19-36` (banner item 2's revision-3 retraction) · `L134` · `L1360-1368` · `L1612-1626` (§5.1.1's
retraction table) · `L1720` · `L1795` (already labelled *"for orientation only and expected to be
stale"*) · `L1852` · `L1928-1993` · `L2426-2430` · `L2614-2615` · `L2681-2682` · `L2841-2860` ·
`L2865` · `L2883-2995` · `L3017` · `L3034` (§10's per-revision entries).

**None is edited.** Each is a record of what a past revision said or why it was rejected. The
document's practice — set in revision 3 and reaffirmed in revisions 4, 5 and 6 — is to **restate and
refute, never silently reword**, precisely so that a later reader can tell "discharged, with limits"
from "never claimed". Revision 7 follows it.

### A.5 — LIVE restatements OUTSIDE `docs/adr/`. NOT T247's to edit. Reported, with follow-ups

`P-70`'s sharpest row is that DEC-2 §8.3's *"no guard for either exists"* survived **one file over**
in `conformance.sh`, invisible to every sweep because every sweep was scoped to the ADR. So this
sweep was scoped to **all 5,129 tracked files** (`sweep-repo-9b6c596.txt`; 12 binary skipped, 0
unreadable). Two live falsehoods outside the ADR:

| file:line | text | status |
|---|---|---|
| `.softhouse/program.json:720` | `"blocks": "Nothing today. No ledger vector exists yet (G-11), so no vector grades the column."` — G-12's `blocks` field | **FALSE at `T247`'s fork `9b6c596`. ALREADY CORRECTED at `main` `a0d5f66`**, merge `e36c3ca`, by the driver on **`T249`**'s finding, in the same fire. `T247` found it independently by a different route and reached the same verdict: ground false, conclusion true. **Follow-up WITHDRAWN.** |
| `.softhouse/gates.md:98` | *"**Nothing grades the ledger's money yet**: all 46 passing vectors are `loanschedule`'s and **zero** touch a GL account, a mapping, a financial activity or a journal entry."* — inside **G-11's own ratification block** | **FALSE, and STILL LIVE at `main` `a0d5f66`** (re-verified after the fire's merges). 21 ledger money cells graded every run; four vectors are journal entries. **Follow-up FU-T247-2.** |
| `.softhouse/gates.md:3561` | *"No `ledger` vector exists yet (G-11 is open), so no vector grades the column."* — G-12's raising record | **FALSE, and STILL LIVE at `main` `a0d5f66`.** The same sentence as the `program.json` field that WAS corrected, in the register the correction did not reach. **FU-T247-2.** |

`.softhouse/vectors/README.md`, `.softhouse/conformance.sh` and every `.go` file under `nexus/`
were in the swept population and produced **no** live restatement of any of the six concepts.

**What this sweep could NOT have found**, stated because a sweep with unstated limits reads as
exhaustive: a restatement phrased in none of the six concept forms; a claim carried as a **number**
rather than a sentence (e.g. a bare `0` in a table cell); a claim living in one of the 12 binary
files; a claim expressed as a **silence** where a qualification should be. The DEC-2 half of the
answer does not rest on the sweep — the ADR was settled by **enumeration**, reading every hit of nine
patterns across all 3,038 lines (`sweep-dec2-9b6c596.txt`), because a population of one file is small
enough to read and enumeration beats pattern-matching (`T246`'s method, adopted).

---

## B. What revision 7 must NOT do, and did not

### B-1. The rule paragraph at L827-828 — the obligation STAYS, only the fact moves

> **The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
> GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
> harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
> rather than a hope.

Two propositions are welded together here and they must be separated:

* *"DEC-2 **obliges** I-1 through I-5"* — **an OBLIGATION. UNTOUCHED.**
* *"**I-3 and I-4 must be enforced by a harness-level source guard, not by a vector**"* — **an
  OBLIGATION, and still exactly right. UNTOUCHED.** Nothing in the new corpus grades I-3 or I-4;
  the six vectors are snapshots and a snapshot cannot observe the absence of a write.
* *"and **grades none of them today**"* — **a FACT, and false.** I-1 and I-2 are graded, per vector,
  with `INDEPENDENT` / `DEPENDENT` distinguished. Only this clause moves.

### B-2. §5.3's ten preconditions — NOT ticked off, and here is why that is the honest call

It would be easy, and wrong, for revision 7 to rewrite §5.3 as *"P-1…P-10: all discharged"*. E-4
records where the second schema's package **names** each precondition and what the harness actually
**printed**, and that is real evidence — but it is **not an independent re-derivation that each
precondition is adequately discharged**. That would be a review of `A2-15`'s work, which nobody has
done, which is not T247's task, and which revision 7 has no business asserting inside a ratified
contract. Two specifics that would embarrass a ratifier who took a blanket tick at face value:

* **P-5 is named nowhere in the ledger package.** `git grep -P '\bP-5\b' -- nexus/internal/apps/ledger`
  returns nothing at `9b6c596`. Its *substance* is measurable (21 money cells, `int64` minor-unit
  strings paired with the oracle's own characters), but the marker every other precondition carries
  is absent.
* **P-9's obligation "transfers to the second schema"** by §5.3's own words, and
  `nexus/internal/apps/ledger/conformance/vector.go:63` claims the transfer is discharged. Whether
  the two `SchemaContexts()` allowlists are jointly airtight is a question about code, and revision 7
  did not open it.

So **H-13** states what is measured — that the preconditions were addressed and six vectors were
promoted and are green — and says in terms that revision 7 **does not certify** any individual
precondition, and files **FU-T247-3** for the re-derivation. **The preconditions' text, order,
identifiers and DEPENDS-ON column are untouched.**

### B-3. `PIN-ledger.json` stays at `dec2_revision: 5`

**Verified independently rather than inherited.** `nexus/internal/apps/ledger/conformance/admit.go:49-52`:

```go
if v.DEC2Revision != opts.Pin.DEC2Revision {
    add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)
}
```

The comparison is **vector-to-pin**. It never reads the ADR. So the ADR's revision number and the
pin are independent quantities, and the pin tracks *"what revision the vectors were captured
against"*, not *"what revision the document is on"*. Revision 7 changes **no obligation** (§B), so
no vector needs re-stamping. Bumping the pin alone makes all six ledger vectors INADMISSIBLE;
bumping pin and vectors together moves `git rev-parse HEAD:.softhouse/vectors`, which every BAR pins
(`P-61`). **`PIN-ledger.json` is not in revision 7's diff.**

### B-4. The CAUTION is not deleted. It is made true, and it is now stronger

See `## C. How the caution survives` at the end of this file.

---

## C. The hunks

Every replacement is given in full. `— BEFORE —` is the byte-exact current text at `9b6c596`;
`— AFTER —` is the proposed text.

---

### H-1 — the banner. Replaces lines **3-73**

#### — BEFORE — (L3-73, abbreviated at the retraction block that is CARRIED FORWARD UNCHANGED)

```
> # ⚠ NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL.
>
> **Read this before any other sentence in this document, and before quoting any number out of it.**
> Every claim below is a claim about what the reference oracle *does* and what a conforming port
> *must* do. **Not one of them is currently checked by anything.** Four separate facts, each
> measured by this task, not reasoned:
>
> 1. **No `ledger` vector exists.** `.softhouse/vectors/` holds `loanschedule/` and `_selftest/` and
>    nothing else [VERIFIED by this task: `ls .softhouse/vectors/`].
> 2. **No `ledger` vector is EXPRESSIBLE.** The store's only accepted schema is
>    `gerege.loanschedule.vector/v1`, ... **This is not a gap somebody forgot to fill; it is machinery
>    that has not been built.**
>
>    **⚠ RETRACTION, revision 3 — ...**   [L19-36, CARRIED FORWARD VERBATIM]
> 3. **A guard for `I-3` ... NOW EXISTS ...**   [L37-53]
> 4. **The "PASS 46" everybody quotes is `loanschedule`'s.** ...   [L54-67]
>
> **§8 contains a sentence that is true and will be misread** ...   [L69-73]
```

#### — AFTER —

```markdown
> # ⚠ THE LEDGER IS GRADED NOW — BY SIX VECTORS, OVER 6 OF ITS 14 DECLARED CAPABILITIES.
> # THAT IS NOT COVERAGE, AND A GREEN LEDGER SECTION IS NOT A CUTOVER ARGUMENT.
>
> **Read this before any other sentence in this document, and before quoting any number out of it.**
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
> **2026-08-22 16:37:56 +0800** — **2 h 13 m later** [MEASURED by `T247` at commit `9b6c596`,
> `git log -1 --format=%ci` on each commit; independently reproducing the figure `G-14` records].
> **Every sentence in the old banner was true when it was written.** The document had no mechanism
> that notices when the world moves underneath a claim it publishes as measured fact, and it placed
> the most perishable such claim exactly where every reader is told to begin. The freshness rule
> below makes staleness *visible*; it does not *prevent* it, and this is what that costs.
>
> **Four facts, RE-MEASURED by `T247` at commit `9b6c596` — taken, not inherited from the gate that
> commissioned this correction:**
>
> 1. **SIX `ledger` vectors exist, and all six PASS.** `.softhouse/vectors/` holds **three** context
>    directories — `_selftest/`, `ledger/`, `loanschedule/` — and `ledger/` holds
>    `LDG-01-manual-je-3leg-minor-units`, `LDG-02-repayment-split-4leg-minor-units`,
>    `LDG-03-overpayment-4leg-minor-units`, `LDG-04-header-account-accepted`,
>    `LDG-REFUSE-01-unbalanced-by-one-minor-unit` and
>    `LDG-REFUSE-02-manual-adjustments-not-permitted` [MEASURED by `T247` at `9b6c596`:
>    `ls .softhouse/vectors/` and `ls .softhouse/vectors/ledger/` — **the same command revisions 1–6
>    cited as proof of the opposite**]. On every run the harness prints, and pins:
>    **`ledger parity PASS 4 FAIL 0` · `ledger oracle-refusal PASS 2 FAIL 0` · `ledger inadmissible 0`
>    · `ledger harness errors 0` · `ledger cells compared 70 graded, of which 21 are MONEY cells in
>    int64 minor units` · `ledger invariants 0 violation(s), 11 non-vacuous assertion(s), 10
>    INDEPENDENT`** [MEASURED by `T247` at `9b6c596` from its own `VERDICT: PASS (exit 0)` run].
>    **`I-1` and `I-2` are among what those cells check**, per vector, with a hold that could only be
>    passed by construction reported as `DEPENDENT` rather than counted as evidence.
>
> 2. **A `ledger` vector IS expressible, because the machinery §5.2 named was BUILT — and §5.1's five
>    legs are untouched by that, which is the distinction this item now has to carry.** §5.1's claim
>    is, and remains, *"no `ledger` vector is expressible **against the frozen
>    `gerege.loanschedule.vector/v1` schema**"*, and that is **still true**: a `loanschedule`-schema
>    file dropped into `ledger/` is INADMISSIBLE by name [`admit.go:139-147`, `SchemaContexts()`].
>    What was false is this item's **unscoped restatement** — *"the store's only accepted schema is
>    `gerege.loanschedule.vector/v1`"* — and its conclusion, *"it is machinery that has not been
>    built"*. **The store accepts TWO schemas.** The second is **`gerege.ledger.vector/v1`**
>    [VERIFIED by `T247` at `9b6c596`: `nexus/internal/apps/ledger/conformance/vector.go:54`], with
>    its own `Request`/`Expect` shapes, its own class set (`parity`, `oracle-refusal`), its own
>    comparator and a cell whitelist derived from it, its own context allowlist, its own store pin
>    (`PIN-ledger.json`, keyed on `dec2_revision`) and its own capability registry
>    (`capabilities-ledger.json`, schema `gerege.ledger.capabilities/v1`). **The machinery was named
>    in §5.2 and built by `A2-15`.** §5.3's revision-7 note records what that does and does **not**
>    certify about the ten preconditions, and a ratifier should read it there rather than infer it
>    here.
>
>    **⚠ RETRACTION, revision 3 — this item said something stronger, and it was FALSE.** Revision 2
>    wrote here *"No `ledger` vector **CAN** exist"*, §8.1 wrote *"Zero `ledger` vectors **CAN**
>    exist"*, and §4.10 wrote *"no `ledger` vector can be admitted **at all**"*. **Admission**-impossibility
>    is strictly stronger than **expression**-impossibility, it is not what §5.1's five legs prove,
>    and it was falsified by measurement — **twice, independently**: by review task `A2-19`, and
>    again by the driver on `main`'s own bytes before revision 3 was commissioned. Copy any promoted
>    `loanschedule` parity vector into `.softhouse/vectors/ledger/`, change **only** `case_id` and
>    `context`, and the harness reported **`VERDICT: PASS (exit 0) — 44 parity vectors match the
>    pinned reference oracle, 5711 cells compared`**. Both reproductions agree to the digit: **44 /
>    5711**, against 43 / 5664 for the same store without the copy. **Those four figures are a
>    HISTORICAL RECORD, measured on the pre-`A2-20` harness over a 43-vector store
>    (`.softhouse/vectors` tree `ce821c63…`); they are NOT the corpus a ratifier is looking at, which
>    is 46 / 7884 — see §5's stamped baseline.** The headline number this entire
>    program quotes was inflatable by two string edits, over a corpus whose 44th vector graded a
>    **loan schedule** while filed as `ledger`. §5.1.1 carries the full retraction, the cause, and the
>    corrected positive control. **The hole has since been closed by `A2-20`** — but the sentence was
>    false when it was written, in the unsafe direction, and the reason it was believed is recorded
>    rather than quietly reworded.
>
> 3. **A source guard for `I-3` (balances are derived) and `I-4` (append-only) runs on every
>    invocation — and NO VECTOR GRADES EITHER INVARIANT.** `run_guards` invokes **eight** guards:
>    `guard_graded_root_is_this_tree` first, which **short-circuits** rather than joining the
>    `failed=1` tally, then **seven** tallied, of which `guard_ledger_invariants` is the **sixth**
>    [RE-MEASURED by `T247` at `9b6c596`: `.softhouse/conformance.sh:1300-1339` defines it,
>    `:1474-1500` is `run_guards`, `:1489-1495` are the seven tallied invocations and `:1494` is this
>    one. **Revisions 3–6 said *"seven guards … the seventh is `guard_ledger_invariants`"* with
>    `:1152-1187` / `:1189-1213` / `:1209`; those were stamped at `2e97162`, are correct there, and
>    are STALE here — `T243` wired an eighth guard, `guard_no_fail_open_instruments`, at `:1495`. An
>    ordinal used as an identifier goes wrong silently; a name does not.**] `T247`'s own run prints
>    `ledger-invariants: PASS` and `invariant violations 0`.
>    **This does NOT mean the ledger is covered, and the guard says so itself**: its PASS text reads
>    *"no violation is visible to a source-level guard over the Go tree"*, **not** *"the ledger tree
>    is covered"*; the detection surface is the **name**, so renaming a balance defeats it; and it
>    prints two `NIL-COVERAGE` lines because this Go tree declares **no database driver and contains
>    no SQL at all**, so **four of the guard's declared detection classes — `I3-SQL-BALANCE`,
>    `I4-BUILDER`, `I4-DML` and `OPAQUE-SQL` — inspected an EMPTY population** and are proven by the
>    guard's own self-test and by **nothing in this repository**. **`I4-BUILDER`'s emptiness is the
>    one the guard does NOT announce**, and it is MEASURED, both polarities, by `A2-32` — revision 4
>    said *"three"* here and recorded `I4-BUILDER` as `[UNVERIFIED]`. §4.4.1 carries the retraction,
>    the class names, the measurement and the limits. **And note what the six new vectors did NOT
>    change: `I-3` and `I-4` are graded by no vector, because a vector is a snapshot of oracle output
>    and a snapshot cannot observe the ABSENCE of a write.**
>
> 4. **The "PASS 46" everybody quotes is still `loanschedule`'s — and that matters MORE now, not
>    less.** All **46** promoted `loanschedule` parity vectors are in the `loanschedule/` directory,
>    and **zero of them touch a GL account, a mapping, a financial activity or a journal entry**
>    [RE-MEASURED by `T247` at `9b6c596`; store tree `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`].
>    **The `ledger` corpus is counted SEPARATELY and must be quoted separately**: the harness prints
>    it under its own heading, *"SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS"*, as **4 / 2 /
>    21**. A reader who cites `PASS 46` as evidence about the ledger is quoting the wrong number,
>    exactly as before; a reader who cites `4 / 2 / 21` as evidence that the ledger is covered is
>    making the new mistake this banner exists to prevent. **Revision 2 leaned on the
>    `loanschedule/` directory boundary as though it were ENFORCED. It was not** — that is what item
>    2's retraction is about, and it is why 43 became 44. **It is enforced now**, at admission, by an
>    allowlist tied to the schema rather than to the directory [VERIFIED by `A2-28`:
>    `nexus/internal/apps/loanschedule/conformance/vector.go:77-81`, `SchemaContexts()` returns
>    `{_selftest, loanschedule}`; `admit.go:139-147` refuses any other `context` as **INADMISSIBLE**;
>    the second schema's own `SchemaContexts()` returns `{ledger}`, `ledger/conformance/vector.go:71`].
>
>    **Every count in this document is a moving target and must be re-measured, never copied.** The
>    `loanschedule` figure was 43 when revision 3 was drafted and 46 by revision 4. The `ledger`
>    figure was **zero when revision 5 was drafted and six 2 h 13 m later**, which is the whole of
>    `G-14`. Any quotation of either carries the commit it was measured at, and a ratifier who finds
>    a bare number without one should treat it as stale until re-run.
>
> **§8 contains a sentence that is true and will be misread**, so it is contradicted here in
> advance: `conformance.sh`'s hard guards *do* walk `nexus/internal/apps/ledger/`. They walk it for
> **floating-point literals, `gofmt`, and — since `T208` — the source-level `I-3`/`I-4` walk of fact
> 3**. That last one is real and it is narrow; the first two are not `I-3` and are not `I-4` at all.
> A reader who takes "the guards cover the ledger tree" to mean the double-entry invariants are
> enforced has been misled by this document, and §8 now says so at the point of the claim.
```

---

### H-2 — the banner's closing paragraph. Replaces lines **75-77**

#### — BEFORE —

```
> **What ratifying DEC-2 would and would not buy.** It would buy a written boundary and an
> admissibility standard. It would buy **no grading whatsoever** until the machinery in §5.3
> exists. Ratification is not coverage, and this document must never be cited as though it were.
```

#### — AFTER —

```markdown
> **⚠ WHAT RATIFYING DEC-2 BOUGHT — past tense, because it HAS been ratified, and because revisions
> 1–6 wrote this sentence in the conditional and left it there.** `G-11` is **CLOSED — RATIFIED**
> (revision 5, reviewed by `A2-33`, ratified by the driver `chosen_by: agent`; Buyan retains veto)
> [TRANSCRIBED from `.softhouse/gates.md` § `G-11`, read by `T247` at `9b6c596`]. It bought a written
> boundary and an admissibility standard. Revisions 1–6 said it would buy **"no grading whatsoever
> until the machinery in §5.3 exists"** — **the machinery was then built and the grading exists**:
> 4 parity, 2 oracle-refusal, 21 money cells, every run.
>
> **THE CAUTION IS UNCHANGED AND IT IS NOW THE WHOLE POINT OF THIS BANNER. Ratification is not
> coverage, and neither is a green ledger section.** What is graded is **6 of the 14 capabilities
> `capabilities-ledger.json` declares**; **8 of 14 are declared OUT of the graded domain**, by name,
> and the harness prints all eight on every run, pass or fail, derived from that file so a gap
> cannot go unprinted [MEASURED by `T247` at `9b6c596`, both terms counted — `P-67`]. Ungraded, by
> name: **slot resolution** (the product→GL mapping chain, including payment-type precedence — the
> single largest thing this context does), **accrual entries**, **account transfers through
> `TRANSFERS_SUSPENSE` (gl 17)**, **charge-off**, **multi-currency entries**, **opening balances and
> `GLClosure`**, **reversals (`I-5`)**, and **running balances — on which `G-12` is OPEN, and on
> which `A2-29` measured the oracle's stored balance to be a SECOND SOURCE OF TRUTH rather than a
> cache, made to disagree with the derived sum by MNT 2,000,000.00 and surviving four
> organisation-wide recomputes**. Add to that: **no vector grades `I-3` or `I-4`** (fact 3), `I-6`
> is outside this contract's domain and `I-7` lands on `A1` and the HTTP layer, not here.
>
> **So: this document must never be cited as evidence that the GL/accounting context is correct, and
> a PASS on its six vectors must never be cited as a cutover argument. CUTOVER IS A HARD `user`
> GATE and nothing in this document or in the harness moves it.**
```

---

### H-3 — the status block. Replaces lines **80-88**

**`T246`'s F-5 OWNERSHIP test, applied clause by clause** — a proposition the ADR merely
**TRANSCRIBES** from a register it does not own is a transcription repair governed by that
register's gate; a proposition the ADR **OWNS** needs a gate however small:

| clause | owner | test result |
|---|---|---|
| *"DRAFT (**revision 5**), drafted by task `A2-32`"* | **the ADR** | **OWNED.** Needs a gate. `G-14` is that gate, and revision 7 is prepared under it. Called out here, never swept in. |
| *"**NOT RATIFIED**"*, *"`A2-32` is NOT AUTHORISED to ratify it and does not"* | **the ADR** for the second clause (a statement about its own author's authority); **`gates.md`/`program.json`** for the first | **MIXED.** The authorship clause is historical and true of `A2-32`; kept, in the past tense. The ratification state is transcribed. |
| *"Gate **G-11 remains OPEN — NOT RATIFIABLE** in `.softhouse/gates.md` and `.softhouse/program.json`"* | **`gates.md` / `program.json`** — the sentence **names the registers it copies from** | **TRANSCRIPTION.** Repair governed by G-11's gate, which is **CLOSED — RATIFIED**. Not an amendment. |
| *"until then **`A2-15` … stays blocked**"* | **`.softhouse/tasks.json`** | **TRANSCRIPTION.** `A2-15` is `status: done` [MEASURED by `T247` at `9b6c596`]. |
| *"and **§5.3 names work that must land** before `A2-15` could succeed even against a ratified contract"* | **the ADR** — §5.3 is its own section | **OWNED.** Corrected under `G-14`, and only its *factual* half; §5.3's preconditions are not touched (B-2). |
| *"Four revisions, four rejections"* and the `A2-31`/`A2-25`/`A2-19`/`A2-14` list | **the ADR** | **OWNED, and TRUE. Carried forward verbatim.** |
| **Line 90 onward** | **the ADR** | **SUBSTANTIVE. NOT TOUCHED.** `H-3b` *appends* a revision-7 paragraph after it; it rewrites nothing in it. |

#### — BEFORE — (L80-88)

```
**Status: DRAFT (revision 5), 22 August 2026, drafted by task `A2-32`. NOT RATIFIED. `A2-32` is NOT
AUTHORISED to ratify it and does not.** **Revision 4 (`A2-28`) was REJECTED** by independent review
(`A2-31`) on two findings, **both of them claims this document made about `main` that were false**;
**revision 3 (`A2-21`) was REJECTED** before it by `A2-25`; **revision 2 (`A2-16`) by `A2-19`**; and
**revision 1 (`A2-13`) by `A2-14`** (local fire `20260821-125942`). **Four revisions, four
rejections.** Gate **G-11 remains OPEN — NOT RATIFIABLE** in `.softhouse/gates.md` and
`.softhouse/program.json`. **Ratification requires a FURTHER independent review passing clean AFTER
revision 5** under standing policy **P-2**; until then `A2-15` (promote GL vectors) stays blocked,
and §5.3 names work that must land before `A2-15` could succeed even against a ratified contract.
```

#### — AFTER —

```markdown
**Status: RATIFIED, at revision 5, and now at REVISION 7. 22 August 2026.** Revision 7 is prepared by
task `T247` under gate **`G-14`** and landed by the driver after an independent review; `T247` is NOT
AUTHORISED to land its own revision and did not.

**`G-11` is CLOSED — RATIFIED.** Revision 5 (`A2-32`) was reviewed independently by `A2-33`, returned
APPROVED, and ratified by the driver `chosen_by: agent` under CLAUDE.md § *Answering gates*; **Buyan
retains veto and may reverse it** [TRANSCRIBED by `T247` at `9b6c596` from `.softhouse/gates.md`
§ `G-11` and `.softhouse/program.json` — the two registers this line copies from and does not own].
**Revision 6** then landed under gate `G-13` (prepared by `T244`, reviewed by `T246`, two corrections
applied before landing), correcting §4.4's `I-5` row and §9 item 13. **`A2-15` is `status: done`** and
has promoted six `ledger` vectors [TRANSCRIBED from `.softhouse/tasks.json`; the vectors MEASURED by
`T247` at `9b6c596`].

**Four revisions, four rejections, and they are why revisions 5–7 are trusted.** **Revision 4
(`A2-28`) was REJECTED** by independent review (`A2-31`) on two findings, **both of them claims this
document made about `main` that were false**; **revision 3 (`A2-21`) was REJECTED** before it by
`A2-25`; **revision 2 (`A2-16`) by `A2-19`**; and **revision 1 (`A2-13`) by `A2-14`** (local fire
`20260821-125942`). Revision 5 was ratified only after `A2-33` re-derived every load-bearing claim
rather than reading `A2-32`'s.

**⚠ A ratified DEC-n may not be amended by an agent without a gate**, and that has not changed.
Revisions 6 and 7 each ran the same route: **prepare, independent review, driver ratification, and
the preparing task lands nothing.** **CUTOVER, regulatory acceptance and parallel-run sign-off remain
hard `user` gates and nothing in this document moves them.**

**⚠ A PROCESS DEFECT, RECORDED BECAUSE IT IS PART OF WHY THIS BANNER STAYED FALSE.** Revision 6
landed real content changes (`L823`, §9 item 13) **without a §10 revision-history entry and without
updating this status block** — so between `8e8d65d` and revision 7 the document identified itself as
*"DRAFT (revision 5) … NOT RATIFIED"* while being a ratified revision 6 [MEASURED by `T247` at
`9b6c596`: `git grep -P '(?i)revision\s+6\b'` over this file returns exactly two lines, `823` and
`2568`, both being revision 6's own corrections; §10 begins at `L2611` and has no revision-6 entry.
Instrument calibrated on a positive — `revision 5` → 15 lines — and a negative — `revision 99` → 0].
**Revision 7 adds §10 entries for BOTH revision 6 and revision 7.** A revision that does not stamp
itself is a revision the next reader cannot date.
```

---

### H-3b — appended AFTER the existing L90-96 paragraph. Nothing in L90-96 is rewritten

```markdown
**Revision 7 changes EVIDENTIAL STATEMENTS ONLY, and it changes NO OBLIGATION.** Not one normative
`must`, not a contract sentinel, not a graded-domain predicate, not a §5.3 precondition, not
`PIN-ledger.json` — which stays at `dec2_revision: 5`, because `admit.go:49-52` compares vector to
pin and never reads this document, and nothing a vector asserts has changed. Its subject is a single
class of defect: **claims this document published as CURRENTLY-TRUE MEASURED FACT that had gone
false underneath it.** Every one was true when written. §10's revision-7 entry lists every site,
classified as FALSE, STALE-STAMPED, TRUE-RE-STAMPED, or HISTORY-AND-DELIBERATELY-UNTOUCHED, and
`T247`'s handoff carries the sweep, its calibration on both polarities, and — stated, not implied —
what the sweep could not have found.
```

---

### H-4 — §0's opening. Replaces lines **247-253**

#### — BEFORE —

```
`.softhouse/vectors/` contains exactly two context directories, `loanschedule/` and `_selftest/`
[VERIFIED: `ls .softhouse/vectors/`, by this task]. Task **A2-8** merged the port of the GL
account model, product-to-account mapping resolution and financial activity accounts to `main`,
and **not one parity vector grades it**. The conformance run reports `PASS 46`; all 46 are
`loanschedule`'s [MEASURED by `A2-28` at commit `2e97162`; the "not one grades the GL package" half
is VERIFIED BY A2-8, NOT RE-OPENED HERE — A2-8's own handoff says so plainly:
*"the harness does not grade this package at all"*].
```

#### — AFTER —

```markdown
**⚠ THIS SECTION RECORDS WHY THIS DOCUMENT WAS WRITTEN, AND THAT SITUATION HAS ENDED. Revision 7
re-measures it rather than deleting it, because the reason a contract exists is not made obsolete by
the contract working.**

**When DEC-2 was commissioned:** `.softhouse/vectors/` contained exactly two context directories,
`loanschedule/` and `_selftest/`. Task **A2-8** had merged the port of the GL account model,
product-to-account mapping resolution and financial activity accounts to `main`, and **not one
parity vector graded it** — `A2-8`'s own handoff said so plainly: *"the harness does not grade this
package at all"*. That is the gap this document was written to close.

**At `9b6c596` it holds THREE** — `_selftest/`, `ledger/`, `loanschedule/` — and `ledger/` holds six
`LDG-*` vectors, four `parity` and two `oracle-refusal`, all passing [MEASURED by `T247` at
`9b6c596`: `ls .softhouse/vectors/`]. The `loanschedule` conformance run still reports `PASS 46` and
all 46 are still `loanschedule`'s; the `ledger` corpus is reported separately as **4 / 2 / 21**.
**What has NOT changed is the part `A2-8` was pointing at:** the product→GL **slot resolver** — the
thing `A2-8` actually ported — is still graded by **no vector at all**; `capabilities-ledger.json`
carries `ledger.slot.resolution` with `in_graded_domain: false`, and the harness prints the reason on
every run. **Six vectors closed the journal-entry half of the gap and left the resolution half open.**
```

---

### H-5 — §2.2's closing. Replaces lines **458-461**

#### — BEFORE —

```
**What this does NOT rescue.** Being statable is not being graded. §5 establishes that no vector
asserting a money cell — or any other `ledger` cell — is currently expressible at all. `I-1` and
`I-2` are gradeable **from the data in hand and from nothing else that is missing except the
machinery**; they are not gradeable **today**. §4.4 now says that in those words.
```

#### — AFTER —

```markdown
**What this does NOT rescue — CORRECTED IN REVISION 7, and the correction is in the reader's
favour.** Revisions 1–6 wrote here that *"§5 establishes that no vector asserting a money cell — or
any other `ledger` cell — is currently expressible at all"*, and that `I-1` and `I-2` *"are not
gradeable today"*. **Both went false when the machinery §5.2 named was built.** `I-1` and `I-2` are
graded today, per vector, in `int64` minor units — **21 money cells across four parity vectors**
[MEASURED by `T247` at `9b6c596`]. **Being statable was not being graded; now it is both, for these
two invariants and for nothing else in §4.4's table.** `I-3` and `I-4` remain gradeable only by a
source-level guard, because a vector is a snapshot of oracle output and a snapshot cannot observe the
absence of a write; `I-5`'s never-mutates half is unreachable for the same reason (§4.4, revision 6);
`I-6` is out of the contract's domain and `I-7` is not this contract's obligation. §4.4 says all of
this at the point of each claim.
```

---

### H-5b — §4.2. Replaces line **711**

#### — BEFORE —

```
vacuous predicate is one nothing could fail; these two can be failed, by any vector carrying a money
cell, and the admission rule must evaluate them on exactly those vectors. Whether the *evaluation*
is expressible is a separate question, answered no in §5.
```

#### — AFTER —

```markdown
vacuous predicate is one nothing could fail; these two can be failed, by any vector carrying a money
cell, and the admission rule must evaluate them on exactly those vectors. Whether the *evaluation*
is expressible is a separate question — **revisions 1–6 answered it "no in §5", and it is now YES:
four promoted vectors carry money cells and `G-07`/`G-08` are evaluated on them** [MEASURED by
`T247` at `9b6c596`]. §5.1's narrower claim — that no such vector is expressible against the frozen
`gerege.loanschedule.vector/v1` schema — is unaffected and still stands (§5.1, §5.2).
```

---

### H-6 — §4.4's lead-in. Replaces lines **813-815**

#### — BEFORE —

```
- **TODAY** — can that separation be written down as an admissible vector and evaluated by the
grader? This is a question about the machinery, and for **every row in this table the answer is
NO**, because no `ledger` vector of any shape is currently expressible (§5).
```

#### — AFTER —

```markdown
- **TODAY** — can that separation be written down as an admissible vector and evaluated by the
grader? This is a question about the machinery. **Revisions 1–6 said the answer was NO for every row
in this table, "because no `ledger` vector of any shape is currently expressible (§5)". CORRECTED IN
REVISION 7: the machinery exists and the answer is now per-row.** `I-1` and `I-2` are **graded**;
`I-3`, `I-4`, `I-5`, `I-6` and `I-7` are **not**, each for a reason column 5 states at the point of
the claim, and none of those reasons is "the machinery is missing" any more [MEASURED by `T247` at
`9b6c596`; the harness prints an `INVARIANT … HOLD` line per vector, and marks a hold that no
implementation could fail as `DEPENDENT` rather than counting it].
```

---

### H-7 — the `I-1` row, column 5 only. Replaces the last cell of line **819**

Columns 1-4 of L819 are UNCHANGED — in particular the invariant statement, the `int64` minor-unit
comparison, and the `A2-235` re-derivation.

#### — BEFORE (final cell only) —

```
| **NO.** §5 — no admissible vector can carry a money cell, or any `ledger` cell. |
```

#### — AFTER (final cell only) —

```
| **YES, SINCE `A2-15` — AND REVISION 7 CORRECTS WHAT REVISIONS 1–6 SAID HERE, WHICH WAS *"NO. §5 — no admissible vector can carry a money cell, or any `ledger` cell."*** Four promoted `ledger` parity vectors each carry the assertion, and the harness reports it per vector as `INVARIANT double_entry_balances HOLD (2 assertion(s), INDEPENDENT)` — `LDG-01` debits `12500062` == credits `12500062` over 3 legs; `LDG-02` `30000000` over 4; `LDG-03` `100000000` over 4; `LDG-04` `10000025` over 2 — all in `int64` minor units [MEASURED by `T247` at `9b6c596` from its own `VERDICT: PASS (exit 0)` run; `LEDGER money cells compared = 21 == pinned 21`]. **What that does and does not buy:** it grades `I-1` **on the four shapes those vectors record**, all MNT, all from `ledger_rest_posting`/`ledger_db_readback`, and on nothing else — no accrual, no transfer, no reversal, no multi-currency, no closure. **A green `I-1` is evidence about four entries, not about the ledger.** |
```

---

### H-8 — the `I-2` row, column 5 only. Replaces the last cell of line **820**

#### — BEFORE (final cell only) —

```
| **NO.** Same reason. |
```

#### — AFTER (final cell only) —

```
| **YES, ON TWO OF THE FOUR — AND THE HARNESS REFUSES TO COUNT THE OTHER TWO, WHICH IS THE POINT.** Revisions 1–6 said *"NO. Same reason."*, inheriting `I-1`'s now-dead ground. **`LDG-02` and `LDG-03` grade it INDEPENDENTLY**: the whole comes from the **recorded REQUEST**, not from a leg — `30000000 == sum of 3 splits` and `100000000 == sum of 3 splits`, `int64` minor units. **`LDG-01` reports `DEPENDENT` and `LDG-04` reports `N/A`**, and the harness says why in its own words: on `LDG-01` *"the whole here IS one of the entry's own legs, so this equation is character-for-character the one `I-1` already asserted … and no implementation can fail one and pass the other"*; on `LDG-04` a 2-leg entry *"is not a split shape … declared not-applicable rather than reported as a hold that nothing could fail"* [MEASURED by `T247` at `9b6c596`]. **So the honest count is 2 independent assertions, not 4** — `P-35`, applied by the instrument to itself. **The defect this grades at all is real and was invisible before `A2-15`:** every journal entry in the A2 corpus had exactly two legs and every amount was a whole tugrik, so a port that dropped minor units was byte-indistinguishable from a correct one on every capture ever taken. |
```

---

### H-9 — the `I-7` row, column 5 only. Replaces the last cell of line **825**

The obligation text in column 4 — *"The obligation is real and lands on **A1** … and on the adapter's
HTTP layer"* — is **UNCHANGED**.

#### — BEFORE (final cell only) —

```
| **N/A** — and note that today there is no `ledger` conformance PASS to say nothing with. |
```

#### — AFTER (final cell only) —

```
| **N/A** — and, CORRECTED IN REVISION 7, **there IS now a `ledger` conformance PASS, and it still says nothing whatever about `I-7`.** Revisions 1–6 read *"today there is no `ledger` conformance PASS to say nothing with"*. There is: 4 parity / 2 oracle-refusal / 21 money cells, green [MEASURED by `T247` at `9b6c596`]. **The correction makes this row MORE important, not less** — the `Idempotency-Key` obligation is unmoved, no ledger vector tests it, and a green ledger section is now available to be misquoted as though it did. |
```

---

### H-10 — the rule paragraph. Replaces lines **827-830**

**Only the factual clause moves. Both obligations are carried forward verbatim (B-1).**

#### — BEFORE —

```
**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope.
```

#### — AFTER —

```markdown
**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context. **Revisions 1–6 added "and grades none of them today"; REVISION 7 CORRECTS
THAT CLAUSE AND ONLY THAT CLAUSE — it grades I-1 and I-2, on four vectors, and grades I-3, I-4 and
I-5 by nothing** [MEASURED by `T247` at `9b6c596`]. **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope — **unchanged by revision 7, and unchanged BY the six vectors**: a vector is a
snapshot of oracle output and cannot observe the absence of a write, so no growth of this corpus
will ever discharge them.
```

---

### H-11 — §4.9(b)'s block quote. Replaces lines **1304-1311**

**The conclusion is TRUE and is kept; only its ground moves (E-8). Same shape as revision 6.**

#### — BEFORE —

```
> **THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN.** The vector schema has exactly
> two expectation kinds, `schedule` and `refusal`, and `refusal` means one of the three **contract**
> sentinels above. There is no encoding for *"the oracle answered 404 with
> `error.msg.productToAccountMapping.not.found`"* — and filing it as a contract refusal would write
> this subsection's own named defect into the corpus. Establishing this is §5.1; a representation
> for it is precondition **P-2** in §5.3. **Every row of the (b) table is therefore ungraded today**,
> including the three `A2-224` / `A2-225` / `A2-092` message-for-message gradings, which exist as
> **Go tests** against committed bytes and not as vectors (§5).
```

#### — AFTER —

```markdown
> **⚠ REVISION 7 CORRECTS THE GROUND OF THIS BLOCK AND KEEPS ITS CONCLUSION. Revisions 1–6 said
> "THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN". It CAN, and it is.** An
> oracle-faithful refusal is now expressible and graded: the second schema carries
> `class: oracle-refusal` and an `expect.refusal` of **HTTP status + error code + message text**,
> explicitly not a contract sentinel, and two such vectors pass on every run —
> `LDG-REFUSE-01` (`403`, `error.msg.glJournalEntry.invalid.mismatch.debits.credits`, *"Sum of All
> Debits must equal the sum of all Credits for a Journal Entry"*) and `LDG-REFUSE-02` (`403`,
> `error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted`) [MEASURED by `T247`
> at `9b6c596`]. The harness labels them, in its own words, *"an HTTP status and error code the
> ORACLE returned and a capture recorded — NOT a contract sentinel"*. **Precondition `P-2` was the
> representation this block said was missing; it exists.**
>
> **The conclusion is UNCHANGED and still true: every row of the (b) table above is ungraded today
> — for a different and narrower reason.** Neither promoted refusal is a (b) row. The (b) rows are
> mapping-not-found, duplicate mapping rows, the slot type check, the financial-activity
> duplicate/invalid pairing, and the GL-account refusal family — **all of them reached through slot
> resolution, and `capabilities-ledger.json` carries `ledger.slot.resolution` with
> `in_graded_domain: false`, so a vector claiming one would be REFUSED rather than graded**
> [MEASURED by `T247` at `9b6c596`]. The three `A2-224` / `A2-225` / `A2-092` message-for-message
> gradings still exist as **Go tests** against committed bytes and not as vectors. **What blocks
> them now is a missing CAPTURE and a capability marked false, not a missing ENCODING** — and that
> distinction is the difference between "nobody has done it" and "it cannot be done", which this
> document has already been rejected once for collapsing (§5.1.1).
```

---

### H-12 — §5's baseline prose. Replaces lines **1449-1452**

**The fenced harness transcript above it (L1435-1447) is a stamped HISTORICAL baseline at store tree
`73c3ea7b…` and is NOT touched.** Neither is the `⚠ THIS BASELINE MOVED THREE TIMES INSIDE ONE FIRE`
note at L1454-1460, which is now more true, not less.

#### — BEFORE —

```
`.softhouse/vectors/` holds **46 promoted parity vectors, all `loanschedule`** [MEASURED above; the
store's only context directories are `loanschedule/` and `_selftest/`]. **The `ledger` context has
none.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to
the minor unit; **DEC-2 would be frozen against a corpus that does not yet exist in the store.**
```

#### — AFTER —

```markdown
**⚠ RE-MEASURED IN REVISION 7, AND THE THIRD MOVE OF THIS BASELINE IS THE ONE THE NOTE BELOW DID NOT
ANTICIPATE — IT WAS A NEW CONTEXT, NOT A BIGGER COUNT.** The transcript above is a stamped historical
baseline at store tree `73c3ea7b…` and is kept as such. **At `9b6c596`** the store holds **46
promoted `loanschedule` parity vectors** — still all `loanschedule`, still zero touching a GL
account — **and, separately, six `ledger` vectors: 4 `parity` + 2 `oracle-refusal`, 70 cells of which
21 are money**; store tree `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` [MEASURED by `T247` at
`9b6c596`, `git rev-parse HEAD:.softhouse/vectors`].

Revisions 1–6 said *"**The `ledger` context has none**"* and *"DEC-2 **would be frozen against a
corpus that does not yet exist in the store**"*. **Both were true when written and both are false at
this commit.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to the minor
unit; **DEC-2 was ratified at revision 5 against a corpus that did not then exist, and the corpus
arrived 2 h 13 m later.** That ordering is not a defect — a contract must precede the vectors it
admits — but it is exactly the mechanism that made this document's opening banner false, and §5.2's
requirements were written against a **freshly measured** baseline rather than a literal for precisely
this reason.
```

---

### H-12b — §5.1. ONE sentence appended after line **1504**'s heading paragraph. The heading itself is NOT changed

```markdown
**⚠ READ THE SCOPE OF THIS HEADING, revision 7.** *"Against the frozen vector schema"* means against
**`gerege.loanschedule.vector/v1`**, and within that scope every one of §5.1's five legs is still
true and was never falsified — a `loanschedule`-schema file placed in `ledger/` is INADMISSIBLE by
name. **What has changed is that a SECOND schema now exists**, `gerege.ledger.vector/v1`, and a
`ledger` vector is expressible and graded against **that** [MEASURED by `T247` at `9b6c596`:
`nexus/internal/apps/ledger/conformance/vector.go:54`]. §5.2 named exactly this extension and
adopted it; `A2-15` built it. **The banner's old item 2 restated this heading with the scope
dropped, and that unscoped restatement is what revision 7 retracts — not this section.**
```

---

### H-13 — §5.3. Replaces lines **2023-2024** and lines **2044-2048**. The TEN-ROW TABLE IS NOT TOUCHED

#### — BEFORE (L2023-2024) —

```
`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.
```

#### — AFTER —

```markdown
`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.

> **⚠ STATUS RE-MEASURED IN REVISION 7 — AND READ WHAT THIS NOTE DOES *NOT* SAY.**
> **`A2-15` is `status: done` and has promoted six `ledger` vectors, all green** [MEASURED by `T247`
> at `9b6c596`]. **The table below is UNCHANGED — no row, no identifier, no order, no DEPENDS-ON
> cell, and no `why` — because these are OBLIGATIONS and revision 7 changes no obligation.** What
> revision 7 corrects is the *factual* summary that used to follow the table, which said **"Nine
> open, one landed"**; that is false at this commit.
>
> **What IS measured:** the second schema's package addresses **P-1, P-2, P-3, P-4, P-6, P-7, P-9 and
> P-10 by name** — `vector.go:54` (`SchemaV1`), `:261` (`Request`), `:386` (`Refusal`), `:101`
> (`ClassOracleRefusal`), `:71` (`SchemaContexts`), `:460` (`DEC2Revision`); `grade.go:26`;
> `capability.go:15`; `impl.go:89-92`; `admit.go:27,125,309-318` — and the harness demonstrates the
> two that a declaration alone could not: `P-4`'s comparator graded **70 ledger cells**, and `P-10`'s
> registry discovered **6** deliberately-wrong ledger implementations from the binary's own
> `-list-implementations` and **killed all six through the harness, not by hand** [MEASURED by
> `T247` at `9b6c596`].
>
> **What is NOT measured, stated plainly rather than smoothed over:**
> **(i)** `P-5` is the one precondition the ledger package **names nowhere** —
> `git grep -P '\bP-5\b' -- nexus/internal/apps/ledger` returns nothing at `9b6c596`. Its substance
> is present and measurable (21 money cells, `int64` minor-unit strings paired with the oracle's own
> emitted characters as a transcription cross-check), but the marker every other precondition
> carries is absent.
> **(ii)** **REVISION 7 DOES NOT CERTIFY THAT ANY PRECONDITION IS *ADEQUATELY* DISCHARGED.** That is
> a review of `A2-15`'s work; nobody has done it, and asserting it inside a ratified contract on the
> strength of source comments would be a fresh unsupported inference of exactly the class that
> rejected this document three times. `FU-T247-3` files the re-derivation. **A ratifier must read
> this note as "the preconditions were addressed and the corpus is green", never as "P-1…P-10 are
> discharged".**
```

#### — BEFORE (L2044-2048) —

```
**Nine open, one landed.** P-6, P-1, P-7, P-2, P-3, P-4, P-5, P-9 and **P-10** remain; **P-8 is
done** and is kept in the table with its residue rather than deleted, so that a later reader can tell
"discharged, with limits" from "never required". **Revision 4 adds P-10 and renumbers nothing** — the
identifiers are referenced from six sections, the harness source and several handoffs, and the same
rule that protected P-1…P-9 in revision 3 protects them here.
```

#### — AFTER —

```markdown
**⚠ "Nine open, one landed" was revision 4's count and REVISION 7 RETRACTS IT AS A CURRENT FACT.**
It was true when written: at revision 4 only `P-8` had landed. At `9b6c596` `A2-15` is done, six
vectors are promoted and green, and all ten preconditions are addressed — with the two caveats the
note above states and does not soften. **Rows are kept, never deleted, so a later reader can tell
"discharged, with limits" from "never required"** — the rule `P-8` established, now applied to all
ten. **Revision 4 added P-10 and renumbered nothing**; the identifiers are referenced from six
sections, the harness source and several handoffs, and the same rule that protected P-1…P-9 in
revision 3 protects them here and in revision 7.
```

---

### H-14 — §8.1. Replaces lines **2345-2409**. Facts 3 and 4's retraction blocks are CARRIED FORWARD VERBATIM

#### — AFTER (heading, preamble, facts 1, 2 and the closing paragraph; facts 3 and 4 keep their existing retraction text with only the citations re-stamped per H-1 fact 3) —

```markdown
### 8.1 WHAT GRADES THE LEDGER, AND WHAT DOES NOT — say it here, not only in the banner

**⚠ THIS SECTION'S HEADING READ "NOTHING GRADES THE LEDGER" IN REVISIONS 1–6, AND IT WAS FALSE.**
It is repeated at the end of the document, as it always has been, because §8 is what a ratifier
reads last and because revision 1's §8 said something adjacent that a reader will merge with it.
**It went false in the same instant the banner did**, and it is corrected in the same revision — a
correction landing where a reviewer NAMED it and not where the document RESTATES it is the defect
class that has rejected this document three times (`P-21`, `P-26`).

**Four facts. RE-MEASURED by `T247` at commit `9b6c596`; each carries the stamp of the task that
took it.** Revision 3 introduced this list as *"Four facts, each measured by this task"* while fact 3
contained a figure nobody had ever measured (`A2-25` F-2; §4.4.1's `P-67` box) — **and revision 4
rewrote this heading to promise the fix while fact 3 still carried an unmeasured numerator**
(`A2-31` F-2) — **and revisions 5 and 6 left facts 1 and 2 asserting, under that same heading, a
world that had ceased to exist** (`T246` F-1; `G-14`). **A heading that asserts measurement is a
claim; it has now been wrong three times in this exact slot, and it is checked here.**

1. **SIX `ledger` vectors exist and all six PASS: 4 `parity`, 2 `oracle-refusal`, 21 money cells in
   `int64` minor units.** The store's context directories are `_selftest/`, `ledger/` and
   `loanschedule/` [MEASURED by `T247` at `9b6c596`].
   **⚠ RETRACTION, revision 7: revisions 1–6 wrote *"Zero `ledger` vectors exist. The store's only
   context directories are `loanschedule/` and `_selftest/`"* here, and the banner said the same and
   cited `ls .softhouse/vectors/` as its evidence.** `A2-15` promoted the six vectors **2 h 13 m**
   after revision 5 landed (`cab9e82` → `1325e8b`), and the claim then stood through revision 6,
   which corrected a different sentence in the same document. **It is restated rather than reworded
   because a silent downgrade would hide that this document told every reader, in its first
   instruction, to believe a fact its own cited command refutes.**

2. **A `ledger` vector IS expressible, against a SECOND schema — and §5.1's five legs are
   untouched.** `gerege.ledger.vector/v1` [`nexus/internal/apps/ledger/conformance/vector.go:54`],
   with its own request/expectation shapes, class set, comparator, cell whitelist, context
   allowlist, store pin and capability registry. §5.1's claim — *no `ledger` vector is expressible
   **against the frozen `gerege.loanschedule.vector/v1` schema*** — is **still true**, and the five
   legs that establish it were never falsified.
   **⚠ RETRACTION, revision 7: revisions 1–6 wrote *"Zero `ledger` vectors are EXPRESSIBLE … 
   Preconditions P-1…P-5 (§5.3) do not exist."*** The preconditions are addressed; §5.3's revision-7
   note records exactly what that is measured to mean and — expressly — what it does **not**
   certify.
   **⚠ RETRACTION, revision 3** *(carried forward verbatim: revision 2 wrote "Zero `ledger` vectors
   CAN exist" here, the banner and §4.10 said the same, and a relabelled `loanschedule` vector was
   admitted, graded and counted at `PASS 44 / 5711` — §5.1.1. It is restated rather than reworded
   because a silent downgrade would hide that a green `PASS 44` ever happened.)*

3. *(unchanged in substance; the guard's `conformance.sh` citations are re-stamped exactly as in the
   banner's fact 3 — `:1300-1339` / `:1474-1500` / `:1494`, **eight** guards invoked, **seven**
   tallied, `guard_ledger_invariants` the **sixth**. The revision-4 and revision-5 retractions about
   detection classes and the `I4-BUILDER` numerator are carried forward VERBATIM.)*
   **Revision 7 appends one sentence: NO VECTOR GRADES `I-3` OR `I-4`, and no growth of the ledger
   corpus ever will**, because a vector is a snapshot of oracle output and a snapshot cannot observe
   the absence of a write. The six new vectors changed nothing here.

4. *(unchanged in substance; re-stamped.)* **The 46 passing `loanschedule` parity vectors are still
   `loanschedule`'s and none touches a GL account, a mapping, a financial activity or a journal
   entry** [RE-MEASURED by `T247` at `9b6c596`]. **The `ledger` corpus is counted separately — the
   harness heads it "SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS" — and quoting either number
   for the other context is the error this fact exists to prevent.**

**⚠ THE CLOSING SENTENCE OF THIS SECTION IS REPLACED. Revisions 1–6 read: *"Ratifying DEC-2 changes
none of the four. It writes down a boundary; it grades nothing."*** DEC-2 **was** ratified, the
machinery it named **was** built, and it **does** grade — narrowly. **What survives, and is now the
load-bearing sentence of this document:** **grading 6 of 14 declared capabilities is not coverage.**
Eight capabilities are declared OUT of the graded domain by name — slot resolution, accrual,
transfers suspense, charge-off, multi-currency, opening balances and `GLClosure`, reversals, running
balances — `I-3` and `I-4` are graded by no vector, `G-12` is OPEN on the running-balance columns,
and **a citation of this document, or of a green ledger section, as evidence of ledger coverage is a
misreading of both.** Cutover remains a hard `user` gate.
```

---

### H-15 — §8.2 and §8.3. Replaces lines **2411-2437**

#### — AFTER —

```markdown
### 8.2 Now that it is ratified

- **`.softhouse/vectors/ledger/` IS a legal context directory, for the second schema and only for
  it** — a `gerege.loanschedule.vector/v1` file placed there is INADMISSIBLE, by name, since `A2-20`
  [`admit.go:139-147`], and the second schema's own `SchemaContexts()` returns `{ledger}`
  [`ledger/conformance/vector.go:71`]. **⚠ Revisions 1–6 said it *"stays unusable until the §5.3
  machinery lands, at which point `conformance.sh ledger` becomes a meaningful command"*. The
  machinery landed and the command is meaningful**: it grades 4 parity and 2 oracle-refusal vectors
  over 70 cells, 21 of them money [MEASURED by `T247` at `9b6c596`].
- **`A2-15` had an admissibility standard and used it**: §4.2's predicates, §4.6's A-1…A-4, §4.10's
  registry, §5.5's `graded_against` requirement, and **§5.2's requirements 1–7** — the last two of
  which are a positive control (**6a** on the same bytes, **6b** on the admission layer's own bytes)
  and a required RED demonstration, without which an extension that does nothing would satisfy the
  specification. **That RED demonstration is now executed rather than declared: 6 deliberately-wrong
  ledger implementations, discovered from the binary's own `-list-implementations`, all 6 killed
  through the harness** [MEASURED by `T247` at `9b6c596`]. **⚠ Revisions 1–6 closed this bullet with
  *"Nine of the ten §5.3 preconditions remain … and `A2-15` cannot start without them"*; `A2-15` is
  `done`. Read §5.3's revision-7 note for what that is measured to mean and what it does not
  certify.**
- The GL/accounting context has a boundary a regulator can be shown, **and now a small number a
  regulator can be shown too**. **⚠ Revisions 1–6 said *"'PASS 46' remains the only thing anyone can
  say about the ledger, and what it says is 'this is about a different context'"*. That is no longer
  the only thing — but the sentence's WARNING is intact and the new numbers need it more.** `PASS 46`
  is still about a different context. The ledger's own numbers are **4 / 2 / 21**, and they are about
  **six entries**.
  **⚠ Revision 3 records what the old sentence cost in revision 2**: it was written as a structural
  guarantee and it was not one. The `ledger` context *could* contribute to the parity count, and did,
  at `PASS 44` (§5.1.1). It is true today **because `A2-20` made it true in code**, not because the
  schema made it true by construction — and the distinction is the difference between a guarantee and
  a convention that happened to hold.

### 8.3 These remain true and must not be misread

- **A `ledger` conformance PASS means "matches the reference oracle on captured vectors, inside the
  graded domain".** It does not mean the ledger is correct, and it means nothing at all about
  savings, shares, working-capital loans, charges, reversals, holds, or nineteen of the twenty-three
  cash placeholder slots. **⚠ Revisions 1–6 closed this bullet with *"Today there is no such PASS to
  misread."* THERE IS ONE NOW, and this bullet is therefore no longer hypothetical — it is the
  operative instruction for reading the harness output.** The graded domain is **6 of the 14
  capabilities `capabilities-ledger.json` declares**, both terms counted [MEASURED by `T247` at
  `9b6c596`]; the harness prints all **8** ungraded ones on every run, pass or fail, derived from
  that file rather than hand-written, so a gap cannot go unprinted.
- *(the `conformance.sh` hard-guards bullet at L2438-2450 is UNCHANGED except that its
  `guard_ledger_invariants` citations are re-stamped as in H-1 fact 3.)*
```

---

## D. Where the ratifier should start, if they read only one thing

**Re-run the command the old banner cited.** `ls .softhouse/vectors/`. If it lists `ledger/`, the old
banner was false and revision 7 is the correction. If it does not, revision 7 is itself stale and
must be re-run before it is landed — which is the rule the document already carries at L106-113 and
which `G-14` exists because nobody applied.
