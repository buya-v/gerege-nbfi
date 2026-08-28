#!/bin/sh
# P-45: drive the write-statement refusal RED, so the guard has been WATCHED to
# fire rather than merely described. Five write shapes must be REFUSED (exit 2),
# and one plain SELECT must be ADMITTED -- a guard that refuses everything
# enforces nothing either.
DIR=$(dirname "$0")/..
TMP=$(mktemp -d)
FAILED=0
echo "T421 READ-ONLY GUARD RED DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "target script: $DIR/capsql-readonly.sh"
echo

drive() {
  printf '%s\n' "$1" > "$TMP/q.sql"
  OUTPUT=$(sh "$DIR/capsql-readonly.sh" T421-REDDRIVE "$TMP/q.sql" 2>&1)
  RC=$?
  LABEL=$(printf '%s' "$1" | tr '\n' ' ' | cut -c1-56)
  if [ "$RC" -eq 2 ]; then
    echo "  REFUSED (exit 2) as designed: $LABEL"
  else
    echo "  *** GUARD DID NOT FIRE (exit $RC): $LABEL"
    echo "$OUTPUT"
    FAILED=1
  fi
}

drive "UPDATE acc_gl_journal_entry SET amount = 1;"
drive "DELETE FROM acc_product_mapping;"
drive "INSERT INTO m_office (name) VALUES ('x');"
drive "DROP TABLE acc_gl_account;"
drive "-- looks harmless
UPDATE acc_gl_account SET name='x';"

printf 'SELECT 1;\n' > "$TMP/q.sql"
sh "$DIR/capsql-readonly.sh" T421-REDDRIVE-CONTROL "$TMP/q.sql" >/dev/null 2>&1
RC=$?
if [ "$RC" -eq 2 ]; then
  echo "  *** CONTROL WRONGLY REFUSED -- the guard refuses everything, which enforces nothing"
  FAILED=1
else
  echo "  CONTROL: a bare SELECT was ADMITTED (exit $RC) -- the guard discriminates"
fi
rm -f "$DIR/out/T421-REDDRIVE-CONTROL.txt" "$DIR/out/T421-REDDRIVE-CONTROL.sql" "$DIR/out/T421-REDDRIVE-CONTROL.psql"
rm -rf "$TMP"
echo
if [ "$FAILED" -eq 0 ]; then
  echo "RED DRIVE: five write shapes REFUSED, control SELECT ADMITTED. Guard enforces."
else
  echo "RED DRIVE FAILED"
fi
exit "$FAILED"
