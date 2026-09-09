#!/bin/bash
# $1=worktree $2=context -> number of registered <ctx>-wrong-* implementations.
cd "$1/nexus" 2>/dev/null || { printf 0; exit 0; }
b="./internal/apps/$2/conformance/cmd/conformance"
out=$(go run "$b" -root "$1" -list-implementations 2>/dev/null)
case "$out" in "") out=$(go run "$b" -list-implementations 2>/dev/null);; esac
printf '%s' "$(printf '%s\n' "$out" | grep -c "^$2-wrong-" | tr -dc '0-9')"
