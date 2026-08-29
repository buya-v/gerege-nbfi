#!/usr/bin/env python3
# T424's buffered-writer stand-in. Same construction T408 used for F-T408-4, kept deliberately
# identical in behaviour so the GREEN-AFTER is measured on the case that broke the guard --
# with one difference, in the harsher direction: the buffer is larger (1 MiB, not 64 KiB), so a
# whole realistic transcript fits inside it and NOTHING reaches the file until close(). That is
# a strictly stronger adversary than T408's.
#
# This is NOT a claim about any particular `tee` binary. It is a demonstration that a guard
# which re-reads a file a live writer owns has delegated its correctness to that writer.
import sys

path = sys.argv[1]
f = open(path, "w", buffering=1 << 20)
for line in sys.stdin:
    sys.stdout.write(line)
    sys.stdout.flush()   # the SCREEN stays live; only the FILE lags. This is the trap.
    f.write(line)
f.close()
