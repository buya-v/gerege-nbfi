#!/bin/bash
# T238 -- THE BAR, run by me, output pasted verbatim into the handoff.
# Harness invoked with `bash`, NEVER `sh` (exit 3 = wrong-interpreter refusal, not a failure).
# NEVER `gofmt -w` contract.go (G-3).
cd "$(git rev-parse --show-toplevel)" || exit 90
. .softhouse/bin/go-env.sh
echo "=== vector store digest (P-61) — MUST BE UNCHANGED BY T238 ==="
echo "  expected at main 477dc2d : 8968c559fa613e8642ab030bd0a029c17d147054"
echo "  measured here            : $(git rev-parse HEAD:.softhouse/vectors)"
echo
echo "=== go build / vet / test ==="
( cd nexus && go build ./... ) ; echo "go build   exit=$?"
( cd nexus && go vet   ./... ) ; echo "go vet     exit=$?"
( cd nexus && go test -count=1 ./... ) ; echo "go test    exit=$?"
echo
echo "=== gofmt -l (expect EXACTLY contract.go, and NEVER gofmt -w it — G-3) ==="
( cd nexus && gofmt -l . )
echo
echo "=== conformance --prove ==="
bash .softhouse/conformance.sh --prove; echo "--prove exit=$?"
echo
echo "=== conformance grade ==="
bash .softhouse/conformance.sh; echo "GRADE exit=$?"
