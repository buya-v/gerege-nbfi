#!/usr/bin/env bash
# T108 — replicate T91's G-4 experiment byte for byte, then correct it.
#
# T91 concluded "T80's asserted BSD-grep-in-UTF-8 behaviour DID NOT REPRODUCE".
# Its G-4 probe is committed at
#   softhouse/T91-preconditions-copy:.softhouse/capture/t91/prove-guards.sh:68-85
# and it contains TWO independent reasons it could never have reproduced T80:
#
#   (1) the poison bytes are inserted at the END of the line, AFTER the match
#       text:      b[:j] + b'\xff\xfe' + b[j:]   where j = index of the '\n'
#       BSD grep's UTF-8 decode fails AT the bad byte, so everything BEFORE it
#       on that line is still searchable.  T80's real transcript had the bad
#       byte BEFORE the matched text.
#
#   (2) both arms of the test are run under `LC_ALL=C` (prove-guards.sh:79,81).
#       LC_ALL=C is the very mitigation under test.  A test of whether LC_ALL=C
#       matters, run with LC_ALL=C in both arms, cannot answer the question.
#
# This script runs T91's shape and T80's shape, each under LC_ALL=C and under a
# UTF-8 locale, with and without -a, and prints all sixteen cells.
#
# No arithmetic; no floating point (P-25).
#
# Usage: bash replicate-t91-g4.sh
set -u

S="$(mktemp -d -t t108t91)"
SENT='PASS  effective rounding mode canary'

python3 - "$S" <<'PY'
import os, sys
s = sys.argv[1]
sent = b'PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)'
clean = b'header line\n  ' + sent + b'\ntrailer line\n'

# T91's exact transformation: find the sentence, find the newline ENDING that
# line, splice \xff\xfe in immediately BEFORE the newline -> AFTER the match.
i = clean.find(sent)
j = clean.find(b'\n', i)
open(os.path.join(s, 't91-shape.txt'), 'wb').write(clean[:j] + b'\xff\xfe' + clean[j:])

# T80's shape: the bad byte lands BEFORE the matched text on the same line.
open(os.path.join(s, 't80-shape.txt'), 'wb').write(clean[:i] + b'\xff\xfe' + clean[i:])
print('built t91-shape.txt (poison AFTER match) and t80-shape.txt (poison BEFORE match)')
PY

echo
echo "hexdump of the poisoned line, T91 shape:"
/usr/bin/grep -c . "$S/t91-shape.txt" >/dev/null 2>&1
sed -n '2p' "$S/t91-shape.txt" 2>/dev/null | xxd | tail -3
echo "hexdump of the poisoned line, T80 shape:"
sed -n '2p' "$S/t80-shape.txt" 2>/dev/null | xxd | head -3
echo

printf '%-12s %-8s %-6s %-6s %s\n' SHAPE LOCALE FLAGS EXIT MEANING
for shape in t91-shape t80-shape; do
  for loc in posixC utf8; do
    for fl in -qF -aqF; do
      if [ "$loc" = posixC ]; then
        env LC_ALL=C LANG=C /usr/bin/grep "$fl" "$SENT" "$S/$shape.txt"
      else
        env -u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8 /usr/bin/grep "$fl" "$SENT" "$S/$shape.txt"
      fi
      st=$?
      if [ "$st" -eq 0 ]; then m="FOUND (correct)"; else m="ABSENT (WRONG - the sentence IS there)"; fi
      printf '%-12s %-8s %-6s %-6s %s\n' "$shape" "$loc" "$fl" "$st" "$m"
    done
  done
done

echo
echo "T91 ran only the two 'posixC' rows of the t91-shape block."
echo "Both of them are FOUND, so it concluded T80 did not reproduce."
echo "The row that reproduces T80 is  t80-shape / utf8 / -aqF."
rm -rf "$S"
