#!/usr/bin/env python3
"""T108 — corpus generator for the grep/invalid-multibyte adjudication.

Writes one file per SHAPE into ./corpus/, byte-exact and deterministic.
No arithmetic of any kind, therefore no floating point (P-25 is satisfied
vacuously: this script computes nothing).

Every shape contains the literal ASCII token `TARGET` on exactly the number of
lines stated in SHAPES[*][1], except `t80-exact-repro`, which reproduces the
shape of the transcript T80 was actually grepping and is scored with three
different patterns by run-matrix.sh.

Run:  python3 gen-corpus.py
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")

# name -> (bytes, expected true count of lines containing b"TARGET")
SHAPES = {
    # ---- lone 0xFF (never valid UTF-8 anywhere) -------------------------
    "s01-ff-same-line-before": (
        b"alpha clean line\n"
        b"\xff TARGET here\n"
        b"omega clean line\n", 1),
    "s02-ff-same-line-after": (
        b"alpha clean line\n"
        b"TARGET here \xff\n"
        b"omega clean line\n", 1),
    "s03-ff-other-line-earlier": (
        b"junk \xff byte\n"
        b"TARGET here\n"
        b"omega clean line\n", 1),
    "s04-ff-other-line-later-eof": (
        b"TARGET here\n"
        b"omega clean line\n"
        b"junk \xff byte\n", 1),
    "s05-ff-eof-no-trailing-newline": (
        b"TARGET here\n"
        b"omega clean line\n"
        b"\xff", 1),

    # ---- truncated UTF-8: lone 0xE2 lead byte (T80's actual byte) -------
    # U+2026 HORIZONTAL ELLIPSIS is e2 80 a6; the shell ate the name up to
    # the first non-identifier byte, leaving a lone e2 in the diagnostic.
    "s06-e2-same-line-before": (
        b"alpha clean line\n"
        b"PIN_PG_MAJOR_MINOR\xe2: TARGET here\n"
        b"omega clean line\n", 1),
    "s07-e2-other-line-later-eof": (
        b"TARGET here\n"
        b"omega clean line\n"
        b"PIN_PG_MAJOR_MINOR\xe2: unbound variable\n", 1),
    "s08-e280-truncated-3byte-eof": (
        b"TARGET here\n"
        b"omega clean line\n"
        b"trailing \xe2\x80\n", 1),

    # ---- embedded NUL ---------------------------------------------------
    "s09-nul-other-line": (
        b"TARGET here\n"
        b"nul \x00 byte\n", 1),
    "s10-nul-same-line": (
        b"pre \x00 TARGET here\n"
        b"omega clean line\n", 1),

    # ---- negative control: valid multibyte UTF-8, nothing invalid -------
    "s11-clean-valid-utf8": (
        b"TARGET here\n"
        b"ellipsis \xe2\x80\xa6 is valid utf-8\n", 1),
    "s12-clean-pure-ascii": (
        b"TARGET here\n"
        b"omega clean line\n", 1),

    # ---- reconstruction of what T80 was actually grepping ---------------
    # Pattern set for this shape (see run-matrix.sh):
    #   '^  PASS'               -> true count 3   (all on CLEAN lines)
    #   'unbound variable'      -> true count 1   (on the DIRTY line)
    #   'PRECONDITIONS BREACHED'-> true count 0   (genuinely absent)
    "t80-exact-repro": (
        b"=== T85 F-2 - a guard that dies instead of firing\n"
        b"  PASS P1 image digest pinned\n"
        b"  PASS P2 container up\n"
        b"  PASS P3 tenant reachable\n"
        b"  FAIL P7 PostgreSQL version is 9.9.9\n"
        b"t36/preconditions.sh: line 166: PIN_PG_MAJOR_MINOR\xe2: unbound variable\n", 0),
}


def main():
    os.makedirs(CORPUS, exist_ok=True)
    for name, (blob, _) in sorted(SHAPES.items()):
        path = os.path.join(CORPUS, name + ".txt")
        with open(path, "wb") as fh:
            fh.write(blob)
        print("wrote %-34s %d bytes" % (name + ".txt", len(blob)))


if __name__ == "__main__":
    main()
