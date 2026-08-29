#!/usr/bin/env bash
# Does capsql.sh's write-verb refusal catch a verb at END OF LINE? Test the REGEX only.
# No database is contacted by this test.
rx='(^|[^[:alnum:]_])(insert|update|delete|truncate|drop|alter|grant|revoke)[[:space:]]'
t=/tmp/t438/wvcases; rm -rf $t; mkdir -p $t
printf 'INSERT INTO x VALUES (1);\n'        > $t/a-normal.sql
printf 'DELETE\n  FROM acc_gl_journal_entry;\n' > $t/b-verb-at-eol.sql
printf 'INSERT(1);\n'                        > $t/c-verb-then-paren.sql
printf 'SELECT 1;\n'                         > $t/d-clean.sql
printf -- '-- we must never UPDATE the oracle\nSELECT 1;\n' > $t/e-verb-in-comment.sql
for f in $t/*.sql; do
  if grep -Eqi "$rx" "$f"; then r="REFUSED"; else r="ALLOWED"; fi
  printf '%-24s -> %s\n' "$(basename $f)" "$r"
done
