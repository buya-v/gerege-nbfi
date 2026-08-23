# T305 — CAN THE OPENING-BALANCE ACCEPTING-SIDE CAPTURE BE TAKEN SAFELY?

**ANSWER: NO. NOT ON THIS RIG, NOT TODAY, AND NOT BY ANY CHEAP VARIATION OF IT.**
Measured against both registered tenants and against the pinned source, not argued.

**NOTHING WAS FIRED AT THE REFERENCE ORACLE THAT WRITES.** Every observation below is a
read-only `SELECT`. There is no `req/` directory in this rig and there is no POST script —
deliberately, and §6 says why. **None of T287's four probes was fired**; its expiry guard
was run first, exits **1**, and its output is quoted in §7.

---

## 1. What the question actually is

T296 mutated the **port** in four arms and re-graded the whole ledger corpus
[`.softhouse/reviews/T296/REVIEW.md` §4]:

| arm | `GoPoster` STEP 1.5 predicate | result |
|---|---|---|
| BASE | `req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0` | PASS |
| **E** | the rule moved BELOW the balance check | **DIES** |
| **A** | `req.Command == "defineOpeningBalance"` alone — the id list never read | **SURVIVES** |
| **B** | `len(req.PostedNonContraTransactionIDs) > 0` alone — the command never read | **SURVIVES** |

Arm E vindicates T294's headline precedence claim and is not in question. **Arm A is the
hole.** A port that refuses *every* opening balance — including on an empty ledger, where
the oracle **accepts** — is green on the entire corpus. That is the `headerRefusingPoster`
class this store already names and already kills elsewhere: `LDG-04` exists precisely
because the reasonable-looking port **refuses** a HEADER account, and **diverging from the
oracle by refusing is still diverging.**

Two consequences, both stated because both are load-bearing:

1. **`posted_non_contra_transaction_ids` is INERT FOR GRADING.** It was the centrepiece of
   T294's non-vacuity argument — *"this port reads a length rather than a boolean somebody
   derived for it"* — and arms A **and** B falsify it in both directions. Lifting the
   precondition into the vector made it **auditable**, which was T289's point and remains
   worth having; it did not make it **graded**.
2. **NO ADDITIONAL REFUSAL VECTOR CAN CLOSE THIS.** Every refusal capture in this corpus
   *agrees* with arm A. The closer is an **accepting-side** observation and nothing else.

The accepting side is the fall-through at
`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:810-816`
[VERIFIED: pinned checkout `426a23544`]:

```java
private void validateJournalEntriesArePostedBefore(final Long contraId) {
    final List<String> transactionIds = this.glJournalEntryRepository.findNonContraTransactionIds(contraId);
    if (!CollectionUtils.isEmpty(transactionIds)) {
        throw new GeneralPlatformDomainRuleException("error.msg.journalentry.defining.openingbalance.not.allowed", ...);
    }
}
```

Empty ⇒ no throw ⇒ execution reaches the writes at `:742`/`:745`.

---

## 2. Neither registered tenant can carry it — MEASURED, both of them

`bash guard-accepting-capture.sh` → **exit 1**, and it prints the measurement rather than a
conclusion [`out/GATE-verdict.txt`]. Five conditions, per tenant:

| condition | source of the requirement | `gerege` | `default` |
|---|---|---|---|
| **C1** `rounding-mode` = 4 (HALF_UP) | CLAUDE.md, ratified 18 Aug 2026 | **4 — ok** | **6 = HALF_EVEN — REFUSE** |
| **C2** timezone ∈ {Asia/Ulaanbaatar, Asia/Hovd} | CLAUDE.md, "two time zones, no DST" | **Asia/Ulaanbaatar — ok** | **Asia/Kolkata (+05:30) — REFUSE** |
| **C3** `findNonContraTransactionIds` EMPTY | `:812`, the accepting side | **26 ids — REFUSE** | **0 — ok** |
| **C4** type-300 → an EQUITY account | `:708`, and `:764-769` | **GL 15, enum 3 — ok** | **UNMAPPED — REFUSE** |
| **C5** a disposability attestation | §6; no measurement can supply it | **absent — REFUSE** | **absent — REFUSE** |

[VERIFIED: `out/M-01-gerege-accepting-precondition.txt`, `out/M-02-default-accepting-precondition.txt`,
`out/M-05-default-residue-class.txt`, and the live `c_configuration` reads quoted in §3.]

**The two tenants fail on DISJOINT conditions, and that is the shape of the whole finding.**
The tenant that is production-representative has a ledger; the tenant with an empty ledger
is not production-representative. There is no third tenant.

### C1 and C2 are not fastidiousness — CLAUDE.md decides them

- `gerege` `c_configuration.rounding-mode = 4`; `default` `= 6`. `java.math.RoundingMode`
  ordinals are `HALF_UP = 4`, `HALF_EVEN = 6`, and CLAUDE.md ratifies `HALF_UP` for MNT and
  names 4 explicitly. CLAUDE.md's own consequence rule for captures taken at a non-ratified
  arithmetic setting is that they are **"discrimination probes, not parity vectors"**. A
  capture on `default` would land in that category **by the project's own rule**, not by my
  preference.
- `default` is `Asia/Kolkata`. CLAUDE.md permits exactly `Asia/Ulaanbaatar` and `Asia/Hovd`.
  `.softhouse/reference-oracle.md` already flags this tenant in those terms and records its
  legitimate role as the **wrong-offset / HALF_EVEN negative control**.

**So the only tenant on which `:812` would fall through is the one the corpus keeps AS a
negative control**, and spending it would consume the control to buy a vector the project's
own rules would refuse to call a parity vector. [UNVERIFIED: whether any *existing* vector
would break if `default`'s accounting state changed — I did not audit the corpus for that,
because C1/C2 already settle the question and the audit would not change the answer.]

### C4 is a second, independent blocker on `default`

`default` has **zero GL accounts** and **no type-300 mapping**. `:708`
`findByFinancialActivityTypeWithNotFoundDetection(300)` therefore throws **first**, so a
`defineOpeningBalance` POST at `default` right now returns a *different refusal*, not an
accept. Reaching the accepting side there needs a **setup campaign** — create an EQUITY
account, create the target accounts, create the financial-activity mapping — and §6 shows
that campaign becomes un-teardownable the moment it succeeds.

---

## 3. The POST is IRREVERSIBLE wherever it is taken — from source, three ways

**(a) A posted journal entry has no delete path in Fineract at all.**
`JournalEntriesApiResource.java` exposes `@GET` and `@POST` only — `@GET` at `:100`, `:169`,
`:246`, `:262`, `:281`; `@POST` at `:192`, `:222`, `:291`; **no `@DELETE`**. Widening the
search: `grep -rn "@DELETE" fineract-provider/src/main/java/org/apache/fineract/accounting/`
matches **nothing**. The only undo is `POST /journalentries/{transactionId}?command=reverse`,
which **appends** reversing entries — which is CLAUDE.md's append-only ledger working
correctly, and is exactly why it is not a teardown.

**(b) An accepted opening balance posts TWO entries per leg, not one.**
`saveAllDebitOrCreditOpeningBalanceEntries` (`:759-797`) calls `helper.persistJournalEntry`
**twice inside the per-leg loop** — the leg's own entry at `:791` and its contra entry at
`:796`. A two-leg opening balance therefore posts **four** journal entries. [VERIFIED:
source read; **[UNVERIFIED]** as an observation — no such POST was fired by this task, by
anyone this fire, and the count is a source reading, not a measurement.]

**(c) The setup becomes UNDELETABLE BY THE CAPTURE'S OWN SUCCESS.**
`GLAccountWritePlatformServiceJpaRepositoryImpl.deleteGLAccount` (`:191-212`) refuses with
`GlAccountInvalidDeleteReason.TRANSACTIONS_LOGGED` if any journal entry references the
account. So every GL account the capture creates in order to reach the accepting side is
deletable **right up until the capture works**, and permanently undeletable afterwards.

**And the capture destroys its own precondition.** The entries it posts are precisely what
makes `findNonContraTransactionIds` non-empty. After a successful accepting capture, that
tenant can never yield another one.

> **P-92**, verbatim: *"a probe whose safety comes from an EXTERNAL PRECONDITION rather than
> from its own content is a loaded weapon, and the danger is highest immediately after the
> capture SUCCEEDS — because taking the observation is often what removes the precondition.
> A refusal capture must carry a fail-closed fence that re-checks the precondition at fire
> time, never a comment asserting the refusal."*

**The accepting capture is the pure form of that shape, and it is worse than the refusals
P-92 was written about**, because for a refusal probe there is a **content** fence — T294's
body was unbalanced by one minor unit and could not post whatever the tenant looked like.
**No content fence exists for an accepting probe.** A body that cannot post is not an
accept. That is why `guard-accepting-capture.sh` gates on the **tenant** and not on the body.

---

## 4. A fresh tenant is not the cheap escape it looks like

**There is no runtime tenant-creation path in this build.** `grep -rn "TenantsApiResource"
--include="*.java"` over the pinned checkout matches **nothing**; the only file whose name
contains both `Tenant` and `ApiResource` is `TenantOidcConfigApiResource.java`, which serves
OIDC config. Tenant onboarding is a **startup** path: `TenantDatabaseUpgradeService`
implements `InitializingBean` and does its work in `afterPropertiesSet()` —
`upgradeTenantStore()` then `upgradeIndividualTenants()`, which iterates
`tenantDetailsService.findAllTenants()` and runs liquibase per tenant. Nothing re-enters it
while the process is live, and `JdbcTenantDetailsService.loadTenantById` is `@Cacheable`.

So creating a tenant means, in order:

1. **`CREATE DATABASE` by hand** — a *server-level* mutation, not a tenant-level one. The
   existing tenant databases are 40–42 MB, 281 tables each.
2. **Hand-written rows in the SHARED `fineract_tenants` registry** — the same registry that
   carries `gerege`'s own registration, across `tenants` (unique constraint on `identifier`,
   two FKs into `tenant_server_connections`) and `tenant_server_connections`.
3. **A RESTART OF THE REFERENCE ORACLE**, so liquibase migrates the new database. A tenant
   row added without a restart resolves to an empty schema and every query against it fails.

[VERIFIED: `out/M-04-tenant-store-cost.txt` — 6 registry tables, 22 tenant-store changelog
rows, database sizes; and the source reads above.]

**Step 3 is the disqualifier, and it is not a data-safety argument.** Restarting the oracle
makes it unreachable for every concurrently running worker, and this program's own rule
(`.softhouse/reference-oracle.md`) is that an unreachable oracle is `EXIT 2`, *"which is not
a PASS and never becomes one"*. A capture task that takes the whole rig down mid-fire has
mutated the **program**, not just the database. **Teardown residue, for completeness:**
`tenants_id_seq` and `tenant_server_connections_id_seq` both stand at 2 and would advance
permanently — the same class of trace as T287's `acc_gl_closure_id_seq.is_called = t`, which
this rig re-measured and confirms is still `t` [`out/M-03-gerege-residue-class.txt`].

**Not evaluated, and named rather than glossed:** whether a `liquibase-only`-profile process
could migrate a new tenant database *without* restarting the main app. It might; the
`FineractProfiles.LIQUIBASE_ONLY` branch exists in `afterPropertiesSet`. **[UNVERIFIED]** — I
did not test it, because steps 1 and 2 (a hand-written row in the registry that also carries
`gerege`) remain regardless, and because C1–C5 would still have to be satisfied on the result.
It is recorded as the one avenue a future task could reopen, not as a route I checked and rejected.

---

## 5. The residue class, measured on the tenant that already carries it

The brief predicted "the same class of trace" as T287. Confirmed, and characterised on both
layers, because T289 F-T289-3 found T287's disclosure read as *"a counter moved"* when the
truth was *"the oracle's public API now tells this story"*.

**`gerege` today** [`out/M-03-gerege-residue-class.txt`]:

```
acc_gl_journal_entry_id_seq        64 | t
acc_gl_closure_id_seq               1 | t     <- T287's permanent trace, still t
m_portfolio_command_source_id_seq 352 | t
352 audit rows, 30 of them on accounting entities (GLACCOUNT / FINANCIALACTIVITYACCOUNT / JOURNALENTRY)
```

**`default` today** [`out/M-05-default-residue-class.txt`], and this is the part worth
reading twice:

```
acc_gl_journal_entry_id_seq         1 | f     <- NEVER ADVANCED
acc_gl_closure_id_seq               1 | f     <- NEVER ADVANCED
accounting audit rows                     0   <- this program has never touched default's accounting
```

**`default`'s accounting surface is PRISTINE.** It is the only unspent accepting-side
precondition in the entire reference oracle — `gerege`'s was spent before this program
started. The accepting observation is therefore a **one-shot resource with exactly one unit
left**, and that unit sits on the tenant whose rounding mode and time zone both disqualify
the result. **Spending it buys a discrimination probe and destroys the only place a real
parity capture could ever have been taken**, if the rig's configuration ever changed.

---

## 6. Why the refusal is a SCRIPT and not this document

**P-89**, verbatim: *"PROSE DOES NOT FIRE ON THE NEXT FIRE — a limit written into a handoff,
a review, or a `## Backlog` heading is invisible to the scheduler."* T294 wrote its own
widening risk into a `## Backlog` heading and it cost a whole review fire to convert that
into a measurement. This finding does not repeat that.

- **`guard-accepting-capture.sh`** re-measures C1–C5 live, per tenant, and **fails closed**:
  unreachable database, unparseable registry row, or an unreadable configuration are all
  **exit 2** — *cannot measure*, explicitly not a refusal and explicitly not a pass. It
  carries **no substitution variables at all**, unlike T294's fence, because a gate whose
  greens can be manufactured by an environment variable is a gate the next task can talk
  its way past.
- **C5 is the condition no measurement can supply.** C1–C4 can all pass and the capture can
  still be wrong to take, because *"may this tenant be permanently mutated"* is a fact about
  the rig, not about the database. It is supplied by an `attest/<tenant>.disposable` file,
  **its absence refuses**, and `conformance.sh` now **fails the bar if such a file is ever
  committed** — a standing authorisation to post undeletable journal entries must be an
  explicit reviewed act, not something that arrives inside somebody's capture rig.
- **`red-drive-gate.sh`** proves the gate is not merely a stuck NO [`out/GATE-red-drive.txt`,
  exit 0]. **Four of the five conditions are driven BOTH WAYS by the two real tenants, with
  nothing substituted** — C1 ok on `gerege` / REFUSE on `default`, C2 the same, C3 ok on
  `default` / REFUSE on `gerege`, C4 ok on `gerege` / REFUSE on `default`. C5's wiring is
  demonstrated with a temporary attestation that the same run removes again.
- **`ARM 2 found a defect in my own gate.** The guard was documented to exit 2 on an
  unreachable database and **could not be shown to**, because `env.sh` — copied from T294 —
  clobbers an inherited `DBC`. That is P-22's shape applied to a guard's own error path, and
  the red-drive caught it rather than the author noticing. `env.sh` now uses `${VAR:-…}`,
  and the override cannot manufacture a PASS: every value it can take either reaches the
  real database or reaches none, and reaching none is exit 2 by construction.

**What is NOT driven, said here rather than left to be discovered:** the gate's **exit 0**
branch is **UNREACHED**. Reaching it needs a tenant passing all five at once and no such
tenant exists. The first task that creates a qualifying tenant is the task that exercises
that branch, and it should say so in its handoff.

---

## 7. T287's probes: run, read, NOT fired

`bash .softhouse/capture/t287-closure-refusals/guard-probe-expiry.sh` → **EXIT 1**, exactly
as the driver measured:

```
business date: 2026-08-23  (DERIVED -- enable-business-date='f', m_business_date rows: 0)
latest GLClosure at office 1: NONE (acc_gl_closure has no row for office 1)
ok      a1-01-future-far.json            transactionDate 2026-12-31 > 2026-08-23 -- still refuses.
ok      a1-02-future-boundary-plus1.json transactionDate 2026-08-24 > 2026-08-23 -- still refuses.
REFUSE  a2-01-preclosure-on-date.json    *** NO GLClosure EXISTS at office 1 ***  ... POSTS 2 JOURNAL ENTRIES
REFUSE  a2-02-preclosure-before.json     *** NO GLClosure EXISTS at office 1 ***  ... POSTS 2 JOURNAL ENTRIES
REFUSED: at least one probe would WRITE to the reference oracle if fired now.
```

**None of the four was fired.** `a1-02` arms **tomorrow, 2026-08-24**, and was not touched.

---

## 8. What a future task must do to close this, and what it must not

**MUST NOT:** promote another refusal vector and call the hole closed. Every refusal capture
in this corpus agrees with arm A. `conformance.sh` will not detect that mistake — the guard
counts **accepting** vectors specifically, and its red-drive ARM 5 proves a refusal vector
carrying `command: defineOpeningBalance` does **not** count. That arm exists because
`LDG-REFUSE-03` is exactly that shape and lives in the real corpus.

**MUST, in order:**

1. Obtain a tenant that passes **C1–C4**: `rounding-mode` 4, `Asia/Ulaanbaatar` or
   `Asia/Hovd`, an empty non-contra ledger, and a type-300 mapping onto an EQUITY account.
   On today's rig that means **a new tenant**, with §4's full cost including an oracle restart
   — which is a scheduling decision for the driver, not a capture decision for a worker.
2. Obtain **C5** — an explicit, reviewed disposability decision recorded as a file. Committing
   it fails the bar until somebody removes it, which is the point: it should be visible.
3. Run `guard-accepting-capture.sh` and get **exit 0**. It has never returned 0; the task
   that first does should say so.
4. Capture the accept, promote it, register a wrong implementation of the **arm A** shape
   (`refuses every defineOpeningBalance`), and prove it dies — that is the kill this whole
   finding is about.
5. **Delete the `T305-ACCEPTING-SIDE-GAP` paragraph from `capabilities-ledger.json` in the
   same diff.** `conformance.sh` fails if an accepting vector exists while the token remains
   — the caveat outliving its defect is the A2-34 F-4 defect and this guard refuses it in
   both directions.

---

## 9. Artefacts

| file | what it is |
|---|---|
| `out/M-01-gerege-accepting-precondition.*` | `gerege`: 26 non-contra ids, type 300 → GL 15 EQUITY |
| `out/M-02-default-accepting-precondition.*` | `default`: 0 ids, type 300 UNMAPPED, 0 GL accounts |
| `out/M-03-gerege-residue-class.*` | `gerege` sequences + 30 accounting audit rows |
| `out/M-04-tenant-store-cost.*` | the shared registry, 6 tables, 22 changelog rows, DB sizes |
| `out/M-05-default-residue-class.*` | `default`: both ledger sequences `is_called = f` — pristine |
| `out/GATE-verdict.txt` | `guard-accepting-capture.sh`, exit 1, per-tenant measurement |
| `out/GATE-red-drive.txt` | `red-drive-gate.sh`, exit 0, C1–C4 driven both ways |
| `out/GUARD-red-drive.txt` | `red-drive-conformance-guard.sh`, exit 0, 8 arms |
| `out/BAR-with-guard.txt` | the full green bar carrying the new census lines |

Every `out/NAME.sql` is a **snapshot** of the bytes executed, not a pointer at `sql/`, so a
later edit to `sql/` cannot silently invalidate the recipe (A2 defect D-1). `capsql.sh`
**refuses any query file containing a write verb in executable position** — a content fence
that does not depend on the author's intent.
