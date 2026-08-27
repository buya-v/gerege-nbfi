#!/usr/bin/env bash
# T254 reviewer instrument: independent census of the mktemp population.
#
# P-75/P-80 compliance:
#   - `grep` in this shell is a ugrep WRAPPER (--ignore-files + 6 --exclude-dir).
#     We call /usr/bin/grep by ABSOLUTE PATH so the wrapper cannot apply.
#   - No `rg` (it is also a wrapper, and there is no binary).
#   - No `git grep -E` with \b (reads as a literal `b` on this build).
#   - set -euo pipefail.
#   - grep exit 1 == a real measured negative; exit >1 == ERROR -> ABORT.
#     We never use `|| true` / `|| echo 0` to paper over exit >1.
#
# Usage: 10-mktemp-census.sh <worktree-root> <outdir>
set -euo pipefail

ROOT="${1:?worktree root}"
OUT="${2:?outdir}"
G=/usr/bin/grep
[ -x "$G" ] || { echo "FATAL: $G not executable" >&2; exit 90; }

cd "$ROOT"

COMMIT="$(git rev-parse HEAD)"

echo "=== mktemp census ==="
echo "root:   $ROOT"
echo "commit: $COMMIT"
echo "grep:   $G ($("$G" --version 2>&1 | head -1))"
echo

# ---- DENOMINATOR TERM 1: every tracked file --------------------------------
git ls-files > "$OUT/.files.all"
N_ALL=$(wc -l < "$OUT/.files.all" | tr -d ' ')
echo "TERM-A  tracked files in repo ............... $N_ALL"

# ---- files that mention mktemp at all --------------------------------------
: > "$OUT/.files.mktemp"
while IFS= read -r f; do
  [ -f "$f" ] || continue
  set +e
  "$G" -Iqs -e 'mktemp' -- "$f"
  rc=$?
  set -e
  case "$rc" in
    0) printf '%s\n' "$f" >> "$OUT/.files.mktemp" ;;
    1) : ;;                                   # real measured negative
    *) echo "FATAL: grep exit $rc on $f" >&2; exit 91 ;;   # ERROR -> ABORT
  esac
done < "$OUT/.files.all"
N_FILES=$(wc -l < "$OUT/.files.mktemp" | tr -d ' ')
echo "TERM-B  tracked files mentioning 'mktemp' ... $N_FILES"
echo

echo "--- files mentioning mktemp ---"
cat "$OUT/.files.mktemp"
echo

# ---- SELECTOR SPLIT: every mktemp call vs every 'mktemp -t' call -----------
# S1 = every occurrence of the token mktemp  (the WIDE selector)
# S2 = every occurrence of 'mktemp' followed by a -t flag (the NARROW selector
#      both T253 implementations claim to have fixed: 10 sites)
: > "$OUT/.hits.all"
: > "$OUT/.hits.dasht"
while IFS= read -r f; do
  set +e
  "$G" -Ins -e 'mktemp' -- "$f" | sed "s|^|$f:|" >> "$OUT/.hits.all"
  rc=${PIPESTATUS[0]}
  set -e
  [ "$rc" -le 1 ] || { echo "FATAL: grep exit $rc on $f" >&2; exit 92; }

  set +e
  "$G" -Ins -E -e 'mktemp[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*-t([[:space:]]|$)' -- "$f" | sed "s|^|$f:|" >> "$OUT/.hits.dasht"
  rc=${PIPESTATUS[0]}
  set -e
  [ "$rc" -le 1 ] || { echo "FATAL: grep exit $rc on $f" >&2; exit 93; }
done < "$OUT/.files.mktemp"

N_ALLHITS=$(wc -l < "$OUT/.hits.all" | tr -d ' ')
N_DASHT=$(wc -l < "$OUT/.hits.dasht" | tr -d ' ')

echo "TERM-C  S1: every line mentioning mktemp ............ $N_ALLHITS"
echo "TERM-D  S2: every 'mktemp -t' call site ............. $N_DASHT"
echo
echo "--- S2: the 'mktemp -t' population (the NARROW selector) ---"
cat "$OUT/.hits.dasht"
echo
echo "--- S1 minus S2: mktemp lines that are NOT 'mktemp -t' ---"
sort "$OUT/.hits.all" > "$OUT/.s1.sorted"
sort "$OUT/.hits.dasht" > "$OUT/.s2.sorted"
comm -23 "$OUT/.s1.sorted" "$OUT/.s2.sorted"
echo
echo "=== end census (commit $COMMIT) ==="
