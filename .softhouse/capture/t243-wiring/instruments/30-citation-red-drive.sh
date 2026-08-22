#!/bin/bash
# T243 RED DRIVE 3 — THE F-3 DECISION, DRIVEN RED THROUGH
# `bash .softhouse/conformance.sh`.
#
# A2-34's F-3: part two of T233's three-part capture citation resolves BY FILE
# NAME on LDG-01/02/03's response artefacts, so it "passes without demonstrating
# anything". The decision recorded in ledger/conformance/admit.go is to KEEP part
# two and PIN its weakest branch by identity, rather than retire it. Three claims
# carry that decision and each one is driven red here:
#
#   RED A — INFLATION. A FOURTH file-name-only citation, not on the pin, is
#           INADMISSIBLE. So the branch A2-34 called tautological can now fail.
#   RED B — THE ARGUMENT ITSELF. A citation pointed at a DIFFERENT artefact,
#           carrying that artefact's CORRECT sha256, is caught by part two and
#           by NOTHING ELSE. This is the whole reason part two was not retired:
#           the digest answers "are these the bytes I transcribed", never "is
#           this the capture case I name". If this arm ever goes green, the
#           decision in admit.go is wrong and should be reversed to a retirement.
#   RED C — DEFLATION. A pin row that no longer describes the corpus is a FATAL,
#           so the pin cannot outlive the weakness it excuses.
#
# THE VECTOR STORE IS PERTURBED IN PLACE AND RESTORED UNDER A TRAP (P-54), and
# the store digest is printed before and after. `git rev-parse HEAD:.softhouse/
# vectors` is the canonical digest (P-61); it must be identical at both ends.
#
# ENGINE AND FLAGS (P-33 / P-53 / P-75): `/usr/bin/grep` by absolute path, BSD
# grep 2.6.0-FreeBSD, LC_ALL=C -a throughout. No bare `grep`, no `rg`. Root from
# `git rev-parse --show-toplevel`.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"

LOG="$R/.softhouse/capture/t243-wiring/evidence"
mkdir -p "$LOG"
V=.softhouse/vectors/ledger
ADMIT=nexus/internal/apps/ledger/conformance/admit.go
PASS=0; FAIL=0
RC=0

# RESTORE FROM A BYTE COPY, NOT FROM `git checkout --`. Measured the hard way in
# this task's own first run: `git checkout -- admit.go` restored it to HEAD and
# deleted the uncommitted change under test, after which every later arm ran
# against a tree that did not compile and "failed" for a reason that had nothing
# to do with what it was testing. A restore whose behaviour depends on what has
# been committed is not a restore.
BACKUP="$(mktemp -d -t t243-rd3)"
cp -R "$V" "$BACKUP/ledger"
cp "$ADMIT" "$BACKUP/admit.go"
restore() {
  rm -rf "$V"
  cp -R "$BACKUP/ledger" "$V"
  cp "$BACKUP/admit.go" "$ADMIT"
}
trap 'restore; rm -rf "$BACKUP"' EXIT

ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  $*"; FAIL=$((FAIL+1)); }

run() {
  local tag="$1"
  set +e
  bash .softhouse/conformance.sh > "$LOG/$tag.txt" 2>&1
  RC=$?
  set -e
}

want_line() {
  local tag="$1" label="$2" needle="$3" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -gt 0 ]; then ok "[$label] found ($n): $needle"
  else bad "[$label] NOT FOUND: $needle"; fi
}

want_absent() {
  local tag="$1" label="$2" needle="$3" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -eq 0 ]; then ok "[$label] absent as required: $needle"
  else bad "[$label] PRESENT but must be absent ($n): $needle"; fi
}

proven_applied() {
  local f="$1" s="$2" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$s" "$f" || true)
  if [ "${n:-0}" -gt 0 ]; then echo "  perturbation PROVEN APPLIED in $f"
  else bad "PERTURBATION DID NOT APPLY to $f — the case below would prove nothing"; fi
}

D0="$(git rev-parse HEAD:.softhouse/vectors)"
echo "T243 RED DRIVE 3 — part two of the capture citation, through conformance.sh"
echo "commit        : $(git rev-parse HEAD)"
echo "vector digest : $D0   (must be identical at the end)"
echo

echo "=================================================================="
echo "MEASUREMENT — where part two ACTUALLY resolves, all twelve"
echo "citations, re-derived independently of the Go code."
echo "=================================================================="
python3 "$R/.softhouse/capture/t243-wiring/instruments/31-citation-census.py"
echo

echo "=================================================================="
echo "CONTROL 0 — pristine tree. The census is printed by the harness on"
echo "every run, and the population equals the pin."
echo "=================================================================="
run control0
echo "  exit=$RC"
want_line control0 control0 "ledger citations        12 PART-TWO resolutions over the loaded corpus: 1 ARTEFACT-BYTES,"
want_line control0 control0 "8 HTTP-SIDECAR, 3 FILE-NAME-ONLY (pinned 3), 0 UNRESOLVED."
want_line control0 control0 "FILE-NAME-ONLY: LDG-01-manual-je-3leg-minor-units provenance.capture_ref"
want_line control0 control0 "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 0 ]; then ok "[control0] exit 0"; else bad "[control0] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "RED A — INFLATION. Repoint LDG-REFUSE-01's capture_ref at a readback"
echo "        artefact whose sidecar does NOT carry the id, with the id and"
echo "        the CORRECT sha256 moved with it. Every other check passes:"
echo "        the artefact exists, is non-empty, and digests exactly. Only"
echo "        part two's WEAKEST branch would admit it, and it is not pinned."
echo "=================================================================="
python3 - "$V/LDG-REFUSE-01-unbalanced-by-one-minor-unit.json" <<'PY'
import hashlib, json, sys
p = sys.argv[1]
art = ".softhouse/capture/tierA-a2/out/A2-347-je-manual-readback.json"
raw = open(art, 'rb').read()
s = open(p, encoding='utf-8').read()
s = s.replace('".softhouse/capture/tierA-a2/out/A2-344-manual-je-unbalanced.json"', '"%s"' % art, 1)
s = s.replace('"a2162fcf5ff5c4e82e05cc91595fdd70e199755d33898e9896ab2abb128082bb"',
              '"%s"' % hashlib.sha256(raw).hexdigest(), 1)
s = s.replace('"capture_case_id": "A2-344-manual-je-unbalanced"',
              '"capture_case_id": "A2-347-je-manual-readback"', 1)
open(p, 'w', encoding='utf-8').write(s)
PY
proven_applied "$V/LDG-REFUSE-01-unbalanced-by-one-minor-unit.json" '"capture_case_id": "A2-347-je-manual-readback"'
run redA
echo "  exit=$RC"
want_line redA RED-A "resolves PART TWO of its citation BY FILE NAME ONLY"
want_line redA RED-A "reads ZERO bytes of the"
want_line redA RED-A "LDG-REFUSE-01-unbalanced-by-one-minor-unit"
want_absent redA RED-A "has changed since the vector"
if [ "$RC" -ne 0 ]; then ok "[RED-A] exit $RC (non-zero)"; else bad "[RED-A] exit 0 — a fourth unpinned file-name-only citation was ADMITTED"; fi
restore
echo

echo "=================================================================="
echo "RED B — THE ARGUMENT. LDG-REFUSE-02's capture_ref is pointed at a"
echo "        DIFFERENT capture's artefact, and given THAT artefact's"
echo "        CORRECT sha256. The digest check is fully satisfied and stays"
echo "        silent. If part two were retired as 'redundant given the"
echo "        sha256', this run would be GREEN over a vector citing the"
echo "        wrong capture case."
echo "=================================================================="
python3 - "$V/LDG-REFUSE-02-manual-adjustments-not-permitted.json" <<'PY'
import hashlib, json, re, sys
p = sys.argv[1]
art = ".softhouse/capture/tierA-a2/out/A2-344-manual-je-unbalanced.json"
raw = open(art, 'rb').read()
v = json.load(open(p, encoding='utf-8'))
assert v["provenance"]["capture_case_id"] == "A2-346-manual-je-nomanual"
s = open(p, encoding='utf-8').read()
s = s.replace('"capture_ref": ".softhouse/capture/tierA-a2/out/A2-346-manual-je-nomanual.json"',
              '"capture_ref": "%s"' % art, 1)
s = s.replace('"capture_sha256": "%s"' % v["provenance"]["capture_sha256"],
              '"capture_sha256": "%s"' % hashlib.sha256(raw).hexdigest(), 1)
open(p, 'w', encoding='utf-8').write(s)
PY
proven_applied "$V/LDG-REFUSE-02-manual-adjustments-not-permitted.json" '"capture_ref": ".softhouse/capture/tierA-a2/out/A2-344-manual-je-unbalanced.json"'
run redB
echo "  exit=$RC"
want_line redB RED-B "occurs neither in the bytes of"
want_line redB RED-B "does not answer to the"
want_line redB RED-B "LDG-REFUSE-02-manual-adjustments-not-permitted"
want_absent redB RED-B "has changed since the vector"
if [ "$RC" -ne 0 ]; then ok "[RED-B] exit $RC (non-zero) — part two caught a mis-citation the sha256 could not"; else bad "[RED-B] exit 0 — the sha256 DOES subsume part two and the decision in admit.go is wrong"; fi
restore
echo

echo "=================================================================="
echo "RED C — DEFLATION. Add a FOURTH pin row for a citation that resolves"
echo "        the STRONGEST way (LDG-04's response carries the id in its own"
echo "        bytes). The pin now excuses a weakness that is not there, and"
echo "        the harness must say so instead of agreeing with itself."
echo "=================================================================="
python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
anchor = 'var citationNameOnlyPin = map[string]string{\n'
add = ('\tcitationPinKey("LDG-04-header-account-accepted", "provenance.capture_ref"): "" +\n'
       '\t\t"T243 RED DRIVE - a pin row that describes nothing",\n')
assert s.count(anchor) == 1
open(p, 'w', encoding='utf-8').write(s.replace(anchor, anchor + add))
PY
proven_applied "$ADMIT" "T243 RED DRIVE - a pin row that describes nothing"
run redC
echo "  exit=$RC"
want_line redC RED-C "citationNameOnlyPin carries"
want_line redC RED-C "resolved ARTEFACT-BYTES on this"
want_line redC RED-C "A pin nothing needs is a sentence nothing checks"
if [ "$RC" -ne 0 ]; then ok "[RED-C] exit $RC (non-zero)"; else bad "[RED-C] exit 0 — a stale pin survived"; fi
restore
echo

echo "=================================================================="
echo "GREEN AGAIN — anti-no-op close."
echo "=================================================================="
run green1
echo "  exit=$RC"
want_line green1 GREEN "8 HTTP-SIDECAR, 3 FILE-NAME-ONLY (pinned 3), 0 UNRESOLVED."
want_line green1 GREEN "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 0 ]; then ok "[GREEN] exit 0"; else bad "[GREEN] exit $RC, wanted 0"; fi
echo

D1="$(git rev-parse HEAD:.softhouse/vectors)"
echo "  vector digest at start : $D0"
echo "  vector digest at end   : $D1"
if [ "$D0" = "$D1" ]; then ok "[digest] the vector store is byte-identical to where it started"
else bad "[digest] THE VECTOR STORE MOVED"; fi
echo -n "  vectors + admit.go differ from their pre-mutation copies (0 = clean): "
if diff -r -q "$BACKUP/ledger" "$V" >/dev/null 2>&1 && cmp -s "$BACKUP/admit.go" "$ADMIT"; then
  echo 0
else
  echo 1
fi
echo

echo "=================================================================="
echo "RED DRIVE 3: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
