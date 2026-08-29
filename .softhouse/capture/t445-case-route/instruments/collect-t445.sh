#!/usr/bin/env bash
# T445 evidence collector. Takes the drive's work root and the destination as ARGUMENTS;
# binds no literal shared-temp path to a name.
#   usage: bash collect-t445.sh <workroot> <evidence-dir> <tag>
set -u
W="${1:?workroot}"; E="${2:?evidence dir}"; TAG="${3:?tag}"
mkdir -p "$E"
GDR='.softhouse/guards'

for a in Z CASE MCASE LEGA LEGDIRTY 2ROW RVQ RWB; do
  [ -f "$W/$a/figures.txt" ] || continue
  cp "$W/$a/figures.txt" "$E/$TAG-$a-figures.txt"
  cp "$W/$a/bar.log"     "$E/$TAG-$a-bar.log" 2>/dev/null || true
done

{
  echo "=== T445 $TAG: THE INDEX SAYS ONE THING, THE FILESYSTEM ANOTHER ==="
  if [ -d "$W/CASE/run" ]; then
    R="$W/CASE/run"; D="$GDR/zz-t445k"
    echo "--- arm CASE: git ls-files -s (the INDEX) ---"
    ( cd "$R" && git ls-files -s -- "$D" )
    echo "--- arm CASE: ls -l (the FILESYSTEM) ---"
    ls -l "$R/$D"
    echo "--- arm CASE: the closing grep reads THIS (filesystem, W.txt) ---"
    cat "$R/$D/W.txt"
    echo "--- arm CASE: the INDEX entry at that same path is THIS blob ---"
    B="$( cd "$R" && git ls-files -s -- "$D/W.txt" | awk '{print $2}' )"
    echo "blob $B:"
    ( cd "$R" && git cat-file blob "$B" )
  fi
  if [ -d "$W/MCASE/run" ]; then
    R="$W/MCASE/run"; D1="$GDR/zz-t445m"; D2="$GDR/ZZ-T445M"
    echo "--- arm MCASE: git ls-files -s (the INDEX) ---"
    ( cd "$R" && git ls-files -s -- "$D1" "$D2" )
    echo "--- arm MCASE: the member row read reads THIS (filesystem) ---"
    cat "$R/$D2/x.sh"
    echo "--- arm MCASE: the INDEX entry at that same path is THIS blob ---"
    B="$( cd "$R" && git ls-files -s -- "$D2/x.sh" | awk '{print $2}' )"
    echo "blob $B:"
    ( cd "$R" && git cat-file blob "$B" )
  fi
} > "$E/$TAG-index-vs-filesystem.txt" 2>&1
cat "$E/$TAG-index-vs-filesystem.txt"
