#!/usr/bin/env bash
# T244 BAR — NO-REGRESSION check. This task changes NO code and NO vectors:
# it prepares a DEC-2 revision as a proposed diff in a handoff and nothing else.
# So the bar is "everything still exactly as the driver measured it on main".
#
# Harness is invoked with `bash`, NEVER `sh` (exit 3 = wrong-interpreter refusal).
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || { echo "FATAL: cannot resolve own dir"; exit 9; }
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || { echo "FATAL: cannot resolve repo root"; exit 9; }
cd "$ROOT" || { echo "FATAL: cannot cd"; exit 9; }
[ -f .softhouse/conformance.sh ] || { echo "FATAL: conformance.sh absent under $ROOT"; exit 9; }

# Repo-local Go toolchain (contents of .softhouse/bin/go-env.sh, inlined because
# this agent's sandbox refuses `. script`).
GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
export GOROOT="$GEREGE_TOOLCHAIN/go"
export GOPATH="$GEREGE_TOOLCHAIN/gopath"
export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
export PATH="$GOROOT/bin:$PATH"

echo "############ T244 BAR ############"
echo "root           : $ROOT"
echo "git HEAD       : $(git rev-parse HEAD)"
echo "git branch     : $(git rev-parse --abbrev-ref HEAD)"
echo "origin/main    : $(git rev-parse origin/main)"
echo "merge-base     : $(git merge-base HEAD origin/main)"
echo "measured at    : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo "go version     : $(go version)"
echo
echo "### VECTOR STORE DIGEST (P-61) — must be UNCHANGED BY THIS TASK ###"
echo "expected (main 477dc2d) : 8968c559fa613e8642ab030bd0a029c17d147054"
echo "actual   (this branch)  : $(git rev-parse HEAD:.softhouse/vectors)"
echo
echo "### files this branch changes vs origin/main (three-dot) ###"
git diff --stat origin/main...HEAD
echo
echo "### did this task touch anything it must not? ###"
echo "docs/adr/            : $(git diff --name-only origin/main...HEAD -- docs/adr/ | wc -l | tr -d ' ') file(s)  [MUST BE 0]"
echo ".softhouse/gates.md  : $(git diff --name-only origin/main...HEAD -- .softhouse/gates.md | wc -l | tr -d ' ') file(s)  [MUST BE 0]"
echo ".softhouse/vectors/  : $(git diff --name-only origin/main...HEAD -- .softhouse/vectors/ | wc -l | tr -d ' ') file(s)  [MUST BE 0]"
echo "nexus/               : $(git diff --name-only origin/main...HEAD -- nexus/ | wc -l | tr -d ' ') file(s)  [MUST BE 0]"
echo
echo "########## CONFORMANCE (bash, never sh) ##########"
bash .softhouse/conformance.sh
CONF_RC=$?
echo "conformance exit code = $CONF_RC"
echo
echo "########## --prove ##########"
bash .softhouse/conformance.sh --prove
PROVE_RC=$?
echo "--prove exit code = $PROVE_RC"
echo
echo "########## GO ##########"
cd "$ROOT/nexus" || exit 9
echo "--- go build ./..."
go build ./... ; echo "go build rc=$?"
echo "--- go vet ./..."
go vet ./... ; echo "go vet rc=$?"
echo "--- go test -count=1 ./..."
go test -count=1 ./... ; echo "go test rc=$?"
echo "--- gofmt -l . (expect EXACTLY contract.go — never gofmt -w it, G-3)"
gofmt -l .
echo "gofmt listed $(gofmt -l . | wc -l | tr -d ' ') file(s)"
echo
echo "############ BAR COMPLETE (conformance rc=$CONF_RC, prove rc=$PROVE_RC) ############"
