#!/usr/bin/env bash
# T246 — P-22 RED/GREEN drive of the LANDING HAZARD.
#
# CLAIM UNDER TEST (T244, G-13): `admit.go:50-51` marks a ledger vector INADMISSIBLE when its
# `dec2_revision` differs from PIN-ledger.json; the check is vector-to-pin ONLY and never reads
# the ADR. Therefore DEC-2 revision 6 must land with the pin STAYING AT 5.
#
# This script proves BOTH directions, in a SCRATCH COPY under /tmp. It NEVER writes to the
# worktree's .softhouse/vectors/ (T246 is forbidden from editing it).
#   GREEN : pin 5 + vectors 5   -> 0 inadmissible
#   RED-A : pin 6 + vectors 5   -> 6 inadmissible  (the "bump the pin alone" mistake)
#   RED-B : pin 5 + vectors 6   -> 6 inadmissible  (the mirror mistake)
#   GREEN2: pin 6 + vectors 6   -> 0 inadmissible  (proves the check is RELATIVE, not absolute-5)
# A scenario that does not move in the expected direction is a FAILURE of this instrument.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../../.." && pwd)"
echo "source tree: $SRC"
test -f "$SRC/.softhouse/vectors/PIN-ledger.json" || { echo "FATAL: cannot see the vector store from $SRC"; exit 9; }
test -f "$SRC/nexus/go.mod" || { echo "FATAL: cannot see nexus/go.mod from $SRC"; exit 9; }

# shellcheck disable=SC1091
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
echo "go: $(go version)"

SCRATCH=/tmp/t246-pin-red
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH/.softhouse"
cp -a "$SRC/nexus" "$SCRATCH/nexus"
cp -a "$SRC/.softhouse/vectors" "$SCRATCH/.softhouse/vectors"
# Admit() resolves provenance.capture_ref against the repository root, so the capture
# corpus must be reachable. Symlinked read-only rather than copied: nothing in this
# instrument writes under it, and a missing capture tree made the GREEN control fail
# loudly on the first run (fail-CLOSED, exactly as intended).
ln -s "$SRC/.softhouse/capture" "$SCRATCH/.softhouse/capture"
test -f "$SCRATCH/.softhouse/capture/tierA-a2/out/A2-347-je-manual-readback.json" \
  || { echo "FATAL: capture corpus not reachable from the scratch root"; exit 9; }
echo "scratch: $SCRATCH"
echo

setpin() { python3 - "$SCRATCH/.softhouse/vectors/PIN-ledger.json" "$1" <<'PY'
import json,sys,re
p,v=sys.argv[1],int(sys.argv[2])
s=open(p).read()
s2=re.sub(r'("dec2_revision"\s*:\s*)\d+', lambda m: m.group(1)+str(v), s)
assert s2!=s or f'"dec2_revision": {v}' in s, "pin rewrite did nothing"
open(p,'w').write(s2)
PY
}
setvec() { python3 - "$SCRATCH/.softhouse/vectors/ledger" "$1" <<'PY'
import json,sys,re,glob,os
d,v=sys.argv[1],int(sys.argv[2])
n=0
for f in sorted(glob.glob(os.path.join(d,'*.json'))):
    s=open(f).read()
    s2=re.sub(r'("dec2_revision"\s*:\s*)\d+', lambda m: m.group(1)+str(v), s)
    open(f,'w').write(s2); n+=1
assert n==6, f"expected 6 ledger vectors, rewrote {n}"
PY
}

# Count inadmissible by calling Admit through the package's own test binary is not
# directly available, so use a tiny in-tree probe placed INSIDE the scratch package.
cat > "$SCRATCH/nexus/internal/apps/ledger/conformance/t246_pinprobe_test.go" <<'EOF'
package conformance

import (
	"path/filepath"
	"testing"
)

// T246 probe: report how many committed ledger vectors Admit() rejects, and on
// what reason. Phrased POSITIVELY (P-35): it prints what it inspected.
func TestT246PinProbe(t *testing.T) {
	store := storeRoot(t)
	vs, errs, err := LoadStore(store, "")
	if err != nil {
		t.Fatalf("LoadStore: %v", err)
	}
	if len(errs) != 0 {
		t.Fatalf("load errors: %v", errs)
	}
	if len(vs) == 0 {
		t.Fatal("ZERO vectors loaded — this probe would be vacuous")
	}
	pin, err := LoadPin(filepath.Join(store, PinFileName))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	reg, err := LoadCapabilityRegistry(filepath.Join(store, CapabilityFileName))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}
	opts := Options{Pin: pin, Registry: reg, RepoRoot: repoRoot(t), StoreRoot: store}
	inadmissible := 0
	dec2reasons := 0
	for _, v := range vs {
		reasons := Admit(v, opts)
		if len(reasons) > 0 {
			inadmissible++
			for _, r := range reasons {
				t.Logf("T246PROBE reason %s :: %s", v.CaseID, r)
				if len(r) >= 13 && r[:13] == "dec2_revision" {
					dec2reasons++
				}
			}
		}
	}
	t.Logf("T246PROBE inspected=%d inadmissible=%d dec2_reasons=%d pin=%d", len(vs), inadmissible, dec2reasons, pin.DEC2Revision)
}
EOF

run() {
  local label="$1" pin="$2" vec="$3" want="$4"
  setpin "$pin"; setvec "$vec"
  local out
  out="$(cd "$SCRATCH/nexus" && go test ./internal/apps/ledger/conformance/ -run TestT246PinProbe -count=1 -v 2>&1 || true)"
  local line
  line="$(printf '%s\n' "$out" | /usr/bin/grep -o 'T246PROBE inspected=.*' | tail -1 || true)"
  printf '%-8s pin=%s vectors=%s  ->  %s\n' "$label" "$pin" "$vec" "${line:-<NO PROBE LINE — instrument failed>}"
  printf '%s\n' "$out" | /usr/bin/grep -o 'T246PROBE reason .*' | sed 's/^/            /' | head -8 || true
  if [ -z "$line" ]; then echo "            INSTRUMENT FAILURE: no probe line"; printf '%s\n' "$out" | tail -20; exit 8; fi
  local got; got="$(printf '%s' "$line" | sed -E 's/.*inadmissible=([0-9]+).*/\1/')"
  if [ "$got" != "$want" ]; then echo "            *** SCENARIO FAILED: wanted inadmissible=$want got $got ***"; exit 7; fi
  echo "            OK (wanted inadmissible=$want)"
  echo
}

echo "=== P-22 RED/GREEN matrix ==="
run GREEN  5 5 0
run RED-A  6 5 6
run RED-B  5 6 6
run GREEN2 6 6 0

echo "=== CONTROL: does ANY Go source read the ADR file? ==="
printf '  docs/adr matches under nexus/: '
{ /usr/bin/grep -rn 'docs/adr' "$SRC/nexus" || true; } | wc -l | tr -d ' '
{ /usr/bin/grep -rn 'docs/adr' "$SRC/nexus" || true; } | sed 's/^/    /'
printf '  DEC-2-gl-accounting matches under nexus/ and conformance.sh: '
{ /usr/bin/grep -rn 'DEC-2-gl-accounting' "$SRC/nexus" "$SRC/.softhouse/conformance.sh" || true; } | wc -l | tr -d ' '
echo
echo "=== ALL FOUR SCENARIOS BEHAVED AS PREDICTED ==="
rm -rf "$SCRATCH"
