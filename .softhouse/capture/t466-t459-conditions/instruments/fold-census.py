#!/usr/bin/env python3
"""
T466 -- FOLD CENSUS, RE-DERIVED.  Answers C-T459-3 without inheriting either earlier count.

WHY THIS EXISTS AND WHY IT IS NOT T454's PROBE RE-RUN.  T454's fold_candidates() kept a
candidate only `if len(f) == 1` -- i.e. it asked "which single character folds onto a single
ASCII character".  A checkout collision does not need that.  The filesystem compares whole
NAMES, so any codepoint whose fold is a STRING that appears in a tracked path is a candidate,
however long that string is.  This probe therefore keeps MULTI-CHARACTER folds and reports
the image as a string.

THREE FACTS ARE MEASURED PER CANDIDATE AND NEVER ASSUMED:
  (1) FOLD    -- python's lower/casefold/NFKD gives an image made only of printable ASCII;
  (2) ORDER   -- the candidate's UTF-8 bytes sort AFTER the image's bytes (memcmp, which is
                 how git orders index entries; the LAST entry wins a checkout collision);
  (3) COLLIDE -- on THIS filesystem, writing both spellings in one directory yields ONE file.
Only a candidate that passes all three is a route.  (1) alone over-generates and (3) alone
cannot be enumerated, so both are run and the disagreement is printed.

LIVE TARGETS are then looked up in the TRACKED PATH LIST supplied on stdin -- a candidate with
no tracked path carrying its image is a route with nothing to attack, and saying so is the
difference between a census and a scare.

No path under the program's own directory is spelled as a literal here; the tracked path list
arrives on stdin.  (guard_dead_path_frontier.)
"""
import os
import shutil
import sys
import tempfile
import unicodedata

PRINTABLE = set(chr(c) for c in range(0x20, 0x7F))


def images(cp):
    """Every ASCII image python offers for this codepoint.  Wider than any one filesystem's
    table on purpose: over-generation is filtered by the live filesystem probe below, while
    under-generation would silently shrink the answer -- the exact failure this chain is
    about."""
    ch = chr(cp)
    forms = {ch.lower(), ch.casefold(), unicodedata.normalize("NFKD", ch).lower()}
    out = set()
    for f in forms:
        if f and f != ch and all(c in PRINTABLE for c in f):
            out.add(f)
    return out


def sorts_after(cp, image):
    return chr(cp).encode("utf-8") > image.encode("utf-8")


def collides(tmpdir, name_a, name_b):
    """Write two DISTINGUISHABLE contents at two spellings in one fresh directory and read
    back.  ONE entry, plus B's bytes under A's name, is a collision.  A read that returns
    neither content is an INSTRUMENT failure and is raised, never reported as 'no'."""
    d = tempfile.mkdtemp(dir=tmpdir)
    try:
        with open(os.path.join(d, name_a), "w") as fh:
            fh.write("AAA")
        with open(os.path.join(d, name_b), "w") as fh:
            fh.write("BBB")
        n = len(os.listdir(d))
        with open(os.path.join(d, name_a)) as fh:
            got = fh.read()
    except (OSError, UnicodeError) as exc:
        shutil.rmtree(d, ignore_errors=True)
        raise RuntimeError("probe could not write %r / %r: %s" % (name_a, name_b, exc))
    shutil.rmtree(d, ignore_errors=True)
    if got not in ("AAA", "BBB"):
        raise RuntimeError("probe read back %r, which is neither content it wrote" % (got,))
    return n == 1 and got == "BBB"


def main():
    tracked = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]
    if len(tracked) < 100:
        sys.stderr.write("REFUSED: tracked path list on stdin has %d rows; this repository "
                         "tracks thousands. An empty corpus finds no live target and would "
                         "report the class shut.\n" % len(tracked))
        return 3

    tmp = tempfile.mkdtemp(prefix="t466-fold-")
    try:
        # CALIBRATION (P-72) BEFORE ANY NEGATIVE. U+017F is the route T446 drove and T454
        # closed; if this probe cannot re-find it, no zero it prints is believable.
        if not collides(tmp, "conformance.sh", "conformance.ſh"):
            sys.stderr.write("REFUSED: CALIBRATION FAILED -- U+017F does not collide on this "
                             "filesystem by this probe. The probe is broken, not the class.\n")
            return 3
        if collides(tmp, "aardvark.sh", "zebra.sh"):
            sys.stderr.write("REFUSED: NEGATIVE CONTROL FAILED -- two unrelated names "
                             "'collided'. The probe reports a collision it did not see.\n")
            return 3
        print("CALIBRATION: U+017F collides = yes; unrelated-name control collides = no.")

        cand = []          # (cp, image) passing fold + order
        for cp in range(0x80, 0x30000):
            for im in images(cp):
                if sorts_after(cp, im):
                    cand.append((cp, im))
        singles = [c for c in cand if len(c[1]) == 1]
        multis = [c for c in cand if len(c[1]) > 1]
        print("FOLD+ORDER CANDIDATES over printable ASCII: %d total "
              "(single-character image %d, MULTI-character image %d)"
              % (len(cand), len(singles), len(multis)))

        # THE FILESYSTEM IS THE ARBITER, and it is asked about EVERY candidate -- not only the
        # ones with something to attack. Filtering to live targets BEFORE the collision probe
        # would make the headline number a fact about this repository's file names rather than
        # about this volume, and the two must not be reported as one figure.
        confirmed = []
        for cp, im in sorted(set(cand)):
            probe_a = "t466probe" + im + ".txt"
            probe_b = "t466probe" + chr(cp) + ".txt"
            try:
                ok = collides(tmp, probe_a, probe_b)
            except RuntimeError as exc:
                print("  INSTRUMENT: U+%04X -> %r : %s" % (cp, im, exc))
                continue
            if ok:
                confirmed.append((cp, im, [p for p in tracked if im in p]))
        print("CONFIRMED COLLIDING ON THIS FILESYSTEM (fold + sorts-after + one file): %d"
              % len(confirmed))
        for cp, im, hits in confirmed:
            nm = unicodedata.name(chr(cp), "<unnamed>")
            print("  U+%04X %-46s -> %-5r live tracked targets %5d  e.g. %s"
                  % (cp, nm, im, len(hits), hits[0] if hits else "<NONE TRACKED>"))
        print("MULTI-CHARACTER-IMAGE MEMBERS OF THAT SET: %d"
              % len([1 for cp, im, _ in confirmed if len(im) > 1]))
        print("MEMBERS WITH AT LEAST ONE LIVE TRACKED TARGET: %d"
              % len([1 for _, _, h in confirmed if h]))
        print("MEMBERS WITH NO TRACKED TARGET IN THIS REPOSITORY (a route with nothing to "
              "aim at TODAY, not a closed one): %s"
              % ", ".join("U+%04X->%r" % (cp, im) for cp, im, h in confirmed if not h))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
