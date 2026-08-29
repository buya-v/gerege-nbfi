#!/bin/bash
# T459 independent fold probe. Writes two distinguishable contents at two spellings
# and reads back which survived. Calibrated on a known-collide and a known-distinct pair.
set -u
W="${T459_WORK:-/tmp/t459}/work/foldprobe"
probe() { # $1 = label, $2 = spelling A (ASCII), $3 = spelling B (candidate)
  rm -rf "$W"; mkdir -p "$W"
  printf 'AAA' > "$W/$2"
  printf 'BBB' > "$W/$3"
  n=$(ls -1 "$W" | wc -l | tr -d ' ')
  v=$(cat "$W/$2")
  if [ "$n" = 1 ] && [ "$v" = BBB ]; then verdict="COLLIDES"; elif [ "$n" = 2 ]; then verdict="distinct"; else verdict="ANOMALY(n=$n v=$v)"; fi
  printf '%-46s files=%s  %s reads=%s  -> %s\n' "$1" "$n" "$2" "$v" "$verdict"
}
probe "CALIB-POS  U+017F LONG S vs ascii s"      'zs.txt' $'z\xc5\xbf.txt'
probe "CALIB-NEG  ascii z vs ascii y"            'zz.txt' 'zy.txt'
probe "U+212A KELVIN vs ascii k"                 'zk.txt' $'z\xe2\x84\xaa.txt'
probe "U+212A appended where there is no k"      'zs.txt' $'zs\xe2\x84\xaa.txt'
probe "ASCII uppercase S vs s"                   'zs.txt' 'zS.txt'
probe "U+037E GREEK QUESTION MARK vs ascii ;"    'z;.txt' $'z\xcd\xbe.txt'
probe "U+1FEF GREEK VARIA vs ascii backtick"     'z`.txt' $'z\xe1\xbf\xaf.txt'
probe "U+0131 DOTLESS I vs ascii i"              'zi.txt' $'z\xc4\xb1.txt'
probe "U+00DF SHARP S vs ss"                     'zss.txt' $'z\xc3\x9f.txt'
probe "NFD e-acute vs NFC e-acute"               $'z\xc3\xa9.txt' $'ze\xcc\x81.txt'
rm -rf "$W"
