#!/bin/bash
# A2-34 reviewer: run the harness with the repo-local Go toolchain.
# Usage: bash run-bar.sh <outfile> [args...]
set -u
OUT="$1"; shift
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
bash .softhouse/conformance.sh "$@" > "$OUT" 2>&1
echo "EXIT=$?" >> "$OUT"
