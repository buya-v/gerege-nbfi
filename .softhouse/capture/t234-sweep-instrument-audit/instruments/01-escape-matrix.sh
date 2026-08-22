#!/usr/bin/env bash
# T234 — the ESCAPE MATRIX.
# For each engine reachable from this repo, and each engine-dependent escape,
# record what the escape ACTUALLY means.  Positive and negative controls in
# every row (P-72: calibrate on a known positive before believing a negative).
set -u
C=/tmp/t234_matrix.txt
{
  printf 'balance column\n'        # L1: 'b' starts a word  -> \bbalance matches, \balance must NOT (if \b real)
  printf 'the balance column\n'    # L2: same
  printf 'unbalance column\n'      # L3: 'balance' NOT at word start
  printf 'x1 y\n'                  # L4: for \d
  printf 'x y\n'                   # L5: for \s
  printf 'x_y\n'                   # L6: for \w
} > "$C"
echo "### corpus $C"; nl -ba "$C"; echo

run() {  # run <label> <cmd...>  -- prints exit code and hit count
  local label="$1"; shift
  local out rc
  out=$("$@" 2>&1); rc=$?
  local n
  n=$(printf '%s' "$out" | { [ -n "$out" ] && wc -l | tr -d ' ' || echo 0; })
  [ -n "$out" ] && n=$(printf '%s\n' "$out" | wc -l | tr -d ' ') || n=0
  printf '  %-42s exit=%-2s hits=%-3s %s\n' "$label" "$rc" "$n" "$(printf '%s' "$out" | head -1 | cut -c1-40)"
}

echo "### ENGINE 1: /usr/bin/grep  (BSD grep 2.6.0-FreeBSD) -- what a .sh script gets"
for p in 'balance column' '\balance column' '\bbalance column' '\bunbalance' 'x\dy' 'x[0-9]y' 'x\sy' 'x y' 'x\wy'; do
  run "grep -E  '$p'" /usr/bin/grep -E -c "$p" "$C"
done
echo
echo "### ENGINE 2: git grep -E  (Apple Git 2.50.1, POSIX ERE via its own compiled regex)"
for p in 'balance column' '\balance column' '\bbalance column' 'x\dy' 'x\sy' 'x\wy'; do
  o=$(git grep -E -c -- "$p" -- .softhouse/capture/t234-sweep-instrument-audit 2>&1); rc=$?
  printf '  %-42s exit=%-2s out=%s\n' "git grep -E '$p'" "$rc" "$(printf '%s' "$o"|head -1)"
done
echo "  (repo-wide hit-line totals, git grep, tracked files only:)"
for p in 'balance column' '\balance column' '\bbalance column'; do
  for f in -E -P; do
    n=$(git grep $f -c -- "$p" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
    ff=$(git grep $f -l -- "$p" 2>/dev/null | wc -l | tr -d ' ')
    printf '    git grep %s %-20s lines=%-6s files=%s\n' "$f" "'$p'" "$n" "$ff"
  done
done
echo
echo "### ENGINE 3: /usr/bin/grep -P  (does it exist at all?)"
/usr/bin/grep -P 'balance' "$C" >/dev/null 2>&1; echo "  exit=$?  (2 = option rejected; NO OUTPUT, looks identical to 'no matches' to a careless caller)"
echo
echo "### ENGINE 4: ugrep 7.5.0 -- reachable ONLY via the interactive shell function wrapper."
echo "  Not reachable from inside a .sh script: BASH_FUNC_grep is not exported (see 00-engine-baseline)."
echo "  T232 measured ugrep -E DOES honour \\b.  [UNVERIFIED here from inside a script, by construction.]"
echo
echo "### ENGINE 5: python3 re -- the SOUND reference used by this audit"
python3 - "$C" <<'PY'
import re,sys
lines=open(sys.argv[1]).read().splitlines()
for p in [r'balance column', r'\balance column', r'\bbalance column', r'x\dy', r'x\sy', r'x\wy']:
    print("  python re %-22s hits=%d" % ("'"+p+"'", sum(1 for l in lines if re.search(p,l))))
PY
