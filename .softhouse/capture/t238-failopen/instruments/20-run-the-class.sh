#!/bin/bash
# T238 -- EXECUTE EVERY READ-ONLY CANDIDATE AND CLASSIFY IT BY MEASUREMENT, NOT BY READING.
#
# T234 named six dead-cd instruments and TESTED THREE. The other three were [UNVERIFIED].
# This runs all six, plus T234's OWN re-runner, and classifies each empirically.
#
# CLASSIFICATION RULE, stated so it is checkable:
#   FAIL-CLOSED  exit != 0.  A reader cannot mistake it for a result.
#   FAIL-OPEN    exit == 0 AND the output reads as a NEGATIVE or as a COMPLETE RESULT.
#     OPEN-SILENT        prints "(no hits)" / nothing -- reads as "the concept is absent"
#     OPEN-WRONG-CORPUS  prints PLAUSIBLE NUMBERS measured over a DIFFERENT tree than the
#                        one it names.  This is the WORSE shape: not silence, a confident
#                        wrong answer with no warning anywhere in the output.
#
# SAFETY / SCOPE, stated per P-66: three instruments in my census's lethal intersection
# MUTATE the tree (t184-vacuity.sh and t184-vacuity2.sh rewrite .softhouse/conformance.sh
# and restore it; verify_merge_t223.sh adds a remote and merges). They are NOT executed
# here -- .softhouse/conformance.sh is held by T243/T226 and is out of my scope. They are
# classified STATICALLY below, and that limitation is declared, not hidden.
set -u
ROOT="$(git rev-parse --show-toplevel)"
OUT="$ROOT/.softhouse/capture/t238-failopen/evidence/class-runs"
mkdir -p "$OUT"
cd "$ROOT" || exit 90

echo "T238 -- EMPIRICAL CLASSIFICATION OF THE FAIL-OPEN CLASS"
echo "commit : $(git rev-parse HEAD)"
echo "cwd    : $PWD"
echo "engines: /usr/bin/grep BSD 2.6.0-FreeBSD | git 2.50.1 | perl 5.034001 | ugrep ABSENT | rg not visible to a script"
echo "Each instrument is run VERBATIM, UNMODIFIED, from the repo root -- exactly as a later"
echo "auditor re-running the committed evidence would run it."
echo

probe() {   # probe <tag> <interpreter> <path> [args...]
  local tag="$1" interp="$2" path="$3"; shift 3
  local log="$OUT/$tag.txt"
  echo "=================================================================="
  echo "INSTRUMENT : $path"
  if [ ! -f "$path" ]; then echo "  ABSENT from this tree"; echo; return; fi
  local rc
  ( "$interp" "$path" "$@" ) >"$log" 2>&1
  rc=$?
  local lines nohits failev
  lines=$(wc -l <"$log" | tr -d ' ')
  nohits=$(LC_ALL=C /usr/bin/grep -c -i -a 'no hits\|^ *none$\|(none)' "$log" || true)
  failev=$(LC_ALL=C /usr/bin/grep -c -a -i 'No such file or directory\|not a git repository\|Traceback\|command not found' "$log" || true)
  printf '  exit status .............. %s\n' "$rc"
  printf '  output lines ............. %s\n' "$lines"
  printf '  "(no hits)"-shaped lines . %s\n' "$nohits"
  printf '  visible failure evidence . %s line(s)\n' "$failev"
  if [ "$rc" -ne 0 ]; then
    printf '  VERDICT .................. FAIL-CLOSED  (non-zero exit -- CORRECT)\n'
  elif [ "$nohits" -gt 0 ]; then
    printf '  VERDICT .................. FAIL-OPEN / OPEN-SILENT  <<< prints a negative it never measured\n'
  elif [ "$failev" -eq 0 ]; then
    printf '  VERDICT .................. FAIL-OPEN / OPEN-WRONG-CORPUS  <<< exit 0, plausible output, NO warning\n'
  else
    printf '  VERDICT .................. FAIL-OPEN / exit 0 but failure text is visible in output\n'
  fi
  echo "  --- first 14 lines of output ---"
  head -14 "$log" | sed -e 's/^/  | /'
  echo "  log: .softhouse/capture/t238-failopen/evidence/class-runs/$tag.txt"
  echo
}

echo "########## GROUP 1 -- THE THREE T234 ACTUALLY TESTED ##########"
echo
probe a2-31-probe-sweep bash .softhouse/reviews/a2-31-dec2-rev4/probe-sweep.sh
probe a2-32-sweep       bash .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-32-evidence/sweep.sh
probe a2-33-sweep       bash .softhouse/reviews/a2-33-dec2-rev5/sweep.sh REPO

echo "########## GROUP 2 -- THE THREE T234 LEFT [UNVERIFIED].  THIS IS THE TASK. ##########"
echo
probe a2-11-enumerate   python3 .softhouse/reviews/A2-11/enumerate-corpus.py
probe t184-census       bash .softhouse/reviews/T184-evidence/t184-census.sh
probe t184-sweep        bash .softhouse/reviews/T184-evidence/t184-sweep.sh

echo "########## GROUP 3 -- T234'S OWN RE-RUNNER ##########"
echo "########## It hard-codes T234's own worktree agent-a71e695cfa5bea70b, now deleted. ##########"
echo
probe t234-rerun        bash .softhouse/capture/t234-sweep-instrument-audit/instruments/20-rerun-dec2-sweeps.sh

echo "=================================================================="
echo "NOT EXECUTED (mutating; classified statically -- see handoff):"
echo "  .softhouse/reviews/T184-evidence/t184-vacuity.sh   rewrites .softhouse/conformance.sh"
echo "  .softhouse/reviews/T184-evidence/t184-vacuity2.sh  rewrites .softhouse/conformance.sh"
echo "  .softhouse/capture/t223-g8-region-predicate/src/verify_merge_t223.sh  adds a remote and merges"
echo "DONE."
