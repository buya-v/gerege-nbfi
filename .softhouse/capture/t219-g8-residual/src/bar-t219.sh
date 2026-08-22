#!/bin/bash
# T219 — the Go half of the BAR, run from the worktree root. Uses the repo-local toolchain that
# .softhouse/bin/go-env.sh installs; GOROOT is deliberately absolute into the main checkout so
# isolated worktrees share one toolchain, exactly as that script documents.
set -u
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
cd "$(dirname "$0")/../../../../nexus" || exit 1
echo "PWD=$(pwd)"
go build ./... ; echo "BUILD_EXIT=$?"
go vet ./...   ; echo "VET_EXIT=$?"
go test -count=1 ./... 2>&1 | tail -12 ; echo "TEST_PIPE_EXIT=${PIPESTATUS[0]}"
echo "--- gofmt -l ---"
gofmt -l .
echo "--- gofmt count ---"
gofmt -l . | wc -l
