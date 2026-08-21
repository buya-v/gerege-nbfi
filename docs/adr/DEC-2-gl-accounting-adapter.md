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
> 2. **No `ledger` vector CAN exist.** The store's only accepted schema is
>    `gerege.loanschedule.vector/v1` and its `Request`/`Expect` shapes are loan-schedule shapes. §5
>    establishes this in code and by three failing positive controls. **This is not a gap somebody
>    forgot to fill; it is machinery that has not been built.**
> 3. **No guard enforces `I-3` (balances are derived) or `I-4` (append-only).** `run_guards` invokes
>    exactly five guards and **all five are about floating point, `gofmt` and exception scope**
>    [VERIFIED by this task: `.softhouse/conformance.sh:843-849`]. **Nothing anywhere in this
>    repository looks for a balance write path, or for an `UPDATE`/`DELETE` against
>    `acc_gl_journal_entry`.**
> 4. **The "PASS 43" everybody quotes is `loanschedule`'s.** All 43 promoted parity vectors are in
>    the `loanschedule/` directory. **Zero of them touch a GL account, a mapping, a financial
>    activity or a journal entry.**
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


**Status: DRAFT (revision 2), 21 August 2026, drafted by task `A2-16`. NOT RATIFIED. `A2-16` may
not ratify it and does not.** Revision 1 (`A2-13`) was **REJECTED** by independent review
(`A2-14`, local fire `20260821-125942`) on three shape findings, all three resolved here — §5 for
R-1 and R-2, §2.2/§3.2/§4.2/§4.4 for R-3, §9 item 10 for the review's finding F-A. **A further
independent review must pass clean before the driver may ratify** under standing policy **P-2**;
until then `A2-15` (promote GL vectors) stays blocked, and §5.3 names work that must land before
`A2-15` could succeed even against a ratified contract.

**What survived the rejection, so that it is not re-litigated.** A2-14 opened over thirty source
and capture citations and found **every `[VERIFIED]` claim traced to real source at the exact
cited line** — none overstated, none mis-cited, none fabricated. G-9 was applied as closed; G-10
was recorded and explicitly left undecided, so no gate was crossed; default-deny is genuinely
inherited; no float is admitted anywhere Gerege owns the number. The rejection was about
inferences drawn on top of that base, and this revision changes those inferences and only those.
Claims carried forward unchanged from revision 1 keep revision 1's citation tier; claims this
task re-opened are marked as such.

**No PIN digest appears in this document**, and §1.1 explains why one *cannot* appear yet: unlike
DEC-1, this ADR is not written against an existing frozen Go file.

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

**Reading "this task" across two revisions.** Unqualified *"this task"* means **`A2-13`**, the
author of revision 1, and its verifications stand — an independent review re-opened over thirty of
them and every one traced to real source at the exact cited line. Where **`A2-16`** re-opened a
claim, corrected one, or measured something new, the citation says so explicitly: **`[VERIFIED by
this task]` inside material revision 2 added**, or **`[RE-VERIFIED by A2-16]`**, or **`[MEASURED by
this task]`** for a harness run this task actually performed rather than reasoned about. Every
`[MEASURED]` in this document is `A2-16`'s and was produced by running the real conformance binary
against a **temporary copy** of the vector store; **no file under `.softhouse/vectors/` or `nexus/`
was modified by revision 2.**

**Harness `file:line` citations drift, and revision 2 re-took the ones it relies on.** Several
harness line numbers moved between revision 1 and revision 2 as unrelated tasks landed — for example
the `-context` flag append and `run_guards`, both cited by revision 1's reviewer at line numbers that
no longer hold. Every harness citation in §4.4.1, §5.1, §5.2 and §5.4 was re-taken by `A2-16` against
its own tree. **A harness citation elsewhere in this document may be stale by a few lines; the facts
behind them were not observed to have changed.**

**Nothing in this document is asserted from memory.** §9 enumerates every `[UNVERIFIED]` and
why it could not be closed. Per the project honesty rule, an honest negative outranks a
plausible positive: a DEC-2 with twenty honest gaps is worth more than one that reads complete
and is wrong in three places.

---

## 0. Why this document exists

`.softhouse/vectors/` contains exactly two context directories, `loanschedule/` and `_selftest/`
[VERIFIED: `ls .softhouse/vectors/`, by this task]. Task **A2-8** merged the port of the GL
account model, product-to-account mapping resolution and financial activity accounts to `main`,
and **not one parity vector grades it**. The conformance run reports `PASS 43`; all 43 are
`loanschedule`'s [VERIFIED BY A2-8, NOT RE-OPENED HERE — A2-8's own handoff says so plainly:
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
| **B-4** | **The office.** | `acc_gl_financial_activity_account` is tenant-global — three columns plus id, no office dimension [VERIFIED BY A2-1 AND A2-2 from `0001_initial_schema.xml:99-109`, NOT RE-OPENED HERE; corroborated by this task from `A2-150`, whose dump of that table projects `id, financial_activity_type, gl_account_id` and joins the account]. |
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
| **I-3** | Balances are DERIVED, never written | No write path to any balance column exists in the Go tree | **NO — STRUCTURAL ONLY.** A vector is a snapshot of oracle output; it cannot observe the *absence* of a write path. Gradeable only by a source-level guard over the Go tree. And the oracle is **not** a positive example: `m_trial_balance.closing_balance` is a written, stored, **unsigned** sum wearing a balance's name [VERIFIED BY A2-2's re-derivation of `UpdateTrialBalanceDetailsTasklet.java:81` reading `JournalEntryRepository.java:61`, NOT RE-OPENED HERE]. It is deliberately **not ported** (§7). | **NO, AND NOT BY ANYTHING ELSE EITHER.** No such guard exists. `run_guards` invokes five guards and all five are about float, `gofmt` and exception scope [VERIFIED by this task: `.softhouse/conformance.sh:843-849`]. See the correction below. |
| **I-4** | The ledger is append-only | No `UPDATE`/`DELETE` against `acc_gl_journal_entry` from application code | **NO — STRUCTURAL ONLY.** "No update ever happened" is not observable from a capture. Partial exception: a reversal is observable *as a row*, because the table carries a `reversed` flag [VERIFIED BY A2-13 from `JournalEntry.java:79`, NOT RE-OPENED HERE]. | **NO, AND NOT BY ANYTHING ELSE EITHER.** Same as I-3: no guard looks for an `UPDATE`/`DELETE` against `acc_gl_journal_entry`. |
| **I-5** | Corrections are reversing entries | A correction adds a leg pair; it never mutates one | **UNGRADED TODAY.** The A2 corpus contains no reversal: `A2-150`'s journal dump does not project `reversed` or `reversal_id` and its six rows are three ordinary pairs [VERIFIED by this task]; A2-8's grading table lists no reversal grading [VERIFIED BY A2-8, NOT RE-OPENED HERE]. Refused with `ErrNoDiscriminatingVector`; retired by one capture. §9 item 13. | **NO.** Nothing to grade, and nothing to grade it with. |
| **I-6** | Holds are postings and alter `available` only, never posted `balance` | — | **OUT OF THE CONTRACT DOMAIN.** No hold concept exists in A2's three tables. Refused with `ErrUnsupportedConfiguration`. | **N/A.** |
| **I-7** | `Idempotency-Key` on every money-movement POST | — | **NOT APPLICABLE TO THIS CONTRACT, and that must be said rather than assumed.** DEC-2's surface exposes no HTTP endpoint and moves no money; it is a value computation. The obligation is real and lands on **A1** (the posting engine) and on the adapter's HTTP layer. A `ledger` conformance PASS says nothing whatever about it. | **N/A** — and note that today there is no `ledger` conformance PASS to say nothing with. |

**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope.

### 4.4.1 THE GUARD I-3 AND I-4 REQUIRE DOES NOT EXIST

Revision 1 stated the requirement correctly and never claimed the guard existed. It also never said
it **doesn't**, and it placed the requirement four lines above a paragraph about guards that *do*
run. A reader will merge them. **This subsection exists so they cannot be merged.**

**`run_guards` invokes exactly five guards** [VERIFIED by this task, `.softhouse/conformance.sh:843-849`,
opened and read]:

```
  guard_no_float_in_vectors
  guard_no_float_in_harness
  guard_gofmt
  guard_no_float_in_capture_requests
  guard_no_narrow_catch_in_capture_rigs
```

**All five concern floating point, source formatting and exception scope. Not one of them looks
for:**

- a write path to any balance column (that is **I-3**);
- an `UPDATE` or `DELETE` statement against `acc_gl_journal_entry`, or any Go call that would emit
  one (that is **I-4**);
- a derived-balance function that caches instead of deriving;
- a correction path that mutates a leg instead of adding a reversing pair (that is **I-5**).

**So the normative requirement in the table above is, today, unsatisfied.** The correct reading of
this whole subsection is: *DEC-2 obliges I-3 and I-4, names the only mechanism that could enforce
them, and records that the mechanism has not been written.* Anyone who ratifies this document
ratifies that gap along with it, knowingly. Writing the guard is named as a precondition in §5.3 and
as a follow-up; it is **not** done by this ADR, which writes no code.

**One inherited claim this draft CORRECTS rather than repeats.** A2-8's follow-up **F-1** records
that `conformance.sh`'s hard guards were scoped to `loanschedule`, so a float in
`nexus/internal/apps/ledger/` would leave the harness green. **That was true when A2-8 wrote it
and is FALSE now: task T166 widened both guards to the Go module root.** [VERIFIED by this task,
re-opened rather than taken on the report: `conformance.sh:401` sets
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
> red — including `-context=loanschedule` — with no legal way to clear it, because §5.1 establishes
> that no `ledger` vector can be admitted at all until §5.3's P-1…P-5 exist.

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
and **no evidence string at all** [VERIFIED by this task: `capability.go:308-331`, the three arms
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

`.softhouse/vectors/` holds **43 promoted parity vectors, all `loanschedule`** [VERIFIED by this
task: the store's only context directories are `loanschedule/` and `_selftest/`]. **The `ledger`
context has none.** DEC-1 was frozen against a twelve-capture corpus re-derived from source to
the minor unit; **DEC-2 would be frozen against a corpus that does not yet exist in the store.**

What *does* exist, and it is substantial but it is **not** the same thing:

- **The A2 capture corpus** — `.softhouse/capture/tierA-a2/`: **147 JSON response bodies** under
  `out/` (of 444 files there, the rest being the paired `.http` and `.status` records) and **89
  request bodies** under `req/` [both counts VERIFIED by this task with `ls | wc -l`], taken from
  the running oracle at tenant `gerege` on the pinned commit.
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
promoted vectors** — and, revision 2 adds, **that could not be promoted if somebody tried.**

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
`vector.go:279-293`, the struct read in full]. **Not one of §4.2's eleven predicates is about
anything in that list.** A `ledger` request is a product id, a placeholder code, a payment type id, a
product type, an accounting rule and a seam; the schema has a home for none of them, and decoding is
**strict** — an unknown field is a hard load failure, not an ignored key [MEASURED, positive control
1 below].

**(3) `Expect.Kind` is the closed set `{schedule, refusal}`, and `Expect.Sentinel` must be one of
the three CONTRACT sentinels.** [VERIFIED by this task: `vector.go:418-431` documents both;
`admit.go:180-194` is the `switch` whose `default` arm is *"expect.kind %q is neither \"schedule\"
nor \"refusal\""*; `enums.go:92-103` `sentinelByName` resolves exactly `ErrInvalidRequest`,
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
closed [VERIFIED by this task, `admit.go:130-176`]:

| class | the rule that excludes an observed oracle 404 | source |
|---|---|---|
| `parity` | **"a parity vector must expect a schedule; a refusal is not an oracle observation"** — the check is `v.Expect.Kind != "schedule"` | `admit.go:517-519` |
| `contract-refusal` | requires `provenance.kind == "contract"` and **`oracle.seam == "none"`** — *"nothing was captured"* — and the sentinel must be one of the three | `admit.go:154-171`, `enums.go:93-103` |
| `selftest` | must live under `_selftest/`, must be hand-authored, **never counts toward parity** | `admit.go:131-143` |

Read together: **the schema's model of an oracle observation IS a schedule.** A refusal is, by
construction, something the *contract* did, derived from contract text, captured from nothing. That
is a coherent model of DEC-1's world and it has no room in it for a context whose oracle answers
"404, `error.msg.productToAccountMapping.not.found`" and where reproducing that string exactly *is*
parity.

**(5) `StructuralCellFields()` is a hard-coded whitelist of three, and it rejects all six cells
revision 1 proposed.** `func StructuralCellFields() []string { return []string{"kind", "from_date",
"due_date"} }` [VERIFIED by this task: `vector.go:571-583`]. Admission compares against it
literally, and refuses anything else with *"names field %q, which is not one of the non-money cells
this harness compares"* [VERIFIED: `admit.go:355-361`]. Revision 1's proposed
`resolved.account_id`, `resolved.gl_code`, `resolved.classification`, `refusal.code`,
`refusal.http_status`, `refusal.message` are **all six** outside it — and so is the `period[<n>].`
prefix the cell parser requires before it even looks at the field name [VERIFIED:
`admit.go:330-344`, `ParseDivergentCell`'s four-way form vocabulary].

**And the whitelist's own doc comment explains why widening it is not a one-line change.** The three
fields are *"exactly the NON-MONEY cells `diffSchedule` actually compares"*, and the stated reason
for the whitelist is that *"naming a cell the harness does not compare would let a vector claim a
kill nothing could ever detect"* — finding **T9-F1b**, which is the defect that once printed nine
killed capabilities at exit 0 over a store whose dates were garbage [VERIFIED by this task:
`vector.go:571-580` and the `StructuralKillIsCompared` comment at `:592-627`]. **A cell is
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
  request [VERIFIED by this task: `registry.go:26-28` declares `impls map[string]contract.ScheduleGenerator`; `grade.go:508` and `registry.go:173` both route every vector through `v.Request.ContractRequest()`]. Widening the schema without
  widening those types produces a vector nothing can be asked to answer.
- *Adopted: a `ledger`-specific schema (`gerege.ledger.vector/v1`) with its own `Request`, its own
  `Expect`, its own comparator and its own cell whitelist*, sharing the store root, the file census,
  the duplicate-case-id check, the raw-token float scan and the capability registry. Shared where
  the property is about **the store**; separate where the property is about **what a comparator
  compares**.

**Second — and this constrains the extension absolutely: the 43 must still pass.** The extension
touches the same harness DEC-1's 43 promoted parity vectors depend on, and those 43 are the only
parity evidence this program has. **A `ledger` extension that costs one of them is not a trade this
contract permits.** The demonstration required of whoever builds it, stated so it cannot be
improvised:

1. **Before/after digests of all 43 vector files** under `.softhouse/vectors/loanschedule/`. A
   second schema string means no existing vector file changes a byte; if any digest moves, the
   extension has widened the first schema and is out of bounds.
2. **`bash .softhouse/conformance.sh` unfiltered, before and after**, both reporting `VERDICT: PASS
   (exit 0)` with **`parity vectors PASS 43 FAIL 0`** and the **same cell count**. The baseline this
   task measured on its own tree is `43 parity vectors match the pinned reference oracle, **5664
   cells compared**` [MEASURED by this task]. A cell count that moves means the comparator changed
   under the loanschedule corpus, which is a regression whatever the verdict line says.
3. **`bash .softhouse/conformance.sh loanschedule` before and after**, identical but for
   timestamps.
4. **No diff to `nexus/internal/apps/loanschedule/contract/contract.go`, and no DEC-1 amendment.**
   If the extension turns out to require either, that is a hard `user` gate — **raise it, do not
   make it.**
5. **Invoke with `bash`, never `sh`** — exit 3 is a wrong-interpreter refusal, not a failure — and
   never `gofmt -w` `contract.go`; `gofmt -l` reporting exactly that one file is the expected state
   (standing instruction, **G-3 CLOSED-OPTION-A**).

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

### 5.3 Preconditions on `A2-15` — none of which exist today

`A2-15` cannot promote a `ledger` vector until **all** of the following exist. They are
preconditions, not follow-ups, and §8 repeats the consequence.

| # | precondition | why, in one line |
|---|---|---|
| **P-1** | A **`ledger` vector schema** with a request shape covering product id, product type, accounting rule, slot family, slot code, payment type id and seam | §5.1 (2) — strict decode rejects every one of them today |
| **P-2** | An **expectation shape for an oracle-faithful refusal** — HTTP status, error code, message text — that is **not** one of the three contract sentinels and is **not** confusable with them | §5.1 (3), §4.9(b); this is the context's commonest graded output |
| **P-3** | A **class** an observed non-schedule oracle answer can be filed under, since `parity` requires a schedule and `contract-refusal` requires `oracle.seam == "none"` | §5.1 (4) — the hardest of the five |
| **P-4** | A **comparator** for `ledger` outputs, and a **cell whitelist derived from it** rather than authored beside it | §5.1 (5); the whitelist's meaning is "what the comparator compares" (T9-F1b) |
| **P-5** | **Money cells** — `int64` minor-unit **strings**, paired with the oracle's own emitted characters as a transcription cross-check only | §4.3, T186 (c); required for `I-1`/`I-2` to be gradeable at all |
| **P-6** | A **decision on `capabilities.json`** — its schema id is the hard constant `gerege.loanschedule.capabilities/v1` and `dec1_revision` is singular. Appending `ledger` rows works today, but the file is named and versioned for one context | §4.10; **not DEC-2's decision to take**, and it must not be improvised |
| **P-7** | The same decision for **`PIN.json`** — schema `gerege.loanschedule.pin/v1`, singular `contract_file` / `contract_sha256` [VERIFIED by this task: `admit.go:65-66`] | a second context implies a second pinned contract file, and the pin has one slot |
| **P-8** | The **`I-3`/`I-4` source guard** §4.4.1 requires | it does not exist; without it, ratifying DEC-2 obliges two invariants nothing checks |

**P-1 through P-5 are the schema extension. P-6 and P-7 are decisions. P-8 is independent of all of
them** — it is a guard over the Go tree and could be written today, against the ported package that
already exists.

### 5.4 What actually enforces Disposition 3 in the DEFAULT run — R-2, corrected and MEASURED

**Revision 1 claimed *"An empty context directory is already FATAL, and is not silent."* That claim
is FALSE, and revision 2 retracts it.** The narrower sentence beside it — that the fatal *names the
context-filtered path*, so `conformance.sh ledger` over an empty `ledger/` cannot pass — is **true**.
Revision 1 presented the two as one argument. They are not, and the difference is the difference
between an enforcement and nothing.

**The mechanism, re-read in source by this task:**

- **The fatal is guarded on the WHOLE returned vector set, not on the requested directory.**
  `if len(vectors) == 0 { … "ZERO VECTORS FOUND under %s" … }`, and `where` is the store root unless
  a context filter was given [VERIFIED by this task: `grade.go:334-342`].
- **`LoadStore` returns ALL contexts when the filter is empty:** `if contextFilter == "" { return
  all, loadErrs, nil }` [VERIFIED by this task: `vector.go:950-952`].
- **`conformance.sh` passes `-context` only when it was given an argument:**
  `[ -n "$context" ] && args+=("-context=$context")` [VERIFIED by this task:
  `.softhouse/conformance.sh:894`].

So on the default invocation `len(vectors)` is 43-plus, the fatal never fires, and the third fatal —
`NO PARITY VECTOR WAS GRADED`, `ParityPass == 0 && len(vectors) > 0` [`grade.go:418-425`] — is inert
for the same reason, because `ParityPass` is 43.

**MEASURED by this task on its own tree**, real binary, temp copy of the store, empty `ledger/`
directory added:

| run | result |
|---|---|
| unfiltered — **what `conformance.sh` performs** | **exit 0**, `VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5664 cells compared`. **The string "ledger" occurs exactly once in the entire output, and it is the no-float census line `covered: nexus/internal/apps/ledger`** — a statement about the Go source tree, not about a vector. No warning. No zero-count. Nothing. |
| `-context=ledger` | exit 2, `VERDICT: UNUSABLE`, `ZERO VECTORS FOUND under <tmp>/ledger` |

**An empty `ledger/` therefore passes silently, and it does so in the run everybody quotes.**

**The leg that DOES hold, and it is a strong one — also MEASURED.** The capability fatal is
**registry-wide**: `CounterfactualCoverage` ranges over `r.GradedCapabilities()`, the whole registry,
with no context scoping anywhere in it [VERIFIED by this task: `capability.go:232-278`]. This task
appended one experimental row to a **temp copy** of `capabilities.json` — `ledger.probe.a216`,
`in_graded_domain: true`, no covering kill — and re-ran **unfiltered**:

```
    UNBACKED in_graded_domain claims: ledger.probe.a216
    * THESE CAPABILITIES ARE MARKED in_graded_domain BUT NO PARITY VECTOR KILLS A NAMED
      WRONG IMPLEMENTATION FOR THEM: ledger.probe.a216. …
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

[MEASURED by this task. The row was added to a temp store only; `.softhouse/vectors/capabilities.json`
was not modified.]

**So the enforcement is real, and it fires on the REGISTRY ROWS, not on the empty directory.**
Revision 1 presented those two as interchangeable legs of one argument and they are not
interchangeable at all: if §4.10's rows are never authored, or are authored `in_graded_domain:
false`, `ledger/` stays empty and **invisible indefinitely**, at exit 0, in every run.

**And §5.1 sits on top of this, which produces the ordering rule below.** Once the rows land as
`true`, the fatal fires — and until P-1…P-5 exist, **no admissible `ledger` vector can be written to
clear it.** The run would be permanently red with no legal way out. That is not a hypothetical: it
is exactly the state the measurement above puts the harness in.

**NORMATIVE SEQUENCING RULE, and revision 2 adds it because the measurement forces it.** `ledger`
capability rows are authored in this order and no other:

1. **The §5.3 machinery lands first** (P-1…P-5), with the 43-vector demonstration of §5.2.
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
`vector.go:940-944`] — and an empty context directory is precisely a store fact that is invisible
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

- **Writing the `ledger` vector schema, comparator, cell whitelist or `I-3`/`I-4` guard** — §5.3's
  eight preconditions. **This ADR writes no code**, and §1.1 gives the reason. Naming machinery is
  not building it, and revision 2 is careful to claim only the former.

---

## 8. Consequences

### 8.1 NOTHING GRADES THE LEDGER — say it here, not only in the banner

The banner at the head of this document says this. It is repeated here, at the end, because §8 is
what a ratifier reads last and because revision 1's §8 said something adjacent that a reader will
merge with it.

**Four facts, each measured by this task:**

1. **Zero `ledger` vectors exist.** The store's only context directories are `loanschedule/` and
   `_selftest/`.
2. **Zero `ledger` vectors CAN exist** — §5.1, established in code and by three positive controls
   that were run. Preconditions P-1…P-5 (§5.3) do not exist.
3. **Zero guards enforce `I-3` or `I-4`.** `run_guards` invokes five and all five are about float,
   `gofmt` and exception scope [`.softhouse/conformance.sh:843-849`]. §4.4.1.
4. **The 43 passing parity vectors are `loanschedule`'s.** None touches a GL account, a mapping, a
   financial activity or a journal entry.

**Ratifying DEC-2 changes none of the four.** It writes down a boundary; it grades nothing. The two
must never be confused, and a citation of this document as evidence of ledger coverage is a
misreading of it.

### 8.2 If ratified

- `.softhouse/vectors/ledger/` becomes a legal context directory — **and stays unusable until the
  §5.3 machinery lands**, at which point `conformance.sh ledger` becomes a meaningful command.
- `A2-15` has an admissibility standard: §4.2's predicates, §4.6's A-1…A-4, §4.10's registry, and
  §5.5's `graded_against` requirement — **and eight preconditions (§5.3) it cannot start without.**
- The GL/accounting context acquires a boundary a regulator can be shown. **"PASS 43" remains the
  only thing anyone can say about the ledger, and what it says is "this is about a different
  context".**

### 8.3 If ratified, these remain true and must not be misread

- **A `ledger` conformance PASS would mean "matches the reference oracle on captured vectors, inside
  the graded domain".** It would not mean the ledger is correct, and it would mean nothing at all
  about savings, shares, working-capital loans, charges, reversals, holds, or nineteen of the
  twenty-three cash placeholder slots. **Today there is no such PASS to misread.**
- **`conformance.sh`'s hard guards DO cover `nexus/internal/apps/ledger/` today — FOR FLOATING POINT
  AND `gofmt`, AND FOR NOTHING ELSE.** T166 widened both roots to the Go module root, re-verified by
  this task (§4.4), and this task's own unfiltered run printed `covered: nexus/internal/apps/ledger`
  in the no-float census [MEASURED]. **That coverage is not `I-3` and it is not `I-4`.** Revision 1
  wrote *"That is what makes I-3 and I-4 enforceable at all"* — true in the sense that a guard must
  be able to *see* the tree before it can check anything in it, and **certain to be read as saying
  the invariants are checked. They are not checked. No guard for either exists** (§4.4.1). What
  remains true from revision 1 is the forward warning: **re-narrowing either root would silently
  un-cover this tree**, and would do so while still printing a healthy-looking file count.
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

---

## 10. Revision history

- **Revision 2 (this document)** — DRAFT, task `A2-16`, 21 August 2026. **NOT RATIFIED; `A2-16` does
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
     document, **§4.4.1** (the `I-3`/`I-4` guard does not exist; the five guards are enumerated),
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
