#!/bin/sh
side=$1
base=/tmp/t135/f5/$side/.softhouse/capture/pathb
cd $base/t36 || exit 9
CANARY_REQ=$base/t22-audit/req/calc-pmode2-gerege.json sh preconditions.sh gerege > /tmp/t135/f5/$side.live.out 2> /tmp/t135/f5/$side.live.err
echo "=== $side LIVE  EXIT=$?"
echo "PASS=$(grep -c '^  PASS' /tmp/t135/f5/$side.live.out)  FAIL=$(grep -c '^  FAIL' /tmp/t135/f5/$side.live.err)"
cat /tmp/t135/f5/$side.live.out /tmp/t135/f5/$side.live.err | grep -E 'prohibited|schema_connection_parameters|canary|ALL PRECONDITIONS'
