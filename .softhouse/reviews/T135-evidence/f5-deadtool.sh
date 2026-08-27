#!/bin/sh
side=$1
cd /tmp/t135/f5/$side/.softhouse/capture/pathb/t36 || exit 9
PATH=/tmp/t135/f5/bin:$PATH sh preconditions.sh gerege > /tmp/t135/f5/$side.out 2> /tmp/t135/f5/$side.err
echo "=== $side  EXIT=$?"
echo "PASS lines=$(grep -c '^  PASS' /tmp/t135/f5/$side.out)"
echo "FAIL lines=$(grep -c '^  FAIL' /tmp/t135/f5/$side.err)"
echo "--- the three prohibition verdicts:"
cat /tmp/t135/f5/$side.out /tmp/t135/f5/$side.err | grep -E 'prohibited-engine|prohibited driver jars|prohibited-driver-jar|schema_connection_parameters'
