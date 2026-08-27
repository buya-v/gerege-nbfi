# shellcheck shell=bash
# T304 — FAIL-CLOSED GUARD AGAINST DESTROYING COMMITTED EVIDENCE.
#
# WHY THIS IS A GUARD AND NOT A COMMENT.  P-45, verbatim: "A test-only guard is not a
# guard. ... Rule: when hardening a check, verify the path that actually executes in
# CI/conformance calls it, not merely that a test does."  The generalisation this file
# applies is the same one: a warning in a handoff that says "expect a dirty tree
# afterwards, `git checkout --` those paths" enforces nothing, because it is read by the
# person who already knows and skipped by the person who does not.  The refusal below
# fires on the machine, at the moment of destruction, whether or not anybody remembered.
#
# T114 binds here: committed evidence is NAMED AND SUPERSEDED, never rewritten in place.
# An instrument that `rm -rf`s a committed evidence directory as a side effect of running
# defeats that ruling by a route nobody watches, and it is LATENT — the damage appears
# only when someone runs the instrument, which is exactly when they are not looking at
# `git status`.
#
# USE (one line, immediately after the target is assigned and before it is destroyed):
#
#     . "$(git rev-parse --show-toplevel)/.softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh"
#     EV="$(t304_evidence_root "$EV")" || exit 2
#
# BEHAVIOUR — three outcomes, no fourth:
#   0 tracked files under the target      -> echo the target unchanged, return 0.
#                                            It is a scratch path that merely LOOKS
#                                            tracked because its PARENT is tracked.
#   >0 tracked, T304_EVIDENCE_SCRATCH set -> echo <scratch>/<basename>, return 0.
#                                            This is the T114-sanctioned route: a scratch
#                                            copy, superseding rather than overwriting.
#   >0 tracked, no scratch root           -> print the count, the path and the exact
#                                            re-run line to stderr; return 2. REFUSE.
#
# There is deliberately NO boolean override (no T304_FORCE=1).  An override is a
# convention someone must remember, and P-45's whole content is that those enforce
# nothing.  The escape hatch is a REDIRECTION to a scratch root, which cannot silently
# destroy anything because it does not name the committed path at all.

t304_evidence_root() {
  t304__target="${1-}"
  if [ -z "$t304__target" ]; then
    echo "T304 GUARD REFUSED: t304_evidence_root called with no target." >&2
    return 2
  fi

  t304__root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "T304 GUARD REFUSED: not inside a git work tree, so 'is this tracked?' is" >&2
    echo "  unanswerable. A guard that cannot measure must refuse, not assume." >&2
    return 2
  }

  # A target OUTSIDE the repo work tree cannot hold tracked files, and `git ls-files`
  # answers "fatal: outside repository" rather than "0" -- which is an ERROR that would
  # read as a refusal. Separate the two explicitly: outside-the-repo is a MEASURED zero,
  # not an unmeasurable. Anything else git cannot answer still refuses, below.
  case "$t304__target" in
    /*) t304__abs="$t304__target" ;;
    *)  t304__abs="$(pwd)/$t304__target" ;;
  esac
  # Normalise "." and ".." without requiring the path to exist (realpath -m is not portable).
  t304__abs="$(printf '%s' "$t304__abs" | awk -F/ '{n=0;for(i=1;i<=NF;i++){if($i==""||$i==".")continue;if($i==".."){if(n>0)n--;continue}n++;a[n]=$i}s="";for(i=1;i<=n;i++)s=s"/"a[i];if(s=="")s="/";print s}')"
  t304__rootn="${t304__root%/}"
  case "$t304__abs" in
    "$t304__rootn"|"$t304__rootn"/*) : ;;
    *) printf '%s\n' "$t304__target"; return 0 ;;
  esac

  # Count tracked files under the target. `git ls-files` is run from the repo root so the
  # answer does not depend on the caller's cwd.
  #
  # P-81, whose text is "`git grep` exits 1 on NO MATCH and >1 on ERROR, so a bad pathspec
  # printed the same reassuring absence as a genuine no-match ... `grep -c || echo 0`
  # [put] 'zero matches' and 'I broke' onto one printed zero."  `git ls-files` has the same
  # shape, and `| wc -l` is exactly that collapse: a git ERROR yields an empty stream and
  # `wc -l` prints 0, which would read as "nothing tracked" and let the rm through.
  # So git's own exit status is captured BEFORE the pipe, and a non-zero status refuses.
  t304__list="$(cd "$t304__root" && git ls-files -- "$t304__target" 2>/dev/null)"
  t304__rc=$?
  if [ "$t304__rc" -ne 0 ]; then
    echo "T304 GUARD REFUSED: git ls-files exited $t304__rc for" >&2
    echo "  $t304__target" >&2
    echo "  A failed measurement is not a measurement of zero (P-81)." >&2
    return 2
  fi
  if [ -z "$t304__list" ]; then
    t304__n=0
  else
    t304__n="$(printf '%s\n' "$t304__list" | wc -l | tr -d ' ')"
  fi
  case "$t304__n" in
    ''|*[!0-9]*)
      echo "T304 GUARD REFUSED: could not count tracked files under" >&2
      echo "  $t304__target  (count was '$t304__n')" >&2
      return 2 ;;
  esac

  if [ "$t304__n" -eq 0 ]; then
    printf '%s\n' "$t304__target"
    return 0
  fi

  if [ -n "${T304_EVIDENCE_SCRATCH-}" ]; then
    t304__base="$(basename "$t304__target")"
    t304__dest="${T304_EVIDENCE_SCRATCH%/}/$t304__base"
    mkdir -p "$t304__dest" || return 2
    echo "T304 GUARD: target holds $t304__n TRACKED files; redirected to scratch" >&2
    echo "  from: $t304__target" >&2
    echo "  to  : $t304__dest" >&2
    printf '%s\n' "$t304__dest"
    return 0
  fi

  {
    echo "T304 GUARD REFUSED — THIS RUN WOULD DESTROY COMMITTED EVIDENCE."
    echo
    echo "  target : $t304__target"
    echo "  holds  : $t304__n TRACKED files (git ls-files)"
    echo
    echo "  T114 binds: committed evidence is named and SUPERSEDED by a scratch copy,"
    echo "  never rewritten in place. This instrument rebuilds its evidence directory"
    echo "  from scratch on every run, so running it here would delete that committed"
    echo "  corpus and replace it with a fresh one under the same paths."
    echo
    echo "  To run it for a NEW answer, supply a scratch root:"
    echo
    echo "      T304_EVIDENCE_SCRATCH=\"\$(mktemp -d)\" bash $0"
    echo
    echo "  To read the committed answer instead, do not run it: the corpus is already"
    echo "  at the target path."
  } >&2
  return 2
}
