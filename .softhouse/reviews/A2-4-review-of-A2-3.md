# A2-4 — independent review of A2-3 (slice A2 oracle capture)

Reviewer **A2-4**, branch `softhouse/A2-4-review-a2-3`, local fire **2026-08-21**.
Target: **`softhouse/A2-3-capture`**, read from the branch (`git show`/`git archive`), never from a
working tree. Reference oracle (Fineract) **UP** throughout; `fineract-fineract-1` and
`fineract-db-1` were **not restarted, rebuilt or re-seeded**.

## VERDICT: **MICRO-FIX**

The corpus is real, the findings hold, and two of them are *stronger* than A2-3 stated. No REJECT
trigger fires: nothing is fabricated, nothing was promoted, no money value was decided in binary
float, and neither shipped gate is a P-22 "cannot fail" guard. But eleven concrete defects need
fixing before this corpus is mined by anyone, one of which is a genuine P-22-class instance
(a safety control in `cap.sh` that structurally cannot execute) and one of which is a
provably-false recipe on 10 of 108 exchanges.

---

## 1. Attack: can any assertion pass on EMPTY INPUT?

### 1a. The Path B preconditions gate — **SOUND, and I could not make it lie**

Run by me, from `.softhouse/capture/pathb`, on **both interpreters**:

```
CANARY_REQ=t22-audit/req/calc-pmode2-gerege.json bash t36/preconditions.sh gerege   -> exit 0
CANARY_REQ=t22-audit/req/calc-pmode2-gerege.json sh   t36/preconditions.sh gerege   -> exit 0
sh and bash transcripts IDENTICAL (byte-for-byte diff, empty)
```

Four attacks on the canary, all **REFUSED**:

| attack | result |
|---|---|
| `CANARY_REQ` unset | exit 1 — *"rounding-mode canary NOT run: CANARY_REQ is unset … A DB row is not proof of the mode in force."* |
| `CANARY_REQ` = a different committed request (`calc-p05.json`) | exit 1 — **DIGEST MISMATCH**, names computed vs pinned sha256, *"THE CANARY WAS NOT SENT and the effective rounding mode is UNPROVEN."* |
| `CANARY_REQ=/dev/null` (**empty input**) | exit 1 — *"'/dev/null' is not a readable file."* |
| `CANARY_EXPECT=99999.99` (the old T77/T91 hole) | exit 1 — *"the canary expectation is a CONSTANT (20925.05). Refusing to grade the arithmetic against a value supplied by the runner."* |

Two negative controls drove it **RED**:

- tenant `default` → exit 1, **5 breaches**, including the JVM's own line
  `Initialized rounding mode for tenant 'default': HALF_EVEN`.
- tenant `nosuchtenant` → exit 1, **10 breaches** — and critically it emits
  *"schema_connection_parameters check **INSPECTED NOTHING**: the query … returned no row at all,
  so 'empty' would mean 'not read', not 'empty'."* **The zero-input defect class this program was
  bitten by is explicitly closed in this rig.** Two assertions also self-report their input volume
  (`47 env line(s) actually scanned`, `5406 jar entry line(s) actually scanned`).

**A2-3's reliance on this gate is justified.** One correction: it emits **22 PASS**, not 23
(`grep -c '  PASS  '` = 22, FAIL = 0). This matches T91's own recorded figure ("after T91: 22 PASS,
0 FAIL, exit 0"). The handoff and `CAPTURE-PLAN.md` §6 both say 23. → **MF-6**.

### 1b. `manifest.py verify` — failable, but it has three holes

Reproduced A2-3's prover verbatim, unmodified:

```
baseline: GREEN (exit 0)
  mutate  -> exit 1 CAUGHT
  delete  -> exit 1 CAUGHT
  add     -> exit 1 CAUGHT
restored: GREEN (exit 0)
RESULT: guard is demonstrably failable          PROVER_EXIT=0
```

So the guard is **not** a P-22 "cannot fail" guard. But I drove three passes it should not give:

**Hole A — vacuous pass on empty input (MF-3).** An empty `MANIFEST.sha256` with no `out/`,
`req/`, `sql/` at all:
```
$ : > MANIFEST.sha256 ; python3 manifest.py verify
OK: 0 files match MANIFEST.sha256
EXIT=0
```
`verify()` iterates `want` and `have`; both empty ⇒ `bad == 0` ⇒ exit 0 with a green sentence.
A guard that certifies zero input must be an error, not a pass. Mitigating: `prove-manifest-red.py`
independently refuses (`exit 2`) if its victim file is absent, so the *prover* cannot be fooled this
way — but `manifest.py verify` is what the `CAPTURE-PLAN.md` reproduce recipe tells the next worker
to run, and it is what would sit in CI.

**Hole B — subdirectory blindness (MF-4).** `entries()` uses `os.listdir` + `os.path.isfile`, which
is **not recursive**. One `mkdir` defeats the UNTRACKED arm that the prover certifies:
```
$ mkdir -p out/extra
$ echo '{"fabricated":true,"amount":999999999}' > out/extra/A2-999-fabricated.json
$ echo 200 > out/extra/A2-999-fabricated.status
$ python3 manifest.py verify
OK: 406 files match MANIFEST.sha256
EXIT=0
```
A fabricated observation planted one directory deep is laundered as verified — precisely the
failure mode the guard's own docstring says it exists to prevent.

**Hole C — the manifest protects the data, not the claims or the rig (MF-5).** `DIRS = ("out",
"req", "sql")`. `CAPTURE-PLAN.md` — the 334-line document carrying **all seven findings** — is not
hashed. Neither are `cap.sh`, `run-*.sh`, `mkreq*.py`, `show.py`, `prove-manifest-red.py`, nor
`manifest.py` itself. Driven:
```
$ printf '\nFABRICATED CONCLUSION: MNT rounds HALF_EVEN and money may be stored as float.\n' >> CAPTURE-PLAN.md
$ printf '\n# tampered\n' >> manifest.py
$ python3 manifest.py verify
OK: 406 files match MANIFEST.sha256
EXIT=0
```

### 1c. `cap.sh` — a P-22-class control that structurally **cannot execute** (MF-1)

`cap.sh` opens `set -e` and then does:
```sh
code=$(curl -sk ... -o "$OUT" -w '%{http_code}')
rc=$?
if [ $rc -ne 0 ]; then
  echo "TRANSPORT FAILURE (curl rc=$rc) for $NAME — NO OBSERVATION WAS MADE." >&2
  rm -f "$OUT"; exit 1
fi
```
Under `set -e` a failing command substitution in an assignment terminates the shell **at the
assignment**. `rc=$?` is never reached and the whole handler — message *and* `rm -f "$OUT"` — is
**unreachable dead code**. Driven against an unreachable endpoint:
```
$ sh ./cap.sh TRANSPORT-TEST GET /glaccounts
CAP_EXIT=7                       # curl's code, not the script's exit 1
                                 # "TRANSPORT FAILURE" never printed
```
And the consequence the `rm -f` was written to prevent, driven:
```
$ echo '{"STALE":"body from a previous, different run"}' > out/TRANSPORT-TEST.json
$ echo 200 > out/TRANSPORT-TEST.status
$ sh ./cap.sh TRANSPORT-TEST GET /glaccounts     # oracle unreachable
CAP_EXIT=7
out/TRANSPORT-TEST.json   -> {"STALE":"body from a previous, different run"}   (survives)
out/TRANSPORT-TEST.status -> 200                                               (survives)
out/TRANSPORT-TEST.http   -> captured-at-utc: 2026-08-21T06:19:44Z             (FRESH)
```
**A stale body and stale status, stamped with a capture time at which no observation was made.**
The failure is still loud (non-zero exit), so nothing was laundered *this* fire — I verified the
shipped corpus is clean: 108 complete `{.json,.status,.http}` triples, **no orphans in either
direction, no zero-byte files**. But this is the P-22 class and it must be fixed.

---

## 2. Attack: is every observation traceable, and does re-issuing reproduce the recorded bytes?

I re-issued recorded recipes against the **live** oracle, taking method and path from A2-3's own
`.http` files and the body from the `req/` file each `.http` names.

**All 27 non-`attempt1` POST refusals** (replaying a refusal mutates no committed row):

```
byte-identical = 24        differs = 3
```

That is the strongest single piece of evidence in this review: **24 of 27 refusal recipes
regenerate their recorded bytes exactly, ~17 hours later.** The corpus is real.

All 13 recorded **GET** exchanges were also re-issued; 4 are byte-identical and 9 differ, every
difference explained by A2-3's own documented mutations to the tenant (see §4). Nothing is
unexplained; nothing is fabricated.

The three non-`attempt1` refusal diffs each turned into a finding:

- **`A2-bad-045-no-usage`** differs *only* in the burned identity value inside the leaked
  PostgreSQL text: `Failing row contains (20, No Usage, …)` at capture vs `(26, …)` now. So the
  duplicate-of-A2-3's contract flag is right that raw PG text reaches the wire — and I add that
  **it embeds a non-deterministic sequence value, so this refusal can never be a byte-exact golden
  vector**, not even against Fineract itself. → **MF-11**.
- **`A2-prod-066-bad-paymenttype`** recorded **404** `PaymentType with 9999 does not exist`; it now
  returns **403** `fundSourceAccountId … Id 2 maps to the account Fund Source of type INCOME`.
  Cause: A2-3's own `A2-111` retyped GL 2 ASSET→INCOME, and the fund-source type check now fires
  *before* the payment-type lookup. **A2-3's corpus is order-dependent in the refusal REASON, not
  just in the ids** — `CAPTURE-PLAN.md` discloses only the id instability. → **MF-10**.
- **`A2-086-disburse-loan3-dupchannel`** was **BYTE-IDENTICAL** on my first replay and only differs
  after my own control disbursement (§4). See §5.

### The `attempt1-*` recipes are provably false — **all 10 of them** (MF-2)

`rename1.py` preserved the attempt-1 **responses** but not the attempt-1 **requests**: `mkreq2.py`
overwrote `req/prod-06*.json` in place. Both `.http` files name the same body:

```
out/attempt1-A2-prod-060-…http :  body-file: req/prod-060-cash-with-channel-override.json
out/A2-prod-060-…http          :  body-file: req/prod-060-cash-with-channel-override.json
$ grep -c isInterestRecalculationEnabled req/prod-060-cash-with-channel-override.json
1
```

So a 400 whose entire content is *"The parameter `isInterestRecalculationEnabled` is mandatory"* is
paired with a request body that **contains that parameter**. Replaying all ten:

```
attempt1-A2-prod-060 … 069     rec=400  now=403/400   DIFFERS  (10/10)
```
(now `Loan product with short name 'A2C1' already exists`, an unrelated refusal).

Ten of 108 exchanges (9.3%) carry a recipe that cannot regenerate them and that actively
contradicts them. This is exactly the 21-Aug hygiene rule and the "mislabelled refusal becomes a
false contract-refusal vector" risk. The fix is cheap: write the attempt-1 bodies to
`req/attempt1-*.json` and repoint the ten `.http` files, or state in each `.http` that the request
is not preserved.

### Orphan and dangling bodies

```
req/ referenced by an observation: 73        present: 76        dangling references: 0
ORPHANS:  upd-070-repoint-fundsource.json     (disclosed in the handoff)
          upd-071-add-channel.json            (disclosed in the handoff)
          disburse-086-nopaymenttype.json     (NOT disclosed)   -> MF-8
```
`A2-086`'s recipe names `disburse-084-paymenttype1.json`; `disburse-086-nopaymenttype.json` was
written, never sent, and hashed into `MANIFEST.sha256` anyway.

### Count check (MF-7)

```
MANIFEST.sha256 entries          406   = 327 out/ + 76 req/ + 3 sql/     -> the 406 claim is CORRECT
out/ files                       327   = 108 .json + 108 .status + 108 .http + 3 .txt
HTTP exchanges                   108   (98 excluding attempt1-*)
DB dumps                           3
```
**"327 observations" is a file count relabelled as observations.** The true figure is 108 HTTP
exchanges (98 excluding the preserved defective batch) plus 3 SQL dumps — a ~3x overclaim in the
headline number. The handoff's own group table sums to ~73 exchanges + 3 dumps, so the table and
the headline already disagree with each other.

---

## 3. Attack: any MONEY value read through binary floating point?

**Clean. No T145 violation.**

- Only one script in the directory parses JSON — `show.py` — and it uses
  `json.load(f, parse_float=decimal.Decimal)`. `manifest.py` reads bytes only. `mkreq*.py` and
  `rename1.py` do not parse JSON at all. Swept every `.py` in the slice for `json.load`,
  `json.loads`, `float(` and `parse_float`: three hits, all accounted for.
- Every monetary literal in `req/` is a bare integer (`"transactionAmount": 1200000`).
- Confirmed at the live DB: `acc_gl_journal_entry.amount` is **`numeric(19,6)`**, and
  `office_running_balance` / `organization_running_balance` likewise. No `double precision`,
  no `real`, anywhere on the money path.
- No money value in the handoff or `CAPTURE-PLAN.md` was computed by the rig; all are quoted from
  the oracle's own output.

---

## 4. Attack: was anything promoted into `.softhouse/vectors/`?

**NO. Verified by diff, not by reading the claim.**

```
$ git diff --name-only main...softhouse/A2-3-capture -- .softhouse/vectors/
(empty)
$ git diff --name-only main...softhouse/A2-3-capture | grep -v 'capture/tierA-a2/' | grep -v 'handoff/'
(empty)
$ git diff --stat main...softhouse/A2-3-capture | tail -1
426 files changed, 2815 insertions(+)      # 425 capture files + 1 handoff, nothing else
```

Scope is clean: no Go, no file outside `.softhouse/capture/tierA-a2/` and the handoff.
I promoted nothing either.

---

## 5. The two highest-value findings, checked against the live oracle

### Finding 1 — `hierarchy` omits the root's own id: **CONFIRMED**, three independent ways

**At the live DB** (`fineract_gerege`, read directly, not through A2-3's dump):
```
 id |     name       | parent_id | hierarchy
  1 | Assets         |           | .
  2 | Fund Source    |         1 | .2.        <- child of root 1, NOT .1.2.
  3 | Current Assets |         1 | .3.
  4 | Loan Portfolio |         3 | .3.4.      <- grandchild, root's id absent
 21 | Liability…     |         1 | .21.
```

**Re-derived at source**, `fineract-core/…/accounting/glaccount/domain/GLAccount.java:186-196`:
```java
public void generateHierarchy() {
    if (this.parent != null) { this.hierarchy = this.parent.hierarchyOf(getId()); }
    else                     { this.hierarchy = "."; }
}
private String hierarchyOf(final Long id) { return this.hierarchy + id.toString() + "."; }
```
The root's hierarchy is the bare `"."`, not `".1."`, so **the root's own id is absent from every
descendant path in the tree, at every depth** — not just from its direct children. A port that
seeds the root as `.1.` produces `.1.2.` and `.1.3.4.` and diverges on every row.

The REST surrogate is `nameDecorated`, built in
`fineract-accounting/…/GLAccountReadPlatformServiceImpl.java:49` as
`substring('……', 1, (LENGTH(hierarchy) - LENGTH(REPLACE(hierarchy,'.','')) - 1) * 4)` — i.e.
`(dot_count - 1) * 4` leading dots. Root `.` → 0; `.2.` → 4; `.3.4.` → 8. My live re-issue of
`GET /glaccounts/3` returned `"nameDecorated":"....Current Assets"`. Arithmetic checks out.

**The ABSENCE claim also holds** — and I re-ran the search rather than trusting it, with the
positive controls the driver's false-zero incident demands. Using `grep -rIn` (not `git grep -E`,
which lacks GNU `\b`):

```
POSITIVE CONTROLS
  test files containing 'GLAccount'                     34   (>0 OK)
  main-source hits for 'hierarchy'                     380   (>0 OK)
  hits for 'nameDecorated'                             128   (>0 OK)
NEGATIVE CONTROL
  hits for 'zzzz_no_such_token_a24_zzzz'                 0   (=0 OK)

RESULTS
  of the 34 GLAccount test files, those mentioning 'hierarchy'      1
     -> TellerWritePlatformServiceJpaImplTest.java, and only findOfficeHierarchy() — OFFICE
        hierarchy, a different entity. NOT a GL hierarchy test.
  ANY test file containing 'hierarchy' at all (whole repo)          4
     -> CenterHelper, CenterDomain, OfficeTest, DatatableUtilTest — none GL accounting.
  tests calling generateHierarchy() / setHierarchy()                0
  generateHierarchy() call sites in main                            2
     -> GLAccountWritePlatformServiceJpaRepositoryImpl.java:98 and :137
```

**A2-3 is right: Fineract has no test anywhere covering GL account `hierarchy`.** A Go port that
writes the intuitive `.1.2.` ships green against the entire upstream suite. This is a genuine
Tier-D vector obligation.

### Finding 2 — duplicate mapping: **CONFIRMED, but A2-3's characterisation is WRONG and must be narrowed**

The premise is confirmed at the live DB. Product 27 carries **two** rows for the same key:
```
 id | product_id | payment_type | gl_account_id | financial_account_type
 52 |         27 |            1 |            16 |                      1
 53 |         27 |            1 |             2 |                      1
```
and `\d acc_product_mapping` shows **no unique constraint** on
`(product_id, product_type, payment_type, financial_account_type, charge_id)` — only the `id`
primary key and three FK indexes. The JPA `@UniqueConstraint(name="financial_action")` is not in
the deployed DDL. A2-3 is right.

I re-issued the recorded disbursement 17 hours later:
```
POST /loans/3?command=disburse   with req/disburse-084-paymenttype1.json   -> HTTP 403
recorded  sha256 3ce26211a1caba3074245f91d9cbdae07066b92dffbda810d82755898ad102e7
re-issued sha256 3ce26211a1caba3074245f91d9cbdae07066b92dffbda810d82755898ad102e7
BYTE-IDENTICAL — "More than one result was returned from Query.getSingleResult()"
```

**But A2-3's control is missing, and it changes the finding.** I ran it — the same loan, the same
product, the same amount, with `paymentTypeId` **omitted**:
```
POST /loans/3?command=disburse   {"actualDisbursementDate":"01 February 2026",
                                  "transactionAmount":1200000,"locale":"en",…}
-> HTTP 200   status -> loanStatusType.active
   journal entries 9/10 posted: DEBIT GL 4 Loan Portfolio / CREDIT GL 2 Fund Source
   (product 27's generic payment_type-NULL row, id 42 -> gl_account_id 2)
```

So **the product CAN disburse.** Only the *duplicated payment-type path* detonates. The correct
statement is:

> A duplicated payment-channel override makes disbursement permanently impossible **through that
> payment type**; disbursements that do not carry it fall back to the generic row and succeed.

"the oracle can create a product that can never disburse" and "every later disbursement fails
permanently" are both overstated. This matters for the port: a Go implementation must refuse on the
duplicated key **only**, not on every disbursement, or it diverges on the very next request. →
**MF-9**. (This also independently re-confirms A2-3's finding 3, the resolution-order rule:
payment-type-specific row wins, absence falls back to `payment_type IS NULL`.)

### Finding 7 — confirmed, and it is worse than A2-3 says (new)

A2-3 stopped at *"the oracle holds a state it would refuse to let you create."* Re-issuing the
journal-entry reads shows the retype is **retroactively visible on already-posted entries**:

```
GET /journalentries?loanId=2&limit=50   entry 4:  glAccountType ASSET  (at capture)
                                                  glAccountType INCOME (now)
GET /journalentries?loanId=4&limit=50   entry 7:  ASSET -> INCOME
```
`\d acc_gl_journal_entry` confirms the cause: the entry row stores `account_id`, `type_enum`
(DEBIT/CREDIT) and `amount`, and **no classification of its own**. The API renders
`glAccountType` from the account's *current* type. An append-only ledger is therefore presenting
mutated history through the read API. This is a port decision that must be recorded — Gerege's
non-negotiable is "the ledger is append-only; corrections are reversing entries", and Fineract's
read path does not honour that for account reclassification. Not a defect in A2-3's work; an
omission from its write-up, and a real one.

---

## 6. The preserved `attempt1-*` failures

**A2-3's note is accurate as far as it goes, and incomplete in a way that creates a false trail.**

Accurate: `rename1.py`'s docstring correctly states the 30 files are the first product batch,
refused 400 because *A2-3's own payload* omitted `isInterestRecalculationEnabled`; that they are
real oracle refusals; and that they are "not evidence about product-to-account mapping". Keeping
them rather than silently overwriting is the right call and I endorse it.

Containment holds inside A2-3's own documents: `grep -n attempt1 CAPTURE-PLAN.md` → **0 hits**;
they are cited in the handoff only as preserved defects, never as A2 evidence.

Incomplete in two ways:
1. The note does not say the corresponding **request bodies were destroyed** and that the ten
   `.http` recipes now point at bodies that contradict their responses (MF-2 above). A downstream
   worker mining `out/` directly — the realistic case — reads a matched request/response pair and
   concludes the shipped body is refused. It is not; it returns 200.
2. It says "those 30 files"; they are 30 *files*, i.e. 10 *exchanges*.

---

## 7. Standing PostgreSQL-only assertion — re-verified by me at the end of this review

```
FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME = org.postgresql.Driver
FINERACT_HIKARI_JDBC_URL                 = jdbc:postgresql://db:5432/fineract_tenants
FINERACT_DEFAULT_TENANTDB_PORT           = 5432
prohibited-engine hits in container env  = 0   (ojdbc|oracle.jdbc|:1521|com.mysql.cj|mariadb|go-sql-driver)
server                                   = PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) aarch64
```
The preconditions gate independently re-asserted the same, plus **0 prohibited driver jars in
`fineract-provider.jar` across 5406 jar entry lines actually scanned**, and
`PostgreSQL JDBC driver present in the jar`. No Oracle Database, MySQL or MariaDB anywhere.

Note for the record: `CAPTURE-PLAN.md` §6 invokes the gate as `sh t36/preconditions.sh`. I ran it
under **both** `sh` and `bash` and the transcripts are byte-identical (T85's invariance holds), so
this is not a defect here — but the pipeline rule is `bash`, and the recipe should say `bash`.
`docker exec -i fineract-db-1 psql -U root …` in the same recipe **does** work (verified); `root`
is a valid role alongside `postgres`.

---

## 8. Findings ledger

### P-22-class (a control that structurally cannot execute)
| id | finding |
|---|---|
| **MF-1** | `cap.sh`'s transport-failure handler is unreachable dead code under `set -e`. Driven: message never prints, `rm -f "$OUT"` never runs, and a stale body + stale status survive under a **fresh** `captured-at-utc`. Fix: capture the status without `set -e` killing the assignment (`set +e` around the curl, or `if ! code=$(...); then`), and assert the `.status` write happened. |

### Recipe / traceability
| id | finding |
|---|---|
| **MF-2** | All 10 `attempt1-*` `.http` recipes name the **attempt-2** request bodies; the attempt-1 bodies were overwritten by `mkreq2.py` and are gone. Driven: 10/10 replay to a *different* refusal. A 400 saying `isInterestRecalculationEnabled` is mandatory is paired with a body that contains it. |
| **MF-8** | `req/disburse-086-nopaymenttype.json` is an **undisclosed** orphan — hashed into the manifest, referenced by no observation. (`upd-070`, `upd-071` are orphans too but are disclosed.) |
| **MF-10** | `A2-prod-066`'s recorded **404** no longer reproduces (now **403**) because A2-3's own `A2-111` retype reordered validation. The corpus is order-dependent in the refusal *reason*, not only in the *ids* — `CAPTURE-PLAN.md` discloses only the latter. |
| **MF-11** | `A2-bad-045`'s recorded body embeds a burned identity value inside the leaked PostgreSQL `Failing row contains (20, …)`. It can never be a byte-exact golden vector, not even against Fineract. Record it as a **shape** vector (globalisation code + column + constraint), never bytes. |

### Guard scope
| id | finding |
|---|---|
| **MF-3** | `manifest.py verify` passes vacuously on empty input: 0 entries ⇒ `OK: 0 files match` ⇒ exit 0. Fix: refuse when the manifest is empty, and pin the expected entry count (406). |
| **MF-4** | `manifest.py` is non-recursive; a fabricated observation in `out/<subdir>/` is not caught. Fix: `os.walk`. |
| **MF-5** | The manifest covers neither `CAPTURE-PLAN.md` (all seven findings), nor the `.sh`/`.py` rig, nor itself. Driven: appending *"MNT rounds HALF_EVEN and money may be stored as float"* to `CAPTURE-PLAN.md` and tampering with `manifest.py` both leave the guard GREEN. |

### Prose / counts (obligations under P-5, `.softhouse/gates-proposed-answers.md`)
| id | finding |
|---|---|
| **MF-6** | "23 assertions" → the gate emits **22 PASS**, 0 FAIL. |
| **MF-7** | "327 observations" is a **file** count. True: **108 HTTP exchanges** (98 excluding `attempt1-*`) + **3** SQL dumps. 406 manifest entries is correct. |
| **MF-9** | Finding 2 overstated. "can never disburse" / "every later disbursement fails permanently" → **only through the duplicated payment type**; omitting `paymentTypeId` disbursed loan 3 at HTTP 200. |
| **MF-12** | Finding 7 understated. Add: posted journal entries **retroactively re-render** under a retyped GL account, because `acc_gl_journal_entry` stores no classification. |

### Endorsed without change
Findings **3** (resolution order — independently re-confirmed: my fallback disbursement credited
GL 2 via product 27's `payment_type IS NULL` row), **4**, **5**, **6**, the two contract flags
(raw PostgreSQL text on the wire; `usage` omission reaching the database), and the entire
"planned but NOT captured" table, which is honest and unusually specific.

---

## 9. Disclosure — state I changed on the shared `gerege` tenant

Required, because it means A2-3's corpus no longer replays identically from this point:

- **`m_loan` id 3** went from `loan_status_id` 200 (approved) to **300 (active)**: my control
  disbursement for §5. Loan transaction 7 and **journal entries 9 and 10** (DEBIT GL 4 1200000.000000
  / CREDIT GL 2 1200000.000000, entry_date 2026-02-01) now exist.
- ~14 replayed refusals burned identity values in `acc_gl_account` and `m_product_loan` sequences.
  **No rows were committed** — `max(acc_gl_account.id)` is still 24, the same 21 rows A2-3 recorded.
- No container was restarted, rebuilt or re-seeded. No GL account, mapping or financial-activity
  row was created, updated or deleted by me.
- `A2-086-disburse-loan3-dupchannel` replayed **byte-identical before** this disbursement; it
  differs after it. That diff is mine, not A2-3's.

## 10. Guards I drove, and the one I could not make fail

| guard | drove RED? |
|---|---|
| Path B preconditions, tenant `default` | **YES** — exit 1, 5 breaches |
| Path B preconditions, nonexistent tenant | **YES** — exit 1, 10 breaches, incl. an explicit "INSPECTED NOTHING" refusal |
| Path B canary, `CANARY_REQ` unset / wrong digest / `/dev/null` / `CANARY_EXPECT` override | **YES** — all four refused |
| `manifest.py verify` — mutate / delete / add at top level | **YES** — all three caught |
| `manifest.py verify` — **empty input** | **could not make it fail** → passes vacuously (MF-3) |
| `manifest.py verify` — fabricated file in a subdirectory | **could not make it fail** (MF-4) |
| `manifest.py verify` — tampered `CAPTURE-PLAN.md` / tampered `manifest.py` | **could not make it fail** (MF-5) |
| `cap.sh` transport-failure handler | **could not make it fire at all** — dead code (MF-1) |

---

*A2-4. Nothing promoted to `.softhouse/vectors/`. No Go written. No container restarted.*
