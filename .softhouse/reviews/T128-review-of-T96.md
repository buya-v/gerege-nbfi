# T128 — independent review of T96 (`softhouse/T96-sole-caller-census`)

Run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`, role `reviewer`.
Branch `softhouse/T128-review-t96`, forked from `main` at `9027f005`.
Reviewing `softhouse/T96-sole-caller-census` (5 commits) against fork point **`8faee447`**.

> Terminology: "the oracle" is the **Fineract reference implementation** pinned at
> `426a23544`. Oracle Database is prohibited in this program and nothing here touches
> a database. **No oracle instance was POSTed to**; no container was started,
> restarted, rebuilt or re-seeded. `conformance.sh` was run read-only and its probe
> reported the reference oracle `up`.
>
> P-25: every number in this review is an integer line/token/file count produced by
> `wc -l`, `grep -c`, `go/scanner` or `shasum`. No floating point anywhere.

---

## VERDICT: **MICRO-FIX**

T96 delivered its charter. `:743` **is** the sole caller of
`calculateEMIOnNewModelAndMerge` in the pinned tree — I re-derived it and it is
**stronger** than T96 argued. All six published counts reproduce their published
numbers, all six decompose line-for-line, all six go red on the edit they exist for,
and graph 6 goes `2 → 3` RED with graphs 1–5 green on the same tree, which is
F-T89-4 measured rather than argued. Every correction T96 made to T78's text is
correct. Zero executable change is proven at the token level.

Three defects remain, all in the guard *text*, all comment-only, and two of them are
live instances of **exactly the class T96 was chartered to close (P-22)**:

- **F-T128-1** — the shipped, "hardened", tokenising graph-4 command is **silently
  green on at least four legal five-constant enum edits**, and its stated reason
  ("strips comments") is false. Graph 4 is closure-critical.
- **F-T128-2** — the whole-tree scope correction landed in **part 9** and not at the
  two sites where the claims are actually made (`:587`, `:625`), which still tell the
  reader to grep **"in the pinned file"**. I drove the `:625` instruction green on a
  tree with five call sites into `:718`. P-21/P-26, fourth recurrence.
- **F-T128-3** — B-3 is understated and its published mitigation is defeated. A
  **pure addition with no deletion** defeats all six counts, and "reproduce the LINES"
  does not catch it because the line numbers do not change.

Each is a small, precisely specifiable text edit. Nothing about the sole-caller
verdict, the six numbers, or the executable-change gates is in question. Hence
MICRO-FIX rather than REJECTED — but **F-T128-1 and F-T128-2 must be fixed before
merge**, because both leave a believed-and-dead guard at the point of a
closure-critical claim, which is the precise failure P-22 exists to forbid.

---

## 1. The sole-caller verdict — **CONFIRMED, and stronger than claimed**

Re-derived at `426a23544` (`git -C /Users/buv/fineract rev-parse HEAD` =
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, "Merge pull request #5946").

```
$ git grep -n "calculateEMIOnNewModelAndMerge" 426a23544 -- . | cat
…/ProgressiveEMICalculator.java:743:            calculateEMIOnNewModelAndMerge(relatedRepaymentPeriods, scheduleModel, operation);
…/ProgressiveEMICalculator.java:1744:    private void calculateEMIOnNewModelAndMerge(List<RepaymentPeriod> repaymentPeriods, …
$ … | wc -l
       2
```

**Exactly two lines.** Corroboration, each run rather than inherited:

| probe | result |
|---|---|
| tracked files at the pin | **7,890** — matches T96 exactly |
| `.java` among them | **6,586** — matches T96 exactly |
| case-insensitive `git grep -in` | 2 lines, the same two |
| prefix probe `EMIOnNewModel` | 2 lines, the same two |
| looser probes `NewModelAndMerge`, `AndMerge` | 2 lines, the same two |
| non-Java JVM sources (`.kt`/`.kts`/`.scala`) | **none exist in the tree** |
| `.groovy` files | 9, all under `buildSrc/` (Gradle plugin/services); none names the method |
| `getDeclaredMethod` / `setAccessible` / `ReflectionTestUtils` / `MethodHandles` in `fineract-progressive-loan` | **no hits** (control grep in the same 100-file path filter returns hits, so the filter is live) |
| `getDeclaredMethods()` tree-wide | **one** — `WorkingCapitalLoanAccountStepDef.java:3484`, filtered `equalsIgnoreCase("get" + fieldName)` |

**T96's `private` inference holds, and the source gives three stronger reasons it
never got:**

1. The class is **`final`** —
   `@Component @RequiredArgsConstructor public final class ProgressiveEMICalculator`
   [VERIFIED `ProgressiveEMICalculator.java:71-73`]. A CGLIB proxy cannot subclass a
   `final` class at all, so the "proxy delegates only to public methods" argument is
   not even needed; there is no CGLIB proxy of this type to reason about.
2. **The seam we actually port constructs it with `new`.**
   `EmbeddableProgressiveLoanScheduleGenerator.java:40` is
   `new ProgressiveEMICalculator(scheduledDateGenerator)` — no container, no proxy.
   The only 8 tree-wide references to the type are: this file, the class itself, an
   `.adoc`, and two test classes that also use `new` (`LoanScheduleGeneratorTest.java:47`,
   `ProgressiveEMICalculatorTest.java:72`).
3. **The one bytecode-manipulating build step is provably out of reach.** The tree
   *does* have one — EclipseLink **static weaving**, applied to every subproject
   (`build.gradle:167-169` → `static-weaving.gradle`), which T96 listed as
   `[UNVERIFIED]` and "not looked for". I looked. `static-weaving.gradle:38-42`
   selects managed classes by
   `@Entity|@MappedSuperclass|@Converter` or a concrete `AttributeConverter`.
   `ProgressiveEMICalculator` is a `@Component` and matches none of them, so it is
   never handed to `StaticWeave`. There is **no** `@EnableLoadTimeWeaving`, **no**
   `LoadTimeWeaver`, and **no** `aop.xml` anywhere in the tree; the only AOP is
   `@EnableAspectJAutoProxy` (`MetricsConfig.java:29`), which is proxy-based, and an
   aspect adds advice around a join point — it never introduces a *call to* a
   private method.

**Ruling: no second caller exists, and T96's UNVERIFIED item "bytecode-level callers
are out of scope" can be narrowed** to "no *build-time* weaving can reach this class",
with only runtime-assembled reflection left genuinely unfalsifiable by text search.
That narrowing belongs in the block.

---

## 2. All six published commands — **6 of 6 reproduce their own numbers**

Run exactly as part 9 publishes them, at the pin:

| graph | identifier | published | mine | ✓ |
|---|---|---|---|---|
| 1 | `setFutureUnrecognizedInterest` | 3 | **3** | ✓ |
| 2 | `calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer` | 3 | **3** | ✓ |
| 3 | `calculateEMIValueAndRateFactors` | 9 | **9** | ✓ |
| 4 | `EmiChangeOperation.Action` constants (tokeniser) | 4 | **4** | ✓ |
| 5 | `calculateLastUnpaidRepaymentPeriodEMI` | 18 | **18** | ✓ |
| 6 | `calculateEMIOnNewModelAndMerge` | 2 | **2** | ✓ |

The block's second claim — that plain `grep -rn` over a clean
`git archive 426a23544 | tar -x` export "gives the same six numbers" — also holds. My
export produced **7,890 files** and my own census script read `3 3 9 4 18 2`.

**Decompositions, re-derived line for line, all exact:**

- **G1 = 3**: `ProgressiveEMICalculator.java:1184`, `:1246`,
  `AdvancedPaymentScheduleTransactionProcessor.java:1995`. `RepaymentPeriod.java:127`
  is the copy-constructor assignment fed by `:156`
  (`repaymentPeriod.getFutureUnrecognizedInterest()`) — propagation, as stated.
- **G2 = 3**: callers `:392`, `:1217`; declaration `:1221`.
- **G3 = 9**: calls `:149, :280, :317, :356`; declaration `:718`; dispatch `:722, :723`;
  prefix-sharing declarations `:703, :730`.
- **G4 = 4**: `DISBURSEMENT`/`INTEREST_RATE_CHANGE`/`CAPITALIZED_INCOME`/`ADD_REPAYMENT_PERIODS`
  at lines **33–36**, enum header `:32`, close `:37`. The cited factory ranges
  `:47-49, :51-53, :55-57, :59-62` and `withZeroAmount()` `:64-69` all land where the
  block says.
- **G5 = 18**: 17 calls `:247, :368, :380, :404, :442, :505, :626, :698, :747, :868,
  :879, :937, :1091, :1214, :1288, :2024, :2129` + declaration `:1160`. `13 + 4 = 17`
  reconciles.
- **G6 = 2**: call `:743`, declaration `:1744`.

---

## 3. The red demonstration — **reproduced independently**

Rig: my own `git archive 426a23544 | tar -x` export (7,890 files), a `cp -R` mutant
copy verified byte-identical by `diff -rq` before each mutation, a driver that
**fails if the mutation is a no-op**, and a census script printing all six with
GREEN/RED. Nothing was compiled; this is a text census, as it must be.

**M-6 — a second call to `calculateEMIOnNewModelAndMerge` in the flat-interest arm
(after `:712`), the plausible upstream change T96 chose:**

```
GRAPH 1 setFutureUnrecognizedInterest                      = 3    [expect 3  ] GREEN
GRAPH 2 calc...TillDateOnScheduleModelCopyAndDefer         = 3    [expect 3  ] GREEN
GRAPH 3 calculateEMIValueAndRateFactors                    = 9    [expect 9  ] GREEN
GRAPH 4 EmiChangeOperation.Action constants                = 4    [expect 4  ] GREEN
GRAPH 5 calculateLastUnpaidRepaymentPeriodEMI              = 18   [expect 18 ] GREEN
GRAPH 6 calculateEMIOnNewModelAndMerge                     = 3    [expect 2  ] RED  <-- MOVED
```

**`2 → 3` RED with graphs 1–5 all GREEN.** F-T89-4 confirmed by measurement: the
pre-T96 tripwire was structurally incapable of seeing the one edit that breaks the
argument it guards. **This is the finding of the task and it stands.**

Every other "goes red on its own edit" claim also reproduced:

| mutant | edit | result |
|---|---|---|
| M-1 | 4th `setFutureUnrecognizedInterest` write | **G1 3 → 4 RED** |
| M-2 | 3rd caller of `:1221` | **G2 3 → 4 RED** |
| M-3 | 5th call site of `:718` | **G3 9 → 10 RED** |
| M-4 | 5th `Action` constant, trailing comma | **G4 4 → 5 RED** |
| M-5 | 18th call of `:1160` | **G5 18 → 19 RED** |
| M-6 | 2nd caller of `:1744` | **G6 2 → 3 RED, G1–G5 GREEN** |

And T96's two self-caught graph-4 mutants behave as recorded on the shipped
tokeniser: **M-4b** (5th constant, *no* trailing comma) → **5 RED**; **M-4c** (two
extra constants on one line) → **6 RED**.

**The published blind spots B-1, B-2, B-3 all reproduce as described:**

- **B-1 / M-2b** (3rd caller of `:1221` in `ProgressiveLoanScheduleGenerator.java`):
  whole-tree **4 RED**; file-scoped **3 GREEN**.
- **B-1 / M-3b** (5th call site of `:718` in another file): whole-tree **10 RED**;
  file-scoped **9 GREEN** — on a tree with five call sites.
- **B-2 / M-1b** (4th write site in `fineract-loan/src/main`): whole-tree **4 RED**;
  the two-directory grep **3 GREEN**.
- **B-3 / M-3c** (5th call site into `:718` **plus** one dispatch line renamed):
  graph 3 reads **9 GREEN** on a file whose call sites into `:718` are
  `:149, :280, :317, :356, :713` — **five**, closure broken, all six green.
- **B-3 / M-5b** (new `:1160` call **plus** deletion of the `:2129` call): graph 5
  reads **18 GREEN**.

---

## 4. Is the blind-spot class closed, or has it moved? — **IT HAS MOVED**

This is the question T96 could not ask of itself, and the answer is the substance of
this review. I attacked the **fixed** versions.

### F-T128-1 (P-22, live in the shipped block) — the tokenised graph-4 command is silently green on at least four legal Java five-constant edits

The block ships this as the fix, with this justification
[`emi.go:969-978`]:

> THIS ONE IS NOT A GREP … TOKENISE IT; DO NOT MATCH WHOLE LINES. … The form above
> **strips comments**, splits on commas and counts identifiers, and reads 5 and 6 on
> those two mutants.

**"Strips comments" is false.** `sed 's|//.*||'` strips *line* comments only. It does
not strip `/* … */`, and comma-splitting is not tokenising. Four mutants, each adding
a **fifth** constant, each legal Java, each read by the shipped command as **4, GREEN**:

| mutant | fifth constant written as | shipped command reads |
|---|---|---|
| **M-4d** | `REAMORTIZE("reamortize"), //` (constructor argument; legal with an overloaded ctor) | **4 — SILENTLY GREEN** |
| **M-4e** | `ADD_REPAYMENT_PERIODS, /* legacy */ REAMORTIZE, //` (block comment) | **4 — SILENTLY GREEN** |
| **M-4f** | `public enum Action { REAMORTIZE, //` (constant on the enum header line) | **4 — SILENTLY GREEN** |
| **M-4g** | `REAMORTIZE { }, //` (constant class body) | **4 — SILENTLY GREEN** |

**These are not exotic.** The enum's current one-constant-per-line layout is held in
place *only* by the trailing `//` markers on every line — the standard Eclipse-formatter
line-break hint. Fineract's own formatter config sets
`org.eclipse.jdt.core.formatter.join_wrapped_lines = true` and
`alignment_for_enum_constants = 0` [VERIFIED `config/fineractdev-formatter.xml`], and
spotless applies it to all Java (`build.gradle:505-510`). **Drop the `//` hints and
the project's own formatter emits exactly the M-4e/M-4f shape.** The M-4c mutant T96
did try goes RED; the same shape with a block comment interposed goes GREEN. T96 fixed
the two *instances* it found and shipped a command it believed general.

**Why it matters:** graph 4 is closure-critical. Part 4 states
[`emi.go:658-661`]: *"A fifth route into `:718` cannot appear without either a fifth
`Action` constant or a fifth call site, and both are compile-visible edits to the
pinned oracle that part 9's counts detect."* On M-4d/e/f/g there **is** a fifth
constant and the count does **not** detect it.

**Required fix.** Either count constants with a real tokeniser (strip `/* */` too;
split on `,` *and* on `{`, `(` and the enum header brace; or simply `javap`/parse), or
— cheaper and honest — **publish these four as named residual blind spots of graph 4**
in the same voice as B-1…B-5, and delete the words "strips comments".

### F-T128-2 (P-21/P-26, live) — the scope fix landed in part 9, not where the claims are made

T96 diagnosed B-1 correctly and wrote in §4: *"Graph 3 is the closure-critical one …
so this was a live P-22 in the block. **Fixed**: part 9 now specifies a whole-tree
`git grep` at the pin."* Part 9 is fixed. The **sites that make the claims are not**:

- **`emi.go:586-588`** (PART 2): `:1221 has EXACTLY TWO callers [VERIFIED at
  426a23544: **grep the method name in the pinned file** returns :392, :1217 and the
  declaration :1221]`.
- **`emi.go:625-631`** (PART 4, closure-critical): `:718 has EXACTLY FOUR call sites
  [VERIFIED at 426a23544: **grep "calculateEMIValueAndRateFactors" in the pinned
  file** returns NINE lines …]`.

Both are verbatim the file-scoped form part 9 itself names as broken
[`emi.go:946-949`]. Driven red/green on my scratch tree:

```
M-3b (fifth call site of :718, in ProgressiveLoanScheduleGenerator.java)
  part 9's whole-tree command      : 10   [expect 9]  RED
  part 4's :625 instruction        :  9   [expect 9]  GREEN   <-- DEAD GUARD
M-2b (third caller of :1221, in another file)
  part 9's whole-tree command      :  4   [expect 3]  RED
  part 2's :587 instruction        :  3   [expect 3]  GREEN   <-- DEAD GUARD
```

A third survivor of the same sweep, phrased differently again:

- **`emi.go:530-532`**: *"closed at every level by **a count that a grep reproduces**"*
  — the block's own statement of method, and false since graph 4 was shown not to be a
  grep. T96 corrected this exact proposition at `:661` and `:691` and missed `:531`.

This is P-26 precisely: T96 swept for its own wording (`grep-reproducible`,
`exhaustive by grep`, `by grep`) and every survivor is phrased differently. **The
scope claim must be corrected at `:587`, `:625` and `:531`, not only in part 9.**
Part 1's write census is the counter-example that shows the sweep gap is real rather
than deliberate: there the widening *is* stated at the point of use
[`emi.go:537-543`].

### F-T128-3 — B-3 is understated, and its published mitigation is defeated

The block says [`emi.go:1039-1047`]:

> THEY STAY GREEN ON A CANCELLING PAIR. Every one is a line count, so **an addition
> offsets a deletion**. … The defence is that the numbers here are DECOMPOSED …
> so a reader who reproduces the LINES, and not only the total, sees the substitution.
> **REPRODUCE THE LINES.**

Both halves are weaker than stated. **No deletion is required**: an addition placed on
a line that already carries the identifier suffices.

```
M-6b: a SECOND call to calculateEMIOnNewModelAndMerge on the SAME physical line 743
      GRAPH 6 = 2   [expect 2]  GREEN     (two call sites; count unmoved)
M-1c: a fourth setFutureUnrecognizedInterest write appended to line 1184
      GRAPH 1 = 3   [expect 3]  GREEN
M-3d: a fifth-call-site mention folded onto the existing :718 declaration line
      GRAPH 3 = 9   [expect 9]  GREEN
```

And on M-6b the published mitigation **fails**: graph 6's decomposition is the line
list `:743` (call) and `:1744` (declaration), and after the mutation the line list is
**still** `:743` and `:1744`. A reader who does exactly what the block instructs —
reproduce the lines, not the total — sees no change. The mitigation degrades to
"re-read the *content* of every listed line", which is a stronger instruction than the
block gives. (It does hold for M-3c, where the line numbers shift; the block's own
example is the favourable case.)

**Honest severity bound, which the block should also carry:** Fineract's Checkstyle
enables `OneStatementPerLine` [VERIFIED `config/checkstyle/checkstyle.xml:112`], so
the two-*statement* form (M-6b, M-1c) would be rejected by the upstream build. It does
not constrain a nested call, a same-line comment mention, or graph 4. So the correct
statement is not "exhaustive" but "exhaustive **modulo** the upstream formatter and
checkstyle configuration, which is not part of this pin's guarantee."

### F-T128-4 (minor) — graph 4's command does not name the pin

Part 9 justifies the other five commands with: *"It names the pin, so it cannot
silently read a moved HEAD"* [`emi.go:936-939`]. Graph 4's published form is
`sed -n … FILE`, a placeholder for a working-tree path, and names no pin. The
handoff's table version *does* (`git show 426a23544:…`); the shipped block does not.
Asymmetry unstated. One-line fix.

### F-T128-5 (minor, factual) — bare-filename citations are already drifting

`EmiChangeOperation.java` lives at
`fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/**data**/`,
not `…/calc/`. This is the same class T96 logged as **B-T96-3** for
`AdvancedPaymentScheduleTransactionProcessor.java` — which is likewise in
`fineract-progressive-loan/src/main`, while part 1's own grep scope pairs it with
`fineract-provider/src/main`. B-T96-3 is a correct diagnosis, left unfixed. Worth
doing in the same MICRO-FIX pass since the file is already open.

---

## 5. T96's corrections to T78 — all verified

**(a) T78's part-1 parenthetical is false both ways. CONFIRMED.**

- Under the **setter** name: `git grep -n "setFutureUnrecognizedInterest" 426a23544 -- .`
  → 3 lines, and `OverdueBalanceCorrection.java:26` is not one of them. That line is
  `* corrections on model copies to prevent phantom futureUnrecognizedInterest.` — it
  contains the **field** name and not the setter name at all.
- Under the **field** name, case-insensitively: **28** over the two `src/main` trees,
  **31** checkout-wide — not one. Exact match to T96.
- "Of which exactly TWO are prose — `ProgressiveEMICalculator.java:1228` and
  `OverdueBalanceCorrection.java:26`": true of the **28**. Checkout-wide there is a
  third comment line, `RepaymentPeriodTest.java:123` (`null, // futureUnrecognizedInterest`).
  The nearer antecedent is "28 mentions", so the sentence is defensible; it is
  ambiguous enough to be worth one clarifying word. **Nit, not a finding.**

**(b) Part 9 claimed all counts were greps while graph 4 had no command. CONFIRMED**
against the fork-point text: `8faee447:emi.go` reads *"FIVE counts, each reproducible
by one grep"* and *"[VERIFIED at T78: graphs 1, 2, 4 and 5 re-derived by grep …]"*,
while graph 4's entry is only `4 constants [EmiChangeOperation.java:32-37]` — no
command at all.

**(c) The `five|FIVE` sweep. CONFIRMED EXACTLY.** `grep -nE "five|FIVE"` on T96's
`emi.go` returns **6** hits and I read every one: `:451` "the five tails", `:685` "the
five counts T78 wrote here" (deliberately historical), `:701` "five separate line
ranges", `:907` "THE OTHER FIVE PINNED ORACLE INPUTS", `:1002` "the five inherited
ones" (deliberate), `:1042` "FIVE call sites into :718" (the M-3c mutant). **No stale
five survives.**

**(d) The "grep-reproducible" sweep. INCOMPLETE — see F-T128-2.** Three restatements
were found and corrected; at least three more survive (`:531`, `:587`, `:625`), each
phrased differently from the sweep terms.

**(e) F-T89-4 closure. CONFIRMED.** T89 asked for `:743`-is-sole-caller as "a sixth
tripwire graph" because "a second caller could appear in the pinned oracle without any
of the five counts moving". T96 states it at both spend sites (part 4's
unreachability inference and part 5 term 4's "only isCopy() model in the program"),
counts it as graph 6, and drove it red. Closed.

---

## 6. Hard gates

| gate | required | measured | ✓ |
|---|---|---|---|
| non-comment change vs fork point | 0 | **0 — token streams identical** | ✓ |
| comment-stripped `emi.go` vs `main` | identical | **identical, sha256 `c5a49c3f…`** | ✓ |
| `contract.go` digest | `0db73d4a…` unchanged | **`0db73d4a…` at `8faee447`, `main`, branch** | ✓ |
| `gofmt -l` | names `contract.go`, not `emi.go` | **`internal/apps/loanschedule/contract/contract.go` only** | ✓ |
| `go build ./...` | 0 | **0** | ✓ |
| `go vet ./...` | 0 | **0** | ✓ |
| `go test ./... -count=1` | green | **ok** (`loanschedule` 8.18 s, `conformance` 31.13 s) | ✓ |
| `conformance.sh` | PASS 0 / 42 / 5576 / 0 / 0 | **PASS exit 0, 42, 5576, 0, 0**, `probe = up` | ✓ |

**Zero executable change, proven independently and more strongly than T96 did.**
Rather than trust a textual comment-stripper, I tokenised both files with the Go
toolchain's `go/scanner` (`.softhouse/toolchain/go/bin/go`, **go1.26.6 darwin/arm64**)
and compared token streams with `COMMENT` tokens dropped — immune to comment markers
inside string literals and to all whitespace:

```
A emi_forkpoint.go (8faee447): 4224 non-comment tokens
B emi_t96.go       (branch)  : 4224 non-comment tokens
IDENTICAL: token streams equal with comments removed -> ZERO EXECUTABLE CHANGE
```

Same result against `main`. I *also* reproduced T96's own stripper output exactly —
**532 lines**, sha256 `c5a49c3fa752ea88946a4104f7cfcf54b0b3f81962f0bc972fb4e1987af13179`
on both `main`'s and the branch's `emi.go`.

**P-24 — the merged state was tested BY MERGING, not argued.** T96 flagged its own
post-merge reasoning as "an argument, not a scratch merge". I did the scratch merge:
`git checkout -b tmp-T128-mergetest main` (at `9027f005`, four commits past T96's
stated `f7e3d59`) then `git merge --no-ff`. Clean, ort strategy, 2 files. The merged
`emi.go` is byte-for-byte the branch's (sha256 `ddecac8b…` on both), and `main` never
touched `emi.go` since the fork — `git log 8faee447..main -- …/emi.go` is empty and
the blob id is `03cbd6bf…` at both. **All eight gate rows above were measured on the
merged tree**, not on the branch. Scratch branch deleted.

**`main` moved again while this review ran** — `9027f005 → bcf2c55b`, 21 commits. One of
them, `79a67d1` ("T109 and T96 done"), is an orchestrator **ledger** entry and not a
merge: `git merge-base --is-ancestor softhouse/T96-sole-caller-census main` reports
**NOT MERGED**, so this review remains pre-merge. Re-checked against `bcf2c55b`:
`git log 8faee447..main -- …/emi.go …/contract/contract.go` is **empty**, `emi.go` is
still `f7741f1a…` (fork-point bytes) and `contract.go` still `0db73d4a…`. The
scratch-merge result above holds against current `main` unchanged.

Scope: `git diff --name-only 8faee447...softhouse/T96-sole-caller-census` lists exactly
two paths — `nexus/internal/apps/loanschedule/emi.go` and the T96 handoff. Nothing
under `.softhouse/vectors/`, `.softhouse/capture/`, `.softhouse/state/`, `PIN.json`,
`capabilities.json` or `tasks.json`.

Standing constraints: no float on any money path (zero executable change at all, and
this review's own analysis is integer counts only, P-25). No MySQL/MariaDB/Oracle
Database driver, dialect or `:1521`. No deposit/insured/protected/guaranteed language.
No `first_name`/`last_name`. No hard-coded TZ offset. No US payment rails. No parity
claim, no cutover, nothing promoted.

---

## 7. Required MICRO-FIX list

1. **F-T128-1** — `emi.go:969-978`. Delete "strips comments" (it strips `//` only) and
   either harden the graph-4 command or publish M-4d/M-4e/M-4f/M-4g as named residual
   blind spots, with the note that the Eclipse formatter config
   (`join_wrapped_lines=true`, `alignment_for_enum_constants=0`) makes the joined-line
   forms the project's own default output once the `//` hints are removed.
2. **F-T128-2** — `emi.go:587` and `emi.go:625`: replace "grep the method name **in
   the pinned file**" with the whole-tree `git grep … 426a23544 -- .` form part 9
   publishes. `emi.go:531`: "a count that a grep reproduces" → "a count that a
   published command reproduces" (graph 4 is not a grep).
3. **F-T128-3** — `emi.go:1039-1047`: restate B-3 as "a line count is not a site
   count; **any** addition on a line that already carries the identifier defeats it,
   with or without a deletion", record that the mitigation is *read the content of
   every listed line* (not just the line numbers), and bound the claim with
   Checkstyle `OneStatementPerLine` / the Eclipse formatter as an upstream property
   that is not part of this pin's guarantee.
4. **F-T128-4** — `emi.go:971`: name the pin in graph 4's command
   (`git show 426a23544:…`), as the other five do.
5. **F-T128-5** — fix `EmiChangeOperation.java` → `…/calc/data/EmiChangeOperation.java`
   and close T96's own **B-T96-3** for `AdvancedPaymentScheduleTransactionProcessor.java`
   (it is in `fineract-progressive-loan/src/main`, not `fineract-provider/src/main`).
6. **Optional, recommended** — narrow T96's `[UNVERIFIED]` "bytecode-level callers are
   out of scope" to record §1's positive result: the tree's one bytecode-manipulating
   build step is EclipseLink static weaving, whose class selection provably excludes
   this `@Component`; and add that the class is `final` and that the ported seam
   constructs it with `new`.

---

## 8. `[UNVERIFIED]` in this review

- **Runtime-assembled reflection.** Like T96, my sole-caller verdict rests on a text
  census. A caller built from name fragments concatenated at runtime would not appear
  in any grep. I narrowed the *build-time* half of this (no weaving path reaches the
  class) but not the runtime half. I consider it very unlikely and did not enumerate
  every reflection API across 6,586 Java files.
- **Nothing was compiled.** All 17 of my mutants are text edits to a `git archive`
  export; several would not type-check. Sound for a census claim (the census is a text
  search); proves nothing about buildability.
- **`REAMORTIZE("reamortize")` legality is my reading**, not a compiler's. Java permits
  overloaded enum constructors, so a mixed bare/arg constant list compiles given both
  a no-arg and a `String` constructor. **If that reading is wrong, M-4d falls but
  M-4e, M-4f and M-4g stand**, and any one of them is sufficient for F-T128-1.
- **The Eclipse-formatter reachability argument for M-4e/M-4f is derived from the
  config file**, not from running spotless. `join_wrapped_lines=true` and
  `alignment_for_enum_constants=0` are `[VERIFIED: config/fineractdev-formatter.xml]`;
  that they *would* join these particular constants is inference.
- **"28 `src/main` trees"** — I measure **29** module-level `*/src/main` directories
  including `buildSrc`, so 28 Fineract modules. The full `**/src/main` glob is 37.
  T96's figure is defensible; its basis is unstated.
- **Graph 5's thirteen post-origination attributions** are inherited from T73. I
  re-derived the 18 lines and the `13 + 4 = 17` arithmetic; I did not re-open the
  thirteen enclosing signatures.
- **Parts 1–8's substantive reasoning, steps (a)–(g), and `emi_L < 0` (T89's F-T89-2)
  were not re-verified.** This review graded the sole-caller fact, the six counts, the
  tripwire's ability to fail, the corrections, and the hard gates — not the money
  argument.
- **The conformance PASS grades code byte-identical to `main`.** It is a gate check,
  not evidence about this branch's content, which is comments only.
