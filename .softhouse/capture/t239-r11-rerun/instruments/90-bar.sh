#!/usr/bin/env bash
# T239 — THE BAR. No-regression: this task ships no code, only evidence + a handoff.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a63a7abf43fa9b0dc
cd "$R" || { echo "FATAL: cd failed"; exit 2; }

. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

echo "=== provenance ==="
echo "branch          : $(git rev-parse --abbrev-ref HEAD)"
echo "HEAD            : $(git rev-parse HEAD)"
echo "merge-base      : $(git merge-base HEAD origin/main)"
echo "origin/main     : $(git rev-parse origin/main)"
echo "vector digest   : $(git rev-parse HEAD:.softhouse/vectors)"
echo "  expected      : 8968c559fa613e8642ab030bd0a029c17d147054  (UNCHANGED BY ME)"
echo

echo "=== go build / vet / test (module root nexus/) ==="
cd "$R/nexus" || exit 2
go build ./... 2>&1 | tail -20; echo "go build   rc=${PIPESTATUS[0]}"
go vet ./...   2>&1 | tail -20; echo "go vet     rc=${PIPESTATUS[0]}"
go test -count=1 ./... 2>&1 | tail -30; echo "go test    rc=${PIPESTATUS[0]}"
echo
echo "=== gofmt -l (must be exactly contract.go; NEVER gofmt -w it, G-3) ==="
gofmt -l . 2>&1
echo "--- end gofmt list ---"
cd "$R" || exit 2
echo

echo "=== conformance harness (bash, never sh) ==="
bash .softhouse/conformance.sh > /tmp/t239-conf.txt 2>&1
rc=$?
echo "harness exit code: $rc"
echo
echo "--- PROBE LINE: test PRESENCE first (four exit-2 paths precede it) ---"
/usr/bin/grep -n -a -i 'probe' /tmp/t239-conf.txt | head -5
echo
echo "--- VERDICT / counts ---"
/usr/bin/grep -n -a -E 'VERDICT|parity|cells|inadmissible|harness error|invariant|pinned|oracle-refusal' /tmp/t239-conf.txt | head -60
