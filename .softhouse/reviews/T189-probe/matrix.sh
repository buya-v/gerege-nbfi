#!/bin/bash
# T189 — the discriminator matrix.
#
# Separates, as separate axes rather than conflating them:
#   IMPL      : /usr/bin/grep (BSD)  vs  the claude-as-ugrep wrapper the `grep` shell function runs
#   FLAGS     : bare -v  vs  -av (the live line's flags)
#   LOCALE    : C, C.UTF-8, en_US.UTF-8, POSIX
#   SHAPE     : file argument | '<' redirection | anonymous pipe   (seekable vs not)
#   BYTES     : invalid UTF-8 (\xe2, \xff\xfe, \xff, \x80, \xc0) vs a real NUL vs a NUL-dense blob vs clean
#
# For every cell it records: exit status, stdout byte count, stdout rendered safely, stderr.
set -u

PROBE_DIR="$(cd "$(dirname "$0")" && pwd)"
FIX="$PROBE_DIR/fixtures"
bash "$PROBE_DIR/mkfixtures.sh" "$FIX"

# P-46: the pattern is EXTRACTED from the live line, never retyped.
SRC="$PROBE_DIR/../../bin/fire-program.sh"
PAT=$(sed -n '224p' "$SRC" | sed -e "s/.*grep -av '//" -e "s/'.*//")
printf 'live line 224 (extracted): '; sed -n '224p' "$SRC"
printf 'extracted pattern bytes  : '; printf '%s' "$PAT" | od -c | head -2

CLAUDE_BIN="${CLAUDE_CODE_EXECPATH:-/Users/buv/.local/bin/claude}"

# Exactly the argv the `grep` shell function builds (bash branch: exec -a ugrep ...).
run_ugrep() { ( exec -a ugrep "$CLAUDE_BIN" -G --ignore-files --hidden -I \
                 --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg \
                 --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl "$@" ) ; }
run_bsd()  { /usr/bin/grep "$@" ; }

render() { od -c | sed -n '1,6p' ; }

cell() {
  local impl="$1" flags="$2" loc="$3" shape="$4" fixture="$5"
  local f="$FIX/$fixture"
  local out err rc
  out="$PROBE_DIR/.out"; err="$PROBE_DIR/.err"

  case "$impl:$shape" in
    bsd:file)  env LC_ALL="$loc" /usr/bin/grep $flags "$PAT" "$f" >"$out" 2>"$err" ; rc=$? ;;
    bsd:redir) env LC_ALL="$loc" /usr/bin/grep $flags "$PAT" <"$f" >"$out" 2>"$err" ; rc=$? ;;
    bsd:pipe)  cat "$f" | env LC_ALL="$loc" /usr/bin/grep $flags "$PAT" >"$out" 2>"$err" ; rc=$? ;;
    ugrep:file)  ( export LC_ALL="$loc"; exec -a ugrep "$CLAUDE_BIN" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl $flags "$PAT" "$f" ) >"$out" 2>"$err" ; rc=$? ;;
    ugrep:redir) ( export LC_ALL="$loc"; exec -a ugrep "$CLAUDE_BIN" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl $flags "$PAT" ) <"$f" >"$out" 2>"$err" ; rc=$? ;;
    ugrep:pipe)  cat "$f" | ( export LC_ALL="$loc"; exec -a ugrep "$CLAUDE_BIN" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl $flags "$PAT" ) >"$out" 2>"$err" ; rc=$? ;;
  esac

  local nb; nb=$(wc -c <"$out" | tr -d ' ')
  local nl; nl=$(wc -l <"$out" | tr -d ' ')
  echo "----------------------------------------------------------------"
  echo "IMPL=$impl FLAGS='$flags' LC_ALL=$loc SHAPE=$shape FIXTURE=$fixture"
  echo "  exit=$rc  stdout_bytes=$nb  stdout_lines=$nl"
  echo "  stdout:"; sed -e 's/^/    | /' "$out" | head -8
  echo "  stderr:"; sed -e 's/^/    ! /' "$err" | head -4
}

FIXTURES="e-clean.txt a-utf8-e2.txt c-fffe.txt f-ff.txt g-80.txt h-c0.txt d-lockline.txt b-nul.txt i-blob.txt"

echo "################ ARM 1 — /usr/bin/grep (BSD), live flags -av, LC_ALL=C (== the live line) ############"
for fx in $FIXTURES; do
  for sh in file redir pipe; do cell bsd "-av" C "$sh" "$fx"; done
done

echo "################ ARM 2 — /usr/bin/grep (BSD), UNhardened flags -v, LC_ALL=C.UTF-8 (== pre-T157 line) ############"
for fx in $FIXTURES; do
  for sh in file redir pipe; do cell bsd "-v" C.UTF-8 "$sh" "$fx"; done
done

echo "################ ARM 3 — claude-as-ugrep wrapper (-I hard-coded), UNhardened flags -v ############"
for fx in $FIXTURES; do
  for sh in file redir pipe; do cell ugrep "-v" C.UTF-8 "$sh" "$fx"; done
done

echo "################ ARM 4 — claude-as-ugrep wrapper, LIVE flags -av, LC_ALL=C ############"
for fx in $FIXTURES; do
  for sh in file redir pipe; do cell ugrep "-av" C "$sh" "$fx"; done
done

echo "################ ARM 5 — locale sweep, BSD, -v, file shape only ############"
for loc in C C.UTF-8 en_US.UTF-8 POSIX; do
  for fx in a-utf8-e2.txt b-nul.txt; do cell bsd "-v" "$loc" file "$fx"; done
done

echo "################ ARM 6 — locale sweep, ugrep wrapper, -v, file shape only ############"
for loc in C C.UTF-8 en_US.UTF-8 POSIX; do
  for fx in a-utf8-e2.txt b-nul.txt; do cell ugrep "-v" "$loc" file "$fx"; done
done

rm -f "$PROBE_DIR/.out" "$PROBE_DIR/.err"
echo "################ DONE ############"
