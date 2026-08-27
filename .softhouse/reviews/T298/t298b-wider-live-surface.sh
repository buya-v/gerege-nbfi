#!/usr/bin/env bash
# T298 (resumed) — attack the load-bearing claim "ZERO LIVE EXECUTABLE HARDCODES".
# T256 measured conformance.sh + bin/ + guards/, comment-stripped, for TWO fixed literals.
# I widen on BOTH axes the brief names:
#   (a) the SURFACE  — Makefile, launchd plist, git hooks (incl. core.hooksPath), .claude/,
#                      package.json scripts, CI yml, and anything reachable by indirection.
#   (b) the PATTERN  — not just the two literals: ANY /Users/, ANY /home/, $HOME-rooted repo
#                      path, and a path ASSEMBLED from pieces (which a fixed-string grep misses).
set -u -o pipefail
echo "T298 wider-live-surface attack — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "HEAD = $(git rev-parse HEAD)"
echo

hr() { printf '%s\n' "-------------------------------------------------------------------"; }

# ---------------------------------------------------------------- A. does the surface exist?
hr; echo "A. SURFACES THE BRIEF NAMES — present or measured absent (P-70: say where I looked)"
for p in Makefile makefile GNUmakefile .github .gitlab-ci.yml Justfile justfile Taskfile.yml package.json .pre-commit-config.yaml; do
  if [ -e "$p" ]; then echo "  PRESENT : $p"; else echo "  ABSENT  : $p"; fi
done
echo "  launchd plists:"; ls -1 .softhouse/launchd/*.plist 2>/dev/null | sed 's/^/    /' || echo "    (none)"
echo "  git hooks dir (worktree resolves hooks through the COMMON dir):"
CD=$(git rev-parse --git-common-dir)
echo "    --git-common-dir = $CD"
echo "    core.hooksPath   = $(git config --get core.hooksPath || echo '(unset -> default)')"
echo "    executable hooks actually installed (non-.sample):"
find "$CD/hooks" -maxdepth 1 -type f ! -name '*.sample' -perm -u+x 2>/dev/null | sed 's/^/      /' || true
n=$(find "$CD/hooks" -maxdepth 1 -type f ! -name '*.sample' -perm -u+x 2>/dev/null | wc -l | tr -d ' ')
echo "    count = $n   (0 = MEASURED zero installed hooks, not an unread directory)"
echo

# ---------------------------------------------------------------- B. the live executable set
hr; echo "B. THE LIVE EXECUTABLE SET, comment-stripped, searched for ANY host path"
LIVE=""
for f in .softhouse/conformance.sh .softhouse/bin/*.sh .softhouse/guards/*.sh .softhouse/launchd/*.plist; do
  [ -f "$f" ] && LIVE="$LIVE $f"
done
echo "  members ($(echo $LIVE | wc -w | tr -d ' ')):"; for f in $LIVE; do echo "    $f"; done
echo
echo "  strip full-line '#' comments, then grep for host-path shapes:"
for f in $LIVE; do
  case "$f" in
    *.plist) body=$(cat "$f") ;;
    *)       body=$(sed -e 's/[[:space:]]*#.*$//' "$f") ;;   # strip trailing comments too — STRICTER than T256
  esac
  hits=$(printf '%s\n' "$body" | grep -n -E '/Users/|/home/[a-z]' || true)
  if [ -n "$hits" ]; then
    echo "  *** $f"
    printf '%s\n' "$hits" | sed 's/^/        /'
  fi
done
echo "  (any *** block above is a LIVE HOST PATH SURVIVING COMMENT-STRIPPING)"
echo

# ---------------------------------------------------------------- C. assembled / indirect paths
hr; echo "C. PATHS A FIXED-STRING GREP WOULD MISS — assembly, indirection, here-docs"
echo "  C1. concatenation of a host prefix with a repo suffix:"
grep -n -E '"/Users|/Users/\$|\$\{?USER\}?/|/Users/"' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO"
echo "  C2. \$HOME-rooted repo path (portable-looking, still host-shaped):"
grep -n -E '\$HOME/[A-Za-z]|~/gerege|~/\.softhouse' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO"
echo "  C3. variable-INDIRECT execution (eval / \${!var} / \$( \$var ) / bash \$var):"
grep -n -E 'eval[[:space:]]|\$\{![A-Za-z_]|bash[[:space:]]+"?\$[A-Za-z_]|sh[[:space:]]+"?\$[A-Za-z_]|\. +"?\$[A-Za-z_]' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO"
echo "  C4. here-doc bodies in the live set that mention the toolchain (a here-doc is not a comment):"
grep -n -E '<<-?[[:space:]]*.?(EOF|SH|PY|EOSQL|BODY)' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO here-docs"
echo "  C5. GOROOT/GOPATH/GOMODCACHE assignments OUTSIDE go-env.sh (the paste this all exists to stop):"
for f in $LIVE; do
  case "$f" in *go-env.sh) continue ;; esac
  grep -n -E '^[[:space:]]*(export[[:space:]]+)?(GOROOT|GOPATH|GOCACHE|GOMODCACHE|GEREGE_TOOLCHAIN)=' "$f" 2>/dev/null | sed "s|^|    $f:|"
done
echo "    (empty = MEASURED ZERO)"
echo

# ---------------------------------------------------------------- D. indirect invocation of the 60
hr; echo "D. CAN ANY GRADED PATH REACH ONE OF THE 60 ARCHIVED INSTRUMENTS?"
echo "  D1. any 'bash|sh|python <path under capture/reviews/handoff>' in the live set:"
grep -n -E '(bash|sh|python3?|\.)[[:space:]]+[^[:space:]]*(capture|reviews|handoff)/' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO"
echo "  D2. any find/glob-and-execute over those trees:"
grep -n -E 'find[[:space:]]+[^|]*(capture|reviews|handoff)|for[[:space:]]+[A-Za-z_]+[[:space:]]+in[[:space:]]+[^;]*(capture|reviews|handoff)' $LIVE 2>/dev/null | sed 's/^/    /' || echo "    MEASURED ZERO"
echo "  D3. launchd plist ProgramArguments — what the unattended fire ACTUALLY runs:"
for p in .softhouse/launchd/*.plist; do
  [ -f "$p" ] || continue
  echo "    $p:"
  sed -n '/ProgramArguments/,/<\/array>/p' "$p" | sed 's/^/      /'
done
echo
echo "  D4. .claude/skills — does any skill instruct a human/agent to run one of the 60?"
grep -rn -E '(capture|reviews)/[^ ]*\.(sh|py)' .claude/skills 2>/dev/null | head -20 | sed 's/^/    /' || echo "    MEASURED ZERO"
echo
hr; echo "END"
