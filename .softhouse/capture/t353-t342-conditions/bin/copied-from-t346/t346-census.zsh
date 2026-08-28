#!/bin/zsh
# T346 independent census. My own adversarial bodies, written without reusing T342's
# fixture set. Drives the REAL readers through `fire-program.sh --lock-signals`, so it
# exercises lock_released_at / lock_started_age / lock_pid_state and NOT a re-implementation.
#
# Direction convention, which is the whole point of the review:
#   FAIL-OPEN  = a lock held by a LIVE process owned by this user reads as takeable.
#                That is the P-85 SAFETY bug. Any FREE-*/TAKE-* in section A.
#   FAIL-SHUT  = a lock that SHOULD be reclaimable is not. That is a LIVENESS bug.
#                Sections B and C.
#
# usage: t346-census.zsh <path-to-fire-program.sh> <label>
emulate -L zsh
set -uo pipefail
FP="$1"; LABEL="$2"
HOST="$(hostname -s)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OLD="$(date -u -r $(( $(date +%s) - 360000 )) +%Y-%m-%dT%H:%M:%SZ)"   # 100 h ago

# a genuinely LIVE pid on this host, and a genuinely DEAD one
sleep 600 & LIVE=$!
sleep 0.1 & DEAD=$!; wait $DEAD 2>/dev/null
trap "kill $LIVE 2>/dev/null" EXIT

TAB=$'\t'
BOM=$'\357\273\277'
COMBINING=$'\314\201'    # U+0301, so `host` is a unicode near-miss of the real hostname

S="$(mktemp -d)"; mkdir -p "$S/.softhouse"
run() { GEREGE_NBFI_REPO="$S" zsh "$FP" --lock-signals 2>&1 | grep -E '^verdict' | head -1; }

typeset -i n=0 open_fail=0 shut_fail=0

# $1 id  $2 expectation (HELD | TAKE-dead-pid | TAKE-ceiling | FREE-released)  $3 body  $4 what
row() {
  local id="$1" want="$2" body="$3" what="$4" v verdict mark
  printf '%s' "$body" > "$S/.softhouse/LOCK"
  v="$(run)"
  verdict="${v##verdict=}"
  n+=1
  mark="ok"
  if [[ "$want" == HELD ]]; then
    [[ "$verdict" == HELD-* ]] || { mark="*** FAIL-OPEN"; open_fail+=1; }
  else
    [[ "$verdict" == "$want" ]] || { mark="*** FAIL-SHUT"; shut_fail+=1; }
  fi
  printf '%-4s %-14s want=%-14s got=%-16s %s\n' "$id" "$mark" "$want" "$verdict" "$what"
}

print -r -- "=== T346 independent census   label=$LABEL"
print -r -- "=== file=$FP"
print -r -- "=== host=$HOST live_pid=$LIVE dead_pid=$DEAD now=$NOW old=$OLD"
print -r -- ""
print -r -- "--- A. LIVE holder, this host, fresh started_at. Correct = HELD-*. Anything else = FAIL-OPEN (P-85 safety)."

row A01 HELD "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}" "baseline, no released_at key"
row A02 HELD "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": null}" "released_at null as LAST key (T280 F-A)"
row A03 HELD "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": null}${TAB}" "same + trailing tab"
row A04 HELD "{\"holder\":\"f\",\"host\":\"$HOST\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":null}" "compact separators, no space after colon"
row A05 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"$NOW\", \"released_at\": null}" "released_at twice: string then null (first-wins says FREE)"
row A06 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": null, \"released_at\": \"$NOW\"}" "released_at twice: null then string (LAST-wins says FREE)"
row A07 HELD "host=$HOST pid=$LIVE \"released_at\": pending" "not JSON at all, contains the substring"
row A08 HELD "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"202" "write truncated mid-value"
row A09 HELD "" "empty file"
row A10 HELD "   ${TAB} " "whitespace-only file"
row A11 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"null\"}" "released_at is the STRING \"null\""
row A12 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": {\"at\": \"$NOW\"}}" "released_at is a nested OBJECT"
row A13 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": 0}" "released_at is a number"
row A14 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"\"}" "released_at is the empty string"
row A15 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"meta\": {\"released_at\": \"$NOW\"}}" "released_at NESTED under another key"
row A16 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"note\": \"not released_at, comma, here\"}" "the token inside a string value"
row A17 HELD "[{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}]" "top level is an ARRAY, not an object"
row A18 HELD "{\"host\": \"$HOST\", \"pid\": \"$LIVE\", \"started_at\": \"$NOW\", \"released_at\": null}" "pid is a STRING"
row A19 HELD "{\"host\": \"$HOST\", \"pid\": true, \"started_at\": \"$NOW\", \"released_at\": null}" "pid is the bool true"
row A20 HELD "{\"host\": \"$HOST\", \"pid\": ${LIVE}.0, \"started_at\": \"$NOW\", \"released_at\": null}" "pid is a float"
row A21 HELD "${BOM}{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}" "UTF-8 BOM prefix"
row A22 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"a,b\"XX}" "malformed, value contains a comma"
row A23 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \" \"}" "released_at is a single SPACE"
row A24 HELD "{\"host\": \"$HOST${COMBINING}\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": null}" "host is a unicode near-miss (combining acute)"
row A25 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\"} trailing garbage" "valid object then trailing garbage"
row A26 HELD "// a comment
{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}" "JSON with a leading comment line"
row A27 HELD "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": false}" "released_at is the bool false"
row A28 HELD "{\"pid\": $LIVE, \"host\": \"$HOST\", \"started_at\": \"$NOW\", \"released_at\": null}" "key order permuted, pid first"

print -r -- ""
print -r -- "--- B. DEAD holder, this host. Correct = TAKE-dead-pid. Anything else = FAIL-SHUT (liveness)."
row B01 TAKE-dead-pid "{\"holder\": \"f\", \"host\": \"$HOST\", \"started_at\": \"$NOW\", \"pid\": $DEAD}" "pid is the LAST key"
row B02 TAKE-dead-pid "{\"holder\":\"f\",\"host\":\"$HOST\",\"started_at\":\"$NOW\",\"pid\":$DEAD}" "compact separators, pid last"
row B03 TAKE-dead-pid "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $DEAD, \"started_at\": \"$NOW\"}" "canonical order"
row B04 TAKE-dead-pid "{\"host\": \"$HOST\", \"pid\": $DEAD, \"started_at\": \"$NOW\", \"released_at\": null}" "canonical + released_at null"

print -r -- ""
print -r -- "--- C. LIVE holder, started_at past the 24 h ceiling. Correct = TAKE-ceiling. Anything else = FAIL-SHUT."
row C01 TAKE-ceiling "{\"holder\": \"f\", \"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$OLD\"}" "100 h old, spaced separators"
row C02 TAKE-ceiling "{\"holder\":\"f\",\"host\":\"$HOST\",\"pid\":$LIVE,\"started_at\":\"$OLD\"}" "100 h old, compact separators"

print -r -- ""
print -r -- "--- D. Genuinely RELEASED lock. Correct = FREE-released. Anything else = FAIL-SHUT."
row D01 FREE-released "{\"host\": \"$HOST\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"$NOW\"}" "released_at a real timestamp string"

print -r -- ""
print -r -- "ROWS=$n FAIL_OPEN=$open_fail FAIL_SHUT=$shut_fail"
rm -rf "$S"
(( open_fail == 0 && shut_fail == 0 )) || exit 1
exit 0
