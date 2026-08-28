#!/usr/bin/env bash
# T328 -- run the date-rule mutation arms and print them verbosely.
# The arms live in nexus/internal/apps/ledger/conformance/daterules_mutation_test.go
# so they run on every `go test ./...`, not only when someone remembers this script.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
echo "T328 mutation arms -- HEAD $(git -C "$REPO" rev-parse --short HEAD)"
echo "---"
cd "$REPO/nexus" || exit 2
go test ./internal/apps/ledger/conformance -run TestDateRuleMutationArms -v
rc=$?
echo "---"
echo "T328 mutation arms: EXIT $rc"
exit "$rc"
