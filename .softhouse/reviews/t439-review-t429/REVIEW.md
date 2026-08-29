# T439 — INDEPENDENT REVIEW of T429 (the oracle-derived column declaration)

## VERDICT: **APPROVED WITH CONDITIONS**

**3 MINOR, 4 LOW, 0 MAJOR. Nothing blocks the merge.** No money or structure column
was moved out of grading; the claim that a 19-column protected set is hard-coded in Go
and unreachable from the JSON is **TRUE AND DRIVEN**, including in the hard case where
the attacker also moves the Go pins.

Reviewer branch `softhouse/T439-review-t429`. Target `softhouse/T429-oracle-derived-columns`
@ `875baee3`. Every measurement below was re-taken by this reviewer; nothing is inherited
from T429's handoff.

| stamp | value |
|---|---|
| Fineract pin | `426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `git -C /Users/buv/fineract rev-parse HEAD`, checkout clean, read **before** any line number] |
| oracle health | `{"status":"UP","groups":["liveness","readiness"]}` at **`2026-08-29T00:42:43Z`** [VERIFIED] |
| database | PostgreSQL **18.3**, `fineract_gerege`, container `fineract-db-1`, tenant `gerege` [VERIFIED] |
| DB clock at first probe | `2026-08-29 00:41:34.359915` UTC [VERIFIED] |
| mutations to the oracle | **ZERO.** Every SQL statement is a `SELECT` (files under `out/*.sql`); every HTTP call is a `GET`. |

Scratch worktrees were kept **outside the repository, in `/tmp`** (`/tmp/t439-t429git`,
`/tmp/t439-t429tree`). No nested checkout was created inside the repo.

---

## THE BAR — probe PRESENCE tested before its value

**T429's tree** (`/tmp/t439-t429git`, a real git worktree):

| | |
|---|---|
| **`probe = ` line PRESENT AT ALL?** | **YES — `grep -c` = 1** |
| its value | **`up`** |
| **EXIT** | **0** |
| VERDICT | `PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` |
| carve-out block | `oracle-derived columns 3 (pinned 3)  provenance 7  graded 3  graded-gap 18` · `graded cell vocabulary 14 (pinned 14)` |
| ledger | `cells compared 268 graded, of which 63 are MONEY cells in int64 minor units` · `LEDGER money cells = 63 == pinned 63` |
| wrong ledger implementations | 15 discovered, **all 15 DIED through the harness** |
| dead-path | `frontier 11, pinned at 11` · `deadOccurrences 108` |

**MERGE RESULT with today's `main` (`e4bde474`)** — merged with `git merge --no-edit main`,
**exit 0, ZERO conflicts**:

| | |
|---|---|
| **`probe = ` PRESENT?** | **YES — `grep -c` = 1**, value **`up`** |
| **EXIT** | **0** |
| VERDICT | `PASS (exit 0) — 46 parity vectors ... 7884 cells compared.` |
| carve-out block | **identical** — 3 / 7 / 3 / 18, 14 cells |
| ledger | `268 graded / 63 MONEY`, unchanged |
| wrong implementations | **16** (main added one) — **all 16 DIED** |
| `go build ./...` | clean |
| `go test ./...` | `ledger`, `ledger/conformance`, `loanschedule`, `loanschedule/conformance` all **ok** |

**A NOTE ON EXIT 2 BEFORE THE PROBE, observed rather than theorised.** My first bar run was
against a `git archive` extraction (`/tmp/t439-t429tree`, no `.git`). It returned **EXIT 2 with
NO `probe = ` line at all** — seven guards refused because `git rev-parse` failed. That is the
harness **failing closed**, and it is exactly why presence is tested before value. It is an
artefact of my extraction method, **not** a defect in T429. Transcript kept out of the repo.

---

## 1. THE MONEY BOUNDARY — all 31 columns audited independently

**The column inventory was re-measured from `information_schema`, not read from the JSON:
31 columns** [VERIFIED: `out/R01-columns-and-i5.txt` §R01.2/R01.3]. The declaration's 31 names
match the database's 31 exactly.

### Could any of the 3 ORACLE-DERIVED columns carry money or ledger structure?

| column | type | carries money? | verdict |
|---|---|---|---|
| `organization_running_balance` | `numeric NOT NULL` | **money-VALUED, but not a posting fact** | correctly exempt |
| `office_running_balance` | `numeric NOT NULL` | same | correctly exempt |
| `is_running_balance_calculated` | `boolean NOT NULL` | no — it is job 9's own work queue | correctly exempt |

Two of the three hold currency amounts, so this deserved the hardest look I could give it.
**The exemption is correct, and the structural reason is stronger than the one T429 gives.**

T429 argues from the port's shape: `PostedEntry`/`PostedLeg` carry no balance member, so the
port cannot produce one [RE-VERIFIED by me: `internal/apps/ledger/conformance/impl.go:61-96` —
`PostedEntry{TransactionID, RequestedAmountMinor, HasRequestedAmount, Legs, TotalDebitsMinor,
TotalCreditsMinor}`, `PostedLeg{AccountID, AccountCode, Side, AmountMinor, SlotName}`; **no
balance field at any level**]. That is true but it is an argument about the *port*, and a
reviewer should not accept "we built it so it cannot" as a reason not to grade something.

**The load-bearing reason is that the running balance is a PURE FUNCTION OF COLUMNS THAT ARE
GRADED.** It is `Σ amount` over prior entries of the same account, signed by `type_enum`
against `acc_gl_account.classification_enum`, ordered by `entry_date, id`
[VERIFIED: `JournalEntryRunningBalanceUpdateServiceImpl.java:220-250`, and re-derived
arithmetically on account 41 below]. Every input — `amount`, `account_id`, `type_enum`,
`entry_date` — is `GRADED` or a protected `GRADED_GAP`. **So the carve-out creates no hiding
place: a defect that could corrupt a running balance must first corrupt a graded input.**
The converse is also measured — the stored balance can be wrong while every input is right
(A2-29's MNT 2,000,000.00; and today's zero), which is precisely why grading it would grade
the oracle's defect.

### Could any of the 7 PROVENANCE columns carry money or ledger structure?

The only one worth attacking is **`id`**, because leg ORDER is ledger structure and the order
is induced by `id`. **It is answered, and not by T429's stated reason.** T429 says a vector
identifies an entry by `(transaction_id, leg order)`. What actually closes it is that
**leg order is itself graded**: `PostedEntry.Legs` is documented *"Order is graded: the
oracle's read-back order is stable by entry id and a port that reorders legs is a port whose
output cannot be diffed against the oracle's"*, and every cell is positional
(`legs[i].gl_account_id`, `legs[i].entry_side`, `legs[i].amount_minor`)
[VERIFIED: `impl.go:74-78`, `grade.go:206-236`]. **The ordering `id` induces is graded even
though the id VALUE is not.** Exempting the surrogate key is correct.

The other six are audit actor and audit instant. The line T429 drew is the right one and I
checked it explicitly: **the three ACCOUNTING dates — `entry_date`, `transaction_date`,
`submitted_on_date` — are all in the protected 19 and all `GRADED_GAP`.** Only the audit
instants (`created_on_utc`, `last_modified_on_utc`, and the two dead legacy columns) are
exempt. A declaration that had quietly swept `entry_date` in with the timestamps would have
been the failure this task exists to prevent; it did not.

Measured facts underwriting the seven [VERIFIED: `out/R01-columns-and-i5.txt` §R01.6]:
`created_date` NULL **109/109**, `lastmodified_date` NULL **109/109**, `last_modified_by = 2`
on **109/109** including the 18 never modified, `created_by` 91×1 / 18×2. All reproduce.

### THE DRIVE — I tried to exempt a money column through the JSON, twice

**D1a — `amount` → `ORACLE_DERIVED`, JSON only.** `EXIT 2`. Four arms fired at once
[`out/t439-d1a.txt`]:

```
table "acc_gl_journal_entry" column "amount" is declared ORACLE_DERIVED. IT IS AMOUNT --
the leg amount -- integer minor units, the cell the whole corpus exists for. MONEY AND
STRUCTURE ARE GRADED, ALWAYS ... This set is HARD-CODED in
ledger/conformance/oraclederived.go and the declaration cannot override it
```

plus the forbidden-cell arm, plus `declares 2 GRADED columns, PINNED 3`, plus
`declares 4 ORACLE_DERIVED columns, PINNED 3`. The whole ledger context went FATAL:
`parity PASS 0 FAIL 0`, `cells compared 0`.

**D1b — the case that actually proves the claim.** A naive JSON edit trips the counting arms,
so I ran the sophisticated attack: `amount` → `PROVENANCE` (which needs no `forbidden_cells`,
silencing that arm) **and moved the Go pins to match** (`ProvenanceColumnPin 7→8`,
`GradedColumnPin 3→2`), silencing both counting arms. Rebuilt, re-ran. **`EXIT 2`, and the
money-column guard fires ALONE** [`out/t439-d1b.txt`]:

```
LEDGER FATAL: ... table "acc_gl_journal_entry" column "amount" is declared PROVENANCE.
IT IS AMOUNT -- the leg amount -- integer minor units, the cell the whole corpus exists for.
```

**The claim is true. The JSON cannot reach that rule, and neither can moving the pins.**

**Found clean:** the 19 members of `moneyAndStructureColumns` are the correct 19. I checked
the complement: the 12 unprotected columns are `id`, `ref_num`, `description`, the four audit
columns, the two dead legacy columns, and the three running-balance columns. **`ref_num` and
`description` are the only two columns that are `GRADED_GAP` without being protected** — see
F-3 below for what that permits and what it costs an attacker.

---

## 2. IS `GRADED_GAP` GRADED, OR AN EXEMPTION WITH A BETTER NAME?

**They print.** All 18 appear by name in the bar output at lines 729-746 of the transcript
[VERIFIED: `out/R05-bar-t429-baseline.txt`], under the heading
`18 COLUMNS ARE GRADED_GAP — money or structure with NO CELL YET. THAT IS A COVERAGE GAP, NOT
AN EXEMPTION`.

**Now the adversarial answer, plainly: NO, `GRADED_GAP` IS NOT GRADED. Nothing compares those
18 columns today.** The comparator's whole vocabulary is 14 cells and only 3 of the 31 columns
have one. Operationally, on this run, a `GRADED_GAP` column is as uncompared as an
`ORACLE_DERIVED` one. T429's handoff does not claim otherwise — it says "money or structure
with no cell yet" — but the framing "*not one moved out of grading*" invites a reader to hear
"still graded", and 18 of the 21 money/structure columns are not being compared by anything.
**That sentence should be read as *not one moved out of the graded DOMAIN*, which is true, and
not as *all 21 are compared*, which is false.**

**What the fourth name actually buys, and it is not nothing — three mechanical differences:**

1. **It is named in the printed output every run.** An `ORACLE_DERIVED` column is printed as
   permanently excluded; a `GRADED_GAP` column is printed as a debt. A reader counting
   coverage sees 18 named debts rather than a silence.
2. **16 of the 18 CANNOT be reclassified as exempt at all** — they are in the protected 19,
   and D1b shows what happens if you try.
3. **The remaining 2 require a Go source edit.** Driven — see F-3.

**What would have to happen for one to become graded** (I traced the path for `office_id`):
a capture from a *second office* (today every capture is office 1, so a cell could not fail —
P-98); a comparison emitted by `diffEntry`; that cell appearing in `CellFields()`'s measured
vocabulary; its addition to `graded_cells`; the column moving `GRADED_GAP → GRADED`; and
`GradedCellPin 14→15`, `GradedColumnPin 3→4`, `GradedGapColumnPin 18→17` all moving in the
same commit. **Every one of those is a Go diff.** That is a real ratchet, and it is the
correct design.

---

## 3. THE CONTRADICTED DEC-2 CARDINAL — re-measured, and DEC-2 confirmed byte-unchanged

**DEC-2 IS BYTE-IDENTICAL.** `docs/adr/DEC-2-gl-accounting-adapter.md` is blob
**`fd5e571839aefea088c790e33da538922b1e69dd`** on `main` **and** on
`softhouse/T429-oracle-derived-columns` — the same object, not merely equal content
[VERIFIED: `git rev-parse main:… / softhouse/T429-…:…`]. The only `docs/adr/` change in the
three-dot diff is an **`A`** (add) of the separate proposed-revision file.
**The hard gate was respected.** [CLEAN]

**The cardinal, re-measured by me at `2026-08-29T00:41:34Z`** [VERIFIED: `out/R01-columns-and-i5.txt` §R01.4]:

```
 total | modified | untouched | null_lm | negative
   109 |       91 |        18 |       0 |        0
```

DEC-2's I-5 says **"60 of the 60 rows … carry `last_modified_on_utc > created_on_utc`"** and
concludes the column **"discriminates nothing"** [VERIFIED: `DEC-2-gl-accounting-adapter.md:1061`].
**Both halves are false at this instant.** It is 91 of 109, and the column discriminates
**one-to-one** with `is_running_balance_calculated`:

```
 is_running_balance_calculated | modified | count
 f                             | f        |    18
 t                             | t        |    91
```

There is no off-diagonal cell. [VERIFIED: §R01.5]

**This is now the fourth independent measurement** (`60/60` → `60/91` → `91/109` → `91/109`),
by four tasks at four instants, and T429's figures reproduce exactly.

**T429's handling is correct and I looked for the wrong version of it.** It did not edit the
ratified document, wrote `docs/adr/DEC-2-PROPOSED-REVISION-T429-oracle-derived-columns.md`,
and raised **G-22**. [CLEAN]

**One thing worth recording that neither T429 nor the brief says: the contradicted clause is
NOT LOAD-BEARING.** DEC-2's I-5 reaches "ungraded" on a *different* ground it states in the
same row — *"a snapshot never observes a write, so it cannot separate 'flags and adds' from
'flags and rewrites' whatever the timestamps say"* — and refuses with
`ErrNoDiscriminatingVector` because **no reversal capture has been promoted to a vector**.
**So correcting the cardinal changes no grading decision in DEC-2.** That is why this is a
document-hygiene gate and not a correctness one, and it supports G-21's standing remedy:
**delete the live-oracle cardinal rather than refresh it** — it will be wrong again the next
night job 9 runs.

---

## 4. THE DECISIVE OBSERVATION — RE-OBSERVED FROM THE LIVE ORACLE

`GET /journalentries/96?runningBalance=true`, issued by me with an `Idempotency-Key`,
**HTTP 200**, at **`2026-08-29T00:42:43Z`** [VERIFIED: `out/R04-je96-runningbalance.json`]:

```json
{"id":96, ... "glAccountId":41,"glAccountCode":"T388-1200",
 "glAccountType":{"id":1,"code":"accountType.asset","value":"ASSET"},
 "entryType":{"id":2,"code":"journalEntrytType.debit","value":"DEBIT"},
 "amount":12356.340000,"transactionId":"L32",
 "officeRunningBalance":0.000000,"organizationRunningBalance":0.000000,
 "runningBalanceComputed":false}
```

**Every term of T429's claim reproduces**, and the wire body independently confirms two things
T429 asserted from the database: account 41 is **ASSET** and `type_enum 2` is **DEBIT**.

**The derived balance, re-derived by me from the table rather than from any stored column**
[VERIFIED: `out/R03-attribution-entry96.txt` §R03.6] — the four DEBITs on ASSET account 41 in
`entry_date, id` order:

```
 78 | L29 | 2026-02-15 | 24000.000000 | running 24000.000000  | computed t
 84 | L30 | 2026-03-15 | 20195.380000 | running 44195.380000  | computed t
 90 | L31 | 2026-04-15 | 16314.670000 | running 60510.050000  | computed t
 96 | L32 | 2026-05-15 | 12356.340000 | running     0.000000  | computed f   <-- 72866.39
102 | L33 | 2026-06-15 |  8318.850000 | running     0.000000  | computed f   <-- 81185.24
108 | L34 | 2026-07-15 |  4200.610000 | running     0.000000  | computed f   <-- 85385.85
```

`24000.00 + 20195.38 + 16314.67 + 12356.34 = 72866.39`. **THE ORACLE IS SERVING ZERO FOR AN
ACCOUNT HOLDING 72,866.39.** [VERIFIED]

**And it is worse than T429 reported, in T429's favour: it is THREE rows on this account, not
one** — entries 96, 102 and 108 all serve `0.000000`, and the true balances are 72,866.39,
81,185.24 and 85,385.85. Tenant-wide it is the 18 rows created after job 9's last run. T429
captured entry 96 and reported entry 96; the finding generalises.

### `0.000000` is a decimal on the wire. What does the port do with it?

**Nothing, and it cannot, at four independent levels — I checked each:**

1. **No type can hold it.** `PostedEntry`/`PostedLeg` carry no balance member
   [VERIFIED: `impl.go:61-96`].
2. **No cell compares it.** `CellFields()` measures 14 cells from the real comparator; none is
   a balance. And if one appeared, the run refuses — driven at D3 below.
3. **No vector can cite a capture containing it.** `Admit` scans the cited artefact's BYTES for
   `organizationRunningBalance` / `officeRunningBalance` / `runningBalanceComputed` and refuses
   [VERIFIED: `admit.go:131-141` → `CaptureRuleReasons`]. The bar prints
   `cited artefacts scanned CLEAN 34 FORBIDDEN 0 UNREADABLE 0`, with UNREADABLE kept as a
   distinct outcome and never folded into CLEAN.
4. **No float parses it.** **`grep -rn "ParseFloat|strconv.Float"` over `nexus/internal/`
   non-test returns ZERO hits**, and the only occurrences of `float64` in the ledger package
   are inside comments forbidding it [VERIFIED]. Money is a digit-STRING parsed to
   `ledger.MinorUnits` (`int64`); `OracleAcceptance.ObservedAmountTexts` is never parsed,
   converted or compared numerically.

**So `0.000000` never becomes a number in Go at any point, including intermediate
calculation.** [CLEAN — the CLAUDE.md non-negotiable holds.]

---

## 5. THE ATTRIBUTION LIMIT — enumeration re-run, and T417 reconciled

**Re-run against `/Users/buv/fineract @ 426a23544` (clean), case-insensitive, over
`*.java` `*.sql` `*.xml` `*.kt`, INCLUDING tests:**

```
UPDATE acc_gl_journal_entry  →  EXACTLY TWO, both in one file:
  JournalEntryRunningBalanceUpdateServiceImpl.java:163
  JournalEntryRunningBalanceUpdateServiceImpl.java:211
INSERT INTO acc_gl_journal_entry  →  ONE: SavingsSchedularInterestPoster.java:165
DELETE FROM acc_gl_journal_entry  →  NONE
```

**The count is two. T429's enumeration reproduces exactly.** [VERIFIED]

I widened the search rather than repeat it: **7 non-test Java files reference the table at all**,
and I opened the ones T429 did not name. `JournalEntryAggregationJobReader` is a **`SELECT`**
[VERIFIED, read]. `GLAccountReadPlatformServiceImpl` and `JournalEntryReadPlatformServiceImpl`
are reads. `AccountGLJournalEntryAnnualSummary` is a different table. **No JPQL/HQL `UPDATE
JournalEntry` and no `@Modifying` repository on the entity exist** [VERIFIED]. `JournalEntry.java`
carries `@Entity` at `:38`, `@Table(name="acc_gl_journal_entry")` at `:40`, **exactly two
`@Setter`s at `:58` and `:78`, and NOT ONE reference to any balance column** [VERIFIED — grep
for `balance` in that file returns nothing]. **So the entity could not write the three exempt
columns even if a command tried.**

### **T417's `:211` and T429's `:211` ARE THE SAME STATEMENT. There is no conflict.**

T417's handoff says: *"**A second raw UPDATE that T409 did not name:** `:211`"* — the complaint
is against **T409**, not T429. **T429 names `:211` in three places**: its source-citation table
(*"the office-scoped write, `office_running_balance` alone | same | 211, batched at 217"*), the
declaration's `office_running_balance.written_by` field, and the G-22 gate block. I read the
source myself: `:211` is
`UPDATE acc_gl_journal_entry SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`,
batched at `:217` [VERIFIED]. **Three independent enumerations — T417's, T429's and mine —
agree: two UPDATEs, `:163` and `:211`, one service.** [RECONCILED, CLEAN]

**T417 adds one fact T429 omits and it strengthens T429's PROVENANCE call:** both statements
bind `last_modified_by` from `platformSecurityContext.authenticatedUser().getId()` — at `:178`
and `:214` [VERIFIED by me, read]. So the actor id is *whoever the job authenticated as*, a
runtime fact, which is a second reason it is provenance rather than a fact about the posting.

### The attribution itself, re-measured

```
91 modified rows | 1 distinct modifier | window [2026-08-28 16:01:00.033938 , .039824]
18 untouched rows, ids 96-113, created  [16:01:00.100207 , .117772]  -- AFTER job 9 finished
```
[VERIFIED: `out/R03-attribution-entry96.txt` §R03.2/§R03.4]

**T429's stated limit is real and correctly stated.** `job_run_history` records when a job ran,
not which rows it wrote; job 17's window also brackets the modifications; the separation rests
on the source enumeration. **T429 did not promote the interval into an identification, and it
should not.** [CLEAN — this is exactly the honesty the brief asked me to check for.]

**One reconciliation I could not make cleanly** — see F-6: I found **8** rows with
`reversed = true` and **8** non-null `reversal_id`, in **3** reversal transactions. The
handoff's phrase *"this tenant records 3 reversals and 91 modified rows"* compares transactions
against rows. All 8 reversed rows were later overwritten by job 9 (their
`last_modified_on_utc` all fall inside job 9's window), so the JPA reversal path leaves no
surviving timestamp evidence — which **strengthens** the attribution rather than weakening it.

---

## 6. ENFORCEMENT — REACHED, NOT P-45. Four arms driven.

**The chain is on the executed path and I traced every link myself:**

- `storeRootNonVectorFiles` names `oracle-derived-columns.json`
  [VERIFIED: `census.go:88-92`]; an unlisted, unloaded store-root `.json` refuses the store.
- **`LoadOracleDerivedRegistry` is called by name from `Run`**, beside `LoadPin` and
  `LoadCapabilityRegistry`, and a load or validation failure appends to `fatal` and returns
  `&Summary{Fatal: fatal}` **before any vector is graded**
  [VERIFIED: `loanschedule/conformance/grade.go:729-738`].
- `OracleDerivedLines()` is rendered unconditionally by `report.go:937`.

| drive | change | result |
|---|---|---|
| **D0** | none (control) | **EXIT 0**, `VERDICT: PASS` |
| **D1a** | `amount` → `ORACLE_DERIVED` via JSON | **EXIT 2**, 4 arms, ledger FATAL, `cells compared 0` |
| **D1b** | `amount` → `PROVENANCE` **+ Go pins moved to match** | **EXIT 2**, money-column guard fires **ALONE** |
| **D2** | **delete the declaration file** | **EXIT 2** — `LEDGER FATAL: oracle-derived column declaration: open …: no such file or directory` |
| **D3** | **add a running-balance cell to the comparator** | **EXIT 2**, 2 arms |
| **D4** | `description` GRADED_GAP→PROVENANCE + pins moved | **EXIT 0** — see F-3 |
| **D5** | same JSON edit, **pins untouched** | **EXIT 2**, both pins fire |
| **D0b** | tree restored | **EXIT 0** — control re-established after the drives |

**D2 — the deletion also proved the NAMED ABSENCE claim.** On that failing run the block still
printed [`out/t439-d2.txt` / `out/t439-d1a.txt:285-291`]:

```
    THE ORACLE-DERIVED COLUMN CARVE-OUT — where THIS PORT IS RIGHT NOT TO MATCH THE ORACLE.
      (NO ORACLE-DERIVED DECLARATION IS LOADED. That is NOT the same state as there being
      no carve-out, and it is the worse of the two: ...)
```

**D3 — I added `s.cmpStr(p+"organization_running_balance", "0", "0")` to `diffEntry`**, rebuilt,
and got **EXIT 2** with two independent arms [`out/t439-d3.txt`]:

```
THE COMPARATOR NOW EMITS CELL "legs[].organization_running_balance", WHICH THE DECLARATION
FORBIDS BECAUSE acc_gl_journal_entry.organization_running_balance IS ORACLE-DERIVED. Somebody
has started GRADING a column this program's non-negotiables say the port must NEVER WRITE ...
EXIT 2 -- this is NOT a pass

the comparator EMITS cell "legs[].organization_running_balance" and the declaration does not
classify it. A NEW GRADED CELL MUST BE CLASSIFIED BEFORE IT IS GRADED
```

**This is not P-45.** The guard runs on the automatic path, refuses before a verdict exists,
and both directions of the set-equality were exercised (D3 is the "a cell appeared" direction;
D1a's `declares 2 GRADED columns, PINNED 3` is the "a cell/column disappeared" direction).

---

## 7. WHAT T429 DISCLOSED AND DID NOT CLOSE — confirmed, and one item is WRONG

**The two pre-existing default-deny surfaces: CONFIRMED as T429 states them.**
`expect.legs[].excluded_fields` is closed to the single member `gl_account_type`
(`admit.go:112-120`) and `divergent_cells` is checked against `IsCellField`. **T429 is right
not to claim credit for them.** [CLEAN]

**The `contract.go` gofmt item: the FACT is right and the CHARACTERISATION IS WRONG.** See F-2.
T429 says `guard_gofmt`'s population is *"narrower than the module"* with an *"unstated limit"*,
and lists `[UNVERIFIED] What guard_gofmt's exact file population is`. **The limit is stated, in
the line the guard prints on every single run:**

```
conformance: gofmt guard — inspected 67 .go files under …/nexus
             (recursive, whole module; contract.go exempt, gate G-3)
```

It is **one file**, filtered by `LC_ALL=C grep -av "/contract/contract.go$"` on the guard's
**output** — deliberately on the output rather than by narrowing the root, *"so that widening
the root can never silently re-include it and narrowing it can never silently drop everything
else"* [VERIFIED: `conformance.sh:930-975`].

---

## FINDINGS

### MINOR

**F-1 — a measured cardinal in the declaration is FALSE: `ref_num` is not NULL on every row.**
The JSON says `"ref_num" … "NULL on every row in this tenant, so a cell would be a control
that cannot fail until a capture populates it."` **Measured `2026-08-29T00:41:34Z`: 72 NULL
and 37 NON-NULL — the 37 are the EMPTY STRING, `length = 0`** [VERIFIED: `out/R02-refnum-reversed.txt`
§R02.1/§R02.3, `out/R03-attribution-entry96.txt` §R03.1]. The *conclusion* survives (all values
are NULL-or-empty, so a cell still could not fail), but the *measurement* is wrong, and this
declaration's entire authority is that it is measured rather than reasoned. `ref_num` is
`GRADED_GAP`, so **nothing was moved out of grading by this error.** P-80 shape.
**Condition: correct the `why_no_cell_yet` text to `NULL on 72 of 109 rows and the empty string
on the remaining 37 — no row carries a value`, and re-check the other per-row cardinals in the
same file.** (I re-checked the other six myself and they all hold — see §1.)

**F-2 — T429's follow-up #6 proposes an action a ratified gate FORBIDS, and should be retracted
rather than carried.** It says *"Either widen `guard_gofmt`'s population or format the file."*
**G-3 (CLOSED, Option A) says: "no task may `gofmt -w` that path, and `gofmt -l` reporting
exactly that one file is the EXPECTED state and must not fail a UAT"** [VERIFIED:
`gates.md:915-943`]. Option B — applying the formatting as an "inert erratum" — was
**explicitly rejected**, because `contract.go` is the frozen DEC-1 artefact whose doc comments
*are* the specification and whose bytes are digest-pinned by `PIN.json`/`VerifyContractDigest`.
A later agent reading follow-up #6 without reading G-3 would rewrite a ratified artefact.
**Condition: close follow-up #6 as WONTFIX citing G-3 Option A, and delete the
`[UNVERIFIED] What guard_gofmt's exact file population is` line — the guard prints it.**

**F-3 — the four new pins are enforced ONLY inside Go; `.softhouse/conformance.sh` censuses
none of them, and the gap is exploitable for 2 of the 31 columns. DRIVEN.**
`grep -in "oracle-derived|graded-gap|ProvenanceColumnPin|GradedGapColumnPin"` over
`.softhouse/conformance.sh` returns **zero hits** [VERIFIED]. **D4:** moving `description` from
`GRADED_GAP` to `PROVENANCE` **passes at EXIT 0** once `ProvenanceColumnPin 7→8` and
`GradedGapColumnPin 18→17` are moved to match, and the printed block duly reads
`provenance 8  graded-gap 17` with `acc_gl_journal_entry.description` gone from the named list.

*Bounded, and not silent:* it is possible for **only `description` and `ref_num`** — the 2 of
31 columns that are `GRADED_GAP` without being in the protected 19; **D5** confirms a JSON-only
attempt is refused at EXIT 2 by both pins; and the printed block changes visibly. So T429's
claim *"widening the carve-out is a source edit a reviewer sees"* is **TRUE**. But every other
exemption population in this program is censused in the shell (T360's `DivergencePinCount`,
the ledger exemption census, the money-cell pin), and this one is not — so it is the only
carve-out whose population no *gate* reads. T429 disclosed this as follow-up #2 and named the
correct reason (T417 held the file this fire).
**Condition: promote follow-up #2 from a follow-up to a filed task — add
`oracle-derived columns`, `provenance`, `graded`, `graded-gap` to `conformance.sh`'s exemption
census now that T417's hold has ended.**

### LOW

**F-4 — the declaration has no check that the TABLE still has 31 columns.**
`column_count_observed: 31` is transcribed into the JSON and validated only against
`len(columns)`, which is itself 31. **Nothing compares the declaration to
`information_schema`.** I measured 31 today so the declaration is accurate — but a Fineract
schema migration adding a 32nd column would leave every count equal, every pin green, and
**one undeclared, ungraded column: precisely the state this file exists to remove.** This
limit is not in T429's `Unverified` list. It is LOW because closing it would make the bar
depend on a live database; **the right remedy is to DISCLOSE it** in the `Unverified` section
and in the JSON's `_note`, and to re-run the census whenever the Fineract pin moves.

**F-5 — `Admit`'s new capture-rule arm fails OPEN on a nil registry.**
`opts.OracleDerived.CaptureRuleReasons(...)` → `ScanCaptureRule` returns `nil` when `r == nil`,
and neither `Admit` nor `ledgerconf.Run` requires `opts.OracleDerived != nil`
[VERIFIED: `oraclederived.go:585-587`, `grade.go:604-607`]. **Not reachable today** — the load
is FATAL in `loanschedule.Run` before `ledgerconf.Run` is called, which is why D2 refuses
rather than passes vacuously. But the ledger package does not enforce its own precondition, so
a future second caller of `ledgerconf.Run` would silently lose the capture rule. A one-line
`if opts.OracleDerived == nil { fatal }` in `ledgerconf.Run` would close it.

**F-6 — "3 reversals" mixes transactions and rows inside one comparison.** The attribution
paragraph reads *"the JPA entity, whose two `@Setter`s are the reversal pair, against which
this tenant records 3 reversals and 91 modified rows."* **Measured: 3 reversal TRANSACTIONS,
8 rows with `reversed = true`, 8 non-null `reversal_id`** [VERIFIED: §R02.4/§R02.5]. Both
readings of "3 reversals" are defensible; comparing them against a ROW count in the same
sentence is not. The argument is unaffected — 8 ≪ 91 either way, and all 8 were subsequently
overwritten by job 9.

**F-7 — a one-line citation over-reach.** T429 cites the first `UPDATE` as
`JournalEntryRunningBalanceUpdateServiceImpl.java:163-165`. The SQL string literal is
**`:163-164`**; `:165` is the `for` loop [VERIFIED, read at the pin]. `:181` (batched),
`:211` and `:217` are all exact. Noise-level, but this program grades line citations.

---

## WHAT I CHECKED AND FOUND CLEAN — so silence is distinguishable from not looking

- **DEC-2 byte-identical**, same blob hash on both branches; only an ADD in `docs/adr/`.
- **All 31 columns re-measured from `information_schema`** and matched name-for-name.
- **The 3 ORACLE_DERIVED and the 7 PROVENANCE audited one at a time** against "could this carry
  money or ledger structure?" — including the two hard cases (`id`/leg ordering, and audit
  instants vs the three accounting dates). None should move.
- **The 19-column protected set is the right 19**, and its complement contains no money column.
- **The money-column guard driven RED with every counting arm silenced** (D1b) — the strongest
  form of the claim, and it holds.
- **Deletion, comparator-addition and named-absence all driven** (D2, D3).
- **Control re-established after the drives** (D0b, EXIT 0) — the tree was restored, not merely
  assumed restored.
- **No float in any Go money path**: zero `ParseFloat` in the module, no `float64` outside
  comments in `ledger/`.
- **Source enumeration re-run and widened** to all 7 referencing files, JPQL, `@Modifying`
  repositories and Liquibase; two UPDATEs, one INSERT, no DELETE.
- **T417 and T429's `:211` accounts reconciled** — same statement, no conflict.
- **Entry 96 re-observed from the live oracle**, HTTP 200, with the instant recorded; and the
  finding found to generalise to entries 102 and 108.
- **Zero mutations to the reference oracle.**
- **Bar green on BOTH T429's tree AND the merge result with today's `main`**, probe PRESENT ×1
  in both, `go build` and `go test` clean on the merge.

## MERGE SAFETY

**Safe to merge.** `git merge --no-edit main` → exit 0, **zero conflicts**; the merged tree
builds, tests green, and the bar returns EXIT 0 with every carve-out figure identical and
main's 16th wrong ledger implementation still dead. None of the three MINOR findings changes
a grading decision or moves a column out of the graded domain; all three are text or process
corrections that can land as follow-up tasks.

**This review did not re-decide G-22.** The I-5 correction and the proposed `§4.4a` amend a
ratified DEC-2 and remain the gate's to settle.
