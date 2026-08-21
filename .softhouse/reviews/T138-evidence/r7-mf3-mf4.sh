#!/bin/sh
# T138 — MF-3 (the breach delta) and MF-4 (the census), measured a THIRD time,
# independently of both T107 and T115.
set -u
C=${1:?checkout}
B=/tmp/T138-mf2-post                     # export of T115 tip, already made by r6
BLOB=e6c1795a172168105d788321a71ee4ca62b73e36
SHIM=.softhouse/capture/charges/bin/preconditions.sh

echo "=================================================================="
echo "MF-3 — t51-negative.sh's form: tenant 'default', no CANARY_REQ"
echo "       pre-T91 (unhardened COPY, blob $BLOB) vs post-T91+T115"
echo "=================================================================="
echo "-- what t51-negative.sh:21 actually invokes:"
LC_ALL=C sed -n '15,25p' "$B/.softhouse/capture/charges/bin/t51-negative.sh" | sed 's/^/   /'
echo
X=/tmp/T138-mf3; rm -rf "$X"; cp -R "$B" "$X"
(cd "$C" && git cat-file blob "$BLOB") > "$X/unhardened-copy.sh"
echo "   unhardened copy sha256: $(shasum -a 256 "$X/unhardened-copy.sh" | cut -d' ' -f1)"
echo "   post shim sha256:       $(shasum -a 256 "$B/$SHIM" | cut -d' ' -f1)"
echo
for interp in sh bash; do
  "$interp" "$X/unhardened-copy.sh" default > "$X/pre-$interp.txt" 2>&1; a=$?
  "$interp" "$B/$SHIM"              default > "$X/post-$interp.txt" 2>&1; b=$?
  pa=$(LC_ALL=C grep -ac '^  PASS ' "$X/pre-$interp.txt");  fa=$(LC_ALL=C grep -ac '^  FAIL ' "$X/pre-$interp.txt")
  pb=$(LC_ALL=C grep -ac '^  PASS ' "$X/post-$interp.txt"); fb=$(LC_ALL=C grep -ac '^  FAIL ' "$X/post-$interp.txt")
  echo "   /bin/$interp   pre-T91: $pa PASS / $fa FAIL / exit $a      post: $pb PASS / $fb FAIL / exit $b      FAIL delta: $((fb-fa))"
done
echo
echo "-- the two FAIL sets side by side (sh):"
echo "   PRE-T91:"
LC_ALL=C grep -a '^  FAIL ' "$X/pre-sh.txt" | sed 's/^/     /'
echo "   POST:"
LC_ALL=C grep -a '^  FAIL ' "$X/post-sh.txt" | sed 's/^/     /'
echo
echo "-- is there a SIXTH breach anywhere?  count of distinct FAIL texts:"
echo "   pre  $(LC_ALL=C grep -a '^  FAIL ' "$X/pre-sh.txt" | sort -u | wc -l | tr -d ' ')   post $(LC_ALL=C grep -a '^  FAIL ' "$X/post-sh.txt" | sort -u | wc -l | tr -d ' ')"
echo
echo "-- the shipped header sentence, post-MF-3:"
LC_ALL=C sed -n '/MF-3 (T115)/,/side by side/p' "$B/$SHIM" | sed 's/^/   /'
echo

echo "=================================================================="
echo "MF-4 — the census, measured a third time from the tree"
echo "=================================================================="
CAP=$B/.softhouse/capture
echo "INCLUSION RULE: an executable invocation of charges/bin/preconditions.sh —"
echo "  either naming the file, or naming charges/bin/run-preconditions.sh (the T40"
echo "  wrapper, whose only job is to invoke it).  .sh and .py under .softhouse/capture/."
echo
echo "--- (a) DIRECT call sites naming preconditions.sh (excluding the shim itself,"
echo "        the COPY, the rig, and t91's own harnesses):"
LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'charges/bin/preconditions\.sh' "$CAP" \
  | LC_ALL=C grep -av '/t91/' \
  | LC_ALL=C sed "s|$CAP/||" | sort | sed 's/^/    /'
echo
echo "--- (b) call sites naming the T40 wrapper run-preconditions.sh:"
LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'run-preconditions\.sh' "$CAP" \
  | LC_ALL=C grep -av '/t91/' \
  | LC_ALL=C sed "s|$CAP/||" | sort | sed 's/^/    /'
echo
echo "--- raw counts:"
DIRECT=$(LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'charges/bin/preconditions\.sh' "$CAP" | LC_ALL=C grep -av '/t91/' | wc -l | tr -d ' ')
WRAP=$(LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'run-preconditions\.sh' "$CAP" | LC_ALL=C grep -av '/t91/' | wc -l | tr -d ' ')
echo "    direct-mention lines: $DIRECT     wrapper-mention lines: $WRAP"
echo
echo "--- (c) classify every direct-mention line: CALL / NOT-A-CALL:"
LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'charges/bin/preconditions\.sh' "$CAP" \
  | LC_ALL=C grep -av '/t91/' | while IFS= read -r l; do
      txt=${l#*:*:}
      case "$txt" in
        *grep\ -v*|*grep\ -av*)      k='NOT A CALL (grep -v exclusion)' ;;
        *"'"*"'"*preconditions.sh*copied*|*Copied\ verbatim*) k='NOT A CALL (provenance string)' ;;
        *sh\ *preconditions.sh*|*'"$W"'*|*run\(*|*subprocess*|*check_output*|*Popen*) k='CALL' ;;
        \#*)                          k='NOT A CALL (comment)' ;;
        *)                            k='REVIEW' ;;
      esac
      echo "    [$k]  ${l#$CAP/}"
    done
