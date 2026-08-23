#!/usr/bin/env python3
"""T290 -- count the printed DISAGREEMENT blocks in an R-VPA transcript, WITHOUT trusting the
rule's own summary line. This is the reviewer's independent movement of the pinned number 4
(P-83: two independent movements of one pinned number reconcile BY RUNNING).

WHY THIS IS A PYTHON FILE AND NOT A SHELL PIPELINE, and it is a finding against this review.
The first draft of `run.sh` counted with `grep -c '...' file || true`. T259's lint caught SIX
findings in that one block, and both are real, not stylistic:
  * `grep -c` prints `0` for `no matches` and, on a bad path or a broken pattern, ALSO prints
    nothing and exits >1 -- `|| true` then paints both as a reassuring zero. That is P-81's
    recorded case verbatim (`T241's census script collapsed grep -c || echo 0, putting "zero
    matches" and "I broke" onto one printed zero`);
  * a bare `grep` may resolve to bundled ugrep with a hidden `--exclude-dir` (P-75).
So the count is done here, where a missing file is an ERROR (2) and a zero count is a MEASURED
zero. Recorded rather than quietly repaired -- this is now the fourth instrument in this program
to break the fail-open rule inside work written to enforce it, and the only thing to its credit is
that the lint was pointed at it before it was committed.

EXIT 0 counted; 2 the transcript is unreadable. There is no exit 1: a count is not a verdict.
PROBE: `T290-COUNT: <file> unacknowledged=.. acknowledged=.. total=..`
"""
import sys
from pathlib import Path

PROBE = "T290-COUNT:"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: count_disagreement_blocks_t290.py <transcript>...", file=sys.stderr)
        return 2
    for arg in sys.argv[1:]:
        p = Path(arg)
        try:
            text = p.read_text()
        except OSError as exc:
            print("ERROR: %s: %s" % (arg, exc), file=sys.stderr)
            return 2
        unack = sum(1 for ln in text.splitlines() if "*** DISAGREEMENT [UNACKNOWLEDGED]" in ln)
        ack = sum(1 for ln in text.splitlines() if "*** DISAGREEMENT [ACKNOWLEDGED]" in ln)
        if "R-VPA -- verdict/predicate agreement" not in text:
            print("ERROR: %s does not look like an R-VPA transcript; refusing to report a count "
                  "over a file I cannot identify" % arg, file=sys.stderr)
            return 2
        print("%s %s unacknowledged=%d acknowledged=%d total=%d"
              % (PROBE, p.name, unack, ack, unack + ack))
    return 0


if __name__ == "__main__":
    sys.exit(main())
