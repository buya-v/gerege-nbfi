#!/bin/bash
# T459: the class T454's census EXCLUDES BY CONSTRUCTION -- folds whose ASCII image is
# MORE THAN ONE character. fold_candidates() keeps a candidate only `if len(f) == 1`.
set -u
W="${T459_WORK:-/tmp/t459}/work/foldprobe2"
probe() { # $1 label, $2 ascii digraph spelling, $3 candidate spelling
  rm -rf "$W"; mkdir -p "$W"
  printf 'AAA' > "$W/$2"; printf 'BBB' > "$W/$3"
  n=$(ls -1 "$W" | wc -l | tr -d ' '); v=$(cat "$W/$2")
  if [ "$n" = 1 ] && [ "$v" = BBB ]; then r="COLLIDES"; elif [ "$n" = 2 ]; then r="distinct"; else r="ANOMALY(n=$n v=$v)"; fi
  printf '%-52s files=%s %s reads=%s -> %s\n' "$1" "$n" "$2" "$v" "$r"
}
probe "U+00DF SHARP S            -> ss"  'zss.txt'  $'z\xc3\x9f.txt'
probe "U+FB00 LIGATURE FF        -> ff"  'zff.txt'  $'z\xef\xac\x80.txt'
probe "U+FB01 LIGATURE FI        -> fi"  'zfi.txt'  $'z\xef\xac\x81.txt'
probe "U+FB02 LIGATURE FL        -> fl"  'zfl.txt'  $'z\xef\xac\x82.txt'
probe "U+FB03 LIGATURE FFI       -> ffi" 'zffi.txt' $'z\xef\xac\x83.txt'
probe "U+FB05 LIGATURE LONG S T  -> st"  'zst.txt'  $'z\xef\xac\x85.txt'
probe "U+FB06 LIGATURE ST        -> st"  'zst.txt'  $'z\xef\xac\x86.txt'
probe "U+0149 N PRECEDED BY APOS -> 'n"  "z'n.txt"  $'z\xc5\x89.txt'
probe "U+01F0 j-caron            -> j+comb" 'zj.txt' $'z\xc7\xb0.txt'
probe "U+FDFA ARABIC SALLALLAHOU -> long"  'zsallallahou.txt' $'z\xef\xb7\xba.txt'
rm -rf "$W"
