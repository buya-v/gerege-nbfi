# A2-9 — independent review of A2-8 (`softhouse/A2-8-ledger-port`, `a1d4a52`)

Reviewer: A2-9. Branch `softhouse/A2-9-review-a2-8`, forked from `main` at `b801707`.
Pinned reference oracle (Fineract) checkout `/Users/buv/fineract` @ `426a23544` — confirmed by
my own read of the files cited below.
Reference oracle instance **UP** (`conformance.sh` printed
`reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`).
PostgreSQL reachable: `docker exec fineract-db-1` (`postgres:18.3`, port 5432) — used to
settle one claim (F-B).

## VERDICT: **MICRO-FIX**

One code change required (**F-A**, 4 lines, diagnostic-only, no number, no money logic, never
on the wire), plus four written corrections (**F-B**, **F-C**, **F-D**, **F-G**) that are
comment/handoff text, not behaviour. Everything money-bearing in this port is **correct**: I
re-derived every monetary computation it touches in integer minor units from the capture bytes
and got A2-8's numbers exactly.

**Not rejected, and I want to be explicit about why**, because the brief warned me the safety
net is absent: I did the no-float grep myself over all 18 files, I re-derived all four traps
from the pinned source myself, I drove five guards RED myself, and I perturbed the port in six
places to prove the tests are not vacuous. The port survived all of it.

---

## 0. Scope, build, harness — measured, not accepted

| check | result |
|---|---|
| `git diff main...softhouse/A2-8-ledger-port --stat` (**three dots**, P-41) | **19 files, 6,065 insertions**: 18 under `nexus/internal/apps/ledger/` + the handoff. Nothing else. Scope clean. |
| `contract.go` byte-unchanged | yes — not in the diff at all |
| `go build ./...` from `nexus/` (module root, not repo root; not piped into `head`) | exit 0 |
| `go vet ./...` | exit 0 |
| `go test ./...` | `ledger ok · loanschedule ok · conformance ok` |
| `go test ./internal/apps/ledger/ -v` | **55 PASS, 0 FAIL, 0 SKIP** — I counted the `--- PASS` lines |
| `gofmt -l nexus/` | exactly `nexus/internal/apps/loanschedule/contract/contract.go` (G-3, expected). `gofmt -w` never run on it by me. |
| `bash .softhouse/conformance.sh` on A2-8's tree | **exit 0**, probe line PRESENT reading `up`, **43 parity PASS / 0 FAIL, 5664 cells graded**, 0 invariant violations, 0 NOT RUN |
| prohibited drivers/vendors/strings over the package (`ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql`, `mariadb`, `go-sql-driver`, `first_name`, `last_name`, Stripe/Plaid/Lithic/Persona, `insured`/`guaranteed`/`protected`) | **zero hits**. The package imports **stdlib only** — no database driver of any kind. |

**The harness figure is identical to `main`'s baseline, and I confirmed why, myself:**
`.softhouse/conformance.sh:573` walks `find "$NEXUS_DIR/internal/apps/loanschedule"`, and
`nexus/internal/apps/loanschedule/conformance/nofloat.go:62` sets
`LoanScheduleTreeRel = nexus/internal/apps/loanschedule`. Both roots are loanschedule-only.
**43/5664 says nothing about this package.** A2-8 says so plainly and raised it as its own F-1;
that is the honest reading and I confirm it independently.

### The no-float grep I did not delegate

Over all 18 `.go` files in `nexus/internal/apps/ledger/`:

- `grep -nE 'float|Float'` → the only hits outside comments are **inside
  `slots_test.go`'s own forbidden-token table and its red-drive samples** (lines 331-333,
  360-362). Zero in any source file.
- `grep -nE '%[-+ #0-9.]*[eEfFgG]'` (float format verbs) → **zero**.
- float literals (`digit.digit`) in non-test source → **zero** (three hits are the strings
  `12.1.3 / 12.1.4` and `§2.6` inside comments).
- every JSON decoder in the tests calls `UseNumber()`; every money value is decoded as
  `json.Number` and converted through `MinorUnitsFromDecimalText` on the literal characters.
  I checked every `json.` site (`grep -n 'json\.'`): **there is no `interface{}` money decode.**

**[VERIFIED by A2-9: there is no floating-point value on any path in this package.]**

---

## 1. THE FOUR TRAPS — re-derived from pinned source by me, not read from A2-8

### Trap 1 — `PortfolioProductType.fromInt` permutes 3/4/5 · CONFIRMED

`PortfolioProductType.java` lines 25-30 declare
`LOAN(1) SAVING(2) CLIENT(5) PROVISIONING(3) SHARES(4) WORKING_CAPITAL_LOAN(6)`;
lines 46-60 switch `case 3 -> CLIENT`, `case 4 -> PROVISIONING`, `case 5 -> SHARES`.
3-cycle 3→5→4→3, `{1,2,6}` fixed. **[VERIFIED: my own `sed` of the pinned file.]**
(A2-8 cites `:26-31` / `:51-59`; actual `:25-30` / `:46-60`. Off by one, harmless.)

**Is the inverse genuinely derived?** Yes. `productTypeFromStored` is an empty map populated in
`init()` by iterating `productTypeStoredValue` — the *encode* table — and inverting it. There is
no second hand-written decode table. `productTypeDeclarationOrder` is a separate array, but it
encodes *declaration order*, which is different information and is used **only** by
`FineractFromIntQuirk`, correctly named so it cannot be mistaken for the inverse.

**I DROVE THE BIJECTION PANIC RED (P-22).** Patched `ProductClient: 5` → `3` in a scratch copy
so CLIENT collides with PROVISIONING, then ran one trivial test:

```
panic: ledger: product_type encode table is not injective: CLIENT and PROVISIONING both store as 3
    .../producttype.go:98
FAIL  github.com/gerege/nexus/internal/apps/ledger  0.474s
```

Restored → green. **The guard fires. It is not a guard nobody has triggered.**

### Trap 2 — the two loan enums collide, and neither key is safe · CONFIRMED

`AccountingConstants.java:37` opens `CashAccountsForLoan` (23 members, codes
`{1..6, 10..26}`, last is `PENALTIES_RECEIVABLE(26)` at `:61`); `:95` opens
`AccrualAccountsForLoan` (25 members, codes `{1..25}`, last is `INCOME_FROM_BUY_DOWN(25)` at
`:121`). **A2-8's line citations `:37-62` and `:95-122` are exact.**

My own set arithmetic: shared codes = `{1..6,10..25}` = **22**; they disagree at
**22** (`CLASSIFICATION_INCOME` / `INCOME_FROM_CAPITALIZATION`),
**24** (`INCOME_FROM_DISCOUNT_FEE` — INCOME role / `BUY_DOWN_EXPENSE` — **EXPENSE** role),
**25** (`FEES_RECEIVABLE` / `INCOME_FROM_BUY_DOWN`) → **3 differ, 19 agree.**
Name is not a function either: `FEES_RECEIVABLE` = 25 cash / **8** accrual;
`PENALTIES_RECEIVABLE` = 26 cash / **9** accrual. **All of A2-8's trap-2 numbers reproduce
exactly.**

**Is the scan test-only? YES — and A2-8 says so at the site (`slots_test.go:206-210`) and in
its handoff.** `conformance.sh` never runs `go test`, so per P-45 this is a package-local
regression check, not a harness guard. That is a *disclosed* limitation, not a concealed one,
and the driver has already raised T166. I did not treat it as a rejection because A2-8 neither
claimed nor implied harness coverage.

**I ATTEMPTED THE CROSS-MAP MYSELF**, in a scratch copy of the package, and measured exactly
what the scan does and does not catch:

| probe written into the package | compiles? | scan fires? |
|---|---|---|
| `AccrualLoanSlot(CashLoanFeesReceivable)` | yes | **YES** — `--- FAIL: TestNoCrossFamilySlotConversion` |
| `AccrualLoanSlot(CashLoanFeesReceivable.Code())` | yes | **YES** |
| `var t = CashLoanFeesReceivable; AccrualLoanSlot(t)` | yes | **NO — evades** |
| `var c int32 = 25; AccrualLoanSlot(c)` | yes | **NO — evades** |
| `float64` / cross-map in `ledger/sub/*.go` | yes | **NO — evades** (see F-E) |

So the guard is real and red-drivable at the literal case, and porous at two indirections.
A2-8's stated limit ("Nothing in the language can stop that") is honest; the *enumeration* of
evasions was missing and is recorded here as **F-F**.

Two corruptions I attempted were caught by the **compiler**, which is a stronger guard than the
scan: setting `AccrualLoanFeesReceivable = 25` produces
`duplicate key 25 in map literal` at `apishape.go:184` and `slots.go:243`; collapsing
`EntryDebit` onto `EntryCredit` produces `duplicate case` at `money.go:167,198`.

### Trap 3 — `acc_gl_journal_entry` carries no classification · CONFIRMED

I read `JournalEntry.java` myself. It declares exactly **21** mapped columns
(`grep -c 'name = '` over the entity = 21), and they are precisely A2-8's list. **There is no
classification column.** `amount` is
`@Column(name = "amount", scale = 6, precision = 19, nullable = false)` at `:91`, and the
live database agrees: `A2-150-db-final-state.txt` reports
`acc_gl_journal_entry.amount → numeric, precision 19, scale 6`.
`JournalEntryType` is `CREDIT(1)/DEBIT(2)` — a different axis from ASSET..EXPENSE.

The guard asymmetry is real and I re-read it: `GLAccountWritePlatformServiceJpaRepositoryImpl`
guards `disabled` at **:119-122** (call to `validateForAttachedProduct`), guards
USAGE→header at **:153-159** with a journal-entries-exist query, and applies the *identical*
query on delete at **:200-205** — **and never applies it to classification.** So classification
is mutable under posted history, by omission rather than by design.

**Does `PostedAccountSnapshot` actually let A1 carry classification on the entry?** Yes:
it is `{AccountID, GLCode, Name, Classification, Usage}`, `GLAccount.Snapshot()` builds it, and
`PostingLeg.Account` is a `PostedAccountSnapshot` — **not** a `*GLAccount`. So the invariant
predicates operate on the snapshot, not on a live account lookup.

**Does anything in the package resolve classification through the account at read time?** No.
The only account lookups are `resolveOrganisationAccount` and `accountOfRow`, both of which run
at *resolution* time (choosing which account a posting hits — which the oracle also does live,
and which never reads classification). There is no entry read-back path in this package at all;
that is A1's. **Trap 3 is correctly handled.**

G-10 is observed, not merely derived, and I verified both halves myself:
`A2-111-update-retype-mapped` = **HTTP 200**, body `{"resourceId":2,"changes":{"type":4}}`;
`A2-209b-read-gl2-retyped-fundsrc` reads GL 2 back as `"type":{"id":4,...,"value":"INCOME"}`.

### Trap 4 — `DECIMAL(19,6)` vs MNT minor unit 2 · A2-8's ANSWER IS CORRECT AND ITS MEASUREMENT REPRODUCES

**The rule A2-8 applies is NONE — it refuses — and it marks the truncation rule `[UNVERIFIED]`.
I agree this is the right shape of answer, and I verified all three legs.**

**(1) The measurement.** I enumerated every JSON file under
`.softhouse/capture/tierA-a2/out/` myself with `json.load(parse_float=decimal.Decimal)` — **no
float in my analysis either** — and walked every `amount` key at any depth:

```
json files parsed 147   unparseable 0
total `amount` fields              52
sub-minor `amount` occurrences      7   (all in A2-209c-loanproducts-template.json)
```

Every one of the 7 is a `chargeOptions[i].amount` of `1.234500`, and every one carries
`chargeCalculationType` ∈ {`% Amount`, `% Loan Amount + Interest`, `% Disbursement Amount`}.
**A2-8's percentage claim is exactly right — they are percentages, not money**, and
misclassifying them would indeed have inverted the conclusion. Every other money value in the
corpus is exact at two decimals. The psql dumps carry exactly one decimal token with >2 places
(`1200000.000000`), and the journal-entry table has **6 rows** — A2-8's "six" is correct.

**(2) The refusal fires — I drove it red with a 6-decimal residue.**

```
"1.234500" REFUSED: ledger: monetary text "1.234500" carries sub-minor-unit residue at scale 2
  (digit "4" beyond 2 decimal places). This port applies NO truncation rule because no captured
  vector establishes one; refusing rather than silently inventing an amount
"0.001"    REFUSED
"0.000001" REFUSED
```

And I drove the *inverse* red: patching the residue loop to `&& false` (i.e. truncate silently)
turns **two** tests red — `TestMinorUnitsRefusesSubMinorResidue` and
`TestSubMinorResidueIsUnobservedNotImpossible`. The refusal is load-bearing.

**(3) The conversion arithmetic, re-derived by me in integer minor units:**

| oracle text | A2-9's hand derivation | port |
|---|---|---|
| `1200000.000000` | 120 000 000 | 120000000 ✓ |
| `200000.000000` | 20 000 000 | 20000000 ✓ |
| `1000000.000000` | 100 000 000 | 100000000 ✓ |
| `50000.000000` | 5 000 000 | 5000000 ✓ |
| `2450000.000000` | 245 000 000 | 245000000 ✓ |
| `-1200000.000000` | −120 000 000 | -120000000 ✓ |
| `100.5` | 10 050 (pad) | 10050 ✓ |
| `100` | 10 000 | 10000 ✓ |

I also checked the overflow guard `next/10 != acc`: for `acc ≥ 0` a wrapped `acc*10+d` is
strictly less than the true product, so integer division cannot round-trip. It is sound.
(`-9223372036854775808` is refused as an overflow of its positive magnitude; that is a
one-value conservatism, not a defect.)

---

## 2. THE MONEY RE-DERIVATION (the reason this role exists)

I did **not** read A2-8's tables. I opened `A2-235-je-after-recovery.json` and summed it myself
with `decimal.Decimal`:

```
id 11  acct  4 (10201 Loan Portfolio)         DEBIT   1200000.000000   L11 2026-02-01
id 12  acct 16 (10300 Fund Source Alternate)  CREDIT  1200000.000000   L11
id 14  acct  4                                CREDIT   200000.000000   L14 2026-03-01
id 15  acct 16                                DEBIT    200000.000000   L14
id 16  acct 13 (50100 Losses Written Off)     DEBIT   1000000.000000   L15 2026-04-01
id 17  acct  4                                CREDIT  1000000.000000   L15
id 18  acct 16                                DEBIT     50000.000000   L16 2026-05-01
id 19  acct 11 (40400 Recoveries)             CREDIT    50000.000000   L16
--------------------------------------------------------------------
DEBIT total 2450000.000000   CREDIT total 2450000.000000
```

**× 100 = 245,000,000 minor units each side. A2-8's figure is exact, and its insistence on
stating the UNIT is right** — A2-7 wrote `2450000.000000` at `A2-7.md:346`, which is the same
money in **major** units, and a unit slip in a trap-4 slice is indistinguishable from a
rounding defect.

**Splits sum to whole**, re-derived: GL account 4 takes a debit of `1,200,000.00` and is
relieved by `200,000.00 + 1,000,000.00`. In minor units
**120,000,000 = 20,000,000 + 100,000,000.** Exact. I fed my own hand-built leg list into
`DoubleEntryBalances` and `SplitsSumToWhole` and both agreed; I then drove `SplitsSumToWhole`
red with a one-minor-unit shortfall and it refused.

`DoubleEntryBalances` also refuses a **negative** leg with the right reasoning ("a negative
debit is a credit wearing the wrong label") — this is the sister project's inverted-hold defect
class, and refusing rather than netting is correct. Nothing in this package writes, stores or
caches a balance; `m_trial_balance` is deliberately not ported, and I confirmed
`UpdateTrialBalanceDetailsTasklet` does write a stored `closing_balance`, so declining it is
right under "balances are derived, never written".

---

## 3. THE FIVE THINGS I WAS ASKED TO ATTACK

### (a) The inherited fabrication — is the correction complete? **YES, and I verified it against the raw bytes.**

```
A2-211-read-product-nine-mandatory.json      7489 bytes
  occurrences of "null"                          0
  paymentChannelToFundSourceMappings             0
  feeToIncomeAccountMappings                     0
  penaltyToIncomeAccountMappings                 0
positive control A2-212 (has one override)       1 occurrence of the key, 0 of "null"
negative control A2-213                          0 occurrences of the key, 0 of "null"
```

A2-8's rule — *unset ⇒ ABSENT, scalar and collection alike, nothing is ever `null`* — is
correct, and its positive controls are real.

**The `null`-marshalling sweep the brief asked for.** Over the whole package:
- struct tags with `json:"…"` in **source**: exactly six, on two structs —
  `AccountReadObject{id,name,glCode}` and `EnumOptionData{id,code,value}`. **No pointer fields,
  no slices, no maps, no `omitempty` anywhere.**
- pointer fields exist only on internal row/model types (`MappingRow`, `GLAccount.ParentID`,
  `GLAccount.TagID`), none of which carry a JSON tag or are serialised.
- there is no `json.Marshal` call in the package at all.

**So nothing in this package can marshal a key to `null` where the oracle omits it.** The
correction is complete at the code level as well as the documentation level.

### (b) The declined half of the driver's instruction — **A2-8 WAS RIGHT. I adjudicate in its favour.**

Fineract is the oracle. Parity with an oracle bug beats a local improvement, and the driver's
instruction as written would have broken message parity at exactly three codes.

**(i) Is the rendered string byte-identical to the oracle's?** Yes.
`ProductToGLAccountMappingNotFoundException` builds
`"Mapping for product of type " + type + " with Id " + productId + " does not exist for an account of type " + accountType`;
the port's format string is `"Mapping for product of type %s with Id %d does not exist for an account of type %s"` —
character-for-character. And the oracle renders `accountType` through
`AccrualAccountsForLoan.fromInt(...)` **always** on the loan path
(`AccountingProcessorHelper.java:1209-1210`, inside `if (accountMapping == null)` at `:1208`),
and through `CashAccountsForLoan.fromInt(...)` always on the working-capital path (`:1025-1026`,
guard at `:1024`). **I read both sites myself.** The port reproduces this, so the three graded
messages match. Perturbing the wording to `does not exists` turns
`TestMissingMappingRefusalsMatchTheOracleMessages` red — the grading is real, against the
committed capture bytes.

The port is byte-faithful elsewhere too, including where the oracle is ugly: it reproduces the
oracle's **missing space** in `"with Id %dmaps to the account"` (`apishape.go:309`), which is
exactly what `A2-214` emits.

**(ii) Does the fallback fire only where the oracle would NPE?** Yes — I enumerated it:

```
code  7: LOAN path -> INTEREST RECEIVABLE     WCL path -> <oracle NPEs>
code  8: LOAN path -> FEES RECEIVABLE         WCL path -> <oracle NPEs>
code  9: LOAN path -> PENALTIES RECEIVABLE    WCL path -> <oracle NPEs>
code 26: LOAN path -> <oracle NPEs>           WCL path -> PENALTIES RECEIVABLE
```

Four (code, path) pairs, all four exactly where the rendering enum has no member and
`.toString()` would be called on a null. **Nowhere else.** The divergence is confined to the
case where the oracle cannot produce a message at all.

**(iii) Is `ApplicableSlotName` never serialised?** Correct — `LedgerError` has **no** JSON
tags, nothing marshals it, and `grep -n ApplicableSlotName *.go` returns four hits: two doc
lines, one assignment, and zero reads. It is never on the wire.

**But that last measurement is also how I found F-A: the field is inert. See below.**

### (c) How much rests on the G-10 chart state, and would anything change under a clean chart?

I re-measured G-10 myself rather than taking A2-8's count. From
`A2-072-db-product-mapping-rows.txt`, the products carrying GL account **2** at
`financial_account_type = 1`: **22, 23, 24, 27, 28** — five products — and the row count is
**six**, because product 27 carries GL 2 twice (core row, and the `payment_type = 1` duplicate).
**A2-8's "five products and six rows" is exactly right.** GL 2 reads
`classification_enum = 1` (ASSET) in `A2-072` and `classification_enum = 4` (INCOME) in
`A2-150` — the two committed dumps genuinely disagree, and the oracle now **refuses** to
re-create the state (`A2-214` = HTTP 403, "…maps to the account Fund Source of type INCOME, the
expected account type was one among accountType.asset or accountType.liability").

**My judgement, which differs from A2-8's self-assessment in one direction:**

- **Resolution gradings are IMMUNE to G-10.** I read all four oracle resolvers end to end:
  `getLinkedGLAccountForLoanProduct`, `…WorkingCapitalLoanProduct`, `…SavingsProduct`,
  `…ShareProduct` all end in `accountMapping.getGlAccount()` with **no reference to the
  account's classification, usage or disabled flag**. Resolution answers "which account id",
  and GL 2's id is 2 under a clean chart too. **No resolution conclusion in this slice changes
  under a clean chart.** A2-8's item 13 ("most of my gradings are taken from that chart state")
  is true as a statement about the *fixture* but overstates the *exposure*.
- **What DOES rest on G-10** is the write-side type-check family: `A2-214`, `A2-prod-063`, and
  the financial-activity create replay. Under a clean chart `A2-214` would be a **200**, not a
  403. Those gradings are self-consistent — each is graded against a capture that recorded the
  retyped state — but they are **not reproducible from a clean chart**, and a re-capture at the
  ratified `(19, HALF_UP)` will need new expected values for them. That should be written into
  the G-10 gate, and it is the one thing I would carry forward.
- A2-8 hit this exactly once, in `TestActivityCreateResponsesMatch`, and handled it correctly:
  it excluded the capture with the reason recorded **at the site** (a P-32 temporal mismatch
  between two committed captures of the same tenant) and asserted the phenomenon separately in
  `TestTheTenantsAssetTransferAccountIsNoLongerAnAsset`. That is the right move, not a
  weakening.

**Product 27's duplicate-row refusal — verified against the capture, and I nearly filed a
finding before the evidence corrected me.** `A2-150` reports
`(27, product_type 1, financial_account_type 1, payment_type 1) → n = 2, gl_account_ids {16,2}`;
`A2-072` shows the three rows (core GL 2; `payment_type 1` GL 16; `payment_type 1` GL 2).
`A2-086-disburse-loan3-dupchannel` = **HTTP 403**,
`error.msg.data.integrity.issue`, `"More than one result was returned from Query.getSingleResult()"`.

My initial objection was that `req/disburse-086-nopaymenttype.json` sends **no** `paymentTypeId`,
under which neither reading of the null-payment-type question yields two rows. **The `.http`
record settles it**: `A2-086-disburse-loan3-dupchannel.http` says
`body-file: req/disburse-084-paymenttype1.json` — the disbursement carried `paymentTypeId: 1`,
so the payment-type query matched both duplicate rows and `getSingleResult()` refused.
A2-8's `TestDuplicateMappingRowsRefuse` passes `paymentType = 1`. **The model is right.**
(The unused `disburse-086-nopaymenttype.json` is a rig-hygiene trap — see F-H.)

A2-8's supporting claim that the JPA `@UniqueConstraint(name = "financial_action")` is **not in
the DDL** also reproduces exactly: it is declared at
`ProductToGLAccountMapping.java:42-43`, and `grep -rn financial_action` over
`fineract-provider/src/main/resources/db/` returns **0**; the only occurrence anywhere in the
checkout is the annotation itself. Duplicates are physically possible.

### (d) Are the tests non-vacuous? **YES — I perturbed the port in six places.**

A test that asserts against bytes it also generated proves nothing, so I broke the *port* and
watched which tests noticed. All perturbations applied to a scratch copy and reverted.

| perturbation of the port | caught by |
|---|---|
| read key `fundSourceAccount` → `WRONGKEY` | `TestResolutionReproducesTheCapturedProductReads`, `TestWriteAndReadNamesDifferForEverySlot` |
| refusal wording `does not exist` → `does not exists` | `TestMissingMappingRefusalsMatchTheOracleMessages` |
| STEP 2 disabled (payment-channel override never applied) | `TestPaymentChannelOverride`, `TestResolutionAtPostingTimeMatchesTheJournalEntries` |
| `AccrualLoanFeesReceivable` 8 → 25 (a hand cross-map) | **compiler**: `duplicate key 25 in map literal` ×2 |
| trap-4 refusal → silent truncation | `TestMinorUnitsRefusesSubMinorResidue`, `TestSubMinorResidueIsUnobservedNotImpossible` |
| `EntryDebit` 2 → 1 (both legs CREDIT) | **compiler**: `duplicate case` ×2 |

The graded assertions genuinely read committed oracle bytes:
`TestGLAccountRefusalCodesMatchTheCaptures` decodes each capture and compares the
globalisation code, the `.status` file **and** the body's `httpStatusCode` — three independent
reads per case, **16 cases**, which I counted. `TestValidationRefusalsAreTheValidationFamily`
covers **17** captures, which I also counted. Both numbers in the handoff are correct.

I spot-verified the capture statuses A2-8 quotes, from the `.status` files:
`A2-fin-102` 403 (body: `"Mapping for activity already exists 200"` — quoted verbatim and
correct), `A2-prod-062` 200, `A2-prod-063` 403, `A2-240` 400, `A2-242` 200, `A2-214` 403,
`A2-084` 200, `A2-085` 200, `A2-111` 200, `A2-fin-104` 400. **All match.**
Payment types: `disburse-084` carries `paymentTypeId: 1`, `disburse-085` carries `2` —
matching `A2-150`'s journal entries (transaction 1 → GL 16 via the override, transaction 2 →
GL 2 core). `A2-150` entry id 6 posts to account 1 "Assets" with `account_usage 2` (HEADER),
confirming the HEADER-is-a-valid-posting-target grading.

**Was any test weakened?** No. I diffed the two commits: `git diff 5d80a72 f50e006` over the
test files is **gofmt whitespace only** (column alignment in `money_test.go` and
`resolve_test.go`) plus the wholly-new `financialactivity_test.go`. **No assertion was removed,
loosened, or turned into a skip.** `go test -v` reports **0 SKIP**, and both scans fail if they
inspect zero files.

### (e) P-46 applied to A2-8's own handoff

I grepped its quoted excerpts, field names, numbers and source line ranges against the
artefacts they are attributed to.

**Reproduced exactly:** the 7,489-byte figure and all four zero-counts on `A2-211`; the A2-212
positive control and A2-213 negative control; `A2-7.md:210-212` as the site of the struck
fabrication and `A2-7.md:346` for `2450000.000000`; the six `acc_gl_journal_entry` rows;
`245,000,000` and `120,000,000 = 20,000,000 + 100,000,000` minor units; "seven charge options"
at `1.234500`; cash 23 / accrual 25 members; 22 shared / 19 agree / 3 differ; product 27's two
rows `{16,2}`; the `A2-224` / `A2-225` / `A2-092` message strings; `55 tests`; `5,609
insertions`; the 43/5664 harness figures; the swapped globalisation codes
(`GLAccountInvalidUsageException.java` really does emit
`error.msg.glaccount.classification.invalid`, and vice versa); the
`FinancialActivityAccountDataValidator` create/update asymmetry (create allows
`CASH_AT_MAINVAULT` and `CASH_AT_TELLER`, update does **not** — verified at `:62-66` vs
`:89-92`); the shares create/update helper mismatch in F-7 (create calls
`savingsProductToGLAccountMappingHelper.savePaymentChannelToFundSourceMappings`, update calls
`shareProductToGLAccountMappingHelper.…` — the bug is real); the rule-change wholesale
replacement at `:409-414` / `:416-429`; and the cross-enum gate at `:1253-1254`, which A2-8
noticed and documented as "correct only by the coincidence that
`CashAccountsForSavings.INCOME_FROM_PENALTIES` is also 5" — **I checked, and it is 5.**

**Not reproduced / incorrect:** F-B, F-C, F-D, F-G below. **F-B is the answer to "hunt for a
confident claim that should have been on the `[UNVERIFIED]` list": there is one, and it is
also wrong.**

---

## FINDINGS

### F-A — `ApplicableSlotName` does not carry the applicable family. It is inert, untested, and its documentation is false. **← the required MICRO-FIX**

`errors.go:35-41` says the field *"carries the name from the enum that ACTUALLY APPLIES. The
two differ at codes 22, 24 and 25"*, and the handoff says the port *"carries **both** names"*.
Both statements are false as implemented.

`resolveProductAccount` holds the caller's **typed** `slot` — which *is* the applicable family,
by construction, because the `Slot` interface is closed — and then throws it away:

```go
return nil, r.mappingNotFound(keyType, productID, code)   // resolve.go:283 — `slot` discarded
```

`mappingNotFound` re-derives from the bare `code`, which is precisely the keying trap 2 says is
unsafe, and sets

```go
applicable = fallbackName(haveAccrual, accrual, haveCash, cash, code)   // == rendered, always
```

By inspection `applicable == rendered` unconditionally, in both switch arms. **I measured it**
over all 48 (code, family) pairs:

```
code 22 family=cash    caller passed CLASSIFICATION INCOME     ApplicableSlotName=INCOME FROM CAPITALIZATION
code 24 family=cash    caller passed INCOME FROM DISCOUNT FEE  ApplicableSlotName=BUY DOWN EXPENSE
code 25 family=cash    caller passed FEES RECEIVABLE           ApplicableSlotName=INCOME FROM BUY DOWN
checked 48 (code,family) pairs; ApplicableSlotName disagreed with the slot the caller
actually passed in 3 of them
```

At exactly the three codes where trap 2 bites, on a **cash** product, the field reports the
**accrual** name — i.e. it duplicates the oracle's wrong rendering instead of correcting it.
No test reads it (`grep` returns one assignment and zero reads), so nothing could have caught
this.

**Severity: not a parity defect** — `Message` is oracle-faithful and the field is never
serialised, so no wire byte moves. But it **defeats the exact mitigation A2-8 offered when it
declined the driver's instruction**, and a future contributor consulting `ApplicableSlotName`
on a cash product would be misled at the three codes that matter most. That is worse than not
having the field.

**Fix (4 lines, mechanical, no number, no money logic, nothing on the wire):**

```go
// resolve.go:283
-		return nil, r.mappingNotFound(keyType, productID, code)
+		return nil, r.mappingNotFound(keyType, productID, slot)

// resolve.go:322
-func (r *Resolver) mappingNotFound(keyType PortfolioProductType, productID int64, code int32) error {
+func (r *Resolver) mappingNotFound(keyType PortfolioProductType, productID int64, slot Slot) error {
 	var rendered, applicable string
+	code := slot.Code()
+	applicable = slot.String()          // the family the CALLER actually holds
 	cash, haveCash := CashLoanSlotFromCode(code)
 	accrual, haveAccrual := AccrualLoanSlotFromCode(code)
```

…then delete the two `applicable = fallbackName(...)` assignments and keep `fallbackName` only
for the `rendered` fallback. `rendered` must not change — it is graded by `A2-224`, `A2-225`
and `A2-092`. A test asserting `ApplicableSlotName != Message`'s name for
`CashLoanClassificationIncome` should ship with it, driven red first (P-22).

### F-B — a confident claim about **PostgreSQL** that is wrong, and is not on the `[UNVERIFIED]` list

`glaccount.go:251-254` says the port "deliberately reproduces" two edge behaviours of the
`nameDecorated` SQL, the first being:

> a hierarchy with zero dots yields depth -1, and SQL SUBSTRING with a negative length yields
> the empty string, so the name is returned bare

**That is not PostgreSQL's behaviour, and PostgreSQL is the only permitted database.** I ran it
against the live reference instance's database (`fineract-db-1`, `postgres:18.3`):

```
$ docker exec fineract-db-1 psql -U postgres -d postgres -tAc \
    "select substring('........................................', 1, -4)"
ERROR:  negative substring length not allowed
```

So the oracle would **fail the query**, not return the bare name. The port returns `a.Name`.

**Reachability:** unreachable with data the oracle itself writes — `generateHierarchy()` always
emits at least one `.`, and every hierarchy in `A2-150` does. So this is not a live parity
defect. But it is a **confidently-stated, refutable claim presented as a verified reproduction**,
which is the P-46 shape, and it is exactly the item the brief asked me to hunt for on the
`[UNVERIFIED]` list. It should read: *"[UNVERIFIED — and in fact PostgreSQL raises
`negative substring length not allowed`; this branch is unreachable because every hierarchy the
oracle writes contains at least one dot]"*.

The rest of `NameDecorated` I verified and it is **correct**: the SQL at
`GLAccountReadPlatformServiceImpl.java:49` uses a **40**-character pad and the Go
`hierarchyDecorationRule` is **40** characters (I counted both); `substring(pad,1,0)` returns
`''` so a depth-0 account gets its bare name (port agrees); and `substring(pad,1,44)` returns
the 40-char pad, so the saturation claim is right (port clamps to `len(rule)`).

### F-C — the number "27 JSON `amount` fields" is not reproducible

`money.go:26` and the handoff both state *"All 27 JSON `amount` fields … read `….000000`"*.
My enumeration of `.softhouse/capture/tierA-a2/out/` finds **52** `amount` fields across 147
JSON files (18 of them in `A2-209c`, 34 outside it), **14** distinct journal entries, and
**0** `amount` fields anywhere under `req/`. I could not reproduce 27 by any grouping I tried.

**The substantive claim is nonetheless TRUE** — and I verified it *more* strongly than A2-8
stated it: over all **52** fields, the only sub-minor values are the **7** percentages in
`A2-209c`. Only the count is wrong. Because the number lives in **committed code** as a
`[VERIFIED: …]` measurement, it should be corrected to a reproducible one (or replaced with the
measurement recipe), per P-46 rule 1.

### F-D — the fabrication correction is attributed to the wrong commit

The handoff says *"Both are corrected in commit `f50e006`"*, and `f50e006`'s own commit message
says *"corrected null-vs-absent read rule"*. `git diff 5d80a72 f50e006` shows that commit
contains only gofmt whitespace, the new `financialactivity_test.go`, and the rule-change comment
block in `apishape.go`. **The corrected text — `apishape.go`'s fact (3), the
`THIS CORRECTS AN INHERITED FABRICATION` block, and the `bytes.Contains(raw, []byte("null"))`
assertion — is already present in `5d80a72`, the first commit on the branch.**

The **code is right**; the provenance narrative is not. It also makes A2-8's stronger claim —
*"I had already built on it before the driver's mid-flight message arrived — so this is a
correction I shipped, not a mistake I avoided"* — unsupported by the git record, which shows no
commit that ever contained the fabricated assertion. Not a defect in the port; a claim that
should be corrected so the next reader does not inherit it.

### F-E — the guard hole is wider than F-1 says: **neither in-package scan looks inside subdirectories**

`TestNoCrossFamilySlotConversion` and `TestNoFloatingPointInThisPackage` both use
`os.ReadDir(".")` and `continue` on `e.IsDir()`. I drove it: a file
`nexus/internal/apps/ledger/sub/zz_sub.go` containing `var Rate float64 = 1.5`

- **passes** `go test ./internal/apps/ledger/` (the scans never see it), and
- **passes** `bash .softhouse/conformance.sh` (root is loanschedule-only).

So today a float in any *subdirectory* of the ledger tree has **zero** coverage from either
mechanism. **T166's fix must be a recursive walk rooted at `internal/apps`**, and it must be
driven red against a float planted in a *subdirectory*, not only in a package directory —
otherwise the widened guard will inherit the same blind spot. (`find` is recursive by default,
so widening `conformance.sh:573` to `internal/apps` closes it; the Go-side scans should switch
to `filepath.WalkDir`.)

### F-F — the cross-family scan's evasions, enumerated

Measured above: it catches the direct conversion and the `.Code()` form, and misses the
conversion through an intermediate variable and from a bare `int32`. A2-8 states the limit
honestly; this is the enumeration, recorded so the next fire does not over-trust the guard.
Not a defect — the language cannot do better — but the compiler is the stronger guard here
(duplicate map keys / duplicate switch cases caught two of my six perturbations outright).

### F-G — cosmetic miscount

Handoff: *"18 files: 9 source, 8 test, 1 doc"*. Actual: **10 source + 7 test + 1 doc = 18**
(A2-8's own source table lists 11 non-test files including `doc.go`, so the handoff is
internally inconsistent too). Total and insertion count are correct.

### F-H — rig hygiene, not A2-8's defect: an unused request body that will mislead

`req/disburse-086-nopaymenttype.json` (no `paymentTypeId`) is referenced by **no** capture —
`grep -l` over every `out/*.http` returns nothing. `A2-086`'s `.http` records
`body-file: req/disburse-084-paymenttype1.json`. A reader matching request to capture **by
number** would conclude the duplicate-row 403 arose from a *null* payment type, and would then
mis-derive the whole `NullPaymentTypePolicy` question — the one thing in this slice that is
still contested. `CAPTURE-PLAN.md` should either delete the unused body or record why it exists.
This is A2-8's F-6 recurring on a third file.

---

## What I checked and found nothing wrong with

So that silence is distinguishable from not looking:

- integer-minor-unit discipline everywhere; no float, no `%f`, no `math.`, no `big.Float`, no
  `interface{}` money decode; `UseNumber()` on every decoder
- append-only: nothing writes, stores or caches a balance; `m_trial_balance` correctly declined
- holds: not in scope for this slice (no hold concept exists here)
- `Idempotency-Key`: the package has **no HTTP surface at all**, so the non-negotiable is not
  engaged; A2-7's F-2 (the capture rig sends none) still stands and is unaffected
- PostgreSQL only: no driver imported at all; the doc records `pgx` for a real implementation
- the frozen adapter contract: untouched, not opened, and no change needed
- Mongolia rules: no `first_name`/`last_name`, no US rails/vendors, no
  insured/protected/guaranteed string anywhere in the refusal surface
- NBFI licence: savings/shares resolvers are pure value computations exposing no endpoint, and
  say so at the site
- STEP 0 / STEP 1 / STEP 2 / STEP 3 per family against all four oracle methods, including the
  loan-vs-WCL asymmetry (`paymentTypeId != null` is required at `:1015` and **not** at `:1199`)
  — the port's three named booleans reproduce it exactly
- `IsFamilyReferenceSlot()` = code 1 for loan, savings and shares — verified against
  `CashAccountsForSavings.SAVINGS_REFERENCE(1)` and `CashAccountsForShares.SHARES_REFERENCE`
- `NullPaymentTypePolicy` is genuinely wired into `InMemoryMappingStore.FindByPaymentType`, not
  a dead field; the payment-type query correctly filters only four columns
- the fifth lookup shape (reason / classification) correctly does **not** filter on
  `financial_account_type`
- `single()` refuses `>1` rather than taking the first — the exact silent-wrong-answer this
  role exists to catch, and it is refused
- all 14 `[UNVERIFIED]` items in the handoff are honest and correctly scoped; F-B is the one
  claim that should have joined them

---

## Evidence

All red-drives, perturbations and measurements were run in a scratch copy at
`/tmp/a2-9scratch` (`git archive softhouse/A2-8-ledger-port nexus .softhouse`), reverted after
each probe, and the package left green (`go test ./... → ok`). **No file in
`nexus/internal/apps/loanschedule/`, no other worker's capture subtree, and no file on `main`
was touched.** The Go toolchain came from `.softhouse/bin/go-env.sh`; every build was run from
`nexus/` and never piped into `head`; the harness was invoked with `bash`, never `sh`.
