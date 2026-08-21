#!/bin/sh
# T138 — MF-1 RED leg, corrected base.
# T115's handoff says "10 of 13 committed transcripts replaced by the single line ...
# -> exit 0, ALL 13".  That only holds when the base set is the POST-fix transcripts
# (where A4c/A7/A8 are genuinely CLEAN).  Over the PRE-fix set the pre-MF-1 scorer
# already exits 1 on those three rows.  Both bases are run here so the claim is scoped.
set -u
W=${1:?workdir}
PREV=$W/pre/.softhouse/capture/t91/verdict.sh
POSTV=$W/post/.softhouse/capture/t91/verdict.sh
BREACH='A2a-mutated-canary-gerege A2b-mutated-canary-default
A2c-crafted-canary-and-expectation-gerege A3a-swapped-canary-gerege
A3b-missing-canary A3c-no-canary A4a-expect-override-default
A4b-expect-override-gerege A5-helpful-correct-override A6-canary-is-a-directory'

for base in postfix-livetwin-sh postfix-livetwin-bash postfix-copy-sh; do
  for scorer in PRE POST; do
    d=$W/red-$base-$scorer
    rm -rf "$d"; mkdir -p "$d"
    cp "$W"/post/.softhouse/capture/t91/out/$base/*.txt "$d"/
    chmod -R u+w "$d"
    for b in $BREACH; do echo 'truncated, nothing was ever run' > "$d/$b.txt"; done
    v=$PREV; [ "$scorer" = POST ] && v=$POSTV
    echo "=== base=$base scorer=$scorer"
    sh "$v" "$d" > "$d.out" 2>&1; rc=$?
    echo "EXIT=$rc"
    echo "last line: $(tail -1 "$d.out")"
    echo "ERROR rows in table: $(sed -n '/^TRANSCRIPT/,/^$/p' "$d.out" | grep -c 'ERROR (no EXIT= line')"
    echo "ADMITS rows in table: $(sed -n '/^TRANSCRIPT/,/^$/p' "$d.out" | grep -c 'ADMITS')"
    echo
  done
done
echo "=== FULL TABLE, base=postfix-livetwin-sh, scorer=PRE (the defect):"
cat "$W/red-postfix-livetwin-sh-PRE.out"
echo
echo "=== FULL TABLE, base=postfix-livetwin-sh, scorer=POST (the fix):"
cat "$W/red-postfix-livetwin-sh-POST.out"
