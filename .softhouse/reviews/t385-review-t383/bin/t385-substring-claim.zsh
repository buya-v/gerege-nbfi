#!/bin/zsh
# ============================================================================
# T385 · Is T383's STATED REASON for keeping substring containment green true?
#
# T383 writes, in the shipped source comment and again in its handoff:
#
#   "a line that merely CONTAINS the token -- `note: ... ROWS=45 ...`, or THIS
#    WIRING'S OWN `lockselftest| ROWS=...` ECHO -- is NOT in the population"
#   "the wiring's own `lockselftest| ROWS=` echo is a substring line, and a
#    naive `grep -c ROWS=` fix would have REFUSED EVERY HEALTHY FIRE."
#
# The population is computed over `$_ST_OUT`, which is captured as
#   _ST_OUT="$(/bin/zsh "$FIRE_SELF" --self-test-lock-readers 2>&1)"
# and the `lockselftest| ` prefix is added AFTERWARDS, only when each line is
# handed to log(). So the claim is testable three ways:
#
#   A. count `ROWS=` in the self-test's own output, anchored and unanchored;
#   B. run the wrapper and count `lockselftest| ROWS=` lines in the FIRE LOG;
#   C. build the "naive" wrapper T383 says would have refused every healthy
#      fire -- an UNANCHORED `grep -c 'ROWS='` over `$_ST_OUT` -- and drive the
#      healthy control at it.
#
# C is the decisive one and carries its own control (the shipped anchored file).
# --probe only, throwaway repo, no lock, nothing dispatched.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ=/tmp/t385/fixed.sh
WORK=/tmp/t385/sub
LIB=/tmp/t385/lib-worktree-prune.zsh
rm -rf "$WORK"; mkdir -p "$WORK/frag"

print -r -- "T385 substring-claim probe"
print -r -- "subject: $SUBJ  sha256=$(shasum -a 256 $SUBJ | awk '{print $1}')"
print -r -- ""

print -r -- "=== A. \$_ST_OUT itself: how many lines carry the token? ==="
typeset ST_OUT
ST_OUT="$(/bin/zsh "$SUBJ" --self-test-lock-readers 2>&1)"
print -r -- "  self-test rc                                  : $?"
print -r -- "  total lines in \$_ST_OUT                       : $(print -r -- "$ST_OUT" | wc -l | tr -d ' ')"
print -r -- "  lines matching UNANCHORED /ROWS=/             : $(print -r -- "$ST_OUT" | LC_ALL=C grep -c 'ROWS=')"
print -r -- "  lines matching the SHIPPED ANCHORED selector  : $(print -r -- "$ST_OUT" | LC_ALL=C grep -cE '^ROWS=[0-9]+ FAIL_OPEN=[0-9]+ FAIL_SHUT=[0-9]+ SKIPPED=[0-9]+$')"
print -r -- "  lines matching /lockselftest\\| ROWS=/          : $(print -r -- "$ST_OUT" | LC_ALL=C grep -c 'lockselftest| ROWS=' || true)"
print -r -- ""

print -r -- "=== B. the FIRE LOG (where the lockselftest| prefix is actually added) ==="
rm -rf /tmp/t385/logs-sub; mkdir -p /tmp/t385/logs-sub
cp "$LIB" "$WORK/"; cp "$SUBJ" "$WORK/fire-program.sh"; chmod +x "$WORK/fire-program.sh"
typeset RUN
RUN="$(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-sub /bin/zsh "$WORK/fire-program.sh" --probe 2>&1)"
print -r -- "  wrapper rc                                    : $?"
print -r -- "  'lockselftest| ROWS=' lines in the run output  : $(print -r -- "$RUN" | LC_ALL=C grep -c 'lockselftest| ROWS=')"
print -r -- "  -> so the substring line IS emitted on a healthy run, but into the LOG,"
print -r -- "     which is downstream of the capture the population is taken from."
print -r -- ""

print -r -- "=== C. THE DECISIVE TEST: build the 'naive grep -c ROWS=' wrapper and drive the healthy control ==="
cat > "$WORK/frag/old.txt" <<'EOF'
_ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep -E '^ROWS=[0-9]+ FAIL_OPEN=[0-9]+ FAIL_SHUT=[0-9]+ SKIPPED=[0-9]+$')"
EOF
cat > "$WORK/frag/new.txt" <<'EOF'
_ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep 'ROWS=')"
EOF
mkdir -p "$WORK/naive"; cp "$LIB" "$WORK/naive/"
if /usr/bin/python3 /tmp/t385/mutate.py "$SUBJ" "$WORK/naive/fire-program.sh" \
     "$WORK/frag/old.txt" "$WORK/frag/new.txt"; then
  chmod +x "$WORK/naive/fire-program.sh"
  typeset NOUT
  NOUT="$(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-sub /bin/zsh "$WORK/naive/fire-program.sh" --probe 2>&1)"
  typeset -i NRC=$?
  print -r -- "  NAIVE unanchored wrapper, HEALTHY input -> rc $NRC"
  print -r -- "$NOUT" | LC_ALL=C grep -E 'FATAL|tally VERIFIED|probe only' | sed 's/^/    | /'
  if (( NRC == 0 )); then
    print -r -- "  VERDICT: the naive unanchored count STARTS the healthy fire."
    print -r -- "           T383's stated reason -- that it 'would have refused every healthy fire'"
    print -r -- "           because of the wiring's own lockselftest| echo -- is FALSE as stated."
  else
    print -r -- "  VERDICT: the naive unanchored count REFUSES the healthy fire; T383's reason holds."
  fi
else
  print -r -- "  VOID: could not build the naive variant (anchor not unique)"
fi
print -r -- ""
print -r -- "=== C-control: the SHIPPED anchored wrapper on the same healthy input ==="
print -r -- "  rc $(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-sub /bin/zsh "$WORK/fire-program.sh" --probe >/dev/null 2>&1; print -r -- $?)  (must be 0)"
