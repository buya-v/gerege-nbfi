#!/usr/bin/env bash
# T282 -- drive the citation checker RED on REAL drifted citations, then GREEN
# on their repair, and prove the OBVIOUS checker cannot tell the difference.
#
# WHY A FIXTURE TREE AND NOT THE LIVE REPO. The three drifted lines below are
# VERBATIM BYTES from three merged files. All three live in zones this checker
# deliberately does not fail closed on (`docs/adr/` is ratified, `capture/` is
# committed evidence, `tasks.json` is orchestrator-owned), and T282 is forbidden
# from editing any of them. So driving RED on the live tree is impossible
# WITHOUT first breaking the ownership rule. The fixture instead REPLANTS those
# exact bytes into `.softhouse/RESUME.md` -- a DIRECTIVE file, the fatal zone,
# and the site of the first recorded instance of this very defect. Same bytes,
# a zone where they are supposed to stop the run.
#
# `--root` is the checker's own flag; the fixture is a real git repo because the
# checker enumerates with `git ls-files` and would otherwise exit 3 (CANNOT RUN,
# never 0 -- P-36: an experiment whose input never arrives looks like a result).
#
# P-84: read the PROBE LINE'S PRESENCE before its value. Every stage below
# asserts the VERDICT line was PRINTED before it reads the exit code, because an
# exit code with no verdict line is a crash wearing a result's clothes.
set -u
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
CHECK="$HERE/check-pnumber-citations.py"
OUT="$HERE/../red"
mkdir -p "$OUT"

FIX="$(mktemp -d "${TMPDIR:-/tmp}/t282-redgreen.XXXXXX")"
trap 'rm -rf "$FIX"' EXIT

fail=0
note() { printf '\n== %s\n' "$*"; }

note "FIXTURE TREE: $FIX  (register copied verbatim from $REPO/.softhouse/patterns.md)"
mkdir -p "$FIX/.softhouse"
cp "$REPO/.softhouse/patterns.md" "$FIX/.softhouse/patterns.md"
cp "$REPO/.softhouse/gates-proposed-answers.md" "$FIX/.softhouse/gates-proposed-answers.md"

# ---------------------------------------------------------------------------
# THE THREE DRIFTED CITATIONS. Verbatim, with provenance. Each names the id it
# CITES and the id patterns.md actually defines that sentence under.
# ---------------------------------------------------------------------------
cat > "$FIX/.softhouse/RESUME.md" <<'RED_EOF'
# STANDING INSTRUCTIONS (T282 RED fixture)

Three citations below are VERBATIM BYTES lifted from merged files in this repo.
Provenance is on the line above each one. Nothing here is invented.

<!-- from docs/adr/DEC-2-gl-accounting-adapter.md:294 -- cites P-79, states P-80 -->
> section number and restates no number** — `P-79`: never fix a rotted number, make the second site
> READ the first.

<!-- from .softhouse/capture/t256-verdict-predicate/RULES-failopen.md:17 -- cites P-80, states P-81 -->
| `\|\| echo …` | **P-80**: prints an absence over an error. `grep` exits 1 on NO MATCH and >1 on ERROR; `\|\| echo 0` makes those the same number |

<!-- from .softhouse/tasks.json:2427 -- cites P-80, states P-81 -->
Three separate workers last fire wrote fail-opens INTO instruments meant to enforce the rule they broke (P-80) — check T250's own instruments before you check anything else.
RED_EOF
cp "$FIX/.softhouse/RESUME.md" "$OUT/fixture-RED-RESUME.md"

git -C "$FIX" init -q
git -C "$FIX" add -A

# ---------------------------------------------------------------------------
note "STAGE 1 -- RED. Expect: VERDICT FAIL printed, exit 1, 3 directive FATAL."
# ---------------------------------------------------------------------------
"$CHECK" --root "$FIX" --show all > "$OUT/10-RED.txt" 2>&1
red_rc=$?
if ! grep -q '^PNUMBER-CITATIONS: VERDICT ' "$OUT/10-RED.txt"; then
  echo "HARD FAIL -- no VERDICT line printed at all. exit was $red_rc. That is a"
  echo "crash, NOT a red result, and it must never be read as one (P-84)."
  fail=1
else
  grep -E '^PNUMBER-CITATIONS: (VERDICT|FATAL MISDIRECTING .softhouse/RESUME)' "$OUT/10-RED.txt"
  n_fatal=$(grep -c '^PNUMBER-CITATIONS: FATAL MISDIRECTING .softhouse/RESUME.md' "$OUT/10-RED.txt")
  echo "exit=$red_rc  directive-fatal-on-RESUME.md=$n_fatal"
  [ "$red_rc" -eq 1 ] || { echo "HARD FAIL: expected exit 1, got $red_rc"; fail=1; }
  [ "$n_fatal" -eq 3 ] || { echo "HARD FAIL: expected 3 fatal, got $n_fatal"; fail=1; }
fi

# ---------------------------------------------------------------------------
note "STAGE 2 -- THE OBVIOUS CHECKER, ON THE SAME RED BYTES."
echo "The predicate 'is the cited P-number defined in patterns.md?' -- run over"
echo "the identical fixture that just produced 3 FATAL findings."
# ---------------------------------------------------------------------------
python3 - "$FIX" > "$OUT/20-existence-only-on-RED.txt" 2>&1 <<'PY_EOF'
import re, sys, os
root = sys.argv[1]
DEFN = re.compile(r'^(?:[-*>]\s+)?(?:#{2,4}\s+|\*\*)P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')
CITE = re.compile(r'(?<![A-Za-z0-9_])P-([1-9][0-9]*)(?![0-9])')
defined = set()
with open(os.path.join(root, ".softhouse/patterns.md"), encoding="utf-8") as fh:
    for line in fh:
        m = DEFN.match(line.strip())
        if m:
            defined.add(int(m.group(1)))
bad = []
n = 0
with open(os.path.join(root, ".softhouse/RESUME.md"), encoding="utf-8") as fh:
    for i, line in enumerate(fh, 1):
        for m in CITE.finditer(line):
            n += 1
            if int(m.group(1)) not in defined:
                bad.append((i, m.group(0)))
print("EXISTENCE-ONLY CHECKER: register holds %d ids; %d citations examined" % (len(defined), n))
print("EXISTENCE-ONLY CHECKER: undefined citations = %d  %s" % (len(bad), bad))
print("EXISTENCE-ONLY CHECKER: VERDICT %s" % ("FAIL" if bad else "PASS"))
sys.exit(1 if bad else 0)
PY_EOF
exist_rc=$?
cat "$OUT/20-existence-only-on-RED.txt"
echo "exit=$exist_rc"
if [ "$exist_rc" -ne 0 ]; then
  echo "HARD FAIL: the existence-only checker was supposed to PASS these bytes."
  fail=1
else
  echo "^^ THIS IS THE POINT. Every cited id EXISTS, so the obvious guard is GREEN"
  echo "   on the exact bytes the sentence-matching guard calls 3x FATAL. A guard"
  echo "   that only checks the number would have passed BOTH recorded instances."
fi

# ---------------------------------------------------------------------------
note "STAGE 3 -- REPAIR. Change the CARDINALS ONLY; every sentence is untouched."
# ---------------------------------------------------------------------------
python3 - "$FIX/.softhouse/RESUME.md" <<'PY_EOF'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
subs = [("`P-79`: never fix a rotted number", "`P-80`: never fix a rotted number"),
        ("**P-80**: prints an absence over an error", "**P-81**: prints an absence over an error"),
        ("the rule they broke (P-80)", "the rule they broke (P-81)")]
for old, new in subs:
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("repaired 3 cardinals; 0 sentences altered")
PY_EOF
cp "$FIX/.softhouse/RESUME.md" "$OUT/fixture-GREEN-RESUME.md"
diff -u "$OUT/fixture-RED-RESUME.md" "$OUT/fixture-GREEN-RESUME.md" > "$OUT/30-repair.diff"
echo "--- the entire repair, and it is three digits: ---"
grep -E '^[-+][^-+]' "$OUT/30-repair.diff" | sed 's/^/  /'
git -C "$FIX" add -A

# ---------------------------------------------------------------------------
note "STAGE 4 -- GREEN. Same file, same sentences, repaired ids. Expect exit 0."
# ---------------------------------------------------------------------------
"$CHECK" --root "$FIX" --show all > "$OUT/40-GREEN.txt" 2>&1
green_rc=$?
if ! grep -q '^PNUMBER-CITATIONS: VERDICT ' "$OUT/40-GREEN.txt"; then
  echo "HARD FAIL -- no VERDICT line printed. exit was $green_rc; that is a crash."
  fail=1
else
  grep -E '^PNUMBER-CITATIONS: VERDICT' "$OUT/40-GREEN.txt"
  n_fatal=$(grep -c '^PNUMBER-CITATIONS: FATAL' "$OUT/40-GREEN.txt")
  echo "exit=$green_rc  fatal=$n_fatal"
  [ "$green_rc" -eq 0 ] || { echo "HARD FAIL: expected exit 0, got $green_rc"; fail=1; }
  [ "$n_fatal" -eq 0 ] || { echo "HARD FAIL: expected 0 fatal, got $n_fatal"; fail=1; }
fi

# ---------------------------------------------------------------------------
note "STAGE 5 -- MUTATION CONTROL. Re-break ONE id and confirm the guard notices"
echo "a single-site regression, not merely the batch of three (P-76: driven red"
echo "only on the shape it was built from proves the wiring, not the coverage)."
# ---------------------------------------------------------------------------
python3 - "$FIX/.softhouse/RESUME.md" <<'PY_EOF'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
s = s.replace("`P-80`: never fix a rotted number", "`P-84`: never fix a rotted number")
io.open(p, "w", encoding="utf-8").write(s)
print("re-broke exactly one cardinal: P-80 -> P-84 (a DIFFERENT wrong id than the original drift)")
PY_EOF
git -C "$FIX" add -A
"$CHECK" --root "$FIX" --show all > "$OUT/50-MUTANT.txt" 2>&1
mut_rc=$?
if ! grep -q '^PNUMBER-CITATIONS: VERDICT ' "$OUT/50-MUTANT.txt"; then
  echo "HARD FAIL -- no VERDICT line printed. exit was $mut_rc."
  fail=1
else
  grep -E '^PNUMBER-CITATIONS: (VERDICT|FATAL MISDIRECTING .softhouse/RESUME)' "$OUT/50-MUTANT.txt"
  n_fatal=$(grep -c '^PNUMBER-CITATIONS: FATAL MISDIRECTING .softhouse/RESUME.md' "$OUT/50-MUTANT.txt")
  echo "exit=$mut_rc  directive-fatal=$n_fatal"
  [ "$mut_rc" -eq 1 ] && [ "$n_fatal" -eq 1 ] || {
    echo "HARD FAIL: expected exit 1 with exactly 1 fatal, got exit $mut_rc / $n_fatal fatal"; fail=1; }
fi

note "RESULT"
if [ "$fail" -eq 0 ]; then
  echo "T282 RED/GREEN: PASS -- RED exit 1 (3 fatal) / existence-only GREEN on the"
  echo "same bytes / repaired GREEN exit 0 / single-site mutant RED exit 1 (1 fatal)."
  exit 0
fi
echo "T282 RED/GREEN: FAIL -- see $OUT"
exit 1
