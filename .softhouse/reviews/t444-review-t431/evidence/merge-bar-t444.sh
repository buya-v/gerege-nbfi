#!/bin/bash
# T444 — build the MERGE RESULT of today's main with T431, then run the full bar on it.
# Work root is an ARGUMENT. Source repo is an ARGUMENT.
set -u
W="$1"; SRC="$2"
[ -n "$W" ] && [ -n "$SRC" ] || { echo "usage: merge-bar.sh <workroot> <srcrepo>"; exit 9; }
if [ -e "$W" ]; then echo "work root $W exists; refusing to reuse"; exit 2; fi
mkdir -p "$W" || exit 2
git clone --no-hardlinks -q "$SRC" "$W/m" >/dev/null 2>&1 || { echo "clone failed"; exit 2; }
cd "$W/m" || exit 2
git checkout -q main || { echo "checkout main failed"; exit 2; }
echo "=== main HEAD ==="
git log --oneline -1
echo "=== merging T431 ==="
git -c user.email=t444@x -c user.name=t444 merge --no-edit origin/softhouse/T431-t407-conditions
echo "merge rc=$?"
echo "=== conflicts? ==="
git ls-files -u | head -20
echo "(none above means clean)"
echo "=== status ==="
git status --porcelain | head -20
echo "=== EXEMPTION_PIN_LEDGER_WRONGIMPLS in merge result ==="
grep -n '^EXEMPTION_PIN_LEDGER_WRONGIMPLS=' .softhouse/conformance.sh
echo "=== the three fix lines present in merge result ==="
grep -cF 'git ls-files -s -- ":(literal)$self_norm" 2>/dev/null' .softhouse/conformance.sh
grep -cF 'elif [ -z "$self_stat" ]; then' .softhouse/conformance.sh
grep -cF 'elif [ "$self_path" != "$self_norm" ]; then' .softhouse/conformance.sh
echo "=== patterns.md:3426 citation resolves in merge result? ==="
sed -n '3426p' .softhouse/patterns.md
sed -n '3271p' .softhouse/conformance.sh
echo "=== BAR: bash .softhouse/conformance.sh ==="
bash .softhouse/conformance.sh > "$W/merge-bar.out" 2>&1
echo "EXIT=$?"
echo "--- P-84: probe line PRESENCE first ---"
grep -c 'probe = ' "$W/merge-bar.out"
echo "--- then its value ---"
grep 'probe = ' "$W/merge-bar.out"
echo "--- VERDICT ---"
grep -E 'VERDICT' "$W/merge-bar.out"
echo "--- wrong ledger implementations ---"
grep -iE 'wrong ledger|WRONGIMPLS|wrong-impl' "$W/merge-bar.out"
echo "--- guards-dir census ---"
grep -E 'GUARDS-DIR-REGISTRATION: population' "$W/merge-bar.out"
echo "--- dead-path frontier ---"
grep -E 'T316-DEADPATH-FRONTIER' "$W/merge-bar.out"
echo "--- host-state census ---"
grep -A2 'CENSUS host state' "$W/merge-bar.out"
echo "--- fail-open frontier ---"
grep -iE 'fail-open frontier|FAILOPEN' "$W/merge-bar.out" | head -5
echo "--- tree clean after run? ---"
git status --porcelain | head
echo "=== full transcript at $W/merge-bar.out ==="
