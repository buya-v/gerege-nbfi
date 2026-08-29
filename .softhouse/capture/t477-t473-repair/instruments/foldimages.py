#!/usr/bin/env python3
"""
T477 -- THE FOLD IMAGES, DERIVED FROM THEIR CODEPOINTS RATHER THAN TYPED.

The read census measures "FOLDABLE" against the set of ASCII images produced by the confirmed
fold-census members.  Typing those images here would be one more restated cardinal (P-80), so
they are COMPUTED: each member codepoint arrives as a hex number on stdin, is normalised, and
its image is printed.  The distinct set is printed once, sorted, one per line.

CALIBRATION (P-72): U+017F must produce `s` and the ASCII letter `a` must produce `a`; if the
normaliser on this host does neither, the images below are a statement about this python build
and not about the filesystem, and this refuses rather than printing a shorter list.
"""
import sys
import unicodedata


def image(cp: int) -> str:
    ch = chr(cp)
    for form in ("NFKD", "NFKC"):
        n = unicodedata.normalize(form, ch).lower()
        if n and n != ch and all(0x20 <= ord(c) < 0x7F for c in n):
            return n
    n = ch.lower()
    if n != ch and all(0x20 <= ord(c) < 0x7F for c in n):
        return n
    n = ch.casefold()
    if n != ch and all(0x20 <= ord(c) < 0x7F for c in n):
        return n
    return ""


def main() -> int:
    if image(0x017F) != "s":
        sys.stderr.write("REFUSED: CALIBRATION FAILED -- U+017F does not fold onto ASCII s on "
                         "this host. The image list would be a fact about this python.\n")
        return 3
    if image(0x0041) != "a":
        sys.stderr.write("REFUSED: CALIBRATION FAILED -- the ASCII case fold does not work.\n")
        return 3
    out = set()
    seen = 0
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        seen += 1
        im = image(int(line, 16))
        if not im:
            sys.stderr.write("REFUSED: %s has NO printable-ASCII image. The member set handed "
                             "in is not the confirmed one.\n" % line)
            return 3
        out.add(im)
    if seen < 2:
        sys.stderr.write("REFUSED: %d codepoint(s) on stdin. An empty or near-empty member set "
                         "makes every site 'not foldable', which is a fact about this pipe.\n"
                         % seen)
        return 3
    sys.stderr.write("MEMBERS IN = %d ; DISTINCT IMAGES OUT = %d\n" % (seen, len(out)))
    for im in sorted(out):
        sys.stdout.write(im + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
