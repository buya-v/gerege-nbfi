#!/bin/sh
# T99 F-4 — `t36/out/recapture-gerege/` CARRIES NO CAPTURED-FROM-TENANT STAMP, SO EVIDENCE THAT
# PREDATES THE STAMP CANNOT BE TOLD APART FROM EVIDENCE WHOSE STAMP WAS REMOVED.
#
# The remedy chosen is the external, committed, CONTENT-ADDRESSED provenance record —
# PROVENANCE-INDEX.json plus provenance.py — and NOT a re-capture.  The reasoning is in
# provenance.py's header; the short form is that a stamp written today would attest to today's run,
# not to the run of 18 August whose bytes are committed, and re-capturing would overwrite the very
# bytes six other capture sets are proved byte-identical to.  No capture's bytes are edited by
# anything in this task: `emit` writes exactly one file, at the tree root.
#
# This proof has to do two different jobs, so it has two halves:
#   4a-4d  THE AMBIGUITY IS REAL AND IS NOW DETECTED — the same tampering run against the pre-fix
#          tree (where nothing can see it) and the fixed tree (where it is named).
#   4e     THE RECORD IS DISCOVERABLE FROM THE CAPTURE, not merely filed near it: the link is the
#          sha256 of the capture's own bytes, so renaming the file, moving it to a directory of its
#          own, or stripping every neighbour still finds the record — and changing one byte loses
#          it, which is correct, because those bytes are then not that capture.
#
# Entirely hermetic: no oracle, no network, no docker.  All tampering happens in the /tmp export.
. "$(dirname "$0")/lib.sh"

PY=python3
STAMPED=t80/out/recapture-gerege          # stamped: written after the mechanism landed
UNSTAMPED=t36/out/recapture-gerege        # the directory the finding names: predates it

echo "=== T99 F-4 — 'no stamp because it predates the mechanism' vs 'no stamp because it was removed'"
t99_export
echo

prefix_admitted=0
fixed_refused=0

# ------------------------------------------------------- 4a. the ambiguity, on the pre-fix tree
echo "--- 4a.prefix — delete the stamp from a directory that HAS one, then compare the two"
rm -f "$P/$STAMPED/CAPTURED-FROM-TENANT"
for d in "$STAMPED" "$UNSTAMPED"; do
  echo "  $d: stamp present? $( [ -f "$P/$d/CAPTURED-FROM-TENANT" ] && echo yes || echo no )   files: $(ls -A "$P/$d" | wc -l | tr -d ' ')"
done
echo "  a reader handed this tree can consult:"
echo "    PROVENANCE-INDEX.json : $( [ -f "$P/PROVENANCE-INDEX.json" ] && echo present || echo 'ABSENT' )"
echo "    provenance.py         : $( [ -f "$P/provenance.py" ] && echo present || echo 'ABSENT' )"
if [ ! -f "$P/$STAMPED/CAPTURED-FROM-TENANT" ] && [ ! -f "$P/$UNSTAMPED/CAPTURED-FROM-TENANT" ] \
   && [ ! -f "$P/PROVENANCE-INDEX.json" ]; then
  prefix_admitted=1
  echo "  VERDICT: both directories now present the same state — no stamp — and the tree carries"
  echo "           nothing that distinguishes the one that never had a stamp from the one whose"
  echo "           stamp was just deleted.  That is the finding."
fi
echo

echo "--- 4a.fixed — the same deletion against this branch's tree"
rm -f "$F/$STAMPED/CAPTURED-FROM-TENANT"
$PY "$F/provenance.py" verify --root "$F" > "$EXPORT/f4a.txt" 2>&1
echo "  EXIT=$?"
sed 's/^/    /' "$EXPORT/f4a.txt" | cut -c1-200
if LC_ALL=C grep -qa "STAMP REMOVED $STAMPED" "$EXPORT/f4a.txt" \
   && ! LC_ALL=C grep -qa "STAMP REMOVED $UNSTAMPED" "$EXPORT/f4a.txt"; then
  echo "  VERDICT: the REMOVAL is named, and the directory that merely PREDATES the mechanism is"
  echo "           not accused.  The two cases are now different states, not the same state."
  fixed_refused=1
fi
git -C "$REPO" archive HEAD | tar -x -C "$EXPORT/fixed"   # restore the tampered file
echo

# ------------------------------------------ 4b. the opposite tamper: a stamp that was FABRICATED
echo "--- 4b — a stamp APPEARING on a directory recorded as predating the mechanism.  (This is not"
echo "         hypothetical: T99's author caused it by accident, running the recipe against the"
echo "         worktree instead of a /tmp export.  It was restored from git; here it is caught.)"
printf 'gerege\n' > "$F/$UNSTAMPED/CAPTURED-FROM-TENANT"
$PY "$F/provenance.py" verify --root "$F" > "$EXPORT/f4b.txt" 2>&1
echo "  EXIT=$?"
LC_ALL=C grep -a 'STAMP APPEARED\|UNACCOUNTED FILE\|^problems' "$EXPORT/f4b.txt" | cut -c1-200 | sed 's/^/    /'
git -C "$REPO" archive HEAD | tar -x -C "$EXPORT/fixed"
rm -f "$F/$UNSTAMPED/CAPTURED-FROM-TENANT"
echo

# ---------------------------------------------------------- 4c. a capture whose bytes were edited
echo "--- 4c — one edited byte in a committed capture"
$PY - "$F/$UNSTAMPED/B-01-baseline-raw.json" <<'EOF'
import sys
p = sys.argv[1]
b = bytearray(open(p, 'rb').read())
i = b.find(b'1')
b[i:i + 1] = b'2'
open(p, 'wb').write(bytes(b))
print('    flipped the first "1" to "2" at offset %d' % i)
EOF
$PY "$F/provenance.py" verify --root "$F" > "$EXPORT/f4c.txt" 2>&1
echo "  EXIT=$?"
LC_ALL=C grep -a 'BYTES MOVED\|^problems' "$EXPORT/f4c.txt" | cut -c1-200 | sed 's/^/    /'
git -C "$REPO" archive HEAD | tar -x -C "$EXPORT/fixed"
echo

# ------------------------------------------------- 4d. a capture directory the index never saw
echo "--- 4d — a new capture directory the index does not account for"
mkdir -p "$F/t99/out/smuggled-gerege"
printf '{"periods":[]}\n' > "$F/t99/out/smuggled-gerege/B-99-raw.json"
$PY "$F/provenance.py" verify --root "$F" > "$EXPORT/f4d.txt" 2>&1
echo "  EXIT=$?"
LC_ALL=C grep -a 'UNACCOUNTED DIRECTORY\|^problems' "$EXPORT/f4d.txt" | cut -c1-200 | sed 's/^/    /'
rm -rf "$F/t99/out/smuggled-gerege"
echo

# --------------------------------------------------------------- 4e. DISCOVERABILITY, the point
echo "--- 4e — discoverable FROM THE CAPTURE, not merely filed near it"
SRC=$F/$UNSTAMPED/B-01-baseline-raw.json
echo "  (i) in place — the index is found the way .git is, by ascending from the file itself:"
$PY "$F/provenance.py" whence "$SRC" 2>&1 | sed 's/^/      /' | cut -c1-200
echo
echo "  (ii) renamed, and moved to a directory of its own with no neighbours and no transcript:"
mkdir -p "$F/t99/out/nowhere"
cp "$SRC" "$F/t99/out/nowhere/8f31c0d2.bin"
$PY "$F/provenance.py" whence "$F/t99/out/nowhere/8f31c0d2.bin" 2>&1 \
  | LC_ALL=C grep -a 'sha256\|index\|FOUND as\|tenant:\|first commit' | sed 's/^/      /' | cut -c1-200
echo
echo "  (iii) moved OUT of the tree entirely — the ascent honestly fails, and the digest still"
echo "        finds the record when the index is named, which is what proves the link is the"
echo "        CONTENT and not the path:"
cp "$SRC" "$EXPORT/9c44ab10.bin"
$PY "$F/provenance.py" whence "$EXPORT/9c44ab10.bin" 2>&1 | sed 's/^/      /' | cut -c1-160
$PY "$F/provenance.py" whence "$EXPORT/9c44ab10.bin" --index "$F/PROVENANCE-INDEX.json" 2>&1 \
  | LC_ALL=C grep -a 'FOUND as\|tenant:\|basis:\|in-band stamp' | sed 's/^/      /' | cut -c1-200
echo
echo "  (iv) one byte changed — NOT FOUND, which is correct: those bytes are no longer that capture"
$PY - "$EXPORT/9c44ab10.bin" <<'EOF'
b = bytearray(open(__import__('sys').argv[1], 'rb').read())
b[-2:-1] = b'X'
open(__import__('sys').argv[1], 'wb').write(bytes(b))
EOF
$PY "$F/provenance.py" whence "$EXPORT/9c44ab10.bin" --index "$F/PROVENANCE-INDEX.json" 2>&1 \
  | LC_ALL=C grep -a 'sha256\|RESULT' | sed 's/^/      /' | cut -c1-160
rm -rf "$F/t99/out/nowhere"
echo

# ------------------------------------------------------- 4f. the verifier must not be vacuous
echo "--- 4f — the verifier is held to the same rule as F-3: it must not pass on an empty tree"
mkdir -p "$EXPORT/emptytree"
cp "$F/provenance.py" "$EXPORT/emptytree/"
$PY "$EXPORT/emptytree/provenance.py" emit --root "$EXPORT/emptytree" > "$EXPORT/f4f.txt" 2>&1
$PY "$EXPORT/emptytree/provenance.py" verify --root "$EXPORT/emptytree" >> "$EXPORT/f4f.txt" 2>&1
echo "  EXIT=$?  (2 = vacuous, refused)"
sed 's/^/    /' "$EXPORT/f4f.txt" | cut -c1-200
echo

# ---------------------------------------------------------------- 4g. and the honest state passes
echo "--- 4g — the untampered committed tree verifies clean"
$PY "$REPO/$PB/provenance.py" verify > "$EXPORT/f4g.txt" 2>&1
echo "  EXIT=$?"
sed 's/^/    /' "$EXPORT/f4g.txt"

t99_verdict "$prefix_admitted" "$fixed_refused" "F-4 (stamp-absence ambiguity)"
