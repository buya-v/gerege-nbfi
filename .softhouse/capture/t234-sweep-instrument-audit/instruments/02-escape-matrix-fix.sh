#!/usr/bin/env bash
# T234 — repairs the broken \d control in 01-escape-matrix.sh (the corpus line was
# "x1 y", so x\dy could not match under ANY reading; the row proved nothing).
# Also reconciles T232's reported "= 14" against what this tree measures.
set -u
# T273 — THE FIXTURE IS NOW SELF-OWNED SCRATCH, NOT A LITERAL PATH IN /tmp.
#
# It used to be `C=/tmp/t234_matrix2.txt`, created by the very next line. That one
# literal made THE HARNESS'S VERDICT a property of the LINTING HOST'S FILESYSTEM
# rather than of this tree. The fail-open linter's C1 rule reads an absolute path
# in an assignment position and asks `os.path.exists`; its ownership filter looks
# for a literal `> /tmp/t234_matrix2.txt` and the redirection here is `> "$C"`, so
# the filter never fired. The answer to `exists` was therefore YES only on a host
# where this script had ALREADY BEEN RUN ONCE — which flipped this file TIER2 (C2
# only) on such a host and TIER1 (C1+C2) on a clean one, and the tier token is part
# of FAILOPEN_PIN_FILE_LIST, so the whole BAR went EXIT 2 WITH NO PROBE LINE the
# moment macOS cleared /tmp on reboot. Measured both ways, this tree, this host:
# .softhouse/capture/t273-residue/evidence/10-PREFIX-reproduction.txt.
#
# `mktemp`'s XXXXXXXXXX template is not a path and no linter can resolve it to one,
# so no classification can depend on it; the directory is created here, owned here,
# and removed on EXIT. The instrument's OUTPUT is unchanged — it never printed $C —
# and that is proved byte-for-byte in evidence/20-instrument-output-{BEFORE,AFTER}.txt.
D="$(mktemp -d "${TMPDIR:-/tmp}/t234-escape-matrix.XXXXXXXXXX")" || exit 2
trap 'rm -rf "$D"' EXIT
C="$D/matrix2.txt"
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
