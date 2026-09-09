# OH-SWEEP — ONE oracle pass that seeds and captures for MANY contexts at once

Repo: /Users/buv/oh-gerege-sweep   Branch: feat/OHSWEEP-batch-capture (checked out)

## The API. Verified working right now. Do NOT go hunting for it, do NOT unzip jars.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'

Your FIRST tool call is an API call. Read a file only when a call fails. Two earlier tasks
in this programme burned 579 and 426 events on reconnaissance and produced nothing on disk.
**Write your scripts and captures AS YOU GO, never at the end** — if this run dies, whatever
is not on disk did not happen.

## Why one pass

Capture is the ONLY phase that needs the oracle, and only one task may touch the oracle at a
time or captures stop being reproducible. Promotion into vectors is entirely OFFLINE and
parallelises afterwards. So this task does the oracle work for SEVEN contexts in one go.

## What already exists — read `.softhouse/capture/seed/MANIFEST.json`, never re-derive it

BUSINESS DATE IS PINNED to **2026-09-01**. Tenant `gerege`: HALF_UP (ordinal 4), precision 19,
MNT, 2 minor units, Asia/Ulaanbaatar. Date everything relative to the pinned date, NEVER to
`date`/`now()`.

    1 office   9 clients   1 staff   4 GL accounts   1 provisioning criteria
    5 loans (all disbursed, spanning 4 provisioning age bands)
    2 tellers (id 1 "SMOKE-Teller" — a stray probe; id 2 "SEED-Teller-01")
    2 cashiers   1 cashier transaction (allocate 100000.50 MNT)

`.softhouse/capture/seed/bin/run.sh` is idempotent — re-run it freely.

## Known-good payload shapes (already probed; use them)

    POST /staff        {firstname, lastname, officeId}
    POST /tellers      {officeId, name, startDate, status, locale, dateFormat}
    POST /tellers/{t}/cashiers/{c}/allocate   {txnAmount, txnDate, locale, dateFormat}
    (settle is the same shape)

## Contexts to cover, cheapest first. Do as many as you can.

For EACH: seed what is missing through the API, then capture the CREATE responses and the
READ-BACKS. Raw bodies to `.softhouse/capture/<context>/out/<case>-raw.json`, requests to
`.softhouse/capture/<context>/req/`. Commit as you finish each context.

  1. branch     tellers, cashiers, allocate/settle, cashier transactions+summary
                (partially seeded already — finish it, add a settle)
  2. shares     share products, share accounts, purchase/approve
  3. collateral collateral products, client collateral, loan-collateral links
  4. investor   external asset owner transfers on an existing disbursed loan
  5. workingcapital  whatever the API exposes over the seeded loans
  6. loan       repayments/waivers/adjustments on the seeded loans, and the read-backs
  7. savings    savings products, accounts, deposits/withdrawals, interest posting

## AMOUNTS MUST DISCRIMINATE WHERE THE DOMAIN ALLOWS

A previous context was seeded entirely with round numbers; every result came out exact and
the vectors proved nothing about arithmetic. For every context where a percentage, a rate,
an apportionment or a division occurs, choose inputs so at least one result lands on a HALF
minor unit, where HALF_UP and HALF_EVEN DIFFER. State the numbers and both outcomes.

Where a seam does only integer minor-unit addition and has NO rounding surface, say so
explicitly. **An honest "this seam cannot discriminate" is a correct result. Do not invent
a tie the domain does not have.**

## Constraints

* NEVER the `default` tenant. API only for writes — no schema DDL, no INSERT/UPDATE/DELETE.
  SQL is READ-ONLY verification.
* Change NO configuration row. `rounding-mode` must still read 4 and `enable-business-date`
  must still be true at the end. VERIFY BOTH and record them.
* Write NO Go. Create NO vectors. This task captures only; promotion is a later, offline task.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or `nexus/`.
* COMMIT AFTER EACH CONTEXT, not once at the end.

## Done means

For each context attempted: raw captures committed under `.softhouse/capture/<context>/out/`,
the scripts that produced them under `.softhouse/capture/<context>/bin/`, and a
`MANIFEST.json` naming every object created with its id. `rounding-mode`=4 and
`enable-business-date`=t verified at the end.

## Report

Per context: what you seeded, what you captured, and the discriminating amounts with both
rounding outcomes — or an explicit statement that the seam has no rounding surface. Name
every context you could NOT cover and why. Covering four honestly beats claiming seven.
