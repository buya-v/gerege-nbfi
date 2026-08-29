#!/bin/bash
# =============================================================================================
# T477 -- THE READ CENSUS, RE-MEASURED ON A CORPUS PINNED BY BLOB ID.  [T473 M-1.]
#
# T466 measured the four selectors on the PRE-FIX harness and shipped the table into the
# POST-FIX harness under the words "over non-comment lines of THIS FILE".  The table was
# therefore about a different object than the one it sat in -- which is the P-80 defect T466
# exists to prosecute, committed inside the correction.
#
# THE STRUCTURAL CAUSE IS THAT THE CORPUS WAS NAMED BY PATH AND NOT BY BLOB ID.  A path names
# whatever is there today; a blob id names an immutable object.  So this instrument takes the
# corpus as an OBJECT ID, extracts it with `git cat-file blob`, and prints that id in its own
# header beside every number it produces.  Re-running it on a different blob produces a
# different header, which is the whole point: a reader can see WHICH object was measured
# without trusting a sentence.
#
# The hasher of the numbers is T466's own `read-census.py`, unmodified, because T473
# reproduced its S1/S2/S3 to the integer from an independently written instrument and the
# question here is the CORPUS, not the selector.  The fold images it needs on stdin are
# DERIVED from the member codepoints by `foldimages.py` beside this file, never typed.
#
# usage:  readcensus.sh <blob-id> [<blob-id> ...]
#         readcensus.sh            (defaults to: committed harness, then harness on disk)
#
# The repository root is derived from this file's own location and entered ONCE, FATALLY.
# No absolute path and no repo-relative literal is spelled here; both are assembled.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
CONF="$SH/conformance"".sh"
RC="$SH/capture/t466-t459-conditions/instruments/read-census"".py"

cd "$R" || {
  echo "ERROR: could not enter the derived repository root: $R" >&2
  echo "ERROR: REFUSING (exit 3). Nothing below would be a measurement." >&2
  exit 3
}
[ -f "$CONF" ] || { echo "ERROR: no harness at the derived root. REFUSING (exit 3)." >&2; exit 3; }
[ -f "$RC" ]   || { echo "ERROR: T466's read census is absent. REFUSING (exit 3)." >&2; exit 3; }

SCR="${T477_WORK:-}"
if [ -z "$SCR" ]; then
  SCR=$(mktemp -d "${TMPDIR:-/tmp}/t477-work.XXXXXXXXXX") || exit 3
fi
export T477_WORK="$SCR"

# THE FOLD-CENSUS MEMBER SET, AS CODEPOINTS.  These thirteen are the set T459 corrected, T466
# re-derived with its own filesystem probe and T473 reproduced member for member.  They are
# spelled as hex NUMBERS and their ASCII images are computed, so no image is transcribed.
IMG="$SCR/fold-images.txt"
"$SELF_DIR/foldimages.py" >"$IMG" <<'CPS'
017F
037E
1FEF
212A
00DF
1E9E
FB00
FB01
FB02
FB03
FB04
FB05
FB06
CPS
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "ERROR: the fold images could not be derived (exit $rc). REFUSING." >&2
  exit 3
fi
nimg=$(LC_ALL=C grep -c '' "$IMG" || true)
echo "FOLD IMAGES DERIVED: $nimg  [$(tr '\n' ' ' <"$IMG")]"
if [ "${nimg:-0}" -lt 2 ]; then
  echo "ERROR: $nimg image(s). REFUSING -- foldability would be a fact about this pipe." >&2
  exit 3
fi
echo

if [ "$#" -gt 0 ]; then
  BLOBS="$*"
else
  a=$(git rev-parse "HEAD:$CONF") || exit 3
  b=$(git hash-object --no-filters -- "$CONF") || exit 3
  BLOBS="$a $b"
fi

for id in $BLOBS; do
  f="$SCR/corpus-$id"
  if ! git cat-file blob "$id" >"$f" 2>/dev/null; then
    echo "ERROR: $id is not a readable blob in this repository. REFUSING." >&2
    exit 3
  fi
  n=$(LC_ALL=C grep -c '' "$f" || true)
  echo "=============================================================================="
  echo "CORPUS BLOB = $id"
  echo "  bytes     = $(LC_ALL=C wc -c <"$f" | tr -d ' ')"
  echo "  newlines  = $n"
  hd=$(git rev-parse "HEAD:$CONF" 2>/dev/null || echo '<none>')
  dk=$(git hash-object --no-filters -- "$CONF" 2>/dev/null || echo '<none>')
  role="an object that is NEITHER the committed harness NOR the harness on disk"
  [ "$id" = "$hd" ] && role="THE COMMITTED HARNESS (git rev-parse HEAD:<harness>)"
  [ "$id" = "$dk" ] && role="THE HARNESS ON DISK (git hash-object --no-filters)"
  [ "$id" = "$hd" ] && [ "$id" = "$dk" ] && role="THE COMMITTED HARNESS, AND ALSO THE BYTES ON DISK"
  echo "  role      = $role"
  echo "------------------------------------------------------------------------------"
  # THE CENSUS IS RUN INTO A FILE AND ITS EXIT CODE IS READ, not piped into `sed` where the
  # pipeline's exit status would be `sed`'s and a crashed census would print as a short list.
  o="$SCR/census-$id.txt"
  if ! /usr/bin/python3 "$RC" "$f" <"$IMG" >"$o" 2>&1; then
    echo "ERROR: the read census exited non-zero on $id. First lines:" >&2
    LC_ALL=C sed -n '1,10p' "$o" >&2
    echo "ERROR: REFUSING (exit 3) -- a census that crashed has not reported a number." >&2
    exit 3
  fi
  LC_ALL=C sed -n '1,7p' "$o"
  echo
done
