#!/usr/bin/env bash
# T234 — repairs the broken \d control in 01-escape-matrix.sh (the corpus line was
# "x1 y", so x\dy could not match under ANY reading; the row proved nothing).
# Also reconciles T232's reported "= 14" against what this tree measures.
set -u
C=/tmp/t234_matrix2.txt
{ printf 'x1y\n'; printf 'xdy\n'; printf 'x y\n'; printf 'xsy\n'; printf 'x_y\n'; printf 'xwy\n'; } > "$C"
echo "### corpus (each line discriminates class-reading from literal-reading)"; nl -ba "$C"; echo
echo "  x1y : matches x\\dy ONLY if \\d = digit class"
echo "  xdy : matches x\\dy ONLY if \\d = literal 'd'"
echo "  x y : matches x\\sy ONLY if \\s = whitespace class"
echo "  xsy : matches x\\sy ONLY if \\s = literal 's'"
echo "  x_y : matches x\\wy ONLY if \\w = word class"
echo "  xwy : matches x\\wy ONLY if \\w = literal 'w'"
echo
echo "### BSD grep -E (/usr/bin/grep) -- reading per escape"
for p in 'x\dy' 'x\sy' 'x\wy'; do
  echo "  pattern $p ->"; /usr/bin/grep -E -n "$p" "$C" | sed 's/^/      /' || echo "      (no match)"
done
echo
echo "### git grep -E vs -P on the same three escapes, repo-wide, tracked files"
for p in 'a\db' 'a\sb' 'a\wb'; do
  for f in -E -P; do
    n=$(git grep $f -c -- "$p" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
    printf '    git grep %s %-10s hitlines=%s\n' "$f" "'$p'" "$n"
  done
done
echo
echo "### python3 re reference"
python3 - "$C" <<'PY'
import re,sys
lines=open(sys.argv[1]).read().splitlines()
for p in [r'x\dy',r'x\sy',r'x\wy']:
    print("    python re %-8s -> %s" % ("'"+p+"'", [l for l in lines if re.search(p,l)]))
PY
echo
echo "### RECONCILING T232's '= 14'  (T232 reported git grep -c -E 'balance column' = 14)"
echo "  NOTE: 'git grep -c' prints ONE LINE PER FILE ('path:count'), so a bare -c piped to"
echo "  wc -l counts FILES, and read as a single number it is neither files nor lines."
for rev in HEAD 90c21d6; do
  if git rev-parse --verify -q "$rev^{commit}" >/dev/null; then
    files=$(git grep -E -l -- 'balance column' "$rev" 2>/dev/null | wc -l | tr -d ' ')
    lines=$(git grep -E -c -- 'balance column' "$rev" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
    printf '    rev %-10s files=%-5s hitlines=%s\n' "$rev" "$files" "$lines"
  else
    printf '    rev %-10s NOT PRESENT IN THIS WORKTREE\n' "$rev"
  fi
done
echo "  scoped to .softhouse only, HEAD:"
printf '    files=%s hitlines=%s\n' \
  "$(git grep -E -l -- 'balance column' -- .softhouse | wc -l | tr -d ' ')" \
  "$(git grep -E -c -- 'balance column' -- .softhouse | awk -F: '{s+=$NF} END{print s+0}')"
