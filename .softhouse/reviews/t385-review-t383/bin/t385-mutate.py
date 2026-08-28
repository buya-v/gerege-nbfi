#!/usr/bin/env python3
# T385: exact-once textual replacement. Exits 9 (VOID) unless OLD occurs exactly once.
import sys
src, dst, oldf, newf = sys.argv[1:5]
s = open(src, encoding='utf-8').read()
old = open(oldf, encoding='utf-8').read()
new = open(newf, encoding='utf-8').read()
n = s.count(old)
if n != 1:
    sys.stderr.write("VOID: anchor occurs %d times, not 1\n" % n)
    sys.exit(9)
open(dst, 'w', encoding='utf-8').write(s.replace(old, new))
