#!/usr/bin/env bash
# T260 — (1) reproduce T255's REAL T253 collision under BOTH T253 implementations, and
#        (2) drive the ANCHOR mechanism RED in the three ways it can fail.
#
# P-80: git grep exits 1 on NO MATCH and >1 on ERROR. Every probe classifies the status.
# P-75: no bare `grep`, no `rg`. `git grep -F` and python `str.count` only.
# The sandbox is /tmp/t260/red, a plain file tree with the repo's relative layout, so the
# instruments compute the same ROOT they compute in the repo. NOTHING under the real repo is
# written by this script.
set -euo pipefail

RED=/tmp/t260/red
SH=/tmp/t260/sh
ANCHOR=$RED/.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py
LINES=$RED/.softhouse/capture/t247-dec2-rev7/verify-line-numbers.py
REV8=$RED/docs/adr/DEC-2-gl-accounting-adapter.md
REV7=$RED/docs/adr/rev7.md

run_anchor () {  # $1 = which conformance.sh
  cp "$SH/$1" "$RED/.softhouse/conformance.sh"
  set +e
  python3 "$ANCHOR" > "/tmp/t260/out.anchor.$1.txt" 2>&1
  local rc=$?
  set -e
  echo "  anchors under $1 -> exit $rc :: $(tail -1 "/tmp/t260/out.anchor.$1.txt")"
  return 0
}

run_lines () {  # $1 = which conformance.sh ; runs against the PRE-rev-8 document
  cp "$SH/$1" "$RED/.softhouse/conformance.sh"
  cp "$REV7" "$RED/docs/adr/DEC-2-gl-accounting-adapter.md"
  set +e
  python3 "$LINES" > "/tmp/t260/out.lines.$1.txt" 2>&1
  local rc=$?
  set -e
  cp "$RED/docs/adr/rev8.keep" "$RED/docs/adr/DEC-2-gl-accounting-adapter.md"
  echo "  line-numbers under $1 -> exit $rc :: $(tail -1 "/tmp/t260/out.lines.$1.txt")"
  return 0
}

cp "$REV8" "$RED/docs/adr/rev8.keep"

echo "================================================================================"
echo "PART 1 — THE REAL T253 COLLISION, reproduced under BOTH implementations"
echo "================================================================================"
for v in base.sh cloud.sh mac.sh; do
  echo "--- conformance.sh variant: $v ---"
  run_anchor "$v"
  run_lines "$v"
  echo "    SH_ROWS verdict lines:"
  # print only the four SH rows' verdicts, classifying rather than trusting
  python3 - "$v" <<'PY'
import sys
v = sys.argv[1]
txt = open("/tmp/t260/out.lines.%s.txt" % v, encoding="utf-8").read().split("\n")
inside = False
for l in txt:
    if "conformance.sh," in l and l.startswith("==="):
        inside = True
        continue
    if inside:
        if l.startswith("==="):
            inside = False
            continue
        if l.strip():
            print("      " + l.rstrip())
PY
done

echo
echo "================================================================================"
echo "PART 2 — DRIVE THE ANCHOR MECHANISM RED (the question the brief asks)"
echo "================================================================================"
cp "$SH/base.sh" "$RED/.softhouse/conformance.sh"
cp "$RED/docs/adr/rev8.keep" "$RED/docs/adr/DEC-2-gl-accounting-adapter.md"

probe () {  # $1 label, $2 python mutation of conformance.sh
  cp "$SH/base.sh" "$RED/.softhouse/conformance.sh"
  python3 -c "$2"
  set +e
  python3 "$ANCHOR" > "/tmp/t260/out.red.$1.txt" 2>&1
  local rc=$?
  set -e
  echo "--- $1 -> checker exit $rc"
  python3 - "$1" <<'PY'
import sys
v = sys.argv[1]
for l in open("/tmp/t260/out.red.%s.txt" % v, encoding="utf-8"):
    if l.startswith("  ROT") or l.startswith("  AMBIG") or l.startswith("REFUSE") \
       or l.startswith("CALIBRATION") or "MISMATCH" in l or l.startswith("ROT DETECTED") \
       or l.startswith("ALL ANCHORS"):
        print("      " + l.rstrip())
PY
  echo "    what a HUMAN following the recipe sees (git grep -n -F, status classified):"
  RC=0
  ( cd "$RED" && git grep -n -F 'guard_ledger_invariants() {' -- .softhouse/conformance.sh ) \
      > /tmp/t260/gg.txt 2>/tmp/t260/gg.err || RC=$?
  # not a git repo -> fall back to a python exact-substring resolver with the same semantics
  python3 - <<'PY'
hay = open("/tmp/t260/red/.softhouse/conformance.sh", encoding="utf-8").read().split("\n")
needle = "guard_ledger_invariants() {"
hits = [(i+1, l) for i, l in enumerate(hay) if needle in l]
if len(hits) == 0:
    print("      resolver: 0 matches -> EXIT 1 (a real measured negative). Reader gets NOTHING.")
elif len(hits) == 1:
    print("      resolver: 1 match  -> EXIT 0, line %d. Unambiguous." % hits[0][0])
else:
    print("      resolver: %d matches -> EXIT 0 (SUCCESS), lines %s."
          % (len(hits), ", ".join(str(h[0]) for h in hits)))
    print("      *** git grep does NOT fail on a non-unique anchor. It prints both and exits 0. ***")
PY
}

probe "DELETED" "
p='/tmp/t260/red/.softhouse/conformance.sh'
t=open(p).read()
t=t.replace('guard_ledger_invariants() {','guard_ledger_invariants_renamed() {',1)
open(p,'w').write(t)
"

probe "EDITED" "
p='/tmp/t260/red/.softhouse/conformance.sh'
t=open(p).read()
t=t.replace('guard_ledger_invariants() {','guard_ledger_invariants()  {',1)
open(p,'w').write(t)
"

probe "NONUNIQUE" "
p='/tmp/t260/red/.softhouse/conformance.sh'
t=open(p).read()
i=t.index('guard_ledger_invariants() {')
t=t[:i]+'# a later task copies the guard into a comment or a second definition:\n# guard_ledger_invariants() {\n'+t[i:]
open(p,'w').write(t)
"

echo
echo "--- CONTROL: unmutated base -> the checker must be GREEN, or the three RED runs prove nothing"
cp "$SH/base.sh" "$RED/.softhouse/conformance.sh"
set +e
python3 "$ANCHOR" > /tmp/t260/out.red.CONTROL.txt 2>&1
rc=$?
set -e
echo "    control exit $rc :: $(tail -1 /tmp/t260/out.red.CONTROL.txt)"
echo
echo "DONE."
