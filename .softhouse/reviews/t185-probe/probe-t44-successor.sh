# T185 INDEPENDENT RED PROBE of t44_float_roundtrip_v2.py -- scratch corpora only, repo untouched.
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac71271ab074115ac
SUCC="$W/.softhouse/capture/audit-t44/analysis/t44_float_roundtrip_v2.py"
S=$(mktemp -d); trap 'rm -rf "$S"' EXIT
rc=0
ck(){ if [ "$2" = "$3" ]; then echo "  AS PREDICTED   $1: $3"; else echo "  *** NOT AS PREDICTED  $1: expected $2 got $3"; rc=1; fi; }

echo "######## A1 -- a VALUE-LOSSY literal planted. Does the detector FIRE, and does it FAIL?"
mkdir -p "$S/a1"
printf '{"amount": 0.1234567890123456789, "other": 1.5}\n' > "$S/a1/lossy.json"
python3 "$SUCC" "$S/a1/*.json" > "$S/a1.txt" 2>&1; e=$?
echo "  exit=$e"
echo "  --- detector lines:"
/usr/bin/grep -E 'VALUE != the decimal|VALUE-lossy|SUCCESSOR:' "$S/a1.txt" | sed 's/^/    /'
nlossy=$(sed -n 's/.*literals whose float VALUE != the decimal *: *\([0-9]*\).*/\1/p' "$S/a1.txt")
ck "VALUE-lossy literals DETECTED (detector not vacuous)" "1" "$nlossy"
ck "exit status when a money literal IS value-corrupted" "1" "$e"

echo
echo "######## A2 -- valid JSON, ZERO bare float literals (P-35 empty-sample)"
mkdir -p "$S/a2"; printf '{"amount": "1250000.00"}\n' > "$S/a2/strings.json"
python3 "$SUCC" "$S/a2/*.json" > "$S/a2.txt" 2>&1; e=$?
ck "exit on parsed-but-zero-literals" "1" "$e"

echo
echo "######## A3 -- an UNREADABLE file (chmod 000): swallowed, or named?"
mkdir -p "$S/a3"; printf '{"a": 1.5}\n' > "$S/a3/ok.json"; printf '{"b": 2.5}\n' > "$S/a3/locked.json"; chmod 000 "$S/a3/locked.json"
python3 "$SUCC" "$S/a3/*.json" > "$S/a3.txt" 2>&1; e=$?
ck "exit with 1 unreadable file present" "1" "$e"
ck "unreadable file NAMED in skip register" "1" "$(/usr/bin/grep -c 'UNSCANNED.*locked.json' "$S/a3.txt")"
/usr/bin/grep -A1 'UNSCANNED' "$S/a3.txt" | head -2 | sed 's/^/    /'
chmod 644 "$S/a3/locked.json"

echo
echo "######## A4 -- a DIRECTORY matching the glob"
mkdir -p "$S/a4/adir.json"; printf '{"a": 1.5}\n' > "$S/a4/ok.json"
python3 "$SUCC" "$S/a4/*.json" > "$S/a4.txt" 2>&1; e=$?
ck "exit with a directory in the glob" "1" "$e"
ck "directory NAMED" "1" "$(/usr/bin/grep -c 'UNSCANNED.*adir.json' "$S/a4.txt")"

echo
echo "######## A5 -- BINARY / UTF-16 file"
mkdir -p "$S/a5"; printf '{"a": 1.5}\n' > "$S/a5/ok.json"
python3 -c "open('$S/a5/utf16.json','wb').write('{\"b\": 2.5}'.encode('utf-16'))"
python3 "$SUCC" "$S/a5/*.json" > "$S/a5.txt" 2>&1; e=$?
ck "exit with a UTF-16 file" "1" "$e"
/usr/bin/grep -A1 'UNSCANNED' "$S/a5.txt" | head -2 | sed 's/^/    /'

echo; echo "######## RESULT"; [ $rc -eq 0 ] && echo "  ALL AS PREDICTED" || echo "  DIVERGENCE FOUND"
exit $rc
