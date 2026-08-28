#!/usr/bin/env python3
"""T331 -- apply T282's wiring diff to .softhouse/conformance.sh.

ANCHORED ON TEXT, NOT LINE NUMBERS, in both directions -- P-80: a corrected cardinal rots in
every place it was restated; the count is the same defect as the line number.

T282's handoff specifies anchor 1 as "immediately BEFORE the line
`guard_no_host_state_in_lint_corpus() {`". THAT ANCHOR RESOLVES UNIQUELY, AND APPLYING IT
LITERALLY IS WRONG, which is a finding about the anchor strategy and is recorded in T331's
handoff. In this file a guard is a DOC BLOCK immediately above its FUNCTION, and
guard_no_host_state_in_lint_corpus's doc block is ~218 lines long and ends in a multi-line
pinned literal. Inserting at the literal token would splice a new function BETWEEN a guard's
documentation and the guard it documents. So this script anchors on the DOC BLOCK HEADER --
the boundary the token was standing in for -- and refuses if the header is not immediately
preceded by the `# ---` rule the file's convention puts there.

Anchor 2 is applied exactly as written: one call immediately after
`  guard_no_host_state_in_lint_corpus  || failed=1`.

IDEMPOTENT AND FAIL-CLOSED: it refuses if the guard is already present, if either anchor
matches zero times, or if either matches more than once. An anchor that matched twice has no
"the" match, and picking one would be a coin flip dressed as a measurement.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3].parent
CONF = ROOT / ".softhouse" / "conformance.sh"
BLOCK = pathlib.Path(__file__).with_name("insert-block.txt")

DOC_HEADER = ("# guard_no_host_state_in_lint_corpus: THE FAIL-OPEN FRONTIER MUST BE A PROPERTY")
TOKEN_ANCHOR = "guard_no_host_state_in_lint_corpus() {"
CALL_ANCHOR = "  guard_no_host_state_in_lint_corpus  || failed=1"
NEW_CALL = "  guard_pnumber_citations             || failed=1        # T282, wired HARD by T331"
RULE = "# ---------------------------------------------------------------------------"


def die(msg):
    print("T331-APPLY: REFUSED -- " + msg)
    sys.exit(1)


def main():
    lines = CONF.read_text(encoding="utf-8").splitlines(keepends=True)
    if any("guard_pnumber_citations()" in l for l in lines):
        die("guard_pnumber_citations() is already present. This script is not a patcher.")

    tok = [i for i, l in enumerate(lines) if l.rstrip("\n") == TOKEN_ANCHOR]
    print("T331-APPLY: T282's literal anchor 1 %r resolves at line(s) %s"
          % (TOKEN_ANCHOR, [i + 1 for i in tok]))
    if len(tok) != 1:
        die("anchor 1 matched %d times; it must match exactly 1." % len(tok))

    hdr = [i for i, l in enumerate(lines) if l.startswith(DOC_HEADER)]
    if len(hdr) != 1:
        die("the doc-block header matched %d times; it must match exactly 1." % len(hdr))
    h = hdr[0]
    if lines[h - 1].rstrip("\n") != RULE:
        die("the doc-block header at line %d is not preceded by the convention's `# ---` rule; "
            "the file's layout has changed and this insertion point is no longer identified."
            % (h + 1))
    ins = h - 1
    print("T331-APPLY: doc-block header at line %d; inserting before its `# ---` rule at line %d"
          % (h + 1, ins + 1))
    print("T331-APPLY: (T282's token anchor would have inserted at line %d, i.e. BETWEEN the "
          "T273 doc block and the function it documents -- see the handoff.)" % (tok[0] + 1))

    call = [i for i, l in enumerate(lines) if l.rstrip("\n") == CALL_ANCHOR]
    print("T331-APPLY: anchor 2 %r resolves at line(s) %s"
          % (CALL_ANCHOR, [i + 1 for i in call]))
    if len(call) != 1:
        die("anchor 2 matched %d times; it must match exactly 1." % len(call))

    block = BLOCK.read_text(encoding="utf-8")
    if not block.endswith("\n"):
        block += "\n"

    # Apply the LATER edit first so the earlier one's index stays valid.
    out = list(lines)
    out.insert(call[0] + 1, NEW_CALL + "\n")
    out.insert(ins, block)
    CONF.write_text("".join(out), encoding="utf-8")
    print("T331-APPLY: applied. %d lines -> %d lines." % (len(lines), len("".join(out).splitlines())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
