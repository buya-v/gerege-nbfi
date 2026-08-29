#!/usr/bin/env python3
"""T459 independent fold census, re-derived. Two differences from T454's instrument, both
deliberate:

  (1) it does NOT restrict the ASCII image to a SINGLE character. T454's fold_candidates()
      keeps a candidate only `if len(f) == 1`, which excludes every MULTI-CHARACTER fold --
      U+00DF -> 'ss', U+FB00..FB06 -> 'ff'/'fi'/'fl'/'ffi'/'st'. Those collide on this
      volume (measured: <evidence>/01-multichar-folds.txt), so the exclusion is an
      UNDER-generation, which is the exact failure mode T454's own docstring warns about.
  (2) it reports the restricted set and the all-printable-ASCII set from one run.

Calibration, before any count is reported: U+017F MUST collide, and 'z' vs 'y' MUST NOT.
"""
import os, shutil, sys, tempfile, unicodedata

TARGET_PATHS = [".softhouse/conformance.sh", ".softhouse/guards"]
SCRATCH = os.environ.get("T459_WORK", "/tmp/t459") + "/work/census"

def fs_collides(a, b):
    os.makedirs(SCRATCH, exist_ok=True)
    d = tempfile.mkdtemp(dir=SCRATCH)
    fa, fb = os.path.join(d, a), os.path.join(d, b)
    open(fa, "w").write("AAA"); open(fb, "w").write("BBB")
    n = len(os.listdir(d)); got = open(fa).read()
    shutil.rmtree(d, ignore_errors=True)
    if got not in ("AAA", "BBB"): raise RuntimeError("probe read %r" % got)
    if n == 1: return True
    if n == 2: return False
    raise RuntimeError("probe dir holds %d entries" % n)

def sorts_after(cp, image):
    return chr(cp).encode() > image.encode()

def candidates(targets, maxlen):
    """codepoints >= U+0080 whose lower/casefold/NFKD image is a string of ASCII characters
    all of which are in `targets`, of length 1..maxlen."""
    out = []
    for cp in range(0x80, 0x30000):
        ch = chr(cp)
        forms = {ch.lower(), ch.casefold()}
        nf = unicodedata.normalize("NFKD", ch)
        if nf: forms.add(nf.lower())
        for f in forms:
            if 1 <= len(f) <= maxlen and all(c in targets for c in f):
                out.append((cp, f)); break
    return out

def run(label, targets, maxlen):
    cands = candidates(targets, maxlen)
    coll = []
    for cp, img in cands:
        a = "z" + img + ".txt"
        b = "z" + chr(cp) + ".txt"
        try:
            if fs_collides(a, b): coll.append((cp, img))
        except Exception as e:
            print("  PROBE FAILURE U+%04X: %s" % (cp, e)); sys.exit(3)
    after = [c for c in coll if sorts_after(c[0], c[1])]
    print("%s" % label)
    print("  candidates generated        : %d" % len(cands))
    print("  COLLIDE on this filesystem  : %d" % len(coll))
    print("  and SORT AFTER their image  : %d" % len(after))
    for cp, img in sorted(coll):
        print("     U+%04X %-38s -> %-4r  sorts-after=%s"
              % (cp, unicodedata.name(chr(cp), "?"), img, sorts_after(cp, img)))
    return len(cands), len(coll)

# --- calibration -----------------------------------------------------------------------
if not fs_collides("zs.txt", "zſ.txt"): print("CALIBRATION FAILED: U+017F"); sys.exit(2)
if fs_collides("zz.txt", "zy.txt"): print("CALIBRATION FAILED: z/y"); sys.exit(2)
print("calibration: U+017F collides, z/y distinct. OK\n")

tset = set(c for p in TARGET_PATHS for c in p if c != "/")
run("RESTRICTED to the characters of the two working-tree-read paths, SINGLE-char image only "
    "(T454's own selector):", tset, 1)
print()
run("RESTRICTED, images of length 1..3 (T459: multi-character folds INCLUDED):", tset, 3)
print()
ascii_printable = set(chr(c) for c in range(0x20, 0x7f)) - {"/"}
run("ALL PRINTABLE ASCII, SINGLE-char image only (T454's headline number):", ascii_printable, 1)
print()
run("ALL PRINTABLE ASCII, images of length 1..3 (T459):", ascii_printable, 3)
shutil.rmtree(SCRATCH, ignore_errors=True)
