# T36 — Path B admissibility: the parked P0s, closed against the live reference oracle

**Task:** T36, branch `softhouse/T36-pathb-admissibility`.
**Fire:** local `20260818-230002`, Buyan's Mac. **The reference oracle (Fineract) WAS reachable and every
claim below is an observation made on it.** Oracle Database is prohibited and appears nowhere; the only
engine touched is **PostgreSQL 18.3**.
**Oracle of record:** `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`,
jar `git.commit.id = 426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`
[VERIFIED: `t36/out/recapture-gerege/attestation.json` → `oracle`].

> **NOTHING WAS PROMOTED to the parity vector store.** DEC-1 is at revision 6 and UNRATIFIED (gate G-1).
> Everything here is RAW OBSERVED. No expected value was authored, extrapolated or "corrected"; where a
> model was used it was used only to *select candidates* to put to the oracle, and that is said each time.

---

## What I closed

### T22 P0-3 — machine-readable attestation sidecar — **CLOSED**

`t36/attest.py` → **`t36/out/recapture-gerege/attestation.json`** (and a second one for the probe set at
`t36/out/emiloop/attestation.json`). It **drives the capture itself**, so the request/response digests and
UTC timestamps describe one run rather than being bolted onto files afterwards. Every field is read from the
running server, its container, its **deployed bytecode**, or its PostgreSQL rows; an unreadable field is
recorded `null` with a note, never guessed (the `notes` array is empty on both runs).

What it actually recorded [all VERIFIED: `t36/out/recapture-gerege/attestation.json`]:

| Field | Observed |
|---|---|
| tenant identifier | `gerege` |
| tenant `timezone_id` | **`Asia/Ulaanbaatar`** (zone id recorded; no offset hard-coded anywhere) |
| `c_configuration.rounding-mode` | **4**, enabled — `RoundingMode.valueOf(4)` = **HALF_UP** |
| rounding mode **in force** | `HALF_UP`, from **this JVM run's own** `MoneyHelper` init line at `09:53:01.711Z` |
| `MoneyHelper.PRECISION` | **19**, read by `javap -constants` from the **deployed** `fineract-core-1.16.0-SNAPSHOT.jar` inside the running container — not from source |
| effective `MathContext` | **`MathContext(19, HALF_UP)`**, `matches_ratified_production_setting: true` |
| `schema_connection_parameters` | **empty string** |
| tenant `schema_server_port` | `5432` |
| Fineract build | image digest + `git.commit.id` + `git.dirty=false` + `1.16.0-SNAPSHOT` + branch `develop` |
| JVM | Zulu `21.0.11+10-LTS`, read *inside* the container |
| PostgreSQL | `PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) … aarch64`, `server_version_num 180003`, image `postgres:18.3` |
| driver | `org.postgresql.Driver`, `jdbc:postgresql://db:5432/fineract_tenants`; **0** prohibited-engine hits in container env, **0** prohibited driver jars in the boot jar |
| per capture | request file + SHA-256 + bytes, response file + SHA-256 + bytes, HTTP status, UTC timestamp, committed-corpus digest and whether it matches |
| products | the four `m_product_loan` rows **as persisted**, plus a SHA-256 of each full row |

Two deliberate choices worth reviewing: money columns are serialised as **exact text**
(`"principal_amount": "1200000.000000"`) because parsing a money column to a binary float even just to
re-serialise it would put a float in a monetary artefact; and `matches_committed_corpus_bytes` is `null`,
not `false`, when there is no committed counterpart, so absence never reads as a mismatch.

**Finding to report loudly, per the brief: there is none of the kind feared.** The re-capture did not run at
some other setting that had to be normalised — it ran at exactly `(19, HALF_UP)` and the attestation says so
from primary sources. The **adverse** fact remains T22's, unchanged and restated here: the **originally
committed** `B-01`..`B-04` were taken on `default` at `(19, HALF_EVEN)` / `Asia/Kolkata`. That is why the
re-capture was needed at all.

### T22 P0-4 — fail-the-run preconditions — **CLOSED, in `REPRODUCE.md` itself**

`t36/preconditions.sh` — 15 assertions, written against the running server, `exit 1` on any breach with the
breach named and an explicit "DO NOT CAPTURE … do not commit it, do not treat it as an observation, do not
normalise it". `REPRODUCE.md:105-110`'s drafted-open block is **replaced** by the closure; the Preconditions
section now runs the script with `|| exit 1` and tabulates what each assertion means.

The five that were missing and now exist: **P9** timezone ∈ {`Asia/Ulaanbaatar`, `Asia/Hovd`}; **P10**
`rounding-mode = 4` and enabled; **P11** `schema_connection_parameters` empty; plus two I added because a DB
row is *not* proof of the arithmetic in force — **P13**, this JVM run's own `MoneyHelper` init line since
`State.StartedAt` (the mode is cached per tenant at startup, so a row edited after boot is inert), and
**P14**, a **behavioural canary**: the half-cent-tie request (`1,162,502.50 × 0.018 = 20,925.045`) must come
back `20925.05`. P14 is the strongest of the fifteen — it is the arithmetic itself answering.

**Proven failable, which is the whole point.** Run against the stock `default` tenant it exits **1** with
**five** breaches — `Asia/Kolkata`, `rounding-mode = 6`, HALF_EVEN in force, the MySQL-era
`schema_connection_parameters`, and canary `20925.04`
[VERIFIED: `t36/out/preconditions-default-NEGATIVE.txt`]. Those five are precisely the defects that made the
original corpus inadmissible. Incidentally the canary **re-observes T22's discriminating result** on both
tenants in one run: `20925.05` on `gerege`, `20925.04` on `default`.

### T22 P0-6 — re-point at a production-settings tenant and re-capture — **CLOSED, twice over**

I did **not** create a tenant and did **not** restart anything: `gerege` (`Asia/Ulaanbaatar`, HALF_UP) was
already provisioned by T22 and is live in the current JVM. Adding a tenant would have cost a container
restart — `MoneyHelper` caches per tenant at startup and the only runtime re-init endpoint,
`InternalConfigurationsApiResource:87-92`, is `@Profile(TEST)` and absent from this image — and a second
worker was running Path A captures on this server for the whole fire. **`docker compose down` was never run,
nothing was restarted or reconfigured, and no database was dropped or truncated.**

Two independent re-captures, both after the preconditions passed:

1. **`t36/recapture.sh`** — the committed calc requests sent **byte-verbatim** (`productId` 1–4 land as-is on
   this tenant) against the products T22 created from the committed payloads.
2. **`t36/recreate-products.sh`** — because arm 1 leans on another task's fixture, I **re-created all four
   products** from the same payloads (products **13–16**, `T61`..`T64`) and **re-issued all four loan
   applications** against them. Only `name`/`shortName` were changed, by *text* substitution on those two
   lines (Fineract rejects a duplicate short name), so every numeric literal stayed byte-identical; the
   script asserts exactly 4 changed diff lines per payload and aborts otherwise. The differential columns
   were read back **from PostgreSQL**, not from the create response: `13 NULL/NULL`, `14 multiplesOf=100`,
   `15 FULL_LEAP_YEAR`, `16 FEB_29_PERIOD_ONLY`.

### T22 P1-11, second clause — **CLOSED. The EMI re-adjust loop is now pinned by observation.**

This is the substantive new result of the task. Entry condition
`|emiDifference| × 100 > originalEmi.copy(floor(n/2))` — and, per the trap that retracted three earlier probe
scripts, `Money.copy(double)` **replaces** the amount [VERIFIED: `Money.java:220-221` → `:216-217` → the
private ctor `:40-52`, which `setScale`s to the currency's decimal places], so at `n = 12` the RHS is
**`Money(6.00)`**, not `EMI × 6`. The loop therefore needs `|residual| > 0.06`; the four corpus captures sit
at `±0.05` and never fire.

I searched whole-MNT principals with T22's audited from-source model (which does **not** implement the loop)
to *pick candidates*, then put nine of them to the oracle — product 1, no `multiplesOf`, everything else
identical to `B-01`. Observed [VERIFIED: `t36/out/emiloop/verdict.txt`, raw at `t36/out/emiloop/`]:

| principal MNT | no-loop model EMI | **OBSERVED EMI** | observed final installment | verdict |
|---|---|---|---|---|
| 1,200,000 (control) | 112,082.37 | 112,082.37 | 112,082.40 | cannot fire (residual `+0.03`); byte-identical to `B-01` |
| **1,200,001** | 112,082.47 | **112,082.46** | 112,082.51 | **LOOP FIRED** |
| **1,200,004** | 112,082.75 | **112,082.74** | 112,082.80 | **LOOP FIRED** |
| **1,200,027** | 112,084.89 | **112,084.90** | 112,084.84 | **LOOP FIRED** |
| 1,200,033 | 112,085.45 | 112,085.45 | 112,085.52 | enters, does not adopt |
| **1,200,039** | 112,086.01 | **112,086.02** | 112,085.96 | **LOOP FIRED** |
| 1,200,045 | 112,086.58 | 112,086.58 | 112,086.51 | enters, does not adopt |
| **1,200,054** | 112,087.42 | **112,087.41** | 112,087.47 | **LOOP FIRED** |
| **1,200,189** | 112,100.03 | **112,100.02** | 112,100.06 | **LOOP FIRED** |

On the six marked rows the oracle **refutes the no-loop model by one minor unit on every one of periods
1–11** and matches a model that implements the loop. `1,200,033` and `1,200,045` cross the entry condition
but back out at `hasLessEmiDifference` (`:1289-1291`) — both behaviours are now witnessed. Ten property
invariants **ALL PASS on all nine** captures [VERIFIED: `t36/out/emiloop/invariants.txt`].

**Consequence for DEC-1 and the Go port:** a port that implements `multiplesOf` rounding and residual
absorption but not the re-adjust loop returns `112,082.47` where the oracle returns `112,082.46` on a plain
12-month MNT loan of 1,200,001₮. The divergence is one tugrik-cent per installment, on ordinary input, and no
vector before today could see it. The two non-adopting rows are as important as the six adopting ones — they
pin the `hasLessEmiDifference` guard, which a naive implementation would omit.

### Supporting work (not asked for, cheap, and it makes the above checkable)

- **`t36/t36_diff.py`** — exact-Decimal, integer-minor-unit, zero-tolerance comparison of **every** JSON leaf,
  distinguishing a *moved number* from a *scale-only* textual difference from a *structural* difference.
- **`t36/mutation-test.sh`** — proves that comparator can fail: one minor unit flipped in a copy of a
  re-capture makes it exit non-zero and name the leaf [VERIFIED: `t36/out/mutation-test.txt`]. T22 found a
  checker whose verdict was hard-coded to PASS; a clean verdict from an unfailable tool is worth nothing.
- **`t36/run-invariants.sh`** — T22's ten invariants (I1–I6, S1–S4) re-run on the re-captures: **ALL PASS**.
- **`t36/t36_rederive_check.py`** — re-points T30's from-source re-derivation at the new captures without
  modifying it (it is outside this task's write scope).

---

## What I could not close (and why)

- **Nothing in the brief was left unattempted, and no attempt failed.** All four deliverables closed.
- **What remains open is not mine to close.** Promotion of `B-01`..`B-04` (or the new EMI-loop captures) to
  the parity vector store is blocked by **gate G-1**: DEC-1 is at revision 6 and unratified. Admissibility is
  a precondition for promotion, not the same thing as it.
- **A second capture-set attestation schema decision I made rather than escalated** (PRODUCT-class, per
  CLAUDE.md "choose and recommend, do not ask"): the sidecar is `attestation.json` beside the raw captures,
  schema `gerege-nbfi/pathb-attestation/v1`, one per capture set. Alternative rejected: embedding provenance
  in the capture files themselves, which would corrupt the raw response bytes and destroy byte-identity as an
  evidence channel. Reversible before ratification.
- **`Asia/Hovd` (+07) is still unexercised.** Gerege operates in two zones; every capture on record is
  `Asia/Ulaanbaatar`. The preconditions *accept* either, so the recipe is ready, but no Hovd tenant exists and
  creating one costs a restart. Harmless for these four vectors (all dates are explicit civil dates), but it
  must be done before any clock-sensitive capture — COB, accruals, arrears, delinquency.
- **Fineract's stale `default` tenant row still carries MySQL-era JDBC parameters.** I did **not** touch it —
  another worker was live on that tenant. It is inert (pgjdbc ignores unknown URL properties, and no MySQL
  driver exists anywhere in the stack), and the preconditions now **refuse to capture** on a tenant carrying
  them. Recommend leaving `default` alone permanently and capturing only on `gerege`.

---

## Attestation

Canonical machine-readable form: **`.softhouse/capture/pathb/t36/out/recapture-gerege/attestation.json`**
(and `.../t36/out/emiloop/attestation.json`). Summary of the run that produced the re-capture:

```
capture path      Path B — running Fineract server (REST + PostgreSQL)
tenant            gerege  |  Asia/Ulaanbaatar  |  schema fineract_gerege  |  port 5432
rounding mode     c_configuration.rounding-mode = 4 (HALF_UP), enabled
                  in force this JVM run: HALF_UP  (MoneyHelper init line, 2026-08-18T09:53:01.711Z)
                  confirmed behaviourally: half-cent canary -> 20925.05   (HALF_EVEN would give 20925.04)
precision         MoneyHelper.PRECISION = 19, read by javap from the DEPLOYED fineract-core jar
MathContext       MathContext(19, HALF_UP)   == ratified production setting
schema_connection_parameters   ""  (empty)
image             sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a, created 2026-08-17T11:29:56Z
jar               git.commit.id 426a23544e8426a38ae43ae404670a0a7e85b9eb, git.dirty false, 1.16.0-SNAPSHOT
JVM               Zulu 21.0.11+10-LTS (read inside the container)
PostgreSQL        18.3 (Debian 18.3-1.pgdg13+1) aarch64, server_version_num 180003, image postgres:18.3
driver            org.postgresql.Driver, jdbc:postgresql://db:5432/fineract_tenants
prohibited engines  0 hits in container env; 0 prohibited driver jars in the boot jar
MNT               decimal_places 2, enabled  (ISO 4217 496, minor unit 2)
```

Per-capture digests, all HTTP 200, captured 2026-08-18T15:13Z:

| id | request SHA-256 (first 16) | response SHA-256 | == committed corpus |
|---|---|---|---|
| B-01 | `e958d0d813ed409f` | `713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009` | **yes** |
| B-02 | `17775e019188e113` | `9de8757deeb02476d48e4c84a42b297cc99fab9a286adb505c005ab8d99d02f8` | **yes** |
| B-03 | `4b187ab177a0c1fb` | `892dd6f537ef34f50f6c46258d054e620565951e671b414184f0ffb9f7da58bf` | **yes** |
| B-04 | `7f8b717611946e8a` | `c80f62b01721ab15e994dcf7fca5d5f3f60ada39aa210ca45bbb67b65c724a80` | **yes** |

**Facts for `.softhouse/reference-oracle.md` (I did not edit it — out of my write scope; the orchestrator
folds these in):**

1. Path B's **two named gaps are closed**. The file currently says "(1) the tenant timezone is `Asia/Kolkata`
   … (2) tenant rounding mode and precision are not asserted per capture". Both are now false: captures are
   taken on `gerege` (`Asia/Ulaanbaatar`), and mode/precision are asserted per capture **three ways** — the
   DB row, this JVM run's own init line, and a behavioural canary.
2. The **Path B capture facts** table should read tenant `gerege`, timezone `Asia/Ulaanbaatar`,
   `MathContext(19, HALF_UP)`, and cite `t36/out/recapture-gerege/attestation.json`.
3. T22 P0-3, P0-4 and P0-6 are **CLOSED (T36, fire `20260818-230002`)**; with P0-5 (T30) that is **all four**.
   The line "Three P0 admissibility items are still open" is now stale.
4. **New artefacts created on the oracle by T36** (additive only; the next fire should be able to tell mine
   from the corpus): tenant `gerege` gained loan products **13–16** (`T61` baseline, `T62` multiplesOf 100,
   `T63` FULL_LEAP_YEAR, `T64` FEB_29_PERIOD_ONLY). Nothing else was created, changed or deleted anywhere.
   **No loan was persisted** — `select count(*) from m_loan` is **0** in both `fineract_gerege` and
   `fineract_default`; `calculateLoanSchedule` is a pure calculation endpoint. Product counts after my run:
   `fineract_gerege` 16, `fineract_default` 10 (untouched). Both containers still `Up … (healthy)`.
5. **`MoneyHelper.PRECISION = 19` is now verified against the DEPLOYED artefact**, not only the source:
   `javap -p -constants` over `BOOT-INF/lib/fineract-core-1.16.0-SNAPSHOT.jar` inside the running container
   prints `public static final int PRECISION = 19;`. `MoneyHelper.validateAndConvertRoundingMode`
   (`MoneyHelper.java:182-190`) is `RoundingMode.valueOf(int)`, so ordinal **4 = HALF_UP** — confirmed in
   source and behaviourally.

---

## Re-capture diff vs the committed corpus

**Every number is identical. Nothing moved.**
[VERIFIED: `t36/out/diff-vs-committed.txt`, produced by `t36/rundiff.sh`]

| capture | numeric leaves compared | numbers that moved | scale-only diffs | structural diffs | bytes identical |
|---|---|---|---|---|---|
| B-01 baseline | 319 | **0** | 0 | 0 | **yes** |
| B-02 multiplesOf 100 | 319 | **0** | 0 | 0 | **yes** |
| B-03 `FULL_LEAP_YEAR` | 324 | **0** | 0 | 0 | **yes** |
| B-04 `FEB_29_PERIOD_ONLY` | 324 | **0** | 0 | 0 | **yes** |

The comparison is per-leaf over the whole document (not just totals), read as exact `Decimal`, compared in
**integer minor units**, with no tolerance anywhere and no binary float constructed at any point. It also
separates a genuinely moved number from a merely re-scaled literal (`0` vs `0.00`) — there were none of
either. And the same four SHA-256 digests came back from the **re-created** products 13–16, so the identity
is eight-for-eight, not four.

**Which numbers moved, and why: none, and the reason is now established rather than assumed.**

- **The rounding mode explains nothing here because these four inputs never reach a tie.** That is not an
  assumption: T30 re-derived `B-03`/`B-04` from source at both `(19, HALF_EVEN)` and `(19, HALF_UP)` and got
  identical digits, T22 did the same for `B-01`/`B-02`, and the mode is demonstrably *not* inert on this path
  in general — the half-cent canary splits `20925.05` / `20925.04` between the two tenants on the same
  server, in the same run, today.
- **The timezone explains nothing here because every date in these requests is an explicit civil date**
  (`"01 January 2026"`, `dd MMMM yyyy`). The tenant zone reaches business-date resolution, which these
  requests use only for validation (`submittedOnDate ≤ business date`), not for arithmetic. It **will** be
  load-bearing the moment a capture depends on "today".
- **Nothing else moved either**, so there is no unexplained movement to report. I am stating this as the
  observed outcome, not predicting it: the diff ran, and it ran with a comparator I first proved can fail.

**Does the re-capture still reproduce T30's from-source re-derivation of `B-03`/`B-04`?**
**Yes — CONSISTENT, all four combinations, digit-for-digit** [VERIFIED: `t36/out/rederive-check.txt`]:

| capture | model mode | verdict |
|---|---|---|
| `B-03` `FULL_LEAP_YEAR` | HALF_UP | **CONSISTENT** |
| `B-03` `FULL_LEAP_YEAR` | HALF_EVEN | **CONSISTENT** |
| `B-04` `FEB_29_PERIOD_ONLY` | HALF_UP | **CONSISTENT** |
| `B-04` `FEB_29_PERIOD_ONLY` | HALF_EVEN | **CONSISTENT** |

**There is no contradiction, and therefore no major finding on those numbers.** This is stronger than
re-running T30 on the same bytes would have been only in one respect worth naming honestly: because the new
captures are byte-identical to the committed ones, this check *had* to pass once the digests matched. Its
value is that it would have caught a byte-identical-but-differently-parsed regression, and that it re-states
the consistency at the production setting rather than at the setting the original capture ran at.

---

## Admissibility verdict

**Path B is now ADMISSIBLE as a capture path.** All four T22 P0 items are closed — P0-5 by T30, P0-3 / P0-4 /
P0-6 by this task against the live oracle. Concretely, every condition the audit named is met and evidenced:
the capture set carries a machine-readable attestation read from primary sources; the recipe refuses to run
outside the ratified environment and is proven to refuse; the captures were taken on a production-settings
tenant at `MathContext(19, HALF_UP)` with a Mongolian timezone; the numbers reproduce byte-for-byte across
two independent product fixtures; ten property invariants pass; and the two captures nobody had rebuilt from
source are consistent with T30's re-derivation at the production setting.

**Path B captures are still NOT parity vectors, and I did not make any.** What blocks that is no longer
admissibility:

1. **Gate G-1 — DEC-1 is at revision 6 and UNRATIFIED.** Until the contract is ratified there is nothing for
   a vector to be a vector *of*. Promotion is a separate decision and was explicitly not mine.
2. **Coverage, not correctness.** Every Path B capture on record is a clean, unpaid, single-disbursement
   schedule. Nothing exercises repayments, charges, down payments, multi-disbursement, delinquency, COB, or
   any path through `getDueAmounts`. The corpus grades the two inputs Path A drops and, as of today, the EMI
   re-adjust loop — and nothing else.
3. **`Asia/Hovd` is unexercised**, and no clock-sensitive behaviour has been captured in either zone.
4. **Cutover remains a hard `user` gate** and nothing here speaks to it.

A reviewer should read the verdict as: *the rig is now trustworthy and its provenance is machine-checkable;
the corpus is still small.*

---

## Unverified

Everything material in this handoff is marked `[VERIFIED: …]` above and traces to a committed artefact. The
following are the honest exceptions:

- **`[UNVERIFIED]` — that the six EMI-loop captures are the *smallest* or *most canonical* principals that
  fire the loop.** I scanned 3,000 consecutive whole-MNT principals from 1,200,000 and put nine to the
  oracle; 209 of the 3,000 were predicted to enter the loop. I did not search cents, other terms, other
  rates, or `multiplesOf` shapes. A smaller or tidier witness may exist.
- **`[UNVERIFIED]` — the loop's behaviour at 2 or 3 iterations.** Every firing case I observed converged
  after **one** adopted adjustment. The source allows up to three (`adjustCounter <= 3`, `:1307`); I did not
  find or look for a shape that adopts twice. That sub-behaviour remains unvectored.
- **`[UNVERIFIED]` — the loop's interaction with `installmentAmountInMultiplesOf`.** All nine probes have no
  `multiplesOf`. T22's negative probe (`out-modeprobe/`) shows the loop can be *entered* and immediately
  broken by the multiplesOf re-rounding, but no capture pins a firing loop *combined* with multiplesOf.
- **`[UNVERIFIED]` — that products 13–16 are byte-identical in every column to products 1–4.** I asserted the
  two differential columns from the persisted rows (`installment_amount_in_multiples_of`,
  `days_in_year_custom_strategy`) and that only `name`/`shortName` changed in the request payloads. I did not
  run a full `to_jsonb` column diff of 13–16 against 1–4 the way T22 did for 1–4. The schedules coming back
  byte-identical is strong indirect evidence, but it is indirect.
- **`[UNVERIFIED]` — anything about `Asia/Hovd` on this stack.** The zone exists in the tenant store's
  `timezones` table per T22; I did not re-check it and provisioned no tenant with it.
- **Note for the reviewer, so it is not mistaken for a violation:** the strings `ojdbc`, `oracle.jdbc`,
  `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver` appear in `t36/preconditions.sh` and `t36/attest.py`
  **only inside `grep` patterns that assert those engines are ABSENT**, and both assertions observed **0
  hits**. They are detection, never a driver, dialect or dependency.

---

## Follow-ups

1. **Orchestrator: fold the five numbered facts above into `.softhouse/reference-oracle.md`** (out of my
   write scope). The "two Path B gaps" paragraph and the "three P0 admissibility items are still open"
   sentence are now stale and actively misleading.
2. **`tasks.json` / program state: T22 P0-3, P0-4, P0-6 and P1-11 (both clauses) are CLOSED.** The Path B
   line should say **all four P0s closed**, and the standing `oracle_unreachable` park on these items should
   be lifted.
3. **DEC-1 must carry the EMI re-adjust loop as a normative rule** — with the `Money.copy(double)` trap
   spelled out (RHS is `Money(floor(n/2))`, not `EMI × floor(n/2)`) and the `hasLessEmiDifference` guard,
   both now witnessed by observation. It is currently recorded only as "unpinned behaviour"; it is pinned.
   That is a DEC-1 edit and belongs to whoever owns the contract, not to me.
4. **Capture the two unvectored sub-behaviours** while the oracle is reachable: a shape that makes the loop
   adopt **twice**, and a shape where the loop fires **with** `installmentAmountInMultiplesOf`.
5. **Provision an `Asia/Hovd` tenant on the next fire that can afford a restart**, before any clock-sensitive
   capture. Both zones must be exercised because Gerege operates in both; the preconditions already accept
   either.
6. **Standing rule: capture on `gerege`, never on `default`.** `REPRODUCE.md` now says so and the
   preconditions enforce it. Leave `default` alone rather than "fixing" its MySQL-era
   `schema_connection_parameters` — other work depends on that tenant.
