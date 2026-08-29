#!/bin/bash
# T459 arms RWB3CTL / RWB3 -- T446's MAJOR-2: the decisive-lines WATCH pinned the line that
# COMPUTES the tracked text, not the line that USES it, so a one-line revert of the REACHED-BY
# witness test back to a filesystem read is invisible to the watch.
#   RWB3CTL : the W.txt/w.txt collision fixture, harness UNMUTATED
#   RWB3    : the same fixture, plus the ONE-LINE revert
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="$1"; VARIANT="$2"      # VARIANT = CTL | MUT
A="RWB3-$VARIANT-$BASE"
arm "$A" "$BASE"
D="$( stage "$A" "$BASE" )" || exit 3
S="$D/src"
MEMBER="$GUARDS/zz-t459-member"".sh"
WITU="$GUARDS/W"".txt"
WITL="$GUARDS/w"".txt"

# the member: it declares its own REACHED-BY row, naming the UPPER-CASE witness
{ printf '#!/usr/bin/env bash\n'
  printf '# T459 fixture member.\n'
  printf '# self-naming header line, as a real member has: zz-t459-member%s\n' ".sh"
  printf '# GUARDS-DIR-REGISTRATION: REACHED-BY %s\n' "$WITU"
  printf 'exit 0\n'; } > "$S/$MEMBER"
chmod +x "$S/$MEMBER"
# the DECOY witness: tracked, regular, 100644, and it names NOTHING
printf 'T459 decoy witness. This file names no member at all.\n' > "$S/$WITU"
( cd "$S" && git add -- "$MEMBER" "$WITU" ) >/dev/null 2>&1

if [ "$VARIANT" = MUT ]; then
  # THE ONE-LINE REVERT: the WITNESS naming test stops using the tracked text and greps the
  # working tree instead.  Assembled from fragments so this file pins nothing.
  OLD='elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then'
  NEW='elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then'
  LC_ALL=C grep -cF -- "$OLD" "$S/$CONF" || { echo "    fixture: decisive line not found" >&2; exit 3; }
  python3 - "$S/$CONF" "$OLD" "$NEW" <<'PY'
import sys
p,old,new=sys.argv[1],sys.argv[2],sys.argv[3]
s=open(p).read()
assert s.count(old)==1, s.count(old)
open(p,'w').write(s.replace(old,new))
PY
  ( cd "$S" && git add -- "$CONF" ) >/dev/null 2>&1
fi

# the lower-case SYMLINK entry: its blob is the TARGET PATH STRING, it sorts after W.txt, and
# it wins the checkout on this fold-insensitive volume.
LNK="$( cd "$S" && printf 'zz-t459-member%s' ".sh" | git hash-object -w --stdin )" || exit 3
( cd "$S" && git update-index --add --cacheinfo "120000,$LNK,$WITL" ) || exit 3

( cd "$S" && git commit -q -m "T459 RWB3 fixture" ) >/dev/null 2>&1 || exit 3
rm -rf "$D/graded"
git clone -q --no-hardlinks "$S" "$D/graded" >/dev/null 2>&1 || exit 3
G="$D/graded"
echo "    committed blob of $WITU = $( cd "$G" && git rev-parse "HEAD:$WITU" )"
echo "    materialised at that path = $( cd "$G" && git hash-object -- "$WITU" )"
echo "    what is on disk there: $( head -c 60 "$G/$WITU" | tr '\n' ' ' )"
runbar "$G" "$D/bar.log"
echo "    --- decisive-lines watch:"
LC_ALL=C grep -m2 'decisive line\|decisive$\|present EXACTLY ONCE\|decisive lines' "$D/bar.log" | sed 's/^/    /'
LC_ALL=C grep -m1 -B2 -A6 'THE DECISIVE LINE IS GONE' "$D/bar.log" | sed 's/^/    /'
echo "    --- reached-by verdict lines:"
LC_ALL=C grep -m3 'REACHED-BY\|reached-by=' "$D/bar.log" | sed 's/^/    /'
