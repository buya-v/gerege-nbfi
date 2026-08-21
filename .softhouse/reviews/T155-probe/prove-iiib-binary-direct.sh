#!/bin/bash
# T155 probe (iii-b) — is the STORE-ROOT hole closed BY THE CENSUS, or only by
# the shell grep that happens to run first?
#
# conformance.sh runs run_guards BEFORE the binary, so a float-carrying store-root
# file is refused by the shell guard and the census is never consulted. This probe
# takes the shell out of the circuit entirely and runs the harness BINARY.
#
# The `-oracle-probe=up` value here is ASSERTED by this probe, not measured — its
# only purpose is to stop the binary short-circuiting on reachability so the Go
# store-load path is actually exercised. Reachability was separately MEASURED as
# `probe = up` in the full conformance runs of probe (ii)/(iii).
set -u
PRE=/tmp/t155/pre
POST=/tmp/t155/post
OUTD=/tmp/t155/out
mkdir -p "$OUTD"
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

build() { # $1 tree, $2 out
  ( cd "$1/nexus" && go build -o "$2" ./internal/apps/loanschedule/conformance/cmd/conformance ) || { echo "REFUSE: build failed for $1"; exit 9; }
}
build "$PRE"  /tmp/t155/bin-pre
build "$POST" /tmp/t155/bin-post

runbin() { # $1 tree, $2 bin, $3 label
  local out="$OUTD/iiib-$3.txt" rc
  ( cd "$1" && "$2" -oracle-probe=up ) > "$out" 2>&1
  rc=$?
  local msg; msg="$(LC_ALL=C grep -aE 'STORE FILE CENSUS|CASE_ID INTEGRITY' "$out" | head -1 | sed 's/^ *//' | cut -c1-120)"
  local verdict; verdict="$(LC_ALL=C grep -a '^VERDICT' "$out" | head -1 | cut -c1-70)"
  printf '  exit=%-3s %s\n  %s\n' "$rc" "${verdict:-<no VERDICT>}" "${msg:-<no census/case_id line>}"
}

for ARM in PRE POST; do
  tree=$PRE; bin=/tmp/t155/bin-pre
  [ "$ARM" = POST ] && { tree=$POST; bin=/tmp/t155/bin-post; }
  V="$tree/.softhouse/vectors"
  echo "=================== ARM $ARM (binary only, no shell guards) ==================="

  echo "[control] unmutated store"
  runbin "$tree" "$bin" "$ARM-ctl"

  echo "[B1] store-root .json with NO float at all"
  printf '{ "note": "planted", "amount": "1250000" }\n' > "$V/T155-B1.json"
  runbin "$tree" "$bin" "$ARM-B1"
  rm -f "$V/T155-B1.json"

  echo "[B2] store-root .json, float behind ONE invalid byte (invisible to the pre-fix shell grep)"
  printf '{\n  "note": "x", \xe2 "rate_pct": 3.6\n}\n' > "$V/T155-B2.json"
  runbin "$tree" "$bin" "$ARM-B2"
  rm -f "$V/T155-B2.json"

  echo "[B3] store-root .json with a PLAIN float (the shell grep would have caught this one)"
  printf '{\n  "rate_pct": 3.6\n}\n' > "$V/T155-B3.json"
  runbin "$tree" "$bin" "$ARM-B3"
  rm -f "$V/T155-B3.json"
  echo
done
