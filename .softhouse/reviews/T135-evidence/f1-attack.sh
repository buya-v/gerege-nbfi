#!/bin/sh
# T135 — independent F-1 attack: bypass shapes T99b's table does NOT contain.
# Hermetic: docker and curl are stubbed to refuse, so the shared reference oracle is untouched.
# The output-path guard runs BEFORE any of them, so ADMITTED/REFUSED is decided purely by the guard.
set -u
SIDE=$1
SRC=/tmp/t135/f1/$SIDE
W=$SRC/.softhouse/capture/pathb
D=$W/t36

mkdir -p /tmp/t135/f1/bin
printf '#!/bin/sh\necho "STUB: refusing (T135 hermetic F-1 probe)" >&2\nexit 1\n' > /tmp/t135/f1/bin/docker
cp /tmp/t135/f1/bin/docker /tmp/t135/f1/bin/curl
chmod +x /tmp/t135/f1/bin/docker /tmp/t135/f1/bin/curl

# fixtures the attacks need
mkdir -p "$D/out/recapture-default"
[ -f "$D/out/recapture-default/CAPTURED-FROM-TENANT" ] || printf 'default\n' > "$D/out/recapture-default/CAPTURED-FROM-TENANT"
rm -f "$D/out/midlink"; ln -s recapture-default "$D/out/midlink"
mkdir -p /tmp/t135/f1/outside-$SIDE/out
rm -f "$W/evil-task"; ln -s /tmp/t135/f1/outside-$SIDE "$W/evil-task"

try() {                       # try <cwd> <label> <RECAPTURE_OUT>
  cwd=$1; label=$2; out=$3
  o=$(cd "$cwd" && RECAPTURE_OUT="$out" TENANT=gerege PATH=/tmp/t135/f1/bin:$PATH \
        sh "$D/recapture.sh" 2>&1)
  case "$o" in
    *"ABORT: output directory"*|*"cannot be resolved"*|*"ABORT: cannot resolve"*) v=REFUSED ;;
    *"### tenant 'gerege'  ->  output directory"*)      v="ADMITTED" ;;
    *)                                                   v="OTHER: $(printf '%s' "$o" | head -1)" ;;
  esac
  printf '  %-7s  %-58s  %s\n' "$SIDE" "$label" "$v"
}

try "$D" 'A1  dot component through an existing dir'    "$D/out/./recapture-default/sub-gerege"
try "$D" 'A2  doubled slashes'                          "$D/out//recapture-default//sub-gerege"
try "$D" 'A3  middle component in the WRONG CASE (OUT)' "$D/OUT/case-gerege"
try "$D" 'A4  symlink at the MIDDLE component'          "$D/out/midlink/sub-gerege"
try "$D" 'A5  task dir is a symlink OUT of the tree'    "$W/evil-task/out/x-gerege"
try "$D/out" 'A6  RELATIVE path, cwd = t36/out'         "recapture-default/rel-gerege"
try "$D" 'A7  out/ repeated: t36/out/out/x-gerege'      "$D/out/out/x-gerege"
try "$D" 'A8  leaf is BARE TENANT one level down'       "$D/out/recapture-default/gerege"
try "$D" 'A9  trailing /. on the nested attack'         "$D/out/recapture-default/sub-gerege/."
try "$D" 'HAPPY t36/out/recapture-gerege'               "$D/out/recapture-gerege"
try "$D" 'HAPPY t36/out/gerege (bare tenant leaf)'      "$D/out/gerege"
