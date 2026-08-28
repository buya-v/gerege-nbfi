#!/bin/zsh
# T342 — WHY the "obvious" fix (add `{}` to the strip class) does not work under zsh.
#
# T280 asserted it "does not compile". This probe establishes exactly what happens,
# variant by variant, so the claim is measured rather than repeated. Each variant is
# written to its own file and run through `zsh -n` (parse only) AND executed, so a
# PARSE error and a WRONG-ANSWER-that-parses are distinguished — they are different
# defects and only one of them is loud.
#
# Input in every case is the value `lock_released_at()` actually holds at that point
# when `released_at` is the last key: the 5-character string  null}
set -uo pipefail
D=$(mktemp -d /tmp/t342-brace.XXXXXX)

run() {   # $1 = label, $2 = body
  local label="$1" body="$2" f="$D/v.zsh" parse exec_out rc
  print -r -- "$body" > "$f"
  parse=$(zsh -n "$f" 2>&1); rc=$?
  if (( rc != 0 )); then
    printf '  %-46s PARSE FAIL: %s\n' "$label" "${parse##*: }"
    return
  fi
  exec_out=$(zsh "$f" 2>&1); rc=$?
  if (( rc != 0 )); then
    printf '  %-46s parses; RUNTIME FAIL rc=%d: %s\n' "$label" $rc "${exec_out##*: }"
  else
    printf '  %-46s parses; result %s\n' "$label" "$exec_out"
  fi
}

print -r -- "input value in every variant: 'null}'   (what the shipped cut leaves when released_at is last)"
print -r -- "expected after the strip: 'null'  -> so the == null test fires -> lock stays HELD"
print -r -- ""

run "0  SHIPPED class  [ \\t\\r\\n\"]" \
'v="null}"
v="${v//[$'"'"' \t\r\n\"'"'"']/}"
print -r -- "[$v]"'

run "A1 naive: add {} inside \$'"'"'...'"'"' in the class" \
'v="null}"
v="${v//[$'"'"' \t\r\n\"{}'"'"']/}"
print -r -- "[$v]"'

run "A2 naive: add } only, inside \$'"'"'...'"'"'" \
'v="null}"
v="${v//[$'"'"' \t\r\n\"}'"'"']/}"
print -r -- "[$v]"'

run "A3 backslash-escaped braces outside the quote" \
'v="null}"
v="${v//[$'"'"' \t\r\n\"'"'"'\{\}]/}"
print -r -- "[$v]"'

run "A4 braces via \$'"'"'\\173\\175'"'"' octal escapes" \
'v="null}"
v="${v//[$'"'"' \t\r\n\"\173\175'"'"']/}"
print -r -- "[$v]"'

run "B  T280 proposal: cut at first } then strip" \
'v="null}"
v="${v%%\}*}"
v="${v//[$'"'"' \t\r\n\"'"'"']/}"
print -r -- "[$v]"'

print -r -- ""
print -r -- "--- the same variants as they would appear INSIDE lock_released_at(), i.e. cut-at-comma first"
print -r -- "--- body has released_at LAST, so the comma cut runs to end of object"

run "0  SHIPPED, full function body" \
'body='"'"'{
  "host": "h",
  "pid": 1,
  "started_at": "2026-08-28T00:00:00Z",
  "released_at": null
}'"'"'
v="${${body#*\"released_at\":}%%,*}"
v="${v//[$'"'"' \t\r\n\"'"'"']/}"
print -r -- "[$v]"'

run "A1 naive class, full function body" \
'body='"'"'{
  "host": "h",
  "pid": 1,
  "started_at": "2026-08-28T00:00:00Z",
  "released_at": null
}'"'"'
v="${${body#*\"released_at\":}%%,*}"
v="${v//[$'"'"' \t\r\n\"{}'"'"']/}"
print -r -- "[$v]"'

run "B  T280 proposal, full function body" \
'body='"'"'{
  "host": "h",
  "pid": 1,
  "started_at": "2026-08-28T00:00:00Z",
  "released_at": null
}'"'"'
v="${${body#*\"released_at\":}%%,*}"
v="${v%%\}*}"
v="${v//[$'"'"' \t\r\n\"'"'"']/}"
print -r -- "[$v]"'

print -r -- ""
print -r -- "scratch: $D"
