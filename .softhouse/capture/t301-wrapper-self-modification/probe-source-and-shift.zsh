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
  #
  # THE INSERTED LINES PRINT. The first draft of this leg inserted COMMENTS, and both
  # hypotheses -- "zsh already buffered the tail" and "zsh re-read at the shifted
  # offset" -- predict the identical output when the inserted bytes are silent.
  # Printing lines break the tie: only a re-read at a shifted offset can emit them.
  # The tail marker is flipped to REWRITTEN in the same write for the same reason.
  /usr/bin/python3 - "$@" <<'PY'
import sys
p, nbytes, anchor = sys.argv[1], int(sys.argv[2]), sys.argv[3]
b = open(p, 'rb').read()
i = b.index(anchor.encode())
chunk = b"print -r -- '  INSERTED-LINE zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz'\n"
pad = chunk * max(1, nbytes // len(chunk))
out = b[:i] + pad + b[i:]
out = out.replace(b'TAIL: ORIGINAL', b'TAIL: REWRITTEN')
out = out.replace(b'FN-BODY: ORIGINAL', b'FN-BODY: REWRITTEN')
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
  # collapse the (potentially thousands of) INSERTED-LINE prints to a count, but show
  # every OTHER line verbatim -- a mid-token resume shows up as a "command not found"
  # or parse error on a partial line, and that must not be summarised away.
  ( zsh "$S" 2>&1 | /usr/bin/awk '
      /INSERTED-LINE/ { n++; next }
      { print }
      END { if (n) printf "  [%d INSERTED-LINE prints executed -- the running shell READ BYTES ADDED AFTER IT STARTED]\n", n }' ) & subj=$!
  sleep 1
  insert_shape "$S" "$nb" "# filler 1400 "
  wait $subj; rc=$?
  after_i=$(/usr/bin/stat -f %i "$S"); after_b=$(/usr/bin/stat -f %z "$S")
  print -r -- "  inode $before_i -> $after_i   bytes $before_b -> $after_b   pipeline rc=$rc"
done

# Also the shape nobody has run: DELETING bytes above the tail (the file SHRINKS, so a
# saved offset can now point past a boundary or off the end entirely).
print -r -- ""
print -r -- "--- DELETE ~19000 bytes above the tail, SAME inode (file shrinks) ---"
S="$WORK/delete.zsh"; mksubject "$S"
before_i=$(/usr/bin/stat -f %i "$S"); before_b=$(/usr/bin/stat -f %z "$S")
( zsh "$S" 2>&1 ) & subj=$!
sleep 1
/usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.index(b'# filler 200 '); j = b.index(b'# filler 1400 ')
out = b[:i] + b[j:]
# discriminating, same reason as the insert legs
out = out.replace(b'TAIL: ORIGINAL', b'TAIL: REWRITTEN')
out = out.replace(b'FN-BODY: ORIGINAL', b'FN-BODY: REWRITTEN')
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
PY
wait $subj; rc=$?
print -r -- "  inode $before_i -> $(/usr/bin/stat -f %i "$S")   bytes $before_b -> $(/usr/bin/stat -f %z "$S")   subject rc=$rc"

# -------------------------------- part 2b: can the resume offset land MID-TOKEN? ----
# The insert legs above resumed cleanly (rc=0) because every inserted line was short, so
# whatever offset zsh resumed at was near a newline. The BRIEF's specific claim is
# stronger: "the remaining commands can be resumed at a shifted offset and MISPARSED."
# To test that, insert lines that are 4000 bytes long: the resume offset then almost
# certainly lands in the MIDDLE of one, and if zsh resumes blindly at a byte offset the
# partial line runs as a command and errors. If it still runs clean, zsh is realigning.
print -r -- ""
print -r -- "=== PART 2b — FORCE THE RESUME OFFSET INTO THE MIDDLE OF A LINE ==="
S="$WORK/midtoken.zsh"; mksubject "$S"
before_b=$(/usr/bin/stat -f %z "$S")
( zsh "$S" 2>&1 | /usr/bin/awk '
    /INSERTED-LONGLINE/ { n++; next }
    { print }
    END { if (n) printf "  [%d INSERTED-LONGLINE prints executed]\n", n }' ) & subj=$!
sleep 1
/usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.index(b'# filler 1400 ')
# one printed line, ~4000 bytes wide, repeated: any offset inside the block is
# overwhelmingly likely to be mid-line.
chunk = b"print -r -- '  INSERTED-LONGLINE " + b"q" * 3950 + b"'\n"
out = b[:i] + chunk * 6 + b[i:]
out = out.replace(b'TAIL: ORIGINAL', b'TAIL: REWRITTEN')
out = out.replace(b'FN-BODY: ORIGINAL', b'FN-BODY: REWRITTEN')
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
PY
wait $subj; rc=$?
print -r -- "  bytes $before_b -> $(/usr/bin/stat -f %z "$S")   pipeline rc=$rc"
print -r -- "  (any 'command not found' / parse error above = the offset landed mid-token:"
print -r -- "   CORRUPTION of the running fire, not a clean swap)"

# ------------------- part 2c: the ONLY configuration that can land mid-token ----
# Part 2b did not actually test what it set out to test, and saying so is the point.
# Call R the byte offset zsh has read up to when it blocks (Part 3 below measures
# R ~ 8 KB), and I the insertion point. Execution resumes at byte R OF THE NEW FILE:
#   * if I > R (parts 2 and 2b: insertion deep in the file, R ~8 KB) the resume point is
#     still in ORIGINAL bytes, zsh walks forward on line boundaries and reaches the
#     inserted block from its TOP -- which is exactly why all 6 long lines ran clean.
#     That leg could never have produced a mid-token resume.
#   * only I < R < I+len(block) puts the resume point INSIDE the inserted bytes.
# So: insert the long-line block just ABOVE the 8 KB mark. Then R lands ~700 bytes into
# a 4000-byte line, and if zsh resumes blindly at a byte offset the fragment runs as a
# command. This is the leg that can actually falsify "shifted offset -> misparse".
print -r -- ""
print -r -- "=== PART 2c — INSERT *ABOVE* THE READ POINT SO THE RESUME LANDS INSIDE A LINE ==="
S="$WORK/midtoken2.zsh"; mksubject "$S"
before_b=$(/usr/bin/stat -f %z "$S")
( zsh "$S" 2>&1 | /usr/bin/awk '
    /INSERTED-LONGLINE/ { n++; next }
    { print }
    END { if (n) printf "  [%d INSERTED-LONGLINE prints executed]\n", n }' ) & subj=$!
sleep 1
/usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.index(b'# filler 100 ')      # ~7.5 KB in: BELOW zsh's ~8 KB read point
chunk = b"print -r -- '  INSERTED-LONGLINE " + b"q" * 3950 + b"'\n"
out = b[:i] + chunk * 6 + b[i:]
out = out.replace(b'TAIL: ORIGINAL', b'TAIL: REWRITTEN')
out = out.replace(b'FN-BODY: ORIGINAL', b'FN-BODY: REWRITTEN')
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
sys.stderr.write("  insertion point I=%d, block len=%d, so bytes [%d,%d) are inserted\n"
                 % (i, len(chunk)*6, i, i+len(chunk)*6))
PY
wait $subj; rc=$?
print -r -- "  bytes $before_b -> $(/usr/bin/stat -f %z "$S")   pipeline rc=$rc"
print -r -- "  6 prints + clean = zsh realigned or R<I after all; FEWER than 6 with a"
print -r -- "  'command not found'/parse error = MID-TOKEN RESUME, the brief's claim."

# ------------------------------------------------- part 3: how far ahead does zsh read? ----
print -r -- ""
print -r -- "=== PART 3 — HOW FAR AHEAD HAS ZSH ALREADY READ? ==="
print -r -- "If zsh has already buffered the whole tail by the time it blocks, the hazard"
print -r -- "window is smaller than it looks. Walk the tail's distance from the sleep and"
print -r -- "find the boundary where an in-place rewrite stops reaching the running shell."
for n in 1 20 40 60 80 100 120 200 2000 20000; do
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

# --------------------- part 3b: measure the read point R exactly, with no shift ----
# Part 3 brackets R between two subjects; this one reads it off directly. The subject is
# a numbered ladder; the rewrite swaps ORIG -> MARK, four characters for four, so NOTHING
# SHIFTS and the only variable left is "how much had zsh already buffered". The first row
# that prints MARK is the row at byte offset R.
print -r -- ""
print -r -- "=== PART 3b — THE READ POINT R, MEASURED DIRECTLY (equal-length swap) ==="
S="$WORK/ladder.zsh"
{
  print -r -- "#!/bin/zsh"
  print -r -- "print -r -- 'ROW 0000 ORIG'"
  print -r -- "sleep 3"
  for i in {1..2000}; do printf "print -r -- 'ROW %04d ORIG'\n" $i; done
} > "$S"
LADDER_BYTES=$(/usr/bin/stat -f %z "$S")
( zsh "$S" 2>&1 ) > "$WORK/ladder.out" & subj=$!
sleep 1
/usr/bin/python3 - "$S" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
n = b.replace(b" ORIG'", b" MARK'")
assert len(n) == len(b), "swap must not shift a single byte"
f = open(p, 'r+b'); f.truncate(0); f.write(n); f.close()
PY
wait $subj
first_mark=$(/usr/bin/grep -n 'MARK' "$WORK/ladder.out" | head -1)
last_orig=$(/usr/bin/grep -n 'ORIG' "$WORK/ladder.out" | tail -1)
rows_total=$(/usr/bin/wc -l < "$WORK/ladder.out")
print -r -- "  ladder: $LADDER_BYTES bytes, 2001 rows, each row 26 bytes"
print -r -- "  rows printed: $rows_total   last ORIG: ${last_orig:-none}   first MARK: ${first_mark:-none}"
print -r -- ""
print -r -- "  --- the rows either side of the read boundary, VERBATIM ---"
if [[ -n "$first_mark" ]]; then
  fm_line=${first_mark%%:*}
  /usr/bin/sed -n "$(( fm_line > 4 ? fm_line - 4 : 1 )),$(( fm_line + 2 ))p" "$WORK/ladder.out" | while IFS= read -r l; do print -r -- "    $l"; done
  print -r -- ""
  print -r -- "  LOOK FOR A ROW THAT IS NEITHER 'ORIG' NOR 'MARK'. If one is there, zsh did not"
  print -r -- "  swap cleanly at a line boundary: its read buffer ENDED IN THE MIDDLE OF A TOKEN,"
  print -r -- "  and it completed that token from the REWRITTEN file -- a SPLICE of old bytes and"
  print -r -- "  new. Here the splice fell inside a quoted string so it printed harmlessly. In a"
  print -r -- "  real script the same splice can fall inside a command name, a variable name, an"
  print -r -- "  \`if\`/\`fi\`, or a heredoc delimiter, and then it is a syntax error or a WRONG"
  print -r -- "  COMMAND. Note this happened on an EQUAL-LENGTH edit: nothing shifted at all."
  /bin/cp "$WORK/ladder.out" "${LADDER_COPY:-/dev/null}" 2>/dev/null || true
fi
print -r -- ""
if [[ -n "$first_mark" ]]; then
  fm_row=${${first_mark#*ROW }%% *}
  print -r -- "  => zsh had buffered through row $((10#$fm_row - 1)); R ~ $(( (10#$fm_row) * 26 + 30 )) bytes"
  print -r -- "  => EVERY BYTE OF THE SCRIPT MORE THAN ~R PAST THE CURRENT COMMAND IS EXPOSED"
else
  print -r -- "  => no MARK row: zsh had buffered the whole $LADDER_BYTES-byte file"
fi

print -r -- ""
print -r -- "DONE"
