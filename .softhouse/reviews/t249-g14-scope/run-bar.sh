#!/bin/bash
# T249 BAR runner. Sets the repo-local Go toolchain exactly as
# .softhouse/bin/go-env.sh does, then invokes the harness with `bash`
# (exit 3 = wrong interpreter). Writes the transcript beside this file.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WT="$(cd "$HERE/../../.." && pwd)"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"
cd "$WT"
{
  echo "T249 BAR"
  echo "worktree : $WT"
  echo "HEAD     : $(git rev-parse HEAD)"
  echo "vectors  : $(git rev-parse HEAD:.softhouse/vectors)"
  echo "go       : $(go version 2>&1)"
  echo "========================================================="
} > "$HERE/bar-output.txt"
bash .softhouse/conformance.sh >> "$HERE/bar-output.txt" 2>&1
rc=$?
echo "CONFORMANCE_EXIT=$rc" >> "$HERE/bar-output.txt"
echo "CONFORMANCE_EXIT=$rc"
