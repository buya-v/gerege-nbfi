#!/bin/bash
# T155 probe (v) — re-census the store on CURRENT main (T154's numbers were
# taken at fork point 187e972, and main has promoted a parity vector since),
# and drive the M-5 allowlist correction empirically.
set -u
PRE=/tmp/t155/pre
POST=/tmp/t155/post
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

census() { # $1 tree, $2 label
  local V="$1/.softhouse/vectors"
  echo "---- $2 ($V) ----"
  local all root ls_n self_n other
  all=$(find "$V" -name '*.json' -type f | wc -l | tr -d ' ')
  root=$(find "$V" -maxdepth 1 -name '*.json' -type f | wc -l | tr -d ' ')
  ls_n=$(find "$V/loanschedule" -name '*.json' -type f 2>/dev/null | wc -l | tr -d ' ')
  self_n=$(find "$V/_selftest" -name '*.json' -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "  .json under the store root (find -type f)   : $all"
  echo "  at the store root itself                    : $root   -> $(find "$V" -maxdepth 1 -name '*.json' -type f -exec basename {} \; | sort | tr '\n' ' ')"
  echo "  loanschedule/                               : $ls_n"
  echo "  _selftest/                                  : $self_n"
  echo "  vector files (= all - root)                 : $((all - root))"
  echo "  arithmetic closes?                          : $([ $((root + ls_n + self_n)) -eq "$all" ] && echo yes || echo 'NO — files exist somewhere else')"
  echo "  class counts from the files themselves:"
  for cls in parity contract-refusal self-test; do
    printf '    %-18s %s\n' "$cls" "$(LC_ALL=C grep -al "\"class\": \"$cls\"" $(find "$V" -name '*.json' -type f) 2>/dev/null | wc -l | tr -d ' ')"
  done
  echo "  non-ASCII case_id?                          : $(LC_ALL=C grep -alE '"case_id": "[^"]*[^A-Za-z0-9._"-]' $(find "$V" -name '*.json' -type f) 2>/dev/null | wc -l | tr -d ' ') files"
}
census "$PRE"  "PRE  = fork point 187e972 (what T154 censused)"
echo
census "$POST" "POST = scratch merge of T154 into CURRENT main"
echo

echo "================================================================"
echo "M-5 corollary: is the two-name allowlist itself float-checked?"
echo "T154 corrected M-5 to 'true only OFF the allowlist, since LoadPin and"
echo "LoadCapabilityRegistry already call RejectFloatTokens'. Driven here."
echo "================================================================"
( cd "$PRE/nexus" && go build -o /tmp/t155/bin-pre ./internal/apps/loanschedule/conformance/cmd/conformance ) || exit 9
V="$PRE/.softhouse/vectors"
for target in PIN.json capabilities.json; do
  cp "$V/$target" "/tmp/t155/$target.bak"
  # inject a float that is NOT hidden behind an invalid byte, so the only
  # question is whether the GO side checks this file at all.
  perl -0pi -e 's/\{/\{\n  "t155_float_probe": 3.6,/' "$V/$target"
  out=$( cd "$PRE" && /tmp/t155/bin-pre -oracle-probe=up 2>&1 ); rc=$?
  echo "  float injected into $target -> PRE binary exit=$rc"
  printf '%s\n' "$out" | LC_ALL=C grep -aiE 'store pin|capability registry|not an integer|float' | head -2 | sed 's/^/      /'
  cp "/tmp/t155/$target.bak" "$V/$target"
done
echo
echo "  control: allowlist restored ->"
out=$( cd "$PRE" && /tmp/t155/bin-pre -oracle-probe=up 2>&1 ); rc=$?
echo "      exit=$rc  $(printf '%s' "$out" | LC_ALL=C grep -a '^VERDICT' | head -1 | cut -c1-70)"
