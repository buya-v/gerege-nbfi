#!/bin/sh
# T138 — V-A reproduced independently.  The pre-fix verdict.sh scores inside a
# PIPELINE SUBSHELL, so its only failure channel is the file $D/.score-fail —
# which lives in the directory under audit.  Make $D read-only and the scorer
# contradicts its own visible table.
set -u
W=${1:?workdir}
PREV=$W/pre/.softhouse/capture/t91/verdict.sh
POSTV=$W/post/.softhouse/capture/t91/verdict.sh
echo "id: $(id -u) ($(id -un))   — not root, so a mode-555 directory really is read-only"
echo

for scorer in PRE POST; do
  v=$PREV; tag=pre-fix; [ "$scorer" = POST ] && { v=$POSTV; tag=post-fix; }
  d=$W/va-$scorer
  rm -rf "$d"; mkdir -p "$d"
  cp "$W"/pre/.softhouse/capture/t91/out/prefix-livetwin-sh/A*.txt "$d"/
  chmod 555 "$d"
  echo "=================================================================="
  echo "verdict.sh ($tag) over a READ-ONLY transcript dir  [mode $(stat -f '%Lp' "$d")]"
  echo "=================================================================="
  sh "$v" "$d" 2>&1; rc=$?
  echo "EXIT=$rc"
  echo "visible ADMITS rows on screen: $(sh "$v" "$d" 2>/dev/null | sed -n '/^TRANSCRIPT/,/^$/p' | grep -c ADMITS)"
  chmod 755 "$d"
  echo
done

echo "=================================================================="
echo "CONTROL: same transcripts, WRITABLE dir, pre-fix scorer"
echo "=================================================================="
d=$W/va-control
rm -rf "$d"; mkdir -p "$d"
cp "$W"/pre/.softhouse/capture/t91/out/prefix-livetwin-sh/A*.txt "$d"/
sh "$PREV" "$d" 2>&1 | tail -10
sh "$PREV" "$d" >/dev/null 2>&1; echo "EXIT=$?"
