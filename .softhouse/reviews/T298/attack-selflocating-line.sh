#!/usr/bin/env bash
# T298 — hostile attack on the self-locating ACTIVATION LINE that T256 installed.
# The line is EXTRACTED FROM THE DOCUMENT, exactly as T256's own drive does, so this attacks
# what is prescribed and not a paraphrase of it.
set -u -o pipefail

REPO="$1"
DOC="$REPO/.softhouse/reference-oracle.md"

ACT="$(awk '
  /T256-ACTIVATION-LINE:BEGIN/ { inblk=1; next }
  /T256-ACTIVATION-LINE:END/   { inblk=0 }
  inblk && /^```/              { fence=!fence; next }
  inblk && fence               { print }
' "$DOC")"
echo "EXTRACTED FROM THE DOCUMENT: [$ACT]"
echo

probe () {   # $1 = label, $2 = cwd, rest = env prefix
  local label="$1"; shift
  local dir="$1"; shift
  echo "=================================================================="
  echo "SCENARIO: $label"
  echo "  cwd    : $dir"
  ( cd "$dir" 2>/dev/null || { echo "  cwd does not exist"; exit 9; }
    env -u GEREGE_GO_SOURCE -u GOROOT "$@" bash -c '
      set -u -o pipefail
      ACT="$1"
      echo "  toplevel says: [$(git rev-parse --show-toplevel 2>&1 | head -1)]"
      eval "$ACT"
      rc=$?
      echo "  activation rc          : $rc"
      echo "  GEREGE_GO_SOURCE       : ${GEREGE_GO_SOURCE:-UNSET}"
      echo "  GOROOT                 : ${GOROOT:-UNSET}"
      echo "  command -v go          : $(command -v go || echo NONE)"
      echo "  --- what the SHELL CONTINUES to do after the failure (fail open vs fail closed):"
      echo "  the script did NOT abort; this line printed."
    ' _ "$ACT" 2>&1 | sed "s/^/  /"
  )
  echo
}

probe "CONTROL — inside the repo (the case T256 drove)" "$REPO"
probe "A1 — inside a DIFFERENT git repo: /Users/buv/fineract, the cwd reference-oracle.md:148 SETS" "/Users/buv/fineract"
probe "A2 — outside any git checkout (/tmp)" "/tmp"
probe "A3 — inside the repo's .git directory" "$REPO/.git"
