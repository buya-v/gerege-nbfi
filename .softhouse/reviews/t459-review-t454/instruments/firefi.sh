#!/bin/bash
# T459 -- the ONE live multi-character-fold target in this tree: `fire-program.sh` contains "fi".
set -u
W="${T459_WORK:-/tmp/t459}/work/firefi"
rm -rf "$W"; mkdir -p "$W"
A="fire-program"".sh"
B=$'\xef\xac\x81'"re-program"".sh"          # U+FB01 LATIN SMALL LIGATURE FI + "re-program.sh"
printf 'THE HONEST FIRE DRIVER\n' > "$W/$A"
printf 'THE FORGED FIRE DRIVER\n' > "$W/$B"
n=$(ls -1 "$W" | wc -l | tr -d ' ')
v=$(cat "$W/$A")
printf 'files in the directory      : %s\n' "$n"
printf 'what "%s" reads back : %s\n' "$A" "$v"
if [ "$n" = 1 ] && [ "$v" = "THE FORGED FIRE DRIVER" ]; then
  echo 'RESULT: COLLIDES. U+FB01 folds onto "fi" on this volume and its UTF-8 leading byte 0xEF'
  echo '        sorts after ASCII "f" = 0x66, so the forged entry WINS a checkout.'
else
  echo 'RESULT: distinct.'
fi
echo
echo 'WHY IT MATTERS: .softhouse/bin/fire-program.sh is (a) a DECLARED WITNESS in the'
echo 'DECLARATION TABLE and (b) the file FU-T454-1 proposes to host the external'
echo 'committed-vs-materialised verifier. T454 counted 4 colliders over all printable ASCII and'
echo 'this character is not among them, because its ASCII image is TWO characters.'
rm -rf "$W"
