#!/usr/bin/env bash
# T389 -- verify T388's own integrity pins actually pin what they claim.
#
# Three separate checks, because they can fail independently:
#   1. MANIFEST.sha256 verifies against the committed bytes (no drift, nothing edited
#      after the digest was taken).
#   2. Every out/NAME.req.sha256 matches its out/NAME.req -- the wire-byte pin that
#      closes defect D-1 (an artefact under out/ carrying no record of what produced it).
#   3. Every out/NAME.sql.sha256 matches its out/NAME.sql -- the same pin on the SQL side.
#   4. COVERAGE: does MANIFEST.sha256 actually cover every committed file, or does it
#      digest a convenient subset? A manifest that omits files proves less than it looks.
set -u
D=/tmp/t389scratch/.softhouse/capture/t388-accrual-capture
cd "$D" || exit 2
rc=0

echo "T389 -- INTEGRITY OF T388's OWN PINS"
echo "tree: $D (extracted from commit 977e37af via git archive)"
echo

echo "== 1. MANIFEST.sha256 verification =="
lines=$(grep -c . MANIFEST.sha256)
echo "manifest lines: $lines"
if shasum -a 256 -c MANIFEST.sha256 > /tmp/t389-manifest-check.txt 2>&1; then
  echo "shasum -c: ALL OK"
else
  echo "shasum -c: *** FAILURES ***"; rc=1
fi
grep -v ': OK$' /tmp/t389-manifest-check.txt | head -20
echo "  files OK   : $(grep -c ': OK$' /tmp/t389-manifest-check.txt)"
echo "  files FAILED: $(grep -c ': FAILED' /tmp/t389-manifest-check.txt)"
echo

echo "== 2. wire-byte pins: out/NAME.req.sha256 vs out/NAME.req =="
n=0; bad=0
for s in out/*.req.sha256; do
  [ -e "$s" ] || continue
  n=$((n+1))
  want=$(awk '{print $1}' "$s")
  f="${s%.sha256}"
  got=$(shasum -a 256 "$f" | awk '{print $1}')
  if [ "$want" != "$got" ]; then echo "  MISMATCH $f"; bad=$((bad+1)); rc=1; fi
done
echo "  checked $n .req pins, mismatches: $bad"
echo

echo "== 3. SQL pins: out/NAME.sql.sha256 vs out/NAME.sql =="
n=0; bad=0
for s in out/*.sql.sha256; do
  [ -e "$s" ] || continue
  n=$((n+1))
  want=$(awk '{print $1}' "$s")
  f="${s%.sha256}"
  got=$(shasum -a 256 "$f" | awk '{print $1}')
  if [ "$want" != "$got" ]; then echo "  MISMATCH $f"; bad=$((bad+1)); rc=1; fi
done
echo "  checked $n .sql pins, mismatches: $bad"
echo

echo "== 4. COVERAGE: files present in the tree but ABSENT from MANIFEST.sha256 =="
find . -type f ! -name 'MANIFEST.sha256' | sed 's|^\./||' | sort > /tmp/t389-tree.txt
awk '{ $1=""; sub(/^ +/,""); print }' MANIFEST.sha256 | sed 's|^\*||' | sort > /tmp/t389-man.txt
echo "  files in tree (excl. manifest): $(wc -l < /tmp/t389-tree.txt | tr -d ' ')"
echo "  files named in manifest       : $(wc -l < /tmp/t389-man.txt | tr -d ' ')"
echo "  --- in tree but NOT in manifest ---"
comm -23 /tmp/t389-tree.txt /tmp/t389-man.txt | sed 's|^|    |'
echo "  --- in manifest but NOT in tree ---"
comm -13 /tmp/t389-tree.txt /tmp/t389-man.txt | sed 's|^|    |'
echo

echo "== 5. RED DRIVE: does the manifest actually detect a mutated byte? =="
cp out/T388-A01-runaccruals.req /tmp/t389-A01-backup
printf 'x' >> out/T388-A01-runaccruals.req
if shasum -a 256 -c MANIFEST.sha256 2>/dev/null | grep -q 'T388-A01-runaccruals.req: FAILED'; then
  echo "  OK -- one appended byte to out/T388-A01-runaccruals.req is DETECTED as FAILED."
else
  echo "  *** the manifest did NOT detect a mutated file -- the pin enforces nothing ***"
  rc=1
fi
cp /tmp/t389-A01-backup out/T388-A01-runaccruals.req
if shasum -a 256 -c MANIFEST.sha256 2>/dev/null | grep -q 'T388-A01-runaccruals.req: OK'; then
  echo "  CONTROL -- restored file verifies OK again."
else
  echo "  *** control run failed; the red drive is not interpretable ***"; rc=1
fi

echo
echo "OVERALL: exit $rc"
exit $rc
