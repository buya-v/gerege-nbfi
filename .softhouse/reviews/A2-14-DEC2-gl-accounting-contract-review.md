# A2-14 — independent review of DEC-2 (GL / accounting adapter contract), revision 1

**Reviewer:** `A2-14`. **Artefact:** `docs/adr/DEC-2-gl-accounting-adapter.md`, 989 lines, drafted by
`A2-13`, merged to `main` as a DRAFT at `cc657f9`.
**Fineract pinned commit:** `426a23544e8426a38ae43ae404670a0a7e85b9eb`
[VERIFIED: `git rev-parse HEAD` in `/Users/buv/fineract`, by this task].

**VERDICT: REJECTED.** Three rejection-grade findings, all in or downstream of §5, plus four
non-blocking findings. None of them is a defect of verification discipline — see
*What I checked and found clean*, which is unusually long and which I want on the record.

---

## Frozen files

| file | expected | before | after |
|---|---|---|---|
| `docs/adr/DEC-1-schedule-generator-adapter.md` | `49dc8923…` | `49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab` | identical |
| `nexus/internal/apps/loanschedule/contract/contract.go` | `0db73d4a…` | `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` | identical |

Neither moved. A2-13 touched exactly two files — `docs/adr/DEC-2-gl-accounting-adapter.md` and its
own handoff [VERIFIED: `git show --stat e18fe5b`]. It did **not** modify `gates.md`, DEC-1 or
`contract.go`.

---

## R-1 (REJECTION) — §5's central argument is false. No `ledger` vector is expressible against the frozen schema, and Disposition 3 needs substantial new harness machinery

DEC-2 §5 states, in bold: *"**Disposition 3 needs no new machinery, and that is the argument for
it.**"* The three fatals it cites do exist and do fire — I re-opened all three and confirm the
citations (§5 verified below). **But the argument they support is wrong**, because a `ledger`
vector cannot be written at all against the current, frozen vector schema. Three independent
blockers, each verified in code:

**(a) `Expect.Kind` has no value a resolution answer can take.**
`Expect.Kind` is `"schedule"` or `"refusal"`, *"Never both, and never neither"*
[VERIFIED: `nexus/internal/apps/loanschedule/conformance/vector.go:416-420`]. `Expect.Periods` is
`[]ExpectPeriod`, schedule-shaped [`:432-434`]. DEC-2's answer type — a resolved GL account
(`{id, gl_code, name, classification}`) — is neither.

**(b) DEC-2's most common graded output has no representation.**
`Expect.Sentinel` *"is required when Kind is `refusal`: one of `ErrInvalidRequest`,
`ErrUnsupportedConfiguration`, `ErrNoDiscriminatingVector`"*, matched EXACTLY
[VERIFIED: `vector.go:422-428`]. DEC-2 §4.9 is emphatic and correct that an oracle-faithful HTTP
404 / 403 is an **ANSWER**, not a contract refusal — *"A port that returned
`ErrNoDiscriminatingVector` where the oracle returns a 404 would 'refuse' a case that is in fact
fully graded"*. §4.9's own table lists five oracle-refusal families as the graded output of this
context. **None of them can be expressed**: not a `schedule`, and not one of the three contract
sentinels.

**(c) The six cells §5 proposes are rejected at admission, not merely absent.**
`StructuralCellFields()` returns the hard-coded closed set `{"kind", "from_date", "due_date"}`
[VERIFIED: `vector.go:581-583`]. `admitCounterfactual` refuses any field outside it — *"names field
%q, which is not one of the non-money cells this harness compares … A cell the harness never
compares cannot be the site of a kill anything could detect"* [VERIFIED: `admit.go:356-361`].
`ParseDivergentCell` accepts only `period[<n>].<field>`; anything else returns
`DivergentCellNotACell` [VERIFIED: `admit.go:415-431`], and its doc comment is explicit that
*"There is one parser for divergent cell names in this harness and this is its vocabulary"*
[`admit.go:391-395`]. `StructuralKillIsCompared` then credits a non-well-formed cell as covering
**nothing** [VERIFIED: `vector.go:661-672`].

So `resolved.account_id`, `resolved.gl_code`, `resolved.classification`, `refusal.code`,
`refusal.http_status`, `refusal.message` — all six of §5's proposed cells — make a vector
INADMISSIBLE and cover no capability.

**Why this is rejection-grade and not a follow-up.** DEC-2 §5 says *"most kills will be
**structural** rather than money-valued … because the answers are account ids and strings"*. For a
context whose entire corpus is structural, the structural-kill machinery rejects every cell it would
need. The section a ratifier is told not to skim rests on an argument that is false in the direction
that matters: it tells `A2-15` the harness already accommodates this work.

**A2-13 knew.** Its handoff follow-up **F-2(b)** says the cell vocabulary *"must be extended"* and
**F-2(c)** raises `PIN.json`'s singular `gerege.loanschedule.pin/v1` schema. The ADR — the artefact
that gets ratified — states the opposite conclusion three sentences before it half-concedes the
point as *"the grader task's work"*. A follow-up in a handoff does not qualify a claim in an ADR.

---

## R-2 (REJECTION) — MEASURED: an empty `ledger/` **does** pass silently, in the run that actually runs

DEC-2 §5's second bullet is headed, in bold: *"**An empty context directory is already FATAL, and is
not silent.**"* The sentence that follows is narrower and is **true**: *"it names the
**context-filtered** path, so `conformance.sh ledger` over an empty `ledger/` cannot pass."* The
heading is false, and the heading is what a ratifier carries away.

**Measured, not reasoned.** I built the real conformance binary from the pinned tree
(`./internal/apps/loanschedule/conformance/cmd/conformance`), copied `.softhouse/vectors` to a temp
store, and created an empty `ledger/` directory in it:

| run | result |
|---|---|
| `conformance -store=<tmp> -oracle-probe=up` (**unfiltered — what `conformance.sh` performs**) | **exit 0, `VERDICT: PASS`, "parity vectors PASS 43".** `ledger` is not named anywhere in the output. No warning, no census line, nothing. |
| `conformance -store=<tmp> -oracle-probe=up -context=ledger` | exit 2, `VERDICT: UNUSABLE`, `ZERO VECTORS FOUND under <tmp>/ledger` |

**The mechanism**, verified in source: `conformance.sh` appends `-context` only when it was given an
argument — `[ -n "$context" ] && args+=("-context=$context")` [VERIFIED: `.softhouse/conformance.sh:855`].
`LoadStore` returns every context when the filter is empty — `if contextFilter == "" { return all,
loadErrs, nil }` [VERIFIED: `vector.go:950-952`]. So `len(vectors) == 0` is false (loanschedule's 47
files load), and the `ZERO VECTORS FOUND` fatal at `grade.go:334-342` never fires.

The third fatal is likewise inert in the default run: `NO PARITY VECTOR WAS GRADED` requires
`ParityPass == 0` [VERIFIED: `grade.go:418-425`], and loanschedule supplies 43.

**What survives, and it is the strong half.** The capability fatal at `grade.go:407-415` **is**
global: `CounterfactualCoverage` ranges `r.GradedCapabilities()` over the whole registry, not a
context-scoped subset [VERIFIED: `capability.go:244-278`]. So once §4.10's rows land in
`capabilities.json` with `in_graded_domain: true` and no covering kill, the unfiltered run does go
red. **That is a real and sufficient enforcement — but it is triggered by the registry rows, not by
the empty directory**, and DEC-2 presents the two as interchangeable legs of one argument. They are
not. If the rows are never authored, or are authored `false`, `ledger/` stays empty and invisible
forever, and nothing in DEC-2 or the harness says so.

**The fix is not mechanical** — it requires deciding what enforces Disposition 3 (a `ledger`-row
requirement in `capabilities.json`? a `conformance.sh` change to refuse an empty context directory
in the unfiltered run?), which is a normative statement in a contract being frozen.

---

## R-3 (REJECTION, G-5 class) — prose and enumerated list contradict each other on whether the contract carries money

This is the exact defect class the brief warned about, in the same structural position as the
still-open **G-5** on DEC-1: a prose sentence excludes what the enumerated graded-domain list
admits.

**The prose says the contract carries no money.**
- §2.2 B-5: *"**Any amount, and any currency.** Neither is a parameter and neither appears in the
  body … **No money flows through this seam at all.**"*
- §2.2: *"**DEC-2's contract is an account-selecting function**: its answers are ids, names, GL
  codes, enum values and refusal strings."*
- §3.2: *"**B-5 (money)** is **not a blind spot at all**; it is a correct statement that this seam
  is money-free, and **the contract carries no amount**."*
- §5: *"because the answers are account ids and strings."*

**The enumerated graded domain (§4.2) says it does.**
- `G-07  Currency.Code == "MNT" and Currency.MinorUnitDigits == 2`
- `G-08  every amount's wire text is EXACT at MinorUnitDigits (no non-zero digit beyond)`

and §4.4 grades money off it: **I-1** (debits == credits) and **I-2** (splits sum to whole) are both
marked **"YES, gradeable today"**, compared as `int64` minor units, citing `A2-235`'s eight legs
(245,000,000 minor units each side) and `A2-150`'s six rows.

**I re-verified that the data carries money, so the predicates are not vacuous for the posting
seam.** `A2-235` holds exactly eight `"amount":` occurrences, every one a bare JSON number of form
`N.000000`: `1200000.000000` ×2, `200000.000000` ×2, `1000000.000000` ×2, `50000.000000` ×2
[VERIFIED by this task, regex over the raw bytes]. In minor units that is
120,000,000 + 20,000,000 + 100,000,000 + 5,000,000 = **245,000,000** per side — DEC-2's arithmetic
is correct. `A2-150`'s journal dump projects `amount` and `currency_code`, six rows, all `MNT`, all
`1200000.000000` [VERIFIED by this task].

**So exactly one of these is true, and DEC-2 asserts both:**

1. the contract carries no amount — in which case **G-07 and G-08 are vacuous** (P-35: true of
   everything, because there is no amount or currency to fail them) and §4.4's I-1/I-2 gradings are
   unreachable; or
2. the contract does carry an amount and a currency on the `ledger_rest_posting` seam — in which
   case **§2.2's and §3.2's flat sentences are false**, and §5's cell vocabulary is missing every
   money cell it needs.

**The root cause is identifiable and worth naming.** §2.2 derives B-5 from the signature of
`getLinkedGLAccountForLoanProduct`, which belongs to the `ledger_inprocess_resolver` seam — the one
seam §4.1 records as **"NO — does not exist"** and §4.2 G-01 explicitly refuses. The conclusion
"the contract carries no amount" is imported from a seam the contract does not admit, and applied
to a contract built on three seams that do, one of which is defined as *"observed through the
journal entries it writes"*.

**Not a MICRO-FIX.** Resolving it decides whether the contract has an amount field and a currency
field — a shape decision, and a graded-domain-member decision. The brief forbids both from a
micro-fix, and rightly.

---

## Non-blocking findings

### F-A — §9 item 10 is a read not taken, not a gap; and the answer is the opposite of the savings side

§9's preamble says *"Each is a gap, not a guess declined."* Item 10 is not a gap. It reads:
*"**Whether `ACCRUAL_UPFRONT` on the LOAN side writes mappings.** The savings switch reaches
`default: break`; the loan side was not read by this task and must not be assumed by symmetry."*

The loan side is one grep away, and it says:

```java
case ACCRUAL_UPFRONT:
    // Fall Through
case ACCRUAL_PERIODIC:
```
[VERIFIED by this task:
`fineract-provider/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/ProductToGLAccountMappingWritePlatformServiceImpl.java:149-151`]

On the **loan** side `ACCRUAL_UPFRONT` falls through and writes the **full** accrual mapping set.
On the **savings** side it writes nothing [VERIFIED by this task:
`SavingsProductToGLAccountMappingHelper.java:192-193`, `case ACCRUAL_UPFRONT: break;`].

DEC-2 was **right** to refuse the symmetry assumption — the two sides genuinely differ — and wrong
to file the question under gaps that could not be closed. It bears on §4.2 **G-03**, which admits
only `{CASH_BASED, ACCRUAL_PERIODIC}`: given the fall-through, a loan product at
`accountingRule = 4` writes rows identical to `ACCRUAL_PERIODIC`, so whether 4 belongs in the graded
domain is a question DEC-2 could have answered and did not.

**Secondary imprecision, inherited:** the savings switch has **no `default:` label at all**
[VERIFIED by this task: zero `default:` occurrences in that file]. It is an explicit
`case ACCRUAL_UPFRONT: break;`. "Reaches `default: break`" is carried in §4.2 G-03 and §6.4 marked
`[VERIFIED BY A2-2, NOT RE-OPENED HERE]`, so this is an inherited wording defect rather than one of
DEC-2's own `[VERIFIED]` claims — but a reader grepping for `default:` will not find it.

### F-B — §4.10's "refused with a named reason" is not what the code does

§4.10 declares `mapping.paymenttype.null` as *"ABSENT on every seam. Declared so a vector claiming
it is refused **with a named reason** rather than as an unknown capability."*

`Assess` interpolates `capDef.Evidence` — the named reason — only on the `blind` and `ungraded`
paths [VERIFIED: `capability.go:322-330`]. A capability that is **declared** but absent from every
seam's status map lands in the `unknown` bucket with the generic message *"seam %q has no recorded
status for capability %q (default-deny: an unaudited input is assumed invisible, never assumed
wired)"* — **the evidence string is not surfaced** [VERIFIED: `capability.go:314-320`].

To get the named reason, the row must be listed on a seam with status `blind`. DEC-2 does exactly
that for `mapping.charge.precedence` (`ledger_inprocess_resolver: blind`) and should do the same
here, or drop the claim. Refusal happens either way — only the diagnostic differs.

### F-C — §4.3 / §9 item 3's forward reference to T186 is stale, but the substance is consistent

§4.3 carries `[UNVERIFIED — T186 is settling the general rule.]` and §9 item 3 says T186 *"is
settling it in parallel"*. **T186 merged this fire** at `c17e9fa`, before A2-13's own merge; A2-13's
branch forked before it landed [VERIFIED: `git merge-base --is-ancestor c17e9fa e18fe5b` → false].

I checked §4.3 against T186's ruling and found **no contradiction**:
- T186 **(a)** oracle-facing capture wire admits major-unit decimal, bound by byte-fidelity ↔ §4.3
  *"Read the literal characters, never a decoded number … converted from the literal token by exact
  integer/string arithmetic."* Consistent.
- T186 **(b)** the Go module's own surface refuses float absolutely ↔ §4.3 *"On the Go side of the
  boundary, absolutely: integer minor units, `int64`, everywhere. No float, no decimal-float, no
  `big.Float`."* Consistent.
- T186 **(c)** the stored vector must be integer minor units ↔ §4.3 places the conversion at *"the
  capture-transcription step for a vector"*. Consistent by implication, but **§4.3 never states
  (c) as a rule**. Now that T186 has ruled, it should.

DEC-2's own escape clause (*"If T186's ruling contradicts anything in this subsection, T186 governs
and this subsection is the amendment"*) holds. This is stale text, not a defect.

### F-D — `capabilities.json` is named and versioned for one context; DEC-2 half-notices

`CapabilityRegistrySchema = "gerege.loanschedule.capabilities/v1"` is a hard constant and the loader
refuses any other value [VERIFIED: `capability.go:12` and `:119-120`]. The file also carries a
singular `dec1_revision: 12` [VERIFIED: `capabilities.json:3`]. Appending `ledger` rows and seams
does not break the loader — the schema string is unchanged and the arrays are open — so §4.10 is
*workable*. But DEC-2 §4.10 notices the file is shared (it declines to add a fifth status on exactly
that ground) and then does not address the schema id or `dec1_revision` at all. A2-13's F-2(c)
raises the same question for `PIN.json`. Worth a decision before `A2-15` improvises one.

---

## What I checked and found clean — stated so silence is distinguishable from not looking

**The verification discipline in this document is the best I have reviewed in this program.** I
spot-checked far more than the four markers the brief required, in **both** directions, and **every
`[VERIFIED]` claim I opened traced to real source at the exact cited line**. Not one was
overstated, mis-cited or fabricated. Specifically:

| DEC-2 claim | verified at |
|---|---|
| Seam signature: three scalars, one `GLAccount`, no amount | `AccountingProcessorHelper.java:1185` — exact |
| Miss renders through `AccrualAccountsForLoan` unconditionally | `:1210` — exact |
| `glAccount = accountMapping.getGlAccount();` / `return glAccount;`, no classification/usage/disabled read | `:1213`, `:1215` — exact |
| STEP 2 has **no** `paymentTypeId != null` conjunct, unlike WCL | `:1199` vs `:1015` — exact, both opened |
| WCL miss renders through `CashAccountsForLoan` | `:1024-1027`, `:1026` — exact |
| Shares path: bare `return accountMapping.getGlAccount();`, no null check | `:1337` — exact |
| `isOrganizationAccount` = `FinancialActivity.fromInt(id) != null` | `:1340-1342` — exact |
| `CashAccountsForLoan` has 23 members | `AccountingConstants.java:37-62` — counted, 23 |
| `AccrualAccountsForLoan` has 25 members | `:95-122` — counted, 25 |
| Collide at 22 / 24 / 25 with the stated names | `CLASSIFICATION_INCOME`/`INCOME_FROM_CAPITALIZATION`, `INCOME_FROM_DISCOUNT_FEE`/`BUY_DOWN_EXPENSE`, `FEES_RECEIVABLE`/`INCOME_FROM_BUY_DOWN` — all three exact |
| cash has 26, accrual lacks it; accrual has 7/8/9, cash lacks them | exact |
| `CHARGE_OFF_EXPENSE` = 16, `GOODWILL_CREDIT` = 13, identical names in both enums | `:48`, `:51`, `:109`, `:112` — exact |
| Placeholder enums top out at 26, disjoint from `{100…300}` | exact |
| Seven financial activities, values `{100,101,102,103,200,201,300}` | `:439-445` — exactly seven |
| `ASSET_TRANSFER` requires `GLAccountType.ASSET` | `:439` — exact |
| Core-row JPQL names **six** NULL discriminators | `ProductToGLAccountMappingRepository.java:38` — counted, six |
| `acc_gl_journal_entry.amount` is `scale = 6, precision = 19` | `JournalEntry.java:91` — exact |
| `reversed` column | `JournalEntry.java:79` — exact |
| `JournalEntry.java` has **zero** occurrences of `classification` | `grep -ic` → 0 — exact |
| GL-account update guard keyed on USAGE + `isHeaderAccount()`, TYPE unmentioned; delete has its own check | `GLAccountWritePlatformServiceJpaRepositoryImpl.java:153-158`, `:201-203` — exact |
| `A2-211`: 9 `accountingMappings`, every value key set exactly `{glCode, id, name}` | decoded — exact |
| `A2-211`: literal `null` occurs **0** times; `paymentChannelToFundSourceMappings` **absent** | exact |
| `A2-211`: 7,489 bytes; `accountingRule` = `{id:2, code:accountingRuleType.cash, value:CASH BASED}` | exact |
| `A2-150`: GL 2 `10100 Fund Source`, `classification_enum = 4`, usage 1 | exact |
| `A2-150`: financial activity 100 → GL 2 (INCOME) while `ASSET_TRANSFER` requires ASSET | exact |
| `A2-150`: journal entry id 6 debits GL 1 `Assets`, `account_usage = 2` (HEADER posting target) | exact |
| `A2-150`: six journal rows, all `MNT`, all `1200000.000000` | exact |
| `A2-235`: eight `"amount":`, every one a bare `N.000000` number | exact |
| Capture corpus: 147 JSON of 444 files in `out/`, 89 in `req/` | counted — exact |
| 43 promoted parity vectors + 4 contract-refusal, all `loanschedule` | 47 files; run reports PASS 43 / 4 — exact |
| 18 ledger Go files, all inspected by the widened guards | counted — exact; my own run printed `covered: nexus/internal/apps/ledger` |
| `conformance.sh:401` `NEXUS_DIR="$REPO_ROOT/nexus"` | exact |
| `conformance.sh` never invokes `go test` (both occurrences are comments) | `:679`, `:682` — exact |
| `grade.go` three fatals | `:334-342`, `:407-415`, `:418-425` — exact |
| Go port: `FineractFromIntQuirk`, `PostedAccountSnapshot`, `ErrMappingNilDereference` (500) | `producttype.go:162`, `glaccount.go:324`, `errors.go:93-95` — exact |
| A2-8's F-1 is stale: T166 widened the guards | confirmed by re-reading the script and by my own run |

**Also clean:**

- **Money non-negotiables.** Every occurrence of "float" in DEC-2 is a prohibition or a hazard
  warning; the document admits a float **nowhere** Gerege owns the number. No `mysql`, `mariadb`,
  `ojdbc`, `oracle.jdbc`, Oracle dialect or port 1521 anywhere in the text. §4.3's three normative
  consequences (preserve the token; refuse residue rather than truncate or round; convert per field
  *semantics* not field *name*) are correct and the third is a genuinely good catch.
- **G-9 applied, not re-litigated.** §4.5 restates the closed decision as a contract boundary
  (model in, chart out), adds two facts G-9 did not reach, and does not reopen it. `gates.md`
  confirms G-9 **CLOSED — DECIDED**.
- **G-10 recorded, not decided.** `gates.md` confirms G-10 **OPEN — driver recommends (c)**. §4.6
  states the hazard in eight numbered facts and derives **A-1…A-4**, which are admissibility rules
  that hold under *either* disposition. A-4 quotes recommendation (c) as a recommendation and says
  in terms *"and **does not decide the gate**"*. **No gate was crossed.**
- **Default-deny is genuinely inherited.** §4.10 quotes `capabilities.json`'s sentence verbatim and
  the code enforces it in four layers — unknown seam, undeclared capability, no seam status,
  status ≠ `exercised` — plus a fifth for `exercised` but outside the graded domain
  [VERIFIED: `capability.go:290-343`]. DEC-2 admits by omission **nowhere** I could find: every
  `in_graded_domain: false` row in §4.10 states its reason, and §4.2's complement column gives a
  refusal ground for all eleven predicates.
- **§4.1's cross-dump rule is a real improvement.** Forbidding a vector from joining columns across
  two psql snapshots, and requiring the dump's `captured-at`, is P-32 made mechanical, and it is
  grounded in an observed contradiction (`A2-072` vs `A2-150` on GL 2) that already cost A2-8 a
  test.
- **§4.7's creation-set ⊄ posting-set finding** is measured rather than reasoned, and §4.9's
  two-kinds-of-refusal distinction is the sharpest thing in the document. Both should survive
  redrafting unchanged.
- **§9 item 2 is genuinely unverifiable.** `findByProductIdAndProductTypeAndFinancialAccountTypeAndPaymentTypeId`
  is a **derived** query with no `@Query` annotation [VERIFIED:
  `ProductToGLAccountMappingRepository.java:30-31`], so the null-binding semantics really are Spring
  Data framework behaviour and not readable from the pinned checkout. Correctly marked, correctly
  refused via `G-06`, and the discriminating capture it names is the right one.

---

## The honest answer to "what grades the ledger's money behaviour today?"

**Nothing does, in any respect.**

- **No vectors.** `.softhouse/vectors/` has `loanschedule/` and `_selftest/` only. Zero `ledger`.
- **No schema to write one in** — R-1.
- **No source guard for I-3 or I-4.** DEC-2 §4.4 states, correctly and as a *requirement*, that
  *"I-3 and I-4 must be enforced by a harness-level source guard, not by a vector"*. It does not
  claim one exists, and **none does**: `run_guards` invokes exactly five guards —
  `guard_no_float_in_vectors`, `guard_no_float_in_harness`, `guard_gofmt`,
  `guard_no_float_in_capture_requests`, `guard_no_narrow_catch_in_capture_rigs`
  [VERIFIED: `.softhouse/conformance.sh:804-811`]. All five are about float, formatting and
  exception scope. **Nothing checks for a balance write path or an `UPDATE`/`DELETE` against
  `acc_gl_journal_entry`.**

DEC-2 §8's "If ratified, these remain true and must not be misread" list should say this in one
sentence a reader cannot miss. It currently says the guards *do* cover the ledger tree — true, but
only for float and gofmt, which is not what I-3 and I-4 are about.

---

## Is this the right seam?

**Yes for the anchor; no for the reasoning imported into it.**

DEC-2 does **not** in fact freeze the contract at `getLinkedGLAccountForLoanProduct`. §4.1 records
`ledger_inprocess_resolver` as **not existing** and §4.2 `G-01` admits only `ledger_rest_admin`,
`ledger_rest_posting` and `ledger_db_readback`. The contract is anchored at the **observable
boundary**, and the in-process method is used as the source-level *explanation* of resolution
semantics. That is the right call — it is the only anchor the existing corpus can support, and it
avoids freezing a rig nobody has built.

**What else it could have been anchored to, and what each would have bought:**

- **`createJournalEntriesForLoan` / the `AccountingProcessorForLoan` family** — where account
  selection and amount finally meet. Would have made I-1…I-5 gradeable in process. Rejected
  correctly: it pulls in the whole loan-transaction model, which is A1's scope, and would have
  broken the one-bounded-context-per-run rule.
- **`JournalEntryWritePlatformService` / the manual journal-entry command path** — **the most
  interesting road not taken.** It is money-producing, double-entry, REST-observable, carries a
  command envelope where `Idempotency-Key` is meaningful, and it operates on A2's own three tables.
  Anchoring a second entry point there would have let DEC-2 grade I-1, I-2, I-4 and I-5 directly
  instead of deferring all of them. §7 pushes journal-entry writing to A1 — defensible, and it is
  *the* reason this contract ends up with no money graded by anything. DEC-2 should say that is a
  consequence of the scope split, not a property of the ledger.
- **The REST journal-entry read endpoint** — already observable; `A2-150` reads the table directly.
  Would have made I-1/I-2 expressible without touching A1.

**The defect is not the seam choice.** It is that §2.2/§3.2 reason about money from
`ledger_inprocess_resolver` — a seam §4.2 refuses — and then state the conclusion as a property of
the whole contract. That is R-3.

---

## Recommendation to the driver

**REJECT and return for revision 2.** The document is close, and most of it should survive
untouched. Four things must change before it is ratifiable:

1. **Decide and state whether the contract carries an amount and a currency** (R-3). Either strike
   `G-07`/`G-08` and the I-1/I-2 "gradeable today" claims, or strike §3.2's *"the contract carries
   no amount"* and §2.2's answer-type enumeration and add money cells to §5's vocabulary. Scope B-5
   explicitly to `ledger_inprocess_resolver`.
2. **Rewrite §5's "needs no new machinery"** (R-1). Name what a `ledger` vector actually requires:
   a third `Expect.Kind`, a representation for an oracle-faithful refusal that is not a contract
   sentinel, an extension to `StructuralCellFields()`, and a `ParseDivergentCell` vocabulary that
   admits non-`period[n]` cells. State it as a **precondition on `A2-15`**, not a follow-up.
3. **Correct the empty-directory claim** (R-2) and say what enforces Disposition 3 in the
   **unfiltered** run — on the evidence, only the `capabilities.json` rows do.
4. **Close §9 item 10** (F-A) — it is a one-grep read, and the answer changes what `G-03` should
   admit.

**No gate is raised by this review**, and none is crossed: G-9 was applied, G-10 was left open and
undecided, DEC-1 and `contract.go` were not touched by A2-13 and not touched by me.
