# DEC-2 — GL / accounting adapter contract

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
>    `gerege.loanschedule.vector/v1`, its `Request`/`Expect` shapes are loan-schedule shapes, and its
>    cell whitelist is three loan-schedule cells — so **no `ledger` input and no `ledger` output can
>    be written down**. §5.1 establishes this in code, in five legs, all five of which an independent
>    review re-opened and confirmed. **This is not a gap somebody forgot to fill; it is machinery
>    that has not been built.**
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
> 3. **A guard for `I-3` (balances are derived) and `I-4` (append-only) NOW EXISTS — revision 2 said
>    it did not, and that was true when revision 2 was written.** `run_guards` invokes **seven**
>    guards, not five; the seventh is `guard_ledger_invariants`, built by `A2-18` and **wired** by
>    `T208` [VERIFIED by `A2-28` at commit `2e97162`: `.softhouse/conformance.sh:1152-1187` defines
>    it, `:1189-1213` is `run_guards` invoking all seven, `:1209` is the invocation; `A2-28`'s own
>    unfiltered run prints `ledger-invariants: PASS` and `invariant violations 0` (MEASURED, §5.4)].
>    **This does
>    NOT mean the ledger is covered, and the guard says so itself**: its PASS text reads *"no
>    violation is visible to a source-level guard over the Go tree"*, **not** *"the ledger tree is
>    covered"*; the detection surface is the **name**, so renaming a balance defeats it; and it
>    prints two `NIL-COVERAGE` lines because this Go tree declares **no database driver and contains
>    no SQL at all**, so **four of the guard's declared detection classes — `I3-SQL-BALANCE`,
>    `I4-BUILDER`, `I4-DML` and `OPAQUE-SQL` — inspected an EMPTY population** and are proven by the
>    guard's own self-test and by **nothing in this repository**. **`I4-BUILDER`'s emptiness is the
>    one the guard does NOT announce**, and it is MEASURED, both polarities, by `A2-32` — revision 4
>    said *"three"* here and recorded `I4-BUILDER` as `[UNVERIFIED]`. §4.4.1 carries the retraction,
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
>    a bare number without one should treat it as stale until re-run.
>
> **§8 contains a sentence that is true and will be misread**, so it is contradicted here in
> advance: `conformance.sh`'s hard guards *do* walk `nexus/internal/apps/ledger/`. They walk it
> **for floating-point literals and `gofmt`**. That is not `I-3`. That is not `I-4`. A reader who
> takes "the guards cover the ledger tree" to mean the double-entry invariants are enforced has
> been misled by this document, and §8 now says so at the point of the claim.
>
> **What ratifying DEC-2 would and would not buy.** It would buy a written boundary and an
> admissibility standard. It would buy **no grading whatsoever** until the machinery in §5.3
> exists. Ratification is not coverage, and this document must never be cited as though it were.


**Status: DRAFT (revision 5), 22 August 2026, drafted by task `A2-32`. NOT RATIFIED. `A2-32` is NOT
AUTHORISED to ratify it and does not.** **Revision 4 (`A2-28`) was REJECTED** by independent review
(`A2-31`) on two findings, **both of them claims this document made about `main` that were false**;
**revision 3 (`A2-21`) was REJECTED** before it by `A2-25`; **revision 2 (`A2-16`) by `A2-19`**; and
**revision 1 (`A2-13`) by `A2-14`** (local fire `20260821-125942`). **Four revisions, four
rejections.** Gate **G-11 remains OPEN — NOT RATIFIABLE** in `.softhouse/gates.md` and
`.softhouse/program.json`. **Ratification requires a FURTHER independent review passing clean AFTER
revision 5** under standing policy **P-2**; until then `A2-15` (promote GL vectors) stays blocked,
and §5.3 names work that must land before `A2-15` could succeed even against a ratified contract.

**Revision 5 changes exactly two things and nothing else** — `A2-31`'s F-1 (§4.4.1's `FU-T208-1`
parenthetical, which was false at its own `[VERIFIED]` stamp) and `A2-31`'s F-2 (the empty-population
numerator, which is FOUR and not three). **Both were swept for the CLAIM rather than the sentence,
across the whole repository**, because a correction landing where a reviewer NAMED it and not where
the document RESTATES it is the defect class that has now rejected this document three times. §10's
revision-5 entry lists every site each correction landed at, and `A2-32`'s handoff carries the sweep
population, the method, and what it skipped.

> ### ⚠ MEASUREMENT FRESHNESS — the rule revision 4 adopts, and the reason it exists
>
> **Three of the four claims that got revision 3 rejected were TRUE WHEN WRITTEN and went stale
> because the harness moved underneath them** (`A2-25` findings F-4, F-5, F-7; the fourth, F-1, was
> a sweep failure). Revision 3 was drafted against a 43-vector store and reviewed against a
> 47-file directory; by the time revision 4 was drafted the same fire had taken it to **46 parity
> vectors / 7884 cells / 50 files**.
>
> **So: every measured claim in this document carries the commit it was measured at**, in the form
> `[MEASURED by A2-28 at commit 2e97162]`. A ratifier must treat a stamp older than the tree in
> front of them as a claim to re-run, not as a fact. **The corpus counts, the guard's census figures
> and every harness `file:line` are all of this kind.** Two categories are deliberately NOT
> re-stamped forward: (i) **historical measurements** — `44 / 5711`, `4 → 5`, `5664 → 5665` — which
> are the record of what a *past* tree did and are labelled as such where they appear; and (ii)
> **Fineract citations**, which are pinned to checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`
> and do not drift.
>
> **The mechanical remedy, recommended and not performed here** (`A2-25` FU-A2-25-3): cite
> **function name plus a grep recipe** rather than a bare line range, or re-take every harness
> citation mechanically at ratification time. Revision 4 re-took them by hand; that does not scale
> and will go stale again.

**Why revision 3 was rejected, in one paragraph, because it is the thing a ratifier most needs to
know.** `A2-25` reproduced §5.1.1's central retraction independently on both sides of `A2-20`, to
the digit, and confirmed §5.1's five legs, the seven-guard count and §2.2 B-4. It nevertheless
**REJECTED** revision 3 because the document asserted **four things that were false about the tree
a ratifier would be ratifying it against**: (F-1) §8.3 still carried *"They are not checked. No
guard for either exists"* **ten lines below** the same bullet's statement that the guard exists —
the same correction-leak defect class that got revision 2 rejected; (F-2) *"three of its **four**
detection classes"* — the guard declares **seven**, and the figure had been asserted as a
measurement; (F-3) **§5.2 requirement 6's BEFORE cannot be satisfied on the bytes it specifies**,
measured by `A2-25` authoring the exact vector and running it; and (F-4) §5.4's F3 caveat describes
a harness defect `A2-22` has since fixed. Revision 4 addresses all four, plus `A2-25`'s F-5, F-6,
F-7, F-8 and F-9. **The full list is §10's revision-4 entry, item by item against `A2-25`'s seven.**

**Why revision 2 was rejected, kept because revision 4 inherits its retraction.** `A2-19` found **one rejection-grade defect**: a single claim, asserted in three places, that
it **falsified by measurement** — *"no `ledger` vector CAN exist"*. A relabelled `loanschedule`
parity vector was admitted, graded and counted at **`VERDICT: PASS (exit 0) — 44 parity vectors …
5711 cells`**. The driver reproduced it independently to the same figures. **Revision 3 retracts the
claim at all three sites (§5.1.1, banner item 2, §8.1 fact 2, §4.10)**, restates the true and weaker
claim §5.1's heading already carried, adds the **positive control and required RED demonstration**
§5.2's specification was missing (`A2-19` F2), applies `A2-19`'s **adjudication on the P-6/P-7
precondition split** (§5.3), and corrects the **one wrong citation** in 64 (§2.2 B-4, "three
columns" → **two**). It additionally corrects three claims that were **true when revision 2 was
written and have since gone stale** because the harness moved under them — the `I-3`/`I-4` guard now
exists (§4.4.1), the context boundary is now enforced (§8.2), and `A2-20` has closed the admission
hole. **What `A2-19` CONFIRMED and revision 3 does not disturb:** all 47 Fineract citations hit at
their exact lines; §5.1's five legs; §5.4's retraction and both its measurements; §8.3's
contradict-at-the-point-of-claim technique; and P-8's independence of P-1…P-5.

**What survived the rejection, so that it is not re-litigated.** A2-14 opened over thirty source
and capture citations and found **every `[VERIFIED]` claim traced to real source at the exact
cited line** — none overstated, none mis-cited, none fabricated. G-9 was applied as closed; G-10
was recorded and explicitly left undecided, so no gate was crossed; default-deny is genuinely
inherited; no float is admitted anywhere Gerege owns the number. The rejection was about
inferences drawn on top of that base, and this revision changes those inferences and only those.
Claims carried forward unchanged from revision 1 keep revision 1's citation tier; claims this
task re-opened are marked as such.

**No PIN digest appears in this document**, and §1.1 explains why one *cannot* appear yet: unlike
DEC-1, this ADR is not written against an existing frozen Go file. **This is load-bearing for §5.3's
P-7**, whose revision-2 premise §1.1 contradicts — see the adjudication in §5.3.

**Terminology.** In this document "**the reference oracle**" always means the **Fineract
reference implementation** at the pinned commit — the implementation this program grades Go
output against (test-oracle sense). It never means **Oracle Database**, which is a prohibited
product in this program. PostgreSQL is the only permitted database, for the reference oracle,
the Go module, capture and shadow runs alike.

**Citation convention.** Every Fineract `file:line` citation is to the pinned checkout
`/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED by `A2-16`:
`git rev-parse HEAD` in that checkout returns exactly that commit]. Every capture citation is to a
committed file under `.softhouse/capture/tierA-a2/`. Every material claim carries
**`[VERIFIED: …]`** — meaning the authoring task opened the source line or the capture bytes — or
**`[UNVERIFIED]`**. A claim taken on another worker's report and not re-opened is marked
**`[VERIFIED BY <task>, NOT RE-OPENED HERE]`**, which is a third and weaker thing, and the
distinction is deliberate.

**Reading "this task" across FOUR revisions.** Unqualified *"this task"* means **`A2-13`**, the
author of revision 1, and its verifications stand — an independent review re-opened over thirty of
them and every one traced to real source at the exact cited line. Where **`A2-16`** re-opened a
claim, corrected one, or measured something new, the citation says so explicitly: **`[VERIFIED by
this task]` inside material revision 2 added**, or **`[RE-VERIFIED by A2-16]`**, or **`[MEASURED by
this task]`** for a harness run this task actually performed rather than reasoned about. Every
`[MEASURED]` in this document is `A2-16`'s and was produced by running the real conformance binary
against a **temporary copy** of the vector store; **no file under `.softhouse/vectors/` or `nexus/`
was modified by revision 2.**

> **⚠ HOW TO READ A `[VERIFIED by this task]` MARK ON A HARNESS CITATION AFTER REVISION 4.** The
> **fact** is attributed to the task that first opened it — `A2-13`, `A2-16` or `A2-21` — and that
> attribution is unchanged. **The LINE NUMBER beside it is `A2-28`'s**, re-taken by content at commit
> `2e97162`, because ~18 of the ranges revision 3 carried no longer resolved (`A2-25` F-6; drift up
> to +325 lines, every stale citation substantively **true**). So a harness `file:line` in this
> document means *"`A2-28` opened this construct at this line at `2e97162`; the earlier task named
> in the mark is who established the fact."* **Fineract citations are NOT of this kind** — they are
> pinned to `426a23544e8426a38ae43ae404670a0a7e85b9eb` and were not re-taken by `A2-28`; they carry
> `A2-19`'s and `A2-25`'s audits (47/47 exact, and B-4 re-opened line by line).

**Revision 3's own marks are `[VERIFIED by this task]` / `[MEASURED by this task]` written by
`A2-21`**, which re-opened: §1.1 (before acting on the P-7 adjudication), §2.2 B-4 at the pinned
Fineract checkout, `admit.go`'s context checks and `A2-20`'s allowlist, `conformance.sh`'s
`run_guards` and `guard_ledger_invariants`, `capability.go`'s coverage loop, `grade.go`'s
remediation text, `capabilities.json` and `PIN.json`'s schema ids, and the full unfiltered
conformance run. **`A2-21` is an ANALYST and wrote no code: its diff touches this file and its
handoff, and nothing else.** The vector store was unchanged at revision 3 —
`git rev-parse HEAD:.softhouse/vectors` = `ce821c638724237652b6b29627148d34b72fab3b`, the canonical
recipe (**P-61**; never `find | shasum | shasum`, which hashes path text and moves with the caller's
cwd).

**Revision 4's own marks are `[VERIFIED by A2-28]` / `[MEASURED by A2-28 at commit 2e97162]`.**
`A2-28` re-opened, at commit **`2e97162`**: **every** harness citation in this document, by content
rather than by line, and re-took the ~18 stale ranges `A2-25`'s F-6 tabulated (§4.4.1's guard
transcript included, whose census figures had moved twice); `.softhouse/guards/ledgerguard/main.go`'s
seven declared detection classes and its three `NIL-COVERAGE` emission sites; `capability.go`'s
`CounterfactualCoverage` and its `RefusalFor` filter; `coverage_refusal_test.go`'s three refusal
tests, run; the vector store's file census; **§5.2 requirement 6's BEFORE, by authoring the exact
vector the requirement names and running it** (both halves of `A2-25`'s F-3 reproduced); and §5.4's
three experiments, re-run. **`A2-28` is an ANALYST and wrote no code: its diff touches this file and
its handoff, and nothing else.** Every experiment ran against a **temporary copy** of the store in
`/tmp`; the committed store is unchanged and its canonical recipe still returns
`git rev-parse HEAD:.softhouse/vectors` = **`73c3ea7b43dd75f04884072719a87fc8e1d255c1`** at
`2e97162` (**P-61**). `gofmt -l nexus/` reports exactly `contract.go` — the expected **G-3
CLOSED-OPTION-A** state.

**Harness `file:line` citations drift, and every revision has had to re-take them.**
Revision 3 re-took the ones it touched, but **inherited ~18 stale ranges from revision 2** and
disclosed the class only as *"may be stale by a few lines"*; `A2-25`'s F-6 established that the
drift reached **+325 lines** at one site and that **every stale citation was substantively TRUE** —
a **freshness** defect, not a fabrication, but one a ratifier cannot check. Revision 4 re-took all
of them at `2e97162` and records the running drift: `run_guards` 843 → 938 → 1154 → **1189**;
`guard_ledger_invariants` 1117 → **1152**; `capability.go`'s coverage loop 243 → 246 → **262**;
`admit.go`'s class switch ~130 → **159**; `conformance.sh`'s `-context` append 894 → **1254**.
**Drift is disclosed, never silently patched over.** Several
harness line numbers moved between revision 1 and revision 2 as unrelated tasks landed — for example
the `-context` flag append and `run_guards`, both cited by revision 1's reviewer at line numbers that
no longer hold. **Revision 4's position, replacing revision 3's "may be stale by a few lines":
every harness citation in this document was re-taken at `2e97162` and resolves there. It will go
stale again the next time anything under `nexus/` or `.softhouse/conformance.sh` moves, and a
ratifier must re-take them at the moment of ratification.**

**Nothing in this document is asserted from memory.** §9 enumerates every `[UNVERIFIED]` and
why it could not be closed. Per the project honesty rule, an honest negative outranks a
plausible positive: a DEC-2 with twenty honest gaps is worth more than one that reads complete
and is wrong in three places.

---

## 0. Why this document exists

`.softhouse/vectors/` contains exactly two context directories, `loanschedule/` and `_selftest/`
[VERIFIED: `ls .softhouse/vectors/`, by this task]. Task **A2-8** merged the port of the GL
account model, product-to-account mapping resolution and financial activity accounts to `main`,
and **not one parity vector grades it**. The conformance run reports `PASS 46`; all 46 are
`loanschedule`'s [MEASURED by `A2-28` at commit `2e97162`; the "not one grades the GL package" half
is VERIFIED BY A2-8, NOT RE-OPENED HERE — A2-8's own handoff says so plainly:
*"the harness does not grade this package at all"*].

`.softhouse/vectors/README.md` shows the store was designed for exactly this: its layout is
`<context>/ — one directory per bounded context`, and `conformance.sh <context>` already
filters to one [VERIFIED: README.md § *Layout*, read by this task]. The second context was
simply never added.

**A vector cannot be promoted against a contract that does not exist.** Admissibility, the
graded domain, and what a refusal *means* are all defined by a frozen contract. DEC-2 is that
contract for the GL/accounting bounded context, so that `A2-15` has something to build a grader
against.

---

## 1. What ratification would mean, and what changing it later would mean

**Ratifying this ADR is a decision the driver may take** once it passes an independent review
with no rejection-grade findings (standing policy **P-2**,
`.softhouse/gates-proposed-answers.md`). Buyan may reverse it at any time before cutover.

**Amending a RATIFIED DEC-n is not an agent's call.** Once ratified, changing any normative
predicate, refusal, pin or graded-domain statement here requires raising a gate. Three reasons,
the same three DEC-1 §1 gives, each with teeth in this context specifically:

1. **The contract is the strangler boundary.** Every call site in Gerege Nexus that needs a GL
   account resolved depends on this shape and on nothing else. Both implementations are written
   to it; a change is a simultaneous change to two implementations and every caller.
2. **The contract is the golden-vector encoding.** A `ledger` vector is a resolution request and
   the oracle-produced answer — an account, or an oracle-faithful refusal. A field added,
   removed, renamed or retyped invalidates the corpus.
3. **The contract is what a regulator is shown.** The parity argument for FRC / parallel-run
   sign-off is "these two implementations answer the same question identically", auditable only
   if the question stopped moving. For a **ledger** this is sharper than for a schedule: a wrong
   GL account is a misstatement of the financial position, not a rounding difference.

**Widening the graded domain (§4.2) is NOT an amendment.** It is behaviour, not shape. This is
DEC-1's distinction and DEC-2 adopts it unchanged.

**Unchanged and untouched by ratification:** cutover from Fineract to Go, regulatory /
parallel-run sign-off, and licence facts remain hard `user` gates. A conformance PASS on the
`ledger` context would mean "matches the reference oracle on captured vectors, inside the graded
domain". It would never mean "safe to cut over".

### 1.1 This ADR does not create or freeze a Go file, and could not

DEC-1 was written **against an existing file** — `nexus/internal/apps/loanschedule/contract/contract.go`
— and its ratification froze that file's doc comments alongside the ADR text
[VERIFIED: DEC-1 §1 and its ratification block, read by this task].

**There is no counterpart file for this context.** The package `nexus/internal/apps/ledger` that
A2-8 merged is the **implementation**: it carries in-memory stores, resolvers and repositories
[VERIFIED: `nexus/internal/apps/ledger/{mapping,resolve,financialactivity}.go` declare
`InMemoryMappingStore`, `Resolver` and `InMemoryFinancialActivityStore`; read by this task]. An
implementation is not a contract, and freezing one as a contract would freeze its storage
choices, which is precisely the mistake the strangler pattern exists to avoid.

**Therefore, and this is a decision this draft records rather than a gap it leaves:**

- Ratification of DEC-2 would freeze **the normative text of this document only**.
- The Go expression of it belongs in a new package — recommended name
  `nexus/internal/apps/ledger/contract` — authored by a **separate task**, reviewed, and pinned
  by a **later revision** of this document that adds the digest. This ADR deliberately writes
  no Go.
- Until that file exists, `A2-15`'s grader must read its admissibility rules from **this
  document and from the capability registry** (§4.10), not from a Go type.

The alternative rejected: writing the Go surface into this ADR as a fenced block and calling it
frozen. Rejected because a shape nobody has compiled, tested or reviewed is not a boundary; it
is a proposal wearing a boundary's clothes, and DEC-1's own history — twelve revisions, nine
review rounds — is the argument.

---

## 2. Context

### 2.1 What this context is, in the oracle

The bounded context is **A2**: the GL account model, `acc_product_mapping` resolution, and
financial activity accounts. Its Fineract behaviour was extracted by `A2-1` (corrected by
`A2-6`), independently reviewed by `A2-2` (verdict MICRO-FIX, every money-critical limb
CONFIRMED), captured by `A2-3` and `A2-7`, ported by `A2-8`, reviewed by `A2-9` (verdict
MICRO-FIX), and micro-fixed by `A2-12`.

The behavioural facts DEC-2 must accommodate:

- **Resolution is four steps.** For a loan product:
  **STEP 0** a pre-emptive *financial-activity* branch when the placeholder id is one of
  `{100, 101, 102, 103, 200, 201, 300}`, which ignores the product entirely
  [VERIFIED: `AccountingProcessorHelper.java:1187` calls `isOrganizationAccount`, defined at
  `:1340-1342` as `FinancialActivity.fromInt(accountMappingTypeId) != null`; the seven values at
  `AccountingConstants.java:439-445` — both spans opened by this task];
  **STEP 1** the *core row* keyed on `(product_id, product_type, financial_account_type)` with
  **all six** discriminator columns NULL [VERIFIED by this task:
  `ProductToGLAccountMappingRepository.java`'s `findCoreProductToFinAccountMapping` JPQL names
  `paymentType`, `charge`, `chargeOffReason`, `writeOffReason`,
  `capitalizedIncomeClassification`, `buydownFeeClassification`, all `is NULL` — six, counted];
  **STEP 2** a *payment-type override*, applied **only** when the placeholder is
  `CashAccountsForLoan.FUND_SOURCE` = 1 [VERIFIED: `AccountingProcessorHelper.java:1199-1206`;
  `AccountingConstants.java:39`];
  **STEP 3** the miss.
- **Charges are a separate entry point** with different precedence per family, and savings
  uniquely lets the `m_charge` row's own GL account outrank every mapping
  [VERIFIED BY A2-1 AND RE-DERIVED BY A2-2, NOT RE-OPENED HERE:
  `AccountingProcessorHelper.java:1218-1238` (loan), `:1240-1269` (savings, `:1255-1258` the
  charge's own account), `:1322-1338` (shares)].
- **The miss is typed on two paths and an NPE on five.** Loan raises
  `ProductToGLAccountMappingNotFoundException` [VERIFIED: `:1208-1211`, opened by this task];
  working-capital-loan likewise [VERIFIED: `:1024-1027`, opened by this task]. Savings, shares
  and all three charge paths dereference the null [VERIFIED by this task at `:1337`, a bare
  `return accountMapping.getGlAccount();` with no preceding null check; the other four cited by
  A2-1 and confirmed by A2-2].
- **The two loan placeholder enums collide.** `CashAccountsForLoan` has 23 members and
  `AccrualAccountsForLoan` 25; they **disagree in name at codes 22, 24 and 25**, cash has 26
  which accrual lacks, and accrual has 7/8/9 which cash lacks
  [VERIFIED by this task, both enums read in full: `AccountingConstants.java:37-62` and
  `:95-122`. 22 = `CLASSIFICATION_INCOME` / `INCOME_FROM_CAPITALIZATION`;
  24 = `INCOME_FROM_DISCOUNT_FEE` / `BUY_DOWN_EXPENSE`;
  25 = `FEES_RECEIVABLE` / `INCOME_FROM_BUY_DOWN`]. **A stored `financial_account_type` is
  therefore not decidable from the row alone** — the product's accounting rule is required.
- **`PortfolioProductType.fromInt` permutes 3/4/5** relative to `getValue()`
  [VERIFIED BY A2-1, RE-DERIVED INDEPENDENTLY BY A2-2 AND AGAIN BY A2-8, NOT RE-OPENED HERE:
  `PortfolioProductType.java:26-31` vs `:51-59`]. Writes use `getValue()`, so storage is
  self-consistent; a port that transcribes `fromInt` inherits the bug.
- **Nothing in the slice is persisted by `ordinal()`**, and no `@Enumerated` appears in the
  scope paths [VERIFIED BY A2-2 with positive controls in both directions, NOT RE-OPENED HERE].
- **`acc_gl_journal_entry` carries no classification column.** [VERIFIED by this task:
  `JournalEntry.java` has **zero** case-insensitive occurrences of `classification`, and its
  `@Column` list is `currency_code`, `transaction_id`, the four `*_transaction_id`, `reversed`,
  `manual_entry`, `entry_date`, `type_enum`, `amount`, `description`, `entity_type_enum`,
  `entity_id`, `ref_num`, `submitted_on_date` — `account_id` is the only route to a
  classification.]
- **Fineract ships the `acc_gl_account` table and zero rows** — see §4.5 (G-9).
- **Duplicate mapping rows are physically possible**: the JPA `@UniqueConstraint(name =
  "financial_action")` has zero occurrences in the Liquibase changelog set
  [VERIFIED BY A2-1, RE-GREPPED WITH A POSITIVE CONTROL BY A2-2 AND AGAIN BY A2-9, NOT RE-OPENED
  HERE], and a duplicate is **observed** on product 27 [VERIFIED by this task from
  `out/A2-150-db-final-state.txt`: `(27, 1, 1, payment_type 1) → n = 2, gl_account_ids {16,2}`].
- **A parent account's classification need not match its child's.** [VERIFIED by this task from
  `A2-150`: GL 21 `Liability Under Asset`, `classification_enum = 2`, `parent_id = 1`, whose
  parent GL 1 `Assets` is `classification_enum = 1`.]

### 2.2 The fact that shapes this contract: the resolver's signature is three scalars, and it sees nothing else

This section is DEC-2's counterpart to DEC-1 §2.2, and it is the reason the rest of the document
is shaped the way it is.

The oracle's resolution entry point for a loan product is:

```
GLAccount getLinkedGLAccountForLoanProduct(Long loanProductId, int accountMappingTypeId, Long paymentTypeId)
```

[VERIFIED by this task: `AccountingProcessorHelper.java:1185-1216`, opened and read in full.]

**Three scalars in, one account out.** Five things that signature and body structurally cannot
see, each demonstrated from source rather than asserted:

| # | What the seam cannot see | Mechanism, verified |
|---|---|---|
| **B-1** | **The product's accounting rule.** | Not a parameter. Consequence at `:1210`: the miss message is rendered by `AccrualAccountsForLoan.fromInt(accountMappingTypeId).toString()` **always**, even for a cash product; the working-capital path renders through `CashAccountsForLoan` **always** at `:1026` [VERIFIED, both lines opened by this task]. At codes **22, 24, 25** the two enums render *different words*, so the oracle emits the wrong family's word for one of the two rules. At code **26** (cash-only) and **7/8/9** (accrual-only) the rendering enum's `fromInt` returns null and `.toString()` throws an NPE instead of producing a refusal. |
| **B-2** | **The resolved account's classification, usage or `disabled` flag.** | The body ends `glAccount = accountMapping.getGlAccount();` at `:1213` and `return glAccount;` at `:1215`, with no reference to any of the three [VERIFIED by this task, the whole method read]. **This is the mechanism of G-10** (§4.6): a retype is invisible to resolution because resolution never looks. A2-9 re-derived the same for all four resolvers and concluded resolution gradings are immune to the retyped chart [VERIFIED BY A2-9, NOT RE-OPENED HERE]. |
| **B-3** | **A charge.** | The charge resolvers are `private` and every caller is inside `AccountingProcessorHelper` itself [VERIFIED by this task: `grep -rn` over the checkout excluding `/build/` returns, for `getLinkedGLAccountForLoanCharges`, only `:402`, `:404`, `:764`, `:1430` — all in that file — plus three comment mentions in an integration test]. **So an in-process seam bound to the public method cannot grade a charge**, by construction. This is structurally the same fact as DEC-1's `loanCharges = null` at `ProgressiveLoanScheduleGenerator.java:83`, reached by a different mechanism: Java visibility rather than a hard-wired null. |
| **B-4** | **The office.** | `acc_gl_financial_activity_account` is tenant-global — **two** columns plus id, no office dimension [**CORRECTED in revision 3, and RE-OPENED at the pinned checkout**: revision 2 said *"three columns plus id"*, carried from A2-1/A2-2 in the document's weakest citation tier. It is **two**. `fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml:98-110` is `changeSet id="4"`, whose `createTable` declares exactly `id` (`:100-102`, autoincrement primary key), `gl_account_id` (`:103-105`) and `financial_activity_type` (`:106-108`) and nothing else [VERIFIED by this task, file opened at `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`, re-confirmed by `git rev-parse HEAD`]. **The load-bearing claim is unaffected and is TRUE: there is no office dimension** — the adjacent `acc_gl_journal_entry` table does declare `office_id` (`:119-121`, in `changeSet id="5"`) and this one does not. The miscount was refuted from inside the same sentence, whose own corroboration lists three names of which one is `id` — and it is the ONE wrong claim an independent citation audit found in 64, in the tier the document itself flags as weakest, which is evidence the tier convention works. Corroborated by this task from `A2-150`, whose dump of that table projects `id, financial_activity_type, gl_account_id` and joins the account]. |
| **B-5** | **Any amount, and any currency.** | Neither is a parameter and neither appears in the body [VERIFIED by this task, the whole method read]. **No money flows through THIS METHOD at all.** Scope, and revision 2 states it in the row rather than leaving it to be inferred: this is a fact about `getLinkedGLAccountForLoanProduct`, which is the analogue of the **`ledger_inprocess_resolver`** seam — **the one seam `G-01` refuses** (§4.1, §4.2). It is **not** a fact about the contract, which is anchored on three other seams, two of which carry money. |

**B-5's scope, corrected in revision 2 — this is finding R-3, and it is the same defect class as
the still-OPEN `G-5` on DEC-1.**

Revision 1 read B-5 off the in-process resolver and then restated it, in §2.2, §3.2 and §5, as
*"the contract carries no amount"*. That is the G-5 shape exactly: a **prose** claim contradicted
by the **enumerated list** it sits beside, with the enumerated list being the part anything
mechanical would follow. `G-07` and `G-08` (§4.2) are predicates about a currency code and about
an amount's wire text; §4.4 grades `I-1`/`I-2` in `int64` minor units. Either the prose was false
or those two predicates were true-of-nothing (**P-35**). Shipping that unresolved would have put a
second ratified ADR into the same contradiction that is currently a hard `user` gate on the first.

**The decision: KEEP THE MONEY, NARROW THE PROSE.** The measured data settles which half was
false, and it is the prose:

- `A2-235` holds exactly eight `"amount":` occurrences, each a bare JSON number: `1200000.000000`
  ×2, `200000.000000` ×2, `1000000.000000` ×2, `50000.000000` ×2 [VERIFIED by this task, regex over
  the raw bytes]. In minor units that is 120,000,000 + 20,000,000 + 100,000,000 + 5,000,000 =
  **245,000,000** per side.
- `A2-150`'s `acc_gl_journal_entry` dump projects **both** `amount` and `currency_code`: six rows,
  every one `1200000.000000` and `MNT` [VERIFIED by this task, lines 65-70 of
  `A2-150-db-final-state.txt`].

So money is present on `ledger_rest_posting` **and** on `ledger_db_readback`, and the alternative
resolution — striking `G-07`/`G-08` and demoting `I-1`/`I-2` — would have thrown away the only two
ledger invariants anything in this program could ever grade, in order to preserve a tidy sentence.
That is the wrong trade.

**The corrected statements, which are what the rest of this document now says:**

- **The `ledger` contract DOES carry an amount and a currency, on the seams that observe a journal
  entry.** `G-07` and `G-08` are live predicates, and §4.2 now scopes them to the vectors they
  actually bind.
- **The RESOLUTION FUNCTION does not.** `getLinkedGLAccountForLoanProduct` takes three scalars and
  returns an account; a vector that asserts only a resolution outcome asserts no money, and
  `G-07`/`G-08` are inert on it — inert by scope, which is a different thing from vacuous.
- **DEC-2's contract is therefore two things, and revision 1 named only the first**: an
  account-selecting function, *and* a money-bearing observation of what the posting engine wrote
  through it. Money is *produced* by slice **A1**; it is *observed* here, and observing it is
  exactly what makes `I-1` and `I-2` statable at all.

**What this does NOT rescue.** Being statable is not being graded. §5 establishes that no vector
asserting a money cell — or any other `ledger` cell — is currently expressible at all. `I-1` and
`I-2` are gradeable **from the data in hand and from nothing else that is missing except the
machinery**; they are not gradeable **today**. §4.4 now says that in those words.

### 2.3 What the REST read-back cannot see

The second blind spot, and it is at the **contract boundary** rather than inside the JVM.

`GET /loanproducts/{id}` returns, for each mapped slot, an object of exactly
`{id, name, glCode}` — **no `type`, no `usage`, no `disabled`, no `manualEntriesAllowed`.**

[VERIFIED by this task, by decoding the raw bytes of
`.softhouse/capture/tierA-a2/out/A2-211-read-product-nine-mandatory.json` (7,489 bytes) with
`json.load(..., parse_float=decimal.Decimal)`: `accountingMappings` holds **9** keys, and every
one of the nine values has key set exactly `['glCode', 'id', 'name']`. The literal string
`null` occurs **0** times in the whole file, and `paymentChannelToFundSourceMappings` is
**absent**, not null.]

Two consequences DEC-2 must carry:

1. **An unset mapping field is ABSENT from the read — scalar and collection alike — and nothing
   is ever `null`.** A Go port that emits `null` keys the oracle omits is a contract-boundary
   parity defect. (A2-7's handoff originally asserted the opposite for collection fields; that
   sentence rested on a **fabricated capture excerpt**, caught by the reviewer A2-11, struck by
   the driver, and independently re-verified by A2-8 and again by this task. It is recorded here
   because the false rule, not the true one, is what a next contributor would have checked a new
   write site against — the P-46 lesson.)
2. **The product read-back structurally cannot reveal a retyped GL account.** That is G-10
   (§4.6). Note the exact scope: **one call cannot reveal it; two calls can** —
   `GET /glaccounts/{id}` returns the classification plainly. A port that resolves
   classification through a second `/glaccounts/{id}` read is not blind to this; a port that
   trusts the product read alone is [A2-11's refinement; VERIFIED BY A2-11 AND BY THE DRIVER,
   NOT RE-OPENED HERE].

---

## 3. Decision

Adopt this document as the frozen adapter contract for the **`ledger`** bounded context — the GL
account model, product-to-account mapping resolution, and financial activity accounts — and
adopt `ledger` as the second `<context>` directory in `.softhouse/vectors/`.

### 3.1 Two domains, and why the distinction is the decision

| | |
|---|---|
| **Contract domain** | Every value the contract admits as well formed. **Frozen by ratification.** |
| **Graded domain** | The strict subset for which a capture exists that can tell a correct implementation from an incorrect one. **Grows as vectors land, with no amendment.** |

A value inside the contract domain but outside the graded domain is **refused with
`ErrNoDiscriminatingVector`** — never silently accepted, never silently dropped. This is
DEC-1's standing G-1 disposition and DEC-2 adopts it verbatim: *expose the input, specify the
oracle's semantics normatively, and refuse rather than guess.* An explicit refusal converts a
silent wrong answer into a loud missing feature.

### 3.2 The structural result — and it is WEAKER than DEC-1's, deliberately

DEC-1 §3.2 can say: *"inside the graded domain, the seam's blind spot is empty"*, because the
three components its seam fails to deliver are exactly the three it pins to inert values.

**DEC-2 cannot say that, and this draft refuses to imply it.**

Of the five blind spots in §2.2:

- **B-3 (charges)** and **B-4 (office)** are **excluded from the contract domain** — no charge
  entry point and no office dimension is admitted (§4.2). Pinned, in DEC-1's sense.
- **B-5 (money)** is **not a blind spot; it is a scope statement, and revision 2 narrows it.** The
  in-process resolver is money-free — but that resolver is `ledger_inprocess_resolver`, the seam
  `G-01` refuses, so its money-freeness is not a property of this contract. **The contract carries
  an amount and a currency** on `ledger_rest_posting` and on any `ledger_db_readback` vector that
  reads `acc_gl_journal_entry`, both of which are admitted seams and both of which are observed
  carrying MNT amounts (§2.2, R-3). `G-07` and `G-08` bind exactly there.
- **B-1 (accounting rule)** is **live and not pinnable.** The contract *does* carry the
  accounting rule, because the caller must supply it to choose the placeholder family (§4.8) —
  but the oracle's own renderer ignores it, so a faithful port must reproduce a message the
  oracle derives from information the oracle did not have. §4.9 R-1 states that normatively
  rather than leaving it to be discovered.
- **B-2 (classification / usage / disabled)** is **live and not pinnable.** It is exactly G-10
  (§4.6), it is OPEN, and DEC-2 records it as a **hazard constraining admissibility**, not as a
  pin.

**So DEC-2's honest structural statement is:** *every blind spot is enumerated; two are excluded
from the contract domain; one is a non-issue; and the remaining two are live, are named, and
constrain which vectors may be promoted rather than which requests are admissible.* A future
reader who finds this weaker than DEC-1's should read it as accurate rather than as unfinished:
the GL seam genuinely is less tractable than the schedule seam, and saying so is the point.

### 3.3 Design rules applied

A field is in the contract if and only if:

1. it changes which GL account is selected, or which refusal is returned, **and**
2. it is a property of the thing being resolved — not of the implementation resolving it, not
   of a neighbouring bounded context, **and**
3. both implementations consume it, **and**
4. it cannot be recomputed from the other fields.

Two argued exceptions to (1):

- **`AccountingRule` is carried although the oracle's renderer ignores it** (B-1). Without it the
  contract cannot name a slot unambiguously (§4.8), and a bare integer placeholder is precisely
  the trap A2-8 modelled five separate Go types to prevent.
- **The resolved account's `Classification` is carried on the ANSWER although resolution does
  not read it** (B-2). Reason: `acc_gl_journal_entry` has no classification column (§2.1), so a
  retype retroactively re-renders every entry ever posted to that account. Carrying the
  classification on the resolved account is the only way the port can record what it was at
  posting time. A2-8 already exposes this as `PostedAccountSnapshot` [VERIFIED: declared at
  `nexus/internal/apps/ledger/glaccount.go:324`, read by this task].

Where evolution is foreseeable, prefer **widening a value domain over changing a shape** — an
enum gains a member, a slot family gains a code. Both are still gated changes; neither
invalidates a vector's field set.

---

## 4. The load-bearing decisions

### 4.1 The seams, and the capability method applied to them

DEC-1's corpus has one dominant seam (`path_a_embeddable`) plus two others. The `ledger` context
has **no in-process seam today at all** — every A2 capture was taken through the running server
or through PostgreSQL. Named, so that a vector must declare which one produced it:

| seam id | what it is | exists today? |
|---|---|---|
| `ledger_rest_admin` | The running Fineract server over REST, administrative surface: `POST/PUT/DELETE /glaccounts`, `/financialactivityaccounts`, `POST/PUT /loanproducts`, and the `GET` read-backs. Against PostgreSQL, tenant `gerege`. | **YES** — the bulk of the `A2-*` capture set. |
| `ledger_rest_posting` | The running server over REST, posting surface: `POST /loans/{id}/transactions?command=…`, observed through the journal entries it writes. The only seam that can grade resolution **at posting time**. | **YES** — `A2-084`, `A2-085`, `A2-086`, `A2-091b`, `A2-220`…`A2-235`. |
| `ledger_db_readback` | A read-only `SELECT` against PostgreSQL: `acc_gl_account`, `acc_gl_financial_activity_account`, `acc_product_mapping`, `acc_gl_journal_entry`. | **YES** — `A2-019`, `A2-072`, `A2-150`. |
| `ledger_inprocess_resolver` | An in-process seam binding `AccountingProcessorHelper.getLinkedGLAccountForLoanProduct` directly — the analogue of DEC-1's Path A. | **NO — does not exist.** Reserved so a future capture task can declare it. Every capability on it is **ABSENT**, which refuses. |
| `none` | No capture. For contract-refusal vectors whose expectation is derived from this document's own normative text, and for hand-authored self-test fixtures. | n/a |

**`ledger_db_readback` carries a hazard the other two do not, and it has already bitten.** A psql
dump is a *snapshot*, and two committed snapshots of the same tenant disagree: `A2-072` reports
GL account 2 with `classification_enum = 1` (ASSET) and `A2-150` reports it as `4` (INCOME)
[VERIFIED by this task from `A2-150`'s `acc_gl_account` dump, row
`| 2 | 1 | 10100 | Fund Source | 4 | 1 |`; the `A2-072` value is VERIFIED BY A2-8 AND RE-MEASURED
BY A2-9, NOT RE-OPENED HERE]. This cost A2-8 one failing test before it was diagnosed.

**Normative consequence:** a `ledger` vector sourced from `ledger_db_readback` must name the dump
file **and** carry that dump's `captured-at` timestamp, and **a vector may not join columns
across two dumps.** This is P-32 (a snapshot read as the current state) made mechanical.

### 4.2 The graded domain, predicate by predicate

Each predicate below is checkable in code without asking the oracle. A request satisfying **all**
of them is inside the graded domain. Any request that is well formed and admissible but fails at
least one is **refused with `ErrNoDiscriminatingVector`**.

```
G-01  Seam                     ∈ {ledger_rest_admin, ledger_rest_posting, ledger_db_readback}
G-02  ProductType              == LOAN                              (stored value 1)
G-03  AccountingRule           ∈ {CASH_BASED, ACCRUAL_PERIODIC}     (stored 2, 3)
G-04  Entry                    == LOAN_PRODUCT_ACCOUNT
G-05  SlotFamily               == CashLoanSlot     when AccountingRule == CASH_BASED
                                == AccrualLoanSlot  when AccountingRule == ACCRUAL_PERIODIC
G-06  PaymentTypeID            != nil    whenever SlotCode == 1 (FUND_SOURCE)
G-07  Currency.Code            == "MNT"  and  Currency.MinorUnitDigits == 2
                               — binds ONLY a vector that asserts a MONEY CELL (see below)
G-08  every amount's wire text is EXACT at MinorUnitDigits  (no non-zero digit beyond)
                               — binds ONLY a vector that asserts a MONEY CELL (see below)
G-09  GLAccount.Classification ∈ {ASSET, LIABILITY, EQUITY, INCOME, EXPENSE}   (1..5)
G-10  GLAccount.Usage          ∈ {DETAIL, HEADER}                              (1, 2)
G-11  for a POSTING-TIME grading only:  SlotCode ∈ {1, 2, 6, 12}
```

**The evidence for each, and the reason the complement is refused:**

| # | Graded because | Complement refused because |
|---|---|---|
| **G-01** | These three seams produced the whole A2 corpus. | `ledger_inprocess_resolver` does not exist; **ABSENT refuses** (default-deny, §4.10). |
| **G-02** | Products 22, 23, 24, 27, 28 are all `product_type = 1` [VERIFIED by this task from `A2-150`'s per-product mapping-count table — five rows, every `product_type` = 1]; product 46 likewise [VERIFIED BY A2-8 from `A2-072`, NOT RE-OPENED HERE]. | The tenant has **no** savings, share or working-capital-loan product [VERIFIED BY A2-8's `[UNVERIFIED]` items 3 and 4, NOT RE-OPENED HERE], so nothing in those resolvers is graded against the oracle at all. `PROVISIONING`(3) and `CLIENT`(5) likewise. |
| **G-03** | Cash observed on products 22, 24, 27, 46; accrual-periodic observed on 28 [VERIFIED by this task for 46: `A2-211`'s `accountingRule` decodes to `{"id":2,"code":"accountingRuleType.cash","value":"CASH BASED"}`; for 28, VERIFIED BY A2-7 from `A2-213`, NOT RE-OPENED HERE]. | `NONE`(1) has no mappings at all. **`ACCRUAL_UPFRONT`(4) is refused for one reason only: it is UNCAPTURED.** Revision 2 corrects revision 1's second reason, which was wrong — see the `ACCRUAL_UPFRONT` note immediately below and §9 item 10, now CLOSED. |
| **G-04** | Loan-product resolution is the only entry point exercised end to end. | Charge resolution: **B-3**, and no charge exists in the tenant [A2-8 item 5]. Reason/classification lookup: no such row exists [item 6]. STEP 0's *data* is graded (§4.5) but its *precedence at posting* is not [item 9]. |
| **G-05** | Both families are exercised: cash by 22/24/27/46, accrual by 28's thirteen slots including the three receivables. | A bare integer cannot select a family (§2.1). Admitting one would re-open the collision at 22/24/25. |
| **G-06** | The corpus's loan fund-source resolutions all carry a payment type: `A2-084` type 1 → GL 16, `A2-085` type 2 → GL 2 (falling back to the core row), `A2-086` type 1 → the duplicate refusal [VERIFIED BY A2-8, AND THE `A2-086` REQUEST BODY RE-CHECKED BY A2-9 AGAINST THE `.http` RECORD, NOT RE-OPENED HERE]. | **`PaymentTypeID == nil` on FUND_SOURCE is genuinely undecided.** The oracle issues the payment-type finder with a null argument and no null guard [VERIFIED by this task: `AccountingProcessorHelper.java:1199-1206` has no `paymentTypeId != null` conjunct, unlike the working-capital path at `:1015`]. Spring Data JPA conventionally renders a null bound to a derived-query equality as `IS NULL`, which would match the **core row**; the alternative reading matches nothing. **Neither reading is settled from the pinned checkout, and no capture separates them.** Refusing is the only defensible answer. §9 item 2. |
| **G-07** | Every journal entry in the corpus is MNT [VERIFIED by this task: `A2-150`'s journal-entry dump, all six rows `currency_code = MNT`]. | No other currency is captured. |
| **G-08** | See §4.3. | See §4.3 and §9 item 1. |
| **G-09 / G-10** | All five classifications and both usages appear: `A2-150`'s `acc_gl_account` is **21 rows** spanning `classification_enum ∈ {1,2,3,4,5}` and `account_usage ∈ {1,2}` [VERIFIED by this task, dump read row by row]. | Nothing outside 1..5 / 1..2 is a legal stored value; out-of-range is `ErrInvalidRequest`, which §4.9's precedence puts **ahead** of any graded-domain refusal. |
| **G-11** | **Only four slots were ever posted to.** `A2-150`'s six journal-entry rows touch GL 4 (`LOAN_PORTFOLIO`), GL 16 and GL 2 (`FUND_SOURCE`) and GL 1 (`LOAN_PORTFOLIO` on product 24, a **HEADER** account) [VERIFIED by this task from the dump]. `A2-235`'s eight legs add `LOSSES_WRITTEN_OFF`(6) and `INCOME_FROM_RECOVERY`(12) [VERIFIED BY A2-7's `analyze7.py` table, NOT RE-OPENED HERE]. | **4 of the 23 cash placeholders.** The other 19 are resolvable-from-stored-rows but **never posted**, and §4.7 forbids reading that absence as a statement about them. |

**`ACCRUAL_UPFRONT` on the LOAN side — closed in revision 2, and it changes G-03's reasoning.**

Revision 1 refused `ACCRUAL_UPFRONT`(4) partly on the ground that *"on the savings side its mapping
switch reaches `default: break` … so the loan side must not be assumed by symmetry"*, and filed the
loan side under §9 as unclosable. **The refusal to assume symmetry was right and the two sides do
differ. Filing it as unclosable was wrong: it is one grep, and this task took it.**

```java
            case ACCRUAL_UPFRONT:
                // Fall Through
            case ACCRUAL_PERIODIC:
```

[VERIFIED by this task at the pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`:
`fineract-provider/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/ProductToGLAccountMappingWritePlatformServiceImpl.java:149-151`,
inside `createLoanProductToGLAccountMapping` (declared `:61`, its switch at `:74`). The three lines
are quoted verbatim above.]

**On the loan side `ACCRUAL_UPFRONT` falls through and writes the FULL accrual mapping set.** On the
savings side it writes nothing. So a loan product created at `accountingRule = 4` persists rows
**byte-identical** to one created at `accountingRule = 3`.

**Two corrections of inherited wording, both verified in the pinned checkout by this task, and both
mattering because a reader will grep for the words:**

- The savings **helper** does not reach a `default:` label. It has `case ACCRUAL_UPFRONT: break;` —
  at **two** sites, `:192-193` and `:313-314` — and the file contains **zero** occurrences of
  `default:` [VERIFIED by this task:
  `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/service/SavingsProductToGLAccountMappingHelper.java`;
  `grep -c 'default:'` returns 0].
- The savings **create switch in the write service** *does* reach `default: break;`, at `:345-346`,
  because it has no `case ACCRUAL_UPFRONT` at all [VERIFIED by this task, same file as the loan
  fall-through: `createSavingProductToGLAccountMapping` declared `:311`, switch `:318`]. Revision 1's
  wording was true of this switch and false of the helper, and cited neither.

`AccountingRuleType` has exactly four members — `NONE(1)`, `CASH_BASED(2)`, `ACCRUAL_PERIODIC(3)`,
`ACCRUAL_UPFRONT(4)` [VERIFIED by this task: `AccountingRuleType.java`, the enum body read in full],
so the loan switch needs no `default:` and has none.

**What this does and does not do to G-03.** It removes the *source* uncertainty and leaves the
*evidential* one, which is the only ground the refusal now stands on: **no capture exists at
`accountingRule = 4`.** Admitting 4 on the strength of "the source says it writes the same rows"
would be admitting a value to the graded domain on a source reading rather than on an observation —
the precise move this program forbids. It stays out, with an honest reason, and **one capture
retires the refusal**: create one loan product at `accountingRule = 4`, read it back, and compare
the persisted mapping set against product 28's. That capture is named in §9 item 10 and is cheap.

**A hazard this uncovers, recorded because a port would reproduce it silently.** `fromInt` is a
`HashMap` lookup returning `null` for an unknown value [VERIFIED by this task,
`AccountingRuleType.java`, the `intToEnumMap` static block and `fromInt`], and both call sites
`switch` on the result directly — so an out-of-range `accountingRule` reaches `switch(null)` and
throws NPE rather than refusing. This is the same shape as §4.9's R-2 divergence and is governed by
it. `[UNVERIFIED]` — whether the API validator rejects out-of-range values before this point; this
task did not open the validator.

**Which vectors `G-07` and `G-08` actually bind — scoping added in revision 2 (R-3).**

`G-07` and `G-08` bind **a vector that asserts a money cell**, and only such a vector. They do not
bind by seam, and revision 2 says so explicitly because "by seam" is the natural guess and it is
wrong in both directions:

- A `ledger_rest_posting` vector asserting a journal entry's `amount` and `currency_code` — **bound.**
- A `ledger_db_readback` vector over `acc_gl_journal_entry` — **bound.** That dump projects `amount`
  and `currency_code` [VERIFIED by this task, `A2-150-db-final-state.txt:65-70`], so "db read-backs
  carry no money" would be false.
- A `ledger_db_readback` vector over `acc_product_mapping` or `acc_gl_account`, or a
  `ledger_rest_admin` vector asserting a resolution outcome or a refusal code — **not bound.** There
  is no amount in the assertion for `G-08` to be exact about.

**A predicate that is inert by scope is not a vacuous predicate (P-35).** The distinction is that a
vacuous predicate is one nothing could fail; these two can be failed, by any vector carrying a money
cell, and the admission rule must evaluate them on exactly those vectors. Whether the *evaluation*
is expressible is a separate question, answered no in §5.

**Two gradings that are NOT posting-time and must not be conflated with G-11:**

- **Resolution reproduced against the product read-back** — product 22 (10 slots), product 28 (13
  slots, accrual), product 46 (9 slots, rows built from the request bytes and compared with
  `A2-211`) [VERIFIED BY A2-8's grading table, NOT RE-OPENED HERE]. This grades the *mapping* and
  the *read shape*. It does not grade a posting.
- **Refusal parity** — `A2-224`, `A2-225`, `A2-092`, sixteen GL-account/mapping refusal codes and
  seventeen validation-family refusals [VERIFIED BY A2-8, AND THE COUNTS 16 AND 17 RE-COUNTED BY
  A2-9, NOT RE-OPENED HERE].

**Rates, principals and dates appear nowhere in this contract.** The `ledger` context's inputs
are enumerable — product ids, product types, placeholder codes, payment type ids,
classifications, usages — so unlike DEC-1 there is **no sampling argument to make**, and none is
made. What is *not* enumerated is the **chart**, which is data (§4.5) and outside the contract.

### 4.3 Money representation, and where the conversion boundary sits

**On the Go side of the boundary, absolutely: integer minor units, `int64`, everywhere.** No
float, no decimal-float, no `big.Float` — in any struct field, schema column, API field, fixture
or intermediate calculation. MNT = ISO 4217 numeric 496, minor unit 2; display 0 decimals
(`1,250,000₮`, postfix), store 2. This is a project non-negotiable, restated rather than derived.

**The oracle-facing wire is nothing like that, and it is measured rather than assumed:**

| where | what the oracle emits | verified |
|---|---|---|
| REST, journal entries | `"amount":1200000.000000` — a **bare JSON number containing a decimal point**, in **major** units, at scale **6** | [VERIFIED by this task: a regex over the raw bytes of `.softhouse/capture/tierA-a2/out/A2-235-je-after-recovery.json` returns eight `"amount":` occurrences, every one a bare number of the form `N.000000`, none quoted] |
| PostgreSQL | `acc_gl_journal_entry.amount` is `numeric(19,6)` | [VERIFIED by this task: `A2-150`'s `information_schema` projection reads `numeric_precision 19, numeric_scale 6`; and `JournalEntry.java:91` declares `@Column(name = "amount", scale = 6, precision = 19)`] |
| REST, product template | the **same-shaped** `"amount"` field also carries **non-money**: seven `chargeOptions` percentages read `1.234500` | [VERIFIED BY A2-8 AND RE-CENSUSED BY A2-12 over 147 files, NOT RE-OPENED HERE: 52 `amount` fields, 7 not exact at two decimals, all seven percentages in `A2-209c`] |

**Three normative consequences.**

1. **Read the literal characters, never a decoded number.** Go's `encoding/json` decodes a bare
   JSON number into `float64` by default, so an unguarded decode routes MNT through a binary
   float — the defect one remove from money code, sitting inside the grading rig. Every decoder
   on this boundary must preserve the token (`UseNumber()` or equivalent), and every monetary
   value must be converted from the literal token by exact integer/string arithmetic.
2. **Refuse residue; do not truncate and do not round.** Predicate **G-08**: a wire text carrying
   a non-zero digit beyond the currency's minor unit is **`ErrInvalidRequest`**, not a value.
   Truncating invents money in one direction, rounding in another, and either makes a parity
   comparison pass while the two systems disagree by a fraction that accumulates. A2-8 already
   implements exactly this refusal and states plainly that **no vector proves the truncation
   rule** [VERIFIED BY A2-8, NOT RE-OPENED HERE].
3. **A blanket "`amount` → minor units" rule is wrong on its face**, because the same
   `DECIMAL(19,6)`-shaped field carries percentages. The conversion must be applied per **field
   semantics**, never per field **name**.

**Where the conversion boundary sits.** DEC-2 needs, and states, only this: the conversion from
the oracle's major-unit decimal text to `int64` minor units happens **at the adapter edge** — the
HTTP/DB decode for a live adapter, and the capture-transcription step for a vector — and **never
deeper in**. Nothing behind that edge ever sees a decimal.

**T186 HAS RULED — revision 2 removes revision 1's live forward reference.** Revision 1 carried
`[UNVERIFIED — T186 is settling the general rule.]` here and *"is settling it in parallel"* at §9
item 3. **T186 merged before revision 1 did**, and A2-13's branch simply forked before it landed
[the ruling is `.softhouse/reviews/T186-wire-money-form-ruling.md`, read in full by this task]. A
ratified contract must not ship a live forward reference to a completed task.

T186's ruling is a three-way split, and **nothing in this subsection contradicts it** [checked
clause by clause by this task]:

| T186 category | ruling | DEC-2's position |
|---|---|---|
| **(a)** oracle-facing capture wire, `.softhouse/capture/**` | major-unit decimal is **ADMISSIBLE and in fact mandatory** — the oracle's bytes are captured as the oracle emitted them, bound as byte-fidelity | consistent: this subsection *measures* the wire (`"amount":1200000.000000`, scale 6, `numeric(19,6)`) rather than assuming it |
| **(b)** the Go module's own adapter/API surface, `nexus/**` | **REJECTION** — binds absolutely | consistent: *"integer minor units, `int64`, everywhere … in any struct field, schema column, API field, fixture or intermediate calculation"* |
| **(c)** the **stored vector**, `.softhouse/vectors/**` | **REJECTION** — money is `int64` minor units, and the measured state is **zero violations** across 50 files | revision 1 *implied* this by placing the conversion at "the capture-transcription step". **Revision 2 states it as a rule** — see immediately below |

**Normative consequence 4, added in revision 2 and required by T186(c): a stored `ledger` vector
carries money as a JSON STRING of integer minor units, never as a JSON number.** The loanschedule
schema already does exactly this — `"principal_minor": "116250250"`, with the oracle's own emitted
characters kept separately as `"principal_major_text": "1162502.50"` for transcription cross-check
only [VERIFIED: T186 §(c), citing
`.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json`]. Any `ledger` money
cell §5.3 introduces **must** adopt that pairing: the graded value is the minor-unit integer string;
the major-unit decimal text is a cross-check on the transcription and is **never** a grading
standard. A `ledger` vector storing `1200000.000000` as a bare JSON number would be rejected by the
store's existing raw-token float scan before any typed decode, which is the correct outcome.

DEC-2 still does **not** pre-empt T186 on what T186 itself left open: the treatment of currencies
whose minor unit is not 2, and whether a shared conversion utility is mandated. Those are outside
this contract. **If T186's ruling and this subsection are ever read as conflicting, T186 governs.**

**`[UNVERIFIED]` — whether the oracle can produce sub-minor-unit residue in a MONEY column at
all.** No captured vector establishes it. The corpus's only values beyond two decimals are the
`A2-209c` percentages, which are **not money** and must not be cited either way. A2-7's probe set
ran at a 0 % interest rate with no charges, no overpayment and no transfer, so the arithmetic
that would generate a sixth decimal was never executed — *"not observed" is a statement about the
probe set, not about Fineract.* §9 item 1.

### 4.4 The double-entry invariants: which are GRADEABLE, and which are structural only

Most of the project's ledger invariants cannot be graded by a `ledger` vector, and **none of them
can be graded today**. Saying which, and saying why the two statements differ, is the honest half of
this contract.

**Revision 1's fourth column answered two questions at once. Revision 2 splits it into two
columns**, because the difference between them is the whole of finding R-1:

- **IN PRINCIPLE** — do captured oracle bytes exist that would separate a correct implementation
  from an incorrect one? This is a question about the corpus.
- **TODAY** — can that separation be written down as an admissible vector and evaluated by the
  grader? This is a question about the machinery, and for **every row in this table the answer is
  NO**, because no `ledger` vector of any shape is currently expressible (§5).

| id | Invariant | Statement, checkable | In principle, from the captures in hand? | Graded today? |
|---|---|---|---|---|
| **I-1** | Debits equal credits | For every transaction, `Σ debit legs == Σ credit legs`, compared as `int64` minor units | **YES.** `A2-235`'s eight legs: debits `120,000,000 + 20,000,000 + 100,000,000 + 5,000,000 = 245,000,000` minor units, credits the same [the eight `"amount":` tokens RE-VERIFIED by this task from the raw bytes; the total matches A2-8's stated 245,000,000]. `A2-150`'s six rows are three balanced pairs at 120,000,000 each [VERIFIED by this task from the dump, lines 65-70]. | **NO.** §5 — no admissible vector can carry a money cell, or any `ledger` cell. |
| **I-2** | Splits sum to whole | `whole == Σ splits`, `int64` minor units | **YES.** `120,000,000 = 20,000,000 + 100,000,000` — disbursed principal against repayment plus write-off [re-derived by this task from the same legs]. | **NO.** Same reason. |
| **I-3** | Balances are DERIVED, never written | No write path to any balance column exists in the Go tree | **NO — STRUCTURAL ONLY.** A vector is a snapshot of oracle output; it cannot observe the *absence* of a write path. Gradeable only by a source-level guard over the Go tree. And the oracle is **not** a positive example: `m_trial_balance.closing_balance` is a written, stored, **unsigned** sum wearing a balance's name [VERIFIED BY A2-2's re-derivation of `UpdateTrialBalanceDetailsTasklet.java:81` reading `JournalEntryRepository.java:61`, NOT RE-OPENED HERE]. It is deliberately **not ported** (§7). | **NO BY A VECTOR — AND, SINCE REVISION 2, YES BY A SOURCE GUARD, PARTIALLY.** Revision 2 said *"no such guard exists"*; that was true when written and is **stale**. `guard_ledger_invariants` (built by `A2-18`, **wired** by `T208`) is the seventh guard `run_guards` invokes and it walks the Go tree for a write path to a balance [VERIFIED by `A2-28` at commit `2e97162`: `.softhouse/conformance.sh:1152-1187` defines it, `:1209` invokes it; MEASURED: `invariant violations 0`]. **Its limits are load-bearing and §4.4.1 states them** — the detection surface is the NAME, so renaming a balance defeats it. **⚠ GATE G-12 IS OPEN ON THIS EXACT INVARIANT AND DEC-2 DOES NOT RESOLVE IT.** `A2-26` observed that `acc_gl_journal_entry` carries **`office_running_balance`** and **`organization_running_balance`** — the reference oracle **stores** a balance on the entry, in a table `CLAUDE.md` separately instructs the port to adopt [raised as **G-12**, `.softhouse/gates.md`; `A2-29` must measure whether those columns are ever READ, whether they reach a contract-boundary response, and whether the stored value can disagree with the derived sum, **before** any option is argued]. This row states the Go-side obligation only. **Nothing in DEC-2 decides what the port does with those two columns, and a ratifier must not read this row as having decided it.** |
| **I-4** | The ledger is append-only | No `UPDATE`/`DELETE` against `acc_gl_journal_entry` from application code | **NO — STRUCTURAL ONLY.** "No update ever happened" is not observable from a capture. Partial exception: a reversal is observable *as a row*, because the table carries a `reversed` flag [VERIFIED BY A2-13 from `JournalEntry.java:79`, NOT RE-OPENED HERE]. | **NO BY A VECTOR — AND BOTH OF THE SOURCE GUARD'S I-4 ARMS INSPECTED AN EMPTY POPULATION HERE.** The same `guard_ledger_invariants` looks for DML against the journal table, but its own two `NIL-COVERAGE` lines say this Go tree contains **no SQL and declares no database driver**, so the `I-4` DML classes (`I4-DML`, and `I3-SQL-BALANCE` with it) are proven by the guard's self-test and **not** by this tree [MEASURED by `A2-28` at commit `2e97162` from the unfiltered run: *"zero mutating driver calls … class OPAQUE-SQL inspected an empty population"*]. **The guard's OTHER `I-4` arm, `I4-BUILDER` — the query-builder/ORM form of the same violation — likewise inspected an EMPTY population, and unlike the SQL classes the guard does NOT announce it** [MEASURED by `A2-32` at commit `33d19a6`, both polarities; §4.4.1's revision-5 retraction. Revision 4 wrote *"THE SOURCE GUARD'S I-4 ARM"*, singular, and recorded `I4-BUILDER` as `[UNVERIFIED]`]. **So NEITHER form of I-4 detection is exercised by this tree at all.** **P-35: a check that inspected zero items is not a pass** — and the guard says so itself for the SQL classes, while saying nothing at all about `I4-BUILDER`. |
| **I-5** | Corrections are reversing entries | A correction adds a leg pair; it never mutates one | **UNGRADED TODAY.** The A2 corpus contains no reversal: `A2-150`'s journal dump does not project `reversed` or `reversal_id` and its six rows are three ordinary pairs [VERIFIED by this task]; A2-8's grading table lists no reversal grading [VERIFIED BY A2-8, NOT RE-OPENED HERE]. Refused with `ErrNoDiscriminatingVector`; retired by one capture. §9 item 13. | **NO.** Nothing to grade, and nothing to grade it with. |
| **I-6** | Holds are postings and alter `available` only, never posted `balance` | — | **OUT OF THE CONTRACT DOMAIN.** No hold concept exists in A2's three tables. Refused with `ErrUnsupportedConfiguration`. | **N/A.** |
| **I-7** | `Idempotency-Key` on every money-movement POST | — | **NOT APPLICABLE TO THIS CONTRACT, and that must be said rather than assumed.** DEC-2's surface exposes no HTTP endpoint and moves no money; it is a value computation. The obligation is real and lands on **A1** (the posting engine) and on the adapter's HTTP layer. A `ledger` conformance PASS says nothing whatever about it. | **N/A** — and note that today there is no `ledger` conformance PASS to say nothing with. |

**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope.

### 4.4.1 THE GUARD I-3 AND I-4 REQUIRE — IT DID NOT EXIST, IT DOES NOW, AND WHAT IT CANNOT SEE

Revision 1 stated the requirement correctly and never claimed the guard existed. It also never said
it **doesn't**, and it placed the requirement four lines above a paragraph about guards that *do*
run. A reader will merge them. **This subsection exists so they cannot be merged.**

> **⚠ STALE BY LANDING — corrected in revision 3, and it moves in the SAFE direction.** Revision 2's
> heading here read *"THE GUARD I-3 AND I-4 REQUIRE DOES NOT EXIST"*, and the banner and §8.1 both
> asserted it as a measured fact. **It was true when revision 2 was written and it is false now.**
> `A2-18` built the guard on exactly the independence §5.3 P-8 claims, and `T208` wired it into
> `run_guards`. Revision 3 does not repeat the claim, and does not silently drop it either: **the
> requirement below is now SATISFIED IN PART, and the part it does not reach is the part a ratifier
> must read.** Nothing else in this subsection changes — the requirement it states, and the reason
> a vector can never discharge it, both stand.

**`run_guards` invokes SEVEN guards** [VERIFIED by `A2-28` at commit `2e97162`,
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
sixth concerns the repo root. None of those six looks for:**

- a write path to any balance column (that is **I-3**);
- an `UPDATE` or `DELETE` statement against `acc_gl_journal_entry`, or any Go call that would emit
  one (that is **I-4**);
- a derived-balance function that caches instead of deriving;
- a correction path that mutates a leg instead of adding a reversing pair (that is **I-5**).

**The seventh does, and this is what it actually delivers** [VERIFIED by `A2-28` at commit
`2e97162`: `.softhouse/conformance.sh:1152-1187`, the definition and its in-file commentary read in
full; MEASURED by `A2-28` at commit `2e97162` from its own unfiltered run, quoted verbatim]:

```
ledger-invariants: selftest OK — 15 cases, 13 RED, 2 GREEN (P-22 and P-50)
ledger-invariants: CENSUS ledger-invariants — inspected 45 Go files / 5 packages / 507 funcs
  (1 hold-named) / 659 assignment or inc-dec statements / 306 write targets / 4074 string
  literals in 3632 concatenation groups / 4691 calls under …/nexus (recursive, whole Go tree)
ledger-invariants: CENSUS ledger-invariants SQL surface — 90 SQL-shaped literals, of which 3 carry
  a DML verb (UPPER BOUND: English prose containing "update" satisfies it) and 0 name an actual
  table; 0 exec-family calls (0 mutating). Findings: 0
ledger-invariants:   census figure READ: inspected 45 >= 45 tracked by git (floor DERIVED, not pinned)
ledger-invariants: PASS — I-3 (balances are derived) and I-4 (append-only) hold over the
ledger-invariants:   Go tree AS FAR AS A SOURCE-LEVEL GUARD CAN SEE.
```

> **⚠ EVERY NUMBER IN THAT TRANSCRIPT CHURNS, AND THIS IS ITS THIRD PRINTING.** Revision 3 quoted
> `44 files / 502 funcs / 645 statements / 296 targets / 3955 literals / 3531 groups / 4572 calls`,
> measured truthfully on its own tree. `A2-25` re-ran it days later and got
> `45 / 507 / 658 / 306 / 4063 / 3621 / 4680`. `A2-28` re-ran it at `2e97162`, after `T116` landed,
> and got the figures above. **Not one of the three was wrong when taken; all three describe
> different trees.** The census counts every Go file under `nexus/`, so *any* commit touching *any*
> Go file moves it. **A ratifier must re-run `bash .softhouse/conformance.sh` and read the census
> off their own transcript, not off this page.** The figures that have NOT moved across all three
> printings are the load-bearing ones: `5 packages`, `1 hold-named`, `15 cases, 13 RED, 2 GREEN`,
> and `Findings: 0`.

It carries a self-test that runs **both polarities** (13 RED, 2 GREEN) — the P-22/P-50 shape, so the
guard is falsifiable in the direction of the fix and not only in the direction of the defect — and
it derives its file-count floor from `git ls-files` rather than pinning it, so a shrinking
population is a refusal rather than a quiet pass.

**FOUR OF THE GUARD'S DECLARED DETECTION CLASSES INSPECTED AN EMPTY POPULATION IN THIS TREE —
`I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML` AND `OPAQUE-SQL`.** [The class enumeration is VERIFIED by
`A2-28` at commit `2e97162` and re-derived by `A2-32` at commit `33d19a6`:
`.softhouse/guards/ledgerguard/main.go`, `Class: "…"` literals enumerated and de-duplicated — eight
literals at `:268`, `:286`, `:303`, `:500`, `:580`, `:596`, `:669`, `:680`, seven distinct classes;
the three `NIL-COVERAGE` emission sites read at `:840`, `:847` and `:852`; MEASURED from the live
run, in which the first two fire and the third does not. `I4-BUILDER`'s empty population is MEASURED
by `A2-32` — see the retraction below.]

| class | population in this tree | source of the finding |
|---|---|---|
| `I3-FIELD-WRITE` | non-empty — 306 write targets inspected | the tree |
| `I3-PKG-STATE` | non-empty | the tree |
| `I3-SQL-BALANCE` | **EMPTY** — zero SQL DML literals | `--selftest` only |
| `I4-BUILDER` | **EMPTY** — zero query-builder/ORM mutating calls; **the guard does NOT announce this one** | `--selftest` only |
| `I4-DML` | **EMPTY** — zero SQL DML literals | `--selftest` only |
| `I6-HOLD-BALANCE` | non-empty by an over-match the guard itself names | the tree, weakly |
| `OPAQUE-SQL` | **EMPTY** — zero mutating driver calls | `--selftest` only |

**The numerator is FOUR and the classes are named, because naming them is checkable and a
denominator is not.** The four that inspected an empty population are **`I3-SQL-BALANCE`**,
**`I4-BUILDER`**, **`I4-DML`** and **`OPAQUE-SQL`**. **The guard announces only the first, third and
fourth of them itself**, in two `NIL-COVERAGE` lines quoted verbatim [MEASURED by `A2-28` at commit
`2e97162`; `A2-32` re-read both lines on its own green run at `33d19a6` — same two lines, same three
classes named, with the literal count moved exactly as the census box above warns it will]:

```
ledger-invariants: NIL-COVERAGE — the SQL surface inspected 4074 string literals and found ZERO SQL
  DML statements of any kind under …/nexus. This tree contains no SQL: the I-4 SQL classes (I4-DML,
  I3-SQL-BALANCE) are proven by this program's --selftest and NOT by this tree. …
ledger-invariants: NIL-COVERAGE — zero mutating driver calls (Exec/ExecContext/SendBatch/CopyFrom/
  Prepare) exist under this root, so class OPAQUE-SQL inspected an empty population. The Go module
  declares no database driver at all.
```

**The fourth empty class is `I4-BUILDER`, and the guard says NOTHING about it — that silence is the
whole reason four revisions and the driver all missed it.** `OPAQUE-SQL`'s emptiness is announced by a
`NIL-COVERAGE` line; `I4-BUILDER`'s is not announced by anything. A reader who counts the empty
classes off the transcript, as three revisions and the driver did, will count three.

> **⚠ RETRACTION, revision 5 — revision 4 said the numerator was THREE and recorded `I4-BUILDER`'s
> population as `[UNVERIFIED]`. IT IS FOUR, and this is `A2-31`'s F-2.**
>
> **MEASURED, both polarities** [VERIFIED by `A2-32` at commit `33d19a6`; independently measured
> first by `A2-31` at `90c21d6`, agreeing]. `I4-BUILDER` fires on an `*ast.CallExpr` whose
> `calleeName` matches `mutatingCallRe`
> (`^(Update|Updates|UpdateAll|UpdateOne|UpdateMany|Delete|DeleteAll|DeleteOne|DeleteMany|Del|Remove|Truncate|Save|Upsert|SetColumn|Set)$`,
> `.softhouse/guards/ledgerguard/main.go:151`, applied at `:593-596`), so **its population is the set
> of such calls under `nexus/`** — exactly the analogue of `OPAQUE-SQL`'s population, which the guard
> itself declares empty by the same criterion. `A2-32`'s probe copies that regex, `calleeName`
> (`:406-418`) and `prunedDirs` (`:161`) verbatim and walks the same root:
>
> | arm | probe: `I4-BUILDER` population | the REAL `ledgerguard` binary |
> |---|---|---|
> | **GREEN** — the real `nexus/` tree | **0** | `clean: … across 47 Go files in 5 packages`, no `I4-BUILDER` finding |
> | **RED** — a `/tmp` scratch copy with three builder verbs planted against a `journalEntry` | **3** (`Update`, `Delete`, `Save`) | `REFUSED …` with `[I4-BUILDER]` three times |
>
> **The control that makes the zero a measurement rather than a broken probe:** the probe's own
> file and call censuses — `47` Go files, `5045` calls — reproduce the guard's own `CENSUS
> ledger-invariants` line on the same tree **to the digit**. It is walking the guard's population,
> not some other one. **P-22 / P-50: a detector nobody has seen fire is not a detector, and this one
> was driven both ways.**
>
> **Why this was reject-grade and not a quibble.** *"Three of seven"* reads as 57 % of the guard
> live; the measured figure is 43 %. **The arithmetic had flipped to flattering the result** — the
> exact hazard `P-67` names one box below, in the same subsection, about the same number. `A2-25`
> predicted the outcome in writing (*"it plausibly does not — which would make the true figure four
> of seven"*), `A2-28` recorded it `[UNVERIFIED]` at ONE site and shipped the uncorrected numerator
> as a measured fact at four others, and `A2-31` took the measurement, which costs one `go run`.
> **An `[UNVERIFIED]` tag at one site does not travel to the other five; only a corrected figure
> does.**

**One honest qualification about the classes that are NOT empty, and it is not asserted as a
figure.**

- **A third `NIL-COVERAGE` arm exists and did not fire** (`main.go:852`, for `I6-HOLD-BALANCE`),
  because the guard counted **one** hold-named function. That one is
  `nexus/internal/apps/ledger/slots_test.go:187 TestPlaceholderDisjointnessHolds` — an over-match on
  *"the property **holds**"* which **the guard's own `CANNOT-CATCH` block names as over-match (ii)**
  [MEASURED from the live transcript]. So `I6-HOLD-BALANCE`'s population is non-empty **only by that
  over-match**, and I-6 is not meaningfully exercised on this tree either.
  So `I3-FIELD-WRITE` and `I3-PKG-STATE` are the only classes with a genuinely non-empty population
  on this tree.

> **⚠ WHERE THE "FOUR" IN REVISION 3 CAME FROM — recorded so it cannot recur (this is `P-67`).**
> Revisions 1–3 said *"three of its **four** detection classes"*, at four separate sites, and §8.1
> introduced it under *"Four facts, **each measured by this task**"*. **It was never measured.** The
> guard's condensed `CANNOT-CATCH` text lists **four blind spots**, and the paragraph below correctly
> says *"FOUR THINGS IT CANNOT SEE"* — **blind spots were read as classes**, two different quantities
> one sentence apart. Line 2097 of revision 3 showed the conflation inside a single sentence:
> *"states **four things it cannot see**, including that **three of its four detection classes** …"*.
> `A2-21`'s own handoff recorded that it had **not opened `ledgerguard/main.go`** and had taken the
> figure from the guard's condensed text, so this was an inference presented as a measurement.
> **The driver then certified it "EXACT" and propagated it** to `.softhouse/program.json`,
> `.softhouse/RESUME.md`, `.softhouse/patterns.md` and `.softhouse/tasks.json` — **the error was the
> driver's before it was `A2-21`'s.** Those four files are outside this task's scope and are raised
> as a follow-up, not fixed here. **The remedy adopted in this revision: state a numerator with the
> members NAMED, and drop the denominator**, because a named list is checkable in one grep and a
> ratio is not.

**FOUR THINGS IT CANNOT SEE, and a ratifier who quotes the PASS without them has been misled.** The
guard prints these itself **in full, on every run, pass or fail — a ratifier's own green transcript
carries them** [VERIFIED by `A2-32` at commit `33d19a6` from its own unfiltered green run: the
`cannotCatch` const in `.softhouse/guards/ledgerguard/main.go` reaches the transcript as
`ledger-invariants: CANNOT-CATCH — the honest limits of this guard, printed on every run, pass or
fail:` followed by all **eight** numbered limits, on a run whose verdict is `PASS (exit 0)`;
`.softhouse/guards/check-ledger-invariants.sh:210-219` is the `awk` block that re-emits the paragraph
on the pass path, gated on `rc = 0`, added by `T209`. `.softhouse/conformance.sh` additionally prints
a separate 8-line condensation of the same limits]. **These are BLIND SPOTS, not detection classes;
the two counts are unrelated and conflating them is what §8.1 got wrong for three revisions:**

1. **The detection surface is the NAME. Renaming a balance defeats the guard.**
2. **Dynamic SQL is caught only through the call set it recognises**; triggers, migrations and
   stored procedures are not walked at all.
3. **`I-5`'s semantic half and non-Go callers are not covered.**
4. **The `I-4` SQL classes inspected an empty population in THIS tree** — the `NIL-COVERAGE` lines
   above report zero SQL DML literals and zero mutating driver calls, because the Go module declares
   no database driver. **P-35 applies exactly: a class that inspected zero items has not been
   exercised**, and the guard says so instead of counting it as clean. Its detection of real ledger
   SQL is proven by its self-test and by nothing in this repository.

> **⚠ RETRACTION, revision 5 — revision 4 said the guard's own head DROPPED this block on the pass
> path, cited `FU-T208-1` as an OPEN follow-up, and stamped the whole parenthetical `[VERIFIED by
> A2-28 at commit 2e97162]`. IT WAS FALSE AT ITS OWN STAMP, and it is `A2-31`'s F-1.**
>
> **What is true.** `T209` — commit `03e9094`, *"widen the ledger guard head's PASS-path filter so
> CANNOT-CATCH reaches green (FU-T208-1)"* — **closed** `FU-T208-1`, and `03e9094` is an **ANCESTOR**
> of `2e97162` [VERIFIED by `A2-32`: `git merge-base --is-ancestor 03e9094 2e97162` exits 0;
> `03e9094` is dated `2026-08-22 09:18:26 +0800` and `2e97162` `2026-08-22 10:34:50 +0800`, so the
> fix was on the tree **one hour and sixteen minutes before revision 4's own fork point**]. The block
> reaches every green run and `A2-31` and `A2-32` each measured it independently on their own
> unfiltered transcripts.
>
> **So this was not staleness. It was an unchecked inference wearing a measurement's stamp** — and it
> is precisely the class `A2-25`'s F-4 rejected one revision earlier: *a caveat that outlived its
> defect*. The stamp made it worse, not better, because the document's headline discipline is that a
> stamped claim was re-derived at that commit. **P-21, P-26, P-37; and P-69 — a stamp certifies WHEN
> a claim was taken, never THAT it was taken.**
>
> **`FU-T208-1` is CLOSED and this document no longer cites it as open anywhere.** The retracted
> claim survives OUTSIDE this document, in `.softhouse/conformance.sh` — **one PRINTED line and a
> 25-line comment block whose entire premise `T209` invalidated** [MEASURED by `A2-32` at `33d19a6`:
> the printed line is `:1187`; the stale comment claims are at `:1163` (*"one of them does not
> arrive on its own"*), `:1166-1168` (the head *"re-prints only `^CENSUS ` and `^NIL-COVERAGE `"*,
> citing a line that has itself moved), `:1172`, `:1176`, `:1177` (*"RAISED as FU-T208-1, not fixed
> here"*) and `:1182` (*"the fix is FU-T208-1"*). `A2-31` named the printed line only; `T209`'s own
> handoff recorded the comment as stale and did not touch it]. It is **not this document's to fix**,
> is routed as `T227` (`A2-31`'s FU-A2-31-2), and the widening is recorded in §10's revision-5 entry
> and in `A2-32`'s handoff. A ratifier reading a transcript today will see the true block and that
> one false printed line together — the false line is the harness's, not this ADR's.

**So the normative requirement in the table above is now SATISFIED IN PART: a source-level guard
runs, it is falsifiable, and its blast radius is a source-level Go tree that contains no SQL.**
The correct reading of this whole subsection is: *DEC-2 obliges I-3 and I-4, names the only
mechanism that could enforce them, and that mechanism now exists over the Go tree while
`I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML` and `OPAQUE-SQL` wait for a tree with a database in it.* Anyone who
ratifies this document ratifies that residue along with it, knowingly. §5.3 **P-8 is accordingly
marked LANDED**, and what replaces it is narrower.

**One inherited claim this draft CORRECTS rather than repeats.** A2-8's follow-up **F-1** records
that `conformance.sh`'s hard guards were scoped to `loanschedule`, so a float in
`nexus/internal/apps/ledger/` would leave the harness green. **That was true when A2-8 wrote it
and is FALSE now: task T166 widened both guards to the Go module root.** [VERIFIED by `A2-28` at
commit `2e97162`, re-opened rather than taken on the report: `conformance.sh:401` sets
`NEXUS_DIR="$REPO_ROOT/nexus"`; `guard_no_float_in_harness` enumerates
`find "$NEXUS_DIR" -name '*.go' -type f` and additionally fails on a zero **package** count; and
`guard_gofmt` roots at `"$NEXUS_DIR"` with the `contract.go` exemption expressed as a filter on
the *output* rather than as a narrowed root. `find nexus -name '*.go' | grep -c ledger` returns
**18**, so all eighteen ledger files are inspected.] The in-file commentary also records that the
defect was **measured, not theorised** — with three floats planted under
`nexus/internal/apps/ledger/`, the pre-fix run was byte-identical to the clean baseline.

**So the requirement is met today, and DEC-2 records WHY it must stay met**: the roots are
*derived* (`find` from the module root) rather than *enumerated*, which is what makes a new
package covered by default. A future change that re-narrows either root to a named subtree
silently un-grades this context's I-3 and I-4, and would do so while still printing a
healthy-looking file count.

### 4.5 The chart of accounts is DATA, not code — G-9, CLOSED, not re-decidable here

**G-9 is CLOSED** (`.softhouse/gates.md` § G-9, local fire `20260821-054355`, `chosen_by:
agent`). Its premise was re-derived by the driver: across the two tenant seed-data changelogs,
**1,918 `<insert>` elements, of which ZERO target `acc_gl_account`**; the table appears in
`db/changelog/tenant/parts/` only as `createTable` plus two `createIndex` statements
[VERIFIED BY THE DRIVER'S OWN RE-DERIVATION, NOT RE-OPENED HERE]. **Fineract ships the table and
no rows.**

DEC-2 is bound by the decision and restates it as a contract boundary:

- **DEC-2 specifies the GL account MODEL** — `Classification` (1..5), `Usage` (DETAIL 1 / HEADER
  2), the parent link, `hierarchy` generation and its display decoration, `disabled`,
  `manual_journal_entries_allowed`, `gl_code`, `name` — **`acc_product_mapping` resolution**
  (§2.1), and **the posting rules** that select an account.
- **The chart itself is seed data, outside the contract.** A vector *names* the chart it was
  taken against (a `ledger_db_readback` dump, §4.1); it does not embed one as a contract fixture.
- **Launch with the minimal chart the captured vectors exercise.** An FRC-aligned production
  chart is a separate, data-only deliverable, downstream of CUTOVER, which is already a hard
  `user` gate. Nothing here pre-empts that.

**Two contract facts G-9 did not reach, and DEC-2 adds:**

- **`hierarchy` is display-only and decides no money** [VERIFIED BY A2-1 AND CONFIRMED BY A2-2,
  NOT RE-OPENED HERE], and a parent's classification need not match its child's [VERIFIED by
  this task, §2.1]. So `hierarchy` is in the contract as an **output** to be reproduced — the
  port rebuilds every stored hierarchy string from the parent chain and is graded on it — and
  **never as a resolution input**.
- **A HEADER account is a valid posting target.** [VERIFIED by this task: `A2-150` journal entry
  id 6 debits GL account 1 `Assets`, whose `account_usage` is `2`.] "Detail accounts only" is a
  dropdown convention, not a domain rule [VERIFIED BY A2-2 from
  `GLAccountReadPlatformServiceImpl.java:214-222` and its seven dropdown call sites, NOT
  RE-OPENED HERE]. A port that refuses a HEADER target would diverge from the oracle **on
  observed data**.

### 4.6 G-10 as a stated hazard, and the constraint it puts on admissibility

**G-10 is OPEN. This draft records it and does not decide it.**

**The hazard, stated exactly** — and the exactness matters, because A2-11's independent review
found the surrounding reasoning had been overstated in one direction and understated in another:

1. GL account **2** (`10100 Fund Source`) was retyped **ASSET → INCOME** underneath live product
   mappings. Two committed dumps of the same tenant disagree: `A2-072` reads
   `classification_enum = 1`, `A2-150` reads `4` [VERIFIED by this task for `A2-150`; `A2-072`
   VERIFIED BY A2-8 AND RE-MEASURED BY A2-9, NOT RE-OPENED HERE].
2. **Five products (22, 23, 24, 27, 28) but SIX mapping rows.** Product 27 holds GL 16 and GL 2
   in a **single payment-type slot**, which the repository resolves to **one** row. So the count
   depends on whether you are counting products, mapping rows, or resolved slots, and **any
   disclosure of G-10 must say which** [A2-11's refinement; the duplicate itself VERIFIED by this
   task from `A2-150`: `(27, 1, 1, payment_type 1) → n = 2, gl_account_ids {16,2}`].
3. **The oracle serves the state without complaint and will not re-create it.** `A2-214` re-sends
   a mapping the oracle itself accepted as product 23 and gets **HTTP 403**,
   `error.msg.fundSourceAccountId.invalid.account.type` [VERIFIED BY A2-7 AND RE-VERIFIED BY
   A2-9, NOT RE-OPENED HERE].
4. **`GET /loanproducts/{id}` structurally cannot reveal it** — `{id, name, glCode}` per slot, no
   type and no usage [VERIFIED by this task, §2.3].
5. **But two calls can.** `GET /glaccounts/2` reveals INCOME plainly. *"The read-back cannot
   reveal it"* is TRUE; *"nothing at the contract boundary reveals it"* is FALSE [A2-11's
   correction; VERIFIED BY A2-11 AND BY THE DRIVER, NOT RE-OPENED HERE].
6. **It is documented behaviour of the update path, not an oddity of this tenant.** The only
   journal-entries-exist guard on the GL-account update path is keyed on **USAGE** and gated on
   `isHeaderAccount()`; **TYPE is not mentioned**, though `deleteGLAccount` has its own
   entries-exist check — so the query was available and simply was not applied to classification
   [VERIFIED BY THE DRIVER'S RE-DERIVATION at
   `GLAccountWritePlatformServiceJpaRepositoryImpl.java:151-159` and `:201-203`, NOT RE-OPENED
   HERE]. **Any Fineract deployment can reach this state.**
7. **Combined with `acc_gl_journal_entry` carrying no classification column** (§2.1, verified by
   this task), a retype **retroactively re-renders every entry ever posted** to that account.
   This is why §3.3 carries classification on the resolved account.
8. **The tenant's financial-activity mapping is in the same state.** `A2-150` shows activity
   **100 = ASSET_TRANSFER** mapped to GL account 2, whose `classification_enum` is now **4**
   (INCOME), while `FinancialActivity.ASSET_TRANSFER` requires `GLAccountType.ASSET`
   [VERIFIED by this task: the `acc_gl_financial_activity_account` dump in `A2-150`, and
   `AccountingConstants.java:439`].

**The constraint DEC-2 puts on admissibility — a rule, not a decision of G-10:**

- **A-1.** Every `ledger` vector whose fixture is one of products **22, 23, 24, 27, 28**, or
  whose fixture touches GL account **2** or financial activity **100**, must **declare** that
  dependency in its provenance. **An undeclared dependency on the retyped chart is
  INADMISSIBLE** — default-deny, the same discipline the capability registry applies to an
  unaudited input.
- **A-2.** **Resolution gradings are immune to the retype and remain admissible.** A2-9 read all
  four oracle resolvers end to end and found none references classification, usage or `disabled`
  [VERIFIED BY A2-9, and independently corroborated by this task for the loan resolver at
  `AccountingProcessorHelper.java:1213`, §2.2 B-2]. Resolution answers "which account id", and
  GL 2's id is 2 under a clean chart too.
- **A-3.** **Write-side type-check gradings are NOT reproducible from a clean chart** and must
  carry the fixture state, not merely the request. Under a clean chart `A2-214` would be an HTTP
  **200**, not a 403 [A2-9's judgement; VERIFIED BY A2-9, NOT RE-OPENED HERE]. The affected
  family is `A2-214`, `A2-prod-063`, and the financial-activity create replay.
- **A-4.** **The driver's standing recommendation is option (c) — promote vectors only from
  products the oracle would still accept today.** DEC-2 records it, notes that under (c) product
  **46** is available as a clean write-side fixture (created HTTP 200 on 2026-08-21 with
  `fundSourceAccountId: 16`, an ASSET [VERIFIED by this task from `A2-211` and from `A2-150`'s
  row for GL 16, `classification_enum = 1`]), and **does not decide the gate**. If (c) is
  adopted, A-3's family is retired and re-captured; if it is not, A-3 governs.

### 4.7 The creation-set / posting-set divergence, and which set DEC-2 grades

A naive contract would get this wrong, so it is stated as a normative rule.

**The two sets are NOT the same, and it is MEASURED, not inferred.** Product **46** was created
carrying exactly the nine slots the create validator marks `notNull()` and none of the ones it
marks `ignoreIfNull()` — HTTP **200**. Then:

| probe | capture | result |
|---|---|---|
| `POST /loans/5/transactions?command=charge-off` | `A2-224` | **HTTP 404** — `Mapping for product of type LOAN with Id 46 does not exist for an account of type CHARGE OFF EXPENSE` |
| `POST /loans/5/transactions?command=goodwillCredit` | `A2-225` | **HTTP 404** — `… does not exist for an account of type GOODWILL CREDIT` |

Both slots are `ignoreIfNull()` at creation — `CHARGE_OFF_EXPENSE` at
`LoanProductDataValidator.java:744` and `GOODWILL_CREDIT` at `:704`
[VERIFIED BY A2-7's own re-read of the pinned source, NOT RE-OPENED HERE]. So:

> **{accounts required at RUNTIME} ⊄ {accounts required at PRODUCT CREATION}.**
> **A product Fineract will happily CREATE cannot complete every POSTING path.**

The two codes are `CHARGE_OFF_EXPENSE` = **16** and `GOODWILL_CREDIT` = **13**, and both are
present **with identical names in both loan enums** [VERIFIED by this task:
`AccountingConstants.java:48` and `:51` for cash, `:109` and `:112` for accrual]. **Consequence
for what these two captures grade:** they grade the *message text* exactly, and they **cannot
discriminate which enum rendered it**, because at 13 and 16 the two enums render the same word.
§4.9's rendering rule is therefore source-derived and **not** confirmed at the boundary. §9 item 4.

**Which set DEC-2 grades:**

- **DEC-2 grades the POSTING set.** An implementation must resolve **per posting path** and
  refuse **at posting time** exactly where the oracle does, with the oracle's own error code,
  HTTP status and message. **A port that pre-validates the nine mandatory slots at product
  creation and then assumes every posting path resolves is wrong**, and would pass any vector
  taken only at creation time. That is the trap this section exists to close.
- **DEC-2 specifies the CREATION set as a separate, weaker VALIDATION predicate** — which
  parameters the oracle demands on `POST /loanproducts`: nine `notNull()` for cash, twelve for
  accrual [VERIFIED BY A2-7's re-read, NOT RE-OPENED HERE].
- **And it specifies the UPDATE rule, which contradicts a plain reading of the update validator.**
  `validateForUpdate` marks **every** account parameter `ignoreIfNull()`, so a PUT flipping
  cash→accrual with no receivables *should* pass. **It is refused 400, listing all twelve**
  (`A2-240`), with the one-variable control passing 200 (`A2-242`). The enforcement is at
  `ProductToGLAccountMappingWritePlatformServiceImpl.java:410-411`:
  `if (accountingRuleChanged) { this.deserializer.validateForLoanProductCreate(command.json()); }`
  — **the create-mandatory set is re-imposed on update if and only if the accounting rule
  changed** [VERIFIED BY A2-7, which measured before it read and then found the mechanism; NOT
  RE-OPENED HERE].

**What DEC-2 explicitly does NOT claim.** A2-7's probe set posted to four of the nine mandatory
slots and not to the other five (`INTEREST_ON_LOANS`, `INCOME_FROM_FEES`,
`INCOME_FROM_PENALTIES`, `OVERPAYMENT`, `TRANSFERS_SUSPENSE`) — but that probe set ran at a 0 %
rate with no charges, no overpayment and no transfer, **so the absence is a statement about the
probes, not about the accounts.** No parity claim is made about those five, and predicate
**G-11** confines posting-time grading to `{1, 2, 6, 12}` for exactly this reason. §9 item 12.

### 4.8 Enum encoding: the stored value, never the ordinal, and never a bare integer

- **Every persisted enum value is the enum's own `getValue()`.** No `ordinal()` call and no
  `@Enumerated` exists in the scope paths [VERIFIED BY A2-2 with positive controls in both
  directions, NOT RE-OPENED HERE]. A Go `iota` on a persisted field is the same trap wearing
  Go's clothes, and DEC-2 forbids it: every enum on this boundary carries an explicit stored
  value and an explicit inverse of that map.
- **`PortfolioProductType` must encode `getValue()` and decode by that map's true inverse.**
  Transcribing `fromInt` inherits the 3→5→4→3 permutation. The oracle's defective decoder may be
  reproduced for fidelity **only** under a differently-named function documented as never usable
  to decode storage [A2-8 ships exactly this; VERIFIED: `producttype.go:162`
  `FineractFromIntQuirk`, read by this task].
- **The five placeholder enums are five separate constant spaces, and a bare integer may not
  reach a resolver.** Because the two loan families disagree at 22/24/25 and each has members the
  other lacks (§2.1), a single flat enum is *already wrong* before any port is written.
  **Honest limit, stated rather than papered over:** Go permits an explicit numeric conversion
  between two named integer types, so nothing in the language can make the separation
  unforgeable; enforcement is a source-level scan, not a type [VERIFIED BY A2-8, which ships
  `TestNoCrossFamilySlotConversion` driven RED first, NOT RE-OPENED HERE].
- **The placeholder codes and the financial-activity codes must be provably disjoint.** STEP 0
  fires on a bare integer comparison (`FinancialActivity.fromInt(id) != null`, §2.1), so a
  placeholder code colliding with `{100,101,102,103,200,201,300}` would silently route a product
  mapping to a tenant-global account. The placeholder enums top out at 26 [VERIFIED by this task
  from `AccountingConstants.java:37-62` and `:95-122`], so they are disjoint **today**; DEC-2
  requires the disjointness to be asserted **executably** rather than assumed, because a future
  Fineract release adding a placeholder is not this contract's decision.

### 4.9 The refusal taxonomy — and the distinction a naive port would collapse

**There are TWO kinds of negative answer in this context, and conflating them is a defect.**

**(a) Contract refusals** — the adapter's own, about what DEC-2 admits. Three sentinels, adopted
unchanged from DEC-1 §4.11 including the wrapping and the precedence:

| Sentinel | Meaning |
|---|---|
| `ErrInvalidRequest` | The request is not well formed. |
| `ErrUnsupportedConfiguration` | Well formed, but this contract does not admit it, or the oracle cannot be asked at all. |
| `ErrNoDiscriminatingVector` | Well formed and computable, but outside the **graded domain** (§4.2). |

`ErrNoDiscriminatingVector` **wraps** `ErrUnsupportedConfiguration`, so a caller that does not
care sees two cases. **Precedence, from strongest obstruction to weakest: `ErrInvalidRequest` →
`ErrUnsupportedConfiguration` → `ErrNoDiscriminatingVector`**, and an implementation returns the
**first** applicable sentinel. The reason is DEC-1's and it holds identically here: without a
precedence rule two conforming implementations could return **different** sentinels for the
identical request, which is indistinguishable from a conformance failure.

**(b) Oracle-faithful refusals** — these are **ANSWERS**, part of the graded output, not contract
refusals. Reproducing them exactly *is* parity. **A port that returned `ErrNoDiscriminatingVector`
where the oracle returns a 404 would "refuse" a case that is in fact fully graded**, and the
harness would report a refusal instead of a failure.

| oracle refusal | code / status | graded by |
|---|---|---|
| mapping not found (loan, WCL) | `error.msg.productToAccountMapping.not.found`, **404** | `A2-224`, `A2-225`, `A2-092` — message for message |
| duplicate mapping rows | `error.msg.data.integrity.issue`, **403**, `More than one result was returned from Query.getSingleResult()` | `A2-086` (product 27, `paymentTypeId: 1`) |
| slot type check | `error.msg.<slot>.invalid.account.type`, **403** | `A2-214`, `A2-prod-063` — and see **A-3**: this family is chart-state-dependent |
| financial activity duplicate / invalid pairing | `error.msg.financialActivityAccount.exists` / `.invalid`, **403** | `A2-fin-102`, `A2-fin-103` |
| GL account refusal family | sixteen codes and statuses | the `A2-bad-*`, `A2-11x`, `A2-12x`, `A2-fin-*` sets |

[All the above VERIFIED BY A2-8's graded test table, WITH THE COUNTS 16 AND 17 RE-COUNTED BY
A2-9; NOT RE-OPENED HERE — except the data underlying `A2-086`'s duplicate and `A2-214`'s
retyped account, which this task re-verified from `A2-150`.]

**Evaluation order is: all three contract sentinels first, then the oracle-faithful answer.** A
request outside the graded domain is refused before the oracle's own refusal is computed, because
a refusal nobody can grade is not an answer.

> **THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN.** The vector schema has exactly
> two expectation kinds, `schedule` and `refusal`, and `refusal` means one of the three **contract**
> sentinels above. There is no encoding for *"the oracle answered 404 with
> `error.msg.productToAccountMapping.not.found`"* — and filing it as a contract refusal would write
> this subsection's own named defect into the corpus. Establishing this is §5.1; a representation
> for it is precondition **P-2** in §5.3. **Every row of the (b) table is therefore ungraded today**,
> including the three `A2-224` / `A2-225` / `A2-092` message-for-message gradings, which exist as
> **Go tests** against committed bytes and not as vectors (§5).

**Two normative rules about the message text:**

- **R-1 — the miss message is rendered by the FIXED enum for the entry point, not by the
  applicable family.** Loan renders through `AccrualAccountsForLoan` always [`:1210`]; WCL
  through `CashAccountsForLoan` always [`:1026`]. At codes 22, 24 and 25 that emits the *other*
  family's word for one of the two accounting rules. **A port must reproduce this**, because the
  alternative — "render the family that actually applies" — emits a string the oracle never
  emits, and would make three currently-exact message gradings inexact. (A2-8 was given the
  divergent rendering as a mid-flight instruction and declined the half that would have broken
  parity, carrying the applicable family as a diagnostic-only field instead; A2-9 adjudicated in
  its favour. DEC-2 records the outcome as the rule.) **`[UNVERIFIED at the boundary]`** — §9
  item 4.
- **R-2 — one deliberate, recorded divergence, in two places.** Where the rendering enum has **no
  member** at the code (cash 26; accrual-only 7/8/9 on the WCL path) the oracle calls
  `.toString()` on a null and the client gets an **NPE**, not a refusal. DEC-2 **does not require
  a port to reproduce a crash**: the port may fall back to the other loan enum's name and still
  return the typed refusal, so the divergence is confined to the case where the oracle cannot
  produce a message at all. Likewise, on the savings / shares / charge paths the oracle's
  missing-mapping outcome is an untyped **HTTP 500** from a null dereference, and a port
  returning a typed error **differs in status code**. Both divergences lie on paths outside the
  graded domain (§4.2 G-02, G-04), and both are recorded here so they are not later mistaken for
  defects. A2-8 ships them and says so [VERIFIED: `nexus/internal/apps/ledger/errors.go` declares
  `ErrMappingNilDereference` with `HTTPStatus: 500` and the divergence written into its doc
  comment; read by this task].

### 4.10 The capability registry for this context, and the default-deny discipline

DEC-2 adopts `.softhouse/vectors/capabilities.json`'s method wholesale, including the sentence
that makes it work:

> **An ABSENT entry refuses too: default-deny, because an unaudited input is assumed invisible
> and never assumed wired.**

Four statuses, unchanged: `exercised` (gradeable) | `blind` (structurally invisible — an
implementation honouring it and one ignoring it score identically) | `aliased` (a value from
another configuration scope arrives in the slot) | `partial` (reached, but on a narrower subset
than a reader would assume). **Only `exercised` permits grading.**

The `ledger` capability rows this contract requires. **This is a specification for the registry,
not the registry file itself** — authoring data files belongs to the grader task.

> **The `in_graded_domain` column below is the TARGET STATE, not the value to author first. Read
> §5.4's NORMATIVE SEQUENCING RULE before writing any of these rows into `capabilities.json`.**
> Every row here lands `false` initially, and a `true` flips only in the change that promotes the
> vector covering it. A `true` authored ahead of its vector turns **every** run in the repository
> red — including `-context=loanschedule` — and **the only legal way to clear it is to withdraw the
> row to `in_graded_domain: false`**, because **§5.1 and §5.4 together** establish that no `ledger`
> vector can be *expressed* until **§5.3's** P-1…P-5 exist, and §5.1's five legs are unaffected by
> `A2-20`'s admission-time context allowlist.
>
> **⚠ RETRACTION, revision 3 — two corrections to the sentence above, both from `A2-19`.**
> **(a)** Revision 2 wrote *"no `ledger` vector can be **admitted at all**"*. **That was FALSE** —
> a relabelled `loanschedule` parity vector was admitted, graded, and counted, taking the headline
> to `PASS 44` / `5711 cells` at exit 0 (banner item 2; §5.1.1). The true claim is
> **expressibility**, which is what §5.1 proves and what the sentence now says. **(b)** Revision 2
> attributed P-1…P-5 to §5.1; they are **§5.3's**, and the composite claim is §5.1 + §5.4, not §5.1
> alone. **(c)** Revision 2 wrote *"no legal way to clear it"*; the harness's own remediation text
> names **two** outs — *"Either promote a vector with a `graded_against` entry, or set
> `in_graded_domain` false in `capabilities.json`"* [VERIFIED by this task: `grade.go:473-474`] — and
> §5.1 closes only the first. The second is
> legal, immediate, and is step 2 of §5.4's own sequencing rule. Revision 2 overstated in the
> **fail-loud** direction, which is the safe one; it is corrected because a document that is being
> ratified as an admissibility standard may not be approximately right about what the harness does.

| capability | description | `in_graded_domain` | status per seam |
|---|---|---|---|
| `gl.account.model` | classification, usage, parent link, hierarchy generation, decorated name | **true** | `ledger_db_readback`, `ledger_rest_admin`: `exercised` |
| `mapping.core.row` | the all-discriminators-NULL row keyed on `(product_id, product_type, financial_account_type)` | **true** | `ledger_rest_admin`, `ledger_rest_posting`, `ledger_db_readback`: `exercised` |
| `mapping.paymenttype.override` | STEP 2, fund-source slot only | **true** | `ledger_rest_posting`: `exercised` (`A2-084` type 1 → GL 16; `A2-085` type 2 → core row) |
| `mapping.paymenttype.null` | resolution with a **nil** payment type on the fund-source slot | **false** | **`blind` on ALL FOUR seams** — `ledger_rest_admin`, `ledger_rest_posting`, `ledger_db_readback`, `ledger_inprocess_resolver`. Corrected in revision 2 — see the note below. §9 item 2. |
| `mapping.duplicate.rows` | two rows in one resolved slot | **true** | `ledger_rest_posting`: `exercised` (`A2-086`) |
| `mapping.charge.precedence` | the three per-family charge chains, and savings' `m_charge`-account override | **false** | `ledger_inprocess_resolver`: `blind` — **B-3**, the charge resolvers are `private`. Other seams: ABSENT, no charge exists in the tenant. |
| `mapping.reason.classification` | charge-off reason, write-off reason, capitalized-income and buy-down classification lookups | **false** | ABSENT on every seam — no such row exists. |
| `financialactivity.model` | the seven activities, their values, codes and required classifications; the create/update asymmetry | **true** for the model | `ledger_db_readback`: `exercised` (three rows in `A2-150`); `ledger_rest_admin`: `exercised` for the refusals |
| `financialactivity.step0.precedence` | STEP 0 pre-empting the product mapping **at posting time** | **false** | ABSENT — the *data* is graded, the *precedence* is not; no capture posts through it. §9 item 5. |
| `posting.resolution.cash.loan` | resolution at journal-entry time, cash loan product | **true**, with the slot set `{1, 2, 6, 12}` declared on the row | `ledger_rest_posting`: `exercised` |
| `posting.resolution.accrual.loan` | the same for an accrual product | **false** | ABSENT — product 28 is read back, never posted on. |
| `resolution.savings` / `resolution.shares` / `resolution.wcl` | the other three product families | **false** | ABSENT on every seam. |
| `entry.classification.carried` | whether the port records the account's classification **on the entry** | **false** | ABSENT — structural (§4.4 I-3 / I-4 class); no vector can grade it. |
| `money.subminor.residue` | a money column carrying a non-zero digit beyond the minor unit | **false** | ABSENT — never observed; §4.3, §9 item 1. |

**Correction in revision 2 — `mapping.paymenttype.null` had to be listed on a seam, not left
ABSENT, for the property the row claims.** Revision 1 said the row was *"declared so a vector
claiming it is refused **with a named reason** rather than as an unknown capability"* while leaving
it ABSENT on every seam. **Those two are incompatible.** `Assess` interpolates the row's `Evidence`
string — the named reason — only on the `blind` and `ungraded` paths; a capability that is *defined*
but absent from a seam's status map lands in the `unknown` bucket with the generic default-deny text
and **no evidence string at all** [VERIFIED by this task: `capability.go:351-392`, the three arms
read; `capDef.Evidence` appears in the `blind` and `ungraded` messages and in neither `unknown`
message]. So the row refused either way and the diagnostic — the entire point of declaring it — was
silently lost. It is now listed as **`blind` on all four seams**.

**All four, and the reason is worth stating because listing only one would have looked tidier and
achieved nothing.** `Assess` reads the status map of **the seam the vector declares**. Listing the row
`blind` only on `ledger_inprocess_resolver` would deliver the named reason exclusively to a vector
declaring the one seam `G-01` already refuses — the diagnostic would arrive precisely where nobody can
receive it. A vector on `ledger_rest_admin` or `ledger_rest_posting` claiming this capability is the
realistic case, and it must get the named reason too. `blind` is the accurate status on each of them:
no seam in the corpus resolves a fund-source slot with a nil payment type, and §9 item 2 records that
the query semantics themselves are undecided, so an implementation honouring the capability and one
ignoring it score identically everywhere — which is what `blind` means.

**One vocabulary decision, recorded rather than taken silently.** Several rows above are ABSENT
for a reason the four statuses do not name: *no fixture exists on the capture tenant* — there is
no savings product, no share product, no WCL product, no charge and no reason row. The obvious
move is to invent a fifth status such as `unfixtured`. **DEC-2 declines**, because
`capabilities.json`'s schema is shared with the `loanschedule` context and adding a status is a
change to that file's contract, which is not DEC-2's to make. ABSENT already refuses, which is
the correct outcome; the *reason* belongs in the row's `evidence` string. Recorded here so the
next reader does not mistake the omission for an oversight.

---

## 5. What DEC-2 would be frozen against — and today that is ZERO vectors

**This is the section a ratifier must not skim.**

**THE STAMPED BASELINE. Every corpus figure in §5 is measured at this one point, and nowhere else in
this document may a bare count appear without one.**

```
[MEASURED by A2-28, commit 2e97162, 22 August 2026, `bash .softhouse/conformance.sh` unfiltered]
    probe line PRESENT and reads: reference oracle (…/actuator/health) probe = up
    parity vectors          PASS 46   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    refused 0 · inadmissible 0 · harness errors 0
    cells compared          7884 graded, 93 ungraded
    invariant violations 0 · invariant assertions 0 NOT RUN · 4 EXEMPTED BY A VECTOR (G-8 family B)
    kills named             106 money, 7 structural
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
vector store  73c3ea7b43dd75f04884072719a87fc8e1d255c1   (git rev-parse HEAD:.softhouse/vectors)
`.softhouse/vectors/loanschedule/` holds 50 .json files: 46 class:parity + 4 class:contract-refusal
`.softhouse/vectors/_selftest/`     holds 1
```

`.softhouse/vectors/` holds **46 promoted parity vectors, all `loanschedule`** [MEASURED above; the
store's only context directories are `loanschedule/` and `_selftest/`]. **The `ledger` context has
none.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to
the minor unit; **DEC-2 would be frozen against a corpus that does not yet exist in the store.**

> **⚠ THIS BASELINE MOVED THREE TIMES INSIDE ONE FIRE.** It was `43 / 5664 / ce821c63…` when
> revision 3 was drafted, `43 / 5664 / 47 files` when `A2-25` reviewed it, and is `46 / 7884 /
> 50 files / 73c3ea7b…` now — `T116` promoted three vectors in between. **A ratifier must re-run the
> harness and compare against their own transcript.** Nothing in §5.2 depends on the specific
> integers; what it depends on is that the number **does not change across the extension**, which is
> why requirements 1, 2 and 6 are phrased against a **freshly measured** baseline rather than
> against a literal.

What *does* exist, and it is substantial but it is **not** the same thing:

- **The A2 capture corpus** — `.softhouse/capture/tierA-a2/`: **191 JSON response bodies** under
  `out/` (of **619** files there, the rest being the paired `.http` and `.status` records) and
  **109 request bodies** under `req/` [both counts MEASURED by `A2-28` at commit `2e97162` with
  `ls | wc -l`; they were 147 / 444 / 89 at revision 3, and `A2-26` added 45 raw ledger captures
  in this fire], taken from the running oracle at tenant `gerege` on the pinned commit.
- **55 Go tests in `nexus/internal/apps/ledger/`**, every one graded against committed
  reference-oracle bytes [count VERIFIED BY A2-8, NOT RE-OPENED HERE]. **These are not harness
  guards.** `conformance.sh` never runs `go test`, so a regression in them does not turn the
  harness red [RE-VERIFIED by `A2-16`: the script contains **no** `go test` invocation — both
  occurrences of the string are comments, at `conformance.sh:718` and `:721`; its only Go command is
  a `go build` of the conformance `cmd` package — and it says so itself at `conformance.sh:721`,
  *"`conformance.sh` never runs `go test`, so a Go-test-only guard is not a guard"* (P-45). The line
  numbers moved between revisions; the fact did not.].

**The honest consequence, stated so nobody reads a green bar as coverage:** ratifying DEC-2 would
freeze a contract whose graded domain (§4.2) is *justified* by observations that are **not yet
promoted vectors** — and, revision 2 adds, **that could not be EXPRESSED if somebody tried** (revision 3: *expressed*, not *admitted* — §5.1.1 retracts the stronger word, which was false).

#### 5.0.1 Three capture facts `A2-26` established in this fire, which constrain what §5.2 may ask for

Recorded here because two of them change what a first `ledger` vector can honestly assert, and the
third is a **trap for the requirement-7 perturbation cell** [all three VERIFIED BY `A2-26`, NOT
RE-OPENED HERE; `A2-28` read the handoff and did not re-open the capture bytes]:

1. **Before `A2-26`, every journal entry in the corpus had exactly two legs** — 7 transactions,
   14 rows. So *"splits sum to the whole"*, an invariant `/softhouse-uat` asserts, was exercised by
   nothing. There are now **2 four-leg and 4 three-leg** transactions.
2. **Before `A2-26`, every ledger amount in the corpus was a whole tugrik.** A port that dropped or
   mis-rounded minor units was byte-indistinguishable from a correct one on **every capture ever
   taken in slice A2**. There are now legs at `270450.58`, `22049.42`, `889549.42` and others. This
   is exactly the **P-22/P-35** shape at the level of the corpus, and it is why §5.2 requirement 7
   now demands a money perturbation rather than merely permitting one.
3. **`glAccountType` in a `/journalentries` response is NOT A STABLE CELL.** It is a projection of
   the *account's current* classification, not of the entry: the identical row renders `ASSET` in
   capture `A2-088` and `INCOME` in `A2-320`, **every other cell byte-identical**, with no entry
   edited. **A `ledger` vector that grades `glAccountType` from this endpoint will go red on a
   GL-account edit that touched no entry.** This was G-10's re-derived hazard; it is now an
   observation. **`A2-15` must treat `glAccountType` as excluded from the graded domain or as a
   separately-sourced cell, and §5.2 requirement 7 may not use it as the perturbation cell.**

### 5.1 No `ledger` vector is expressible against the frozen vector schema — MEASURED

**This is finding R-1, and revision 1's central claim about it —** *"Disposition 3 needs no new
machinery, and that is the argument for it"* **— was false.** Revision 2 retracts it. The
retraction is not a wording change: it inverts the argument for the disposition this section
recommends, so §5.2 re-argues that disposition on different grounds.

The store's admission machinery is a **loan-schedule** machine. Not a generic one with a
loan-schedule tenant in it — a loan-schedule one, in its schema string, its request type, its
expectation type, its comparator and its cell whitelist. Each of the five findings below was opened
in source by this task, and the section closes with three positive controls that were **run**.

**(1) The schema string names the context.** `VectorSchemaV1 = "gerege.loanschedule.vector/v1"` is
the **only** value the loader accepts, and it is checked before anything else [VERIFIED by this
task: `nexus/internal/apps/loanschedule/conformance/vector.go:16-18` declares it as *"the only
schema string this harness accepts"*; `admit.go:109-110` refuses any other]. A `ledger` vector
would have to declare itself a loanschedule vector in its first line.

**(2) `Request` has no field a `ledger` request could go in.** The type is thirteen fields —
`TimeZone`, `Currency`, `Rounding`, `ScheduleStartDate`, `Disbursements`, `NumberOfRepayments`,
`RepaymentEvery`, `RepaymentFrequencyUnit`, `AnnualNominalInterestRate`, `InterestMethod`,
`DayCount`, `DownPaymentPercentage`, `InstallmentRoundingMultipleMinor` [VERIFIED by this task:
`vector.go:345-419`, the struct read in full]. **Not one of §4.2's eleven predicates is about
anything in that list.** A `ledger` request is a product id, a placeholder code, a payment type id, a
product type, an accounting rule and a seam; the schema has a home for none of them, and decoding is
**strict** — an unknown field is a hard load failure, not an ignored key [MEASURED, positive control
1 below].

**(3) `Expect.Kind` is the closed set `{schedule, refusal}`, and `Expect.Sentinel` must be one of
the three CONTRACT sentinels.** [VERIFIED by this task: `vector.go:484-511` documents both;
`admit.go:208-222` is the `switch` whose `default` arm is *"expect.kind %q is neither \"schedule\"
nor \"refusal\""*; `enums.go:92-104` `sentinelByName` resolves exactly `ErrInvalidRequest`,
`ErrUnsupportedConfiguration`, `ErrNoDiscriminatingVector` and errors on anything else.]

**So §4.9's oracle-faithful 404 — the single commonest graded output this context has — has no
representation at all.** §4.9 is emphatic that these are **ANSWERS**, not contract refusals, and
that *"a port that returned `ErrNoDiscriminatingVector` where the oracle returns a 404 would
'refuse' a case that is in fact fully graded"*. The schema offers exactly two encodings and both are
wrong: `kind: "schedule"` is not what happened, and `kind: "refusal"` with any of the three
sentinels asserts the contract refused when in fact **the oracle answered**. Encoding it as a
contract refusal would write the §4.9 defect *into the corpus*.

**(4) There is no class the observed 404 can be filed under — and this is the hardest wall, harder
than revision 1 or its reviewer identified.** The three classes are mutually exclusive and jointly
closed [VERIFIED by this task, `admit.go:159-206`]:

| class | the rule that excludes an observed oracle 404 | source |
|---|---|---|
| `parity` | **"a parity vector must expect a schedule; a refusal is not an oracle observation"** — the check is `v.Expect.Kind != "schedule"` | `admit.go:545` |
| `contract-refusal` | requires `provenance.kind == "contract"` and **`oracle.seam == "none"`** — *"nothing was captured"* — and the sentinel must be one of the three | `admit.go:180-201`, `enums.go:93-103` |
| `selftest` | must live under `_selftest/`, must be hand-authored, **never counts toward parity** | `admit.go:160-170` |

Read together: **the schema's model of an oracle observation IS a schedule.** A refusal is, by
construction, something the *contract* did, derived from contract text, captured from nothing. That
is a coherent model of DEC-1's world and it has no room in it for a context whose oracle answers
"404, `error.msg.productToAccountMapping.not.found`" and where reproducing that string exactly *is*
parity.

**(5) `StructuralCellFields()` is a hard-coded whitelist of three, and it rejects all six cells
revision 1 proposed.** `func StructuralCellFields() []string { return []string{"kind", "from_date",
"due_date"} }` [VERIFIED by this task: `vector.go:647-649`]. Admission compares against it
literally, and refuses anything else with *"names field %q, which is not one of the non-money cells
this harness compares"* [VERIFIED: `admit.go:384-388`]. Revision 1's proposed
`resolved.account_id`, `resolved.gl_code`, `resolved.classification`, `refusal.code`,
`refusal.http_status`, `refusal.message` are **all six** outside it — and so is the `period[<n>].`
prefix the cell parser requires before it even looks at the field name [VERIFIED:
`admit.go:417-435`, `ParseDivergentCell`'s four-way form vocabulary].

**And the whitelist's own doc comment explains why widening it is not a one-line change.** The three
fields are *"exactly the NON-MONEY cells `diffSchedule` actually compares"*, and the stated reason
for the whitelist is that *"naming a cell the harness does not compare would let a vector claim a
kill nothing could ever detect"* — finding **T9-F1b**, which is the defect that once printed nine
killed capabilities at exit 0 over a store whose dates were garbage [VERIFIED by this task:
`vector.go:647-649` and the `StructuralKillIsCompared` comment at `:671-692`]. **A cell is
admissible if and only if some comparator compares it.** `diffSchedule` compares schedule rows.
Adding `resolved.gl_code` to this list without a comparator that compares GL codes would reintroduce
T9-F1b at the level of the harness itself — a whitelist that no longer means what it says.

#### The three positive controls, RUN

Revision 1 asserted machinery adequacy without exercising it. Revision 2 exercised it. Method: build
the real binary from `CMD_PKG` [`conformance.sh:411`], copy `.softhouse/vectors` to a temp store, add
a `ledger/` directory, author the vector, run `-context=ledger -oracle-probe=up`. **No file in the
repository was modified by any of this.**

| # | the vector | what the harness did |
|---|---|---|
| **PC-1** | a `ledger` vector written the way §4.9 and §5 actually need it: `schema: "gerege.ledger.vector/v1"`, request `{product_id, placeholder_code, payment_type_id}`, `expect: {kind: "oracle_refusal", sentinel: "HTTP404", http_status: 404}` | **not read as a vector at all.** `ledger/LEDGER-PROBE-404.json: decode: json: unknown field "product_id"`, listed under *"FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable)"*. Exit 2. |
| **PC-2** | the same case with every schema-forced field filled in with loanschedule filler, keeping only the three things this context actually needs | **INADMISSIBLE**, with the four refusals quoted below. Exit 2. |
| **PC-3** | the same case filed as `class: "contract-refusal"` — the only other class outside `_selftest/` | **INADMISSIBLE**: *"class \"contract-refusal\" requires oracle.seam \"none\": nothing was captured"* and *"expect.sentinel: \"ErrGLAccountMappingNotFound\" is not one of ErrInvalidRequest, ErrUnsupportedConfiguration, ErrNoDiscriminatingVector"*. Exit 2. |

PC-2's refusals, quoted verbatim from the run [MEASURED by this task]:

```
    a parity vector must expect a schedule; a refusal is not an oracle observation
    expect.kind "oracle_refusal_404" is neither "schedule" nor "refusal"
    graded_against[0] (...) divergent_cells[0] "period[0].gl_account_id" names field
      "gl_account_id", which is not one of the non-money cells this harness compares
      (kind, from_date, due_date). A cell the harness never compares cannot be the
      site of a kill anything could detect
```

**The harness is behaving correctly in every one of these. That is the point.** Nothing here is a
bug to be fixed; it is a machine doing exactly what it was built to do, to a vector from a context
it was never built for.

**But PC-3 was a FALSE NEGATIVE, and revision 2 read it as a wall. §5.1.1 is that retraction.**

### 5.1.1 RETRACTION — "no `ledger` vector CAN exist" was FALSE, and PC-3 is why it was believed

**This subsection is the whole of revision 2's rejection (`A2-19`, finding F1), and it is placed
here, inside §5.1, because §5.1's own heading was already carrying the correct claim while the
banner, §8.1 and §4.10 carried a stronger one.**

**What was claimed.** In three places, and asserted as *measured fact* rather than inference:

| site | revision 2's words |
|---|---|
| Banner, item 2 | *"**No `ledger` vector CAN exist.**"* |
| §8.1, fact 2 | *"**Zero `ledger` vectors CAN exist**"* |
| §4.10 (`A2-17`'s micro-fix) | *"…because §5.1 establishes that no `ledger` vector can be admitted **at all** until §5.3's P-1…P-5 exist."* |

**What is true.** §5.1's heading: **no `ledger` vector is EXPRESSIBLE** against the frozen vector
schema. That is what the five legs prove, an independent review re-opened all five at their exact
cited lines and confirmed them, and it is fully sufficient for §5.2's rejection of disposition (b).
**Admission-impossibility is strictly stronger than inexpressibility**, the five legs do not reach
it, and it is false.

**How it was falsified — MEASURED, and reproduced twice independently.** Copy any promoted
`loanschedule` parity vector into `.softhouse/vectors/ledger/`, change **only** `case_id` (to clear
the duplicate-id check) and `context` (to match its new directory), leave `capabilities_required`,
`graded_against`, `oracle.seam`, `provenance` and the recorded `sha256` **untouched** — and:

```
LEDGER-PARITY-PURE-A219      parity           path_a_e...  PASS             47        2
    parity vectors          PASS 44   FAIL 0
    cells compared          5711 graded, 89 ungraded (never recorded by the capture)
VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle, 5711 cells compared.
```

against **43 / 5664** for the same store without the copy.

| reproduction | by | figures |
|---|---|---|
| first | review task **`A2-19`**, temp store, binary built from `CMD_PKG`; raw transcript committed at `.softhouse/reviews/a2-19-dec2-rev2/E8-ledger-PARITY-counted-as-44.txt` | **44 parity / 5711 cells**, exit 0 |
| second | **the driver**, independently, with its own probe vector on `main`'s own bytes, before revision 3 was commissioned | **44 parity / 5711 cells**, exit 0 |

**The two agree to the digit.** The lighter form was measured too: the same copy of a
`contract-refusal` vector was admitted and passed, moving contract-refusal **4 → 5** and cells
**5664 → 5665**, also at exit 0.

**Two distinct harms, and the second is the worse one.**

1. **The headline number was inflatable by two string edits.** `44 parity vectors match the pinned
   reference oracle` is the sentence this entire program quotes as its evidence.
2. **The report claimed coverage that does not exist.** The 44th vector graded a **loan schedule**
   while sitting in `ledger/` and printing a `ledger`-context row with `PASS` on it — which is
   precisely the false green DEC-2 is being written to prevent.

**The cause was one missing check, not a design flaw.** `context` was constrained **only** to be
non-empty and to equal its own directory name [VERIFIED by this task at
`nexus/internal/apps/loanschedule/conformance/admit.go:115-117` (`context is empty`) and `:119-120`
(*"context %q does not match the directory %q the file lives in"*)]. Both constraints are satisfied
by `cp`. **No allowlist of context names existed anywhere in the package.**

**Why revision 2 believed it: PC-3 was a FALSE NEGATIVE — pattern P-50.** The strong claim rested
on positive control **PC-3** above, *"the same case filed as `class: "contract-refusal"`"*,
reported INADMISSIBLE. Read PC-3's own quoted refusals: it failed on **two author-correctable
defects**, not on a structural wall —

- `expect.sentinel: "ErrGLAccountMappingNotFound" is not one of ErrInvalidRequest,
  ErrUnsupportedConfiguration, ErrNoDiscriminatingVector` — the author chose a non-contract
  sentinel; the schema already offers three legal ones.
- `class "contract-refusal" requires oracle.seam "none": nothing was captured` — the author set a
  seam; the schema already requires `none` for that class.

Correct both, as the schema itself instructs, and the vector is **admitted**. **`A2-16` built a
control that failed and read it as a wall; `A2-17` re-derived the argument but did not re-run the
corrected control.** That is **P-50** exactly: *a prover must be falsifiable in the direction of the
FIX, not only in the direction of the defect.* PC-3 could only ever go red, so its red was read as
proof. **PC-3 is hereby reclassified from "a positive control that establishes a wall" to "a
demonstration that an incorrectly-authored vector is refused" — which is a much weaker statement
and is all it ever supported.**

**The hole is CLOSED — by `A2-20`, after the claim was made, and closing it does not rescue the
claim.** `SchemaContexts()` now returns the complete set of contexts a `gerege.loanschedule.vector/v1`
vector may claim — `{_selftest, loanschedule}` — and `admit.go` refuses any other as **INADMISSIBLE**
[VERIFIED by this task: `vector.go:31-81` declares and documents it; `admit.go:139-147` is the
refusal; `IsSchemaContext` at `vector.go:83-91`]. **Both** shapes are now refused: the parity form
and the `contract-refusal` form, and the refusal lives at **admission** rather than at the
comparator precisely because a `contract-refusal` vector consults no comparator at all — a check
phrased as *"the comparator for this class does not exist"* would have let the second form straight
through. `A2-21` re-ran the unfiltered harness on its own tree and reproduced the then-current
baseline exactly: **`VERDICT: PASS (exit 0) — 43 parity vectors … 5664 cells`**, contract-refusal
`PASS 4`, self-test `PASS 1`, `refused 0`, `inadmissible 0`, `invariant violations 0`, probe line
present and reading `up` [MEASURED by `A2-21` on a 43-vector store; **superseded**]. **`A2-28`
re-ran it at commit `2e97162` and reproduces the same SHAPE at the current corpus size:
`VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`, contract-refusal `PASS 4`, self-test
`PASS 1`, `refused 0`, `inadmissible 0`, `invariant violations 0`, probe = `up`** [MEASURED by
`A2-28` at commit `2e97162`; §5's stamped baseline]. The parity and cell counts moved because
`T116` promoted three vectors; **the four figures that carry the argument — refusal 4, self-test 1,
refused 0, inadmissible 0 — did not.**

**What this retraction does NOT change**, so that a reader does not over-correct:

- **§5.1's five legs all stand.** All five were re-opened at their exact cited lines by an
  independent review and confirmed.
- **§5.2's rejection of disposition (b) stands**, because it rests on inexpressibility, not on
  inadmissibility. The intersection is still empty.
- **§5.3's preconditions stand** (as re-ordered in revision 3).
- **§5.4's retraction and its measurements stand** — independently reproduced.
- **The falsifying vector graded NOTHING about the ledger.** It was a loanschedule capture in a
  ledger costume. DEC-2's substantive position was never the thing that was wrong; the *statement*
  of the wall was, and it was overstated in the unsafe direction.

**And the discipline this records, because it is the reason the sentence is retracted rather than
quietly reworded.** A silent downgrade from *"CAN exist"* to *"is expressible"* would leave the next
reader unable to tell that a measured green `PASS 44` ever happened, or that a positive control
failed for the wrong reason and was believed. **The failure class this program keeps catching is a
check that cannot fail (P-22), reached through a prover that was never made falsifiable toward the
fix (P-50).** Both are on the record here, named.

### 5.2 The decision: EXTEND the machinery — and DEC-2 grades nothing until it exists

Two dispositions were open. **(a) extend the vector schema**, which is real machinery and must stop
being implied to be free; or **(b) restrict DEC-2 to grading only what the schema can already
express.**

**(b) is rejected, and the argument is short because the arithmetic is short: the intersection is
empty.** §5.1 (2) shows no `ledger` *input* has a field; §5.1 (3) and (4) show no `ledger` *output*
has an encoding or a class. So "grade only what the schema expresses" is not a narrower DEC-2 — it
is a DEC-2 that grades **zero** predicates and admits **zero** vectors, while §0's entire stated
purpose is to give `A2-15` something to build a grader against. A contract that can never be graded
is not a weaker contract; it is a memo.

**(a) is adopted. The machinery is named, it is not built here, and this document does not pretend
it is anywhere else either.** Three things follow, and revision 2 states all three as normative.

**First — the extension is a SECOND vector schema and a SECOND comparator, not a widening of the
first.** This is a design decision this task takes, with the alternative recorded:

- *Rejected: widen `gerege.loanschedule.vector/v1` in place* — add `ledger` fields to `Request`,
  a third `Expect.Kind`, `ledger` cells to `StructuralCellFields()`. Three reasons.
  **(i)** `StructuralCellFields()`'s safety property is *"exactly the non-money cells `diffSchedule`
  actually compares"*; a union list covering two comparators is a superset of what either compares,
  which is precisely T9-F1b (§5.1 (5)). **(ii)** `sentinelByName` returns
  `contract.Err*` values imported from `nexus/internal/apps/loanschedule/contract` [VERIFIED by this
  task: `enums.go:93-103`, `registry.go:11`], so **a fourth sentinel means editing the frozen
  `contract.go` — a DEC-1 amendment and a hard `user` gate.** Revision 2 does not go near it.
  **(iii)** the whole grading pipeline is typed on `contract.ScheduleGenerator` / `contract.Schedule`
  and every vector's request is mapped through `Request.ContractRequest()` onto the frozen DEC-1
  request [VERIFIED by this task: `registry.go:26-28` declares `impls map[string]contract.ScheduleGenerator`; `grade.go:561` and `registry.go:173` both route every vector through `v.Request.ContractRequest()`]. Widening the schema without
  widening those types produces a vector nothing can be asked to answer.
- *Adopted: a `ledger`-specific schema (`gerege.ledger.vector/v1`) with its own `Request`, its own
  `Expect`, its own comparator and its own cell whitelist*, sharing the store root, the file census,
  the duplicate-case-id check, the raw-token float scan and the capability registry. Shared where
  the property is about **the store**; separate where the property is about **what a comparator
  compares**.

**Second — and this constrains the extension absolutely: the WHOLE `loanschedule` corpus must still
pass, unchanged, at whatever size it is on the day.** The extension touches the same harness DEC-1's
promoted parity vectors depend on, and those vectors are the only parity evidence this program has.
**A `ledger` extension that costs one of them is not a trade this contract permits.**

> **⚠ THE BUILDER MEASURES THE BASELINE; IT IS NOT COPIED OUT OF THIS DOCUMENT.** Revisions 2 and 3
> wrote the literals `43` and `5664` into requirements 1, 2 and 6. **Both were correct when written
> and both are wrong now** — `T116` promoted three vectors and the corpus is `46 / 7884 / 50 files`
> at commit `2e97162` (§5's stamped baseline). A literal in a normative requirement rots into an
> instruction a conscientious builder cannot obey. **So requirements 1, 2 and 6 are phrased against
> `B`, the baseline the builder measures IMMEDIATELY BEFORE its first edit, in its own working
> tree.** The demand is unchanged and is not weakened by this: it is *"the number does not move
> across your change"*, and `A2-25` confirmed by measurement that the harness distinguishes `43`
> from `44` today, so a builder who files ledger vectors into the parity count **will** show an
> inflated `B` and be caught. **`B` must be recorded in the submission**, with the commit it was
> taken at, alongside the `A2-28` figures so a reviewer can see what moved and why.

The demonstration required of whoever builds it, stated so it cannot be improvised:

1. **Before/after digests of EVERY `.json` file under `.softhouse/vectors/loanschedule/` — the
   DIRECTORY, not a count, and not just the parity subset.** At `2e97162` that is **50** files:
   **46** `class: parity` and **4** `class: contract-refusal` [MEASURED by `A2-28`]. Revision 3 said
   *"all 43 vector files"*, which would have left the **four contract-refusal vectors unprotected**
   — and the contract-refusal form is **the second falsification shape §5.1.1 records** (`4 → 5`,
   `5664 → 5665`), independently reproduced by `A2-25`. **The set to protect is the directory
   listing, taken fresh; a builder who digests a fixed count has already lost the file that count
   omits.** A second schema string means no existing vector file changes a byte; if any digest
   moves, the extension has widened the first schema and is out of bounds.
2. **`bash .softhouse/conformance.sh` unfiltered, before and after**, both reporting `VERDICT: PASS
   (exit 0)` with `parity vectors PASS <B.parity> FAIL 0`, `contract-refusal PASS <B.refusal>`,
   `self-test PASS <B.selftest>` and **the same cell count `<B.cells>`** — where every `<B.…>` is
   read off the builder's own **before** run and not off this page. **The `A2-28` reference values,
   for orientation only and expected to be stale:** `46 / 4 / 1 / 7884 graded, 93 ungraded`, store
   `73c3ea7b43dd75f04884072719a87fc8e1d255c1` [MEASURED by `A2-28` at commit `2e97162`]. A cell
   count that moves means the comparator changed under the loanschedule corpus, which is a
   regression whatever the verdict line says.
3. **`bash .softhouse/conformance.sh loanschedule` before and after**, identical but for
   timestamps.
4. **No diff to `nexus/internal/apps/loanschedule/contract/contract.go`, and no DEC-1 amendment.**
   If the extension turns out to require either, that is a hard `user` gate — **raise it, do not
   make it.**
5. **Invoke with `bash`, never `sh`** — exit 3 is a wrong-interpreter refusal, not a failure — and
   never `gofmt -w` `contract.go`; `gofmt -l` reporting exactly that one file is the expected state
   (standing instruction, **G-3 CLOSED-OPTION-A**).

> **⚠ REQUIREMENTS 1–5 ARE PURE NON-REGRESSION, AND REVISION 3 ADDS 6 AND 7 BECAUSE OF IT.** This is
> `A2-19`'s finding **F2**, and it is the failure class this program has paid for more than any
> other. **Every one of requirements 1–5 is satisfied by a builder who adds nothing at all.** A dead
> second schema no vector uses, a comparator nothing calls, an empty file — all five pass perfectly,
> because all five are *guards against change*, and doing nothing changes nothing. There is no
> requirement in 1–5 that the new machinery be demonstrated to **work**. **P-22: a control that
> cannot fail is worse than none, because it is believed. P-35: a check that inspected zero items is
> an ERROR, not a pass.** The program has already paid for this twice — `T9-F1b` printed nine killed
> capabilities at exit 0 over a store whose dates were garbage, and `T156` was the red/green exit
> trap. Requirements **6** and **7** are therefore **normative and not optional**: a submission that
> satisfies 1–5 and not 6–7 **has not satisfied §5.2**, and a reviewer should read it as an
> extension that does nothing.

6. **POSITIVE CONTROL — the extension must NEWLY DO something today's harness demonstrably does
   NOT.**

   > **⚠ REVISION 4 REWRITES THIS REQUIREMENT'S "BEFORE", BECAUSE REVISION 3's COULD NOT BE
   > SATISFIED ON THE BYTES IT SPECIFIED. This is `A2-25`'s F-3 and it was reject-grade.**
   > Revision 3 named the bytes (a `gerege.ledger.vector/v1` file carrying a genuine `ledger`
   > request) and then mandated that the demonstration quote **two specific refusals** — the schema
   > check and the context allowlist. **`A2-25` authored exactly that vector and ran it. Neither
   > mandated refusal fires.** `A2-28` reproduced it independently at commit `2e97162` on a temp
   > store, quoting the diagnostic and the surviving population and never the exit code (**P-62**):
   >
   > ```
   > --- FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable) ---
   >     ledger/LEDGER-REQ6-BEFORE.json: decode: json: unknown field "product_id"
   >
   >     parity vectors   PASS 46   FAIL 0
   >     inadmissible     0
   >     cells compared   7884 graded, 93 ungraded
   > ```
   >
   > **The file dies at STRICT JSON DECODE and never becomes a `*Vector`**, so `admit.go:109-110`
   > and `admit.go:139-147` are both unreachable for it and `inadmissible` stays **0** — the
   > requirement's own headline, *"a `ledger` vector is INADMISSIBLE"*, is not what the harness
   > reports either. **The only bytes that emit both mandated refusals together are a
   > loanschedule-shaped vector wearing a ledger costume** — `A2-28` planted one and got exactly
   > that, `schema "gerege.ledger.vector/v1", want "gerege.loanschedule.vector/v1"` and
   > `context "ledger" is not a context this harness grades`, `inadmissible 1`, parity still `46`
   > [MEASURED by `A2-28` at commit `2e97162`, second temp store]. But **those bytes carry a
   > `loanschedule` request**: they are §5.1.1's own retracted defect, they demonstrate nothing about
   > a second schema, and under §5.2's adopted design they could never be the AFTER subject.
   > **So revision 3 bound BEFORE and AFTER to "the same bytes" and no single set of bytes satisfied
   > both halves.** A conscientious `A2-15` would have hit an impossible instruction and improvised,
   > and the nearest satisfiable improvisation is the costume file — **the requirement written to
   > close the vacuous-control hole re-opened it through its own text** (**P-22** at one remove).
   >
   > **Revision 4 fixes it by making the BEFORE demand the refusal the bytes ACTUALLY produce, not
   > by loosening the evidence.** A strict-decode load failure is a stronger BEFORE than an
   > admission refusal, not a weaker one: the bytes do not even parse. **The AFTER half is kept
   > verbatim in substance** — `A2-25` judged it strong and genuinely falsifiable and confirmed the
   > harness distinguishes `43` from `44` today — with only the stale literals replaced by the
   > measured baseline `B` of requirement 2. **The two admission-layer refusals are NOT dropped;
   > they are moved into 6b, which fires on its own bytes and says so.**

   **6a — SAME BYTES, BEFORE AND AFTER. This is the positive control proper, and both halves must
   be shown on one file.**

   - **BEFORE (today, on the builder's own tree): the bytes are REFUSED AT LOAD.** Author the vector
     the extension is meant to make legal — a `gerege.ledger.vector/v1` file under
     `.softhouse/vectors/ledger/` carrying a `ledger` request (product id, product type, accounting
     rule, slot family, slot code, payment type id, seam) and a `ledger` expectation. On today's
     harness it must be reported under **`FILES THAT COULD NOT BE READ AS VECTORS (each one makes
     this run unusable)`**, carrying `decode: json: unknown field "<the first ledger-only field the
     decoder meets>"`, with **`inadmissible 0`** and the loanschedule population intact at `B`.
     **Quote the diagnostic line and the surviving population; never the exit code** — `exit 2` is
     overloaded across at least five distinct conditions (**P-62**), so an exit code proves nothing
     about *which* refusal fired.
   - **This BEFORE is REACHABLE, and it was MEASURED before being demanded.** The transcript in the
     box above is `A2-28`'s, taken on the exact bytes this bullet specifies. **A requirement in this
     document may not demand evidence nobody has produced; that is the defect this bullet replaces.**
   - **AFTER: the same bytes are ADMITTED, GRADED and reported.** The per-vector table must carry a
     `ledger`-context row, and the summary must report the ledger vector **under its own comparator
     and its own count** — *not* folded into `parity vectors PASS <B.parity>`. **The loanschedule
     parity count must still read exactly `B.parity` and the cell count exactly `B.cells`**, which
     is what requirement 2 already demands and what makes 6 and 2 jointly meaningful: 6 proves
     something new is graded, 2 proves nothing old moved. **A submission where `B.parity` becomes
     `B.parity + 1` has reproduced the defect §5.1.1 retracts**, and the harness is known to be able
     to show that difference [`A2-25` measured the 43/44 discrimination; `A2-28` re-confirmed that
     an inadmissible ledger file leaves the parity count at 46].

   **6b — THE ADMISSION-LAYER REFUSALS, ON DIFFERENT BYTES, AND THIS IS STATED EXPLICITLY.**

   - The two refusals revision 3 mandated **are real and they matter** — they are what closed
     §5.1.1's hole — but they fire on a **loanschedule-decodable** file claiming an unknown context,
     which is a *different file* from 6a's. **Plant that file too**, and quote both refusals
     together: the schema check (`admit.go:109-110`, a vector whose `schema` is not
     `gerege.loanschedule.vector/v1` is INADMISSIBLE) and the context allowlist
     (`admit.go:139-147`, `SchemaContexts()` = `{_selftest, loanschedule}`), with
     **`inadmissible 1`** and the parity count unmoved.
   - **6b's file is NOT 6a's, cannot be 6a's, and is not the AFTER subject.** It is §5.1.1's
     relabelled-vector shape and it grades nothing about the ledger. Its purpose is narrow and
     stated: to show the builder has not weakened the allowlist while adding a schema beside it.
   - **What 6b becomes after the extension is a design question the builder must answer in writing,
     not silently.** Once `gerege.ledger.vector/v1` is a real schema, a file bearing it is no longer
     *"a vector whose schema is not `gerege.loanschedule.vector/v1`"*; it is a vector of the other
     schema, and `admit.go:109-110` is the wrong refusal for it. **P-9** is exactly this obligation
     transferring: the second schema declares its own contexts and refuses the rest. **State which
     refusal 6b's bytes hit after the change and why it is still the right one.**

   - **The `_selftest/` corpus is not a substitute for either half.** A self-test fixture is
     hand-authored and is excluded from the parity count by construction (`admit.go:160-170`); it
     demonstrates that the comparator *runs*, never that a promoted `ledger` vector is admissible.

7. **REQUIRED RED DEMONSTRATION — the new comparator must be shown to GO RED, on a defect it is
   supposed to catch, and GREEN on the pristine bytes.** Exactly one arrangement of the world may
   pass. State all four cells of the matrix, and a submission missing any one of them is incomplete:

   | | pristine expectation | perturbed expectation |
   |---|---|---|
   | **correct implementation** | **GREEN** — required | **RED** — required |
   | **named wrong implementation** (`graded_against`) | **RED** — required | not required |

   > **⚠ REVISION 4 CLOSES A DISJUNCTION THAT MADE THE MONEY HALF OPTIONAL. This is `A2-25`'s F-8,
   > and it is the finding `A2-25` most wanted a ratifier to weigh.** Revision 3's perturbation
   > clause read *"a resolved `gl_code`, a resolved account id, a refusal's HTTP status or error
   > code, **or** a money cell"*, and every money constraint that followed was **conditional** on
   > having chosen money (*"Perturb by one minor unit **where the cell is money**"*). **So a builder
   > could perturb `gl_code`, satisfy requirement 7 in full, and ship a `ledger` extension whose
   > money comparator had never once been driven red.** §5.3's **P-5** requires money cells to
   > *exist*; nothing required them to be *exercised*. Since §4.4 establishes that `I-1` and `I-2`
   > are the only two ledger invariants anything in this program could ever grade, and §5.5 warns
   > that *"a `ledger` corpus whose money cells only ever kill structurally has graded no amount"*,
   > that left the money path in exactly the vacuous class (**P-22**/**P-35**) requirement 7 exists
   > to close. **`A2-26` makes it concrete rather than theoretical: before this fire every ledger
   > amount in the A2 corpus was a whole tugrik, so a port that dropped minor units was
   > byte-indistinguishable from a correct one on every capture ever taken** (§5.0.1). **The
   > disjunction is replaced by a conjunction below.**

   - **AT LEAST TWO perturbations are required, one of each kind, and neither substitutes for the
     other:**
     - **(i) one STRUCTURAL cell** — a resolved `gl_code`, a resolved account id, or a refusal's
       HTTP status or error code; **and**
     - **(ii) one MONEY cell, perturbed by exactly ONE MINOR UNIT**, in `int64` minor units
       (**P-5**), reported as a **money** kill with a **non-zero `margin_minor`**.

     A comparator that only detects large divergences is not a comparator, and DEC-1's own history
     (a one-minor-unit error in period 5 that never heals) is the argument. **A submission with no
     money perturbation has not satisfied requirement 7**, whatever else it shows.
   - **Each perturbation must be a single cell, and it must be a cell §4.2 or §4.4 makes normative.**
     Perturbing a field the comparator does not compare demonstrates nothing, and is the shape of
     **T9-F1b**: a whitelist that no longer means what it says.
   - **`glAccountType` MAY NOT be the perturbation cell**, and may not be promoted as a graded cell
     from `/journalentries` at all without a separate source: `A2-26` observed the identical row
     rendering `ASSET` in one capture and `INCOME` in another with every other cell byte-identical
     and no entry edited, because the field projects the *account's current* classification rather
     than the entry's (§5.0.1). **A red on an unstable cell is not a demonstration that the
     comparator works; it is a demonstration that the corpus is not reproducible.**
   - **The money perturbation must be RED for a MONEY reason.** The transcript must show the
     divergence reported as a **money** kill with a non-zero `margin_minor`, not as a structural cell
     difference. §5.5 is explicit that the harness prints that distinction for a reason (finding
     D-4), and a `ledger` corpus whose money cells only ever kill structurally has graded no amount.
   - **RED must be shown by the DIAGNOSTIC, not by the exit code (P-62).** Quote the failing cell,
     the expected and actual values, and the vector's `case_id`. An empty or unloadable corpus exits
     with the same code as a correctly-detected divergence.
   - **The `graded_against` row must kill something.** §5.5's rule applies from the first vector: *a
     capture that kills nothing is a capture, not a grader*. The RED in the bottom-left cell is what
     licenses the corresponding `capabilities.json` row to flip to `in_graded_domain: true` under
     §5.4 step 3, and nothing else does.
   - **The demonstration itself must be falsifiable toward the fix (P-50).** Assert internally that
     the pre-fix bytes drive the battery **RED** *and* the post-fix bytes drive it **GREEN**, so the
     prover cannot be read as healthy while the defect is present. A prover that passes because the
     bug is there is a demonstration, not a regression test.

   > **⚠ THE BOTTOM-LEFT CELL NEEDS A MECHANISM §5.3 DOES NOT YET NAME. This is `A2-25`'s F-9, and
   > revision 4 closes it with a new precondition rather than by softening the cell.** The matrix
   > demands **RED against the named wrong implementation**. In this harness `graded_against` is a
   > **declarative record** — `type Counterfactual struct { ID, Capability, Description, Kind,
   > DivergentCells, MarginMinor … }` [VERIFIED by `A2-28` at commit `2e97162`: `vector.go:542-…`;
   > admission validates the declaration's **shape**, and nothing in the grading path executes a
   > wrong implementation from it]. Driving a *real* wrong implementation red needs either the
   > **registry route** (`registry.go:34` `Register`, `Lookup`, the binary's `-impl` flag) or a
   > mutation harness. **No §5.3 precondition named either for `ledger`** — P-1…P-9 cover schema,
   > `dec1_revision`, refusal expectation, class, comparator, money cells, the `capabilities.json`
   > decision, the guard and the context binding — **yet §8.2 tells `A2-15` it "cannot start without
   > them".** The list was incomplete relative to §5.2's own requirement 7. This errs **strict**, so
   > it created no vacuous guard, but it would have surfaced as an argument during `A2-15`.
   > **Revision 4 adds precondition P-10 (§5.3) and requirement 7 now points at it.**

   - **NAME THE MECHANISM BEFORE CLAIMING THE BOTTOM-LEFT CELL.** State which of the two routes the
     submission uses — a `ledger` implementation registered under a name and selected with `-impl`,
     or a mutation harness — and **quote the transcript in which the named wrong implementation is
     actually run and actually goes red.** A `graded_against` row is a *claim* that a wrong
     implementation would be killed; it is not that killing. **A submission that presents the
     declaration as the demonstration has not filled the bottom-left cell** (§5.3 **P-10**).

**Requirements 6 and 7 are what make 1–5 mean anything.** 1–5 say *"you broke nothing"*; 6 and 7 say
*"you built something, and it can tell right from wrong"*. **Neither half is sufficient alone**, and
revision 2 shipped only the first half.

**Third — Disposition 3 survives, on a different argument.** Three dispositions were open on
ratification-versus-vectors, carried forward from revision 1 unchanged:

1. **Ratify now and promote later.** Rejected: §4.2's predicates cite captures as evidence, and a
   predicate justified by an unpromoted capture is a promise, not a grading.
2. **Refuse to ratify until vectors exist.** Rejected: **a vector cannot be promoted against a
   contract that does not exist** — that is §0, and it is a deadlock. §5.1 makes it a *harder*
   deadlock than revision 1 knew: not only is there no contract to promote against, there is no
   schema to write the promotion in.
3. **Ratify the contract, and require the FIRST promotion task to promote at least one parity vector
   per `in_graded_domain: true` capability in §4.10 before the `ledger` context may be reported as
   graded at all.** **Recommended.**

**But the argument for 3 is NOT "it needs no new machinery" — that was revision 1's argument and it
was false.** The argument is: **the machinery it needs is bounded, nameable and separable (§5.3), and
the alternatives are a deadlock (2) or an unbacked claim (1).** Disposition 3 is the only one that
lets the boundary be written down now and the grading arrive later without either pretending in the
meantime — *provided* this document says plainly, everywhere a reader could be misled, that the
grading has not arrived. That proviso is what §8.1, §4.4.1, §4.9 and the banner are for.

It remains a **recommendation to the ratifier**, not a decision this task may take.

### 5.3 Preconditions on `A2-15` — RE-ORDERED in revision 3, and one of them has since LANDED

`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.

**THE IDENTIFIERS ARE STABLE; THE ORDER IS THE NORMATIVE PART.** `P-1`…`P-10` are referred to by name
from §4.10, §5.2, §5.4, §5.5, §8.2, the harness source and several task handoffs, so neither
revision 3 nor revision 4 renumbers them; revision 4 appends **P-10** and touches no other id. It re-orders the table, and the **DEPENDS ON** column is what a builder
schedules against.

| order | # | precondition | why, in one line | depends on |
|---|---|---|---|---|
| **1st** | **P-6** | A **decision on `capabilities.json`** — its schema id is the hard constant `gerege.loanschedule.capabilities/v1` and `dec1_revision` is singular [VERIFIED by this task: `capabilities.json:2-3`]. Appending `ledger` rows works today, but the file is named and versioned for one context | §4.10; **not DEC-2's decision to take**, and it must not be improvised. **MOVED TO FIRST in revision 3** — see the adjudication below | — |
| **2nd** | **P-1** | A **`ledger` vector schema** with a request shape covering product id, product type, accounting rule, slot family, slot code, payment type id and seam | §5.1 (2) — strict decode rejects every one of them today | P-6 |
| **3rd** | **P-7** | **RE-SCOPED in revision 3.** What `dec1_revision` a **non-`loanschedule`** vector declares, given that it is checked per-vector against the single store pin [VERIFIED by this task: `admit.go:149`, `if v.DEC1Revision != pin.DEC1Revision`]. A `ledger` vector asserting `dec1_revision: 12` is asserting a **`loanschedule`** contract revision, which is semantically wrong | the question is real; the premise revision 2 gave for it was not — see the adjudication below | P-1 |
| **4th** | **P-2** | An **expectation shape for an oracle-faithful refusal** — HTTP status, error code, message text — that is **not** one of the three contract sentinels and is **not** confusable with them | §5.1 (3), §4.9(b); this is the context's commonest graded output | P-1 |
| **4th** | **P-3** | A **class** an observed non-schedule oracle answer can be filed under, since `parity` requires a schedule and `contract-refusal` requires `oracle.seam == "none"` | §5.1 (4) — the hardest of the five | P-1 |
| **4th** | **P-4** | A **comparator** for `ledger` outputs, and a **cell whitelist derived from it** rather than authored beside it | §5.1 (5); the whitelist's meaning is "what the comparator compares" (T9-F1b) | P-1 |
| **4th** | **P-5** | **Money cells** — `int64` minor-unit **strings**, paired with the oracle's own emitted characters as a transcription cross-check only | §4.3, T186 (c); required for `I-1`/`I-2` to be gradeable at all | P-1, P-4 |
| **5th** | **P-9** | **NEW in revision 3.** The `ledger` schema must **declare its own contexts** and the store must refuse a vector whose `context` is not one its schema, comparator and capabilities belong to | §5.1.1 — without this the parity count itself is not context-safe, which is how `43` became `44`. **`A2-20` has discharged the `loanschedule` half** (`SchemaContexts()`, `vector.go:31-81`; `admit.go:139-147`); the obligation transfers to the second schema, which is not written | P-1, P-4 |
| **5th** | **P-10** | **NEW in revision 4.** A **mechanism that actually RUNS a named wrong implementation and shows it going red** — either a `ledger` implementation registered under a name and selected with the binary's `-impl` flag (`registry.go:34` `Register`, `Lookup`), or a mutation harness. **`graded_against` is a DECLARATIVE record and does not execute anything** [VERIFIED by `A2-28` at commit `2e97162`: `vector.go:542-…`; admission validates the declaration's shape only] | `A2-25` F-9. §5.2 requirement 7's matrix demands **RED against the named wrong implementation** and §8.2 tells `A2-15` it cannot start without the preconditions — but no precondition named the mechanism that cell needs. **Without this, the bottom-left cell is satisfiable by writing a JSON row**, which is P-22 in the one place §5.2 was written to close it | P-1, P-4, P-5 |
| **—** | **P-8** | **LANDED.** The **`I-3`/`I-4` source guard** §4.4.1 requires | **Built by `A2-18`, wired by `T208`**; it runs on every invocation and `A2-28` measured `invariant violations 0` at commit `2e97162`. Its four residual **blind spots** are §4.4.1's, and **four of its declared detection classes — `I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`, `OPAQUE-SQL` — inspected an empty population** in this tree (**P-35**); revision 4 said *"three … of seven"* here and `A2-32` MEASURED `I4-BUILDER`'s population as zero. *Blind spots and detection classes are different quantities; conflating them is what §4.4.1's P-67 box records.* | **independent of all the above — that independence is what licensed it to be built first** |

**Nine open, one landed.** P-6, P-1, P-7, P-2, P-3, P-4, P-5, P-9 and **P-10** remain; **P-8 is
done** and is kept in the table with its residue rather than deleted, so that a later reader can tell
"discharged, with limits" from "never required". **Revision 4 adds P-10 and renumbers nothing** — the
identifiers are referenced from six sections, the harness source and several handoffs, and the same
rule that protected P-1…P-9 in revision 3 protects them here.

**THE ADJUDICATION ON P-6 AND P-7 — revision 3 applies `A2-19`'s ruling, and states both halves.**

`A2-17` proposed that **P-6 and P-7 both** be decided **before** P-1…P-5. `A2-19` adjudicated: the
proposal is directionally right, it **bundles two unlike things**, and the bundle is **SPLIT**.

- **P-6 moves FIRST. Accepted, and the third reason is decisive.** (i) The file is **shared by
  design** — §5.2's adopted disposition names "the capability registry" as one of the five things
  the second schema shares, so the registry is explicitly *not* separable from the extension.
  (ii) **DEC-2 itself declines to decide it**: §4.10's closing paragraph refuses to add a fifth
  status because "`capabilities.json`'s schema is shared with the `loanschedule` context … which is
  not DEC-2's to make". (iii) **§5.4's NORMATIVE SEQUENCING RULE cannot be obeyed without it.** Step
  2 of that rule says rows are authored `in_graded_domain: false` **first**. A builder cannot author
  a single row — not even a `false` one — without knowing whether `ledger` rows live in this file or
  in another. **P-6 blocks step 1 of the rule that is itself supposed to come first**, which is a
  real ordering inversion. §5.1.1 strengthens this: the store-level files are the natural chokepoint
  at which a context/schema/capability mismatch is refusable, which is what makes P-9 closable.
- **P-7 does NOT move, and its premise is retracted.** Revision 2 gave P-7's rationale as *"a second
  context implies a second pinned contract file, and the pin has one slot."* **§1.1 contradicts that
  premise, and this task re-opened §1.1 to confirm it before acting**: §1.1 states that this ADR
  *"does not create or freeze a Go file, and could not"*, that *"there is no counterpart file for
  this context"*, that *"this ADR deliberately writes no Go"*, and the status block states that **no
  PIN digest appears in this document at all**. There is **no second contract file to pin**, and
  there will not be one until a `ledger` contract is frozen — a separate, later gate. What *does*
  need deciding is narrower: **what contract revision a non-`loanschedule` vector declares.** That
  question **depends on** P-1 fixing the ledger vector's shape rather than blocking it, so P-7 is
  re-scoped and placed **after P-1**.

**Adjudicated sequencing, which is what the table above encodes:**

```
P-6  ->  P-1  ->  P-7 (narrowed to the dec1_revision question)
         P-1  ->  P-2, P-3, P-4, P-5  ->  P-9
                  P-4, P-5            ->  P-10 (the run-a-wrong-implementation mechanism)
P-8  ->  LANDED (A2-18 / T208); it was independent of every one of the above,
         which is exactly why it could be, and was, built first
```

**P-1 through P-5 are the schema extension. P-6 and P-7 are decisions. P-9 is the context binding.
P-10 is the mechanism §5.2 requirement 7's bottom-left cell needs and revision 3 never named.
P-8 was independent of all of them** — a guard over the Go tree, writable against the ported package
that already existed — **and it has now been written.**

### 5.4 What actually enforces Disposition 3 in the DEFAULT run — R-2, corrected and MEASURED

**Revision 1 claimed *"An empty context directory is already FATAL, and is not silent."* That claim
is FALSE, and revision 2 retracts it.** The narrower sentence beside it — that the fatal *names the
context-filtered path*, so `conformance.sh ledger` over an empty `ledger/` cannot pass — is **true**.
Revision 1 presented the two as one argument. They are not, and the difference is the difference
between an enforcement and nothing.

**The mechanism, re-read in source by this task:**

- **The fatal is guarded on the WHOLE returned vector set, not on the requested directory.**
  `if len(vectors) == 0 { … "ZERO VECTORS FOUND under %s" … }`, and `where` is the store root unless
  a context filter was given [VERIFIED by this task: `grade.go:373-379`].
- **`LoadStore` returns ALL contexts when the filter is empty:** `if contextFilter == "" { return
  all, loadErrs, nil }` [VERIFIED by this task: `vector.go:1016-1018`].
- **`conformance.sh` passes `-context` only when it was given an argument:**
  `[ -n "$context" ] && args+=("-context=$context")` [VERIFIED by this task:
  `.softhouse/conformance.sh:1254`].

So on the default invocation `len(vectors)` is the whole store, the fatal never fires, and the third
fatal — `NO PARITY VECTOR WAS GRADED`, `ParityPass == 0 && len(vectors) > 0` [`grade.go:478-480`] —
is inert for the same reason, because `ParityPass` is non-zero.

**RE-MEASURED by `A2-28` at commit `2e97162`** — the binary built from `CMD_PKG`, a temp copy of the
store in `/tmp`, an empty `ledger/` directory added, `.softhouse/vectors/` never written to. **Both
of revision 2's results reproduce; only the corpus figures moved:**

| run | result |
|---|---|
| unfiltered — **what `conformance.sh` performs** | **exit 0**, `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared`. **The string "ledger" occurs exactly ONCE in the entire output** — `grep -c` returned `1` — **and it is the no-float census line `covered: nexus/internal/apps/ledger`**, a statement about the Go source tree, not about a vector. No warning. No zero-count. Nothing. |
| `-context=ledger` | exit 2, `VERDICT: UNUSABLE`, `ZERO VECTORS FOUND under /tmp/…/ledger: an empty vector set is exit 2` |

**An empty `ledger/` therefore passes silently, and it does so in the run everybody quotes.**

**The leg that DOES hold, and it is a strong one — RE-MEASURED.** The capability fatal is
**registry-wide**: `CounterfactualCoverage` ranges over `r.GradedCapabilities()`, the whole registry,
with no context scoping anywhere in it [VERIFIED by `A2-28` at commit `2e97162`:
`capability.go:262-300`]. `A2-16` appended one experimental row to a **temp copy** of
`capabilities.json` and re-ran unfiltered; **`A2-28` repeated the experiment with its own row and
reproduced it**:

```
    UNBACKED in_graded_domain claims: ledger.probe.a228
    * THESE CAPABILITIES ARE MARKED in_graded_domain BUT NO PARITY VECTOR KILLS A NAMED
      WRONG IMPLEMENTATION FOR THEM: ledger.probe.a228. …
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

[MEASURED by `A2-28` at commit `2e97162`. The row was added to a temp store in `/tmp` only;
`.softhouse/vectors/capabilities.json` was not modified, and
`git rev-parse HEAD:.softhouse/vectors` still returns `73c3ea7b43dd75f04884072719a87fc8e1d255c1`.]

> **⚠ REVISION 3 CARRIED A CAVEAT HERE. REVISION 4 RETRACTS IT: `A2-22` FIXED THE DEFECT, AND THE
> BLAST RADIUS THE CAVEAT LEFT `[UNVERIFIED]` IS NOW MEASURED BY A COMMITTED TEST.** This is `A2-25`'s
> finding **F-4**, and it was reject-grade **as merged** rather than as drafted: `A2-21` raised the
> issue correctly as `FU-A2-21-1`, and `A2-22` landed after it.
>
> **What revision 3 said:** *"the loop filters on CLASS only — `if v.Class != ClassParity { continue }`
> — and not on whether the vector was ADMITTED … So a vector the harness **REFUSED** still contributes
> coverage"*, with the blast radius left as *"an inference, not a measurement"* `[UNVERIFIED]`.
>
> **What the tree says now** [VERIFIED by `A2-28` at commit `2e97162`, `capability.go:262-278`]:
>
> ```go
> func (r *CapabilityRegistry) CounterfactualCoverage(vectors []*Vector) (map[string][]string, []string) {
> 	for _, v := range vectors {
> 		if v.Class != ClassParity { continue }
> 		if verdict := r.RefusalFor(v); !verdict.Gradeable { … continue }
> ```
>
> with a doc comment at `capability.go:245-247` reading *"A REFUSED VECTOR BACKS NOTHING (finding
> A2-19 F3), and this function decides that for itself"*. The harness now prints
> **`kills carried by REFUSED vectors: 0, credited to NOTHING`** on every run [MEASURED by `A2-28`
> at commit `2e97162`, line 146 of the unfiltered transcript].
>
> **And the blast radius is no longer an inference.** `A2-22` shipped
> **`TestLiveStoreRefusedVectorBlastRadius`** (`coverage_refusal_test.go:50`), which measures exactly
> the question revision 3 left open — whether any *currently committed* vector is affected — plus
> `TestRefusedVectorCannotBackACapability` (`:202`) and
> `TestRefusedVectorDoesNotSilenceUnbackedEndToEnd` (`:305`). **All three PASS**
> [MEASURED by `A2-28` at commit `2e97162`: `go test ./internal/apps/loanschedule/conformance/
> -run 'Refus|Coverage'`].
>
> **What survives the retraction, and it is not nothing.** Two limits remain, and a ratifier should
> read them as the residue of this leg rather than as the old caveat in new words:
> **(i)** the coverage loop's admissibility check is still **the caller's job** — the function's own
> doc comment says so (*"ADMISSIBILITY IS STILL THE CALLER'S JOB … Run filters it before calling"*),
> so the property is jointly held by `Run` and `CounterfactualCoverage`, not by one of them;
> **(ii)** `conformance.sh` never runs `go test` (P-45), so those three tests are **not** harness
> guards — a regression in them does not turn the conformance run red. That is a general property of
> every Go test in this repository, stated in §5, and it is why the retraction rests on the
> **source** at `capability.go:262-278` and on the harness's own printed
> `kills carried by REFUSED vectors: 0` line, not on the tests alone.

**So the enforcement is real, and it fires on the REGISTRY ROWS, not on the empty directory.**
Revision 1 presented those two as interchangeable legs of one argument and they are not
interchangeable at all: if §4.10's rows are never authored, or are authored `in_graded_domain:
false`, `ledger/` stays empty and **invisible indefinitely**, at exit 0, in every run.

**And §5.1 sits on top of this, which produces the ordering rule below.** Once the rows land as
`true`, the fatal fires — and until P-1…P-5 exist, **no MEANINGFUL `ledger` vector can be written to
clear it.** The run would be permanently red, and the only legal way out is to withdraw the row to
`in_graded_domain: false` (§4.10's retraction (c); `grade.go:473-474`) — not to author a vector.
**Revision 3's precision, and it matters here**: a `ledger`-context *file* is refusable at admission
today (`A2-20`), and before `A2-20` a relabelled `loanschedule` vector was admitted and would have
cleared the fatal while grading nothing about the ledger (§5.1.1). What P-1…P-5 gate is a vector that
*expresses a ledger claim*, which is the only kind that clearing this fatal ought to accept. That is not a hypothetical: it
is exactly the state the measurement above puts the harness in.

**NORMATIVE SEQUENCING RULE, and revision 2 adds it because the measurement forces it.** `ledger`
capability rows are authored in this order and no other:

1. **The §5.3 machinery lands first** (P-1…P-5, and P-10 for requirement 7's bottom-left cell), with
   the **whole-directory** non-regression demonstration of §5.2 requirements 1–2 against a freshly
   measured baseline `B` — not against a literal copied from this document.
2. **Rows are authored `in_graded_domain: false`**, each carrying in its `evidence` string the
   reason — *no admissible vector can yet be written for this capability* — so the row is a recorded
   gap rather than a claim.
3. **A row flips to `true` in the same change that promotes the vector covering it**, never before.

**A row set to `true` ahead of its vector turns every run in the repository red and cannot be
cleared by any legal means.** Any task that does it has broken the harness for every other context,
not just for `ledger`.

**A remaining hole, recorded and NOT closed by this document, because closing it is code.** Nothing
makes an empty or vector-less context directory visible in the **unfiltered** run. Two candidate
fixes, both outside DEC-2's scope and both for the harness owner: make `conformance.sh` refuse a
context directory that exists and is empty even without `-context`; or have `LoadStore` report
per-context zero counts in the unfiltered census the way `StoreFileCensus` already reports stray
files. **The second is more in keeping with T123/T154's precedent** — *"the filter narrows what is
GRADED, never what is CHECKED"*, which is the census's own stated rule [VERIFIED by this task:
`vector.go:1006-1009`] — and an empty context directory is precisely a store fact that is invisible
from one angle, which is the defect class T123 was written to close. **DEC-2 records the hole; it
does not fix it.**

### 5.5 The `graded_against` requirement, restated with its true cost

A `ledger` parity vector must name the **wrong implementations it kills** (`graded_against`). The
loanschedule store's finding applies directly — *"an all-products-identical capture is not evidence
of non-gradeability"*, and conversely **a capture that kills nothing is a capture, not a grader**.

For this context **many** kills will be structural rather than money-valued (`kind: "structural"`,
`margin_minor: "0"`, non-empty `divergent_cells`), because much of what this contract answers is
account ids, GL codes, enum values and refusal strings. **Revision 2 corrects revision 1's "most",
which followed from the over-broad B-5:** vectors asserting a journal entry carry real amounts
(§2.2, R-3), and `I-1`/`I-2` are **money** kills with non-zero margins once P-5 exists. A `ledger`
corpus of nothing but structural kills would grade no amount at all, and the harness prints exactly
that distinction for a reason (finding D-4).

The cell vocabulary revision 1 proposed — `resolved.account_id`, `resolved.gl_code`,
`resolved.classification`, `refusal.code`, `refusal.http_status`, `refusal.message` — remains the
right **starting list**, plus money cells per P-5. **What revision 2 changes is the claim about what
it costs:** revision 1 called it *"the grader task's work, named here so it is not improvised"*,
which reads like configuration. It is **P-4**: a comparator, and a whitelist derived from that
comparator rather than authored beside it. Authoring the six names without the comparator would
produce a store that reports kills nothing checks — finding T9-F1b, reintroduced deliberately.

---

## 6. Forward-compatibility analysis

Ordered by descending risk.

- **6.1 Charges — the highest risk.** Charge resolution has three different precedence chains
  across loan / savings / shares, and savings uniquely lets the `m_charge` row's own GL account
  outrank every mapping. None of it is captured, and on an in-process seam it is structurally
  unreachable (**B-3**). Adding it needs a fourth entry point in the contract, which is an
  amendment. Mitigated only by being **excluded from the contract domain now** rather than
  admitted and left ungraded — an admitted-but-ungraded charge entry point would be exactly the
  surface nobody sets that this contract avoids accumulating.
- **6.2 Savings, shares and working-capital loans — real, unmitigated, licence-constrained.** The
  three resolvers exist in the oracle and are source-derived in the port, but the capture tenant
  has no such product, so nothing is graded. Note the licence interaction: under the ratified
  **NBFI (ББСБ)** tenant parameters, deposit-taking **activation** is prohibited (Law on
  Non-Banking Financial Activities Art. 12.1.3 / 12.1.4), so savings code ships **disabled** and
  exposes no endpoint. That is a constraint on activation, **not** on porting, and it does not
  make the savings resolver correct — it makes it ungraded. DEC-2 refuses it either way.
- **6.3 The classification-on-the-entry question — mitigated by shape, unresolved in fact.**
  Carrying `Classification` on the resolved account (§3.3) means a later entry writer *can*
  record it. Whether A1 does is A1's diff, and DEC-2 does not decide it. `[UNVERIFIED]`: the
  runtime consequence of a retype re-rendering a historic entry has **not been observed**. One
  request would settle it — read a journal entry posted before the retype and confirm it
  re-renders under the new classification — and would convert this slice's most consequential
  claim from re-derived to observed. §9 item 6.
- **6.4 A second accounting-rule value (`ACCRUAL_UPFRONT`) — an enum member, shape holds.** On the
  savings side its mapping switch reaches `default: break` and writes **no mappings at all**; the
  loan side must be measured, not assumed by symmetry. §9 item 10.
- **6.5 More placeholder codes — a value-domain widening, shape holds**, *provided* §4.8's
  disjointness assertion against the financial-activity codes is executable rather than a comment.
- **6.6 A second currency — low risk for the RESOLUTION half, real for the OBSERVATION half.**
  Revision 2 corrects revision 1 here, which said *"§2.2 B-5 means no amount crosses this seam"* and
  inherited the over-broad B-5 (R-3). **Resolution** genuinely is currency-free: three scalars in,
  an account out, and adding MNT-plus-one changes no predicate. **Observation is not.** `G-07` pins
  `Currency.Code == "MNT"` and `G-08` pins exactness at two minor-unit digits, and every journal
  entry in the corpus is MNT [VERIFIED: `A2-150`'s dump, six rows]. A second currency with a
  different minor unit widens the value domain of both predicates and interacts with a question
  **T186 explicitly left open** (§4.3) — the treatment of currencies whose minor unit is not 2. It
  is a **value-domain widening, not a shape change**, so it is not an amendment; but it is not the
  non-event revision 1 described. It remains a larger risk for **A1**, which produces the amounts.
- **6.7 The chart itself — no risk to the shape, by construction.** G-9 puts it outside the
  contract (§4.5), so an FRC-aligned chart is a data deliverable and changes no predicate here.
- **6.8 What holds under all of the above.** The two-domain structure of §3.1, the seam registry
  of §4.1, the enum-encoding rules of §4.8, the two-kinds-of-refusal distinction of §4.9, and the
  default-deny discipline of §4.10. None is a Fineract artefact and none changes meaning when a
  neighbouring context arrives.

---

## 7. Deliberately out of scope for DEC-2

Named, because a contract is defined as much by its edges as by its interior.

- **Journal-entry writing, reversal, and the sign convention** — slice **A1**. DEC-2 resolves
  *which account*; A1 writes the leg. **A2 fixes no sign convention and this document invents
  none**: no table in the slice carries a sign or normal-balance flag, and nothing derives one
  from the account classification [VERIFIED BY A2-1 AND RE-DERIVED BY A2-2 in three directions,
  NOT RE-OPENED HERE]. The one sign the context *consumes* is the trial balance's, defined
  outside the slice, and A1 must re-derive it from those files rather than from any document.
- **`m_trial_balance`** — slice **A3**, and **not ported as a balance store**. Its
  `closing_balance` is written at insert from an **unsigned** `SUM(je.amount)`, which is a written
  stored balance *and* a wrong one (§4.4 I-3). It may be ported only as a derived or materialised
  view whose refresh is a pure function of `acc_gl_journal_entry`, with no write path from
  application code.
- **The chart of accounts** — data, G-9 (§4.5).
- **`Idempotency-Key`** — the adapter's HTTP layer and A1 (§4.4 I-7).
- **Deposit-taking activation** — a `user` gate, unaffected by anything here.
- **Amending DEC-1 or `nexus/internal/apps/loanschedule/contract/contract.go`** — **not required by
  revision 1, not required by revision 2, and not done by either.** The `A2-13` and `A2-16` handoffs
  each record the before-and-after sha256 of both files.

  **One conditional that a builder of §5.3's machinery must not walk into.** The harness resolves a
  vector's refusal sentinel through `sentinelByName`, which returns `contract.Err*` values imported
  from the **frozen** `contract.go` [VERIFIED by this task: `enums.go:93-103`, `registry.go:11`]. **A
  fourth sentinel added to that function is a modification of a ratified DEC-1 artefact and therefore
  a hard `user` gate.** §5.2 chooses a design that avoids it — a separate `ledger` schema with its
  own expectation type and its own sentinel space, sharing nothing with `contract.Err*`. If a future
  task finds itself unable to avoid touching `contract.go`, **that is the moment to stop and raise a
  gate**, not to make a one-line change to a file whose whole purpose is that it does not move.

- **Writing the `ledger` vector schema, comparator or cell whitelist** — §5.3's remaining **nine**
  preconditions (P-1…P-7, P-9 and the new **P-10**). **This ADR writes no code**, and §1.1 gives the
  reason. Naming machinery is not building it, and revisions 2, 3 and 4 are careful to claim only
  the former. **The `I-3`/`I-4` guard is the one item that has since left this list**: `A2-18` built
  it and `T208` wired it, discharging **P-8** with the residue §4.4.1 records.
- **Running a named wrong implementation** — **P-10**, new in revision 4. `graded_against` records
  a counterfactual; it does not execute one (`A2-25` F-9). Building the registry route or a mutation
  harness is `A2-15`'s work, not this ADR's, and §5.2 requirement 7's bottom-left cell cannot be
  claimed without it.

---

## 8. Consequences

### 8.1 NOTHING GRADES THE LEDGER — say it here, not only in the banner

The banner at the head of this document says this. It is repeated here, at the end, because §8 is
what a ratifier reads last and because revision 1's §8 said something adjacent that a reader will
merge with it.

**Four facts. Each was RE-MEASURED by `A2-28` at commit `2e97162`, and fact 3's numerator was
RE-MEASURED AGAIN by `A2-32` at commit `33d19a6`; each carries the stamp of the task that took it.**
Revision 3 introduced this list as *"Four facts, each measured by this task"* while fact 3 contained
a figure nobody had ever measured (`A2-25` F-2; §4.4.1's `P-67` box) — **and revision 4 rewrote this
heading to promise the fix while fact 3 still carried an unmeasured numerator** (`A2-31` F-2). **A
heading that asserts measurement is a claim; it has now been wrong twice in this exact slot, and it
is checked here.**

1. **Zero `ledger` vectors exist.** The store's only context directories are `loanschedule/` and
   `_selftest/`.
2. **Zero `ledger` vectors are EXPRESSIBLE** — §5.1, established in code in five legs, all five
   re-opened and confirmed by independent review. Preconditions P-1…P-5 (§5.3) do not exist.
   **⚠ RETRACTION, revision 3: revision 2 wrote *"Zero `ledger` vectors CAN exist"* here, and the
   banner and §4.10 said the same. That was FALSE.** A relabelled `loanschedule` parity vector —
   two string edits, `case_id` and `context` — was **admitted, graded and counted**, taking the
   headline to **`VERDICT: PASS (exit 0) — 44 parity vectors … 5711 cells`**, measured twice
   independently (`A2-19`, and the driver on `main`) to identical figures. **Admission**-impossibility
   is strictly stronger than **expression**-impossibility and was never established. §5.1.1 carries
   the retraction, the cause (a positive control that was a false negative — **P-50**), and the fact
   that `A2-20` has since closed the hole. It is restated here rather than reworded because a silent
   downgrade would hide that a green `PASS 44` ever happened.
3. **A source guard for `I-3` and `I-4` now RUNS, and FOUR OF ITS DECLARED DETECTION CLASSES
   — `I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML` and `OPAQUE-SQL` — inspected an EMPTY population in
   this tree.**
   `run_guards` invokes **seven** guards, not five; the seventh is `guard_ledger_invariants`
   [`.softhouse/conformance.sh:1152-1187` defines it, `:1209` invokes it], built by `A2-18` and
   wired by `T208`, and `A2-28` measured `invariant violations 0` at commit `2e97162`.
   **⚠ Revision 2 said no such guard existed. That was true when written and is stale.**
   **⚠ RETRACTION, revision 4: revisions 1–3 said "three of its FOUR detection classes" here and at
   three other sites, under a heading claiming each fact was measured. The guard declares SEVEN**
   — `I3-FIELD-WRITE`, `I3-PKG-STATE`, `I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`, `I6-HOLD-BALANCE`,
   `OPAQUE-SQL` [VERIFIED by `A2-28` at commit `2e97162` from
   `.softhouse/guards/ledgerguard/main.go`, re-derived by `A2-32` at `33d19a6`] — **and the "four"
   was the guard's count of BLIND SPOTS, read as a count of classes** (`A2-25` F-2; §4.4.1 records
   the mechanism as **P-67**).
   **⚠ RETRACTION, revision 5: the NUMERATOR was wrong too, and revision 4 shipped it in this slot
   under the heading it had just rewritten to promise the opposite.** Revision 4 said *"THREE of its
   SEVEN"* and recorded `I4-BUILDER`'s population as `[UNVERIFIED]` at one site in §4.4.1 while
   asserting the uncorrected three as a measured fact at four others, this one included. **It is
   FOUR** — `I4-BUILDER`'s population under `nexus/` is **zero**, MEASURED in both polarities by
   `A2-32` at `33d19a6` (and first by `A2-31` at `90c21d6`), with the real `ledgerguard` binary as
   the control (`A2-31` F-2; §4.4.1 carries the measurement). **Revision 5 names the four and drops
   the ratio, because a named list is checkable and a ratio is not** — the remedy §4.4.1 prescribed
   in revision 4 and did not apply to itself. What the guard
   does **not** buy: the detection surface is the **name**, so renaming a balance defeats it;
   triggers, migrations and stored procedures are not walked; `I-5`'s semantic half and non-Go
   callers are uncovered; and the `I-4` SQL classes found **zero** SQL DML literals and **zero**
   mutating driver calls, because this Go module declares no database driver — so they are proven by
   the guard's self-test and by nothing in this repository (**P-35**). §4.4.1.
4. **The 46 passing parity vectors are `loanschedule`'s** [MEASURED by `A2-28` at commit `2e97162`;
   it was 43 at revision 3, and `T116` promoted three in between — **re-measure, do not copy**].
   None touches a GL account, a mapping, a financial activity or a journal entry. The directory
   boundary **was not enforced** when revision 2 leaned on it (fact 2's retraction); **it is enforced
   now**, at admission, by a context allowlist tied to the schema [`conformance/vector.go:77-81`,
   `admit.go:139-147`].

**Ratifying DEC-2 changes none of the four.** It writes down a boundary; it grades nothing. The two
must never be confused, and a citation of this document as evidence of ledger coverage is a
misreading of it.

### 8.2 If ratified

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
  context"** [count MEASURED by `A2-28` at commit `2e97162`; it moves, the sentence does not].
  **⚠ Revision 3 records what this sentence cost in revision 2**: it was written as a
  structural guarantee and it was not one. The `ledger` context *could* contribute to the parity
  count, and did, at `PASS 44` (§5.1.1). The sentence is true today **because `A2-20` made it true
  in code**, not because the schema made it true by construction — and the distinction is the
  difference between a guarantee and a convention that happened to hold.

### 8.3 If ratified, these remain true and must not be misread

- **A `ledger` conformance PASS would mean "matches the reference oracle on captured vectors, inside
  the graded domain".** It would not mean the ledger is correct, and it would mean nothing at all
  about savings, shares, working-capital loans, charges, reversals, holds, or nineteen of the
  twenty-three cash placeholder slots. **Today there is no such PASS to misread.**
- **`conformance.sh`'s hard guards DO cover `nexus/internal/apps/ledger/` today — FOR FLOATING POINT,
  `gofmt`, AND (since `T208`) A SOURCE-LEVEL `I-3`/`I-4` WALK OF THE GO TREE, AND FOR NOTHING ELSE.**
  **Revision 3 corrects revision 2's "and for nothing else", which was true when written**: the
  seventh guard exists now (§4.4.1). **It does not make the ledger covered** — its own transcript
  says a PASS means *"no violation is visible to a source-level guard over the Go tree"*, not *"the
  ledger tree is covered"*, and **four of its declared detection classes — `I3-SQL-BALANCE`,
  `I4-BUILDER`, `I4-DML`, `OPAQUE-SQL` — inspected an empty population here** (revision 4 said
  *"three … of seven"*; `I4-BUILDER` is MEASURED empty by `A2-32` — §4.4.1). The float and `gofmt`
  warning is unchanged and still the point: T166 widened both roots to the Go module root,
  re-verified by `A2-28` at commit `2e97162` (§4.4), and `A2-28`'s own unfiltered run printed
  `covered: nexus/internal/apps/ledger` in the no-float census [MEASURED by `A2-28` at commit
  `2e97162`]. **THAT FLOAT-AND-GOFMT COVERAGE IS NOT `I-3` AND IS NOT `I-4`; the SEPARATE seventh
  guard is what walks for those, and it DOES run.**

  > **⚠ REVISION 4 DELETES A FALSE SENTENCE THAT SAT INSIDE THIS BULLET. This is `A2-25`'s F-1, and
  > it was the rejection-grade finding.** Revision 3 ended this bullet with *"Revision 1 wrote 'That
  > is what makes I-3 and I-4 enforceable at all' — true in the sense that a guard must be able to
  > see the tree before it can check anything in it, and certain to be read as saying the invariants
  > are checked. **They are not checked. No guard for either exists** (§4.4.1)."*
  >
  > **That was false on the live tree, and it sat TEN LINES BELOW this same bullet's own
  > "AND (since `T208`) A SOURCE-LEVEL `I-3`/`I-4` WALK OF THE GO TREE".** It cited §4.4.1, whose
  > heading is *"IT DID NOT EXIST, IT DOES NOW"* — pointing the reader at its own refutation. It sat
  > under a heading, *"If ratified, these remain true"*, which is itself a truth claim, in the
  > section §10 calls *"what a ratifier reads last"*. And `A2-21`'s own change log **listed §8.3 as
  > corrected**: it corrected the head of this bullet and left the tail. **That is exactly the defect
  > class revision 2 was rejected for** (**P-21**, **P-26**, **P-37**), recurring one revision later.
  >
  > **The sweep revision 4 ran, because a site list is not a sweep.** `A2-25`'s FU-A2-25-5 names the
  > mechanical remedy and revision 4 performed it: after correcting the claim, **grep the NEGATION of
  > the corrected claim, not the claim** — `not checked`, `No guard for either exists`, `no such
  > guard`, `does not exist`, `did not exist`, `nothing checks` — across the whole document, and
  > inspect **every** hit rather than the ones the reviewer named. The surviving hits are all
  > legitimate: §4.4's I-3 row (*"Revision 2 said 'no such guard exists'; that was true when written
  > and is stale"* — a labelled retraction), §5's *"a contract that does not exist"*, §5.1.1's
  > quotation of the retracted words, §4.2's Fineract 404 message text, and §10's historical
  > entries. **No fifth surviving assertion of the negation exists** [VERIFIED by `A2-28` at commit
  > `2e97162`, `grep -n` over the whole file, every hit opened].
  >
  > **A stale harness comment survives outside this document and is raised, not fixed:**
  > `.softhouse/conformance.sh:1115-1116` still reads *"the I-3/I-4 SOURCE GUARD that DEC-2 §4.4
  > requires and §4.4.1 **records as not existing**"* [VERIFIED by `A2-28` at commit `2e97162`].
  > Harmless today, and it will mislead the next reader who follows it into DEC-2. It is `A2-25`'s
  > FU-A2-25-2 and it is **out of this task's scope** — `A2-28` touched no harness file.

  What remains true from revision 1 is the forward warning: **re-narrowing either root would
  silently un-cover this tree**, and would do so while still printing a healthy-looking file count.
- **A `ledger` file's CONTEXT is now checked at admission** — a `gerege.loanschedule.vector/v1`
  vector claiming any context outside `{_selftest, loanschedule}` is INADMISSIBLE
  [`vector.go:77-81`, `admit.go:139-147`]. **Until `A2-20`, it was not**, and a two-string-edit copy
  of a promoted parity vector reported `PASS 44` at exit 0 (§5.1.1). **A second schema inherits this
  obligation and does not inherit this check** — that is precondition **P-9**.
- **The `graded_against` machinery is genuine enforcement, and it fires on the REGISTRY ROWS, not on
  an empty directory** (§5.4, measured both ways). An empty `.softhouse/vectors/ledger/` passes at
  exit 0 in the default run today; a `ledger` capability row marked `in_graded_domain: true` with no
  covering kill turns every run in the repository red immediately. **Observe §5.4's sequencing rule**
  — rows land `false`, and flip in the same change that promotes the vector covering them.
- Cutover, regulatory sign-off and licence facts remain hard `user` gates, and **G-10 remains
  OPEN**.

---

## 9. Every `[UNVERIFIED]` in this document, and why it could not be closed

Each is a gap, not a guess declined — **except item 10, which revision 2 CLOSES, because it was
never a gap. It was a read not taken.** Revision 1's preamble classed all thirteen as *"a gap, not a
guess declined"*, and for twelve of them that was accurate. Item 10 was one grep away. The
correction is recorded rather than quietly applied, because "unclosable" and "not yet opened" are
different claims and only one of them is honest about the cost of closing it.

**Revision 4 adds items 14 and 15 and closes item 16**, and states the same distinction about its
own additions: **item 14 is a read not taken, not an unclosable gap**, and is labelled as such.

1. **Whether the oracle can produce sub-minor-unit residue in a money column at all, and what it
   would do with one.** No captured vector establishes it; the corpus's only values beyond two
   decimals are percentages. Closing it needs a capture at a non-zero rate with charges — i.e.
   arithmetic the A2 probe set never executed. §4.3.
2. **The null-payment-type query semantics.** `IS NULL` (matching the core row) versus matching
   nothing. Not resolvable from the pinned checkout — it is a Spring Data JPA framework
   behaviour, and this repository has already been burned by an unsupported framework assertion
   once. **No capture discriminates the two readings.** The discriminating capture is cheap and
   named: a row with `payment_type` NULL and `charge_id` set at placeholder 1 — under `IS NULL`
   the payment-type query matches two rows and yields the non-unique refusal; under the other
   reading the core row stands. §4.2 G-06.
3. ~~**The program-wide major/minor conversion boundary** — T186 is settling it in parallel.~~
   **CLOSED in revision 2: T186 HAS RULED**, and it merged *before* revision 1 did — A2-13's branch
   forked before it landed, so revision 1 shipped a live forward reference to a completed task. The
   three-way ruling — (a) major-unit decimal mandatory on the capture wire, (b) absolute rejection
   on the Go module's own surface, (c) integer minor units in the stored vector — is reproduced in
   §4.3 with DEC-2's position on each, and **§4.3 now states (c) as an explicit rule for `ledger`
   vectors** rather than leaving it implied. No contradiction with this document was found. What
   T186 itself left open — non-2 minor units, and whether a shared conversion utility is mandated —
   is outside this contract and is **not** claimed closed here. §4.3.
4. **Which enum actually rendered the observed miss messages.** R-1 is source-derived. `A2-224`
   and `A2-225` are at codes 16 and 13, where both loan enums render identically, so they cannot
   discriminate. A capture at code **22**, **24** or **25** on a **cash** product would settle it
   in one request. §4.7, §4.9.
5. **STEP 0's precedence at posting time.** The financial-activity branch is re-derived from
   source and its data is graded against `A2-150`, but no capture exercises a posting that routes
   through it. §4.10.
6. **Trap 3's consequence at runtime** — that a retype retroactively re-renders a historic entry.
   The source is confirmed (no classification column, mutable classification, guard keyed on
   usage only); the re-rendering was **not observed**. One request would convert it. §6.3.
7. **Reachability of the two `fromInt(...).toString()` NPEs** in the oracle's own error path
   (cash 26; accrual-only 7/8/9 on the WCL path). The null return is proven from source; the
   reachability is not. §4.9 R-2.
8. **The exact HTTP 500 body** the oracle returns on a savings or shares mapping miss. No capture
   exercises it — the tenant has no such product. §4.9 R-2.
9. **The financial-activity create/update asymmetry** (101 and 102 are creatable but not settable
   on update). Read from both halves of the validator and implemented; **not observed** — no
   capture does a `PUT` with `financialActivityId: 101`. A cheap refusal vector nobody has taken.
10. ~~**Whether `ACCRUAL_UPFRONT` on the LOAN side writes mappings.**~~ **CLOSED in revision 2. IT
    WRITES THE FULL ACCRUAL SET.** `case ACCRUAL_UPFRONT: // Fall Through` into `case
    ACCRUAL_PERIODIC:` [VERIFIED by this task at the pinned checkout:
    `ProductToGLAccountMappingWritePlatformServiceImpl.java:149-151`, inside
    `createLoanProductToGLAccountMapping`]. The savings side writes nothing — `case ACCRUAL_UPFRONT:
    break;` at `SavingsProductToGLAccountMappingHelper.java:192-193` and `:313-314`, a file
    containing **zero** `default:` labels; the savings create switch in the write service reaches
    `default: break;` at `:345-346` because it has no `ACCRUAL_UPFRONT` case at all [all VERIFIED by
    this task]. **Revision 1 was right to refuse the symmetry assumption and wrong to file the
    question as unclosable.** Full treatment, including the two wording corrections and the
    `switch(null)` hazard, is in §4.2 under `G-03`. **What is still open, and is now the ONLY ground
    for `G-03`'s refusal, is evidential: no capture exists at `accountingRule = 4`** — one product
    creation and one read-back retires it, comparing the persisted mapping set against product 28's.
    §4.2 G-03, §6.4.
11. **Whether `PortfolioProductType.fromInt`'s two oracle call sites are ever reached with a
    stored 3, 4 or 5.** The permutation is verified; the blast radius is not.
12. **The five never-posted mandatory slots.** No parity claim is made about `INTEREST_ON_LOANS`,
    `INCOME_FROM_FEES`, `INCOME_FROM_PENALTIES`, `OVERPAYMENT` or `TRANSFERS_SUSPENSE` at posting
    time. §4.7.
13. **Whether the A2 corpus can grade a reversal.** It cannot today: no reversal appears, and the
    committed journal dump does not project the reversal columns. §4.4 I-5.

**Revision 4 added two and CLOSED one; revision 5 CLOSES another (item 14) and adds none:**

14. ~~**NEW — whether `I4-BUILDER` inspects a non-empty population in this Go tree.**~~
    **CLOSED in revision 5, by MEASUREMENT, and the answer was the one `A2-25` and `A2-28` both
    suspected: it is EMPTY.** `A2-31` measured it at `90c21d6` and `A2-32` re-measured it
    independently at `33d19a6`; both drove the probe in **both polarities** against the real
    `ledgerguard` binary, and both read `0` on the real tree. **The corrected figure is FOUR
    classes, not three, and it is now stated at every site that carries it** — banner fact 3,
    §4.4 I-4, §4.4.1, §5.3's P-8 row, §8.1 fact 3, §8.3 and §10 (`A2-31` F-2). **`I4-BUILDER` is the
    one empty class the guard does NOT announce**, which is why three revisions and the driver
    counted three: they counted off the transcript. `A2-28` was right to refuse to assert a
    numerator it had not measured, and wrong to leave the unmeasured one standing at four other
    sites. §4.4.1.
15. **NEW, and it is an OPEN GATE rather than a gap — G-12.** `acc_gl_journal_entry` carries
    `office_running_balance` and `organization_running_balance`: **the reference oracle stores a
    balance on the entry**, while `CLAUDE.md`'s first-tier non-negotiable says balances are derived
    and never written, in a table the same file instructs the port to adopt. **DEC-2 references it
    and resolves nothing** — `A2-29` must first measure whether the columns are ever READ, whether
    they reach a contract-boundary response, and whether the stored value can disagree with the
    derived sum. Option (c) — declaring any vector cell that exposes them outside the graded domain
    — **narrows the graded domain and is a hard `user` gate**, recommendable but not takeable.
    §4.4 I-3, `.softhouse/gates.md` § G-12.
16. ~~**The blast radius of `CounterfactualCoverage` crediting REFUSED vectors** (§5.4's caveat,
    revision 3).~~ **CLOSED in revision 4.** `A2-22` fixed the loop (`capability.go:262-278` filters
    on `RefusalFor`) and shipped `TestLiveStoreRefusedVectorBlastRadius`
    (`coverage_refusal_test.go:50`), which measures exactly the question revision 3 left as *"an
    inference, not a measurement"*. `A2-28` ran it green at commit `2e97162`, and the harness prints
    `kills carried by REFUSED vectors: 0, credited to NOTHING` on every run. **The two residual
    limits are stated in §5.4 and are not this item**: admissibility is still the caller's job by
    the function's own doc comment, and `conformance.sh` never runs `go test` (P-45).

---

## 10. Revision history

- **Revision 5 (this document)** — DRAFT, task `A2-32`, 22 August 2026, worktree at **`33d19a6`**.
  **NOT RATIFIED; `A2-32` is NOT AUTHORISED to ratify it and does not, and says so in the status
  block, the banner and here.** Gate **G-11 stays OPEN — NOT RATIFIABLE** until a **further
  independent review passes clean AFTER revision 5**. Drafted in response to `A2-31`'s **REJECTION**
  of revision 4. **Analyst task: no Go was written into `nexus/`; `nexus/`, `.softhouse/vectors/`,
  `.softhouse/conformance.sh`, `.softhouse/guards/`, `capabilities.json`, `PIN.json`, `contract.go`
  and DEC-1 were all untouched.** `git rev-parse HEAD:.softhouse/vectors` =
  `73c3ea7b43dd75f04884072719a87fc8e1d255c1`, **unchanged**. The `I4-BUILDER` probe is a throwaway
  program under `/tmp`; a copy is committed under the task's handoff directory as evidence and is
  not part of the module or the harness.

  **Revision 5 changes EXACTLY the two things `A2-31` found, and deliberately nothing else.**
  Revision 2 was rejected in part because its reviewer applied its own unreviewed fix; new
  authorship beyond the reviewer's items is itself a defect, so a third issue found during this
  revision's sweep is **registered as a follow-up, not fixed** (see `A2-32`'s handoff).

  1. **`A2-31` F-1 — §4.4.1's `FU-T208-1` parenthetical CORRECTED, and the caveat that outlived its
     defect REMOVED.** Revision 4 stated, under `[VERIFIED by A2-28 at commit 2e97162]`, that the
     guard's own head **DROPS** the `CANNOT-CATCH` block on the pass path. **It does not, and it did
     not at that commit**: `T209` (`03e9094`) closed `FU-T208-1` and is an **ANCESTOR** of `2e97162`
     by one hour sixteen minutes. **The claim was FALSE AT ITS OWN STAMP** — not stale, which is the
     distinction that makes it `A2-25`'s F-4 class recurring one revision later. **Landed at ONE
     site inside this document** — §4.4.1's `FOUR THINGS IT CANNOT SEE` paragraph, rewritten to the
     measured truth and followed by a labelled revision-5 retraction box. **The whole-repo sweep
     found no second live site inside this document**; the surviving copies are in
     `.softhouse/conformance.sh`'s condensation header, which is **not this document's to fix** and
     is routed as `T227` (`A2-31` FU-A2-31-2). **`A2-32` measured that file as carrying the claim in
     ONE PRINTED LINE PLUS A 25-LINE COMMENT BLOCK, not the single line `A2-31` named** — see
     `A2-32`'s handoff; that widening is reported to `T227`, not acted on here.
  2. **`A2-31` F-2 — the empty-population numerator CORRECTED from THREE to FOUR, with the classes
     NAMED and the denominator DROPPED, at EVERY site that carries the claim.** `I4-BUILDER`'s
     population under `nexus/` is **zero**, MEASURED in both polarities by `A2-31` at `90c21d6` and
     independently re-measured by `A2-32` at `33d19a6`, with the real `ledgerguard` binary as the
     control and the guard's own `CENSUS` line as the proof that the probe walks the guard's
     population. The four are **`I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`** and **`OPAQUE-SQL`**.
     **`I4-BUILDER` is the one empty class the guard does NOT announce**, which is why three
     revisions and the driver counted three off the transcript.

     **The NINE sites the correction landed at, listed because the last revision's change log was
     false about its own artefact and that is what made this rejection-grade. `A2-31` named FIVE;
     the other four are restatements of the same claim in different words, and finding them was the
     point of sweeping for the CLAIM rather than the sentence:**

     | # | site | what it said in revision 4 | named by `A2-31`? |
     |---|---|---|---|
     | 1 | **Banner, item 3** | *"three of the guard's **seven** declared detection classes"* | yes |
     | 2 | **§4.4, `I-4` row** | *"THE SOURCE GUARD'S `I-4` ARM"*, singular, with `I4-BUILDER` unmentioned | **no** |
     | 3 | **§4.4.1, headline** | *"THE GUARD DECLARES SEVEN DETECTION CLASSES, AND THREE OF THEM …"* | yes |
     | 4 | **§4.4.1, class table** | `I4-BUILDER` → *"**not established** — see below"* | **no** |
     | 5 | **§4.4.1, numerator paragraph + qualification bullet** | *"The numerator is three"*; `I4-BUILDER` `[UNVERIFIED]` | **no** |
     | 6 | **§4.4.1, *"the correct reading of this whole subsection"*** | the three-class wait-list, `I4-BUILDER` omitted | **no** |
     | 7 | **§5.3, `P-8` row** | *"three of its **seven** declared detection classes"* | yes |
     | 8 | **§8.1, fact 3** (and its heading) | *"THREE OF ITS SEVEN DECLARED DETECTION CLASSES"*, under a heading promising each fact was re-measured | yes |
     | 9 | **§8.3, guard bullet** | *"three of its **seven** declared detection classes"* | yes |

     **Plus two records that asserted the claim rather than restating it, both corrected in place
     with labelled notes:** **§9 item 14** (*"whether `I4-BUILDER` inspects a non-empty population"*)
     is **CLOSED by measurement**; and **§10's revision-4 entry, item 2**, which said *"REPLACED at
     all four sites"* when there were **five** and *"The denominator is dropped"* when it was
     **present at all five** — corrected inline rather than reworded, so the false statement and its
     correction are both readable.

     **The denominator is genuinely dropped this time**, at all nine sites: the text names the four
     classes and does not divide by seven. The count `seven` survives only where it is a
     **standalone measured fact about the guard** — §4.4.1's `[VERIFIED]` enumeration, §8.1 fact 3's
     revision-4 retraction, and the `P-67` box — never as the denominator of a ratio.

- **Revision 4** — DRAFT, task `A2-28`, 22 August 2026, forked from `main` at
  **`2e97162`**. **NOT RATIFIED; `A2-28` is NOT AUTHORISED to ratify it and does not, and says so
  in the status block, the banner and here.** Gate **G-11 stays OPEN — NOT RATIFIABLE** until a
  **further independent review passes clean AFTER revision 4**. Drafted in response to `A2-25`'s
  **REJECTION** of revision 3. **Analyst task: no Go was written; `nexus/`, `.softhouse/vectors/`,
  `.softhouse/conformance.sh`, `.softhouse/guards/`, `capabilities.json`, `PIN.json`, `contract.go`
  and DEC-1 were all untouched; `git status --porcelain` shows exactly this file and the task
  handoff.** Every experiment ran against a temporary copy of the store in `/tmp`.

  **Changes, item by item against `A2-25`'s seven, so a reviewer can check completeness against the
  list that was written to make this ONE revision rather than two:**

  1. **`A2-25` F-1 — §8.3's *"They are not checked. No guard for either exists"* DELETED (§8.3).**
     It was false on the live tree, contradicted its own bullet **ten lines above**, cited §4.4.1
     (whose heading is *"IT DID NOT EXIST, IT DOES NOW"*) as though it supported the sentence, and
     sat under a heading asserting truth in the section §10 itself calls *"what a ratifier reads
     last"*. **It is the same defect class revision 2 was rejected for** (P-21, P-26, P-37), and
     `A2-21`'s own change log had listed §8.3 as corrected — it corrected the bullet's head and left
     its tail. **The sweep run this time is the one `A2-25`'s FU-A2-25-5 prescribes: grep the
     NEGATION of the corrected claim, not the claim** — `not checked`, `No guard for either exists`,
     `no such guard`, `does not exist`, `did not exist`, `nothing checks` — over the whole document,
     with every hit opened. **No fifth surviving assertion exists**; the surviving hits are labelled
     retractions, quotations of the retracted words, Fineract 404 message text, and §5's deadlock
     sentence. A **stale harness comment** carrying the same claim survives at
     `.softhouse/conformance.sh:1115-1116` and is **raised, not fixed** — out of scope
     (FU-A2-25-2).
  2. **`A2-25` F-2 — the wrong denominator REPLACED at all four sites (§4.4.1, §8.1 fact 3, §8.3,
     §10) with the numerator and the class NAMES.** The guard declares **seven** detection classes —
     `I3-FIELD-WRITE`, `I3-PKG-STATE`, `I3-SQL-BALANCE`, `I4-BUILDER`, `I4-DML`, `I6-HOLD-BALANCE`,
     `OPAQUE-SQL` — re-derived by `A2-28` from `.softhouse/guards/ledgerguard/main.go` at
     `2e97162`; the three that inspected an **empty population** are **`I4-DML`**,
     **`I3-SQL-BALANCE`** and **`OPAQUE-SQL`**. **The denominator is dropped**, because a named list
     is checkable in one grep and a ratio is not. §4.4.1 records the origin as **P-67** — the
     guard's **four BLIND SPOTS** were read as four **classes**, two different quantities one
     sentence apart — and records that **the driver certified the figure "EXACT" and propagated it**
     to `.softhouse/program.json`, `.softhouse/RESUME.md`, `.softhouse/patterns.md` and
     `.softhouse/tasks.json`, **so the error was the driver's before it was `A2-21`'s.** Those four
     files are outside this task's scope and are a follow-up. Two honest qualifications are added
     and neither is asserted as a figure: `I6-HOLD-BALANCE`'s population is non-empty **only by an
     over-match the guard itself names**, and **`I4-BUILDER`'s population was not established**
     `[UNVERIFIED]`, which is why no corrected numerator is claimed beyond the three the guard
     reports.

     > **⚠ CORRECTION, revision 5 — TWO OF THE SENTENCES IMMEDIATELY ABOVE WERE FALSE ABOUT THE
     > DOCUMENT THEY DESCRIBE, and that is `A2-31`'s F-2 in its sharpest form. They are left in place
     > and corrected here rather than reworded, for the same reason §5.1.1 restates rather than
     > rewords.**
     >
     > 1. ***"REPLACED at all four sites"* — there were FIVE.** Revision 4 carried the ratio at the
     >    banner (item 3), §4.4.1's headline, §5.3's P-8 row, §8.1 fact 3 and §8.3. The `A2-25` F-2
     >    site list was four; the document's own count was never taken.
     > 2. ***"The denominator is dropped"* — IT WAS NOT DROPPED AT ANY OF THE FIVE.** Every one of
     >    them read *"three of its **seven** …"*. §4.4.1 **prescribed** the remedy in its own `P-67`
     >    box (*"state a numerator with the members NAMED, and drop the denominator"*) and did not
     >    apply it to its own headline a few dozen lines above. **P-26.**
     >
     > **A change log that lists a site as corrected while the artefact still carries it is exactly
     > `A2-25`'s F-1, which was the rejection-grade finding on revision 3** — there it was `A2-21`'s
     > change log listing §8.3 as corrected while §8.3's tail survived. **Third fire.** And the
     > numerator was wrong as well: **it is FOUR, not three** — `I4-BUILDER` is empty, MEASURED
     > (§4.4.1's revision-5 retraction). **Revision 5 states the four with the classes NAMED and NO
     > DENOMINATOR at NINE sites — the five it named plus four it did not — and corrects §9 item 14
     > and this entry as well, each listed in the revision-5 entry below.**
  3. **`A2-25` F-3 — §5.2 requirement 6's BEFORE REWRITTEN, and this was the most important of the
     seven.** Requirement 6 is one of two requirements that will grade `A2-15`, and **it could not
     be satisfied on the bytes it specified**: the `gerege.ledger.vector/v1` file it names dies at
     **strict JSON decode** (`unknown field "product_id"`), so `admit.go:109-110` and
     `admit.go:139-147` — the two refusals it mandated — are both **unreachable** and `inadmissible`
     stays **0**. `A2-25` measured this; **`A2-28` reproduced BOTH halves independently at
     `2e97162`** on temp stores: the ledger-shaped bytes die at load with `inadmissible 0`, and the
     only bytes that emit both mandated refusals together are a **loanschedule-shaped vector in a
     ledger costume** — §5.1.1's own retracted defect, which could never be the AFTER subject under
     a genuine second schema. **The requirement written to close the vacuous-control hole re-opened
     it through its own text (P-22 at one remove).** The fix does **not** loosen the evidence: the
     BEFORE now demands the refusal the bytes **actually produce** — a strict-decode load failure,
     which is a *stronger* BEFORE than an admission refusal because the bytes do not even parse —
     quoted by diagnostic and surviving population, never by exit code (P-62). **The requirement is
     split into 6a (same bytes, before and after) and 6b (the admission-layer refusals, on their own
     bytes, said explicitly to be a different file that is not the AFTER subject)**, which is the
     second of the two shapes `A2-25` permitted. **The AFTER half is KEPT** — `A2-25` judged it
     strong and genuinely falsifiable, and confirmed the harness distinguishes 43 from 44 — with
     only the stale literals replaced by requirement 2's measured baseline `B`.
  4. **`A2-25` F-4 — §5.4's F3 caveat RETRACTED.** `A2-22` fixed the defect: `capability.go:262-278`
     now filters on `RefusalFor` as well as class, with a doc comment at `:245-247` reading *"A
     REFUSED VECTOR BACKS NOTHING (finding A2-19 F3), and this function decides that for itself"*,
     and the harness prints `kills carried by REFUSED vectors: 0, credited to NOTHING`. **The blast
     radius the caveat left `[UNVERIFIED]` is now measured by a committed test** —
     `TestLiveStoreRefusedVectorBlastRadius` (`coverage_refusal_test.go:50`) — which `A2-28` ran
     green along with two siblings. **Two residual limits are stated rather than dropped**:
     admissibility remains the caller's job by the function's own doc comment, and `conformance.sh`
     never runs `go test` (P-45), so the retraction rests on the **source** and on the harness's own
     printed line, not on the tests.
  5. **`A2-25` F-5 and F-6 — the guard transcript RE-TAKEN and ~18 stale line citations REFRESHED,
     and the defect is named for what it is: FRESHNESS, not fabrication.** **Every stale citation
     was substantively TRUE**; `A2-25` opened each by content and confirmed it. The problem is that
     a ratifier cannot check a citation that does not resolve, and the drift reached **+325 lines**
     at one site. `A2-28` re-took **every** harness citation in the document by content at
     `2e97162` and refreshed 28 distinct ranges across `admit.go`, `vector.go`, `grade.go`,
     `capability.go`, `enums.go` and `conformance.sh`. §4.4.1's quoted guard census was re-taken and
     **carries a box recording that this is its THIRD printing with three different sets of
     figures**, none of them wrong when taken, because the census counts every Go file under
     `nexus/` and any commit moves it.
  6. **`A2-25` F-7 — §5.2 requirement 1's "43 vector files" REPLACED by the DIRECTORY.** `A2-28`
     re-counted rather than copying any number from the review or the brief:
     `.softhouse/vectors/loanschedule/` holds **50** `.json` files — **46** `class: parity` + **4**
     `class: contract-refusal` — at commit `2e97162`, store tree
     `73c3ea7b43dd75f04884072719a87fc8e1d255c1` [MEASURED]. Revision 3's literal would have left the
     four contract-refusal vectors **unprotected**, and the contract-refusal form is the **second
     falsification shape §5.1.1 records** (`4 → 5`, `5664 → 5665`). **Requirements 1, 2 and 6 are
     now phrased against `B`, the baseline the builder measures immediately before its first edit**,
     with the `A2-28` values given for orientation and explicitly expected to be stale.
  7. **`A2-25` F-8 and F-9 — WEIGHED AND BOTH ADOPTED (§5.2 requirement 7, §5.3).**
     **F-8:** requirement 7's perturbation clause was a **disjunction**, and every money constraint
     was conditional on having chosen money — so a builder could perturb `gl_code` and ship a
     `ledger` extension whose money comparator had never been driven red. **The disjunction is
     replaced by a conjunction**: at least one structural cell **and** at least one money cell
     perturbed by exactly one minor unit, reported as a money kill with non-zero `margin_minor`.
     `A2-26` makes this concrete — **before this fire every ledger amount in the A2 corpus was a
     whole tugrik**, so a port that dropped minor units was byte-indistinguishable from a correct
     one on every capture ever taken (§5.0.1). **F-9:** the matrix demands RED against a **named
     wrong implementation**, but `graded_against` is a **declarative record** and nothing in the
     grading path executes it; the registry route or a mutation harness is needed, and **no §5.3
     precondition named either**. **New precondition P-10** closes it, requirement 7 now points at
     it, and no existing identifier is renumbered.

  **Beyond `A2-25`'s seven — the standing correction, adopted (status block, §5, and every
  `[MEASURED]` mark).** *"Re-measure every claim about `main` at the moment of RATIFICATION, not the
  moment of drafting."* **Three of revision 3's four false claims were true when written**, and
  revision 4 would repeat the failure if it stated numbers without dates. So: **every measured claim
  carries the commit it was measured at**; §5 opens with a single **stamped baseline** and §5.2's
  requirements reference it rather than literals; historical measurements (`44 / 5711`, `4 → 5`,
  `5664 → 5665`) are labelled as the record of a *past* tree and are not re-stamped forward; and
  Fineract citations are exempt, being pinned to `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

  **What moved on `main` after revision 3 was written, recorded so the next reviewer can tell
  motion from error:** **`T116`** promoted three vectors (43 → 46; `report.go` now prints exemptions
  with reasons); **`T193`** added a wire-float arm over store-cited capture records; **`A2-22`**
  fixed `CounterfactualCoverage` and shipped the blast-radius test; **`A2-24`** upheld the
  `CorroborationsClaimed` narrowing; **`T214`** landed 64 evidence paths; **`A2-26`** took 45 raw
  ledger captures and found `glAccountType` is **not a stable cell**. **New §5.0.1** records the
  three `A2-26` capture facts that constrain what §5.2 may ask for, and requirement 7 now forbids
  `glAccountType` as the perturbation cell.

  **A new gate is REFERENCED and deliberately NOT resolved: G-12.** `acc_gl_journal_entry` carries
  `office_running_balance` and `organization_running_balance` — the reference oracle **stores** a
  balance while `CLAUDE.md` says balances are derived and never written, in a table the port is
  separately instructed to adopt. §4.4's I-3 row now points at **G-12** and states plainly that
  **DEC-2 decides nothing about those two columns**. `A2-29` must measure first; a recommendation
  written before that measurement would be the guess this program keeps catching.

  **What revision 4 did NOT touch, because `A2-25` ruled them not in dispute:** the §5.1.1
  retraction and its figures; §5.1's five legs; the **seven**-guard count for `run_guards`; §2.2
  B-4's correction and its load-bearing "no office dimension" claim; and `A2-21`'s clean scope.
  Fineract citations were **not** re-audited by `A2-28` and carry `A2-19`'s and `A2-25`'s audits;
  that is stated so the silence is not read as a pass.

  **Bar re-run, not quoted from the brief.** `bash .softhouse/conformance.sh` (never `sh`) at
  `2e97162`, after the edit: probe line **present** and reading `up`; **`VERDICT: PASS (exit 0) —
  46 parity vectors match the pinned reference oracle, 7884 cells compared`**; vector store
  `73c3ea7b43dd75f04884072719a87fc8e1d255c1`; contract-refusal 4, self-test 1, refused 0,
  inadmissible 0, harness errors 0, invariant violations 0. `gofmt -l nexus/` reports exactly
  `contract.go` (**G-3 CLOSED-OPTION-A**). **No gate was crossed. G-11 remains OPEN; G-10 remains
  OPEN; G-12 is referenced and not resolved; G-4, G-5 and G-8 are untouched; cutover, regulatory
  sign-off and licence facts remain hard `user` gates.**

- **Revision 3** — DRAFT, task `A2-21`, 22 August 2026. **REJECTED** by independent review `A2-25`
  on four findings (F-1 … F-4), with five further observations (F-5 … F-9); full verdict in
  `A2-25`'s handoff. **NOT RATIFIED; `A2-21` was NOT AUTHORISED to ratify it and did not.**

  > **⚠ READ THE REVISION-3 ENTRY BELOW AS THE RECORD OF WHAT REVISION 3 CLAIMED, NOT AS CURRENT
  > TEXT.** Four of its statements are corrected above: its *"three of its four detection classes"*
  > (revision-4 item 2), its requirement 6 (item 3), its F3 caveat (item 4), and the `43 / 5664`
  > literals it wrote into requirements 1, 2 and 6 (item 6). **The entry is left unedited on
  > purpose**, for the same reason §5.1.1 restates rather than rewords: a silent downgrade would
  > hide that the claims were ever made.

- **Revision 3 (as drafted)** — DRAFT, task `A2-21`, 22 August 2026. **NOT RATIFIED; `A2-21` is
  NOT AUTHORISED to ratify it and does not.** Drafted in response to `A2-19`'s **REJECTION** of
  revision 2, recorded as gate **G-11 (OPEN — NOT RATIFIABLE)**. A further independent review must
  pass clean before the driver may ratify. **Analyst task: no Go was written, `nexus/` was not
  touched, `.softhouse/vectors/` was not touched, and the diff is this file plus the task handoff.**

  **Changes, all of them:**

  1. **`A2-19` F1 RETRACTED at all three sites — the rejection-grade finding (§5.1.1, banner item 2,
     §8.1 fact 2, §4.10).** Revision 2's *"no `ledger` vector **CAN** exist"* / *"can be admitted at
     all"* was **FALSE**, and it failed in the **unsafe** direction: a relabelled `loanschedule`
     parity vector — two string edits, `case_id` and `context` — was **admitted, graded and counted**
     at **`VERDICT: PASS (exit 0) — 44 parity vectors … 5711 cells`**, against 43 / 5664 without it;
     a relabelled `contract-refusal` vector likewise passed, moving 4 → 5 and 5664 → 5665.
     **Reproduced twice independently to identical figures** — by `A2-19`, and by the driver on
     `main`'s own bytes. The true and weaker claim, which §5.1's own heading already carried, is
     **inexpressibility**, and that is what the document now says. **New §5.1.1** records what was
     claimed, that it was false, how it was falsified, what is true, the cause — **one line:
     `context` was constrained only to be non-empty and to equal its own directory name
     (`admit.go:115-117`, `:119-120`), with no allowlist anywhere** — and why it was believed:
     **positive control PC-3 was a FALSE NEGATIVE**, failing on two **author-correctable** defects (a
     non-contract sentinel; `oracle.seam != none`) rather than on a structural wall. That is
     **P-50**: the prover was never made falsifiable in the direction of the fix. **PC-3 is
     reclassified** from "a control establishing a wall" to "a demonstration that a badly-authored
     vector is refused". **`A2-20` has since closed the hole** (`SchemaContexts()`,
     `vector.go:31-81`; `admit.go:139-147`) — recorded, and explicitly **not** treated as rescuing
     the sentence, which was false when written.
  2. **`A2-19` F2 resolved (§5.2) — the specification `A2-15` is graded against was satisfiable by
     an extension that does NOTHING.** All five of revision 2's requirements are non-regression
     guards on `loanschedule`, and doing nothing changes nothing. **Requirements 6 and 7 are added
     and are normative:** **(6) a POSITIVE CONTROL** — a stated before/after on the same bytes, where
     the `ledger` vector is INADMISSIBLE today (quoting the refusal **text** and the surviving
     population, **never** the exit code, **P-62**) and is admitted, graded and reported under **its
     own count** afterwards, with `loanschedule` still at exactly 43 / 5664; and **(7) a REQUIRED
     RED DEMONSTRATION** — a four-cell matrix in which the comparator goes **RED** on a one-cell
     perturbation of a normative cell (one **minor unit** where it is money), **GREEN** on the
     pristine bytes, and **RED** against the named wrong implementation, with a money divergence
     reported as a **money** kill with a non-zero `margin_minor`, RED shown by the **diagnostic**,
     and the prover itself falsifiable toward the fix (**P-50**). **P-22** and **P-35** are cited at
     the point of the requirement.
  3. **`A2-19`'s adjudication on the precondition split APPLIED (§5.3).** **P-6 (`capabilities.json`)
     moves BEFORE P-1…P-5**, because §5.4 step 2 cannot be obeyed without it — a builder cannot
     author even a `false` row without knowing which file `ledger` rows live in. **P-7 does NOT
     move**: its revision-2 premise (*"a second context implies a second pinned contract file"*) is
     contradicted by **§1.1**, which this task **re-opened and confirmed before acting** — §1.1 says
     this ADR *"does not create or freeze a Go file, and could not"*, that there is *"no counterpart
     file for this context"*, and that it *"deliberately writes no Go"*, and the status block states
     no PIN digest appears at all. P-7 is **re-scoped** to the `dec1_revision` question
     (`admit.go:149`) and placed **after P-1**. **P-9 is added** — the schema must declare its own
     contexts (`A2-19`'s recommendation; `A2-20` discharged the `loanschedule` half, the second
     schema inherits the obligation). **Identifiers are NOT renumbered** — they are referenced from
     six sections, the harness source and three handoffs — so the table gains an explicit **order**
     and **depends-on** column instead.
  4. **The one wrong citation in 64 CORRECTED (§2.2, B-4).** *"three columns plus id"* → **two**.
     Re-opened at the pinned checkout: `0001_initial_schema.xml:98-110`, `changeSet id="4"`, declares
     `id`, `gl_account_id`, `financial_activity_type` and nothing else. **The load-bearing claim — no
     office dimension — is unaffected and TRUE**, and the adjacent `acc_gl_journal_entry` *does*
     carry `office_id` (`:119-121`), which is the contrast that makes the point.
  5. **THREE CLAIMS THAT WERE TRUE WHEN REVISION 2 WAS WRITTEN AND HAVE SINCE GONE STALE — corrected
     rather than left to rot, and flagged as stale-by-landing rather than as errors.** These are
     **beyond `A2-19`'s findings**, because the harness moved after `A2-19` measured it, and a
     reviewer should scrutinise them as revision 3's own additions.
     - **§4.4.1, §4.4, banner fact 3, §8.1 fact 3, §5.3 P-8, §7, §8.3: the `I-3`/`I-4` source guard
       NOW EXISTS.** `A2-18` built it on exactly the independence `A2-19` confirmed, and **`T208`
       wired it**. `run_guards` invokes **seven** guards, not five (`conformance.sh:1189-1213`), and
       the seventh is `guard_ledger_invariants` (`:1117-1152`, invoked `:1174`). §4.4.1 is retitled
       and states **four things it cannot see**, including that **three of its four detection classes
       inspected an EMPTY population in this tree** — no SQL, no database driver, two `NIL-COVERAGE`
       lines — so they are proven by its self-test and **by nothing in this repository** (**P-35**).
       **P-8 is marked LANDED, kept in the table with its residue rather than deleted.**
     - **Banner fact 4, §8.2, §8.3: the `loanschedule/` directory boundary is now ENFORCED.** It was
       not when revision 2 leaned on it — that is change 1 — and §8.2's *"PASS 43 remains the only
       thing anyone can say about the ledger"* is now true **because `A2-20` made it true in code**,
       not by construction. The distinction is stated at the point of the claim.
     - **Harness line drift disclosed, not patched over**: `run_guards` 843 → 938 → **1154**;
       `capability.go`'s coverage loop 243 → **246**.
  6. **`A2-19` F3 recorded as a CAVEAT and NOT fixed (§5.4).** `CounterfactualCoverage` filters on
     **class only**, never on whether the vector was **admitted**, so a **refused** vector still
     contributes coverage — `A2-19` measured it silencing the `UNBACKED` fatal (1 → 0) and inflating
     the kill tally (103 → 104). Not exploitable to green today, because the refusal itself forces
     exit 2 — **but for a different reason than §5.4 states**, so the leg §5.4 calls strong is weaker
     than its words. **This is a HARNESS defect, not DEC-2's to fix**; it is raised, not made. Blast
     radius left explicitly `[UNVERIFIED]`.
  7. **`A2-19` F5 and F6 corrected inside §4.10's block.** P-1…P-5 are **§5.3's**, not §5.1's, and
     the composite claim is §5.1 + §5.4. *"No legal way to clear it"* overstated: the harness names
     **two** outs (`grade.go:473-474`) and §5.1 closes only the first; the second — withdraw the row
     to `false` — is legal, immediate, and is step 2 of §5.4's own rule. Revision 2 erred in the
     **fail-loud** direction, which is the safe one; it is corrected because a document ratified as
     an admissibility standard may not be approximately right about what the harness does.

  **What `A2-19` CONFIRMED and revision 3 deliberately leaves untouched:** all **47/47** Fineract
  citations hit at their exact lines (overall `[VERIFIED]` hit rate **62/64 = 96.9 %**, one drift and
  one wrong, **neither a money claim** — and the one wrong was in the tier the document itself flags
  as weakest, which is evidence the tier convention works); **§5.1's five legs**, all re-opened;
  **§5.4's retraction and both its measurements**, reproduced exactly; the banner + §8.1 + §8.3
  **do** defuse the `I-3`/`I-4` misreading, and §8.3's contradict-at-the-point-of-claim technique is
  the model change 1 should have followed; and **P-8's independence of P-1…P-5**, which is what
  licensed `A2-18` to build the guard.

  **No gate was crossed and none is newly raised by the text.** **G-11 remains OPEN and revision 3
  does not close it** — `A2-21` is not authorised to ratify, and ratification is the driver's after a
  clean independent review. G-9 is applied as closed; **G-10 remains OPEN and is not decided here**;
  **G-4, G-5 and G-8 are untouched**; cutover, regulatory sign-off and licence facts remain hard
  `user` gates. `docs/adr/DEC-1-schedule-generator-adapter.md` and
  `nexus/internal/apps/loanschedule/contract/contract.go` were **not modified**; nothing under
  `nexus/`, `.softhouse/vectors/`, `.softhouse/conformance.sh` or `.softhouse/bin/` was modified.
  The unfiltered harness run was **re-measured after the edit** and reproduces the driver's
  pre-dispatch baseline exactly: probe line **present** and reading `up`, `VERDICT: PASS (exit 0) —
  43 parity vectors, 5664 cells`, contract-refusal 4, self-test 1, refused 0, inadmissible 0,
  invariant violations 0.

- **Revision 2** — DRAFT, task `A2-16`, 21 August 2026. **REJECTED** by independent review `A2-19`;
  full review at `.softhouse/reviews/a2-19-dec2-rev2/REVIEW.md`, with the falsifying transcripts
  committed beside it (`E4-ledger-refusal-ADMITTED-PASS.txt`,
  `E8-ledger-PARITY-counted-as-44.txt`, `E7-refused-vector-silences-unbacked.txt`). Recorded as gate
  **G-11 (OPEN — NOT RATIFIABLE)**. `A2-17` returned MICRO-FIX on it and applied its own 7-line fix,
  which left revision 2 as merged reviewed by nobody; `A2-19` reviewed the post-micro-fix document,
  deliberately applied **no** fix — F1 is an admissibility predicate, which its brief forbade a
  micro-fix from touching — and rejected. **The original revision-2 entry follows unchanged, as the
  record of what revision 2 claimed.**

- **Revision 2 (as drafted)** — DRAFT, task `A2-16`, 21 August 2026. **NOT RATIFIED; `A2-16` does
  not ratify it.** A further independent review must pass clean first, and ratification is then the
  driver's under standing policy **P-2**. Drafted in response to `A2-14`'s **REJECTION** of revision
  1 — a rejection on **shape**, not on honesty or research, with every one of revision 1's
  `[VERIFIED]` claims confirmed against real source at the exact cited line.

  **Changes, all of them:**

  1. **R-1 resolved (§5.1, §5.2, §5.3).** Revision 1's *"Disposition 3 needs no new machinery, and
     that is the argument for it"* is **retracted as false**. §5.1 establishes in code — and by
     **three positive controls that were run**, not reasoned — that no `ledger` vector is
     expressible: the schema string names `loanschedule`, `Request`'s thirteen fields have no home
     for a `ledger` input, `Expect.Kind` is `{schedule, refusal}`, `Expect.Sentinel` is the three
     contract sentinels, **no vector class can hold an observed non-schedule oracle answer**, and
     `StructuralCellFields()` is a whitelist of three that rejects all six proposed cells. §5.2
     **decides to EXTEND** — as a *second* schema and comparator, never a widening of the first,
     with the reasoning for each rejected alternative and an explicit refusal to touch the frozen
     `contract.go`. It states the **43-vector non-regression demonstration** the extension owes.
     §5.3 turns §5 into **eight named preconditions on `A2-15`**, none of which exists.
  2. **R-2 corrected (§5.4).** Revision 1's *"An empty context directory is already FATAL, and is
     not silent"* is **retracted as false** for the unfiltered run, which is the run
     `conformance.sh` actually performs. **Measured both ways** on this task's own tree: unfiltered
     → **exit 0, `VERDICT: PASS`**, `ledger` named nowhere but the no-float census line; filtered →
     exit 2. The leg that *does* hold — the **registry-wide** capability fatal — was also measured,
     by appending one experimental row to a temp copy of `capabilities.json`: **exit 2**. Revision 1
     presented the two as interchangeable; they are not, and a **normative sequencing rule** for
     `ledger` capability rows now follows from the difference.
  3. **R-3 resolved (§2.2, §3.2, §4.2, §4.4).** The prose-versus-list contradiction — the same
     defect class as the still-**OPEN** `G-5` on DEC-1 — is settled by **keeping the money and
     narrowing the prose**. `B-5` is rescoped to `ledger_inprocess_resolver`, the one seam `G-01`
     refuses; `G-07`/`G-08` are kept and **scoped to vectors that assert a money cell**, which is
     not the same as scoping by seam; `I-1`/`I-2` are split into *gradeable in principle from the
     captures in hand* (**yes**) and *graded today* (**no**).
  4. **§9 item 10 CLOSED (§4.2, §9).** `ACCRUAL_UPFRONT` **falls through** into `ACCRUAL_PERIODIC`
     on the loan side and writes the full accrual set; savings writes nothing. Two inherited wording
     errors about `default:` labels corrected. `G-03`'s refusal now rests on the one ground that
     survives: **no capture at `accountingRule = 4`**.
  5. **§9 item 3 CLOSED (§4.3).** T186 has **ruled**; revision 1's live forward reference is
     replaced by the ruling, and T186 **(c)** — the stored vector carries integer minor units — is
     stated as an explicit rule for `ledger` vectors.
  6. **"Nothing grades the ledger" made structurally unmissable** — the banner at the head of the
     document, **§4.4.1** (the `I-3`/`I-4` guard did not exist when revision 2 was written; the guards
   are enumerated — **revision 3 corrects this: it exists now, and §4.4.1 states its limits**),
     **§4.9**'s block on the unrepresentable 404, and **§8.1**. Revision 1's §8 sentence about guard
     coverage is kept, marked **true for float and `gofmt` only**, and explicitly contradicted where
     it would otherwise be read as covering the append-only and derived-balance invariants.
  7. **`mapping.paymenttype.null` listed `blind` on all four seams (§4.10)**, because `Assess`
     interpolates the named reason only on the `blind`/`ungraded` paths — an ABSENT row refuses with
     generic text and loses the diagnostic the row exists to carry.

  **No gate was crossed and none is newly raised by the text.** G-9 is applied as closed; **G-10
  remains OPEN and is not decided here**; cutover, regulatory sign-off and licence facts are
  untouched. `docs/adr/DEC-1-schedule-generator-adapter.md` and
  `nexus/internal/apps/loanschedule/contract/contract.go` were **not modified** — the `A2-16`
  handoff records both sha256 digests before and after. **No Go was written and `nexus/` was not
  touched.**

- **Revision 1** — DRAFT, task `A2-13`, 21 August 2026. First draft. **Not ratified, no PIN digest,
  and no Go authored.** Reviewed independently by `A2-14` (local fire `20260821-125942`), verdict
  **REJECTED** on three shape findings; full review at
  `.softhouse/reviews/A2-14-DEC2-gl-accounting-contract-review.md`. Its factual base survives into
  revision 2 substantially unchanged.
