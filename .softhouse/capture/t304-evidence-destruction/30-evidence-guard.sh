#!/usr/bin/env bash
# T304 -- the evidence-destruction guard.
#
# WHAT IT ENFORCES
#   Committed evidence under an adjudicated protected root must not DISAPPEAR or be
#   REWRITTEN IN PLACE. Eight instruments in this tree `rm -rf` their own committed
#   evidence directory at start-up (census: 10-census.py -> 20-resolve-targets.py;
#   adjudication: adjudication.json family A). Running any of them replaces committed
#   files with a fresh capture and says nothing. T114's standing ruling -- anything that
#   produced committed evidence is superseded by a scratch copy, NEVER edited in place --
#   has no executable enforcement today; this is it.
#
# WHY IT IS NOT A PER-SITE REPAIR
#   Three of the eight sites are BYTE-FROZEN by T284's callsite_registry.json
#   (30-redB-mismatch-detected.sh c08602cc, t261-redB-attack.sh 86a2f0ec,
#   t261-redC-wrap.sh 76a4dfce). T284's red-drive arm R3 -- "a FROZEN file gains a byte"
#   -- exits 1. Adding a refusal INSIDE those three would turn T284's guard red and would
#   itself breach T114. The enforcement therefore has to sit OUTSIDE the instruments.
#
# TWO LEGS
#   LEG 1  worktree: a tracked file under a protected root that is DELETED or MODIFIED
#          relative to HEAD. Catches the destruction in the window between the instrument
#          running and the worker's `git add -A` sweeping it into an unrelated commit --
#          which is the window in which it becomes unattributable.
#   LEG 2  ratchet: the tracked file COUNT per root, against a pinned FLOOR. Catches a
#          destruction that has already been committed. DECREASE-ONLY: additions are
#          always allowed and never require moving the pin. F-T283-7 measured the other
#          shape (`attest_population_pin.json`, an EQUALITY pin) going red on 22
#          sanctioned tierA-a2 captures; a decrease-only ratchet cannot do that.
#
# FAIL DIRECTION, per leg, deliberately:
#   LEG 1 fails CLOSED toward refusing. A legitimate supersession under T114 writes a NEW
#         directory -- an ADD -- and never a D or an M, so the eager direction costs the
#         sanctioned workflow nothing. Measured below: the clean tree is green.
#   LEG 2 fails CLOSED toward refusing only on a DECREASE, because a decrease is the only
#         movement that can lose evidence.
#   Both REFUSE (exit 2) rather than pass when they cannot measure -- missing pin,
#   unreadable pin, a pinned root that no longer exists, or zero roots inspected. P-22:
#   "a guard, a canary, or a control that cannot fail is worse than none -- because it is
#   believed ... a guard that inspects zero files must be an error, not a pass."
#
# EXITS
#   0  all protected roots intact
#   1  committed evidence destroyed or rewritten in place
#   2  REFUSED -- no verdict is available (never to be read as clean)
#   3  wrong interpreter

# --- interpreter refusal: FEATURE-TEST THE CAPABILITY, NEVER THE SHELL'S NAME ---
# P-20 (patterns.md): "a driver's dispatch brief is an unreviewed artefact, and it can be
# WRONG in ways the worker must be free to refuse" -- the instance being T81, told that
# `bash` via an `sh` symlink was a legitimate run, when on this machine /bin/sh IS bash
# 3.2.57 and POSIX mode disables process substitution. Two consequences, both applied here:
#   (1) this guard uses NO process substitution, so bash-as-sh can run it correctly and
#       must not be refused merely for being called `sh`;
#   (2) the refusal probes the one capability actually required -- bash substring
#       expansion -- instead of reading $BASH_VERSION, which is set under `sh` too.
# [VERIFIED on this machine: `/bin/sh -c 'echo ${BASH_VERSION}'` prints 3.2.57(1)-release,
#  so a $BASH_VERSION test would have PASSED under sh and proved nothing. /bin/dash is
#  present and is genuinely incapable; red-drive arm W2 exercises it.]
if ! ( _p=abcdef; [ "${_p:0:2}" = "ab" ] ) 2>/dev/null; then
    echo "t304-evidence-guard: REFUSING -- this shell lacks bash substring expansion." >&2
    exit 3
fi

set -uo pipefail

refuse() { printf 't304-evidence-guard: REFUSED -- %s\n' "$*" >&2; exit 2; }

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || refuse "not inside a git repository."
[ -d "$ROOT/.softhouse" ] || refuse "$ROOT does not contain .softhouse; wrong repository root."

PIN="${T304_PIN:-$ROOT/.softhouse/capture/t304-evidence-destruction/evidence_roots.json}"
[ -f "$PIN" ] || refuse "the protected-root pin is missing: ${PIN#"$ROOT/"}. A guard with no pin inspects nothing, and a guard that inspects nothing must not report clean."
[ -r "$PIN" ] || refuse "the protected-root pin is unreadable: ${PIN#"$ROOT/"}."

# ---------------------------------------------------------------- read the pin
# python3 is already a hard dependency of this repo's instrument corpus.
# NO `mapfile`/`readarray`: /bin/bash on this platform is 3.2.57 and does not have them.
PINTMP=$(mktemp "${TMPDIR:-/tmp}/t304pin.XXXXXX") || refuse "mktemp failed."
STATTMP=$(mktemp "${TMPDIR:-/tmp}/t304stat.XXXXXX") || refuse "mktemp failed."
trap 'rm -f "$PINTMP" "$STATTMP"' EXIT

python3 - "$PIN" > "$PINTMP" 2>/dev/null <<'PY'
import json, sys
try:
    rows = json.load(open(sys.argv[1]))["roots"]
except Exception as e:
    print("PARSE_ERROR %s" % e)
    sys.exit(0)
for r in rows:
    print("%s\t%d" % (r["path"], int(r["min_tracked_files"])))
PY

nroots=$(wc -l < "$PINTMP" | tr -d ' ')
if [ "${nroots:-0}" -eq 0 ]; then
    refuse "the pin declares ZERO protected roots. An empty domain grades nothing."
fi
case "$(head -1 "$PINTMP")" in
    PARSE_ERROR*) refuse "the pin is not valid JSON: $(head -1 "$PINTMP")" ;;
esac

rc=0
inspected=0
findings=0

echo "T304 evidence-destruction guard"
echo "  pin   : ${PIN#"$ROOT/"}"
echo "  roots : $nroots"
echo

while IFS=$'\t' read -r path floor; do
    [ -n "$path" ] || refuse "the pin carries an empty root path."

    # A pinned root that has vanished entirely is the worst case, not a skip.
    n=$(git -C "$ROOT" ls-files -- "$path" | wc -l | tr -d ' ')
    if [ "$n" -eq 0 ]; then
        printf '  ROOT GONE   %-68s pinned floor %s, measured 0 tracked file(s)\n' "$path" "$floor"
        findings=$((findings + 1))
        rc=1
        continue
    fi
    inspected=$((inspected + 1))

    # ---- LEG 2: decrease-only ratchet over the COMMITTED state
    if [ "$n" -lt "$floor" ]; then
        printf '  RATCHET     %-68s pinned floor %s, measured %s -- committed evidence was REMOVED\n' "$path" "$floor" "$n"
        findings=$((findings + 1))
        rc=1
    fi

    # ---- LEG 1: worktree/index D or M of a tracked file under the root
    # `--untracked-files=no` on purpose: ADDING evidence is always allowed.
    # No process substitution -- see the interpreter note at the top.
    git -C "$ROOT" status --porcelain --untracked-files=no -- "$path" > "$STATTMP" 2>/dev/null
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        xy=${line:0:2}
        f=${line:3}
        case "$xy" in
            *D*|*M*|*R*)
                printf '  DESTROYED   %-68s %s %s\n' "$path" "$xy" "$f"
                findings=$((findings + 1))
                rc=1
                ;;
        esac
    done < "$STATTMP"
done < "$PINTMP"

if [ "$inspected" -eq 0 ]; then
    refuse "ZERO protected roots were inspectable. Reporting clean over an empty domain is the exact fail-open this guard exists to remove."
fi

echo
if [ "$rc" -eq 0 ]; then
    echo "t304-evidence-guard: PASS -- $inspected protected root(s), no committed evidence deleted, rewritten or renamed."
else
    cat >&2 <<EOF

t304-evidence-guard: FAIL -- $findings finding(s).

Committed evidence under a protected root has been deleted, rewritten in place, or
renamed. This is what happens when one of the eight family-A instruments is run in the
real checkout: it \`rm -rf\`s its own committed evidence directory at start-up and
rewrites it with a fresh capture.

T114 binds: anything that produced committed evidence is superseded by a SCRATCH copy,
never edited in place. If you meant to re-capture, run the instrument against a scratch
clone and commit a NEW directory.

To see what moved:   git status --porcelain --untracked-files=no -- <root>
To put it back:      git checkout -- <root>
The census and the per-site adjudication behind this pin:
  .softhouse/capture/t304-evidence-destruction/adjudication.json
EOF
fi
exit $rc
