#!/bin/zsh
# T217 -- drive ONE (fire-program.sh, ceiling) pair through release_lock with
# a HANGING `git push`, content-bound to the same extraction contract T211
# proved works against both pre- and post-fix bytes.
#
# usage: run-push-case.zsh <fire-program.sh> <label> <ceiling_secs>
set -uo pipefail
HERE="${0:A:h}"
SRC=$1; LABEL=$2; CEIL=${3:-15}
T211_EXTRACT="${T211_EXTRACT:-$HERE/../../handoff/2026-08-21-run2-tierA-gl-accounting-A2/T211-probe/extract.py}"

export T217_REPO=/tmp/t217-scratch/repo-$LABEL
export T217_FRAG=/tmp/t217-scratch/frag-$LABEL
export T217_HANG_SECS=120
export T217_FAKEGIT_LOG=/tmp/t217-scratch/fakegit-$LABEL.log
BIN=/tmp/t217-scratch/bin-$LABEL

rm -rf "$T217_FRAG" "$T217_REPO" "$BIN"; mkdir -p "$T217_FRAG" "$BIN"
rm -f "$T217_FAKEGIT_LOG"

print -r -- "############################################################"
print -r -- "# CASE $LABEL   ceiling=${CEIL}s"
print -r -- "# subject bytes: $SRC"
print -r -- "# zsh: $(/bin/zsh --version)"
print -r -- "############################################################"

/usr/bin/python3 "$T211_EXTRACT" "$SRC" "$T217_FRAG" || exit 1

# scratch repo, LOCK present (mirrors T211's setup-scratch.zsh; no 'origin' --
# the fake git intercepts `push` before any network call is attempted)
mkdir -p "$T217_REPO/.softhouse"
LOCK_JSON="{\"holder\": \"local-launchd\", \"host\": \"$(hostname -s)\", \"pid\": 0, \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
( cd "$T217_REPO" \
  && git init -q -b main \
  && print -r -- baseline > .softhouse/tasks.json \
  && print -r -- "$LOCK_JSON" > .softhouse/LOCK \
  && git add -A \
  && git -c user.name=t217 -c user.email=t217@example.com commit -q -m baseline ) || exit 1

# a scratch bin dir containing a `git` that hangs on push, ahead of the real
# one on PATH for the subject process only (this shell's PATH is untouched)
cp "$HERE/fake-git-template.zsh" "$BIN/git"
chmod +x "$BIN/git"

print -r -- ""
SUBJECT_CMD="PATH=\"$BIN:\$PATH\" /bin/zsh \"$HERE/push-subject.zsh\""
/usr/bin/python3 "$HERE/spawn-push.py" "$SUBJECT_CMD" "$LABEL" "$CEIL"

print -r -- ""
print -r -- "=== post-mortem ==="
if [[ -r "$HERE/out-$LABEL.txt" ]]; then
  BODY=$(<"$HERE/out-$LABEL.txt")
  SAW_RETURN=0; SAW_WARN=0
  for L in ${(f)BODY}; do
    [[ "$L" == *"release_lock RETURNED after"* ]] && { print -r -- "OBSERVED  $L"; SAW_RETURN=1 }
    [[ "$L" == *"WARN: git push"* ]] && { print -r -- "OBSERVED  $L"; SAW_WARN=1 }
  done
  (( SAW_RETURN )) || print -r -- "OBSERVED  release_lock NEVER returned within the ceiling"
  (( SAW_WARN ))   || print -r -- "OBSERVED  no 'WARN: git push' line (push finished quietly, or timeout logic did not fire)"
else
  print -r -- "OBSERVED  no transcript at $HERE/out-$LABEL.txt"
fi
if [[ -f "$T217_REPO/.softhouse/LOCK" ]]; then
  print -r -- "LOCAL LOCK FILE = PRESENT-STRANDED"
else
  print -r -- "LOCAL LOCK FILE = released (rm -f runs before any git call, so this should be true in EVERY case)"
fi
if [[ -r "$T217_FAKEGIT_LOG" ]]; then
  print -r -- "fake-git push was invoked: YES ($(wc -l < $T217_FAKEGIT_LOG | tr -d ' ') time(s))"
else
  print -r -- "fake-git push was invoked: NO (release_lock's push code path never ran -- P-64 check)"
fi
# sweep any leftover fake-git sleep from this case
pkill -f "t217-scratch/bin-$LABEL/git push" 2>/dev/null && print -r -- "(swept a leftover hung fake-git)"
print -r -- ""
