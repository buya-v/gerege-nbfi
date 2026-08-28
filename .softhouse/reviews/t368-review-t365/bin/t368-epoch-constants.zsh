#!/bin/zsh
# T368 — close T365's UNVERIFIED item (a), and derive group H's five constants INDEPENDENTLY
# of the code under test.
#
# T365 relied on T361's Go measurement. Go is on this host, so there was no reason not to run
# it; this does. And group H's expectations are computed with python's `calendar.timegm`, NOT
# by calling `_iso8601_epoch` — grading a function against its own output is the failure the
# group exists to avoid.
#
# Usage: zsh t368-epoch-constants.zsh [path to the go probe source]
emulate -L zsh
set -uo pipefail

GOSRC="${1:-${0:A:h}/t368-go-zerotime.go.txt}"

print -r -- "=== T368: closing UNVERIFIED item (a) — what Go's zero time.Time marshals to"
go version
W="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/t368-go.XXXXXX")" || exit 3
[[ -n "$W" && -d "$W" && "$W" != "/" ]] || exit 3
trap 'rm -rf "$W"' EXIT
cp "$GOSRC" "$W/main.go"
printf 'module t368probe\n\ngo 1.21\n' > "$W/go.mod"
( cd "$W" && GOFLAGS=-mod=mod go run ./main.go ) || { print -u2 "ABORT: the go probe did not run"; exit 3; }
print -r -- ""
print -r -- "--- the probe source:"
cat "$GOSRC"

print -r -- ""
print -r -- "=== group H's constants, derived with calendar.timegm (NOT with _iso8601_epoch)"
/usr/bin/python3 - <<'PY'
import calendar, datetime
print('python datetime.min ->', datetime.datetime.min.strftime('%Y-%m-%dT%H:%M:%SZ'))
print('python datetime.max ->', datetime.datetime.max.strftime('%Y-%m-%dT%H:%M:%SZ'))
for s in ['1970-01-01T00:00:00Z', '1970-01-02T00:00:00Z',
          '2000-02-29T00:00:00Z', '2099-12-31T23:59:59Z']:
    t = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    print('%-22s -> %d' % (s, calendar.timegm(t.timetuple())))
try:
    datetime.datetime.strptime('2100-02-29T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    print('2100-02-29             -> ACCEPTED  *** BAD: the expectation itself is wrong')
except ValueError as e:
    print('2100-02-29             -> REFUSED by python:', e)
PY
