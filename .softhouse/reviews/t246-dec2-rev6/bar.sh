#!/usr/bin/env bash
# T246 — THE BAR, run by the reviewer itself, never quoted from another worker.
# Harness invoked with `bash`, NEVER `sh` (exit 3 = wrong interpreter, and it is NOT an outage).
set -uo pipefail
cd "$(dirname "$0")/../../.." || { echo "FATAL: cannot reach the repo root"; exit 9; }
ROOT="$(pwd)"
echo "repo root : $ROOT"
test -f "$ROOT/.softhouse/conformance.sh" || { echo "FATAL: no conformance.sh under $ROOT"; exit 9; }
echo

echo "=== 0. STAMPS ==="
echo -n "HEAD              : "; git rev-parse HEAD
echo -n "branch            : "; git branch --show-current
echo -n "origin/main       : "; git rev-parse origin/main
echo -n "merge-base        : "; git merge-base HEAD origin/main
echo -n "vector store tree : "; git rev-parse HEAD:.softhouse/vectors
echo -n "loanschedule tree : "; git rev-parse HEAD:.softhouse/vectors/loanschedule
echo -n "ledger tree       : "; git rev-parse HEAD:.softhouse/vectors/ledger
echo

# shellcheck disable=SC1091
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
echo "go: $(go version)"
echo

echo "=== 1. CONFORMANCE (bash, never sh) ==="
bash .softhouse/conformance.sh > /tmp/t246-conf.txt 2>&1
CONF=$?
echo "conformance exit = $CONF"
echo
echo "--- PROBE LINE: test PRESENCE first (four exit-2 paths precede it) ---"
PROBE="$(LC_ALL=C /usr/bin/grep -a 'probe' /tmp/t246-conf.txt | /usr/bin/grep -a -i -e 'oracle' -e 'probe =' | head -5)"
if [ -z "$PROBE" ]; then
  echo "  *** PROBE LINE ABSENT — this is NOT an oracle-down reading, the harness never got there ***"
else
  echo "$PROBE" | sed 's/^/  /'
fi
echo
echo "--- VERDICT ---"
LC_ALL=C /usr/bin/grep -a -e 'VERDICT' /tmp/t246-conf.txt | sed 's/^/  /'
echo
echo "--- corpus lines ---"
LC_ALL=C /usr/bin/grep -a -e 'parity vectors' -e 'LEDGER' -e 'inadmissible' -e 'harness error' -e 'invariant violation' -e 'cells compared' -e 'money cells' -e 'NOT RUN' -e 'EXEMPTED' -e 'GROUNDED' /tmp/t246-conf.txt | head -60 | sed 's/^/  /'
echo
echo "--- census pins ---"
LC_ALL=C /usr/bin/grep -a -e '== pinned' -e '!= pinned' -e 'census' /tmp/t246-conf.txt | head -40 | sed 's/^/  /'
echo

echo "=== 2. --prove ==="
bash .softhouse/conformance.sh --prove > /tmp/t246-prove.txt 2>&1
PROVE=$?
echo "prove exit = $PROVE"
LC_ALL=C /usr/bin/grep -a -e 'passed' -e 'failed' -e 'PROOF' /tmp/t246-prove.txt | tail -10 | sed 's/^/  /'
echo

echo "=== 3. GO ==="
cd "$ROOT/nexus" || exit 9
echo -n "go build ./...   : "; go build ./... 2>&1 | tee /tmp/t246-build.txt | wc -l | tr -d ' '; echo "   (lines of output; 0 = clean)"
echo -n "go vet ./...     : "; go vet ./... 2>&1 | tee /tmp/t246-vet.txt | wc -l | tr -d ' '; echo "   (lines of output; 0 = clean)"
go test ./... -count=1 > /tmp/t246-test.txt 2>&1; T=$?
echo "go test -count=1 : exit $T"
LC_ALL=C /usr/bin/grep -a -e '^FAIL' -e '^ok' /tmp/t246-test.txt | head -30 | sed 's/^/  /'
echo
echo "gofmt -l (MUST be exactly contract.go — NEVER gofmt -w it, G-3):"
gofmt -l . | sed 's/^/  /'
echo

echo "=== 4. THE STORE MUST BE UNCHANGED ==="
cd "$ROOT" || exit 9
echo -n "vector store tree AFTER : "; git rev-parse HEAD:.softhouse/vectors
echo "git status of protected paths (MUST be empty):"
git status --porcelain -- .softhouse/vectors docs/adr .softhouse/gates.md nexus | sed 's/^/  /'
echo "  (end)"
echo
echo "full transcripts: /tmp/t246-conf.txt /tmp/t246-prove.txt /tmp/t246-test.txt"
