# Reproducing Path B captures

Unlike Path A (in-process seam, no database), Path B drives the **running Fineract server over
PostgreSQL**. The PostgreSQL-only rule governs it directly: the stack must be the `postgresql` compose
profile, and the assertions below are part of the recipe, not optional checks.

## Preconditions — FAIL THE RUN, do not assume

> **CLOSED per T22 audit P0-4 (applied by T36, 2026-08-18, against the running server).** These were
> previously prose checks a reader could skip, and they did not cover the two settings that actually decide
> the arithmetic. They are now an **executable script that exits non-zero on a breach and names it**, and the
> capture recipe below refuses to run unless it exits 0.

```sh
# 15 assertions, every one read from the running server, its deployed bytecode, or its
# PostgreSQL rows.  Exits 0 only if ALL hold; exits 1 and prints each breach otherwise.
CANARY_REQ=t22-audit/req/calc-pmode2-gerege.json \
  sh t36/preconditions.sh gerege  ||  exit 1     # <- a breach ABORTS; do not capture
```

What it asserts, and why each one can invalidate a capture:

| # | Assertion | Breach means |
|---|---|---|
| P1 | `fineract:latest` digest = `sha256:e596339626bf…` | not the pinned oracle |
| P2 | jar `git.commit.id` = `426a23544e…`, `git.dirty=false` | different build, or built from a dirty tree |
| P3 | **`MoneyHelper.PRECISION` = 19**, read by `javap` from the **deployed** `fineract-core` jar | the `MathContext` is not the ratified one |
| P4 | `actuator/health` = `UP` | the server is not serving |
| P5 | `org.postgresql.Driver` + `jdbc:postgresql://…`, and **0** hits for `ojdbc\|oracle.jdbc\|:1521\|com.mysql.cj\|mariadb\|go-sql-driver` in the container env | a prohibited engine (Oracle Database / MySQL / MariaDB) is in play |
| P6 | 0 prohibited driver jars inside `fineract-provider.jar`; a PostgreSQL driver present | ditto |
| P7 | PostgreSQL server version starts `PostgreSQL 18.3` | different engine build |
| P8 | the tenant row exists | capturing against a tenant that is not there |
| P9 | **`tenants.timezone_id` ∈ {`Asia/Ulaanbaatar`, `Asia/Hovd`}** | a non-Mongolian zone; fatal for any clock-sensitive capture. The **zone id** is asserted — never an offset |
| P10 | **`c_configuration.rounding-mode` = 4 (HALF_UP)** and the row enabled | `6` = HALF_EVEN is not production-representative |
| P11 | **`tenant_server_connections.schema_connection_parameters` is empty** | the stock `default` row carries MySQL-era JDBC parameters |
| P12 | tenant `schema_server_port` = `5432` | `1521` = Oracle Database, `3306` = MySQL — both prohibited |
| P13 | **this JVM run logged `Initialized rounding mode for tenant …: HALF_UP`** since `State.StartedAt` | `MoneyHelper` caches the mode per tenant at startup, so a DB row edited after boot is **inert** |
| P14 | **effective-mode canary**: the half-cent tie request returns period-1 interest `20925.05` | the arithmetic in force is not HALF_UP (`20925.04` = HALF_EVEN) |
| P15 | MNT seeded `decimal_places = 2` and enabled for the tenant | wrong minor unit |

P13 and P14 exist because P10 alone is **not** proof: configuration is not behaviour. P14 is the strongest of
the fifteen — it is the arithmetic itself answering.

**The script is demonstrably failable.** Run against the stock `default` tenant it exits 1 with five
breaches — Kolkata timezone, `rounding-mode = 6`, HALF_EVEN in force, MySQL-era `schema_connection_parameters`,
and canary `20925.04`. Transcript: `t36/out/preconditions-default-NEGATIVE.txt`. Those five are exactly the
defects that made the original Path B corpus inadmissible.

Any breach **invalidates the capture** — it would mean the run did not execute the pinned oracle, did not
execute it on the mandated engine, or did not execute it at the ratified `MathContext(19, HALF_UP)`.

## Which tenant to capture on

**`gerege`** — `Asia/Ulaanbaatar`, `rounding-mode = 4` (HALF_UP), empty `schema_connection_parameters`.
**Never `default`**: it is `Asia/Kolkata` at HALF_EVEN and fails P9/P10/P11/P13/P14.

## Environment

```sh
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='          # mifos:password, stock demo credentials
# CHANGED by T36 (T22 P0-6): captures are taken on the production-settings tenant, never `default`.
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
```

## Fixture setup (idempotent only if the tenant is fresh — ids are assumed below)

```sh
# Enable MNT alongside the stock USD
curl -sk -X PUT "$B/currencies" -H "$A" -H "$T" -H "$CT" -d '{"currencies":["MNT","USD"]}'

# Clients. `fullname` is used deliberately so the fixture does not assert a first/last name shape.
# client 1 activated 2026-01-01; client 2 activated 2023-01-01 (needed for a 2024 leap-year term)
curl -sk -X POST "$B/clients" -H "$A" -H "$T" -H "$CT" -d '{"officeId":1,"fullname":"Path B Fixture Borrower","legalFormId":1,"active":true,"activationDate":"01 January 2026","locale":"en","dateFormat":"dd MMMM yyyy"}'
curl -sk -X POST "$B/clients" -H "$A" -H "$T" -H "$CT" -d '{"officeId":1,"fullname":"Path B Leap Fixture","legalFormId":1,"active":true,"activationDate":"01 January 2023","locale":"en","dateFormat":"dd MMMM yyyy"}'

# Loan products 1-4, verbatim payloads committed in req/
for f in product-1-baseline product-2-multiplesof100 product-3-diycs-fullleapyear product-4-diycs-feb29only; do
  curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" -d @req/$f.json
done
```

Products 1 and 2 differ **only** in `installmentAmountInMultiplesOf` (null vs 100).
Products 3 and 4 differ **only** in `daysInYearCustomStrategy` (`FULL_LEAP_YEAR` vs `FEB_29_PERIOD_ONLY`);
both also set `interestCalculationPeriodType=0` (Daily) and Actual/Actual day counts, without which the
field cannot affect the schedule.

Confirm each field actually persisted before trusting a comparison — the server accepts and ignores some
inputs, which is the entire reason Path B exists:

```sh
curl -sk "$B/loanproducts/2" -H "$A" -H "$T" | grep -o '"installmentAmountInMultiplesOf":[^,]*'
curl -sk "$B/loanproducts/3" -H "$A" -H "$T" | grep -o '"daysInYearCustomStrategy":{[^}]*}'
```

## The captures

> **CORRECTED per T22 audit P0-5 (applied by T30, 2026-08-18 — no oracle required).** The loop below
> previously wrote `-o out/B-$n-*-raw.json`. A shell glob in an output path does **not** do what it looks like
> it does: `*` cannot expand against a file that does not exist yet, so `curl` creates files named literally
> `B-01-*-raw.json` — never the committed names. Running the old recipe verbatim could not reproduce the
> corpus. The loop now names each output file explicitly. It also captures **`%{http_code}`** and **fails the
> capture on any status other than `200`**: `curl -s … -o file` discards the status entirely, so before this
> fix a `400` error body would land in `out/` looking exactly like a capture.

```sh
set -e
for pair in "01:calc-B-01-baseline:B-01-baseline" \
            "02:calc-B-02-multiplesof100:B-02-multiplesof100" \
            "03:calc-B-03-diycs-fullleapyear:B-03-diycs-fullleapyear" \
            "04:calc-B-04-diycs-feb29only:B-04-diycs-feb29only"; do
  n=${pair%%:*}; rest=${pair#*:}; req=${rest%%:*}; outname=${rest#*:}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
              -H "$A" -H "$T" -H "$CT" -d @req/$req.json \
              -o "out/$outname-raw.json" -w '%{http_code}')
  echo "B-$n  HTTP $code  -> out/$outname-raw.json"
  if [ "$code" != "200" ]; then
    echo "CAPTURE FAILED: B-$n returned HTTP $code — the file in out/ is an ERROR BODY, not a capture." >&2
    echo "Do not commit it, and do not treat it as an observation." >&2
    exit 1
  fi
done

# The committed corpus, for a byte-identity check after the run:
#   713a35601b8909f47640770ba93431a053882b161769c6af35728bacac062009  out/B-01-baseline-raw.json
#   9de8757deeb02476d48e4c84a42b297cc99fab9a286adb505c005ab8d99d02f8  out/B-02-multiplesof100-raw.json
#   892dd6f537ef34f50f6c46258d054e620565951e671b414184f0ffb9f7da58bf  out/B-03-diycs-fullleapyear-raw.json
#   c80f62b01721ab15e994dcf7fca5d5f3f60ada39aa210ca45bbb67b65c724a80  out/B-04-diycs-feb29only-raw.json
sha256sum out/B-0*-raw.json
```

**CLOSED, 2026-08-18 by T36 against the running server** — what stood here was T22 P0-4: the Preconditions
block did not *fail the run* on `c_configuration.rounding-mode = 4` (HALF_UP), on
`tenants.timezone_id ∈ {Asia/Ulaanbaatar, Asia/Hovd}`, or on an empty
`tenant_server_connections.schema_connection_parameters`. All three are now assertions **P10, P9 and P11** of
`t36/preconditions.sh`, which the Preconditions section above runs and which **exits non-zero and names the
breach**. Two assertions T22 did not ask for were added because a DB row is not proof of the arithmetic in
force: **P13** (this JVM run's own `MoneyHelper` init line for this tenant) and **P14** (a behavioural
half-cent canary). The script is demonstrably failable — it exits 1 with five breaches on the stock `default`
tenant (`t36/out/preconditions-default-NEGATIVE.txt`).

**Re-point CLOSED too (T22 P0-6).** The capture set was re-taken on tenant `gerege`
(`Asia/Ulaanbaatar`, HALF_UP) at the ratified `MathContext(19, HALF_UP)`, twice — once against the products
already there and once against four products this task re-created from the same payloads. **All four
responses came back byte-identical to the committed corpus, all eight times.** Machine-readable attestation
(T22 P0-3): `t36/out/recapture-gerege/attestation.json`. Number-by-number diff:
`t36/out/diff-vs-committed.txt`.

`out/*.json` are the **raw response bytes**. The server emits money as JSON *numbers*, not strings, so any
tooling that reads these must treat them as text or exact decimal — parsing to a binary float before
storing would corrupt the vector.

## Gotchas met while building this (each cost a round trip)

- `calculateLoanSchedule` **rejects** `loanScheduleType` / `loanScheduleProcessingType` in the request; they
  are derived from the product. Send them and you get a 400 naming the parameter.
- `allowPartialPeriodInterestCalcualtion` (sic, misspelled in the API) must be **omitted** for a progressive
  product; sending it fails validation.
- `isInterestRecalculationEnabled` is mandatory on product creation even when false.
- `submittedOnDate` must be **≥ the client's activation date** and **≤ the current business date**. This is
  why the leap-year captures need a separately activated client — the stock fixture client cannot back-date
  to 2024, and 2028 is rejected as future.

- **A tenant cannot be added without restarting the server.** `MoneyHelper` caches the rounding mode per
  tenant at startup, and the only runtime re-init endpoint (`InternalConfigurationsApiResource:87-92`) is
  `@Profile(TEST)` and absent from this image. So provisioning a new tenant costs a restart — which is why
  T36 reused the already-provisioned `gerege` rather than creating another while a second worker depended on
  the server staying up. Adding **products** and issuing **loan applications** need no restart.

## The whole recipe, executable (T36)

```sh
sh   t36/preconditions.sh gerege     # 15 fail-the-run assertions        (T22 P0-4)
                                     # HARDENED BY T76 - see below; the canary is now
                                     # pinned by CONTENT and its expectation is a CONSTANT
python3 t36/attest.py gerege pathb   # preconditions + capture + attestation.json (T22 P0-3, P0-6)
sh   t36/rundiff.sh                  # number-by-number diff vs the committed corpus
sh   t36/run-invariants.sh           # T22's ten property invariants
python3 t36/t36_rederive_check.py    # re-checks T30's from-source re-derivation of B-03/B-04
sh   t36/mutation-test.sh            # proves the comparator can fail
sh   t36/recreate-products.sh        # re-creates the four products and re-issues the four applications
sh   t36/emiloop-probe.sh            # EMI re-adjust-loop probes           (T22 P1-11, 2nd clause)
python3 t36/t36_emiloop_verdict.py   # loop-fired verdict vs the no-loop model
```

Findings and their evidence: `PATHB-REPORT.md`.

---

## HARDENED by T76 (2026-08-20) — the preconditions could be talked out of failing

T22 P0-4 asked that the recipe **fail the run** rather than sit in prose, and T36 delivered that. Two
ways remained to make it pass while the arithmetic in force was the wrong one. Both are closed, and both
closures are demonstrated by an attack transcript rather than asserted:

| attack | what it tried | result | transcript |
|---|---|---|---|
| A | capture on the stock `default` tenant | **exit 1, 5 breaches** (Kolkata, `rounding-mode=6`, HALF_EVEN in force, MySQL-era `schema_connection_parameters`, canary `20925.04`) | `t76/out/attack-A-default.txt` |
| B | `CANARY_EXPECT=20925.04` — tell the script HALF_EVEN is what it should expect | **CORRECTED BY T80.** T76's transcript did not run the command in this caption: it ran a *decoy* variable, `CANARY_EXPECT_OVERRIDE`, which T76 itself had introduced and which no attacker would set, and its documented count of 6 breaches did not reproduce (T77 measured **5**). The tripwire now watches `CANARY_EXPECT` itself, and the caption's own command now measures **exit 1, 6 breaches** on `default` and **exit 1, 1 breach** on `gerege` | `t80/out/attack-4a-expect-override-default-sh.txt`, `t80/out/attack-4b-expect-override-gerege-sh.txt`; the now-inert decoy: `t80/out/attack-4c-decoy-variable-sh.txt` |
| C | swap the canary for a request that is **not** a half-minor-unit tie (principal `1162502.78`), so `20925.05` comes back under either mode | **THIS CLOSURE WAS FALSE; SUPERSEDED BY T80.** The "content pin" was four `grep -qF` **prefix** matches and a sha256 that was **printed but never compared**. T77 defeated it with one character (`1162502.5` → `1162502.55`) and reached *ALL PRECONDITIONS HOLD, exit 0* — and, on the HALF_EVEN `default` tenant, *PASS effective rounding mode canary (= HALF_UP)*. The request is now pinned by **digest comparison** against a literal in the script, and a mismatch means the canary is **not sent at all** | superseded transcript `t76/out/attack-C-swapped-canary.txt`; live closure `t80/out/attack-2a-mutated-canary-gerege-sh.txt`, `t80/out/attack-2b-mutated-canary-default-sh.txt`, `t80/out/attack-3a-swapped-canary-gerege-sh.txt` |
| D | omit the canary entirely | **exit 1** — "A DB row is not proof of the mode in force" | `t76/out/attack-D-nocanary.txt` |

The honest run on `gerege` still exits **0** with **22 PASS** and no FAIL (`t76/out/preconditions-gerege.txt`).

**Two small generalisations to `t36/attest.py`, for provenance rather than function:** `ATTEST_OUT` lets a
later task write its own evidence directory instead of overwriting the capture set a reviewer diffs
against, and `ATTEST_TASK` / `ATTEST_BRANCH` stop a sidecar produced by a later task from claiming T36
produced it. Default behaviour is byte-for-byte unchanged.

**One operational note that cost a round trip:** `conformance.sh` has a `#!/bin/bash` shebang and uses
process substitution. Invoked as `sh .softhouse/conformance.sh` it dies with a syntax error at line 104 and
**exits 2** — which is the harness's own "nothing was graded" code and reads exactly like a real fatal
verdict. Run it as `bash .softhouse/conformance.sh` or `./.softhouse/conformance.sh`.

---

## HARDENED by T80 (2026-08-20) — the canary did not bite, and the abort was unreachable

T77 rejected T76's §3 by **attacking it**, which is the only test that means anything here. Two P0s, both
now closed and both closed by a run rather than by a sentence. Every transcript below is the verbatim
output of `t80/run-attacks.sh` / `t80/happy-path.sh`, exit code included.

**P0-A — the canary is pinned by DIGEST COMPARISON, not by substring.** `grep -qF '"principal": 1162502.5'`
also matches `1162502.55`, and `1162502.55 × 0.018 = 20925.0459` is **not** a half-minor-unit tie, so it
answers `20925.05` under HALF_UP *and* HALF_EVEN. The assertion was a tautology. `preconditions.sh` now
computes the sha256 of the file it is about to POST and compares it to the literal
`2a6621be…52154` recorded in the script. Two operands, only one of which a caller can reach.
On mismatch the canary is **not sent**, so the sentence *"PASS effective rounding mode canary … (= HALF_UP)"*
is unreachable except on the exact pinned tie.

**P0-B — `recapture.sh` can now actually abort, and files its output under the tenant it used.** `bad()`
writes FAIL to **stderr**; the old gate `tee`'d only **stdout** and grepped that, so its `grep -c '^  FAIL'`
was always `0` and the ABORT was dead code. T77 ran `TENANT=default sh recapture.sh` and got five breached
preconditions — including a canary that **404'd**, i.e. the mode in force was never established — no abort,
all four captures taken, exit 0, written into a **hard-coded** `recapture-gerege` directory. The gate now
tests the **exit status** of `preconditions.sh` and, independently, greps a transcript that captures **both**
streams; and `O` derives from `$TENANT`, an explicit `RECAPTURE_OUT` must still be *named* for the tenant,
and a `CAPTURED-FROM-TENANT` stamp refuses a cross-tenant overwrite.

| # | attack | result | transcript (`t80/out/`) |
|---|---|---|---|
| 1a | `TENANT=default sh t36/recapture.sh` | **exit 1**, 5 breaches, `ABORT`, **zero** captures, filed under `recapture-default` | `attack-1a-wrong-tenant-sh.txt` |
| 1b | `TENANT=default RECAPTURE_OUT=…/recapture-gerege …` | **exit 1** at the name guard, *before* the preconditions run | `attack-1b-wrong-tenant-into-gerege-dir-sh.txt` |
| 1c | directory already stamped `gerege`, re-used for a `default` capture | **exit 1** at the stamp | `attack-1c-stamp-mismatch-sh.txt` |
| 2a | canary principal `1162502.5` → `1162502.55`, tenant `gerege` | **exit 1**, 1 breach: `DIGEST MISMATCH`, both digests named | `attack-2a-mutated-canary-gerege-sh.txt` |
| 2b | the same mutation on the HALF_EVEN `default` tenant | **exit 1**, 5 breaches; the HALF_UP PASS line is **absent** | `attack-2b-mutated-canary-default-sh.txt` |
| 3a | canary swapped for another committed, valid, non-tie request | **exit 1**, digest mismatch, canary not sent | `attack-3a-swapped-canary-gerege-sh.txt` |
| 3b/3c | canary path missing / unset | **exit 1** each | `attack-3b-…`, `attack-3c-…` |
| 4a/4b | `CANARY_EXPECT=20925.04` on `default` / `gerege` | **exit 1**, 6 and 1 breaches | `attack-4a-…`, `attack-4b-…` |
| 4c | T76's decoy `CANARY_EXPECT_OVERRIDE` | **exit 0** — it is now inert, as it should be | `attack-4c-decoy-variable-sh.txt` |
| 4 | every attack re-run with the recipe under `bash` instead of `sh` | **11/11 transcripts byte-identical** after normalising the interpreter name | `attack-4-shell-invariance.txt` |
| 5 | happy path on `gerege` | **exit 0**, **22 PASS / 0 FAIL**, four captures **byte-identical across six independently produced sets** | `attack-5-happy-path.txt` |

Reproduce the whole thing:

```sh
sh   .softhouse/capture/pathb/t80/run-attacks.sh      # SH=sh   by default
SH=bash bash .softhouse/capture/pathb/t80/run-attacks.sh
sh   .softhouse/capture/pathb/t80/shell-invariance.sh
sh   .softhouse/capture/pathb/t80/happy-path.sh
```

**The `sh` / exit-2 note above still stands and is NOT fixed here:** invoke the conformance harness only as
`bash .softhouse/conformance.sh`. Under `sh` it exits **2**, the harness's "oracle unusable" fatal code,
which a program driver would read as a legitimate oracle-down park. That is a different script (T77
P2-T77-5) and outside T80's scope.

### The T76 additions to the recipe

```sh
# independent re-capture into a T76-owned directory, with its own attestation sidecar
ATTEST_TASK=T76 ATTEST_BRANCH=softhouse/T76-pathb-gerege-recapture \
  ATTEST_OUT="$PWD/t76/out/recapture-gerege" python3 t36/attest.py gerege pathb

# the ten T22 invariants, then T76's I7 mirror-column invariant the ten do not cover
python3 t22-audit/t22_invariants.py t76/out/recapture-gerege/B-0*-raw.json
python3 t76/t76_mirror_invariant.py t76/out/recapture-gerege/B-0*-raw.json

# B-01 vs the PROMOTED Path A vector P-MNT-1M2, and both differentials, in exact minor units
python3 t76/t76_crosscheck.py
```
