#!/usr/bin/env bash
# T471 -- T465 RE-SCOPED `check-lock-exclusion-anchor.sh` (handoff §2.3) and reports ONE drive:
# "Driven against the live file: VERDICT: PASS". A re-scoped probe driven only GREEN is the
# shape this program keeps having to reject, so this drives it RED.
#
# The probe takes its TARGET as $1, so every arm below runs against a SCRATCH COPY of
# fire-program.sh outside the graded repo. The live file is never touched.
#
# ARMS:
#   GREEN        unmodified copy                                -> expect exit 0
#   K-DECL       the DECLARATION widened by one `*`             -> expect nonzero; this is the
#                                                                  widening T465 claims is now
#                                                                  caught where NO use site
#                                                                  would show it
#   K-USE        one USE site widened (drops out of the census) -> expect nonzero via the T215
#                                                                  categorical floor
#   K-DUP        the declaration duplicated at column 0         -> expect exit 2 (refusal)
#
# NO REAL REPO PATH IS SPELT HERE (P-103): assembled from $S.
# EXIT 0 all arms behaved; 1 an arm misbehaved; 2 a dependency did not resolve.

set -u
S=".softhouse"
PROBE_REL="$S/reviews/t172-probe/check-lock-exclusion-anchor.sh"
TARGET_REL="$S/bin/fire-program.sh"
DECL_NAME="LOCK_EXCLUDE_PATHSPEC"

SRC="${1:-}"; OUTDIR="${2:-}"
[ -n "$SRC" ] && [ -n "$OUTDIR" ] || { echo "usage: $0 <tree> <outdir>" >&2; exit 2; }
case "$SRC" in /Users/buv/gerege-nbfi*) echo "ERROR: the tree under test must be OUTSIDE the graded repo." >&2; exit 2;; esac
[ -f "$SRC/$PROBE_REL" ] || { echo "ERROR: no probe at $SRC/$PROBE_REL -- REFUSING" >&2; exit 2; }
[ -f "$SRC/$TARGET_REL" ] || { echo "ERROR: no target at $SRC/$TARGET_REL -- REFUSING" >&2; exit 2; }
[ -d "$OUTDIR" ] || { echo "ERROR: no outdir" >&2; exit 2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t471-anchor.XXXXXX") || exit 2
bad=0

arm () {  # $1 label, $2 expect (0 | nonzero | 2)
  local label exp f rc
  label="$1"; exp="$2"
  f="$OUTDIR/anchor-$label.txt"
  zsh "$SRC/$PROBE_REL" "$WORK/target.sh" >"$f" 2>&1
  rc=$?
  printf 'ARM=%-8s exit=%-3s (expected %s)\n' "$label" "$rc" "$exp"
  grep -aE 'VERDICT|FAIL|ERROR|REFUS' "$f" | sed -n '1,3p' | sed 's/^/    /'
  case "$exp" in
    0)       [ "$rc" -eq 0 ] || { echo "    ** MISBEHAVED"; bad=1; } ;;
    2)       [ "$rc" -eq 2 ] || { echo "    ** MISBEHAVED"; bad=1; } ;;
    nonzero) [ "$rc" -ne 0 ] || { echo "    ** MISBEHAVED: GREEN on a planted defect"; bad=1; } ;;
  esac
}

echo "=== GREEN: unmodified copy"
cp "$SRC/$TARGET_REL" "$WORK/target.sh"
arm GREEN 0

echo "=== K-DECL: widen the DECLARATION by one character"
cp "$SRC/$TARGET_REL" "$WORK/target.sh"
python3 - "$WORK/target.sh" "$DECL_NAME" <<'PY'
import sys
p, name = sys.argv[1], sys.argv[2]
t = open(p).read().split("\n")
hits = [i for i, l in enumerate(t) if l.startswith(name + "=")]
assert len(hits) == 1, "expected exactly one declaration, found %d" % len(hits)
t[hits[0]] = t[hits[0]].replace('"', '', 0)
line = t[hits[0]]
# widen: append a glob INSIDE the quoted value
assert line.count('"') >= 2, line
i = line.rfind('"')
t[hits[0]] = line[:i] + '*' + line[i:]
open(p, "w").write("\n".join(t))
PY
arm K-DECL nonzero

echo "=== K-USE: widen ONE use site so it drops out of the census"
cp "$SRC/$TARGET_REL" "$WORK/target.sh"
python3 - "$WORK/target.sh" "$DECL_NAME" <<'PY'
import sys
p, name = sys.argv[1], sys.argv[2]
t = open(p).read().split("\n")
frag = '"$%s"' % name
hits = [i for i, l in enumerate(t) if frag in l and not l.lstrip().startswith("#")]
assert len(hits) >= 1, "no use site found"
t[hits[0]] = t[hits[0]].replace(frag, '"${%s}*"' % name, 1)
open(p, "w").write("\n".join(t))
PY
arm K-USE nonzero

echo "=== K-DUP: duplicate the declaration at column 0"
cp "$SRC/$TARGET_REL" "$WORK/target.sh"
python3 - "$WORK/target.sh" "$DECL_NAME" <<'PY'
import sys
p, name = sys.argv[1], sys.argv[2]
t = open(p).read().split("\n")
hits = [i for i, l in enumerate(t) if l.startswith(name + "=")]
assert len(hits) == 1
t.insert(hits[0] + 1, t[hits[0]])
open(p, "w").write("\n".join(t))
PY
arm K-DUP 2

rm -rf "$WORK"
echo "T471-ANCHOR-CANFAIL: arms=4 misbehaved=$bad"
[ "$bad" -eq 0 ] || exit 1
