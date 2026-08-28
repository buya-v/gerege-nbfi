#!/bin/zsh
# T280 — check the proposed one-character fix for F-A actually fixes it, in isolation.
# OLD = the shipped strip class [ \t\r\n"] ; NEW = the same class plus {}
body_last='{
  "host": "h",
  "pid": 123,
  "started_at": "2026-08-28T00:00:00Z",
  "released_at": null
}'
body_last_real='{
  "host": "h",
  "pid": 123,
  "released_at": "2026-08-28T09:00:00Z"
}'
body_mid='{
  "host": "h",
  "released_at": null,
  "pid": 123
}'
read_old() { local body="$1" v
  [[ "$body" == *'"released_at":'* ]] || return 0
  v="${${body#*\"released_at\":}%%,*}"
  v="${v//[$' \t\r\n\"']/}"
  [[ "$v" == null || -z "$v" ]] && return 0
  print -r -- "$v"; }
# VARIANT A (naive: add {} to the strip class) -- DOES NOT WORK, zsh rejects the pattern.
# VARIANT B: cut the value at the first '}' as well as the first ',', then strip as before.
read_new() { local body="$1" v
  [[ "$body" == *'"released_at":'* ]] || return 0
  v="${${body#*\"released_at\":}%%,*}"
  v="${v%%\}*}"
  v="${v//[$' \t\r\n\"']/}"
  [[ "$v" == null || -z "$v" ]] && return 0
  print -r -- "$v"; }
print -r -- "  case        OLD reader                NEW reader (proposed)"
for n in last last_real mid; do
  case $n in
    last)      b="$body_last" ;;
    last_real) b="$body_last_real" ;;
    mid)       b="$body_mid" ;;
  esac
  printf '  %-10s  %-24s %s\n' "$n" "'$(read_old "$b")'" "'$(read_new "$b")'"
done
print -r -- ""
print -r -- "  expected: last -> '' (null, lock HELD) ; last_real -> the timestamp ; mid -> ''"
