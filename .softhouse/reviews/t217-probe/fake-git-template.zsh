#!/bin/zsh
# T217 -- fake `git` used ONLY inside this probe's PATH-shadowed scratch run.
# Passes every subcommand through to the REAL git except `push`, which hangs
# (models a stalled network call). run-push-case.zsh writes a copy of this
# under a scratch bin dir named literally `git`, ahead of the real one on
# PATH, so the SUBJECT's unqualified `git push` calls hit this instead.
# Never installed anywhere persistent; never touches the live repo.
REAL_GIT=/usr/bin/git
if [[ "$1" == "push" ]]; then
  print -r -- "$(date +%s.%N) fake-git: push invoked with: $*" >> "${T217_FAKEGIT_LOG:-/tmp/t217-fakegit.log}"
  exec /bin/sleep "${T217_HANG_SECS:-120}"
fi
exec "$REAL_GIT" "$@"
