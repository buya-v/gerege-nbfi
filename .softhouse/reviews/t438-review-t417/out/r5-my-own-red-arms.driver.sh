#!/usr/bin/env bash
W=/tmp/t438/t417tree/.softhouse/capture/t417-scheduler-attribution/instruments/oracle-window-witness.sh
export ORACLE_WITNESS_DIR=/tmp/t438/redwit
rm -rf /tmp/t438/redwit; mkdir -p /tmp/t438/redwit

echo "############ RED-A: doctored LEDGER digest in the open witness -> must report MOVED, exit 1"
cp /tmp/t438/witness/T438A.open.tsv /tmp/t438/redwit/REDA.open.tsv
sed -i '' 's/^tbl	acc_gl_journal_entry	109	.*/tbl	acc_gl_journal_entry	109	00000000000000000000000000000000/' /tmp/t438/redwit/REDA.open.tsv
grep -c '^tbl	acc_gl_journal_entry	109	00000000' /tmp/t438/redwit/REDA.open.tsv
bash "$W" close REDA; echo "rc=$?"

echo; echo "############ RED-B: doctored in-flight (jobs currently_running=1) -> must REFUSE, exit 1"
cp /tmp/t438/witness/T438A.open.tsv /tmp/t438/redwit/REDB.open.tsv
sed -i '' 's/^jobs	currently_running	0/jobs	currently_running	1/' /tmp/t438/redwit/REDB.open.tsv
grep -c '^jobs	currently_running	1' /tmp/t438/redwit/REDB.open.tsv
bash "$W" close REDB; echo "rc=$?"

echo; echo "############ RED-C: doctored SEQUENCE last_value -> must report MOVED, exit 1"
cp /tmp/t438/witness/T438A.open.tsv /tmp/t438/redwit/REDC.open.tsv
sed -i '' 's/^seq	acc_gl_journal_entry_id_seq	.*/seq	acc_gl_journal_entry_id_seq	999999/' /tmp/t438/redwit/REDC.open.tsv
grep -c '^seq	acc_gl_journal_entry_id_seq	999999' /tmp/t438/redwit/REDC.open.tsv
bash "$W" close REDC; echo "rc=$?"

echo; echo "############ RED-D: a table REMOVED from the open witness (appearance detection)"
cp /tmp/t438/witness/T438A.open.tsv /tmp/t438/redwit/REDD.open.tsv
sed -i '' '/^tbl	m_loan	/d' /tmp/t438/redwit/REDD.open.tsv
bash "$W" close REDD; echo "rc=$?"

echo; echo "############ RED-E: close with NO open witness"
bash "$W" close NEVEROPENED; echo "rc=$?"
