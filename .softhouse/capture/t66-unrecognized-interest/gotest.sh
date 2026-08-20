#!/bin/sh
# T66 helper: run go tests in this worktree with the repo-local toolchain.
set -eu
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export GOROOT="/Users/buv/gerege-nbfi/.softhouse/toolchain/go"
export GOCACHE="/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache"
export GOMODCACHE="/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache"
export PATH="$GOROOT/bin:$PATH"
cd "$ROOT/nexus"
exec go "$@"
