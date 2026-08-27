#!/bin/sh
side=$1
base=/tmp/t135/f5/$side/.softhouse/capture/pathb
cd $base/t36 || exit 9
PATH=/tmp/t135/f5/gonebin:$PATH CANARY_REQ=$base/t22-audit/req/calc-pmode2-gerege.json \
  sh preconditions.sh gerege > /tmp/t135/f5/$side.gone.out 2> /tmp/t135/f5/$side.gone.err
echo "=== $side  CONTAINER GONE  EXIT=$?"
echo "PASS=$(grep -c '^  PASS' /tmp/t135/f5/$side.gone.out)  FAIL=$(grep -c '^  FAIL' /tmp/t135/f5/$side.gone.err)"
cat /tmp/t135/f5/$side.gone.out /tmp/t135/f5/$side.gone.err | grep -E 'prohibited|schema_connection_parameters'
