#!/bin/bash
# Two failure texts exist: "-root is required" (binaries that need it) and
# "flag provided but not defined: -root" (loanschedule, which rejects it).
c=$1; w=$2; b="./internal/apps/$c/conformance/cmd/conformance"
out=$(go run "$b" -root /Users/buv/gerege-nbfi -impl "$w" 2>&1)
case "$out" in
  *"not defined: -root"*|*"-root is required"*) out=$(go run "$b" -impl "$w" 2>&1);;
esac
n=$(printf '%s\n' "$out" | grep -oE 'parity_fail=[0-9]+' | head -1 | tr -dc '0-9')
[ -z "$n" ] && n=$(printf '%s\n' "$out" | grep -oE 'LOAN SCHEDULE [0-9]+ mismatch' | head -1 | tr -dc '0-9')
printf '%s' "${n:-0}"
