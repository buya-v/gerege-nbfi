#!/bin/bash
# $1=worktree $2=context $3=impl -> kill count. Handles BOTH -root error texts.
cd "$1/nexus" 2>/dev/null || { printf 0; exit 0; }
b="./internal/apps/$2/conformance/cmd/conformance"
out=$(go run "$b" -root "$1" -impl "$3" 2>&1)
case "$out" in *"not defined: -root"*|*"-root is required"*) out=$(go run "$b" -impl "$3" 2>&1);; esac
n=$(printf '%s\n' "$out" | grep -oE 'parity_fail=[0-9]+' | head -1 | tr -dc '0-9')
[ -z "$n" ] && n=$(printf '%s\n' "$out" | grep -oE 'LOAN SCHEDULE [0-9]+ mismatch' | head -1 | tr -dc '0-9')
printf '%s' "${n:-0}"
