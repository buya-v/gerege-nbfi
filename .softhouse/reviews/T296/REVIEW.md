# T296 — independent review of T294: the capture holds, the CAPABILITY GATE did not

**Branch** `softhouse/t296-review-t294` · **subject** T294, merged at `e4b9428` (parent `32e6743`,
branch tip `a407f09`) · **pinned Fineract** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(`git rev-parse`, verified this fire) · **evidence** `.softhouse/reviews/T296/`

---

## 0. VERDICT — SPLIT

# APPROVED, WITH ONE MICRO-FIX APPLIED ON THIS BRANCH

**The capture stands.** I attacked the write fence, the precedence inference, the wire
transcription and the money-cell pin, from the pinned source and from the committed bytes, and
**broke none of them**. T294's citations are correct line for line, its safety argument is
correct, and its arithmetic is correct. Nothing in this branch is fabricated and nothing in it is
unsafe.

**One thing T294 did not look at, and it is the one it handed to the reviewer.** T294's backlog
(5) says the `capabilities-ledger.json` flip "widens what a future vector may claim", that "prose
does not fire (P-89)", that "a structural fix (splitting the row) is explicitly forbidden by
T289 F-T289-4", and that it is "worth a reviewer's judgement". Every clause of that is true
**except the third's implied conclusion** — T294 checked whether the ONE structural fix it had in
mind was forbidden, found it was, and stopped. **A structural fix that is not a split and not a
rename was available, in the same file T294 was already editing, and it works.**

I MEASURED the widening rather than arguing it (§3), APPLIED the fix, and DROVE IT RED. The bar is
**PASS exit 0 on the committed tree**, probe line PRESENT reading `up`, every pin unmoved.

| finding | severity | blocking | disposition |
|---|---|---|---|
| **F-T296-1** the flip turned a DATA refusal into a PROSE one, measured two arms | MEDIUM, structural | no | **FIXED on this branch**, red-driven |
| **F-T296-2** the vector grades the COMMAND, not the PREDICATE; the lifted input is inert | MEDIUM, claim scope | no | **FILE A TASK** — no fix exists on this tenant |
| **F-T296-3** "the capture settles it rather than the source" overstates by a hair | LOW | no | note only |

**What I did NOT re-do, because the driver stated it was already verified first-hand:** the
read-only SQL against the live reference oracle (`acc_gl_journal_entry` 60 / maxid 64,
`acc_gl_closure` 0, 26 distinct transaction ids, `m_portfolio_command_source` 351 → 352 disclosed
as `processingResult: "Error"`) and the character-for-character comparison of every `expect.refusal`
cell against `out/OB-01-*.status` and `errors[0]`. I re-checked the artefact side of both anyway
(§2d), because it costs nothing and a manifest is cheap to verify; both hold.

**I fired NOTHING at the reference oracle.** No POST, no GET, no `psql`. T287's four probes were
not touched, `req/a1-02-future-boundary-plus1.json` (arms 2026-08-24) was not read into any runner,
and the one closure-family artefact I used — `A1-01-future-far` — was consumed as **committed bytes
on disk**, never re-sent.

---

## 1. THE PRECEDENCE CLAIM — RE-DERIVED FROM SOURCE, AND IT SURVIVES

The brief called this "the most interesting and the most fragile" claim. It is the first one, and
it holds. I walked the whole route rather than checking T294's table.

### 1a. The route, from the endpoint down, with nothing taken on T294's word

| step | file:line @ `426a23544` | what I read |
|---|---|---|
| `POST /journalentries?command=defineOpeningBalance` | `JournalEntriesApiResource.java:211-212` | `is(commandParam, "defineOpeningBalance")` → `CommandWrapperBuilder().defineOpeningBalanceForJournalEntry()` → `logCommandSource` |
| the handler | `DefineOpeningBalanceCommandHandler.java:30,37-38` | `@CommandType(entity="JOURNALENTRY", action="DEFINEOPENINGBALANCE")`, body is `return this.writePlatformService.defineOpeningBalance(command);` — **a bare pass-through, no validator in between** |
| the service | `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:701-703` | `@Transactional`, `defineOpeningBalance(JsonCommand)` |
| guard | `:717` `validateJournalEntriesArePostedBefore(contraId)` → `:810-816` | throws `GeneralPlatformDomainRuleException("error.msg.journalentry.defining.openingbalance.not.allowed", "Defining Opening balances not allowed after journal entries posted", transactionIds)` |
| the competing rule | `:724` → `:651` `checkDebitAndCreditAmounts(credits, debits)`, defined at `:306-326` | `creditsSum.compareTo(debitsSum) != 0` → `JournalEntryInvalidException(DEBIT_CREDIT_SUM_MISMATCH)` |

**Both grounds genuinely exist for OB-01 and they are evaluated in one pass, sequentially, in one
method, inside one transaction.** `:717` precedes `:719-721` (office lookup) precedes `:724`
(business rules, which contains `:651`) precedes `:726-735` (the reversal loop, the first domain
write) and `:742`/`:745` (the persists). Every one of those line numbers is what T294 says it is.

### 1b. The three "third explanations" I looked for and did not find

1. **An earlier validator that could have answered instead.** `:706`
   `journalEntryCommand.validateForCreate()` — read in full at
   `fineract-accounting/…/command/JournalEntryCommand.java:59-113`. It checks `transactionDate`
   not-blank, `officeId` > 0, `currencyCode` not-blank, comment/reference lengths, and per-leg
   `glAccountId` not-null / `amount` zero-or-positive. **It does not sum debits against credits.**
   So it cannot be the reason the balance rule "lost"; it never ran on the balance at all.
2. **A filter or ordering by validation stage.** There is none. The command bus hands the JSON
   straight to the service (`DefineOpeningBalanceCommandHandler` above); the two checks are two
   statements seven lines apart with no branch, no early return and no exception handler between
   them (`:753` catches only `JpaSystemException | DataIntegrityViolationException`, neither of
   which either check throws).
3. **A conditional that could suppress `:651` for this body.** `checkDebitAndCreditAmounts` is
   `BigDecimal.compareTo` on unscaled sums. No currency, no `MathContext`, no rounding mode, no
   tenant parameter is consulted. It would have fired.

**VERDICT ON THE CLAIM: SOUND.** `:717` beats `:651`, the pair is genuinely ordered, and the
"only ordered refusal pair in this corpus" claim survives — `LDG-REFUSE-01` (A2-344) is unbalanced
with both legs on manual-permitted accounts and `LDG-REFUSE-02` (A2-346) is balanced, so neither
violates two rules and the manual/balance precedence really is `[UNVERIFIED]`.

### 1c. F-T296-3 (LOW, note only) — one word of overstatement

The vector's `_note` says *"here the capture settles it rather than the source."* The source was
never ambiguous: two sequential statements in one method with nothing between them. The capture
**confirms** an unambiguous source order; it does not adjudicate a genuine uncertainty. T294 says
"Source agrees" in the same sentence, so nothing here is false and no edit is required — but a
later reader should not take "measured precedence" to mean "the source could not have told us".
**Not a defect. Recorded so the next reader of that sentence calibrates it.**

---

## 2. THE UNBALANCED-BODY WRITE FENCE — ATTACKED, NOT BROKEN

The brief asked whether any tenant state, config, currency setting or code path makes a
one-minor-unit imbalance acceptable. **I could not find one. Here is exactly where I looked**, so
the absence is a statement about the search and not a shrug.

### 2a. The comparator itself — `:306-326`

```java
for (final SingleDebitOrCreditEntryCommand creditEntryCommand : credits) { … creditsSum = creditsSum.add(creditEntryCommand.getAmount()); }
for (final SingleDebitOrCreditEntryCommand debitEntryCommand  : debits ) { … debitsSum  = debitsSum.add (debitEntryCommand.getAmount ()); }
if (creditsSum.compareTo(debitsSum) != 0) { throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.DEBIT_CREDIT_SUM_MISMATCH, …); }
```

`BigDecimal.compareTo`, unscaled, on the sums. **Nothing tenant-scoped enters it** — not
`m_currency.decimal_places`, not `MoneyHelper.getMathContext()`, not the rounding mode. A tenant
configured with MNT at 0 decimal places changes nothing here, because no rounding is applied
before the comparison.

### 2b. The parse — the only remaining lever, followed to the bottom

`amount` reaches the command through
`JournalEntryCommandFromApiJsonDeserializer.populateCreditsOrDebitsArray` →
`fromApiJsonHelper.extractBigDecimalNamed("amount", creditElement, locale)` →
`JsonParserHelper.java:142-156` → `convertFrom(valueAsString, parameterName, locale)` at `:702-753`:

```java
final Number parsedNumber = numberFormatter.parse(source, clientApplicationLocale);
if (parsedNumber instanceof BigDecimal) { number = (BigDecimal) parsedNumber; }
else { number = BigDecimal.valueOf(parsedNumber.doubleValue()); }
```

Spring's `NumberStyleFormatter` returns a `DecimalFormat` with `setParseBigDecimal(true)`, so the
first branch is taken and **no double is constructed**. Two degenerate cases checked anyway:

- a locale in which `.` is a **grouping** separator parses the two tokens as `25000025` and
  `25000024` — still unequal, still refused;
- a locale that cannot parse them at all throws `PlatformApiDataValidationException` at `:744-752`
  — a refusal, still no write;
- an absent `locale` throws at `:704-714` — a refusal, still no write.

### 2c. Why the fence is *stronger* than T294 claimed

The reversal loop at `:726-735` — the first domain write — sits **after** `:724`, and `:724`
contains `:651`. So for OB-01 to write anything, `creditsSum.compareTo(debitsSum)` must return
`0`. It cannot. **Every branch I can reach out of `defineOpeningBalance` for this body ends in a
refusal before a domain write**, whatever the ledger, the clock, the closure table or the currency
config say. T294's Fence 1 is correct and it is load-bearing.

*One note for accuracy, already disclosed by T294 and not a finding:* "throws before any write" is
true of the **domain** write. The `m_portfolio_command_source` audit row is a write, it happens on
the command-source path outside this method, and T294 both disclosed it (§5) and characterised its
public face (`processingResult: "Error"`). That is the correct scoping, stated correctly.

### 2d. The artefacts, re-verified

```
shasum -a 256 -c MANIFEST.sha256              →  32 lines, 32 OK
cmp req/ob-01-….json out/OB-01-….req          →  silent (byte-identical)
sha256(out/OB-01-….req)   dae579d2…e7e70aeae  ==  vector provenance.request_capture_sha256
sha256(out/OB-01-….json)  9383ed52…46a06462b7  ==  vector provenance.capture_sha256
out/OB-01-….status        403                  ==  expect.http_status / expect.refusal.http_status
errors[0].userMessageGlobalisationCode         ==  expect.refusal.code
errors[0].defaultUserMessage                   ==  expect.refusal.message
```

The message is `Defining Opening balances not allowed after journal entries posted`, identical in
the wire body and at `:814`. Nothing was transcribed from the Java constant in place of the wire —
they are the same characters, so there was nothing to get wrong, and T294 said so rather than
claiming a victory over a conflict that never arose.

---

## 3. F-T296-1 (MEDIUM, structural) — THE CAPABILITY FLIP, MEASURED

**This is the finding.** T294 named the risk and left it to the reviewer; the reviewer's job was to
turn it into a number.

### 3a. The reproduction

`probe/build-closure-probe-vector.py` builds a **closure-family** refusal vector — the FUTURE-DATED
shape, one of the three that `ledger.opening.balance.and.closure`'s own `description` names — out of
**T287's real, committed raw artefacts** `A1-01-future-far.{json,req}`, with the sha256s recomputed
from those bytes so it clears provenance verification on its own merits. It is a plain create
(`command: ""`), so none of T294's three new opening-balance inputs is set and none of T294's new
admissibility rules can account for the result.

`probe/measure-capability-gate.sh` runs it twice against a **scratch copy** of the store. The two
registries differ in exactly one boolean.

```
ARM B   ledger.opening.balance.and.closure  in_graded_domain FALSE   (the pre-T294 state)
        LDG-REFUSE-04-PROBE-future-dated-entry   INADMISSIBLE   0 cells

ARM A   ledger.opening.balance.and.closure  in_graded_domain TRUE    (the merged state)
        LDG-REFUSE-04-PROBE-future-dated-entry   FAIL           3 cells (0 money)
```

[`out/capgate-armA-merged.txt`, `out/capgate-armB-flip-reverted.txt`]

**Before T294 the registry refused an unobserved shape as DATA. After T294 it admits and grades it,
and the only thing saying it should not be there is the row's `evidence` prose.** `P-89`, whose text
is *"PROSE DOES NOT FIRE ON THE NEXT FIRE — a limit written into a handoff, a review, or a
`## Backlog` heading is invisible to the scheduler"*, is precisely this shape, and T294 cited it
against itself while leaving the condition in place.

### 3b. What the store's OTHER defences do and do not cover

Worth recording, because the first run of this probe was refused by a **different** gate and I
nearly mis-attributed it. With `graded_against: []` the harness says:

```
graded_against is empty. A vector that kills no named wrong implementation is a capture,
not a grader, and the store must not pretend otherwise
```

That is a real and good defence, and it means the "free-ride on LDG-REFUSE-03's kill" I went looking
for **does not exist**. Provenance sha256 verification and the wrong-implementation census also
stand. **The gap is narrower than I first supposed and it is still real:** once a closure vector
names any kill, nothing but prose stops it claiming a capability for a shape this store has never
observed.

### 3c. The fix, and why it is not the one T289 forbade

Applied in `nexus/internal/apps/ledger/conformance/admit.go` (commit `40673a3`): a vector may name
`ledger.opening.balance.and.closure` **only when `request.command == "defineOpeningBalance"`** — the
one shape that was actually observed.

**T289 F-T289-4 settled that the row is coherent and must not be renamed or split**, because
`defineOpeningBalance:703` reaches the same guard at `:724` that the manual create path reaches at
`:157`. **This rule renames nothing and splits nothing.** The row stays one row and keeps naming all
three shapes. What is scoped is the *claim a vector may make on it*. T294 tested one candidate fix
against T289's ruling, found it forbidden, and concluded no structural fix existed — the search
stopped one step early, in the file it had open.

**Driven RED, because a rule nobody has seen refuse is a rule nobody has tested** (`P-22`, *"a
control that cannot fail is worse than none"*). `TestOpeningBalanceCapabilityIsScopedToTheObservedShape`
in `openingbalance_test.go`; `probe/run-go-tests.sh` deletes the rule and re-runs it:

```
--- FAIL: TestOpeningBalanceCapabilityIsScopedToTheObservedShape (0.14s)
    … was ADMITTED, or refused for another reason … : []
```

**`[]` — an EMPTY reason list.** Without the rule, a plain-create vector claiming this capability is
admitted with no complaint whatsoever. [`out/go-tests-and-red-drive.txt`]

The anti-vacuity control is `TestOpeningBalanceInputsAreDefaultDeny`'s first sub-test, which requires
the committed vector to stay ADMITTED — so a rule that refused everything goes red there instead of
passing silently here. With the rule in place, ARM A now refuses the probe while `LDG-REFUSE-03` stays
`PASS`, `ledger oracle-refusal PASS 3 FAIL 0`.

**When a closure refusal is finally promoted — T294 backlog (6) — that task must widen this rule
deliberately, with the capture in hand, instead of finding the door already open.**

---

## 4. F-T296-2 (MEDIUM, claim scope) — THE VECTOR GRADES THE COMMAND, NOT THE PREDICATE

T294 registered one wrong implementation and showed it dies. The brief's harder question — does the
vector kill defects the author did **not** ship beside it — is answered by mutating the **port** and
re-grading. Four arms, `probe/mutate-the-port.sh`, [`out/mutation-arms.txt`]:

| arm | GoPoster STEP 1.5 predicate | ledger corpus |
|---|---|---|
| BASE | `req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0` | PASS 4 / refusal PASS 3 |
| **A** | `req.Command == "defineOpeningBalance"` — the id list is never read | **PASS 4 / refusal PASS 3 — SURVIVES** |
| **B** | `len(req.PostedNonContraTransactionIDs) > 0` — the command is never read | **PASS 4 / refusal PASS 3 — SURVIVES** |
| E | the rule moved BELOW the balance check (the precedence flip) | **FAIL — refusal PASS 2 FAIL 1** |

**Arm E is the good news and it is T294's headline claim, empirically true:** the vector really does
grade that the port places the opening-balance rule ahead of the balance rule. That part is not
vacuous and `TestOpeningBalanceRefusalPrecedesTheBalanceRule` checks its own premise properly (it
re-derives the imbalance from the vector's own `amount_major_text` characters, by exact string
arithmetic, no float even in a premise check — and would `t.Fatalf` if a later edit balanced it).

**Arm A is the finding.** A port that refuses **every** `defineOpeningBalance` command — including on
an empty ledger, where the oracle **accepts** (`:812` `CollectionUtils.isEmpty(transactionIds)` is
true and execution falls through to the writes at `:742`/`:745`) — is green on this entire corpus.
That is not an exotic defect. It is exactly the shape of `headerRefusingPoster`, which this corpus
already names as a real class: *"THE DEFECT: it is the reasonable thing to do and the oracle does not
do it."* An over-refusing opening-balance port is the same mistake wearing different clothes, and
`LDG-REFUSE-03` cannot see it.

**Why this is a claim defect and not just a coverage limit.** T294's §10 states plainly that the
accepting side is unverified and *"Nothing in this branch claims it"* — correct, and honest. But
T294 **did** claim something about the lifted input, three times, and that claim is what arms A and
B falsify:

> *"The vector carries the oracle's own list (`request.posted_non_contra_transaction_ids`,
> transcribed from `errors[0].args`), so this port reads a length rather than a boolean somebody
> derived for it."* — `impl.go` STEP 1.5, and the same argument in the vector `_note` and handoff §6

The port **need not read it at all**. `posted_non_contra_transaction_ids` is admitted, transcribed,
validated for blanks, and **inert for grading**. It is a `P-89`-shaped artefact — *"shipped wired to
nothing"* — and unlike the three cases that pattern was written about, **this one did not declare
itself**: it was presented as the thing that makes the vector non-vacuous.

**There is no fix available on tenant `gerege`.** Killing arm A needs an ACCEPTING opening-balance
observation, which needs an empty ledger or one where every transaction touches GL 15 — and T294 is
right that reaching either destroys the corpus every other ledger vector cites. I therefore did
**not** patch anything here.

**RECOMMENDED, as a filed task rather than a sentence** (`P-89`: *"an unwired guard MAY merge … but
ONLY against a FILED, DISPATCHABLE TASK with an owner, a dependency edge, and a red-drive
requirement"*):

1. **Correct the claim** where it is made — `impl.go` STEP 1.5, the vector `_note`, the capability
   evidence — from "the port reads a length" to "the port MAY read a length; nothing in this store
   requires it, because the accepting side of `:812` is unobserved [T296 arm A]."
2. **Cheap partial hardening, vector-side:** `admit.go` could require
   `len(posted_non_contra_transaction_ids) > 0` whenever `expect.refusal.code` is
   `error.msg.journalentry.defining.openingbalance.not.allowed`. It constrains the vector, not the
   port, so it does not close arm A — say so when writing it, or it becomes the next thing a
   reviewer has to disprove.
3. **The real closer is a second tenant**, not a second vector: an opening-balance ACCEPT captured
   on a fresh tenant with an empty ledger kills arm A outright and is the only thing that does.

---

## 5. THE MONEYCELLS PIN — VERIFIED FROM THE COMPARATOR, NOT FROM THE CLAIM

T294 held `EXEMPTION_PIN_LEDGER_MONEYCELLS` at 21 and argued `cmpMoney` is unreachable on a refusal
path. **Read, not deferred to.**

- `grade.go:512-524` — `switch v.Expect.Kind { case "refusal": diffRefusal(...) ; default: … diffEntry(...) }`.
  `diffEntry` is the **only** caller of `cmpMoney` (`:183`, `:190`, `:195`). A `refusal` vector never
  reaches it.
- `diffRefusal` (`:205-221`) compares exactly three cells through `cmpInt` and `cmpStr`. There is no
  fourth cell and no money cell on that path, on either branch — including the `got == nil` branch,
  which still names and counts the same three.
- Belt and braces: even if `diffEntry` *were* reached, `expect.legs` is `[]` and both totals are
  `""`, and `parseMinor("")` returns an error (`:224-226`) which suppresses the totals comparison.
  **Zero money cells by two independent routes.**

**The pin at 21 is correct by construction, not by luck**, and the inverse warning T294 wrote beside
it — *"if that number ever rises on a refusal vector, the comparator has started grading an amount
nobody observed"* — is the right thing to have written there. `PARITY` 4, `REFUSAL` 2 → 3 and
`WRONGIMPLS` 6 → 7 all reproduce.

---

## 6. THE BAR — RUN BY ME, ON A COMMITTED TREE

`P-84`, whose text is *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING — READ THE ABSENCE, NOT THE
VALUE … four exit-2 paths precede the probe, and a failed HARD guard is one of them"*, applied
first: **the probe line's PRESENCE was read before its value.**

Run 1 — the merged tree, before any change of mine:

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

Run 2 — **after `git add -A` and `git commit`**, honouring T294's own §11 lesson (*"`ledgerguard`
reads the tree through `git ls-files`, so an UNTRACKED file is invisible to it. A bar run before
`git add` is not the bar"*). My micro-fix touches a Go file that guard scans, so this is the run that
counts [`out/bar-t296.txt`]:

```
conformance: reference oracle (…/actuator/health) probe = up            ← PRESENT, and `up`
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
conformance:   exemption census READ: LEDGER oracle-refusal vector = 3 == pinned 3
conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
conformance: CENSUS wrong ledger implementations — discovered 7 … pinned at 7
conformance:   all 7 wrong ledger implementations DIED through this harness, not by hand.
EXIT=0
```

`go test ./internal/apps/ledger/...` — both packages ok [`out/go-tests-and-red-drive.txt`]. Nothing I
added moved a pin: my change is one admissibility rule plus one test function, in two files that
already existed.

---

## 7. WHAT I TRIED THAT FAILED — the coverage of the search

An approval is only worth what the search behind it was worth, so here is what did **not** produce a
finding:

- **A fourth explanation for the observed precedence** — the command bus, the handler, the
  `@Transactional` boundary, the `catch` at `:753`, and `validateForCreate` in full. Nothing between
  `:717` and `:651` but straight-line code (§1b).
- **An attack on the write fence via locale, currency decimal places, `MathContext`, or a double in
  the parse path.** `convertFrom`'s `BigDecimal.valueOf(double)` branch at `:735` is a genuine latent
  float path in the oracle — worth someone's attention for its own sake — but Spring's
  `NumberStyleFormatter` sets `parseBigDecimal(true)`, so it is not taken, and it would not have
  equalised these two amounts if it were (§2b).
- **A free-ride on `LDG-REFUSE-03`'s kill** by a closure vector with `graded_against: []`. Blocked by
  a gate I did not know about until it fired (§3b).
- **A vacuous premise in `TestOpeningBalanceRefusalPrecedesTheBalanceRule`.** It re-derives the
  imbalance from the vector's own characters and fails loudly if a later edit balances the request.
  It is a good test.
- **A `divergent_cells` overclaim.** `graded_against` names `refusal.code` and `refusal.message` and
  **not** `refusal.http_status`; arm E's measured diff is exactly those two. Declared claim and
  measured diff match cell for cell — `T9-F1b` respected.
- **Byte infidelity anywhere in the rig.** 32/32 manifest, `cmp` silent, both sha256s match the
  vector (§2d).

---

## 8. FOR THE MERGING TASK

1. **Merge this branch.** It is one admissibility rule, one red-driven test, and the review's
   evidence. Bar green on the committed tree.
2. **File F-T296-2** with a red-drive requirement, per `P-89`. The claim correction (§4 item 1) is
   the cheap half and should not wait for the capture.
3. **T294's own backlog items 1–6 stand and are all worth taking**, particularly (1) — T294 found by
   source reading that `GoPoster` may have the manual-permission / balance precedence **backwards**,
   named the exact one-capture experiment that settles it (unbalanced **and** targeting GL 18, so the
   body is unpostable by construction — a textbook `P-92` content fence), and correctly declined to
   change the port on a source reading. **That is the next A2 capture and T294 is right about it.**
4. **T287's four probes are still armed and `a1-02` armed on 2026-08-24 — yesterday, as of this
   review.** T294 flagged it; nothing in T294 or T296 disarms it. Backlog (6) — promote the raw
   observations under T289's strategy (c) and never re-fire — remains the only move that both
   promotes them and disarms them.
