#!/bin/sh
# T44 audit leg (charges) — build the four discrimination probes by PURE TEXT SUBSTITUTION
# on committed request files. No JSON parse, no re-serialise, no float. Money is never
# touched here: only a dueDate string, and (AP-4) a charges array appended as literal text.
set -eu

AUD=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/charges
SH=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse
mkdir -p "$AUD/req"

SRC19=$SH/capture/charges/req/calc-FC-19-pctinterest-sdd-inside-p6.json

# AP-1 .. AP-3: FC-19 byte-verbatim with ONLY the dueDate literal replaced.
sed 's/"dueDate": "15 June 2026"/"dueDate": "20 January 2026"/' "$SRC19" > "$AUD/req/calc-AP-1-sdd-pctinterest-inside-p1.json"
sed 's/"dueDate": "15 June 2026"/"dueDate": "01 February 2026"/' "$SRC19" > "$AUD/req/calc-AP-2-sdd-pctinterest-on-p1-duedate.json"
sed 's/"dueDate": "15 June 2026"/"dueDate": "01 April 2026"/'    "$SRC19" > "$AUD/req/calc-AP-3-sdd-pctinterest-on-p3-duedate.json"

# AP-4: committed B-02 (installmentAmountInMultiplesOf = 100, so EMI != principal+interest)
# with charge 5 (PERCENT_OF_AMOUNT_AND_INTEREST, INSTALMENT_FEE) appended as literal text.
sed 's/ "locale": "en",/ "charges": [\n  { "chargeId": 5, "amount": 1.2345 } ],\n "locale": "en",/' \
  "$SH/capture/pathb/req/calc-B-02-multiplesof100.json" > "$AUD/req/calc-AP-4-b02-pctamtint-instalment.json"

for f in "$AUD"/req/calc-AP-*.json; do
  echo "== $(basename "$f")"; cat "$f"; echo
done
