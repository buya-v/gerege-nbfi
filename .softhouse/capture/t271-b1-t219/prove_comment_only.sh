#!/usr/bin/env bash
# T271 -- prove the two edits inside `t219-g8-residual/` are LABELLED CORRECTIONS and not a
# retro-edit of the committed evidence (T114/T176).
#
#   1. `out/classify-t219.json` is BYTE-UNCHANGED by T271. Its sha256 is what
#      `acknowledged-t219.json` pins; if it moved, every acknowledgement over it would go VOID
#      and the rows would go RED, which is the mechanism working, not a hazard to route around.
#   2. `src/classify_t219.py` gained a `*** T271 CORRECTION ***` banner and NOTHING ELSE: the
#      pre-edit file is extracted BY PINNED BLOB SHA (not `HEAD:path`, which becomes the edited
#      file the moment this branch is committed -- T268's lesson), both versions are run on the
#      same inputs, and the two outputs must be byte-identical.
#   3. The `cells` array of that output must equal the committed `out/classify-t219.json` --
#      i.e. the four disagreements T271 acknowledges are reproducible from the raw capture and
#      are not an artefact of a stale file.
#
# EXIT: 0 all three hold; 1 a real measured negative; 2 error. Never conflated (P-80).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
T219="$ROOT/.softhouse/capture/t219-g8-residual"
WORK="$(mktemp -d)"
PROBE="T271-COMMENTONLY:"
PINNED_ACK_SHA="5226eacea7ff004eb545a9d8d02278096834e22ccd64f74828472dc0c5708bc8"
PINNED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"

# The classifier as committed alongside its own output, pinned by BLOB sha.
PRE_BLOB="$(git -C "$ROOT" rev-parse "6eacc06:.softhouse/capture/t219-g8-residual/src/classify_t219.py")"

echo "$PROBE inputs"
echo "  repo root        : $ROOT"
echo "  HEAD             : $(git -C "$ROOT" rev-parse HEAD)"
echo "  pre-edit blob    : $PRE_BLOB   (classify_t219.py as committed at 6eacc06 with its output)"
echo "  live classify sha: $(shasum -a 256 "$T219/out/classify-t219.json" | cut -d' ' -f1)"
echo "  pinned in ack    : $PINNED_ACK_SHA"
echo ""

FAIL=0

# ---- 1. the committed evidence is byte-unchanged by T271 --------------------------------------
LIVE_SHA="$(shasum -a 256 "$T219/out/classify-t219.json" | cut -d' ' -f1)"
if [ "$LIVE_SHA" = "$PINNED_ACK_SHA" ]; then
  echo "  [1] classify-t219.json UNCHANGED and matches the sha the acknowledgement pins   OK"
else
  echo "  [1] classify-t219.json MOVED: $LIVE_SHA -- every acknowledgement over it is VOID   FAIL"
  FAIL=1
fi

# ---- 2. the classifier edit is comment-only ---------------------------------------------------
git -C "$ROOT" cat-file blob "$PRE_BLOB" > "$WORK/classify_pre.py"
REF3G="$ROOT/.softhouse/capture/out/capture-prod3g-raw.json"
LIVE_REF3G_SHA="$(shasum -a 256 "$REF3G" | cut -d' ' -f1)"
if [ "$LIVE_REF3G_SHA" != "$PINNED_REF3G_SHA" ]; then
  echo "ERROR: the calibration reference moved: $LIVE_REF3G_SHA" >&2
  rm -rf "$WORK"
  exit 2
fi
RAW="$T219/out/capture-t219-raw.json.gz"
( cd "$T219" && python3 "$WORK/classify_pre.py" "$RAW" prediction.json "$REF3G" ) > "$WORK/out_pre.json"
( cd "$T219" && python3 src/classify_t219.py    "$RAW" prediction.json "$REF3G" ) > "$WORK/out_post.json"
if cmp -s "$WORK/out_pre.json" "$WORK/out_post.json"; then
  echo "  [2] pre-edit and post-edit classifier outputs are BYTE-IDENTICAL                  OK"
else
  echo "  [2] the edit CHANGED BEHAVIOUR -- it is not comment-only                          FAIL"
  diff "$WORK/out_pre.json" "$WORK/out_post.json" | head -40
  FAIL=1
fi

# ---- 3. the cells the acknowledgement is about are reproducible from the raw capture ----------
CMP="$HERE/compare_sections_t271.py"
RC3=0
python3 "$CMP" cells "$WORK/out_post.json" "$T219/out/classify-t219.json" || RC3=$?
if [ "$RC3" -eq 0 ]; then
  echo "  [3] re-run cells[] == committed cells[]                                           OK"
elif [ "$RC3" -eq 1 ]; then
  echo "  [3] re-run cells[] DIFFER from the committed record                               FAIL"
  FAIL=1
else
  echo "ERROR: the comparison itself errored (exit $RC3)" >&2
  rm -rf "$WORK"
  exit 2
fi

# ---- 4. what is NOT reproducible, stated rather than hidden (P-66/P-70) -----------------------
echo ""
echo '  PRE-EXISTING AND NOT CAUSED BY T271, stated because a reader of [3] will ask: the two'
echo '  calibration[] rows are NOT reproducible from the committed inputs. The committed file'
echo '  records threwIdentical=false / status=DIFFERS; re-running the committed classifier'
echo '  against the committed raw captures and the calibration reference at its pinned sha'
echo '  (unchanged since T64) yields threwIdentical=true / status=REPRODUCED. cells[] reproduces'
echo '  exactly; only calibration[] does not. T271 did not touch it and does not rule on it --'
echo '  see the handoff Follow-ups. It does not touch the four B-1 pairs, which live in cells[].'
RC4=0
python3 "$CMP" calibration "$WORK/out_post.json" "$T219/out/classify-t219.json" || RC4=$?
if [ "$RC4" -gt 1 ]; then
  echo "ERROR: the comparison itself errored (exit $RC4)" >&2
  rm -rf "$WORK"
  exit 2
fi

rm -rf "$WORK"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "$PROBE GREEN unchanged=1 commentOnly=1 cellsReproduce=1 calibrationReproduces=$((1 - RC4))"
else
  echo "$PROBE REFUSED  -- see the FAIL lines above"
fi
exit "$FAIL"
