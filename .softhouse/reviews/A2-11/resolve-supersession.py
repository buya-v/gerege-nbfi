#!/usr/bin/env python3
"""T270 -- READ the supersession register; never restate what it says.

  python3 resolve-supersession.py <register-path> <frozen-file-basename>

  stdout  the basename of the replacement, on success, and nothing else
  exit 0  the register names a replacement and that replacement is on disk
  exit 2  it does not -- REFUSE.  There is no fallback to the frozen original.

WHY THIS EXISTS
---------------
`.softhouse/reviews/A2-11/run-all.sh` used to invoke `prove-mkreq7-guard-red.py`
directly.  T164 had already replaced that script's float arm -- it asserted
"analyze7.py parses money as Decimal" with a WHOLE-FILE SOURCE GREP that its own
target's docstring satisfies -- but the harness kept executing it, so every run
printed `ok   it parses JSON numbers as Decimal` / `16 assertions, 0 failed` /
`exit=0` beside a real guard that says the opposite.

T114 requires the BYTES of an evidence-producing script be preserved.  It does NOT
require that the file keep being EXECUTED as though it still graded something.
Those are two obligations, and conflating them is what produced the trap: a
superseded guard that still prints PASS is not preserved evidence.

P-80 ("make the second site READ the first, do not restate the cardinal") is why
this is a lookup rather than a hard-coded successor name in the shell script.  If
somebody later re-points `prove-mkreq7-guard-red.py` at a different replacement,
`run-all.sh` follows without being edited; if somebody DELETES the register line,
`run-all.sh` REFUSES rather than quietly reverting to the trap.  Fail-closed is the
whole point -- a fallback to the original would recreate the defect this closes.

READ-ONLY.  Writes nothing but stdout/stderr.  Contacts no oracle.
"""
import os
import sys


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    register, frozen = argv[1], argv[2]

    if not os.path.exists(register):
        print("REFUSE: supersession register %s is not on disk. A missing register is "
              "an ERROR, not a licence to run the superseded file." % register,
              file=sys.stderr)
        return 2

    # Same parse as census-json-float-siblings.py: `#` starts a comment, `A -> B`.
    entries = {}
    for raw in open(register):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        parts = [x.strip() for x in line.split("->")]
        if len(parts) == 2 and parts[0] and parts[1]:
            entries[parts[0]] = parts[1]

    if not entries:
        print("REFUSE: %s parsed to 0 entries. A register that resolves nothing cannot "
              "authorise anything (P-22: nil coverage is an error, not a pass)."
              % register, file=sys.stderr)
        return 2

    if frozen not in entries:
        print("REFUSE: %s does not name a replacement for %s. %d entr(ies) parsed: %s.\n"
              "        Not falling back to the superseded file -- that fallback IS the "
              "defect T270 closed." % (register, frozen, len(entries),
                                       ", ".join(sorted(entries))),
              file=sys.stderr)
        return 2

    repl = entries[frozen]
    rdir = os.path.dirname(os.path.abspath(register))
    if not os.path.exists(os.path.join(rdir, repl)):
        print("REFUSE: %s redirects %s -> %s, but %s is not on disk beside the register. "
              "A redirect to a missing replacement is worse than no redirect."
              % (register, frozen, repl, repl), file=sys.stderr)
        return 2

    print(repl)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
