#!/bin/zsh
# T377 — bench probe for the knob validator's PREDICATE, in isolation, before it is wired.
# Not a control: the control is `_knob_int` in `fire-program.sh`, driven end-to-end by
# `red-drive.zsh`. This file exists so the predicate's behaviour on each hostile value class
# is on the record separately from the file that ships it.
set -uo pipefail

_k() {
  local raw="$1"
  [[ "$raw" == <0-> ]] || { print -r -- "REFUSE not-a-non-negative-integer"; return 1; }
  local t="$raw"; while [[ "$t" == 0?* ]]; do t="${t#0}"; done
  local -i v; v=$t
  [[ "$v" == "$t" ]] || { print -r -- "REFUSE out-of-range (wrapped to $v)"; return 1; }
  print -r -- "ACCEPT $v"; return 0
}

typeset -a cases
cases=(
  '3600'
  '0'
  '007'
  '86400'
  'abc'
  '-100000'
  '99999999999999999999'
  '9223372036854775807'
  ''
  ' 5'
  '5 '
  '1e3'
  '0x10'
  '3600;print INJECTED'
  '0)) || { print INJECTED; }; ((1'
  '$(print INJECTED)'
)
for c in "${cases[@]}"; do
  printf '%-36s -> ' "${c:-<empty>}"
  _k "$c" 2>&1 | tr '\n' ' '
  print -r -- ""
done
