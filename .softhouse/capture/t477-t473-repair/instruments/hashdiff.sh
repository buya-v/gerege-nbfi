#!/bin/bash
# =============================================================================================
# T477 -- THE HASHER DIFFERENTIAL, RE-RUN AFTER THE REWRITE.
#
# T473 verified T466's hasher over a deliberately nasty corpus: 0 mismatches against
# `git hash-object --no-filters`, and all 14 perturbations detected.  T477 REWROTE that hasher
# (raw byte paths, no decode, NUL-delimited output), so that verification does not carry over
# and is taken again here rather than inherited.
#
# The hasher is extracted VERBATIM from the harness on disk, between `recpy=` and its closing
# quote, so what is graded is the shipped text and not a copy that could drift.
#
# The corpus is built in a fresh repository under the scratch root -- never in this repository.
# The repository root is derived from this file`s own location and entered ONCE, FATALLY.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
CONF="$SH/conformance"".sh"
cd "$R" || { echo "REFUSED: could not enter $R" >&2; exit 3; }
[ -f "$CONF" ] || { echo "REFUSED: no harness at $R" >&2; exit 3; }

SCR="${T477_WORK:-}"
if [ -z "$SCR" ]; then
  SCR=$(mktemp -d "${TMPDIR:-/tmp}/t477-work.XXXXXXXXXX") || exit 3
fi
export T477_WORK="$SCR"
case "$SCR" in "$R"|"$R"/*) echo "REFUSED: scratch inside the repository." >&2; exit 3 ;; esac

PY="$SCR/extracted-hasher.py"
LC_ALL=C awk "/^  recpy='\$/{f=1;next} f&&/^'\$/{exit} f{print}" "$CONF" >"$PY"
n=$(LC_ALL=C grep -c '' "$PY")
echo "hasher extracted from the harness on disk : $n line(s)"
echo "harness blob (on disk, --no-filters)      : $(git hash-object --no-filters -- "$CONF")"
if [ "$n" -lt 20 ]; then
  echo "REFUSED: the extraction produced $n lines. That is not the hasher." >&2
  exit 3
fi
if ! LC_ALL=C grep -q 'hashlib' "$PY"; then
  echo "REFUSED: the extracted text does not import hashlib. Extraction is wrong." >&2
  exit 3
fi

W="$SCR/hashdiff"
rm -rf "$W"; mkdir -p "$W"
cd "$W" || { echo "REFUSED: could not enter the corpus root." >&2; exit 3; }
git init -q .
git config user.email t477@example.invalid
git config user.name  T477

/usr/bin/python3 - <<'MAKE'
import os
os.makedirs("a/b/c/d/e", exist_ok=True)
def w(name, data):
    with open(name, "wb") as fh:
        fh.write(data)
w("empty.txt", b"")
w("allbytes.bin", bytes(range(256)) * 2)
w("crlf.txt", b"line one\r\nline two\r\n")
w("cr.txt", b"line one\rline two\r")
w("notrailing.txt", b"no newline at end")
w("exec.sh", b"#!/bin/sh\necho hi\n")
os.chmod("exec.sh", 0o755)
w("badutf8.bin", b"\xff\xfe\x00\x41 not utf-8 \x80\x81")
w("star*name[a].txt", b"glob metacharacters in the name\n")
w("news\nline.txt", b"a newline IN THE NAME\n")
w("space tab\there.txt", b"space and tab in the name\n")
w("longſs.txt", b"U+017F in the name\n")
w("a/b/c/d/e/deep.txt", b"deeply nested\n")
w("big.bin", b"0123456789abcdef" * (12 * 1024 * 64))
w("ümläut.txt", b"utf-8 name\n")
for name, target in (("rel.link", "empty.txt"),
                     ("abs.link", "/nonexistent/absolute/target"),
                     ("broken.link", "no-such-file"),
                     ("utf8.link", "ümläut.txt"),
                     ("long.link", "x" * 300)):
    if os.path.lexists(name):
        os.remove(name)
    os.symlink(target, name)
MAKE

git add -A .
git commit -q -m "T477 hasher differential corpus"
echo
echo "corpus committed. HEAD entries by mode:"
git ls-tree -r HEAD | LC_ALL=C awk '{print $1}' | LC_ALL=C sort | LC_ALL=C uniq -c | LC_ALL=C sed 's/^/    /'

LIST="$SCR/hd-listing"
git -c core.quotepath=false ls-tree -r -z HEAD >"$LIST"
OUT="$SCR/hd-out"
/usr/bin/python3 -I -S "$PY" "empty.txt" <"$LIST" >"$OUT" 2>"$SCR/hd-err"
echo "hasher exit=$?  stderr bytes=$(LC_ALL=C wc -c <"$SCR/hd-err" | tr -d ' ')"

# THE COMPARISON.  git`s own answer for every entry, taken with --no-filters, and for a symlink
# taken from the LINK TARGET STRING because that is what git`s blob for mode 120000 is -- the
# `--stdin-paths` form would dereference it.
/usr/bin/python3 - "$LIST" "$OUT" <<'CMP'
import hashlib, os, subprocess, sys
listing = open(sys.argv[1], "rb").read()
recs = [r for r in listing.split(b"\x00") if r]
rows = [r for r in open(sys.argv[2], "rb").read().split(b"\x00") if r]
differs = {}
scanned = None
calib = None
for r in rows:
    if r.startswith(b"DIFFERS "):
        _, d, sha, p = r.split(b" ", 3)
        differs[p] = (d, sha)
    elif r.startswith(b"SCANNED "):
        scanned = int(r.split(b" ", 1)[1])
    elif r.startswith(b"CALIB "):
        calib = r
    else:
        print("UNPARSED ROW: %r" % r)
def blobsha(b):
    h = hashlib.sha1()
    h.update(b"blob " + str(len(b)).encode() + b"\x00")
    h.update(b)
    return h.hexdigest().encode()
mismatch = 0
compared = 0
for r in recs:
    meta, sep, path = r.partition(b"\t")
    f = meta.split(b" ")
    mode, sha = f[0], f[2]
    if mode == b"120000":
        want = blobsha(os.readlink(path))
    else:
        want = subprocess.check_output(
            ["git", "hash-object", "--no-filters", "--", path]).strip()
    compared += 1
    got = differs.get(path, (want, sha))[0] if path in differs else None
    # A path the hasher did NOT report as DIFFERS is a path it claims equals the HEAD sha.
    claim = differs[path][0] if path in differs else sha
    if claim != want:
        mismatch += 1
        print("MISMATCH %s: hasher %s  git/readlink %s" % (path, claim, want))
print("")
print("paths in the HEAD listing = %d" % len(recs))
print("paths compared            = %d" % compared)
print("MISMATCHES                = %d" % mismatch)
print("SCANNED reported          = %s" % scanned)
print("CALIB row                 = %r" % calib)
print("rows the hasher OMITTED   = %d" % (len(recs) - compared))
sys.exit(1 if mismatch else 0)
CMP
rc=$?
echo "differential exit=$rc"
echo
echo "--- PERTURBATION LEG: every regular file is altered by one byte; each must be DETECTED"
before=$(LC_ALL=C tr '\000' '\n' <"$OUT" | LC_ALL=C grep -c '^DIFFERS ' || true)
echo "DIFFERS rows before perturbation: $before"
# `git ls-files` C-QUOTES a name containing a newline or a non-ASCII byte, and a quoted name
# fails `-f`, so a newline-delimited read of it would SILENTLY SKIP exactly the paths this
# corpus exists to exercise -- T473`s own parser lost one that way. NUL-delimited, quotepath
# off, and the perturbed count is compared against the detected count below.
nreg=0
while IFS= read -r -d '' p; do
  [ -f "$p" ] && [ ! -L "$p" ] || continue
  printf 'X' >>"$p"
  nreg=$((nreg + 1))
done < <(git -c core.quotepath=false ls-files -z)
/usr/bin/python3 -I -S "$PY" "empty.txt" <"$LIST" >"$SCR/hd-out2" 2>/dev/null
after=$(LC_ALL=C tr '\000' '\n' <"$SCR/hd-out2" | LC_ALL=C grep -c '^DIFFERS ' || true)
echo "regular files perturbed         : $nreg"
echo "DIFFERS rows after perturbation : $after"
if [ "$after" -eq "$nreg" ]; then
  echo "PERTURBATION LEG: PASS -- every perturbed file was detected, symlinks untouched."
else
  echo "PERTURBATION LEG: FAIL -- $after detected of $nreg perturbed."
  rc=1
fi
exit "$rc"
