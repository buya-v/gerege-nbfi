#!/usr/bin/env bash
# T402 -- BUILD THE "T386-MINIMAL" SPECIMEN.
#
#   bash t402-make-t386min.sh <in-sweep.sh> <out-sweep.sh>
#
# Applies T386's literal five-line fix -- read `cat`'s status at both sites and refuse -- to a
# copy of `casualty-sweep.sh`, AND NOTHING ELSE. The specimen exists so that ARM R of
# t402-errf-class-drive.sh can answer a question T386's review could not: is reading `cat`'s
# status SUFFICIENT, or only NECESSARY?
#
# IT REFUSES RATHER THAN PROCEEDS. Each anchor must appear EXACTLY ONCE. A builder that
# silently patches zero sites would hand the drive an unmodified file and the drive would then
# report "the five-line fix does not help" about a fix that was never applied -- which is the
# same shape as everything else in this task. Exit 2 on any anchor miscount, and say which.
set -uo pipefail
IN=${1:?usage: <in> <out>}
OUT=${2:?usage: <in> <out>}

python3 - "$IN" "$OUT" <<'PY'
import sys

src_path, out_path = sys.argv[1], sys.argv[2]
with open(src_path, "r", encoding="utf-8") as fh:
    text = fh.read()

# --- anchor 1: engine_count() -------------------------------------------------------------
A1 = '  ENGINE_ERR=$(cat "$SWEEP_ERRF")\n'
R1 = (
    '  ENGINE_ERR=$(cat "$SWEEP_ERRF"); cat_rc=$?\n'
    '  if [ "$cat_rc" -ne 0 ]; then\n'
    '    return 2\n'
    '  fi\n'
)

# --- anchor 2: sel() ----------------------------------------------------------------------
A2 = '  err=$(cat "$SWEEP_ERRF")\n'
R2 = (
    '  err=$(cat "$SWEEP_ERRF"); cat_rc=$?\n'
    '  if [ "$cat_rc" -ne 0 ]; then\n'
    '    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4\n'
    '    printf \'    *** SELECTOR DID NOT RUN: the stderr channel is unreadable, so a status of\\n\'\n'
    '    printf \'    *** %s cannot be told apart from a search that never started.\\n\' "$rc"\n'
    '    return\n'
    '  fi\n'
)

fail = []
for name, anchor in (("engine_count ENGINE_ERR=$(cat ...)", A1), ("sel err=$(cat ...)", A2)):
    n = text.count(anchor)
    print("  anchor %-40s occurrences=%d" % (name, n))
    if n != 1:
        fail.append("%s occurs %d times, wanted exactly 1" % (name, n))

if fail:
    for f in fail:
        print("  REFUSED: " + f)
    sys.exit(2)

text = text.replace(A1, R1, 1).replace(A2, R2, 1)
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write(text)
print("  specimen written: T386's five-line fix applied at 2 sites, nothing else changed")
PY
