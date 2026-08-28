#!/usr/bin/env python3
"""T409 -- verify T390's append BYTE-FOR-BYTE.

T390 claims it took .softhouse/capture/t388-accrual-capture/out/PROBES-APPEND-T388.tsv
VERBATIM via `cat >>` and did not retype it. This checks that literally, on bytes:

  1. digest of the in-tree source file (as of main, where T388 is already merged);
  2. digest of the same path at the T388 branch tip commit 977e37af, which is what T390
     said it compared against;
  3. main's PROBES.tsv must be a byte PREFIX of T390's PROBES.tsv  (nothing above the
     append was edited, retyped or reflowed);
  4. the source file's bytes must occur as one CONTIGUOUS run inside the appended tail;
  5. whatever else is in the tail is T390's own addition -- reported, not assumed.

Usage: python3 verify-append.py <main-probes> <t390-probes> <t388-source> <tip-source>
"""
import hashlib
import sys


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    with open(p, "rb") as f:
        return f.read()


main_p, t390_p, src_p, tip_p = sys.argv[1:5]
main_b, t390_b, src_b, tip_b = (read(p) for p in (main_p, t390_p, src_p, tip_p))

print("T409 APPEND VERIFICATION (bytes, not lines)")
print()
print("  main   PROBES.tsv      %6d bytes  sha256 %s" % (len(main_b), sha(main_b)))
print("  T390   PROBES.tsv      %6d bytes  sha256 %s" % (len(t390_b), sha(t390_b)))
print("  T388   append source   %6d bytes  sha256 %s   [%s]" % (len(src_b), sha(src_b), src_p))
print("  same path at tip       %6d bytes  sha256 %s   [%s]" % (len(tip_b), sha(tip_b), tip_p))
print()

ok = True

r = src_b == tip_b
print("  [1] in-tree source == same path at branch tip 977e37af : %s" % ("SAME" if r else "DIFFER"))
ok &= r
print("      T390's claimed digest 89b9ded0d45805562a318e437c4cfe336ace1778e4e7c612041e3402436520d8")
print("      measured             %s  -> %s"
      % (sha(src_b), "MATCH" if sha(src_b).startswith("89b9ded0d45805562a318e437c4cfe336ace1778e4e7c612041e3402436520d8") else "MISMATCH"))
ok &= sha(src_b) == "89b9ded0d45805562a318e437c4cfe336ace1778e4e7c612041e3402436520d8"
print()

r = t390_b.startswith(main_b)
print("  [2] main's PROBES.tsv is a byte PREFIX of T390's        : %s" % ("YES" if r else "NO -- SOMETHING ABOVE THE APPEND CHANGED"))
ok &= r
tail = t390_b[len(main_b):] if r else b""
print("      appended tail: %d bytes" % len(tail))
print()

idx = tail.find(src_b)
print("  [3] T388 source occurs CONTIGUOUSLY in the tail         : %s" % ("YES at offset %d" % idx if idx >= 0 else "NO -- RETYPED OR ALTERED"))
ok &= idx >= 0
print()

if idx >= 0:
    before = tail[:idx]
    after = tail[idx + len(src_b):]
    print("  [4] bytes BEFORE the verbatim block: %d" % len(before))
    print("      %r" % before[:200])
    print("  [5] bytes AFTER  the verbatim block: %d  (T390's own scheduler block)" % len(after))
    nrows = sum(1 for ln in after.split(b"\n") if ln.startswith(b"txn\t") or ln.startswith(b"cmd\t"))
    print("      registry rows in the after-block: %d" % nrows)
    for ln in after.split(b"\n"):
        if ln.startswith(b"txn\t") or ln.startswith(b"cmd\t"):
            print("        %s" % ln.decode()[:120])

# field-count discipline on every registry row of the final file
print()
print("  [6] every txn/cmd row of the final registry has >= 5 tab-separated fields")
bad = 0
for n, ln in enumerate(t390_b.split(b"\n"), 1):
    if ln.startswith(b"txn\t") or ln.startswith(b"cmd\t"):
        if len(ln.split(b"\t")) < 5:
            print("        SHORT ROW line %d: %r" % (n, ln[:120]))
            bad += 1
        if b"  " in ln.split(b"\t")[0]:
            print("        SPACE-FOR-TAB line %d" % n)
            bad += 1
print("      short/malformed rows: %d" % bad)
ok &= bad == 0

print()
print("VERDICT: %s" % ("APPEND IS VERBATIM AND NOTHING ABOVE IT MOVED" if ok else "APPEND VERIFICATION FAILED"))
sys.exit(0 if ok else 1)
