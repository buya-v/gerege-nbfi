#!/bin/bash
# T109 — DRIVE THE NEW BASELINE-DIGEST COMPARISON RED.
#
# Each case swaps FORK-POINT-SHA for a crafted pin, runs the rig, and records:
#   exit code, stdout byte count (0 == not even the header printed == no proof row ran),
#   and whether ANY proof-row artefact was written to scratch/.
# The committed FORK-POINT-SHA is restored from git after every case and verified clean at the end.
set -u
ROOT="${1:?repo root}"
RIG="$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs"
PIN="$RIG/FORK-POINT-SHA"
S="$RIG/scratch"
BAK="/tmp/t109-pin-backup"

cp "$PIN" "$BAK"

restore() { cp "$BAK" "$PIN"; }

run_case() {
  label="$1"
  echo
  echo "=============================================================================="
  echo "CASE: $label"
  echo "--- FORK-POINT-SHA directives fed to the rig -----------------------------------"
  grep -vE '^[[:space:]]*(#|$)' "$PIN" | sed -e 's/^/  | /'
  echo "--- rig stdout -----------------------------------------------------------------"
  bash "$RIG/prove-guards-go-red.sh" > /tmp/t109-case.out 2> /tmp/t109-case.err
  got=$?
  sed -e 's/^/  1| /' /tmp/t109-case.out
  echo "--- rig stderr -----------------------------------------------------------------"
  sed -e 's/^/  2| /' /tmp/t109-case.err
  echo "--------------------------------------------------------------------------------"
  echo "  exit                 : $got"
  echo "  stdout bytes         : $(wc -c < /tmp/t109-case.out | tr -d ' ')"
  echo "  proof-row artefacts  : $(ls "$S" 2>/dev/null | grep -c '^att-\|^cf-') (att-*/cf-* written by an expect row)"
  echo "  scratch entries      : $(ls "$S" 2>/dev/null | wc -l | tr -d ' ')"
}

MAINTIP="$(git -C "$ROOT" rev-parse main)"
ROOTCOMMIT="$(git -C "$ROOT" rev-list --max-parents=0 main | tail -n 1)"
echo "main tip     : $MAINTIP"
echo "root commit  : $ROOTCOMMIT"

# ---------------------------------------------------------------------------------------------
# R1 — THE HEADLINE. T103's case 5i: pin main's own tip. Valid, reachable, 40 hex. Scored a GREEN
#      25/25 before this check existed.
# ---------------------------------------------------------------------------------------------
{
  echo "# R1: main's tip, with the REAL fork-point digests still pinned."
  echo "commit $MAINTIP"
  grep '^sha256 ' "$BAK"
} > "$PIN"
run_case "R1 — pin main's tip, correct digests (T103 case 5i: was a green 25/25)"
restore

# ---------------------------------------------------------------------------------------------
# R1b — the same wrong pin WITH digests recomputed from it, i.e. an operator who "fixed" the
#       mismatch by adjusting the digests instead of the pin. Documents the residual hole.
# ---------------------------------------------------------------------------------------------
{
  echo "commit $MAINTIP"
  for p in .softhouse/capture/src/run-pass3i.sh .softhouse/handoff/T74-promote-vectors.py .softhouse/capture/t74-multiplesof/build-counterfactuals.py; do
    d="$(git -C "$ROOT" show "$MAINTIP:$p" | shasum -a 256 | cut -d' ' -f1)"
    echo "sha256 $d  $p"
  done
} > "$PIN"
run_case "R1b — main's tip WITH digests recomputed from it (the residual hole, stated not hidden)"
restore

# ---------------------------------------------------------------------------------------------
# R2 — the T102-era bare-sha file: the CORRECT sha, no digest pins at all.
# ---------------------------------------------------------------------------------------------
{
  echo "# R2: T102-era format — bare sha, no digest pins."
  echo "8da4b831b96a146c2b46ad34d85ed098395de160"
} > "$PIN"
run_case "R2 — T102-era bare sha (correct commit, NO digest pins) must be refused"
restore

# ---------------------------------------------------------------------------------------------
# R3 — correct commit, ONE digest altered. Proves each comparison executes individually.
# ---------------------------------------------------------------------------------------------
sed -e 's/^sha256 27bb20b4/sha256 00bb20b4/' "$BAK" > "$PIN"
run_case "R3 — correct commit, promote-vectors digest altered by ONE nibble"
restore

sed -e 's/^sha256 e7aee917/sha256 f7aee917/' "$BAK" > "$PIN"
run_case "R3b — correct commit, build-counterfactuals digest altered (the third file, never printed before T109)"
restore

# ---------------------------------------------------------------------------------------------
# R4 — a `commit` line missing entirely.
# ---------------------------------------------------------------------------------------------
grep '^sha256 ' "$BAK" > "$PIN"
run_case "R4 — no \`commit\` directive"
restore

# ---------------------------------------------------------------------------------------------
# R5 — two `commit` lines (T103's F-6, previously "last one silently wins").
# ---------------------------------------------------------------------------------------------
{
  echo "commit 8da4b831b96a146c2b46ad34d85ed098395de160"
  echo "commit $MAINTIP"
  grep '^sha256 ' "$BAK"
} > "$PIN"
run_case "R5 — two \`commit\` directives (F-6: a prepend/append must not silently re-baseline)"
restore

# ---------------------------------------------------------------------------------------------
# R6 — a valid commit that does NOT contain the baseline paths (T103's F-4: was 18/7).
# ---------------------------------------------------------------------------------------------
{
  echo "commit $ROOTCOMMIT"
  grep '^sha256 ' "$BAK"
} > "$PIN"
run_case "R6 — repo ROOT commit: valid, but lacks the baseline paths (F-4: was a misdiagnosable 18/7)"
restore

# ---------------------------------------------------------------------------------------------
# T102's original four refusals must still hold under the new parser.
# ---------------------------------------------------------------------------------------------
mv "$PIN" /tmp/t109-pin-hidden
run_case "T102-1 — FORK-POINT-SHA missing"
mv /tmp/t109-pin-hidden "$PIN"

echo "commit not-a-sha" > "$PIN"
run_case "T102-2 — non-hex commit value"
restore

{ echo "commit 8da4b83"; grep '^sha256 ' "$BAK"; } > "$PIN"
run_case "T102-3 — abbreviated commit sha"
restore

{ echo "commit deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"; grep '^sha256 ' "$BAK"; } > "$PIN"
run_case "T102-4 — 40 hex, not a commit in this repository"
restore

# ---------------------------------------------------------------------------------------------
echo
echo "=============================================================================="
echo "FORK-POINT-SHA restored?  git diff --stat on the pin:"
git -C "$ROOT" diff --stat -- .softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA
echo "  (empty above == restored to the committed/working bytes)"
diff "$BAK" "$PIN" && echo "  byte-identical to the backup taken before this run"
