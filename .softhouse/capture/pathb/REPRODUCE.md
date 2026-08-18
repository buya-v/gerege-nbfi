# Reproducing Path B captures

Unlike Path A (in-process seam, no database), Path B drives the **running Fineract server over
PostgreSQL**. The PostgreSQL-only rule governs it directly: the stack must be the `postgresql` compose
profile, and the assertions below are part of the recipe, not optional checks.

## Preconditions — assert, do not assume

```sh
# 1. The pinned image, same digest all Path A passes used
docker image inspect fineract:latest --format '{{.Id}}'
# must be sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

# 2. PostgreSQL, and ONLY PostgreSQL
docker inspect fineract-fineract-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -iE 'driver|jdbc'
# must show org.postgresql.Driver and jdbc:postgresql://db:5432/fineract_tenants
# must show NO ojdbc / oracle.jdbc / :1521 / com.mysql.cj / mariadb

# 3. Server healthy
curl -sk https://localhost:8443/fineract-provider/actuator/health   # {"status":"UP",...}

# 4. Postgres server version, recorded with the capture
docker exec fineract-db-1 psql -U postgres -t -c 'select version();'
```

Any mismatch **invalidates the capture** — it would mean the run did not execute the pinned oracle, or did
not execute it on the mandated engine.

## Environment

```sh
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='          # mifos:password, stock demo credentials
T='Fineract-Platform-TenantId: default'
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

**Still open on this recipe, and NOT fixed here** — T22 P0-4: the Preconditions block above does not yet
*fail the run* on the two settings that actually decide the arithmetic (`c_configuration.rounding-mode` must
be **4** = HALF_UP; `tenants.timezone_id` must be `Asia/Ulaanbaatar` or `Asia/Hovd`) nor assert that
`tenant_server_connections.schema_connection_parameters` is empty. Those assertions are written against a
running server and are parked with the re-point (T22 P0-6) for the next oracle-reaching fire.

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

Findings and their evidence: `PATHB-REPORT.md`.
