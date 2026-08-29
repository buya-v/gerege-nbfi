#!/usr/bin/env bash
# T445 probe: WHICH of two case-colliding index entries survives a fresh checkout?
# The DECLARATION-TABLE direction names its witness paths in ALL LOWER CASE, so the
# question is whether an attacker can make a case-variant DECOY win the collision for a
# target that is already all-lowercase. Measured, not reasoned.
#   usage: bash probe-collision-order.sh <workroot>
set -u
W="${1:?workroot}"
mkdir -p "$W"

one() {
  local name_real="$1" name_decoy="$2" tag="$3" R blob
  R="$W/$tag"
  rm -rf "$R"; mkdir -p "$R"
  ( cd "$R" && git init -q . && git config user.email p@example.invalid && git config user.name P )
  printf 'REAL CONTENT\n' > "$R/$name_real"
  ( cd "$R" && git add "$name_real" >/dev/null )
  blob="$( printf 'DECOY CONTENT\n' | ( cd "$R" && git hash-object -w --stdin ) )"
  ( cd "$R" && git update-index --add --cacheinfo "100644,$blob,$name_decoy" )
  ( cd "$R" && git commit -q -m x >/dev/null )
  rm -rf "$W/$tag-clone"
  git clone -q "$R" "$W/$tag-clone" 2>"$W/$tag-clone.warn"
  printf '=== %s : real=%s decoy=%s ===\n' "$tag" "$name_real" "$name_decoy"
  printf 'index:\n'; ( cd "$W/$tag-clone" && git ls-files -s )
  printf 'what a read of the REAL name returns: '
  cat "$W/$tag-clone/$name_real" 2>&1
  printf 'collision warning: '; LC_ALL=C sed -n '1,8p' "$W/$tag-clone.warn"
  printf '\n'
}

# 1. target all-lowercase, decoy upper-cased: can the decoy win?
one 'fire-program.sh' 'Fire-program.sh' lower-target-upper-decoy
one 'fire-program.sh' 'FIRE-PROGRAM.SH' lower-target-shout-decoy
# 2. control: target has an upper-case letter, decoy lower-cases it -> decoy sorts LAST
one 'W.txt' 'w.txt' upper-target-lower-decoy
