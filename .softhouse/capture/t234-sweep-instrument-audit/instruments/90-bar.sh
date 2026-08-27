#!/usr/bin/env bash
# T234 — BAR.  Run from the worktree root.
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-a71e695cfa5bea70b || exit 9
. .softhouse/bin/go-env.sh
echo "### vectors digest in MY worktree (must be 73c3ea7b43dd75f04884072719a87fc8e1d255c1)"
git rev-parse HEAD:.softhouse/vectors
echo "### conformance"
bash .softhouse/conformance.sh
echo "CONFORMANCE_EXIT=$?"
echo "### go build / vet / test / gofmt"
cd nexus || exit 8
go build ./... ; echo "BUILD_EXIT=$?"
go vet ./...   ; echo "VET_EXIT=$?"
go test -count=1 ./... 2>&1 | tail -20 ; echo "TEST_DONE"
gofmt -l .     ; echo "GOFMT_DONE"
