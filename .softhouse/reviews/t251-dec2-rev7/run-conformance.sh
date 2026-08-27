#!/usr/bin/env bash
# T251: run the conformance harness once from THIS worktree and capture the full
# transcript. Nothing here modifies the harness, the vectors or the ADR.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
export GOROOT="$GEREGE_TOOLCHAIN/go"
export GOPATH="$GEREGE_TOOLCHAIN/gopath"
export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
export PATH="$GOROOT/bin:$PATH"

OUT=".softhouse/reviews/t251-dec2-rev7/conformance-2871f17.log"

set +e
bash .softhouse/conformance.sh >"$OUT" 2>&1
rc=$?
set -e
echo "CONFORMANCE EXIT=$rc"
echo "TRANSCRIPT LINES=$(wc -l <"$OUT")"
exit 0
