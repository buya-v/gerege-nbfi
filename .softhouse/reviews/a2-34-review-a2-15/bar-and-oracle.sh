#!/bin/bash
# A2-34: the rest of the BAR, plus the P-69 oracle re-run and the DEC-2 restraint check.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"

echo "######## CITATION TIER — which of the three tiers each of the 12 components lands on"
python3 - "$R" <<'PY'
import json, os, sys, glob
R = sys.argv[1]
for f in sorted(glob.glob(os.path.join(R, ".softhouse/vectors/ledger/*.json"))):
    v = json.load(open(f)); p = v["provenance"]
    for label, refk, idk in (("RESP", "capture_ref", "capture_case_id"),
                             ("REQ ", "request_capture_ref", "request_capture_case_id")):
        ap = os.path.join(R, p[refk]); cid = p[idk]
        raw = open(ap, "rb").read()
        base = os.path.splitext(ap)[0]
        if base.endswith(".req"): base = base[:-4]
        side = b""
        if os.path.exists(base + ".http"): side = open(base + ".http", "rb").read()
        if cid.encode() in raw: tier = "1 ARTEFACT BYTES  (strongest)"
        elif cid.encode() in side: tier = "2 .http SIDECAR"
        elif cid in os.path.basename(ap): tier = "3 FILE NAME       (weakest: tautological)"
        else: tier = "*** NONE — would be refused"
        print(f"  {v['case_id']:48s} {label} tier {tier}")
PY

echo
echo "######## --prove"
bash .softhouse/conformance.sh --prove > /tmp/a234-prove.txt 2>&1; echo "  exit=$?"
tail -4 /tmp/a234-prove.txt
LC_ALL=C /usr/bin/grep -aE "passed|failed" /tmp/a234-prove.txt | tail -3

echo
echo "######## conformance.sh loanschedule (filtered)"
bash .softhouse/conformance.sh loanschedule > /tmp/a234-ls.txt 2>&1; echo "  exit=$?"
LC_ALL=C /usr/bin/grep -aE "^    (parity vectors|contract-refusal|self-test|cells compared|inadmissible|refused|harness errors)|VERDICT|LEDGER NOT SELECTED" /tmp/a234-ls.txt

echo
echo "######## go build / vet / test / gofmt"
cd nexus
go build ./... ; echo "  go build exit=$?"
go vet ./... 2>&1 | tail -3 ; echo "  go vet done"
go test -count=1 ./... 2>&1 | tail -8
echo "  --- gofmt -l over the whole module:"
gofmt -l .
echo "  (must be EXACTLY internal/apps/loanschedule/contract/contract.go — G-3)"
cd "$R"

echo
echo "######## VECTOR STORE DIGEST"
echo -n "  git rev-parse HEAD:.softhouse/vectors = "; git rev-parse HEAD:.softhouse/vectors
echo -n "  git rev-parse HEAD:.softhouse/vectors/loanschedule = "; git rev-parse HEAD:.softhouse/vectors/loanschedule
echo -n "  git rev-parse HEAD:.softhouse/vectors/_selftest = "; git rev-parse HEAD:.softhouse/vectors/_selftest

echo
echo "######## P-69 — RE-RUN sql/q4-a2-26-ledger-state.sql against the LIVE oracle"
ls -la .softhouse/capture/tierA-a2/sql/q4-a2-26-ledger-state.sql .softhouse/capture/tierA-a2/sql/q7-a2-15-ledger-state-json.sql
echo "--- containers:"
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' 2>&1 | head

echo
echo "######## DEC-2 RESTRAINT — was the ratified ADR amended?"
git log --oneline -3 -- docs/adr/DEC-2-gl-accounting-adapter.md
echo "  last commit touching DEC-2 above; A2-15's merge is d76594a / branch tip 1325e8b"
git diff --name-only 1325e8b~1 1325e8b -- docs/ ; echo "  (docs/ touched by A2-15's own commit? empty = no)"
echo "--- DEC-2 §4.4's I-5 sentence, as it stands today:"
LC_ALL=C /usr/bin/grep -n -aF 'contains no reversal' docs/adr/DEC-2-gl-accounting-adapter.md
LC_ALL=C /usr/bin/grep -n -aF 'I-5' docs/adr/DEC-2-gl-accounting-adapter.md | head -6
echo "--- A2-15's corrected reason, recorded in code instead:"
LC_ALL=C /usr/bin/grep -n -aF 'A2-348' nexus/internal/apps/ledger/conformance/invariants.go | head -4
LC_ALL=C /usr/bin/grep -n -aF 'I-5' nexus/internal/apps/ledger/conformance/invariants.go | head -6
