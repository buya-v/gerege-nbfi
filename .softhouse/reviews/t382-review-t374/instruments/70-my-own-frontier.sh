#!/bin/bash
# T382 — my OWN instruments must not move the dead-path frontier. This names every row my
# review adds, before I commit, so the bar is not the first thing to find out.
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_OUT=<scratch dir> bash <this script>
# The committed transcript was produced with T382_OUT=/tmp/t382-out.
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
mkdir -p "$O"
python3 .softhouse/capture/t316-dead-path-guards/census_dead_paths.py --json "$O/census-mine.json" > "$O/census-mine.txt" 2>&1
echo "census rc=$?"
tail -1 "$O/census-mine.txt"
echo
echo "--- rows my review contributes ---"
python3 - "$O/census-mine.json" <<'PY'
import json
import sys

d = json.load(open(sys.argv[1]))
per = d["perFile"]

# REFUSE rather than report a comfortable zero from a shape I did not actually read.
# The first version of this block guessed at the JSON layout, found nothing, and printed
# "count: 0  total rows: 0" over a census that had 114 rows -- a vacuous pass in the very
# instrument that exists to stop me shipping one. Named here so the correction is visible.
if not isinstance(per, dict) or not per:
    print("REFUSED: perFile is %r, not a non-empty mapping. An empty census passes "
          "everything." % type(per).__name__)
    sys.exit(2)

rows = []
for f, v in per.items():
    if not isinstance(v, dict) or "dead" not in v:
        print("REFUSED: perFile[%r] has no 'dead' key; the layout changed and this "
              "reader would silently report zero." % f)
        sys.exit(2)
    for lit in v["dead"]:
        rows.append((f, lit))

if not rows:
    print("REFUSED: zero dead rows repo-wide. The pin is 109; a zero here is a broken "
          "reader, not a clean tree.")
    sys.exit(2)

mine = [r for r in rows if "t382-review-t374" in r[0]]
for f, lit in sorted(mine):
    print("  %s | %s" % (f, lit))
print("rows contributed by this review: %d" % len(mine))
print("total dead rows repo-wide      : %d   (the pin is the number to compare against)"
      % len(rows))
sys.exit(1 if mine else 0)
PY
echo "reader rc=$?  (0 = my review contributes NO dead row; 1 = it does, named above; 2 = REFUSED)"
