#!/usr/bin/env bash
# T304 -- drive the evidence-destruction guard RED.
#
# P-22 (patterns.md): "Ship no guard you have not personally driven RED. State the input
# that makes it fail, and commit the transcript. ... And a guard that inspects zero files
# must be an error, not a pass."
#
# Every arm runs in a THROWAWAY LOCAL CLONE. The real checkout is never written -- arm Z0
# re-runs the guard on the real tree at the end and requires 0, which is the proof that
# nothing leaked. Every arm is oracle-free.
#
# The arms are chosen to separate the guard's two legs from each other. R4 in particular
# COMMITS the destruction, which silences LEG 1 entirely; if LEG 2 did no independent
# work, R4 would go green and the ratchet would be decoration.

set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
GUARD="$HERE/30-evidence-guard.sh"
PIN="$HERE/evidence_roots.json"

[ -f "$GUARD" ] || { echo "no guard at $GUARD"; exit 2; }
[ -f "$PIN" ]   || { echo "no pin at $PIN"; exit 2; }

SB=$(mktemp -d "${TMPDIR:-/tmp}/t304rd.XXXXXX") || exit 2
cleanup() { rm -rf "$SB"; }
trap cleanup EXIT

pass=0; unexpected=0

echo "T304 RED DRIVE -- the evidence-destruction guard"
echo "  guard   : ${GUARD#"$ROOT/"}"
echo "  sandbox : $SB"
echo

echo "building the throwaway clone (local, hardlinked -- the real tree is never written)"
git clone --local --quiet "$ROOT" "$SB/clone" 2>/dev/null || { echo "clone failed"; exit 2; }
git -C "$SB/clone" config user.email t304@local
git -C "$SB/clone" config user.name  t304
echo "  clone at $SB/clone"

# The clone carries HEAD, not the working tree. On the first run of this drive the pin
# under test was still the PREVIOUS, uncommitted-over version -- a single root
# `.softhouse` with a floor of 6777 -- and every negative control went red for a reason
# that had nothing to do with the arm. A drive that silently grades a stale artefact is
# measuring the wrong thing, so refuse instead.
clone_pin="$SB/clone/.softhouse/capture/t304-evidence-destruction/evidence_roots.json"
if [ ! -f "$clone_pin" ]; then
    echo "REFUSING: the clone carries no pin -- commit evidence_roots.json before driving." >&2
    exit 2
fi
if ! cmp -s "$clone_pin" "$PIN"; then
    echo "REFUSING: the pin in the clone (HEAD) differs from the pin in the working tree." >&2
    echo "  Commit .../evidence_roots.json first; otherwise this drive grades a stale pin." >&2
    diff "$clone_pin" "$PIN" | head -20 >&2
    exit 2
fi
clone_guard="$SB/clone/.softhouse/capture/t304-evidence-destruction/30-evidence-guard.sh"
if [ -f "$clone_guard" ] && ! cmp -s "$clone_guard" "$GUARD"; then
    echo "REFUSING: the guard in the clone (HEAD) differs from the one in the working tree." >&2
    exit 2
fi
echo "  pin and guard in the clone are byte-identical to the working tree (checked, not assumed)"
echo

# arm NAME EXPECTED_RC DESCRIPTION -- body reads from stdin, runs inside the clone
arm() {
    local name="$1" want="$2" desc="$3"
    git -C "$SB/clone" reset --hard --quiet HEAD
    git -C "$SB/clone" clean -qfd
    local body; body=$(cat)
    ( cd "$SB/clone" && eval "$body" ) >"$SB/$name.setup" 2>&1
    local got out
    out=$( cd "$SB/clone" && bash "$GUARD" 2>&1 ); got=$?
    printf '%s\n' "$out" > "$SB/$name.out"
    if [ "$got" -eq "$want" ]; then
        printf '  %-4s expected rc=%s  got rc=%s  ok   %s\n' "$name" "$want" "$got" "$desc"
        pass=$((pass + 1))
    else
        printf '  %-4s expected rc=%s  got rc=%s  ***  %s\n' "$name" "$want" "$got" "$desc"
        sed 's/^/         | /' "$SB/$name.out" | head -20
        unexpected=$((unexpected + 1))
    fi
    # the reason under the status, so a status can be checked against a reason
    grep -aE 'DESTROYED|RATCHET|ROOT GONE|REFUSED|PASS --' "$SB/$name.out" | head -3 \
        | sed 's/^/         > /'
}

T250B=".softhouse/capture/t250-tenant-attestation/evidence/redB"
T274W=".softhouse/capture/t274-attestation-failopen/evidence/wrap"
VEC=".softhouse/vectors"

echo "-- CALIBRATION --"
arm C0 0 "an untouched clone must PASS" <<'EOF'
true
EOF

echo
echo "-- LEG 1: the destruction is in the WORKTREE, not yet committed --"

arm R1 1 "ONE tracked evidence file deleted" <<EOF
rm -f "\$(git ls-files -- $T250B | head -1)"
EOF

arm R2 1 "ONE tracked evidence file REWRITTEN IN PLACE (T114's exact prohibition)" <<EOF
f=\$(git ls-files -- $T250B | head -1); printf 'tampered\n' >> "\$f"
EOF

arm R3 1 "the real family-A statement: \`rm -rf \$EV\` over T250's committed redB (70 files)" <<EOF
rm -rf $T250B
EOF

arm R4 1 "T274's wrap evidence (145 files) destroyed -- the root T284's site 3 leans on" <<EOF
rm -rf $T274W
EOF

arm R5 1 "a tracked evidence file RENAMED (a move is a destruction of the old path)" <<EOF
f=\$(git ls-files -- $T250B | head -1); git mv "\$f" "\$f.renamed"
EOF

arm R6 1 "a PARITY VECTOR mutated in place -- the B3/B4 kill window on .softhouse/vectors" <<EOF
f=\$(git ls-files -- $VEC/ledger | head -1); printf '\n' >> "\$f"
EOF

echo
echo "-- LEG 2: the destruction is ALREADY COMMITTED, so LEG 1 is silent by construction --"

arm R7 1 "redB deleted AND COMMITTED -- only the ratchet can see this" <<EOF
rm -rf $T250B
git add -A >/dev/null 2>&1
git commit -qm "destroy T250 redB evidence" >/dev/null 2>&1
git status --porcelain --untracked-files=no -- $T250B
EOF

arm R8 1 "a protected root deleted ENTIRELY and committed -> ROOT GONE, not a skip" <<EOF
git rm -r -q $T274W >/dev/null 2>&1
git commit -qm "remove t274 wrap evidence" >/dev/null 2>&1
EOF

echo
echo "-- NEGATIVE CONTROLS: the guard must NOT be too eager, or it stalls every future fire --"

arm N1 0 "a NEW untracked file added under a protected root -- adding evidence is allowed" <<EOF
printf 'new capture\n' > $T250B/t304-negative-control.txt
EOF

arm N2 0 "a WHOLE NEW evidence directory added and COMMITTED -- the pin must NOT need moving" <<EOF
mkdir -p $T250B/newarm
printf 'x\n' > $T250B/newarm/probe.json
git add -A >/dev/null 2>&1
git commit -qm "a sanctioned new capture" >/dev/null 2>&1
EOF

arm N3 0 "a file changed OUTSIDE every protected root -- ordinary work must not trip it" <<'EOF'
printf '\n# t304 negative control\n' >> CLAUDE.md
EOF

echo
echo "-- REFUSALS: when it cannot measure it must REFUSE (2), never report clean --"

arm F1 2 "the pin is DELETED -> refuse, never 'clean'" <<EOF
rm -f .softhouse/capture/t304-evidence-destruction/evidence_roots.json
EOF

arm F2 2 "the pin declares ZERO roots -> an empty domain grades nothing" <<'EOF'
printf '{"roots": []}\n' > .softhouse/capture/t304-evidence-destruction/evidence_roots.json
EOF

arm F3 2 "the pin is not valid JSON -> refuse, do not fall through to clean" <<'EOF'
printf 'not json at all\n' > .softhouse/capture/t304-evidence-destruction/evidence_roots.json
EOF

echo
echo "-- INTERPRETER: the capability, never the name (P-20) --"
git -C "$SB/clone" reset --hard --quiet HEAD; git -C "$SB/clone" clean -qfd

# /bin/sh on this machine IS bash 3.2.57, so it is CAPABLE and must RUN, not refuse.
# A guard that refused it would refuse a shell that can grade correctly.
shver=$(/bin/sh -c 'echo ${BASH_VERSION:-not-bash}')
w1=$( cd "$SB/clone" && /bin/sh "$GUARD" 2>&1 ); w1rc=$?
if [ "$w1rc" -eq 0 ]; then
    printf '  %-4s expected rc=0  got rc=0  ok   /bin/sh (== bash %s here) is CAPABLE and runs\n' "W1" "$shver"
    pass=$((pass + 1))
else
    printf '  %-4s expected rc=0  got rc=%s  ***  /bin/sh (== bash %s here)\n' "W1" "$w1rc" "$shver"
    printf '%s\n' "$w1" | sed 's/^/         | /' | head -6
    unexpected=$((unexpected + 1))
fi

# A genuinely incapable POSIX shell must hit the exit-3 refusal.
if [ -x /bin/dash ]; then
    w2=$( cd "$SB/clone" && /bin/dash "$GUARD" 2>&1 ); w2rc=$?
    if [ "$w2rc" -eq 3 ]; then
        printf '  %-4s expected rc=3  got rc=3  ok   /bin/dash lacks substring expansion -> REFUSE\n' "W2"
        pass=$((pass + 1))
    else
        printf '  %-4s expected rc=3  got rc=%s  ***  /bin/dash\n' "W2" "$w2rc"
        printf '%s\n' "$w2" | sed 's/^/         | /' | head -6
        unexpected=$((unexpected + 1))
    fi
else
    printf '  %-4s SKIPPED -- no genuinely incapable shell on this machine; exit 3 is UNTESTED here\n' "W2"
fi

echo
echo "-- THE REAL TREE, UNTOUCHED, MUST STILL BE GREEN --"
z0=$( cd "$ROOT" && bash "$GUARD" 2>&1 ); z0rc=$?
if [ "$z0rc" -eq 0 ]; then
    printf '  %-4s expected rc=0  got rc=0  ok   the guard on the REAL tree\n' "Z0"
    pass=$((pass + 1))
else
    printf '  %-4s expected rc=0  got rc=%s  ***  the guard on the REAL tree -- the drive LEAKED\n' "Z0" "$z0rc"
    printf '%s\n' "$z0" | sed 's/^/         | /'
    unexpected=$((unexpected + 1))
fi

echo
echo "SCORE: $pass as expected, $unexpected unexpected"
if [ "$unexpected" -eq 0 ]; then
    echo "T304 RED DRIVE: PASS"
    exit 0
fi
echo "T304 RED DRIVE: FAIL"
exit 1
