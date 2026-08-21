#!/bin/bash
# T189 — build the exact byte fixtures the four prior attempts used.
# Bytes are the ones quoted in T157's handoff and the driver's addendum, not new spellings.
set -u
D="$1"
mkdir -p "$D"

# T157's exact fixture: invalid UTF-8 (\xe2 alone) mid-line, poison AFTER the anchor column.
printf 'zzz clean line before\n M poison_\xe2_after.go\n?? another_after.go\n' > "$D/a-utf8-e2.txt"

# driver's fixture (i): \xff\xfe invalid UTF-8.
printf 'keep-me\n\xff\xfe invalid bytes here\nalso-keep\n' > "$D/c-fffe.txt"

# driver's fixture (ii): a real NUL byte.
printf 'keep-me\n\x00binary\nalso-keep\n' > "$D/b-nul.txt"

# T157's "poison directly on the LOCK-matching line" fixture.
printf '?? .softhouse/LOCK\xe2\n M real_change.go\n' > "$D/d-lockline.txt"

# control: no poison at all, the real shape run_exit_guard sees.
printf '?? .softhouse/LOCK\n M real_change.go\n?? new_deliverable.go\n' > "$D/e-clean.txt"

# other invalid-UTF-8 spellings, to separate "invalid UTF-8" from "NUL" cleanly.
printf 'keep-me\nmid \xff poison\nalso-keep\n' > "$D/f-ff.txt"
printf 'keep-me\nmid \x80 poison\nalso-keep\n' > "$D/g-80.txt"
printf 'keep-me\nmid \xc0 poison\nalso-keep\n' > "$D/h-c0.txt"

# a high-density binary blob: many NULs + invalid bytes, i.e. unambiguously "binary".
printf 'keep-me\n\x00\x01\x02\xff\xfe\x00\x00 blob\nalso-keep\n' > "$D/i-blob.txt"
