#!/bin/zsh
# ============================================================================
# T400 · F-T385-1 RE-MEASUREMENT on T400's own file, plus the HEALTHY-FIRE CONTROL.
#
# A. the population `$_ST_OUT` — how many lines carry the summary token, anchored,
#    unanchored, and with the wiring's `lockselftest| ` prefix;
# B. the FIRE LOG — where that prefix is actually added (downstream of the capture);
# C. DECISIVE — build the naive UNANCHORED `grep 'ROWS='` wrapper and drive the
#    healthy control at it. T383 said such a fix "would have refused every healthy
#    fire". T385 measured rc 0. This re-measures it on T400's file.
# D. HEALTHY-FIRE CONTROL — the shipped (T400) wrapper, unmutated, must START.
#    "A control that refuses everything is the same defect as one that cannot fail."
#
# --probe only, throwaway repo /tmp/t400/subject, /tmp LOG_DIR, snapshot vars unset.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ="${1:-/tmp/t400/fixed.sh}"; SUBJ="${SUBJ:A}"
WORK=/tmp/t400/sub; rm -rf "$WORK"; mkdir -p "$WORK/frag" /tmp/t400/logs-sub
LIB=/tmp/t400/lib-worktree-prune.zsh

print -r -- "T400 substring-claim re-measurement + healthy-fire control"
print -r -- "subject: $SUBJ  sha256=$(shasum -a 256 $SUBJ | awk '{print $1}')"
print -r -- ""

print -r -- "=== A. \$_ST_OUT itself: how many lines carry the token? ==="
typeset ST_OUT; typeset -i ST_RC
ST_OUT="$(/bin/zsh "$SUBJ" --self-test-lock-readers 2>&1)"; ST_RC=$?
print -r -- "  self-test rc                                  : $ST_RC"
print -r -- "  total lines in \$_ST_OUT                       : $(print -r -- "$ST_OUT" | wc -l | tr -d ' ')"
print -r -- "  lines matching UNANCHORED /ROWS=/             : $(print -r -- "$ST_OUT" | LC_ALL=C grep -c 'ROWS=')"
print -r -- "  lines matching the SHIPPED ANCHORED selector  : $(print -r -- "$ST_OUT" | LC_ALL=C grep -cE '^ROWS=[0-9]+ FAIL_OPEN=[0-9]+ FAIL_SHUT=[0-9]+ SKIPPED=[0-9]+$')"
print -r -- "  lines matching /lockselftest\\| ROWS=/          : $(print -r -- "$ST_OUT" | LC_ALL=C grep -c 'lockselftest| ROWS=')"
print -r -- "  the unanchored match(es), verbatim:"
print -r -- "$ST_OUT" | LC_ALL=C grep 'ROWS=' | sed 's/^/    > /'
print -r -- ""

print -r -- "=== B. the FIRE LOG (where the lockselftest| prefix is added) ==="
cp "$LIB" "$WORK/"; cp "$SUBJ" "$WORK/fire-program.sh"; chmod +x "$WORK/fire-program.sh"
typeset RUN; typeset -i RRC
RUN="$(GEREGE_NBFI_REPO=/tmp/t400/subject LOG_DIR=/tmp/t400/logs-sub /bin/zsh "$WORK/fire-program.sh" --probe 2>&1)"; RRC=$?
print -r -- "  wrapper rc                                    : $RRC"
print -r -- "  'lockselftest| ROWS=' lines in the run output  : $(print -r -- "$RUN" | LC_ALL=C grep -c 'lockselftest| ROWS=')"
print -r -- "  -> emitted on a healthy run, but into the LOG, which is DOWNSTREAM of the"
print -r -- "     capture the population is taken from. It can never join the population."
print -r -- ""

print -r -- "=== C. DECISIVE: the naive UNANCHORED wrapper on healthy input ==="
cat > "$WORK/frag/old.txt" <<'EOF'
_ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep -E '^ROWS=[0-9]+ FAIL_OPEN=[0-9]+ FAIL_SHUT=[0-9]+ SKIPPED=[0-9]+$')"
EOF
cat > "$WORK/frag/new.txt" <<'EOF'
_ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep 'ROWS=')"
EOF
mkdir -p "$WORK/naive"; cp "$LIB" "$WORK/naive/"
if /usr/bin/python3 /tmp/t400/mutate.py "$SUBJ" "$WORK/naive/fire-program.sh" \
     "$WORK/frag/old.txt" "$WORK/frag/new.txt"; then
  chmod +x "$WORK/naive/fire-program.sh"
  typeset NOUT; typeset -i NRC
  NOUT="$(GEREGE_NBFI_REPO=/tmp/t400/subject LOG_DIR=/tmp/t400/logs-sub /bin/zsh "$WORK/naive/fire-program.sh" --probe 2>&1)"; NRC=$?
  print -r -- "  NAIVE unanchored wrapper, HEALTHY input -> rc $NRC"
  print -r -- "$NOUT" | LC_ALL=C grep -E 'FATAL|tally VERIFIED|probe only' | cut -c1-180 | sed 's/^/    | /'
  if (( NRC == 0 )); then
    print -r -- "  VERDICT: the naive unanchored count STARTS the healthy fire on T400's file too."
    print -r -- "           T383's stated reason is FALSE as stated; T385's measurement reproduces."
  else
    print -r -- "  VERDICT: it REFUSES -- T383's reason would hold. (T385 measured rc 0.)"
  fi
else
  print -r -- "  VOID: could not build the naive variant (anchor not unique)"
fi
print -r -- ""

print -r -- "=== D. HEALTHY-FIRE CONTROL: the shipped T400 wrapper, unmutated ==="
print -r -- "  rc $RRC  (must be 0 -- a control that refuses everything is the same defect"
print -r -- "            as one that cannot fail)"
print -r -- "$RUN" | LC_ALL=C grep -E 'FATAL|tally VERIFIED|probe only' | cut -c1-200 | sed 's/^/    | /'
print -r -- ""
if (( ST_RC == 0 && RRC == 0 )); then
  print -r -- "RESULT: PASS -- self-test rc 0 and the healthy fire STARTS."
else
  print -r -- "RESULT: FAIL -- self-test rc $ST_RC, wrapper rc $RRC"
fi
