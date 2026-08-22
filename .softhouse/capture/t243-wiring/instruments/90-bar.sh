#!/bin/bash
# T243 — THE BAR, run by T243 itself. Harness invoked with `bash`, never `sh`
# (exit 3 is its wrong-interpreter refusal, not a failure and not an outage).
# `gofmt -w` is NEVER run on contract.go (G-3).
set -uo pipefail
R="$(git rev-parse --show-toplevel)"
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"
L=/tmp/t243-bar
mkdir -p "$L"

echo "commit         : $(git rev-parse HEAD)"
echo "fork point     : $(git merge-base HEAD origin/main)"
echo "origin/main    : $(git rev-parse origin/main)"
echo "vector store   : $(git rev-parse HEAD:.softhouse/vectors)"
echo

bash .softhouse/conformance.sh > "$L/graded.txt" 2>&1
echo "conformance.sh exit  : $?"
LC_ALL=C /usr/bin/grep -aE 'probe = |^VERDICT|parity vectors +PASS|contract-refusal|self-test fixtures|cells compared|ungraded|ledger parity|ledger oracle-refusal|ledger inadmissible|ledger harness errors|ledger citations|refused|inadmissible|harness errors|invariant violations|NOT RUN|EXEMPTED|GROUNDED|census READ|CENSUS wrong ledger|KILLED |SURVIVED |DIED through|CENSUS fail-open|frontier' "$L/graded.txt"
echo

bash .softhouse/conformance.sh --prove > "$L/prove.txt" 2>&1
echo "--prove exit         : $?"
LC_ALL=C /usr/bin/grep -aE '^PROOFS:|^PROOF FAIL' "$L/prove.txt"
echo

cd "$R/nexus"
go build ./... > "$L/build.txt" 2>&1;        echo "go build exit        : $?"
go vet   ./... > "$L/vet.txt" 2>&1;          echo "go vet exit          : $?"
go test -count=1 ./... > "$L/test.txt" 2>&1; echo "go test exit         : $?"
LC_ALL=C /usr/bin/grep -aE '^(ok|FAIL|---)' "$L/test.txt"
echo "gofmt -l             :"
gofmt -l . | LC_ALL=C /usr/bin/sed 's/^/    /'
