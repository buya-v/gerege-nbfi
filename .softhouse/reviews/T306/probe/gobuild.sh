#!/bin/bash
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acee94120db93ffce
. "$W/.softhouse/bin/go-env.sh"
cd "$W/nexus" || exit 1
go build ./... || exit 1
echo "BUILD OK"
go vet ./internal/apps/ledger/... || exit 1
echo "VET OK"
go test ./internal/apps/ledger/... "$@" 2>&1 | tail -60
