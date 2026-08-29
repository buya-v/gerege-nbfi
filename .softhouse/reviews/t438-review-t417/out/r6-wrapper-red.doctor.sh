#!/usr/bin/env bash
# stands in for a "capture command": while the window is open, it doctors the OPEN witness
# so that close() must report the graded surface as MOVED. Touches only /tmp. No SQL at all.
f="$ORACLE_WITNESS_DIR/T438RED.open.tsv"
sed -i '' 's/^tbl	acc_gl_journal_entry	109	.*/tbl	acc_gl_journal_entry	109	00000000000000000000000000000000/' "$f"
echo "doctored $f"
