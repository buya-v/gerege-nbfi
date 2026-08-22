#!/usr/bin/env bash
# T244 sweep — P-26: hunt the CONCEPT "the corpus contains no reversal", not the sentence.
#
# ############################################################################
# ENGINE NOTE — READ THIS, IT IS A FINDING, NOT BOILERPLATE.
#
# `rg` IS NOT A BINARY ON THIS MACHINE. It is a SHELL FUNCTION that Claude Code
# installs into the interactive snapshot *precisely because ripgrep is absent*
# (`/Users/buv/.claude/shell-snapshots/snapshot-zsh-*.sh`, guarded by
# `if ! (unalias rg; command -v rg)`). The function re-execs the `claude` binary
# with ARGV0=rg. There is no rg in /usr/bin, /usr/local/bin or /opt/homebrew/bin.
#
# CONSEQUENCE: any sweep SCRIPT that calls `rg` gets `rg: command not found`
# and, if it does not fail closed, prints "(no hits)" for every pattern and
# exits 0 — FALSE CORROBORATION. That is the fail-OPEN class again, arriving by
# a mechanism this program has not catalogued (the catalogued one is the dead-`cd`).
# The first version of THIS script hit it; the fail-closed calibration caught it.
#
# So this script uses ONLY script-safe engines:
#   ENGINE 1 : BSD grep 2.6.0-FreeBSD   (-r -n -i -E; honours \b \d \s \w)
#   ENGINE 2 : git grep                 (-n -i -E over TRACKED files)
#   ENGINE 3 : python3 re               (the MULTI-LINE pass, re.DOTALL)
#   NOT USED : rg        -> shell-function only, invisible to scripts (above)
#              grep -P   -> DOES NOT EXIST here, exit 2 (verified)
#              ugrep/ggrep/pcre2grep -> ABSENT (verified with command -v)
#              `\b` under `git grep -E` -> reads as literal 'b', silent zero (P-53/P-12)
#
# ANCHORING: the stem is `revers` with NO RIGHT ANCHOR. T224's sweep was killed by
# right-anchoring an inflected stem, not by the engine. `revers` catches
# reversal/reversals/reversed/reversing/reverse/reversion.
#
# FAIL MODE: FAIL-CLOSED. Calibration on a KNOWN POSITIVE runs FIRST and the
# script ABORTS (exit 8) if any engine cannot see it.
# ############################################################################
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || { echo "FATAL: cannot resolve own dir"; exit 9; }
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || { echo "FATAL: cannot resolve repo root"; exit 9; }
cd "$ROOT" || { echo "FATAL: cannot cd to $ROOT"; exit 9; }
[ -f docs/adr/DEC-2-gl-accounting-adapter.md ] || { echo "FATAL: DEC-2 absent under $ROOT — wrong tree, refusing"; exit 9; }

G=/usr/bin/grep

echo "===================== T244 SWEEP: stale 'no reversal' reason ====================="
echo "resolved root  : $ROOT"
echo "pwd            : $(pwd)"
echo "git HEAD       : $(git rev-parse HEAD)"
echo "git branch     : $(git rev-parse --abbrev-ref HEAD)"
echo "measured at    : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo "engine 1       : $($G --version 2>&1 | head -1)"
echo "engine 2       : git $(git --version | awk '{print $3}') grep"
echo "engine 3       : python3 $(python3 -c 'import sys;print(sys.version.split()[0])') re (multi-line)"
echo "rg             : $(command -v rg >/dev/null 2>&1 && echo 'resolves (SHELL FUNCTION ONLY — unusable here)' || echo 'command not found inside script — CONFIRMED')"
echo

# ---- SCOPE, stated per P-66/P-70 BEFORE any negative is recorded ----
echo "--- SCOPE (stated before any negative, P-66/P-70) ---"
echo "tracked files (git ls-files)      : $(git ls-files | wc -l | tr -d ' ')"
echo "all files on disk excl .git       : $(find . -type f -not -path './.git/*' | wc -l | tr -d ' ')"
echo "  of which .md                    : $(find . -type f -name '*.md' -not -path './.git/*' | wc -l | tr -d ' ')"
echo "  of which .json                  : $(find . -type f -name '*.json' -not -path './.git/*' | wc -l | tr -d ' ')"
echo "SEARCH SCOPE = the whole worktree on disk, excluding .git only."
echo

# ---- CALIBRATION ON A KNOWN POSITIVE (P-72). FAIL-CLOSED. ----
echo "--- CALIBRATION: known positive = DEC-2 §4.4 line 823 ---"
C1=$($G -rniE 'corpus contains no reversal' --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ')
echo "engine 1 BSD grep  'corpus contains no reversal' -> hit lines: $C1"
C2=$(git grep -niE 'corpus contains no reversal' -- . 2>/dev/null | wc -l | tr -d ' ')
echo "engine 2 git grep  'corpus contains no reversal' -> hit lines: $C2"
C3=$(python3 "$SELF_DIR/mlsweep.py" --count 'corpus contains no reversal' 2>/dev/null)
echo "engine 3 python3   'corpus contains no reversal' -> hit lines: $C3"
C4=$($G -rniE 'revers' --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ')
echo "engine 1 unanchored stem 'revers'                -> hit lines: $C4"
if [ "${C1:-0}" -lt 1 ] || [ "${C2:-0}" -lt 1 ] || [ "${C3:-0}" -lt 1 ] || [ "${C4:-0}" -lt 1 ]; then
  echo
  echo "!!!! CALIBRATION FAILED — an engine cannot see a string KNOWN to be present."
  echo "!!!! ABORTING (exit 8). Any '(no hits)' after this point would be an artefact."
  exit 8
fi
echo "CALIBRATION PASSED on all three engines. Negatives below are MEASUREMENTS."
echo

# ---- NEGATIVE CONTROL: prove the instrument CAN return zero ----
echo "--- NEGATIVE CONTROL (token that must not exist) ---"
N1=$($G -rniE 'zzq-t244-nonexistent-token' --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ')
echo "engine 1 -> $N1 (expect 0)"
N3=$(python3 "$SELF_DIR/mlsweep.py" --count 'zzq-t244-nonexistent-token' 2>/dev/null)
echo "engine 3 -> $N3 (expect 0)"
echo

# ---- PASS 1: LINE-ORIENTED, the concept in many phrasings ----
echo "================ PASS 1 — LINE-ORIENTED (BSD grep -rniE) ================"
P1=(
  'corpus contains no revers'
  'contains no revers'
  'no revers'
  'without a revers'
  'never .{0,20}revers'
  'lack[s]? .{0,20}revers'
  'absent.{0,40}revers'
  'revers.{0,40}(absent|missing|not captured|not observed|not present)'
  '(no|zero|nothing).{0,60}revers'
  'revers.{0,60}(no capture|not captured|no vector|nothing to grade)'
  'ErrNoDiscriminatingVector'
  'retired by one capture'
)
for p in "${P1[@]}"; do
  echo "--- PATTERN: $p"
  out=$($G -rniE "$p" --exclude-dir=.git . 2>/dev/null)
  if [ -z "$out" ]; then echo "    (no hits)"; else echo "$out" | cut -c1-240 | sed 's/^/    /'; fi
  echo
done

# ---- PASS 2: MULTI-LINE. T234 found 743 matches SPANNING A NEWLINE. ----
echo "================ PASS 2 — MULTI-LINE (python3 re.DOTALL), spanning newlines ================"
python3 "$SELF_DIR/mlsweep.py"
echo

# ---- PASS 3: cross-engine confirmation ----
echo "================ PASS 3 — CROSS-ENGINE on 'contains no revers' ================"
echo "--- engine 1 BSD grep:"
$G -rniE 'contains no revers' --exclude-dir=.git . 2>/dev/null | cut -c1-200 | sed 's/^/    /'
echo "--- engine 2 git grep (tracked only):"
git grep -niE 'contains no revers' -- . 2>/dev/null | cut -c1-200 | sed 's/^/    /'
echo

echo "================ SWEEP COMPLETE ================"
