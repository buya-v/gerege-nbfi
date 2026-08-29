#!/usr/bin/env bash
export ORACLE_WITNESS_DIR=/tmp/t438/wrapwit
rm -rf /tmp/t438/wrapwit; mkdir -p /tmp/t438/wrapwit
CW=/tmp/t438/t417tree/.softhouse/capture/t417-scheduler-attribution/instruments/capture-under-witness.sh
bash "$CW" T438RED -- bash /tmp/t438/doctor.sh
echo "WRAPPER rc=$?"
echo "=== PROVENANCE BLOCK AS WRITTEN ==="
cat -A /tmp/t438/wrapwit/T438RED.provenance.tsv | sed 's/\$$//' | sed 's/\^I/<TAB>/g'
