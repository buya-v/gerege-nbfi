#!/bin/sh
# T388 step 20 -- create the thirteen CLEAN GL accounts.
#
# Every call goes through cap11.sh, so each one leaves out/NAME.req (the exact wire
# bytes), out/NAME.req.sha256, out/NAME.http (the record, INCLUDING the Idempotency-Key
# actually sent), out/NAME.status and out/NAME.json. Nothing here is synthesised: a body
# that was not sent leaves no .req, and a response that was not received leaves no .json.
#
# THE IDEMPOTENCY KEYS ARE TASK-NAMING ON PURPOSE. m_portfolio_command_source
# .idempotency_key is NOT NULL and Fineract MINTS a UUID when the caller sends no header
# (IdempotencyKeyResolver.java:36 -> IdempotencyKeyGenerator.create()), so a probe that
# omits the header is UNATTRIBUTABLE FOREVER -- T371 re-derived that 339 of 359 rows in
# this tenant name nothing. Every key below begins `T388-` so the row it writes can be
# traced back to this file.
#
# A 4xx BURNS THE KEY. saveInitial() runs BEFORE executeCommandInTransaction(), so a
# refusal is as permanent as an acceptance and re-running this script with the same keys
# will NOT re-create anything -- it will hit exceptionWhenTheRequestAlreadyProcessed.
# That is the intended behaviour: this script is a record of one fire, not a fixture.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)

# stem<space>key -- one per line, read on stdin by the loop so no array syntax is needed.
"$DIR/cap11.sh" T388-G01-gl-fund-source           POST /glaccounts req/G01-gl-fund-source.json           T388-G01-gl-fund-source
"$DIR/cap11.sh" T388-G02-gl-loan-portfolio        POST /glaccounts req/G02-gl-loan-portfolio.json        T388-G02-gl-loan-portfolio
"$DIR/cap11.sh" T388-G03-gl-interest-on-loans     POST /glaccounts req/G03-gl-interest-on-loans.json     T388-G03-gl-interest-on-loans
"$DIR/cap11.sh" T388-G04-gl-income-from-fees      POST /glaccounts req/G04-gl-income-from-fees.json      T388-G04-gl-income-from-fees
"$DIR/cap11.sh" T388-G05-gl-income-from-penalties POST /glaccounts req/G05-gl-income-from-penalties.json T388-G05-gl-income-from-penalties
"$DIR/cap11.sh" T388-G06-gl-losses-written-off    POST /glaccounts req/G06-gl-losses-written-off.json    T388-G06-gl-losses-written-off
"$DIR/cap11.sh" T388-G07-gl-interest-receivable   POST /glaccounts req/G07-gl-interest-receivable.json   T388-G07-gl-interest-receivable
"$DIR/cap11.sh" T388-G08-gl-fees-receivable       POST /glaccounts req/G08-gl-fees-receivable.json       T388-G08-gl-fees-receivable
"$DIR/cap11.sh" T388-G09-gl-penalties-receivable  POST /glaccounts req/G09-gl-penalties-receivable.json  T388-G09-gl-penalties-receivable
"$DIR/cap11.sh" T388-G10-gl-transfers-suspense    POST /glaccounts req/G10-gl-transfers-suspense.json    T388-G10-gl-transfers-suspense
"$DIR/cap11.sh" T388-G11-gl-overpayment           POST /glaccounts req/G11-gl-overpayment.json           T388-G11-gl-overpayment
"$DIR/cap11.sh" T388-G12-gl-income-from-recovery  POST /glaccounts req/G12-gl-income-from-recovery.json  T388-G12-gl-income-from-recovery
"$DIR/cap11.sh" T388-G13-gl-goodwill-credit       POST /glaccounts req/G13-gl-goodwill-credit.json       T388-G13-gl-goodwill-credit
