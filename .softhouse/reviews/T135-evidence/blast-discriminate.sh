#!/bin/sh
# Does the liveness-witness discriminator actually discriminate?  Apply it to the transcripts my
# own RED runs produced, where the scans provably had NO input.
set -u
w() {
  f=$1; lbl=$2
  p5=0; p6=0; p11=0
  LC_ALL=C grep -qa 'PASS  driverClassName org.postgresql.Driver' "$f" && \
    LC_ALL=C grep -qa 'PASS  JDBC URL is jdbc:postgresql' "$f" && p5=1
  LC_ALL=C grep -qa 'PASS  PostgreSQL JDBC driver present in the jar' "$f" && p6=1
  LC_ALL=C grep -qa 'PASS  tenant schema_server_port = 5432' "$f" && p11=1
  vac=$(LC_ALL=C grep -ca 'PASS  0 prohibited\|PASS  schema_connection_parameters is empty' "$f")
  printf '  %-42s P5w=%s P6w=%s P11w=%s   vacuous-shaped PASS lines: %s\n' "$lbl" "$p5" "$p6" "$p11" "$vac"
}
echo "MAIN's bytes, run under conditions where the scans had NO input:"
w /tmp/t135/f5/main.out          "docker+curl dead"
w /tmp/t135/f5/main.gone.out     "fineract container gone, db alive"
echo
echo "MAIN's bytes, run LIVE (the scans had input):"
w /tmp/t135/f5/main.live.out     "live oracle"
echo
echo "=> the witness triple is 000 / 001 when nothing was scanned and 111 when it was."
echo
echo "Same discriminator over the CHARGES capture tree (not in this task's fix scope):"
sh /tmp/t135/blast/measure.sh /Users/buv/gerege-nbfi/.softhouse/capture/charges 2>/dev/null | tail -20
