#!/bin/bash
# T155 probe (vii) — attacks T154 did NOT claim to have driven, aimed at the new
# census's own seams. Every fixture is float-free unless the row says otherwise,
# so the shell guard cannot be the thing that refuses.
set -u
POST=/tmp/t155/post
OUTD=/tmp/t155/out
mkdir -p "$OUTD"
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
( cd "$POST/nexus" && go build -o /tmp/t155/bin-post ./internal/apps/loanschedule/conformance/cmd/conformance ) || exit 9
V="$POST/.softhouse/vectors"

run() { # $1 label, $2.. extra binary args
  local label="$1"; shift
  local out="$OUTD/vii-$label.txt" rc
  ( cd "$POST" && /tmp/t155/bin-post -oracle-probe=up "$@" ) > "$out" 2>&1
  rc=$?
  local msg; msg="$(LC_ALL=C grep -aE 'STORE FILE CENSUS|CASE_ID INTEGRITY|DUPLICATE|could not be|load error|LOAD' "$out" | head -1 | sed 's/^ *//' | cut -c1-130)"
  printf '  exit=%-3s %s\n' "$rc" "${msg:-<no refusal line>}"
  printf '           %s\n' "$(LC_ALL=C grep -a '^VERDICT' "$out" | head -1 | cut -c1-72)"
}

echo "control (unmutated, binary only):"; run ctl
echo

echo "V1  malformed .json INSIDE a context dir, NO float"
printf 'this is not json at all\n' > "$V/T155-V1.json.tmp"; mv "$V/T155-V1.json.tmp" "$V/loanschedule/T155-V1.json"
run V1; rm -f "$V/loanschedule/T155-V1.json"
echo

echo "V2  HARD LINK of a committed vector, new name, inside the context dir"
ln "$V/loanschedule/P-00-baseline-6x7pct.json" "$V/loanschedule/T155-V2-hardlink.json" 2>/dev/null || echo "  (hard link unsupported here)"
run V2; rm -f "$V/loanschedule/T155-V2-hardlink.json"
echo

echo "V3  HARD LINK of a committed vector, placed at the STORE ROOT"
ln "$V/loanschedule/P-00-baseline-6x7pct.json" "$V/T155-V3-hardlink.json" 2>/dev/null || echo "  (hard link unsupported here)"
run V3; rm -f "$V/T155-V3-hardlink.json"
echo

echo "V4  a HIDDEN top-level context directory holding a clean vector"
mkdir -p "$V/.hidden"
sed 's/"case_id": "P-00"/"case_id": "T155-HIDDEN"/' "$V/loanschedule/P-00-baseline-6x7pct.json" > "$V/.hidden/T155-HIDDEN.json"
run V4; rm -rf "$V/.hidden"
echo

echo "V5  the same store-root plant, but under a CONTEXT FILTER (-context=_selftest)"
echo "    (T123's rule: the filter narrows what is GRADED, never what is CHECKED)"
printf '{ "note": "planted", "amount": "1250000" }\n' > "$V/T155-V5.json"
run V5 -context=_selftest; rm -f "$V/T155-V5.json"
echo

echo "V6  a DIRECTORY named like a vector: loanschedule/T155-V6.json/"
mkdir -p "$V/loanschedule/T155-V6.json"
run V6; rm -rf "$V/loanschedule/T155-V6.json"
echo

echo "V7  a second copy of a vector with a DIFFERENT case_id (legitimate shape — must still PASS)"
sed 's/"case_id": "P-00"/"case_id": "T155-V7"/' "$V/loanschedule/P-00-baseline-6x7pct.json" > "$V/loanschedule/T155-V7.json"
run V7; rm -f "$V/loanschedule/T155-V7.json"
echo "    ^ ANTI-VACUITY ROW: if this one refuses too, the census refuses everything and proves nothing."
echo

echo "leftovers?"; find "$V" -name '*T155*' -o -name '.hidden' -o -type l | sed 's/^/  LEFTOVER /'
