#!/usr/bin/env bash
# T284 SITE 1 SUCCESSOR -- T250's redB arms, RE-FROZEN AND EXPLICITLY SCOPED TO SCHEMA 1.
#
# THE SITE THIS SUPERSEDES
#   .softhouse/capture/t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh
#   It captures LIVE (schema 2 since T274) and then calls `verify` with
#   request-only arguments.  Measured on this branch: 2 of 8 arms as expected,
#   6 schema refusals, exit 1 -- ../evidence/RED-site1.txt.  The refusal is
#   CORRECT.  The instrument is FROZEN (T114's standing ruling: anything that
#   produced committed evidence is superseded by a scratch copy, NEVER edited in
#   place -- it wrote 127 committed files under ../evidence/, including the
#   per-arm verify.out / verify.err that ARE the output of that call).  So it is
#   not edited.  It is re-frozen: its arms are RETAINED here against the SCHEMA 1
#   corpus it committed, which is the only corpus its call shape can speak about.
#
#   DO NOT RUN THE ORIGINAL IN PLACE.  Its first act is `rm -rf` over
#   ../evidence/redB, which is committed evidence AND the input to T274's P1
#   control (T283 F-T283-6, which happened to its author).  This successor never
#   writes inside the repository; it copies to a scratch directory.
#
#   The LIVE re-capture half of T250's arms is not duplicated here.  It already
#   exists, schema-2-native, at
#   .softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh
#   That file is asserted to exist below rather than cited on trust.
#
# WHAT THIS ADDS THAT NOTHING ELSE MEASURES
#   Whether T250's COMMITTED evidence is still ADMISSIBLE under the current
#   (T274 + T283) verifier.  T283 measured the live-recapture path and found
#   2/8.  Nobody measured the committed path.  If T250's committed arms stopped
#   reproducing, 127 files of evidence would have quietly become unverifiable.
#
# THE SCOPE GATE, WHICH IS THE POINT OF THE TASK
#   A site scoped to schema 1 must REFUSE a schema 2 input LOUDLY, never skip it.
#   Before any arm runs, every input sidecar is checked for an
#   `attestation-schema:` line.  One present -> this exits 2 with the reason and
#   grades NOTHING.  A schema 2 input is not "not applicable"; it is out of
#   scope, and out of scope is a refusal.
#   That gate is DRIVEN RED ON EVERY RUN by the SELFTEST below, which plants a
#   schema line in a scratch copy and requires the gate to refuse.  A gate nobody
#   has watched fire is a gate that enforces nothing -- P-45: a test-only guard
#   is not a guard; when hardening a check, verify the path that actually
#   executes calls it, not merely that a test does.
#
# ENGINE (P-33/P-53): no grep, no rg, no git grep.  `git rev-parse` locates the
# root and its failure is fatal.  The corpus is a fixed list of eight arm
# directories; its identity is pinned by a sha256 over the sorted per-file
# digests, and drift REFUSES.  Line selection is `sed -n '/re/p'` with LC_ALL=C.
#
# CALIBRATION (P-72): arm 0 is a known POSITIVE (must verify, rc=0) and arms
# 1/2/5/6 are known NEGATIVES (must be caught, rc=1).  If the positive fails or a
# negative passes, this exits non-zero.  The corpus assertion fails loudly on an
# empty or missing corpus rather than reporting nothing to grade.
#
# EXIT: 0 replay reproduced; 1 an arm moved or the selftest failed; 2 REFUSED
# (corpus absent, corpus empty, pin drift, or an out-of-scope input).
set -euo pipefail

fail_hard() { printf 'site1-replay REFUSING: %s\n' "$*" >&2; exit 2; }

ROOT=$(git rev-parse --show-toplevel) || fail_hard "not inside a git repository; the corpus root is unknown."
[ -d "$ROOT/.softhouse" ] || fail_hard "$ROOT does not contain .softhouse; wrong repository root."

CORPUS="$ROOT/.softhouse/capture/t250-tenant-attestation/evidence/redB"
WA="$ROOT/.softhouse/capture/lib/wire_attestation.py"
LIVE_HALF="$ROOT/.softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh"
CORPUS_PIN="615416e3a70d35ca5ea391416d55620ff991f51de1e7d2c27f103def6f99c774"

[ -f "$WA" ] || fail_hard "the verifier under test does not exist: $WA"
[ -d "$CORPUS" ] || fail_hard "T250's committed redB corpus does not exist: $CORPUS -- a statement about this tree, not about the arms."
[ -f "$LIVE_HALF" ] || fail_hard "the LIVE half of T250's arms is declared to live at $LIVE_HALF and is not there. This instrument deliberately does NOT duplicate it, so its absence means the live coverage is GONE, not merely elsewhere."

ARMS="0 1 2 3 4 5 6 7"

# ---------------------------------------------------------------- corpus identity
corpus_digest() {
    ( cd "$CORPUS" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256 ) | cut -d' ' -f1
}

nfiles=$(find "$CORPUS" -type f | wc -l | tr -d ' ')
if [ "$nfiles" -eq 0 ]; then
    fail_hard "the corpus at $CORPUS holds ZERO files. An empty corpus grades nothing, and reporting a clean replay over it would be the exact fail-open this task exists to remove."
fi
digest=$(corpus_digest)

echo "T284 SITE 1 REPLAY -- T250's committed schema 1 redB arms, under today's verifier"
echo "  verifier : $(shasum -a 256 "$WA" | cut -d' ' -f1)"
echo "  corpus   : .softhouse/capture/t250-tenant-attestation/evidence/redB"
echo "  files    : $nfiles"
echo "  digest   : $digest"
if [ "$digest" != "$CORPUS_PIN" ]; then
    fail_hard "the committed corpus MOVED.
    pinned   $CORPUS_PIN
    measured $digest
  T250's evidence is frozen (T114). If it changed, either it was retro-edited --
  which T274 deliberately refused to do and which this instrument partly exists to
  detect -- or somebody ran the frozen original in place and it rewrote its own
  evidence with a fresh schema 2 capture. Either way no replay verdict is available."
fi
echo "  digest matches the pin."
echo

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t284site1.XXXXXX") || fail_hard "mktemp -d failed"
SELF=$(mktemp -d "${TMPDIR:-/tmp}/t284site1self.XXXXXX") || fail_hard "mktemp -d failed"
trap 'rm -rf "$SCRATCH" "$SELF"' EXIT
cp -R "$CORPUS/." "$SCRATCH/"

# ------------------------------------------------------------------- scope gate
# A schema 1 scoped site REFUSES a schema 2 input. It does not skip it.
scope_gate() {          # scope_gate DIR  -> 0 in scope, 1 out of scope (reasons printed)
    sg_dir=$1
    sg_bad=0
    for sg_a in $ARMS; do
        sg_side="$sg_dir/arm-$sg_a/probe.http"
        if [ ! -f "$sg_side" ]; then
            printf '  arm-%s  sidecar MISSING: %s\n' "$sg_a" "$sg_side"
            sg_bad=1
            continue
        fi
        sg_line=$(LC_ALL=C sed -n '/^attestation-schema:/p' "$sg_side" | LC_ALL=C sed -n '1p')
        if [ -n "$sg_line" ]; then
            printf '  arm-%s  OUT OF SCOPE -- sidecar declares `%s`\n' "$sg_a" "$sg_line"
            sg_bad=1
        fi
    done
    return "$sg_bad"
}

echo "-- scope gate: every input sidecar must be SCHEMA 1 (no attestation-schema line) --"
gate_rc=0
scope_gate "$SCRATCH" || gate_rc=$?
if [ "$gate_rc" -ne 0 ]; then
    fail_hard "at least one input sidecar is NOT schema 1 (listed above). This
  instrument's call shape presents no response artefact, so it can issue no
  verdict about a sidecar that attests one. REFUSED, and NOTHING was graded.
  A schema 2 capture belongs to $LIVE_HALF, not here."
fi
echo "  all 8 arms are schema 1 -- in scope."
echo

# ------------------------------------------------------------------------ arms
pass=0
fail=0
run_arm() {             # run_arm N EXPECTED DESC
    ra_n=$1; ra_exp=$2; ra_desc=$3
    ra_dir="$SCRATCH/arm-$ra_n"
    ra_rc=0
    python3 "$WA" verify --sidecar "$ra_dir/probe.http" --headers "$ra_dir/probe.reqhdr" \
        --req "$ra_dir/probe.req" > "$ra_dir/t284.out" 2> "$ra_dir/t284.err" || ra_rc=$?
    if [ "$ra_rc" -eq "$ra_exp" ]; then ra_ok='ok'; pass=$((pass + 1));
    else ra_ok='*** MOVED ***'; fail=$((fail + 1)); fi
    printf '  ARM %s  T250 expected rc=%s  got rc=%s  %-14s %s\n' \
        "$ra_n" "$ra_exp" "$ra_rc" "$ra_ok" "$ra_desc"
    LC_ALL=C sed -n '1,2p' "$ra_dir/t284.err" | LC_ALL=C sed 's/^/        /'
}

echo "-- T250's eight arms, with T250's ORIGINAL expected exit statuses --"
run_arm 0 0 "POSITIVE CONTROL: nothing touched"
run_arm 1 1 "sidecar claims a tenant that was not sent"
run_arm 2 1 "header record edited, sidecar untouched"
run_arm 3 2 "header record DELETED -- must refuse"
run_arm 4 2 "legacy literal sidecar, no derivation provenance"
run_arm 5 1 "body artefact swapped under a sidecar that hashed the original"
run_arm 6 1 "Content-Length sent != committed body byte count"
run_arm 7 0 "HONEST NEGATIVE: whole set forged consistently -- NOT caught here"
echo
echo "  arms as expected: $pass    arms MOVED: $fail"
echo

# --------------------------------------------------------------------- selftest
# The scope gate, DRIVEN RED, every run.
echo "-- SELFTEST: the scope gate must REFUSE a schema 2 input, not skip it --"
cp -R "$CORPUS/." "$SELF/"
python3 - "$SELF/arm-0/probe.http" <<'PY'
import sys
p = sys.argv[1]
with open(p, "r") as fh:
    lines = fh.read().split("\n")
lines.insert(1, "attestation-schema: 2")
with open(p, "w") as fh:
    fh.write("\n".join(lines))
PY
self_rc=0
scope_gate "$SELF" > "$SELF/gate.out" 2>&1 || self_rc=$?
LC_ALL=C sed 's/^/  /' "$SELF/gate.out"
if [ "$self_rc" -eq 0 ]; then
    echo "  SELFTEST FAILED: the scope gate ACCEPTED a schema 2 sidecar." >&2
    echo "  A schema-1-scoped site that lets a schema 2 input through is a fail-open," >&2
    echo "  and every arm result above is therefore untrustworthy." >&2
    exit 1
fi
echo "  SELFTEST ok: the planted schema 2 sidecar was REFUSED (gate returned $self_rc)."
echo

if [ "$fail" -ne 0 ]; then
    echo "SITE 1 REPLAY: FAIL -- $fail arm(s) moved against T250's committed evidence." >&2
    exit 1
fi
cat <<EOF
SITE 1 REPLAY: PASS
  All 8 of T250's redB arms reproduce their ORIGINAL expected exit statuses
  against T250's COMMITTED schema 1 corpus under the current verifier. T250's
  127 committed evidence files remain ADMISSIBLE; T274 changed what is CHECKED
  on a fresh capture, not what T250's frozen evidence says.
  SCOPE, stated so it cannot be over-read: this says NOTHING about a schema 2
  capture. That is 30-t250-arms-still-hold.sh, asserted present above.
EOF
