#!/bin/sh
# T163 — drive census-json-float-siblings.py RED four ways, on scratch copies.
RIG="$1"
SB=/tmp/t163-sabotage-run
rm -rf "$SB"; mkdir -p "$SB"
cp "$RIG"/*.py "$SB/"; cp "$RIG"/*.sh "$SB/"; cp "$RIG"/SUPERSEDED.txt "$SB/"

echo "############################################################################"
echo "# P-22 — the census must be FALSIFIABLE.  Four sabotages, each on a scratch"
echo "# copy in $SB.  The committed rig is never touched."
echo "############################################################################"
echo
echo "=== SABOTAGE 0 (control): the rig as committed, unmodified ==="
( cd "$SB" && python3 census-json-float-siblings.py 2>&1 | tail -14 )
echo "   exit=$( cd "$SB" && python3 census-json-float-siblings.py >/dev/null 2>&1; echo $? )"
echo

echo "=== SABOTAGE 1: delete the resolve7.py -> resolve8.py redirect ==="
grep -v '^resolve7.py ->' "$RIG/SUPERSEDED.txt" > "$SB/SUPERSEDED.txt"
( cd "$SB" && python3 census-json-float-siblings.py 2>&1 | grep -A2 'EVERY WIRE WRITER' )
echo "   exit=$( cd "$SB" && python3 census-json-float-siblings.py >/dev/null 2>&1; echo $? )"
echo

echo "=== SABOTAGE 2: point the redirect at a DIRTY replacement (resolve7.py itself) ==="
sed 's|^resolve7.py -> resolve8.py|resolve7.py -> resolve7.py|' "$RIG/SUPERSEDED.txt" > "$SB/SUPERSEDED.txt"
( cd "$SB" && python3 census-json-float-siblings.py 2>&1 | grep -A2 'EVERY REDIRECT' )
echo "   exit=$( cd "$SB" && python3 census-json-float-siblings.py >/dev/null 2>&1; echo $? )"
echo

echo "=== SABOTAGE 3: point the redirect at a replacement that does NOT EXIST ==="
sed 's|^resolve7.py -> resolve8.py|resolve7.py -> resolve99.py|' "$RIG/SUPERSEDED.txt" > "$SB/SUPERSEDED.txt"
( cd "$SB" && python3 census-json-float-siblings.py 2>&1 | grep -A2 'EVERY REDIRECT' )
echo "   exit=$( cd "$SB" && python3 census-json-float-siblings.py >/dev/null 2>&1; echo $? )"
echo

echo "=== SABOTAGE 4: drop in a NEW, UNCLASSIFIED req/-writing script carrying a FLOAT ==="
cp "$RIG/SUPERSEDED.txt" "$SB/SUPERSEDED.txt"
printf 'import json\nP = "req/new-body.json"\njson.dump({"principal": 1200000.00}, open(P, "w"))\n' > "$SB/mkreq9.py"
( cd "$SB" && python3 census-json-float-siblings.py 2>&1 | grep -A2 'EVERY MECHANICAL CANDIDATE\|R5) — scope' )
echo "   exit=$( cd "$SB" && python3 census-json-float-siblings.py >/dev/null 2>&1; echo $? )"
echo
echo "NOTE ON SABOTAGE 4, recorded because it CHANGED THE FIX.  The first version of R5"
echo "scoped itself to WIRE writers only, so this sabotage left it printing"
echo '"0 float literal(s) in WIRE writers" -- true, and useless, because mkreq9.py was'
echo "not classified as WIRE yet.  Two guards each relying on the other having run first"
echo "is the P-36 shape.  R5's scope is now WIRE plus every UNCLASSIFIED candidate, and"
echo "both guards fire independently above."
rm -rf "$SB"
