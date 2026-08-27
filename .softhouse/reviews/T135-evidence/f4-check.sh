#!/bin/sh
# T135 — independent F-4 drive. Tamper cases of my own against a throwaway export of the branch.
# NOTE: run this from OUTSIDE /tmp/t135/f4 — it wipes that directory on entry.
set -u
B=/tmp/t135/f4/tree
rm -rf /tmp/t135/f4 && mkdir -p /tmp/t135/f4
git -C /tmp/t135/clone archive t99 .softhouse/capture/pathb | tar -x -C /tmp/t135/f4
mv /tmp/t135/f4/.softhouse/capture/pathb "$B"
P="python3 $B/provenance.py"

run() { lbl=$1; o=$($P verify --root "$B" 2>&1); st=$?; \
  printf '  %-52s exit=%s  %s\n' "$lbl" "$st" "$(printf '%s\n' "$o" | grep -E '^(directories|files|problems)' | tr '\n' ' ')"; \
  printf '%s\n' "$o" | grep -E '^  (MISSING|BYTES|STAMP|UNACCOUNTED)' | sed 's/^/       /'; }

echo "--- 4g baseline: the untampered committed tree"
run "untampered"

echo; echo "--- C1  one byte changed inside a committed capture"
f=$(ls "$B"/t36/out/recapture-gerege/*-raw.json | head -1)
cp "$f" /tmp/t135/f4/save1; printf ' ' >> "$f"
run "one byte appended to $(basename "$f")"; cp /tmp/t135/f4/save1 "$f"

echo; echo "--- C2  a stamp DELETED from a stamped directory"
s=$B/t80/out/recapture-gerege/CAPTURED-FROM-TENANT
cp "$s" /tmp/t135/f4/save2; rm -f "$s"
run "stamp removed from t80/out/recapture-gerege"; cp /tmp/t135/f4/save2 "$s"

echo; echo "--- C3  a stamp FORGED onto the unstamped t36/out/recapture-gerege"
s2=$B/t36/out/recapture-gerege/CAPTURED-FROM-TENANT
printf 'gerege\n' > "$s2"; run "stamp forged onto t36/out/recapture-gerege"; rm -f "$s2"

echo; echo "--- C4  a whole smuggled capture directory appears"
mkdir -p "$B/t36/out/smuggled-gerege"; printf '{"x":1}\n' > "$B/t36/out/smuggled-gerege/S-01-raw.json"
run "smuggled directory"; rm -rf "$B/t36/out/smuggled-gerege"

echo; echo "--- C5  a committed capture FILE deleted"
cp "$f" /tmp/t135/f4/save5; rm -f "$f"; run "capture file removed"; cp /tmp/t135/f4/save5 "$f"

echo; echo "--- C6  the INDEX itself deleted (verify must not pass by not running)"
cp "$B/PROVENANCE-INDEX.json" /tmp/t135/f4/save6; rm -f "$B/PROVENANCE-INDEX.json"
run "no index"; cp /tmp/t135/f4/save6 "$B/PROVENANCE-INDEX.json"

echo; echo "--- C7  the index EMPTIED of all directory records"
python3 - "$B" <<'EOF'
import json,sys,os
p=os.path.join(sys.argv[1],'PROVENANCE-INDEX.json')
i=json.load(open(p)); i['directories']=[]
json.dump(i,open(p,'w'),indent=1)
EOF
run "index with zero directory records"; cp /tmp/t135/f4/save6 "$B/PROVENANCE-INDEX.json"

echo; echo "--- C8  verify against an EMPTY tree"
mkdir -p /tmp/t135/f4/empty; cp "$B/PROVENANCE-INDEX.json" /tmp/t135/f4/empty/
o=$(python3 "$B/provenance.py" verify --root /tmp/t135/f4/empty 2>&1); st=$?
printf '  %-52s exit=%s\n' "empty tree, index present" "$st"
printf '%s\n' "$o" | grep -E '^(directories|files|problems)|ERROR' | sed 's/^/       /'

echo; echo "--- restored?"; run "restored tree"
