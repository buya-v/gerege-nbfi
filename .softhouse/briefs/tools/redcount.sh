#!/bin/bash
# $1=worktree $2=context. Some binaries REQUIRE -root, loanschedule REJECTS it.
# Try both, take whichever produced output. grep -c prints 0 and exits 1 -- never
# append `|| echo 0`, that yields "0\n0" and breaks arithmetic downstream.
cd "$1/nexus" 2>/dev/null || { printf 0; exit 0; }
b="./internal/apps/$2/conformance/cmd/conformance"
out=$(go run "$b" -root "$1" -list-implementations 2>/dev/null)
[ -z "$out" ] && out=$(go run "$b" -list-implementations 2>/dev/null)
printf '%s' "$(printf '%s\n' "$out" | grep -c "^$2-wrong-" | tr -dc '0-9')"
