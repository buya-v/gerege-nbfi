#!/bin/sh
side=$1
base=/tmp/t135/f5/$side/.softhouse/capture/pathb
cd $base/t36 || exit 9
PATH=/tmp/t135/f5/poisonbin:$PATH CANARY_REQ=$base/t22-audit/req/calc-pmode2-gerege.json \
  sh preconditions.sh gerege > /tmp/t135/f5/$side.pc.out 2> /tmp/t135/f5/$side.pc.err
echo "=== $side POSITIVE CONTROL  EXIT=$?"
echo "PASS=$(grep -c '^  PASS' /tmp/t135/f5/$side.pc.out)  FAIL=$(grep -c '^  FAIL' /tmp/t135/f5/$side.pc.err)"
cat /tmp/t135/f5/$side.pc.out /tmp/t135/f5/$side.pc.err | grep -E 'prohibited|schema_connection_parameters'
