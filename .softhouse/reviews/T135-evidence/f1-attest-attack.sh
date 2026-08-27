#!/bin/sh
set -u
SIDE=$1
W=/tmp/t135/f1/$SIDE/.softhouse/capture/pathb
D=$W/t36
mkdir -p "$D/out/recapture-default"
[ -f "$D/out/recapture-default/CAPTURED-FROM-TENANT" ] || printf 'default\n' > "$D/out/recapture-default/CAPTURED-FROM-TENANT"
rm -f "$D/out/midlink"; ln -s recapture-default "$D/out/midlink"
mkdir -p /tmp/t135/f1/outside-$SIDE/out
rm -f "$W/evil-task"; ln -s /tmp/t135/f1/outside-$SIDE "$W/evil-task"

try() {
  label=$1; out=$2; set2=${3:-pathb}
  o=$(cd "$D" && ATTEST_OUT="$out" PATH=/tmp/t135/f1/bin:$PATH python3 "$D/attest.py" gerege "$set2" 2>&1)
  case "$o" in
    *"ABORT: output directory"*) v=REFUSED ;;
    *) v="ADMITTED(past the guard)" ;;
  esac
  printf '  %-7s  %-52s  %s\n' "$SIDE" "$label" "$v"
}
try 'B1  dot component'                    "$D/out/./recapture-default/sub-gerege"
try 'B2  doubled slashes'                  "$D/out//recapture-default//sub-gerege"
try 'B3  symlink at the MIDDLE component'  "$D/out/midlink/sub-gerege"
try 'B4  task dir symlinked OUT of tree'   "$W/evil-task/out/x-gerege"
try 'B5  out/ repeated'                    "$D/out/out/x-gerege"
try 'B6  bare tenant leaf one level down'  "$D/out/recapture-default/gerege"
try 'B7  emiloop set, NESTED'              "$D/out/recapture-default/hidden" emiloop
try 'HAPPY t80/out/attest-gerege'          "$W/t80/out/attest-gerege"
try 'HAPPY emiloop t36/out/emiloop'        "$D/out/emiloop" emiloop
