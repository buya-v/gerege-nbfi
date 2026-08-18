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

```sh
for n in 01 02 03 04; do
  case $n in 01) f=calc-B-01-baseline;;          02) f=calc-B-02-multiplesof100;;
             03) f=calc-B-03-diycs-fullleapyear;; 04) f=calc-B-04-diycs-feb29only;; esac
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
       -H "$A" -H "$T" -H "$CT" -d @req/$f.json -o out/B-$n-*-raw.json
done
```

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
