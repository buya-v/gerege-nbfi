# T305 — CAN THE OPENING-BALANCE ACCEPTING-SIDE CAPTURE BE TAKEN SAFELY?

**ANSWER: NOT ON EITHER TENANT OF THE STANDING REFERENCE ORACLE — AND YES ON A THROWAWAY
INSTANCE. THE OBSERVATION HAS BEEN TAKEN.** `POST /journalentries?command=defineOpeningBalance`
against an EMPTY ledger returned **HTTP 200** and six journal entries. The standing reference
oracle was not touched: its four ledger counters were read before the POST, after the POST and
after the teardown, and all three readings equal the baseline.

> **THIS FILE SUPERSEDES ITS OWN FIRST VERSION AND SAYS SO IN THE PLACES IT WAS WRONG.**
> The first version concluded **"NO. NOT ON THIS RIG, NOT TODAY, AND NOT BY ANY CHEAP VARIATION
> OF IT."** §2, §3 and §5 of that version were correct and are kept. **§4 was not.** It costed
> exactly one escape route — a new tenant *inside the standing instance* — found it needed an
> oracle restart, and generalised from that one route to "no cheap variation exists". It never
> examined the route the brief actually named: **a throwaway containerised instance.** That route
> needs no hand-made database, no row in the shared registry and no restart of anything, and it
> is §4b. The generalisation was the defect, not the measurement.

**WHAT WAS FIRED, AND AT WHAT.** Nine writes, every one of them at a container built for this
capture and destroyed in the same run: five setup calls, three accepted POSTs and one refused
POST. **NOTHING WAS FIRED AT THE STANDING REFERENCE ORACLE — not one write, at any point, by any
version of this rig.** Every observation this task took of `gerege` or `default` is a read-only
`SELECT` or a health GET. **None of T287's four probes was fired**; its expiry guard was run and
is quoted, re-measured today, in §7.

---

## 1. What the question actually is

T296 mutated the **port** in four arms and re-graded the whole ledger corpus
[`.softhouse/reviews/T296/REVIEW.md` §4]:

| arm | `GoPoster` STEP 1.5 predicate | result |
|---|---|---|
| BASE | `req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0` | PASS |
| **E** | the rule moved BELOW the balance check | **DIES** |
| **A** | `req.Command == "defineOpeningBalance"` alone — the id list never read | **SURVIVED** |
| **B** | `len(req.PostedNonContraTransactionIDs) > 0` alone — the command never read | **SURVIVED** |

Arm E vindicates T294's precedence claim and is not in question. **Arm A was the hole.** A port
that refuses *every* opening balance — including on an empty ledger, where the oracle **accepts**
— was green on the entire corpus. That is the `headerRefusingPoster` class this store already
names: **the reasonable thing to do, which the oracle does not do.**

**NO ADDITIONAL REFUSAL VECTOR COULD HAVE CLOSED IT.** Every refusal capture in this corpus
*agrees* with arm A. Only an accepting-side observation kills it, and the accepting side is the
fall-through at `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:810-816` [VERIFIED: pinned
checkout `426a23544`]:

```java
private void validateJournalEntriesArePostedBefore(final Long contraId) {
    final List<String> transactionIds = this.glJournalEntryRepository.findNonContraTransactionIds(contraId);
    if (!CollectionUtils.isEmpty(transactionIds)) { throw new GeneralPlatformDomainRuleException(...); }
}
```

---

## 2. Neither registered tenant can carry it — MEASURED, both of them, and re-measured today

`bash guard-accepting-capture.sh` → **exit 1** [`out/GATE-verdict.txt`; re-run
2026-08-27T15:09:30Z with identical results]. Five conditions, per tenant:

| condition | source of the requirement | `gerege` | `default` |
|---|---|---|---|
| **C1** `rounding-mode` = 4 (HALF_UP) | CLAUDE.md, ratified 18 Aug 2026 | **4 — ok** | **6 = HALF_EVEN — REFUSE** |
| **C2** timezone ∈ {Asia/Ulaanbaatar, Asia/Hovd} | CLAUDE.md, "two time zones, no DST" | **Asia/Ulaanbaatar — ok** | **Asia/Kolkata (+05:30) — REFUSE** |
| **C3** `findNonContraTransactionIds` EMPTY | `:812`, the accepting side | **26 ids — REFUSE** | **0 — ok** |
| **C4** type-300 → an EQUITY account | `:708`, and `:764-769` | **GL 15, enum 3 — ok** | **UNMAPPED — REFUSE** |
| **C5** a disposability attestation | §6; no measurement can supply it | **absent — REFUSE** | **absent — REFUSE** |

**The two tenants fail on DISJOINT conditions, and that is still the shape of the finding.** The
tenant that is production-representative has a ledger; the tenant with an empty ledger is not
production-representative (CLAUDE.md's own rule makes a capture at a non-ratified rounding mode a
*"discrimination probe, not a parity vector"*, and `.softhouse/reference-oracle.md` records
`default` as the deliberate wrong-offset / HALF_EVEN negative control). **There is no third
registered tenant.** Everything in this section survived the re-measurement unchanged.

---

## 3. The POST is IRREVERSIBLE wherever it is KEPT — from source, three ways

**(a) A posted journal entry has no delete path in Fineract at all.**
`JournalEntriesApiResource.java` exposes `@GET` and `@POST` only; `grep -rn "@DELETE"` over
`fineract-provider/src/main/java/org/apache/fineract/accounting/` matches **nothing**. The only
undo is `POST /journalentries/{transactionId}?command=reverse`, which **appends** — CLAUDE.md's
append-only ledger working correctly, and exactly why it is not a teardown.

**(b) An accepted opening balance posts TWO entries per leg. NOW OBSERVED, NOT INFERRED.**
`saveAllDebitOrCreditOpeningBalanceEntries` (`:759-797`) calls `helper.persistJournalEntry` twice
inside the per-leg loop — `:791` the leg, `:796` its contra. **The first version of this file
marked the consequence `[UNVERIFIED]` because no POST had been fired. It is now MEASURED: three
legs in, SIX journal entries out** [`throwaway/out/OB-ACCEPT-01-readback-db.json`], and the contra
entries are **per leg, not summed**.

**(c) The setup becomes UNDELETABLE BY THE CAPTURE'S OWN SUCCESS.**
`GLAccountWritePlatformServiceJpaRepositoryImpl.deleteGLAccount` (`:191-212`) refuses with
`TRANSACTIONS_LOGGED` once any journal entry references the account.

> **P-92**, verbatim: *"a probe whose safety comes from an EXTERNAL PRECONDITION rather than from
> its own content is a loaded weapon, and the danger is highest immediately after the capture
> SUCCEEDS — because taking the observation is often what removes the precondition."*

**No content fence exists for an accepting probe** — a body that cannot post is not an accept —
so the fence has to be on the TARGET. That is what `capture.sh`'s F1–F5 are, and it is why the
target is a container rather than a tenant.

---

## 4. A fresh tenant INSIDE THE STANDING INSTANCE is not the cheap escape it looks like

Unchanged from the first version, and still true. **There is no runtime tenant-creation path in
this build**: `grep -rn "TenantsApiResource" --include="*.java"` over the pinned checkout matches
**nothing**, and `TenantDatabaseUpgradeService` implements `InitializingBean` and runs liquibase
per tenant in `afterPropertiesSet()` — **startup only**, with `JdbcTenantDetailsService.loadTenantById`
`@Cacheable` on top. So a tenant added to the STANDING instance means (1) `CREATE DATABASE` by
hand, (2) hand-written rows in the SHARED `fineract_tenants` registry that also carries `gerege`'s
registration, and (3) **a restart of the reference oracle** — an outage for every concurrently
running worker, which mutates the *program* and not just a database. That is still a refusal.

**THE ERROR THE FIRST VERSION MADE WAS TO STOP THERE.** All three costs are costs of putting the
new tenant *inside the standing instance*. None of them applies to §4b.

---

## 4b. THE THROWAWAY INSTANCE — measured, and it is the answer

The brief asked directly: *"whether a throwaway containerised oracle instance is a cleaner answer
than mutating the standing one; if it is, say what it costs and whether the vector captured there
is admissible under this corpus's rules."* **It is cleaner, it is cheap, and the vector is
admissible.** Rig: `.softhouse/capture/t305-openingbalance-accepting-side/throwaway/`, one
command, `bash run-all.sh`.

### 4b.1 The tenant parameters are ENVIRONMENT VARIABLES, and that is the whole unlock

The first version assumed a qualifying tenant had to be *constructed*. It does not: the pinned
source binds three tenant-seed parameters straight into the liquibase seed [VERIFIED, pinned
`426a23544`]:

| parameter | binding | seeds |
|---|---|---|
| `FINERACT_DEFAULT_TENANTDB_IDENTIFIER` | `application.properties:61` → `spring.liquibase.parameters.fineract.tenant.identifier` (`:499`) | `tenants.identifier`, `tenant-store/parts/0002_initial_data.xml` |
| `FINERACT_DEFAULT_TENANTDB_TIMEZONE` (default `Asia/Kolkata`) | `:60` → `:501` | `tenants.timezone_id`, `0002_initial_data.xml:41` |
| `FINERACT_CONFIG_ROUNDING_MODE` (**default 6**) | `:77` `fineract.tenant.config.rounding-mode` → `:514` | `c_configuration.rounding-mode`, `tenant/parts/0002_initial_data.xml:219-220` |

**MEASURED AT FIRST BOOT of the throwaway**, before anything was fired at it:

```
tenants:  1|t305|T305 throwaway accepting-side capture tenant|Asia/Ulaanbaatar|fineract_t305
c_configuration.rounding-mode = 4          <- HALF_UP, the CLAUDE.md-ratified mode
acc_gl_journal_entry          = 0          <- C3 holds BY CONSTRUCTION
acc_gl_account                = 0
financial activity 300        = UNMAPPED   <- C4 is the only one the setup campaign must supply
```

So **C1, C2 and C3 are satisfied at boot, from environment variables, with no hand-written SQL and
no restart of anything.** C4 is four API calls. C5 — disposability — is not attested, it is
**structural**: the instance is destroyed.

### 4b.2 What it costs, measured rather than estimated

| cost | measured |
|---|---|
| image build | **none.** `fineract:latest` is already local, and it is the SAME image id the standing app runs: `sha256:e596339626bf…` from `docker inspect -f '{{.Image}}' fineract-fineract-1` |
| wall clock | **~2 min** to a healthy `{"status":"UP"}` on 8444, including the full liquibase migration of a new tenant store and tenant database; **~4 min** for the whole `run-all.sh` including capture and teardown |
| memory | the Docker VM has **7.75 GiB**; the standing stack uses **1.33 GiB** (fineract 1.202 GiB + db 125 MiB) and the throwaway needs about the same. `-Xmx1G` per JVM |
| disk | container writable layers only — the compose file declares **no named volume**, so `down -v` reclaims everything |
| ports | **8444** (free, checked) and **no published database port at all**; the standing stack keeps 8443 and 5432 |
| residue on the standing rig | **none measured.** Four counters, three times: `60/64` journal entries, `0` closures, `26` distinct transaction ids, `352` command-source rows — before, after, and after teardown |
| residue on the host | the `/tmp/t305-oracle-logs` directory and cached image layers that already existed |

Compare the residue class the brief predicted (T287's `acc_gl_closure_id_seq is_called=t` and a
PUBLIC audit row, still present on `gerege` today [`out/M-03-gerege-residue-class.txt`]): **the
throwaway leaves no sequence, no audit row and no database, because the database is gone.**

### 4b.3 The isolation is MEASURED, not asserted

`guard-throwaway-isolation.sh`, fail-closed, run first by `run-all.sh` and its output committed as
`throwaway/out/STANDING-baseline.txt`:

- **I1** the compose file publishes neither 5432 nor 8443 — the two ports the standing stack owns;
- **I2** its container names collide with no running container, and are refused outright if they
  are the standing ones;
- **I3** no named volume is declared (so `down -v` really does destroy all state) and every bind
  mount carries an explicit `ro`/`rw` mode;
- **I4** the only read-write mount is under `/tmp` — nothing in the pinned Fineract checkout or in
  this repository is writable by the capture rig;
- **I5** the standing oracle is UP and its four counters are recorded, so `capture.sh` and
  `down.sh` can re-check them.

**ONE FALSE POSITIVE, RECORDED RATHER THAN QUIETLY FIXED** (P-72, *calibrate the instrument on a
known positive*): the guard's first draft matched `^\s+- /` and refused all six `env_file:` and
`tmpfs:` entries as "no explicit ro/rw mode". A bind mount is `- <src>:<dst>[:mode]` and its
DESTINATION starts with `/` too; that is the discriminator, and the comment in the script says so.

### 4b.4 The capture's own fence is on the TARGET, because no content fence exists

`capture.sh` refuses unless **all five** hold, and each fails closed:

- **F1** the base URL names port **8444** and the tenant header names **t305** (the standing oracle
  is 8443 / `gerege`, and no environment value can make those look alike);
- **F2** `t305-oracle-app` is running and its database answers;
- **F3** the TARGET'S OWN registry reads `t305|Asia/Ulaanbaatar|fineract_t305` and its own
  `c_configuration.rounding-mode` reads 4 — read from the target, never from the rig's own files;
- **F4** the target's `acc_gl_journal_entry` is **empty** — which is the accepting precondition
  itself;
- **F5** the STANDING oracle's four counters equal the baseline, checked **before and again after**
  the POST.

### 4b.5 What the oracle answered

```
POST /journalentries?command=defineOpeningBalance   ->   HTTP 200
{"officeId":1,"transactionId":"<server-assigned>"}
```

and the readback carries **six** entries for three request legs, each leg followed by a CONTRA
entry of the opposite side on the financial-activity-300 account, **per leg and not summed**:

| id | GL | code | side | amount (stored scale 6) |
|---|---|---|---|---|
| 1 | 2 | T305-1000 | DEBIT | 250000.250000 |
| 2 | 1 | T305-3000 | CREDIT | 250000.250000 |
| 3 | 3 | T305-1100 | DEBIT | 100000.370000 |
| 4 | 1 | T305-3000 | CREDIT | 100000.370000 |
| 5 | 4 | T305-2000 | CREDIT | 350000.620000 |
| 6 | 1 | T305-3000 | DEBIT | 350000.620000 |

`25000025 + 10000037 = 35000062` minor units, and both totals are `70000124`. **The body carries
three legs of three DIFFERENT amounts on purpose:** a one-debit-one-credit body cannot distinguish
a per-leg contra from a single netted one.

### 4b.6 Is a vector captured there ADMISSIBLE? Yes — and here is the argument, with its limit

Four things make a capture admissible in this store, and the throwaway satisfies all four.

1. **THE CODE IS THE SAME BYTES.** Not "the same version" — the same image id, which is a
   measurable fact and was measured. The thing a vector grades is the behaviour of that code.
2. **THE TENANT ARITHMETIC IS THE RATIFIED ONE.** `HALF_UP`, seeded, verified from the target's own
   `c_configuration`. `MoneyHelper.PRECISION` is a compile-time 19, so the mode is the only
   tenant-scoped term in the `MathContext` — which is exactly why `default` is disqualified and
   `t305` is not.
3. **THE BYTE PROVENANCE IS THE USUAL ONE.** Request bytes, response bytes, status, sha256 of each,
   `.http` sidecar, captured-at-utc. T296 re-verified the whole of T294 from committed bytes
   without re-firing anything; the same is possible here.
4. **THE RECIPE IS COMMITTED AND DETERMINISTIC.** `run-all.sh` rebuilds the instance from the same
   image, seeds the same tenant parameters, replays the same setup campaign and re-fires the same
   bytes. What it cannot reproduce is the server-assigned transaction id and the wall clock —
   neither of which is a graded cell. **This is arguably MORE reproducible than a capture on
   `gerege`, whose state drifts with every fire; `gerege` could never yield this observation twice
   even in principle, because taking it once destroys the precondition.**

**THE HONEST LIMIT, stated rather than buried.** A throwaway cannot capture anything that depends
on `gerege`'s accumulated state — its chart, its products, its 60 entries, its history. **The
accepting side of `:812` is the exact opposite of that: it is only observable on a tenant with NO
accumulated state.** So the throwaway is not a workaround for the graded tenant here; for this one
observation it is the only surface that can exist. **A future task must not read this section as a
general licence to capture off-tenant.** The tenant is named `t305` and not `gerege` precisely so
that no reader can mistake one for the other.

---

## 4c. THE LARGEST FINDING WAS NOT PLANNED: THE REFUSAL RULE IS NOT WHAT THIS STORE SAYS IT IS

`capture2.sh`'s first arm was named `OB-REFUSE-02` and **predicted HTTP 403**. It got **HTTP 200**.

`findNonContraTransactionIds(contraId)` EXCLUDES every transaction that touches the contra
account, and **every entry an opening balance writes touches it** (`:796`). So **opening balances
do not block each other.** The oracle REVERSES the previous one (`:726-735`
`findNonReversedContraTransactionIds` → `revertJournalEntry`) and posts the new one. Measured, on
one instance, with **byte-identical request bytes** (`cmp` silent) each time:

| arm | ledger state when fired | answer |
|---|---|---|
| `OB-ACCEPT-01` | empty | **HTTP 200**, 6 entries |
| `OB-ACCEPT-02` | 6 opening-balance entries | **HTTP 200**, the first 6 flagged `reversed=t` with `reversal_id` set, 6 reversal entries on their own transaction id, 6 new entries |
| `MJE-ACCEPT-01` | 18 entries, all contra-touching | **HTTP 200** — a plain manual entry, the shape T296 arm B refuses |
| `OB-REFUSE-03` | one NON-CONTRA transaction now exists | **HTTP 403**, `errors[0].args` = exactly that one transaction id |

**THE RULE IS "AFTER A NON-CONTRA JOURNAL ENTRY", NEVER "AFTER ANY JOURNAL ENTRY".** The oracle's
own message at `:814` says the wrong thing, and this store repeated it — in `LDG-REFUSE-03`'s
title, in `impl.go`'s STEP 1.5 comment and in the capability row. All three are corrected in this
diff. **The port's PREDICATE was already right** (it reads
`posted_non_contra_transaction_ids`, whose name has the distinction in it); only the prose was
wrong, which is P-11 exactly — *the code can be RIGHT and its stated reason WRONG, and the reason
is what the next contributor checks.*

---

## 5. The residue class, measured on the tenant that already carries it

Unchanged and still true. **`gerege` today** [`out/M-03-gerege-residue-class.txt`]:
`acc_gl_journal_entry_id_seq` 64 `is_called=t`; **`acc_gl_closure_id_seq` 1 `is_called=t` — T287's
permanent trace**; `m_portfolio_command_source_id_seq` 352; 352 audit rows, 30 on accounting
entities. **`default` today** [`out/M-05-default-residue-class.txt`]: both ledger sequences
`is_called = f`, zero accounting audit rows — **pristine, and this task did not spend it.** That
was the first version's strongest practical point and it stands: `default`'s untouched accounting
surface was a one-shot resource, and the throwaway route means it was not consumed to buy a
capture the project's own rules would have refused to call a parity vector.

---

## 6. Why the refusal is a SCRIPT and not this document — and what changes now

`guard-accepting-capture.sh` still exists and still exits 1, and that is **correct**: it answers
*"may an accepting capture be taken on a REGISTERED TENANT of the standing oracle?"* and the
answer is still no. It is not superseded by §4b; it is the fence that makes §4b the only route.
Its C5 remains the condition no measurement can supply, `attest/<tenant>.disposable` remains the
only way to supply it, and `conformance.sh` still **fails the bar if such a file is ever
committed**.

**What changes is the OTHER guard.** `guard_accepting_side_gap_declared` is two-way by
construction: with an accepting vector now in the store, the token `T305-ACCEPTING-SIDE-GAP` must
be **removed in the same diff**, and it is. That is the guard working as designed — the caveat
does not get to outlive its defect (A2-34 F-4).

---

## 7. T287's probes: run, read, NOT fired — AND THE ARMING STATE HAS CHANGED SINCE THE FIRST VERSION

`bash .softhouse/capture/t287-closure-refusals/guard-probe-expiry.sh` → **EXIT 1**, re-run today:

```
business date: 2026-08-27  (DERIVED -- enable-business-date='f', m_business_date rows: 0; today in Asia/Ulaanbaatar)
latest GLClosure at office 1: NONE (acc_gl_closure has no row for office 1)
ok      a1-01-future-far.json             transactionDate 2026-12-31 > 2026-08-27 -- still refuses.
REFUSE  a1-02-future-boundary-plus1.json  *** transactionDate 2026-08-24 is NOT after business date 2026-08-27 ***
REFUSE  a2-01-preclosure-on-date.json     *** NO GLClosure EXISTS at office 1 ***
REFUSE  a2-02-preclosure-before.json      *** NO GLClosure EXISTS at office 1 ***
```

**THREE OF THE FOUR ARE NOW ARMED, NOT TWO.** The first version of this file quoted `a1-02` as
`ok … still refuses` and noted it would arm "tomorrow, 2026-08-24". **That day has passed.**
Firing `a1-02` now POSTS TWO JOURNAL ENTRIES into the standing reference oracle, permanently.
**None of the four was fired by any version of this task.**

---

## 8. What is closed, and what a future task must still do

**CLOSED BY THIS TASK:**

1. The accepting side of `:812` is **OBSERVED**, on the ratified arithmetic, with committed bytes.
2. **T296 arm A is KILLED.** It is registered as `ledger-wrong-openingbalance-always-refusing` and
   dies to `LDG-05`.
3. A second defect the same capture exposes — writing the caller's legs and missing the contra
   entries — is registered as `ledger-wrong-openingbalance-no-contra` and dies too.
4. The **"after any journal entry"** misstatement is corrected in all three places this store
   made it.

**STILL OPEN, and named so it is not mistaken for done:**

1. **The REVERSAL behaviour is observed and graded by nothing.** `OB-ACCEPT-02` shows a
   re-definition reversing the previous opening balance; no port in this store reverses anything
   and the vector schema has no shape for "this POST also modified earlier entries". That is the
   next promotion and it has its capture already.
2. **T296 arm B is still unkilled by a vector**, though `MJE-ACCEPT-01` is the capture that would
   kill it: a plain manual entry accepted while non-contra transactions exist. Promoting it needs
   the `posted_non_contra_transaction_ids` input on a NON-opening-balance vector, which `admit.go`
   currently refuses by an explicit T294 rule. **That rule is right on today's evidence and would
   have to be re-argued, not quietly relaxed.**
3. **The accepting side of the CLOSURE and FUTURE-DATE boundaries** (T295 backlog B-1 and B-2)
   remains uncaptured. **§4b is the route for both**, and the rig is reusable: they need the same
   throwaway, a `GLClosure`, and one entry either side of the boundary.
4. `guard-accepting-capture.sh`'s **exit 0 branch is still UNREACHED**, and now never will be by
   this route — the throwaway is not a registered tenant of the standing oracle and the gate does
   not measure it. That is a deliberate seam and it is stated here rather than papered over.

---

## 9. Artefacts

| file | what it is |
|---|---|
| `out/M-01…M-05` | the read-only per-tenant measurement of the STANDING oracle (unchanged) |
| `out/GATE-verdict.txt`, `out/GATE-red-drive.txt` | `guard-accepting-capture.sh` exit 1, and its red-drive |
| `out/GUARD-red-drive.txt` | the `conformance.sh` guard's 8-arm red-drive |
| `throwaway/docker-compose.t305.yml` | the disposable instance, self-contained, no named volume |
| `throwaway/guard-throwaway-isolation.sh` | I1–I5, fail-closed |
| `throwaway/setup.sh` | MNT, four GL accounts, financial activity 300 |
| `throwaway/capture.sh` | **the accepting capture**, F1–F5 target fence |
| `throwaway/capture2.sh` | the ACCEPT / ACCEPT-with-reversal / REFUSE sequence on one body |
| `throwaway/down.sh` | destroy, and prove the standing oracle did not move |
| `throwaway/run-all.sh` | all of the above as one reproducible command |
| `throwaway/build-vector.py` | builds `LDG-05` from the captured bytes; no graded cell is typed |
| `throwaway/patch-capability.py` | replaces the capability row's gap paragraph, one paragraph wide |
| `throwaway/red-drive-port.sh` | 4 arms: STEP 4 deleted -> LDG-05 FAILS; both wrong impls die; `impl.go` restored by sha256 |
| `throwaway/out/PORT-red-drive.txt` | that red-drive's transcript |
| `throwaway/out/` | every request, response, status, sha256 and `.http` sidecar |
