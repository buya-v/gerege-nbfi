#!/bin/bash
# T149 — grade a SCRATCH vector store against the registered Go port.
#
# This is NOT .softhouse/conformance.sh and does not replace it: it skips the shell
# guards, the float grep guards and the live oracle probe, and it asserts the probe as
# "up" from the caller. It exists for ONE purpose — to find out whether a CANDIDATE
# vector is admissible and whether the port reproduces it, WITHOUT putting the candidate
# into the real store first. Every verdict that this task reports as a conformance
# verdict comes from `bash .softhouse/conformance.sh`, never from here.
#
#     bash grade-scratch-store.sh <store-dir> [extra args...]
set -u
STORE="$1"; shift || true
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
TC=/Users/buv/gerege-nbfi/.softhouse/toolchain
export GOROOT="$TC/go" GOPATH="$TC/gopath" GOCACHE="$TC/gocache" GOMODCACHE="$TC/gomodcache"
export PATH="$TC/go/bin:$PATH"
cd "$REPO/nexus" || exit 2
go run ./internal/apps/loanschedule/conformance/cmd/conformance \
    -store "$STORE" -oracle-probe=up "$@"
