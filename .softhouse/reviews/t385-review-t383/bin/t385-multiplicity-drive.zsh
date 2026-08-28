#!/bin/zsh
# ============================================================================
# T385 · INDEPENDENT RE-DRIVE of T383's multiplicity refusal on fire-program.sh
#
# Written from scratch by T385; it does NOT reuse T383's t383-red-drive.zsh.
# Expectations are POST-FIX, so the SAME driver is RED against the shipped file
# (main, dbb18b7b...) and GREEN against T383's file (5c4f0244...). That
# difference is the evidence.
#
# SAFETY. Every case mutates a COPY under /tmp/t385/w and drives it with
# `--probe` only, pointed at a throwaway repo (/tmp/t385/subject) and a /tmp
# LOG_DIR. FIRE_SNAPSHOT_OF / FIRE_SCRIPT_DIR / FIRE_REPO_SCRIPT /
# FIRE_NO_SNAPSHOT are unset first: a LIVE fire exports them and a child would
# otherwise announce the REAL repo copy as its origin (T383 s6; T380 hit it too).
# No lock is taken, nothing is dispatched, the shared checkout is never written.
#
# A replacement that does not occur EXACTLY ONCE scores VOID and never passes.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ="${1:?usage: t385-multiplicity-drive.zsh <wrapper-under-test>}"
SUBJ="${SUBJ:A}"
WORK=/tmp/t385/w-${SUBJ:t:r}
LIB=/tmp/t385/lib-worktree-prune.zsh
rm -rf "$WORK"; mkdir -p "$WORK/frag"

print -r -- "T385 multiplicity drive"
print -r -- "wrapper under test : $SUBJ"
print -r -- "sha256             : $(shasum -a 256 "$SUBJ" | awk '{print $1}')"
print -r -- "zsh                : $ZSH_VERSION"
print -r -- ""

typeset -i CHECKS=0 WRONG=0 VOID=0

cat > "$WORK/frag/anchor.txt" <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

typeset RC OUT
_case() {
  local id="$1" want_rc="$2" must="$3" mustnot="$4" note="$5"
  CHECKS+=1
  mkdir -p "$WORK/$id"
  cat > "$WORK/frag/$id.new"
  cp "$LIB" "$WORK/$id/"
  if ! /usr/bin/python3 /tmp/t385/mutate.py "$SUBJ" "$WORK/$id/fire-program.sh" \
        "$WORK/frag/anchor.txt" "$WORK/frag/$id.new" 2>"$WORK/$id/void.txt"; then
    VOID+=1; print -r -- "$id  VOID   $(cat "$WORK/$id/void.txt")"; return
  fi
  chmod +x "$WORK/$id/fire-program.sh"
  OUT="$(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs \
         /bin/zsh "$WORK/$id/fire-program.sh" --probe 2>&1)"
  RC=$?
  local verdict=ok
  (( RC == want_rc )) || verdict="WRONG(rc=$RC want=$want_rc)"
  if [[ -n "$must" && "$must" != "-" ]]; then
    print -r -- "$OUT" | LC_ALL=C grep -qE "$must" || verdict="WRONG(missing /$must/)"
  fi
  if [[ -n "$mustnot" && "$mustnot" != "-" ]]; then
    print -r -- "$OUT" | LC_ALL=C grep -qE "$mustnot" && verdict="WRONG(FORBIDDEN /$mustnot/ present)"
  fi
  [[ "$verdict" == ok ]] || WRONG+=1
  printf '%-6s %-42s rc=%-3d %s\n' "$id" "$verdict" "$RC" "$note"
  print -r -- "$OUT" | LC_ALL=C grep -E 'FATAL|tally VERIFIED|probe only|TALLY LINE' | sed 's/^/         | /'
}

# ---------------------------------------------------------------- CONTROLS --
_case d00 0 'tally VERIFIED by the wiring' 'TALLY LINE' \
  'CONTROL: one well-formed clean summary. THE FIRE MUST START.' <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d01 2 'printed NO TALLY LINE' '-' 'ZERO summary lines (printer removed).' <<'EOF'
  print -r -- "the summary printer has been removed"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d02 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  'EXACTLY ONE, failing. Must be the READERS message, not multiplicity.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
EOF

# ------------------------------------------------- THE FIVE T380/T383 DEFEATS
_case d03 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'TWO: failing THEN clean -- T380 F-T380-1 exact input. Shipped: rc 0, FIRE STARTS.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped"
EOF

_case d04 2 'printed 2 TALLY LINES' 'this is the READERS' \
  'TWO: clean THEN failing -- the head -1 mirror. Readers must NOT be blamed.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
EOF

_case d05 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'TWO IDENTICAL clean lines -- neither is wrong; the POPULATION is.' <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d06 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  'TRAILING WHITESPACE impostor beside a real failing line: must not silence it.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped "
EOF

_case d07 2 'printed NO TALLY LINE' '-' \
  'The ONLY summary carries TRAILING WHITESPACE: unrecognisable == absent.' <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped "
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d08 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'A summary line emitted as DATA inside a string. Shipped: rc 0, FIRE STARTS.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  _t385_data="ROWS=99 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0"
  print -r -- "$_t385_data"
EOF

_case d09 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'A summary on STDERR: the capture is 2>&1. Shipped: rc 0, FIRE STARTS.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -u2 -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped"
EOF

_case d10 0 'tally VERIFIED by the wiring' 'TALLY LINE' \
  'WRITE-boundary split (two writes, ONE line): must NOT be a false refusal.' <<'EOF'
  printf 'ROWS=%d FAIL_OPEN=%d ' $_n $_open
  printf 'FAIL_SHUT=%d SKIPPED=%d\n' $_shut $_skipped
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d11 2 'printed NO TALLY LINE' '-' \
  'LINE-boundary split: matches nothing, refuses under the zero arm.' <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open"
  print -r -- "FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case d12 0 'tally VERIFIED by the wiring' 'TALLY LINE' \
  'Lines that merely CONTAIN the token, prefixed and suffixed: no false multiplicity.' <<'EOF'
  print -r -- "note: ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped (end)"
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

# ------------------------------------ NEW DEFEATS T383 DID NOT LIST (T385) ---
_case n01 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'NEW: the summary emitted as a FILENAME the self-test echoes.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  _t385_d="$($FIRE_MKTEMP -d "${TMPDIR:-/tmp}/t385fn.XXXXXX")"
  : > "$_t385_d/ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0"
  for _t385_f in "$_t385_d"/*(N); do print -r -- "${_t385_f:t}"; done
EOF

_case n02 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  'NEW: CRLF impostor beside a real failing line -- CR must keep it OUT of the population.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  printf 'ROWS=%d FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=%d\r\n' $_n $_skipped
EOF

_case n03 2 'printed NO TALLY LINE' '-' \
  'NEW: the ONLY summary has a CRLF ending -- unrecognisable == absent, SHUT.' <<'EOF'
  printf 'ROWS=%d FAIL_OPEN=%d FAIL_SHUT=%d SKIPPED=%d\r\n' $_n $_open $_shut $_skipped
  (( _open == 0 && _shut == 0 )) || exit 1
EOF

_case n04 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  'NEW: UTF-8 FULLWIDTH DIGIT impostor must not join the population.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  printf 'ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=０\n'
EOF

_case n05 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  'NEW: UTF-8 NBSP as a field separator in an impostor.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  printf 'ROWS=45\u00a0FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0\n'
EOF

_case n06 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  'NEW: a NESTED REAL invocation of the self-test emits a second, genuine, clean summary.' <<'EOF'
  _open=1
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  if [[ -z "${T385_NESTED:-}" ]]; then
    T385_NESTED=1 /bin/zsh "${0:A}" --self-test-lock-readers 2>/dev/null | LC_ALL=C grep -E '^ROWS='
  fi
EOF

_case n07 2 'UNDERSTATES' 'OVERSTATES' \
  'NEW: an unreachable line matching the CENSUS selector -- census inflates, must refuse UNDERSTATES.' <<'EOF'
  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  (( _open == 0 && _shut == 0 )) || exit 1
  if false; then
_row t385fake nofile "1970-01-01T00:00:00Z" HELD "T385 census-inflation probe: never executed"
  fi
EOF

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then print -r -- "RESULT: PASS"; else print -r -- "RESULT: FAIL"; fi
