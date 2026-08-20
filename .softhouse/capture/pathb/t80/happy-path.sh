#!/bin/sh
# T80 — ATTACK 5 of the acceptance test, inverted: prove the HARDENED recipe still WORKS.
#
# Hardening that also breaks the happy path is not hardening.  This runs the real recipe on the
# real tenant at the ratified (19, HALF_UP) settings, twice (once under `sh`, once under `bash`),
# plus the attestation generator, and then compares every response byte-for-byte against the
# corpus T77 confirmed.  Nothing is written into any committed evidence directory: every run gets
# its own t80/-owned output directory, whose name still ends in the tenant id so the recipe's own
# provenance guard accepts it.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
cd "$W"

echo "=== HAPPY PATH — tenant gerege, MathContext(19, HALF_UP)"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "--- 5a: sh t36/recapture.sh  ->  t80/out/recapture-gerege"
RECAPTURE_OUT=$O/recapture-gerege sh t36/recapture.sh
echo "EXIT=$?"
echo

echo "--- 5b: bash t36/recapture.sh  ->  t80/out/bash-recapture-gerege"
RECAPTURE_OUT=$O/bash-recapture-gerege bash t36/recapture.sh
echo "EXIT=$?"
echo

echo "--- 5c: python3 t36/attest.py gerege  ->  t80/out/attest-gerege"
ATTEST_OUT=$O/attest-gerege ATTEST_TASK=T80 ATTEST_BRANCH=softhouse/T80-pathb-recipe-hardening \
  python3 t36/attest.py gerege
echo "EXIT=$?"
echo

echo "--- precondition PASS/FAIL counts of the sh happy-path run"
echo "PASS lines: $(grep -c '^  PASS' "$O/recapture-gerege/preconditions.txt")"
echo "FAIL lines: $(grep -c '^  FAIL' "$O/recapture-gerege/preconditions.txt" || true)"
echo

echo "--- byte-identity vs the corpus T77 confirmed (four distinct digests, five sets)"
for n in B-01-baseline B-02-multiplesof100 B-03-diycs-fullleapyear B-04-diycs-feb29only; do
  shasum -a 256 \
    "$W/out/$n-raw.json" \
    "$W/t36/out/recapture-gerege/$n-raw.json" \
    "$W/t76/out/recapture-gerege/$n-raw.json" \
    "$O/recapture-gerege/$n-raw.json" \
    "$O/bash-recapture-gerege/$n-raw.json" \
    "$O/attest-gerege/$n-raw.json" 2>/dev/null
  echo
done

echo "--- distinct digests per capture id (expect exactly 1 each)"
rc=0
for n in B-01-baseline B-02-multiplesof100 B-03-diycs-fullleapyear B-04-diycs-feb29only; do
  c=$(shasum -a 256 \
        "$W/out/$n-raw.json" \
        "$W/t36/out/recapture-gerege/$n-raw.json" \
        "$W/t76/out/recapture-gerege/$n-raw.json" \
        "$O/recapture-gerege/$n-raw.json" \
        "$O/bash-recapture-gerege/$n-raw.json" \
        "$O/attest-gerege/$n-raw.json" \
      | awk '{print $1}' | sort -u | wc -l | tr -d ' ')
  echo "$n: $c distinct digest(s) across 6 independently produced sets"
  [ "$c" = "1" ] || rc=1
done
echo
echo "--- the tenant this capture set was taken from, as stamped by the recipe"
cat "$O/recapture-gerege/CAPTURED-FROM-TENANT"
echo
echo "--- what the sidecar now says about DEC-1 (was: 'revision 6 and UNRATIFIED')"
python3 -c "import json,sys; a=json.load(open(sys.argv[1])); print(a['_status']); print(json.dumps(a['_dec1'])); print(a['does_not_license'][0])" \
  "$O/attest-gerege/attestation.json"
echo
[ "$rc" = "0" ] && echo "RESULT: HAPPY PATH INTACT — every capture byte-identical across all six sets." \
                || echo "RESULT: A CAPTURE MOVED — investigate before trusting anything above."
exit $rc
