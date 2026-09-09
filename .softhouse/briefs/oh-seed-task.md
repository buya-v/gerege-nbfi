# OH-SEED — seed the gerege oracle. ACTION FIRST.

Repo: /Users/buv/oh-gerege-seed   Branch: feat/OHSEED-oracle-rig (checked out)

## Everything you need to call the API. Do not go looking for it.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'
    curl -sk "$BASE/offices" -H "$AUTH" -H "$TEN"      # verified working, HTTP 200

VERIFIED WORKING RIGHT NOW: GET /offices, /glaccounts, /clients, /businessdate all
return HTTP 200 with exactly those headers. There is no auth problem to solve.

A previous attempt at this task spent 579 events reading the repo and issued THREE curl
calls and ZERO POSTs. Do not repeat that. **Your first tool call is a POST that creates
something.** Read a file only when a call fails and you need to know why.

## Do these in order

Write each step as a shell script under `.softhouse/capture/seed/bin/` as you go — not at
the end. Save every request body to `.softhouse/capture/seed/req/` and every raw response
to `.softhouse/capture/seed/out/<case>-raw.json` BEFORE moving on.

  STEP 1  Pin the business date.
          PUT /configurations/name/enable-business-date  {"enabled":true}
          POST /businessdate  {"type":"BUSINESS_DATE","date":"01 September 2026",
                               "dateFormat":"dd MMMM yyyy","locale":"en"}
          Then GET /businessdate and SAVE the response. Every date you use later is
          relative to this pinned date, never to `date` or `now()`.

  STEP 2  GL accounts (currently 0). POST /glaccounts for the asset / liability /
          expense / income set provisioning needs. Save each id.

  STEP 3  Provisioning criteria. POST /provisioningcriteria with definitions for all four
          categories (STANDARD=1, SUB-STANDARD=2, DOUBTFUL=3, LOSS=4 — already in the
          oracle) with age bands and percentages, mapped to the GL accounts from STEP 2.

  STEP 4  Clients. POST /clients (1 exists). Use pinned names prefixed `SEED-`.

  STEP 5  Loan product. POST /loanproducts with pinned terms, MNT, name prefixed `SEED-`.
          Do NOT reuse "T22 mode probe halfcent" — it belongs to an earlier task.

  STEP 6  Loans. For each client: POST /loans (submit), then
          POST /loans/{id}?command=approve, then POST /loans/{id}?command=disburse.
          Choose submission/disbursement dates RELATIVE TO THE PINNED BUSINESS DATE so a
          known set lands in at least two different provisioning age bands.

  STEP 7  Write `.softhouse/capture/seed/MANIFEST.json` — every object created, its id,
          and the case file it came from. Later context tasks read this instead of
          re-deriving anything.

  STEP 8  Write `.softhouse/capture/seed/ATTESTATION.md`: the pinned business date, the
          config rows before and after, the rounding-mode re-check, every id created,
          and anything you could not do.

  STEP 9  Run the whole rig a SECOND time and show it creates nothing new (idempotent:
          check-then-create, keyed on the `SEED-` prefix or external id).

## Constraints

* NEVER touch the `default` tenant.
* Everything through the API. No schema DDL, no INSERT/UPDATE/DELETE. SQL is READ-ONLY
  verification only.
* `enable-business-date` is the ONLY configuration row you may change. `rounding-mode`
  must still read 4 (HALF_UP) at the end — VERIFY and record it.
* Do NOT edit anything under `nexus/`, `.softhouse/guards/`, or `.softhouse/conformance.sh`.
  This task writes no Go and no vectors.
* Money is integer minor units; no floating point in the rig's own code.
* COMMIT YOUR WORK before you finish.

## Done means

Read-only SQL shows non-zero gl accounts, criteria, clients, loans and DISBURSED loans,
with loans in at least two age bands; rounding-mode still 4; MANIFEST.json and
ATTESTATION.md present; the second run creates nothing; work committed.

Report the SQL counts, the pinned business date, the rounding-mode re-check, and the
two-run idempotence proof. If a step cannot be done honestly, say so and continue with the
rest — a partial rig with an honest gap is fine; a silent one is not.
