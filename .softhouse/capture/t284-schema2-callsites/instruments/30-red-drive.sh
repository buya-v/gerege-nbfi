#!/usr/bin/env bash
# T284 RED DRIVE -- every repair in this task, BROKEN ON PURPOSE, then restored.
#
# WHY, IN ONE SENTENCE
#   A verify path nobody has watched FAIL is a verify path that enforces nothing.
#   This program has recorded that five times (P-45: a test-only guard is not a
#   guard -- when hardening a check, verify the path that ACTUALLY EXECUTES calls
#   it, not merely that a test does), and T284 exists because the last instance
#   was three instruments left correct, loud, and dead.
#
# WHERE THE BREAKING HAPPENS
#   In a THROWAWAY GIT REPOSITORY built from a copy of the tracked tree, never in
#   the real one.  Two reasons, both learned rather than invented:
#     * the T250 instrument this task repairs `rm -rf`s committed evidence when
#       it runs, and T283 lost an iteration to exactly that (F-T283-6);
#     * a worker whose red-drive dirties the tree it is grading is the shape this
#       program keeps re-finding.
#   Every arm therefore restores by construction: the real tree is never written.
#   The clone is `git reset --hard` + `git clean -fd` before EVERY arm, so no arm
#   can inherit another's damage -- an arm that only fails because the previous
#   one broke something is not a measurement.  Arm `Z0` re-runs the guard on the
#   REAL tree at the end and requires 0, which is the proof that nothing here
#   leaked out of the clone.
#
# ARMS.  Each states the exit status it REQUIRES and why, and a wrong status --
# in EITHER direction -- fails this instrument.  `C0` is the calibration: a guard
# that fails everything detects nothing (P-72).
#
#   REGISTRY GUARD (10-callsite-registry.py)
#     C0  untouched clone                                     -> 0  PASS
#     R1  a NEW, undeclared REQUEST_ONLY call site appears     -> 1  UNDECLARED
#     R2  a declared call site is DELETED                      -> 1  VANISHED
#     R3  a FROZEN file gains one byte                         -> 1  FROZEN MOVED
#     R4  a successor's call loses its response flags          -> 1  CLASS DRIFT
#     R5  a declared successor is deleted                      -> 1  MISSING SUCCESSOR
#     R6  a SCHEMA2-STATUS.md notice is deleted                -> 1  MISSING REQUIRED FILE
#     F1  the pin is removed                                   -> 2  REFUSED
#     F2  the calibration positive loses its call              -> 2  REFUSED
#
#   SITE 1 SUCCESSOR (20-site1-schema1-replay.sh)
#     S1  T250's committed corpus is altered                   -> 2  corpus moved
#     S2  the corpus is made SCHEMA 2 *and the digest pin is
#         re-stamped to match*, so the scope gate is reached
#         in isolation                                         -> 2  OUT OF SCOPE
#     S3  T274's live half is deleted                          -> 2  coverage gone
#
#   SITE 2 SUCCESSOR (t284-redB-attack-v2.sh)
#     S4  the FROZEN predecessor is deleted                    -> 2  no supersession
#
#   SITE 3 SUCCESSOR (t284-redC-residual-v2.sh)
#     S5  T274 instrument 20 is deleted                        -> 2  retired coverage gone
#     S6  T274 instrument 20's length list is altered          -> 2  moving target
#
# EVERY ARM IS ORACLE-FREE.  S4/S5/S6 abort before any capture is attempted, and
# S1/S2/S3 never touch the network.  So this transcript is reproducible whether
# or not the reference oracle (Fineract) is up.
#
# ENGINE (P-33/P-53): no grep, no rg, no git grep.  The clone is built from
# `git ls-files -z` over the real tree; edits are `sed`/`python3`; nothing is
# matched with a bare pattern engine.
#
# EXIT: 0 every arm behaved as required; 1 at least one did not; 2 the rig could
# not be built (no verdict).
set -euo pipefail

fail_hard() { printf 'red-drive REFUSING: %s\n' "$*" >&2; exit 2; }

REAL=$(git rev-parse --show-toplevel) || fail_hard "not inside a git repository."
[ -d "$REAL/.softhouse" ] || fail_hard "$REAL does not contain .softhouse."

REG=".softhouse/capture/t284-schema2-callsites/instruments/10-callsite-registry.py"
PIN=".softhouse/capture/t284-schema2-callsites/instruments/callsite_registry.json"
S1SH=".softhouse/capture/t284-schema2-callsites/instruments/20-site1-schema1-replay.sh"
S2SH=".softhouse/capture/t284-schema2-callsites/successors/t284-redB-attack-v2.sh"
S3SH=".softhouse/capture/t284-schema2-callsites/successors/t284-redC-residual-v2.sh"
FROZEN1=".softhouse/capture/t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh"
FROZEN2=".softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh"
MARKER1=".softhouse/capture/t250-tenant-attestation/instruments/SCHEMA2-STATUS.md"
LIVEHALF=".softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh"
WRAPOWNER=".softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh"
CORPUS=".softhouse/capture/t250-tenant-attestation/evidence/redB"

for f in "$REG" "$PIN" "$S1SH" "$S2SH" "$S3SH" "$FROZEN1" "$FROZEN2" "$MARKER1" \
         "$LIVEHALF" "$WRAPOWNER"; do
    [ -e "$REAL/$f" ] || fail_hard "the rig is incomplete: $f is missing from the real tree. No verdict."
done

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t284reddrive.XXXXXX") || fail_hard "mktemp -d failed"
TRANSCRIPT="$WORK/arms.log"

echo "T284 RED DRIVE -- every repair broken on purpose, in a throwaway clone"
echo "  real tree (never written): $REAL"
echo "  clone root               : $WORK"
echo "  registry guard sha256    : $(shasum -a 256 "$REAL/$REG" | cut -d' ' -f1)"
echo

init_clone() {           # build the clone ONCE: a git repo holding the tracked tree
    rm -rf "$C"
    mkdir -p "$C"
    ( cd "$REAL" && git ls-files -z ) > "$WORK/filelist"
    ( cd "$REAL" && LC_ALL=C tar -cf - --null -T "$WORK/filelist" ) | ( cd "$C" && tar -xf - )
    git -C "$C" init -q
    git -C "$C" add -A
    git -C "$C" -c user.email=t284@local -c user.name=t284 commit -qm clone
}

# Per-arm restoration is `reset --hard` + `clean -fd` against the clone's own
# commit, NOT a re-copy: the tracked tree is 6,694 files / 190 MB and copying it
# once per arm made this instrument take longer than the thing it grades. The
# reset is exact -- every arm starts from the identical committed state, so no
# arm can inherit another's damage.
reset_clone() {
    git -C "$C" reset -q --hard
    git -C "$C" clean -qfd
}

pass=0
bad=0
arm() {                  # arm LABEL EXPECTED_RC DESC  (command read from stdin)
    a_label=$1; a_exp=$2; a_desc=$3
    a_rc=0
    bash -c "$(cat)" > "$WORK/$a_label.out" 2>&1 || a_rc=$?
    if [ "$a_rc" -eq "$a_exp" ]; then a_v='ok'; pass=$((pass + 1));
    else a_v='*** UNEXPECTED ***'; bad=$((bad + 1)); fi
    printf '  %-4s expected rc=%s  got rc=%s  %-20s %s\n' \
        "$a_label" "$a_exp" "$a_rc" "$a_v" "$a_desc" | tee -a "$TRANSCRIPT"
    # `sed -E`, NOT plain sed. BSD sed reads `\|` in a BRE as a LITERAL, so the
    # first draft of this line matched nothing and every arm printed its status
    # with no reason beneath it -- a transcript that shows a green tick and
    # withholds the evidence for it. Caught by reading the output rather than the
    # score, which is the same defect this instrument grades in site 3.
    # Only the FINDING lines (`  * ` bullets) and REFUSING/scope lines. Matching
    # bare words like UNDECLARED also hit the guard's own descriptive census
    # above the verdict, which drowned the reason in the decision prose.
    LC_ALL=C sed -E -n '/^  \* |REFUSING|OUT OF SCOPE|SELFTEST|FAIL -- [0-9]/p' \
        "$WORK/$a_label.out" | LC_ALL=C sed -n '1,2p' | LC_ALL=C sed 's/^/         | /'
}

C="$WORK/clone"
init_clone

echo "-- REGISTRY GUARD --"

reset_clone
arm C0 0 "untouched clone must PASS (calibration)" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
mkdir -p "$C/.softhouse/capture/t284-schema2-callsites/scratch"
printf '#!/usr/bin/env bash\npython3 "\$WA" verify --sidecar a.http --headers a.reqhdr\n' \
    > "$C/.softhouse/capture/t284-schema2-callsites/scratch/rogue.sh"
git -C "$C" add -A
arm R1 1 "a NEW undeclared REQUEST_ONLY call site" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
rm -f "$C/$FROZEN2"
git -C "$C" add -A
arm R2 1 "a declared call site DELETED" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
printf '\n# one byte of drift\n' >> "$C/$FROZEN1"
arm R3 1 "a FROZEN file gains a byte" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
python3 - "$C/$S3SH" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
t = t.replace('--resp "$v_d/$v_n.json" --resphdr "$v_d/$v_n.resphdr" \\\n            --status "$v_d/$v_n.status" \\\n', '')
t = t.replace('--req "$v_d/$v_n.req" --resp "$v_d/$v_n.json" \\\n            --resphdr "$v_d/$v_n.resphdr" --status "$v_d/$v_n.status" \\\n', '')
open(p, "w").write(t)
PY
arm R4 1 "a successor's call loses its response flags" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
rm -f "$C/$LIVEHALF"
git -C "$C" add -A
arm R5 1 "a declared successor is deleted" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
rm -f "$C/$MARKER1"
git -C "$C" add -A
arm R6 1 "a SCHEMA2-STATUS.md notice is deleted" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
rm -f "$C/$PIN"
arm F1 2 "the pin is removed -> REFUSE, never 'clean'" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

reset_clone
python3 - "$C/.softhouse/capture/lib/oracle_send.sh" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
t = t.replace('--sidecar "$os_http" --headers "$os_reqhdr" --req "$os_derive_body" \\\n',
              '--headers "$os_reqhdr" --req "$os_derive_body" \\\n')
open(p, "w").write(t)
PY
arm F2 2 "the calibration positive loses its call -> REFUSE" <<EOF
python3 "$C/$REG" --root "$C" --pin "$C/$PIN"
EOF

echo
echo "-- SITE 1 SUCCESSOR (schema-1 scoped replay) --"

reset_clone
printf 'x' >> "$C/$CORPUS/arm-0/probe.http"
arm S1 2 "T250's committed corpus altered -> corpus MOVED" <<EOF
cd "$C" && bash "$C/$S1SH"
EOF

reset_clone
python3 - "$C/$CORPUS/arm-0/probe.http" <<'PY'
import sys
p = sys.argv[1]
lines = open(p).read().split("\n")
lines.insert(1, "attestation-schema: 2")
open(p, "w").write("\n".join(lines))
PY
# Re-stamp the digest pin so the corpus check PASSES and the SCOPE GATE is the
# only thing left that can refuse. Without this the digest check fires first and
# the gate is never reached -- an arm that cannot reach the thing it names is not
# a measurement of it.
NEWDIG=$( cd "$C/$CORPUS" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1 )
python3 - "$C/$S1SH" "$NEWDIG" <<'PY'
import re, sys
p, d = sys.argv[1], sys.argv[2]
t = open(p).read()
t = re.sub(r'^CORPUS_PIN="[0-9a-f]*"$', 'CORPUS_PIN="%s"' % d, t, flags=re.M)
open(p, "w").write(t)
PY
arm S2 2 "corpus made SCHEMA 2, pin re-stamped -> OUT OF SCOPE" <<EOF
cd "$C" && bash "$C/$S1SH"
EOF

reset_clone
rm -f "$C/$LIVEHALF"
arm S3 2 "T274's live half deleted -> coverage GONE, refuse" <<EOF
cd "$C" && bash "$C/$S1SH"
EOF

echo
echo "-- SITE 2 SUCCESSOR --"
reset_clone
rm -f "$C/$FROZEN2"
arm S4 2 "the FROZEN predecessor is deleted -> no supersession" <<EOF
cd "$C" && bash "$C/$S2SH"
EOF

echo
echo "-- SITE 3 SUCCESSOR --"
reset_clone
rm -f "$C/$WRAPOWNER"
arm S5 2 "T274 instrument 20 deleted -> retired coverage GONE" <<EOF
cd "$C" && bash "$C/$S3SH"
EOF

reset_clone
python3 - "$C/$WRAPOWNER" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
t = t.replace("for n in 1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000; do",
              "for n in 1 10 200 300; do")
open(p, "w").write(t)
PY
arm S6 2 "T274 instrument 20's length list altered -> moving target" <<EOF
cd "$C" && bash "$C/$S3SH"
EOF

echo
echo "-- the real tree, untouched, must still be GREEN --"
arm Z0 0 "registry guard on the REAL tree" <<EOF
python3 "$REAL/$REG"
EOF

echo
echo "SCORE: $pass as expected, $bad unexpected"
rm -rf "$WORK"
if [ "$bad" -ne 0 ]; then
    echo "T284 RED DRIVE: FAIL" >&2
    exit 1
fi
echo "T284 RED DRIVE: PASS -- every repair was driven RED through the shape it exists to catch,"
echo "and the real tree, never written, is GREEN."
