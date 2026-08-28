#!/bin/bash
# T362 — P-25 float audit and prohibited-stack scan of T357's branch.
#
# THE FILE LIST IS DERIVED FROM GIT, NEVER TYPED. An earlier draft of this script carried
# a hard-coded list of the eleven files T357 adds or edits, and `bash .softhouse/conformance.sh`
# REFUSED with exit 2 on guard_dead_path_frontier: those paths exist on T357's branch and
# not in this reviewer's checkout, so every one of them was a dead repo-path reference. The
# guard was right, and its instruction is to REPAIR rather than pin. Deriving the list from
# `git diff --name-only` against T357's literal fork sha fixes both problems at once: no dead
# token, and the audit cannot go stale if T357's file set changes.
set -u
# TARGET TREE — passed in, never defaulted. See the sibling drive-red script's header.
C="${1:?usage: $0 <path to a main+T357 checkout to scan>}"
[ -d "$C/.git" ] || { echo "REFUSE: $C is not a git checkout" >&2; exit 9; }
FORK=e0819a7647befc6037c58784a70990e88fef0841   # LITERAL fork point of T357 (P-24)
TIP="${2:-softhouse/T357-a2-11-section1-red}"
git -C "$C" rev-parse --verify --quiet "$FORK^{commit}" >/dev/null \
  || { echo "REFUSE: $C does not contain T357's fork sha $FORK" >&2; exit 9; }
git -C "$C" rev-parse --verify --quiet "$TIP^{commit}" >/dev/null \
  || { echo "REFUSE: $C does not resolve the T357 ref $TIP" >&2; exit 9; }
# SCOPED TO T357'S OWN CONTRIBUTION, $FORK..$TIP — never $FORK..HEAD. On a merge result
# HEAD also carries every OTHER branch main absorbed since the fork, and an earlier draft
# of this script audited all of them: it reported conformance.sh's own prohibited-stack
# guard text as "ojdbc / mysql / 1521 added-line hits", which is a false alarm about a
# file T357 never touched. A scan whose population is wrong is worse than no scan.

echo "=== P-25 float scan of every CODE file T357 adds or edits ==="
echo "    (list DERIVED: git diff --name-only $FORK..$TIP, filtered to .py/.sh)"
FILES=$(git -C "$C" diff --name-only "$FORK..$TIP" | grep -E '\.(py|sh)$')
echo "    files: $(printf '%s\n' "$FILES" | grep -c .)"
echo
for f in $FILES; do
  printf '%-70s ' "$f"
  n=$(git -C "$C" show "$TIP:$f" | grep -cE 'float\(|float64|[^A-Za-z_][0-9]+\.[0-9]+|\bdouble\b')
  echo "hits=$n"
done
echo
echo "--- every hit, in context ---"
for f in $FILES; do
  git -C "$C" show "$TIP:$f" | grep -nE 'float\(|float64|[^A-Za-z_][0-9]+\.[0-9]+|\bdouble\b' | sed "s|^|  ${f##*/}:|"
done

echo
echo "=== AST float audit of every ADDED python file ==="
ADDED=$(git -C "$C" diff --name-only --diff-filter=A "$FORK..$TIP" | grep -E '\.py$')
python3 - "$C" "$TIP" $ADDED <<'PY'
import ast, subprocess, sys
root, tip = sys.argv[1], sys.argv[2]
for rel in sys.argv[3:]:
    src = subprocess.run(["git", "-C", root, "show", "%s:%s" % (tip, rel)],
                         capture_output=True, check=True).stdout.decode()
    t = ast.parse(src)
    lits = [n for n in ast.walk(t)
            if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    calls = [n for n in ast.walk(t) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "float"]
    imports = sorted({n.names[0].name.split(".")[0] for n in ast.walk(t)
                      if isinstance(n, ast.Import)}
                     | {n.module.split(".")[0] for n in ast.walk(t)
                        if isinstance(n, ast.ImportFrom) and n.module})
    print("  %-42s float_literals=%d float()_calls=%d imports=%s"
          % (rel.split("/")[-1], len(lits), len(calls), imports))
PY

echo
echo "=== prohibited-stack scan across the whole branch diff ==="
D="$(mktemp -t t362-stack)"
trap 'rm -f "$D"' EXIT
git -C "$C" diff "$FORK..$TIP" > "$D"
for t in ojdbc oracle.jdbc 1521 mysql mariadb Stripe Plaid Lithic Persona \
         docker-compose-mysql docker-compose-mariadb; do
  printf '  %-24s added-line hits=%s\n' "$t" "$(grep '^+' "$D" | grep -ic -- "$t")"
done
