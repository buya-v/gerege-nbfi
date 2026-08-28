#!/bin/zsh
# T301 PROBE B — TWO THINGS PROBE A CANNOT SEE.
#
# (1) THE SOURCED LIBRARY. fire-program.sh:87 does
#         source "$SCRIPT_DIR/lib-worktree-prune.zsh"
#     at the TOP of the fire, but the functions it defines are called HOURS later in the
#     tail (worktree prune, after the claude child exits). The brief flags this as a
#     candidate residual exposure because "its read timing differs from the main
#     script's". Reasoning says a sourced file is fully read and parsed at the `source`,
#     so a later edit cannot reach it -- but P-95 ("a fallback and a fail-open are
#     indistinguishable by reading") applies to interpreters too. MEASURE IT.
#
# (2) THE T288 SHAPE, WHICH T309 NEVER RAN. T309 leg B REPLACED a ~90 KB script wholesale
#     and saw the rewritten tail execute. T288's actual incident was an INSERTION -- 19 KB
#     added above the unread tail, shifting every later byte. Those are different
#     failure modes: a same-length swap resumes on a valid line boundary, an insertion
#     resumes at an offset that now points into the MIDDLE of something. The brief's
#     premise is specifically "seeks by BYTE OFFSET ... can be resumed at a shifted
#     offset and MISPARSED", and nobody has ever observed that. Observe it.
#
# READ THE MARKERS:
#   TAIL: ORIGINAL   the running shell was not affected
#   TAIL: REWRITTEN  the running shell executed bytes it never started with
#   a parse error / garbled output = the offset landed mid-token: CORRUPTION, not a swap
#   rc alone tells you nothing; T309 says so and it is right.

set -u
emulate -L zsh

WORK="$(mktemp -d "${TMPDIR:-/tmp}/t301-shift.XXXXX")"
print -r -- "zsh: $ZSH_VERSION"
print -r -- "uname: $(uname -sr)"
print -r -- "work: $WORK"

# ---------------------------------------------------------------- part 1: source ----
print -r -- ""
print -r -- "=== PART 1 — A SOURCED LIBRARY, EDITED AFTER THE \`source\` RETURNS ==="

mklib() {
  local f="$1" marker="$2"
  {
    print -r -- "# t301 lib"
    local i; for i in {1..400}; do print -r -- "# lib filler $i ----------------------------------------"; done
    print -r -- "libfn() { print -r -- 'LIB: $marker'; }"
  } > "$f"
}

for mode in inplace rename; do
  D="$WORK/src-$mode"; mkdir -p "$D"
  mklib "$D/lib.zsh" ORIGINAL
  cat > "$D/main.zsh" <<'MAIN'
#!/bin/zsh
SCRIPT_DIR="${0:A:h}"
source "$SCRIPT_DIR/lib.zsh"
print -r -- "  sourced; lib inode now $(/usr/bin/stat -f %i "$SCRIPT_DIR/lib.zsh")"
print -r -- "  READY"
sleep 3
libfn
MAIN
  print -r -- ""
  print -r -- "--- lib edited by $mode, AFTER source, BEFORE the call ---"
  print -r -- "  lib inode before: $(/usr/bin/stat -f %i "$D/lib.zsh")"
  ( zsh "$D/main.zsh" ) &
  subj=$!
  sleep 1
  mklib "$WORK/newlib-$mode" REWRITTEN
  if [[ $mode == inplace ]]; then
    cat "$WORK/newlib-$mode" > "$D/lib.zsh"          # same inode (probe A: INPLACE)
  else
    /bin/mv "$WORK/newlib-$mode" "$D/lib.zsh"        # new inode (probe A: RENAME)
  fi
  wait $subj
  print -r -- "  lib inode after:  $(/usr/bin/stat -f %i "$D/lib.zsh")"
  print -r -- "  lib on disk now says: $(/usr/bin/grep -o 'LIB: [A-Z]*' "$D/lib.zsh")"
done

# ------------------------------------------------- part 2: the T288 insertion shape ----
print -r -- ""
print -r -- "=== PART 2 — INSERTING BYTES ABOVE THE UNREAD TAIL (the T288 shape) ==="
print -r -- "Same inode every time. The question is not 'does the tail change' — T309"
print -r -- "settled that — it is 'does a SHIFTED offset resume on a line boundary'."

# subject: a long script that announces, sleeps, then runs a distinctive tail.
# The tail is deep enough that a 19 KB insertion above it moves it a long way.
mksubject() {
  local f="$1" ; local n="${2:-1500}"
  {
    print -r -- "#!/bin/zsh"
    print -r -- "print -r -- '  subject start (pid \$\$)'"
    print -r -- "sleep 3"
    local i; for i in $(seq 1 $n); do print -r -- "# filler $i ------------------------------------------------------------"; done
    print -r -- "print -r -- '  TAIL: ORIGINAL'"
    print -r -- "myfn() { print -r -- '  FN-BODY: ORIGINAL'; }"
    print -r -- "myfn"
    print -r -- "print -r -- '  subject end'"
  } > "$f"
}

insert_shape() {
  # $1 subject path, $2 bytes to insert, $3 anchor line to insert above
  /usr/bin/python3 - "$@" <<'PY'
import sys
p, nbytes, anchor = sys.argv[1], int(sys.argv[2]), sys.argv[3]
b = open(p, 'rb').read()
i = b.index(anchor.encode())
chunk = b'# INSERTED ' + b'z' * 60 + b'\n'
pad = chunk * (nbytes // len(chunk))
out = b[:i] + pad + b[i:]
# SAME INODE on purpose: r+b, truncate, write back.
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
PY
}

for nb in 200 19000; do
  S="$WORK/insert-$nb.zsh"
  mksubject "$S"
  before_i=$(/usr/bin/stat -f %i "$S"); before_b=$(/usr/bin/stat -f %z "$S")
  print -r -- ""
  print -r -- "--- insert ${nb} bytes above the tail, SAME inode ---"
  ( zsh "$S" ) & subj=$!
  sleep 1
  insert_shape "$S" "$nb" "# filler 1400 "
  wait $subj; rc=$?
  after_i=$(/usr/bin/stat -f %i "$S"); after_b=$(/usr/bin/stat -f %z "$S")
  print -r -- "  inode $before_i -> $after_i   bytes $before_b -> $after_b   subject rc=$rc"
done

# Also the shape nobody has run: DELETING bytes above the tail (the file SHRINKS, so a
# saved offset can now point past a boundary or off the end entirely).
print -r -- ""
print -r -- "--- DELETE ~19000 bytes above the tail, SAME inode (file shrinks) ---"
S="$WORK/delete.zsh"; mksubject "$S"
before_i=$(/usr/bin/stat -f %i "$S"); before_b=$(/usr/bin/stat -f %z "$S")
( zsh "$S" ) & subj=$!
sleep 1
/usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.index(b'# filler 200 '); j = b.index(b'# filler 1400 ')
out = b[:i] + b[j:]
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
PY
wait $subj; rc=$?
print -r -- "  inode $before_i -> $(/usr/bin/stat -f %i "$S")   bytes $before_b -> $(/usr/bin/stat -f %z "$S")   subject rc=$rc"

# ------------------------------------------------- part 3: how far ahead does zsh read? ----
print -r -- ""
print -r -- "=== PART 3 — HOW FAR AHEAD HAS ZSH ALREADY READ? ==="
print -r -- "If zsh has already buffered the whole tail by the time it blocks, the hazard"
print -r -- "window is smaller than it looks. Walk the tail's distance from the sleep and"
print -r -- "find the boundary where an in-place rewrite stops reaching the running shell."
for n in 1 20 200 2000 20000; do
  S="$WORK/dist-$n.zsh"; mksubject "$S" "$n"
  bytes=$(/usr/bin/stat -f %z "$S")
  ( zsh "$S" 2>&1 | /usr/bin/grep -E 'TAIL:' ) & subj=$!
  sleep 1
  /usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read().replace(b'TAIL: ORIGINAL', b'TAIL: REWRITTEN')
f = open(p, 'r+b'); f.truncate(0); f.write(b); f.close()
PY
  print -rn -- "  filler=$n (${bytes} bytes, tail ~$((bytes - 200)) B past the sleep): "
  wait $subj
done

print -r -- ""
print -r -- "DONE"
