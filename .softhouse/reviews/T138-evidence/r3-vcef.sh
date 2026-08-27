#!/bin/sh
# T138 — independent reproduction of V-C, V-E, V-F and V-G.
set -u
W=${1:?workdir}
PRE=$W/pre/.softhouse/capture/t91
POST=$W/post/.softhouse/capture/t91
CANON=$W/post/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json

echo "###################################################################### V-C"
echo "sed that does not match is a COPY.  Reformat the canonical request and see"
echo "what the PRE-fix run-attacks.sh would have fired at the rig."
echo
echo "canonical request principal line:"
LC_ALL=C grep -a principal "$CANON" | sed 's/^/   /'
echo "canonical sha256: $(shasum -a 256 "$CANON" | cut -d' ' -f1)"
rm -rf "$W/vc"; mkdir -p "$W/vc"
LC_ALL=C sed 's/"principal": 1162502.5,/"principal": 1162502.50,/' "$CANON" > "$W/vc/canon-reformatted.json"
echo "reformatted (1162502.5 -> 1162502.50) sha256: $(shasum -a 256 "$W/vc/canon-reformatted.json" | cut -d' ' -f1)"
echo "the two committed T91 mutations applied to the REFORMATTED canon:"
sed 's/"principal": 1162502.5,/"principal": 1162502.55,/' "$W/vc/canon-reformatted.json" > "$W/vc/req-mutated-55.json"
sed 's/"principal": 1162502.5,/"principal": 1162502.4,/'  "$W/vc/canon-reformatted.json" > "$W/vc/req-crafted-04.json"
for f in req-mutated-55 req-crafted-04; do
  if cmp -s "$W/vc/$f.json" "$W/vc/canon-reformatted.json"; then
    echo "   $f.json is BYTE-IDENTICAL to the (reformatted) canon — the 'attack' is a copy"
  else
    echo "   $f.json differs — the mutation took"
  fi
  echo "      principal now: $(LC_ALL=C grep -a principal "$W/vc/$f.json" | tr -d ' ')"
done
echo
echo "-- and: is the reformatted canon still the SAME NUMBER but a DIFFERENT digest?"
python3 - "$CANON" "$W/vc/canon-reformatted.json" <<'PY'
import json,sys,decimal
a=json.load(open(sys.argv[1]),parse_float=decimal.Decimal)
b=json.load(open(sys.argv[2]),parse_float=decimal.Decimal)
print("   principal canon      :", a["principal"])
print("   principal reformatted:", b["principal"])
print("   numerically equal    :", a["principal"]==b["principal"])
print("   (decimal, not float — P-25)")
PY
echo
echo "-- POST-fix run-attacks.sh assert_mutated on that input (G-6's red leg, run standalone):"
echo "   see R4-GUARDS.txt, leg G-6."
echo

echo "###################################################################### V-E"
echo "shell-invariance.sh compared ONE SIDE's file list."
rm -rf "$W/ve"; mkdir -p "$W/ve/z-sh" "$W/ve/z-bash"
printf 'header\nEXIT=0\n' > "$W/ve/z-sh/A1.txt"
printf 'header\nEXIT=0\n' > "$W/ve/z-bash/A1.txt"
printf 'TOTALLY DIFFERENT CONTENT\nALL PRECONDITIONS HOLD\nEXIT=0\n' > "$W/ve/z-bash/A2.txt"
echo "-- PRE-fix:"
sh "$PRE/shell-invariance.sh" "$W/ve" z; echo "   PRE_EXIT=$?"
echo "-- POST-fix (same directory):"
sh "$POST/shell-invariance.sh" "$W/ve" z; echo "   POST_EXIT=$?"
echo
echo "-- reversed: sh-only transcript (the case the PRE-fix loop DID cover)"
rm -rf "$W/ve2"; mkdir -p "$W/ve2/z-sh" "$W/ve2/z-bash"
printf 'header\nEXIT=0\n' > "$W/ve2/z-sh/A1.txt"
printf 'header\nEXIT=0\n' > "$W/ve2/z-bash/A1.txt"
printf 'X\nEXIT=0\n' > "$W/ve2/z-sh/A2.txt"
sh "$PRE/shell-invariance.sh" "$W/ve2" z; echo "   PRE_EXIT=$?"
echo

echo "###################################################################### V-F"
echo "scratch .inv-a/.inv-b written INTO the audited directory \$O."
rm -rf "$W/vf"; mkdir -p "$W/vf/z-sh" "$W/vf/z-bash"
printf 'AAA\nEXIT=0\n' > "$W/vf/z-sh/A1.txt"
printf 'BBB DIFFERENT\nEXIT=1\n' > "$W/vf/z-bash/A1.txt"
echo "-- control: writable \$O, PRE-fix — the difference IS caught"
sh "$PRE/shell-invariance.sh" "$W/vf" z; echo "   PRE_EXIT=$?"
echo
echo "-- now plant identical stale scratch and make \$O read-only:"
printf 'STALE\n' > "$W/vf/.inv-a"; printf 'STALE\n' > "$W/vf/.inv-b"
chmod 555 "$W/vf"
sh "$PRE/shell-invariance.sh" "$W/vf" z 2>&1; echo "   PRE_EXIT=$?"
echo "-- POST-fix on the very same read-only \$O:"
sh "$POST/shell-invariance.sh" "$W/vf" z 2>&1; echo "   POST_EXIT=$?"
chmod 755 "$W/vf"
echo

echo "###################################################################### V-G"
echo "two skip-branches that returned success, in the PRE-fix prove-guards.sh"
echo "-- the G-4 skip branch, pre-fix source:"
LC_ALL=C grep -n -A3 'poison' "$PRE/prove-guards.sh" | sed -n '1,20p' | sed 's/^/   /'
echo "-- the ugrep else-branch, pre-fix source:"
LC_ALL=C sed -n '/command -v ugrep/,/^fi/p' "$PRE/prove-guards.sh" | sed 's/^/   /'
echo "-- post-fix G-4 skip branch:"
LC_ALL=C sed -n '/no committed pre-fix transcripts to poison/,+2p' "$POST/prove-guards.sh" | sed 's/^/   /'
echo "-- post-fix ugrep else-branch:"
LC_ALL=C sed -n '/ugrep is NOT on PATH/,/^fi/p' "$POST/prove-guards.sh" | sed 's/^/   /'
echo "-- is ugrep on PATH from INSIDE a script (P-33)?"
command -v ugrep >/dev/null 2>&1 && echo "   yes: $(command -v ugrep)" || echo "   no — the else-branch is the one that runs here"
echo "-- pre-fix script's final statement:"
tail -3 "$PRE/prove-guards.sh" | sed 's/^/   /'
