# T251 — INDEPENDENT REVIEW of DEC-2 revision 7 (prepared by `T247`)

**Reviewer fork point, MEASURED not assumed (P-71):** `git rev-parse HEAD` →
**`a6bec723fd0769d5c5b6349a375756d1104a7c73`**, branch `softhouse/T251-dec2-rev7-review`,
worktree `/home/user/wt/T251`. `T247` prepared revision 7 at `9b6c596c2b66769e7b7e7b5c2ca012b7f3df122a`.
Every figure below is measured by `T251` at `a6bec72` unless it names another commit.

**Vector-store digest, READ LIVE:** `git rev-parse HEAD:.softhouse/vectors` →
**`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`** — matches the value the brief and `T247` carry.
**UNMOVED by this task** (re-read at exit, same value; `git status --porcelain` clean of any
`.softhouse/vectors/` path).

**Environment fact accounted for:** the reference oracle (Fineract) is UNREACHABLE from this host,
and separately the harness cannot produce a verdict on Linux at all (`T253`). **This review asserts
NO conformance result and re-uses none.** Everything below is a document read, a source read, or a
JSON read — all fully available. Where a claim under review depends on a harness run, it is marked
`[HARNESS-DEPENDENT — NOT RE-RUN HERE]`.

---

# VERDICT: **MICRO-FIX**

**The load-bearing answer first, unambiguously: NO OBLIGATION MOVED.** Re-derived character by
character at `a6bec72` (check 3 below). Revision 7 is an evidential correction, as `G-14` requires.

**But it must NOT be landed as drafted.** Four corrections are required first. One of them (F-1) is
a re-enactment of the exact defect `G-14` exists to punish: revision 7's freshly "RE-MEASURED"
`conformance.sh` citations **are already stale at the commit the driver would land them at**.
Two more (F-2, F-3) are **sites the 34-row edit list never enumerated**, both carrying the same
banner fact — including one in the very table revision 7 edits three other rows of.

---

## Check 1 — RE-MEASURE every line number at MY fork commit

Ran `T247`'s `verify-line-numbers.py` at `a6bec72`. It asserts **46 rows** (42 ADR + 4
`conformance.sh`) plus a negative control.

**Result: 43 hold, 3 MOVED — and the verifier itself reports the failure.**

```
=== DEC-2 ADR  (docs/adr/DEC-2-gl-accounting-adapter.md, 3039 lines) ===
  ... 42 rows, ALL ok ...
=== conformance.sh  (.softhouse/conformance.sh, 2574 lines) ===
  ok     L1300  guard_ledger_invariants() {
  MOVED  L1474  expected 'run_guards() {'
         got      '  LC_ALL=C sort "$got.raw" >"$got"'
  MOVED  L1494  expected 'guard_ledger_invariants             || failed=1'
         got      '    warn "conformance: The pin is FAILOPEN_PIN_FILE_LIST in .softhouse/conformance.sh."'
  MOVED  L1495  expected 'guard_no_fail_open_instruments      || failed=1'
         got      '    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."'

STALE — RE-MEASURE BEFORE APPLYING: 3 row(s) MOVED out of 46 checked   (exit 1)
```

- **All 42 ADR line assertions HOLD at `a6bec72`**, including `T246`'s eight (L3, L7, L10, L87,
  L815, L819, L825, L2437) and the three must-be-unchanged controls (L80, L90, L827). The four
  merges `main` took under `T247` did **not** move the ADR.
- **Three of the four `conformance.sh` assertions FAILED.** See F-1.

### The verifier is NOT self-certifying — its negative arm was made to fail, and it did

`P-22`/`P-35` demand this. I copied the script to scratch, changed the negative control's needle from
`ZZQQ-T247-THIS-MUST-NOT-MATCH` to `DEC-2` (which **is** on ADR line 1), and re-ran:

```
=== NEGATIVE CONTROL (expect 1 MOVED) ===
  ok     L1     DEC-2
CALIBRATION FAIL: the negative control did not fail. Results are void.   (exit 2)
```

**It aborts and prints no `ok` rows at all when its negative arm passes.** The arm discriminates,
and the 42 ADR `ok`s are therefore worth something. The `conformance.sh` arm has no negative control
of its own — but it produced three genuine failures this run, which is the strongest possible
evidence that it discriminates.

---

## Check 2 — hunt for a 35th site. **FOUND: three, and one is a family.**

Method: enumeration, not sweeping (`P-75`). I enumerated (a) every line of the ADR against 17
concept patterns, subtracted the 34 edit-list ranges and the 16 declared-HISTORY ranges, and read
all 133 survivors; (b) every carrier of the guard citation strings `1152-1187`, `1189-1213`,
`:1209`, `invokes SEVEN`, `the seventh`, `all seven`.

**The (b) enumeration is decisive.** `T247`'s own `EVIDENCE.md` E-5 states the citation is carried by
*"The banner (fact 3, `L37-42`) and **four other sites**"* — **five carriers**. Its 34-row edit list
disposes of **two** of them. Enumerated at `a6bec72`:

| # | site | in the 34-row edit list? | in the declared HISTORY list? |
|---|---|---|---|
| 1 | **L37-42** banner fact 3 | YES (#10 → H-1) | — |
| 2 | **L821** §4.4 table, `I-3` row, column 5 | **NO** | **NO** |
| 3 | **L847-874** §4.4.1 | **NO** | **NO** |
| 4 | **L2375-2376** §8.1 fact 3 | YES (#28 → H-14) | — |
| 5 | **L2920** §10 revision-3 entry | — | YES (2883-2995) — correctly untouched |

Sites 2 and 3 are the misses. Both are **exactly the failure mode the brief names**: they restate a
banner fact without restating the banner's words. See F-2 and F-3.

A third, unrelated miss — **L1426, the §5 section heading** — is at F-5.

---

## Check 3 — **DID ANY OBLIGATION MOVE? NO.**

`H-10` replaces L827-830. First, the `— BEFORE —` block is **byte-identical** to the file at
`a6bec72` (verified by exact string equality on the joined lines, not by eye). Then a word-level
`difflib` opcode run, BEFORE → AFTER:

```
KEPT      : **The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the GL/accounting
REPLACED  : 'context, and **grades'  ->  'context. **Revisions 1–6 added "and grades'
KEPT      : none of them
REPLACED  : 'today.**'  ->  'today"; REVISION 7 CORRECTS THAT CLAUSE AND ONLY THAT CLAUSE — it grades I-1 and
                            I-2, on four vectors, and grades I-3, I-4 and I-5 by nothing** [MEASURED …].'
KEPT      : **I-3 and I-4 must be enforced by a harness-level source guard, not by a vector**, and DEC-2 states
            that as a normative requirement rather than a hope
REPLACED  : 'hope.'  ->  'hope — **unchanged by revision 7, and unchanged BY the six vectors**: a vector is a
                          snapshot of oracle output and cannot observe the absence of a write, so no growth of
                          this corpus will ever discharge them.'
```

**The two welded obligations survive word for word:**

1. *"DEC-2 **obliges** I-1 through I-5 on any implementation of the GL/accounting context"* — kept
   verbatim; the only change to it is the trailing `,` becoming `.` where the fact clause was cut off.
2. *"**I-3 and I-4 must be enforced by a harness-level source guard, not by a vector**, and DEC-2
   states that as a normative requirement rather than a hope"* — kept **verbatim, unbroken**.

**The only proposition removed is the FACT** *"and **grades none of them today.**"* — which is false
at `a6bec72`. `T247`'s B-1 separation is correct and its execution is exact.

### The same test applied to every other hunk

I read all 17 hunks and classified every replaced clause. **No hunk removes, weakens, narrows or
adds a normative `must`/`shall`/`may not`, a contract sentinel, a graded-domain predicate, a §5.3
precondition, a §4.2 predicate, an §4.6 A-n rule, a §4.10 registry rule, or a refusal condition.**
Specifically:

- **H-13** — §5.3's **ten-row precondition table is not in the hunk at all**; both replaced ranges
  (L2023-2024 lead-in, L2044-2048 count paragraph) are prose. Confirmed by reading the hunk's own
  BEFORE blocks against the file: neither contains a table row, an identifier, or a DEPENDS-ON cell.
- **H-9** — the `I-7` obligation text lives in **column 4**; the hunk replaces **column 5 only**. The
  `Idempotency-Key` obligation is untouched, and the AFTER text says so explicitly.
- **H-7 / H-8** — columns 1-4 untouched; column 5 is the *"Graded today?"* answer, which is a fact.
- **H-11** — replaces §4.9(b)'s **ground** and keeps its **conclusion** ("every row of the (b) table
  is ungraded today"), which I independently confirm is still true: none of the two promoted
  refusals is a (b) row, and `ledger.slot.resolution` carries `in_graded_domain: false` (measured).
- **H-6 / H-5 / H-5b / H-4 / H-12 / H-14 / H-15** — all replace present-tense factual assertions
  about the store, the schema and the harness. No obligation text appears in any BEFORE block.
- **H-2 / H-3 / H-3b** — status and caution; see checks 4 and 7.

**ANSWER: NO. No normative clause, field, rounding rule, graded-cell definition or refusal condition
moved.** This part of revision 7 is clean and I would not reject on it.

---

## Check 4 — does the CAUTION survive, and does its ratio have BOTH terms measured? **YES to both.**

`P-67` applied by me, independently, on the file rather than on `T247`'s table.
`.softhouse/vectors/capabilities-ledger.json` at `a6bec72`, parsed with `python3 json`:

```
rows carrying in_graded_domain : 14
TRUE  = 6     FALSE = 8     OMITTING THE FIELD = 0
```

| in graded domain | capability |
|---|---|
| YES | `ledger.money.minor.unit.conversion`, `ledger.journal.entry.readback`, `ledger.accounting.path.loan.repayment`, `ledger.manual.entry.posting`, `ledger.header.account.posting`, `ledger.refusal.parity` |
| NO | `ledger.slot.resolution`, `ledger.accrual.entry`, `ledger.transfers.suspense`, `ledger.charge.off`, `ledger.multi.currency.entry`, `ledger.opening.balance.and.closure`, `ledger.reversal.entry`, `ledger.running.balance` |

**Both terms measured. 6 of 14. 8 declared out.** The eight names `H-2` lists — slot resolution,
accrual, transfers suspense, charge-off, multi-currency, opening balances and `GLClosure`, reversals,
running balances — are **the eight `false` rows, exactly, with nothing added and nothing dropped.**
This is not revision 6's F-2 shape: neither term is inferred.

**The caution is not deleted and not softened. It is strengthened in four places:**

- `H-2` keeps *"Ratification is not coverage"* **verbatim** and extends it: *"and neither is a green
  ledger section"*, then adds a sentence that did not exist before — *"a PASS on its six vectors must
  never be cited as a cutover argument. CUTOVER IS A HARD `user` GATE."*
- `H-1` fact 4 adds the new failure mode by name: *"a reader who cites `4 / 2 / 21` as evidence that
  the ledger is covered is making the new mistake this banner exists to prevent."*
- `H-14`'s closing makes *"grading 6 of 14 declared capabilities is not coverage"* the load-bearing
  sentence and re-lists the eight.
- `H-9` argues the `I-7` row becomes **more** important, not less.

The new banner headline is a warning, not a green light: *"THAT IS NOT COVERAGE, AND A GREEN LEDGER
SECTION IS NOT A CUTOVER ARGUMENT."* **No rejection on check 4.**

---

## Check 5 — the two newly-found banner falsehoods, and the ORDINAL

### L76 — *"would buy no grading whatsoever"*

Confirmed present and false at `a6bec72`: L75-77 read *"**What ratifying DEC-2 would and would not
buy.** … It would buy **no grading whatsoever** until the machinery in §5.3 exists."* DEC-2 **is**
ratified (`G-11` CLOSED — RATIFIED, per `.softhouse/gates.md`) and the machinery exists. `H-2`
corrects it and keeps the caution. **Correct catch, correct fix.**

### Fact 3's ordinal — I counted the guards in `run_guards` myself, from source

Enumerated `run_guards()` in `.softhouse/conformance.sh` at `a6bec72`, printed line by line:

```
1504 run_guards() {
1505   local failed=0
…
1514   guard_graded_root_is_this_tree || {        ← SHORT-CIRCUITS: warns and `exit "$EXIT_UNUSABLE"`
1519   guard_no_float_in_vectors           || failed=1
1520   guard_no_float_in_harness           || failed=1
1521   guard_gofmt                         || failed=1
1522   guard_no_float_in_capture_requests  || failed=1
1523   guard_no_narrow_catch_in_capture_rigs || failed=1
1524   guard_ledger_invariants             || failed=1
1525   guard_no_fail_open_instruments      || failed=1
1530 }
```

**MEASURED: `run_guards` invokes EIGHT guards. One short-circuits; SEVEN are tallied.
`guard_ledger_invariants` is the SIXTH tallied — and the SEVENTH invoked overall.**
Nine `guard_*()` definitions exist in the file (L676, 759, 827, 1084, 1145, 1215, 1300, 1430) — eight,
plus `run_guards` itself at 1504. `T247`'s **counts are correct.**

**But the ordinal finding is over-stated, and revision 7 rebuilds the defect. Two separate problems:**

**(a) On the document's own counting basis, the old ordinal was NEVER WRONG.** L38-41 reads
*"`run_guards` invokes **seven** guards, not five; the seventh is `guard_ledger_invariants` … `:1189-1213`
is `run_guards` **invoking all seven**"*, and §4.4.1's fenced list at L854-861 enumerates the seven
**starting with `guard_graded_root_is_this_tree`**. The basis is **all invocations**, short-circuiting
one included. On that basis, at `a6bec72`, `guard_ledger_invariants` **is still the seventh invoked**.
What went false is the **count** ("seven" → eight), not the ordinal. `T247`'s E-5 reports
*"'the seventh' → the sixth of the seven tallied"* and `H-1` concludes *"An ordinal used as an
identifier goes wrong silently"* — that conclusion is reached by **silently switching the counting
basis** from all-invoked to tallied-only. The premise is not established.

**(b) Revision 7 replaces one ordinal with another ordinal — the brief's exact trap.** `H-1` fact 3
lands *"of which `guard_ledger_invariants` is the **sixth**"*, and `H-14` fact 3 repeats
*"**seven** tallied, `guard_ledger_invariants` the **sixth**"*. That is a fresh perishable positional
claim in the banner a reader is told to read first, published **in the same sentence that warns
against exactly this**. It will go stale the first time a guard is wired ahead of it — and its
companion line numbers already went stale in under one fire (F-1). The name is present and carries
the whole identifying load; the ordinal adds nothing and is pure future staleness. **See correction
C-4.**

---

## Check 6 — `PIN-ledger.json` and the store digest

- **`.softhouse/vectors/PIN-ledger.json` reads `"dec2_revision": 5`** at `a6bec72`. **Revision 7 does
  not bump it** — no hunk touches it, and `B-3` states so explicitly. **CORRECT.**
- All six `LDG-*.json` vectors declare `dec2_revision: 5`, schema `gerege.ledger.vector/v1`,
  context `ledger` (parsed, all six).
- `nexus/internal/apps/ledger/conformance/admit.go:49-52` verified verbatim at `a6bec72`:
  ```go
  if opts.Pin != nil {
      if v.DEC2Revision != opts.Pin.DEC2Revision {
          add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)
  ```
  The comparison is **vector-to-pin**. Line numbers 49-52 are exact.
- **Decoupling verified independently, not inherited:** `git grep -P 'DEC-2-gl-accounting-adapter'
  -- nexus/ .softhouse/conformance.sh` returns **nothing**. No code or harness path reads the ADR, so
  the ADR revision number and the pin are genuinely independent quantities. `P-66`/`P-70`: I looked
  in the Go module tree and in `conformance.sh`; I did not search `.softhouse/bin/`.
- `.softhouse/vectors/capabilities-ledger.json` also carries `dec2_revision: 5`; `capability.go:111`
  only checks it is **positive**, never equal to the pin — so there is no second coupling a rev-7
  bump could trip. Untouched by revision 7 either way.
- **Digest: `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, read live at entry and again at exit of this
  review. UNMOVED.** No hunk writes under `.softhouse/vectors/`.

**No rejection on check 6.**

---

## Check 7 — the status block, under `T246`'s F-5 OWNERSHIP test

Confirmed at `a6bec72` that L80-88 reads *"Status: DRAFT (revision 5) … NOT RATIFIED … Gate G-11
remains OPEN — NOT RATIFIABLE"* while `G-11` is CLOSED — RATIFIED and revision 6 has landed
(`T247`'s E-7 reproduced: `git grep -P '(?i)revision\s+6\b'` over the ADR returns exactly **L823**
and **L2568**, both being revision 6's own corrections; §10 begins at **L2611** and carries no
revision-6 entry).

`H-3` applies the ownership test clause by clause and I agree with every row:

- *"G-11 remains OPEN — NOT RATIFIABLE **in `.softhouse/gates.md` and `.softhouse/program.json`**"*
  names the registers it copies from — **transcription**, repairable under G-11's own (closed) gate.
- *"`A2-15` … stays blocked"* transcribes `.softhouse/tasks.json` — **transcription**.
- *"DRAFT (revision 5)"* and *"§5.3 names work that must land"* are **OWNED**, are called out as
  owned, and are corrected **under G-14**, which is the gate for exactly this. Not swept in.
- **L90 onward is NOT rewritten.** `H-3b` *appends* after L90-96. I verified L90 still reads
  *"**Revision 5 changes exactly two things and nothing else**"* and that no hunk's BEFORE block
  contains any of L89-96. **The brief's explicit constraint is honoured.**

`H-3` also adds §10 entries for **both** revision 6 and revision 7, which is the right repair for the
process defect it names. **Correct, with one loose end at F-8.**

---

## Check 8 — was `T247`'s REFUSAL to certify §5.3 correct? **YES. Reproduced, and it did not dodge.**

I re-measured the refusal's own factual basis rather than accepting it.

```
git grep -P '\bP-N\b' -- nexus/internal/apps/ledger      (27 tracked files)
  P-1: 3   P-2: 5   P-3: 3   P-4: 2   P-5: 0   P-6: 4   P-7: 4   P-8: 1   P-9: 3   P-10: 7
POSITIVE control : P-5 anywhere under nexus/  → 0 hits (so it is absent from the whole module, not
                                                just this package)
NEGATIVE control : P-99 under the ledger pkg  → 0 hits
```

**`P-5` is named nowhere in the ledger package — confirmed, with the discrimination shown both ways
(`P-66`/`P-70`: I looked at all 27 tracked files under `nexus/internal/apps/ledger`, and at all of
`nexus/`).** Every other precondition is named. `T247`'s statement is exact.

I also spot-checked every source citation `H-13` would land, at `a6bec72`:
`vector.go:54` `const SchemaV1 = "gerege.ledger.vector/v1"` ✓ · `:261` `Request … P-1` ✓ ·
`:386` `Refusal … P-2` ✓ · `:101` `ClassOracleRefusal … P-2 and P-3` ✓ · `:71` `func SchemaContexts()` ✓ ·
`:63` `PRECONDITION P-9` ✓ · `:460` `DEC2Revision … P-7` ✓ · `grade.go:26` `precondition P-4` ✓ ·
`capability.go:15` `PRECONDITION P-6` ✓ · `impl.go:89-92` `registry — precondition P-10` ✓ ·
`admit.go:27` `P-9` ✓ · `admit.go:125` `P-1` ✓ · `admit.go:309` `graded_against: P-10` ✓.
**All hold.** Two citation nits at F-9.

**Judgement: the refusal was CORRECT and is the strongest thing in revision 7.** The evidence
`T247` has is *"the package names each precondition and the harness printed a green run"*. That is
evidence of **address**, not of **adequacy**. Certifying adequacy would require re-deriving `A2-15`'s
work, which nobody has done, and asserting it inside a ratified contract on the strength of source
comments is the precise class of unsupported inference that rejected this document three times.
`H-13`'s AFTER text says so in terms — *"A ratifier must read this note as 'the preconditions were
addressed and the corpus is green', never as 'P-1…P-10 are discharged'"* — and files `FU-T247-3`.
**It dodged nothing: it decided the question and the decision was "do not certify", which is a
decision, recorded, with its ground.** Two of the three legs of that ground I reproduced above; the
third (the harness executing P-4's comparator and P-10's six kills) is
`[HARNESS-DEPENDENT — NOT RE-RUN HERE]` and I neither confirm nor dispute it.

---

# FINDINGS

## F-1 — HIGH, MUST-FIX. Revision 7's "RE-MEASURED" `conformance.sh` citations are ALREADY STALE at the landing commit. This re-enacts `G-14`.

`T247` measured its citations at `9b6c596`. `main` then merged **`c13e9d8` — "T248: the fail-open
guard widened until it sees the site that motivated it"** — which added **+30 lines** to
`conformance.sh` (2543 → 2573 lines) **above `run_guards`**.

`git log --oneline 9b6c596..a6bec72 -- .softhouse/conformance.sh` → **exactly one commit, `c13e9d8`.**

| citation | revision 7 as drafted (`9b6c596`) | **TRUE at `a6bec72`** |
|---|---|---|
| `guard_ledger_invariants()` definition | `:1300-1339` | **`:1300-1339` — still correct** |
| `run_guards()` | `:1474-1500` | **`:1504-1530`** |
| the seven tallied invocations | `:1489-1495` | **`:1519-1525`** |
| the `guard_ledger_invariants` invocation | `:1494` | **`:1524`** |
| `guard_no_fail_open_instruments` | `:1495` | **`:1525`** |

These wrong numbers appear in **`H-1` fact 3**, are repeated by reference in **`H-14` fact 3**
(*"`:1300-1339` / `:1474-1500` / `:1494`"*), and are inherited by **`H-15`**'s instruction that the
§8.3 guard bullet be *"re-stamped as in H-1 fact 3"*.

**This is not a nit. It is `G-14`'s own failure mode, reproduced inside the correction for `G-14`**:
a claim published as freshly measured that went false underneath the document before it landed. If
the driver lands revision 7 as drafted, the very first thing it ships is a stale stamp.

**`T247` is not at fault** — its citations were correct at its fork and it wrote and shipped
`verify-line-numbers.py` precisely so the driver would catch this. **The instrument worked. It must
be honoured.**

## F-2 — HIGH, MUST-FIX. **The 35th site: L821, the `I-3` row of the very table revision 7 edits.**

Not in the 34-row edit list. Not in the declared HISTORY list. Column 5 of L821 reads, live at
`a6bec72`:

> `guard_ledger_invariants` (built by `A2-18`, **wired** by `T208`) **is the seventh guard
> `run_guards` invokes** and it walks the Go tree for a write path to a balance [VERIFIED by `A2-28`
> at commit `2e97162`: **`.softhouse/conformance.sh:1152-1187` defines it, `:1209` invokes it**;
> MEASURED: `invariant violations 0`].

Revision 7 rewrites **L819 (`I-1`), L820 (`I-2`) and L825 (`I-7`)** of this table and walks past
**L821**. The result, if landed as drafted: the banner says *"eight guards … the **sixth**"* and
**L821, two lines below the rows revision 7 just rewrote, says "the **seventh** guard"**, citing
`:1152-1187` and `:1209` — line numbers that were superseded at `2e97162` and are now wrong twice
over.

**This is the L820 failure mode again, one row down.** L821's *"Graded today?"* answer is still
**NO** and still correct, so no "nothing grades" wording sweep can reach it; the falsehood is in the
**supporting citation**, not in the answer. It is reachable only by the enumeration `T247`'s own E-5
implies (*"the banner and four other sites"*) and then did not carry into the edit list.

## F-3 — HIGH, MUST-FIX. §4.4.1 at **L847-874** — the same fact in full, including a fenced list that OMITS the eighth guard.

Not in the edit list. Not in the HISTORY list. Live at `a6bec72`:

- **L847-851**: *"**`run_guards` invokes SEVEN guards** [VERIFIED by `A2-28` at commit `2e97162`,
  `.softhouse/conformance.sh:1189-1213` … An independent review counted this **two ways** … and got
  seven both times]"* — **the count is FALSE (eight) and the citation is stale twice over.**
- **L854-861**: a fenced code block **enumerating the guards by name** —
  `guard_graded_root_is_this_tree`, `guard_no_float_in_vectors`, `guard_no_float_in_harness`,
  `guard_gofmt`, `guard_no_float_in_capture_requests`, `guard_no_narrow_catch_in_capture_rigs`,
  `guard_ledger_invariants`. **`guard_no_fail_open_instruments` is MISSING.**
  This is the worst single artefact in the document: a **literal enumeration**, presented as the
  authoritative list, that is materially incomplete. No wording sweep can hit a list.
- **L863-864**: *"**Five of the seven** still concern floating point, source formatting and exception
  scope, and **a sixth** concerns the repo root. **None of those six** looks for:"* — the arithmetic
  is wrong at eight guards; there are now **seven** that do not look for `I-3`/`I-4`.
- **L872-874**: *"**The seventh does**, and this is what it actually delivers [VERIFIED by `A2-28` at
  commit `2e97162`: `.softhouse/conformance.sh:1152-1187` …]"* — **ordinal as identifier, stale
  citation.**

**§4.4.1 is the section the banner and §8.1 both point a ratifier at** (*"§4.4.1 carries the
retraction, the class names, the measurement and the limits"*). Landing revision 7 without it means
the corrected banner forwards the reader to an uncorrected page.

## F-4 — MEDIUM, MUST-FIX. The ordinal was rebuilt, and the premise for rebuilding it was not established.

Both halves are argued in full under check 5. In short: (a) on the document's own all-invocations
basis the old *"the seventh"* is **still correct** at `a6bec72`, and `T247` reached the opposite
conclusion by switching to a tallied-only basis without saying so; (b) revision 7 then publishes a
**new** ordinal, *"the sixth"*, in the banner — one perishable positional claim swapped for another,
in the sentence that warns against doing so.

## F-5 — MEDIUM, MUST-FIX. **§5's section heading, L1426, is a live falsehood nobody enumerated.**

```
1426| ## 5. What DEC-2 would be frozen against — and today that is ZERO vectors
```

Not in the edit list, not in the HISTORY list. It asserts, **in a section heading, in the present
tense**, the same proposition `H-12` retracts in the prose **26 lines below it** (L1452,
*"DEC-2 would be frozen against a corpus that does not yet exist in the store"*). Six ledger vectors
exist at `a6bec72`. Landing `H-12` without the heading is the document's own named defect —
*"a correction landing where a reviewer NAMED it and not where the document RESTATES it"* — committed
inside the same section, 26 lines apart.

## F-6 — LOW. §5.2's heading, L1726.

```
1726| ### 5.2 The decision: EXTEND the machinery — and DEC-2 grades nothing until it exists
```

Reads as a still-pending condition. The machinery exists and DEC-2 grades. Weaker than F-5 (the
heading is about a decision, and the body correctly narrates the decision as historical), so this is
optional — but if the driver fixes F-5 it should look at this in the same pass.

## F-7 — LOW, MUST-FIX (cheap). §8.3's guard bullet still says *"the seventh guard"* twice.

`H-15` closes with *"(the `conformance.sh` hard-guards bullet at L2438-2450 is UNCHANGED except that
its `guard_ledger_invariants` citations are re-stamped as in H-1 fact 3.)"*. **That bullet contains no
`conformance.sh:` line citation to re-stamp** — only a commit stamp `2e97162`. What it *does* contain
is **L2441** *"the **seventh** guard exists now (§4.4.1)"* and **L2449** *"the SEPARATE **seventh**
guard is what walks for those"*, which `H-15`'s instruction does not reach. Landing as drafted leaves
the banner saying "sixth" and §8.3 saying "seventh" about the same guard.

## F-8 — LOW. §10's revision-5 entry self-identifies as the current document.

L2613: *"**Revision 5 (this document)** — DRAFT, task `A2-32` …"*. `T247` lists **L2614-2615** as
HISTORY-untouched but not **L2613**. After revision 7 the parenthetical *"(this document)"* is false.
The rest of the entry is a true historical record and must stay. Fix: drop the two words.

## F-9 — LOW. Two ambiguous/off-by-one citations revision 7 would land.

- **`admit.go:139-147`** is cited bare in `H-1` fact 2 and in `H-15`'s first bullet, both times
  surrounded by *ledger*-schema text. At `a6bec72`, **`ledger`'s** `admit.go:139-147` is the
  `request.ProductID` / `request.accounting_rule` rules; the context-refusal it means is
  **`nexus/internal/apps/loanschedule/conformance/admit.go:139-147`** (verified: L139
  `if v.Context != "" && !IsSchemaContext(v.Context)`). **Qualify the path** — an unqualified
  `admit.go` in a document that now discusses two packages is a citation that points at the wrong
  file.
- **`loanschedule/conformance/vector.go:77-81`** is cited for `SchemaContexts()`. At `a6bec72` the
  function is **L78-82** (L77 is comment tail, L82 is the closing brace). Off by one at both ends.

## F-10 — INFO, no action. `H-13`'s "eight preconditions by name".

`H-13` says the package addresses *"P-1, P-2, P-3, P-4, P-6, P-7, P-9 and P-10 by name"* — eight.
Measured, **nine** of the ten are named in the package: `P-8` also appears once, at
`ledger/conformance/admit.go:201` (`"exempt (P-8)"`). The load-bearing claim — that **P-5 alone is
named nowhere** — is exact and unaffected. Recorded for completeness, not as a required change.

---

# CORRECTIONS THE DRIVER MUST APPLY BEFORE RATIFYING

**C-1 (F-1) — re-run `verify-line-numbers.py` at the LANDING commit and re-stamp every
`conformance.sh` citation from that run, not from `9b6c596`.** At `a6bec72` the correct values are:

```
definition          .softhouse/conformance.sh:1300-1339      (unchanged)
run_guards          .softhouse/conformance.sh:1504-1530      (was drafted :1474-1500)
seven tallied       .softhouse/conformance.sh:1519-1525      (was drafted :1489-1495)
guard_ledger_invariants invoked at              :1524        (was drafted :1494)
guard_no_fail_open_instruments at               :1525        (was drafted :1495)
```

Apply in **`H-1` fact 3**, **`H-14` fact 3**, and anywhere `H-15` inherits them. **If the landing
commit is not `a6bec72`, these numbers must be measured again — do not copy them from this review.**
`verify-line-numbers.py` must exit **0** at the landing commit before the edit is applied.

**C-2 (F-2) — add L821 to the edit list.** Replace, in the `I-3` row's column 5, the clause
*"is the seventh guard `run_guards` invokes"* with a **name-only** form, and re-stamp the citation.
Suggested minimal edit, obligation-free (it touches only the supporting citation; the row's
*"Graded today?"* answer **NO BY A VECTOR** and its `G-12` warning are untouched):

> `guard_ledger_invariants` (built by `A2-18`, **wired** by `T208`) is one of the guards `run_guards`
> invokes on every run, and it walks the Go tree for a write path to a balance
> [RE-MEASURED by `<landing task>` at `<landing commit>`: `.softhouse/conformance.sh:1300-1339`
> defines it, `:1524` invokes it. **Revisions 1–6 read "is the seventh guard `run_guards` invokes"
> and cited `:1152-1187` / `:1209`, stamped at `2e97162`; both the count and the line numbers have
> since moved.**]

**C-3 (F-3) — add §4.4.1 L847-874 to the edit list.** Four things must change together:

1. **L847** *"invokes SEVEN guards"* → **EIGHT**, with the citation re-stamped to `:1504-1530`, and
   the *"an independent review counted this two ways and got seven both times"* clause restated as
   the historical record it now is rather than left as a live corroboration.
2. **L854-861** — **add `guard_no_fail_open_instruments` to the fenced list** (it is invoked at
   `:1525`, wired by `T243`). A list presented as authoritative and missing a member is worse than
   a stale sentence.
3. **L863-864** — *"Five of the seven … a sixth concerns the repo root. None of those six"* →
   *"Five of the eight … a sixth concerns the repo root, a seventh concerns fail-open instruments.
   None of those seven"*.
4. **L872** — *"**The seventh does**"* → *"**`guard_ledger_invariants` does**"*, citation re-stamped
   to `:1300-1339`.

**C-4 (F-4) — delete the new ordinal from `H-1` fact 3 and `H-14` fact 3.** Keep the **count**
(*"invokes eight guards: one short-circuits, seven are tallied"*) — the count is what the sentence
needs, and it is what actually went false. **Drop *"of which `guard_ledger_invariants` is the
sixth"*;** the name already identifies it, the ordinal adds nothing and is the same perishable shape
whose companion line numbers went stale in under one fire. Correspondingly, **soften the retraction
clause**: at `a6bec72` *"the seventh"* is still true on the all-invocations basis the old text used,
so the honest retraction is *"the COUNT was seven and is now eight"*, not *"the ordinal now points at
a different guard"*.

**C-5 (F-5) — correct §5's heading, L1426.** e.g.
`## 5. What DEC-2 was frozen against — and at ratification that was ZERO vectors`, or add the
revision-7 re-measure marker the section body already carries. Landing `H-12` without this leaves the
retracted proposition standing 26 lines above the retraction.

**C-6 (F-7) — extend `H-15`'s instruction** so the §8.3 guard bullet's *"the seventh guard"* at
**L2441** and **L2449** is corrected to the guard's **name**, not merely "citations re-stamped"
(there are no line citations in that bullet to re-stamp).

**C-7 (F-8) — drop *"(this document)"* from §10 L2613** when the revision-6 and revision-7 entries
are added. The rest of that entry is history and must stay.

**C-8 (F-9) — qualify `admit.go:139-147` as `loanschedule/conformance/admit.go:139-147`** in `H-1`
fact 2 and `H-15` bullet 1, and correct `loanschedule/conformance/vector.go:77-81` to **`:78-82`**.

---

# WHAT I DID **NOT** FIND, STATED SO THE ABSENCE IS NOT READ AS EXHAUSTIVE

- **No obligation moved.** Re-derived per hunk; I am confident in this and it is the finding the gate
  exists to protect.
- **No PIN bump, no digest movement, no write under `.softhouse/vectors/`, `nexus/`,
  `.softhouse/conformance.sh`.** Verified across all 17 hunks.
- **No weakening of the caution.** It is strengthened in four places, and its ratio has both terms
  measured from the file.
- **What this review could not do:** run the harness (oracle unreachable; harness broken on Linux per
  `T253`). Every claim in revision 7 that depends on a harness run — the `4 / 2 / 21` counts, the
  invariant `INDEPENDENT`/`DEPENDENT` split, the census pins, `P-4`'s 70 cells and `P-10`'s six kills
  — is **NOT re-verified here**. Their *sources* (the six vector files, `capabilities-ledger.json`,
  the Go package) are verified; their *runtime output* is not.
- **What my enumeration could not have found:** a restatement carried as a bare number in a table
  cell with no surrounding concept word; a claim expressed as a silence where a qualification should
  be; a restatement using none of my 17 concept patterns **and** none of the six citation strings.
  The `conformance.sh`-citation family (check 2b) **is** exhaustive — it is a string enumeration over
  a single file, calibrated on five distinct patterns that agree on the same five sites.
- **Where I looked, for the non-existence claims:** `P-5` — all 27 tracked files under
  `nexus/internal/apps/ledger`, then all of `nexus/`. ADR-reads-by-code — `nexus/` and
  `.softhouse/conformance.sh` only; I did **not** search `.softhouse/bin/`.

---

# THE ONE-LINE RECOMMENDATION

**Revision 7's substance is sound and its refusals are its best feature. Do not ratify it as
drafted.** Apply **C-1 … C-8**, re-run `verify-line-numbers.py` **at the landing commit** with the
three `conformance.sh` rows updated to the values that commit measures, confirm it exits **0**, and
then land. `G-14` closes on that.

**Re-measured at exit (P-69):** `HEAD` = `a6bec723fd0769d5c5b6349a375756d1104a7c73`;
`HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`. Both unchanged since entry.
`T251` edited **nothing** outside `.softhouse/reviews/t251-dec2-rev7/` and its handoff.
