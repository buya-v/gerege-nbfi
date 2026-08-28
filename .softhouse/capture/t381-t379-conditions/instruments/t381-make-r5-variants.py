#!/usr/bin/env python3
"""
T381 D-R5 -- build the two variants that drive the backslash-class CHECK'S OWN exit status.

    python3 t381-make-r5-variants.py <after.sh> <out-red.sh> <out-green.sh>

The R3 refusal in `sel()` could have been written the obvious way:

    if printf '%s' "$a" | LC_ALL=C grep -q PAT; then refuse; fi

which is the FIFTH instance of this file's own defect -- `grep` exits 2 on ERROR, an `if`
reads a 2 as FALSE, and a check that DID NOT RUN passes the selector straight through. There
is no version on `main` to compare against, because the check is new in T381, so the RED
specimen is CONSTRUCTED here -- the same thing T238 did when it preserved `sweep-ORIGINAL.sh`.

Both variants then have the CHECK'S OWN PATTERN replaced by an invalid BRE, so that `grep`
really does error and the two forms are separated by nothing except whether they read it.

Every substitution is COUNT-ANCHORED and the script dies if a count is not exactly one, so a
variant is never silently built from a file this no longer matches.
"""
import sys

if len(sys.argv) != 4:
    sys.exit(__doc__)
src, red_p, green_p = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src, encoding="utf-8").read()

# The shipped block, verbatim. Written as a list of lines so the backslashes stay readable.
HARDENED = "\n".join([
    r"""    printf '%s' "$a" | LC_ALL=C grep -q '\\[bBdDsSwW<>]'; esc_rc=$?""",
    r"""    if [ "$esc_rc" -ge 2 ]; then""",
    r"""      printf '    *** SELECTOR REFUSED: the backslash-class CHECK ITSELF did not run (rc=%s). An\n' "$esc_rc" """.rstrip(),
    r"""      printf '    *** unrun check is not a clean check, so nothing was searched.\n'""",
    r"""      [ "$SWEEP_RC" -ge 3 ] || SWEEP_RC=3""",
    r"""      return""",
    r"""    fi""",
    r"""    if [ "$esc_rc" -eq 0 ]; then""",
])
NAIVE = r"""    if printf '%s' "$a" | LC_ALL=C grep -q '\\[bBdDsSwW<>]'; then"""
CHECK_PAT = r"""'\\[bBdDsSwW<>]'"""
BROKEN_PAT = r"""'[zz-unclosed'"""

n = s.count(HARDENED)
if n != 1:
    sys.exit("D-R5: the hardened check block was found %d times in %s, expected 1" % (n, src))
red = s.replace(HARDENED, NAIVE, 1)


def break_check_pattern(text, label):
    c = text.count(CHECK_PAT)
    if c != 1:
        sys.exit("D-R5: the check pattern was found %d times in the %s variant, expected 1" % (c, label))
    return text.replace(CHECK_PAT, BROKEN_PAT, 1)


red = break_check_pattern(red, "RED")
green = break_check_pattern(s, "GREEN")

open(red_p, "w", encoding="utf-8").write(red)
open(green_p, "w", encoding="utf-8").write(green)
print("D-R5 variants built: RED uses `if printf | grep -q`, GREEN reads the status; both have")
print("  the check's own pattern replaced by the invalid BRE %s" % BROKEN_PAT)
