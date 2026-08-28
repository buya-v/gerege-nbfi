#!/usr/bin/env bash
# T145 -- RED/GREEN drive for guard-float-decides-money.py.
# A guard that has never been seen to fail is a decoration (P-22). Four legs.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
G="$ROOT/.softhouse/capture/t145-analysis-float/bin/guard-float-decides-money.py"
PLANT="$ROOT/.softhouse/capture/t145-analysis-float/out/planted_breach.py"
pass=0; fail=0

leg () {  # leg <name> <expected-exit> <actual-exit>
  if [ "$2" = "$3" ]; then echo "  AS PREDICTED  $1 (exit $3)"; pass=$((pass+1));
  else echo "  !! WRONG      $1 wanted exit $2, got $3"; fail=$((fail+1)); fi
}

echo "T145 -- guard RED/GREEN"
echo "REV=$(git -C "$ROOT" rev-parse HEAD)"
echo

python3 "$G" "$ROOT" >/dev/null 2>&1; leg "GREEN  clean tree, both sites declared" 0 $?

cat > "$PLANT" <<'PY'
# PLANTED BREACH -- written and deleted by drive-guard-red.sh, never committed.
import json
got = json.load(open("x"))["emi"]
want = json.load(open("y"))["emi"]
if float(got) != float(want):
    print("money moved")
PY
git -C "$ROOT" add -f .softhouse/capture/t145-analysis-float/out/planted_breach.py >/dev/null 2>&1
python3 "$G" "$ROOT" > "$ROOT/.softhouse/capture/t145-analysis-float/out/guard-red-leg.txt" 2>&1
r=$?; leg "RED    a NEW two-sided float money comparison" 2 $r
grep -q "planted_breach.py:5" "$ROOT/.softhouse/capture/t145-analysis-float/out/guard-red-leg.txt" \
  && { echo "  AS PREDICTED  the guard named the planted line 5"; pass=$((pass+1)); } \
  || { echo "  !! WRONG      the guard did not name planted_breach.py:5"; fail=$((fail+1)); }
git -C "$ROOT" rm -f --cached .softhouse/capture/t145-analysis-float/out/planted_breach.py >/dev/null 2>&1
rm -f "$PLANT"

# RED-2: a ONE-SIDED float comparison -- T186 rule A1's ratified shape -- must NOT fire.
cat > "$PLANT" <<'PY'
# PLANTED A1-SHAPE -- repr(float(tok)) == tok. One side is a STRING. PERMITTED.
def check(tok):
    return repr(float(tok)) == tok
PY
git -C "$ROOT" add -f .softhouse/capture/t145-analysis-float/out/planted_breach.py >/dev/null 2>&1
python3 "$G" "$ROOT" >/dev/null 2>&1; leg "GREEN  A1's ratified one-sided shape does NOT fire" 0 $?
git -C "$ROOT" rm -f --cached .softhouse/capture/t145-analysis-float/out/planted_breach.py >/dev/null 2>&1
rm -f "$PLANT"

# RED-3: a DECLARED site that vanished must also fail -- the declaration cannot become a silencer.
python3 - "$ROOT" <<'PY' > "$ROOT/.softhouse/capture/t145-analysis-float/out/guard-vanish-leg.txt" 2>&1
import subprocess, sys, tempfile, shutil, os, re
root = sys.argv[1]
g = os.path.join(root, ".softhouse/capture/t145-analysis-float/bin/guard-float-decides-money.py")
src = open(g).read()
# point the declaration at a line that is NOT a two-sided float comparison
mutant = src.replace('".softhouse/capture/actualactual/analysis/discriminate.py": (\n        160,',
                     '".softhouse/capture/actualactual/analysis/discriminate.py": (\n        9999,')
assert mutant != src, "mutation did not apply"
tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=os.path.dirname(g))
tmp.write(mutant); tmp.close()
p = subprocess.run([sys.executable, tmp.name, root], capture_output=True, text=True)
os.unlink(tmp.name)
print("exit=%d" % p.returncode)
print(p.stdout)
PY
v=$(grep -o 'exit=[0-9]*' "$ROOT/.softhouse/capture/t145-analysis-float/out/guard-vanish-leg.txt" | head -1 | cut -d= -f2)
leg "RED    a DECLARED site pointed at a vanished line" 2 "$v"

echo
echo "LEGS: $((pass+fail))   AS PREDICTED: $pass   WRONG: $fail"
[ "$fail" = 0 ] || exit 1
echo "GUARD RED/GREEN PASS -- the guard has been SEEN to fail, and seen not to fire on A1."
