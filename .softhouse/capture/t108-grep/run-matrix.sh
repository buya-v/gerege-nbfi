#!/usr/bin/env bash
# T108 — the grep / invalid-multibyte matrix.
#
# Runs every (shape x tool x locale x flagset x pattern) cell and records the
# EXIT STATUS and the stdout for each.  Exit status matters as much as the
# match: the alleged defect is SILENT — it returns 0 with no diagnostic.
#
# This script contains no arithmetic other than integer cell counting, so it
# contains no floating point (P-25).
#
# Usage:  bash run-matrix.sh          # writes out/matrix.tsv
#
# ---------------------------------------------------------------------------
# TOOLS
#
#   bsd      /usr/bin/grep  — BSD grep 2.6.0-FreeBSD, the macOS system grep.
#
#   ccfn     the Claude Code Bash-tool `grep` SHELL FUNCTION, copied verbatim
#            from the session shell snapshot (out/shell-function.txt).  It is
#            NOT a binary on PATH: it re-executes the `claude` binary with
#            argv[0]=ugrep, i.e. ugrep 7.5.0 is EMBEDDED in the claude
#            executable.  That is why `command -v ugrep` is empty on this host
#            while `grep --version` prints "ugrep 7.5.0".  The hard-coded flags
#            that matter are -G (grep-compatible BRE), -I (SKIP BINARY FILES)
#            and --ignore-files (obey .gitignore).
#
#   ugrepGI  the same embedded ugrep with only -G -I   (isolates -I)
#   ugrepG   the same embedded ugrep with only -G      (control, no -I)
# ---------------------------------------------------------------------------
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$HERE/corpus"
OUT="$HERE/out"

CC_BIN="${CLAUDE_CODE_EXECPATH:-}"
if [ ! -x "$CC_BIN" ]; then CC_BIN="$HOME/.local/bin/claude"; fi

run_tool() {   # run_tool <tool> <args...>
  local tool="$1"; shift
  case "$tool" in
    bsd)      /usr/bin/grep "$@" ;;
    ccfn)     ARGV0=ugrep "$CC_BIN" -G --ignore-files --hidden -I \
                --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg \
                --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl "$@" ;;
    ugrepGI)  ARGV0=ugrep "$CC_BIN" -G -I "$@" ;;
    ugrepG)   ARGV0=ugrep "$CC_BIN" -G "$@" ;;
    *) echo "unknown tool $tool" >&2; return 99 ;;
  esac
}

# re-entrant arm, so each cell runs in its own process with its own locale env
if [ "${1:-}" = "--exec" ]; then
  shift
  run_tool "$@"
  exit $?
fi

mkdir -p "$OUT"

TOOLS="bsd ccfn ugrepGI ugrepG"
LOCALES="utf8C utf8enUS posixC"
FLAGSETS="-c -ac"

locale_env() {
  case "$1" in
    utf8C)    echo "-u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8" ;;
    utf8enUS) echo "LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8" ;;
    posixC)   echo "LC_ALL=C LANG=C" ;;
  esac
}

patterns_for() {
  case "$1" in
    t80-exact-repro)
      echo '^  PASS|3;unbound variable|1;PRECONDITIONS BREACHED|0' ;;
    *)
      echo 'TARGET|1' ;;
  esac
}

TSV="$OUT/matrix.tsv"
printf 'shape\ttool\tlocale\tflags\tpattern\texpected\tgot\texit\tverdict\tstderr\n' > "$TSV"

cells=0
silent=0
loud=0

for f in "$CORPUS"/*.txt; do
  shape="$(basename "$f" .txt)"
  IFS=';' read -r -a pats <<< "$(patterns_for "$shape")"
  for pe in "${pats[@]}"; do
    pat="${pe%|*}"; exp="${pe##*|}"
    for tool in $TOOLS; do
      for loc in $LOCALES; do
        for flags in $FLAGSETS; do
          errf="$(mktemp -t t108err)"
          got="$(env $(locale_env "$loc") bash "$0" --exec "$tool" "$flags" "$pat" "$f" 2>"$errf")"
          st=$?
          err="$(tr '\n' ' ' < "$errf" | sed 's/  */ /g; s/^ //; s/ $//')"
          rm -f "$errf"
          got_clean="$(printf '%s' "$got" | tr -d '\n')"
          if [ "$got_clean" = "$exp" ]; then
            verdict=OK
          elif [ "$got_clean" = "0" ] && [ "$exp" != "0" ] && [ -z "$err" ]; then
            verdict=SILENT-MISS; silent=$((silent + 1))
          elif [ "$got_clean" = "0" ] && [ "$exp" != "0" ]; then
            verdict=LOUD-MISS; loud=$((loud + 1))
          else
            verdict=OTHER
          fi
          printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$shape" "$tool" "$loc" "$flags" "$pat" "$exp" \
            "${got_clean:-<empty>}" "$st" "$verdict" "${err:-<none>}" >> "$TSV"
          cells=$((cells + 1))
        done
      done
    done
  done
done

echo "cells run:     $cells"
echo "SILENT-MISS:   $silent"
echo "LOUD-MISS:     $loud"
echo "matrix:        $TSV"
