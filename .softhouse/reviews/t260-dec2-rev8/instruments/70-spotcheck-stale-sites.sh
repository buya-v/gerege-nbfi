#!/usr/bin/env bash
# T260 — spot-check the four "live stale sites neither review enumerated", and every ANCHOR in
# revision 8, using the DOCUMENTED reader recipe `git grep -n -F` with P-80 status classification.
#
# P-80 is the point of this script: `git grep` exits 1 on NO MATCH and >1 on ERROR. A negative is
# only a measured negative if the status was 1. A status >1 must ABORT, never be printed as an
# absence. Every probe below classifies.
# P-75: no bare `grep`, no `rg`. `git grep -F` only.
set -euo pipefail

SH=.softhouse/conformance.sh

probe () {  # $1 = needle, $2 = expectation note
  local needle="$1" note="${2:-}"
  local out rc
  set +e
  out="$(git grep -c -F -- "$needle" -- "$SH" 2>/tmp/t260/gg.err)"
  rc=$?
  set -e
  if [ "$rc" -gt 1 ]; then
    echo "ABORT (P-80): git grep exited $rc — an ERROR, not an absence. stderr:"
    cat /tmp/t260/gg.err
    exit 2
  fi
  if [ "$rc" -eq 1 ]; then
    echo "  0 matches, exit 1  -> A REAL MEASURED NEGATIVE.  $note"
    echo "      needle: $needle"
  else
    local n="${out##*:}"
    echo "  $n matching line(s), exit 0.  $note"
    echo "      needle: $needle"
    git grep -n -F -- "$needle" -- "$SH" | sed 's/^/        /' | cut -c1-160
  fi
}

echo "conformance.sh blob under test: $(git hash-object "$SH")"
echo "expected (a71c140 / main / T255): 029439ba6124ed10394554cf5ac9128cf3c42100"
echo

echo "=== CALIBRATION (P-35/P-66): a needle that MUST be absent, and one that MUST be present ==="
probe "ZZQQ-T260-THIS-MUST-NOT-MATCH" "negative control — must report 0/exit 1"
probe "run_guards" "positive control — must report >0"
echo

echo "=== SPOT-CHECK 1: FU-A2-25-2's harness comment, which T255 records as GONE ==="
probe "records as not existing" "T255 claims 0 matches / exit 1 / FU-A2-25-2 CLOSED"
probe "the I-3/I-4 SOURCE GUARD that DEC-2" "the wider phrase, in case only the tail was reworded"
echo

echo "=== SPOT-CHECK 2: the \`go test\` count — DEC-2 rev8 says FOUR occurrences, all comments ==="
set +e
git grep -n -F -- "go test" -- "$SH" > /tmp/t260/gotest.txt 2>/tmp/t260/gg.err
rc=$?
set -e
if [ "$rc" -gt 1 ]; then echo "ABORT (P-80): git grep exited $rc"; cat /tmp/t260/gg.err; exit 2; fi
echo "  occurrences of the string \`go test\`: $(wc -l < /tmp/t260/gotest.txt)"
sed 's/^/    /' /tmp/t260/gotest.txt | cut -c1-170
echo "  of those, how many are on a COMMENT line (first non-space char is '#'):"
python3 - <<'PY'
import re
n_comment = 0
n_total = 0
for line in open("/tmp/t260/gotest.txt", encoding="utf-8"):
    body = line.split(":", 2)[2] if line.count(":") >= 2 else ""
    n_total += 1
    if body.lstrip().startswith("#"):
        n_comment += 1
print("    total %d, comment-lines %d, non-comment %d" % (n_total, n_comment, n_total - n_comment))
PY
probe "so a Go-test-only guard is not a" "the ANCHOR revision 8 uses in place of :718/:721"
echo

echo "=== SPOT-CHECK 3: the :401 / :411 pair, which rev8 says were TRUE and converted anyway ==="
probe 'NEXUS_DIR="$REPO_ROOT/nexus"' "anchor replacing :401"
probe 'CMD_PKG="./internal/apps/loanschedule/conformance/cmd/conformance"' "anchor replacing :411"
echo

echo "=== SPOT-CHECK 4: the -context pass-through, replacing :1254 ==="
probe '[ -n "$context" ] && args+=("-context=$context")' "anchor replacing :1254"
echo

echo "=== SPOT-CHECK 5: what :718 / :721 / :1254 / :401 / :411 ACTUALLY point at now ==="
python3 - <<'PY'
lines = open(".softhouse/conformance.sh", encoding="utf-8").read().split("\n")
for n in (401, 411, 718, 721, 1254, 1115, 1116):
    txt = lines[n - 1] if n <= len(lines) else "<past EOF>"
    print("    :%-5d %s" % (n, txt.strip()[:130]))
PY
echo
echo "=== EVERY ANCHOR in revision 8, resolved by the DOCUMENTED recipe, status classified ==="
python3 - <<'PY' > /tmp/t260/anchors.tsv
import re
t = open("/tmp/t260/rev8.md", encoding="utf-8").read()
for p, s in re.findall(r"\[ANCHOR\s+(\S+?)\s+::\s+`([^`]+)`\]", t):
    print("%s\t%s" % (p, s))
PY
n_ok=0; n_rot=0; n_amb=0; n_err=0
while IFS=$'\t' read -r path needle; do
  set +e
  out="$(git grep -c -F -- "$needle" -- "$path" 2>/tmp/t260/gg.err)"
  rc=$?
  set -e
  if [ "$rc" -gt 1 ]; then
    echo "  ERROR   exit $rc on $path :: ${needle:0:70}"; n_err=$((n_err+1)); continue
  fi
  if [ "$rc" -eq 1 ]; then
    echo "  ROT     0 matches, exit 1 — $path :: ${needle:0:70}"; n_rot=$((n_rot+1)); continue
  fi
  c="${out##*:}"
  if [ "$c" -eq 1 ]; then
    echo "  ok      1 match  — $path :: ${needle:0:70}"; n_ok=$((n_ok+1))
  else
    echo "  AMBIG   $c matches, exit 0 (git grep SUCCEEDS) — $path :: ${needle:0:70}"; n_amb=$((n_amb+1))
  fi
done < /tmp/t260/anchors.tsv
echo "  --- ok $n_ok / ROT $n_rot / AMBIG $n_amb / ERROR $n_err  (P-67: all four terms) ---"
