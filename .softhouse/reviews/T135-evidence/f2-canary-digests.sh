#!/bin/sh
# T135 — re-derive BOTH canary digests with implementations OUTSIDE the rig.
set -u
SRC=/tmp/t135/f5/main/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json
MUT=/tmp/t135/f2/mutated.json
mkdir -p /tmp/t135/f2
sed 's/"principal": 1162502.5,/"principal": 1162502.55,/' "$SRC" > "$MUT"
echo "committed canary: $SRC"
echo "mutated copy:     $MUT  (one character: 1162502.5 -> 1162502.55)"
echo "byte diff:"
cmp -l "$SRC" "$MUT" 2>&1 | head -5
echo
for f in "$SRC" "$MUT"; do
  echo "--- $f"
  printf '  openssl      %s\n' "$(/usr/bin/openssl dgst -sha256 -r "$f" | cut -d' ' -f1)"
  printf '  python3      %s\n' "$(/usr/bin/python3 -I -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f")"
  printf '  sha256sum    %s\n' "$(/sbin/sha256sum "$f" 2>/dev/null | cut -d' ' -f1)"
  printf '  shasum(perl) %s\n' "$(/usr/bin/shasum -a 256 "$f" | cut -d' ' -f1)"
  printf '  go           %s\n' "$(/Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/go run /tmp/t135/f2/sha.go "$f" 2>&1 | tail -1)"
done
