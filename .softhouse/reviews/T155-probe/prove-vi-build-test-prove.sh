#!/bin/bash
# T155 probe (vi) — the merged tree's own housekeeping, on the SCRATCH MERGE
# into current main (P-24), never on T154's branch tip alone.
#   go build / go vet / go test / conformance.sh --prove / gofmt -l
# Never pipe a build into head: head's exit code is not the compiler's.
set -u
POST=/tmp/t155/post
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
cd "$POST/nexus" || exit 9

echo "=== go build ./... ==="
go build ./... ; echo "exit=$?"
echo "=== go vet ./... ==="
go vet ./... ; echo "exit=$?"
echo "=== go test ./... ==="
go test ./... > /tmp/t155/out/vi-gotest.txt 2>&1; echo "exit=$?"
tail -20 /tmp/t155/out/vi-gotest.txt
echo "=== gofmt -l . (G-3: contract.go and NOTHING ELSE is expected; never gofmt -w) ==="
gofmt -l . ; echo "exit=$?"
echo "=== conformance.sh --prove ==="
cd "$POST" || exit 9
bash "$POST/.softhouse/conformance.sh" --prove > /tmp/t155/out/vi-prove.txt 2>&1; echo "exit=$?"
LC_ALL=C grep -acE '^PROOF OK' /tmp/t155/out/vi-prove.txt | sed 's/^/PROOF OK lines: /'
LC_ALL=C grep -acE '^PROOF FAIL' /tmp/t155/out/vi-prove.txt | sed 's/^/PROOF FAIL lines: /'
LC_ALL=C grep -aE 'passed|failed|VERDICT' /tmp/t155/out/vi-prove.txt | tail -5
