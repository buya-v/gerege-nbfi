#!/bin/sh
# T138 — re-run T108's decisive discriminating probe myself (P-33), and then ask
# whether G-4, as shipped by T115, could ever produce the effect it exists to detect.
set -u
D=/tmp/T138-grep; rm -rf "$D"; mkdir -p "$D"

python3 - "$D" <<'PY'
import sys, os
d = sys.argv[1]
S = b'PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)'
# shape A: invalid byte BEFORE the match, same line   (T108 s01/s06 -> SILENT MISS on BSD/UTF-8)
open(os.path.join(d,'before.txt'),'wb').write(b'header\n' + b'\xff\xfe ' + S + b'\nEXIT=0\n')
# shape B: invalid byte AFTER the match, same line    (T108 s02 -> matches correctly)
open(os.path.join(d,'after.txt'),'wb').write(b'header\n' + S + b' \xff\xfe' + b'\nEXIT=0\n')
# shape C: invalid byte on a DIFFERENT line           (T108 s03/s04 -> matches correctly)
open(os.path.join(d,'other.txt'),'wb').write(b'\xff\xfe junk\n' + S + b'\nEXIT=0\n')
print('wrote three shapes')
PY

echo
echo "which program is 'grep' from inside a script? (P-33: type -a, not command -v)"
echo "   \$(command -v grep) = $(command -v grep)"
/usr/bin/grep --version 2>&1 | head -1 | sed 's/^/   \/usr\/bin\/grep --version: /'
echo

printf '%-14s %-24s %s\n' SHAPE INVOCATION 'rc (0=found, 1=NOT found)'
for f in before after other; do
  for inv in "utf8 -qF" "utf8 -aqF" "LC_ALL=C -qF" "LC_ALL=C -aqF"; do
    loc=${inv%% *}; fl=${inv#* }
    if [ "$loc" = utf8 ]; then
      LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep $fl 'PASS  effective rounding mode canary' "$D/$f.txt"
    else
      LC_ALL=C /usr/bin/grep $fl 'PASS  effective rounding mode canary' "$D/$f.txt"
    fi
    printf '%-14s %-24s %s\n' "$f" "$inv" "$?"
  done
done
echo
echo "=================================================================="
echo "Now: which shape does prove-guards.sh's G-4 actually build?"
echo "=================================================================="
git -C /tmp/T138clone show bd59187cf83c7c7161db23668e91d45bd46be2a8:.softhouse/capture/t91/prove-guards.sh \
  | LC_ALL=C sed -n '/^python3 - "\$S\/poison/,/^PY$/p' | sed 's/^/   /'
echo
echo "   i = index of the certification text; j = index of the NEWLINE after it;"
echo "   the poison is inserted at b[:j] + FFFE + b[j:]  ->  AFTER the match, same line."
echo "   That is T108 shape s02, the one BSD grep matches CORRECTLY in every locale."
echo "   => G-4's probe cannot produce the BSD silent miss at all (P-33's rule:"
echo "      'N-of-N green cells refute nothing unless the failing shape is among the N')."
