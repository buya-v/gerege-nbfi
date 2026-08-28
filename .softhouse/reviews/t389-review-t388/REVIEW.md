# T389 — INDEPENDENT REVIEW OF T388 (`softhouse/T388-accrual-capture` @ `977e37af`)

**Reviewer:** T389, branch `softhouse/T389-review-t388`.
**Grant written:** `.softhouse/reviews/t389-review-t388/` only. Nothing else was written.
**Oracle:** reachable this fire — `fineract-fineract-1` (healthy, `:8443`), `fineract-db-1`
`postgres:18.3` (healthy, `:5432`), `actuator/health` = `{"status":"UP"}`, Fineract pinned at
`426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED by `git rev-parse` in `/Users/buv/fineract`].
**No entity was created, modified or deleted in the oracle by this review.** Every database
statement issued is a `SELECT`; every HTTP request issued is a `GET`. The recipes that would have
moved state were verified by read-back instead, and this review says exactly which (§3).

---

## VERDICT: **APPROVED WITH CONDITIONS**

The capture is sound. Its headline claim is true, its observations are genuine, its arithmetic is
clean, its recipes re-issue, and it did not redden the existing corpus. The conditions are one
**MAJOR** incompleteness in the blast-radius record and five **MINOR** citation/statement defects.
None of them impeaches the evidence; all of them would mislead the promotion task that consumes it,
which is precisely who reads this document next.

### THE P0, ANSWERED FIRST: **NO PROMOTED GL ACCOUNT MOVED.**

Established on **four independent axes**, none of them read from T388's notes
[`out/T389-P0-contamination.txt`, `out/T389-P0b.txt`]:

| axis | measurement | result |
|---|---|---|
| **id monotonicity** | `max(id)` over every row on a forbidden account = **75**; `min(id)` over T388's rows = **76** | strictly disjoint |
| **wall clock** | last write to any forbidden account `2026-08-28 07:25:25Z`; T388's first write `2026-08-28 11:40:25Z` | **4h 15m earlier**; rows at/after T388's first write = **0** |
| **account set** | distinct accounts touched by every entry `id > 75` = `{35,36,37,38,39,41,42,43}` | intersection with forbidden set **EMPTY** |
| **no deletion / no reversal** | id gaps in `1..95` are `{5,8,13,22}`, all `< 76`; all 6 reversed forbidden rows are ids 33–47 created `2026-08-22`, six days before the fire | T388 removed and reversed nothing |

Per-account counts today — `1→3, 2→3, 4→12, 6→1, 8→2, 10→1, 15→0, 16→21, 17→5, 18→0, 21→13, 22→0`
— **match T388's before/after table exactly**, including `gl 18 → 0` and `gl 22 → 0`, the pair the
`ledger.accrual.entry` argument rests on.

I note the context the brief supplied and did not re-discover as a defect: `oracle-state-baseline.sh`
is invoked by nothing that runs (`git grep -F` finds references only in its own directory's docs,
`reference-oracle.md`, handoffs, and T367's review drives), so the automated net was **not armed**.
That is T390 item 3 and is not charged to T388. It is why the four axes above are measured rather
than assumed.

---

## 1. The forbidden set — MY DERIVATION MATCHES T388'S EXACTLY

I derived it **independently and more broadly**, not starting from T388's list
[`T389-derive-forbidden-independent.py`, `out/T389-R01-independent-forbidden-set.txt`]. T388's rule
was a single one: *key name ends in `gl_account_id`*. Mine applies **five** rules, so a miss requires
all five to fail — including camelCase (`glAccountId`), any `*account*` key with an integer value,
any `*gl*` key with an integer value, and any value under a path containing `slot`/`unposted`. It
also scans a file T388 did not (below).

**Result: `{1, 2, 4, 6, 8, 10, 15, 16, 17, 18, 21, 22}` — identical to T388's.**
Rules R1–R4 each independently produce that exact set. **There is no thirteenth member.**

R5 (the deliberately over-broad slot/unposted rule) additionally surfaced `{7, 9, 28}`. I checked
these rather than reporting them: they are `slot_code` and `product_id` inside
`capabilities-ledger.json`'s `unposted_slots`, **not** GL account ids. Correctly excluded.

I separately checked a class **no id scan of any kind would see**: vectors that pin an account by
**code** rather than id. Eight standing-oracle codes are pinned (`10000, 10201, 10300, 10400, 20100,
40100, 40300, 99008`). T388 minted `T388-1000 … T388-5100`; **collisions = 0** [`out/T389-SLOT-decode.txt` §S-1],
and every pinned code still resolves to its pinned id with `manual_journal_entries_allowed` and
`disabled` unchanged. No pre-existing account was edited — the A2-26 hazard is genuinely avoided.

**T388's two claimed discoveries are real and I reproduce both:** `gl 22` is reachable only through
`capabilities-ledger.json`'s `unposted_slots`, and `gl 15` only through a `contra_gl_account_id` key.

### The checker is genuinely drivable red (P-45), re-driven not read

T388 states it red-drove its checker with `--check 16,41`. I **re-drove it**
[`T389-redrive-checker.sh`, `out/T389-R02-redrive-checker.txt`], against the real promoted store,
with T388's mutation **and four it did not use**:

| case | input | expected | actual |
|---|---|---|---|
| CONTROL — real set 35–47 (unmutated) | disjoint | exit 0 | **exit 0, `intersection: EMPTY`** |
| MUTATION A — T388's own red drive | `16,41` | exit 1 | **exit 1, `intersection: [16]`** |
| MUTATION B — gl 22 (unposted_slots only) | `22,35` | exit 1 | **exit 1, `[22]`** |
| MUTATION C — gl 15 (contra key only) | `15,36` | exit 1 | **exit 1, `[15]`** |
| MUTATION D — gl 18 (LDG-REFUSE-02) | `18,43` | exit 1 | **exit 1, `[18]`** |
| MUTATION E — whole real set + one forbidden | `35..47,17` | exit 1 | **exit 1, `[17]`** |
| ANTI-CALIB — an id in no set | `999` | exit 0 | **exit 0** |

7/7. The checker fails on intersecting input, passes on unmutated input, and does not fail
indiscriminately. It enforces something.

---

## 2. The observations ARE genuine slot accruals

Decoded independently through a fresh `acc_product_mapping` join, not from T388's SQL
[`out/T389-SLOT-decode.txt` §S-3, §S-6]:

**Exactly nine** entries arrive through a receivable slot — **78/81/83 (`L29`), 84/87/89 (`L30`),
90/93/95 (`L31`)** on gl **41/42/43**, slots **7/8/9**. All `DEBIT`, all `MNT`, all
`manual_entry = f`. Matches T388 leg for leg.

The T242 trap is avoided **structurally, not by luck**:

- every entry's `loan_transaction_id` resolves to `m_loan_transaction.transaction_type_enum = 10`
  (ACCRUAL) on loan 8, product 63, `accounting_type = 3`;
- `AccountingRuleType.java:32` — **`ACCRUAL_PERIODIC(3)`** [VERIFIED at the pinned sha];
- `AccountingConstants.java` — `AccrualAccountsForLoan` **7 = INTEREST_RECEIVABLE, 8 = FEES_RECEIVABLE,
  9 = PENALTIES_RECEIVABLE**, and `CashAccountsForLoan` has no 7/8/9 at all, so the enum choice is
  forced, not selected [VERIFIED at the pinned sha];
- product 63's mapping is a **bijection**: 13 mappings, 13 distinct accounts, 13 distinct slots — so
  `gl_account_id → financial_account_type` really is a function on this product;
- and I checked the sharper thing T388 asserted only implicitly: **none of accounts 35–47 appears on
  any other product at all**. There is no second slot for any of them to be confused with.

For contrast I confirmed the trap is live and real: **gl 16 is slot 9 (`PENALTIES_RECEIVABLE`) on
accrual product 28 and slot 1 (`FUND_SOURCE`) on ten cash products.** An enum-blind or
product-blind decode there would be wrong in both directions.

**Double entry holds in integer minor units**, re-derived in SQL with no float:
`L28 120000000=120000000`, `L29 2770000=2770000`, `L30 2389538=2389538`, `L31 2001467=2001467`,
difference **0** on all four. **Zero** T388 amounts carry a non-zero third decimal, so nothing is
sub-minor-unit.

### The `/runaccruals` = job 16 claim — **THE CORE HOLDS**, the citation does not

Verified against the pinned source. Both paths converge on the **same single-overload method**
`LoanAccrualsProcessingService.addPeriodicAccruals(LocalDate)`
(`LoanAccrualsProcessingServiceImpl.java:120-127`, whose own Javadoc says *"for batch job 'Add
Periodic Accrual Transactions' and add accruals api for Loan"*). `AddPeriodicAccrualEntriesTasklet.java:40-51`
calls it with `DateUtils.getBusinessLocalDate()`, verbatim as T388 quotes. Job id **16** is seeded in
source at `0002_initial_data.xml:821-838` with cron `0 2 0 1/1 * ? *`, wired
name → `JobName.ADD_PERIODIC_ACCRUAL_ENTRIES` → `AddPeriodicAccrualEntriesConfig.java:50` → that
tasklet. **The observations are of genuine periodic accrual, and T388's refusal to call this evidence
about the scheduler is correct.** See findings **m-1**, **m-2**, **m-3** for what is wrong around it.

---

## 3. Recipes — RE-ISSUED, and the split is stated

T388 recorded **27** exchanges: **7 GETs** and **20 state-moving POSTs**.

**Re-issued (7 GETs)** [`T389-reissue-recipes.sh`, `out/T389-R03-reissue.txt`, bodies under
`out/reissue/`]. Six returned **byte-identical** bodies to the recorded `.json` (key-order-normalised
only; no value normalisation): `A03`/`A04`/`A05` (the contract-boundary `GET
/journalentries?transactionId=L29|L30|L31`), `A06` (`/loanproducts/63`), `A07` (`/loans/8?associations=all`),
`P01` (`/businessdate`). This is strong evidence the artefacts are genuine oracle output.

**The seventh differs, and must:** `P08` is `GET /loans/8` captured *before* the accrual. The accrual
is permanent, so that body is unreproducible. My script declares this in advance rather than
excusing it afterwards, and asserts the correct control — **today's response matches `A07`**, the
same GET taken after accrual, which it does.

**NOT re-issued (20 POSTs)** — re-issuing any would move the oracle a second time and corrupt the
evidence this review exists to check. Verified by **read-back against the live database** instead,
which is the stronger test since it reads what was persisted rather than what was echoed: all 13 GL
accounts, product 63, client 3, loan 8, loan transactions 28–31 and journal entries 76–95 are present
with exactly the recorded ids and values.

**The HTTP 400 is recorded honestly, not hidden.** `out/T388-P04-loan-application.status` = `400`;
the `.json` carries the real oracle error (`charges[1][amount]` / `charges[2][amount]` mandatory);
the `.http` names the key that was burned. The database agrees independently:
`m_portfolio_command_source` **375** = `T388-P04-loan-application`, `status = 5` (ERROR), and the
successful retry is **376** under a **different** key `T388-P05-loan-application`. Correct handling of
a burned key.

**Integrity pins verified, with a red drive** [`T389-verify-manifest.sh`, `out/T389-R04-manifest-integrity.txt`]:
`MANIFEST.sha256` verifies **193/193 OK, 0 FAILED**; all **20** `.req.sha256` and **7** `.sql.sha256`
wire-byte pins match; coverage is complete (193 files in tree, 193 named). Appending **one byte** to
`out/T388-A01-runaccruals.req` is **detected as FAILED**, and the restored file verifies OK again —
so the manifest is a real pin, not decoration.

---

## 4. Money and the non-negotiables — CLEAN

- **No float in any money path.** **Zero** float-shaped tokens in `req/` bodies or in any `out/*.req`
  wire-byte artefact — every numeric literal T388 sent is an integer, including the `24` %/yr rate
  chosen to avoid one. The only `json.load` calls in the rig are in the forbidden-set deriver, which
  reads **account ids** and never touches an amount. `awk` appears twice, summing `git grep` **match
  counts**, not money. The oracle's own instrument independently reports **"0 floating-point columns
  on the ledger tables"** [`out/T389-R05-oracle-state-baseline.txt`].
- **`Idempotency-Key` on every money-movement POST — verified in the database, not the notes.** All
  20 rows **360–379** carry a task-naming `T388-*` key; **none** is a minted UUID. Row 379 is
  `EXECUTE / PERIODICACCRUALACCOUNTING`, so even the accrual trigger went through the command bus
  with a key.
- **Three name fields.** `ovog Боржигин → lastname`, `patronymic Батбаярын → middlename`, `given name
  Ганболд → firstname`, mapped **explicitly** in the record (§1) because Fineract's schema cannot be
  changed from a capture task. No `first_name`/`last_name` anywhere.
- **National ID structurally valid.** `УБ90051423` — 10 characters, `УБ` = 2 Cyrillic, `90051423` = 8
  digits; month field `05`, so the `+20` rule for births from 2000 onward correctly does not apply.
  T388 states validation was **structural only** (check digit unpublished). Correct.
- **MNT.** `m_currency` / `m_organisation_currency` both carry `decimal_places = 2`; all 20 T388 legs
  are `MNT`. Ledger currency mix unchanged in kind (MNT 89, USD 2).
- **PostgreSQL only.** No `ojdbc`, `oracle.jdbc`, MySQL, MariaDB, port 1521/3306 driver or dialect
  anywhere in the diff. The three apparent grep hits are a sha256 hex containing `1521`, and quoted
  prose in transcripts about Fineract's own MySQL-only SQL — none is an introduction. Engine
  confirmed live: **PostgreSQL 18.3**.
- **Deposit-taking.** No savings/deposit behaviour touched; a loan product and a loan were created.
  No string calls anything insured, protected or guaranteed. The record states the NBFI position and
  cites Art. 12.1.3 / 12.1.4.
- **Grant respected.** `git diff --name-status main...977e37af` = **195 files, every one `A`**. T388
  modified zero existing files, so no other worker's held path was touched.

---

## 5. The state-move record — COMPLETE IN SHAPE, INCOMPLETE IN POPULATION

`ORACLE-STATE-MOVED-BY-T388.md` (374 lines) is a **strict superset** of T352's shape (created
entities with ids / transactions and legs / P0 check / attribution / blast radius split into
executable + doctrine + not-affected / re-derivation), which is the right response to T359's C-2. It
declares its own undischarged obligation rather than burying it, and I confirmed that obligation is
**real**: `bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh` **exits
1** and stars all four transactions and all 20 command-source rows as `UNATTRIBUTED`
[`out/T389-R05-oracle-state-baseline.txt`]. The discharge is staged at `out/PROBES-APPEND-T388.tsv`.

**T388's reported casualties are all confirmed by my own reading:**

- `t327/throwaway/capture.sh:82` and `down.sh:54` do pin `m_loan` by string equality against a
  baseline file, refusing / setting `rc=1` on mismatch — and `m_loan` **is** in t327's counter list
  (`"m_loan|SELECT count(*)::text FROM m_loan"`), now 7 → **8**.
- **`t305` does NOT pin `m_loan`** — `grep` across all three of its scripts returns **rc 1, zero
  matches**. T388's claim, which it said it verified by reading, holds.
- `capabilities-ledger.json`'s four sentences, `CASUALTIES.md:40,44`, `gates.md:4519-4520`,
  `t371-t367-conditions/README.md:15-16`, `reference-oracle.md:912-913` — all confirmed, including
  the distinction T388 insists on: *"NOT ONE ENTRY IN THIS **CORPUS**"* is **still true**, because
  T388 promoted nothing. That distinction is correct and must survive the rewrite.

### **M-1 (MAJOR) — a casualty T388 missed, in a ratified DEC-n**

`docs/adr/DEC-2-gl-accounting-adapter.md:1061` (invariant **I-5**), present tense:

> *"it is a snapshot taken when the table held **6** rows and it now holds **60**"*
> *"**60 of the 60 rows in `acc_gl_journal_entry` carry `last_modified_on_utc > created_on_utc`**"*

and the same claim restated at **`:3004`**.

**Live, measured by me:**
```
$ docker exec -i fineract-db-1 psql -U root -d fineract_gerege -Atc \
  "select count(*) filter (where last_modified_on_utc > created_on_utc)||' of '||count(*) from acc_gl_journal_entry;"
60 of 91
```
*Control:* the same query at T388's declared before-state would have read `60 of 71`; the pin was
already false. **T388 moved it 75 → 91.**

Why this is MAJOR rather than trivial: the **universality** is what the I-5 argument *uses* — the
column is dismissed as discriminating nothing *because every row carries it*. It is now 60 of 91, so
the stated premise is false. This sits in a **ratified** DEC-n, which an agent may not amend without
raising a gate.

**In fairness to T388, three mitigations, stated because the finding is otherwise unfair:**
1. T388 **declared its boundary honestly** — *"I did NOT search outside `.softhouse/`"*. This is not
   a silent omission of the T352 kind; T352's C-2 was worse because it *named a casualty path that
   does not exist* while missing real ones.
2. **T388 did not break it first.** T352/T359 took it 60 → 75. T388 deepened an already-false pin.
3. **No prior casualty task ever swept `docs/` either** — T363, T371 and T388 all used a
   `.softhouse/`-only population, which is why three successive tasks missed it.

The finding is against the **record's completeness**, which is its whole purpose. The repair is to
widen the sweep population to the whole repository (8,363 tracked files, of which 79 lie outside
`.softhouse/`), not merely to fix two lines.

### Sweep scope actually covered by this review

Population: `git ls-files` = **8,363** tracked files. Archive predicate adopted verbatim from
`t363-oracle-baseline/instruments/casualty-sweep.sh:85` as T371 amended it → 6,290 archived, **2,073
LIVE**. Selectors used `git grep -nE`/`-F` with **no `\b`** (T232) and **exit status read** so an
unrun selector cannot print as a measured zero (T367 F2). Every repo-wide selector returned rc 0; the
only two measured zeros were rc **1** (engine ran, matched nothing): no promoted vector names
`L28`–`L31`, and nothing anywhere claims product 63 free or unused. **No selector returned rc ≥ 2.**

Beyond M-1, additional stale pins found and classified honestly — **none charged to T388 as a miss**,
since all are either pre-broken, correct-as-history, or postdate T388's fork point:

| file:line | pin | live | classification |
|---|---|---|---|
| `.softhouse/RESUME.md:77` | *"not one journal entry in this tenant has ever arrived through a RECEIVABLE slot"* | **9 have** | **FALSE, and LIVE.** But `git show softhouse/T388-accrual-capture:.softhouse/RESUME.md` shows this string **does not exist** at T388's tip; `git log -S` places it at `5626b71b`, which **postdates** T388's merge-base `dbf7d312`. **The driver wrote this after dispatching T388.** Not T388's defect — but it is false today and `/softhouse-program` reads it. |
| `capture/actualactual/src/pathb-capture.sh:52,122` | `m_loan = 0`, string equality, `exit 1` | 8 | executable, **fails** — broken long before T388 |
| `pathb-capture.sh:124`, `charges/bin/t48-capture.sh:154` | `m_product_loan = 16` | 34 | same; T388 moved 33→34 |
| `capture/t327-.../README.md:153` | `acc_gl_account = 23` | 36 | past-tense history; note `acc_gl_account` is a counter class **absent from every casualty list to date** |
| `.softhouse/observations/20260827-...md:26`, `actualactual/PROVENANCE.md:91`, `REPRODUCE.md:45`, `leapboundary/ATTESTATION.md:49`, `PROVENANCE.md:110` | `m_loan 7/0`, `m_product_loan 16/21`, `m_client 2` | 8 / 34 / **3** | dated attestations, correct as history; `m_client 2→3` is T388's |

**Verified unaffected, checked rather than assumed:** no GL-account **balance** is pinned anywhere;
`.softhouse/conformance.sh` and `.softhouse/guards/` contain no `psql`/`docker exec`, so **the bar
reads no database** and no *printed count* can move — only hand-written prose; `go build`/`go test`
are untouched because T388 modified no existing file.

---

## 6. FINDINGS

### MAJOR

**M-1 — blast-radius record incomplete: `docs/` was never swept, and a ratified DEC-n pin is now
false.** `docs/adr/DEC-2-gl-accounting-adapter.md:1061` and `:3004`. Reproduction and control above.

### MINOR

**m-1 — the `/runaccruals` citation is wrong at its first hop.** T388 writes
`AccrualAccountingApiResource.java:62 → AccrualAccountingWritePlatformServiceImpl.executeLoansPeriodicAccrual`.
Line **62** builds a `CommandWrapper`; the dispatch is line **64**,
`commandsSourceWritePlatformService.logCommandSource(commandRequest)`, and the real chain is
`:64 → PortfolioCommandSourceWritePlatformServiceImpl.logCommandSource:57-82 →
SynchronousCommandProcessingService.executeCommandAttempt:111-151 →
CommandSourceService.processCommandAndSaveResult:116-124 →
ExecutePeriodicAccrualCommandHandler.processCommand:37-41 →
AccrualAccountingWritePlatformServiceImpl.java:45-49`. The conclusion survives intact. *Ironically the
command-bus hop T388 omitted is exactly what produced command-source row 379 and its `Idempotency-Key`,
which T388 itself relies on elsewhere.*

**m-2 — "the ONLY difference is where `tillDate` comes from" is overstated.** Inside
`addPeriodicAccruals` the two paths are identical. Before it they are not: the API path additionally
carries an `EXECUTE_PERIODICACCRUALACCOUNTING` permission check, idempotency-key resolution, a
persisted `m_portfolio_command_source` row, a maker-checker gate
(`CommandSourceService.java:130-141`; inert by seed default), and a `tillDate <= businessDate`
validator (`AccrualAccountingDataValidator.java:54-71`); the job path instead sets
`ActionContext.DEFAULT` explicitly (`JobStarter.java:94-96`), which matters because under a COB
action context `DateUtils.getBusinessLocalDate()` returns the **COB** date. **This error runs in
T388's favour** — its operative conclusion (*"NOT evidence about the scheduler"*) is not merely
correct but *more* correct than the argument it gave. Two things I checked that are **not**
divergences: `validateDateBefore` **permits equality**, so the API can reproduce the job's exact
input; and neither path is COB-gated (`/runaccruals` does not match `LOAN_PATH_PATTERN`).

**m-3 — the "periods 1–3 accrued, 4–6 did not" attribution is to the wrong query.**
`FIND_LOANS_FOR_PERIODIC_ACCRUAL` (`LoanRepository.java:117-118`) is an `EXISTS` subquery that selects
**which loans to process**, not which periods accrue. The per-period cutoff is
`LoanAccrualsProcessingServiceImpl.getInstallmentsToAccrue:471-473` via
`LoanRepaymentScheduleProcessingWrapper.isBeforePeriod:260-263`. The strict `<` is real for non-first
periods, so **the observed behaviour T388 describes is right** — but three traps a Go port would
inherit are hidden by the mis-citation: the **first** installment is `<=`, not `<`; the whole date
test is bypassed when `charge-accrual-date = submitted-date`; and progressive schedules with
`isInterestRecognitionOnDisbursementDate()` shift `tillDate` by **+1 day**
(`LoanAccrualsProcessingServiceImpl.java:454-457`). T388 flags this observation as raw material for a
promotion task, which is why it matters.

**m-4 — the `run-all.sh` caveat is inaccurate for `t327`.** T388 writes *"step 0 of **both**
`run-all.sh` scripts does `rm -rf "$OUT"` and regenerates `STANDING-baseline.txt` … through the
supported entry point both rigs are UNAFFECTED."* True for t305 (unconditional `rm -rf`). **False for
t327:** `run-all.sh:38-46` **refuses** on a non-empty `out/` unless `T327_FORCE_OVERWRITE=1`, and
`out/` is committed with **89** files, so the supported entry point **exits 1 at :43 before step 0
ever runs**. The safety conclusion survives — t327 cannot fire against a stale baseline either way —
but by **refusal**, not regeneration. Verified by reading `run-all.sh:34-52` and
`git ls-files …/throwaway/out | wc -l`.

**m-5 — the gl-16 restatement carries stale numbers.** T388 writes *"gl 16 is `PENALTIES_RECEIVABLE`
on product 28 **and** `FUND_SOURCE` on five cash products, and every one of its **sixteen** rows
arrives through the latter."* Live: **ten** cash products (22, 23, 27, 46, 54–58, 60), **21** rows,
and the mechanism split is `manual_entry=f` slot 1 → **10 rows**; `manual_entry=t`, **no slot at all**
→ **11 rows**. So "every one of its sixteen rows arrives through the latter" is false on count *and*
on mechanism. The T242 lesson it illustrates is untouched — but a document that correctly lectures
about counts typed into prose going stale should not itself carry three.

### TRIVIAL

**t-1** — *"all **67** files in `.softhouse/vectors/`"*. There are **68** `.json`;
`_selftest/SELFTEST-01-two-period-zero-rate.json` is not scanned. I verified this is **harmless** —
that file carries no `*account*` or `*gl*` key of any kind — but the deriver should state the
subtree it walks rather than a count that can drift.

**t-2** — *"`MANIFEST.sha256` digests all **191** files"*. It digests **193**.

### NOT charged to T388

- `oracle-state-baseline.sh` is unwired — **T390 item 3**, per the brief.
- The `PROBES.tsv` obligation is undischarged — **deliberate and declared**; the file is outside
  T388's grant and its directory was concurrently held by T381. Blast radius is nil in practice
  because nothing that runs invokes the instrument.
- `.softhouse/RESUME.md:77` is false today, but the string postdates T388's fork point. **The driver
  wrote it after dispatching T388.**

---

## 7. THE BAR — clean tree, `bash`, both targets

`git status --porcelain` was **empty** before each transcript was captured, and each ran with **`bash`,
never `sh`**. Probe-line presence was tested **before** its value was read (**P-84**).

| target | commit | exit | probe line | ledger parity | oracle-refusal | inadmissible | ledger cells / money | loanschedule | dead-path |
|---|---|---|---|---|---|---|---|---|---|
| **T388 branch** | `977e37af` (detached scratch worktree) | **0** | **PRINTED**, `probe = up` | **7 / 0** | **6 / 0** | **0** | **142 / 39** | **46 / 0, 7,884** | **109** |
| **MERGE RESULT** | `f7b6c1a8` (current `main`) + `977e37af` = `9dd4ad33` | **0** | **PRINTED**, `probe = up` | **7 / 0** | **6 / 0** | **0** | **142 / 39** | **46 / 0, 7,884** | **109** |

The merge is conflict-free and purely additive. **Every required figure is unmoved on both.** T388
did not redden the existing corpus.

Transcripts: `out/T389-BAR-on-T388-branch.txt`, `out/T389-BAR-on-MERGE-RESULT.txt`.

**The T370/T361 trap is closed positively, not merely asserted.** T388's own recorded transcript
reports `T316-DEADPATH-CENSUS: corpus=1356` and `frontier 11, pinned at 11` — **identical** to my run
on the fully-committed tree. That census walks `git ls-files`, so had T388's ~195 files been untracked
when it ran the bar, its corpus count would have differed from mine. It does not. And the residual
case that T388 could not cover — its own bar transcript is not covered by the run that produced it —
is closed by **my** run at `977e37af`, which includes every file and still exits 0.

---

## 8. CONDITIONS

None blocks the capture's evidentiary value; all are for the promotion task that consumes it.

1. **Widen the casualty-sweep population to the whole repository** and repair
   `docs/adr/DEC-2-gl-accounting-adapter.md:1061,3004`. DEC-2 is **ratified**, so amending it is a
   gate, not an edit — raise it. *(M-1)*
2. **Correct the four source citations** (m-1, m-2, m-3) before any task builds an accrual vector on
   them. m-3 in particular hides three real traps for a Go port.
3. **Correct the `t327` `run-all.sh` mechanism statement** (m-4) and refresh the gl-16 numbers (m-5).
4. **Discharge the `PROBES.tsv` obligation** from the staged `out/PROBES-APPEND-T388.tsv`.
5. **Repair `.softhouse/RESUME.md:77`** — false today, driver-authored, and read by
   `/softhouse-program` on every resume.
6. When rewriting `capabilities-ledger.json`, **preserve the sentence that is still true**: *"NOT ONE
   ENTRY IN THIS **CORPUS**"*. The corpus is the promoted store, and T388 promoted nothing.

---

## 9. ARTEFACTS

| file | what it is |
|---|---|
| `T389-derive-forbidden-independent.py` | independent 5-rule forbidden-set derivation, broader than T388's |
| `T389-redrive-checker.sh` | re-drive of T388's checker: 5 mutations + control + anti-calibration |
| `T389-reissue-recipes.sh` | re-issue of the 7 read-only recipes, with the declared expected difference |
| `T389-verify-manifest.sh` | manifest / wire-byte / SQL pin verification **with a byte-mutation red drive** |
| `sql/t389-p0-contamination.sql`, `sql/t389-p0b.sql`, `sql/t389-slot-decode.sql` | the SELECT-only queries, exact bytes executed |
| `out/T389-R01-independent-forbidden-set.txt` | the independent derivation |
| `out/T389-R02-redrive-checker.txt` | 7/7 checker cases |
| `out/T389-R03-reissue.txt` + `out/reissue/` | re-issue transcript and today's response bodies |
| `out/T389-R04-manifest-integrity.txt` | 193/193 OK, red drive detected |
| `out/T389-R05-oracle-state-baseline.txt` | the instrument at exit 1, confirming the declared obligation |
| `out/T389-P0-contamination.txt`, `out/T389-P0b.txt`, `out/T389-SLOT-decode.txt` | the P0 and slot-decode measurements |
| `out/T389-BAR-on-T388-branch.txt`, `out/T389-BAR-on-MERGE-RESULT.txt` | the two bar transcripts |
