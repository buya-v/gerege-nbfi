#!/bin/bash
# T155 probe (viii) — store_integrity_test.go's own header says, of the WHOLE
# FILE: "This file must COMPILE ON MAIN, because a guard that only compiles
# against the fix cannot be driven red on the bytes that had the defect ... the
# whole file is therefore a valid main test, and on main it fails."
#
# T154 added TestStoreFileCensus to that file, which calls StoreFileCensus — a
# function that does not exist on main. Drive the claim.
set -u
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
SCRATCH=/tmp/t155/main-plus-test
rm -rf "$SCRATCH"; cp -R /tmp/t155/main "$SCRATCH"
P="$SCRATCH/nexus/internal/apps/loanschedule/conformance"

echo "=== control: main's own tree compiles ==="
( cd "$SCRATCH/nexus" && go vet ./internal/apps/loanschedule/conformance ) 2>&1 | tail -5
echo "control exit=${PIPESTATUS[0]}"
echo

echo "=== T154's store_integrity_test.go dropped onto MAIN ==="
cp /tmp/t155/post/nexus/internal/apps/loanschedule/conformance/store_integrity_test.go "$P/store_integrity_test.go"
( cd "$SCRATCH/nexus" && go vet ./internal/apps/loanschedule/conformance ) > /tmp/t155/out/viii-vet.txt 2>&1
echo "exit=$?"
head -12 /tmp/t155/out/viii-vet.txt
echo
echo "=== T154's conformance_test.go dropped onto MAIN ==="
rm -rf "$SCRATCH"; cp -R /tmp/t155/main "$SCRATCH"
cp /tmp/t155/post/nexus/internal/apps/loanschedule/conformance/conformance_test.go "$P/conformance_test.go"
( cd "$SCRATCH/nexus" && go vet ./internal/apps/loanschedule/conformance ) > /tmp/t155/out/viii-vet2.txt 2>&1
echo "exit=$?"
head -12 /tmp/t155/out/viii-vet2.txt
