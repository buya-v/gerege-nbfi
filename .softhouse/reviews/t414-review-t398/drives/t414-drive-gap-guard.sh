#!/usr/bin/env bash
# T414 -- INDEPENDENT re-derivation of T398's register-gap claim.
#
# Written from the brief and from reading the checker, NOT by editing T398's
# drive. Six arms, in two groups.
#
# GROUP 1 -- THE LATENT FATAL, ON PRE-T398 `main`. The checker as `main` carries
# it, with NO exemption. This is the claim that motivates the whole change.
#   ARM 0-CTL  main checker + main patterns.md UNTOUCHED (max(reg)=98, P-99 is
#              BEYOND the register)                       -> want gaps=none rc=0
#   ARM 0-FAT  main checker + main patterns.md + ONE dummy definition at 100
#              (P-99 is now INTERIOR)                     -> want FATAL GAP 99 rc=1
#   The pair is the control: the ONLY difference between them is a pattern filed
#   above 99. If 0-CTL is green and 0-FAT is red, the register was frozen at 98.
#
# GROUP 2 -- IS THE FIX A WIDENING? Against T398's BRANCH tree.
#   ARM A  real branch tree                               -> want rc=0 gaps=none
#   ARM B  UNDECLARED hole: 97's definition deleted       -> want rc=1 GAP 97
#   ARM C  branch input, exemption NEUTRALISED in a copy  -> want rc=1 GAP 99
#
# Nothing mutates the repo tree; every arm runs in a throwaway scratch root.
#   bash <this> <repo-root>
set -uo pipefail
REPO=${1:?usage: <repo-root>}
CHK=.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py
MAIN=main
BR=softhouse/T398-measured-but-backwards
T=$(mktemp -d "${TMPDIR:-/tmp}/t414-gap.XXXXXX") || exit 2
trap 'rm -rf "$T"' EXIT

echo "repo    : $REPO"
echo "engine  : $(python3 -VV 2>&1 | head -1)"
echo "main    : $(git -C "$REPO" rev-parse --short "$MAIN")"
echo "T398    : $(git -C "$REPO" rev-parse --short "$BR")"
echo

# materialise a treeish into a scratch root that is its own git repo, because
# the checker enumerates its corpus with `git ls-files`.
mat() { # <treeish> <dest>
  mkdir -p "$2"
  git -C "$REPO" archive "$1" | tar -x -C "$2" 2>/dev/null
}
seal() { # <dest> -- make it a git repo so `git ls-files` answers
  git -C "$1" init -q . >/dev/null 2>&1
  git -C "$1" add -A >/dev/null 2>&1
  git -C "$1" -c user.email=t414@local -c user.name=T414 commit -qm scratch >/dev/null 2>&1
}
say() { LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (register=|FATAL|VERDICT)' "$1" | sed 's/^/    /'; }
run() { ( cd "$1" && python3 "$CHK" ) > "$2" 2>&1; echo $?; }

echo '################ GROUP 1 -- THE LATENT FATAL ON PRE-T398 main ################'
echo
echo "=== ARM 0-CTL: main checker, main patterns.md UNTOUCHED ======================="
mat "$MAIN" "$T/0c"; seal "$T/0c"
grep -n 'gaps = \[n for n in range' "$T/0c/$CHK" | sed 's/^/    main gap scan: /'
R0C=$(run "$T/0c" "$T/0c.txt"); say "$T/0c.txt"
echo "    rc=$R0C   EXPECT rc=0, gaps=none -- the reserved id sits BEYOND max(reg)=98"
echo
echo "=== ARM 0-FAT: main checker, ONE dummy pattern filed at 100 ==================="
mat "$MAIN" "$T/0f"
python3 - "$T/0f/.softhouse/patterns.md" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# a single DEFN_BOLD-shaped definition line, appended. Nothing else changes.
s += ("\n\n---\n\n**P-100 - A DUMMY DEFINITION FILED BY T414'S DRIVE TO CROSS THE RESERVED ID.**\n"
      "\nThis rule has no content. Its only job is to make max(reg) exceed the reserved\n"
      "id so the gap scan sees that reserved absence as an INTERIOR hole.\n")
open(p, "w", encoding="utf-8").write(s)
print("    appended ONE dummy definition line at 100 -- no other edit")
PY
seal "$T/0f"
R0F=$(run "$T/0f" "$T/0f.txt"); say "$T/0f.txt"
echo "    rc=$R0F   EXPECT rc=1 and FATAL REGISTER GAP on the reserved id -- the latent fatal"
echo
echo '################ GROUP 2 -- IS THE FIX A WIDENING? ###########################'
echo
echo "=== ARM A: T398 branch tree as landed ========================================="
mat "$BR" "$T/a"; seal "$T/a"
grep -n 'if n not in reg and n not in NEGATIVE_CONTROL_IDS' "$T/a/$CHK" | sed 's/^/    branch gap scan: /'
RA=$(run "$T/a" "$T/a.txt"); say "$T/a.txt"
echo "    rc=$RA   EXPECT rc=0 and gaps=none"
echo
echo "=== ARM B: WRONG INPUT -- an UNDECLARED hole (97's definition deleted) ========"
mat "$BR" "$T/b"
python3 - "$T/b/.softhouse/patterns.md" <<'PY'
import sys, re
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().split("\n")
out, killed = [], 0
DEFN = re.compile(r'^(?:[-*>]\s+)?\*\*P-97\s*[.·—–-]\s+')
for l in lines:
    if DEFN.match(l) and killed == 0:
        killed += 1
        out.append("**DEFINITION OF 97 REMOVED BY T414'S RED DRIVE -- citations left in place.**")
        continue
    out.append(l)
open(p, "w", encoding="utf-8").write("\n".join(out))
print("    deleted definition lines for 97:", killed)
assert killed == 1, "RED drive is VOID -- no definition found to delete"
PY
[ $? -eq 0 ] || { echo "    ARM B setup FAILED -- void"; exit 2; }
seal "$T/b"
RB=$(run "$T/b" "$T/b.txt"); say "$T/b.txt"
echo "    rc=$RB   EXPECT rc=1 and FATAL REGISTER GAP 97 -- 97 is NOT a declared control"
echo
echo "=== ARM C: CONTROL ON THE FIX -- exemption neutralised in a throwaway copy ====="
mat "$BR" "$T/c"
python3 - "$T/c/$CHK" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "if n not in reg and n not in NEGATIVE_CONTROL_IDS]"
new = "if n not in reg]"
assert old in s, "exemption line not found -- this control is VOID"
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("    exemption neutralised in the COPY only")
PY
[ $? -eq 0 ] || { echo "    ARM C setup FAILED -- void"; exit 2; }
seal "$T/c"
RC=$(run "$T/c" "$T/c.txt"); say "$T/c.txt"
echo "    rc=$RC   EXPECT rc=1 and FATAL REGISTER GAP on the reserved id -- exemption is load-bearing"
echo
echo "=== SELFTEST on the branch checker ============================================"
( cd "$T/a" && python3 "$CHK" --selftest ) > "$T/st.txt" 2>&1; RST=$?
tail -3 "$T/st.txt" | sed 's/^/    /'
echo "    rc=$RST   EXPECT rc=0 SELFTEST: PASS"
echo
echo '################ SUMMARY #####################################################'
printf '  ARM 0-CTL  main, register tops out at 98    rc=%s  (want 0)\n' "$R0C"
printf '  ARM 0-FAT  main + one pattern at 100        rc=%s  (want 1, GAP on reserved id)\n' "$R0F"
printf '  ARM A      branch as landed                 rc=%s  (want 0)\n' "$RA"
printf '  ARM B      undeclared hole at 97            rc=%s  (want 1, GAP 97)\n' "$RB"
printf '  ARM C      exemption removed                rc=%s  (want 1, GAP on reserved id)\n' "$RC"
printf '  SELFTEST                                    rc=%s  (want 0)\n' "$RST"
if [ "$R0C" = 0 ] && [ "$R0F" = 1 ] && [ "$RA" = 0 ] && [ "$RB" = 1 ] && [ "$RC" = 1 ] && [ "$RST" = 0 ]; then
  echo '  >>> ALL SIX AS EXPECTED. The latent fatal is REAL on pre-T398 main, and the'
  echo '  >>> exemption is load-bearing (C) and narrow (B).'
  exit 0
fi
echo '  >>> NOT AS EXPECTED.'
exit 1
