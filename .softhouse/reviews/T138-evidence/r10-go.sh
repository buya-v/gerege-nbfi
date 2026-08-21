#!/bin/sh
# T138 — go build / go test / gofmt -l on the MERGED tree (P-24, P-30).
# The toolchain is repo-local at .softhouse/toolchain/go/bin/go; no host change.
set -u
D=${1:-/tmp/T138-merge}
cd "$D" || exit 2
. "$D/.softhouse/bin/go-env.sh"
echo "go version: $(go version)"
echo "GOROOT: $(go env GOROOT)"
cd "$D/nexus" || exit 2
echo
echo "=== go build ./..."
go build ./...; echo "BUILD_EXIT=$?"
echo
echo "=== go test ./..."
go test ./... 2>&1 | sed 's/^/   /'
echo
echo "=== gofmt -l ."
gofmt -l . | sed 's/^/   /'
echo "   (count: $(gofmt -l . | wc -l | tr -d ' '))"
echo "   NOTE: gofmt -w was NOT run (G-3)."
