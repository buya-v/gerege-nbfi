#!/bin/zsh
# ============================================================================
# T385 · Is the count in fire-program.sh genuinely an ARRAY COUNT under this zsh?
#
# T383 shipped, then caught with its own m00 control, a bug where
# `_ST_NSUM=${#${(f)_ST_SUMS}}` in an ASSIGNMENT context is SCALAR, so `${#...}`
# is a STRING LENGTH. It read 41 -- the character count of the summary -- and
# refused the healthy fire with "printed 41 TALLY LINES".
#
# This script re-derives that claim from first principles under the shell that
# actually runs the wrapper, and then exercises the SHIPPED idiom at 0, 1 and 2+
# lines. It touches no repo file.
# ============================================================================
set -u
print -r -- "zsh $ZSH_VERSION on $(uname -srm)"
print -r -- ""

SUM1='ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0'
print -r -- "one summary line is ${#SUM1} characters long"
print -r -- ""

print -r -- "--- A. THE BUG T383 CAUGHT: the nested form in an ASSIGNMENT context ---"
for n in 0 1 2 3; do
  local v=""
  case $n in
    0) v="" ;;
    1) v="$SUM1" ;;
    2) v="$SUM1"$'\n'"$SUM1" ;;
    3) v="$SUM1"$'\n'"$SUM1"$'\n'"$SUM1" ;;
  esac
  typeset -i bad=0
  bad=${#${(f)v}}
  printf '  lines=%d   BUGGY  _NSUM=${#${(f)v}}      -> %d\n' $n $bad
done
print -r -- ""

print -r -- "--- B. THE SHIPPED IDIOM: split into a real array, then count it ---"
for n in 0 1 2 3; do
  local v=""
  case $n in
    0) v="" ;;
    1) v="$SUM1" ;;
    2) v="$SUM1"$'\n'"$SUM1" ;;
    3) v="$SUM1"$'\n'"$SUM1"$'\n'"$SUM1" ;;
  esac
  typeset -a arr; arr=()
  typeset -i good=0
  if [[ -n "$v" ]]; then
    arr=( ${(f)v} )
    good=${#arr}
  fi
  printf '  lines=%d   SHIPPED  arr=( ${(f)v} ); ${#arr} -> %d   %s\n' $n $good \
    "$( (( good == n )) && print -r -- 'CORRECT' || print -r -- '*** WRONG' )"
done
print -r -- ""

print -r -- "--- C. the [[ -n ]] guard matters: what an EMPTY variable splits to ---"
EMPTY=""
typeset -a a0;  a0=( ${(f)EMPTY} )
typeset -a a0b; a0b=( "${(@f)EMPTY}" )
print -r -- "  arr=( \${(f)EMPTY} )      -> ${#a0} element(s)   (unquoted: empty word removed)"
print -r -- "  arr=( \"\${(@f)EMPTY}\" )  -> ${#a0b} element(s)   (quoted: ONE EMPTY element -- would report a phantom tally line)"
print -r -- "  the shipped code guards with [[ -n \"\$_ST_SUMS\" ]] before splitting, so neither form can produce a phantom."
print -r -- ""

print -r -- "--- D. glob hazard in the unquoted array assignment ---"
setopt localoptions nonomatch
GLOBBY="ROWS=45 FAIL_OPEN=* FAIL_SHUT=0 SKIPPED=0"
typeset -a g; g=( ${(f)GLOBBY} )
print -r -- "  a line carrying a glob metachar -> ${#g} element(s); value = ${g[1]}"
print -r -- "  (unquoted parameter expansion is not globbed unless GLOB_SUBST is set; it is off here.)"
print -r -- "  NOTE: this line could never reach the array anyway -- the anchored grep admits only [0-9]+ fields."
