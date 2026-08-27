#!/usr/bin/env bash
# T254 reviewer instrument: audit BOTH authors' COMMITTED instruments against
# P-75/P-80. Last fire, three workers wrote fail-opens into instruments built to
# enforce the very rule they broke -- one into the fail-open detector itself.
#
# CHECKED, per file:
#   B1  bare `grep` (this host: a ugrep 7.5.0 WRAPPER with --ignore-files and six
#       --exclude-dir silently prepended -- 33% recall, measured). Absolute
#       /usr/bin/grep, `git grep`, or python3 re are the sound forms.
#   B2  `rg` (no binary on this host; `rg P F | head` exits 0 -> a silent pass)
#   B3  `git grep -E` with \b (reads as a LITERAL b on this build: misses AND
#       fabricates, returning zero SILENTLY)
#   B4  missing `set -euo pipefail` in a .sh
#   B5  `|| true` / `|| echo` / `grep -c || echo 0` -- these CONFLATE grep exit 1
#       (a real measured negative) with exit >1 (an ERROR that must ABORT)
#
# P-80: this auditor reports grep exit 1 as a measured negative and ABORTS on
# exit >1. It never prints an absence it did not measure.
set -euo pipefail
G=/usr/bin/grep
LIST="${1:?file list}"
LABEL="${2:?label}"
ROOTREF="${3:?git ref to read blobs from}"
WORK="${4:?scratch dir}"

mkdir -p "$WORK"

has() {  # has PATTERN FILE -> 0 hit, 1 clean; aborts on grep error
  local pat="$1" f="$2" rc
  set +e
  "$G" -q -E -e "$pat" -- "$f"
  rc=$?
  set -e
  case "$rc" in
    0) return 0 ;;
    1) return 1 ;;
    *) echo "FATAL: grep exit $rc on $f" >&2; exit 91 ;;
  esac
}

n_files=0; n_sh=0; n_py=0
b1=0; b2=0; b3=0; b4=0; b5=0
: > "$WORK/findings.txt"

while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in *.sh|*.py) ;; *) continue ;; esac
  n_files=$((n_files+1))
  local_tmp="$WORK/blob"
  git show "$ROOTREF:$f" > "$local_tmp" 2>/dev/null || { echo "SKIP (unreadable): $f" >> "$WORK/findings.txt"; continue; }

  case "$f" in *.sh) n_sh=$((n_sh+1)) ;; *.py) n_py=$((n_py+1)) ;; esac

  # B1 bare grep: a `grep` token NOT preceded by / (abs path) and not `git grep`
  if has '(^|[^/[:alnum:]_.-])grep[[:space:]]' "$local_tmp"; then
    if ! has '(/usr/bin/grep|git grep|"\$G"|\$\{G\})' "$local_tmp"; then
      b1=$((b1+1)); echo "B1 bare-grep      $f" >> "$WORK/findings.txt"
    else
      echo "B1? mixed-grep    $f  (has both a bare token and a sound form - manual look)" >> "$WORK/findings.txt"
    fi
  fi

  # B2 rg
  if has '(^|[^[:alnum:]_./-])rg[[:space:]]' "$local_tmp"; then
    b2=$((b2+1)); echo "B2 rg             $f" >> "$WORK/findings.txt"
  fi

  # B3 git grep -E with \b
  if has 'git grep[^\n]*\\b' "$local_tmp"; then
    b3=$((b3+1)); echo "B3 gitgrep-\\b     $f" >> "$WORK/findings.txt"
  fi

  # B4 .sh without set -euo pipefail
  case "$f" in
    *.sh)
      if ! has 'set -euo pipefail' "$local_tmp"; then
        b4=$((b4+1)); echo "B4 no-set-euo     $f" >> "$WORK/findings.txt"
      fi ;;
  esac

  # B5 exit-code conflation
  if has '(\|\|[[:space:]]*true|\|\|[[:space:]]*echo|-c[^\n]*\|\|[[:space:]]*echo)' "$local_tmp"; then
    b5=$((b5+1)); echo "B5 rc-conflation  $f" >> "$WORK/findings.txt"
  fi
done < "$LIST"

echo "======================================================================"
echo "INSTRUMENT AUDIT — $LABEL   (blobs read from $ROOTREF)"
echo "======================================================================"
echo "TERM-1  .sh/.py instruments added by this branch ....... $n_files  (.sh=$n_sh .py=$n_py)"
echo "TERM-2  B1 bare grep (ugrep wrapper hazard) ............ $b1"
echo "TERM-3  B2 rg ......................................... $b2"
echo "TERM-4  B3 git grep -E with \\b ........................ $b3"
echo "TERM-5  B4 .sh missing set -euo pipefail .............. $b4"
echo "TERM-6  B5 || true / || echo rc-conflation ............ $b5"
echo
echo "--- per-file findings ---"
cat "$WORK/findings.txt"
echo "--- end $LABEL ---"
