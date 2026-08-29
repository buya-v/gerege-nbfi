#!/bin/bash
# T464 — is the born-at-tip ADJUDICATION TABLE falsifiable in BOTH directions, or is it a
# rubber stamp? An adjudication list that could only say YES is the fail-open re-spelled.
#   7a  fabricated obs, adjudicated by name+digest        -> expect 0
#   7b  its adjudicated BYTES then changed                -> expect 1 (ADJUDICATION MOVED)
#   7c  a DEAD entry naming nothing born at the tip       -> expect 1 (silent widening)
set -u
S='.softhouse'
CAP="$S/capture/tierA-a2"
GRADER="$S/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
SRC="${T464_SRC:?}"; SCRATCH="${T464_SCRATCH:?}"; AFTER_REF="${T464_AFTER:?}"
D="$SCRATCH/adj"; FAIL=0
NM="A2-999-T464-FABRICATED.json"

prepare() {
  if [ ! -d "$D/.git" ]; then rm -rf "$D"; git clone --quiet --shared "$SRC" "$D" || return 3; fi
  git -C "$D" checkout --quiet --force --detach "$AFTER_REF" || return 3
  git -C "$D" reset --quiet --hard "$AFTER_REF" || return 3
  git -C "$D" clean -qfdx || return 3
}
fabricate() {
  printf '{"fabricated":true,"note":"T464 drive"}\n' > "$D/$CAP/out/$NM" || return 3
  H="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$D/$CAP/out/$NM")"
  printf '%s  out/%s\n' "$H" "$NM" >> "$D/$MAN"
  LC_ALL=C sort -k2 "$D/$MAN" -o "$D/$MAN"
  git -C "$D" add -- "$CAP/out/$NM" "$MAN"
  git -C "$D" -c user.name=t464 -c user.email=t464@local commit -q -m "T464 fabricated born-at-tip"
}
adjudicate() {  # adjudicate <name> <digest>
  python3 - "$D/$GRADER" "$1" "$2" <<'PYEOF'
import sys
p, name, dig = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8").read()
old = "ARM_F_BORN_AT_TIP_ADJUDICATED = {}"
assert old in s, "table anchor missing"
open(p, "w", encoding="utf-8").write(
    s.replace(old, 'ARM_F_BORN_AT_TIP_ADJUDICATED = {"out/%s": "%s"}' % (name, dig), 1))
PYEOF
}
grade() { ( cd "$D" && python3 "$GRADER" ) > "$SCRATCH/$1.txt" 2>&1; echo $?; }
expect() { if [ "$2" = "$3" ]; then echo "  OK   $1: exit $2"; else echo "  BAD  $1: exit $2 want $3"; FAIL=$((FAIL+1)); fi; }

echo "############ T464 — ADJUDICATION TABLE, DRIVEN BOTH WAYS"
prepare || exit 3; fabricate || exit 3; adjudicate "$NM" "$H" || exit 3
RC="$(grade 7a)"; expect "7a adjudicated by name+digest" "$RC" 0
grep -c 'FAIL ' "$SCRATCH/7a.txt" | sed 's/^/       FAIL lines: /'
grep -E 'ADJUDICATED' "$SCRATCH/7a.txt" | head -2 | sed 's/^/       /'

printf '{"fabricated":true,"note":"T464 drive MUTATED AFTER ADJUDICATION"}\n' > "$D/$CAP/out/$NM"
NEW="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$D/$CAP/out/$NM")"
python3 - "$D/$MAN" "$H" "$NEW" <<'PYEOF'
import sys
p, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8").read()
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
PYEOF
git -C "$D" add -A >/dev/null
git -C "$D" -c user.name=t464 -c user.email=t464@local commit -q -m "T464 change the adjudicated bytes"
RC="$(grade 7b)"; expect "7b adjudicated BYTES changed" "$RC" 1
grep -E 'MOVED|FAIL ' "$SCRATCH/7b.txt" | head -4 | sed 's/^/       /'

prepare || exit 3; adjudicate "A2-000-NOT-BORN-AT-TIP.json" "deadbeef"
RC="$(grade 7c)"; expect "7c DEAD entry, nothing born at tip" "$RC" 1
grep -E 'FAIL ' "$SCRATCH/7c.txt" | head -2 | sed 's/^/       /'

echo
[ "$FAIL" -ne 0 ] && { echo "T464 ADJUDICATION DRIVE: $FAIL case(s) off."; exit 1; }
echo "T464 ADJUDICATION DRIVE: 3/3. EXIT 0"
