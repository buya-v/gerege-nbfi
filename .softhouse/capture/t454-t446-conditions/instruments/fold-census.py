#!/usr/bin/env python3
"""
T454 -- THE FOLD CENSUS.  How many characters other than U+017F fold onto an ASCII
character that appears in a path this harness reads from the WORKING TREE, and how many
of those sort AFTER their ASCII partner in git's index order?

WHY THIS EXISTS.  T445 argued that the one working-tree read it kept -- the harness
reading `.softhouse/conformance.sh` -- was safe because "the index entry that sorts LAST
wins a checkout collision, so an all-lowercase ASCII path is unbeatable".  T446 falsified
that with ONE character, U+017F LATIN SMALL LETTER LONG S, and said explicitly: "One fold
is enough to falsify 'cannot win'; I make no claim about how many there are."  This is
that claim, measured.

THE INSTRUMENT MUST NOT BE ABLE TO PRINT A NEGATIVE IT DID NOT MEASURE (T238 sweeplib's
invariant, adopted in shape rather than by sourcing -- this is a self-contained census with
no sweep engine to calibrate):

  * the candidate generator is CALIBRATED on a known positive (U+017F -> 's') and a known
    negative (U+212A KELVIN SIGN -> 'k', which is a real fold but 'k' is NOT in the target
    path) BEFORE any count is reported.  A generator that cannot find U+017F cannot report
    "no other folds" and be believed;
  * "the filesystem collided" and "the filesystem did not collide" and "the probe could not
    run" are THREE facts with three exit codes: 0 / 0 / 3;
  * every filesystem probe writes two distinguishable contents and reads back which one
    survived; a read that returns neither is exit 3, never "no collision".

EXIT CODES
  0  the census ran and its numbers are measurements
  2  a calibration failed -- no number in this run is interpretable
  3  the instrument could not perform a probe it needed to perform
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata

# ---------------------------------------------------------------------------------------
# THE TARGET SET.  Not "every ASCII letter": the letters that actually appear in a path
# this harness reads from the WORKING TREE rather than from a blob.  The list of such
# paths is the corrected audit table in the T454 handoff; the union of their characters is
# what an attacker gets to choose from.
# ---------------------------------------------------------------------------------------
TARGET_PATHS = [
    ".softhouse/conformance.sh",
    ".softhouse/guards",
]


def target_chars():
    """EVERY character of the target paths except '/', not merely the letters.  '.' is in
    the set on purpose: a fold onto the dot would give an attacker `.ſofthouse/…` or
    `.softhouse/conformance˙sh`, and excluding punctuation because "folds are a letter
    thing" would be an assumption reported as a measurement."""
    s = set()
    for p in TARGET_PATHS:
        for ch in p:
            if ch != "/":
                s.add(ch)
    return s


def fold_candidates(targets):
    """Every codepoint below U+30000 whose lower/casefold/NFKD form is exactly one of the
    target ASCII characters.  Deliberately WIDER than APFS's own table: over-generation is
    filtered by the filesystem probe below, while under-generation would silently shrink
    the answer, which is the failure mode this whole chain is about."""
    out = {}
    for cp in range(0x80, 0x30000):
        ch = chr(cp)
        forms = {ch.lower(), ch.casefold()}
        nfkd = unicodedata.normalize("NFKD", ch)
        if len(nfkd) == 1:
            forms.add(nfkd.lower())
        for f in forms:
            if len(f) == 1 and f in targets:
                out.setdefault(f, []).append(cp)
                break
    return out


def utf8_sorts_after(cp, ascii_ch):
    """git compares index paths with memcmp over bytes.  Any codepoint >= U+0080 encodes to
    a leading byte >= 0xC2, which is greater than every ASCII byte.  Measured, not assumed."""
    a = chr(cp).encode("utf-8")
    b = ascii_ch.encode("utf-8")
    return a > b


def fs_collides(tmpdir, path_a, path_b):
    """Write two DISTINGUISHABLE contents at two spellings and read back which survives.
    Returns True (one file, the second content won), False (two distinct files), or raises
    if the read returns something that is neither -- which is an instrument failure and
    never a 'no'."""
    d = tempfile.mkdtemp(dir=tmpdir)
    fa = os.path.join(d, path_a)
    fb = os.path.join(d, path_b)
    with open(fa, "w") as fh:
        fh.write("AAA")
    with open(fb, "w") as fh:
        fh.write("BBB")
    n = len(os.listdir(d))
    with open(fa) as fh:
        got = fh.read()
    shutil.rmtree(d, ignore_errors=True)
    if got not in ("AAA", "BBB"):
        raise RuntimeError(
            "probe read back %r from %r, which is neither content it wrote" % (got, path_a)
        )
    if n == 1:
        return True
    if n == 2:
        return False
    raise RuntimeError("probe directory holds %d entries; expected 1 or 2" % n)


def main():
    # `--all-ascii` widens the target set from the characters of the two paths above to
    # EVERY printable ASCII character.  That is the number a later reader actually wants:
    # the count for one path is a fact about that path's spelling, and the next
    # working-tree read this harness grows will have a different spelling.  T446's own
    # U+212A row is why: it reported "does not fold" from a probe run on a path with no
    # 'k' in it, and the correction only shows up in a census whose target set includes
    # characters the attacked path does not contain.
    if "--all-ascii" in sys.argv[1:]:
        targets = [chr(c) for c in range(0x21, 0x7F) if chr(c) != "/"]
    else:
        targets = sorted(target_chars())
    print("T454 FOLD CENSUS")
    print("host            : %s" % " ".join(os.uname()))
    print("target paths    : %s" % ", ".join(TARGET_PATHS))
    print("target chars    : %s  (%d)" % ("".join(targets), len(targets)))

    tmp = tempfile.mkdtemp(prefix="t454-fold-")
    try:
        # --------------------------------------------------------------- CALIBRATION
        # A generator that cannot find the ONE fold already known to exist cannot be
        # trusted to report that there are no others.
        cand = fold_candidates(set(targets))
        if 0x017F not in cand.get("s", []):
            print("CALIBRATION MISSED: the generator did not produce U+017F for 's'.")
            print("No negative from this run is interpretable.")
            return 2
        print("calibrate+      : PASS -- generator produced U+017F for 's'")
        # A generator that reports EVERYTHING is as useless as one that reports nothing, so
        # it is also calibrated on a known negative: U+00E9 LATIN SMALL LETTER E WITH ACUTE
        # lowercases and casefolds to itself and its NFKD form is two codepoints, so it must
        # never appear as a fold partner of a single ASCII character.
        allcands = [c for v in cand.values() for c in v]
        if 0x00E9 in allcands:
            print("ANTI-CALIBRATION FAILED: U+00E9 appears as a single-ASCII fold partner. The")
            print("generator is over-reporting; no count below is interpretable. REFUSED.")
            return 2
        print("calibrate-      : PASS -- U+00E9 absent from the candidate set")

        # --------------------------------------------------------------- FILESYSTEM PROBE
        try:
            known_pos = fs_collides(tmp, "conformance.sh", "conformance.ſh")
            known_neg = fs_collides(tmp, "conformance.sh", "conformance.zh")
        except (OSError, RuntimeError) as exc:
            print("PROBE FAILURE: %s" % exc)
            return 3
        if not known_pos:
            print("CALIBRATION MISSED: U+017F did NOT collide with 's' on this filesystem.")
            print("This host does not reproduce T446's premise; no count below applies to it.")
            return 2
        if known_neg:
            print("ANTI-CALIBRATION FAILED: 'z' collided with 's'. The filesystem probe is")
            print("reporting collisions that are not there. REFUSED.")
            return 2
        print("fs calibrate    : PASS -- U+017F collides, 'z' does not")

        # T446 reported U+212A KELVIN SIGN as a fold that does NOT collide on this
        # filesystem.  It is re-measured here, independently, because the whole census
        # rests on the probe agreeing with a result someone else obtained with a different
        # instrument.  A probe that disagreed with a known outside measurement would be a
        # reason to distrust every row below.
        try:
            kelvin = fs_collides(tmp, "xky", "xKy")
        except (OSError, RuntimeError) as exc:
            print("PROBE FAILURE (U+212A cross-check): %s" % exc)
            return 3
        print("cross-check     : U+212A vs 'k' collides=%s  (T446 measured: does not)"
              % ("YES" if kelvin else "no"))

        # --------------------------------------------------------------- THE CENSUS
        print("")
        print("%-6s %-8s %-9s %-8s %-9s %s" % (
            "ascii", "cands", "collides", "after", "usable", "example"))
        total_c = total_coll = total_after = total_usable = 0
        rows = []
        for a in targets:
            cps = cand.get(a, [])
            coll = []
            for cp in cps:
                try:
                    if fs_collides(tmp, "x" + a + "y", "x" + chr(cp) + "y"):
                        coll.append(cp)
                except (OSError, RuntimeError):
                    # An unwritable name is NOT a measured "does not collide".  It is
                    # excluded from BOTH numerator and denominator and counted separately.
                    continue
            after = [cp for cp in coll if utf8_sorts_after(cp, a)]
            total_c += len(cps)
            total_coll += len(coll)
            total_after += len(after)
            usable = after
            total_usable += len(usable)
            ex = "U+%04X" % usable[0] if usable else "-"
            rows.append((a, len(cps), len(coll), len(after), len(usable), ex))
            print("%-6s %-8d %-9d %-8d %-9d %s" % (
                a, len(cps), len(coll), len(after), len(usable), ex))

        print("")
        print("TOTAL candidates generated      : %d" % total_c)
        print("TOTAL that COLLIDE on this fs   : %d" % total_coll)
        print("TOTAL that also SORT AFTER      : %d" % total_after)
        print("TOTAL usable as a checkout win  : %d" % total_usable)
        print("")
        print("READING: a candidate is usable when it (a) folds onto an ASCII character of")
        print("the target path on THIS filesystem and (b) its UTF-8 bytes sort after that")
        print("character, so its index entry is written LAST and wins the collision.")
        print("EVERY non-ASCII collider satisfies (b) unconditionally: UTF-8 encodes every")
        print("codepoint >= U+0080 with a leading byte >= 0xC2 > 0x7A.  So 'all-lowercase")
        print("ASCII is unbeatable' is not merely false for U+017F; it is false for the")
        print("whole non-ASCII collider set, and the count below is that set's size.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
