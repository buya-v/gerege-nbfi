#!/bin/bash
# T131 - shapes T108's 360-cell matrix did NOT contain, chosen because each could
# change the ruling.  BSD grep only (script => BSD), plus the guard's own regex.
D="$(cd "$(dirname "$0")" && pwd)/corpus"; mkdir -p "$D"
python3 - "$D" <<'PY'
import sys, pathlib
d = pathlib.Path(sys.argv[1])
# X1: float BEFORE the poison and another AFTER it, same line
(d/'x1-float-both-sides.json').write_bytes(b'{\n  a: 1.5, \xe2 b: 2.5,\n  "n": "ok"\n}\n')
# X2: VALID multibyte (U+2014 em dash, e2 80 94) before the float - the shape that
#     actually exists in the committed vector store
(d/'x2-valid-emdash.json').write_bytes(b'{\n  note \xe2\x80\x94 x: 1.5,\n  "n": "ok"\n}\n')
# X3: poison INSIDE a JSON string literal, float outside, same line - tests whether
#     perl's string-strip removes the poison before grep ever sees it
(d/'x3-poison-in-string.json').write_bytes(b'{\n  "s": "bad \xe2 here", x: 1.5,\n  "n": "ok"\n}\n')
# X4: truncated em dash (e2 80) - the realistic corruption of a byte sequence that
#     IS present in 5 committed vectors, placed outside a string
(d/'x4-truncated-emdash.json').write_bytes(b'{\n  note \xe2\x80 x: 1.5,\n  "n": "ok"\n}\n')
print("built x1..x4")
PY
PAT='[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'
printf '%-26s %-10s %-8s %s\n' FILE LOCALE TOKENS "GUARD SAYS"
for f in x1-float-both-sides x2-valid-emdash x3-poison-in-string x4-truncated-emdash; do
  for loc in C.UTF-8 C; do
    for t in bare fixed; do
      if [ "$t" = bare ]; then
        perl -0pe 's/"(\\.|[^"\\])*"//g' "$D/$f.json" | LC_ALL=$loc /usr/bin/grep -Eq "$PAT" && v="FLOAT FOUND (correct)" || v="clean - PASSES  <== SILENT PASS"
      else
        perl -0pe 's/"(\\.|[^"\\])*"//g' "$D/$f.json" | LC_ALL=C /usr/bin/grep -aEq "$PAT" && v="FLOAT FOUND (correct)" || v="clean - PASSES  <== SILENT PASS"
      fi
      printf '%-26s %-10s %-8s %s\n' "$f" "$loc" "$t" "$v"
    done
  done
done
