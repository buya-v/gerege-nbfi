#!/bin/bash
# INDEPENDENT D-2 poison, written by A2-10 WITHOUT reading A2-5's prover.
# Goal of the attack: make a STALE BODY / STALE STATUS survive under a FRESH captured-at-utc.
SRC="$1"          # path to the cap.sh under test
LABEL="$2"
STALE_TS="2000-01-01T00:00:00Z"
STALE_BODY='{"stale":"BODY FROM AN EARLIER FIRE - MUST NOT BE RE-DATED"}'
PASS=0; FAIL=0; SKIP=0

mksandbox() {
  d=$(mktemp -d /tmp/poison/sb.XXXXXX)
  mkdir -p "$d/out" "$d/req"
  cp "$SRC" "$d/cap.sh"; chmod +x "$d/cap.sh"
  {
    echo "B=https://127.0.0.1:1/api/v1"
    echo "A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='"
    echo "T='Fineract-Platform-TenantId: gerege'"
    echo "CT='Content-Type: application/json'"
    echo "export B A T CT"
  } > "$d/env.sh"
  printf '%s' "$STALE_BODY" > "$d/out/POISON.json"
  printf '200\n' > "$d/out/POISON.status"
  {
    echo "POST /glaccounts"
    echo "Fineract-Platform-TenantId: gerege"
    echo "Authorization: Basic <mifos:password>"
    echo "captured-at-utc: $STALE_TS"
  } > "$d/out/POISON.http"
  printf '{"x":1}' > "$d/req/b.json"
  echo "$d"
}

# check DESC DIR EXITCODE ERRFILE
check() {
  desc="$1"; d="$2"; ec="$3"; errf="$4"; verdict=ok; reasons=""
  if grep -qiE 'illegal option|invalid option|bad option|not an identifier|unknown option' "$errf" 2>/dev/null; then
    SKIP=$((SKIP+1)); printf '  skip    %-40s (shell refused the options)\n' "$desc"; rm -rf "$d"; return
  fi
  [ "$ec" -eq 0 ] && { verdict=BAD; reasons="$reasons exit0"; }
  if [ -f "$d/out/POISON.http" ]; then
    ts=$(sed -n 's/^captured-at-utc: //p' "$d/out/POISON.http")
    [ "$ts" = "$STALE_TS" ] || { verdict=BAD; reasons="$reasons FRESH-TIMESTAMP($ts)"; }
  fi
  body=$(cat "$d/out/POISON.json" 2>/dev/null)
  [ "$body" = "$STALE_BODY" ] || { verdict=BAD; reasons="$reasons BODY-MUTATED"; }
  st=$(cat "$d/out/POISON.status" 2>/dev/null)
  [ "$st" = "200" ] || { verdict=BAD; reasons="$reasons STATUS-MUTATED"; }
  if [ "$verdict" = ok ]; then
    PASS=$((PASS+1)); printf '  CAUGHT  %-40s exit=%s\n' "$desc" "$ec"
  else
    FAIL=$((FAIL+1)); printf '  *** LAUNDERED *** %-30s exit=%s %s\n' "$desc" "$ec" "$reasons"
  fi
  rm -rf "$d"
}

echo "=== $LABEL :: $SRC ==="
for SH in /bin/sh /bin/bash /bin/dash /bin/zsh /bin/ksh; do
  [ -x "$SH" ] || { echo "  (absent: $SH)"; continue; }
  for OPTS in "NONE" "-e" "-u" "-eu" "-e -o pipefail" "-eu -o pipefail" "-E -e"; do
    for BRANCH in body nobody; do
      d=$(mksandbox)
      errf="$d.err"
      if [ "$BRANCH" = body ]; then set -- POISON POST /glaccounts req/b.json; else set -- POISON POST /glaccounts; fi
      if [ "$OPTS" = "NONE" ]; then
        "$SH" "$d/cap.sh" "$@" >/dev/null 2>"$errf"; ec=$?
      else
        "$SH" $OPTS "$d/cap.sh" "$@" >/dev/null 2>"$errf"; ec=$?
      fi
      check "$SH ${OPTS} ${BRANCH}" "$d" "$ec" "$errf"
      rm -f "$errf"
    done
  done
done

for BRANCH in body nobody; do
  d=$(mksandbox); errf="$d.err"
  if [ "$BRANCH" = body ]; then "$d/cap.sh" POISON POST /glaccounts req/b.json >/dev/null 2>"$errf"; ec=$?
  else "$d/cap.sh" POISON POST /glaccounts >/dev/null 2>"$errf"; ec=$?; fi
  check "shebang ${BRANCH}" "$d" "$ec" "$errf"; rm -f "$errf"
done

echo "PASS=$PASS FAIL=$FAIL SKIP=$SKIP"
[ "$FAIL" -eq 0 ]
