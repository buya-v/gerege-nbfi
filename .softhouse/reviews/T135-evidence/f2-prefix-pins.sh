#!/bin/sh
# T135 — re-derive T99's four PIN_PREFIX_* digests against `git archive ab2de89` bytes, with Go.
set -u
B=/tmp/t135/f5/main/.softhouse/capture/pathb
GO=/Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/go
for pair in \
  "t36/recapture.sh:efccb0a4323628b45952a7e2dff12590e7dce3a2705ae66aa73aa53cd3b0d7d7" \
  "t36/preconditions.sh:7c68f2dcc539a27648f2fb0623927c1231c9b3729bdfb77eb01bd90e67ae876b" \
  "t80/forbidden-sentence.sh:71142e40b4af9ec873f0eca6a3ecb60d18033f2f0d37f75a2b29ffc4b9bf798f" \
  "t36/attest.py:0edced54a750fa17981af5a287b413c1a8298680ce2b7d4952087a14e61ce780" ; do
  f=${pair%%:*}; pin=${pair#*:}
  got=$($GO run /tmp/t135/f2/sha.go "$B/$f" | tail -1)
  if [ "$got" = "$pin" ]; then r="MATCHES pin"; else r="*** MISMATCH (pin $pin)"; fi
  printf '  %-28s %s  %s\n' "$f" "$got" "$r"
done
